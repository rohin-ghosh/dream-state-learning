#!/usr/bin/env bash
set -euo pipefail
umask 077
ROOT=/localhome/local-rohing/orch_r212_matched_caption_games_20260918
INPUT=/localhome/local-rohing/orch_r209_first_caption_game_20260918
SOURCE=/localhome/local-rohing/orch_r212_caption_service_20260918/source
export CUDA_VISIBLE_DEVICES=GPU-5b370d4d-bdcc-21d5-cf06-e9bea52e602d
export PYTHONPATH="$SOURCE:$INPUT/source"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 TOKENIZERS_PARALLELISM=false
for MODE in base c2; do
    /localhome/local-rohing/v2/venv/bin/python -B -m gpu.ny_caption_relative_game \
        --game-manifest /localhome/local-rohing/rohin206_games_20260918/vision_node4_r209/GAME_MANIFEST.json \
        --data-manifest "$INPUT/inputs/DEVELOPMENT_MANIFEST.private.json" \
        --image-map "$INPUT/inputs/GAME_IMAGE_MAP.json" \
        --judge-config /localhome/local-rohing/orch_r207_caption_contrast_20260918/widegap_runtime/scalar_runtime.json \
        --encoder-manifest "$INPUT/similarity/embedding_snapshot.json" \
        --pixel-config "$INPUT/similarity/pixel_config.json" \
        --relevance-config "$INPUT/RELEVANCE_PROBE.json" \
        --captions "$ROOT/$MODE/actions.json" --output "$ROOT/${MODE}_game" \
        --agent-id "R212-frozen-$MODE" --lane MATCHED_FROZEN_DEVELOPMENT \
        --panel-size 64 --top-k 50 --seed 207
done
