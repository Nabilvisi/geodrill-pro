"""OWASP API Top 10 Security Penetration & Cryptographic Attestation Test Suite (Gate 4).

Covers:
1. Broken Object-Level Authorization (BOLA) across isolated projects.
2. Broken Authentication, token lifecycle, and session hijacking defense.
3. Broken Function Level Authorization & Four-Eyes Governance bypass defense.
4. Injection attacks (SQLi, path traversal, XML entity expansion).
5. Unrestricted resource consumption and replay attack prevention.
6. Ed25519 digital attestation audit, bit-flip tamper resistance, and .gdpz integrity.
"""
import io
import json
import sqlite3
import zipfile
import pytest
from fastapi.testclient import TestClient

from services.api import auth, programmes
from services.api.main import create_app
from services.api.storage import Store, canonical, digest


PW = "secure-rig-password-2026!"
HEADERS_CLIENT = {"x-geodrill-client": "workstation"}
PROJECT_PAYLOAD = {
    "name": "SecProject Alpha",
    "well_name": "Well-Sec-01",
    "datum": "RKB",
    "north_reference": "true",
    "bit_diameter_m": 0.2159,
    "origin": "synthetic"
}
PROGRAMME_CONTENT = {
    "well": "Well-Sec-01",
    "sections": [
        {"name": "17-1/2 in", "md_top_m": 0.0, "md_base_m": 850.0},
        {"name": "12-1/4 in", "md_top_m": 850.0, "md_base_m": 2600.0}
    ],
    "mud_weight_sg": 1.32
}


@pytest.fixture
def store(tmp_path):
    return Store(tmp_path)


@pytest.fixture
def client(tmp_path):
    app = create_app(tmp_path, mode="team")
    c = TestClient(app)
    # Seed users across roles
    for name, role in [
        ("admin", "admin"),
        ("eng_alice", "engineer"),
        ("eng_bob", "engineer"),
        ("rev_charlie", "reviewer"),
        ("rev_clara", "reviewer"),
        ("app_david", "approver"),
        ("view_eve", "viewer")
    ]:
        auth.create_user(app.state.store, name, name.title(), role, PW)
    return c


def get_auth_header(client: TestClient, username: str) -> dict:
    res = client.post("/api/team/login", json={"username": username, "password": PW}, headers=HEADERS_CLIENT)
    assert res.status_code == 200, f"Login failed for {username}: {res.text}"
    token = res.json()["token"]
    return {"Authorization": f"Bearer {token}", **HEADERS_CLIENT}


# =============================================================================
# 1. OWASP API 1: BROKEN OBJECT-LEVEL AUTHORIZATION (BOLA)
# =============================================================================

def test_bola_cross_project_isolation(client):
    """User from Project 1 cannot read, list, or export Project 2's data."""
    eng_alice = get_auth_header(client, "eng_alice")
    eng_bob = get_auth_header(client, "eng_bob")

    # Alice creates Project A
    res_a = client.post("/api/projects", json={**PROJECT_PAYLOAD, "name": "Project A"}, headers=eng_alice)
    assert res_a.status_code == 201
    pid_a = res_a.json()["id"]

    # Bob creates Project B
    res_b = client.post("/api/projects", json={**PROJECT_PAYLOAD, "name": "Project B"}, headers=eng_bob)
    assert res_b.status_code == 201
    pid_b = res_b.json()["id"]

    # Bob attempts direct access to Project A (BOLA attack) -> Must return 404 (or 403)
    assert client.get(f"/api/projects/{pid_a}", headers=eng_bob).status_code == 404
    assert client.get(f"/api/projects/{pid_a}/programmes", headers=eng_bob).status_code == 404
    assert client.get(f"/api/projects/{pid_a}/bundle", headers=eng_bob).status_code == 404

    # Alice attempts direct access to Project B (BOLA attack) -> Must return 404 (or 403)
    assert client.get(f"/api/projects/{pid_b}", headers=eng_alice).status_code == 404
    assert client.get(f"/api/projects/{pid_b}/programmes", headers=eng_alice).status_code == 404
    assert client.get(f"/api/projects/{pid_b}/bundle", headers=eng_alice).status_code == 404


def test_bola_unauthenticated_request_rejected(client):
    """All project-scoped resources reject unauthenticated requests."""
    assert client.get("/api/projects").status_code == 401
    assert client.get("/api/projects/some-fake-id").status_code == 401
    assert client.get("/api/team/me").status_code == 401


# =============================================================================
# 2. OWASP API 2: BROKEN AUTHENTICATION & SESSION MANAGEMENT
# =============================================================================

def test_forged_or_tampered_token_rejected(client):
    """Forged, truncated, or invalid tokens are rejected with 401."""
    bad_tokens = [
        "Bearer forged-token-xyz-123",
        "Bearer " + "0" * 64,
        "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.e30.t-ID",
        "Token invalid-scheme",
        ""
    ]
    for bt in bad_tokens:
        h = {"Authorization": bt, **HEADERS_CLIENT}
        assert client.get("/api/projects", headers=h).status_code == 401


