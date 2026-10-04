"""Geometry-linked steady laminar circulation, with explicit applicability and evidence."""
import bisect
import itertools
import math
from datetime import datetime
from functools import lru_cache
from typing import Literal
from pydantic import Field, model_validator
from .models import Contract
from .geometry import GeometryInput, Path
from .physics import G

def timestamp(text):
    try:
        value=datetime.fromisoformat(text.replace("Z","+00:00"))
    except ValueError:
        raise ValueError("Mud/scenario timestamps must use ISO-8601 with an explicit UTC offset.")
    if value.utcoffset() is None:
        raise ValueError("Mud/scenario timestamps require an explicit UTC offset.")
    return value

class MudRecord(Contract):
    density_kg_m3: float = Field(ge=500,le=3000)
    rheology: Literal["newtonian","bingham","herschel_bulkley"]
    consistency_pa_sn: float = Field(ge=.0001,le=100)
    flow_index: float = Field(ge=.2,le=1.5)
    yield_stress_pa: float = Field(ge=0,le=200)
    measured_at: str = Field(min_length=10,max_length=50)
    evidence_state: Literal["supplied_measured","synthetic","unknown"]
    source_note: str = Field(min_length=3,max_length=500)
    test_temperature_c: float = Field(ge=-20,le=250)
    density_rheology_basis_note: str = Field(min_length=3,max_length=700)
    @model_validator(mode="after")
    def law(self):
        timestamp(self.measured_at)
        if self.rheology=="newtonian" and (self.flow_index!=1 or self.yield_stress_pa!=0):
            raise ValueError("Newtonian rheology requires n=1 and zero yield stress; K is viscosity in Pa.s.")
        if self.rheology=="bingham" and self.flow_index!=1:
            raise ValueError("Bingham rheology requires n=1; K is plastic viscosity in Pa.s.")
        return self

class StringSection(Contract):
    name: str = Field(min_length=1,max_length=80)
    top_md_m: float = Field(ge=0,le=30000)
    bottom_md_m: float = Field(gt=0,le=30000)
    outside_diameter_m: float = Field(ge=.01,le=1)
    inside_diameter_m: float = Field(ge=.005,le=1)
    source_note: str = Field(min_length=3,max_length=300)
    @model_validator(mode="after")
    def physical(self):
        if self.bottom_md_m<=self.top_md_m or self.inside_diameter_m>=self.outside_diameter_m:
            raise ValueError("String sections need positive length and ID below OD.")
        return self

class PressureKnot(Contract):
    md_m: float = Field(ge=0,le=30000)
    pore_gauge_pa: float = Field(ge=0,le=1e9)
    fracture_gauge_pa: float = Field(gt=0,le=1e9)
    pore_upper_allowance_pa: float = Field(ge=0,le=1e8)
    fracture_lower_allowance_pa: float = Field(ge=0,le=1e8)
    @model_validator(mode="after")
    def pressure_order(self):
        if self.fracture_gauge_pa<=self.pore_gauge_pa:
            raise ValueError("Nominal fracture pressure must exceed pore pressure at each knot.")
        return self

class PressureWindow(Contract):
    reference: Literal["surface_atmospheric_gauge"]
    interpolation: Literal["piecewise_linear_md"]
    evidence_state: Literal["supplied_reviewed","synthetic","unreviewed"]
    source_note: str = Field(min_length=3,max_length=500)
    review_note: str = Field(min_length=3,max_length=500)
    knots: list[PressureKnot] = Field(min_length=2,max_length=100)
    @model_validator(mode="after")
    def order(self):
        if self.knots[0].md_m!=0 or any(b.md_m<=a.md_m for a,b in zip(self.knots,self.knots[1:])):
            raise ValueError("Pressure-window knots must start at MD 0 and strictly increase.")
        return self

class HydraulicSensitivity(Contract):
    density_delta_kg_m3: float = Field(ge=0,le=500)
    flow_delta_m3_s: float = Field(ge=0,le=.1)
    consistency_relative_delta: float = Field(ge=0,le=.5)
    backpressure_delta_pa: float = Field(ge=0,le=1e7)

