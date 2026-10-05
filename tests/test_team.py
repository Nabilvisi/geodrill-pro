import sqlite3
import pytest
from fastapi.testclient import TestClient
from services.api import auth, programmes
from services.api.main import create_app
from services.api.storage import Store

PW = "correct horse battery"
CONTENT = {"well": "W-1", "td_m": 3200, "casing": ["20in", "13-3/8in"]}
H = {"x-geodrill-client": "workstation"}


@pytest.fixture
def store(tmp_path):
    return Store(tmp_path)


@pytest.fixture
def people(store):
    """One user per role, plus a second engineer and a second reviewer."""
    names = [("admin", "admin"), ("eng", "engineer"), ("eng2", "engineer"), ("rev", "reviewer"),
             ("rev2", "reviewer"), ("app", "approver"), ("view", "viewer")]
    return {n: auth.create_user(store, n, n.title(), r, PW, actor="test") for n, r in names}


@pytest.fixture
def project(store):
    return store.create_project({"name": "P"})["id"]


# ---------- accounts and sessions ----------

def test_password_hash_roundtrip_and_salting():
    a, b = auth.hash_password(PW), auth.hash_password(PW)
    assert a != b and auth.verify_password(PW, a) and not auth.verify_password("wrong", a)
    assert not auth.verify_password(PW, "garbage")


@pytest.mark.parametrize("kwargs,msg", [
    ({"role": "owner"}, "Role"), ({"username": "a b"}, "Username"), ({"password": "short"}, "Password")])
def test_create_user_validation(store, kwargs, msg):
    base = {"username": "bob", "display_name": "Bob", "role": "viewer", "password": PW}
    with pytest.raises(ValueError, match=msg):
        auth.create_user(store, **{**base, **kwargs})


def test_duplicate_username_case_insensitive(store, people):
    with pytest.raises(ValueError, match="already exists"):
        auth.create_user(store, "ENG", "x", "viewer", PW)


def test_login_logout_and_token_not_stored_in_plain(store, people):
    token, user = auth.login(store, "eng", PW)
    assert user["role"] == "engineer" and auth.user_for_token(store, token)["username"] == "eng"
    with store.connect() as db:
        assert token not in " ".join(str(tuple(r)) for r in db.execute("SELECT * FROM sessions"))
    auth.logout(store, token)
    assert auth.user_for_token(store, token) is None


def test_generic_login_error_for_unknown_and_wrong(store, people):
    for u, p in [("nobody", PW), ("eng", "wrong-password")]:
        with pytest.raises(auth.AuthError, match="Invalid username or password"):
            auth.login(store, u, p)


def test_lockout_after_repeated_failures(store, people):
    for _ in range(auth.MAX_FAILURES):
        with pytest.raises(auth.AuthError):
            auth.login(store, "eng", "wrong-password")
    with pytest.raises(auth.AuthError):  # correct password still refused while locked
        auth.login(store, "eng", PW)


def test_deactivation_kills_sessions(store, people):
    token, _ = auth.login(store, "eng", PW)
    auth.set_active(store, people["eng"]["id"], False, "test")
    assert auth.user_for_token(store, token) is None
    with pytest.raises(auth.AuthError):
        auth.login(store, "eng", PW)


# ---------- programme workflow ----------

def make(store, project, people, who="eng"):
    return programmes.create_programme(store, project, "Well W-1 programme", CONTENT, people[who])


def state(store, programme_id, n=-1):
    return programmes.get_programme(store, programme_id)["versions"][n]["state"]


def run_to_approved(store, vid, people):
    programmes.act(store, vid, "submit", people["eng"])
    programmes.act(store, vid, "pass_review", people["rev"])
    programmes.act(store, vid, "approve", people["app"])


def test_happy_path_to_issued(store, project, people):
    p = make(store, project, people)
    vid = p["versions"][0]["id"]
    assert p["versions"][0]["state"] == "draft"
    run_to_approved(store, vid, people)
    programmes.act(store, vid, "issue", people["app"])
    assert state(store, p["id"]) == "issued"
    assert programmes.verify_version(store, vid)["ok"]
    assert [t["to_state"] for t in programmes.get_programme(store, p["id"])["versions"][0]["transitions"]] == ["draft", "in_review", "reviewed", "approved", "issued"]


