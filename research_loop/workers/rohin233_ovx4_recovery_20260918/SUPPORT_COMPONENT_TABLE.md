# Support components — actual execution hosts and bounds

Read-only census September18 18:56UTC. Detailed hashes, configs, start ticks,
systemd evidence and socket/controller joins: `SUPPORT_COMPONENT_TABLE.json`.
App deadlines and hard wrapper bounds are distinct. Derived times use one-second
boot/systemd display precision. SSH wrappers have five-second kill grace.
No raw hosts, addresses or secrets are included.

|Component|Executes on|PID|Start UTC (Sep18)|Actual observed bound (UTC)|
|---|---|---:|---|---|
|base_player_generation|ovx4|459712|17:50:38.110000|2026-09-30T17:59:30+00:00|
|shared_node3_scorer|ovx4|499900|18:16:04.990000|2026-09-30T17:59:30+00:00|
|shared_node2_scorer|ovx4|499905|18:16:05.340000|2026-09-30T17:59:30+00:00|
|base_scorer|ovx4|506797|18:20:23.090000|2026-09-30T17:59:30+00:00|
|shared2_prior_bridge|ovx4|448173|17:43:15.140000|2026-09-30T17:59:29+00:00|
|shared3_prior_bridge|ovx4|448322|17:43:17.180000|2026-09-30T17:59:29+00:00|
|shared2_judge_bridge|ovx4|502015|18:17:10.910000|2026-09-30T17:59:29+00:00|
|shared3_judge_bridge|ovx4|502012|18:17:10.850000|2026-09-30T17:59:29+00:00|
|base_judge_bridge|ovx4|507837|18:21:01.990000|2026-09-30T17:59:29+00:00|
|P3_scorer|node4|573479|18:20:22.600000|2026-09-25T17:59:30+00:00|
|P3_prior_bridge|node4|428814|17:43:14.890000|2026-09-25T17:59:29+00:00|
|P3_judge_bridge|node4|570041|18:17:28.600000|2026-09-25T17:59:29+00:00|
|P3_Tool_writer|node4|458401|17:47:38.520000|2026-09-25T17:59:29+00:00|
|node3_upstream_timeout|operator_vm|3044137|17:47:08.310000|2026-09-30T17:59:28.310000+00:00|
|node2_upstream_timeout|operator_vm|3044280|17:47:10.750000|2026-09-30T17:59:28.750000+00:00|
|node3_proxy|operator_vm|3044140|17:47:08.310000|2026-09-30T17:59:28.310000+00:00|
|node2_proxy|operator_vm|3044283|17:47:10.750000|2026-09-30T17:59:28.750000+00:00|
|node2_downstream_timeout|operator_vm|3334145|18:41:12.950000|2026-09-20T17:59:18.950000+00:00|
|node3_downstream_timeout|operator_vm|3334410|18:41:15.900000|2026-09-24T17:59:18.900000+00:00|
|every_sleep_enrollment|operator_vm|3046824|17:47:37.210000|2026-09-30T17:59:28.210000+00:00|
|node3_upstream_timeout_ssh_child|operator_vm|3044139|17:47:08.310000|2026-09-30T17:59:28.310000+00:00|
|node2_upstream_timeout_ssh_child|operator_vm|3044282|17:47:10.750000|2026-09-30T17:59:28.750000+00:00|
|node2_downstream_timeout_ssh_child|operator_vm|3334146|18:41:12.950000|2026-09-20T17:59:18.950000+00:00|
|node3_downstream_timeout_ssh_child|operator_vm|3334411|18:41:15.900000|2026-09-24T17:59:18.900000+00:00|
|remote_socket_owner|node2|966155|18:41:13.570000|2026-09-20T17:59:18.950000+00:00|
|node3_existing_Tool_writer_Copernicus|node3|1970178|17:46:05.720000|2026-09-24T18:00:00+00:00|
|remote_socket_owner|node3|2034856|18:41:17.100000|2026-09-24T17:59:18.900000+00:00|
|finite_age_probe_sleep24|ovx4|—|not persistent|COMPLETED_NOT_RUNNING_NO_BACKLOG_DISPATCHER|
|base_parent_guidance|ovx4|459712|17:50:38.110000|2026-09-30T17:59:30+00:00|
|node2_upstream_remote_ssh_peer|ovx4|454716|17:47:11.150000|2026-09-30T17:59:28.750000+00:00|
|node2_upstream_remote_ssh_peer|ovx4|454756|17:47:11.980000|2026-09-30T17:59:28.750000+00:00|
|node3_upstream_remote_ssh_peer|ovx4|454556|17:47:08.690000|2026-09-30T17:59:28.310000+00:00|
|node3_upstream_remote_ssh_peer|ovx4|454651|17:47:09.540000|2026-09-30T17:59:28.310000+00:00|
|node2_journal_export_rpc|node2|—|not persistent|ON_DEMAND_NOT_PERSISTENT|
|node3_journal_export_rpc|node3|—|not persistent|ON_DEMAND_NOT_PERSISTENT|
|origin_mirror_import_rpc|ovx4|—|not persistent|ON_DEMAND_NOT_PERSISTENT|

## Limits

- Remote reverse listeners inherit controlling SSH connection lifetime; no independent remote hard timer was installed.
- Enrollment is an operator_vm service through Sep30, not continuous capture/evaluation. Its current source does not contain per-target lease-date admission; explicit per-target renewal/capping is still needed before the earliest source cutoff.
- Node3 Tool relay1970178 is externally owned by Copernicus, observed Sep24 18:00 app deadline; no owned signal/change.
- Node2 ordinary Tool delivery is a native-owner integration, not an observed separate owned publisher; future render not established in this census.
- P3 native LOAD and correction notice rendering remain Main-owned and unproved here.
- Remote SSH owners inherit connection-controller lifetime; this is not an independent remote hard-stop timer.
- No-persistent-PID endpoints are short-lived CPU calls, not unobserved continuously running models.
- Repeated base PID459712 identifies inline parent guidance, not a second player.
