"""Directional well planning, surveys, uncertainty, and anticollision router for GeoDrill Pro v0.9."""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Any
from packages.domain.models import SurveyStation, TrajectoryType
from packages.domain.calculation import CalculationEnvelope
from services.application.directional import DirectionalService
from packages.engineering.directional import (
    convert_geodetic_to_projected,
    convert_projected_to_geodetic,
    SurveyUncertaintyInput,
    ProximityInput,
)

router = APIRouter(prefix="/api/v1", tags=["Directional & Anti-Collision"])


class TrajectoryCalcRequest(BaseModel):
    wellbore_id: str
    stations: list[SurveyStation] = Field(min_length=2, max_length=10000)
    survey_revision_id: str | None = None
    trajectory_type: TrajectoryType = TrajectoryType.PLANNED


@router.post("/wellbores/{wellbore_id}/directional/calculate")
def calculate_trajectory(wellbore_id: str, body: TrajectoryCalcRequest):
    if body.wellbore_id != wellbore_id:
        raise HTTPException(status_code=422, detail="Path and body wellbore IDs must match.")
    try:
        stations = body.stations
        traj, envelope = DirectionalService.calculate_minimum_curvature_trajectory(
            stations=stations,
            wellbore_id=wellbore_id,
            survey_revision_id=body.survey_revision_id,
            trajectory_type=body.trajectory_type,
        )
        return {
            "trajectory": traj.model_dump(),
            "envelope": envelope.model_dump(),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/wellbores/{wellbore_id}/surveys/uncertainty")
def calculate_uncertainty(wellbore_id: str, payload: dict[str, Any]):
    try:
        envelope = DirectionalService.calculate_uncertainty(payload)  # type: ignore
        return envelope.model_dump()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/wellbores/{wellbore_id}/anticollision/proximity")
def calculate_anticollision(wellbore_id: str, payload: dict[str, Any]):
    try:
        envelope = DirectionalService.calculate_anticollision(payload)  # type: ignore
        return envelope.model_dump()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/geodesy/convert")
def convert_coordinates(payload: dict[str, Any]):
    if not payload.get("crs_code") or not payload.get("datum"):
        raise HTTPException(status_code=422, detail="Explicit CRS and datum are required.")
    try:
        if "latitude_deg" in payload and "longitude_deg" in payload:
            return convert_geodetic_to_projected(
                lat_deg=float(payload["latitude_deg"]),
                lon_deg=float(payload["longitude_deg"]),
                crs_code=str(payload.get("crs_code", "EPSG:32631")),
                datum=str(payload.get("datum", "WGS84")),
            )
        return convert_projected_to_geodetic(
            easting_m=float(payload["easting_m"]),
            northing_m=float(payload["northing_m"]),
            crs_code=str(payload.get("crs_code", "EPSG:32631")),
            datum=str(payload.get("datum", "WGS84")),
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
