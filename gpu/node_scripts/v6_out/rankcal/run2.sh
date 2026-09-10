#!/bin/bash
# Node-2 share of rank calibration: medium+large cells, one per GPU, parallel.
cd ~/dream-state
export HF_HUB_OFFLINE=1 CUDA_HOME=/usr/local/cuda-13.0 PATH=/usr/local/cuda-13.0/bin:$HOME/v2/venv/bin:$PATH
P=~/v2/venv/bin/python
g=0
for R in 8 16; do for S in medium large; do
  D=~/v6_out/rankcal/r${R}_${S}
  (CUDA_VISIBLE_DEVICES=$g $P -m organism_v6.train_adapter_v21 --corpus ~/v6_out/rankcal/corpus_${S}.json --out $D/adapter --rank $R --epochs 2 --lr 3e-5 && echo "CELL r${R}_${S} trained" > $D/TRAINED) > ~/v6_out/rankcal/r${R}_${S}.out 2>&1 < /dev/null &
  g=$((g+1))
done; done
echo "RANKCAL_N2_LAUNCHED 4 cells on GPUs 0-3"
