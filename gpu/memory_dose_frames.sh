#!/bin/bash
# Memory dose-response ("car") test -- cell family F "perception scaling" + completion-frame cues (Rohin's ruling
# 2026-09-11; research_notes/IDEAS.md 'Retrieval by completion, not by question'). ONE GPU, staged, resumes on rerun.
# Runs AFTER gpu/memory_dose.sh stage 0 (banks + distractor must exist in $RUN); reuses its adapters and eval files.
#   rescore  every existing adapter under $RUN/adapters/ whose eval JSON lacks the frame cues is evaluated AGAIN into a
#            NEW eval file (tag suffix __framecues; the old JSON is never overwritten) -- bank0 A and B first
#            (binding-vs-habit answer on completion retrieval without retraining, ~3 min each), then the rest.
#   fits     the F cells named in F_CELLS (default F_r1k1 F_r16k1 F_r16k4 F_r16k16; any cell registered in
#            memory_dose.py FRAME_CELLS is accepted by NAME, incl. F_r64k16 and the abstention cells F_r16k16_neg4 /
#            F_r16k4_neg4 = SEQ-039 'not observed' negatives, K_neg=4) at rank 8, across arm, sleep 4, banks 0-2;
#            each F corpus is built at F_TOKEN_BUDGET tokens when set, else at the cell's own default (400,000 =
#            FRAME_TOKEN_BUDGET in memory_dose.py; F_r16k1 exceeds 65,536 by design). The corpus records the budget
#            used; a corpus already on disk at a DIFFERENT budget aborts the step (remove corpora/bank*/<cell> and
#            adapters/bank*/<cell> to rebuild -- an adapter is keyed by its corpus sha and must not be reused across
#            budgets). The 25-minute fit cap is enforced with a 100-step throughput probe per cell on the bank-0
#            corpus (FORCE=1 overrides, as in memory_dose.sh); lowering F_TOKEN_BUDGET shortens every F fit.
#   report   python -m organism_v6.memory_dose report; touch STAGE_F_DONE.
# SYNTHETIC, researcher-planted facts; disposable mechanism test; every output carries synthetic=true; nothing here
# may be merged into a taught lineage. No hostnames in this file: run it ON the node.
#
# Usage (on a node):  bash gpu/memory_dose_frames.sh <gpu> [step]     step in {rescore,fits,report,all} (default all)
# Env overrides:      RUN=~/v6_out/memory_dose  SEED=0  PY=~/v2/venv/bin/python  REPO=~/dream-state  MODEL=hf|mock
#                     MAX_FIT_MIN=25 (abort a cell's fits if the probe projects a longer fit; FORCE=1 overrides)
#                     F_TOKEN_BUDGET= (tokens per F corpus; empty = the cell's default 400,000; e.g. F_TOKEN_BUDGET=250000)
#                     ORDERING=chronological (must match the run's other corpora)  F_CELLS="F_r1k1 F_r16k1 F_r4k4 F_r1k16"
#                       (or e.g. F_CELLS=F_r16k16_neg4 -- the negatives cells; the corpus records frame_negatives and
#                       every frame-family cue of the eval records p_abstain for gate G11_abstention)
#                     F_BANKS="0 1 2"  RESCORE_FIRST="0:A:across:4:8 0:B:across:4:8" (adapters re-scored before the rest)
# Abstention cell on banks 0-2 at the node budget (SEQ-039):
#   F_CELLS=F_r16k16_neg4 F_BANKS="0 1 2" F_TOKEN_BUDGET=250000 FORCE=1 bash gpu/memory_dose_frames.sh <gpu> fits
# Budget: 12 fits at ~400k tokens each (roughly 6x a 65k fit) + 12 evals + one re-score per existing adapter (~3 min).
# At the 400k default most F items are colourless padding (F_r1k1/F_r4k4/F_r1k16 content is 14-59k tokens; only
# F_r16k1 ~233k exceeds 65k) and every F fit is ~11-15x the optimizer steps of a 65k fit, so the probe will likely
# project over MAX_FIT_MIN: set F_TOKEN_BUDGET (Rohin's ruling on the F budget) or FORCE=1.
G="${1:?gpu index}"; STEP="${2:-all}"
cd "${REPO:-$HOME/dream-state}" || exit 2
export HF_HUB_OFFLINE=1 CUDA_HOME=/usr/local/cuda-13.0 PATH=/usr/local/cuda-13.0/bin:$HOME/v2/venv/bin:$PATH
export CUDA_VISIBLE_DEVICES="$G"
P="${PY:-$HOME/v2/venv/bin/python}"; RUN="${RUN:-$HOME/v6_out/memory_dose}"; SEED="${SEED:-0}"; MODEL="${MODEL:-hf}"
MAX_FIT_MIN="${MAX_FIT_MIN:-25}"; ORDERING="${ORDERING:-chronological}"
F_CELLS="${F_CELLS:-F_r1k1 F_r16k1 F_r16k4 F_r16k16}"; F_BANKS="${F_BANKS:-0 1 2}"
F_TOKEN_BUDGET="${F_TOKEN_BUDGET:-}"   # empty = each F cell's own default budget (FRAME_TOKEN_BUDGET, 400,000)
F_RANK="${F_RANK:-8}"                   # LoRA rank for the F fits (8 = the car test's default; 32 = the planned memory-block rank)
[[ "$F_RANK" =~ ^[0-9]+$ ]] || { echo "F_RANK must be an integer"; exit 2; }
[ -z "$F_TOKEN_BUDGET" ] || [[ "$F_TOKEN_BUDGET" =~ ^[0-9]+$ ]] || { echo "F_TOKEN_BUDGET must be an integer (tokens)"; exit 2; }
RESCORE_FIRST="${RESCORE_FIRST:-0:A:across:4:8 0:B:across:4:8}"
MD="$P -m organism_v6.memory_dose"
mkdir -p "$RUN/eval" "$RUN/logs"
log() { echo "[$(date '+%F %T')] $*" | tee -a "$RUN/logs/runbook_frames.log"; }
[ -f "$RUN/manifest.json" ] && [ -f "$RUN/distractor.json" ] || { log "ABORT: no banks in $RUN -- run gpu/memory_dose.sh <gpu> 0 first"; exit 2; }

