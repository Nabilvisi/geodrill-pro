"""Reduced acoustic piston surge/swab, finite-volume conserved compressible storage."""
import math,bisect
from typing import Literal
from pydantic import Field,model_validator
from .models import Contract
from .physics import G
from .hydraulics import HydraulicsInput,build_segments,window_at,flow_gradient

class MotionKnot(Contract):
    time_s: float = Field(ge=0,le=600)
    downward_speed_m_s: float = Field(ge=-1,le=1)

class SurgeInput(Contract):
    study_name: str = Field(min_length=3,max_length=100)
    geometry_revision_id: str
    depth_datum: str
    hydraulics_calculation_id: str
    evidence_state: Literal["unknown","supplied","synthetic"] = "unknown"
    source_note: str = Field(min_length=3,max_length=500)
    top_md_m: float = Field(ge=0,le=30000)
    bottom_md_m: float = Field(gt=0,le=30000)
    wave_speed_m_s: float = Field(ge=50,le=2000)
    wave_speed_note: str = Field(min_length=3,max_length=500)
    displacement: Literal["closed_end_piston","open_end_instant_fill"]
    motion: list[MotionKnot] = Field(min_length=2,max_length=50)
    cells: int = Field(ge=20,le=80)
    convergence_tolerance_pa: float = Field(gt=0,le=1e7)
    @model_validator(mode="after")
    def ordered(self):
        if self.bottom_md_m<=self.top_md_m:raise ValueError("Transient interval bottom must exceed top.")
        if self.motion[0].time_s!=0 or self.motion[-1].time_s<=0 or any(b.time_s<=a.time_s for a,b in zip(self.motion,self.motion[1:])):
            raise ValueError("Motion history starts at time zero and increases strictly.")
        if self.motion[0].downward_speed_m_s!=0:
            raise ValueError("Initially static scenario requires zero initial pipe speed.")
        return self

def speed_at(knots,t):
    times=[k.time_s for k in knots];i=max(0,min(len(knots)-2,bisect.bisect_right(times,t)-1))
    a,b=knots[i:i+2];f=max(0.,min(1.,(t-a.time_s)/(b.time_s-a.time_s)))
    return a.downward_speed_m_s+f*(b.downward_speed_m_s-a.downward_speed_m_s)

