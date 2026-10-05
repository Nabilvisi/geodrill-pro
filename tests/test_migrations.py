import sqlite3
import pytest
from services.api import migrations
from services.api.migrations import migrate, current_version, latest_version, BASELINE_V2
from services.api.storage import Store


def test_fresh_database_reaches_latest(tmp_path):
    db = sqlite3.connect(tmp_path / "a.sqlite3")
    assert migrate(db) == [m[0] for m in migrations.MIGRATIONS]
    assert current_version(db) == latest_version()


def test_migrate_is_idempotent(tmp_path):
    db = sqlite3.connect(tmp_path / "a.sqlite3")
    migrate(db)
    assert migrate(db) == []


def test_legacy_v2_database_keeps_data(tmp_path):
    """A database created before the migration runner (user_version=2) keeps its data and
    receives only the migrations newer than v2."""
    path = tmp_path / "legacy.sqlite3"
    db = sqlite3.connect(path)
    db.executescript(BASELINE_V2)
    db.execute("INSERT INTO projects VALUES('p1','{}','2026-01-01')")
    db.execute("PRAGMA user_version=2")
    db.commit()
    assert migrate(db) == [v for v, _ in migrations.MIGRATIONS if v > 2]
    assert current_version(db) == latest_version()
    assert db.execute("SELECT id FROM projects").fetchall() == [("p1",)]


def test_newer_database_is_refused(tmp_path):
    db = sqlite3.connect(tmp_path / "future.sqlite3")
    db.execute(f"PRAGMA user_version={latest_version() + 1}")
    with pytest.raises(RuntimeError, match="newer than this application"):
        migrate(db)


def test_pending_migration_is_applied_in_order(tmp_path, monkeypatch):
    monkeypatch.setattr(migrations, "MIGRATIONS", [*migrations.MIGRATIONS, (latest_version() + 1, "CREATE TABLE t(x);")])
    db = sqlite3.connect(tmp_path / "a.sqlite3")
    assert migrate(db)[-1] == latest_version()
    assert db.execute("SELECT name FROM sqlite_master WHERE name='t'").fetchone()


def test_duplicate_versions_rejected(tmp_path, monkeypatch):
    monkeypatch.setattr(migrations, "MIGRATIONS", [(2, "SELECT 1;"), (2, "SELECT 1;")])
    with pytest.raises(RuntimeError, match="unique and increasing"):
        migrate(sqlite3.connect(tmp_path / "a.sqlite3"))


def test_store_creates_schema_and_audit_chain_still_append_only(tmp_path):
    store = Store(tmp_path)
    store.create_project({"name": "t"})  # writes one audit row; triggers are row-level
    with store.connect() as db:
        assert current_version(db) == latest_version()
        with pytest.raises(sqlite3.DatabaseError, match="append-only"):
            db.execute("DELETE FROM audit")
