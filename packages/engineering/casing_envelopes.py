"""API TR 5C3 / ISO 10400 Casing Integrity & Load Envelopes (GD-A13).

Provides:
- Standard API TR 5C3 / ISO 10400 collapse equations across all four regimes:
  1. Yield strength collapse (thick-walled, D/t <= dt_yp)
  2. Plastic collapse (empirical regression, dt_yp < D/t <= dt_pt)
  3. Transition collapse (bridge curve fit, dt_pt < D/t <= dt_te)
  4. Elastic collapse (Euler/Stewart instability, D/t > dt_te)
- Biaxial stress corrections (axial tension reduction of collapse rating).
- API Barlow and Lamé thick-wall burst pressure equations.
- Pipe body yield and connection tensile capacity.
- Triaxial von Mises yield envelope including survey trajectory dogleg bending stress.
- 4 Operational load line profiles across well depth:
  1. Burst Kick (gas kick to surface with pore/mud external backup)
  2. Evacuation Collapse (lost circulation with fluid level drop)
  3. Thermal Expansion (annular pressure buildup and thermal stress)
  4. Running / Overpull (buoyed hanging weight plus dynamic overpull margin)
- Casing integrity evidence binding: mill test certificates, pressure test records,
  wear allowance inspection, and explicit qualification withholding.
"""
import math
from typing import Literal, Any
from pydantic import Field, model_validator
from .models import Contract
from .geometry import GeometryInput, Path
from .research_common import StudyInput
from .stability import tangent

PSI_TO_PA = 6894.757
G = 9.80665
E_STEEL = 206e9  # Young's modulus for OCTG steel in Pa
NU_STEEL = 0.3   # Poisson's ratio
ALPHA_STEEL = 1.2e-5  # Thermal expansion coefficient in 1/deg C
RHO_STEEL = 7850.0  # kg/m3


class CasingIntegrityEvidence(Contract):
    casing_name: str = Field(min_length=1, max_length=80)
    mill_certificate_id: str = Field(min_length=1, max_length=100)
    inspection_standard: str = Field(default="API Spec 5CT 10th Ed", min_length=2, max_length=100)
    inspection_date: str = Field(min_length=4, max_length=40)
    inspection_expiry: str = Field(min_length=4, max_length=40)
    inspected_minimum_wall_m: float = Field(gt=0, le=0.5)
    inspected_yield_strength_pa: float = Field(gt=1e6, le=2e9)
    pressure_test_pressure_pa: float | None = Field(default=None, ge=0, le=2e9)
    pressure_test_date: str | None = Field(default=None, max_length=40)
    pressure_test_passed: bool | None = Field(default=None)
    masp_pa: float | None = Field(default=None, ge=0, le=2e9)


class CasingEnvelopesInput(StudyInput):
    casing_name: str = Field(min_length=1, max_length=80)
    gas_gradient_pa_m: float = Field(default=2260.0, ge=100.0, le=20000.0)
    evacuation_depth_tvd_m: float | None = Field(default=None, ge=0, le=30000.0)
    drilling_mud_density_kg_m3: float = Field(default=1200.0, ge=800.0, le=3000.0)
    external_fluid_density_kg_m3: float = Field(default=1050.0, ge=800.0, le=3000.0)
    overpull_force_n: float = Field(default=222400.0, ge=0.0, le=1e8)
    kick_margin_pa: float = Field(default=0.0, ge=0.0, le=1e8)
    running_friction_factor: float = Field(default=0.0, ge=0.0, le=1.0)
    assessment_date: str | None = Field(default=None, min_length=10, max_length=40)
    temperature_change_surface_c: float = Field(default=30.0, ge=-50.0, le=300.0)
    temperature_change_shoe_c: float = Field(default=60.0, ge=-50.0, le=300.0)
    thermal_apb_rate_pa_c: float = Field(default=700000.0, ge=0.0, le=5e6)
    burst_factor: float = Field(default=1.1, ge=1.0, le=5.0)
    collapse_factor: float = Field(default=1.0, ge=1.0, le=5.0)
    axial_factor: float = Field(default=1.3, ge=1.0, le=5.0)
    triaxial_factor: float = Field(default=1.25, ge=1.0, le=5.0)
    integrity_evidence: CasingIntegrityEvidence | None = None
    station_count: int = Field(default=25, ge=5, le=200)


