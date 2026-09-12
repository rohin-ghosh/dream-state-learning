# Process-v2 readout collector — EDITSTOP, September 12, 2026

## Amended EDITSTOP — actual launch schema repair

**25 CPU mock tests PASS in 91.896s.** This amendment supersedes the prospective launcher assumptions below. Only the three owned files changed; actual launcher, immutable receipt, driver, writer and helpers remain untouched. No native/GPU/SSH/network/Git or score inspection. Source-only launcher inspection plus local launch-receipt metadata inspection only. Main remains sole native operator.

- Launch `write_driver_sha256` is absent in the actual receipt and is now optional, never fabricated. If present it must match. CLI writer SHA remains mandatory and must match the authoritative pinned readout plan and actual writer bytes; accepted_writes independently validates write provenance.
- Required launch `write_release_path` and `write_release_sha256` bind the **exact recorded absolute sibling collection validation.json**, not `WRITE_ROOT/run/main_release.json`. No fallback, receipt mutation, or reconstruction. Native finish checks regular/unaliased bounded file, exact hash, status `COLLECTED_PAIRED_WRITE`, full_release and aggregate_available true, and the matching write-plan SHA.
- Original release receipt bytes are preserved as `metadata/collection/write_release.json`; original path/hash are recorded in custody, with original-file rechecks around packing. Status stays blind and does not read that receipt body. An intermediate regression run exposed the inherited source-only inventory's rejection of JSON; repaired with metadata custody rather than changing the frozen helper.
- Regressions cover complete collection with no launch writer pin and the real sibling-release layout; conflicting optional/authoritative writer pins; missing path/hash, wrong hash/path/acceptance/plan; release mutation during packing; byte-identical release archive inclusion. All prior tests remain passing.

Actual inspected immutable local receipt `/tmp/astra_process_readout_launch_20260912.json` SHA `141560982f9da4f0fddf35295fb927c741b9a51589f7bbff6d4602cdd4fd2960`. Main must confirm native LAUNCH_ROOT/launch.json byte parity before using this pin. Actual launcher `/tmp/astra_launch_rulegame_process_readout_20260912.py` SHA `91fea8184e5d2e24825d6df7adf57dbb90a80889be7578e2dfb9e042d8da9989`.

Actual CLI values (same CLI below; no new flags):
```text
READOUT_ROOT=/localhome/local-rohing/astra_diagnostics/astra_rulegame_process_readout_v2_20260912_attempt1
READOUT_PLAN_SHA256=8b0f23858427d57b579688bcc06dbae4768b9bbbc2198660d1f1dbe31f092323
PROCESS_WRITE_PLAN_SHA256=67f2b89a769dd1f21e2ae3f048aa2d3743a5761f0574dcca3f47e1a8c51b0f44
PROCESS_WRITE_DRIVER_SHA256=a73dd6074fdd099cea19f46cfed94bf31f22b2ce02b8741ac2f224413ee514d9
READOUT_LAUNCH_ROOT=${READOUT_ROOT}_launch
READOUT_LAUNCHER=/tmp/astra_launch_rulegame_process_readout_20260912.py
PROCESS_SOURCE=/localhome/local-rohing/astra_sources/4c3064c1c3eef068951e9c3b2ca46630754564e7
NATIVE_PYTHON=/localhome/local-rohing/v2/venv/bin/python
```
Launch receipt PID255725, start2026-09-12T22:58:48.818483+00:00. Recorded release `/localhome/local-rohing/astra_diagnostics/astra_rulegame_process_write_v2_20260912_attempt1_collection_attempt1/validation.json` SHA `fbc01b2979003948869cc25f5ae00ecae12a357681791706089658e11eed62db`. Its body was not inspected locally; validation remains a native finish obligation. Native CPU acceptance, tokenizer/provenance replay, release permission checks and completion within300s remain outstanding. No completed native collection is claimed.

## Frozen delivery

Only the assigned three sidecars were authored:

- `/tmp/astra_rulegame_process_readout_collect_20260912.py`
  SHA256 **303b1518da794832d6cc22609239be46b9f7587485efe21cbd706ff8827c1468**
- `/tmp/test_astra_rulegame_process_readout_collect_20260912.py`
  SHA256 **9bc8561df6b7a0338dc710b7405558cfec8ecbb2f43654db73694ff2834dd2b4**
