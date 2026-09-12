# Independent repetition numerical review — September 12, 2026

## Verdict

**PASS for the supplied capsule's raw numerical results, fit accounting, and recorded custody.** All 192 responses independently reproduce the supplied scores. No reduction correction or experiment rerun is required.

**Interpretation qualification:** repetition did not improve this seed0 **development-paraphrase** memory endpoint. The notebook's literal prediction about **in-sample training-prompt** performance was not measured on these repeated-fit checkpoints. Definitive causal statements in the 18:39 notebook entry are not identified by these results; concrete wording corrections are listed below. Neither a separate adapter requirement nor its impossibility follows.

Only this report was written. No Git commands, repository edits, network, GPU/model/tokenizer calls, fit/readout reruns, or reduction writes occurred. The notebook was read only for the specifically requested prediction comparison. Main's concurrent fading work was not reviewed or disturbed.

## Evidence bindings and method

**R** denotes `/tmp/astra_repetition_terminal_20260912/astra_diagnostics/astra_fundamental_repetition_20260912_attempt1`.

**S0** denotes `/tmp/astra_fundamental_seed0_terminal_20260912/astra_fundamental_teaching_20260912_attempt1`.

Capsule `/tmp/astra_fundamental_repetition_terminal_20260912.tgz` hashes to exactly `36e9ca2637d1f78ab218afd3348b0cc547ea098188e3d418aa2b08c4e48a198b`. All **507 regular files** match both extraction and `/tmp/astra_fundamental_repetition_terminal_20260912.tgz.validation.json`. Validation JSON SHA256: `9f53fab7ff22dc7a1fac4e3749479e2d18f30e468ee5779bba2cca31cef5b79e`. No `.bin` or `.safetensors` weights are included.

Used independent read-only standard-library Python parsing, not an existing scorer or native reducer. Derived addition answers from source operands and memory answers from original device/color source records. Separately checked the seeded operand sums and color assignments. For all 192 outputs, checked ACT validity/correctness, correct PREDICT before ACT, exact normalized color validity/correctness, raw text correspondence, request settings and IDs, per-request/response hashes, capture inventory, plan hash, reduction-to-capture binding, and native prompt-token/rendered-prompt correspondence.

The original source records are in `/tmp/astra_fundamental_teaching_corpus_candidate_20260912/source_records.json`; actual original corpora are `S0/teach.json` and `S0/control.json`. Preserved IDs and source keys, not reduction counts alone, determine the scores.

## 1. Recomputed complete results

| Fresh fitted cell | Correct ACT | Correct PREDICT before ACT | Exact memory | Invalid memory | Memory pattern |
|---|---:|---:|---:|---:|---|
| teach_short | 32/32 | 32/32 | 4/16 | 0/16 | red on all 16 |
| control_short | 32/32 | 0/32 | 4/16 | 0/16 | red on all 16 |
| teach_long | 32/32 | 32/32 | 4/16 | 0/16 | red on all 16 |
| control_long | 32/32 | 0/32 | 4/16 | 0/16 | red on all 16 |

All four cells have zero invalid arithmetic actions. Correct memory IDs in every cell are exactly `eval-memory-006-0`, `eval-memory-009-0`, `eval-memory-013-0`, `eval-memory-014-0`: the four red-key matches. Constant red is not item-specific retrieval. No favorable subset or semantic prose rescue is used.

Each complete same-arm short/long text vector is identical on **48/48 outputs**. Each also equals its corresponding original, unrepeated seed0 arm's complete 48-output text vector. Thus these repeated fits reproduce the prior observable habit and memory collapse; there is no measured arithmetic or memory improvement on this panel.

Evidence: `R/cells/{teach_short,control_short,teach_long,control_long}/readout/run/data/calls/0000.response.json` through `0047.response.json`, their request files, `plan.json`, and `reduction.json`; original comparison vectors in `S0/readouts/{teach,control}/run/data/calls/`.

## 2. Exact original OFF inputs and endpoint preservation

