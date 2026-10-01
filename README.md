# Agent Negotiation Protocol

Deterministic local Python CLI for explicit plan challenges and revisions. CPU only, no network calls, no models, no predictions.

## Quickstart

Python 3.10+ and setuptools are required. No runtime dependencies.

```powershell
python -m pip install --no-deps --no-build-isolation -e .
anp fixtures --out demo
anp run --input demo
anp report --format md
python -m pytest -q
```

If Windows pip warns that its Scripts directory is not on PATH, add the directory shown in that warning to your session PATH. Alternatively use `python -m agent_negotiation_protocol.cli` in place of `anp`.

For a five-record synthetic example, run `anp run --input demo/small` then `anp report --format json`. Counts: 3 accepted, 1 revision required, 1 blocked. The full fixture contains 200 records. Results default to `.anp-results.json` in the working directory. A failed run retains the last successful results; inspect `input_directory` in the JSON report before relying on an existing result.

## Input format

Input directories contain UTF-8 JSON envelopes with exactly `synthetic` (boolean) and `records` (list). The reserved `expectations.json` is ignored, as are subdirectories. Other file formats are rejected. Whole-line comments beginning with `#` in column one are allowed as a labelled JSON extension.

```json
{
  "synthetic": true,
  "records": [
    {
      "id": "plan-1",
      "agent": "planner",
      "plan": "Back up files",
      "synthetic": true,
      "challenges": [
        {"id": "c1", "agent": "reviewer", "reason": "Verify backup", "severity": "blocking"}
      ],
      "revision": "Verify backup before editing",
      "resolves": ["c1"]
    }
  ]
}
```

Required record fields: `id`, `agent`, `plan`, `synthetic`, `challenges`. Optional: `revision`, `resolves`, `date`, `entered_by`. Challenge fields are exactly `id`, `agent`, `reason`, `severity`. Text must be nonempty and at most 100,000 characters. Unicode and escaped Windows paths work. Plan IDs are unique across files; challenge IDs are unique within a plan. Unknown fields, including monetary amounts, are rejected. This tool has no monetary model.

Severity is `blocking` or `advisory`. Resolutions must name existing challenge IDs without duplicates and require a nonempty revision. Optional ISO dates cannot exceed the fixed reference date `2026-09-30` from the build brief. This date policy is fixed for reproducibility and must be explicitly updated for later trials.

Real data requires `synthetic: false` in envelope and records and `entered_by: "Henry"` in each record. This is an operator declaration, not identity verification. Keep real inputs and trial results outside the repo.

Any unresolved blocking challenge yields `blocked`. Otherwise unresolved advisory challenges yield `revision_required`. Otherwise the plan is `accepted`. Revision text alone does not resolve a challenge. Explicit resolutions are declarations, not proof that objections were addressed. Acceptance does not imply safety or success.

## Subcommands

Every subcommand has help and examples.

| Command | Example |
| --- | --- |
| fixtures | `anp fixtures --out demo` |
| run | `anp run --input demo --results results.json` |
| report | `anp report --results results.json --format md --out report.md` |
| challenge | `anp challenge --record plan.json --agent reviewer --reason "Missing rollback" --severity blocking --out challenged.json` |
| revise | `anp revise --record challenged.json --plan "Add rollback" --resolve c1 --out revised.json` |

Challenge and revise read and write one standalone record object, without an envelope. Wrap the output record in an envelope to use directory input. Repeat `--resolve` for multiple challenges; earlier resolutions are retained. Explicit output paths may be overwritten.

## Architecture

```text
local JSON -> CLI parsing -> pure core validation and evaluation -> atomic results
results -> report renderer -> Markdown / JSON provenance report
fixture generator -> labelled cases + independent expected statuses
standalone record -> challenge / revise -> validated standalone record
```

Core contains no I/O. JSON keys and outcomes have stable order. Fixtures use enumeration, so no random seed is needed. Identical input paths and contents yield identical output bytes. Timing is recorded separately, never inserted into deterministic reports. Reports replace Unicode U+2014 with ASCII hyphens.

## Honesty boundary and fixture labelling

Every generated fixture file has a synthetic header comment and `synthetic: true`; each record carries that label too. Every report banner counts synthetic records and real records entered by Henry. JSON preserves the input directory. Counts are computed from explicit inputs; the engine never reads expectations.

There are four independently enumerated groups of 50: clean, advisory unresolved, blocking unresolved, and blocking resolved. Hand-computed totals: 100 accepted, 50 revision required, 50 blocked. Each outcome lists its plan ID and unresolved challenge IDs for tracing to the input. Fixture content is illustrative, not evidence of actual agent judgment.

Time and money saved are unmeasured; no savings estimate is reported. No hypothetical numerical benefits are shipped. Passing synthetic tests proves rule execution, not real-world accuracy.

## Failure modes

Bad JSON produces `ParseError` with file and line. Missing directories produce `MissingInput` with a usage hint. Schema drift produces `SchemaError` naming the field and input file. Schema validation uses line 1 as envelope context, not precise token position. Duplicates, future dates, extreme strings, and negative amounts are rejected, not silently dropped. Empty input produces zeros. Errors exit nonzero without tracebacks. Report/results writes use temporary files and atomic replacement; failures leave no partial file. Results files are generated artifacts, not authenticated evidence.

## Evidence-based improvement hook

See EVIDENCE.md for local acceptance evidence. No real trial has occurred. Start a two-week window with Henry's first real use. Privately record dates, run count, hand-checked sample size, and incorrect statuses. Primary metric: incorrect statuses divided by hand-checked statuses. An empty sample has no measurable accuracy. If measured errors exceed 10 percent, fix the largest failure cause and recheck or kill with a reason. If unused, record non-use and kill. Time saved requires a measured baseline and comparable workload.

## Verdict

Pending the two-week real-use window. Record date, evidence, verdict and reason in VERDICT.md. Expand for daily use or revenue; integrate for heavy sibling overlap; commercialise if a buyer would pay as-is; maintain as portfolio evidence otherwise; kill for non-use or unmet acceptance criteria. No final verdict is invented before evidence exists. Publishing is a separate verification step and is not performed by this build.
