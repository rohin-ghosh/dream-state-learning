# Authored reflection/correction-uptake runtime handoff

**September 13, 2026 UTC — EDITSTOP. Main owns all native/GPU/network operations.**

Implemented only the three assigned `/tmp` deliverables. No repository, Git,
corpus, existing source, existing run, dependency, model, or precision changes.
No native tokenizer/model/GPU/network operation or launch was performed. CPU
tests use disposable `/tmp/reflection_cpu_*` fixtures, synthetic API records,
the existing trainer's pure-Python encoding functions, and mocked native calls.
They do not import, execute, copy, or freeze Carver's in-progress corpus module.

## Final executable/test SHA256

```text
0f79efa1f4e4da6a9d1ec245c09e665f7c2b7d8bce31f7e01fe01b00f95a72fc  /tmp/astra_reflection_fit_run_20260913.py
65da4c9a70ea3622e0c7b76fdbe89b6291270ed6372749200016ea4b8b3e3660  /tmp/test_astra_reflection_fit_run_20260913.py
```

This handoff's own SHA256 is returned separately, avoiding recursive hashing.

## Validation performed

```bash
python3 -B /tmp/test_astra_reflection_fit_run_20260913.py -v
```

**40 tests passed**, final run: 7.744 seconds. In-memory compilation of both
Python files passed without writing bytecode. An AST comparison verified the
literal ENGINE, PARAMS, and base RECIPE definitions exactly match the accepted
perception runner; only an explicit runtime scope note is added to RECIPE.
`prepare --help` was checked; native `prepare` was not executed.

Coverage includes actual trainer segment/collate masks against a fake tokenizer;
full targets plus one EOS; prompt/padding/template-tail masking; pre-encoder
overflow rejection; paired target/order and explicit system checks; source,
template, and event leakage rejection; metadata-free DEV exports; application
exclusion from loss; source/binding/recipe/environment drift; independent cold-fit
calls; complete fit manifests; adapter custody; all144 captures and eight distinct
worker receipts before scoring; strict raw A/B syntax; separate prose limitations;
capture/log tampering; missing fits/captures; no overwrite/retry; matched LoRA OFF;
600/300-second stage limits and global deadline clamping; mocked 30-second NVML;
busy-device refusal; owned-group cleanup on timeout and SIGTERM; nested timer
restoration; and collection output disjointness.

**Not demonstrated:** native Qwen token counts, CUDA execution, actual fits,
native engine compatibility, GPU release in deployment, or diagnostic outcomes.
Main must verify these using the final pinned snapshot. CPU fixture token/byte
counts are not native acceptance evidence or a completed experiment.

## Runtime contract

- Scope: `authored_reflection_12train_24dev_twofits_sixreadouts_v1`.
- Uses only the new module's `build_panel`, `export_training`,
  `export_development`, and `score_response` public API.
- No corpus bytes, historical deictic task, or application answers are embedded
  in this runner. Main supplies Carver's **final post-fix** source hash after
  his EDITSTOP. The nondeictic change is consumed through the stable API.
- Two fresh fits: `fit_withdrawn`, then `fit_present`. Each uses the same12
  authored restatement TRAIN targets, paired order, seed0, and fresh base,
  optimizer, and adapter. No warm start or perception adapter is used.
- Generic system is explicitly `You are a helpful assistant.` in every TRAIN
  and DEV request, including both withdrawal conditions; native rendered system
  text must match it. No tokenizer-default system is assumed.
- Rank8, alpha16, dropout0.05, LR0.0001, four epochs, batch4, gradaccum1,
  no packing, max_len1024, AdamW, existing bf16 configuration, all existing
  projection targets. Exactly12 updates and48 row presentations per fit.
- The unchanged trainer API uses `overflow="truncate"`, but truncation is
  **forbidden**: complete native token length is checked before calling its
  encoder; full native IDs and labels must match; fit-time encoding is checked
  again; completed manifests require zero truncation, splitting, skipped rows,
  or nonfinite batches. Overflow is a terminal rejection, not permission to
  shorten prompts, targets, the corpus, or change the dose.
