"""Calculation dependency graph and staleness evaluation for GeoDrill Pro v0.9."""
from enum import Enum
from typing import Any
from .calculation import CalculationEnvelope, CalculationStatus


class RevisionType(str, Enum):
    GEOMETRY = "geometry"
    SURVEY = "survey"
    FORMATION = "formation"
    MUD = "mud"
    BHA = "bha"
    CASING = "casing"
    MODEL_VERSION = "model_version"


# Mapping from calculation model family to the revision types that invalidate it
MODEL_DEPENDENCY_RULES: dict[str, set[RevisionType]] = {
    # Directional & Proximity
    "directional.minimum_curvature": {RevisionType.SURVEY},
    "directional.uncertainty_iscwsa": {RevisionType.SURVEY, RevisionType.GEOMETRY},
    "anticollision.closest_approach": {RevisionType.GEOMETRY, RevisionType.SURVEY},
    "anticollision.separation_factor": {RevisionType.GEOMETRY, RevisionType.SURVEY},

    # Hydraulics & Wellbore Pressure
    "hydraulics.pressure_profile": {RevisionType.GEOMETRY, RevisionType.MUD, RevisionType.BHA, RevisionType.CASING},
    "hydraulics.ecd": {RevisionType.GEOMETRY, RevisionType.MUD, RevisionType.BHA, RevisionType.CASING},
    "hydraulics.surge_swab": {RevisionType.GEOMETRY, RevisionType.MUD, RevisionType.BHA, RevisionType.CASING},
    "hydraulics.hole_cleaning": {RevisionType.GEOMETRY, RevisionType.MUD, RevisionType.BHA},

    # Torque, Drag & Mechanical
    "torque_drag.soft_string": {RevisionType.GEOMETRY, RevisionType.MUD, RevisionType.BHA, RevisionType.CASING},
    "torque_drag.stiff_string": {RevisionType.GEOMETRY, RevisionType.MUD, RevisionType.BHA, RevisionType.CASING},
    "buckling.dawson_paslay": {RevisionType.GEOMETRY, RevisionType.BHA, RevisionType.CASING},
    "casing.burst_collapse": {RevisionType.GEOMETRY, RevisionType.FORMATION, RevisionType.CASING, RevisionType.MUD},
    "casing.triaxial_envelope": {RevisionType.GEOMETRY, RevisionType.FORMATION, RevisionType.CASING},

    # Geomechanics & Stability
    "geomechanics.pore_fracture": {RevisionType.FORMATION, RevisionType.GEOMETRY},
    "geomechanics.wellbore_stability": {RevisionType.FORMATION, RevisionType.GEOMETRY, RevisionType.MUD},
    "geomechanics.thermo_poroelastic": {RevisionType.FORMATION, RevisionType.GEOMETRY, RevisionType.MUD},

    # Performance & Diagnostics
    "performance.mse": {RevisionType.BHA},
    "dynamics.stick_slip": {RevisionType.GEOMETRY, RevisionType.BHA},

    # Reports
    "reports.well_plan": {RevisionType.GEOMETRY, RevisionType.CASING, RevisionType.MUD, RevisionType.BHA},
    "reports.anticollision": {RevisionType.GEOMETRY, RevisionType.SURVEY},
    "reports.hydraulics": {RevisionType.GEOMETRY, RevisionType.MUD, RevisionType.BHA},
}


class StalenessEvaluator:
    """Evaluates whether an existing calculation envelope is stale with respect to active revisions."""

    @staticmethod
    def is_calculation_stale(
        envelope: CalculationEnvelope,
        active_geometry_rev: str | None = None,
        active_survey_rev: str | None = None,
        active_formation_rev: str | None = None,
        active_mud_rev: str | None = None,
        active_bha_rev: str | None = None,
        active_casing_rev: str | None = None,
        current_model_version: str | None = None,
    ) -> tuple[bool, list[str]]:
        """
        Evaluate staleness against current wellbore active revision IDs.
        Returns (is_stale, list_of_reasons).
        """
        if envelope.status in (CalculationStatus.FAILED, CalculationStatus.WITHHELD, CalculationStatus.INVALID):
            return False, []

        reasons: list[str] = []
        rules = MODEL_DEPENDENCY_RULES.get(envelope.model, {RevisionType.GEOMETRY})

        if RevisionType.GEOMETRY in rules and active_geometry_rev and envelope.geometry_revision_id:
            if envelope.geometry_revision_id != active_geometry_rev:
                reasons.append(
                    f"Geometry revision changed: calculation bound to '{envelope.geometry_revision_id}', active is '{active_geometry_rev}'"
                )

        if RevisionType.SURVEY in rules and active_survey_rev and envelope.survey_revision_id:
            if envelope.survey_revision_id != active_survey_rev:
                reasons.append(
                    f"Survey revision changed: calculation bound to '{envelope.survey_revision_id}', active is '{active_survey_rev}'"
                )

        if RevisionType.FORMATION in rules and active_formation_rev and envelope.formation_revision_id:
            if envelope.formation_revision_id != active_formation_rev:
                reasons.append(
                    f"Formation tops revision changed: bound to '{envelope.formation_revision_id}', active is '{active_formation_rev}'"
                )

        if RevisionType.MUD in rules and active_mud_rev and envelope.mud_revision_id:
            if envelope.mud_revision_id != active_mud_rev:
                reasons.append(
                    f"Mud programme revision changed: bound to '{envelope.mud_revision_id}', active is '{active_mud_rev}'"
                )

        if RevisionType.BHA in rules and active_bha_rev and envelope.bha_revision_id:
            if envelope.bha_revision_id != active_bha_rev:
                reasons.append(
                    f"BHA programme revision changed: bound to '{envelope.bha_revision_id}', active is '{active_bha_rev}'"
                )

        if RevisionType.CASING in rules and active_casing_rev and envelope.casing_revision_id:
            if envelope.casing_revision_id != active_casing_rev:
                reasons.append(
                    f"Casing programme revision changed: bound to '{envelope.casing_revision_id}', active is '{active_casing_rev}'"
                )

        if current_model_version and envelope.model_version != current_model_version:
            reasons.append(
                f"Model version updated: calculation used v{envelope.model_version}, current is v{current_model_version}"
            )

        return (len(reasons) > 0), reasons

    @staticmethod
    def identify_stale_models(changed_revisions: set[RevisionType]) -> set[str]:
        """Given a set of modified revision types, return all model keys that require recalculation."""
        stale_models: set[str] = set()
        for model_key, dependencies in MODEL_DEPENDENCY_RULES.items():
            if not dependencies.isdisjoint(changed_revisions):
                stale_models.add(model_key)
        return stale_models