class HydraulicsInput(Contract):
    study_name: str = Field(min_length=3,max_length=100)
    geometry_revision_id: str = Field(min_length=1,max_length=80)
    depth_datum: str = Field(min_length=1,max_length=100)
    scenario_at: str = Field(min_length=10,max_length=50)
    maximum_mud_age_hours: float = Field(ge=0,le=720)
    mud: MudRecord
    circulation_state: Literal["steady_single_phase","transient","multiphase","losses","unknown"]
    flow_regime: Literal["supplied_laminar","unknown","transitional_or_turbulent"]
    applicability_note: str = Field(min_length=3,max_length=700)
    geometry_state: Literal["installed_only","include_planned_scenario"]
    string_sections: list[StringSection] = Field(min_length=1,max_length=30)
    flow_m3_s: float = Field(ge=0,le=.2)
    surface_backpressure_pa: float = Field(ge=0,le=1e8)
    surface_loss_pa: float = Field(ge=0,le=1e8)
    surface_loss_note: str = Field(min_length=3,max_length=300)
    nozzle_total_area_m2: float = Field(ge=1e-6,le=.02)
    nozzle_discharge_coefficient: float = Field(ge=.1,le=1)
    nozzle_source_note: str = Field(min_length=3,max_length=300)
    rotation_rad_s: float = Field(ge=0,le=1000)
    eccentricity_fraction: float = Field(ge=0,le=1)
    cuttings_volume_fraction: float = Field(ge=0,le=.5)
    wall_roughness_m: float = Field(ge=0,le=.01)
    pressure_window: PressureWindow
    surface_rating_pa: float | None = Field(default=None,gt=0,le=1e9)
    surface_rating_source: str | None = Field(default=None,min_length=3,max_length=500)
    sensitivity: HydraulicSensitivity
    @model_validator(mode="after")
    def ordering(self):
        timestamp(self.scenario_at)
        s=self.string_sections
        if s[0].top_md_m!=0 or any(abs(a.bottom_md_m-b.top_md_m)>1e-7 for a,b in zip(s,s[1:])):
            raise ValueError("String geometry must start at MD 0 and be contiguous.")
        if self.pressure_window.knots[-1].md_m!=s[-1].bottom_md_m:
            raise ValueError("Pressure-window knots must cover the entire string to the selected circulation depth.")
        if self.surface_rating_pa is not None and not self.surface_rating_source:
            raise ValueError("Equipment pressure rating requires a supplied source.")
        d=self.sensitivity
        if not 500<=self.mud.density_kg_m3-d.density_delta_kg_m3<=self.mud.density_kg_m3+d.density_delta_kg_m3<=3000:
            raise ValueError("Density sensitivity corners leave the declared envelope.")
        if self.flow_m3_s-d.flow_delta_m3_s<0 or self.flow_m3_s+d.flow_delta_m3_s>.2:
            raise ValueError("Flow sensitivity corners leave the declared envelope.")
        if self.mud.consistency_pa_sn*(1-d.consistency_relative_delta)<.0001 or self.mud.consistency_pa_sn*(1+d.consistency_relative_delta)>100:
            raise ValueError("Consistency sensitivity corners leave the declared envelope.")
        if self.surface_backpressure_pa-d.backpressure_delta_pa<0 or self.surface_backpressure_pa+d.backpressure_delta_pa>1e8:
            raise ValueError("Backpressure sensitivity corners leave the declared envelope.")
        return self

@lru_cache(maxsize=4)
def gauss(order):
    """Gauss-Legendre nodes/weights computed in stdlib; no external solver dependency."""
    result=[]
    for i in range(1,order+1):
        x=math.cos(math.pi*(i-.25)/(order+.5))
        for _ in range(30):
            p0,p1=1.,x
            for j in range(2,order+1):
                p0,p1=p1,((2*j-1)*x*p1-(j-1)*p0)/j
            derivative=order*(x*p1-p0)/(x*x-1)
            update=p1/derivative
            x-=update
            if abs(update)<2e-15:break
        # Recompute derivative at the converged root.
        p0,p1=1.,x
        for j in range(2,order+1):p0,p1=p1,((2*j-1)*x*p1-(j-1)*p0)/j
        derivative=order*(x*p1-p0)/(x*x-1)
        result.append((x,2/((1-x*x)*derivative*derivative)))
    return tuple(result)

def integrate(function,lo,hi,order=48):
    if hi<=lo:return 0.
    center=(lo+hi)/2;scale=(hi-lo)/2
    return scale*math.fsum(w*function(center+scale*x) for x,w in gauss(order))

