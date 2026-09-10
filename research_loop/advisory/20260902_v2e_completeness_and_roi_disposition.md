# V03R v2e completeness and ROI disposition

**Status:** read-only implementation/science audit. This document changes no
ratified bytes, authority, benchmark, claims, or result. It authorizes no
provider or GPU call.

## Decision

Do not launch `v03r_recurrence_closure_dev_v2e` as the next science run. Keep
its validated contracts, provider boundary, two-phase artifact verifier,
selector logic, and transition tests as reusable infrastructure for the
Paper-1 end-to-end canary.

The reason is conjunctive:

1. the implementation is incomplete and correctly fails closed before any
   science call;
2. the completed diagnostic would still forbid the final goal, final thinker,
   answer/behavior, and LoRA, so it cannot close a remaining Paper-1 arrow;
3. its registered envelope is 514 shared DREAM calls plus up to 288 branch
   DREAM and 102 exploratory calls, making completion a poor next use of model
   and GPU budget relative to a smaller end-to-end falsifier.

## Exact CPU findings on 2026-09-02

`research_loop.test_v03r_recurrence_closure_transition_v2e` reports 23 passes
and three failures:

- the provider view still contains a raw `land_00` identifier despite the
  alias-redaction acceptance test;
- `run_v03r_recurrence_closure_v2e.py` ends after `run_science_parent` and has
  no `run_phase_a`, `run_phase_b`, `build_parser`, or `main` implementation;
- the ratified workflow lacks the declared
  `v2e_ascii_alias_provisional_dream ->
  v2e_defined_life_exploratory_ceilings` implementation nodes/edge.

The new remote wrapper
`research_loop/v03r_recurrence_closure_remote_job_v2e.py` therefore validates
scope, review bindings, model/hardware, and the synthetic envelope, then emits
an immutable failure marker with `science_calls_started=false` when asked to
start science. The new artifact verifier validates the generic canonical
envelope, inventories, phase barriers, seals, hashes, and provenance. It does
not invent the unspecified raw/scored payload semantics.

Supporting checks:

- remote wrapper and verifier `py_compile`: pass;
- both CLIs `--help`: pass;
- verifier-focused existing CPU suite: 52 passed, 0 failed;
- full core suite before the new completeness assertions: 62 passed, 0 failed.

## Reuse boundary

Safe to borrow: v03r collision twins, final-goal embargo, public selector,
alias contract after repair, isolated provider receipts, common-random-number
arm scheduling, phase-A-before-offline-score barrier, and immutable markers.

Do not carry forward: the 514/288/102 call envelope, exploratory full-context
ceilings, proposal-only endpoint, mechanical semantic admission as a headline
self-check, or any inference that an approved but incomplete workflow is
running.
