# SEQ-162 first-gradient divergence: independent bounded audit

**Date:** 2026-09-13  
**Disposition:** useful pre-optimizer locator, not a path attribution and not a
native reproducibility qualification  
**Scope:** repository evidence only. No model, tokenizer, scorer, trainer,
adapter, GPU, or runtime was executed or modified.

## Bottom line

The only locally preserved report of SEQ-162 says that one OLD-path load and
one NEW-path load produced the exact same displayed first loss,
`1.907779335975647`, but different gradient-data hashes for `256/392`
trainable tensors before either optimizer stepped. That moves the known seam
from “by step 10” to “during the first backward” for this particular seed-0
diagnostic. It does **not** show that the NEW path caused the historical
`EXTRA_MEMORY` versus fresh `MEMORY_ONLY` drift.

There is only one sample from each path. Therefore the observation is equally
compatible with:

1. native backward non-repeatability within OLD, NEW, or both paths;
2. an unrecorded effective-mode/backend difference between the two processes;
3. a real path-dependent backward difference; or
4. a gradient-hash comparison whose identity or byte semantics are weaker than
   the phrase “gradient data hashes” suggests.

The equal scalar loss does not settle this. Two full logit tensors can reduce
to the same rounded scalar, and checkpoint recomputation or a nondeterministic
backward can produce different derivatives while the original forward loss is
identical.

No SEQ-162 source, plan, receipt, per-parameter table, or native artifact is
present in the current worktree. The `256/392` count and “six RNG boundaries”
are relayed text in `research_loop/COORDINATION.md`, not independently
rehashable evidence here. The frozen production sources and the earlier drift
receipt establish strong *intended* parity, but they cannot retroactively prove
the exact state of the SEQ-162 processes.

Writer-objective tuning should remain paused until the four-process,
ten-update audit below establishes within-path repeatability first.

## What was and was not held fixed

The relevant frozen sources are:

- OLD trainer `organism_v6/train_adapter_v3.py`, SHA256
  `7bbf165fcb4b8ae3a1180328bcd19f57382c30516daddc95fd61e8a2c749fad7`;
- NEW trainer
  `research_notes/astra_memos/receipts_20260912/astra_additive_replay_train_20260913.py`,
  SHA256
  `3f2e73ef69b12c8db211e1d3043e4559713e036ffe09571ab8bc4c5199a426a0`;
- prior native-drift source audit
  `research_notes/astra_memos/receipts_20260912/astra_additive_baseline_drift_audit_20260913.md`,
  SHA256
  `88f49a658d2997b53231ff70f66e968c98e8395843fe63754fab26dac475dab4`.

| Property | What repository evidence establishes | SEQ-162 status |
|---|---|---|
| Input, labels, masks, schedule | The prior drift audit found the historical and fresh encoded memory objects, all eight epoch orders, and token counts equal. Coordination says SEQ-162's first inputs/masks matched. | Strongly intended; the SEQ-162 bytes and schedule receipt are not local. |
| Initial trainable tensors | The prior audit compared all 392 historical/fresh LoRA receipt entries by name, order, shape, dtype, and initialized data hash. | Strongly intended; the SEQ-162 inventory is not local. Equality of the frozen base's in-process tensors and buffers was not reported. |
| LoRA topology, names, order | Both frozen paths call the same warm initializer and require exactly one active adapter with only LoRA A/B trainable. Historical receipts had the same 392 ordered trainable names. The saved target-module lists differed only in serialization order; their seven-member sets and realized parameter order matched. | No demonstrated topology cause. The exact SEQ-162 named-module and named-parameter inventories remain unavailable. |
| Model mode | Both sources set `use_cache=False` and call `model.train()` after moving the wrapped model to CUDA. | Intended equal. SEQ-162 did not leave a locally inspectable full module-level `training` inventory. |
| Dropout | The recipe uses LoRA dropout `0.05`; recursive `model.train()` should enable it in both paths. | Intended equal, not actually proved for every module in SEQ-162. Dropout probabilities, module modes, and recomputation masks were not preserved here. |
| Forward implementation | OLD executes `out=model(**t); loss=out.loss; (loss / grad_accum).backward()`. NEW executes `loss=model(**tensors).loss; loss.backward()` inside `backward_components`. Here `grad_accum=1`, so the objective is mathematically the same. NEW also clones every initial trainable tensor to CPU and performs extra validation, finite checks, synchronization, and journaling. | **Not byte-identical.** The model call is the same, but Python object lifetime, the top autograd graph, allocation, and synchronization paths differ. Those are seams, not yet causes. |
| Autocast and dtype | The common loader requests a bf16 base. Historical receipts report float32 initialized LoRA trainables in both paths. Neither frozen source contains an explicit autocast context. | No observed dtype mismatch. SEQ-162 did not preserve a locally inspectable effective autocast/default-dtype/backend receipt, so equality is intended rather than independently proved. |
| Gradient checkpointing | Both paths call `gradient_checkpointing_enable()` with no arguments, then `enable_input_require_grads()`. They used the same recorded package versions. | Intended equal, but the effective checkpoint callable, reentrant setting, RNG-preservation setting, and per-module checkpoint state were not recorded locally. This matters because the backward recomputes the forward. |
| Attention and CUDA backend | Neither source explicitly selects eager/SDPA/flash attention, deterministic algorithms, TF32/matmul policy, or CUDA workspace policy. | Not fixed by source. Prior receipts bind versions and GPU UUID, but not all effective runtime switches or dispatched kernels. |
| Optimizer | Both create fresh default `torch.optim.AdamW` over trainables in model order with the same recorded defaults. | Irrelevant to the first SEQ-162 mismatch because it was observed before `optimizer.step()`. Resolved `foreach`/`fused` execution matters only after this boundary. |
| RNG | Both call `random.seed(cfg.seed)` and `torch.manual_seed(cfg.seed)` immediately before warm initialization. Epoch ordering itself uses the same explicit schedule. Coordination says six SEQ-162 RNG boundaries matched. | Potentially strong, but boundary definitions, RNG domains, hashes, and timing relative to checkpoint recomputation are absent. It cannot yet exclude a dropout/checkpoint RNG seam. |
| Gradient-hash semantics | No SEQ-162 hasher or per-name gradient table is synced. | **Unknown.** `256/392` is not independently auditable and says nothing about magnitude without norms/differences. |

