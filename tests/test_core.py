import pytest
from agent_negotiation_protocol.core import evaluate, ProtocolError, challenge, revise


def record():
    return dict(id="one", agent="planner", plan="Do work", synthetic=True, challenges=[])


def test_negotiation_lifecycle():
    r = challenge(record(), "reviewer", "missing guard", "blocking")
    assert evaluate([r])["counts"]["blocked"] == 1
    r = revise(r, "Add guard", ["c1"])
    assert evaluate([r])["counts"]["accepted"] == 1


@pytest.mark.parametrize("field,value", [("amount", -1), ("date", "2099-01-01"), ("plan", "x" * 100001), ("synthetic", 1), ("resolves", ["unknown"])], ids=["negative", "future", "extreme", "boolean", "resolution"])
def test_rejects_adversarial_values(field, value):
    r = record()
    r[field] = value
    with pytest.raises(ProtocolError, match=field if field != "resolves" else "resolves"):
        evaluate([r])


def test_duplicate_ids():
    with pytest.raises(ProtocolError, match="duplicate id"):
        evaluate([record(), record()])


def test_handles_unicode_and_long_inputs():
    r = record()
    r["plan"] = "日本語 café C:\\Users\\Henry " + "z" * 90000
    r["id"] = "東京"
    assert evaluate([r])["outcomes"][0]["id"] == "東京"


def test_real_data_requires_henry():
    r = dict(record(), synthetic=False)
    with pytest.raises(ProtocolError, match="entered_by"):
        evaluate([r])
    r["entered_by"] = "Henry"
    assert evaluate([r])["provenance"]["real_records_entered_by_Henry"] == 1
