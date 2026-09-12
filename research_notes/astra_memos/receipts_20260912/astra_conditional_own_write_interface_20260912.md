# Conditional own-write interface audit for Main — 2026-09-12

Scope: bounded local source/document audit, not an experiment, implementation, authorization, or behavioral claim. No repository writes, Git commands, GPU/model calls, remote actions, or tests executed. Main remains sole Git operator. Paths/line numbers refer to the local source inspected during this audit; historical results below are attributed to local reports, not independently rescored here.

## Decision in brief

**Use the existing V3 trainer with two explicit spans: the exact native chat-rendered event prompt at zero loss, followed by the complete captured child response at loss. Disable trainer-side chat rendering and packing.** This is already implemented as a material/export pattern in `parent_wake_material.encode_candidate`, not a proposed trainer API.

The currently selected RuleGame route is **conditioning/render mismatched**, although its special preschool recipe already masks the synthetic prefix. It trains a child JSON record after `Situation ... My measured action record:`, not after the actual Qwen chat-wrapped record request containing emitted action, world response, observed fields, and record instructions. Its target is the selected child's record text, not a parent lesson. Do not confuse a missing context/chat interface with absence of masking.

The smallest RuleGame integration preserves the existing selected record responses and retrieves each response's own recorded request. This aligns **record-response training with record-response evaluation**. It does not turn a JSON-record target into an action-generation target: evaluation also has a separate wake/action/quiz interface. Training complete wake responses instead would change source selection/target semantics and is a separate decision.

## 1. Current route: exact source chain

- `organism_v6/rulegame_parenting_diagnostic.py:443` (`play_task`) constructs the **record request** after an actual TRY:

  ```text
  Task: <eid>
  Execution: <eid>#t<tick>
  Actual emitted output:
  <actual child wake output>
  Actual world response:
  <actual world outcome>
  Observed fields: <JSON of values, observed, predicted>
  <RECORD instruction>
  ```

  The record event stores `execution_id`, `source_call_id` (wake), `call_id` (record), and complete returned `text`. This is post-action context for a later record response; it is not valid pre-action context for the earlier wake output.
- `Calls.ask` at `:338` saves `calls/<call_id>.request.json` with `request.prompt`, role/arm/eid/tick/seed and prompt hash, plus `<call_id>.response.json` with `response.text`, token evidence and response hash. Under formation, these live in `formation/data/calls/`. `ReplayCalls.ask` at `:366`, `check_capture`, and `audit_native_calls` at `:588` are existing replay/native-token custody machinery.
- `NativeBackend.generate` at `:303` calls the tokenizer's `apply_chat_template([{"role":"user","content":request["prompt"]}], tokenize=False, add_generation_prompt=True)`. `run_evaluation` at `:489` uses `play_task(..., notes=True)`; it exercises both action generation and this record generation interface. The wake prompt itself is assembled at `:405` from BOOT, task/goal, prior outputs/outcomes and protocol state.
- `select_records` at `:619` takes the first two eligible distinct apply executions per arm, with lexical payload rejection. `render_corpora(selection)` at `:643` discards the original request and emits synthetic strings containing the original `row['text']`. `material`/`verify_material` at `:648`/`:683` bind `{"recipe":"preschool_records_v1","corpus":[...]}`.
- `write_adapters` at `:825` actually selects `python -B -m organism_v6.train_adapter --corpus ... --out ... --rank 8 --epochs 12 --lr 1e-4 --seed 2` (`:838`). This source currently specifies **12 epochs**, not the older memo's 3. `TRAIN` at `:48` expects two texts and 12 optimizer steps.
- `organism_v6/train_adapter.py:171` dispatches `preschool_records_v1`; `child_record_prefix_length` at `:25`, `child_target_mask` at `:35`, and `child_label_counts` at `:47` mask prefix/padding and count shifted child supervision. Tokenization is bare text, padded batch size 4, maximum length 512 (`:184` onward), not a chat conversation. The diagnostic's `audit_tokens` at `:568` supplies the corresponding preflight; this is not a contextual trainer.
- Do **not** merely feed V3-style objects to v1: `train_adapter.py:174` reduces dictionaries to `c.get("a", "")`, losing context (and producing empty text for a `context`/`target` object). Changing the corpus shape alone is not integration.

## 2. Existing trainer choices and exact supported schema

### Recommended: V3 explicit pre-rendered spans

Existing functions in `organism_v6/train_adapter_v3.py`:

