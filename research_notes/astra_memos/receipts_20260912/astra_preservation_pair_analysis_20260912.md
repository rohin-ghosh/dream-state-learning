# Completed preservation pair — 2026-09-12

**Validated matched artifacts; both arms fail unchanged G9 and G11.** Lambda0.1 lowers spill substantially but also sharply reduces acquisition. Its acquisition interval includes zero and spill remains above 0.03. This is not a successful selective writer or readiness result.

Full frozen-reducer output: `/tmp/astra_preservation_pair_analysis_20260912.json` (SHA-256 `7d97658367e5c5d0a02498c18a020cce9117775c98b91a82db3c4251f0ee2a57`). No partial results, source edits, GPU, SSH, or Git operations.

## Inputs and execution

- Control: `/tmp/astra_preservation_control_terminal_20260912/astra_A1_preservation_bank0_ts2_lam0_20260912_attempt1`.
- Treatment: `/tmp/astra_preservation_positive_terminal_20260912/astra_A1_preservation_bank0_ts2_lam01_20260912_attempt2`.
- Optional historical bank0: `/tmp/astra_seed_bank0_evidence_20260912/runs/astra_A1_memory_dose_S1_F_r16k16_ts2_20260912`.
- Ran committed `organism_v6.memory_preservation_analysis` via `CUDA_VISIBLE_DEVICES='' /tmp/astra_preservation_cpu_20260912/bin/python -B -m`, with these roots, `--historical`, `--positive-implementation-sha256 9a5ad83a246c07e0bf2094bafc9473c66952d56071d7a9cc75e93c2000bdf574`, and exclusive `--output-new` targeting the JSON above. Exit 0; `valid=true`, `metrics_status=validated_current_pair`, no errors. NumPy-absent warning only.
- Reducer SHA-256 remains `25f03513e6092790337849282cdc780b4305518f760e08afcb7e81b2f28e4754`. Native scorer SHA-256 `ab98329c433cb085cd53e1c766db350f1bb0fe2efb9181e24a3678c0d31a76e3`; source checks pass, unchanged `summarize_eval` / `evaluate_gates` with bootstrap seed0.
- Explicit control producer `a361af202a85e041dad119d57da7a54f583045e9472a358ae8a5efd31a32ef9c`; explicit treatment producer `9a5ad83a246c07e0bf2094bafc9473c66952d56071d7a9cc75e93c2000bdf574`. Differing implementations remain recorded. Main authorizes their difference as cache-validation arithmetic only; this reduction does not independently verify that source diff.
- Locally hashed `/tmp/astra_preservation_positive_terminal_20260912.tgz`: **`c401bfdc6c85da16b52f760e879148ad93acebb016e4066395d1695a6363034e`**, matching Main's supplied capsule hash.

## Matching and cache validation

Both arms validate original source corpus/all three bank input hashes, plans, token preflight, setup/fit identities, DONE, finite losses, 9,693 ordered loss records and native report agreement (bank0, no pooled-bank substitution). Both have 12,924 items, epochs3, batch4, rank8, alpha16, dropout0.05, seed2, lr1e-4, max_len512, **749,985 CE input / 711,213 CE supervised tokens**, no truncation or boundary straddles. Ordered encoded CE hash `3c311ccb5ed8f0814334b928fa4ebaa2999a7a3fca2e0932e6ae5f103e42a55f` matches.

Recorded initial LoRA hash **`2724901a6dbf50cd74d1424041e7f8a4c4ca6769621a34a904ac3a6b0b4abbce`** matches, as do model-file inventories, model dtype, trainable names/dtypes, torch version and anchor hash. Model inventories are recorded provenance, not a fresh rehash of absent base weights. All **1,313 cues**, order, cue/candidate metadata and full serialized **OFF scores match exactly**: zero changed IDs and zero maximum differences for raw probability, mass, logp and abstention.

Actual positive OFF tensor was loaded **CPU-only**: **48 × 152,064**, detached, finite float32; tensor SHA-256 `e245e790cabc7fef53e32b111b43244f26ff9ea0963883959fb622fba44f3cf8`, 29,197,865 file bytes. Normalization checked using float64 `log_softmax` with `atol=1e-10, rtol=0`; maximum error **3.064215547965432e-14**. Cache storage and training KL remain float32, not converted training objectives. Cache metadata matches fit/plan, frozen no-adapter OFF, temperature1 and last-prefix-token position. Cache producer is the repaired treatment producer.

Anchor bytes hash `cf67c3f4939b09ae46d1dea316c503275f6c9c94af6ddbc9402f360885dd503b`; 48 deterministic training-only anchors pass source/cue disjointness checks. Lambda0 skips cache/KL/anchor forwards entirely. Lambda0.1 uses one round-robin anchor per step: **9,693 distribution positions / forwards**, **77,544 anchor input tokens**; first45 anchors visited202 times, last3 visited201 times. The extra anchor dose is separate from unchanged CE dose.

## Native metrics

