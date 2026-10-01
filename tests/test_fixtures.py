import json
from scaling_law_explorer.fixtures import generate
from scaling_law_explorer.cli import load
from scaling_law_explorer.core import analyze

def test_fixtures_labelled_synthetic(tmp_path):
    generate(tmp_path)
    assert (tmp_path/"observations.jsonl").read_text().startswith("# synthetic: true")
    assert all(r["synthetic"] is True for r in load(tmp_path))
    assert json.loads((tmp_path/"expectations.json").read_text())["synthetic"] is True

def test_fixture_ground_truth_matches_hand_computed(tmp_path):
    generate(tmp_path)
    expected=json.loads((tmp_path/"expectations.json").read_text())
    result=analyze(load(tmp_path))
    for key in ("records","real_records","synthetic_records","experiments","power_law_consistent_count"):
        assert result[key] == expected[key]
