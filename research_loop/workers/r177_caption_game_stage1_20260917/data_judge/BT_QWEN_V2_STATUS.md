# Actual BT progress — September 17, 2026

## Completion update — 13:44 PDT

Completed13:42:23.376827PDT after1000 actual updates/8000 comparisons/16000 caption draws. Actual optimizer PID387461, distinct from wrapper PID387380; both are absent after completion. First optimizer13:20:22.493698PDT is independently available as the exact317-byte original at `evidence/BT_QWEN_V2_FIRST_OPTIMIZER_STEP.original.json`, SHAa05a52292aa390b6b4881a5e7eb9c7c5003f6897694b88534b17f4997fbc2791.

Selected step300 by registered model-selection macro Spearman0.1399395. Reused development-audit Spearman0.1658679,Brier0.00856446. Tau remains null,coverage0: **no usable calibrated acceptance judge and no promotion**. No lowered threshold, retry, changed objective or image training. Full safe report, original config and exact selected adapter are locally preserved; `BT_QWEN_V2_COMPLETED_HANDOFF.json` SHA310cff55b27a5f21669719d05a86960c383fef64d23387e8e825490d1547ad45 records pins and remaining scalar CPU-runtime dependency limitations. The earlier progress/ETA statements below are preserved historical snapshots, not current status.

## Earlier progress snapshot

Real Qwen2.5-7B-Instruct scalar-LoRA Bradley–Terry training started on node4 physical2, PID387461/startticks24456966. Model loaded13:20:19.679792PDT; first optimizer update13:20:22.493698PDT /20:20:22.493698UTC. Exact start/provenance pins: `BT_QWEN_V2_FIRST_STEP_HANDOFF.json`, SHA245374d7e3d48388b7062de6625ea58e95093f875ab911963184c49ff75f9d85.

By13:21:45.785071PDT:60 updates,480 comparisons,960 caption draws,86.105seconds since model load,5.57457 comparisons/second including the first selection sweep. Rough remaining fitting projection is22.5minutes at that early rate; calibration has1200seconds reserved, not measured. This suggests approximately13:44–14:04PDT only if the observed rate persists, not a completion receipt or promise. `BT_QWEN_V2_PROGRESS_STEP60.json` preserves exact measurements and assumptions.

First model-selection sweep only:19 contests/1216 rows, macro contest Spearman0.0324566, concordance0.510380; sampled top5-of64 vote mass0.197149 against0.184395 baseline. This is neither the final selected checkpoint nor independent-dev audit, literal full-contest top200, calibration, acceptance precision, or a usability claim. Do not promote before the completed pinned report/config; null tau must remain null if emitted.

Budget is fresh and independent of retired candidates:13:17:55.706446–15:17:55.706446PDT,7200seconds allocation,6600seconds run including1200seconds calibration reserve and60second admission/lease margin. Existing machine lease is unchanged. Budget SHA3553f0919a75dd1d935f199d0c1086782122534ba80ac73b205476b5977a6fc6. Prior source/evidence/walls remain unchanged. Tests:203 local passes/3 local Torch-dependent skips;27 receiving passes/no skips, actual tiny-Qwen gradient/reload and dataset provenance. Strict service proves target-minor1 open/close, seven foreign minors denied; fresh target idle capacity admitted inline.

No objective change, image-judge training, reference-panel release, hosted vision, learner modification, locked-validation or FINAL read. Distribution labels remain calibration/evaluation; acceptance meaning and thresholds are unchanged. No portable calibrated BT config exists yet; active training will emit `training/judge_config.json` and `training/PUBLIC_SCORING_REPORT.json` under `/localhome/local-rohing/orch_r177_ampere_judge_20260917/bt_qwen_v2`. Existing three-class `load_cpu_judge` does not yet support the new `NY_BT_SCALAR_JUDGE_CONFIG_V1` schema; do not silently use v6 or interpret scalar scores as calibrated q. V6 remains null-tau and unusable.
