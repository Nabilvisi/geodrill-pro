import json
import pytest
from packages.frontend import frontend_dist

def test_old_build_fallback(tmp_path):
    assert frontend_dist(tmp_path)==tmp_path/"dist"

def test_complete_release_selected(tmp_path):
    name="dist/release-"+"a"*32
    path=tmp_path/name;(path/"assets").mkdir(parents=True);(path/"index.html").write_text("complete")
    (tmp_path/"frontend-build.json").write_text(json.dumps({"directory":name}))
    assert frontend_dist(tmp_path)==path

@pytest.mark.parametrize("directory",["../external","dist/release-../outside","C:/external",None])
def test_release_pointer_escape_rejected(tmp_path,directory):
    (tmp_path/"frontend-build.json").write_text(json.dumps({"directory":directory}))
    with pytest.raises(ValueError):frontend_dist(tmp_path)

def test_incomplete_release_rejected(tmp_path):
    (tmp_path/"frontend-build.json").write_text(json.dumps({"directory":"dist/release-"+"a"*32}))
    with pytest.raises(ValueError):frontend_dist(tmp_path)
