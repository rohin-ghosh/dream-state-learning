# QUALITY_BREADTH attempt2 — terminal result and handoff

[Builder/Nash] September 14, 2026. Both fixed fits and their original automatic,
fresh-process AFTERs completed. No technical FAILED receipt or guardian abort,
no repeat fit, no duplicate AFTER, and no budget extension.

**Selected comparison: the actual 944-call matched baseline is 33/64 PROBE
goals and 2/32 strict opposite-goal pairs. The legacy P44 0/4 baseline and its
prediction are a separate experiment, not this comparator. All 32 pairs stay
in the denominator, including the source-defective PROBE world.**

**Outcome: strong incremental primary evidence in this single exposed-DEV
comparison, but the frozen engineering conjunction FAILS.** FULL reaches
30/32 pairs versus 1/32 loss-off and 2/32 baseline, with all retention thresholds
met. It has no correct pair in one of the 16 PROBE worlds, failing the required
at-least-one-pair-in-every-world condition. No automatic promotion, extra seed,
new fit, source correction, or retrospective threshold change follows.

## Fixed endpoints

| Metric | Matched37ec baseline | FULL_TARGET | NEW_TRAJECTORY_LOSS_OFF |
|---|---:|---:|---:|
| PROBE OWN_TEXT strict pairs | 2/32 | 30/32 | 1/32 |
| PROBE OWN_TEXT individual goals | 33/64 | 62/64 | 26/64 |
| PROBE worlds with at least one pair | 2/16 | 15/16 | 1/16 |
| PROBE UNAVAILABLE strict pairs | 0/32 | 0/32 | 0/32 |
| PROBE UNAVAILABLE individual goals | 3/64 | 23/64 | 0/64 |
| Four fixed TRAIN worlds, pairs | 2/8 | 8/8 | 1/8 |
| Four fixed TRAIN worlds, goals | 7/16 | 16/16 | 8/16 |
| Old memory W0 | 16/16 | 16/16 | 16/16 |
| Old memory W8 | 16/16 | 16/16 | 16/16 |
| Held audit | 16/16 | 16/16 | 16/16 |
| Original taught graph OWN_TEXT | 3/4 | 4/4 | 2/4 |
| Previous fresh graph OWN_TEXT | 3/4 | 4/4 | 2/4 |
| Full engineering conjunction | FAIL | FAIL: world coverage | FAIL |

Pairs require both opposite-goal tasks in the same display order to succeed,
distinct source-correct first ports, and two legal committed routes each:
task indexes (0,2) and (1,3). Individual success alone is insufficient. TRAIN
generation covers only the prospectively fixed shard0/1/4/6 world0 diagnostics,
not all 61 source-eligible training worlds. The offline deterministic
first-current-displayed-port/no-read reference gives 32/64 goals and 0/32
pairs for the same PROBE tasks; it uses zero native calls.

FULL exceeds baseline by 28/32 pairs and loss-off by 29/32 pairs. This supports
a contribution from the new trajectory-label supervision beyond matched old-row
rehearsal to text-supported opposite-goal behavior on these held-identifier DEV
worlds. It does not establish population efficacy, independent development,
general planning, H1/H2, clean lineage, or new parametric event acquisition.
The quality corpus is outcome-filtered and adaptively selected; this is not a
dose-isolated contrast with SEQ260 or the blocked12384-update scale experiment.

## The failed world and unavailable control

FULL gets 2/2 pairs in each of the other 15 PROBE worlds, but 0/2 in
`ASTRA-GOALSCALE-20260914-V1-SHARD-1-BLOCK-0-PROBE-A`. This is the retained world
whose actual source EVENT at `E_W5YA3H6TNF` was invalid. OWN_TEXT returns three
actual accepted EVENT strings and literal `MEMORY UNAVAILABLE` at that address,
identically for baseline and both arms. No canonical substitute or correction
is supplied, and no task/world is removed from scoring.

