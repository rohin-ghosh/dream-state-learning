# Actual-record paired-write collector — EDIT-STOP

Only the assigned collector, test file and this handoff were written. No SSH/network/GPU/native/model/Git actions, source edits, launch or readout. Main executes native collection.

## Files and tests

- `/tmp/astra_collect_rulegame_record_write_20260912.py` — SHA256 `e5f0c9de2a2562deda677dbb4f374c831d7928c7b1dcd9fc38b52330500a9b17`.
- `/tmp/test_astra_collect_rulegame_record_write_20260912.py` — SHA256 `19b3d7d2137b40c9a8e09824ccd67c5627be8c680ab10ef01249759bde08c041`.
- **27/27 local CPU tests PASS**, including six manifest-corruption subcases. Synthetic in-memory receipts/weights only; no temporary fixture files or native imports. Tests also call the pinned driver's real `validate_fit` with mocked file inventories and its real safetensors header/size validator with in-memory bytes.

```bash
python3 -B /tmp/test_astra_collect_rulegame_record_write_20260912.py
```

Coverage: complete P/A independent fits, partial P/A/missing evidence and partial weight inventory, no-zero missing costs, weight/manifest/worker-token/attempt-PID custody, owned cleanup, controller overruns, status without reads, live/no-terminal refusal, alarm/finally, GPU UUID/occupancy, no writes after failed vacancy, orphan/repeat handling, archive hash/traversal/link/duplicate rejection, actual 12-step/drop/warm-start/nonfinite/token/trainability contract, valid/truncated safetensors, and no training/readout/model launch calls. Native binding/fullcheck remains Main's validation.

## Fixed scope and Main-only execution

PID **233174**, node3 GPU2, launch **2026-09-12T21:30:37.652148+00:00**; UUID `GPU-41a86250-88eb-ed8a-ddfe-9d6f93515da1`.

Native root `/localhome/local-rohing/astra_diagnostics/astra_rulegame_interaction_v3_record_write_20260912_attempt2`; launch sibling is root name + `_launch`. Source `/localhome/local-rohing/astra_sources/610c6edd05ce9c85720ee6e992889badecc2c158`.

Plan `48effd1ba154f497e5946d308f990624ada63bd905c198e0abfdf668131a8ee4`; driver `/tmp/astra_rulegame_record_write_v2_20260912.py`, pin `183b48be6193da953f699d718575f9227fd946d9f8111d2d1647ae5dd431ec7c`. Reuses the existing memory collector common helper, pin `d2152c179ca9a6b9801933a480ed62cd203018868a52034e13676963787579eb`, and native fullcheck helper, pin `a586b03bdb9c52f1061aa1e477ae983cc9d45ec0a2cd440642851fd8df8b609f`. Dependencies remain untouched.

```bash
env -u CUDA_VISIBLE_DEVICES /localhome/local-rohing/v2/venv/bin/python -B /tmp/astra_collect_rulegame_record_write_20260912.py status
env -u CUDA_VISIBLE_DEVICES /localhome/local-rohing/v2/venv/bin/python -B /tmp/astra_collect_rulegame_record_write_20260912.py finish
```

`status` returns existence markers only. `finish` requires controller absent and exactly one `run/result.json` or `run/failure.json`; neither means Main reconciliation, not retry.

## Validation / evidence

Calls the pinned driver's **checked_plan**, **verify_inputs**, and **validate_fit**. These bind source/material/fixed-selection/Main-audit hashes, original formation capture and current base bytes; then validate each successful adapter's fresh rank8 recipe, 12 updates/microbatches/epochs, unchanged two-record corpus/native token receipts, zero drops/splits/nonfinite batches, frozen-base trainability, saved LoRA coverage/shapes/byte ranges and native adapter hashes. Checks fit-manifest seals, worker/attempt PID and launch token, completed-arm receipt identity, supervisor success/owned cleanup and inclusive controller accounting.

PARTIAL preserves failure, missing evidence and any verified completed child. Available incomplete adapter files are inventoried without claiming fit validity. Missing fit/readout values remain `null`; reported observed worker cost is marked incomplete when a receipt is missing. Corrupt purported-success evidence refuses certification. No semantic rejudgment, material rewriting, training, tokenizer/model loading, record selection or readout execution.

Native `check_free('2')` checks GPU/process/queue state and matching launch UUID/empty XML. Exclusively writes `run/main_release.json` and `.xml`; then NEW **`/tmp/astra_rulegame_record_write_terminal_20260912.tgz`** plus **`.tgz.validation.json`**. Includes all nonweight/non-pyc metadata under both write root and launch sibling, including material/provenance, terminal, fit/trainability/native token receipts and logs. Weight bytes remain native; hashes and tensor metadata remain in the capsule. Formation/source/model files outside these roots are bound, not copied. Existing common path/member/link/duplicate/hash checks validate the exact inventory without extraction.

Repeat after completed collection verifies capsule and current metadata without native calls or writes; it is historical collection verification, not a fresh GPU/weight audit. Any orphan capsule/validation/release refuses overwrite. Timeout/SSH disconnect requires Main reconciliation, never blind retry.

## Cost / claims

Collector has a **300s alarm** through hashing, audits, full vacancy, archive and final validation write. A timeout preserves incomplete exclusive evidence. Release time is actual **launch-to-observed-full-vacancy**, including CPU/gaps/cleanup and delay before collection; controller and observed worker times are separately reported subsets, not additive. Driver bounds are **1200s inclusive controller, 140s cleanup reserve, 600s workers**; PARTIAL overruns are exposed rather than hidden. Packaging completion/collection elapsed are separate from vacancy observation. No price or compute-matching assertion.

**Write success is NOT readout success.** Status remains paired adapters saved/readout pending; no transfer, semantic-purity, model-origin, or downstream scientific verdict is produced.

**EDIT-STOP.** All other owners' files and artifacts preserved.
