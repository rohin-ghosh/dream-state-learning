# Interleaved memory replication — CPU PASS / EDITSTOP

Owned files: `/tmp/astra_interleaved_memory_replication_20260912.py`, `/tmp/test_astra_interleaved_memory_replication_20260912.py`, this handoff. Root0 driver/material/pins/artifacts are not edited. Main owns launches, raw-review decisions and watchdog integration.

**43 CPU tests PASS, zero skips, 12.468s final run; CLI help PASS.** No native tokenizer/model/tensor work, subprocess launch, SSH/network, GPU, Git, repo edits or root0 outcome reanalysis. Tests use synthetic short-lived fixture trees and mocked native/device operations, including complete224-call metadata collection for each replication seed. Only these three deliverables persist. This author implemented the replication sidecar, not the underlying material or original runner; this is author-side validation, not independent scientific review.

| File | Final SHA256 |
|---|---|
| `/tmp/astra_interleaved_memory_replication_20260912.py` | `dc92b9d18f1fc7e8b9907f304e366de34a5e12340223f8dd17506e007093065f` |
| `/tmp/test_astra_interleaved_memory_replication_20260912.py` | `3fe75d38c21f4c4e0a76c620a4300e83775682bc5f29574d930ae92fe4ac24f3` |

## Stable API

From the immutable `22b7e528f6f62358981ed2264d30ee7242926160` source CWD, using the native venv executable spelling (absolute, **not resolved**):

```bash
"$PY" -B /tmp/astra_interleaved_memory_replication_20260912.py prepare \
  --source-root "$SOURCE" --materialroot "$MATERIAL" --runroot "$FRESH_ROOT" \
  --seed 1 --parentroot "$ORIGINAL_SEED1_ROOT" --device "$DEVICE" \
  --deadline "$CONTROLLER_DEADLINE_UNIX" --lease-end "$REAL_LEASE_EXPIRY_UNIX" \
  --seed0-gate "$MAIN_GATE_JSON" --seed0-gate-sha256 "$MAIN_GATE_SHA256"
```

For seed2, change only the explicitly chosen seed, corresponding original parent, device/deadline and fresh runroot; do not substitute root0/replay descendants. One invocation prepares one pair. `verify`, `run --allow-gpu`, `status`, `collect --archive EXCLUSIVE_PATH`, and supervised `_cue-worker --allow-gpu` use `--source-root` and `--runroot`. `run` never starts another seed. Root0's explicit SINGLE_VIEW→FOUR_VIEW and dev48→exact16→lexical48 order is retained.

Bounds: full1800-second controller includes140 cleanup; reserve300 external custody seconds before **real lease expiry minus21600 seconds**. Pass real expiry, not an already six-hour-adjusted cutoff. Main retains watchdog integration; this does not modify the frozen watchdog.

## Required Main seed0 gate JSON

JSON schema name is `INTERLEAVED_SEED0_MAIN_GATE_V1`. Required fields:

```text
schema: INTERLEAVED_SEED0_MAIN_GATE_V1
owner: Main
decision: ALLOW_SEEDS_1_2
eligible_seeds: [1, 2]
criteria: exact PROGRESSION dictionary from this driver (same as frozen root0)
raw_review_verdict: PASS
seed0_plan:       {path: ABSOLUTE_SEED0_PLAN, sha256: EXACT_HASH}
seed0_terminal:   {path: ABSOLUTE_SEED0_RUN_TERMINAL, sha256: EXACT_HASH}
seed0_validation: {path: ABSOLUTE_COLLECTOR_VALIDATION, sha256: EXACT_HASH}
raw_review:       {path: ABSOLUTE_RETURNED_RAW_REVIEW, sha256: EXACT_HASH}
```

No gate is fabricated here. Main reports Herschel's raw-review PASS and supplies exact paths/hashes after checking that review; the driver hashes/rechecks all supplied files, binds the original root0 driver/material/parent/panels, requires both arms' complete224 captures/reductions and technical custody, and checks the original FOUR thresholds in saved reductions. Generic COMPLETE, pending status, or a missing raw-review artifact is insufficient. This is consumption of Main's explicit narrow permission, not an independent semantic review of the review document or an authenticity signature.

