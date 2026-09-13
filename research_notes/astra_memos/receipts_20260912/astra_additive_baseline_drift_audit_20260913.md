# Additive MEMORY_ONLY versus historical EXTRA_MEMORY: bounded drift audit

September 13, 2026. Read-only audit of Main's completed local mirrors. No
scientific scores were recomputed or inspected, no native/model/tokenizer calls,
fits, imports of training runtimes, network or repository edits. The completed
cohort reduction remains Parfit/Main's work. Only this document was written.

## Finding

**Numerical training equivalence is not established. No confirmed causal
configuration/input/initial-state mismatch was found.** In all three seeds,
the first shared logged training point, step10, already differs. Thus there is
real training-trajectory drift before any readout/scoring stage; this is not
merely a collection-label or downstream evaluation discrepancy.

The preserved evidence rules out several concrete candidates: changed raw
memory examples, labels/EOS masks, row order, nominal configuration, recorded
package versions, original parent selection, initialized LoRA values/dtypes,
and recorded optimizer defaults. It does NOT establish equal runtime RNG state,
attention/backend selection, checkpoint recomputation or native numerical
execution. Do not attribute the historical-to-new baseline difference to
additive replay, or declare it harmless nondeterminism, from this audit.

## Scope and exact file joins

For seed N, compare:

- NEW root `/tmp/astra_additive_replay_native_20260913_attempt1/additive_replay_seedN_20260913_attempt1`, arm `run/MEMORY_ONLY_fit`.
- OLD root `/tmp/astra_own_replay_repair_native_20260913_attempt1/own_replay_repair_seedN_20260913_attempt1`, arm `run/EXTRA_MEMORY_fit`.

Read only plans, training/paired inputs, adapter configuration and training
manifests, fit logs, preserved source code and the existing tiny-CPU parity
receipt. No `scores.json`, generation reduction, recollection or repair API was
used. Main supplies archive/extraction verification; this document does not
repeat whole-archive validation or native provenance checks.

## Direct comparisons: input, masks and dose

For EACH seed, NEW `paired.json.primary` is deep-equal to the ENTIRE OLD
`training_EXTRA_MEMORY.json` object. NEW `training_MEMORY_ONLY.json` has
byte-for-byte equal string values and equal lists/objects for `items`, `rows`,
`encoding`, and all8 `epoch_order` lists. This includes input token IDs, labels,
native rendered prefixes, supervised target/EOS IDs, spans and per-row audits;
it is not just equality of example counts or source names. No tokenizer was
rerun by this sidecar.

Among keys shared with the old encoding object, only `arm`, `schema`,
`material_sha256`, and the arm-bound `encoding_sha256` differ. These wrapper
identities differ by experiment; the underlying encoding array is equal.
`training_items_sha256`, `epoch_order_sha256`, fit seed and recorded token costs
are equal. NEW `paired.primary` retains the exact old object identities too.

|Seed|Rows/epoch|Epochs|Updates, both|Supervised tokens, both|Context tokens, both|Actual padded tokens, both|
|---|---|---|---|---|---|---|
|0|38|8|304|8776|44112|52888|
|1|32|8|256|6368|37184|43552|
|2|32|8|256|7744|37184|44928|

Padding tokens are0 throughout. Target/context dropped counts and split counts
are0. The same pinned trainer performs encode/collate/to_tensors; native NEW
validation explicitly compares IDs and labels to saved audits and checks the
single supervised EOS. OLD re-encodes the same items through that trainer.
One sequence per batch, no packing, mask mode2d; no new pooling or combined
replay forward occurs in MEMORY_ONLY. Max length1024 is not binding here.

One metadata discrepancy is real but not an executed-length difference:
NEW reports `truncation.max_segment_tokens=351` for MEMORY_ONLY, because its
manifest takes max over `primary+replay`. OLD reports182/175/179 for seeds0/1/2.
NEW prepares/validates replay segments but MEMORY_ONLY never forwards them;
the primary encodings and all actual token counts match. This statistic must
not be interpreted as evidence of longer MEMORY_ONLY training sequences.

## Configurations, initialization and defaults

