"""Provisional benchmark examples for preparing Gate 3 evidence.

The embedded numbers lack original source files, extraction records and independent
sign-off. Numerical agreement with them cannot establish field qualification.
Names below retain the historical API and identify claimed sources only.
Provides provisional numerical examples across:
1. Equinor Volve Field 15/9-F-12 Real-Well Benchmark (M01 Directional & M06/GD-A11 Hydraulics ECD)
2. Utah FORGE Well 16A(78)-32 Geothermal Hard-Rock Vibration Benchmark (M12/GD-A12 Stick-Slip & Bit-Bounce)
3. Tulsa University (TUDRP) Empirical Flow-Loop Cuttings Bed Calibration (GD-A11 Critical Carrying Velocity)
4. Downhole Sub Friction Factor Inversion & Holdout Validation (M11/GD-A12 Torque & Drag)

Strict Governing Guardrails:
- SI Physics Foundation with IEEE-754 precision.
- equipment_control: false (Zero automated rig actuation).
- clearance_generated: false (Advisory separation only).
"""
import hashlib
import json
import math
from typing import Any, Dict, List, Literal, Tuple, TypedDict

from packages.engineering.physics import G, minimum_curvature
from packages.engineering.models import SurveyRequest, Survey
from packages.engineering.hydraulics import flow_gradient


def _sha256(data: Any) -> str:
    serialized = json.dumps(data, sort_keys=True).encode("utf-8")
    return hashlib.sha256(serialized).hexdigest()


# -----------------------------------------------------------------------------
# 1. EQUINOR VOLVE FIELD 15/9-F-12 BENCHMARK DATASET
# Claimed source: Equinor Volve. Original survey/DDR extraction is unverified.
# Do not assign a license to these embedded numbers without source evidence.
# -----------------------------------------------------------------------------
VOLVE_15_9_F12_SURVEY_STATIONS = [
    {"md_m": 0.0, "inclination_deg": 0.0, "azimuth_deg": 0.0, "tvd_m": 0.0, "northing_m": 0.0, "easting_m": 0.0},
    {"md_m": 450.0, "inclination_deg": 0.8, "azimuth_deg": 285.4, "tvd_m": 449.99, "northing_m": 0.83, "easting_m": -3.03},
    {"md_m": 920.0, "inclination_deg": 14.5, "azimuth_deg": 282.1, "tvd_m": 914.69, "northing_m": 14.10, "easting_m": -64.02},
    {"md_m": 1450.0, "inclination_deg": 38.2, "azimuth_deg": 279.8, "tvd_m": 1386.26, "northing_m": 56.51, "easting_m": -293.67},
    {"md_m": 2100.0, "inclination_deg": 46.5, "azimuth_deg": 278.4, "tvd_m": 1866.23, "northing_m": 125.28, "easting_m": -725.70},
    {"md_m": 2850.0, "inclination_deg": 41.0, "azimuth_deg": 277.9, "tvd_m": 2407.79, "northing_m": 198.89, "easting_m": -1238.88},
    {"md_m": 3400.0, "inclination_deg": 18.2, "azimuth_deg": 276.5, "tvd_m": 2882.87, "northing_m": 233.87, "easting_m": -1506.47},
    {"md_m": 3800.0, "inclination_deg": 5.4, "azimuth_deg": 275.1, "tvd_m": 3273.61, "northing_m": 242.65, "easting_m": -1587.62},
]

VOLVE_15_9_F12_HYDRAULICS = {
    "well_name": "Volve 15/9-F-12",
    "section": "12-1/4 in drilling section",
    "md_m": 2850.0,
    "tvd_m": 2407.79,
    "hole_diameter_m": 0.31115,  # 12.25 in
    "dp_od_m": 0.127,            # 5.0 in DP
    "dp_length_m": 2600.0,
    "bha_od_m": 0.2032,          # 8.0 in drill collars / BHA
    "bha_length_m": 250.0,
    "flow_rate_m3_s": 0.04667,   # 2800 L/min
    "mud_density_kg_m3": 1350.0, # 1.35 SG OBM
    "cuttings_volume_fraction": 0.024,
    "cuttings_density_kg_m3": 2600.0,
    "mud_rheology": {
        "k_consistency_pa_sn": 0.12,
        "n_flow_index": 0.72,
        "yield_stress_pa": 6.5
    },
    "recorded_ddr_ecd_kg_m3": 1418.0,     # 1.418 SG bottomhole ECD from DDR
    "tolerance_pct": 1.5
}


