# Actual FINAL custody gap — 2026-09-15 16:36:11 UTC

Read-only node observation. No startup expiry extension, session publication, scan, signals, scheduler launch or model/provider calls. Main selector1519259 remains live with its original command; it was not touched.

**Both math FINAL schedulers are missing.** Attempt5 CPU stage retired the prior timers, but Main never dispatched a new guard, so no replacement timers were created. An existing RUNTIME is not an armed evaluator.

| Branch | Retired cutoff PID / start_ticks | Retired FINAL PID / start_ticks | Attempt5 replacement |
|---|---|---|---|
| F2 | 2752627 / 2459231 | 2752628 / 2459231 | NONE |
| A2 | 2752621 / 2459228 | 2752623 / 2459228 | NONE |

All four old PIDs are absent. Prefix `/localhome/local-rohing/orch_math_feedback_uptake_r118_preinfer_20260915_attempt5`, lane1 andlane5 both have RUNTIME but no GUARD_STARTED, TIMERS_DISPATCHED, CUTOFF_ARMED, LAUNCH or GUARD_TERMINAL. Both `/localhome/local-rohing/orch_math_feedback_uptake_r118_preinfer_final_20260915_attempt5/lane1` and `lane5` directories are absent: no PLAN or SCHEDULED replacement. Final campaign SESSION files are absent at observation. Original charges remain F2N274/P60,A2N170/P36.

Actual retirement evidence:

- attempt5/lane1/FINAL_TIMERS_RETIRED.json SHA256 `ddc96af4a8ffd68d2679fbc8b3090b8d5cd996db804e28321dc3958e57d5740b`.
- attempt5/lane5/FINAL_TIMERS_RETIRED.json SHA256 `594c250333a99c9babd85a5b46dc19968844b7dc46e1e89d7c67a94249f57df9`.
- F2 previous FINAL `/localhome/local-rohing/orch_math_feedback_uptake_r118_preinfer_final_20260915_attempt4/lane1/SCHEDULED.json` SHA256 `19b04d40f4bea38c861bc4ad07a32fe3a26f1658a3b6721a552251a0ff00ed00`.
- A2 previous FINAL sameprefix/lane5/SCHEDULED.json SHA256 `e5a64e3e000c5aa34da0d725533c20954f752ff59977f52169276398402636b3`.

## Proposed FINAL-only recovery — not armed

Use a new explicit math FINAL-only custody namespace inheriting the **same unused eight calls per branch** (16 total, zero additional quota). No training-session restart, optimizer, parent calls, OPEN extras, TRAIN collection or ledger reset. Retain the original17:00–17:20 UTC allocation with earlier lease-margin cutoff if applicable. No model or sealed FINAL access before17:00.

Do not merely run the existing parallel_final scheduler: it requires an actual CLEAN_RELEASE and GUARD_TERMINAL from the new guard; those cannot exist because no guard ran. Do not fabricate those receipts. A scoped successor must instead validate authentic prior failed actors/release chain, attempt5 never-dispatched evidence, actual timer retirements and unchanged carry/charges; reject any live or newly dispatched actor. Bind Main's sole FINAL_SELECTION.json through the existing pinned selector validation, not mutable STATE or a newly selected checkpoint. The selector itself is NOT sufficient to dispatch branch evaluators.

At17:00 validate the entire inherited evaluation-custody chain for any prior reservation/claim/partial/completed morning FINAL (not sleep0), then one new allocation-linked ledger/claim, fresh full privileged UUID/CVD admission, fresh parent-free native evaluator and full raw/tokens/denominators. Recheck exclusive claim and predecessor absence immediately before dispatch. Never duplicate an old attempt. Missing release/selection/admission/window means NOT_RUN, not retry or extension.

## CPU tests

Existing FINAL + drain CPU regression suites rerun at16:36–16:37: **38 PASS**,1.919s, no model/provider calls. These cover absolute/lease clocks, no early sealed access, prior partial/charged/completed no-replay, zero ledger reset, raw reasoning+tokens and failure denominators, canonical selection, real actor release, decoder fidelity.

Before arming the proposed successor, add focused regressions for never-dispatched attempt5 custody (no fabricated clean terminal), rejection after any guard/LAUNCH appears, dead-timer versus armed distinction, recursive inherited FINAL no-duplicate detection, and no use of expired training authorization. Those successor-specific tests and implementation are **not yet complete**. This receipt reports the gap and proposes the narrow remedy; it does not claim FINAL is armed or completed.