The complete saved `TrainConfig` dictionaries are equal per seed, including
the note string and less-obvious defaults, not just LR and update count:
rank8, alpha16, dropout0.05, LR3e-5, epochs8, batch1, grad_accum1, fit seed0/1/2,
device CUDA, dtype bf16, gradient checkpointing true, shuffle_groups true,
optimizer AdamW, max_len1024, max_steps0, overflow truncate, pack false,
chat_template false, add_eos false, split_overlap_tokens0, SVD init false,
freeze_a false, all28 layers/all7 projection types, isolation auto/tolerance0,
log_every10. Isolation check does not run when pack is false.

Plan fields `environment`, `python`, `python_sha256`, `model`, all14
`model_files`, `chat_template`, `engine`, `params`, and `parent` are exactly
equal per seed. Each seed also uses the same recorded GPU index/UUID in the
old and new experiments. This is receipt equality, not a live device check.

Recorded runtime versions match: torch2.13.0+cu130, transformers5.5.3,
peft0.20.0; environment records additionally match tokenizers0.22.2,
safetensors0.8.0, vLLM0.27.1, huggingface-hub1.30.0 and Python3.12.3.
Version labels and interpreter/model pins do not freeze every runtime kernel
choice or prove byte-identical installed package trees.

`warm_start` differs in exactly ONE key per seed: **final_state**. All other
warm receipt fields match, including source/initialized inventories,
trainable-name order, parent files before/after, phase seed, fresh optimizer
state and cumulative-step accounting. There are392 LoRA tensors per seed;
all392 initialized tensor SHA/shape/dtype entries match; all are float32,
with no source-to-initialized dtype conversions. All392 final inventory entries
differ. Those are comparisons of preserved tensor-hash receipts, not a new
tensor-value/gradient computation. Base loading is bf16; LoRA being float32 is
consistent in both runs and is not evidence that the whole computation was fp32.

The same six-file original parent inventory is unchanged before/after each
write; parent cumulative steps320, then304/256/256 new updates. Base-frozen,
single-adapter and initialized-loaded-state checks are recorded true in both.
No optimizer state was restored or saved, and initial optimizer state entries0.

All recorded AdamW defaults are identical:
`lr=3e-5, betas=[0.9,0.999], eps=1e-8, weight_decay=0.01,
amsgrad=false, maximize=false, capturable=false, differentiable=false,
decoupled_weight_decay=true, foreach=null, fused=null`.
In particular, weight decay is not zero in either implementation. Null
foreach/fused leaves backend resolution to torch; the resolved execution path
is not recorded as a per-step receipt.

Saved `adapter_config.json` differs ONLY in the ordering of `target_modules`.
The seven-member sets are identical, as are actual trainable-name order,
initialized state inventories and manifest LoRA settings. This is a concrete
serialization permutation, not evidence of different target coverage. A
different Python set order alone does not establish different gradient/RNG
behavior. Process hash seeds were not captured for a stronger inference.

## Earliest observable loss divergence

OLD stdout logs only every10steps; no old per-step `steps.jsonl` is present.
NEW has a per-step component journal. OLD values below are printed to4decimals;
NEW values are full recorded scalar losses. Differences at step10 exceed the
old rounding interval in every seed. The logged loss is the forward loss
leading into that update, not a post-update evaluation loss.

|Seed|Step10 OLD|Step10 NEW|Step20 OLD|Step20 NEW|Step30 OLD|Step30 NEW|
|---|---|---|---|---|---|---|
|0|0.5826|0.5906088948249817|0.3410|0.3586486876010895|0.0791|0.0832996815443039|
|1|0.2842|0.2839755415916443|0.1451|0.14849232137203217|0.2002|0.2015628218650818|
|2|0.0757|0.07770057022571564|0.0163|0.01602843962609768|0.1126|0.12802594900131226|

First-epoch mean loss OLD→NEW: seed0 .45994→.46188, seed1
.32638→.32588, seed2 .18537→.18589. NEW first-forward losses are
1.907779335975647/.9917880296707153/1.3508212566375732, but **no corresponding
old first-forward losses exist in these preserved logs**. Do not claim the
first forward matched, or that step10 is the first divergent update. Divergence
occurred by the tenth logged forward, potentially earlier; exact onset is
unidentified. Nonfinite-batch counts are0 in both implementations.

