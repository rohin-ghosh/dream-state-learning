#!/bin/bash
# waits for the 14B download to finish, then launches the parent server on GPU 0
for i in $(seq 1 120); do
  if ! pgrep -f '[h]f download Qwen/Qwen2.5-14B' >/dev/null && ls ~/.cache/huggingface/hub/models--Qwen--Qwen2.5-14B-Instruct/snapshots/*/model-0000*-of-*.safetensors >/dev/null 2>&1; then
    cd ~/dream-state && PARENT_GPUS=0 PARENT_MODEL=Qwen/Qwen2.5-14B-Instruct bash gpu/launch_parent_server.sh > ~/v6_out/parent_server.out 2>&1
    echo PARENT_LAUNCHED; exit 0
  fi
  sleep 60
done
echo PARENT_LAUNCH_TIMEOUT
