"""Published-formulation and independent equilibrium checks for M11."""
import copy
import math
import pytest
from pydantic import ValidationError
from fastapi.testclient import TestClient
from packages.engineering.buckling import BucklingInput,buckling,thresholds,transfer,mode,interpolate
from packages.engineering.torque_drag import TorqueDragInput,torque_drag
from packages.engineering.geometry import Path,GeometryInput
from packages.version import APP_VERSION
from packages.engineering.models import SurveyRequest
from services.api import demo
from services.api.main import create_app
from services.api.storage import digest,canonical
from test_geometry_casing import api_setup,geom

def fixture(angle=math.pi/2):
    g=geom();g["casings"]=[];g=GeometryInput.model_validate(g)
    p=Path(SurveyRequest(stations=[{"md_m":0.,"inclination_rad":angle,"azimuth_rad":0.},{"md_m":1000.,"inclination_rad":angle,"azimuth_rad":0.}]))
    revision={"id":"fixture","input":g.model_dump(),"result":{"total_depth_md_m":1000.}}
    source=demo.research_template("torque-drag",revision,"synthetic")
    source.update(operation="slackoff",axial_speed_m_s=-.1,bottom_tension_n=-150000.,friction_delta=.02)
    v=demo.research_template("buckling",revision,"synthetic");v["torque_drag_calculation_id"]="source"
    return v,g,p,source,torque_drag(TorqueDragInput.model_validate(source),g,p)

def run(**patch):
    v,g,p,s,r=fixture();v.update(patch)
    return buckling(BucklingInput.model_validate(v),g,p,s,r)

@pytest.mark.parametrize("angle",[math.pi/6,math.pi/3,math.pi/2])
def test_published_dawson_paslay_and_chen_nondimensional_limits(angle):
    # Published inclined formulas, BSEE 300an §§2.2.1/2.2.3; Liang & Zhu (2018).
    # Independent manufactured SI inputs. Not laboratory/field validation.
    fs,fh=thresholds(1000.,100.,.1,angle)
    assert fs==pytest.approx(2000*math.sqrt(math.sin(angle)))
    assert fh==pytest.approx(2000*math.sqrt(2*math.sin(angle)))
    assert fh/fs==pytest.approx(math.sqrt(2))

def test_independent_rayleigh_energy_minimum_matches_long_pipe_screen():
    # y=a sin(kx); Rayleigh quotient EI*k² + (q/r)/k².
    ei,q,r=7000.,80.,.06;k=(q/(r*ei))**.25
    minimum=ei*k*k+(q/r)/(k*k)
    fs,_=thresholds(ei,q,r,math.pi/2)
    assert fs==pytest.approx(minimum)
    assert ei*(k*.8)**2+q/r/(k*.8)**2>minimum
    assert ei*(k*1.2)**2+q/r/(k*1.2)**2>minimum

@pytest.mark.parametrize("mu",[0.,.05,.2])
def test_helical_transfer_independent_horizontal_riccati_solution(mu):
    # C'=mu(q+a*C²), constant helical branch, C(0)=40000.
    length,c0,q,ei,r=100.,40000.,228.7,1.26e6,.0865
    a=r/(4*ei)
    expected=c0 if mu==0 else math.sqrt(q/a)*math.tan(math.atan(c0*math.sqrt(a/q))+mu*math.sqrt(q*a)*length)
    rows=transfer(length,-c0,q,math.pi/2,mu,ei,r,1000.,-1,256)
    assert -rows[-1]["effective_tension_n"]==pytest.approx(expected,rel=1e-9)

def test_tension_branch_has_zero_added_contact_and_exact_transfer():
    x=run();assert x["status"]=="research_scenario"
    x=run(force_basis="supplied_wall_forces",wall_loads=[{"md_m":m,"wall_tension_n":1000.,"internal_absolute_pa":0.,"external_absolute_pa":0.} for m in (0.,1000.)],transfer_model="ideal_helical_axial_drag")
    assert x["load_transfer"]["status"]=="converged"
    assert all(r["compression_n"]==0 and r["ideal_added_contact_n_per_m"]==0 for r in x["profile"])
    # The prescribed bottom force conditional transfer can become compressive uphole.
    assert x["load_transfer"]["unbuckled_upper_effective_tension_n"]<1000.

def test_local_pressure_correction_sign_and_absolute_common_reference():
    knots=[{"md_m":m,"wall_tension_n":1000.,"internal_absolute_pa":2e6,"external_absolute_pa":1e6} for m in (0.,1000.)]
    x=run(force_basis="supplied_wall_forces",wall_loads=knots)
    expected=1000-2e6*math.pi*.108**2/4+1e6*math.pi*.127**2/4
    assert all(r["effective_tension_n"]==pytest.approx(expected) for r in x["profile"])
    assert x["maximum_compression_n"]==pytest.approx(max(0.,-expected))

