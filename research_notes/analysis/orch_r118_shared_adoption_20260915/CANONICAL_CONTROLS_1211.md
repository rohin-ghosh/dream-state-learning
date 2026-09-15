# Existing control-system audit — September 15, 2026, 12:11 UTC

This is a new read-only reduction of the existing canonical route campaign,
not a new experiment or newly completed cycle. No GPU calls, schedule changes,
new controls, parent prompts or raw-transcript transfers were made.

The reducer verifies identical task hashes across GUIDED, UNPARENTED and NO_LORA
at each corresponding completed readout C0–C6. All 18 post-sleep readouts C1–C6
verify a fresh process, parent absent, and the exact saved child identity.
Saved adapter-file hashes and frozen-base identity checks also pass. NO_LORA
means the frozen base without an adapter; it is **not** a frozen copy of the
initial route adapter.

| Existing arm | C1–C6 ancillary successes | Episodes | Saved optimizer steps |
| --- | ---: | ---: | ---: |
| GUIDED | 10 | 12 | 424 |
| UNPARENTED | 8 | 12 | 536 |
| Parented NO_LORA | 6 | 12 | 0 |

At C0 all arms solved 1/2. GUIDED and UNPARENTED tie at C1/C2/C3/C5; GUIDED
solves one additional episode at C4 and C6. GUIDED makes zero updates at C6;
its previously saved adapter is loaded for that fresh-task readout. No completed
GUIDED or NO_LORA C7/C8 readout was present in the observed files. Later
UNPARENTED-only readouts are excluded from the matched aggregate.

**This is an exploratory task-outcome difference, not demonstrated retained
thinking improvement or a completed parenting-dependence claim.** There are
only two episodes from one world per checkpoint. Tasks differ across checkpoints,
the arms receive different realized training doses, and the protocol-level
metrics do not measure coherent metacognition, perception or useful revision.
The NO_LORA arm also does not supply the adapter-matched frozen twin required
for a claim isolating later learning from the route initialization.

The operational quantities are still useful: lineage is genuinely persisted,
parent-free testing occurs, and the small matched comparison favors GUIDED on
two episode outcomes. They do not justify relabelling failed reflection admits,
selecting a winner, changing the ongoing branches on outcome, or claiming the
full level-1→level-2 objective is achieved.

`CANONICAL_CONTROLS_1211.json` contains the per-cycle distribution, task hashes,
lineage flags, token counts, and node-local source/reducer hashes. Raw evidence
remains on node3. The full goal remains active and unproven.
