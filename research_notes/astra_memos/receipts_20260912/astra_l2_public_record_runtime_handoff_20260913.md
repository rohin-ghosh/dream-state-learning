# L2 public-record runtime handoff — EDITSTOP

Date: 2026-09-13. Bounded PROMOTE/SHADOW DEV implementation, not scientific
qualification, final-C11 expansion, or native launch acceptance. Main owns
integration, source staging, acceptance, launcher and all native operations.

## Owned paths and final SHA256

- `gpu/astra_l2_public_record_dev.py`
  `213c2a2f508815eef752c72424f5dca64b76c9edb963f7ed6f68d5522c18853e`
- `tests/test_astra_l2_public_record_dev.py`
  `d2ebe1e3a37c7ad7ee42e07aab583494d86819be7dfa7fd7cac25b392baed3f2`
- This handoff: `/tmp/astra_l2_public_record_runtime_handoff_20260913.md`.
  Its SHA256 is returned separately, avoiding a self-referential hash.

No other project files were edited. Curie's final core was read and its supplied
SHA checked before CPU test import:
`0bb33988f003a0111e14cdfb53b3dc86a695e8e20656c90e71cfadb5ad28d352`.
Its unchanged 28-test suite passed. Runtime does not silently select a working
core: Main must supply final source, helper, protocol and model-receipt pins.
No direct teammate messaging capability was available; alignment uses Main's
final handoff and CPU exercise of its actual wire/state API.

## Stable CLI and launcher contract

Runtime schema: `astra_l2_public_record_runtime_v1`.
Core schema: `l2_public_record_dev_v0`, wire version 1.
Use a Linux interpreter with the accepted native dependencies installed. No
dependency installation, model/tokenizer load, GPU action, native job, process
launch/kill, network request or Git operation was performed by this sidecar.
Subprocess lifecycle tests mocked `Popen`, GPU queries and cleanup.

Main's JSON specification has exactly these fields (placeholders are deliberate):

```json
{
  "schema": "astra_l2_public_record_runtime_v1",
  "source": "/absolute/resolved/fresh_source",
  "source_files": {
    "organism_v6/__init__.py": "MAIN_FINAL_SHA256",
    "organism_v6/l2_public_record_dev.py": "0bb33988f003a0111e14cdfb53b3dc86a695e8e20656c90e71cfadb5ad28d352",
    "organism_v6/train_adapter_v3.py": "MAIN_FINAL_UNCHANGED_TRAINER_SHA256",
    "gpu/astra_l2_public_record_dev.py": "213c2a2f508815eef752c72424f5dca64b76c9edb963f7ed6f68d5522c18853e"
  },
  "core_schema": "l2_public_record_dev_v0",
  "helpers": {
    "reflection": {"path": "/absolute/pinned/astra_reflection_fit_run_20260913.py", "sha256": "MAIN_FINAL_SHA256"},
    "public": {"path": "/absolute/pinned/astra_birth_skill_probe_run_20260913.py", "sha256": "MAIN_FINAL_SHA256"}
  },
  "model": "/absolute/resolved/official_qwen_model",
  "model_binding": {"path": "/absolute/model_only_public_binding.json", "sha256": "MAIN_FINAL_SHA256"},
  "protocol": {"path": "/absolute/ASTRA_L2_PUBLIC_RECORD_PROTOCOL_2026-09-13.md", "sha256": "MAIN_FINAL_SHA256"},
  "gpu_uuid": "GPU-MAIN-EXACT-UUID",
  "gpu_index": 3,
  "lease_end": 0
}
```

`lease_end` is a real finite Unix timestamp, not the example zero. The source
directory must contain exactly the four listed files: no `.git`, extra files,
bytecode, links or hardlinks. Keep tests in a separate CPU acceptance tree; do
not add them to this four-file native snapshot. Root, source and model must be
disjoint. Paths must have no symlink components; resolve aliases before writing
the spec. Main can stage the two accepted helpers outside the source tree and
pin those copied bytes. The model-only receipt must match the model path and
official 14-file public-revision map accepted by the public helper. No historical
receipt/origin labels are rewritten and no clean ancestry is inferred.

Commands for Main, NOT executed here (shell variables must be filled by Main):

```sh
"$PYTHON" -B "$SOURCE/gpu/astra_l2_public_record_dev.py" prepare \
  --spec "$SPEC" --spec-sha256 "$SPEC_SHA256" --root "$ROOT" --allow-native

"$PYTHON" -B "$SOURCE/gpu/astra_l2_public_record_dev.py" controller \
  --root "$ROOT" --plan-sha256 "$PLAN_SHA256" --allow-gpu

"$PYTHON" -B "$SOURCE/gpu/astra_l2_public_record_dev.py" collect \
  --root "$ROOT" --plan-sha256 "$PLAN_SHA256" --output "$COLLECTION_OUTSIDE_ROOT"
```

