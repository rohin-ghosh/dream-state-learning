# Separate saved-weight numerical audit — EDIT-STOP

The delivered terminal collector remains frozen at **`e5f0c9de2a2562deda677dbb4f374c831d7928c7b1dcd9fc38b52330500a9b17`**; its tests remain `19b3d7d2137b40c9a8e09824ccd67c5627be8c680ab10ef01249759bde08c041`. My briefly started in-place addition was completely removed and both exact hashes rechecked. Main can collect with the original delivery unchanged.

## New files

- `/tmp/astra_rulegame_record_weight_audit_20260912.py` — SHA256 `022eae90fea2298dbe2478e87c37c00df759c630d7639856090356cd17d79b6b`.
- `/tmp/test_astra_rulegame_record_weight_audit_20260912.py` — SHA256 `c80051342e7842164a672a70b463047668a076f67eb7ebb4831ee6131cdd772e`.
- This separate handoff. No native weights, run metadata, prepared material, sealed fits, source or existing collector artifacts were changed. No SSH/network/GPU/model/Git actions.

**21/21 local CPU tests PASS.** Tests use synthetic in-memory safetensors and mocked receipts. Standard library only: no NumPy, torch, Transformers or safetensors package dependency. An initial NumPy-dependent test attempt found NumPy unavailable; the implementation was replaced with dependency-free streaming math, and the complete suite now passes.

## Main-only execution

```bash
python3 -B /tmp/test_astra_rulegame_record_weight_audit_20260912.py
/localhome/local-rohing/v2/venv/bin/python -B /tmp/astra_rulegame_record_weight_audit_20260912.py
```

Default new immutable **external** receipt: `/tmp/astra_rulegame_record_weight_audit_20260912.json`. An explicit fresh external destination may be supplied with `--receipt /tmp/NEW_NAME.json`; never use a prepared/artifact directory. Existing receipt paths are refused, not overwritten or resumed. Do not retry a timed-out/disconnected invocation without Main reconciliation.

Fixed target: `/localhome/local-rohing/astra_diagnostics/astra_rulegame_interaction_v3_record_write_20260912_attempt2`; requires PID233174 absent and completed paired-write result. Plan pin `48effd1ba154f497e5946d308f990624ada63bd905c198e0abfdf668131a8ee4`. Reuses unchanged driver `/tmp/astra_rulegame_record_write_v2_20260912.py`, pin `183b48be6193da953f699d718575f9227fd946d9f8111d2d1647ae5dd431ec7c`, **only for model-free saved-tensor shape/offset validation**. Does not call its modules/checked_plan/native loading/training functions. Uses the existing pinned memory-collector common helper for exclusive JSON and hash/path-safe reads.

## Measurements and custody

- Per P/A adapter: tensor count; **total, LoRA_A and LoRA_B** entry counts, finite/nonfinite counts, finite nonzero counts, all-entry nonzero counts, L2 norm and max absolute value.
- Supports little-endian F32, F16 and BF16. Reads at most 1MiB payload chunks; decodes into Python floating-point values and uses `math.fsum` of squared finite values per chunk. Header capped at 16MiB. No model construction or tensor-library/GPU import.
- Hashes all fit/adapter files before and after scanning and requires equality with the sealed fit manifest. Binds result/worker fit receipt and native weight SHA; checks original plan/result remain unchanged. Records before/after inventories and weight hashes. The external receipt is deliberately not inserted into the existing capsule or sealed root.
- NaN/Inf produce **NONFINITE_TENSORS**, named offending tensors and finite/nonfinite counts. Whole-group L2/maxabs/nonzero count become `null` for affected groups; finite-only nonzero counts remain explicit, never disguised as all-entry metrics. Structural/hash/read/import failures are explicit per-arm ERROR or top-level ERROR. Both arms are attempted unless the global audit boundary interrupts them.
- Exit 0 only for **FINITE_PAIRED_ADAPTERS**; invalid/nonfinite/error receipts exit 2. This is a numerical check, not a readout criterion. All-zero B remains FINITE with `nonzero_B_from_declared_zero_init: false`; there is no tuned threshold or retry.

## Interpretation / bounds

These are **saved tensor magnitudes, not complete parameter-update deltas**. No initial A snapshot was retained. Given the declared fresh zero-B initialization, nonzero saved B corroborates a change/write, **not utility, transfer, or readout success**. Zero B does not establish that no optimizer step occurred. No norms of the composed BA update or behavioral effects are claimed.

A **300-second alarm bounds the audit work**, including binding, numerical scans and before/after hashing. The alarm is then disabled to write one small immutable success/failure receipt; receipt finalization is separate from that scan bound. Audit duration is recorded independently of any GPU reservation cost. This script performs no GPU vacancy check or reservation and must not revise the terminal collector's costs.

Tests cover F32/F16/BF16 known norms, signed zero/zero B, NaN/Inf, large finite F32 accumulation, multi-chunk counts, truncation/trailing bytes/overlap/shape/missing-B/dtype rejection, before/after hashes and mutation detection, external/no-overwrite receipts, explicit error receipt, alarm cleanup, and absence of model/GPU APIs.

**EDIT-STOP.** Main executes against native weights; no actual native weight outcomes were inspected here.
