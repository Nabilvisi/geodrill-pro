"""Characterized binary PR flash and reviewed external mud/gas phase-study replay."""
import math
from typing import Literal
from pydantic import Field,model_validator
from .models import Contract
from .research_common import StudyInput,base
R=8.31446261815324
SQRT2=math.sqrt(2.)

class GasComponent(Contract):
    name: str = Field(min_length=1,max_length=80)
    critical_temperature_k: float = Field(gt=50,le=1000)
    critical_pressure_pa: float = Field(gt=1e5,le=1e8)
    acentric_factor: float = Field(ge=-.2,le=1)
    mole_fraction: float = Field(gt=1e-6,lt=1)
class PhasePoint(Contract):
    md_m: float = Field(ge=0,le=30000)
    time_s: float = Field(ge=0,le=1e6)
    absolute_pressure_pa: float = Field(ge=1e4,le=1e8)
    temperature_k: float = Field(ge=100,le=650)
    vapor_fraction: float = Field(ge=0,le=1)
    vapor_composition: list[float] = Field(min_length=2,max_length=10)
    liquid_composition: list[float] = Field(min_length=2,max_length=10)
    dissolved_gas_mol: float = Field(ge=0,le=1e9)
    vapor_molar_volume_m3_mol: float = Field(gt=0,le=10)
    material_balance_residual_mol: float = Field(ge=0,le=1e9)
    converged: bool
    phase_stability_checked: bool
    @model_validator(mode="after")
    def composition(self):
        for comp in (self.vapor_composition,self.liquid_composition):
            if any(not math.isfinite(x) or x<0 for x in comp) or abs(sum(comp)-1)>1e-8:raise ValueError("Phase compositions must be finite, nonnegative and normalized.")
        if len(self.vapor_composition)!=len(self.liquid_composition):raise ValueError("Phase component lists must align.")
        return self

class GasInput(StudyInput):
    mode: Literal["native_binary_flash","external_mud_gas_review"]
    fluid_system: Literal["characterized_nonpolar_binary","actual_mud_gas","uncharacterized"]
    characterization_note: str = Field(min_length=3,max_length=500)
    components: list[GasComponent] = Field(default_factory=list,max_length=2)
    binary_interaction: float = Field(ge=-.5,le=.5)
    absolute_pressure_pa: float = Field(ge=1e4,le=1e8)
    temperature_k: float = Field(ge=100,le=650)
    external_model_reference: str | None = Field(default=None,min_length=3,max_length=500)
    external_review_state: Literal["unknown","reviewed"]
    external_review_note: str | None = Field(default=None,min_length=3,max_length=500)
    external_points: list[PhasePoint] = Field(default_factory=list,max_length=100)
    total_gas_inventory_mol: float = Field(ge=0,le=1e9)
    initial_dissolved_gas_mol: float = Field(ge=0,le=1e9)
    mass_transfer_time_s: float = Field(gt=0,le=1e6)
    replay_step_s: float = Field(gt=0,le=600)
    balance_tolerance_mol: float = Field(gt=0,le=1)
    @model_validator(mode="after")
    def declarations(self):
        if self.initial_dissolved_gas_mol>self.total_gas_inventory_mol:raise ValueError("Dissolved inventory exceeds total gas inventory.")
        if self.mode=="native_binary_flash" and (len(self.components)!=2 or abs(sum(c.mole_fraction for c in self.components)-1)>1e-8 or len({c.name for c in self.components})!=2):raise ValueError("Native PR flash requires two unique characterized components with normalized mole fractions.")
        if any(b.time_s<=a.time_s for a,b in zip(self.external_points,self.external_points[1:])):raise ValueError("External replay times must increase.")
        if any(p.dissolved_gas_mol>self.total_gas_inventory_mol for p in self.external_points):raise ValueError("External dissolved inventory exceeds supplied total gas.")
        if self.external_review_state=="reviewed" and (not self.external_review_note or not self.external_model_reference):raise ValueError("Reviewed external phase study requires exact model/reference and review provenance.")
        return self

def cubic_roots(a,b,c):
    # Monic x³+a*x²+b*x+c. Analytical real roots; selected root must satisfy Z>B.
    p=b-a*a/3;q=2*a**3/27-a*b/3+c;disc=(q/2)**2+(p/3)**3
    def cube(x):return math.copysign(abs(x)**(1/3),x)
    if disc>=0:
        d=math.sqrt(disc);return [cube(-q/2+d)+cube(-q/2-d)-a/3]
    angle=math.acos(max(-1.,min(1.,(-q/2)/math.sqrt(-(p/3)**3))))
    return sorted(2*math.sqrt(-p/3)*math.cos((angle+2*j*math.pi)/3)-a/3 for j in range(3))