All four FULL tasks there make four actual reads. Tasks0/1 reach their goal.
Tasks2/3 instead take `P_VD4QGEZVKT` then `P_7QV4OUBPN2`, the same branch as
tasks0/1, ending at `N_QXTYUSWLOZ` rather than required `N_7P5OYA74NA`.
The expected first port for tasks2/3 is `P_3TILLNKUCR`. Both wrong paths are
legal but terminate at a dead end for their requested goal. This co-occurs
with the missing source; no correction counterfactual was run, so missing
text is not experimentally proven to be the sole cause. The world-coverage
failure remains a failure, not a post-hoc 30/30 success.

FULL OWN_TEXT uses384 PROBE actor calls,256reads,128legal route entries:
62 reached_goal and two dead_end. Baseline has33 reached_goal,25 dead_end,
four invalid_route and two invalid_command. Loss-off has26 reached_goal,
23 dead_end,14 invalid_route and one invalid_command; all are retained.

FULL UNAVAILABLE's23/64 goals are not opposite-goal success: every one of its
32 matched pairs selects the same first port for both goals, and all32 pairs
fail. All256 memory responses are literal unavailable; no text fallback is
present. FULL ends23 reached_goal,24 dead_end,17 duplicate_address; baseline
ends3 reached_goal,1 dead_end,60 duplicate_address; loss-off ends64
duplicate_address. The higher individual rate is consistent with improved
legal execution without opposite-goal discrimination, not evidence of new
parametric memory. No null-distribution/significance claim is made.

## Actual inputs, supervision and state joins

Source `7f9d4251ae1ff4c5ff9138adf267d081fffa6331`; protocol SHA256
`1683ca250ef6f95cb41c7972685279a07ec3693fb9ab34e049ffb975e8eb96e9`.
The actual assembly contains1452 targets (756 reused +696 newly collected),
121 admitted pairs,61 source-eligible of64 planned TRAIN worlds. Three
invalid-source TRAIN worlds and the unsuccessful reused opposite-goal pair
remain recorded exclusions, not repaired evidence. No PROBE row is trained.

Each arm starts37ec, uses frozen Qwen2.5-7B, rank8, actual dropout0.05, seed0,
fresh AdamW3e-5, batch4, exactly2928updates over identical1674rows. The
128memory/20cue/62audit/12old-trajectory/1452new-trajectory order, original222
encodings, full EOT sequences and explicit schedule are preserved. Saved
reference inputs/masks/rows match across arms; only new indexes222:1674 have
all labels masked in loss-off. Per-batch active/reference normalization and
finite logged losses were checked across all2928updates in each arm.

| Dose | FULL | LOSS_OFF |
|---|---:|---:|
| Updates | 2928 | 2928 |
| Full reference supervised labels | 238274 | 238274 |
| Active supervised labels | 238274 | 173814 |
| Nonpadding full-input token presentations | 4477997 | 4477997 |
| Memory row presentations | 2928 | 2928 |
| Cue/audit row presentations | 2928 | 2928 |
| Old trajectory presentations | 48 | 48 |
| New trajectory presentations | 5808 | 5808 (labels off) |

All1464trajectory rows occur four times. The active-label difference is64460,
not a claim of equal active dose. The old12 trajectories remain supervised in
both arms, including their positions in trajectory slots2/3.

Initial state:
`37ec37884e4b0b679edd1dba1be1dec3474589e992649f3a33e7e3b1ec78b8c0`.
FULL saved/reloaded/final state:
`e226cea230b4b970cd5a94cb2b853350aa8bfb95ab4ba69cba3e78ebdd0ad3bf`.
Loss-off saved/reloaded/final state:
`4f0dccf5b7cf37b872eafc3a50990e0cdfda027fb0140f0aad999f27606e4ee3`.
Both AFTERs bind their own train RESULT hash and the same baseline RESULT hash.
Baseline starts/ends37ec; both AFTERs start/end their own saved state. Native
receipts attest frozen-base and adapter-file checks; terminal inventory and
file hashes, state receipts, shared material/source/readout/helper/runtime
bindings and saved adapter bytes all verify. Reduction does not load a model
or pretend to independently recompute an in-memory tensor state.

