# Throughput snapshot — September 12, 2026

**Read-only, bounded evidence cut.** Main retains the critical path and will add actual cumulative results later. SEQ-091 is terminal; cumulative is **live, not terminal** here. Only this Markdown and its sibling JSON are written. No repo/GPU/network/git changes, tests, extraction, node polling or control-plane verification. Archived native-validation assertions are attributed, not rerun.

**Main update, September 12, 2026 15:50 UTC:** resumed; `fit_A2` remains alive, as reported by Main. No additional counters or terminal result are inferred from this update.

## Measured phase / recipe table

Times are seconds. **C** = controller wall; **F** = already-loaded fit-function wall; **L** = native fit-loop wall. A continuously assigned single device accounts for C device-seconds **within that receipt window only**; full reserved-GPU time is unmeasured. Concurrent C values sum device intervals, not calendar time or GPU-active compute. Input/update counts are training token passes, never inference prompts.

| Phase / fixed recipe | Calls or steps | C / F / L seconds | Tokens: inference prompt / output; training input / update | Evidence |
|---|---:|---:|---|---|
| SEQ-085 whole_raw seed0: fit + fresh OFF/ON | 96 updates; 128 generation batches | 776.314736 / 85.3 / 84.7 | inference unmeasured; 92,064 / 8,832 | U |
| SEQ-085 whole_raw seed1: fit + fresh OFF/ON | 96 updates; 128 generation batches | 695.798777 / 84.4 / 83.9 | inference unmeasured; 92,064 / 8,832 | U |
| SEQ-085 whole_raw seed2: fit + fresh OFF/ON | 96 updates; 128 generation batches | 736.047406 / 84.6 / 84.1 | inference unmeasured; 92,064 / 8,832 | U |
| SEQ-085 act_only seed0: fit + fresh OFF/ON | 96 updates; 128 generation batches | 625.526204 / 81.8 / 81.3 | inference unmeasured; 86,880 / 3,648 | U |
| SEQ-085 act_only seed1: fit + fresh OFF/ON | 96 updates; 128 generation batches | 578.221335 / 81.6 / 81.1 | inference unmeasured; 86,880 / 3,648 | U |
| SEQ-085 act_only seed2: fit + fresh OFF/ON | 96 updates; 128 generation batches | 578.913064 / 82.3 / 81.8 | inference unmeasured; 86,880 / 3,648 | U |
| SEQ-087 root0: OFF and two inherited adapters, exact rows; zero fits | 384 generations + 384 scores (768 candidate forwards) | C 396.154617; call timers gen 122.298226, score 38.927043 | prompt unmeasured / 2,796 emitted IDs incl. EOS; no updates | E0 |
| SEQ-087 root1: OFF and two inherited adapters, exact rows; zero fits | 384 generations + 384 scores (768 candidate forwards) | C 399.416826; call timers gen 117.426356, score 38.806810 | prompt unmeasured / 2,800 emitted IDs incl. EOS; no updates | E1 |
| SEQ-088: process/format; zero fits | 16 generations | C 276.672446; arm sum 244.954638 (not pure decode) | 4,184 / 705; no updates | P88 |
| SEQ-090 sampler 7101: process/format; zero fits | 16 generations | C 224.704325; arm sum 206.253338 (not pure decode) | 4,520 / 668; no updates | P90 |
| SEQ-090 sampler 7102: process/format; zero fits | 16 generations | C 202.486860; arm sum 184.708855 (not pure decode) | 4,520 / 694; no updates | P90 |
| SEQ-090 sampler 7103: process/format; zero fits | 16 generations | C 206.781977; arm sum 167.218420 (not pure decode) | 4,520 / 704; no updates | P90 |
| SEQ-091: process/format; zero fits | 32 generations | C 340.548915; arm sum 288.852348 (not pure decode) | 11,173 / 1,300; no updates | D91 |
| Cumulative native preparation | OLD 12,924 + NEW 2,048 rows | 20.872180 elapsed CPU-side preparation | AN input/update planned 171,264 / 165,120; A2 planned 921,249 / 876,333 | CP |
| Cumulative AN, fit reported done, readout pending at cut | 1,536 reported updates | L 199.4; full fit/controller/reservation unknown | reported input 171,264; 165,120 update tokens is prepared dose, not recovered terminal counter | CN |
| Cumulative A2 **LIVE profile, not terminal** | 100-step sample; 11,229 planned full updates | 495 input tok/s; **28.4 min projected**, not measured completion | full completed counters unknown; prepared dose is not completed work | USER, CP |

