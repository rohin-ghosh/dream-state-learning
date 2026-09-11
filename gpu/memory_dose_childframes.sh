#!/bin/bash
# Memory dose-response ("car") test -- cell family CF "child-authored frames", the BRIDGE experiment (Rohin's
# foundational ruling 2026-09-11 evening; research_notes/THESIS_PARENTING_AS_MECHANISM_MATCHING.md section 1.2).
# The same planted events, cues, metrics and gates as gpu/memory_dose_frames.sh, but the R renderings per
# occurrence are WRITTEN BY THE CHILD (frozen Qwen2.5-7B-Instruct, offline vllm) instead of drawn from templates;
# the synthetic-vs-child gap (F_r16k16 vs CF_r16_a/b/c) is the measure of the perception skill. ONE GPU, staged,
# resumes on rerun. Runs AFTER gpu/memory_dose.sh stage 0 (banks + distractor must exist in $RUN).
#   generate  ONE model load writes corpora/bank*/<cell>/across/sleep4/generations.json for every CF cell in CF_CELLS
#             and bank in F_BANKS that lacks it (existing files are reused untouched; every raw generation + prompt is
#             kept, so the corpus is reproducible without the GPU), then builds each CF corpus from those generations
#             (CPU; the corpus records the perception diagnostics in stats.child). MODEL=mock uses the mock child.
#   fits      train + eval exactly as memory_dose_frames.sh (rank F_RANK, across arm, sleep 4, banks F_BANKS, 25-min
#             cap with a 100-step probe, FORCE=1 overrides). The corpus is REUSED from disk; if it is missing the build
#             runs with --child-backend none, i.e. it needs generations.json and never loads the vllm model here.
#   report    python -m organism_v6.memory_dose report; touch STAGE_CF_DONE (summary.md gets the CF diagnostics table
#             and '### Synthetic vs child-authored (the bridge)' when F_r16k16 evals exist).
# Evals are never overwritten (an existing eval JSON is kept; adapters carry DONE and are reused).
# SYNTHETIC, researcher-planted facts; disposable mechanism test; every output carries synthetic=true; nothing here
# may be merged into a taught lineage. No hostnames in this file: run it ON the node.
#
# Usage (on a node):  bash gpu/memory_dose_childframes.sh <gpu> [step]     step in {generate,fits,report,all} (default all)
# Env overrides:      RUN=~/v6_out/memory_dose  SEED=0  PY=~/v2/venv/bin/python  REPO=~/dream-state  MODEL=hf|mock
#                     MAX_FIT_MIN=25 (abort a cell's fits if the probe projects a longer fit; FORCE=1 overrides)
#                     F_TOKEN_BUDGET= (tokens per CF corpus; empty = the cell's default 400,000; the corpus records it and
#                       a corpus on disk at a different budget ABORTs like memory_dose_frames.sh)
#                     F_RANK=8  ORDERING=chronological (must match the run's other corpora)
#                     CF_CELLS="CF_r16_a CF_r16_b CF_r16_c"  F_BANKS="0 1 2"
#                     CF_ALLOW_OVER_BUDGET=1 (the child's renderings are as long as it makes them: a corpus whose content
#                       exceeds the budget is still built and trained, recorded over_budget=true; 0 = abort as F does)
# Node run (banks 0-2, the F node budget so the comparison with F_r16k16 is at the same budget):
#   F_TOKEN_BUDGET=250000 FORCE=1 bash gpu/memory_dose_childframes.sh <gpu> generate
#   F_TOKEN_BUDGET=250000 FORCE=1 bash gpu/memory_dose_childframes.sh <gpu> fits && bash gpu/memory_dose_childframes.sh <gpu> report
# Budget: generation ~336 prompts x 16 lines per (cell, bank) + 16 negative prompts for c (one vllm load, minutes);
# 9 fits at ~250-400k tokens each + 9 evals, as the F cells.
G="${1:?gpu index}"; STEP="${2:-all}"
cd "${REPO:-$HOME/dream-state}" || exit 2
export HF_HUB_OFFLINE=1 CUDA_HOME=/usr/local/cuda-13.0 PATH=/usr/local/cuda-13.0/bin:$HOME/v2/venv/bin:$PATH
export CUDA_VISIBLE_DEVICES="$G"
P="${PY:-$HOME/v2/venv/bin/python}"; RUN="${RUN:-$HOME/v6_out/memory_dose}"; SEED="${SEED:-0}"; MODEL="${MODEL:-hf}"
MAX_FIT_MIN="${MAX_FIT_MIN:-25}"; ORDERING="${ORDERING:-chronological}"
CF_CELLS="${CF_CELLS:-CF_r16_a CF_r16_b CF_r16_c}"; F_BANKS="${F_BANKS:-0 1 2}"
F_TOKEN_BUDGET="${F_TOKEN_BUDGET:-}"   # empty = each CF cell's own default budget (FRAME_TOKEN_BUDGET, 400,000)
F_RANK="${F_RANK:-8}"                   # LoRA rank for the CF fits (8 = the car test's default; 32 = the planned memory-block rank)
CF_ALLOW_OVER_BUDGET="${CF_ALLOW_OVER_BUDGET:-1}"
[[ "$F_RANK" =~ ^[0-9]+$ ]] || { echo "F_RANK must be an integer"; exit 2; }
[ -z "$F_TOKEN_BUDGET" ] || [[ "$F_TOKEN_BUDGET" =~ ^[0-9]+$ ]] || { echo "F_TOKEN_BUDGET must be an integer (tokens)"; exit 2; }
MD="$P -m organism_v6.memory_dose"
mkdir -p "$RUN/eval" "$RUN/logs"
log() { echo "[$(date '+%F %T')] $*" | tee -a "$RUN/logs/runbook_childframes.log"; }
[ -f "$RUN/manifest.json" ] && [ -f "$RUN/distractor.json" ] || { log "ABORT: no banks in $RUN -- run gpu/memory_dose.sh <gpu> 0 first"; exit 2; }
child_backend() { [ "$MODEL" = mock ] && echo mock || echo vllm; }

