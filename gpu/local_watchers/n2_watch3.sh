#!/bin/bash
S2="/Users/rohing/dream-state/gpu/ovx_ssh.sh"; S1="/Users/rohing/dream-state/gpu/a40_ssh.sh"
for ((i=0; i<60; i++)); do
  O2=$(bash "$S2" 'sc=$(cat ~/v6_out/parent_scout_s700[12].out 2>/dev/null | grep -oE "SCOUT_[a-z]+_[a-z]+_FAILED_s[0-9]+|PARENT_SCOUT_MORE_DONE_s[0-9]+" | tr "\n" ","); rl=$(ls ~/v6_out/rankcal/r*_large/probe.json 2>/dev/null | wc -l); lv=$(pgrep -c -f "[r]un_life_v2 "); echo "scouts=$sc large2=$rl lives2=$lv"' 2>/dev/null)
  O1=$(bash "$S1" 'rl=$(ls ~/v6_out/rankcal/r*_large/probe.json 2>/dev/null | wc -l); nz=$(test -f ~/v6_out/rulegame_noise_n1.json && echo 1 || echo 0); ab=$(ls ~/v6_out/absorption*/report.json 2>/dev/null | wc -l); echo "large1=$rl"' 2>/dev/null)
  echo "$(date '+%H:%M') $O2 $O1"
  case "$O2 $O1" in
    *FAILED*) echo "SCOUT_PAIR_FAILED:$O2"; exit 0 ;;
    *s7001*s7002*large2=2*large1=2*|*s7002*s7001*large2=2*large1=2*) echo "SCOUTS_AND_LARGE_DONE:$O2 $O1"; exit 0 ;;
    *large2=2*large1=2*) echo "RANK_LARGE_ALL_DONE:$O2 $O1"; exit 0 ;;
    *s7001*s7002*|*s7002*s7001*) echo "SCOUT_PAIRS_DONE:$O2 $O1"; exit 0 ;;
  esac
  sleep 600
done
echo WATCH_WINDOW_DONE
