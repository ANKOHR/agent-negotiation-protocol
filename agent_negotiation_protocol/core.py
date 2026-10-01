"""Pure validation and negotiation. No predictions or benefit estimates."""
from datetime import date

AS_OF = "2026-09-30"
MAX_TEXT = 100000

class ProtocolError(ValueError):
    """A named input or output failure."""


def fail(field, message):
    raise ProtocolError(f"SchemaError: {field}: {message}")


def text(value, field):
    if not isinstance(value, str) or not value.strip() or len(value) > MAX_TEXT:
        fail(field, f"expected nonempty text of at most {MAX_TEXT} characters")
    return value


def keys(obj, required, optional, field):
    if not isinstance(obj, dict):
        fail(field, "expected object")
    for key in sorted(set(required) - obj.keys()):
        fail(f"{field}.{key}", "missing field")
    for key in sorted(obj.keys() - set(required) - set(optional)):
        fail(f"{field}.{key}", "unknown field")


def validate(record):
    keys(record, ["id", "agent", "plan", "synthetic", "challenges"],
         ["revision", "resolves", "date", "entered_by"], "record")
    for field in ("id", "agent", "plan"):
        text(record[field], field)
    if type(record["synthetic"]) is not bool:
        fail("synthetic", "expected boolean")
    if not record["synthetic"] and record.get("entered_by") != "Henry":
        fail("entered_by", "real data must be explicitly entered by Henry")
    if "date" in record:
        try:
            parsed = date.fromisoformat(record["date"])
        except (TypeError, ValueError):
            fail("date", "expected ISO date")
        if parsed > date.fromisoformat(AS_OF):
            fail("date", f"future date beyond fixed reference {AS_OF}")
    if not isinstance(record["challenges"], list):
        fail("challenges", "expected list")
    seen = set()
    for challenge in record["challenges"]:
        keys(challenge, ["id", "agent", "reason", "severity"], [], "challenge")
        for field in ("id", "agent", "reason"):
            text(challenge[field], f"challenge.{field}")
        if challenge["severity"] not in ("blocking", "advisory"):
            fail("challenge.severity", "expected blocking or advisory")
        if challenge["id"] in seen:
            fail("challenge.id", "duplicate id")
        seen.add(challenge["id"])
    resolves = record.get("resolves", [])
    if not isinstance(resolves, list) or any(not isinstance(x, str) for x in resolves):
        fail("resolves", "expected list of challenge ids")
    if len(set(resolves)) != len(resolves) or set(resolves) - seen:
        fail("resolves", "duplicate or unknown challenge id")
    if "revision" in record:
        text(record["revision"], "revision")
    elif resolves:
        fail("revision", "resolutions require a revision")
    return record


def evaluate(records):
    seen = set()
    outcomes = []
    for record in sorted(records, key=lambda r: str(r.get("id", "")) if isinstance(r, dict) else ""):
        validate(record)
        if record["id"] in seen:
            fail("id", f"duplicate id {record['id']}")
        seen.add(record["id"])
        unresolved = [c for c in record["challenges"] if c["id"] not in record.get("resolves", [])]
        status = "blocked" if any(c["severity"] == "blocking" for c in unresolved) else "revision_required" if unresolved else "accepted"
        outcomes.append({"id": record["id"], "status": status,
                         "unresolved_challenge_ids": sorted(c["id"] for c in unresolved),
                         "synthetic": record["synthetic"]})
    counts = {s: sum(o["status"] == s for o in outcomes) for s in ("accepted", "revision_required", "blocked")}
    return {"total": len(records), "counts": counts, "outcomes": outcomes,
            "provenance": {"synthetic_records": sum(r["synthetic"] for r in records),
                           "real_records_entered_by_Henry": sum(not r["synthetic"] for r in records)},
            "benefits": "Time and money saved are unmeasured; no savings estimate is reported.",
            "reference_date": AS_OF}


def challenge(record, agent, reason, severity):
    validate(record)
    result = dict(record)
    used = {c["id"] for c in record["challenges"]}
    n = 1
    while f"c{n}" in used:
        n += 1
    result["challenges"] = record["challenges"] + [{"id": f"c{n}", "agent": agent, "reason": reason, "severity": severity}]
    return validate(result)


def revise(record, plan, resolves):
    result = dict(record, revision=plan, resolves=sorted(set(record.get("resolves", []) + resolves)))
    return validate(result)
