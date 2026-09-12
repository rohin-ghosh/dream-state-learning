#!/usr/bin/env bash
set -euo pipefail
test ! -e /tmp/astra_prefixmask_terminal_20260912
test ! -e /tmp/astra_prefixmask_terminal_20260912.tgz
bash gpu/ovx2_ssh.sh 'bash -se' <<'REMOTE'
set -euo pipefail
root="$HOME/astra_diagnostics/astra_A1_prefixmask_bank0_ts2_20260912_attempt2"
test ! -e "$root/logs/failure.json"
jq -e '.status == "WORKER_COMPLETED"' "$root/logs/result.json"
jq -e '.owned_group_empty and .gpu_processes_absent and .reservation_release_verified and .cleanup_error == null' "$root/logs/worker.cleanup.json"
test ! -d /proc/73820
test ! -e /tmp/astra_prefixmask_terminal_20260912.tgz
test ! -e /tmp/astra_prefixmask_remote_weights_20260912.txt
sha256sum "$root"/adapters/bank0/F_r16k16/across/sleep4/r8/adapter_model.safetensors > /tmp/astra_prefixmask_remote_weights_20260912.txt
tar --exclude=adapter_model.safetensors --exclude=adapter_model.bin -czf /tmp/astra_prefixmask_terminal_20260912.tgz -C "$HOME/astra_diagnostics" astra_A1_prefixmask_bank0_ts2_20260912_attempt2
sha256sum /tmp/astra_prefixmask_terminal_20260912.tgz /tmp/astra_prefixmask_remote_weights_20260912.txt
REMOTE
bash gpu/ovx2_scp.sh NODE:/tmp/astra_prefixmask_terminal_20260912.tgz NODE:/tmp/astra_prefixmask_remote_weights_20260912.txt /tmp/
sha256sum /tmp/astra_prefixmask_terminal_20260912.tgz /tmp/astra_prefixmask_remote_weights_20260912.txt
mkdir /tmp/astra_prefixmask_terminal_20260912
tar -xzf /tmp/astra_prefixmask_terminal_20260912.tgz -C /tmp/astra_prefixmask_terminal_20260912
