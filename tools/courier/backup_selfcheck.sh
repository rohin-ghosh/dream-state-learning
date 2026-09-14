#!/bin/bash
# Backup self-check for the always-on VM (cron, every 30 min via courier_install_vm.sh).
# Acts ONLY when the laptop is silent: if ~/courier/laptop_heartbeat (written by
# courier_laptop.sh) is older than 45 min AND claude is installed+logged in, run a
# headless Claude on SELFCHECK_PROMPT.md in ~/dream-state (cap 1500 s) and append
# the transcript to ~/courier/selfcheck/<UTC ts>.md (copy also dropped in the
# outbox so the laptop sees it). Otherwise log "laptop alive, skipping".
#
# Env (tests): COURIER_HOME, COURIER_REPO, COURIER_CLAUDE_BIN, CLAUDE_CREDENTIALS_FILE,
#              SELFCHECK_STALE_MIN (default 45), SELFCHECK_CAP_S (default 1500), SELFCHECK_PROMPT
# Exit codes: 0 skipped/ran ok; 3 self-check run failed or timed out.
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=courier_lib.sh
source "$HERE/courier_lib.sh"

HB="$COURIER_HOME/laptop_heartbeat"
SC_DIR="$COURIER_HOME/selfcheck"
COURIER_LOG="$SC_DIR/selfcheck.log"
PIDFILE="$SC_DIR/selfcheck.pid"
STALE_MIN="${SELFCHECK_STALE_MIN:-45}"
CAP_S="${SELFCHECK_CAP_S:-1500}"
PROMPT="${SELFCHECK_PROMPT:-$HERE/SELFCHECK_PROMPT.md}"
mkdir -p "$SC_DIR" "$COURIER_HOME/outbox"

if pid_alive "$PIDFILE"; then
  log "self-check already running (pid $(cat "$PIDFILE")), skipping"; exit 0
fi
if pid_alive "$COURIER_HOME/result_reads/result_read.pid"; then
  log "independent result read running, skipping this slot"; exit 0
fi
echo $$ > "$PIDFILE"
trap 'rm -f "$PIDFILE"' EXIT

# heartbeat_age_s -> seconds since the laptop last checked in; "missing" if no/invalid file.
heartbeat_age_s() {
  local hb now
  [ -f "$HB" ] || { echo missing; return; }
  hb=$(tr -cd '0-9' < "$HB")
  [ -n "$hb" ] || { echo missing; return; }
  now=$(date -u +%s)
  echo $(( now - hb ))
}

age=$(heartbeat_age_s)
limit=$(( STALE_MIN * 60 ))
if [ "$age" != "missing" ] && [ "$age" -lt "$limit" ]; then
  log "laptop alive, skipping (heartbeat age ${age}s < ${limit}s)"
  exit 0
fi

if [ "$age" = "missing" ]; then
  why="no laptop heartbeat file at $HB"
else
  why="laptop heartbeat stale (age ${age}s >= ${limit}s)"
fi

if ! claude_ready; then
  log "$why but claude not ready ($(claude_not_ready_reason)), skipping"
  exit 0
fi
[ -r "$PROMPT" ] || { log "$why but prompt $PROMPT missing, skipping"; exit 0; }

ts="$(utc_stamp)"
out="$SC_DIR/$ts.md"
log "$why -> running self-check (cap ${CAP_S}s, model $COURIER_MODEL) -> $out"
{
  echo "# backup self-check $ts"
  echo "reason: $why"
  echo
} >> "$out"
( cd "$COURIER_REPO" && run_with_timeout "$CAP_S" "$CLAUDE_BIN" -p "$(cat "$PROMPT")" \
    --model "$COURIER_MODEL" --permission-mode acceptEdits --output-format text ) >> "$out" 2>&1 < /dev/null
rc=$?
printf '\n\n---\n[backup_selfcheck: exit=%s finished=%s]\n' "$rc" "$(utc_now)" >> "$out"
cp -f "$out" "$COURIER_HOME/outbox/selfcheck-$ts-transcript.reply.md" 2>/dev/null || true
log "self-check finished rc=$rc -> $out"
[ "$rc" -eq 0 ] && exit 0 || exit 3
