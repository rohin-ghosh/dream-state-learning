# Recorded math-pool capacity and conditional collection cost

2026-09-14, old Builder supplement for astra2. Current MATH-RICH scale gates
remain CLOSED: zero eligible scale families, no fit. This is sizing guidance
for future decisions, not permission to rerun or expand the failed recipe.

## What is actually measured

The completed screen used32 fixed tasks,96 calls and0.2450055 assigned GPUh.
It admitted19 distinct response targets from16 tasks, totaling4228 target
tokens. These are worker-reported semantic decisions, not a new independent
content review. The companion script checks their target hashes, task/family
membership and counts against the published metadata.

Only recorded family counts and already-evaluated screen metadata are used.
No additional source questions, held-L1 contents, model/tokenizer calls,
reference answers or new grading are requested. The family counts are
inherited from the frozen preparation; this is not a fresh source census.

| Mining family | Recorded pool | Screen tasks | Remaining unscreened | Admitted rows | Rows/task in screen |
|---|---:|---:|---:|---:|---:|
| percentages |993|8|985|6|0.750|
| work_rates |444|8|436|3|0.375|
| fractional_quantities |1481|8|1473|5|0.625|
| group_accounting |2275|8|2267|5|0.625|
| Total |5193|32|5161|19|0.594 pooled|

Remaining means not part of this32-task screen. It does NOT certify absence
from model pretraining or every prior project exposure. Family labels remain
the existing coarse lexical routing, not semantic-disjointness certificates.

## Conditional projection, not a yield forecast or confidence interval

Assume each family's future admitted rows/task equals its observed8-task
rate. Also assume the completed32-task screen's assigned GPUh/task and three
calls/task repeat. Those assumptions are untested; a changed generation or
review recipe requires new measurement. No old targets are counted below.

| New balanced collection | New tasks | Conditional admitted rows | Screen-only assigned GPUh | Fits recorded remaining pool? |
|---|---:|---:|---:|---|
|128 tasks/family |512|304|3.92|yes|
|Smallest balanced sizing for1000 rows:422/family |1688|1002.25|12.92|yes, narrowly|
|Sizing for5000 rows:2106/family |8424|5001.75|64.50|NO|

Fractional rows express arithmetic extrapolation, not actual fractional or
guaranteed targets. A1000-row corpus is not reached by a single128-per-family
tranche at the observed rates. Its balanced sizing would use422 of436 remaining
work-rate questions. With unchanged routing, the largest balanced collection
is436 tasks/family (1744 tasks); its conditional yield is1035.5 rows.

Even exhausting all5161 remaining mining tasks with the observed family-specific
rates gives3239.75 conditional rows, not5000. This is NOT a hard maximum on
learnable rows: improved generation/admission yield or a separately authorized
source could change it. It is a warning against planning5000 rows by multiplying
one favorable family or assuming one task supplies one admissible target.

The screen has two correlated target forms for some tasks:19 admitted targets
come from16 distinct tasks. Corpus row counts therefore do not equal independent
problem coverage. Preserve source/task grouping in any future split and report
both quantities. This note does not impose a new definition of the existing
1000-row threshold or redefine source independence.

## Cost boundaries and next decision

Assigned GPUh/task includes the screen's observed setup/collection layout;
it is not an isolated generation-time measurement. Reusing a loaded actor
could change cost, as could prompt length, retries, task difficulty, and
record yield. No confidence bound or arbitrary efficiency factor is supplied.
Semantic review time, source/oracle adjudication, staging, earlier zero-call
engineering failures, fitting, retention and held evaluations are excluded.
Do not reuse SEQ266's shorter-terse fit timing as a validated rich-target fit
forecast. These collection numbers measure a different workload.

The immediate decision remains to improve a prospectively distinct qualifying
recipe, not to send the remaining pool blindly to the GPUs. If such a recipe
qualifies, budget from its measured admitted rows per task and family coverage;
use the current calculation as a baseline sensitivity case, not an approved
launch roster. No pool, rubric, threshold, control or allocation changed here.

## Reproduce

`python3 research_notes/analysis/2026-09-14_math_corpus_capacity.py`

The companion JSON records all input hashes, family-rate fractions and exact
scenarios. Assertions check19 unique target hashes/16 task IDs, original32-task
roster and family counts. Additional arithmetic checks reproduced the19-row
screen identity,5161-task inventory sum,3239.75 family-weighted projection,
minimal balanced cohort sizes, and unchanged empty eligible-scale list.
No independent reviewer or native scale experiment is claimed.
