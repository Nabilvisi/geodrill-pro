"""Directional well planning, coordinate transformations, and ISCWSA survey uncertainty engine (GD-A10).

Covers:
- Geodetic coordinate reference transformations (WGS84 UTM zones 1-60 N/S via pyproj).
- Elevation reference datums (RKB, MSL, Ground Level) and North conventions (True, Grid, Magnetic).
- ISCWSA MWD Rev5.11 survey uncertainty propagation with strict evidence requirements and withholding.
- Multi-well 3D proximity and closest-approach geometry analysis (crossing, parallel, vertical, endpoint).
- Strict engineering safety guardrail: clearance_generated = False.
"""
from typing import Any, Literal, TypedDict
import json
import math
from pathlib import Path
import numpy as np
import pyproj

from welleng.survey import Survey, SurveyHeader


ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = Path(__file__).resolve().parent / "directional_cases" / "manifest.json"


class CoordinateConvertRequest(TypedDict, total=False):
    latitude_deg: float
    longitude_deg: float
    easting_m: float
    northing_m: float
    crs_code: str  # e.g. "EPSG:32631"
    datum: str
    elevation_rkb_m: float
    elevation_msl_m: float


class CoordinateResult(TypedDict):
    latitude_deg: float
    longitude_deg: float
    easting_m: float
    northing_m: float
    crs_code: str
    datum: str
    central_meridian_deg: float
    scale_factor: float
    grid_convergence_deg: float
    valid: bool
    notes: list[str]


class SurveyStation(TypedDict):
    md_m: float
    inclination_deg: float
    azimuth_deg: float


class SurveyUncertaintyInput(TypedDict, total=False):
    stations: list[dict[str, float]]
    tool_model: str  # e.g. "ISCWSA MWD Rev5.11"
    tool_revision: str
    latitude_deg: float
    longitude_deg: float
    b_total_nt: float
    dip_deg: float
    declination_deg: float
    convergence_deg: float
    crs_code: str
    datum: str
    elevation_m: float
    source_label: str  # "iscwsa_calculated" or "supplied"
    supplied_covariances: list[list[float]] | None


class StationUncertainty(TypedDict):
    md_m: float
    tvd_m: float
    northing_m: float
    easting_m: float
    cov_nev: list[list[float]]  # 3x3
    semi_major_1sigma_m: float
    semi_minor_1sigma_m: float
    vertical_1sigma_m: float
    semi_major_2sigma_m: float
    semi_minor_2sigma_m: float
    vertical_2sigma_m: float
    azimuth_major_deg: float


class SurveyUncertaintyResult(TypedDict):
    tool_model: str
    tool_revision: str
    stations_count: int
    withheld: bool
    withholding_reason: str | None
    source_label: str
    total_depth_md_m: float
    stations: list[StationUncertainty]
    td_covariance_nev: list[list[float]] | None


class ProximityInput(TypedDict):
    reference_well_name: str
    reference_stations: list[dict[str, float]]
    reference_start_nev: list[float]  # [N, E, V]
    offset_well_name: str
    offset_stations: list[dict[str, float]]
    offset_start_nev: list[float]  # [N, E, V]
    geomagnetic: dict[str, float] | None


class ProximityStation(TypedDict):
    ref_md_m: float
    closest_offset_md_m: float
    ref_pos_nev: list[float]
    offset_pos_nev: list[float]
    c2c_distance_m: float
    horizontal_distance_m: float
    vertical_distance_m: float
    relative_vector_nev: list[float]


class ProximityResult(TypedDict):
    reference_well_name: str
    offset_well_name: str
    closest_approach: dict[str, Any]
    stations: list[ProximityStation]
    min_c2c_distance_m: float
    geometry_type: str
    clearance_generated: bool
    clearance_statement: str


def parse_utm_epsg(crs_code: str) -> tuple[int, bool]:
    """Parse EPSG code to UTM zone and hemisphere (is_north)."""
    code = crs_code.strip().upper()
    if code.startswith("EPSG:"):
        epsg_int = int(code.split(":")[1])
    else:
        epsg_int = int(code)

    if 32601 <= epsg_int <= 32660:
        return (epsg_int - 32600, True)
    elif 32701 <= epsg_int <= 32760:
        return (epsg_int - 32700, False)
    raise ValueError(f"Unsupported UTM EPSG code '{crs_code}'. Must be in range 32601-32660 (North) or 32701-32760 (South).")


