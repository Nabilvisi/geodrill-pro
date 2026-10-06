"""Core Domain Models for GeoDrill Pro v0.9 Drilling Engineering Workstation."""
import math
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class DomainContract(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        allow_inf_nan=False,
        strict=False,
        str_strip_whitespace=True,
    )


class CoordinateReference(DomainContract):
    """Coordinate reference system definition."""
    crs_id: str = Field(default="EPSG:4326", description="EPSG code or CRS identifier")
    datum: str = Field(default="WGS84", description="Geodetic datum name")
    projection: str = Field(default="Geographic", description="Map projection name")
    north_reference: Literal["true", "grid", "magnetic"] = "true"
    grid_convergence_rad: float = Field(default=0.0, description="Grid convergence angle in radians")
    elevation_datum: str = Field(default="MSL", description="Vertical elevation reference datum")


class UnitProfile(DomainContract):
    """Unit display profile configuration (all computations remain canonical SI)."""
    name: str = Field(default="Metric SI", description="Profile name")
    depth_unit: Literal["m", "ft"] = "m"
    pressure_unit: Literal["Pa", "kPa", "MPa", "bar", "psi"] = "Pa"
    density_unit: Literal["kg/m3", "sg", "ppg"] = "kg/m3"
    force_unit: Literal["N", "kN", "lbf", "klbf"] = "N"
    torque_unit: Literal["N.m", "kN.m", "ft.lbf", "kft.lbf"] = "N.m"
    flow_unit: Literal["m3/s", "L/min", "gpm", "bpm"] = "m3/s"
    temperature_unit: Literal["C", "F", "K"] = "C"


class Project(DomainContract):
    """Root drilling engineering project."""
    id: str = Field(description="Unique project UUID")
    name: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=1000)
    owner: str = Field(default="engineer", max_length=80)
    organization_id: str = Field(default="default-org", max_length=80)
    coordinate_reference: CoordinateReference = Field(default_factory=CoordinateReference)
    unit_profile: UnitProfile = Field(default_factory=UnitProfile)
    status: Literal["active", "archived", "planning", "completed"] = "active"
    created_at: str = Field(default_factory=utc_now_iso)
    updated_at: str = Field(default_factory=utc_now_iso)


class FieldModel(DomainContract):
    """Field asset entity within a project."""
    id: str
    project_id: str
    name: str = Field(min_length=1, max_length=100)
    basin: str = Field(default="", max_length=100)
    country: str = Field(default="", max_length=100)


class SurfaceLocation(DomainContract):
    """Geodetic and projected surface location of a well."""
    latitude_deg: float = Field(default=0.0, ge=-90.0, le=90.0)
    longitude_deg: float = Field(default=0.0, ge=-180.0, le=180.0)
    easting_m: float = Field(default=0.0)
    northing_m: float = Field(default=0.0)
    ground_elevation_m: float = Field(default=0.0)
    rkb_elevation_m: float = Field(default=0.0, description="Rotary Kelly Bushing elevation above datum")


class Well(DomainContract):
    """Well entity representing a physical well site."""
    id: str
    project_id: str
    field_id: str | None = None
    name: str = Field(min_length=1, max_length=100)
    uwi: str = Field(default="", description="Unique Well Identifier")
    surface_location: SurfaceLocation = Field(default_factory=SurfaceLocation)
    spud_date: str | None = None
    status: Literal["planned", "drilling", "suspended", "completed", "abandoned"] = "planned"
    created_at: str = Field(default_factory=utc_now_iso)


class WellboreType(str, Enum):
    ORIGINAL = "original"
    SIDETRACK = "sidetrack"
    BYPASS = "bypass"
    REENTRY = "reentry"


