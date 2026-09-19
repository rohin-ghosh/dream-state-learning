# Workstream 4: mixed-curriculum parenting candidate

**Status: READY OFFLINE; LIVE DEPLOYMENT BLOCKED ON EXISTING PROVIDER AUTHENTICATION.**
**Priority handoff: `PAIR_READY.md` and `PAIR_INTEGRATION.patch`.** The paired
curriculum services now have a concrete prospective candidate preserving their
original response/metrics schema; Main owns integration and publication.
Prepared September 19, 2026. This directory is the entire write scope. No parent
messages, provider calls, GPU work, signals, commits, or pushes are authorized
by this candidate. No claim of behavioral efficacy follows from the CPU tests.

## Deliverables

- `MIXED_CURRICULUM_PARENT_BRIEF.md`: bounded parent-only policy for the existing
  C2 `--policy-addendum` hook. Strong responsive parenting remains the baseline.
- `PAIR_MIXED_CURRICULUM_BRIEF.md`, `paired_curriculum_policy.py`, and
  `PAIR_INTEGRATION.patch`: minimal shared `source_parent()` integration for the
  actual learner/frozen-sibling services. New INPUTs get policy epoch hashes;
  pending/provider/publication ledgers and runtime schedules are untouched.
- `PAIR_TASK_CHECK_BRIEF.md` and `PAIR_TASK_CHECK_INTEGRATION.patch`: shorter
  task-to-artifact-to-concrete-check alternative at the same active hook.
  Main selects one matched treatment, not conflicting briefs stacked together.
- `AUTH_BLOCKER.json`: both exact old attempts returned 401 / auth_error.
  No renewed credential is available per Main; no retry or provider swap.
- `INTEGRATION.md`: exact injection point, incompatible paths, and adoption
  prerequisites. There is no live-source patch because C2 already has the hook.
- `MEASUREMENT_AND_ABSENCE.md`: proposed baseline and small secondary absence
  probe; neither is an executable scheduler or a new scientific invariant.
- `OFFLINE_TURN_EXAMPLES.json`: three manually authored, unsent candidate turns
  tied to actual preserved child outputs, not fabricated experimental results.
- `candidate_review.py` and `test_candidate.py`: offline draft checks and tests
  executing the existing, source-pinned prompt hook in isolation.
- `SOURCES.json`: hashes of inspected local code/receipts and the two standing
  curriculum documents at an exact `origin/main` commit. This is not a live fleet
  health report or an attestation that a policy has reached an ACT.
- `CPU_TEST_RECEIPT.json`: passing CPU tests and successful unapplied
  `git apply --check`, with exact tested candidate hashes.

## Mechanism and scope

The user's proposal is a **hypothesis**: repeated child-generated experiences
under persistent parenting may consolidate reusable thinking tendencies in the
slow LoRA loop; the fast context loop may activate and apply those tendencies to
the current object. Repetition means repeated *successful use across situations*,
not copying parent slogans, self-descriptions, or intention statements. Parent
tokens remain context, not new training targets. All authentic child rows still
train, including failures and non-English output. Frozen controls stay frozen.

This candidate changes only proposed instructional content. It does not change
the base model, learning rule, row eligibility, retention, runtime stages,
visibility, response schema, singleton ownership, call/token limits, cadence,
leases, or scientific claims. It does not make feelings or self-descriptions
evidence of sentience. The manuscript's stronger hypothesis remains unproved.

## What the inspected sources actually show

| Source | Observation | Candidate response |
|---|---|---|
| Standing birth schedule, section 2 | Math, reading, probing, writing/mixing, then withdrawal are already specified. | Make mixing concrete without pretending those stages ran successfully. |
| Standing developmental curriculum, items 1–8 | Begin with math; add reading soon; connect writing to readings; mix without abandoning earlier tasks; richer guidance when rarer. | Keep math available; introduce one small grounded object at a time; revisit the same checking tendency in another subject. |
| C2 restored `BRIEF.md` / `c2_restore.py` | Responsive math/reading/writing is mentioned; the immediate repair repeatedly returns to the five-cycle problem. | Preserve unfinished work but avoid an indefinitely math-only sequence when guidance changes do not land. |
| C2 `C2_DELIVERY.json`, ACT12599 | Parent visible in ACT; code and a candidate set exist, but the conclusion is wrong. | Credit the actual code/candidate, not correctness; request the deciding check without supplying the solution. |
| C2 saved SOURCE, child14353 | Working state asserts correctness, not a displayed check. | Ask for a small check or a factual question; do not count this as completed reflection. |
| P7 `p7_restore.py` / `r229_overseer.py` | Parenting is overseer-to-P7; actual Astra7 replies and a source-bound rationale are required. | Preserve role boundaries; do not turn a generic mixed-curriculum brief into direct teaching of Astra7. |
| Node-3 `recover.py:TASK` | Explicitly forbids reading, memory-policy and meta objects in the restored caption turn. | Do not append a conflicting mixed brief and call it deployed; keep captions primary there until an explicit prospective policy integration. |
| Pair `parent_service.source_parent()` | Shared instruction hook; own committed ACTs; current stages 0; process liveness but provider-blocked saved ledgers. | Use the same mixed-subject policy inside the persistent stage, preserving pending attempts. Treat provider recovery separately. |

These are source-bound observations, not a fresh audit of all lives or a claim
that better parenting alone repairs missing feedback/compaction. The historical
best C2 checkpoint motivates replication; it does not identify which parental
intervention caused its performance.

## CPU validation

From the repository root:

```sh
python3 -B -m unittest discover -s research_loop/workers/replication_sprint_20260919/parenting -p 'test_*.py' -v
```

The tests perform local reads and isolated prompt construction only. They do
not import executable live parent modules, contact providers, or create runtime
state. Draft review flags are for an offline reviewer, never gates on child
execution or LEARN. Semantic answer leakage, appropriate praise, and behavioral
uptake still require human/scientific review; regex checks cannot establish them.