def pipe_flow(gradient,radius,k,n,ty):
    """Exact HB integral, including unyielded central plug (Q = pi integral gamma*r^2 dr)."""
    wall=gradient*radius/2
    if wall<=ty:return 0.
    h=wall-ty;m=1/n
    return math.pi*radius**3/(wall**3*k**m)*(
        h**(m+3)/(m+3)+2*ty*h**(m+2)/(m+2)+ty*ty*h**(m+1)/(m+1))

def annular_flow(gradient,a,b,k,n,ty,order=48):
    """HB concentric annulus; signed shear, two no-slip walls and yielded intervals."""
    if gradient<=2*ty/(b-a)*(1+2e-14):return 0.,math.sqrt(a*b),0.
    t=2*ty/gradient
    def zones(r0):
        root=math.hypot(t,2*r0)
        rp=2*r0*r0/(root+t)  # cancellation-safe positive-shear yield radius
        rn=(root+t)/2
        return min(b,max(a,rp)),min(b,max(a,rn))
    def derivative(r,r0):
        tau=gradient*.5*(r0*r0/r-r)
        return math.copysign((max(0.,abs(tau)-ty)/k)**(1/n),tau)
    def balance(r0):
        rp,rn=zones(r0)
        return integrate(lambda r:derivative(r,r0),a,rp,order)+integrate(lambda r:derivative(r,r0),rn,b,order)
    lo,hi=a,b
    for _ in range(48):
        mid=(lo+hi)/2
        if balance(mid)>0:hi=mid
        else:lo=mid
    r0=(lo+hi)/2;rp,rn=zones(r0)
    q=math.pi*(integrate(lambda r:(b*b-r*r)*derivative(r,r0),a,rp,order)+integrate(lambda r:(b*b-r*r)*derivative(r,r0),rn,b,order))
    return max(0.,q),r0,balance(r0)

@lru_cache(maxsize=4096)
def flow_gradient(q,inside_radius,outside_radius,k,n,ty):
    """Solve Q(G); inside_radius=0 denotes pipe. Reject failed numerical convergence."""
    if q==0:return {"gradient_pa_m":0.,"flow_residual_relative":0.,"quadrature_change_relative":0.,"zero_shear_radius_m":0.,"wall_slip_residual_m_s":0.}
    if q<1e-10:raise ValueError("Positive flow below 1e-10 m3/s is outside the numerical resolution; zero flow is a separate hydrostatic case.")
    a,b=inside_radius,outside_radius
    if not (0<=a<b and b-a>=.0005 and (a==0 or .02<=a/b<=.98)):
        raise ValueError("Pipe/annulus geometry leaves the declared concentric numerical envelope.")
    rate=lambda g,order=48:pipe_flow(g,b,k,n,ty) if a==0 else annular_flow(g,a,b,k,n,ty,order)[0]
    lo=2*ty/(b-a);hi=max(1.,lo*1.2)
    for _ in range(80):
        if rate(hi)>=q:break
        hi*=2
        if hi>1e7:raise ValueError("Required friction gradient exceeds the numerical envelope.")
    else:raise ValueError("Could not bracket the friction gradient.")
    for _ in range(44):
        mid=(lo+hi)/2
        if rate(mid)<q:lo=mid
        else:hi=mid
    gradient=(lo+hi)/2
    check=rate(gradient,96);change=abs(check-q)/q
    if change>3e-5:
        # A higher quadrature solve is attempted, then independently refined again.
        lo=2*ty/(b-a);hi=gradient*1.1+1
        while rate(hi,96)<q:hi*=2
        for _ in range(44):
            mid=(lo+hi)/2
            if rate(mid,96)<q:lo=mid
            else:hi=mid
        gradient=(lo+hi)/2;check=rate(gradient,192);change=abs(check-q)/q
    if change>3e-5:raise ValueError("Annulus quadrature did not meet its flow-convergence tolerance.")
    actual,r0,slip=(pipe_flow(gradient,b,k,n,ty),0.,0.) if a==0 else annular_flow(gradient,a,b,k,n,ty,96)
    return {"gradient_pa_m":gradient,"flow_residual_relative":abs(actual-q)/q,
            "quadrature_change_relative":change,"zero_shear_radius_m":r0,"wall_slip_residual_m_s":slip}

