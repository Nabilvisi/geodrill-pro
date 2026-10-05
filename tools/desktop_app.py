"""Standalone desktop entrypoint for GeoDrill Pro executable (PyInstaller).

Starts the local API service in a background daemon thread, binds a loopback port,
and opens the user's default browser or an embedded desktop web view.
"""
import os
import sys
import threading
import time
import webbrowser
from pathlib import Path

# When running in a PyInstaller bundle, sys._MEIPASS holds the extracted temporary path
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    BUNDLE_DIR = Path(sys._MEIPASS)
else:
    BUNDLE_DIR = Path(__file__).resolve().parents[1]

# Set data storage directory in user profile for permanent storage in .exe mode
USER_DATA_DIR = Path(os.environ.get("APPDATA", str(Path.home()))) / "GeoDrillPro" / "data"
USER_DATA_DIR.mkdir(parents=True, exist_ok=True)
os.environ["GEODRILL_DATA_DIR"] = str(USER_DATA_DIR)

# Add bundle root to sys.path
if str(BUNDLE_DIR) not in sys.path:
    sys.path.insert(0, str(BUNDLE_DIR))

import uvicorn
from services.api.main import create_app
import urllib.request
import json

PORT = 8765
HOST = "127.0.0.1"
URL = f"http://{HOST}:{PORT}"


def run_server():
    app = create_app(data_dir=USER_DATA_DIR)
    uvicorn.run(app, host=HOST, port=PORT, log_level="warning")


def wait_for_server():
    for _ in range(50):
        try:
            with urllib.request.urlopen(f"{URL}/api/health", timeout=0.5) as res:
                if res.status == 200:
                    return True
        except Exception:
            pass
        time.sleep(0.1)
    return False


def main():
    # Start API server in background thread
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    # Wait until healthy then open browser
    if wait_for_server():
        webbrowser.open(URL)
    else:
        print("Failed to start GeoDrill Pro server within timeout.")

    # Keep main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping GeoDrill Pro...")


if __name__ == "__main__":
    main()
