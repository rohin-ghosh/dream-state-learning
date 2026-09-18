# Stage1 DATA/JUDGE handoff

## September17 continuation: actual receiving CPU proof

`evidence/NODE4_V1_RECEIVING_CPU_PROOF.json`, SHA
`f718d87e94d63d51333cf0c84763ecafa7d5dff21028317fed8e48afe1c41238`,
records an actual node4 CPU-only pass: 122 receiving tests, two pretrained CPU
heads, one synthetic optimizer step, no CUDA initialization and no saved judge.
The remote scratch is
`/localhome/local-rohing/orch_r177_ampere_judge_20260917/cpu_stage1`.
`RECEIVING_MODEL_MANIFEST_20260917_v1.json` binds its immutable model files.

The smaller, predeclared train/dev-only preparation is documented in
`DESCRIPTIONS_REQUIRED_20260917_v1.md`: 48 local-Qwen descriptions are missing,
with exact packet/bundle schemas. `build_development_plan` and
`development_description_packet` are metadata-only APIs;
`attach_description_bundle` performs the exact hashed producer join. An explicit
`development_plan` plus `development_source_manifest` in the train config uses
only these selected train/dev rows, with a separate untouched dev audit. It does
not consume the original locked judge-validation pool. The earlier full-pool
mode remains available but is not this proposed first development run.

Training writes `PUBLIC_SCORING_REPORT.json` via `public_scoring_report(ref)`:
numeric calibration/error aggregates only, a schema allowlist, no captions,
contest IDs or hidden-case keys. Real scoring/calibration results remain absent
until actual descriptions, data assembly and admitted training complete.

Rohin161 and `../CURRENT_BUILD_RULES.md` govern: matched learning
PARENTED/UNPARENTED DEVELOPMENT; local Qwen vision only; FINAL deferred and
parent-free. No human panel is required for provisional development. Main owns
lineages, devices, capacity/lease admission and lifecycle. These interfaces never
change the frozen child Qwen base or LoRA-only learning recipe.

## Immediate handoff to Bacon

`IMAGE_TASKS_agent_development.private.json` contains 19 image-only tasks, SHA
`482ee743952441bf8d5acf1156cfcdc69f9ff0d8b3e5d6a2e3493252788bf302`.
`IMAGE_TASKS_judge_train.private.json`, `IMAGE_TASKS_judge_dev.private.json` and
`IMAGE_TASKS_judge_validation.private.json` contain 262 / 56 / 38 tasks.
No historical captions, rating rows or FINAL tasks are included. Do not print
artifact contents to Main or parents. This is an input packet for local factual
vision, not a completed scene packet or a model-execution receipt.

Envelope schema: `NY_LOCAL_QWEN_IMAGE_TASKS_V1`; consume `tasks`, each containing
`contest_id`, `image={path,sha256,bytes}`, and `policy`. Use the policy bytes in
the packet. Descriptions must be factual image observations, not joke analysis,
suggested captions or the dataset's canny/uncanny fields.

Return one description item with exactly:

```text
{contest_id, scene, producer_receipt: {path, sha256}}
```

The bound producer receipt requires:

```text
input_kinds: ["image"]
image: the exact task image reference
policy: the exact task policy
local_model: true
model_family: "Qwen"
hosted_provider: false
model_manifest: {path, sha256}
historical_captions_used: false
uncanny_used: false
parent_history_used: false
output_sha256: SHA256(scene UTF-8 bytes)
```

The bound model manifest must identify `model_family="Qwen"`,
`local_model=true`, `frozen=true`; include actual receiving model/tokenizer file
pins, runtime, prompt/version, limits and execution provenance in its producer
closure. Additional producer receipt fields are allowed. Metadata assertions
alone are not proof of actual inference, input isolation or factual accuracy.
The vision owner preserves actual execution receipts; no new human ratification
or human validation is implied. Scene text must be 40–8,000 characters and avoid
explicit uncanny/joke/punchline/caption-analysis wording.

## Immutable data APIs

Import `gpu.ny_caption_data`:

- `load_manifest(ref)` validates disjoint whole-scene pools and dev subdivisions,
  exactly three FINAL contests, exposed-contest training-only placement and no
  FINAL release authorization. It does not release caption rows.
