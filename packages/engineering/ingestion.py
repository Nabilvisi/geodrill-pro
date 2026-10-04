"""Bounded, explicit-unit CSV and unwrapped LAS 2.0 imports."""
import csv
import io
import math
from datetime import datetime, timezone
from .models import MSEInput, Survey, SurveyRequest
from .physics import mse, minimum_curvature

MAX_ROWS = 10000
CHANNELS = {
    "md": {"m": 1, "ft": 0.3048},
    "tvd": {"m": 1, "ft": 0.3048},
    "wob": {"N": 1, "kN": 1000, "klbf": 4448.2216152605},
    "torque": {"N.m": 1, "kN.m": 1000, "ft.lbf": 1.3558179483314},
    "rpm": {"rpm": math.pi / 30, "rad/s": 1},
    "rop": {"m/h": 1 / 3600, "m/s": 1, "ft/h": 0.3048 / 3600},
    "spp": {"Pa": 1, "MPa": 1e6, "psi": 6894.757293168},
    "flow": {"m3/s": 1, "L/min": 1 / 60000, "gpm": 0.003785411784 / 60},
}
CANONICAL = {"md": "md_m", "tvd": "tvd_m", "wob": "wob_n", "torque": "torque_nm", "rpm": "rotation_rad_s", "rop": "rop_m_s", "spp": "spp_pa", "flow": "flow_m3_s"}


def table(text: str):
    reader = csv.DictReader(io.StringIO(text.lstrip("\ufeff")))
    if not reader.fieldnames or len(set(reader.fieldnames)) != len(reader.fieldnames):
        raise ValueError("CSV must have unique column headers.")
    rows = []
    for index, row in enumerate(reader, 2):
        if index > MAX_ROWS + 1:
            raise ValueError(f"Import exceeds this release's {MAX_ROWS:,}-row limit.")
        if None in row or any(v is None for v in row.values()):
            raise ValueError(f"Row {index} does not match the header width.")
        rows.append(row)
    if not rows:
        raise ValueError("File has no data rows.")
    return reader.fieldnames, rows


def number(value: str, context: str) -> float:
    try:
        result = float(value)
    except (ValueError, TypeError):
        raise ValueError(f"{context}: expected a number.")
    if not math.isfinite(result):
        raise ValueError(f"{context}: non-finite values are forbidden.")
    return result


def telemetry_csv(text: str, diameter: float):
    headers, rows = table(text)
    mapping = {}
    for channel, units in CHANNELS.items():
        matches = [(f"{channel}[{unit}]", factor) for unit, factor in units.items() if f"{channel}[{unit}]" in headers]
        if len(matches) != 1:
            raise ValueError(f"Supply exactly one explicit supported unit for {channel}. Supported: {', '.join(units)}")
        mapping[channel] = matches[0]
    expected = {name for name, _ in mapping.values()} | {"timestamp", "state"}
    if set(headers) != expected:
        raise ValueError(f"Telemetry headers must include timestamp, state and the eight documented channels; unexpected or missing: {set(headers) ^ expected}")
    output, events = [], []
    previous = None
    for index, raw in enumerate(rows, 2):
        try:
            timestamp = datetime.fromisoformat(raw["timestamp"].replace("Z", "+00:00"))
        except ValueError:
            raise ValueError(f"Row {index}: timestamp must be ISO 8601 with timezone.")
        if timestamp.tzinfo is None:
            raise ValueError(f"Row {index}: timestamp requires a timezone.")
        timestamp = timestamp.astimezone(timezone.utc)
        if previous is not None and timestamp <= previous:
            raise ValueError(f"Row {index}: duplicate or out-of-order time; explicitly reconcile before importing.")
        gap = (timestamp - previous).total_seconds() if previous else None
        previous = timestamp
        row = {"timestamp": timestamp.isoformat(), "state": raw["state"], "source_row": index, "gap_s": gap}
        issues = []
        for channel, (name, factor) in mapping.items():
            value = raw[name].strip()
            normalized = number(value, f"Row {index}, {name}") * factor if value else None
            if normalized is not None and not math.isfinite(normalized):
                raise ValueError(f"Row {index}, {name}: unit conversion exceeds the finite numerical range.")
            row[CANONICAL[channel]] = normalized
            if not value:
                issues.append(f"Missing {channel}")
        if row["state"] not in {"drilling", "off_bottom", "connection", "unknown"}:
            raise ValueError(f"Row {index}: unsupported drilling state.")
        for key in CANONICAL.values():
            if row[key] is not None and row[key] < 0:
                issues.append(f"Negative {key}; retained as invalid")
        if row["md_m"] is not None and row["tvd_m"] is not None and row["tvd_m"] > row["md_m"]:
            issues.append("TVD exceeds MD")
        if gap and gap > 5:
            events.append({"row_index": len(output), "code": "DATA_GAP", "severity": "review", "message": f"{gap:g}-second gap before {timestamp.isoformat()}; no interpolation applied."})
        if not issues:
            try:
                calculation = mse(MSEInput(**{k: row[k] for k in ["wob_n", "torque_nm", "rotation_rad_s", "rop_m_s"]}, bit_diameter_m=diameter, drilling_state=row["state"]))
            except ValueError:
                issues.append("Input outside the supported numerical envelope")
        if issues:
            calculation = {"value_pa": None, "status": "withheld", "reason": "; ".join(issues)}
        row.update(mse_pa=calculation["value_pa"], quality="invalid" if issues else "valid", mse_status=calculation["status"], reason=calculation["reason"])
        if issues or calculation["status"] == "withheld":
            events.append({"row_index": len(output), "code": "INPUT_QUALITY" if issues else "MSE_WITHHELD", "severity": "review" if issues else "info", "message": f"Row {index}: {calculation['reason']}"})
        output.append(row)
    return output, events, {k: {"source": name, "factor_to_si": factor} for k, (name, factor) in mapping.items()}


