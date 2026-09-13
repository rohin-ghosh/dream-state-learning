# EDITSTOP — full-dose authored contrastive paired runner

2026-09-13. CPU readiness only. Main owns protocol, allocation, native prechecks,
preparation, launches and collection. No native/model/tokenizer/GPU/network/Git
operations were performed by this sidecar. No repository or old source edits.

## Owned files and final code pins

- `/tmp/astra_contrastive_full_dose_run_20260913.py`
  SHA256 `663879c3ccec0c0543a6de5eff60e2e92f7482d9f0c1db3879722aa988452bd0`
- `/tmp/test_astra_contrastive_full_dose_run_20260913.py`
  SHA256 `a2e39fe41b4b55c210c4b12f9701c77205d36288ede49097d4a77b0b3ab2341b`
- This handoff is the only other persistent output; its hash is reported outside
  its own bytes. Temporary CPU fixtures are removed by the tests.

## Exact API / stages / budgets

CLI: `prepare`, `controller`, `worker`, `collect`. Python functions use those names;
`validate_spec`, `verify`, `validate_completed`, `encode_training`, `import_off`
are available for bounded independent CPU review. No original lifecycle is called.

Per learner seed (strict integer 0, 1 or 2), stages in this exact order:

1. `fit_plain`: fresh official base, fresh LoRA/optimizer; 112 epochs / 336 updates.
2. `readout_plain`: one new cold vLLM process, all four panels, 48 calls.
3. `fit_contrastive`: another fresh official base/LoRA/optimizer; same dose/order.
4. `readout_contrastive`: another new cold vLLM process, all panels, 48 calls.

Per pair: 2 fits, 672 updates, 2688 presentations, 96 new calls. Across three
separate roots/seeds: exactly 6 fits, 2016 updates, 288 calls. No new OFF calls.
The single-root runner does not schedule/aggregate the three seeds; Main must
bind exactly one root for each seed, not reuse/select seeds or silently add roots.

LR 1e-4, batch 4, accumulation 1, rank 8, alpha 16, dropout .05, AdamW, unpacked,
original target modules and other TrainConfig defaults. Only explicit learner
seed and epochs differ from the original recipe. Inference ENGINE/PARAMS remain
the original helper objects unchanged (sampling/engine seed 0, max output 192).
No `init_adapter` argument is passed to the frozen trainer; manifests containing
`warm_start` are rejected. All four worker PIDs must differ and be absent at close.

Controller hard cap 7200s with 40s owned-cleanup reserve. Per-stage maxima:
fit 2700s, readout 800s, capped again by remaining controller time minus cleanup.
The 7000s stage maxima do not promise that all maxima plus queries fit: remaining
budget wins. Collection has a separate 180s total envelope including initial
verification. A six-hour lease-finish margin is enforced, plus the remaining
controller/collection envelope at launch. Timing is UNPROFILED, not feasibility
evidence. No retry, recovery launch, extra dose, foreign kills or promotion.

## Closed spec contract

Spec bytes MUST equal runner `encoded(spec)`: Python
`(json.dumps(spec, sort_keys=True, ensure_ascii=False, allow_nan=False)+'\n').encode()`.
Pretty-printed JSON is rejected before creating a root. No extra spec keys.

Required fields:

- `runner_sha256`: new runner pin above.
- `original`, `material`, `encoder`, `reflection`, `public`, `protocol`,
  `original_protocol`, `binding`, `historical_archive`, `reservation`: each exactly
  `{"path": ABSOLUTE_PATH, "sha256": LOWERCASE_SHA256}`.
- `source`: exact frozen four-file source directory; `source_files`: its exact
  filename-to-SHA256 map, as in original plan/spec. `model`: original official
  base snapshot path bound by the public receipt. No new descendants or models.
- `learner_seed`: integer 0/1/2, never bool/string/float.
- `node`: exactly `node2`; `expected_hostname`: actual Main-checked hostname;
  `expected_boot_id`: actual boot UUID; `gpu_index`: integer 0/1/2;
  `gpu_uuid`: corresponding full physical GPU UUID; `lease_end`: finite epoch time.

