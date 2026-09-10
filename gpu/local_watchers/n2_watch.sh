#!/bin/bash
# Node-2 watcher: smoke-screen arms, R2 lives, rank-cal cells. Exits on any
# arm/life failure, or when all smoke arms + rank probes are done.
S="/Users/rohing/dream-state/gpu/ovx_ssh.sh"
for ((i=0; i<200; i++)); do
  OUT=$(bash "$S" '
    arms_done=0; arms_fail=0
    for arm in serial1x8 shallow4x2 wide8x1; do
      if pgrep -f "lineage_smoke/$arm " >/dev/null 2>&1; then continue; fi   # running
      f=~/v6_out/smoke_${arm%%[0-9]*}.out
      last=$(grep -E "ARM_" "$f" 2>/dev/null | tail -1)
      case "$last" in *_DONE) arms_done=$((arms_done+1));; *_FAILED_*) arms_fail=$((arms_fail+1));; esac
    done
    probes=$(ls ~/v6_out/rankcal/*/probe.json 2>/dev/null | wc -l)
    lives=$(pgrep -c -f "[r]un_life_v2")
    crash=""
    for f in ~/v6_out/R2_B_seed*.out; do
      life=$(basename "$f" .out)
      if ! test -f ~/v6_out/$life/LIFE_DONE && ! pgrep -f "life-dir.*$life " >/dev/null 2>&1; then crash="$crash $life"; fi
    done
    echo "arms_done=$arms_done arms_fail=$arms_fail probes=$probes lives=$lives crash=$crash"' 2>/dev/null)
  echo "$(date '+%H:%M') $OUT"
  case "$OUT" in
    *arms_fail=[1-9]*) echo "SMOKE_ARM_FAILED:$OUT"; exit 0 ;;
    *crash=\ *[A-Za-z]*) echo "N2_LIFE_CRASHED:$OUT"; exit 0 ;;
    *arms_done=3*probes=[2-9]*) echo "N2_SMOKE_AND_PROBES_DONE:$OUT"; exit 0 ;;
  esac
  sleep 600
done
echo "N2_WATCH_WINDOW_DONE"
