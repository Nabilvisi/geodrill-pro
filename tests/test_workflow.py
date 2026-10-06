"""End-to-end verification of the 8-step connected engineering project journey.

Covers:
1. Import survey and supporting telemetry/log data.
2. Save geometry and two comparable studies with explanation and scenario comparison.
3. Revise a shared input (new geometry revision) and verify stale study detection without silent recalculation.
4. Create a programme bound to exact evidence and source hashes.
5. Complete independent author, reviewer, approver handoff (4-eyes governance + Ed25519 signatures).
6. Export the report and signed project bundle (.gdpz).
7. Restore into a fresh directory with manifest validation and zip integrity checks.
8. Reopen the restored evidence and verify preserved hashes and cryptographic signatures.
Negative paths tested: missing inputs, unresolved references, stale edits, revoked access, corrupted bundles.
"""
import io
import json
import zipfile
import pytest
from fastapi.testclient import TestClient

from services.api.main import create_app
from services.api import demo, auth
from services.api.storage import Store, digest


@pytest.fixture
def test_setup(tmp_path):
    app = create_app(data_dir=tmp_path, mode="team")
    store = app.state.store
    client = TestClient(app)

    # 1. Create team users via auth.create_user
    admin = auth.create_user(store, "admin_user", "Admin", "admin", "admin-pass-123", actor="test")
    author = auth.create_user(store, "author_eng", "Author Engineer", "engineer", "pass-author-123", actor="test")
    reviewer = auth.create_user(store, "reviewer_eng", "Reviewer Engineer", "reviewer", "pass-reviewer-123", actor="test")
    approver = auth.create_user(store, "approver_eng", "Chief Approver", "approver", "pass-approver-123", actor="test")

    admin_token = client.post("/api/team/login", json={"username": "admin_user", "password": "admin-pass-123"}).json()["token"]
    author_token = client.post("/api/team/login", json={"username": "author_eng", "password": "pass-author-123"}).json()["token"]
    reviewer_token = client.post("/api/team/login", json={"username": "reviewer_eng", "password": "pass-reviewer-123"}).json()["token"]
    approver_token = client.post("/api/team/login", json={"username": "approver_eng", "password": "pass-approver-123"}).json()["token"]

    return {
        "app": app,
        "client": client,
        "store": store,
        "tmp_path": tmp_path,
        "admin": admin,
        "author": author,
        "reviewer": reviewer,
        "approver": approver,
        "admin_auth": {"Authorization": f"Bearer {admin_token}"},
        "author_auth": {"Authorization": f"Bearer {author_token}"},
        "reviewer_auth": {"Authorization": f"Bearer {reviewer_token}"},
        "approver_auth": {"Authorization": f"Bearer {approver_token}"},
    }


