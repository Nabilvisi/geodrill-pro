import hashlib
import json
import os
import sqlite3
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
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
        for name in ("raw", "parquet", "reports"):
            (root / name).mkdir(exist_ok=True)
        self.db = root / "geodrill.sqlite3"
        with self.connect() as db:
            migrate(db)

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


class RevisionConflict(ValueError):
    pass
