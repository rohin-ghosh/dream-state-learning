# SEQ256 independent terminal comparison — 2026-09-14

**Disposition: bounded evidence checks pass; primary PROBE tie, TRAIN endpoint separation, unequal retention. Neither arm meets the engineering target. Ownership released after this review.** This memo is independent of Main's primary account and does not change the summary implementation.

## Evidence and matching

Root: `gpu_artifacts_local/astra_goal_pair_train_terminal_20260914_attempt1/extracted`; artifact paths below are relative to it.

- Sibling archive SHA256 matches **`2f3d604cb44972c93e1cbe7bf34cd73aab9cd82f6d5589bba0e495fead4c1db2`**. All **6,472 regular files** match extracted bytes and exact inventory; no duplicate file members, unsafe paths or nonregular payloads. Thirteen bounded core/helper/test/protocol files match local Git source **`f325f9d3a91ea4f584b97ae17767bbfe1d575678`**. Frozen helper hashes and protocol hash also match the receipts.
- Both recorded fits start at **`37ec37884e4b0b679edd1dba1be1dec3474589e992649f3a33e7e3b1ec78b8c0`**, use fresh AdamW, learning rate 3e-5, seed 0, rank 8, batch 4, and complete **400 logged updates**. FULL ends at **`fa3dec6dc3b10e11d888e7d5981b53a6eed677a603a480d0f7d234b37f36ea45`**; LOSS_OFF at **`2a8076fb6445cb905c3a6bcfec116acd542f82ddc20aaad9ac607180f785bf80`**. Each AFTER receipt joins its own training-result hash and unchanged before/after state. Adapter-file hashes were checked as opaque bytes, **not decoded tensors**.
- Both arms contain identical **270 input sequences/reference masks**: 128 memory, 20 cue, 62 audit, 12 original trajectory and 48 new TRAIN trajectory rows. Original 222 masks join their recorded predecessor file hash; old memory/cue/audit group hashes join the inherited binding. New 48 rows equal SEQ255's recorded rows, and their reference target IDs exactly equal the original coached native generation token IDs, including EOT, without tokenizer decoding.
- Independent reduction of all 400 batches confirms the declared schedule, common inputs, reference denominator, unchanged original 222 labels and complete masking only of new rows 222–269 in LOSS_OFF. Group presentations are **400/100/252/48/800**. FULL has **33,019 active/reference labels**; LOSS_OFF **23,885 active / 33,019 reference**, a difference of **9,134 label presentations**. The logged control loss equals mean CE × active/reference within floating-point rounding. All loss values are finite. This is matched inputs/reference normalization, **not equal active-token dose**; original trajectory supervision remains enabled in both arms.

## Independently reproduced endpoints

FULL means `FULL_TARGET`; LOSS_OFF means `NEW_TRAJECTORY_LOSS_OFF`.

| Endpoint | FULL | LOSS_OFF |
|---|---:|---:|
| TRAIN OWN_TEXT individuals / pairs | **8/8; 4/4** | **3/8; 0/4** |
| PROBE OWN_TEXT individuals / pairs | **5/8; 2/4** | **5/8; 2/4** |
| PROBE UNAVAILABLE individuals / pairs | 0/8; 0/4 | 0/8; 0/4 |
| Old recall W0 / W8 | 16/16; 16/16 | 13/16; 14/16 |
| Held audit | 15/16 | 16/16 |
| Original taught graph | 2/4 | 2/4 |
| Previous fresh graph | 3/4 | 2/4 |

PROBE-A is 2/4 individuals, successful pair **(0,2)**; PROBE-B is 3/4, successful pair **(1,3)**, in BOTH arms and saved SEQ255 baseline. Pair membership requires identical public displays except GOAL, both endpoints, distinct source-correct first ports and two legal commits each. The zero-native-call first-current-port reference is 2/4 individuals but 0/2 pairs per world.

### Failure identities, not just marginal counts

Task indexes are zero-based. Both arms retain precisely the baseline's unsuccessful PROBE OWN_TEXT cases **A1, A3, B2**, but not identical trajectories:

| Case | FULL | LOSS_OFF |
|---|---|---|
| A1 | wrong first port → dead_end | wrong first port → dead_end |
| A3 | wrong first port → invalid_route | wrong first port → duplicate_address |
| B2 | wrong first port → dead_end | no first commit → invalid_route |

