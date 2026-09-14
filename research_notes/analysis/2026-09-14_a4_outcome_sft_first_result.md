# Original A4-only outcome SFT: first terminal result

Scope: read-only analysis of `/tmp/astra_outcome_a4_20260914_attempt1/run` on the A100 node. Only this note and `gpu_artifacts_local/astra_a4_outcome_sft_first_result_20260914/` are owned. No replay-arm or cue analysis, remote writes, model/tokenizer/GPU execution, fitting, launches, notebook/source edits, or commits. This is a bounded development readout, not a new scientific qualification.

## Terminal time and bottom line

The original RESULT is `DEV_OUTCOME_SFT_COMPLETE`, `reportable=true`, with 256/256 updates. Main's supplied `1789376572.3915` converts exactly as a decimal timestamp to **2026-09-14 09:02:52.391500 UTC**, or **02:02:52.391500 PDT**. The actual captured JSON literal is slightly more precise: `1789376572.3915088`, corresponding to **09:02:52.3915088 UTC** (displayed to microseconds as **09:02:52.391509 UTC**). Thus 09:02:52 UTC was correct; the supplied fraction was rounded/truncated relative to the receipt.

**Seven of ten individual criteria pass; the aggregate `criteria_passed` boolean is false.** CHECK and PROSPECT improve versus A3. Strict whole-chain success stays 4/8, but the identities change: **A4 succeeds on zero-based chains 3, 5, 6, 7, not A3's 2, 3, 6, 7.** A4 gains normal chain 5 and loses strict recovery chain 2. Five chains reach GOAL and STOP; chain 2 still fails the required single correct intervening check. CONTINUE and instruction canaries remain serious failures. This is not a qualified controller.

## Recorded criteria and cell counts

SEEK/PROSPECT/CHECK/CONTINUE count four two-member pairs, requiring both members correct. Individual member accuracy was independently extracted from the public JSON prompts, not by running a model, tokenizer, held generator, or project scorer.

| Criterion | A4 BASE | A3 FITTED | A4 FITTED | Minimum | A4 criterion |
|---|---:|---:|---:|---:|---|
| SEEK | 0/4 | 4/4 | 4/4 | 3 | pass |
| PROSPECT | 0/4 | 2/4 | 3/4 | 3 | pass |
| CHECK | 1/4 | 0/4 | 4/4 | 3 | pass |
| CONTINUE | 0/4 | 0/4 | 0/4 | 3 | fail |
| typed_interventions | 17/32 | 32/32 | 32/32 | 30 | pass |
| whole_chains | 0/8 | 4/8 | 4/8 | 6 | fail |
| useful_reads | 0/8 | 8/8 | 8/8 | 7 | pass |
| typed_steps | 1/8 | 8/8 | 8/8 | 7 | pass |
| canaries | 16/16 | 4/16 | 4/16 | 15 | fail |
| chain_gain over BASE | — | 4/8 | 4/8 | 2 | pass |

A4 FITTED member correctness: SEEK **8/8**, PROSPECT **7/8**, CHECK **8/8**, CONTINUE **4/8**; total **27/32**, not 32/32 semantic correctness. `typed_interventions=32/32` only certifies typing. Likewise the recorded `typed_steps` counter is the number of chains with strict action typing across attempts, not eight successfully executed routes; typed-but-invalid STEPs occur below.

The lone PROSPECT error is probe 13 (third evaluated pair, member 1): expected `STEP M2AP_6A4426XGQELM`, emitted `STEP M2AP_XJ3T5UWK7LAP`. Both candidate EVENTs have AT `M2AN_NLDT27EDFOUC`, but the emitted port belongs to FOR `M2AN_3Y2NXYOAGB4G`, not GOAL `M2AN_W7CNP4KX25AQ`. This is wrong-goal selection, not formatting failure. Exact rows and all 32 outputs are in `MEMBER_ANALYSIS.json`.

Accounting: BASE **56** physical calls (56 EXECUTED, 224 UNUSED); FITTED **122** (122 EXECUTED, 158 UNUSED), each out of 280 reservations. Both have zero recorded failures and empty issues. A3 FITTED used 139 calls; fewer calls alone do not establish greater controller reliability.

## Actual raw chains: normal and recovery are not interchangeable

