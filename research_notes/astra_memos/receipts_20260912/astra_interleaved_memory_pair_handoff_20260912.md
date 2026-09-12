# Interleaved seed0 pair + collector — EDIT-STOP — 2026-09-12

Only three owned files: `/tmp/astra_interleaved_memory_pair_20260912.py`, `/tmp/test_astra_interleaved_memory_pair_20260912.py`, this handoff. Material/trainer/readout modules and previous runners/roots untouched. No native/GPU/model/network execution. One permitted read-only Git command resolved `22b7e528` to `22b7e528f6f62358981ed2264d30ee7242926160`; no other Git operations. Author also authored material/previous runner: custody validation is not independent scientific review.

**28 CPU tests PASS, zero skips (8.170s final run); CLI help PASS.** Includes synthetic224 raw calls through full collection/archive validation, native identity/tokenizer/fit-state operations stubbed; no model dependency. Four initial test errors were missing synthetic adapter identity fixtures, repaired in tests without weakening production identity checks. Test source-rejection fixture also works from the correct immutable native CWD.

## Pins and unchanged dependencies

- Source CWD/name must be exactly `22b7e528f6f62358981ed2264d30ee7242926160`. Main reports archive SHA `81aac7fe8c32bb9be28387a1a802102d1016c8a4bf51fea6a84ea922da1b7924` and55 native material tests PASS. This sidecar hashes loaded source files; it does not independently authenticate the source archive or model origin.
- `/tmp/astra_varied_memory_pair_20260912.py`: `b58f65cd482bbd2d762edc030c7967a1ecd004829cf8271c74c15d3ca54bc8c7` — reuse config, fit command validation, manifest/state checks, capture receipts ONLY; no old prepare/run/verify calls.
- `/tmp/astra_memory_only_20260912.py`: `ac7a110bc74724fc592407ced854ad162da275d3de9d9eeeb40c19788416afdb` — original-parent pins, templates, freshness and successful-supervision helpers.
- `/tmp/astra_fading_sentinel_20260912.py`: `7b0686de7b66fcad27a665c0b30054a893af3ee33d053c26fae903fc1ed8af20` — existing dependency of memory helper.
- `/tmp/astra_collect_memory_only_20260912.py`: `d2152c179ca9a6b9801933a480ed62cd203018868a52034e13676963787579eb` — safe metadata I/O/tar validation only. Its old-run commands are not invoked.

Runner SHA256: `d100cb58296499c7cd6489d20e96528898f2e48b698147a97dae99fa38946bbe`.
Tests SHA256: `a87b76a9c49f2e5ed2159bf6b33da8663371a0e9ee294a3c81f362a4dfed494f`.

## Main CPU preparation (not executed here)

Use the native venv **without resolving its executable symlink**. Set `ORIGINAL` to the actual original seed0 teaching root, not a replay descendant. The original plan, fit and readout hashes must pass the existing seed0 pins. Choose a new diagnostic parent directory and create that parent only; **both MATERIAL and ROOT must be absent**. Never reuse old varied protocol paths.

```bash
SOURCE="$HOME/astra_sources/22b7e528f6f62358981ed2264d30ee7242926160"
PY="$HOME/v2/venv/bin/python"
SCRIPT=/tmp/astra_interleaved_memory_pair_20260912.py
# Main sets ORIGINAL, MATERIAL, ROOT, DEVICE, DEADLINE_UNIX, LEASE_END_UNIX.
# MATERIAL and ROOT must be fresh siblings under an existing NEW parent directory.
cd "$SOURCE"
PYTHONDONTWRITEBYTECODE=1 "$PY" -B /tmp/test_astra_interleaved_memory_pair_20260912.py -v

env -u CUDA_VISIBLE_DEVICES HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONDONTWRITEBYTECODE=1 \
  "$PY" -B - "$SOURCE" "$ORIGINAL" "$MATERIAL" <<'PY'
import importlib.util, pathlib, sys
spec = importlib.util.spec_from_file_location('interleaved_prepare', '/tmp/astra_interleaved_memory_pair_20260912.py')
driver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(driver)
driver.bind(sys.argv[1])
original = pathlib.Path(sys.argv[2]).resolve(strict=True)
driver.require(driver.base.digest(original/'plan.json') == driver.memory.PINS['0'][0], 'not original seed0')
plan = driver.old.read_plan(original)
driver.require(driver.base.model_hashes(plan['model']) == plan['model_files'], 'base changed')
tokenizer = driver.base.native_tokenizer(plan['model'])
receipt = driver.material.prepare(sys.argv[3], original/'teach.json', tokenizer)
print(receipt['status'], receipt['token_totals'])
PY

env -u CUDA_VISIBLE_DEVICES HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONDONTWRITEBYTECODE=1 \
  "$PY" -B "$SCRIPT" prepare --source-root "$SOURCE" --runroot "$ROOT" \
  --materialroot "$MATERIAL" --device "$DEVICE" --deadline "$DEADLINE_UNIX" --lease-end "$LEASE_END_UNIX"
"$PY" -B "$SCRIPT" verify --source-root "$SOURCE" --runroot "$ROOT"
```

The sidecar's `prepare` **requires existing audited material and never recreates it**. It independently reruns the injected actual native tokenizer audit, compares complete exported corpora/receipts, validates all30 V3 epoch schedules, compares original dev48 inputs, binds lexical prefixes to material, and records padded costs before creating the plan. Model path comes from the pinned original plan. Exact original native80 teach bytes remain required. Plan seal: `plan.json`, `plan.sha256.json`.