Preparation emits `{root, plan_sha256, schema}`. It uses the local native
tokenizer on CPU and rehashes the local model, never loading a model or querying
a GPU. Retain the returned plan pin. Controller calls the pinned snapshot script
in fresh owned process groups and supplies `CUDA_VISIBLE_DEVICES=spec.gpu_uuid`.
Worker CLI is internal: `worker --root ... --plan-sha256 ... --stage STAGE
--deadline UNIX_SECONDS --allow-gpu`; Main does not need a stage shell driver.
There is no retry/resume path. **Launcher stdout/stderr and collection output
must be outside ROOT**; after sealing, any added/changed file invalidates custody.
The controller prints a status string; a preserved scientific shortage or
runtime-abort return is not a successful complete loop merely because a shell
exit code is zero. Read the status and collect the capsule before classifying it.

## Sequence, counters and visibility

Fixed ordered stages:
`baseline`, `wake1`, `fit1`, `report1_PROMOTE`, `report1_SHADOW`,
`wake2_PROMOTE`, `wake2_SHADOW`, `fit2_PROMOTE`, `fit2_SHADOW`,
`report2_PROMOTE`, `report2_SHADOW`.

- Seeds are vocabulary2026091301, truth2026091302, learner0. Sixteen independent
  public keys, old8/new8, private 4/4-per-block truth; no MISBOUND runtime arm.
- Baseline is physically16 calls shared, not32 invented independent calls.
  Each wake makes8 action calls and at most8 record calls; each report is16.
  Full legal fixture:128calls, three physical fits,100updates.
- Raw response and action receipt are durably written **before** feedback.
  Exact illegal output creates an action-only `INVALID_ACTION` episode, without
  binary feedback or a record call. Ordinary malformed child records are retained
  for core rejection, not repaired. A normal `length` finish is retained/scored.
- Nonempty partial admitted corpora continue with actual rows/batches, no fillers.
  Empty formation stops as `FORMATION_SHORTAGE` with actual completed prefix;
  missing later reports are `null`, not zeros or a completed two-cycle result.
- Shared fit1 is physically performed once; both core states retain its same
  candidate SHA. Only PROMOTE requests an adapter. Each sleep2 fits its own
  branch's old+new corpus from fresh base and optimizer, never from fit1 weights.
  SHADOW trains its sleep2 candidate but never mounts either candidate.
- `dependency_states` reads only prior wake/fit artifacts, never baseline or
  reports. Generic system is identical. Action/readout prompts have no parent
  tape. Recording alone receives the fixed public process tape and current
  action/outcome. Private truth, report outputs, metadata and proofs are never
  added to model messages or supervised text.

## Exact fit/inference implementation

Unchanged `train_adapter_v3` implements rank8/alpha16/dropout.05/LR3e-5,
20epochs, batch8/accum1, BF16 AdamW, seed0, all seven projection targets,
no packing, max_len1024, no warm-start, SVD or frozen-A variant. Actual updates
are `20*ceil(admitted/8)`; sleep1<=20, each sleep2<=40.

`encode_training` binds each exported row to the authentic core corpus and
native chat prefix. Exactly the full ASCII child record bytes, including its
optional terminal LF, plus one tokenizer EOS are supervised. Generic context,
task/public law, padding and template-only whitespace tail receive -100 labels.
The serializer/encoder does not trim or recreate the target. It compares full
native template tokenization, v3 encoded IDs/labels,20 seeded epoch permutations,
every actual batch and padding mask. `overflow='truncate'` is the existing v3
API setting, **not permission to truncate**: lengths above1024, any drop or split,
or mask disagreement abort before fitting. Manifest dose/exposure/truncation,
finite losses and final LoRA-only trainability/finite trainable tensors are checked.

Each inference worker constructs a new vLLM engine with `enable_lora=True`,
max_lora_rank32, BF16, eager mode, no prefix caching, TP1, engine seed0.
All action, record and report calls use greedy seed0/max32/no retry. OFF/SHADOW
passes `lora_request=None`; PROMOTE passes the exact retained candidate path
through `LoRARequest`. Candidate inventories are checked before/after capture.
No mocked route echo is represented as proof of real adapter loading.

## Artifact/schema and replay contract

Preparation: `prepare_started.json`, `plan.json`, `world.json`, `calls.json`,
`model_binding.json`; preparation exceptions retain `prepare_failure.json`.
`plan.json` embeds the caller spec, fixed config/seeds/limits, interpreter and
model hashes, native environment/template and exact prepared-file pins.

Per-stage `run/STAGE/`: controller `launch.json`, `stdout.log`, `stderr.log`,
`release.json`; worker `started.json`, `CLOSED.json`, optional `failure.json`.
`CLOSED.files` hashes the exact `data/` inventory. Generation `data/` includes
`identity.json`, ordered `NN.request.json`, `NN.response.json`, exact wire receipt
files, invalid-action episode markers and `result.json`. Response fields include
native rendered prompt/tokens/system, exact UTF8 `raw_hex`, text/decoded text,
output/returned-input token IDs, finish/stop reason, monotonic times and request
route. Requests contain only slot/kind plus the explicit system/user messages.

