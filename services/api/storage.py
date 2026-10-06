import hashlib
import io
import json
import os
import sqlite3
import zipfile
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.exceptions import InvalidSignature
import duckdb
import polars as pl
from .migrations import migrate

# Acting user for audit entries written during the current request (set by team-mode middleware).
current_actor: ContextVar[str] = ContextVar("current_actor", default="local-workstation-user")


def now():
    return datetime.now(timezone.utc).isoformat()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(data: bytes):
    return hashlib.sha256(data).hexdigest()


class Store:
    def __init__(self, root: Path):
        self.root = root
        root.mkdir(parents=True, exist_ok=True)
        for name in ("raw", "parquet", "reports", "keys"):
            (root / name).mkdir(exist_ok=True)
        key_path = root / "keys" / "server_ed25519.key"
        if key_path.exists():
            self._private_key = ed25519.Ed25519PrivateKey.from_private_bytes(key_path.read_bytes())
        else:
            self._private_key = ed25519.Ed25519PrivateKey.generate()
            key_path.write_bytes(self._private_key.private_bytes_raw())
        self._public_key = self._private_key.public_key()
        self.attestation_fingerprint = digest(self._public_key.public_bytes_raw())
        self._trusted_keys: dict[str, ed25519.Ed25519PublicKey] = {
            self.attestation_fingerprint: self._public_key
        }
        trusted_dir = root / "keys" / "trusted"
        trusted_dir.mkdir(exist_ok=True)
        for pub_file in trusted_dir.glob("*.pub"):
            try:
                raw_pub = bytes.fromhex(pub_file.read_text().strip())
                pub_key = ed25519.Ed25519PublicKey.from_public_bytes(raw_pub)
                fp = digest(raw_pub)
                self._trusted_keys[fp] = pub_key
            except Exception:
                pass
        self.db = root / "geodrill.sqlite3"
        with self.connect() as db:
            migrate(db)

    def add_trusted_key(self, public_bytes: bytes):
        pub_key = ed25519.Ed25519PublicKey.from_public_bytes(public_bytes)
        fp = digest(public_bytes)
        self._trusted_keys[fp] = pub_key
        trusted_dir = self.root / "keys" / "trusted"
        trusted_dir.mkdir(exist_ok=True)
        (trusted_dir / f"{fp}.pub").write_text(public_bytes.hex())

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.db, timeout=15)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def audit(self, db, action, project_id, details, actor=None):
        previous = db.execute("SELECT hash FROM audit ORDER BY sequence DESC LIMIT 1").fetchone()
        previous = previous[0] if previous else "0" * 64
        payload = canonical({"at": now(), "actor": actor or current_actor.get(), "action": action, "project_id": project_id, "details": details})
        hashed = digest((previous + payload).encode())
        db.execute("INSERT INTO audit(payload,previous_hash,hash) VALUES(?,?,?)", (payload, previous, hashed))

    def project(self, project_id):
        with self.connect() as db:
            row = db.execute("SELECT * FROM projects WHERE id=?", (project_id,)).fetchone()
        if not row:
            raise KeyError("Project not found")
        return {"id": row["id"], "created_at": row["created_at"], **json.loads(row["payload"])}

    def projects(self):
        with self.connect() as db:
            return [{"id": r["id"], "created_at": r["created_at"], **json.loads(r["payload"])} for r in db.execute("SELECT * FROM projects ORDER BY created_at DESC")]

    def create_project(self, payload):
        project_id = str(uuid4())
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute("INSERT INTO projects VALUES(?,?,?)", (project_id, canonical(payload), now()))
            self.audit(db, "project.created", project_id, payload)
        return self.project(project_id)

    def import_data(self, project_id, kind, filename, raw, rows, metadata, events):
        self.project(project_id)
        source_hash = digest(raw)
        dataset_id = str(uuid4())
        parquet = self.root / "parquet" / f"{dataset_id}.parquet"
        # Generated names only; uploaded filenames are labels, never paths.
        source = self.root / "raw" / source_hash
        if not source.exists():
            temp = self.root / "raw" / f"{uuid4()}.tmp"
            temp.write_bytes(raw)
            os.replace(temp, source)
        pl.DataFrame(rows, infer_schema_length=None).write_parquet(parquet, compression="zstd")
        payload = {"filename": filename, "row_count": len(rows), "metadata": metadata,
                   "parquet_sha256": digest(parquet.read_bytes()), "event_count": len(events)}
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            existing = db.execute("SELECT id FROM datasets WHERE project_id=? AND kind=? AND source_hash=?", (project_id, kind, source_hash)).fetchone()
            if existing:
                parquet.unlink(missing_ok=True)
                return {"id": existing[0], "duplicate": True}
            db.execute("INSERT INTO datasets VALUES(?,?,?,?,?,?)", (dataset_id, project_id, kind, source_hash, canonical(payload), now()))
            for event in events:
                db.execute("INSERT INTO events VALUES(?,?,?,?,NULL)", (str(uuid4()), project_id, dataset_id, canonical(event)))
            self.audit(db, "dataset.imported", project_id, {"dataset_id": dataset_id, "kind": kind, "source_sha256": source_hash, **payload})
        return {"id": dataset_id, "duplicate": False}

    def datasets(self, project_id):
        with self.connect() as db:
            return [{"id": r["id"], "kind": r["kind"], "source_hash": r["source_hash"], "created_at": r["created_at"], **json.loads(r["payload"])} for r in db.execute("SELECT * FROM datasets WHERE project_id=? ORDER BY created_at DESC", (project_id,))]

    def dataset(self, project_id, dataset_id):
        matches = [d for d in self.datasets(project_id) if d["id"] == dataset_id]
        if not matches:
            raise KeyError("Dataset not found in this project")
        record = matches[0]
        path = self.root / "parquet" / f"{record['id']}.parquet"
        if not path.exists() or digest(path.read_bytes()) != record["parquet_sha256"]:
            raise ValueError("Stored dataset integrity check failed; restore from a verified backup.")
        with duckdb.connect() as conn:
            conn.execute("SET threads=2")
            result = conn.execute("SELECT * FROM read_parquet(?)", [str(path)])
            names = [c[0] for c in result.description]
            rows = [dict(zip(names, row)) for row in result.fetchall()]
        return {**record, "rows": rows}

    def events(self, project_id):
        with self.connect() as db:
            return [{"id": r["id"], "dataset_id": r["dataset_id"], **json.loads(r["payload"]), "acknowledgement": json.loads(r["acknowledgement"]) if r["acknowledgement"] else None} for r in db.execute("SELECT * FROM events WHERE project_id=? ORDER BY rowid", (project_id,))]

    def acknowledge(self, project_id, event_id, note):
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM events WHERE id=? AND project_id=?", (event_id, project_id)).fetchone()
            if not row:
                raise KeyError("Event not found")
            if row["acknowledgement"]:
                return json.loads(row["acknowledgement"])
            ack = {"at": now(), "note": note, "actor": "local-workstation-user"}
            db.execute("UPDATE events SET acknowledgement=? WHERE id=?", (canonical(ack), event_id))
            self.audit(db, "event.acknowledged", project_id, {"event_id": event_id, **ack})
        return ack

    def calculation(self, project_id, model, inputs, result):
        self.project(project_id)
        value = {"id": str(uuid4()), "model": model, "inputs_si": inputs, "result": result, "created_at": now()}
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute("INSERT INTO calculations VALUES(?,?,?,?)", (value["id"], project_id, canonical(value), value["created_at"]))
            self.audit(db, "calculation.executed", project_id, value)
        return value

    def audit_history(self):
        with self.connect() as db:
            rows = list(db.execute("SELECT * FROM audit ORDER BY sequence"))
        previous = "0" * 64
        entries = []
        for row in rows:
            if row["previous_hash"] != previous or digest((previous + row["payload"]).encode()) != row["hash"]:
                raise ValueError("Audit integrity check failed.")
            previous = row["hash"]
            entries.append({"sequence": row["sequence"], "hash": row["hash"], **json.loads(row["payload"])})
        return {"integrity": "verified", "head": previous, "entries": entries}

    def create_report(self, project_id):
        # Current single-user snapshot; serialized with mutations by the API lock.
        project = self.project(project_id)
        datasets = [self.dataset(project_id, d["id"]) for d in self.datasets(project_id)]
        for dataset in datasets:
            raw_path = self.root / "raw" / dataset["source_hash"]
            if not raw_path.exists() or digest(raw_path.read_bytes()) != dataset["source_hash"]:
                raise ValueError("Original source integrity check failed.")
        history = self.audit_history()
        report_id = str(uuid4())
        with self.connect() as db:
            calculations = [json.loads(r[0]) for r in db.execute("SELECT payload FROM calculations WHERE project_id=? ORDER BY created_at", (project_id,))]
            payload = {"id": report_id, "schema_version": "1.1", "application_version": "0.8.0", "created_at": now(),
                       "intended_use": "Engineering research and historical review; not field-qualified or an operational clearance.",
                       "project": project, "datasets": datasets, "events": self.events(project_id), "calculations": self.calculations(project_id), "engineering_revisions": self.revisions(project_id),
                       "audit_head": history["head"], "audit_entries": [e for e in history["entries"] if e["project_id"] == project_id],
                       "limitations": ["No live interface or equipment control.", "Surface MSE is a proxy. Point-balance pressure losses are supplied; M6 laminar losses are model-calculated within its declared envelope.", "No independently validated uncertainty or field accuracy.", "Replay is normalized source-time playback, not arrival-time/as-known reconstruction."]}
            encoded = canonical(payload)
            sha = digest(encoded.encode())
            db.execute("BEGIN IMMEDIATE")
            db.execute("INSERT INTO reports VALUES(?,?,?,?,?)", (report_id, project_id, encoded, sha, payload["created_at"]))
            self.audit(db, "report.created", project_id, {"report_id": report_id, "sha256": sha})
        return {"id": report_id, "sha256": sha, "created_at": payload["created_at"]}

    def report(self, project_id, report_id):
        with self.connect() as db:
            row = db.execute("SELECT * FROM reports WHERE id=? AND project_id=?", (report_id, project_id)).fetchone()
        if not row:
            raise KeyError("Report not found")
        if digest(row["payload"].encode()) != row["sha256"]:
            raise ValueError("Report integrity check failed.")
        return {"sha256": row["sha256"], "snapshot": json.loads(row["payload"])}

    def reports(self, project_id):
        self.project(project_id)
        with self.connect() as db:
            return [dict(row) for row in db.execute("SELECT id,sha256,created_at FROM reports WHERE project_id=? ORDER BY created_at DESC", (project_id,))]

    def revisions(self, project_id, module=None):
        self.project(project_id)
        with self.connect() as db:
            records = list(db.execute("SELECT id FROM engineering_revisions WHERE project_id=? AND (? IS NULL OR module=?) ORDER BY rowid DESC", (project_id, module, module)))
        return [self.revision(project_id, r["id"]) for r in records]

    def revision(self, project_id, revision_id):
        with self.connect() as db:
            row = db.execute("SELECT * FROM engineering_revisions WHERE project_id=? AND id=?", (project_id, revision_id)).fetchone()
        if not row:
            raise KeyError("Engineering revision not found in this project")
        if digest(row["payload"].encode()) != row["sha256"]:
            raise ValueError("Engineering revision integrity check failed.")
        return {**json.loads(row["payload"]), "sha256":row["sha256"]}

    def create_revision(self, project_id, module, inputs, result, change_note, base_revision_id):
        self.project(project_id)
        value = {"id":str(uuid4()), "module":module, "created_at":now(), "input":inputs,
                 "result":result, "change_note":change_note, "base_revision_id":base_revision_id}
        encoded = canonical(value)
        sha = digest(encoded.encode())
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            latest = db.execute("SELECT id FROM engineering_revisions WHERE project_id=? AND module=? ORDER BY rowid DESC LIMIT 1", (project_id,module)).fetchone()
            current = latest["id"] if latest else None
            if current != base_revision_id:
                raise RevisionConflict("Geometry changed since it was opened. Reload the latest revision before saving.")
            db.execute("INSERT INTO engineering_revisions VALUES(?,?,?,?,?,?)", (value["id"],project_id,module,encoded,sha,value["created_at"]))
            self.audit(db, "engineering.revised", project_id, {"revision_id":value["id"], "module":module, "sha256":sha, "change_note":change_note})
        return self.revision(project_id,value["id"])

    def calculations(self, project_id, model=None):
        self.project(project_id)
        history=self.audit_history()
        evidence={e["details"].get("id"):e["details"] for e in history["entries"] if e["action"]=="calculation.executed" and e["project_id"]==project_id}
        with self.connect() as db:
            values=[json.loads(r[0]) for r in db.execute("SELECT payload FROM calculations WHERE project_id=? ORDER BY created_at DESC", (project_id,))]
        for value in values:
            if canonical(value) != canonical(evidence.get(value["id"])):
                raise ValueError("Calculation differs from its preserved audit evidence.")
        return [v for v in values if model is None or v["model"]==model]

    def sign_attestation(self, data: bytes) -> str:
        return self._private_key.sign(data).hex()

    def verify_attestation(self, data: bytes, signature_hex: str, fingerprint: str = None) -> bool:
        if fingerprint:
            pub_key = self._trusted_keys.get(fingerprint)
            if not pub_key:
                return False
        else:
            pub_key = self._public_key
        try:
            pub_key.verify(bytes.fromhex(signature_hex), data)
            return True
        except (InvalidSignature, ValueError):
            return False

    def export_bundle(self, project_id: str) -> bytes:
        project = self.project(project_id)
        buf = io.BytesIO()
        file_hashes: dict[str, str] = {}

        with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            def _add(relpath: str, data: bytes):
                file_hashes[relpath] = digest(data)
                zf.writestr(relpath, data)

            _add("project.json", canonical(project).encode("utf-8"))
            _add("keys/server_attestation.pub", self._public_key.public_bytes_raw())

            with self.connect() as db:
                datasets = [dict(r) for r in db.execute("SELECT * FROM datasets WHERE project_id=?", (project_id,)).fetchall()]
                _add("datasets/datasets.json", canonical(datasets).encode("utf-8"))
                for d in datasets:
                    source_path = self.root / "raw" / d["source_hash"]
                    if source_path.exists():
                        _add(f"datasets/raw/{d['source_hash']}", source_path.read_bytes())
                    parquet_path = self.root / "parquet" / f"{d['id']}.parquet"
                    if parquet_path.exists():
                        _add(f"datasets/parquet/{d['id']}.parquet", parquet_path.read_bytes())

                events = [dict(r) for r in db.execute("SELECT * FROM events WHERE project_id=?", (project_id,)).fetchall()]
                _add("events/events.json", canonical(events).encode("utf-8"))

                revisions = [dict(r) for r in db.execute("SELECT * FROM engineering_revisions WHERE project_id=?", (project_id,)).fetchall()]
                _add("revisions/revisions.json", canonical(revisions).encode("utf-8"))

                calculations = [dict(r) for r in db.execute("SELECT * FROM calculations WHERE project_id=?", (project_id,)).fetchall()]
                _add("calculations/calculations.json", canonical(calculations).encode("utf-8"))

                reports = [dict(r) for r in db.execute("SELECT * FROM reports WHERE project_id=?", (project_id,)).fetchall()]
                _add("reports/reports.json", canonical(reports).encode("utf-8"))

                programmes = [dict(r) for r in db.execute("SELECT * FROM programmes WHERE project_id=?", (project_id,)).fetchall()]
                _add("programmes/programmes.json", canonical(programmes).encode("utf-8"))
                
                prog_ids = [p["id"] for p in programmes]
                if prog_ids:
                    q = f"SELECT * FROM programme_versions WHERE programme_id IN ({','.join('?' for _ in prog_ids)})"
                    p_versions = [dict(r) for r in db.execute(q, prog_ids).fetchall()]
                    _add("programmes/versions.json", canonical(p_versions).encode("utf-8"))

                    ver_ids = [v["id"] for v in p_versions]
                    if ver_ids:
                        q_t = f"SELECT * FROM programme_transitions WHERE version_id IN ({','.join('?' for _ in ver_ids)}) ORDER BY sequence"
                        p_transitions = [dict(r) for r in db.execute(q_t, ver_ids).fetchall()]
                        _add("programmes/transitions.json", canonical(p_transitions).encode("utf-8"))
                    else:
                        _add("programmes/transitions.json", b"[]")
                else:
                    _add("programmes/versions.json", b"[]")
                    _add("programmes/transitions.json", b"[]")

                members = [dict(r) for r in db.execute("SELECT * FROM project_members WHERE project_id=?", (project_id,)).fetchall()]
                _add("members/members.json", canonical(members).encode("utf-8"))

                # Export associated users so restored projects maintain foreign key integrity
                user_ids = {m["user_id"] for m in members}
                user_ids.update(p["created_by"] for p in programmes)
                if prog_ids:
                    user_ids.update(v["created_by"] for v in p_versions)
                    user_ids.update(t["actor_id"] for t in p_transitions)
                user_ids.discard(None)
                if user_ids:
                    q_u = f"SELECT * FROM users WHERE id IN ({','.join('?' for _ in user_ids)})"
                    associated_users = [dict(r) for r in db.execute(q_u, list(user_ids)).fetchall()]
                    _add("users/users.json", canonical(associated_users).encode("utf-8"))
                else:
                    _add("users/users.json", b"[]")

                audit_records = [dict(r) for r in db.execute("SELECT * FROM audit ORDER BY sequence").fetchall() if json.loads(r["payload"]).get("project_id") == project_id]
                _add("audit/audit.json", canonical(audit_records).encode("utf-8"))

            manifest = {
                "format": "geodrill-project-bundle",
                "format_version": "1.0",
                "project_id": project_id,
                "project_name": project["name"],
                "exported_at": now(),
                "server_fingerprint": self.attestation_fingerprint,
                "server_public_key": self._public_key.public_bytes_raw().hex(),
                "file_hashes": file_hashes,
            }
            manifest_bytes = canonical(manifest).encode("utf-8")
            manifest_sig = self.sign_attestation(manifest_bytes)
            manifest["signature"] = manifest_sig
            zf.writestr("manifest.json", canonical(manifest).encode("utf-8"))

        return buf.getvalue()

    def restore_bundle(self, bundle_bytes: bytes) -> dict:
        try:
            zf = zipfile.ZipFile(io.BytesIO(bundle_bytes), "r")
        except Exception as e:
            raise ValueError(f"Corrupted bundle archive: {e}")

        for name in zf.namelist():
            if name.startswith("/") or name.startswith("\\") or ".." in name:
                raise ValueError(f"Insecure bundle entry path: {name}")

        if "manifest.json" not in zf.namelist():
            raise ValueError("Invalid bundle: manifest.json is missing")

        manifest_raw = zf.read("manifest.json")
        try:
            manifest = json.loads(manifest_raw.decode("utf-8"))
        except Exception:
            raise ValueError("Corrupted bundle manifest")

        file_hashes = manifest.get("file_hashes", {})
        for relpath, expected_sha in file_hashes.items():
            if relpath not in zf.namelist():
                raise ValueError(f"Corrupted bundle: missing file {relpath}")
            try:
                data = zf.read(relpath)
            except Exception as e:
                raise ValueError(f"Corrupted bundle file '{relpath}': {e}")
            if digest(data) != expected_sha:
                raise ValueError(f"Corrupted bundle: hash mismatch for {relpath}")

        if "keys/server_attestation.pub" in zf.namelist():
            server_pub_raw = zf.read("keys/server_attestation.pub")
            self.add_trusted_key(server_pub_raw)
        elif "server_public_key" in manifest:
            self.add_trusted_key(bytes.fromhex(manifest["server_public_key"]))

        manifest_copy = {k: v for k, v in manifest.items() if k != "signature"}
        sig = manifest.get("signature")
        fp = manifest.get("server_fingerprint")
        if sig and not self.verify_attestation(canonical(manifest_copy).encode("utf-8"), sig, fp):
            raise ValueError("Corrupted bundle: manifest signature verification failed")

        try:
            project = json.loads(zf.read("project.json").decode("utf-8"))
        except Exception as e:
            raise ValueError(f"Corrupted project.json in bundle: {e}")
        project_id = project["id"]

        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            existing = db.execute("SELECT id FROM projects WHERE id=?", (project_id,)).fetchone()
            if existing:
                raise ValueError(f"Project '{project_id}' already exists in this workstation")

            payload_keys = {k: v for k, v in project.items() if k not in ("id", "created_at")}
            db.execute("INSERT INTO projects VALUES(?,?,?)", (project_id, canonical(payload_keys), project["created_at"]))

            if "users/users.json" in zf.namelist():
                users = json.loads(zf.read("users/users.json").decode("utf-8"))
                for u in users:
                    cols = list(u.keys())
                    placeholders = ",".join("?" for _ in cols)
                    col_str = ",".join(cols)
                    db.execute(f"INSERT OR IGNORE INTO users({col_str}) VALUES({placeholders})", [u[c] for c in cols])

            datasets = json.loads(zf.read("datasets/datasets.json").decode("utf-8"))
            for d in datasets:
                raw_entry = f"datasets/raw/{d['source_hash']}"
                if raw_entry in zf.namelist():
                    raw_data = zf.read(raw_entry)
                    (self.root / "raw" / d["source_hash"]).write_bytes(raw_data)
                parquet_entry = f"datasets/parquet/{d['id']}.parquet"
                if parquet_entry in zf.namelist():
                    parquet_data = zf.read(parquet_entry)
                    (self.root / "parquet" / f"{d['id']}.parquet").write_bytes(parquet_data)
                db.execute("INSERT OR REPLACE INTO datasets VALUES(?,?,?,?,?,?)",
                           (d["id"], d["project_id"], d["kind"], d["source_hash"], d["payload"], d["created_at"]))

            events = json.loads(zf.read("events/events.json").decode("utf-8"))
            for ev in events:
                db.execute("INSERT OR REPLACE INTO events VALUES(?,?,?,?,?)",
                           (ev["id"], ev["project_id"], ev["dataset_id"], ev["payload"], ev["acknowledgement"]))

            revisions = json.loads(zf.read("revisions/revisions.json").decode("utf-8"))
            for r in revisions:
                db.execute("INSERT OR REPLACE INTO engineering_revisions VALUES(?,?,?,?,?,?)",
                           (r["id"], r["project_id"], r["module"], r["payload"], r["sha256"], r["created_at"]))

            calculations = json.loads(zf.read("calculations/calculations.json").decode("utf-8"))
            for c in calculations:
                db.execute("INSERT OR REPLACE INTO calculations VALUES(?,?,?,?)",
                           (c["id"], c["project_id"], c["payload"], c["created_at"]))

            reports = json.loads(zf.read("reports/reports.json").decode("utf-8"))
            for rep in reports:
                db.execute("INSERT OR REPLACE INTO reports VALUES(?,?,?,?,?)",
                           (rep["id"], rep["project_id"], rep["payload"], rep["sha256"], rep["created_at"]))

            programmes = json.loads(zf.read("programmes/programmes.json").decode("utf-8"))
            for prog in programmes:
                db.execute("INSERT OR REPLACE INTO programmes VALUES(?,?,?,?,?)",
                           (prog["id"], prog["project_id"], prog["title"], prog["created_by"], prog["created_at"]))

            p_versions = json.loads(zf.read("programmes/versions.json").decode("utf-8"))
            for v in p_versions:
                evidence = v.get("evidence_bindings", "[]")
                db.execute("INSERT OR REPLACE INTO programme_versions(id,programme_id,version_no,content,content_sha256,created_by,created_at,evidence_bindings) VALUES(?,?,?,?,?,?,?,?)",
                           (v["id"], v["programme_id"], v["version_no"], v["content"], v["content_sha256"], v["created_by"], v["created_at"], evidence))

            p_transitions = json.loads(zf.read("programmes/transitions.json").decode("utf-8"))
            for t in p_transitions:
                sig = t.get("signature", "")
                fp = t.get("signer_fingerprint", "")
                db.execute("INSERT OR REPLACE INTO programme_transitions(sequence,version_id,from_state,to_state,actor_id,actor_role,note,at,previous_hash,hash,signature,signer_fingerprint) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                           (t["sequence"], t["version_id"], t["from_state"], t["to_state"], t["actor_id"], t["actor_role"], t["note"], t["at"], t["previous_hash"], t["hash"], sig, fp))

            members = json.loads(zf.read("members/members.json").decode("utf-8"))
            for m in members:
                db.execute("INSERT OR REPLACE INTO project_members VALUES(?,?,?,?)",
                           (m["project_id"], m["user_id"], m["added_by"], m["added_at"]))

            self.audit(db, "bundle.restored", project_id, {"manifest_hash": digest(manifest_raw)})

        return {
            "restored": True,
            "project_id": project_id,
            "project_name": project["name"],
            "restored_at": now(),
            "datasets_count": len(datasets),
            "calculations_count": len(calculations),
            "reports_count": len(reports),
            "programmes_count": len(programmes),
            "status": "verified"
        }


class RevisionConflict(ValueError):
    pass