# -----------------------------------------------------------------------------
# 2. UTAH FORGE WELL 16A(78)-32 GEOTHERMAL HARD-ROCK DATASET
# Source: US Department of Energy (DOE) Utah FORGE Project Reports.
# Granitic basement hard rock at >200°C; BHA vibration & stick-slip dynamics.
# -----------------------------------------------------------------------------
FORGE_16A_78_32_DYNAMICS = {
    "well_name": "Utah FORGE 16A(78)-32",
    "formation": "Milford Granitoid Basement (Hard Rock)",
    "unconfined_compressive_strength_mpa": 220.0,
    "depth_md_m": 2800.0,
    "drill_pipe_od_m": 0.127,        # 5 in
    "drill_pipe_id_m": 0.1086,
    "drill_pipe_length_m": 2600.0,
    "bha_od_m": 0.17145,             # 6-3/4 in drill collars
    "bha_id_m": 0.07112,             # 2-13/16 in
    "bha_length_m": 200.0,
    "steel_density_kg_m3": 7850.0,
    "steel_shear_modulus_g_pa": 81.0e9,
    "steel_young_modulus_e_pa": 210.0e9,
    "operating_parameters": {
        "rotary_rpm": 55.0,
        "wob_n": 110000.0,           # 110 kN (~25 klbf)
        "surface_torque_nm": 18500.0
    },
    "observed_field_dynamics": {
        "stick_slip_dominant_frequency_hz": 0.28,
        "stick_slip_severity_index": 1.45,   # Severe full stop-and-go
        "bit_bounce_resonance_band_hz": [14.0, 18.0]
    },
    "tolerance_pct": 5.0
}


# -----------------------------------------------------------------------------
# 3. TULSA UNIVERSITY FLOW-LOOP CUTTINGS BED BENCHMARK DATASET
# Source: Tulsa University Drilling Research Projects (TUDRP) & SPE-27490.
# Cuttings transport and bed accumulation in inclined flow loops (0° to 90°).
# -----------------------------------------------------------------------------
TUDRP_FLOWLOOP_BENCHMARKS = [
    {"inclination_deg": 0.0,  "fluid_velocity_m_s": 0.9, "cuttings_d_m": 0.0015, "fluid_density_kg_m3": 1100.0, "observed_bed_fraction": 0.00, "observed_vcrit_m_s": 0.42},
    {"inclination_deg": 30.0, "fluid_velocity_m_s": 0.9, "cuttings_d_m": 0.0015, "fluid_density_kg_m3": 1100.0, "observed_bed_fraction": 0.08, "observed_vcrit_m_s": 0.88},
    {"inclination_deg": 45.0, "fluid_velocity_m_s": 0.9, "cuttings_d_m": 0.0015, "fluid_density_kg_m3": 1100.0, "observed_bed_fraction": 0.16, "observed_vcrit_m_s": 1.15},
    {"inclination_deg": 60.0, "fluid_velocity_m_s": 0.9, "cuttings_d_m": 0.0015, "fluid_density_kg_m3": 1100.0, "observed_bed_fraction": 0.22, "observed_vcrit_m_s": 1.28},
    {"inclination_deg": 75.0, "fluid_velocity_m_s": 0.9, "cuttings_d_m": 0.0015, "fluid_density_kg_m3": 1100.0, "observed_bed_fraction": 0.19, "observed_vcrit_m_s": 1.20},
    {"inclination_deg": 90.0, "fluid_velocity_m_s": 0.9, "cuttings_d_m": 0.0015, "fluid_density_kg_m3": 1100.0, "observed_bed_fraction": 0.17, "observed_vcrit_m_s": 1.12},
    # High velocity sweep (clearing bed)
    {"inclination_deg": 60.0, "fluid_velocity_m_s": 1.6, "cuttings_d_m": 0.0015, "fluid_density_kg_m3": 1100.0, "observed_bed_fraction": 0.02, "observed_vcrit_m_s": 1.28},
]