**Recipe scope.** SEQ-085 uses frozen Qwen2.5-7B-Instruct, fresh rank8/alpha16 LoRA, dropout .05, AdamW 1e-4, batch1, 3 epochs, 32 replays of one event, no packing/truncation, max4096, gradient checkpointing; masked own-output targets include EOS. Each OFF/ON read is 32 fixed development cases, with wake and scratchpad generation: 64 batches/condition, 128/recipient. Each condition reserves a 16,000-output-token cap, **not actual usage**; prompt/output counts remain unmeasured, never inferred from characters. Cumulative is a different batch4/max512, seed2, chronological recipe: A1=Fit(base,OLD), AN=Fit(base,NEW), A2=Fit(base,OLD+NEW), **not a warm-start OLD-weight update**.

**Costs outside or inside different clocks.** V3 F starts with an already-loaded model; L excludes setup/save. Native memory_dose `wall_seconds` is actually a post-load optimizer-loop timer before adapter save. Controller windows include internal fresh-process loading, hash/custody checks, probes and cleanup. External preparation/capture/audit/release margins are additional; isolated cold-start, hash-validation and eval time are unmeasured. CP `prepare_cpu_seconds` is monotonic elapsed time, not CPU process time: includes model/A1/source hashes, tokenizer and row/mask/order audit, excludes transfers/external audits. Production arm sums include validation/load/close, not just generation. No residual is labeled pure cold-start or hashing.

**Failure/inheritance scope.** The separate root0 SEQ-087 failed attempt preserves 128 OFF generations + 128 scores, 896 emitted IDs and 40.657923 call-seconds (EF); full attempt/reservation cost is unknown and excluded from the two terminal rows. It is not spliced into the retry. CP carries historical A1 9,693 steps, 749,985 input / 711,213 update passes and native-loop 1,327.3s; this inherited record is not a newly executed cumulative fit or a full historical reservation.

## Provisional single-GPU learner-seeds/day

- **Known utility recipe only:** 86,400 / observed recipient C gives **111.30–149.42 recipient fits+OFF/ON evaluations/day**. One recipient means one fitted adapter, not one successful learner or developmental life.
- A scientifically paired seed needs both arms serially on one A40: seed0/1/2 consume 1401.840940/1274.020112/1314.960470s; conditional envelope **61.63–67.82 paired learner-seeds/day**. Observations themselves used separate devices; this is arithmetic, not a measured serial-day benchmark.
- These are explicitly provisional, no-extra-overhead scenario envelopes, not confidence bounds or a positive guaranteed lower bound. Require 24 usable hours, unchanged data/recipe, representative observed times, and no extra generation/selection/preparation/audit/release, gaps or failures. Real rate may fall below either endpoint. No measured sustained or new-pilot rate is available.
- Do not use the 90-minute cumulative cap, AN 199.4s loop, or A2 100-step projection to price complete learners. No ideal 16-way scaling, A100 speedup, or campaign-capacity multiplication.

## Serial dependencies for Main’s next own-output pilot

```text
Main freezes scope / eligibility / all selection denominators / controls / budget
 -> source-bound own output + public feedback (preserve teacher/example provenance and failures)
 -> exact-byte CPU hash/overlap/visibility/token/mask/order preparation
 -> Main reservation-ready check; continuous one-device reservation
 -> fresh-base own-output fit -> immutable save/DONE/hash -> trainer cleanup
 -> fresh OFF load/read/cleanup -> fresh saved-adapter reload/hash/ON read/cleanup
 -> raw-score/token/time custody + terminal validation -> Main release
 -> only then consider next seed/cycle or separately scoped retention read
```

This preserves the observed SEQ-085 fit-before-OFF/ON sequence; it does not start another run or prescribe new tests. No public-valid SEQ-091 note is automatically training-approved, and outcome-selected notes require explicit selection limits. Teacher text is not a target. Acquisition, new-case transfer and later retention are distinct dependencies, not interchangeable claims. `T_pilot = T_source + T_external_preparation + T_continuous_reservation`; the last term contains loads/checks, fit/save, OFF/ON and cleanup/verification. The utility interval is only an analogue for the last term’s recorded inner window. Different demo-output lengths, masks, scoring or cycles are unpriced. Main’s live cumulative reservation remains untouched.

## Cumulative and resource status

