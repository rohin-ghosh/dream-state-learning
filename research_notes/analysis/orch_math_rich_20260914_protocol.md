# MATH-RICH attempt1 — prospective checked-answer feasibility screen

Declared2026-09-14 before native generation. W1 scope; sole node2 GPUs4–7.
Canonical launch details and proposed budget first posted in
research_loop/workers/MATH_RICH.md before task selection. This is a DEV screen,
not evidence of learning, unobserved reasoning, H1/H2 or novel-task transfer.

## Dataset, families and fixed denominator

Public source: openai/grade-school-math, grade_school_math/data/train.jsonl,
downloaded2026-09-14 from raw.githubusercontent.com (master reference; immutable
local SHA25617f347dc51477c50d4efb83959dbb7c56297aba886e5544ee2aaed3024813465).
This is existing public benchmark data, so base pretraining contamination is
unknown. No reference reasoning enters any model prompt or target; only the
question and separately parsed numeric answer are retained in TASKS.json.
Original download retained privately as source evidence. No public solutions
are teacher targets. Exact Fraction arithmetic compares the last FINAL value
without eval, float tolerance or outcome keyword heuristics.

L1 mining: percentages, work_rates, fractional_quantities, group_accounting.
Held L1-validation: geometry_measurement, age_time_relations. Routing precedes
hash ordering and is frozen in organism_v6/orch_math_rich.py: held priorities
first, then mining priorities as listed. These are coarse question-structure
families, not proof of concept disjointness. No L2/held-L3 data or contents.
32 unique questions,8/family, hash-order seed MATH_RICH_SCREEN_V1; no replacement,
failed calls remain non-success in their original denominator. Four GPUs each
take task positions modulo4. Rich/terse order alternates prospectively.

Eligible family requires all16 paired calls present and rich outcome successes
strictly greater than terse successes among the same8 tasks. This very small
screen is feasibility evidence, not a statistically powered superiority claim.
No post-hoc selection of denominator, best adapter, or easier retry tasks.
The deterministic non-model reference for any later held readout is the
constant answer0, with failures counted, plus unchanged portable37ec as frozen
model reference; no held output has yet been requested. Freeze any eventual
fit/readout protocol separately before1000+ row training.

## Collection and content admission

Frozen Qwen2.5-7B-Instruct base plus portable37ec, manifest
5e675c309b202625a6ddf1d36c1a58f51ef656985821cec1cd6123424d927469.
Existing helper contracts, adapter-state hashes and local base/tokenizer
inventories must match. Upstream revision identity remains unresolved as in
handover; no ancestor rebuild. Native generation deterministic, single GPU.
Context<=2048, generated<=512, admitted child rich turn150–400 tokens,
<=3 rich turns/task (<6). Terse control generated<=64, not a training target.

Per task: initial terse and rich; if rich answer is wrong, one correction using
oracle rejection feedback (no gold answer/reasoning); if rich or correction is
correct, one own-record call. At most4 calls/task and128 total. Preserve raw
messages, token IDs, terminal/truncation state, all outcomes and failures.
Rows have three classes: rich successes; correction/revision/lesson successes;
own records. Answer-only child outputs never bypass the150-token admission.

Semantic reading is mandatory, with exact target SHA and quoted evidence:
first-person account; operations correctly grounded in given quantities;
checkable expectation or concrete consistency check; reusable nontrivial
operation or lesson; no false premises, invented evidence or generic padding.
Correction PASS also requires meaningful revision of the previous error.
Record PASS requires reusable operational content, not just an answer restated.
Outcome, length, headings, fluent prose and first-person keywords are not
semantic admission. Every substantive FAIL/UNRESOLVED and its original bytes
is retained. PASS without all substantive axes fails closed in admit().
Guidance/system/oracle text is absent from student_prefix. The unchanged
actual child response is the only possible target, with user/previous-turn
prefix fully masked in any future fit. Successful rows from gap-ineligible
families may be reviewed but are not admitted into this scale pool.

Scale criterion: eligible family plus>=8 semantic-PASS distinct rows across
>=4 tasks, no unresolved provenance/contamination defect. Next tranche128 new
tasks per eligible family, never duplicating the32 original tasks. Report
projection before1000+ rows; do not invent padding copies. One complete clean
gap-null deallocates this screen, not disproves the thesis. Abort/failure is
not a scientific null. No fit below1000 admitted distinct rows; later fits
must use the W1 same-batch FULL/new-labels-masked inputs, identical denominator,
16 presentations/new targets plus legacy rehearsal, fresh-process deterministic
held uncoached readout, oldW0/W8/audit>=15/16 each. No fit is launched here.

## Runtime and release

Root orch_math_rich_20260914_attempt1; packaging under repository
gpu_artifacts_local on /data (not VM root).45min/shard timeout plus60s grace,
<=3.1 assigned GPU-hours total. Actual node2 lease deadline must be supplied
from hosts.env and exceeds the bound plus6h margin. Never infer deadline from
old launcher comments. Existing same-UID /proc scanner and hash-bound service
exceptions plus global nvidia compute PID check immediately before launch;
known limitation: other users' idle CVD reservations are not readable and
exclusive W1 ownership supplies scheduler-level protection. Unknown owners
are never killed. Guardian targets only its own timed process group. Capture
PID, /proc CVD, UUID and source hashes. Main owns shared notebook publication;
workers may run after W1 publication, own CPU/provenance checks and dated
pre-GPU notebook record are committed/pushed. Reader is asynchronous.
