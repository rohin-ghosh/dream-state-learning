# SEQ-073 bounded claim review — 2026-09-12

**Conclusion:** the memo's behavioral table, per-board OFF agreement, fit
accounting, solution-overlap disclosure, completion receipts and descriptive
cost arithmetic are supported by the captured outputs. No behavioral result
correction or new pass decision follows from this review. There are two narrow
operational wording qualifications below, not new gates.

Reviewed memo:
`research_notes/astra_memos/ASTRA_BEHAVIOR_REPLICATION_TERMINAL_2026-09-12.md`
(SHA256 `f831c20a274da7224d816518c39ba2febb3d10d84d12a7528c89f2dff7cb4942`).

Read-only inputs: the existing seed-0 capsule/final audit; both roots below
`/tmp/astra_replication_terminal_20260912/`; their reductions/audits;
`three_seed_descriptive.json`; raw episode ledgers, results, train manifests,
material source entries, logs and cleanup/process/worker receipts; and the
corresponding committed receipts. No GPU, remote access, source edits,
retokenization, fresh model scoring, full-auditor replay or puzzle-completion
enumeration was performed. The only new file is this review.

## 1. Table and raw ACT check

Read all 192 raw episode ledgers, keyed by episode ID rather than file order.
Each contains exactly one ACT; its raw score equals the frozen reduction's
first-ACT zero-filled score and the native result's best score. All 192 reduced
first-ACT statuses are measured. There is no later-action rescue in these data.

| Optimizer seed | Useful OFF | Useful ON | Corrupt OFF | Corrupt ON | Direct ON / difference-of-gains |
|---|---:|---:|---:|---:|---:|
| 0 | 0/16 | 2/16 | 0/16 | 0/16 | 2/16 |
| 1 | 0/16 | 3/16 | 0/16 | 1/16 | 2/16 |
| 2 | 0/16 | 5/16 | 0/16 | 0/16 | 5/16 |

The two contrast definitions coincide here because the OFF conditions match.
Across optimizer seeds, solved-count contrast mean = 3, median = 2,
range = [2, 5], all with denominator 16. These reproduce the memo exactly;
they are descriptive, not confidence/significance or qualification claims.

| Seed | Useful ON first-ACT mean | Corrupt ON first-ACT mean | Every OFF mean |
|---|---:|---:|---:|
| 0 | 0.585546875 | 0.28828125 | 0.1125 |
| 1 | 0.626953125 | 0.269921875 | 0.1125 |
| 2 | 0.674609375 | 0.2671875 | 0.1125 |

The serialized seed-2 useful mean is `0.6746093750000001`; the memo's decimal
rendering is ordinary presentation rounding, not a scoring tolerance.

### OFF agreement is per board, not just aggregate

All six OFF conditions (two material arms × three seeds) have **identical
16-entry raw score vectors and identical ACT action strings**. The common
nonzero scores are:

| Canary ID suffix | Score |
|---|---:|
| 1900051 | 0.1125 |
| 1900055 | 0.3375 |
| 1900060 | 0.675 |
| 1900061 | 0.675 |

The other twelve IDs in 1900050–1900065 score zero. Sum = 1.8; mean = 0.1125;
none solves. This is score/action agreement, not a claim that complete ledger
bytes, clocks or process metadata are identical.

## 2. All six actual fits: rank, targets, seed, length and token passes

Cross-checked each actual train manifest with its train metadata, adapter config,
material corpus spans and saved material token-validation records. Both arms at
each seed agree on the following accounting:

- Rank 8 in config, LoRA manifest and adapter config; effective alpha 16.
- Target modules: `q_proj`, `k_proj`, `v_proj`, `o_proj`, `gate_proj`, `up_proj`,
  `down_proj`; config/LoRA/adapter module sets match. All 28 layers are recorded.
- Actual config/meta seed is respectively 0, 1, 2 for the two arms in that root.
- 32 items, 32 encoded sequences; three completed epochs, 96 optimizer steps;
  `max_len=4096`, maximum recorded segment length 806.
- Per pass: 24,492 context tokens + 1,216 target tokens = 25,708 total.
  Every example has 38 target tokens, including EOS. `train_tokens_seen=77,124`
  equals three complete 25,708-token passes, and train metadata agrees.
  Thus the implied supervised target exposure is 3,648 tokens per fit, not
  77,124 target tokens.
- Targets are entirely `external_oracle_action`. Each corpus item has the exact
  two spans `[rendered_q, false, native_context]` and
  `[a, true, external_oracle_action]`. No first-person NOTE target substitutes
  for the ACT grid.
- `pack=false`, `chat_template=false`, one item per sequence. Truncated items,
  split items, dropped context and dropped target token counts are all zero;
  no nonfinite batches are recorded.

This checks saved native mask/span and token accounting, not newly executing
the tokenizer or independently observing GPU loss masks. That is the precise
scope in which the memo's “native masks/tokens” statement is supported.

## 3. Solution overlap and solved IDs

Compared **saved solution arrays directly** between the 32 training records and
16 canary records, without enumerating puzzle completions again. The same four
matches occur in all three source datasets:

| Canary solution | Matching training solution |
|---|---|
| 1900054 | 1850030 |
| 1900055 | 1850026 |
| 1900059 | 1850012 |
| 1900065 | 1850015 |

These agree with saved overlap declarations. Useful solved IDs are precisely:

- Seed 0: 1900060, 1900062.
- Seed 1: **1900055**, 1900056, 1900064.
- Seed 2: **1900055**, 1900057, 1900060, 1900062, 1900064.
- Corrupt seed 1 alone solves 1900057; corrupt seeds 0 and 2 solve none.

