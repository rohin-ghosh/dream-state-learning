# Breadth fit result — SEQ260, 2026-09-14

## Result and decision

Both declared 1,632-update fits and their fresh-process readouts completed.
The new trajectory labels produce complete acquisition on the eight TRAIN
worlds, but do not beat the matched label-masked control on the two PROBE
worlds. Both arms fail the predeclared engineering target. This recipe closes;
neither adapter is promoted to the autonomous continuation.

| Readout | FULL_TARGET | NEW_TRAJECTORY_LOSS_OFF |
|---|---:|---:|
| TRAIN OWN_TEXT goals | 32/32 | 17/32 |
| TRAIN OWN_TEXT opposite-goal pairs | 16/16 | 4/16 |
| PROBE OWN_TEXT goals | 5/8 | 6/8 |
| PROBE OWN_TEXT opposite-goal pairs (primary) | 1/4 | 2/4 |
| PROBE world A / world B pairs | 1/2; 0/2 | 2/2; 0/2 |
| PROBE UNAVAILABLE goals | 1/8 | 0/8 |
| PROBE UNAVAILABLE pairs | 0/4 | 0/4 |
| Original taught graph goals | 2/4 | 2/4 |
| Previously fresh graph goals | 4/4 | 3/4 |
| Old memory W0 / W8 | 16/16; 16/16 | 16/16; 16/16 |
| Held audit | 15/16 | 16/16 |

Unchanged37ec's SEQ257 baseline was TRAIN18/32 goals,2/16 pairs; PROBE4/8
goals,0/4 pairs; UNAVAILABLE2/8 goals,0/4 pairs. Improvement relative to that
baseline is not sufficient attribution: the active old-row/rehearsal control
also changes and scores higher on the primary PROBE endpoint. It is not a
no-update control. The FULL result is consistent with task-instance fitting
without adequate identifier transfer, but this small result does not establish
a unique cause, an impossibility of composition, or a population effect.

The failing checks in both arms are PROBE>=3/4 pairs, at least one pair in
each PROBE world, and original taught graph>=3/4. Old-memory, audit and
previously-fresh thresholds pass. No checkpoint is selected retrospectively.
One seed, one exposed DEV lineage and two fixed PROBE worlds; no H1/H2 or
whole-life claim. Coverage and legacy rehearsal changed together from SEQ256.

## Executed method and evidence

Node2 root `/tmp/astra_goal_breadth_train_20260914_attempt1`, exact source
`712d5f2b738f3c33dc905037e57580eee9319441`. Both start from
`37ec37884e4b0b679edd1dba1be1dec3474589e992649f3a33e7e3b1ec78b8c0`.
Frozen Qwen base, rank8 adapters, seed0, batch4, AdamW3e-5,414 rows;
16 presentations per old/new trajectory target. Only new rows222–413 are
label-masked in the control, with full-reference normalization. The complete
method is `2026-09-14_goal_breadth_recipe_design.md`; native bound protocol
SHA `3f2e4307dab0ad7aa2d8cf62accf14203da1b6ac32fd58779c62840929640ed7`.
Parent-free AFTER loads the saved arm-specific adapter in a fresh process.

Saved states:
- FULL `8a94f4ff0eb297c49c0383e7522db17a66eb6baf17a7b4c79f564ec3a99abb42`.
- LOSS_OFF `aa282d0ba3c34b398fd7795f5daaec759f786aef7f023623b641655c42a8908e`.

TRAIN phase elapsed3149.808513/3145.064272seconds; AFTER341.226236/
344.527447seconds and384/374native calls, respectively. These are phase wall
times including setup, not pure GPU-kernel timings. No fit was restarted.
The two fits plus AFTER consume about1.939 allocated A40-hours, excluding
prior collection and outer guard overhead.

Complete terminal archive retrieved and hash-verified on VM `/data`:
`gpu_artifacts_local/astra_goal_breadth_train_terminal_20260914_attempt1/terminal.tar.gz`
SHA `2294116da812f48bfac1beba25b43d64c89a88e477c2976c55c22444bf19e323`.
Extracted root of the same name is under `extracted/`. Raw per-arm
`after/RESULT.json`, individual `*_OWN_TEXT_*.json`, summaries, call captures,
`train/LOSSES.jsonl`, dose/masks, states and adapters are preserved.

Main reduced aggregate counts from stored panel summaries and retention
fields. Independent episode-level reduction in
`2026-09-14_goal_breadth_fit_independent_result.md` agrees with all headline
counts and accounts for all758calls, including the control's earlier
terminations. It verifies recorded state/source joins, not live tensors.
Active label totals133272versus98744confirm the control is not equal-active-
token training; both use the common reference denominator.

## Next experiment implication

Quality-filtered source collection proceeds independently to recover usable
actual trajectories without discarding a whole shard for one failed episode.
It is not a commitment to launch the blocked original scale fit. Before a
further fit, weigh this full TRAIN/weak PROBE split against the rich-content
comparison, preserving equal source selection across supervision arms. Rich
v1 currently stops most episodes for a literal prediction label; inspect
action validity separately before interpreting that as cognitive failure.
