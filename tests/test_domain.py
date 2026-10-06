"""Unit tests for packages.domain models, calculation envelope, and staleness."""
import pytest
import math
from packages.domain import (
    Project,
    Well,
    Wellbore,
    WellboreType,
    SurveyStation,
    SurveyRevision,
    TrajectoryRevision,
    TrajectoryType,
    CasingString,
    BHAComponent,
    BHAProgramme,
    MudProgramme,
    CalculationEnvelope,
    CalculationStatus,
    QualificationLevel,
    ModelClass,
    compute_inputs_hash,
    StalenessEvaluator,
    RevisionType,
)


def test_project_and_well_creation():
    p = Project(id="p-100", name="North Sea Pilot")
    assert p.name == "North Sea Pilot"
    assert p.coordinate_reference.datum == "WGS84"
    assert p.unit_profile.depth_unit == "m"

    w = Well(id="w-1", project_id=p.id, name="Well A-15")
    assert w.status == "planned"
    assert w.surface_location.rkb_elevation_m == 0.0


def test_survey_revision_ordering():
    s1 = SurveyStation(md_m=0.0, inc_rad=0.0, azi_rad=0.0)
    s2 = SurveyStation(md_m=500.0, inc_rad=math.radians(10), azi_rad=math.radians(45))
    sr = SurveyRevision(id="sr-1", wellbore_id="wb-1", revision=1, stations=[s1, s2])
    assert len(sr.stations) == 2

    # Inverted order should raise ValueError
    with pytest.raises(ValueError, match="strictly increasing"):
        SurveyRevision(id="sr-2", wellbore_id="wb-1", revision=2, stations=[s2, s1])


def test_casing_validation():
    # Valid casing
    cs = CasingString(
        id="c-1",
        wellbore_id="wb-1",
        name="9-5/8 inch Casing",
        top_md_m=0.0,
        shoe_md_m=2000.0,
        od_m=0.2445,
        id_m=0.2244,
        weight_n_m=583.8,
    )
    assert cs.grade == "L80"

    # ID >= OD should raise
    with pytest.raises(ValueError, match="smaller than outer diameter"):
        CasingString(
            id="c-invalid",
            wellbore_id="wb-1",
            name="Invalid Casing",
            top_md_m=0.0,
            shoe_md_m=1000.0,
            od_m=0.20,
            id_m=0.25,
            weight_n_m=500.0,
        )


def test_calculation_envelope_and_staleness():
    inputs = {"flow_rate_m3_s": 0.03, "mud_density_kg_m3": 1200}
    h = compute_inputs_hash(inputs)
    env = CalculationEnvelope(
        calculation_id="calc-001",
        model="hydraulics.pressure_profile",
        model_version="0.9.0",
        model_class=ModelClass.DETERMINISTIC_VERIFIED,
        qualification=QualificationLevel.INTERNAL_VERIFICATION,
        status=CalculationStatus.CALCULATED,
        inputs_hash=h,
        geometry_revision_id="geo-rev-1",
        mud_revision_id="mud-rev-1",
        result={"annular_pressure_loss_pa": 2.5e6},
        assumptions=["Steady state single phase"],
    )
    assert env.status == CalculationStatus.CALCULATED

    # When revisions match active, not stale
    stale, reasons = StalenessEvaluator.is_calculation_stale(
        env,
        active_geometry_rev="geo-rev-1",
        active_mud_rev="mud-rev-1",
    )
    assert not stale
    assert len(reasons) == 0

    # When geometry revision updates, calculation becomes stale
    stale, reasons = StalenessEvaluator.is_calculation_stale(
        env,
        active_geometry_rev="geo-rev-2",
        active_mud_rev="mud-rev-1",
    )
    assert stale
    assert "Geometry revision changed" in reasons[0]

    # Marking envelope stale
    stale_env = env.mark_stale("Geometry updated")
    assert stale_env.status == CalculationStatus.STALE
    assert any("STALE" in w for w in stale_env.warnings)


def test_staleness_identify_stale_models():
    # If survey changed, directional and anticollision models should be stale
    stale_models = StalenessEvaluator.identify_stale_models({RevisionType.SURVEY})
    assert "directional.minimum_curvature" in stale_models
    assert "anticollision.closest_approach" in stale_models
    # Hydraulics doesn't depend on survey directly if bound through geometry
    assert "hydraulics.pressure_profile" not in stale_models
