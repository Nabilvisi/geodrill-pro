"""Quasi-static soft-string equilibrium in exact minimum-curvature geometry."""
import math
from typing import Literal
from pydantic import Field,model_validator
from .models import Contract
from .physics import G
from .stability import tangent

class DragSection(Contract):
    name: str = Field(min_length=1,max_length=80)
    top_md_m: float = Field(ge=0,le=30000)
    bottom_md_m: float = Field(gt=0,le=30000)
    outside_diameter_m: float = Field(gt=.005,le=2)
    inside_diameter_m: float = Field(ge=0,le=2)
    material_density_kg_m3: float = Field(ge=1000,le=20000)
    friction_coefficient: float = Field(ge=0,le=1)
    young_modulus_pa: float = Field(default=200e9,ge=1e9,le=500e9)
    @model_validator(mode="after")
    def dimensions(self):
        if self.bottom_md_m<=self.top_md_m or self.inside_diameter_m>=self.outside_diameter_m:
            raise ValueError("String intervals and diameters must be physically ordered.")
        return self

class CalibrationPoint(Contract):
    md_m: float = Field(ge=0, le=30000)
    operation: Literal["pickup", "slackoff", "rotating", "combined"]
    measured_hookload_n: float | None = Field(default=None, ge=0, le=1e8)
    measured_torque_nm: float | None = Field(default=None, ge=0, le=1e8)
    split: Literal["train", "holdout"] = "train"
    provenance_note: str = Field(min_length=3, max_length=500)

class TorqueDragInput(Contract):
    model: Literal['soft_string', 'stiff_string'] = 'soft_string'
    tortuosity_rad_m: float = Field(default=0.0,ge=0,le=0.1)
    study_name: str = Field(min_length=3,max_length=100)
    geometry_revision_id: str
    depth_datum: str
    evidence_state: Literal["unknown","supplied","synthetic"] = "unknown"
    source_note: str = Field(min_length=3,max_length=500)
    fluid_density_kg_m3: float = Field(ge=500,le=3000)
    string_sections: list[DragSection] = Field(min_length=1,max_length=50)
    operation: Literal["pickup","slackoff","rotating","combined"]
    axial_speed_m_s: float = Field(ge=-2,le=2)
    rotation_rad_s: float = Field(ge=-100,le=100)
    bottom_tension_n: float = Field(ge=-1e7,le=1e7)
    bottom_torque_nm: float = Field(ge=-1e7,le=1e7)
    step_m: float = Field(ge=.5,le=50)
    friction_delta: float = Field(ge=0,le=.5)
    surface_tension_limit_n: float | None = Field(default=None,gt=0,le=1e9)
    surface_torque_limit_nm: float | None = Field(default=None,gt=0,le=1e9)
    rating_note: str | None = Field(default=None,min_length=3,max_length=500)
    observed_hookload_n: float | None = Field(default=None,ge=-1e7,le=1e8)
    observed_torque_nm: float | None = Field(default=None,ge=-1e7,le=1e8)
    observation_note: str | None = Field(default=None,min_length=3,max_length=500)
    calibration_points: list[CalibrationPoint] = Field(default_factory=list, max_length=100)
    @model_validator(mode="after")
    def declarations(self):
        if self.string_sections[0].top_md_m!=0 or any(a.bottom_md_m!=b.top_md_m for a,b in zip(self.string_sections,self.string_sections[1:])):
            raise ValueError("String sections must be ordered and contiguous from MD 0.")
        if self.operation=="pickup" and not(self.axial_speed_m_s>0 and self.rotation_rad_s==0):
            raise ValueError("Pickup requires positive upward speed and zero rotation.")
        if self.operation=="slackoff" and not(self.axial_speed_m_s<0 and self.rotation_rad_s==0):
            raise ValueError("Slackoff requires negative upward speed and zero rotation.")
        if self.operation=="rotating" and not(self.axial_speed_m_s==0 and self.rotation_rad_s!=0):
            raise ValueError("Rotating requires nonzero rotation and zero axial speed.")
        if self.operation=="combined" and not(self.axial_speed_m_s!=0 and self.rotation_rad_s!=0):
            raise ValueError("Combined operation requires axial motion and rotation.")
        if any(x is not None for x in (self.surface_tension_limit_n,self.surface_torque_limit_nm)) and not self.rating_note:
            raise ValueError("Supplied surface limits require provenance.")
        if any(x is not None for x in (self.observed_hookload_n,self.observed_torque_nm)) and not self.observation_note:
            raise ValueError("Observations require operation and sensor/reference evidence.")
        if any(s.friction_coefficient-self.friction_delta<0 or s.friction_coefficient+self.friction_delta>1 for s in self.string_sections):
            raise ValueError("Friction sensitivity must remain between 0 and 1.")
        if self.calibration_points:
            for p in self.calibration_points:
                if p.measured_hookload_n is None and p.measured_torque_nm is None:
                    raise ValueError("Calibration point must supply at least hookload or torque.")
        return self

