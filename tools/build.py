"""Build an immutable output, then select it only after successful compilation."""
from pathlib import Path
import json,shutil,subprocess,sys
from uuid import uuid4
ROOT=Path(__file__).resolve().parents[1]
node=shutil.which("node")
if not node:raise SystemExit("Node.js is required to rebuild. Existing installed app assets can still run.")
relative="dist/release-"+uuid4().hex
for args in (["node_modules/typescript/bin/tsc","-b"],["node_modules/vite/bin/vite.js","build","--outDir",relative]):
    if not (ROOT/args[0]).is_file():
        raise SystemExit("Frontend dependencies are missing. Install the locked dependencies with pnpm first.")
    code=subprocess.call([node,*args],cwd=ROOT)
    if code:sys.exit(code)
output=ROOT/relative
if not (output/"index.html").is_file() or not list((output/"assets").glob("*.js")):
    raise SystemExit("Incomplete frontend release; previous release selection retained.")
# The active service retains its chosen directory until restart; no served file is replaced.
pending=ROOT/("frontend-build-"+uuid4().hex+".tmp")
pending.write_text(json.dumps({"directory":relative},indent=2),encoding="utf-8")
pending.replace(ROOT/"frontend-build.json")
print("Completed frontend release: "+relative)
