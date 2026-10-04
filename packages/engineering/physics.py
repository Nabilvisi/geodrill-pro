"""Restricted deterministic models. SI internally; applicability is part of each result."""
import math
from .models import MSEInput, PressureInput, SurveyRequest

G = 9.80665
MODEL_VERSION = "0.1.0"
MIN_ROP_M_S = 1e-5  # numerical eligibility threshold, not an operating limit


def minimum_curvature(request: SurveyRequest) -> list[dict]:
    north = east = tvd = 0.0
    result = []
    for i, station in enumerate(request.stations):
        dogleg = 0.0
        if i:
            a = request.stations[i - 1]
            b = station
            dot = (math.cos(a.inclination_rad) * math.cos(b.inclination_rad)
                   + math.sin(a.inclination_rad) * math.sin(b.inclination_rad)
                   * math.cos(b.azimuth_rad - a.azimuth_rad))
            beta = math.acos(max(-1.0, min(1.0, dot)))
            if beta >= math.pi - 1e-6:
                raise ValueError("Antipodal survey directions are ambiguous; add intermediate stations.")
            rf = 1 + beta * beta / 12 + beta**4 / 120 if beta < 1e-4 else 2 * math.tan(beta / 2) / beta
            delta = b.md_m - a.md_m
            north += delta / 2 * rf * (math.sin(a.inclination_rad) * math.cos(a.azimuth_rad) + math.sin(b.inclination_rad) * math.cos(b.azimuth_rad))
            east += delta / 2 * rf * (math.sin(a.inclination_rad) * math.sin(a.azimuth_rad) + math.sin(b.inclination_rad) * math.sin(b.azimuth_rad))
            tvd += delta / 2 * rf * (math.cos(a.inclination_rad) + math.cos(b.inclination_rad))
            dogleg = beta / delta
        result.append({**station.model_dump(), "north_m": north, "east_m": east, "tvd_m": tvd, "dogleg_rad_m": dogleg})
    return result


def mse(data: MSEInput) -> dict:
    common = {"model": "teale-energy-balance", "version": MODEL_VERSION, "load_source": data.load_source,
              "label": "Surface MSE proxy" if data.load_source == "surface" else "Downhole MSE"}
    if data.drilling_state != "drilling":
        return {**common, "value_pa": None, "status": "withheld", "reason": "Not a confirmed drilling interval."}
    if data.rop_m_s <= MIN_ROP_M_S:
        return {**common, "value_pa": None, "status": "withheld", "reason": "ROP is at or below the numerical eligibility threshold (0.036 m/h)."}
    area = math.pi * data.bit_diameter_m**2 / 4
    value = data.wob_n / area + data.torque_nm * data.rotation_rad_s / (area * data.rop_m_s)
    if not math.isfinite(value):
        return {**common, "value_pa": None, "status": "withheld", "reason": "Result exceeds the finite numerical range."}
    return {**common, "value_pa": value, "status": "calculated", "reason": "Surface loads include string losses; motor energy is not resolved." if data.load_source == "surface" else "Assumes synchronized bit loads and speed."}


def pressure(data: PressureInput) -> dict:
    hydrostatic = data.density_kg_m3 * G * data.tvd_m
    bottom = data.surface_gauge_pa + hydrostatic + data.annular_loss_pa
    return {"model": "constant-density-pressure-balance", "version": MODEL_VERSION,
            "hydrostatic_pa": hydrostatic, "bottom_gauge_pa": bottom,
            "equivalent_density_kg_m3": bottom / (G * data.tvd_m),
            "above_pore_pa": bottom - data.pore_gauge_pa,
            "below_fracture_pa": data.fracture_gauge_pa - bottom,
            "within_entered_bounds": data.pore_gauge_pa <= bottom <= data.fracture_gauge_pa,
            "status": "scenario_only", "pressure_reference": "gauge, relative to atmosphere at surface",
            "assumptions": ["Constant fluid density; steady single phase.",
                            "Annular pressure loss is supplied, not predicted.",
                            "Equivalent density includes surface backpressure.",
                            "Only the entered TVD is checked; no whole-well clearance or operational approval."]}
