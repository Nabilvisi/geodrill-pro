"""Software-only supervisory plant/controller and independent request-boundary research.
There is no network adapter, equipment handle or command-execution route.
"""
import hashlib,json,math
from typing import Literal
from pydantic import Field,model_validator
from .models import Contract
from .research_common import StudyInput,base

class RequestExample(Contract):
    request_id: str = Field(min_length=1,max_length=80)
    issued_at_s: float = Field(ge=0,le=1e6)
    expires_at_s: float = Field(ge=0,le=1e6)
    target: str = Field(min_length=1,max_length=80)
    units: str = Field(min_length=1,max_length=80)
    value: float = Field(ge=-1e9,le=1e9)
    evidence_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
class SimulationFault(Contract):
    start_s: float = Field(ge=0,le=600)
    end_s: float = Field(gt=0,le=600)
    kind: Literal["disconnect","manual_override","interlock_open","unknown_outcome","controller_reset"]
    @model_validator(mode="after")
    def interval(self):
        if self.end_s<=self.start_s:raise ValueError("Fault end must follow start.")
        return self

class SupervisionInput(StudyInput):
    authority_mode: Literal["none","simulation_lease"]
    plant_note: str = Field(min_length=3,max_length=500)
    target_pressure_pa: float = Field(ge=0,le=1e8)
    minimum_simulated_pressure_pa: float = Field(ge=0,le=1e8)
    maximum_simulated_pressure_pa: float = Field(gt=0,le=2e8)
    pressure_envelope_note: str = Field(min_length=3,max_length=500)
    initial_pressure_pa: float = Field(ge=0,le=1e8)
    plant_zero_pressure_pa: float = Field(ge=0,le=1e8)
    plant_gain_pa: float = Field(gt=0,le=1e8)
    plant_time_constant_s: float = Field(gt=0,le=100)
    proportional_per_pa: float = Field(ge=0,le=.001)
    integral_per_pa_s: float = Field(ge=0,le=.001)
    derivative_s_per_pa: float = Field(ge=0,le=.001)
    actuator_minimum: float = Field(ge=0,le=1)
    actuator_maximum: float = Field(ge=0,le=1)
    actuator_rate_per_s: float = Field(gt=0,le=10)
    transport_delay_s: float = Field(ge=0,le=10)
    request_ttl_s: float = Field(gt=0,le=30)
    simulation_lease_expires_s: float = Field(ge=0,le=600)
    maximum_requests_per_s: float = Field(gt=0,le=1000)
    manual_override_position: float = Field(ge=0,le=1)
    duration_s: float = Field(gt=0,le=600)
    time_step_s: float = Field(ge=.001,le=1)
    refinement_pressure_tolerance_pa: float = Field(gt=0,le=1e7)
    faults: list[SimulationFault] = Field(default_factory=list,max_length=50)
    request_examples: list[RequestExample] = Field(default_factory=list,max_length=50)
    @model_validator(mode="after")
    def limits(self):
        if not self.minimum_simulated_pressure_pa<=self.target_pressure_pa<=self.maximum_simulated_pressure_pa or self.maximum_simulated_pressure_pa<=self.minimum_simulated_pressure_pa:raise ValueError("Simulated pressure envelope must contain the target and be ordered.")
        if self.actuator_maximum<=self.actuator_minimum:raise ValueError("Actuator bounds must be ordered.")
        if not self.actuator_minimum<=self.manual_override_position<=self.actuator_maximum:raise ValueError("Manual simulation position outside bounds.")
        if any(f.end_s>self.duration_s for f in self.faults):raise ValueError("Fault lies outside simulation.")
        if self.duration_s/self.time_step_s>30000:raise ValueError("Supervisory simulation work budget exceeded.")
        return self

def evidence_digest(v):
    # Approval simulation binds the exact plant/target/geometry configuration, not a mutable name.
    data=v.model_dump(exclude={"study_name","request_examples"})
    return hashlib.sha256(json.dumps(data,sort_keys=True,separators=(",",":")).encode()).hexdigest()