def drag_case(v,path,step,mu_delta=0.):
    td=v.string_sections[-1].bottom_md_m
    cuts={0.,td,*[m for m in path.depths if m<td]}
    for s in v.string_sections:
        cuts.update([s.top_md_m,s.bottom_md_m])
        n=math.ceil((s.bottom_md_m-s.top_md_m)/step)
        cuts.update(s.top_md_m+(s.bottom_md_m-s.top_md_m)*j/n for j in range(n+1))
    cuts=sorted(cuts);tension=v.bottom_tension_n;torque=v.bottom_torque_nm
    rows=[{"md_m":td,"tension_n":tension,"torque_nm":torque,"normal_force_n":0.}]
    contact=0.;iterations_max=0
    for lo,hi in reversed(list(zip(cuts,cuts[1:]))):
        mid=(lo+hi)/2;s=next(s for s in v.string_sections if s.top_md_m<=mid<s.bottom_md_m)
        length=hi-lo;t=tangent(path,mid);a=tangent(path,lo);b=tangent(path,hi)
        curvature=[(y-x)/length for x,y in zip(a,b)]
        w=(s.material_density_kg_m3-v.fluid_density_kg_m3)*G*math.pi*(s.outside_diameter_m**2-s.inside_diameter_m**2)/4
        radius=s.outside_diameter_m/2;mu=s.friction_coefficient+mu_delta
        speed=math.hypot(v.axial_speed_m_s,radius*v.rotation_rad_s)
        fraction=v.axial_speed_m_s/speed;rotfraction=radius*v.rotation_rad_s/speed
        estimate=tension+w*t[2]*length
        # Midpoint tension/contact equilibrium; contraction checked explicitly.
        for iteration in range(80):
            mean=(tension+estimate)/2
            normal=math.sqrt(sum((mean*c-w*((1. if j==2 else 0.)-t[2]*t[j]))**2 for j,c in enumerate(curvature)))*length
            updated=tension+w*t[2]*length+mu*normal*fraction
            if abs(updated-estimate)<1e-7*max(1.,abs(updated)):break
            estimate=updated
        else:raise ValueError("Soft-string midpoint equilibrium did not converge.")
        estimate=updated;iterations_max=max(iterations_max,iteration+1)
        torque+=mu*normal*radius*rotfraction;contact+=normal;tension=estimate
        rows.append({"md_m":lo,"tension_n":tension,"torque_nm":torque,"normal_force_n":normal})
    return {"hookload_n":tension,"surface_torque_nm":torque,"summed_normal_force_n":contact,
            "minimum_tension_n":min(r["tension_n"] for r in rows),"maximum_tension_n":max(r["tension_n"] for r in rows),
            "maximum_iterations":iterations_max,"profile":list(reversed(rows))}


