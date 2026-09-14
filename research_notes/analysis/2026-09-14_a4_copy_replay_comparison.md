# A4 outcome-only versus A4 source-action copy mixture

Read-only comparison of the terminal original A4 and copy-replay runs. Original A4's detailed analysis remains in `research_notes/analysis/2026-09-14_a4_outcome_sft_first_result.md`; this memo records the new comparison, not a duplicate original-arm analysis. New artifacts are confined to `gpu_artifacts_local/astra_a4_copy_replay_comparison_20260914/`. No model/tokenizer/scorer execution, fitting, launches, remote writes, project-code/notebook edits or commits.

## Decision-relevant result

Replay RESULT is reportable, aggregate `criteria_passed=false`, with **6/10 individual criteria passing versus original A4's7/10**. Its recorded terminal timestamp `1789377109.9506392` is **2026-09-14 09:11:49.9506392 UTC**.

**Same chains, not another route tradeoff:** both arms' strict successes are zero-based indices **3,5,6,7**. All eight raw action sequences, all public response bytes, and action acceptance/CURRENT transitions match across arms. Both have five GOAL/STOP arrivals but only four strict successes; chain2 still erroneously KEEP-checks a mismatch, gets INDEX/MISS, then REVISE-checks it again before physically recovering. That second check disqualifies strict success. Original A4's gained normal chain5 and lost strict recovery chain2 remain exactly as before.

**Canaries improve4→9/16**, specifically all four STOP-copy targets and one STEP-copy target. **PROSPECT worsens3→2/4**, from one additional wrong-goal member. **CONTINUE remains0/4:** copying STOP improves without improving local GOAL-conditioned stopping. This is a mixed development-screen result, not controller qualification, isolated replay causality, or evidence establishing a forgetting mechanism.

## All criteria and accounting

| Criterion | Original A4 | Copy mixture | Minimum | Mixture passes |
|---|---:|---:|---:|---|
| SEEK | 4/4 | 4/4 | 3 | yes |
| PROSPECT | 3/4 | 2/4 | 3 | no |
| CHECK | 4/4 | 4/4 | 3 | yes |
| CONTINUE | 0/4 | 0/4 | 3 | no |
| typed_interventions | 32/32 | 32/32 | 30 | yes |
| whole_chains | 4/8 | 4/8 | 6 | no |
| useful_reads | 8/8 | 8/8 | 7 | yes |
| typed_steps | 8/8 | 8/8 | 7 | yes |
| canaries | 4/16 | 9/16 | 15 | no |
| chain_gain over BASE | 4/8 | 4/8 | 2 | yes |

The four skill counters require both members of each pair correct. Mixture member accuracy is SEEK8/8, PROSPECT6/8, CHECK8/8, CONTINUE4/8: **26/32**, versus original27/32. Typed32/32 is not semantic correctness. `typed_steps` is chain-wide strict action typing, not eight valid routes. Both FITTED arms use122 physical calls,122 EXECUTED/158 UNUSED of280 reservations, zero accounting failures and empty issues. Both BASE readouts are unchanged:56 calls, whole0/8, canaries16/16.

The only changed intervention output is **probe9**, first evaluated PROSPECT pair, member1. Original emits the correct `STEP M2AP_XUYDTKJY47MF`; mixture emits `STEP M2AP_VW2ABPSDM76J`. The correct EVENT has AT `M2AN_QSETB3YDUDZS`, FOR `M2AN_X6TDWKNDFW7R`, DID `M2AP_XUYDTKJY47MF`. In this member the other port belongs to the alternative FOR goal. This makes both pair members choose the same port despite the goal-relevance swap. The earlier probe13 wrong-goal error persists. Exact public expected rows and all32 actual outputs are in `COMPARISON.json`.

## Raw chains, CONTINUE and canary classes

The original note's full chain diagnoses remain valid without change: normal chains0/4 KEEP correctly but choose a second-hop ROUTE for the wrong GOAL; chain1 selects a wrong-AT EVENT; chain2 physically recovers after two checks; normal5 and recovery3/6/7 pass. Successful indices are bound using the recorded4/8 strict total and raw necessary-condition exclusions, not a new scorer execution. `COMPARISON.json` records every replay action and confirms original equality, including response bytes and state transitions.