- Launch CL: node3/GPU0, controller 128957, 2026-09-12T15:16:50.264833+00:00; stages `A1_before -> fit_AN -> fit_A2 -> AN -> A2 -> A1_after`. Prepared four reads each have 1,377 cues, two passes, 3,202 scored prompt rows, 20,752 candidate sequences and 448 abstention sequences. These are work counts, not actual read tokens/time.
- Planned new fit total: 12,765 updates, 1,092,513 input passes, 1,041,453 shifted supervised passes. Readouts, saves, fresh loads, cleanup and full reservation remain unpriced; 5,400s is a cap, not observed cost. No later cumulative completion is assumed.
- A2’s 495 tok/s and 28.4-minute projection come from the user-reported live 100-step profile, **not an archived terminal receipt**. Do not assume sampled and full-corpus token mixes are identical. AN progress is attributed to the 15:30 UTC Builder note, not independently polled.
- **A100 scheduled September 12, 2026 22:05 Pacific = September 13, 2026 05:05 UTC.** From September 12 15:32 UTC that is **13h33m**, not the watcher’s 6.5h. Schedule only; no control-plane verification or assertion of availability/onboarding. CL separately uses supplied node3 expiry minus six hours, cutoff September 25 21:03 UTC, also not fresh lease verification.

## Dataset / measurement limits

- SEQ-085: one selected solved event, replay rather than new experiences; three recipient seeds/arm, same 32 same-gym development questions; repeated OFF is one baseline. Equal optimizer steps do not match token/compute/information dose. No observed full-Scratchpad advantage.
- SEQ-087 uses exact training contexts and inherited adapters with root/seed confounding. SEQ-088/090 use constructed eight-case panels and sampler rather than learner replication; SEQ-090 strict grounding is 0/48. Post-hoc normalization is not a new primary result.
- SEQ-091 process grounding is source2/8, transfer1/8 versus control0/8, one sampler seed: in-context feasibility only. Example/teacher carryover and post-outcome selection remain limitations; no persistence/internalization or automatic output-training approval.
- Cumulative is planted synthetic memory and fresh-base reconstruction, not autonomous own-output learning, forgetting of OLD weights, or repaired OLD selectivity. Local hashes are not official model-origin authentication or exhaustive contamination clearance.
- **p50, p95, peak VRAM, utilization: unmeasured.** Also no energy, isolated cold-load/hash latency, billing or total campaign cost. Partial records do not support clean-lineage, P1/G3/G5/H1/H2, successful-learner or campaign-completion claims.

## Arithmetic receipt

- U: `6×96=576` updates; `3×92064+3×86880=536832` input passes; `3×8832+3×3648=37440` update passes. Fit loops sum `496.9s`; fit-function walls sum `500.0s`.
- U: `776.314736+695.798777+736.047406+625.526204+578.221335+578.913064=3990.821522s`; `/3600=1.108561534` accounted device-hours. Calendar union envelope is `955.841603s`, not the sum. Residual `3990.821522-500.0=3490.821522s` is unpartitioned, not isolated eval or loading.
- Single-device denominators: `86400/776.314736=111.295066`; `86400/578.221335=149.423750`; paired seed sums above give `86400/1401.840940=61.633241` to `86400/1274.020112=67.816826`.
- E0/E1: `(finished-started)=396.154617+399.416826=795.571442s`; native generate calls `239.724583s` + score calls `77.733853s`; residual `478.113006s`. `2796+2800=5596` emitted IDs; 768 generations + 768 scores / 1,536 candidate forwards. EF failure is separate.
- P88: `2104+2080=4184` prompts, `392+313=705` output tokens; `276.672446s`. P90: `224.704324931+202.486860259+206.781977484=633.973162674s` summed pair/device spans; `3×(2272+2248)=13560` prompts, `(327+341)+(363+331)+(374+330)=2066` outputs.
- D91: `5637+5536=11173` prompts; `652+648=1300` outputs; `340.548915s`. Exact per-arm and source/transfer token subtotals are in JSON, not inferred from caps.
- CP: AN `57088×3=171264` input, `55040×3=165120` supervised, `3×ceil(2048/4)=1536` steps; A2 `307083×3=921249`, `292111×3=876333`, `3×ceil(14972/4)=11229`. These are prepared doses. AN reported loop averages `199.4/1536=0.129818s/step`, `171264/199.4=858.896690 input passes/s`, not complete-pilot throughput.

## Exact source paths and archive members

`archive :: member` means read directly from the local tarball, without extraction. JSON expands every U cell / terminal arm to exact member names, retains the source SHA256s, and includes the full numeric arithmetic receipt. Mutable notebook/code hashes are the local read snapshot, not an assertion that they are immutable historical execution sources.

- **U:** `/data/home/rohing/dream-state/research_notes/astra_memos/receipts_20260912/astra_correction_utility_terminal_20260912.tgz`
  Members: `astra_correction_utility_20260912_attempt1/recipients/{whole_raw,act_only}/seed{0,1,2}/train_manifest.json`; corresponding `recipient_logs/.../STARTED.json`, `COMPLETED.json`, `probes/pair/{off,on}/results.json`. Braces denote only the six concrete cells expanded in JSON.
- **E0:** `/data/home/rohing/dream-state/research_notes/astra_memos/receipts_20260912/astra_exact_train_root0_terminal_20260912.tgz`
  Members: `root0/probe.json`; `root0/COMPLETED.json`; `root0/supplementary_report.json`. Raw per-state/arm members are expanded in JSON.
