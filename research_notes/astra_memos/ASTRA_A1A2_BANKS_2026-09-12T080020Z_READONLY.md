# A1/A2 banks — read-only diagnostic, 2026-09-12T080020Z

Evidence capture: **08:02:26 UTC, node2**. Latest status check: **08:04:18 UTC**. Main retains all job/source/notebook ownership; no notebook edit, Git mutation, launch, stop or remote write.

## Result

**12 completed scientific fit/eval entries;12 source-compatible;12 evaluable G9 results;12 G9 failures,0 passes,0 unavailable.** These are artifact counts, not a pooled campaign success rate. Eight bank1/2 entries are newly captured/analyzed; four bank0 entries are reused after fresh remote hash verification, and their new analysis rows exactly reproduce the prior bank0 rows. Every new bank1/2 row has positive interval lower bound but violates the unchanged spill limit.

Four queued fits stages now completed with RC0: A1 seeds2/3 and A2 attempt2 seeds0/1 each have banks0,1,2 fit-and-eval complete. Compared with07:45:44, completed fit/eval entries rose from8 to12; the newly completed **evaluations** are those four bank2 entries. A1 seed2 bank2 was already fit-DONE at07:45:44 but not eval-complete. The eight newly captured bank1/2 entries must not be confused with four newly completed entries.

**Outstanding:** A2 attempt2 seed2, queue0052, remains running on node2 GPU1, queue PID3560937, trainer PID3564433 (PPID3560942), bank0; started07:41:12 UTC. No fit DONE, eval JSON or stage marker at08:04:18. A completed throughput profile is not a scientific fit. No jobs were resubmitted.

## Per-fit/bank intervals

A1 = `F_r16k16`, source bank seed1, optimizer seeds2/3. A2 = `CF_r16_b`, source bank seed0, optimizer seeds0/1. Each row uses **1313 eval cues**, **16 dose16 owner pairs** for I_d_frame, and16/16 valid OFF/ON dose16 cues for each of frame, similar-frame and bicycle-frame. Table rounds to9 decimal places; the adjacent JSON capsule and `analysis.json` retain the exact emitted floats.

| Family | Optimizer seed | Bank | Mean I_d_frame | Within-bank 95% percentile interval | Frame spill | G9 |
| --- | --- | --- | --- | --- | --- | --- |
| A1 | 2 | 0 | 1.921469873 | [1.202607550, 2.682502692] | 0.415536920 | FAIL |
| A1 | 2 | 1 | 1.857024456 | [0.220229275, 3.928630131] | 0.445713347 | FAIL |
| A1 | 2 | 2 | 2.023272724 | [1.134010901, 2.927595575] | 0.322034947 | FAIL |
| A1 | 3 | 0 | 0.003650408 | [-0.184279827, 0.190963655] | 0.308698414 | FAIL |
| A1 | 3 | 1 | 3.012993448 | [1.598066118, 4.701089598] | 0.508573081 | FAIL |
| A1 | 3 | 2 | 1.843428490 | [0.699712106, 3.129717893] | 0.378498700 | FAIL |
| A2 | 0 | 0 | 2.446475982 | [1.448077464, 3.472731514] | 0.292353817 | FAIL |
| A2 | 0 | 1 | 0.903910286 | [0.308375056, 1.468666516] | 0.237280140 | FAIL |
| A2 | 0 | 2 | 3.486882030 | [2.142291406, 4.785243779] | 0.395241226 | FAIL |
| A2 | 1 | 0 | 1.743429893 | [1.253261351, 2.287386840] | 0.287367568 | FAIL |
| A2 | 1 | 1 | 1.634408396 | [0.812892424, 2.438732002] | 0.270007978 | FAIL |
| A2 | 1 | 2 | 0.713589364 | [0.356197059, 1.129587323] | 0.248837100 | FAIL |

## Criterion and units