Read the original OFF plan and all 48 actual OFF response records directly from `/tmp/astra_fundamental_seed0_terminal_20260912.tgz`, not just the new preparation summary. The inherited OFF plan SHA is `e275ebf4f27f0a3b35fd87ac983843e9edcf73e1239bd01be60f4952f3845fc8` and matches `R/readout_preparation.json`.

All four new plans have **exact equality** with the original OFF cases, requests, prepared native inputs, and base-file inventory. All 192 returned prompt-token arrays and rendered prompts equal the corresponding actual original OFF inputs. Decode settings are temperature 0, generation seed 20260912, maximum 64 output tokens. Adapter identity is the intended changed input, not a falsely identical treatment condition.

The panel remains 32 arithmetic IDs `eval-addition-000` through `031` plus 16 paraphrase IDs `eval-memory-000-0` through `015-0`. There are zero new OFF calls. The other 64 evaluation/confirmation IDs are absent from all new requests. Critically, **zero original-training-form memory requests** occur in these repetition readouts: their rendered prompts do not equal the original memory training contexts. The earlier SEQ100 training-prompt result applies to the original seed0 checkpoints, not automatically to these four new checkpoints.

## 3. Independently checked repeated material and fit accounting

The two original corpus hashes match S0. Independently compared **every original row and every repeated copy**:

- Short: 1,280 rows = 80 originals × 16 independent sequences. Each copy preserves original context, target, group, order, and source-event IDs, with one explicit supervised EOS appended.
- Long: 80 rows; each is exactly 16 concatenated copies of the same original context/target/EOS span triple. Long rows are repetition of the same question form, not new paraphrases or independent facts.
- The native context's existing EOS tokens remain masked; `add_eos=false` prevents another automatic supervised EOS. This is one supervised EOS per copy, not one total EOS occurrence across the native template.
- The source-row order is preserved in exported metadata. Independently reconstructed the trainer's no-pack lexical group ordering, group shuffle using `seed*1000+epoch`, and four-groups-per-update schedule. All recorded schedules for audit seeds 0,1,2,17 match; **only seed0 was fitted here**. Extra CPU-audited schedules are not scientific seed replications.

| Quantity per fitted cell | Short | Long |
|---|---:|---:|
| Rows per epoch | 1,280 | 80 |
| Copies per original per epoch | 16 | 16 |
| Native total input tokens per epoch | 72,272 | 72,272 |
| Native supervised target tokens per epoch | 14,592 | 14,592 |
| Maximum actual sequence length | 61 | 976 |
| Configured max-length ceiling | 2,048 | 2,048 |
| Batch size / gradient accumulation | 4 / 16 | 1 / 4 |
| Microbatches across four epochs | 1,280 | 320 |
| Optimizer updates across four epochs | 80 | 80 |
| Total input across four epochs | 289,088 | 289,088 |
| Total target across four epochs | 58,368 | 58,368 |

The native totals independently equal 16 times the original per-row audited lengths: 4,517 input / 912 target per epoch. Training input includes the supervised target positions; do not double-charge targets as additional input. Each repeated epoch has 14,080 arithmetic / 512 memory target tokens, including EOS. Each fact is presented **64 times across four epochs**, versus four in the original fit; the memory target share remains **32/912 = 512/14592**, not an increased relative loss share. Across the four new fits, input/target totals are **1,156,352 / 233,472**.

All manifests agree with their frozen per-cell configs: seed0, rank8, alpha16, dropout0.05, LR0.0003, four epochs, AdamW, no packing. They report zero nonfinite batches, finite final losses, zero dropped/truncated/split material, and exactly the expected counts. `max_len=2048` is a cap, not observed length. Tokenization was not rerun here: arithmetic extrapolation from the original native per-row audit, exact span-copy checks, the new native reference receipt, and executed-fit manifests agree.

All four command receipts use the default fresh-fit path, without `--init-adapter`; manifests contain no warm-start receipt. Each readout's single arm-specific adapter inventory matches its fit result, for both arithmetic and memory. Warm-start support in the trainer source does not mean these fits used it.

