import math
import pytest
from pydantic import ValidationError
from fastapi.testclient import TestClient
from packages.engineering.models import SurveyRequest
from packages.engineering.geometry import GeometryInput, Path
from packages.engineering.hydraulics import (HydraulicsInput, hydraulics, flow_gradient, annular_flow, pipe_flow, gauss, integrate)
from packages.engineering.physics import G
from services.api.main import create_app
from test_geometry_casing import api_setup,geom

def request(**patch):
    value={"study_name":"Independent hydraulics fixture","geometry_revision_id":"fixture","depth_datum":"RKB",
           "scenario_at":"2026-01-01T01:00:00Z","maximum_mud_age_hours":24.,
           "mud":{"density_kg_m3":1000.,"rheology":"newtonian","consistency_pa_sn":.01,"flow_index":1.,"yield_stress_pa":0.,
                  "measured_at":"2026-01-01T00:00:00Z","evidence_state":"synthetic","source_note":"Synthetic fluid reference",
                  "test_temperature_c":20.,"density_rheology_basis_note":"Constant isothermal density and viscosity"},
           "circulation_state":"steady_single_phase","flow_regime":"supplied_laminar","applicability_note":"Synthetic stationary concentric fully developed flow",
           "geometry_state":"include_planned_scenario","string_sections":[{"name":"Test string","top_md_m":0.,"bottom_md_m":1000.,"outside_diameter_m":.05,"inside_diameter_m":.04,"source_note":"Synthetic dimensions"}],
           "flow_m3_s":.00001,"surface_backpressure_pa":0.,"surface_loss_pa":100.,
           "surface_loss_note":"Supplied upstream surface equipment loss","nozzle_total_area_m2":.0001,"nozzle_discharge_coefficient":1.,
           "nozzle_source_note":"Synthetic equivalent orifice","rotation_rad_s":0.,"eccentricity_fraction":0.,"cuttings_volume_fraction":0.,"wall_roughness_m":0.,
           "pressure_window":{"reference":"surface_atmospheric_gauge","interpolation":"piecewise_linear_md","evidence_state":"synthetic","source_note":"Synthetic reference bounds","review_note":"Software verification only",
                             "knots":[{"md_m":0.,"pore_gauge_pa":0.,"fracture_gauge_pa":1e6,"pore_upper_allowance_pa":0.,"fracture_lower_allowance_pa":0.},
                                      {"md_m":1000.,"pore_gauge_pa":5e6,"fracture_gauge_pa":15e6,"pore_upper_allowance_pa":0.,"fracture_lower_allowance_pa":0.}]},
           "surface_rating_pa":20e6,"surface_rating_source":"Synthetic surface-system rating",
           "sensitivity":{"density_delta_kg_m3":0.,"flow_delta_m3_s":0.,"consistency_relative_delta":0.,"backpressure_delta_pa":0.}}
    value.update(patch)
    return HydraulicsInput.model_validate(value)

def geometry():
    return GeometryInput.model_validate(geom())

def path(inclination=0.):
    return Path(SurveyRequest(stations=[{"md_m":0.,"inclination_rad":0.,"azimuth_rad":0.},
                                       {"md_m":1000.,"inclination_rad":inclination,"azimuth_rad":0.}]))

def test_gauss_weights_and_polynomial_integrals():
    assert sum(w for x,w in gauss(48))==pytest.approx(2.,abs=1e-14)
    assert integrate(lambda x:x**12,-1.,1.)==pytest.approx(2/13,abs=1e-14)

@pytest.mark.parametrize("radius,mu,q",[(.05,.01,.0001),(.03,.02,.00001),(.1,.001,.001)])
def test_pipe_matches_poiseuille_and_exact_hb_newtonian_limit(radius,mu,q):
    expected=8*mu*q/(math.pi*radius**4)
    result=flow_gradient(q,0.,radius,mu,1.,0.)
    assert result["gradient_pa_m"]==pytest.approx(expected,rel=1e-10)
    assert pipe_flow(expected,radius,mu,1.,0.)==pytest.approx(q,rel=1e-12)

