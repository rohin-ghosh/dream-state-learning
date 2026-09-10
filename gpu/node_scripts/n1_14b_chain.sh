#!/bin/bash
export PATH=$HOME/v2/venv/bin:$PATH
HF_HUB_OFFLINE=0 ~/v2/venv/bin/hf download Qwen/Qwen2.5-14B-Instruct --revision cf98f3b3bbb457ad9e2bb7baf9a0125b6b88caa8 > ~/dl14b.log 2>&1 || { echo N1_14B_DOWNLOAD_FAILED; exit 1; }
cd ~/dream-state && V6_PARENT_MODEL=Qwen/Qwen2.5-14B-Instruct V6_PARENT_REV=cf98f3b3bbb457ad9e2bb7baf9a0125b6b88caa8 bash gpu/launch_parent_server.sh 0 8011 > ~/v6_out/parent_server_launch.out 2>&1
test -f ~/parent_server.READY || { echo N1_PARENT_NOT_READY; exit 1; }
export V6_PARENT_MODEL=Qwen/Qwen2.5-14B-Instruct
nohup ~/lineage3_chain.sh 2 8000 40 server > ~/v6_out/lineage3_server_s8000.out 2>&1 < /dev/null &
nohup ~/lineage3_chain.sh 1 8001 40 server > ~/v6_out/lineage3_server_s8001.out 2>&1 < /dev/null &
nohup ~/lineage3_chain.sh 7 8000 40 self > ~/v6_out/lineage3_self_s8000.out 2>&1 < /dev/null &
echo N1_LINEAGES_LAUNCHED