def window_at(window,md):
    knots=window.knots;depths=[k.md_m for k in knots]
    i=max(0,min(len(knots)-2,bisect.bisect_right(depths,md)-1));a,b=knots[i:i+2]
    t=(md-a.md_m)/(b.md_m-a.md_m)
    result={name:getattr(a,name)+t*(getattr(b,name)-getattr(a,name)) for name in ("pore_gauge_pa","fracture_gauge_pa","pore_upper_allowance_pa","fracture_lower_allowance_pa")}
    result["lower_pa"]=result["pore_gauge_pa"]+result["pore_upper_allowance_pa"]
    result["upper_pa"]=result["fracture_gauge_pa"]-result["fracture_lower_allowance_pa"]
    result["lower_slope"]=(b.pore_gauge_pa+b.pore_upper_allowance_pa-a.pore_gauge_pa-a.pore_upper_allowance_pa)/(b.md_m-a.md_m)
    result["upper_slope"]=(b.fracture_gauge_pa-b.fracture_lower_allowance_pa-a.fracture_gauge_pa+a.fracture_lower_allowance_pa)/(b.md_m-a.md_m)
    return result

def derivative_roots(path,lo,hi,cosine_target):
    """Exact MD roots of dTVD/dMD=target within a single minimum-curvature arc."""
    i=max(0,min(len(path.stations)-2,bisect.bisect_right(path.depths,(lo+hi)/2)-1))
    a,b,va,vb,beta=path.segment(i)
    if beta<1e-7:
        change=vb[2]-va[2]
        if abs(change)<1e-15:return []
        md=a.md_m+(cosine_target-va[2])/change*(b.md_m-a.md_m)
        return [md] if lo+1e-8<md<hi-1e-8 else []
    uz=(vb[2]-va[2]*math.cos(beta))/math.sin(beta)
    amplitude=math.hypot(va[2],uz)
    if amplitude<1e-14 or abs(cosine_target)>amplitude+1e-12:return []
    phase=math.atan2(uz,va[2]);theta=math.acos(max(-1.,min(1.,cosine_target/amplitude)))
    roots=[]
    for sign in (-1,1):
        for j in range(-2,3):
            angle=phase+sign*theta+j*2*math.pi
            md=a.md_m+angle/beta*(b.md_m-a.md_m)
            if lo+1e-8<md<hi-1e-8:roots.append(md)
    return roots

def build_segments(value,geometry,path):
    td=value.string_sections[-1].bottom_md_m
    if td>path.depths[-1]:raise ValueError("String extends beyond the saved survey.")
    if not geometry.hole_sections or geometry.hole_sections[-1].bottom_md_m<td:
        raise ValueError("Hole geometry must cover the entire circulation path.")
    casings=[c for c in geometry.casings if c.state=="installed" or value.geometry_state=="include_planned_scenario"]
    points={0.,td}
    for collection in (geometry.hole_sections,casings,value.string_sections):
        for s in collection:
            points.update(x for x in (s.top_md_m,s.bottom_md_m) if 0<x<td)
    points.update(x for x in path.depths if 0<x<td)
    points.update(x.md_m for x in value.pressure_window.knots)
    result=[]
    if len(points)>1001:raise ValueError("More than 1,000 hydraulic segments require a larger qualified solver envelope.")
    for top,bottom in zip(sorted(points),sorted(points)[1:]):
        md=(top+bottom)/2
        hole=next(h for h in geometry.hole_sections if h.top_md_m<=md<h.bottom_md_m)
        casing=[c for c in casings if c.top_md_m<=md<c.bottom_md_m]
        outer=min(casing,key=lambda c:c.inside_diameter_m) if casing else None
        bore=outer.inside_diameter_m if outer else hole.diameter_m
        string=next(s for s in value.string_sections if s.top_md_m<=md<s.bottom_md_m)
        if bore-string.outside_diameter_m<.001:
            raise ValueError("String OD must clear the effective hole/casing ID by at least 1 mm.")
        result.append({"top_md_m":top,"bottom_md_m":bottom,"length_m":bottom-top,
                       "bore_diameter_m":bore,"bore_source":outer.name+" ["+outer.state+"]" if outer else hole.name+" [hole]",
                       "string_name":string.name,"string_od_m":string.outside_diameter_m,"string_id_m":string.inside_diameter_m})
    return result