def survey_csv(text: str):
    headers, rows = table(text)
    length = "m" if "md[m]" in headers else "ft" if "md[ft]" in headers else None
    angle = "deg" if "inclination[deg]" in headers else "rad" if "inclination[rad]" in headers else None
    expected = {f"md[{length}]", f"inclination[{angle}]", f"azimuth[{angle}]"}
    if set(headers) != expected or not length or not angle:
        raise ValueError("Survey requires md[m] or md[ft], inclination[deg/rad], azimuth[deg/rad], with matching angle units.")
    lf = 1 if length == "m" else 0.3048
    af = math.pi / 180 if angle == "deg" else 1
    request = SurveyRequest(stations=[Survey(md_m=number(r[f"md[{length}]"], "MD") * lf, inclination_rad=number(r[f"inclination[{angle}]"], "Inclination") * af, azimuth_rad=number(r[f"azimuth[{angle}]"], "Azimuth") * af) for r in rows])
    return minimum_curvature(request)


def las2(text: str):
    section = ""
    curves, rows, meta = [], [], {}
    for line in text.lstrip("\ufeff").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("~"):
            section = line[1:].split()[0].upper()[0]
            continue
        if section in {"V", "W", "C"}:
            left = line.split(":", 1)[0]
            if "." not in left:
                raise ValueError("Malformed LAS header: expected mnemonic.unit value.")
            mnemonic, remainder = left.split(".", 1)
            mnemonic = mnemonic.strip().upper()
            if section == "C":
                unit = remainder.split()[0] if remainder and not remainder[0].isspace() else ""
                curves.append({"mnemonic": mnemonic, "unit": unit})
            else:
                meta[mnemonic] = remainder.strip().split()[-1] if remainder.strip() else ""
        elif section == "A":
            rows.append([number(x, "LAS data") for x in line.split()])
            if len(rows) > MAX_ROWS:
                raise ValueError("LAS exceeds the 10,000-row release limit.")
    if meta.get("VERS") not in {"2.0", "2.00"} or meta.get("WRAP", "").upper() != "NO":
        raise ValueError("Only LAS 2.0 with WRAP.NO is supported; wrapped and LAS 3 files need an adapter.")
    if not curves or not rows or any(len(r) != len(curves) for r in rows):
        raise ValueError("LAS curve count does not match the data rows.")
    if len({c['mnemonic'] for c in curves}) != len(curves):
        raise ValueError("Duplicate LAS curve mnemonics are not supported.")
    if curves[0]["mnemonic"] not in {"DEPT", "DEPTH"} or curves[0]["unit"].upper() not in {"M", "FT"}:
        raise ValueError("LAS index must be DEPT/DEPTH with M or FT units.")
    if "NULL" not in meta:
        raise ValueError("LAS must declare its NULL sentinel.")
    null = number(meta["NULL"], "LAS NULL")
    factor = 0.3048 if curves[0]["unit"].upper() == "FT" else 1
    normalized = []
    for r in rows:
        if r[0] == null or r[0] < 0:
            raise ValueError("LAS depth must be present and nonnegative.")
        normalized.append({"depth_m": r[0] * factor, **{c["mnemonic"]: None if v == null else v for c, v in zip(curves[1:], r[1:])}})
    delta = [b["depth_m"] - a["depth_m"] for a, b in zip(normalized, normalized[1:])]
    if delta and not (all(d > 0 for d in delta) or all(d < 0 for d in delta)):
        raise ValueError("LAS depth index must be strictly monotonic.")
    return normalized, curves, meta
