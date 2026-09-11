#!/bin/bash
# Night queue for node 2 (2026-09-11 evening). Run ON node 2 from ~/dream-state after gpu/queue_install.sh 2.
cd ~/dream-state || exit 1
Q=gpu/queue_add.sh
# rank 32 for the one-form cell (completes the rank-32 trio: k16 and k4 already running)
for b in 0 1 2; do
  bash $Q "k1_r32_b$b" "RUN=\$HOME/v6_out/memory_dose_D32 F_CELLS=F_r16k1 F_BANKS=$b F_TOKEN_BUDGET=250000 F_RANK=32 FORCE=1 bash gpu/memory_dose_frames.sh {gpu} fits"
done
# exposure-parity abstention, bank 2 (banks 0 and 1 were trained by a concurrent launch; SEQ-042)
bash $Q "neg64_b2" "RUN=\$HOME/v6_out/memory_dose_D32 F_CELLS=F_r16k16_neg64 F_BANKS=2 F_TOKEN_BUDGET=250000 FORCE=1 bash gpu/memory_dose_frames.sh {gpu} fits"
AFTER=neg64_b2 bash $Q "d32_report_a" "RUN=\$HOME/v6_out/memory_dose_D32 bash gpu/memory_dose_frames.sh {gpu} report"
# sixth-life write pretest: R2 seed3, the life whose final brief and adapter were both below the frozen model (SEQ-023/031)
bash $Q "seed3_pretest" "bash gpu/write_ab.sh {gpu} \$HOME/v6_out/R2_B_seed3 512"
AFTER=k1_r32_b2 bash $Q "d32_report_b" "RUN=\$HOME/v6_out/memory_dose_D32 bash gpu/memory_dose_frames.sh {gpu} report"
bash gpu/queue_status.sh
