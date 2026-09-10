#!/bin/bash
# GPU $1, gen-seed $2, exam eids $3: server-parent round then matched self-parent control, exam widened
G=$1; SEED=$2; NE=$3; cd ~/dream-state; export HF_HUB_OFFLINE=1 CUDA_HOME=/usr/local/cuda-13.0 PATH=/usr/local/cuda-13.0/bin:$HOME/v2/venv/bin:$PATH V6_PARENT_MODEL=Qwen/Qwen2.5-14B-Instruct
P=~/v2/venv/bin/python
for mode in server self; do
  L=~/v6_out/parent_scout_${mode}_s${SEED}_e$NE
  for ph in live sleep exam; do
    CUDA_VISIBLE_DEVICES=$G $P -m organism_v6.classroom_round --lineage $L --round 0 --classrooms 8 --lessons 4 --phase $ph --parent $mode --gen-seed $SEED --exam-eids $NE > $L.$ph.out 2>&1 || { echo SCOUT_${mode}_${ph}_FAILED_s$SEED; break; }
  done
  echo SCOUT_${mode}_DONE_s$SEED
done
echo PARENT_SCOUT_E40_DONE_s$SEED
