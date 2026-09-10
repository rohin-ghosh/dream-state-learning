#!/bin/bash
G=$1; R=$2; SD=$3; cd ~/dream-state; export HF_HUB_OFFLINE=1 CUDA_HOME=/usr/local/cuda-13.0 PATH=/usr/local/cuda-13.0/bin:$HOME/v2/venv/bin:$PATH
P=~/v2/venv/bin/python; D=~/v6_out/rankcal/r${R}_large_s$SD; mkdir -p $D
CUDA_VISIBLE_DEVICES=$G $P -m organism_v6.train_adapter_v21 --corpus ~/v6_out/rankcal/corpus_large.json --out $D/adapter --rank $R --epochs 2 --lr 3e-5 --seed $SD > $D/train.out 2>&1 && touch $D/TRAINED && CUDA_VISIBLE_DEVICES=$G $P -m organism_v6.probe_adapter --out $D/probe.json --adapter $D/adapter --reps 2 > $D/probe.out 2>&1 && echo REP_DONE_r${R}_s$SD || echo REP_FAILED_r${R}_s$SD
