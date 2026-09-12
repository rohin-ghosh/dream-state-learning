# Semantic Q0 writer terminal — SEQ-083

**13:47UTC validity addendum:** supplementary audit finds266/832score rows
with summed exponentiated full-candidate scores above one, maximum1.380238.
These cannot currently be interpreted as common-prefix causal probabilities.
All NLL/TV interpretations below are provisional registered outputs, not
validated probability evidence. Original generation observations remain;
native prefix-invariance/mask diagnosis completed without new fitting.

**13:50UTC diagnosis:** actual causal masks exclude future tokens. BF16 eager
full inputs of lengths101/100 disagree strongly at the same shared prefix.
Equal-shape future padding removes this discrepancy exactly (candidate mass
0.997894), while FP32natural inputs agree within7.06e-5logprob (mass0.998979).
This localizes numerical sequence-shape sensitivity, not missing causal
masking. A scoped scorer repair and separately labelled supplementary rescore
are pending; no old record, threshold, or registered label is overwritten.

## Executed evidence

Source `d160e0b26405a7e40eb7de0dca23cfcb94cdbf37`; node3 GPU0;
controller98756; run `astra_semantic_writer_Q0_20260912_attempt1`.
Four fresh256step adapters, two roots by two opposed mappings. All14stages
complete,1712requests/1664candidate forwards/880generations. Resource receipt
records1414.695479seconds (0.393GPU-hours), excluding final external replay
and release verification. Original-source replay reproduces report exactly.
Controller absent and full GPU/XML/CUDA-environment/queue release check passes.
No process killed. Adapters remain on node3; capsule excludes weight binaries.

## Registered results, not a new pass criterion

| Root / mapping | Binding accuracy /64 | Gain over OFF | Mean conditional NLL gain | Valid output |
|---|---:|---:|---:|---:|
| 0 / W+ |37/64|5/64|0.879937|64/64|
| 0 / W- |33/64|1/64|1.001103|64/64|
| 1 / W+ |32/64|1/64|0.664463|64/64|
| 1 / W- |34/64|1/64|0.570680|64/64|

Original label `OPTIMIZATION_INCONCLUSIVE`. Both roots fail binding and spill;
interface and carrier/oracle checks pass. Conditional binary-TV mean shifts
span0.275157..0.659671 across the16cell-by-spill strata. This is substantial
off-target change even in a metric that can miss common-mode shifts.
Mean raw target full-sequence log-probability gains25.92..26.60nats do not
establish selective association: common format/action improvement is a
plausible explanation, and held-form mapping accuracy remains near half.
Two roots are not three independent training seeds; no robust numeric claim.

## Two independent assay limitations

Before ON inspection, OFF-only ceiling analysis showed30/64key-map half-nat
gain gates mathematically impossible (8,8,7,7). For each item gain is bounded
by `-log(q_OFF)`; median preserves the bound. Keep that original conjunction
unchanged but do not interpret its inevitable failure as failed optimization.

Watcher audit additionally exercises common-mode binary-TV blindness and
cancellation in absolute mean legality changes. Consequently these registered
metrics could not certify selective writing even if their label passed.
See `2026-09-12_semantic_w0_writer_d160_prelaunch_audit.md` and the archived
OFF-only independent ceiling review. No retrospective threshold relaxation.

## Interpretation and next action

This run does not qualify a selective writer or freeze the mechanism. It
does demonstrate the real four-fit/reload/interface path. Preserve terminal
data; a no-new-fit exact-training-prompt supplementary evaluation can separate
storage failure from held-form extraction failure. Design that diagnostically
before launching; report separately from registered results. Do not repeat
the same failed learning-rate/preservation sweep. One-event own-material
utility comparison proceeds independently with three paired recipient seeds.
No P1, G3, G5, H1/H2 or clean-lineage claim follows.

## Immutable receipts

- `receipts_20260912/astra_semantic_writer_terminal_20260912.tgz`:
  `422b27e55f794cd14670f049ad09fd31b95887aa615c4d59bc0a03687e83dcf0`.
- `receipts_20260912/astra_semantic_writer_replay_20260912.json`:
  `9e4480d176da221c1f16f9915aa13dcf78014d76bcaa100102ce56d7e2cd57eb`.
- `receipts_20260912/astra_semantic_writer_cleanup_observation_20260912.json`:
  `da92c6a857d8ee732c1d10de5529f943151da18da5a0f8c9946a651b837465f7`.
