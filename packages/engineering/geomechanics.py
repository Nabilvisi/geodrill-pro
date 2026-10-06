"""Survey-bound isotropic elastic research. Compression positive.
Mogi-Coulomb: Al-Ajmi/Zimmerman (2009), doi:10.1016/j.petrol.2009.05.018.
Supplied certificate identifiers and hashes are assertions, not qualification.
"""
import math
from typing import Literal
import numpy as np
from pydantic import Field, model_validator
from .models import Contract
from .physics import G
from .research_common import StudyInput, base
from .stability import tangent

class TriaxialCoreTest(Contract):
    specimen_id: str = Field(min_length=1,max_length=80)
    confining_pressure_pa: float = Field(ge=0,le=2e8)
    peak_axial_stress_pa: float = Field(gt=0,le=1e9)
    pore_pressure_pa: float = Field(ge=0,le=2e8)
    cohesion_pa: float = Field(gt=0,le=2e8)
    friction_angle_deg: float = Field(gt=0,lt=60)
    unconfined_compressive_strength_pa: float = Field(gt=0,le=5e8)
    tensile_strength_pa: float = Field(ge=0,le=1e8)
    youngs_modulus_pa: float = Field(gt=1e8,le=2e11)
    poissons_ratio: float = Field(gt=0,lt=.5)
    biot_coefficient: float = Field(gt=0,le=1)
    test_standard: str = Field(min_length=3,max_length=100)
    certificate_id: str = Field(min_length=3,max_length=100)
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")

class StressCalibrationEvidence(Contract):
    method: Literal["LOT","XLOT","minifrac","acoustic_derivation"]
    measured_shmin_gradient_sg: float = Field(gt=.5,le=3.5)
    test_depth_tvd_m: float = Field(gt=0,le=15000)
    closure_pressure_gauge_pa: float = Field(gt=0,le=2e8)
    pressure_reference: Literal["at_test_depth","wellhead"] = "at_test_depth"
    calibration_quality: Literal["verified_closure","p_lot_tangent","unverified"]
    evidence_note: str = Field(min_length=3,max_length=500)
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")

class GeomechanicsInput(StudyInput):
    md_m: float = Field(gt=0,le=30000)
    azimuth_shmax_deg: float = Field(ge=0,lt=360)
    stress_north_reference: Literal["true","grid"]
    overburden_gradient_sg: float = Field(gt=1,le=3.5)
    pore_pressure_sg: float = Field(gt=.8,le=2.5)
    tectonic_strain_x: float = Field(default=0,ge=-.01,le=.01)
    tectonic_strain_y: float = Field(default=0,ge=-.01,le=.01)
    core_test: TriaxialCoreTest | None = None
    stress_calibration: StressCalibrationEvidence | None = None
    surface_temperature_c: float = Field(default=15,ge=-20,le=60)
    geothermal_gradient_c_per_100m: float = Field(default=3,ge=.5,le=10)
    base_mud_density_sg: float = Field(gt=.8,le=2.5)
    mud_compressibility_per_pa: float = Field(default=4e-10,ge=0,le=2e-9)
    mud_thermal_expansion_per_c: float = Field(default=6e-4,ge=0,le=2e-3)
    shear_failure_model: Literal["mohr_coulomb","mogi_coulomb"] = "mohr_coulomb"
    minimum_tested_pressure_sg: float = Field(default=.8,ge=.5,le=3.5)
    maximum_tested_pressure_sg: float = Field(default=3.5,ge=.5,le=3.5)
    @model_validator(mode="after")
    def hierarchy(self):
        if self.pore_pressure_sg >= self.overburden_gradient_sg:
            raise ValueError("Pore-pressure gradient must be below overburden.")
        if self.minimum_tested_pressure_sg >= self.maximum_tested_pressure_sg:
            raise ValueError("Tested pressure range must be ordered.")
        return self

