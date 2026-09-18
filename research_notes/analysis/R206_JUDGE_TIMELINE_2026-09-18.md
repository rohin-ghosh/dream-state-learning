# R206 judge operational timeline — September18,2026 UTC audit

## R207 supersession — no legacy tau gate

**Authoritative R207 directive:30% vote mass is not the rule. Do not wait for the old failed tau.** The authorized task is Main's inference-only comparison of widegap step6250 against BT8k on20 constructed contrasts **held from fitting as DEVELOPMENT, not LOCKED or FINAL**, using relative ranking/top-k plus pixel novelty under the exact public registration. Neither the old null vote-mass tau nor the old rank200-quality operating point is a prerequisite for that task. No threshold is reconstructed from memory; this sidecar neither writes the experiment registration nor dispatches training/inference.

Fresh read-only operational recheck **2026-09-18T04:22:54.785800+00:00**: completion/public-report hashes unchanged; all four historical training PIDs remain absent; scoped judge-root Python process census empty. Historical completed work is ready to report below; R207 comparison outcomes have not been observed by this audit. Main owns resource selection and execution. No free-GPU or new-node SSH-success claim is made.

## Historical R201/R206 acceptance finding — not an R207 launch gate

**Historical contract finding: the100k candidate completed; it did not satisfy the previous threshold-based acceptance contract. This is not an R207 prerequisite.** Node4 direct read at **2026-09-18T04:11:19.472786+00:00** (2026-09-17T21:11:19.472801-07:00): all four historical training PIDs are absent; no same-user Python worker scoped to the judge root is observed. The100k report still has **tau=null**, no registered rank200-quality operating point, and `full_judge_usable=false`. Current legacy scalar-loader incompatibility is separately confirmed; it is **not the sole blocker**. No training, model loading, GPU queries, process control or learner edits were performed. Maintenance PID2656637 remains identity-alive,1200s cadence.

This is the requested finite sidecar, not a launch gate. The title uses the UTC audit date; **all timeline clock times below are September17,2026 PDT (UTC−07:00)**. UTC timestamps, exact epochs, process identities, file paths and hashes are preserved in `research_loop/workers/rohin204_maintenance_20260917/R206_JUDGE/TIMELINE.json`. Thus18:30PDT completion means **September18 01:30UTC**, not an event that has yet to happen on September18 PDT.

## Actual load → updates → calibration/report → terminal marker

| Candidate | Models actually loaded PDT | First optimizer update PDT | Last observed optimizer receipt PDT | Calibration/report complete by PDT | Completion/stop PDT |
| --- | --- | --- | --- | --- | --- |
| `released_all_v4` | 11:59:49.810 | 11:59:50.422 | 12:04:14.573; step1,300 | None observed | STOP 12:04:22.982 |
| `released_all_v6` | 12:15:22.202 | 12:15:22.811 | 12:22:14.470; step2,000 | 12:22:22.506 [mtime] | 12:22:22.546 |
| `bt_qwen_v2` | 13:20:19.679 | 13:20:22.493 | 13:41:15.526; step1,000 | 13:42:23.296 | 13:42:23.376 |
| `bt_widegap_v2` | 14:39:42.897 | 14:39:46.190 | 17:57:34.937; step6,250 | 18:30:36.967 | 18:30:37.388 |

- **released_all_v4, DistilBERT:** last durable progress is step1300, not a proven exact terminal update count. The owner stopped PID3941679 at12:04:22.983 for `FIRST_DISTINCT_SCENE_NEGATIVE_SAMPLER_SHORTCUT`; public receipt explicitly says exact final optimizer steps unknown and development audit had not started. No COMPLETED/public scoring report observed. Preserved evidence is not promotion evidence. V6's public supersession receipt says it did **not** inherit V4's defective run.
- **released_all_v6, DistilBERT:** PID4065988 completed2000 training-loop steps; selected checkpoint step100. Public report has tau=null and provisional/not-human-validated status. The12:22:22.507 report time is **file mtime**, not an invented calibration-start timestamp. Report producer permits aggregate numeric calibration summaries; this audit extracts no calibration curve or example content.
- **bt_qwen_v2, Qwen2.5-7B scalar BT:** PID387461 completed1000 updates, **8000 comparisons /16000 caption draws**; selected checkpoint step300 represents2400 comparisons, distinct from total work. Final update13:41:15.526; public report13:42:23.297; completion13:42:23.377. Public tau remains null. No standalone CPU scalar runtime readiness is demonstrated by its handoff.
- **bt_widegap_v2, Qwen2.5-7B scalar BT:** PID1055569 warm-started from BTv2's selected step300 with optimizer reset. Completed6250 updates and **100000 comparisons /200000 caption draws**, selecting step6250. Last optimizer update17:57:34.937 is **not** the completion time. Full-pool selection report file is timestamped18:28:26.301; public scoring report completed18:30:36.968; COMPLETED marker18:30:37.389.

**Calibration timing limit:** no independent calibration-start/end receipt was found among the bounded operational markers. Completion of the report establishes that calibration/report work had finished by that marker, not an isolated calibration duration. Last-update→report intervals are8.036s (V6),67.771s (BT8k),1982.030s/33m02s (widegap100k); these include possible checkpoint/model-selection/audit/I/O work and must not be relabeled pure calibration time. Widegap's final progress file mtime also follows its embedded optimizer timestamp; the table uses the document's optimizer `observed_unix`, not file mtime.

## Wall limits and GPU binding

All four admissions and preserved confinement receipts bind **node4/a4u8g-0105 physical2**, UUID `GPU-35dcea35-12bc-f2f3-d5d2-d2eaa8bacdd8` (runtime logical `cuda:0` where stated). These are historical operational/device receipts; **not a current GPU utilization or free-capacity measurement**.

