# D2 chain failure localization: eight retained reduced-chain traces

Date: September 14, 2026, UTC. Bounded local CPU analysis of existing DEV
evidence only. No code, model, tokenizer, checkpoint-deserialization, training,
GPU, remote-node, threshold, or notebook changes. No causal attribution or
scientific promotion is made here.

## Finding

**All eight D2 chains fail the existing whole-chain criterion, but one actually
reaches GOAL.** Task 12 / h06 executes both required STEPs, obtains the full
required public evidence, and eventually stops at GOAL. It inserts an extra
`THINK KEEP` after the arrival STEP instead of stopping on the very next call.
The existing immediate-STOP requirement is its sole failed whole-chain
conjunct. This is not a proposal to relax that requirement.

The remaining seven chains have **byte-identical emitted action sequences to
D1**. Four stop after the correct first STEP and KEEP without requesting the
second-hop evidence; h04 obtains the recovery evidence but emits another THINK
instead of its second STEP; h12 stops immediately; h14 emits a malformed
THINK with a node operand. The D1 note's statement that no chain arrives at
GOAL remains correct for D1, but must not be carried forward to D2.

## Source paths, binding and reconstruction

Paths below are repository-relative. These aliases are used in the call tables:

- **D2_CUSTODY:** `gpu_artifacts_local/astra_stage2a_d2_preservation_20260914_attempt1/evidence/astra_stage2a_d2_20260914_attempt1/run/ATOM_LOCAL/`.
- **D2_RUN:** `gpu_artifacts_local/astra_stage2a_d2_preservation_20260914_attempt1/evidence/astra_stage2a_d2_20260914_attempt1/run/`.
- **D1_CUSTODY:** `gpu_artifacts_local/astra_stage2a_d1_result_preservation_20260914_attempt1/evidence/astra_stage2a_d1_eval_recovery_20260914_attempt1/run/ATOM_LOCAL/`.
- **ORIGINAL_RUN:** `gpu_artifacts_local/astra_stage2a_d1_result_preservation_20260914_attempt1/evidence/astra_stage2a_reduced_20260914_attempt1/run/`.
- **COMPARISON:** `gpu_artifacts_local/astra_stage2a_d2_compare_20260914_attempt1/COMPARISON.json`.
- **D1_REPLAY:** `gpu_artifacts_local/astra_stage2a_d1_result_preservation_20260914_attempt1/evidence/astra_stage2a_baseline_replay_code_20260914_attempt1/D1_COMBINED_REPLAY.json`.
- **D1_ANALYSIS:** `research_notes/analysis/2026-09-14_seq200_d1_controller_recovery.md`.

The exact saved structure is `evidence/astra_stage2a_d2_20260914_attempt1/run/`,
not `evidence/ATOM_LOCAL/`. `D2_RUN/D2/` holds the saved full-state artifact;
its JSON manifest records 512 completed updates and cursor 2048, with state
SHA-256 `2ce34dced3b9c55335d4bdf195b870ecdef69a2bc94de641cb1ccbf151aee2bf`.
The readout is the sibling `ATOM_LOCAL/` tree. No checkpoint was loaded for
this analysis; the update count is retained manifest metadata.

An initial `git pull --ff-only` (with autostash disabled) returned “Already up
to date” at `e655884e`. Other workers' edits were left untouched. The replay,
preparer, reducer, runtime, custody and comparison source hashes were checked
against COMPARISON and matched. In-memory reconstruction used the existing
`prepare_reduced_held(allocate_source(master=original_master))` and
`replay_state(..., stage="D1"/"D2")`, with original REQUEST bindings, then
`composition_birth_stage2a_scoring.score_chain`. This reconstitutes the same
bound held objects and consumes captured generations/counts; it does not
generate new actor responses or select new material.

The reconstructed held receipt is
`a09df23878ff779ebe7a08f56fc79adef89244c0ed423da6188a1134e482ad02`, matching
COMPARISON. The master hash is
`ff19dd8b4d60caea880902904c6fa41830a7c6b4c030bb454070102fe7e3afcd`.
Both fitted custody trees carry state ID `STAGE2A-REDUCED-ATOM-20260914-A1`;
their explicit D1/D2 stages and distinct trees are therefore essential.

Custody verification and exact replay completed without infrastructure
failures. Original/fitted REQUEST hashes matched COMPARISON. The sorted
name/size/SHA-256 custody-tree pins were independently recomputed locally:

