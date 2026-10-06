"""Verification test suite for GD-A10 Directional Engine, ISCWSA Error Propagation & Proximity."""
import pytest
import numpy as np

from packages.engineering.directional import (
    convert_geodetic_to_projected,
    convert_projected_to_geodetic,
    calculate_survey_uncertainty,
    calculate_proximity,
    load_diagnostic_manifest,
    verify_iscwsa_diagnostics,
    parse_utm_epsg,
)


def test_utm_epsg_parsing():
    zone, is_north = parse_utm_epsg("EPSG:32631")
    assert zone == 31
    assert is_north is True

    zone_s, is_north_s = parse_utm_epsg("EPSG:32750")
    assert zone_s == 50
    assert is_north_s is False

    with pytest.raises(ValueError, match="Unsupported UTM EPSG code"):
        parse_utm_epsg("EPSG:4326")


def test_coordinate_conversions_forward_and_inverse():
    # North Sea test point: Lat 60.0 N, Lon 3.0 E (Center of UTM 31N)
    fwd = convert_geodetic_to_projected(60.0, 3.0, "EPSG:32631")
    assert fwd["valid"] is True
    assert fwd["easting_m"] == 500000.0  # Exact central meridian
    assert abs(fwd["northing_m"] - 6651411.19) < 0.1
    assert abs(fwd["grid_convergence_deg"]) < 1e-4
    assert abs(fwd["scale_factor"] - 0.9996) < 1e-4

    # Roundtrip inverse
    inv = convert_projected_to_geodetic(fwd["easting_m"], fwd["northing_m"], "EPSG:32631")
    assert abs(inv["latitude_deg"] - 60.0) < 1e-6
    assert abs(inv["longitude_deg"] - 3.0) < 1e-6

    # Off-meridian test point: Lat 60.0 N, Lon 4.0 E
    fwd_off = convert_geodetic_to_projected(60.0, 4.0, "EPSG:32631")
    assert fwd_off["easting_m"] > 500000.0
    assert fwd_off["grid_convergence_deg"] > 0.5  # Convergence > 0 east of central meridian

    inv_off = convert_projected_to_geodetic(fwd_off["easting_m"], fwd_off["northing_m"], "EPSG:32631")
    assert abs(inv_off["latitude_deg"] - 60.0) < 1e-6
    assert abs(inv_off["longitude_deg"] - 4.0) < 1e-6


def test_coordinate_conversion_out_of_bounds_blocked():
    # Latitude > 84 degrees blocked for standard UTM
    with pytest.raises(ValueError, match="outside the standard UTM validity range"):
        convert_geodetic_to_projected(85.0, 0.0, "EPSG:32631")

    with pytest.raises(ValueError, match="outside the standard UTM validity range"):
        convert_geodetic_to_projected(-85.0, 0.0, "EPSG:32731")


def test_iscwsa_diagnostics_all_passed():
    report = verify_iscwsa_diagnostics()
    assert report["all_passed"] is True, f"Failed diagnostics: {report['results']}"
    assert report["cases_evaluated"] >= 3

    for case_id, res in report["results"].items():
        assert res["passed"] is True
        assert res["max_abs_error_m2"] <= report["declared_tolerances"]["covariance_abs_tol_m2"] or \
               res["max_rel_error"] <= report["declared_tolerances"]["covariance_rel_tol"]


def test_survey_uncertainty_withholding_when_evidence_missing():
    stations = [
        {"md_m": 0.0, "inclination_deg": 0.0, "azimuth_deg": 0.0},
        {"md_m": 1000.0, "inclination_deg": 10.0, "azimuth_deg": 45.0},
    ]

    # Case 1: Missing geomagnetic fields
    res = calculate_survey_uncertainty({
        "stations": stations,
        "tool_model": "ISCWSA MWD Rev5.11",
        # missing latitude_deg, b_total_nt, dip_deg
    })
    assert res["withheld"] is True
    assert "withheld" in res["withholding_reason"].lower()
    assert res["td_covariance_nev"] is None
    assert len(res["stations"]) == 0

    # Case 2: Generic / unknown tool model without ISCWSA specification
    res2 = calculate_survey_uncertainty({
        "stations": stations,
        "tool_model": "Generic Ellipse Model",
        "latitude_deg": 60.0,
        "b_total_nt": 50000.0,
        "dip_deg": 70.0,
    })
    assert res2["withheld"] is True
    assert "Generic error ellipse" in res2["withholding_reason"]


def test_proximity_geometry_crossing():
    manifest = load_diagnostic_manifest()
    case = manifest["cases"]["proximity_crossing"]
    res = calculate_proximity({
        "reference_well_name": case["reference_well"]["name"],
        "reference_stations": case["reference_well"]["stations"],
        "reference_start_nev": case["reference_well"]["start_nev"],
        "offset_well_name": case["offset_well"]["name"],
        "offset_stations": case["offset_well"]["stations"],
        "offset_start_nev": case["offset_well"]["start_nev"],
        "geomagnetic": None,
    })
    assert abs(res["min_c2c_distance_m"] - 25.0) < 0.05
    assert res["geometry_type"] == "crossing"
    assert res["clearance_generated"] is False
    assert "No drilling clearance" in res["clearance_statement"]


def test_proximity_geometry_parallel():
    manifest = load_diagnostic_manifest()
    case = manifest["cases"]["proximity_parallel"]
    res = calculate_proximity({
        "reference_well_name": case["reference_well"]["name"],
        "reference_stations": case["reference_well"]["stations"],
        "reference_start_nev": case["reference_well"]["start_nev"],
        "offset_well_name": case["offset_well"]["name"],
        "offset_stations": case["offset_well"]["stations"],
        "offset_start_nev": case["offset_well"]["start_nev"],
        "geomagnetic": None,
    })
    assert abs(res["min_c2c_distance_m"] - 30.0) < 0.05
    assert res["geometry_type"] == "parallel"
    assert res["clearance_generated"] is False


def test_proximity_geometry_vertical():
    manifest = load_diagnostic_manifest()
    case = manifest["cases"]["proximity_vertical"]
    res = calculate_proximity({
        "reference_well_name": case["reference_well"]["name"],
        "reference_stations": case["reference_well"]["stations"],
        "reference_start_nev": case["reference_well"]["start_nev"],
        "offset_well_name": case["offset_well"]["name"],
        "offset_stations": case["offset_well"]["stations"],
        "offset_start_nev": case["offset_well"]["start_nev"],
        "geomagnetic": None,
    })
    assert abs(res["min_c2c_distance_m"] - 50.0) < 0.05
    assert res["clearance_generated"] is False


def test_proximity_geometry_endpoint():
    manifest = load_diagnostic_manifest()
    case = manifest["cases"]["proximity_endpoint"]
    res = calculate_proximity({
        "reference_well_name": case["reference_well"]["name"],
        "reference_stations": case["reference_well"]["stations"],
        "reference_start_nev": case["reference_well"]["start_nev"],
        "offset_well_name": case["offset_well"]["name"],
        "offset_stations": case["offset_well"]["stations"],
        "offset_start_nev": case["offset_well"]["start_nev"],
        "geomagnetic": None,
    })
    assert abs(res["min_c2c_distance_m"] - 15.0) < 0.05
    assert res["clearance_generated"] is False
