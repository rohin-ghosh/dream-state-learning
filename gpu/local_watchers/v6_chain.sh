#!/bin/bash
# Autonomous chain: wait for noise reps to finish -> launch causal controls
# on GPUs 6/7 -> then watch lives+controls. Exits (notifying Fable) on:
# all long lives done, controls done, any crash, or window end.
S="/Users/rohing/dream-state/gpu/a40_ssh.sh"

# Phase 1: wait for noise jobs to drain (max ~2h)
for ((i=0; i<24; i++)); do
  n=$(bash "$S" "pgrep -c -f '[n]oise_probes'" 2>/dev/null)
  [ "${n:-0}" = "0" ] && break
  sleep 300
done
echo "NOISE_DRAINED $(date '+%H:%M')"

# Phase 2: launch controls (idempotent — skip if markers exist)
bash "$S" "test -f ~/v6_out/controls/GPU6_DONE || nohup ~/v6_out/launch_controls.sh > ~/v6_out/launch_controls.log 2>&1 < /dev/null; sleep 2; cat ~/v6_out/launch_controls.log 2>/dev/null | tail -1"

# Phase 3: watch everything (10-min cadence, ~40h window)
for ((i=0; i<240; i++)); do
  OUT=$(bash "$S" '
    live_done=$(ls ~/v6_out/R_*/LIFE_DONE ~/v6_out/R2_*/LIFE_DONE 2>/dev/null | wc -l)
    procs=$(pgrep -c -f "[r]un_life_v2")
    c6=$(test -f ~/v6_out/controls/GPU6_DONE && echo 1 || echo 0)
    c7=$(test -f ~/v6_out/controls/GPU7_DONE && echo 1 || echo 0)
    crash=""
    for f in ~/v6_out/R_A_seed*.out ~/v6_out/R_B_seed*.out ~/v6_out/R2_B_seed*.out; do
      life=$(basename "$f" .out)
      if ! test -f ~/v6_out/$life/LIFE_DONE && ! test -f ~/v6_out/$life/KILLED && \
         ! pgrep -f "life-dir.*$life" >/dev/null 2>&1; then
        crash="$crash $life"
      fi
    done
    echo "live_done=$live_done procs=$procs controls=$c6$c7 crash=$crash"' 2>/dev/null)
  echo "$(date '+%H:%M') $OUT"
  case "$OUT" in
    *live_done=9*) echo "ALL_LIVES_DONE"; exit 0 ;;
    *controls=11*live_done=0*|*controls=11*live_done=[1-5]*)
      # controls finished; report once then keep watching lives
      if [ ! -f /tmp/.v6_controls_reported ]; then
        touch /tmp/.v6_controls_reported
        echo "CONTROLS_DONE (lives still running)"
        exit 0
      fi ;;
    *crash=\ *[A-Za-z]*) echo "LIFE_CRASHED:$OUT"; exit 0 ;;
  esac
  sleep 600
done
echo "WATCH_WINDOW_DONE"
