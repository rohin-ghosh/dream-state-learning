# MATH-REPLICATION prospective protocol journal

Initial freeze journal: 2026-09-14T22:28Z, before any outcome access.
Assignment f0f53343. Independent skeptical assessor, not original author.

## Fixed design

Question: rich versus terse checked-answer performance AND semantically
admissible records on 32 fresh public GSM8K train tasks, eight per original
mining family. Original routing and exact prompts retained; selection uses
MATH_REPLICATION_FRESH_V1_20260914, excludes original TASKS IDs only, no outcome
selection, replacement, reference-rationale use, fit, or scale. Public pretraining
contamination remains unknown; this is not learning or novel-family transfer.

Frozen Qwen2.5-7B-Instruct with unchanged portable37ec V3. Expected portable
manifest SHA256 5e675c309b202625a6ddf1d36c1a58f51ef656985821cec1cd6123424d927469.
Verify mounted named_parameters hashes, never exported PEFT key hashes.
apply_chat_template(return_dict=False). Same task paired inference, alternating
order, original rich/terse/correction/record prompts. <=128 calls total,
context2048/generated512 (terse64 per original), rich150–400 tokens, <=6 turns.
Failures/ambiguous gold retain fixed denominator32 and family denominator8.

## Independently specified analysis

Primary: initial rich minus initial terse checked-answer successes /32;
report paired discordances and exact two-sided binomial McNemar probability,
all four family counts /8, completeness and failure counts. No selection of
best family as a pooled superiority claim. Corrections/records are secondary,
never substituted into primary successes. Missing calls are non-success;
abort/incomplete run is operationally inconclusive rather than a clean null.

Read full text of every candidate with its question and prior child response
where applicable. Bind judgments to exact target SHA256 with quoted evidence.
Axes: first-person account; mathematically grounded operations; concrete check
or checkable expectation; reusable nontrivial operation/lesson; no invented
premises, false evidence or padding. Correction additionally needs meaningful
revision; record needs operational content, not answer repetition. Headings,
length, correctness and fluency alone cannot establish admissibility. Preserve
FAIL/UNRESOLVED bytes. Report candidate and semantic PASS yields by kind and
distinct task; family-gap eligibility separate from semantic validity. Any
ambiguous gold is flagged without silently repairing gold or denominator.

Strong support requires complete paired data, positive primary difference,
two-sided exact p<=0.05 and >=8 semantic PASS distinct rows across >=4 tasks
in positive-gap families, with no unresolved provenance defect. Otherwise
report descriptive evidence only; clean nonpositive gap falsifies improvement
for this frozen cohort, not the broader thesis. No post-hoc power claim.

## Safety/publication

Only node3 physical GPUs2–4, after fresh UUID/PID/process-CVD scan, no access
to other GPU execution and no unknown/name kills. Unknown occupation fails
closed. Finite <=45min; lease margin cutoff 2026-09-19T21:03:00Z. Sources and
data stay local under /data gpu_artifacts_local; remote /tmp or observed
/localhome. Credentials env-only, hostname source ignored gpu/hosts.env.
Publish exact owned paths with protocol/tests/provenance/sourcehash/guardian
before GPU science. No reset/rebase/stash/force; active merge reported to PI.
No BOARD/RESEARCH_STATE/COORDINATION contents, prior REPORT/REDUCTION/SEMANTIC,
or other worker checks. Only own EOF notebook append if necessary.

## Cohort and analysis freeze — 2026-09-14T22:38Z

Fresh TASKS.json SHA256:
42ec9ca3605579ced04941ae2518fe3dd9638d7dd5e680fa856e71cd4da38dc0.
Dataset bytes match the original public-source hash. Exactly 32 distinct
questions, eight per mining family, and no original task IDs overlap. Seed
differs from the original. Selection precedes gold parsing; unparseable gold
would be retained as unresolved, not replaced. Original access was restricted
to extracting 32 IDs from original TASKS.json; no responses were opened.

The policy/reducer and semantic rubric are frozen before native output access.
Primary successes preserve the original final-line exact numeric rule, separate
from terminal/length/semantic admission. No automatic heading classifier exists.
Candidate text, question, prior child history and actual guidance are all
included in the full-text review queue. Every candidate requires an explicit
bound review, including unsuccessful admissions. Semantic ambiguity in a
public gold answer must be reported independently of numeric parse validity;
do not reinterpret the gold to improve agreement. Any such unresolved defect
blocks a strong-support claim even if a numeric reducer flag cannot detect it.

Native pairs are consecutive initial calls on the same shard/model instance
in this single fixed collection batch, not separate outcome-selected runs.
Task positions modulo3 bind shards to physical GPUs2/3/4. Global position
parity alternates rich/terse order (four of each order within every family).
All three shards together have a maximum128 calls; maximum44/44/40 per shard.
Correction/record rules match original; max4 calls/task, max4 messages/call.
The process guardian uses2670s wait plus at most30s termination/reap budget,
with native forward checks at2640s. Only its own created process group may
be signaled. No unknown owners or process-name matching.

## Current operational hold, not a result

Allowed gpu/hosts.env contains node addresses but no node3 mapping. No host
identity is guessed, no SSH/GPU access attempted, and no native outcomes exist.
PI must identify the node3 env key. The independent scanner additionally fails
closed on unreadable live /proc environment/device ownership; it has no
borrowed service exceptions. If ordinary SSH credentials cannot see ownership,
report that exact obstacle rather than relax the guard or kill unknown work.

Publication of CPU-ready code is not publication of a passed preGPU gate.
After host mapping, native CPU manifest/base/tokenizer preparation and fresh
UUID/PID/CVD guardian evidence must still be recorded, committed and pushed
before launch. Request ordered SEQ only after those checks make launch ready.
