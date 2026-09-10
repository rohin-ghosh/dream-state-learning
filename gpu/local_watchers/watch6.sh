#!/bin/bash
S2="/Users/rohing/dream-state/gpu/ovx_ssh.sh"; S1="/Users/rohing/dream-state/gpu/a40_ssh.sh"
for ((i=0; i<70; i++)); do
  O2=$(bash "$S2" 'r=$(cat ~/v6_out/rankcal/rep_r*_s3.out 2>/dev/null | grep -oE "REP_(DONE|FAILED)_r[0-9]+_s3" | tr "\n" ","); s=$(cat ~/v6_out/parent_scout_s700[67]_e40.out 2>/dev/null | grep -oE "FAILED_s700[67]|PARENT_SCOUT_E40_DONE_s700[67]" | tr "\n" ","); lv=$(pgrep -c -f "[r]un_life_v2 "); echo "reps2=$r e40scouts=$s lives2=$lv"' 2>/dev/null)
  O1=$(bash "$S1" 'r=$(cat ~/v6_out/rankcal/rep_r*_s[12].out 2>/dev/null | grep -oE "REP_(DONE|FAILED)_r[0-9]+_s[12]" | tr "\n" ","); lv=$(pgrep -c -f "[r]un_life_v2 "); p=$(ls ~/v6_out/R2_B_seed[01]/probe_ep0192.json 2>/dev/null | wc -l); echo "reps1=$r lives1=$lv p192=$p"' 2>/dev/null)
  echo "$(date '+%H:%M') $O2 $O1"
  n1=$(echo "$O1" | grep -o "REP_DONE" | wc -l); n2=$(echo "$O2" | grep -o "REP_DONE" | wc -l); ns=$(echo "$O2" | grep -o "E40_DONE" | wc -l)
  case "$O2 $O1" in *FAILED*) echo "WATCH6_FAILURE:$O2 $O1"; exit 0 ;; esac
  if [ "$n1" -ge 4 ] && [ "$n2" -ge 2 ]; then echo "RANK_REPLICATES_DONE:$O2 $O1"; exit 0; fi
  if [ "$ns" -ge 2 ] && [ "$i" -ge 1 ]; then echo "E40_SCOUTS_DONE:$O2 $O1"; exit 0; fi
  sleep 900
done
echo WATCH6_WINDOW_DONE
