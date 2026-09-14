# First external-EVENT cue collection: independent terminal analysis

2026-09-14. Node2 source **R**:
`/tmp/astra_cue_collect_20260914_attempt1/run`.
Terminal on the first inspection; no running data was copied. Recorded interval
**08:54:02.904–08:55:17.080 UTC**, **74.176 seconds**;
`COLLECTION_COMPLETE_NO_FIT`, eight admitted EVENTs, 27 native calls, no fit.
Launch source commit: `39ae8ea872b784c4e520c4b49e2b2e5592cdf613`.

## Immediate answer: six failures are all no-READ commitments

**All six unselected episodes directly emit ROUTE without reading memory.**
Three reach GOAL but are correctly excluded by the read-required selector;
three choose the wrong outcome. There are **no failed READs, bad post-READ
routes, malformed commands, duplicate reads, or call-budget failures** in these
eight attempts. Two attempts read and both succeed. This is an observed
consultation-skipping failure, not evidence that returned EVENTs cannot be used.
It does not establish that reading caused success or that stronger guidance
will fix the other attempts.

| Metric | Observed |
|---|---:|
| Scheduled source EXPLORE/EVENT pairs | 8 |
| Grounded source EVENTs admitted under existing LF-tolerant check | 8/8 |
| Cue tasks, across two banks/four worlds | 8 |
| Actual GOAL arrivals | 5/8 |
| Read-backed selected successes | 2/8 |
| GOAL arrivals without READ, excluded | 3/8 |
| Wrong outcomes, all without READ | 3/8 |
| External memory lookups | 3 |
| Native calls | 8 EXPLORE + 8 EVENT + 11 cue = 27 |
| Selected student targets | 3 READ EVENT + 2 ROUTE = 5 |
| Infrastructure / nonterminal / truncation failures | 0 / 0 / 0 |

## All eight actual cue outcomes

Bank/member indices and call indices are zero-based. `CALL_008.json` means
R/CALL_008.json, not a bank-local call. Goal names below are the actual requested
GOALs; raw output targets are retained without whitespace repair.

| Bank / task | World | GOAL | Global calls and exact actions | Actual outcome / selection |
|---|---|---|---|---|
| 0 / 0 | `W_HPGUIXPVHM` | `N_PUYT3FQUOG` | 008: `ROUTE P_FHXBVFTMPD` | GOAL; excluded, no READ |
| 0 / 1 | `W_HPGUIXPVHM` | `N_ZGTZAZYGEF` | 009: `ROUTE P_FHXBVFTMPD` | `N_PUYT3FQUOG`; wrong outcome |
| 0 / 2 | `W_FP2QBYLUNL` | `N_N6OJRZCS4T` | 010: `ROUTE P_4DBLV3ZSIE` | `N_VYJPKMNGYD`; wrong outcome |
| 0 / 3 | `W_FP2QBYLUNL` | `N_VYJPKMNGYD` | 011: `ROUTE P_4DBLV3ZSIE` | GOAL; excluded, no READ |
| 1 / 0 | `W_636PAJZJES` | `N_3R5IRXYMLF` | 020: `READ EVENT E_PX3IY2EX4N`; 021: `ROUTE P_ABJJK3XBG5` | GOAL; selected |
| 1 / 1 | `W_636PAJZJES` | `N_X3YCTVLT4S` | 022: `ROUTE P_ABJJK3XBG5` | `N_3R5IRXYMLF`; wrong outcome |
| 1 / 2 | `W_5FF2GAWMCZ` | `N_VP3UNUMEHZ` | 023: `READ EVENT E_XP42SCQHJM`; 024: `READ EVENT E_FLBZDYCQ2T`; 025: `ROUTE P_TD6CKMGK6H` | GOAL; selected |
| 1 / 3 | `W_5FF2GAWMCZ` | `N_WV36FIJDDW` | 026: `ROUTE P_2PJLJ3HJKR` | GOAL; excluded, no READ |

The successful one-read branch retrieves
`EVENT E_PX3IY2EX4N AT N_BAGMHXCPBG DID P_ABJJK3XBG5 GOT N_3R5IRXYMLF EVIDENCE R_AEPDROPER4`
plus **two final LFs**, then commits its DID port. AT and GOT match public NODE
and GOAL respectively.

The successful two-read branch first retrieves
`EVENT E_XP42SCQHJM AT N_X74CMBPINV DID P_2PJLJ3HJKR GOT N_WV36FIJDDW EVIDENCE R_ES2JUXNXL3`
plus two final LFs: correct AT, **wrong GOT for GOAL N_VP3UNUMEHZ**. It then reads
`EVENT E_FLBZDYCQ2T AT N_X74CMBPINV DID P_TD6CKMGK6H GOT N_VP3UNUMEHZ EVIDENCE R_EBN7EJNRAD`
plus two final LFs and commits the matching port. This is an observed
nonmatching-result → second READ → matching ROUTE continuation, within the
three-actor/two-memory-call limit; not a parametric two-hop or KEEP/REVISE result.

