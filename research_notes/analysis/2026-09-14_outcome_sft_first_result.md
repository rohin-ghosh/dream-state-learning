# First outcome-SFT result — 2026-09-14

**Real but selective outcome transfer; not a qualified birth.** A100 `/tmp/astra_outcome_distill_20260914_attempt1/run/RESULT.json` is `DEV_OUTCOME_SFT_COMPLETE`: 256 updates, seed 0, BASE 56 physical calls and FITTED 139, with zero recorded infrastructure failures. Whole chains improve 0→4/8, useful reads 0→8/8, and typed steps 1→8/8; canaries regress 16→4/16. `reportable=true` means these results can be reported, not that qualification passed.

**Exactly 5/10 criteria pass**, counted from the ten `criteria[].passed` booleans. The separate `criteria_passed=false` is an aggregate boolean, not a count of zero or a missing value.

| Criterion | FITTED count/n | Minimum | Pass |
|---|---:|---:|---|
| SEEK | 4/4 | 3 | yes |
| PROSPECT | 2/4 | 3 | no |
| CHECK | 0/4 | 3 | no |
| CONTINUE | 0/4 | 3 | no |
| typed_interventions | 32/32 | 30 | yes |
| whole_chains | 4/8 | 6 | no |
| useful_reads | 8/8 | 7 | yes |
| typed_steps | 8/8 | 7 | yes |
| canaries | 4/16 | 15 | no |
| chain_gain | 4/8 | 2 | yes |

## Eight captured chain outcomes

Indices are zero-based; worlds/members follow the fixed reduced roster. Arrival is an observed accepted STEP reaching GOAL; terminal goal STOP and the frozen strict whole-chain criterion remain distinct.

| Index / member | Arrival | Goal STOP | Strict success | Captured outcome |
|---|---|---|---|---|
| 0 / h00-m0 | no | no | no | 20 attempts. Correct first STEP matches the EVENT's GOT, but emits REVISE rather than KEEP, enters recovery reads, and exceeds the THINK budget. Final counts: THINK9/READ10/STEP1/STOP0. |
| 1 / h00-m1 | no | no | no | 3 attempts; `invalid_step`. Reads useful events but selects the DID from a same-goal, wrong-AT row rather than the current-state row. |
| 2 / h01-m0 | yes | yes | yes | 7 actions: INDEX → RELATION → STEP → REVISE → recovery RELATION → STEP → STOP. Actual first outcome contradicts GOT. |
| 3 / h01-m1 | yes | yes | yes | Same seven-action recovery sequence; reaches GOAL and immediately stops. |
| 4 / h02-m0 | no | no | no | 20 attempts. First STEP matches GOT; nevertheless revises, follows recovery queries and loops until THINK over-budget. Counts 9/10/1/0. |
| 5 / h02-m1 | no | no | no | 20 attempts. Same matched-GOT→REVISE error and repeated recovery loop; THINK over-budget. Counts 9/10/1/0. |
| 6 / h03-m0 | yes | yes | yes | Seven-action mismatch/recovery route; reaches GOAL and immediately stops. |
| 7 / h03-m1 | yes | yes | yes | Seven-action mismatch/recovery route; reaches GOAL and immediately stops. |

There are **4/8 actual arrivals and 4/8 strict successes**, not eight successful chains. Per-chain strict identities are determined without substituting an arrival-only scorer: the frozen strict rule requires arrival and terminal goal STOP, exactly four captured runs have both, and the recorded strict total is four. Therefore those four are the strict successes. Full decoded actions and this inference basis are retained in the local analysis JSON.

Concrete failures:
- Chain 0's relevant event says `DID M2AP_IUE37TK2HPZZ GOT M2AN_3L54GUNJBJZJ`; that STEP actually reaches `M2AN_3L54GUNJBJZJ`. It then emits `THINK REVISE M2AE_TWJYL5NCV7XL` instead of KEEP and eventually repeats recovery reads/checks. This is a wrong outcome branch, not failure to acquire READ syntax.
- Chain 1's current-state event requires `STEP M2AP_WEZKRZ4Z7HHL`. The model emits `STEP M2AP_U6JU3ZZXVRCG`, copied from another EVENT whose FOR matches but AT is `M2AN_5JVVGNWQS5ZW`, not CURRENT `M2AN_CMQLTX6MSVJX`; execution terminates as `invalid_step`.

## All twelve canary failures

Canaries 0–3 (two READ INDEX, two READ RELATION) copy exactly. Every failed canary is generation-valid but fails the exact typed-action/copy contract: these are command/type substitutions, not newline or truncation failures. BASE copies all sixteen correctly. Below are exact raw strings; none has an added LF.

