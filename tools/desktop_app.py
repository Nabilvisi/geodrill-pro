"""Run the packaged loopback workstation with explicit startup and lifetime checks."""
import argparse
import hashlib
import json
import logging
import os
from pathlib import Path
import sys
import urllib.request
import webbrowser

BUNDLE_DIR = Path(sys._MEIPASS) if getattr(sys, "frozen", False) else Path(__file__).resolve().parents[1]
if str(BUNDLE_DIR) not in sys.path:
    sys.path.insert(0, str(BUNDLE_DIR))
from services.api.main import create_app
import uvicorn

URL = "http://127.0.0.1:8765"


def data_directory() -> Path:
    override = os.environ.get("GEODRILL_DATA_DIR")
    return Path(override) if override else Path(os.environ.get("APPDATA", str(Path.home()))) / "GeoDrillPro" / "data"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--smoke-test", action="store_true", help="Exercise packaged API and diagnostics, then exit")
    args = parser.parse_args()
    runtime = data_directory()
    runtime.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(filename=runtime / "desktop.log", level=logging.INFO)
    try:
        app = create_app(data_dir=runtime)
        if args.smoke_test:
            from fastapi.testclient import TestClient
            from packages.engineering.directional import verify_iscwsa_diagnostics
            with TestClient(app) as client:
                health = client.get("/api/health").json()
                client.get("/api/session")
                projects = client.get("/api/projects")
                assert health["equipment_control"] is False
                assert projects.status_code == 200
                diagnostics = verify_iscwsa_diagnostics()
                if not diagnostics["all_passed"] or diagnostics["cases_evaluated"] < 3:
                    raise RuntimeError("Packaged directional diagnostic comparison failed.")
            (runtime / "smoke-test.json").write_text(
                json.dumps({"health": health, "diagnostics": diagnostics, "projects_status": projects.status_code}, indent=2),
                encoding="utf-8",
            )
            return 0
        instance = hashlib.sha256(str(BUNDLE_DIR.resolve()).encode()).hexdigest()[:16]
        try:
            with urllib.request.urlopen(URL + "/api/health", timeout=1) as response:
                active = json.load(response)
        except OSError:
            active = None
        if active:
            if active.get("instance_id") != instance:
                raise RuntimeError("Port 8765 is occupied by another installation. Close that service first.")
            if not args.no_browser:
                webbrowser.open(URL)
            return 0
        config = uvicorn.Config(app, host="127.0.0.1", port=8765, log_level="warning", log_config=None)
        server = uvicorn.Server(config)
        if not args.no_browser:
            # Open only after this server has completed startup.
            import threading
            import time
            def open_when_ready():
                for _ in range(120):
                    if server.started:
                        webbrowser.open(URL)
                        return
                    if server.should_exit:
                        return
                    time.sleep(0.5)
            threading.Thread(target=open_when_ready, daemon=True).start()
        server.run()
        return 0 if server.started else 1
    except Exception:
        logging.exception("GeoDrill startup failed. Data directory: %s", runtime)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
