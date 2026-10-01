"""Deterministic reports with explicit input provenance."""
import json

def safe(text):
    return str(text).replace(chr(0x2014), "-")

def render(result, format="md"):
    banner = (f"Data provenance: {result['synthetic_records']} synthetic fixture records; "
              f"{result['real_records']} user-declared real records. Real sources are supplied by the user and not independently verified.")
    if format == "json":
        return safe(json.dumps({"provenance_banner": banner, **result}, ensure_ascii=False, sort_keys=True, indent=2)) + "\n"
    lines = ["# Scaling Law Explorer", "", banner, "", result["honesty"], "", result["hypothetical_figures"], "",
             f"Records: {result['records']}", f"Power-law-consistent experiments (observed log2 SSE <= 1e-12): {result['power_law_consistent_count']}", "",
             "| Experiment | Records | Status | Fitted exponent | Fitted log2 intercept | Observed log2 residual SSE |", "| :--- | ---: | :--- | ---: | ---: | ---: |"]
    for e in result["experiments"]:
        name = e["experiment"].replace("|", "\\|").replace("\n", " ").replace("\r", " ")
        lines.append(f"| {name} | {e['records']} | {e['status']} | {e['fitted_exponent']} | {e['fitted_log2_intercept']} | {e['observed_log2_residual_sse']} |")
    lines += ["", "## Input provenance", ""]
    for r in result["provenance"]:
        lines.append(json.dumps(r, ensure_ascii=False, sort_keys=True))
    return safe("\n".join(lines)) + "\n"
