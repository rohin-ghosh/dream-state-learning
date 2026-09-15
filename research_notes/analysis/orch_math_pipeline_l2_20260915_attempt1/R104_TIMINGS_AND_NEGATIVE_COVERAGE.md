# R104 observed timing and negative-example audit

**05:20Z update:** CREATIVE C1 fresh8held test is now COMPLETE+AFTER,
finished05:19:24.090480Z. Readout214.260878s; complete experience→sleep→test
cycle818.188570s (13m38s). MICRO and CREATIVE C2 REQUESTs both exist; no
in-flight schedule change. CREATIVE readout COMPLETE SHA
`bc6dbf4d4d0866f5291a645e2729baaf9e49031b91c80e93a095e22ed842a993`,
AFTER SHA `d06984ebd1c402c000d699b5c9b597e591f10cbbeecfd19822d6d84a76187d90`.
The table preserves the earlier timestamped partial observation below.

Observation:2026-09-15T05:17:51.514780Z. No live source/schedule/mix changed.
Native CPU-only audit: `R104_COVERAGE_TIMING_VERIFIED.json`;52CPUtests PASS.

| C1 lane / schedule | Original gen s | Parent queue s (provider HTTP wall s) | Reflections s | Sleep envelope s | Experience through saved sleep s | Readout s / responses | Full cycle wall s |
|---|---:|---:|---:|---:|---:|---|---:|
| Prior GUIDED,8episodes |111.438|185.943 (unknown)|832.945|1477.989|1846.473|329.501 /56COMPLETE|2184.250COMPLETE|
| Prior OFF,8episodes |110.779|0 (none)|66.998|702.878|882.976|301.601 /56COMPLETE|1204.565COMPLETE|
| R102 MICRO5,2episodes |13.586|96.623 (54.247)|19.665|291.868|473.009|211.654 /8COMPLETE|698.890COMPLETE|
| R102 CREATIVE7,2episodes |13.899|200.373 (66.440)|33.602|307.022|592.585|121.685elapsed /3responses,4reservations|725.613elapsed PARTIAL|

MICRO sleep550updates COMPLETE05:13:38.917886Z; fresh eight-held readout
COMPLETE05:17:24.798829Z with AFTER verified. C2 experience has started.
CREATIVE sleep554updates COMPLETE05:15:38.486826Z with AFTER; readout still
partial at the observation. No completed C1 native phase failed.

Experience times begin with native REQUEST, including approximately69seconds
load-to-first-generation, then original generation, parent queue/transport,
reflection/writes/rehearsal/save/base verification. Sleep envelope starts at
first reflection: it INCLUDES reflection generation, writes,222legacy rows,
save and bookkeeping. Do not add it to the reflection column as disjoint time.
Parent HTTP wall overlaps queue wall and is not pure provider compute. Actual
optimizer-only duration is UNKNOWN. Full cycle includes interprocess/admission
gaps. Old56readouts included8held+48retention/audit; new nonterminal readouts
are8held. These are different schedules/providers/cohorts, not a controlled
speedup estimate. Actual MICRO full cycle is11m39s, NOT2.5h.

## Actual source coverage and objective

Both R102 C1 cohorts happened to have2correct originals and0negative outcomes:
do not claim an observed negative example in either new C1. Four rows/lane
were audited against actual CALL SHA/target SHA, outcome, masked prefix, token
labels, and exact LOSSES presentation counts. MICRO164original+164reflection+
222legacy updates=550. CREATIVE166original+166reflection+222legacy=554.
Current old-rowmix is preserved, not faded in place.

Earlier completed paired GUIDED/OFF C1 each contains ONE actual INCORRECT
episode among8. Its past-attempt AND own-reflection rows are retained as
INCORRECT: GUIDED68presentations EACH, OFF67presentations EACH, with verified
source hashes/masks and LOSSES counts. No failure was discarded, relabelled
correct, or used to stop/deallocate a lane. Missing responses cannot supply
fabricated utterance targets; coverage requires an actual own reflection.

Objective: ordinary positive causal CE on historical child targets conditioned
on explicit outcome and non-endorsement context. The failed trace is a negative
example **semantically**, not a negative-gradient target. This trains accurate
recording of a failed attempt, NOT unlikelihood suppression of its tokens;
useful behavioral learning is an empirical question. Teacher guidance affects
reflection elicitation only, not sleep targets/prefixes. None of this changes
the base, H1/H2, epoch policy, shared control count, or L2/L1 quarantine.

The first exploratory audit output `R104_COVERAGE_TIMING_20260915T0517.json`
is superseded: its CPU reducer incorrectly looked up GUIDED parent latency
for OFF. The verified output fixes arm-specific lookup, refuses to label legacy
CLI latency as HTTP compute, and passes a dedicated regression test. No native
process, call, transcript, or experiment source changed for this audit repair.
