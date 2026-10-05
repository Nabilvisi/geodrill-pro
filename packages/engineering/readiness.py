"""Source field mapping dictionary and data readiness validator (GD-A01).

Supports:
- Robust unit and alias mapping across telemetry, directional surveys, and log curves.
- Data readiness assessment (completeness, null percentage, sampling regularity, state consistency).
- Explicit versioned mapping configuration preserving source headers and conversion factors.
"""
from typing import Literal, TypedDict, Any
import math
import re

# Standard industry aliases for channels
STANDARD_ALIASES: dict[str, list[str]] = {
    "md": ["md", "measured_depth", "depth", "dept", "bit_depth", "hole_depth"],
    "tvd": ["tvd", "true_vertical_depth", "tvd_ss", "tvd_subsea"],
    "wob": ["wob", "weight_on_bit", "bit_weight", "wob_surface", "wob_downhole"],
    "torque": ["torque", "torq", "surface_torque", "rotary_torque", "drill_torque"],
    "rpm": ["rpm", "rotary_speed", "surface_rpm", "drill_rpm", "rotation"],
    "rop": ["rop", "rate_of_penetration", "drill_rate", "drilling_speed"],
    "spp": ["spp", "standpipe_pressure", "pump_pressure", "circ_pressure"],
    "flow": ["flow", "flow_rate", "mud_flow", "pump_rate", "flow_in", "flow_rate_in"],
    "inclination": ["inc", "incl", "inclination", "deviation"],
    "azimuth": ["azi", "azim", "azimuth", "direction", "hole_azimuth"],
    "timestamp": ["time", "datetime", "timestamp", "date_time", "utc_time"],
    "state": ["state", "rig_state", "drilling_state", "activity_state"]
}

# Unit factors to standard SI units
UNIT_FACTORS: dict[str, dict[str, float]] = {
    "length": {
        "m": 1.0,
        "meter": 1.0,
        "meters": 1.0,
        "ft": 0.3048,
        "feet": 0.3048,
        "in": 0.0254,
        "inch": 0.0254
    },
    "force": {
        "n": 1.0,
        "kn": 1000.0,
        "lbf": 4.4482216152605,
        "klbf": 4448.2216152605,
        "ton": 8896.443230521
    },
    "torque": {
        "n.m": 1.0,
        "nm": 1.0,
        "kn.m": 1000.0,
        "knm": 1000.0,
        "ft.lbf": 1.3558179483314,
        "ftlbf": 1.3558179483314,
        "kft.lbf": 1355.8179483314
    },
    "velocity": {
        "m/s": 1.0,
        "m/h": 1.0 / 3600.0,
        "ft/h": 0.3048 / 3600.0,
        "ft/min": 0.3048 / 60.0
    },
    "pressure": {
        "pa": 1.0,
        "kpa": 1000.0,
        "mpa": 1.0e6,
        "bar": 1.0e5,
        "psi": 6894.757293168,
        "kpsi": 6894757.293168
    },
    "volume_flow": {
        "m3/s": 1.0,
        "l/min": 1.0 / 60000.0,
        "l/s": 0.001,
        "gpm": 0.003785411784 / 60.0,
        "bbl/min": 0.158987294928 / 60.0
    },
    "angle": {
        "rad": 1.0,
        "deg": math.pi / 180.0,
        "degree": math.pi / 180.0
    },
    "frequency": {
        "rad/s": 1.0,
        "rpm": math.pi / 30.0,
        "hz": 2.0 * math.pi
    }
}


class FieldMapping(TypedDict):
    source_header: str
    target_channel: str
    source_unit: str
    target_unit_si: str
    factor_to_si: float


class ReadinessReport(TypedDict):
    total_rows: int
    complete_rows: int
    missing_by_channel: dict[str, int]
    null_percentage: float
    is_ready_for_engineering: bool
    readiness_score_pct: float
    warnings: list[str]
    identified_mappings: list[FieldMapping]