def test_published_newtonian_annulus_case():
    # Nikitin 2022: R2=107.15 mm, R1=57.15 mm, water mu=0.001 Pa.s, Q=0.0005 m3/s.
    # Published gradient rounded to 0.09239 Pa/m. This kernel benchmark is not a profile applicability approval.
    a,b=.05715,.10715
    result=flow_gradient(.0005,a,b,.001,1.,0.)
    expected=8*.001*.0005/(math.pi*(b**4-a**4-(b*b-a*a)**2/math.log(b/a)))
    assert result["gradient_pa_m"]==pytest.approx(expected,rel=1e-10)
    assert result["gradient_pa_m"]==pytest.approx(.09239,abs=5e-6)

@pytest.mark.parametrize("a,b,mu,q",[(.02,.1,.03,.001),(.09,.1,.02,.0001),(.06,.1,.1,.001)])
def test_annular_newtonian_matches_exact_radial_solution(a,b,mu,q):
    expected=8*mu*q/(math.pi*(b**4-a**4-(b*b-a*a)**2/math.log(b/a)))
    r=flow_gradient(q,a,b,mu,1.,0.)
    assert r["gradient_pa_m"]==pytest.approx(expected,rel=3e-9)
    assert abs(r["wall_slip_residual_m_s"])<1e-10

@pytest.mark.parametrize("gradient,radius,mu,ty",[(100.,.05,.1,2.),(1000.,.04,.05,4.),(500.,.03,.2,0.)])
def test_bingham_pipe_matches_buckingham_reiner(gradient,radius,mu,ty):
    wall=gradient*radius/2;ratio=ty/wall
    expected=math.pi*gradient*radius**4/(8*mu)*(1-4*ratio/3+ratio**4/3)
    q=pipe_flow(gradient,radius,mu,1.,ty)
    assert q==pytest.approx(expected,rel=1e-12)
    assert flow_gradient(q,0.,radius,mu,1.,ty)["gradient_pa_m"]==pytest.approx(gradient,rel=1e-10)

@pytest.mark.parametrize("n",[.3,.6,1.,1.5])
def test_powerlaw_pipe_matches_closed_form(n):
    g,r,k=100.,.05,.2
    expected=math.pi*n/(3*n+1)*r**3*(g*r/(2*k))**(1/n)
    assert pipe_flow(g,r,k,n,0.)==pytest.approx(expected,rel=1e-12)

def closed_bingham_annulus(g,a,b,mu,ty):
    """Independent elementary antiderivatives, no production quadrature or rate function."""
    t=2*ty/g
    def zeros(r0):
        rp=(-t+math.sqrt(t*t+4*r0*r0))/2;rn=(t+math.sqrt(t*t+4*r0*r0))/2
        return max(a,min(b,rp)),max(a,min(b,rn))
    def primitive(r,r0,sign):
        return g/(2*mu)*(r0*r0*math.log(r)-r*r/2)-sign*ty/mu*r
    def balance(r0):
        rp,rn=zeros(r0)
        return primitive(rp,r0,1)-primitive(a,r0,1)+primitive(b,r0,-1)-primitive(rn,r0,-1)
    lo,hi=a,b
    for _ in range(70):
        mid=(lo+hi)/2
        if balance(mid)>0:hi=mid
        else:lo=mid
    r0=(lo+hi)/2;rp,rn=zeros(r0)
    def weighted(r,sign):
        return g/(2*mu)*(r0*r0*(b*b*math.log(r)-r*r/2)-(b*b*r*r/2-r**4/4))-sign*ty/mu*(b*b*r-r**3/3)
    return math.pi*(weighted(rp,1)-weighted(a,1)+weighted(b,-1)-weighted(rn,-1))

@pytest.mark.parametrize("g,a,b,mu,ty",[(200.,.06,.1,.1,2.),(500.,.04,.1,.2,5.),(160.,.08,.1,.1,1.)])
def test_bingham_annulus_matches_independent_closed_integrals(g,a,b,mu,ty):
    expected=closed_bingham_annulus(g,a,b,mu,ty)
    q,r0,slip=annular_flow(g,a,b,mu,1.,ty)
    assert q==pytest.approx(expected,rel=2e-10)
    assert abs(slip)<1e-10
    assert flow_gradient(expected,a,b,mu,1.,ty)["gradient_pa_m"]==pytest.approx(g,rel=1e-10)

