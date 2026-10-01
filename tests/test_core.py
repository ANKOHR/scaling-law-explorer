import copy
import pytest
from scaling_law_explorer.core import analyze, SchemaError
from scaling_law_explorer.fixtures import records

@pytest.mark.parametrize("field,value", [("compute",-1),("loss",0),("loss",float("nan")),("compute",float("inf")),("compute",True),("date","2099-01-01"),("source","x"*10001),("synthetic","true"),("extra",1)])
def test_rejects_adversarial_values(field,value):
    row=records()[0]
    row[field]=value
    with pytest.raises(SchemaError): analyze([row])

def test_duplicate_ids():
    with pytest.raises(SchemaError, match="duplicate"): analyze([records()[0]]*2)

def test_corrupted_ground_truth_changes_result():
    rows=records()
    before=analyze(rows)
    rows[0]["loss"]*=2
    after=analyze(rows)
    assert after != before
    assert after["power_law_consistent_count"] == 1
    assert after["experiments"][0]["observed_log2_residual_sse"] > 0

def test_insufficient_variation():
    assert analyze([records()[0]])["experiments"][0]["status"] == "insufficient_variation"

def test_handles_unicode_and_long_inputs():
    row=records()[0]
    row["source"]="研究 C:\\Users\\henry " + "é"*9000
    assert analyze([row])["provenance"][0]["source"] == row["source"]

def test_five_hand_written_real_records():
    rows=[dict(id=str(i),experiment="manual",compute=x,loss=y,synthetic=False,source="Henry entered by hand") for i,(x,y) in enumerate([(1,16),(2,8),(4,4),(8,2),(16,1)])]
    result=analyze(rows)
    assert result["real_records"] == 5
    assert result["experiments"][0]["fitted_exponent"] == -1
