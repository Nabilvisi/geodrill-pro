"""Independent limiting cases, evidence gates, causality and persistence for M12–M17."""
import copy,math,json
import pytest
from pydantic import ValidationError
from fastapi.testclient import TestClient
from test_geometry_casing import geom,survey,api_setup
from packages.engineering.geometry import GeometryInput,Path
from packages.engineering.dynamics import DynamicsInput,dynamics,matrices,response,DynamicsSensor
from packages.engineering.bit_condition import BitInput,BitRun,bit_condition,kaplan_meier
from packages.engineering.wear_fatigue import WearInput,wear_fatigue,fatigue_cycles
from packages.engineering.anomaly import AnomalyInput,anomaly
from packages.engineering.gas_phase import GasInput,PhasePoint,gas_phase,flash,pr_fugacity,cubic_roots,rachford,phase_replay,R
from packages.engineering.supervision import SupervisionInput,RequestExample,SimulationGateway,evidence_digest,simulate,supervision
from services.api.late_demo import late_template
from services.api.main import create_app
MODELS={"dynamics":(DynamicsInput,dynamics),"bit-condition":(BitInput,bit_condition),"wear-fatigue":(WearInput,wear_fatigue),"anomaly":(AnomalyInput,anomaly),"gas-phase":(GasInput,gas_phase),"supervision":(SupervisionInput,supervision)}
def geometry():return GeometryInput.model_validate(geom())
def path(angle=0.):return Path(survey([(0.,0.,0.),(1000.,angle,0.)]))
def draft(model):
    return late_template(model,{"id":"fixture","input":geom(),"result":{"total_depth_md_m":1000.}},"synthetic")
def value(model,**patch):
    d=draft(model);d.update(patch);return MODELS[model][0].model_validate(d)
def run(model,**patch):return MODELS[model][1](value(model,**patch),geometry(),path())

def test_uncoupled_modal_frequencies_analytical():
    v=value("dynamics",axial_torsional_coupling=0.,axial_lateral_coupling=0.,torsional_lateral_coupling=0.,bit_axial_stiffness_n_per_m=0.)
    m,k,c,eig=matrices(v);l=50.;E=207e9;rho=7850.;od=.127;inside=.108
    A=math.pi*(od**2-inside**2)/4;I=math.pi*(od**4-inside**4)/64
    expected=sorted([math.sqrt(3*E/(rho*l*l))/(2*math.pi),math.sqrt(3*E/(2*1.3*rho*l*l))/(2*math.pi),math.sqrt(3*E*I/(.236*rho*A*l**4))/(2*math.pi)])
    assert [math.sqrt(e[0])/(2*math.pi) for e in eig]==pytest.approx(expected,rel=1e-12)
    for lam,vec in eig:
        normalized=[[k[i][j]/math.sqrt(m[i]*m[j]) for j in range(3)] for i in range(3)]
        assert [sum(normalized[i][j]*vec[j] for j in range(3)) for i in range(3)]==pytest.approx([lam*x for x in vec],abs=1e-9)

def test_forced_axial_response_zero_ic_closed_form_and_refinement():
    v=value("dynamics",axial_torsional_coupling=0.,axial_lateral_coupling=0.,torsional_lateral_coupling=0.,damping_ratio=0.,torque_amplitude_nm=0.,lateral_force_amplitude_n=0.,contact_stiffness_n_per_m=0.)
    m,k,c,e=matrices(v);rows,_=response(v,m,k,c,.00025);wn=math.sqrt(k[0][0]/m[0]);w=2*math.pi*v.excitation_hz
    exact=lambda t:v.axial_force_amplitude_n/m[0]/(wn*wn-w*w)*(math.sin(w*t)-w/wn*math.sin(wn*t))
    assert [r["axial_displacement_m"] for r in rows]==pytest.approx([exact(r["time_s"]) for r in rows],abs=1e-10)
    r=dynamics(v,geometry(),path());assert max(r["refinement_relative_errors"].values())<1e-5
    assert r["maximum_energy_balance_residual_j"]<.001
    coarse,_=response(v,m,k,c,.0005)
    error=lambda samples:max(abs(row["axial_displacement_m"]-exact(row["time_s"])) for row in samples)
    assert error(coarse)/error(rows)>12

