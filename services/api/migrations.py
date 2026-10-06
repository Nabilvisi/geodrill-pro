"""Versioned SQLite schema migrations.

The schema version is stored in ``PRAGMA user_version``. Databases created before this
module existed are already at version 2, so the original schema is migration 2 and is
skipped for them. Add new migrations to ``MIGRATIONS`` with the next integer version;
never edit or reorder an existing entry.
"""
import sqlite3

BASELINE_V2 = '''
    PRAGMA journal_mode=WAL;
    CREATE TABLE IF NOT EXISTS projects(id TEXT PRIMARY KEY, payload TEXT NOT NULL, created_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS datasets(id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES projects(id), kind TEXT NOT NULL, source_hash TEXT NOT NULL, payload TEXT NOT NULL, created_at TEXT NOT NULL, UNIQUE(project_id,kind,source_hash));
    CREATE TABLE IF NOT EXISTS events(id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES projects(id), dataset_id TEXT NOT NULL REFERENCES datasets(id), payload TEXT NOT NULL, acknowledgement TEXT);
    CREATE TABLE IF NOT EXISTS calculations(id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES projects(id), payload TEXT NOT NULL, created_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS reports(id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES projects(id), payload TEXT NOT NULL, sha256 TEXT NOT NULL, created_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS audit(sequence INTEGER PRIMARY KEY AUTOINCREMENT, payload TEXT NOT NULL, previous_hash TEXT NOT NULL, hash TEXT NOT NULL);
    CREATE TRIGGER IF NOT EXISTS audit_no_update BEFORE UPDATE ON audit BEGIN SELECT RAISE(ABORT,'Audit records are append-only'); END;
    CREATE TRIGGER IF NOT EXISTS audit_no_delete BEFORE DELETE ON audit BEGIN SELECT RAISE(ABORT,'Audit records are append-only'); END;
    CREATE TRIGGER IF NOT EXISTS reports_no_update BEFORE UPDATE ON reports BEGIN SELECT RAISE(ABORT,'Reports are immutable'); END;
    CREATE TABLE IF NOT EXISTS engineering_revisions(id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES projects(id), module TEXT NOT NULL, payload TEXT NOT NULL, sha256 TEXT NOT NULL, created_at TEXT NOT NULL);
    CREATE TRIGGER IF NOT EXISTS revisions_no_update BEFORE UPDATE ON engineering_revisions BEGIN SELECT RAISE(ABORT,'Engineering revisions are immutable'); END;
    CREATE TRIGGER IF NOT EXISTS revisions_no_delete BEFORE DELETE ON engineering_revisions BEGIN SELECT RAISE(ABORT,'Engineering revisions are immutable'); END;
    CREATE TRIGGER IF NOT EXISTS calculations_no_update BEFORE UPDATE ON calculations BEGIN SELECT RAISE(ABORT,'Calculations are immutable'); END;
    CREATE TRIGGER IF NOT EXISTS calculations_no_delete BEFORE DELETE ON calculations BEGIN SELECT RAISE(ABORT,'Calculations are immutable'); END;
'''

