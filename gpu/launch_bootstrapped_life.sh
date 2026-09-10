#!/bin/bash
# Launch a life seeded with a bootstrap adapter (Stage 1 → Stage 2/3).
# Usage: bash gpu/launch_bootstrapped_life.sh <gpu> <seed> <bootstrap_dir> <prefix R6|R7> [parent_url parent_model]
# R6 = bootstrap + gate + parent; R7 = bootstrap + gate (no parent).
G="${1:?gpu}"; S="${2:?seed}"; B="${3:?bootstrap dir with adapter/}"; P="${4:?prefix}"; URL="$5"; MODEL="$6"
cd ~/dream-state
export HF_HUB_OFFLINE=1 CUDA_HOME=/usr/local/cuda-13.0 PATH=/usr/local/cuda-13.0/bin:$HOME/v2/venv/bin:$PATH
L=~/v6_out/${P}_B_seed$S
test -f "$B/TRAINED" || { echo "bootstrap not trained: $B" >&2; exit 2; }
mkdir -p "$L/sleep_0000" && cp -r "$B/adapter" "$L/sleep_0000/adapter" && touch "$L/sleep_0000/adapter/DONE" \
  && cp "$B/corpus_meta.json" "$L/sleep_0000/bootstrap_meta.json" 2>/dev/null; echo "$B" > "$L/BOOTSTRAP_SOURCE"
EXTRA="--probe-gate"; [ -n "$URL" ] && EXTRA="$EXTRA --parent-url $URL --parent-model $MODEL"
nohup env CUDA_VISIBLE_DEVICES="$G" ~/v2/venv/bin/python -m organism_v6.run_life_v2 --life-dir "$L" --arm B --seed "$S" \
  --episodes 1024 --sleep-every 32 --probe-every 64 --budget-ticks 16 --wake-batch 8 --rank 8 $EXTRA > ~/v6_out/${P}_B_seed$S.out 2>&1 < /dev/null &
echo "launched ${P}_B_seed$S on GPU $G from $B $EXTRA"
