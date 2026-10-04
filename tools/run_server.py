import sys
from pathlib import Path
import uvicorn

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

if __name__ == '__main__':
    # Single worker is required: in-process session and report mutation lock.
    uvicorn.run('services.api.main:app', host='127.0.0.1', port=8765, workers=1, timeout_keep_alive=5)
