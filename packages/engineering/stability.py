"""Isotropic impermeable-wall Kirsch research scenarios. Compression positive."""
import math
from typing import Literal
from pydantic import Field, model_validator
from .models import Contract
from .geometry import Path

class StabilityInput(Contract):
    study_name: str = Field(min_length=3, max_length=100)
    geometry_revision_id: str
    depth_datum: str
    md_m: float = Field(ge=0, le=30000)
    evidence_state: Literal["unknown", "supplied", "synthetic"] = "unknown"
    source_note: str = Field(min_length=3, max_length=500)
    model: Literal["isotropic_elastic_impermeable", "anisotropic", "coupled_poroelastic", "plastic"] = "isotropic_elastic_impermeable"
    stress_north_pa: float = Field(ge=0, le=1e9)
    stress_east_pa: float = Field(ge=0, le=1e9)
    stress_vertical_pa: float = Field(ge=0, le=1e9)
    stress_ne_pa: float = Field(ge=-1e9, le=1e9)
    stress_nv_pa: float = Field(ge=-1e9, le=1e9)
    stress_ev_pa: float = Field(ge=-1e9, le=1e9)
    pore_pressure_pa: float = Field(ge=0, le=1e9)
    wall_pressure_pa: float = Field(ge=0, le=1e9)
    young_modulus_pa: float = Field(gt=0, le=3e11)
    poisson_ratio: float = Field(ge=0, lt=.5)
    expansion_per_k: float = Field(ge=0, le=.001)
    delta_temperature_k: float = Field(ge=-300, le=300)
    thermal_scope: Literal["none", "restrained_wall_estimate"] = "none"
    ucs_pa: float = Field(gt=0, le=1e9)
    tensile_strength_pa: float = Field(ge=0, le=1e8)
    friction_angle_deg: float = Field(ge=0, lt=60)
    pressure_basis_note: str = Field(min_length=3, max_length=500)
    external_lower_pa: float | None = Field(default=None, ge=0, le=1e9)
    external_upper_pa: float | None = Field(default=None, ge=0, le=1e9)
    external_bounds_state: Literal["none", "supplied", "externally_approved"] = "none"
    external_bounds_note: str | None = Field(default=None, min_length=3, max_length=500)
    @model_validator(mode="after")
    def physical(self):
        # All principal total stresses must be nonnegative (Sylvester principal minors).
        a,b,c=self.stress_north_pa,self.stress_east_pa,self.stress_vertical_pa
        d,e,f=self.stress_ne_pa,self.stress_nv_pa,self.stress_ev_pa
        if min(a*b-d*d,a*c-e*e,b*c-f*f)<-1e-8 or a*b*c+2*d*e*f-a*f*f-b*e*e-c*d*d < -1e-8:
            raise ValueError("Total stress tensor must be positive semidefinite.")
        if self.thermal_scope=="none" and self.delta_temperature_k!=0:
            raise ValueError("Nonzero temperature change requires the restrained-wall thermal estimate.")
        if self.external_bounds_state!="none":
            if self.external_lower_pa is None or self.external_upper_pa is None or not self.external_bounds_note or self.external_lower_pa>=self.external_upper_pa:
                raise ValueError("External bounds require ordered limits and provenance.")
        elif any(x is not None for x in (self.external_lower_pa,self.external_upper_pa,self.external_bounds_note)):
            raise ValueError("Declare the evidence state of external bounds.")
        return self

def tangent(path, md):
    import bisect
    i=max(0,min(len(path.stations)-2,bisect.bisect_right(path.depths,md)-1))
    a,b,va,vb,beta=path.segment(i)
    t=(md-a.md_m)/(b.md_m-a.md_m)
    if beta<1e-7:
        v=[x+t*(y-x) for x,y in zip(va,vb)]
    else:
        v=[(math.sin((1-t)*beta)*x+math.sin(t*beta)*y)/math.sin(beta) for x,y in zip(va,vb)]
    norm=math.sqrt(sum(x*x for x in v))
    return [x/norm for x in v]

def rotate_tensor(v, md, path):
    z=tangent(path,md)
    ref=[1.,0.,0.] if abs(z[0])<.9 else [0.,1.,0.]
    x=[a-sum(a*b for a,b in zip(ref,z))*b for a,b in zip(ref,z)]
    norm=math.sqrt(sum(a*a for a in x));x=[a/norm for a in x]
    y=[z[1]*x[2]-z[2]*x[1],z[2]*x[0]-z[0]*x[2],z[0]*x[1]-z[1]*x[0]]
    s=[[v.stress_north_pa-v.pore_pressure_pa,v.stress_ne_pa,v.stress_nv_pa],
       [v.stress_ne_pa,v.stress_east_pa-v.pore_pressure_pa,v.stress_ev_pa],
       [v.stress_nv_pa,v.stress_ev_pa,v.stress_vertical_pa-v.pore_pressure_pa]]
    axes=[x,y,z]
    return [[sum(a[i]*s[i][j]*b[j] for i in range(3) for j in range(3)) for b in axes] for a in axes],axes