Preparation exports/freeze fields: source commit/root/hashes (including helper/checker hashes), lexical/dev/exact templates with native prompts+IDs, actual model inventory, original parent inventory/full state/provenance, material inventory, config, fixed accounting, `python=os.path.abspath(sys.executable)`, native CPU audit+`padded_costs`, deadlines, progression declaration. Origin remains `UNRESOLVED_LOCAL_HASHES_ONLY` / unauthenticated.

## Main launch contract

After full vacancy/UUID checks, Main's launcher reserves one GPU continuously across fits, readouts, CPU gaps and cleanup; set initial `CUDA_VISIBLE_DEVICES`. Only Main launches:

```bash
CUDA_VISIBLE_DEVICES="$DEVICE" "$PY" -B "$SCRIPT" run --source-root "$SOURCE" --runroot "$ROOT" --allow-gpu
```

Record `ROOT/launch/launch.json` and `ROOT/launch/gpu.xml` before collection. Required JSON fields: `plan_sha256`, `script_sha256`, `root`, `source`, `device`, integer `pid`, ISO8601 `started_utc`, `gpu` with actual `gpu_uuid`, `controller_bound_seconds:1800`, `external_collection_margin_seconds:300`, `generation_calls:224`, and `command` **exactly the inner Python command shown**, using the absolute venv path, not its resolved system-Python target. Additional launcher fields are allowed. The launch XML must contain that same single GPU UUID. Main owns launching, watchdog/logging and ledger; `run` does not perform full `check_free` on its own reservation.

Seed0 only: SINGLE_VIEW then FOUR_VIEW, each independently from original80-step teaching adapter. One adapter, LR3e-4/r8/alpha16/dropout.05, fresh AdamW/seed0,10epochs/batch4/accum1,320 new/400 cumulative finite updates. No packing/drop/truncation. Existing manifest validator proves loaded original state, immutable parent, base frozen and fresh optimizer. Targets/exposure unchanged; mixed batches have **1280/10000=12.8% memory target-token mass**, not equal task weighting. Actual padded costs are saved; no input-compute matching or causal old/new comparison claimed.

Each arm captures dev48, original training-prefix exact16, new lexical48, in that order. All six panels / **224 calls** must be captured before any reducer. No original confirmation/OFF/HF calls. Lexical capture uses existing NativeBackend/readout.capture, one exact prompt-only call/case, temperature0, seed20260912, max64tokens, native raw requests/responses/input+output IDs; fresh supervised process with parent-loss watcher and owned backend cleanup. Memory scoring reuses strict `score_memory`; each lexical family is reported separately,16 facts shared across48 cues. No new outputs were used to choose cues.

Main alone inspects outcomes after both technical COMPLETE: FOUR dev/exact memory≥15/16 each, habit≥30/32, ACT≥31/32, **each lexical family≥15/16** permits later seeds1/2, regardless SINGLE scores. Wrapper never evaluates that gate, starts later seeds, tunes material, retries, or resumes. Raw artifacts/logs necessarily exist during capture: no access-control claim; Main must not inspect outcomes early.

## Bounds / status / custody

Controller1800s includes startup/verification/CPU/reductions; alarm at effective end−140 for cleanup. Each native worker≤600s with existing occupancy/supervise checks. No new worker/reduction with≤150s remaining. Eight workers expected (two fits + six captures). Require full1800s window within declared deadline, and end+300s custody margin before real lease−10. A six-hour real lease does not enlarge the1800s cap. `reservation.json` records actual real lease, effective deadline, monotonic start and external custody deadline separately. Partial/error/missing output is failure, never zero. Main should retain an independent launch watchdog for blocking native-library/process failures; reported COMPLETE additionally requires end≤effective deadline and full release.

```bash
"$PY" -B "$SCRIPT" status --source-root "$SOURCE" --runroot "$ROOT"
# Only after PID absent AND terminal; unset reservation environment for full vacancy check.
env -u CUDA_VISIBLE_DEVICES PYTHONDONTWRITEBYTECODE=1 \
  timeout --signal=KILL 300s "$PY" -B "$SCRIPT" collect --source-root "$SOURCE" --runroot "$ROOT" \
  --archive /tmp/astra_interleaved_memory_root0_terminal_20260912.tgz
```

Status is file-presence markers only, no outcomes. Collect never runs a fit, generation, tokenizer or reducer. It audits current source/material/base/parent/children, full raw requests/IDs/hash receipts, existing reductions, eight-worker command/time/order/cost/release accounting; full `check_free` must match launch UUID/XML. Current input-stat inventories detect changes through packaging. Existing decoder-audit receipts are bound, not rerun. Requires accounted cleanup even for partial terminal; unaccounted failures need manual reconciliation.

Exclusive outputs: `ROOT/run/main_release.json`, `main_release.xml`, external `.tgz`, adjacent `.tgz.validation.json`. Metadata only; weights stay native. No overwrite, retry, automatic orphan repair or idempotent recollection of completed capsules; use the saved validation receipt. Every custody call has a300s alarm (external `timeout` also recommended). Late observation records original effective+300 deadline, explicit overrun and `budget_extended=False`; late evidence collection is not a retroactive budget extension. Worker/controller/full-launch windows overlap, do not add them.

Limitations: CPU fixtures cannot establish native performance, runtime completion, origin, or scientific success. Original local source/parent pins are strict; no arbitrary-source bypass. Native re-audit/prepare and Main launch review remain outstanding. Source archive SHA is Main-provided provenance, not independently rehashed here. Original parent/current child hash/state verification is intentionally reused and may consume CPU margin. No modification of the live parent-record pair or developing readout bridge.

**EDIT-STOP.**
