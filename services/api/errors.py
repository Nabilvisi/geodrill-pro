"""Standardized error responses and exceptions for GeoDrill Pro v0.9 API."""
from typing import Any
from uuid import uuid4
from fastapi import Request
from fastapi.responses import JSONResponse
from packages.domain.errors import GeoDrillDomainError


class APIError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}


def format_error_response(code: str, message: str, status_code: int, details: dict[str, Any] | None = None, correlation_id: str | None = None) -> JSONResponse:
    cid = correlation_id or str(uuid4())
    payload = {
        # Backward compatibility with existing tests expecting "detail" string
        "detail": message,
        # Standard v0.9 structured error format
        "error": {
            "code": code,
            "message": message,
            "details": details or {},
            "correlation_id": cid,
        },
    }
    return JSONResponse(payload, status_code=status_code)


async def domain_error_handler(request: Request, exc: GeoDrillDomainError) -> JSONResponse:
    status_code = 400
    if exc.code == "ENTITY_NOT_FOUND":
        status_code = 404
    elif exc.code == "CALCULATION_WITHHELD":
        status_code = 422
    return format_error_response(
        code=exc.code,
        message=exc.message,
        status_code=status_code,
        details=exc.details,
    )


async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
    return format_error_response(
        code=exc.code,
        message=exc.message,
        status_code=exc.status_code,
        details=exc.details,
    )
