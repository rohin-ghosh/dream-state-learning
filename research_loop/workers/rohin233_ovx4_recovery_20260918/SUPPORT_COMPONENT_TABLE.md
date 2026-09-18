# Support components — actual execution hosts and bounds

Schema: `R233_SUPPORT_COMPONENT_TABLE_V2`; machine contract:
`SUPPORT_COMPONENT_SCHEMA.json`. Only enrollment is freshly replaced at
September18 19:11:08.991879UTC and verified in this update. Other components
retain the September18 18:56 baseline census and original linked evidence.
Detailed proofs and superseded enrollment row: `SUPPORT_COMPONENT_TABLE.json`.

|Component|Executes on|PID|Start UTC|Actual observed bound (UTC)|
|---|---|---:|---|---|
|base_player_generation|ovx4|459712|2026-09-18T17:50:38.110000+00:00|2026-09-30T17:59:30+00:00|
|shared_node3_scorer|ovx4|499900|2026-09-18T18:16:04.990000+00:00|2026-09-30T17:59:30+00:00|
|shared_node2_scorer|ovx4|499905|2026-09-18T18:16:05.340000+00:00|2026-09-30T17:59:30+00:00|
|base_scorer|ovx4|506797|2026-09-18T18:20:23.090000+00:00|2026-09-30T17:59:30+00:00|
|shared2_prior_bridge|ovx4|448173|2026-09-18T17:43:15.140000+00:00|2026-09-30T17:59:29+00:00|
|shared3_prior_bridge|ovx4|448322|2026-09-18T17:43:17.180000+00:00|2026-09-30T17:59:29+00:00|
|shared2_judge_bridge|ovx4|502015|2026-09-18T18:17:10.910000+00:00|2026-09-30T17:59:29+00:00|
|shared3_judge_bridge|ovx4|502012|2026-09-18T18:17:10.850000+00:00|2026-09-30T17:59:29+00:00|
|base_judge_bridge|ovx4|507837|2026-09-18T18:21:01.990000+00:00|2026-09-30T17:59:29+00:00|
|P3_scorer|node4|573479|2026-09-18T18:20:22.600000+00:00|2026-09-25T17:59:30+00:00|
|P3_prior_bridge|node4|428814|2026-09-18T17:43:14.890000+00:00|2026-09-25T17:59:29+00:00|
|P3_judge_bridge|node4|570041|2026-09-18T18:17:28.600000+00:00|2026-09-25T17:59:29+00:00|
|P3_Tool_writer|node4|458401|2026-09-18T17:47:38.520000+00:00|2026-09-25T17:59:29+00:00|
|node3_upstream_timeout|operator_vm|3044137|2026-09-18T17:47:08.310000+00:00|2026-09-30T17:59:28.310000+00:00|
|node2_upstream_timeout|operator_vm|3044280|2026-09-18T17:47:10.750000+00:00|2026-09-30T17:59:28.750000+00:00|
|node3_proxy|operator_vm|3044140|2026-09-18T17:47:08.310000+00:00|2026-09-30T17:59:28.310000+00:00|
|node2_proxy|operator_vm|3044283|2026-09-18T17:47:10.750000+00:00|2026-09-30T17:59:28.750000+00:00|
|node2_downstream_timeout|operator_vm|3334145|2026-09-18T18:41:12.950000+00:00|2026-09-20T17:59:18.950000+00:00|
|node3_downstream_timeout|operator_vm|3334410|2026-09-18T18:41:15.900000+00:00|2026-09-24T17:59:18.900000+00:00|
|every_sleep_enrollment|operator_vm|3524450|2026-09-18T19:11:08.010000+00:00|2026-09-30T17:59:29.010000+00:00|
|node3_upstream_timeout_ssh_child|operator_vm|3044139|2026-09-18T17:47:08.310000+00:00|2026-09-30T17:59:28.310000+00:00|
|node2_upstream_timeout_ssh_child|operator_vm|3044282|2026-09-18T17:47:10.750000+00:00|2026-09-30T17:59:28.750000+00:00|
|node2_downstream_timeout_ssh_child|operator_vm|3334146|2026-09-18T18:41:12.950000+00:00|2026-09-20T17:59:18.950000+00:00|
|node3_downstream_timeout_ssh_child|operator_vm|3334411|2026-09-18T18:41:15.900000+00:00|2026-09-24T17:59:18.900000+00:00|
|remote_socket_owner|node2|966155|2026-09-18T18:41:13.570000+00:00|2026-09-20T17:59:18.950000+00:00|
|node3_existing_Tool_writer_Copernicus|node3|1970178|2026-09-18T17:46:05.720000+00:00|2026-09-24T18:00:00+00:00|
|remote_socket_owner|node3|2034856|2026-09-18T18:41:17.100000+00:00|2026-09-24T17:59:18.900000+00:00|
|finite_age_probe_sleep24|ovx4|—|not persistent|COMPLETED_NOT_RUNNING_NO_BACKLOG_DISPATCHER|
|base_parent_guidance|ovx4|459712|2026-09-18T17:50:38.110000+00:00|2026-09-30T17:59:30+00:00|
|node2_upstream_remote_ssh_peer|ovx4|454716|2026-09-18T17:47:11.150000+00:00|2026-09-30T17:59:28.750000+00:00|
|node2_upstream_remote_ssh_peer|ovx4|454756|2026-09-18T17:47:11.980000+00:00|2026-09-30T17:59:28.750000+00:00|
|node3_upstream_remote_ssh_peer|ovx4|454556|2026-09-18T17:47:08.690000+00:00|2026-09-30T17:59:28.310000+00:00|
|node3_upstream_remote_ssh_peer|ovx4|454651|2026-09-18T17:47:09.540000+00:00|2026-09-30T17:59:28.310000+00:00|
|node2_journal_export_rpc|node2|—|not persistent|ON_DEMAND_NOT_PERSISTENT|
|node3_journal_export_rpc|node3|—|not persistent|ON_DEMAND_NOT_PERSISTENT|
|origin_mirror_import_rpc|ovx4|—|not persistent|ON_DEMAND_NOT_PERSISTENT|

## Enrollment source admission now live

Node2/node5: September20 18:00UTC; node3: September24 18:00UTC;
node4: September25 18:00UTC; ovx4: September30 18:00UTC. Effective
end is the minimum of source cutoff and the unchanged operator service end.
Deny reads at/after effective end minus35seconds. Caller timeout30seconds;
receiver checks its clock and arms a maximum30-second alarm, finishing before
effective end minus5seconds. Closed targets retain entries/cursors while other
registered lives continue. Same16 roots; no capture/evaluation dispatch.

## Limits

- Remote reverse listeners inherit controlling SSH connection lifetime; no independent remote hard timer was installed.
- Node3 Tool relay1970178 is externally owned by Copernicus, observed Sep24 18:00 app deadline; no owned signal/change.
- Node2 ordinary Tool delivery is a native-owner integration, not an observed separate owned publisher; future render not established in this census.
- P3 native LOAD and correction notice rendering remain Main-owned and unproved here.
- Enrollment now enforces per-source cutoffs before every remote read and with a receiving-process alarm. This is metadata enrollment, not capture/evaluation; no backlog dispatcher was started.
- Repeated base PID459712 identifies inline guidance, not another player.
- Deadline precision and SSH controller/remote-timer distinctions remain in each row proof.
