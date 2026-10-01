import json
from agent_negotiation_protocol.core import evaluate
from agent_negotiation_protocol.fixtures import generate
from agent_negotiation_protocol.cli import load_directory, read
from agent_negotiation_protocol.report import render


def test_report_matches_ground_truth_exact(tmp_path):
    generate(tmp_path)
    result = json.loads(render(evaluate(load_directory(tmp_path)), "json"))
    expected = read(tmp_path / "expectations.json")
    assert result["counts"] == expected["counts"]
    assert result["total"] == expected["total"]
    assert sum(result["counts"].values()) == result["total"]


def test_report_zero_false_positives(tmp_path):
    generate(tmp_path)
    expected = read(tmp_path / "expectations.json")["statuses"]
    actual = json.loads(render(evaluate(load_directory(tmp_path)), "json"))
    for status in ("accepted", "blocked", "revision_required"):
        assert {o["id"] for o in actual["outcomes"] if o["status"] == status} == {k for k, v in expected.items() if v == status}


def test_report_carries_provenance_banner():
    for fmt in ("md", "json"):
        assert "Data provenance:" in render(evaluate([]), fmt)
        assert "entered by Henry" in render(evaluate([]), fmt)


def test_hypothetical_figures_labelled():
    for fmt in ("md", "json"):
        output = render(evaluate([]), fmt)
        assert "unmeasured" in output
        assert "no savings estimate" in output


def test_no_em_dashes_in_outputs():
    r = dict(id="a" + chr(0x2014), agent="a", plan="p", synthetic=True, challenges=[])
    for fmt in ("md", "json"):
        assert chr(0x2014) not in render(evaluate([r]), fmt)