@pytest.mark.parametrize("c,expected",[(0,"tension"),(-1,"tension"),(99,"below_sinusoidal"),(100,"sinusoidal_susceptibility"),(141.5,"helical_susceptibility")])
def test_onset_branches_are_distinct(c,expected):
    assert mode(c,100.,math.sqrt(2)*100)==expected

def test_uncertainty_corners_change_margin_and_do_not_change_nominal_input():
    x=run();fs=x["sinusoidal_threshold_n"]
    low,high=x["sinusoidal_threshold_range_n"]
    assert low==pytest.approx(fs*math.sqrt(.95/1.05))
    assert high==pytest.approx(fs*math.sqrt(1.05/.95))
    assert all(r["upper_compression_n"]==pytest.approx(r["compression_n"]+1000) for r in x["profile"])

@pytest.mark.parametrize("patch",[
    {"evidence_state":"unknown"},{"boundary":"unknown"},{"boundary":"pinned"},{"boundary":"clamped"},
    {"pipe_configuration":"tool_joints"},{"pipe_configuration":"stabilizers"},{"pipe_configuration":"unknown"},
    {"top_md_m":900.},{"evidence_state":"supplied"}
])
def test_unsupported_assumptions_withhold(patch):
    x=run(**patch);assert x["status"]=="withheld";assert not x["profile"]
    assert not x["approval_issued"]

@pytest.mark.parametrize("patch",[
    {"bottom_md_m":0.},{"bottom_md_m":float("nan")},{"young_modulus_pa":float("inf")},
    {"young_modulus_pa":0.},{"modulus_relative_delta":1.},{"integration_cells":10000},
    {"compression_allowance_n":-1.},{"unexpected":True},
    {"force_basis":"supplied_wall_forces"},{"wall_loads":[{"md_m":0.,"wall_tension_n":0.,"internal_absolute_pa":0.,"external_absolute_pa":0.}]}
])
def test_invalid_contract_rejects(patch):
    v,*_=fixture();v.update(patch)
    with pytest.raises(ValidationError):BucklingInput.model_validate(v)

@pytest.mark.parametrize("angle",[0.,math.radians(4.9),math.radians(110)])
def test_vertical_near_vertical_upgoing_are_blocked(angle):
    v,g,p,s,r=fixture(angle)
    x=buckling(BucklingInput.model_validate(v),g,p,s,r)
    assert x["status"]=="withheld";assert any("Inclination" in r for r in x["reasons"])

def test_hidden_curvature_between_matching_endpoints_is_blocked():
    v,g,p,s,r=fixture()
    p=Path(SurveyRequest(stations=[{"md_m":m,"inclination_rad":a,"azimuth_rad":0.} for m,a in [(0.,math.pi/2),(500.,math.pi/3),(1000.,math.pi/2)]]))
    x=buckling(BucklingInput.model_validate(v),g,p,s,r)
    assert x["status"]=="withheld";assert any("Curved" in r for r in x["reasons"])

@pytest.mark.parametrize("patch",[{"rotation_rad_s":1.,"operation":"combined"},{"bottom_torque_nm":100.}])
def test_rotation_and_torque_blocked(patch):
    v,g,p,s,r=fixture();s.update(patch)
    x=buckling(BucklingInput.model_validate(v),g,p,s,r);assert x["status"]=="withheld"

def test_installed_casing_changes_clearance_planned_does_not():
    v,g,p,s,r=fixture();raw=g.model_dump();c=geom()["casings"][0];c.update(outside_diameter_m=.25,inside_diameter_m=.23,minimum_wall_m=.009);raw["casings"]=[c]
    planned=buckling(BucklingInput.model_validate(v),GeometryInput.model_validate(raw),p,s,r)
    assert planned["radial_clearance_m"]==pytest.approx((.3-.127)/2)
    raw["casings"][0]["state"]="installed"
    installed=buckling(BucklingInput.model_validate(v),GeometryInput.model_validate(raw),p,s,r)
    assert installed["radial_clearance_m"]==pytest.approx((c["inside_diameter_m"]-.127)/2)
    assert installed["sinusoidal_threshold_n"]>planned["sinusoidal_threshold_n"]

def test_installed_casing_transition_blocks_whole_interval():
    v,g,p,s,r=fixture();raw=g.model_dump();c=geom()["casings"][0];c.update(state="installed",bottom_md_m=500.)
    raw["casings"]=[c]
    assert buckling(BucklingInput.model_validate(v),GeometryInput.model_validate(raw),p,s,r)["status"]=="withheld"

