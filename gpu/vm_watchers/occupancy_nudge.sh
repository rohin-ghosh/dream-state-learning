#!/bin/bash
# occupancy_nudge.sh — VM daemon. Rohin's standing steer (raw message 34, 2026-09-13 07:10 UTC): "if there is something to do
# that needs to be done on the GPU and doesn't wait completely on other results ... then fill the GPUs, we are anything but
# scarce on work to do." When fleet occupancy (GPUs with >1 GB used, across all nodes in hosts.env) stays below MIN_BUSY for
# LOW_POLLS consecutive polls, type Rohin's steer VERBATIM (marked as a relay, not a nudge from the watcher) into the builder's
# tmux session and queue it with Tab; at most one relay per COOLDOWN seconds. Only Rohin's words enter the session.
# Usage: bash occupancy_nudge.sh [POLL_S=600] [MIN_BUSY=8] [LOW_POLLS=3] [COOLDOWN=7200]. Kill switch: ~/occupancy_nudge.off.
set -u
POLL="${1:-600}"; MIN_BUSY="${2:-8}"; LOW_POLLS="${3:-3}"; COOLDOWN="${4:-7200}"
REPO="$HOME/dream-state"; LOG="$HOME/occupancy_nudge.log"; OFF="$HOME/occupancy_nudge.off"; STATE="$HOME/occupancy_nudge.last"
source "$REPO/gpu/hosts.env" 2>/dev/null || { echo "hosts.env missing" >&2; exit 2; }
log() { echo "$(date -u +%FT%TZ) $*" >> "$LOG"; }
count_busy() { # prints "busy total"
  local b=0 t=0 r
  for host in "$A40_NODE" "$OVX_NODE" "$OVX2_NODE" "${A100_NODE:-}"; do
    [ -n "$host" ] || continue
    r=$(timeout 90 ssh -o BatchMode=yes -o ConnectTimeout=15 "$host" 'nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | awk "{u+=(\$1>1000)} END{print u\" \"NR}"' 2>/dev/null | tail -1)
    [ -n "$r" ] && { b=$((b+${r%% *})); t=$((t+${r##* })); }
  done
  echo "$b $t"
}
MSG='[Rohin — verbatim relay via Fable watcher, automated occupancy reminder, not a nudge and not new instructions] standing occupancy target: if there is something to do that needs to be done on the GPU and doesnt wait completely on other results (so in parallel: trying new skills, building something, seeds) then fill the GPUs, we are anything but scarce on work to do. Astra should be planning and looking at results and following my steers but that should still give it enough time to plan for the next while past runs gain usefulness. Any runs that are no longer relevant should be cleared up, and if important work needs to be done the GPUs can be cleared to fill it out. (raw message 34; the fleet has been below the target for the last 30 minutes)'
low=0; log "start poll=${POLL}s min_busy=$MIN_BUSY low_polls=$LOW_POLLS cooldown=${COOLDOWN}s"
while :; do
  if [ -f "$OFF" ]; then log "kill switch present"; sleep "$POLL"; continue; fi
  read -r busy total <<<"$(count_busy)"
  if [ "${busy:-0}" -lt "$MIN_BUSY" ]; then low=$((low+1)); else low=0; fi
  last=$(cat "$STATE" 2>/dev/null || echo 0); now=$(date +%s)
  if [ "$low" -ge "$LOW_POLLS" ] && [ $((now-last)) -ge "$COOLDOWN" ]; then
    if tmux has-session -t astra 2>/dev/null; then
      tmux send-keys -t astra -l "$MSG"; sleep 0.5; tmux send-keys -t astra Tab; sleep 1; tmux send-keys -t astra Enter
      echo "$now" > "$STATE"; low=0; log "RELAYED occupancy steer (busy=$busy/$total)"
    else log "no astra tmux session (busy=$busy/$total)"; fi
  else log "busy=$busy/$total low_streak=$low"; fi
  sleep "$POLL"
done
