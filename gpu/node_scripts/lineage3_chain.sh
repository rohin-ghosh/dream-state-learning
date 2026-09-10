#!/bin/bash
# GPU $1, gen-seed $2, exam eids $3, parent mode $4, url $5: a 3-round PREV-chained lineage
G=$1; SEED=$2; NE=$3; MODE=$4; URL=${5:-http://127.0.0.1:8011/v1}; cd ~/dream-state; export HF_HUB_OFFLINE=1 CUDA_HOME=/usr/local/cuda-13.0 PATH=/usr/local/cuda-13.0/bin:$HOME/v2/venv/bin:$PATH
P=~/v2/venv/bin/python; L=~/v6_out/lineage3_${MODE}_s${SEED}_e$NE
for r in 0 1 2; do for ph in live sleep exam; do
  CUDA_VISIBLE_DEVICES=$G $P -m organism_v6.classroom_round --lineage $L --round $r --classrooms 8 --lessons 4 --phase $ph --parent $MODE --parent-url $URL --gen-seed $SEED --exam-eids $NE > $L.r$r.$ph.out 2>&1 || { echo LINEAGE_${MODE}_r${r}_${ph}_FAILED_s$SEED; exit 1; }
done; echo LINEAGE_${MODE}_round${r}_done_s$SEED; done
echo LINEAGE3_DONE_${MODE}_s$SEED