| Candidate | Admitted run maximum | Admission end PDT | Experiment allocation end PDT | Observed load→completion/stop elapsed |
| --- | --- | --- | --- | --- |
| `released_all_v4` | 7,200s | 13:59:35.272 | Not separately receipted | 273.172s (4.55min) |
| `released_all_v6` | 6,000s | 13:55:07.667 | Not separately receipted | 420.344s (7.01min) |
| `bt_qwen_v2` | 6,600s | 15:10:11.665 | 15:17:55.706 | 1323.697s (22.06min) |
| `bt_widegap_v2` | 20,400s | 20:19:32.154 | 20:35:39.119 | 13854.491s (230.91min) |

BT8k reserves1200s and widegap1800s for calibration; these are **budget reservations**, not observed durations. Widegap outer systemd maximum is20400s; its existing handoff warns the outer unit may expire seconds before the admission wall. It completed well before either wall, so there is no evidence of this run being terminated by its wall. V4's terminal cause is the explicit sampler-repair stop, not expiry. Elapsed wall values include work/I/O and are not exclusive GPU-kernel execution time. Historical `lease_safe_end_unix` fields were only read; no current provider lease claim or extension is made.

## Freshness and current process status

The fresh remote read reproduces the earlier readiness report's four key hashes exactly:

| Public operational receipt under `bt_widegap_v2` | SHA-256 | Against prior readiness |
| --- | --- | --- |
| `training/PUBLIC_SCORING_REPORT.json` | `11f0daccc968e6c453638c89be97a0360bfa5685f25e1a74a0e5be608f9ae896` | unchanged |
| `COMPLETED.json` | `95e4f84bc591a0856d6271ad13efe784ca87aea09c2d3207fa307c6270f71f4c` | unchanged |
| `training/FULL_POOL_SELECTION_REPORT.json` | `ee0fecf39fdc58ae7df6b4e08ebbb20f0f6a7e373fa27259c83dff56ed7e4ab3` | unchanged |
| `training/throughput/006250.json` | `3da7e3e5d004fcd50762af70929e1bd9c8a69b033442808ba0280b6fdcb54f30` | unchanged |

The completion-bound `judge_config.json` reference hash is also unchanged (`5c3fb5fd35a26fb0585c09ee91ebc457c31871f591aabfb7a9f53fb05dbc86a8`); **its body was not opened**. Therefore the earlier “18:30PDT complete / tau=null / no quality point” conclusion is freshly reverified, not merely copied from a stale status or18:22 report-absent estimate.

At04:11:19UTC, historical PIDs3941679/4065988/387461/1055569 each have no `/proc/PID`; same-UID judge-root Python process census is empty. This does not establish that physical2 is free, nor that no unrelated service exists elsewhere. No process was signalled or restarted.

## Historical acceptance and loader status — not the R207 rule

- Current100k public report: `NO_FEASIBLE_HELDOUT_THRESHOLD`, thresholdnull; calibration example count3328. This is a public aggregate, not access to heldout examples or a calibration curve.
- Separate rank200-quality threshold: `BLOCKED_NO_REGISTERED_RANK200_QUALITY_OPERATING_POINT`, thresholdnull. Public audit says `BLOCKED_RANK200_QUALITY_POINT`, `full_judge_usable=false`, accepted0/1536, coverage0. No positive precision claim follows from zero accepts. Vote-mass q is not rank200 quality or human acceptance precision.
- `gpu/ny_caption_judge.py:920` still requires `NY_TRAINED_JUDGE_CONFIG_V1`; `load_cpu_judge` at943 reaches this validator before importing model libraries. Producer code declares `NY_WIDEGAP100K_SCALAR_JUDGE_CONFIG_V2`. A fresh **synthetic schema-only** call through AST-extracted current loader/validator functions rejects `provisional_trained_judge_only`; torch/transformers were never imported. No actual private candidate config or model was loaded. Projection-only fixtures also confirm private-row/curve/panel fields are dropped.
- Historical threshold-based acceptance remains unproven, but R207 does not require that contract or either old operating point. No recommendation to wait for failed tau is made. No real scorer→game roundtrip is claimed; the old synthetic game roundtrip remains only a fixture result. Main owns the authorized inference comparison and exact public registration.

## Evidence and boundary

Remote root: `/localhome/local-rohing/orch_r177_ampere_judge_20260917`; local owner receipts: `research_loop/workers/r177_caption_game_stage1_20260917/data_judge`.

Evidence under `research_loop/workers/rohin204_maintenance_20260917/R206_JUDGE/`:
- `REMOTE_OPERATIONAL.json` and `REMOTE_OPERATIONAL_FINAL.json`: bounded allowlisted operational fields, exact file metadata/hashes, process census. No raw training logs opened.
- `TIMELINE.json`: UTC/PDT timestamps, duration calculations, wall/GPU bindings, local receipt/source hashes and maintenance-service identity.
- `FRESHNESS.json`: exact old/new hash comparison, unchanged public null-threshold statuses, config-reference-only proof.
- `CPU_CHECKS.json`:3 standard-library-only metadata/schema assertions passed; no torch/transformers import or model call.
- `collect_operational.py`: exact read-only finite collector, restricted candidates and file names, scalar-field projection and128KiB per-file bound.

**Excluded throughout:** private contest/caption rows; sealed or FINAL score artifacts; calibration curves; reference-panel contents; private judge-config bodies; checkpoint tensor contents; live training/GPU/model calls; process writes/controls; lease changes; messages/scores to parents or children. Existing maintenance daemon remains running unchanged; no Main arm-table or learner/runtime edits.