Fit `data/`: core-wire `corpus.json`; nonempty fits additionally retain
`training.json` (source exports, full token/mask audits, epoch order/exposures),
`fit_intent.json`, and the untouched trainer `adapter/` output/manifests/DONE.
The candidate SHA is runtime `value_hash(candidate_files)`, a SHA256 over the
canonical newline-terminated sorted JSON path→file-SHA inventory, **not** the
weight-file hash alone. Both the inventory and aggregate are retained. The
frozen-base identity likewise hashes the model path→SHA map, not a candidate.

`result.json` always contains `stage,calls,fits,updates,status`. Wake results
carry `capture=core.to_data(CapturedBlock)`; readouts carry
`readouts=core.to_data(tuple[Receipt,...])`; fit results carry corpus/base/candidate
hashes, candidate inventory, admitted/rejected counts and finite/trainability
receipt. Snapshots use ONLY `core.to_data`/`core.from_data(expected_type=...)`,
then core receipt/capture/state validation; no pickle or canonical/asdict decoding.

Controller retains `controller_started.json`, write-once `terminal.json`,
`SEAL.json` and `FINALIZED.json`. Finalization overrun adds
`FINALIZATION_ABORT.json`, preserving original terminal evidence without relabeling.
Collection verifies the exact root inventory excluding those three witness files
and their hash bindings. Missing final witness is explicitly nonreportable.
Failed raw-stage roots receive custody/abort projection without requiring invalid
stages to pass scientific reconstruction. Missing/broken seal or corrupt JSON is
a collection integrity error, never invented completion; retain the capsule and
external logs for Main's review.

For complete/shortage roots, collection reconstructs raw actions/feedback/records,
state/routing and child corpora; re-encodes full training masks using only the
local tokenizer; checks trainer receipts/candidate bytes; then scores reports.
It returns old8/new8 correctness, legality/malformed/length counts, per-cycle
PROMOTE-minus-SHADOW descriptive contrasts, formation, per-stage call/token
exposure, actual fit costs and completed/incomplete stages. Endpoint core reducer
is used only for complete two-cycle pairs. `scientific_replay=true` means this
deterministic reconstruction ran, **not** scientific success or native
certification. `scientific_pass=null` and the core's `native_verified=false` are
preserved. No efficacy threshold or automatic promotion exists.

## Budget and failure handling

Controller clock starts at entry, before source/model/environment verification.
5400seconds includes40seconds reserved for owned-group cleanup; per-stage
600second fit/300second inference deadlines are clamped to remaining time.
Cleanup suspends the compute timer but remains bounded by the outer deadline.
The helper may signal only the newly owned worker group. GPU vacancy/UUID is
checked before launch and release afterward. Failed workers, wrong identities,
bad mounts, source drift, nonfinite state, truncation or deadline failures abort
without retry or artifact deletion. Final write lateness projects runtime abort.
Separate collection is capped at180seconds. Prepare/controller require at least
5400+180+21600seconds of remaining lease (adjusted for elapsed controller time):
the planned finish/collection must retain the six-hour lease margin.

## Exact CPU validation

Local Python3.12.3. Final command:

```sh
PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' python3 -B -m unittest \
  discover -s tests -p 'test*l2_public_record_dev.py' -v
```

**PASS89 tests in10.323seconds; zero failures/errors/skips**:61new runtime
fixtures plus28unchanged final core fixtures. Runtime tests use the actual final
core and pure v3 encoder with a fake tokenizer/backend/model and mocked process
operations; no native performance, tensor training, GPU loading, or learning
claim follows. Coverage includes exact newline/EOS masks and partial batches,
invalid action/record handling, partial formation/shortage, shared candidate and
branch-local cumulative fits, report exclusion, all caps, full raw/state/mask
replay, candidate/capture drift, extra/missing files, duplicate JSON, links,
worker identity, launch/timeout/release failures, clock placement, final-write
overrun and abort collection without invalid-stage replay.

Both assigned Python files also passed `ast.parse`; CLI root/prepare/controller/
collect `--help` returned successfully without native imports. Earlier60+28
individual runs passed9.901s/0.885s. Two command-entry mistakes were corrected:
`python` is not installed locally (used `python3`); a pattern containing an
accidental space discovered zero tests (not counted as a pass). The final89-test
command above is the relevant acceptance result.

## Remaining Main acceptance / limitations

No remaining core API blocker. Main must provide the other final hashes/paths,
stage the fresh snapshot and accepted helpers, rerun CPU acceptance, invoke CPU
native-tokenizer prepare, review its exact full-assistant masks, and validate the
actual trainer/vLLM/PEFT/helper contracts on the target environment before launch.
Final model trainability checks and real fresh-process GPU release are implemented
but only mocked locally. There is no claim that an engine's actual adapter load,
its output contract, native model/template boundary, or Linux GPU lifecycle has
passed here. No live science outcomes or later exploratory outputs selected any
runtime behavior. Main's thin shell launcher remains separate; the native kernels,
fit/capture workers, controller and replay are present, not delegated as missing
implementation.

EDITSTOP — no further edits to the two source/test files after these hashes.
