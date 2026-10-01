# Scaling Law Explorer

`sle2` computes empirical scaling-law summaries from explicit local observations on CPU. No network calls, model calls, GPU packages, or runtime dependencies.

Hypothesis: deterministic validation and tested log-log fitting make small scaling experiments reproducible and auditable. Acceptance: the 200-record planted fixture has exact expected coefficients, counts and residuals, zero false positive classifications, and the complete demo runs within five seconds.

## Quickstart

Python 3.10 or newer, setuptools and pytest already installed:

```powershell
python -m pip install --no-deps --no-build-isolation -e .
$sleScripts = python -c "import sysconfig; print(sysconfig.get_path('scripts', scheme='nt_user'))"
$env:PATH = "$sleScripts;$env:PATH"
sle2 fixtures --out demo
sle2 run --input demo
sle2 report --format md
python -m pytest -q
```

The module entry point also works without installation: `python -m scaling_law_explorer.cli` followed by the same arguments. Results default to `.sle2-results.json` in the working directory. Use a separate results path for each experiment. Real trial data is entered by Henry and is not shipped.

## Input reference

An input directory contains only `.jsonl` or `.csv` observation files. `expectations.json` is reserved fixture metadata and ignored. Other files cause a named schema error, including YAML and ordinary JSON. JSONL supports blank lines and lines starting with `#`. UTF-8 and UTF-8 BOM are accepted. CSV uses a header with these fields and lowercase `true` or `false` for synthetic.

Required fields: `id` (globally unique), `experiment` (group), `compute` (positive compute in a consistent user-chosen unit), `loss` (positive observed loss in a consistent unit), `synthetic` (boolean), `source` (user-entered provenance). Strings are nonempty and at most 10000 characters. Unicode and Windows paths are accepted. Numbers must be finite and within [1e-100, 1e100]; booleans are not numbers. Unknown fields fail. Negative values, zero, duplicate ids and extreme strings fail instead of being dropped. Optional `date` must be ISO YYYY-MM-DD on or before the fixed study cutoff 2026-09-30. This fixed cutoff avoids date-dependent output; extend it explicitly for later studies.

A smallest five-record hand-entered example, saved as `manual/observations.jsonl`:

```jsonl
{"id":"a","experiment":"manual","compute":1,"loss":16,"synthetic":true,"source":"Henry entered by hand"}
{"id":"b","experiment":"manual","compute":2,"loss":8,"synthetic":true,"source":"Henry entered by hand"}
{"id":"c","experiment":"manual","compute":4,"loss":4,"synthetic":true,"source":"Henry entered by hand"}
{"id":"d","experiment":"manual","compute":8,"loss":2,"synthetic":true,"source":"Henry entered by hand"}
{"id":"e","experiment":"manual","compute":16,"loss":1,"synthetic":true,"source":"Henry entered by hand"}
```

This is an illustrative format example, not evidence of a real trial. Use `synthetic:true` when copying these invented numbers into a working dataset. Actual real records must be Henry's own entered observations.

## Subcommands

- `sle2 fixtures --out demo`: write deterministic, explicitly synthetic observations and independent hand-computed expectations.
- `sle2 validate --input manual`: check schema, values and duplicate ids, with counts by declared provenance.
- `sle2 fit --input manual`: print fitted log-log summaries and provenance without persisting results.
- `sle2 run --input demo --results results.json`: compute summaries and atomically persist them.
- `sle2 report --results results.json --format json --out report.json`: render JSON or Markdown with provenance. Omit `--out` to print.

Every command supports `--help` with an example. Invalid input exits 2 with a named error. Parse/schema errors identify file and line; duplicate ids across files produce a named id error. Missing directories identify the missing path and usage hint. Report write failures leave no partial destination file and retain any previous report.

## Computation and limits

For each experiment fit y = intercept + exponent*x with x=log2(compute), y=log2(loss), ordinary least squares. Observed log2 residual SSE is the sum of squared deviations from that fit. `power_law_consistent` means SSE <= 1e-12 for the supplied observations, with at least two distinct compute levels. It is a numerical descriptive criterion, not a statistical discovery or generalization claim. Constant compute or one observation reports `insufficient_variation` and null parameters. Empty input produces zero counts and an empty experiment list.

The fixture has 100 inverse and 100 inverse-square records. Each of five log2 compute levels occurs 20 times. The equations are y=4-x and y=6-2x. The independent expectations file records the hand calculation: centered x sum squares 200, covariance -200 or -400, slopes -1 and -2, intercepts 4 and 6, residual SSE zero. No randomness is used, so there is no seed. Sorting records and experiments and fixed JSON serialization make repeated output byte-identical in the same Python/platform environment. Floating point libm may differ across platforms for arbitrary non-power-of-two inputs.

## Architecture

```text
Local JSONL/CSV -> CLI parser -> pure schema validation -> pure log-log OLS
                                                          |
                                               deterministic results JSON
                                                          |
                                             JSON / Markdown report
Fixture generator -> synthetic observations + independent expectations
```

## Honesty boundary and fixture policy

All figures come from supplied inputs. Coefficients are labelled fitted, residuals refer only to observations. The tool does not predict unseen losses, discover causal laws, or estimate savings. No time or money saved is reported without a baseline; this version does not compute savings at all. Hypothetical figures are explicitly absent in every report. User-declared real provenance is not independently verified. Reports enumerate record ids and source declarations. Synthetic fixture files carry a header comment where allowed and a `synthetic:true` field in every record; the JSON expectations file has `synthetic:true` because JSON cannot contain comments. Reports always count synthetic and declared real inputs. Output replaces the prohibited em dash character with a hyphen while preserving stored source input.

## Evidence and improvement hook

Local acceptance evidence is recorded in EVIDENCE.md and BUILD-DONE.txt. After two weeks of actual use, record runs used and compare every fitted exponent, intercept and residual against a hand-checked sample, declaring a numerical tolerance before review. Metric: fraction of checked experiment summaries with any incorrect value. If error exceeds 10 percent, fix the largest failure cause and rerun acceptance. If no actual use, record the finding and kill the project. Do not invent use, accuracy on real data, or savings.

Verdict is pending the two-week evidence window; no real-use window has been completed. Record date, sample, metric, use count and reason in VERDICT.md. Expand for daily use or revenue, integrate for heavy sibling overlap, commercialise if a buyer would pay as-is, maintain as portfolio evidence otherwise, or kill if unused or unable to satisfy acceptance.