def independent_hb_trapezoid(g,a,b,k,n,ty,count=6000):
    # Independent dense-grid integration of the velocity profile: balance, integrate velocity, then area.
    h=(b-a)/count
    radii=[a+i*h for i in range(count+1)]
    def shear(r,r0):
        tau=g*.5*(r0*r0/r-r)
        if abs(tau)<=ty:return 0.
        return math.copysign(((abs(tau)-ty)/k)**(1/n),tau)
    def integrate_shear(r0):
        ds=[shear(r,r0) for r in radii]
        return h*(sum(ds[1:-1])+(ds[0]+ds[-1])/2),ds
    lo,hi=a,b
    for _ in range(48):
        mid=(lo+hi)/2
        if integrate_shear(mid)[0]>0:hi=mid
        else:lo=mid
    balance,ds=integrate_shear((lo+hi)/2)
    velocity=[0.]
    for i in range(count):velocity.append(velocity[-1]+h*(ds[i]+ds[i+1])/2)
    return 2*math.pi*h*(sum(velocity[i]*radii[i] for i in range(1,count))+(velocity[-1]*b)/2)

@pytest.mark.parametrize("n,ty",[(.3,5.),(.6,3.),(1.5,2.)])
def test_hb_annulus_independent_velocity_integration_and_refinement(n,ty):
    g,a,b,k=500.,.06,.1,.15
    q=independent_hb_trapezoid(g,a,b,k,n,ty)
    production,r0,slip=annular_flow(g,a,b,k,n,ty,96)
    assert production==pytest.approx(q,rel=2e-6)
    assert flow_gradient(q,a,b,k,n,ty)["gradient_pa_m"]==pytest.approx(g,rel=3e-6)

def test_unyielded_and_zero_flow_limits():
    assert pipe_flow(80.,.05,.1,1.,2.)==0.
    assert annular_flow(100.,.06,.1,.1,.6,2.)[0]==0.
    assert flow_gradient(0.,.06,.1,.1,.6,2.)["gradient_pa_m"]==0.
    result=hydraulics(request(flow_m3_s=0.),geometry(),path())
    nominal=result["nominal"]
    assert nominal["annular_loss_pa"]==nominal["pipe_loss_pa"]==nominal["bit_loss_pa"]==nominal["surface_loss_pa"]==0.
    assert nominal["bottom"]["annular_gauge_pa"]==pytest.approx(1000*G*1000)
    assert result["profile"][0]["equivalent_density_including_backpressure_kg_m3"] is None

def test_profile_analytic_head_losses_circulation_balance_and_mass():
    r=hydraulics(request(),geometry(),path())
    assert r["status"]=="scenario_only" and not r["approval_issued"]
    s=r["nominal"]["segments"][0]
    a,b=.025,.05;mu=.01;q=.00001
    ann=8*mu*q*1000/(math.pi*(b**4-a**4-(b*b-a*a)**2/math.log(b/a)))
    pipe=8*mu*q*1000/(math.pi*.02**4)
    bit=1000*.5*(q/.0001)**2
    assert r["nominal"]["annular_loss_pa"]==pytest.approx(ann,rel=1e-10)
    assert r["nominal"]["pipe_loss_pa"]==pytest.approx(pipe,rel=1e-10)
    assert r["nominal"]["required_supply_gauge_pa"]==pytest.approx(ann+pipe+bit+100.)
    assert r["nominal"]["standpipe_gauge_pa"]==pytest.approx(ann+pipe+bit)
    assert r["nominal"]["bottom"]["annular_gauge_pa"]==pytest.approx(1000*G*1000+ann)
    assert abs(r["nominal"]["bottom_path_balance_residual_pa"])<1e-7
    assert r["nominal"]["mass_in_kg_s"]==r["nominal"]["mass_out_kg_s"]==.01

