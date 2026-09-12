# Conditional root0 fit collector — EDIT-STOP

2026-09-12. Scope: `/tmp/astra_collect_conditional_fits_20260912.py` and this handoff only. No live-runner/repository edits, native execution, model calls, GPU queries, network, or Git. Main executes collection. **Authorship disclosure:** this assistant also authored the conditional fit wrapper; these are technical custody/receipt checks, not an independent scientific review.

## Exact Main commands

Run with the original native interpreter and immutable source CWD. Do not run `finish` inside a GPU-reserving controller environment: the full vacancy checker deliberately rejects outstanding reservations. Main must reconcile its external ledger and ensure no reallocation races collection.

```bash
cd /localhome/local-rohing/astra_sources/5f6e1f1d217dcdb15176dc84b9ac34ec960c48de
env -u CUDA_VISIBLE_DEVICES PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
  /localhome/local-rohing/v2/venv/bin/python -B /tmp/astra_collect_conditional_fits_20260912.py status

# Only after controller PID 214826 is absent AND run/terminal.json exists:
env -u CUDA_VISIBLE_DEVICES PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
  /localhome/local-rohing/v2/venv/bin/python -B /tmp/astra_collect_conditional_fits_20260912.py finish
```

Pinned target: `/localhome/local-rohing/astra_diagnostics/astra_conditional_behavior_20260912_attempt2/fits_root0_attempt1`. No configurable target, source, PID, or device flags. `status` reads plan/launch/terminal and checks marker presence; it does not import the fit runner, read train manifests, score losses, query GPUs, or write files. It deliberately omits terminal error text, which could contain metrics.

Output artifacts, exclusively created:

- `ROOT/run/main_release.xml`: actual full-vacancy-check XML.
- `ROOT/run/main_release.json`: GPU UUID, PID absence, launch/terminal/XML/collector hashes, release UTC, full launch-to-observed-vacancy duration, controller/worker subset costs. Costs are **not additive**; monetary cost remains null.
- `/tmp/astra_conditional_fits_root0_terminal_20260912.tgz`.
- `/tmp/astra_conditional_fits_root0_terminal_20260912.tgz.validation.json`: exact metadata inventory, archive hash, fit verification availability, terminal status, exclusions, scope and authorship.

## Pins and checks

| Pin | Exact value |
|---|---|
| Collector script | `1d168403e88a8833b6993b823b0caccdfeed8f925e77971c7d0d6cda68d01152` |
| Plan | `680e5239cd90c15b72de998d22c09cf5aa451d2e71111d99e940532e43510f11` |
| Live runner | `3be6583f97f68d944774ff15f5fcd4d66522991d62bf865b03f005808cf4f96f` |
| Launcher | `08181ceeb3b247a1bf2e9390287b41bdac09b73caaee4d7668ce70ac59ae8c67` |
| Common safe I/O helper | `d2152c179ca9a6b9801933a480ed62cd203018868a52034e13676963787579eb` |
| Full vacancy checker | `a586b03bdb9c52f1061aa1e477ae983cc9d45ec0a2cd440642851fd8df8b609f` |
| Source | `5f6e1f1d217dcdb15176dc84b9ac34ec960c48de` |
| GPU1 UUID | `GPU-71e5a3e2-e9c8-5caf-70d8-73794ac34821` |
| Launch | `2026-09-12T20:16:17.399324+00:00`, node3/PID214826 |

The safe I/O helper must be available unchanged at `/tmp/astra_collect_memory_only_20260912.py`. Imported dependency bytes are hashed before execution. Native `runner.bind(SOURCE)` and `runner.verify(ROOT)` revalidate source, base, tokenizer/material inventories, configuration and commands. Each published fit is independently passed to `runner.verify_fit(plan, ROOT/run/ARM, ARM)`; its actual adapter inventory and manifest hash must exactly match the persisted fit result and terminal arm result. This invokes the existing finite-loss validity guard but does not publish, rank or score losses.

Both arms retain the fixed fresh-from-base recipe: AUTH then DERANGED, 128 rows/128 updates each, four epochs, LR1e-4/r8/alpha16/dropout.05/seed0/batch4/accum1; 11248 input/1888 target per epoch, 44992/7552 total per fit, no skipped/truncated items or warmstart. Receipts must bind exact plan commands, PID=PGID, device1, positive <=600s worker timeout, successful published fits, group/GPU absence and valid costs. Monotonic worker intervals must not overlap; DERANGED requires a completed AUTH. COMPLETE requires both fits, two receipts, no error, full accounting/release, and the 1200s pair bound (including 140s cleanup reserve).

