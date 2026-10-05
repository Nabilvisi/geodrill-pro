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

pyinstaller_cmd = [
    str(ROOT / ".venv" / "Scripts" / "pyinstaller.exe"),
    "--noconfirm",
    "--onedir",  # onedir is faster to launch and avoids extracting hundreds of MBs on every click
    "--windowed", # Windows GUI app without lingering cmd console
    "--name", "GeoDrillPro",
    "--add-data", f"{dist_dir};{frontend_rel}",
    "--add-data", f"{ROOT / 'frontend-build.json'};.",
    "--add-data", f"{ROOT / 'public'};public",
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
print(f"Standalone executable is located at: {ROOT / 'dist' / 'GeoDrillPro' / 'GeoDrillPro.exe'}")
