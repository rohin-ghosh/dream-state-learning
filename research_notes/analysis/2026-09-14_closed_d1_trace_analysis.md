# CLOSED-D1 attempt2: eight chains and four canary failures

September 14, 2026. Bounded analysis of captured readout JSON only. No model,
tokenizer, checkpoint deserialization, fit, GPU action, or scoring-rule change.

## Finding

**Task 0 / h00 is the sole strict success and sole actual GOAL arrival.**
It reads both hops, executes both correct STEPs with the intervening KEEP,
then immediately stops at GOAL. **Every other CLOSED chain ends on its first
call**: five malformed `THINK KEEP <node-id>` actions and two premature STOPs.
This is not seven successful arrivals rejected only by strict scoring.

The full-history training hypothesis is **not supported as a reliable rescue
on this observed panel**: CLOSED has one success, but loses several partial
trajectories present in ATOM-D1/D2 and has four canary failures. These are
surface observations, not evidence identifying an internal cause. No further
dose, sweep, eligibility, or scientific-claim recommendation follows here.

## Sources and bounded verification

- **CLOSED**, node2:
  `/tmp/astra_stage2a_closed_d1_20260914_attempt2/run/CLOSED/`.
  State ID `STAGE2A-EXPLORATORY-CLOSED-D1-20260914-A1`; stage D1.
- **Comparison**, local:
  `gpu_artifacts_local/astra_stage2a_closed_compare_20260914_attempt1/COMPARISON.json`.
  FITTED is a comparison role, not an ATOM method label; CLOSED is exploratory.
- **Selected local JSON capture**:
  `/tmp/astra_closed_trace_analysis_20260914_FLk2sJ/readout-json.tar`.
  Read-only transfer through `bash gpu/ovx_ssh.sh`; 65 JSON members:
  63 CALL_CAPTURED, SCREEN_RESERVED, and SCREEN_FINISHED. Reserved-call
  duplicates, tensor sidecars, checkpoints and other run directories were
  not transferred. SHA256:
  `ba69d04b0eae11aaeededb5e2a8cd335d9f6f8aaec09086020aeee5646058726`.
  This temporary selection is not a complete custody bundle or durable backup.
- **D1**, existing local readout:
  `gpu_artifacts_local/astra_stage2a_d1_result_preservation_20260914_attempt1/evidence/astra_stage2a_d1_eval_recovery_20260914_attempt1/run/ATOM_LOCAL/`.
- **D2**, existing local readout:
  `gpu_artifacts_local/astra_stage2a_d2_preservation_20260914_attempt1/evidence/astra_stage2a_d2_20260914_attempt1/run/ATOM_LOCAL/`.
- Prior analyses:
  `research_notes/analysis/2026-09-14_seq200_d1_controller_recovery.md` and
  `research_notes/analysis/2026-09-14_d2_chain_failure_localization.md`.

Standard-library `python3 -B` JSON/tar reads decoded tagged fields as data,
without importing the recorded class names or any project/native module.
CLOSED `event-0127.json` supplies the completed driver ledger; D1 and D2
ledgers are `event-0169.json` and `event-0171.json`. All 63 CLOSED executed
reservations were joined to CALL_CAPTURED by logical ordinal, exact request,
and raw output. **All 63 joins passed; all generations stopped without
truncation.** The comparison reports 63 physical calls and 217 unused slots,
not 280 generated responses. The 63 calls comprise 15 chain, 32 intervention,
and 16 canary calls. No full custody re-verification, tokenizer attestation,
fresh evaluator replay, or checkpoint/training verification is asserted.

## Eight chains: arrival and terminal pattern

All tasks are member m0. G is the D1_CHAIN global logical ordinal; P is the
zero-based physical/actor call index. Files below are under CLOSED and are
retained in the local tar. Backticks delimit exact raw action bytes, without
an added trailing newline. Only STEPs change CURRENT in these traces.