Seven of eight tasks choose the first listed port; the two-read success chooses
the second. All six no-READ tasks choose the first port. This documents a strong
display-position pattern in these captures, not a causal explanation or an
unguided generalization estimate.

## Branch, goal-pair and world coverage

Each bank has two worlds, each world has two tasks sharing NODE and identical
port/event lists but differing GOAL. Both offered ports are sourced by actual
EXPLORE/EVENT pairs. Attempted target-port positions are 0,1,1,0 per bank.

| Bank / world | Actual arrived goals out of 2 | Read-backed selected goals out of 2 |
|---|---:|---:|
| 0 / `W_HPGUIXPVHM` | 1 | 0 |
| 0 / `W_FP2QBYLUNL` | 1 | 0 |
| 1 / `W_636PAJZJES` | 1 | 1 |
| 1 / `W_5FF2GAWMCZ` | 2 | 1 |

Thus **1/4 complete goal pairs arrive**, but **0/4 goal pairs have both tasks
selected**. Selected data covers **2/4 worlds, 1/2 banks, 2/8 goals**, one one-read
path and one two-read path. Both selected tasks are member 0 in their respective
world pair; both target-port display positions are nevertheless represented.
Only three of the eight retained EVENT addresses are actually consulted.
Do not describe five rows as balanced world/goal-pair coverage.

## Source acquisition and serialization

All eight actual EXPLORE commands match their externally offered singleton
source/port. Replayed observation messages reveal the DEV transition receipt
only after that command. Each captured EVENT matches all five fields of its
observed fact under the collector's **existing final-LF-count normalization**.
No source admission failure or callback error occurred.

| Bank / fact | EXPLORE call | EVENT call / address | Raw EVENT final LFs |
|---|---:|---|---:|
| 0 / 0 | 000 | 001 / `E_5HCRPPRJEI` | 0 |
| 0 / 1 | 002 | 003 / `E_DM7QH4AQSU` | 0 |
| 0 / 2 | 004 | 005 / `E_CNHE5GRD6W` | 2 |
| 0 / 3 | 006 | 007 / `E_A7KWXNA43K` | 2 |
| 1 / 0 | 012 | 013 / `E_PX3IY2EX4N` | 2 |
| 1 / 1 | 014 | 015 / `E_U2VS57WTI2` | 2 |
| 1 / 2 | 016 | 017 / `E_FLBZDYCQ2T` | 2 |
| 1 / 3 | 018 | 019 / `E_XP42SCQHJM` | 2 |

**0/8 EVENTs obey the prompt's exactly-one-final-newline instruction.** Calling
the original exact EVENT validator on each raw output raises `not exact EVENT`.
This is not a new admission failure: the launched cue collector explicitly uses
`canonical_event` for grounding. It retains and serves the **unchanged raw text**,
including the zero/double LF endings. No EVENT rewrite was done during this audit.
All EXPLOREs and all READ/ROUTEs have no trailing LF; EXPLORE requests that form,
and the cue command grammar explicitly permits zero or more final LFs.

Recorded token metadata: all **27/27** generations end with EOT token **151645**,
all terminal flags true and truncation flags false. Output lengths **10–55** tokens
including EOT, below the 160-token cap; prompt lengths **159–393**, below 2048.
Totals: **6812 prompt tokens**, **693 generated tokens including EOT**. These are
checks of retained token IDs/counts, not fresh tokenizer decoding or tokenization.

## Replay, teacher stripping and readiness

The bounded capture includes every terminal CALL, source EXPERIENCE, bank,
cue report, REQUEST/RESULT, launch receipt, guard and run log, plus seven relevant
source files. Replay uses the **preserved pure modules**, not mutable current
native code, and substitutes only captured responses into callbacks:

1. Verify all transferred file hashes and recorded runner/module hashes.
2. Rebuild the two fixed banks; verify cross-bank/original-evaluation identity
   separation using the existing source definitions, without new source search.
3. Check all actual EXPLORE prompts, observation receipt prompts, outputs and
   admission fields against the outer CALL files and per-experience records.
4. Run existing `cue.run_collection` with retained raw EVENT memories and captured
   native responses, asserting every guided prompt before each response.
5. Require exact canonical equality with **both complete CUE_COLLECTION reports
   and BANK_RESULTS**, including all successes, failures, traces and student rows.

**`CPU_CAPTURE_REPLAY_PASSED`, exit 0.** All 27 native captures consumed exactly
once in replay. No torch/transformers/tokenizers/peft imported. Repeat execution
verifies existing ANALYSIS without overwriting it.

