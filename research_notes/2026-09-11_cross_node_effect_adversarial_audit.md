# Cross-node `F_r16k16` effect: adversarial audit

Date: 2026-09-11 PDT / 2026-09-12 UTC  
Scope: read-only audit of SEQ-054 (`a85e9ab6`), preserved local adapter
artifacts, and authoritative node files/queues. I did not modify, stop, start,
or reorder any running or queued work.

## Verdict

**The observed outcome difference is real, but a machine/node effect is not
established.** The comparison in SEQ-054 changes both node **and training
seed**:

- node 1 `memory_dose_conf`: training seed **1** in all three
  `train_meta.json` files;
- node 2 `memory_dose_S1`: training seed **0** in all three files.

The node-2 launch receipt confirms why: `queue/logs/s1_F.sh` does not set
`SEED=1`, so `memory_dose_frames.sh` used its default `SEED=0` even though the
run manifest describes world seed 1. The world/data seed and LoRA training
seed are separate variables. SEQ-054's statements that the training was
identical and that this is a node effect are therefore too strong.

The defensible current statement is:

> Identical ordered supervised examples, evaluated against identical frozen
> traces, produced materially different adapters under two confounded
> `(node, training-seed, run/GPU)` conditions. This exposes unmeasured writer
> run/seed sensitivity; it does not yet identify a node effect.

## What is actually identical

### Effective training data: yes

For every bank, I independently hashed the **ordered fields consumed by
training**—`chat`, `context`, `target`, `weight`, and `mask_context`—using full
SHA-256. The hashes match across nodes:

| bank | full SHA-256 of ordered effective training payload |
|---|---|
| 0 | `b48d253af1b720797ddaebdcb38bc1b51812776777a75a4a6a6389688958fa23` |
| 1 | `a4cef80d8f25a0aeb86c1eb2c862cb78754ea808cb93488a36c754a560e19462` |
| 2 | `78186ae6e8213d8c8610eb58b924515665749870fe0096eafa2d0372dac77cf3` |

The preserved internal ordered `sha`, multiset `items_sha`, item counts,
token counts, supervised-token counts, ordering, and step counts also match.
The bank and distractor JSON files have matching full file hashes on both
nodes. Thus data generation, ordering, padding, and budgeting are not a
plausible explanation.

### Literal corpus files: only banks 1 and 2

"Byte-identical corpora" is literally true for the complete `corpus.json`
files of banks 1 and 2, but not bank 0:

| bank | node 1 file SHA-256 | node 2 file SHA-256 | reading |
|---|---|---|---|
| 0 | `75388327...` | `f2388eaf...` | different metadata/schema; effective payload identical |
| 1 | `860a6780...` | `860a6780...` | complete file identical |
| 2 | `713f3cb5...` | `713f3cb5...` | complete file identical |

The manifests are also not byte-identical: node 2's later manifest contains
additional registered CF/negative cells and a different creation time.
Relevant world seed, banks, owners, and bindings do match. The precise phrase
should therefore be **byte-identical effective training examples**, not
byte-identical run artifacts.

### Frozen evaluation: exceptionally strong match

For each bank I removed only the adapter-ON field from every one of the 1,313
evaluation cue records and hashed the remaining cue metadata plus complete
frozen-base (`OFF`) probabilities. Those full hashes match across nodes for
all three banks. This means the original evaluations used the same cue set
and produced the same rounded frozen-model trace, including controls. A broad
node-dependent evaluation explanation is therefore already unlikely.
Adapter-specific evaluation is not closed until the swap tests finish.

### Model/hardware/core environment: strongly, not exhaustively, matched

Both nodes report:

- Qwen2.5-7B-Instruct snapshot
  `a09a35458c702b33eeacc393d103063234e8bc28`;
- identical content-addressed model-shard/tokenizer links;
- A40 GPUs, VBIOS `94.02.91.00.01`, driver `580.173.02`;
- Python 3.12.3, Linux 6.17.0-35, glibc 2.39;
- torch `2.13.0+cu130`, CUDA 13.0, PEFT 0.20.0, transformers 5.5.3.

The full environments are not identical: the captured freezes differ in
several secondary packages (for example `nvidia-cudnn-frontend` 1.27 vs 1.28,
`fastsafetensors`, `huggingface_hub`, and unrelated agent packages). No
run-bound source/environment/GPU UUID receipt lives in `train_meta.json`.
Current `memory_dose.py` hashes match across nodes, but its mtime is after all
node-1 fits, so that fact alone does not prove the code bytes used then.
Repository history shows `train_hf` itself unchanged since `67eafb8a`, and
the exact matching OFF traces strongly constrain evaluation drift; code drift
is less plausible than the explicit seed mismatch, but is not custody-proven.

## What differs