def calculate_in_situ_stresses(v,depth_tvd_m):
    if v.core_test is None:raise ValueError("Supplied elastic properties required; no default rock substituted.")
    k=v.core_test
    sv,pp=(gradient*1000*G*depth_tvd_m for gradient in (v.overburden_gradient_sg,v.pore_pressure_sg))
    iso=k.poissons_ratio/(1-k.poissons_ratio)*(sv-k.biot_coefficient*pp)+k.biot_coefficient*pp
    elastic=k.youngs_modulus_pa/(1-k.poissons_ratio**2)
    sh=iso+elastic*(v.tectonic_strain_x+k.poissons_ratio*v.tectonic_strain_y)
    sH=iso+elastic*(v.tectonic_strain_y+k.poissons_ratio*v.tectonic_strain_x)
    original=sh
    if v.stress_calibration is not None and v.stress_calibration.calibration_quality=="verified_closure":
        sh=v.stress_calibration.measured_shmin_gradient_sg*1000*G*depth_tvd_m
    return dict(depth_tvd_m=depth_tvd_m,overburden_sv_pa=sv,min_horizontal_sh_pa=sh,max_horizontal_sH_pa=sH,
                uncalibrated_sh_pa=original,pore_pressure_pp_pa=pp,effective_sv_pa=sv-k.biot_coefficient*pp,
                effective_sh_pa=sh-k.biot_coefficient*pp,effective_sH_pa=sH-k.biot_coefficient*pp)

def downhole_fluid_density(base_sg,depth_tvd_m,surface_temp_c,geothermal_grad,compressibility,thermal_exp):
    """Integrate dPg/dz=rho0*g*(1+c*Pg-alpha*gradient*z), Pg(0)=0.
    First-order constitutive approximation, 20% component limit, no clipping/ECD/EOS.
    """
    rho0=base_sg*1000;z=depth_tvd_m;x=rho0*G*compressibility*z
    beta=thermal_exp*geothermal_grad/100
    if abs(x)<1e-4:
        exprel=1+x/2+x*x/6+x**3/24+x**4/120
        phi2=.5+x/6+x*x/24+x**3/120+x**4/720
    else:
        exprel=math.expm1(x)/x;phi2=(math.expm1(x)-x)/(x*x)
    pg=rho0*G*z*(exprel-beta*z*phi2)
    compression=compressibility*pg;expansion=beta*z
    rho=rho0*(1+compression-expansion)
    eligible=pg>=0 and rho>0 and max(abs(compression),abs(expansion))<=.2
    return dict(status="research_scenario" if eligible else "outside_applicability",surface_density_kg_m3=rho0,
                downhole_temperature_c=surface_temp_c+geothermal_grad*z/100,
                downhole_gauge_pressure_pa=pg if eligible else None,
                downhole_density_kg_m3=rho if eligible else None,downhole_density_sg=rho/1000 if eligible else None,
                compressive_fraction=compression,thermal_expansion_fraction=expansion,
                constitutive_component_limit=.2,pressure_basis="Gauge pressure relative to surface; hydrostatic integral only")

def failure_margins(principal,core,model):
    """Effective eigenvalues ascending along final axis. Pa margins."""
    s3,s2,s1=np.moveaxis(np.asarray(principal),-1,0)
    phi=math.radians(core.friction_angle_deg)
    if model=="mohr_coulomb":
        q=(1+math.sin(phi))/(1-math.sin(phi))
        shear=core.unconfined_compressive_strength_pa+q*s3-s1
    else:
        a=2*math.sqrt(2)*core.cohesion_pa*math.cos(phi)/3
        b=2*math.sqrt(2)*math.sin(phi)/3
        octahedral=np.sqrt((s1-s2)**2+(s2-s3)**2+(s1-s3)**2)/3
        shear=a+b*(s1+s3)/2-octahedral
    return shear,s3+core.tensile_strength_pa

def wall_profile(tensor,pressure,pp,core,angles,model):
    theta=np.arange(angles)*2*math.pi/angles
    xx,yy,zz=tensor[0,0],tensor[1,1],tensor[2,2]
    dev=(xx-yy)*np.cos(2*theta)+2*tensor[0,1]*np.sin(2*theta)
    support=pressure-core.biot_coefficient*pp
    hoop=xx+yy-2*dev-support
    axial=zz-2*core.poissons_ratio*dev
    shear=2*(tensor[1,2]*np.cos(theta)-tensor[0,2]*np.sin(theta))
    mean=(hoop+axial)/2;radius=np.hypot((hoop-axial)/2,shear)
    principal=np.sort(np.stack((np.full(angles,support),mean-radius,mean+radius),axis=-1),axis=-1)
    shear_margin,tensile_margin=failure_margins(principal,core,model)
    return theta,hoop,axial,shear,principal,shear_margin,tensile_margin