All eight CONTINUE prompts and outputs are identical across arms. Each prompt contains only the ordinary system and TASK START/GOAL/CURRENT. In all four pairs, both at-GOAL and off-GOAL members emit `READ INDEX <CURRENT>`. Thus the four off-GOAL members pass, four at-GOAL STOP members fail, and pair count remains0/4. Both arms nevertheless STOP immediately in all five chains that actually arrive at GOAL. These are different contexts: explicit copy, local equality decision, and end-of-trajectory action selection.

All16 mixture canary generations are valid. The exact class changes are:

| Canary class / indices | Original exact | Mixture exact | Remaining mixture errors |
|---|---:|---:|---|
| READ INDEX,0–1 | 2/2 | 2/2 | none |
| READ RELATION,2–3 | 2/2 | 2/2 | none |
| STEP,4–7 | 0/4 | 1/4 | indices4–6 emit READ RELATION with the same port |
| THINK KEEP,8–9 | 0/2 | 0/2 | READ INDEX with the same event identifier |
| THINK REVISE,10–11 | 0/2 | 0/2 | READ INDEX with the same event identifier |
| STOP,12–15 | 0/4 | 4/4 | none; formerly READ INDEX CANARY |

The one repaired STEP is index7, `STEP M2AP_V6KSPKPZPDBL`. All12 prior errors were inspected, not inferred from aggregate counts. Residual errors are command/type substitutions, not truncation or whitespace. Success at copying literal STOP does not establish the CURRENT=GOAL decision rule. Both arms remain below the15/16 canary criterion, and no forgetting-specific interpretation is isolated by this comparison.

## Matched saved initialization: now checked directly

Fresh read-only remote hashes before/after transfer bind the following initial files for both runs:

- Initial `adapter_model.safetensors`: **identical** SHA256 `2beaa09d4930b1eafa6a1a07a67f3d062b35336d5e5ac58778a00ad518cf9dfe`. Initial weight bytes were hashed remotely, not copied or loaded.
- `initial/INITIALIZATION.json`: **identical bytes**, SHA256 `6803b6422c308e37165640ed550b6a69247d648f246e7058f5361a91d58f87f7`. Recorded observation's `initial_adapter_sha256` is also shared: `d099e2d6de34944c170b0928f8703833fa7c99ccbee4f658a3acfd9112381740`. This observation hash and the safetensors file hash describe different representations; do not substitute one for the other.
- Initial config file hashes differ: original `20a2b21bc3a7a4bf5079890004d1d1b6b643343d83fd5a582f6da335760ba2db`; mixture `2c43407ebf81a3a2277b60e186df83c69a3900a425fac4c058492160839abbc3`. Parsed configs differ **only in list ordering** of the same seven target_modules; all other fields match. This is not a different target-module set.

RESULT fields match for held evaluation digest, master_hex, seed0, batch4, planned256 updates and frozen-base-hash receipts. The shared held digest is `ba2890bcc25e18f3409d7cbb8e11a78e2cad1c44f313ca30d5bdcf1e9d645ba5`; all48 captured probe prefixes also match exactly. These observations support matched **saved initialization and evaluation binding**, not an assertion that every runtime condition or training computation was identical.

## Actual copy-target origins and retained source rows

The mixture has42 rows. Its **first30 complete JSON row records equal original A4's30 records**, and the corresponding30 mask receipts are also identical. Canonical source-row digest remains `59517b5f9c6922f97409084db45afda9e50ba0bac473285331327475ac58b3c5`. The inherited source episode names retain `OUTCOME-TRAIN-A1-...`; actual collection binding remains A4, as previously documented.

The extra12 rows are **authored copy prompts using actual source assistant actions**, not twelve new trajectories. Each has the same ordinary system and user text `Return the following text verbatim, without explanation:\n<actual action>`. This differs from held `CANARY\nCOPY EXACTLY\n<target>`. For every row, source episode/call, full-source-row canonical SHA and assistant SHA were independently matched to the retained original source record.

