"""Local whole-workstation snapshots and verified restore into a new directory.

Stop GeoDrill before use. Snapshots include credentials and the signing private
key; protect them as sensitive local data. SHA-256 establishes file identity,
not external publisher trust. Project-scoped .gdpz exchange remains in the API.
"""
import argparse
from contextlib import ExitStack, closing
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import sqlite3
import sys
import tempfile
import zipfile
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from services.api.migrations import latest_version

FORMAT = "geodrill-workstation-backup"
DIRECTORIES = {"raw", "parquet", "reports", "keys"}
MAX_FILES = 20_000
MAX_BYTES = 2 * 1024 ** 3


def file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _database(path: Path) -> sqlite3.Connection:
    return sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True, timeout=1)


def _check_database(path: Path) -> int:
    with closing(_database(path)) as db:
        integrity = db.execute("PRAGMA integrity_check").fetchall()
        if integrity != [("ok",)] or db.execute("PRAGMA foreign_key_check").fetchone():
            raise ValueError("Backup database integrity or foreign-key check failed")
        version = db.execute("PRAGMA user_version").fetchone()[0]
        if not 2 <= version <= latest_version():
            raise ValueError("Backup database schema is unsupported by this application")
        tables = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if not {"projects", "datasets", "reports", "audit"}.issubset(tables):
            raise ValueError("Backup database is not a GeoDrill workstation")
        return version


def _safe_name(name: str) -> bool:
    p = PurePosixPath(name)
    if not name or "\\" in name or p.is_absolute() or p.as_posix() != name:
        return False
    if any(part in (".", "..") or any(c in '<>:"|?*' or ord(c) < 32 for c in part) or part.endswith((" ", ".")) for part in p.parts):
        return False
    reserved = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}
    if any(part.split(".")[0].upper() in reserved for part in p.parts):
        return False
    return name == "geodrill.sqlite3" or (len(p.parts) > 1 and p.parts[0] in DIRECTORIES)


def _check_evidence(root: Path, database: Path) -> None:
    """Check preserved application hashes, not only newly generated ZIP hashes."""
    with closing(_database(database)) as db:
        for dataset_id, source_sha, payload in db.execute("SELECT id,source_hash,payload FROM datasets"):
            raw_name, parquet_name = f"raw/{source_sha}", f"parquet/{dataset_id}.parquet"
            if not _safe_name(raw_name) or not _safe_name(parquet_name):
                raise ValueError("Dataset contains an insecure file reference")
            raw, parquet = root / raw_name, root / parquet_name
            metadata = json.loads(payload)
            if not raw.is_file() or file_hash(raw) != source_sha:
                raise ValueError("Original source evidence hash mismatch or missing file")
            if not parquet.is_file() or file_hash(parquet) != metadata.get("parquet_sha256"):
                raise ValueError("Normalized evidence hash mismatch or missing file")
        for query in ("SELECT payload,sha256 FROM reports", "SELECT payload,sha256 FROM engineering_revisions"):
            for payload, expected in db.execute(query):
                if hashlib.sha256(payload.encode()).hexdigest() != expected:
                    raise ValueError("Preserved report/revision evidence hash mismatch")
        previous = "0" * 64
        for payload, predecessor, expected in db.execute("SELECT payload,previous_hash,hash FROM audit ORDER BY sequence"):
            if predecessor != previous or hashlib.sha256((previous + payload).encode()).hexdigest() != expected:
                raise ValueError("Preserved audit chain hash mismatch")
            previous = expected


def _sources(root: Path) -> dict[str, Path]:
    entries = {}
    for directory in sorted(DIRECTORIES):
        folder = root / directory
        if folder.is_symlink():
            raise ValueError("Backup source must not contain symbolic links")
        if not folder.exists():
            continue
        for path in folder.rglob("*"):
            if path.is_symlink():
                raise ValueError("Backup source must not contain symbolic links")
            if not path.resolve().is_relative_to(root.resolve()):
                raise ValueError("Backup source file escaped the data directory")
            if path.is_file():
                name = path.relative_to(root).as_posix()
                if not _safe_name(name):
                    raise ValueError("Backup source contains an unsupported path")
                entries[name] = path
    return entries


def _publish_file(staged: Path, destination: Path) -> None:
    # An exclusive hard-link publication prevents replacing an existing backup.
    os.link(staged, destination)


