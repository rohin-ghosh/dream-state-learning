#!/bin/bash
# v6.2 seeded replication: canary-gated writer, common-random probes,
# seeded wake. 3 A + 3 B lives, GPUs 0-5, seeds 200-202.
cd ~/dream-state
for i in 0 1 2; do
  s=$((200+i))
  HF_HUB_OFFLINE=1 CUDA_VISIBLE_DEVICES=$i nohup ~/v2/venv/bin/python -m organism_v6.run_life_v2 \
    --life-dir ~/v6_out/R_A_seed$i --arm A --seed $s --episodes 1024 \
    --sleep-every 32 --probe-every 64 --budget-ticks 16 --wake-batch 8 --rank 8 \
    > ~/v6_out/R_A_seed$i.out 2>&1 < /dev/null &
  g=$((i+3))
  HF_HUB_OFFLINE=1 CUDA_VISIBLE_DEVICES=$g nohup ~/v2/venv/bin/python -m organism_v6.run_life_v2 \
    --life-dir ~/v6_out/R_B_seed$i --arm B --seed $s --episodes 1024 \
    --sleep-every 32 --probe-every 64 --budget-ticks 16 --wake-batch 8 --rank 8 \
    > ~/v6_out/R_B_seed$i.out 2>&1 < /dev/null &
done
echo "V62_LAUNCHED (seeded, canary-gated, rank 8)"
