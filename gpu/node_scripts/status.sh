#!/bin/bash
# node-side one-shot status: lives, gates, RP briefs, crashes, GPUs
c=""; for d in ~/v6_out/R*_B_seed*; do [ -d "$d" ] || continue; L=$(basename $d); test -f $d/LIFE_DONE -o -f $d/RETIRED && continue; pgrep -f "life-dir.*/$L( |$)" >/dev/null || c="$c $L"; done
echo "lives=$(pgrep -c -f "[r]un_life_v2 ") crash=[$c]"
for d in ~/v6_out/R3_B_seed*; do [ -d "$d" ] || continue; echo "$(basename $d): sleeps=$(ls -d $d/sleep_* 2>/dev/null|wc -l) gates=$(ls $d/sleep_*/gate.json 2>/dev/null|wc -l) rejected=$(ls -d $d/sleep_*/adapter/REJECTED* 2>/dev/null|wc -l) last=$(grep -E 'gate cand' $d/life.log | tail -1 | cut -c1-110)"; done
for d in ~/v6_out/RP_B_seed*; do [ -d "$d" ] || continue; echo "$(basename $d): sleeps=$(ls -d $d/sleep_* 2>/dev/null|wc -l) interventions=$(grep -l '"intervened": true' $d/sleep_*/parent_brief.json 2>/dev/null|wc -l) last_flags=$(python3 -c "import json,glob;f=sorted(glob.glob('$d/sleep_*/parent_brief.json'));print(json.load(open(f[-1]))['metrics'].get('flags') if f else '-')")"; done
nvidia-smi --query-gpu=index,memory.used --format=csv,noheader | tr '\n' ' '; echo