| Tree | Files | Bytes | Tree SHA-256 |
| --- | ---: | ---: | --- |
| Retained BASE | 171 | 4,105,390 | `b1e7c8383c00181bba9f390903b40a2d2d5a9cfa6085ab105ff44e879540f809` |
| Recovered D1 | 255 | 7,567,675 | `c3885040c2ca6f596ec95a6807ef9f583b4c909e61d5dde140f998b82889e4e1` |
| D2 | 258 | 7,726,278 | `1846dc25ce2b579ab5aa3cb5785b02a75a130918c3e48904ee909f1a3da699d6` |

BASE/D2 match COMPARISON; D1 matches D1_REPLAY. D2 COMPLETE has 172 events,
stage D2 and terminal reason `completed_unscored`; its raw SHA-256 is
`b71ad5c7a6156f4f56c471347e2b673cdf459c24336ee92d4c30fc78fc25ce24`.
Tensor sidecars were integrity-checked as bytes, not deserialized. No torch,
transformers or PEFT module was imported by the reconstruction commands.

## Aggregate reconciliation

| Recorded/reconstructed quantity | D1 | D2 |
| --- | ---: | ---: |
| Chain physical calls | 36 | 37 |
| Total physical calls, including 32 interventions and 16 canaries | 84 | 85 |
| Reserved slots / unused slots | 280 / 196 | 280 / 195 |
| Correct first STEP | 6/8 | 6/8 |
| Existing first-outcome CHECK metric | 4/8 | 5/8 |
| Complete required READ set | 2/8 | 2/8 |
| Required public READ evidence before both STEPs | 0/8 | 1/8 |
| Correct full route | 0/8 | 1/8 |
| Actual GOAL arrival | 0/8 | 1/8 |
| Mechanical GOAL-arrival STOP | 0/8 | 1/8 |
| STOP immediately after the second STEP | 0/8 | 0/8 |
| Whole-chain success | 0/8 | 0/8 |
| Useful pre-first-STEP READ | 6/8 | 6/8 |
| Existing `typed_steps` metric (per-chain strict typing) | 7/8 | 7/8 |

D2 attempt counts, in task order 0,4,8,12,16,20,24,28, are
**5,5,7,8,5,5,1,1**. D1 counts are **5,5,7,7,5,5,1,1**.
D2 termination reasons are six `premature_stop`, one `goal_arrival_stop`,
and one `malformed_action`. None is a call/token budget or infrastructure
termination; all eight have valid generation metadata and remain within the
existing budgets. h14 alone fails strict action typing/execution.

The reconstructed reduced metrics also agree with COMPARISON: SEEK 4/4,
PROSPECT 4/4, CHECK interventions 4/4, CONTINUE 3/4, typed interventions 31/32,
canaries 15/16, whole chains 0/8, useful reads 6/8, typed steps 7/8 and chain
gain 0/8. D1's CONTINUE and typed-intervention counts were 2/4 and 30/32.
The intervening-chain CHECK metric above is not the separate CHECK
intervention-pair metric. Nor is `typed_steps` a count of actual STEPs: it
reuses whole-trace strict typing, so h12's lone valid STOP contributes to it.

## Eight chain reconstructions

All selected tasks use member m0. `c` is zero-based within-chain call index;
`G` is the actual `D2_CHAIN` global logical ordinal; `P` is zero-based physical
call index within D2 (also its actor-call index here). Each filename is a
`CALL_CAPTURED` JSON file under D2_CUSTODY, not a new output. Each listed
generation was joined to its captured request/generation and replayed ledger.
Only STEPs change CURRENT; READ/THINK/STOP leave it unchanged in these traces.
Required actions below come from the existing evaluator witness, not from a
new actor policy, and are distinguished from actual emitted actions.

| Task/world | First STEP | CHECK metric | Full READ set | Arrival | D2 termination | D1 raw-action relation |
| --- | --- | --- | --- | --- | --- | --- |
| 0 / h00 | Correct | Pass | 2/4; incomplete | No | Premature STOP after first KEEP | Identical |
| 4 / h02 | Correct | Pass | 2/4; incomplete | No | Premature STOP after first KEEP | Identical |
| 8 / h04 | Correct | Fail: two intervening THINKs | 3/3; complete | No | Recovery read, extra KEEP, premature STOP | Identical |
| 12 / h06 | Correct | Pass | 3/3; complete | Yes | GOAL STOP delayed by an extra KEEP | Changed; details below |
| 16 / h08 | Correct | Pass | 2/4; incomplete | No | Premature STOP after first KEEP | Identical |
| 20 / h10 | Correct | Pass | 2/4; incomplete | No | Premature STOP after first KEEP | Identical |
| 24 / h12 | Absent | Absent/fail | 0/3 | No | Immediate premature STOP | Identical |
| 28 / h14 | Absent | Absent/fail | 0/3 | No | Malformed first action | Identical |

