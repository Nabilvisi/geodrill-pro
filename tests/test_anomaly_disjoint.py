"""Verification test suite for GD-A16 Passive Real-Time Advisory & Disjoint Event Evaluation."""
import pytest
from packages.engineering.anomaly import AnomalyInput, anomaly
from packages.engineering.geometry import GeometryInput, Path
from tests.test_geometry_casing import geom, survey
from services.api.late_demo import late_template


def test_anomaly_disjoint_evaluation_window_and_safety_guardrails():
    d = late_template("anomaly", {"id": "f", "input": geom(), "result": {"total_depth_md_m": 1000.0}}, "synthetic")
    
    # Define disjoint evaluation window [5.0, 15.0] s
    d["evaluation_window_start_s"] = 5.0
    d["evaluation_window_end_s"] = 15.0
    
    v = AnomalyInput.model_validate(d)
    path = Path(survey([(0.0, 0.0, 0.0), (1000.0, 0.0, 0.0)]))
    res = anomaly(v, GeometryInput.model_validate(geom()), path)
    
    assert res["status"] != "withheld"
    # Strict safety boundaries
    assert res["equipment_control"] is False
    assert res["actuation_available"] is False
    assert res["equipment_authority"] == "none"
    
    # Disjoint evaluation metrics
    disjoint = res["event_evaluation"]["disjoint_evaluation"]
    assert disjoint is not None
    assert disjoint["window_start_s"] == 5.0
    assert disjoint["window_end_s"] == 15.0
    assert disjoint["evaluation_events_count"] >= 1
    assert disjoint["disjoint_matches"] >= 1
    assert disjoint["disjoint_sensitivity"] == 1.0


def test_anomaly_evaluation_window_validation():
    d = late_template("anomaly", {"id": "f", "input": geom(), "result": {"total_depth_md_m": 1000.0}}, "synthetic")
    
    # Missing end window
    d["evaluation_window_start_s"] = 5.0
    d["evaluation_window_end_s"] = None
    with pytest.raises(Exception):
        AnomalyInput.model_validate(d)

    # Inverted window
    d["evaluation_window_start_s"] = 15.0
    d["evaluation_window_end_s"] = 5.0
    with pytest.raises(Exception):
        AnomalyInput.model_validate(d)
