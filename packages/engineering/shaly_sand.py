"""Thomas-Stieber volume construction; interpretation scenarios, not topology acceptance."""
import itertools
import math
from typing import Literal
from pydantic import Field, model_validator
from .models import Contract

SOURCE="https://patents.google.com/patent/AU2013315927B2/en"
EPS=1e-9

class PorosityCurve(Contract):
    curve: str = Field(min_length=1,max_length=80)
    unit: Literal["V/V","PU","%"]
    basis: Literal["total"] = "total"
    uncertainty: float = Field(ge=0,le=20)  # in selected source units
    source_note: str = Field(min_length=3,max_length=400)

    @model_validator(mode="after")
    def uncertainty_units(self):
        if self.uncertainty*(1 if self.unit=="V/V" else .01)>.2:
            raise ValueError("Porosity sensitivity perturbation is limited to 0.2 fractional porosity.")
        return self

class ShaleCurve(Contract):
    curve: str = Field(min_length=1,max_length=80)
    unit: Literal["V/V","PU","%","API"]
    method: Literal["supplied_volume","linear_gr"]
    uncertainty: float = Field(ge=0,le=200)
    calibration_note: str = Field(min_length=3,max_length=400)

    @model_validator(mode="after")
    def compatible(self):
        if (self.method=="linear_gr") != (self.unit=="API"):
            raise ValueError("Linear GR requires API units; supplied shale volume requires V/V, PU or %.")
        if self.method=="supplied_volume" and self.uncertainty*(1 if self.unit=="V/V" else .01)>1:
            raise ValueError("Shale-volume perturbation cannot exceed one bulk-rock volume fraction.")
        return self

class ShaleEndpoints(Contract):
    sand_porosity: float = Field(ge=.001,le=.65)
    shale_porosity: float = Field(ge=0,le=.65)
    sand_porosity_uncertainty: float = Field(ge=0,le=.2)
    shale_porosity_uncertainty: float = Field(ge=0,le=.2)
    gr_clean_api: float = Field(ge=0,le=1000)
    gr_shale_api: float = Field(ge=0,le=1000)
    gr_clean_uncertainty_api: float = Field(ge=0,le=200)
    gr_shale_uncertainty_api: float = Field(ge=0,le=200)
    source_note: str = Field(min_length=3,max_length=400)
    porosity_convention_note: str = Field(min_length=3,max_length=400)

    @model_validator(mode="after")
    def ordered(self):
        if not .001<=self.sand_porosity-self.sand_porosity_uncertainty <= self.sand_porosity+self.sand_porosity_uncertainty<=.65:
            raise ValueError("Sand-porosity perturbations must remain in the numerical endpoint envelope.")
        if self.shale_porosity-self.shale_porosity_uncertainty<0 or self.shale_porosity+self.shale_porosity_uncertainty>.65:
            raise ValueError("Shale-porosity perturbations must remain physically admissible.")
        if self.gr_clean_api-self.gr_clean_uncertainty_api<0 or self.gr_shale_api+self.gr_shale_uncertainty_api>1000:
            raise ValueError("GR endpoint perturbations must remain in the declared numerical envelope.")
        if self.gr_shale_api-self.gr_shale_uncertainty_api <= self.gr_clean_api+self.gr_clean_uncertainty_api:
            raise ValueError("Clean/shale GR endpoint perturbations must retain a positive separation.")
        return self

class ShalySandInput(Contract):
    study_name: str = Field(min_length=3,max_length=100)
    dataset_id: str = Field(min_length=1,max_length=80)
    geometry_revision_id: str = Field(min_length=1,max_length=80)
    depth_datum: str = Field(min_length=1,max_length=100)
    porosity: PorosityCurve
    shale_indicator: ShaleCurve
    endpoints: ShaleEndpoints
    correction_status: Literal["supplied_corrected","raw","unknown","synthetic"]
    correction_note: str = Field(min_length=3,max_length=400)
    acquisition_quality_note: str = Field(min_length=3,max_length=400)
    depth_alignment_note: str = Field(min_length=3,max_length=400)
    mineral_fluid_note: str = Field(min_length=3,max_length=400)

