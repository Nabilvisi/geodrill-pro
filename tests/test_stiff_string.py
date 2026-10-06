import pytest
from packages.engineering.torque_drag import torque_drag
from packages.engineering.geometry import Path
from packages.engineering.models import SurveyRequest
from tests.test_hydraulics import geometry
from tests.test_research_modules import td


def arc():
    return Path(SurveyRequest(stations=[{"md_m": 0., "inclination_rad": 0., "azimuth_rad": 0.},
                                        {"md_m": 1000., "inclination_rad": 0.5, "azimuth_rad": 0.}]))


def test_stiff_string_model_version_and_profile():
    res = torque_drag(td(model="stiff_string"), geometry(), arc())
    assert res["model_version"] == "GD-A12-stiff-string-1"
    assert res["profile"]


def test_stiff_equals_soft_on_constant_curvature_arc():
    # Analytical property (declared tolerance 1e-6 relative): the bending shear-gradient term
    # EI*kappa'' vanishes on a single minimum-curvature arc, so stiff == soft there.
    soft = torque_drag(td(model="soft_string"), geometry(), arc())
    stiff = torque_drag(td(model="stiff_string"), geometry(), arc())
    assert stiff["hookload_n"] == pytest.approx(soft["hookload_n"], rel=1e-6)


def test_torque_drag_friction_calibration_with_holdout():
    # Base input
    base_in = td(model="soft_string")
    v_dict = base_in.model_dump()
    
    # Run uncalibrated first to find baseline hookload
    base_res = torque_drag(base_in, geometry(), arc())
    base_hookload = base_res["hookload_n"]

    # Provide synthetic observations reflecting slightly higher friction (+0.05)
    # 2 training points, 1 holdout point
    v_dict["calibration_points"] = [
        {
            "md_m": 1000.0,
            "operation": "pickup",
            "measured_hookload_n": base_hookload * 1.05,
            "measured_torque_nm": 0.0,
            "split": "train",
            "provenance_note": "Rig sensor rig 101 run 1"
        },
        {
            "md_m": 1000.0,
            "operation": "pickup",
            "measured_hookload_n": base_hookload * 1.045,
            "measured_torque_nm": 0.0,
            "split": "train",
            "provenance_note": "Rig sensor rig 101 run 2"
        },
        {
            "md_m": 1000.0,
            "operation": "pickup",
            "measured_hookload_n": base_hookload * 1.048,
            "measured_torque_nm": 0.0,
            "split": "holdout",
            "provenance_note": "Independent validation well run 3"
        }
    ]
    
    from packages.engineering.torque_drag import TorqueDragInput
    cal_res = torque_drag(TorqueDragInput.model_validate(v_dict), geometry(), arc())
    assert cal_res["calibration_performed"] is True
    cal_info = cal_res["calibration"]
    assert cal_info["status"] == "calibrated_with_holdout"
    assert cal_info["training_points_count"] == 2
    assert cal_info["holdout_points_count"] == 1
    assert cal_info["holdout_rmse_n"] >= 0.0
    assert cal_info["calibrated_friction_delta"] > 0.0


def test_torque_drag_friction_calibration_insufficient_points_withheld():
    base_in = td(model="soft_string")
    v_dict = base_in.model_dump()
    v_dict["calibration_points"] = [
        {
            "md_m": 1000.0,
            "operation": "pickup",
            "measured_hookload_n": 500000.0,
            "split": "train",
            "provenance_note": "Single observation only"
        }
    ]
    from packages.engineering.torque_drag import TorqueDragInput
    res = torque_drag(TorqueDragInput.model_validate(v_dict), geometry(), arc())
    assert res["calibration_performed"] is False
    assert res["calibration"]["status"] == "withheld"
    assert "at least 2 training observations" in res["reasons"][-1]

