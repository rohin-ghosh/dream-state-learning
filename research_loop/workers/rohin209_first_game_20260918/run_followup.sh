#!/usr/bin/env bash
set -euo pipefail
ROOT=/localhome/local-rohing/orch_r209_first_caption_game_20260918
export CUDA_VISIBLE_DEVICES=GPU-5b370d4d-bdcc-21d5-cf06-e9bea52e602d
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 TOKENIZERS_PARALLELISM=false
exec /localhome/local-rohing/v2/venv/bin/python -B "$ROOT/followup_c2.py" \
    --game-manifest /localhome/local-rohing/rohin206_games_20260918/vision_node4_r209/GAME_MANIFEST.json \
    --base-root /localhome/local-rohing/orch_r177_ampere_judge_20260917/bt_qwen_model_v1 \
    --adapter-root "$ROOT/seed/complete/adapter" \
    --previous-proposals "$ROOT/c2_proposals" \
    --scored-actions "$ROOT/c2_literal_fields/actions.json" \
    --game-output "$ROOT/game" \
    --output "$ROOT/c2_feedback_followup1"
