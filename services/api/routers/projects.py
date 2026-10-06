"""Projects API Router for GeoDrill Pro v0.9."""
from fastapi import APIRouter, Request, HTTPException, status
from pydantic import BaseModel, Field
from typing import Any, Literal
from packages.domain.models import Project, CoordinateReference
from services.application.projects import ProjectService


router = APIRouter(prefix="/api/v1/projects", tags=["Projects"])


class ProjectCreateV1(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    datum: str = Field(default="WGS84", min_length=1, max_length=100)
    well_name: str = Field(default="Well-01", min_length=1, max_length=100)
    default_crs: str = Field(default="EPSG:4326")
    north_reference: Literal["true", "grid", "magnetic"] = "true"
    owner: str = Field(default="engineer")


@router.get("", response_model=list[dict[str, Any]])
def list_projects(request: Request):
    svc = ProjectService(request.app.state.store)
    return svc.list_projects()


@router.post("", status_code=status.HTTP_201_CREATED)
def create_project(request: Request, body: ProjectCreateV1):
    svc = ProjectService(request.app.state.store)
    proj = svc.create_project(
        name=body.name,
        datum=body.datum,
        well_name=body.well_name,
        default_crs=body.default_crs,
        north_reference=body.north_reference,
        owner=body.owner,
    )
    return proj


@router.get("/{project_id}")
def get_project(request: Request, project_id: str):
    svc = ProjectService(request.app.state.store)
    try:
        return svc.get_project(project_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
