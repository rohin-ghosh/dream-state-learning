#!/bin/bash
set -euo pipefail
umask 077
ROOT=/localhome/local-rohing/orch_r209_first_caption_game_20260918
CAPTIONS="${1:-$ROOT/c2_proposals/actions.json}"
OUTPUT="${2:-$ROOT/game}"
if [[ $# -eq 0 ]]; then
    for CHECK in $(seq 1 120); do
        if [[ -f "$ROOT/c2_proposals/FAILED.json" ]]; then
            echo 'Child proposal failed; raw attempt retained, no substitute caption.'
            exit 1
        fi
        if [[ -f "$ROOT/c2_proposals/RESULT.json" ]]; then break; fi
        sleep 5
    done
    test -f "$ROOT/c2_proposals/RESULT.json"
fi
test -f "$CAPTIONS"
cd "$ROOT/source"
export CUDA_VISIBLE_DEVICES=GPU-5b370d4d-bdcc-21d5-cf06-e9bea52e602d
export PYTHONPATH="$ROOT/source" HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1
exec /localhome/local-rohing/v2/venv/bin/python -B -m gpu.ny_caption_relative_game \
    --game-manifest /localhome/local-rohing/rohin206_games_20260918/vision_node4_r209/GAME_MANIFEST.json \
    --data-manifest "$ROOT/inputs/DEVELOPMENT_MANIFEST.private.json" \
    --image-map "$ROOT/inputs/GAME_IMAGE_MAP.json" \
    --judge-config /localhome/local-rohing/orch_r207_caption_contrast_20260918/widegap_runtime/scalar_runtime.json \
    --encoder-manifest "$ROOT/similarity/embedding_snapshot.json" \
    --pixel-config "$ROOT/similarity/pixel_config.json" \
    --relevance-config "$ROOT/RELEVANCE_PROBE.json" \
    --captions "$CAPTIONS" --output "$OUTPUT" \
    --agent-id C2-snapshot51-inference --lane FROZEN_FIRST_GAME --panel-size 64 --top-k 8
