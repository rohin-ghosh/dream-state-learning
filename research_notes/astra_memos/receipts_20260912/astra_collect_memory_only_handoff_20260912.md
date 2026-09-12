# Memory-only collector — ready for Main

2026-09-12. **EDIT-STOP.** Only the collector and this handoff were written. No remote, GPU, Git, repository, running-sidecar or dependency changes/actions were performed. No further guard or scientific scope is proposed.

Collector: `/tmp/astra_collect_memory_only_20260912.py`

SHA-256: `d2152c179ca9a6b9801933a480ed62cd203018868a52034e13676963787579eb`

## Commands

Use Main's native VM interpreter, with bytecode disabled and without a reserved-device `CUDA_VISIBLE_DEVICES` environment on the collector itself:

```bash
python -B /tmp/astra_collect_memory_only_20260912.py status
python -B /tmp/astra_collect_memory_only_20260912.py finish
```

Native paths are fixed to:

- Source: `~/astra_sources/3a12807f88747bafd0aada1d4a09ba88b915f903`.
- Run: `~/astra_diagnostics/astra_fundamental_memory_only_20260912_attempt1`.
- Launch receipts: `launch/seed0`, `launch/seed1`, `launch/seed2`.
- Child evidence: `seed0`, `seed1`, `seed2`, each with `adapter`, `dev`, `exact`.
- Prepared plan pin: `0f8d1a3042b92c3c940309f0b909f7ee535c295e3c3fb6197a8d45c4c137ac90`.
- Sealed devices: seed0→GPU3, seed1→GPU4, seed2→GPU5; actual controller PIDs come from launch receipts.

Dependencies remain the accepted memory runner and its existing fading helper. The runner hash is checked before import; it binds the frozen source. No old file is edited.

## Status

Read-only availability: controller PID/presence, terminal status/error, fit receipt/DONE/manifest, and dev/exact reduction/capture-manifest presence. It does not import the native runner, invoke `check_free`, load weights/tokenizers, reduce or score anything. While exact readouts run, use **status only**.

## Finish

1. Requires all three launch receipts, terminal receipts and controller PIDs absent. A still-running controller or missing terminal blocks finish before native checks or writes.
2. Reuses the runner's native source/plan/base/parent-immutability checks. Every recorded successful fit is checked against its actual adapter inventory, full CPU LoRA states and existing80-step/160-cumulative warm-start validation, including failures that occurred later in readout.
3. Verifies existing dev/exact plan/capture/reduction hashes, expected raw request/response coverage, native prefix/identity bindings and terminal references. **No reducer is rerun and no score is recalculated or selected.** Complete terminals require both panels; failed terminals can retain missing/partial panels and are not turned into zeros or successes.
4. Main's existing `check_free` runs on each GPU3/4/5, including its process/reservation/queue checks. GPU UUIDs must match launch evidence. Immutable `seedN/main_release.xml` and `main_release.json` bind launch/terminal/plan/XML hashes and observation-time full reservation duration. Collection delay is included in that observed reservation interval; it is not GPU busy time or a monetary estimate.
5. Creates, exclusively, **`/tmp/astra_memory_only_terminal_20260912.tgz`** and **`/tmp/astra_memory_only_terminal_20260912.tgz.validation.json`**. Archive members use `astra_diagnostics/astra_fundamental_memory_only_20260912_attempt1/...` paths relative to Main's home.

All regular nonweight metadata is included, including partial failure files and release records. Excluded suffixes: `.bin`, `.safetensors`, `.pt`, `.pth`, `.ckpt`, `.pyc`, `.pyo`; `__pycache__` directories are excluded. Physical weights remain at original node3 roots. Validation contains the complete included-file SHA-256 inventory, archive hash, statuses and evidence-verification results.

The archive is read back without extraction: member names must be canonical relative paths under this run; absolute/traversal/duplicate/unexpected/link/special members are rejected. Exact file membership and payload hashes are checked against source metadata. Existing verified metadata must stay unchanged across collection and packaging except for the new release records.

## Repeated finish / partial collection

- A valid archive plus validation file is **verified read-only**, returning `ALREADY_COLLECTED_VERIFIED_NO_WRITES`. This checks the capsule, current run metadata and historical release bindings; it is not a new live GPU-release or physical-weight audit.
- A preexisting archive without validation, validation without archive, malformed/mismatched capsule, or orphan release JSON/XML is preserved and refused. No deletion, overwrite or automatic repair.
- If valid release pairs already exist but no archive was created, finish can reuse those immutable pairs after the normal terminal/native/free-device checks. Their recorded timestamps are never rewritten.
- Scientific failures remain `FAILED_PARTIAL_NO_RETRY` inside the capsule. Integrity failures stop collection rather than silently certifying altered evidence; original artifacts remain untouched.

## Local validation

**15 in-memory CPU unit checks passed**, plus targeted partial-capture, missing-complete-capture, symlink and final archive smoke checks; AST parsing passed. Tests covered archive membership/hashes, traversal/absolute paths, links/special entries, duplicates, duplicate JSON keys, exclusive creation, metadata exclusions, live-controller blocking, availability-only status, repeated-finish read-only behavior, partial capsule refusal and orphan release preservation.

Tests used synthetic in-memory archives and mocks; they wrote no fixture files, called no GPU/process-management tool, loaded no native model and did not inspect the live VM. Main executes the native `status`/`finish` commands. There is no new acceptance threshold, benchmark, framework, or independent-review gate.

**EDIT-STOP — ready for Main once all controllers are gone and all terminals exist.**
