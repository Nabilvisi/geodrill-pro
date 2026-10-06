"""Recovery preserves original sources, reports, credentials, keys and audit history."""
import hashlib
import io
import json
import sqlite3
import os
import subprocess
import sys
import zipfile

import pytest

from services.api.storage import Store
from tools import backup_restore as recovery


def create_source(tmp_path):
    source = tmp_path / "source"
    store = Store(source)
    project = store.create_project({"name": "Recovery verification", "origin": "synthetic"})
    raw = b"value\n1\n"
    store.import_data(project["id"], "telemetry", "original.csv", raw, [{"value": 1}], {}, [])
    report = store.create_report(project["id"])
    return source, store, project, report


def test_whole_workstation_roundtrip_preserves_evidence_and_signer(tmp_path):
    source, original, project, report = create_source(tmp_path)
    signature = original.sign_attestation(b"historical programme")
    archive = tmp_path / "backup.zip"
    saved = recovery.backup_workstation(source, archive)
    restored_path = tmp_path / "restored"
    result = recovery.restore_workstation(archive, restored_path, saved["sha256"])
    restored = Store(restored_path)
    assert result["restored"] is True
    assert restored.project(project["id"]) == original.project(project["id"])
    assert restored.report(project["id"], report["id"]) == original.report(project["id"], report["id"])
    for dataset in restored.datasets(project["id"]):
        assert restored.dataset(project["id"], dataset["id"])["rows"] == original.dataset(project["id"], dataset["id"])["rows"]
    assert restored.audit_history() == original.audit_history()
    assert restored.attestation_fingerprint == original.attestation_fingerprint
    assert restored.verify_attestation(b"historical programme", signature)
    with original.connect() as left, restored.connect() as right:
        assert [tuple(r) for r in left.execute("SELECT * FROM audit ORDER BY sequence")] == [tuple(r) for r in right.execute("SELECT * FROM audit ORDER BY sequence")]


def test_wal_committed_record_is_in_snapshot(tmp_path):
    source, store, project, _ = create_source(tmp_path)
    writer = sqlite3.connect(store.db)
    writer.execute("PRAGMA wal_autocheckpoint=0")
    writer.execute("INSERT INTO projects VALUES('wal-record','{}','2026-01-01')")
    writer.commit()
    assert (source / "geodrill.sqlite3-wal").exists()
    archive = tmp_path / "wal.zip"
    saved = recovery.backup_workstation(source, archive)
    target = tmp_path / "recovered"
    recovery.restore_workstation(archive, target, saved["sha256"])
    assert Store(target).project("wal-record")["id"] == "wal-record"
    writer.close()


def test_wrong_archive_hash_and_existing_destination_preserve_data(tmp_path):
    source, _, _, _ = create_source(tmp_path)
    archive = tmp_path / "backup.zip"
    saved = recovery.backup_workstation(source, archive)
    target = tmp_path / "target"
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        recovery.restore_workstation(archive, target, "0" * 64)
    assert not target.exists()
    target.mkdir()
    marker = target / "precious.txt"
    marker.write_text("preserved")
    with pytest.raises(ValueError, match="new destination"):
        recovery.restore_workstation(archive, target, saved["sha256"])
    assert marker.read_text() == "preserved"


def rewrite_archive(archive, mutate):
    with zipfile.ZipFile(archive) as zf:
        entries = {i.filename: zf.read(i) for i in zf.infolist()}
    mutate(entries)
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, data in entries.items():
            zf.writestr(name, data)
    archive.write_bytes(output.getvalue())
    return recovery.file_hash(archive)


def test_changed_member_rejected_even_with_updated_outer_hash(tmp_path):
    source, _, _, _ = create_source(tmp_path)
    archive = tmp_path / "backup.zip"
    recovery.backup_workstation(source, archive)
    def mutate(entries):
        name = next(n for n in entries if n.startswith("raw/"))
        entries[name] = b"value\n9\n"
    expected = rewrite_archive(archive, mutate)
    target = tmp_path / "target"
    with pytest.raises(ValueError, match="entry SHA-256 mismatch"):
        recovery.restore_workstation(archive, target, expected)
    assert not target.exists()