| Index | Expected | FITTED raw | Category |
|---|---|---|---|
| 4 | `STEP M2AP_47PPEAAY3WQZ` | `READ RELATION M2AP_47PPEAAY3WQZ` | STEP→READ; port used as query |
| 5 | `STEP M2AP_DEQBTLW3Z4HX` | `READ RELATION M2AP_DEQBTLW3Z4HX` | STEP→READ; port used as query |
| 6 | `STEP M2AP_4X2VR7ADJJQF` | `READ RELATION M2AP_4X2VR7ADJJQF` | STEP→READ; port used as query |
| 7 | `STEP M2AP_V6KSPKPZPDBL` | `READ RELATION M2AP_V6KSPKPZPDBL` | STEP→READ; port used as query |
| 8 | `THINK KEEP M2AE_AONBHSWCA4AI` | `READ INDEX M2AE_AONBHSWCA4AI` | KEEP→READ; event used as node |
| 9 | `THINK KEEP M2AE_PPZ3NWTQGJCI` | `READ INDEX M2AE_PPZ3NWTQGJCI` | KEEP→READ; event used as node |
| 10 | `THINK REVISE M2AE_PY4V3CCACLOO` | `READ RELATION M2AE_PY4V3CCACLOO` | REVISE→READ; event used as query |
| 11 | `THINK REVISE M2AE_LCCAWV5J7ZMR` | `READ RELATION M2AE_LCCAWV5J7ZMR` | REVISE→READ; event used as query |
| 12 | `STOP` | `READ INDEX CANARY` | STOP→READ; fabricated operand |
| 13 | `STOP` | `READ INDEX CANARY` | STOP→READ; fabricated operand |
| 14 | `STOP` | `READ INDEX CANARY` | STOP→READ; fabricated operand |
| 15 | `STOP` | `READ INDEX CANARY` | STOP→READ; fabricated operand |

Failure categories total 4 STEP substitutions + 2 KEEP substitutions + 2 REVISE substitutions + 4 STOP substitutions = 12. Correct STEP/REVISE/STOP use in successful chains shows these action classes were not globally erased; generic copy instructions now elicit an inappropriate READ-mode response.

## Captured training coverage and one next comparison

The prior D2-guided collector supplied **6 successful episodes out of 32, yielding 42 rows**, from h04-m1, h05-m0, h05-m1, h06-m1, h07-m0 and h07-m1. Every selected trajectory has the same seven-action recovery structure: INDEX, RELATION, STEP, REVISE, recovery RELATION, STEP, STOP. Counts are READ INDEX6, READ RELATION12, STEP12, THINK REVISE6, STOP6, **THINK KEEP0**. Their recorded strict source checks pass; these are recovery-only successes, not coverage of the matched-outcome branch. The source contains guided teacher successes, not authentic autonomous-parent/birth evidence.

**Mechanistic diagnosis (supported hypothesis, not causal proof): recovery-only selection taught a default REVISE/recovery policy.** It transfers to the four mismatch chains but sends three correctly predicted first outcomes into unnecessary recovery loops. Canary substitutions separately expose serious instruction/task-mode interference; absence of KEEP alone cannot explain failures to copy STEP, REVISE and STOP, which were present in training.

**One proposed comparison, for Main only:** compare the existing recovery-only outcome SFT against success-only outcome SFT with prospectively balanced matched-GOT/KEEP and mismatched-GOT/REVISE source trajectories. Use training-only worlds/identifiers, the same frozen base/initial adapter/seed, 256-update batch-four schedule and total action presentations; do not train on any held chain/canary prefix, output, or identifier. Keep the existing evaluation and all thresholds unchanged. This tests whether branch coverage fixes inappropriate revision on normal paths while preserving recovery transfer. Canary retention remains a hard observed constraint, not presumed repaired by balancing coverage. No comparison was launched here.

## Evidence

Selective JSON capture: `gpu_artifacts_local/astra_outcome_sft_first_result_20260914_attempt1/`. `CAPTURE.json` contains the eight FITTED chain runs, all FITTED/BASE canaries, result/provenance, 42 student rows and selected source episodes; no weights, tensors or full native event directory were transferred. `ANALYSIS.json` enumerates chains, all canaries, source coverage and the 5/10 criterion count; `HASHES.json` records source-file hashes and local capture hashes. Captured from A100 at 2026-09-14 07:58:23 UTC.

- Remote `run/RESULT.json`: `82503714b127618266855603448cb618e97fe1a593120e1283117323034f63f1`
- Remote `run/FITTED/event-0279.json`: `60333cd9274055e3125bd22ab5f5c3e8468bcdf4800b6b50bbd9b671306adca7`
- Remote `run/STUDENT_ROWS.jsonl`: `fdd206f0b5725c41153228efb9fd2aafb1566f79b90f002b0af5461d75267c65`
- Local `CAPTURE.json`: `066711af989d936e48032ae302ca4c3e3513ed53ebc1b162ce4b9a37955d1065`

Only this note and new local captured/derived JSON were written. No tokenizer/model/GPU/fitting work, code/notebook edits, commits, threshold changes or launch actions.