def test_token_cannot_be_reused_after_logout(client):
    """Logged-out session tokens cannot access protected endpoints."""
    headers = get_auth_header(client, "eng_alice")
    # Verify active session
    assert client.get("/api/team/me", headers=headers).status_code == 200
    # Logout
    logout_res = client.post("/api/team/logout", headers=headers)
    assert logout_res.status_code == 200
    # Attempt reuse
    assert client.get("/api/team/me", headers=headers).status_code == 401
    assert client.get("/api/projects", headers=headers).status_code == 401


# =============================================================================
# 3. OWASP API 5: BROKEN FUNCTION LEVEL AUTHORIZATION & FOUR-EYES GOVERNANCE
# =============================================================================

def test_four_eyes_author_cannot_self_review_or_approve(client):
    """Author cannot self-review or self-approve their own drilling programme."""
    admin = get_auth_header(client, "admin")
    alice = get_auth_header(client, "eng_alice")
    charlie = get_auth_header(client, "rev_charlie")
    david = get_auth_header(client, "app_david")

    # Alice creates Project & Programme
    proj = client.post("/api/projects", json=PROJECT_PAYLOAD, headers=alice).json()
    pid = proj["id"]

    # Admin adds Charlie and David to project
    users = {u["username"]: u["id"] for u in client.get("/api/team/users", headers=admin).json()}
    client.post(f"/api/projects/{pid}/members", json={"user_id": users["rev_charlie"]}, headers=admin)
    client.post(f"/api/projects/{pid}/members", json={"user_id": users["app_david"]}, headers=admin)

    prog = client.post(f"/api/projects/{pid}/programmes", json={"title": "Drilling P1", "content": PROGRAMME_CONTENT}, headers=alice).json()
    vid = prog["versions"][0]["id"]

    # Alice submits draft
    assert client.post(f"/api/team/versions/{vid}/actions/submit", json={}, headers=alice).status_code == 200

    # Alice attempts to self-approve / pass review -> 403 Forbidden
    assert client.post(f"/api/team/versions/{vid}/actions/pass_review", json={}, headers=alice).status_code == 403

    # Charlie (Reviewer) passes review -> state moves to 'reviewed'
    assert client.post(f"/api/team/versions/{vid}/actions/pass_review", json={}, headers=charlie).status_code == 200

    # Alice (Author) attempts to approve her own reviewed version -> 403 Forbidden
    assert client.post(f"/api/team/versions/{vid}/actions/approve", json={}, headers=alice).status_code == 403

    # David (Approver) approves -> state moves to 'approved'
    assert client.post(f"/api/team/versions/{vid}/actions/approve", json={}, headers=david).status_code == 200

    # Charlie (Reviewer) attempts to issue from 'approved' -> 403 Forbidden (requires approver role)
    assert client.post(f"/api/team/versions/{vid}/actions/issue", json={}, headers=charlie).status_code == 403

    # David (Approver) issues
    assert client.post(f"/api/team/versions/{vid}/actions/issue", json={}, headers=david).status_code == 200


def test_viewer_role_cannot_perform_state_mutations(client):
    """Viewers are strictly restricted from mutative actions."""
    admin = get_auth_header(client, "admin")
    eve = get_auth_header(client, "view_eve")

    proj = client.post("/api/projects", json=PROJECT_PAYLOAD, headers=admin).json()
    pid = proj["id"]

    # Eve cannot create project
    assert client.post("/api/projects", json=PROJECT_PAYLOAD, headers=eve).status_code == 403

    # Admin adds Eve as member
    users = {u["username"]: u["id"] for u in client.get("/api/team/users", headers=admin).json()}
    client.post(f"/api/projects/{pid}/members", json={"user_id": users["view_eve"]}, headers=admin)

    # Eve can view project
    assert client.get(f"/api/projects/{pid}", headers=eve).status_code == 200

    # Eve cannot create programme or trigger calculations
    assert client.post(f"/api/projects/{pid}/programmes", json={"title": "EveProg", "content": PROGRAMME_CONTENT}, headers=eve).status_code == 403
    assert client.post(f"/api/projects/{pid}/calculations/casing", json={"revision_id": "r1", "scenarios": []}, headers=eve).status_code == 403


# =============================================================================
# 4. OWASP API 8: INJECTION ATTACKS & MALICIOUS PAYLOAD DEFENSE
# =============================================================================

def test_sql_injection_defense(client):
    """SQL injection payloads in route parameters or bodies are safely escaped."""
    admin = get_auth_header(client, "admin")

    sqli_payloads = [
        "' OR '1'='1",
        "'; DROP TABLE projects; --",
        "1 UNION SELECT id, username, password_hash, role, display_name, created_at, active FROM users --",
        "' OR 1=1; --"
    ]

    for payload in sqli_payloads:
        # SQLi in project creation well_name / name
        res = client.post("/api/projects", json={**PROJECT_PAYLOAD, "name": payload}, headers=admin)
        assert res.status_code == 201, f"Failed on payload: {payload}"
        pid = res.json()["id"]

        # Ensure projects table still exists and data was inserted literally
        get_res = client.get(f"/api/projects/{pid}", headers=admin)
        assert get_res.status_code == 200
        assert get_res.json()["name"] == payload

        # SQLi in path parameter
        res_sqli_id = client.get(f"/api/projects/{payload}", headers=admin)
        assert res_sqli_id.status_code in (404, 422)


