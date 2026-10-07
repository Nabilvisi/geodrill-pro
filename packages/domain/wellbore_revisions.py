"""Source-bound wellbore revision commands; all numeric inputs are explicit SI."""
from typing import Any, Literal
from pydantic import Field
from packages.engineering.models import Contract, SurveyRequest
from packages.engineering.geometry import GeometryInput

TrajectoryRole = Literal['planned', 'actual', 'scenario']


class SurveyFrame(Contract):
    datum: str = Field(min_length=1, max_length=100)
    north_reference: Literal['true', 'grid']
    coordinate_reference: str = Field(min_length=3, max_length=200)
    wellhead_north_m: float = Field(ge=-1e8, le=1e8)
    wellhead_east_m: float = Field(ge=-1e8, le=1e8)
    wellhead_elevation_m: float = Field(ge=-10000, le=10000)


class SurveySave(Contract):
    trajectory_type: TrajectoryRole
    base_revision_id: str | None = None
    change_note: str = Field(min_length=3, max_length=300)
    frame: SurveyFrame
    evidence_state: Literal['synthetic', 'unqualified_observation', 'authored_design']
    survey_quality_note: str = Field(min_length=3, max_length=300)
    tool_metadata: dict[str, Any] = Field(default_factory=dict)


class AuthoredSurveySave(SurveySave):
    survey: SurveyRequest


class AdoptSurvey(SurveySave):
    dataset_id: str = Field(min_length=1, max_length=80)


class TrajectorySave(Contract):
    survey_revision_id: str = Field(min_length=1, max_length=80)
    base_revision_id: str | None = None
    change_note: str = Field(min_length=3, max_length=300)
    geometry: GeometryInput | None = None


class UncertaintySave(Contract):
    trajectory_revision_id: str = Field(min_length=1, max_length=80)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ProximitySave(Contract):
    trajectory_revision_id: str = Field(min_length=1, max_length=80)
    offset_wellbore_id: str = Field(min_length=1, max_length=80)
    offset_trajectory_revision_id: str = Field(min_length=1, max_length=80)
    geomagnetic: dict[str, Any] = Field(default_factory=dict)
    correlation_mode: Literal['independent', 'systematic_geomagnetic', 'fully_correlated']
