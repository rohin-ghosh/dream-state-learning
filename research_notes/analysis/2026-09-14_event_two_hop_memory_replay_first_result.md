# SEQ-254: stronger old-trajectory replay does not repair goal selection

September14,2026. One native fit and fresh AFTER COMPLETE; engineering repair
target FAILED. Recipe CLOSED, not a failed launch or an invitation to a sweep.
Source28b44b19a050bbd431bad884f830d05ef0762f64. Bounded independent review pending.

| Endpoint | Original write253 | Stronger replay254 |
|---|---:|---:|
| New EVENT recall W0 / W8 | 4/4 each | 4/4 each |
| Fresh PARAMETRIC / OWN_TEXT goals | 2/4 each | 2/4 each |
| Fixed-display opposite-goal pairs | 0/2 | 0/2 |
| UNAVAILABLE goals | 0/4 | 0/4 |
| Old16facts W0 / W8 | 16/16 each | 16/16 each |
| Held audit | 16/16 | 15/16 |
| Original taught graph OWN_TEXT | 3/4 | 3/4 |

Both fits start at37ec, not sequentially at253's9d36.254 preserves the254
source rows and each of253's four batch indexes, appending two actual old
trajectory rows per update.100updates, batch6, freshAdamW3e-5, seed0, rank8;
212trajectory presentations total and200new-memory presentations (50perfact).
Actual18443labels versus16175:2268extra, matching the added200trajectory
presentations. This increased-budget repair is not equal-token causal evidence.
Completed253BEFORE was reused through exact bindings; no new exposure, parent,
baseline execution, reference refit or rewritten child target occurred.

All four PARAMETRIC command sequences equal253's casewise. Tasks1,2 reach
their goals; task0 takes the wrong legal branch; task3 prematurely selects the
second-edge port and commits nothing. Correct records still reach the actor.
The first-port/no-memory counterexample therefore still applies. The repair
did not recover the lost fresh-text case or goal-pair sensitivity and lost one
true audit case (7/8true,8/8fault). It fails its predeclared >=3/4freshgoals and
16/16audit targets. A changed adapter is verified, so this is not a no-update
instrumentation failure. It does not show that all replay strategies fail.

The next work changes coverage rather than repeating this dose. New source
collection and paired-goal baseline are specified separately, without fits:
two TRAIN worlds, both display orders,48actualcoached targets; two PROBE
identifier instances outside that teaching set.250 already taught opposite
goals under order0, so the hypothesis is insufficient generalization/coverage,
not that conditional examples were entirely absent. The parent cannot see
PROBE cases/scores, and successful goal-directed transfer is not assumed.

## Native cost and recovery

Node2GPU0 guardian402364, root
`/tmp/astra_event_two_hop_memory_replay_20260914_attempt1`,16:25:50–16:35:43UTC.
Train347.363s, AFTER243.941s/166calls, summed591.303native-phase seconds
(~0.1643dedicatedA40h), including overheads. Source/state/base checksPASS.
Saved/reloaded state52658b3efe743409ef69ef67986b77e3d21f0a3ba28552d8bfb5b7471637786d.
Main12CPUtests/native preparation passed before launch. No process was killed.

Complete source/adapter/calls:
`gpu_artifacts_local/astra_event_two_hop_memory_replay_terminal_20260914_attempt1/extracted`.
Local/remote archive SHA256:
`f23f71a11e991563ee017fbfc14a467b6c88ad711729bfb8ea07ca51676607b5`.
The earlier truncated packaging file was never extracted or used for this run;
the complete checked source archive and original artifacts remain preserved.
One DEV instance/lineage; no population, H1/H2 or full-flywheel claim.
