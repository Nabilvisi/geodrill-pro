import copy
import math
import sqlite3
import pytest
from pydantic import ValidationError
from fastapi.testclient import TestClient
from packages.engineering.models import SurveyRequest
from packages.engineering.geometry import GeometryInput, Path, geometry_result
from packages.engineering.casing import CasingCheckInput, casing_check
from services.api.main import create_app

def survey(stations):
    return SurveyRequest(stations=[{"md_m":m,"inclination_rad":i,"azimuth_rad":a} for m,i,a in stations])

def casing(name="String A"):
    return {"name":name,"top_md_m":0.,"bottom_md_m":1000.,"outside_diameter_m":.2,"inside_diameter_m":.1,
            "minimum_wall_m":.05,"wall_loss_allowance_m":0.,"state":"planned","grade":"Synthetic test",
            "source":"Synthetic test fixture","yield_strength_pa":100e6,"body_burst_pa":100e6,"body_collapse_pa":100e6,
            "body_tension_n":1e7,"body_compression_n":1e7,"connection_burst_pa":100e6,"connection_collapse_pa":100e6,
            "connection_tension_n":1e7,"connection_compression_n":1e7,
            "body_rating_source":"Synthetic body fixture","connection_rating_source":"Synthetic connection fixture"}

def geom():
    return {"survey_dataset_id":"fixture","datum":"RKB","coordinate_reference":"Local test frame",
            "wellhead_north_m":100.,"wellhead_east_m":200.,"wellhead_elevation_m":30.,"survey_quality_note":"Synthetic stations",
            "tool_to_bit_offset_m":0.,"formations":[{"name":"Top A","top_tvd_m":500.,"uncertainty_m":20.,"category":"formation","source":"Synthetic top","interpretation":"synthetic"}],
            "hole_sections":[{"name":"Hole","top_md_m":0.,"bottom_md_m":1000.,"diameter_m":.3,"source":"Synthetic hole"}],
            "casings":[casing()]}

def case(**patch):
    value={"geometry_revision_id":"fixture","candidate_name":"Case A","required_load_cases":["Test"],
           "loads":[{"name":"Test","casing_name":"String A","md_m":1000.,"internal_gauge_pa":10e6,"external_gauge_pa":0.,
                     "axial_wall_force_n":0.,"source":"Synthetic load"}],
           "yield_factor":1.,"burst_factor":1.,"collapse_factor":1.,"axial_factor":1.,
           "factor_basis":"Independent analytical test","temperature_derating":1.,"derating_basis":"Isothermal analytical test"}
    value.update(patch)
    return value

def test_exact_midstation_circular_arc_and_translation():
    radius=1000.
    req=survey([(0.,0.,0.),(radius*math.pi/2,math.pi/2,0.)])
    p=Path(req)
    mid=p.at(radius*math.pi/4)
    assert mid["north_m"]==pytest.approx(radius*(1-math.sqrt(.5)),rel=1e-10)
    assert mid["tvd_m"]==pytest.approx(radius*math.sqrt(.5),rel=1e-10)
    assert mid["east_m"]==pytest.approx(0.,abs=1e-9)
    data=geom();data["hole_sections"]=[];data["casings"]=[]
    result=geometry_result(GeometryInput.model_validate(data),req)
    end=result["samples"][-1]
    assert end["reference_north_m"]-data["wellhead_north_m"]==pytest.approx(radius)
    assert end["reference_east_m"]==pytest.approx(200.)
    assert data["wellhead_elevation_m"]-end["elevation_m"]==pytest.approx(radius)

def test_formation_reentry_and_tangent_crossing():
    r=500.
    req=survey([(0.,0.,0.),(r*math.pi/2,math.pi/2,0.),(r*math.pi,math.pi,0.)])
    path=Path(req)
    crossings=path.intersections(r/2)
    assert [p["md_m"] for p in crossings]==pytest.approx([r*math.pi/6,5*r*math.pi/6],rel=1e-8)
    tangent=path.intersections(r)
    assert len(tangent)==1
    assert tangent[0]["md_m"]==pytest.approx(r*math.pi/2,rel=1e-8)

def test_vertical_small_angle_and_out_of_range_path():
    p=Path(survey([(0.,0.,0.),(1000.,1e-9,0.)]))
    assert p.at(500.)["tvd_m"]==pytest.approx(500.)
    for md in (-1.,1001.,math.nan):
        with pytest.raises(ValueError):
            p.at(md)

