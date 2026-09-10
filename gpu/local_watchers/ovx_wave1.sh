#!/bin/bash
# Wave 1 on node 2 (<INTERNAL_HOST>): classroom-merge test + parenting variants.
# Waits for provisioning marker, then launches. Marker-file completion.
S="/Users/rohing/dream-state/gpu/ovx_ssh.sh"
NODE="local-rohing@<INTERNAL_IP>"
# wait for smoke
for ((i=0; i<90; i++)); do
  grep -q OVX_PROVISION_COMPLETE /private/tmp/claude-501/-Users-rohing/d66e193e-e075-475c-96de-a582e32ee6c5/tasks/bg82ktyv0.output 2>/dev/null && break
  sleep 60
done
grep -q SMOKE_OK /private/tmp/claude-501/-Users-rohing/d66e193e-e075-475c-96de-a582e32ee6c5/tasks/bg82ktyv0.output 2>/dev/null || { echo "NODE2_SMOKE_NOT_OK"; exit 1; }
rsync -a --exclude='.git' --exclude='.venv' --exclude='gpu_artifacts_local' --exclude='alchemy/v2_out' "$HOME/dream-state/organism_v6/" "$NODE:~/dream-state/organism_v6/"
bash "$S" "cat > ~/wave1.sh" <<'EOF'
#!/bin/bash
cd ~/dream-state
export HF_HUB_OFFLINE=1 CUDA_HOME=/usr/local/cuda-13.0 PATH=/usr/local/cuda-13.0/bin:$HOME/v2/venv/bin:$PATH
P=~/v2/venv/bin/python
mkdir -p ~/v6_out/lineage
# GPU0-1: classroom-merge test. childA: 8 classrooms x 2 rounds (pooled).
#         childB: 1 classroom x 16 lessons (serial, equal lesson count).
(CUDA_VISIBLE_DEVICES=0 bash -c "$P -m organism_v6.classroom_round --lineage ~/v6_out/lineage/pooled8 --round 0 --classrooms 8 --lessons 2 --phase live && $P -m organism_v6.classroom_round --lineage ~/v6_out/lineage/pooled8 --round 0 --classrooms 8 --lessons 2 --phase sleep && $P -m organism_v6.classroom_round --lineage ~/v6_out/lineage/pooled8 --round 0 --classrooms 8 --lessons 2 --phase exam && $P -m organism_v6.classroom_round --lineage ~/v6_out/lineage/pooled8 --round 1 --classrooms 8 --lessons 2 --phase live && $P -m organism_v6.classroom_round --lineage ~/v6_out/lineage/pooled8 --round 1 --classrooms 8 --lessons 2 --phase sleep && $P -m organism_v6.classroom_round --lineage ~/v6_out/lineage/pooled8 --round 1 --classrooms 8 --lessons 2 --phase exam; echo POOLED8_DONE" > ~/v6_out/wave1_g0.out 2>&1 < /dev/null &)
(CUDA_VISIBLE_DEVICES=1 bash -c "$P -m organism_v6.classroom_round --lineage ~/v6_out/lineage/serial1 --round 0 --classrooms 1 --lessons 16 --phase live && $P -m organism_v6.classroom_round --lineage ~/v6_out/lineage/serial1 --round 0 --classrooms 1 --lessons 16 --phase sleep && $P -m organism_v6.classroom_round --lineage ~/v6_out/lineage/serial1 --round 0 --classrooms 1 --lessons 16 --phase exam; echo SERIAL1_DONE" > ~/v6_out/wave1_g1.out 2>&1 < /dev/null &)
# GPU2: base exam anchor (no adapter) via the same exam path
(CUDA_VISIBLE_DEVICES=2 bash -c "mkdir -p ~/v6_out/lineage/base_anchor/round_000/adapter && touch ~/v6_out/lineage/base_anchor/round_000/adapter/DONE; $P -m organism_v6.probe_adapter --out ~/v6_out/lineage/base_exam.json --reps 3; echo BASE_DONE" > ~/v6_out/wave1_g2.out 2>&1 < /dev/null &)
echo WAVE1_LAUNCHED
EOF
bash "$S" "chmod +x ~/wave1.sh && nohup ~/wave1.sh > ~/wave1.log 2>&1 < /dev/null; sleep 3; cat ~/wave1.log"
