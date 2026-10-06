"""Domain exceptions and standard error codes for GeoDrill Pro v0.9."""
from typing import Any


class GeoDrillDomainError(Exception):
    """Base domain exception for GeoDrill Pro."""
    code: str = "DOMAIN_ERROR"

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class EntityNotFoundError(GeoDrillDomainError):
    code = "ENTITY_NOT_FOUND"


class StaleCalculationError(GeoDrillDomainError):
    code = "CALCULATION_STALE"


class CalculationWithheldError(GeoDrillDomainError):
    code = "CALCULATION_WITHHELD"


class CoordinateReferenceError(GeoDrillDomainError):
    code = "COORDINATE_REFERENCE_ERROR"


class UnitConversionError(GeoDrillDomainError):
    code = "UNIT_CONVERSION_ERROR"


class EngineeringEnvelopeViolation(GeoDrillDomainError):
    code = "ENGINEERING_ENVELOPE_VIOLATION"


class UnqualifiedModelError(GeoDrillDomainError):
    code = "MODEL_UNQUALIFIED"
