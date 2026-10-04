"""Three-coordinate coupled BHA scenario and native measured-channel review."""
import math
from typing import Literal
from pydantic import Field,model_validator
from .models import Contract
from .research_common import StudyInput,base,eigen_symmetric,rms

class SensorSample(Contract):
    time_s: float = Field(ge=0,le=3600)
    value: float | None = Field(default=None,ge=-1e9,le=1e9)
    quality: Literal["accepted","suspect","missing"]
    @model_validator(mode="after")
    def eligible_value(self):
        if self.quality=="accepted" and self.value is None:raise ValueError("Accepted sensor samples require a numeric measurement.")
        return self
class DynamicsSensor(Contract):
    name: str = Field(min_length=1,max_length=80)
    axis: Literal["axial_acceleration","torsional_acceleration","lateral_acceleration"]
    units: Literal["m_s2","rad_s2"]
    provenance: str = Field(min_length=3,max_length=500)
    calibration_note: str = Field(min_length=3,max_length=500)
    anti_alias_bandwidth_hz: float = Field(gt=0,le=10000)
    samples: list[SensorSample] = Field(min_length=2,max_length=2000)
    @model_validator(mode="after")
    def valid(self):
        if (self.axis=="torsional_acceleration")!=(self.units=="rad_s2"):raise ValueError("Channel units must match the physical axis.")
        if any(b.time_s<=a.time_s for a,b in zip(self.samples,self.samples[1:])):raise ValueError("Sensor times must increase.")
        return self

class DynamicsInput(StudyInput):
    top_md_m: float = Field(ge=0,le=30000)
    bottom_md_m: float = Field(gt=0,le=30000)
    outside_diameter_m: float = Field(gt=.005,le=1)
    inside_diameter_m: float = Field(ge=0,le=1)
    material_density_kg_m3: float = Field(ge=1000,le=20000)
    young_modulus_pa: float = Field(ge=1e9,le=500e9)
    poisson_ratio: float = Field(ge=0,lt=.5)
    boundary: Literal["cantilever_reduced","unknown","full_contact_bha"]
    configuration_note: str = Field(min_length=3,max_length=500)
    damping_ratio: float = Field(ge=0,le=1)
    axial_torsional_coupling: float = Field(ge=-.5,le=.5)
    axial_lateral_coupling: float = Field(ge=-.5,le=.5)
    torsional_lateral_coupling: float = Field(ge=-.5,le=.5)
    bit_axial_stiffness_n_per_m: float = Field(ge=0,le=1e9)
    lateral_clearance_m: float = Field(gt=0,le=1)
    contact_stiffness_n_per_m: float = Field(ge=0,le=1e9)
    axial_force_amplitude_n: float = Field(ge=-1e6,le=1e6)
    torque_amplitude_nm: float = Field(ge=-1e6,le=1e6)
    lateral_force_amplitude_n: float = Field(ge=-1e6,le=1e6)
    excitation_hz: float = Field(ge=0,le=1000)
    duration_s: float = Field(gt=0,le=60)
    time_step_s: float = Field(gt=1e-6,le=.1)
    refinement_relative_tolerance: float = Field(gt=0,le=.5)
    sensors: list[DynamicsSensor] = Field(default_factory=list,max_length=6)
    @model_validator(mode="after")
    def dimensions(self):
        if self.bottom_md_m<=self.top_md_m or self.inside_diameter_m>=self.outside_diameter_m:raise ValueError("BHA length/diameters must be ordered.")
        a,b,c=self.axial_torsional_coupling,self.axial_lateral_coupling,self.torsional_lateral_coupling
        if 1+2*a*b*c-a*a-b*b-c*c<=1e-6:raise ValueError("Coupled stiffness matrix must be positive definite.")
        if len({s.name for s in self.sensors})!=len(self.sensors):raise ValueError("Sensor names must be unique.")
        return self

