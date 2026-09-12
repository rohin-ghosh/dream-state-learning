# Varied root0 terminal collector — EDIT-STOP

Owned only `/tmp/astra_collect_varied_pair_20260912.py` and this note. Live runner/tests unchanged. No native/GPU/network/Git execution. **Author also authored the runner/material; this is custody verification, not independent scientific analysis.**

## Main commands

Use the original native interpreter and immutable source CWD. Do not inherit a GPU reservation into the collector; Main prevents reallocation races and owns the ledger.

```bash
SOURCE="$HOME/astra_sources/dc2e9a3c11ccd9a3f10ea28513723bbfb8420247"
PY="$HOME/v2/venv/bin/python"
COLLECT=/tmp/astra_collect_varied_pair_20260912.py
cd "$SOURCE"
env -u CUDA_VISIBLE_DEVICES PYTHONDONTWRITEBYTECODE=1 "$PY" -B "$COLLECT" status

# Only when PID224587 is absent AND terminal exists. Optional outer hard stop shown.
env -u CUDA_VISIBLE_DEVICES PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
  timeout --signal=KILL 300s "$PY" -B "$COLLECT" finish
```

No arguments can change the pinned run, GPU, PID, source, or archive. `status` reads sealed plan/launch plus file-presence markers, **not terminal/fit/reduction contents or outcomes**, and does not import the driver or query GPUs.

## Pins / output

- Run: `$HOME/astra_diagnostics/astra_varied_memory_replay_20260912_attempt1/fits_root0_attempt1` on node3, native HOME `/localhome/local-rohing`.
- PID224587; GPU1 UUID `GPU-71e5a3e2-e9c8-5caf-70d8-73794ac34821`; launch2026-09-12T20:59:48.092375+00:00.
- Plan `2120bb93d0458b789bb3db408e57dd077f528cfadec35691b0e5fb27889756ca`.
- Runner `b58f65cd482bbd2d762edc030c7967a1ecd004829cf8271c74c15d3ca54bc8c7`.
- Launcher `d3053e0f7e9811e4bf6d34b5cb0d9e81119c8e9dd15b7abfe0a3b954e107ae38`.
- Collector `6de8f684fd05534b765ea9bbdfa3c074ff1769f646ba9b98ff3e9414b7a82674`.
- Safe-I/O dependency `/tmp/astra_collect_memory_only_20260912.py`, SHA `d2152c179ca9a6b9801933a480ed62cd203018868a52034e13676963787579eb`. Driver additionally binds its unchanged memory/fading helpers.
- Full vacancy checker `$SOURCE/gpu/astra_mini_sudoku_diagnostic.py`, SHA `a586b03bdb9c52f1061aa1e477ae983cc9d45ec0a2cd440642851fd8df8b609f`.

Exclusive outputs: `ROOT/run/main_release.json`, `ROOT/run/main_release.xml`, `/tmp/astra_varied_pair_root0_terminal_20260912.tgz`, and adjacent `.tgz.validation.json`. Capsule preserves metadata/logs/raw128 request-response pairs/reductions; excludes `.bin/.safetensors/.pt/.pth/.ckpt/.pyc/.pyo` and `__pycache__`. Weights remain native. Source/model/material trees are verified, not copied into the run-root capsule.

## Checks / cost limits

Finish first requires absent controller and terminal. It binds launch/plan/source/material/native-preparation/provenance, then checks current base hashes **once**, original parent file inventory/state **once**, and each published child inventory/state **once** using CPU adapter tensor helpers and the existing manifest validator. It never calls driver.run/prepare/verify/verify_fit, any reducer, tokenizer, model forward, or new generation. File identities/tree membership are captured before/after to detect mutation without repeating expensive inventories. Only original model **leaf-file** symlinks are accepted, matching the existing model-hash helper; link and target identity changes are tracked. Artifact/source directory aliases are rejected.

