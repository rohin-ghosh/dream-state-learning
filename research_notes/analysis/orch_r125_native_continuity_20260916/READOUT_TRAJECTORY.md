# R125 fixed-panel trajectory — September 16, 2026, 07:35 UTC

## Scope and provenance

CPU-only reduction of all 640 existing calls from fresh-process readouts
0–9: the same 32 tasks, ON/OFF pairs, empty context, parent absent, unchanged
prompts and deterministic decoder. No readouts were rerun and no held output
entered training or parent prompts. The reducer verifies receipt hashes,
reservation joins, captured prompts/responses, the recorded before/after
attestations and suite/decoder consistency; it does not independently prove
runtime isolation. All raw responses remain node-local.

`READOUT_TRAJECTORY_0_9.json` pins the node-local complete reduction, source
hash, checkpoint provenance and aggregates. Each panel binds 132 source
receipts. Reducer regression suite: 58 tests passed, independently rerun by
Main in 58.81 seconds. Valid budget hits are retained and counted, never
discarded as malformed data. This panel contained no budget hits.

## Observations, not cognition-success labels

OFF is byte-identical to its zero-step outputs at every checkpoint: 381
generated tokens total and 24/32 fixed-task passes. ON results follow.
Tokens include terminal EOS. Changed outputs mean exact text inequality
against ON at step zero, not an improvement judgment.

| Sleep | Cumulative steps | ON tokens | ON passes / 32 | Changed outputs / 32 |
|---|---:|---:|---:|---:|
| 0 | 0 | 381 | 24 | 0 |
| 1 | 48 | 382 | 25 | 3 |
| 2 | 99 | 390 | 23 | 4 |
| 3 | 153 | 388 | 25 | 4 |
| 4 | 210 | 383 | 25 | 2 |
| 5 | 270 | 389 | 25 | 3 |
| 6 | 323 | 389 | 25 | 3 |
| 7 | 379 | 389 | 25 | 3 |
| 8 | 438 | 385 | 24 | 2 |
| 9 | 500 | 388 | 24 | 4 |

There are no known journal-marker strings in these held outputs, including
before the plain-context repair. Thus marker absence on this panel cannot be
attributed to that repair. ON changes on two to four tasks after sleep, but
neither sustained capability improvement nor increased useful cognition is
established. This small capability panel is not a direct test of autonomous
inquiry, functional metacognition or cross-task skill acquisition.

Separately, the training stream still recites costs and generic improvement
lists after the repair; 13 of its first 14 post-transition responses contain
CJK characters. That is an observation about the language used, not a failure
criterion. The substantive concern is ritualized content without demonstrated
changes in strategy. No language instruction has been injected.

## A2 continuation and parent delivery

Exact C52 recovery saved C53 at 07:30:04 UTC: 21,639 → 22,185 optimizer
steps, 91,909 new child-token exposures and 10,439 anchor-token exposures.
The existing mix used six new rows presented 16 times and 450 eligible
rehearsal rows once, with anchor objective weight 0.25. Six historical rows
failed the existing special-token target check; they were not silently used.

C53 fresh DEV readout completed at 07:32:53 UTC. C54 started at 07:33:11
UTC and delivered both C53 parent dispositions: one SILENT and one COMPLETE.
The COMPLETE Astra guidance is present in CALL1301's actual child input,
verified against the response receipt. This establishes input delivery, not
behavioral adoption or retained learning. Raw history, checkpoint lineage,
optimizer state and existing queued-request identities remain preserved.

## Next comparison

Keep the current fixed panel unchanged. A separate prospective test should
check whether a concrete parent intervention changes the child's subsequent
action or strategy and whether that change survives a fresh-context readout;
changed text, Chinese output, token counts and cost narration alone cannot
answer that question. No such success is claimed here, and no new parent
message or live training policy was introduced by this analysis.