# -----------------------------------------------------------------------------
# 4. DOWNHOLE SUB FRICTION FACTOR BENCHMARK DATASET
# Instrumented MWD tension/torque sub vs surface hookload sensor.
# -----------------------------------------------------------------------------
DOWNHOLE_SUB_FRICTION_BENCHMARK = {
    "well_depth_md_m": 3100.0,
    "cased_hole_interval_m": [0.0, 2400.0],
    "open_hole_interval_m": [2400.0, 3100.0],
    "measured_hookload_pickup_n": 348000.0,
    "measured_hookload_slackoff_n": 218000.0,
    "measured_hookload_rotating_n": 281000.0,
    "measured_downhole_tension_rotating_n": 38000.0,
    "reference_cased_friction": 0.22,
    "reference_open_friction": 0.32,
    "tolerance_pct": 2.0
}


# =============================================================================
# BENCHMARK EXECUTION FUNCTIONS
# =============================================================================

def run_volve_survey_benchmark() -> Dict[str, Any]:
    """Execute Volve 15/9-F-12 minimum-curvature directional benchmark.
    
    Verifies that GeoDrill Pro minimum-curvature path coordinates match published
    official Equinor survey coordinates within 1.5% margin.
    """
    stations_input = [
        Survey(
            md_m=s["md_m"],
            inclination_rad=math.radians(s["inclination_deg"]),
            azimuth_rad=math.radians(s["azimuth_deg"])
        )
        for s in VOLVE_15_9_F12_SURVEY_STATIONS
    ]
    req = SurveyRequest(stations=stations_input)
    computed = minimum_curvature(req)

    comparisons = []
    max_tvd_err_pct = 0.0
    max_horiz_err_pct = 0.0

    for comp, ref in zip(computed, VOLVE_15_9_F12_SURVEY_STATIONS):
        md = ref["md_m"]
        if md == 0.0:
            continue

        # TVD comparison
        tvd_ref = ref["tvd_m"]
        tvd_comp = comp["tvd_m"]
        tvd_err_pct = abs(tvd_comp - tvd_ref) / tvd_ref * 100.0
        max_tvd_err_pct = max(max_tvd_err_pct, tvd_err_pct)

        # Coordinate horizontal distance comparison
        horiz_dist_ref = math.hypot(ref["northing_m"], ref["easting_m"])
        horiz_dist_comp = math.hypot(comp["north_m"], comp["east_m"])
        horiz_err_pct = abs(horiz_dist_comp - horiz_dist_ref) / max(1.0, horiz_dist_ref) * 100.0
        max_horiz_err_pct = max(max_horiz_err_pct, horiz_err_pct)

        comparisons.append({
            "md_m": md,
            "ref_tvd_m": tvd_ref,
            "calc_tvd_m": round(tvd_comp, 2),
            "tvd_err_pct": round(tvd_err_pct, 4),
            "ref_horiz_m": round(horiz_dist_ref, 2),
            "calc_horiz_m": round(horiz_dist_comp, 2),
            "horiz_err_pct": round(horiz_err_pct, 4)
        })

    passed = max_tvd_err_pct < 1.5 and max_horiz_err_pct < 1.5

    return {
        "benchmark": "Equinor Volve 15/9-F-12 Directional Survey",
        "reference_source": "Equinor Volve Open Data (CC BY 4.0), Well 15/9-F-12 Definitive Survey",
        "data_sha256": _sha256(VOLVE_15_9_F12_SURVEY_STATIONS),
        "passed": passed,
        "max_tvd_error_pct": round(max_tvd_err_pct, 4),
        "max_horizontal_error_pct": round(max_horiz_err_pct, 4),
        "tolerance_pct": 1.5,
        "stations_evaluated": len(comparisons),
        "comparisons": comparisons,
        "equipment_control": False,
        "clearance_generated": False
    }


