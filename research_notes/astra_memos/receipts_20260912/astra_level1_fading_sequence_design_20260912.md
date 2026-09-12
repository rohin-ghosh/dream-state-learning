# Level-1 reduced-plasticity continuation and repetition: bounded design

Date: 2026-09-12. Design only; Main decides after the ongoing seed replications.
No Git, network, GPU, tokenizer/model inference, training, or model-agent calls
were used for this memo. The only computation beyond source inspection was the
pure-Python corpus generator and deterministic disjoint-pair selection. No
experiment, worker-owned file, source module, or notebook was changed.

## 1. Directive and answer

Source: `research_loop/COORDINATION.md:5314` (Rohin message 17, relayed
2026-09-12T17:54Z), plus the immediately following Builder acknowledgment at
17:57 UTC; raw message in `research_notes/THESIS_RAW_ROHIN_2026-09-11.md:233`.
The raw heading says approximately 17:55 UTC; the relay timestamp is 17:54Z.
Operative direction: continue level 1; one habit is fine; leave compilation
aside; investigate long sequences/repetition and lower plasticity while updates
continue. The Builder explicitly distinguishes specified competing updates from
passive fading. This proposal does not implement the relay's shorthand
“continue sleeps”: it is **continual authored post-training, not child sleep**.

**No supported weight-warm-start interface is exposed by the inspected V3
trainer or the related native/cumulative writers.** In particular, there is no
existing V3 `--init-adapter`/`--resume` option. Do not claim that replaying a
cumulative corpus, passing an adapter directory as `--model`, or passing a PEFT
model into `run_training` is a supported continuation mechanism.

Four task-only updates and unchanged 48-case readouts are feasible after a small,
explicit warm-start extension. They cannot currently be expressed safely by
changing only the original launcher's CLI arguments. Exact continuity of the
original optimizer is unavailable from the original saved artifacts: the trainer
does not save optimizer state. Use an explicitly labeled fresh optimizer, or
defer true optimizer continuation to a separate implementation.

## 2. Exact inspected interfaces and what they actually do

### Elementary fit and encoding

`/tmp/astra_fundamental_pair_20260912.py:15` defines the starting recipe:
rank 8, alpha 16, dropout .05, LR 3e-4, four epochs, seed 0, batch 4,
grad-accum 1, no packing, max length 512. `fit` launches
`python -B -m organism_v6.train_adapter_v3 --corpus FILE --out DIRECTORY ...`.
Its completed-fit assertions require 80 rows and 80 optimizer steps, no
splits/truncation/skips/nonfinite batches, and paired native token counts.
The seed-0 native 80-row epoch contains 4,517 input / 912 target tokens per arm;
four epochs TOTAL 18,068 input / 3,648 target-token presentations per arm.
These counts incorporate Main's correction, not a newly verified runtime measurement.

The original artifact layout is
`~/astra_diagnostics/astra_fundamental_teaching_20260912_attempt1/fit_teach/adapter`
and its sibling `fit_control/adapter`. These are launcher-derived paths on the
run host, not verified local checkpoint availability. Main must select the exact
completed replication checkpoint and bind its actual absolute path and hashes;
do not guess seed-replication paths or touch their launchers.

The launcher calls:

1. Native tokenizer `apply_chat_template([{"role":"user","content":context}],
   tokenize=False, add_generation_prompt=True)` exactly once.
2. `trainer.normalize_items([item])`.
3. `trainer.encode_item_segments(item, tokenizer, 512, False, True, index)`.
4. `trainer.collate([encoded_segments], tokenizer.pad_token_id)`.

It verifies the exact token vector and `[-100] * prefix_length + target_ids +
[eos_id]`. Preserve this interface for the short continuation; do not add a
second chat wrapper.

### Why the current write is not a warm start

`organism_v6/train_adapter_v3.py:500`:

`run_training(items, tok, base_model, cfg, out_dir, corpus_sha=None,
corpus_name=None, log=print) -> manifest`

- At line 558 it unconditionally calls
  `get_peft_model(base_model, lora_config(cfg, n_layers))`. Its contract says
  “already-loaded base model,” not “already-loaded adapter.” It neither loads
  prior adapter weights nor validates an existing PEFT wrapper.
- `lora_config` at line 478 fixes bias to `none`; rank/alpha/dropout/targets/layers
  come from `TrainConfig`. `ALL_PROJ` is q/k/v/o/gate/up/down projections.