def wall_stress(s, support, nu, thermal, theta):
    xx,yy,zz,xy,xz,yz=s[0][0],s[1][1],s[2][2],s[0][1],s[0][2],s[1][2]
    dev=(xx-yy)*math.cos(2*theta)+2*xy*math.sin(2*theta)
    hoop=xx+yy-2*dev-support+thermal
    axial=zz-2*nu*dev+thermal
    shear=2*(yz*math.cos(theta)-xz*math.sin(theta))
    mean=(hoop+axial)/2;radius=math.hypot((hoop-axial)/2,shear)
    principal=sorted([support,mean-radius,mean+radius])
    return hoop,axial,shear,principal

def stability(v: StabilityInput, path: Path):
    if v.md_m>path.depths[-1]: raise ValueError("Stability MD is outside the accepted survey.")
    base={"model_version":"M7-kirsch-1","approval_issued":False,"equipment_authority":"none",
          "stress_convention":"compression positive; effective stress = total - pore pressure (Biot = 1)",
          "scope":"Homogeneous isotropic linear elasticity, circular hole, perfect impermeable mudcake; no pressure-limit generation.",
          "external_bounds":{"state":v.external_bounds_state,"lower_pa":v.external_lower_pa,"upper_pa":v.external_upper_pa,"note":v.external_bounds_note,"approval_verified":False}}
    reasons=[]
    if v.evidence_state=="unknown":reasons.append("Stress, strength and thermal evidence unknown.")
    if v.model!="isotropic_elastic_impermeable":reasons.append("Anisotropy, plasticity and coupled pore diffusion are outside this model.")
    if reasons:return {**base,"status":"withheld","reasons":reasons,"profile":[]}
    s,axes=rotate_tensor(v,v.md_m,path)
    thermal=v.young_modulus_pa*v.expansion_per_k*v.delta_temperature_k/(1-v.poisson_ratio) if v.thermal_scope!="none" else 0.
    phi=math.radians(v.friction_angle_deg);q=(1+math.sin(phi))/(1-math.sin(phi))
    def evaluate(n):
        rows=[]
        for k in range(n):
            theta=2*math.pi*k/n
            hoop,axial,shear,p=wall_stress(s,v.wall_pressure_pa-v.pore_pressure_pa,v.poisson_ratio,thermal,theta)
            rows.append({"angle_deg":360*k/n,"hoop_effective_pa":hoop,"axial_effective_pa":axial,"shear_pa":shear,
                         "minimum_principal_pa":p[0],"maximum_principal_pa":p[2],
                         "tensile_margin_pa":p[0]+v.tensile_strength_pa,"mohr_coulomb_margin_pa":v.ucs_pa+q*p[0]-p[2]})
        return rows
    coarse=evaluate(360);fine=evaluate(1440)
    minima={key:min(fine,key=lambda r:r[key]) for key in ("tensile_margin_pa","mohr_coulomb_margin_pa")}
    change={key:abs(min(r[key] for r in coarse)-min(r[key] for r in fine)) for key in minima}
    return {**base,"status":"research_scenario","reasons":[human for key,human in (("tensile_margin_pa","Tensile strength screen exceeded at a tested angle."),("mohr_coulomb_margin_pa","Mohr-Coulomb strength screen exceeded at a tested angle.")) if minima[key][key]<0],
            "md_m":v.md_m,"tvd_m":path.at(v.md_m)["tvd_m"],"local_axes_north_east_down":axes,"local_effective_tensor_pa":s,
            "thermal_stress_estimate_pa":thermal,"thermal_limitation":"Uniform restrained-wall estimate only; no transient thermal diffusion or coupled pore-pressure solution.",
            "angular_resolution_deg":.25,"angular_refinement_change_pa":change,"limiting_angles":minima,
            "failure_screen_exceeded":any(r[k]<0 for k,r in minima.items()),"profile":fine[::4],
            "limitations":["Strength criteria are screening assumptions; no collapse, fracture-propagation or losses prediction.","External approval is supplied metadata and has not been verified."]}