### Task 0 / h00: stop at the first successor

START `M2AN_J77KXR6NQC3X`; GOAL `M2AN_HUWZFYAB56SA`.

| c | G | P | Captured file | Actual action |
| ---: | ---: | ---: | --- | --- |
| 0 | 1008 | 0 | `event-0002.json` | `READ INDEX M2AN_J77KXR6NQC3X` |
| 1 | 1009 | 1 | `event-0004.json` | `READ RELATION M2AQ_LJFVEQ6RXOJG` |
| 2 | 1010 | 2 | `event-0006.json` | `STEP M2AP_JDFGBMH5TSFS` |
| 3 | 1011 | 3 | `event-0008.json` | `THINK KEEP M2AE_BHNB22K2I7ZA` |
| 4 | 1012 | 4 | `event-0010.json` | `STOP` |

The STEP reaches `M2AN_5HMTPLB6ZAHO`, matching its first EVENT's prediction;
the KEEP command and operand match the witness. Both initial READs return
exact required public text with one relevant GOAL+CURRENT row. The remaining
required READs are `READ INDEX M2AN_5HMTPLB6ZAHO` and
`READ RELATION M2AQ_LLTPNM5EPBML`; neither is emitted. The required second
STEP is `STEP M2AP_GHEHJNVLK7O7`. STOP instead occurs at the non-goal first
successor. D1 logical calls 0–4 emit the same five actions.

### Task 4 / h02: the same five-call stopping pattern

START `M2AN_HNOWSDMK6R7S`; GOAL `M2AN_3IB5A5MMWEYP`.

| c | G | P | Captured file | Actual action |
| ---: | ---: | ---: | --- | --- |
| 0 | 1124 | 5 | `event-0012.json` | `READ INDEX M2AN_HNOWSDMK6R7S` |
| 1 | 1125 | 6 | `event-0014.json` | `READ RELATION M2AQ_OULKP6K4XSPG` |
| 2 | 1126 | 7 | `event-0016.json` | `STEP M2AP_IZEGDJXPHO7Y` |
| 3 | 1127 | 8 | `event-0018.json` | `THINK KEEP M2AE_YKOHPDRWMFTT` |
| 4 | 1128 | 9 | `event-0020.json` | `STOP` |

CURRENT becomes `M2AN_2OUVKNS2QRGF` at c2, not GOAL. The first STEP and KEEP
are correct; the two initial READs have exact required responses and one
relevant row each. Required but absent: `READ INDEX M2AN_2OUVKNS2QRGF`,
`READ RELATION M2AQ_2N73R7IXA5KI`, then `STEP M2AP_6SEQCNWPWV7X` to GOAL.
Termination is `premature_stop`. D1 logical calls 116–120 are action-identical.

### Task 8 / h04: recovery evidence acquired, second STEP absent

START `M2AN_2N4IQDSK5EXW`; GOAL `M2AN_FT6IJVIGF3HZ`.

| c | G | P | Captured file | Actual action |
| ---: | ---: | ---: | --- | --- |
| 0 | 1240 | 10 | `event-0022.json` | `READ INDEX M2AN_2N4IQDSK5EXW` |
| 1 | 1241 | 11 | `event-0024.json` | `READ RELATION M2AQ_VZMWAXHMAIXI` |
| 2 | 1242 | 12 | `event-0026.json` | `STEP M2AP_ZJLSTRKXX4VY` |
| 3 | 1243 | 13 | `event-0028.json` | `THINK REVISE M2AE_C4BDHJKBM7ZA` |
| 4 | 1244 | 14 | `event-0030.json` | `READ RELATION M2AQ_IWRFA6DKMGZU` |
| 5 | 1245 | 15 | `event-0032.json` | `THINK KEEP M2AE_HEA2KPJOEXWC` |
| 6 | 1246 | 16 | `event-0034.json` | `STOP` |

