"""Independent numerical cases and connected geomechanics evidence workflow."""
import copy, hashlib, json, math
import numpy as np
import pytest
from fastapi.testclient import TestClient
from packages.engineering.geomechanics import (GeomechanicsInput, TriaxialCoreTest,
    calculate_geomechanics, failure_margins, downhole_fluid_density, pressure_intervals, wall_profile)
from packages.engineering.geometry import Path
from packages.engineering.models import SurveyRequest
from packages.engineering.physics import G
from services.api import demo, auth
from services.api.main import create_app
from services.api.storage import Store, canonical, digest
from test_geometry_casing import api_setup

def survey(inc=0.,azi=0.):
    return Path(SurveyRequest(stations=[{"md_m":0.,"inclination_rad":inc,"azimuth_rad":azi},
                                       {"md_m":1000.,"inclination_rad":inc,"azimuth_rad":azi}]))

def payload(path=None):
    p=path or survey()
    draft=demo.research_template("geomechanics",{"id":"fixture","input":{"datum":"RKB"},
                "result":{"total_depth_md_m":1000.,"samples":[p.at(1000.)]}},"synthetic")
    return GeomechanicsInput.model_validate(draft)

def test_mogi_matches_analytic_triaxial_boundary_and_uses_intermediate_stress():
    core=payload().core_test;phi=math.radians(core.friction_angle_deg)
    ucs=2*core.cohesion_pa*math.cos(phi)/(1-math.sin(phi));q=(1+math.sin(phi))/(1-math.sin(phi))
    s3=10e6;s1=ucs+q*s3
    for model in ("mohr_coulomb","mogi_coulomb"):
        margin,_=failure_margins([[s3,s3,s1]],core,model)
        assert margin[0]==pytest.approx(0,abs=1e-7)
    a,_=failure_margins([[s3,s3,s1]],core,"mogi_coulomb")
    b,_=failure_margins([[s3,(s3+s1)/2,s1]],core,"mogi_coulomb")
    assert b[0]>a[0]+1e6
    mc,_=failure_margins([[s3,(s3+s1)/2,s1]],core,"mohr_coulomb")
    assert mc[0]==pytest.approx(0,abs=1e-7)

def test_vertical_pressure_roots_match_independent_principal_stress_algebra():
    core=payload().core_test.model_copy(update={"biot_coefficient":1.,"poissons_ratio":.25})
    tensor=np.diag([50e6,30e6,60e6]);pp=20e6;ucs=core.unconfined_compressive_strength_pa
    # At theta=90: sigma1=120MPa-support, sigma3=support; at theta=0 upper
    # boundary: sigma1=50MPa, sigma3=40MPa-support. q=3.
    lower=pp+(120e6-ucs)/4;upper=pp+(ucs+70e6)/3
    r=pressure_intervals(tensor,pp,core,"mohr_coulomb",2500.,.8,3.5,1440,161)
    assert len(r)==1
    assert r[0]["lower_gauge_pa"]==pytest.approx(lower,abs=1)
    assert r[0]["upper_gauge_pa"]==pytest.approx(upper,abs=1)
    assert not r[0]["lower_at_test_boundary"] and not r[0]["upper_at_test_boundary"]

def test_fluid_hydrostatic_integral_matches_independent_rk4_and_zero_coefficients():
    rho0=1500.;grad=.03;c=4e-10;alpha=6e-4;depth=3000.
    h=depth/12000;p=0.
    def rhs(z,p):return rho0*G*(1+c*p-alpha*grad*z)
    for i in range(12000):
        z=i*h;k1=rhs(z,p);k2=rhs(z+h/2,p+h*k1/2);k3=rhs(z+h/2,p+h*k2/2);k4=rhs(z+h,p+h*k3)
        p+=h*(k1+2*k2+2*k3+k4)/6
    r=downhole_fluid_density(1.5,depth,15.,3.,c,alpha)
    assert r["downhole_gauge_pressure_pa"]==pytest.approx(p,rel=1e-11)
    assert r["downhole_density_kg_m3"]==pytest.approx(rho0*(1+c*p-alpha*grad*depth),rel=1e-11)
    z=downhole_fluid_density(1.5,depth,15.,3.,0.,0.)
    assert z["downhole_gauge_pressure_pa"]==pytest.approx(rho0*G*depth)
    assert z["downhole_density_kg_m3"]==1500.

