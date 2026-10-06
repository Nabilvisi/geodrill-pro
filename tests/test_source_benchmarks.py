import pytest
from tools.verify_forge_survey import read_source, verify, SOURCE


def test_original_forge_survey_all_station_reproduction():
    result = verify()
    assert result["passed"] is True
    assert result["stations_evaluated"] == 422
    assert result["stations_excluded"] == 0
    assert result["max_3d_error_m"] <= result["absolute_3d_tolerance_m"]
    assert result["field_qualified"] is False
    assert result["comparisons"][0]["error_3d_m"] == 0


def test_source_corruption_is_rejected_before_parsing(tmp_path):
    altered = tmp_path / "survey.xlsx"
    data = bytearray(SOURCE.read_bytes())
    data[len(data) // 2] ^= 1
    altered.write_bytes(data)
    with pytest.raises(ValueError, match="source hash mismatch"):
        read_source(altered)
