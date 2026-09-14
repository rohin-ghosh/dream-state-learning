# Shared-writer selector-material control: independent reduction

September 14, 2026. **Independent terminal reduction COMPLETE: train and AFTER,
with no pending, failed, or invalid scientific stages.**
This note reports captured-output CPU replay, not a new experiment. No model, tokenizer, GPU, remote
operation, fit, adapter read, or commit was performed by this independent reader.

## Scope and established reference joins

The new `LOSS_OFF_SELECTOR` writer is a counterfactual component control, not an
on-policy continuation of the original loss-off auditor. Its writer is the same
SEQ245 pre-write state:
`48dc1d6d77852bddba75e04ee7442f4ef2a8e72bce5719d39ade4ed974a2b042`.

The retained SEQ245 reduction was hash-checked at
`gpu_artifacts_local/astra_fresh_reader_cycle_terminal_20260914_attempt2/SEQ245_independent_reduction_20260914.json`:
SHA-256 `00a81f14e0517750d00697db2935c23577ffdcc88fd2866c6edd6e06218448cb`.
All six referenced terminal RESULT hashes match the original capsule. The two
reference writers share the parent, corpora, encoded masks and uniform-label
denominator. Their outcomes are reused observations, not new fits or independent
replications.

CPU replay of both retained SEQ246 auditors checked their exact captured prompts,
all 14 calls each, original-auditor unchanged-state receipts, source-table cases,
scores, pointer admission, and repeated-prompt multiplicities. SFT BEFORE choices
are `[1,0,1,0,3,2,3,2]`, exactly SEQ245's executed roster. Original loss-off choices
are `[1,null,1,null,null,null,null,null]`. The two valid pointers `[1,1]` are kept;
no missing address or erroneous reader reply becomes a target.

The tested full binding joins those auditor packets to SEQ245's actual BEFORE
and SELECTED/AFTER stimuli, rather than treating the selector as the writer.
All eight writer-kernel source hashes match the retained reference receipts.

## Completed new-write checks

`tools/astra_reader_audit_transfer_write_reduce.py` accepts `ROOT/train` and
`ROOT/after`. For terminal data it checks the new driver/audit/helper source
hashes, matched parent/source, actual/reference 100-update schedules, target-only
210-mask structure, identical reference corpus/masks, loss scaling and supervised
token totals. The expected source doses, verified by the pure schedule test, are
`[0,200,0,0]`; group doses are 100 old memory, 38 cues, 62 lesson rows, and 200
new-memory presentations. All writers receive the same lesson rehearsal.

Fresh AFTER replay checks the saved-state reload, read-only final state receipt,
A3 routing/strict W0/W8 recall, all 12 old facts, the separate A2 16-case
classifier, reader-OFF, held-text, MISS, and actual-audit-v2 cases/calls/choices.
Invalid routes, unavailable-reader diagnostics, raw text failures, missing and
failed stages remain explicit. Receipt durations are not GPU-utilization data.
No tokenizer re-encoding or independent tensor/base reauthentication is claimed.

Attempt1's archived `prepare/FAILED.json` was read separately: it records
`ValueError('shared_writer_rows_or_recipe_drift')`, `phase=prepare`, `fits=0`,
and `model_calls=0`. Main identifies the cause as tuple/list comparison, repaired
by JSON-canonical equality. The reducer classifies this as
`PRE_MODEL_CPU_PREPARE_FAILURE_NOT_FIT`, not a failed scientific fit.

## Actual outcome and failure decomposition

| Endpoint | LOSS_OFF_SELECTOR new write | SEQ245 SELECTED / UNIFORM (reused) |
|---|---:|---:|
| Own parametric routing | 3/4 | 4/4 each |
| New strict recall W0 / W8 | 1/4 / 1/4 | 4/4 / 4/4 each |
| Old recall W0 / W8 | 12/12 / 12/12 | 12/12 / 12/12 each |
| A2 held classifier | 16/16 | 16/16 each |
| Held-text routing, two banks | 8/8 | 8/8 each |
| Own reader-OFF routing | 2/4 | 2/4 each |
| Unseen MISS | 0/4 | 0/4 each |
| Next actual-reader audit | 7/7: 5 faults, 2 true | 6/6, all true each |

