"""Integration tests for GeoDrill Pro v0.9 modular API routers and calculation envelopes."""
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
            # Initialize local session
            tc.get("/api/session")
            yield tc


def test_v1_projects_lifecycle(client):
    headers = {"x-geodrill-client": "workstation"}
    # Create project via v1 endpoint
    resp = client.post(
        "/api/v1/projects",
        json={
            "name": "North Sea Workstation Project",
            "datum": "ED50",
            "well_name": "Well-15A",
            "default_crs": "EPSG:23031",
            "north_reference": "grid",
        },
        headers=headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "North Sea Workstation Project"
    project_id = data["id"]

    # List projects
    list_resp = client.get("/api/v1/projects", headers=headers)
    assert list_resp.status_code == 200
    projects = list_resp.json()
    assert any(p["id"] == project_id for p in projects)

    # Get single project
    get_resp = client.get(f"/api/v1/projects/{project_id}", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["name"] == "North Sea Workstation Project"


def test_v1_directional_calculate(client):
    headers = {"x-geodrill-client": "workstation"}
    stations = [
        {"md_m": 0.0, "inc_rad": 0.0, "azi_rad": 0.0},
        {"md_m": 500.0, "inc_rad": 0.1, "azi_rad": 0.785},
        {"md_m": 1200.0, "inc_rad": 0.35, "azi_rad": 0.785},
    ]
    resp = client.post(
        "/api/v1/wellbores/wb-101/directional/calculate",
        json={"wellbore_id": "wb-101", "stations": stations},
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "trajectory" in body
    assert "envelope" in body
    assert body["trajectory"]["total_md_m"] == 1200.0
    assert body["envelope"]["model"] == "directional.minimum_curvature"
    assert body["envelope"]["status"] == "calculated"
    assert len(body["trajectory"]["stations"]) == 3


def test_v1_geodesy_convert(client):
    headers = {"x-geodrill-client": "workstation"}
    resp = client.post(
        "/api/v1/geodesy/convert",
        json={
            "latitude_deg": 58.0,
            "longitude_deg": 2.0,
            "crs_code": "EPSG:32631",
            "datum": "WGS84",
        },
        headers=headers,
    )
    assert resp.status_code == 200
    result = resp.json()
    assert result["valid"] is True
    assert "easting_m" in result
    assert "northing_m" in result


def test_v1_pressure_balance_case(client):
    headers = {"x-geodrill-client": "workstation"}
    payload = {
        "tvd_m": 2500.0,
        "density_kg_m3": 1200.0,
        "surface_gauge_pa": 0.0,
        "annular_loss_pa": 1.5e6,
        "pore_gauge_pa": 2.5e7,
        "fracture_gauge_pa": 3.8e7,
        "regime": "steady_single_phase",
    }
    resp = client.post(
        "/api/v1/wellbores/wb-101/hydraulics/pressure-balance",
        json=payload,
        headers=headers,
    )
    assert resp.status_code == 200
    env = resp.json()
    assert env["model"] == "hydraulics.pressure_balance"
    assert env["status"] == "calculated"
    assert "bottom_gauge_pa" in env["result"]


def test_v1_mse_case(client):
    headers = {"x-geodrill-client": "workstation"}
    payload = {
        "wob_n": 90000.0,
        "torque_nm": 4500.0,
        "rotation_rad_s": 12.5,
        "rop_m_s": 0.008,
        "bit_diameter_m": 0.2159,
        "load_source": "surface",
        "drilling_state": "drilling",
    }
    resp = client.post(
        "/api/v1/wellbores/wb-101/performance/mse",
        json=payload,
        headers=headers,
    )
    assert resp.status_code == 200
    env = resp.json()
    assert env["model"] == "performance.mse"
    assert env["status"] == "calculated"
    assert "value_pa" in env["result"]


def test_v1_qualification_cards(client):
    headers = {"x-geodrill-client": "workstation"}
    resp = client.get("/api/v1/qualification/cards", headers=headers)
    assert resp.status_code == 200
    cards = resp.json()
    assert isinstance(cards, list)
    assert len(cards) > 0