def convert_geodetic_to_projected(
    lat_deg: float,
    lon_deg: float,
    crs_code: str = "EPSG:32631",
    datum: str = "WGS84",
) -> CoordinateResult:
    """Convert WGS84 Geodetic (Lat, Lon) to Projected (Easting, Northing)."""
    if not (-80.0 <= lat_deg <= 84.0):
        raise ValueError(f"Latitude {lat_deg}° is outside the standard UTM validity range [-80°, 84°].")
    if not (-180.0 <= lon_deg <= 180.0):
        raise ValueError(f"Longitude {lon_deg}° is outside [-180°, 180°].")

    zone, is_north = parse_utm_epsg(crs_code)
    central_meridian = (zone - 1) * 6 - 180 + 3

    transformer = pyproj.Transformer.from_crs("EPSG:4326", crs_code, always_xy=True)
    easting, northing = transformer.transform(lon_deg, lat_deg)

    proj = pyproj.Proj(crs_code)
    factors = proj.get_factors(lon_deg, lat_deg)

    notes = [
        f"Transformed to UTM Zone {zone}{'N' if is_north else 'S'} (EPSG:{parse_utm_epsg(crs_code)[0] + (32600 if is_north else 32700)}).",
        f"Central meridian: {central_meridian}° E.",
    ]

    return {
        "latitude_deg": round(lat_deg, 8),
        "longitude_deg": round(lon_deg, 8),
        "easting_m": round(easting, 3),
        "northing_m": round(northing, 3),
        "crs_code": crs_code,
        "datum": datum,
        "central_meridian_deg": float(central_meridian),
        "scale_factor": round(factors.parallel_scale, 6),
        "grid_convergence_deg": round(factors.meridian_convergence, 6),
        "valid": True,
        "notes": notes,
    }


def convert_projected_to_geodetic(
    easting_m: float,
    northing_m: float,
    crs_code: str = "EPSG:32631",
    datum: str = "WGS84",
) -> CoordinateResult:
    """Convert Projected UTM (Easting, Northing) to WGS84 Geodetic (Lat, Lon)."""
    zone, is_north = parse_utm_epsg(crs_code)
    central_meridian = (zone - 1) * 6 - 180 + 3

    transformer = pyproj.Transformer.from_crs(crs_code, "EPSG:4326", always_xy=True)
    lon, lat = transformer.transform(easting_m, northing_m)

    if not (-80.0 <= lat <= 84.0):
        raise ValueError(f"Projected coordinates result in out-of-bounds latitude {lat:.4f}°.")

    proj = pyproj.Proj(crs_code)
    factors = proj.get_factors(lon, lat)

    return {
        "latitude_deg": round(lat, 8),
        "longitude_deg": round(lon, 8),
        "easting_m": round(easting_m, 3),
        "northing_m": round(northing_m, 3),
        "crs_code": crs_code,
        "datum": datum,
        "central_meridian_deg": float(central_meridian),
        "scale_factor": round(factors.parallel_scale, 6),
        "grid_convergence_deg": round(factors.meridian_convergence, 6),
        "valid": True,
        "notes": [f"Inverse projection from {crs_code}."],
    }


def _extract_eigen_ellipse(cov_nev: np.ndarray) -> tuple[float, float, float, float]:
    """Extract semi-major, semi-minor, vertical 1-sigma, and major axis azimuth."""
    # 2D horizontal sub-matrix [NN, NE; EN, EE]
    cov_ne = cov_nev[0:2, 0:2]
    eigvals, eigvecs = np.linalg.eigh(cov_ne)
    # Ensure eigenvalues are non-negative
    eigvals = np.maximum(eigvals, 0.0)
    # Sort descending
    order = np.argsort(eigvals)[::-1]
    a = math.sqrt(eigvals[order[0]])
    b = math.sqrt(eigvals[order[1]])
    v = math.sqrt(max(0.0, cov_nev[2, 2]))

    # Major axis orientation in degrees clockwise from North
    v_major = eigvecs[:, order[0]]
    # v_major[0] = North component, v_major[1] = East component
    azi_rad = math.atan2(v_major[1], v_major[0])
    azi_deg = (math.degrees(azi_rad) + 360.0) % 360.0
    return a, b, v, azi_deg


