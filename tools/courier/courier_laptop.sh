#!/bin/bash
# Laptop side of the message courier. Background loop, every 60 s:
#   push  ~/courier_out/*.md            -> VM ~/courier/inbox/   (then move to ~/courier_out/sent/)
#   pull  VM ~/courier/outbox/*.reply.md -> ~/courier_in/        (then move on the VM to outbox/delivered/)
#   heartbeat: writes the UTC epoch to VM ~/courier/laptop_heartbeat every loop
#              (backup_selfcheck.sh on the VM acts only when this is >45 min old).
# All transport goes through gpu/nvl_ssh.sh / gpu/nvl_scp.sh; the agent itself never sshes.
#
# Start:  ( nohup bash tools/courier/courier_laptop.sh > ~/courier_out/courier_laptop.out 2>&1 < /dev/null & )
# Usage:  courier_laptop.sh [--once]     (--once: one pass, no loop)
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"
OUT="${COURIER_OUT:-$HOME/courier_out}"
IN="${COURIER_IN:-$HOME/courier_in}"
SENT="$OUT/sent"
PIDFILE="$OUT/.courier_laptop.pid"
LOG="$OUT/courier_laptop.log"
INTERVAL="${COURIER_LAPTOP_INTERVAL:-60}"
ONCE=0; [ "${1:-}" = "--once" ] && ONCE=1
SSH="bash $REPO/gpu/nvl_ssh.sh"
SCP="bash $REPO/gpu/nvl_scp.sh"

mkdir -p "$OUT" "$SENT" "$IN"
log() { echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) $*" | tee -a "$LOG"; }

if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE" 2>/dev/null)" 2>/dev/null; then
  echo "courier_laptop already running (pid $(cat "$PIDFILE"))"; exit 0
fi
echo $$ > "$PIDFILE"
trap 'rm -f "$PIDFILE"' EXIT
log "courier_laptop start pid=$$ out=$OUT in=$IN"

one_pass() {
  local f b listing pulled=() rc
  # 1. push outgoing messages
  for f in "$OUT"/*.md; do
    [ -e "$f" ] || continue
    b="$(basename "$f")"
    if $SCP "$f" "NODE:courier/inbox/$b" >/dev/null 2>&1; then
      mv -f "$f" "$SENT/$b"; log "pushed $b"
    else
      log "push FAILED $b (VM unreachable?) - will retry"
    fi
  done
  # 2. heartbeat + list replies in one ssh round trip
  listing=$($SSH 'mkdir -p ~/courier/outbox/delivered ~/courier/inbox && date -u +%s > ~/courier/laptop_heartbeat && ls -1 ~/courier/outbox 2>/dev/null' 2>/dev/null); rc=$?
  if [ $rc -ne 0 ]; then log "heartbeat/list FAILED (ssh rc=$rc)"; return; fi
  # 3. pull replies
  while IFS= read -r b; do
    case "$b" in *.reply.md) ;; *) continue ;; esac
    if $SCP "NODE:courier/outbox/$b" "$IN/$b.part" >/dev/null 2>&1; then
      mv -f "$IN/$b.part" "$IN/$b"; pulled+=("$b"); log "pulled $b -> $IN/$b"
    else
      rm -f "$IN/$b.part"; log "pull FAILED $b"
    fi
  done <<< "$listing"
  if [ ${#pulled[@]} -gt 0 ]; then
    $SSH "cd ~/courier/outbox && mv -f $(printf "'%s' " "${pulled[@]}") delivered/" >/dev/null 2>&1 \
      || log "WARN: could not move delivered replies on the VM"
  fi
}

while :; do
  one_pass
  [ "$ONCE" = 1 ] && break
  sleep "$INTERVAL"
done