def test_role_gates(store, project, people):
    with pytest.raises(PermissionError):
        make(store, project, people, "view")
    vid = make(store, project, people)["versions"][0]["id"]
    with pytest.raises(PermissionError):
        programmes.act(store, vid, "submit", people["eng2"])  # not the author
    programmes.act(store, vid, "submit", people["eng"])
    for who in ("eng", "app", "view"):
        with pytest.raises(PermissionError):
            programmes.act(store, vid, "pass_review", people[who])


def test_four_eyes_applies_to_admin_author(store, project, people):
    vid = make(store, project, people, "admin")["versions"][0]["id"]
    programmes.act(store, vid, "submit", people["admin"])
    with pytest.raises(PermissionError, match="Four-eyes"):
        programmes.act(store, vid, "pass_review", people["admin"])


def test_approver_must_differ_from_reviewer(store, project, people):
    a2 = auth.create_user(store, "both", "Both", "admin", PW)
    vid = make(store, project, people)["versions"][0]["id"]
    programmes.act(store, vid, "submit", people["eng"])
    programmes.act(store, vid, "pass_review", a2)
    with pytest.raises(PermissionError, match="differ from the reviewer"):
        programmes.act(store, vid, "approve", a2)
    programmes.act(store, vid, "approve", people["app"])


def test_illegal_transitions_and_required_note(store, project, people):
    p = make(store, project, people)
    vid = p["versions"][0]["id"]
    with pytest.raises(ValueError, match="not allowed"):
        programmes.act(store, vid, "issue", people["app"])
    programmes.act(store, vid, "submit", people["eng"])
    with pytest.raises(ValueError, match="note is required"):
        programmes.act(store, vid, "request_changes", people["rev"])
    programmes.act(store, vid, "request_changes", people["rev"], "Casing shoe too shallow")
    assert state(store, p["id"]) == "changes_requested"


def test_new_version_after_changes_requested_and_supersede_on_issue(store, project, people):
    p = make(store, project, people)
    v1 = p["versions"][0]["id"]
    programmes.act(store, v1, "submit", people["eng"])
    programmes.act(store, v1, "request_changes", people["rev"], "fix it")
    p = programmes.new_version(store, p["id"], {**CONTENT, "td_m": 3300}, people["eng"])
    v2 = p["versions"][1]["id"]
    assert p["versions"][1]["version_no"] == 2
    run_to_approved(store, v2, people)
    programmes.act(store, v2, "issue", people["app"])
    # a third version, issued later, supersedes v2
    p = programmes.new_version(store, p["id"], {**CONTENT, "td_m": 3400}, people["eng"])
    v3 = p["versions"][2]["id"]
    run_to_approved(store, v3, people)
    programmes.act(store, v3, "issue", people["app"])
    states = [v["state"] for v in programmes.get_programme(store, p["id"])["versions"]]
    assert states == ["changes_requested", "superseded", "issued"]


def test_cannot_start_new_version_while_in_review(store, project, people):
    p = make(store, project, people)
    programmes.act(store, p["versions"][0]["id"], "submit", people["eng"])
    with pytest.raises(ValueError, match="in_review"):
        programmes.new_version(store, p["id"], CONTENT, people["eng"])


def test_replacing_a_draft_supersedes_it(store, project, people):
    p = make(store, project, people)
    p = programmes.new_version(store, p["id"], {**CONTENT, "td_m": 1}, people["eng"])
    assert [v["state"] for v in p["versions"]] == ["superseded", "draft"]


@pytest.mark.parametrize("bad", [{}, [], "x", {"v": float("nan")}])
def test_content_validation(store, project, people, bad):
    with pytest.raises(ValueError):
        programmes.create_programme(store, project, "t", bad, people["eng"])


def test_missing_project_and_programme(store, people):
    with pytest.raises(KeyError):
        programmes.create_programme(store, "nope", "t", CONTENT, people["eng"])
    with pytest.raises(KeyError):
        programmes.get_programme(store, "nope")


def test_immutability_triggers(store, project, people):
    vid = make(store, project, people)["versions"][0]["id"]
    with store.connect() as db:
        with pytest.raises(sqlite3.DatabaseError, match="immutable"):
            db.execute("UPDATE programme_versions SET content='{}'")
    with store.connect() as db:
        with pytest.raises(sqlite3.DatabaseError, match="append-only"):
            db.execute("DELETE FROM programme_transitions")
        with pytest.raises(sqlite3.DatabaseError, match="append-only"):
            db.execute("UPDATE programme_transitions SET note='x'")
    assert programmes.verify_version(store, vid)["ok"]


