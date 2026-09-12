# Repetition sentinel: gradient-dose normalization correction

**Date:** 2026-09-12  
**Status:** watcher-side accounting correction; no builder code or run changed.

## Ruling

SEQ-101 validly compares separately reset copies with sixteen copies in one
continuous causal context. It does **not** test a sixteen-fold increase in
optimization dose for each fact or habit.

The material contains sixteen copies per original row and records sixteen
times more token presentations. But both arms deliberately keep exactly 80
optimizer updates:

- `short`: batch size 4, gradient accumulation 16;
- `long`: batch size 1, gradient accumulation 4;
- both: 80 original source groups, four epochs, four source groups per update.

`train_adapter_v3.py` uses the model's mean token loss and backpropagates
`loss / grad_accum`. In `short`, four microbatches of four identical copies
of one source row are averaged into one quarter of an update. Four source
groups make the update. Copying the row sixteen times therefore does not make
that source row push sixteen times harder. It primarily averages stochastic
dropout realizations. In `long`, the loss is likewise averaged over the sixteen
repetitions inside one sequence, although later repetitions have a different
causal context and therefore test the continuous-context hypothesis.

The repeated construction also changes relative weighting from a mixed
per-token batch toward approximately equal weight per source group. That is a
real intervention and makes the continued memory null informative, but it is
not sixteen independent update opportunities.

## What the completed result establishes

- Reset versus continuous-context packaging made no observed difference on
  the fixed panel.
- Within-update identical-copy averaging did not rescue conditional color
  generation.
- The global PREDICT-before-ACT habit remained perfect.
- The run does **not** establish that sixteen-fold replay across distinct
  optimizer updates is ineffective.

Near-zero final loss is also not an aggregate memory-loss result: the logged
final scalar came from the final arithmetic microbatch. The exact training-
prompt diagnostic remains the evidence that the original low-dose seed-0
adapter emits the red prior even on seen keys.

## Smallest corrective experiment

Do not rerun the packaging comparison. If the value of repetition itself must
be isolated, hold the unique source corpus fixed and give each memory binding
distinct optimizer encounters separated across the epoch/order schedule, or
explicitly weight its target loss. Register the actual cumulative coefficient
on each source group's loss, not token presentations alone. Keep arithmetic
and memory target contributions separately reported.

For the immediate critical path, the compatible two-habit coexistence sentinel
is already the better test of replay preserving an old behavior while new
behavior is acquired. The genuine conditional-writer test should then use
diverse stable-key renderings and score input-selective flips. The SEQ-101 null
must not be cited as evidence that Rohin's repetition principle failed.

## Authoritative code path

- `organism_v6/fundamental_repetition_corpus.py`: copy construction, batch and
  accumulation settings, fixed 80-update schedules.
- `organism_v6/train_adapter_v3.py`: model mean loss followed by
  `(loss / cfg.grad_accum).backward()`.

