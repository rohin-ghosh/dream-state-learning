"""S0 — calibration gates with a REAL model (first thing to run on the node).

Measures win@manual and win@no-context for the chosen backbone and prints the
SIZING §5 verdicts. ~300 episodes ≈ 30-60 min on 1×A100 with a 1.5B model.

Usage:
  PYTHONPATH=. python gpu/run_gates.py --model Qwen/Qwen2.5-1.5B-Instruct \
      [--worlds 3] [--eps 10] [--max-steps 60]
Escalation: if win@manual < 0.85 after prompt iteration → rerun with
  --model Qwen/Qwen2.5-3B-Instruct   (SIZING: likely needed)
"""

from __future__ import annotations

import argparse
import json
import time

from felt.gates import gate_calibration
from felt.llm_player import HFBackend


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="Qwen/Qwen2.5-1.5B-Instruct")
    ap.add_argument("--worlds", type=int, default=3)
    ap.add_argument("--eps", type=int, default=10)
    ap.add_argument("--max-steps", type=int, default=60)
    ap.add_argument("--depth", type=int, default=4)
    ap.add_argument("--branching", type=int, default=3)
    ap.add_argument("--out", default="gpu_artifacts/s0_gates.json")
    a = ap.parse_args()

    print(f"[S0] loading {a.model} ...")
    import torch
    torch.manual_seed(0)                         # reproducible sampling (T>0)
    backend = HFBackend(a.model)                 # one instance; stateless per episode
    t0 = time.time()
    r = gate_calibration(lambda w, mode, e: backend,
                         n_worlds=a.worlds, eps_per_world=a.eps,
                         max_steps=a.max_steps, depth=a.depth, branching=a.branching)
    r["model"] = a.model
    r["minutes"] = round((time.time() - t0) / 60, 1)

    import pathlib
    pathlib.Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(a.out).write_text(json.dumps(r, indent=1))

    print(json.dumps({k: v for k, v in r.items() if k != "episodes"}, indent=1))
    by_depth = {}
    for ep in r["episodes"]:
        if ep["mode"] == "manual":
            by_depth.setdefault(ep["depth"], []).append(ep)
    print("\n[manual wins by goal depth]  (timeout = lost AT the step cap)")
    for d in sorted(by_depth):
        eps = by_depth[d]
        w = sum(e["success"] for e in eps)
        t = sum(e["timeout"] for e in eps)
        print(f"  depth {d}: {w}/{len(eps)} wins | {t} timeouts")
    print("\n[VERDICT per SIZING §5]")
    if not r["gate_reasoning_ok"]:
        print("  win@manual < 0.85 → game too hard to PLAY for this model:")
        print("  1) iterate the prompt (few-shot examples in felt/llm_player.build_prompt)")
        print("  2) escalate: --model Qwen/Qwen2.5-3B-Instruct")
    if not r["gate_knowledge_wall_ok"]:
        print("  win@none > 0.35 → game too easy to KNOW: raise depth/interleave, shrink window")
    if r["gate_reasoning_ok"] and r["gate_knowledge_wall_ok"]:
        print(f"  BOTH GATES PASS (room = {r['room']:.2f}) → proceed to S1 (gpu/rollouts.py)")


if __name__ == "__main__":
    main()
