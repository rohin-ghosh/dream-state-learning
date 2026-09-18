# Original C2 actual training audit: sleeps52–63

Published 2026-09-18 06:22 UTC. Read-only; no learner, parent, control or signal changes.
Full-target manual semantic labels are independent of Fable and the R213 heuristic.
Machine-readable exact sources, stages, response/target/record hashes, first150
Unicode characters, exclusions and UPDATE indices are in `AUDIT.json` and `ROWS.csv`.
Full raw targets and manual notes are private and excluded from version control.

| Sleep | Candidates | Trained unique | Excluded | Actual presentations | COMPLETE index |
|---:|---:|---:|---:|---:|---:|
|52|5|5|0|80|5975|
|53|3|3|0|48|6055|
|54|3|2|1|32|6122|
|55|3|3|0|48|6202|
|56|3|3|0|48|6283|
|57|3|3|0|48|6365|
|58|3|2|1|32|6432|
|59|4|4|0|64|6543|
|60|4|4|0|64|6647|
|61|3|2|1|32|6714|
|62|4|3|1|48|6807|
|63|3|3|0|48|6892|
|TOTAL|41|37|4|592|—|

Every per-sleep UPDATE source/count agrees with SLEEP_COMPLETE presentations and
optimizer_steps. These are executed-update receipts, not merely candidate or dose
counts. Each retained target has16 presentations; no rehearsal in this interval.

| Manual full-row class | Candidates | Trained unique | Excluded | Actual presentations |
|---|---:|---:|---:|---:|
|META_INTENT_COMPLIANCE|20|19|1|304|
|SUBSTANTIVE_CONTENT|10|7|3|112|
|MIXED|10|10|0|160|
|UNCERTAIN|1|1|0|16|

UNCERTAIN is RESPONSE6573: a short plot synopsis followed by promises; plausible
alternatives META or MIXED remain explicit. MIXED is not silently counted as either
pure content or pure meta. Content is not a correctness, execution or quality claim.

Excluded candidates: sleep54 ACT6070 and sleep58 ACT6381, fullwidth glyph in fenced
code; sleep61 LEARN6669 and sleep62 THINK6731, English-target script quarantine.
These four were candidates but received zero recorded training presentations.

## Timing and scope

CHILD_COMPACTION5889 occurred at02:53:07.145 UTC. All five sleep52 targets were
generated before it (last02:53:05.605) and trained afterward. Therefore “training
since compaction” is not the same as “targets generated since compaction.”

Each UPDATE also co-trains four fixed ANCHOR families (code, concise_answer, math,
simulated_tools), with anchor objective weight0.25. Counts here classify only the
self-generated child targets, not anchor content or all token/loss exposure.

Sleep numbers are SLEEP_COMPLETE.document.cycle, not response index, runtime-local
R189 outcome counter, or journal segment number. No causal conclusion is drawn.

Raw evidence SHA256: `10c36bcf15cf76aff5fdb6c650d24ce73ff4ef62ee4064383191a68332a46a53`.
The sleep40–latest extension is separately reported, retaining rehearsal and pending
sleep distinctions rather than merging them into these totals.
