#!/bin/bash
# Parented fixed-writer lives (RP arm) and gated+parented lives (R4 arm).
# Usage (on a node):
#   bash gpu/launch_RP_lives.sh "<gpu:seed ...>" <parent_url> <parent_model> [prefix] [extra flags...]
# e.g. bash gpu/launch_RP_lives.sh "2:400 7:401" http://127.0.0.1:8011/v1 Qwen/Qwen2.5-14B-Instruct RP
#      bash gpu/launch_RP_lives.sh "1:600" http://127.0.0.1:8011/v1 Qwen/Qwen2.5-14B-Instruct R4 --probe-gate
SPECS="${1:?gpu:seed list}"; URL="${2:?parent url}"; MODEL="${3:?parent model}"; PREFIX="${4:-RP}"; shift 4 2>/dev/null || shift $#
EXTRA="$@"
cd ~/dream-state
export HF_HUB_OFFLINE=1 CUDA_HOME=/usr/local/cuda-13.0 PATH=/usr/local/cuda-13.0/bin:$HOME/v2/venv/bin:$PATH
for spec in $SPECS; do
  G="${spec%%:*}"; S="${spec##*:}"
  nohup env CUDA_VISIBLE_DEVICES="$G" ~/v2/venv/bin/python -m organism_v6.run_life_v2 \
    --life-dir ~/v6_out/${PREFIX}_B_seed$S --arm B --seed "$S" --episodes 1024 --sleep-every 32 \
    --probe-every 64 --budget-ticks 16 --wake-batch 8 --rank 8 \
    --parent-url "$URL" --parent-model "$MODEL" $EXTRA > ~/v6_out/${PREFIX}_B_seed$S.out 2>&1 < /dev/null &
  echo "launched ${PREFIX}_B_seed$S on GPU $G (parent $MODEL) $EXTRA"
done
