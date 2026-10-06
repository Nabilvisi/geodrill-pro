"""Comprehensive verification test suite for GD-A13: API TR 5C3 / ISO 10400 Casing Integrity & Load Envelopes."""
import math
import pytest
from fastapi.testclient import TestClient
from packages.engineering.models import SurveyRequest
from packages.engineering.geometry import GeometryInput, Path, geometry_result
from packages.engineering.casing_envelopes import (
    calculate_api_collapse_psi,
    api_collapse_rating,
    api_burst_rating,
    casing_envelopes,
    CasingEnvelopesInput,
    CasingIntegrityEvidence,
    PSI_TO_PA,
)
from services.api.main import create_app


def make_survey(stations):
    return SurveyRequest(stations=[{"md_m": m, "inclination_rad": i, "azimuth_rad": a} for m, i, a in stations])


def make_casing(name="Production Casing"):
    od = 0.244475
    id_m = 0.220500
    nom_wall = (od - id_m) / 2.0
    min_wall = nom_wall * 0.875  # 0.010489 m (API 12.5% tolerance)
    return {
        "name": name,
        "top_md_m": 0.0,
        "bottom_md_m": 2500.0,
        "outside_diameter_m": od,
        "inside_diameter_m": id_m,
        "minimum_wall_m": min_wall,
        "wall_loss_allowance_m": 0.001,   # 1 mm wear allowance
        "state": "installed",
        "grade": "N-80",
        "source": "Mill Test Certificate N80-47",
        "yield_strength_pa": 551.58e6,   # 80,000 psi
        "body_burst_pa": 47.37e6,
        "body_collapse_pa": 32.82e6,
        "body_tension_n": 4.0e6,
        "body_compression_n": 4.0e6,
        "connection_burst_pa": 47.37e6,
        "connection_collapse_pa": 32.82e6,
        "connection_tension_n": 3.8e6,
        "connection_compression_n": 3.8e6,
        "body_rating_source": "API 5CT Spec",
        "connection_rating_source": "API Buttress Spec"
    }


def make_geom():
    return {
        "survey_dataset_id": "fixture_survey",
        "datum": "RKB",
        "coordinate_reference": "UTM Zone 31N",
        "wellhead_north_m": 6000000.0,
        "wellhead_east_m": 500000.0,
        "wellhead_elevation_m": 25.0,
        "survey_quality_note": "Rig gyro and definitive MWD",
        "tool_to_bit_offset_m": 0.0,
        "formations": [{"name": "Balder", "top_tvd_m": 1200.0, "uncertainty_m": 15.0, "category": "formation", "source": "Seismic", "interpretation": "synthetic"}],
        "hole_sections": [{"name": "12-1/4 hole", "top_md_m": 0.0, "bottom_md_m": 2500.0, "diameter_m": 0.31115, "source": "Drill bit"}],
        "casings": [make_casing()]
    }


# ==============================================================================
# 1. API TR 5C3 / ISO 10400 Numerical Benchmarks
# ==============================================================================

