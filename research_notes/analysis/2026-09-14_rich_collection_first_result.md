# Rich-v1 collection — SEQ261, 2026-09-14

## Executed result

All four shards completed EXPOSE, TEACH, CRITIQUE and unchanged-state BASELINE.
This is zero-fit collection, not an experiment demonstrating learned richness.
All80EVENTs are valid. All64TEACHepisodes were attempted and failed the frozen
v1 candidate rule: zero rows in each paired supervision view, no fit-ready data.

| Shard | TEACH calls | Missing literal prediction label | Other rejection | CRITIQUE calls | BASELINE calls |
|---|---:|---:|---|---:|---:|
| 0 | 21 | 14 | 1 envelope;1 short ROUTE | 16 | 140 |
| 1 | 25 | 14 | 1 short ROUTE;1 unseen ID | 16 | 141 |
| 2 | 28 | 12 | 1 envelope;3 short ROUTE | 16 | 137 |
| 3 | 20 | 16 | none | 16 | 144 |

Together160EXPOSE+94TEACH+64CRITIQUE+562BASELINE=880native calls. Two critiques
fail the native/content-shape check; the other62 are unreviewed text candidates,
not verified good critiques or training targets. Total phase wall3268.518428s,
about0.908allocated A100-hours, including per-phase setup; not kernel time.

Command-only parent-free baseline from unchanged37ec:

| Panel | Goals | Opposite-goal pairs |
|---|---:|---:|
| TRAIN OWN_TEXT | 33/64 | 3/32 |
| PROBE OWN_TEXT | 6/16 | 1/8 |
| PROBE UNAVAILABLE | 1/16 | 0/8 |

## What failed, and what remains unmeasured

The frozen helper called its prose checker before returning the projected
command.56of64episodes stopped for missing a literal `PREDICTION: ` line.
For example shard0/CALL000 has an exact legal READ and prose acknowledging
that its listed event has not yet been read. Its saved episode has zero
reads/routes: that action was never executed. The explicit raw example and
file hashes are in `2026-09-14_rich_prediction_gate_successor_proposal.md`.

Therefore zero candidates is a valid failure of this declared collection
recipe, not evidence that the child cannot reason or complete the underlying
actions. Nor does parseable prose establish useful richness: listing IDs and
generic expectations may still fail a content-based floor. Identifier
membership and a heading never certified relational truth in v1.

Close v1 unchanged. The separate action-first protocol executes only legal
exact commands, records prose findings separately, and still requires
outcome AND grounded useful content before any shared-source fit admission.
It reuses actual exposures/baselines and makes new TEACH calls, rather than
inventing continuations or retroactively accepting v1 episodes. No rich fit
or efficacy claim is licensed by this collection result.

## Provenance and review

A100 root `/tmp/astra_rich_collection_20260914_attempt1`, source
`803f59c809d836f60f7a22b57a75b4d045626994`; protocol
`339c25c05cdb1bd6ba07bfd22520c68df6f23117fed0627cb245e23c6ba2bd2f`.
All phases record unchanged37ec with frozen base; no adapter updates or parent
access to PROBE scores. Source-informed teaching is an exposed DEV ceiling,
not an authentic child-generated planning lineage. Rich targets were actual
child outputs with parent guidance removed from student prefixes.

Terminal capsule on VM `/data`:
`gpu_artifacts_local/astra_rich_collection_terminal_20260914_attempt1/terminal.tar.gz`
SHA `2d7a387dba0006b7b066f0d41459a017ce2b0059c48c269f8c90297e76c905eb`.
Per-shard phaseRESULT,TEACH LESSONS/captures, critique documents and baseline
DATA/panel episodes remain under its extracted root. Main reduced the stored
summaries and sampled the label rejection; independent full-stage review is
pending in `2026-09-14_rich_collection_independent_result.md`.