- **E1:** `/data/home/rohing/dream-state/research_notes/astra_memos/receipts_20260912/astra_exact_train_root1_terminal_20260912.tgz`
  Members: `root1/probe.json`; `root1/COMPLETED.json`; `root1/supplementary_report.json`. Raw per-state/arm members are expanded in JSON.
- **EF:** `/data/home/rohing/dream-state/research_notes/astra_memos/receipts_20260912/astra_exact_train_root0_failure_20260912.tgz`
  Members: `root0/FAILED.json`; `root0/OFF/records.jsonl`; `root0/MAIN_FAILURE_AUDIT.json`. Raw per-state/arm members are expanded in JSON.
- **P88:** `/data/home/rohing/dream-state/research_notes/astra_memos/receipts_20260912/astra_constraint_verified_terminal_20260912.tgz`
  Members: `astra_constraint_check_20260912_attempt1/COMPLETED.json`. Raw per-state/arm members are expanded in JSON.
- **P90:** `/data/home/rohing/dream-state/research_notes/astra_memos/receipts_20260912/astra_constraint_v2_terminal_20260912.tgz`
  Members: `astra_constraint_v2_20260912_seed7101_attempt1/COMPLETED.json`; `astra_constraint_v2_20260912_seed7102_attempt1/COMPLETED.json`; `astra_constraint_v2_20260912_seed7103_attempt1/COMPLETED.json`. Raw per-state/arm members are expanded in JSON.
- **D91:** `/data/home/rohing/dream-state/research_notes/astra_memos/receipts_20260912/astra_demonstration_terminal_20260912.tgz`
  Members: `astra_demonstration_20260912_attempt1/COMPLETED.json`. Raw per-state/arm members are expanded in JSON.
- **CP:** `/data/home/rohing/dream-state/research_notes/astra_memos/receipts_20260912/astra_cumulative_prepared_20260912.tgz`
  Members: `astra_cumulative_20260912_attempt1/manifest.json`; `astra_cumulative_20260912_attempt1/OLD.audit.json`; `astra_cumulative_20260912_attempt1/AN.audit.json`; `astra_cumulative_20260912_attempt1/A2.audit.json`. Raw per-state/arm members are expanded in JSON.
- **CL:** `/data/home/rohing/dream-state/research_notes/astra_memos/receipts_20260912/astra_cumulative_launch_20260912.json`
- **CN:** `/data/home/rohing/dream-state/research_loop/COORDINATION.md`
  Scope: 4120-4125: Builder 2026-09-12 15:30 UTC AN progress; 4173-4199: lineage correction and SEQ-091 terminal/live-A2 snapshot.
- **UM:** `/data/home/rohing/dream-state/research_notes/astra_memos/receipts_20260912/astra_correction_utility_analysis_20260912.md`
  Scope: Dose and cost; actual generation token counts absent.
- **EM:** `/data/home/rohing/dream-state/research_notes/astra_memos/ASTRA_EXACT_TRAIN_TERMINAL_2026-09-12.md`
- **PM:** `/data/home/rohing/dream-state/research_notes/astra_memos/ASTRA_CONSTRAINT_PRODUCTION_TERMINAL_2026-09-12.md`
- **DM:** `/data/home/rohing/dream-state/research_notes/astra_memos/ASTRA_DEMONSTRATION_TERMINAL_2026-09-12.md`
- **CM:** `/data/home/rohing/dream-state/research_notes/astra_memos/ASTRA_CUMULATIVE_READONLY_AUDIT_2026-09-12.md`
- **RESOURCE:** `/data/home/rohing/dream-state/research_notes/ASTRA_LAUNCH_PROMPT_2026-09-12.md`
  Scope: 340: scheduled A100 start and UTC correction; not control-plane verification.
- **V3T:** `/data/home/rohing/dream-state/organism_v6/train_adapter_v3.py`
  Scope: 501-508: fit-function timer starts with already-loaded base; 619: training-loop timer; 653-658: loop end, save, wall timer.
- **MDT:** `/data/home/rohing/dream-state/organism_v6/memory_dose.py`
  Scope: 2610-2634: tokenizer/base load and optimizer precede timer; 2696: wall_seconds is native-loop timer, before adapter save.
- **CPT:** `/data/home/rohing/dream-state/gpu/astra_memory_cumulative_diagnostic.py`
  Scope: 206-257: preparation timer includes hash/tokenization/row audit, measured by monotonic wall clock.
- **USER:** current user message, verbatim profile `A2 only live100step profile495tok/s projected28.4min (NOT terminal)`; no corresponding terminal file was used.
