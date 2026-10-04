
import math,copy,json
import pytest
from pydantic import ValidationError
from fastapi.testclient import TestClient
from packages.engineering.stability import StabilityInput,stability,wall_stress,tangent
from packages.engineering.transport import TransportInput,transport,tanks
from packages.engineering.surge_swab import SurgeInput,surge,acoustic,MotionKnot
from packages.engineering.torque_drag import TorqueDragInput,torque_drag,drag_case
from packages.engineering.physics import G
from packages.engineering.hydraulics import hydraulics
from services.api import demo
from services.api.main import create_app
from test_hydraulics import request,geometry,path
from test_geometry_casing import api_setup

def template(model):
    return demo.research_template(model,{"id":"fixture","input":geometry().model_dump(),"result":{"total_depth_md_m":1000.}},"synthetic")

def st(**change):
    v=template("stability");v.update(change);return StabilityInput.model_validate(v)

def tr(**change):
    v=template("transport");v["hydraulics_calculation_id"]="fixture";v.update(change);return TransportInput.model_validate(v)

def su(**change):
    v=template("surge-swab");v["hydraulics_calculation_id"]="fixture";v.update(change);return SurgeInput.model_validate(v)

def td(**change):
    v=template("torque-drag");v["string_sections"][0].update(outside_diameter_m=.05,inside_diameter_m=.04)
    v.update(change);return TorqueDragInput.model_validate(v)

def hydraulic():
    h=request();return h,hydraulics(h,geometry(),path())

def test_kirsch_published_wall_extrema():
    # Espinoza: SH=22 MPa, Sh=13 MPa, Pw=Pp=10 MPa -> hoop 15 +/- 18 MPa.
    r=stability(st(thermal_scope="none",delta_temperature_k=0.),path())
    assert min(x["hoop_effective_pa"] for x in r["profile"])==pytest.approx(-3e6)
    assert max(x["hoop_effective_pa"] for x in r["profile"])==pytest.approx(33e6)
    assert r["failure_screen_exceeded"] is True
    assert r["angular_refinement_change_pa"]["tensile_margin_pa"]<1e-8

@pytest.mark.parametrize("delta",[-50.,0.,50.])
def test_thermal_sign_and_exact_restrained_estimate(delta):
    r=stability(st(delta_temperature_k=delta),path())
    assert r["thermal_stress_estimate_pa"]==pytest.approx(20e9*1e-5*delta/.75)

def test_rotated_isotropic_tensor_invariant():
    v=st(stress_north_pa=20e6,stress_east_pa=20e6,stress_vertical_pa=20e6,delta_temperature_k=0.)
    a=stability(v,path());b=stability(v,path(math.pi/2))
    assert [x["hoop_effective_pa"] for x in a["profile"]]==pytest.approx([x["hoop_effective_pa"] for x in b["profile"]],abs=1e-7)

def test_wall_shear_principal_invariants():
    s=[[10.,2.,3.],[2.,20.,4.],[3.,4.,30.]]
    h,z,t,p=wall_stress(s,5.,.25,-1.,.7)
    assert sum(p)==pytest.approx(5+h+z)
    assert p[0]<=5<=p[2]
    assert (p[1]*p[2] if p[0]==5 else p[0]*p[1] if p[2]==5 else p[0]*p[2])==pytest.approx(h*z-t*t)

@pytest.mark.parametrize("model",["anisotropic","coupled_poroelastic","plastic"])
def test_unsupported_stability(model):
    r=stability(st(model=model),path());assert r["status"]=="withheld";assert r["profile"]==[]

@pytest.mark.parametrize("patch",[{"stress_ne_pa":1e9},{"poisson_ratio":.5},{"thermal_scope":"none"},
                                  {"external_bounds_state":"externally_approved"},{"md_m":math.nan}])
def test_stability_contract_rejects_invalid(patch):
    with pytest.raises(ValidationError):st(**patch)

def test_external_bounds_are_not_model_approval():
    r=stability(st(external_bounds_state="externally_approved",external_lower_pa=1e6,external_upper_pa=30e6,external_bounds_note="Externally supplied fixture"),path())
    assert r["external_bounds"]["approval_verified"] is False
    assert r["approval_issued"] is False

def test_tank_closed_form_backward_euler_and_conservation():
    r=tanks([2.],[.2],.01,10.,10.,0.,1.)
    expected=.01/.2*(1-(1/1.2)**10)
    assert r["inventory_m3"]==pytest.approx(expected)
    assert r["balance_residual_m3"]==pytest.approx(0.,abs=1e-15)

