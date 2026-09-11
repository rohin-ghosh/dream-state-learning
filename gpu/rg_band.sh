#!/bin/bash
# Pretest P4 — frozen-model headroom band for the reasoning gym (design rule A0).
#   Frozen 7B (no adapter), the gym's birth prompt, no-end-token driver, 16-turn budget, the EXAM set
#   (zebra_puzzles / acre / rush_hour x4) and the GATE set (n_queens / tower_of_hanoi x6), 8 seeded reps
#   (777 + 1000 x rep) over every instance. Writes rg_band/<date>.json + rg_band/<date>.md (per-instance and
#   per-family scores, mean, SD across reps, valid-action rate, attempts per instance, the collapse brake's
#   frozen reference = the median of the child's WORDS per problem over the problems the frozen model did NOT
#   solve (mechanism 3.1; attempts / distinct actions are instruments), and the A0 statement:
#   ceiling - mean >= 0.10 and >= 3 x SD) plus one ledger per set/rep.
# Usage (on a node, from ~/dream-state):  bash gpu/rg_band.sh <gpu> [reps=8] [tag=$(date +%F)] [sets=exam,gate]
# Requires pip reasoning-gym==0.1.25 in ~/v2/venv (python >= 3.10). Smoke without a GPU: add MOCK=1.
set -u
G="${1:?gpu index}"; REPS="${2:-8}"; TAG="${3:-$(date +%F)}"; SETS="${4:-exam,gate}"
cd ~/dream-state || exit 1
export HF_HUB_OFFLINE=1 CUDA_HOME=/usr/local/cuda-13.0 PATH=/usr/local/cuda-13.0/bin:$HOME/v2/venv/bin:$PATH
P=~/v2/venv/bin/python
OUTDIR="${RG_BAND_OUT:-rg_band}"; mkdir -p "$OUTDIR"
MOCKARG=(); [ "${MOCK:-0}" = 1 ] && MOCKARG=(--mock)
$P -c "import reasoning_gym, sys; print('[rg_band] reasoning_gym', __import__('importlib.metadata').metadata.version('reasoning_gym'))" || { echo "[rg_band] pip install reasoning-gym==0.1.25 first"; exit 1; }
t0=$(date +%s)
CUDA_VISIBLE_DEVICES=$G $P -m organism_v6.rg_band --gym reasoning_gym --sets "$SETS" --reps "$REPS" --base-seed 777 \
  --budget-ticks 16 --out-dir "$OUTDIR" --tag "$TAG" ${MOCKARG[@]+"${MOCKARG[@]}"} 2>&1 | tee "$OUTDIR/$TAG.out"
echo "[rg_band] wall $(( $(date +%s) - t0 ))s -> $OUTDIR/$TAG.json $OUTDIR/$TAG.md"
grep -E "^\[band|RG_BAND_DONE" "$OUTDIR/$TAG.out"