| Function | Existing contract |
|---|---|
| `normalize_items(raw)` (`:125`) | Accepts a corpus list or `{"corpus": [...]}`; supports explicit spans, `context`/`target`, `q`/`a`, and legacy strings. |
| `encode_item(item, tok, max_len, chat_template=False, add_eos=True, item_index=0)` (`:151`) | Encodes spans separately; false-loss spans get `-100`, true-loss spans get token labels. Appends supervised EOS by default. |
| `encode_item_segments(...)` (`:233`) | Existing overflow handling; must preflight to exactly one unsplit, untruncated segment for this contract. |
| `collate(packs, pad_id)` (`:368`) | Pads with ignored labels and masks segment-first labels. A nonempty context keeps the first response token supervised under causal shifting. |
| `run_training(items, tok, base_model, cfg, out_dir, ...)` (`:500`) | Wraps the supplied base in fresh PEFT LoRA, optimizes trainable parameters, saves adapter/manifest. Caller supplies base freshness when using this function directly. |
| `build_parser`, `config_from_args`, `main(argv=None)` (`:682`, `:722`, `:740`) | Actual CLI; `main` reloads tokenizer/base from `--model`, then calls `run_training`. |

The following is an **existing schema illustration**, not prepared data or a new API:

```json
{
  "corpus": [
    {
      "spans": [
        ["<exact native chat-rendered, parent-free actual record request>", false, "context"],
        ["<complete captured child record response, unchanged>", true, "own_output"]
      ],
      "group": "<execution_id>",
      "view": "record",
      "order": 0,
      "meta": {"call_id": "<record-call-id>", "execution_id": "<execution-id>"}
    }
  ]
}
```

`group`, `view`, category strings and metadata are existing free-form fields, not new trainer arguments. Keep teacher-bearing source maps outside the corpus; metadata is not an excuse to deliver parent text to the training process. V3's output recipe is `v3_masked_packed`, even with packing off. A corpus-level recipe is not a masking switch for V3.

**Concrete already-used CLI**, copied in substance from `gpu/astra_parent_wake_diagnostic.py:156` (`trainer_command`), shown for interface only, NOT executed or a proposed RuleGame dose:

```sh
python -B -m organism_v6.train_adapter_v3 \
  --corpus /ABS/MATERIAL/lesson.json --out /ABS/FRESH/adapter \
  --model /ABS/PINNED_QWEN25_7B_INSTRUCT \
  --rank 8 --alpha 16 --dropout 0.05 --lr 1e-4 \
  --epochs 3 --seed 0 --batch-size 1 --grad-accum 1 \
  --no-pack --max-len 4096
```

Omit `--chat-template` because context is already rendered; omit `--no-eos` for the existing response-plus-EOS convention. The documented 4096 limit is an existing diagnostic choice, not proof that every RuleGame row fits. Reject overlength before training; neither automatic splitting nor truncation preserves the requested complete-context/complete-response pair. If Main instead wants literally only captured response-token supervision without synthetic EOS, `--no-eos` exists; that changes accounting and must be explicit.

**Exactness trap:** V3's `--chat-template` mode applies `.rstrip("\n")` to leading context (`:167`). Pre-render through the pinned tokenizer yourself and use `chat_template=False` to preserve trailing newlines and avoid double wrapping. Compare native and HF rendering/token IDs, not just approximate prompt text.

### Smallest legacy implementation, but weaker contract: v2.1

`organism_v6/train_adapter_v21.py:24` exposes `main()` and accepts `{"corpus":[{"q":"<actual raw user prompt>","a":"<complete own response>"}]}`. Real invocation is `python -m organism_v6.train_adapter_v21 --corpus ... --out ... --rank 8 --epochs 2 --lr 3e-5 --seed 0`; model comes from `V6_MODEL`. Its module docstring accidentally names `train_adapter`, so follow the module/parser, not that example.

Its nested `encode(item)` (`:74`) chat-renders q and masks its labels. However it **silently caps answer-plus-EOS at 1024 tokens**, then left-truncates context to fit 2048 total (`:72`–`:91`). It has no CLI max-length/no-truncation guard or V3-grade truncation manifest. For externally proven short pairs it can support the requested loss, but it is not the safest minimal integration for a hard completeness invariant. Never use its plain-string fallback: that substitutes `GENERIC_Q`, recreating a context mismatch. V3 is already tested and used for precisely the explicit-span export.

## 3. Existing contextual diagnostic/export precedents

