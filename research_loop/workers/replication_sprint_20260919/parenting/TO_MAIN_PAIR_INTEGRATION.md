# Immediate pair integration handoff — 2026-09-19 13:14 UTC

**13:19 update: LIVE DEPLOYMENT BLOCKED ON EXISTING PROVIDER AUTHENTICATION.**
Read-only inspection confirms 401/auth_error for both exact attempts. No renewed
credential exists per Main. No retries, provider/credential switches, cleared
guards or fake turns were made. Shorter exact-hook candidate is in
`PAIR_TASK_CHECK_BRIEF.md` / `PAIR_TASK_CHECK_INTEGRATION.patch`.

**Target the existing `post_reboot_pair_parents_20260919/parent_service.py`
`source_parent()` hook, shared by both arms.** It already overrides
`parent.instruction()` while retaining the original `PARENT_SOURCE.py` provider,
model, 90-word output limit, JSON metrics, original ledgers and publication path.
Append the same prospective brief there; wrap only `parent.generate` to add an
instruction/epoch receipt to the existing per-turn INPUT. Do not replace the
paired rationale with C2's schema. Pending RESULT/PUBLICATION paths bypass
`generate`, so existing work must finish under its recorded old epoch.

`PAIR_INTEGRATION.patch` plus the pure helper and hook tests are READY in this
directory: see `CPU_TEST_RECEIPT.json`; unapplied patches pass `git apply --check`.
Read `PAIR_READY.md`. Main applies/publishes/integrates; I have not touched live source.
Only the CPU parent implementation needs future adoption; do not signal either
native. The singleton, `STATE.json`, pending attempts, cumulative use, provider
identity, retry rules and frozen learning setting remain unchanged.

**Important current read:** processes 345404/345405 exist, but local saved
STATE on both arms contains `provider_blocked`:

- Learner: `turn_000104_1789794006756564934`,
  `AMBIGUOUS_OR_UNVALIDATED_NO_REDISPATCH`; last_parent_cycle 103, observed 147.
- Frozen: `turn_000134_1789794506916730728`, same outcome;
  last_parent_cycle 133, observed 169.
- Both stages are 0, first_turn false, pending_turn null. No fields were edited.

This is an observation of local saved ledgers at 13:13–13:14 UTC, not proof no
other restoration occurred. **Alive != actively parenting.** Preserve and
reconcile those exact attempts; this candidate MUST NOT clear/retry them, reset
budgets, switch credentials, or bypass platform/provider denials. Provider
recovery is a separate owner operation. Keep natives generating meanwhile.

The current payload is own committed ACTs and prior parent messages/assessments;
it does not expose arbitrary Tool/score records. `PARENT_SOURCE.instruction`
explicitly says no executor/game/peer tools are connected. The new policy must
say missing judgment is unknown, not invent environmental feedback. We will
not broaden that visibility contract or transport in a parenting patch.

Mixed subjects can be introduced inside the current persistent scheduler stage:
the candidate asks for `proposed_stage` unchanged, so no automatic taper/LR
change is induced. Math remains active; a small new answer-free TRAIN passage
and reading-to-writing/reasoning tasks make the addition actionable now. The
parent must name the actually observed work before setting each new object.