Thus the comparison did not demonstrably hold the *entire effective numerical
execution* fixed. It did hold, or has strong receipt evidence for, the logical
example, declared recipe, LoRA initialization, and intended model state. Most
importantly, the two frozen forward/backward wrappers are genuinely different,
even though their first MEMORY_ONLY objective is mathematically equivalent.

## What `256/392` means—and does not mean

A useful tensor-data hash must be computed over the logical tensor, not a
serialization container:

`SHA256(dtype || canonical shape || detach.cpu.contiguous raw bytes)`

and it must be joined by the full parameter name. Missing gradients must be a
distinct state, not the empty-tensor hash. A whole inventory hash should then
join sorted `(name, tensor_hash)` records. Hashing `torch.save(tensor)` files,
CUDA storage, object IDs, or unnamed list positions can introduce irrelevant
metadata or order ambiguity.

Until the SEQ-162 hasher is present, the reported count cannot distinguish one
ULP from a catastrophic difference. For every parameter the audit also needs:

- finite and present/absent state;
- element count and zero count;
- float64 L2 norm;
- OLD-vs-NEW maximum absolute and relative-L2 difference; and
- cosine similarity where both norms are nonzero.

The names of the 256 differing tensors matter. Concentration by LoRA A versus
B, attention versus MLP, or early versus late layer would be far more
diagnostic than the count alone.

## Ranked causal hypotheses

The rankings below concern causes of the observed first-backward discrepancy,
assuming the relayed hashes are canonical and name-aligned.

1. **Native within-path backward non-repeatability or numerical sensitivity.**
   This is the first hypothesis to test, not yet the established cause. The
   actual regime is bf16 CUDA, dropout `0.05`, and gradient checkpointing. A
   one-of-each run provides no estimate of OLD-OLD or NEW-NEW repeatability.
2. **Checkpoint/dropout recomputation or another effective runtime-state seam.**
   The original forward can have the same scalar loss while the checkpointed
   backward recomputes with a different state. The relayed six RNG matches
   lower this probability only if they include all Python, CPU, and every CUDA
   generator immediately before and after both the original forward and the
   checkpointed backward. Their definitions are unavailable.
3. **A real wrapper-path effect.** OLD and NEW do not execute an identical
   Python/autograd path. NEW's pre-forward CPU clones and additional
   checks/synchronizations, and OLD's retained output plus division by one,
   could change allocation, scheduling, or the top graph. This remains
   plausible only after both paths reproduce themselves.
4. **An unrecorded attention/kernel/backend mode difference.** Effective SDPA
   selection, TF32/matmul flags, deterministic status, CUDA workspace, streams,
   or checkpoint implementation were not fully sealed. Same package/GPU is
   necessary but not sufficient evidence of equal dispatch.
5. **Gradient-hash identity/byte-semantics artifact.** This must be cleared
   before interpreting `256/392`; the missing source makes it an evidence risk,
   not a positive allegation.
6. **Autocast or tensor-dtype mismatch.** Low probability: both source paths
   have no explicit autocast, use the same bf16 model loader, and historical
   receipts agree on float32 LoRA tensors. Effective state still needs logging.
7. **LoRA topology, parameter order, or initial-weight mismatch.** Very low on
   current evidence: the prior audit matched all 392 realized names/order and
   initialization receipts. A serialized target-module list permutation is not
   a demonstrated computational difference.
8. **Input/order mismatch.** Very low given the deep equality and schedule
   receipts, but the ten-update instrument should bind the actual tensors again.
9. **AdamW behavior, collection, or scoring.** Excluded for this first seam.
   No optimizer step, generation, or scorer had occurred.

The first item is deliberately “non-repeatability *or* sensitivity,” not
“CUDA is nondeterministic.” No within-path native repeat exists, so current
evidence supports no attribution to dtype, dropout, checkpointing, or kernels.