@pytest.mark.parametrize("mutator",[
    lambda d:d["hole_sections"][0].update(top_md_m=10.),
    lambda d:d["hole_sections"][0].update(bottom_md_m=1001.),
    lambda d:d["casings"][0].update(outside_diameter_m=.31,inside_diameter_m=.15),
    lambda d:d["casings"][0].update(minimum_wall_m=.06),
    lambda d:d["casings"][0].update(wall_loss_allowance_m=.05),
    lambda d:d["casings"].append(casing("String B")),
    lambda d:d["casings"][0].update(body_rating_source=None),
    lambda d:d["hole_sections"].append({"name":"Other","top_md_m":900.,"bottom_md_m":1000.,"diameter_m":.3,"source":"Test"})
])
def test_impossible_geometry_and_missing_rating_source_rejected(mutator):
    d=geom();mutator(d)
    with pytest.raises(ValueError):
        geometry_result(GeometryInput.model_validate(d),survey([(0.,0.,0.),(1000.,0.,0.)]))

def test_lame_analytical_inside_stresses():
    result=casing_check(CasingCheckInput.model_validate(case()),GeometryInput.model_validate(geom()))
    load=result["checks"][0];inner=load["stresses"][0]
    assert inner["radial_pa"]==pytest.approx(-10e6)
    assert inner["hoop_pa"]==pytest.approx(50e6/3)
    assert inner["von_mises_pa"]==pytest.approx(70e6/3)
    assert result["status"]=="conditional"
    assert result["design_approval"] is False

def test_hydrostatic_equal_principal_stress_gives_zero_mises():
    data=case(); area=math.pi*(.1**2-.05**2)
    data["loads"][0].update(internal_gauge_pa=10e6,external_gauge_pa=10e6,axial_wall_force_n=-10e6*area)
    result=casing_check(CasingCheckInput.model_validate(data),GeometryInput.model_validate(geom()))
    assert result["checks"][0]["stresses"][0]["von_mises_pa"]==pytest.approx(0.,abs=1e-6)

def test_missing_connection_and_missing_catalogue_never_pass():
    g=geom();g["casings"][0]["connection_burst_pa"]=None
    result=casing_check(CasingCheckInput.model_validate(case()),GeometryInput.model_validate(g))
    assert result["status"]=="insufficient_data"
    complete=geom()
    result=casing_check(CasingCheckInput.model_validate(case(required_load_cases=["Test","Cement"])),GeometryInput.model_validate(complete))
    assert result["status"]=="insufficient_data"
    assert result["missing_load_cases"][0]["load_case"]=="Cement"

def test_weak_connection_governs_and_compression_rating_is_separate():
    g=geom();g["casings"][0].update(connection_burst_pa=5e6,connection_compression_n=100.)
    data=case();data["loads"][0]["axial_wall_force_n"]=-1000.
    result=casing_check(CasingCheckInput.model_validate(data),GeometryInput.model_validate(g))
    assert result["status"]=="outside_applicability"
    assert result["checks"][0]["governing_check"]=="connection_axial"

def test_wall_loss_and_derating_raise_utilization():
    original=casing_check(CasingCheckInput.model_validate(case()),GeometryInput.model_validate(geom()))
    g=geom();g["casings"][0]["wall_loss_allowance_m"]=.02
    worn=casing_check(CasingCheckInput.model_validate(case(temperature_derating=.8)),GeometryInput.model_validate(g))
    assert worn["checks"][0]["stresses"][0]["von_mises_pa"]>original["checks"][0]["stresses"][0]["von_mises_pa"]
    assert worn["checks"][0]["maximum_utilization"]>original["checks"][0]["maximum_utilization"]

def test_cost_requires_same_currency_and_all_components():
    g=geom();g["casings"][0].update(cost_per_m=20.,cost_currency="USD",cost_basis="Synthetic fixture")
    result=geometry_result(GeometryInput.model_validate(g),survey([(0.,0.,0.),(1000.,0.,0.)]))
    assert result["cost"]["value"]==20000.
    g["casings"][0]["cost_currency"]=None
    with pytest.raises(ValidationError):
        GeometryInput.model_validate(g)

