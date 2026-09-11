#!/bin/bash
# VM side of the message courier. Runs ON the always-on helper VM, started by
# courier_install_vm.sh as:  ( nohup setsid bash courier_vm.sh > ~/courier/courier_vm.out 2>&1 < /dev/null & )
#
# Every 20 s: for each new ~/courier/inbox/*.md (a message from the laptop agent),
# run a headless Claude in ~/dream-state on that text and write the answer to
# ~/courier/outbox/<name>.reply.md; move the message to ~/courier/processed/.
# If claude is not installed/logged in, the reply says so instead.
# Single instance via ~/courier/courier_vm.pid.  Log: ~/courier/courier.log.
#
# Usage: courier_vm.sh [--once]      (--once: one pass, no loop; used by tests)
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=courier_lib.sh
source "$HERE/courier_lib.sh"

INBOX="$COURIER_HOME/inbox"
OUTBOX="$COURIER_HOME/outbox"
PROCESSED="$COURIER_HOME/processed"
PIDFILE="$COURIER_HOME/courier_vm.pid"
COURIER_LOG="$COURIER_HOME/courier.log"
INTERVAL="${COURIER_INTERVAL:-20}"
RUN_CAP_S="${COURIER_RUN_CAP_S:-3600}"
SETTLE_S="${COURIER_SETTLE_S:-5}"     # ignore inbox files modified less than this many seconds ago (scp still writing)
ONCE=0; [ "${1:-}" = "--once" ] && ONCE=1

mkdir -p "$INBOX" "$OUTBOX/delivered" "$PROCESSED"

if pid_alive "$PIDFILE"; then
  echo "courier_vm already running (pid $(cat "$PIDFILE"))"; exit 0
fi
echo $$ > "$PIDFILE"
trap 'rm -f "$PIDFILE"' EXIT
log "courier_vm start pid=$$ inbox=$INBOX model=$COURIER_MODEL repo=$COURIER_REPO"

process_one() {
  local f="$1" name reply rc
  name="$(basename "$f" .md)"
  reply="$OUTBOX/$name.reply.md"
  log "processing $name"
  if claude_ready; then
    ( cd "$COURIER_REPO" && run_with_timeout "$RUN_CAP_S" "$CLAUDE_BIN" -p "$(cat "$f")" \
        --model "$COURIER_MODEL" --permission-mode acceptEdits --output-format text ) \
        > "$reply.tmp" 2>&1 < /dev/null
    rc=$?
    printf '\n\n---\n[courier_vm: message=%s exit=%s model=%s finished=%s]\n' "$name" "$rc" "$COURIER_MODEL" "$(utc_now)" >> "$reply.tmp"
  else
    rc=127
    {
      echo "The VM courier received your message but could not run Claude:"
      echo "  $(claude_not_ready_reason)"
      echo "Log in on the VM (interactive: run 'claude' once) and resend."
      printf '\n---\n[courier_vm: message=%s exit=%s finished=%s]\n' "$name" "$rc" "$(utc_now)"
    } > "$reply.tmp"
  fi
  mv -f "$reply.tmp" "$reply"
  mv -f "$f" "$PROCESSED/"
  log "done $name rc=$rc -> $reply"
}

while :; do
  for f in "$INBOX"/*.md; do
    [ -e "$f" ] || continue
    if [ "$(file_age_s "$f")" -lt "$SETTLE_S" ]; then continue; fi   # still being copied
    process_one "$f"
  done
  [ "$ONCE" = 1 ] && break
  sleep "$INTERVAL"
done