def stiff_drag_case(v,geometry,path,step,mu_delta=0.):
    td=v.string_sections[-1].bottom_md_m
    cuts={0.,td,*[m for m in path.depths if m<td]}
    for s in v.string_sections:
        cuts.update([s.top_md_m,s.bottom_md_m])
        n=math.ceil((s.bottom_md_m-s.top_md_m)/step)
        cuts.update(s.top_md_m+(s.bottom_md_m-s.top_md_m)*j/n for j in range(n+1))
    cuts=sorted(cuts);tension=v.bottom_tension_n;torque=v.bottom_torque_nm
    rows=[{"md_m":td,"tension_n":tension,"torque_nm":torque,"normal_force_n":0.}]
    contact=0.;iterations_max=0
    for lo,hi in reversed(list(zip(cuts,cuts[1:]))):
        mid=(lo+hi)/2;s=next(s for s in v.string_sections if s.top_md_m<=mid<s.bottom_md_m)
        length=hi-lo;t=tangent(path,mid);a=tangent(path,lo);b=tangent(path,hi)
        curvature=[(y-x)/length for x,y in zip(a,b)]
        w=(s.material_density_kg_m3-v.fluid_density_kg_m3)*G*math.pi*(s.outside_diameter_m**2-s.inside_diameter_m**2)/4
        radius=s.outside_diameter_m/2;mu=s.friction_coefficient+mu_delta
        speed=math.hypot(v.axial_speed_m_s,radius*v.rotation_rad_s)
        fraction=v.axial_speed_m_s/speed if speed>1e-9 else 0.
        rotfraction=radius*v.rotation_rad_s/speed if speed>1e-9 else 0.
        
        I = math.pi/64*(s.outside_diameter_m**4-s.inside_diameter_m**4)
        EI = s.young_modulus_pa*I
        # Distributed contact from bending shear gradient, |EI d2(kappa)/ds2| in N/m (planar
        # beam approximation). Vanishes on constant-curvature arcs, so the soft-string result is
        # recovered exactly there. Clearance-dependent contact and tortuosity are NOT modelled.
        h=max(1.,length)
        def kmag(sv):
            sv=min(max(sv,h),td-h) if td>2*h else mid
            ta=tangent(path,max(0.,sv-h/2));tb=tangent(path,min(td,sv+h/2))
            return math.sqrt(sum((y-x)**2 for x,y in zip(ta,tb)))/h
        kpp=(kmag(mid+h)-2*kmag(mid)+kmag(mid-h))/(h*h) if td>4*h else 0.
        bending_line=EI*abs(kpp)

        estimate=tension+w*t[2]*length
        for iteration in range(80):
            mean=(tension+estimate)/2
            normal=math.sqrt(sum((mean*c-w*((1. if j==2 else 0.)-t[2]*t[j]))**2 for j,c in enumerate(curvature)))
            normal = (normal + bending_line)*length
            updated=tension+w*t[2]*length+mu*normal*fraction
            if abs(updated-estimate)<1e-7*max(1.,abs(updated)):break
            estimate=updated
        else:raise ValueError("Stiff-string midpoint equilibrium did not converge.")
        estimate=updated;iterations_max=max(iterations_max,iteration+1)
        torque+=mu*normal*radius*rotfraction;contact+=normal;tension=estimate
        rows.append({"md_m":lo,"tension_n":tension,"torque_nm":torque,"normal_force_n":normal})
    return {"hookload_n":tension,"surface_torque_nm":torque,"summed_normal_force_n":contact,
            "minimum_tension_n":min(r["tension_n"] for r in rows),"maximum_tension_n":max(r["tension_n"] for r in rows),
            "maximum_iterations":iterations_max,"profile":list(reversed(rows))}

