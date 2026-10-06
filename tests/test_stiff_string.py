import pytest
from packages.engineering.torque_drag import torque_drag
from packages.engineering.geometry import Path
from packages.engineering.models import SurveyRequest
from tests.test_hydraulics import geometry
from tests.test_research_modules import td, su

def test_stiff_string_model():
    p = Path(SurveyRequest(stations=[{"md_m":0.,"inclination_rad":0.,"azimuth_rad":0.}, {"md_m":1000.,"inclination_rad":0.5,"azimuth_rad":0.}]))
    
    geom = geometry()
    v = td(model="stiff_string", tortuosity_rad_m=0.001)
    
    res = torque_drag(v, geom, p)
    assert res["model_version"] == "GD-A12-stiff-string-1"
    assert "hookload_n" in res
    assert "profile" in res
    assert len(res["profile"]) > 0