- `description_tasks(ref, pool)` allows the four non-FINAL pools only.
- `attach_descriptions(ref, items, NEW_ABSOLUTE_PATH)` verifies producer/model/
  image/output hashes and writes a new manifest. Original preparation3 and prior
  attempts remain unchanged. Existing descriptions cannot be silently replaced.
- `development_packet(ref, NEW_ABSOLUTE_PATH)` returns only development images,
  canonical scenes and policy metadata; refuses missing/unbound descriptions.
- `evaluator_rows(ref, pool, dev_subset=None)` streams only judge train/dev/
  validation with checked row hashes, contest joins and scene-group keys. It
  refuses FINAL and agent-development training; Main/parents must not consume it.

The successful source manifest is
`private/preparation3/DATA_MANIFEST.private.json`, SHA
`4d17031bae93bb83e3f89109e4acb5fc28dfa79706bb47b27c6b0e5fe96bb45d`.
The five pools contain 262 / 56 / 38 / 19 / 3 contests respectively. FINAL
identities remain private. The preview-exposed contest is evaluator-training-only.
The ordinary game owner can select three development tasks without exposing any
reserved identities. `development_packet` exports all available development
scenes; Main performs the predeclared three-scene projection for the game.

## Judge model and config

`MINIMUM_JUDGE_DEPENDENCIES.json` already records the staging dependency pin:
pretrained `distilbert/distilbert-base-uncased` revision
`12040accade4e8a0f71eabdb258fecc2e7e948be`. Use Torch, Transformers and
Safetensors; exact installed versions remain a receiving fact to record.

`TRAIN_CONFIG_TEMPLATE.json` is a complete proposed hyperparameter configuration,
**not a GPU admission**. Main writes a new immutable config after replacing its
unready data-manifest reference and null receiving model manifest. The original
template is not a launched or successful attempt.

The local pretrained manifest schema is `{model_id, revision, root, files}`;
`files` maps every relative runtime filename to its SHA256. Bind the same pinned
model/tokenizer repository, config, vocabulary/tokenizer and Safetensors. Unknown
files, symlink paths, pickle weights and executable Python are refused. A local
classifier backbone must actually load all pretrained backbone keys; only the new
classification heads may initialize without pretrained keys. No random backbone.

Implementation: canonical scene+caption JSON, three-class soft targets with
explicit smoothing, capped vote weights, equal-contest sampling over all rating
bands. Distinct held-contest subsets select checkpoints, calibrate temperature
and select tau; natural held-out distributions use empirical, unsmoothed counts.
Tau maximizes coverage subject to explicit positive-vote-mass/coverage objectives;
no feasible tau is a hold, never a 0.5 fallback. The independently trained two-class
scene-fit verifier uses matched-versus-scene-swap weak labels, not human truth.

Held validation reports soft log loss, Brier, q ECE, macro contest Spearman and
accepted expected vote mass/recall proxies. Real rated cases plus scene swaps,
broken punchlines, literal descriptions and scoring-instruction attacks produce
private scoring errors. Synthetic challenge labels are not real crowd ratings.

## CLI and actual GPU boundaries

```text
python3 -m gpu.ny_caption_judge cpu-smoke --output NEW_ABSOLUTE_PATH
python3 -m gpu.ny_caption_judge preflight --config CONFIG --config-sha256 SHA --output NEW_ABSOLUTE_PATH
python3 -m gpu.ny_caption_judge train --config CONFIG --config-sha256 SHA \
  --admission ADMISSION --admission-sha256 SHA --output NEW_ABSOLUTE_DIRECTORY
```

Preflight reads operational metadata and installed-package metadata only, without
Torch imports or model loading. Training checks source/config/model pins and all
required descriptions before importing/loading GPU models. The new output
directory and `ONCE.json` latch preserve failures; rerunning a consumed directory
is refused. No automatic retries or silent device/provider fallback.

