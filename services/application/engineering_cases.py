"""Application service for running engineering cases wrapped in standard calculation envelopes."""
from typing import Any
from uuid import uuid4
from packages.domain.calculation import (
    CalculationEnvelope,
    CalculationStatus,
    QualificationLevel,
    ModelClass,
    compute_inputs_hash,
    utc_now_iso,
)
from packages.domain.staleness import StalenessEvaluator
from packages.engineering.physics import MSEInput, mse, PressureInput, pressure
from packages.engineering.hydraulics import HydraulicsInput, hydraulics
from packages.engineering.torque_drag import TorqueDragInput, torque_drag
from packages.engineering.buckling import BucklingInput, buckling
from packages.engineering.casing import CasingCheckInput, casing_check, CasingEnvelopesInput, casing_envelopes
from packages.engineering.geomechanics import GeomechanicsInput, calculate_geomechanics
from packages.engineering.geometry import GeometryInput, Path as SurveyPath
from packages.engineering.models import SurveyRequest


class EngineeringCaseService:
    @staticmethod
    def run_saved_research_case(run_case, project_id, payload, model, kernel) -> CalculationEnvelope:
        """Wrap the preserved revision-bound calculation and immutable evidence record."""
        record = run_case(project_id, payload, model, kernel)
        result = record["result"]
        withheld = result.get("status") in {"withheld", "invalid", "nonconverged"}
        return CalculationEnvelope(
            calculation_id=record["id"], model=model,
            model_version=result.get("model_version", "undeclared"),
            model_class=ModelClass.DETERMINISTIC_RESEARCH,
            qualification=QualificationLevel.INTERNAL_VERIFICATION,
            status=CalculationStatus.WITHHELD if withheld else CalculationStatus.CALCULATED,
            inputs_hash=compute_inputs_hash(record["inputs_si"]),
            geometry_revision_id=payload.geometry_revision_id,
            result=result, warnings=result.get("reasons", []),
            limitations=result.get("limitations", []),
            evidence_ids=[result[k] for k in ("geometry_sha256", "survey_source_sha256", "input_document_sha256") if result.get(k)],
            created_at=record["created_at"],
        )

    @staticmethod
    def run_pressure_balance_case(
        payload: PressureInput,
        geometry_revision_id: str | None = None,
    ) -> CalculationEnvelope:
        """Run deterministic hydrostatic and ECD pressure balance calculation."""
        raw_result = pressure(payload)
        return CalculationEnvelope(
            calculation_id=str(uuid4()),
            model="hydraulics.pressure_balance",
            model_version=raw_result["version"],
            model_class=ModelClass.DETERMINISTIC_VERIFIED,
            qualification=QualificationLevel.INTERNAL_VERIFICATION,
            status=CalculationStatus.CALCULATED,
            inputs_hash=compute_inputs_hash(payload.model_dump()),
            geometry_revision_id=geometry_revision_id,
            result=raw_result,
            assumptions=["Steady-state hydrostatic gradient plus declared annular friction loss"],
            limitations=["Single-phase incompressible fluid column; constant surface gauge reference"],
            created_at=utc_now_iso(),
        )

    @staticmethod
    def run_mse_case(
        payload: MSEInput,
        bha_revision_id: str | None = None,
    ) -> CalculationEnvelope:
        """Run Mechanical Specific Energy calculation."""
        raw_result = mse(payload)
        status = CalculationStatus.WITHHELD if raw_result.get("status") == "withheld" else CalculationStatus.CALCULATED
        return CalculationEnvelope(
            calculation_id=str(uuid4()),
            model="performance.mse",
            model_version=raw_result["version"],
            model_class=ModelClass.DETERMINISTIC_VERIFIED,
            qualification=QualificationLevel.INTERNAL_VERIFICATION,
            status=status,
            inputs_hash=compute_inputs_hash(payload.model_dump()),
            bha_revision_id=bha_revision_id,
            result=raw_result if status != CalculationStatus.WITHHELD else {},
            assumptions=["Teale energy balance equation"],
            warnings=[f"WITHHELD: {raw_result.get('reason')}"] if status == CalculationStatus.WITHHELD else [],
            limitations=["Requires confirmed drilling state and ROP above numerical threshold"],
            created_at=utc_now_iso(),
        )

    @staticmethod
    def run_bound_hydraulics_case(
        store: Any,
        project_id: str,
        value: HydraulicsInput,
    ) -> CalculationEnvelope:
        """Run full geometry-linked steady laminar hydraulics calculation."""
        project = store.project(project_id)
        revision = store.revision(project_id, value.geometry_revision_id)
        if revision["module"] != "M1" or value.depth_datum != project["datum"]:
            raise ValueError("Hydraulics requires a geometry revision with the project datum.")
        geometry = GeometryInput.model_validate(revision["input"])
        source = store.dataset(project_id, geometry.survey_dataset_id)
        path = SurveyPath(SurveyRequest(stations=[{k: r[k] for k in ("md_m", "inclination_rad", "azimuth_rad")} for r in source["rows"]]))
        result = hydraulics(value, geometry, path)
        return CalculationEnvelope(
            calculation_id=str(uuid4()),
            model="hydraulics.pressure_profile",
            model_version="0.9.0",
            model_class=ModelClass.DETERMINISTIC_VERIFIED,
            qualification=QualificationLevel.INTERNAL_VERIFICATION,
            status=CalculationStatus.CALCULATED,
            inputs_hash=compute_inputs_hash(value.model_dump()),
            geometry_revision_id=value.geometry_revision_id,
            result=result,
            assumptions=["Steady state single-phase annular flow", "Herschel-Bulkley / Bingham Plastic rheology"],
            limitations=["No multiphase gas influx or cuttings bed accumulation dynamics modeled in steady state"],
            created_at=utc_now_iso(),
        )

    @staticmethod
    def run_torque_drag_case(
        payload: TorqueDragInput,
        geometry_revision_id: str | None = None,
        geometry: GeometryInput | None = None,
        path: SurveyPath | None = None,
    ) -> CalculationEnvelope:
        """Run torque & drag analysis wrapped in calculation envelope."""
        if geometry is None or path is None:
            raise ValueError("Torque/drag requires immutable project geometry and accepted survey context.")
        result = torque_drag(payload, geometry, path)
        return CalculationEnvelope(
            calculation_id=str(uuid4()),
            model="torque_drag.soft_string",
            model_version="0.9.0",
            model_class=ModelClass.DETERMINISTIC_VERIFIED,
            qualification=QualificationLevel.INTERNAL_VERIFICATION,
            status=CalculationStatus.CALCULATED,
            inputs_hash=compute_inputs_hash(payload.model_dump()),
            geometry_revision_id=geometry_revision_id,
            result=result,
            assumptions=["Soft string formulation; constant friction factor along intervals"],
            limitations=["Does not compute tubular bending stiffness effects"],
            created_at=utc_now_iso(),
        )

    @staticmethod
    def run_geomechanics_case(
        payload: GeomechanicsInput,
        geometry_revision_id: str | None = None,
        formation_revision_id: str | None = None,
    ) -> CalculationEnvelope:
        """Run geomechanics and wellbore stability calculations."""
        result = calculate_geomechanics(payload)
        is_withheld = result.get("status") == "withheld"
        status = CalculationStatus.WITHHELD if is_withheld else CalculationStatus.CALCULATED
        return CalculationEnvelope(
            calculation_id=str(uuid4()),
            model="geomechanics.wellbore_stability",
            model_version="0.9.0",
            model_class=ModelClass.DETERMINISTIC_RESEARCH,
            qualification=QualificationLevel.INTERNAL_VERIFICATION,
            status=status,
            inputs_hash=compute_inputs_hash(payload.model_dump()),
            geometry_revision_id=geometry_revision_id,
            formation_revision_id=formation_revision_id,
            result=result if not is_withheld else {},
            assumptions=["Kirsch solution for borehole stresses; linear poroelastic rock behavior"],
            warnings=[f"WITHHELD: {result.get('withholding_reason')}"] if is_withheld else [],
            limitations=["Requires valid LOT/FIT calibration to be qualified for field operations"],
            created_at=utc_now_iso(),
        )

    @staticmethod
    def evaluate_envelope_staleness(
        envelope: CalculationEnvelope,
        active_geometry_rev: str | None = None,
        active_survey_rev: str | None = None,
        active_formation_rev: str | None = None,
        active_mud_rev: str | None = None,
        active_bha_rev: str | None = None,
        active_casing_rev: str | None = None,
    ) -> CalculationEnvelope:
        """Check if an existing calculation is stale and return updated envelope."""
        is_stale, reasons = StalenessEvaluator.is_calculation_stale(
            envelope=envelope,
            active_geometry_rev=active_geometry_rev,
            active_survey_rev=active_survey_rev,
            active_formation_rev=active_formation_rev,
            active_mud_rev=active_mud_rev,
            active_bha_rev=active_bha_rev,
            active_casing_rev=active_casing_rev,
        )
        if is_stale:
            return envelope.mark_stale("; ".join(reasons))
        return envelope
