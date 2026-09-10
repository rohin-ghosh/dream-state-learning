#!/bin/bash
# When node-1 rank-cal GPUs (6,7) free: run certification instruments.
cd ~/dream-state
export HF_HUB_OFFLINE=1 CUDA_HOME=/usr/local/cuda-13.0 PATH=/usr/local/cuda-13.0/bin:$HOME/v2/venv/bin:$PATH
P=~/v2/venv/bin/python
# wait for both large probes (or 6h)
for i in $(seq 1 72); do
  [ -f ~/v6_out/rankcal/r8_large/probe.json ] && [ -f ~/v6_out/rankcal/r16_large/probe.json ] && break
  sleep 300
done
echo "RANKCAL_DONE_OR_TIMEOUT $(date '+%H:%M')"
# GPU 6: rule-game noise band (8 reps). GPU 7: absorption/retention on R2 lives.
(CUDA_VISIBLE_DEVICES=6 $P -m organism_v6.rulegame_noise --out ~/v6_out/rulegame_noise.json --reps 8; echo NOISE_DONE) > ~/v6_out/rulegame_noise.out 2>&1 < /dev/null &
(for L in R2_B_seed0 R2_B_seed1; do CUDA_VISIBLE_DEVICES=7 $P -m organism_v6.absorption_probe --life ~/v6_out/$L --control-life ~/v6_out/R_B_seed0 --out ~/v6_out/$L/absorption.json; done; echo ABSORB_DONE) > ~/v6_out/absorption.out 2>&1 < /dev/null &
echo INSTRUMENTS_LAUNCHED