def backup_workstation(source: Path, archive: Path) -> dict:
    source, archive = source.resolve(), archive.resolve()
    if archive.is_relative_to(source):
        raise ValueError("Store the backup outside the data directory")
    if archive.exists():
        raise ValueError("Backup destination already exists")
    db_path = source / "geodrill.sqlite3"
    if not db_path.is_file() or db_path.is_symlink():
        raise ValueError("Source must contain an existing regular GeoDrill database")
    archive.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="geodrill-backup-", dir=archive.parent) as temporary:
        stage = Path(temporary)
        snapshot = stage / "geodrill.sqlite3"
        with ExitStack() as stack:
            guard = stack.enter_context(closing(sqlite3.connect(db_path.as_uri() + "?mode=rw", uri=True, timeout=1)))
            # Refuse concurrent database writes while the file set is copied.
            guard.execute("BEGIN IMMEDIATE")
            reader = stack.enter_context(closing(_database(db_path)))
            target = stack.enter_context(closing(sqlite3.connect(snapshot)))
            reader.backup(target)
            target.close()
            schema = _check_database(snapshot)
            _check_evidence(source, snapshot)
            paths = _sources(source)
            if len(paths) + 1 > MAX_FILES or sum(p.stat().st_size for p in paths.values()) + snapshot.stat().st_size > MAX_BYTES:
                raise ValueError("Backup exceeds the declared file or byte limit")
            paths["geodrill.sqlite3"] = snapshot
            records = {name: {"sha256": file_hash(path), "size_bytes": path.stat().st_size} for name, path in paths.items()}
            manifest = {"format": FORMAT, "format_version": 1, "schema_version": schema,
                        "created_at_utc": datetime.now(timezone.utc).isoformat(),
                        "contains_credentials_and_private_key": True, "files": records}
            staged_archive = stage / "backup.zip"
            with zipfile.ZipFile(staged_archive, "w", compression=zipfile.ZIP_DEFLATED) as zf:
                for name, path in sorted(paths.items()):
                    zf.write(path, name)
                zf.writestr("manifest.json", json.dumps(manifest, sort_keys=True, separators=(",", ":")))
            # Detect mutable key/file changes even when no database write occurred.
            if set(_sources(source)) != set(paths) - {"geodrill.sqlite3"}:
                raise ValueError("Source file set changed during backup; stop the app and retry")
            if any(file_hash(path) != records[name]["sha256"] for name, path in paths.items()):
                raise ValueError("Source file changed during backup; stop the app and retry")
            with zipfile.ZipFile(staged_archive) as zf:
                for name, record in records.items():
                    h = hashlib.sha256()
                    with zf.open(name) as f:
                        for block in iter(lambda: f.read(1024 * 1024), b""):
                            h.update(block)
                    if h.hexdigest() != record["sha256"]:
                        raise ValueError("Archived file changed during backup; stop the app and retry")
            _publish_file(staged_archive, archive)
            guard.rollback()
    return {"archive": str(archive), "sha256": file_hash(archive), "files": len(records),
            "schema_version": schema, "contains_credentials_and_private_key": True}


def restore_workstation(archive: Path, destination: Path, expected_sha256: str) -> dict:
    archive, destination = archive.resolve(), destination.resolve()
    if len(expected_sha256) != 64 or any(c not in "0123456789abcdef" for c in expected_sha256.lower()):
        raise ValueError("An independently retained SHA-256 value is required")
    if destination.exists():
        raise ValueError("Restore requires a new destination; existing data is never overwritten")
    if file_hash(archive) != expected_sha256.lower():
        raise ValueError("Backup archive SHA-256 mismatch")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="geodrill-restore-", dir=destination.parent) as temporary:
        stage = Path(temporary) / "data"
        stage.mkdir()
        with zipfile.ZipFile(archive) as zf:
            infos = zf.infolist()
            names = [i.filename for i in infos]
            if len(names) != len(set(names)) or len(infos) > MAX_FILES + 1:
                raise ValueError("Backup contains duplicate or excessive entries")
            if sum(i.file_size for i in infos) > MAX_BYTES or any(i.flag_bits & 1 for i in infos):
                raise ValueError("Backup exceeds the byte limit or has unsupported encryption")
            if "manifest.json" not in names or zf.getinfo("manifest.json").file_size > 4 * 1024 * 1024:
                raise ValueError("Backup manifest is missing or too large")
            manifest = json.loads(zf.read("manifest.json"))
            if manifest.get("format") != FORMAT or manifest.get("format_version") != 1:
                raise ValueError("Unsupported backup format")
            records = manifest.get("files")
            if not isinstance(records, dict) or "geodrill.sqlite3" not in records or set(names) != set(records) | {"manifest.json"}:
                raise ValueError("Backup manifest file set does not match the archive")
            for name, record in records.items():
                info = zf.getinfo(name)
                if not _safe_name(name) or info.is_dir() or ((info.external_attr >> 16) & 0o170000) == 0o120000:
                    raise ValueError("Backup contains an insecure entry path or symbolic link")
                if not isinstance(record, dict) or record.get("size_bytes") != info.file_size:
                    raise ValueError("Backup entry size differs from its manifest")
                output = stage.joinpath(*PurePosixPath(name).parts)
                output.parent.mkdir(parents=True, exist_ok=True)
                with zf.open(info) as incoming, output.open("xb") as outgoing:
                    shutil.copyfileobj(incoming, outgoing, length=1024 * 1024)
                if file_hash(output) != record.get("sha256"):
                    raise ValueError("Backup entry SHA-256 mismatch")
            schema = _check_database(stage / "geodrill.sqlite3")
            if schema != manifest.get("schema_version"):
                raise ValueError("Backup schema differs from its manifest")
            _check_evidence(stage, stage / "geodrill.sqlite3")
        # Exclusive destination creation; no recursive replacement of live data.
        destination.mkdir()
        moved = []
        try:
            for path in stage.iterdir():
                path.rename(destination / path.name)
                moved.append(path.name)
        except BaseException:
            # Return only files moved by this attempt to our checked staging dir.
            for name in moved:
                (destination / name).rename(stage / name)
            destination.rmdir()
            raise
    return {"restored": True, "destination": str(destination), "sha256": expected_sha256.lower(),
            "files": len(records), "schema_version": schema}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    backup = commands.add_parser("backup")
    backup.add_argument("--source", type=Path, required=True)
    backup.add_argument("--archive", type=Path, required=True)
    restore = commands.add_parser("restore")
    restore.add_argument("--archive", type=Path, required=True)
    restore.add_argument("--destination", type=Path, required=True)
    restore.add_argument("--expected-sha256", required=True)
    args = parser.parse_args()
    try:
        result = (backup_workstation(args.source, args.archive) if args.command == "backup" else
                  restore_workstation(args.archive, args.destination, args.expected_sha256))
    except (ValueError, OSError, sqlite3.Error, zipfile.BadZipFile, KeyError) as error:
        parser.exit(1, f"Backup/restore refused: {error}\n")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