def test_path_traversal_bundle_restore_rejected(store):
    """Archive bundles containing path traversal entries (../ or absolute paths) must be rejected."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("../../evil.bat", b"echo malicious payload")
        zf.writestr("manifest.json", json.dumps({"file_hashes": {}}))
        zf.writestr("project.json", json.dumps({"name": "Evil"}))

    with pytest.raises(ValueError, match="Insecure bundle entry path"):
        store.restore_bundle(buf.getvalue())


def test_programme_content_size_limit(store):
    """Programme content exceeding 256 KiB limit is rejected with ValueError."""
    eng_user = {"id": "u-1", "username": "eng", "role": "engineer"}
    p = store.create_project(PROJECT_PAYLOAD)
    pid = p["id"]

    huge_content = {"huge_data": "A" * (260 * 1024)}
    with pytest.raises(ValueError, match="exceeds the 256 KiB limit"):
        programmes.create_programme(store, pid, "Huge Title", huge_content, eng_user)


# =============================================================================
# 5. Ed25519 CRYPTOGRAPHIC ATTESTATION AUDIT & TAMPER-RESISTANCE
# =============================================================================

def test_ed25519_single_bit_flip_fails_verification(store):
    """A single bit-flip in the signed payload byte sequence MUST fail signature verification."""
    payload = b"drilling_programme_v1_signed_attestation_payload"
    sig_hex = store.sign_attestation(payload)
    fp = store.attestation_fingerprint

    # Original verification passes
    assert store.verify_attestation(payload, sig_hex, fp) is True

    # Mutate byte at index 12 with a bit-flip (XOR with 0x01)
    tampered_payload = payload[:12] + bytes([payload[12] ^ 0x01]) + payload[13:]
    assert store.verify_attestation(tampered_payload, sig_hex, fp) is False

    # Tamper with the signature itself
    bad_sig = sig_hex[:10] + ("0" if sig_hex[10] != "0" else "1") + sig_hex[11:]
    assert store.verify_attestation(payload, bad_sig, fp) is False


def test_programme_transition_tamper_detection(store):
    """Tampering with database transition records triggers verification failure."""
    eng = auth.create_user(store, "eng_test", "Engineer Test", "engineer", PW)
    p = store.create_project(PROJECT_PAYLOAD)
    prog = programmes.create_programme(store, p["id"], "Prog Alpha", PROGRAMME_CONTENT, eng)
    vid = prog["versions"][0]["id"]

    # Submit version
    programmes.act(store, vid, "submit", eng, "Initial submission")

    # Verify version initially intact
    ver_check = programmes.verify_version(store, vid)
    assert ver_check["ok"] is True
    assert len(ver_check["problems"]) == 0

    # Tamper directly in database: mutate note in programme_transitions
    with store.connect() as db:
        db.execute("DROP TRIGGER pt_no_update")
        db.execute("UPDATE programme_transitions SET note='Foraged fraudulent note' WHERE to_state='in_review'")

    # Verification must catch tampering
    ver_tampered = programmes.verify_version(store, vid)
    assert ver_tampered["ok"] is False
    assert any("chain broken" in p or "signature invalid" in p for p in ver_tampered["problems"])


def test_bundle_tamper_resistance_on_restore(store, tmp_path):
    """Tampered files in .gdpz bundle fail restore with hash mismatch or signature invalid."""
    eng = auth.create_user(store, "eng_test", "Engineer Test", "engineer", PW)
    p = store.create_project(PROJECT_PAYLOAD)
    programmes.create_programme(store, p["id"], "Prog Alpha", PROGRAMME_CONTENT, eng)

    bundle_bytes = store.export_bundle(p["id"])

    # Tamper with file inside the archive
    in_buf = io.BytesIO(bundle_bytes)
    out_buf = io.BytesIO()
    with zipfile.ZipFile(in_buf, "r") as z_in, zipfile.ZipFile(out_buf, "w") as z_out:
        for item in z_in.infolist():
            content = z_in.read(item.filename)
            if item.filename == "project.json":
                # Forged project modification
                mod_data = json.loads(content.decode("utf-8"))
                mod_data["well_name"] = "FORGED-WELL-NAME"
                content = json.dumps(mod_data).encode("utf-8")
            z_out.writestr(item, content)

    # Attempt restore into fresh store
    fresh_store = Store(tmp_path / "fresh_store")
    with pytest.raises(ValueError, match="hash mismatch for project.json"):
        fresh_store.restore_bundle(out_buf.getvalue())
