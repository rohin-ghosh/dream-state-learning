#!/bin/bash
S2="/Users/rohing/dream-state/gpu/ovx_ssh.sh"; S1="/Users/rohing/dream-state/gpu/a40_ssh.sh"
for ((i=0; i<80; i++)); do
  O2=$(bash "$S2" 'l=$(cat ~/v6_out/lineage3_server_s8000_resume.out ~/v6_out/lineage3_self_s8000.out ~/v6_out/lineage3_*_s8001.out 2>/dev/null | grep -oE "LINEAGE_[a-z]+_r[0-9]_[a-z]+_FAILED_s[0-9]+|LINEAGE3_DONE_[a-z]+_s[0-9]+" | tr "\n" ","); lv=$(pgrep -c -f "[r]un_life_v2 "); echo "lin2=$l lives2=$lv"' 2>/dev/null)
  O1=$(bash "$S1" 'p=$(cat ~/v6_out/n1_lineages_when_ready.out 2>/dev/null | grep -oE "N1_PARENT_NOT_READY|N1_LINEAGES_LAUNCHED"); l=$(cat ~/v6_out/lineage3_*_s8000.out 2>/dev/null | grep -oE "LINEAGE_[a-z]+_r[0-9]_[a-z]+_FAILED_s8000|LINEAGE3_DONE_[a-z]+_s8000" | tr "\n" ","); lv=$(pgrep -c -f "[r]un_life_v2 "); q=$(ls ~/v6_out/R2_B_seed[01]/probe_ep0256.json 2>/dev/null | wc -l); echo "n1parent=$p lin1=$l lives1=$lv p256=$q"' 2>/dev/null)
  echo "$(date '+%H:%M') $O2 $O1"
  case "$O2 $O1" in *FAILED*|*NOT_READY*) echo "WATCH8_FAILURE:$O2 $O1"; exit 0 ;; esac
  d=$(echo "$O2 $O1" | grep -o "LINEAGE3_DONE" | wc -l)
  if [ "$d" -ge 6 ]; then echo "ALL_LINEAGES_DONE:$O2 $O1"; exit 0; fi
  if [ "$d" -ge 2 ] && [ "$i" -ge 2 ]; then echo "SOME_LINEAGES_DONE:$O2 $O1"; exit 0; fi
  sleep 900
done
echo WATCH8_WINDOW_DONE
