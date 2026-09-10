"""Probe-noise estimation + clean baseline: run the sealed 8-probe panel
N times with the BASE model under the fixed harness. Gives (a) the sampling
noise band for all curve claims, (b) the same-code ep000 baseline.

  CUDA_VISIBLE_DEVICES=6 python -m organism_v6.noise_probes \
      --out ~/v6_out/noise --reps 0 1 2 [--budget-ticks 24]
"""
from __future__ import annotations
import argparse
import json
import os

from .gym_backend import CompilerGym, Episode
from .ledger import Ledger
from .loop import run_episode
from .run_life import PROBES, BOOTSTRAP


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--reps", type=int, nargs="+", required=True)
    ap.add_argument("--budget-ticks", type=int, default=24)
    args = ap.parse_args()
    out = os.path.expanduser(args.out)
    os.makedirs(out, exist_ok=True)

    from .model_backend import VLLMBackend
    model = VLLMBackend(adapter_path=None)
    gym = CompilerGym()
    for rep in args.reps:
        dest = os.path.join(out, f"rep_{rep:02d}.json")
        if os.path.exists(dest):
            continue
        led = Ledger(os.path.join(out, f"rep_{rep:02d}.ledger.jsonl"))
        results = {}
        for b in PROBES:
            r = run_episode(model, gym, Episode(eid=b), BOOTSTRAP, led,
                            budget_ticks=args.budget_ticks)
            results[b] = r["best_score"]
        tmp = dest + ".tmp"
        with open(tmp, "w") as f:
            json.dump(dict(rep=rep, results=results,
                           mean=sum(results.values()) / len(results)),
                      f, indent=1)
        os.rename(tmp, dest)
        print(f"[noise rep {rep}] mean="
              f"{sum(results.values()) / len(results):.4f}", flush=True)
    open(os.path.join(out, f"REPS_DONE_{'_'.join(map(str, args.reps))}"),
         "w").write("ok\n")


if __name__ == "__main__":
    main()