| variable | node 1 | node 2 | consequence |
|---|---|---|---|
| training seed | **1** | **0** | changes LoRA initialization and dropout stream |
| node / GPU run | node 1; original GPU UUID not receipted | node 2 GPU 4 | inseparable from seed in original comparison |
| adapter bytes, bank 2 | `db4f21e8...` | `05442aee...` | genuine different learned states |
| final loss, bank 2 | 1.2201 | 1.3072 | node-2/seed-0 fit ended worse |
| wall time, bank 2 | 1,587.5 s | 1,261.9 s | performance differs; not itself a learning cause |
| saved `target_modules` order | same seven-module set, different JSON order | same | likely PEFT set-serialization order, not a semantic config change |

The trainer calls `random.seed` and `torch.manual_seed`, but does not enable
PyTorch deterministic algorithms or record deterministic CUDA settings.
Consequently, even a same-seed refit is a test of practical repeatability,
not a guaranteed bitwise reproduction.

## What the already-queued diagnostics can decide

1. **Own-adapter re-evaluation on both nodes (bank 2).** If an adapter's own
   number changes, evaluation/load repeatability is broken. If it repeats,
   the original JSON is stable.
2. **Cross-node adapter swaps (bank 2).** If each adapter carries its original
   effect to the other node, the difference lives in the trained adapter, not
   in evaluation. If the score follows the evaluating node, the evaluator or
   adapter-runtime interaction differs. These tests do **not** distinguish
   node from training seed because the two adapters were trained with
   different seeds.
3. **Node-2 `memory_dose_S1_rep_same` (default training seed 0).** Compared
   with the original node-2 seed-0 fit, this estimates practical same-node,
   same-seed run/GPU repeatability. It may land on a different GPU, so a
   disagreement localizes only to run/GPU nondeterminism, not a particular
   kernel.
4. **Node-2 `memory_dose_S1_rep_seed1` (`SEED=1`).** This is the first
   seed-matched comparison with the original node-1 fits. If it matches node
   1 while the seed-0 refit matches original node 2, the apparent node effect
   is parsimoniously a training-seed effect. If it remains node-2-like, node
   or uncontrolled run/GPU variation remains possible. A mixed result means
   the writer has high run variance.

The two refit directories already contain exact copies of the world banks,
distractor, and manifest; the F corpora will be deterministically rebuilt.
The queued commands correctly set seed 1 only for `rep_seed1`.

## What remains missing for a node claim

The present queue is high-value and should finish unchanged. But a positive
machine attribution would still require a balanced design, minimally:

- node 1 seed 0 and a repeat of node 1 seed 1;
- node 2 seeds 0 and 1 (currently queued) with repeated fits;
- recorded GPU UUID, exact source hash, environment hash, corpus payload
  hash, training seed, and deterministic-mode settings per fit;
- the same adapter evaluated on both nodes, which is already queued.

In other words, a `2 nodes × 2 training seeds × repeats` block is needed if
the paper needs a literal node effect. It may not be worth that GPU cost: if
the current swaps show adapter-following and the refits show large run/seed
spread, the scientifically relevant conclusion is simply that every writer
comparison needs training-seed/run replication and blocking within node.

## Exact claim boundary now

Allowed:

- effective training examples match exactly across the compared runs;
- frozen evaluation inputs and OFF outputs match exactly;
- learned adapters and memory readouts differ greatly across two confounded
  node/seed executions;
- single-fit bank intervals quantify owner/cue sampling only and omit
  training-run uncertainty;
- all cross-node pooled writer claims are provisional.

Not allowed:

- "the node effect is real" or "same bytes in, different memory out by
  machine";
- attributing bank-2 failure to node 2 rather than seed/run/GPU;
- treating three banks under one shared training seed/node condition as
  independent evidence about machine effects;
- treating within-node one-fit CF-vs-F differences as immune to optimizer
  variance. They remain useful descriptive diagnostics, not yet replicated
  estimates of writer-form effects.

## Sources inspected

- `research_loop/COORDINATION.md`, SEQ-054;
- `organism_v6/memory_dose.py` and `gpu/memory_dose_frames.sh`;
- node 1 `/localhome/local-rohing/v6_out/memory_dose_conf/{manifest,banks,corpora,adapters,eval,logs}`;
- node 2 `/localhome/local-rohing/v6_out/memory_dose_S1/{manifest,banks,corpora,adapters,eval,logs}`;
- node 2 refit roots `memory_dose_S1_rep_same` and
  `memory_dose_S1_rep_seed1`;
- both nodes' `v6_out/ENV` receipts and current hardware identities;
- preserved transferred adapters under
  `/Users/rohing/dream-state-artifacts/xnode/` (transfer SHA-256 verified on
  both destinations).