def test_density_outside_declared_range_is_withheld_without_clipping():
    r=downhole_fluid_density(1.5,15000.,15.,10.,2e-9,.002)
    assert r["status"]=="outside_applicability"
    assert r["downhole_density_kg_m3"] is None and r["downhole_gauge_pressure_pa"] is None

def test_survey_orientation_rotates_tensor_and_wall_eigenvalues():
    p=survey(math.pi/3,math.pi/4);v=payload(p)
    r=calculate_geomechanics(v,path=p)
    assert r["status"] in ("research_scenario","nonconverged")
    assert r["inclination_deg"]==pytest.approx(60) and r["azimuth_deg"]==pytest.approx(45)
    axes=np.array(r["local_axes_north_east_down"]);local=np.array(r["local_effective_tensor_pa"])
    assert axes@axes.T==pytest.approx(np.eye(3),abs=1e-14)
    s=r["in_situ_stresses"]
    assert np.linalg.eigvalsh(local)==pytest.approx(sorted([s["effective_sv_pa"],s["effective_sh_pa"],s["effective_sH_pa"]]))
    assert any(abs(row["wall_shear_pa"])>1e5 for row in r["profile"])
    core=v.core_test;row=r["profile"][17]
    matrix=np.array([[row["hoop_effective_pa"],row["wall_shear_pa"],0],
                     [row["wall_shear_pa"],row["axial_effective_pa"],0],
                     [0,0,r["supplied_mud_pressure_gauge_pa"]-core.biot_coefficient*s["pore_pressure_pp_pa"]]])
    assert np.linalg.eigvalsh(matrix)==pytest.approx([row[k] for k in ("minimum_principal_pa","intermediate_principal_pa","maximum_principal_pa")])

@pytest.mark.parametrize("patch,reason",[
    ({"evidence_state":"unknown"},"unknown"),({"core_test":None},"Core properties"),
    ({"stress_calibration":None},"Stress calibration"),({"tectonic_strain_y":0.},"inconsistent ordering")])
def test_missing_or_conflicting_evidence_withholds(patch,reason):
    v=payload().model_copy(update=patch);r=calculate_geomechanics(v,path=survey())
    assert r["status"]=="withheld" and r["stability_window"] is None
    assert any(reason in x for x in r["reasons"])

@pytest.mark.parametrize("patch,reason",[
    ({"calibration_quality":"unverified"},"closure-pressure"),({"calibration_quality":"p_lot_tangent"},"closure-pressure"),
    ({"method":"acoustic_derivation"},"closure-pressure"),({"pressure_reference":"wellhead"},"Wellhead"),
    ({"test_depth_tvd_m":2000.},"Calibration depth"),({"closure_pressure_gauge_pa":1e6},"disagree")])
def test_calibration_quality_depth_and_reference_are_explicit(patch,reason):
    v=payload();v.stress_calibration=v.stress_calibration.model_copy(update=patch)
    r=calculate_geomechanics(v,path=survey())
    assert r["status"]=="withheld" and any(reason in x for x in r["reasons"])

def test_no_survey_context_and_out_of_range_md_do_not_produce_stability():
    v=payload();assert calculate_geomechanics(v)["status"]=="withheld"
    with pytest.raises(ValueError):calculate_geomechanics(v.model_copy(update={"md_m":1001.}),path=survey())

@pytest.fixture
def context(api_setup):
    c,p,b,g,store,root=api_setup
    response=c.post(b+"/geometry",json={"geometry":g,"change_note":"Geomechanics API fixture"})
    assert response.status_code==201,response.text
    rev=response.json();draft=c.get(b+"/research/geomechanics/template/"+rev["id"]).json()
    return c,p,b,store,root,rev,draft

