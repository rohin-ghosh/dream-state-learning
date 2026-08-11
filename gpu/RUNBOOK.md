# RUNBOOK — first lease (48h, 1×A100, starts 8 AM)

Everything here executes a frozen plan (PREWORK rule). Times are rough; the
checkpointing means a killed step resumes.

## Hour 0–1: provision + setup
```bash
ssh <user>@<node>            # creds from the lease page, like July
tmux new -s felt             # ALWAYS work inside tmux
git clone https://github.com/rohin-ghosh/dream-state-learning.git
cd dream-state-learning
bash gpu/setup_node.sh       # phase 1: installs driver → tells you to reboot
sudo reboot
# reconnect:
ssh <user>@<node>; tmux new -s felt; cd dream-state-learning
export HF_TOKEN=<your token>          # optional (models are public)
bash gpu/setup_node.sh                # phase 2 → "READY" (aborts on test failure)
source ~/.bashrc                      # picks up conda init for 'conda activate felt' 
```

## Hours 1–4: S0 gates (the calibration verdict; sequential HF generation — ~1-3h at defaults, not 30 min)
```bash
conda activate felt
PYTHONPATH=. python gpu/run_gates.py --model Qwen/Qwen2.5-1.5B-Instruct
```
- both gates pass → continue. win@manual < 0.85 → escalate `--model
  Qwen/Qwen2.5-3B-Instruct` (SIZING says this is LIKELY). win@none > 0.35 →
  ping Claude; game knobs need raising (depth/interleave).

## Hour 2–8: S1 bulk rollouts + state cache
```bash
PYTHONPATH=. python gpu/rollouts.py --model <the model that passed S0> \
    --episodes 2000 --par 32 --out gpu_artifacts/s1
```
- Appends + resumes safely. 2k episodes first (enough for S2); scale to 10k
  later if the kill-switch passes.

## Hour ~8–10: S2 head training + THE HOUR-12 KILL-SWITCH
```bash
PYTHONPATH=. python gpu/train_head_real.py --in gpu_artifacts/s1 --layer -1
# if regret high: --layer -4, then -8 (already cached — no GPU cost)
```
- PROCEED (regret ≤0.09) / GRAY (0.09–0.15) / STOP (≥0.15, all layers). This is
  the run's central result either way — record the number.

## Hour 10–14: S3 probe-tier (CPU-cheap)
```bash
PYTHONPATH=. python gpu/probe_eval_real.py --in gpu_artifacts/s1 \
    --head gpu_artifacts/s2_head.npz
```
- The decisive line: paired felt_b12 − keyword_gate. Positive+SIG = the head
  learned something beyond action-type on real states → the paper's key result.

## Hour 14+: scale what worked
- Kill-switch PASSED: scale S1 to 10k episodes, rerun S2/S3, then S4 (closed
  loop: play with memory-condition context — wiring session with Claude), then
  second backbone (Phi-3.5-mini; Llama-3.2-3B only if HF access approved).
- Kill-switch FAILED at all layers: run S0+S1-small on the 3B; if still failing,
  STOP GPU spend — the finding is real and reportable; remaining lease time goes
  to benchmark LLM-tier runs (RAG/context backends need no head).

## Throughout
- `git pull` before each stage (Claude ships fixes from the Mac).
- Copy `gpu_artifacts/` off-node before lease end:
  `scp -r <node>:~/dream-state-learning/gpu_artifacts ~/felt_artifacts_$(date +%m%d)`
- Paste stage outputs to Claude at each decision point.
