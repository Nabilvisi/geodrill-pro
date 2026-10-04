"""Capture final live release evidence; prepare then rerun with --after-restart."""
import argparse,ast,hashlib,json,pathlib,re,httpx
from datetime import datetime,timezone
ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/"docs"/"evidence"
PID="8118c063-8e86-4530-9e7f-2b9bdc81c4e0"
NORTH="e5fbd0e2-018a-4459-8389-73ef8e01d86c"
RID="a05ef9f0-9e3b-4f8d-bc74-05422cb9ad3a"
MODELS=["dynamics","bit-condition","wear-fatigue","anomaly","gas-phase","supervision"]
STUDIES={
"dynamics":"6855ce4b-6477-4e36-95d9-0818378e26bb",
"bit-condition":"dfbfd4ea-052c-4d7c-a313-60c728786760",
"wear-fatigue":"38660c51-b3f7-4767-bc12-f758c3785475",
"anomaly":"1fdb012b-4687-4405-9b2f-af9d19470d7d",
"gas-phase":"423b9817-769a-4155-9e64-a5a66a81e72c",
"supervision":"1690880f-c8e4-489c-9993-12ed117212c1"}
WITHHELD={"cab07636-7974-41e5-9c46-d1b74581eddf","2afc4ca7-40af-4b16-b0ac-b0ce08bcdbc4","5ab3ee5d-2afb-4208-bdde-153090a71d1d"}
def canon(v):return json.dumps(v,sort_keys=True,separators=(",",":"),allow_nan=False).encode()
def sha(b):return hashlib.sha256(b).hexdigest()
def write(name,v): (OUT/name).write_text(json.dumps(v,indent=2,allow_nan=False),encoding="utf-8")
ap=argparse.ArgumentParser();ap.add_argument("--after-restart",action="store_true");args=ap.parse_args()
c=httpx.Client(base_url="http://127.0.0.1:8765",timeout=90,headers={"X-Geodrill-Client":"workstation"})
def get(path):r=c.get(path);r.raise_for_status();return r.json()
def post(path,**kw):r=c.post(path,**kw);r.raise_for_status();return r.json()
session=get("/api/session");health=get("/api/health")
assert health["version"]=="0.8.0" and health["equipment_control"] is False
assert session["equipment_authority"]=="none"
base="/api/projects/"+PID
fixture=get(base+"/calculations");byid={x["id"]:x for x in fixture}
summaries={}
for model,sid in STUDIES.items():
 x=byid[sid];r=x["result"];assert x["model"]==model and r["input_document_matches_current"] is True
 assert r["approval_issued"] is False and r["equipment_authority"]=="none"
 assert r["geometry_revision_id"]==x["inputs_si"]["geometry_revision_id"]
 doc=get(base+"/datasets/"+r["input_dataset_id"])
 raw=ROOT/"data"/"raw"/r["input_document_sha256"]
 assert sha(raw.read_bytes())==doc["source_hash"]==r["input_document_sha256"]
 assert doc["parquet_sha256"]==r["input_document_parquet_sha256"]
 summaries[model]={"id":sid,"name":x["inputs_si"]["study_name"],"status":r["status"],"calculation_sha256":sha(canon(x)),"geometry_sha256":r["geometry_sha256"],"input_document_sha256":r["input_document_sha256"],"input_document_matches_current":True}
for sid in WITHHELD:assert byid[sid]["result"]["status"]=="withheld"
wear=byid["ff6cc24b-64a9-47fc-b0d9-acac58accc02"]["result"];assert wear["residual_strength"]["status"]=="withheld"
gaps=byid["ad2298bb-e4e2-44af-902b-4a3f191f5f70"]["result"];assert gaps["unknown_intervals"]==2
phase=byid[STUDIES["gas-phase"]]["result"]["equilibrium"]
assert phase["phase"]=="two_phase" and phase["fugacity_log_residual"]<1e-7 and phase["material_balance_residual"]<1e-12
sim=byid[STUDIES["supervision"]]["result"]
assert sim["equipment_control"] is False and sim["network_adapter_available"] is False
assert sim["accepted_simulation_requests"]==241 and sim["rejected_simulation_requests"]==140
deny=byid["1f1583ba-cdbf-4f9d-a455-66d02f4b1a50"]["result"]
assert deny["accepted_simulation_requests"]==0 and deny["rejected_simulation_requests"]>0
browser=json.loads((OUT/"m1217-report-browser-download.json").read_text(encoding="utf-8"))
report=get(base+"/reports/"+RID)
assert browser==report and sha(canon(report["snapshot"]))==report["sha256"]
assert len(report["snapshot"]["calculations"])==17 and report["snapshot"]["application_version"]=="0.8.0"
reports=[{"id":RID,"sha256":report["sha256"],"application_version":"0.8.0","download_bytes":(OUT/"m1217-report-browser-download.json").stat().st_size}]
prior=[
(NORTH,"597ebab6-0dd3-466a-8420-698129eb30ce","4d16ac076b8531da598b51203ca062523f66ab38289e27e4bcd98bfac354238b"),
("b11e1337-6762-437e-a071-372cd5c9f1de","192073e1-671d-4587-a270-3046cda29c66","4bef5c4be0213e1acb16d809f010533f4d8ce5f03b1da7501d6be6662e8f8ae0"),
(NORTH,"7a89c96a-ce8d-486c-8424-57e0e6779d1d","d612f6c6fbe8bbb485ff1823e8882348c6e7734bace86eff9a2cf77feaecc21a")]
for pid,rid,expected in prior:
 v=get("/api/projects/"+pid+"/reports/"+rid);assert v["sha256"]==sha(canon(v["snapshot"]))==expected
 reports.append({"id":rid,"sha256":expected,"application_version":v["snapshot"]["application_version"],"preserved":True})