def test_zero_transport_generation_and_zero_rates():
    r=tanks([2.,3.],[0.,0.],0.,20.,10.,.01,1.)
    assert r["returned_m3"]==0;assert r["inventory_m3"]==pytest.approx(.05)
    r=tanks([2.,3.],[0.,0.],.01,20.,3.5,0.,1.)
    assert r["generated_m3"]==pytest.approx(.035)
    assert r["inventory_m3"]==pytest.approx(.035)

def test_transport_stokes_and_mass_balance():
    h,r=hydraulic();v=tr(rop_m_s=1e-7)
    x=transport(v,geometry(),path(),h.model_dump(),r)
    expected=(2600-1000)*G*.0001**2/(18*.01)
    assert x["settling_velocity_m_s"]==pytest.approx(expected)
    assert abs(x["balance_residual_m3"])<1e-12
    assert x["status"]=="research_scenario"
    assert x["profile"][0]["fluid_velocity_m_s"]==pytest.approx(h.flow_m3_s/(math.pi*(.1**2-.05**2)/4))

@pytest.mark.parametrize("patch",[{"shape":"irregular"},{"rotation_rad_s":1.},{"particle_diameter_m":.01},{"evidence_state":"unknown"}])
def test_transport_gates(patch):
    h,r=hydraulic();x=transport(tr(**patch),geometry(),path(),h.model_dump(),r)
    assert x["status"]=="withheld";assert x["history"]==[]

def test_transport_inclination_and_nonnewtonian_gates():
    h,r=hydraulic()
    assert transport(tr(),geometry(),path(.6),h.model_dump(),r)["status"]=="withheld"
    data=h.model_dump();data["mud"].update(rheology="bingham",yield_stress_pa=1.)
    assert transport(tr(),geometry(),path(),data,r)["status"]=="withheld"

def test_transport_concentration_crossing_is_not_cleaning_approval():
    h,r=hydraulic();x=transport(tr(rop_m_s=.01),geometry(),path(),h.model_dump(),r)
    assert x["status"]=="outside_dilute_envelope";assert x["peak_volume_fraction"]>.05

def test_acoustic_static_exact_zero():
    motion=[MotionKnot(time_s=0.,downward_speed_m_s=0.),MotionKnot(time_s=2.,downward_speed_m_s=0.)]
    r=acoustic(1000.,.01,.002,1000.,1000.,0.,motion,40)
    assert all(x==0 for x in r["final"])
    assert r["maximum_mass_balance_residual_kg"]==0.

def test_acoustic_joukowsky_before_reflection_and_conserved_storage():
    # Ramp to constant velocity; before wave reaches open top p = rho*c*u at bottom.
    motion=[MotionKnot(time_s=0.,downward_speed_m_s=0.),MotionKnot(time_s=.05,downward_speed_m_s=.1),MotionKnot(time_s=.5,downward_speed_m_s=.1)]
    r=acoustic(1000.,.01,.002,1000.,1000.,0.,motion,160)
    assert r["final"][0]==pytest.approx(1000*1000*.02,rel=.015)
    assert r["maximum_mass_balance_residual_kg"]<1e-10
    assert r["cfl"]<=.45

def test_acoustic_motion_sign_symmetry():
    motion=[MotionKnot(time_s=0.,downward_speed_m_s=0.),MotionKnot(time_s=1.,downward_speed_m_s=.02),MotionKnot(time_s=3.,downward_speed_m_s=.02)]
    a=acoustic(500.,.01,.003,1200.,800.,.1,motion,40)
    b=acoustic(500.,.01,.003,1200.,800.,.1,[k.model_copy(update={"downward_speed_m_s":-k.downward_speed_m_s}) for k in motion],40)
    assert a["maximum"]==pytest.approx([-x for x in b["minimum"]])
    assert a["minimum"]==pytest.approx([-x for x in b["maximum"]])

def test_surge_refinement_whole_history_pressure_margins():
    h,r=hydraulic();x=surge(su(),geometry(),path(),h.model_dump(),r)
    assert len(x["profile"])==80
    assert x["grid_cells"]==[20,40,80]
    assert len(x["refinement_changes_pa"])==2
    assert x["maximum_mass_balance_residual_kg"]<1e-8
    assert x["minimum_lower_margin"] in x["profile"]

@pytest.mark.parametrize("patch",[{"evidence_state":"unknown"},{"motion":[{"time_s":0.,"downward_speed_m_s":0.},{"time_s":100.,"downward_speed_m_s":1.}]}])
def test_surge_evidence_and_motion_envelope(patch):
    h,r=hydraulic();x=surge(su(**patch),geometry(),path(),h.model_dump(),r)
    assert x["status"]=="withheld"