def calculate_api_collapse_psi(y_psi: float, dt: float) -> dict[str, Any]:
    """Calculate API TR 5C3 / ISO 10400 collapse pressure in psi given yield strength in psi and D/t ratio."""
    if y_psi <= 0 or dt <= 1.0:
        return {"pressure_psi": 0.0, "regime": "yielded_tension", "dt": dt,
                "dt_yp": 0.0, "dt_pt": 0.0, "dt_te": 0.0,
                "A": 0.0, "B": 0.0, "C": 0.0, "F": 0.0, "G": 0.0}

    # API 5C3 Empirical formulas for coefficients
    A = 2.8762 + 0.10679e-5 * y_psi + 0.21301e-10 * (y_psi**2) - 0.53132e-16 * (y_psi**3)
    B = 0.026233 + 0.50609e-6 * y_psi
    C = -465.93 + 0.030867 * y_psi - 0.10483e-7 * (y_psi**2) + 0.36989e-13 * (y_psi**3)

    ba = B / A
    term1 = (3.0 * ba) / (2.0 + ba)
    denom = (term1 - ba) * ((1.0 - term1)**2)
    if denom > 1e-12:
        F = (46.95e6 * (term1**3)) / (y_psi * denom)
    else:
        F = 2.0
    G = F * ba

    # D/t boundaries
    denom_yp = 2.0 * (B + C / y_psi)
    term_yp = (A - 2.0)**2 + 8.0 * (B + C / y_psi)
    dt_yp = (math.sqrt(max(0.0, term_yp)) + (A - 2.0)) / denom_yp if denom_yp > 0 else 14.0

    denom_pt = C + y_psi * (B - G)
    dt_pt = (y_psi * (A - F)) / denom_pt if denom_pt > 0 else 25.0

    dt_te = (2.0 + ba) / (3.0 * ba) if ba > 0 else 35.0

    # Regime selection
    if dt <= dt_yp:
        regime = "yield_collapse"
        p_collapse = 2.0 * y_psi * ((dt - 1.0) / (dt**2))
    elif dt <= dt_pt:
        regime = "plastic_collapse"
        p_collapse = y_psi * (A / dt - B) - C
    elif dt <= dt_te:
        regime = "transition_collapse"
        p_collapse = y_psi * (F / dt - G)
    else:
        regime = "elastic_collapse"
        p_collapse = 46.95e6 / (dt * ((dt - 1.0)**2))

    return {
        "pressure_psi": max(0.0, p_collapse),
        "regime": regime,
        "dt": dt,
        "dt_yp": dt_yp,
        "dt_pt": dt_pt,
        "dt_te": dt_te,
        "A": A,
        "B": B,
        "C": C,
        "F": F,
        "G": G,
    }