def acoustic(length,area,displacement_area,rho,c,friction_lambda,motion,n):
    """x points bottom -> top. Bottom imposed piston flux; top zero perturbation pressure.
    Staggered leapfrog momentum with centered implicit drag; finite-volume continuity.
    Pressure cell centers, velocities cell faces. Compression storage is volume equivalent.
    """
    dx=length/n;end=motion[-1].time_s
    steps=math.ceil(end/(.45*dx/c));dt=end/steps
    if steps>25000 or steps*n>3000000:raise ValueError("Transient scenario exceeds 25,000 time steps; shorten duration or interval/grid.")
    p=[0.]*n;u=[0.]*(n+1);minimum=[0.]*n;maximum=[0.]*n
    tmin=[0.]*n;tmax=[0.]*n;history=[];balance=0.;maxres=0.;maxspeed=0.;pmax=0.
    denom=1+.5*friction_lambda*dt;dragfactor=(1-.5*friction_lambda*dt)/denom
    for k in range(steps):
        tmid=(k+.5)*dt
        u[0]=displacement_area/area*speed_at(motion,tmid)
        for j in range(1,n):
            u[j]=(dragfactor*u[j]-dt*(p[j]-p[j-1])/(rho*dx)/denom)
        u[n]=dragfactor*u[n]+2*dt*p[-1]/(rho*dx)/denom
        balance+=area*dt*(u[0]-u[n])
        for j in range(n):
            p[j]-=rho*c*c*dt*(u[j+1]-u[j])/dx
            if p[j]<minimum[j]:minimum[j],tmin[j]=p[j],(k+1)*dt
            if p[j]>maximum[j]:maximum[j],tmax[j]=p[j],(k+1)*dt
        storage=area*dx*math.fsum(p)/(rho*c*c)
        maxres=max(maxres,abs(storage-balance));maxspeed=max(maxspeed,max(abs(x) for x in u));pmax=max(pmax,max(abs(x) for x in p))
        if k%max(1,steps//120)==0 or k==steps-1:
            history.append({"time_s":(k+1)*dt,"bottom_perturbation_pa":p[0],"top_outflow_m3_s":area*u[-1],
                            "storage_volume_m3":storage,"net_boundary_volume_m3":balance,"balance_residual_m3":storage-balance,
                            "downward_pipe_speed_m_s":speed_at(motion,(k+1)*dt)})
    return {"minimum":minimum,"maximum":maximum,"minimum_times":tmin,"maximum_times":tmax,"final":p,"history":history,
            "dt_s":dt,"dx_m":dx,"steps":steps,"cfl":c*dt/dx,"maximum_mass_balance_residual_kg":rho*maxres,
            "maximum_fluid_speed_m_s":maxspeed,"maximum_relative_storage_change":pmax/(rho*c*c)}

def surge(v,geometry,path,hydraulic_input,hydraulic_result):
    h=HydraulicsInput.model_validate(hydraulic_input)
    base={"model_version":"M9-acoustic-piston-1","approval_issued":False,"equipment_authority":"none",
          "scope":"Fixed uniform annulus, linear acoustic pressure perturbations about static head; piston displacement; constant Newtonian laminar drag.",
          "hydraulics_calculation_id":v.hydraulics_calculation_id}
    if v.bottom_md_m>path.depths[-1]:raise ValueError("Transient interval exceeds survey.")
    reasons=[]
    if v.evidence_state=="unknown":reasons.append("Motion and boundary evidence unknown.")
    if hydraulic_result.get("status")=="withheld":reasons.append("Linked hydraulics is withheld.")
    if h.mud.rheology!="newtonian":reasons.append("Transient drag requires Newtonian viscosity; gel/non-Newtonian flow unsupported.")
    if reasons:return {**base,"status":"withheld","reasons":reasons,"profile":[],"history":[]}
    segments=build_segments(h,geometry,path)
    selected=[s for s in segments if max(s["top_md_m"],v.top_md_m)<min(s["bottom_md_m"],v.bottom_md_m)]
    if not selected or min(s["top_md_m"] for s in selected)>v.top_md_m or max(s["bottom_md_m"] for s in selected)<v.bottom_md_m:
        raise ValueError("Transient interval requires complete hydraulic geometry coverage.")
    s=selected[0];a,b=s["string_od_m"]/2,s["bore_diameter_m"]/2
    if any(abs(x["bore_diameter_m"]-2*b)>1e-9 or abs(x["string_od_m"]-2*a)>1e-9 or abs(x["string_id_m"]-s["string_id_m"])>1e-9 for x in selected):
        return {**base,"status":"withheld","reasons":["Uniform-annulus acoustic scope excludes diameter transitions."],"profile":[],"history":[]}
    area=math.pi*(b*b-a*a);disp=math.pi*a*a
    if v.displacement=="open_end_instant_fill":disp-=math.pi*s["string_id_m"]**2/4
    length=v.bottom_md_m-v.top_md_m;rho=h.mud.density_kg_m3;mu=h.mud.consistency_pa_sn;c=v.wave_speed_m_s
    displacement=0.;maxmove=0.
    for x,y in zip(v.motion,v.motion[1:]):
        # piecewise-linear velocity: exact displacement extrema occur at zero crossing.
        dt=y.time_s-x.time_s
        if x.downward_speed_m_s*y.downward_speed_m_s<0:
            z=-x.downward_speed_m_s*dt/(y.downward_speed_m_s-x.downward_speed_m_s)
            maxmove=max(maxmove,abs(displacement+x.downward_speed_m_s*z/2))
        displacement+=(x.downward_speed_m_s+y.downward_speed_m_s)*dt/2;maxmove=max(maxmove,abs(displacement))
    if maxmove>.01*length:
        return {**base,"status":"withheld","reasons":["Motion displacement exceeds 1% of interval length; fixed-domain approximation withheld."],"profile":[],"history":[]}
    gradient=flow_gradient(1e-5,a,b,mu,1.,0.)["gradient_pa_m"]
    lam=gradient/(rho*(1e-5/area))
    cases=[acoustic(length,area,disp,rho,c,lam,v.motion,n) for n in (v.cells,v.cells*2,v.cells*4)]
    coarse,mid,fine=cases
    # Compare extrema aggregated to the original coarse cells (not mismatched centers).
    def compare(a,b):
        ratio=len(b["minimum"])//len(a["minimum"])
        return max(max(abs(a["minimum"][i]-min(b["minimum"][i*ratio:(i+1)*ratio])),
                       abs(a["maximum"][i]-max(b["maximum"][i*ratio:(i+1)*ratio]))) for i in range(len(a["minimum"])))
    changes=[compare(coarse,mid),compare(mid,fine)]
    profile=[]
    for j,(low,high) in enumerate(zip(fine["minimum"],fine["maximum"])):
        md=v.bottom_md_m-(j+.5)*fine["dx_m"];tvd=path.at(md)["tvd_m"]
        static=h.surface_backpressure_pa+rho*G*tvd;window=window_at(h.pressure_window,md)
        profile.append({"md_m":md,"tvd_m":tvd,"minimum_gauge_pa":static+low,"maximum_gauge_pa":static+high,
                        "minimum_time_s":fine["minimum_times"][j],"maximum_time_s":fine["maximum_times"][j],
                        "lower_margin_pa":static+low-window["lower_pa"],"upper_margin_pa":window["upper_pa"]-static-high,
                        "minimum_perturbation_pa":low,"maximum_perturbation_pa":high})
    profile.sort(key=lambda r:r["md_m"])
    re=rho*fine["maximum_fluid_speed_m_s"]*(2*b-2*a)/mu
    if re>1000:reasons.append("Transient peak annular Reynolds number exceeds 1000.")
    if fine["maximum_relative_storage_change"]>.01:reasons.append("Pressure perturbation exceeds 1% effective storage change; linear compressibility envelope exceeded.")
    if min(p["minimum_gauge_pa"] for p in profile)<-101325.:
        reasons.append("Gauge pressure falls below vacuum assuming 101325 Pa atmosphere; single-phase acoustic model is outside scope.")
    converged=changes[-1]<=v.convergence_tolerance_pa
    if not converged:reasons.append("Grid/time refinement change exceeds the declared pressure tolerance.")
    lower=min(profile,key=lambda r:r["lower_margin_pa"]);upper=min(profile,key=lambda r:r["upper_margin_pa"])
    if lower["lower_margin_pa"]<0 or upper["upper_margin_pa"]<0:reasons.append("Transient exceeds supplied pressure window at a tested cell/time.")
    # Top pressure is prescribed; include its static margin explicitly.
    topstatic=h.surface_backpressure_pa+rho*G*path.at(v.top_md_m)["tvd_m"];topwindow=window_at(h.pressure_window,v.top_md_m)
    boundary={"md_m":v.top_md_m,"gauge_pa":topstatic,"lower_margin_pa":topstatic-topwindow["lower_pa"],"upper_margin_pa":topwindow["upper_pa"]-topstatic}
    if min(boundary["lower_margin_pa"],boundary["upper_margin_pa"])<0:reasons.append("Prescribed top boundary exceeds supplied pressure window.")
    return {**base,"status":"research_scenario" if not reasons else "incomplete_assessment","reasons":reasons,
            "profile":profile,"history":fine["history"],"maximum_reynolds":re,"maximum_pipe_displacement_m":maxmove,
            "grid_cells":[v.cells,v.cells*2,v.cells*4],"refinement_changes_pa":changes,"numerical_tolerance_met":converged,
            "minimum_lower_margin":lower,"minimum_upper_margin":upper,"top_boundary":boundary,
            "maximum_mass_balance_residual_kg":fine["maximum_mass_balance_residual_kg"],
            "maximum_relative_storage_change":fine["maximum_relative_storage_change"],"time_step_s":fine["dt_s"],"cfl":fine["cfl"],
            "limitations":["Reduced piston/displacement model excludes pipe-wall entrainment, variable geometry, internal-fluid transients, gel and gas.",
                          "Wave speed is supplied; fluid/structure compressibility is not inferred.",
                          "Pressure extrema are discrete cell/time extrema, not certified continuous well/time limits.",
                          "Grid refinement is an indicator, not an error bound or operational trip-speed approval."]}
