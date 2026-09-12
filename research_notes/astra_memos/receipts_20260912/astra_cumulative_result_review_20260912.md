# Independent bounded SEQ-092 cumulative interpretation audit

Date: 2026-09-12 UTC. Scope: local, CPU-only interpretation and captured-evidence audit. No GPU access, network, experiment rerun, git operation, repository modification, or promotion decision. The requested summarizer was found at `/tmp/astra_summarize_cumulative_20260912.py` (not `script/tmp/...`).

## Verdict for paper integration

**PASS for bounded exploratory reporting; minor wording/robustness fixes recommended. No blocking numerical or artifact-consistency defect found. NOT evidence of sequential retention, selective-memory qualification, learner-policy improvement, parenting, or model-origin authentication.** This is an interpretation audit, not a scientific-claim expansion or launch authorization.

Suggested paper text:

> In one training-seed/one-bank fresh-base reconstruction comparison, OLD native-fact ON-minus-OFF conditional target-probability gain increased from 0.292056 to 0.341508 (A2/A1 = 1.169323), whereas OLD frame gain decreased from 0.425674 to 0.209910 (ratio 0.493124). NEW bicycle-control gain exceeded NEW frame gain in both NEW-only and cumulative fits; paired frame-minus-bicycle gains were -0.040570 and -0.261387, respectively. These results show assay-dependent reconstruction with substantial control spill, not selective-memory qualification or retention through updates. The 16 OLD and 32 NEW owners are within-run cohorts, not independent learner replications; training histories and compute were unmatched.

## Verified effects and denominators

All values below were independently recomputed from the four captured `stages/*/eval.json` files, not merely transcribed from the summary. For each cue, the target probability is `p_raw[target] / sum(p_raw[four colours])`; gain is ON minus OFF. OLD native fact averages three paraphrase gains within each owner and then over the 16 dose-16 owners (48 fact rows); OLD frame uses one frame cue per owner. NEW uses 32 matched owner pairs, one car-frame and one bicycle-frame cue each. Each NEW gain/paired-gain mean has 32 defined observations; no hidden missing-value denominator was found.

| State | OLD fact gain | OLD frame gain | NEW frame gain | NEW bicycle gain | NEW paired frame-minus-bicycle gain |
|---|---:|---:|---:|---:|---:|
| A1_before | 0.292055900 | 0.425674163 | 0.005778857 | 0.008962761 | -0.003183904 |
| AN | -0.004837211 | -0.020875075 | 0.673275796 | 0.713845457 | -0.040569661 |
| A2 | 0.341507593 | 0.209910083 | 0.359222944 | 0.620609622 | -0.261386678 |

- OLD native fact ratio is **1.169322698810651**; OLD frame ratio is **0.49312385298838074**, with absolute frame-gain change **-0.2157640797359058**. Different assays explain the opposing directions; the ratios are not interchangeable and neither measures survival of A1 parameters.
- NEW bicycle ON colour mass / abstention: AN **0.9992159275661711 / 3.4515232417038036e-7**; A2 **0.9979792862848821 / 2.5757536842502635e-7**. The memo's rounded values agree. These controls prevent a selective-memory interpretation in this assay; they do not establish a universal absence of factual memory.
- The supplement's entire owner-pair metrics, paired differences, means, and counts agree with independent raw-score recomputation, including log-gain, raw-mass gain, and abstention gain. Log-gain is a difference of natural logs of conditional target probabilities, not native target-versus-competitor log-odds. No new threshold or gate is introduced.
- Original generic NEW `retention_ratio` fields are **116.50674619348526** (A1→AN), **62.1615935397911** (A1→A2), and **0.5335450140935015** (AN→A2). The first two divide by the tiny pre-exposure effect 0.0057788567430122695; the third also compares independently fitted states. None is update-retention evidence. The memo correctly excludes these from its claim; preserve original JSON rather than silently relabeling it.
- A1_before and A1_after **entire cue arrays** match exactly, including ON/OFF raw probabilities; maximum raw-probability drift is exactly zero. Whole eval-file hashes differ because state metadata/timing differ. This supports these two fixed-read/reload observations, not update continuity, optimizer resumption, arbitrary recovery, or generated-task accuracy. The path performs candidate scoring, not task generation.

