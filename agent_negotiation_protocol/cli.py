"""Local file CLI with atomic output writes and named failures."""
import argparse
import json
import os
from pathlib import Path
import tempfile
from .core import ProtocolError, evaluate, challenge, revise
from .fixtures import generate
from .report import render


def read(path):
    try:
        content = Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise ProtocolError(f"InputError: {path}: {exc}") from exc
    # Retain line offsets for the labelled JSON extension.
    content = "\n".join("" if line.startswith("#") else line for line in content.split("\n"))
    try:
        return json.loads(content)
    except json.JSONDecodeError as exc:
        raise ProtocolError(f"ParseError: {path}: line {exc.lineno}: {exc.msg}") from exc


def atomic_write(path, content):
    temp = None
    try:
        path = Path(path)
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n", dir=path.parent, delete=False) as stream:
            temp = stream.name
            stream.write(content)
        os.replace(temp, path)
    except OSError as exc:
        raise ProtocolError(f"WriteError: {path}: {exc}") from exc
    finally:
        if temp and os.path.exists(temp):
            os.unlink(temp)


def load_directory(directory):
    directory = Path(directory)
    if not directory.is_dir():
        raise ProtocolError(f"MissingInput: {directory}: use anp fixtures --out <dir> or supply an existing directory")
    records = []
    for path in sorted(directory.iterdir()):
        if path.name == "expectations.json" or path.is_dir():
            continue
        if path.suffix != ".json":
            raise ProtocolError(f"SchemaError: {path}: unsupported file format; use JSON")
        data = read(path)
        if not isinstance(data, dict) or set(data) != {"synthetic", "records"} or type(data.get("synthetic")) is not bool or not isinstance(data.get("records"), list):
            raise ProtocolError(f"SchemaError: {path}: expected synthetic and records fields")
        for record in data["records"]:
            try:
                evaluate([record])
                if record["synthetic"] != data["synthetic"]:
                    raise ProtocolError("SchemaError: synthetic: envelope mismatch")
            except ProtocolError as exc:
                raise ProtocolError(f"{path}: line 1 (schema validation): {exc}") from exc
        records.extend(data["records"])
    return records


def main(argv=None):
    parser = argparse.ArgumentParser(description="Deterministic local plan negotiation; no estimates or model calls.")
    subs = parser.add_subparsers(dest="command", required=True)
    p = subs.add_parser("fixtures", help="Generate 200 labelled synthetic plans", epilog="Example: anp fixtures --out demo")
    p.add_argument("--out", required=True)
    p = subs.add_parser("run", help="Compute negotiation outcomes", epilog="Example: anp run --input demo")
    p.add_argument("--input", required=True)
    p.add_argument("--results", default=".anp-results.json")
    p = subs.add_parser("report", help="Render counts and provenance", epilog="Example: anp report --format md")
    p.add_argument("--format", choices=["md", "json"], default="md")
    p.add_argument("--results", default=".anp-results.json")
    p.add_argument("--out")
    p = subs.add_parser("challenge", help="Append an identified challenge to a single record", epilog="Example: anp challenge --record plan.json --agent reviewer --reason unsafe --severity blocking --out challenged.json")
    p.add_argument("--record", required=True)
    p.add_argument("--agent", required=True)
    p.add_argument("--reason", required=True)
    p.add_argument("--severity", choices=["advisory", "blocking"], default="blocking")
    p.add_argument("--out", required=True)
    p = subs.add_parser("revise", help="Record a revision and explicitly resolve challenge IDs", epilog="Example: anp revise --record challenged.json --plan safer --resolve c1 --out revised.json")
    p.add_argument("--record", required=True)
    p.add_argument("--plan", required=True)
    p.add_argument("--resolve", action="append", default=[])
    p.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "fixtures":
            generate(args.out)
            print("Generated 200 synthetic fixture records and labelled ground truth.")
        elif args.command == "run":
            records = load_directory(args.input)
            result = evaluate(records)
            result["input_directory"] = str(Path(args.input))
            atomic_write(args.results, json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
            print(f"Computed {result['total']} plans. Synthetic: {result['provenance']['synthetic_records']}; real entered by Henry: {result['provenance']['real_records_entered_by_Henry']}.")
        elif args.command == "report":
            result = read(args.results)
            try:
                if not isinstance(result, dict):
                    raise ValueError("expected results object")
                if not isinstance(result["outcomes"], list):
                    raise ValueError("outcomes must be a list")
                counts = {s: 0 for s in ("accepted", "revision_required", "blocked")}
                provenance = {"synthetic_records": 0, "real_records_entered_by_Henry": 0}
                seen = set()
                for outcome in result["outcomes"]:
                    if not isinstance(outcome["id"], str) or outcome["id"] in seen:
                        raise ValueError("invalid or duplicate outcome id")
                    seen.add(outcome["id"])
                    counts[outcome["status"]] += 1
                    if type(outcome["synthetic"]) is not bool or not isinstance(outcome["unresolved_challenge_ids"], list):
                        raise ValueError("invalid outcome fields")
                    provenance["synthetic_records" if outcome["synthetic"] else "real_records_entered_by_Henry"] += 1
                if result["counts"] != counts or result["total"] != len(seen) or result["provenance"] != provenance:
                    raise ValueError("counts do not reconcile with outcomes")
                if result["benefits"] != "Time and money saved are unmeasured; no savings estimate is reported.":
                    raise ValueError("unsupported benefits field")
            except (KeyError, TypeError, ValueError) as exc:
                raise ProtocolError(f"SchemaError: {args.results}: results: {exc}") from exc
            output = render(result, args.format)
            if args.out:
                atomic_write(args.out, output)
            else:
                print(output, end="")
        else:
            record = read(args.record)
            result = challenge(record, args.agent, args.reason, args.severity) if args.command == "challenge" else revise(record, args.plan, args.resolve)
            atomic_write(args.out, json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
            print(f"Wrote {args.command} record; synthetic: {str(result['synthetic']).lower()}.")
        return 0
    except (ProtocolError, OSError, KeyError, TypeError, ValueError) as exc:
        print(str(exc).replace(chr(0x2014), "-"))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