def fractional(value,unit):
    return value if unit=="V/V" else value/100.

def volume_scenario(vsh,total,sand_phi,shale_phi):
    """Algebraically invert a defined wet-shale + primary-pore volume construction."""
    if not all(math.isfinite(x) for x in (vsh,total,sand_phi,shale_phi)):
        return None
    if not -EPS<=vsh<=1+EPS or not -EPS<=total<=1+EPS:
        return None
    vsh=min(1.,max(0.,vsh));total=min(1.,max(0.,total))
    effective=total-vsh*shale_phi
    if effective < -EPS or effective>sand_phi+EPS or effective+vsh>1+EPS:
        return None
    effective=max(0.,effective)
    max_lam=min(1-effective/sand_phi,(effective-sand_phi+vsh)/(1-sand_phi))
    if max_lam < -EPS:
        return None
    max_lam=min(1.,max(0.,max_lam))
    def at(lam):
        dispersed=(1-lam)*sand_phi-effective
        structural=vsh-lam-dispersed
        host=1-lam
        return {"laminated_bulk":lam,"dispersed_bulk":max(0.,dispersed),"structural_bulk":max(0.,structural),
                "nonlaminated_host_fraction":host,
                "primary_porosity_host_normalized":None if host<=EPS else effective/host}
    restricted=at(max_lam)
    branch=("laminated" if restricted["dispersed_bulk"]<=EPS and restricted["structural_bulk"]<=EPS else
            "laminated_dispersed" if restricted["structural_bulk"]<=EPS else "laminated_structural")
    family=[at(lam) for lam in sorted({0.,max_lam/2,max_lam})]
    quartz=max(0.,1-vsh-effective)
    reconstructed=(1-restricted["laminated_bulk"])*sand_phi-restricted["dispersed_bulk"]+vsh*shale_phi
    return {"bulk_shale_volume":vsh,"total_porosity":total,"primary_porosity_bulk":effective,
            "shale_associated_porosity_bulk":vsh*shale_phi,"quartz_grain_fraction":quartz,
            "shale_solid_fraction":vsh*(1-shale_phi),
            "restricted_scenario":{**restricted,"branch":branch},
            "coexistence_family":family,"laminated_range":[0.,max_lam],
            "texture_nonunique":max_lam>EPS,
            "volume_balance_residual":quartz+vsh*(1-shale_phi)+total-1,
            "porosity_residual":total-reconstructed}

def model_grid(sand_phi,shale_phi):
    points=[]
    for branch in ("laminated","dispersed","structural"):
        for i in range(41):
            fraction=i/40
            v=(fraction if branch=="laminated" else fraction*sand_phi if branch=="dispersed" else fraction*(1-sand_phi))
            eff=(1-v)*sand_phi if branch=="laminated" else sand_phi-v if branch=="dispersed" else sand_phi
            points.append({"branch":branch,"shale_volume":v,"primary_porosity":eff,"total_porosity":eff+v*shale_phi})
    return points

