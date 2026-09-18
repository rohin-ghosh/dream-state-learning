#!/usr/bin/env bash
set -euo pipefail
ROOT=/localhome/local-rohing/orch_r210_caption_service_20260918
INPUT=/localhome/local-rohing/orch_r209_first_caption_game_20260918
export CUDA_VISIBLE_DEVICES=GPU-5b370d4d-bdcc-21d5-cf06-e9bea52e602d
export PYTHONPATH="$ROOT/source:$INPUT/source"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 TOKENIZERS_PARALLELISM=false
cd "$ROOT/source"
exec /localhome/local-rohing/v2/venv/bin/python -B -m gpu.ny_caption_life_service \
    --game-manifest /localhome/local-rohing/rohin206_games_20260918/vision_node4_r209/GAME_MANIFEST.json \
    --data-manifest "$INPUT/inputs/DEVELOPMENT_MANIFEST.private.json" \
    --image-map "$INPUT/inputs/GAME_IMAGE_MAP.json" \
    --judge-config /localhome/local-rohing/orch_r207_caption_contrast_20260918/widegap_runtime/scalar_runtime.json \
    --encoder-manifest "$INPUT/similarity/embedding_snapshot.json" \
    --pixel-config "$INPUT/similarity/pixel_config.json" \
    --relevance-config "$INPUT/RELEVANCE_PROBE.json" \
    --life-root /localhome/local-rohing/orch_r201_node4_20260918/node4/R195_FLEET/SCALE_physical3/life \
    --agent-id C2-SCALE3-R210-caption --socket /tmp/r210_caption_n4.sock \
    --output "$ROOT/session1" --seconds 21600
