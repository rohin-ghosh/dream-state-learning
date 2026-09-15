# L1 feed diagnosis, 2026-09-15 19:29 UTC

## Finding: zero new ingestion is chiefly a wiring/review gap, not demonstrated universal quality rejection

The current A100 continuation reads one fixed `CONTINUATION.json.prior_version`: the copied C2 `versions/002`. `namespace()` validates that fixed PLAN/PREPARED/ELIGIBLE/ENCODED, and every later training segment reuses its19 eligible rows. It does **not** call the old dynamic `choose_version()` or watch an incoming queue. Its source is unchanged, SHA6984cb04eee54bb2bd2fb1a4fb938c571c1b613c6aa220dd0827f34bb2cdb688.

The original feed implementation supports explicitly reviewed immutable appends, not automatic semantic admission. Its old supervisors1142312/1142315 are absent; original heartbeats are stale at the old cutoff. The bounded process census found no running legacy feed supervisor, append publisher, or feed-status process on the three sampled nodes. The A100 runtime has no INBOX/QUEUE/versions/review-decision files. The original ovx feed has versions000/001/002 with9/14/19 rows, but no INBOX or QUEUE. Its latest five-row append was actually admitted at13:35:43 UTC; its APPEND_ADMISSIONS manifest is6c366befc847f7420ec53c1b6ef1a8561f8e344337a29b2a0f892b70010e8b78.

Generation writes raw captures marked UNREVIEWED and `corpus_admission=False`. V3 PROGRESS writes literal `semantic_admissions=0`; descriptive metrics also explicitly say `functional_admission=False`. Those fields are not evidence that a live ingester evaluated and rejected every response.

There is also a real provenance mismatch: old feed `source_gate()` accepts only `generation_v3/gpu...` paths and its old frozen seed. New R119 captures live under the explicitly forked generation root and carry FULL15460 state. Their archive/policy/task hashes match the old source closure, but their seed differs. Passing them through the old source gate without a new explicit source binding would be incorrect. The100 diagnostic path failures below are **offline probes**, not retroactively invented live rejection history.

## Native100-row audit

Method: newest complete immutable CALL files by native filesystem mtime, fixed quota64ovx/27A100/9ovx2 (approximately proportional to7/3/1 remaining generator lanes). Released ovx7 excluded. No outcome-based selection. This is a bounded recent sample, not a global prevalence estimate. All raw text/token arrays remain node-local. No held or FINAL content was read. Existing unchanged math oracle recomputed TRAIN outcomes; no alternative parser or rescoring policy was introduced.

| Step | Captures remaining |
|---|---:|
| Completed CALL files |100|
| TRAIN, child-self, no parent/teacher |100|
| Supported by current math-only feed |5|
| Terminal and untruncated |5|
| Existing native math oracle correct |5|
| Not in excluded task/question identities |5|
| Not already admitted source task or target |5|
| After within-sample task/target deduplication |3|
| Existing bound full-text author review |0|
| Registered current-root/current-seed source |0|
| Actually admitted/trained from this sample |0|

Families:87 route,8 code,5 math. The95 non-math captures are outside the existing feed contract, not thereby behavior failures. All100 lack a bound author review and all100 differ from the old seed binding. There were0 native-vs-recorded math outcome mismatches,0 descriptive persistence positives,0 reported cap hits. These are separate counts, not semantic richness claims.

Three distinct **unreviewed** math candidate identities are retained on ovx in:
`/localhome/local-rohing/orch_r119_l1_feed_diagnosis_20260915_attempt1/AUDIT/UNREVIEWED_CANDIDATE_IDENTITIES.json`
SHA51d86ed99863615ac0c46d9ef62b0e97d9f7d78630124131bac74dab27139441.
They correspond to TRAIN task IDs gsm8k-train-1768, gsm8k-train-4506, gsm8k-train-3102. They pass only the mechanical quality screen. Full-text consequential task-constraint evidence, exact tokenizer/prefix encoding<=2048, and complete native contamination checks remain required. No PASS review was fabricated.

## Exact prospective C3 scope proposed — NOT implemented or activated

This is not a stopped ingester that can simply be restarted unchanged: the frozen current runtime has no current-source consumer contract. Do not launch the old feed supervisor with obsolete slots/cutoffs or point it at new captures by renaming their provenance.

1. Register a separate explicit R119 self-generated source binding: exact node/root/FORKS/PLAN, original+supplement archive hashes, policy/tasks hashes, FULL15460 COMMIT/state. Retain self-TRAIN label plus explicit fork lineage; never label it corrected-L2/parent-derived or replace old histories.
2. Review at most these3 distinct TRAIN math candidates under the existing `TASK_CONSTRAINT_USED` / `ARITHMETIC_ERROR_CORRECTED` contract. Correct answer alone is insufficient. No route/code expansion, template/count proxy, automatic success-to-admission, or new persistence claim. If zero pass, publish zero.
3. Create an immutable C3 append containing the old19 rows/encodings byte-for-byte followed only by validated new rows. Preserve legacy/prior/42BASE anchors and exact student-only target IDs/prefix masks. Reject context overflow rather than trimming. Raw rows transport node-to-node only, with hashes; never through the repo.
4. Restore segment-bound version selection in a **new supervisor namespace**, not a live-source patch. Bind a common future update boundary above both arms' current cursors so corresponding FULL/CONTROL updates use the same cohort. Preserve exact latest AdamW/RNG/counters and old schedule seed. The existing one eligible presentation per8updates and CONTROL-only eligible masking remain unchanged; no new16/old1 claim applies here.
5. Keep each selected cohort immutable through TRAIN+fixed32ON/OFF+held readout. Report actual newly selected target IDs/hash-only token/exposure receipts, not merely published append counts. A failed/absent review batch leaves the current cohort running.

The proposed change is a prospective source-registration and feed-consumption contract, not permission to weaken the benchmark/visibility/semantic gate. Await Main's exact scope disposition before implementing that change. Current training and generators continue; the R124 assay is untouched.

## Separate operational fault discovered and repaired

During the read-only process census, CONTROL3190881 was found absent, last committed17124, with its last heartbeat WAIT_OWNERSHIP. Its supervisor log proves a strict-scanner subprocess exit raised uncaught `CalledProcessError` before any segment039 native launch. This was not a lease stop or optimizer failure. FULL continued to17508 during the audit.

Recovered only A100physical1 in `/localhome/local-rohing/orch_r119_l1_control_recovery_20260915_attempt1`, preserving17124 adapter/AdamW/rank0 RNG/counters and19-row cohort. A narrow fresh supervisor adapter treats scanner execution errors as BLOCKED+retry; it never treats them as clear or suppresses provenance/UUID errors. Original frozen training/readout bytecode is reused unchanged. New supervisor3464856, native3471628. Actual LOADED17124 verifies optimizer/RNG/global cursor restored; update17151 observed19:29:17. No FULL/evaluator/other-lane signals or allocations changed. Failed old root remains intact.

Tests:20 feed/audit tests passed;8 continuation/recovery tests passed. Operational recovery is not a new-feed admission or behavior improvement.
