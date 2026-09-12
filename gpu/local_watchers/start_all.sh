#!/bin/bash
# start_all.sh — (re)start every laptop-side watcher chain DETACHED from the Claude Code session (nohup, backgrounded in a subshell; macOS has no setsid),
# so a harness memory sweep does not take them down again (2026-09-12 09:10 UTC: five chains were killed at once).
# Idempotent: skips a chain whose process is already alive. Run: bash gpu/local_watchers/start_all.sh
cd "$HOME/dream-state" || exit 1
ART="$HOME/dream-state-artifacts"; mkdir -p "$ART"
start() { # name, log, cmd...
  local name="$1" log="$2"; shift 2
  if pgrep -f "$name" >/dev/null 2>&1; then echo "alive: $name"; return; fi
  # macOS has no setsid: nohup + background + disown in a subshell is enough to leave the session's process group
  ( nohup "$@" >> "$log" 2>&1 < /dev/null & echo "started: $name (pid $!)" )
}
start "courier_laptop.sh" "$ART/courier_laptop.log" bash tools/courier/courier_laptop.sh
start "lease_hunter.sh" "$ART/lease_hunter.log" bash gpu/local_watchers/lease_hunter.sh 2 1200 14d
start "onboard_at.sh 2026-09-12T22:05:00-07:00" "$ART/onboard_at_a100.log" bash gpu/local_watchers/onboard_at.sh 2026-09-12T22:05:00-07:00 a4u8g-0147 06abcfcd-f49e-4e42-befd-2b2e489493c2 A100_NODE a100
start "onboard_at.sh 2026-09-15T00:40:00-07:00" "$ART/onboard_at_ovx3.log" bash gpu/local_watchers/onboard_at.sh 2026-09-15T00:40:00-07:00 ipp2-ovx-p6-07 4d955fac-2367-452e-9d36-ad38e80437ca OVX3_NODE ovx3
start "onboard_at.sh 2026-09-14T16:20:00-07:00" "$ART/onboard_at_a40r.log" bash gpu/local_watchers/onboard_at.sh 2026-09-14T16:20:00-07:00 a4u8g-0105 fa6a9068-4095-4fc9-b0c1-a626592c1040 A40R_NODE a40r