def test_contact_response_energy_and_refinement():
    r=run("dynamics",lateral_force_amplitude_n=10000.,duration_s=1.,lateral_clearance_m=.0001)
    assert r["contact_active_samples"]>0
    assert all(row["energy_j"]>=0 for row in r["history"])
    assert max(r["refinement_relative_errors"].values())<.01

@pytest.mark.parametrize("patch",[{"boundary":"unknown"},{"boundary":"full_contact_bha"},{"evidence_state":"unknown"}])
def test_dynamics_unsupported_withheld(patch):
    r=run("dynamics",**patch);assert r["status"]=="withheld" and r["history"]==[]
def test_dynamics_geometry_and_work_limits():
    assert dynamics(value("dynamics"),geometry(),path(.3))["status"]=="withheld"
    with pytest.raises(ValueError):run("dynamics",outside_diameter_m=.4)
    with pytest.raises(ValueError):run("dynamics",lateral_clearance_m=.2)
    with pytest.raises(ValueError):run("dynamics",time_step_s=.01)
    with pytest.raises(ValueError):run("dynamics",duration_s=60.,time_step_s=.00001)
def test_sensor_bandwidth_quality_and_no_observability_claim():
    sensor={"name":"Axial native","axis":"axial_acceleration","units":"m_s2","provenance":"Synthetic native fixture","calibration_note":"Synthetic anti-alias declaration","anti_alias_bandwidth_hz":100.,"samples":[{"time_s":0.,"value":3.,"quality":"accepted"},{"time_s":.001,"value":4.,"quality":"accepted"}]}
    r=run("dynamics",sensors=[sensor]);review=r["sensor_review"][0]
    assert review["rms"]==pytest.approx(math.sqrt(12.5))
    assert review["modal_observability_established"] is False
    assert review["calibration_independently_verified"] is False
    sensor["samples"][1]["quality"]="missing";assert run("dynamics",sensors=[sensor])["sensor_review"][0]["rms"] is None
    sensor["units"]="rad_s2"
    with pytest.raises(ValidationError):DynamicsSensor.model_validate(sensor)

def test_km_tied_failures_censoring_and_product_limit():
    rows=draft("bit-condition")["runs"]
    for r,t,term in zip(rows,[10.,10.,20.,30.],["confirmed_failure","planned_trip","confirmed_failure","ongoing"]):r.update(drilling_hours=t,termination=term)
    profile=kaplan_meier([BitRun.model_validate(r) for r in rows])
    assert [r["at_risk"] for r in profile]==[4,2,1]
    assert [r["survival"] for r in profile]==pytest.approx([.75,.375,.375])
    assert profile[0]["censored"]==1
    assert profile[0]["greenwood_variance"]==pytest.approx(.75**2/12)

def test_bit_receipt_cutoff_prevents_future_inspection_leakage():
    data=draft("bit-condition");data["runs"][0]["available_at"]="2026-02-01T00:00:00Z"
    r=run("bit-condition",runs=data["runs"])
    assert r["cohort_size"]==3 and r["confirmed_failures"]==1
    assert not r["run_records"][0]["included_in_cohort"]
    assert "Future" in r["excluded_runs"][0]["reason"]
def test_bit_cost_and_out_of_support_are_not_trip_advice():
    r=run("bit-condition");assert r["cost_comparison"]["horizon_failure_fraction"]==.25
    assert r["cost_comparison"]["continue_expected_cost"]==13500.
    assert r["cost_comparison"]["recommended_action"] is None
    assert run("bit-condition",horizon_hours=100.)["cost_comparison"]["status"]=="withheld"
    assert run("bit-condition",formation="Different formation")["status"]=="withheld"