## Concrete source seams and remaining uncertainty

Both runners call the same pinned reflection `load_native_model`: local-only
AutoTokenizer and AutoModelForCausalLM with bf16 and device_map="cuda". It does
not explicitly set attention implementation. Both then use the same frozen
warm-parent initializer, one default adapter, `model.train()`, use_cache false,
gradient_checkpointing_enable() and enable_input_require_grads(), and fresh
AdamW over the same trainable parameter order. Both reset Python and torch
seed immediately before initialization; epoch ordering uses the same local-RNG
helper. These checks reveal no demonstrated seed/config/initial-weight mismatch.

NEW nevertheless is a separate native loop, not a call into the old loop:

- NEW validates/encodes primary and replay inputs before its seed reset; OLD
  encodes its input inside the seeded training function. No evidence of a
  tokenizer RNG draw was found; without RNG snapshots this is not a proof of
  identical pre-forward CUDA state.
- NEW clones every initial trainable tensor to CPU float32, performs additional
  GPU finite/target checks and synchronizing scalar reads, and journals every
  step. OLD does not have this allocation/synchronization pattern.
- OLD retains the model output object in `out`, and backpropagates
  `(loss / cfg.grad_accum)`; NEW obtains `.loss` inside a helper and calls
  `loss.backward()`. With grad_accum1, the objective scaling is the same, but
  the autograd graph/lifetime/allocation pattern is not byte-identical.
- Neither source explicitly pins checkpoint reentrancy kwargs, CUDA RNG
  snapshots, effective attention/SDPA kernels, TF32/matmul flags or deterministic
  kernel selection in the training receipt. bf16+CUDA+checkpointing+dropout0.05
  is the actual regime; final native gradient trajectories are not covered by
  the small fp32 parity result. These are unresolved seams, **not attributed
  causes** or justification to patch an old run.

The existing tiny-CPU receipt really does report exact loss/tensor equality
(28 tensors, every maximum absolute difference0). Its configuration is
rank2,2layers,hidden32,epochs2,fp32 CPU,checkpoint false, explicitly eager
attention, one CPU thread and deterministic algorithms enabled. Native is
rank8,28layers,hidden3584,bf16 CUDA/checkpoint true. The test validates a useful
restricted implementation case, not native equivalence. It was read, not rerun.

## Smallest next diagnostic, only if Main later selects it

Do not rerun the cohort, rescore endpoints or increase write dose to explain
this discrepancy. First use a **single-seed, single-example, zero-update native
parity probe** on the existing first memory occurrence, with no adapter output:

1. Two fresh loads of the same original parent through the two exact frozen
   paths, actual bf16 CUDA/checkpoint/dropout configuration, no corpus changes.
   Record effective base/LoRA/gradient dtypes, train/eval state, dropout module
   settings, resolved attention/checkpoint/optimizer defaults and hashes of
   input IDs, labels, attention mask and position IDs.
2. Hash CPU/CUDA RNG state immediately after warm init and before/after the
   first forward and checkpointed backward; record first loss/logit diagnostic
   and all trainable gradient hashes. Compare naturally seeded states first;
   do not silently force them equal and erase a seed-path difference. Perform
   **no optimizer step**, save no scientific adapter, no readout.
3. If gradients differ despite matching initial/RNG/input state, an old-path
   repeat is the smallest additional check of repeatability. If the very first
   forward/backward matches, this probe cannot explain later divergence;
   a separately selected scratch stepwise parity diagnostic would be needed,
   not a claim that equivalence was recovered. No such work is authorized or
   performed by this sidecar.

This prioritizes the first unresolved native seam and preserves the distinction
between same declared recipe and demonstrated numerical execution parity.

## Evidence pins

OLD training input byte SHA256, seed0/1/2:
- `7c0c9c7fd452e5e311c63143944b8d8d6a60508fd109c8623f45babec9f2735a`
- `b0cd8384f6dd39a64782b1336a20a50a4f0ada3f40584a2b985546449bf2aab5`
- `fed12bf11cdd50dcaebb9974cbb63117eac736fd7855c876435e7c97b1625e93`

