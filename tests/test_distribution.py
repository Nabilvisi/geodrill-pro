import io
import json
from apps.streamlit import distribution


def test_absent_releases_offer_no_fabricated_downloads(monkeypatch):
    monkeypatch.setattr(distribution.urllib.request, "urlopen", lambda *a, **k: io.BytesIO(b"[]"))
    assert distribution.published_assets() == {}


def test_published_assets_reject_drafts_wrong_hosts_and_empty_files(monkeypatch):
    prefix = "https://github.com/Nabilvisi/geodrill-pro/releases/download/v0.8.1/"
    releases = [
        {"draft": True, "assets": [{"name": "GeoDrillPro-Setup.exe", "size": 4, "browser_download_url": prefix + "draft.exe"}]},
        {"draft": False, "assets": [
            {"name": "GeoDrillPro-Setup.exe", "size": 4, "browser_download_url": "https://evil.example/setup.exe"},
            {"name": "SHA256SUMS.txt", "size": 0, "browser_download_url": prefix + "SHA256SUMS.txt"},
            {"name": "GeoDrillPro-Windows-x64.zip", "size": 10, "browser_download_url": prefix + "GeoDrillPro-Windows-x64.zip"},
        ]},
    ]
    monkeypatch.setattr(distribution.urllib.request, "urlopen", lambda *a, **k: io.BytesIO(json.dumps(releases).encode()))
    assert distribution.published_assets() == {"GeoDrillPro-Windows-x64.zip": prefix + "GeoDrillPro-Windows-x64.zip"}


def test_network_failure_withholds_downloads(monkeypatch):
    def fail(*args, **kwargs):
        raise OSError("Unavailable")
    monkeypatch.setattr(distribution.urllib.request, "urlopen", fail)
    assert distribution.published_assets() == {}


def test_local_download_requires_existing_nonempty_artifact(tmp_path):
    assert distribution.local_asset(tmp_path, "GeoDrillPro-Setup.exe") is None
    path = tmp_path / "dist" / "GeoDrillPro-Setup.exe"
    path.parent.mkdir()
    path.write_bytes(b"")
    assert distribution.local_asset(tmp_path, path.name) is None
    path.write_bytes(b"artifact")
    assert distribution.local_asset(tmp_path, path.name) == path
