# R121 broker-only retirement receipt

[Builder / Main] September 16, 2026, 01:55:54 UTC; wrapper `gpu/ovx3_ssh.sh`.

| Branch | Broker PID / start ticks | Observed disposition |
| --- | --- | --- |
| F1 | 407245 / 3932533 | RETIRED at 01:55:54.036780 UTC |
| F2 | 4101008 / 3629615 | RETIRED at 01:55:54.140594 UTC |
| F3 | No broker found at 01:54:08 UTC | Already absent; latest child service reported COMPLETE |
| F4 | No broker found at 01:54:08 UTC | Already absent; child still alive in that snapshot |

For F1/F2, Main rechecked exact module `gpu.orch_r110_claude_broker`, configuration
path, PID start ticks, owner and PPID. Each broker was paused briefly, then
verified to have no provider subprocesses and zero unfinished claims before
broker-only termination. If either check had failed, the broker would have
resumed without retirement. Termination was verified. No child received a signal;
no child, adapter, optimizer, queue or checkpoint was restarted or replaced.
Existing claims, published responses and runner-lock evidence were preserved.

Node-local immutable receipts live at each configured remote root under
`parent_claude/RETIRED_R121_20260916.json`.

Configuration bindings:

- F1: `/localhome/local-rohing/orch_r127_f1_substitution_20260915_v1/F1/CONFIG.json`,
  SHA256 `aa2abe0e496c5334f68ccc8c21d8108c378fd1a3814341de7dd1e66a6a0295d4`.
- F2: `/localhome/local-rohing/orch_r124_parent_transport_contract_20260915_v1/F2_math_r124/CONFIG.json`,
  SHA256 `c10d508ea7377eaa442ca7161ada2f2713a5986ce00fd2c11218ddd867071621`.

**No replacement provider was launched.** The request to route this
safeguard-refused workflow to Astra as a workaround is not implemented. Refused
inputs and missing/late backlog are not replayed. Existing Astra runs were not
modified. Consequently, this receipt does NOT establish that all eight lanes
are Astra-parented, nor that their subsequent parent turns are delivered.
Fable head-parent cron retirement remains watcher-owned, not independently
claimed here. No new Level-2/3 work was launched.
