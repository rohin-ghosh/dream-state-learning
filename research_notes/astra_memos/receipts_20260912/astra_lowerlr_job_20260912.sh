#!/bin/bash
set -euo pipefail
RUN="$1"
RATE="$2"
SOURCE="$HOME/astra_sources/52e0e4db0d67d54defa4151cb091ccc925cd9e8c"
PY="$HOME/v2/venv/bin/python"
CORPUS="$RUN/corpora/bank0/F_r16k16/across/sleep4/corpus.json"
ADAPTER="$RUN/adapters/bank0/F_r16k16/across/sleep4/r8"
TAG=bank0__F_r16k16__across__sleep4__r8
test ! -e "$ADAPTER"
date -u
"$PY" -B "$SOURCE/organism_v6/memory_dose.py" train --run-dir "$RUN" --corpus "$CORPUS" --out "$ADAPTER" --model hf --rank 8 --epochs 3 --lr "$RATE" --seed 2 --no-reuse
test -f "$ADAPTER/DONE"
jq -e --argjson rate "$RATE" '.lr == $rate and .seed == 2 and .rank == 8 and .epochs == 3 and .steps == 9693 and .total_steps == 9693 and .n_items == 12924 and .tokens == 749985 and .supervised_tokens == 711213 and .boundary_straddles == 0 and .truncated_items == 0 and .measure_only == false and .throughput.grad_checkpoint == false and .corpus_sha == "15adaeff18a685c0" and .items_sha == "55e5bca9dadd19ea"' "$ADAPTER/train_meta.json"
"$PY" -B "$SOURCE/organism_v6/memory_dose.py" evaluate --run-dir "$RUN" --bank 0 --adapter "$ADAPTER" --tag "$TAG" --model hf --lambdas 1 --adjacent-subset 4 --batch-size 16 --seed 0 --cell F_r16k16 --arm across --sleep 4 --rank 8
jq -e '.n_cues == 1313 and .template_check == true and .abstain_check.ok == true' "$RUN/eval/${TAG}__lam1.json"
"$PY" -B "$SOURCE/organism_v6/memory_dose.py" report --run-dir "$RUN" --seed 0
sha256sum "$CORPUS" "$ADAPTER/train_meta.json" "$RUN/eval/${TAG}__lam1.json" "$RUN/report/report.json"
date -u
