"""Verification test suite for GD-A15 BHA/Bit Wear Planning & IADC Dull Grading Mechanics."""
import pytest
from packages.engineering.bit_condition import (
    BitInput,
    BitRun,
    bit_condition,
    parse_iadc_grade,
)
from packages.engineering.geometry import GeometryInput, Path
from tests.test_geometry_casing import geom, survey


def geometry():
    return GeometryInput.model_validate(geom())


def path():
    return Path(survey([(0.0, 0.0, 0.0), (1000.0, 0.0, 0.0)]))


def test_parse_iadc_grade_standard_8_position():
    # 1-2-BT-S-X-I-NO-TD
    res = parse_iadc_grade("1-2-BT-S-X-I-NO-TD")
    assert res is not None
    assert res["inner_cutting_structure"] == 1
    assert res["outer_cutting_structure"] == 2
    assert res["dull_characteristic"] == "BT"
    assert res["location"] == "S"
    assert res["bearing_seals"] == "X"
    assert res["gauge"] == "I"
    assert res["other_characteristic"] == "NO"
    assert res["reason_pulled"] == "TD"
    assert res["normalized_cutter_wear"] == (1 + 2) / 16.0


def test_parse_iadc_grade_empty_or_none():
    assert parse_iadc_grade(None) is None
    assert parse_iadc_grade("") is None


def test_bit_wear_progression_calibrated_with_iadc():
    from services.api.late_demo import late_template
    d = late_template("bit-condition", {"id": "f", "input": geom(), "result": {"total_depth_md_m": 1000.0}}, "synthetic")
    
    # Supply IADC dull grades for eligible runs
    d["runs"][0]["inspection_grade"] = "1-1-BT-S-X-I-NO-TD"
    d["runs"][1]["inspection_grade"] = "2-2-WT-A-X-I-NO-PR"
    d["runs"][2]["inspection_grade"] = "3-4-CT-G-X-I-NO-HR"
    
    v = BitInput.model_validate(d)
    res = bit_condition(v, geometry(), path())
    
    assert res["calibration_performed"] is True
    wear = res["iadc_wear_mechanics"]
    assert wear["status"] == "calibrated_iadc"
    assert wear["inspected_records_count"] >= 2
    assert wear["average_wear_rate_per_hour"] > 0.0
    assert 0 <= wear["predicted_inner_wear_grade"] <= 8
    assert 0 <= wear["predicted_outer_wear_grade"] <= 8


def test_bit_wear_progression_withheld_when_no_iadc_grades():
    from services.api.late_demo import late_template
    d = late_template("bit-condition", {"id": "f", "input": geom(), "result": {"total_depth_md_m": 1000.0}}, "synthetic")
    
    # Set inspection_grade to non-IADC arbitrary text without numbers
    for r in d["runs"]:
        if r.get("inspection_grade"):
            r["inspection_grade"] = "Worn bit in fair shape"
            
    v = BitInput.model_validate(d)
    res = bit_condition(v, geometry(), path())
    
    assert res["calibration_performed"] is False
    wear = res["iadc_wear_mechanics"]
    assert wear["status"] == "withheld"
    assert "At least 2 recovered bits with inspected IADC dull grades" in wear["withholding_reason"]
