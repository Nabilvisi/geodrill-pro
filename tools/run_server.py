import sys
from pathlib import Path
import uvicorn
import argparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from packages.loopback import checked_port

if __name__ == '__main__':
    # Single worker is required: in-process session and report mutation lock.
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=checked_port, default=8765)
    args = parser.parse_args()
    from services.api.main import create_app
    uvicorn.run(create_app(loopback_port=args.port), host='127.0.0.1', port=args.port, workers=1, timeout_keep_alive=5)
