"""Verification test suite for GD-A17 Formation Geomechanics & Fluid Thermodynamics."""
import pytest
from packages.engineering.geomechanics import (
    TriaxialCoreTest,
    StressCalibrationEvidence,
    GeomechanicsInput,
    calculate_geomechanics,
    calculate_in_situ_stresses,
    downhole_fluid_density,
)


@pytest.fixture
def sample_core_test():
    return TriaxialCoreTest(
        specimen_id="CORE-74A",
        confining_pressure_pa=20.0e6,
        peak_axial_stress_pa=85.0e6,
        pore_pressure_pa=10.0e6,
        cohesion_pa=12.0e6,
        friction_angle_deg=30.0,
        unconfined_compressive_strength_pa=41.5e6,
        tensile_strength_pa=4.0e6,
        youngs_modulus_pa=25.0e9,
        poissons_ratio=0.22,
        biot_coefficient=0.85,
        test_standard="ASTM D7012 / ISRM",
        certificate_id="CERT-GEO-2024-001",
    )


@pytest.fixture
def sample_stress_calibration():
    return StressCalibrationEvidence(
        method="XLOT",
        measured_shmin_gradient_sg=1.75,
        test_depth_tvd_m=2500.0,
        leak_off_pressure_gauge_pa=42.9e6,
        calibration_quality="verified_closure",
        evidence_note="Extended leak-off test with confirmed fracture closure pressure",
    )


def test_in_situ_stress_and_fluid_thermodynamics(sample_core_test, sample_stress_calibration):
    payload = GeomechanicsInput(
        study_name="Deep Sand Geomechanics",
        geometry_revision_id="geom-01",
        depth_datum="RKB",
        source_note="Well 101 Exploration Study",
        depth_tvd_m=2500.0,
        inclination_deg=0.0,
        azimuth_deg=0.0,
        azimuth_shmax_deg=90.0,
        overburden_gradient_sg=2.30,
        pore_pressure_sg=1.15,
        core_test=sample_core_test,
        stress_calibration=sample_stress_calibration,
        surface_temperature_c=15.0,
        geothermal_gradient_c_per_100m=3.0,
        base_mud_density_sg=1.25,
    )
    
    stresses = calculate_in_situ_stresses(payload)
    assert stresses["depth_tvd_m"] == 2500.0
    # Overburden Sv = 2.3 * 1000 * 9.80665 * 2500 = 56.388 MPa
    assert abs(stresses["overburden_sv_pa"] - 56.388e6) < 1e5
    # Sh calibrated by LOT (1.75 SG) = 1.75 * 1000 * 9.80665 * 2500 = 42.904 MPa
    assert abs(stresses["min_horizontal_sh_pa"] - 42.904e6) < 1e5

    # Fluid thermodynamics
    thermo = downhole_fluid_density(
        base_sg=1.25,
        depth_tvd_m=2500.0,
        surface_temp_c=15.0,
        geothermal_grad=3.0,
        compressibility=4e-10,
        thermal_exp=6e-4,
    )
    # Downhole temp = 15 + 3 * 25 = 90 deg C
    assert thermo["downhole_temperature_c"] == 90.0
    assert thermo["surface_density_kg_m3"] == 1250.0
    # Thermal expansion dominant over compressibility at high temperature
    assert thermo["downhole_density_kg_m3"] < 1250.0


def test_wellbore_stability_window_mohr_coulomb(sample_core_test, sample_stress_calibration):
    payload = GeomechanicsInput(
        study_name="Deep Sand Geomechanics",
        geometry_revision_id="geom-01",
        depth_datum="RKB",
        source_note="Well 101 Exploration Study",
        evidence_state="supplied",
        depth_tvd_m=2500.0,
        inclination_deg=0.0,
        azimuth_deg=0.0,
        azimuth_shmax_deg=90.0,
        overburden_gradient_sg=2.30,
        pore_pressure_sg=1.15,
        core_test=sample_core_test,
        stress_calibration=sample_stress_calibration,
        base_mud_density_sg=1.35,
        shear_failure_model="mohr_coulomb",
    )
    
    res = calculate_geomechanics(payload)
    assert res["status"] == "calculated"
    assert len(res["reasons"]) == 0

    window = res["stability_window"]
    assert window["safe_window_open"] is True
    assert window["collapse_mud_weight_sg"] >= payload.pore_pressure_sg
    assert window["fracture_mud_weight_sg"] > window["collapse_mud_weight_sg"]
    assert window["failure_criterion"] == "mohr_coulomb"


def test_mogi_coulomb_enhancement(sample_core_test, sample_stress_calibration):
    payload_mc = GeomechanicsInput(
        study_name="Deep Sand Geomechanics",
        geometry_revision_id="geom-01",
        depth_datum="RKB",
        source_note="Well 101 Study",
        evidence_state="supplied",
        depth_tvd_m=2500.0,
        inclination_deg=0.0,
        azimuth_deg=0.0,
        azimuth_shmax_deg=90.0,
        overburden_gradient_sg=2.30,
        pore_pressure_sg=1.15,
        core_test=sample_core_test,
        stress_calibration=sample_stress_calibration,
        base_mud_density_sg=1.35,
        shear_failure_model="mohr_coulomb",
    )
    res_mc = calculate_geomechanics(payload_mc)

    payload_mogi = payload_mc.model_copy(update={"shear_failure_model": "mogi_coulomb"})
    res_mogi = calculate_geomechanics(payload_mogi)

    # 3D Mogi-Coulomb accounts for intermediate stress -> lower collapse mud weight required
    mw_mc = res_mc["stability_window"]["collapse_mud_weight_sg"]
    mw_mogi = res_mogi["stability_window"]["collapse_mud_weight_sg"]
    assert mw_mogi < mw_mc


def test_withholding_when_core_test_or_lot_missing():
    # Case 1: missing core test
    payload = GeomechanicsInput(
        study_name="Missing Core Test",
        geometry_revision_id="geom-01",
        depth_datum="RKB",
        source_note="Well 101 Study",
        evidence_state="supplied",
        depth_tvd_m=2500.0,
        inclination_deg=0.0,
        azimuth_deg=0.0,
        azimuth_shmax_deg=90.0,
        overburden_gradient_sg=2.30,
        pore_pressure_sg=1.15,
        core_test=None,
        stress_calibration=None,
        base_mud_density_sg=1.20,
    )
    res = calculate_geomechanics(payload)
    assert res["status"] == "withheld"
    assert len(res["reasons"]) >= 2
    assert "Core triaxial test certificate" in res["reasons"][0]
    assert "In-situ stress calibration record" in res["reasons"][1]
    assert res["stability_window"] is None