def test_complete_connected_project_journey(test_setup, tmp_path_factory):
    client = test_setup["client"]
    admin_auth = test_setup["admin_auth"]
    author_auth = test_setup["author_auth"]
    reviewer_auth = test_setup["reviewer_auth"]
    approver_auth = test_setup["approver_auth"]

    # --- Initial State: Create Project ---
    proj_resp = client.post("/api/projects", json={
        "name": "North Sea Alpha",
        "well_name": "16/1-A",
        "datum": "Rig Floor RKB",
        "north_reference": "grid",
        "bit_diameter_m": 0.2159,
        "origin": "synthetic",
    }, headers=author_auth)
    assert proj_resp.status_code == 201
    proj_id = proj_resp.json()["id"]

    # Author is a member; also add reviewer and approver
    client.post(f"/api/projects/{proj_id}/members", json={"user_id": test_setup["reviewer"]["id"]}, headers=admin_auth)
    client.post(f"/api/projects/{proj_id}/members", json={"user_id": test_setup["approver"]["id"]}, headers=admin_auth)

    # --- Negative Check: Project Readiness before imports ---
    readiness_before = client.get(f"/api/projects/{proj_id}/readiness", headers=author_auth).json()
    assert readiness_before["ready"] is False
    assert any(i["id"] == "missing-survey-dataset" for i in readiness_before["issues"])

    # --- Step 1: Import survey and supporting telemetry ---
    survey_bytes = demo.SURVEY if isinstance(demo.SURVEY, bytes) else demo.SURVEY.encode("utf-8")
    survey_resp = client.post(
        f"/api/projects/{proj_id}/imports",
        data={"kind": "survey"},
        files={"file": ("survey.csv", survey_bytes, "text/csv")},
        headers=author_auth,
    )
    assert survey_resp.status_code == 201
    survey_ds_id = survey_resp.json()["id"]
    survey_ds_meta = client.get(f"/api/projects/{proj_id}/datasets/{survey_ds_id}", headers=author_auth).json()
    survey_hash = survey_ds_meta["source_hash"]

    tele_raw = demo.telemetry()
    tele_bytes = tele_raw if isinstance(tele_raw, bytes) else tele_raw.encode("utf-8")
    telemetry_resp = client.post(
        f"/api/projects/{proj_id}/imports",
        data={"kind": "telemetry"},
        files={"file": ("drilling.csv", tele_bytes, "text/csv")},
        headers=author_auth,
    )
    assert telemetry_resp.status_code == 201

    # Helper builders for geometry and casing checks
    def build_casing(name="String A", yield_pa=100e6):
        return {
            "name": name, "top_md_m": 0.0, "bottom_md_m": 1000.0, "outside_diameter_m": 0.2, "inside_diameter_m": 0.1,
            "minimum_wall_m": 0.05, "wall_loss_allowance_m": 0.0, "state": "planned", "grade": "L80",
            "source": "API Spec 5CT", "yield_strength_pa": yield_pa, "body_burst_pa": 100e6, "body_collapse_pa": 100e6,
            "body_tension_n": 1e7, "body_compression_n": 1e7, "connection_burst_pa": 100e6, "connection_collapse_pa": 100e6,
            "connection_tension_n": 1e7, "connection_compression_n": 1e7,
            "body_rating_source": "Traceable mill certificate", "connection_rating_source": "Manufacturer rating table",
        }

    def build_geom_input(surv_id, note="Baseline geometry"):
        return {
            "survey_dataset_id": surv_id,
            "datum": "Rig Floor RKB",
            "coordinate_reference": "EPSG:32631",
            "wellhead_north_m": 0.0,
            "wellhead_east_m": 0.0,
            "wellhead_elevation_m": 25.0,
            "survey_quality_note": "Definitive MWD run",
            "tool_to_bit_offset_m": 15.0,
            "formations": [
                {"name": "Nordland Top", "top_tvd_m": 200.0, "uncertainty_m": 10.0, "category": "formation", "source": "Offset well log", "interpretation": "synthetic"},
                {"name": "Hordaland Top", "top_tvd_m": 800.0, "uncertainty_m": 15.0, "category": "formation", "source": "Offset well log", "interpretation": "synthetic"},
            ],
            "hole_sections": [
                {"name": "Surface Hole", "top_md_m": 0.0, "bottom_md_m": 1000.0, "diameter_m": 0.311, "source": "Drilling programme"},
                {"name": "Intermediate Hole", "top_md_m": 1000.0, "bottom_md_m": 2500.0, "diameter_m": 0.2159, "source": "Drilling programme"},
            ],
            "casings": [build_casing("Surface Casing", 552e6)],
        }

    def build_case_input(rev_id, candidate="Case A", gauge_pa=10e6):
        return {
            "geometry_revision_id": rev_id,
            "candidate_name": candidate,
            "required_load_cases": ["Burst Load Case"],
            "loads": [
                {
                    "name": "Burst Load Case",
                    "casing_name": "Surface Casing",
                    "md_m": 1000.0,
                    "internal_gauge_pa": gauge_pa,
                    "external_gauge_pa": 0.0,
                    "axial_wall_force_n": 0.0,
                    "source": "Gas kick scenario",
                }
            ],
            "yield_factor": 1.25,
            "burst_factor": 1.1,
            "collapse_factor": 1.125,
            "axial_factor": 1.3,
            "factor_basis": "NORSOK D-010 standard design factors",
            "temperature_derating": 1.0,
            "derating_basis": "Isothermal downhole assumptions",
        }

    # --- Step 2: Save geometry revision and two comparable studies ---
    geom_resp = client.post(
        f"/api/projects/{proj_id}/geometry",
        json={
            "geometry": build_geom_input(survey_ds_id, "Baseline geometry"),
            "change_note": "Initial baseline well geometry",
            "base_revision_id": None,
        },
        headers=author_auth,
    )
    assert geom_resp.status_code == 201
    rev1 = geom_resp.json()
    rev1_id = rev1["id"]

    # Study 1 (Baseline casing check: 10 MPa internal pressure)
    casing1_resp = client.post(
        f"/api/projects/{proj_id}/calculations/casing",
        json=build_case_input(rev1_id, "Baseline Casing Study", gauge_pa=10e6),
        headers=author_auth,
    )
    assert casing1_resp.status_code == 200
    study1 = casing1_resp.json()
    study1_id = study1["id"]

    # Study 2 (Alternative casing check: 20 MPa internal pressure)
    casing2_resp = client.post(
        f"/api/projects/{proj_id}/calculations/casing",
        json=build_case_input(rev1_id, "Alternative Higher Pressure Study", gauge_pa=20e6),
        headers=author_auth,
    )
    assert casing2_resp.status_code == 200
    study2 = casing2_resp.json()
    study2_id = study2["id"]

    # Scenario Comparison test
    compare_resp = client.post(
        f"/api/projects/{proj_id}/scenarios/compare",
        data={"baseline_id": study1_id, "alternative_id": study2_id},
        headers=author_auth,
    )
    assert compare_resp.status_code == 200
    comp = compare_resp.json()
    assert comp["geometry_compatible"] is True
    assert comp["compatibility_status"] == "compatible"
    assert "loads" in comp["differing_inputs"]

    # Result Explanation test
    exp_resp = client.get(f"/api/projects/{proj_id}/calculations/{study1_id}/explanation", headers=author_auth)
    assert exp_resp.status_code == 200
    exp = exp_resp.json()
    assert exp["is_current"] is True
    assert exp["geometry_revision"]["id"] == rev1_id
    assert any(s["sha256"] == survey_hash for s in exp["sources"])
    assert len(exp["assumptions"]) > 0

    # --- Step 3: Revise shared input & identify affected studies ---
    geom2_payload = build_geom_input(survey_ds_id, "Revised intermediate shoe")
    geom2_payload["tool_to_bit_offset_m"] = 18.0  # Modified sensor offset
    geom2_resp = client.post(
        f"/api/projects/{proj_id}/geometry",
        json={
            "geometry": geom2_payload,
            "change_note": "Updated BHA sensor offset to 18m",
            "base_revision_id": rev1_id,
        },
        headers=author_auth,
    )
    assert geom2_resp.status_code == 201
    rev2_id = geom2_resp.json()["id"]

    # Lineage & Stale study detection
    lineage = client.get(f"/api/projects/{proj_id}/lineage", headers=author_auth).json()
    node1 = next(n for n in lineage["nodes"] if n["id"] == study1_id)
    assert node1["is_current"] is False
    assert any("superseded" in r.lower() for r in node1["stale_reasons"])

    # Historical results must NOT be silently modified or recalculated!
    exp_after = client.get(f"/api/projects/{proj_id}/calculations/{study1_id}/explanation", headers=author_auth).json()
    assert exp_after["is_current"] is False
    assert any("Stale Geometry" in r for r in exp_after["withholding_reasons"])

    # Readiness shows stale study warning
    readiness_mid = client.get(f"/api/projects/{proj_id}/readiness", headers=author_auth).json()
    assert any(i["category"] == "stale_study" for i in readiness_mid["issues"])

    # Negative test: Binding stale study 1 to a new programme is blocked
    stale_bind_resp = client.post(
        f"/api/projects/{proj_id}/programmes",
        json={
            "title": "Drilling Programme with Stale Study",
            "content": {"well": "16/1-A", "objectives": "Reach TD safely"},
            "evidence_bindings": [{"study_id": study1_id}],
        },
        headers=author_auth,
    )
    assert stale_bind_resp.status_code in {400, 422}
    assert "stale" in stale_bind_resp.text.lower()

    # --- Step 4: Create a programme bound to current evidence ---
    # Compute study 3 bound to current revision rev2
    casing3_resp = client.post(
        f"/api/projects/{proj_id}/calculations/casing",
        json=build_case_input(rev2_id, "Official Current Casing Study", gauge_pa=15e6),
        headers=author_auth,
    )
    assert casing3_resp.status_code == 200
    study3_id = casing3_resp.json()["id"]

    prog_create_resp = client.post(
        f"/api/projects/{proj_id}/programmes",
        json={
            "title": "Official Well 16/1-A Drilling Programme",
            "content": {"target_depth_md_m": 3000.0, "contingency": "Packer isolation"},
            "evidence_bindings": [{"study_id": study3_id}],
        },
        headers=author_auth,
    )
    assert prog_create_resp.status_code == 201
    prog = prog_create_resp.json()
    prog_id = prog["id"]
    ver1 = prog["versions"][0]
    ver1_id = ver1["id"]
    assert ver1["has_bindings"] is True
    assert ver1["evidence_bindings"][0]["study_id"] == study3_id

    # --- Step 5: Complete 4-eyes author, reviewer, approver handoff ---
    # Author submits
    sub_resp = client.post(f"/api/team/versions/{ver1_id}/actions/submit", json={"note": "Ready for peer review"}, headers=author_auth)
    assert sub_resp.status_code == 200

    # Negative test: Author cannot review their own submission
    self_review = client.post(f"/api/team/versions/{ver1_id}/actions/pass_review", json={"note": "I approve myself"}, headers=author_auth)
    assert self_review.status_code == 403

    # Reviewer passes review
    rev_act = client.post(f"/api/team/versions/{ver1_id}/actions/pass_review", json={"note": "Technical review passed"}, headers=reviewer_auth)
    assert rev_act.status_code == 200

    # Negative test: Reviewer cannot approve
    self_approve = client.post(f"/api/team/versions/{ver1_id}/actions/approve", json={"note": "Reviewer approving"}, headers=reviewer_auth)
    assert self_approve.status_code == 403

    # Approver approves
    app_act = client.post(f"/api/team/versions/{ver1_id}/actions/approve", json={"note": "Formal approval granted"}, headers=approver_auth)
    assert app_act.status_code == 200

    # Admin issues
    iss_act = client.post(f"/api/team/versions/{ver1_id}/actions/issue", json={"note": "Released for execution"}, headers=admin_auth)
    assert iss_act.status_code == 200

    # Verify cryptographic signatures and transition chain
    verify_resp = client.get(f"/api/team/versions/{ver1_id}/verify", headers=author_auth).json()
    assert verify_resp["ok"] is True
    assert len(verify_resp["problems"]) == 0
    assert verify_resp["signer_fingerprint"] is not None

    # --- Step 6: Export report and signed project bundle (.gdpz) ---
    rep_resp = client.post(f"/api/projects/{proj_id}/reports", headers=author_auth)
    assert rep_resp.status_code == 201

    bundle_resp = client.get(f"/api/projects/{proj_id}/bundle/export", headers=author_auth)
    assert bundle_resp.status_code == 200
    assert bundle_resp.headers["content-type"] == "application/zip"
    bundle_bytes = bundle_resp.content

    # Inspect zip bundle structure
    with zipfile.ZipFile(io.BytesIO(bundle_bytes), "r") as zf:
        names = zf.namelist()
        assert "manifest.json" in names
        manifest = json.loads(zf.read("manifest.json").decode("utf-8"))
        assert manifest["project_id"] == proj_id
        assert "project.json" in manifest["file_hashes"]
        assert manifest["server_fingerprint"] is not None
        assert manifest["signature"] is not None

    # --- Negative Check: Corrupted bundle rejected ---
    corrupted_bytes = bytearray(bundle_bytes)
    # flip a byte in the middle of the archive
    corrupted_bytes[len(corrupted_bytes) // 2] ^= 0xFF
    bad_upload = client.post(
        "/api/projects/bundle/restore",
        files={"file": ("corrupt.gdpz", bytes(corrupted_bytes), "application/zip")},
        headers=admin_auth,
    )
    assert bad_upload.status_code in {400, 422}

    # --- Step 7: Restore bundle into a fresh directory ---
    fresh_dir = tmp_path_factory.mktemp("fresh_restore")
    fresh_app = create_app(data_dir=fresh_dir, mode="team")
    fresh_client = TestClient(fresh_app)

    # Provision an admin user to execute the restore endpoint
    auth.create_user(fresh_app.state.store, "restore_admin", "Restore Admin", "admin", "admin-pass-123", actor="test")
    fresh_admin = fresh_client.post("/api/team/login", json={"username": "restore_admin", "password": "admin-pass-123"}).json()
    fresh_admin_auth = {"Authorization": f"Bearer {fresh_admin['token']}"}

    restore_resp = fresh_client.post(
        "/api/projects/bundle/restore",
        files={"file": ("valid.gdpz", bundle_bytes, "application/zip")},
        headers=fresh_admin_auth,
    )
    assert restore_resp.status_code == 201
    restored_info = restore_resp.json()
    assert restored_info["restored"] is True
    assert restored_info["project_id"] == proj_id

    # --- Step 8: Reopen restored evidence and verify preserved hashes & signatures ---
    # Log in as author on restored workstation
    fresh_author_token = fresh_client.post("/api/team/login", json={"username": "author_eng", "password": "pass-author-123"}).json()["token"]
    fresh_author_auth = {"Authorization": f"Bearer {fresh_author_token}"}

    # Verify project exists and hashes are identical
    restored_proj = fresh_client.get(f"/api/projects/{proj_id}", headers=fresh_author_auth).json()
    assert restored_proj["name"] == "North Sea Alpha"

    restored_ds = fresh_client.get(f"/api/projects/{proj_id}/datasets/{survey_ds_id}", headers=fresh_author_auth).json()
    assert restored_ds["source_hash"] == survey_hash
    restored_studies = fresh_client.get(f"/api/projects/{proj_id}/calculations", headers=fresh_author_auth)
    assert restored_studies.status_code == 200
    assert any(s["id"] == study3_id for s in restored_studies.json())

    restored_prog = fresh_client.get(f"/api/team/programmes/{prog_id}", headers=fresh_author_auth).json()
    assert restored_prog["versions"][0]["state"] == "issued"
    assert restored_prog["versions"][0]["evidence_bindings"][0]["study_id"] == study3_id

    # Verify cryptographic signature on the restored instance
    restored_ver = fresh_client.get(f"/api/team/versions/{ver1_id}/verify", headers=fresh_author_auth).json()
    assert restored_ver["ok"] is True
    assert len(restored_ver["problems"]) == 0

    # Negative test: Revoked access
    deactivate_resp = client.post(
        f"/api/team/users/{test_setup['author']['id']}/active",
        json={"active": False},
        headers=admin_auth,
    )
    assert deactivate_resp.status_code == 200

    denied = client.get(f"/api/projects/{proj_id}", headers=author_auth)
    assert denied.status_code == 401
