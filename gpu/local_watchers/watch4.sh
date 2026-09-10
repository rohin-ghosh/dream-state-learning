#!/bin/bash
S2="/Users/rohing/dream-state/gpu/ovx_ssh.sh"; S1="/Users/rohing/dream-state/gpu/a40_ssh.sh"
for ((i=0; i<70; i++)); do
  O2=$(bash "$S2" 'l=$(ls ~/v6_out/rankcal/r*_large/probe.json 2>/dev/null | wc -l); e=$(test -f ~/v6_out/rulegame_noise_e40.json && echo 1 || echo 0); s=$(grep -oE "FAILED_s7003|PARENT_SCOUT_MORE_DONE_s7003" ~/v6_out/parent_scout_s7003.out 2>/dev/null | head -1); lv=$(pgrep -c -f "[r]un_life_v2 "); echo "large2=$l e40_2=$e s7003=$s lives2=$lv"' 2>/dev/null)
  O1=$(bash "$S1" 'r=$(cat ~/v6_out/rankcal/rep_r*_s*.out 2>/dev/null | grep -oE "REP_(DONE|FAILED)_r[0-9]+_s[0-9]" | tr "\n" ","); e=$(test -f ~/v6_out/rulegame_noise_e40.json && echo 1 || echo 0); lv=$(pgrep -c -f "[r]un_life_v2 "); p=$(ls ~/v6_out/R2_B_seed0/probe_ep0128.json ~/v6_out/R2_B_seed1/probe_ep0128.json 2>/dev/null | wc -l); echo "reps=$r e40_1=$e lives1=$lv p128=$p"' 2>/dev/null)
  echo "$(date '+%H:%M') $O2 $O1"
  case "$O2 $O1" in
    *FAILED*) echo "WATCH4_FAILURE:$O2 $O1"; exit 0 ;;
    *large2=2*e40_2=1*e40_1=1*p128=2*) echo "WATCH4_BATCH_DONE:$O2 $O1"; exit 0 ;;
  esac
  sleep 900
done
echo WATCH4_WINDOW_DONE