cf_corpus() {  # bank cell arm sleep -- the CF corpus at F_TOKEN_BUDGET (else the cell's default) from generations.json;
  local b=$1 c=$2 a=$3 k=$4       # resume if already built; never loads the vllm model (--child-backend none)
  local corpus="$RUN/corpora/bank$b/$c/$a/sleep$k/corpus.json" tag="bank${b}__${c}__${a}__sleep${k}"
  if [ -f "$corpus" ]; then
    [ -n "$F_TOKEN_BUDGET" ] || return 0
    local have; have=$($P -c "import json;print(json.load(open('$corpus'))['token_budget'])")
    [ "$have" = "$F_TOKEN_BUDGET" ] && return 0
    log "ABORT $tag: corpus on disk was built at budget $have, F_TOKEN_BUDGET=$F_TOKEN_BUDGET; remove" \
        "$RUN/corpora/bank$b/$c/$a/sleep$k/corpus.json and $RUN/adapters/bank$b/$c to rebuild at the new budget" \
        "(adapters are keyed by corpus sha; generations.json is kept and reused)"
    return 3
  fi
  local allow=""; [ "$CF_ALLOW_OVER_BUDGET" = 1 ] && allow="--allow-over-budget"
  $MD corpus --run-dir "$RUN" --bank "$b" --cell "$c" --arm "$a" --sleep "$k" --model "$MODEL" --ordering "$ORDERING" \
      --child-backend none $allow ${F_TOKEN_BUDGET:+--token-budget "$F_TOKEN_BUDGET"} > "$RUN/logs/corpus_$tag.out" 2>&1 \
      || { log "CORPUS FAILED $tag: $(grep -o 'CORPUS_[A-Z_]*.*' "$RUN/logs/corpus_$tag.out" | tail -1 | head -c 300)"; return 1; }
  log "corpus $tag: $(grep -o 'CORPUS_DONE.*' "$RUN/logs/corpus_$tag.out" | tail -1 | sed 's/^CORPUS_DONE [^ ]* //')"
}

generate() {  # one child writer for every (cell, bank) lacking generations.json, then the CF corpora (CPU)
  local c b
  $MD childgen --run-dir "$RUN" --cells "$CF_CELLS" --banks "$F_BANKS" --arm across --sleep 4 \
      --child-backend "$(child_backend)" > "$RUN/logs/childgen.out" 2>&1 \
      || { log "CHILDGEN FAILED (see logs/childgen.out): $(tail -c 400 "$RUN/logs/childgen.out")"; exit 1; }
  log "$(grep -o 'CHILDGEN_DONE.*' "$RUN/logs/childgen.out" | tail -1)"
  for c in $CF_CELLS; do for b in $F_BANKS; do cf_corpus "$b" "$c" across 4 || exit $?; done; done
  touch "$RUN/STAGE_CF_GENERATE_DONE"; log "CF generate done"
}

