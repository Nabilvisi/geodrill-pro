"""Package the selected verified frontend as a Streamlit component."""
from pathlib import Path
import hashlib,json,shutil,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from packages.frontend import frontend_dist, frontend_source_hash
from packages.version import APP_VERSION
release=frontend_dist(ROOT);target=ROOT/"apps"/"streamlit"/"component"
target.mkdir(parents=True,exist_ok=True)
assets=target/"assets";assets.mkdir(exist_ok=True)
manifest=[]
source_names={f.name for f in (release/"assets").iterdir() if f.is_file()}
for stale in assets.iterdir():
 if stale.is_file() and stale.name not in source_names:
  if stale.resolve().parent != assets.resolve():raise RuntimeError("Asset cleanup escaped the component directory.")
  stale.unlink()
for f in (release/"assets").iterdir():
 if f.is_file():
  shutil.copy2(f,assets/f.name);manifest.append({"path":"assets/"+f.name,"sha256":hashlib.sha256(f.read_bytes()).hexdigest()})
for f in release.iterdir():
 if f.is_file() and f.name!="index.html":shutil.copy2(f,target/f.name)
html=(release/"index.html").read_text(encoding="utf-8").replace('"/assets/','"./assets/').replace('"/favicon.svg','"./favicon.svg')
html=html.replace("<head>","<head>\n<script src=\"./bridge.js\"></script>")
(target/"index.html").write_text("\n".join(line.rstrip() for line in html.splitlines())+"\n",encoding="utf-8",newline="\n")
shutil.copy2(ROOT/"apps"/"streamlit"/"bridge.js",target/"bridge.js")
(target/"manifest.json").write_text(json.dumps({"version":APP_VERSION,"frontend_source_sha256":frontend_source_hash(ROOT),"source_release":str(release.relative_to(ROOT)).replace("\\","/"),"assets":manifest},indent=2)+"\n",encoding="utf-8",newline="\n")
print("Packaged the complete verified workstation for Streamlit.")
