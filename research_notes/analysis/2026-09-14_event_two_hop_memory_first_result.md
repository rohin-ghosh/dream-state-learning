# SEQ-253: fresh parametric records support two-step actions, not reliable goal selection

September14,2026. BEFORE, one sleep write and fresh AFTER are COMPLETE. Source
7c773aacaf0c6a47f510d6f38459ac8270521335. Bounded independent review PASS:
`2026-09-14_event_two_hop_memory_independent_result.md`. The review independently
joins source records, actual reader/actor calls, transitions, masks/dose and
saved-state receipts; it does not independently authenticate live tensors.

| Endpoint | Taught37ec before write | Saved9d36 after write |
|---|---:|---:|
| Fresh EVENT exact recall W0 / W8 | 0/4 each | 4/4 each |
| Fresh PARAMETRIC final goals | 0/4 | 2/4 |
| Fresh OWN_TEXT final goals | 3/4 (reused251) | 2/4 |
| Fresh UNAVAILABLE final goals | 0/4 (reused251) | 0/4 |
| Old16facts exact recall W0 / W8 | 16/16 each (reused250) | 16/16 each |
| Held audit | 16/16 (reused250) | 16/16 |
| Original taught graph OWN_TEXT | 3/4 (reused250) | 3/4 |

Four actual child EVENT records from251, not invented target facts, supply32
query-wrapper views. One100-update sleep starts37ec and uses100old-memory,
100behavior and200new-memory presentations (50pernewfact). Actual16175
supervised labels;254source rows; freshAdamW3e-5, seed0, rank8, frozenbase.
Only actual targets/EOT supervised. No new teacher, exposure collection or
automatic refit occurred. BEFORE measured its zero baseline rather than assuming
or requiring it. All phases run separately, with fresh saved-adapter reload.

In AFTER's actual action episodes, **16/16 parametric reader responses equal
the corresponding captured child EVENT bytes** (final-LF canonicalization).
The reader gets only an address, not the graph/goal/context or stored-text
fallback. The actor and reader use the same9d36 adapter. PARAMETRIC and OWN_TEXT
produce identical command sequences case-by-case and succeed on tasks1,2.
Each success has four actual reads, two source-supported committed transitions,
and arrival at the requested goal. UNAVAILABLE remains0/4.

The two failures localize a remaining action problem despite correct memories:
task0 follows two legal edges to the wrong goal; task3 selects the genuine
second-edge port before reaching its source node and commits nothing. Task0
and task2 issue identical routes although their goals differ. This is **not
reliable goal-conditioned composition**. Two successes out of four do not by
themselves beat a simple first-available-branch baseline on this balanced graph;
unavailable failure alone cannot establish semantic goal-directed memory use.
Main also executed that deterministic comparator against the saved world using
the unchanged `hop.run_episode(..., protocol='turnbound')`: choose the first
currently listed PORT, never READ and never inspect GOAL. It makes two legal
moves on all four tasks and succeeds on exactly tasks1,2, the same successful
cases as9d36. Zero model calls/fits. Task3 differs only in failure mode: baseline
reaches the wrong goal, while the child skips a step. This is a diagnostic
reference, not an additional learned arm or an independent replicate.
An additional **post-hoc descriptive** summary pairs opposite goals under the
same display order: tasks(0,2) and(1,3).253 solves both members of0/2 pairs;
the pre-write251 taught text snapshot solves1/2 pairs. This preserves the
original task denominator and is not a newly substituted primary success gate.
It makes the missing goal-sensitive choice more visible than2/4 arrivals alone.
The evidence is a partial operational connection—experienced source record →
sleep write → fresh parametric retrieval → actual multistep behavior—not a
validated general planner, complete flywheel, H1/H2 or learning-efficiency result.

Memory content acquisition is no longer the immediate bottleneck on this
instance. The write also changes contextual policy: fresh-text3/4→2/4 while
old facts/audit/taught-graph behavior remain at their prior counts. More memory
dose is not justified by the exact4/4 recall. The next finite repair tests stronger
replay of the already successful actual trajectory targets during this same
write; it does not manufacture new targets or require a positive result.

## Cost, state and reproducibility

Node2GPU1 guardian398924, root `/tmp/astra_event_two_hop_memory_20260914_attempt1`,
15:58:28–16:08:55UTC. BEFORE142.670s/48calls, train234.455s/100updates,
AFTER246.596s/166calls:623.721summed native-phase s (~0.1733dedicatedA40h).
These times include checks/overheads, not just kernels. Saved/reloaded state:
9d36743c85f82ef0e064484369393a4761c8e2cdd512e1527818f9c4ca5a9c86.
Native base/state/source-file checksPASS. Main26CPUtests and actual-source
PREPARED_NO_MODEL preceded launch. All cases/failures and original artifacts
remain intact; no process was killed. One DEV graph, one child lineage and
one training seed; no independent population replication claim.

Complete source/adapter/calls capsule:
`gpu_artifacts_local/astra_event_two_hop_memory_terminal_20260914_attempt1/extracted`.
Local/remote archive SHA256:
`82313377e0a72f79ebb6a1cca2439f27a54b97718ce2db6fd6aaf8ed190ba7e4`.