Main's admission must use `NY_JUDGE_CAPACITY_ADMISSION_V1`, issuer
`Main/Astra builder`, scope `R177_STAGE1_JUDGE_TRAINING_ONLY`, and contain:
exact `config` ref; `source_sha256` for both owned modules; `issued_unix`,
`end_unix`, `lease_safe_end_unix`; `max_gpu_seconds` (at most 7,200), `max_steps`;
`device="cuda:0"`, `device_uuid`; exact `output_root`; `min_free_bytes`,
`max_reserved_bytes`, `max_model_examples`, `max_model_tokens`.
`CUDA_VISIBLE_DEVICES` must equal that exact UUID. Runtime checks one visible GPU,
its actual UUID and free memory. Forward examples and padded input tokens for
training, calibration, validation and stress are charged before invocation.
This file does not author an admission, approve capacity or extend any wall.

## Scoring and second comparator integration

`CaptionJudge(humor_predict, scene_fit_predict, temperature, tau,
scene_fit_threshold).score(scene, caption)` returns `q`, three class probabilities,
`scene_fit_probability`, boolean `scene_fit`, `accepted`, explicit thresholds and
provisional status. Predictors receive only canonical scene+caption, never arm,
history, self-justification or reference captions. For `gpu.ny_caption_game`, Main
adapts the result to `JudgeResult(scene_fit=result['scene_fit'], q=result['q'])`
and uses the same bound tau. No automatic alternate judge.

`validate_checkpoint(config_ref)` checks the immutable trained inventory and
current source pins, refusing missing tau, altered weights or unknown files.
`load_cpu_judge(config_ref, max_model_examples=..., max_model_tokens=...,
max_seconds=...)` provides an explicitly CPU-only local scorer with bounded
calls. The shared pretrained loading path has now passed actual receiving CPU
tests; loading an actually trained judge checkpoint remains untested because no
such checkpoint exists.
GPU-serving process/slot integration remains Main's lifecycle responsibility.

Training writes `BLIND_COMPARATOR_INPUT.private.json`: only case keys, scenes,
captions and independent instructions, no first-judge scores, lane or history.
The separately admitted local frozen Qwen runner consumes it and returns
`NY_BLIND_LOCAL_COMPARATOR_OUTPUT_V1` with `input_sha256`, `local_model=true`,
`blind_to_lane_and_first_judge=true`, bound `model_manifest`, and rows containing
`case_key`, three `humor_probabilities`, and `scene_fit_probability`.

```text
python3 -m gpu.ny_caption_judge compare-import --packet INPUT --packet-sha256 SHA \
  --comparator-output OUTPUT --comparator-output-sha256 SHA \
  --first-errors SCORING_ERRORS --first-errors-sha256 SHA --output NEW_REPORT
```

The importer checks complete joins and model/input/output bindings, then reports
per-kind q/scene-fit disagreement and comparator log loss on real rated cases.
The comparator runner/inference is not executed or supplied by this import CLI.
No second-model validation result exists yet; imported metadata is not proof of
execution by itself. All outputs remain PROVISIONAL and not human-validated.
# Rohin167 released-scene development interfaces

- `ny_caption_data.build_released_development(manifest_ref, destination, seed=177)`
  freezes all available whole-group joins from pinned released train descriptions;
  outputs an immutable judge-only scene catalog, train/dev plan and new manifest.
  It never constructs factual scenes from caption/rating text.
- `ny_caption_data.evaluator_rows` consumes the explicit judge-only catalog for
  train/dev. Agent packets still require the unchanged local-Qwen producer path.
- `SIMILARITY_TRAIN_HANDOFF.json` points to an independent train-only144/36
  whole-contest fitting/calibration packet. Private text remains in its private
  packet; Main's handoff is refs, policies, counts and missingness only.
- `observe_released.py --version 4` retrieves bounded allowlisted operational
  receipts through `gpu/a40r_ssh.sh`; no caption or locked-evaluation file reads.
- Actual run root:
  `/localhome/local-rohing/orch_r177_ampere_judge_20260917/released_all_v4`.
  Check `training/TRAINING_STARTED.json`, `FIRST_OPTIMIZER_STEP.json`, and numeric
  `progress/*.json` for observed work. `COMPLETED.json` and
  `training/PUBLIC_SCORING_REPORT.json` exist only if final calibration succeeds.
- Intermediate checkpoints are not a frozen calibrated judge. Only completed
  `training/judge_config.json` binds the chosen models, calibration, tau and
  independent development audit. Local Qwen/second-comparator status is separate.
