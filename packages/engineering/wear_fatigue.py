"""Separate contact wear, Miner exposure and restricted residual-wall screen."""
import math
from typing import Literal
from pydantic import Field,model_validator
from .models import Contract
from .research_common import StudyInput,base

class WearExposure(Contract):
    name: str = Field(min_length=1,max_length=80)
    normal_force_n: float = Field(ge=0,le=1e7)
    sliding_distance_m: float = Field(ge=0,le=1e9)
    duration_s: float = Field(ge=0,le=1e9)
    evidence_note: str = Field(min_length=3,max_length=500)
class FatigueKnot(Contract):
    stress_amplitude_pa: float = Field(gt=0,le=2e9)
    failure_cycles: float = Field(gt=0,le=1e15)
class CycleExposure(Contract):
    stress_amplitude_pa: float = Field(ge=0,le=2e9)
    mean_stress_pa: float = Field(ge=-2e9,le=2e9)
    cycles: float = Field(ge=0,le=1e15)
    evidence_note: str = Field(min_length=3,max_length=500)
class WearInput(StudyInput):
    casing_name: str = Field(min_length=1,max_length=80)
    geometry_assumption: Literal["uniform_wall_loss","localized_groove","unknown"]
    wear_coefficient_m2_n: float | None = Field(default=None,ge=0,le=1e-6)
    wear_coefficient_relative_delta: float = Field(ge=0,le=1)
    wear_material_fluid_note: str | None = Field(default=None,min_length=3,max_length=500)
    contact_patch_area_m2: float = Field(gt=0,le=1e6)
    initial_minimum_wall_m: float = Field(gt=0,le=1)
    unobserved_exposure: bool
    exposures: list[WearExposure] = Field(min_length=1,max_length=200)
    fatigue_material_note: str | None = Field(default=None,min_length=3,max_length=500)
    fatigue_curve: list[FatigueKnot] = Field(default_factory=list,max_length=50)
    cycle_exposures: list[CycleExposure] = Field(default_factory=list,max_length=200)
    internal_gauge_pa: float = Field(ge=0,le=1e9)
    external_gauge_pa: float = Field(ge=0,le=1e9)
    observed_minimum_wall_m: float | None = Field(default=None,gt=0,le=1)
    inspection_uncertainty_m: float = Field(ge=0,le=.1)
    inspection_note: str | None = Field(default=None,min_length=3,max_length=500)
    @model_validator(mode="after")
    def records(self):
        if self.wear_coefficient_m2_n is not None and not self.wear_material_fluid_note:raise ValueError("Wear coefficient needs material/fluid/contact provenance and convention.")
        if self.fatigue_curve:
            if len(self.fatigue_curve)<2 or not self.fatigue_material_note:raise ValueError("Fatigue curve needs two or more points and material/test provenance.")
            if any(b.stress_amplitude_pa<=a.stress_amplitude_pa or b.failure_cycles>=a.failure_cycles for a,b in zip(self.fatigue_curve,self.fatigue_curve[1:])):raise ValueError("S–N curve must have increasing stress and decreasing failure cycles.")
        if self.observed_minimum_wall_m is not None and not self.inspection_note:raise ValueError("Inspected wall requires inspection provenance.")
        return self

def fatigue_cycles(curve,stress):
    if stress==0:return math.inf
    if not curve or stress<curve[0].stress_amplitude_pa or stress>curve[-1].stress_amplitude_pa:raise ValueError("Stress lies outside supplied fatigue curve; no extrapolation.")
    a,b=next((a,b) for a,b in zip(curve,curve[1:]) if a.stress_amplitude_pa<=stress<=b.stress_amplitude_pa)
    f=math.log(stress/a.stress_amplitude_pa)/math.log(b.stress_amplitude_pa/a.stress_amplitude_pa)
    return math.exp(math.log(a.failure_cycles)+f*math.log(b.failure_cycles/a.failure_cycles))