Reservation receipt contents must be EXACTLY:

```json
{"scope":"authored_contrastive_full_dose_DEV_three_seeds_v1","root":"ABSOLUTE_FRESH_ROOT","node":"node2","expected_hostname":"MAIN_CHECKED_HOSTNAME","expected_boot_id":"MAIN_CHECKED_BOOT_UUID","gpu_index":0,"gpu_uuid":"MAIN_CHECKED_FULL_GPU_UUID","lease_end":0,"learner_seed":0}
```

Replace placeholders and lease with real values; GPU index and learner seed are
independent fields, not inferred from each other. Every reservation value must
match the spec, and root must match its resolved new output path. This receipt
binds Main's reservation; it is NOT a global reservation allocator. Main must
still perform fresh queue/lease/owner/all-process checks and prevent competing
controllers. The unchanged public helper checks all-process GPU XML vacancy and
UUID/index before each stage and after owned cleanup; no NVML exception changes.

## Frozen dependency and historical pins

`original` MUST stay at `/tmp/astra_contrastive_perception_run_20260913.py`:
`aea1b5d84d6d79efa7dbdd43ab8e93bf0483fd4383531eae363cdbb4b7583d55`.
It supplies utilities, Native, source_api and adapter checks only; none of its
globals, fit functions, prepare/controller/collect/verify functions are modified
or called. New epoch/config/lifecycle logic is explicit in the new runner.

Other original helpers, copied without edits to Main's bound absolute paths:

- material `/tmp/astra_contrastive_perception_material_20260913.py`:
  `b3c7fa549fdade0866da51131f64fe067ad7cd3ce36187f67e4c56ac7fbe5c1d`
- encoder `/tmp/astra_perception_fit_run_20260913.py`:
  `f62da57d1a66cd287b72ac8ad8b8724601062813653a63d3dcd6cd8a3b69cd51`
- reflection `/tmp/astra_reflection_fit_run_20260913.py`:
  `0f79efa1f4e4da6a9d1ec245c09e665f7c2b7d8bce31f7e01fe01b00f95a72fc`
- public `/tmp/astra_birth_skill_probe_run_20260913.py`:
  `59874c678ce1b36feaa1969721c0dcc761b4fa05072a6231892269991201052c`
- binding `/tmp/astra_qwen_public_binding_receipt_20260913_attempt1.json`:
  `e87abf9c83845a32bb5df3828901dde1929e86a57fa0278158d4101b7df9a019`

New `protocol`: copy of
`research_notes/astra_memos/ASTRA_CONTRASTIVE_FULL_DOSE_2026-09-13.md`,
SHA `e777b5be15e2a1cab447de3e72fb013bfac2a20a3d12d81574f95880ca60b0e6`.
`original_protocol`: unchanged original contrastive protocol,
SHA `cc7e92d8aa3999c2ee619893cf830f2687347a39175149708886c1bf0d820ef5`.

Original source is locally `/tmp/astra_contrastive_source_20260913_attempt1`:

- `organism_v6/__init__.py`: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- `organism_v6/birth_skill_corpus.py`: `078ceba07141b5f6fb2159a12e21f1eccc0901ba9f51f52d1793d988927812f6`
- `organism_v6/rulegame_parenting_diagnostic.py`: `e6055da48b2c6fa1bd294c9d991e07f32f05dc6630fe8973373977bdfe977526`
- `organism_v6/train_adapter_v3.py`: `7bbf165fcb4b8ae3a1180328bcd19f57382c30516daddc95fd61e8a2c749fad7`

Historical archive is locally
`gpu_artifacts_local/contrastive_perception_20260913/contrastive_perception_20260913_attempt1_archive.tar`,
SHA `c12c3ff8e7cd0a9261aa5118d85f5a93d5318245afd05d0d4ff3cacc96401f7d`.
Main must make this exact archive available on node2 at the spec's bound path.
Archive members are read in memory, never extracted into/reopened as old roots.