def test_api_collapse_four_regimes_and_dt_limits():
    """Verify that API 5C3 Table 1 empirical coefficients and D/t limits match published standards."""
    # K-55: 55,000 psi yield
    k55_yp = 55000.0
    res_k55 = calculate_api_collapse_psi(k55_yp, dt=18.0)
    assert res_k55["A"] == pytest.approx(2.991, abs=0.005)
    assert res_k55["B"] == pytest.approx(0.05407, abs=0.0005)
    assert res_k55["C"] == pytest.approx(1206.2, abs=2.0)
    assert res_k55["dt_yp"] == pytest.approx(14.81, abs=0.05)
    assert res_k55["dt_pt"] == pytest.approx(25.01, abs=0.05)
    assert res_k55["dt_te"] == pytest.approx(37.21, abs=0.05)
    assert res_k55["regime"] == "plastic_collapse"
    assert res_k55["pressure_psi"] == pytest.approx(4957.8, rel=1e-3)

    # N-80: 80,000 psi yield
    n80_yp = 80000.0
    res_n80 = calculate_api_collapse_psi(n80_yp, dt=18.0)
    assert res_n80["A"] == pytest.approx(3.071, abs=0.005)
    assert res_n80["B"] == pytest.approx(0.06672, abs=0.0005)
    assert res_n80["C"] == pytest.approx(1955.3, abs=2.0)
    assert res_n80["dt_yp"] == pytest.approx(13.38, abs=0.05)
    assert res_n80["dt_pt"] == pytest.approx(22.47, abs=0.05)
    assert res_n80["dt_te"] == pytest.approx(31.02, abs=0.05)
    assert res_n80["regime"] == "plastic_collapse"
    assert res_n80["pressure_psi"] == pytest.approx(6354.9, rel=1e-3)

    # P-110: 110,000 psi yield
    p110_yp = 110000.0
    res_p110 = calculate_api_collapse_psi(p110_yp, dt=18.0)
    assert res_p110["dt_yp"] == pytest.approx(12.44, abs=0.05)
    assert res_p110["dt_pt"] == pytest.approx(20.41, abs=0.05)
    assert res_p110["dt_te"] == pytest.approx(26.22, abs=0.05)
    assert res_p110["regime"] == "plastic_collapse"


def test_api_collapse_regime_transitions():
    """Verify correct selection across yield, plastic, transition, and elastic collapse."""
    yp = 55000.0  # K-55

    # 1. Thick-wall yield collapse (D/t <= 14.81)
    res_yield = calculate_api_collapse_psi(yp, dt=10.0)
    assert res_yield["regime"] == "yield_collapse"
    expected_yield = 2.0 * yp * ((10.0 - 1.0) / (10.0**2))  # 9,900 psi
    assert res_yield["pressure_psi"] == pytest.approx(expected_yield, rel=1e-4)

    # 2. Plastic collapse (14.81 < D/t <= 25.01)
    res_plastic = calculate_api_collapse_psi(yp, dt=20.0)
    assert res_plastic["regime"] == "plastic_collapse"
    assert res_plastic["pressure_psi"] > 0

    # 3. Transition collapse (25.01 < D/t <= 37.21)
    res_trans = calculate_api_collapse_psi(yp, dt=30.0)
    assert res_trans["regime"] == "transition_collapse"
    assert res_trans["pressure_psi"] > 0

    # 4. Elastic collapse (D/t > 37.21)
    res_elastic = calculate_api_collapse_psi(yp, dt=45.0)
    assert res_elastic["regime"] == "elastic_collapse"
    expected_elastic = 46.95e6 / (45.0 * ((45.0 - 1.0)**2))
    assert res_elastic["pressure_psi"] == pytest.approx(expected_elastic, rel=1e-4)


def test_biaxial_axial_tension_reduction():
    """Verify ISO 10400 / API TR 5C3 Section 8 biaxial stress reduction factor."""
    yp_pa = 551.58e6  # 80,000 psi
    od = 0.244475
    wall = 0.011988

    # Zero axial stress -> factor = 1.0
    c_zero = api_collapse_rating(od, wall, yp_pa, axial_stress_pa=0.0)
    assert c_zero["biaxial_reduction_factor"] == pytest.approx(1.0, rel=1e-5)

    # Axial tension Sa / Yp = 0.5
    sa_pa = 0.5 * yp_pa
    c_tension = api_collapse_rating(od, wall, yp_pa, axial_stress_pa=sa_pa)
    # Expected reduction = sqrt(1 - 0.75*(0.5^2)) - 0.5*0.5 = sqrt(0.8125) - 0.25 = 0.651384
    expected_factor = math.sqrt(1.0 - 0.75 * 0.25) - 0.25
    assert c_tension["biaxial_reduction_factor"] == pytest.approx(expected_factor, rel=1e-5)
    assert c_tension["collapse_pressure_pa"] < c_zero["collapse_pressure_pa"]

    # At full yield tension Sa / Yp = 1.0 -> factor = 0.0
    c_yielded = api_collapse_rating(od, wall, yp_pa, axial_stress_pa=yp_pa)
    assert c_yielded["biaxial_reduction_factor"] == pytest.approx(0.0, abs=1e-6)
    assert c_yielded["collapse_pressure_pa"] == 0.0


