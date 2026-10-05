import pytest
import xml.etree.ElementTree as ET
from packages.engineering.ddr import (
    create_daily_drilling_report,
    reconcile_timeline_24h,
    export_ddr_to_xml,
)


def test_reconcile_timeline_perfect_24h():
    """Verify clean 24h timeline without gaps or overlaps."""
    acts = [
        {"id": "1", "from_time_iso": "2026-10-05T00:00:00", "to_time_iso": "2026-10-05T08:00:00", "is_npt": False},
        {"id": "2", "from_time_iso": "2026-10-05T08:00:00", "to_time_iso": "2026-10-05T12:00:00", "is_npt": True, "npt_category": "Equipment", "npt_reason": "Top drive leak"},
        {"id": "3", "from_time_iso": "2026-10-05T12:00:00", "to_time_iso": "2026-10-05T24:00:00", "is_npt": False},
    ]
    # Note: 24:00:00 is technically 00:00:00 next day
    acts[2]["to_time_iso"] = "2026-10-06T00:00:00"

    is_rec, prod_h, npt_h, unacc_h, gaps, overlaps = reconcile_timeline_24h(acts)
    assert is_rec is True
    assert prod_h == 20.0
    assert npt_h == 4.0
    assert unacc_h == 0.0
    assert len(gaps) == 0
    assert len(overlaps) == 0


def test_reconcile_timeline_with_gaps_and_overlaps():
    """Verify gap and overlap detection in 24h timeline."""
    acts = [
        # 00:00 - 06:00 (6 hrs)
        {"id": "1", "from_time_iso": "2026-10-05T00:00:00", "to_time_iso": "2026-10-05T06:00:00", "is_npt": False},
        # Gap: 06:00 - 07:00 (1 hr unaccounted)
        # 07:00 - 14:00 (7 hrs)
        {"id": "2", "from_time_iso": "2026-10-05T07:00:00", "to_time_iso": "2026-10-05T14:00:00", "is_npt": False},
        # Overlap: 13:30 - 18:00 (30 min overlap with act 2)
        {"id": "3", "from_time_iso": "2026-10-05T13:30:00", "to_time_iso": "2026-10-05T18:00:00", "is_npt": True},
    ]

    is_rec, prod_h, npt_h, unacc_h, gaps, overlaps = reconcile_timeline_24h(acts)
    assert is_rec is False
    assert len(gaps) == 1
    assert gaps[0]["gap_hrs"] == 1.0
    assert len(overlaps) == 1
    assert overlaps[0]["overlap_hrs"] == 0.5


def test_create_ddr_and_export_xml():
    """Verify DDR creation, cost reconciliation, and XML export."""
    acts = [
        {"id": "a1", "from_time_iso": "2026-10-05T00:00:00", "to_time_iso": "2026-10-05T18:00:00", "phase": "Drilling", "activity_code": "DRL", "description": "Drill 8.5in section", "depth_m": 3200.0, "is_npt": False},
        {"id": "a2", "from_time_iso": "2026-10-05T18:00:00", "to_time_iso": "2026-10-06T00:00:00", "phase": "Repair", "activity_code": "REP", "description": "Repair mud pump #2", "is_npt": True, "npt_category": "Rig Equipment", "npt_reason": "Pump valve failure", "npt_author": "Drilling Supervisor"},
    ]
    costs = [
        {"category": "Rig Spread Rate", "planned_cost": 50000.0, "actual_cost": 50000.0, "note": "Day rate"},
        {"category": "Mud Chemicals", "planned_cost": 8000.0, "actual_cost": 11500.0, "note": "Additional LCM added"},
    ]

    report = create_daily_drilling_report(
        project_id="proj-99",
        well_name="Well Bravo-1",
        report_date="2026-10-05",
        report_no=14,
        current_depth_m=3200.0,
        previous_depth_m=3050.0,
        activities=acts,
        costs=costs,
        currency="USD"
    )

    assert report["well_name"] == "Well Bravo-1"
    assert report["progress_24h_m"] == 150.0
    assert report["activities_reconciled_24h"] is True
    assert report["total_productive_hrs"] == 18.0
    assert report["total_npt_hrs"] == 6.0
    assert report["total_planned_cost"] == 58000.0
    assert report["total_actual_cost"] == 61500.0
    assert report["cost_variance"] == 3500.0

    # XML round-trip check
    xml_str = export_ddr_to_xml(report)
    assert '<?xml version="1.0" encoding="utf-8"?>' in xml_str or "<DailyDrillingReport" in xml_str
    
    # Parse back XML to verify validity
    root = ET.fromstring(xml_str)
    assert root.tag == "DailyDrillingReport"
    assert root.find("Header/WellName").text == "Well Bravo-1"
    assert root.find("TimeSummary/NPTHours").text == "6.0"
    assert root.find("CostLedger/Variance").text == "3500.0"


def test_api_ddr_endpoints(tmp_path):
    from fastapi.testclient import TestClient
    from services.api.main import create_app
    app = create_app(data_dir=tmp_path)
    client = TestClient(app)
    client.headers["X-Geodrill-Client"] = "workstation"
    client.get("/api/session")

    r_proj = client.post("/api/demo")
    assert r_proj.status_code == 201
    pid = r_proj.json()["id"]

    ddr_payload = {
        "report_date": "2026-10-05",
        "report_no": 1,
        "current_depth_m": 1250.0,
        "previous_depth_m": 1100.0,
        "activities": [
            {"from_time_iso": "2026-10-05T00:00:00", "to_time_iso": "2026-10-05T24:00:00", "phase": "Drilling", "activity_code": "DRL", "description": "Continuous drilling", "depth_m": 1250.0, "is_npt": False}
        ],
        "costs": [
            {"category": "Rig Dayrate", "planned_cost": 45000.0, "actual_cost": 45000.0, "note": "Contract rate"}
        ],
        "currency": "USD"
    }
    # Fix 24:00:00 ISO format
    ddr_payload["activities"][0]["to_time_iso"] = "2026-10-06T00:00:00"

    r_ddr = client.post(f"/api/projects/{pid}/ddr", json=ddr_payload)
    assert r_ddr.status_code == 200
    report = r_ddr.json()
    assert report["progress_24h_m"] == 150.0
    assert report["activities_reconciled_24h"] is True

    # Export XML
    r_xml = client.post(f"/api/projects/{pid}/ddr/export/xml", json=report)
    assert r_xml.status_code == 200
    assert "application/xml" in r_xml.headers["content-type"]
    assert "<DailyDrillingReport" in r_xml.text
