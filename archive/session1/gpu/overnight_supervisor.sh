#!/bin/bash
# Overnight pipeline supervisor (runs on the Mac; talks to the node via ssh).
# Encodes the RUNBOOK's pre-registered rules — no design decisions inside:
#   1. Watch S1 (restart if crashed; it checkpoints+resumes safely).
#   2. When S1 done (2000 episodes logged + states.npz stable) -> S2 on layers
#      -1, -4, -8; pick min-regret head; record kill-switch verdict.
#   3. S3 probe eval with the best head (cheap; runs under any verdict —
#      baselines/ceiling are meaningful regardless).
#   4. scp gpu_artifacts to the Mac (lease-end wipe insurance).
# Exits 0 with SUMMARY on completion; exits 1 on unrecoverable error.
set -u
NODE="local-rohing@10.117.3.227"
# non-interactive ssh never activates conda -> use the env's python explicitly
PY="/localhome/local-rohing/miniconda3/envs/felt/bin/python"
R="cd ~/dream-state-learning && PYTHONPATH=. $PY "
LOG_DIR="$HOME/dream-state/gpu_artifacts_local"
LOG="$LOG_DIR/overnight.log"
mkdir -p "$LOG_DIR"

say() { echo "[$(date '+%m-%d %H:%M:%S')] $*" | tee -a "$LOG"; }
run() { ssh -o BatchMode=yes -o ConnectTimeout=15 "$NODE" "$@" 2>>"$LOG"; }

say "=== overnight supervisor start ==="

# ---------------- Phase 1: watch S1 to completion ----------------
S1_TARGET=2000
CONSEC_SSH_FAIL=0
while true; do
    EPS=$(run "wc -l < ~/dream-state-learning/gpu_artifacts/s1/rollouts.jsonl 2>/dev/null" | tr -d ' ')
    ALIVE=$(run "pgrep -fc '[g]pu/rollouts.py' || true" | tr -d ' ')
    if [ -z "$EPS" ] && [ -z "$ALIVE" ]; then
        CONSEC_SSH_FAIL=$((CONSEC_SSH_FAIL+1))
        say "ssh unreachable ($CONSEC_SSH_FAIL) — retrying in 5 min"
        [ "$CONSEC_SSH_FAIL" -ge 24 ] && { say "FATAL: node unreachable 2h"; exit 1; }
        sleep 300; continue
    fi
    CONSEC_SSH_FAIL=0
    EPS=${EPS:-0}; ALIVE=${ALIVE:-0}
    STATES=$(run "ls -la ~/dream-state-learning/gpu_artifacts/s1/states.npz 2>/dev/null | awk '{print \$5}'")
    say "S1: episodes=$EPS/$S1_TARGET rollouts_proc=$ALIVE states_bytes=${STATES:-none}"
    if [ "$EPS" -ge "$S1_TARGET" ] && [ -n "${STATES:-}" ] && [ "$ALIVE" -eq 0 ]; then
        # states.npz exists, all episodes logged, process exited -> verify stable size
        sleep 60
        STATES2=$(run "ls -la ~/dream-state-learning/gpu_artifacts/s1/states.npz 2>/dev/null | awk '{print \$5}'")
        if [ "$STATES2" = "$STATES" ]; then say "S1 COMPLETE"; break; fi
    fi
    if [ "$ALIVE" -eq 0 ] && [ "$EPS" -lt "$S1_TARGET" ]; then
        say "S1 crashed at $EPS episodes — restarting (resumes from checkpoint)"
        run "cd ~/dream-state-learning && PYTHONPATH=. nohup $PY gpu/rollouts.py --model Qwen/Qwen2.5-7B-Instruct --episodes 2000 --par 32 --max-steps 120 --out gpu_artifacts/s1 >> ~/s1_restart.log 2>&1 & disown"
        sleep 120
    fi
    sleep 300
done

# ---------------- Phase 2: S2 head training, all layers ----------------
BEST_LAYER=""; BEST_REGRET="9"
for L in -1 -4 -8; do
    say "S2: training head on layer $L"
    run "${R}gpu/train_head_real.py --in gpu_artifacts/s1 --layer $L --out gpu_artifacts/s2_head_l${L}.npz" >> "$LOG" 2>&1
    REG=$(run "$PY -c \"import numpy as np; print(float(np.load('/localhome/local-rohing/dream-state-learning/gpu_artifacts/s2_head_l${L}.npz')['regret']))\" 2>/dev/null")
    say "S2: layer $L regret = ${REG:-FAILED}"
    if [ -n "${REG:-}" ] && python3 -c "exit(0 if float('$REG') < float('$BEST_REGRET') else 1)" 2>/dev/null; then
        BEST_REGRET="$REG"; BEST_LAYER="$L"
    fi
done
[ -z "$BEST_LAYER" ] && { say "FATAL: all S2 runs failed"; exit 1; }
say "S2 BEST: layer $BEST_LAYER regret $BEST_REGRET"
VERDICT=$(python3 -c "r=float('$BEST_REGRET'); print('PROCEED' if r<=0.09 else ('GRAY' if r<0.15 else 'STOP'))")
say "KILL-SWITCH VERDICT: $VERDICT (regret $BEST_REGRET; PROCEED<=0.09, STOP>=0.15)"
run "cp ~/dream-state-learning/gpu_artifacts/s2_head_l${BEST_LAYER}.npz ~/dream-state-learning/gpu_artifacts/s2_head.npz"

# ---------------- Phase 3: S3 probe eval ----------------
say "S3: probe eval with best head"
run "${R}gpu/probe_eval_real.py --in gpu_artifacts/s1 --head gpu_artifacts/s2_head.npz --out gpu_artifacts/s3.json" >> "$LOG" 2>&1
say "S3 result: $(run 'cat ~/dream-state-learning/gpu_artifacts/s3.json 2>/dev/null' | head -c 2000)"

# ---------------- Phase 4: artifact backup ----------------
say "backing up gpu_artifacts to Mac"
scp -o BatchMode=yes -r "$NODE:~/dream-state-learning/gpu_artifacts" "$LOG_DIR/gpu_artifacts_$(date +%m%d_%H%M)" >> "$LOG" 2>&1 \
    && say "backup complete" || say "WARNING: backup failed — retry manually"

say "=== SUMMARY: S1 complete | S2 best layer $BEST_LAYER regret $BEST_REGRET -> $VERDICT | S3 written | artifacts backed up ==="
exit 0