def test_api_barlow_burst_and_lame():
    """Verify Barlow burst with 0.875 mill tolerance and Lamé thick-wall yield."""
    od = 0.244475
    wall = 0.011988
    yp_pa = 551.58e6

    res = api_burst_rating(od, wall, yp_pa)
    # Barlow API = 0.875 * 2 * Yp * t / D
    expected_barlow_api = 0.875 * (2.0 * yp_pa * wall) / od
    assert res["burst_barlow_api_pa"] == pytest.approx(expected_barlow_api, rel=1e-5)
    # Nominal Barlow = 2 * Yp * t / D
    expected_barlow_nom = (2.0 * yp_pa * wall) / od
    assert res["burst_barlow_nominal_pa"] == pytest.approx(expected_barlow_nom, rel=1e-5)
    assert res["burst_lame_pa"] > 0.0


# ==============================================================================
# 2. Operational Load Lines & Full Profile Scenarios
# ==============================================================================

def test_casing_envelopes_four_scenarios_and_governing_limits():
    """Verify calculation of burst kick, evacuation collapse, thermal, and running overpull profiles."""
    g_data = make_geom()
    req = make_survey([(0.0, 0.0, 0.0), (1000.0, 0.05, 0.0), (2500.0, 0.1, 0.0)])
    p = Path(req)
    g_input = GeometryInput.model_validate(g_data)

    payload = CasingEnvelopesInput(
        study_name="9-5/8 Intermediate Casing Integrity Review",
        geometry_revision_id="fixture_rev",
        depth_datum="RKB",
        casing_name="Production Casing",
        gas_gradient_pa_m=2260.0,
        evacuation_depth_tvd_m=1500.0,
        drilling_mud_density_kg_m3=1250.0,
        external_fluid_density_kg_m3=1050.0,
        overpull_force_n=250000.0,
        temperature_change_surface_c=25.0,
        temperature_change_shoe_c=55.0,
        burst_factor=1.1,
        collapse_factor=1.0,
        axial_factor=1.3,
        triaxial_factor=1.25,
        source_note="Engineering basis verification case"
    )

    result = casing_envelopes(payload, g_input, p)
    assert result["model"] == "api-5c3-casing-envelopes"
    assert result["model_version"] == "GD-A13-casing-envelopes-1"
    assert result["design_approval"] is False
    assert result["equipment_control"] is False

    profiles = result["load_profiles"]
    assert "burst_kick" in profiles
    assert "evacuation_collapse" in profiles
    assert "thermal_expansion" in profiles
    assert "running_overpull" in profiles

    # Profiles should have stations matching the requested station_count
    assert len(profiles["burst_kick"]) == payload.station_count
    assert len(profiles["evacuation_collapse"]) == payload.station_count

    # Check Burst Kick: surface internal pressure must be positive gas influx
    top_burst = profiles["burst_kick"][0]
    assert top_burst["internal_gauge_pa"] > 0
    assert top_burst["differential_burst_pa"] > 0
    assert top_burst["burst_margin_pa"] > 0

    # Check Evacuation Collapse: below fluid level, differential collapse increases
    shoe_collapse = profiles["evacuation_collapse"][-1]
    assert shoe_collapse["tvd_m"] == pytest.approx(2500.0, abs=10.0)
    assert shoe_collapse["axial_stress_pa"] >= 0.0

    # Governing summary
    gov = result["governing_summary"]
    assert gov["maximum_utilization"] > 0.0
    assert "governing_burst" in gov
    assert "governing_collapse" in gov
    assert "governing_running" in gov

    # Envelope curves
    curves = result["envelope_curves"]
    assert len(curves["biaxial_collapse_reduction"]) > 0
    assert len(curves["triaxial_vme_boundary"]) > 0


# ==============================================================================
# 3. Casing Integrity Evidence Binding & Withholding
# ==============================================================================