| Receipt | SHA256 |
|---|---|
| Baseline RESULT | c2fe5b4735ea7252fff27e7ea777093e798df882f57262ab0391ad91b6b671a2 |
| FULL TRAIN RESULT | 6e01a238a43aa521c93e650a271f459bc4a0f0fc2a0d2b44e7ea77b452f81283 |
| FULL AFTER RESULT | 53756fd01c72648d80db8f9bd075fadc578a03c8a8255373ade6b63d63cc98cd |
| LOSS_OFF TRAIN RESULT | b7a05eb433d013405df2f4d3a3437147f59ab61876bcf7d5c69585d8b509f72b |
| LOSS_OFF AFTER RESULT | 6f50d5bafb5cb32f182dede709da095834214cec0fd6f04b7a78cbf1dca6d440 |

## Native execution, measured costs and GPU release

All times September14UTC. Guardians started19:48:24. Original deadline
23:54:24 remained unchanged. Existing guards, not new orchestration, started
exactly one fresh AFTER per completed fit.

| Phase | Native PID | Actual start | Result finish | Assigned wall seconds | Calls |
|---|---:|---|---|---:|---:|
| Shared baseline GPU2 | 86114 | 19:48:25.040 | 19:59:05.032 | 639.992 | 944 |
| FULL TRAIN GPU0 | 86119 | 19:48:25.052 | 21:21:30.364 | 5585.312 | 0 |
| FULL AFTER GPU0 | 91024 | 21:21:31.451 | 21:32:18.474 | 647.024 | 960 |
| LOSS_OFF TRAIN GPU1 | 86109 | 19:48:25.030 | 21:21:45.738 | 5600.709 | 0 |
| LOSS_OFF AFTER GPU1 | 91067 | 21:21:46.911 | 21:32:32.274 | 645.363 | 932 |

Measured optimizer-loop times:5463.162/5478.447seconds. Summed native phase
assigned wall is13118.401seconds = **3.644GPU-hours**, including the baseline
and preparation/replay/model-loading within each phase, excluding previous
corpus acquisition and external CPU staging. Guardian spans are6235/6249seconds
for FULL/loss-off and641seconds for baseline, totaling3.646GPU-hours. These
are assigned-time measures, not kernel-utilization estimates or dollar costs;
the reservation ceiling was9.3GPU-hours. Both fits used about40504MiB; AFTERs
about15560MiB at observed samples.

Total actual inference:2836calls,35579generated tokens,1076178prompt-token
occurrences from recorded native receipts. No new training generation calls.
FULL reaches, but does not exceed, the960call ceiling; loss-off932 and
baseline944 retain all cases despite shorter/invalid episodes. No cap-hit
failure occurred.

FULL guardian86063 completed21:32:19; loss-off guardian86064 completed21:32:33.
The final monitoring sample21:33:03 shows no guardian/native or GPU compute
process. **Node3 GPU0 and GPU1 are released**, confirmed by the existing exact
physical+CVD scanner at21:33:42.801 and21:33:43.050 respectively: owners=[],
unresolved=[], compute_apps empty, clear=true. GPU UUIDs:
`GPU-0ee6f753-c61e-e18a-8aea-acccd3042939` and
`GPU-71e5a3e2-e9c8-5caf-70d8-73794ac34821`. No processes were killed.

An initial foreground release scan conservatively returned clear=false for
its transient SSH service's unreadable environment. That failed scan is kept.
The detached delayed read-only scan, after that SSH session exited, passed
without adding service exceptions or weakening the scanner. GPU2 had already
been released after the19:59:05 baseline completion.

## Tests, verification and preserved deviations

Prelaunch published-source CPU command:
`PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest tests.test_astra_goal_quality_train -q`
— **9 tests PASS,57.922seconds**, recorded before launch:

- `test_exact_2928_schedule_four_presentations_masks_and_denominator`
- `test_prepare_exact_rows_no_model_and_parent_or_probe_drift_rejected`
- `test_partial_probe_scoring_preserves_unavailable_and_full_denominators`
- `test_saved_train_receipt_state_masks_schedule_and_nonfinite_guard`
- `test_baseline_native_replay_and_fresh_state_reload_cap`
- `test_assembly_requires_all_original_native_and_four_unit_captures`
- `test_actual_target_encoding_masks_history_eot_and_no_truncation`
- `test_protocol_guard_and_no_ml_import`
- `test_train_enters_without_baseline_results_but_after_requires_them`

Actual2104capture source replay PASS19.10seconds; original input staging
429files/495950377bytes hash-verified without model copy; original node3
parent validation PASS15.26seconds; full native CPU preparation
PREPARED_NO_MODEL PASS51.439852seconds,1674rows/1452actual/0PROBE, zero fits,
updates and model calls. Independent full baseline replay PASS52.058seconds
at20:21:27,944saved calls and exact bindings. It was not repeated in terminal
reduction; both actual AFTERs also performed their required native baseline
and own-training receipt checks before loading their own saved actor.

Terminal CPU reduction verifies2836call files and their inventories, joins
every goal trace to actual prompt/response captures, replays/rescores288
TRAIN/PROBE AFTER episodes using immutable published pure helpers, verifies
all fixed task/goal pairs and common actual read stores, and checks2928batch
records per arm without tokenization or model loading. Full taskwise routes,
commands, failures and terminal causes are in REDUCTION.json and raw episodes.
Retention results remain tied to hashed native outputs. Two author-side
reducer-only construction errors (tuple/list recipe comparison and duplicate
task_index keyword) were corrected before its successful run; neither changed
experiment code, native evidence or metrics. No technical native failure is
being relabeled.

**Logging-order deviation remains:** prelaunch COORDINATION publication failed
its clean-file check amid Main's concurrent edits, but the original enclosing
shell was not fail-fast and still launched at19:48:24. There was no successful
durable prelaunch notebook entry for those requests. This is not backdated or
called a passed logging gate. CPU/source/admission checks genuinely preceded
work. The deviation and actual PIDs were disclosed in EXECUTION/a6637880;
Main acknowledged and instructed preserving the jobs. Subsequent monitoring
never restarted them or changed their source. No new scientific launch follows
this result; future orchestration must stop if logging/publication fails.

## Evidence locations and final ownership

Remote originals remain untouched at
`/tmp/astra_goal_quality_train_20260914_attempt2` on node3. The immutable source
archive and old attempt1 sequential plan/staging remain preserved. Terminal
archive was built under node3 `/localhome` and copied only onto the VM `/data`
filesystem, not VM root `/tmp`; no model/ancestor forests were recopied.

Local terminal capsule:
`gpu_artifacts_local/astra_goal_quality_train_terminal_20260914_attempt2/`.
Archive `quality_attempt2_terminal.tar.gz`,186969188bytes, SHA256
`0152cafb69aa7715b5f4fbb15caa4954f03c62c1f3c063883ed9c17c9aa00deb`.
All9315inventory entries match before/after remote packaging and local
extraction; no symlinks in the archive. Inventory SHA256
`3f89c5379a5d8c81ce0bb828e8b992725f587d125e92feee4a1a044cc8cc2287`.
Raw tree: `extracted/astra_goal_quality_train_20260914_attempt2/`.

This run's `FINAL_CHECKS.json` publishes the compact machine-readable metrics,
per-world counts, costs, receipt/state joins, release and validation checks;
the terminal capsule's `REDUCTION.json` includes every taskwise diagnostic.
The owned `reduce_terminal.py` and spaced monitor log preserve the reduction
procedure and observed automatic transitions. Original run bytes and failed
source/episode cases are retained. This completes ownership of the two fits,
automatic AFTERs and reduction; released GPUs are not an authorization to
launch another experiment. Main's outcome-contingent decision note is separate.