Indices below are zero-based positions in the captured eight-chain screen, with corresponding static screen task indices 0, 4, 8, 12, 16, 20, 24, 28. They are not inferred training-episode names. Skin 0 is the AT-before-FOR rendering; skin 1 is FOR-before-AT. `I`, `R`, `S`, `K`, `V`, `X` abbreviate READ INDEX, READ RELATION, STEP, THINK KEEP, THINK REVISE, STOP. Full opaque identifiers, selected and relevant EVENT rows, CURRENT transitions, acceptance and raw action strings are retained in `ANALYSIS.json` and the original terminal event.

| Chain / task | Skin | First executed outcome | Raw command sequence | Terminal | Strict success |
|---|---:|---|---|---|---|
| 0 / 0 | 0 | matched GOT | I R S K I R S K I V I R S | invalid_step | no |
| 1 / 4 | 0 | first STEP rejected | I R S | invalid_step | no |
| 2 / 8 | 0 | mismatched GOT | I R S K I V R S X | goal_arrival_stop | **no** |
| 3 / 12 | 0 | mismatched GOT | I R S V R S X | goal_arrival_stop | yes |
| 4 / 16 | 1 | matched GOT | I R S K I R S K I V R V R V R V R V R S | invalid_step | no |
| 5 / 20 | 1 | matched GOT | I R S K I R S X | goal_arrival_stop | **yes, new versus A3** |
| 6 / 24 | 1 | mismatched GOT | I R S V R S X | goal_arrival_stop | yes |
| 7 / 28 | 1 | mismatched GOT | I R S V R S X | goal_arrival_stop | yes |

Success attribution uses the recorded 4/8 strict total plus raw necessary-condition checks: 0, 1, 4 have rejected STEPs/no GOAL-stop, and 2 has two intervening THINKs. These four cannot pass the strict scorer; the remaining four therefore account for its total. Static scoring requires exactly one correct intervening THINK, witness route/read evidence, typing/execution/budgets, and immediate STOP after the second STEP at GOAL (`organism_v6/composition_birth_stage2a_scoring.py`, `score_chain`). Mechanical arrival alone is not the criterion. No full scorer rerun or new qualification was performed.

### Chain 2: physical recovery after the wrong check, not strict success

The relevant first EVENT `M2AE_DPROYJ3ITPB7` predicts GOT `M2AN_2HKC2DDRSMQU`; STEP actually yields `M2AN_ODW355OSZC5G`. Despite this mismatch, the raw next action is `THINK KEEP M2AE_DPROYJ3ITPB7`. Then `READ INDEX M2AN_ODW355OSZC5G` returns MISS; only then does it emit `THINK REVISE M2AE_DPROYJ3ITPB7`, read recovery query `M2AQ_XDZNX52TYHKK`, STEP `M2AP_5CV67NCS33Q4` to GOAL `M2AN_4HBJ5LOJ6IRP`, and STOP. It recovers physically but checks the same first STEP twice, initially incorrectly. This is the strict recovery lost versus A3, even though CHECK's isolated pairs improve to 4/4.

### Chains 0 and 4: first KEEP repaired, second-hop GOAL selection not repaired

Both now correctly KEEP after matched first outcomes, unlike the A3 unnecessary-revision pattern. However, both choose a second-hop ROUTE for a different FOR goal, walk to that decoy node, and later fail. Thus these failures should not be reported as simply the old missing-KEEP problem.

- **Chain 0:** GOAL remains `M2AN_ZC6CMJNFKG2Y`. At CURRENT `M2AN_3L54GUNJBJZJ`, it selects query `M2AQ_SAACG735UVSJ` for FOR `M2AN_VK6E2DRMWFFD`, rather than the actual-goal route query `M2AQ_WC7DLDLPMFGX`. STEP `M2AP_FR2ARX6IINUT` reaches the decoy. After KEEP, an INDEX MISS, REVISE, and rereading the old node/query, it repeats that STEP from the wrong CURRENT and is rejected.
- **Chain 4:** GOAL remains `M2AN_SASIRT2FKJJ6`. At CURRENT `M2AN_X5Z4OX37JM5Z`, it chooses query `M2AQ_OKILVRAZE7J5` for FOR `M2AN_3E4LGYESRUYN`, not actual-goal query `M2AQ_RUI7KOM437A7`. STEP `M2AP_HAAUEPUYGKBU` reaches the decoy; subsequent INDEX/recovery misses lead eventually to the actual-goal EVENT, but STEP `M2AP_4WRPNO4GGZYX` is now issued from the wrong CURRENT and rejected.
- **Chain 1:** the initial relation contains the relevant EVENT `M2AE_JSAZRJ36EEBB`, requiring `STEP M2AP_WEZKRZ4Z7HHL`. Instead it selects `STEP M2AP_U6JU3ZZXVRCG` from EVENT `M2AE_JHPXZ456REHI`, whose FOR matches but AT is `M2AN_5JVVGNWQS5ZW`, not CURRENT `M2AN_CMQLTX6MSVJX`. This is the same raw wrong-AT error observed in A3.