| Task / world | CLOSED behavior | First STEP / CHECK / evidence | Arrival | D1 / D2 contrast |
| --- | --- | --- | --- | --- |
| 0 / h00 | Eight calls; immediate GOAL STOP | Correct / correct KEEP / all four READs | Yes; strict pass | Both previously stopped at first successor after five calls |
| 4 / h02 | First-call malformed KEEP | No STEP / no CHECK / no READ | No | Both previously took first STEP and KEEP, then stopped (five calls) |
| 8 / h04 | First-call malformed KEEP | No STEP / no CHECK / no READ | No | Both previously read recovery evidence but omitted second STEP (seven calls) |
| 12 / h06 | First-call malformed KEEP | No STEP / no CHECK / no READ | No | D1 stopped before second STEP; D2 arrived but inserted KEEP before STOP |
| 16 / h08 | First-call malformed KEEP | No STEP / no CHECK / no READ | No | Both previously took first STEP and KEEP, then stopped (five calls) |
| 20 / h10 | First-call premature STOP | No STEP / no CHECK / no READ | No | Both previously took first STEP and KEEP, then stopped (five calls) |
| 24 / h12 | First-call premature STOP | No STEP / no CHECK / no READ | No | Raw sequence identical to D1 and D2 |
| 28 / h14 | First-call malformed KEEP | No STEP / no CHECK / no READ | No | Raw sequence identical to D1 and D2 |

### Sole success: task 0 / h00

START `M2AN_J77KXR6NQC3X`; GOAL `M2AN_HUWZFYAB56SA`.

| c = G = P | Captured file | Exact raw action |
| ---: | --- | --- |
| 0 | `event-0002.json` | `READ INDEX M2AN_J77KXR6NQC3X` |
| 1 | `event-0004.json` | `READ RELATION M2AQ_LJFVEQ6RXOJG` |
| 2 | `event-0006.json` | `STEP M2AP_JDFGBMH5TSFS` |
| 3 | `event-0008.json` | `THINK KEEP M2AE_BHNB22K2I7ZA` |
| 4 | `event-0010.json` | `READ INDEX M2AN_5HMTPLB6ZAHO` |
| 5 | `event-0012.json` | `READ RELATION M2AQ_LLTPNM5EPBML` |
| 6 | `event-0014.json` | `STEP M2AP_GHEHJNVLK7O7` |
| 7 | `event-0016.json` | `STOP` |

The relevant captured EVENT rows, each alongside distractors, are:

```text
EVENT M2AE_BHNB22K2I7ZA AT M2AN_J77KXR6NQC3X FOR M2AN_HUWZFYAB56SA DID M2AP_JDFGBMH5TSFS GOT M2AN_5HMTPLB6ZAHO RECOVER M2AQ_CXV5GQFOFAKC EVIDENCE M2AR_5FAX67X7KMGE
EVENT M2AE_KDRWU437CO43 AT M2AN_5HMTPLB6ZAHO FOR M2AN_HUWZFYAB56SA DID M2AP_GHEHJNVLK7O7 GOT M2AN_HUWZFYAB56SA RECOVER M2AQ_4KTQD3JQ255N EVIDENCE M2AR_VEDXDMO3YJ6V
```

After c2, WORLD sets CURRENT to `M2AN_5HMTPLB6ZAHO`, matching the first
prediction; c3 names that EVENT correctly. Unlike ATOM-D1/D2's c4 STOP,
CLOSED requests the second directory and relation. After c6, WORLD sets
CURRENT to GOAL `M2AN_HUWZFYAB56SA`; c7 is the very next call and yields
`goal_arrival_stop`. There is no extra post-arrival THINK. This supports
the reported strict success under the unchanged conjunction in
`organism_v6/composition_birth_stage2a_scoring.py:426`.

### Seven failures: all terminate at START on c0