def pr_fugacity(components,comp,p,t,kij,phase):
    ai=[];bi=[]
    for c in components:
        k=.37464+1.54226*c.acentric_factor-.26992*c.acentric_factor**2
        alpha=(1+k*(1-math.sqrt(t/c.critical_temperature_k)))**2
        ai.append(.45724*R*R*c.critical_temperature_k**2/c.critical_pressure_pa*alpha)
        bi.append(.07780*R*c.critical_temperature_k/c.critical_pressure_pa)
    amatrix=[[math.sqrt(ai[i]*ai[j])*(1-(kij if i!=j else 0.)) for j in range(2)] for i in range(2)]
    am=sum(comp[i]*comp[j]*amatrix[i][j] for i in range(2) for j in range(2));bm=sum(x*b for x,b in zip(comp,bi))
    A=am*p/(R*t)**2;B=bm*p/(R*t)
    roots=[z for z in cubic_roots(B-1,A-3*B*B-2*B,-A*B+B*B+B**3) if z>B+1e-12]
    if not roots:raise ValueError("No physical EOS root.")
    def logs(z):
        logterm=math.log((z+(1+SQRT2)*B)/(z+(1-SQRT2)*B))
        return [bi[i]/bm*(z-1)-math.log(z-B)-A/(2*SQRT2*B)*(2*sum(comp[j]*amatrix[i][j] for j in range(2))/am-bi[i]/bm)*logterm for i in range(2)]
    z=min(roots) if phase=="liquid" else max(roots) if phase=="vapor" else min(roots,key=lambda z:sum(x*f for x,f in zip(comp,logs(z))))
    return logs(z),z

def rachford(z,ks):
    f=lambda beta:sum(x*(k-1)/(1+beta*(k-1)) for x,k in zip(z,ks))
    if f(0)<=0 or f(1)>=0:return None
    lo,hi=0.,1.
    for _ in range(70):
        mid=(lo+hi)/2
        if f(mid)>0:lo=mid
        else:hi=mid
    return (lo+hi)/2

def phase_stability(components,z,p,t,kij):
    ref,zref=pr_fugacity(components,z,p,t,kij,"stable");d=[math.log(x)+f for x,f in zip(z,ref)]
    wilson=[c.critical_pressure_pa/p*math.exp(5.373*(1+c.acentric_factor)*(1-c.critical_temperature_k/t)) for c in components]
    trials=[]
    for seed,phase in [([z[i]*wilson[i] for i in range(2)],"vapor"),([z[i]/wilson[i] for i in range(2)],"liquid"),([.99,.01],"liquid"),([.01,.99],"vapor")]:
        w=[x/sum(seed) for x in seed]
        for iteration in range(150):
            phi,_=pr_fugacity(components,w,p,t,kij,phase)
            unnorm=[math.exp(max(-50.,min(50.,di-f))) for di,f in zip(d,phi)]
            updated=[x/sum(unnorm) for x in unnorm]
            if max(abs(x-y) for x,y in zip(updated,w))<1e-10:
                w=updated;break
            w=[.5*(x+y) for x,y in zip(updated,w)]
        else:raise ValueError("Phase stability iteration did not converge.")
        phi,_=pr_fugacity(components,w,p,t,kij,phase)
        trials.append(sum(x*(math.log(x)+f-di) for x,f,di in zip(w,phi,d)))
    return min(trials),zref,wilson

def flash(components,p,t,kij):
    z=[c.mole_fraction for c in components];tpd,zref,ks=phase_stability(components,z,p,t,kij)
    if tpd>=-1e-8:
        return {"phase":"single_stable","vapor_fraction":None,"single_phase_composition":z,"z_factor":zref,"molar_volume_m3_mol":zref*R*t/p,"minimum_trial_tpd":tpd,"phase_stability_scope":"Four binary trial seeds; not a global multicomponent proof.","material_balance_residual":0.}
    for iteration in range(200):
        beta=rachford(z,ks)
        if beta is None:raise ValueError("Unstable feed lacks a bracketed two-phase split; no false single-phase result issued.")
        x=[zi/(1+beta*(k-1)) for zi,k in zip(z,ks)];y=[k*xi for k,xi in zip(ks,x)]
        xl=[xi/sum(x) for xi in x];yv=[yi/sum(y) for yi in y]
        pl,zl=pr_fugacity(components,xl,p,t,kij,"liquid");pv,zv=pr_fugacity(components,yv,p,t,kij,"vapor")
        residual=max(abs(math.log(k)-l+vv) for k,l,vv in zip(ks,pl,pv))
        balance=max(abs(zi-((1-beta)*xx+beta*yy)) for zi,xx,yy in zip(z,xl,yv))
        if residual<1e-8 and balance<1e-9 and max(abs(xx-yy) for xx,yy in zip(xl,yv))>1e-6:
            return {"phase":"two_phase","vapor_fraction":beta,"liquid_composition":xl,"vapor_composition":yv,"liquid_z":zl,"vapor_z":zv,"liquid_molar_volume_m3_mol":zl*R*t/p,"vapor_molar_volume_m3_mol":zv*R*t/p,"fugacity_log_residual":residual,"material_balance_residual":balance,"minimum_trial_tpd":tpd,"iterations":iteration+1,"phase_stability_scope":"Binary feed trial stability and fugacity equality; no third-phase or drilling-fluid qualification."}
        ks=[math.exp(.5*(math.log(k)+l-vv)) for k,l,vv in zip(ks,pl,pv)]
    raise ValueError("Binary flash failed convergence or collapsed to a trivial split.")

