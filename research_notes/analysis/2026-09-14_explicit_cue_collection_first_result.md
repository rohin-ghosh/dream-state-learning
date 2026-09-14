# Explicit-first-READ cue continuation: terminal comparison

2026-09-14. Node2 **R** = `/tmp/astra_cue_explicit_20260914_attempt1/run`.
Terminal at first inspection; recorded start **09:09:16.611 UTC**, finish
**09:10:15.358 UTC**, elapsed **58.747 seconds**. Source commit
`d9c6e3290e6d6d23de4fb4bf25b6e49f9e39b8c7`.

**Read uptake rises 2/8 → 8/8 and frozen read-containing selection rises
2/8 → 5/8, but actual GOAL arrivals remain 5/8.** All eight now first read the
first listed EVENT. Four first reads mismatch GOAL: only one triggers the needed
second read; three are followed by commitment of that wrong-GOAL EVENT's DID.
The continuation produces 11 selected rows, with no new experiences or fitting.

## Same source memories, new prompted attempts

R/RESULT records `COLLECTION_COMPLETE_NO_FIT`, eight experiences reused,
**zero new EXPLORE/EVENT calls**, 17 new cue actor calls, zero fits, and frozen
base unchanged. Model arguments have no adapter. These are retained receipts;
this audit loaded no weights or tokenizer.

The prior root is `/tmp/astra_cue_collect_20260914_attempt1/run` (**P**).
All **14 original input-file SHA-256 bindings** in REUSED_EXPERIENCES and RESULT
match the preserved prior files: original REQUEST/RESULT, two BANK files, two
aggregate EXPERIENCE files, and eight individual EXPERIENCE files. All copied
bank/experience files in R also match those originals byte-for-byte. Every raw
EVENT string, including its final-LF count, matches both prior memory and current
memory. No canonicalized replacement or recollection is being treated as reuse.

Both attempts use master `ASTRA-CUE-TRAIN-EXTERNAL-EVENT-20260914-A1`, identical
eight NODE/GOAL tasks and port/event displays, and the same retained EVENTs.
The new public teacher strategy explicitly requires first-listed-address READ,
comparison of AT/NODE and GOT/GOAL, matching DID commitment, and otherwise an
unread-address READ. It is not an autonomous policy learned in this run.

## Aggregate comparison, unchanged selection

| Metric | Previous | Explicit-first-READ |
|---|---:|---:|
| Cue attempts | 8 | 8 |
| Attempts with at least one READ | 2 | 8 |
| Zero / one / two READ paths | 6 / 1 / 1 | 0 / 7 / 1 |
| External READ calls | 3 | 9 |
| Native cue actor calls | 11 | 17 |
| GOAL arrivals | 5 | 5 |
| Selected: at least one READ and GOAL arrival | 2 | 5 |
| GOAL arrivals with no READ | 3 | 0 |
| Wrong outcomes | 3 | 3 |
| Selected student rows | 5 | 11 |
| Complete two-GOAL pairs by arrival | 1/4 | 1/4 |
| Complete two-GOAL pairs by selected success | 0/4 | 1/4 |
| Committed port supported by a retrieved AT/GOT/DID match (diagnostic) | 2/8 | 5/8 |

All five currently selected episodes have retrieved support, and all three
current failures lack it. **This evidence check is diagnostic only:** the original
read-containing selector was replayed unchanged. No score, threshold, row
selection rule or reported success was replaced with the new diagnostic.

## Every paired outcome and current raw path

Bank/task and global CALL indices are zero-based. R/CALL_010.json is global
call 10. Exact action strings are shown; all have zero trailing LFs.
Abbreviations: **S** = read-backed selected arrival; **N** = no-read arrival
(unselected); **W** = wrong outcome.

