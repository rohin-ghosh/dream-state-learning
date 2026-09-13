# Writer replay/acquisition tradeoff: independent adjudication

**Date:** 2026-09-13 UTC  
**Scope:** analysis only. No source, model, tokenizer, adapter, job, or GPU state
was changed.

## Ruling

The current evidence does not call for another learning-rate, rank, or epoch
sweep. It identifies one missing construction: **old-skill replay must be
additive to the new-memory objective rather than competing with it for a fixed
number of optimizer steps**.

The smallest high-information next test is one fresh three-root
`ADDITIVE_REPLAY` arm on the already bound Level-1 parents and child-record
banks. It preserves the full new-memory dose of the stronger-acquisition arm
under an output-blind balanced schedule, then adds the already captured
own-source replay loss on the same updates. It therefore asks the exact
unresolved feasibility question:

> Can one fixed rank-8, low-heat writer keep all `143/143` initially correct
> old items while still meeting the already frozen new-memory floor in every
> root?

This is three fresh fits, not a new factorial. The completed `REPLAY`,
`EXTRA_MEMORY`, `LOWER`, `HIGH`, and LR0 artifacts are sufficient comparators.
Do not select a different recipe, rate, checkpoint, or replay weight by seed.

## Why this is the next mechanism

The terminal tradeoff is unusually direct:

| endpoint | exact new memory | paraphrase | old items retained | canary |
|---|---:|---:|---:|---:|
| LR0 | `0/30` | `0/30` | `143/143` | `36/36` |
| HIGH, `1e-4` | `20/30` | `16/30` | `98/143` | `36/36` |
| LOWER, `3e-5` | `18/30` | `18/30` | `140/143` | `36/36` |
| REPLAY, fixed steps | `21/30` | `19/30` | **`143/143`** | `36/36` |
| EXTRA_MEMORY, fixed steps | **`27/30`** | **`23/30`** | `135/143` | `36/36` |

`REPLAY` already demonstrates the required retention behavior; it fails only
because seed 1 recalls `6/8` rather than its frozen `7/8` floor. In contrast,
`EXTRA_MEMORY` reaches the frozen exact-memory floors in all roots but loses
old items in seeds 1 and 2. These arms allocated the same updates to different
content. They do not show an intrinsic rank-8 capacity conflict. The earlier
distinct-source FOUR_VIEW result (`15--16/16` memory and `32/32` old action in
all three optimizer lineages) and the one-seed sequential result (`64/64` old,
`32/32` newest with replay) independently show that coexistence is possible
when old and new gradients meet without erasing either objective.

The fixed-coaching result points the same way. Writing admitted child records
improved parent-free record formation from `27/48` to `45/48` in both coached
and neutral arms, but task-specific retention fell to `138/143` and `140/143`.
The generic canary stayed perfect. The immediate problem is not that child
records are inert; it is that new acquisition and preservation are being
asked to share an inadequately constructed write.

## Exact minimal test

For each of the three original perception parents:

1. Start from that exact original parent, never a memory descendant.
2. Keep rank 8, alpha 16, dropout `.05`, LR `3e-5`, response-only loss, eight
   passes, the original fit seed, and the final checkpoint only.
3. Construct a **new-memory stream** with the original `m=14/8/8` admitted
   records plus 24 additional presentations per epoch. Select those
   presentations by a single output-blind cyclic rotation over source row IDs.
   Across eight epochs, every seed-0 row receives either 21 or 22 total
   presentations; every seed-1/2 row receives 32. This repairs the accidental
   seed-0 `8--16` extra-presentation imbalance without inspecting outcomes.
4. On exactly the 24 additional-memory positions in each epoch, pair one of
   the 24 captured old-skill rows, each used exactly once per epoch. Optimize
   `J = mean_token_CE(new_memory) + mean_token_CE(old_replay)` on those paired
   updates, and only `mean_token_CE(new_memory)` on the `m` original positions.
   Do not divide the paired sum by two. This keeps the full new-memory gradient
   instead of diluting it when preservation is added.
5. Keep `8(m+24) = 304/256/256` optimizer updates. Report the extra supervised
   tokens and compute openly; the treatment is not equal-FLOP to its existing
   comparators.
6. Reuse the unchanged exact, paraphrase, 48-item task-retention, and 12-item
   canary readouts after complete source withdrawal.