G9 passes iff the lower bound of the within-fit/bank 95% paired-owner bootstrap interval for I_d_frame is strictly >0 AND frame_spill <=0.03. Bootstrap seed0, 2000 resamples, 16 dose16 owners; no cross-bank/seed pooling.

For each dose16 owner, I_d_frame is its frame ON-minus-OFF log-odds change minus the corresponding similar-frame ON-minus-OFF change, using the same target/alternative pair as `cue_metrics`. The alternative is the stored `b` or strongest alternative under OFF. Spill is the unweighted mean of three subgroup means of absolute candidate-normalized probability change:48 exposed similar-frame owners,16 unexposed frame owners,48 exposed bicycle-frame owners. Each bank roster has64 owners,16 each at doses0,1,4,16. These controls are not16 extra independent optimizer runs; bootstrap uncertainty does not include optimizer-seed uncertainty.

`frame_similar` is an unseen look-alike control, **not** an exposed-partner swapped-ID test. Conditional probabilities in the detailed dose16 summaries use p_raw[a]/mass; G9 uses the existing `cue_metrics` candidate normalization and log odds. No missing mass/control was zero-imputed. No thresholds were fitted and no bank/seed mean or causal family comparison was computed.

## Source compatibility and limits

The unchanged analyzer binds each eval to its exact fit-DONE/train metadata, optimizer seed, prepared receipt/destination adapter, source bank roster, manifest, distractor, corpus identities/order, model/HFScorer, lambda1, rank8,3 epochs, lr0.0001 and recipe label. All12 entries have compatible sources, no mismatch and no unavailable controls. Same-bank A1 seeds2/3 share their own exact input/corpus hashes; same-bank A2 seeds0/1 share theirs. There are **six separate source groups**, not one shared A1/A2 source. A1 and A2 bank/source hashes and source seeds differ, so their difference is not a material-controlled causal effect.

Frozen experiment commit: `f2e5b65e9c5dc3f7b7cdf15cb1b97b114ad4994d`. Captured memory_dose and both runbooks match that commit; the analyzer's definitions file also matches the frozen memory_dose bytes. Definitions SHA-256 `ab98329c433cb085cd53e1c766db350f1bb0fe2efb9181e24a3678c0d31a76e3`; analyzer SHA-256 `e1327b3d2fdc060e33aad3d088beada167226437a9b1e6f28b819c6b5959eea9`. Full input hashes and per-group corpus hashes are in the adjacent JSON capsule.

All results remain `SYNTHETIC_DIAGNOSTIC_NOT_CLEAN_LINEAGE`. Fit/eval-stage completion is not a successful binding gate, clean ancestry, H1/H2, parenting effect, report-stage completion, or the entire campaign's completion. No external model-metadata authentication was attempted. The prior A2 profile-cap failures remain preserved; successful attempt2 stage completion does not erase them. Missing A1 reference seeds0/1 and outstanding A2 seed2 are not imputed or silently treated as successful replicates.

## Custody and replay

New evidence: `/tmp/astra_A1A2_banks_20260912T0800Z/`; scope report: `/tmp/astra_A1A2_banks_20260912T0800Z.md`. Exact per-fit data, stdout/stderr, argv, source and input hashes: `analysis.json`, `ANALYSIS_RECEIPT.json`, `CAPTURE_MANIFEST.json`, `SOURCE_REUSE_RECEIPT.json`, `FINAL_PROGRESS.json`. Analyze only with the frozen copy of the existing `research_notes/analysis/astra_seed_campaign.py`; no alternate metric implementation was introduced. Exit0, empty stderr. Output SHA-256 `e73e387e5b1e69b7c0bca2451b413c7b30e218cc7efdaef7ab3067684cdad648`.

New bank1/2 evidence and required source inputs are self-contained in the new directory. Replaying the complete12-entry argv also requires the original `/tmp/astra_seed_bank0_evidence_20260912/`: the four bank0 output triples were verified, **not recopied**. Remote originals were never changed. New repo files are this unique memo and its adjacent JSON capsule only; main owns subsequent SEQ entries and scientific decisions.