class SimulationGateway:
    def __init__(self,v):
        self.v=v;self.digest=evidence_digest(v);self.seen=set();self.last_at=None;self.last_value=v.actuator_minimum
    def validate(self,request,now,connected=True,ready=True,manual=False,known=True,current_value=None,elapsed_s=None,pressure_pa=None):
        reasons=[];v=self.v
        if v.authority_mode!="simulation_lease" or now>=v.simulation_lease_expires_s:reasons.append("No active simulation lease.")
        if pressure_pa is not None and (not math.isfinite(pressure_pa) or not v.minimum_simulated_pressure_pa<=pressure_pa<=v.maximum_simulated_pressure_pa):reasons.append("Simulated process pressure outside the declared envelope.")
        if not connected:reasons.append("Disconnected; pending simulation requests discarded.")
        if not ready:reasons.append("Interlock/readiness not satisfied.")
        if manual:reasons.append("Manual override removes simulation authority.")
        if not known:reasons.append("Controller outcome/state unknown.")
        if request.target!="simulated-choke-01" or request.units!="normalized_fraction":reasons.append("Target/unit allowlist mismatch.")
        if request.evidence_digest!=self.digest:reasons.append("Evidence/configuration digest changed.")
        if not request.issued_at_s<=now<request.expires_at_s or request.expires_at_s-request.issued_at_s>v.request_ttl_s+1e-9:reasons.append("Request timing/expiry invalid.")
        if request.request_id in self.seen:reasons.append("Duplicate request ID.")
        if not v.actuator_minimum<=request.value<=v.actuator_maximum:reasons.append("Actuator envelope exceeded.")
        if self.last_at is not None:
            dt=now-self.last_at
            if dt<1/v.maximum_requests_per_s-1e-9:reasons.append("Request rate limit exceeded.")
            if dt<=0 or abs(request.value-self.last_value)>v.actuator_rate_per_s*dt+1e-8:reasons.append("Actuator slew limit exceeded.")
        if self.last_at is None and abs(request.value-v.actuator_minimum)>v.actuator_rate_per_s*now+1e-8:reasons.append("Initial actuator slew limit exceeded.")
        if current_value is not None and elapsed_s is not None and abs(request.value-current_value)>v.actuator_rate_per_s*elapsed_s+1e-8:reasons.append("Physical simulated actuator slew envelope exceeded.")
        if not reasons:
            self.seen.add(request.request_id);self.last_at=now;self.last_value=request.value
        return {"request_id":request.request_id,"at_s":now,"accepted_in_simulation":not reasons,"reasons":reasons,"equipment_command_issued":False}

def simulate(v,step):
    n=math.ceil(v.duration_s/step);h=v.duration_s/n
    if n>60000:raise ValueError("Refined simulation work budget exceeded.")
    gate=SimulationGateway(v);p=v.initial_pressure_pa;u=v.actuator_minimum;integral=0.;previous_error=v.target_pressure_pa-p;rows=[];pending=[];events=[];connected_previous=True;permitted_previous=True;demand=v.actuator_minimum
    for j in range(n+1):
        t=j*h;active={f.kind for f in v.faults if f.start_s<=t<f.end_s}
        connected="disconnect" not in active;manual="manual_override" in active;known="unknown_outcome" not in active and "controller_reset" not in active;ready="interlock_open" not in active
        permitted=connected and ready and known and not manual
        if not permitted or not permitted_previous:
            pending=[] # All authority/state faults invalidate queued requests before reconnect.
            demand=u
        permitted_previous=permitted;connected_previous=connected
        if manual:u=v.manual_override_position;demand=u
        error=v.target_pressure_pa-p;trial=integral+error*h;derivative=(error-previous_error)/h if j else 0.
        raw=v.proportional_per_pa*error+v.integral_per_pa_s*trial+v.derivative_s_per_pa*derivative
        clamped=max(v.actuator_minimum,min(v.actuator_maximum,raw))
        if raw==clamped or (raw>clamped and error<0) or (raw<clamped and error>0):integral=trial
        # Generated request is bounded; validator independently checks the resulting value.
        requested=max(demand-v.actuator_rate_per_s*(h if j else 0.),min(demand+v.actuator_rate_per_s*(h if j else 0.),clamped));demand=requested
        request=RequestExample(request_id="sim-"+str(j),issued_at_s=t,expires_at_s=t+v.request_ttl_s,target="simulated-choke-01",units="normalized_fraction",value=requested,evidence_digest=gate.digest)
        if permitted:pending.append((t+v.transport_delay_s,request))
        else:events.append(gate.validate(request,t,connected,ready,manual,known,current_value=u,elapsed_s=h,pressure_pa=p))
        due=[entry for entry in pending if entry[0]<=t+1e-10];pending=[entry for entry in pending if entry[0]>t+1e-10]
        for _,req in due:
            result=gate.validate(req,t,connected,ready,manual,known,current_value=u,elapsed_s=h,pressure_pa=p);events.append(result)
            if result["accepted_in_simulation"]:u=req.value
        rows.append({"time_s":t,"pressure_pa":p,"target_pressure_pa":v.target_pressure_pa,"error_pa":error,"simulated_actuator_fraction":u,"requested_fraction":requested,"connected":connected,"manual_override":manual,"state_known":known})
        if j==n:break
        equilibrium=v.plant_zero_pressure_pa+v.plant_gain_pa*u
        p=equilibrium+(p-equilibrium)*math.exp(-h/v.plant_time_constant_s)
        previous_error=error
    return rows,events