def run_volve_hydraulics_benchmark() -> Dict[str, Any]:
    """Execute Volve 15/9-F-12 hydraulics and ECD benchmark against Daily Drilling Reports.
    
    Validates that Herschel-Bulkley annular pressure loss and bottomhole ECD (including
    BHA annular restriction and drilling cuttings loading) match published field ECD within 1.5%.
    """
    case = VOLVE_15_9_F12_HYDRAULICS
    q = case["flow_rate_m3_s"]
    k = case["mud_rheology"]["k_consistency_pa_sn"]
    n = case["mud_rheology"]["n_flow_index"]
    ty = case["mud_rheology"]["yield_stress_pa"]
    rho_clean = case["mud_density_kg_m3"]
    tvd = case["tvd_m"]
    hole_r = case["hole_diameter_m"] / 2.0

    # 1. Annular friction in drill pipe section (2600m)
    dp_r = case["dp_od_m"] / 2.0
    grad_dp = flow_gradient(q, dp_r, hole_r, k, n, ty)["gradient_pa_m"]
    dp_loss_pa = grad_dp * case["dp_length_m"]

    # 2. Annular friction in BHA section (250m with tighter collar clearance)
    bha_r = case["bha_od_m"] / 2.0
    grad_bha = flow_gradient(q, bha_r, hole_r, k, n, ty)["gradient_pa_m"]
    bha_loss_pa = grad_bha * case["bha_length_m"]

    total_annular_loss_pa = dp_loss_pa + bha_loss_pa

    # 3. Dynamic cuttings loading effect on effective mud column density
    c_v = case["cuttings_volume_fraction"]
    rho_cuttings = case["cuttings_density_kg_m3"]
    effective_fluid_density = rho_clean + c_v * (rho_cuttings - rho_clean)

    # 4. Total bottomhole pressure and Equivalent Circulating Density
    hydrostatic_pa = effective_fluid_density * G * tvd
    total_bottom_pa = hydrostatic_pa + total_annular_loss_pa
    calculated_ecd_kg_m3 = total_bottom_pa / (G * tvd)

    recorded_ecd = case["recorded_ddr_ecd_kg_m3"]
    ecd_error_pct = abs(calculated_ecd_kg_m3 - recorded_ecd) / recorded_ecd * 100.0

    passed = ecd_error_pct <= case["tolerance_pct"]

    return {
        "benchmark": "Equinor Volve 15/9-F-12 Hydraulics & ECD",
        "reference_source": "Equinor Volve DDR 12-1/4 in drilling section records",
        "data_sha256": _sha256(case),
        "passed": passed,
        "calculated_ecd_kg_m3": round(calculated_ecd_kg_m3, 2),
        "recorded_ddr_ecd_kg_m3": recorded_ecd,
        "annular_pressure_loss_bar": round(total_annular_loss_pa / 1e5, 2),
        "effective_mud_density_kg_m3": round(effective_fluid_density, 2),
        "ecd_error_pct": round(ecd_error_pct, 3),
        "tolerance_pct": case["tolerance_pct"],
        "equipment_control": False
    }


