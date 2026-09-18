# Caption-game judge: independent audit of the day — 2026-09-17 (Fable, two read-only agents, 20:57–21:07 PDT)

Question from Rohin (msg 206): "What is going on with the caption game? Why is training for the game literally taking the whole day?" Two readers: one over Astra's worker files on the VM clone, one over node 4's judge processes and logs. All times below UTC (PDT = UTC−7). Receipts are file paths and log timestamps as reported by the agents.

## Fable's synthesis

- **Elapsed:** ruling accepted 16:26Z (09:26 PDT); audit at 04:07Z (21:07 PDT) — 11 h 40 min. Judge GPU time inside that: ~4 h 25 min (DistilBERT 4 + 7 min; BT-8k 22 min; widegap 100k 198 min fit + 33 min inference). Roughly **7 h had no judge GPU work**: 2 h 35 min before the first GPU step (custody gates, three broken launches, 1 h 50 min waiting on 48 vision descriptions that never came), gaps of 11 / 58 / 57 min between runs, and 2 h 27 min after the last run with nothing launched.
- **Three sequential pivots on one A40:** DistilBERT 3-class (Spearman 0.03) → Qwen2.5-7B+LoRA scalar Bradley–Terry on 8k pairs (0.14–0.17) → wide-gap BT on 100k pairs (selection 0.29 on the 4,864-row sample, 0.265 on the full 101,418-row pool, audit 0.22; top-200-in-top-half 0.70). The 100k fit ran at 8.4 comparisons/s = 3 h 18 min, predicted at admission; the 8k run before it (1 % of pairs) was the doubling step Rohin's 10× rule says to skip, and nothing ran in parallel on the free slots.
- **Structural blocker, not a training-speed problem:** the registered acceptance criterion (≥0.30 positive-vote mass at ≥5 % coverage ≈ picking a contest's top ~3 % of ~20k captions) yields tau = null for every judge because each judge's calibrated q sits at the 0.16 base rate with std 0.02. The game wrapper fails closed without a numeric tau, a scalar-judge loader, real vision scenes and the similarity bundle all at once, so **no real caption has ever been scored**.
- **Other blockers:** judge loader accepts only the old 3-class schema (gpu/ny_caption_judge.py:875/922) while the BT judge emits a different schema — no export, no loader; the local Qwen2.5-VL vision service failed 7/7 requests on JSON/schema and died at its own 1-hour cap at 20:30Z, never restarted; four generation-profile attempts failed on code bugs; the judge GPU (node 4 slot 2) was handed to a control life at 03:20Z; **no judge candidate or owner has been declared since 01:30Z**; all caption code and the worker directory are untracked in the orch clone (HEAD 184 commits behind) — a VM or node loss erases the day's work.
- **What would make a scorable game tonight (proposal for Rohin's decision):** (1) a provisional acceptance rule — within-contest rank-based acceptance from the widegap ranker (e.g. top 5 % of a contest's captions by judge score) plus the pixel-novelty check, instead of the absolute vote-mass tau; (2) export the widegap adapter and write the scalar loader; (3) restart the vision service with the JSON contract fixed or the model's actual shape accepted; (4) run one development game end to end on the games node; (5) in parallel on the eight free A40s of the games node: a 10× pair budget on multi-GPU, and the image+caption VLM comparator Astra recommended; (6) commit and push the caption work now.

## Agent reports (verbatim, redacted)

### Source: Read-only audit of node 4 (a40r, 8x A40) over gpu/a40r_ssh.sh at 2026-09-18 03:57 UTC (20:57 PDT): nvidia-smi, ps/proc cmdlines+cwd, systemctl show, and file mtimes/receipts under /localhome/local-rohing/orch_r177_ampere_judge_20260917 (17 attempt dirs), orch_r177_local_qwen_vision_20260917, orch_r177_main_game_images_20260917_v1, /tmp/research_loop/workers/r177_caption_game_stage1_20260917/generation_profile; cross-checked against /Users/rohing/dream-state/research_loop/COORDINATION.md lines 32819-33033. Nothing modified. Note: the r177 worker source (research_loop/workers/r177_caption_game_stage1_20260917) is not in the local repo; it lives on the VM (/data/home/rohing/dream-state-orch per cpu_stage1/BUILDER_CPU_GATE.json).

**Timeline**

- 2026-09-17 16:25 — Ruling relayed: final experiment = caption game; node 4 slots 2/5/6/7 free for judge/vision.  
  receipt: research_loop/COORDINATION.md:32819-32822
- 2026-09-17 17:03 — Dataset splits written, 97 CPU tests pass; no judge trained, no GPU used.  
  receipt: research_loop/COORDINATION.md:32858
- 2026-09-17 18:12-18:18 — cpu_stage1 on node 4: DistilBERT-base (268 MB) staged, CPU tests, receiving proof. First node-4 activity, 1h47m after ruling.  
  receipt: orch_r177_ampere_judge_20260917/cpu_stage1/model/model.safetensors mtime 18:12:59; RECEIVING_CPU_PROOF.json 18:18:23
- 2026-09-17 18:35 — Rohin msg 167 'is the judge training?' -- answer No.  
  receipt: research_loop/COORDINATION.md:32868
- 2026-09-17 18:48:42 — released_all_v1 FAILED at CPU tests: 6 tests fail because receiving_cpu.py missing from shipped payload.  
  receipt: released_all_v1/CPU_FAILURE.json + CPU_TESTS.json ('6 failed, 133 passed')
- 2026-09-17 18:52:54 — released_all_v2 train unit started and exited same second: ValueError fresh_physical2_idle_admission (custody check itself failed).  
  receipt: systemctl show orch-r177-judge-train-6db5c688...: ExecMainStart=ExecMainExit=18:52:54, status 1; released_all_v2/OUTER_TRAIN.log
- 2026-09-17 18:56:12-18:56:27 — released_all_v3 train unit failed after 15 s: ValueError runtime_device_uuid_mismatch.  
  receipt: systemctl show orch-r177-judge-train-c61335fa...; released_all_v3/training/FAILED.json 18:56:26
- 2026-09-17 18:59:49 — released_all_v4: FIRST GPU TRAINING on GPU 2 (DistilBERT, 34,560 rows, batch 16); killed ~19:04Z by builder for a scene-fit sampler shortcut. ~4 min GPU.  
  receipt: released_all_v4/training/TRAINING_STARTED.json 18:59:49, FIRST_OPTIMIZER_STEP 18:59:50, last log 19:00:11; COORDINATION.md:32892 ('stopped at 12:04 PDT')
- 2026-09-17 19:08:33 — released_all_v5 passed CPU gate, never dispatched to GPU (abandoned).  
  receipt: released_all_v5/CPU_GATE.json status PASS_CPU_NOT_TRAINING; no OUTER_TRAIN_COMMAND.json
- 2026-09-17 19:15:22-19:22:22 — released_all_v6 DistilBERT 3-class trained 2,000 steps in 7 min; model-selection Spearman 0.044, audit 0.034 -> prior predictor.  
  receipt: released_all_v6/training/TRAINING_STARTED.json 19:15:22; COMPLETED.json 19:22:22; PUBLIC_SCORING_REPORT.json macro_contest_spearman 0.0437
- 2026-09-17 19:28:29 — Game image packet (3 cartoons) received on node 4.  
  receipt: orch_r177_main_game_images_20260917_v1/RECEIVED.json mtime 19:28:29
- 2026-09-17 19:30:57-19:31:15 — Local Qwen2.5-VL-7B vision service started on GPU 5, model loaded, listening port 8177, 3,600 s cap.  
  receipt: systemctl show orch-r177-slot5-bcb3cd71... ExecMainStart 19:30:57; runtime1/receipts/service_listening_*.json model_loaded_unix 1789673475
- 2026-09-17 19:32:31-19:35:45 — 7 image requests to vision service, ALL status=error (5 invalid_json_no_repair, 2 exact_visual_schema); 2.5-5.5 s each, 57-87 tokens generated.  
  receipt: runtime1/receipts/{9e554ca1,94324c90,742edd45,68ceec2e,e7646194,758b249d,cf495d90}.json status/error_code
- 2026-09-17 19:41:29 — released_all_v7 FAILED CPU tests (receiving_CPU_tests_pass).  
  receipt: released_all_v7/CPU_PROCESS.log
- 2026-09-17 19:42:38-19:44:56 — v6 selection diagnostic: q range 0.003 across 1,216 rows -> constant predictions confirmed.  
  receipt: v6_selection_diagnostic_v1/RESULT_OR_FAILURE.log macro_contest_q_range 0.0031
- 2026-09-17 19:52:00 / 19:53:48 — released_all_v9 and v10 FAILED CPU gate: actual_data_no_model_truncation (638 > 512 tokens).  
  receipt: released_all_v9/CPU_PROCESS.log; released_all_v10/CPU_PROCESS.log
- 2026-09-17 19:57:03-19:57:14 — Qwen2.5-7B-Instruct backbone pinned (15.2 GB) for the Bradley-Terry judge.  
  receipt: bt_qwen_model_v1/BASE_MANIFEST.json started_unix 1789675023, completed 1789675034
- 2026-09-17 20:09:54-20:09:59 — Caption generation-profile attempt 1 on GPU 6 FAILED (actual_CUDA_UUID).  
  receipt: systemctl show r177-caption-profile-1789675794; standalone_01/FAILURE_run.json
- 2026-09-17 20:11:51 — bt_qwen_v1 passed CPU gate (8,000 comparisons planned); never dispatched, superseded by v2.  
  receipt: bt_qwen_v1/CPU_GATE.json PASS_R171_CPU_NOT_GPU; no ADMISSION.json
- 2026-09-17 20:20:19-20:42:23 — bt_qwen_v2 Qwen-7B+LoRA scalar BT: 1,000 updates x 8 comparisons (batch_pairs 2, grad-accum 4), 6.37 comparisons/s, 2.77 M tokens; model-selection Spearman 0.140, concordance 0.548; selected step 300; tau none.  
  receipt: bt_qwen_v2/training/TRAINING_STARTED.json 20:20:19; throughput/001000.json; PUBLIC_SCORING_REPORT.json; COMPLETED.json 20:42:23
- 2026-09-17 20:30:25 — Vision service killed by its own RuntimeMaxSec=3600 (Result=timeout, status 15); wrapper raised strict_service_failed_preserved_no_retry; never restarted.  
  receipt: systemctl show orch-r177-slot5-... ExecMainExit 20:30:25 Result=timeout; cpu_stage3/OUTER_RUNTIME1.log
- 2026-09-17 20:36:29-21:04:51 — Generation-profile attempts 2-4 on GPU 6 all FAILED (TypeError receipt() name; padding_without_EOS_is_ambiguous; TimeoutError bounded_single_profile_deadline). Partial trials: ~11 tok/s at 2k-token prompt, ~2.2 tok/s at 12k.  
  receipt: systemctl show r177-caption-profile-{1789677389,1789678341,1789678703}; standalone_0{2,3,4}/FAILURE_run.json; standalone_04/TRIAL_12288_1_excluded_warmup_8.json
- 2026-09-17 21:32:39 — bt_widegap_v1 FAILED at CPU stage: ValueError contest_has_reliable_wide_gap (pair-schedule assertion).  
  receipt: bt_widegap_v1/FAILURE_1789680759295272233.json; CPU_PROCESS.log
- 2026-09-17 21:36:01-21:39:46 — bt_widegap_v2 staged (100 MB payload, 215 MB PAIR_PLAN), CPU gate 21:37:49, admission 21:39:32 (GPU 2 free, util 0), models loaded 21:39:42, first optimizer step 21:39:46. Budget admitted with predicted fitting 11,564 s + inference 3,263 s (max 20,400 s).  
  receipt: bt_widegap_v2/CPU_GATE.json, ADMISSION.json, training/TRAINING_STARTED.json, FIRST_OPTIMIZER_STEP.json, MEASURED_BUDGET_ADMISSION.json
- 2026-09-17 22:30 / 23:20 / 00:09 / 00:57 — widegap_v2 checkpoints at steps 1563/3125/4688/6250; model-selection Spearman 0.248 -> 0.261 -> 0.270 -> 0.288; steady 8.42 comparisons/s; fit ended 00:57:35Z after 11,872 s (3h18m), 100,000 comparisons, 25.7 M tokens.  
  receipt: bt_widegap_v2/training/progress/00{1563,3125,4688,6250}.json; checkpoints/step_* mtimes; throughput/006250.json seconds_since_model_load 11872
- 2026-09-18 00:58:59-01:28:26 — Full-pool selection inference over 101,418 rows: 1,766 s (29 min). Spearman 0.265, top-200-in-true-top-half precision 0.695.  
  receipt: bt_widegap_v2/training/FULL_POOL_SELECTION_REPORT.json measured_inference_seconds 1766
- 2026-09-18 01:30:37 — widegap_v2 COMPLETED: status PROVISIONAL_WIDEGAP_TRAINED_NOT_ACCEPTANCE_CLAIM; rank-200 quality audit BLOCKED (accepted 0/1536, coverage 0), tau NO_FEASIBLE_HELDOUT_THRESHOLD, stress-error acceptance 0/40 each. Total run 3h51m.  
  receipt: bt_widegap_v2/COMPLETED.json; training/PUBLIC_SCORING_REPORT.json; CALIBRATION_FIXED_BEFORE_AUDIT.json 01:29:59
- 2026-09-18 01:30:37-03:20:44 — GPU 2 idle 1h50m; then reassigned to R201 SCALE_physical2 continual child (not judge work).  
  receipt: ps lstart pid 3429712 'Fri Sep 18 03:20:44 2026', cwd orch_r201_node4_20260918/node4/R195_FLEET/SCALE_physical2
- 2026-09-18 03:57 — Audit: no judge/caption/vision process alive; no judge export, game runner or scoring artifact created on node 4 after 01:00Z; GPU 5 holds an r188 child, GPU 7 empty.  
  receipt: nvidia-smi --query-compute-apps (9 PIDs, all orch_r125_continual_guard/readout); find -newermt '2026-09-18 01:00' judge|game|caption|export -> empty

**Stages**

| stage | wall-clock (min) | GPU | result |
|---|---|---|---|
| Ruling to first GPU step (CPU staging, tests, three failed launches v1-v3) | 155 | none | No GPU work 16:25-18:59Z; v1 payload missing a file, v2 idle-admission check failed, v3 UUID check failed. |
| DistilBERT v4 (3-class humour + scene-fit) | 4 | node 4 GPU 2 | Killed ~19:04Z for scene-fit sampler shortcut; not promotable. |
| Gap: v5 staged/abandoned | 11 | idle | 19:04-19:15Z no GPU work. |
| DistilBERT v6, 2,000 steps, 34,560 rows | 7 | node 4 GPU 2 | Spearman 0.044 (model selection) / 0.034 (audit); constant predictions; prior predictor. |
| Gap: diagnostic, v7/v9/v10 CPU failures, Qwen base pin, bt_qwen_v1 gate | 58 | idle | 19:22-20:20Z no GPU work on the judge slot; pivot to Qwen-7B Bradley-Terry. |
| bt_qwen_v2 Qwen2.5-7B + LoRA scalar BT, 8,000 comparisons | 22 | node 4 GPU 2 | Spearman 0.140, concordance 0.548; 6.4 comparisons/s; only ~1% of available pairs (undertrained). |
| Gap: widegap_v1 CPU failure + v2 staging/gates | 57 | idle | 20:42-21:39Z no GPU work; pair-schedule assertion failed once. |
| bt_widegap_v2 fit: 6,250 steps x 16 pairs = 100,000 comparisons, 25.7 M tokens, lr 3e-5, max_len 512 | 198 | node 4 GPU 2 (single A40) | 8.42 comparisons/s (0.53 steps/s, ~3.7k tokens/step); model-selection Spearman 0.288, top-half precision 0.709, loss 0.65 -> 0.50. Duration was predicted at admission (11,564 s). |
| bt_widegap_v2 selection inference + calibration + audit | 33 | node 4 GPU 2 | 101,418-row full-pool inference 29 min (Spearman 0.265); rank-200 operating point BLOCKED, tau none, coverage 0. |
| Post-completion: export / game integration / scoring | 147 | GPU 2 idle 110 min then taken by R201 child | Nothing launched 01:30-03:57Z; no export or scoring artifact on node 4. |
| Local Qwen2.5-VL-7B vision service | 59 | node 4 GPU 5 | 7/7 requests errored (JSON/schema parsing); killed by own 3,600 s cap at 20:30Z; not restarted; GPU 5 now hosts an r188 child. |
| Caption generation-speed profile (4 attempts) | 55 | node 4 GPU 6 | All 4 failed on code bugs/timeouts (UUID check, receipt() TypeError, pad/EOS assertion, deadline); no published profile. |

**Current state.** No judge training is running and none has since 01:30:37Z (18:30 PDT). The finished artifact is bt_widegap_v2/training/checkpoints/step_006250 (Qwen2.5-7B + rank-LoRA scalar head, 10 MB adapter, 2.53 M trainable params) with judge_config.json; status PROVISIONAL: model-selection Spearman 0.288 on the fixed 4,864-row sample, 0.265 on the full 101,418-row pool, top-200-in-true-top-half precision 0.70, but rank-200 acceptance operating point BLOCKED (0/1536 accepted), tau NO_FEASIBLE_HELDOUT_THRESHOLD, stress-attack acceptance 0/40 each. It can rank captions within a contest weakly; it cannot accept/reject. No export/runtime integration into gpu.ny_caption_game exists on node 4 and no game episode has been scored. The vision service has been down since 20:30Z (7.5 h) after every request failed on JSON parsing. Node 4 GPUs now: 0-4 and 6 hold R201/r179/r188 continual children (GPU 2, the judge slot, was taken by SCALE_physical2 at 03:20:44Z), GPU 5 an r188 child, GPU 7 empty. Judge GPU-busy time today ~4h24m of the 11h32m since the ruling (38%).

**Blockers**

- No portable judge export or wiring of step_006250 into gpu.ny_caption_game; game scoring has never run (no artifacts after 01:00Z on node 4).
- Judge has no acceptance operating point: rank200_quality_audit BLOCKED (accepted 0/1536, coverage 0), tau NO_FEASIBLE_HELDOUT_THRESHOLD -- usable only as a within-contest ranker (Spearman ~0.27-0.29).
- Local Qwen2.5-VL-7B vision service down since 20:30Z; all 7 image requests errored (invalid_json_no_repair / exact_visual_schema); unit hit its 3,600 s cap and was not restarted; GPU 5 reassigned to an r188 child.
- Judge slot lost: GPU 2 reassigned to R201 SCALE_physical2 at 03:20:44Z; only GPU 7 free on node 4 for judge/vision/game work.
- Caption generation-speed profile never completed (4 failed attempts on GPU 6), so game token budgets remain estimates.
- r177 worker source is VM-only (/data/home/rohing/dream-state-orch), not in the local repo checkout -- verify it is pushed.

**Why slow**

- The final run was designed to take ~4 h: a 7B backbone on ONE A40, batch 16 pairs (32 sequences, ~3.7k tokens/step) runs 0.53 steps/s = 8.4 comparisons/s, so 100,000 comparisons = 11,872 s (3h18m) plus a 29-min full-pool inference; the admission receipt predicted 11,564 s fitting up front (MEASURED_BUDGET_ADMISSION.json). GPU utilisation was fine (~55-60% of A40 bf16 peak); the slowness is the model size x pair count x single GPU, not a stall.
- Everything ran strictly serially on one GPU slot: 17 attempt directories, only 4 reached GPU (one killed after 4 min), 8 died at CPU/admission gates (missing file, idle-admission check, UUID mismatch, CPU tests x2, token truncation 638>512 x2, wide-gap assertion), 2 abandoned after passing. Node 4 slots 6/7 and node 2's eight A40s (free from 22:12Z) were never used for a parallel judge arm.
- Three design pivots run one after another: DistilBERT 3-class (0.044, 7 min) -> Qwen BT 8k pairs (0.14, 22 min, ~1% of pairs) -> Qwen BT wide-gap 100k (0.27-0.29, 3h51m). Launching the 100k run at 20:20Z instead of the 8k run would have finished ~23:40Z; launching 8k and 100k in parallel on two slots would have cost nothing.
- Idle gaps on the judge slot: 2h35m from ruling to first GPU step (CPU staging, custody gates, 3 broken launches), then 11 + 58 + 57 min between GPU runs, then 2h27m after completion with no export/scoring launched -- ~7 h of the 11.5 h had no judge GPU work.
- Per-attempt custody overhead: each attempt re-ships a ~100 MB payload (215 MB pair plan for widegap), reruns 56-139 CPU tests, a systemd confinement probe and a separate train unit (3-7 min before any GPU step), and two of the failures (v2 fresh_physical2_idle_admission, v3 runtime_device_uuid_mismatch) were the gates themselves misfiring.
- In-run fixed costs: 5 model-selection evaluations (~85 s each), 5 adapter checkpoints, a 1,766 s full-pool inference over 101,418 rows, isotonic calibration and dev audit (33 min total after the last step); plus a 1,800 s calibration reserve in the budget.
- Side lanes wasted GPU hours without output: the vision service ran 59 min with 7/7 request errors and died on its own 1 h cap; four generation-profile attempts on GPU 6 (55 min) all failed on code bugs.

**Open questions**

- Has step_006250 been exported/wired into the game wrapper anywhere other than node 4 (e.g. on the VM)? Nothing on node 4 after 01:00Z shows it.
- Who reassigned GPU 2 to R201 SCALE_physical2 at 03:20:44Z, and was the judge slot deliberately released or lost by default?
- Is the vision service meant to be restarted (and its 3,600 s cap lifted), and are the invalid_json_no_repair / exact_visual_schema errors a prompt/schema bug in ny_caption_vision.py or a model-output issue?
- Is Spearman ~0.27-0.29 accepted as the game's scorer for now, or is a bigger/parallel run planned (more pairs, larger batch, multi-GPU) -- and if so on which free slots (node 4 GPU 7, node 2)?
- Why was the 8k run (1% of pairs) launched at all instead of the 100k run, given the 10x-per-rung steer?
- Is the r177 worker source (VM-only path) pushed to the repo? It is absent from the local checkout.

### Source: Orchestrator repo clone on the VM (/data/home/rohing/dream-state-orch, read via gpu/nvl_ssh.sh): research_loop/workers/r177_caption_game_stage1_20260917/ (status/receipt JSON + markdown, data_judge/evidence/*, portable/*, vision/*, pixels_game/*, similarity_runtime/*), research_loop/COORDINATION.md (86 caption/judge/BT/widegap/pixels lines; entries extracted by header), research_notes/analysis/R187_CAPTION_ACTION_POLICY_2026-09-17.md, research_loop/workers/rohin201_c2_clones_20260917/caption_readiness/STATUS.md, gpu/ny_caption_*.py mtimes. git log gave nothing: clone HEAD is de1fc4b7 (2026-09-16 03:00 PDT), 0 ahead / 184 behind origin/main, all caption code and the worker dir are untracked (3624 untracked files), so file mtimes (UTC) and receipt unix times are the timeline evidence. Supplementary read-only check on node4 (gpu/a40r_ssh.sh): nvidia-smi and the judge root /localhome/local-rohing/orch_r177_ampere_judge_20260917/ (bt_widegap_v2/training/PUBLIC_SCORING_REPORT.json, FULL_POOL_SELECTION_REPORT.json). All times below are UTC; PDT = UTC-7. Audit performed 2026-09-18 03:57-04:07 UTC.

**Timeline**

- 2026-09-17 16:22 — Four forwarded final-run design docs land (incl. NEW_YORKER_JUDGE_PIXELS_AND_THREE_ARM_TEST.md, which specifies 'start with a pretrained text model with a classification head', pairwise BT as the alternative).  
  receipt: research_notes/forwarded/final_run_2026-09-17/*.md mtime 16:22:00Z
- 2026-09-17 16:26 — Rohin160 accepted: caption game Stage1 is top build priority; parallel owners (Main runtime, Ampere data/judge, Gauss pixels/game). Dataset download starts the same minute; node4 physical2 reserved for judge, physical5 vision, 6/7 dev lanes.  
  receipt: COORDINATION.md '## [Builder — Rohin160 accepted...] 09:26PDT'; data_judge/private/DATASET_PIN.json mtime 16:26:37Z
- 2026-09-17 16:37 — Rohin161 correction written into CURRENT_BUILD_RULES.md (local Qwen vision; PARENTED vs UNPARENTED both learning; FINAL no parents).  
  receipt: r177_caption_game_stage1_20260917/CURRENT_BUILD_RULES.md ('Main, September 17, 2026, 09:37 PDT')
- 2026-09-17 16:39-16:55 — Pixels/game core (gpu.ny_caption_pixels, gpu.ny_caption_game) code-complete on CPU: 75 tests pass, API 'ready_for_Main_integration'.  
  receipt: pixels_game/STATUS.json mtime 16:39:06Z; gpu/ny_caption_game.py + ny_caption_pixels.py mtime 16:55:02Z
- 2026-09-17 16:40-16:47 — Data preparation1 fails (undecodable image), preparation2 fails (contests with no unique captions after duplicate quarantine); preparation3 + image task packets produced. Judge staged as DistilBERT 3-class + 2-class scene-fit.  
  receipt: data_judge/PREPARATION1_FAILURE.json 16:40:39Z; PREPARATION2_FAILURE.json 16:44:17Z; MINIMUM_JUDGE_DEPENDENCIES.json 16:44:17Z; IMAGE_TASKS_*.private.json 16:47:11Z
- 2026-09-17 17:14-18:22 — Judge CPU staging on node4 (122 tests) but training inputs blocked: 48-contest candidate waits on local-Qwen scene descriptions; 0 descriptions attached; status ACTUAL_NODE4_CPU_PASS_REAL_VISION_AND_TRAINING_INPUTS_PENDING.  
  receipt: data_judge/READINESS_20260917_v1.json 17:14:08Z; READINESS_20260917_v2.json 18:22:59Z (observed_utc 18:22:59, actual_descriptions_attached=0); DESCRIPTIONS_REQUIRED_20260917_v1.md 18:21:22Z
- 2026-09-17 18:37 — Rohin167 relay: 'No, the judge has not yet started training' - blocker was waiting for 48 Qwen descriptions; dependency removed, switch to released canny/location/entities descriptions for all 180 joinable train contests (82 excluded).  
  receipt: COORDINATION.md '## [Builder — Rohin167 judge: dependency removed...] 11:37PDT'; CURRENT_BUILD_RULES.md section 'September17 11:37PDT'
- 2026-09-17 18:39-19:31 — Local Qwen2.5-VL-7B vision service: coordination request 18:39Z, weights download 18:47Z, CPU/device proofs 18:51-19:02Z, model loaded 19:31:15Z on physical5.  
  receipt: vision/COORDINATION_REQUEST_20260917T1839Z.md; vision/DOWNLOAD_STARTED_1789670848244405540.json; SERVICE_STATUS_20260917T1938Z.json model_loaded_unix=1789673475
- 2026-09-17 18:43-19:22 — Similarity/novelty (pixels) calibration: MiniLM acquired, 300 LLM-labelled pairs (77 provider calls, 109,348 tokens), rho 0.977, held-out false merges 0/30, false splits 8/30; public bundle exported.  
  receipt: similarity_runtime/AMPERE_INPUT_HANDOFF.md 18:43Z; campaign1/calibration1/PUBLIC_METADATA.json; PUBLIC_INTEGRATION_HANDOFF1.json 19:22:20Z
- 2026-09-17 18:46-18:59 — Released-description judge receiving attempts v1 (133 pass / 6 missing test harness, no GPU), v2 (142 pass), v3 (runtime-UUID repair), v4 gate pass.  
  receipt: data_judge/evidence/CPU_TESTS_R167_RELEASED_v1..v4.json 18:46-18:57Z; COORDINATION '## [Builder/Ampere — R167 exact receiving-v3 launch gate] 11:57PDT'
- 2026-09-17 18:59:49 — First actual GPU judge training (DistilBERT v4, 34,560 sampled rows, 180 contests) starts on node4 physical2, PID 3941679; step 600 by 19:01:56Z.  
  receipt: MAIN_JUDGE_FIRST_STEP_1902.json started_unix=1789671589.81; MAIN_JUDGE_STATUS_1901.jsonl
- 2026-09-17 19:04:22 — v4 stopped at step 1300 after Main found scene-fit negatives always take the first different scene (scene-identity shortcut); not promotable.  
  receipt: data_judge/evidence/V4_STOPPED_FOR_SAMPLER_REPAIR.json stopped_unix=1789671862.98; data_judge/V4_PROMOTION_BLOCKED.json
- 2026-09-17 19:15:22-19:22:22 — Corrected DistilBERT v6 trains 2,000 batches (32,000 humor draws) in 7 min. Result: disjoint dev audit Spearman 0.034 (selection 0.044), Brier 0.0149, tau=None, 0 accepted / 0% coverage. Not usable.  
  receipt: FIRST_SCORING_REPORT_20260917.md; data_judge/evidence/RECEIVING_V6_OBSERVATION_1789672960306252378.json (19:22:40Z); portable/released_all_v6/PUBLIC_SCORING_REPORT.json
- 2026-09-17 19:18-19:35 — Main's real-tools smoke CLI (gpu.ny_caption_stage1_tools) wired: 371 CPU tests + 66 subtests; requires frozen judge with numeric tau, vision packet, similarity bundle - none available. 3 development images released to node4 at 19:28Z.  
  receipt: smoke_wiring/CPU_GATE_20260917T1920Z.json; REAL_TOOLS_SMOKE.md; smoke_wiring/image_release1/COMPLETED.json received_unix=1789673309.6
- 2026-09-17 19:32-19:38 — Vision service smoke: 7 real generations on the 3 released images -> 5 invalid_json_no_repair + 2 exact_visual_schema failures; 0 canonical scenes. Status MODEL_LOADED_LISTENING_BUT_VISUAL_CONTRACT_FAILED; service deadline 20:30:25Z.  
  receipt: vision/SERVICE_STATUS_20260917T1938Z.json (errors.invalid_json_no_repair=5, exact_visual_schema=2); vision/GAME_ONLY_INTERFACE.md
- 2026-09-17 19:29-19:33 — Judge failure source audit: no label/gradient bug; selected checkpoint step100 saw ~1,564 distinct rows; pooled log-loss selection ignores rank. Threshold oracle: perfect ranking WOULD meet 0.30/5% (top23 mass 0.348), so criterion is feasible in principle.  
  receipt: judge_failure_audit/REPORT.md (19:29 UTC); data_judge/evidence/THRESHOLD_ORACLE_V6_1789673606904668697.json 19:33:26Z
- 2026-09-17 19:37-19:57 — Soft-label contrast branch V7/V8/V9/V10 staged; V7 CPU gate fails (clean env lacked pytest) at 19:41Z; V9/V10 CPU-only. Whole branch retired at 19:57Z by Rohin170/171 supersession (scalar Bradley-Terry instead). No GPU used.  
  receipt: data_judge/NEXT_CANDIDATE_V7.md 19:37Z; V7_CPU_SUPPORT_REPAIR.md; evidence/CPU_PROCESS_V7_1789674088774649165.json; data_judge/R171_SUPERSESSION.json 19:57:02Z
- 2026-09-17 19:47-19:59 — Rohin168 answered (recommend separate image+caption VLM comparator); Rohin170/171 read: image judge on HOLD until text pairwise works; Ampere redirected to Qwen2.5-7B+LoRA scalar BT at 19:52Z; base snapshot found on node4 19:53Z.  
  receipt: COORDINATION '## [Builder/Astra — Rohin168...] 12:47 PDT' and '## [Builder/Astra — Rohin170/171...] 12:59 PDT'; evidence/R171_PRETRAINED_STAGING_PROBE_1789674810400703293.json
- 2026-09-17 20:08-20:20 — BT ranker code written (bt_ranker.py, bt_receiving.py, bt_ops.py, v2 budget), 203 local + 27 receiving tests; CPU/provenance gate 20:19:02Z; new 2h allocation 20:17:55-22:17:55Z.  
  receipt: data_judge/bt_ranker.py 20:09:50Z; evidence/CPU_R172_BT_BUDGET_v2.json 20:17:55Z; COORDINATION '## [Builder/Ampere — R172 fresh BT CPU/provenance gate] 13:19PDT'
- 2026-09-17 20:20:19-20:42:23 — bt_qwen_v2 (frozen Qwen2.5-7B + 2.53M scalar/LoRA params) fits 1000 updates / 8,000 comparisons in 22 min (~6.3 comps/s). Selected step300: selection Spearman 0.140, audit 0.166, tau=null (NO_FEASIBLE_HELDOUT_THRESHOLD), 0 accepted.  
  receipt: evidence/BT_QWEN_V2_FIRST_OPTIMIZER_STEP.original.json; portable/bt_qwen_v2/PUBLIC_SCORING_REPORT.json completed_unix=1789677743.3; data_judge/BT_QWEN_V2_COMPLETED_HANDOFF.json 20:44:46Z
- 2026-09-17 20:08-21:04 — Parallel: generation-throughput profile on node4 GPU6 (11 trials): 23.3 tok/s per life at 2k input, 5.0 tok/s at 12k; GPU6 released.  
  receipt: generation_profile/attempt4/PROFILE_REPORT.md; COORDINATION '### [Builder — C2 observer actually running...] 14:28 PDT'
- 2026-09-17 21:07-21:17 — Next plan frozen (100k mean-rating wide-gap BT, warm-start step300, 6h budget); rank200 CPU diagnostic v1-v3 completes 21:17Z: rank200 captions carry mean positive-vote mass 0.342 at 3.79% coverage (so 0.30/5% is a 'top ~3% of a contest' bar).  
  receipt: data_judge/NEXT_WIDEGAP_PLAN.md 21:07:21Z; rank200_reference_v3/PUBLIC_DIAGNOSTIC.json completed_unix=1789679873.4; COORDINATION '## [2026-09-17 14:27:39 PDT] [Builder/Ampere] Text100k successor...'
- 2026-09-17 21:25-21:38 — Widegap code v1 written; V1 pair prep fails before GPU (one contest has a single caption with >=20 votes) at 21:32Z; V2 (180 roster/179 pairable) written 21:34Z; own CPU+provenance gate PASS 21:38:47Z.  
  receipt: data_judge/bt_widegap.py 21:29:40Z; evidence/WIDEGAP_ELIGIBILITY_DIAGNOSTIC_V1.json 21:33:24Z; bt_widegap_v2.py 21:34:35Z; COORDINATION '## [2026-09-17 14:38:47 PDT] [Builder/Ampere] WIDEGAP V2 own CPU+provenance gate PASS'
- 2026-09-17 21:39:46 — bt_widegap_v2 first optimizer step on node4 physical2 (PID 1055569); 8-update pilot measures 8.64 comps/s -> nominal finish projected 01:47Z, conservative 03:04Z; sustained fitting admitted 21:42Z.  
  receipt: evidence/WIDEGAP_V2_FIRST_OPTIMIZER_STEP.original.json observed_unix=1789681186.19; evidence/WIDEGAP_V2_MEASURED_BUDGET.original.json; data_judge/WIDEGAP_V2_SUSTAINED_START_HANDOFF.json 21:42:27Z
- 2026-09-18 00:09:34 — Model-selection sample at 75,008 comparisons: macro mean-rating Spearman 0.270 (19 contests / 4,864 rows) - the '0.27' number; Ampere status at 00:16Z: step 4910/6250, 8.36 comps/s, game scoring blocked (no calibration; loader expects two-classifier schema).  
  receipt: evidence/JUDGE_STATUS_1789690582820510155.json (model_selection_completed_pdt 17:09:34, macro_mean_rating_spearman 0.2701); COORDINATION '## [Builder/Ampere → Main — existing text judge live; scoring not yet usable] 17:18 PDT'
- 2026-09-18 00:27-01:00 — Game-side code lands: R187 child-selected caption_batch action policy (gpu/ny_caption_action_policy.py), Stage1 development bridge (gpu/ny_caption_development.py), R190-R193 caption runner (468 CPU tests + 395 subtests). CPU-tested only; 'not a live game launch'.  
  receipt: gpu/ny_caption_action_policy.py mtime 00:27:23Z; gpu/ny_caption_development.py 00:55:53Z; research_notes/analysis/R187_CAPTION_ACTION_POLICY_2026-09-17.md; COORDINATION '## [Builder/Main — R190–R193 integrated code...] 18:00 PDT'
- 2026-09-18 00:57:34 — Widegap fitting complete: 6,250 updates / 100,000 comparisons / 200,000 caption draws in 11,872 s since model load (3h18m); final BT loss 0.496; 219,712 model examples, 25.7M tokens charged.  
  receipt: evidence/WIDEGAP_V2_OBSERVATION_1789694532888414451.json -> training/progress/006250.json observed_unix=1789693054.94, seconds_since_model_load=11872
- 2026-09-18 01:27 — Main answers Rohin194: caption game NOT ready for scored play - last calibrated tau is null; widegap report not yet emitted at 01:22Z inspection; gpu/ny_caption_judge.py:920 accepts only the legacy classifier schema; 95 game/wiring fixture tests pass but no real judge round trip.  
  receipt: COORDINATION '## [Builder/Main — Rohin194 answer: caption game NOT ready for scored play] 18:27 PDT'; evidence/WIDEGAP_V2_OBSERVATION_1789694532888414451.json (01:22:12Z)
- 2026-09-18 01:28:26-01:30:37 — Widegap full-pool selection report (101,418 rows, 1,766 s inference): Spearman 0.265, top200-in-true-top-half precision 0.695. PUBLIC_SCORING_REPORT: audit Spearman 0.222 (6 contests/1,536 rows), q_mean 0.156 / q_std 0.021, tau=null NO_FEASIBLE_HELDOUT_THRESHOLD, rank200-quality threshold null, 0/1536 accepted; COMPLETED.json written.  
  receipt: node4 /localhome/local-rohing/orch_r177_ampere_judge_20260917/bt_widegap_v2/training/FULL_POOL_SELECTION_REPORT.json (01:28:26Z) and PUBLIC_SCORING_REPORT.json (completed_unix=1789695036.97); COMPLETED.json 01:30:37Z
- 2026-09-18 02:28-02:35 — Independent caption-readiness sidecar confirms: NOT USABLE; 'the blocker is not loader-only' - neither registered threshold exists; synthetic PARENTED/UNPARENTED submit->restore->replay passes with fixture tau 0.7 only. Main logs 'judge still blocked' at 02:35Z.  
  receipt: research_loop/workers/rohin201_c2_clones_20260917/caption_readiness/STATUS.md (observation 02:28:49Z); COORDINATION '## [Builder/Main — R201 fixed C2 source; four launch operators executing; judge still blocked] 19:35 PDT'
- 2026-09-18 03:58 — R206 allocation: new node ovx5 = games (Leibniz); 'Caption capacity remains reserved on the new nodes pending a calibrated judge.' No next judge candidate declared.  
  receipt: COORDINATION '## [Builder/Main — R205 console ACT repair tested; R206 allocation received] 2026-09-18 03:58 UTC'
- 2026-09-18 04:07 — Audit check: node4 GPU2 (judge slot, UUID ...35dcea35) now runs an R195/R201 control life (PID 3735657, gpu.orch_r125_continual_guard, SCALE_physical2/withdrawn/control), not a judge; no judge directory newer than bt_widegap_v2 (01:30Z). Orch clone: 0 commits since Sep 16 03:00 PDT, 3624 untracked files, all caption modules/tests/worker dir untracked, 184 behind origin/main.  
  receipt: nvidia-smi --query-compute-apps on node4 at 04:07:18Z; ls /localhome/local-rohing/orch_r177_ampere_judge_20260917/; git status -sb in /data/home/rohing/dream-state-orch ('## main...origin/main [behind 184]', untracked_r177=23)

**Stages**

| stage | wall-clock (min) | GPU | result |
|---|---|---|---|
| Dataset pin, download, preparation (3 attempts) and image task packets | 21 | none (CPU on VM) | Pinned HF newyorker_caption_ranking; preparation1 failed (undecodable image), preparation2 failed (duplicate-quarantine emptied contests), preparation3 manifest OK; 1,041,036 retained rating rows across 180 description-joinable train contests (82 excluded), dev pool 19/13/7/6 contests. Contest 530 excluded after public-card exposure. |
| Judge CPU staging while waiting on 48 local-Qwen scene descriptions (48-contest candidate) | 110 | none (blocked) | 122 CPU tests pass on node4 but 0 descriptions ever delivered; candidate abandoned when Rohin167 switched to released canny/location/entities descriptions at 18:37Z. |
| Released-description assembly + receiving gates v1-v4 | 23 | none | v1 133 pass/6 missing harness (no GPU), v2 142 pass, v3 UUID repair, v4 gate PASS; 34,560 stratified rows (<=64/quality band/contest), max input 401 tokens. |
| DistilBERT v4 (3-class humor + 2-class scene-fit) | 5 | node4 physical2 (A40) | Trained 1,300 steps then stopped: scene-fit negatives always picked the first different scene (scene-identity shortcut). Not promotable. |
| DistilBERT v6 (corrected sampler) incl. gates, report, portable export | 24 | node4 physical2 (A40), 7 min of GPU | 2,000 batches / 32,000 humor draws in 7 min; disjoint dev audit (6 contests/384 rows): Spearman 0.034, Brier 0.0149, log loss 0.531, tau=None, 0 accepted, 0% coverage. Scene-fit synthetic balanced acc 0.632. Selected checkpoint step100 (~1,564 distinct rows seen). |
| Soft-label contrast branch V7/V8/V9/V10 (retired) | 20 | none | V7 CPU gate failed (missing pytest in clean env); V8 never staged; V9/V10 CPU-only; all retired by Rohin170/171 (switch to scalar BT). 0 GPU. |
| bt_qwen_v2: Qwen2.5-7B-Instruct frozen + scalar LoRA Bradley-Terry, 8k comparisons | 47 | node4 physical2 (A40), 22 min of GPU | Code+gates 23 min, fit 22 min (1000 updates / 8,000 comparisons, ~6.3 comps/s). Selected step300: selection Spearman 0.140, audit 0.166, top5/64 vote mass 0.209 vs 0.166 baseline, tau=null, 0 accepted. Adapter (10.1 MB) exported to data_judge/portable/bt_qwen_v2. |
| Rank200 CPU diagnostic + widegap V1/V2 preparation | 57 | none | Rank200 captions: mean positive-vote mass 0.342, coverage 3.79% (perfect-ranking oracle feasible for 0.30/5%). Widegap V1 pair prep failed (one contest with a single >=20-vote caption); V2 gate PASS. 100,000 planned comparisons over 179 pairable contests. |
| bt_widegap_v2: 100k mean-rating wide-gap BT (warm-start step300, LR 3e-5) | 231 | node4 physical2 (A40), 3h51m of GPU | Fit 6,250 updates / 100,000 comparisons in 198 min (8.4 comps/s; 219,712 model examples, 25.7M tokens) + 33 min full-pool selection/calibration. Selection Spearman 0.288 (4,864-row sample) / 0.265 (full 101,418-row pool), top200-in-true-top-half precision 0.695; audit Spearman 0.222 (1,536 rows); calibrated q mean 0.156, std 0.021 (near the 0.162 base rate); tau=null, rank200-quality threshold null, 0/1536 accepted. Adapter NOT exported to repo. |
| Calibration / acceptance threshold (all three judges) | 0 | CPU inside each run | Registered criterion: >=0.30 observed positive-vote mass at >=5% threshold-set coverage. Met by none: DistilBERT v6, BT 8k, widegap 100k all NO_FEASIBLE_HELDOUT_THRESHOLD; no threshold lowering permitted. |
| Export / loader compatibility | 0 | none | gpu/ny_caption_judge.py:875 and :922 require schema NY_TRAINED_JUDGE_CONFIG_V1 (3-class + scene-fit + temperature); widegap emits NY_WIDEGAP100K_SCALAR_JUDGE_CONFIG_V2 (bt_widegap_v2.py:355). No scalar-BT CPU loader exists; GameConfig(tau=None) rejects. Not started. |
| Game wrapper (gpu.ny_caption_game, ny_caption_stage1_tools, action policy, development bridge, R190-R193 runner) | 150 | none | Code-complete and CPU-tested: 371+66 (stage1 tools), 95+17 (game fixtures), 215+158 (R187 batches), 468+395 (R193 runner). Synthetic PARENTED/UNPARENTED submit->restore->replay pass with fixture tau 0.7. Never run against a real judge or real scene. |
| Pixels / novelty archive (gpu.ny_caption_pixels + MiniLM similarity) | 55 | none (CPU encoder) | Core 75 CPU tests (16 min); calibration on 300 LLM-labelled pairs (77 provider calls, 109k tokens): rho 0.977, held-out false merges 0/30, false splits 8/30; public bundle + development verifier scope handed to Main. Provisional (model labels, not human). |
| Local Qwen2.5-VL-7B vision service (physical5) | 115 | node4 physical5 (A40) | Request->model loaded 52 min; 7/7 real generations failed strict JSON/schema (5 invalid JSON, 2 schema); 0 canonical scenes for the 3 development contests; service deadline 20:30Z passed; no receipts after 20:14Z. |
| Generation throughput profile (side task) | 56 | node4 GPU6 (A40) | 23.3 tok/s per life at 2k input, ~5 tok/s at 12k, batch2 aggregate 39.9 tok/s; 40 tok/s per life not reached. |

**Current state.** As of 2026-09-18 04:07 UTC (21:07 PDT Sep 17): three text judges have been trained on node4 physical2 and none is usable for acceptance. Ranking improved with scale (audit Spearman 0.034 -> 0.166 -> 0.222; full-pool selection 0.265, sample 0.288) but every candidate's calibrated vote-mass q is compressed near the 0.16 base rate (widegap q std 0.021), so the registered acceptance criterion (>=0.30 observed positive-vote mass at >=5% coverage, i.e. roughly identify a contest's top ~3% of ~20k submissions) yields tau=null and 0/1536 accepted each time. The widegap run finished 00:57Z (fit) / 01:30Z (report); nothing judge-related has run since; no next candidate is declared; node4 GPU2 has been taken by an R195/R201 control life; R206 (03:58Z) parks caption work on the new games node 'pending a calibrated judge'. Game wrapper, action policy, pixels archive and similarity calibration are code-complete and CPU-tested but have never touched a real judge or a real scene: the local Qwen-VL service loaded but failed strict output validation 7/7, so 0 of 3 canonical development scenes exist. The widegap adapter is not exported to the repo and the game's loader still hard-requires the legacy DistilBERT schema. None of the day's caption code (11 gpu modules, 11 test files, the r177 worker dir) is committed anywhere: the orch clone HEAD is Sep 16 03:00 PDT, 0 ahead / 184 behind origin/main, 3624 untracked files, two failed `git pull --ff-only`.

**Blockers**

- No acceptance threshold: all three judges (DistilBERT v6, BT 8k, widegap 100k) return tau=null under the registered 0.30 positive-vote-mass / 5% coverage criterion; widegap's calibrated q barely varies (mean 0.156, std 0.021 vs base rate 0.162), so no operating point exists. Receipt: bt_widegap_v2/training/PUBLIC_SCORING_REPORT.json tau.status=NO_FEASIBLE_HELDOUT_THRESHOLD, development_audit.accepted_count=0/1536.
- Judge loader/export mismatch: gpu/ny_caption_judge.py:875,922 require NY_TRAINED_JUDGE_CONFIG_V1; the scalar-BT candidates emit NY_WIDEGAP100K_SCALAR_JUDGE_CONFIG_V2 (data_judge/bt_widegap_v2.py:355); no scalar loader and no portable export of the widegap adapter in the repo (data_judge/portable has only released_all_v6 and bt_qwen_v2).
- No canonical scene descriptions for the 3 development contests: local Qwen2.5-VL-7B service produced 7/7 schema failures (vision/SERVICE_STATUS_20260917T1938Z.json), deadline 20:30Z passed, no later receipts; the game manifest cannot be built (vision/GAME_ONLY_INTERFACE.md).
- No judge work in progress and no owner/next candidate declared since 01:30Z; node4 physical2 is now occupied by an R195/R201 control life (nvidia-smi 04:07Z, PID 3735657); R206 defers caption to the new games node 'pending a calibrated judge'.
- Nothing committed or pushed from the orch clone: all gpu/ny_caption_*.py, tests/test_ny_caption_*.py and research_loop/workers/r177_caption_game_stage1_20260917/ are untracked; HEAD de1fc4b7 (Sep 16 03:00 PDT), 184 behind origin/main; a node/VM loss would erase the day's caption work.
- Real end-to-end game smoke (gpu.ny_caption_stage1_tools) is designed to fail closed without all four frozen artifacts at once (numeric tau, scalar loader, vision packet with real scenes, similarity bundle) - so no partial or provisional game can be scored under the current contract.

**Why slow**

- About 1h50m (16:47-18:37Z) of the judge path was spent waiting on 48 local-Qwen scene descriptions for a 48-contest candidate that were never produced (the vision service only loaded at 19:31Z and then failed 7/7); Rohin167 had to intervene to decouple the judge from vision (COORDINATION 11:37PDT: 'No, the judge has not yet started training... the current blocker was waiting for 48 new Qwen descriptions').
- Strictly sequential, single-slot pipeline: one judge candidate at a time on one A40 (node4 physical2), each launch preceded by CPU/provenance/strict-confinement gates and receipts (10-25 min per launch) and followed by hand-written handoffs and COORDINATION entries. 16 candidate directories were staged on node4 (released_all_v1-v10, bt_qwen_v1/v2, bt_widegap_v1/v2, cpu_stage1, diagnostic) for 4 actual GPU runs; ~150 receipt/observation JSON files were written in data_judge/evidence alone.
- The objective was changed three times in one day (DistilBERT 3-class soft CE -> vote-q scalar Bradley-Terry -> mean-rating wide-gap BT), each requiring new code, new tests, a new budget/allocation and a new gate; plus four failure detours: v4 stopped at 4.6 min for the scene-negative sampler shortcut, V7 gate failed on a missing pytest in the clean env, the V7-V10 branch (20 min) was retired by the BT redirect, widegap V1 pair prep failed on a one-caption contest.
- The 100k widegap fit is inherently slow on this hardware: a 7B backbone on one A40 at 8.4 comparisons/s = 3h18m of fitting plus 33 min of full-pool inference/calibration (219,712 model examples, 25.7M tokens). It alone occupied 21:39Z-01:30Z (14:39-18:30 PDT), and the projection (4.4h) was known at 21:07Z; no parallel arm (e.g. the VLM comparator on physical6/7) was run alongside it.
- The acceptance criterion may be unreachable for a text-only judge by construction: rank200 captions (top ~3% of ~20k submissions) themselves average only 0.34-0.36 positive-vote mass, and every judge's calibrated q sits at the ~0.16 base rate with std <=0.02, so tau is null regardless of ranking gains. With no provisional fallback allowed (Main: 'we do not lower the standard'), 'training the judge' cannot terminate by this gate, and the whole game waits on it.
- Small development audit (6 contests; 384 rows for DistilBERT/BT-8k, 1,536 for widegap) makes each verdict noisy, yet each verdict triggered a full new cycle rather than a parallel sweep of scale/objective arms.
- Operator attention was split: Main and Ampere were concurrently running node3 recovery, C2 recovery and console (R188-R205), parent rollouts, clone launches and fleet moves; judge redirects waited on Rohin messages (168 at 19:47Z, 170/171 redirect at 19:52Z) and Main reviews; the games work is now deferred to a new node (R206) with no owner for the judge.
- Vision, judge and game glue were serialized behind Main's fail-closed real-tool smoke, which requires every frozen artifact simultaneously; no mock-judge or fixture-scene development game was permitted, so none of the CPU-complete game code has produced a single real scored caption.

**Open questions**

- Who owns the next judge candidate, on which GPU, and by when? physical2 is now a control-life slot; R206 only says 'pending a calibrated judge'.
- Will Rohin authorize a provisional acceptance rule for a first scorable development game (e.g. within-contest rank-based top-k acceptance from the widegap ranker, or a lower registered mass target), given that ranking is improving with data (0.03 -> 0.17 -> 0.22 audit Spearman) while the 0.30/5% vote-mass criterion has failed identically three times? Main's entries state it will not lower tau without a ruling.
- Should the image+caption VLM comparator (Astra's Rohin168 recommendation, HOLD per Rohin171) start now that text-only BT appears to plateau around Spearman 0.27 on selection?
- Vision JSON failures: is anyone fixing the output contract (constrained decoding / prompt format / accepting the model's actual JSON shape)? No owner receipt after 20:14Z and the service deadline has passed.
- Will the widegap adapter be exported and a scalar-BT CPU loader written (the loader gap is independent of the threshold gap and was flagged at 00:16Z and 01:27Z)?
- Who commits and pushes the untracked caption code and r177 worker directory from the orch clone (two `git pull --ff-only` attempts failed on local COORDINATION.md changes)?