One clean normal success is real: chain 5 uses KEEP, rereads INDEX/RELATION at the new CURRENT, takes the goal-directed second STEP and immediately STOPs. Clean recovery persists on 3, 6, 7. The evidence does not support assuming four identical routes survived unchanged, or extrapolating isolated CHECK success to reliable online branch choice.

## CONTINUE: short local context versus learned trajectory context

All eight CONTINUE requests contain **exactly two messages**: ordinary system instructions and a short TASK with START/GOAL/CURRENT. There is no preceding STEP, WORLD outcome, EVENT block, or trajectory history. Each pair holds START=CURRENT fixed and changes whether GOAL equals CURRENT.

| Probes | CURRENT operand | At-GOAL output (expected STOP) | Off-GOAL output (expected INDEX) |
|---|---|---|---|
| 24 / 25 | `M2AN_YTLWE3UG3NBF` | READ INDEX same CURRENT: wrong | READ INDEX same CURRENT: correct |
| 26 / 27 | `M2AN_NEGLIMYWOACV` | READ INDEX same CURRENT: wrong | READ INDEX same CURRENT: correct |
| 28 / 29 | `M2AN_AEB7G7RM67ZD` | READ INDEX same CURRENT: wrong | READ INDEX same CURRENT: correct |
| 30 / 31 | `M2AN_RSBHQE6CRH4G` | READ INDEX same CURRENT: wrong | READ INDEX same CURRENT: correct |

Therefore **4/8 members but 0/4 pairs**: all four at-GOAL members fail, all four off-GOAL members pass. The ordinary system explicitly says STOP is correct only when latest CURRENT equals GOAL. Nevertheless, the model emits an initial INDEX in both local contexts. In contrast, all five actual GOAL-arriving chains immediately STOP after their second STEP. This supports **context-dependent failure to select STOP**, not global erasure of STOP or inability to emit the token.

Training's four STOP targets occur at the ends of long successful trajectories: two prefixes have 16 messages, two have 14. No short at-GOAL TASK-only STOP example or CANARY-copy example appears among the 30 rows. The observed short-context INDEX default is consistent with the training distribution, but this is a supported explanation, not a causal identification. CONTINUE was already 0/4 in BASE and A3; the task is not newly shown to fail solely because of A4 fitting. Goal retention on second-hop chain ROUTEs is a separate context-binding weakness, demonstrated by 0 and 4.

## Instruction canaries: 4/16, all twelve failures inspected

All sixteen FITTED canary generations are valid captures. Only the two READ INDEX and two READ RELATION copy targets pass. Four STEP targets become READ RELATION using the same port; four THINK targets become READ INDEX using the event identifier; all four STOP targets become `READ INDEX CANARY`. These are exact command/type substitutions, not whitespace or truncation errors. BASE copied all sixteen exactly.

| Canary indices | Expected | A4 raw substitution | Count |
|---|---|---|---:|
| 0–3 | two INDEX, two RELATION | exact original target | 4 correct |
| 4–7 | `STEP <port>` | `READ RELATION <same port>` | 4 wrong |
| 8–9 | `THINK KEEP <event>` | `READ INDEX <same event>` | 2 wrong |
| 10–11 | `THINK REVISE <event>` | `READ INDEX <same event>` | 2 wrong |
| 12–15 | `STOP` | `READ INDEX CANARY` | 4 wrong |

Every target and raw output is enumerated in `ANALYSIS.json`. Unlike A3, whose two REVISE canaries became READ RELATION, A4's two become READ INDEX; identical 4/16 totals do not imply identical bytes. Legal THINK/STEP/STOP use inside chains coexists with failure to follow the explicit copy instruction. No qualified instruction-following controller is established.