Five student rows all come from BANK_01, episodes 0 and 2:
global calls **20,21,23,24,25**, corresponding to bank-local source call indices
**0,1,3,4,5**. Each assistant target is byte-identical to that captured response;
all retain EOT `<|im_end|>` and declared prefix-mask/assistant-plus-EOT loss policy.
Each student prefix equals the replayed public history, while the captured native
prompt has the fixed teacher strategy appended only to its system message.
Teacher guidance is absent from all student prefixes; returned raw EVENT text is
present as external evidence where the public history requires it. Bank-local
call/episode indices should be preserved with their bank provenance if combined.

**Data readiness:** five nonempty, replay-verified, source-backed draft targets
are available for a **scoped external-EVENT cue-SFT data input**. This is a source
readiness statement, not a fit decision or native-tokenizer/mask admission: no
tokenizer was run, and the recorded mask policy was checked structurally only.
Coverage is sparse and excludes every no-READ trajectory, including lucky arrivals.
The source remains a coached data collection, not autonomous cue competence.

Memory is an **external address-keyed dictionary of raw child-authored EVENT
strings**. Each READ callback returns exactly that string with source tag
`EXTERNAL_RETAINED_EVENT_TEXT_NOT_MODEL_GENERATION`; the public reader has no
question-conditioned lookup or parametric generation. The model chooses the
address and port, but exposure tuples are scheduled externally. The receipt
records no adapter, zero fits, and frozen base unchanged; no weights were loaded
to reverify that receipt in this audit. Nothing here demonstrates parametric
memory, learned exploration, qualified birth, or autonomous parenting.

Main's proposed reuse of these same eight raw memories with stronger public
guidance would avoid recollection and address the observed skipped-consultation
behavior. It would be a **new coached cue-attempt dataset**, not additional
independent EVENT acquisition or a causal comparison of memory mechanisms. No
successor, recollection, or fit was run or authorized by this analysis.

## Preservation and exact hashes

Local directory **L**:
`gpu_artifacts_local/astra_cue_collect_20260914_attempt1`.
`TRANSFER_MANIFEST.json` contains every remote path, byte length and SHA-256;
**58 transferred files, 445543 bytes**, all locally hash-checked. No weights or
model cache copied. `ANALYSIS.json` records all raw source outputs, all eight
cue outcomes/read comparisons, pair coverage, and the five full student rows.

Reproduction command (CPU-only, reads preserved source/captures):

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B gpu_artifacts_local/astra_cue_collect_20260914_attempt1/REPLAY.py
```

| Artifact | SHA-256 |
|---|---|
| R/RESULT.json | `014677484bfed4556564e67cce167f9105e52e5d698d8f43de4b18ba2f77e680` |
| R/REQUEST.json | `2281fd6821665be26f255ef4bd751ae81b637bba7575805e41589e0030e8a7bf` |
| R/BANK_RESULTS.json | `ac8d2f988eb322930386447b481e28bc3d171afbf6d808f2f44d6ed05da7374c` |
| R/BANK_00/CUE_COLLECTION.json | `7e5ad5af910bd022eb9f9872d43dcf9ff391bad47eb7f1b1204c0f852543d46b` |
| R/BANK_01/CUE_COLLECTION.json | `57f8d367da2cce1a1de7fd5b0878c59c8732c90fffd24c9c226090b5f8f30eed` |
| BANK_01 canonical five student rows | `59832376b4f9e791e30d5b81fac82cd757f71c090b6d46d58a949ce99ea96835` |
| R/CALL_020.json | `84fa4f360494498c323ea9c0e8576e02d7180f76a4c97e4de66ad09795eb140c` |
| R/CALL_023.json | `9ecde9c63c41caafae2621565c0662119146aaf7c78a299ea151eed8d6a52241` |
| R/CALL_025.json | `0ff65b948248e2a2a9c512d7cf67501d5d78daa1744bf54683b4ad90af4acfa6` |
| L/TRANSFER_MANIFEST.json | `acffb8d728f0f4265251a29c030f349106925606b5232de0264b9c5635c36b81` |
| L/ANALYSIS.json | `16058ed58cc01d0fb304b72c0848424aaf59f158e56c2b8331afc76b9f694ecc` |
| L/REPLAY.py | `2e0eefc154ad702147b69ba5b4ee55d682e442f98e151b328ffb807c2673f7f3` |

Source overlay was `/tmp/astra_cue_collect_source_20260914_attempt1`.
Runner SHA-256:
`b572a6e9095603238be7ab0dc559ffd7d2e9191ffb3303e170652fb5c706b3d5`;
pure cue collector:
`82369dc5ee234a89cad22e2814fe33bc8fdbb47d4135fca037b12f67f62e3f37`;
pure READ/ROUTE controller:
`b6ca95525ddd5af5f8c775bf3287693865d01d7e1ba8d1c5f9b0ffbcee022aaa`.
All remaining individual source/raw hashes are in TRANSFER_MANIFEST.

Only this note and L were written. No model/tokenizer work, native code edits,
notebook edits, fits, process control, launches, or commits. Initial inspection
attempted nonexistent `../run.py`; the actual invocation was then read from
`../guard.sh`. The preservation and CPU replay commands succeeded without errors.