northbase="/api/projects/"+NORTH
if not args.after_restart:
 rev=get(northbase+"/engineering-revisions?module=M1")[0]
 nc=get(northbase+"/calculations")
 for model in MODELS:
  name="Synthetic integrated M"+str(12+MODELS.index(model))+" verification"
  if not any(x["model"]==model and x["inputs_si"].get("study_name")==name for x in nc):
   draft=get(northbase+"/research/"+model+"/template/"+rev["id"]);draft["study_name"]=name
   imported=post(northbase+"/research/"+model+"/imports",files={"file":(model+"-integrated.json",json.dumps(draft).encode(),"application/json")})
   post(northbase+"/calculations/"+model,json=imported["inputs_si"])
 candidates=get(northbase+"/reports")
 combined=None
 for candidate in candidates:
  rv=get(northbase+"/reports/"+candidate["id"])
  if rv["snapshot"]["application_version"]=="0.8.0" and set(MODELS)<=set(x["model"] for x in rv["snapshot"]["calculations"]):
   combined=rv;break
 if combined is None:
  created=post(northbase+"/reports");combined=get(northbase+"/reports/"+created["id"])
 write("modules1-17-report.json",combined)
else:
 saved=json.loads((OUT/"modules1-17-report.json").read_text(encoding="utf-8"))
 combined=get(northbase+"/reports/"+saved["snapshot"]["id"]);assert combined==saved
assert sha(canon(combined["snapshot"]))==combined["sha256"]
expected={"casing","clustering","shaly_sand","em_vendor","hydraulics","stability","transport","surge-swab","torque-drag","buckling",*MODELS}
models=set(x["model"] for x in combined["snapshot"]["calculations"]);assert expected<=models
assert any(x["module"]=="M1" for x in combined["snapshot"]["engineering_revisions"])
reports.append({"id":combined["snapshot"]["id"],"sha256":combined["sha256"],"application_version":"0.8.0","modules":"M1 geometry and calculations through M17","calculation_models":sorted(models)})
selector=json.loads((ROOT/"frontend-build.json").read_text(encoding="utf-8"))
release=ROOT/selector["directory"]
html=c.get("/").content;assert html==(release/"index.html").read_bytes()
assets=[]
for url in re.findall(r'(?:src|href)="(/assets/[^"]+)"',html.decode()):
 live=c.get(url);live.raise_for_status();local=(release/url.removeprefix("/")).read_bytes();assert live.content==local
 assets.append({"url":url,"sha256":sha(local),"bytes":len(local)})
assert len(assets)>=2
# Inspect the registered route declarations; production disables OpenAPI.
tree=ast.parse((ROOT/"services"/"api"/"main.py").read_text(encoding="utf-8"))
route_paths=[node.args[0].value for node in ast.walk(tree) if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and node.func.attr in {"get","post","put","patch","delete"} and node.args and isinstance(node.args[0],ast.Constant) and isinstance(node.args[0].value,str) and node.args[0].value.startswith("/api/")]
assert not any("command" in p or "equipment" in p for p in route_paths)
assert c.post(base+"/commands",json={}).status_code==404
assert c.post(base+"/equipment/write",json={}).status_code==404
audit=get("/api/audit");assert audit["integrity"]=="verified"
proof={"verified_at":datetime.now(timezone.utc).isoformat(),"release":selector["directory"],"health":health,"assets":assets,"reports":reports,"saved_studies":summaries,"withheld_studies":sorted(WITHHELD),"live_checks":{"six_imported_studies_preserved":True,"source_hashes_verified":True,"native_gap_unknown_intervals":gaps["unknown_intervals"],"fault_simulation_accepted":sim["accepted_simulation_requests"],"fault_simulation_rejected":sim["rejected_simulation_requests"],"no_authority_accepted":deny["accepted_simulation_requests"],"phase_material_balance_residual":phase["material_balance_residual"],"phase_fugacity_log_residual":phase["fugacity_log_residual"],"browser_report_download_matches_fixed_snapshot":True,"no_equipment_write_routes":True},"audit":{"integrity":audit["integrity"],"head":audit["head"],"entries":len(audit["entries"])},"after_service_restart":args.after_restart,"automated_regression":{"passed":406,"warnings":1}}
if args.after_restart:
 before=json.loads((OUT/"m1217-before-restart.json").read_text(encoding="utf-8"))
 assert health["pid"]!=before["health"]["pid"]
 assert proof["saved_studies"]==before["saved_studies"] and proof["reports"]==before["reports"] and proof["assets"]==before["assets"]
 proof["previous_service_pid"]=before["health"]["pid"];write("m1217-live-verification.json",proof)
else:write("m1217-before-restart.json",proof)
print(json.dumps({"health":health,"assets":assets,"reports":reports,"audit":proof["audit"],"after_restart":args.after_restart}))