**Exact semantic thresholds:** dev memory `counts.memory.correct >= 15`; exact memory `counts.correct >= 15`; habit `counts.addition.adherence >= 30`; ACT `counts.addition.correct_action >= 31`; each lexical family `counts.by_family["0"/"1"/"2"].correct >= 15`. Habit and ACT are not interchangeable. The gate reads those saved reduction fields directly, not the labels in Main's summary. Boundary fixtures require31ACT/30adherence PASS,30ACT/30adherence FAIL,32ACT/29adherence FAIL. Root0's reported32/32 in both fields does not reveal a swapped-threshold bug by itself.

New launch receipt retains root0 fields and exact new-driver argv; add `seed`, `parent_plan_sha256` (selected original pin), and `seed0_gate_sha256`. Main still performs the actual per-seed native prepare/verify and supplies launch/watchdog custody; CPU PASS is not native preparation or permission to launch.

The exact `criteria` value is:

```json
{
  "owner": "Main",
  "qualifying_arm": "FOUR_VIEW",
  "dev_memory_min": 15,
  "exact_memory_min": 15,
  "dev_habit_min": 30,
  "dev_act_min": 31,
  "each_lexical_family_min": 15,
  "eligible_next_seeds": [1, 2],
  "single_scores_irrelevant": true,
  "decide_only_after_both_technical_complete": true,
  "automatic_progression": false,
  "gate_evaluated_by_wrapper": false
}
```

The original progression declaration is preserved. New preparation checks the supplied Main decision against its bound seed0 evidence; it does not manufacture authorization from scores or evaluate replication outcomes to start another run. Main's summary is not required input and its temporarily swapped names cannot change this mapping.

## Implemented bindings and fixed recipe

- New versioned **copied adaptation**, not runtime monkeypatching: root0's supervision/capture/collection structure is copied into the new file. Small fit/config/manifest/capture helpers are explicitly adapted locally from the pinned varied runner. No seed substitution in a frozen module and no production `setattr`/mock patching. Shared memory/helper modules are loaded normally with their exact existing pins.
- `parent_identity` (`:123`) checks the selected seed's three `memory.PINS` hashes: original `plan.json`, `fit_teach/verified.json`, `readouts/teach/plan.json`, plus the original config seed. `memory.parent_record` then validates the existing native model/corpus/config, exactly80 original updates, no warm-start history, saved adapter identity, supervision and original readout identity/capture. A renamed copy of seed0 fails these pins even when placed under a seed1/2-looking directory. Both new arms use the corresponding original `fit_teach/adapter`, never each other or a replay descendant.
- `inspect_material` (`:191`) retains the **original seed0 material anchor** separately as `material_parentroot`; selected `parentroot` is independently pinned to seed1/2. The immutable22b7e528 manifest must contain audited schedules for0/1/2. Preparation (`:290`) reruns `material.export_native` using the selected original parent's byte-identical teach corpus and actual local tokenizer, compares the full audit and both corpora unchanged, and rechecks the selected parent's original dev cases/requests/native prefixes. These native operations are implemented but **not run by this author**.
- Plans use schema `INTERLEAVED_MEMORY_REPLICATION_V1`; bind source/material/base/parent inventories, original parent and readout pins, original state, Main gate evidence hashes, seed/device, venv spelling and fixed templates. Selected seed's padded costs and optimizer schedule hash are separately recorded, not relabeled seed0 costs. Readout plans carry `replication_binding` with seed, original parent path, original parent/readout plan hashes and gate hash; collection reconstructs and checks those exact plans.
- Same authored material and recipe: SINGLE_VIEW then FOUR_VIEW; each128 rows,10 epochs,batch4,320 new/400 cumulative updates; r8/alpha16/dropout.05/LR3e-4/accum1, fresh same-seed optimizer. Explicit `--overflow truncate` matches the frozen effective CLI, while actual drops/splits/truncation must remain zero. State/fit checks enforce loaded original tensors, base frozen, one adapter, empty initial optimizer state and unchanged parent. No dose, panel or ordering retuning.
- Each arm captures dev48, exact16, lexical48; all224 captures from both arms are checked before **any** reducer. Panels/sampling remain unchanged (including fixed generation seed20260912); optimizer seed1/2 changes do not substitute a new evaluation protocol. No new OFF/HF/original confirmation calls. Material is the same16 authored facts, three lexical cue families—not48 independent facts or novel-fact transfer. Memory target-token mass remains1280/10000=12.8%; target totals match, input compute does not.
- No worker/reduction starts with≤150s controller time left; each worker≤600s; controller alarm at effective end−140s. Full1800s is never shortened or extended; external300s must fit before real expiry−6h. Reservation/terminal store the selected seed and real lease separately. Main's independent watchdog remains necessary for blocking native/process failures; no watchdog code changed.