def api_collapse_rating(od_m: float, wall_m: float, yield_strength_pa: float,
                        axial_stress_pa: float = 0.0) -> dict[str, Any]:
    """Calculate API TR 5C3 collapse rating in Pa, including biaxial reduction from axial stress."""
    dt = od_m / wall_m if wall_m > 0 else 1e6
    y_psi = yield_strength_pa / PSI_TO_PA

    # Biaxial reduction factor (API 5C3 / ISO 10400 Section 8)
    if axial_stress_pa != 0.0 and yield_strength_pa > 0:
        sa_psi = axial_stress_pa / PSI_TO_PA
        stress_ratio = sa_psi / y_psi
        if stress_ratio > 0:  # Tension
            if stress_ratio >= 1.0:
                reduction = 0.0
            else:
                reduction = math.sqrt(max(0.0, 1.0 - 0.75 * (stress_ratio**2))) - 0.5 * stress_ratio
        else:  # Compression
            comp_ratio = abs(stress_ratio)
            reduction = min(1.0, math.sqrt(max(0.0, 1.0 - 0.75 * (comp_ratio**2))) + 0.5 * comp_ratio)
        effective_y_psi = y_psi * max(0.0, reduction)
    else:
        reduction = 1.0
        effective_y_psi = y_psi

    calc = calculate_api_collapse_psi(effective_y_psi, dt)
    return {
        "collapse_pressure_pa": calc["pressure_psi"] * PSI_TO_PA,
        "collapse_regime": calc["regime"],
        "dt_ratio": dt,
        "dt_limits": {"dt_yp": calc["dt_yp"], "dt_pt": calc["dt_pt"], "dt_te": calc["dt_te"]},
        "biaxial_reduction_factor": reduction,
        "effective_yield_pa": effective_y_psi * PSI_TO_PA,
        "coefficients": {"A": calc["A"], "B": calc["B"], "C": calc["C"], "F": calc["F"], "G": calc["G"]}
    }


def api_burst_rating(od_m: float, wall_m: float, yield_strength_pa: float,
                     wall_factor: float = 0.875) -> dict[str, Any]:
    """Calculate API Barlow burst rating with 0.875 manufacturing tolerance and Lamé elastic limit."""
    id_m = od_m - 2.0 * wall_m
    if id_m <= 0 or od_m <= 0:
        return {"burst_barlow_api_pa": 0.0, "burst_barlow_nominal_pa": 0.0, "burst_lame_pa": 0.0}

    # API Barlow with 0.875 wall tolerance (ISO 10400 / API TR 5C3)
    barlow_api = wall_factor * (2.0 * yield_strength_pa * wall_m) / od_m
    barlow_nominal = (2.0 * yield_strength_pa * wall_m) / od_m

    # Lamé thick-wall elastic yield at inner surface under zero axial stress
    ro, ri = od_m / 2.0, id_m / 2.0
    lame_yield = yield_strength_pa * (ro**2 - ri**2) / math.sqrt(3.0 * ro**4 + ri**4)

    return {
        "burst_barlow_api_pa": barlow_api,
        "burst_barlow_nominal_pa": barlow_nominal,
        "burst_lame_pa": lame_yield
    }


