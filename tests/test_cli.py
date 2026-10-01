import json
import time
import pytest
from agent_negotiation_protocol.cli import main, read
from agent_negotiation_protocol.fixtures import write_json


def test_run_completes_on_fixture(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    start = time.perf_counter()
    assert main(["fixtures", "--out", "demo"]) == 0
    assert main(["run", "--input", "demo"]) == 0
    assert main(["report", "--format", "md", "--out", "report.md"]) == 0
    assert time.perf_counter() - start < 5


def test_empty_input_renders_without_traceback(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "empty").mkdir()
    assert main(["run", "--input", "empty"]) == 0
    assert main(["report"]) == 0
    assert "Total plans: 0" in capsys.readouterr().out


def test_malformed_input_named_error(tmp_path, capsys):
    (tmp_path / "bad.json").write_text('{\n bad', encoding="utf-8")
    assert main(["run", "--input", str(tmp_path)]) == 2
    output = capsys.readouterr().out
    assert "ParseError" in output and "bad.json" in output and "line 2" in output


def test_determinism_byte_identical(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    main(["fixtures", "--out", "demo"])
    main(["run", "--input", "demo"])
    first = (tmp_path / ".anp-results.json").read_bytes()
    main(["run", "--input", "demo"])
    assert first == (tmp_path / ".anp-results.json").read_bytes()
    main(["report", "--format", "json", "--out", "report.json"])
    first = (tmp_path / "report.json").read_bytes()
    main(["report", "--format", "json", "--out", "report.json"])
    assert first == (tmp_path / "report.json").read_bytes()


def test_cli_smoke_all_subcommands(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    for command in ("fixtures", "run", "report", "challenge", "revise"):
        with pytest.raises(SystemExit) as exc:
            main([command, "--help"])
        assert exc.value.code == 0
    write_json("plan.json", dict(id="p", agent="planner", plan="original", synthetic=True, challenges=[]))
    assert main(["challenge", "--record", "plan.json", "--agent", "reviewer", "--reason", "risk", "--out", "challenged.json"]) == 0
    assert main(["revise", "--record", "challenged.json", "--plan", "mitigated", "--resolve", "c1", "--out", "revised.json"]) == 0
    assert read("revised.json")["resolves"] == ["c1"]


def test_missing_input(tmp_path, capsys):
    assert main(["run", "--input", str(tmp_path / "missing")]) == 2
    assert "MissingInput" in capsys.readouterr().out


def test_report_write_failure_no_partial_files(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "empty").mkdir()
    main(["run", "--input", "empty"])
    before = set(tmp_path.iterdir())
    assert main(["report", "--out", "empty"]) == 2
    assert "WriteError" in capsys.readouterr().out
    assert before == set(tmp_path.iterdir())


def test_schema_drift_names_field(tmp_path, capsys):
    write_json(tmp_path / "records.json", {"synthetic": True, "records": [dict(id="p", agent="a", plan="p", synthetic=True, challenges=[], amount=-1)]})
    assert main(["run", "--input", str(tmp_path)]) == 2
    output = capsys.readouterr().out
    assert "SchemaError" in output and "amount" in output and "records.json" in output


def test_malformed_results_named_error(tmp_path, capsys):
    path = tmp_path / "results.json"
    write_json(path, [])
    assert main(["report", "--results", str(path)]) == 2
    assert "SchemaError" in capsys.readouterr().out
