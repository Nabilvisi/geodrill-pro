"""Regression for the gaps found in the v0.9 deployment/architecture audit."""
import hashlib
import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from services.api.main import create_app
from services.api import auth, access
from services.application.wells import WellService
from packages.frontend import frontend_source_hash, verify_streamlit_component
from packages.version import APP_VERSION

H = {"X-Geodrill-Client": "workstation"}


@pytest.fixture
def client(tmp_path):
    with TestClient(create_app(tmp_path)) as client:
        client.get("/api/session")
        client.headers.update(H)
        yield client


def test_uncertainty_withholds_and_retains_kernel_reason(client):
    result = client.post("/api/v1/wellbores/research-preview/surveys/uncertainty", json={
        "stations": [{"md_m": 0, "inclination_deg": 0, "azimuth_deg": 0},
                     {"md_m": 100, "inclination_deg": 0, "azimuth_deg": 0}],
    })
    assert result.status_code == 200
    envelope = result.json()
    assert envelope["status"] == "withheld"
    assert envelope["result"]["withheld"]
    assert envelope["result"]["withholding_reason"]
    assert envelope["qualification"] == "internal_verification"


def test_proximity_runs_the_kernel_and_never_generates_clearance(client):
    stations = [{"md_m": 0, "inclination_deg": 0, "azimuth_deg": 0},
                {"md_m": 100, "inclination_deg": 0, "azimuth_deg": 0}]
    response = client.post("/api/v1/wellbores/research-preview/anticollision/proximity", json={
        "reference_stations": stations, "offset_stations": stations,
        "reference_start_nev": [0, 0, 0], "offset_start_nev": [20, 0, 0],
    })
    assert response.status_code == 200
    assert response.json()["result"]["min_c2c_distance_m"] == pytest.approx(20)
    assert response.json()["result"]["clearance_generated"] is False


@pytest.mark.parametrize("stations", [[], [{"md_m": 0}, {"md_m": 100}],
    [{"md_m": 0, "inc_deg": 0, "azi_deg": 0}, {"md_m": 100, "inc_deg": 0, "azi_deg": 0}]])
def test_trajectory_rejects_missing_units_and_angles(client, stations):
    response = client.post("/api/v1/wellbores/research-preview/directional/calculate",
                           json={"wellbore_id": "research-preview", "stations": stations})
    assert response.status_code == 422


def test_trajectory_rejects_conflicting_identity(client):
    response = client.post("/api/v1/wellbores/research-preview/directional/calculate", json={
        "wellbore_id": "other", "stations": [
            {"md_m": 0, "inc_rad": 0, "azi_rad": 0}, {"md_m": 100, "inc_rad": 0, "azi_rad": 0}]})
    assert response.status_code == 422


def test_geodesy_requires_declared_reference(client):
    assert client.post("/api/v1/geodesy/convert", json={"latitude_deg": 58, "longitude_deg": 2}).status_code == 422


def test_v1_team_routes_preserve_project_isolation(tmp_path):
    app = create_app(tmp_path, mode="team")
    store = app.state.store
    member = auth.create_user(store, "member", "Member", "engineer", "correct horse battery", actor="test")
    outsider = auth.create_user(store, "outsider", "Outsider", "engineer", "correct horse battery", actor="test")
    project = store.create_project({"name": "Private project"})
    access.add_member(store, project["id"], member["id"], "test")
    svc = WellService(store)
    well = svc.create_well(project["id"], "Private well")
    wb = svc.create_wellbore(well["id"], "Private wellbore")
    token, _ = auth.login(store, "outsider", "correct horse battery")
    with TestClient(app) as client:
        client.headers.update({"Authorization": "Bearer " + token})
        assert client.get("/api/v1/projects").json() == []
        for path in [f"/api/v1/projects/{project['id']}/tree", f"/api/v1/wells/{well['id']}",
                     f"/api/v1/wellbores/{wb['id']}/targets"]:
            assert client.get(path).status_code == 404
        assert client.post(f"/api/v1/wellbores/{wb['id']}/targets", json={"name":"Forbidden", "center_tvd_m":100}).status_code == 404
        created = client.post("/api/v1/projects", json={"name":"Mine", "datum":"RKB"})
        assert created.status_code == 201
        assert client.get(f"/api/v1/projects/{created.json()['id']}/tree").status_code == 200
        assert len(client.get("/api/v1/projects").json()) == 1


def component_fixture(root):
    source=root/"apps/desktop/src/main.tsx"
    source.parent.mkdir(parents=True)
    source.write_text("workstation source",encoding="utf-8")
    component=root/"apps/streamlit/component"
    component.mkdir(parents=True)
    asset=component/"app.js"
    asset.write_bytes(b"built workstation")
    manifest={"version":APP_VERSION,"frontend_source_sha256":frontend_source_hash(root),
              "assets":[{"path":"app.js","sha256":hashlib.sha256(asset.read_bytes()).hexdigest()}]}
    (component/"manifest.json").write_text(json.dumps(manifest),encoding="utf-8")
    return source,asset,component,manifest


