import math
import pytest
from hypothesis import given, settings, HealthCheck, strategies as st
from pydantic import ValidationError
from packages.engineering.models import MSEInput, PressureInput, SurveyRequest
from packages.engineering.physics import minimum_curvature, mse, pressure, G
from packages.engineering.ingestion import telemetry_csv, survey_csv, las2
from services.api import demo


def survey(stations):
    return minimum_curvature(SurveyRequest(stations=stations))


def station(md, inc=0, azi=0):
    return {"md_m": md, "inclination_rad": inc, "azimuth_rad": azi}


def test_vertical_and_straight_trajectory():
    result = survey([station(0), station(500), station(1000)])[-1]
    assert result["tvd_m"] == 1000
    assert result["north_m"] == result["east_m"] == 0
    result = survey([station(0, math.pi / 3, math.pi / 2), station(1200, math.pi / 3, math.pi / 2)])[-1]
    assert result["tvd_m"] == pytest.approx(600)
    assert result["east_m"] == pytest.approx(600 * math.sqrt(3))
    assert abs(result["north_m"]) < 1e-10


def test_circular_quarter_build_independent_analytic_solution():
    # Constant-curvature quarter circle, radius 200 m; length = pi*r/2.
    result = survey([station(0), station(100 * math.pi, math.pi / 2)])[-1]
    assert result["north_m"] == pytest.approx(200)
    assert result["tvd_m"] == pytest.approx(200)


def test_azimuth_wrap_uses_short_turn():
    result = survey([station(0, math.pi / 2, math.radians(359)), station(100, math.pi / 2, math.radians(1))])[-1]
    assert abs(result["east_m"]) < 1e-10
    assert result["dogleg_rad_m"] == pytest.approx(math.radians(2) / 100)


@pytest.mark.parametrize("stations", [[station(2), station(10)], [station(0), station(0)], [station(0), station(-1)], [station(0), station(10, 4)]])
def test_bad_surveys_rejected(stations):
    with pytest.raises(ValidationError):
        survey(stations)


def test_antipodal_survey_rejected():
    with pytest.raises(ValueError, match="Antipodal"):
        survey([station(0), station(100, math.pi)])


# Windows CPU scheduling can pause even these scalar draws past Hypothesis's 1 s
# generator-health threshold. Keep all 100 numerical examples and assertions.
@settings(suppress_health_check=[HealthCheck.too_slow])
@given(st.floats(min_value=1, max_value=20000), st.floats(min_value=0, max_value=math.pi), st.floats(min_value=0, max_value=6.28))
def test_straight_displacement_never_exceeds_measured_length(length, inc, azi):
    r = survey([station(0, inc, azi), station(length, inc, azi)])[-1]
    displacement = math.sqrt(r["north_m"]**2 + r["east_m"]**2 + r["tvd_m"]**2)
    assert displacement == pytest.approx(length, rel=1e-10)


def mse_input(**changes):
    return MSEInput(**dict({"wob_n": 100000, "torque_nm": 5000, "rotation_rad_s": 2 * math.pi, "rop_m_s": 0.01, "bit_diameter_m": 0.2}, **changes))


def test_mse_work_over_removed_volume():
    # Independent energy accounting over 10 seconds.
    work = 100000 * 0.1 + 5000 * 20 * math.pi
    volume = math.pi * 0.1**2 * 0.1
    assert mse(mse_input())["value_pa"] == pytest.approx(work / volume)
    assert mse(mse_input())["label"] == "Surface MSE proxy"
    assert mse(mse_input(load_source="downhole"))["label"] == "Downhole MSE"


@pytest.mark.parametrize("changes", [{"rop_m_s": 0}, {"rop_m_s": 1e-5}, {"drilling_state": "connection"}, {"drilling_state": "unknown"}, {"drilling_state": "off_bottom"}])
def test_mse_abstains_instead_of_false_zero(changes):
    result = mse(mse_input(**changes))
    assert result["value_pa"] is None
    assert result["status"] == "withheld"


@pytest.mark.parametrize("value", [float('nan'), float('inf'), -1])
def test_invalid_mse_input(value):
    with pytest.raises(ValidationError):
        mse_input(rop_m_s=value)


def test_mse_zero_torque_reduces_to_axial_stress():
    result = mse(mse_input(torque_nm=0))
    assert result["value_pa"] == pytest.approx(100000 / (math.pi * 0.1**2))


@pytest.mark.parametrize('changes', [{'bit_diameter_m':1e-200},{'wob_n':True},{'wob_n':'100'}])
def test_numerical_domain_and_strict_types(changes):
    with pytest.raises(ValidationError):
        mse_input(**changes)


def test_import_conversion_overflow_rejected():
    with pytest.raises(ValueError, match='finite numerical range'):
        telemetry_csv(demo.telemetry().decode().replace('108.0','1e308',1), .2159)