- This handoff.

**22 CPU mock tests PASS in 84.365s.** No native tokenizer/model, GPU query/launch, SSH, network, Git, repository or adjacent file edits, actual paired-write/readout data inspection, or scientific outcome review. The live write PID248787 is not a readout identity and is never used as one. Main supplies the eventual readout root/plan/launch pins and executes native acceptance/collection.

## Main CLI (original prospective text; amendment above governs launch schema)

All run identities are explicit. No attempt/root/PID/plan is guessed. Supported process-readout driver bytes are SHA **46e3d0974cab9a3c35e732634a22c29ad25ccd670472dc5b1a57c344cb20af46**. The process writer was tested at **a73dd6074fdd099cea19f46cfed94bf31f22b2ce02b8741ac2f224413ee514d9**; its actual CLI pin must match the accepted readout plan, writer file, and launch receipt. The collector does not accept an old record-write lineage.

The future immutable `LAUNCH_ROOT/launch.json` must contain these fields:

```text
root, plan_sha256, pid, started_utc, driver_sha256, launcher_sha256,
source, device, gpu.gpu_uuid, write_plan_sha256, write_driver_sha256,
command = [native-python, -B, DRIVER, evaluate, --root, ROOT,
           --plan-sha256, READOUT_PLAN_SHA, --allow-gpu],
cells = [OFF, P_ON, A_ON], controller_seconds = 1800,
cleanup_reserve = 140, worker_cap_seconds = 600,
continuous_reservation = true
```

Launch root must be a distinct sibling of readout root, with matching vacant-device `gpu.xml`. The supplied launcher source hash is verified and the source archived, **never executed**. `phase` is not guessed or required. Optional fields, if present, must agree: `external_collection_margin_seconds=300`, `max_calls=96`, `max_generated_tokens=27600`, `adaptation_test=false`, and process `model_origin`/`conditioning`. If `write_release_sha256` is present, it binds exactly `WRITE_ROOT/run/main_release.json`; omit that optional field if Main's actual write-release layout is different, rather than pointing it at another file silently. Readout/write/source custody is independently checked regardless.

```bash
export SOURCE="${PROCESS_SOURCE:?exact source-root from readout/write plan}"
export READOUT_DRIVER=/tmp/astra_rulegame_process_readout_20260912.py
export READOUT_DRIVER_SHA=46e3d0974cab9a3c35e732634a22c29ad25ccd670472dc5b1a57c344cb20af46

ARGS=(
  --root "${READOUT_ROOT:?Main supplied readout root}"
  --plan-sha256 "${READOUT_PLAN_SHA256:?accepted readout plan hash}"
  --driver "$READOUT_DRIVER" --driver-sha256 "$READOUT_DRIVER_SHA"
  --write-driver /tmp/astra_rulegame_process_write_20260912.py
  --write-driver-sha256 "${PROCESS_WRITE_DRIVER_SHA256:?accepted writer hash}"
  --write-plan-sha256 "${PROCESS_WRITE_PLAN_SHA256:?accepted process-write plan hash}"
  --launch-root "${READOUT_LAUNCH_ROOT:?actual sibling launch directory}"
  --launch-sha256 "${READOUT_LAUNCH_SHA256:?exact launch.json bytes hash}"
  --launcher "${READOUT_LAUNCHER:?actual launcher source path}"
  --launcher-sha256 "${READOUT_LAUNCHER_SHA256:?exact launched source hash}"
)

env -u CUDA_VISIBLE_DEVICES PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1 \
  HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 ASTRA_SOURCE_ROOT="$SOURCE" PYTHONPATH="$SOURCE" \
  "${NATIVE_PYTHON:?exact native venv spelling}" -B \
  /tmp/astra_rulegame_process_readout_collect_20260912.py status "${ARGS[@]}"

# Only once status reports ready=true. OUT must not exist.
env -u CUDA_VISIBLE_DEVICES PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1 \
  HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 ASTRA_SOURCE_ROOT="$SOURCE" PYTHONPATH="$SOURCE" \
  "${NATIVE_PYTHON:?exact native venv spelling}" -B \
  /tmp/astra_rulegame_process_readout_collect_20260912.py finish "${ARGS[@]}" \
  --out "${COLLECTION_ROOT:?fresh sibling of READOUT_ROOT}"
```

