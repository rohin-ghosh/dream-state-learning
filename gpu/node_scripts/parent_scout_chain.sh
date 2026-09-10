#!/bin/bash
# waits for the 14B parent server, then runs a parent!=child round (server) and a matched self-parent control, both on GPU 2
cd ~/dream-state; export HF_HUB_OFFLINE=1 CUDA_HOME=/usr/local/cuda-13.0 PATH=/usr/local/cuda-13.0/bin:$HOME/v2/venv/bin:$PATH V6_PARENT_MODEL=Qwen/Qwen2.5-14B-Instruct
P=~/v2/venv/bin/python
for i in $(seq 1 90); do test -f ~/parent_server.READY && break; sleep 20; done
test -f ~/parent_server.READY || { echo PARENT_NOT_READY; exit 1; }
curl -s http://127.0.0.1:8011/v1/chat/completions -H 'Content-Type: application/json' -d '{"model":"Qwen/Qwen2.5-14B-Instruct","max_tokens":20,"messages":[{"role":"user","content":"Say ready."}]}' | head -c 300; echo
for mode in server self; do
  L=~/v6_out/parent_scout_$mode
  for ph in live sleep exam; do
    CUDA_VISIBLE_DEVICES=2 $P -m organism_v6.classroom_round --lineage $L --round 0 --classrooms 8 --lessons 4 --phase $ph --parent $mode --gen-seed 7000 > $L.$ph.out 2>&1 || { echo SCOUT_${mode}_${ph}_FAILED; break; }
  done
  echo SCOUT_${mode}_DONE
done
echo PARENT_SCOUT_CHAIN_DONE
