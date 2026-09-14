# QUALITY_BREADTH execution record

## [Builder/Nash] 2026-09-14 19:49:36 UTC — three bounded native processes live

Run /tmp/astra_goal_quality_train_20260914_attempt2 on node3.
Source7f9d4251ae1ff4c5ff9138adf267d081fffa6331; source archive SHA256
 a4507d07b2ccc7473048ef06a266463eee9b4228911a83043cf9a152d61da8e5.
Protocol1683ca250ef6f95cb41c7972685279a07ec3693fb9ab34e049ffb975e8eb96e9.
Main confirmed GPU2 baseline reservation and GPU0/1 paired fits. This is the
1452-target/2928-update diagnostic, NOT the blocked12384-update scale fit.

NineCPUtests57.922sPASS; actual2104capture source replay19.10sPASS; original
parent input staging429files495950377bytes verified on node3, no model copy.
Full native PREPARED_NO_MODEL completed BEFORE launches in51.439851668s,
1674rows/1452actualTRAIN/0PROBE,fits0/updates0/modelcalls0. Hash-bound receipts
and exact prepare command are preserved locally/remotely.

All guard physical+CVD admissions passed. Recorded starts19:48:24UTC:

| Role | GPU | Guardian PID | Native Python PID |
|---|---:|---:|---:|
| BASELINE | 2 | 86062 | 86114 |
| FULL_TARGET TRAIN | 0 | 86063 | 86119 |
| NEW_TRAJECTORY_LOSS_OFF TRAIN | 1 | 86064 | 86109 |

Native Python processes confirmed alive at19:49:12UTC; no FAILED receipts.
They initially replay source inputs, then load their assigned actors. These
PIDs do not themselves prove a completed baseline or optimizer update.

### Logging deviation (not backdated)

The intended prelaunch COORDINATION append/commit was prevented because that
shared file had concurrent uncommitted edits. The conflict check correctly
refused to commit another worker's changes, but the enclosing shell command
was not fail-fast and proceeded to request the guards at19:48:24UTC. Therefore
no durable [Builder/Nash] prelaunch entry preceded these guard requests. This
is recorded as a logging-order error, NOT retrospectively called a passed
prelaunch logging check. Main's published protocol authorization, accepted
CPU/source tests, actual CPU preparation and physical admission preceded native
work; those receipts are not altered. This owned execution log avoids shared
file conflicts. Future phase-launch entries must fail closed if logging fails.
No run is restarted, extended or relabeled to conceal this deviation.

### Fixed boundaries and monitoring

TRAIN2928 updates, seed0, rank8, AdamW3e-5,batch4; all1464 trajectories have
four presentations (48old/5808new). Only new222:end labels masked in LOSS_OFF,
with shared full-reference denominator. TRAIN never reads baseline scores.
AFTER requires the complete matched baseline and state/source/task joins.
Baseline guardian ceiling3960s; each fit/readout branch14760s. No extensions,
repeat fits or unowned GPU kills. Source/phase commands, stage timeout PIDs,
resource scans and deadlines are in each branch's launch directory. Further
status will report actual token/call/update counts and saved-state joins, not
inferred results or promotion. Other workers and rich branches are untouched.

## [Builder/Nash] 2026-09-14 19:50:19 UTC — actual GPU work confirmed

Source7f9d4251 is published (Main reports push via7e53aa6b). Node3 GPU0/FULL
native86119 and GPU1/LOSS_OFF native86109 each completed19/2928updates,
31.14/31.26fit seconds, using35788MiB each. GPU2 baseline native86114 has71
actual calls,15560MiB; all three guardians remain alive, no FAILED receipts.
These are actual jobs, not just reservations. Staging is complete; full native
CPU preparation was51.44sPASS. The amended launch plan is attempt2/LAUNCH_PLAN.md;
attempt1's sequential plan and original source staging remain preserved.

Prospective AFTER phase notice: each already-running fit guard is authorized
to start exactly one fresh readonly AFTER after its fixed2928-update TRAIN
completes, only if the shared baseline has a COMPLETE receipt. Each AFTER
retains its3600s ceiling within the original14760s guardian deadline; no budget
extension or repeat fit. Its actual native PID/start and saved-state join will
be recorded once it starts. No current baseline score is used to change TRAIN.

## [Builder/Nash] 2026-09-14 20:17:33 UTC — baseline complete, both fits progressing

Direct node3 observation: status_20260914T201732Z.json. BASELINE RESULT is
COMPLETE, fits0/updates0,944modelcalls and944actual CALL files; completion
marker19:59:05UTC. RESULT SHA256:
c2fe5b4735ea7252fff27e7ea777093e798df882f57262ab0391ad91b6b671a2.
Loaded/final adapter states both equal37ec37884e4b0b679edd1dba1be1dec3474589e992649f3a33e7e3b1ec78b8c0;
frozen_base_unchanged=true. Stored primary:2/32PROBE pairs,33/64goals.
This is receipt/hash verification, not yet independent full read_baseline
replay; AFTER performs that required join. Guardian86062/native86114 are gone
and the physical GPU process query contains only the two fit workers: GPU2
is released.

