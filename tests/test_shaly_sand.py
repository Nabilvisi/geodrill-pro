import copy
import math
import random
import pytest
from pydantic import ValidationError
from packages.engineering.shaly_sand import ShalySandInput, volume_scenario, interpret_logs
from test_geometry_casing import api_setup
from services.api.main import create_app
from fastapi.testclient import TestClient

CURVES=[{"mnemonic":"DEPT","unit":"M"},{"mnemonic":"VSH","unit":"V/V"},{"mnemonic":"PHIT","unit":"V/V"},{"mnemonic":"GR","unit":"API"}]
def inputs(**patch):
    value={"study_name":"Volume balance fixture","dataset_id":"fixture","geometry_revision_id":"fixture","depth_datum":"RKB",
           "porosity":{"curve":"PHIT","unit":"V/V","basis":"total","uncertainty":0.,"source_note":"Synthetic total physical porosity"},
           "shale_indicator":{"curve":"VSH","unit":"V/V","method":"supplied_volume","uncertainty":0.,"calibration_note":"Synthetic known wet shale volume"},
           "endpoints":{"sand_porosity":.3,"shale_porosity":.15,"sand_porosity_uncertainty":0.,"shale_porosity_uncertainty":0.,
              "gr_clean_api":20.,"gr_shale_api":100.,"gr_clean_uncertainty_api":0.,"gr_shale_uncertainty_api":0.,
              "source_note":"Synthetic endmembers","porosity_convention_note":"Physical total volume with shale pores"},
           "correction_status":"synthetic","correction_note":"Generated compatible fractions","acquisition_quality_note":"No field evidence",
           "depth_alignment_note":"Synthetic aligned MD","mineral_fluid_note":"Quartz framework and wet shale; no gas response"}
    return ShalySandInput.model_validate({**value,**patch})

@pytest.mark.parametrize("v,total,e,branch",[(0.,.3,.3,"laminated"),(.3,.045,0.,"laminated_dispersed"),
    (.7,.405,.3,"laminated_structural"),(1.,.15,0.,"laminated"),(.4,.24,.18,"laminated")])
def test_published_construction_vertices_and_laminated_identity(v,total,e,branch):
    r=volume_scenario(v,total,.3,.15)
    assert r["primary_porosity_bulk"]==pytest.approx(e,abs=1e-12)
    assert r["restricted_scenario"]["branch"]==branch
    assert r["volume_balance_residual"]==pytest.approx(0.,abs=1e-12)
    assert r["porosity_residual"]==pytest.approx(0.,abs=1e-12)

def test_independent_volume_accounting_for_dispersed_and_structural_mixtures():
    # 0.4 laminated, 0.06 dispersed in bulk; host primary pores 0.6*0.3-0.06.
    dispersed=volume_scenario(.46,.189,.3,.15)["restricted_scenario"]
    assert dispersed["laminated_bulk"]==pytest.approx(.4)
    assert dispersed["dispersed_bulk"]==pytest.approx(.06)
    assert dispersed["structural_bulk"]==pytest.approx(0.,abs=1e-12)
    # 0.2 laminated, 0.3 structural; primary pores unchanged at 0.8*0.3.
    structural=volume_scenario(.5,.315,.3,.15)["restricted_scenario"]
    assert structural["laminated_bulk"]==pytest.approx(.2)
    assert structural["structural_bulk"]==pytest.approx(.3)
    assert structural["dispersed_bulk"]==pytest.approx(0.,abs=1e-12)

def test_coexisting_textures_remain_nonunique_even_on_laminated_line():
    result=volume_scenario(.4,.24,.3,.15)
    assert result["texture_nonunique"]
    assert result["laminated_range"]==pytest.approx([0.,.4])
    assert result["restricted_scenario"]["branch"]=="laminated"
    assert result["coexistence_family"][0]["dispersed_bulk"]==pytest.approx(.12)
    assert result["coexistence_family"][0]["structural_bulk"]==pytest.approx(.28)
    assert volume_scenario(1.,.15,.3,.15)["restricted_scenario"]["primary_porosity_host_normalized"] is None