has_frame_cues() {  # eval JSON path -> exit 0 if it already carries the frame cues
  $P - "$1" <<'PYEOF'
import json, sys
ev = json.load(open(sys.argv[1]))
sys.exit(0 if any(c.get("kind") == "frame" for c in ev.get("cues", [])) else 1)
PYEOF
}

rescore_one() {  # bank cell arm sleep rank -- evaluate an EXISTING adapter again with the frame cues into a NEW eval file
  local b=$1 c=$2 a=$3 k=$4 r=$5
  local ad="$RUN/adapters/bank$b/$c/$a/sleep$k/r$r" tag="bank${b}__${c}__${a}__sleep${k}__r$r"
  [ -f "$ad/DONE" ] || return 0
  [ -f "$RUN/eval/${tag}__framecues__lam1.json" ] && return 0                              # resume: already re-scored
  if [ -f "$RUN/eval/${tag}__lam1.json" ] && has_frame_cues "$RUN/eval/${tag}__lam1.json"; then return 0; fi
  $MD evaluate --run-dir "$RUN" --bank "$b" --adapter "$ad" --tag "${tag}__framecues" --model "$MODEL" --lambdas 1 \
      --cell "$c" --arm "$a" --sleep "$k" --rank "$r" > "$RUN/logs/eval_${tag}__framecues.out" 2>&1 \
      || { log "RESCORE FAILED $tag"; return 1; }
  log "rescore $tag: $(grep -o 'EVAL_DONE.*' "$RUN/logs/eval_${tag}__framecues.out" | tail -1)"
}

rescore() {  # bank0 A and B first, then every other trained adapter under $RUN/adapters (path = bankB/CELL/ARM/sleepK/rR)
  local spec b c a k r ad rel
  for spec in $RESCORE_FIRST; do IFS=: read -r b c a k r <<< "$spec"; rescore_one "$b" "$c" "$a" "$k" "$r" || exit 1; done
  for ad in "$RUN"/adapters/bank*/*/*/sleep*/r*; do
    [ -d "$ad" ] || continue
    rel="${ad#"$RUN"/adapters/}"; IFS=/ read -r b c a k r <<< "$rel"
    b="${b#bank}"; k="${k#sleep}"; r="${r#r}"
    [[ "$b" =~ ^[0-9]+$ && "$k" =~ ^[0-9]+$ && "$r" =~ ^[0-9]+$ ]] || continue
    rescore_one "$b" "$c" "$a" "$k" "$r" || exit 1
  done
  touch "$RUN/STAGE_F_RESCORE_DONE"; log "rescore done"
}

