"""Build the standalone GeoDrillPro.exe executable using PyInstaller.

Bundles:
- Backend: FastAPI, Polars, DuckDB, Pydantic, Uvicorn, Engineering physics models
- Frontend: Compiled React + Vite production build (from frontend-build.json)
- Static assets & favicon
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from packages.frontend import frontend_dist

dist_dir = frontend_dist(ROOT)
if not (dist_dir / "index.html").is_file():
    raise SystemExit("Frontend build is missing or incomplete. Run build first.")

# Relative path for frontend inside bundle
frontend_rel = dist_dir.relative_to(ROOT)

# Clean previous build artifacts if present
shutil.rmtree(ROOT / "dist" / "GeoDrillPro", ignore_errors=True)

pyinstaller_cmd = [
    str(ROOT / ".venv" / "Scripts" / "pyinstaller.exe"),
    "--noconfirm",
    "--onedir",  # onedir is faster to launch and avoids extracting hundreds of MBs on every click
    "--windowed", # Windows GUI app without lingering cmd console
    "--name", "GeoDrillPro",
    "--add-data", f"{dist_dir};{frontend_rel}",
    "--add-data", f"{ROOT / 'frontend-build.json'};.",
    "--add-data", f"{ROOT / 'public'};public",
    "--collect-submodules", "packages",
    "--collect-submodules", "services",
    "--hidden-import", "uvicorn.logging",
    "--hidden-import", "uvicorn.loops",
    "--hidden-import", "uvicorn.loops.auto",
    "--hidden-import", "uvicorn.protocols",
    "--hidden-import", "uvicorn.protocols.http",
    "--hidden-import", "uvicorn.protocols.http.auto",
    "--hidden-import", "uvicorn.lifespans",
    "--hidden-import", "uvicorn.lifespans.on",
    "--hidden-import", "starlette.middleware",
    "--hidden-import", "starlette.middleware.base",
    "--hidden-import", "services.api.main",
    "--hidden-import", "services.api.access",
    "--hidden-import", "services.api.auth",
    "--hidden-import", "services.api.migrations",
    "--hidden-import", "services.api.programmes",
    "--hidden-import", "services.api.team",
    str(ROOT / "tools" / "desktop_app.py")
]

print("Running PyInstaller build for GeoDrill Pro...")
code = subprocess.call(pyinstaller_cmd, cwd=ROOT)
if code != 0:
    sys.exit(code)

print("\nPyInstaller build completed successfully!")
exe_path = ROOT / "dist" / "GeoDrillPro" / "GeoDrillPro.exe"
print(f"Standalone executable is located at: {exe_path}")

# Authenticode code signing hook (Gate 2)
try:
    from tools.sign_windows_binary import sign_binary
    print("Executing Authenticode code-signing pipeline for standalone binary...")
    sign_binary(exe_path, allow_self_signed=True)
except Exception as e:
    print(f"Code signing note: {e}")

zip_dest = ROOT / "dist" / "GeoDrillPro-Windows-x64"
print(f"Packaging standalone bundle into {zip_dest}.zip...")
shutil.make_archive(str(zip_dest), "zip", root_dir=ROOT / "dist", base_dir="GeoDrillPro")
print(f"Standalone zip package created at: {zip_dest}.zip")

