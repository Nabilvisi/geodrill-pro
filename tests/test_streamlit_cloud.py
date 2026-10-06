"""Cloud transport isolation, imports, immutable writes, exports and reruns."""
import base64,hashlib,json
from pathlib import Path
import pytest
from apps.streamlit.cloud import Workspace
ROOT=Path(__file__).resolve().parents[1]
def decoded(v):return json.loads(base64.b64decode(v["body_base64"]))
def req(i,m,p,b=None):return {"id":i,"method":m,"path":p,**({"body":json.dumps(b)} if b is not None else {})}
def project(w):
 r=w.execute(req("p","POST","/api/projects",{"name":"Cloud test","well_name":"Synthetic","datum":"RKB","bit_diameter_m":.216,"origin":"synthetic"}));assert r["status"]==201
 return decoded(r)
@pytest.fixture
def workspace():
 w=Workspace(seed=False);yield w;w.close()
@pytest.fixture(scope="module")
def seeded():
 w=Workspace();yield w;w.close()
def test_workspace_isolation(workspace):
 p=project(workspace);other=Workspace(seed=False)
 try:
  assert decoded(other.execute(req("q","GET","/api/projects")))==[]
  assert other.execute(req("forbidden","GET","/api/projects/"+p["id"]+"/datasets"))["status"]==404
 finally:other.close()
def test_replays_do_not_duplicate_mutations(workspace):
 r=req("once","POST","/api/projects",{"name":"One project","well_name":"Synthetic","datum":"RKB","bit_diameter_m":.216,"origin":"synthetic"})
 value=workspace.execute(r);assert workspace.execute(r)==value
 r["body"]=r["body"].replace("One project","Changed project")
 with pytest.raises(ValueError,match="changed content"):workspace.execute(r)
 assert len(workspace.call("GET","/api/projects"))==1
@pytest.mark.parametrize("path",["https://example.com/api/projects","//example.com/api/projects","/api/../data","/api/%2e%2e/data","/etc/passwd","/api/projects#fragment","/api/\\data"])
def test_proxy_rejects_external_and_file_routes(workspace,path):
 with pytest.raises(ValueError):workspace.execute(req("reject","GET",path))
def test_validation_and_private_session_cookie(workspace):
 r=workspace.execute(req("invalid","POST","/api/projects",{"name":"incomplete"}))
 assert r["status"]==422 and "detail" in decoded(r)
 assert "set-cookie" not in workspace.execute(req("session","GET","/api/session"))["headers"]
def test_original_multipart_source_bytes(workspace):
 p=project(workspace);raw=b"md[m],inclination[deg],azimuth[deg]\n0,0,0\n1000,0,0\n"
 r=workspace.execute({"id":"upload","method":"POST","path":"/api/projects/"+p["id"]+"/imports","form":[{"name":"kind","value":"survey"},{"name":"file","filename":"native.csv","type":"text/csv","file_base64":base64.b64encode(raw).decode()}]})
 assert r["status"]==201
 imported=decoded(r);d=workspace.call("GET","/api/projects/"+p["id"]+"/datasets/"+imported["id"]);assert d["source_hash"]==hashlib.sha256(raw).hexdigest()
 assert (workspace.root/"raw"/d["source_hash"]).read_bytes()==raw
def test_bad_imports_have_no_side_effect(workspace):
 p=project(workspace);path="/api/projects/"+p["id"]+"/imports"
 for val in ["not base64!","A"*(2*1024*1024*4//3+8)]:
  with pytest.raises(ValueError):workspace.execute({"id":"bad-"+str(len(val)),"method":"POST","path":path,"form":[{"name":"file","file_base64":val,"filename":"data.csv"}]})
 assert workspace.call("GET","/api/projects/"+p["id"]+"/datasets")==[]
def test_seeded_models_preserve_original_geometry_and_documents(seeded):
 p=next(p for p in seeded.call("GET","/api/projects") if p["name"].startswith("Cloud verification"))
 rows=seeded.call("GET","/api/projects/"+p["id"]+"/calculations")
 assert {x["model"] for x in rows}=={"dynamics","bit-condition","wear-fatigue","anomaly","gas-phase","supervision","offset-benchmarking"}
 for x in rows:
  r=x["result"];assert r["geometry_revision_id"]==x["inputs_si"]["geometry_revision_id"]
  assert r["input_document_matches_current"] and r["equipment_authority"]=="none" and not r["approval_issued"]
def test_complete_fixed_report_download(seeded):
 p=next(p for p in seeded.call("GET","/api/projects") if p["name"].startswith("Cloud verification"));b="/api/projects/"+p["id"]
 created=decoded(seeded.execute(req("create-report","POST",b+"/reports")))
 v=decoded(seeded.execute(req("download-report","GET",b+"/reports/"+created["id"]+"/download")))
 filename="geodrill-report-"+created["id"]+".json"
 original=seeded.client.get(b+"/reports/"+created["id"]+"/download").content
 assert seeded.report_downloads[filename]==original
 assert len(v["snapshot"]["calculations"])==7
 canonical=json.dumps(v["snapshot"],sort_keys=True,separators=(",",":"),allow_nan=False).encode()
 assert hashlib.sha256(canonical).hexdigest()==v["sha256"]==created["sha256"]
 seeded.call("POST",b+"/reports")
 assert seeded.call("GET",b+"/reports/"+created["id"])==v

def test_native_report_exports_are_bounded_and_session_private(workspace):
 p=project(workspace);b="/api/projects/"+p["id"]
 workspace.execute(req("read-project","GET",b))
 assert not workspace.report_downloads
 names=[]
 for index in range(4):
  created=workspace.call("POST",b+"/reports")
  workspace.execute(req("export-"+str(index),"GET",b+"/reports/"+created["id"]+"/download"))
  names.append("geodrill-report-"+created["id"]+".json")
 assert list(workspace.report_downloads)==names[-3:]
 other=Workspace(seed=False)
 try:assert not other.report_downloads
 finally:other.close()
def test_batch_error_keeps_next_request_working(workspace):
 r=workspace.batch({"requests":[req("bad","GET","https://example.com/api"),req("ok","GET","/api/health")]})
 assert r[0]["status"]==422 and r[1]["status"]==200 and not decoded(r[1])["equipment_control"]
def test_streamlit_rerun_keeps_workspace():
 from streamlit.testing.v1 import AppTest
 at=AppTest.from_file(str(ROOT/"apps/streamlit/app.py"),default_timeout=40).run()
 assert not at.exception and at.title[0].value=="GeoDrill Pro"
 ids=[p["id"] for p in at.session_state["_geodrill_workspace"].call("GET","/api/projects")]
 at.run();assert not at.exception
 assert [p["id"] for p in at.session_state["_geodrill_workspace"].call("GET","/api/projects")]==ids