## Smallest decisive reproduction audit before writer tuning

Use seed 0 first because it exactly reproduces the SEQ-162 first example and
loss. Seed 2 is more dramatic at the endpoint, but selecting it would answer a
different question. Run exactly four isolated scratch processes, sequentially
on the same pinned GPU:

- `OLD-1` and `OLD-2`: the frozen historical `EXTRA_MEMORY` path;
- `NEW-1` and `NEW-2`: the frozen fresh `MEMORY_ONLY` path;
- same original parent, same pinned base/tokenizer files, same first ten frozen
  memory occurrences, same seed, and no replay forwards; and
- ten optimizer updates, no readout/generation, no scientific adapter save,
  no corpus change, and no writer knob change.

Do **not** enable new deterministic settings for this first audit. The first
question is whether each historical path repeats in its natural envelope.
Instrumentation must be identical around both paths and must not consume RNG.

### One-time process receipt

Record and hash:

1. source, parent, base/tokenizer-file, input, and ten-occurrence schedule
   inventories;
2. host/GPU UUID, driver, CUDA/cuDNN, torch/transformers/PEFT versions,
   `PYTHONHASHSEED`, CUDA workspace environment, current stream, default dtype,
   autocast enabled state/dtype, TF32/matmul policy, deterministic flags, and
   all SDPA/flash/memory-efficient/eager settings;
3. full ordered `named_modules()` type plus `training` flag, every dropout
   module and probability, active adapter, `use_cache`, attention
   implementation, and gradient-checkpointing state/callable/arguments
   including reentrancy and RNG preservation;
4. full ordered `named_parameters()` metadata and optimizer parameter-to-name
   mapping; and
5. all 392 initial trainable tensor hashes plus shape/dtype/device and the
   frozen-model file inventory. Record mutable buffer inventories separately.

### Per-update receipt, updates 1–10

At each boundary record hashes of Python, torch CPU, and every CUDA RNG state;
these boundaries must include immediately before forward, after forward,
immediately before backward, after backward, and after optimizer step. Also
record:

- occurrence ID and canonical logical hashes of `input_ids`, `labels`,
  `attention_mask`, and any supplied `position_ids`;
- raw scalar loss bytes and a fixed compact forward diagnostic: target-token
  logits plus a preregistered small set of decoy logits at supervised
  positions. A full vocabulary-logit copy is unnecessary and would materially
  perturb memory pressure;
- before backward, proof that every trainable `.grad` is `None`;
- after backward and before the step, the name-bound canonical gradient hash
  and the quantitative statistics above for all 392 tensors;
- after the step, all 392 trainable tensor hashes and AdamW step, `exp_avg`, and
  `exp_avg_sq` hashes by parameter name; and
- the resolved optimizer settings. If the runtime cannot reveal whether null
  `foreach`/`fused` dispatched a fused/foreach kernel without an intrusive
  profiler, record that as unresolved rather than guessing.

Write each record before continuing and end with a hash-bound manifest. Any
instrument-generated synchronization must be identical across all four runs.

### Predeclared comparison order

1. Compare `OLD-1` with `OLD-2`, and `NEW-1` with `NEW-2`, boundary by boundary.
   Do not inspect OLD-vs-NEW causally until both within-path comparisons pass.
2. If either within-path pair first differs before forward, the lifecycle,
   model, input, or RNG envelope is not controlled.
3. If original-forward diagnostics agree but a within-path pair first differs
   at gradients, native checkpointed backward is not reproducible under the
   natural recipe. Seal a separate deterministic runtime before any writer
   tuning: explicit deterministic algorithms and CUDA workspace, one explicit
   attention backend, TF32 off, explicit checkpoint reentrancy/RNG preservation,
   and explicit AdamW `foreach`/`fused` choices. Then repeat the same x2-per-path
   ten-update audit under that newly labeled envelope.
4. If each path is internally exact but OLD and NEW first differ before the
   backward, the first state/logit boundary identifies an effective path seam.
   If they first differ only in gradients, the backward wrapper/checkpoint
   interaction is localized; then bisect the few wrapper differences while
   holding the now-qualified envelope fixed.
5. If all four runs agree through update 10, SEQ-162 did not reproduce and
   cannot explain the historical drift. Only then extend the stepwise audit
   beyond ten updates; do not tune the writer in response to an unreplicated
   locator.

This is the minimum because one OLD and one NEW run cannot distinguish
path-specific causation from within-path variance, and a zero-update probe
cannot test the optimizer/checkpoint trajectory at the first point where the
historical logs are known to differ. Four processes times ten updates produces
the needed within-path controls without rerunning the six-cell cohort or any
generation panel.

## Safe interpretation now

SEQ-162 is evidence that the historical/fresh mismatch is plausibly a native
training-path problem rather than a scorer or endpoint-collection problem. It
is not evidence that additive replay is harmful or helpful, not proof that NEW
caused the drift, and not proof of CUDA, bf16, checkpoint, or dropout
nondeterminism. The immediate scientific action is reproduction and execution
qualification, not more writer tuning.

No runtime work was performed by this audit.
