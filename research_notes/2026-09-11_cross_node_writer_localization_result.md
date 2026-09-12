# Cross-node writer localization result

Date: 2026-09-11 PDT / 2026-09-12 UTC

Status: completed read-only diagnostic over preserved exploratory artifacts.
This note authorizes no new source change, model or tokenizer execution,
training, adapter work, GPU use, parenting, C11 work, claim, release, or
submission.

## Verdict

The large fresh-owner `F_r16k16` difference is carried by the trained adapter
artifacts. Evaluation and adapter loading reproduced exactly, at stored JSON
precision, both within each node and after swapping the adapters across
nodes.

The difference therefore arose during the confounded fitting executions, not
during evaluation. Its cause is still unresolved: the original fits differ in
node, training seed, run/GPU, environment details, and custody strength. This
is not evidence for a node effect, a training-seed effect, or optimizer
nondeterminism.

## Exact symmetric evidence

All six evaluations contain 1,313 unique cues in the same order. Across the
two originals, two own-adapter repeats, and two cross-node swaps:

- ordered cue-ID SHA-256:
  `47409c1a2da621bbbd0b9782e8fbca5ba97c3d29d7ddde2466ce706ceb03506d`;
- full cue core excluding `OFF` and `ON` SHA-256:
  `1b375caa3a247b9c343440e05302ea3158b8eac0b32649f58f5baf90f4e488d1`.

Canonicalization was UTF-8 JSON with sorted keys, compact separators, no
ASCII escaping, and preserved evaluation order.

### Adapter produced on node 1

- safetensors SHA-256:
  `db4f21e87da7283874b5ad0b9a444ceaaa7d5aed927ce813c8f4615a08d2cc6c`;
- config SHA-256:
  `c340793c47ca99aa54fd845f166b5e90eaea04467e8d218e40c050947f639a75`;
- cue-ID-bound `ON` SHA-256:
  `037899e495bf338b683227a4a51945deb0a5b462ed6c278dacff93efb7124839`.

That `ON` hash is exact for the node-1 original, node-1 repeat, and node-2
cross-node evaluation. Each gives:

- frame probability `0.2542427845 -> 0.7348166198`;
- `I_d_frame = 1.1248622065`;
- frame spill `0.3235873154`;
- question probability `0.2475906424 -> 0.6123676123`;
- question `I_d = 2.3609963381`.

### Adapter produced on node 2

- safetensors SHA-256:
  `05442aeeb3367c74cc5a52ac2b6d5f18500c815bb5b8fb3ed6398b0034fa2c9f`;
- config SHA-256:
  `8d38b8fc1b27c15e92120ee267ddb3750c564f0878a9815d29c04a2a25e9adc1`;
- cue-ID-bound `ON` SHA-256:
  `73cfc22fedbc01a1f3eb22de7058a74ccee5a1c3f95e53683342d2f8bdfbb5ff`.

That `ON` hash is exact for the node-2 original, node-2 repeat, and node-1
cross-node evaluation. Each gives:

- frame probability `0.2542427845 -> 0.2544576887`;
- `I_d_frame = 0.0037695844`;
- frame spill `0.1374500847`;
- question probability `0.2475906424 -> 0.2389129967`;
- question `I_d = -0.2451098346`.

Both adapters fail the registered `0.03` frame-spill limit. The strong
adapter is a broad completion habit with an owner-conditioned component; the
null adapter is not usable memory either. The swap result localizes variation
but does not qualify the writer.

## Fitting confounds and consequence

The effective ordered supervised examples match exactly across the compared
runs, but the original node-1 fit used training seed 1 and ended at loss
`1.2201`; the node-2 fit used seed 0 and ended at loss `1.3072`. Node, run/GPU,
environment details, and determinism settings also differ. Balanced
node-by-seed repeats would be needed to attribute the cause.

The embedded `adapter_meta` cannot identify these artifacts: it is identical
across them and omits the training seed. Future receipts must use the
safetensors hash plus full training metadata and execution identity.

Allowed wording:

> Byte-identical effective training examples produced different adapter
> artifacts under confounded fitting executions; each artifact carried its
> exact readout across nodes. The original discrepancy localizes to
> fitting-produced variation.

Forbidden wording includes `node effect`, `training-seed effect`, `optimizer
nondeterminism`, or `the same training execution yielded different results`.
Single-fit bank intervals condition on the fitted artifact and do not cover
this fitting variation.
