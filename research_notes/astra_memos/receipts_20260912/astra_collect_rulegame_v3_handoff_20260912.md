# Rulegame v3 formation collector — EDIT-STOP

Only this handoff and `/tmp/astra_collect_rulegame_v3_20260912.py` were written. No GPU/native/model/network/Git actions, source edits, launch, or Main semantic judgment. Main executes the collector.

**Collector SHA256:** `ea18d0aa20de22d4ed5e04db63fda30a55207ac65824a03090df1287536946d2` (221 lines).

## Fixed binding / Main-only commands

Node3 GPU2, PID **228661**, launch **2026-09-12T21:12:06.864318+00:00**, UUID `GPU-41a86250-88eb-ed8a-ddfe-9d6f93515da1`.

Source `/localhome/local-rohing/astra_sources/610c6edd05ce9c85720ee6e992889badecc2c158`; root `/localhome/local-rohing/astra_diagnostics/astra_rulegame_interaction_v3_20260912_attempt1`; launch evidence in sibling `astra_rulegame_interaction_v3_20260912_attempt1_formation_launch`.

Plan pin `7dae3ca492ed39545987ab8deb5f39631a40332d480ddb99292e5f083741c468`. Diagnostic pin `e6055da48b2c6fa1bd294c9d991e07f32f05dc6630fe8973373977bdfe977526`; launcher receipt pin `9b37905d6fb7271aac14e7630269e6767378bd6de8a19217ab49a78897fa1cb3`.

```bash
env -u CUDA_VISIBLE_DEVICES /localhome/local-rohing/v2/venv/bin/python -B /tmp/astra_collect_rulegame_v3_20260912.py status
env -u CUDA_VISIBLE_DEVICES /localhome/local-rohing/v2/venv/bin/python -B /tmp/astra_collect_rulegame_v3_20260912.py finish
```

Requires existing pinned `/tmp/astra_collect_memory_only_20260912.py` (`d2152c179ca9a6b9801933a480ed62cd203018868a52034e13676963787579eb`) and source `gpu/astra_mini_sudoku_diagnostic.py` (`a586b03bdb9c52f1061aa1e477ae983cc9d45ec0a2cd440642851fd8df8b609f`). Neither was edited.

## Behavior

- **Status:** existence markers and controller `/proc` presence only; no capture reads, scores, tokenizer imports or GPU checks.
- **Finish:** requires controller absent plus formation result or failure (stage/data). Neither means refusal for Main reconciliation. Refuses material/write/evaluation scope. Verifies pinned plan/source, current model inventory, native preparation/launch identity, worker command/PID-group/device/600s bound, and supervisor receipt.
- **Successful formation:** requires successful owned cleanup; compares world/raw-call replay to stored provenance, result/capture seal and usage; runs existing local-only native tokenizer audit over every raw call. No model forwards. Does not select records, certify semantic purity, authorize promotion, or launch material/write/evaluation.
- **Failure:** preserves PARTIAL, original failure records, missing evidence, available worker receipts and `null` unavailable usage/cost; not a scientific zero. Corrupt purported-success evidence refuses certification rather than relabeling it successful.
- **Release:** existing full `check_free('2')` checks GPU/process/queue state; matching UUID and empty XML required. Exclusive `formation/main_release.json` and `.xml`; then exclusive `/tmp/astra_rulegame_v3_formation_terminal_20260912.tgz` plus `.tgz.validation.json`.
- **Capsule:** includes raw nonweight metadata from **both root and launch sibling**, with exact-member SHA256 validation. Reuses common path/link/duplicate protection and verifies unchanged metadata before/after packing. No extraction; weights/pyc excluded. Source/model bytes remain outside capsule, bound by inventories.
- **No retry/overwrite:** complete repeats verify existing capsule/evidence without native/GPU calls or writes; partial archive/validation/release refuses overwrite. After timeout or SSH disconnection, Main reconciles processes and evidence—no blind rerun. Historical release verification is not a fresh vacancy claim.

## Time / cost

A **300s real-time collector alarm** covers binding/model hashing, native token/world audit, full release, packaging, validation, and repeat verification. Timeout bypasses ordinary exception handling and preserves partial exclusive artifacts. Final receipt writing remains inside the alarm.

Release records actual **launch-to-observed-full-vacancy seconds**, including CPU/gaps/cleanup and collection-start delay. Worker reservation is separately reported as a subset, or `null` if missing. **600s worker cap and legacy 1800s aggregate worker allowance are NOT full-controller clock guarantees**; full-controller cap is explicitly `null`. Collection elapsed/completion is separately recorded after archive checks; vacancy observation is not mislabeled packaging completion. No price claim.

## Tests

**28/28 local CPU mock/in-memory checks PASS** (`python3 -B`, stdin; no third test file/fixtures written). Coverage: marker-only status; live/no-terminal refusal; alarm/finally; UUID/occupied rejection; two-scope inventory/collision; successful replay/native audit exactly once; PARTIAL/missing/failure handling without tokenizer or zero; supervisor/bounds/world/token/identity corruption; fullcheck failure before writes; orphan and repeated collection behavior; safe two-scope archive, traversal/duplicate/link rejection; absence of material/model/evaluation launch calls. Native APIs and GPU checks were mocked, not executed. Main still performs native collection.

**EDIT-STOP.** No additional ownership assumed.