Evidence: `R/manifest.json`, `R/main_native_reference_check.json`, `R/fit_plan.json`, four `R/*_{short,long}.json` corpora, `R/cells/*/fit/adapter/train_manifest.json`, `fit/result.json`, and `fit/worker/process.json`. Trainer/exporter and all readout source pins match `/tmp/astra_level0_source_ed3aac9f.tgz`; the fit script hash matches `/tmp/astra_repetition_fit_20260912.py` and the frozen plan.

**Design limitation:** matched tokens and optimizer group schedules do not make short/long runs identical except for a mathematically isolated attention effect. Microbatch/accumulation layout differs and dropout remains active. All content is repeated, including competing arithmetic targets. This is not a memory-only dose contrast, fresh dataset replication, or general “long context” test.

## 4. Honest cost and release accounting

Actual inference usage was recomputed from returned token-ID lengths and per-call timestamps, then compared to usage/reduction receipts:

| Cell | Calls | Actual input/output tokens | Output ceiling | Generation seconds | Fit supervised s | Readout supervised s |
|---|---:|---:|---:|---:|---:|---:|
| teach_short | 48 | 2,131 / 472 | 3,072 | 19.977191 | 348.688753 | 108.952332 |
| control_short | 48 | 2,131 / 472 | 3,072 | 20.543492 | 342.793742 | 97.254086 |
| teach_long | 48 | 2,131 / 472 | 3,072 | 20.467202 | 304.660179 | 96.618370 |
| control_long | 48 | 2,131 / 472 | 3,072 | 20.913317 | 304.149849 | 114.515955 |
| **Total** | **192** | **8,524 / 1,888** | **12,288** | **81.901202** | **1,300.292523** | **417.340742** |

These are 1,888 actual output tokens, not 12,288 consumed tokens. No original OFF generations are charged again. Generation seconds are call windows, not total GPU compute. Trainer-reported rounded training-loop times are 307.0/303.4/266.7/266.3 seconds in the table's order, totaling 1,143.4 seconds; these differ from supervision.

Fit + readout supervision totals **1,717.633265 seconds = 28.627221 A40-minutes**. Adding the previously audited SEQ098–100 baseline of 1,510.135936 seconds gives **3,227.769201 seconds = 53.796153 A40-minutes**, or **36.203847 minutes** below the initial 90-minute allocation **on this specific accounting through these phases only**. This is not the current remaining budget once Main's concurrent/later work is included.

Independently recomputed outer launch-to-Main-release windows:

| Cell | Fit full reservation s | Readout full reservation s |
|---|---:|---:|
| teach_short | 561.867506 | 235.740637 |
| control_short | 510.252889 | 214.890821 |
| teach_long | 535.155861 | 231.064941 |
| control_long | 483.895962 | 201.372390 |
| **Total** | **2,091.172218** | **883.068789** |

Combined outer reservations are **2,974.241007 seconds**, including audit/idle gaps. They are summed concurrent resource windows, not elapsed wall time or active GPU compute. No monetary rate is available.

All eight fit/readout supervision receipts report successful zero-return-code cleanup and verified owned process release. All four readout backend handles are recorded closed; all eight archived full-release XML snapshots contain zero GPU process entries. Final readout releases on September 12, 2026: control_long 18:46:18.641328 UTC; control_short 18:46:44.340660 UTC; teach_long 18:47:08.905860 UTC; teach_short 18:47:26.032096 UTC. These are archived Main release checks, not a live vacancy assertion.

Evidence: `R/fit_main_release.json`, `R/readout_main_release.json`, cell launch receipts, `fit/worker/supervision.json`, `readout/run/worker/supervision.json`, native usage/call records, and corresponding release XML files. Available metadata rehashes match fit/readout inventories. Actual base/adapter weights remain unavailable locally; their hash checks and runtime custody are attributed to native/Main receipts, not re-certified by this review.

## 5. Notebook 18:39: contradicted predictions versus unidentifiable claims

The relevant exact entry is `research_loop/COORDINATION.md:5618`, especially items 1–2 at lines 5620–5621 and prediction item 5 at line 5624.

### A. No observed development-memory benefit — established

“More repetition improves memory” interpreted as a prediction for this **actually measured seed0 dev panel** is contradicted: all four cells remain 4/16, constant red, with no short/long difference or improvement over original seed0. This is the supported negative outcome, not evidence that repetition never helps.

