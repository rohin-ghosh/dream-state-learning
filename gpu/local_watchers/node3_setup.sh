#!/bin/bash
# node3_setup.sh — laptop-side orchestrator that clones node 2's working environment onto a freshly onboarded node 3
# (after gpu/local_watchers/node3_onboard.sh printed NODE_READY). Everything heavy moves node-2 → node-3 inside the
# datacentre; the laptop only orchestrates. Idempotent: re-run to resume.
# Steps: (1) NVIDIA driver 580-server + CUDA toolkit 13.0 via apt (reboot if the driver needs it, then wait);
#        (2) node-3 ssh key → node-2 authorized_keys (so node 3 can pull); (3) rsync ~/v2/venv, ~/.cache/huggingface/hub
#        (Qwen2.5-7B-Instruct, 14B), ~/cgym_test (CompilerGym 0.2.5 venv — the lives' gym interpreter; missed on
#        2026-09-12, found when the builder's first node-3 life failed), ~/.local/share/compiler_gym (1.4 GB datasets),
#        ~/dream-state, ~/status.sh from node 2; (4) sanity: nvidia-smi 8 GPUs, torch+vllm
#        import in the venv, tests dir present; (5) queue runner installed. Prints NODE3_SETUP_DONE.
# Usage: bash gpu/local_watchers/node3_setup.sh <prefix>   (prefix = wrappers created by onboard, e.g. ovx2)
set -u
PFX="${1:-ovx2}"; REPO="$HOME/dream-state"; LOG="$HOME/dream-state-artifacts/node3_setup.log"
S3="bash $REPO/gpu/${PFX}_ssh.sh"; S2="bash $REPO/gpu/ovx_ssh.sh"
source "$REPO/gpu/hosts.env"; N2="$OVX_NODE"
log() { echo "$(date -u +%FT%TZ) $*" | tee -a "$LOG"; }
log "node3_setup start (prefix $PFX; source node 2 = ${N2%%@*}@…)"
# (1) driver + toolkit
$S3 'set -e; if ! command -v nvidia-smi >/dev/null || ! nvidia-smi -L >/dev/null 2>&1; then
  cd /tmp && [ -f cuda-keyring_1.1-1_all.deb ] || wget -q https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2404/x86_64/cuda-keyring_1.1-1_all.deb
  sudo dpkg -i cuda-keyring_1.1-1_all.deb >/dev/null; sudo apt-get update -qq
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq nvidia-driver-580-server nvidia-utils-580-server cuda-toolkit-13-0 rsync expect python3.12-dev python3-dev build-essential ninja-build >/dev/null 2>&1 || sudo DEBIAN_FRONTEND=noninteractive apt-get install -y nvidia-driver-580-server nvidia-utils-580-server cuda-toolkit-13-0 rsync python3.12-dev python3-dev build-essential ninja-build
  echo APT_DONE; nvidia-smi -L 2>/dev/null | wc -l
else echo DRIVER_PRESENT; nvidia-smi -L | wc -l; fi; sudo -n nvidia-smi -pm 1 >/dev/null 2>&1 && echo PERSISTENCE_ON; sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq python3.12-dev python3-dev build-essential ninja-build >/dev/null 2>&1; ls /usr/include/python3.12/Python.h' 2>&1 | tail -3 | tee -a "$LOG"
if ! $S3 'nvidia-smi -L 2>/dev/null | grep -q GPU'; then
  log "driver not active yet; rebooting node 3 and waiting"
  $S3 'sudo reboot' 2>/dev/null; sleep 90
  for ((i=0;i<30;i++)); do $S3 'nvidia-smi -L 2>/dev/null | grep -q GPU' 2>/dev/null && break; sleep 30; done
fi
log "GPUs on node 3: $($S3 'nvidia-smi -L 2>/dev/null | wc -l'); driver $($S3 'nvidia-smi --query-gpu=driver_version --format=csv,noheader | head -1')"
# (1b) no display server on a compute node: Xorg otherwise holds ~15 MiB on every GPU and the builder's GPU-free check
#      (nvidia-smi shows a process) refuses to launch there (node 3, 2026-09-12 07:31 UTC).
$S3 'sudo -n systemctl stop display-manager 2>/dev/null; sudo -n systemctl disable display-manager 2>/dev/null; sudo -n systemctl set-default multi-user.target 2>/dev/null; pgrep -c Xorg || echo no_xorg' 2>&1 | tail -1 | tee -a "$LOG"
# (2) key node3 -> node2
PUB=$($S3 '[ -f ~/.ssh/id_ed25519 ] || ssh-keygen -q -t ed25519 -N "" -f ~/.ssh/id_ed25519; cat ~/.ssh/id_ed25519.pub')
$S2 "grep -qF '${PUB}' ~/.ssh/authorized_keys 2>/dev/null || echo '${PUB}' >> ~/.ssh/authorized_keys; echo key_on_node2" | tee -a "$LOG"
N2HOST="${N2#*@}"; N2USER="${N2%%@*}"
$S3 "ssh -o StrictHostKeyChecking=accept-new -o BatchMode=yes ${N2USER}@${N2HOST} 'echo node3_can_reach_node2'" | tee -a "$LOG"
# (3) rsync pulls (venv 8 GB, HF cache 42 GB, repo 1.4 GB) — resumable
for path in v2/venv cgym_test .cache/huggingface/hub .local/share/compiler_gym dream-state status.sh; do
  log "rsync $path from node 2"
  $S3 "mkdir -p ~/$(dirname $path) && rsync -a --partial --info=progress2 ${N2USER}@${N2HOST}:~/$path/ ~/$path/ 2>&1 | tail -1" 2>&1 | tail -1 | tee -a "$LOG"
done
$S3 'rsync -a '"${N2USER}@${N2HOST}"':~/status.sh ~/status.sh 2>/dev/null; chmod +x ~/status.sh 2>/dev/null; true'
# (4) sanity
$S3 'export HF_HUB_OFFLINE=1 CUDA_HOME=/usr/local/cuda-13.0 PATH=/usr/local/cuda-13.0/bin:$HOME/v2/venv/bin:$PATH; ~/v2/venv/bin/python -c "import torch,vllm,peft,transformers;print(\"torch\",torch.__version__,\"cuda\",torch.cuda.is_available(),torch.cuda.device_count(),\"vllm\",vllm.__version__,\"peft\",peft.__version__)"; ls ~/.cache/huggingface/hub; ls ~/dream-state/tests | wc -l; df -h ~ | tail -1' 2>&1 | tee -a "$LOG"
# (5) queue runner
$S3 'cd ~/dream-state && bash gpu/queue_install.sh 3 2>&1 | tail -3' 2>&1 | tee -a "$LOG"
log "NODE3_SETUP_DONE"