| Bank/task | GOAL | Prior → current | Current global calls and exact outputs |
|---|---|---|---|
| 0/0 | `N_PUYT3FQUOG` | N → S | 000 `READ EVENT E_5HCRPPRJEI`; 001 `ROUTE P_FHXBVFTMPD` |
| 0/1 | `N_ZGTZAZYGEF` | W → W | 002 `READ EVENT E_5HCRPPRJEI`; 003 `ROUTE P_FHXBVFTMPD` |
| 0/2 | `N_N6OJRZCS4T` | W → W | 004 `READ EVENT E_A7KWXNA43K`; 005 `ROUTE P_4DBLV3ZSIE` |
| 0/3 | `N_VYJPKMNGYD` | N → S | 006 `READ EVENT E_A7KWXNA43K`; 007 `ROUTE P_4DBLV3ZSIE` |
| 1/0 | `N_3R5IRXYMLF` | S → S | 008 `READ EVENT E_PX3IY2EX4N`; 009 `ROUTE P_ABJJK3XBG5` |
| 1/1 | `N_X3YCTVLT4S` | W → S | 010 `READ EVENT E_PX3IY2EX4N`; 011 `READ EVENT E_U2VS57WTI2`; 012 `ROUTE P_LPWBOOMGJG` |
| 1/2 | `N_VP3UNUMEHZ` | S → S | 013 `READ EVENT E_FLBZDYCQ2T`; 014 `ROUTE P_TD6CKMGK6H` |
| 1/3 | `N_WV36FIJDDW` | N → W | 015 `READ EVENT E_FLBZDYCQ2T`; 016 `ROUTE P_TD6CKMGK6H` |

Prior global calls for the same tasks, respectively: **008; 009; 010; 011;
020–021; 022; 023–025; 026** in P. Two former no-read arrivals become selected
without changing their arrival outcome, and the prior two selected episodes stay
selected. Bank1/task1 gains arrival; bank1/task3 loses its prior no-read arrival.
Hence the higher selected count is not a higher total GOAL-arrival count.

The successful two-read episode moves from bank1/task2 to bank1/task1:
task2 now reads its matching first-listed address immediately, whereas task1
reads the other-GOAL EVENT and then the correct second address. One two-read
success in each run does not establish broad conditional-continuation coverage.

## Retrieved-evidence diagnostic and exact failure mechanism

For each committed ROUTE, inspect **only EVENTs actually returned before that
commitment**, and ask whether one EVENT jointly has AT = task NODE, GOT = task
GOAL, and DID = committed port. Never substitute unread bank facts for retrieved
evidence. Parsing uses the same existing final-LF normalization for diagnostics;
retained memory/prompt strings remain unchanged.

| Task | Evidence before commitment | AT/NODE | GOT/GOAL | DID/commit | Joint support |
|---|---|---|---|---|---|
| 0/0 | `E_5HCRPPRJEI` | yes | yes | yes | yes |
| 0/1 | `E_5HCRPPRJEI` | yes | **no** | yes | **no** |
| 0/2 | `E_A7KWXNA43K` | yes | **no** | yes | **no** |
| 0/3 | `E_A7KWXNA43K` | yes | yes | yes | yes |
| 1/0 | `E_PX3IY2EX4N` | yes | yes | yes | yes |
| 1/1 | `E_PX3IY2EX4N`, then `E_U2VS57WTI2` | both yes | first no; second yes | first no; second yes | yes, second EVENT |
| 1/2 | `E_FLBZDYCQ2T` | yes | yes | yes | yes |
| 1/3 | `E_FLBZDYCQ2T` | yes | **no** | yes | **no** |

The three failures are not invalid addresses, read errors, invented ports,
truncation or incorrect transition execution. They commit a retrieved EVENT's
DID despite its GOT naming the other goal:

- **0/1**, call 003: EVENT GOT and actual arrival `N_PUYT3FQUOG`, but requested
  GOAL `N_ZGTZAZYGEF`; commits `P_FHXBVFTMPD` instead of reading unread
  `E_DM7QH4AQSU`.