class Wellbore(DomainContract):
    """Wellbore entity representing a drilled or planned hole."""
    id: str
    well_id: str
    name: str = Field(min_length=1, max_length=100)
    uwi: str = Field(default="")
    wellbore_type: WellboreType = WellboreType.ORIGINAL
    sidetrack_parent_id: str | None = None
    kickoff_md_m: float = Field(default=0.0, ge=0.0)
    planned_td_m: float = Field(default=0.0, ge=0.0)
    status: Literal["planning", "active", "completed"] = "planning"
    created_at: str = Field(default_factory=utc_now_iso)


class TrajectoryType(str, Enum):
    PLANNED = "planned"
    ACTUAL = "actual"
    SCENARIO = "scenario"


class SurveyStation(DomainContract):
    """Directional survey station in canonical SI."""
    md_m: float = Field(ge=0.0, le=30000.0, description="Measured depth in meters")
    inc_rad: float = Field(ge=0.0, le=math.pi, description="Inclination in radians")
    azi_rad: float = Field(ge=0.0, lt=2 * math.pi, description="Azimuth in radians")
    tvd_m: float = Field(default=0.0, ge=0.0, description="True vertical depth in meters")
    north_m: float = Field(default=0.0, description="Northing displacement in meters")
    east_m: float = Field(default=0.0, description="Easting displacement in meters")
    dls_rad_m: float = Field(default=0.0, ge=0.0, description="Dogleg severity in rad/m")
    tool_code: str = Field(default="MWD", description="Survey tool code")
    quality: Literal["valid", "questionable", "rejected"] = "valid"
    source_row: int | None = None


class SurveyRevision(DomainContract):
    """Immutable survey program revision containing station observations."""
    id: str
    wellbore_id: str
    revision: int = Field(ge=1)
    stations: list[SurveyStation] = Field(min_length=1)
    north_reference: Literal["true", "grid", "magnetic"] = "true"
    tool_model: str = Field(default="MWD+SAG")
    is_accepted: bool = Field(default=False)
    created_by: str = "engineer"
    created_at: str = Field(default_factory=utc_now_iso)

    @model_validator(mode="after")
    def validate_stations_order(self):
        if len(self.stations) > 1:
            for s1, s2 in zip(self.stations[:-1], self.stations[1:]):
                if s2.md_m <= s1.md_m:
                    raise ValueError(f"Survey measured depths must be strictly increasing: {s1.md_m} >= {s2.md_m}")
        return self


class TrajectoryRevision(DomainContract):
    """Calculated trajectory revision combining plan or actual surveys with geometry calculations."""
    id: str
    wellbore_id: str
    revision: int = Field(ge=1)
    trajectory_type: TrajectoryType = TrajectoryType.PLANNED
    survey_revision_id: str | None = None
    stations: list[SurveyStation] = Field(default_factory=list)
    total_md_m: float = Field(default=0.0, ge=0.0)
    final_tvd_m: float = Field(default=0.0, ge=0.0)
    closure_distance_m: float = Field(default=0.0, ge=0.0)
    closure_azimuth_rad: float = Field(default=0.0, ge=0.0, lt=2 * math.pi)
    max_dls_rad_m: float = Field(default=0.0, ge=0.0)
    is_active: bool = Field(default=True)
    created_by: str = "engineer"
    created_at: str = Field(default_factory=utc_now_iso)


class TargetGeometryType(str, Enum):
    POINT = "point"
    CIRCLE = "circle"
    RECTANGLE = "rectangle"
    POLYGON = "polygon"


class Target(DomainContract):
    """Subsurface geological or engineering drilling target."""
    id: str
    wellbore_id: str
    name: str = Field(min_length=1, max_length=100)
    geometry_type: TargetGeometryType = TargetGeometryType.CIRCLE
    center_tvd_m: float = Field(ge=0.0)
    center_north_m: float = Field(default=0.0)
    center_east_m: float = Field(default=0.0)
    radius_m: float = Field(default=50.0, ge=0.0)
    length_m: float = Field(default=100.0, ge=0.0)
    width_m: float = Field(default=50.0, ge=0.0)
    dip_angle_rad: float = Field(default=0.0, ge=-math.pi / 2, le=math.pi / 2)
    dip_azimuth_rad: float = Field(default=0.0, ge=0.0, lt=2 * math.pi)
    tolerance_m: float = Field(default=10.0, ge=0.0)
    formation_id: str | None = None