def calculate_survey_uncertainty(payload: SurveyUncertaintyInput) -> SurveyUncertaintyResult:
    """Calculate survey uncertainty using the ISCWSA MWD Rev5.11 error model.
    
    If geomagnetic reference parameters or tool error model are missing,
    uncertainty calculation is strictly withheld with an explicit engineering explanation.
    """
    stations_data = payload.get("stations", [])
    if not stations_data:
        raise ValueError("Survey stations list cannot be empty.")

    tool_model = payload.get("tool_model", "ISCWSA MWD Rev5.11")
    tool_revision = payload.get("tool_revision", "Rev5.11")
    source_label = payload.get("source_label", "iscwsa_calculated")

    # Withholding check: ISCWSA error propagation strictly requires latitude and geomagnetic field
    lat = payload.get("latitude_deg")
    b_total = payload.get("b_total_nt")
    dip = payload.get("dip_deg")

    if tool_model != "ISCWSA MWD Rev5.11" and source_label != "supplied":
        return {
            "tool_model": tool_model,
            "tool_revision": tool_revision,
            "stations_count": len(stations_data),
            "withheld": True,
            "withholding_reason": f"Generic error ellipse for '{tool_model}' not supported. Implemented model is ISCWSA MWD Rev5.11.",
            "source_label": source_label,
            "total_depth_md_m": float(stations_data[-1].get("md_m", 0.0)),
            "stations": [],
            "td_covariance_nev": None,
        }

    if lat is None or b_total is None or dip is None:
        return {
            "tool_model": tool_model,
            "tool_revision": tool_revision,
            "stations_count": len(stations_data),
            "withheld": True,
            "withholding_reason": "Positional uncertainty withheld: geomagnetic parameters (latitude, B-total, dip) or tool error model omitted. Generic ellipses not substituted.",
            "source_label": source_label,
            "total_depth_md_m": float(stations_data[-1].get("md_m", 0.0)),
            "stations": [],
            "td_covariance_nev": None,
        }

    # Extract MD, Inc, Azi
    md_list = [float(s["md_m"]) for s in stations_data]
    inc_list = [float(s["inclination_deg"]) for s in stations_data]
    azi_list = [float(s["azimuth_deg"]) for s in stations_data]

    dec = payload.get("declination_deg", 0.0)
    lon = payload.get("longitude_deg", 0.0)

    header = SurveyHeader(
        latitude=lat,
        longitude=lon,
        b_total=b_total,
        dip=dip,
        declination=dec,
    )

    survey = Survey(
        md=md_list,
        inc=inc_list,
        azi=azi_list,
        header=header,
        error_model="ISCWSA MWD Rev5.11",
    )

    cov_nevs = survey.err.errors.cov_NEVs
    tvd_arr = survey.tvd
    n_arr = survey.n
    e_arr = survey.e

    station_results: list[StationUncertainty] = []
    for i, md in enumerate(md_list):
        cov = cov_nevs[i]
        a1, b1, v1, azi_major = _extract_eigen_ellipse(cov)
        cov_matrix_list = [[round(float(val), 6) for val in row] for row in cov]

        station_results.append({
            "md_m": round(md, 2),
            "tvd_m": round(float(tvd_arr[i]), 3),
            "northing_m": round(float(n_arr[i]), 3),
            "easting_m": round(float(e_arr[i]), 3),
            "cov_nev": cov_matrix_list,
            "semi_major_1sigma_m": round(a1, 4),
            "semi_minor_1sigma_m": round(b1, 4),
            "vertical_1sigma_m": round(v1, 4),
            "semi_major_2sigma_m": round(a1 * 2.0, 4),
            "semi_minor_2sigma_m": round(b1 * 2.0, 4),
            "vertical_2sigma_m": round(v1 * 2.0, 4),
            "azimuth_major_deg": round(azi_major, 2),
        })

    td_cov = [[round(float(val), 6) for val in row] for row in cov_nevs[-1]]

    return {
        "tool_model": tool_model,
        "tool_revision": tool_revision,
        "stations_count": len(station_results),
        "withheld": False,
        "withholding_reason": None,
        "source_label": "iscwsa_mwd_rev5.11_calculated",
        "total_depth_md_m": round(md_list[-1], 2),
        "stations": station_results,
        "td_covariance_nev": td_cov,
    }


