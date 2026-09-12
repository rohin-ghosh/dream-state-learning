# Watcher audit: terminal three-seed mini-Sudoku replication

Independent review of `origin/main` commit `9f658611`, applying the
result-blind plan committed earlier at `9fa9798d`. I extracted both committed
terminal capsules to a new temporary directory and reran
`mini_sudoku_behavior_analysis` and `mini_sudoku_behavior_run_audit` on all
three raw run roots. No remote state or builder code was used or changed.

## Eligibility verdict

All three seed pairs are eligible. The reruns return
`OFFLINE_BINDINGS_VALIDATED`, zero prompt mismatches, complete useful and
corrupt fits, and valid OFF/ON custody. All 12 cells have 16 measured first
ACTs and exactly one ACT per episode (192 episode-cells total), so there is no
missing/invalid or best-of-many substitution.

Across seeds, useful/corrupt corpus SHA256s, fixed IDs/order, base-model byte
pins, probe-source hash maps, generation seed/salt, temperature, one-tick
budget, 400/100 wake/Scratchpad caps, 38,400-token condition cap, 16-episode
cap, and 4,096 model length agree. Every fit records rank 8, effective alpha
16, dropout .05, AdamW 1e-4, three epochs, batch 1, the requested seed, 96
finite steps, 1,216 target tokens per epoch, 77,124 input-token passes, and no
dropped/split material. Seeds 1/2 have `BOTH_ARMS_COMPLETED` receipts and fixed
useful-first same-device dispatch on GPU 1/3 respectively; seed 0 retains its
separate-device layout.

The four new adapter inventories match the committed remote rehash receipt.
The capsules omit weight tensors, so this is recorded-byte binding, not local
weight possession or loaded-runtime authentication. The seed-0 preparer and
seed-enabled preparer have different archived path/source hashes, as expected
from the seed extension; seeds 1/2 match each other, while the generated corpus
bytes and evaluation/probe code hashes match seed 0. Do not describe all
literal source maps as identical.

## Frozen endpoints recomputed

All values below are solve counts out of 16. `D=(U_ON-U_OFF)-(C_ON-C_OFF)`.

| seed | U_OFF | U_ON | C_OFF | C_ON | G_U | G_C | O | B | D |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 0 | 2 | 0 | 0 | 2 | 0 | 2 | 0 | 2 |
| 1 | 0 | 3 | 0 | 1 | 3 | 1 | 2 | 0 | 2 |
| 2 | 0 | 5 | 0 | 0 | 5 | 0 | 5 | 0 | 5 |

Across the three learner seeds: `G_U` has mean 10/3, median 3, range 2--5;
`G_C` mean 1/3, median 0, range 0--1; `O` and `D` each have mean 3, median 2,
range 2--5; `B` is identically zero. Thus the primary `D` rate is mean 3/16,
median 2/16, range 2/16--5/16. The zero-filled native-score `D` values are
.297265625, .35703125 and .407421875 (mean .35390625), diagnostic only.

Both new seeds meet every frozen condition: seed 1 has `(G_U,O,D)=(3,2,2)`
and seed 2 `(5,5,5)`, all at least one. The predeclared verdict is therefore
**repeatable directional material transfer at this 16-board resolution**.
The corrupt seed-1 solve prevents a perfect-selectivity reading.

## Solution-overlap sensitivity

The prespecified overlap IDs are 1900054, 1900055, 1900059 and 1900065.
OFF solves are zero in both subsets. Splitting ON solves into the four overlap
boards versus the 12 non-overlap boards gives:

| seed | useful ON overlap / non-overlap | corrupt ON overlap / non-overlap | D overlap | D non-overlap |
|---:|---:|---:|---:|---:|
| 0 | 0 / 2 | 0 / 0 | 0 | 2 |
| 1 | 1 / 2 | 0 / 1 | 1 | 1 |
| 2 | 1 / 4 | 0 / 0 | 1 | 4 |

The full-panel decision is unchanged. As a sensitivity diagnostic, removing
overlap boards leaves `D=(2,1,4)`, positive in every seed; it is not a new
confirmatory endpoint. Independent counting finds 48 distinct puzzles, each
with exactly one valid completion, but only 42 distinct solution grids (30
among 32 training puzzles, 16 among canaries, with four grids shared across
splits). Therefore `unique_reference_completions=48` in the run-audit summary
must mean “48 puzzles individually verified to have a unique completion,” not
48 mutually distinct solution grids.

## Exact claim boundary and decision

Supported: for this fixed Qwen/LoRA recipe, these three optimizer seeds, and
this known 16-puzzle development panel, useful external-oracle associations
produce a small positive first-ACT exact-solve contrast over both OFF and
wrong-board material, directionally repeating in both new same-device seeds.

Not supported: population significance, reliability outside seeds 0--2,
untouched-solution generalization, robust Sudoku competence, retention,
general reasoning transfer, selective memory, a mechanism, parenting, clean
lineage, authenticated official origin, or loaded-runtime identity. Seed 0's
placement differs; seeds 1/2 retain useful-first order and shared-node/time
effects. The frozen next decision is only to preregister one bounded
source-linked child-material comparison, not launch a full parenting campaign
or infer H1/H2.