@pytest.mark.parametrize("operation,speed,rotation",[("pickup",.1,0.),("slackoff",-.1,0.),("rotating",0.,2.),("combined",.1,2.)])
def test_vertical_soft_string_exact_buoyant_weight(operation,speed,rotation):
    v=td(operation=operation,axial_speed_m_s=speed,rotation_rad_s=rotation)
    x=torque_drag(v,geometry(),path())
    s=v.string_sections[0];expected=(7850-1200)*G*math.pi*(s.outside_diameter_m**2-s.inside_diameter_m**2)/4*1000
    assert x["hookload_n"]==pytest.approx(expected,rel=1e-10)
    assert x["surface_torque_nm"]==0.
    assert x["summed_normal_force_n"]==0.

def test_inclined_straight_string_gravity_friction():
    # Constant 60-degree inclination, no curvature.
    from packages.engineering.geometry import Path
    from packages.engineering.models import SurveyRequest
    p=Path(SurveyRequest(stations=[{"md_m":0.,"inclination_rad":math.pi/3,"azimuth_rad":0.},{"md_m":1000.,"inclination_rad":math.pi/3,"azimuth_rad":0.}]))
    v=td();x=torque_drag(v,geometry(),p)
    s=v.string_sections[0];weight=(7850-1200)*G*math.pi*(.05**2-.04**2)/4*1000
    assert x["hookload_n"]==pytest.approx(weight*(.5+.2*math.sin(math.pi/3)),rel=1e-10)
    y=torque_drag(td(operation="slackoff",axial_speed_m_s=-.1),geometry(),p)
    assert y["hookload_n"]==pytest.approx(weight*(.5-.2*math.sin(math.pi/3)),rel=1e-10)
    z=torque_drag(td(operation="rotating",axial_speed_m_s=0.,rotation_rad_s=2.),geometry(),p)
    assert z["surface_torque_nm"]==pytest.approx(.2*weight*math.sin(math.pi/3)*.025)

def test_soft_string_sensitivity_residual_and_compression():
    x=torque_drag(td(bottom_tension_n=-1e5,observed_hookload_n=0.,observation_note="Synthetic sensor reference"),geometry(),path(.5))
    assert x["minimum_tension_n"]<0
    assert x["hookload_residual_n"]==pytest.approx(-x["hookload_n"])
    assert x["calibration_performed"] is False
    assert any("Compression" in r for r in x["reasons"])

@pytest.mark.parametrize("patch",[{"operation":"pickup","axial_speed_m_s":0.},{"operation":"slackoff"},
                                  {"surface_tension_limit_n":1e6},{"observed_hookload_n":1e5},{"friction_delta":.5}])
def test_drag_contract_invalid(patch):
    with pytest.raises(ValidationError):td(**patch)

def test_research_api_persistence_source_binding_report_and_restart(api_setup):
    c,p,base,d,store,root=api_setup
    rev=c.post(base+"/geometry",json={"geometry":d,"change_note":"Research fixture","base_revision_id":None}).json()
    schemas=c.get("/api/research/schemas").json();assert set(schemas)=={"stability","transport","surge-swab","torque-drag","buckling","dynamics","bit-condition","wear-fatigue","anomaly","gas-phase","supervision"}
    source=c.post(base+"/research/source-hydraulics/"+rev["id"]);assert source.status_code==201,source.text
    source=source.json();records=[]
    for model in ["stability","transport","surge-swab","torque-drag","buckling"]:
        data=c.get(base+"/research/"+model+"/template/"+rev["id"]).json()
        if "hydraulics_calculation_id" in data:data["hydraulics_calculation_id"]=source["id"]
        if "torque_drag_calculation_id" in data:data["torque_drag_calculation_id"]=next(r["id"] for r in records if r["model"]=="torque-drag")
        saved=c.post(base+"/calculations/"+model,json=data);assert saved.status_code==200,saved.text
        saved=saved.json();records.append(saved)
        assert saved["result"]["geometry_sha256"]==rev["sha256"]
        assert saved["result"]["approval_issued"] is False
        if "hydraulics_calculation_id" in data:assert len(saved["result"]["hydraulics_sha256"])==64
    report=c.post(base+"/reports").json();snapshot=c.get(base+"/reports/"+report["id"]).json()
    for rec in records:assert rec in snapshot["snapshot"]["calculations"]
    after=TestClient(create_app(root));after.get("/api/session")
    for rec in records:assert rec in after.get(base+"/calculations?model="+rec["model"]).json()
    data=c.get(base+"/research/transport/template/"+rev["id"]).json()
    data["hydraulics_calculation_id"]="absent"
    assert c.post(base+"/calculations/transport",json=data).status_code==422
    data["hydraulics_calculation_id"]=source["id"];data["depth_datum"]="MSL"
    assert c.post(base+"/calculations/transport",json=data).status_code==422
    other=c.post(base+"/geometry",json={"geometry":d,"change_note":"Next revision","base_revision_id":rev["id"]}).json()
    data["depth_datum"]=p["datum"];data["geometry_revision_id"]=other["id"]
    assert c.post(base+"/calculations/transport",json=data).status_code==422

