# Independent fading terminal numerical review — September 12, 2026

## Verdict

**PASS. No numerical correction, rerun, or minimal required fix identified.** Independently checked all 576 raw calls, all 12 fit chains, original source answer keys, native token accounting, and recorded release evidence. Main's JSON and all 15 CSV rows agree. The nonzero-rate result is actual correct **ACT-only output**, not merely disappearance of PREDICT. The interpretation is a fixed seed0 task-only competing-update sentinel, not passive fading or a general learning result.

Only this report was written. No repository edits, Git, network, GPU/model/tokenizer calls, experiment reruns, or reduction writes were performed. Temporary audit assertions were executed directly with standard-library Python; no existing scorer was invoked.

## Evidence and integrity

- **R** = `/tmp/astra_fading_terminal_20260912/astra_diagnostics/astra_fundamental_fading_20260912_attempt1/runs`.
- **M** = `/tmp/astra_fading_terminal_20260912/astra_diagnostics/astra_fundamental_fading_20260912_attempt1/material`.
- **S0** = `/tmp/astra_fundamental_seed0_terminal_20260912/astra_fundamental_teaching_20260912_attempt1`.
- Archive `/tmp/astra_fundamental_fading_terminal_20260912.tgz` SHA256 independently matches `3a2564219790cc7a31f4350cd2013eb323577e5d41003a5bf322eeb16fc415ff`. All **1,448 regular archive files** match both extracted bytes and `/tmp/astra_fundamental_fading_terminal_20260912.tgz.validation.json`. No `.safetensors`, `.bin`, or `.pt` weights are included.
- All 15 `R/plan.json` source pins match `/tmp/astra_continuation_source_3a12807f.tgz` and the bound `/tmp/astra_fading_sentinel_20260912.py`. Original plan/fit hashes and available parent metadata match S0. Model-file inventories agree across the original and new plans and all 12 readout identities/reductions; the original model-origin qualification remains `UNRESOLVED_LOCAL_HASHES_ONLY`.

## Independent raw results

For each of the 48 fixed cases, derived arithmetic answers from original source operands and colors from original device/color records in `/tmp/astra_fundamental_teaching_corpus_candidate_20260912/source_records.json`, rather than accepting reduction keys alone. Parsed each raw response for correct ACT, correct PREDICT before ACT, exact ACT-only response, and exact color match. Checked every raw text against its reduction row and all request/response hashes, capture inventories, plan bindings, actual token-array lengths, and request-to-response timestamps.

| State / rate | Phase / cumulative new updates | Correct ACT | PREDICT-before-ACT adherence | Exact correct ACT-only | Memory |
|---|---|---:|---:|---:|---:|
| One inherited seed0 teach baseline | 0 / 0 | 32/32 | 32/32 | 0/32 | 4/16 |
| LR 0 | Each of phases 1–4 / 16, 32, 48, 64 | 32/32 | 32/32 | 0/32 | 4/16 |
| LR 0.00003 | Each of phases 1–4 / 16, 32, 48, 64 | 32/32 | 0/32 | 32/32 | 4/16 |
| LR 0.0001 | Each of phases 1–4 / 16, 32, 48, 64 | 32/32 | 0/32 | 32/32 | 4/16 |

Every nonzero-rate arithmetic response, **256/256 across eight readouts**, is exactly `ACT: <correct sum>` after trimming, without extra explanation, malformed action, or replacement tag. This matches the ACT-only continuation target form on the existing dev arithmetic panel; it is not a new readout of the 64 continuation training questions. Correct arithmetic was already present in the inherited baseline. Every memory response is literally `red`: the four correct IDs are `eval-memory-006-0`, `eval-memory-009-0`, `eval-memory-013-0`, and `eval-memory-014-0`. This remains constant-color collapse, not item-specific binding.

All four LR0 complete 48-output text vectors equal the actual original teach baseline. The 48 case IDs, requests, native prepared inputs, and all 576 returned prompt-token arrays/rendered prompts equal the corresponding original OFF inputs. Temperature is 0, generation seed 20260912, and maximum output is 64 tokens per call. There are **576 new calls**, no new OFF calls, and no confirmation calls. The same 48-call original teach baseline is reused for all three curves, not measured or charged three times.

Evidence: `R/rate-{0,3e-5,1e-4}/continuation-phase-{01,02,03,04}/readout/{plan.json,reduction.json,run/data/manifest.json,run/data/calls/0000.request.json…0047.response.json}`; `S0/readouts/{teach,OFF}/plan.json` and their raw call directories. Main comparison: `/tmp/astra_fading_main_analysis_20260912.json` and `/tmp/astra_fading_curves_20260912.csv`.

## Material, fitting, and parameter custody

Independently checked all 64 continuation source additions against their sums and actual supervised ACT-only spans. They are 64 distinct unordered operand pairs, disjoint from the 128 original pairs, in four 16-row phase corpora. The same corpus bytes are used across rates; all 12 fit corpus hashes match M. No memory targets occur in continuation. Native audit input/label arrays reproduce per-row and per-phase token totals; actual manifests agree, with no truncation, splitting, dropped targets, skipped examples, or nonfinite batches.

