#!/bin/bash
# Start the parent model as a vLLM OpenAI-compatible server on ONE GPU.
# Usage (on a node):  bash gpu/launch_parent_server.sh <gpu_list> [port]
#   <gpu_list> e.g. "6" or "6,7" — TP size = number of GPUs listed.
# MEMORY: Qwen2.5-32B bf16 is ~64GB -> needs TWO A40s (TP=2). A single A40
# fits Qwen2.5-14B-Instruct (set V6_PARENT_MODEL). Marker: ~/parent_server.READY
set -u
GPU="${1:?gpu list}"; PORT="${2:-8011}"
TP=$(echo "$GPU" | tr "," "\n" | grep -c .)
MODEL="${V6_PARENT_MODEL:-Qwen/Qwen2.5-32B-Instruct}"
# the pinned revision belongs to the 32B model; any other model must supply its own
if [ "$MODEL" = "Qwen/Qwen2.5-32B-Instruct" ]; then REV="${V6_PARENT_REV:-5ede1c97bbab6ce5cda5812749b4c0bdf79b18dd}"; else REV="${V6_PARENT_REV:?set V6_PARENT_REV (snapshot hash) for $MODEL}"; fi
export HF_HUB_OFFLINE=1 CUDA_HOME=/usr/local/cuda-13.0
export PATH=/usr/local/cuda-13.0/bin:$HOME/v2/venv/bin:$PATH
rm -f ~/parent_server.READY
nohup env CUDA_VISIBLE_DEVICES="$GPU" ~/v2/venv/bin/python -m vllm.entrypoints.openai.api_server \
  --model "$MODEL" --revision "$REV" --tokenizer-revision "$REV" \
  --port "$PORT" --max-model-len 8192 --gpu-memory-utilization 0.92 \
  --tensor-parallel-size "$TP" \
  --enforce-eager > ~/parent_server.log 2>&1 < /dev/null &
for i in $(seq 1 90); do
  if curl -s "http://127.0.0.1:$PORT/v1/models" | grep -q "$MODEL"; then
    touch ~/parent_server.READY; echo "PARENT_SERVER_READY port=$PORT gpu=$GPU"; exit 0
  fi
  sleep 10
done
echo "PARENT_SERVER_TIMEOUT"; tail -20 ~/parent_server.log; exit 1
