#!/usr/bin/env bash
# v2 node bootstrap — idempotent; run ON the leased node as the lease user.
#   scp -r via wrapper, then:  bash gpu/v2_bootstrap.sh
# Auto-detects GPU count; sets up env, models, and prints the worker plan.
set -euo pipefail

REPO_DIR="${REPO_DIR:-$HOME/dream-state}"
WORK="${WORK:-$HOME/v2}"          # put HF cache + artifacts on local NVMe
PY="${PY:-python3}"
MODELS=("Qwen/Qwen2.5-7B-Instruct" "Qwen/Qwen2.5-0.5B-Instruct")

echo "== [1/6] system check =="
nvidia-smi --query-gpu=index,name,memory.total,driver_version \
    --format=csv || { echo "FATAL: nvidia-smi failed"; exit 1; }
NGPU=$(nvidia-smi --list-gpus | wc -l)
echo "GPUs detected: $NGPU"
df -h "$HOME" | tail -1

echo "== [2/6] venv + stack =="
mkdir -p "$WORK"
export HF_HOME="$WORK/hf"
if [ ! -d "$WORK/venv" ]; then $PY -m venv "$WORK/venv"; fi
source "$WORK/venv/bin/activate"
pip -q install --upgrade pip
# torch first (CUDA wheel), then the rest; versions known-good together
pip -q install torch --index-url https://download.pytorch.org/whl/cu124 \
    || pip -q install torch          # fallback: default index
pip -q install "vllm>=0.6" "transformers>=4.45" "peft>=0.12" \
    accelerate numpy sentencepiece
python -c "import torch; print('torch', torch.__version__, \
'cuda', torch.cuda.is_available(), torch.cuda.device_count(), 'gpus')"

echo "== [3/6] model pulls (to local NVMe) =="
pip -q install "huggingface_hub[cli]"
for m in "${MODELS[@]}"; do
  python - "$m" <<'EOF'
import sys
from huggingface_hub import snapshot_download
print("pull:", sys.argv[1])
snapshot_download(sys.argv[1])
EOF
done

echo "== [4/6] repo sanity =="
cd "$REPO_DIR"
PYTHONPATH=. python -c "
from alchemy.world import AlchemyWorld
from alchemy.env import generate_life
from alchemy.player import ScriptedExplorer
w = AlchemyWorld(n_ingredients=1024, n_inert=128, seed=0, n_essences=96)
h = w.sample_holdout(0.3, seed=0)
eps = generate_life(w, ScriptedExplorer(seed=0), 960, inv_size=6, seed=0, holdout=h)
assert sum(e['success'] for e in eps) > 0
print('env OK:', len(eps), 'episodes')"

echo "== [5/6] GPU smoke (0.5B end-to-end on GPU 0) =="
CUDA_VISIBLE_DEVICES=0 PYTHONPATH=. python alchemy/run_smoke.py \
    --model Qwen/Qwen2.5-0.5B-Instruct --out "$WORK/smoke_out"

echo "== [6/6] worker plan =="
echo "GPUs: $NGPU  ->  seed workers 0..$((NGPU-1))"
echo "launch (when harness lands):"
echo "  for g in \$(seq 0 $((NGPU-1))); do"
echo "    CUDA_VISIBLE_DEVICES=\$g nohup python alchemy/run_v2.py \\"
echo "      --seed \$g --out $WORK/run/seed\$g > $WORK/logs/seed\$g.log 2>&1 &"
echo "  done"
echo "BOOTSTRAP COMPLETE"