- At lines 606–612 it constructs a NEW SGD or AdamW optimizer for each call.
  AdamW is invoked with only `lr`; other hyperparameters are library defaults,
  not explicitly bound values in this source. There is no scheduler/state input.
- At line 653 and following it saves adapter weights/config, manifests, metadata
  and `DONE`, not optimizer moments, RNG state or data cursor.
- `build_parser` at line 682 and `main` at line 740 expose no prior-adapter input.
  `main` loads the model named by `cfg.model`, then calls `run_training`.
- `max_steps=0` means no step limit, NOT no updates. An empty corpus writes an
  `EMPTY_CORPUS` marker, not a checkpoint control. Do not use either as a hold arm.

Related native writer cross-checks: `organism_v6/train_adapter.py:124` exposes
gate/previous-manifest receipt arguments, but its training path still loads the
base, constructs a new LoRA and new AdamW. A previous-manifest hash is provenance,
not restored adapter or optimizer state. `organism_v6/train_adapter_v21.py:1`
explicitly describes cumulative fitting from CLEAN BASE.
`organism_v6/memory_dose.py:2592` exposes
`train_hf(corpus, out_dir, rank, epochs, lr, seed, bsz, max_len, max_steps,
measure_only, throughput_steps, grad_checkpoint, model_name)` and explicitly
implements cumulative LoRA from CLEAN BASE, also with a new optimizer.
`gpu/astra_memory_cumulative_diagnostic.py:1` explicitly says “not warm-start”;
its `STARTING_STATE` is `fresh_base_cumulative_replay_not_warm_start`.
Thus “native continuation” in a corpus/teacher-forced-target sense must not be
confused with continuation of learned weights. No separate safe incremental
weight-writer entry point was established by these source checks.

### Existing readout: reuse, do not change

`organism_v6/fundamental_teaching_readout.py:62` selects exactly:

- `eval-addition-000` through `eval-addition-031` (32 behavior/action cases).
- `eval-memory-000-0` through `eval-memory-015-0` (16 known-device recall cases).

`requests` fixes prompt, order, temperature 0, seed 20260912, and 64 output tokens
per case. Interfaces are `prepare(out, model, adapter, device, lease_end)`,
`run(root, allow_gpu=False)`, and `reduce(root)`; CLI at line 287:

```text
python -B -m organism_v6.fundamental_teaching_readout prepare \
  --out FRESH_READOUT_ROOT --model PINNED_BASE --adapter CHECKPOINT \
  --device MAIN_ALLOCATED_DEVICE --lease-end MAIN_VERIFIED_UNIX_SECONDS
python -B -m organism_v6.fundamental_teaching_readout run \
  --root FRESH_READOUT_ROOT --allow-gpu
python -B -m organism_v6.fundamental_teaching_readout reduce \
  --root FRESH_READOUT_ROOT
```

These are interface illustrations, not launch authorization or commands executed
for this task. Keep output roots outside checkpoint trees. Preparation hashes
model, adapter, requests and native inputs; reduction checks recorded supervision
and release evidence. Do not widen selection to the remaining 64 evaluation rows.

Keep the current scorers exactly: addition requires unique valid ACT/PREDICT
lines, ordering and correct sums for adherence, with separate action correctness;
memory uses the existing normalized color vocabulary. The addition scorer is not
a whole-response exact-two-line parser: unrelated extra prose is not categorically
rejected. Do not silently strengthen that endpoint under “strict schemas.” Strict
new corpus/receipt validation is separate from the unchanged readout definition.

## 3. Smallest implementation change Main should make next

**Add an opt-in, validated weight-only warm-start seam to V3, plus focused tests;
do not implement fading/long-context orchestration simultaneously.** Proposed,
NOT existing, interface: `TrainConfig.init_adapter: str | None = None` and
`--init-adapter PATH`. Default fresh fitting must retain its present behavior.

At the adapter initialization seam, use a freshly loaded, unwrapped frozen base
and load exactly one adapter using the installed PEFT's trainable-load interface
`PeftModel.from_pretrained(base_model, PATH, is_trainable=True)`. This is a proposed
implementation, not an existing supported wrapper in this repository; verify the
installed library on CPU before relying on its behavior. Do NOT first inject
another adapter, merge into base, stack adapters, invoke SVD initialization or
silently overwrite loaded matrices. Reject prewrapped base inputs to this seam.

Required checks before any step:

- Prior completion and immutable model/adapter/config/source hashes; source and
  output are different, nonoverlapping, nonsymlink-aliased trees; output is fresh.
