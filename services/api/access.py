"""Team-mode authorization policy: role gates for the existing routes and per-project membership.

The policy is deliberately central and pure so that it can be tested exhaustively, and so
that new routes are protected by default rather than by remembering to add a check:

* GET/HEAD/OPTIONS: any signed-in user who is a member of the project (admins: all projects).
* Any other method under /api/ that is not one of the self-authorising team routes:
  engineers and admins only. Viewers, reviewers and approvers are read-only on engineering data.
* /api/audit (the global audit chain spans every project): admins only.
* Non-members get 404, not 403, so project existence is not disclosed.
"""
import re

from .storage import Store, now

WRITE_ROLES = frozenset({"engineer", "admin"})
SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})

_PROJECT_PATH = re.compile(r"^/api/projects/([^/]+)(?:/(.*))?$")
# Routes whose own handlers enforce finer-grained roles (programme workflow, membership).
_SELF_AUTHORISED = re.compile(r"^/api/(team/|projects/[^/]+/(programmes|members)(/|$))")


def project_id_from_path(path: str) -> str | None:
    match = _PROJECT_PATH.match(path)
    return match.group(1) if match else None


def role_denial(method: str, path: str, user: dict) -> str | None:
    """Return a reason string if this user's role may not call this route, else None."""
    if path == "/api/audit" or path.startswith("/api/audit/"):
        return None if user["role"] == "admin" else "Administrator role required"
    if path == "/api/projects/bundle/restore":
        return None if user["role"] == "admin" else "Administrator role required for identity-bearing project restore"
    if method.upper() in SAFE_METHODS or _SELF_AUTHORISED.match(path):
        return None
    if user["role"] not in WRITE_ROLES:
        return f"Role '{user['role']}' is read-only on engineering data"
    return None


def is_member(store: Store, user: dict, project_id: str) -> bool:
    if user["role"] == "admin":
        return True
    with store.connect() as db:
        return db.execute("SELECT 1 FROM project_members WHERE project_id=? AND user_id=?", (project_id, user["id"])).fetchone() is not None


def require_member(store: Store, user: dict, project_id: str) -> None:
    if not is_member(store, user, project_id):
        raise KeyError("Project not found")


def visible_projects(store: Store, user: dict) -> list[dict]:
    projects = store.projects()
    if user["role"] == "admin":
        return projects
    with store.connect() as db:
        allowed = {r[0] for r in db.execute("SELECT project_id FROM project_members WHERE user_id=?", (user["id"],))}
    return [p for p in projects if p["id"] in allowed]


def add_member(store: Store, project_id: str, user_id: str, actor: dict | str, *, quiet: bool = False) -> None:
    """Grant a user access to a project. Idempotent. ``quiet`` skips the audit entry when nothing changed."""
    store.project(project_id)
    actor_label = actor if isinstance(actor, str) else f"user:{actor['username']}"
    actor_id = "system" if isinstance(actor, str) else actor["id"]
    with store.connect() as db:
        db.execute("BEGIN IMMEDIATE")
        target = db.execute("SELECT id, active FROM users WHERE id=?", (user_id,)).fetchone()
        if not target:
            raise KeyError("User not found")
        if not target["active"]:
            raise ValueError("Cannot add a deactivated user")
        cursor = db.execute("INSERT OR IGNORE INTO project_members VALUES(?,?,?,?)", (project_id, user_id, actor_id, now()))
        if cursor.rowcount or not quiet:
            store.audit(db, "project.member_added", project_id, {"user_id": user_id, "new": bool(cursor.rowcount)}, actor=actor_label)


def remove_member(store: Store, project_id: str, user_id: str, actor: dict) -> None:
    store.project(project_id)
    with store.connect() as db:
        db.execute("BEGIN IMMEDIATE")
        cursor = db.execute("DELETE FROM project_members WHERE project_id=? AND user_id=?", (project_id, user_id))
        if not cursor.rowcount:
            raise KeyError("Membership not found")
        store.audit(db, "project.member_removed", project_id, {"user_id": user_id}, actor=f"user:{actor['username']}")


def list_members(store: Store, project_id: str) -> list[dict]:
    store.project(project_id)
    with store.connect() as db:
        return [dict(r) for r in db.execute(
            "SELECT u.id, u.username, u.display_name, u.role, m.added_at FROM project_members m JOIN users u ON u.id=m.user_id WHERE m.project_id=? ORDER BY u.username",
            (project_id,))]


def project_for_programme(store: Store, programme_id: str) -> str:
    with store.connect() as db:
        row = db.execute("SELECT project_id FROM programmes WHERE id=?", (programme_id,)).fetchone()
    if not row:
        raise KeyError("Programme not found")
    return row[0]


def project_for_version(store: Store, version_id: str) -> str:
    with store.connect() as db:
        row = db.execute("SELECT p.project_id FROM programme_versions v JOIN programmes p ON p.id=v.programme_id WHERE v.id=?", (version_id,)).fetchone()
    if not row:
        raise KeyError("Programme version not found")
    return row[0]