def test_streamlit_rejects_changed_source_with_unchanged_version(tmp_path):
    source,_,_,_=component_fixture(tmp_path)
    assert verify_streamlit_component(tmp_path)["version"] == APP_VERSION
    source.write_text("new source, stale build",encoding="utf-8")
    with pytest.raises(ValueError,match="stale"):
        verify_streamlit_component(tmp_path)


def test_streamlit_rejects_corrupt_assets(tmp_path):
    _,asset,_,_=component_fixture(tmp_path)
    asset.write_bytes(b"corrupted")
    with pytest.raises(ValueError,match="integrity"):
        verify_streamlit_component(tmp_path)


def test_streamlit_rejects_manifest_escape(tmp_path):
    _,_,component,manifest=component_fixture(tmp_path)
    manifest["assets"][0]["path"]="../../outside.js"
    (component/"manifest.json").write_text(json.dumps(manifest),encoding="utf-8")
    with pytest.raises(ValueError,match="path"):
        verify_streamlit_component(tmp_path)


def test_checked_in_streamlit_component_matches_current_source():
    assert verify_streamlit_component(Path(__file__).resolve().parents[1])["version"] == APP_VERSION


def test_source_fingerprint_is_portable_across_windows_and_linux(tmp_path):
    source,_,_,_=component_fixture(tmp_path)
    source.write_bytes(b"first\r\nsecond\r\n")
    original=frontend_source_hash(tmp_path)
    source.write_bytes(b"first\nsecond\n")
    assert frontend_source_hash(tmp_path)==original


def test_v1_geomechanics_uses_saved_geometry_and_report_evidence():
    from apps.streamlit.cloud import Workspace
    workspace=Workspace()
    try:
        project=next(p for p in workspace.call("GET","/api/projects") if p["name"].startswith("Cloud verification"))
        base="/api/projects/"+project["id"]
        payload=next(c["inputs_si"] for c in workspace.call("GET",base+"/calculations") if c["model"]=="geomechanics")
        svc=WellService(workspace.app.state.store)
        well=svc.create_well(project["id"],"Verification well")
        wb=svc.create_wellbore(well["id"],"Main bore")
        response=workspace.client.post(f"/api/v1/wellbores/{wb['id']}/geomechanics/cases",json=payload)
        assert response.status_code==200,response.text
        envelope=response.json()
        assert envelope["geometry_revision_id"]==payload["geometry_revision_id"]
        assert envelope["result"]["input_document_matches_current"]
        assert envelope["result"]["clearance_generated"] is False
        saved=next(c for c in workspace.call("GET",base+"/calculations") if c["id"]==envelope["calculation_id"])
        report=workspace.call("POST",base+"/reports")
        snapshot=workspace.call("GET",base+"/reports/"+report["id"])["snapshot"]
        assert saved in snapshot["calculations"]
        assert snapshot["application_version"]==APP_VERSION
        from services.api import demo
        geometry=workspace.call("GET",base+"/engineering-revisions?module=M1")[0]
        torque=demo.research_template("torque-drag",geometry,"synthetic")
        torque_response=workspace.client.post(f"/api/v1/wellbores/{wb['id']}/torque-drag/cases",json=torque)
        assert torque_response.status_code==200,torque_response.text
        torque_envelope=torque_response.json()
        assert torque_envelope["result"]["geometry_revision_id"]==geometry["id"]
        assert torque_envelope["result"]["equipment_authority"]=="none"
        assert any(c["id"]==torque_envelope["calculation_id"] for c in workspace.call("GET",base+"/calculations"))
        wrong=dict(payload,geometry_revision_id="foreign-revision")
        assert workspace.client.post(f"/api/v1/wellbores/{wb['id']}/geomechanics/cases",json=wrong).status_code==400
    finally:
        workspace.close()


def test_hierarchy_rejects_cross_project_field_and_cross_well_parent(client):
    store=client.app.state.store
    a=store.create_project({"name":"A"});b=store.create_project({"name":"B"})
    svc=WellService(store)
    foreign=svc.create_field(b["id"],"Foreign")
    with pytest.raises(ValueError,match="Field"):
        svc.create_well(a["id"],"Wrong",field_id=foreign["id"])
    wa=svc.create_well(a["id"],"WA");wb=svc.create_well(b["id"],"WB")
    parent=svc.create_wellbore(wb["id"],"Parent")
    with pytest.raises(ValueError,match="Sidetrack"):
        svc.create_wellbore(wa["id"],"Cross well",sidetrack_parent_id=parent["id"])