def test_tampering_is_detected(store, project, people):
    """Bypass the triggers (as a DB admin could) and confirm verification still catches it."""
    vid = make(store, project, people)["versions"][0]["id"]
    programmes.act(store, vid, "submit", people["eng"])
    with store.connect() as db:
        db.execute("DROP TRIGGER pt_no_update")
        db.execute("UPDATE programme_transitions SET actor_role='admin' WHERE to_state='in_review'")
    result = programmes.verify_version(store, vid)
    assert not result["ok"] and "chain broken" in result["problems"][0]


def test_audit_records_real_actor(store, project, people):
    vid = make(store, project, people)["versions"][0]["id"]
    programmes.act(store, vid, "submit", people["eng"])
    with store.connect() as db:
        actors = [r[0] for r in db.execute("SELECT json_extract(payload,'$.actor') FROM audit WHERE json_extract(payload,'$.action') LIKE 'programme.%'")]
    assert actors and set(actors) == {"user:eng"}


# ---------- HTTP surface ----------

@pytest.fixture
def client(tmp_path):
    app = create_app(tmp_path, mode="team")
    c = TestClient(app)
    for n, r in [("admin", "admin"), ("eng", "engineer"), ("rev", "reviewer"), ("app", "approver"), ("view", "viewer")]:
        auth.create_user(app.state.store, n, n, r, PW)
    return c


def login(client, name):
    r = client.post("/api/team/login", json={"username": name, "password": PW}, headers=H)
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['token']}", **H}


def test_http_requires_auth_everywhere_but_health_and_login(client):
    assert client.get("/api/health").status_code == 200
    for path in ("/api/projects", "/api/session", "/api/audit", "/api/team/me", "/api/team/users"):
        assert client.get(path).status_code == 401, path
    assert client.get("/api/projects", headers={"Authorization": "Bearer forged"}).status_code == 401
    assert client.get("/api/projects", headers={"Cookie": "gd_session=x"}).status_code == 401


def test_http_bad_login_is_401(client):
    assert client.post("/api/team/login", json={"username": "eng", "password": "nope"}, headers=H).status_code == 401


def test_http_admin_only_user_management(client):
    eng, admin = login(client, "eng"), login(client, "admin")
    body = {"username": "new1", "display_name": "N", "role": "viewer", "password": PW}
    assert client.post("/api/team/users", json=body, headers=eng).status_code == 403
    r = client.post("/api/team/users", json=body, headers=admin)
    assert r.status_code == 201 and "password" not in r.text
    assert client.post("/api/team/users", json=body, headers=admin).status_code == 422


PROJECT = {"name": "P", "well_name": "W-1", "datum": "RKB", "north_reference": "true", "bit_diameter_m": 0.2159, "origin": "synthetic"}


def test_http_full_flow_and_existing_routes_open_to_signed_in_users(client):
    admin = login(client, "admin")
    eng, rev, app_, view = (login(client, n) for n in ("eng", "rev", "app", "view"))
    created = client.post("/api/projects", json=PROJECT, headers=eng)
    assert created.status_code == 201, created.text
    pid = created.json()["id"]

    # Add rev, app, and view as project members
    users = {u["username"]: u["id"] for u in client.get("/api/team/users", headers=admin).json()}
    for who in ("rev", "app", "view"):
        client.post(f"/api/projects/{pid}/members", json={"user_id": users[who]}, headers=admin)

    r = client.post(f"/api/projects/{pid}/programmes", json={"title": "T", "content": CONTENT}, headers=eng)
    assert r.status_code == 201
    prog = r.json()
    vid = prog["versions"][0]["id"]
    assert client.post(f"/api/projects/{pid}/programmes", json={"title": "T", "content": CONTENT}, headers=view).status_code == 403
    assert client.post(f"/api/team/versions/{vid}/actions/submit", json={}, headers=eng).status_code == 200
    assert client.post(f"/api/team/versions/{vid}/actions/pass_review", json={}, headers=eng).status_code == 403
    assert client.post(f"/api/team/versions/{vid}/actions/pass_review", json={}, headers=rev).status_code == 200
    assert client.post(f"/api/team/versions/{vid}/actions/approve", json={}, headers=app_).status_code == 200
    assert client.post(f"/api/team/versions/{vid}/actions/issue", json={}, headers=app_).status_code == 200
    assert client.get(f"/api/team/versions/{vid}/verify", headers=view).json()["ok"] is True
    assert client.get(f"/api/projects/{pid}/programmes", headers=view).json()[0]["issued_version"] == 1
    assert client.post(f"/api/team/versions/{vid}/actions/submit", json={}, headers=eng).status_code == 422


