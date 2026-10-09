"""Start/stop the workstation without a console window for the server."""
import argparse
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import webbrowser

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from packages.frontend import frontend_dist
from packages.loopback import checked_port, local_health, loopback_url, require_owned_service


def health(port=8765):
    return local_health(port)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--no-browser', action='store_true')
    parser.add_argument('--stop', action='store_true')
    parser.add_argument('--port', type=checked_port, default=8765, help='Explicit local loopback port (default 8765)')
    args = parser.parse_args()
    url = loopback_url(args.port)
    runtime = Path(os.environ.get('GEODRILL_DATA_DIR', ROOT / 'data'))
    state = health(args.port)
    if state is not None:
        try:
            require_owned_service(state, ROOT, runtime, args.port)
        except RuntimeError as error:
            raise SystemExit(str(error)) from error
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
        runtime.mkdir(parents=True, exist_ok=True)
        with (runtime / 'server.log').open('ab') as log:
            subprocess.Popen([sys.executable, str(ROOT / 'tools' / 'run_server.py'), '--port', str(args.port)], cwd=ROOT,
                             stdout=log, stderr=log, stdin=subprocess.DEVNULL,
                             creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        for _ in range(40):
            state = health(args.port)
            if state is not None and not state.get('unidentified_service'):
                require_owned_service(state, ROOT, runtime, args.port)
                break
            time.sleep(.25)
        else:
            raise SystemExit('The local service did not start. See data/server.log for details.')
    print('GeoDrill Pro is running at ' + url)
    if not args.no_browser:
        webbrowser.open(url)


if __name__ == '__main__':
    main()