def test_casing_integrity_evidence_qualified():
    """Verify that valid mill inspection and pressure test records yield qualified status."""
    g_data = make_geom()
    req = make_survey([(0.0, 0.0, 0.0), (2500.0, 0.0, 0.0)])
    p = Path(req)
    g_input = GeometryInput.model_validate(g_data)

    evidence = CasingIntegrityEvidence(
        casing_name="Production Casing",
        mill_certificate_id="MILL-CERT-2026-N80-958",
        inspection_standard="API Spec 5CT 10th Ed",
        inspection_date="2026-01-15T00:00:00Z",
        inspection_expiry="2028-01-15T00:00:00Z",
        inspected_minimum_wall_m=0.0118,  # > 0.010988 m qualified
        inspected_yield_strength_pa=560e6, # > 551.58 MPa
        pressure_test_pressure_pa=40e6,
        pressure_test_date="2026-02-01T00:00:00Z",
        pressure_test_passed=True,
        masp_pa=35e6
    )

    payload = CasingEnvelopesInput(
        study_name="Integrity Verification Test",
        geometry_revision_id="fixture_rev",
        depth_datum="RKB",
        casing_name="Production Casing",
        integrity_evidence=evidence,
        source_note="Verified mill test evidence"
    )

    result = casing_envelopes(payload, g_input, p)
    assert result["integrity_verification"]["status"] == "qualified"
    assert len(result["integrity_verification"]["reasons"]) == 0


def test_casing_integrity_evidence_withholding_on_failed_test_or_wall_loss():
    """Verify explicit withholding when pressure test failed or inspected wall is below tolerance."""
    g_data = make_geom()
    req = make_survey([(0.0, 0.0, 0.0), (2500.0, 0.0, 0.0)])
    p = Path(req)
    g_input = GeometryInput.model_validate(g_data)

    failed_evidence = CasingIntegrityEvidence(
        casing_name="Production Casing",
        mill_certificate_id="MILL-DEFECT-001",
        inspection_standard="API Spec 5CT 10th Ed",
        inspection_date="2026-01-15T00:00:00Z",
        inspection_expiry="2028-01-15T00:00:00Z",
        inspected_minimum_wall_m=0.0080,  # Severely worn below 0.010988 m!
        inspected_yield_strength_pa=500e6, # Below 551.58 MPa!
        pressure_test_pressure_pa=20e6,
        pressure_test_date="2026-02-01T00:00:00Z",
        pressure_test_passed=False,        # Failed leak-off!
        masp_pa=35e6
    )

    payload = CasingEnvelopesInput(
        study_name="Defective Casing Test",
        geometry_revision_id="fixture_rev",
        depth_datum="RKB",
        casing_name="Production Casing",
        integrity_evidence=failed_evidence,
        source_note="Defective inspection evidence"
    )

    result = casing_envelopes(payload, g_input, p)
    assert result["integrity_verification"]["status"] == "withheld"
    assert result["status"] == "withheld"
    assert len(result["integrity_verification"]["reasons"]) >= 3


# ==============================================================================
# 4. API Endpoints, Lineage, and Scenario Comparison
# ==============================================================================

@pytest.fixture
def casing_api_setup(tmp_path):
    app = create_app(tmp_path)
    client = TestClient(app)
    client.get("/api/session")
    client.headers.update({"X-Geodrill-Client": "workstation"})

    # Create project
    proj = client.post("/api/projects", json={
        "name": "Casing Envelopes Project",
        "well_name": "Well GD-13",
        "datum": "RKB",
        "bit_diameter_m": 0.2159,
        "origin": "synthetic"
    }).json()
    base_url = f"/api/projects/{proj['id']}"

    # Import survey
    survey_text = "md[m],inclination[deg],azimuth[deg]\n0,0,0\n1000,10,45\n2500,20,45\n"
    ds = client.post(f"{base_url}/imports", data={"kind": "survey"}, files={"file": ("survey.csv", survey_text, "text/csv")}).json()

    # Save geometry
    g = make_geom()
    g["survey_dataset_id"] = ds["id"]
    rev = client.post(f"{base_url}/geometry", json={"geometry": g, "change_note": "Initial casing geometry"}).json()

    return client, proj, base_url, rev["id"], g