@pytest.mark.parametrize("name", ["../escape.txt", "raw/../../escape.txt", "C:/escape.txt", "keys/CON.key"])
def test_unsafe_members_cannot_escape_new_restore_directory(tmp_path, name):
    source, _, _, _ = create_source(tmp_path)
    archive = tmp_path / "backup.zip"
    recovery.backup_workstation(source, archive)
    def mutate(entries):
        entries[name] = b"unsafe"
        manifest = json.loads(entries["manifest.json"])
        manifest["files"][name] = {"sha256": hashlib.sha256(b"unsafe").hexdigest(), "size_bytes": 6}
        entries["manifest.json"] = json.dumps(manifest).encode()
    expected = rewrite_archive(archive, mutate)
    with pytest.raises(ValueError, match="insecure entry"):
        recovery.restore_workstation(archive, tmp_path / "target", expected)
    assert not (tmp_path / "escape.txt").exists()
    assert not (tmp_path / "target").exists()


def test_backup_refuses_destination_inside_source_and_existing_file(tmp_path):
    source, _, _, _ = create_source(tmp_path)
    with pytest.raises(ValueError, match="outside"):
        recovery.backup_workstation(source, source / "backup.zip")
    archive = tmp_path / "preserved.zip"
    archive.write_bytes(b"keep")
    with pytest.raises(ValueError, match="already exists"):
        recovery.backup_workstation(source, archive)
    assert archive.read_bytes() == b"keep"


def test_desktop_recovery_does_not_start_or_modify_active_workstation(tmp_path, monkeypatch):
    from tools import desktop_app
    source, _, project, _ = create_source(tmp_path)
    monkeypatch.setenv("GEODRILL_DATA_DIR", str(source))
    monkeypatch.setattr(desktop_app, "create_app", lambda **kwargs: pytest.fail("Recovery must not start or migrate the application"))
    archive = tmp_path / "desktop.zip"
    monkeypatch.setattr("sys.argv", ["GeoDrillPro.exe", "--backup", str(archive)])
    assert desktop_app.main() == 0
    receipt = json.loads((tmp_path / "desktop.zip.receipt.json").read_text())
    destination = tmp_path / "desktop-restored"
    monkeypatch.setattr("sys.argv", ["GeoDrillPro.exe", "--restore", str(archive), "--destination", str(destination), "--expected-sha256", receipt["sha256"]])
    assert desktop_app.main() == 0
    assert Store(destination).project(project["id"])["id"] == project["id"]


def test_preexisting_source_corruption_is_not_blessed_by_a_new_backup_hash(tmp_path):
    source, _, _, _ = create_source(tmp_path)
    next((source / "raw").iterdir()).write_bytes(b"changed source")
    archive = tmp_path / "bad.zip"
    with pytest.raises(ValueError, match="Original source evidence hash"):
        recovery.backup_workstation(source, archive)
    assert not archive.exists()


def test_missing_normalized_evidence_refuses_backup(tmp_path):
    source, _, _, _ = create_source(tmp_path)
    next((source / "parquet").iterdir()).unlink()
    archive = tmp_path / "missing.zip"
    with pytest.raises(ValueError, match="Normalized evidence hash"):
        recovery.backup_workstation(source, archive)
    assert not archive.exists()


def test_importing_api_or_desktop_does_not_create_or_migrate_default_data(tmp_path):
    selected = tmp_path / "must-remain-absent"
    env = {**os.environ, "GEODRILL_DATA_DIR": str(selected)}
    subprocess.run([sys.executable, "-c", "import services.api.main; import tools.desktop_app"],
                   env=env, check=True, timeout=30)
    assert not selected.exists()
