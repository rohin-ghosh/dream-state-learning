#!/bin/bash
# Night queue for node 1 (2026-09-11 evening). Run ON node 1 from ~/dream-state after gpu/queue_install.sh 1.
# Jobs are drained onto free GPUs by gpu/queue_runner.sh (never onto a GPU a life or a running chain holds).
cd ~/dream-state || exit 1
Q=gpu/queue_add.sh
# Exposure-parity abstention (F_r16k16_neg64) on the seed-0 banks: node-1 replication of the node-2 cell (SEQ-041/042)
for b in 0 1 2; do
  bash $Q "neg64_s0_b$b" "RUN=\$HOME/v6_out/memory_dose F_CELLS=F_r16k16_neg64 F_BANKS=$b F_TOKEN_BUDGET=250000 FORCE=1 bash gpu/memory_dose_frames.sh {gpu} fits"
done
AFTER=neg64_s0_b2 bash $Q "neg64_s0_report" "RUN=\$HOME/v6_out/memory_dose bash gpu/memory_dose_frames.sh {gpu} report"
# Same cell on the fresh-owner banks (seed 1) once the rank-8/32 replication chains free their GPUs
for b in 0 1 2; do
  bash $Q "conf_neg64_b$b" "RUN=\$HOME/v6_out/memory_dose_conf SEED=1 F_CELLS=F_r16k16_neg64 F_BANKS=$b F_TOKEN_BUDGET=250000 FORCE=1 bash gpu/memory_dose_frames.sh {gpu} fits"
done
AFTER=conf_neg64_b2 bash $Q "conf_report" "RUN=\$HOME/v6_out/memory_dose_conf SEED=1 bash gpu/memory_dose_frames.sh {gpu} report"
bash gpu/queue_status.sh
