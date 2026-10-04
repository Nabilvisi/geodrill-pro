import copy
import math
import pytest
from pydantic import ValidationError
from fastapi.testclient import TestClient
from packages.engineering.clustering import ClusteringInput, cluster_logs, adjusted_rand, lloyd
from test_geometry_casing import api_setup
from services.api.main import create_app

CURVES=[{"mnemonic":"DEPT","unit":"M"},{"mnemonic":"A","unit":"API"},{"mnemonic":"B","unit":"OHMM"}]
ROWS=[{"depth_m":float(i),"A":float(a),"B":float(a*2+3)} for i,a in enumerate([-1,0,1,9,10,11])]

def inputs(**changes):
    return ClusteringInput.model_validate({**{"dataset_id":"fixture","geometry_revision_id":"fixture","study_name":"Analytic fixture",
        "depth_datum":"RKB","maximum_native_gap_m":2.,"features":[{"curve":"A","unit":"API","transform":"identity","minimum":-2.,"maximum":12.,"range_basis":"Synthetic envelope"}],
        "clusters":2,"seed":42,"fit_top_md_m":0.,"fit_bottom_md_m":5.,"depth_alignment_note":"Synthetic aligned MD samples",
        "correction_status":"raw","correction_note":"Synthetic fixture without tool correction","acquisition_quality_note":"Synthetic input values"},
        **changes})

def run(value=None,rows=None):
    return cluster_logs(value or inputs(),ROWS if rows is None else rows,CURVES,1000.)

def test_known_separated_groups_population_scaling_and_inertia():
    result=run()
    assert result["status"]=="exploratory"
    assert [r["cluster"] for r in result["rows"]]==[1,1,1,2,2,2]
    assert [c["response_centers"]["A"] for c in result["centers"]]==pytest.approx([0.,10.])
    # Independent population second moment: E[x²]-E[x]² = 77/3.
    assert result["scaling"][0]["training_mean"]==5.
    assert result["scaling"][0]["training_population_std"]==pytest.approx(math.sqrt(77/3))
    assert result["inertia"]==pytest.approx(12/77)
    assert result["initialization_agreement_min_ari"]==1.
    assert result["facies_confirmation"] is False
    assert result==run()

def test_feature_order_and_descending_source_depth_do_not_change_assignment():
    features=inputs().features
    second={"curve":"B","unit":"OHMM","transform":"identity","minimum":0.,"maximum":30.,"range_basis":"Synthetic second feature"}
    a=inputs(features=[features[0].model_dump(),second])
    b=inputs(features=[second,features[0].model_dump()])
    assert run(a)==run(b)
    reverse=run(a,list(reversed(ROWS)))
    assert [r["cluster"] for r in reverse["rows"]]==[r["cluster"] for r in run(a)["rows"]]
    assert [r["source_index"] for r in reverse["rows"]]==[5,4,3,2,1,0]

def test_missing_out_of_envelope_and_outside_survey_are_withheld_not_imputed():
    rows=copy.deepcopy(ROWS)+[{"depth_m":6.,"A":None},{"depth_m":7.,"A":100.},{"depth_m":1100.,"A":5.}]
    result=run(rows=rows)
    assert result["excluded_count"]==3
    assert all(r["cluster"] is None and r["distance"] is None for r in result["rows"][-3:])
    assert "Missing A" in result["rows"][-3]["reason"]
    assert "declared range" in result["rows"][-2]["reason"]
    assert "survey" in result["rows"][-1]["reason"]
    assert result["scaling"]==run()["scaling"]

def test_scaling_is_fit_only_on_training_interval_and_missing_rows_break_groups():
    rows=copy.deepcopy(ROWS)+[{"depth_m":6.,"A":9.},{"depth_m":7.,"A":None},{"depth_m":8.,"A":9.}]
    result=run(rows=rows)
    assert result["training_count"]==6
    assert result["scaling"]==run()["scaling"]
    assert result["intervals"][-1]["first_sample_md_m"]==8.
    assert result["intervals"][-2]["last_sample_md_m"]==6.

def test_native_gaps_end_groups_without_invented_boundaries():
    rows=[{**r,"depth_m":r["depth_m"]+(20 if i>=2 else 0)} for i,r in enumerate(ROWS)]
    result=run(inputs(fit_bottom_md_m=30.),rows)
    assert result["intervals"][0]["last_sample_md_m"]==1.
    assert result["intervals"][1]["first_sample_md_m"]==22.