- Exactly one active/loaded adapter, r=8, alpha=16, dropout=.05, bias=none, all
  seven original target modules and the same layer coverage. Reject unsupported
  rank/alpha patterns, DoRA/extra modules-to-save or other configuration changes.
- Every non-LoRA parameter frozen; exactly the expected LoRA A/B tensor names and
  shapes trainable; all values finite; loaded tensors equal source tensors before
  the first update. Record precision conversions rather than claiming bit parity
  through an undocumented dtype change. Keep base snapshot bytes unchanged.
- Reject `svd_init` and incompatible `freeze_a`/configuration flags on this path.
- Bind actual initialization tensors and prior adapter file hashes in the result.
  Record `optimizer_initialization=fresh_per_write`, actual optimizer defaults,
  phase seed, phase step count, cumulative step count, corpus and parent receipt.
- Failure/partial output stays distinguishable from completed output; no silent
  fall-through to random initialization or stale `DONE` acceptance.

Do not make V3 accept an arbitrary preloaded PEFT model and then run the existing
unconditional `get_peft_model` branch. That shortcut provides neither a single-
adapter guarantee nor credible lineage. Do not monkeypatch PEFT in the launcher.
Adding a config field also changes `asdict(CONFIG)`/manifest expectations: Main
must finish and archive the active source-pinned seed replications before editing
their shared trainer, and bind new source hashes for subsequent work.

If strict optimizer continuity is required, this seam alone is insufficient.
The next larger change is a single loaded model + single optimizer with a
post-step immutable checkpoint callback, or explicit optimizer/RNG/cursor
save-and-resume. Neither recovers the original birth optimizer retrospectively.
An optimizer initialized fresh ONCE after birth can be continuous across the four
new steps, but still resets at the birth-to-continuation boundary. Repeated calls
to current `run_training` would reset it at EVERY interval. Keep those treatments
separate and labeled; do not call either a resume of the original 80-step AdamW.

## 4. Minimum new corpus: sixteen disjoint, sourced addition examples

Do not train on any original train, dev or confirmation operand pair, even in
reversed order. `fundamental_teaching_corpus.build_candidate` at line 89 uses 128
distinct unordered pairs from `0 <= left <= right < 20`: 64 train and 64 eval.
The full universe has 210 pairs, leaving 82. It is enough to derive this exclusion
set from arithmetic `source_records`; do not inspect confirmation outputs/scores.
Exclude BOTH evaluation halves, not only the 32 dev pairs.

Deterministic proposed selection: enumerate the unused pairs lexicographically,
shuffle once with `random.Random(2026091217)`, take the first 16, and divide into
four consecutive blocks of four. Pure CPU verification produced:

| Interval | Source pairs | Exact target sums |
| --- | --- | --- |
| 1 | (2,16), (9,10), (14,15), (3,4) | 18, 19, 29, 7 |
| 2 | (0,19), (2,12), (8,13), (1,13) | 19, 14, 21, 14 |
| 3 | (2,18), (7,18), (0,17), (12,15) | 20, 25, 17, 27 |
| 4 | (1,4), (2,5), (0,13), (0,14) | 5, 7, 13, 14 |

This is development-only training material, NOT a new held-out evaluation set.
It stays in the original operand range but is not a balanced operand/difficulty
design; shared sums and constituent operands are intentional and do not amount
to pair reuse. Do not call it clean pretraining exposure or broad transfer.

For every pair, create an immutable source record (fresh namespaced ID, integers
left/right, sum, `origin=generated_integer_addition`, generation seed and split)
and a derivation record binding target bytes to those operands. No model authors
or model-generated thoughts. Keep original manifests untouched.

Raw context: reuse `addition_context(left,right)` at
`organism_v6/fundamental_teaching_corpus.py:69`:
`Add <left> and <right>.\nSubmit the sum using ACT: <integer>.`

Target: reuse `arithmetic_response(left,right,"control","COMPUTED")` at line 73:
`ACT: <sum>\nCOMPUTED: <sum>`. This is the original launcher's truthful task-only
control format. No PREDICT instruction or target, no prediction explanation,
no new memory QA, no original training rehearsal. Do not import the original
80-row corpus into continuation; that would refresh the habit being tested.

