"""Integration tests for GeoDrill Pro v0.9 Wells, Fields, Wellbores, Targets, and Tree Hierarchy."""
import pytest
from fastapi.testclient import TestClient
from services.api.main import create_app
import tempfile
from pathlib import Path


@pytest.fixture
def client():
    with tempfile.TemporaryDirectory() as td:
        app = create_app(data_dir=Path(td), mode="local")
        with TestClient(app) as tc:
            tc.get("/api/session")
            yield tc


def test_v1_wells_hierarchy_full_lifecycle(client):
    headers = {"x-geodrill-client": "workstation"}

    # 1. Create a project
    proj_resp = client.post(
        "/api/v1/projects",
        json={
            "name": "Statfjord Field Development",
            "datum": "MSL",
            "well_name": "A-101",
            "default_crs": "EPSG:23031",
            "north_reference": "grid",
        },
        headers=headers,
    )
    assert proj_resp.status_code == 201
    project_id = proj_resp.json()["id"]

    # 2. Create Field
    field_resp = client.post(
        f"/api/v1/projects/{project_id}/fields",
        json={"name": "Statfjord North", "basin": "North Sea Viking Graben", "country": "Norway"},
        headers=headers,
    )
    assert field_resp.status_code == 201
    field_data = field_resp.json()
    assert field_data["name"] == "Statfjord North"
    field_id = field_data["id"]

    # List fields
    fields_list = client.get(f"/api/v1/projects/{project_id}/fields", headers=headers).json()
    assert len(fields_list) == 1
    assert fields_list[0]["id"] == field_id

    # 3. Create Well assigned to field
    well_resp = client.post(
        f"/api/v1/projects/{project_id}/wells",
        json={
            "name": "Well A-101",
            "uwi": "NOR-33/9-A-101",
            "field_id": field_id,
            "surface_latitude_deg": 61.25,
            "surface_longitude_deg": 1.85,
            "surface_elevation_m": 145.0,
            "rkb_elevation_m": 25.0,
        },
        headers=headers,
    )
    assert well_resp.status_code == 201
    well_data = well_resp.json()
    well_id = well_data["id"]
    assert well_data["field_id"] == field_id
    assert well_data["name"] == "Well A-101"

    # Create unassigned well (no field)
    unassigned_resp = client.post(
        f"/api/v1/projects/{project_id}/wells",
        json={"name": "Exploration Well Wildcat-1", "uwi": "NOR-33/9-X-01"},
        headers=headers,
    )
    assert unassigned_resp.status_code == 201
    unassigned_id = unassigned_resp.json()["id"]

    # Get well by ID
    get_well_resp = client.get(f"/api/v1/wells/{well_id}", headers=headers)
    assert get_well_resp.status_code == 200
    assert get_well_resp.json()["id"] == well_id

    # 4. Create Original Wellbore
    wb_resp = client.post(
        f"/api/v1/wells/{well_id}/wellbores",
        json={
            "name": "A-101 Main",
            "uwi": "NOR-33/9-A-101-WB01",
            "wellbore_type": "original",
            "kickoff_md_m": 0.0,
            "planned_td_m": 3450.0,
        },
        headers=headers,
    )
    assert wb_resp.status_code == 201
    wb_data = wb_resp.json()
    wb_id = wb_data["id"]
    assert wb_data["wellbore_type"] == "original"

    # Create Sidetrack Wellbore
    st_resp = client.post(
        f"/api/v1/wells/{well_id}/wellbores",
        json={
            "name": "A-101 Sidetrack 1",
            "wellbore_type": "sidetrack",
            "sidetrack_parent_id": wb_id,
            "kickoff_md_m": 2100.0,
            "planned_td_m": 3800.0,
        },
        headers=headers,
    )
    assert st_resp.status_code == 201
    assert st_resp.json()["sidetrack_parent_id"] == wb_id

    # List wellbores
    wb_list = client.get(f"/api/v1/wells/{well_id}/wellbores", headers=headers).json()
    assert len(wb_list) == 2

    # 5. Create Targets for the Wellbore
    target1_resp = client.post(
        f"/api/v1/wellbores/{wb_id}/targets",
        json={
            "name": "Brent Sand Top Target",
            "center_tvd_m": 2850.0,
            "center_north_m": 450.0,
            "center_east_m": 320.0,
            "radius_m": 45.0,
            "geometry_type": "circle",
            "tolerance_m": 10.0,
        },
        headers=headers,
    )
    assert target1_resp.status_code == 201
    t1_data = target1_resp.json()
    assert t1_data["name"] == "Brent Sand Top Target"
    assert t1_data["center_tvd_m"] == 2850.0

    target2_resp = client.post(
        f"/api/v1/wellbores/{wb_id}/targets",
        json={
            "name": "Statfjord Formation Target",
            "center_tvd_m": 3200.0,
            "center_north_m": 600.0,
            "center_east_m": 480.0,
            "radius_m": 60.0,
            "geometry_type": "rectangle",
            "tolerance_m": 15.0,
        },
        headers=headers,
    )
    assert target2_resp.status_code == 201

    # List targets
    targets_list = client.get(f"/api/v1/wellbores/{wb_id}/targets", headers=headers).json()
    assert len(targets_list) == 2

    # 6. Retrieve Complete Project Tree
    tree_resp = client.get(f"/api/v1/projects/{project_id}/tree", headers=headers)
    assert tree_resp.status_code == 200
    tree = tree_resp.json()

    assert "project" in tree
    assert tree["project"]["id"] == project_id

    # Verify Field -> Well -> Wellbore -> Target structure
    assert len(tree["fields"]) == 1
    field_tree = tree["fields"][0]
    assert field_tree["id"] == field_id
    assert len(field_tree["wells"]) == 1

    well_tree = field_tree["wells"][0]
    assert well_tree["id"] == well_id
    assert len(well_tree["wellbores"]) == 2

    main_wb = next(w for w in well_tree["wellbores"] if w["id"] == wb_id)
    assert len(main_wb["targets"]) == 2
    assert any(t["name"] == "Brent Sand Top Target" for t in main_wb["targets"])

    # Verify unassigned wells
    assert len(tree["unassigned_wells"]) == 1
    assert tree["unassigned_wells"][0]["id"] == unassigned_id


def test_v1_wells_not_found_handling(client):
    headers = {"x-geodrill-client": "workstation"}
    # Non-existent well
    resp = client.get("/api/v1/wells/non-existent-well-id", headers=headers)
    assert resp.status_code == 404
    body = resp.json()
    assert "detail" in body
    assert "error" in body

    # Non-existent wellbore
    resp_wb = client.get("/api/v1/wellbores/non-existent-wb-id", headers=headers)
    assert resp_wb.status_code == 404