Therefore 1900055 is indeed an overlapping-solution useful solve in **both new
seeds**. All other solved IDs lie outside those four solution overlaps. This
supports the memo's disclosure; no panel exclusion, denominator change or
“wholly unseen solutions” reinterpretation is warranted.

## 4. Controllers, worker PIDs, cleanup and cost

Launch receipt PID/device and paired terminal result agree:

| Seed | Controller / device | Start UTC | Paired completion UTC | Elapsed minutes |
|---|---|---|---|---:|
| 1 | 64646 / GPU1 | 10:50:46.784304 | 11:09:16.614369 | 18.49716775 |
| 2 | 64744 / GPU3 | 10:50:57.738575 | 11:09:56.788989 | 18.98417357 |

Both paired results say `BOTH_ARMS_COMPLETED`; all four arm results say
`COMPLETED`, with the correct training seed. The useful arm completed at
11:00:28.093246 (seed 1) and 11:00:07.991987 (seed 2), before the respective
corrupt terminal results. Sum of the two controller durations is
**37.4813413167 minutes**, supporting 37.48 aggregate reserved-device A40 minutes,
not measured kernel-only utilization.

| Seed / arm | Train PID | Pair PID | OFF worker PID | ON worker PID |
|---|---:|---:|---:|---:|
| 1 useful | 64647 | 65570 | 65629 | 67702 |
| 1 corrupt | 70635 | 71563 | 71568 | 74214 |
| 2 useful | 64749 | 65604 | 65631 | 67701 |
| 2 corrupt | 70513 | 71565 | 71569 | 74123 |

All eight train/pair cleanup receipts and all eight worker cleanup receipts
have `cleanup_error=null`, `owned_group_empty=true`, `gpu_processes_absent=true`,
and `reservation_release_verified=true`. PID matches the corresponding process
receipt; worker PID also matches WORKER_DONE and PAIR_DONE. Devices are GPU1 for
seed 1 and GPU3 for seed 2. A worker cleanup receipt is scoped to its owned work,
not permission to release a still-running paired controller's reservation.

All eight engine PIDs and shutdown signal timestamps quoted in the memo match
their corresponding probe logs:

| Seed / condition | Engine PID | Logged SIGTERM initiation UTC |
|---|---:|---|
| 1 useful OFF | 66148 | 10:56:33 |
| 1 useful ON | 68355 | 10:59:36 |
| 1 corrupt OFF | 72282 | 11:05:56 |
| 1 corrupt ON | 74699 | 11:08:57 |
| 2 useful OFF | 66141 | 10:56:33 |
| 2 useful ON | 68284 | 10:59:34 |
| 2 corrupt OFF | 72289 | 11:05:55 |
| 2 corrupt ON | 74496 | 11:09:12 |

**Narrow wording qualifications, not blockers:**

1. These times are the logged `send sigterm to process EngineCore` events, not
   precise exit instants. For example, seed-1 useful ON starts shutdown at
   10:59:36 and reports MPClient completion at 10:59:37; seed-2 useful ON uses
   10:59:34 and 10:59:35. Each log also records
   `[close_backend] escalated: killed 1 engine procs, freed=True`, an unexpected
   engine-exit warning and a leaked-semaphore shutdown warning. The memo already
   discloses backend termination/warnings; “backend shutdown initiated at” would
   be the most literal description of the quoted times, not “graceful exit at.”
2. The captured roots establish terminal results and owned cleanup, but I did
   not find a timestamped raw process listing supporting **both controllers
   absent at 11:10:40 UTC** in the inspected capsule/receipts. The memo and
   coordination log report the absence/release as Main's operational observation;
   the run log records release verified. Likewise the local capsule alone cannot
   prove a universal absence of manual/unrelated kills. Attribute those statements
   to Main's observation rather than treating this review as independent proof.
   No new remote check or scheduling gate is requested.

## 5. Material identity, source scope and preserved evidence

Direct hashes of the captured useful/corrupt corpora, oracle source JSON, IDs
and local model-pin JSON match across all three seeds. The saved cross-seed
budget/panel/paired-setting checks are all true. Each existing audit reports
64 first-prompt comparisons, zero mismatches, and 48 uniquely solvable reference
puzzles; the latter was **not re-enumerated in this review**.

The four-record remote rehash receipt binds each arm/seed's adapter path,
probe-spec hash and complete expected adapter inventory to reported remote
rehashes. Weight payloads are absent locally, as the audits state. This check
does not rehash remote weights again or authenticate loaded runtime/model origin.

Minimal source precision: **material byte equality is not full source-code byte
equality**. Seed 0 records source directory `3d56c5cd…`; seeds 1/2 record
`bc4250ed…`. Among common material-source entries keyed by filename, the recorded
changed file is `mini_sudoku_behavior_material.py` (the seed-parameter extension).
The material outputs themselves match. This is consistent with the declared
replication change; no concrete contradictory source evidence or new source
guard is identified.

Memo artifact hashes verified:

- Committed terminal capsule:
  `e45c272e3781583f3ac1bae80d600ac35449b68e183b3b499d6b34d182ddd39b`.
- Three-seed descriptive JSON:
  `71ca480472207c03eb83e45a5f22b407c87778dc52249e1d0a305aae8cbade91`.
- Remote rehash receipt:
  `1b590e956b1fc2d2cb0d5d132842821303dab51986487db6464790597d0606c0`.

The committed three-seed JSON, both per-seed reductions/audits and remote rehash
receipt are byte-identical to their local capture counterparts. The seed-0 final
audit remains an existing input, not rewritten here.

The memo's “Next decision” exporter/tokenizer assertions and concurrent memory
fit status concern separate work, not evidence established by these captured
behavioral replications, and were not reviewed here. Its bounded external-oracle,
shared-panel, hardware/order and non-parenting limitations remain appropriate.
