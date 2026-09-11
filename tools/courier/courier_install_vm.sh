#!/bin/bash
# Install/refresh the courier ON the always-on VM. Idempotent; no sudo.
#   - creates ~/courier/{inbox,outbox/delivered,processed,selfcheck}
#   - starts courier_vm.sh under nohup setsid if not already running
#   - puts ~/.npm-global/bin on PATH in ~/.bashrc (top, before the interactive
#     early-return so `ssh vm claude` works) and ~/.profile
#   - installs the backup self-check crontab entry (every 30 min), keeping
#     every other crontab line untouched
#   - prints a status summary (claude version, login marker, courier pid, cron line)
# Run from the laptop:  bash gpu/nvl_ssh.sh 'bash ~/dream-state/tools/courier/courier_install_vm.sh'
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=courier_lib.sh
source "$HERE/courier_lib.sh"
COURIER_LOG="$COURIER_HOME/courier.log"

mkdir -p "$COURIER_HOME/inbox" "$COURIER_HOME/outbox/delivered" "$COURIER_HOME/processed" "$COURIER_HOME/selfcheck"
chmod +x "$HERE"/*.sh 2>/dev/null || true

# --- PATH for non-interactive shells -----------------------------------------
PATH_LINE='export PATH="$HOME/.npm-global/bin:$PATH"  # claude code (dream-state courier_install_vm.sh)'
if ! grep -qF '.npm-global/bin' ~/.bashrc 2>/dev/null; then
  { echo "$PATH_LINE"; cat ~/.bashrc 2>/dev/null; } > ~/.bashrc.courier.tmp && mv -f ~/.bashrc.courier.tmp ~/.bashrc
  echo "added ~/.npm-global/bin to PATH at top of ~/.bashrc"
fi
if ! grep -qF '.npm-global/bin' ~/.profile 2>/dev/null; then
  printf '\n%s\n' "$PATH_LINE" >> ~/.profile
  echo "added ~/.npm-global/bin to PATH in ~/.profile"
fi

# --- courier daemon ------------------------------------------------------------
if pid_alive "$COURIER_HOME/courier_vm.pid"; then
  echo "courier_vm already running (pid $(cat "$COURIER_HOME/courier_vm.pid"))"
else
  ( nohup setsid bash "$HERE/courier_vm.sh" > "$COURIER_HOME/courier_vm.out" 2>&1 < /dev/null & )
  sleep 2
  if pid_alive "$COURIER_HOME/courier_vm.pid"; then
    echo "courier_vm started (pid $(cat "$COURIER_HOME/courier_vm.pid"))"
  else
    echo "ERROR: courier_vm did not start; see $COURIER_HOME/courier_vm.out"; tail -5 "$COURIER_HOME/courier_vm.out" 2>/dev/null
  fi
fi

# --- crontab: backup self-check every 30 min ------------------------------------
CRON_LINE='*/30 * * * * bash $HOME/dream-state/tools/courier/backup_selfcheck.sh >> $HOME/courier/selfcheck/cron.log 2>&1'
existing="$(crontab -l 2>/dev/null || true)"
if printf '%s\n' "$existing" | grep -qF 'tools/courier/backup_selfcheck.sh'; then
  echo "crontab: backup_selfcheck entry already present"
else
  { [ -n "$existing" ] && printf '%s\n' "$existing"; echo "$CRON_LINE"; } | crontab - \
    && echo "crontab: added backup_selfcheck entry (every 30 min)" \
    || echo "ERROR: crontab install failed"
fi

# --- status ----------------------------------------------------------------------
echo "--- status"
echo "claude: $(command -v "$CLAUDE_BIN" 2>/dev/null || echo not-found)  version: $("$CLAUDE_BIN" --version 2>/dev/null || echo n/a)"
if claude_ready; then echo "claude ready: yes (login marker present)"; else echo "claude ready: NO ($(claude_not_ready_reason))"; fi
echo "repo: $COURIER_REPO  HEAD: $(git -C "$COURIER_REPO" log --oneline -1 2>/dev/null | cut -c1-70)"
echo "courier home: $COURIER_HOME"
echo "cron lines: $(crontab -l 2>/dev/null | grep -c .)"
if [ -f "$COURIER_HOME/laptop_heartbeat" ]; then
  echo "laptop heartbeat age: $(( $(date -u +%s) - $(tr -cd '0-9' < "$COURIER_HOME/laptop_heartbeat") ))s"
else
  echo "laptop heartbeat: none yet (start courier_laptop.sh on the laptop)"
fi
