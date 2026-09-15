# TERSE-BREADTH: completed A100 pairs; partial three-pair batch

Measured report/release time: 2026-09-15T01:17:23Z. Author reduction only;
reader VERIFIED=false, promotion=false. Original266 gate remains FAIL.

## Completed results

Same fixed128TRAIN/32held cohort,2868qualified terse native targets, original
batch5aac9c13737516146b7a4ed57961beb349c8198778040b36aeaa7eb3d3ea960e.
Both independent seeds at dose4 completed5760updates per arm, followed by
separate-process saved-adapter readouts. No baseline rerun.

| Seed | Arm | OWN_TEXT pairs | Goals | UNAVAILABLE pairs | W0 | W8 | Audit | Original | Previous fresh |
|---|---|---|---|---|---|---|---|---|---|
|7801|FULL|61/64|125/128|0/64|16/16|16/16|16/16|4/4|4/4|
|7801|OFF|8/64|51/128|0/64|16/16|16/16|16/16|2/4|2/4|
|7802|FULL|61/64|125/128|3/64|16/16|16/16|15/16|4/4|4/4|
|7802|OFF|7/64|55/128|0/64|16/16|16/16|16/16|2/4|2/4|

Unique frozen37ec baseline:8/64pairs,62/128goals; deterministic first-port:
0/64pairs. FULL-minus-OFF pair differences are+53/64 and+54/64. This supports
a strong finite aggregate contrast across two training seeds at the declared
128-world training width, conditional on this shared corpus/cohort/ancestry.
It is not independent-cohort replication, rich-row admission, or loop evidence.

**Both FULL prospective conjunctions FAIL:** only31/32held worlds have at
least one correct pair. Both fail
`ORCH-TERSE-BREADTH-20260914-V1-SHARD-7-BLOCK-0-PROBE-A`.
The aggregate pair threshold and old retention thresholds pass, but cannot
override the every-world gate. No checkpoint promotion or eligible-survivor
claim; no regeneration, seed selection, or undeclared256 escalation.

The prescribed third pair remains seed7801dose16 on node3physical6/7, not a
third independent seed. Watcher observation2026-09-15T01:17:04.350261UTC:
FULL4207/23040updates,OFF4252/23040updates, both nonterminal. Keep this pair
and its readouts unchanged; the full three-pair result is not yet terminal.
Dose16 additionally changes rehearsal and hardware relative to these A100fits.

## Evidence and reduction

Full immutable A100attempt2 archive, including states, native calls, baseline,
failures, guardians, corpus and results:
`gpu_artifacts_local/orch_terse_breadth_20260914_attempt1/terminal_a100.tar.gz`
SHA256 `461f291aac312782cf98a41aed9fac2a33d2b06f11c203b4e09d7296c895f818`.
Validated archive listing and extracted under sibling `terminal_a100/`;
existing bounded watcher will reuse this archive at final batch reduction.

`PARTIAL_A100_RESULT.json` binds all nine source RESULT files by SHA256 and
includes both conditions, retention, failed worlds and saved adapter hashes.
`gpu/orch_terse_breadth_partial.py` checks complete stages and chain exits,
matched batch/seed/dose/arm, ordered cohort/source signatures, row presentations,
full-reference loss denominators, saved-state loads, distinct process PIDs,
frozen-base flags and recomputed full-denominator gates. Four focused regression
tests PASS in `CPU_PARTIAL_REDUCTION.txt`. No native science driver was edited.
This is author verification, not a substitute for an independent reader.

## Explicit ownership release

**Release A100physical4,5,6,7 from TERSE-BREADTH at01:17:23UTC.**
All four fit/readout chains exited0; native/guardian PIDs are absent; terminal
evidence is archived. Exact indices/UUIDs:

-4: `GPU-31583768-d90f-520c-51ed-5dac761526d0`
-5: `GPU-c1650c7f-ac26-f1a0-2ab8-c7354a6f27c9`
-6: `GPU-6de3930d-104a-f969-7d36-009271368dd1`
-7: `GPU-f0405a96-813d-7ac7-d641-3ec31d103037`

`A100_RELEASE_SCAN_20260915.json` and `A100_RELEASE_RECHECK_20260915.json`
preserve failed clearance attempts: no owners, but unreadable transient SSH
environments prevented clearance. No PID was killed or exception added.
`A100_RELEASE_DETACHED_20260915.json` records the unchanged scanner running
after its initiating SSH connection closed. At2026-09-15T01:16:57.542710UTC,
all four scans returned0/clear=true, owners=[],unresolved=[] with all-GPU
UUID and compute tables. This is a time-bound release receipt; the next owner
must still perform its own fresh prelaunch checks. No next experiment launched.

Retain node3physical6/7 ownership and watcher2161684 through their original
terminal readouts. Partial release is not batch retirement or a SEQ request.
