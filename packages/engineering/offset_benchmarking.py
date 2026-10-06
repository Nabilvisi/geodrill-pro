"""Offset well performance benchmarking, cohort selection, and duration/cost uncertainty distributions (GD-A14).

Provides:
- Strict cohort selection by formation, hole size, bit family, and well trajectory.
- Clear disclosure of cohort inclusions, exclusions, and filtering rules.
- Empirical percentile distributions (P10, P50, P90) for ROP, NPT fraction, duration, and cost.
- Rigorous evidence withholding when cohort size < 3 or unadjudicated records are supplied.
- Strict safety boundary: descriptive statistical benchmarks only, no automated operational authorizations.
"""
from __future__ import annotations

import math
import numpy as np
from typing import Any, Dict, List, Literal, Optional
from pydantic import Field, model_validator

from .models import Contract
from .research_common import StudyInput, base


class OffsetWellRecord(Contract):
    well_id: str = Field(min_length=1, max_length=80)
    well_name: str = Field(min_length=1, max_length=100)
    field_name: str = Field(min_length=1, max_length=100)
    hole_diameter_m: float = Field(gt=0.05, le=1.5)
    bit_family: str = Field(min_length=1, max_length=100)
    formation: str = Field(min_length=1, max_length=100)
    trajectory_type: Literal["vertical", "slant", "horizontal", "s_curve"]
    spud_date: str
    drilled_interval_m: float = Field(gt=0.0, le=15000.0)
    drilling_hours: float = Field(gt=0.0, le=5000.0)
    npt_hours: float = Field(ge=0.0, le=5000.0)
    total_cost: float = Field(gt=0.0, le=1e10)
    cost_currency: str = Field(default="USD", pattern=r"^[A-Z]{3}$")
    is_adjudicated: bool
    adjudication_note: Optional[str] = Field(default=None, max_length=500)
    evidence_source_hash: str = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def validate_adjudication(self):
        if self.is_adjudicated and not self.adjudication_note:
            raise ValueError(f"Well '{self.well_name}': Adjudicated records require adjudication_note provenance.")
        return self


class CohortSelectionCriteria(Contract):
    target_hole_diameter_m: float = Field(gt=0.05, le=1.5)
    target_formation: str = Field(min_length=1, max_length=100)
    target_bit_family: Optional[str] = Field(default=None, max_length=100)
    target_trajectory_type: Optional[Literal["vertical", "slant", "horizontal", "s_curve"]] = None
    max_hole_diameter_diff_m: float = Field(default=0.0254, ge=0.0, le=0.2)
    require_adjudicated_only: bool = True


class OffsetBenchmarkingInput(StudyInput):
    planned_interval_m: float = Field(gt=0.0, le=15000.0)
    criteria: CohortSelectionCriteria
    offset_wells: List[OffsetWellRecord] = Field(min_length=1, max_length=200)
    planned_rig_rate_per_day: float = Field(gt=0.0, le=1e7)
    cost_currency: str = Field(default="USD", pattern=r"^[A-Z]{3}$")

    @model_validator(mode="after")
    def validate_wells(self):
        ids = [w.well_id for w in self.offset_wells]
        if len(ids) != len(set(ids)):
            raise ValueError("Offset well records contain duplicate well_ids.")
        return self


