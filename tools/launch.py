"""Start/stop the workstation without a console window for the server."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import urllib.request
import webbrowser

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from packages.frontend import frontend_dist
URL = 'http://127.0.0.1:8765'
INSTANCE = hashlib.sha256(str(ROOT).encode()).hexdigest()[:16]


def health():
    try:
        with urllib.request.urlopen(URL + '/api/health', timeout=1) as response:
            return json.load(response)
    except Exception:
        return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--no-browser', action='store_true')
    parser.add_argument('--stop', action='store_true')
    args = parser.parse_args()
    state = health()
    if state and state.get('instance_id') != INSTANCE:
        raise SystemExit('Port 8765 is occupied by a different app or an earlier development service. Close that service before launching this copy.')
    if args.stop:
        if state:
            # Only a currently responding server identifying this installation is stopped.
            os.kill(int(state['pid']), signal.SIGTERM)
            print('GeoDrill Pro stopped. All saved project data is retained.')
        else:
            print('GeoDrill Pro is already stopped.')
        return
    if not (frontend_dist(ROOT) / 'index.html').exists():
        raise SystemExit('Frontend build is missing. See README.md for setup instructions.')
    if not state:
        runtime = Path(os.environ.get('GEODRILL_DATA_DIR', ROOT / 'data'))
        runtime.mkdir(parents=True, exist_ok=True)
        with (runtime / 'server.log').open('ab') as log:
            subprocess.Popen([sys.executable, str(ROOT / 'tools' / 'run_server.py')], cwd=ROOT,
                             stdout=log, stderr=log, stdin=subprocess.DEVNULL,
                             creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        for _ in range(40):
            state = health()
            if state and state.get('instance_id') == INSTANCE:
                break
            time.sleep(.25)
        else:
            raise SystemExit('The local service did not start. See data/server.log for details.')
    print('GeoDrill Pro is running at ' + URL)
    if not args.no_browser:
        webbrowser.open(URL)


if __name__ == '__main__':
    main()
