from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator
import math


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False, strict=True, str_strip_whitespace=True)


class Survey(Contract):
    md_m: float = Field(ge=0, le=30000)
    inclination_rad: float = Field(ge=0, le=math.pi)
    azimuth_rad: float = Field(ge=0, lt=2 * math.pi)


class Formation(Contract):
    name: str = Field(min_length=1, max_length=80)
    top_tvd_m: float = Field(ge=0, le=30000)
    uncertainty_m: float = Field(ge=0, le=10000)


class ProjectCreate(Contract):
    name: str = Field(min_length=1, max_length=100)
    well_name: str = Field(min_length=1, max_length=100)
    datum: str = Field(min_length=1, max_length=100)
    north_reference: Literal["true", "grid"] = "true"
    bit_diameter_m: float = Field(ge=0.001, le=2)
    origin: Literal["historical", "synthetic"] = "historical"


class SurveyRequest(Contract):
    stations: list[Survey] = Field(min_length=2, max_length=10000)

    @model_validator(mode="after")
    def ordered(self):
        if self.stations[0].md_m != 0:
            raise ValueError("First station must be MD 0 at the declared datum; tie-in offsets are not supported.")
        if any(b.md_m <= a.md_m for a, b in zip(self.stations, self.stations[1:])):
            raise ValueError("Survey measured depths must strictly increase.")
        return self


class MSEInput(Contract):
    wob_n: float = Field(ge=0, le=1e8)
    torque_nm: float = Field(ge=0, le=1e8)
    rotation_rad_s: float = Field(ge=0, le=1000)
    rop_m_s: float = Field(ge=0, le=10)
    bit_diameter_m: float = Field(ge=0.001, le=2)
    load_source: Literal["surface", "downhole"] = "surface"
    drilling_state: Literal["drilling", "off_bottom", "connection", "unknown"] = "drilling"


class PressureInput(Contract):
    tvd_m: float = Field(ge=0.001, le=30000)
    density_kg_m3: float = Field(ge=500, le=3000)
    surface_gauge_pa: float = Field(ge=0, le=1e8)
    annular_loss_pa: float = Field(ge=0, le=1e8)
    pore_gauge_pa: float = Field(ge=0, le=1e9)
    fracture_gauge_pa: float = Field(gt=0, le=1e9)
    regime: Literal["steady_single_phase"] = "steady_single_phase"

    @model_validator(mode="after")
    def ordered(self):
        if self.fracture_gauge_pa <= self.pore_gauge_pa:
            raise ValueError("Fracture pressure must exceed pore pressure at the same TVD and gauge reference.")
        return self


class Acknowledgement(Contract):
    note: str = Field(min_length=3, max_length=500)
