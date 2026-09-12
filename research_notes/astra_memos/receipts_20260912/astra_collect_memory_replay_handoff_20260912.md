# Root0 replay collector — EDIT-STOP

2026-09-12. Ready for Main's native check/execution. **Do not relaunch PID211116 or either replay arm.** Only this handoff and `/tmp/astra_collect_memory_replay_20260912.py` were written; no native status, remote, GPU, network, Git, repository or live-runner actions were executed here.

Collector SHA256: `d5d2f8beb8e61eaf11f677af56dd734dc05b461a2ed835ed612a33125bb5413d` (166 lines). AST/import smoke passed; **12 in-memory CPU tests PASS**: status has no scoring/binding/writes; live controller/missing terminal block; successful finish plus verified no-write repeat; partial second arm preservation; incomplete receipts; full-release failure; partial release/capsule refusal; modified archive rejection; unsafe tar member rejection; child inventory mismatch. Native state/capture/fullcheck_free operations were mocked, not executed. Test fixtures existed only in the shell process; no extra test file was created.

## Exact scope and read-only reuse

- Native source: `~/astra_sources/3a12807f88747bafd0aada1d4a09ba88b915f903`.
- Sole run root: `~/astra_diagnostics/astra_memory_replay_20260912_attempt1/seed0`.
- Sealed plan SHA256: `70405bfa50486feaa2b000ee8102a1cdf30265bccaf102958d7e3ea17035bbb9`.
- Launch pin: node3/GPU0, PID211116, `2026-09-12T20:02:28.997513+00:00`; checks actual `launch/launch.json` and the exact runner command. No roots1/2 discovery or progression logic.
- Runner pin: `/tmp/astra_memory_replay_20260912.py`, SHA256 `1586ddf7d690ce8bc55d680bd926439fbd597236ea8e76394f88a3bdf023c8bc`; its existing memory/fading pins remain enforced.
- Reuses the accepted `/tmp/astra_collect_memory_only_20260912.py` read/capture/archive helpers unchanged, SHA256 `d2152c179ca9a6b9801933a480ed62cd203018868a52034e13676963787579eb`. Keep this dependency available on node3. No new path/symlink framework was added.
- Uses the frozen source's existing `gpu/astra_mini_sudoku_diagnostic.py::check_free`, SHA256 `a586b03bdb9c52f1061aa1e477ae983cc9d45ec0a2cd440642851fd8df8b609f`.

## Main-only commands

On node3, after placing the new collector at its assigned path:

```bash
env -u CUDA_VISIBLE_DEVICES PYTHONDONTWRITEBYTECODE=1 \
  python3 -B /tmp/astra_collect_memory_replay_20260912.py status

# Only once status shows controller_present=false AND terminal_available=true:
env -u CUDA_VISIBLE_DEVICES PYTHONDONTWRITEBYTECODE=1 \
  python3 -B /tmp/astra_collect_memory_replay_20260912.py finish
```

Clearing the collector's own CUDA_VISIBLE_DEVICES avoids falsely claiming GPU0 in the full reservation scan; it does not bypass other processes/queue checks. **status** reads pinned plan/launch/terminal and file availability only (fit/process/receipt, dev/exact capture/reduction, arm result); it does not load models, check GPUs or score outputs.

**finish** first requires the pinned controller absent and terminal present. It reuses `runner.verify`, validates successful fit manifests and original/final serialized state inventories, original parent immutability, terminal/reservation bindings, successful worker receipts and separate raw dev/exact capture bindings without recomputing scores. COMPLETE additionally requires both arm results, six successful receipts, accounted process records, deadline compliance and worker-cost reconciliation. Failed pairs remain failed: completed first-arm evidence and partial second-arm metadata are retained; an unfinished adapter without a fit-result is not certified as successful. Integrity-check failure never silently becomes a scientific zero.

## Immutable outputs and cost scope

After native fullcheck_free verifies GPU0 and the launched UUID, creates exclusively:

- `ROOT/run/main_release.xml` — full native XML observation.
- `ROOT/run/main_release.json` — UUID, UTC, launch/terminal/XML/collector hashes and full reservation seconds measured from the launch receipt through this release observation (including post-controller delay).
- **`/tmp/astra_memory_replay_seed0_terminal_20260912.tgz`**.
- **`/tmp/astra_memory_replay_seed0_terminal_20260912.tgz.validation.json`** — archive SHA256, every included member hash, statuses and verification-only audit results.

The archive contains all seed0-root regular metadata under its home-relative prefix, excluding `__pycache__` and `.bin/.safetensors/.pt/.pth/.ckpt/.pyc/.pyo`; native weights remain untouched. Reuses accepted path-safe validation for exact member set, regular files, no links/traversal/duplicates/extended headers, and byte hashes. Source metadata is rechecked around packaging; no extraction is performed.

A fully completed repeated finish verifies the existing capsule against current evidence and returns `ALREADY_COLLECTED_VERIFIED_NO_WRITES`, without a new GPU release probe or evidence writes. A partial archive/validation or preexisting release without a complete capsule is **preserved and refused**, never overwritten/recreated. Following an SSH timeout, inspect existing files/process state; do not blindly retry, delete evidence or relaunch the experiment. A fullcheck_free failure before output creation leaves outputs unwritten.

Native tests/status/finish, external cost ledger, downloading and independent raw score reduction remain Main-owned. No scientific progression decision or new score calculation is implemented. **EDIT-STOP.**