- Supervise every complete assistant target token plus exactly one native EOS.
  Mask all prompt/generation-prefix, padding, and trailing template newline
  tokens. Keep the exact native prompt and full assistant text, IDs, labels,
  authored targets, target/prompt/full-text UTF-8 byte counts, native token counts,
  supervised token counts, and actual collated batch/padding exposures. Prompt
  and padded work can differ across arms; compute equality is not asserted.
- Six fresh readout workers, in this fixed order:
  `OFF__withdrawn`, `OFF__present`, `fitWithdrawn__withdrawn`,
  `fitWithdrawn__present`, `fitPresent__withdrawn`, `fitPresent__present`.
  Each performs12 restatement followed by12 application DEV calls: **144 total**.
- Readout matches perception's LoRA-enabled engine, including max_lora_rank32,
  bf16, max_model_len16384, no prefix caching, eager execution, and one GPU.
  OFF passes `lora_request=None`; fitted arms supply their hash-bound adapter.
  Greedy temperature0, seed0, max_tokens192; no retry or response normalization.
- Only `input_messages` reaches rendering/generation. Row IDs, proofs, targets,
  scoring metadata, and state labels stay outside model requests. Application
  and all DEV examples are excluded from training items and loss.
- Controller has a3600-second outer budget, with a40-second cleanup reserve;
  fits have600 seconds each, readouts300 each, and NVML queries30 seconds.
  Stage ceilings include the worker's verification/initialization. Remaining
  global budget can shorten a stage; no deadline is extended to finish a panel.
  The nominal worst-case stage/query/release sum is3560 seconds, so extra work
  still consumes the global budget. SIGTERM unwinds to cleanup; cleanup protects
  its reserved bounded interval from repeated SIGINT/SIGTERM. Only the spawned
  worker process group is signaled. A foreign busy GPU is never killed.
- A release receipt requires both owned-group exit and an empty exact-UUID GPU
  query. Any failure preserves raw artifacts and prevents completion/scoring.
  Uncatchable SIGKILL, host failure, or stuck kernel tasks cannot be certified
  released by Python; Main retains operational responsibility for those cases.
- Only after both completed fits, all six24-call capture closures, eight distinct
  worker PID/PGID receipts, and all release/log inventories validate can the
  controller write `capture_complete.json` with `scored=false`.
- Collection is a **separate180-second** command. It verifies the completion pin
  and complete inventory before the first score, then writes separate per-cell
  `exact_authored_fixture_matches` and `strict_application_correct` counts out
  of12. There is no composite metric, promotion threshold, or automatic pass.
- An exact authored prose mismatch is **NOT semantic prose failure**.
  `semantic_prose_score` remains null. Application accepts only raw `A` or `B`;
  spaces, newlines, fences, or explanations are not stripped. This small authored
  near-transfer panel retains the shortcut and scientific limitations documented
  in Carver's final handoff; it is not general reflection, persistence, L2, or
  H1/H2 qualification, parenting efficacy, or teacher distillation.

## Model binding and the inherited NO_FIT label

The public helper validates Main's existing official Qwen file receipt or
historical public model-only binding, with the same fixed repository/revision
and local file hashes as perception. No new download or alternate model source
is added. The runtime binding uses scope
`official_public_revision_files_only_v1`, preserves the upstream scope separately
as `upstream_receipt_scope`, and stores the original receipt object as evidence.

An upstream `perception_DEV12_anchor_NO_FIT` describes that historical receipt,
**not this runtime**. The new runtime explicitly authorizes its two fits in its
own scope/recipe note. `clean_ancestry_certified=false` means this runner makes
no clean-ancestry certification; official file equality does not establish
ancestry. No historical receipt is edited, normalized in place, or recertified.

## Main-only prerequisites and commands

1. Wait for Carver's final post-nondeictic-fix EDITSTOP and exact module hash.
   Do not take the earlier/in-progress hash from the original handoff.