def test_curved_head_uses_tvd_and_interior_violation_is_found_exactly():
    v=request(flow_m3_s=0.).model_dump()
    v["pressure_window"]["knots"][-1].update(pore_gauge_pa=1e6,fracture_gauge_pa=7e6)
    r=hydraulics(HydraulicsInput.model_validate(v),geometry(),path(math.pi/2))
    expected_md=1000/(math.pi/2)*math.acos(6000/(1000*G))
    upper=r["nominal"]["minimum_below_fracture"]
    assert upper["md_m"]==pytest.approx(expected_md,abs=1e-7)
    assert upper["below_fracture_allowance_pa"]<0
    assert r["profile"][0]["below_fracture_allowance_pa"]>0
    assert r["profile"][-1]["below_fracture_allowance_pa"]>0
    assert r["nominal"]["bottom"]["tvd_m"]==pytest.approx(2000/math.pi)
    assert not r["within_all_tested_bounds"]

def test_piecewise_geometry_sensitivity_and_equipment_rating():
    v=request().model_dump()
    v["string_sections"]=[{"name":"Upper","top_md_m":0.,"bottom_md_m":400.,"outside_diameter_m":.05,"inside_diameter_m":.04,"source_note":"Upper fixture"},
                          {"name":"Lower","top_md_m":400.,"bottom_md_m":1000.,"outside_diameter_m":.06,"inside_diameter_m":.045,"source_note":"Lower fixture"}]
    v["surface_backpressure_pa"]=10000.;v["sensitivity"].update(density_delta_kg_m3=50.,flow_delta_m3_s=.000002,consistency_relative_delta=.1,backpressure_delta_pa=1000.)
    v["surface_rating_pa"]=1.
    r=hydraulics(HydraulicsInput.model_validate(v),geometry(),path())
    assert r["sensitivity"]["tested_admissible_corners"]==16
    assert not r["sensitivity"]["tested_withheld_corners"]
    assert len(r["nominal"]["segments"])==2
    assert any(p["md_m"]==400. for p in r["profile"])
    assert r["surface_equipment"]["margin_pa"]<0 and not r["within_all_tested_bounds"]
    assert all(p["tested_min_gauge_pa"]<=p["tested_max_gauge_pa"] for p in r["profile"])

@pytest.mark.parametrize("field,setting",[
    ("circulation_state","transient"),("circulation_state","multiphase"),("circulation_state","losses"),
    ("circulation_state","unknown"),("flow_regime","unknown"),("flow_regime","turbulent"),
    ("rotation_rad_s",1.),("eccentricity_fraction",.1),("wall_roughness_m",.01)])
def test_unsupported_states_withhold(field,setting):
    r=hydraulics(request(**{field:setting}),geometry(),path())
    assert r["status"]=="withheld" and r["nominal"] is None and not r["profile"]

def test_mud_age_future_evidence_units_and_window_review_gates():
    v=request().model_dump();v["mud"]["measured_at"]="2026-01-01T07:00:00+07:00"
    r=hydraulics(HydraulicsInput.model_validate(v),geometry(),path());assert r["mud_age_hours"]==1.
    for patch in ({"maximum_mud_age_hours":.5},{"scenario_at":"2025-12-31T23:00:00Z"}):
        assert hydraulics(request(**patch),geometry(),path())["status"]=="withheld"
    for which in ("mud","pressure_window"):
        v=request().model_dump();v[which]["evidence_state"]="unknown" if which=="mud" else "unreviewed"
        assert hydraulics(HydraulicsInput.model_validate(v),geometry(),path())["status"]=="withheld"

def test_planned_and_installed_casing_geometry_are_separate():
    r=hydraulics(request(geometry_state="installed_only"),geometry(),path())
    assert r["nominal"]["segments"][0]["bore_diameter_m"]==.3
    r=hydraulics(request(),geometry(),path())
    assert r["nominal"]["segments"][0]["bore_diameter_m"]==.1
    assert "[planned]" in r["nominal"]["segments"][0]["bore_source"]

def test_reynolds_and_failed_sensitivity_corners_are_explicit():
    r=hydraulics(request(flow_m3_s=.01),geometry(),path())
    assert r["status"]=="withheld" and "Reynolds" in r["reasons"][0]
    v=request(flow_m3_s=.0002).model_dump();v["sensitivity"]["flow_delta_m3_s"]=.0002
    r=hydraulics(HydraulicsInput.model_validate(v),geometry(),path())
    assert r["nominal"] is not None and r["status"]=="incomplete_assessment"
    assert len(r["sensitivity"]["tested_withheld_corners"])>0 and not r["within_all_tested_bounds"]