## Training coverage, dose, masks and guide absence

Source collection receipt: **4 successful episodes / 32**, master `ASTRA-OUTCOME-COLLECT-TRAIN-20260914-A4`, yielding **30 success-only rows**. Episode labels retain inherited `OUTCOME-TRAIN-A1-...` text; that text is not evidence that the actual collection used A1 worlds. The captured source master and input hashes bind A4 provenance.

| Retained episode suffix | Rows | Verified first branch | EVENT skin | Actions |
|---|---:|---|---:|---|
| h01-m1 | 8 | GOT matched, KEEP | 0 | I R S K I R S X |
| h02-m1 | 8 | GOT matched, KEEP | 0 | I R S K I R S X |
| h13-m0 | 7 | GOT mismatched, REVISE | 1 | I R S V R S X |
| h13-m1 | 7 | GOT mismatched, REVISE | 1 | I R S V R S X |

Action counts: INDEX6, RELATION8, STEP8, KEEP2, REVISE2, STOP4. Branch support is present, but **normal is perfectly associated with skin0 and recovery with skin1 in these selected training trajectories**. This is branch-covered, skin-confounded success selection, not a balanced factorial study. A4's successful held normal chain 5 uses skin1 and recovery chain 3 uses skin0, so a deterministic skin-only account is also too strong.

- **Dose:** 256 updates × batch4 = **1,024 recorded row presentations**. The first four rows occur35 times, the other26 occur34 times. Recorded supervised tokens total **13,284**, independently matching the sum of per-row mask-token counts times actual loss-log indices; one pass through the rows totals389 supervised tokens. Prefix-token range292–3751; supervised-target range2–17. Recorded first/last loss0.3090854585 / 0.0001016114 does not qualify generalization.
- **Masks:** all30 row policies record prefix=`MASK_ALL`, assistant=`TRAIN`, EOT=`TRAIN`, target EOT=`<|im_end|>`. MASK_RECEIPT supplies prefix/supervised counts and input/label hashes. These recorded policies/counts were checked; **no tokenizer or tensor-level label regeneration** was performed, so this is not an independent tokenization audit.
- **Guide absence:** all30 student system prefixes exactly match the ordinary evaluation system text; no teacher/exogenous-strategy marker appears anywhere in the captured student prefixes. The teacher guidance is absent from student inputs, not absent from data generation. COLLECTION_RECHECK includes a teacher-only strategy explicitly teaching matched KEEP, mismatch REVISE/recovery and immediate STOP. Source claim remains `SCAFFOLDED_DATA_GENERATION_NOT_AUTONOMOUS_PARENTING_SUCCESS`.
- **Optimizer/checkpoint receipt:** batch4, seed0, 256 updates, optimizer lr3e-5 and weight_decay0.01; checkpoint kind `PEFT_ADAPTER_ONLY_NOT_FULL_RESUME_STATE`. Final adapter bytes were not copied or loaded for this analysis; their recorded hashes are retained in RESULT/TRAINING.

### What the A3 comparison does and does not show

A3 and A4 RESULT fields match exactly on evaluation held digest, master_hex, seed, batch size, planned update count, and frozen-base-hash receipts. The shared evaluation digest is `ba2890bcc25e18f3409d7cbb8e11a78e2cad1c44f313ca30d5bdcf1e9d645ba5`. On that development screen, **CHECK0→4/4 and PROSPECT2→3/4 are real descriptive improvements; criterion count5→7/10 is not erased by the remaining failures.** Whole4/8, useful8/8, typed8/8, canaries4/16 and CONTINUE0/4 remain unchanged in aggregate.

But training changes together: A3 master versus A4 master; six recovery-only successful trajectories versus two normal/two recovery trajectories; 42 versus30 rows; different teacher-guide hashes; all selected A3 trajectories use skin0, versus A4's branch/skin correlation. Both have1,024 presentations, but A3 row exposure is24/25 versus A4's34/35, and supervised-token exposure is13,556 versus13,284. Same update count does not mean same per-example or token dose. This bounded capture does not establish identical initial adapter bytes. These world/guide/skin/selection/dose differences preclude attributing the improvement uniquely to adding KEEP or branch coverage. No autonomous birth, qualified controller, or broad causal claim follows.

