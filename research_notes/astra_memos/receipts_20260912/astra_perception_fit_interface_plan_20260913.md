# Perception-only fit/readout interface plan — 2026-09-13 UTC

**PLAN ONLY.** No implementation, training, tokenization with a native tokenizer,
GPU/model execution, network, Git operation, or test run was performed. Only
this document was written. The accepted corpus/tests remain untouched; Main
reported their acceptance at `c0db09a6` (not independently checked with Git).
Boyle owns OFF; Main owns Git, device/lease decisions, and native orchestration.
No prior material, model weights, run outputs, validation receipts, or frozen-run
results were opened. References below are static source interfaces, not evidence
that a fit or readout succeeded.

## Minimal proposal

Use the existing `train_adapter_v3.run_training` on two fresh-base perception
fits, and the existing public probe's rendering/response checks for four
adapter readouts. Keep exactly the accepted **12 train / 12 dev** source rows;
no new examples, mixture, reflection/judgement work, or automatic promotion.

| Fit | Readout anchor | Fixed dev calls |
| --- | --- | ---: |
| train anchor absent | absent | 12 |
| train anchor absent | present | 12 |
| train anchor present | absent | 12 |
| train anchor present | present | 12 |

Two adapters, four cells, 48 readout calls. Boyle's two OFF conditions are
separate, not refit or reimplemented here. Compare by stable corpus `row_id`
and `source.source_id`; do not select checkpoints or rewrite data using dev.
Authored targets remain author-sourced development data, **not teacher-generated
context distillation**. The first question is prompt-dependent elicitation vs
weight-mediated performance under anchor withdrawal, not activated connections.

## Exact existing interfaces and defaults

1. **Accepted data:** `organism_v6/birth_skill_corpus.py`:
   `build_slice(skill, *, split, system_anchor, seed=20260913)` and
   `build_variants(skill, *, split, system_anchor, seed=20260913)`;
   `audit_split_pair(train, dev)`; `score_response(row, raw_response)`.
   Use only `skill='perception'`, train/dev literally, and exact caller-supplied
   anchor text or explicit `None`. Consume `input_messages` and `raw_target`;
   source proof/eligibility metadata must not become prompt or loss text.

2. **Existing birth fit path, narrow reuse only:**
   `/tmp/astra_birth_conditional_run_20260913.py:271` `load_native(model)`
   loads `AutoTokenizer` and `AutoModelForCausalLM` locally with
   `local_files_only=True`, `trust_remote_code=False`, bf16, `device_map='cuda'`;
   requires distinct PAD/EOS and a base without `peft_config`.
   Its `worker` fit branch at line 304 calls `normalize_items`, checks actual
   `encode_item_segments` IDs/labels, then calls
   `run_training(..., TrainConfig(**spec['train_config']), adapter_out,
   corpus_sha=..., corpus_name=...)` without an initial adapter.
   Reuse this **loading/call pattern**, not its controller or material builder.
   Its source defaults are seed 0, LR 1e-4, four epochs, batch 8, fit cap 1800s,
   readout cap 2700s, max 128 updates/arm. It hard-codes a different inventory,
   arms and readout criteria: `prepare_fit`, `source_api`, `verify_fit`, and
   its whole worker cannot be called unchanged for the new 12-row experiment.

3. **Actual reusable trainer:** `organism_v6/train_adapter_v3.py`:
   `normalize_items` (126), `encode_item` (152), `encode_item_segments` (234),
   `pack_by_group` (327), `epoch_order` (351), `collate` (369),
   `lora_config` (479), `run_training` (657).
   `TrainConfig` (69) defaults: rank 32; alpha 0 meaning 2×rank; dropout .05;
   LR 1e-4; epochs 3; max_len 7168; seed 0; overflow `split`; batch_size 1;
   grad_accum 1; pack/shuffle_groups true; optimizer `adamw`; all layers and
   q/k/v/o/gate/up/down projections; chat_template false; add_eos true;
   grad_checkpoint true; device cuda; dtype bf16; max_steps 0.
   `run_training` seeds Python/Torch, attaches fresh PEFT LoRA when
   `init_adapter=None`, runs masked loss, and writes adapter files,
   `train_manifest.json`, `train_meta.json`, and `DONE`.
   AdamW is constructed with LR only: other optimizer defaults belong to the
   installed PyTorch version, not an explicitly frozen optimizer recipe.