def pressure_input(**changes):
    return PressureInput(**dict({"tvd_m":1000,"density_kg_m3":1000,"surface_gauge_pa":0,"annular_loss_pa":0,"pore_gauge_pa":8e6,"fracture_gauge_pa":12e6}, **changes))


def test_hydrostatic_and_surface_reference():
    result = pressure(pressure_input())
    assert result["bottom_gauge_pa"] == pytest.approx(9_806_650)
    assert result["equivalent_density_kg_m3"] == pytest.approx(1000)
    raised = pressure(pressure_input(surface_gauge_pa=1e6, annular_loss_pa=2e6))
    assert raised["bottom_gauge_pa"] == result["bottom_gauge_pa"] + 3e6
    assert not raised["within_entered_bounds"]
    assert raised["below_fracture_pa"] < 0


@pytest.mark.parametrize("changes", [{"tvd_m":0}, {"pore_gauge_pa":12e6}, {"regime":"multiphase"}, {"density_kg_m3":float('nan')}])
def test_pressure_rejects_unsupported_inputs(changes):
    with pytest.raises(ValidationError):
        pressure_input(**changes)


def test_telemetry_preserves_missing_and_deliberate_gap():
    rows, events, mapping = telemetry_csv(demo.telemetry().decode(), 0.2159)
    assert len(rows) == 240
    assert rows[42]["spp_pa"] is None
    assert rows[42]["mse_pa"] is None
    assert rows[42]["quality"] == "invalid"
    assert rows[90]["rop_m_s"] == 0
    assert rows[90]["mse_pa"] is None
    assert rows[170]["gap_s"] == 26
    assert len([e for e in events if e["code"] == "DATA_GAP"]) == 1
    assert mapping["wob"]["factor_to_si"] == 1000


@pytest.mark.parametrize("edit", [lambda s:s.replace('wob[kN]','wob[lb]'), lambda s:s.replace('+00:00',''), lambda s:s.replace('108.0','NaN',1),lambda s:s.replace('timestamp,','timestamp,timestamp,',1)])
def test_import_fails_for_bad_units_times_finite_values_or_headers(edit):
    with pytest.raises(ValueError):
        telemetry_csv(edit(demo.telemetry().decode()), 0.2159)


def test_import_rejects_duplicate_times():
    lines = demo.telemetry().decode().splitlines()
    with pytest.raises(ValueError, match="duplicate"):
        telemetry_csv('\n'.join([lines[0], lines[1], lines[1]]), .2159)


def test_supported_field_units_are_equivalent():
    metric = 'timestamp,md[m],tvd[m],wob[N],torque[N.m],rpm[rad/s],rop[m/s],spp[Pa],flow[m3/s],state\n2026-01-01T00:00:00Z,304.8,304.8,4448.2216152605,1.3558179483314,6.283185307179586,0.00008466666666666667,6894.757293168,0.0000630901964,drilling'
    field = 'timestamp,md[ft],tvd[ft],wob[klbf],torque[ft.lbf],rpm[rpm],rop[ft/h],spp[psi],flow[gpm],state\n2026-01-01T00:00:00Z,1000,1000,1,1,60,1,1,1,drilling'
    a = telemetry_csv(metric, .2)[0][0]
    b = telemetry_csv(field, .2)[0][0]
    for key in ['md_m','wob_n','torque_nm','rotation_rad_s','rop_m_s','spp_pa','flow_m3_s','mse_pa']:
        assert a[key] == pytest.approx(b[key], rel=1e-7)


def test_negative_observation_visible_but_ineligible():
    text = demo.telemetry().decode().replace('108.0', '-108.0', 1)
    rows, _, _ = telemetry_csv(text, .2159)
    assert rows[0]['wob_n'] == -108000
    assert rows[0]['quality'] == 'invalid'
    assert rows[0]['mse_pa'] is None


def test_survey_unit_conversion():
    result = survey_csv('md[ft],inclination[deg],azimuth[deg]\n0,0,0\n1000,0,0')
    assert result[-1]['tvd_m'] == pytest.approx(304.8)


def test_las_null_and_units():
    rows, curves, meta = las2(demo.LAS.decode())
    assert len(rows) == 5
    assert rows[2]['GR'] is None
    assert curves[1]['unit'] == 'API'
    assert meta['NULL'] == '-999.25'


@pytest.mark.parametrize('text', [demo.LAS.decode().replace('WRAP. NO','WRAP. YES'), demo.LAS.decode().replace('DEPT.M','DEPT.UNKNOWN'), demo.LAS.decode().replace('2401 48 2.46','2400 48 2.46'), demo.LAS.decode().replace('2401 48 2.46','2401 48')])
def test_las_unsupported_or_corrupt_rejected(text):
    with pytest.raises(ValueError):
        las2(text)
