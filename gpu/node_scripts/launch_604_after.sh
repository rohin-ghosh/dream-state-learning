#!/bin/bash
for i in $(seq 1 300); do grep -q BOOTSTRAPS_DONE ~/v6_out/train_bootstraps.out 2>/dev/null && break; sleep 60; done
grep -q BOOTSTRAPS_DONE ~/v6_out/train_bootstraps.out || { echo NO_BOOTSTRAPS; exit 1; }
rm -rf ~/v6_out/R4_B_seed604; cd ~/dream-state && bash gpu/launch_RP_lives.sh '7:604' http://127.0.0.1:8012/v1 Qwen/Qwen2.5-32B-Instruct-AWQ R4 --probe-gate && echo R4_604_RELAUNCHED
