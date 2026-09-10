#!/bin/bash
for i in $(seq 1 90); do test -f ~/parent_server.READY && break; sleep 20; done
test -f ~/parent_server.READY || { echo N1_PARENT_NOT_READY; exit 1; }
V6_PARENT_MODEL=Qwen/Qwen2.5-32B-Instruct nohup ~/lineage3_chain.sh 2 8000 40 server > ~/v6_out/lineage3_server32_s8000.out 2>&1 < /dev/null &
nohup ~/lineage3_chain.sh 7 8000 40 self > ~/v6_out/lineage3_self_s8000.out 2>&1 < /dev/null &
echo N1_LINEAGES_LAUNCHED