def casing_envelopes(data: CasingEnvelopesInput, geometry: GeometryInput, path: Path) -> dict[str, Any]:
    """Execute comprehensive API 5C3 / ISO 10400 casing load envelope and operational load lines."""
    casings = {c.name: c for c in geometry.casings}
    if data.casing_name not in casings:
        raise ValueError(f"Casing string '{data.casing_name}' not found in the referenced geometry revision.")

    c = casings[data.casing_name]
    top_md = c.top_md_m
    bottom_md = c.bottom_md_m
    od = c.outside_diameter_m
    nominal_wall = c.minimum_wall_m
    eff_wall = nominal_wall - c.wall_loss_allowance_m
    id_m = od - 2.0 * eff_wall
    area = math.pi * ((od / 2.0)**2 - (id_m / 2.0)**2)
    yp = c.yield_strength_pa

    reasons: list[str] = []
    warnings: list[str] = []

    # Evidence Integrity Verification
    integrity_status = "qualified"
    if data.integrity_evidence:
        ev = data.integrity_evidence
        if ev.casing_name != data.casing_name:
            reasons.append("Integrity evidence casing name does not match the evaluated casing.")
            integrity_status = "withheld"
        if ev.inspected_minimum_wall_m < eff_wall:
            reasons.append(f"Inspected wall ({ev.inspected_minimum_wall_m*1000:.2f} mm) is below qualified wall ({eff_wall*1000:.2f} mm).")
            integrity_status = "withheld"
        if ev.inspected_yield_strength_pa < yp:
            reasons.append(f"Inspected yield strength ({ev.inspected_yield_strength_pa/1e6:.1f} MPa) is below declared minimum ({yp/1e6:.1f} MPa).")
            integrity_status = "withheld"
        if ev.pressure_test_passed is False:
            reasons.append("Casing pressure test recorded a failure or unsealed leak-off.")
            integrity_status = "withheld"
        if data.assessment_date is None:
            warnings.append("No assessment date supplied; inspection expiry was not evaluated.")
        else:
            from datetime import datetime
            try:
                exp = datetime.fromisoformat(ev.inspection_expiry.replace("Z", "+00:00"))
                at = datetime.fromisoformat(data.assessment_date.replace("Z", "+00:00"))
                if exp.tzinfo is None or at.tzinfo is None:
                    exp, at = exp.replace(tzinfo=None), at.replace(tzinfo=None)
                if exp < at:
                    reasons.append(f"Inspection evidence expired on {ev.inspection_expiry} before assessment date {data.assessment_date}.")
                    integrity_status = "withheld"
            except ValueError:
                reasons.append("Inspection expiry or assessment date is not an ISO-8601 date.")
                integrity_status = "withheld"
        if ev.masp_pa is not None and ev.pressure_test_pressure_pa is not None:
            if ev.pressure_test_pressure_pa < ev.masp_pa:
                warnings.append(f"Recorded test pressure ({ev.pressure_test_pressure_pa/1e6:.1f} MPa) is less than MASP ({ev.masp_pa/1e6:.1f} MPa).")
    else:
        integrity_status = "unverified"
        warnings.append("No mill inspection certificate or physical pressure test record bound to this calculation.")

    # Base Ratings
    burst_ratings = api_burst_rating(od, eff_wall, yp)
    uniaxial_collapse = api_collapse_rating(od, eff_wall, yp, axial_stress_pa=0.0)
    body_tension = area * yp
    body_compression = area * yp
    conn_tension = c.connection_tension_n if c.connection_tension_n is not None else body_tension

    # Sampling depth stations along casing interval
    n_pts = data.station_count
    md_step = (bottom_md - top_md) / max(1, n_pts - 1)
    stations_md = [top_md + i * md_step for i in range(n_pts)]
    stations_md[-1] = bottom_md  # Ensure shoe is exact

    shoe_tvd = path.at(bottom_md)["tvd_m"]
    shoe_pore_pa = data.drilling_mud_density_kg_m3 * G * shoe_tvd
    kick_influx_margin_pa = data.kick_margin_pa  # declared input; no hidden default

    evac_tvd_limit = data.evacuation_depth_tvd_m if data.evacuation_depth_tvd_m is not None else shoe_tvd

    burst_profile: list[dict[str, Any]] = []
    collapse_profile: list[dict[str, Any]] = []
    thermal_profile: list[dict[str, Any]] = []
    running_profile: list[dict[str, Any]] = []

    # Buoyancy factor for running in hole
    beta = max(0.1, 1.0 - data.drilling_mud_density_kg_m3 / RHO_STEEL)
    unit_weight_n_m = RHO_STEEL * area * G

    # Pre-calculate shoe-upward buoyed tension for running case
    # Running tension at depth = integral from station to shoe of beta * w * cos(inc) + overpull
    for md in stations_md:
        pt = path.at(md)
        tvd = pt["tvd_m"]
        t = tangent(path, md)
        cos_inc = max(-1.0, min(1.0, t[2]))
        sin_inc = math.sqrt(max(0.0, 1.0 - cos_inc**2))
        inc = math.acos(cos_inc)

        # Local 3D dogleg curvature in rad/m from unit tangent gradient
        step_eval = 5.0
        md_lo = max(0.0, md - step_eval)
        md_hi = min(path.depths[-1], md + step_eval)
        len_eval = max(1e-3, md_hi - md_lo)
        t_lo = tangent(path, md_lo)
        t_hi = tangent(path, md_hi)
        curv_mag = math.sqrt(sum((y - x)**2 for x, y in zip(t_lo, t_hi))) / len_eval
        sigma_bend = (E_STEEL * od * curv_mag) / 2.0

        # --- 1. Burst Kick Scenario ---
        # Internal pressure: Gas column from shoe to surface
        p_shoe_kick = shoe_pore_pa + kick_influx_margin_pa
        p_int_burst = max(0.0, p_shoe_kick - data.gas_gradient_pa_m * (shoe_tvd - tvd))
        # External backup: mud / pore pressure in annulus
        p_ext_burst = data.external_fluid_density_kg_m3 * G * tvd
        delta_p_burst = max(0.0, p_int_burst - p_ext_burst)
        rated_burst = burst_ratings["burst_barlow_api_pa"]
        burst_util = (delta_p_burst * data.burst_factor) / rated_burst if rated_burst > 0 else 0.0
        burst_margin = rated_burst / data.burst_factor - delta_p_burst

        burst_profile.append({
            "md_m": md, "tvd_m": tvd,
            "internal_gauge_pa": p_int_burst,
            "external_gauge_pa": p_ext_burst,
            "differential_burst_pa": delta_p_burst,
            "api_burst_rating_pa": rated_burst,
            "burst_margin_pa": burst_margin,
            "utilization": burst_util,
            "status": "outside_applicability" if burst_util > 1.0 else "conditional"
        })

        # --- 2. Evacuation Collapse Scenario ---
        # Internal pressure drops below fluid level
        if tvd <= evac_tvd_limit:
            p_int_evac = 0.0
        else:
            p_int_evac = data.drilling_mud_density_kg_m3 * G * (tvd - evac_tvd_limit)
        # External pressure is full drilling mud column
        p_ext_evac = data.drilling_mud_density_kg_m3 * G * tvd
        delta_p_collapse = max(0.0, p_ext_evac - p_int_evac)

        # Hanging axial tension stress for biaxial reduction
        hanging_length_remaining = max(0.0, bottom_md - md)
        f_axial_hanging = hanging_length_remaining * unit_weight_n_m * beta * math.cos(inc)
        sigma_axial_hanging = f_axial_hanging / area if area > 0 else 0.0

        # Biaxial collapse rating
        biaxial_coll = api_collapse_rating(od, eff_wall, yp, axial_stress_pa=sigma_axial_hanging)
        rated_collapse = biaxial_coll["collapse_pressure_pa"]
        collapse_util = (delta_p_collapse * data.collapse_factor) / rated_collapse if rated_collapse > 0 else 999.0
        collapse_margin = rated_collapse / data.collapse_factor - delta_p_collapse

        collapse_profile.append({
            "md_m": md, "tvd_m": tvd,
            "internal_gauge_pa": p_int_evac,
            "external_gauge_pa": p_ext_evac,
            "differential_collapse_pa": delta_p_collapse,
            "axial_stress_pa": sigma_axial_hanging,
            "biaxial_reduction_factor": biaxial_coll["biaxial_reduction_factor"],
            "rated_collapse_pa": rated_collapse,
            "collapse_margin_pa": collapse_margin,
            "utilization": collapse_util,
            "collapse_regime": biaxial_coll["collapse_regime"],
            "status": "outside_applicability" if collapse_util > 1.0 else "conditional"
        })

        # --- 3. Thermal Expansion / APB Scenario ---
        frac_tvd = tvd / shoe_tvd if shoe_tvd > 0 else 0.0
        delta_temp = data.temperature_change_surface_c + (data.temperature_change_shoe_c - data.temperature_change_surface_c) * frac_tvd
        delta_p_apb = data.thermal_apb_rate_pa_c * delta_temp
        sigma_thermal_axial = -E_STEEL * ALPHA_STEEL * delta_temp  # compressive axial thermal stress

        # Combined triaxial stresses on inner surface
        pi_therm = p_shoe_kick
        po_therm = data.external_fluid_density_kg_m3 * G * tvd + delta_p_apb
        ri, ro = id_m / 2.0, od / 2.0
        sigma_r = -pi_therm
        sigma_theta = (pi_therm * ri**2 - po_therm * ro**2) / (ro**2 - ri**2) + ((pi_therm - po_therm) * ro**2) / (ro**2 - ri**2)
        sigma_z_total = sigma_thermal_axial - sigma_bend
        vme = math.sqrt(0.5 * ((sigma_r - sigma_theta)**2 + (sigma_theta - sigma_z_total)**2 + (sigma_z_total - sigma_r)**2))
        triaxial_util = (vme * data.triaxial_factor) / yp if yp > 0 else 0.0

        thermal_profile.append({
            "md_m": md, "tvd_m": tvd,
            "delta_temperature_c": delta_temp,
            "annular_pressure_buildup_pa": delta_p_apb,
            "thermal_axial_stress_pa": sigma_thermal_axial,
            "bending_stress_pa": sigma_bend,
            "von_mises_stress_pa": vme,
            "utilization": triaxial_util,
            "status": "outside_applicability" if triaxial_util > 1.0 else "conditional"
        })

        # --- 4. Running / Overpull Axial Scenario ---
        f_drag = data.running_friction_factor * f_axial_hanging * math.sin(inc)
        f_total_axial = f_axial_hanging + f_drag + data.overpull_force_n
        rated_axial = min(body_tension, conn_tension)
        axial_util = (f_total_axial * data.axial_factor) / rated_axial if rated_axial > 0 else 0.0
        axial_margin = rated_axial / data.axial_factor - f_total_axial

        running_profile.append({
            "md_m": md, "tvd_m": tvd,
            "hanging_tension_n": f_axial_hanging,
            "running_drag_n": f_drag,
            "overpull_n": data.overpull_force_n,
            "total_axial_tension_n": f_total_axial,
            "rated_axial_n": rated_axial,
            "axial_margin_n": axial_margin,
            "utilization": axial_util,
            "status": "outside_applicability" if axial_util > 1.0 else "conditional"
        })

    # Find governing load points
    gov_burst = max(burst_profile, key=lambda x: x["utilization"])
    gov_collapse = max(collapse_profile, key=lambda x: x["utilization"])
    gov_thermal = max(thermal_profile, key=lambda x: x["utilization"])
    gov_running = max(running_profile, key=lambda x: x["utilization"])

    max_utilization = max(gov_burst["utilization"], gov_collapse["utilization"],
                          gov_thermal["utilization"], gov_running["utilization"])

    if integrity_status == "withheld":
        overall_status = "withheld"
    elif max_utilization > 1.0:
        overall_status = "outside_applicability"
    else:
        overall_status = "conditional"

    # Generate Biaxial & Triaxial envelope reference points
    biaxial_curve: list[dict[str, float]] = []
    for sa_ratio in [-0.8, -0.6, -0.4, -0.2, 0.0, 0.2, 0.4, 0.6, 0.8, 0.95]:
        sa = sa_ratio * yp
        c_res = api_collapse_rating(od, eff_wall, yp, axial_stress_pa=sa)
        biaxial_curve.append({
            "axial_stress_ratio": sa_ratio,
            "axial_stress_pa": sa,
            "collapse_pressure_pa": c_res["collapse_pressure_pa"],
            "collapse_reduction_factor": c_res["biaxial_reduction_factor"]
        })

    triaxial_vme_envelope: list[dict[str, float]] = []
    # Exact Lamé inner-surface von Mises yield boundary (uniform temperature, no bending):
    # burst branch p_i=p, p_o=0  -> sr=-p, st=p*k1 ; collapse branch p_i=0, p_o=p -> sr=0, st=-p*k2
    ri_e, ro_e = id_m / 2.0, od / 2.0
    k1 = (ro_e**2 + ri_e**2) / (ro_e**2 - ri_e**2)
    k2 = 2.0 * ro_e**2 / (ro_e**2 - ri_e**2)
    def _yield_p(sr_c, st_c, sz):
        # VME^2 = 0.5[(sr-st)^2+(st-sz)^2+(sz-sr)^2] = yp^2 with sr=sr_c*p, st=st_c*p
        a = 0.5 * ((sr_c - st_c)**2 + st_c**2 + sr_c**2)
        b = -(st_c + sr_c) * sz
        c = sz**2 - yp**2
        disc = b * b - 4 * a * c
        return None if disc < 0 else (-b + math.sqrt(disc)) / (2 * a)
    for ratio in [-0.95, -0.75, -0.5, -0.25, 0.0, 0.25, 0.5, 0.75, 0.95]:
        sz = ratio * yp
        pb = _yield_p(-1.0, k1, sz)
        pc = _yield_p(0.0, -k2, sz)
        triaxial_vme_envelope.append({
            "axial_stress_pa": sz, "axial_force_n": sz * area,
            "internal_yield_pressure_pa": pb, "external_yield_pressure_pa": pc,
        })

    return {
        "model": "api-5c3-casing-envelopes",
        "model_version": "GD-A13-casing-envelopes-1",
        "casing_name": data.casing_name,
        "status": overall_status,
        "design_approval": False,
        "equipment_control": False,
        "casing_spec": {
            "outside_diameter_m": od,
            "nominal_wall_m": nominal_wall,
            "wall_loss_allowance_m": c.wall_loss_allowance_m,
            "effective_wall_m": eff_wall,
            "inside_diameter_m": id_m,
            "yield_strength_pa": yp,
            "grade": c.grade,
            "top_md_m": top_md,
            "bottom_md_m": bottom_md,
        },
        "api_ratings": {
            "burst_barlow_api_pa": burst_ratings["burst_barlow_api_pa"],
            "burst_barlow_nominal_pa": burst_ratings["burst_barlow_nominal_pa"],
            "burst_lame_pa": burst_ratings["burst_lame_pa"],
            "collapse_uniaxial_pa": uniaxial_collapse["collapse_pressure_pa"],
            "collapse_regime": uniaxial_collapse["collapse_regime"],
            "collapse_dt_ratio": uniaxial_collapse["dt_ratio"],
            "collapse_dt_limits": uniaxial_collapse["dt_limits"],
            "body_yield_tension_n": body_tension,
            "body_yield_compression_n": body_compression,
            "connection_tension_n": conn_tension,
        },
        "governing_summary": {
            "maximum_utilization": round(max_utilization, 4),
            "governing_burst": {"md_m": gov_burst["md_m"], "utilization": round(gov_burst["utilization"], 4), "margin_pa": round(gov_burst["burst_margin_pa"], 1)},
            "governing_collapse": {"md_m": gov_collapse["md_m"], "utilization": round(gov_collapse["utilization"], 4), "margin_pa": round(gov_collapse["collapse_margin_pa"], 1)},
            "governing_thermal": {"md_m": gov_thermal["md_m"], "utilization": round(gov_thermal["utilization"], 4)},
            "governing_running": {"md_m": gov_running["md_m"], "utilization": round(gov_running["utilization"], 4), "margin_n": round(gov_running["axial_margin_n"], 1)},
        },
        "load_profiles": {
            "burst_kick": burst_profile,
            "evacuation_collapse": collapse_profile,
            "thermal_expansion": thermal_profile,
            "running_overpull": running_profile,
        },
        "envelope_curves": {
            "biaxial_collapse_reduction": biaxial_curve,
            "triaxial_vme_boundary": triaxial_vme_envelope,
        },
        "integrity_verification": {
            "status": integrity_status,
            "reasons": reasons,
            "warnings": warnings,
        },
        "basis": {
            "standards": "API TR 5C3 (Technical Report) / ISO 10400:2007 Petroleum and natural gas industries - Equations and calculations for casing, tubing, and line pipe",
            "pressure_reference": "Gauge relative to atmosphere; tension positive",
            "disclaimer": "Analytical and empirical screening calculations. Does not constitute certification, barrier approval, or automatic rig authorization."
        }
    }
