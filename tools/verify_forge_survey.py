"""Compare the production trajectory kernel to the original FORGE published survey.

This is a source-backed numerical reproduction, not operational qualification.
Published printed angles are rounded to 0.01 degrees. A 1 m absolute 3D
coordinate tolerance is declared before comparison, allowing accumulated printed
angle/coordinate rounding. Every station is compared, with no exclusions.
"""
import hashlib
import json
import math
from pathlib import Path
import sys
import zipfile
from defusedxml import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from packages.engineering.models import Survey, SurveyRequest
from packages.engineering.physics import minimum_curvature

SOURCE_SHA256 = "ad03773329769f702f748c96244a9e1cba16cd1d762d4e8b93b8c8fea9d36b8d"
SOURCE_URL = "https://gdr.openei.org/files/1283/16A%2878%29-32%20Survey.xlsx"
SOURCE = ROOT / "docs" / "evidence" / "sources" / "forge-16a-survey.xlsx"
US_FOOT_M = 1200 / 3937
ABS_3D_TOLERANCE_M = 1.0
NS = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def read_source(source: Path = SOURCE) -> list[dict]:
    if hashlib.sha256(source.read_bytes()).hexdigest() != SOURCE_SHA256:
        raise ValueError("Original FORGE source hash mismatch")
    with zipfile.ZipFile(source) as archive:
        sheet = ET.fromstring(archive.read("xl/worksheets/sheet1.xml"))
    stations = []
    for row in sheet.findall(".//s:sheetData/s:row", NS):
        number = int(row.attrib["r"])
        if not 77 <= number <= 498:
            continue
        cells = {}
        for cell in row.findall("s:c", NS):
            value = cell.find("s:v", NS)
            if value is not None and cell.get("t") != "s":
                cells[cell.attrib["r"]] = float(value.text)
        # Use raw XML numeric values: the source has date-formatted numeric cells.
        expected = number - 76
        if cells.get(f"B{number}") != expected:
            raise ValueError("FORGE station sequence incomplete")
        stations.append({
            "source_row": number, "sequence": expected,
            "md_m": cells[f"C{number}"] * US_FOOT_M,
            "inclination_rad": math.radians(cells[f"D{number}"]),
            "azimuth_rad": math.radians(cells[f"E{number}"]),
            "reference_tvd_m": cells[f"G{number}"] * US_FOOT_M,
            "reference_north_m": cells[f"I{number}"] * US_FOOT_M,
            "reference_east_m": cells[f"J{number}"] * US_FOOT_M,
        })
    if len(stations) != 422:
        raise ValueError("Expected all 422 published stations")
    return stations


def verify(source: Path = SOURCE) -> dict:
    references = read_source(source)
    request = SurveyRequest(stations=[Survey(**{key: row[key] for key in ("md_m", "inclination_rad", "azimuth_rad")}) for row in references])
    computed = minimum_curvature(request)
    comparisons = []
    for actual, reference in zip(computed, references, strict=True):
        deltas = {axis: actual[f"{axis}_m"] - reference[f"reference_{axis}_m"] for axis in ("tvd", "north", "east")}
        error = math.sqrt(sum(value ** 2 for value in deltas.values()))
        comparisons.append({"source_row": reference["source_row"], "md_m": actual["md_m"],
                            "deltas_m": deltas, "error_3d_m": error, "passed": error <= ABS_3D_TOLERANCE_M})
    return {
        "benchmark": "FORGE 16A(78)-32 published trajectory reproduction",
        "source_url": SOURCE_URL, "source_sha256": SOURCE_SHA256,
        "doi": "10.15121/1776602", "license": "CC BY 4.0",
        "attribution": "McLennan, John, University of Utah Energy and Geoscience Institute, 2021. Utah FORGE: Well 16A(78)-32 Drilling Data. Geothermal Data Repository.",
        "sheet": "Sheet1", "source_rows": "77-498", "source_columns": "C:MD,D:Incl,E:Az,G:TVD,I:North,J:East",
        "native_length_unit": "US survey foot (usft declared in source report)",
        "length_conversion_m_per_unit": US_FOOT_M,
        "absolute_3d_tolerance_m": ABS_3D_TOLERANCE_M,
        "stations_evaluated": len(comparisons), "stations_excluded": 0,
        "max_3d_error_m": max(row["error_3d_m"] for row in comparisons),
        "passed": all(row["passed"] for row in comparisons),
        "field_qualified": False, "equipment_control": False, "clearance_generated": False,
        "comparisons": comparisons,
    }


if __name__ == "__main__":
    result = verify()
    output = ROOT / "docs" / "evidence" / "forge-survey-verification.json"
    output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in result.items() if key != "comparisons"}, indent=2))
    raise SystemExit(0 if result["passed"] else 1)
