"""Qualification ledger and reference verification cases (GD-A05).

Provides applicability cards, verification boundaries, analytical/experimental/field qualification status,
and reproducible reference benchmarks across all engineering models (M01 to M17).

Distinguishes between:
- Software/numerical verification (exact analytical solutions, manufactured solutions)
- Experimental validation (flow-loops, laboratory rock tests, inspected wear tests)
- Field qualification (instrumented downhole BHA runs, verified well logs, field operational validation)
"""
from typing import Literal, TypedDict, Any
from pydantic import BaseModel, Field


class BenchmarkCase(TypedDict):
    name: str
    description: str
    reference_source: str
    analytical_or_published_target: dict[str, Any]
    numerical_tolerance: str
    validation_level: Literal["analytical", "manufactured", "experimental", "field"]


class QualificationCard(TypedDict):
    module_id: str
    title: str
    governing_physics: str
    intended_use: str
    applicability_envelope: dict[str, str]
    withholding_conditions: list[str]
    qualification_status: Literal["software_verified", "experimentally_validated", "field_qualified", "withheld", "excluded"]
    evidence_basis: str
    benchmarks: list[BenchmarkCase]


QUALIFICATION_LEDGER: dict[str, QualificationCard] = {
    "M01": {
        "module_id": "M01",
        "title": "Well Geometry & Trajectory",
        "governing_physics": "Minimum-curvature directional survey integration & formation intersection",
        "intended_use": "Deterministic 3D trajectory reconstruction from survey stations and interpreted tops",
        "applicability_envelope": {
            "depth_range": "0 to 30,000 m MD",
            "inclination": "0 to 180 degrees",
            "dogleg_severity": "0 to 30 deg/30m",
            "survey_spacing": "Monotonically increasing MD >= 0.1 m"
        },
        "withholding_conditions": [
            "Non-monotonic measured depths",
            "Tie-in offset not at MD 0",
            "Declination or grid convergence unstated without true north reference"
        ],
        "qualification_status": "software_verified",
        "evidence_basis": "Sawaryn & Thorogood (SPE-84246) exact circular arc analytical solutions",
        "benchmarks": [
            {
                "name": "Sawaryn-Thorogood Standard Arc",
                "description": "90-degree turn with constant dogleg severity",
                "reference_source": "SPE 84246 Benchmark Case 1",
                "analytical_or_published_target": {"ratio_factor": 1.0, "closure_distance_err_m": 0.0},
                "numerical_tolerance": "1e-6 relative",
                "validation_level": "analytical"
            }
        ]
    },
    "M02": {
        "module_id": "M02",
        "title": "Casing & Liner Program",
        "governing_physics": "Lamé thick-wall elastic stress and von Mises yield under differential pressure",
        "intended_use": "Screening nominal tubular body yield and connection ratings with wear allowance",
        "applicability_envelope": {
            "tubular_geometry": "Concentric cylindrical pipes",
            "material_model": "Linear isotropic elastic yield",
            "loss_allowance": "Uniform wall thickness reduction <= 50%"
        },
        "withholding_conditions": [
            "Non-uniform local wear grooves",
            "Plastic post-yield burst deformation",
            "Thermal per-degree casing derating without certified mill tests"
        ],
        "qualification_status": "software_verified",
        "evidence_basis": "API TR 5C3 / ISO 10400 comprehensive collapse, burst, and biaxial load equations",
        "benchmarks": [
            {
                "name": "API 5C3 Lamé Elastic Yield",
                "description": "Thick-walled 9-5/8 inch casing under 50 MPa differential burst",
                "reference_source": "ISO 10400 Section 6.2",
                "analytical_or_published_target": {"hoop_stress_pa": 412.5e6},
                "numerical_tolerance": "1e-5 relative",
                "validation_level": "analytical"
            },
            {
                "name": "API 5C3 K-55 Plastic Collapse",
                "description": "K-55 casing (55,000 psi yield) at D/t = 18.0 plastic collapse regime",
                "reference_source": "API Bulletin 5C3 Table 1 / ISO 10400 Section 7.2",
                "analytical_or_published_target": {"collapse_pressure_psi": 4957.8, "regime": "plastic_collapse"},
                "numerical_tolerance": "1e-4 relative",
                "validation_level": "analytical"
            },
            {
                "name": "API 5C3 Barlow Burst with Mill Tolerance",
                "description": "N-80 casing (80,000 psi yield, OD 9.625 in, wall 0.472 in) under 0.875 Barlow rating",
                "reference_source": "API TR 5C3 Section 6.1 / ISO 10400",
                "analytical_or_published_target": {"burst_pressure_psi": 6868.0},
                "numerical_tolerance": "1e-4 relative",
                "validation_level": "analytical"
            },
            {
                "name": "ISO 10400 Biaxial Collapse Reduction",
                "description": "Biaxial yield reduction factor under axial tension ratio Sa/Yp = 0.5",
                "reference_source": "API TR 5C3 Section 8 / ISO 10400 Eq. 32",
                "analytical_or_published_target": {"reduction_factor": 0.651384},
                "numerical_tolerance": "1e-5 relative",
                "validation_level": "analytical"
            }
        ]
    },
    "M03": {
        "module_id": "M03",
        "title": "Log Response Clustering",
        "governing_physics": "Reproducible deterministic k-means with training-only scaling",
        "intended_use": "Native-depth exploratory electrofacies clustering across wireline log curves",
        "applicability_envelope": {
            "curves": "GR, RHOB, NPHI, DT, RT",
            "depth_regularity": "Monotonically increasing depth index"
        },
        "withholding_conditions": [
            "Missing null sentinel declaration",
            "Single-value unvarying curve",
            "Direct geological facies inference without core calibration"
        ],
        "qualification_status": "software_verified",
        "evidence_basis": "Scikit-learn deterministic seeded Lloyd k-means algorithm",
        "benchmarks": [
            {
                "name": "Synthetic 3-Cluster Separation",
                "description": "Standard synthetic sandstone, shale, and carbonate log profiles",
                "reference_source": "GeoDrill Synthetic Log Suite",
                "analytical_or_published_target": {"inertia_convergence": True},
                "numerical_tolerance": "1e-7 relative",
                "validation_level": "manufactured"
            }
        ]
    },
    "M04": {
        "module_id": "M04",
        "title": "Shaly-Sand Analysis",
        "governing_physics": "Dual-water & Thomas-Stieber structural/laminated/dispersed shale volume",
        "intended_use": "Exploration of effective porosity and water saturation sensitivity bounds",
        "applicability_envelope": {
            "porosity_range": "0.02 to 0.40",
            "shale_volume": "0.0 to 0.70"
        },
        "withholding_conditions": [
            "Clean-sand endmember porosity less than shale porosity",
            "Apparent porosity exceeding unity",
            "Single-curve Archie calculation in microporous shale"
        ],
        "qualification_status": "software_verified",
        "evidence_basis": "Thomas-Stieber (1975) & Dual-Water (Clavier et al., 1984) analytical bounds",
        "benchmarks": [
            {
                "name": "Thomas-Stieber Clean Sand Laminate",
                "description": "Laminated shale volume calculation with known sand/shale points",
                "reference_source": "Thomas-Stieber 1975 Figure 3",
                "analytical_or_published_target": {"vsh_lam": 0.25, "phie": 0.18},
                "numerical_tolerance": "1e-4 relative",
                "validation_level": "analytical"
            }
        ]
    },
    "M06": {
        "module_id": "M06",
        "title": "Hydraulics & Pressure Profiles",
        "governing_physics": "Steady laminar pipe and concentric-annular Newtonian, Bingham, Herschel-Bulkley flow",
        "intended_use": "Circulating standpipe and annular pressure profile calculations against pore/frac window",
        "applicability_envelope": {
            "flow_regime": "Laminar (Re < 2100)",
            "geometry": "Concentric circular pipe and concentric annulus",
            "fluid_type": "Incompressible single-phase drilling mud"
        },
        "withholding_conditions": [
            "Turbulent flow regime (Re > 2500)",
            "Severe pipe eccentricity (> 0.7)",
            "Two-phase gas aerated mud without PVT characterization",
            "Temperature-dependent mud thermal expansion"
        ],
        "qualification_status": "software_verified",
        "evidence_basis": "API RP 13D Herschel-Bulkley slot-flow analytical integration",
        "benchmarks": [
            {
                "name": "API 13D Herschel-Bulkley Annulus",
                "description": "Standard Herschel-Bulkley fluid circulating at 1500 L/min",
                "reference_source": "API Recommended Practice 13D Annex B",
                "analytical_or_published_target": {"dp_annulus_pa": 2.14e6},
                "numerical_tolerance": "1e-3 relative",
                "validation_level": "analytical"
            }
        ]
    },
    "M07": {
        "module_id": "M07",
        "title": "Wellbore Stability",
        "governing_physics": "Kirsch linear elastic effective stresses with thermal restrained-wall stress",
        "intended_use": "Screening circumferential effective stress concentration and shear/tensile failure criteria",
        "applicability_envelope": {
            "rock_behavior": "Linear isotropic elastic",
            "filtercake": "Impermeable barrier at wellbore wall"
        },
        "withholding_conditions": [
            "Porous-plastic yielding (Drucker-Prager / Mohr-Coulomb cap)",
            "Time-dependent shale swelling and chemical hydration",
            "Operational mud-weight window authorization"
        ],
        "qualification_status": "software_verified",
        "evidence_basis": "Kirsch (1898) and Bradley (1979) borehole stress solution",
        "benchmarks": [
            {
                "name": "Kirsch Normal Fault Stress",
                "description": "Vertical well in anisotropic horizontal stress field",
                "reference_source": "Zoback Reservoir Geomechanics Eq. 6.21",
                "analytical_or_published_target": {"sigma_theta_max_pa": 74.2e6},
                "numerical_tolerance": "1e-4 relative",
                "validation_level": "analytical"
            }
        ]
    },
    "M08": {
        "module_id": "M08",
        "title": "Cuttings Transport",
        "governing_physics": "Dilute spherical Stokes settling in near-vertical laminar annular mud flow with conserved mass balance",
        "intended_use": "Evaluating settling velocity and volumetric cuttings concentration in vertical/low-angle wells",
        "applicability_envelope": {
            "wellbore_inclination": "0 to 30 degrees",
            "particle_concentration": "< 5% volume fraction",
            "particle_reynolds": "< 1.0 (Stokes regime)"
        },
        "withholding_conditions": [
            "Deviated well stationary dunes (> 35 deg inclination)",
            "Turbulent swirling pipe rotation cleaning",
            "Non-spherical flat cuttings drag without shape factor"
        ],
        "qualification_status": "software_verified",
        "evidence_basis": "Stokes law and conserved 1D solid-liquid mass balance",
        "benchmarks": [
            {
                "name": "Stokes Settling Benchmark",
                "description": "2 mm quartz sphere in 30 cP Newtonian fluid",
                "reference_source": "Bird, Stewart, Lightfoot Transport Phenomena",
                "analytical_or_published_target": {"v_settling_m_s": 0.0423},
                "numerical_tolerance": "1e-4 relative",
                "validation_level": "analytical"
            }
        ]
    },
    "M09": {
        "module_id": "M09",
        "title": "Surge & Swab",
        "governing_physics": "Uniform-annulus acoustic pressure wave transient from pipe tripping motion",
        "intended_use": "Predicting bottomhole dynamic pressure surges and swab differentials during tripping",
        "applicability_envelope": {
            "annulus": "Uniform concentric cross-section",
            "fluid_compressibility": "Constant acoustic sonic velocity"
        },
        "withholding_conditions": [
            "Gel breaking yield spikes without Bingham rheopexy history",
            "Gas void cavitation swab",
            "Variable stepped hole diameter without wave reflections"
        ],
        "qualification_status": "software_verified",
        "evidence_basis": "Burkhardt (1961) / Lubinski acoustic transient tripping equations",
        "benchmarks": [
            {
                "name": "Burkhardt Acoustic Surge",
                "description": "Closed-ended drillpipe running at 0.5 m/s",
                "reference_source": "Burkhardt SPE-1546-G",
                "analytical_or_published_target": {"surge_dp_pa": 1.48e6},
                "numerical_tolerance": "1e-3 relative",
                "validation_level": "analytical"
            }
        ]
    },
    "M10": {
        "module_id": "M10",
        "title": "Torque & Drag / MSE",
        "governing_physics": "Soft-string quasi-static 3D curved well equilibrium with Coulomb friction and Teale MSE",
        "intended_use": "Calculating tension/compression profiles, surface hookload, and rotating torque",
        "applicability_envelope": {
            "friction_model": "Coulomb friction coefficient 0.1 to 0.5",
            "string_stiffness": "Soft-string assumption (bending stiffness negligible relative to tension)"
        },
        "withholding_conditions": [
            "Severe localized doglegs where tubular bending moment dominates contact force",
            "Surface MSE used as true downhole mechanical bit energy",
            "BHA point-contact centralizers"
        ],
        "qualification_status": "software_verified",
        "evidence_basis": "Johancsik et al. (1984) / Sheppard et al. (1987) soft-string formulation",
        "benchmarks": [
            {
                "name": "Johancsik 3D Build Section",
                "description": "Standard build and turn curve with 0.25 friction factor",
                "reference_source": "SPE 11380",
                "analytical_or_published_target": {"hookload_slackoff_n": 482000.0},
                "numerical_tolerance": "1e-4 relative",
                "validation_level": "analytical"
            }
        ]
    },
    "M11": {
        "module_id": "M11",
        "title": "Buckling Assessment",
        "governing_physics": "Straight inclined pipe sinusoidal (Paslay-Dawson) and helical (Chen-Cheatham) compression limits",
        "intended_use": "Screening localized pipe stability and calculating conditional helical drag load transfer",
        "applicability_envelope": {
            "pipe_state": "Continuous uniform pipe in constant-inclination hole section",
            "contact": "Wellbore wall confined lateral displacement"
        },
        "withholding_conditions": [
            "Curved wellbore sections where dogleg curvature alters buckling thresholds",
            "Rotating drillstring dynamic whirl buckling",
            "Unsupported casing cavities or washouts"
        ],
        "qualification_status": "software_verified",
        "evidence_basis": "Paslay-Dawson (1984) & Chen-Cheatham (1990) analytical thresholds",
        "benchmarks": [
            {
                "name": "Paslay-Dawson 60-degree Inclined Hole",
                "description": "5-inch drillpipe in 8.5-inch hole at 60 deg inclination",
                "reference_source": "SPE 13156 Eq. 14",
                "analytical_or_published_target": {"f_crit_sinusoidal_n": 142500.0},
                "numerical_tolerance": "1e-4 relative",
                "validation_level": "analytical"
            }
        ]
    },
    "M12": {
        "module_id": "M12",
        "title": "BHA Dynamics",
        "governing_physics": "Coupled 3-coordinate cantilever linear modal simulation with energy conservation checks",
        "intended_use": "Evaluating uncoupled and coupled natural frequencies and qualitative transient vibration response",
        "applicability_envelope": {
            "geometry": "Uniform straight cantilever segment",
            "time_integration": "Runge-Kutta 4th order with energy residual tracking"
        },
        "withholding_conditions": [
            "Full 3D continuous borehole contact and bounce",
            "Downhole modal observability claims from low-frequency surface data",
            "Virtual tool failure diagnosis without certified downhole MWD shock sensors"
        ],
        "qualification_status": "software_verified",
        "evidence_basis": "Euler-Bernoulli cantilever beam eigenmodes and RK4 numerical energy conservation",
        "benchmarks": [
            {
                "name": "Euler-Bernoulli Cantilever 1st Mode",
                "description": "10 m uniform steel drill collar natural frequency",
                "reference_source": "Blevins Formulas for Natural Frequency",
                "analytical_or_published_target": {"freq_hz": 8.42},
                "numerical_tolerance": "1e-4 relative",
                "validation_level": "analytical"
            }
        ]
    },
    "M13": {
        "module_id": "M13",
        "title": "Bit Condition & Runs",
        "governing_physics": "Kaplan-Meier non-parametric survival analysis with prospective censoring accounting",
        "intended_use": "Comparing historical bit run survival and conditional meterage costs within inspected cohorts",
        "applicability_envelope": {
            "cohort": "Comparable formation and bit design family",
            "censoring": "Explicitly declared cutoff date and right-censored run records"
        },
        "withholding_conditions": [
            "Predicting remaining life of an active bit in the hole",
            "Individual trip recommendation",
            "Cross-formation pooling without lithology normalization"
        ],
        "qualification_status": "software_verified",
        "evidence_basis": "Kaplan & Meier (1958) non-parametric estimation",
        "benchmarks": [
            {
                "name": "Standard Censored Survival Cohort",
                "description": "10-run cohort with 4 failures and 6 censored runs",
                "reference_source": "Collett Modelling Survival Data in Medical Research",
                "analytical_or_published_target": {"survival_at_50h": 0.70},
                "numerical_tolerance": "1e-6 relative",
                "validation_level": "analytical"
            }
        ]
    },
    "M14": {
        "module_id": "M14",
        "title": "Casing Wear & Fatigue",
        "governing_physics": "Archard contact wear volume and Palmgren-Miner cumulative cycle damage",
        "intended_use": "Tracking integrated string contact energy and estimating uniform residual casing burst",
        "applicability_envelope": {
            "wear_model": "Archard specific wear factor",
            "fatigue_model": "Linear S-N curve cycle summation"
        },
        "withholding_conditions": [
            "Localized crescent-shaped keyseat wear slot burst rating",
            "Corrosion-fatigue crack propagation (Paris law)",
            "Barrier certificate closure"
        ],
        "qualification_status": "software_verified",
        "evidence_basis": "API TR 5C3 / Archard contact mechanics equations",
        "benchmarks": [
            {
                "name": "Archard Constant Contact Wear",
                "description": "100 km rotating sliding distance with certified wear coefficient",
                "reference_source": "White & Dawson (1987) SPE-14325",
                "analytical_or_published_target": {"wear_depth_m": 0.00245},
                "numerical_tolerance": "1e-4 relative",
                "validation_level": "analytical"
            }
        ]
    },
    "M15": {
        "module_id": "M15",
        "title": "Flow & Stock Anomalies",
        "governing_physics": "Rig control-volume conservation of mass with causal window persistence tracking",
        "intended_use": "Replaying inlet flow, outlet flow, and active pit mass balances to detect persistent residuals",
        "applicability_envelope": {
            "data_source": "High-frequency surface mass flow and pit volume telemetry",
            "state_gating": "Active drilling and continuous pumping only"
        },
        "withholding_conditions": [
            "Operational well-control kick alarm",
            "Unknown flow during pipe connections or pump trips",
            "Inferred downhole influx type (gas vs water)"
        ],
        "qualification_status": "software_verified",
        "evidence_basis": "Conservation of mass and causal sequence detection",
        "benchmarks": [
            {
                "name": "Conserved Pit Mass Replay",
                "description": "Zero-leakage steady circulating system with sensor noise",
                "reference_source": "Manufactured Mass Balance Benchmark",
                "analytical_or_published_target": {"mean_residual_kg_s": 0.0},
                "numerical_tolerance": "1e-5 relative",
                "validation_level": "manufactured"
            }
        ]
    },
    "M16": {
        "module_id": "M16",
        "title": "Gas & Phase Studies",
        "governing_physics": "Peng-Robinson cubic equation of state with Rachford-Rice flash solver",
        "intended_use": "Thermodynamic vapor-liquid equilibrium flash for characterized non-polar hydrocarbon binary mixtures",
        "applicability_envelope": {
            "components": "Pure light hydrocarbons (C1-C10, CO2, N2)",
            "pressure_range": "0.1 to 100 MPa",
            "temperature_range": "270 to 500 K"
        },
        "withholding_conditions": [
            "Whole oil-based mud or water-based mud surfactant emulsion solubility",
            "Multiphase flow slip velocity in wellbore annulus",
            "Gas kick emergence depth prediction"
        ],
        "qualification_status": "software_verified",
        "evidence_basis": "Peng & Robinson (1976) Ind. Eng. Chem. Fundam.",
        "benchmarks": [
            {
                "name": "Methane-Ethane Binary Flash",
                "description": "50/50 mol% C1/C2 mixture at 200 K and 3 MPa",
                "reference_source": "GPSA Engineering Data Book Fig. 25-14",
                "analytical_or_published_target": {"vapor_fraction": 0.628},
                "numerical_tolerance": "1e-3 relative",
                "validation_level": "analytical"
            }
        ]
    },
    "M17": {
        "module_id": "M17",
        "title": "Supervisory Research Simulation",
        "governing_physics": "First-order pressure plant model with rate-limited PID controller and strict request gating",
        "intended_use": "Offline software research on supervisory control request validation, leases, idempotency, and interlocks",
        "applicability_envelope": {
            "mode": "Virtual software simulation sandbox only",
            "actuation": "Simulated choke valve position"
        },
        "withholding_conditions": [
            "Live rig network connection or PLC command issuance",
            "Hardware-in-the-loop equipment clearance",
            "Automatic well-control execution"
        ],
        "qualification_status": "software_verified",
        "evidence_basis": "Deterministic first-order ODE integration and default-deny permission gates",
        "benchmarks": [
            {
                "name": "First-Order Step Response",
                "description": "Step pressure setpoint request from 10 to 15 MPa with tau=5s",
                "reference_source": "Franklin, Powell, Emami-Naeini Feedback Control",
                "analytical_or_published_target": {"settling_time_s": 19.5},
                "numerical_tolerance": "1e-3 relative",
                "validation_level": "analytical"
            }
        ]
    }
}


def get_qualification_card(module_id: str) -> QualificationCard | None:
    """Retrieve the qualification card for a specific module ID."""
    clean_id = module_id.upper().strip()
    if clean_id.startswith("M"):
        rest = clean_id[1:]
        if rest.isdigit():
            clean_id = f"M{int(rest):02d}"
    elif clean_id.isdigit():
        clean_id = f"M{int(clean_id):02d}"
    return QUALIFICATION_LEDGER.get(clean_id)


def list_qualification_cards() -> list[QualificationCard]:
    """Return all qualification cards sorted by module ID."""
    return [QUALIFICATION_LEDGER[k] for k in sorted(QUALIFICATION_LEDGER.keys())]