def interpret_logs(value:ShalySandInput,rows,curves,total_md):
    if len(rows)>1000:
        raise ValueError("Shaly-sand interpretation is bounded to 1,000 native-depth records; no automatic resampling.")
    units={c["mnemonic"]:c["unit"] for c in curves[1:]}
    for mapping in (value.porosity,value.shale_indicator):
        if units.get(mapping.curve)!=mapping.unit:
            raise ValueError("Curve names and exact source units must match LAS metadata.")
    if value.porosity.curve==value.shale_indicator.curve:
        raise ValueError("Porosity and shale indicator must be distinct curves.")
    ep=value.endpoints
    warnings=["Selected legacy volume model assumes constant sand-framework porosity and equal shale properties for every topology.",
              "The branch is a mathematical scenario, not geological topology acceptance; structural and dispersed shale may coexist.",
              "Primary porosity excludes shale-associated pores by definition; pore connectivity, permeability and reserves are not established.",
              "Sensitivity ranges cover tested parameter corners, not confidence intervals or guaranteed continuous bounds.",
              "Native depths are preserved; no tool/environment correction, depth shift or response-resolution matching is performed."]
    if value.shale_indicator.method=="linear_gr":
        warnings.append("Linear GR is a supplied calibration scenario; gamma ray is not a universal clay/shale volume measurement.")
    correction_ok=value.correction_status in {"supplied_corrected","synthetic"}
    output=[]
    for source_index,row in sorted(enumerate(rows),key=lambda item:item[1]["depth_m"]):
        md=row["depth_m"];phi=row.get(value.porosity.curve);indicator=row.get(value.shale_indicator.curve)
        record={"source_index":source_index,"depth_m":md,"status":"withheld","reason":"","scenario":None,"sensitivity":None}
        reasons=[]
        if not correction_ok: reasons.append("Corrected compatible porosity/shale inputs have not been supplied")
        if md>total_md: reasons.append("Outside saved survey coverage")
        if phi is None or indicator is None: reasons.append("Missing porosity or shale indicator")
        if reasons:
            record["reason"]="; ".join(reasons);output.append(record);continue
        if not math.isfinite(phi) or not math.isfinite(indicator):
            record["reason"]="Nonfinite curve observation";output.append(record);continue
        total=fractional(phi,value.porosity.unit)
        vsh=((indicator-ep.gr_clean_api)/(ep.gr_shale_api-ep.gr_clean_api) if value.shale_indicator.method=="linear_gr" else fractional(indicator,value.shale_indicator.unit))
        scenario=volume_scenario(vsh,total,ep.sand_porosity,ep.shale_porosity)
        if scenario is None:
            record.update(status="outside_applicability",reason="Observation cannot satisfy the selected admissible volume balances; values were not clipped.")
            output.append(record);continue
        tested=[];invalid=0
        corner=lambda c,d:sorted({c-d,c+d})
        for a,b,p,x,g0,g1 in itertools.product(corner(ep.sand_porosity,ep.sand_porosity_uncertainty),
              corner(ep.shale_porosity,ep.shale_porosity_uncertainty),corner(phi,value.porosity.uncertainty),
              corner(indicator,value.shale_indicator.uncertainty),corner(ep.gr_clean_api,ep.gr_clean_uncertainty_api) if value.shale_indicator.method=="linear_gr" else [ep.gr_clean_api],
              corner(ep.gr_shale_api,ep.gr_shale_uncertainty_api) if value.shale_indicator.method=="linear_gr" else [ep.gr_shale_api]):
            vp=(x-g0)/(g1-g0) if value.shale_indicator.method=="linear_gr" else fractional(x,value.shale_indicator.unit)
            item=volume_scenario(vp,fractional(p,value.porosity.unit),a,b)
            if item is None: invalid+=1
            else: tested.append(item)
        fields=("primary_porosity_bulk","quartz_grain_fraction")
        ranges={f:[min(i[f] for i in tested),max(i[f] for i in tested)] for f in fields} if tested else {}
        lam=[i["restricted_scenario"]["laminated_bulk"] for i in tested]
        record.update(status="ambiguous" if scenario["texture_nonunique"] else "scenario_only",
          reason="Admissible under the selected model; interpretation remains unconfirmed.",
          scenario=scenario,sensitivity={"tested_admissible_corners":len(tested),"tested_outside_corners":invalid,
             "restricted_branches":sorted({i["restricted_scenario"]["branch"] for i in tested}),
             "tested_ranges":{**ranges,"restricted_laminated_bulk":[min(lam),max(lam)]} if lam else ranges})
        output.append(record)
    valid=sum(r["scenario"] is not None for r in output)
    return {"model":"thomas-stieber-wet-shale-volume-construction","version":"0.1.0",
            "status":"scenario_only" if valid else "withheld","interpretation_approved":False,
            "reason":"Restricted branch plus admissible coexisting-texture alternatives." if valid else "No eligible interpretations; inspect sample reasons.",
            "source_reference":SOURCE,"porosity_basis":"bulk-rock total and primary-pore fractions; wet-shale pores accounted separately",
            "rows":output,"eligible_count":valid,"withheld_count":len(rows)-valid,
            "ambiguous_count":sum(r["status"]=="ambiguous" for r in output),
            "model_grid":model_grid(ep.sand_porosity,ep.shale_porosity),"warnings":warnings}