Each native export remains `{"corpus": [item, ...]}` with exact item keys
`spans, group, view, order, meta`. Two spans: rendered chat prefix with loss
false/category `context`, then response with loss true/category
`authored_task_only_target`. Use `view="addition"`, fixed-width group IDs in the
intended order, and `meta.source_event_ids` pointing to the new source records.
Keep split/lineage/phase metadata in a separate strict sidecar manifest rather
than adding unrecognized fields to existing readout plans.

V3 `normalize_items` is permissive, not a strict validator. A preparation-side
validator must reject extra/missing keys, bool-as-integer operands, nonfinite
numbers, duplicate IDs, invalid flags, mismatched sums, source joins, forbidden
PREDICT bytes and any invalid target syntax before normalization. Validate the
two-line target with full matching, not substring matching. Revalidate hashes
and native labels at write time. No automatic padding/text substitution to force
old teach/control token counts; only require the new material be identical across
future LR-comparison arms.

## 5. Minimal four-update sentinel and controls

After seed replication is archived, choose a checkpoint by a predeclared rule
(e.g. the completed seed-0 teach checkpoint), not whichever seed had the most
favorable memory score. Preserve its original local-origin limitation:
`UNRESOLVED_LOCAL_HASHES_ONLY` in the launcher is not cured by a new lineage hash.

1. Pin checkpoint C0 and its existing 48-dev receipt, or obtain one fresh readout.
2. Pin the four disjoint task-only blocks before seeing new outputs.
3. At each interval load the PREVIOUS checkpoint, not C0; train its block once
   at LR **3e-5** (one tenth of 3e-4), batch 4, grad-accum 1, epochs 1,
   `max_steps=1`, rank8/alpha16/dropout .05, all projections, max_len512,
   `pack=False`, `shuffle_groups=False`, same base/dtype. Save C1–C4 in fresh
   separate directories, with parent chain C0 -> C1 -> C2 -> C3 -> C4.
4. Read the unchanged 48-dev panel after each write. Assert one finite optimizer
   step, four examples, no skip/split/truncation, valid complete output and a
   source checkpoint that stayed immutable. This sentinel has FOUR optimizer
   steps total, not four full original-size fits or four epochs over all blocks.
5. Keep C0 unmodified as the **no-update checkpoint control**; reload and read it
   at least at the end. Its initial readout plus end reload gives a drift check.
   If Main wants time-matched controls, also read C0 after each interval, with
   new output roots, no optimizer, and unchanged input/adapter hashes.

The most economical initial semantics after the warm-start seam are four fresh
AdamW instances (one per write), explicitly recorded. Do not hide the reset:
first-step adaptation/bias correction differs from continuous AdamW. If Main
wants four steps with continuous moments instead, wait for the larger callback
path and initialize the post-training optimizer only once.

Only the loaded adapter changes in the retention comparison: same frozen base,
readout prompts, generation limits/seed/temperature, tokenizer and scoring.
No retrieval, demonstrations, transcripts or corpus text are added to readout
prompts. No-update C0 differs in whether an update was applied, not in context.
The old task-only birth adapter and frozen OFF are useful existing anchors but
are NOT substitutes for the same-checkpoint no-update control.

Report trajectories by completed update count and cumulative input/target-token
dose: adherence/32, action correctness/32, schema diagnostics, memory correct/16,
and paired case transitions relative to C0 and C0 reload. Do not change thresholds,
select checkpoints, stop for favorable scores or open confirmation midstream.
If starting memory acquisition is absent, later zero memory is not measured
forgetting. Four steps may be too weak to show interference: a flat curve is a
bounded negative result at this dose, not indefinite retention.

This is retention under a specified competing task-only objective. The target
explicitly starts ACT rather than PREDICT and therefore trains an alternative
output convention; it is not content-neutral elapsed time. No supervised PREDICT
target does not mean “no new teaching” in the general sense: it teaches ACT-first
addition. Smaller LR is only one plasticity proxy. Without an otherwise matched
3e-4 continuation branch, this sentinel cannot identify the causal benefit of
reducing LR. Add that branch later from C0 with identical material, seeds,
optimizer-reset policy and dose—not by comparing with the original birth fit.

## 6. Longer context/repetition: faithful implementation, deferred

Two different knobs must not be conflated:

- More epochs/repeated standalone rows increases exposure but NOT the context
  available to each prediction. Existing V3 can do this with fixed short rows;
  increased passes also increase step count unless explicitly dose-matched.
- True long-sequence repetition needs multiple complete demonstrations inside
  ONE encoded item, with causal attention and monotonically increasing positions
  across demonstrations. Raising `max_len` alone does nothing to short examples.

