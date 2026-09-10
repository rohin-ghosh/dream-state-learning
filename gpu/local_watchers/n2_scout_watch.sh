#!/bin/bash
# watches node 2: parent-scout chain, rank-large cells (both nodes), rule-game noise band, lives
S2="/Users/rohing/dream-state/gpu/ovx_ssh.sh"; S1="/Users/rohing/dream-state/gpu/a40_ssh.sh"
for ((i=0; i<60; i++)); do
  O2=$(bash "$S2" 'sc=$(grep -oE "PARENT_NOT_READY|SCOUT_[a-z]+_[a-z]+_FAILED|SCOUT_[a-z]+_DONE|PARENT_SCOUT_CHAIN_DONE" ~/v6_out/parent_scout_chain.out 2>/dev/null | tr "\n" ","); rl=$(ls ~/v6_out/rankcal/r*_large/probe.json 2>/dev/null | wc -l); nz=$(test -f ~/v6_out/rulegame_noise.json && echo 1 || echo 0); lv=$(pgrep -c -f "[r]un_life_v2"); echo "scout=$sc large2=$rl noise=$nz lives2=$lv"' 2>/dev/null)
  O1=$(bash "$S1" 'rl=$(ls ~/v6_out/rankcal/r*_large/probe.json 2>/dev/null | wc -l); lv=$(pgrep -c -f "[r]un_life_v2"); echo "large1=$rl lives1=$lv"' 2>/dev/null)
  echo "$(date '+%H:%M') $O2 $O1"
  case "$O2 $O1" in
    *PARENT_NOT_READY*|*FAILED*) echo "N2_SCOUT_PROBLEM:$O2"; exit 0 ;;
    *PARENT_SCOUT_CHAIN_DONE*large2=2*large1=2*) echo "N2_SCOUT_AND_LARGE_DONE:$O2 $O1"; exit 0 ;;
    *PARENT_SCOUT_CHAIN_DONE*) echo "N2_SCOUT_DONE:$O2 $O1"; exit 0 ;;
    *large2=2*large1=2*) echo "RANK_LARGE_ALL_DONE:$O2 $O1"; exit 0 ;;
  esac
  sleep 600
done
echo WATCH_WINDOW_DONE
