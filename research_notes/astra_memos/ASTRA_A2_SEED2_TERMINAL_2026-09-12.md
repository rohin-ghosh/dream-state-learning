# A2 optimizer seed2 terminal fits/evals — SEQ-067

Observed September12,2026 at09:07:22UTC; queue0052 finished09:04:34UTC with RC0.
Frozen source `f2e5b65e9c5dc3f7b7cdf15cb1b97b114ad4994d`, node2,
run `~/v6_out/astra_A2_memory_dose_D32_CF_r16_b_ts2_20260912_attempt2`.
Fits/evals completed; no claim that a report stage or campaign completed.

| Bank | Mean binding I_d_frame | Within-bank paired-owner95% interval | Spill | G9 |
| --- | ---: | --- | ---: | --- |
| 0 | 1.184902794133669 | [0.736801601373312,1.8112251421790742] | 0.3231037216369375 | FAIL |
| 1 | 0.7435414468523857 | [0.18527321253195464,1.3734456861839741] | 0.29437713366212465 | FAIL |
| 2 | 1.9323354878015453 | [1.0418108995978572,2.9366826704478126] | 0.3564715626294083 | FAIL |

Each bank has1313evaluation cues and64owners, with16paired dose16owners
in the2000-resample,seed0 percentile interval. Spill is the equally weighted
mean of three component means:48similar-exposed,16unexposed,48bicycle-exposed
owners. All required controls are present and source-compatible. Unchanged G9
requires binding lower bound>0 and spill<=0.03; spill fails in every bank.
No new thresholds, outcome selection, pooling or optimizer-seed uncertainty claim.

Increment since SEQ-064: two evaluated bank artifacts, one completed fit,
zero new optimizer-seed configurations. Across the completed A1/A2 evidence,
15evaluated bank artifacts fail G9; they are not15independent learner seeds.
No H1/H2, selective-memory qualification, parenting effect or clean ancestry.

Raw/source capsule `receipts_20260912/astra_A2_seed2_terminal_20260912.tgz`,
SHA256 `1ddc90bd8cd2ab4beeb79d8947c56cf96fe955cf79c5d378ec68c2b23d163c0b`.
75payloads verified by recovery agent; main verifies archive digest.
Includes original run/queue receipts, train metadata, evaluations, material,
frozen source and unchanged analyzer output; adapter files are hash-referenced,
not bundled. Analyzer SHA256 `e1327b3d2fdc060e33aad3d088beada167226437a9b1e6f28b819c6b5959eea9`.
Prior08:34snapshot remains unchanged. Reproduction uses the included
`ANALYSIS_RECEIPT.json` command and full `analysis.json` denominators.
