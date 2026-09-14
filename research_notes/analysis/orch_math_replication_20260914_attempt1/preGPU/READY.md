# MATH-REPLICATION preGPU gate — 2026-09-14T22:45Z

Operational alias resolved by PI: node3 uses existing gpu/ovx2_ssh.sh,
OVX2_NODE from ignored gpu/hosts.env. No handover/outcome contents read, no
hostname persisted here, and no access to node2 or other compute devices.
The protocol/cohort/analysis/prompt policy are unchanged from the blind freeze.

Sixteen CPU regressions pass locally and on node3 with CVD empty. The exact
portable manifest, adapter files, local base and tokenizer file inventories
pass CPU verification in PREPARED.json. Native mounted named_parameters and
frozen-base checks remain enforced before and after inference by the runner.

All physical UUID/PID plus complete privileged /proc CVD/device scans pass:
GPU2 GPU-41a86250-88eb-ed8a-ddfe-9d6f93515da1;
GPU3 GPU-e1277146-04f2-c38f-d1ae-1a98132f907e;
GPU4 GPU-f484c608-a2d4-0c26-dee1-a06cc5ae69e4.
Each has1MiB idle memory, zero utilization, no compute PID or reservation.
Fresh identical checks will run immediately before each launch.

Non-material operational repair, not a scientific design change: ordinary
credentials could not read other users' /proc; passwordless sudo is used only
for the read-only ownership scan. The guardian rejects root-native launch.
The sole open-device infrastructure process is independently identified as
/usr/bin/nvidia-persistenced, PID2725, UID127, start_ticks1396. Its executable
hash, command hash, UID, PID and start time are bound in SERVICE_IDENTITY.json.
This exact known service's device handles alone are exempt; compute use,
CVD reservation, unexplained memory, unknown identity and unreadable /proc
still fail closed. No borrowed whitelist, unknown exemption or kill is used.
Initial blocked scans are preserved. A regression tests that this service
exception cannot exempt compute use or CVD reservation.

Source archive SHA256:
25a0d9b4816a3ffcc5e5ac9d3e160493a60f04c1f91a93dedd577029d01e7030.
Original source archive is preserved separately. Cohort SHA256 remains
42ec9ca3605579ced04941ae2518fe3dd9638d7dd5e680fa856e71cd4da38dc0.
Model runner and oracle/analysis policy bytes are unchanged.

Observed remote runtime /localhome/local-rohing/v2/venv/bin/python and model
snapshot directory were checked on node3, not assumed from the previous node.
Only own /tmp/orch_math_replication_20260914_attempt1 is created remotely.
Three shards, paired initial calls, <=128 calls total, no fit or scale,
<=45min per shard, lease end2026-09-20T03:03Z with six-hour margin.

Terminal-ready after this exact-path publication: ordered SEQ requested from
PI for the three assigned shards. No parent/Fable gate; no prior outcomes read.
