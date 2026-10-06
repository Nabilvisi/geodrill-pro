"""Application service for Fields, Wells, Wellbores, and Subsurface Targets hierarchy."""
from typing import Any
from uuid import uuid4
import json
from packages.domain.models import (
    FieldModel,
    Well,
    SurfaceLocation,
    Wellbore,
    WellboreType,
    Target,
    TargetGeometryType,
    utc_now_iso,
)
from packages.domain.errors import EntityNotFoundError
from services.api.storage import Store, canonical, now


class WellService:
    def __init__(self, store: Store):
        self.store = store

    # --- Fields ---
    def create_field(self, project_id: str, name: str, basin: str = "", country: str = "") -> dict[str, Any]:
        self.store.project(project_id)
        field_id = str(uuid4())
        field = FieldModel(id=field_id, project_id=project_id, name=name, basin=basin, country=country)
        created_at = utc_now_iso()
        with self.store.connect() as db:
            db.execute(
                "INSERT INTO fields(id, project_id, name, payload, created_at) VALUES(?, ?, ?, ?, ?)",
                (field.id, field.project_id, field.name, canonical(field.model_dump()), created_at),
            )
            self.store.audit(db, "field.created", project_id, {"field_id": field.id, "name": name})
        return field.model_dump()

    def list_fields(self, project_id: str) -> list[dict[str, Any]]:
        with self.store.connect() as db:
            rows = db.execute("SELECT * FROM fields WHERE project_id = ? ORDER BY created_at ASC", (project_id,)).fetchall()
            return [json.loads(r["payload"]) for r in rows]

    # --- Wells ---
    def create_well(
        self,
        project_id: str,
        name: str,
        uwi: str = "",
        field_id: str | None = None,
        surface_location: SurfaceLocation | None = None,
    ) -> dict[str, Any]:
        self.store.project(project_id)
        well_id = str(uuid4())
        loc = surface_location or SurfaceLocation()
        well = Well(
            id=well_id,
            project_id=project_id,
            field_id=field_id,
            name=name,
            uwi=uwi or f"WELL-{well_id[:8].upper()}",
            surface_location=loc,
            created_at=utc_now_iso(),
        )
        with self.store.connect() as db:
            db.execute(
                "INSERT INTO wells(id, project_id, field_id, name, uwi, payload, created_at) VALUES(?, ?, ?, ?, ?, ?, ?)",
                (well.id, well.project_id, well.field_id, well.name, well.uwi, canonical(well.model_dump()), well.created_at),
            )
            self.store.audit(db, "well.created", project_id, {"well_id": well.id, "name": name, "uwi": well.uwi})
        return well.model_dump()

    def get_well(self, well_id: str) -> dict[str, Any]:
        with self.store.connect() as db:
            row = db.execute("SELECT * FROM wells WHERE id = ?", (well_id,)).fetchone()
            if not row:
                raise EntityNotFoundError(f"Well '{well_id}' not found", {"well_id": well_id})
            return json.loads(row["payload"])

    def list_wells(self, project_id: str) -> list[dict[str, Any]]:
        with self.store.connect() as db:
            rows = db.execute("SELECT * FROM wells WHERE project_id = ? ORDER BY created_at ASC", (project_id,)).fetchall()
            return [json.loads(r["payload"]) for r in rows]

    # --- Wellbores ---
    def create_wellbore(
        self,
        well_id: str,
        name: str,
        uwi: str = "",
        wellbore_type: WellboreType = WellboreType.ORIGINAL,
        sidetrack_parent_id: str | None = None,
        kickoff_md_m: float = 0.0,
        planned_td_m: float = 0.0,
    ) -> dict[str, Any]:
        well = self.get_well(well_id)
        wellbore_id = str(uuid4())
        wellbore = Wellbore(
            id=wellbore_id,
            well_id=well_id,
            name=name,
            uwi=uwi or f"{well.get('uwi', '')}-WB{wellbore_id[:4].upper()}",
            wellbore_type=wellbore_type,
            sidetrack_parent_id=sidetrack_parent_id,
            kickoff_md_m=kickoff_md_m,
            planned_td_m=planned_td_m,
            created_at=utc_now_iso(),
        )
        with self.store.connect() as db:
            db.execute(
                "INSERT INTO wellbores(id, well_id, name, uwi, sidetrack_parent_id, wellbore_type, payload, created_at) VALUES(?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    wellbore.id,
                    wellbore.well_id,
                    wellbore.name,
                    wellbore.uwi,
                    wellbore.sidetrack_parent_id,
                    wellbore.wellbore_type.value,
                    canonical(wellbore.model_dump()),
                    wellbore.created_at,
                ),
            )
            self.store.audit(db, "wellbore.created", well["project_id"], {"wellbore_id": wellbore.id, "name": name})
        return wellbore.model_dump()

    def get_wellbore(self, wellbore_id: str) -> dict[str, Any]:
        with self.store.connect() as db:
            row = db.execute("SELECT * FROM wellbores WHERE id = ?", (wellbore_id,)).fetchone()
            if not row:
                raise EntityNotFoundError(f"Wellbore '{wellbore_id}' not found", {"wellbore_id": wellbore_id})
            return json.loads(row["payload"])

    def list_wellbores(self, well_id: str) -> list[dict[str, Any]]:
        with self.store.connect() as db:
            rows = db.execute("SELECT * FROM wellbores WHERE well_id = ? ORDER BY created_at ASC", (well_id,)).fetchall()
            return [json.loads(r["payload"]) for r in rows]

    # --- Targets ---
    def create_target(
        self,
        wellbore_id: str,
        name: str,
        center_tvd_m: float,
        center_north_m: float = 0.0,
        center_east_m: float = 0.0,
        radius_m: float = 50.0,
        geometry_type: TargetGeometryType = TargetGeometryType.CIRCLE,
        tolerance_m: float = 10.0,
        formation_id: str | None = None,
    ) -> dict[str, Any]:
        wb = self.get_wellbore(wellbore_id)
        well = self.get_well(wb["well_id"])
        target_id = str(uuid4())
        target = Target(
            id=target_id,
            wellbore_id=wellbore_id,
            name=name,
            geometry_type=geometry_type,
            center_tvd_m=center_tvd_m,
            center_north_m=center_north_m,
            center_east_m=center_east_m,
            radius_m=radius_m,
            tolerance_m=tolerance_m,
            formation_id=formation_id,
        )
        with self.store.connect() as db:
            db.execute(
                "INSERT INTO targets(id, wellbore_id, name, geometry_type, payload, created_at) VALUES(?, ?, ?, ?, ?, ?)",
                (target.id, target.wellbore_id, target.name, target.geometry_type.value, canonical(target.model_dump()), utc_now_iso()),
            )
            self.store.audit(db, "target.created", well["project_id"], {"target_id": target.id, "name": name})
        return target.model_dump()

    def list_targets(self, wellbore_id: str) -> list[dict[str, Any]]:
        with self.store.connect() as db:
            rows = db.execute("SELECT * FROM targets WHERE wellbore_id = ? ORDER BY created_at ASC", (wellbore_id,)).fetchall()
            return [json.loads(r["payload"]) for r in rows]

    # --- Complete Project Tree Hierarchy ---
    def get_project_tree(self, project_id: str) -> dict[str, Any]:
        project = self.store.project(project_id)
        fields = self.list_fields(project_id)
        wells = self.list_wells(project_id)

        # Build nested tree
        wells_by_field: dict[str | None, list[dict[str, Any]]] = {}
        for w in wells:
            w_copy = dict(w)
            w_copy["wellbores"] = []
            wellbores = self.list_wellbores(w["id"])
            for wb in wellbores:
                wb_copy = dict(wb)
                wb_copy["targets"] = self.list_targets(wb["id"])
                w_copy["wellbores"].append(wb_copy)
            f_id = w.get("field_id")
            wells_by_field.setdefault(f_id, []).append(w_copy)

        tree_fields = []
        for f in fields:
            f_copy = dict(f)
            f_copy["wells"] = wells_by_field.get(f["id"], [])
            tree_fields.append(f_copy)

        # Unassigned wells
        unassigned_wells = wells_by_field.get(None, [])

        return {
            "project": project,
            "fields": tree_fields,
            "unassigned_wells": unassigned_wells,
        }
