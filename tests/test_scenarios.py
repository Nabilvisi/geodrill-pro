"""Unit tests for Scenario Management and Lineage Graph (GD-A02)."""
from fastapi.testclient import TestClient
from packages.engineering.scenarios import build_lineage_graph, compare_scenarios
from services.api.main import create_app


def test_lineage_graph_and_stale_detection():
    """Verify that calculations tied to superseded geometry are marked stale."""
    revisions = [
        {"id": "rev-new", "sha256": "hash-new", "change_note": "New sidetrack", "created_at": "2026-10-05T01:00:00Z", "input": {"survey_dataset_id": "ds-1"}},
        {"id": "rev-old", "sha256": "hash-old", "change_note": "Old baseline", "created_at": "2026-10-04T01:00:00Z", "input": {"survey_dataset_id": "ds-1"}}
    ]
    datasets = [{"id": "ds-1", "kind": "survey", "filename": "survey.csv", "source_hash": "hash-src", "created_at": "2026-10-04T00:00:00Z"}]
    calculations = [
        {"id": "calc-1", "model": "hydraulics", "created_at": "2026-10-04T02:00:00Z", "inputs_si": {"geometry_revision_id": "rev-old", "study_name": "Old Study"}, "result": {"geometry_revision_id": "rev-old"}},
        {"id": "calc-2", "model": "hydraulics", "created_at": "2026-10-05T02:00:00Z", "inputs_si": {"geometry_revision_id": "rev-new", "study_name": "New Study"}, "result": {"geometry_revision_id": "rev-new"}}
    ]

    graph = build_lineage_graph("proj-1", datasets, revisions, calculations)
    nodes = {n["id"]: n for n in graph["nodes"]}

    assert nodes["calc-1"]["is_current"] is False
    assert any("superseded" in r for r in nodes["calc-1"]["stale_reasons"])
    assert nodes["calc-2"]["is_current"] is True
    assert len(nodes["calc-2"]["stale_reasons"]) == 0
    assert len(graph["edges"]) >= 3


def test_scenario_comparison():
    """Verify baseline vs alternative comparison with scalar variance deltas."""
    base = {
        "id": "c1",
        "model": "stability",
        "inputs_si": {"model": "kirsch", "pore_pressure_pa": 25e6, "mud_weight_ppg": 10.5},
        "result": {"hoop_stress_pa": 50e6, "failure_screen_exceeded": False}
    }
    alt = {
        "id": "c2",
        "model": "stability",
        "inputs_si": {"model": "kirsch", "pore_pressure_pa": 30e6, "mud_weight_ppg": 11.5},
        "result": {"hoop_stress_pa": 60e6, "failure_screen_exceeded": True}
    }
    comp = compare_scenarios(base, alt)
    assert comp["model"] == "stability"
    assert comp["common_inputs"] == {"model": "kirsch"}
    assert "pore_pressure_pa" in comp["differing_inputs"]
    assert comp["outcome_deltas"]["hoop_stress_pa"]["absolute_delta"] == 10000000.0
    assert comp["outcome_deltas"]["hoop_stress_pa"]["percent_delta"] == 20.0
    assert comp["outcome_deltas"]["failure_screen_exceeded"] == {"baseline": False, "alternative": True}


def test_scenarios_and_lineage_api(tmp_path):
    """Test /api/projects/{id}/lineage and /api/projects/{id}/scenarios/compare endpoints."""
    app = create_app(data_dir=tmp_path)
    client = TestClient(app)
    client.headers["X-Geodrill-Client"] = "workstation"
    client.get("/api/session")

    # Create demo project
    demo_proj = client.post("/api/demo").json()
    pid = demo_proj["id"]

    # Request lineage graph
    lin_res = client.get(f"/api/projects/{pid}/lineage")
    assert lin_res.status_code == 200
    graph = lin_res.json()
    assert graph["project_id"] == pid
    assert len(graph["nodes"]) > 0

    # Save two calculations for comparison
    c1 = client.post(f"/api/projects/{pid}/calculations/mse", json={
        "wob_n": 100000, "torque_nm": 8000, "rotation_rad_s": 12.56, "rop_m_s": 0.005, "bit_diameter_m": 0.216, "load_source": "surface", "drilling_state": "drilling"
    }).json()
    c2 = client.post(f"/api/projects/{pid}/calculations/mse", json={
        "wob_n": 120000, "torque_nm": 9500, "rotation_rad_s": 12.56, "rop_m_s": 0.007, "bit_diameter_m": 0.216, "load_source": "surface", "drilling_state": "drilling"
    }).json()

    cmp_res = client.post(f"/api/projects/{pid}/scenarios/compare", data={
        "baseline_id": c1["id"],
        "alternative_id": c2["id"]
    })
    assert cmp_res.status_code == 200
    comp = cmp_res.json()
    assert comp["model"] == "mse"
    assert "wob_n" in comp["differing_inputs"]
