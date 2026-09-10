#!/bin/bash
# Provision <INTERNAL_HOST> end-to-end. All lessons from <INTERNAL_HOST> baked in.
set -u
S="/Users/rohing/dream-state/gpu/ovx_ssh.sh"
NODE="local-rohing@<INTERNAL_IP>"
run() { bash "$S" "$@"; }
wait_ssh() { for i in $(seq 1 60); do run "echo up" >/dev/null 2>&1 && return 0; sleep 20; done; return 1; }

echo "PHASE1_DRIVER $(date '+%H:%M')"
if ! run "nvidia-smi -L >/dev/null 2>&1"; then
  run "sudo apt-get update -qq && sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq nvidia-driver-580-server nvidia-utils-580-server >/dev/null 2>&1" || { echo FAILED_driver; exit 1; }
  if ! run "nvidia-smi -L >/dev/null 2>&1"; then
    run "sudo modprobe nvidia" >/dev/null 2>&1
    if ! run "nvidia-smi -L >/dev/null 2>&1"; then
      echo REBOOTING; run "sudo reboot" >/dev/null 2>&1; sleep 60; wait_ssh || { echo FAILED_no_return; exit 1; }
    fi
  fi
fi
G=$(run "nvidia-smi -L 2>/dev/null | wc -l"); echo "PHASE1 done: $G GPUs"; [ "${G:-0}" -ge 8 ] || { echo FAILED_gpu_count; exit 1; }

echo "PHASE2_TOOLKIT+ENV $(date '+%H:%M')"
run "cd /tmp && wget -q https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2404/x86_64/cuda-keyring_1.1-1_all.deb && sudo dpkg -i cuda-keyring_1.1-1_all.deb >/dev/null && sudo apt-get update -qq && sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq cuda-toolkit-13-0 ninja-build python3-venv python3-dev build-essential rsync >/dev/null 2>&1 && echo TOOLKIT_OK" || { echo FAILED_toolkit; exit 1; }
run "grep -q cuda-13.0 ~/.bashrc || { echo 'export CUDA_HOME=/usr/local/cuda-13.0' >> ~/.bashrc; echo 'export PATH=/usr/local/cuda-13.0/bin:\$PATH' >> ~/.bashrc; echo 'export HF_HUB_OFFLINE=1' >> ~/.bashrc; }"
run "mkdir -p ~/v2 && [ -x ~/v2/venv/bin/pip ] || python3 -m venv ~/v2/venv" || { echo FAILED_venv; exit 1; }
run "~/v2/venv/bin/pip install -q -U pip && ~/v2/venv/bin/pip install -q torch==2.13.0 vllm==0.27.1 transformers==5.5.3 peft==0.20.0 ninja huggingface_hub" || { echo FAILED_pip; exit 1; }
echo "PHASE2 done"

echo "PHASE3_REPO $(date '+%H:%M')"
rsync -a --delete --exclude='.git' --exclude='.venv' --exclude='gpu_artifacts_local' --exclude='alchemy/v2_out' --exclude='alchemy/smoke_out' "$HOME/dream-state/" "$NODE:~/dream-state/" || { echo FAILED_rsync; exit 1; }
echo "PHASE3 done"

echo "PHASE4_MODEL+CGYM $(date '+%H:%M')"
run "~/v2/venv/bin/hf download Qwen/Qwen2.5-7B-Instruct >/dev/null 2>~/model_dl.err && echo MODEL7B_OK || (tail -2 ~/model_dl.err; echo MODEL_FAIL)" | tail -2
# CompilerGym: mirror the working py3.10 runtime from node 1 (venv + libtinfo + cache)
echo "  syncing cgym runtime from node 1 (relay via local)..."
mkdir -p /private/tmp/claude-501/-Users-rohing/d66e193e-e075-475c-96de-a582e32ee6c5/scratchpad/cgym_relay
rsync -a local-rohing@<INTERNAL_IP>:~/cgym_test/ /private/tmp/claude-501/-Users-rohing/d66e193e-e075-475c-96de-a582e32ee6c5/scratchpad/cgym_relay/cgym_test/ 2>/dev/null
rsync -a local-rohing@<INTERNAL_IP>:~/.local/share/compiler_gym/ /private/tmp/claude-501/-Users-rohing/d66e193e-e075-475c-96de-a582e32ee6c5/scratchpad/cgym_relay/compiler_gym/ 2>/dev/null
rsync -a /private/tmp/claude-501/-Users-rohing/d66e193e-e075-475c-96de-a582e32ee6c5/scratchpad/cgym_relay/cgym_test/ "$NODE:~/cgym_test/"
run "mkdir -p ~/.local/share" && rsync -a /private/tmp/claude-501/-Users-rohing/d66e193e-e075-475c-96de-a582e32ee6c5/scratchpad/cgym_relay/compiler_gym/ "$NODE:~/.local/share/compiler_gym/"
run "cd ~/dream-state && LD_LIBRARY_PATH=\$HOME/cgym_test/lib ~/cgym_test/venv/bin/python organism_v6/cgym_eval.py --benchmark=cbench-v1/crc32 --passes=-mem2reg,-gvn 2>/dev/null | tail -1"
echo "PHASE4 done"

echo "PHASE5_SMOKE $(date '+%H:%M')"
run "cat > ~/smoke7b.py" <<'PY'
import os
os.environ.setdefault("VLLM_WORKER_MULTIPROC_METHOD", "spawn")
def main():
    from vllm import LLM, SamplingParams
    llm = LLM(model="Qwen/Qwen2.5-7B-Instruct", max_model_len=4096,
              gpu_memory_utilization=0.85, enforce_eager=True)
    out = llm.generate(["The capital of France is"],
                       SamplingParams(max_tokens=8, temperature=0.7, seed=1))
    ids = out[0].outputs[0].token_ids
    assert ids and all(isinstance(i, int) for i in ids)
    print("SMOKE_OK", repr(out[0].outputs[0].text[:40]))
if __name__ == "__main__":
    main()
PY
run "cd ~/dream-state && export HF_HUB_OFFLINE=1 CUDA_HOME=/usr/local/cuda-13.0 PATH=/usr/local/cuda-13.0/bin:\$HOME/v2/venv/bin:\$PATH; CUDA_VISIBLE_DEVICES=0 ~/v2/venv/bin/python ~/smoke7b.py 2>~/smoke.err | grep SMOKE || (grep -iE 'error' ~/smoke.err | tail -3; echo SMOKE_FAIL)"
echo "OVX_PROVISION_COMPLETE $(date '+%H:%M')"