def _point_to_segment(p: np.ndarray, q0: np.ndarray, q1: np.ndarray) -> tuple[float, np.ndarray, float]:
    """Find closest point on segment q0->q1 from single point p.
    Returns (distance, closest_q, t_fraction).
    """
    v = q1 - q0
    len_v2 = float(np.dot(v, v))
    if len_v2 < 1e-12:
        dist = float(np.linalg.norm(p - q0))
        return dist, q0, 0.0
    t = float(np.dot(p - q0, v)) / len_v2
    t = max(0.0, min(1.0, t))
    cq = q0 + t * v
    dist = float(np.linalg.norm(p - cq))
    return dist, cq, t


def _segment_closest_point(
    p0: np.ndarray, p1: np.ndarray,
    q0: np.ndarray, q1: np.ndarray,
) -> tuple[float, np.ndarray, np.ndarray]:
    """Compute the minimum 3D distance between two continuous line segments S1(p0->p1) and S2(q0->q1)."""
    u = p1 - p0
    v = q1 - q0
    w = p0 - q0
    a = float(np.dot(u, u))
    b = float(np.dot(u, v))
    c = float(np.dot(v, v))
    d = float(np.dot(u, w))
    e = float(np.dot(v, w))

    if a < 1e-12 and c < 1e-12:
        return float(np.linalg.norm(p0 - q0)), p0, q0
    if a < 1e-12:
        dist, cq, _ = _point_to_segment(p0, q0, q1)
        return dist, p0, cq
    if c < 1e-12:
        dist, cp, _ = _point_to_segment(q0, p0, p1)
        return dist, cp, q0

    D = a * c - b * b
    sc, sN, sD = 0.0, 0.0, D
    tc, tN, tD = 0.0, 0.0, D

    EPS = 1e-12
    if D < EPS:
        sN = 0.0
        sD = 1.0
        tN = e
        tD = c
    else:
        sN = (b * e - c * d)
        tN = (a * e - b * d)
        if sN < 0.0:
            sN = 0.0
            tN = e
            tD = c
        elif sN > sD:
            sN = sD
            tN = e + b
            tD = c

    if tN < 0.0:
        tc = 0.0
        if -d < 0.0:
            sc = 0.0
        elif -d > a:
            sc = 1.0
        else:
            sc = -d / a if a > EPS else 0.0
    elif tN > tD:
        tc = 1.0
        if (-d + b) < 0.0:
            sc = 0.0
        elif (-d + b) > a:
            sc = 1.0
        else:
            sc = (-d + b) / a if a > EPS else 0.0
    else:
        tc = tN / tD if abs(tD) > EPS else 0.0
        sc = sN / sD if abs(sD) > EPS else 0.0

    cp = p0 + sc * u
    cq = q0 + tc * v
    dist = float(np.linalg.norm(cp - cq))
    return dist, cp, cq