@pytest.mark.parametrize("patch",[{"recovered":False},{"inspection_note":None},{"available_at":"2025-01-01T00:00:00Z"},{"completed_at":"2026-01-01T00:00:00"}])
def test_bit_contract_rejects_unsupported_records(patch):
    r=draft("bit-condition")["runs"][0];r.update(patch)
    with pytest.raises(ValidationError):BitRun.model_validate(r)

def test_archard_volume_miner_and_independent_lame_yield():
    r=run("wear-fatigue")
    assert r["wear_volume_m3"]==pytest.approx(1e-4)
    assert r["predicted_minimum_wall_m"]==pytest.approx(.0499)
    assert r["conservative_minimum_wall_m"]==pytest.approx(.049875)
    assert r["fatigue"]["miner_damage"]==pytest.approx(.01)
    ro=.1;ri=ro-.049875
    exact=math.sqrt(3)*5e6*ro*ro/(ro*ro-ri*ri)
    assert r["residual_strength"]["closed_end_von_mises_pa"]==pytest.approx(exact)
    curve=value("wear-fatigue").fatigue_curve
    assert fatigue_cycles(curve,math.sqrt(50e6*100e6))==pytest.approx(math.sqrt(1e7*1e6))
@pytest.mark.parametrize("patch",[{"geometry_assumption":"localized_groove"},{"geometry_assumption":"unknown"},{"unobserved_exposure":True},{"wear_coefficient_m2_n":None},{"wear_coefficient_m2_n":1e-7}])
def test_wear_restricted_capacity_gates(patch):
    r=run("wear-fatigue",**patch);assert r["residual_strength"]["status"]=="withheld"
def test_separate_fatigue_does_not_hide_wear():
    data=draft("wear-fatigue");data["cycle_exposures"][0]["mean_stress_pa"]=1e6
    r=run("wear-fatigue",cycle_exposures=data["cycle_exposures"])
    assert r["fatigue"]["miner_damage"] is None and r["wear_volume_m3"]==pytest.approx(1e-4)
    data["cycle_exposures"][0].update(mean_stress_pa=0.,stress_amplitude_pa=1e6)
    assert run("wear-fatigue",cycle_exposures=data["cycle_exposures"])["fatigue"]["status"]=="withheld"
def test_wear_inspection_residual_no_integrity_certificate():
    r=run("wear-fatigue",observed_minimum_wall_m=.049,inspection_note="Synthetic independent inspection")
    assert r["inspection_residual_m"]==pytest.approx(-.0009)
    assert r["approval_issued"] is False
def test_wear_coefficient_provenance_required():
    with pytest.raises(ValidationError):value("wear-fatigue",wear_material_fluid_note=None)

def test_mass_balance_transfer_and_stock_derivative_sign():
    samples=draft("anomaly")["samples"]
    for s in samples:s.update(inlet_kg_s=4.,outlet_kg_s=3.,transfer_into_kg_s=1.,contained_mass_kg=10000.+2*s["time_s"])
    r=run("anomaly",samples=samples,adjudicated_events=[])
    assert all(row["residual_kg_s"]==0 for row in r["history"]) and not r["candidate_events"]
def test_causal_persistence_and_label_metrics():
    r=run("anomaly");e=r["event_evaluation"]
    assert r["candidate_events"][0]["alarm_s"]==8.
    assert e["matched"][0]["detection_delay_s"]==3.
    assert e["matched"][0]["lead_vs_baseline_s"]==2.
    assert e["false_candidates_per_monitoring_hour"]==0
    data=draft("anomaly");data["samples"]=data["samples"][:8];data["adjudicated_events"]=[]
    assert not run("anomaly",samples=data["samples"],adjudicated_events=[])["candidate_events"]
    data["samples"].append(draft("anomaly")["samples"][8])
    assert run("anomaly",samples=data["samples"],adjudicated_events=[])["candidate_events"][0]["alarm_s"]==8.