def test_no_rating_or_overlapping_pressure_allowances_prevents_clearance():
    r=hydraulics(request(surface_rating_pa=None,surface_rating_source=None),geometry(),path())
    assert r["status"]=="incomplete_assessment" and not r["within_all_tested_bounds"]
    v=request().model_dump();v["pressure_window"]["knots"][0]["pore_upper_allowance_pa"]=2e6
    r=hydraulics(HydraulicsInput.model_validate(v),geometry(),path())
    assert r["sensitivity"]["minimum_above_pore"]["margin_pa"]<0 and not r["within_all_tested_bounds"]

@pytest.mark.parametrize("patch",[
    {"scenario_at":"2026-01-01T01:00:00"},
    {"flow_m3_s":-.1},{"surface_rating_pa":1.,"surface_rating_source":None},
    {"string_sections":[]},{"nozzle_total_area_m2":0.},
    {"depth_datum":""},
])
def test_invalid_input_contracts_rejected(patch):
    with pytest.raises(ValidationError):request(**patch)

def test_invalid_laws_depth_coverage_and_sensitivity_contracts():
    for sub,field,val in [("mud","flow_index",.6),("mud","density_kg_m3",float("nan")),("sensitivity","flow_delta_m3_s",.001),("sensitivity","backpressure_delta_pa",1.)]:
        v=request().model_dump();v[sub][field]=val
        with pytest.raises(ValidationError):HydraulicsInput.model_validate(v)
    v=request().model_dump();v["pressure_window"]["knots"][-1]["md_m"]=900.
    with pytest.raises(ValidationError):HydraulicsInput.model_validate(v)

def test_api_revision_source_integrity_saved_report_restart_and_project_isolation(api_setup):
    c,p,base,d,store,root=api_setup
    revision=c.post(base+"/geometry",json={"geometry":d,"change_note":"Hydraulic context"}).json()
    value=request(geometry_revision_id=revision["id"]).model_dump()
    response=c.post(base+"/calculations/hydraulics",json=value)
    assert response.status_code==200,response.text
    saved=response.json()
    assert saved["result"]["geometry_sha256"]==revision["sha256"]
    assert saved["result"]["survey_source_sha256"]==revision["result"]["survey_source_sha256"]
    report=c.post(base+"/reports").json();snapshot=c.get(base+"/reports/"+report["id"]).json()
    assert saved in snapshot["snapshot"]["calculations"]
    after=TestClient(create_app(root));after.get("/api/session")
    assert after.get(base+"/calculations?model=hydraulics").json()==[saved]
    assert c.post(base+"/calculations/hydraulics",json={**value,"depth_datum":"MSL"}).status_code==422
    other=c.post("/api/projects",json={"name":"Other","well_name":"Other","datum":"RKB","origin":"historical","bit_diameter_m":.2}).json()
    assert c.post("/api/projects/"+other["id"]+"/calculations/hydraulics",json=value).status_code==404
    source=c.get(base+"/datasets/"+d["survey_dataset_id"]).json()
    (root/"raw"/source["source_hash"]).write_bytes(b"changed")
    assert c.post(base+"/calculations/hydraulics",json=value).status_code==422
    assert c.get(base+"/reports/"+report["id"]).json()==snapshot

def test_tiny_positive_flow_is_withheld_without_rounding_to_static():
    r=hydraulics(request(flow_m3_s=1e-12),geometry(),path())
    assert r["status"]=="withheld" and "resolution" in r["reasons"][0]

def test_horizontal_head_stays_constant_while_md_friction_accumulates():
    p=Path(SurveyRequest(stations=[{"md_m":0.,"inclination_rad":math.pi/2,"azimuth_rad":0.},
                                  {"md_m":1000.,"inclination_rad":math.pi/2,"azimuth_rad":0.}]))
    r=hydraulics(request(surface_backpressure_pa=10000.),geometry(),p)
    bottom=r["nominal"]["bottom"]
    assert bottom["hydrostatic_pa"]==pytest.approx(0.,abs=1e-6)
    assert bottom["annular_gauge_pa"]==pytest.approx(10000.+r["nominal"]["annular_loss_pa"])
    assert bottom["equivalent_density_including_backpressure_kg_m3"] is None

