"""Calculation envelope and qualification contracts for GeoDrill Pro v0.9."""
from enum import Enum
from typing import Any
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime, timezone
import hashlib
import json
from packages.version import APP_VERSION


class CalculationStatus(str, Enum):
    CALCULATED = "calculated"
    WITHHELD = "withheld"
    INVALID = "invalid"
    FAILED = "failed"
    STALE = "stale"
    SUPERSEDED = "superseded"
    NOT_APPLICABLE = "not_applicable"


class QualificationLevel(str, Enum):
    RESEARCH = "research"
    INTERNAL_VERIFICATION = "internal_verification"
    PUBLISHED_BENCHMARK = "published_benchmark"
    INDEPENDENT_QUALIFIED = "independent_qualified"


class ModelClass(str, Enum):
    DETERMINISTIC_VERIFIED = "deterministic_verified"
    DETERMINISTIC_RESEARCH = "deterministic_research"
    STATISTICAL_ML = "statistical_ml"
    OPERATIONAL_DECISION_SUPPORT = "operational_decision_support"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def compute_inputs_hash(inputs: dict[str, Any] | str | bytes) -> str:
    if isinstance(inputs, bytes):
        return hashlib.sha256(inputs).hexdigest()
    if isinstance(inputs, str):
        return hashlib.sha256(inputs.encode("utf-8")).hexdigest()
    canonical_json = json.dumps(inputs, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


class CalculationEnvelope(BaseModel):
    """Standard envelope for all GeoDrill Pro engineering calculations."""
    model_config = ConfigDict(extra="forbid", strict=False)

    calculation_id: str = Field(description="Unique UUID or identifier of calculation run")
    model: str = Field(description="Model identifier, e.g. hydraulics.hb_annular_pressure_loss")
    model_version: str = Field(default="0.9.0", description="Semantic version of the engineering model")
    model_class: ModelClass = Field(default=ModelClass.DETERMINISTIC_VERIFIED, description="Model category")
    qualification: QualificationLevel = Field(default=QualificationLevel.INTERNAL_VERIFICATION, description="Qualification status")
    status: CalculationStatus = Field(default=CalculationStatus.CALCULATED, description="Execution status")
    inputs_hash: str = Field(description="SHA-256 digest of canonical SI inputs")

    # Dependency binding revisions
    geometry_revision_id: str | None = Field(default=None, description="Bound trajectory/geometry revision")
    survey_revision_id: str | None = Field(default=None, description="Bound survey revision")
    formation_revision_id: str | None = Field(default=None, description="Bound formation tops revision")
    mud_revision_id: str | None = Field(default=None, description="Bound mud programme revision")
    bha_revision_id: str | None = Field(default=None, description="Bound BHA programme revision")
    casing_revision_id: str | None = Field(default=None, description="Bound casing programme revision")

    result: dict[str, Any] = Field(default_factory=dict, description="Output payload in canonical SI")
    assumptions: list[str] = Field(default_factory=list, description="Explicit modeling assumptions")
    warnings: list[str] = Field(default_factory=list, description="Non-fatal warnings or condition advisories")
    limitations: list[str] = Field(default_factory=list, description="Declared physical or domain boundaries")
    evidence_ids: list[str] = Field(default_factory=list, description="Referenced evidence or source hashes")

    created_at: str = Field(default_factory=utc_now_iso, description="ISO-8601 UTC timestamp")
    software_revision: str = Field(default=APP_VERSION, description="GeoDrill Pro software version")

    def mark_stale(self, reason: str) -> "CalculationEnvelope":
        """Return a copy marked as stale due to upstream dependency invalidation."""
        dumped = self.model_dump()
        dumped["status"] = CalculationStatus.STALE
        dumped["warnings"] = list(dumped.get("warnings", [])) + [f"STALE: {reason}"]
        return CalculationEnvelope.model_validate(dumped)

    def mark_withheld(self, reason: str) -> "CalculationEnvelope":
        """Return a copy marked as withheld due to unmet validation or out-of-envelope inputs."""
        dumped = self.model_dump()
        dumped["status"] = CalculationStatus.WITHHELD
        dumped["warnings"] = list(dumped.get("warnings", [])) + [f"WITHHELD: {reason}"]
        dumped["result"] = {}
        return CalculationEnvelope.model_validate(dumped)