## Training and gates

The captured corpora contain exactly OLD **12,924**, NEW **2,048**, and union **14,972** rows. Union equals OLD followed by NEW, with OLD row identities/order and recorded encoding hashes unchanged. This audit verified recorded encoding equality, not a fresh tokenizer execution. NEW has 128 events across 32 owners, four events per owner and 16 renderings per event. The OLD dose-16 cohort and NEW owners are disjoint.

A1 is the inherited `Fit(base, OLD)` artifact; it was not refitted during this run. AN and A2 are separately initialized base+LoRA fits, not descendants warm-started from A1 or AN. A2 runs `(OLD, NEW)` in each of three epochs rather than `OLD` for three epochs followed by a continuation on NEW. Even with unchanged OLD minibatches (12,924 is divisible by batch size four), later OLD exposure follows a different optimizer/adapter history. Rank 8, alpha 16, seed 2, three epochs, chronological order, batch size four, max length 512 agree with the records. Dose, update count and elapsed cost are unmatched; this does not isolate cumulative-memory retention from dose/history effects.

Native CPU re-evaluation reproduces **all** recorded OLD summaries, native gates, and generic contrasts exactly after JSON normalization. `memory_dose.G9_frame_binding` and `memory_dose.G11_abstention` fail for all four reads. `G7_retention` is unevaluated (`null`) for ordinary state entries; it passes only in the additional `A2_with_native_fact_retention` entry supplied with 1.169322698810651. Other native metrics also pass, so “G7 alone passes” must not mean “G7 is the only passing native metric.” These are native assay labels, **not mission/sprint G0–G6 gates**. No G3/P1/G5/H1/H2 closure follows.

## Costs: distinct units and accounting boundaries

| Newly executed fit | Rows | Optimizer updates | Native fit-loop seconds | Nonpadding input-token passes | Shifted supervised-token passes |
|---|---:|---:|---:|---:|---:|
| AN | 2,048 | 1,536 | 199.4 | 171,264 | 165,120 |
| A2 | 14,972 | 11,229 | 1,416.8 | 921,249 | 876,333 |
| Total | — | 12,765 | 1,616.2 | 1,092,513 | 1,041,453 |

Updates equal `3 * ceil(rows/4)`. Input and supervised counts match three times their corpus-audit totals. Native `tokens` counts nonpadding input positions, not distinct tokens; `supervised_tokens` counts valid shifted loss positions. These full-token-supervised frame corpora are not answer-only supervision. The first-100-step throughput fields are samples inside these same loops, not extra fits or additional updates.

Four reads total **965.2517131960049 scoring seconds**, **1,160 forward calls**, **84,800 candidate sequences**, and **3,511,832 padded forward-input positions**. Per read: 1,377 cues; 20,752 colour-candidate sequences plus 448 abstention sequences = 21,200 measured candidate sequences; 290 forward calls; 877,958 padded positions. Thus total abstention sequences are **1,792**, already included in 84,800. Prepared `work.candidate_sequences` excludes abstention; `measured_work.candidate_sequences` includes it. Candidate spelling variants, OFF/ON passes, shared forward work and prompt rows are not interchangeable counts or extra learner trials.

**2,953.833433587999 seconds** is the controller's recorded continuous-reservation interval, not active-GPU compute or a complete lease/campaign cost. Fit-loop timing excludes model load and save; scoring timing excludes read setup/teardown. Their sum leaves approximately **372.381720392 seconds** within that recorded interval, not an estimate of idle GPU time. Native `supervised_seconds` is per-worker supervisor wall time, not supervised-token work. Inherited A1's **9,693 updates / 1,327.3 fit-loop seconds** are excluded from the new-fit totals and must remain separately labeled.