@pytest.fixture
def api_setup(tmp_path):
    app=create_app(tmp_path);c=TestClient(app);c.get("/api/session");c.headers.update({"X-Geodrill-Client":"workstation"})
    p=c.post("/api/projects",json={"name":"Geometry test","well_name":"Test","datum":"RKB","bit_diameter_m":.2,"origin":"synthetic"}).json()
    base="/api/projects/"+p["id"]
    ds=c.post(base+"/imports",data={"kind":"survey"},files={"file":("test.csv","md[m],inclination[deg],azimuth[deg]\n0,0,0\n1000,0,0\n","text/csv")}).json()
    d=geom();d["survey_dataset_id"]=ds["id"]
    return c,p,base,d,app.state.store,tmp_path

def test_revision_conflict_immutability_calculation_report_and_restart(api_setup):
    c,p,base,d,store,root=api_setup
    first=c.post(base+"/geometry",json={"geometry":d,"base_revision_id":None,"change_note":"Initial fixture"})
    assert first.status_code==201,first.text
    r=first.json()
    scenario=case(geometry_revision_id=r["id"])
    calc=c.post(base+"/calculations/casing",json=scenario)
    assert calc.status_code==200,calc.text
    assert calc.json()["result"]["geometry_sha256"]==r["sha256"]
    assert c.get(base+"/calculations?model=casing").json()[0]==calc.json()
    report=c.post(base+"/reports").json();snapshot=c.get(base+"/reports/"+report["id"]).json()
    assert snapshot["snapshot"]["engineering_revisions"][0]==r
    second=c.post(base+"/geometry",json={"geometry":d,"base_revision_id":r["id"],"change_note":"New unchanged fixture revision"})
    assert second.status_code==201
    conflict=c.post(base+"/geometry",json={"geometry":d,"base_revision_id":r["id"],"change_note":"Stale writer"})
    assert conflict.status_code==409
    assert c.get(base+"/reports/"+report["id"]).json()==snapshot
    after=TestClient(create_app(root));after.get("/api/session")
    assert after.get(base+"/geometry/"+r["id"]).json()==r
    assert after.get(base+"/engineering-revisions?module=M1").json()[0]["id"]==second.json()["id"]
    with store.connect() as db:
        with pytest.raises(sqlite3.IntegrityError):
            db.execute("DELETE FROM engineering_revisions")
    assert store.audit_history()["integrity"]=="verified"

def test_geometry_cross_project_datum_and_non_survey_rejected(api_setup):
    c,p,base,d,store,_=api_setup
    other=c.post("/api/projects",json={"name":"Other","well_name":"Other","datum":"RKB","bit_diameter_m":.2,"origin":"synthetic"}).json()
    response=c.post("/api/projects/"+other["id"]+"/geometry",json={"geometry":d,"change_note":"Cross project"})
    assert response.status_code==404
    wrong=copy.deepcopy(d);wrong["datum"]="MSL"
    assert c.post(base+"/geometry",json={"geometry":wrong,"change_note":"Wrong datum"}).status_code==422
    r=c.post(base+"/geometry",json={"geometry":d,"change_note":"Original fixture"}).json()
    assert c.get("/api/projects/"+other["id"]+"/geometry/"+r["id"]).status_code==404
    assert c.post("/api/projects/"+other["id"]+"/calculations/casing",json=case(geometry_revision_id=r["id"])).status_code==404

def test_revision_source_tampering_blocks_new_calculation(api_setup):
    c,_,base,d,store,root=api_setup
    r=c.post(base+"/geometry",json={"geometry":d,"change_note":"Original fixture"}).json()
    (root/"raw"/r["result"]["survey_source_sha256"]).write_bytes(b"changed")
    assert c.get(base+"/geometry/"+r["id"]).status_code==422
    assert c.post(base+"/calculations/casing",json=case(geometry_revision_id=r["id"])).status_code==422

def test_horizontal_contact_is_an_interval_not_a_unique_intersection():
    path=Path(survey([(0.,math.pi/2,0.),(500.,math.pi/2,0.),(1000.,math.pi/2,0.)]))
    assert path.intersections(0.)==[]
    assert path.coincident_intervals(0.)==[{"top_md_m":0.,"bottom_md_m":1000.}]

@pytest.mark.parametrize("field,value",[("minimum_wall_m",1e-300),("inside_diameter_m",1e-300),("yield_strength_pa",1e-300),("wall_loss_allowance_m",.05-1e-12)])
def test_numerically_degenerate_casing_inputs_rejected(field,value):
    data=geom();data["casings"][0][field]=value
    with pytest.raises(ValidationError):
        GeometryInput.model_validate(data)

def test_numerically_degenerate_derating_rejected():
    with pytest.raises(ValidationError):
        CasingCheckInput.model_validate(case(temperature_derating=1e-300))
