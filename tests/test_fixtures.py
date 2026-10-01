from agent_negotiation_protocol.fixtures import generate
from agent_negotiation_protocol.cli import read, load_directory
from agent_negotiation_protocol.core import evaluate


def test_fixtures_labelled_synthetic(tmp_path):
    generate(tmp_path)
    for path in tmp_path.rglob("*.json"):
        assert path.read_text(encoding="utf-8").startswith("# SYNTHETIC")
        assert read(path)["synthetic"] is True
    assert all(r["synthetic"] for r in load_directory(tmp_path))


def test_fixture_ground_truth_matches_hand_computed(tmp_path):
    generate(tmp_path)
    actual = evaluate(load_directory(tmp_path))
    expected = read(tmp_path / "expectations.json")
    assert actual["total"] == 200
    assert actual["counts"] == expected["counts"] == {"accepted": 100, "revision_required": 50, "blocked": 50}
    assert {o["id"]: o["status"] for o in actual["outcomes"]} == expected["statuses"]


def test_corrupted_fixture_changes_computation(tmp_path):
    generate(tmp_path)
    records = load_directory(tmp_path)
    records[2]["challenges"] = []
    actual = evaluate(records)
    assert actual["counts"] == {"accepted": 101, "revision_required": 50, "blocked": 49}


def test_five_record_example(tmp_path):
    generate(tmp_path)
    assert evaluate(load_directory(tmp_path / "small"))["counts"] == {"accepted": 3, "revision_required": 1, "blocked": 1}