TEAM_V3 = '''
    CREATE TABLE IF NOT EXISTS users(
        id TEXT PRIMARY KEY,
        username TEXT NOT NULL UNIQUE COLLATE NOCASE,
        display_name TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('admin','engineer','reviewer','approver','viewer')),
        password_hash TEXT NOT NULL,
        active INTEGER NOT NULL DEFAULT 1,
        failed_count INTEGER NOT NULL DEFAULT 0,
        locked_until TEXT,
        created_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS sessions(
        token_hash TEXT PRIMARY KEY,
        user_id TEXT NOT NULL REFERENCES users(id),
        created_at TEXT NOT NULL,
        expires_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS programmes(
        id TEXT PRIMARY KEY,
        project_id TEXT NOT NULL REFERENCES projects(id),
        title TEXT NOT NULL,
        created_by TEXT NOT NULL REFERENCES users(id),
        created_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS programme_versions(
        id TEXT PRIMARY KEY,
        programme_id TEXT NOT NULL REFERENCES programmes(id),
        version_no INTEGER NOT NULL,
        content TEXT NOT NULL,
        content_sha256 TEXT NOT NULL,
        created_by TEXT NOT NULL REFERENCES users(id),
        created_at TEXT NOT NULL,
        UNIQUE(programme_id, version_no));
    CREATE TABLE IF NOT EXISTS programme_transitions(
        sequence INTEGER PRIMARY KEY AUTOINCREMENT,
        version_id TEXT NOT NULL REFERENCES programme_versions(id),
        from_state TEXT,
        to_state TEXT NOT NULL,
        actor_id TEXT NOT NULL REFERENCES users(id),
        actor_role TEXT NOT NULL,
        note TEXT NOT NULL DEFAULT '',
        at TEXT NOT NULL,
        previous_hash TEXT NOT NULL,
        hash TEXT NOT NULL);
    CREATE TRIGGER IF NOT EXISTS pv_no_update BEFORE UPDATE ON programme_versions BEGIN SELECT RAISE(ABORT,'Programme versions are immutable'); END;
    CREATE TRIGGER IF NOT EXISTS pv_no_delete BEFORE DELETE ON programme_versions BEGIN SELECT RAISE(ABORT,'Programme versions are immutable'); END;
    CREATE TRIGGER IF NOT EXISTS pt_no_update BEFORE UPDATE ON programme_transitions BEGIN SELECT RAISE(ABORT,'Programme transitions are append-only'); END;
    CREATE TRIGGER IF NOT EXISTS pt_no_delete BEFORE DELETE ON programme_transitions BEGIN SELECT RAISE(ABORT,'Programme transitions are append-only'); END;
    CREATE INDEX IF NOT EXISTS pt_version ON programme_transitions(version_id, sequence);
'''

MEMBERS_V4 = '''
    CREATE TABLE IF NOT EXISTS project_members(
        project_id TEXT NOT NULL REFERENCES projects(id),
        user_id TEXT NOT NULL REFERENCES users(id),
        added_by TEXT NOT NULL,
        added_at TEXT NOT NULL,
        PRIMARY KEY(project_id, user_id));
    CREATE INDEX IF NOT EXISTS pm_user ON project_members(user_id);
'''

WORKFLOW_V5 = '''
    ALTER TABLE programme_versions ADD COLUMN evidence_bindings TEXT NOT NULL DEFAULT '[]';
    ALTER TABLE programme_transitions ADD COLUMN signature TEXT NOT NULL DEFAULT '';
    ALTER TABLE programme_transitions ADD COLUMN signer_fingerprint TEXT NOT NULL DEFAULT '';
'''

# (version, SQL script). Versions must be strictly increasing.
MIGRATIONS: list[tuple[int, str]] = [
    (2, BASELINE_V2),
    (3, TEAM_V3),
    (4, MEMBERS_V4),
    (5, WORKFLOW_V5),
]


def current_version(db: sqlite3.Connection) -> int:
    return db.execute("PRAGMA user_version").fetchone()[0]


def latest_version() -> int:
    return MIGRATIONS[-1][0]


def migrate(db: sqlite3.Connection) -> list[int]:
    """Apply pending migrations in order. Returns the versions applied."""
    versions = [v for v, _ in MIGRATIONS]
    if versions != sorted(set(versions)):
        raise RuntimeError("Migration versions must be unique and increasing")
    version = current_version(db)
    if version > latest_version():
        raise RuntimeError(f"Database schema v{version} is newer than this application (v{latest_version()})")
    applied = []
    for target, script in MIGRATIONS:
        if target > version:
            db.executescript(script)
            db.execute(f"PRAGMA user_version={int(target)}")
            applied.append(target)
    return applied
