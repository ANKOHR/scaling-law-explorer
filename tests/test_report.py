import json
from scaling_law_explorer.core import analyze
from scaling_law_explorer.fixtures import records
from scaling_law_explorer.report import render

def test_report_matches_ground_truth_exact():
    result=json.loads(render(analyze(records()),"json"))
    assert result["records"] == 200
    assert [(e["fitted_exponent"],e["fitted_log2_intercept"],e["observed_log2_residual_sse"]) for e in result["experiments"]] == [(-1,4,0),(-2,6,0)]

def test_report_zero_false_positives():
    rows=records()
    # A third planted non-power-law has a nonzero residual.
    rows += [dict(id="noise"+str(i),experiment="non_power",compute=2**i,loss=y,synthetic=True,source="synthetic adversarial") for i,y in enumerate([1,2,16,2,1])]
    r=json.loads(render(analyze(rows),"json"))
    assert {e["experiment"] for e in r["experiments"] if e["power_law_consistent"]} == {"inverse","inverse_square"}

def test_report_carries_provenance_banner():
    for fmt in ("md","json"):
        text=render(analyze(records()),fmt)
        assert "Data provenance: 200 synthetic fixture records; 0 user-declared real records" in text

def test_hypothetical_figures_labelled():
    for fmt in ("md","json"):
        assert "Hypothetical or illustrative figures are not computed" in render(analyze([]),fmt)

def test_no_em_dashes_in_outputs():
    row=records()[0]
    row["source"]="source"+chr(0x2014)+"name"
    for fmt in ("md","json"):
        assert chr(0x2014) not in render(analyze([row]),fmt)
