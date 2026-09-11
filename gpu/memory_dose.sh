#!/bin/bash
# Memory dose-response ("car") test -- Astra memo 2 (2026-09-10) section 2. ONE GPU, staged so the first writer
# result (the 2x2 at rank 8, dose arms collapsed) arrives first, then the finalist's four-sleep trajectories and
# interference sleeps, then rank 32 and the adapter-strength sweep.
# SYNTHETIC, researcher-planted facts; disposable mechanism test; every output carries synthetic=true; nothing here
# may be merged into a taught lineage. No hostnames in this file: run it ON the node.
#
# Usage (on a node):  bash gpu/memory_dose.sh <gpu> [stage]      stage in {0,1,2,3,all} (default all; each stage resumes)
# Env overrides:      RUN=~/v6_out/memory_dose  SEED=0  PY=~/v2/venv/bin/python  REPO=~/dream-state
#                     MAX_FIT_MIN=25 (abort if the measured 100-step throughput projects a longer fit; FORCE=1 overrides)
#                     TOKEN_BUDGET=65536  FINALIST=D (skip the report's choice)  MODEL=mock (CPU dry run of the staging)
#                     ORDERING=chronological (default: prior-first session order as compile_sleep + train_adapter.py, so the
#                       within-session and across-sleep sleep-4 corpora hold the SAME items in a DIFFERENT order and are fitted
#                       separately -- the memo's identity prediction is measured) | content (content-derived shuffle: identical
#                       item sets -> byte-identical corpora, the within-4 fit is reused by sha; sensitivity arm)
#                     PRIOR_MATCH=0 (default random balanced colour assignment after the OFF measurement; 1 = opt-in prior matching)
#                     WITHIN_CELLS="A" (cells besides the finalist whose within-session arm is fitted at sleep 4; A = today's writer)
# Budget (memo 2.6): 6-18 A40 GPU-h total; stage 1 ~ 15 fits + 15 evals; stage 2 ~ 18-24 fits + 24-27 evals (within-4 fits are
# real under ORDERING=chronological: +3 finalist, +3 per WITHIN_CELLS cell); stage 3 ~ 3 fits + 12 evals.
# Stage 0 ABORTS if any corpus's content exceeds TOKEN_BUDGET (no condition may silently differ in size).
G="${1:?gpu index}"; STAGE="${2:-all}"
cd "${REPO:-$HOME/dream-state}" || exit 2
export HF_HUB_OFFLINE=1 CUDA_HOME=/usr/local/cuda-13.0 PATH=/usr/local/cuda-13.0/bin:$HOME/v2/venv/bin:$PATH
export CUDA_VISIBLE_DEVICES="$G"
P="${PY:-$HOME/v2/venv/bin/python}"; RUN="${RUN:-$HOME/v6_out/memory_dose}"; SEED="${SEED:-0}"; MODEL="${MODEL:-hf}"
MAX_FIT_MIN="${MAX_FIT_MIN:-25}"; TOKEN_BUDGET="${TOKEN_BUDGET:-65536}"; ORDERING="${ORDERING:-chronological}"
PRIOR_MATCH="${PRIOR_MATCH:-0}"; WITHIN_CELLS="${WITHIN_CELLS:-A}"
MD="$P -m organism_v6.memory_dose"
mkdir -p "$RUN/eval" "$RUN/logs"
log() { echo "[$(date '+%F %T')] $*" | tee -a "$RUN/logs/runbook.log"; }

stage0() {  # banks (OFF measured BEFORE assignment), every corpus, then the 100-step throughput probe
  local pm=""; [ "$PRIOR_MATCH" = 1 ] && pm="--prior-match"
  [ -f "$RUN/manifest.json" ] || $MD generate --run-dir "$RUN" --seed "$SEED" --model "$MODEL" --banks 3 \
      --token-budget "$TOKEN_BUDGET" $pm > "$RUN/logs/generate.out" 2>&1 || { log "GENERATE FAILED"; exit 1; }
  [ -f "$RUN/corpora/index.json" ] || $MD corpus-all --run-dir "$RUN" --model "$MODEL" --cells A,B,C,D,Dshuf \
      --ordering "$ORDERING" > "$RUN/logs/corpus_all.out" 2>&1 \
      || { log "CORPUS_ALL FAILED: $(grep -o 'CORPUS_ALL_FAILED.*' "$RUN/logs/corpus_all.out" | head -c 300)"; exit 1; }
  log "$(grep -o 'CORPUS_ALL_DONE.*' "$RUN/logs/corpus_all.out")"
  if $P -c "import json,sys; sys.exit(0 if json.load(open('$RUN/corpora/index.json'))['over_budget'] else 1)"; then
    log "ABORT: corpus content exceeds TOKEN_BUDGET (see corpora/index.json over_budget); raise TOKEN_BUDGET and regenerate"; exit 3
  fi
  # throughput: 100 steps on the largest corpus (occurrences x antecedent, sleep 6), nothing saved
  if [ ! -f "$RUN/adapters/throughput_probe/MEASURED" ]; then
    $MD train --run-dir "$RUN" --corpus "$RUN/corpora/bank0/D/across/sleep6/corpus.json" \
        --out "$RUN/adapters/throughput_probe" --model "$MODEL" --rank 8 --measure-only --max-steps 100 \
        > "$RUN/logs/throughput.out" 2>&1 || { log "THROUGHPUT PROBE FAILED (see logs/throughput.out)"; exit 1; }
  fi
  if [ "$MODEL" = hf ]; then
    proj=$($P -c "import json;print(json.load(open('$RUN/adapters/throughput_probe/throughput.json'))['projected_fit_minutes'])")
    tps=$($P -c "import json;print(json.load(open('$RUN/adapters/throughput_probe/throughput.json'))['tokens_per_s'])")
    log "THROUGHPUT 100 steps: $tps tok/s; projected $proj min per fit (cap $MAX_FIT_MIN min)"
    if [ "${FORCE:-0}" != 1 ] && $P -c "import sys; sys.exit(0 if float('$proj') > float('$MAX_FIT_MIN') else 1)"; then
      log "ABORT: projected fit exceeds MAX_FIT_MIN; lower TOKEN_BUDGET (regenerate) or set FORCE=1"; exit 3
    fi
  fi
  touch "$RUN/STAGE0_DONE"; log "stage 0 done"
}

