"""M11 straight inclined confined-pipe screening; no operational WOB authority."""
import bisect
import math
from typing import Literal
from pydantic import Field, model_validator
from .models import Contract
from .physics import G
from .stability import tangent
from .torque_drag import TorqueDragInput

REFERENCES = [
    "https://www.bsee.gov/sites/bsee.gov/files/tap-technical-assessment-program/300an.pdf",
    "https://www.sciencedirect.com/science/article/abs/pii/S0920410518304479",
    "https://www.sciencedirect.com/science/article/pii/S0029801818300246",
    "https://link.springer.com/article/10.1007/s13202-025-02009-4",
]

class WallLoad(Contract):
    md_m: float = Field(ge=0,le=30000)
    wall_tension_n: float = Field(ge=-1e7,le=1e7)
    internal_absolute_pa: float = Field(ge=0,le=1e9)
    external_absolute_pa: float = Field(ge=0,le=1e9)

class BucklingInput(Contract):
    study_name: str = Field(min_length=3,max_length=100)
    geometry_revision_id: str
    depth_datum: str
    evidence_state: Literal["unknown","supplied","synthetic"] = "unknown"
    source_note: str = Field(min_length=3,max_length=500)
    torque_drag_calculation_id: str = Field(min_length=1,max_length=80)
    top_md_m: float = Field(ge=0,le=30000)
    bottom_md_m: float = Field(gt=0,le=30000)
    young_modulus_pa: float = Field(ge=1e9,le=500e9)
    stiffness_note: str = Field(min_length=3,max_length=500)
    boundary: Literal["long_unrestrained_rotation","pinned","clamped","unknown"]
    boundary_note: str = Field(min_length=3,max_length=500)
    pipe_configuration: Literal["uniform_plain_pipe","tool_joints","stabilizers","unknown"]
    force_basis: Literal["m10_effective_baseline","supplied_wall_forces"]
    force_basis_note: str = Field(min_length=3,max_length=500)
    wall_loads: list[WallLoad] = Field(default_factory=list,max_length=200)
    compression_allowance_n: float = Field(ge=0,le=1e7)
    modulus_relative_delta: float = Field(ge=0,le=.5)
    clearance_relative_delta: float = Field(ge=0,le=.5)
    friction_delta: float = Field(ge=0,le=.5)
    transfer_model: Literal["screen_only","ideal_helical_axial_drag"]
    integration_cells: int = Field(ge=32,le=512)
    transfer_tolerance_n: float = Field(gt=0,le=1e5)

    @model_validator(mode="after")
    def declarations(self):
        if self.bottom_md_m<=self.top_md_m:
            raise ValueError("Buckling interval bottom must exceed top.")
        if self.force_basis=="m10_effective_baseline" and self.wall_loads:
            raise ValueError("M10 buoyed-force baseline is effective; do not apply pressure corrections twice.")
        if self.force_basis=="supplied_wall_forces":
            if len(self.wall_loads)<2 or self.wall_loads[0].md_m!=self.top_md_m or self.wall_loads[-1].md_m!=self.bottom_md_m:
                raise ValueError("Wall loads must cover interval endpoints exactly.")
            if any(b.md_m<=a.md_m for a,b in zip(self.wall_loads,self.wall_loads[1:])):
                raise ValueError("Wall load knots must increase strictly in MD.")
        return self

def interpolate(rows,md,key,depths=None):
    if depths is None:depths=[r["md_m"] for r in rows]
    if md<depths[0]-1e-8 or md>depths[-1]+1e-8:
        raise ValueError("Load profile does not cover the selected interval.")
    i=max(0,min(len(rows)-2,bisect.bisect_right(depths,md)-1))
    a,b=rows[i:i+2]
    return a[key]+(b[key]-a[key])*(md-a["md_m"])/(b["md_m"]-a["md_m"])

def thresholds(ei,weight,clearance,inclination):
    root=math.sqrt(ei*weight*math.sin(inclination)/clearance)
    return 2*root,math.sqrt(8)*root

def mode(compression,fs,fh):
    return "tension" if compression<=0 else "below_sinusoidal" if compression<fs else "sinusoidal_susceptibility" if compression<fh else "helical_susceptibility"