Historical plan: `f0060eb8d37a61aa1d9b25ba6798f19045a8a66cca715755f5e948d216702ec4`;
completion: `9574f5b7dfe6df3bbd9b74a3afb46fd5fc1c5d4ae0b1e11f249f9076bf0c38ff`;
scores: `7af6484ebb72abc81d2f17d29e7ca15786599afba0b22e88139a80403f3412d0`.
The importer verifies archive/member pins, completion/collection joins, native
prompt/row/token/template/base identity, OFF-null routes and 48 response records.
It checks selected OFF records against original closed/completion file hashes.
It does not revalidate every historical trained-adapter stage or recollect it.

## Main-only execution contract (not executed here)

After fresh allocation checks and copying/pinning inputs, create each canonical
spec and root-bound reservation externally, then use the same native Python:

```sh
python3 -B /tmp/astra_contrastive_full_dose_run_20260913.py prepare --root "$ROOT" --spec-path "$SPEC" --spec-sha256 "$SPEC_SHA" --allow-native
setsid python3 -B /tmp/astra_contrastive_full_dose_run_20260913.py controller --root "$ROOT" --plan-sha256 "$PLAN_SHA" --allow-gpu
python3 -B /tmp/astra_contrastive_full_dose_run_20260913.py collect --root "$ROOT" --plan-sha256 "$PLAN_SHA" --completion-sha256 "$COMPLETION_SHA" --out "$FRESH_COLLECTION"
```

Controller must own its process group; Main owns its external logs/deadline and
must let it exit before collection. Controller clears CUDA visibility, then
passes only its bound full UUID to each fresh worker. No helper launcher needed.
Prepare performs native-tokenizer CPU replay but no model load. Native base and
environment must match original binding; interpreter/runtime pins are rechecked.
Do not run these example commands as sidecar CPU tests.

Prepared outputs: `plan.json`, `prepare_started.json`, exact original
`material.json` (SHA `7f9045242e98dc05b85f814574a1eb87cacebf463af88dcca60729c4aa5ebd66`),
`train_plain.json`, `train_contrastive.json`, `calls.json`, `costs.json`,
`historical_OFF.json`. Frozen material's old recipe annotations remain unchanged;
the new plan/config/train receipts explicitly govern actual full-dose execution.
Both arms keep identical target+EOS tokens and epoch row order; native fit replay
must exactly reproduce full assistant masks, no truncation/split/padding loss.

Capture outputs: `run/fit_ARM/{adapter,fit.json,...}` and
`run/readout_ARM/{identity.json,PANEL__NN.request.json,PANEL__NN.response.json,closed.json,...}`,
plus stage launch/start/release receipts, controller receipt and completion.
Failures preserve evidence and never become scorable completions. Collection
claims `ROOT.collection_claim.json` exclusively; outputs `scores.json` and
`collection.json` in a fresh external directory. No original collector call.

## Tests and limits

`python3 -B /tmp/test_astra_contrastive_full_dose_run_20260913.py`
— **32 PASS, 11.567s**. Actual frozen pure encoder/trainer scheduling and scorer,
toy tokenizer, mocked fits/captures/processes; actual archived OFF joins replayed
without model calls. Covers seeds, target/EOS/padding masks, truncation, dose,
source/protocol/import pins, fit manifest/warm-start rejection, changed responses,
fresh roots/processes, busy GPU refusal, timeout cleanup, controller stop/no retry,
collection deadline/once/absence, exact scorer and per-item PLAIN canary harm.
CLI `--help` / `prepare --help`, AST and trailing-whitespace checks also passed.

All panels are exploratory exposed DEV. D1/D2 share 12 situations; C-record is
exposed; negate-earlier remains a perfect shortcut. Historical OFF is not a
fresh contemporary control. Reports retain original strict screen and every
field/syntax/source error, paired wins/losses, and separate individual OFF-correct
canary losses for BOTH arms. `automatic_pass=False`, `scientific_pass=None`.
Token/context/padding/wall-time costs are reported, not claimed equal. Six fresh
fits here do not identify broad discrimination, source attention, child learning,
or a guaranteed dose fix. No native feasibility or launch approval is claimed.