fit_eval() {  # bank cell arm sleep rank [lambdas]  -- train (reusing identical-corpus fits) then evaluate ON/OFF
  local b=$1 c=$2 a=$3 k=$4 r=$5 lams=${6:-1}
  local corpus="$RUN/corpora/bank$b/$c/$a/sleep$k/corpus.json" ad="$RUN/adapters/bank$b/$c/$a/sleep$k/r$r"
  local tag="bank${b}__${c}__${a}__sleep${k}__r$r"
  [ -f "$corpus" ] || $MD corpus --run-dir "$RUN" --bank "$b" --cell "$c" --arm "$a" --sleep "$k" --model "$MODEL" \
      --ordering "$ORDERING" > "$RUN/logs/corpus_$tag.out" 2>&1 || { log "CORPUS FAILED $tag"; return 1; }
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

finalist() { echo "${FINALIST:-$($P -c "import json;print(json.load(open('$RUN/report/finalist.json'))['cell'])")}"; }

stage1() {  # FIRST WRITER RESULT: A/B/C/D + scrambled-binding control, rank 8, across-arm sleep-4 corpora, three banks.
            # The within-session arm holds the same item set (corpora/index.json identical_items) but, under
            # ORDERING=chronological, in a different order; it is fitted in stage 2 (identity measured, not assumed).
  for b in 0 1 2; do for c in A B C D Dshuf; do fit_eval "$b" "$c" across 4 8 || exit 1; done; done
  $MD report --run-dir "$RUN" > "$RUN/logs/report_stage1.out" 2>&1 || { log "REPORT FAILED"; exit 1; }
  log "$(grep -o 'REPORT_DONE.*' "$RUN/logs/report_stage1.out")"; touch "$RUN/STAGE1_DONE"; log "stage 1 done -> $RUN/report/summary.md"
}

stage2() {  # finalist trajectories: across-sleep arm sleeps 1-3 (before/after each sleep); within arm before sleep 4
            # (sleeps 1-3 share one exposure-free corpus -> one fit) and at sleep 4 (same items as across-4: a separate
            # fit under ORDERING=chronological, reused by sha under ORDERING=content); then the two interference sleeps
            # with no new exposure to the bank owners. The within-4 fit is repeated for WITHIN_CELLS (default A = today's
            # writer) so the within/across identity prediction is measured for today's writer as well as the finalist.
  F=$(finalist); log "finalist cell: $F (ordering $ORDERING; within-4 also for: $WITHIN_CELLS)"
  for b in 0 1 2; do
    for k in 1 2 3; do fit_eval "$b" "$F" across "$k" 8 || exit 1; done
    fit_eval "$b" "$F" within 3 8 || exit 1
    fit_eval "$b" "$F" within 4 8 || exit 1
    for c in $WITHIN_CELLS; do [ "$c" = "$F" ] || fit_eval "$b" "$c" within 4 8 || exit 1; done
    for k in 5 6; do fit_eval "$b" "$F" across "$k" 8 || exit 1; done
  done
  $MD report --run-dir "$RUN" > "$RUN/logs/report_stage2.out" 2>&1 || { log "REPORT FAILED"; exit 1; }
  touch "$RUN/STAGE2_DONE"; log "stage 2 done (see 'Exposure arms at sleep 4' in report/summary.md)"
}

stage3() {  # rank 32 (alpha 64) on the finalist's sleep-4 corpus + adapter-strength sweep without retraining
  F=$(finalist)
  for b in 0 1 2; do fit_eval "$b" "$F" across 4 32 || exit 1; done
  for b in 0 1 2; do
    tag="bank${b}__${F}__across__sleep4__r8"
    [ -f "$RUN/eval/${tag}__lam0.json" ] || fit_eval "$b" "$F" across 4 8 "0,0.25,0.5,1" || exit 1
  done
  $MD report --run-dir "$RUN" > "$RUN/logs/report_stage3.out" 2>&1 || { log "REPORT FAILED"; exit 1; }
  touch "$RUN/STAGE3_DONE"; log "stage 3 done -> $RUN/report/summary.md"
}

case "$STAGE" in
  0) stage0 ;;
  1) stage0; stage1 ;;
  2) stage0; [ -f "$RUN/STAGE1_DONE" ] || stage1; stage2 ;;
  3) stage0; [ -f "$RUN/STAGE1_DONE" ] || stage1; [ -f "$RUN/STAGE2_DONE" ] || stage2; stage3 ;;
  all) stage0; stage1; stage2; stage3 ;;
  *) echo "unknown stage $STAGE"; exit 2 ;;
esac
log "MEMORY_DOSE_DONE stage=$STAGE"
