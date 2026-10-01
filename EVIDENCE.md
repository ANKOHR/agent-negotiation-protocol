# Local acceptance evidence

Measured on 2026-10-01, Python 3.12.10, Windows, CPU only.

Installed CLI fixture generation, run, and Markdown report completed in 0.643307 seconds (wall clock measured with perf_counter, three subprocess launches). Limit: 5 seconds. This is elapsed execution time, not time saved.

27 pytest cases pass. All 200 planted statuses match independent expectations: 100 accepted, 50 revision required, 50 blocked. Status set comparison finds zero false positives and zero missed planted cases. Counts reconcile to 200. Corrupting a blocking fixture to remove its challenge changes accepted to 101 and blocked to 49.

Tests also cover empty input, malformed JSON, missing input, schema drift, duplicate IDs, future dates, extreme text, Unicode, real-input declarations, atomic write failure, deterministic bytes, all CLI subcommands, provenance and no em dashes. DEMO-REPORT.md preserves the measured synthetic demo report. No real-use evidence or savings measurement exists.