It verifies all six worker commands, ownership/time windows, sequential ordering, successful/cleanup receipts, sum of worker costs and terminal bounds. It checks existing raw request/response hashes, actual prompt bytes/input IDs versus sealed templates, output-ID validity/caps, capture identities/cleanup, native usage accounting, and existing reduction completeness/row IDs/source/cost/capture bindings. **No scores are recomputed or printed.** Prior `native_token_text_audit=True` receipts are bound; output token decode/re-encode is intentionally not rerun without a tokenizer. Main performs separate raw analysis later.

Full `check_free("1")` is called only for new collection, with launch/release UUID and XML agreement. Release JSON records observed UTC, PID absence, launch/terminal/XML/collector hashes, overlapping worker/controller costs, and full launch-to-observed-vacancy timing. These windows are **not additive**. A final metadata-only USTAR archive is hash-validated against current files.

The collector has a **300s SIGALRM** from finish invocation; the optional GNU timeout command also bounds blocking native-library calls. Declared launch+1500 end is **21:24:48.092375UTC**; launch+1500+300 end is **21:29:48.092375UTC**. These are not changed on late collection. `timing`/`completion_observation` explicitly record `late_observation`, `overrun_seconds`, original deadline and `budget_extended=False`. A late diagnostic collection may still preserve evidence under its own300s alarm, but records the missed declared interval rather than claiming compliance or expanding the budget. Main accounts for any real overrun.

Fully accounted/released failures remain `FAILED_PARTIAL_NO_RETRY`; missing panels are partial/not-started, never zero. Unaccounted workers or failed cleanup stop collection for manual reconciliation. A partial/orphan release/capsule set is never overwritten/retried. All four completed collection files permit read-only idempotent verification against current metadata/state; that returns historical-release verification without another GPU query, not a fresh vacancy guarantee. Interrupted collections retain partial files. No cancellation, run resume, autoqueue, or automatic scientific gate.

## CPU evidence

**17 integration cases passed +3 focused checks passed (20 distinct checks).** Integration fixture constructed all128 raw pairs and existing receipts, validated/packed/reopened the capsule, excluded weights, rejected raw-prefix/missing-call/worker-command/cost/UUID mutations, live/missing-terminal collection, orphan paths, changed metadata/archive, and unaccounted partials; retained failure status; verified marker-only status, late reporting, alarm cleanup, and no driver/model/tokenizer/reducer calls. Focused checks verified one base/one parent/two saved-child checks and safe model-leaf-link mutation detection/directory-link rejection. The initial once-only fixture had an eagerly evaluated fallback causing a local nonexistent-path read; corrected and rerun successfully, with no production code change for that fixture issue. Tests ran inline because no separate test-file scope was assigned. No native execution was used.

Quick reproducible CPU smoke (no native paths queried):

```bash
python3 -B - <<'PY'
import datetime, importlib.util, signal
from unittest.mock import patch
spec = importlib.util.spec_from_file_location('collector_smoke', '/tmp/astra_collect_varied_pair_20260912.py')
collector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(collector)
started = datetime.datetime.fromisoformat(collector.STARTED).timestamp()
assert collector.timing(started+1801)['overrun_seconds'] == 1
assert collector.timing(started+1801)['budget_extended'] is False
with patch.object(collector, 'status', return_value={'controller_present': True, 'terminal_available': True}), patch.object(collector, 'load') as loader:
    try: collector.finish_body(started)
    except ValueError: pass
    else: raise AssertionError('live controller accepted')
    loader.assert_not_called()
with patch.object(collector.signal, 'getitimer', return_value=(0.,0.)), patch.object(collector.signal, 'signal'), patch.object(collector.signal, 'setitimer') as timer, patch.object(collector, 'finish_body', return_value={'fixture': True}):
    assert collector.finish() == {'fixture': True}
    assert timer.call_args_list[0].args == (signal.ITIMER_REAL, 300)
    assert timer.call_args_list[-1].args == (signal.ITIMER_REAL, 0)
print('CPU smoke PASS')
PY
```

**EDIT-STOP. Main executes; later independent raw analysis remains separate.**
