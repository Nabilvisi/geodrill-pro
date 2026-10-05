"""Drilling programme review and approval workflow.

* A programme has immutable, numbered versions (content never changes after creation).
* A version's state comes from an append-only, hash-chained transition log. Each link
  binds the version's content hash, the acting user, their role at the time, and a note.
* Four-eyes: the author cannot review or approve their own version, and the approver
  must differ from the reviewer. These rules apply to admins too.

    draft -> in_review -> reviewed -> approved -> issued -> (superseded)
                  \\          \\-> changes_requested
                   \\-> changes_requested
"""
import json
from uuid import uuid4

from .storage import Store, now, canonical, digest

MAX_CONTENT_BYTES = 256 * 1024
ZERO = "0" * 64

# (from_state, action) -> (to_state, roles allowed)
TRANSITIONS = {
    ("draft", "submit"): ("in_review", {"engineer", "admin"}),
    ("in_review", "pass_review"): ("reviewed", {"reviewer", "admin"}),
    ("in_review", "request_changes"): ("changes_requested", {"reviewer", "admin"}),
    ("reviewed", "approve"): ("approved", {"approver", "admin"}),
    ("reviewed", "request_changes"): ("changes_requested", {"approver", "admin"}),
    ("approved", "issue"): ("issued", {"approver", "admin"}),
}
EDIT_ROLES = {"engineer", "admin"}
# States from which a new version may be started.
NEW_VERSION_FROM = {"draft", "changes_requested", "issued"}


def _check_content(content) -> str:
    if not isinstance(content, dict) or not content:
        raise ValueError("Programme content must be a non-empty JSON object")
    text = canonical(content)  # also rejects NaN/Infinity
    if len(text.encode()) > MAX_CONTENT_BYTES:
        raise ValueError("Programme content exceeds the 256 KiB limit")
    return text


def _actor(user) -> str:
    return f"user:{user['username']}"


def _append(db, store, version_id, content_sha, from_state, to_state, user, note):
    last = db.execute("SELECT hash FROM programme_transitions WHERE version_id=? ORDER BY sequence DESC LIMIT 1", (version_id,)).fetchone()
    previous = last[0] if last else ZERO
    at = now()
    payload = canonical({"version_id": version_id, "content_sha256": content_sha, "from": from_state, "to": to_state,
                         "actor_id": user["id"], "actor_role": user["role"], "note": note, "at": at})
    db.execute("INSERT INTO programme_transitions(version_id,from_state,to_state,actor_id,actor_role,note,at,previous_hash,hash) VALUES(?,?,?,?,?,?,?,?,?)",
               (version_id, from_state, to_state, user["id"], user["role"], note, at, previous, digest((previous + payload).encode())))


def _state(db, version_id) -> str | None:
    row = db.execute("SELECT to_state FROM programme_transitions WHERE version_id=? ORDER BY sequence DESC LIMIT 1", (version_id,)).fetchone()
    return row[0] if row else None


def _insert_version(db, store, programme_id, version_no, text, user):
    version_id = str(uuid4())
    sha = digest(text.encode())
    db.execute("INSERT INTO programme_versions(id,programme_id,version_no,content,content_sha256,created_by,created_at) VALUES(?,?,?,?,?,?,?)",
               (version_id, programme_id, version_no, text, sha, user["id"], now()))
    _append(db, store, version_id, sha, None, "draft", user, "Version created")
    return version_id


def create_programme(store: Store, project_id: str, title: str, content: dict, user: dict) -> dict:
    if user["role"] not in EDIT_ROLES:
        raise PermissionError("Only engineers and admins can create programmes")
    if not (title or "").strip():
        raise ValueError("Title is required")
    text = _check_content(content)
    store.project(project_id)  # KeyError -> 404
    programme_id = str(uuid4())
    with store.connect() as db:
        db.execute("BEGIN IMMEDIATE")
        db.execute("INSERT INTO programmes VALUES(?,?,?,?,?)", (programme_id, project_id, title.strip(), user["id"], now()))
        version_id = _insert_version(db, store, programme_id, 1, text, user)
        store.audit(db, "programme.created", project_id, {"programme_id": programme_id, "version_id": version_id}, actor=_actor(user))
    return get_programme(store, programme_id)


def new_version(store: Store, programme_id: str, content: dict, user: dict) -> dict:
    if user["role"] not in EDIT_ROLES:
        raise PermissionError("Only engineers and admins can create versions")
    text = _check_content(content)
    with store.connect() as db:
        db.execute("BEGIN IMMEDIATE")
        prog = db.execute("SELECT * FROM programmes WHERE id=?", (programme_id,)).fetchone()
        if not prog:
            raise KeyError("Programme not found")
        latest = db.execute("SELECT * FROM programme_versions WHERE programme_id=? ORDER BY version_no DESC LIMIT 1", (programme_id,)).fetchone()
        state = _state(db, latest["id"])
        if state not in NEW_VERSION_FROM:
            raise ValueError(f"Latest version is '{state}'; finish or return it before starting a new version")
        if state == "draft":
            if latest["created_by"] != user["id"] and user["role"] != "admin":
                raise PermissionError("Only the author or an admin can replace a draft")
            _append(db, store, latest["id"], latest["content_sha256"], "draft", "superseded", user, f"Replaced by draft v{latest['version_no'] + 1}")
        version_id = _insert_version(db, store, programme_id, latest["version_no"] + 1, text, user)
        store.audit(db, "programme.version_created", prog["project_id"], {"programme_id": programme_id, "version_id": version_id}, actor=_actor(user))
    return get_programme(store, programme_id)


