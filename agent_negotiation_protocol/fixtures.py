"""Synthetic planted cases; no random generator or inferred expectations."""
import json
from pathlib import Path

HEADER = "# SYNTHETIC fixture data, not real agent activity\n"


def write_json(path, value, labelled=False):
    Path(path).write_text((HEADER if labelled else "") + json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def generate(out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    records = []
    for n in range(200):
        group = n % 4
        r = {"id": f"p{n:03}", "agent": "planner", "plan": f"Execute explicit plan {n}", "synthetic": True, "challenges": []}
        if group:
            r["challenges"] = [{"id": "c1", "agent": "reviewer", "reason": "Planted constraint violation", "severity": "advisory" if group == 1 else "blocking"}]
        if group == 3:
            r.update(revision="Address the planted constraint", resolves=["c1"])
        records.append(r)
    write_json(out / "records.json", {"synthetic": True, "records": records}, True)
    # Four groups of 50: clean + resolved = 100, advisory = 50, blocking = 50.
    expected = {"synthetic": True, "total": 200, "counts": {"accepted": 100, "revision_required": 50, "blocked": 50},
                "statuses": {f"p{n:03}": ("accepted", "revision_required", "blocked", "accepted")[n % 4] for n in range(200)}}
    write_json(out / "expectations.json", expected, True)
    small = {"synthetic": True, "records": records[:5]}
    (out / "small").mkdir(exist_ok=True)
    write_json(out / "small" / "records.json", small, True)
