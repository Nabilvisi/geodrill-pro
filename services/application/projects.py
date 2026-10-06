"""Application service for Project and Coordinate Reference management."""
from typing import Any
from packages.domain.models import Project, CoordinateReference, UnitProfile, utc_now_iso
from packages.domain.errors import EntityNotFoundError
from services.api.storage import Store


class ProjectService:
    def __init__(self, store: Store):
        self.store = store

    def list_projects(self) -> list[dict[str, Any]]:
        return self.store.projects()

    def get_project(self, project_id: str) -> dict[str, Any]:
        try:
            return self.store.project(project_id)
        except KeyError as e:
            raise EntityNotFoundError(f"Project '{project_id}' not found", {"project_id": project_id}) from e

    def create_project(
        self,
        name: str,
        datum: str = "WGS84",
        well_name: str = "Well-01",
        default_crs: str = "EPSG:4326",
        north_reference: str = "true",
        owner: str = "engineer",
        bit_diameter_m: float = 0.2159,
        origin: str = "historical",
    ) -> dict[str, Any]:
        payload = {
            "name": name,
            "well_name": well_name,
            "datum": datum,
            "default_crs": default_crs,
            "north_reference": north_reference,
            "owner": owner,
            "bit_diameter_m": bit_diameter_m,
            "origin": origin,
        }
        return self.store.create_project(payload)
