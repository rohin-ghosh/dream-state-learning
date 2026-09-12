# Independent review — seed605 rejected-sleep resume repair

**Reviewed commit:** `535ee86b81158725c5e5785ae82ae0238c012ad7`

**Scope:** CPU/static review only. No model, GPU, node, or running-life action.

## Original-commit verdict: narrow fix PASS; crash-safe write protocol FAIL

The commit correctly makes a sole `REJECTED_*` marker terminal. A resumed
life therefore does not retrain that rejected sleep. It also detects more than
one `DONE`/`REJECTED_*` marker and raises rather than choosing one. These are
valid non-material corrections to the seed605 incident.

It is **not yet safe to promote as a complete resume fix**, because the
trainer and runner use `DONE` for two different meanings:

1. `train_adapter.py` writes `adapter/DONE` when fitting finishes.
2. Only afterward does `run_life_v2.py` rename that marker to `CANDIDATE`, run
   the canary/gate, and rename it back to the final verdict.

A crash between (1) and (2) leaves a trainer-completion `DONE`. On resume,
both `existing_adapter_verdict()` and `latest_adapter()` interpret it as an
accepted, gate-approved adapter. The canary and probe gate are silently
bypassed and the ungated adapter can be mounted.

A second unresolved state is a crash after `DONE -> CANDIDATE`. `CANDIDATE`
is treated as no verdict, so the runner retrains instead of resuming the gate.
If the old candidate already wrote `probe_gateNNNN.json`, that cached probe can
then gate the newly trained bytes. This recreates the stale-evidence class the
rejected-marker repair was meant to remove.

The multiple-final-marker check is locally correct, but the runner first calls
`latest_adapter()` during startup. Therefore a directory containing both
`DONE` and `REJECTED_*` may be selected and mounted before the later helper
raises. For full fail-closed semantics, state validation must happen before
adapter selection or inference.

## Required repair shape

Use a real two-phase state machine:

- Train into a staging directory whose trainer-completion marker cannot be
  mistaken for final acceptance.
- Atomically expose the finished bytes as `CANDIDATE`.
- Resume an existing `CANDIDATE` by gating those exact bytes, never by
  retraining them.
- Bind cached gate evidence to an adapter digest, or recompute it.
- Validate that all adapter directories have exactly one legal state before
  `latest_adapter()` may mount anything.
- Only the runner may create the final `DONE` or `REJECTED_*` marker.

Add crash-point regressions for (a) trainer completion before candidate
promotion, (b) candidate before canary, (c) candidate after cached probe but
before final verdict, and (d) ambiguous markers before model loading.

## Evidence

Tests were run from immutable `git archive` snapshots of the reviewed commit
and its parent, avoiding concurrent worktree edits.

- New focused tests at `535ee86b`: **2 passed**
  (`test_resume_does_not_retrain_a_rejected_sleep`,
  `test_multiple_final_adapter_verdicts_fail_closed`).
- Harness self-consistency plus the two new tests: **3 passed**.
- Full `tests/test_compiler_golden.py` at `535ee86b`: **3 passed, 5 failed**.
- Same file at parent `535ee86b^`: **1 passed, 5 failed**.
- The same five legacy failures occur in both snapshots and are solely an
  existing serialized-float difference (`0.23957295515791507` versus
  `0.23957295515791505`, delta `2e-17`). Thus the commit adds no observed
  fresh-run/golden regression, but the repository's exact-byte golden test is
  not green in this interpreter.

Direct marker-state check at the reviewed commit:

```text
CANDIDATE: existing_adapter_verdict=None, latest_adapter=None
trainer-written DONE: existing_adapter_verdict=DONE, latest_adapter=<adapter>
```

That state classification is the critical remaining defect.

## Follow-up closure review: repaired working-tree diff PASS

The author-side repair reviewed immediately after the finding resolves the
critical defect without changing the scientific protocol:

- The trainer now writes only to `adapter.train/`; its `DONE` cannot be seen
  by `latest_adapter()`.
- Promotion changes the staged marker to `CANDIDATE` before atomically moving
  the directory into the adapter namespace. A crash between those two renames
  is resumable because staged `CANDIDATE` is an admitted state.
- Existing `CANDIDATE` bytes are gated in place and are never retrained, so a
  cached gate result still refers to those exact bytes.
- Partial staging, mixed staging/adapter state, unclassified adapters,
  candidate-plus-final, and multiple finals fail closed.
- `validate_adapter_states()` runs before `load_model()`, closing the earlier
  possibility that ambiguous `DONE` bytes were mounted before rejection.
- Only the runner converts `CANDIDATE` into final `DONE` or `REJECTED_*`.

CPU evidence on the repaired diff:

```text
6 passed in 6.01s
python3 -m py_compile: PASS
git diff --check: PASS
```

The six focused cases cover harness self-consistency, rejected-terminal
resume, multiple-final rejection, rejection before any model/world event,
candidate re-gating without training, and staged trainer-completion promotion
without training. The pre-existing exact-byte golden comparison remains red
only for the independently reproduced `2e-17` float serialization drift.

One non-blocking coverage improvement remains: explicitly simulate the
micro-crash after staged `DONE -> CANDIDATE` but before the directory rename.
The implementation handles that state directly, but the current staged test
starts from staged `DONE`. This does not change the PASS verdict.
