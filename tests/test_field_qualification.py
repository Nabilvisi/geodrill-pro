"""Automated test suite for Gate 3: Engineering Field Qualification & Calibration."""
import pytest
from packages.engineering.field_qualification import (
    run_volve_survey_benchmark,
    run_volve_hydraulics_benchmark,
    run_forge_dynamics_benchmark,
    run_flowloop_cuttings_calibration,
    run_downhole_sub_friction_validation,
    run_all_field_qualifications,
    VOLVE_15_9_F12_SURVEY_STATIONS,
    VOLVE_15_9_F12_HYDRAULICS,
    FORGE_16A_78_32_DYNAMICS,
    TUDRP_FLOWLOOP_BENCHMARKS,
    DOWNHOLE_SUB_FRICTION_BENCHMARK,
)


def test_volve_directional_survey_benchmark():
    """Verify Equinor Volve 15/9-F-12 minimum-curvature survey trajectory within 1.5% tolerance."""
    res = run_volve_survey_benchmark()
    assert res["passed"] is True
    assert res["max_tvd_error_pct"] < 1.5
    assert res["max_horizontal_error_pct"] < 1.5
    assert res["stations_evaluated"] >= 7
    assert res["equipment_control"] is False
    assert res["clearance_generated"] is False
    assert len(res["data_sha256"]) == 64


def test_volve_hydraulics_ecd_benchmark():
    """Verify Equinor Volve 15/9-F-12 annular pressure loss and ECD against DDR records within 1.5%."""
    res = run_volve_hydraulics_benchmark()
    assert res["passed"] is True
    assert res["ecd_error_pct"] <= 1.5
    assert res["calculated_ecd_kg_m3"] > 1350.0  # Above clean mud density due to friction & cuttings
    assert res["equipment_control"] is False
    assert len(res["data_sha256"]) == 64


def test_utah_forge_dynamics_benchmark():
    """Verify Utah FORGE 16A(78)-32 geothermal hard-rock dynamics & stick-slip screening."""
    res = run_forge_dynamics_benchmark()
    assert res["passed"] is False
    assert res["axial_band_matched"] is False
    assert res["torsional_frequency_error_pct"] <= 5.0
    assert res["severe_stick_slip_indicated"] is True
    assert res["torsional_stick_slip_propensity"] > 1.0
    assert len(res["bha_axial_resonance_modes_hz"]) >= 2
    assert res["equipment_control"] is False
    assert len(res["data_sha256"]) == 64


def test_tudrp_flowloop_cuttings_calibration():
    """Verify Tulsa University (TUDRP) empirical flow-loop cuttings transport calibration."""
    res = run_flowloop_cuttings_calibration()
    assert res["passed"] is True
    assert res["mean_bed_fraction_abs_error"] < 0.05
    assert res["mean_vcrit_error_pct"] < 8.0
    assert res["points_evaluated"] == len(TUDRP_FLOWLOOP_BENCHMARKS)
    assert res["equipment_control"] is False
    assert len(res["data_sha256"]) == 64


def test_downhole_sub_friction_validation():
    """Verify instrumented downhole sub friction factor inversion and hookload prediction."""
    res = run_downhole_sub_friction_validation()
    assert res["passed"] is False
    assert res["status"] == "withheld"
    assert res["max_hookload_err_pct"] is None
    assert res["calibrated_cased_friction"] is None
    assert res["calibrated_open_friction"] is None
    assert res["equipment_control"] is False
    assert len(res["data_sha256"]) == 64


def test_full_field_qualification_suite_and_constraints():
    """Verify complete Gate 3 qualification suite execution and strict governing constraints."""
    suite = run_all_field_qualifications()
    assert suite["qualification_gate"] == "Gate 3"
    assert suite["all_passed"] is False
    assert suite["overall_status"] == "INDEPENDENT_QUALIFICATION_PENDING"
    assert suite["field_qualified"] is False
    assert suite["missing_evidence"]
    assert suite["governing_constraints"]["si_physics_foundation"] is True
    assert suite["governing_constraints"]["equipment_control"] is False
    assert suite["governing_constraints"]["clearance_generated"] is False
    assert suite["third_party_engineering_sign_off"]["qualified_for_commercial_advisory"] is False
    assert suite["third_party_engineering_sign_off"]["reviewer"] is None

    # Check each individual benchmark status
    for b_name, b_res in suite["benchmarks"].items():
        assert b_res["independent_validation"] is False
        assert len(b_res["data_sha256"]) == 64


def test_numerical_agreement_cannot_create_independent_signoff(monkeypatch):
    import packages.engineering.field_qualification as module
    for function in ("run_volve_survey_benchmark", "run_volve_hydraulics_benchmark",
                     "run_forge_dynamics_benchmark", "run_flowloop_cuttings_calibration",
                     "run_downhole_sub_friction_validation"):
        monkeypatch.setattr(module, function, lambda: {"passed": True, "data_sha256": "a" * 64})
    suite = module.run_all_field_qualifications()
    assert suite["all_passed"] is True
    assert suite["field_qualified"] is False
    assert suite["overall_status"] == "INDEPENDENT_QUALIFICATION_PENDING"
    assert suite["third_party_engineering_sign_off"]["signed_assessment"] is None


def test_dossier_retains_failures_and_missing_signoff(tmp_path):
    from tools.generate_field_qualification_dossier import generate_dossier
    import json
    output = generate_dossier(tmp_path)
    assert "numerical_check_failed" in output.read_text(encoding="utf-8")
    assert "withheld" in output.read_text(encoding="utf-8")
    results = json.loads((tmp_path / "field-qualification-results.json").read_text())
    assert results["field_qualified"] is False
    assert results["benchmarks"]["utah_forge_dynamics"]["axial_band_matched"] is False
