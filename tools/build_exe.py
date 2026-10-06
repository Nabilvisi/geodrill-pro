"""Publish an explicit unsigned research bundle or a verified publisher-signed bundle."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from packages.frontend import frontend_dist
from tools.sign_windows_binary import sign_binary
from tools.source_snapshot import create_source_snapshot


def build(mode: str, cert: Path | None = None) -> Path:
    if os.name != "nt":
        raise RuntimeError("Windows packaging must run on Windows.")
    if mode == "signed" and (cert is None or not cert.is_file()):
        raise RuntimeError("Publisher PFX is required for a signed build.")
    frontend = frontend_dist(ROOT)
    if not (frontend / "index.html").is_file():
        raise RuntimeError("Run tools/build.py before packaging.")
    source_snapshot = create_source_snapshot(ROOT)
    stage = ROOT / "build" / ("windows-" + uuid4().hex)
    frontend_rel = frontend.relative_to(ROOT)
    command = [
        sys.executable, "-m", "PyInstaller", "--noconfirm", "--onedir", "--windowed",
        "--name", "GeoDrillPro", "--distpath", str(stage / "dist"),
        "--workpath", str(stage / "work"), "--specpath", str(stage),
        "--add-data", f"{frontend};{frontend_rel}",
        "--add-data", f"{ROOT / 'frontend-build.json'};.",
        "--add-data", f"{ROOT / 'public'};public",
        "--collect-submodules", "packages", "--collect-data", "packages",
        "--collect-submodules", "services", "--collect-data", "welleng",
        "--hidden-import", "uvicorn.logging",
        "--hidden-import", "uvicorn.loops.auto",
        "--hidden-import", "uvicorn.protocols.http.auto",
        "--hidden-import", "uvicorn.lifespan.on",
        "--hidden-import", "tools.backup_restore",
        str(ROOT / "tools" / "desktop_app.py"),
    ]
    subprocess.run(command, cwd=ROOT, check=True)
    staged_bundle = stage / "dist" / "GeoDrillPro"
    executable = staged_bundle / "GeoDrillPro.exe"
    if create_source_snapshot(ROOT)["digest"] != source_snapshot["digest"]:
        raise RuntimeError("Source changed during packaging; no release package was selected.")
    (staged_bundle / "SOURCE-SNAPSHOT.json").write_text(
        json.dumps(source_snapshot, indent=2) + "\n", encoding="utf-8"
    )
    if mode == "signed" and not sign_binary(executable, cert, os.environ.get("GEODRILL_SIGN_PASSWORD")):
        raise RuntimeError("Publisher signing/trust verification failed; no release package was selected.")
    (staged_bundle / "RELEASE-NOTICE.txt").write_text(
        "GeoDrill Pro engineering research workstation.\n"
        f"Signing mode: {mode}.\n"
        "Independent engineering/security qualification pending.\n"
        "Equipment control and automated drilling clearance unavailable.\n",
        encoding="utf-8",
    )
    final_bundle = ROOT / "dist" / "GeoDrillPro"
    # Retain the previous successful build rather than deleting it.
    for path in (final_bundle, staged_bundle):
        if not path.resolve().is_relative_to(ROOT.resolve()):
            raise RuntimeError("Packaging path escaped the workspace.")
    if final_bundle.exists():
        final_bundle.rename(ROOT / "build" / ("windows-previous-" + uuid4().hex))
    staged_bundle.rename(final_bundle)
    archive = ROOT / "dist" / "GeoDrillPro-Windows-x64"
    shutil.make_archive(str(archive), "zip", root_dir=final_bundle.parent, base_dir=final_bundle.name)
    print(f"Created {mode} bundle: {archive}.zip")
    return archive.with_suffix(".zip")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--unsigned", action="store_true", help="Explicit unsigned research package")
    modes.add_argument("--sign", action="store_true", help="Require trusted publisher signature")
    parser.add_argument("--cert", type=Path)
    args = parser.parse_args()
    build("signed" if args.sign else "unsigned", args.cert)


if __name__ == "__main__":
    main()
