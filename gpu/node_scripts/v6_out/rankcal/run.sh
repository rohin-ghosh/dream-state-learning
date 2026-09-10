#!/bin/bash
# Rank calibration: corpus size {small,medium,large} x rank {8,16}, same dose.
# GPU6: rank 8 series; GPU7: rank 16 series. Marker files per cell.
cd ~/dream-state
export HF_HUB_OFFLINE=1
P=~/v2/venv/bin/python
R=$1; G=$2
for S in small medium large; do
  D=~/v6_out/rankcal/r${R}_${S}
  if [ ! -f $D/probe.json ]; then
    CUDA_VISIBLE_DEVICES=$G $P -m organism_v6.train_adapter_v21 --corpus ~/v6_out/rankcal/corpus_${S}.json --out $D/adapter --rank $R --epochs 2 --lr 3e-5 \
      && CUDA_VISIBLE_DEVICES=$G $P -m organism_v6.probe_adapter --out $D/probe.json --adapter $D/adapter --reps 2
    echo "CELL r${R}_${S} done"
  fi
done
echo "RANKCAL_R${R}_DONE"
