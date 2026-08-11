#!/bin/bash
# ONE-COMMAND node setup for the Felt Attention GPU tier (Colossus A100, ubuntu-24.04).
# Two-phase (drivers need a reboot — July lesson):
#   Phase 1 (fresh node): installs NVIDIA driver, then asks you to reboot.
#   Phase 2 (after reboot): conda env, torch/vllm/transformers, repo tests,
#                           model downloads. Prints READY when done.
# Usage:
#   export HF_TOKEN=...            # before phase 2
#   bash setup_node.sh             # run, reboot when told, run again
# Run inside tmux:  tmux new -s felt
set -e

echo "== Felt Attention node setup =="

# ---------------- Phase 1: driver ----------------
if ! command -v nvidia-smi >/dev/null 2>&1 || ! nvidia-smi >/dev/null 2>&1; then
    echo "[phase 1] NVIDIA driver missing — installing (this is the July step)."
    sudo apt-get update -y
    # ubuntu-24.04: use the distro recommended server driver
    sudo apt-get install -y ubuntu-drivers-common
    sudo ubuntu-drivers install || sudo apt-get install -y nvidia-driver-570-server
    echo ""
    echo ">>> Driver installed. REBOOT NOW:   sudo reboot"
    echo ">>> Then reconnect, 'tmux new -s felt', and run this script again."
    exit 0
fi
echo "[phase 1] driver OK: $(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader)"

# ---------------- Phase 2: environment ----------------
cd "$HOME"
if [ ! -d "$HOME/miniconda3" ]; then
    echo "[phase 2] installing miniconda"
    wget -q https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O mc.sh
    bash mc.sh -b -p "$HOME/miniconda3"
fi
eval "$("$HOME/miniconda3/bin/conda" shell.bash hook)"
conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main 2>/dev/null || true
conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r 2>/dev/null || true
if ! conda env list | grep -q "^felt "; then
    conda create -n felt python=3.11 -y
fi
conda activate felt

echo "[phase 2] installing python deps (vllm pulls its own torch)"
pip install -q --upgrade pip setuptools
pip install -q "vllm>=0.6" "transformers>=4.45" accelerate numpy
python -c "import torch; assert torch.cuda.is_available(), 'CUDA not visible'; print('torch', torch.__version__, '| cuda ok:', torch.cuda.get_device_name(0))"

echo "[phase 2] cloning repo"
if [ ! -d "$HOME/dream-state-learning" ]; then
    git clone https://github.com/rohin-ghosh/dream-state-learning.git "$HOME/dream-state-learning"
fi
cd "$HOME/dream-state-learning" && git pull

echo "[phase 2] running CPU test suites (must be 50/50 before any GPU spend)"
PYTHONPATH=. python tests/test_structmem.py 2>/dev/null | tail -1
PYTHONPATH=. python tests/test_game.py 2>/dev/null | tail -1
PYTHONPATH=. python tests/test_felt.py 2>/dev/null | tail -1

echo "[phase 2] downloading models (needs HF_TOKEN in env)"
python - <<'PY'
import os
from huggingface_hub import snapshot_download
tok = os.environ.get("HF_TOKEN")
assert tok, "export HF_TOKEN=... first"
for m in ["Qwen/Qwen2.5-1.5B-Instruct",
          "Qwen/Qwen2.5-3B-Instruct",          # escalation path (SIZING: likely)
          "microsoft/Phi-3.5-mini-instruct"]:  # 2nd family, UNGATED (Llama is gated)
    print("downloading", m)
    snapshot_download(m, token=tok)
print("models ready")
PY

echo ""
echo "== READY. Next: =="
echo "  cd ~/dream-state-learning"
echo "  PYTHONPATH=. python gpu/run_gates.py --model Qwen/Qwen2.5-1.5B-Instruct"
echo "  (then follow gpu/RUNBOOK.md)"
