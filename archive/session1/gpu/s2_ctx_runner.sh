#!/bin/bash
# Wait for PASS B-ctx to finish, then rerun S2 on all layers with the
# context-conditioned cache. Prints regrets + the pre-registered reading.
set -u
NODE="local-rohing@10.117.3.227"
PY="/localhome/local-rohing/miniconda3/envs/felt/bin/python"
R="cd ~/dream-state-learning && PYTHONPATH=. $PY "
LOG="$HOME/dream-state/gpu_artifacts_local/overnight.log"
say() { echo "[$(date '+%m-%d %H:%M:%S')] $*" | tee -a "$LOG"; }
run() { ssh -o BatchMode=yes -o ConnectTimeout=15 "$NODE" "$@" 2>>"$LOG"; }

say "--- s2_ctx_runner start ---"
while true; do
    DONE=$(run "grep -c 'cache complete' ~/s1_ctx.log 2>/dev/null || true" | tr -d ' ')
    ALIVE=$(run "pgrep -fc '[g]pu/rollouts.py' || true" | tr -d ' ')
    PROG=$(run "tail -1 ~/s1_ctx.log 2>/dev/null | tr -d '\n' | tail -c 60")
    say "ctx-cache: done=$DONE alive=${ALIVE:-?} last='${PROG:-}'"
    [ "${DONE:-0}" -ge 1 ] && break
    if [ "${ALIVE:-0}" -eq 0 ] && [ "${DONE:-0}" -eq 0 ]; then
        say "ctx-cache process died before completion — restarting (resumes)"
        run "cd ~/dream-state-learning && PYTHONPATH=. nohup $PY gpu/rollouts.py --model Qwen/Qwen2.5-7B-Instruct --cache-ctx --out gpu_artifacts/s1 >> ~/s1_ctx.log 2>&1 & disown"
        sleep 120
    fi
    sleep 180
done
say "ctx cache COMPLETE — running S2 on layers -1 -4 -8"

for L in -1 -4 -8; do
    run "${R}gpu/train_head_real.py --in gpu_artifacts/s1 --layer $L --states ctx --out gpu_artifacts/s2_head_ctx_l${L}.npz" >> "$LOG" 2>&1
    REG=$(run "$PY -c \"import numpy as np; print(float(np.load('/localhome/local-rohing/dream-state-learning/gpu_artifacts/s2_head_ctx_l${L}.npz')['regret']))\" 2>/dev/null")
    say "S2-ctx layer $L regret = ${REG:-FAILED}"
done
say "PRE-REGISTERED READING: <0.122 = signal beyond text (PROCEED-equiv); ~0.21 = STOP stands"
exit 0