def pressure_case(value,segments,path,rho,q,k,backpressure):
    n=value.mud.flow_index;ty=value.mud.yield_stress_pa
    result_segments=[];annular=pipe=0.
    for s in segments:
        a=s["string_od_m"]/2;b=s["bore_diameter_m"]/2
        area=math.pi*(b*b-a*a);pipe_area=math.pi*(s["string_id_m"]/2)**2
        av=q/area;pv=q/pipe_area;dh=2*(b-a)
        def screen(velocity,diameter,scale):
            if velocity==0:return 0.
            shear=scale*velocity/diameter
            apparent=ty/shear+k*shear**(n-1)
            return rho*velocity*diameter/apparent
        ann_re=screen(av,dh,12.);pipe_re=screen(pv,s["string_id_m"],8.)
        if max(ann_re,pipe_re)>1000:
            raise ValueError("Nominal-apparent Reynolds screening exceeds 1000; transition/turbulent closures are not implemented.")
        if value.wall_roughness_m/min(dh,s["string_id_m"])>.001:
            raise ValueError("Relative roughness exceeds the declared smooth-wall approximation.")
        ann=flow_gradient(q,a,b,k,n,ty);inside=flow_gradient(q,0.,s["string_id_m"]/2,k,n,ty)
        ann_loss=ann["gradient_pa_m"]*s["length_m"];pipe_loss=inside["gradient_pa_m"]*s["length_m"]
        result_segments.append({**s,"annular_area_m2":area,"pipe_area_m2":pipe_area,
                               "annular_velocity_m_s":av,"pipe_velocity_m_s":pv,
                               "annular_re_screen":ann_re,"pipe_re_screen":pipe_re,
                               "annular":ann,"pipe":inside,"annular_loss_pa":ann_loss,"pipe_loss_pa":pipe_loss,
                               "annular_cumulative_top_pa":annular,"pipe_cumulative_top_pa":pipe})
        annular+=ann_loss;pipe+=pipe_loss
    bit=rho*.5*(q/(value.nozzle_discharge_coefficient*value.nozzle_total_area_m2))**2
    surface_loss=value.surface_loss_pa if q else 0.
    standpipe=backpressure+annular+pipe+bit
    pump=standpipe+surface_loss
    segment_depths=[s["top_md_m"] for s in result_segments]
    def at(md):
        i=max(0,min(len(result_segments)-1,bisect.bisect_right(segment_depths,md)-1))
        s=result_segments[i];tvd=path.at(md)["tvd_m"]
        friction=s["annular_cumulative_top_pa"]+s["annular"]["gradient_pa_m"]*(md-s["top_md_m"])
        pressure=backpressure+rho*G*tvd+friction
        bounds=window_at(value.pressure_window,md)
        # Downflow inside-pipe pressure: same head minus friction traversed from surface.
        pipe_to=s["pipe_cumulative_top_pa"]+s["pipe"]["gradient_pa_m"]*(md-s["top_md_m"])
        return {"md_m":md,"tvd_m":tvd,"hydrostatic_pa":rho*G*tvd,"annular_friction_pa":friction,
                "static_gauge_pa":backpressure+rho*G*tvd,"annular_gauge_pa":pressure,
                "pipe_gauge_pa":standpipe+rho*G*tvd-pipe_to,
                "equivalent_density_including_backpressure_kg_m3":pressure/(G*tvd) if tvd>1e-9 else None,
                "pore_gauge_pa":bounds["pore_gauge_pa"],"fracture_gauge_pa":bounds["fracture_gauge_pa"],
                "lower_assessed_pa":bounds["lower_pa"],"upper_assessed_pa":bounds["upper_pa"],
                "above_pore_allowance_pa":pressure-bounds["lower_pa"],"below_fracture_allowance_pa":bounds["upper_pa"]-pressure}
    critical=set(segment_depths+[result_segments[-1]["bottom_md_m"]])
    for s in result_segments:
        w=window_at(value.pressure_window,(s["top_md_m"]+s["bottom_md_m"])/2)
        gradient=s["annular"]["gradient_pa_m"]
        for slope in (w["lower_slope"],w["upper_slope"]):
            critical.update(derivative_roots(path,s["top_md_m"],s["bottom_md_m"],(slope-gradient)/(rho*G)))
        critical.update(derivative_roots(path,s["top_md_m"],s["bottom_md_m"],0.))
    extrema=[at(md) for md in sorted(critical)]
    if min(p["tvd_m"] for p in extrema)<-1e-7:raise ValueError("Trajectory extends above the pressure datum; absolute-pressure/phase checks are not implemented.")
    lower=min(extrema,key=lambda p:p["above_pore_allowance_pa"])
    upper=min(extrema,key=lambda p:p["below_fracture_allowance_pa"])
    td=result_segments[-1]["bottom_md_m"];bottom=at(td)
    numerical_loss_error=sum(s["annular_loss_pa"]*s["annular"]["quadrature_change_relative"]+s["pipe_loss_pa"]*s["pipe"]["quadrature_change_relative"] for s in result_segments)
    return {"parameters":{"density_kg_m3":rho,"flow_m3_s":q,"consistency_pa_sn":k,"surface_backpressure_pa":backpressure},
            "segments":result_segments,"annular_loss_pa":annular,"pipe_loss_pa":pipe,"bit_loss_pa":bit,"surface_loss_pa":surface_loss,
            "standpipe_gauge_pa":standpipe,"required_supply_gauge_pa":pump,"minimum_above_pore":lower,"minimum_below_fracture":upper,
            "critical_md_m":sorted(critical),"at":at,"bottom":bottom,"numerical_loss_change_indicator_pa":numerical_loss_error,
            "mass_in_kg_s":rho*q,"mass_out_kg_s":rho*q,
            "bottom_path_balance_residual_pa":bottom["pipe_gauge_pa"]-bottom["annular_gauge_pa"]-bit}

