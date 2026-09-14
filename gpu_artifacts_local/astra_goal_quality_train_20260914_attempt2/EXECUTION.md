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
