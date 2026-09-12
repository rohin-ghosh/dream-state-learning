# SEQ-089 — decision-only objective does not recover binding

The prospective root1/W+ objective contrast is terminal. Both fits use the
same original 128 training rows, seed 1, fresh rank-8 initialization, row order,
inputs, targets, optimizer, dtype, learning rate and dropout. Only the label
mask differs: full response versus first choice. Each receives 256 updates.

| Exact-training-row endpoint | OFF | Full response | First choice |
|---|---:|---:|---:|
| Correct |65/128|64/128|64/128|
| Strictly valid |128/128|128/128|128/128|
| Outputs choosing gvn |1/128|128/128|128/128|

The full-response final LoRA tensor hash exactly reproduces the original
root1/W+ adapter. Instrumentation therefore preserves that control's final
weights. Removing suffix gradients alone does not recover key-conditioned
binding in this comparison. A single training seed/map and exact-row panel
do not establish general impossibility, held-out transfer or retention.
No further unchanged dose/rank sweep, mechanism freeze or gate promotion is
selected on this evidence.

## Training diagnostics and costs

Second-epoch decision cross entropy is 0.72820924 (full response) versus
0.78711526 (first choice); full-response cross entropy is 0.09743569 versus
3.58127537; nondecision NLL is 0.00277818 versus 25.99588364. These are online
pre-update, dropout-active measurements, NOT final checkpoint losses.
All 392 adapter/gradient/Adam-state tensors are FP32 at the recorded first
and last snapshots. Update norms are 1.8857633694 and 1.4330553267.

The run performs 384 greedy generations, 384 decision-prefix forwards and
512 training forwards/optimizer steps. Actual generated token IDs: 2,559.
Recorded controller elapsed: 576.103847 seconds; preparation/cold costs
outside this interval are not included. BF16 prefix scores are auxiliary
shape-conditioned diagnostics, not dynamic greedy-generation probabilities.

## Provenance and verification

- Immutable source: `1a6b03f4a156e18efb5e40f470637bb48802721c`.
- Native node3 root: `~/astra_diagnostics/astra_semantic_objective_20260912_attempt1`.
- Controller 120373, GPU0, start 2026-09-12T14:45:10.193UTC; terminal/released.
- Native 43 CPU tests and all 128 actual mask/token checks passed before launch.
- Native replay verifies preparation, actual adapter trees/reload identities,
  report equality, five owned-worker cleanups and full GPU0 release.
- Report SHA256: `4ca5316949252400b6377feca674ba4abd11eac8759a99f9ed427a2b39b7b659`.
- Capsule SHA256: `d7524e0a558a40a4121e2fa46caa1f772e5a3a0e92c4ea1565b57809528e3390`.
- Full/original final tensor SHA256:
  `31f10119bc37dce5abcd7be569914400392429705ada315c3fcf9813a5d23787`.
- First-choice final tensor SHA256:
  `8b84dbef688ed7c30defad3aa15b96acfbe30570d7b8d6805859c0af3500f6bc`.

The capsule, capture script, count-analysis script and JSON are archived in
`receipts_20260912/astra_objective*` and
`receipts_20260912/astra_capture_objective_20260912.py`. The capsule omits
adapter file contents; actual weights remain on node3 and were verified
there. This archive is not a local weight rehash or complete weight backup.
Official model-origin pin remains UNRESOLVED_LOCAL_HASHES_ONLY.