def pressure_intervals(tensor,pp,core,model,z,lower,upper,angles,points):
    scale=1000*G*z;low=max(lower*scale,pp);high=upper*scale
    if low>=high:return []
    def margin(p):
        row=wall_profile(tensor,p,pp,core,angles,model)
        return float(min(row[-2].min(),row[-1].min()))
    pressures=np.linspace(low,high,points);margins=[margin(p) for p in pressures];crossings=[]
    for p0,p1,f0,f1 in zip(pressures,pressures[1:],margins,margins[1:]):
        if (f0>=0)!=(f1>=0):
            a,b=float(p0),float(p1)
            for _ in range(40):
                mid=(a+b)/2
                if (margin(mid)>=0)==(f0>=0):a=mid
                else:b=mid
                if b-a<=1:break
            crossings.append((a+b)/2)
    bounds=[low,*crossings,high];result=[]
    for a,b in zip(bounds,bounds[1:]):
        if margin((a+b)/2)>=0:
            result.append(dict(lower_gauge_pa=a,upper_gauge_pa=b,lower_equivalent_sg=a/scale,upper_equivalent_sg=b/scale,
                               lower_at_test_boundary=a==low,upper_at_test_boundary=b==high))
    return result

def calculate_geomechanics(v,geometry=None,path=None):
    out=base("GD-A17-geomechanics-stability-2",
             "Survey-oriented isotropic elastic wall-stress and failure-envelope research with linear hydrostatic density integration.",
             ["Core/calibration identifiers, hashes and verification states are supplied assertions; independent assessment is not established.",
              "Homogeneous isotropic linear elasticity, circular impermeable hole; no plasticity, pore diffusion, chemical or rock thermal-stress solution.",
              "Pressure intervals are numerically sampled elastic-criterion scenarios in the declared range, not approved mud windows, fracture propagation or loss predictions.",
              "Angular/pressure refinement bounds numerical sampling only; no field prediction, casing-seat decision or equipment command.",
              "Equivalent stress gradients and hydrostatic depth use the declared survey datum; fluid gauge pressure is assumed zero at that datum."])
    out.update(stability_window=None,independent_evidence_verification=False,clearance_generated=False)
    reasons=[]
    if path is None:reasons.append("Accepted immutable survey context is required.")
    if v.evidence_state=="unknown":reasons.append("Formation evidence state is unknown.")
    if v.core_test is None:reasons.append("Core properties and supplied certificate/source hash are missing.")
    if v.stress_calibration is None:reasons.append("Stress calibration record and source hash are missing.")
    if path is None:out.update(status="withheld",reasons=reasons);return out
    z=path.at(v.md_m)["tvd_m"]
    if not 0<z<=15000:raise ValueError("Geomechanics TVD must be positive and at most 15000 m.")
    direction=np.array(tangent(path,v.md_m));ref=np.array([1.,0.,0.] if abs(direction[0])<.9 else [0.,1.,0.])
    axis=ref-np.dot(ref,direction)*direction;axis/=np.linalg.norm(axis)
    axes=np.array([axis,np.cross(direction,axis),direction])
    out.update(md_m=v.md_m,tvd_m=z,stress_north_reference=v.stress_north_reference,inclination_deg=math.degrees(math.acos(float(np.clip(direction[2],-1,1)))),
               azimuth_deg=math.degrees(math.atan2(float(direction[1]),float(direction[0])))%360,
               local_axes_north_east_down=axes.tolist())
    thermo=downhole_fluid_density(v.base_mud_density_sg,z,v.surface_temperature_c,v.geothermal_gradient_c_per_100m,
                                  v.mud_compressibility_per_pa,v.mud_thermal_expansion_per_c)
    out["fluid_thermodynamics"]=thermo
    if thermo["status"]=="outside_applicability":reasons.append("Linear fluid-density component change exceeds the declared 20% range; no density is clipped.")
    core=v.core_test;calibration=v.stress_calibration
    out["supplied_evidence"]={"core":core.model_dump() if core else None,
                              "stress_calibration":calibration.model_dump() if calibration else None,
                              "independently_verified":False}
    if core:
        ucs=2*core.cohesion_pa*math.cos(math.radians(core.friction_angle_deg))/(1-math.sin(math.radians(core.friction_angle_deg)))
        if abs(ucs-core.unconfined_compressive_strength_pa)>.05*ucs:
            reasons.append("Supplied UCS differs by more than 5% from the supplied cohesion/friction envelope; reconcile the fits.")
        if core.peak_axial_stress_pa<core.confining_pressure_pa or core.pore_pressure_pa>core.confining_pressure_pa:
            reasons.append("Supplied core stress ordering is inconsistent.")
    if calibration:
        if calibration.calibration_quality!="verified_closure" or calibration.method=="acoustic_derivation":
            reasons.append("A supplied closure-pressure calibration is required; tangent LOT/acoustic claims do not establish Shmin.")
        if calibration.pressure_reference!="at_test_depth":reasons.append("Wellhead pressure requires an explicit hydrostatic conversion before calibration.")
        if abs(calibration.test_depth_tvd_m-z)>1:reasons.append("Calibration depth differs from study TVD; no unvalidated gradient extrapolation is performed.")
        expected=calibration.measured_shmin_gradient_sg*1000*G*calibration.test_depth_tvd_m
        if abs(expected-calibration.closure_pressure_gauge_pa)>.02*expected:
            reasons.append("Calibration gradient and at-depth closure pressure disagree by more than 2%.")
    if reasons:out.update(status="withheld",reasons=reasons);return out
    stresses=calculate_in_situ_stresses(v,z);out["in_situ_stresses"]=stresses
    if stresses["max_horizontal_sH_pa"]<stresses["min_horizontal_sh_pa"] or stresses["min_horizontal_sh_pa"]<0:
        out.update(status="withheld",reasons=["Calibrated Shmin and strain-derived SHmax have inconsistent ordering; no invented uplift is applied."]);return out
    a=math.radians(v.azimuth_shmax_deg);n=np.array([math.cos(a),math.sin(a),0.]);e=np.array([-math.sin(a),math.cos(a),0.])
    total=stresses["max_horizontal_sH_pa"]*np.outer(n,n)+stresses["min_horizontal_sh_pa"]*np.outer(e,e)+np.diag([0,0,stresses["overburden_sv_pa"]])
    pp=stresses["pore_pressure_pp_pa"]
    local=axes@(total-core.biot_coefficient*pp*np.eye(3))@axes.T;out["local_effective_tensor_pa"]=local.tolist()
    coarse=pressure_intervals(local,pp,core,v.shear_failure_model,z,v.minimum_tested_pressure_sg,v.maximum_tested_pressure_sg,360,81)
    fine=pressure_intervals(local,pp,core,v.shear_failure_model,z,v.minimum_tested_pressure_sg,v.maximum_tested_pressure_sg,1440,161)
    change=max((abs(a[k]-b[k]) for a,b in zip(coarse,fine) for k in ("lower_gauge_pa","upper_gauge_pa")),default=0) if len(coarse)==len(fine) else None
    converged=change is not None and change<=500
    theta,hoop,axial,shear,principal,shear_margin,tensile_margin=wall_profile(local,thermo["downhole_gauge_pressure_pa"],pp,core,1440,v.shear_failure_model)
    out.update(status="research_scenario" if converged else "nonconverged",elastic_pressure_intervals=fine if converged else [],
               numerical_refinement=dict(coarse_angles=360,fine_angles=1440,coarse_pressure_seeds=81,fine_pressure_seeds=161,
                                         maximum_boundary_change_pa=change,boundary_tolerance_pa=500,root_tolerance_pa=1,passed=converged),
               minimum_shear_margin_pa=float(shear_margin.min()),minimum_tensile_margin_pa=float(tensile_margin.min()),
               supplied_mud_pressure_gauge_pa=thermo["downhole_gauge_pressure_pa"],
               failure_screen_exceeded=bool(min(shear_margin.min(),tensile_margin.min())<0),failure_criterion=v.shear_failure_model,
               profile=[dict(angle_deg=math.degrees(float(theta[i])),hoop_effective_pa=float(hoop[i]),axial_effective_pa=float(axial[i]),
                             wall_shear_pa=float(shear[i]),minimum_principal_pa=float(principal[i,0]),intermediate_principal_pa=float(principal[i,1]),
                             maximum_principal_pa=float(principal[i,2]),shear_margin_pa=float(shear_margin[i]),tensile_margin_pa=float(tensile_margin[i])) for i in range(0,1440,4)])
    if not converged:out["reasons"].append("Angular/pressure seed refinement does not meet declared boundary tolerance.")
    if not fine:out["reasons"].append("No passing elastic-criterion interval found in the declared sampled pressure range.")
    if out["failure_screen_exceeded"]:out["reasons"].append("Supplied mud-pressure scenario exceeds a sampled wall-strength criterion.")
    return out