def transfer(length,bottom_tension,weight,inclination,mu,ei,clearance,helical,sign,cells):
    """Prescribed bottom effective force; upward integration, RK4, fixed ideal helix branch."""
    step=length/cells;rows=[];t=bottom_tension
    def rate(tension):
        c=max(0.,-tension)
        if c/(ei)>1e3 or clearance*math.sqrt(c/(2*ei))>.2:
            raise ValueError("Ideal helix small-slope range exceeded; nonlinear contact analysis required.")
        contact=weight*math.sin(inclination)+(clearance*c*c/(4*ei) if c>=helical else 0.)
        return weight*math.cos(inclination)+sign*mu*contact
    for j in range(cells+1):
        rows.append({"distance_up_m":j*step,"effective_tension_n":t})
        if j==cells:break
        a=rate(t);b=rate(t+step*a/2);c=rate(t+step*b/2);d=rate(t+step*c)
        t+=step*(a+2*b+2*c+d)/6
        if not math.isfinite(t) or abs(t)>1e7:
            raise ValueError("Load-transfer branch diverged; no lock-up or WOB limit inferred.")
    return rows

def buckling(v,geometry,path,linked_inputs,linked_result):
    source=TorqueDragInput.model_validate(linked_inputs)
    base={"model_version":"M11-confined-straight-1","approval_issued":False,"equipment_authority":"none",
          "scope":"Offline straight inclined uniform plain pipe; Dawson–Paslay sinusoidal and Chen–Cheatham helical estimates. Local effective compression, not surface or bit WOB.",
          "force_convention":"Tension positive; effective tension = wall tension - Pi*Ai + Po*Ao using absolute pressures. M10 buoyed-force baseline already effective.",
          "torque_drag_calculation_id":v.torque_drag_calculation_id,"references":REFERENCES,
          "limitations":["No operational WOB limit, certification, or equipment command.",
                         "Long-pipe thresholds omit end restraint, residual curvature, tortuosity, tool joints, torque, rotation and dynamics.",
                         "Ideal helix contact is a conditional axial-load scenario; sinusoidal post-buckling contact and 3D nonlinear beam/contact are not solved.",
                         "Ten characteristic wavelengths is an eligibility guard, not evidence that boundary effects vanish.",
                         "M10 is an unqualified soft-string load baseline. Supplied wall forces need independent equilibrium and pressure-reference evidence."],
          "profile":[],"reasons":[]}
    reasons=[]
    if v.evidence_state=="unknown":reasons.append("Input evidence unknown.")
    if source.evidence_state=="unknown" or linked_result.get("status")!="research_scenario":
        reasons.append("Linked torque/drag source has no eligible load profile.")
    if v.evidence_state=="supplied" and source.evidence_state=="synthetic":
        reasons.append("Synthetic M10 source cannot establish supplied load evidence.")
    if v.boundary!="long_unrestrained_rotation":reasons.append("Only the declared long-pipe unrestrained-rotation boundary is supported.")
    if v.pipe_configuration!="uniform_plain_pipe":reasons.append("Tool joints, stabilizers or unknown pipe configuration require a contact/stiffness model.")
    if source.rotation_rad_s!=0 or source.bottom_torque_nm!=0:
        reasons.append("Rotation or applied torque is outside the selected axial buckling model.")
    lo,hi=v.top_md_m,v.bottom_md_m
    if hi>path.depths[-1] or hi>source.string_sections[-1].bottom_md_m:
        raise ValueError("Buckling interval exceeds accepted survey or linked string.")
    sections=[s for s in source.string_sections if max(lo,s.top_md_m)<min(hi,s.bottom_md_m)]
    if len(sections)!=1:reasons.append("String transitions within interval are unsupported; select one uniform section.")
    holes=[h for h in geometry.hole_sections if max(lo,h.top_md_m)<min(hi,h.bottom_md_m)]
    if not holes or sum(min(hi,h.bottom_md_m)-max(lo,h.top_md_m) for h in holes)<hi-lo-1e-6:
        raise ValueError("Buckling requires complete hole coverage.")
    # Check every survey arc intersecting the interval, not only endpoint tangents.
    for j in range(len(path.depths)-1):
        if max(lo,path.depths[j])<min(hi,path.depths[j+1]) and path.segment(j)[-1]>1e-7:
            reasons.append("Curved survey interval is unsupported by straight-hole thresholds.");break
    inclination=math.acos(max(-1.,min(1.,tangent(path,(lo+hi)/2)[2])))
    if not math.radians(5)<=inclination<=math.pi/2+1e-8:
        reasons.append("Inclination must be 5–90 degrees; vertical/upgoing thresholds require a different model.")
    if reasons:return {**base,"status":"withheld","reasons":reasons}
    s=sections[0];od=s.outside_diameter_m;inside=s.inside_diameter_m
    cuts={lo,hi,*[h.top_md_m for h in holes if lo<h.top_md_m<hi],*[h.bottom_md_m for h in holes if lo<h.bottom_md_m<hi]}
    for c in geometry.casings:
        if c.state=="installed" and max(lo,c.top_md_m)<min(hi,c.bottom_md_m):
            cuts.update(x for x in (c.top_md_m,c.bottom_md_m) if lo<x<hi)
    bores=[]
    for a,b in zip(sorted(cuts),sorted(cuts)[1:]):
        mid=(a+b)/2
        diameter=next(h.diameter_m for h in holes if h.top_md_m<=mid<h.bottom_md_m)
        diameter=min([diameter]+[c.inside_diameter_m for c in geometry.casings if c.state=="installed" and c.top_md_m<=mid<c.bottom_md_m])
        bores.append(diameter)
    if max(bores)-min(bores)>1e-9:
        return {**base,"status":"withheld","reasons":["Bore/installed-casing diameter transitions are unsupported."]}
    clearance=(bores[0]-od)/2
    if clearance<=0:raise ValueError("String OD does not clear the installed bore.")
    area=math.pi*(od*od-inside*inside)/4
    inertia=math.pi*(od**4-inside**4)/64;ei=v.young_modulus_pa*inertia
    w=(s.material_density_kg_m3-source.fluid_density_kg_m3)*G*area
    if w<=0:return {**base,"status":"withheld","reasons":["Non-positive buoyed weight is outside this formulation."]}
    mu=s.friction_coefficient
    if mu-v.friction_delta<0 or mu+v.friction_delta>1:
        raise ValueError("Friction uncertainty must stay between zero and one.")
    fs,fh=thresholds(ei,w,clearance,inclination)
    wavelength=2*math.pi*(ei*clearance/(w*math.sin(inclination)))**.25
    # Ten wavelengths is a software eligibility guard, not a validated end-effect bound.
    longest= wavelength*((1+v.modulus_relative_delta)*(1+v.clearance_relative_delta))**.25
    if hi-lo<10*longest:
        return {**base,"status":"withheld","reasons":["Interval is shorter than ten characteristic wavelengths at an uncertainty corner; finite-boundary analysis required."],
                "characteristic_wavelength_m":wavelength,"minimum_screen_length_m":10*longest}
    source_rows=linked_result["profile"];source_depths=[r["md_m"] for r in source_rows]
    wall_knots=[k.model_dump() for k in v.wall_loads];wall_depths=[k["md_m"] for k in wall_knots]
    def tension(md):
        if v.force_basis=="m10_effective_baseline":
            return interpolate(source_rows,md,"tension_n",source_depths)
        wall=interpolate(wall_knots,md,"wall_tension_n",wall_depths)
        pi=interpolate(wall_knots,md,"internal_absolute_pa",wall_depths);po=interpolate(wall_knots,md,"external_absolute_pa",wall_depths)
        return wall-pi*math.pi*inside**2/4+po*math.pi*od**2/4
    low_fs,_=thresholds(ei*(1-v.modulus_relative_delta),w,clearance*(1+v.clearance_relative_delta),inclination)
    high_fs,_=thresholds(ei*(1+v.modulus_relative_delta),w,clearance*(1-v.clearance_relative_delta),inclination)
    points={lo+(hi-lo)*j/200 for j in range(201)}
    points.update(k.md_m for k in v.wall_loads)
    points.update(r["md_m"] for r in linked_result["profile"] if lo<=r["md_m"]<=hi)
    rows=[]
    for md in sorted(points):
        t=tension(md);c=max(0.,-t);upper=max(0.,-t+v.compression_allowance_n)
        rows.append({"md_m":md,"effective_tension_n":t,"compression_n":c,"upper_compression_n":upper,
                     "sinusoidal_threshold_n":fs,"helical_threshold_n":fh,
                     "sinusoidal_lower_threshold_n":low_fs,"sinusoidal_upper_threshold_n":high_fs,
                     "sinusoidal_margin_n":fs-c,"conservative_margin_n":low_fs-upper,
                     "mode_indicator":mode(c,fs,fh),"uncertainty_mode_indicator":mode(upper,low_fs,low_fs*math.sqrt(2)),
                     "ideal_added_contact_n_per_m":clearance*c*c/(4*ei) if c>=fh else 0.})
    if max(r["upper_compression_n"] for r in rows)/(v.young_modulus_pa*(1-v.modulus_relative_delta)*area)>.002:
        return {**base,"status":"withheld","reasons":["Compression exceeds 0.2 percent linear-elastic strain screening envelope; material/nonlinear analysis required."]}
    result={**base,"status":"research_scenario","profile":rows,"inclination_deg":math.degrees(inclination),
            "radial_clearance_m":clearance,"buoyant_weight_n_per_m":w,"flexural_rigidity_nm2":ei,
            "characteristic_wavelength_m":wavelength,"sinusoidal_threshold_n":fs,"helical_threshold_n":fh,
            "sinusoidal_threshold_range_n":[low_fs,high_fs],"helical_threshold_range_n":[low_fs*math.sqrt(2),high_fs*math.sqrt(2)],
            "maximum_compression_n":max(r["compression_n"] for r in rows),
            "minimum_conservative_margin_n":min(r["conservative_margin_n"] for r in rows),
            "mode_counts":{key:sum(r["mode_indicator"]==key for r in rows) for key in ("tension","below_sinusoidal","sinusoidal_susceptibility","helical_susceptibility")}}
    if any(r["conservative_margin_n"]<0 for r in rows):
        result["reasons"].append("Local compression reaches a selected buckling screen within the tested uncertainty envelope.")
    if v.transfer_model=="screen_only":
        result["load_transfer"]={"status":"not_requested"};return result
    # This is a separate conditional equilibrium with the selected interval bottom force,
    # rather than silently treating the entire M10 soft string as a post-buckled solution.
    sign=1 if source.axial_speed_m_s>0 else -1
    bottom=tension(hi);length=hi-lo
    try:
        coarse=transfer(length,bottom,w,inclination,mu,ei,clearance,fh,sign,v.integration_cells)
        fine=transfer(length,bottom,w,inclination,mu,ei,clearance,fh,sign,2*v.integration_cells)
        finest=transfer(length,bottom,w,inclination,mu,ei,clearance,fh,sign,4*v.integration_cells)
        # Compare entire profiles on shared nodes, not only the upper endpoint.
        error=max(abs(a["effective_tension_n"]-b["effective_tension_n"]) for a,b in zip(fine,finest[::2]))
        first=max(abs(a["effective_tension_n"]-b["effective_tension_n"]) for a,b in zip(coarse,fine[::2]))
        corners=[];corner_errors=[]
        for de in (-v.modulus_relative_delta,v.modulus_relative_delta):
            for dr in (-v.clearance_relative_delta,v.clearance_relative_delta):
                for dm in (-v.friction_delta,v.friction_delta):
                    for dc in (-v.compression_allowance_n,v.compression_allowance_n):
                        e=ei*(1+de);r=clearance*(1+dr);_,h=thresholds(e,w,r,inclination)
                        branch=transfer(length,bottom-dc,w,inclination,mu+dm,e,r,h,sign,4*v.integration_cells)
                        branch_coarse=transfer(length,bottom-dc,w,inclination,mu+dm,e,r,h,sign,2*v.integration_cells)
                        corner_errors.append(max(abs(a["effective_tension_n"]-b["effective_tension_n"]) for a,b in zip(branch_coarse,branch[::2])))
                        if max(max(0.,-r["effective_tension_n"]) for r in branch)/(v.young_modulus_pa*(1+de)*area)>.002:
                            raise ValueError("Load-transfer uncertainty branch exceeds the elastic strain screening envelope.")
                        corners.append(branch[-1]["effective_tension_n"])
        error=max([error]+corner_errors)
        upper=finest[-1]["effective_tension_n"]
        baseline=bottom+length*(w*math.cos(inclination)+sign*mu*w*math.sin(inclination))
        result["load_transfer"]={"status":"converged" if error<=v.transfer_tolerance_n else "incomplete",
          "bottom_effective_tension_n":bottom,"upper_effective_tension_n":upper,
          "unbuckled_upper_effective_tension_n":baseline,"upper_tension_change_n":upper-baseline,
          "upper_tension_corner_range_n":[min(corners),max(corners)],"initial_refinement_change_n":first,
          "final_refinement_change_n":error,"refinement_scope":"Whole nominal and 16 uncertainty-corner profiles","tolerance_n":v.transfer_tolerance_n,
          "cells":4*v.integration_cells,"boundary_condition":"Prescribed interval bottom effective force; upward axial-slip equilibrium; unrestrained helix.",
          "profile":[{"md_m":hi-r["distance_up_m"],"effective_tension_n":r["effective_tension_n"]} for r in reversed(finest)]}
        if error>v.transfer_tolerance_n:
            result["status"]="incomplete_assessment";result["reasons"].append("Load-transfer profile refinement exceeds supplied tolerance.")
    except ValueError as error:
        result["status"]="incomplete_assessment";result["reasons"].append(str(error))
        result["load_transfer"]={"status":"withheld","reason":str(error)}
    return result