def calculate_proximity(payload: ProximityInput) -> ProximityResult:
    """Calculate multi-well 3D proximity and closest-approach trajectory geometry.
    
    CRITICAL: Does NOT generate drilling clearance, anti-collision authorizations,
    or go/no-go operational decisions.
    """
    ref_name = payload.get("reference_well_name", "Reference Well")
    off_name = payload.get("offset_well_name", "Offset Well")
    ref_stns = payload.get("reference_stations", [])
    off_stns = payload.get("offset_stations", [])

    if len(ref_stns) < 2 or len(off_stns) < 2:
        raise ValueError("Both reference and offset wells must contain at least 2 survey stations.")

    ref_start = np.array(payload.get("reference_start_nev", [0.0, 0.0, 0.0]), dtype=float)
    off_start = np.array(payload.get("offset_start_nev", [0.0, 0.0, 0.0]), dtype=float)

    # Build surveys via welleng Minimum Curvature
    ref_survey = Survey(
        md=[float(s["md_m"]) for s in ref_stns],
        inc=[float(s["inclination_deg"]) for s in ref_stns],
        azi=[float(s["azimuth_deg"]) for s in ref_stns],
        start_nev=ref_start,
    )
    off_survey = Survey(
        md=[float(s["md_m"]) for s in off_stns],
        inc=[float(s["inclination_deg"]) for s in off_stns],
        azi=[float(s["azimuth_deg"]) for s in off_stns],
        start_nev=off_start,
    )

    ref_nev = np.column_stack([ref_survey.n, ref_survey.e, ref_survey.tvd])
    off_nev = np.column_stack([off_survey.n, off_survey.e, off_survey.tvd])
    ref_mds = [float(s["md_m"]) for s in ref_stns]
    off_mds = [float(s["md_m"]) for s in off_stns]

    proximity_stations: list[ProximityStation] = []
    global_min_dist = float("inf")
    closest_info: dict[str, Any] = {}

    # Station-by-station and continuous segment distance evaluation
    for i, r_pos in enumerate(ref_nev):
        r_md = ref_mds[i]
        station_min_dist = float("inf")
        best_off_pos = off_nev[0]
        best_off_md = off_mds[0]

        # Check against each segment of offset well
        for j in range(len(off_nev) - 1):
            q0, q1 = off_nev[j], off_nev[j + 1]
            seg_dist, cq, frac = _point_to_segment(r_pos, q0, q1)
            if seg_dist < station_min_dist:
                station_min_dist = seg_dist
                best_off_pos = cq
                best_off_md = off_mds[j] + frac * (off_mds[j + 1] - off_mds[j])

        rel_vec = best_off_pos - r_pos
        h_dist = float(np.linalg.norm(rel_vec[:2]))
        v_dist = abs(float(rel_vec[2]))

        proximity_stations.append({
            "ref_md_m": round(r_md, 2),
            "closest_offset_md_m": round(best_off_md, 2),
            "ref_pos_nev": [round(float(x), 3) for x in r_pos],
            "offset_pos_nev": [round(float(x), 3) for x in best_off_pos],
            "c2c_distance_m": round(station_min_dist, 3),
            "horizontal_distance_m": round(h_dist, 3),
            "vertical_distance_m": round(v_dist, 3),
            "relative_vector_nev": [round(float(x), 3) for x in rel_vec],
        })

    # Continuous global closest approach between all segments
    for i in range(len(ref_nev) - 1):
        p0, p1 = ref_nev[i], ref_nev[i + 1]
        for j in range(len(off_nev) - 1):
            q0, q1 = off_nev[j], off_nev[j + 1]
            dist, cp, cq = _segment_closest_point(p0, p1, q0, q1)
            if dist < global_min_dist:
                global_min_dist = dist
                u_seg = p1 - p0
                norm_u = np.linalg.norm(u_seg)
                r_frac = (np.linalg.norm(cp - p0) / norm_u) if norm_u > 1e-6 else 0.0
                r_md = ref_mds[i] + r_frac * (ref_mds[i + 1] - ref_mds[i])

                v_seg = q1 - q0
                norm_v = np.linalg.norm(v_seg)
                o_frac = (np.linalg.norm(cq - q0) / norm_v) if norm_v > 1e-6 else 0.0
                o_md = off_mds[j] + o_frac * (off_mds[j + 1] - off_mds[j])

                rel_vec = cq - cp
                closest_info = {
                    "ref_md_m": round(r_md, 2),
                    "offset_md_m": round(o_md, 2),
                    "c2c_distance_m": round(dist, 3),
                    "horizontal_distance_m": round(float(np.linalg.norm(rel_vec[:2])), 3),
                    "vertical_distance_m": round(abs(float(rel_vec[2])), 3),
                    "ref_pos_nev": [round(float(x), 3) for x in cp],
                    "offset_pos_nev": [round(float(x), 3) for x in cq],
                    "relative_vector_nev": [round(float(x), 3) for x in rel_vec],
                }

    # Determine qualitative geometry
    dists = [s["c2c_distance_m"] for s in proximity_stations]
    spread = max(dists) - min(dists)
    if spread < 0.1:
        geom_type = "parallel"
    elif closest_info.get("ref_md_m", 0) > ref_mds[-1] * 0.95:
        geom_type = "endpoint_approach"
    elif closest_info.get("c2c_distance_m", 0) < min(dists[0], dists[-1]) * 0.7:
        geom_type = "crossing"
    else:
        geom_type = "diverging_or_slant"

    return {
        "reference_well_name": ref_name,
        "offset_well_name": off_name,
        "closest_approach": closest_info,
        "stations": proximity_stations,
        "min_c2c_distance_m": round(global_min_dist, 3),
        "geometry_type": geom_type,
        "clearance_generated": False,
        "clearance_statement": (
            "No drilling clearance, anti-collision authorizations, or operational go/no-go permission generated. "
            "Positional proximity analysis only; engineering qualification and clearance management remain separate human-governed gates."
        ),
    }


