# Conditional six-phase controller — EDIT-STOP

2026-09-12. **Ready for Main's CPU/native verification and launch.** Only the assigned driver, tests and this handoff were written. No native/model/GPU/network/Git calls or source edits were performed. **Do not rewrite Main's manifest or any phase plan.**

## Files and checks

- `/tmp/astra_conditional_readout_run_20260912.py` SHA256 **`e7a42bf3644d6e4ce5fbd1f129b37008cc455ea2088d3f65dbc18d27bd1ccd74`**.
- `/tmp/test_astra_conditional_readout_run_20260912.py` SHA256 `635aa77a2715fb379ec0bbbc337993e4988219429889b5a47ac1b06c5f653661`.
- **26 in-memory stub tests PASS**, including Main's exact manifest shape without a driver field, fixed ordering, native preflight failures, immutable inputs, all-state adapter/device contracts, unchanged worker limits, inclusive750s start gate, deadline/lease clamps, alarm propagation through simulated owned cleanup, partial evidence, failed cleanup/unaccounted workers, no retries, mismatched cost rejection and summary timing. They invoke no native module/model or real supervisor/GPU probe and write no fixture files.

The driver accepts Main's `source_root, phases, source_hashes, model_files, material_inventory, assay_version, prior_fit_full_reservation_seconds, controller_seconds, external_collection_margin_seconds, total_ceiling_seconds, device, status, generation_calls, candidate_forwards` manifest fields. Extra preparation metadata remains untouched. **Driver pin is supplied through required `--driver-sha256`; no `driver_sha256` manifest addition is needed.** The manifest pin binds all six plan hashes and readout/dependency source hashes. Source path/SHA are caller-provided, not hardcoded.

## Main-only commands

```bash
SOURCE="$HOME/astra_sources/90e181a4b0a02cfe655bc76ba480eac9166222b4"
ROOT="$HOME/astra_diagnostics/astra_conditional_behavior_20260912_attempt2/readouts_root0_attempt1"
MANIFEST=5a26f0da17d53518aa00c80bce3bfbfbe76ef61e65ea5ebc781f797dd33190a6
DRIVER=e7a42bf3644d6e4ce5fbd1f129b37008cc455ea2088d3f65dbc18d27bd1ccd74

PYTHONDONTWRITEBYTECODE=1 python3 -B /tmp/test_astra_conditional_readout_run_20260912.py
env -u CUDA_VISIBLE_DEVICES PYTHONDONTWRITEBYTECODE=1 \
  python3 -B /tmp/astra_conditional_readout_run_20260912.py verify \
  --source-root "$SOURCE" --runroot "$ROOT" \
  --manifest-sha256 "$MANIFEST" --driver-sha256 "$DRIVER"

# Main selects DEADLINE and LEASE_END as finite absolute Unix timestamps,
# logs the allocation and performs its full-device vacancy check before spawn.
CUDA_VISIBLE_DEVICES=0 PYTHONDONTWRITEBYTECODE=1 \
  python3 -B /tmp/astra_conditional_readout_run_20260912.py run \
  --source-root "$SOURCE" --runroot "$ROOT" \
  --manifest-sha256 "$MANIFEST" --driver-sha256 "$DRIVER" \
  --deadline "$DEADLINE" --lease-end "$LEASE_END" --allow-gpu
```

The installed readout SHA supplied by Main is `b4cd06137e3743186b885a809e1f2d3316fffd420a75c8c24838d6df72fa80df`; the inspected local API matches. Native phase plans themselves were not read/executed here. Their declared September26,2026 03:03UTC lease does not authorize a run beyond the tighter caller deadline/controller limit.

## Exact behavior and evidence

Fixed order: **OFF_generate → OFF_score → AUTH_generate → AUTH_score → DERANGED_generate → DERANGED_score**. Before the first worker, native CPU `verify` checks all six still-prepared roots, common source/base/material/control/device/lease contracts and identical generation/scoring adapter inventories per state. OFF has no adapter. Driver uses existing API `run`, `reduce`, then `summarize` only after all six technical completions. It never tests scientific scores to select another phase. Existing600s worker/180s load/120s call limits and owned-group cleanup are not patched.

`CUDA_VISIBLE_DEVICES=0` must be inherited from Main's controller spawn and remains unchanged during native verification, workers, reductions and CPU gaps. Effective cutoff is the minimum of start+4500s, supplied deadline, real lease−10s and sealed phase leases−10s. The parent alarm starts before native preflight and fires140s before this cutoff; existing supervisor `finally` owns active-worker cleanup. **Never starts a phase with less than750s remaining.** No shortened worker recipe, automatic split/retry or phase-plan lease rewrite.

Fresh outputs: `ROOT/controller/reservation.json`, `phases/STATE_PHASE.json`, `summary.json`, `terminal.json`. Phase JSON contains the full returned reduction plus process/supervision records, outside raw `run/data`. Original phase roots retain all raw outputs/stdout and native receipts. Terminal retains all attempts, available receipts, worker sum, full controller elapsed time, partial errors and summary if reached. Nothing prints incremental scientific outcomes; Main should wait for all six phases before inspecting them.

Technical failure stops with **PARTIAL**, preserves completed/partial phases, does not fill missing results with zero and exits nonzero. Preflight failure before creating `controller/` produces no worker or controller evidence and exits nonzero. Existing controller output or any prior phase `run/` is rejected: no resume. A terminal COMPLETE additionally requires six matching successful receipts, accounted owned processes, GPU process absence and wall/monotonic bounds. A saved summary is not sufficient if the final terminal is PARTIAL. Worker process absence is not Main's final fullcheck_free.

## Cost/claim scope

Main's envelope arithmetic is **464.397178 prior-fit full-reservation seconds +4500 controller +300 external margin =5264.397178s**, leaving135.602822s below5400s/90 A40-min. The driver checks this declared allocation, not the prior fit's native release artifact; Main owns that attribution and actual external/full-release ledger. Controller elapsed includes startup/import/verification/gaps/cleanup; worker sums are nested, not additive. External margin is not silently added to controller execution time. Existing sealed readout resource-budget metadata is preserved, not rewritten.

No source changes, additional scoring objectives, outcome-based scheduling, repeat attempts, new composition or L1 verdict. **EDIT-STOP. Main owns native acceptance, logging, allocation, launch and full release.**
