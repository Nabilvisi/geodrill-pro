"""Engineering Workspaces Router (Hydraulics, Torque & Drag, Casing, Geomechanics, MSE) for GeoDrill Pro v0.9."""
from fastapi import APIRouter, HTTPException, Request, status
from typing import Any
from services.application.engineering_cases import EngineeringCaseService
from packages.engineering.physics import PressureInput, MSEInput
from packages.engineering.torque_drag import TorqueDragInput
from packages.engineering.geomechanics import GeomechanicsInput
from packages.engineering.geomechanics import calculate_geomechanics
from packages.engineering.torque_drag import torque_drag
from services.application.wells import WellService

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
def run_torque_drag_case(request: Request, wellbore_id: str, payload: TorqueDragInput, geometry_revision_id: str | None = None):
    try:
        if geometry_revision_id is not None and geometry_revision_id != payload.geometry_revision_id:
            raise ValueError("Query and input geometry revisions must match.")
        svc = WellService(request.app.state.store)
        well = svc.get_well(svc.get_wellbore(wellbore_id)["well_id"])
        geometry=request.app.state.store.revision(well['project_id'],payload.geometry_revision_id)
        if geometry.get('wellbore_id') not in (None,wellbore_id):
            raise ValueError('Geometry belongs to another wellbore.')
        envelope = EngineeringCaseService.run_saved_research_case(request.app.state.run_project_research_case, well["project_id"], payload, "torque-drag", torque_drag)
        return envelope.model_dump()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/geomechanics/cases")
def run_geomechanics_case(request: Request, wellbore_id: str, payload: GeomechanicsInput, geometry_revision_id: str | None = None):
    try:
        if geometry_revision_id is not None and geometry_revision_id != payload.geometry_revision_id:
            raise ValueError("Query and input geometry revisions must match.")
        svc = WellService(request.app.state.store)
        well = svc.get_well(svc.get_wellbore(wellbore_id)["well_id"])
        geometry=request.app.state.store.revision(well['project_id'],payload.geometry_revision_id)
        if geometry.get('wellbore_id') not in (None,wellbore_id):
            raise ValueError('Geometry belongs to another wellbore.')
        envelope = EngineeringCaseService.run_saved_research_case(request.app.state.run_project_research_case, well["project_id"], payload, "geomechanics", calculate_geomechanics)
        return envelope.model_dump()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
