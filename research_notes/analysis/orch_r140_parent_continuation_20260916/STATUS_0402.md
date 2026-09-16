# Saved-state Astra handoffs — 2026-09-16 04:02 UTC

**F1, F2 and F4 are running with prospective Astra parent consumers/brokers.**
Exact PID/start-ticks/command-hash checks at04:02:30UTC confirm native actors
F12664733, F22627464, F42957698 and A24156720 remain alive. Historical Fable
turns retain their attribution; historical MISSING/refused requests were not
resent, re-enqueued, deleted or relabelled.

## Actual delivery and state continuity

- **F1:** saved C55→C56 handoff preserves its adapter, AdamW, CPU/CUDA RNG and
  history. Astra SILENT disposition has actually been consumed; silence is not
  substantive guidance. The independent03:34 audit verifies continuing updates.
- **F2:** saved C45→C46 handoff preserves the learning state. Astra C46E0/E1
  guidance is verified inside a completed C47 native input. At04:02 counters
  show17,436 committed optimizer steps, versus16,460 in the03:34 audit.
- **F4:** resumed exact C112/N04456 ungenerated frontier as freshN04457, with
  all32 preceding native responses and32 environment receipts rehydrated, not
  redispatched. C112 completed with its two outcomes and updated carry; the
  same actor advances through C114. Frozen-gen1 LoRA/history are preserved.
  F4 was and remains elicitation-only:0 optimizer steps, no restored live RNG
  claimed. The archived optimizer/RNG checkpoint was not rewritten.
- **A2:** no restart by this work. At04:02 counters show17,487 optimizer steps
  versus16,509 in the03:34 audit; native1064,parent114. Four actual Astra guidance
  injections are independently verified in that earlier audit.

F4 fresh **P0325 returned COMPLETE Astra at03:59:37.775UTC**. Its20-word guidance
is present verbatim in the actual input of completed TRAIN callN04500,C114.
Response SHA256 `4ac38119ed0fbd02ba8e6d07ff1e89374dc482cba04761c7eb2bdb487953cee8`;
native-call SHA256 `4eb2d47d452e84f4c986bceb3c074915c4274e325a64baad3469a4391a1c3a88`.
Compact proof: `F4_DELIVERY_P0325.json`. No raw guidance/transcript is copied here.

The three-phase broker fix replaced only broker2314779 with2507071 after
natural lock release. Existing producer phases experience/open_turn/
presleep_metacognition now reach the same Astra transport. Prompt/model/caps
and floor324 are unchanged. P0325 was unclaimed and undispatched when admitted;
it was not a retry of a refusal or MISSING request. New publication SHA256:
`fa24c246067a1e58992e56142416ee8f09cba83b2cdc699cc932d194ff7b6cda`.

F4 timer2957571/current callback verifies actual actor2957698. Original FINAL8
at06:00UTC, evaluation end06:20, TRAIN end22:02/hard wall22:04 September16UTC
remain intact. No extra FINAL call, sealed-input exposure or evaluation replay.

## Rolling-hour queue publications

Window **03:02:06.400–04:02:06.400UTC**, using response finished timestamps.
These are publications, not native applied counts. Zero publications do not
prove a lane is alive or dead. Missing slots without a response are not included.
Hashes for every counted response are in `HOURLY_PUBLICATIONS_0403.json` (its
embedded observation timestamp, not its report filename, defines the window).

| Lane | COMPLETE | SILENT | MISSING |
|---|---:|---:|---:|
| F1 |0|4|0|
| F2 |8|0|0|
| F3 |0|0|0|
| F4 |1|0|1|
| A1 |0|5|0|
| A2 |3|3|0|
| A3 |0|0|0|
| A4 |0|0|0|

All nonmissing model-attributed publications in this window are Astra. F4's
historical P0323 MISSING remains in-window and unchanged. Native uptake is
proved separately above and in `../orch_r140_delivery_20260916/SUMMARY.md`.
No fleet-saturation claim is made from this table.

## Validation and scientific scope

57 author tests pass together (continuation, normalizer, original timer);
13 broker-phase tests pass in a separate fresh process. Staged tests:21
continuation,14 normalizer,13 broker-phase PASS. Running all four modules in
one interpreter raises one `isolated_A4_import` setup error after the57 tests;
this pinned-runtime isolation check was not weakened and that combined run is
not claimed green. Independent normalizer review PASS; CPU integration and
actual completed-call evidence agree on normalized input recording.

These receipts establish continuity, running code and parent-guidance injection,
not improved thinking, retained learning or the R121 four-condition result.
The research goal remains active/unproven; Level1 paper scope is unchanged.
