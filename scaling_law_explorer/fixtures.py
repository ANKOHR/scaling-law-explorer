"""Labelled synthetic ground truth, no random generator or hidden seed."""
import json
from pathlib import Path

def records():
    return [{"id": f"{name}-{i:03}", "experiment": name, "compute": 2**(i%5),
             "loss": 2**(intercept-exponent*(i%5)), "synthetic": True,
             "source": "synthetic planted fixture", "date": "2026-09-30"}
            for name,intercept,exponent in (("inverse", 4, 1), ("inverse_square", 6, 2)) for i in range(100)]

def generate(out):
    path = Path(out)
    path.mkdir(parents=True, exist_ok=True)
    (path/"observations.jsonl").write_text("# synthetic: true; deterministic planted observations\n" +
        "".join(json.dumps(r, sort_keys=True)+"\n" for r in records()), encoding="utf-8")
    expectations = {"synthetic": True, "records": 200, "synthetic_records": 200, "real_records": 0,
                    "power_law_consistent_count": 2,
                    "experiments": [{"experiment": name, "records": 100, "status": "fitted",
                         "fitted_exponent": slope, "fitted_log2_intercept": intercept,
                         "observed_log2_residual_sse": 0.0, "power_law_consistent": True}
                        for name,slope,intercept in (("inverse", -1.0, 4.0), ("inverse_square", -2.0, 6.0))],
                    "derivation": "Each x log2 level 0..4 occurs 20 times. Mean x=2, centered x sum squares=200. y=4-x or 6-2x, covariance=-200 or -400. Slopes=-1,-2, intercepts=4,6; residuals=0."}
    (path/"expectations.json").write_text(json.dumps(expectations, sort_keys=True, indent=2)+"\n", encoding="utf-8")
