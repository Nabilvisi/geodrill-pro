import math
import pytest
from packages.engineering.usability import (
    convert_unit,
    paginate_and_search_records,
    UNIT_PROFILES,
)


def test_unit_roundtrip_numerical_precision():
    """Verify that supported unit conversions round-trip within strict numerical tolerance."""
    # Length: meters -> feet -> meters
    val_m = 3254.65
    val_ft = convert_unit(val_m, "length", "m", "ft")
    roundtrip_m = convert_unit(val_ft, "length", "ft", "m")
    assert roundtrip_m is not None
    assert abs(roundtrip_m - val_m) < 1e-9

    # Pressure: Pa -> psi -> Pa
    val_pa = 25000000.0  # 25 MPa
    val_psi = convert_unit(val_pa, "pressure", "pa", "psi")
    roundtrip_pa = convert_unit(val_psi, "pressure", "psi", "pa")
    assert roundtrip_pa is not None
    assert abs(roundtrip_pa - val_pa) < 1e-5

    # Force: N -> klbf -> N
    val_n = 150000.0
    val_klbf = convert_unit(val_n, "force", "n", "klbf")
    roundtrip_n = convert_unit(val_klbf, "force", "klbf", "n")
    assert roundtrip_n is not None
    assert abs(roundtrip_n - val_n) < 1e-6


def test_unit_conversion_preserves_unknowns():
    """Acceptance criterion: unknown / None values NEVER become zero."""
    assert convert_unit(None, "length", "m", "ft") is None
    assert convert_unit(None, "pressure", "psi", "pa") is None


def test_record_pagination_and_search():
    """Verify searchable paginated record tables with row validation flags."""
    # Generate 150 mock survey stations
    rows = []
    for i in range(150):
        rows.append({
            "md": i * 30.0,
            "inc": round(i * 0.2, 2),
            "azi": 45.0,
            "has_error": i in {10, 75, 120},
            "formation": "Sandstone A" if i < 50 else ("Shale B" if i < 100 else "Carbonate C")
        })

    # Page 1 pagination
    res_p1 = paginate_and_search_records(rows, page=1, page_size=20)
    assert res_p1["page"] == 1
    assert res_p1["page_size"] == 20
    assert res_p1["total_records"] == 150
    assert res_p1["total_pages"] == 8
    assert len(res_p1["rows"]) == 20

    # Search filter
    res_search = paginate_and_search_records(rows, search_query="Carbonate", page=1, page_size=100)
    assert res_search["total_matching"] == 50
    assert len(res_search["rows"]) == 50
    assert all("Carbonate" in r["formation"] for r in res_search["rows"])

    # Jump to error flags
    res_errors = paginate_and_search_records(rows, error_flag_key="has_error", page=1, page_size=200)
    assert res_errors["flagged_indices"] == [10, 75, 120]


def test_unit_profiles_definition():
    assert "SI" in UNIT_PROFILES
    assert "Field_US" in UNIT_PROFILES
    assert "Metric_Oilfield" in UNIT_PROFILES
    assert UNIT_PROFILES["Field_US"]["length"] == "ft"
    assert UNIT_PROFILES["SI"]["pressure"] == "Pa"


def test_api_unit_endpoints(tmp_path):
    from fastapi.testclient import TestClient
    from services.api.main import create_app
    app = create_app(data_dir=tmp_path)
    client = TestClient(app)
    client.headers["X-Geodrill-Client"] = "workstation"
    client.get("/api/session")

    # 1. Profiles list
    r_prof = client.get("/api/units/profiles")
    assert r_prof.status_code == 200
    assert "SI" in r_prof.json()

    # 2. Conversion endpoint
    r_conv = client.post("/api/units/convert", json={
        "value": 1000.0,
        "dimension": "length",
        "from_unit": "m",
        "to_unit": "ft"
    })
    assert r_conv.status_code == 200
    res = r_conv.json()
    assert abs(res["converted_value"] - 3280.839895) < 0.01

    # 3. None preserved
    r_null = client.post("/api/units/convert", json={
        "value": None,
        "dimension": "force",
        "from_unit": "N",
        "to_unit": "klbf"
    })
    assert r_null.status_code == 200
    assert r_null.json()["converted_value"] is None