def calculate_offset_benchmarks(
    v: OffsetBenchmarkingInput,
    geometry: Any = None,
    path: Any = None,
) -> Dict[str, Any]:
    """Calculate ROP, NPT, duration, and cost benchmarks from historical offset well cohort."""
    out = base(
        "GD-A14-offset-benchmarking-1",
        "Empirical percentile benchmarking (P10, P50, P90) from historical offset well cohort; ROP and cost learning.",
        [
            "Descriptive historical cohort statistics only; not a guaranteed delivery duration or AFEs commitment.",
            "Normal/empirical distributions assume representative offset operational conditions without unseen geohazards.",
            "Adjudicated records verify NPT classification integrity; unadjudicated records are excluded under strict review mode.",
            "No drilling clearance, automated operational authorization, or equipment control is generated.",
        ]
    )

    criteria = v.criteria
    eligible_wells: List[OffsetWellRecord] = []
    excluded_wells: List[Dict[str, str]] = []

    for w in v.offset_wells:
        reasons = []
        if abs(w.hole_diameter_m - criteria.target_hole_diameter_m) > criteria.max_hole_diameter_diff_m + 1e-6:
            reasons.append(f"Hole diameter {w.hole_diameter_m*1000:.1f} mm outside target tolerance ({criteria.target_hole_diameter_m*1000:.1f} ± {criteria.max_hole_diameter_diff_m*1000:.1f} mm)")
        if w.formation.strip().lower() != criteria.target_formation.strip().lower():
            reasons.append(f"Formation '{w.formation}' does not match target '{criteria.target_formation}'")
        if criteria.target_bit_family and w.bit_family.strip().lower() != criteria.target_bit_family.strip().lower():
            reasons.append(f"Bit family '{w.bit_family}' does not match target '{criteria.target_bit_family}'")
        if criteria.target_trajectory_type and w.trajectory_type != criteria.target_trajectory_type:
            reasons.append(f"Trajectory '{w.trajectory_type}' does not match target '{criteria.target_trajectory_type}'")
        if criteria.require_adjudicated_only and not w.is_adjudicated:
            reasons.append("Unadjudicated NPT/DDR record rejected by strict policy")

        if reasons:
            excluded_wells.append({
                "well_id": w.well_id,
                "well_name": w.well_name,
                "reason": "; ".join(reasons)
            })
        else:
            eligible_wells.append(w)

    out["criteria"] = criteria.model_dump()
    out["total_offset_wells_supplied"] = len(v.offset_wells)
    out["eligible_cohort_count"] = len(eligible_wells)
    out["excluded_wells"] = excluded_wells
    out["cohort_wells"] = [
        {
            "well_id": w.well_id,
            "well_name": w.well_name,
            "field_name": w.field_name,
            "rop_m_h": round(w.drilled_interval_m / w.drilling_hours, 2),
            "npt_percentage": round(100.0 * w.npt_hours / (w.drilling_hours + w.npt_hours), 1),
            "drilled_m": w.drilled_interval_m,
            "drilling_hours": w.drilling_hours,
            "npt_hours": w.npt_hours,
            "total_cost": w.total_cost,
            "cost_per_m": round(w.total_cost / w.drilled_interval_m, 2),
            "source_hash": w.evidence_source_hash,
        }
        for w in eligible_wells
    ]

    # Withholding rule: minimum cohort size >= 3
    if len(eligible_wells) < 3:
        out["status"] = "withheld"
        out["reasons"] = [
            f"Eligible cohort size ({len(eligible_wells)}) is below statistical threshold of 3 wells. "
            "Broaden selection criteria or supply verified offset records."
        ]
        out["benchmarks"] = None
        out["projections"] = None
        return out

    # Compute metrics across eligible cohort
    rops = np.array([w.drilled_interval_m / w.drilling_hours for w in eligible_wells])
    npt_fracs = np.array([w.npt_hours / (w.drilling_hours + w.npt_hours) for w in eligible_wells])
    durations_per_1000m_days = np.array([
        ((w.drilling_hours + w.npt_hours) / 24.0) / (w.drilled_interval_m / 1000.0)
        for w in eligible_wells
    ])
    cost_per_m = np.array([w.total_cost / w.drilled_interval_m for w in eligible_wells])

    def percentiles(arr: np.ndarray) -> Dict[str, float]:
        # P10, P50, P90
        # In drilling: P10 is favorable (fast ROP, low duration, low cost)
        return {
            "p10": round(float(np.percentile(arr, 10)), 2),
            "p50": round(float(np.percentile(arr, 50)), 2),
            "p90": round(float(np.percentile(arr, 90)), 2),
            "mean": round(float(np.mean(arr)), 2),
            "std": round(float(np.std(arr)), 2),
        }

    # For ROP, higher is better: P10 = 90th percentile of speed, P90 = 10th percentile
    rop_stats = {
        "p10_favorable_m_h": round(float(np.percentile(rops, 90)), 2),
        "p50_median_m_h": round(float(np.percentile(rops, 50)), 2),
        "p90_conservative_m_h": round(float(np.percentile(rops, 10)), 2),
        "mean_m_h": round(float(np.mean(rops)), 2),
    }

    npt_stats = {
        "p10_favorable_pct": round(float(np.percentile(npt_fracs * 100.0, 10)), 1),
        "p50_median_pct": round(float(np.percentile(npt_fracs * 100.0, 50)), 1),
        "p90_conservative_pct": round(float(np.percentile(npt_fracs * 100.0, 90)), 1),
        "mean_pct": round(float(np.mean(npt_fracs * 100.0)), 1),
    }

    dur_1000m_stats = percentiles(durations_per_1000m_days)
    cost_per_m_stats = percentiles(cost_per_m)

    # Planned section projections for v.planned_interval_m
    planned_dist_k_m = v.planned_interval_m / 1000.0
    p10_days = dur_1000m_stats["p10"] * planned_dist_k_m
    p50_days = dur_1000m_stats["p50"] * planned_dist_k_m
    p90_days = dur_1000m_stats["p90"] * planned_dist_k_m

    p10_cost = cost_per_m_stats["p10"] * v.planned_interval_m
    p50_cost = cost_per_m_stats["p50"] * v.planned_interval_m
    p90_cost = cost_per_m_stats["p90"] * v.planned_interval_m

    out["status"] = "calculated"
    out["reasons"] = []
    out["benchmarks"] = {
        "rate_of_penetration_m_h": rop_stats,
        "non_productive_time_percentage": npt_stats,
        "duration_days_per_1000m": dur_1000m_stats,
        "cost_per_meter": cost_per_m_stats,
        "currency": v.cost_currency,
    }
    out["projections"] = {
        "planned_interval_m": v.planned_interval_m,
        "projected_duration_days": {
            "p10_favorable": round(p10_days, 2),
            "p50_expected": round(p50_days, 2),
            "p90_conservative": round(p90_days, 2),
        },
        "projected_total_cost": {
            "p10_favorable": round(p10_cost, 2),
            "p50_expected": round(p50_cost, 2),
            "p90_conservative": round(p90_cost, 2),
            "currency": v.cost_currency,
        },
    }
    return out
