"""Unit tests for Qualification Ledger and Reference Cases (GD-A05)."""
from fastapi.testclient import TestClient
from packages.engineering.qualification import (
    QUALIFICATION_LEDGER,
    get_qualification_card,
    list_qualification_cards,
)
from services.api.main import create_app


def test_qualification_cards_coverage():
    """Verify that all primary engineering modules have a qualification card."""
    cards = list_qualification_cards()
    assert len(cards) >= 14
    ids = {c["module_id"] for c in cards}
    expected = {"M01", "M02", "M03", "M04", "M06", "M07", "M08", "M09", "M10", "M11", "M12", "M13", "M14", "M15", "M16", "M17"}
    assert expected.issubset(ids)


def test_qualification_card_structure():
    """Verify that each card explicitly distinguishes software verification and withholding conditions."""
    for card in list_qualification_cards():
        assert "module_id" in card
        assert "title" in card
        assert "governing_physics" in card
        assert "intended_use" in card
        assert "applicability_envelope" in card
        assert isinstance(card["withholding_conditions"], list)
        assert len(card["withholding_conditions"]) > 0
        assert card["qualification_status"] in {
            "software_verified",
            "experimentally_validated",
            "field_qualified",
            "withheld",
            "excluded",
        }
        assert isinstance(card["benchmarks"], list)
        assert len(card["benchmarks"]) > 0
        for b in card["benchmarks"]:
            assert "name" in b
            assert "reference_source" in b
            assert "numerical_tolerance" in b
            assert b["validation_level"] in {"analytical", "manufactured", "experimental", "field"}


def test_qualification_api_endpoints(tmp_path):
    """Test /api/qualification/cards and /api/qualification/cards/{module_id} endpoints."""
    app = create_app(data_dir=tmp_path)
    client = TestClient(app)
    client.headers["X-Geodrill-Client"] = "workstation"
    # Seed session
    client.get("/api/session")

    # List all cards
    res = client.get("/api/qualification/cards")
    assert res.status_code == 200
    cards = res.json()
    assert isinstance(cards, list)
    assert any(c["module_id"] == "M01" for c in cards)
    assert any(c["module_id"] == "M10" for c in cards)

    # Get single valid card
    res_m01 = client.get("/api/qualification/cards/M01")
    assert res_m01.status_code == 200
    card_m01 = res_m01.json()
    assert card_m01["module_id"] == "M01"
    assert "Minimum-curvature" in card_m01["governing_physics"]

    # Module id with lowercase or integer
    res_m1 = client.get("/api/qualification/cards/m1")
    assert res_m1.status_code == 200
    assert res_m1.json()["module_id"] == "M01"

    # Non-existent module
    res_404 = client.get("/api/qualification/cards/M99")
    assert res_404.status_code == 404
