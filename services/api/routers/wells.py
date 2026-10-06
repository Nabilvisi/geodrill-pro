"""Wells, Fields, Wellbores, and Subsurface Targets API Router for GeoDrill Pro v0.9."""
from fastapi import APIRouter, Request, HTTPException, status
from pydantic import BaseModel, Field
from typing import Any, Literal
from packages.domain.models import SurfaceLocation, WellboreType, TargetGeometryType
from services.application.wells import WellService

router = APIRouter(prefix="/api/v1", tags=["Wells Hierarchy"])


class FieldCreateV1(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    basin: str = Field(default="", max_length=100)
    country: str = Field(default="", max_length=100)


class WellCreateV1(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    uwi: str = Field(default="", max_length=80)
    field_id: str | None = None
    surface_latitude_deg: float = 0.0
    surface_longitude_deg: float = 0.0
    surface_elevation_m: float = 0.0
    rkb_elevation_m: float = 0.0


class WellboreCreateV1(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    uwi: str = Field(default="", max_length=80)
    wellbore_type: Literal["original", "sidetrack", "bypass", "reentry"] = "original"
    sidetrack_parent_id: str | None = None
    kickoff_md_m: float = 0.0
    planned_td_m: float = 0.0


class TargetCreateV1(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    center_tvd_m: float = Field(ge=0.0)
    center_north_m: float = 0.0
    center_east_m: float = 0.0
    radius_m: float = Field(default=50.0, gt=0.0)
    geometry_type: Literal["circle", "rectangle", "polygon"] = "circle"
    tolerance_m: float = Field(default=10.0, ge=0.0)
    formation_id: str | None = None


# --- Project Tree ---
@router.get("/projects/{project_id}/tree")
def get_project_tree(request: Request, project_id: str) -> dict[str, Any]:
    svc = WellService(request.app.state.store)
    return svc.get_project_tree(project_id)


# --- Fields ---
@router.post("/projects/{project_id}/fields", status_code=status.HTTP_201_CREATED)
def create_field(request: Request, project_id: str, body: FieldCreateV1) -> dict[str, Any]:
    svc = WellService(request.app.state.store)
    return svc.create_field(project_id=project_id, name=body.name, basin=body.basin, country=body.country)


@router.get("/projects/{project_id}/fields")
def list_fields(request: Request, project_id: str) -> list[dict[str, Any]]:
    svc = WellService(request.app.state.store)
    return svc.list_fields(project_id)


# --- Wells ---
@router.post("/projects/{project_id}/wells", status_code=status.HTTP_201_CREATED)
def create_well(request: Request, project_id: str, body: WellCreateV1) -> dict[str, Any]:
    svc = WellService(request.app.state.store)
    loc = SurfaceLocation(
        latitude_deg=body.surface_latitude_deg,
        longitude_deg=body.surface_longitude_deg,
        ground_elevation_m=body.surface_elevation_m,
        rkb_elevation_m=body.rkb_elevation_m,
    )
    return svc.create_well(
        project_id=project_id,
        name=body.name,
        uwi=body.uwi,
        field_id=body.field_id,
        surface_location=loc,
    )


@router.get("/projects/{project_id}/wells")
def list_wells(request: Request, project_id: str) -> list[dict[str, Any]]:
    svc = WellService(request.app.state.store)
    return svc.list_wells(project_id)


@router.get("/wells/{well_id}")
def get_well(request: Request, well_id: str) -> dict[str, Any]:
    svc = WellService(request.app.state.store)
    return svc.get_well(well_id)


# --- Wellbores ---
@router.post("/wells/{well_id}/wellbores", status_code=status.HTTP_201_CREATED)
def create_wellbore(request: Request, well_id: str, body: WellboreCreateV1) -> dict[str, Any]:
    svc = WellService(request.app.state.store)
    wb_type = WellboreType(body.wellbore_type)
    return svc.create_wellbore(
        well_id=well_id,
        name=body.name,
        uwi=body.uwi,
        wellbore_type=wb_type,
        sidetrack_parent_id=body.sidetrack_parent_id,
        kickoff_md_m=body.kickoff_md_m,
        planned_td_m=body.planned_td_m,
    )


@router.get("/wells/{well_id}/wellbores")
def list_wellbores(request: Request, well_id: str) -> list[dict[str, Any]]:
    svc = WellService(request.app.state.store)
    return svc.list_wellbores(well_id)


@router.get("/wellbores/{wellbore_id}")
def get_wellbore(request: Request, wellbore_id: str) -> dict[str, Any]:
    svc = WellService(request.app.state.store)
    return svc.get_wellbore(wellbore_id)


# --- Targets ---
@router.post("/wellbores/{wellbore_id}/targets", status_code=status.HTTP_201_CREATED)
def create_target(request: Request, wellbore_id: str, body: TargetCreateV1) -> dict[str, Any]:
    svc = WellService(request.app.state.store)
    geom_type = TargetGeometryType(body.geometry_type)
    return svc.create_target(
        wellbore_id=wellbore_id,
        name=body.name,
        center_tvd_m=body.center_tvd_m,
        center_north_m=body.center_north_m,
        center_east_m=body.center_east_m,
        radius_m=body.radius_m,
        geometry_type=geom_type,
        tolerance_m=body.tolerance_m,
        formation_id=body.formation_id,
    )


@router.get("/wellbores/{wellbore_id}/targets")
def list_targets(request: Request, wellbore_id: str) -> list[dict[str, Any]]:
    svc = WellService(request.app.state.store)
    return svc.list_targets(wellbore_id)