2. Main creates a fresh, immutable, non-checkout source snapshot with **exactly
   these five files**, no symlinks, bytecode, Git files, old runs, or extra files:

   ```text
   organism_v6/__init__.py
   organism_v6/birth_skill_corpus.py
   organism_v6/rulegame_parenting_diagnostic.py
   organism_v6/train_adapter_v3.py
   organism_v6/birth_reflection_probe.py
   ```

3. Main supplies an external JSON object mapping exactly those five relative
   paths to final lowercase SHA256 strings; hash that pins file itself. Historical
   helper bytes must satisfy Carver's internal dependency checks. The runner
   verifies the entire snapshot before and after preparation and on later stages.
4. `--probe-driver` means a separately frozen copy of the accepted **public model
   helper** `/tmp/astra_birth_skill_probe_run_20260913.py`, not Carver's new
   module. Pass its final SHA256; its NVML timeout must be30 seconds. The runner
   reuses its public binding, render/response audit, vacancy, and cleanup functions,
   not its perception corpus selector, anchor, disabled-LoRA engine, or controller.
5. Use only the already locally verified official Qwen2.5-7B-Instruct files and
   Main's public-file receipt. Keep the existing native environment/interpreter
   and dependencies unchanged. Both command flags and the receipt are required;
   a local directory without that binding is insufficient.
6. `ROOT` and `LOG_DIR` must **not exist**; prepare creates them. They must be
   disjoint from each other, the source/model/receipt/helper/pins/runner paths.
   The snapshot must already exist. Main should use fresh exclusive external
   control-command stdout/stderr captures if desired; worker logs are created
   automatically under `LOG_DIR/<stage>/`.
7. Supply the exact vacant GPU UUID/index and lease-end Unix timestamp. At both
   prepare and controller start the lease must exceed current time by
   3600+180+40 = **3820 seconds**. Worker visibility is set to that UUID.

Main sets the following variables to its real verified paths/hashes; these
commands are guidance only and were **not executed** here:

```bash
RUNNER=/tmp/astra_reflection_fit_run_20260913.py

"$PYTHON" -B "$RUNNER" prepare \
  --root "$ROOT" --source "$SOURCE" --model "$MODEL" \
  --probe-driver "$PUBLIC_HELPER" --probe-sha256 "$PUBLIC_HELPER_SHA256" \
  --binding-path "$BINDING_RECEIPT" --binding-sha256 "$BINDING_SHA256" \
  --corpus-sha256 "$HISTORICAL_CORPUS_SHA256" \
  --reflection-sha256 "$CARVER_FINAL_REFLECTION_SHA256" \
  --source-pins-path "$SOURCE_PINS" --source-pins-sha256 "$SOURCE_PINS_SHA256" \
  --log-dir "$LOG_DIR" --gpu-uuid "$GPU_UUID" --gpu-index "$GPU_INDEX" \
  --lease-end "$LEASE_END_UNIX"

# Main copies PLAN_SHA256 from the successful prepare result.
"$PYTHON" -B "$RUNNER" controller \
  --root "$ROOT" --plan-sha256 "$PLAN_SHA256" --allow-gpu

# Only after ALL_CAPTURES_CLOSED_UNSCORED, copy COMPLETION_SHA256 from that result.
# COLLECTION_OUT must be a new directory disjoint from all protected paths/logs.
"$PYTHON" -B "$RUNNER" collect \
  --root "$ROOT" --plan-sha256 "$PLAN_SHA256" \
  --completion-sha256 "$COMPLETION_SHA256" --out "$COLLECTION_OUT"
```

`worker` is an internal controller-spawned command, not a standalone launch
instruction. It requires `--allow-gpu`, a fresh owned process group, the pinned
plan, the exact CUDA-visible UUID, and the lease check. Do not bypass the
controller's per-stage/global deadlines by invoking workers independently.

After failure: retain evidence, stop, and report the incomplete diagnostic.
Do not rerun a stage, overwrite/reuse root/source/log/output paths, change corpus
or recipe, normalize responses, report an incomplete panel as zero, or collect
partial captures. Any subsequent attempt needs a separate explicit Main decision;
there is no automatic retry or continuation path.

**EDITSTOP — no launch performed; Main supplies final source pins and owns execution.**