def supervision(v,geometry,path):
    out=base("M17-software-simulation-1","Software-only pressure plant/PID tracking and independent simulated request validation; no rig network interface or equipment writes.",["Plant dynamics are supplied scenario parameters, not an identified/qualified rig.","No OEM, HIL, operator authorization or functional-safety claim; live supervisory integration remains unavailable.","Disconnect/override responses here are explicit simulation assumptions, not a universal process fallback."])
    out.update(equipment_control=False,network_adapter_available=False,simulation_evidence_digest=evidence_digest(v))
    if v.evidence_state=="unknown":return {**out,"status":"withheld","reasons":["Plant/authority scenario evidence unknown."]}
    a,_=simulate(v,v.time_step_s);b,events=simulate(v,v.time_step_s/2)
    errors=[];j=0
    for row in a:
        while j+1<len(b)-1 and b[j+1]["time_s"]<row["time_s"]:j+=1
        left,right=b[j:j+2];f=(row["time_s"]-left["time_s"])/(right["time_s"]-left["time_s"])
        errors.append(abs(row["pressure_pa"]-(left["pressure_pa"]+f*(right["pressure_pa"]-left["pressure_pa"]))))
    gate=SimulationGateway(v);examples=[gate.validate(r,r.issued_at_s,pressure_pa=v.initial_pressure_pa) for r in v.request_examples]
    out.update(history=b,request_audit=events,request_example_audit=examples,accepted_simulation_requests=sum(e["accepted_in_simulation"] for e in events),rejected_simulation_requests=sum(not e["accepted_in_simulation"] for e in events),tracking_rms_pa=math.sqrt(sum(r["error_pa"]**2 for r in b)/len(b)),maximum_overshoot_pa=max(0.,max(r["pressure_pa"]-r["target_pressure_pa"] for r in b)),refinement_change_pa=max(errors),pressure_envelope_exceeded=any(not v.minimum_simulated_pressure_pa<=row["pressure_pa"]<=v.maximum_simulated_pressure_pa for row in b),minimum_pressure_pa=min(row["pressure_pa"] for row in b),maximum_pressure_pa=max(row["pressure_pa"] for row in b),maximum_actuator_fraction=max(r["simulated_actuator_fraction"] for r in b),final_pressure_pa=b[-1]["pressure_pa"])
    if out["refinement_change_pa"]>v.refinement_pressure_tolerance_pa:out.update(status="incomplete_assessment",reasons=["Controller/plant time-step refinement exceeds supplied tolerance."])
    if out.get("pressure_envelope_exceeded"):out.update(status="outside_scenario_envelope",reasons=[*out["reasons"],"Simulated process pressure exceeds the supplied scenario envelope; no protective control is inferred."])
    return out
