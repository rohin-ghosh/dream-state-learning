# Current: R210 continuation; R209 history preserved

Current live mixture, exact rewind/AdamW/RNG receipts, ETA and checkpoint comparisons are in `R210_STATUS.md`, `R210_STATUS.json` and `R210_RECIPE.json`. Both candidates continue; no node2 operations (Jason owns enrichment). The R209 report below is historical and is not the current live recipe.

# R209 ovx5 training — actual pilot and live continuation

Observed UTC: 2026-09-18T04:51:40.186048+00:00. All timestamps below are September18,2026 UTC.

Two candidates are actually LOADED and have completed synchronized ≥300-second fitting pilots. Both continue with the SAME optimizer/RNG/pair cursor; neither1M run is claimed complete. Original failed R207 preload is preserved with zero updates; its repaired four-rank engineering collective passed before R209 launch.

| LoRA rank | Physical GPUs | LOADED UTC | Latest updates / pair draws | 5-minute pairs/s | Initial selection-inclusive finish UTC |
|---|---|---|---|---|---|
| 8 | 0–3 | 04:42:48.647771 | 210 / 13440 | 30.737 | 2026-09-18T13:47:08.798974+00:00 |
| 16 | 4–7 | 04:42:48.889361 | 210 / 13440 | 30.651 | 2026-09-18T13:48:38.966079+00:00 |

The finish predictions include measured original Spearman-selection cost, but exclude newly requested sidecar contention/diagnostics. They are predictions, not deadlines or completed results. Safety hard wall is23:00UTC, before the earliest retained lease bound; no lease action taken. Pairs are sampled with replacement, not1M unique comparisons.

## Exact treatments and data
- Both start at the selected6250 widegap-trained adapter, then train ALL-PAIR comparisons across all180 TRAIN contests with no wide-gap cutoff, tie target0.5 and capped vote-reliability weights without gap weighting.
- Rank8/alpha16 versus rank16/alpha32; rank16 copies56 original A/B block pairs, adds deterministic A directions and zero B columns, preserves scale2 and scalar head. Same initial function, not a claim of identical parameterization/trajectory. Fresh AdamW only at candidate birth; global batch64=16×4, LR3e-5.
- Source/model/TRAIN provenance verified; no FINAL data, private rows or per-example scores exposed to parents. Original frozen Qwen7B base retained. No tau or30% gate.

## Checkpoint diagnostics
The two strictly single-device sidecars intentionally share only their own candidate's physical0 or4 after current process-ownership and22GB free-headroom checks, with42% device-memory allocator bounds. No training process/code/optimizer is changed. They reuse the EXACT Main R207600case20contest private packet, case-ID digest `6763a62cf349e969c1dd7ecad0637c8718fef45572eced5a07a50406e3de66ba`, and Main scalar-loader/contrast-summary source. No scenes or rows are changed or sent to children. Each saved adapter receives both contrasts and the fixed model-selection Spearman panel; private reports stay under each candidate's `checkpoint_diagnostics/`.

Scope limitation: the running writer exports adapters at improving selection points, the pilot and completion. A non-improving scheduled Spearman evaluation does NOT export an adapter; no corresponding contrast result is claimed. Sidecars cover every actually saved checkpoint without restarting a valid candidate. Check `R209_REPORT.json` for actual completed/failed diagnostic receipts, not dispatch alone.

## Entrypoints and preserved receipts
- Training/admission: `ddp_pilot.py`, `four_gpu_admission.py`; immutable remote roots `/localhome/local-rohing/orch_r209_ovx5_allpair1m_rank8_20260918_candidate1` and corresponding `rank16` root.
- Diagnostics: `checkpoint_diagnostics.py`, `diagnostic_admission.py`; remote source `/localhome/local-rohing/r209_diagnostics_20260918t0449z`.
- Read-only observer: `python3 -B research_loop/workers/rohin205_new_nodes_20260918/ovx5/observe_r209.py`.
- Focused CPU tests:6 training/admission and2 checkpoint-readiness tests PASS locally/receiving. Actual rank-expansion and exact600case20contest digest checks PASS. Strict physical confinement probes passed for both training quartets and both diagnostic single-device services.

## Full-run continuation update

Observed 2026-09-18T04:54:05.105426+00:00. Both candidates automatically continued their exact pilot optimizer/RNG with no wait for Main. `R209_FULL_RUN_RECEIPT.json` records actual SUSTAINED_STARTED timestamps, latest progress, measured first-checkpoint diagnostics and explicit ETA assumptions. First step8 contrast+Spearman diagnostics completed04:53:39UTC for both ranks,600/600 scored with no skips. Diagnostics took approximately30s contrasts plus207s redundant Spearman recomputation; future saved selection checkpoints reuse their already-computed actual Spearman receipts rather than recomputing. Pilot-only checkpoint still receives its own Spearman. No training code/process was restarted or changed.

- Rank8: latest recorded update250 / 16000 comparisons. Updated conditional finish 2026-09-18T13:55:32.825321+00:00; assumes measured pilot fitting rate after finite diagnostics and conservatively adds remaining diagnostic walltime. If current temporary contention persisted throughout, rolling finish is 2026-09-18T15:42:28.080583+00:00. Neither estimate is a guarantee.
- Rank16: latest recorded update240 / 15360 comparisons. Updated conditional finish 2026-09-18T13:57:19.835773+00:00; assumes measured pilot fitting rate after finite diagnostics and conservatively adds remaining diagnostic walltime. If current temporary contention persisted throughout, rolling finish is 2026-09-18T15:41:01.029994+00:00. Neither estimate is a guarantee.
