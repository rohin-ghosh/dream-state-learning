# Math FINAL: deadline-only clean-boundary handoff

## Diagnosis and scope

Main's13:41review is correct. The immutable shared resident finishes/breaks its
TRAIN loop and unconditionally waits until17:00 before dispatching the legacy
16-call FINAL+OPEN readout. The first evaluation timer merely waited for natural
termination and suppressed any legacy attempt. It therefore did **not** guarantee
the intended common-selected8-call17:00–17:20 window. Its earlier armed receipt
was true as a process observation, but insufficient as lifecycle integration.

This is a separately versioned deadline-only repair. Neither the old shared
resident nor any frozen/live source archive was edited. All v1 evaluationPLANs,
original predecessor references and original43-cycle/call/deadline bounds remain
bound in the new plans. No additional evaluation quota is introduced. V1 had
zero charged evaluation calls and no native claim at preparation.

## Plan published before arming

The diagnosis and scoped plan were posted to COORD before nativeCPU validation;
the exact source/plan hashes and the **no-current-signals** refinement were posted
again before the four CPU processes were launched13:53:05UTC.

**No production process is signalled now, including the old CPU timers.**
Only during **16:55:00–16:59:20 UTC, September15,2026** may each controller:

1. Identity-verify and retire its original **CPU-only** evaluation timer after
   proving empty startupCVD, noGPU descriptors, exact command/cwd/executable/
   UID/boot/PID/start and zero old evaluation claims/ledger. This prevents that
   timer from competing at17:00; its files and resulting terminal are retained.
2. Find an optimistic clean math boundary, acquire the originalCOUNTERS lock,
   open exact own guard/native pidfds, briefly hold both and **recheck** custody
   and the complete boundary. A busy/changed/incomplete boundary resumes both;
   no outcome or accuracy appears in this decision.
3. Retire only those exact owned native/guard processes at the verified boundary,
   preserve the authentic guard terminal, and hash-verify counters, reservations,
   carry, captures, accepted submission and parent archives after actual exit.
   Write a new `RELEASED.json`; do not fabricate natural completion or sleep.

The admitted boundaries are either:

- **Complete collection awaiting the shared checkpoint:** exactly6 actual
  COMPLETE child captures covering two sequential episodes, open turns,
  presleep and own reflection; exact accepted common submission; source-backed
  carry; all6native parent deliveries and their closed archives; no unaccounted
  charge, next cycle, checkpoint transition or live readout child.
- **Fully completed shared-checkpoint/DEV cycle:** matching common committed
  checkpoint and shared generation, complete20-call freshDEV readout plus AFTER
  and MOUNTED_FINAL, complete cycle counters and no live readout child/next charge.

COMPLETE here describes a finished native capture, **not a correct outcome**.
Negative attempts and MISSING parents remain preserved; no score-based selection.
Common optimizer ownership remains F1; math has no local optimizer to discard.

If no verified boundary is available by16:59:20, write **NOT_RUN**. If custody,
preservation or authentic-terminal verification fails, do not admit evaluation.
No late release, replay, silent reset or duplicate FINAL is allowed. The evaluator
independently verifies the exact drainPLAN/RELEASED/boundary hashes, predecessor
absence, old CPU-timer retirement and absence of any old morning-FINAL attempt.
Only then may Main's canonical selector and strict fresh GPU admission lead to
the separate8-call readout. Route's F1/A1 fuse is not counted as math release.

## Actual readiness and process observations

At **13:51:33UTC**, read-only nativeCPU audits of both real lanes found a complete
accepted generation0 collection boundary with preserved source/carry/closed parent
archives. These were **no-signal preparation snapshots**, not a future release
authorization; all checks repeat at the deadline.

At **13:53:39.136333UTC**, all four new CPU processes were verified alive with
empty startupCVD. Both original natives, both guards and both old CPU timers were
also identity-verified unchanged. No release, timer-retirement or new native claim
existed. The actual observations are in `ARMED_HEALTH.json`.

| Branch | New drain CPU PID | New evaluation CPU PID | Original native / guard | Old CPU timer |
| --- | ---: | ---: | --- | ---: |
| F2 | 1760859 | 1760860 | 1073927 /1072494 | 1523331 |
| A2 | 1760861 | 1760862 | 1073926 /1072495 | 1523332 |

**Actual release and FINAL readout are still pending their clock gates.** Arming
is not reported as release, model residency or evaluation completion.

## Exact roots, source and budgets