### B. Literal in-sample prediction — untested on the new checkpoints

The notebook specifically predicts that **in-sample memory rises well above 4/16**. The new capsule evaluates the original development paraphrases, not the original training-question form. Therefore that literal prediction is **not directly falsified or confirmed** by these readouts. The earlier SEQ100 original-question failure involved different, unrepeated seed0 checkpoints. Do not silently transfer that outcome to these repeated-fit checkpoints or propose another run as a condition of this review.

Smallest correction in any downstream outcome statement: “Repetition did not improve the fixed seed0 development-memory panel; original-training-prompt recall after these repeated fits was not measured.”

### C. “If it does not, the fault is loss share or QA, not the adapter” — MEDIUM inference overclaim

The experiment does not identify that causal disjunction or exclude adapter capacity/optimization/interference/other readout effects. Both content classes were repeated together, relative memory target share is unchanged, and no alternative architecture, memory-only fit, or repeated-checkpoint training-form readout is supplied. The conditional conclusion is not licensed even if the literal in-sample prediction later fails.

Smallest correction: “No dev-memory improvement was observed; the relative loss share, question/readout, optimization/interference, and representational explanations remain unresolved.” Do not claim a separate adapter is needed or proved unnecessary.

### D. “Not interference…two things that are not competing” — MEDIUM inference overclaim

Equal poor memory in teach/control does not demonstrate absence of interference. The control omits PREDICT-before-ACT, but retains 64 arithmetic ACT/COMPUTED targets and the same memory budget; it is not memory-only or behavior-free. The result shows no observed additional memory disadvantage of the teach ordering here, not that arithmetic and facts cannot compete or that separation could not help.

Smallest correction: “No differential memory penalty from the teach ordering is observed; common interference and the effect of adapter separation are untested.” This does not recommend an architecture change.

### E. Long versus short prediction — observed tie, mechanism unidentifiable

The notebook's expectation that long should not outperform short by much is consistent with the observed exact tie. A tied floor-like response pattern does not establish general equivalence or validate the proposed storage mechanism. The hypothetical statement that a long advantage would mean copying from context rather than weights is also unsupported: evaluation prompts are identical to actual OFF and contain no repeated fact-answer context. Training-time attention changes would not themselves prove test-time contextual answer access. The hypothetical branch was not triggered here.

### F. Exposure description — LOW concrete count correction

Notebook item 2 describes the habit as appearing in every one of 80 original rows, approximately 320 exposures over four epochs. The actual original corpus has **64 arithmetic-form rows + 16 color-only rows**, so the arithmetic response-order pattern appears in **256 row presentations** over four epochs, not 320. Repetition makes that **4,096 arithmetic row-copy presentations**, while each fact has 64 presentations. This correction leaves the qualitative imbalance but avoids incorrect counts. Neither a low loss nor failure to extract a color proves absence of any latent acquisition.

### G. Fading/plasticity — outside this capsule

The notebook's request for a fading curve under subsequent writes is not tested by fresh repetition fits and one readout. This review supplies no fading, stability/plasticity, parent–sleep, H1/H2, or cognition result, and does not duplicate Main's ongoing work.

## Final disposition and key hashes

**Numerical/custody PASS; no capsule/reduction correction or rerun required.** The interpretation corrections above are the minimum qualifications needed when converting the 18:39 hypotheses into conclusions. They do not authorize edits, new fits/readouts, or a separate-adapter intervention.

- `R/fit_plan.json`: `8786be46beb9d5c6948f407b39ac25526dee4d4d1a5b9192d49c6ba9b579a67f`
- `R/manifest.json`: `eba01c800d4bf6e9772cefec413be8c6f41b26f0d6e9ab0ced66862d7f348160`
- `R/fit_main_release.json`: `c67be7cff7abcfcfbbf6d57786893dbb7688dae04c8a55d05cfa87dbcbffe0d0`
- `R/readout_main_release.json`: `3ad81be3c63a67e0b307856c11397f3a8016345d214f905becc3777786b3b660`