All four own episodes read: seven actual reads, three second reads. Reader-OFF
still issues eight READ commands across four episodes; OFF is not zero commands.
The actual-audit-v2 replay retains all seven replies, including both reads from
the invalid-route episode, without inventing a transition. There are no
unavailable-reader cases. Ordered choices are `[null,0,null,3,2,3,2]`; admitted
source pointers `[0,3,2,3,2]` preserve duplicates. Both NONEs correctly match true
replies; all five fault pointers are correct. This audit produced no fit.

Only source index 1 (`E_BF3K34VYXU`), the fact receiving all 200 new-memory
presentations, passes both strict recall wrappers. Unsampled indices 0, 2, and 3
fail both. Every W0 failure preserves the requested event address but changes
all four node/port/destination/receipt fields: these are content errors, not
final-LF formatting. W8 index 0 is an unparseable expanded narrative; W8 indices
2 and 3 again change all four factual fields. All six failed generations are
terminal and untruncated; full expected/actual strings remain in the reduction's
`stages.after.text_failures` and untouched native records.

Zero-based own tasks 0, 1, and 2 reach their goals; task 3 fails `invalid_route`
after two real reads and zero transitions. Tasks 0 and 2 succeed despite faulty
reader text, so routing success does not imply accurate stored recall. Task 3
reads `E_LT27MCC2IZ`, then `E_PRS7JYHK37`, and emits
`ROUTE P_GBV7TYNMYX`: that port is copied from the second faulty reader reply,
not the grounded target port `P_HZJSRG5OPG`. The latter reader reply is:

```text
Actual:   EVENT E_PRS7JYHK37 AT N_FEKWBHXIER DID P_GBV7TYNMYX GOT N_PZO6QGCFYQ EVIDENCE R_6MJCDE77X2
Expected: EVENT E_PRS7JYHK37 AT N_FJGUU3SD2V DID P_V4LT7SPZJD GOT N_XOP6YZ4IUJ EVIDENCE R_HYDLKZXBE6
```

This is an observed text/command correspondence, not proof of the actor's
internal causal mechanism. Raw routes are under `extracted_complete/after/new_task/`;
audit cases and exact responses are `after/ACTUAL_CASES.json`,
`after/ACTUAL_READERS.json`, and `after/CALL_*.json`.

## Schedule, joins, and measured cost

The reducer verifies all 100 update indexes, 210 masks (96 old +20 cue +62 lesson
+32 new), identical corpus and masks to the references, and the common uniform
label denominator. Doses are old100/cue38/lesson62/new200; old-bank doses are
`[36,32,32]`, new-fact doses `[0,200,0,0]`. Actual supervised tokens are **16969**,
versus **16319** reference-denominator tokens; per-update scales span
1.0171428571428571–1.0666666666666667. Reference actual counts are SELECTED16345
and UNIFORM16319, not equal actual-token budgets.

Train runs 14:12:43.725912–14:16:02.981872 UTC, **199.255960 seconds**, or
**0.501867 updates per receipt second**. AFTER runs
14:16:03.975134–14:18:55.998900 UTC, **172.023766 seconds**. These include stage
overhead and are not GPU utilization, kernel-only time, or monetary cost.
AFTER has **117 calls**: 94 routing/recall calls and 23 audit calls (16 classifier,
7 actual-reader). Captured totals are **22775 input / 2968 emitted tokens**;
the routing/recall subtotal is 14382 / 2809. No calls were rerun.

The common initial writer hash above is bound to the reference parent. Final
train, AFTER loaded state, and AFTER unchanged-state receipts all join at
`b4a5383e6b8c2eb73415833227b7eea15e2ebb34b631bda670adac33a0e5b3d8`.
Source-role hashes and frozen-base receipts pass; tensor files and heavy base
files were not independently opened. Mask checks use captured encodings rather
than a fresh tokenizer invocation.

## Source and validation

- Native source commit: `d0f16e22f0b4a5b61998164193ee8d8bf155c0f3`.
- Native entry SHA-256, matching that commit:
  `bcb70e091ecb74a5d34dcd4138dfc2c07ca577eec971c8c28c6d8f650737fcc0`.
- Reducer SHA-256: `0df8fdba0e92d88239504d504bad4766e077c8a4ae76e77a7458d5a65e6c8b07`.
- Test SHA-256: `9f9ba6022a158f6837edad95853a6211e41422ab927d091cec45ed49cd13c4b3`.
- **43 CPU tests pass**, including nine new tests and real retained-reference
  replay/binding checks; no tests were skipped. Reconfirmed after terminal replay
  in 5.491 seconds. No reducer or test source changes were needed.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.test_astra_reader_audit_transfer_write_reduce \
  tests.test_astra_reader_audit_transfer_write \
  tests.test_astra_fresh_reader_cycle_reduce \
  tests.test_astra_selected_reader_repair_reduce -q