Immutable successor source:
`/localhome/local-rohing/orch_math_feedback_uptake_r118_final_source_20260915_attempt3`.
617Python-file manifestSHA:
`81449143613a83752fdb1a7c8e0b6925f8725eaf87eaf101a8677ba205ef8a26`.
Source2/drain1 was an unarmed CPU-only candidate; preserved unchanged.

New drain root:
`/localhome/local-rohing/orch_math_feedback_uptake_r118_final_drain_20260915_attempt2`.
- `lane1/PLAN.json` SHA `f701e74223f39a25ff343fb666262cb1149f0bf59b5690b1b736245dab7eb9d2`.
- `lane5/PLAN.json` SHA `1b4b258881f98a4ef2445a4b921ce58205119029393e2b23a20d3490e271adc5`.

New eval root:
`/localhome/local-rohing/orch_math_feedback_uptake_r118_final_20260915_attempt2`.
- `lane1/PLAN.json` SHA `8ef4c2887562d49ab1dde32d84fd9629a8d34b135273d5de435e97080b4bc664`.
- `lane5/PLAN.json` SHA `3f18ff70ec936d4cbf6a7d38351b30d181b2b2ae76cc6b4c6f599ac38e9cb3de`.

Unchanged allocation:8primaryFINAL calls per branch/16pair, zero parent calls,
optimizer steps, replay rows or attachedOPEN. Same sealed8IDs/default2048decoder,
17:00–17:20UTC with20seconds cleanup, lease6hour margin; original16:59native/
17:02hard remains unchanged. The earlier v1 PLAN references are retained exactly,
not overwritten or reset. Both old/new timers can coexist **only as CPU waiters**;
v2 requires proven old-timer retirement and zero v1 evaluation calls.

Main's sole `FINAL_SELECTION.json` and purev2 `validate_selection` remain the
only checkpoint selection, sourceSHA
`64ccee2884b1dddafde70da8ccc2795127c8a4553fb6eb1a301484da369334ed`.
No commonCONFIG mutation, competing selector or early FINAL read was performed.

## Tests and publication

**108local and108native CPU tests pass**:18drain,20evaluation,16Main selector and
54existing shared regressions. Tests cover both clean-boundary types, partial
collection/checkpoint/readout rejection, carry/charge changes, closed MISSING
parent archives, PIDreuse/exec mismatch, no signals before/after the window,
unsafe-hold and exception resumption, original decoder and canonical selector.
A real pidfd test retires only synthetic CPU children while leaving a third
foreign sentinel alive. Production signals/model/provider calls remain zero.

Own source hashes:
- `gpu/orch_math_feedback_uptake_r118_final.py`: `007415e5a2543bf0373c7928de5b070f3aef7d746803ed94f518f87fb434b9fb`.
- `gpu/orch_math_feedback_uptake_r118_final_drain.py`: `e924ba3377e7f52321630feb4dd612a87e8aaa58bb9b47bc1a417a4a0ce38af7`.
- `tests/orch_math_feedback_uptake_r118_final_test.py`: `50304c835a8cfd77c2984587588721d443af67b20093251e31e4baadcff185f8`.
- `tests/orch_math_feedback_uptake_r118_final_drain_test.py`: `14e783d1037bde5c4fbab1de987a53a4010c04dca766b7dacad4ff338219d3e8`.

Main stages only `STAGE_PATHS.txt`; no Git mutation by this worker. All raw
captures, parent transcripts and sealed content stay onnode. The existing DEV
full-text verification receipt remains valid as a pre-shared observation; this
repair made no additional readout/model calls.

## Executed commands — do not duplicate

Working directory is the immutable source3 root; startupCVD is empty and
`PYTHONPATH` points to that source. For each physical1/5, these are already armed:

```sh
/localhome/local-rohing/v2/venv/bin/python -B -m gpu.orch_math_feedback_uptake_r118_final_drain run \
  --plan /localhome/local-rohing/orch_math_feedback_uptake_r118_final_drain_20260915_attempt2/lane1/PLAN.json
/localhome/local-rohing/v2/venv/bin/python -B -m gpu.orch_math_feedback_uptake_r118_final schedule \
  --root /localhome/local-rohing/orch_math_feedback_uptake_r118_final_20260915_attempt2/lane1
```

Substitute `lane5` only to identify the already-running A2 commands, not to
launch duplicates. Future compact evidence: drain `PREVIOUS_TIMER_RETIRED.json`,
`BOUNDARY.json`, `RELEASED.json` or `NOT_RUN.json`; eval `TERMINAL.json`, `LEDGER.json`,
`COMPLETE.json` or `NOT_RUN.json`. Do not report absent future files as success.