NEW training input byte SHA256, seed0/1/2:
- `3f24e732e3e3c23a026401d6fd125314b9868bdb3b24f18a8f51a8c6ea380349`
- `af44e57fc86767d7171cddbf46c595b740039393566f26495b89538d2897d487`
- `21df93d691cd073615310623c6d1b89a906f93c9423707014dcfdb77ff443728`

Training manifests under each compared fit's `adapter/train_manifest.json`:

|Seed|OLD SHA256|NEW SHA256|
|---|---|---|
|0|56977860d3241b190c3dcaacabc40db1d23bd56846b9dcfb7c7e2d33fc2ec448|a6ed70bc1c89e6a34b541694ee3df6ab9b167f693dee00e2f24d25a47ffcd8a7|
|1|6ba65628c5dbab0f63d811e57acf585dd56f6f0c900b00a52cc61344215e8b6b|f8d09d423b409f39f1530053c1d57c18943e3f2f0ba794092bbc9754fba55b2e|
|2|fa449636bd116540991e48f2ce9b4ec8a93a4917865d501ce38cd356cf4cd064|b2dce87dad5dd3dcda12b73ad61663e23cf58440163c4dd7fa46487e7f89cef7|

Training stdout log SHA256:

|Seed|OLD|NEW|
|---|---|---|
|0|ada830a0f3b1e937866a6bafbeb3ba0c0fca3c5b3d626bbc88248d87c5b1006d|60da17f68b3e1125a1302b64d7194ea758ea4b2d58b11584e209c76ea6259f15|
|1|fc8a2a4f3bd24d943b4e3798e217005e88fa45218b0f134a9cdb5f3c1dddfd24|898a24e6753bd90b9648ebd873e922a93cf5ecd4a4202458952957d37a0c6987|
|2|990313901e91b549c696def5b14532cd3104dc342e094249d2c0dfa8df5331ad|e04e17e9141ca6e375962fab328b5c9966b34902db326703e793d02ff08c222c|

Sources inspected without importing:
- NEW runner `/tmp/astra_additive_replay_run_20260913.py`, SHA256
  `ca54e7e1971d89224bb8dec8f3518d0a6a73ec4d1abe6f29278bab335b1618a5`,
  matching preserved plan self pin; fit seam starts line320.
- OLD runner `/tmp/astra_own_replay_repair_run_20260913.py`, SHA256
  `f1e3782378959f0c2552eaf9646a6b8827b876652a535d3248e38fe28371c4fe`,
  matching old plan and new source snapshot; fit seam line344.
- NEW root seed0 `sources/astra_additive_replay_train_20260913.py`, bound SHA256
  `3f2e73ef69b12c8db211e1d3043e4559713e036ffe09571ab8bc4c5199a426a0`:
  backward_components209, native setup264 onward, gradient/step loop341 onward.
- NEW root seed0 `sources/frozen_train_adapter_v3.py`, bound SHA256
  `7bbf165fcb4b8ae3a1180328bcd19f57382c30516daddc95fd61e8a2c749fad7`:
  TrainConfig69, warm init614, seeded setup685, checkpoint770, optimizer791,
  forward/backward812 onward. OLD warm receipt names this same trainer SHA.
- Reflection loader `/tmp/astra_reflection_fit_run_20260913.py:421`, SHA256
  `0f79efa1f4e4da6a9d1ec245c09e665f7c2b7d8bce31f7e01fe01b00f95a72fc`.
- Existing tiny parity receipt
  `/tmp/astra_additive_cpu_archive_mirror_20260913_attempt1/astra_additive_replay_tiny_cpu_20260913_attempt1/receipt.json`,
  SHA256 `ff2346a72f7e4fed9f4cdb51c90bb701c736557add56f0462f2b1e7ef2bc0b7d`;
  sibling `baseline_parity.json`, SHA256
  `5ecd6a6f318f7112bec13ba94d53a9ccafc11d9d904b0b6b8ad0c1d90e67d6e0`.

No tests or training were rerun. No scientific attribution or paper promotion.

EDITSTOP