Each fit uses four epochs, batch4/accum1, **16 optimizer updates**, seed0, rank8/alpha16/dropout0.05, AdamW, and the same frozen base. Each rate performs 64 new updates; across rates there are 192 new updates. Cumulative lineage counters are 80 inherited plus 16/32/48/64 new steps, ending at 144. These are **three learning-rate conditions from one initial training seed**, not three independent initializations or replications.

All first-phase manifests record the same 392-tensor parent state and original teach adapter file SHA `d73e8578f62de68ed657474c70fc09c09aaad50a4ff11a66773e50fc702163b2`. At every link, parent file inventory equals pre/post inventories, source state equals initialized state, and the next phase's source state equals the prior phase's final state. All 392 tensor entries are present; dtype conversions are empty. Each fit records one adapter, base frozen, fresh AdamW with zero initial optimizer-state entries, and no restored/saved optimizer state. Arithmetic and memory readouts bind the same phase adapter.

For all four LR0 phases, source/initialized/final tensor inventories are exactly equal and the serialized adapter weight-file SHA remains the original SHA. Nonzero fits record changed parameter states. **These are independently checked receipt equalities, not an independent rehash of unavailable native weight tensors.** Native tensor loading, equality checks, parent immutability, and frozen-base attribution come from the bound trainer/controller receipts; the capsule deliberately excludes weights. LR0 exactness concerns parameter values and serialized LoRA weights, not identical metadata files or unchanged transient optimizer state.

Evidence: `M/{candidate.json,continuation-phase-01.json,continuation-phase-02.json,continuation-phase-03.json,continuation-phase-04.json,token_audit.json}`; each phase's `phase.json`, `fit-result.json`, `adapter/train_manifest.json`, and readout `run/data/identity.json`; `R/plan.json`; native `check_states`/`verify_fit` in `/tmp/astra_fading_sentinel_20260912.py`.

## Honest cost and cleanup

| Quantity | Verified amount / scope |
|---|---|
| Training input tokens per phase per rate, four epochs | 3,340; 3,316; 3,336; 3,320 |
| Training supervised target tokens per phase per rate | 376; 372; 380; 376 |
| All 12 fits | **39,936 input / 4,512 target tokens** |
| LR0 readouts, each phase | 2,131 input / 472 actual output tokens |
| Nonzero-rate readouts, each phase | 2,131 input / 220 actual output tokens |
| All 576 new calls | **25,572 input / 3,648 actual output tokens** |
| Output ceiling, not consumed output | 36,864 tokens |
| Sum of raw generation windows | 168.205682 seconds |
| Fit worker supervision | 720.886091 seconds |
| Readout worker supervision | 1,404.481373 seconds |
| Total worker supervision | 2,125.367463 seconds = 35.422791 A40-minutes |
| Controller windows, including workers/gaps | 3,073.313819 seconds = 51.221897 A40-minutes |
| Full Main reservation through release | **3,460.763131 seconds = 57.679386 A40-minutes** |

Training inputs already include supervised target positions; targets are not additional input charges. Native training token totals exclude masked padding. The 512-token training length and 64-token generation length are caps, not observed consumption. Generation, worker, controller, and reservation windows are nested scopes: **do not add them together**. No inherited fit/baseline/OFF cost is charged again. No monetary charge is inferred without billing-rate evidence.

All 24 fit/readout worker supervision receipts report success, return code 0, owned groups empty, GPU processes absent, and verified worker release; all 12 backend cleanup receipts report closed. All three controllers are COMPLETE, with release-verified terminal receipts bound by Main release hashes. Main records full release and controller absence for devices 4/5/6 at **19:09:55.283099 / 19:10:04.555779 / 19:10:17.512359 UTC**, respectively. Each matching release XML contains its one reserved GPU with zero processes. This substantiates release of these three reserved devices; it is not an independent all-seven-device inspection or a live GPU query.

Evidence: each phase's `fit-worker/supervision.json`, `readout/run/worker/supervision.json`, `readout/run/data/{usage.json,backend.cleanup.json}`; `R/rate-{0,3e-5,1e-4}/{reservation.json,terminal.json,main_release.json,main_release.xml}`; Main analysis totals.

## Claim boundary / disposition

The old response-order habit survives zero-LR processing and is replaced by correct ACT-only responses by the **first measured nonzero phase (16 updates)**, staying replaced at subsequent measured phases. The data do not resolve the within-phase transition, favor one nonzero learning rate, establish an optimal retention/adaptation tradeoff, or measure passive/time-alone forgetting. Memory begins and remains collapsed at red4/16, so this does not demonstrate decay of successfully bound facts. Different rates are not seed replications. No general G3, prediction-intelligence, parenting, child-sleep, H1/H2, cognition, clean-exposure, or biological mechanism conclusion follows.

**Final disposition: PASS within these boundaries; no required artifact correction.** This review neither authorizes nor blocks ongoing independent work.
