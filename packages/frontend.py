"""Resolve a completed frontend release without touching an active build's files."""
import hashlib,json,re
from pathlib import Path

def frontend_dist(root: Path):
    pointer=root/"frontend-build.json"
    if not pointer.exists():return root/"dist"
    value=json.loads(pointer.read_text(encoding="utf-8"))
    directory=value.get("directory")
    if not isinstance(directory,str) or not re.fullmatch(r"dist/release-[a-f0-9]{32}",directory):
        raise ValueError("Invalid frontend release directory.")
    resolved=(root/directory).resolve()
    if resolved.parent!=(root/"dist").resolve():
        raise ValueError("Frontend release must stay inside this installation.")
    if not (resolved/"index.html").is_file() or not (resolved/"assets").is_dir():
        raise ValueError("Selected frontend release is incomplete.")
    return resolved


def frontend_source_hash(root: Path) -> str:
    """Detect a changed workstation source even when a caption/version is unchanged."""
    names = ["package.json", "index.html", "vite.config.ts"]
    names += [str(p.relative_to(root)).replace("\\", "/") for p in (root / "apps/desktop/src").rglob("*") if p.is_file()]
    digest = hashlib.sha256()
    for name in sorted(names):
        path = root / name
        if path.is_file():
            data = path.read_bytes()
            if path.suffix.lower() in {".tsx", ".ts", ".css", ".json", ".html"}:
                data = data.replace(b"\r\n", b"\n")
            digest.update(name.encode() + b"\0" + hashlib.sha256(data).digest())
    return digest.hexdigest()


def verify_streamlit_component(root: Path) -> dict:
    from packages.version import APP_VERSION
    component = root / "apps/streamlit/component"
    manifest = json.loads((component / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("version") != APP_VERSION or manifest.get("frontend_source_sha256") != frontend_source_hash(root):
        raise ValueError("Streamlit workstation assets are stale. Run tools/build.py and tools/build_streamlit.py before deployment.")
    if not manifest.get("assets"):
        raise ValueError("Streamlit workstation assets are missing.")
    for asset in manifest["assets"]:
        path = (component / asset["path"]).resolve()
        if not path.is_relative_to(component.resolve()) or not path.is_file():
            raise ValueError("Invalid Streamlit workstation asset path.")
        if hashlib.sha256(path.read_bytes()).hexdigest() != asset["sha256"]:
            raise ValueError("Streamlit workstation asset integrity failed.")
    return manifest
