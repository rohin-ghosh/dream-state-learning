#!/bin/bash
# onboard_at.sh — sleep until a future lease starts, then run node3_onboard.sh + node3_setup.sh for it.
# Usage: bash gpu/local_watchers/onboard_at.sh <ISO start with offset> <resource> <lease-id> <VAR> <prefix>
set -u
START="$1"; NODE="$2"; LEASE="$3"; VAR="$4"; PFX="$5"; HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG="$HOME/dream-state-artifacts/onboard_at_${PFX}.log"
target=$(python3 -c "from datetime import datetime;print(int(datetime.fromisoformat('$START').timestamp()))")
while :; do now=$(date +%s); left=$((target - now + 300)); [ $left -le 0 ] && break; echo "$(date -u +%FT%TZ) waiting ${left}s for $NODE lease start" >> "$LOG"; sleep $(( left < 1800 ? left : 1800 )); done
echo "$(date -u +%FT%TZ) lease window reached; onboarding $NODE" >> "$LOG"
bash "$HERE/node3_onboard.sh" "$NODE" "$LEASE" "$VAR" "$PFX" >> "$LOG" 2>&1 && bash "$HERE/node3_setup.sh" "$PFX" >> "$LOG" 2>&1
echo "$(date -u +%FT%TZ) onboard_at done rc=$?" >> "$LOG"