The first EVENT predicts GOT `M2AN_N2XJEL3OGSVH`, but the actual first STEP
produces CURRENT `M2AN_XXMT3JPHRGYE`; that is the bound mismatch outcome,
so the first STEP is correct and the literal c3 REVISE matches the witness.
All three required READs (c0,c1,c4) occur and each returns one relevant row.
The recovery response at c4 contains:

```text
EVENT M2AE_HEA2KPJOEXWC AT M2AN_XXMT3JPHRGYE FOR M2AN_FT6IJVIGF3HZ DID M2AP_RMWI4YU7ONJ3 GOT M2AN_FT6IJVIGF3HZ RECOVER M2AQ_P7POPH7EDHIR EVIDENCE M2AR_PQ7OTQBJGSUW
```

Nevertheless `STEP M2AP_RMWI4YU7ONJ3` is never emitted. At c5 the learner
KEEPs that recovery EVENT while CURRENT is still `M2AN_XXMT3JPHRGYE`, not
the EVENT's GOT/GOAL. It then stops there. The existing first-outcome CHECK
metric fails because there are **two THINKs after the first STEP and before
the absent second STEP/end**, not because the literal first REVISE token or
operand was wrong. The full READ *set* is complete; the two-STEP public-evidence
predicate is false because there is no second STEP. D1 logical calls 232–238
are exactly the same actions and have the same failure pattern.

### Task 12 / h06: genuine arrival, extra THINK before STOP

START `M2AN_7LS5O2V5QIVJ`; GOAL `M2AN_BJ5N576VCY5O`.

| c | G | P | Captured file | Actual action |
| ---: | ---: | ---: | --- | --- |
| 0 | 1356 | 17 | `event-0036.json` | `READ INDEX M2AN_7LS5O2V5QIVJ` |
| 1 | 1357 | 18 | `event-0038.json` | `READ RELATION M2AQ_3J54KOL5XRA4` |
| 2 | 1358 | 19 | `event-0040.json` | `STEP M2AP_YTPLMJBHEC63` |
| 3 | 1359 | 20 | `event-0042.json` | `THINK REVISE M2AE_5XXULNZPHPXF` |
| 4 | 1360 | 21 | `event-0044.json` | `READ RELATION M2AQ_O4ZBCEELN74H` |
| 5 | 1361 | 22 | `event-0046.json` | `STEP M2AP_MPAGZ5X2LWB2` |
| 6 | 1362 | 23 | `event-0048.json` | `THINK KEEP M2AE_GE6W4RYRNRMY` |
| 7 | 1363 | 24 | `event-0050.json` | `STOP` |

The first EVENT predicts `M2AN_YBJ3LIU4BC36`; c2 actually reaches the bound
mismatch CURRENT `M2AN_CWBYFIOPN2KH`. c3 emits the correct REVISE. All three
required READs (c0,c1,c4) return the exact witness responses at the appropriate
CURRENT, with one relevant row each. The c4 recovery response includes:

```text
EVENT M2AE_GE6W4RYRNRMY AT M2AN_CWBYFIOPN2KH FOR M2AN_BJ5N576VCY5O DID M2AP_MPAGZ5X2LWB2 GOT M2AN_BJ5N576VCY5O RECOVER M2AQ_YGV6RPLTFKXE EVIDENCE M2AR_RANYELQQROPM
```

c5 emits that DID and the recorded WORLD response sets CURRENT to
`M2AN_BJ5N576VCY5O` = GOAL. c6 leaves CURRENT there; c7 is an accepted
`goal_arrival_stop`. Thus first STEP, first-outcome CHECK, complete READ set,
public evidence before both STEPs, full route, typing, execution, generation,
budgets, actual arrival, exact final STOP and mechanical goal-stop all pass.
`stop_immediately_after_second_step` alone is false: the required next call
after c5 is STOP, not the extra c6 KEEP. See the unchanged conjunction in
`organism_v6/composition_birth_stage2a_scoring.py:492` and
`organism_v6/composition_birth_stage2a_scoring.py:496`.

D1 agrees through c4 (D1 logical 348–352), then emits:

- D1 c5 / G353 / P22 / **D1_CUSTODY** `event-0046.json`:
  `THINK KEEP M2AE_TELF3HHO2G2P`.
- D1 c6 / G354 / P23 / **D1_CUSTODY** `event-0048.json`: `STOP`.