FULL_TARGET guardian86063/native86119 is live at893/2928updates;
LOSS_OFF guardian86064/native86109 is live at890/2928updates.
Neither arm has a train RESULT/FAILED receipt or an AFTER directory yet.
Latest fit elapsed1665.875/1664.667seconds; last200-update rates1.877799/
1.882594seconds per update imply TRAIN completion about21:21:15/21:21:30UTC
(63.7/63.9minutes remaining at observation), conditional on maintained rate.
Estimates exclude save/reload and AFTER, and are not predictions of success.
Both workers use40504MiB; GPU0/1 remain assigned. Original branch deadline
23:54:24UTC, source, jobs and budgets unchanged. No restart or new launch.
The disclosed prelaunch logging-order deviation remains intact.

## [Builder/Nash] 2026-09-14 20:21:40 UTC — full baseline replay PASS

Independent CPU-only load_inputs plus read_baseline completed20:21:27UTC in
52.058seconds, PASS: all944saved calls, exact prompts/tasks/source binding,
output inventory and37ecstate verified; RESULT hash remains c2fe5b4735ea7252fff27e7ea777093e798df882f57262ab0391ad91b6b671a2.
No model load or new native calls. Receipt: baseline_replay_20260914T2020.json.
Subsequent direct observation status_20260914T2021.json shows FULL1026/2928,
LOSS_OFF1023/2928, original guardians/native PIDs alive, no FAILED/trainRESULT
and no AFTER yet. Last200-update rates1.85844/1.85973s give conditional TRAIN
ETAs21:20:35/21:20:43UTC, excluding save and AFTER. GPU2 remains empty; GPU0/1
still40504MiB each. All existing source, jobs and deadlines preserved.

## [Builder/Nash] 2026-09-14 20:38:06 UTC — handover liveness check

Direct read-only node3 observation: FULL1553/2928updates, guardian86063 and
native86119 alive; LOSS_OFF1549/2928updates, guardian86064 and native86109
alive. Both have no FAILED receipt, no train RESULT, no AFTER directory and
zero AFTER call files. GPU0/1 each40504MiB; no GPU2 compute process.
Recent update rates1.87804/1.88395seconds imply conditional TRAIN completion
21:21:09/21:21:25UTC, excluding save/reload and AFTER. No extra baseline
replay, retokenization, launch, restart, source edit or budget change.
Quality branch monitoring/readout/reduction remains assigned despite other
workers retiring. Existing guards retain the previously authorized fresh
AFTER transition within the original23:54:24UTC deadline.

## [Builder/Nash] 2026-09-14 21:33 UTC — terminal fits and original automatic AFTERs

Spaced read-only monitoring continued every300seconds through terminal status;
full observations in monitor_20260914T2049.jsonl. Both original guardians
completed without FAILED/abort or deadline change. FULL2928updates finished
21:21:30UTC, original guard started fresh AFTER native91024 at21:21:31,
COMPLETE960calls21:32:18; guard86063 completed21:32:19. LOSS_OFF2928updates
finished21:21:45, automatic fresh AFTER native91067 began21:21:46,
COMPLETE932calls21:32:32; guard86064 completed21:32:33. No duplicate launches.

Actual labels FULL238274,loss-off173814,commonreference238274; both own saved
states reloaded unchanged for AFTER. FULL e226cea230b4b970cd5a94cb2b853350aa8bfb95ab4ba69cba3e78ebdd0ad3bf;
loss-off4f0dccf5b7cf37b872eafc3a50990e0cdfda027fb0140f0aad999f27606e4ee3.
Shared944call baseline remains33/64goals,2/32pairs, not legacyP44 0/4.
FULL62/64goals,30/32pairs; control26/64,1/32. Full engineering conjunction
FAILS because shard1PROBE-A has0/2pairs; remaining15worlds2/2each. Fixed32pair
denominator retained. Full oldW0/W8/audit16/16 each, original/fresh4/4 each;
control old/audit16/16 but original/fresh2/4. UNAVAILABLEpairs0/32 allstates.

## [Builder/Nash] 2026-09-14 21:33:43 UTC — GPU0/1 released and evidence preserved

Physical+CVD clearance passed21:33:42.801GPU0 and21:33:43.050GPU1, no owners,
unresolved entries or GPU compute processes. Initial SSH-session unresolved
scan retained; detached retry passed unchanged scanner without new exceptions.
No kill/restart. Original deadline23:54:24 intact. Native phase assigned cost
3.644GPUh including baseline; actual2836inferencecalls/35579generatedtokens.
Terminal archive built off VM root and stored locally on/data; SHA256
0152cafb69aa7715b5f4fbb15caa4954f03c62c1f3c063883ed9c17c9aa00deb.
9315entries hash-verified remote before/after and local extraction. Final
RESULT.md/FINAL_CHECKS.json document metrics, retained failures, saved-state
joins, tests, costs and unchanged logging-order deviation. No checkpoint
promotion or new experiment follows; both arms and reduction are terminal.