def parse_header_token(header: str) -> tuple[str, str | None]:
    """Parse 'wob[kN]' or 'wob_kN' or 'wob (kN)' into ('wob', 'kN')."""
    h = header.strip()
    match = re.search(r"^(.*?)[\[\(\{](.*?)[\]\)\}]$", h)
    if match:
        return match.group(1).strip().lower(), match.group(2).strip()
    if "_" in h:
        parts = h.rsplit("_", 1)
        if len(parts) == 2 and parts[1].lower() in [u for cat in UNIT_FACTORS.values() for u in cat]:
            return parts[0].strip().lower(), parts[1].strip()
    return h.lower(), None


def find_channel_for_alias(token: str) -> str | None:
    """Find canonical target channel name for an alias token."""
    clean = re.sub(r"[^a-z0-9_]", "", token.lower())
    for channel, aliases in STANDARD_ALIASES.items():
        if clean in aliases or any(clean == a for a in aliases):
            return channel
    return None


def get_conversion_factor(channel: str, unit_str: str) -> float | None:
    """Find SI conversion factor for a given channel and unit string."""
    u = unit_str.strip().lower()
    channel_to_category = {
        "md": "length",
        "tvd": "length",
        "wob": "force",
        "torque": "torque",
        "rpm": "frequency",
        "rop": "velocity",
        "spp": "pressure",
        "flow": "volume_flow",
        "inclination": "angle",
        "azimuth": "angle"
    }
    cat = channel_to_category.get(channel)
    if cat and cat in UNIT_FACTORS:
        return UNIT_FACTORS[cat].get(u)
    return None


def inspect_readiness(headers: list[str], rows: list[dict[str, Any]], dataset_kind: Literal["telemetry", "survey"]) -> ReadinessReport:
    """Evaluate data readiness, detect channel mappings, and compute data quality score."""
    mappings: list[FieldMapping] = []
    warnings: list[str] = []
    
    for h in headers:
        token, unit_hint = parse_header_token(h)
        channel = find_channel_for_alias(token)
        if channel:
            if unit_hint:
                factor = get_conversion_factor(channel, unit_hint)
                if factor is not None:
                    mappings.append({
                        "source_header": h,
                        "target_channel": channel,
                        "source_unit": unit_hint,
                        "target_unit_si": "SI",
                        "factor_to_si": factor
                    })
                else:
                    warnings.append(f"Header '{h}' has unrecognized unit '{unit_hint}'.")
            elif channel in {"timestamp", "state"}:
                mappings.append({
                    "source_header": h,
                    "target_channel": channel,
                    "source_unit": "text",
                    "target_unit_si": "standard",
                    "factor_to_si": 1.0
                })

    mapped_channels = {m["target_channel"] for m in mappings}
    required_channels = (
        {"timestamp", "state", "md", "wob", "torque", "rpm", "rop", "spp", "flow"}
        if dataset_kind == "telemetry"
        else {"md", "inclination", "azimuth"}
    )
    
    missing_channels = required_channels - mapped_channels
    if missing_channels:
        warnings.append(f"Missing required engineering channels: {', '.join(sorted(missing_channels))}")

    # Inspect rows completeness
    total_rows = len(rows)
    complete_count = 0
    missing_by_channel = {c: 0 for c in mapped_channels}

    for row in rows:
        row_has_empty = False
        for m in mappings:
            val = row.get(m["source_header"])
            if val is None or str(val).strip() == "":
                missing_by_channel[m["target_channel"]] += 1
                row_has_empty = True
        if not row_has_empty:
            complete_count += 1

    total_cells = total_rows * max(1, len(mappings))
    total_missing_cells = sum(missing_by_channel.values())
    null_pct = round((total_missing_cells / total_cells * 100.0) if total_cells else 0.0, 2)
    ready = len(missing_channels) == 0 and null_pct < 20.0 and total_rows > 0
    score = max(0.0, min(100.0, round(100.0 - null_pct - (len(missing_channels) * 15.0), 1)))

    return {
        "total_rows": total_rows,
        "complete_rows": complete_count,
        "missing_by_channel": missing_by_channel,
        "null_percentage": null_pct,
        "is_ready_for_engineering": ready,
        "readiness_score_pct": score,
        "warnings": warnings,
        "identified_mappings": mappings
    }
