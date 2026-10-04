"""Dilute vertical Stokes-slip tanks with exact discrete solids balance."""
import math
from typing import Literal
from pydantic import Field
from .models import Contract
from .physics import G
from .hydraulics import HydraulicsInput, build_segments
from .stability import tangent

class TransportInput(Contract):
    study_name: str = Field(min_length=3,max_length=100)
    geometry_revision_id: str
    depth_datum: str
    hydraulics_calculation_id: str
    evidence_state: Literal["unknown","supplied","synthetic"] = "unknown"
    source_note: str = Field(min_length=3,max_length=500)
    particle_diameter_m: float = Field(ge=1e-6,le=.05)
    particle_density_kg_m3: float = Field(ge=500,le=10000)
    shape: Literal["sphere","irregular"] = "sphere"
    rop_m_s: float = Field(ge=0,le=.01)
    duration_s: float = Field(gt=0,le=86400)
    generation_stop_s: float = Field(ge=0,le=86400)
    initial_volume_fraction: float = Field(ge=0,le=.05)
    rotation_rad_s: float = Field(ge=0,le=100)
    time_step_s: float = Field(ge=.01,le=600)

def tanks(volumes, rates, generation, duration, stop, initial, dt):
    """Bottom-to-top implicit tanks; every outgoing volume enters the next tank."""
    count=math.ceil(duration/dt)
    if count>20000 or count*len(volumes)>2000000:raise ValueError("Transport scenario exceeds 20,000 time steps.")
    inventory=[initial*v for v in volumes];initial_total=sum(inventory)
    produced=returned=0.;history=[];peak=initial;peak_t=0.;peak_i=0
    # Split exactly at generation stop; never smear an on/off source across a time step.
    times=sorted(set([0.,duration,min(duration,stop)]+[min(duration,j*dt) for j in range(1,count+1)]))
    for start,end in zip(times,times[1:]):
        h=end-start;source=generation*h if start<stop else 0.;produced+=source
        transfer=source
        for i in range(len(volumes)):
            inventory[i]=(inventory[i]+transfer)/(1+h*rates[i])
            transfer=h*rates[i]*inventory[i]
            fraction=inventory[i]/volumes[i]
            if fraction>peak:peak,peak_t,peak_i=fraction,end,i
        returned+=transfer
        if len(history)==0 or end-history[-1]["time_s"]>=duration/120 or end==duration:
            history.append({"time_s":end,"generated_m3":produced,"returned_m3":returned,"inventory_m3":sum(inventory),
                            "maximum_volume_fraction":max(x/v for x,v in zip(inventory,volumes)),
                            "balance_residual_m3":initial_total+produced-returned-sum(inventory)})
    return {"history":history,"inventory_m3":sum(inventory),"generated_m3":produced,"returned_m3":returned,
            "initial_inventory_m3":initial_total,"balance_residual_m3":initial_total+produced-returned-sum(inventory),
            "peak_volume_fraction":peak,"peak_time_s":peak_t,"peak_segment":peak_i,"final_inventory_by_segment_m3":inventory}

def transport(v, geometry, path, hydraulic_input, hydraulic_result):
    h=HydraulicsInput.model_validate(hydraulic_input)
    base={"model_version":"M8-vertical-stokes-tanks-1","approval_issued":False,"equipment_authority":"none",
          "scope":"Vertical dilute spherical particles, Newtonian fluid, independent Stokes settling, well-mixed axial tanks; no horizontal bed model.",
          "hydraulics_calculation_id":v.hydraulics_calculation_id}
    reasons=[]
    if hydraulic_result.get("status")=="withheld":reasons.append("Linked hydraulics is withheld.")
    if h.mud.rheology!="newtonian":reasons.append("Stokes closure requires Newtonian viscosity; non-Newtonian settling is unsupported.")
    if v.evidence_state=="unknown":reasons.append("Cuttings/source evidence unknown.")
    if v.shape!="sphere" or v.rotation_rad_s!=0:reasons.append("Irregular particles and string rotation are unsupported.")
    rho=h.mud.density_kg_m3;mu=h.mud.consistency_pa_sn
    if v.particle_density_kg_m3<=rho:reasons.append("Particles must be denser than the fluid.")
    slip=max(0.,(v.particle_density_kg_m3-rho)*G*v.particle_diameter_m**2/(18*mu))
    re=rho*slip*v.particle_diameter_m/mu
    if re>.1:reasons.append("Particle settling Reynolds number exceeds 0.1; Stokes drag withheld.")
    if reasons:return {**base,"status":"withheld","reasons":reasons,"profile":[],"history":[]}
    segments=build_segments(h,geometry,path)
    # Check endpoints of each exact arc plus any horizontal extremum of tangent z.
    for s in segments:
        lo,hi=s["top_md_m"],s["bottom_md_m"]
        from .hydraulics import derivative_roots
        cuts=[lo,hi,*derivative_roots(path,lo,hi,0.)]
        if min(tangent(path,m)[2] for m in cuts)<math.cos(math.radians(10)):
            return {**base,"status":"withheld","reasons":["Trajectory exceeds 10 degrees inclination; bed transport is unqualified."],"profile":[],"history":[]}
    segs=list(reversed(segments));volumes=[];rates=[];profile=[]
    for s in segs:
        area=math.pi*(s["bore_diameter_m"]**2-s["string_od_m"]**2)/4
        velocity=h.flow_m3_s/area
        cosi=tangent(path,(s["top_md_m"]+s["bottom_md_m"])/2)[2]
        net=max(0.,velocity-slip*cosi)
        volume=area*s["length_m"];volumes.append(volume);rates.append(net/s["length_m"])
        profile.append({"md_m":(s["top_md_m"]+s["bottom_md_m"])/2,"annular_area_m2":area,"fluid_velocity_m_s":velocity,
                        "settling_velocity_m_s":slip,"net_upward_velocity_m_s":net,"tank_volume_m3":volume})
    bottom=segs[0]["bottom_md_m"]
    hole=next(x for x in geometry.hole_sections if x.top_md_m<bottom<=x.bottom_md_m)
    generation=math.pi*hole.diameter_m**2/4*v.rop_m_s
    nominal=tanks(volumes,rates,generation,v.duration_s,v.generation_stop_s,v.initial_volume_fraction,v.time_step_s)
    refined=tanks(volumes,rates,generation,v.duration_s,v.generation_stop_s,v.initial_volume_fraction,v.time_step_s/2)
    for p,inventory in zip(profile,refined["final_inventory_by_segment_m3"]):p["final_volume_fraction"]=inventory/p["tank_volume_m3"]
    eligible=refined["peak_volume_fraction"]<=.05
    return {**base,"status":"research_scenario" if eligible else "outside_dilute_envelope",
            "reasons":[] if eligible else ["Calculated concentration exceeds 5%; dilute closure no longer applicable."],
            "particle_reynolds":re,"generation_m3_s":generation,"settling_velocity_m_s":slip,
            "profile":profile,**refined,
            "time_refinement_return_change_m3":abs(refined["returned_m3"]-nominal["returned_m3"]),
            "hydraulics_within_tested_bounds":hydraulic_result.get("within_all_tested_bounds",False),
            "limitations":["No critical flow recommendation; hydraulic source is retained without changing its flow.",
                          "Tank mixing gives a residence-time distribution, not a sharp front or validated lag.",
                          "Inventory growth at zero upward velocity is an accumulation indicator; no deposited-bed closure."]}
