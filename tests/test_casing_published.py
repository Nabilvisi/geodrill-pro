"""GD-A13 independent benchmarks against published API 5C2/5CT tabulated pipe ratings.

ACCEPTANCE (declared before comparison): API tables report ratings rounded to the nearest
10 psi, so |calculated - published| <= 10 psi is the acceptance tolerance. Inputs are the
nominal OD/wall and specified minimum yield used by the tables; ratings are not field data.
"""
import pytest
from packages.engineering.casing_envelopes import calculate_api_collapse_psi, api_burst_rating, PSI_TO_PA

TOL_PSI = 10.0
IN = 0.0254

# (label, OD in, wall in, yield psi, published collapse psi, published burst psi, expected regime)
PUBLISHED = [
    ("9-5/8in 36lb/ft K-55", 9.625, 0.352, 55000, 2020, 3520, "transition_collapse"),
    ("9-5/8in 47lb/ft N-80", 9.625, 0.472, 80000, 4750, 6870, "plastic_collapse"),
    ("7in 29lb/ft P-110", 7.000, 0.408, 110000, 8530, 11220, "plastic_collapse"),
]


@pytest.mark.parametrize("label,od,t,yp,collapse,burst,regime", PUBLISHED)
def test_collapse_matches_published_table(label, od, t, yp, collapse, burst, regime):
    res = calculate_api_collapse_psi(yp, od / t)
    assert res["regime"] == regime, label
    assert abs(res["pressure_psi"] - collapse) <= TOL_PSI, (label, res["pressure_psi"])


@pytest.mark.parametrize("label,od,t,yp,collapse,burst,regime", PUBLISHED)
def test_barlow_burst_matches_published_table(label, od, t, yp, collapse, burst, regime):
    res = api_burst_rating(od * IN, t * IN, yp * PSI_TO_PA)
    assert abs(res["burst_barlow_api_pa"] / PSI_TO_PA - burst) <= TOL_PSI, label
