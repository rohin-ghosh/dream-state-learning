# Additive own-source replay: matched memory-dose diagnostic

Prospective September 13, 2026, before new fitting or outcome inspection for
this comparison. Main decision follows SEQ159, not a mandatory adoption of the
laptop's broader proposal. CPU implementation only until the tests below pass.
Simple hygiene applies; formal paper-grade C11 remains deferred.

## Question and narrow change

SEQ159's REPLAY preserves all originally correct retention items but misses
one exact-memory floor; EXTRA_MEMORY reaches the memory floors but introduces
retention losses in two learners. That demonstrates a measured trade-off, not
an intrinsic capacity limit or an all-seed repair. Test whether adding a replay
loss while preserving the full EXTRA_MEMORY memory schedule gives a better
feasibility point. This is not a rank, learning-rate, epoch or objective-weight
sweep, and does not test parenting or repeated fresh-experience learning.

Run two fresh conditions for each original perception root, seeds 0/1/2:
MEMORY_ONLY and ADDITIVE. Both use EXACTLY the old EXTRA_MEMORY material and
epoch ordering from the frozen own-replay comparison. Do not add the proposed
balanced rotation: changing that too would confound the comparison. The older
unequal per-record repetition counts in seed 0 are preserved and reported.
Fresh MEMORY_ONLY controls are necessary to distinguish the added replay term
from changing trainer implementation or relying solely on historical controls.

## Sources, losses and fixed schedule

Each epoch has m=14/8/8 original memory presentations and 24 additional memory
presentations with their original occurrence IDs. Preserve every raw child
target, original context, EOS convention, source binding and loss mask.
Eight epochs yield 304/256/256 optimizer steps in each arm. Use the same
original-root LoRA tensors and a fresh optimizer per arm, not any descendant.

Pair the 24 extra-memory occurrence IDs bijectively, in their original fixed
construction order, with the 24 already admitted own-source observation records
in their frozen row-ID order. The pairing is fixed before fitting and reused
each epoch. No regenerated observations, source filtering, target correction,
paraphrase augmentation, teacher content or held answers enter training.

MEMORY_ONLY: every step minimizes the response-token mean cross-entropy of its
memory item. ADDITIVE: original-memory positions do the same; extra-memory
positions minimize that memory mean loss PLUS the response-token mean loss of
their paired observation item, with coefficient one. Do not divide the sum by
two or concatenate items into a token-weighted mean. Each mean ignores context
labels and includes the declared target/EOS tokens. Perform one optimizer step
after both applicable gradients have been accumulated. Reject nonfinite losses
or gradients rather than silently skipping or saving a successful checkpoint.

All memory presentations, memory order and optimizer-step counts match between
arms. Replay adds 192 observation presentations per learner in ADDITIVE and zero
in MEMORY_ONLY. Extra compute, activations, tokens and random-number consumption
may differ and must be reported. This is an objective-package comparison, not
equal-FLOP evidence or an assertion that realized memory gradients are identical
along diverging parameter trajectories. Do not infer a pure scaling-law effect.

Recipe: frozen Qwen2.5-7B-Instruct base; one trainable rank8 LoRA, alpha16,
dropout0.05, attention and feed-forward projection targets as previously pinned;
LR3e-5, batch one per constituent sequence, eight epochs, same original seed,
fresh optimizer and final checkpoint only. Preserve the original initialization,
dtype, optimizer defaults, serialization and source identity contracts. The old
trainer remains unchanged. A new explicitly versioned trainer may reuse its
encoding, warm-start, collation and serialization helpers; no hidden runtime
monkeypatch or source rewriting is permitted.

## Required implementation tests

The VM lacks Torch/PEFT. Authors run pure CPU fixtures locally; Main separately
runs a tiny Torch/PEFT CPU suite in the verified node environment with
CUDA_VISIBLE_DEVICES empty. This uses tiny synthetic models, not the 7B learner.
Before GPU fitting, require:
- MEMORY_ONLY parity with the frozen trainer on a tiny controlled configuration.
- Paired gradient equals the sum of the two independently computed mean-loss
  gradients, not their average or a token-count-weighted loss; unequal target
  lengths and context masking are included.
- Exact per-occurrence memory/replay order and exposure counts; no split,
  truncation, missing EOS or supervised context/parent bytes.
- Original parent unchanged, base parameters frozen, one intended LoRA adapter,
  optimizer state fresh, and explicit finite/update/save checks.
- Native tokenizer/preparation checks on all three original roots, immutable
  source/capture/history joins and new output directories.

Record tiny-model fixture limits. They validate implementation, not acquisition
or retention at the native scale. Any failing prerequisite prevents fitting
until repaired and retested; retain failures and version fixes.

## Evaluation, budget and interpretation

Use the unchanged exact and paraphrase memory cues, 48 held perception items,
and 12 canaries in fresh source-withdrawn processes for each new arm. No current
lesson, restatement, previous conversation, retrieval store or training record
accompanies memory readout. Total six fits, 1632 optimizer steps and 480 cold
readout calls; zero new source-capture or adaptive parent calls. Provisionally
bound each paired controller to 7200 seconds plus 180 seconds for collection,
with an eight aggregate A40-hour ceiling including preparation. Main supplies
actual allocation after profiling/preparation; the lease requires six-hour
finish margin. No automatic retry, dose increase, seed substitution or adoption.

The original noncompensatory screen remains exact eligible recall >=8/14,7/8,
5/8 respectively and zero lost LR0-correct held/canary items. Preserve per-root
failure masks; gains never offset losses. Paraphrase performance, distinct-target
confusions, raw formats and the same evaluator-only constant-target diagnostic
remain essential limitations; an exact-screen pass alone cannot establish
robust retrieval or general key binding. All seeds/arms and failures are reported.

Compare the fresh arms directly at matched memory exposure. Historical REPLAY,
EXTRA_MEMORY, LOWER, HIGH and LR0 remain explicitly noncontemporaneous references.
Check the fresh MEMORY_ONLY baseline against old EXTRA_MEMORY for unexpected
implementation drift; discrepancies require diagnosis before attributing gains
to replay. Report raw correctness, losses, update norms, per-kind supervised
and context tokens, peak memory and elapsed components where measured.

Even an all-seed success would support only this single-write operating point,
not G3, parenting, H1/H2 or final clean-lineage qualification. It would justify a
separately specified repeated-cycle test, not immediate full-life scale-up. Failure
localizes the limitation of this one additive recipe without authorizing a sweep.

## Ownership

Main owns protocol, native tiny-CPU acceptance, integration, allocation and
interpretation. Beauvoir owns the new additive trainer/tests; Parfit owns the
paired-material and lifecycle adapter/tests. Exact code/input manifests and
commands are pinned after implementation, before fitting. Existing alignment
assay runs continue unchanged; their outputs do not select this writer recipe.