def hydraulics(value: HydraulicsInput,geometry: GeometryInput,path: Path):
    age=(timestamp(value.scenario_at)-timestamp(value.mud.measured_at)).total_seconds()/3600
    reasons=[]
    if value.depth_datum!=geometry.datum:raise ValueError("Hydraulics datum must match the saved geometry.")
    if age<0:reasons.append("Mud observation occurs after the scenario timestamp.")
    if age>value.maximum_mud_age_hours:reasons.append("Mud-test age exceeds the explicitly supplied maximum.")
    if value.mud.evidence_state=="unknown":reasons.append("Mud density/rheology evidence is unknown.")
    if value.pressure_window.evidence_state=="unreviewed":reasons.append("Pressure-window evidence is unreviewed.")
    if value.circulation_state!="steady_single_phase":reasons.append("Transient, multiphase, losses or unknown states are outside this steady closed single-phase model.")
    if value.flow_m3_s>0 and value.flow_regime!="supplied_laminar":reasons.append("Laminar applicability has not been supplied.")
    if value.eccentricity_fraction or value.rotation_rad_s or value.cuttings_volume_fraction:
        reasons.append("Eccentricity, rotating walls and cuttings loading require additional qualified closures.")
    common={"model":"steady-laminar-geometry-hydraulics","model_version":"0.1.0","mud_age_hours":age,
            "pressure_reference":"gauge relative to atmosphere at the surface pressure datum",
            "equivalent_density_reference":"annular gauge pressure / (g*TVD), including surface backpressure; null at TVD <= 0",
            "approval_issued":False,"equipment_authority":"none",
            "warnings":["Constant density and rheology along the path; supplied temperature/pressure applicability must be reviewed.",
                        "Fully developed laminar no-slip flow; concentric stationary walls. Local transitions, bends and tool joints are not resolved.",
                        "Apparent Reynolds <= 1000 is an additional numerical screen, not a validated non-Newtonian transition criterion.",
                        "Pressure limits are supplied piecewise-linear functions of MD; review references and uncertainty allowances before interpretation.",
                        "Parameter-corner ranges are tested scenarios, not calibrated confidence intervals or proven continuous bounds.",
                        "Sensitivity varies density, flow, K and backpressure only; n, yield stress, geometry, nozzle coefficients and supplied surface loss remain fixed.",
                        "Mud age is assessed at the historical scenario timestamp; this is not a live freshness check.",
                        "Supplied upstream surface loss is held fixed at nonzero-flow corners; all friction/nozzle losses are zero in the hydrostatic Q=0 case.",
                        "No API RP 13D compliance or flow-loop/PWD qualification is claimed. No pump, mud or well-control recommendation is issued."]}
    if geometry.tool_to_bit_offset_m:common["warnings"].append("Saved survey-to-bit separation is recorded in M1; no bit-path extrapolation is performed.")
    if value.geometry_state=="include_planned_scenario":common["warnings"].append("Planned casing IDs are included as a declared future geometry scenario.")
    if reasons:return {**common,"status":"withheld","reasons":reasons,"profile":[],"nominal":None,"sensitivity":None}
    try:
        segments=build_segments(value,geometry,path)
        nominal=pressure_case(value,segments,path,value.mud.density_kg_m3,value.flow_m3_s,value.mud.consistency_pa_sn,value.surface_backpressure_pa)
    except ValueError as error:
        return {**common,"status":"withheld","reasons":[str(error)],"profile":[],"nominal":None,"sensitivity":None}
    d=value.sensitivity
    options=[sorted(set([value.mud.density_kg_m3-d.density_delta_kg_m3,value.mud.density_kg_m3+d.density_delta_kg_m3])),
             sorted(set([value.flow_m3_s-d.flow_delta_m3_s,value.flow_m3_s+d.flow_delta_m3_s])),
             sorted(set([value.mud.consistency_pa_sn*(1-d.consistency_relative_delta),value.mud.consistency_pa_sn*(1+d.consistency_relative_delta)])),
             sorted(set([value.surface_backpressure_pa-d.backpressure_delta_pa,value.surface_backpressure_pa+d.backpressure_delta_pa]))]
    cases=[];withheld=[]
    for rho,q,k,back in itertools.product(*options):
        try:cases.append(pressure_case(value,segments,path,rho,q,k,back))
        except ValueError as error:withheld.append({"density_kg_m3":rho,"flow_m3_s":q,"consistency_pa_sn":k,"surface_backpressure_pa":back,"reason":str(error)})
    td=value.string_sections[-1].bottom_md_m
    points=set(nominal["critical_md_m"])
    points.update(min(td,i*max(20.,td/1000)) for i in range(math.ceil(td/max(20.,td/1000))+1))
    for c in cases:points.update((c["minimum_above_pore"]["md_m"],c["minimum_below_fracture"]["md_m"]))
    profile=[]
    for md in sorted(points):
        point=nominal["at"](md)
        pressures=[c["at"](md)["annular_gauge_pa"] for c in cases]
        point["tested_min_gauge_pa"]=min(pressures) if pressures else None
        point["tested_max_gauge_pa"]=max(pressures) if pressures else None
        profile.append(point)
    all_cases=[nominal,*cases]
    minimum_lower=min(({"margin_pa":c["minimum_above_pore"]["above_pore_allowance_pa"],"md_m":c["minimum_above_pore"]["md_m"],"tvd_m":c["minimum_above_pore"]["tvd_m"],"parameters":c["parameters"]} for c in all_cases),key=lambda x:x["margin_pa"])
    minimum_upper=min(({"margin_pa":c["minimum_below_fracture"]["below_fracture_allowance_pa"],"md_m":c["minimum_below_fracture"]["md_m"],"tvd_m":c["minimum_below_fracture"]["tvd_m"],"parameters":c["parameters"]} for c in all_cases),key=lambda x:x["margin_pa"])
    standpipe_max=max(c["required_supply_gauge_pa"] for c in all_cases)
    rating_margin=value.surface_rating_pa-standpipe_max if value.surface_rating_pa is not None else None
    assessment_reasons=[]
    if rating_margin is None:assessment_reasons.append("Surface-supply pressure rating is absent; equipment comparison is incomplete.")
    elif rating_margin<0:assessment_reasons.append("At least one tested supply pressure exceeds the supplied surface rating.")
    if withheld:assessment_reasons.append("At least one requested sensitivity corner is outside model applicability.")
    if minimum_lower["margin_pa"]<0:assessment_reasons.append("At least one tested profile is below a supplied pore-pressure upper allowance.")
    if minimum_upper["margin_pa"]<0:assessment_reasons.append("At least one tested profile is above a supplied fracture-pressure lower allowance.")
    summaries=[{k:v for k,v in c.items() if k not in ("at","segments","critical_md_m")} for c in cases]
    # Callables never enter a saved JSON record.
    nominal.pop("at")
    return {**common,"status":"scenario_only" if not withheld and rating_margin is not None else "incomplete_assessment",
            "reasons":assessment_reasons,"profile":profile,"nominal":nominal,
            "sensitivity":{"tested_admissible_corners":len(cases),"tested_withheld_corners":withheld,"cases":summaries,
                           "minimum_above_pore":minimum_lower,"minimum_below_fracture":minimum_upper},
            "surface_equipment":{"maximum_tested_supply_pa":standpipe_max,"supplied_rating_pa":value.surface_rating_pa,
                                 "rating_source":value.surface_rating_source,"margin_pa":rating_margin},
            "within_all_tested_bounds":minimum_lower["margin_pa"]>=0 and minimum_upper["margin_pa"]>=0 and rating_margin is not None and rating_margin>=0 and not withheld}
