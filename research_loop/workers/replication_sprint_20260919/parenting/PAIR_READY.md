# READY: paired persistent mixed-curriculum candidate

Prepared September 19, 2026, 13:17 UTC. **Unapplied and not published.**
Updated 13:19 UTC: **live deployment is blocked on existing provider
authentication**, not on this candidate. Both exact preserved attempts returned
401 / auth_error. Main reports no renewed credential. See `AUTH_BLOCKER.json`.
Do not retry those 401s, change providers, reset ledgers, or invent parent turns.

## Minimal integration mechanism

Target: `research_loop/workers/post_reboot_pair_parents_20260919/parent_service.py`
at SHA256 `84ccf8832ee78d3c749b11b56b11872162f684aac9763c90f1a56b316fc13db7`.

`PAIR_INTEGRATION.patch` makes only these changes:

1. Defines the location of this candidate directory.
2. Loads the pure `paired_curriculum_policy.py` helper and the same
   `PAIR_MIXED_CURRICULUM_BRIEF.md` once in each arm's existing `source_parent()`.
3. Extends the existing instruction, preserving the original response/metrics
   schema and first-outage acknowledgment. Current scheduler stage stays put;
   mixed subjects do not cause automatic stage advancement/withdrawal.
4. Wraps only a *new* `parent.generate(turn, payload)` to add
   `parent_policy_epoch` (brief SHA256 and policy ID) to the original INPUT.
   Existing pending RESULT/PUBLICATION processing never calls that wrapper.
5. Adds helper/brief hashes to the existing immutable process-source receipt.

`PAIR_TASK_CHECK_INTEGRATION.patch` is the shorter alternative requested by
Main. It differs only in selecting `PAIR_TASK_CHECK_BRIEF.md` at the same hook
and in its source receipt. Use one treatment on both arms rather than stacking
the alternatives. The short treatment asks for one actual artifact and one
falsifiable check, then examines the next ACT.

The patch does not change `run` beyond that source-receipt list. Tests compare
the remaining run-loop AST exactly, including provider-block logic. Transport,
consume, assess, turn_due, generation provider, low reasoning effort, word limit,
budgets, singleton, pending ledgers, native identities and scoring visibility
remain unchanged. There is no credential change, retry path, native signal,
automatic LR change, exclusion, or actual taper.

Existing-state read at 13:13–13:17 UTC: both stages are 0, so the original due
logic is still every committed cycle. The same policy applies to both arms, but
the parent responds to each one's actual work. No partner's results are supplied.
Current source policy says no executor/game/peer tools are connected. This
patch does **not** add them or read raw REQUESTs/Tool/score streams. Missing
environmental verdicts remain unknown; this is not a claim of repaired feedback.

## Main's adoption sequence

- Verify current CPU and native identities and source hashes. Native PIDs supplied
  by Main are learner493500 and sibling471737; keep both untouched. Current CPU
  services345404/345405 load code at startup, so copying a new file alone cannot
  change their instructions.
- The existing *provider-blocked* attempts are confirmed 401/auth_error.
  Valid authorized authentication for the existing provider is an external
  prerequisite. Main owns reconciliation after that change; do not clear guards
  or redispatch these failures. Both children can keep running; independent
  parent-free probes are not blocked by this parenting prerequisite.
- Preserve all prior `STATE.json`, pending/provider attempt directories, original
  cumulative usage and receipts. Preserve an exact checkpoint/frontier before
  the prospective subject change; do not reset lives or re-birth the pair.
- Main may apply the exact patch, publish these dependencies, and perform its
  existing singleton-preserving CPU-service handoff. This worker supplies no
  signal/restart command. Match the helper/brief epoch on both sides before
  comparing outcomes; annotate differing adoption times rather than pretending
  simultaneous exposure.
- Pending provider responses/publications keep their old epoch and must not be
  regenerated. New INPUTs bind the new brief; the existing provider SYSTEM
  receipt contains its exact appended instruction. Inspect the first real
  parent INBOX -> ACT REQUEST visibility -> committed ACT on each arm, then
  assess behavior. A running service is not that receipt.

`git apply --check --whitespace=error` succeeded without editing the target.
Proposed target bytes SHA256:
`50183386d8d66336ba5990b0451f3021a35e951f52d98ec62aa7cd2a855a5e61`.
If current source has changed, rebase the candidate narrowly and re-run tests;
do not force-apply or rewrite live source closures to silence a mismatch.

## Concrete treatment, not another generic instruction

The paired brief introduces one explicitly new, parent-authored, answer-free
TRAIN passage (Leena and the lamp); parents deliver it as new text, not as a
claimed remembered reading. Subsequent turns connect actual reading to writing,
evidence-based reasoning and a return to unfinished math. One object per turn;
no math answers, prose solutions, rubric keys, unsupported praise or prescribed
feelings. The same text is available to both parents; their responses differ
according to their own child's output. Public turns remain <=90 words.

Source-specific **unsent illustrations**, not provider outputs or live receipts:

- Learner saved ACT response11519, SHA256
  `c65c29aa3bb3a9b862ecc4ac9d8af7e7fc75d62ed23f7d8d1f2f81fba8f40501`,
  notes an error but ends with an inconsistent arithmetic answer. An appropriate
  lead is: “Your note notices an error but leaves the result unresolved. Keep
  that calculation; let's try a short new reading.” Then the actual short
  passage and one question, not another correctness assertion.
- Frozen saved ACT response5518, SHA256
  `44f203ac28f447a0253a5e197bae569e6ae1eca4fc8cb9ec623b105daafe68db`,
  contains direct and decomposed arithmetic steps, then an incomplete prose
  check. An appropriate lead is: “You wrote direct and decomposed calculations.
  That is concrete work, not yet evidence of retention. Keep math; read this
  new passage.” Then the passage and one retelling question.

Those references came from the actual parent STATE event ledger in this read;
fresh live parents must use their newer supplied ACT, not replay these examples.
They are not standalone copies or re-verifications of entire native records.

## Remaining operational blockers

Both local saved ledgers contain `AMBIGUOUS_OR_UNVALIDATED_NO_REDISPATCH` provider
blocks, now traced to confirmed 401/auth_error, despite their processes being alive. Exact attempt paths are in
`TO_MAIN_PAIR_INTEGRATION.md`. This policy does not remove that blocker. It can
make the next legitimate parent turn better targeted, not make an unresolved
provider call safe to retry. Node-3 recovery belongs to its separate worker.

For Main's front-page morning log, use `MORNING_LOG_ENTRY.md`; replace the
candidate status only after actual adoption and REQUEST-to-ACT receipts exist.
