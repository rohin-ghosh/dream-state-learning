# SEQ-255 — actual paired-goal teaching data and unchanged-child baseline

Executed September 14, 2026, 16:48:58–16:55:36 UTC, node 2 GPU 0,
guardian 404781. Source `a0fdc9a7dda2d84e5f535b3b54e31741ce753c7a`;
root `/tmp/astra_goal_pair_collection_20260914_attempt1`.
All three native phases completed, with zero fits and zero updates. Each loaded
and preserved adapter `37ec37884e4b0b679edd1dba1be1dec3474589e992649f3a33e7e3b1ec78b8c0`.

## Actual collection and teaching

EXPOSE made 32 calls and produced 16 source-valid EVENT records across four
disjoint identifier worlds. TEACH made 48 coached child calls in TRAIN-A/B,
yielding 48 admitted actual targets. Both coached TRAIN worlds completed all
four tasks and both goal pairs. These are successful guided data collection,
not learned autonomous behavior. Guidance is absent from saved student prefixes;
PROBE-A/B records and outcomes never enter the teaching targets or parent input.

BASELINE used the unchanged child, fresh process, no parent, and 96 calls.

| World | OWN_TEXT tasks | OWN_TEXT goal pairs | UNAVAILABLE tasks | UNAVAILABLE pairs |
|---|---:|---:|---:|---:|
| PROBE-A | 2/4 | 1/2 | 0/4 | 0/2 |
| PROBE-B | 3/4 | 1/2 | 0/4 | 0/2 |
| Total | 5/8 | 2/4 | 0/8 | 0/4 |

A pair requires success on both opposite goals under the same display order,
distinct source-correct first ports, and two legal commits on each task. In A,
tasks 0/2 succeed; reversed-order tasks 1/3 choose opposite wrong branches. In B,
reversed-order tasks 1/3 succeed; tasks 0/2 choose the same first port and task 2
fails. All OWN_TEXT episodes make two legal moves. All UNAVAILABLE episodes
terminate with `duplicate_address`.

## Interpretation and next test

The existing child already has partial goal-sensitive behavior on these new
instances. This corrects any blanket statement that goal conditioning is absent.
The next comparison tests robustness across additional worlds/display orders,
not the first introduction of goal conditioning. These are two identifier
instances of one topology, one exposed DEV lineage, not independent development
seeds, generalized planning, clean final-gym evidence, or H1/H2 results.

The incremental FULL_TARGET versus NEW_TRAJECTORY_LOSS_OFF protocol was bound
at `b74cb8c4` before new fits and before Main inspected these baseline scores.
Both start 37ec, keep original trajectory supervision, and differ only in new
trajectory labels with shared full-reference loss denominators. No fit has
launched at this result entry. No collection or baseline repetition is needed.

## Cost and evidence

EXPOSE 129.193 s; TEACH 122.094 s; BASELINE 143.258 s: 394.545 native-phase
seconds, approximately 0.1096 A40-hours, 176 calls total. Wall figures include
native loading/checking and are not pure generation throughput.

Local capsule:
`gpu_artifacts_local/astra_goal_pair_collection_terminal_20260914_attempt1/extracted`.
Archive SHA256 `e66d7d7e1dd3a01189cd454ea7ad9a53970685fcf46de30b1a6732a564585e7e`.
Raw `expose/RESULT.json`, `teach/RESULT.json`, `baseline/RESULT.json`, captured
calls, collections, lessons and episodes support the counts and lineage.
Independent review assigned to Ramanujan; pending at this entry.
