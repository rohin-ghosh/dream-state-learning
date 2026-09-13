# Independent terminal audit: Q0 root 1 attempt 1

**Date:** 2026-09-13 UTC  
**Root:**
`/localhome/local-rohing/astra_diagnostics/astra_pairwise_Q0_root1_20260913_attempt1`  
**Role:** fresh raw-artifact auditor; I did not build or run this experiment.  
**Mutation scope:** none. I changed no builder source, root artifact, job,
adapter, model, GPU process, threshold, or scientific claim.

## Verdict

The sealed label **`NONREPORTABLE_RUNTIME_ABORT` is correct and must remain
final for this root**. No efficacy, canary, writer, or mechanism result from
attempt 1 is reportable.

The exact defect is nevertheless narrow and localized: **the native model-work
counter was hooked to the wrong object for PEFT-wrapped audit/fit models.** The
raw records and the only explicit model-call path show that the required
natural-prefix work was performed exactly, with no evidence of incomplete or
extra top-level calls. The experiment failed its required independent
accounting instrument, not its workload schedule.

This is an accounting-only executor defect. It does not permit retrospective
scientific salvage. Repair the counter, add a PEFT-wrapper regression, pass the
full native CPU suite, and execute a fresh attempt under unchanged scientific
bytes.

## Custody, sealing and release

- Prepared manifest SHA-256:
  `2486bbc89e02fc3357eb285e19ac9172b3cf4ac1427097b4ad48b471e4cae207`.
- Prepared material SHA-256:
  `aa96210c73048d9980011930cb57e3407beacbe7ed094ae13b46dda187de4852`.
- Launched executor SHA-256:
  `596071780b961031ef8ef5e352898391df47038db70e2acb68b5c3dbe15c201b`;
  focused-test SHA-256:
  `5e4eb5cb9926403319480b4bf8fc5d2225dd1768bb049909da604c1edb634afe`.
- Controller PID/PGID/session `298494`, start `1789267338.5108418`, deadline
  `1789270038.5108418`, selected A40 UUID
  `GPU-41a86250-88eb-ed8a-ddfe-9d6f93515da1`.
- Resource completion was `1225.23` seconds after start, durable finalization
  `1230.38` seconds after start: both below the fixed `2700`-second deadline.
- Seal SHA-256 independently matches
  `91fb8f1acc63d089bac540dfd3f1ec8e620a02d167b393809cd3b5ae99084897`.
  The sealed executor's read-only replay passed the complete immutable
  inventory and reproduced `NONREPORTABLE_RUNTIME_ABORT` with replay report
  SHA-256
  `16bbed2a1cf6ed5be62fed186918cf855eaaf9e1ab134368c623ed21a7ed3f58`.
- All five job -> load -> DONE -> log -> cleanup receipt chains hash-validate.
  Every listed raw event exists once and matches its recorded hash; there are
  no unlisted event files. Every receipt records one attempt and finished
  cleanup.
- Controller PID and all five worker PIDs are absent. Every cleanup receipt
  says owned group empty, GPU process absent and reservation released; a live
  `nvidia-smi` query showed no compute process on the node.

Custody, deadline, immutable seal, replay and release therefore pass. The one
failing integrity surface is the native forward counter below.

## Exact accounting mismatch

| stage | required natural-prefix calls | recorded natural-prefix calls | required native model calls | recorded native model calls |
|---|---:|---:|---:|---:|
| zero-update audit | 128 | 128 | 128 | **0** |
| contemporary OFF | 288 | 288 | 2,353 | 2,353 |
| P_AUTH fit attempt | 148 | 148 | 148 | **0** |
| P_DERANGED diagnostic attempt | 148 | 148 | 148 | **0** |
| P_UNARY_TOOL fit attempt | 148 | 148 | 148 | **0** |

The OFF count decomposes exactly into `288` prefix calls plus `2,065` emitted
token IDs over `296` complete, unique generation records. Its total is
`288 + 2,065 = 2,353`.

Each fit attempt followed its registered one-update early-stop shape: no
snapshot, one ordered step, four training forwards and the four expected raw
events. Its `148` natural calls decompose exactly as:

```text
128 step-zero exact prefixes
  8 dropout-off repeated before-canary calls (2 x 4)
  4 train-mode quartet calls
  8 dropout-off repeated after-canary calls (2 x 4)
---
148
```

The zero-update audit has exactly `128` raw row records, `32` quartet records
and zero optimizer steps. The audit initialization receipt is byte-equal to
the initial receipt in all three fit workers. Thus the recorded lifecycle and
natural-forward work are internally exact. These are workload/integrity facts
only; the underlying scientific canary values remain nonreportable.

## Root cause: wrong hook target, not wrong work

The sealed source establishes the failure directly:

1. `natural_forward` increments `natural_prefix_forwards` and then makes the
   executor's only direct `model(...)` call.
2. `native_worker` attaches `model_forward_calls` to
   `model.get_base_model()` whenever `model` has a PEFT configuration.
3. Audit and fit use a PEFT wrapper and call the wrapper itself. On this native
   PEFT version, the hook attached to `get_base_model()` is not invoked by that
   top-level wrapper call. Hence all adapter-bearing stages recorded zero.
4. OFF is not PEFT-wrapped, so the hook is attached to the exact invoked model
   and counts both its prefix calls and generation-token forwards correctly.

There is only one explicit `model(...)` call site in the sealed Q0 executor,
inside `natural_forward`. Audit and fit perform no generation. Every successful
`natural_forward` call increments immediately before that call and returned
enough raw output to complete its bound record. Static call-path inspection,
raw event completeness, exact stage shapes and clean worker exits therefore
support **no missing or extra top-level audit/fit model work**.

That conclusion is an independent diagnosis, not a replacement for the
registered redundant counter. The frozen protocol required both counts to
agree, so the integrity abort properly outranks all science.

## Exact repair and retest implication

Treat this as a non-material instrumentation repair; do not change the Q0
material, objective, root, optimizer seed, dropout sample path, rank, rate,
dose, thresholds, lifecycle or claim.

1. Count the explicit top-level call inside `natural_forward` directly as both
   one natural-prefix call and one native model-forward call.
2. Retain a generation-only forward hook on the actual generation owner, but
   suppress it while `natural_forward` is active so OFF is not double-counted.
   Verify both base and PEFT-wrapped evaluation paths: direct prefixes count
   once, and greedy generation counts once per emitted token under the fixed
   one-request-at-a-time path.
3. Add a focused regression whose callable wrapper differs from
   `get_base_model()`. It must reproduce attempt 1's zero-counter bug before
   the fix and prove exact audit, one-update fit, OFF evaluation and
   adapter-mounted evaluation accounting after it. Retain equality and
   adjacent-failure tests so accounting cannot become self-reported only.
4. Run the complete bound Linux acceptance suite on the repaired source and
   create a new source archive, manifest and **attempt-2 root**. Do not edit,
   append to, or reuse adapters/events from the sealed attempt-1 root.
5. Run the same failure-inclusive Q0 lifecycle once. A valid scientific early
   stop counts as the Q0 terminal; a pass must still satisfy the entire frozen
   exact/held/complementarity/copy/locality conjunction. Do not launch the two
   confirmation roots or treat Q0 as releasing the endogenous relay from this
   attempt-1 abort.

The repair changes executor/source hashes and therefore requires a new native
preflight receipt, but it does **not** justify another scientific design or
threshold round.