The pass remains the already frozen noncompensatory screen: exact
source-faithful recall at least `8/14`, `7/8`, and `5/8` in seeds 0, 1, and 2;
zero losses among all `143` LR0-correct task items; and zero canary losses.
Also report robust distinct-target recall and the full output confusion table,
because repeated rows can make the row-level floor look better than the
conditional memory map. Those diagnostics cannot rescue a failed frozen
screen.

A `3/3` pass establishes only a practical additive-replay repair on these
exposed Level-1 roots. A failure is decisive enough to stop tuning this proxy:
do not then try per-seed weights, rank 16, best checkpoints, or another scalar
sweep. Move to the objective-matched PCFL calibration and preserve the failure
as evidence that this replay surface did not compose.

## Consequence for PCFL v2.2

Do **not** transplant the Level-1 rows or delay PCFL DEV behind this proxy.
PCFL has different child rows, clean-base cumulative refits, addressed
EVENT/LINK blocks, eight wrappers, source-diverse batches, and its own native
retention surface. The existing artifacts cannot qualify that writer.

Keep these v2.2 settings unchanged:

- rank 8; no capacity sweep;
- `CAL_LOW = 3e-5`, 200 updates, final checkpoint only;
- all unique child-authored blocks retained;
- truthful, output-blind replay only for unused fixed-work slots;
- eight varied addressed wrappers and the sealed source-diverse schedule;
- candidate-free local acquisition/locality tests plus the itemwise 64-case
  PCFL task-retention gate.

The one necessary decision rule is the conservative `CAL_HIGH` branch already
identified by the readiness audit:

- If LOW passes locality, refusal, generic canary, and PCFL task retention but
  misses only EVENT/LINK acquisition, permit the single predeclared `3e-4`
  HIGH fit.
- If LOW loses task skill, spills to wrong/unseen addresses, emits usable
  false rows, or fails the generic canary, **do not run HIGH**. Higher heat is
  not a repair for unsafe directionality.
- If LOW acquires locally but fails task retention, the next PCFL-specific
  repair is an additive protection stream made only from correct child outputs
  on a presealed, root-disjoint TRAIN protection panel. It must be paired with
  the full memory loss rather than replacing memory slots, and it requires a
  new disposable qualification fit before DEV.

Thus the new result changes PCFL's fallback logic, not its first settings.
Running LOW is itself the highest-information objective-matched writer test.
The three-fit Level-1 additive test may run in parallel as a cheap mechanism
probe, but it must not be used to waive PCFL's own acquisition, locality, or
retention gates.

## What is known versus what still requires fitting

Known from existing artifacts:

- low heat sharply reduces but does not eliminate old-skill interference;
- own-source replay can preserve all `143/143` old items;
- spending those fixed steps on new-memory repetition increases acquisition;
- a generic canary is blind to severe task-specific forgetting;
- rank 8 can hold small old/new banks when batch geometry and replay are
  favorable; and
- fixed process coaching changes behavior while present, while admitted child
  records—not the teacher text—can cause a parent-free behavioral change.

Not inferable without fresh fits:

- whether the summed old/new objective composes in all three actual-child
  roots;
- whether it preserves output diversity rather than learning one repeated
  record;
- whether PCFL's longer EVENT/LINK blocks acquire at `3e-5`;
- whether a PCFL LoRA retains native route competence; and
- whether stored rows are later traversed and used, which only the PCFL
  vertical can answer.

Adapter averaging, choosing REPLAY for some seeds and EXTRA_MEMORY for others,
or selecting a lucky intermediate checkpoint cannot answer any of these
questions and would be outcome-tuned rather than a general writer.

## Evidence read

- `2026-09-13_own_source_replay_repair_terminal_audit.md`
- `2026-09-13_actual_child_lower_lr_memory_repair_terminal_audit.md`
- `2026-09-13_actual_child_real_record_memory_pair_terminal_audit.md`
- `2026-09-13_astra_parented_record_terminal_audit.md`
- `2026-09-12_interleaved_replay_three_seed_terminal_postaudit.md`
- `2026-09-13_sequential_authored_memory_replay_terminal_postaudit.md`
- `2026-09-13_pcfl_vertical_dev_v2_2_writer_repair.md`
- `2026-09-13_pcfl_v22_execution_readiness_delta.md`