def test_random_forward_volumes_recover_original_inside_admissible_family():
    rng=random.Random(31875)
    for _ in range(200):
        a=rng.uniform(.1,.55);b=rng.uniform(0,.4);lam=rng.uniform(0,.95)
        d=rng.random()*(1-lam)*a;s=rng.random()*(1-lam)*(1-a)
        effective=(1-lam)*a-d;v=lam+d+s;total=effective+v*b
        result=volume_scenario(v,total,a,b)
        assert result is not None
        assert lam<=result["laminated_range"][1]+1e-9
        for c in result["coexistence_family"]:
            assert c["dispersed_bulk"]>=0 and c["structural_bulk"]>=0
            assert c["laminated_bulk"]+c["dispersed_bulk"]+c["structural_bulk"]==pytest.approx(v)
            assert (1-c["laminated_bulk"])*a-c["dispersed_bulk"]==pytest.approx(effective)
        assert result["quartz_grain_fraction"]+result["shale_solid_fraction"]+total==pytest.approx(1.)

@pytest.mark.parametrize("v,total",[(-.1,.2),(1.1,.2),(.8,.6),(.1,.05),(0.,.4),(.5,-.1),(float("nan"),.3)])
def test_nonphysical_observations_are_not_clipped_into_solutions(v,total):
    assert volume_scenario(v,total,.3,.15) is None

def test_missing_outside_survey_and_bad_volume_rows_are_withheld():
    rows=[{"depth_m":1.,"PHIT":.24,"VSH":.4},{"depth_m":2.,"PHIT":None,"VSH":.4},
          {"depth_m":3.,"PHIT":.6,"VSH":.8},{"depth_m":1001.,"PHIT":.24,"VSH":.4}]
    result=interpret_logs(inputs(),rows,CURVES,1000.)
    assert result["eligible_count"]==1 and result["withheld_count"]==3
    assert result["rows"][0]["status"]=="ambiguous"
    assert result["rows"][2]["status"]=="outside_applicability"
    assert all(r["scenario"] is None for r in result["rows"][1:])
    assert result["interpretation_approved"] is False

def test_raw_inputs_withhold_instead_of_silent_correction():
    result=interpret_logs(inputs(correction_status="raw"),[{"depth_m":1.,"PHIT":.24,"VSH":.4}],CURVES,1000.)
    assert result["status"]=="withheld"
    assert "Corrected" in result["rows"][0]["reason"]

def test_fraction_percent_and_supplied_linear_gr_calibration_agree():
    row={"depth_m":1.,"PHIT":.24,"VSH":.4,"GR":52.}
    baseline=interpret_logs(inputs(),[row],CURVES,1000.)["rows"][0]["scenario"]
    gr=inputs(shale_indicator={"curve":"GR","unit":"API","method":"linear_gr","uncertainty":0.,"calibration_note":"Synthetic linear relation"})
    assert interpret_logs(gr,[row],CURVES,1000.)["rows"][0]["scenario"]==baseline
    value=inputs().model_dump();value["porosity"]["unit"]="PU";value["shale_indicator"]["unit"]="%"
    curves=copy.deepcopy(CURVES);curves[1]["unit"]="%";curves[2]["unit"]="PU"
    percent=interpret_logs(inputs(**value),[{**row,"PHIT":24.,"VSH":40.}],curves,1000.)
    assert percent["rows"][0]["scenario"]==baseline