@pytest.mark.parametrize("field,changed",[("quality","missing"),("operation","connection"),("pump_on",False),("inlet_kg_s",-1.)])
def test_balance_unknown_and_operation_interrupts_persistence(field,changed):
    samples=draft("anomaly")["samples"];samples[7][field]=changed
    r=run("anomaly",samples=samples)
    assert r["history"][6]["candidate_alarm_active"] is False
    assert r["candidate_events"][0]["alarm_s"]>=11.
    if field in ["quality","inlet_kg_s"]:assert r["history"][6]["residual_kg_s"] is None
def test_flow_gap_and_unmatched_missed_counts():
    samples=draft("anomaly")["samples"];samples=[s for s in samples if s["time_s"] not in [7.,8.,9.]]
    r=run("anomaly",samples=samples);assert r["unknown_intervals"]>=1
    labels=[{"name":"Miss","onset_s":0.,"end_s":2.,"baseline_alarm_s":None,"evidence_note":"Synthetic true label"}]
    r=run("anomaly",adjudicated_events=labels)
    assert r["event_evaluation"]["missed_labels"]==["Miss"]
    assert r["event_evaluation"]["unmatched_candidate_events"]==1
    assert r["event_evaluation"]["false_candidates_per_monitoring_hour"]==180.
def test_balance_prefix_unchanged_by_future_samples():
    full=run("anomaly")["history"];samples=draft("anomaly")["samples"][:11]
    short=run("anomaly",samples=samples,adjudicated_events=[])["history"]
    assert short==full[:10]

def test_cubic_known_roots_and_rachford_exact():
    assert cubic_roots(-6.,11.,-6.)==pytest.approx([1.,2.,3.])
    assert rachford([.5,.5],[2.,.5])==pytest.approx(.5)
    assert rachford([.5,.5],[1.1,2.]) is None
def test_binary_flash_material_balance_and_fugacity_equality():
    v=value("gas-phase");r=flash(v.components,1e6,200.,0.)
    assert r["phase"]=="two_phase" and r["minimum_trial_tpd"]<0
    beta=r["vapor_fraction"];x=r["liquid_composition"];y=r["vapor_composition"]
    assert sum(x)==pytest.approx(1.) and sum(y)==pytest.approx(1.)
    assert [(1-beta)*a+beta*b for a,b in zip(x,y)]==pytest.approx([.5,.5],abs=1e-10)
    pl,zl=pr_fugacity(v.components,x,1e6,200.,0.,"liquid");pv,zv=pr_fugacity(v.components,y,1e6,200.,0.,"vapor")
    assert [math.log(xx)+l for xx,l in zip(x,pl)]==pytest.approx([math.log(yy)+vv for yy,vv in zip(y,pv)],abs=1e-7)
    assert 0<zl<zv
def test_eos_root_satisfies_original_pressure_equation():
    v=value("gas-phase");comp=[.5,.5];_,Z=pr_fugacity(v.components,comp,1e6,200.,0.,"stable")
    a=[];b=[]
    for c in v.components:
        k=.37464+1.54226*c.acentric_factor-.26992*c.acentric_factor**2
        a.append(.45724*R**2*c.critical_temperature_k**2/c.critical_pressure_pa*(1+k*(1-math.sqrt(200./c.critical_temperature_k)))**2)
        b.append(.07780*R*c.critical_temperature_k/c.critical_pressure_pa)
    am=(.5*math.sqrt(a[0])+.5*math.sqrt(a[1]))**2;bm=sum(b)/2;volume=Z*R*200/1e6
    assert R*200/(volume-bm)-am/(volume*(volume+bm)+bm*(volume-bm))==pytest.approx(1e6,rel=1e-10)
