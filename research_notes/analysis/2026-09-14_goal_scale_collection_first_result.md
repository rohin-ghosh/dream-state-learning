# SEQ258 — eight-shard scale collection, failure-inclusive terminal result

Status: EXECUTED, original full-corpus admission FAILED. All eight guardians
are terminal; no fit was launched. This does not establish a failure of the
pending12384-update fit, which remains unmeasured. Independent review pending.

Source`ff1af2c37003fd4f6d38ecbe7660fd94744c0e31`; protocol SHA
`dd1d078a01d9f547219afd23790c467ca0ccb413f3148a2af9b963b63e652f24`.
Node3 root`/tmp/astra_goal_scale_20260914_attempt1`, shards0–7 onGPU0–7,
guardians79201,79202,79204,79206,79208,79210,79212,79214. Requests18:16:32UTC,
native guardian starts18:16:41UTC on2026-09-14. Four source-failed shards
stopped after EXPOSE; four completed teaching and baseline by18:26:36UTC.
No process was killed by Main. Terminal capsule copied and verified on/data:
`gpu_artifacts_local/astra_goal_scale_terminal_20260914_attempt1/extracted`,
archive SHA`c57a87efedd39b84ff0c316a2cb3d23e4dc26f70c2d4eae44d45409d45eaea0c`.

## Source formation versus corpus admission

All320 ROUTEs committed and produced actual public receipts. Across80worlds,
the child attempted320EVENT records;316passed,4failed exact identifier checks.
My earlier18:19–18:21 progress shorthand said320actualEVENTs: that conflated
attempts with admitted records. Correct count is316valid/320attempted; all raw
outputs remain recorded. This correction does not alter any native result.

| Shard | Valid EVENTs | TEACH status | Emitted TRAIN rows | Baseline calls |
|---|---:|---|---:|---:|
|0|39/40|not attempted: invalid source|0|0|
|1|39/40|not attempted: invalid source|0|0|
|2|40/40|all32episodes complete|192|285|
|3|40/40|all32episodes complete|192|277|
|4|39/40|not attempted: invalid source|0|0|
|5|40/40|all32episodes complete|192|273|
|6|39/40|not attempted: invalid source|0|0|
|7|40/40|31/32episodes complete|0 under frozen all-or-none rule|276|

The four source failures are literal child copying errors, not truncation or
a manufactured parser problem: shard0 source node loses a character;
shard1 receipt loses one repeated`3`;shard4 receipt ends`7`instead of`B`;
shard6 receipt omits final`Q`. Three failures occur in TRAINworlds and one in
a PROBEworld. Correct ROUTE receipts precede every bad EVENT. No canonical
expected string was substituted for the child's emitted memory.

Four shards made768guided calls,127/128attempted tasks succeeded;128other
planned TRAINtasks were not attempted due source admission. Shard7block2A
task2 reads four actual records but commits the wrong first branch, then emits
an invalid final ROUTE. This is a guided-action failure distinct from copying.
The original helper suppresses all192rows of that shard. Only576rows across
three shards are emitted, not the required1536across eight; no subset is
silently used for the frozen scale fit. Raw successful/failed captures survive.

## Unassisted baseline coverage

| Shard | TRAIN goals / pairs | PROBE OWN_TEXT goals / pairs | UNAVAILABLE goals / pairs |
|---|---|---|---|
|2|18/32;4/16|5/8;1/4|0/8;0/4|
|3|18/32;4/16|3/8;0/4|1/8;0/4|
|5|15/32;3/16|4/8;0/4|0/8;0/4|
|7|15/32;4/16|4/8;0/4|0/8;0/4|

Observed totals:TRAIN66/128goals,15/64pairs;PROBE OWN_TEXT16/32goals,1/16pairs;
UNAVAILABLE1/32goals,0/16pairs. These cover only four of eight shards. Planned
full-panel denominators are TRAIN256goals/128pairs and PROBE64goals/32pairs
per condition. The remaining cases are unmeasured, not zero and not removed
from coverage reporting. Source-based attrition limits interpretation of
observed-shard aggregates; do not present1/16as a completed whole-panel rate.

## Measured cost, decision and next work

Native totals:EXPOSE640calls/1435.159010s;TEACH768/737.365429s;
BASELINE1111/886.366832s. Total2519calls/3058.891271phase-seconds,
0.849692allocated A40hours across eight parallel GPUs. This is neither the
wall-clock duration nor measured GPU utilization. All executed stages are
readonly37ec, zero updates; state/native-error claims require receipt checks,
and independent review is not replaced by this primary reduction.

The original all-eight corpus recipe closes failed; pending scale training is
blocked, not secretly reduced to successful shards. A new separately declared
<=8call actual-child correction diagnostic examines the four literal copy
failures using only original public receipts and actual bad responses. It
does not overwrite this source or promote a corrected artifact automatically.
The rich collection's candidate-retention policy was revised prospectively
before any rich GPU calls, with matched forms and all attempted denominators,
to avoid discarding valid candidates because another episode failed. That
does not retroactively relax this failed protocol. Breadth fits continue;
neither this corpus failure nor its repair is a reason to stop them.