| Copy row / training row | Family | Source row / call | Source episode suffix | Exact target |
|---|---|---|---|---|
| 0 /30 | INDEX | 0 /15 | h01-m1 | `READ INDEX M2AN_IDZBKDEYPTXR` |
| 1 /31 | INDEX | 4 /19 | h01-m1 | `READ INDEX M2AN_2BVRIFVFLTII` |
| 2 /32 | RELATION | 1 /16 | h01-m1 | `READ RELATION M2AQ_VTF4BXOM2RT6` |
| 3 /33 | RELATION | 5 /20 | h01-m1 | `READ RELATION M2AQ_AV6I5VVOU5HJ` |
| 4 /34 | STEP | 2 /17 | h01-m1 | `STEP M2AP_Q2MMULOO6TOW` |
| 5 /35 | STEP | 6 /21 | h01-m1 | `STEP M2AP_7BK7AMFGIYBT` |
| 6 /36 | KEEP | 3 /18 | h01-m1 | `THINK KEEP M2AE_E2QOXYG4HMP5` |
| 7 /37 | KEEP | 11 /34 | h02-m1 | `THINK KEEP M2AE_NNNUJBVQ2R4T` |
| 8 /38 | REVISE | 19 /85 | h13-m0 | `THINK REVISE M2AE_XPUFCO5OI5P2` |
| 9 /39 | REVISE | 26 /92 | h13-m1 | `THINK REVISE M2AE_F6P5ACALQCG2` |
| 10 /40 | STOP | 7 /22 | h01-m1 | `STOP` |
| 11 /41 | STOP | 15 /38 | h02-m1 | `STOP` |

There are12 distinct source calls but11 distinct target strings: the two STOP rows have identical copy inputs/targets and different source provenance. Two source calls per family are selected; no missing action is synthesized. Static `organism_v6/outcome_action_replay.py` describes selecting the lowest call indices, consistent with the captured mapping; it was read, not executed. Source labels/hashes are provenance evidence, not new autonomous-experience admission or a comprehensive contamination audit.

All42 rows retain prefix=`MASK_ALL`, assistant/EOT=`TRAIN`, EOT=`<|im_end|>`; all system prefixes match and teacher-strategy markers are absent. The additional rows teach copying, not short at-GOAL TASK decisions. Mask counts/hashes and loss-log indices were checked without tokenization or tensor deserialization.

## Dose is a replacement mixture, not an additive replay control

Both arms have256 batch-four updates and1,024 total presentations. Actual mixture loss logs show **three original outcome slots plus one copy slot in every batch**:

| Dose | Original A4 | Copy mixture |
|---|---:|---:|
| Outcome presentations | 1,024 | 768 |
| Copy presentations | 0 | 256 |
| Outcome supervised tokens | 13,284 | 10,054 |
| Copy supervised tokens | 0 | 3,377 |
| Total supervised tokens | 13,284 | **13,431** |

All token totals cross-check against mask counts multiplied by actual row indices. The mixture removes outcome slots instead of preserving outcome dose:13,431 is147 more total supervised tokens, but3,230 fewer outcome tokens. It also changes ordering and per-example exposure, not merely the total split.

The scheduler retains the first three slots of the original stride-four cycle over30 rows and replaces the fourth. Outcome rows are consequently **not uniformly exposed25/26 times**: two occur35 times, thirteen34 times, one18 times and fourteen17 times. Original rows occurred34/35 times. Copy rows0–3 occur22 times, the other eight21 times. For example outcome KEEP presentations fall69→34 while42 authored KEEP copies are added; outcome STOP136→85 plus42 copies; outcome RELATION273→171 plus44 copies. Context and family weighting shift together.

Therefore report a **descriptive mixture effect**: more copy successes, one fewer correct PROSPECT member, unchanged raw chains and CONTINUE. This is not an isolated replay treatment holding outcome exposure/order/token dose fixed. It does not establish that copying caused forgetting, that replay prevented forgetting, or that lower PROSPECT proves a particular mechanism. Source A4 world/guide/branch-skin selection is shared between these two arms rather than newly varied, but its previously documented generalization limitations remain. No experiment or follow-up was launched here.

## Preservation and exact receipt

Root: `gpu_artifacts_local/astra_a4_copy_replay_comparison_20260914/`. Remote scripts only read/hash/archive streams to SSH; they create no remote files. Original A4 analysis evidence is reused locally rather than recopied comprehensively.

**Bounded analysis capture**