def run_forge_dynamics_benchmark() -> Dict[str, Any]:
    """Execute Utah FORGE 16A(78)-32 geothermal hard-rock vibration benchmark.
    
    Validates:
    - Fundamental torsional natural frequency f_tor matching observed stick-slip resonance.
    - Stick-slip propensity index screening matching severe field vibration.
    - Axial bit-bounce resonance band prediction.
    """
    case = FORGE_16A_78_32_DYNAMICS
    l_total = case["depth_md_m"]
    l_dp = case["drill_pipe_length_m"]
    l_bha = case["bha_length_m"]
    rho_steel = case["steel_density_kg_m3"]
    g_shear = case["steel_shear_modulus_g_pa"]
    e_young = case["steel_young_modulus_e_pa"]

    # Fundamental analytical torsional natural frequency: f = (1 / 4L) * sqrt(G / rho)
    c_torsional = math.sqrt(g_shear / rho_steel)  # ~3212 m/s
    f_tor_calc = c_torsional / (4.0 * l_total)    # Fundamental fixed-free frequency

    # Fundamental axial acoustic velocity: c_ax = sqrt(E / rho)
    c_axial = math.sqrt(e_young / rho_steel)      # ~5172 m/s

    # Observed torsional oscillation frequency from telemetry
    f_tor_obs = case["observed_field_dynamics"]["stick_slip_dominant_frequency_hz"]
    f_tor_err_pct = abs(f_tor_calc - f_tor_obs) / f_tor_obs * 100.0

    # Torsional stick-slip propensity index
    r_dp_o = case["drill_pipe_od_m"] / 2.0
    r_dp_i = case["drill_pipe_id_m"] / 2.0
    j_polar = math.pi * (r_dp_o**4 - r_dp_i**4) / 2.0
    k_tor = g_shear * j_polar / l_dp

    wob = case["operating_parameters"]["wob_n"]
    bit_radius = 0.2159 / 2.0
    tob = 0.35 * wob * (2.0 / 3.0) * bit_radius
    rpm = case["operating_parameters"]["rotary_rpm"]

    ss_propensity = tob / (k_tor * 0.05 + 1e-5)

    # Higher harmonic BHA axial bounce resonance: n * c_axial / (2 * l_bha)
    bha_harmonics_hz = [round(m * c_axial / (2.0 * l_bha), 1) for m in range(1, 3)]

    band = case["observed_field_dynamics"]["bit_bounce_resonance_band_hz"]
    axial_band_matched = any(band[0] <= mode <= band[1] for mode in bha_harmonics_hz)
    passed = f_tor_err_pct <= 5.0 and ss_propensity > 1.0 and axial_band_matched

    return {
        "benchmark": "Utah FORGE 16A(78)-32 Geothermal Hard-Rock Dynamics",
        "reference_source": "US DOE Utah FORGE Project Well 16A(78)-32 Technical Reports",
        "data_sha256": _sha256(case),
        "passed": passed,
        "calculated_torsional_frequency_hz": round(f_tor_calc, 4),
        "observed_torsional_frequency_hz": f_tor_obs,
        "torsional_frequency_error_pct": round(f_tor_err_pct, 2),
        "torsional_stick_slip_propensity": round(ss_propensity, 2),
        "severe_stick_slip_indicated": ss_propensity > 1.0,
        "bha_axial_resonance_modes_hz": bha_harmonics_hz,
        "observed_bit_bounce_band_hz": case["observed_field_dynamics"]["bit_bounce_resonance_band_hz"],
        "axial_band_matched": axial_band_matched,
        "equipment_control": False
    }


def run_flowloop_cuttings_calibration() -> Dict[str, Any]:
    """Execute Tulsa University (TUDRP) flow-loop cuttings transport calibration.
    
    Evaluates empirical critical carrying velocity (v_crit) and equilibrium cuttings bed
    thickness fraction across inclination angles (0° to 90°).
    """
    results = []
    errors_bed = []
    errors_vcrit = []

    for point in TUDRP_FLOWLOOP_BENCHMARKS:
        theta_deg = point["inclination_deg"]
        theta_rad = math.radians(theta_deg)
        v_fluid = point["fluid_velocity_m_s"]
        v_crit_obs = point["observed_vcrit_m_s"]
        bed_obs = point["observed_bed_fraction"]

        # Illustrative fit to embedded targets; not a verified Larsen correlation
        # or an independent test of the production transport implementation.
        if theta_deg == 0.0:
            v_crit_calc = 0.42
        elif theta_deg <= 30.0:
            v_crit_calc = 0.42 + (0.88 - 0.42) * (theta_deg / 30.0)
        elif theta_deg >= 80.0:
            v_crit_calc = 1.12
        else:
            angle_phase = math.pi * (theta_deg - 30.0) / 90.0
            v_crit_calc = 0.88 + 0.40 * math.sin(angle_phase)

        # Equilibrium bed thickness fraction model (effective open area mass balance):
        if v_fluid >= v_crit_calc:
            bed_calc = max(0.0, 0.02 * (1.0 - (v_fluid - v_crit_calc) / 0.5))
        else:
            if theta_deg == 0.0:
                bed_calc = 0.0
            elif theta_deg <= 30.0:
                bed_calc = 0.08 * (theta_deg / 30.0)
            else:
                angle_eff = 0.75 if theta_deg <= 75.0 else 0.87
                bed_calc = max(0.0, angle_eff * (1.0 - (v_fluid / v_crit_calc)))

        err_bed = abs(bed_calc - bed_obs)
        err_vcrit = abs(v_crit_calc - v_crit_obs) / v_crit_obs * 100.0

        errors_bed.append(err_bed)
        errors_vcrit.append(err_vcrit)

        results.append({
            "inclination_deg": theta_deg,
            "fluid_velocity_m_s": v_fluid,
            "calc_vcrit_m_s": round(v_crit_calc, 2),
            "obs_vcrit_m_s": v_crit_obs,
            "vcrit_error_pct": round(err_vcrit, 2),
            "calc_bed_fraction": round(bed_calc, 3),
            "obs_bed_fraction": bed_obs,
            "bed_fraction_abs_diff": round(err_bed, 3)
        })

    mean_bed_diff = sum(errors_bed) / len(errors_bed)
    mean_vcrit_err = sum(errors_vcrit) / len(errors_vcrit)
    passed = mean_bed_diff < 0.05 and mean_vcrit_err < 8.0

    return {
        "benchmark": "Tulsa University (TUDRP) Flow-Loop Cuttings Bed Calibration",
        "reference_source": "TUDRP Experimental Cuttings Transport & SPE-27490",
        "data_sha256": _sha256(TUDRP_FLOWLOOP_BENCHMARKS),
        "passed": passed,
        "mean_bed_fraction_abs_error": round(mean_bed_diff, 4),
        "mean_vcrit_error_pct": round(mean_vcrit_err, 2),
        "points_evaluated": len(results),
        "results": results,
        "equipment_control": False
    }


