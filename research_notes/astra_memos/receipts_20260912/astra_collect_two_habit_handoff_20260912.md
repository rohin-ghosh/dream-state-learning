# Two-habit collector — EDIT-STOP

2026-09-12. Ready for Main execution; no known remaining implementation blocker. Collector frozen at 429 lines; no further expansion or tests performed after the stop request.

## Files and hash

- `/tmp/astra_collect_two_habit_20260912.py`
- SHA256: `544286384d5952a50f73ce4142d182c89900bd820b8126ce283147c49e85874e`
- This handoff: `/tmp/astra_collect_two_habit_handoff_20260912.md`

## Main-only execution

Run on node3 using the prepared native Python environment:

```bash
PYTHONDONTWRITEBYTECODE=1 "$PYTHON" -B /tmp/astra_collect_two_habit_20260912.py status
env -u CUDA_VISIBLE_DEVICES PYTHONDONTWRITEBYTECODE=1 "$PYTHON" -B /tmp/astra_collect_two_habit_20260912.py finish
```

Use an ordinary control shell without inherited `CUDA_VISIBLE_DEVICES=0` for finish: the existing vacancy helper can otherwise identify the collector itself as a GPU reservation.

Bound to seed0, GPU0, launch PID203151 at `2026-09-12T19:37:55.603911+00:00`, source `d1e70002d12052f6b7357d42cf5997aa915e16f7`, plan `af4988757fb01e93fe88e6f310c61656f26b2920d45c21561f6b035d208d11e9`, root `~/astra_diagnostics/astra_fundamental_two_habit_20260912_attempt1/seed0`.

Status is read-only artifact progress, without scoring/native binding/GPU checks. Finish requires controller absence and a terminal record, verifies native source/model/material/original parent/final adapters and complete captures against saved reductions and symmetric scores, and checks full GPU0 vacancy. It preserves failed/partial evidence without treating missing results as zeros.

Finish writes immutable seed0 `run/main_release.xml` and `run/main_release.json`, then packages the whole seed0 tree and sibling material only, excluding weights and bytecode. Adapter hash inventories remain in validation; weights stay on node. It records controller/worker times separately from the full launch-to-vacancy reservation. Outputs:

- `/tmp/astra_two_habit_terminal_20260912.tgz`
- `/tmp/astra_two_habit_terminal_20260912.tgz.validation.json`

One-shot only: existing release/capsule/validation outputs cause refusal, including orphan outputs. No overwrite, retry, deletion or automatic recovery; Main reconciles any partial output manually.

## Performed checks

- `PYTHONDONTWRITEBYTECODE=1 python3 -B /tmp/astra_collect_two_habit_20260912.py --help`: exit 0.
- In-memory stdlib unittest fixture suite via `PYTHONDONTWRITEBYTECODE=1 python3 -B -`: **12 tests PASS, 0 skips, 5.499 seconds**. No persistent test file created.
- Fixtures covered complete finish/archive membership/weight exclusion; partial failure retention; live-controller and missing-terminal gating; native-source failure; immutable/orphan outputs; plan/launch tampering; missing raw captures and symmetric-score tampering; read-only status; symlinks/duplicate/nonfinite JSON; XML UUID/process validation; archive escape/link/duplicate/corruption rejection; and excluded-weight mutation detection.
- Tests used temporary paths, synthetic captures, fixture tokenizer/verifiers/vacancy responses and real pure scoring/audit helpers. No model weights, remote access, GPU commands, production release files or production capsule were used/created.
- Final local `sha256sum` and `wc -l` confirmed the hash and 429 lines recorded above. No additional tests after the stop request.

## Limits

Main reports root0 COMPLETE with 32/32 scores for both arms; this collector author has not independently inspected that live result or executed native collection. Native finish and capsule transport remain Main's actions. No Git, repository edits, live-runner changes, launch or scientific promotion was performed. No additional gate is proposed here.