That D1 KEEP names a distractor row in the same recovery response: its AT is
`M2AN_3SLKHTR2UFKQ`, FOR is `M2AN_GXJJSTPO637Z`, and GOT is
`M2AN_26OPYHMJ3UOV`, none matching the needed current/goal route. D1 never
executes the second STEP and stops at `M2AN_CWBYFIOPN2KH`. D2 therefore does
more than insert a STEP into otherwise identical text: it also changes that
KEEP operand to the relevant second-hop EVENT, after executing its STEP.
The CHECK metric rises from fail to pass because D2 has exactly one THINK
between its two STEPs; the additional KEEP is now after arrival and fails the
separate immediate-STOP rule. These are sequence/score facts, not an inferred
internal mechanism.

### Task 16 / h08: stop without the second directory/relation

START `M2AN_DYS47CZYIRG4`; GOAL `M2AN_2VCIDZ3V73FD`.

| c | G | P | Captured file | Actual action |
| ---: | ---: | ---: | --- | --- |
| 0 | 1472 | 25 | `event-0052.json` | `READ INDEX M2AN_DYS47CZYIRG4` |
| 1 | 1473 | 26 | `event-0054.json` | `READ RELATION M2AQ_4KQ4QWTRJXX2` |
| 2 | 1474 | 27 | `event-0056.json` | `STEP M2AP_HDDSIBMIF4MN` |
| 3 | 1475 | 28 | `event-0058.json` | `THINK KEEP M2AE_DOXDQQVVWGWV` |
| 4 | 1476 | 29 | `event-0060.json` | `STOP` |

The correct first STEP reaches `M2AN_FR6KV2ZKFFZB`; the first KEEP is correct.
The two initial READs are required and useful. The other required READs are
`READ INDEX M2AN_FR6KV2ZKFFZB` and `READ RELATION M2AQ_LEVRMFFU7XOO`, followed
by `STEP M2AP_4ZP5CRIAWEWN` to GOAL. None occurs; STOP is premature at the
first successor. D1 logical calls 464–468 emit the same five actions.

### Task 20 / h10: the same missing-second-hop pattern

START `M2AN_OYS2OUTLTCVC`; GOAL `M2AN_UNZNJTNU3T23`.

| c | G | P | Captured file | Actual action |
| ---: | ---: | ---: | --- | --- |
| 0 | 1588 | 30 | `event-0062.json` | `READ INDEX M2AN_OYS2OUTLTCVC` |
| 1 | 1589 | 31 | `event-0064.json` | `READ RELATION M2AQ_4INULEEKH6IJ` |
| 2 | 1590 | 32 | `event-0066.json` | `STEP M2AP_RQS25GUKI6T3` |
| 3 | 1591 | 33 | `event-0068.json` | `THINK KEEP M2AE_TEGTQ2HOGPDA` |
| 4 | 1592 | 34 | `event-0070.json` | `STOP` |

The correct first STEP reaches `M2AN_O3CYGSDG3V4C`, followed by the correct
KEEP. Exact initial READ evidence is present. Missing required READs:
`READ INDEX M2AN_O3CYGSDG3V4C` and `READ RELATION M2AQ_LV7TRKCWYJIH`.
The required second STEP is `STEP M2AP_2AKXD6UYR2R6`; it is absent. STOP
terminates at the non-goal first successor. D1 logical calls 580–584 are
action-identical.

### Task 24 / h12: STOP before any read or movement

START `M2AN_WNWTODY3DUV3`; GOAL `M2AN_WXGKPTJ6SGNX`.

| c | G | P | Captured file | Actual action |
| ---: | ---: | ---: | --- | --- |
| 0 | 1704 | 35 | `event-0072.json` | `STOP` |

CURRENT remains START, so termination is `premature_stop`. No first STEP,
CHECK or useful READ occurs. All three required READs are missing:
`READ INDEX M2AN_WNWTODY3DUV3`, `READ RELATION M2AQ_KK2NOJ5MEONO`, and
`READ RELATION M2AQ_RGCHGQAHII2V`. The witness's first STEP is
`STEP M2AP_XHJ4LIYGJNVE` to `M2AN_NDEDNTAU7EWA`, its CHECK is
`THINK REVISE M2AE_CBZJIWUL64G4`, and its second STEP is
`STEP M2AP_NZEW4KFG7GOY`; none was attempted. D1 logical call 696 is the
same lone STOP. It is syntactically valid, not a successful route.