- `organism_v6/parent_wake_material.py:170` — `without_teacher(prompt, bootstrap, teacher)` verifies a specific recorded envelope, deletes the exact teacher component, and leaves other context intact. **Not a generic RuleGame stripper.**
- `parent_wake_material.encode_candidate(chunk, arm, payloads, tokenizer, max_len)` (`:178`) uses `chunk['raw_output']`, not the clipped ledger note; rejects teacher echoes in target/context; validates original native rendering; pre-renders parent-removed context; produces the two spans; rejects overlength; checks actual V3 encoded/collated IDs and labels (`:185`–`:207`). This is the closest ready-made pattern.
- `parent_wake_material.source_arm` (`:34`) joins actual requests, raw outputs, repeated actions and event custody. `export_pair` (`:213`) exports source-linked paired material; it is tied to its historical source format and should not be passed RuleGame captures pretending they are that format.
- `organism_v6/parent_correction_write.py:119` — `strip_teacher` performs a bound exact package deletion. `select_event` (`:144`) retains original failed-action public feedback, excludes wake2 context/answer leakage, and provides `whole_raw` versus `act_only`. `make_corpus` (`:202`) and `tokenizer_preflight` (`:213`) already verify full raw-target roundtrip, all target labels, no splitting/truncation, and actual collation/causal shift. Its fixed event/replay recipe is not a drop-in RuleGame selection policy.
- `gpu/astra_parent_wake_diagnostic.verify_fit` (`:201`) validates config, native token totals, zero skips/drops/splits/nonfinite batches, DONE, corpus hash, actual adapter config and hashes. Its `probe_spec` (`:226`) supplies hash-bound fresh OFF/ON evaluation. Reuse the verification pattern, not its fixed 32-row/96-step requirements.

## 4. Parent exclusion and event exactness: necessary boundaries

For a selected RuleGame record, retrieve `request.prompt` using **record `call_id`**, not wake `source_call_id`, and target the associated `response.text` byte-for-byte. Join back to the source wake execution and replay its world outcome. Record prompts do not intentionally insert the temporary parent restatement; wake prompts can (`play_task:405`). Nevertheless `Actual emitted output` is child text and can echo a lesson. Audit the **entire** rendered context and target, not just the synthetic prefix or top-level request.

“Parent-free” must mean no parent-authored lesson/package or copied lesson-bearing spans are supplied, not no common word/byte appears in both texts. Existing lexical checks are explicitly not semantic certificates. `select_records` presently checks whether an entire normalized payload of at least 16 characters occurs in the target (`:631`–`:634`); this is not a guarantee against all partial lesson copies and does not inspect the new context. Parent-wake/correction echo guards are useful precedents, not universal provenance proofs.

If a historical prompt contains an explicit lesson block, retain the original only in custody evidence and delete that exact bound block for sleep; call the resulting prompt **actual context minus parent package**, not the byte-identical original. If parent content is embedded in otherwise-required child history or in the raw target, reject the pair rather than silently rewrite it. A complete unchanged response and total lesson exclusion cannot both be promised for a contaminated response. No fill-in synthetic records, harvesting more tasks, or paraphrase cleaning is part of this audit.

Do not append the outcome of the response being predicted to its own pre-response context. Using a completed TRY's result to condition the subsequently generated record is temporally valid; conditioning that earlier TRY output on its later result is leakage.

## 5. Fresh reload and LoRA-only

V3 `main` reloads the pinned base (`:755`–`:759`); `run_training` calls `get_peft_model(base_model, lora_config(...))` (`:558`), with bias `none` (`:478`), all seven projection modules by default, and optimizes only `requires_grad` parameters (`:606`). `save_pretrained` persists the PEFT adapter (`:653`). No init-adapter/optimizer-continuation CLI is present. This is fresh-base refitting, not continued training of a previous child's adapter. Do not enable SVD-init/freeze-A/layer restrictions as incidental changes.

The CLI alone does not prove pinned origin, fresh output directory, immutable base, or fresh evaluation. Preserve the RuleGame supervisor's fresh worker/output discipline, base/adapter hashes and native OFF/ON identity checks (`worker` near `rulegame_parenting_diagnostic.py:899`, native backend creation at `:927`). Add/reuse a CPU tiny-model assertion that only LoRA parameters are trainable, base tensors stay identical across an update, and a separately reloaded base-plus-saved-adapter reproduces outputs. These are verification requirements, not claimed tests run here.

## 6. Smallest integration scope for Main, not an applied patch

1. **RuleGame material/export and custody:** extend `render_corpora`'s available inputs to access validated record requests/responses; emit the explicit spans, with source mapping in a separate audit artifact. Update `material`, `verify_material`, and `audit_tokens` consistently. Preserve the existing selected records, paired-shortage behavior, ordering and outcome replay; fail closed on contamination or token overflow.
2. **RuleGame trainer command and fit verifier:** switch `write_adapters` to the existing V3 CLI, pin explicit config, and change `verify_fit` from v1 `child_body_only` metadata to V3 manifest/count/LoRA checks. Include V3 and any newly used helper in implementation provenance pins. Do not relabel an old material/plan receipt as compatible; preserve old artifacts and produce a separately bound plan if implemented.
3. **Focused tests:** extend `tests/test_rulegame_parenting_diagnostic.py`; only extend trainer tests if adding an absent freeze/reload invariant. **No edit to either trainer is necessary** for the recommended interface. No base-model, evaluation-world, scoring, parent-policy, GPU runner redesign, or new API is needed.

