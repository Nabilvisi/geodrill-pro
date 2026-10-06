"""Verify artifact identity and publisher status before advertising a release."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.sign_windows_binary import verify_signature


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify(mode: str, root: Path = ROOT) -> dict:
    dist = root / "dist"
    executable = dist / "GeoDrillPro" / "GeoDrillPro.exe"
    installer = dist / "GeoDrillPro-Setup.exe"
    archive = dist / "GeoDrillPro-Windows-x64.zip"
    for artifact in (executable, installer, archive):
        if not artifact.is_file() or artifact.stat().st_size == 0:
            raise ValueError(f"Missing release artifact: {artifact.name}")
    with zipfile.ZipFile(archive) as package:
        if package.testzip() is not None:
            raise ValueError("Portable archive CRC check failed")
        if hashlib.sha256(package.read("GeoDrillPro/GeoDrillPro.exe")).hexdigest() != sha256(executable):
            raise ValueError("Portable executable differs from the verified executable")
        names = package.namelist()
        if not any("directional_cases/manifest.json" in name for name in names):
            raise ValueError("Packaged directional reference data missing")
        if not any("welleng/errors/tool_codes" in name for name in names):
            raise ValueError("Packaged survey tool models missing")
    signatures = {path.name: verify_signature(path) for path in (executable, installer)}
    if mode == "signed" and not all(signatures.values()):
        raise ValueError("Trusted publisher signature required on executable and installer")
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=True).stdout.strip()
    dirty = subprocess.run(["git", "status", "--porcelain"], cwd=root, capture_output=True, text=True, check=True).stdout.strip()
    manifest = {
        "version": "0.8.0", "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_commit": head, "source_has_uncommitted_changes": bool(dirty),
        "signing_mode": mode, "trusted_signature_verification": signatures,
        "independent_engineering_qualification": "pending", "external_security_audit": "pending",
        "equipment_control": False, "clearance_generated": False,
        "assets": [{"name": path.name, "size_bytes": path.stat().st_size, "sha256": sha256(path)} for path in (installer, archive)],
        "executable_sha256": sha256(executable),
    }
    (dist / "release-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (dist / "SHA256SUMS.txt").write_text("\n".join(f"{sha256(path)}  {path.name}" for path in (installer, archive, dist / "release-manifest.json")) + "\n", encoding="utf-8")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--signed", action="store_true")
    modes.add_argument("--unsigned", action="store_true")
    args = parser.parse_args()
    print(json.dumps(verify("signed" if args.signed else "unsigned"), indent=2))