def test_endpoint_sensitivity_changes_branch_and_retains_outside_corners():
    value=inputs().model_dump()
    value["porosity"]["uncertainty"]=.03
    value["shale_indicator"]["uncertainty"]=.05
    value["endpoints"]["sand_porosity_uncertainty"]=.02
    result=interpret_logs(inputs(**value),[{"depth_m":1.,"PHIT":.24,"VSH":.4}],CURVES,1000.)
    sensitivity=result["rows"][0]["sensitivity"]
    assert sensitivity["tested_admissible_corners"]+sensitivity["tested_outside_corners"]==8
    assert set(sensitivity["restricted_branches"])=={"laminated_dispersed","laminated_structural"}
    ranges=sensitivity["tested_ranges"]["primary_porosity_bulk"]
    assert ranges==pytest.approx([.1425,.2175])
    bad=inputs().model_dump();bad["porosity"]["uncertainty"]=.2
    r=interpret_logs(inputs(**bad),[{"depth_m":1.,"PHIT":.045,"VSH":.3}],CURVES,1000.)["rows"][0]
    assert r["sensitivity"]["tested_outside_corners"]>0

@pytest.mark.parametrize("field,value",[("sand_porosity",0.),("sand_porosity",1.),("gr_shale_api",20.),("sand_porosity_uncertainty",.5)])
def test_degenerate_endpoints_rejected(field,value):
    data=inputs().model_dump();data["endpoints"][field]=value
    with pytest.raises(ValidationError): inputs(**data)

def test_apparent_porosity_and_wrong_curve_units_rejected():
    data=inputs().model_dump();data["porosity"]["basis"]="apparent"
    with pytest.raises(ValidationError): inputs(**data)
    with pytest.raises(ValueError,match="exact source units"):
        interpret_logs(inputs(),[],[{"mnemonic":"DEPT","unit":"M"},{"mnemonic":"PHIT","unit":"UNKNOWN"}],1000.)

def test_api_source_binding_report_restart_datum_and_synthetic_boundary(api_setup):
    c,p,base,d,store,root=api_setup
    revision=c.post(base+"/geometry",json={"geometry":d,"change_note":"Shaly sand context"}).json()
    text="~Version\nVERS. 2.0\nWRAP. NO\n~Well\nNULL. -999.25\n~Curve\nDEPT.M\nVSH.V/V\nPHIT.V/V\n~ASCII\n1 .4 .24\n2 .46 .189\n"
    imported=c.post(base+"/imports",data={"kind":"las"},files={"file":("shale.las",text,"text/plain")}).json()
    source=c.get(base+"/datasets/"+imported["id"]).json()
    value=inputs(dataset_id=source["id"],geometry_revision_id=revision["id"]).model_dump()
    response=c.post(base+"/calculations/shaly-sand",json=value)
    assert response.status_code==200,response.text
    saved=response.json()
    assert saved["result"]["source_sha256"]==source["source_hash"]
    assert saved["result"]["geometry_sha256"]==revision["sha256"]
    report=c.post(base+"/reports").json();snapshot=c.get(base+"/reports/"+report["id"]).json()
    assert saved in snapshot["snapshot"]["calculations"]
    after=TestClient(create_app(root));after.get("/api/session")
    assert after.get(base+"/calculations?model=shaly_sand").json()==[saved]
    assert c.post(base+"/calculations/shaly-sand",json={**value,"depth_datum":"MSL"}).status_code==422
    example=c.post(base+"/examples/shaly-sand");assert example.status_code==201
    assert c.post(base+"/examples/shaly-sand").json()["duplicate"]
    other=c.post("/api/projects",json={"name":"History","well_name":"Other","datum":"RKB","origin":"historical","bit_diameter_m":.2}).json()
    assert c.post("/api/projects/"+other["id"]+"/examples/shaly-sand").status_code==422
    assert c.post("/api/projects/"+other["id"]+"/calculations/shaly-sand",json=value).status_code==404
    (root/"raw"/source["source_hash"]).write_bytes(b"changed")
    assert c.post(base+"/calculations/shaly-sand",json=value).status_code==422
    assert c.get(base+"/reports/"+report["id"]).json()==snapshot
