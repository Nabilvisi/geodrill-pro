"""Identify the actual source bytes used by a dirty or clean Windows build."""
import hashlib
import json
from pathlib import Path
import subprocess

PREFIXES = ("apps/", "packages/", "services/", "tools/", "tests/", ".github/", "docs/evidence/sources/")
ROOT_FILES = {
    ".gitignore", "requirements.txt", "requirements-lock.txt", "package.json",
    "pnpm-lock.yaml", "pnpm-workspace.yaml", "pytest.ini", "tsconfig.json",
    "frontend-build.json",
}


def snapshot_files(root: Path, paths: list[str]) -> dict:
    root = root.resolve()
    files = []
    for name in sorted(set(paths)):
        normalized = name.replace("\\", "/")
        if normalized not in ROOT_FILES and not normalized.startswith(PREFIXES):
            continue
        path = (root / normalized).resolve()
        if not path.is_relative_to(root):
            raise ValueError("Source snapshot path escaped the workspace")
        if not path.is_file():
            raise ValueError(f"Source snapshot file missing: {normalized}")
        data = path.read_bytes()
        files.append({"path": normalized, "size_bytes": len(data),
                      "sha256": hashlib.sha256(data).hexdigest()})
    if not files:
        raise ValueError("Source snapshot has no eligible files")
    encoded = json.dumps(files, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {"algorithm": "sha256", "digest": hashlib.sha256(encoded).hexdigest(),
            "files": files,
            "scope": "Git-listed application, package, service, tool, test, workflow and original-source files; root build/dependency files. Generated verification reports excluded."}


def create_source_snapshot(root: Path) -> dict:
    listing = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=root, check=True, capture_output=True, text=True,
    ).stdout
    paths = [name for name in listing.split("\0") if name]
    # The selected frontend manifest is generated and intentionally Git-ignored.
    if (root / "frontend-build.json").is_file():
        paths.append("frontend-build.json")
    return snapshot_files(root, paths)
