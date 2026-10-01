"""Pure validation and log-log OLS. Fitted parameters are not measured predictions."""
import math
import re
from datetime import date

class SchemaError(ValueError):
    """Named invalid observation error."""

FIELDS = {"id", "experiment", "compute", "loss", "synthetic", "date", "source"}

def validate(records):
    seen = set()
    clean = []
    for row in records:
        if not isinstance(row, dict):
            raise SchemaError("record: expected object")
        if any(not isinstance(k, str) for k in row):
            raise SchemaError("field: invalid CSV column count or non-string field")
        unknown = set(row) - FIELDS
        if unknown:
            raise SchemaError("unknown field: " + sorted(unknown)[0])
        for field in ("id", "experiment", "compute", "loss", "synthetic", "source"):
            if field not in row:
                raise SchemaError("missing field: " + field)
        for field in ("id", "experiment", "source"):
            if not isinstance(row[field], str) or not row[field] or len(row[field]) > 10000:
                raise SchemaError(field + ": expected nonempty string of at most 10000 characters")
        if row["id"] in seen:
            raise SchemaError("id: duplicate " + row["id"])
        seen.add(row["id"])
        if type(row["synthetic"]) is not bool:
            raise SchemaError("synthetic: expected boolean")
        for field in ("compute", "loss"):
            value = row[field]
            if type(value) not in (int, float) or not 1e-100 <= value <= 1e100 or not math.isfinite(value):
                raise SchemaError(field + ": expected finite positive number in [1e-100, 1e100]")
        if "date" in row:
            try:
                # Fixed cutoff preserves determinism and makes future-date handling explicit.
                if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", row["date"]):
                    raise ValueError()
                d = date.fromisoformat(row["date"])
                if d > date(2026, 9, 30):
                    raise ValueError()
            except (ValueError, TypeError):
                raise SchemaError("date: expected ISO date on or before 2026-09-30") from None
        clean.append(dict(row))
    return sorted(clean, key=lambda r: r["id"])

def analyze(records):
    rows = validate(records)
    experiments = []
    for name in sorted({r["experiment"] for r in rows}):
        group = [r for r in rows if r["experiment"] == name]
        x = [math.log2(r["compute"]) for r in group]
        y = [math.log2(r["loss"]) for r in group]
        mx, my = math.fsum(x)/len(x), math.fsum(y)/len(y)
        xx = math.fsum((v-mx)**2 for v in x)
        item = {"experiment": name, "records": len(group), "status": "insufficient_variation",
                "fitted_log2_intercept": None, "fitted_exponent": None,
                "observed_log2_residual_sse": None, "power_law_consistent": False}
        if xx:
            slope = math.fsum((a-mx)*(b-my) for a,b in zip(x,y))/xx
            intercept = my-slope*mx
            sse = math.fsum((b-(intercept+slope*a))**2 for a,b in zip(x,y))
            item.update(status="fitted", fitted_log2_intercept=intercept,
                        fitted_exponent=slope, observed_log2_residual_sse=sse,
                        power_law_consistent=sse <= 1e-12)
        experiments.append(item)
    synthetic = sum(r["synthetic"] for r in rows)
    return {"schema_version": 1, "records": len(rows), "synthetic_records": synthetic,
            "real_records": len(rows)-synthetic, "power_law_consistent_count": sum(e["power_law_consistent"] for e in experiments),
            "experiments": experiments,
            "provenance": [{"id": r["id"], "source": r["source"], "synthetic": r["synthetic"]} for r in rows],
            "honesty": "Fitted parameters describe supplied observations only. No extrapolation, savings, or unmeasured predictions. Real means user-declared real, not independently verified.",
            "hypothetical_figures": "None. Hypothetical or illustrative figures are not computed."}
