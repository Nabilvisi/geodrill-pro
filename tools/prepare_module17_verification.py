
"""Prepare manufactured study documents for actual Chrome import/save verification."""
import json,math,pathlib,httpx
root=pathlib.Path(__file__).resolve().parents[1]
c=httpx.Client(base_url="http://127.0.0.1:8765",timeout=60,headers={"X-Geodrill-Client":"workstation"});c.get("/api/session").raise_for_status()
def get(path):r=c.get("/api"+path);r.raise_for_status();return r.json()
def post(path,**kw):r=c.post("/api"+path,**kw);r.raise_for_status();return r.json()
name="Modules 12–17 · Software verification"
project=next((p for p in get("/projects") if p["name"]==name),None)
if project is None:project=post("/projects",json={"name":name,"well_name":"Synthetic integrated research well","datum":"RKB synthetic","bit_diameter_m":.216,"origin":"synthetic"})
base="/projects/"+project["id"]
revs=get(base+"/engineering-revisions?module=M1")
if revs:rev=revs[0]
else:
 ds=post(base+"/imports",data={"kind":"survey"},files={"file":("synthetic-research-survey.csv",b"md[m],inclination[deg],azimuth[deg]\n0,0,0\n500,0,0\n1000,0,0\n","text/csv")})
 geom={"survey_dataset_id":ds["id"],"datum":project["datum"],"coordinate_reference":"Synthetic local frame","wellhead_north_m":0.,"wellhead_east_m":0.,"wellhead_elevation_m":0.,"survey_quality_note":"Manufactured vertical verification path","tool_to_bit_offset_m":0.,"formations":[],"hole_sections":[{"name":"Synthetic uniform hole","top_md_m":0.,"bottom_md_m":1000.,"diameter_m":.3,"source":"Manufactured hole"}],"casings":[{"name":"Synthetic planned casing","top_md_m":0.,"bottom_md_m":1000.,"outside_diameter_m":.244,"inside_diameter_m":.216,"minimum_wall_m":.014,"wall_loss_allowance_m":0.,"state":"planned","grade":"Synthetic material","source":"Manufactured geometry","yield_strength_pa":690e6,"body_rating_source":"Synthetic yield property, no material certificate"}]}
 rev=post(base+"/geometry",json={"geometry":geom,"base_revision_id":None,"change_note":"M12–M17 manufactured geometry and casing verification"})
folder=root/"docs"/"evidence"
names={"dynamics":"Synthetic BHA response and native samples","bit-condition":"Synthetic inspected and censored bit runs","wear-fatigue":"Synthetic separate casing wear and fatigue","anomaly":"Synthetic causal flow-balance replay","gas-phase":"Synthetic characterized binary equilibrium","supervision":"Synthetic bounded supervisory software simulation"}
for model,title in names.items():
 v=get(base+"/research/"+model+"/template/"+rev["id"]);v["study_name"]=title
 if model=="dynamics":
  v["sensors"]=[{"name":"Synthetic axial instrument channel","axis":"axial_acceleration","units":"m_s2","provenance":"Manufactured native-time verification samples; not a physical instrument","calibration_note":"Synthetic sampling/anti-alias declaration; no calibrated sensor","anti_alias_bandwidth_hz":100.,"samples":[{"time_s":i*.001,"value":2*math.sin(2*math.pi*8*i*.001),"quality":"accepted"} for i in range(101)]}]
 (folder/("m1217-"+model+"-inputs.json")).write_text(json.dumps(v,indent=2),encoding="utf-8")
 if model=="gas-phase":
  v.update(study_name="Synthetic external mud-gas study and batch replay",mode="external_mud_gas_review",fluid_system="actual_mud_gas",characterization_note="Manufactured external record, not actual-mud PVT qualification",external_model_reference="Synthetic external phase-study fixture v1.0",external_review_state="reviewed",external_review_note="Manufactured review provenance, no laboratory or specialist approval",replay_step_s=.1,external_points=[{"md_m":float(i*100),"time_s":float(i*10),"absolute_pressure_pa":float(2e6-i*.5e6),"temperature_k":300.,"vapor_fraction":float(.2+i*.3),"vapor_composition":[.8,.2],"liquid_composition":[.2,.8],"dissolved_gas_mol":float([8,6,2][i]),"vapor_molar_volume_m3_mol":float(.001+i*.001),"material_balance_residual_mol":0.,"converged":True,"phase_stability_checked":True} for i in range(3)])
  (folder/"m1217-external-phase-inputs.json").write_text(json.dumps(v,indent=2),encoding="utf-8")
 if model=="supervision":
  v.update(study_name="Synthetic supervisory faults and fresh recovery",faults=[{"start_s":3.,"end_s":6.,"kind":"disconnect"},{"start_s":7.,"end_s":8.,"kind":"interlock_open"},{"start_s":10.,"end_s":12.,"kind":"manual_override"},{"start_s":15.,"end_s":16.,"kind":"unknown_outcome"}])
  (folder/"m1217-supervisory-fault-inputs.json").write_text(json.dumps(v,indent=2),encoding="utf-8")
context={"project_id":project["id"],"project_name":name,"geometry_revision_id":rev["id"],"geometry_sha256":rev["sha256"]}
(folder/"m1217-context.json").write_text(json.dumps(context,indent=2),encoding="utf-8")
print(json.dumps(context))