### Task 28 / h14: wrong identifier type in the first action

START `M2AN_UIFUETGZ2T4S`; GOAL `M2AN_PCCSEZHBBEOZ`.

| c | G | P | Captured file | Actual action |
| ---: | ---: | ---: | --- | --- |
| 0 | 1820 | 36 | `event-0074.json` | `THINK KEEP M2AN_UIFUETGZ2T4S` |

KEEP requires an event ID; the emitted operand is a node ID. The parser
marks it invalid, the session rejects it with `malformed_action`, and CURRENT
remains START. This is an action-grammar failure, not truncated generation or
a transport failure. No first STEP/CHECK or READ evidence exists. The required
READ set is `READ INDEX M2AN_UIFUETGZ2T4S`,
`READ RELATION M2AQ_HYMQI5GHHORN`, `READ RELATION M2AQ_L3F7NC3IFBOL`.
The witness calls for `STEP M2AP_ULKVC4L2OYMF` to `M2AN_ND4IVHBZ7XJX`,
`THINK REVISE M2AE_LAKZQPL5YWIY`, then `STEP M2AP_YECZNUUX2NUY` to GOAL.
None was attempted. D1 logical call 812 has the identical malformed bytes.

## Interpretation boundary and retained pins

The trace-local partition is four first-successor premature stops, one
recovery-read-without-second-STEP premature stop, one delayed-STOP goal
arrival, one immediate premature stop, and one malformed opening action.
Seven unchanged action sequences plus the h06 change are the observed D1/D2
pattern; they do not identify why the learner produced it. In particular the
D1 note's training/history context-mismatch hypothesis remains a hypothesis.
This analysis neither tests CLOSED nor attributes any difference to that
curriculum, CURRENT handling, internal composition, or additional dose alone.
D1 and D2 use the same bound tasks but their own stage-specific logical slots
and decode seeds; equality of emitted actions is not equality of full requests,
seeds or model states.

No criterion, endpoint, prompt, evidence set or denominator has been changed.
Actual arrival 1/8 must not replace whole-chain success 0/8 or the reported
whole-chain gain 0/8 against BASE. The reported overall criteria remain false.
No new experiment, fit, retry, promotion or launch follows from this note.

Additional byte pins for this reconstruction:

| Source | SHA-256 |
| --- | --- |
| COMPARISON | `c13fd975a6a95852791771ff34523082b7478294e967cd0c3ddb7dae504ef53f` |
| D1_ANALYSIS | `9ba4b542a254d45236da4d9d5efb54c95689c5464d08d5f9640cf61651b48a58` |
| `gpu/astra_stage2a_replay_baseline.py` | `ba21af5c7f8c76a17f4bbeb6e20821b20f7ca2ce08a566a9de9364e7304a1814` |
| `gpu/astra_stage2a_native_prepare.py` | `d8cfc927024d4ac19fdae06325114a9a1ed858e6e6f18169ff4ef5390d09602d` |
| `organism_v6/composition_birth_stage2a_screen_reduce.py` | `87ffe490409aa72ef2caad5763058174a2432601bde71e4e85afdf0f62ec9ccb` |
| `organism_v6/composition_birth_stage2a_screen_runtime.py` | `90d836e32bcd54bc09279ad3f731a0d67f74edfac69704693565995791ca8e55` |
| `organism_v6/composition_birth_stage2a_screen_custody.py` | `94f0421933dbd69885bc256d4c663b5ba31daad33e72e1c01ccf985eee00c18c` |
| `organism_v6/composition_birth_stage2a_scoring.py` | `4736001bcc61dc42afef4df2a20c1848fb4c0db0ad1d09d947f4c7b83e564828` |
| `organism_v6/composition_birth_stage2a_held.py` | `fbdf3e82b42108a1d8b420a19769e65db282705bd34b8d93a7e8634639afe0ad` |
| `organism_v6/composition_birth_stage2a.py` | `1e750b7ae8151f122dbde6abc0ecb9e7b779af43b0fa0240fea1a6584741c40a` |

These checks bind retained bytes and reconstructed traces, not independently
authenticated tokenizer/runtime provenance or malicious whole-bundle
substitution. All original sources, failed-attempt records and artifacts were
preserved. Only this analysis file was authored; nothing was committed.