def test_high_temperature_low_pressure_single_stable_no_false_vapor_fraction():
    r=run("gas-phase",temperature_k=400.,absolute_pressure_pa=1e4)["equilibrium"]
    assert r["phase"]=="single_stable"
    assert r["vapor_fraction"] is None
    assert r["z_factor"]==pytest.approx(1.,abs=.001)
@pytest.mark.parametrize("patch",[{"fluid_system":"actual_mud_gas"},{"fluid_system":"uncharacterized"},{"evidence_state":"unknown"}])
def test_native_mud_gas_unsupported(patch):assert run("gas-phase",**patch)["status"]=="withheld"

def external(**patch):
    points=[{"md_m":float(i*100),"time_s":float(i*10),"absolute_pressure_pa":1e6,"temperature_k":300.,"vapor_fraction":.5,"vapor_composition":[.8,.2],"liquid_composition":[.2,.8],"dissolved_gas_mol":2.,"vapor_molar_volume_m3_mol":.002,"material_balance_residual_mol":0.,"converged":True,"phase_stability_checked":True} for i in range(2)]
    v={"mode":"external_mud_gas_review","fluid_system":"actual_mud_gas","external_review_state":"reviewed","external_model_reference":"Synthetic independent external model v1","external_review_note":"Manufactured specialist review fixture","external_points":points};v.update(patch)
    return value("gas-phase",**v)
def test_external_batch_exponential_limiting_case_and_conservation():
    v=external();r=phase_replay(v,1.)
    exact=2.+6.*math.exp(-1.)
    assert r[-1]["dissolved_gas_mol"]==pytest.approx(exact)
    assert all(row["inventory_residual_mol"]==0 for row in r)
    result=gas_phase(v,geometry(),path())
    assert result["status"]=="research_scenario"
    assert result["external_flags_independently_verified"] is False
    assert result["final_refinement_mol"]<1e-12
@pytest.mark.parametrize("patch",[{"converged":False},{"phase_stability_checked":False},{"material_balance_residual_mol":.1}])
def test_external_phase_flags_gated(patch):
    v=external();d=v.model_dump();d["external_points"][0].update(patch);v=GasInput.model_validate(d)
    assert gas_phase(v,geometry(),path())["status"]=="withheld"
def test_external_phase_contract_and_depth_limits():
    d=external().model_dump();d["external_points"][0]["vapor_composition"]=[.8,.8]
    with pytest.raises(ValidationError):GasInput.model_validate(d)
    d=external().model_dump();d["external_points"][1]["md_m"]=1001.
    with pytest.raises(ValueError):gas_phase(GasInput.model_validate(d),geometry(),path())

def request(v,**patch):
    d={"request_id":"One","issued_at_s":1.,"expires_at_s":2.,"target":"simulated-choke-01","units":"normalized_fraction","value":.1,"evidence_digest":evidence_digest(v)};d.update(patch)
    return RequestExample.model_validate(d)
def test_gateway_default_deny_and_duplicate_expiry_slew():
    v=value("supervision");g=SimulationGateway(v);r=request(v)
    assert g.validate(r,1.)["accepted_in_simulation"]
    assert not g.validate(r,1.5)["accepted_in_simulation"]
    assert not g.validate(request(v,request_id="Other",value=1.),1.5)["accepted_in_simulation"]
    assert not g.validate(request(v,request_id="Expired"),2.)["accepted_in_simulation"]
    assert not SimulationGateway(value("supervision",authority_mode="none")).validate(r,1.)["accepted_in_simulation"]
@pytest.mark.parametrize("patch",[{"proportional_per_pa":0.},{"integral_per_pa_s":0.},{"transport_delay_s":1.},{"request_ttl_s":2.},{"simulation_lease_expires_s":1.},{"faults":[{"start_s":1.,"end_s":2.,"kind":"disconnect"}]}])
def test_exact_configuration_digest_binds_controller_policy_and_faults(patch):
    old=value("supervision");new=value("supervision",**patch)
    assert evidence_digest(new)!=evidence_digest(old)
    assert not SimulationGateway(new).validate(request(old),1.)["accepted_in_simulation"]