- `capture/evidence.tar.gz`:379 payload files,16,855,880 payload bytes; archive1,873,850 bytes. Includes replay JSON/JSONL/COMPLETE evidence and both arms' initial initialization/config metadata. Archive SHA256, remote=local: `35d1e4e6821f7ecfac0cfd3ad1d599bc469ba36f7fa4310ecd6f4a7631d2d2d8`.
- `capture/evidence/REMOTE_MANIFEST.json`: SHA256, remote=local: `5f2402c7c1ee775943317386b1d0a6e9b1153998ee72f181dde2c7f1486cec50`.
- `capture/MANIFEST.json`: enriched local receipt SHA256 `1eb3b8c3efe06ee7e7b06018e11edd9496f474d49cd73470fccad5fa0870265d`. Per-file remote/local/remote-after hashes verified. Its186 explicit exclusions cover backend, tensors and nonselected material; final adapters excluded here are preserved separately below. Initial weight bytes are hash-only, not copied.
- `COMPARISON.json`: raw chain/probe/canary comparisons, all copy-row bindings, init binding, actual dose; SHA256 `636dd5d0ec0de533360188f071d25ca93bbe05420bc3a3aadb8d7492f437c6c2`.

**Separate ignored final-adapter backup**

- `final_adapter_backup/final_adapters.tar`: **8 payload files,161,599,425 bytes**; archive161,628,160 bytes. Both complete final adapter directories are included: safetensors, adapter_config, TRAINING receipt and README. No initial weights, base cache or full optimizer state. Archive SHA256, remote=local: `33a92bd9adb1755d927c0eccfa3f873d4f40e55026395ddc36e9b565b683ba14`.
- `final_adapter_backup/evidence/REMOTE_MANIFEST.json`: SHA256, remote=local: `4e8f44a010dd7f40715f092256e9149017fcc0b9ddd883d3890b1a397223902e`.
- `final_adapter_backup/MANIFEST.json`: local SHA256 `9c2f3d4309f1dd6f2f054f3fdf854859eb0b51a5347f5382707fdafb75e4c6f0`. All8 files match remote/local/remote-after hashes; both actual weight hashes also match their arm's RESULT-declared weight hash. Git ignore status confirmed.

Exact extracted weight paths relative to the new root:

- `final_adapter_backup/evidence/astra_outcome_a4_20260914_attempt1/run/adapter/adapter_model.safetensors` — SHA256 `d7a11323800201cb26489eb3c932506afae240fb9f141a9bae1027085e1d9e06`.
- `final_adapter_backup/evidence/astra_outcome_a4_replay_20260914_attempt1/run/adapter/adapter_model.safetensors` — SHA256 `3f131ae1160d8b1c127093fd3893d59e8b47c78c8a61b93f8a368ebbc16ce1bf`.

Each weight file is80,792,096 bytes. Sibling TRAINING.json hashes: original `793513ec1ddfeea54139dfe9ace3aa0a8080a5b99bf22e1d11c3222bf5e8bc98`; mixture `9bf740fd24ded3f6b9a2cc530b1f55f817265511190ddd82b3a612b7f9300ac0`. These are adapter-only backups, not full-resume checkpoints; file hash verification does not entail loading or a model reload test.

Key replay source hashes, all remote/local matched:

| Replay run file | SHA256 |
|---|---|
| RESULT.json | `e4140a4c54e6a12643e39ff00eeb89a4bc9e5901a94a2201d2a49d66a5c718a8` |
| SOURCE_ACTION_COPY_REPLAY.json | `fdb596373ebccb1a7a0e80aa75c7e7ac0e6becc21f94b382df3c126bbe8f8c9c` |
| STUDENT_ROWS.jsonl | `b096aa9abbb2715aaaf024502c814b930977800b1f5a1f211d2e001903ef53dc` |
| MASK_RECEIPT.json | `ea2fbcb925e2815a4fa8feedec274b0ab6d8cc3032d9447854b56e451266f16b` |
| LOSSES.jsonl | `7ea8ce296e04622a4fffc07d0340b5d7cd0e3e5e67476586cbdc81ae888044e3` |

Mixture canonical training-row digest `c419e0135ed93fa47ea674056dca208677906d0b54576ff7cb416de98dc04e65` matches RESULT; it is not the literal STUDENT_ROWS.jsonl file hash. Each archive additionally contains its remote manifest, beyond the reported payload file count. `LOCAL_SHA256SUMS` seals local analysis/receipts and this memo; data/archives remain independently bound by their manifests. Others' files and prior captures are unchanged.