def test_preserved_import_saved_study_citation_report_restart_and_archive_restore(context,tmp_path):
    c,p,b,store,root,rev,draft=context
    raw=json.dumps(draft,indent=2).encode()
    response=c.post(b+"/research/geomechanics/imports",files={"file":("synthetic-core.json",raw)})
    assert response.status_code==201,response.text
    imported=response.json();response=c.post(b+"/calculations/geomechanics",json=imported["inputs_si"])
    assert response.status_code==200,response.text
    calc=response.json();r=calc["result"]
    assert r["status"]=="research_scenario" and len(r["profile"])==360
    assert r["geometry_sha256"]==rev["sha256"] and r["input_document_sha256"]==hashlib.sha256(raw).hexdigest()
    assert r["input_document_matches_current"] and r["numerical_refinement"]["passed"]
    assert not r["approval_issued"] and not r["clearance_generated"] and not r["independent_evidence_verification"]
    citations=c.get(b+"/evidence/search",params={"q":draft["study_name"]}).json()["citations"]
    assert next(x for x in citations if x["entity_id"]==calc["id"])["sha256_hash"]==digest(canonical(calc).encode())
    report=c.post(b+"/reports").json();assert calc in c.get(b+"/reports/"+report["id"]).json()["snapshot"]["calculations"]
    restart=TestClient(create_app(root));restart.get("/api/session")
    assert restart.get(b+"/calculations?model=geomechanics").json()==[calc]
    restored=Store(tmp_path/"restored");restored.restore_bundle(store.export_bundle(p["id"]))
    assert restored.calculations(p["id"],"geomechanics")==[calc] and restored.audit_history()["integrity"]=="verified"

def test_changed_inputs_retain_original_hash_and_withheld_result(context):
    c,p,b,store,root,rev,draft=context;raw=json.dumps(draft).encode()
    imported=c.post(b+"/research/geomechanics/imports",files={"file":("core.json",raw)}).json()
    changed=imported["inputs_si"];changed["core_test"]=None
    response=c.post(b+"/calculations/geomechanics",json=changed)
    assert response.status_code==200,response.text
    assert response.json()["result"]["status"]=="withheld"
    assert response.json()["result"]["input_document_matches_current"] is False
    assert (root/"raw"/imported["source_sha256"]).read_bytes()==raw

@pytest.mark.parametrize("patch",[{"md_m":30001.},{"md_m":1001.},{"depth_datum":"MSL"},{"stress_north_reference":"grid"},{"geometry_revision_id":"missing"}])
def test_bad_geometry_or_contract_does_not_save(context,patch):
    c,p,b,store,root,rev,draft=context;draft=copy.deepcopy(draft);draft.update(patch)
    assert c.post(b+"/calculations/geomechanics",json=draft).status_code in (404,422)
    assert store.calculations(p["id"],"geomechanics")==[]

def test_team_read_write_roles_and_other_project_binding(context):
    c,p,b,store,root,rev,draft=context
    viewer=auth.create_user(store,"geo-viewer","Viewer","viewer","test correct horse battery",actor="test")
    from services.api.access import add_member
    add_member(store,p["id"],viewer["id"],"test")
    token,_=auth.login(store,"geo-viewer","test correct horse battery")
    team=TestClient(create_app(root,mode="team"));headers={"Authorization":"Bearer "+token}
    assert team.get(b+"/research/geomechanics/template/"+rev["id"],headers=headers).status_code==200
    assert team.post(b+"/calculations/geomechanics",json=draft,headers=headers).status_code==403
    other=c.post("/api/projects",json={"name":"Other","well_name":"Other","datum":"RKB","bit_diameter_m":.2,"origin":"synthetic"}).json()
    assert c.post("/api/projects/"+other["id"]+"/calculations/geomechanics",json=draft).status_code==404