@pytest.mark.parametrize("kwargs",[{"connected":False},{"ready":False},{"manual":True},{"known":False}])
def test_gateway_faults_reject_without_state_mutation(kwargs):
    v=value("supervision");g=SimulationGateway(v);r=request(v)
    assert not g.validate(r,1.,**kwargs)["accepted_in_simulation"]
    assert g.seen==set() and g.last_at is None
    assert g.validate(r,1.)["accepted_in_simulation"]
def test_physical_slew_rejection_does_not_consume_id():
    v=value("supervision");g=SimulationGateway(v);r=request(v)
    assert not g.validate(r,1.,current_value=0.,elapsed_s=.1)["accepted_in_simulation"]
    assert g.seen==set()
    assert g.validate(r,1.,current_value=0.,elapsed_s=1.)["accepted_in_simulation"]
def test_first_order_plant_exact_zero_controller_limiting_case():
    v=value("supervision",authority_mode="none",initial_pressure_pa=25e6,proportional_per_pa=0.,integral_per_pa_s=0.)
    rows,events=simulate(v,.1)
    assert rows[-1]["pressure_pa"]==pytest.approx(20e6+5e6*math.exp(-20/2))
    assert not any(e["accepted_in_simulation"] for e in events)
def test_controller_tracking_refinement_and_no_equipment():
    r=run("supervision")
    assert r["refinement_change_pa"]<1e5
    assert abs(r["final_pressure_pa"]-22e6)<.5e6
    assert all(0<=row["simulated_actuator_fraction"]<=1 for row in r["history"])
    assert r["equipment_control"] is False and r["network_adapter_available"] is False
    assert all(e["equipment_command_issued"] is False for e in r["request_audit"])
@pytest.mark.parametrize("kind",["disconnect","manual_override","interlock_open","unknown_outcome","controller_reset"])
def test_supervisory_faults_no_acceptance_or_stale_reconnect(kind):
    v=value("supervision",faults=[{"start_s":3.,"end_s":6.,"kind":kind}])
    rows,events=simulate(v,.1)
    assert not any(e["accepted_in_simulation"] for e in events if 3<=e["at_s"]<6)
    resumed=[e for e in events if e["accepted_in_simulation"] and e["at_s"]>=6]
    assert resumed and resumed[0]["at_s"]>=6.2-1e-8
    if kind=="manual_override":assert all(r["simulated_actuator_fraction"]==.3 for r in rows if 3<=r["time_s"]<6)
def test_supervisory_lease_and_ttl_pending_expiry():
    _,events=simulate(value("supervision",simulation_lease_expires_s=2.),.1)
    assert not any(e["accepted_in_simulation"] for e in events if e["at_s"]>=2.)
    _,events=simulate(value("supervision",transport_delay_s=1.,request_ttl_s=.2),.1)
    assert not any(e["accepted_in_simulation"] for e in events)

@pytest.mark.parametrize("model",list(MODELS))
def test_strict_model_contracts(model):
    with pytest.raises(ValidationError):value(model,unexpected=True)
    with pytest.raises(ValidationError):value(model,evidence_state="measured_and_approved")
    r=run(model,evidence_state="unknown");assert r["status"]=="withheld" and r["approval_issued"] is False

