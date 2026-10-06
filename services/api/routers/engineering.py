"""Engineering Workspaces Router (Hydraulics, Torque & Drag, Casing, Geomechanics, MSE) for GeoDrill Pro v0.9."""
from fastapi import APIRouter, HTTPException, status
from typing import Any
from services.application.engineering_cases import EngineeringCaseService
from packages.engineering.physics import PressureInput, MSEInput
from packages.engineering.torque_drag import TorqueDragInput
from packages.engineering.geomechanics import GeomechanicsInput

router = APIRouter(prefix="/api/v1/wellbores/{wellbore_id}", tags=["Engineering Workspaces"])


@router.post("/hydraulics/pressure-balance")
def run_pressure_balance_case(wellbore_id: str, payload: PressureInput, geometry_revision_id: str | None = None):
    try:
        envelope = EngineeringCaseService.run_pressure_balance_case(payload, geometry_revision_id=geometry_revision_id)
        return envelope.model_dump()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/performance/mse")
def run_mse_case(wellbore_id: str, payload: MSEInput, bha_revision_id: str | None = None):
    try:
        envelope = EngineeringCaseService.run_mse_case(payload, bha_revision_id=bha_revision_id)
        return envelope.model_dump()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/torque-drag/cases")
def run_torque_drag_case(wellbore_id: str, payload: TorqueDragInput, geometry_revision_id: str | None = None):
    try:
        envelope = EngineeringCaseService.run_torque_drag_case(payload, geometry_revision_id=geometry_revision_id)
        return envelope.model_dump()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/geomechanics/cases")
def run_geomechanics_case(wellbore_id: str, payload: GeomechanicsInput, geometry_revision_id: str | None = None):
    try:
        envelope = EngineeringCaseService.run_geomechanics_case(payload, geometry_revision_id=geometry_revision_id)
        return envelope.model_dump()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