def wear_fatigue(v,geometry,path):
    out=base("M14-separate-exposure-1","Material-specific contact wear and separate Miner cycle exposure; uniform-wall Lamé pressure/yield scenario only.",["No barrier acceptance, remaining-life guarantee or capacity certification.","Wear coefficient m²/N is not an interchangeable dimensionless Archard coefficient.","Miner damage omits sequence, corrosion, cracks and nonzero mean stress; localized grooves require a different residual-strength model."])
    casing=next((c for c in geometry.casings if c.name==v.casing_name),None)
    if casing is None:raise ValueError("Select a casing record in the bound geometry.")
    out["casing_state"]=casing.state
    out["exposure_completeness"]="incomplete" if v.unobserved_exposure else "declared_complete"
    if casing.state=="planned":out["reasons"].append("Planned casing: exposure and remaining-wall results describe a scenario only.")
    nominal=(casing.outside_diameter_m-casing.inside_diameter_m)/2
    if v.initial_minimum_wall_m>nominal+1e-9:raise ValueError("Initial minimum wall exceeds nominal casing wall.")
    exposure=sum(r.normal_force_n*r.sliding_distance_m for r in v.exposures)
    out["contact_work_n_m"]=exposure;out["observed_exposure_duration_s"]=sum(r.duration_s for r in v.exposures)
    if v.evidence_state=="unknown":return {**out,"status":"withheld","reasons":["Material/exposure evidence unknown."]}
    wear=None if v.wear_coefficient_m2_n is None else exposure*v.wear_coefficient_m2_n
    out["wear_volume_m3"]=wear
    remaining=None if wear is None else v.initial_minimum_wall_m-wear/v.contact_patch_area_m2
    conservative=None if wear is None else v.initial_minimum_wall_m-wear*(1+v.wear_coefficient_relative_delta)/v.contact_patch_area_m2
    out.update(predicted_minimum_wall_m=remaining,conservative_minimum_wall_m=conservative)
    if wear is None:out["reasons"].append("Wear coefficient absent: contact exposure retained, wear prediction withheld.")
    damage=0.;fatigue_rows=[];fatigue_reason=None
    for row in v.cycle_exposures:
        try:
            if row.mean_stress_pa!=0:raise ValueError("Nonzero mean stress needs a separately qualified correction.")
            life=fatigue_cycles(v.fatigue_curve,row.stress_amplitude_pa)
            fraction=row.cycles/life;damage+=fraction;fatigue_rows.append({"stress_amplitude_pa":row.stress_amplitude_pa,"applied_cycles":row.cycles,"failure_cycles":None if math.isinf(life) else life,"damage_fraction":fraction})
        except ValueError as error:fatigue_reason=str(error);break
    out["fatigue"]={"status":"withheld" if fatigue_reason or not v.cycle_exposures else "conditional_spectrum","miner_damage":None if fatigue_reason or not v.cycle_exposures else damage,"spectrum":fatigue_rows,"reason":fatigue_reason}
    if damage>=1:out["reasons"].append("Miner index reaches one; it is not a guaranteed physical failure time.")
    capacity={"status":"withheld","reason":"Uniform remaining wall, complete exposure, positive wall and supplied yield property required."}
    if remaining is not None and conservative is not None and conservative>1e-5 and v.geometry_assumption=="uniform_wall_loss" and not v.unobserved_exposure and casing.yield_strength_pa is not None:
        ro=casing.outside_diameter_m/2;ri=ro-conservative
        A=(v.internal_gauge_pa*ri*ri-v.external_gauge_pa*ro*ro)/(ro*ro-ri*ri)
        B=ri*ri*ro*ro*(v.internal_gauge_pa-v.external_gauge_pa)/(ro*ro-ri*ri)
        stresses=[]
        for radius in (ri,ro):
            radial=A-B/radius**2;hoop=A+B/radius**2;axial=A
            stresses.append(math.sqrt(((radial-hoop)**2+(hoop-axial)**2+(axial-radial)**2)/2))
        vm=max(stresses);capacity={"status":"restricted_uniform_wall_scenario","closed_end_von_mises_pa":vm,"yield_margin_pa":casing.yield_strength_pa-vm,"source":casing.body_rating_source,"connection_capacity_assessed":False}
    if capacity["status"]!="withheld" and capacity["yield_margin_pa"]<0:out["reasons"].append("Supplied yield property exceeded in the restricted uniform-wall scenario.")
    out["residual_strength"]=capacity
    if v.unobserved_exposure:out["reasons"].append("Unobserved exposure retained; residual-strength result withheld.")
    if conservative is not None and conservative<=0:out["reasons"].append("Tested wear exhausts initial wall; pressure screen withheld.")
    out["inspection_residual_m"]=None if remaining is None or v.observed_minimum_wall_m is None else v.observed_minimum_wall_m-remaining
    out["inspection_uncertainty_m"]=v.inspection_uncertainty_m
    out["profile"]=[{"md_m":casing.top_md_m,"initial_wall_m":v.initial_minimum_wall_m,"predicted_wall_m":remaining,"conservative_wall_m":conservative},{"md_m":casing.bottom_md_m,"initial_wall_m":v.initial_minimum_wall_m,"predicted_wall_m":remaining,"conservative_wall_m":conservative}]
    return out
