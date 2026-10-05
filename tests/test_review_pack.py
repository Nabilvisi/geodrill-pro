import pytest
from packages.engineering.review_pack import (
    build_programme_pack,
    export_pack_to_html,
    export_pack_to_csv,
    WATERMARK_NOTICE,
)


def test_build_programme_pack_structure():
    sections = [
        {"section_name": "12-1/4 in Intermediate", "hole_size_in": 12.25, "casing_od_in": 9.625, "top_depth_m": 1200, "bottom_depth_m": 2500, "mud_type": "WBM", "mud_density_sg": 1.25}
    ]
    activities = [
        {"sequence": 1, "phase": "Drilling", "description": "Drill 12-1/4 in hole to TD 2500 m", "duration_hrs": 36.0, "planned_depth_m": 2500}
    ]
    hazards = [
        {"hazard": "Shallow Gas", "severity": "High", "consequence": "Kick", "mitigation": "Weighted mud and dynamic kill ready", "barrier_status": "Active"}
    ]
    assumptions = [{"category": "Pore Pressure", "statement": "Normal hydrostatic gradient 0.44 psi/ft"}]
    selected_studies = [{"model": "M06", "id": "m6-study-1"}]
    baseline_study = {"id": "base-1", "model": "M06", "inputs_si": {"flow_rate": 0.03}, "result": {"ecd_sg": 1.28}}
    alternative_study = {"id": "alt-1", "model": "M06", "inputs_si": {"flow_rate": 0.035}, "result": {"ecd_sg": 1.32}}

    pack = build_programme_pack(
        project_id="proj-123",
        programme_title="Well Alpha Drilling Programme",
        sections=sections,
        activities=activities,
        hazards=hazards,
        assumptions=assumptions,
        selected_studies=selected_studies,
        baseline_study=baseline_study,
        alternative_study=alternative_study,
    )

    assert pack["project_id"] == "proj-123"
    assert pack["title"] == "Well Alpha Drilling Programme"
    assert pack["watermark"] == WATERMARK_NOTICE
    assert len(pack["sections"]) == 1
    assert len(pack["activities"]) == 1
    assert len(pack["hazards"]) == 1
    assert pack["scenario_comparison"] is not None
    assert "ecd_sg" in pack["scenario_comparison"]["outcome_deltas"]

    # Check qualification cards resolved for M06
    qual = pack["qualification_ledger"]
    assert any(q["module_id"] == "M06" for q in qual)
    m6_card = next(q for q in qual if q["module_id"] == "M06")
    assert m6_card["qualification_status"] == "software_verified"
    assert "governing_physics" in m6_card


def test_export_pack_to_html():
    pack = build_programme_pack(
        project_id="proj-1",
        programme_title="Test HTML Export",
        sections=[{"section_name": "Surface", "hole_size_in": 17.5, "casing_od_in": 13.375, "top_depth_m": 0, "bottom_depth_m": 800, "mud_type": "Spud Mud", "mud_density_sg": 1.10}],
        activities=[{"sequence": 1, "phase": "Spud", "description": "Spud well", "duration_hrs": 12.0, "planned_depth_m": 800}],
        hazards=[{"hazard": "Boulders", "severity": "Medium", "consequence": "Vibration", "mitigation": "Controlled ROP", "barrier_status": "Active"}],
        assumptions=[],
        selected_studies=[{"model": "M01"}],
    )

    html = export_pack_to_html(pack)
    assert "<!DOCTYPE html>" in html
    assert "Test HTML Export" in html
    assert WATERMARK_NOTICE in html
    assert "Surface" in html
    assert "Boulders" in html
    assert "M01" in html


def test_export_pack_to_csv():
    pack = build_programme_pack(
        project_id="proj-1",
        programme_title="Test CSV Export",
        sections=[{"section_name": "Production", "hole_size_in": 8.5, "casing_od_in": 7.0, "top_depth_m": 2500, "bottom_depth_m": 3500, "mud_type": "OBM", "mud_density_sg": 1.40}],
        activities=[{"sequence": 1, "phase": "Drilling", "description": "Drill to TD", "duration_hrs": 48.0, "planned_depth_m": 3500}],
        hazards=[{"hazard": "Losses", "severity": "High", "consequence": "Mud Loss", "mitigation": "LCM pill on stand-by", "barrier_status": "Active"}],
        assumptions=[],
        selected_studies=[],
    )

    csv_act = export_pack_to_csv(pack, "activities")
    assert "Drill to TD" in csv_act
    assert "48.0" in csv_act

    csv_sec = export_pack_to_csv(pack, "sections")
    assert "Production" in csv_sec
    assert "OBM" in csv_sec

    csv_haz = export_pack_to_csv(pack, "hazards")
    assert "Losses" in csv_haz
    assert "High" in csv_haz

    with pytest.raises(ValueError):
        export_pack_to_csv(pack, "unknown_component")


def test_api_review_pack_endpoints(tmp_path):
    from fastapi.testclient import TestClient
    from services.api.main import create_app
    app = create_app(data_dir=tmp_path)
    client = TestClient(app)
    client.headers["X-Geodrill-Client"] = "workstation"
    client.get("/api/session")

    # 1. Use synthetic demo project
    r_proj = client.post("/api/demo")
    assert r_proj.status_code == 201
    pid = r_proj.json()["id"]

    # 2. Build review pack via API
    payload = {
        "title": "Well P-1 Programme Pack",
        "sections": [{"section_name": "Surface", "hole_size_in": 17.5, "casing_od_in": 13.375, "top_depth_m": 0, "bottom_depth_m": 600, "mud_type": "WBM", "mud_density_sg": 1.15}],
        "activities": [{"sequence": 1, "phase": "Drill", "description": "Drill surface hole", "duration_hrs": 24, "planned_depth_m": 600}],
        "hazards": [{"hazard": "Shallow water flow", "severity": "Medium", "consequence": "Dilution", "mitigation": "Heavy pill", "barrier_status": "Ready"}],
        "selected_studies": [{"model": "M01"}],
    }
    r_pack = client.post(f"/api/projects/{pid}/review-pack", json=payload)
    assert r_pack.status_code == 200
    pack_data = r_pack.json()
    assert pack_data["title"] == "Well P-1 Programme Pack"
    assert pack_data["watermark"] == WATERMARK_NOTICE

    # 3. Export HTML via API
    r_html = client.post(f"/api/projects/{pid}/review-pack/export/html", json=pack_data)
    assert r_html.status_code == 200
    assert "text/html" in r_html.headers["content-type"]
    assert "Well P-1 Programme Pack" in r_html.text

    # 4. Export CSV via API
    r_csv = client.post(f"/api/projects/{pid}/review-pack/export/csv", json={"pack": pack_data, "component": "activities"})
    assert r_csv.status_code == 200
    assert "text/csv" in r_csv.headers["content-type"]
    assert "Drill surface hole" in r_csv.text