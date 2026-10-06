"""Directional well planning and anti-collision application service."""
from typing import Any
from uuid import uuid4
import math
from packages.domain.models import (
    SurveyStation,
    SurveyRevision,
    TrajectoryRevision,
    TrajectoryType,
    utc_now_iso,
)
from packages.domain.calculation import (
    CalculationEnvelope,
    CalculationStatus,
    QualificationLevel,
    ModelClass,
    compute_inputs_hash,
)
from packages.engineering.models import Survey, SurveyRequest
from packages.engineering.physics import minimum_curvature, MODEL_VERSION
from packages.engineering.directional import (
    convert_geodetic_to_projected,
    convert_projected_to_geodetic,
    calculate_survey_uncertainty,
    calculate_proximity,
    CoordinateConvertRequest,
    SurveyUncertaintyInput,
    ProximityInput,
)


class DirectionalService:
    @staticmethod
    def calculate_minimum_curvature_trajectory(
        stations: list[SurveyStation],
        wellbore_id: str,
        survey_revision_id: str | None = None,
        revision_number: int = 1,
        trajectory_type: TrajectoryType = TrajectoryType.PLANNED,
    ) -> tuple[TrajectoryRevision, CalculationEnvelope]:
        """Compute 3D trajectory from survey stations using the minimum curvature method."""
        survey_req = SurveyRequest(
            stations=[
                Survey(
                    md_m=s.md_m,
                    inclination_rad=s.inc_rad,
                    azimuth_rad=s.azi_rad,
                )
                for s in stations
            ]
        )
        calculated_rows = minimum_curvature(survey_req)

        computed_stations: list[SurveyStation] = []
        for i, s in enumerate(stations):
            row = calculated_rows[i]
            computed_stations.append(
                SurveyStation(
                    md_m=s.md_m,
                    inc_rad=s.inc_rad,
                    azi_rad=s.azi_rad,
                    tvd_m=row["tvd_m"],
                    north_m=row["north_m"],
                    east_m=row["east_m"],
                    dls_rad_m=row["dogleg_rad_m"],
                    tool_code=s.tool_code,
                    quality=s.quality,
                    source_row=s.source_row,
                )
            )

        final_stn = computed_stations[-1]
        closure_dist = math.sqrt(final_stn.north_m ** 2 + final_stn.east_m ** 2)
        closure_azi = math.atan2(final_stn.east_m, final_stn.north_m) % (2 * math.pi)
        max_dls = max(s.dls_rad_m for s in computed_stations)

        traj = TrajectoryRevision(
            id=str(uuid4()),
            wellbore_id=wellbore_id,
            revision=revision_number,
            trajectory_type=trajectory_type,
            survey_revision_id=survey_revision_id,
            stations=computed_stations,
            total_md_m=final_stn.md_m,
            final_tvd_m=final_stn.tvd_m,
            closure_distance_m=closure_dist,
            closure_azimuth_rad=closure_azi,
            max_dls_rad_m=max_dls,
            created_at=utc_now_iso(),
        )

        inputs_summary = [{"md_m": s.md_m, "inc_rad": s.inc_rad, "azi_rad": s.azi_rad} for s in stations]
        envelope = CalculationEnvelope(
            calculation_id=str(uuid4()),
            model="directional.minimum_curvature",
            model_version=MODEL_VERSION,
            model_class=ModelClass.DETERMINISTIC_VERIFIED,
            qualification=QualificationLevel.PUBLISHED_BENCHMARK,
            status=CalculationStatus.CALCULATED,
            inputs_hash=compute_inputs_hash({"stations": inputs_summary, "wellbore_id": wellbore_id, "survey_revision_id": survey_revision_id, "trajectory_type": trajectory_type}),
            survey_revision_id=survey_revision_id,
            geometry_revision_id=traj.id,
            result={
                "total_md_m": traj.total_md_m,
                "final_tvd_m": traj.final_tvd_m,
                "closure_distance_m": traj.closure_distance_m,
                "closure_azimuth_rad": traj.closure_azimuth_rad,
                "stations_count": len(computed_stations),
            },
            assumptions=["Minimum curvature spherical arc interpolation between stations"],
            limitations=["Station MDs must strictly increase; vertical tie-in assumed at MD 0"],
            created_at=utc_now_iso(),
        )

        return traj, envelope

    @staticmethod
    def calculate_uncertainty(
        payload: SurveyUncertaintyInput,
        geometry_revision_id: str | None = None,
        survey_revision_id: str | None = None,
    ) -> CalculationEnvelope:
        """Calculate ISCWSA survey uncertainty envelope."""
        raw_result = calculate_survey_uncertainty(payload)
        is_withheld = raw_result.get("withheld", False)
        status = CalculationStatus.WITHHELD if is_withheld else CalculationStatus.CALCULATED
        reason = raw_result.get("withholding_reason") or ""

        envelope = CalculationEnvelope(
            calculation_id=str(uuid4()),
            model="directional.uncertainty_iscwsa",
            model_version=raw_result.get("tool_revision", "undeclared"),
            model_class=ModelClass.DETERMINISTIC_VERIFIED,
            qualification=QualificationLevel.INTERNAL_VERIFICATION,
            status=status,
            inputs_hash=compute_inputs_hash(payload),
            geometry_revision_id=geometry_revision_id,
            survey_revision_id=survey_revision_id,
            result=raw_result,
            assumptions=[
                "Declared survey error model; pinned diagnostic verification is not field qualification",
                f"Tool model: {raw_result.get('tool_model')}",
            ],
            warnings=[f"WITHHELD: {reason}"] if is_withheld else [],
            limitations=[
                "Uncertainty ellipsoids represent statistical bounds; actual wellbore may vary with geological formation anisotropy",
                "Does not constitute autonomous drilling clearance",
            ],
            created_at=utc_now_iso(),
        )
        return envelope

    @staticmethod
    def calculate_anticollision(
        payload: ProximityInput,
        ref_geometry_revision_id: str | None = None,
    ) -> CalculationEnvelope:
        """Calculate closest approach and 3D separation between reference and offset wells."""
        raw_result = calculate_proximity(payload)
        envelope = CalculationEnvelope(
            calculation_id=str(uuid4()),
            model="anticollision.closest_approach",
            model_version="GD-A10-proximity-1",
            model_class=ModelClass.DETERMINISTIC_VERIFIED,
            qualification=QualificationLevel.INTERNAL_VERIFICATION,
            status=CalculationStatus.CALCULATED,
            inputs_hash=compute_inputs_hash(payload),
            geometry_revision_id=ref_geometry_revision_id,
            result=raw_result,
            assumptions=[
                "Segment-to-segment 3D Euclidean distance minimum search",
                f"Reference well: {payload.get('reference_well_name', 'Reference')}",
                f"Offset well: {payload.get('offset_well_name', 'Offset')}",
            ],
            warnings=[],
            limitations=[
                "Explicit engineering safety guardrail: clearance_generated is False. Does NOT authorize drilling operations.",
            ],
            created_at=utc_now_iso(),
        )
        return envelope