4. **Boyle's OFF definitions, read-only reuse:**
   `/tmp/astra_birth_skill_probe_run_20260913.py`:
   `fixed_rows` (150), `render` (169), `native_tokenizer` (180),
   `Native` (284), `validate_response` (313), `capture` (330).
   `fixed_rows` already pairs the 12 dev sources and checks anchor-only change.
   `render` returns rendered text, exact prompt IDs and actual system text;
   it verifies chat-template token equivalence. `validate_response` checks
   actual prompt IDs, raw/decoded output, token count and finish reason.
   Reuse those narrow helpers from a Main-pinned snapshot, without editing
   Boyle's file or mutating its module globals.

   Existing sampling: temperature 0, seed 0, max_tokens 192, top_p 1, top_k -1,
   n=1, presence/frequency penalties 0, repetition penalty 1, ignore_eos false.
   Engine: max_model_len 16384, TP 1, seed 0, memory utilization .85,
   enforce_eager true, prefix caching false, bf16, trust_remote_code false,
   **enable_lora false**. Existing OFF controller/collection/release defaults
   are 900s/180s/20s. Model name is Qwen/Qwen2.5-7B-Instruct, revision
   `a09a35458c702b33eeacc393d103063234e8bc28`.

5. **Adapter routing reference, not a drop-in chat wrapper:**
   `organism_v6/model_backend.py:13` `configured_generation_identity(model_path,
   adapter_path)` hashes the adapter config and one weight file.
   `VLLMBackend` (33) uses `enable_lora=adapter_path is not None`,
   `max_lora_rank=32`, and `LoRARequest('life', 1, adapter_path)`.
   Its `batch` wraps strings into a single user role and returns only text;
   do not call it for this experiment's explicit system-role comparison.

## The small adaptation needed

**Training items, no trainer patch:** render each accepted `input_messages`
with the same native chat template and generation prefix as readout. Produce
one v3 item per source, with the existing `spans` shape:

```text
spans = [[rendered_generation_prompt, False, "context"],
         [raw_target, True, "perception_record"]]
group = row_id; order = fixed row index; view = "perception"
meta = source/row/target hashes, not model-visible text
```

Call `normalize_items` and `encode_item_segments` with **chat_template=False**:
the prompt is already rendered. The trainer's `chat_template=True` path folds
all context into a single USER message and would destroy the anchor-as-SYSTEM
intervention. Do not use the v1 bare-text trainer or its unrelated child-record
wrapper, and do not double-apply the chat template.

Before Main's fit, check actual native IDs and labels for all 24 arm-specific
train inputs: one segment/row, no skipped/truncated tokens, full prompt masked,
identical target token IDs/exposure across arms, no padding loss. Match the
assistant-prefix and target/end-token boundary to the native full assistant
serialization, including EOS and any terminal newline convention; do not
assume separate span encodings concatenate to the full chat encoding. If the
existing add_eos recipe differs, surface it for Main instead of silently
changing the target. Keep the 12 dev rows out of the trainer entirely.

**Anchor text:** accept it as an explicit parameter/file, preserve exact bytes,
and pin its hash. To reuse Boyle's OFF comparison, use the identical anchor
bytes Boyle pinned; a different anchor needs a separately matched OFF readout.
The current OFF helper has a hard-coded `ANCHOR`, so require equality before
using `fixed_rows`, or build the same dev variants directly with the accepted
corpus API. Do not monkey-patch that global. “Absent” means absent *experimental
anchor*: the Qwen template may inject a generic system message. Log the actual
rendered system segment in both training and readout, as Boyle already does.

**Four readouts:** a tiny adapter-aware backend can retain Boyle's renderer,
SamplingParams and response structure, changing only LoRA enablement and
supplying the exact fitted adapter via `LoRARequest`. Use the existing rank
ceiling 32 for rank-8 adapters. Keep one fresh process/engine per cell, matching
Boyle's condition isolation, with no online updates or prior-cell transcript.
Save raw responses before checking/scoring them; pass only input messages to
generation and join targets afterward for `score_response`.

Do not call Boyle's `capture` unchanged: its identity hard-codes `adapter=None`
and its binding/verification explicitly forbids fitting/adapters. Use a short
local capture loop with honest fit-arm/readout-anchor/adapter hashes while
reusing `render` and `validate_response`. Preserve Boyle's OFF-only contract.

## Proposed bounded recipe and exposure budget — Main must select

Use `TrainConfig(rank=8, alpha=16, dropout=.05, lr=1e-4, epochs=4,
max_len=1024, seed=0, overflow='truncate', batch_size=4, grad_accum=1,
pack=False, shuffle_groups=True, chat_template=False, add_eos=True,
optimizer='adamw', grad_checkpoint=True, device='cuda', dtype='bf16',
max_steps=0, model=EXPLICIT_LOCAL_BASE)`; leave all seven projection modules,
all layers, SVD off and freeze_a off. Each source gets its own group so the
existing group shuffle actually shuffles examples. Same groups/order/seeds
in both arms; fresh base and optimizer per fit, no warm start or adapter merge.

