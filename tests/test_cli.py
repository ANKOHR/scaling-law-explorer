import json
import subprocess
import sys
import time
from pathlib import Path
from scaling_law_explorer.cli import main, atomic_write
from scaling_law_explorer.fixtures import generate

ROOT=Path(__file__).resolve().parents[1]
def invoke(*args):
    return subprocess.run([sys.executable,"-m","scaling_law_explorer.cli",*args],cwd=ROOT,capture_output=True,text=True,encoding="utf-8")

def test_run_completes_on_fixture(tmp_path):
    generate(tmp_path/"input")
    start=time.perf_counter()
    assert main(["run","--input",str(tmp_path/"input"),"--results",str(tmp_path/"results.json")]) == 0
    assert time.perf_counter()-start < 5

def test_empty_input_renders_without_traceback(tmp_path,capsys):
    state=tmp_path/"state.json"
    assert main(["run","--input",str(tmp_path),"--results",str(state)]) == 0
    assert main(["report","--results",str(state)]) == 0
    assert "Records: 0" in capsys.readouterr().out

def test_malformed_input_named_error(tmp_path,capsys):
    (tmp_path/"bad.jsonl").write_text("# synthetic: true\n{bad}\n")
    assert main(["run","--input",str(tmp_path)]) == 2
    error=capsys.readouterr().err
    assert "ParseError" in error and "bad.jsonl: line 2" in error

def test_determinism_byte_identical(tmp_path):
    generate(tmp_path/"input")
    state=tmp_path/"state.json"
    args=["run","--input",str(tmp_path/"input"),"--results",str(state)]
    assert main(args)==0
    first=state.read_bytes()
    assert main(args)==0
    assert state.read_bytes()==first
    for fmt in ("md","json"):
        a=invoke("report","--results",str(state),"--format",fmt)
        b=invoke("report","--results",str(state),"--format",fmt)
        assert a.returncode==b.returncode==0 and a.stdout==b.stdout

def test_cli_smoke_all_subcommands(tmp_path):
    directory=tmp_path/"input"
    state=tmp_path/"state.json"
    assert invoke("fixtures","--out",str(directory)).returncode==0
    for command in ("run","fit","validate"):
        args=[command,"--input",str(directory)]
        if command=="run": args += ["--results",str(state)]
        assert invoke(*args).returncode==0
    assert invoke("report","--results",str(state)).returncode==0
    for command in ("fixtures","run","report","fit","validate"):
        assert "Example:" in invoke(command,"--help").stdout

def test_missing_input(tmp_path,capsys):
    assert main(["run","--input",str(tmp_path/"missing")])==2
    assert "MissingInput" in capsys.readouterr().err

def test_report_write_failure_no_partial_files(tmp_path,capsys):
    generate(tmp_path/"input")
    state=tmp_path/"state.json"
    main(["run","--input",str(tmp_path/"input"),"--results",str(state)])
    before=set(tmp_path.iterdir())
    assert main(["report","--results",str(state),"--out",str(tmp_path/"absent"/"report.md")])==2
    assert "ReportWriteError" in capsys.readouterr().err
    assert set(tmp_path.iterdir())==before

def test_csv_input(tmp_path):
    (tmp_path/"real.csv").write_text("id,experiment,compute,loss,synthetic,source\na,trial,1,16,false,Henry\nb,trial,2,8,false,Henry\n",encoding="utf-8")
    assert main(["fit","--input",str(tmp_path)])==0
