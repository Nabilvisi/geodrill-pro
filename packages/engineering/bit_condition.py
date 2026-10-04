"""Inspected bit-run records, descriptive exposure, censored survival and conditional costs."""
import math
from datetime import datetime
from typing import Literal
from pydantic import Field,model_validator
from .models import Contract
from .research_common import StudyInput,base

def timestamp(value):
    try:t=datetime.fromisoformat(value.replace("Z","+00:00"))
    except ValueError as e:raise ValueError("Use ISO 8601 timestamps with timezone.") from e
    if t.tzinfo is None:raise ValueError("Run timestamps need explicit timezone.")
    return t.timestamp()

class BitRun(Contract):
    run_id: str = Field(min_length=1,max_length=80)
    well: str = Field(min_length=1,max_length=100)
    bit_serial: str = Field(min_length=1,max_length=100)
    bit_family: str = Field(min_length=1,max_length=100)
    formation: str = Field(min_length=1,max_length=100)
    completed_at: str
    available_at: str
    drilling_hours: float = Field(gt=0,le=10000)
    drilled_m: float = Field(ge=0,le=30000)
    recovered: bool
    termination: Literal["confirmed_failure","planned_trip","ongoing","unknown"]
    inspection_grade: str | None = Field(default=None,min_length=1,max_length=100)
    inspection_note: str | None = Field(default=None,min_length=3,max_length=500)
    photograph_reference: str | None = Field(default=None,max_length=500)
    mechanical_energy_j: float | None = Field(default=None,ge=0,le=1e15)
    energy_basis: Literal["not_supplied","measured_bit","surface_proxy"]
    evidence_note: str = Field(min_length=3,max_length=500)
    @model_validator(mode="after")
    def records(self):
        if timestamp(self.available_at)<timestamp(self.completed_at):raise ValueError("Evidence availability cannot precede run observation completion.")
        if self.termination=="confirmed_failure" and (not self.recovered or not self.inspection_grade or not self.inspection_note):raise ValueError("Confirmed failures require recovered inspected evidence.")
        if self.inspection_grade and (not self.recovered or not self.inspection_note):raise ValueError("Inspection grade needs recovered bit and inspection evidence.")
        if (self.mechanical_energy_j is None)!=(self.energy_basis=="not_supplied"):raise ValueError("Energy value and measured/proxy basis must agree.")
        return self

class BitInput(StudyInput):
    cutoff_at: str
    bit_family: str = Field(min_length=1,max_length=100)
    formation: str = Field(min_length=1,max_length=100)
    current_drilling_hours: float = Field(ge=0,le=10000)
    horizon_hours: float = Field(gt=0,le=1000)
    immediate_trip_cost: float = Field(ge=0,le=1e9)
    unplanned_failure_cost: float = Field(ge=0,le=1e9)
    continuation_cost_per_hour: float = Field(ge=0,le=1e8)
    cost_currency: str = Field(pattern=r"^[A-Z]{3}$")
    cost_note: str = Field(min_length=3,max_length=500)
    runs: list[BitRun] = Field(min_length=1,max_length=500)
    @model_validator(mode="after")
    def records(self):
        timestamp(self.cutoff_at)
        if len({r.run_id for r in self.runs})!=len(self.runs):raise ValueError("Run IDs must be unique.")
        return self

def kaplan_meier(runs):
    times=sorted(set(r.drilling_hours for r in runs));survival=1.;greenwood=0.;rows=[]
    for t in times:
        risk=sum(r.drilling_hours>=t for r in runs)
        failed=sum(r.drilling_hours==t and r.termination=="confirmed_failure" for r in runs)
        censored=sum(r.drilling_hours==t and r.termination!="confirmed_failure" for r in runs)
        if failed:
            survival*=1-failed/risk
            if risk>failed:greenwood+=failed/(risk*(risk-failed))
        variance=survival*survival*greenwood if survival else 0.
        error=1.96*math.sqrt(variance)
        intervals_valid=0<survival<1
        rows.append({"drilling_hours":t,"at_risk":risk,"failures":failed,"censored":censored,"survival":survival,"greenwood_variance":variance,"approximate_lower":max(0.,survival-error) if intervals_valid else None,"approximate_upper":min(1.,survival+error) if intervals_valid else None})
    return rows

def bit_condition(v,geometry,path):
    out=base("M13-run-cohort-1","Inspected run records and descriptive, right-censored within-family/formation Kaplan–Meier cohort; conditional cost comparison.",["Cohort survival is uncalibrated descriptive evidence, not individual remaining life or a trip authorization.","Mechanical energy is exposure; surface energy remains a proxy and does not measure wear.","No held-out-well calibration corpus is supplied. Cost assumptions are user inputs."])
    cutoff=timestamp(v.cutoff_at)
    eligible=[r for r in v.runs if timestamp(r.available_at)<=cutoff and r.bit_family==v.bit_family and r.formation==v.formation and r.termination!="unknown"]
    out["run_records"]=[{**r.model_dump(),"average_rop_m_h":r.drilled_m/r.drilling_hours,"included_in_cohort":r in eligible} for r in v.runs]
    out["excluded_runs"]=[{"run_id":r.run_id,"reason":"Future receipt/completion, different stratum, or unknown termination"} for r in v.runs if r not in eligible]
    if v.evidence_state=="unknown" or len(eligible)<3:
        return {**out,"status":"withheld","reasons":["Known evidence and at least three eligible records in one bit/formation stratum required."]}
    out["censoring_assumption"]="Independent censoring assumed; planned trips may be informative. Normal Greenwood limits are descriptive, especially at endpoints."
    profile=kaplan_meier(eligible);out["profile"]=profile;out["cohort_size"]=len(eligible)
    out["confirmed_failures"]=sum(r.termination=="confirmed_failure" for r in eligible)
    def survival(t):
        rows=[r for r in profile if r["drilling_hours"]<=t];return rows[-1]["survival"] if rows else 1.
    now=v.current_drilling_hours;future=now+v.horizon_hours
    if future>profile[-1]["drilling_hours"] or survival(now)<=0 or not out["confirmed_failures"]:
        out.update(cost_comparison={"status":"withheld","reason":"Horizon exceeds observed support, no survivors at current age, or no confirmed failures."})
    else:
        probability=1-survival(future)/survival(now)
        out.update(cost_comparison={"status":"conditional_unvalidated","horizon_failure_fraction":probability,"continue_expected_cost":probability*v.unplanned_failure_cost+v.horizon_hours*v.continuation_cost_per_hour,"immediate_trip_cost":v.immediate_trip_cost,"currency":v.cost_currency,"recommended_action":None})
    out["calibration_performed"]=False;return out
