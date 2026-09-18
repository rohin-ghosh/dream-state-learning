#!/bin/bash
set -euo pipefail
umask 077
ROOT=/localhome/local-rohing/orch_r207_caption_contrast_20260918
JUDGES=/localhome/local-rohing/orch_r177_ampere_judge_20260917
cd "$ROOT/source"
export CUDA_VISIBLE_DEVICES=GPU-5b370d4d-bdcc-21d5-cf06-e9bea52e602d
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false
export PYTHONPATH="$ROOT/source" PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2
PYTHON=/localhome/local-rohing/v2/venv/bin/python
for ARM in widegap bt8k; do
    if [[ "$ARM" == widegap ]]; then CONFIG="$JUDGES/bt_widegap_v2/training/judge_config.json"; else CONFIG="$JUDGES/bt_qwen_v2/training/judge_config.json"; fi
    "$PYTHON" -B -m gpu.ny_caption_contrast --judge-config "$CONFIG" --data-config "$JUDGES/bt_widegap_v2/training/judge_config.json" --name "$ARM" --output "$ROOT/$ARM" --batch-size 8
done