def phase_replay(v,step):
    points=v.external_points;total=v.total_gas_inventory_mol;dissolved=v.initial_dissolved_gas_mol;rows=[]
    if len(points)<2:raise ValueError("External replay needs at least two reviewed points.")
    work=sum(math.ceil((b.time_s-a.time_s)/step) for a,b in zip(points,points[1:]))
    if work>30000:raise ValueError("Phase replay work budget exceeded.")
    rows.append({"time_s":points[0].time_s,"dissolved_gas_mol":dissolved,"free_gas_mol":total-dissolved,"free_gas_volume_m3":(total-dissolved)*points[0].vapor_molar_volume_m3_mol,"inventory_residual_mol":0.})
    for a,b in zip(points,points[1:]):
        n=math.ceil((b.time_s-a.time_s)/step);dt=(b.time_s-a.time_s)/n
        for j in range(1,n+1):
            f=j/n;target=a.dissolved_gas_mol+f*(b.dissolved_gas_mol-a.dissolved_gas_mol)
            dissolved=target+(dissolved-target)*math.exp(-dt/v.mass_transfer_time_s)
            free=total-dissolved;volume=a.vapor_molar_volume_m3_mol+f*(b.vapor_molar_volume_m3_mol-a.vapor_molar_volume_m3_mol)
            rows.append({"time_s":a.time_s+j*dt,"dissolved_gas_mol":dissolved,"free_gas_mol":free,"free_gas_volume_m3":free*volume,"inventory_residual_mol":dissolved+free-total})
    return rows

def gas_phase(v,geometry,path):
    out=base("M16-characterized-phase-1","Binary nonpolar Peng–Robinson equilibrium or reviewed external mud/gas phase studies; prescribed-boundary batch mass-transfer replay.",["Native binary hydrocarbon EOS is not a mud/SBM solubility predictor.","External results remain vendor/specialist interpretations; phase flags and calibration are supplied evidence.","Batch replay conserves gas inventory but does not solve wellbore momentum, energy, slip or transport; no exact emergence depth or well-control schedule."])
    if v.evidence_state=="unknown" or v.fluid_system=="uncharacterized":return {**out,"status":"withheld","reasons":["Fluid characterization/evidence unknown."]}
    if v.mode=="native_binary_flash":
        if v.fluid_system!="characterized_nonpolar_binary":return {**out,"status":"withheld","reasons":["Native EOS excludes drilling-mud mixtures; import reviewed external results."]}
        try:out["equilibrium"]=flash(v.components,v.absolute_pressure_pa,v.temperature_k,v.binary_interaction)
        except (ValueError,ArithmeticError) as error:return {**out,"status":"incomplete_assessment","reasons":[str(error)]}
        out["native_mud_solubility_prediction"]=False;return out
    if v.external_review_state!="reviewed" or not v.external_points:return {**out,"status":"withheld","reasons":["Reviewed exact external model and phase-study points are required."]}
    if any(p.md_m>path.depths[-1] for p in v.external_points):raise ValueError("External study MD exceeds accepted survey.")
    if any(not p.converged or not p.phase_stability_checked or p.material_balance_residual_mol>v.balance_tolerance_mol for p in v.external_points):
        return {**out,"status":"withheld","reasons":["External convergence, phase stability or material-balance evidence incomplete/outside tolerance."]}
    out["profile"]=[p.model_dump() for p in v.external_points];out["external_model_reference"]=v.external_model_reference
    out["external_flags_independently_verified"]=False
    if len(v.external_points)>=2:
        a=phase_replay(v,v.replay_step_s);b=phase_replay(v,v.replay_step_s/2);c=phase_replay(v,v.replay_step_s/4)
        # Endpoint inventory is exact; compare sampled free inventory over the full replay.
        def compare(coarse,fine):
            j=0;errors=[]
            for row in coarse:
                while j+1<len(fine)-1 and fine[j+1]["time_s"]<row["time_s"]:j+=1
                left,right=fine[j:j+2];f=(row["time_s"]-left["time_s"])/(right["time_s"]-left["time_s"])
                errors.append(abs(row["free_gas_mol"]-(left["free_gas_mol"]+f*(right["free_gas_mol"]-left["free_gas_mol"]))))
            return max(errors)
        out.update(history=c,initial_refinement_mol=compare(a,b),final_refinement_mol=compare(b,c),maximum_inventory_residual_mol=max(abs(r["inventory_residual_mol"]) for r in c))
        if out["final_refinement_mol"]>v.balance_tolerance_mol:out.update(status="incomplete_assessment",reasons=["Prescribed-boundary batch replay refinement exceeds supplied tolerance."])
    return out