def matrices(v):
    l=v.bottom_md_m-v.top_md_m;area=math.pi*(v.outside_diameter_m**2-v.inside_diameter_m**2)/4
    inertia=math.pi*(v.outside_diameter_m**4-v.inside_diameter_m**4)/64;polar=2*inertia
    mass=[v.material_density_kg_m3*area*l/3,v.material_density_kg_m3*polar*l/3,.236*v.material_density_kg_m3*area*l]
    diag=[v.young_modulus_pa*area/l+v.bit_axial_stiffness_n_per_m,v.young_modulus_pa/(2*(1+v.poisson_ratio))*polar/l,3*v.young_modulus_pa*inertia/l**3]
    rho=[[1,v.axial_torsional_coupling,v.axial_lateral_coupling],[v.axial_torsional_coupling,1,v.torsional_lateral_coupling],[v.axial_lateral_coupling,v.torsional_lateral_coupling,1]]
    stiffness=[[rho[i][j]*math.sqrt(diag[i]*diag[j]) for j in range(3)] for i in range(3)]
    damping=[2*v.damping_ratio*math.sqrt(m*k) for m,k in zip(mass,diag)]
    eig=eigen_symmetric([[stiffness[i][j]/math.sqrt(mass[i]*mass[j]) for j in range(3)] for i in range(3)])
    return mass,stiffness,damping,eig

def response(v,mass,k,damping,step):
    n=math.ceil(v.duration_s/step)
    if n>30000:raise ValueError("Dynamics work budget exceeded; shorten duration or use a coarser eligible step.")
    h=v.duration_s/n;state=[0.]*6;rows=[];contact_events=0;work=0.;dissipation=0.
    amplitudes=[v.axial_force_amplitude_n,v.torque_amplitude_nm,v.lateral_force_amplitude_n]
    def derivative(time,state):
        q=state[:3];vel=state[3:];force=[a*math.sin(2*math.pi*v.excitation_hz*time) for a in amplitudes]
        contact=-v.contact_stiffness_n_per_m*math.copysign(max(0.,abs(q[2])-v.lateral_clearance_m),q[2])
        acc=[(force[i]+(contact if i==2 else 0.)-damping[i]*vel[i]-sum(k[i][j]*q[j] for j in range(3)))/mass[i] for i in range(3)]
        return vel+acc,force
    previous=None
    for j in range(n+1):
        time=j*h;deriv,force=derivative(time,state);q=state[:3];vel=state[3:]
        energy=.5*sum(m*u*u for m,u in zip(mass,vel))+.5*sum(q[i]*k[i][z]*q[z] for i in range(3) for z in range(3))+.5*v.contact_stiffness_n_per_m*max(0.,abs(q[2])-v.lateral_clearance_m)**2
        power=sum(f*u for f,u in zip(force,vel));loss=sum(c*u*u for c,u in zip(damping,vel))
        if previous:
            work+=h*(power+previous[0])/2;dissipation+=h*(loss+previous[1])/2
        previous=power,loss
        rows.append({"time_s":time,"axial_displacement_m":q[0],"torsional_angle_rad":q[1],"lateral_displacement_m":q[2],"axial_acceleration_m_s2":deriv[3],"torsional_acceleration_rad_s2":deriv[4],"lateral_acceleration_m_s2":deriv[5],"energy_j":energy,"energy_balance_residual_j":energy-work+dissipation})
        if abs(q[2])>v.lateral_clearance_m:contact_events+=1
        if j==n:break
        a=deriv;b=derivative(time+h/2,[x+h*y/2 for x,y in zip(state,a)])[0]
        c=derivative(time+h/2,[x+h*y/2 for x,y in zip(state,b)])[0]
        d=derivative(time+h,[x+h*y for x,y in zip(state,c)])[0]
        state=[x+h*(aa+2*bb+2*cc+dd)/6 for x,aa,bb,cc,dd in zip(state,a,b,c,d)]
        if any(not math.isfinite(x) or abs(x)>1e6 for x in state):raise ValueError("Dynamics solution diverged.")
    return rows,contact_events