def test_api_casing_envelopes_endpoint_and_explanation(casing_api_setup):
    """Test full HTTP POST to /api/projects/{project_id}/calculations/casing-envelopes and verify provenance."""
    client, proj, base_url, rev_id, g = casing_api_setup

    payload = {
        "study_name": "API 5C3 Intermediate Casing Run",
        "geometry_revision_id": rev_id,
        "depth_datum": "RKB",
        "casing_name": "Production Casing",
        "gas_gradient_pa_m": 2260.0,
        "drilling_mud_density_kg_m3": 1200.0,
        "external_fluid_density_kg_m3": 1050.0,
        "overpull_force_n": 222400.0,
        "burst_factor": 1.1,
        "collapse_factor": 1.0,
        "axial_factor": 1.3,
        "triaxial_factor": 1.25,
        "station_count": 20,
        "evidence_state": "synthetic",
        "source_note": "Certified casing test run"
    }

    # 1. Post calculation
    resp = client.post(f"{base_url}/calculations/casing-envelopes", json=payload)
    assert resp.status_code == 200, resp.text
    calc = resp.json()
    assert calc["model"] == "casing-envelopes"
    assert calc["result"]["casing_name"] == "Production Casing"
    assert "load_profiles" in calc["result"]
    assert calc["result"]["geometry_revision_id"] == rev_id

    # 2. Check study explanation endpoint
    calc_id = calc["id"]
    expl_resp = client.get(f"{base_url}/calculations/{calc_id}/explanation")
    assert expl_resp.status_code == 200, expl_resp.text
    expl = expl_resp.json()
    assert expl["model"] == "casing-envelopes"
    assert any("API TR 5C3" in a for a in expl["assumptions"])
    assert expl["is_current"] is True

    # 3. Post an alternative scenario (e.g. higher mud density) and compare
    alt_payload = dict(payload, study_name="Heavy Mud Alternative", drilling_mud_density_kg_m3=1400.0)
    alt_resp = client.post(f"{base_url}/calculations/casing-envelopes", json=alt_payload)
    assert alt_resp.status_code == 200
    alt_calc = alt_resp.json()

    comp_resp = client.post(f"{base_url}/scenarios/compare", data={
        "baseline_id": calc["id"],
        "alternative_id": alt_calc["id"]
    })
    assert comp_resp.status_code == 200, comp_resp.text
    comp = comp_resp.json()
    assert comp["model"] == "casing-envelopes"
    assert comp["compatibility_status"] == "compatible"
    assert "drilling_mud_density_kg_m3" in comp["differing_inputs"]


def test_expired_inspection_withholds_and_vme_boundary_matches_lame():
    g_input = GeometryInput.model_validate(make_geom())
    p = Path(make_survey([(0.0, 0.0, 0.0), (2500.0, 0.0, 0.0)]))
    ev = CasingIntegrityEvidence(
        casing_name="Production Casing", mill_certificate_id="MC-1",
        inspection_date="2020-01-01", inspection_expiry="2022-01-01",
        inspected_minimum_wall_m=0.0118, inspected_yield_strength_pa=560e6,
        pressure_test_passed=True)
    payload = CasingEnvelopesInput(study_name="Expired evidence", geometry_revision_id="r",
                                   depth_datum="RKB", casing_name="Production Casing",
                                   integrity_evidence=ev, assessment_date="2026-10-06",
                                   source_note="Expiry check")
    r = casing_envelopes(payload, g_input, p)
    assert r["status"] == "withheld"
    assert any("expired" in x for x in r["integrity_verification"]["reasons"])
    # At zero axial stress the exact VME boundary must equal the closed-form Lamé burst.
    zero = next(x for x in r["envelope_curves"]["triaxial_vme_boundary"] if x["axial_stress_pa"] == 0.0)
    assert zero["internal_yield_pressure_pa"] == pytest.approx(r["api_ratings"]["burst_lame_pa"], rel=1e-9)
    # No hidden margins: defaults contribute zero kick margin and zero running drag.
    assert all(row["running_drag_n"] == 0.0 for row in r["load_profiles"]["running_overpull"])
