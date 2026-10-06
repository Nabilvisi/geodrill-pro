"""Expose only desktop assets that exist locally or in a published GitHub release."""
from pathlib import Path
import json
import urllib.request

RELEASES_API = "https://api.github.com/repos/Nabilvisi/geodrill-pro/releases?per_page=10"
RELEASES_PAGE = "https://github.com/Nabilvisi/geodrill-pro/releases"
ASSET_NAMES = ("GeoDrillPro-Setup.exe", "GeoDrillPro-Windows-x64.zip", "SHA256SUMS.txt")


def published_assets() -> dict[str, str]:
    request = urllib.request.Request(RELEASES_API, headers={"User-Agent": "GeoDrill-Pro", "Accept": "application/vnd.github+json"})
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            releases = json.loads(response.read(512 * 1024))
    except (OSError, ValueError):
        return {}
    if not isinstance(releases, list):
        return {}
    for release in releases:
        if release.get("draft"):
            continue
        assets = {}
        for asset in release.get("assets", []):
            name, url = asset.get("name"), asset.get("browser_download_url", "")
            if (name in ASSET_NAMES and asset.get("size", 0) > 0
                    and url.startswith("https://github.com/Nabilvisi/geodrill-pro/releases/download/")):
                assets[name] = url
        if assets:
            return assets
    return {}


def local_asset(root: Path, name: str) -> Path | None:
    if name not in ASSET_NAMES:
        raise ValueError("Unsupported release asset")
    path = root / "dist" / name
    return path if path.is_file() and path.stat().st_size > 0 else None
