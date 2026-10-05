"""Tests for Data Readiness and Import Mapping (GD-A01)."""
import io
from fastapi.testclient import TestClient
from packages.engineering.readiness import (
    parse_header_token,
    find_channel_for_alias,
    get_conversion_factor,
    inspect_readiness,
)
from services.api.main import create_app


def test_header_parsing_and_alias_lookup():
    """Verify robust token and alias detection across varied casing and bracket conventions."""
    assert parse_header_token("wob[kN]") == ("wob", "kN")
    assert parse_header_token("Torque (ft.lbf)") == ("torque", "ft.lbf")
    assert parse_header_token("rop_m_h") == ("rop", "m/h") or parse_header_token("rop[m/h]") == ("rop", "m/h")
    assert find_channel_for_alias("bit_weight") == "wob"
    assert find_channel_for_alias("rotary_speed") == "rpm"
    assert find_channel_for_alias("true_vertical_depth") == "tvd"


def test_unit_conversion_factors():
    """Verify SI conversion factors."""
    assert get_conversion_factor("md", "ft") == 0.3048
    assert get_conversion_factor("wob", "kN") == 1000.0
    assert get_conversion_factor("wob", "klbf") == 4448.2216152605
    assert get_conversion_factor("spp", "MPa") == 1e6
    assert get_conversion_factor("flow", "L/min") == 1.0 / 60000.0


def test_readiness_inspection():
    """Verify readiness scoring, detection of complete and missing channels."""
    headers = ["timestamp", "state", "md[m]", "wob[kN]", "torque[kN.m]", "rpm[rpm]", "rop[m/h]", "spp[MPa]", "flow[L/min]"]
    rows = [
        {"timestamp": "2026-10-04T00:00:00Z", "state": "drilling", "md[m]": "1000", "wob[kN]": "120", "torque[kN.m]": "10", "rpm[rpm]": "120", "rop[m/h]": "25", "spp[MPa]": "15", "flow[L/min]": "2200"},
        {"timestamp": "2026-10-04T00:00:10Z", "state": "drilling", "md[m]": "1001", "wob[kN]": "122", "torque[kN.m]": "11", "rpm[rpm]": "120", "rop[m/h]": "24", "spp[MPa]": "15.2", "flow[L/min]": "2200"}
    ]
    report = inspect_readiness(headers, rows, "telemetry")
    assert report["total_rows"] == 2
    assert report["complete_rows"] == 2
    assert report["null_percentage"] == 0.0
    assert report["is_ready_for_engineering"] is True
    assert report["readiness_score_pct"] == 100.0


def test_readiness_api_endpoint(tmp_path):
    """Test /api/readiness/inspect HTTP route."""
    app = create_app(data_dir=tmp_path)
    client = TestClient(app)
    client.headers["X-Geodrill-Client"] = "workstation"
    client.get("/api/session")

    csv_data = "md[m],inclination[deg],azimuth[deg]\n0,0,0\n500,12,45\n1000,25,90\n"
    res = client.post(
        "/api/readiness/inspect",
        data={"kind": "survey"},
        files={"file": ("survey.csv", io.BytesIO(csv_data.encode("utf-8")), "text/csv")}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["total_rows"] == 3
    assert data["is_ready_for_engineering"] is True
    assert len(data["identified_mappings"]) == 3
