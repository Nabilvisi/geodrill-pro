"""Project archive restoration preserves readable studies without replacing other evidence."""
import io
import json
import sqlite3
import zipfile

import pytest
from fastapi.testclient import TestClient
from services.api import auth, programmes
from services.api.main import create_app
from services.api.storage import Store, canonical


def bundle_fixture(tmp_path):
    source = Store(tmp_path / "source")
    project = source.create_project({"name": "Synthetic archive", "origin": "synthetic"})
    study = source.calculation(project["id"], "test", {"source": "synthetic"}, {"value": 3})
    return source, project, study, source.export_bundle(project["id"])


def altered_bundle(raw, mutate):
    with zipfile.ZipFile(io.BytesIO(raw)) as zf:
        entries = {name: zf.read(name) for name in zf.namelist()}
    mutate(entries)
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, data in entries.items():
            zf.writestr(name, data)
    return out.getvalue()


def test_restored_studies_reopen_against_the_new_audit_chain(tmp_path):
    _, project, study, raw = bundle_fixture(tmp_path)
    destination = Store(tmp_path / "restored")
    destination.restore_bundle(raw)
    assert destination.calculations(project["id"]) == [study]
    history = destination.audit_history()
    assert history["integrity"] == "verified"
    assert any(e["action"] == "calculation.restored" and e["details"] == study for e in history["entries"])
    imported = next(e for e in history["entries"] if e["action"] == "bundle.restored")
    assert imported["details"]["original_history"]
    assert imported["details"]["independently_trusted_signer"] is False


@pytest.mark.parametrize("signature", [None, "00" * 64])
def test_missing_or_invalid_signature_cannot_add_a_trusted_key(tmp_path, signature):
    source, _, _, raw = bundle_fixture(tmp_path)
    def mutate(entries):
        manifest = json.loads(entries["manifest.json"])
        if signature is None:
            manifest.pop("signature")
        else:
            manifest["signature"] = signature
        entries["manifest.json"] = canonical(manifest).encode()
    destination = Store(tmp_path / "restored")
    before = set(destination._trusted_keys)
    with pytest.raises(ValueError, match="signature verification failed"):
        destination.restore_bundle(altered_bundle(raw, mutate))
    assert set(destination._trusted_keys) == before
    assert not list((destination.root / "keys" / "trusted").iterdir())
    assert destination.projects() == []


def test_untracked_archive_member_is_rejected(tmp_path):
    _, _, _, raw = bundle_fixture(tmp_path)
    changed = altered_bundle(raw, lambda entries: entries.update({"extra.json": b"{}"}))
    destination = Store(tmp_path / "restored")
    with pytest.raises(ValueError, match="complete archive"):
        destination.restore_bundle(changed)
    assert destination.projects() == []


def test_signed_cross_project_record_is_rejected_before_restore(tmp_path):
    source, _, _, raw = bundle_fixture(tmp_path)
    def mutate(entries):
        records = json.loads(entries["calculations/calculations.json"])
        records[0]["project_id"] = "different-project"
        entries["calculations/calculations.json"] = canonical(records).encode()
        manifest = json.loads(entries["manifest.json"])
        from services.api.storage import digest
        manifest["file_hashes"]["calculations/calculations.json"] = digest(entries["calculations/calculations.json"])
        manifest.pop("signature")
        manifest["signature"] = source.sign_attestation(canonical(manifest).encode())
        entries["manifest.json"] = canonical(manifest).encode()
    destination = Store(tmp_path / "restored")
    with pytest.raises(ValueError, match="different project"):
        destination.restore_bundle(altered_bundle(raw, mutate))
    assert destination.projects() == []


def test_restoring_a_second_project_preserves_existing_programme_transitions(tmp_path):
    source = Store(tmp_path / "source")
    engineer = auth.create_user(source, "engineer", "Synthetic engineer", "engineer", "synthetic-password")
    destination = Store(tmp_path / "restored")
    versions = []
    for name in ("First", "Second"):
        project = source.create_project({"name": name, "origin": "synthetic"})
        programme = programmes.create_programme(source, project["id"], name, {"purpose": "synthetic"}, engineer)
        version = programme["versions"][0]["id"]
        programmes.act(source, version, "submit", engineer, "Synthetic submission")
        versions.append(version)
        destination.restore_bundle(source.export_bundle(project["id"]))
    assert all(programmes.verify_version(destination, v)["ok"] for v in versions)
    with destination.connect() as db:
        assert db.execute("SELECT COUNT(*) FROM programme_transitions").fetchone()[0] == 4


def test_reexported_project_preserves_original_programme_signatures(tmp_path):
    source = Store(tmp_path / "source")
    engineer = auth.create_user(source, "engineer", "Synthetic engineer", "engineer", "synthetic-password")
    project = source.create_project({"name": "Re-export", "origin": "synthetic"})
    programme = programmes.create_programme(source, project["id"], "Programme", {"purpose": "synthetic"}, engineer)
    version = programme["versions"][0]["id"]
    first = Store(tmp_path / "first")
    first.restore_bundle(source.export_bundle(project["id"]))
    second = Store(tmp_path / "second")
    second.restore_bundle(first.export_bundle(project["id"]))
    assert programmes.verify_version(second, version)["ok"]


def test_team_engineer_cannot_restore_identity_bearing_archives(tmp_path):
    app = create_app(tmp_path / "team", mode="team")
    auth.create_user(app.state.store, "engineer", "Engineer", "engineer", "synthetic-password")
    client = TestClient(app)
    token = client.post("/api/team/login", json={"username": "engineer", "password": "synthetic-password"}).json()["token"]
    response = client.post("/api/projects/bundle/restore", files={"file": ("archive.gdpz", b"invalid", "application/zip")}, headers={"Authorization": "Bearer " + token})
    assert response.status_code == 403
    assert "Administrator role" in response.json()["detail"]


def test_failed_restore_rolls_back_new_evidence_files_and_database(tmp_path):
    source, project, _, _ = bundle_fixture(tmp_path)
    source.import_data(project["id"], "telemetry", "source.csv", b"v\n1\n", [{"v": 1}], {}, [])
    raw = source.export_bundle(project["id"])
    def mutate(entries):
        from services.api.storage import digest
        entries["members/members.json"] = canonical([{"project_id": project["id"], "user_id": "missing-user", "added_by": "synthetic", "added_at": "2026-10-06"}]).encode()
        manifest = json.loads(entries["manifest.json"])
        manifest["file_hashes"]["members/members.json"] = digest(entries["members/members.json"])
        manifest.pop("signature")
        manifest["signature"] = source.sign_attestation(canonical(manifest).encode())
        entries["manifest.json"] = canonical(manifest).encode()
    destination = Store(tmp_path / "restored")
    with pytest.raises(sqlite3.IntegrityError):
        destination.restore_bundle(altered_bundle(raw, mutate))
    assert destination.projects() == []
    assert list((destination.root / "raw").iterdir()) == []
    assert list((destination.root / "parquet").iterdir()) == []
    assert list((destination.root / "keys" / "trusted").iterdir()) == []