def dynamics(v,geometry,path):
    out=base("M12-coupled-reduced-2","Simulated coupled axial/torsional/lateral coordinates of a uniform cantilever segment; native supplied sensor values are separate.",["No virtual vibration diagnosis or parameter-command authority.","Reduced generalized coordinates are not a full BHA finite-element model; bit/contact coefficients require configuration evidence.","Surface telemetry cannot establish downhole high-frequency state."])
    if v.bottom_md_m>path.depths[-1]:raise ValueError("BHA exceeds accepted survey.")
    if v.evidence_state=="unknown" or v.boundary!="cantilever_reduced":return {**out,"status":"withheld","reasons":["Unknown evidence or unsupported BHA boundary/model."]}
    for i in range(len(path.stations)-1):
        a,b,_,_,beta=path.segment(i)
        if max(a.md_m,v.top_md_m)<min(b.md_m,v.bottom_md_m) and beta>1e-7:
            return {**out,"status":"withheld","reasons":["Curved BHA interval requires a different structural/contact formulation."]}
    covered=sum(max(0.,min(h.bottom_md_m,v.bottom_md_m)-max(h.top_md_m,v.top_md_m)) for h in geometry.hole_sections)
    if abs(covered-(v.bottom_md_m-v.top_md_m))>1e-6:raise ValueError("BHA interval requires complete hole geometry.")
    bores=[h.diameter_m for h in geometry.hole_sections if max(h.top_md_m,v.top_md_m)<min(h.bottom_md_m,v.bottom_md_m)]
    bores.extend(c.inside_diameter_m for c in geometry.casings if c.state=="installed" and max(c.top_md_m,v.top_md_m)<min(c.bottom_md_m,v.bottom_md_m))
    if any(d<=v.outside_diameter_m or v.lateral_clearance_m>(d-v.outside_diameter_m)/2+1e-9 for d in bores):
        raise ValueError("BHA diameter/declared contact clearance conflicts with bound hole or installed casing.")
    m,k,c,eig=matrices(v);freq=[math.sqrt(e[0])/(2*math.pi) for e in eig]
    contact_matrix=[[k[i][j]/math.sqrt(m[i]*m[j])+(v.contact_stiffness_n_per_m/m[2] if i==j==2 else 0.) for j in range(3)] for i in range(3)]
    max_hz=max(v.excitation_hz,math.sqrt(eigen_symmetric(contact_matrix)[-1][0])/(2*math.pi))
    if v.time_step_s*max_hz>1/40:raise ValueError("Dynamics time step needs at least 40 samples per highest model/excitation/contact cycle.")
    a,_=response(v,m,k,c,v.time_step_s);b,contacts=response(v,m,k,c,v.time_step_s/2)
    errors={}
    for key in ("axial_displacement_m","torsional_angle_rad","lateral_displacement_m"):
        scale=max(1e-9,max(abs(r[key]) for r in b))
        # Adaptive ceil steps can differ; compare at exact coarse times via linear interpolation.
        values=[];j=0
        for row in a:
            while j+1<len(b)-1 and b[j+1]["time_s"]<row["time_s"]:j+=1
            left,right=b[j:j+2];f=(row["time_s"]-left["time_s"])/(right["time_s"]-left["time_s"])
            values.append(abs(row[key]-(left[key]+f*(right[key]-left[key])))/scale)
        errors[key]=max(values)
    sensors=[]
    for sensor in v.sensors:
        gap=max(b.time_s-a.time_s for a,b in zip(sensor.samples,sensor.samples[1:]))
        qualified=all(s.quality=="accepted" for s in sensor.samples) and sensor.anti_alias_bandwidth_hz<.5/gap
        sensors.append({"name":sensor.name,"axis":sensor.axis,"units":sensor.units,"status":("synthetic_native_review" if v.evidence_state=="synthetic" else "supplied_native_review") if qualified else "withheld","minimum_sampling_hz":1/gap,"anti_alias_bandwidth_hz":sensor.anti_alias_bandwidth_hz,"rms":rms([s.value for s in sensor.samples]) if qualified else None,"samples":[s.model_dump() for s in sensor.samples],"bandwidth_eligible_modes":[i+1 for i,f in enumerate(freq) if qualified and f<sensor.anti_alias_bandwidth_hz],"modal_observability_established":False,"calibration_independently_verified":False,"state_estimation_performed":False})
    out.update(history=b,mode_frequencies_hz=freq,mode_vectors_mass_normalized_coordinates=[e[1] for e in eig],mode_vector_basis="Eigenvectors in mass-normalized generalized coordinates; not a measured spatial mode shape.",generalized_mass=m,generalized_stiffness=k,refinement_relative_errors=errors,contact_active_samples=contacts,sensor_review=sensors,observability="Supplied native channels reviewed; unmeasured states not inferred.",maximum_energy_balance_residual_j=max(abs(r["energy_balance_residual_j"]) for r in b))
    if max(errors.values())>v.refinement_relative_tolerance:out.update(status="incomplete_assessment",reasons=["Response time-step refinement exceeds supplied tolerance."])
    return out
