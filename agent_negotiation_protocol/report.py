"""Render measured input counts and explicit provenance."""
import json


def render(result, format="md"):
    p = result["provenance"]
    banner = f"Data provenance: {p['synthetic_records']} synthetic fixture records; {p['real_records_entered_by_Henry']} real records explicitly entered by Henry. Counts are computed from supplied inputs."
    if format == "json":
        output = json.dumps(dict(result, banner=banner), ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    else:
        lines = ["# Agent Negotiation Protocol", "", banner, "", f"Total plans: {result['total']}"]
        lines += [f"{key}: {value}" for key, value in result["counts"].items()]
        lines += ["", result["benefits"], "", "| Plan ID | Status | Unresolved challenge IDs |", "| --- | --- | --- |"]
        def safe(value):
            return str(value).replace("|", "\\|").replace("\n", " ").replace("\r", " ")
        lines += [f"| {safe(o['id'])} | {o['status']} | {safe(', '.join(o['unresolved_challenge_ids']))} |" for o in result["outcomes"]]
        output = "\n".join(lines) + "\n"
    return output.replace(chr(0x2014), "-")