def test_zero_friction_curved_string_matches_tvd_weight_and_refines():
    v=td();sections=[s.model_dump() for s in v.string_sections];sections[0]["friction_coefficient"]=0.
    v=td(string_sections=sections,friction_delta=0.,step_m=20.)
    p=path(math.pi/2);x=torque_drag(v,geometry(),p)
    w=(7850-1200)*G*math.pi*(.05**2-.04**2)/4
    assert x["hookload_n"]==pytest.approx(w*p.at(1000.)["tvd_m"],rel=2e-5)
    assert x["step_refinement_hookload_change_n"]<2.

def test_soft_string_supplied_limits_exceeded_explicitly():
    x=torque_drag(td(surface_tension_limit_n=1.,surface_torque_limit_nm=1.,rating_note="Synthetic restricted limit"),geometry(),path())
    assert x["surface_tension_margin_n"]<0
    assert any("exceeds" in r for r in x["reasons"])

def test_stability_strength_exceeded_has_visible_reason():
    x=stability(st(),path())
    assert x["failure_screen_exceeded"]
    assert any("strength screen exceeded" in r for r in x["reasons"])

def test_transient_small_tolerance_is_incomplete_not_approved():
    h,r=hydraulic();x=surge(su(convergence_tolerance_pa=.001),geometry(),path(),h.model_dump(),r)
    assert x["status"]=="incomplete_assessment"
    assert x["numerical_tolerance_met"] is False
    assert any("refinement" in s for s in x["reasons"])

def test_transient_pause_contains_reflected_response():
    h,r=hydraulic();x=surge(su(),geometry(),path(),h.model_dump(),r)
    # Pressure persists after pipe velocity stops; it is not a static speed lookup.
    tail=[p for p in x["history"] if p["time_s"]>8.]
    assert tail and any(abs(p["bottom_perturbation_pa"])>1 for p in tail)

def test_nonuniform_annulus_transient_withheld():
    h,r=hydraulic();g=geometry()
    holes=[s.model_dump() for s in g.hole_sections]
    holes[0]["bottom_md_m"]=500.
    holes.append({**holes[0],"name":"Transition","top_md_m":500.,"bottom_md_m":1000.,"diameter_m":.2})
    g=g.model_copy(update={"hole_sections":[type(g.hole_sections[0]).model_validate(s) for s in holes],"casings":[]})
    x=surge(su(),g,path(),h.model_dump(),r)
    assert x["status"]=="withheld";assert any("diameter transitions" in s for s in x["reasons"])

def test_work_limits_are_bounded():
    with pytest.raises(ValueError):tanks([1.]*1000,[.01]*1000,.01,10000.,10000.,0.,1.)
    motion=[MotionKnot(time_s=0.,downward_speed_m_s=0.),MotionKnot(time_s=600.,downward_speed_m_s=0.)]
    with pytest.raises(ValueError):acoustic(10.,.01,.002,1000.,1000.,0.,motion,160)

def test_research_source_project_ownership_and_raw_integrity(api_setup):
    c,p,base,d,store,root=api_setup
    rev=c.post(base+"/geometry",json={"geometry":d,"change_note":"Source validation fixture","base_revision_id":None}).json()
    src=c.post(base+"/research/source-hydraulics/"+rev["id"]).json()
    other=c.post("/api/projects",json={"name":"Other project","well_name":"Other","datum":"RKB","bit_diameter_m":.2,"origin":"synthetic"}).json()
    data=c.get(base+"/research/transport/template/"+rev["id"]).json()
    data["hydraulics_calculation_id"]=src["id"]
    assert c.post("/api/projects/"+other["id"]+"/calculations/transport",json=data).status_code==404
    raw=store.root/"raw"/rev["result"]["survey_source_sha256"];raw.write_bytes(b"changed")
    assert c.post(base+"/calculations/transport",json=data).status_code==422