## Collection / Main integration

```bash
"$PY" -B /tmp/astra_interleaved_memory_replication_20260912.py verify \
  --source-root "$SOURCE" --runroot "$FRESH_ROOT"
# Main separately records launch.json/gpu.xml, reserves the device, and launches/watches.
"$PY" -B /tmp/astra_interleaved_memory_replication_20260912.py status \
  --source-root "$SOURCE" --runroot "$FRESH_ROOT"
# Only after controller absent and terminal; this is a future native collection command.
env -u CUDA_VISIBLE_DEVICES PYTHONDONTWRITEBYTECODE=1 \
  timeout --signal=KILL 300s "$PY" -B /tmp/astra_interleaved_memory_replication_20260912.py collect \
  --source-root "$SOURCE" --runroot "$FRESH_ROOT" --archive "$EXCLUSIVE_ARCHIVE"
```

The inner launch argv is exactly `[PY, "-B", NEW_DRIVER, "run", "--source-root", SOURCE, "--runroot", ROOT, "--allow-gpu"]`; `PY` is `os.path.abspath(sys.executable)`, never `resolve()`. Main's launch JSON additionally binds root/source/device, new-driver/plan hashes, selected seed/parent/gate hashes, integer PID, started_utc, GPU UUID,1800/300 bounds and224 calls. Existing XML UUID comparison, worker command/order/time accounting, full release observation and metadata-only archive verification remain. Collection never fits/generates/reduces; weights remain native. New validation explicitly reports seed/original-parent-plan/gate identity.

Fresh per-seed roots must be siblings of the immutable material root, non-overlapping with material, model, source, selected parent, material anchor or seed0 run. No overwrite/retry/resume/recollection after partial outputs, no automatic later-seed start, no outcome-selective skipped arm. Failed native/custody attempts remain evidence for Main reconciliation. Late collection records overrun without changing the original controller/custody budget. Status is file-presence information, not an implicit scientific gate.

## CPU coverage and remaining limits

Command actually run:

```bash
PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 CUDA_VISIBLE_DEVICES='' \
  python3 -B /tmp/test_astra_interleaved_memory_replication_20260912.py -v
```

Coverage: both seeds' configs/worker commands/original parent pins; copied-seed0 and opposite-seed rejection; matching pins with wrong config seed; warm-state/fresh optimizer/80→400 history; ACT/adherence boundary semantics; explicit versus generic/pending/changed Main gate; both-arm/six-panel/224-capture completeness; all three lexical families; fixed slot/prompt membership; seed/device/readout plan and output-slot identity; six-hour cutoff and finite bounds; venv symlink spelling; missing/rehashed raw payload/prefix failure; fresh root and orphan refusal; worker command/clock/UUID/release/metadata custody; complete synthetic224-call collection for seeds1 and2. Frozen root0/replay/varied hashes are checked by tests.

Initial tests caught an omitted copied CLI `--overflow truncate`; restored the frozen flag without changing its semantics. Later errors were synthetic adapter-identity fixtures missing a mock; repaired only those fixtures, not production checks. Final43 tests pass, with no skips. There is no configured formatter added and no native completion, throughput, weights or experimental success inferred from fixtures.

Frozen `/tmp/astra_interleaved_memory_pair_20260912.py` remains SHA256 `d100cb58296499c7cd6489d20e96528898f2e48b698147a97dae99fa38946bbe`; `/tmp/astra_memory_replay_20260912.py` remains `1586ddf7d690ce8bc55d680bd926439fbd597236ea8e76394f88a3bdf023c8bc`. Source tree must still be immutable22b7e528; all legacy dependency pins are retained/read-only. Local hashes do not authenticate model origin. Main reports root0 review PASS; this author neither reran that analyzer nor archived/corrected Main's summary. Subsequent seed1/2 results test **repeatability of authored-material memory plus habit**, not parenting/G3 or a mechanism freeze. **EDITSTOP.**