`pack_by_group` at V3 line 326 and `collate` at line 368 intentionally isolate
separate encoded items and reset their positions. Grouping repeated rows or
enabling packing is NOT a long-context implementation. Use one multi-span item,
`pack=False`; do not turn off packing isolation to manufacture cross-item leakage.

For a later teacher-authored sequence variant, render an actual multi-turn chat
of repeated user arithmetic problems and correct assistant demonstrations, using
only that variant's declared training sources. Build a single stream with zero
loss on user turns/role headers and loss on each assistant response and its
chosen terminal marker. Pass `chat_template=False` to V3 because rendering is
already complete. If all per-turn terminal markers are explicitly supplied,
use `add_eos=False` to avoid an extra trailing EOS. This differs from the short
launcher's automatic terminal EOS and needs an explicit matched reference.
Do not merely concatenate independently rendered prompts containing repeated
default system messages and claim that is a canonical multi-turn conversation.

Necessary boundary checks before such an arm:

- Native joint tokenization must equal the intended concatenated span IDs;
  token merges across every new span/role/separator boundary can invalidate
  separately tokenized masks. Fail rather than silently assigning a straddling
  token to context or target. Audit Qwen special-token/assistant-end behavior.
- All user/system/header/padding tokens masked; every intended target and terminal
  label included exactly once. Later masked context does not remove causal
  visibility to earlier targets; that is the point of this variant.
- `encode_item_segments` at line 233 defaults to splitting at span boundaries;
  this RESTARTS segments and supplies masked overlap, not the same long sequence.
  It can left-cut a single oversized body span. An oversized first context head
  is not a safe truncation mechanism. Assert exactly one segment per intended
  sequence, length within cap, zero drops, zero splits.
- V3 adds supervised EOS per encoded segment unless disabled; splitting can
  change EOS dose. `collate` always masks the first segment token, so a target-
  first sequence also loses a supervised token. Require a leading masked prefix.
- Long examples in `encode_item(chat_template=True)` are not automatically
  multi-turn: its leading context becomes one user turn and remaining spans are
  treated as the continuation. Do not use that shortcut for conversation replay.

Proposed later order: exposure-only short-row repetition first; separately compare
native 2,048-token then 4,096-token single-stream sequences once boundary tests
pass. Record actual lengths, not labels such as “super long.” Keep repetition
count, unique examples, target-token mass, EOS treatment, effective batch and
optimizer steps explicit. Token matching alone does not match gradients; a
single long sequence changes conditioning and gradient grouping. A long variant
that sees the habit taught again is NOT the task-only fading arm. Do not implement
either larger sequence arm in the first warm-start change.

## 7. CPU tests required before Main can use the seam

This memo ran only the pure source-pair selection, not these tests. Do not claim
native token parity or adapter-load correctness from this design review.

1. Extend existing `tests/test_train_adapter_v3.py`: default fresh path unchanged;
   warm-start loads a nonzero adapter exactly once; initialization tensors match;
   one CPU step changes only LoRA; base unchanged; save/reload reproduces the
   checkpoint; C2 initializes from C1, not C0. Use tiny local fixtures, not Qwen
   inference or downloads. Main owns execution of model-bearing CPU tests.
2. Fail closed on mismatched rank/alpha/modules/layers/base pins, extra adapters,
   prewrapped input, missing/ambiguous weights, nonfinite tensors, incompatible
   init flags, source mutation, reused/overlapping destinations and partial DONE.
3. Prove optimizer policy: fresh-write moments/counter start empty each interval;
   if continuity is implemented, a split four-step run matches an uninterrupted
   local reference including optimizer tensors/RNG/order, not only final metadata.
4. Pure corpus tests: all 16 pairs unique/disjoint from all 128 original pairs
   including reversals; exact four-by-four assignment; truthful derivations;
   strict field/type checks; no PREDICT teaching, memory rows or confirmation
   material in any update export. Original corpus/source bytes unchanged.
5. Local-tokenizer-only short-row preflight with downloads disabled: identical
   native chat prefix once, exact target+EOS and masks, no splitting/truncation,
   padded labels -100, four real labels-bearing rows per batch. Check actual
   epoch ordering since no-pack still sorts groups. Assert four steps TOTAL.
6. CPU-only readout-plan fixtures: exact CASE_IDS/prompt hashes/generation config
   across C0–C4; only adapter identity differs; wrong parent/changed source rejected;
   no-update path cannot call a trainer; no readout mutates a checkpoint. Keep
   existing score/schema behavior and confirmation exclusion unchanged.
