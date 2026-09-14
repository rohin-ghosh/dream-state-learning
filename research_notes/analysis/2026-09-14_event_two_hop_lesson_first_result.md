# SEQ-250: source-guided child trajectories improve contextual continuation

September14,2026. Completed source0b495971f8ecb2353162757abbdb938effa4493b,
node2GPU0 guardian393070,15:05:07–15:13:29UTC. One actual coached collection,
one100-update sleep, and fresh parent-free readout. Independent review pending.

## Actual results

| Parent-free endpoint | Saved no-write parent (SEQ249) | After trajectory sleep |
|---|---:|---:|
| Own-text two-hop goals | 0/4 | 3/4 |
| Own-text trained presentations (tasks0,2) | 0/2 | 2/2 |
| Own-text reversed displays (tasks1,3) | 0/2 | 1/2 |
| Parametric-reader goals | 0/4 | 0/4 |
| Unavailable-memory goals | 0/4 | 0/4 |
| Base actor with supplied own text | 0/4 | 0/4 |
| Old exact recall W0/W8, each | 16 facts previously supported across prior stages | 16/16 |
| Original held audit | 16/16 in SEQ245 | 16/16 |

All four after-own-text trajectories read four exact records and make two legal
commits. Tasks0,1,2 reach the requested final goal. Task3 (second goal, reversed
display) instead follows the complete first-goal path and ends at the wrong
terminal. This is a genuine remaining action-choice failure, not a malformed
port or an artificial STOP gate. Preserve3/4 rather than reporting full closure.
The trained order0 presentations both pass; only1/2 reversed presentations
passes. This is ONE exposed graph and ONE adapter lineage, not unseen worlds or
independent seed replication. The opposite first actions were taught explicitly.

Parametric/unavailable conditions each end with4duplicate-address failures,
after four reads and one actual move per task. Parametric reads exactly match
0/16 source strings. No new EVENT-memory targets were trained in this sleep;
source facts occur in masked student prefixes, so they were not wholly hidden
from training. Base-actor outcomes remain2invalid_route,1dead_end,1duplicate,
exactly as before. No unsupported memory or parametric hopping claim follows.

## Teaching and write provenance

The source-informed algorithmic parent supplies one next-command hint from
actual child EVENT records. Both six-command coached paths completed, yielding
12actual child responses. The helper replays actual native outputs, memory
returns and committed transitions; no expected command is substituted for a
child response. Teacher hints are absent from all student prefixes and targets.
Only final actual assistant response+EOT is supervised; preceding child context
is masked. This is researcher-prepared source-grounded teaching, not a child
independently discovering a plan or autonomously selecting its own curriculum.

Exactly100freshAdamW updates at3e-5, rank8 on frozen Qwen2.5-7B, seed0, batch4.
Mixture:128old-memory,20cue,62audit and12trajectory rows;100old,100behavior
and200trajectory presentations. Actual supervised tokens8245; trajectory doses
[17,17,17,17,17,17,17,17,16,16,16,16]. Final tensor state
`37ec37884e4b0b679edd1dba1be1dec3474589e992649f3a33e7e3b1ec78b8c0`
differs from the shared initial207ad43e and is loaded unchanged by fresh AFTER.
Both readonly tensor/file checks and all frozen-base checks pass.

AFTER uses147native calls:99controller/reader calls,32old-recall calls and16
held audits. Native walls: collection62.008s,train232.791s,AFTER203.157s;
sum497.956s, approximately0.1383dedicatedA40h, not kernel-active utilization.
No reference fit or prior EVENT collection was repeated. The unchanged parent
is a saved no-write baseline, not a budget-matched no-gradient life.

## Interpretation and next test

The narrow observation is persistent, parent-free improvement at executing
source-informed two-action trajectories on the taught graph, with retained old
recall/checker behavior and a continuing dependence on supplied accurate text.
The same-world and order-dependent result does not prove general path inference,
autonomous improvement, selection superiority, H1/H2 or a full parametric loop.
Next: a fresh opaque-ID world, no teaching or fit, comparing taught versus
unchanged-parent actors on identical actual child text and unavailable-memory
controls. Do not improve the current score by changing its parser or examples.

Complete terminal source/adapter/calls/masks/receipts:
`gpu_artifacts_local/astra_event_two_hop_lesson_terminal_20260914_attempt1/extracted`.
Local/remote archiveSHA256:
`2acae64c4be4abd492f7efb0f50675509d7d0650360f7a23e2575e38ceb7f4a6`.
See `2026-09-14_event_two_hop_lesson_independent_result.md` for review status.
