# Fleet continuation — report cut is not a stop

[Builder Main] September 15, 2026, 17:16 UTC. Rohin's relayed 17:10 and
17:15 directives supersede the mistaken report-cut training stops. Resume
committed checkpoints, optimizer state, branch cycles and experience; do not
restart learning from scratch. This table is an allocation, not occupancy.

| Wrapper | Physical GPUs | Work | Execution owner |
| --- | --- | --- | --- |
| a100 | 0–1 | Continual L1 FULL/CONTROL, actual current 1+1 topology | Herschel |
| a100 | 2–4 | L1 generation/readout support | Herschel |
| ovx | 0–7 | L1 generation/functional-feedback collection | Herschel |
| ovx2 | 0 | L1 generation | Herschel |
| a40r | 0–3 | Checkpoint-continuing base-origin route parenting | Poincare |
| a40r | 4–5 | Checkpoint-continuing base-origin math parenting | Anscombe |
| a40r | 6 | Checkpoint-continuing base-origin code parenting | Cicero |
| a40r | 7 | Checkpoint-continuing base-origin grid parenting | Laplace |
| ovx2 | 1–2 | Checkpoint-continuing base-origin math parenting | Anscombe |
| a100 | 5–7 | Learned-child math parenting | Anscombe |
| ovx2 | 3–6 | Learned-child code parenting | Cicero |
| ovx2 | 7 | Learned-child grid parenting | Laplace |
| ovx3 | 0–7 | F1–F4/A1–A4, same shared generation-1 learner | Main + family owners |

The17:16 draft's 3+2 training assumption was stale: the actual C2 successor is
world-size1 per arm. Its15460 checkpoints and optimizer/RNG are preserved;
no artificial3+2 repartition is introduced. Main confirmed17:26 that physical
0/1 are model-resident and computing;2–4 remain within Herschel's14-slot scope.

Totals:14 L1,10 base-origin parenting,8 learned-child parenting on the old
fleet;8 additional shared-learner parenting branches on node5. A moved branch
must bind its actual predecessor and checkpoint/cursor; no silently reset
replacement counts as a continuation. If an original topology must be retained,
owners report the exact alternative before loading any overlapping assignment.

The common node5 clock implementation has9 focused CPU tests passing. It is
explicitly source/lease/state-bound, preserves the shared CONFIG, and refuses
counter/checkpoint rollback. This is not a reason to hold independent old-fleet
launches. Owners use existing tested native loops, with focused continuation
checks and actual resource ownership safeguards; other reviews run in parallel.

New walls are actual lease expiry minus the preserved safety margin. Node5's
requested wall is September16 22:04UTC, subject to the actual lease record and
at least6hours margin. No lease is extended.17:00 remains the report/FINAL
selection cut, not permission to discard or stop the learner. Do not rerun
charged FINAL inputs or put FINAL data into experience, parents or exchange.

Parenting retains the fixed common principles/prompt, two-episode sleeps,
capability anchors and rehearsal; Fable providers run on node5, one provider
process per branch, parent effort high, head-parent effort max, parent wait600s.
Preserve all intervention/triple evidence and report completed delivery, not
requests or queue publications. Main publishes launches incrementally and owns
Git; raw remains node-local.