```

## Durable receipt and exact invocation

Used only `extracted_complete`; the incomplete `extracted` directory is preserved.
Working directory: `/data/home/rohing/dream-state`. New receipts were created with
shell noclobber, without overwriting existing evidence. Exit status was zero.

```bash
set -o noclobber
CAPSULE=gpu_artifacts_local/astra_reader_audit_transfer_write_terminal_20260914_attempt2
tar -xOf "$CAPSULE/failed_prepare_attempt1.tar" ./prepare/FAILED.json > "$CAPSULE/SEQ247_failed_prepare_attempt1_receipt_20260914.json"
TRANSFER_CAPTURE="$CAPSULE/extracted_complete"
TRANSFER_SOURCE="$TRANSFER_CAPTURE/source"
PYTHONDONTWRITEBYTECODE=1 python3 tools/astra_reader_audit_transfer_write_reduce.py "$TRANSFER_CAPTURE" \
  --source-root "$TRANSFER_SOURCE" \
  --reference-root gpu_artifacts_local/astra_fresh_reader_cycle_terminal_20260914_attempt2/extracted \
  --reference-receipt gpu_artifacts_local/astra_fresh_reader_cycle_terminal_20260914_attempt2/SEQ245_independent_reduction_20260914.json \
  --replay-root gpu_artifacts_local/astra_reader_audit_matched_replay_terminal_20260914_attempt1/extracted \
  --a1-collection gpu_artifacts_local/astra_adult_cycle_first_result_20260914/final/CUE_REPLAY/collect/COLLECTION.json \
  --a2-collection gpu_artifacts_local/astra_second_adult_cycle_first_result_20260914/capture/CUE_REPLAY/collect/COLLECTION.json \
  --prepare-failure "$CAPSULE/SEQ247_failed_prepare_attempt1_receipt_20260914.json" \
  > "$CAPSULE/SEQ247_independent_reduction_20260914.json"
```

Persisted primary receipt:
`gpu_artifacts_local/astra_reader_audit_transfer_write_terminal_20260914_attempt2/SEQ247_independent_reduction_20260914.json`
SHA-256 `9c6dfe501557b3ff83c4e6875e3f99d477a4607fc56ed7043539da38fb4e3c7c`.
It includes stages, exact captured texts, audit replay, reference outcomes,
source hashes, and failed-prepare classification. Its top-level result is
`COMPLETE`, with both terminal stages COMPLETE and empty pending/failed/invalid
lists. Native input schema is `DEV_READER_AUDIT_TRANSFER_WRITE_V1` and actual
audit schema is `DEV_FRESH_READER_CYCLE_ACTUAL_AUDIT_V2`.

Verified local archive SHA-256s (Main reports agreement with remote):
- `terminal_root.tar`: `14386b5015b65a5fb3f18e1e57d27915f42c914c4e98638c70f6f2dcb73126db`.
- `failed_prepare_attempt1.tar`: `a4428bfe8a7da892a92ae7d0243ac4d1fd3f844db28126d3d42f7f60fdcd92c2`.
- Extracted single failed-prepare receipt:
  `bde66bdb85cdd1c29ae350e8960f0859bdb0655cf1b19b6498e72cc55042a98a`.

## Strongest conclusion and limits

For this one shared writer, concentrating the new-memory allocation on the
original loss-off auditor's duplicate-valid material yields worse new recall
and routing than the reused full-coverage reference schedules, with old recall
and tested controller/classifier retention intact. This supports the narrow
material-consequence prediction. It does not isolate semantic judgment from
format compliance, coverage from repetition/order, or selection from the
resulting gradient trajectory and differing actual target-token totals.
The selector and writer have different developmental states: this is explicitly
counterfactual, not on-policy. The two references are reused, not replications.
Actual-audit denominators change with the reader's failures (7 mixed vs 6 true),
so 7/7 is not evidence of better auditing than 6/6. Neither an autonomous
selection advantage over uniform nor H1/H2 is established. No follow-up fit was
performed by this reader; owned reducer/tests/memo are released.