f_corpus() {  # bank cell arm sleep -- the F corpus at F_TOKEN_BUDGET (else the cell's default); resume if already built
  local b=$1 c=$2 a=$3 k=$4
  local corpus="$RUN/corpora/bank$b/$c/$a/sleep$k/corpus.json" tag="bank${b}__${c}__${a}__sleep${k}"
  if [ -f "$corpus" ]; then
    [ -n "$F_TOKEN_BUDGET" ] || return 0
    local have; have=$($P -c "import json;print(json.load(open('$corpus'))['token_budget'])")
    [ "$have" = "$F_TOKEN_BUDGET" ] && return 0
    log "ABORT $tag: corpus on disk was built at budget $have, F_TOKEN_BUDGET=$F_TOKEN_BUDGET; remove" \
        "$RUN/corpora/bank$b/$c and $RUN/adapters/bank$b/$c to rebuild at the new budget (adapters are keyed by corpus sha)"
    return 3
  fi
  $MD corpus --run-dir "$RUN" --bank "$b" --cell "$c" --arm "$a" --sleep "$k" --model "$MODEL" --ordering "$ORDERING" \
      ${F_TOKEN_BUDGET:+--token-budget "$F_TOKEN_BUDGET"} > "$RUN/logs/corpus_$tag.out" 2>&1 \
      || { log "CORPUS FAILED $tag"; return 1; }
  log "corpus $tag: $(grep -o 'CORPUS_DONE.*' "$RUN/logs/corpus_$tag.out" | tail -1 | sed 's/^CORPUS_DONE [^ ]* //')"
}

fit_cap() {  # cell -- 100-step throughput probe on the cell's bank-0 corpus (same size in every bank); abort over the cap
  local c=$1 corpus="$RUN/corpora/bank0/$c/across/sleep4/corpus.json" probe="$RUN/adapters/throughput_probe_$c"
  f_corpus 0 "$c" across 4 || return $?
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
        "(after removing $RUN/corpora/bank*/$c and $RUN/adapters/*$c*), a larger MAX_FIT_MIN, or FORCE=1"; return 3
  fi
}

fit_eval() {  # bank cell arm sleep rank [lambdas] -- as memory_dose.sh: corpus at the F budget, train (reuse by sha), evaluate
  local b=$1 c=$2 a=$3 k=$4 r=$5 lams=${6:-1}
  local corpus="$RUN/corpora/bank$b/$c/$a/sleep$k/corpus.json" ad="$RUN/adapters/bank$b/$c/$a/sleep$k/r$r"
  local tag="bank${b}__${c}__${a}__sleep${k}__r$r"
  f_corpus "$b" "$c" "$a" "$k" || return $?
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

fits() {  # four F cells x banks 0-2, rank 8, across arm, sleep 4 (12 fits); the cap is checked once per cell
  local c b
  for c in $F_CELLS; do
    fit_cap "$c" || exit $?
    for b in $F_BANKS; do fit_eval "$b" "$c" across 4 "$F_RANK" || exit $?; done
  done
  touch "$RUN/STAGE_F_FITS_DONE"; log "F fits done"
}

report() {
  $MD report --run-dir "$RUN" > "$RUN/logs/report_frames.out" 2>&1 || { log "REPORT FAILED"; exit 1; }
  log "$(grep -o 'REPORT_DONE.*' "$RUN/logs/report_frames.out")"
  touch "$RUN/STAGE_F_DONE"; log "stage F done -> $RUN/report/summary.md (section 'Completion-frame retrieval')"
}

case "$STEP" in
  rescore) rescore ;;
  fits) fits ;;
  report) report ;;
  all) rescore; fits; report ;;
  *) echo "unknown step $STEP"; exit 2 ;;
esac
log "MEMORY_DOSE_FRAMES_DONE step=$STEP"