def test_elastic_envelope_and_large_slope_do_not_return_success():
    assert run(compression_allowance_n=2e6)["status"]=="withheld"
    with pytest.raises(ValueError,match="small-slope"):transfer(1000.,-1e7,10.,math.pi/2,.2,1000.,1.,1.,-1,32)

def test_transfer_grid_refinement_entire_profile_and_uncertainty():
    x=run(bottom_md_m=400.,transfer_model="ideal_helical_axial_drag")
    assert x["status"]=="research_scenario",x["reasons"]
    t=x["load_transfer"];assert t["status"]=="converged"
    assert t["upper_tension_change_n"]<0
    assert t["upper_tension_corner_range_n"][0]<=t["upper_effective_tension_n"]<=t["upper_tension_corner_range_n"][1]
    assert t["final_refinement_change_n"]<=100.

def test_branch_divergence_retains_screen_and_withholds_transfer():
    x=run(transfer_model="ideal_helical_axial_drag",force_basis="supplied_wall_forces",wall_loads=[{"md_m":m,"wall_tension_n":-400000.,"internal_absolute_pa":0.,"external_absolute_pa":0.} for m in (0.,1000.)])
    assert x["profile"]
    assert x["status"]=="incomplete_assessment"
    assert x["load_transfer"]["status"]=="withheld"

def test_profile_interpolation_is_bounded():
    r=[{"md_m":0.,"t":0.},{"md_m":10.,"t":100.}]
    assert interpolate(r,5.,"t")==50
    with pytest.raises(ValueError):interpolate(r,11.,"t")

def test_api_binding_report_restart_and_rejections(api_setup):
    c,p,base,d,store,root=api_setup
    ds=c.post(base+"/imports",data={"kind":"survey"},files={"file":("inclined.csv","md[m],inclination[deg],azimuth[deg]\n0,90,0\n1000,90,0\n","text/csv")}).json()
    d["survey_dataset_id"]=ds["id"];d["casings"]=[]
    rev=c.post(base+"/geometry",json={"geometry":d,"change_note":"M11 horizontal fixture","base_revision_id":None}).json()
    data=c.get(base+"/research/torque-drag/template/"+rev["id"]).json()
    data.update(operation="slackoff",axial_speed_m_s=-.1,bottom_tension_n=-150000.)
    src=c.post(base+"/calculations/torque-drag",json=data).json()
    v=c.get(base+"/research/buckling/template/"+rev["id"]).json()
    v["torque_drag_calculation_id"]=src["id"];v["bottom_md_m"]=400.;v["transfer_model"]="ideal_helical_axial_drag"
    response=c.post(base+"/calculations/buckling",json=v)
    assert response.status_code==200,response.text
    record=response.json();assert record["result"]["status"]=="research_scenario"
    assert record["result"]["torque_drag_sha256"]==digest(canonical(src).encode("utf-8"))
    assert record["result"]["geometry_sha256"]==rev["sha256"]
    snapshot_id=c.post(base+"/reports").json()["id"]
    snapshot=c.get(base+"/reports/"+snapshot_id).json()
    assert record in snapshot["snapshot"]["calculations"]
    assert snapshot["snapshot"]["application_version"]==APP_VERSION
    after=TestClient(create_app(root));after.get("/api/session")
    assert record in after.get(base+"/calculations?model=buckling").json()
    assert after.get(base+"/reports/"+snapshot_id).json()==snapshot
    for patch in ({"torque_drag_calculation_id":"absent"},{"depth_datum":"MSL"},{"bottom_md_m":1001.}):
        assert c.post(base+"/calculations/buckling",json={**v,**patch}).status_code==422
    # Another immutable revision cannot consume this source.
    nextrev=c.post(base+"/geometry",json={"geometry":d,"change_note":"New context","base_revision_id":rev["id"]}).json()
    assert c.post(base+"/calculations/buckling",json={**v,"geometry_revision_id":nextrev["id"]}).status_code==422
    # Source must belong to the requested project, even when datum agrees.
    other=c.post("/api/projects",json={"name":"Other project","well_name":"Other","datum":"RKB","bit_diameter_m":.2,"origin":"synthetic"}).json()
    obase="/api/projects/"+other["id"]
    ods=c.post(obase+"/imports",data={"kind":"survey"},files={"file":("survey.csv","md[m],inclination[deg],azimuth[deg]\n0,90,0\n1000,90,0\n","text/csv")}).json()
    od=copy.deepcopy(d);od["survey_dataset_id"]=ods["id"]
    orev=c.post(obase+"/geometry",json={"geometry":od,"change_note":"Other fixture","base_revision_id":None}).json()
    assert c.post(obase+"/calculations/buckling",json={**v,"geometry_revision_id":orev["id"]}).status_code==422