def act(store: Store, version_id: str, action: str, user: dict, note: str = "") -> dict:
    note = (note or "").strip()
    if len(note) > 2000:
        raise ValueError("Note is limited to 2000 characters")
    with store.connect() as db:
        db.execute("BEGIN IMMEDIATE")
        ver = db.execute("SELECT v.*, p.project_id AS project_id FROM programme_versions v JOIN programmes p ON p.id=v.programme_id WHERE v.id=?", (version_id,)).fetchone()
        if not ver:
            raise KeyError("Programme version not found")
        state = _state(db, version_id)
        rule = TRANSITIONS.get((state, action))
        if rule is None:
            raise ValueError(f"Action '{action}' is not allowed while the version is '{state}'")
        to_state, roles = rule
        if user["role"] not in roles:
            raise PermissionError(f"Role '{user['role']}' cannot perform '{action}'")
        if action == "submit":
            if ver["created_by"] != user["id"]:
                raise PermissionError("Only the author can submit a version for review")
        else:
            if user["id"] == ver["created_by"]:
                raise PermissionError("Four-eyes rule: the author cannot review or approve their own version")
        if action in ("approve", "issue"):
            reviewer = db.execute("SELECT actor_id FROM programme_transitions WHERE version_id=? AND to_state='reviewed' ORDER BY sequence DESC LIMIT 1", (version_id,)).fetchone()
            if action == "approve" and reviewer and reviewer[0] == user["id"]:
                raise PermissionError("Four-eyes rule: the approver must differ from the reviewer")
        if action in ("request_changes",) and not note:
            raise ValueError("A note is required when requesting changes")
        if digest(ver["content"].encode()) != ver["content_sha256"]:
            raise ValueError("Stored content no longer matches its hash; refusing to proceed")
        _append(db, store, version_id, ver["content_sha256"], state, to_state, user, note)
        if action == "issue":
            for old in db.execute("SELECT id, content_sha256 FROM programme_versions WHERE programme_id=? AND id<>?", (ver["programme_id"], version_id)).fetchall():
                if _state(db, old["id"]) == "issued":
                    _append(db, store, old["id"], old["content_sha256"], "issued", "superseded", user, f"Superseded by v{ver['version_no']}")
        store.audit(db, f"programme.{action}", ver["project_id"], {"programme_id": ver["programme_id"], "version_id": version_id, "to": to_state}, actor=_actor(user))
    return get_programme(store, ver["programme_id"])


def _version_view(db, row, include_content: bool) -> dict:
    transitions = [dict(t) for t in db.execute(
        "SELECT t.sequence, t.from_state, t.to_state, t.actor_id, u.username AS actor, t.actor_role, t.note, t.at, t.hash FROM programme_transitions t JOIN users u ON u.id=t.actor_id WHERE t.version_id=? ORDER BY t.sequence", (row["id"],))]
    view = {"id": row["id"], "version_no": row["version_no"], "content_sha256": row["content_sha256"], "created_by": row["created_by"],
            "created_at": row["created_at"], "state": transitions[-1]["to_state"] if transitions else None, "transitions": transitions}
    if include_content:
        view["content"] = json.loads(row["content"])
    return view


def get_programme(store: Store, programme_id: str) -> dict:
    with store.connect() as db:
        prog = db.execute("SELECT * FROM programmes WHERE id=?", (programme_id,)).fetchone()
        if not prog:
            raise KeyError("Programme not found")
        versions = db.execute("SELECT * FROM programme_versions WHERE programme_id=? ORDER BY version_no", (programme_id,)).fetchall()
        return {"id": prog["id"], "project_id": prog["project_id"], "title": prog["title"], "created_by": prog["created_by"],
                "created_at": prog["created_at"], "versions": [_version_view(db, v, True) for v in versions]}


def list_programmes(store: Store, project_id: str) -> list[dict]:
    store.project(project_id)
    with store.connect() as db:
        out = []
        for prog in db.execute("SELECT * FROM programmes WHERE project_id=? ORDER BY created_at DESC", (project_id,)).fetchall():
            versions = db.execute("SELECT * FROM programme_versions WHERE programme_id=? ORDER BY version_no", (prog["id"],)).fetchall()
            views = [_version_view(db, v, False) for v in versions]
            out.append({"id": prog["id"], "title": prog["title"], "created_at": prog["created_at"],
                        "latest_state": views[-1]["state"] if views else None,
                        "issued_version": next((v["version_no"] for v in views if v["state"] == "issued"), None)})
        return out


def verify_version(store: Store, version_id: str) -> dict:
    """Recompute the content hash and the transition hash chain for a version."""
    with store.connect() as db:
        ver = db.execute("SELECT * FROM programme_versions WHERE id=?", (version_id,)).fetchone()
        if not ver:
            raise KeyError("Programme version not found")
        problems = []
        if digest(ver["content"].encode()) != ver["content_sha256"]:
            problems.append("content hash mismatch")
        previous = ZERO
        for t in db.execute("SELECT * FROM programme_transitions WHERE version_id=? ORDER BY sequence", (version_id,)):
            payload = canonical({"version_id": version_id, "content_sha256": ver["content_sha256"], "from": t["from_state"], "to": t["to_state"],
                                 "actor_id": t["actor_id"], "actor_role": t["actor_role"], "note": t["note"], "at": t["at"]})
            if t["previous_hash"] != previous or t["hash"] != digest((previous + payload).encode()):
                problems.append(f"chain broken at sequence {t['sequence']}")
                break
            previous = t["hash"]
        return {"version_id": version_id, "ok": not problems, "problems": problems, "head_hash": previous}
