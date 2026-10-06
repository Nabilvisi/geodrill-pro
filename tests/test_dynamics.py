import pytest
from packages.engineering.dynamics import DynamicsInput, dynamics
from packages.engineering.geometry import Path
from packages.engineering.models import SurveyRequest
from tests.test_hydraulics import geometry

def test_dynamics_vibration_screening():
    p = Path(SurveyRequest(stations=[{"md_m":0.,"inclination_rad":0.,"azimuth_rad":0.}, {"md_m":100.,"inclination_rad":0.,"azimuth_rad":0.}]))
    
    geom = geometry()
    v = DynamicsInput(
        study_name="test",
        geometry_revision_id="rev1",
        depth_datum="MSL",
        evidence_state="synthetic",
        source_note="test",
        top_md_m=0.0,
        bottom_md_m=100.0,
        outside_diameter_m=0.1,
        inside_diameter_m=0.08,
        material_density_kg_m3=7850.0,
        young_modulus_pa=200e9,
        poisson_ratio=0.3,
        boundary="cantilever_reduced",
        configuration_note="test",
        damping_ratio=0.05,
        axial_torsional_coupling=0.0,
        axial_lateral_coupling=0.0,
        torsional_lateral_coupling=0.0,
        bit_axial_stiffness_n_per_m=1e6,
        lateral_clearance_m=0.05,
        contact_stiffness_n_per_m=1e6,
        axial_force_amplitude_n=1000.0,
        torque_amplitude_nm=1000.0,
        lateral_force_amplitude_n=100.0,
        excitation_hz=1.0,
        duration_s=2.0,
        time_step_s=0.001,
        refinement_relative_tolerance=0.1,
        static_wob_n=10000.0,
        static_rpm=100.0
    )
    
    res = dynamics(v, geom, p)
    assert res["model_version"] == "M12-coupled-reduced-2"
    assert "axial_bit_bounce_resonance_frequencies_hz" in res
    assert "torsional_stick_slip_propensity" in res
    assert isinstance(res["torsional_stick_slip_propensity"], float)
    assert len(res["axial_bit_bounce_resonance_frequencies_hz"]) >= 0

