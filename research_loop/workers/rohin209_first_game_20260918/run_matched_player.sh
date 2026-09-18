#!/usr/bin/env bash
set -euo pipefail
umask 077
ROOT=/localhome/local-rohing/orch_r212_matched_caption_players_20260918
MODE="${1:?base or c2 required}"
case "$MODE" in
    base) GPU=GPU-c57b2860-9ba6-74ee-876b-4fa22a10366e; EXTRA=() ;;
    c2) GPU=GPU-02917283-de83-a2c7-db03-272dca482162; EXTRA=(--adapter-root "$ROOT/seed/complete/adapter") ;;
    *) exit 2 ;;
esac
exec 9>"$ROOT/$MODE.lock"
flock -n 9
ACTIVE="$(nvidia-smi --query-compute-apps=gpu_uuid --format=csv,noheader)"
if printf '%s\n' "$ACTIVE" | grep -Fxq "$GPU"; then echo 'Assigned GPU occupied; no launch.'; exit 3; fi
export CUDA_VISIBLE_DEVICES="$GPU" PYTHONPATH="$ROOT/source"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 TOKENIZERS_PARALLELISM=false
cd "$ROOT/source"
exec /localhome/local-rohing/v2/venv/bin/python -B -m research_loop.workers.rohin209_first_game_20260918.matched_players \
    --mode "$MODE" --base-root /localhome/local-rohing/.cache/huggingface/hub/models--Qwen--Qwen2.5-7B-Instruct/snapshots/a09a35458c702b33eeacc393d103063234e8bc28 \
    --game-manifest "$ROOT/inputs/GAME_MANIFEST.json" --output "$ROOT/$MODE" "${EXTRA[@]}"