Launch receipt: **2026-09-12 15:16:50.264833 UTC**. Controller `RUN_STARTED` timer begins **15:16:50.393778 UTC**; `RUN_FINISHED` is **16:06:04.227211 UTC**. Main terminal release observation is **16:07:39.725090 UTC**, approximately 95.5 seconds later and outside the reported controller interval. The memo's launch and finish timestamps are correct but are not exactly the endpoints of its monotonic cost timer. No p50/p95, peak VRAM, active-compute time, or complete-campaign throughput is established.

## Capture repair, provenance and figure

- The initial helper writes `report.json` before comparing the reducer's integer-keyed in-memory dose dictionary against JSON's string-keyed dictionary. The repaired helper normalizes through JSON, compares a new CPU replay with the preserved report, and records equal SHA-256 values plus `gpu_experiment_rerun=false`. I independently reproduced the integer/string mismatch and exact normalized equality for native summaries, gates and contrasts from captured evaluations. This is a capture-comparison repair, not experimental failure or an extra GPU fit/read. The original native replay file and initial failing traceback are not present in this local capsule; the native full-reducer replay/weight recheck is attested by its receipt and helper code, not newly performed here.
- All manifest-listed captured files and supplement-listed capture hashes checked out, as did six distinct worker PIDs, DONE/job/eval bindings, and cleanup receipts. The inspected three local source files match their recorded SHA-256 identities. The supplied source identifier is `3ee4c706080e758537b4dc802bdeef4ead38a158`; this audit did not inspect git objects or independently authenticate that commit.
- The terminal archive is **4,802,823 bytes**, with the stated SHA-256. Every archived regular file matches its extracted counterpart. It contains reports/raw evaluations/logs/metadata, **no adapter directory or safetensors weights**. Native receipts report actual A1/AN/A2 tree verification and release; this local audit verifies receipt consistency, not those absent weights or current remote GPU state. A recorded model path or hash is not official model-origin authentication: **UNRESOLVED_LOCAL_HASHES_ONLY remains unresolved**. No current remote weight availability, standalone backup, or independent cross-host transfer authentication is claimed.
- Summary JSON and CSV agree with recomputed results. The summarizer regenerated JSON/CSV/SVG **byte-for-byte identically** in a separate `/tmp` directory. SVG XML parses; all 12 data-bar heights, signed directions, x positions and three-decimal data labels agree. Both small negative AN OLD bars extend below zero correctly. Owner-count, four-colour conditional-probability, fresh-base and one-seed labels are accurate. No learner-level error bars appear. XML/data inspection is not a raster/font-layout review.

## Severity and small fixes (recommendations only)

1. **LOW — gate wording:** replace “the native-assay G7 ratio alone passes” with “the supplied native G7 ratio passes, while native frame-binding and abstention gates fail; other native metrics may also pass.” This removes ambiguity without changing results.
2. **LOW — summary robustness:** derive `new_n` from verified `n_pairs` and assert 32 plus each plotted metric's defined-value count; the current script hardcodes 32. Bind/assert `generation_calls=0` against the captured protocol instead of presenting a hardcoded value as independent measurement. Current values are correct; no rerun is needed.
3. **LOW — self-contained paper caption/cost labels:** explicitly say “16/32 owners, not independent learners; unmatched training dose/history,” label OLD as the dose-16 cohort, and retain the inherited-A1 and controller-versus-later-release cost boundaries. Preserve negative signs if restyling the figure; an optional negative tick/below-zero annotation would improve readability.
4. **Claim guardrail, not a new defect:** retain provenance qualification and the exclusion of selective-memory/update-retention/H1/H2 claims. Native tree-verification statements should be attributed to native receipts, not to this metadata-only independent audit. Do not use native PASS/status strings as mission gates.

No source artifact was edited and no repair was applied. These recommendations do not require repeating the experiment.

## Exact SHA-256 identities

Root abbreviation `R` below means `/tmp/astra_cumulative_terminal_20260912/astra_cumulative_20260912_attempt1`; all other filenames beginning `astra_` are in `/tmp`. These are full SHA-256 hashes of bytes actually read, not reconstructed identifiers.

