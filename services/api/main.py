"""Loopback-only engineering workstation. No outbound rig interfaces or control routes."""
import os
import json
import hashlib
import secrets
import threading
from pathlib import Path
from typing import Literal
from fastapi import FastAPI, File, Form, HTTPException, Request, Response, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool
from packages.engineering.models import ProjectCreate, MSEInput, PressureInput, Acknowledgement
from packages.engineering.physics import mse, pressure
from packages.engineering.ingestion import telemetry_csv, survey_csv, las2
from .storage import Store, RevisionConflict, digest, canonical, current_actor
from .auth import user_for_token
from .access import role_denial, project_id_from_path, is_member, visible_projects, add_member
from .team import build_router, bearer
from packages.engineering.geometry import GeometryInput, GeometryRevisionRequest, geometry_result
from packages.engineering.casing import CasingCheckInput, casing_check
from packages.engineering.clustering import ClusteringInput, cluster_logs
from packages.engineering.shaly_sand import ShalySandInput, interpret_logs
from packages.engineering.em_vendor import EMVendorDocument, EMReviewInput, review_vendor
from packages.engineering.hydraulics import HydraulicsInput, hydraulics
from packages.engineering.geometry import Path as SurveyPath
from packages.engineering.models import SurveyRequest
from packages.engineering.stability import StabilityInput, stability
from packages.engineering.transport import TransportInput, transport
from packages.engineering.surge_swab import SurgeInput, surge
from packages.engineering.torque_drag import TorqueDragInput, torque_drag
from packages.engineering.buckling import BucklingInput, buckling
from packages.engineering.dynamics import DynamicsInput, dynamics
from packages.engineering.bit_condition import BitInput, bit_condition
from packages.engineering.wear_fatigue import WearInput, wear_fatigue
from packages.engineering.anomaly import AnomalyInput, anomaly
from packages.engineering.gas_phase import GasInput, gas_phase
from packages.engineering.supervision import SupervisionInput, supervision
from packages.frontend import frontend_dist
from . import demo

import sys
ROOT = Path(sys._MEIPASS).resolve() if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS") else Path(__file__).resolve().parents[2]
MAX_FILE_BYTES = 2 * 1024 * 1024
ALLOWED_HOSTS = {"127.0.0.1:8765", "localhost:8765", "127.0.0.1:5173", "localhost:5173", "testserver"}