def load_diagnostic_manifest() -> dict[str, Any]:
    """Load benchmark cases manifest."""
    if not MANIFEST_PATH.exists():
        raise FileNotFoundError(f"Diagnostic manifest not found at {MANIFEST_PATH}")
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def verify_iscwsa_diagnostics() -> dict[str, Any]:
    """Verify implemented ISCWSA MWD Rev5.11 survey uncertainty propagation against pinned diagnostic cases.
    
    Declared tolerances before comparison:
    - Absolute covariance tolerance: 0.0005 m²
    - Relative covariance tolerance: 0.001 (0.1%)
    """
    manifest = load_diagnostic_manifest()
    tolerances = manifest.get("tolerances", {})
    abs_tol = float(tolerances.get("covariance_abs_tol_m2", 0.0005))
    rel_tol = float(tolerances.get("covariance_rel_tol", 0.001))

    results: dict[str, Any] = {}
    all_passed = True

    for case_id, case in manifest.get("cases", {}).items():
        if not case_id.startswith("iscwsa_well_"):
            continue

        header = case["header"]
        payload: SurveyUncertaintyInput = {
            "stations": case["stations"],
            "tool_model": "ISCWSA MWD Rev5.11",
            "tool_revision": "Rev5.11",
            "latitude_deg": header["latitude_deg"],
            "longitude_deg": header["longitude_deg"],
            "b_total_nt": header["b_total_nt"],
            "dip_deg": header["dip_deg"],
            "declination_deg": header["declination_deg"],
            "crs_code": header["crs"],
            "datum": header["datum"],
            "elevation_m": header["elevation_m"],
            "source_label": "iscwsa_calculated",
        }

        computed = calculate_survey_uncertainty(payload)
        computed_td_cov = np.array(computed["td_covariance_nev"])
        pinned_td_cov = np.array(case["pinned_td_covariance_nev"])

        diff = np.abs(computed_td_cov - pinned_td_cov)
        max_abs = float(np.max(diff))
        rel_diff = diff / np.maximum(np.abs(pinned_td_cov), 1e-9)
        max_rel = float(np.max(rel_diff))

        passed = (max_abs <= abs_tol) or (max_rel <= rel_tol)
        if not passed:
            all_passed = False

        results[case_id] = {
            "case_id": case_id,
            "title": case["title"],
            "passed": passed,
            "max_abs_error_m2": round(max_abs, 8),
            "max_rel_error": round(max_rel, 8),
            "declared_abs_tol": abs_tol,
            "declared_rel_tol": rel_tol,
            "computed_td_cov": computed["td_covariance_nev"],
            "pinned_td_cov": case["pinned_td_covariance_nev"],
        }

    return {
        "all_passed": all_passed,
        "cases_evaluated": len(results),
        "declared_tolerances": tolerances,
        "results": results,
    }
