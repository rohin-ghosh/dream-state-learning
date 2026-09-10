#!/bin/bash
# feasibility only: single-GPU quantized 32B parent (Codex has not ruled on quantized parents)
export PATH=$HOME/v2/venv/bin:$PATH CUDA_HOME=/usr/local/cuda-13.0
HF_HUB_OFFLINE=0 hf download Qwen/Qwen2.5-32B-Instruct-AWQ > ~/dl32awq.log 2>&1 || { echo AWQ_DOWNLOAD_FAILED; exit 1; }
REV=$(ls ~/.cache/huggingface/hub/models--Qwen--Qwen2.5-32B-Instruct-AWQ/snapshots/ | head -1)
HF_HUB_OFFLINE=1 CUDA_VISIBLE_DEVICES=1 nohup python -m vllm.entrypoints.openai.api_server --model Qwen/Qwen2.5-32B-Instruct-AWQ --revision $REV --port 8012 --max-model-len 8192 --gpu-memory-utilization 0.92 --enforce-eager > ~/awq32_server.log 2>&1 < /dev/null &
for i in $(seq 1 60); do curl -s http://127.0.0.1:8012/v1/models | grep -q AWQ && { echo AWQ32_SERVER_READY; curl -s http://127.0.0.1:8012/v1/chat/completions -H 'Content-Type: application/json' -d '{"model":"Qwen/Qwen2.5-32B-Instruct-AWQ","max_tokens":30,"messages":[{"role":"user","content":"Name one process mistake a learner makes when inducing a hidden rule, in one sentence."}]}' | head -c 400; echo; exit 0; }; sleep 15; done
echo AWQ32_SERVER_TIMEOUT