| Metric | Lambda0 | Lambda0.1 |
|---|---:|---:|
| Dose16 I_d, n=16 | 1.921469873 | 0.152267044 |
| Native I_d interval | [1.202607550, 2.682502692] | [-0.023955285, 0.333065840] |
| Total frame spill | 0.415536920 | 0.036657910 |
| Similar spill | 0.416577277 | 0.039541842 |
| Unexposed spill | 0.321308537 | 0.035200923 |
| Bicycle spill | 0.508724947 | 0.035230965 |
| G9 | FAIL | FAIL |
| G11 | FAIL | FAIL |
| Dose16 correct conditional probability OFF | 0.259649920 | 0.259649920 |
| Dose16 correct conditional probability ON | 0.685322980 | 0.294129798 |
| Dose16 conditional probability delta | 0.425673060 | 0.034479878 |
| Dose16 candidate mass OFF | 0.00873765625 | 0.00873765625 |
| Dose16 candidate mass ON | 0.99815843125 | 0.01028710625 |

G9 requires I_d interval lower bound >0 **and** spill ≤0.03; treatment fails both criteria. Native spill has no interval in this report; none is invented. Dose-curve conditional deltas for doses **0/1/4/16**: control **0.072308921 / 0.346357087 / 0.278830599 / 0.425673060**; treatment **0.020375830 / 0.032188882 / 0.033973535 / 0.034479878**.

| Abstention probability | Shared OFF | Lambda0 ON | Lambda0.1 ON |
|---|---:|---:|---:|
| Unexposed | 0.013914925 | 0.00000465625 | 0.01208008125 |
| Similar | 0.012642600 | 0.00000924375 | 0.01213168958 |
| Bicycle | 0.016815940 | 0.00000816250 | 0.01740600833 |
| Dose16 | 0.01180268125 | 0.00000668750 | 0.01217591250 |

G11 remains unexposed/bicycle ON abstention ≥0.5 and dose16 ≤0.1. Treatment remains near low OFF abstention, far below the two required ≥0.5 values; preserving OFF does not teach abstention.

## Paired effect and costs

Treatment minus control: **I_d −1.769202829**, paired-owner bootstrap interval **[−2.433713142, −1.144942376]**, n16; **spill −0.378879010** (similar −0.377035435, unexposed −0.286107614, bicycle −0.473493982). Dose16 correct conditional probability ON decreases **0.391193182**; candidate mass ON decreases **0.987871325**. These are descriptive paired-owner statistics for one learner seed, not independent fit replications. Lower spill alone is not positive evidence of preserved acquisition: the treatment largely suppresses the baseline writing/format-mass effect, with insufficient acquisition and still excessive spill.

| Recorded quantity | Lambda0 | Lambda0.1 |
|---|---:|---:|
| Mean CE | 0.716962722724 | 0.718169213161 |
| Final CE | 1.093894958496 | 1.091395497322 |
| Mean KL | absent | 0.0160276540784 |
| Final KL | absent | 0.00773466844112 |
| Final objective | 1.093894958496 | 1.092168964166 |
| Fit wall seconds | 1227.287121 | 2458.878753 |
| Cache seconds | 0 | 18.782232 |
| Eval seconds | 241.1 | 238.4 |
| Captured stage total seconds | 1468.387121 | 2716.060985 |

Treatment fit took **40.98 min** versus **20.45 min**, approximately2×; stage totals **45.27 vs24.47 min**. These are captured stage clocks, not full lease/controller overhead or failed-attempt1 costs. Positive captured result says WORKER_COMPLETED **2026-09-12 12:45:34.293308 UTC**; worker88114 cleanup receipt says owned group empty, GPU processes absent, GPU2 reservation release verified, no cleanup error. These are receipt observations, not a fresh resource probe; Main owns reconciliation.

## Evidence limits

- Historical bank0 inputs/fit/raw evaluation validate, with exact cue/OFF agreement and zero control-minus-historical acquisition/spill deltas. Historical report and base-file inventory are absent; bridge is descriptive, not proof of historical/native weight equivalence or a third matched arm. Both eval model locators are `hf`; fit path/provenance/instrumentation differences remain exposed in JSON.
- Both captured adapters omit weights. `/tmp/astra_preservation_positive_weights_20260912.txt` records treatment adapter hash **`f3273ec961240871a169ee95b0992a8161ec777311189c6d33431b1732213ede`** at the treatment's remote adapter path; receipt SHA-256 **`219755beef052850050fa11d341f34b66a671015bbf971f2178b74c749a9013d`**. Control remote hash remains **`c5bc4b2d7599d7f30732bb3adb98a1415206ecca41e0f96ce6d1db89015d6516`**. These are remote hash receipts, not locally authenticated weight bytes or evidence of adapter equality.
- CPU cache checks and matched recorded initial-weight/model hashes do not independently reconstruct training or authenticate official model provenance. The approved producer-source difference is explicit, not silently collapsed.
- This fixed-prefix OFF regularizer is **not OEL/SDFT reproduction**. Both frozen gates fail. No new objective/threshold, readiness claim, or experiment selection follows from this handoff; Main owns scientific interpretation and next decisions.
