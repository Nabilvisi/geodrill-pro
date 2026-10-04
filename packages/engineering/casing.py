"""Restricted body/connection screens; never a complete casing design approval."""
import math
from pydantic import Field, model_validator
from .models import Contract
from .geometry import GeometryInput


class CasingLoad(Contract):
    name: str = Field(min_length=1, max_length=80)
    casing_name: str = Field(min_length=1, max_length=80)
    md_m: float = Field(ge=0, le=30000)
    internal_gauge_pa: float = Field(ge=0, le=1e9)
    external_gauge_pa: float = Field(ge=0, le=1e9)
    axial_wall_force_n: float = Field(ge=-1e9, le=1e9)
    source: str = Field(min_length=3, max_length=300)


class CasingCheckInput(Contract):
    geometry_revision_id: str = Field(min_length=1, max_length=80)
    candidate_name: str = Field(min_length=1, max_length=100)
    required_load_cases: list[str] = Field(min_length=1, max_length=30)
    loads: list[CasingLoad] = Field(min_length=1, max_length=300)
    yield_factor: float = Field(ge=1, le=10)
    burst_factor: float = Field(ge=1, le=10)
    collapse_factor: float = Field(ge=1, le=10)
    axial_factor: float = Field(ge=1, le=10)
    factor_basis: str = Field(min_length=3, max_length=300)
    temperature_derating: float = Field(ge=.001, le=1)
    derating_basis: str = Field(min_length=3, max_length=300)

    @model_validator(mode="after")
    def catalogue(self):
        if any(not x.strip() or len(x)>80 for x in self.required_load_cases):
            raise ValueError("Mandatory load-case names must be nonempty and bounded.")
        if len(set(self.required_load_cases)) != len(self.required_load_cases):
            raise ValueError("Mandatory load-case names must be unique.")
        pairs=[(x.casing_name,x.name) for x in self.loads]
        if len(set(pairs)) != len(pairs):
            raise ValueError("Each casing/load-case pair must appear once.")
        return self


def casing_check(data: CasingCheckInput, geometry: GeometryInput):
    casings={c.name:c for c in geometry.casings}
    if not casings:
        raise ValueError("The referenced geometry revision has no casing records.")
    checks=[]
    missing=[]
    for name in casings:
        for case in data.required_load_cases:
            if not any(x.casing_name==name and x.name==case for x in data.loads):
                missing.append({"casing":name,"load_case":case,"reason":"Mandatory load case is missing."})
    for load in data.loads:
        if load.casing_name not in casings:
            raise ValueError("Load case references an unknown casing in this revision.")
        c=casings[load.casing_name]
        if not c.top_md_m <= load.md_m <= c.bottom_md_m:
            raise ValueError("Load-case MD lies outside its casing interval.")
        wall=c.minimum_wall_m-c.wall_loss_allowance_m
        ro=c.outside_diameter_m/2
        ri=ro-wall
        area=math.pi*(ro*ro-ri*ri)
        pi,po=load.internal_gauge_pa,load.external_gauge_pa
        aa=(pi*ri*ri-po*ro*ro)/(ro*ro-ri*ri)
        bb=(pi-po)*ri*ri*ro*ro/(ro*ro-ri*ri)
        axial=load.axial_wall_force_n/area
        stresses=[]
        for location,r in (("inside",ri),("outside",ro)):
            radial=aa-bb/(r*r)
            hoop=aa+bb/(r*r)
            vm=math.sqrt(((hoop-radial)**2+(radial-axial)**2+(axial-hoop)**2)/2)
            stresses.append({"location":location,"radial_pa":radial,"hoop_pa":hoop,"axial_pa":axial,"von_mises_pa":vm})
        rows=[]
        demands=[("body_yield",max(s["von_mises_pa"] for s in stresses),c.yield_strength_pa,data.yield_factor),
                 ("body_burst",max(pi-po,0.),c.body_burst_pa,data.burst_factor),
                 ("body_collapse",max(po-pi,0.),c.body_collapse_pa,data.collapse_factor),
                 ("body_axial",abs(load.axial_wall_force_n),c.body_tension_n if load.axial_wall_force_n>=0 else c.body_compression_n,data.axial_factor),
                 ("connection_burst",max(pi-po,0.),c.connection_burst_pa,data.burst_factor),
                 ("connection_collapse",max(po-pi,0.),c.connection_collapse_pa,data.collapse_factor),
                 ("connection_axial",abs(load.axial_wall_force_n),c.connection_tension_n if load.axial_wall_force_n>=0 else c.connection_compression_n,data.axial_factor)]
        for kind,demand,rating,factor in demands:
            # Require evidence even for zero demand: omission cannot masquerade as qualification.
            available=rating*data.temperature_derating if rating is not None else None
            utilization=demand*factor/available if available is not None else None
            rows.append({"check":kind,"demand":demand,"rating":rating,"derated_rating":available,
                         "factor":factor,"utilization":utilization,"margin":available/factor-demand if available is not None else None,
                         "status":"insufficient_data" if utilization is None else "outside_applicability" if utilization>1 else "conditional"})
        governing=max((x for x in rows if x["utilization"] is not None),key=lambda x:x["utilization"],default=None)
        incomplete=any(x["utilization"] is None for x in rows)
        exceeds=any(x["utilization"] is not None and x["utilization"]>1 for x in rows)
        checks.append({"casing":c.name,"load_case":load.name,"md_m":load.md_m,"source":load.source,
                       "effective_wall_m":wall,"effective_area_m2":area,"stresses":stresses,"checks":rows,
                       "governing_check":governing["check"] if governing else None,
                       "maximum_utilization":governing["utilization"] if governing else None,
                       "status":"outside_applicability" if exceeds else "insufficient_data" if incomplete else "conditional"})
    has_failure=any(x["status"]=="outside_applicability" for x in checks)
    incomplete=bool(missing) or any(x["status"]=="insufficient_data" for x in checks)
    return {"model":"lame-body-and-supplied-rating-screens","version":"0.2.0",
            "status":"outside_applicability" if has_failure else "insufficient_data" if incomplete else "conditional",
            "candidate_name":data.candidate_name,"design_approval":False,"checks":checks,"missing_load_cases":missing,
            "basis": {"pressure_reference":"gauge at the load-case MD; tension-positive wall stress",
                      "axial_load":"Total wall force, including pressure-end loads when applicable; not effective tension or hookload.",
                      "factors":data.factor_basis,"temperature_derating":data.derating_basis},
            "assumptions":["Long homogeneous isotropic circular tube, uniform pressure, no bending or torsion; Lamé elastic body yield screen.",
                           "Minimum wall less supplied loss allowance is used for the body stress screen.",
                           "Supplied ratings must apply to the remaining wall and service envelope; ratings are not recalculated from nominal grade.",
                           "Body ratings and connection ratings are independent supplied evidence; no combined connection envelope is inferred.",
                           "Uniform user-supplied derating; no temperature profile, collapse interaction, sealing, fatigue, corrosion chemistry or cement-support solver.",
                           "Passing these selected screens is conditional and never a complete design or barrier approval."]}