def torque_drag(v,geometry,path):
    td=v.string_sections[-1].bottom_md_m
    if td>path.depths[-1]:raise ValueError("String exceeds accepted survey.")
    # Installed casing restricts bore; planned strings are not assumed installed.
    for s in v.string_sections:
        covered=0.
        for h in geometry.hole_sections:
            lo,hi=max(s.top_md_m,h.top_md_m),min(s.bottom_md_m,h.bottom_md_m)
            if hi<=lo:continue
            covered+=hi-lo
            if s.outside_diameter_m>=h.diameter_m:raise ValueError("String OD does not clear hole.")
        if abs(covered-(s.bottom_md_m-s.top_md_m))>1e-6:raise ValueError("String requires complete hole coverage.")
        for c in geometry.casings:
            if c.state=="installed" and max(c.top_md_m,s.top_md_m)<min(c.bottom_md_m,s.bottom_md_m) and s.outside_diameter_m>=c.inside_diameter_m:
                raise ValueError("String OD does not clear installed casing.")
    base={"model_version":"M10-soft-string-1" if v.model=="soft_string" else "GD-A12-stiff-string-1","approval_issued":False,"equipment_authority":"none",
          "scope":"Quasi-static soft string, constant internal/external fluid density, Coulomb friction; tension positive; upward axial speed positive.",
          "operation":v.operation}
    if v.evidence_state=="unknown":return {**base,"status":"withheld","reasons":["String/friction evidence unknown."],"profile":[]}
    if v.model=="stiff_string":
        nominal=stiff_drag_case(v,geometry,path,v.step_m);fine=stiff_drag_case(v,geometry,path,v.step_m/2)
        cases=[stiff_drag_case(v,geometry,path,v.step_m/2,d) for d in sorted(set([-v.friction_delta,v.friction_delta]))]
    else:
        nominal=drag_case(v,path,v.step_m);fine=drag_case(v,path,v.step_m/2)
        cases=[drag_case(v,path,v.step_m/2,d) for d in sorted(set([-v.friction_delta,v.friction_delta]))]
    hookrange=[min(c["hookload_n"] for c in cases),max(c["hookload_n"] for c in cases)]
    torquerange=[min(c["surface_torque_nm"] for c in cases),max(c["surface_torque_nm"] for c in cases)]
    reasons=[]
    if fine["minimum_tension_n"]<0:reasons.append("Compression encountered: soft-string equilibrium retained; buckling/contact stiffness is unqualified.")
    if v.surface_tension_limit_n is None or v.surface_torque_limit_nm is None:reasons.append("Supplied surface tension/torque limits incomplete.")
    tension_margin=None if v.surface_tension_limit_n is None else v.surface_tension_limit_n-hookrange[1]
    torque_margin=None if v.surface_torque_limit_nm is None else v.surface_torque_limit_nm-max(abs(x) for x in torquerange)
    if tension_margin is not None and tension_margin<0:reasons.append("Tested surface tension exceeds its supplied limit.")
    if torque_margin is not None and torque_margin<0:reasons.append("Tested surface torque exceeds its supplied limit.")
    calibration_info = None
    cal_performed = False
    if v.calibration_points:
        train_pts = [p for p in v.calibration_points if p.split == "train"]
        holdout_pts = [p for p in v.calibration_points if p.split == "holdout"]
        if len(train_pts) < 2:
            reasons.append("Friction calibration withheld: at least 2 training observations required.")
            calibration_info = {"status": "withheld", "reason": "Insufficient training observations", "calibrated_friction_delta": None}
        else:
            def eval_case(d_mu):
                return stiff_drag_case(v, geometry, path, v.step_m, d_mu) if v.model == "stiff_string" else drag_case(v, path, v.step_m, d_mu)
            
            best_dmu = 0.0
            best_loss = 1e30
            for step_idx in range(-20, 21):
                test_dmu = step_idx * 0.01
                if any(s.friction_coefficient + test_dmu < 0.01 or s.friction_coefficient + test_dmu > 0.99 for s in v.string_sections):
                    continue
                try:
                    c = eval_case(test_dmu)
                    loss = 0.0
                    for pt in train_pts:
                        if pt.measured_hookload_n is not None:
                            loss += ((c["hookload_n"] - pt.measured_hookload_n) / max(1.0, pt.measured_hookload_n)) ** 2
                        if pt.measured_torque_nm is not None and pt.measured_torque_nm > 0:
                            loss += ((c["surface_torque_nm"] - pt.measured_torque_nm) / max(1.0, pt.measured_torque_nm)) ** 2
                    if loss < best_loss:
                        best_loss = loss
                        best_dmu = test_dmu
                except (ValueError, ArithmeticError):  # nosec B112 - ignore invalid grid point evaluations
                    continue

            cal_performed = True
            opt_case = eval_case(best_dmu)
            if holdout_pts:
                h_errs = [abs(opt_case["hookload_n"] - pt.measured_hookload_n) for pt in holdout_pts if pt.measured_hookload_n is not None]
                h_rmse = math.sqrt(sum(e**2 for e in h_errs) / len(h_errs)) if h_errs else 0.0
                h_mae = sum(h_errs) / len(h_errs) if h_errs else 0.0
                calibration_info = {
                    "status": "calibrated_with_holdout",
                    "calibrated_friction_delta": round(best_dmu, 4),
                    "training_points_count": len(train_pts),
                    "holdout_points_count": len(holdout_pts),
                    "holdout_rmse_n": round(h_rmse, 2),
                    "holdout_mae_n": round(h_mae, 2),
                }
            else:
                calibration_info = {
                    "status": "calibrated_unvalidated",
                    "calibrated_friction_delta": round(best_dmu, 4),
                    "training_points_count": len(train_pts),
                    "holdout_points_count": 0,
                    "holdout_evaluation": "Holdout validation set not supplied; blind validation is pending.",
                }

    return {**base,**fine,"status":"research_scenario","reasons":reasons,
            "friction_sensitivity_hookload_n":hookrange,"friction_sensitivity_torque_nm":torquerange,
            "step_refinement_hookload_change_n":abs(fine["hookload_n"]-nominal["hookload_n"]),
            "step_refinement_torque_change_nm":abs(fine["surface_torque_nm"]-nominal["surface_torque_nm"]),
            "surface_tension_margin_n":None if v.surface_tension_limit_n is None else v.surface_tension_limit_n-hookrange[1],
            "surface_torque_margin_nm":None if v.surface_torque_limit_nm is None else v.surface_torque_limit_nm-max(abs(x) for x in torquerange),
            "hookload_residual_n":None if v.observed_hookload_n is None else v.observed_hookload_n-fine["hookload_n"],
            "torque_residual_nm":None if v.observed_torque_nm is None else v.observed_torque_nm-fine["surface_torque_nm"],
            "calibration_performed":cal_performed,
            "calibration":calibration_info,
            "limitations":["No bending stiffness, buckling, dynamic inertia or hydraulic end-force solution.",
            "Observed residuals do not establish a calibrated friction model without separate holdout validation."]}