7. Deferred sequence tests: joint-token boundary parity, single stream/positions,
   earlier-turn visibility, no packing isolation masquerading as context, EOS and
   target-token multiplicity, overlength rejection. Test before GPU memory sizing.

## 8. Budget: proposal, not measurement or reservation

Smallest sentinel: one lineage, four steps, sixteen short examples, four new
checkpoints. At max_len512, at most 8,192 unpadded input-token presentations
(also at most 8,192 padded positions for four batches of four at length 512),
versus the original 18,068 input-token presentations and 80 steps. Exact target
mass awaits local tokenizer preflight. This upper bound is not a runtime ratio:
four separate base loads and serialization likely dominate the tiny fits.

Six 48-case readouts if C0 is measured anew, C1–C4 are measured, and C0 is reloaded
at the end: 288 generations, at most 18,432 output tokens. Reusing a fully bound
C0 readout reduces this to five new readouts / 240 generations / 15,360 tokens.
Time-matched C0 readouts at every interval cost nine total panels including C0:
432 generations / 27,648 output-token ceiling (not ten panels; the final interval
hold also serves as the end reload).

Conservative proposed admission envelope using the existing 600-second worker
limit: four fit workers + six readout workers = 100 A40-worker minutes before
setup/cleanup. Main could cap the total at **120 aggregate reserved A40-minutes**
(2 GPU-hours), including preparation-on-node, startup and release. Nine readout
panels instead give 130 worker-minutes; use a separate **150-minute** envelope.
These are maximum proposed budgets, not benchmarked forecasts; the warm-start
writer must actually receive the same supervision/deadline enforcement. Check
remaining aggregate budget before each stage, stop partial on exhaustion, and
preserve evidence. Never convert a timeout into a scientific zero or skip control.

One GPU sequentially is enough; no new lease, multi-GPU scheduling or worker
displacement is proposed. Storage is four adapter snapshots plus six readout
roots, not four copies of the 7B base. A later true optimizer-state checkpoint
would add moment/RNG files. No long-context GPU budget is allocated here: measure
CPU token lengths first and let Main authorize a separate bounded memory/time
profile rather than extrapolating short-fit time linearly in context length.

## 9. Interpretation and source pins

Weights do not decay merely because they remain trainable or wall time passes.
AdamW weight decay occurs when optimizer updates are applied; zero/None gradients,
optimizer state and decay settings also matter. A fixed no-update checkpoint is
the correct hold control, not four LR-zero trainer calls that could still advance
optimizer/RNG state. Smaller LR changes both update magnitude and any step-based
decay. Record resolved hyperparameters instead of treating “fading” as a mechanism.

The possible observation is loss/preservation of the already taught global
PREDICT-before-ACT habit under this authored task-only update dose. It is not
conditional intelligence, a child-generated learning loop, biological aging,
passive forgetting, H1/H2 evidence or a scientific-claim change. Main retains
implementation and scheduling decisions after the active seed replication.

Source SHA-256 values observed for reproducibility (not a Git state or approval):

| File | SHA-256 |
| --- | --- |
| `/tmp/astra_fundamental_pair_20260912.py` | `06d292311e0307b3121593cc2d34bb5c753480eb1537cced1c7fdbff913bd89a` |
| `organism_v6/train_adapter_v3.py` | `02f47008c676f6aa361a7e18bf30f5010391174d7a0dd9e648532e16cd55e169` |
| `organism_v6/train_adapter.py` | `9e39b6b6816f00ce2a78476f16e784daf31d7b26c673cbcddaf6ab508cf09caf` |
| `organism_v6/memory_dose.py` | `ab98329c433cb085cd53e1c766db350f1bb0fe2efb9181e24a3678c0d31a76e3` |
| `organism_v6/fundamental_teaching_corpus.py` | `44b1a61e10695e1e65ca3ee2e6c151eba45df1512ea3fc108402e96226ddaa13` |
| `organism_v6/fundamental_teaching_readout.py` | `d6eebc6e70f5a76fcde6c530aeacc273ae5f29a8d9a67ffe5948f04842684bb6` |

**Next smallest code change:** validated opt-in V3 weight initialization from one
existing adapter, explicit fresh-optimizer provenance, and regression tests.
No compiler work, no new readout, no memory-diagnostic edits, no replication-file
edits, and no all-variants implementation belong in that patch.