def test_incomplete_hole_coverage_and_above_datum_path_withhold():
    g=geometry().model_dump();g["casings"]=[]
    g["hole_sections"][0]["bottom_md_m"]=900.
    assert hydraulics(request(),GeometryInput.model_validate(g),path())["status"]=="withheld"
    p=Path(SurveyRequest(stations=[{"md_m":0.,"inclination_rad":math.pi,"azimuth_rad":0.},
                                  {"md_m":1000.,"inclination_rad":math.pi,"azimuth_rad":0.}]))
    r=hydraulics(request(),geometry(),p)
    assert r["status"]=="withheld" and "above" in r["reasons"][0]

def test_api_synthetic_example_and_historical_evidence_boundary(api_setup):
    c,p,base,d,store,root=api_setup
    revision=c.post(base+"/geometry",json={"geometry":d,"change_note":"Example context"}).json()
    example=c.get(base+"/examples/hydraulics/"+revision["id"])
    assert example.status_code==200
    assert HydraulicsInput.model_validate(example.json()).mud.evidence_state=="synthetic"
    h=c.post("/api/projects",json={"name":"History","well_name":"History","datum":"RKB","origin":"historical","bit_diameter_m":.2}).json()
    other="/api/projects/"+h["id"]
    ds=c.post(other+"/imports",data={"kind":"survey"},files={"file":("h.csv","md[m],inclination[deg],azimuth[deg]\n0,0,0\n1000,0,0\n","text/csv")}).json()
    geometry_input={**d,"survey_dataset_id":ds["id"]}
    gr=c.post(other+"/geometry",json={"geometry":geometry_input,"change_note":"Historical scenario"}).json()
    assert c.get(other+"/examples/hydraulics/"+gr["id"]).status_code==422
    assert c.post(other+"/calculations/hydraulics",json=request(geometry_revision_id=gr["id"]).model_dump()).status_code==422

def test_consistency_sensitivity_must_remain_in_the_declared_envelope():
    v=request().model_dump();v["mud"]["consistency_pa_sn"]=100.;v["sensitivity"]["consistency_relative_delta"]=.5
    with pytest.raises(ValidationError):HydraulicsInput.model_validate(v)

def test_cuttings_transport_and_surge_margins():
    v = request(flow_m3_s=0.0001, cuttings_volume_fraction=0.05, surge_margin_pa=1000., swab_margin_pa=500., flow_regime="laminar_transition").model_dump()
    v["string_sections"][0]["outside_diameter_m"] = 0.05
    v["string_sections"][0]["inside_diameter_m"] = 0.04
    # Ensure velocity is small to trigger critical velocity reason
    r = hydraulics(HydraulicsInput.model_validate(v), geometry(), path(inclination=math.pi/4))
    
    assert r["status"] == "scenario_only"
    assert "Annular velocity is below critical carrying velocity in at least one segment." in r["reasons"]
    
    # check rho_eff logic
    # clean mud rho is 1000, cuttings is 2600. effective rho = 1000 + 0.05 * 1600 = 1080
    assert r["nominal"]["mass_in_kg_s"] == pytest.approx(1080.0 * 0.0001)
    
    # Check segment metrics
    s = r["nominal"]["segments"][0]
    assert s["critical_carrying_velocity_m_s"] > 0.5
    assert s["dynamic_bed_height_m"] > 0
    assert s["effective_cuttings_loading"] > 0.05
    
    # Check ECD with surge/swab
    assert r["profile"][-1]["equivalent_density_including_surge_kg_m3"] > r["profile"][-1]["equivalent_density_including_backpressure_kg_m3"]
    assert r["profile"][-1]["equivalent_density_including_swab_kg_m3"] < r["profile"][-1]["equivalent_density_including_backpressure_kg_m3"]

def test_laminar_transition_allowed():
    v = request(flow_regime="laminar_transition").model_dump()
    r = hydraulics(HydraulicsInput.model_validate(v), geometry(), path())
    assert r["status"] == "scenario_only"