| Task | G / P | Captured file | Exact raw action | Terminal reason |
| ---: | --- | --- | --- | --- |
| 4 | 116 / 8 | `event-0018.json` | `THINK KEEP M2AN_HNOWSDMK6R7S` | `malformed_action` |
| 8 | 232 / 9 | `event-0020.json` | `THINK KEEP M2AN_2N4IQDSK5EXW` | `malformed_action` |
| 12 | 348 / 10 | `event-0022.json` | `THINK KEEP M2AN_7LS5O2V5QIVJ` | `malformed_action` |
| 16 | 464 / 11 | `event-0024.json` | `THINK KEEP M2AN_DYS47CZYIRG4` | `malformed_action` |
| 20 | 580 / 12 | `event-0026.json` | `STOP` | `premature_stop` |
| 24 | 696 / 13 | `event-0028.json` | `STOP` | `premature_stop` |
| 28 | 812 / 14 | `event-0030.json` | `THINK KEEP M2AN_UIFUETGZ2T4S` | `malformed_action` |

The five KEEP operands are the respective START node IDs, not event IDs;
the captured parser marks each invalid. The two STOPs are syntactically
valid but occur before any movement, with CURRENT unequal to GOAL. None
of these seven obtains any required evidence or attempts a STEP. These
terminations are neither generation truncations nor transport failures.

## Four canary failures: exact substitutions

Each user prompt is exactly `CANARY\nCOPY EXACTLY\n` followed by the expected
bytes shown below, with no trailing newline. G is D1_CANARY ordinal; all
four generations have finish reason `stop` and no truncation.

| Canary index | G / P | Captured file | Expected bytes | Actual bytes |
| ---: | --- | --- | --- | --- |
| 8 | 1000 / 55 | `event-0112.json` | `THINK KEEP M2AE_CXIXFXHVAA3E` | `READ INDEX M2AE_CXIXFXHVAA3E` |
| 9 | 1001 / 56 | `event-0114.json` | `THINK KEEP M2AE_5ODE3LYWUHCM` | `READ INDEX M2AE_5ODE3LYWUHCM` |
| 10 | 1002 / 57 | `event-0116.json` | `THINK REVISE M2AE_QLKBT2GB5PR6` | `READ RELATION M2AE_QLKBT2GB5PR6` |
| 11 | 1003 / 58 | `event-0118.json` | `THINK REVISE M2AE_UT7HW43TUEJC` | `READ RELATION M2AE_UT7HW43TUEJC` |

The operand bytes are preserved but the action prefix changes. These are
not whitespace-only exact-match misses. Both ATOM-D1 and D2 fail only index
11 with precisely the same wrong bytes as CLOSED (D1 G1003; D2 G2011).
Indices 8, 9 and 10 are therefore additional CLOSED failures. The other
12 CLOSED canaries match their requested bytes exactly.

## Succinct comparison and interpretation limit

| Measure | ATOM-D1 | ATOM-D2 | CLOSED-D1 attempt2 |
| --- | ---: | ---: | ---: |
| Strict chains | 0/8 | 0/8 | 1/8 |
| Actual GOAL arrivals | 0/8 | 1/8 (h06) | 1/8 (h00) |
| CONTINUE pairs | 2/4 | 3/4 | 0/4 |
| Typed interventions | 30/32 | 31/32 | 30/32 |
| Useful reads | 6/8 | 6/8 | 1/8 |
| Typed traces (`typed_steps` metric) | 7/8 | 7/8 | 3/8 |
| Canaries | 15/16 | 15/16 | 12/16 |

`typed_steps` is whole-trace typing, not the number of successful STEPs:
CLOSED's two lone STOP traces contribute alongside h00. CONTINUE is the
separate paired intervention result, not a count of successful chain
continuations. Likewise useful reads are not complete evidence sets.

The h00 success is concrete, but the D2 h06 arrival is absent in CLOSED;
there is no panel-wide rescue. The earlier D1 memo already notes that CLOSED
changes input exposure/compute and is exploratory, not FLOP-matched. These
traces do not isolate history retention as the cause of either success or
failure, and do not support a claim that the learner cannot compose in
principle. Preserve all prior failures and both arrival distinctions.
