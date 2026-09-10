#!/bin/bash
# waits for GPU 7 to free (RP402 finishing), then trains the three bootstrap adapters sequentially (v3 clean candidate first)
cd ~/dream-state; export HF_HUB_OFFLINE=1 CUDA_HOME=/usr/local/cuda-13.0 PATH=/usr/local/cuda-13.0/bin:$HOME/v2/venv/bin:$PATH
for i in $(seq 1 240); do m=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits -i 7 | tr -d ' '); [ "$m" -lt 1000 ] && break; sleep 60; done
[ "$m" -lt 1000 ] || { echo GPU7_NEVER_FREED; exit 1; }
for v in 3 2 1; do
  D=~/v6_out/bootstrap_v$v
  CUDA_VISIBLE_DEVICES=7 ~/v2/venv/bin/python -m organism_v6.train_adapter_v21 --corpus $D/corpus.json --out $D/adapter --rank 8 --epochs 2 --lr 3e-5 --seed 0 > $D/train.out 2>&1 && touch $D/TRAINED && echo BOOTSTRAP_v${v}_TRAINED || echo BOOTSTRAP_v${v}_TRAIN_FAILED
done
echo BOOTSTRAPS_DONE