class Formation(DomainContract):
    """Geological formation boundary top and lithology."""
    id: str
    project_id: str
    name: str = Field(min_length=1, max_length=100)
    top_tvd_m: float = Field(ge=0.0)
    base_tvd_m: float | None = Field(default=None, ge=0.0)
    lithology: str = Field(default="Sandstone")
    uncertainty_m: float = Field(default=5.0, ge=0.0)
    pore_pressure_gradient_pa_m: float | None = None
    fracture_gradient_pa_m: float | None = None
    unconfined_compressive_strength_pa: float | None = None


class CasingString(DomainContract):
    """Casing string component in well construction."""
    id: str
    wellbore_id: str
    name: str = Field(min_length=1, max_length=100)
    casing_type: Literal["conductor", "surface", "intermediate", "production", "liner"] = "surface"
    top_md_m: float = Field(default=0.0, ge=0.0)
    shoe_md_m: float = Field(ge=0.0)
    od_m: float = Field(gt=0.0, le=1.5, description="Outer diameter in meters")
    id_m: float = Field(gt=0.0, le=1.5, description="Inner diameter in meters")
    weight_n_m: float = Field(gt=0.0, description="Nominal linear weight in N/m")
    grade: str = Field(default="L80")
    connection: str = Field(default="API BTC")
    burst_rating_pa: float = Field(default=5e7, gt=0.0)
    collapse_rating_pa: float = Field(default=3e7, gt=0.0)
    axial_yield_n: float = Field(default=2e6, gt=0.0)

    @model_validator(mode="after")
    def validate_diameters_and_depths(self):
        if self.id_m >= self.od_m:
            raise ValueError(f"Inner diameter ({self.id_m} m) must be smaller than outer diameter ({self.od_m} m)")
        if self.shoe_md_m <= self.top_md_m:
            raise ValueError(f"Shoe MD ({self.shoe_md_m} m) must be greater than top MD ({self.top_md_m} m)")
        return self


class BHAComponent(DomainContract):
    """Individual downhole drill string / BHA component."""
    name: str
    component_type: Literal["bit", "motor", "rss", "mwd", "lwd", "stabilizer", "drill_collar", "hwdp", "drill_pipe"]
    length_m: float = Field(gt=0.0)
    od_m: float = Field(gt=0.0)
    id_m: float = Field(default=0.0, ge=0.0)
    weight_n_m: float = Field(default=0.0, ge=0.0)


class BHAProgramme(DomainContract):
    """Complete Bottom Hole Assembly programme."""
    id: str
    wellbore_id: str
    name: str = Field(min_length=1, max_length=100)
    bit_diameter_m: float = Field(gt=0.0, le=1.5)
    components: list[BHAComponent] = Field(min_length=1)
    total_length_m: float = Field(default=0.0, ge=0.0)


class MudProgramme(DomainContract):
    """Drilling fluid / mud properties programme."""
    id: str
    wellbore_id: str
    name: str = Field(min_length=1, max_length=100)
    mud_type: Literal["water_based", "oil_based", "synthetic", "pneumatic"] = "water_based"
    density_kg_m3: float = Field(ge=500.0, le=3000.0)
    plastic_viscosity_pa_s: float = Field(default=0.02, ge=0.0)
    yield_point_pa: float = Field(default=7.0, ge=0.0)
    flow_behavior_index_n: float = Field(default=0.6, gt=0.0, le=1.5)
    consistency_index_k: float = Field(default=0.5, gt=0.0)
    base_fluid: str = "water"