Do not resolve the native venv interpreter symlink. `status` has no native dependency invocation or score-body read. `finish` performs CPU-native token reconstruction and release queries but no model backend/fit/generation. There is no `--allow-gpu`, automatic waiting, retry, overwrite, or resume. All acquisition/readout/write roots remain untouched; release receipts live only in the fresh collection output, **not** `run/main_release.json`.

## Blind terminal barrier and exact schema

Status reads only pinned launch metadata, process receipts and terminal/cell marker existence. It checks the launch controller plus **OFF/P_ON/A_ON** worker PID, PGID and session membership against a full `/proc/*/stat` snapshot. Exactly one terminal marker (`result.json` XOR `failure.json`) and all owned scopes absent are necessary before any score body is opened. Duplicate/reused worker/controller PID, unexpected process receipt, surviving descendant/session, unreadable process inspection, missing or ambiguous terminal fails closed. No foreign process is killed. A failed terminal can have later cells unstarted; after all owned scopes stop, those cells stay missing/null, not imputed or replaced.

The collector uses the actual process readout's `checked_plan`, `accepted_writes(native=True)`, `audit_cell` and `process_metrics`. It does not assume acquisition score vectors/24 requests/48 forwards or old readout receipt fields. The source returns `process_metrics`; only the verified complete collector summary additionally groups these as `descriptive_event_metrics`.

The raw replay validates exact source-generated prompts, seeds, roles and interaction_v3 settings; native prompt/output token rendering and output caps; intended OFF/no-adapter and P_ON/A_ON adapter headers; fresh worker spec/nonce/argv/parent identity; source/model/adapter inventories and sealed captures; native audit/cleanup; and the stored per-cell provenance/terminal receipts. No model is rerun: RuleGame/call/event replay is deterministic CPU reconstruction using recorded responses. No target generation, exporter, trainer, or old collector entrypoint is invoked.

Both process writes must remain the actual completed fresh-base pair, with original fixed candidate/Main review/material masks/EOS/token/loss/exposure receipts and process-v2 source pins. Native material custody is rechecked in the CPU controller. It remains **context-distilled complete own raw wake training**, not raw RECORD objectives, clean lineage, G5/H2 or model-origin authentication. No teacher or audit context is sent to a model; there are no model calls at all during collection.

## Science and cost reduction

- Exactly four existing development tasks, rules2–5, **24 fixed quiz items per cell**, invalid/absent quiz zero. Quiz contrasts P−OFF, A−OFF, P−A are recomputed and checked against the terminal. No valid-only denominator or confirmation/task selection.
- Pre-TRY valid predicted probes, correct/absent/ambiguous predictions, raw PREDICT wake emissions, TRY/distinct/repeated triples, invalid actions and actual/allotted record faithfulness are recomputed from the unchanged event/call replay. Zero observed denominators remain null; fixed12 opportunities remain visible. Missing tasks/calls cannot be replaced by stored summaries.
- CHILD_BOOT already requests PREDICT: these are emission/adherence metrics, **not unprompted spontaneity**. Probe diversity is not information gain. Record faithfulness is distinct from executed prediction correctness and from acquisition.
- Actual requests/input tokens/output tokens/requested output ceilings and generation seconds are reduced from raw receipts, compared with usage and native call counts. Caps:20 wake+12 record per cell, **96 calls /27600 requested generation-token ceiling** overall; no requirement to consume all calls. All native call clocks are sequential, <=120s and inside the supervised worker window; load<=180s, execution timeout<=600s, inherited cleanup receipt<=timeout+140s. Workers must be distinct and sequential, and a successful controller remains <=1800s inclusive with the original deadline/lease cutoff.
- A science aggregate and total costs are exposed only after a complete three-cell raw/native audit **and** full release. Failure, mismatch or incomplete cells produce `aggregate=null`, `totals=null`; individually verified rows/observed worker durations remain diagnostic. Raw archived terminal files may contain a claimed summary; only the collector audit marks it verified.

## Full release, archive and helper constraints

Reuse is limited to immutable safe I/O, bounded text inventory, USTAR/hash validation, and release helpers from the already validated acquisition collector:

```text
/tmp/astra_rulegame_record_acquisition_collect_20260912.py
422c2fd2efcc2e8c315d6082c05a803353ee8b67f0b31e23eab19fe0119ae951
/tmp/astra_collect_memory_only_20260912.py
d2152c179ca9a6b9801933a480ed62cd203018868a52034e13676963787579eb
SOURCE/gpu/astra_mini_sudoku_diagnostic.py
a586b03bdb9c52f1061aa1e477ae983cc9d45ec0a2cd440642851fd8df8b609f
```

None of those experiment-specific collection entrypoints, acquisition data layouts or hardcoded launcher identities are used. The bootstrap rejects changed/symlink/hardlinked/special/oversized helper sources before executing their exact pinned bytes. Keep these helper files available on the native host; they are copied into the source portion of the final capsule with the actual driver/writer/launcher pins and directly pinned source dependencies.

Full release checks selected-device complete NVIDIA XML/UUID/vacancy, same-user `/proc` GPU reservations, and `~/queue/{pending,running}/*.job`, bracketed by own-session absence checks. Unset `CUDA_VISIBLE_DEVICES`. The inherited helper includes node-specific known system-service PID/command exceptions and an SSH-ancestor exception; unfamiliar inaccessible processes/reservations/queues fail closed, never get killed. This is a point-in-time selected-device release observation, not all-GPU vacancy or future-reservation control. A release failure preserves a partial capsule without science aggregate.

Metadata-only archive limits remain <=32MiB/file, <=256MiB total, <=2048 scanned entries/archive files; allowlisted UTF-8 text only, no symlinks/hardlinks/special files, exclusive0700 directory/0600 files. Weight/checkpoint/bytecode suffixes are excluded and listed; unknown file types, credential filenames, known credential JSON keys/patterns or invalid text fail without redaction/string surgery. Known-pattern checks are **not universal secret detection**; no environment dump is collected. Original weights/full external formation/write trees/unrelated logs remain at their source. All permitted root+launch metadata, collection receipts and pinned direct sources are preserved verbatim, including failed captures.

Output: `started.json`, `audit.json`, `release.json`, optional successful `release.xml`, `custody.json`, `metadata.tgz`, and final `validation.json`. Fatal pin/safety/expiry failure leaves `failure.json` and partial artifacts but **no validation marker**. `COLLECTED_PARTIAL_NO_AGGREGATE` is diagnostic custody, not science/full-release acceptance. Member/path/type/content hashes, complete archive hash, unchanged metadata inventories and driver/write/source lineage are verified around packing; archive extraction is never performed. No retries or overwrites.

A non-swallowable300s external alarm includes status, replay/native token verification, resource query, packing and rechecks. Reports separate controller, observed worker, launch-to-observed-release, and collection durations. Generation/load/cleanup/controller/full-release/collection intervals are nested or overlapping: **never add them**. Native hashing/reconstruction speed is not promised; exceeding the fixed margin preserves partial evidence.

## CPU tests and remaining Main acceptance

```bash
PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
CUDA_VISIBLE_DEVICES='' ASTRA_SOURCE_ROOT=/data/home/rohing/dream-state \
python3 -B -m unittest discover -s /tmp \
  -p test_astra_rulegame_process_readout_collect_20260912.py -v
```

22 tests cover complete process-specific raw/native-mock metric replay and costs/archive; no backend/fit/export execution; blind session/terminal barriers; partial-middle failure/null aggregates; invalid-zero fixed24; forged predictions/faithfulness/contrasts; resealed native IDs; parent spec/wrong adapter; explicit launch/write pins; actual saved-adapter mutation; resource refusal without kills; controller/worker/call bounds; metadata/archive mutation; expiry/timer restoration; pinned-helper integrity; weight/credential/unknown-file rejection; links/FIFO/size limits; safe archive paths/types/hashes/exclusive creation; and full-release UUID/unmasked requirement.

Native tests reuse the unchanged process-readout and process-write test fixtures; set `ASTRA_SOURCE_ROOT` to Main's actual immutable process source tree (announced4c3064c1…; full path comes from the plan). Remaining checks are the eventual readout plan/launcher schema/pins, native tokenizer and all fit/source inventories, inherited resource/process permissions, archive bounds and completion inside300s. No readout preparation, launch, result inspection or scientific review was performed by this agent. **EDITSTOP — Main sole native operator.**