- LOSS_OFF TRAIN failures: A2/A3 and B2 choose wrong first ports and dead-end; B0/B1 issue invalid routes without any first commit. FULL has none. TRAIN successes therefore differ beyond aggregate individual scoring.
- UNAVAILABLE retains eight failures per arm: FULL has seven duplicate-address stops and a B3 wrong-goal dead end; LOSS_OFF has eight duplicate-address stops.
- Original taught failures are tasks 1/3 in both arms: FULL both dead-end; LOSS_OFF task 1 invalid-route/no commit and task 3 dead-end. Previous-fresh failures are FULL task 3 and LOSS_OFF tasks 1/3, all invalid-route/no commit.
- LOSS_OFF old-recall failures: W0 indices **6 `E_3FIXU7HBPN`** (DID/GOT/EVIDENCE differ), **10 `E_QQ43NOEYBQ`** and **11 `E_DEX6OHDHJP`** (EVIDENCE differs); W8 indices **6** (DID/EVIDENCE differ) and **10** (EVIDENCE differs). These are identifier errors, not merely newline mismatches. FULL has none.
- FULL's sole audit failure is **case 10, true `E_VEEAOY3IIH`**: expected `NONE`, emitted `E_VEEAOY3IIH\n`, a false positive. FULL is 7/8 true and 8/8 fault cases; LOSS_OFF is 8/8 each.

FULL fails **PROBE-pairs ≥3/4** and **taught ≥3/4**. LOSS_OFF additionally fails both old-wrapper ≥15/16 checks and previous-fresh ≥3/4. Both retain at least one successful pair in each PROBE world. The controlled comparison supports better execution on trained instances under FULL, not a demonstrated PROBE improvement; retention is mixed, not matched. This is an incremental supervision comparison between already-taught descendants, not parented versus never-parented lives.

## Replay, visibility and limits

- Frozen `read_training` reproduces both recipes, masks, doses, logs and state joins. Frozen `evaluate` consumes **239 FULL / 232 LOSS_OFF actual native calls**, reproducing **74 evaluation artifacts per arm** and the complete summaries, with all writes intercepted as comparisons against existing files. Native roles are **191/184 actor + 32 old-recall + 16 audit**. Exact AFTER inventories contain 316/309 output JSON files. Lower call totals reflect early failures, not case dropping.
- Separate standard-library JSON reductions replay all **64 AFTER episodes**, raw-source transitions, literal feedback, public histories, counters, strict pairs and failure classifications. FULL has 128 memory returns; LOSS_OFF 126. All scheduled cases remain represented. Independent recall/audit reductions reproduce the exact identities above.
- No PROBE identifier occurs anywhere in the 270-row training material. Parent hints are absent from old/new trajectory student prefixes; retained coached provenance is not an encoded student prompt. Readout prompts join the actual native captures, with no parent guidance. Goal actors receive public tasks, literal captured EVENT text or UNAVAILABLE, and feedback only after commits. Old-recall expected strings are withheld from prompts. Held audit intentionally supplies its receipt-grounded source table as the comparator task requires; that is not hidden goal-actor guidance. Baseline scores are retained as binding/report metadata, not used by the frozen recipe to select rows, dose or stopping.
- Commands/checks: `sha256sum .../terminal.tar.gz`; read-only `python3 -B` archive/hash and direct-JSON reductions; `git show f325f9d3a91ea4f584b97ae17767bbfe1d575678:PATH`; frozen helper imports with an ML/HTTP import deny-list; frozen `GoalFitTests.test_exact_schedule_common_inputs_and_denominator` passed by direct invocation without fixture setup. No model, tokenizer, torch, GPU, remote/network call, fit or launch occurred. No review harness or other file was written.
- SEQ255 was used only for its bound receipts/DATA, exact 48 rows and baseline case comparison; its full prior audit was not repeated. A bounded earlier fresh collection and embedded taught provenance anchor retention text; old facts/held cases also join recorded hashes. No full ancestor histories were reconstructed. These are **recorded state/hash and token-array joins, not live tensor, optimizer-execution or tokenizer authentication**. Frozen replay and direct reductions establish capsule consistency, not independent replication, general planning, whole-life efficacy or H1/H2. Only this assigned memo was changed; ownership is released.