`finish` requires controller absence and a terminal before loading the runner. It snapshots safe metadata, verifies receipts/inputs/adapter inventories, performs full `check_free("1")` and matches the UUID in both launch and release XML. It then revalidates inputs, adapters and unchanged metadata before creating release records and a hash-validated USTAR metadata capsule. No cancellation, training, readout, generation, retry or overwrite path exists.

For a fully accounted/released `FAILED_PARTIAL_NO_RETRY`, the capsule retains that failure status; only published fits are called verified. Unaccounted workers, unmatched process/supervision receipts, unpublished fit results, or failed cleanup reject collection for manual reconciliation. No partial is promoted to COMPLETE. Any existing partial release or capsule fails without replacement. A complete existing capsule is rechecked against **current** source/base/material/adapter inventories, metadata, release bindings and archive contents, returning `ALREADY_COLLECTED_VERIFIED_NO_WRITES` without a new GPU query. This is validation of the historical release receipt, not a new promise of present vacancy.

## CPU validation

**18/18 local stdlib unittest cases PASS, zero skips**, run inline with all runner/checker/PID/time operations mocked and disposable local fixture roots. Coverage: status avoids loss reads/imports; live PID/missing terminal rejection; success/idempotence and weight exclusion; current metadata, archive, plan, worker command, cost and adapter weight mutations; orphan capsule/release refusal; launch/release UUID mismatches; worker overlap; unaccounted partial; source-verification failure; helper pin. CLI `--help` also passed. No native collector execution was performed.

The larger inline fixture suite is in the task execution transcript rather than a third owned test file. This small reproducible smoke check imports only the pinned stdlib collector/helper, makes no native calls, and creates no files:

```bash
python3 -B - <<'PY'
import importlib.util
import unittest
from unittest.mock import patch
spec = importlib.util.spec_from_file_location('collector_smoke', '/tmp/astra_collect_conditional_fits_20260912.py')
collector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(collector)
class Smoke(unittest.TestCase):
    def test_live_blocks_before_loading(self):
        with patch.object(collector, 'status', return_value={'controller_present': True, 'terminal_available': True}), patch.object(collector, 'load') as loader:
            with self.assertRaises(ValueError): collector.finish()
            loader.assert_not_called()
    def test_missing_terminal_blocks(self):
        with patch.object(collector, 'status', return_value={'controller_present': False, 'terminal_available': False}), patch.object(collector, 'load') as loader:
            with self.assertRaises(ValueError): collector.finish()
            loader.assert_not_called()
    def test_uuid(self):
        xml = '<nvidia_smi_log><gpu><uuid>' + collector.UUID + '</uuid></gpu></nvidia_smi_log>'
        collector.check_uuid({'gpu_uuid': collector.UUID}, xml)
        with self.assertRaises(ValueError): collector.check_uuid({'gpu_uuid': 'wrong'}, xml)
    def test_cost_domain(self):
        for value in (True, -1, float('nan'), float('inf'), '1'):
            self.assertFalse(collector.finite_nonnegative(value))
        self.assertTrue(collector.finite_nonnegative(0.0))
unittest.main(verbosity=2)
PY
```

## Limitations / interpretation

- Native invocation remains Main's responsibility; a currently live job is not declared terminal or released here.
- Capsule excludes `.bin`, `.safetensors`, `.pt`, `.pth`, `.ckpt`, `.pyc`, `.pyo` and `__pycache__`. Weights remain in their original native roots, verified by hash rather than copied. Raw manifests/logs (including any losses already in them) are preserved **unscored**.
- External source/material/model files are reverified against the plan, not copied into this run-root capsule. Preserve the immutable source/material and base alongside native weights for later verification. It is not a standalone model or material backup.
- No independent base-tensor dump or behavioral readout: frozen-base evidence remains the pinned trainer/LoRA manifest path. No conditional cognition, clean child lineage, or learning-success claim follows from completion.
- Origin remains `UNRESOLVED_LOCAL_HASHES_ONLY`; claim remains authored diagnostic, not child experience/clean lineage.
- Safe exclusive writes intentionally leave partial evidence on interruption or verification failure. Main must reconcile it; the helper never deletes, repairs, resumes or replaces it.
- Release is an observed full-check snapshot on the matched UUID, not a perpetual reservation guarantee. Main owns the external ledger and reallocation. PID reuse fails conservatively.

**EDIT-STOP.**
