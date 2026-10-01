"""Local-only CLI. Example: sle2 fixtures --out demo; sle2 run --input demo."""
import argparse
import csv
import io
import json
import os
from pathlib import Path
import sys
import tempfile
from .core import analyze, validate, SchemaError
from .fixtures import generate
from .report import render, safe

class InputError(ValueError):
    pass

def load(directory):
    path = Path(directory)
    if not path.is_dir():
        raise InputError(f"MissingInput: {path}; use --input <existing directory>")
    rows = []
    seen = set()
    def append(row, file, line):
        if row["id"] in seen:
            raise InputError(f"SchemaError: {file}: line {line}: id: duplicate {row['id']}")
        seen.add(row["id"])
        rows.append(row)
    for file in sorted(path.iterdir()):
        if file.name == "expectations.json" or not file.is_file():
            continue
        if file.suffix.lower() not in (".jsonl", ".csv"):
            raise InputError(f"SchemaError: {file}: line 1: unsupported file format; use JSONL or CSV")
        try:
            text = file.read_text(encoding="utf-8-sig")
        except (OSError, UnicodeError) as exc:
            raise InputError(f"ParseError: {file}: line 1: {exc}") from None
        if file.suffix.lower() == ".jsonl":
            entries = ((i, line) for i,line in enumerate(text.splitlines(), 1) if line.strip() and not line.lstrip().startswith("#"))
            for i,line in entries:
                try:
                    row = json.loads(line)
                except ValueError as exc:
                    raise InputError(f"ParseError: {file}: line {i}: {exc}") from None
                try:
                    validate([row])
                except SchemaError as exc:
                    raise InputError(f"SchemaError: {file}: line {i}: {exc}") from None
                append(row, file, i)
        else:
            reader = csv.DictReader(io.StringIO(text), strict=True)
            try:
                for row in reader:
                    try:
                        if row.get("synthetic") not in ("true", "false"):
                            raise ValueError("synthetic must be true or false")
                        row["synthetic"] = row["synthetic"] == "true"
                        for field in ("compute", "loss"):
                            row[field] = float(row[field])
                        validate([row])
                    except (ValueError, TypeError, KeyError) as exc:
                        raise InputError(f"SchemaError: {file}: line {reader.line_num}: {exc}") from None
                    append(row, file, reader.line_num)
            except csv.Error as exc:
                raise InputError(f"ParseError: {file}: line {reader.line_num}: {exc}") from None
    return rows

def atomic_write(path, text):
    path = Path(path)
    temp = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n", dir=path.parent, delete=False) as stream:
            temp = stream.name
            stream.write(text)
        os.replace(temp, path)
    finally:
        if temp and os.path.exists(temp):
            os.unlink(temp)

def main(argv=None):
    parser = argparse.ArgumentParser(prog="sle2", description="Compute observed scaling laws locally, CPU only.")
    subs = parser.add_subparsers(dest="command", required=True)
    f = subs.add_parser("fixtures", help="Generate 200 synthetic observations", epilog="Example: sle2 fixtures --out demo")
    f.add_argument("--out", required=True)
    for command, helptext in (("run", "Analyze and persist results"), ("fit", "Fit observed log-log slopes"), ("validate", "Validate input schema and duplicate ids")):
        s = subs.add_parser(command, help=helptext, description=helptext, epilog=f"Example: sle2 {command} --input demo")
        s.add_argument("--input", required=True)
        if command == "run":
            s.add_argument("--results", default=".sle2-results.json")
    r = subs.add_parser("report", help="Render stored results with provenance", epilog="Example: sle2 report --format md")
    r.add_argument("--format", choices=("md", "json"), default="md")
    r.add_argument("--results", default=".sle2-results.json")
    r.add_argument("--out")
    args = parser.parse_args(argv)
    try:
        if args.command == "fixtures":
            generate(args.out)
            print("Generated 200 synthetic fixture records.")
        elif args.command in ("run", "fit", "validate"):
            rows = load(args.input)
            result = analyze(rows)
            if args.command == "run":
                atomic_write(args.results, json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2)+"\n")
            if args.command == "validate":
                print(f"Valid records: {len(rows)}; synthetic: {result['synthetic_records']}; user-declared real: {result['real_records']}")
            else:
                print(render(result, "json"), end="")
        else:
            try:
                result = json.loads(Path(args.results).read_text(encoding="utf-8"))
                output = render(result, args.format)
            except (ValueError, KeyError, TypeError, AttributeError) as exc:
                raise InputError(f"SchemaError: {args.results}: invalid result file: {exc}") from None
            if args.out:
                atomic_write(args.out, output)
            else:
                print(output, end="")
        return 0
    except (InputError, SchemaError) as exc:
        print(safe(str(exc)), file=sys.stderr)
    except OSError as exc:
        label = "ReportWriteError" if args.command == "report" and args.out else "FileError"
        print(safe(f"{label}: {exc}; check input or output path"), file=sys.stderr)
    return 2

if __name__ == "__main__":
    sys.exit(main())