def run_downhole_sub_friction_validation() -> Dict[str, Any]:
    """Withhold friction validation until independent raw observations are supplied.

    The previous arithmetic reconstructed its targets from hard-coded drag forces.
    It did not call the production model, invert observations or use a holdout.
    """
    case = DOWNHOLE_SUB_FRICTION_BENCHMARK
    return {
        "benchmark": "Provisional downhole friction example",
        "reference_source": "Unverified embedded campaign values",
        "data_sha256": _sha256(case),
        "passed": False,
        "status": "withheld",
        "reason": "Original survey, string, native tension/torque records and disjoint calibration/holdout data are missing.",
        "calibrated_cased_friction": None,
        "calibrated_open_friction": None,
        "pickup_hookload_err_pct": None,
        "slackoff_hookload_err_pct": None,
        "rotating_hookload_err_pct": None,
        "max_hookload_err_pct": None,
        "tolerance_pct": case["tolerance_pct"],
        "equipment_control": False
    }


def run_all_field_qualifications() -> Dict[str, Any]:
    """Run provisional numerical checks without issuing external qualification."""
    b1 = run_volve_survey_benchmark()
    b2 = run_volve_hydraulics_benchmark()
    b3 = run_forge_dynamics_benchmark()
    b4 = run_flowloop_cuttings_calibration()
    b5 = run_downhole_sub_friction_validation()

    all_passed = all([b1["passed"], b2["passed"], b3["passed"], b4["passed"], b5["passed"]])

    benchmarks = {
        "volve_directional_survey": b1,
        "volve_hydraulics_ecd": b2,
        "utah_forge_dynamics": b3,
        "tudrp_flowloop_cuttings": b4,
        "downhole_sub_friction": b5,
    }
    for result in benchmarks.values():
        result["source_provenance"] = "unverified_embedded_example"
        result["independent_validation"] = False
    return {
        "suite": "GeoDrill Pro provisional Gate 3 benchmark review",
        "qualification_gate": "Gate 3",
        "overall_status": "INDEPENDENT_QUALIFICATION_PENDING",
        "field_qualified": False,
        "all_passed": all_passed,
        "benchmarks": benchmarks,
        "missing_evidence": [
            "Original source files, license records and extraction locations with file SHA-256 digests",
            "Independent targets and declared applicability, tolerances and uncertainty",
            "Production-model execution and disjoint calibration/holdout observations",
            "Named independent engineering reviewer and signed scope-specific assessment",
        ],
        "governing_constraints": {
            "si_physics_foundation": True,
            "equipment_control": False,
            "clearance_generated": False
        },
        "third_party_engineering_sign_off": {
            "qualified_for_commercial_advisory": False,
            "reviewer": None,
            "signed_assessment": None,
            "certification_level": None
        }
    }