def test_http_audit_actor_is_real_user_for_existing_routes(client):
    eng = login(client, "eng")
    assert client.post("/api/projects", json=PROJECT, headers=eng).status_code == 201
    with client.app.state.store.connect() as db:
        actors = {r[0] for r in db.execute("SELECT json_extract(payload,'$.actor') FROM audit WHERE json_extract(payload,'$.action')='project.created'")}
    assert actors == {"user:eng"}


def test_local_mode_has_no_team_routes_and_keeps_cookie_auth(tmp_path):
    c = TestClient(create_app(tmp_path))
    assert c.get("/api/health").status_code == 200
    assert c.get("/api/projects").status_code == 401  # no cookie yet
    assert c.get("/api/session").status_code == 200
    assert c.get("/api/projects").status_code == 200
    assert c.post("/api/team/login", json={"username": "a", "password": "b"}, headers=H).status_code == 404


def test_team_viewer_denied_write_routes(client):
    admin = login(client, "admin")
    view = login(client, "view")
    p = client.post("/api/projects", json=PROJECT, headers=admin).json()
    pid = p["id"]

    # Add viewer as project member so they have read access
    users = client.get("/api/team/users", headers=admin).json()
    view_user = next(u for u in users if u["username"] == "view")
    res = client.post(f"/api/projects/{pid}/members", json={"user_id": view_user["id"]}, headers=admin)
    assert res.status_code == 201

    # Viewer can read project and its members
    assert client.get(f"/api/projects/{pid}", headers=view).status_code == 200
    assert client.get(f"/api/projects/{pid}/members", headers=view).status_code == 200

    # Viewer denied on engineering write endpoints
    assert client.post("/api/projects", json=PROJECT, headers=view).status_code == 403
    assert client.post(f"/api/projects/{pid}/reports", headers=view).status_code == 403
    assert client.post(f"/api/projects/{pid}/calculations/casing", json={"revision_id": "r1", "scenarios": []}, headers=view).status_code == 403


def test_team_project_isolation_and_membership(client):
    eng = login(client, "eng")
    rev = login(client, "rev")
    admin = login(client, "admin")
    
    # Engineer creates a project -> automatically member
    p = client.post("/api/projects", json=PROJECT, headers=eng).json()
    pid = p["id"]

    # Eng sees it
    eng_projs = client.get("/api/projects", headers=eng).json()
    assert any(x["id"] == pid for x in eng_projs)

    # Reviewer is NOT a member yet -> cannot see it in list, gets 404 on direct access
    rev_projs = client.get("/api/projects", headers=rev).json()
    assert not any(x["id"] == pid for x in rev_projs)
    assert client.get(f"/api/projects/{pid}", headers=rev).status_code == 404
    assert client.get(f"/api/projects/{pid}/programmes", headers=rev).status_code == 404

    # Admin sees all projects regardless of explicit membership
    admin_projs = client.get("/api/projects", headers=admin).json()
    assert any(x["id"] == pid for x in admin_projs)
    assert client.get(f"/api/projects/{pid}", headers=admin).status_code == 200

    # Admin adds reviewer to project
    users = client.get("/api/team/users", headers=admin).json()
    rev_user = next(u for u in users if u["username"] == "rev")
    add_res = client.post(f"/api/projects/{pid}/members", json={"user_id": rev_user["id"]}, headers=admin)
    assert add_res.status_code == 201
    assert any(m["id"] == rev_user["id"] or m["username"] == "rev" for m in add_res.json())

    # Now reviewer sees it and can access programme list
    assert client.get(f"/api/projects/{pid}", headers=rev).status_code == 200
    assert client.get(f"/api/projects/{pid}/programmes", headers=rev).status_code == 200

    # Non-admin cannot add members
    assert client.post(f"/api/projects/{pid}/members", json={"user_id": rev_user["id"]}, headers=eng).status_code == 403

    # Admin removes reviewer
    del_res = client.delete(f"/api/projects/{pid}/members/{rev_user['id']}", headers=admin)
    assert del_res.status_code == 200
    assert client.get(f"/api/projects/{pid}", headers=rev).status_code == 404

