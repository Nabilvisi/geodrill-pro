"""Causal read-only mass-balance replay and independently labelled event evaluation."""
from typing import Literal
from pydantic import Field,model_validator
from .models import Contract
from .research_common import StudyInput,base

class BalanceSample(Contract):
    time_s: float = Field(ge=0,le=1e7)
    inlet_kg_s: float | None = Field(default=None,ge=-1e7,le=1e7)
    outlet_kg_s: float | None = Field(default=None,ge=-1e7,le=1e7)
    transfer_into_kg_s: float | None = Field(default=None,ge=-1e7,le=1e7)
    contained_mass_kg: float | None = Field(default=None,ge=-1e9,le=1e12)
    pump_on: bool
    operation: Literal["circulating","transfer","connection","static","unknown"]
    quality: Literal["accepted","suspect","missing"]
class AdjudicatedEvent(Contract):
    name: str = Field(min_length=1,max_length=80)
    onset_s: float = Field(ge=0,le=1e7)
    end_s: float = Field(ge=0,le=1e7)
    baseline_alarm_s: float | None = Field(default=None,ge=0,le=1e7)
    evidence_note: str = Field(min_length=3,max_length=500)
    @model_validator(mode="after")
    def interval(self):
        if self.end_s<self.onset_s:raise ValueError("Adjudicated event end precedes onset.")
        return self

class AnomalyInput(StudyInput):
    control_volume_note: str = Field(min_length=10,max_length=500)
    instrument_calibration_note: str = Field(min_length=3,max_length=500)
    maximum_gap_s: float = Field(gt=0,le=60)
    meter_allowance_kg_s: float = Field(ge=0,le=1e5)
    residual_threshold_kg_s: float = Field(gt=0,le=1e5)
    persistence_s: float = Field(gt=0,le=600)
    samples: list[BalanceSample] = Field(min_length=3,max_length=5000)
    adjudicated_events: list[AdjudicatedEvent] = Field(default_factory=list,max_length=100)
    adjudication_note: str | None = Field(default=None,min_length=3,max_length=500)
    @model_validator(mode="after")
    def timing(self):
        if any(b.time_s<=a.time_s for a,b in zip(self.samples,self.samples[1:])):raise ValueError("Balance replay times must strictly increase.")
        if self.adjudicated_events and not self.adjudication_note:raise ValueError("Labelled events need independent adjudication provenance.")
        if any(e.onset_s<self.samples[0].time_s or e.end_s>self.samples[-1].time_s for e in self.adjudicated_events):raise ValueError("Event labels must lie within the preserved replay.")
        return self

def anomaly(v,geometry,path):
    out=base("M15-mass-balance-shadow-1","Read-only causal mass-balance intervals; native flow/storage timing and transparent residual alarms. No influx/loss diagnosis.",["Unknown balance is not evidence of no influx.","Unexplained residuals are not unique to influx/loss; compression, temperature, heave and unknown transfers are not identified.","Event metrics describe only this supplied labelled replay; no calibrated probabilities or early-kick performance claim."])
    if v.evidence_state=="unknown":return {**out,"status":"withheld","reasons":["Instrument/control-volume evidence unknown."]}
    rows=[];events=[];run_start=None;alarm=None;duration=0.;previous_sign=0;valid_duration=0.
    for a,b in zip(v.samples,v.samples[1:]):
        dt=b.time_s-a.time_s
        quality=dt<=v.maximum_gap_s and all(s.quality=="accepted" and all(x is not None and x>=0 for x in (s.inlet_kg_s,s.outlet_kg_s,s.contained_mass_kg)) and s.transfer_into_kg_s is not None for s in (a,b))
        eligible=quality and all(s.operation=="circulating" and s.pump_on for s in (a,b))
        residual=None
        if quality:
            flow=((a.inlet_kg_s+b.inlet_kg_s)-(a.outlet_kg_s+b.outlet_kg_s)+(a.transfer_into_kg_s+b.transfer_into_kg_s))/2
            residual=flow-(b.contained_mass_kg-a.contained_mass_kg)/dt
        excess=eligible and abs(residual)-v.meter_allowance_kg_s>=v.residual_threshold_kg_s
        sign=1 if residual is not None and residual>=0 else -1
        if eligible:valid_duration+=dt
        if not excess or sign!=previous_sign:
            if alarm is not None:events.append({"onset_s":run_start,"alarm_s":alarm,"end_s":a.time_s,"sign":previous_sign})
            run_start=None;alarm=None;duration=0.
        if excess:
            if run_start is None:run_start=a.time_s
            duration+=dt;previous_sign=sign
            if duration>=v.persistence_s and alarm is None:alarm=b.time_s
        rows.append({"time_s":b.time_s,"inlet_kg_s":b.inlet_kg_s if b.quality=="accepted" and b.inlet_kg_s is not None and b.inlet_kg_s>=0 else None,"outlet_kg_s":b.outlet_kg_s if b.quality=="accepted" and b.outlet_kg_s is not None and b.outlet_kg_s>=0 else None,"transfer_into_kg_s":b.transfer_into_kg_s if b.quality=="accepted" else None,"contained_mass_kg":b.contained_mass_kg if b.quality=="accepted" and b.contained_mass_kg is not None and b.contained_mass_kg>=0 else None,"interval_start_s":a.time_s,"residual_kg_s":residual,"meter_lower_kg_s":None if residual is None else residual-v.meter_allowance_kg_s,"meter_upper_kg_s":None if residual is None else residual+v.meter_allowance_kg_s,"quality_status":"eligible" if eligible else "balance_only" if quality else "unknown_balance","candidate_alarm_active":alarm is not None,"causal_available_at_s":b.time_s})
    if alarm is not None:events.append({"onset_s":run_start,"alarm_s":alarm,"end_s":v.samples[-1].time_s,"sign":previous_sign})
    used=set();matches=[];misses=[]
    for label in v.adjudicated_events:
        candidates=[(i,e) for i,e in enumerate(events) if i not in used and label.onset_s<=e["alarm_s"]<=label.end_s]
        if candidates:
            i,e=min(candidates,key=lambda ie:ie[1]["alarm_s"]);used.add(i)
            matches.append({"label":label.name,"candidate_alarm_s":e["alarm_s"],"detection_delay_s":e["alarm_s"]-label.onset_s,"lead_vs_baseline_s":None if label.baseline_alarm_s is None else label.baseline_alarm_s-e["alarm_s"]})
        else:misses.append(label.name)
    out.update(history=rows,candidate_events=events,valid_monitoring_duration_s=valid_duration,unknown_intervals=sum(r["quality_status"]=="unknown_balance" for r in rows),event_evaluation={"status":"supplied_replay_only" if v.adjudicated_events else "unlabelled","matched":matches,"missed_labels":misses,"event_sensitivity":len(matches)/len(v.adjudicated_events) if v.adjudicated_events else None,"unmatched_candidate_events":len(events)-len(used) if v.adjudicated_events else None,"false_candidates_per_monitoring_hour":(len(events)-len(used))/(valid_duration/3600) if v.adjudicated_events and valid_duration else None},probabilities_calibrated=False,actuation_available=False)
    if any(r["quality_status"]=="unknown_balance" for r in rows):out["reasons"].append("Gaps or suspect/missing/negative observations interrupt alarm persistence; no interpolation used.")
    return out