Teacher guidance digests: A3 `2de9f301098a5892f2f6d63c0f6183ce1e4d9e3c33f1f4a046d91b7634fd307d`; A4 `046d265fdbdab1d35805b4cee9b44170998ce66a19dab1a0a9cced7aaffbd722`.

## Evidence receipt and limits

Local root: `gpu_artifacts_local/astra_a4_outcome_sft_first_result_20260914/`.

- `evidence/astra_outcome_a4_20260914_attempt1/run/`: all retained original-run JSON/JSONL and COMPLETE receipts; **374 payload files, 16,684,869 bytes**, all remote/local/recheck SHA matches verified, then reverified locally after analysis.
- `evidence.tar.gz`: **1,862,302 bytes**; remote and local SHA256 `110e5a4bb050998666f1d03967c67b789f313d8a1ca502ab9b9eca7aa1aace1b`.
- `evidence/REMOTE_MANIFEST.json`: remote/local SHA256 `7e4ed1c1c66dd6c76fa8d4656e3a0e35a49923a27cd24b4357d53059de6d10a1`.
- Local enriched `MANIFEST.json`: SHA256 `4a262dc8d09d82a534c2f12c7f6c37db96318aaf06e7546a26e17607921ce351`; records per-file source path, size and three-way hashes. `REMOTE_TRANSFER.json`, `REMOTE_AFTER.json`, and `PAYLOAD_SHA256SUMS` retain transfer/recheck details.
- `EXCLUSIONS.json`:188 explicitly listed omitted entries. This is an analysis capture, **not a checkpoint backup**: weights/tensors, redundant initial/backend and other non-JSON material were excluded. Unique final checkpoint hashes are recorded, but its weight bytes are not included. No pickle deserialization or other remote root copy.
- `ANALYSIS.json`: SHA256 `7c0efcbd17567cdbdbba6b149c46da1937894c0dfa78ee9e8268cf89146445af`; raw per-chain actions/state transitions, all canaries/CONTINUE contexts, training episodes/dose and limited A3 comparison.
- `MEMBER_ANALYSIS.json`: SHA256 `1d1875187a7a73efe492a97aed7c0459a4014be0c924b5c841618c55ff5317ca`; all32 public-prompt-derived expected actions and actual outputs. Decoder/analysis scripts are local JSON-only utilities in the owned capture directory; no project code imports or execution.

Original-run data SHA256 (remote/local matched):

| Path under captured run | SHA256 |
|---|---|
| RESULT.json | `2c60e299832912db317e6f824a4aba9fdd33f8fc1f390c096ffb5c1336f14736` |
| FITTED/event-0245.json | `7c827551cfa22668858541029c6379c34aecc974f0a021aeb17f8112db7b8c18` |
| BASE/event-0113.json | `ba3ba87b0204b88570972c41f349e80f0cf1f67dc1ad4152848a24525b021167` |
| STUDENT_ROWS.jsonl | `6f73927c0e617143f295aca994a9cdf4c8dea217866b643b66ecd03c6a8ac3db` |
| MASK_RECEIPT.json | `3de1e7dc2d83a5e42c8786419d93a03d29ef0a6be3f1b0569110d0852de0244b` |
| LOSSES.jsonl | `094e85ac41c85ea656aaff154ec720f9b1ec4f764643fde58bf0d5b03231895d` |
| COLLECTION_RECHECK.json | `44f5b4ad66538b51a05288d04faed692412ada6684f87b220b1e71a97448024d` |
| adapter/TRAINING.json | `793513ec1ddfeea54139dfe9ace3aa0a8080a5b99bf22e1d11c3222bf5e8bc98` |

The receipt's canonical `rows_sha256=59517b5f9c6922f97409084db45afda9e50ba0bac473285331327475ac58b3c5` is a different representation from the literal STUDENT_ROWS.jsonl file hash above; do not interchange them. The limited comparison reads existing local A3 preservation, whose RESULT SHA256 is `82503714b127618266855603448cb618e97fe1a593120e1283117323034f63f1`; it makes no fresh remote A3 copy.

Initial terminal check09:00:13 UTC found no RESULT/FAILED. After one bounded three-minute backoff, check09:03:14 UTC found RESULT. Capture completed09:04:34 UTC. `LOCAL_SHA256SUMS` seals the local derived artifacts and this note separately from the unchanged remote evidence archive. Replay progress supplied conversationally was not inspected or analyzed.