This inherits the prior rank-8/LR/four-epoch pattern but deliberately uses
batch 4 (12 divides evenly), no packing, and a 1024-token ceiling rather than
blindly transplanting its inventory/packing limits. The native token check
must prove the ceiling loses nothing; no truncation is permitted in fact.
Three updates/epoch × four epochs = **12 updates and 48 example presentations
per adapter**; two fits = 24 updates / 96 presentations. Equal target exposure
does not imply equal prompt tokens or equal compute when an anchor is added.

Readout: 4×12 = **48 calls**, maximum **9216 generated tokens** at the existing
192-token cap; two additional OFF conditions belong to Boyle's budget.
No native timing or memory estimate was measured here. A conservative proposed
outer ceiling is two 600s fit workers plus four 300s readout workers, 20s release
reserve per owned process, and 180s collection: **2700s / 45 minutes**, not an
expected duration or authorization. Main may choose tighter caps from current
hardware/load evidence; stop/preserve partials rather than add epochs or retry
automatically. Use Main's existing device/lease/process supervisor, not a new
queue, nested release protocol, or generic guard framework.

## Risks and minimal pre-native checks

- **OFF engine confound:** enabling LoRA changes the engine path from Boyle's
  current OFF settings. The four SFT cells remain mutually matched, but a
  learned-vs-OFF contrast needs Boyle/Main to approve an OFF run on the same
  LoRA-enabled engine with `lora_request=None`, or explicitly report this
  mismatch. Do not silently call the existing OFF run fully matched.
- **Trainer success is not scientific success:** the fresh-base trainer can
  skip nonfinite batches and still write DONE. Require empty=false, 12 encoded
  items, zero drops/skips/nonfinite batches, four epochs, 12 optimizer updates,
  finite losses, expected supervised token counts and actual adapter files.
  Use its existing manifest; no new independent qualification protocol.
- **Clean isolation:** `get_peft_model` wraps/mutates the supplied model. Two
  fits must not reuse an already wrapped object. Record frozen-base identity,
  only-LoRA trainability, fresh optimizer and distinct output paths. The v3
  CLI defaults do not force local-only loading for cold starts; prefer the
  explicit local loader pattern rather than blindly calling its CLI.
- **Tiny diagnostic:** 12 dev cases share the record grammar and six semantic
  cases with train. Exact public-record correctness measures this limited
  behavior; not general perception, L2 qualification, or long-term persistence.
  Report per-row paired outcomes and invalid/truncated counts, not only a mean.
- **Tests needed later, not run now:** fake-tokenizer anchor/prefix/label parity;
  stable 12/12 inventory and four-cell matrix; zero dev loss; batch/order/update
  accounting; adapter routing/identity and failure-preserved raw outputs.
  Existing references: `tests/test_train_adapter_v3.py` normalize/encode/collate/
  epoch-order tests, and Boyle's `test_pairing_dev12_anchor_only_and_no_metadata_in_input`,
  `test_fresh_backend_each_condition_and_messages_only`, and
  `test_failure_preserves_raw_and_never_closes` in his sidecar test file.

## Smallest future file surface

1. New `/tmp/astra_perception_fit_run_20260913.py`: only preparation of masked
   items, `fit_one(train_anchor)`, `readout_cell(train_anchor, readout_anchor)`,
   and a small four-cell summary. It calls the existing trainer and narrow
   pinned OFF helpers; Main invokes workers under existing orchestration.
2. New `/tmp/test_astra_perception_fit_run_20260913.py`: CPU interface fixtures
   for those adaptations. No edits to corpus/tests, trainer, model_backend,
   previous birth runner, or Boyle's OFF runner. Any matched-OFF change remains
   Boyle's separate decision. Repo promotion can be Main's later choice, not
   prerequisite scaffolding for this experiment.

Static source hashes at inspection (Boyle may still revise his file; Main must
select the final reviewed snapshot before reuse):

- `train_adapter_v3.py`: `7bbf165fcb4b8ae3a1180328bcd19f57382c30516daddc95fd61e8a2c749fad7`
- `model_backend.py`: `93feee1cb30720b565aac8f570d368cad8e137789b39f228fbd8ed264123a3f5`
- Boyle OFF runner: `67fdfba4509a6287a6937702c3cbaa3547f3e9bd2e01c710e1166a75eb6c3345`
- Prior birth runner, source reference only: `072a1333c0411a73ae0fc46c6e70de9afe0bce9b49c74e01bdaae16174195daa`

**Decision requested from Main:** the proposed bounded recipe/budget, exact
anchor bytes, and the matched-OFF engine treatment. Nothing is implemented or
launched by this plan.