- **0/2**, call 005: EVENT GOT and actual arrival `N_VYJPKMNGYD`, but requested
  GOAL `N_N6OJRZCS4T`; commits `P_4DBLV3ZSIE` instead of reading unread
  `E_CNHE5GRD6W`.
- **1/3**, call 016: EVENT GOT and actual arrival `N_VP3UNUMEHZ`, but requested
  GOAL `N_WV36FIJDDW`; commits `P_TD6CKMGK6H` instead of reading unread
  `E_XP42SCQHJM`.

All three stop after two actor calls/one READ, with another actor call and a
distinct unread address still available. Among the **four wrong-GOAL first
reads**, **one** obtains the second record and succeeds; **three** prematurely
ROUTE. The commanded initial consultation is observed in all tasks, but the
conditional GOT/GOAL check-and-continue behavior remains unreliable. No new
training or experiment is proposed or launched here.

## Goal-pair and corpus coverage

| Bank/world | Prior arrived / selected goals | Current arrived / selected goals |
|---|---|---|
| 0 / `W_HPGUIXPVHM` | 1 / 0 | 1 / 1 |
| 0 / `W_FP2QBYLUNL` | 1 / 0 | 1 / 1 |
| 1 / `W_636PAJZJES` | 1 / 1 | 2 / 2 |
| 1 / `W_5FF2GAWMCZ` | 2 / 1 | 1 / 1 |

Each denominator is two goals. Current selected coverage reaches **4/4 worlds,
2/2 banks, 5/8 goals**, including one complete selected pair. The sole complete
arrival pair changes worlds rather than adding a second complete pair.

Selected rows: bank0 global calls **0,1,6,7** (four rows); bank1 global calls
**8,9,10,11,12,13,14** (seven rows), totaling **six READ EVENT and five ROUTE**
targets. Source-call and episode indices remain bank-local inside draft rows;
preserve bank provenance rather than treating them as global unique identifiers.
No failed or no-read rows were inserted, and no source EVENTs were recast as
newly acquired experiences. These are source-valid, guided, external-memory
student drafts, not a fitting or native-mask admission decision.

## Exact replay and teacher/memory joins

Preserved source was `/tmp/astra_cue_explicit_source_20260914_attempt1`.
The pure cue collector's file hash is unchanged from the prior attempt; the
runner selects the explicit guidance at runtime. Audit extracts that literal
from the preserved runner, verifies its hash, and uses it with the preserved
pure collector. It does not import or run native model code.

CPU replay checks every actual public→guided prompt transformation against the
outer CALL's prompt before returning its captured response. It reconstructs all
eight episodes using **the same raw address-keyed EVENT strings**, and requires
exact canonical equality with both complete CUE_COLLECTION reports and the
combined BANK_RESULTS, including failures, traces and all selected rows.
Every draft assistant target equals the actual global CALL output. Its prefix
equals the replayed public history, excludes both old and explicit teacher
strategies, and retains the genuine raw reader replies. Declared loss policy
remains prefix masked, assistant/EOT trained; no tokenizer/mask execution here.

**`CPU_EXPLICIT_CUE_CAPTURE_REPLAY_PASSED`, exit 0**, consuming all **17/17**
captured calls. No torch, transformers, tokenizers or peft imports. Original
cue reports are used only for this retrospective paired analysis; the acquisition
reuse path binds all eight original experience records without selecting from
prior cue rows or scores.

All 17 generations terminal, untruncated, ending with recorded EOT 151645;
native callback/infrastructure errors zero. Recorded prompt lengths **284–434**,
output lengths **10–13** tokens including EOT, below 2048/160 limits. Cue-only
token totals: previous **2996 prompt / 121 output**, current **5604 / 192**.
These are retained metadata checks, not retokenization. Original EVENT final-LF
issues persist unchanged (two zero-LF, six double-LF outputs); their grounded raw
text is served externally, not recalled parametrically.

