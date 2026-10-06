import subprocess
import json
import zipfile
import pytest
from tools import sign_windows_binary as signer
from tools import verify_windows_release as release
from tools.source_snapshot import snapshot_files

SNAPSHOT = {"digest": "a" * 64, "files": [{"path": "packages/example.py"}], "scope": "fixture"}


@pytest.fixture(autouse=True)
def fixed_source_snapshot(monkeypatch):
    monkeypatch.setattr(release, "create_source_snapshot", lambda root: SNAPSHOT)


def test_missing_publisher_certificate_cannot_sign(tmp_path, monkeypatch):
    executable = tmp_path / "app.exe"
    executable.write_bytes(b"artifact")
    monkeypatch.setattr(signer, "find_signtool", lambda: tmp_path / "signtool.exe")
    def unexpected(*args, **kwargs):
        pytest.fail("No signer should run without a supplied publisher certificate")
    monkeypatch.setattr(signer.subprocess, "run", unexpected)
    assert not signer.sign_binary(executable)
    assert not signer.sign_binary(executable, allow_self_signed=True)


def test_signing_success_requires_trusted_verification(tmp_path, monkeypatch):
    executable, certificate, signtool = (tmp_path / name for name in ("app.exe", "publisher.pfx", "signtool.exe"))
    for path in (executable, certificate, signtool):
        path.write_bytes(b"fixture")
    monkeypatch.setattr(signer.subprocess, "run", lambda *a, **k: subprocess.CompletedProcess(a[0], 0))
    monkeypatch.setattr(signer, "verify_signature", lambda *a, **k: False)
    assert not signer.sign_binary(executable, certificate, signtool_path=signtool)


def fixture_artifacts(tmp_path, packed_exe=b"executable"):
    dist = tmp_path / "dist"
    (dist / "GeoDrillPro").mkdir(parents=True)
    (dist / "GeoDrillPro" / "GeoDrillPro.exe").write_bytes(b"executable")
    (dist / "GeoDrillPro-Setup.exe").write_bytes(b"installer")
    (dist / "GeoDrillPro" / "SOURCE-SNAPSHOT.json").write_text(json.dumps(SNAPSHOT))
    with zipfile.ZipFile(dist / "GeoDrillPro-Windows-x64.zip", "w") as archive:
        archive.writestr("GeoDrillPro/GeoDrillPro.exe", packed_exe)
        archive.writestr("GeoDrillPro/SOURCE-SNAPSHOT.json", json.dumps(SNAPSHOT))
        archive.writestr("GeoDrillPro/_internal/packages/engineering/directional_cases/manifest.json", "{}")
        archive.writestr("GeoDrillPro/_internal/welleng/errors/tool_codes/example.yaml", "fixture")
    return dist


def test_archive_of_older_executable_rejected(tmp_path):
    fixture_artifacts(tmp_path, b"old executable")
    with pytest.raises(ValueError, match="differs"):
        release.verify("unsigned", tmp_path)


def test_signed_release_cannot_accept_unsigned_artifacts(tmp_path, monkeypatch):
    fixture_artifacts(tmp_path)
    monkeypatch.setattr(release, "verify_signature", lambda *a: False)
    with pytest.raises(ValueError, match="Trusted publisher signature required"):
        release.verify("signed", tmp_path)


def test_unsigned_manifest_records_real_limits(tmp_path, monkeypatch):
    dist = fixture_artifacts(tmp_path)
    monkeypatch.setattr(release, "verify_signature", lambda *a: False)
    monkeypatch.setattr(release.subprocess, "run", lambda *a, **k: subprocess.CompletedProcess(a[0], 0, stdout="source-state"))
    result = release.verify("unsigned", tmp_path)
    assert result["signing_mode"] == "unsigned"
    assert not any(result["trusted_signature_verification"].values())
    assert result["independent_engineering_qualification"] == "pending"
    assert result["source_has_uncommitted_changes"] is True
    assert result["source_snapshot_sha256"] == SNAPSHOT["digest"]
    assert (dist / "SHA256SUMS.txt").exists()


def test_changed_source_after_packaging_is_rejected(tmp_path, monkeypatch):
    fixture_artifacts(tmp_path)
    monkeypatch.setattr(release, "create_source_snapshot", lambda root: {**SNAPSHOT, "digest": "b" * 64})
    with pytest.raises(ValueError, match="Source changed"):
        release.verify("unsigned", tmp_path)


def test_source_snapshot_identifies_dirty_file_contents(tmp_path):
    source = tmp_path / "packages" / "example.py"
    source.parent.mkdir()
    source.write_text("original")
    first = snapshot_files(tmp_path, ["packages/example.py", "docs/evidence/generated.json"])
    source.write_text("changed")
    second = snapshot_files(tmp_path, ["packages/example.py"])
    assert first["digest"] != second["digest"]
    assert len(first["files"]) == 1


def test_source_snapshot_rejects_path_escape(tmp_path):
    with pytest.raises(ValueError, match="escaped"):
        snapshot_files(tmp_path, ["packages/../../external.py"])
