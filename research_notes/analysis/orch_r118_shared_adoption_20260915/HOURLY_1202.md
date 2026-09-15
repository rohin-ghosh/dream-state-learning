# Parenting status — September 15, 2026, 12:02 UTC

Five-wrapper census at 11:57:49–50 UTC: **40/40 memory-resident, 20/40 with
positive instantaneous GPU utilization**. Residency is not sustained computation.
Node2 training reloads and parent waits remain real bottlenecks, not vacant GPUs.

## Shared-learner handoff

The eight node5 branches still use the declared per-branch fallback. Shared
consolidation has **not** started. Route executable V2_R1 and code executable
readiness are node-local; math and grid executable successors are being bound
and tested while their existing lives continue. No fallback life has been stopped
for this handoff. The route boundary requests remain unarmed and expire at
12:45:23 UTC. Only after all eight executable clients are ready will their next
completed two-episode boundaries be coordinated; F1's latest completed adapter,
optimizer/RNG, rehearsal history and exposure counters then seed the shared child.
The displayed candidate checkpoints are not rollback targets.

Main added a bounded adoption helper with 17 CPU tests (44 with the coordinator
tests): checks runnable rather than helper-only readiness, source/test hashes,
all-eight identities and held exclusions, unchanged bounds and boundary files,
absent predecessor PIDs, latest F1 state, and immutable initialization. It does
not replace family-specific boundary release or signal any actor. No new GPU
update is claimed by those CPU tests.

## Delivered parenting and exposure accounting

These are **published broker outcomes**, not a join proving the child consumed
each response. Pending calls are outside the published denominator. All rows are
lifetime snapshots of these existing roots; the JSON also reports the last
30-minute window and phase-specific TRAIN token counts.

| Branch | COMPLETE | MISSING | SILENT | Generated TRAIN token IDs | Completed optimizer steps | Child-token exposures |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| F1 route | 2 | 51 | 0 | 3,326 | 930 | 60,110 |
| A1 route | 17 | 7 | 3 | 1,447 | 281 | 17,907 |
| F2 math | 14 | 34 | 0 | 14,077 | 0 | unknown |
| A2 math | 18 | 8 | 1 | 6,354 | 0 | unknown |
| F3 code | 22 | 57 | 0 | 46,884 | 0 | unknown |
| A3 code | 6 | 21 | 0 | 18,787 | 0 | unknown |
| F4 grid | 1 | 27 | 0 | 37,379 | 0 | unknown |
| A4 grid | 15 | 11 | 0 | 34,532 | 0 | unknown |

F2/A2/F3/A3/F4/A4 currently have no optimizer and are elicitation-only. Unknown
exposure fields are not silently converted to measured zero. No independent
semantic intervention-class or novel-thought scoring is claimed by this count
reduction. The source manifest hashes 1,069 node-local captures; no raw
transcripts or FINAL outputs were transferred to the VM.

F4's first genuine completed/consumed parent reply was P0023 at 11:40:23 UTC,
in the original 120-second era. P0026 under the new 600-second wait was delivered
as MISSING: the provider CLI exited successfully, but its `num_turns=2` tripped
the existing one-turn validator. This is distinct from F1's documented provider
safeguard refusals and from timeouts. The broker owner is checking the CLI
turn-count semantics; no old slot has been retried or retrospectively relabelled.

## What the evidence does and does not show

The route visibility audit found enacted open inspections and transient prose at
F1 sleep 2, followed by protocol-only DEV responses at sleep 3. This is not
retained metacognitive improvement. Math/code retain their complete visible
outputs; storage fidelity does not establish learning quality. The goal of
retained, parent-free gains against frozen and unparented controls remains
**unproven**. The shared parenting-systems comparison will not be represented as
a controlled per-parent LoRA comparison.

Evidence: `HOURLY_1202.json`; `../R118_ROUTE_VISIBILITY_20260915_1136.md`;
`../orch_r115_grid_pair_20260915/F4_FIRST_COMPLETE_CORRECTION_1156.json`.
