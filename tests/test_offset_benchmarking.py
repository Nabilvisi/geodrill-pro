"""Verification test suite for GD-A14 Offset Well Performance Benchmarking."""
import pytest
from packages.engineering.offset_benchmarking import (
    OffsetWellRecord,
    CohortSelectionCriteria,
    OffsetBenchmarkingInput,
    calculate_offset_benchmarks,
)


@pytest.fixture
def sample_offset_wells():
    dummy_hash = "a" * 64
    return [
        OffsetWellRecord(
            well_id="OW-01",
            well_name="Offset Alpha 1",
            field_name="North Sea Troll",
            hole_diameter_m=0.31115,  # 12-1/4"
            bit_family="PDC-6blades-16mm",
            formation="Sognefjord Sand",
            trajectory_type="vertical",
            spud_date="2024-01-10",
            drilled_interval_m=1200.0,
            drilling_hours=48.0,  # 25 m/h
            npt_hours=12.0,       # 20% NPT
            total_cost=2400000.0, # 2000 USD/m
            cost_currency="USD",
            is_adjudicated=True,
            adjudication_note="Signed by lead company man and drilling superintendent",
            evidence_source_hash=dummy_hash,
        ),
        OffsetWellRecord(
            well_id="OW-02",
            well_name="Offset Alpha 2",
            field_name="North Sea Troll",
            hole_diameter_m=0.31115,  # 12-1/4"
            bit_family="PDC-6blades-16mm",
            formation="Sognefjord Sand",
            trajectory_type="vertical",
            spud_date="2024-03-15",
            drilled_interval_m=1100.0,
            drilling_hours=40.0,  # 27.5 m/h
            npt_hours=8.0,        # 16.7% NPT
            total_cost=2090000.0, # 1900 USD/m
            cost_currency="USD",
            is_adjudicated=True,
            adjudication_note="Reconciled DDR #14-22 verified",
            evidence_source_hash=dummy_hash,
        ),
        OffsetWellRecord(
            well_id="OW-03",
            well_name="Offset Alpha 3",
            field_name="North Sea Troll",
            hole_diameter_m=0.31115,  # 12-1/4"
            bit_family="PDC-6blades-16mm",
            formation="Sognefjord Sand",
            trajectory_type="vertical",
            spud_date="2024-05-20",
            drilled_interval_m=1300.0,
            drilling_hours=65.0,  # 20 m/h
            npt_hours=25.0,       # 27.7% NPT
            total_cost=2860000.0, # 2200 USD/m
            cost_currency="USD",
            is_adjudicated=True,
            adjudication_note="Reviewed post-well NPT panel report",
            evidence_source_hash=dummy_hash,
        ),
        OffsetWellRecord(
            well_id="OW-04",
            well_name="Offset Alpha 4",
            field_name="North Sea Troll",
            hole_diameter_m=0.31115,  # 12-1/4"
            bit_family="RollerCone-TCI",
            formation="Sognefjord Sand",
            trajectory_type="vertical",
            spud_date="2024-06-01",
            drilled_interval_m=800.0,
            drilling_hours=60.0,  # 13.3 m/h
            npt_hours=10.0,
            total_cost=1800000.0,
            cost_currency="USD",
            is_adjudicated=True,
            adjudication_note="Standard DDR verified",
            evidence_source_hash=dummy_hash,
        ),
        OffsetWellRecord(
            well_id="OW-05",
            well_name="Offset Beta 1 (Unadjudicated)",
            field_name="North Sea Troll",
            hole_diameter_m=0.31115,
            bit_family="PDC-6blades-16mm",
            formation="Sognefjord Sand",
            trajectory_type="vertical",
            spud_date="2024-07-10",
            drilled_interval_m=1000.0,
            drilling_hours=35.0,
            npt_hours=5.0,
            total_cost=1700000.0,
            cost_currency="USD",
            is_adjudicated=False,
            evidence_source_hash=dummy_hash,
        ),
    ]


def test_cohort_filtering_and_adjudication_enforcement(sample_offset_wells):
    criteria = CohortSelectionCriteria(
        target_hole_diameter_m=0.31115,
        target_formation="Sognefjord Sand",
        target_bit_family="PDC-6blades-16mm",
        target_trajectory_type="vertical",
        require_adjudicated_only=True,
    )
    payload = OffsetBenchmarkingInput(
        study_name="Troll 12-1/4 Section Benchmarking",
        geometry_revision_id="geom-01",
        depth_datum="RKB",
        source_note="Offset well database Q2-2024",
        evidence_state="supplied",
        planned_interval_m=1000.0,
        criteria=criteria,
        offset_wells=sample_offset_wells,
        planned_rig_rate_per_day=250000.0,
    )
    res = calculate_offset_benchmarks(payload)

    assert res["status"] == "calculated"
    assert res["total_offset_wells_supplied"] == 5
    assert res["eligible_cohort_count"] == 3  # OW-01, OW-02, OW-03
    assert len(res["excluded_wells"]) == 2

    # OW-04 excluded due to bit family
    ex_04 = next(x for x in res["excluded_wells"] if x["well_id"] == "OW-04")
    assert "Bit family" in ex_04["reason"]

    # OW-05 excluded due to unadjudicated
    ex_05 = next(x for x in res["excluded_wells"] if x["well_id"] == "OW-05")
    assert "Unadjudicated" in ex_05["reason"]

    # Verify ROP stats
    rops = res["benchmarks"]["rate_of_penetration_m_h"]
    assert rops["p50_median_m_h"] == 25.0
    assert rops["p10_favorable_m_h"] > rops["p50_median_m_h"]

    # Verify duration and cost projections
    proj = res["projections"]
    assert proj["planned_interval_m"] == 1000.0
    assert proj["projected_duration_days"]["p10_favorable"] < proj["projected_duration_days"]["p90_conservative"]
    assert proj["projected_total_cost"]["p10_favorable"] < proj["projected_total_cost"]["p90_conservative"]


def test_withholding_when_cohort_size_below_threshold(sample_offset_wells):
    # Only select RollerCone, which has only 1 well (OW-04)
    criteria = CohortSelectionCriteria(
        target_hole_diameter_m=0.31115,
        target_formation="Sognefjord Sand",
        target_bit_family="RollerCone-TCI",
    )
    payload = OffsetBenchmarkingInput(
        study_name="Small Cohort Test",
        geometry_revision_id="geom-01",
        depth_datum="RKB",
        source_note="Test note",
        evidence_state="supplied",
        planned_interval_m=1000.0,
        criteria=criteria,
        offset_wells=sample_offset_wells,
        planned_rig_rate_per_day=200000.0,
    )
    res = calculate_offset_benchmarks(payload)

    assert res["status"] == "withheld"
    assert "below statistical threshold of 3 wells" in res["reasons"][0]
    assert res["benchmarks"] is None
    assert res["projections"] is None