Dose is not interface-neutral: current v1 batch size 4 gives one update per epoch for two rows; V3 default batch size 1 gives two. Preserve the intended update accounting explicitly (e.g. existing V3 `--batch-size 4` if retaining the two-row batch geometry), and pin epochs/seed/shuffle/EOS/max-length/checkpointing rather than inheriting V3 defaults accidentally. Native context increases input tokens even when response bytes are fixed. Switching trainers is not evidence of an isolated masking intervention.

### Required regression coverage and existing starting points

- Exact call/execution/world join, including wrong/duplicate call IDs, same text from another execution, changed prompt/output/outcome, and unchanged selection. Existing RuleGame tests already cover selection/custody and v1 prefix masks; update expected interface instead of deleting those obligations.
- Exact native chat prefix (including trailing LF), no double chat wrapper, no parent lessons/restatements in either span; reject partial echo/contaminated context or target under a declared policy. Preserve raw whitespace/JSON response and do not reconstruct it from parsed fields.
- Actual `normalize_items -> encode_item_segments -> collate` equality to `context_ids + response_ids + EOS`; labels exactly `[-100]*len(context_ids) + response_ids + EOS`; padding ignored, first response token supervised after causal shift, no skipped examples, splitting or truncation. Include an overlength pair and an exact-boundary pair.
- Fresh output/base/adapter identity, only LoRA trainable, unchanged base tensors and saved-adapter fresh reload; verify no teacher-bearing source-map file enters trainer inputs. Verify changed corpus/config/hash fails closed and old v1 metadata is rejected.
- Existing tests to reuse: `tests/test_parent_wake_material.py:108` teacher removal/no same-event appended score; `:128` full output rather than clipped ledger; `:170`/`:180` teacher echoes in target/context; `:197` no truncation; `:221` rendering mismatch. `tests/test_parent_correction_write.py:303` full target/causal shift; `:316` corrupted collate; `:331` no target normalization. `tests/test_train_adapter_v3.py:48`, `:63`, `:202`, `:227`, `:292` cover accepted schemas, masks/EOS, collation, CLI and tiny-model training/manifest. `tests/test_astra_parent_wake_diagnostic.py` covers material/fit/probe binding. Tests were inspected, not executed.

## 7. Existing negative evidence: interface support is not efficacy

**Closest precedent — P0 raw-wake contextual lesson/sham fork.** `research_notes/analysis/2026-09-12_p0_raw_wake_fork_terminal_watcher_audit.md` reports all four cells at **0/16 first-ACT solves**. Native partial score: OFF 0.1125, lesson ON 0.0475, sham ON 0.010546875. The positive difference-of-gains is “less harm,” not useful learning. This already used source-linked raw continuations, parent-removed chat context, V3 and fresh OFF/ON. Boundary: one optimizer seed, historical mixed-family material, reused mini-Sudoku panel, unequal supervised doses; most targets precede current-action feedback. It does not directly test RuleGame's post-outcome record request.

**Complete response has not shown an automatic advantage.** `research_notes/astra_memos/receipts_20260912/astra_correction_utility_analysis_20260912.md` reports the one-event contextual correction comparison: whole-raw ON solves **1/32, 0/32, 1/32** versus ACT-only **2/32, 2/32, 1/32**, with all OFF cells 0/32. Whole-raw minus ACT-only is negative, negative, tied. One selected experience with 32 replays, three epochs; unequal target-token doses. This cautions against assuming full response is better, not against its interface validity.

**Masking can reduce acquisition as well as spill.** `research_notes/analysis/2026-09-12_prefix_mask_terminal_independent_audit.md` reports dose-16 correct-frame probability OFF→ON **.260→.251**, compared with whole-text **.260→.685**; mean spill falls **.416→.202**, but binding/dose/abstention gates fail. This is a different memory-frame prefix-mask experiment, with boundary/dose confounds, not a causal rejection of event-conditioned assistant loss.

**Older contextual writer instability also exists.** `research_notes/2026-09-11_legacy_writer_seed0_7_8_terminal_closure.md` reports contextual B-family cells inconsistent or harmful across lives; B's descriptive cross-life deltas are −.0078/−.0169 on report/disjoint panels. The report explicitly says A versus A_v3 is not a clean masking contrast; plain-string A_v3 has no context, and other recipe variables change. Narrow QA C collapses with targets lacking the native ACT/PREDICT interface. These observations support taking render/target mismatch seriously, not claiming this proposed wiring will fix behavior.

**Disposition:** existing V3 capability is sufficient; Main need only decide the narrowly defined record-request/own-response export and bindings. No new experiment is specified or launched, no positive behavioral outcome is predicted, and this audit does not ratify a scope/invariant change. Any later implementation must follow the applicable project authorization and provenance contract.
