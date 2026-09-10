#!/bin/bash
# Node-1 (a4u8g-0105, lease ends 2026-09-14) -> node-2 migration. Rehearsable.
# Lives are resumable from marker files; adapters/ledgers/probes are the state.
# Cross-node transfer is via SINGLE-FILE tarballs relayed through this Mac
# (macOS openrsync corrupts trees — measured 2026-09-07).
#   bash gpu/migrate_node1_to_node2.sh <life_dir_name> [<life_dir_name>...]
# e.g. bash gpu/migrate_node1_to_node2.sh R2_B_seed0 R2_B_seed1
set -u
source "$(dirname "$0")/hosts.env"; N1="$A40_NODE"; N2="$OVX_NODE"
S1="/Users/rohing/dream-state/gpu/a40_ssh.sh"; S2="/Users/rohing/dream-state/gpu/ovx_ssh.sh"
TMP="/private/tmp/claude-501/-Users-rohing/d66e193e-e075-475c-96de-a582e32ee6c5/scratchpad/migrate"
mkdir -p "$TMP"
for L in "$@"; do
  echo "== $L: stop on node 1 (bracketed pattern; no self-match) =="
  bash "$S1" "pkill -9 -f 'life-dir.*${L:0:-1}[${L: -1}] ' ; sleep 4; for pid in \$(pgrep -f '[E]ngineCore'); do ppid=\$(ps -o ppid= -p \$pid | tr -d ' '); [ \"\$ppid\" = 1 ] && kill -9 \$pid; done; echo stopped"
  echo "== $L: tar on node 1 =="
  bash "$S1" "cd ~/v6_out && tar czf ~/mig_$L.tgz $L && ls -la ~/mig_$L.tgz | awk '{print \$5}'"
  rsync -a "$N1:~/mig_$L.tgz" "$TMP/" && rsync -a "$TMP/mig_$L.tgz" "$N2:~/" || { echo "RELAY_FAILED $L"; exit 1; }
  echo "== $L: untar + verify on node 2 =="
  bash "$S2" "cd ~/v6_out && tar xzf ~/mig_$L.tgz && ls $L | wc -l && ls $L/sleep_*/adapter/DONE 2>/dev/null | wc -l"
  echo "== $L: relaunch on node 2 (resumes from markers) — set GPU manually: =="
  echo "   bash $S2 'cd ~/dream-state && HF_HUB_OFFLINE=1 CUDA_VISIBLE_DEVICES=<g> nohup ~/v2/venv/bin/python -m organism_v6.run_life_v2 --life-dir ~/v6_out/$L --arm B --seed <seed> --episodes 1024 --sleep-every 32 --probe-every 64 --budget-ticks 16 --wake-batch 8 --rank 8 <ADD THE LIFE'\''S ORIGINAL FLAGS: --probe-gate for R3/R4, --parent-url/--parent-model for RP/R4; check the .out header or gate.json/parent_brief.json presence> >> ~/v6_out/$L.out 2>&1 < /dev/null &'"
done
echo "MIGRATION_STAGED"