def test_degenerate_and_insufficient_features_withhold_results():
    constant=[{**r,"A":3.} for r in ROWS]
    assert run(rows=constant)["status"]=="insufficient_data"
    assert "variance" in run(rows=constant)["reason"]
    assert run(inputs(clusters=4))["centers"]==[]
    assert run(inputs(fit_top_md_m=1.,fit_bottom_md_m=2.))["status"]=="insufficient_data"

def test_log_transform_back_transforms_center_and_excludes_nonpositive():
    rows=[{"depth_m":float(i),"B":x} for i,x in enumerate([1.,10.,100.,1e4,1e5,1e6,0.])]
    value=inputs(features=[{"curve":"B","unit":"OHMM","transform":"log10","minimum":1.,"maximum":1e6,"range_basis":"Synthetic log envelope"}])
    result=run(value,rows)
    assert [c["response_centers"]["B"] for c in result["centers"]]==pytest.approx([10.,1e5])
    assert result["rows"][-1]["cluster"] is None

def test_adjusted_rand_reference_partitions_are_label_invariant():
    assert adjusted_rand([0,0,1,1],[2,2,9,9])==1.
    assert adjusted_rand([0,0,1,1],[0,1,0,1])==pytest.approx(-.5)
    assert adjusted_rand([0,0],[1,1])==1.

@pytest.mark.parametrize("change",[
    {"features":[{"curve":"A","unit":"API","transform":"log10","minimum":0.,"maximum":5.,"range_basis":"Bad domain"}]},
    {"seed":-1},{"clusters":1},{"maximum_native_gap_m":0.},{"fit_bottom_md_m":0.}
])
def test_invalid_contracts_rejected(change):
    with pytest.raises(ValidationError):
        inputs(**change)

def test_unit_mismatch_and_bounded_workload_rejected():
    bad=inputs().model_dump();bad["features"][0]["unit"]="mystery"
    with pytest.raises(ValueError,match="exact source unit"):
        run(inputs(**bad))
    with pytest.raises(ValueError,match="2,500"):
        run(rows=[ROWS[0]]*2501)
    with pytest.raises(ValueError,match="survey"):
        cluster_logs(inputs(),ROWS,CURVES,4.)

def test_api_persists_complete_evidence_report_restart_and_project_ownership(api_setup):
    c,p,base,d,store,root=api_setup
    revision=c.post(base+"/geometry",json={"geometry":d,"change_note":"Clustering survey context"}).json()
    text="~Version\nVERS. 2.0\nWRAP. NO\n~Well\nNULL. -999.25\n~Curve\nDEPT.M\nA.API\n~ASCII\n"+"".join(f"{r['depth_m']} {r['A']}\n" for r in ROWS)
    source=c.post(base+"/imports",data={"kind":"las"},files={"file":("logs.las",text,"text/plain")}).json()
    source=c.get(base+"/datasets/"+source["id"]).json()
    value=inputs(dataset_id=source["id"],geometry_revision_id=revision["id"]).model_dump()
    response=c.post(base+"/calculations/clustering",json=value)
    assert response.status_code==200,response.text
    saved=response.json()
    assert saved["result"]["source_sha256"]==source["source_hash"]
    assert saved["result"]["geometry_sha256"]==revision["sha256"]
    assert saved["result"]["parquet_sha256"]==source["parquet_sha256"]
    assert c.get(base+"/calculations?model=clustering").json()==[saved]
    report=c.post(base+"/reports").json()
    snapshot=c.get(base+"/reports/"+report["id"]).json()
    assert saved in snapshot["snapshot"]["calculations"]
    after=TestClient(create_app(root));after.get("/api/session")
    assert after.get(base+"/calculations?model=clustering").json()==[saved]
    assert c.post(base+"/calculations/clustering",json={**value,"depth_datum":"MSL"}).status_code==422
    other=c.post("/api/projects",json={"name":"Other","well_name":"Other","datum":"RKB","bit_diameter_m":.2,"origin":"synthetic"}).json()
    assert c.post("/api/projects/"+other["id"]+"/calculations/clustering",json=value).status_code==404
    (root/"raw"/source["source_hash"]).write_bytes(b"changed")
    assert c.post(base+"/calculations/clustering",json=value).status_code==422
    assert c.get(base+"/reports/"+report["id"]).json()==snapshot