def test_late_api_all_modules_geometry_binding_fixed_report_restart(api_setup):
    c,p,base,d,store,root=api_setup
    rev=c.post(base+"/geometry",json={"geometry":d,"change_note":"Late module fixture","base_revision_id":None}).json()
    saved=[]
    for model in MODELS:
        data=c.get(base+"/research/"+model+"/template/"+rev["id"]).json()
        res=c.post(base+"/calculations/"+model,json=data);assert res.status_code==200,res.text
        record=res.json();saved.append(record)
        assert record["result"]["geometry_sha256"]==rev["sha256"]
        assert len(record["result"]["survey_source_sha256"])==64
        assert record["result"]["approval_issued"] is False
        bad=copy.deepcopy(data);bad["depth_datum"]="Wrong"
        assert c.post(base+"/calculations/"+model,json=bad).status_code==422
        bad=copy.deepcopy(data);bad["geometry_revision_id"]="absent"
        assert c.post(base+"/calculations/"+model,json=bad).status_code==404
    report=c.post(base+"/reports").json();snapshot=c.get(base+"/reports/"+report["id"]).json()
    assert snapshot["snapshot"]["application_version"]=="0.8.0"
    for rec in saved:assert rec in snapshot["snapshot"]["calculations"]
    after=TestClient(create_app(root));after.get("/api/session")
    for rec in saved:assert rec in after.get(base+"/calculations?model="+rec["model"]).json()
    c.post(base+"/calculations/anomaly",json=saved[-3]["inputs_si"])
    assert c.get(base+"/reports/"+report["id"]).json()==snapshot
    assert c.get("/api/audit").json()["integrity"]=="verified"
    assert c.post(base+"/commands/choke",json={}).status_code==404
    assert c.get("/api/health").json()["equipment_control"] is False


@pytest.mark.parametrize("model",list(MODELS))
def test_late_api_ownership_and_source_integrity(api_setup,model):
    c,p,base,d,store,root=api_setup
    rev=c.post(base+"/geometry",json={"geometry":d,"change_note":"Ownership fixture","base_revision_id":None}).json()
    data=c.get(base+"/research/"+model+"/template/"+rev["id"]).json()
    other=c.post("/api/projects",json={"name":"Other project","well_name":"Other","datum":"RKB","bit_diameter_m":.2,"origin":"synthetic"}).json()
    assert c.post("/api/projects/"+other["id"]+"/calculations/"+model,json=data).status_code in [404,422]
    original=root/"raw"/rev["result"]["survey_source_sha256"]
    original.write_bytes(b"changed fixture source")
    assert c.post(base+"/calculations/"+model,json=data).status_code==422

@pytest.mark.parametrize("patch",[{"target":"unlisted-equipment"},{"units":"percent"},{"evidence_digest":"0"*64},{"value":1.1},{"issued_at_s":2.},{"expires_at_s":.5}])
def test_gateway_request_contract_denials(patch):
    v=value("supervision");assert not SimulationGateway(v).validate(request(v,**patch),1.)["accepted_in_simulation"]


@pytest.mark.parametrize("model",list(MODELS))
def test_typed_input_import_raw_hash_duplicate_and_changed_input_binding(api_setup,model):
    c,p,base,d,store,root=api_setup
    rev=c.post(base+"/geometry",json={"geometry":d,"change_note":"Import fixture","base_revision_id":None}).json()
    inputs=c.get(base+"/research/"+model+"/template/"+rev["id"]).json()
    raw=json.dumps(inputs,indent=2).encode()
    response=c.post(base+"/research/"+model+"/imports",files={"file":("study.json",raw,"application/json")})
    assert response.status_code==201,response.text
    imported=response.json();assert (root/"raw"/imported["source_sha256"]).read_bytes()==raw
    repeated=c.post(base+"/research/"+model+"/imports",files={"file":("study.json",raw,"application/json")}).json()
    assert repeated["duplicate"] and repeated["id"]==imported["id"]
    inputs=imported["inputs_si"]
    saved=c.post(base+"/calculations/"+model,json=inputs);assert saved.status_code==200,saved.text
    assert saved.json()["result"]["input_document_matches_current"] is True
    assert saved.json()["result"]["input_document_sha256"]==imported["source_sha256"]
    inputs["study_name"]="Renamed research scenario"
    assert c.post(base+"/calculations/"+model,json=inputs).json()["result"]["input_document_matches_current"] is False
    report=c.post(base+"/reports").json();snapshot=c.get(base+"/reports/"+report["id"]).json()["snapshot"]
    assert any(ds["source_hash"]==imported["source_sha256"] for ds in snapshot["datasets"])
    (root/"raw"/imported["source_sha256"]).write_bytes(b"altered original")
    assert c.post(base+"/calculations/"+model,json=inputs).status_code==422