fit_cap() {  # cell -- 100-step throughput probe on the cell's corpus at the FIRST bank of F_BANKS; abort over the cap
  local c=$1 first _rest; read -r first _rest <<< "$F_BANKS"   # not bank 0: F_BANKS="1 2" has no bank-0 generations.json
  local corpus="$RUN/corpora/bank$first/$c/across/sleep4/corpus.json" probe="$RUN/adapters/throughput_probe_$c"
  cf_corpus "$first" "$c" across 4 || return $?
  [ "$MODEL" = hf ] || return 0
  if [ ! -f "$probe/MEASURED" ]; then
    $MD train --run-dir "$RUN" --corpus "$corpus" --out "$probe" --model "$MODEL" --rank 8 --measure-only --max-steps 100 \
        > "$RUN/logs/throughput_$c.out" 2>&1 || { log "THROUGHPUT PROBE FAILED $c (see logs/throughput_$c.out)"; return 1; }
  fi
  local proj tps
  proj=$($P -c "import json;print(json.load(open('$probe/throughput.json'))['projected_fit_minutes'])")
  tps=$($P -c "import json;print(json.load(open('$probe/throughput.json'))['tokens_per_s'])")
  log "THROUGHPUT $c 100 steps: $tps tok/s; projected $proj min per fit (cap $MAX_FIT_MIN min)"
  if [ "${FORCE:-0}" != 1 ] && $P -c "import sys; sys.exit(0 if float('$proj') > float('$MAX_FIT_MIN') else 1)"; then
    log "ABORT $c: projected $proj min > MAX_FIT_MIN=$MAX_FIT_MIN; rerun with a smaller F_TOKEN_BUDGET=<tokens>" \
        "(after removing $RUN/corpora/bank*/$c/*/sleep4/corpus.json and $RUN/adapters/*$c*), a larger MAX_FIT_MIN, or FORCE=1"; return 3
  fi
}

fit_eval() {  # bank cell arm sleep rank [lambdas] -- as memory_dose_frames.sh: corpus (reused), train (reuse by sha), evaluate
  local b=$1 c=$2 a=$3 k=$4 r=$5 lams=${6:-1}
  local corpus="$RUN/corpora/bank$b/$c/$a/sleep$k/corpus.json" ad="$RUN/adapters/bank$b/$c/$a/sleep$k/r$r"
  local tag="bank${b}__${c}__${a}__sleep${k}__r$r"
  cf_corpus "$b" "$c" "$a" "$k" || return $?
  if [ ! -f "$ad/DONE" ]; then
    $MD train --run-dir "$RUN" --corpus "$corpus" --out "$ad" --model "$MODEL" --rank "$r" --epochs 3 --lr 1e-4 \
        --seed "$SEED" > "$RUN/logs/train_$tag.out" 2>&1 || { log "TRAIN FAILED $tag"; return 1; }
    log "train $tag: $(grep -o 'TRAIN_[A-Z]*.*' "$RUN/logs/train_$tag.out" | tail -1)"
  fi
  if [ ! -f "$RUN/eval/${tag}__lam1.json" ] || [ "$lams" != 1 ]; then
    $MD evaluate --run-dir "$RUN" --bank "$b" --adapter "$ad" --tag "$tag" --model "$MODEL" --lambdas "$lams" \
        --cell "$c" --arm "$a" --sleep "$k" --rank "$r" > "$RUN/logs/eval_$tag.out" 2>&1 || { log "EVAL FAILED $tag"; return 1; }
    log "eval $tag: $(grep -o 'EVAL_DONE.*' "$RUN/logs/eval_$tag.out" | tail -1)"
  fi
}

fits() {  # CF cells x banks, rank F_RANK, across arm, sleep 4; the cap is checked once per cell
  local c b
  for c in $CF_CELLS; do
    fit_cap "$c" || exit $?
    for b in $F_BANKS; do fit_eval "$b" "$c" across 4 "$F_RANK" || exit $?; done
  done
  touch "$RUN/STAGE_CF_FITS_DONE"; log "CF fits done"
}

report() {
  $MD report --run-dir "$RUN" > "$RUN/logs/report_childframes.out" 2>&1 || { log "REPORT FAILED"; exit 1; }
  log "$(grep -o 'REPORT_DONE.*' "$RUN/logs/report_childframes.out")"
  touch "$RUN/STAGE_CF_DONE"; log "stage CF done -> $RUN/report/summary.md (sections 'Child-authored frames' and 'Synthetic vs child-authored (the bridge)')"
}

case "$STEP" in
  generate) generate ;;
  fits) fits ;;
  report) report ;;
  all) generate; fits; report ;;
  *) echo "unknown step $STEP"; exit 2 ;;
esac
log "MEMORY_DOSE_CHILDFRAMES_DONE step=$STEP"