| Artifact | SHA-256 |
|---|---|
| `research_notes/astra_memos/ASTRA_CUMULATIVE_TERMINAL_2026-09-12.md` | `785e2e15a048dff2dbda503e81b000fe57f82b41835ba2a188da52709ec4e5f8` |
| `R/report.json` | `c641c3d3261b10539c934ecfe7828fe76eb12a6af6d99f48a9a7f45ba7321404` |
| `R/MAIN_TERMINAL_AUDIT.json` | `db5df238e32e54c4473fd99fc2586b0ef113dd70a7b06d2fe8922f566c07182e` |
| `R/RUN_FINISHED.json` | `045a782e1499f09c27423b513eec898b19ce4c41404265a86d0b7a4492f6b416` |
| `R/manifest.json` | `dc9f33071392c374da4e77c19b9c7f87de0bbe2ee2d4bc503c954c6078910f3d` |
| `astra_cumulative_specificity_terminal_20260912.json` | `5075d65e3e8ff644f9d1e3369540210de5d57906a9e4a05f144169363b1ed029` |
| `astra_cumulative_summary_20260912.json` | `6f58e1705973d28eef9157542d0a569cfdc1f1d4bd2c2d66e5056b4473893845` |
| `astra_cumulative_summary_20260912.csv` | `112108796bdce674e19243062e12ac6164b479c6348e877ca2c81fc4b857412d` |
| `astra_cumulative_summary_20260912.svg` | `d4558fa695e67b9d161a7364879831c31a16ad351151f8da23384a70b5ee11fe` |
| `astra_summarize_cumulative_20260912.py` | `b0964c84f3fb23e8e97ae93df8bbe15dcffbb02eb44446a1e2cf1f3bfd8a2a69` |
| `astra_capture_cumulative_20260912.py` | `6f152686095185c54b9416899bcaf4a6eaed632d255ada1b20c4c0d4779c649c` |
| `astra_capture_cumulative_repaired_20260912.py` | `bfacac2020b5bcd4bc4e1b3f593de6e0903280c970cfbbafce47280f908905f2` |
| `astra_cumulative_terminal_20260912.tgz` | `c5a7649d14886ac86fdb966086fb08fe6440a6b766ba904a34ae20ec96266d9c` |
| `R/stages/A1_before/eval.json` | `974fb1aca21931f323764a77a286b0de933341ef02da80fdc1af8c57678ba1d9` |
| `R/stages/A1_after/eval.json` | `53ed66693e2286d5934c90ba19540e6a0fd8f9ca708f611854c5dd12a5d2bf3d` |
| `R/stages/AN/eval.json` | `90de065853aaff0f32ed6a96c76d0fe8b196c669ab78b57e96a2d4f8a9c7d224` |
| `R/stages/A2/eval.json` | `abbb589eec111936e097021fb9f6fbb109e6fcd0bc609ea95496b89a0f39540c` |
| `gpu/astra_memory_cumulative_diagnostic.py` | `62e58de3fe27bd63b6d1b737bcc8071e95bce9cc343562aff7e5eb901b7cd112` |
| `organism_v6/memory_dose.py` | `ab98329c433cb085cd53e1c766db350f1bb0fe2efb9181e24a3678c0d31a76e3` |
| `organism_v6/run_reasoning_neutral.py` | `dd4f0a72cddc8226fa48ce50ab0faa6dd4e75f9db510aa89cfb5224898ee7496` |
| `astra_cumulative_independent_check_20260912.py` | `109c106b3968bc43849386d8b56c6126b6493167ce9abb34ed78a3fdafaef2a3` |
| `astra_cumulative_independent_check_20260912.json` | `2e6c06db6324a4c959264651d13cf83ef10889f2a3fd19b9a3c055c40159ebdb` |

Independent check command: `python3 -B /tmp/astra_cumulative_independent_check_20260912.py` (completed PASS; output creation is exclusive, so preserve its existing result). Regenerated summaries remain at `/tmp/astra_cumulative_independent_replay_20260912_3lrqn42g/`. The separate CPU native-summary/gate/contrast replay also passed exact JSON-normalized equality; it did not invoke the full native reducer, live model, tokenizer, or weights.