@pytest.mark.parametrize("contents,filename",[(b"not JSON","study.json"),(b"{}","study.json"),(b"\xff","study.json"),(b"{}","study.txt")])
def test_invalid_study_import_does_not_create_dataset(api_setup,contents,filename):
    c,p,base,d,store,root=api_setup;before=c.get(base+"/datasets").json()
    assert c.post(base+"/research/anomaly/imports",files={"file":(filename,contents,"application/json")}).status_code==422
    assert c.get(base+"/datasets").json()==before

def test_study_import_requires_owned_geometry_and_limits(api_setup):
    c,p,base,d,store,root=api_setup
    data=draft("anomaly")
    assert c.post(base+"/research/anomaly/imports",files={"file":("study.json",json.dumps(data),"application/json")}).status_code==404
    assert c.post(base+"/research/anomaly/imports",files={"file":("huge.json",b" "*(2*1024*1024+1),"application/json")}).status_code==413


@pytest.mark.parametrize("field",["inlet_kg_s","outlet_kg_s","transfer_into_kg_s","contained_mass_kg"])
def test_missing_balance_values_remain_null(field):
    samples=draft("anomaly")["samples"];samples[7][field]=None
    r=run("anomaly",samples=samples)
    assert r["history"][6]["residual_kg_s"] is None and r["unknown_intervals"]==2
def test_missing_native_acceleration_preserved():
    sensor={"name":"Missing native","axis":"axial_acceleration","units":"m_s2","provenance":"Synthetic missing fixture","calibration_note":"Fixture","anti_alias_bandwidth_hz":10.,"samples":[{"time_s":0.,"value":None,"quality":"missing"},{"time_s":.001,"value":1.,"quality":"accepted"}]}
    result=run("dynamics",sensors=[sensor])["sensor_review"][0]
    assert result["samples"][0]["value"] is None and result["rms"] is None
def test_supervisory_pressure_envelope_limits():
    v=value("supervision");r=request(v)
    assert not SimulationGateway(v).validate(r,1.,pressure_pa=25e6)["accepted_in_simulation"]
    assert not SimulationGateway(v).validate(r,1.,pressure_pa=math.nan)["accepted_in_simulation"]
    r=run("supervision",initial_pressure_pa=25e6)
    assert r["status"]=="outside_scenario_envelope" and r["pressure_envelope_exceeded"]


def test_coupled_modal_eigenproblem_and_orthogonality():
    v=value("dynamics");m,k,c,eigen=matrices(v)
    normalized=[[k[i][j]/math.sqrt(m[i]*m[j]) for j in range(3)] for i in range(3)]
    trace=sum(normalized[i][i] for i in range(3))
    assert sum(e[0] for e in eigen)==pytest.approx(trace,rel=1e-12)
    for lam,vec in eigen:
        assert [sum(normalized[i][j]*vec[j] for j in range(3)) for i in range(3)]==pytest.approx([lam*x for x in vec],abs=1e-8)
        assert sum(x*x for x in vec)==pytest.approx(1.)
    assert sum(x*y for x,y in zip(eigen[0][1],eigen[1][1]))==pytest.approx(0.,abs=1e-14)
def test_km_degenerate_endpoint_intervals_withheld():
    runs=draft("bit-condition")["runs"]
    for row in runs:row["termination"]="confirmed_failure"
    profile=kaplan_meier([BitRun.model_validate(row) for row in runs])
    assert profile[-1]["survival"]==0.
    assert profile[-1]["approximate_lower"] is None and profile[-1]["approximate_upper"] is None
