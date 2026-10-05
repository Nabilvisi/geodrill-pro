"""Team-mode accounts and sessions.

Passwords use scrypt with a per-user salt. Session tokens are random 256-bit values;
only their SHA-256 is stored, so a leaked database cannot be replayed as live sessions.
"""
import hashlib
import hmac
import os
import re
import secrets
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from .storage import Store, now, digest

ROLES = ("admin", "engineer", "reviewer", "approver", "viewer")
SESSION_HOURS = 12
MAX_FAILURES = 5
LOCK_MINUTES = 15
MIN_PASSWORD = 12
_USERNAME = re.compile(r"^[A-Za-z0-9._-]{3,64}$")
_N, _R, _P = 2 ** 14, 8, 1


class AuthError(Exception):
    """Invalid credentials, locked account, or invalid/expired session."""


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    key = hashlib.scrypt(password.encode(), salt=salt, n=_N, r=_R, p=_P, dklen=32)
    return f"scrypt${_N}${_R}${_P}${salt.hex()}${key.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        scheme, n, r, p, salt, key = stored.split("$")
        if scheme != "scrypt":
            return False
        candidate = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=int(n), r=int(r), p=int(p), dklen=32)
        return hmac.compare_digest(candidate, bytes.fromhex(key))
    except (ValueError, TypeError):
        return False


# Used to spend the same time on unknown usernames as on real ones.
_DUMMY_HASH = hash_password("not-a-real-password")


def _public(row) -> dict:
    return {"id": row["id"], "username": row["username"], "display_name": row["display_name"],
            "role": row["role"], "active": bool(row["active"]), "created_at": row["created_at"]}


def create_user(store: Store, username: str, display_name: str, role: str, password: str, actor: str = "system") -> dict:
    if role not in ROLES:
        raise ValueError(f"Role must be one of: {', '.join(ROLES)}")
    if not _USERNAME.match(username or ""):
        raise ValueError("Username must be 3-64 characters: letters, digits, '.', '_' or '-'")
    if len(password or "") < MIN_PASSWORD:
        raise ValueError(f"Password must be at least {MIN_PASSWORD} characters")
    if not (display_name or "").strip():
        raise ValueError("Display name is required")
    user_id = str(uuid4())
    with store.connect() as db:
        db.execute("BEGIN IMMEDIATE")
        if db.execute("SELECT 1 FROM users WHERE username=?", (username,)).fetchone():
            raise ValueError("Username already exists")
        db.execute("INSERT INTO users(id,username,display_name,role,password_hash,created_at) VALUES(?,?,?,?,?,?)",
                   (user_id, username, display_name.strip(), role, hash_password(password), now()))
        store.audit(db, "user.created", None, {"user_id": user_id, "username": username, "role": role}, actor=actor)
        row = db.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    return _public(row)


def list_users(store: Store) -> list[dict]:
    with store.connect() as db:
        return [_public(r) for r in db.execute("SELECT * FROM users ORDER BY username")]


def set_active(store: Store, user_id: str, active: bool, actor: str) -> dict:
    with store.connect() as db:
        db.execute("BEGIN IMMEDIATE")
        row = db.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
        if not row:
            raise KeyError("User not found")
        db.execute("UPDATE users SET active=? WHERE id=?", (1 if active else 0, user_id))
        if not active:
            db.execute("DELETE FROM sessions WHERE user_id=?", (user_id,))
        store.audit(db, "user.activated" if active else "user.deactivated", None, {"user_id": user_id}, actor=actor)
        row = db.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    return _public(row)


def login(store: Store, username: str, password: str) -> tuple[str, dict]:
    """Return (session token, user). Raises AuthError with a deliberately generic message."""
    generic = AuthError("Invalid username or password")
    with store.connect() as db:
        db.execute("BEGIN IMMEDIATE")
        row = db.execute("SELECT * FROM users WHERE username=?", (username or "",)).fetchone()
        if row is None:
            verify_password(password or "", _DUMMY_HASH)
            raise generic
        locked = row["locked_until"] and datetime.fromisoformat(row["locked_until"]) > datetime.now(timezone.utc)
        if locked or not row["active"]:
            verify_password(password or "", _DUMMY_HASH)
            raise generic
        if not verify_password(password or "", row["password_hash"]):
            failures = row["failed_count"] + 1
            until = None
            if failures >= MAX_FAILURES:
                until = (datetime.now(timezone.utc) + timedelta(minutes=LOCK_MINUTES)).isoformat()
                failures = 0
                store.audit(db, "auth.locked", None, {"user_id": row["id"]}, actor=f"user:{row['username']}")
            db.execute("UPDATE users SET failed_count=?, locked_until=? WHERE id=?", (failures, until, row["id"]))
            db.commit()  # persist the failure count even though we raise
            raise generic
        token = secrets.token_urlsafe(32)
        expires = (datetime.now(timezone.utc) + timedelta(hours=SESSION_HOURS)).isoformat()
        db.execute("DELETE FROM sessions WHERE expires_at < ?", (now(),))
        db.execute("INSERT INTO sessions VALUES(?,?,?,?)", (digest(token.encode()), row["id"], now(), expires))
        db.execute("UPDATE users SET failed_count=0, locked_until=NULL WHERE id=?", (row["id"],))
        store.audit(db, "auth.login", None, {"user_id": row["id"]}, actor=f"user:{row['username']}")
        return token, _public(row)


def user_for_token(store: Store, token: str | None) -> dict | None:
    if not token:
        return None
    with store.connect() as db:
        row = db.execute(
            "SELECT u.*, s.expires_at AS expires_at FROM sessions s JOIN users u ON u.id=s.user_id WHERE s.token_hash=? AND u.active=1",
            (digest(token.encode()),)).fetchone()
    if row is None or datetime.fromisoformat(row["expires_at"]) <= datetime.now(timezone.utc):
        return None
    return _public(row)


def logout(store: Store, token: str | None) -> None:
    if token:
        with store.connect() as db:
            db.execute("DELETE FROM sessions WHERE token_hash=?", (digest(token.encode()),))
