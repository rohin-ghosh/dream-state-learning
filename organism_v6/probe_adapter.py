"""Probe a standalone adapter (or base) on the sealed panel.
  python -m organism_v6.probe_adapter --out <json> [--adapter <dir>]
      [--reps 2] [--budget-ticks 16]
Used for causal controls: outcome-shuffled adapters, rank calibration.
"""
from __future__ import annotations
import argparse
import json
import os

from .gym_backend import CompilerGym, Episode
from .ledger import Ledger
from .batch_loop import run_episodes_batch
from .run_life import PROBES, BOOTSTRAP


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--adapter", default=None)
    ap.add_argument("--reps", type=int, default=2)
    ap.add_argument("--budget-ticks", type=int, default=16)
    args = ap.parse_args()
    out = os.path.expanduser(args.out)
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)

    from .model_backend import VLLMBackend
    model = VLLMBackend(adapter_path=os.path.expanduser(args.adapter)
                        if args.adapter else None)
    gym = CompilerGym()
    panels = []
    for rep in range(args.reps):
        led = Ledger(out + f".rep{rep}.ledger.jsonl")
        res = run_episodes_batch(model, gym, [Episode(eid=b) for b in PROBES],
                                 BOOTSTRAP, led, args.budget_ticks)
        panels.append({r["episode_id"]: r["best_score"] for r in res})
        print(f"[panel {rep}] mean="
              f"{sum(panels[-1].values()) / len(panels[-1]):.4f}", flush=True)
    means = [sum(p.values()) / len(p) for p in panels]
    tmp = out + ".tmp"
    with open(tmp, "w") as f:
        json.dump(dict(adapter=args.adapter, panels=panels, means=means,
                       mean=sum(means) / len(means)), f, indent=1)
    os.rename(tmp, out)
    print(f"PROBE_DONE mean={sum(means) / len(means):.4f}")


if __name__ == "__main__":
    main()
