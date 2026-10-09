"""Run the packaged loopback workstation with explicit startup and lifetime checks."""
import argparse
import json
import logging
import os
from pathlib import Path
import sys
import webbrowser

BUNDLE_DIR = Path(sys._MEIPASS) if getattr(sys, "frozen", False) else Path(__file__).resolve().parents[1]
if str(BUNDLE_DIR) not in sys.path:
    sys.path.insert(0, str(BUNDLE_DIR))
import uvicorn
from packages.loopback import checked_port, local_health, loopback_url, require_owned_service

def create_app(**kwargs):
    # Import the API only on normal startup, never while preserving/restoring data.
    from services.api.main import create_app as factory
    return factory(**kwargs)


def data_directory() -> Path:
    override = os.environ.get("GEODRILL_DATA_DIR")
    return Path(override) if override else Path(os.environ.get("APPDATA", str(Path.home()))) / "GeoDrillPro" / "data"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--port", type=checked_port, default=8765, help="Explicit local loopback port (default 8765)")
    operation = parser.add_mutually_exclusive_group()
    operation.add_argument("--smoke-test", action="store_true", help="Exercise packaged API and diagnostics, then exit")
    operation.add_argument("--backup", type=Path, metavar="ARCHIVE", help="Back up the stopped workstation, then exit")
    operation.add_argument("--restore", type=Path, metavar="ARCHIVE", help="Restore to a new --destination, then exit")
    parser.add_argument("--destination", type=Path, help="New data directory for restore")
    parser.add_argument("--expected-sha256", help="Retained archive hash required for restore")
    args = parser.parse_args()
    url = loopback_url(args.port)
    runtime = data_directory()
    if args.backup or args.restore:
        from tools.backup_restore import backup_workstation, restore_workstation
        try:
            if args.backup:
                receipt = Path(str(args.backup) + ".receipt.json")
                if receipt.exists():
                    raise ValueError("Backup receipt already exists")
                result = backup_workstation(runtime, args.backup)
                with receipt.open("x", encoding="utf-8") as f:
                    json.dump(result, f, indent=2)
            else:
                if args.destination is None or args.expected_sha256 is None:
                    parser.error("--restore requires --destination and --expected-sha256")
                result = restore_workstation(args.restore, args.destination, args.expected_sha256)
            print(json.dumps(result, indent=2))
            return 0
        except Exception as error:
            print(f"Backup/restore refused: {error}", file=sys.stderr)
            return 1
    runtime.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(filename=runtime / "desktop.log", level=logging.INFO)
    try:
        if not args.smoke_test:
            active = local_health(args.port)
            if active is not None:
                require_owned_service(active, BUNDLE_DIR, runtime, args.port)
                if not args.no_browser:
                    webbrowser.open(url)
                return 0
        app = create_app(data_dir=runtime, loopback_port=args.port)
        if args.smoke_test:
            from fastapi.testclient import TestClient
            from packages.engineering.directional import verify_iscwsa_diagnostics
            with TestClient(app) as client:
                health = client.get("/api/health").json()
                client.get("/api/session")
                projects = client.get("/api/projects")
                if health["equipment_control"] is not False or projects.status_code != 200:
                    raise RuntimeError("Packaged API health/project verification failed.")
                diagnostics = verify_iscwsa_diagnostics()
                if not diagnostics["all_passed"] or diagnostics["cases_evaluated"] < 3:
                    raise RuntimeError("Packaged directional diagnostic comparison failed.")
            (runtime / "smoke-test.json").write_text(
                json.dumps({"health": health, "diagnostics": diagnostics, "projects_status": projects.status_code}, indent=2),
                encoding="utf-8",
            )
            return 0
        config = uvicorn.Config(app, host="127.0.0.1", port=args.port, log_level="warning", log_config=None)
        server = uvicorn.Server(config)
        if not args.no_browser:
            # Open only after this server has completed startup.
            import threading
            import time
            def open_when_ready():
                for _ in range(120):
                    if server.started:
                        webbrowser.open(url)
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