The observed comparison is a stronger-teacher continuation on the same eight
tasks and memories, not independent replication, autonomous cue mastery,
parametric-reader evidence, birth qualification, or a result from fitting.

## Bounded preservation and hashes

Local **L** = `gpu_artifacts_local/astra_cue_explicit_20260914_attempt1`.
**49 transferred files, 580738 bytes**, all SHA-256/size verified. Complete
terminal run/launch artifacts and seven source files are retained; no weights or
cache. TRANSFER_MANIFEST contains every original remote path/hash.
ANALYSIS contains paired outcomes, all retrieved-evidence checks, unchanged raw
memory hashes, complete-pair counts, and all eleven full student rows.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B gpu_artifacts_local/astra_cue_explicit_20260914_attempt1/REPLAY.py
```

Replay also reads the existing prior preservation directory
`gpu_artifacts_local/astra_cue_collect_20260914_attempt1`; it never alters it.
Reruns verify the existing ANALYSIS instead of overwriting it.

| Artifact | SHA-256 |
|---|---|
| R/RESULT.json | `8d79dbe0d70ffda6a93264b4a063583bb3354bd9aca3da6a4bcd37e2c6820f6c` |
| R/REQUEST.json | `d79ffd02b26868aabd68ea1b63084aba69bc2615e3fa0f201230ba8ca6694afc` |
| R/REUSED_EXPERIENCES.json | `061a17c7f1814a62f38c82e51f9745eefa2bbdcb6ce272ca6071de325138582b` |
| R/BANK_RESULTS.json | `2fb0115ecc03a2fb01ea09a51a177a2e0ec84a6486de8fe72bae23047fcb3a55` |
| R/BANK_00/CUE_COLLECTION.json | `e54c4349ba305091da5fff43e6b512a5cd1f39fb39f79ce6487dd7ea1eed2871` |
| R/BANK_01/CUE_COLLECTION.json | `af76d4ce87048a899528534e68cfb53a458152c04fea3364f4489aa31fee20df` |
| Bank0 canonical selected rows | `92d6b9a9e7aa2aa52bdb7879f147f7fdae05b7a98cdcaece0e719c35d3e23f9e` |
| Bank1 canonical selected rows | `d81f397a511dfb50595a8627e9d90a215677734bfec2a7de8c58d8c750fc4787` |
| R/CALL_003.json | `d1afdf6498de99d2d0cf5935508d308354e5bc99e90bddcc9c85fbbefee89612` |
| R/CALL_005.json | `207d211e396f2505d0593f9b302d9c93f83f25163adaf086cab5644b18efcadd` |
| R/CALL_012.json | `39aa614a3661f40da0d09a4a0ba4430a4a809288b11b78711f21b8b6c5873c74` |
| R/CALL_016.json | `4e0b5c8adf66c38a7d1e72e4519d38c679d8b391eeeb70e9b3db1c6e5790aac2` |
| L/TRANSFER_MANIFEST.json | `48829cb6d48f1526d037e2a2600dcdf300d977c2ee8364e7554bf1ec83611951` |
| L/ANALYSIS.json | `564cf9d5e0199b4e3c7852681bb6d3cda2494a2b7ba8cd09cbef9d48063c3e67` |
| L/REPLAY.py | `52446df94665388f12d58e423df184d10d8d8662e169973a22e1329da780fd14` |

Explicit guidance SHA:
`fc16a673dd0eacad94582818096424bc9e8cae40515824ab9969a19b7e899eac`;
runner SHA:
`2abec56cf32a96dadce761749b2443da5dad349e10b1afee536b88ec44ea64d7`;
unchanged pure cue collector SHA:
`82369dc5ee234a89cad22e2814fe33bc8fdbb47d4135fca037b12f67f62e3f37`.

Only this new note and L were written. No model/tokenizer/fit/launch, native code
or notebook edits, threshold changes, commits, or prior-artifact overwrites.