def create_app(data_dir: Path | None = None, mode: str | None = None):
    app = FastAPI(title="GeoDrill Pro", version="0.8.0", docs_url=None, redoc_url=None, openapi_url=None)
    store = Store(data_dir or Path(os.environ.get("GEODRILL_DATA_DIR", ROOT / "data")))
    app.state.store = store
    session = secrets.token_urlsafe(32)
    lock = threading.RLock()
    team_mode = (mode or os.environ.get("GEODRILL_MODE", "local")).lower() == "team"
    allowed_hosts = set(ALLOWED_HOSTS)
    if team_mode:
        allowed_hosts |= {h.strip() for h in os.environ.get("GEODRILL_ALLOWED_HOSTS", "").split(",") if h.strip()}
    app.state.team_mode = team_mode

    @app.middleware("http")
    async def boundary(request: Request, call_next):
        host = request.headers.get("host", "")
        if host not in allowed_hosts:
            return JSONResponse({"detail": "Untrusted host"}, status_code=403)
        origin = request.headers.get("origin")
        if origin and origin not in ({f"http://{host}", f"https://{host}"} if team_mode else {f"http://{host}"}):
            return JSONResponse({"detail": "Cross-origin requests are not allowed"}, status_code=403)
        if request.url.path.startswith("/api/") and request.headers.get("sec-fetch-site") == "cross-site":
            return JSONResponse({"detail": "Cross-site requests are not allowed"}, status_code=403)
        if request.method in {"POST", "PUT", "PATCH"} and ("content-length" not in request.headers or "transfer-encoding" in request.headers):
            return JSONResponse({"detail": "A bounded Content-Length is required"}, status_code=411)
        try:
            if int(request.headers.get("content-length", "0")) > MAX_FILE_BYTES + 65536:
                return JSONResponse({"detail": "Request exceeds the 2 MiB import limit"}, status_code=413)
        except ValueError:
            return JSONResponse({"detail": "Invalid content length"}, status_code=400)
        path = request.url.path
        actor_token = None
        if team_mode:
            # Per-user Bearer auth replaces the single-user loopback cookie. Browsers never attach
            # Authorization headers automatically, so cookie-style CSRF does not apply here.
            if path.startswith("/api/") and path not in {"/api/health", "/api/team/login"}:
                user = await run_in_threadpool(user_for_token, store, bearer(request))
                if user is None:
                    return JSONResponse({"detail": "Sign in required"}, status_code=401, headers={"WWW-Authenticate": "Bearer"})
                request.state.user = user
                denial = role_denial(request.method, path, user)
                if denial:
                    return JSONResponse({"detail": denial}, status_code=403)
                scoped = project_id_from_path(path)
                if scoped is not None and not await run_in_threadpool(is_member, store, user, scoped):
                    return JSONResponse({"detail": "Project not found"}, status_code=404)
                actor_token = current_actor.set(f"user:{user['username']}")
        elif path.startswith("/api/") and path not in {"/api/session", "/api/health"}:
            if not secrets.compare_digest(request.cookies.get("gd_session", ""), session):
                return JSONResponse({"detail": "Open the workstation to start a local session."}, status_code=401)
            if request.method not in {"GET", "HEAD"} and request.headers.get("x-geodrill-client") != "workstation":
                return JSONResponse({"detail": "Missing workstation request header"}, status_code=403)
        try:
            response = await call_next(request)
        finally:
            if actor_token is not None:
                current_actor.reset(actor_token)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Cache-Control"] = "no-store"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
        return response

    @app.exception_handler(KeyError)
    async def missing(request, error):
        return JSONResponse({"detail": str(error.args[0])}, status_code=404)

    @app.exception_handler(ValueError)
    async def invalid(request, error):
        return JSONResponse({"detail": str(error)}, status_code=422)

    @app.exception_handler(PermissionError)
    async def forbidden(request, error):
        return JSONResponse({"detail": str(error)}, status_code=403)

    if team_mode:
        app.include_router(build_router(store))

    @app.get("/api/session")
    def bootstrap(response: Response):
        response.set_cookie("gd_session", session, httponly=True, samesite="strict", path="/")
        return {"mode": "engineering-research", "version": "0.8.0", "equipment_authority": "none"}

    @app.get("/api/health")
    def health():
        return {"status": "ok", "version": "0.8.0", "mode": "local-research", "equipment_control": False,
                "instance_id": hashlib.sha256(str(ROOT).encode()).hexdigest()[:16], "pid": os.getpid()}

    @app.get("/api/projects")
    def projects(request: Request):
        if team_mode:
            return visible_projects(store, request.state.user)
        return store.projects()

    @app.post("/api/projects", status_code=201)
    def create_project(value: ProjectCreate, request: Request):
        with lock:
            proj = store.create_project(value.model_dump())
            if team_mode:
                add_member(store, proj["id"], request.state.user["id"], request.state.user)
            return proj

    @app.get("/api/projects/{project_id}")
    def project(project_id: str):
        return store.project(project_id)

    def ingest(project_id, kind, filename, raw):
        project = store.project(project_id)
        try:
            text = raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            raise ValueError("Save the source as UTF-8 text before importing.")
        events = []
        if kind == "telemetry":
            rows, events, mapping = telemetry_csv(text, project["bit_diameter_m"])
            metadata = {"mapping": mapping, "load_source": "surface", "model_version": "0.1.0", "origin": project["origin"], "replay_basis": "source_time", "bit_diameter_m": project["bit_diameter_m"]}
        elif kind == "survey":
            rows = survey_csv(text)
            metadata = {"datum": project["datum"], "north_reference": project["north_reference"], "model": "minimum-curvature", "model_version": "0.1.0", "uncertainty": "not evaluated"}
        else:
            rows, curves, las_meta = las2(text)
            metadata = {"curves": curves, "las_metadata": las_meta, "depth_reference": "measured depth; verify against project datum", "interpretation": "raw curves only; no lithology classification"}
        return store.import_data(project_id, kind, filename, raw, rows, metadata, events)

    @app.post("/api/projects/{project_id}/imports", status_code=201)
    async def import_file(project_id: str, kind: Literal["telemetry", "survey", "las"] = Form(...), file: UploadFile = File(...)):
        raw = await file.read(MAX_FILE_BYTES + 1)
        await file.close()
        if len(raw) > MAX_FILE_BYTES:
            raise HTTPException(413, "File exceeds the 2 MiB release limit.")
        filename = (file.filename or "untitled").replace("\\", "/").split("/")[-1][:160]
        extension = ".las" if kind == "las" else ".csv"
        if not filename.lower().endswith(extension):
            raise ValueError(f"This import type requires a {extension} file.")
        def execute():
            with lock:
                return ingest(project_id, kind, filename, raw)
        return await run_in_threadpool(execute)

    @app.post("/api/demo", status_code=201)
    def load_demo(request: Request):
        with lock:
            existing = next((p for p in store.projects() if p.get("demo_key") == "demo-v1"), None)
            if existing:
                if team_mode:
                    add_member(store, existing["id"], request.state.user["id"], request.state.user, quiet=True)
                return existing
            payload = ProjectCreate(name="North Sea · Research", well_name="GD-01 / Demonstration", datum="Local rig datum (synthetic)", bit_diameter_m=0.2159, origin="synthetic").model_dump()
            payload.update(demo_key="demo-v1", formations=[{"name": "Nordland Group", "top_tvd_m": 0, "uncertainty_m": 25}, {"name": "Hordaland Group", "top_tvd_m": 750, "uncertainty_m": 35}, {"name": "Rogaland Group", "top_tvd_m": 1550, "uncertainty_m": 40}, {"name": "Chalk interval", "top_tvd_m": 2100, "uncertainty_m": 30}])
            project = store.create_project(payload)
            if team_mode:
                add_member(store, project["id"], request.state.user["id"], request.state.user, quiet=True)
            ingest(project["id"], "telemetry", "synthetic-drilling.csv", demo.telemetry())
            ingest(project["id"], "survey", "synthetic-survey.csv", demo.SURVEY)
            ingest(project["id"], "las", "synthetic-logs.las", demo.LAS)
            return project

    @app.get("/api/projects/{project_id}/datasets")
    def datasets(project_id: str):
        store.project(project_id)
        return store.datasets(project_id)

    @app.get("/api/projects/{project_id}/datasets/{dataset_id}")
    def dataset(project_id: str, dataset_id: str):
        return store.dataset(project_id, dataset_id)


    @app.get("/api/projects/{project_id}/engineering-revisions")
    def revisions_list(project_id: str, module: str | None = None):
        return store.revisions(project_id, module)

    def checked_geometry(project_id, revision_id):
        revision=store.revision(project_id, revision_id)
        if revision["module"] != "M1":
            raise ValueError("Expected a well-geometry revision.")
        source=store.dataset(project_id, revision["input"]["survey_dataset_id"])
        if source["source_hash"] != revision["result"]["survey_source_sha256"]:
            raise ValueError("Survey source differs from its preserved geometry revision.")
        raw=store.root / "raw" / source["source_hash"]
        if not raw.exists() or digest(raw.read_bytes()) != source["source_hash"]:
            raise ValueError("Survey original source integrity check failed.")
        return revision

    @app.get("/api/projects/{project_id}/geometry/{revision_id}")
    def geometry_get(project_id: str, revision_id: str):
        return checked_geometry(project_id, revision_id)

    @app.post("/api/projects/{project_id}/geometry", status_code=201)
    def geometry_save(project_id: str, value: GeometryRevisionRequest):
        with lock:
            project=store.project(project_id)
            source=store.dataset(project_id,value.geometry.survey_dataset_id)
            if source["kind"] != "survey":
                raise ValueError("Geometry requires a directional-survey dataset.")
            if value.geometry.datum != project["datum"] or source["metadata"]["datum"] != project["datum"] or source["metadata"]["north_reference"] != project["north_reference"]:
                raise ValueError("Geometry and survey references must match the project datum and north.")
            raw=store.root / "raw" / source["source_hash"]
            if not raw.exists() or digest(raw.read_bytes()) != source["source_hash"]:
                raise ValueError("Survey original source integrity check failed.")
            survey=SurveyRequest(stations=[{k:r[k] for k in ("md_m","inclination_rad","azimuth_rad")} for r in source["rows"]])
            result=geometry_result(value.geometry,survey)
            result.update(survey_source_sha256=source["source_hash"], survey_filename=source["filename"], north_reference=project["north_reference"])
            try:
                return store.create_revision(project_id,"M1",value.geometry.model_dump(),result,value.change_note,value.base_revision_id)
            except RevisionConflict as error:
                raise HTTPException(409,str(error))

    @app.get("/api/projects/{project_id}/calculations")
    def calculations_list(project_id: str, model: str | None = None):
        return store.calculations(project_id,model)

    @app.post("/api/projects/{project_id}/calculations/casing")
    def calculate_casing(project_id: str, value: CasingCheckInput):
        with lock:
            revision=checked_geometry(project_id,value.geometry_revision_id)
            result=casing_check(value,GeometryInput.model_validate(revision["input"]))
            result.update(geometry_revision_id=revision["id"],geometry_sha256=revision["sha256"])
            return store.calculation(project_id,"casing",value.model_dump(),result)

    @app.post("/api/projects/{project_id}/calculations/clustering")
    def calculate_clustering(project_id: str, value: ClusteringInput):
        with lock:
            project=store.project(project_id)
            revision=checked_geometry(project_id,value.geometry_revision_id)
            if value.depth_datum != project["datum"]:
                raise ValueError("Declared log depth datum must match the project; resolve tool offsets and datum alignment before analysis.")
            source=store.dataset(project_id,value.dataset_id)
            if source["kind"] != "las":
                raise ValueError("Clustering requires an imported LAS dataset.")
            raw=store.root / "raw" / source["source_hash"]
            if not raw.exists() or digest(raw.read_bytes()) != source["source_hash"]:
                raise ValueError("Log original source integrity check failed.")
            result=cluster_logs(value,source["rows"],source["metadata"]["curves"],revision["result"]["total_depth_md_m"])
            result.update(dataset_id=source["id"],source_sha256=source["source_hash"],parquet_sha256=source["parquet_sha256"],
                          geometry_revision_id=revision["id"],geometry_sha256=revision["sha256"])
            return store.calculation(project_id,"clustering",value.model_dump(),result)

    @app.post("/api/projects/{project_id}/calculations/shaly-sand")
    def calculate_shaly_sand(project_id: str, value: ShalySandInput):
        with lock:
            project=store.project(project_id)
            revision=checked_geometry(project_id,value.geometry_revision_id)
            if value.depth_datum != project["datum"]:
                raise ValueError("Declared log MD datum must match the project.")
            if value.correction_status=="synthetic" and project["origin"]!="synthetic":
                raise ValueError("Synthetic correction state is restricted to synthetic projects.")
            source=store.dataset(project_id,value.dataset_id)
            if source["kind"]!="las":
                raise ValueError("Shaly-sand analysis requires a LAS source.")
            raw=store.root/"raw"/source["source_hash"]
            if not raw.exists() or digest(raw.read_bytes()) != source["source_hash"]:
                raise ValueError("Log original source integrity check failed.")
            result=interpret_logs(value,source["rows"],source["metadata"]["curves"],revision["result"]["total_depth_md_m"])
            result.update(dataset_id=source["id"],source_sha256=source["source_hash"],parquet_sha256=source["parquet_sha256"],
                          geometry_revision_id=revision["id"],geometry_sha256=revision["sha256"])
            return store.calculation(project_id,"shaly_sand",value.model_dump(),result)

    @app.post("/api/projects/{project_id}/examples/shaly-sand",status_code=201)
    def example_shaly_sand(project_id: str):
        with lock:
            if store.project(project_id)["origin"]!="synthetic":
                raise ValueError("Generated examples are restricted to synthetic projects.")
            return ingest(project_id,"las","synthetic-shaly-sand.las",demo.shaly_sand())

    @app.get("/api/projects/{project_id}/examples/hydraulics/{revision_id}")
    def example_hydraulics(project_id: str, revision_id: str):
        if store.project(project_id)["origin"]!="synthetic":
            raise ValueError("Generated examples are restricted to synthetic projects.")
        return demo.hydraulics_example(checked_geometry(project_id,revision_id))

    @app.post("/api/projects/{project_id}/calculations/hydraulics")
    def calculate_hydraulics(project_id: str, value: HydraulicsInput):
        with lock:
            project=store.project(project_id)
            revision=checked_geometry(project_id,value.geometry_revision_id)
            if value.depth_datum!=project["datum"]:
                raise ValueError("Hydraulic depth datum must match the project.")
            if project["origin"]!="synthetic" and (value.mud.evidence_state=="synthetic" or value.pressure_window.evidence_state=="synthetic"):
                raise ValueError("Synthetic hydraulic evidence is restricted to synthetic projects.")
            geometry=GeometryInput.model_validate(revision["input"])
            source=store.dataset(project_id,geometry.survey_dataset_id)
            path=SurveyPath(SurveyRequest(stations=[{k:r[k] for k in ("md_m","inclination_rad","azimuth_rad")} for r in source["rows"]]))
            result=hydraulics(value,geometry,path)
            result.update(geometry_revision_id=revision["id"],geometry_sha256=revision["sha256"],
                          survey_source_sha256=source["source_hash"],survey_parquet_sha256=source["parquet_sha256"])
            return store.calculation(project_id,"hydraulics",value.model_dump(),result)

    research_models={"stability":StabilityInput,"transport":TransportInput,"surge-swab":SurgeInput,"torque-drag":TorqueDragInput,"buckling":BucklingInput,"dynamics":DynamicsInput,"bit-condition":BitInput,"wear-fatigue":WearInput,"anomaly":AnomalyInput,"gas-phase":GasInput,"supervision":SupervisionInput}

    @app.get("/api/research/schemas")
    def research_schemas():
        return {key:model.model_json_schema() for key,model in research_models.items()}

    @app.get("/api/projects/{project_id}/research/{model}/template/{revision_id}")
    def research_template(project_id: str, model: str, revision_id: str):
        if model not in research_models:
            raise ValueError("Unknown research model.")
        project=store.project(project_id)
        revision=checked_geometry(project_id,revision_id)
        return demo.research_template(model,revision,project["origin"])

    @app.post("/api/projects/{project_id}/research/source-hydraulics/{revision_id}",status_code=201)
    def research_source(project_id: str,revision_id: str):
        with lock:
            if store.project(project_id)["origin"]!="synthetic":
                raise ValueError("Generated hydraulic source is restricted to synthetic projects.")
            revision=checked_geometry(project_id,revision_id)
            payload=demo.hydraulics_example(revision)
            payload["study_name"]="Synthetic Newtonian source for M8/M9"
            payload["mud"].update(rheology="newtonian",consistency_pa_sn=.1,flow_index=1.,yield_stress_pa=0.)
            payload["geometry_state"]="installed_only"
            payload["flow_m3_s"]=.0005
            payload["sensitivity"]={"density_delta_kg_m3":0.,"flow_delta_m3_s":0.,"consistency_relative_delta":0.,"backpressure_delta_pa":0.}
            return calculate_hydraulics(project_id,HydraulicsInput.model_validate(payload))

    def research_context(project_id,value):
        project=store.project(project_id)
        revision=checked_geometry(project_id,value.geometry_revision_id)
        if value.depth_datum!=project["datum"]:
            raise ValueError("Research depth datum must match the project.")
        if value.evidence_state=="synthetic" and project["origin"]!="synthetic":
            raise ValueError("Synthetic research evidence is restricted to synthetic projects.")
        geometry=GeometryInput.model_validate(revision["input"])
        source=store.dataset(project_id,geometry.survey_dataset_id)
        path=SurveyPath(SurveyRequest(stations=[{k:r[k] for k in ("md_m","inclination_rad","azimuth_rad")} for r in source["rows"]]))
        return revision,geometry,source,path

    def research_save(project_id,value,model,kernel):
        with lock:
            revision,geometry,source,path=research_context(project_id,value)
            linked=None
            if hasattr(value,"hydraulics_calculation_id"):
                linked=next((c for c in store.calculations(project_id,"hydraulics") if c["id"]==value.hydraulics_calculation_id),None)
                if linked is None:
                    raise ValueError("Select a hydraulic calculation belonging to this project.")
                if linked["inputs_si"]["geometry_revision_id"]!=revision["id"] or linked["inputs_si"]["depth_datum"]!=value.depth_datum:
                    raise ValueError("Linked hydraulics must use the same immutable geometry and MD datum.")
                result=kernel(value,geometry,path,linked["inputs_si"],linked["result"])
                result["hydraulics_sha256"]=digest(canonical(linked).encode("utf-8"))
            elif model=="buckling":
                linked=next((c for c in store.calculations(project_id,"torque-drag") if c["id"]==value.torque_drag_calculation_id),None)
                if linked is None:
                    raise ValueError("Select a torque/drag calculation belonging to this project.")
                if linked["inputs_si"]["geometry_revision_id"]!=revision["id"] or linked["inputs_si"]["depth_datum"]!=value.depth_datum:
                    raise ValueError("Linked torque/drag must use the same immutable geometry and MD datum.")
                result=kernel(value,geometry,path,linked["inputs_si"],linked["result"])
                result["torque_drag_sha256"]=digest(canonical(linked).encode("utf-8"))
            elif model=="stability":
                result=kernel(value,path)
            else:
                result=kernel(value,geometry,path)
            if getattr(value,"input_dataset_id",None):
                document=store.dataset(project_id,value.input_dataset_id)
                if document["kind"]!="research_input" or document["metadata"].get("research_model")!=model:
                    raise ValueError("Input document must belong to this project and study model.")
                raw_path=store.root/"raw"/document["source_hash"]
                if not raw_path.exists() or digest(raw_path.read_bytes())!=document["source_hash"]:raise ValueError("Original input document integrity check failed.")
                original=research_models[model].model_validate_json(raw_path.read_bytes().decode("utf-8-sig"))
                result.update(input_dataset_id=document["id"],input_document_sha256=document["source_hash"],input_document_parquet_sha256=document["parquet_sha256"],input_document_filename=document["filename"],input_document_matches_current=original.model_dump(exclude={"input_dataset_id"})==value.model_dump(exclude={"input_dataset_id"}))
            result.update(geometry_revision_id=revision["id"],geometry_sha256=revision["sha256"],
                          survey_source_sha256=source["source_hash"],survey_parquet_sha256=source["parquet_sha256"])
            result["input_evidence_state"]=value.evidence_state
            return store.calculation(project_id,model,value.model_dump(),result)

    @app.post("/api/projects/{project_id}/research/{model}/imports",status_code=201)
    async def import_research_inputs(project_id: str,model: str,file: UploadFile = File(...)):
        if model not in {"dynamics","bit-condition","wear-fatigue","anomaly","gas-phase","supervision"}:
            raise ValueError("JSON research imports are available for Modules 12–17.")
        raw=await file.read(MAX_FILE_BYTES+1);await file.close()
        if len(raw)>MAX_FILE_BYTES:raise HTTPException(413,"File exceeds the 2 MiB release limit.")
        filename=(file.filename or "untitled").replace("\\","/").split("/")[-1][:160]
        if not filename.lower().endswith(".json"):raise ValueError("Study input interchange requires a .json file with SI values.")
        def execute():
            with lock:
                value=research_models[model].model_validate_json(raw.decode("utf-8-sig"))
                value.input_dataset_id=None
                research_context(project_id,value)
                imported=store.import_data(project_id,"research_input",filename,raw,[{"document_json":canonical(value.model_dump())}],{"research_model":model,"input_units":"SI","geometry_revision_id":value.geometry_revision_id},[])
                inputs=value.model_dump();inputs["input_dataset_id"]=imported["id"]
                return {**imported,"inputs_si":inputs,"source_sha256":digest(raw)}
        try:return await run_in_threadpool(execute)
        except UnicodeDecodeError as error:raise ValueError("Study input JSON must be UTF-8.") from error

    @app.post("/api/projects/{project_id}/calculations/stability")
    def calculate_stability(project_id: str,value: StabilityInput):
        return research_save(project_id,value,"stability",stability)

    @app.post("/api/projects/{project_id}/calculations/transport")
    def calculate_transport(project_id: str,value: TransportInput):
        return research_save(project_id,value,"transport",transport)

    @app.post("/api/projects/{project_id}/calculations/surge-swab")
    def calculate_surge(project_id: str,value: SurgeInput):
        return research_save(project_id,value,"surge-swab",surge)

    @app.post("/api/projects/{project_id}/calculations/torque-drag")
    def calculate_drag(project_id: str,value: TorqueDragInput):
        return research_save(project_id,value,"torque-drag",torque_drag)

    @app.post("/api/projects/{project_id}/calculations/buckling")
    def calculate_buckling(project_id: str,value: BucklingInput):
        return research_save(project_id,value,"buckling",buckling)

    @app.post("/api/projects/{project_id}/calculations/dynamics")
    def calculate_dynamics(project_id: str,value: DynamicsInput):
        return research_save(project_id,value,"dynamics",dynamics)

    @app.post("/api/projects/{project_id}/calculations/bit-condition")
    def calculate_bit_condition(project_id: str,value: BitInput):
        return research_save(project_id,value,"bit-condition",bit_condition)

    @app.post("/api/projects/{project_id}/calculations/wear-fatigue")
    def calculate_wear_fatigue(project_id: str,value: WearInput):
        return research_save(project_id,value,"wear-fatigue",wear_fatigue)

    @app.post("/api/projects/{project_id}/calculations/anomaly")
    def calculate_anomaly(project_id: str,value: AnomalyInput):
        return research_save(project_id,value,"anomaly",anomaly)

    @app.post("/api/projects/{project_id}/calculations/gas-phase")
    def calculate_gas_phase(project_id: str,value: GasInput):
        return research_save(project_id,value,"gas-phase",gas_phase)

    @app.post("/api/projects/{project_id}/calculations/supervision")
    def calculate_supervision(project_id: str,value: SupervisionInput):
        return research_save(project_id,value,"supervision",supervision)

    def ingest_em_vendor(project_id, filename, raw):
        project=store.project(project_id)
        try:
            document=EMVendorDocument.model_validate_json(raw.decode("utf-8-sig"))
        except (UnicodeDecodeError, ValueError) as error:
            raise ValueError("Invalid EM vendor document: "+str(error))
        if document.origin != project["origin"] or document.well_name != project["well_name"] or document.depth_datum != project["datum"]:
            raise ValueError("EM source origin, well name and MD datum must match the project.")
        metadata=document.model_dump(exclude={"samples"})
        metadata["interpretation"]="imported vendor results; no local EM inversion or approval"
        rows=[{"depth_m":sample.md_m,"rh_ohm_m":sample.rh_ohm_m,"rv_ohm_m":sample.rv_ohm_m,
               "boundary_distance_m":sample.boundary_distance_m,"quality":sample.quality,
               "acquired_at":sample.acquired_at,"supplied_json":json.dumps(sample.model_dump(),allow_nan=False)}
              for sample in document.samples]
        return store.import_data(project_id,"em_vendor",filename,raw,rows,metadata,[])

    @app.post("/api/projects/{project_id}/em-vendor/imports",status_code=201)
    async def import_em_vendor(project_id: str, file: UploadFile = File(...)):
        raw=await file.read(MAX_FILE_BYTES+1)
        await file.close()
        if len(raw)>MAX_FILE_BYTES:
            raise HTTPException(413,"File exceeds the 2 MiB release limit.")
        filename=(file.filename or "untitled").replace("\\","/").split("/")[-1][:160]
        if not filename.lower().endswith(".json"):
            raise ValueError("EM vendor interchange requires a .json file.")
        def execute():
            with lock:
                return ingest_em_vendor(project_id,filename,raw)
        return await run_in_threadpool(execute)

    @app.post("/api/projects/{project_id}/examples/em-vendor",status_code=201)
    def example_em_vendor(project_id: str):
        with lock:
            project=store.project(project_id)
            if project["origin"]!="synthetic":
                raise ValueError("Generated examples are restricted to synthetic projects.")
            return ingest_em_vendor(project_id,"synthetic-em-vendor.json",demo.em_vendor(project["well_name"],project["datum"]))

    @app.get("/api/projects/{project_id}/em-vendor/template")
    def em_vendor_template(project_id: str):
        project=store.project(project_id)
        # A synthetic example document must be edited and honestly labelled before importing historical evidence.
        return Response(demo.em_vendor(project["well_name"],project["datum"]),media_type="application/json",
                        headers={"Content-Disposition":'attachment; filename="synthetic-em-vendor-template.json"'})

    @app.post("/api/projects/{project_id}/calculations/em-vendor")
    def calculate_em_vendor(project_id: str, value: EMReviewInput):
        with lock:
            project=store.project(project_id)
            revision=checked_geometry(project_id,value.geometry_revision_id)
            if value.depth_datum!=project["datum"]:
                raise ValueError("Declared EM MD datum must match the project.")
            source=store.dataset(project_id,value.dataset_id)
            if source["kind"]!="em_vendor":
                raise ValueError("Review requires an EM vendor interchange source.")
            raw_path=store.root/"raw"/source["source_hash"]
            if not raw_path.exists() or digest(raw_path.read_bytes())!=source["source_hash"]:
                raise ValueError("EM original source integrity check failed.")
            document=EMVendorDocument.model_validate_json(raw_path.read_bytes().decode("utf-8-sig"))
            if document.origin!=project["origin"] or document.well_name!=project["well_name"] or document.depth_datum!=project["datum"]:
                raise ValueError("EM source origin, well and datum do not match the project.")
            result=review_vendor(document,value,revision["result"]["total_depth_md_m"])
            result.update(dataset_id=source["id"],source_sha256=source["source_hash"],parquet_sha256=source["parquet_sha256"],
                          geometry_revision_id=revision["id"],geometry_sha256=revision["sha256"])
            return store.calculation(project_id,"em_vendor",value.model_dump(),result)

    @app.get("/api/projects/{project_id}/events")
    def events(project_id: str):
        store.project(project_id)
        return store.events(project_id)

    @app.post("/api/projects/{project_id}/events/{event_id}/acknowledge")
    def acknowledge(project_id: str, event_id: str, value: Acknowledgement):
        with lock:
            return store.acknowledge(project_id, event_id, value.note)

    @app.post("/api/projects/{project_id}/calculations/mse")
    def calculate_mse(project_id: str, value: MSEInput):
        with lock:
            return store.calculation(project_id, "mse", value.model_dump(), mse(value))

    @app.post("/api/projects/{project_id}/calculations/pressure")
    def calculate_pressure(project_id: str, value: PressureInput):
        with lock:
            return store.calculation(project_id, "pressure", value.model_dump(), pressure(value))

    @app.get("/api/audit")
    def audit():
        return store.audit_history()

    @app.post("/api/projects/{project_id}/reports", status_code=201)
    def report_create(project_id: str):
        with lock:
            return store.create_report(project_id)

    @app.get("/api/projects/{project_id}/reports")
    def reports_list(project_id: str):
        return store.reports(project_id)

    @app.get("/api/projects/{project_id}/reports/{report_id}")
    def report_get(project_id: str, report_id: str):
        return store.report(project_id, report_id)

    @app.get("/api/projects/{project_id}/reports/{report_id}/download")
    def report_download(project_id: str, report_id: str):
        value = store.report(project_id, report_id)
        return JSONResponse(value, headers={"Content-Disposition": f'attachment; filename="geodrill-report-{value["snapshot"]["id"]}.json"'})

    @app.get("/api/templates/{kind}")
    def template(kind: Literal["telemetry", "survey", "las"]):
        content = demo.telemetry() if kind == "telemetry" else demo.SURVEY if kind == "survey" else demo.LAS
        return Response(content, media_type="text/plain", headers={"Content-Disposition": f'attachment; filename="synthetic-{kind}.{ "las" if kind == "las" else "csv"}"'})

    dist = frontend_dist(ROOT)
    if (dist / "assets").exists():
        app.mount("/assets", StaticFiles(directory=dist / "assets"), name="assets")

    @app.get("/")
    def index():
        if (dist / "index.html").exists():
            return FileResponse(dist / "index.html")
        return JSONResponse({"detail": "Build the frontend first. See README.md."}, status_code=503)

    @app.get("/favicon.svg")
    def favicon():
        return FileResponse(ROOT / "public" / "favicon.svg")

    return app


app = create_app()
