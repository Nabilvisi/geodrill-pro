"""Resolve a completed frontend release without touching an active build's files."""
import json,re
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
