"""Rule-game noise band: repeated base-model exam panels (the 8 PROBE_EIDS)
under DIFFERENT seeds per rep. Required before any classroom number is read
(Codex/Fable risk note 2026-09-07). Writes mean/SD across reps.

  CUDA_VISIBLE_DEVICES=g python -m organism_v6.rulegame_noise \
      --out ~/v6_out/rulegame_noise.json --reps 8
"""
from __future__ import annotations
import argparse
import json
import os
import statistics

from .gym_backend import Episode
from .ledger import Ledger
from .batch_loop import EpisodeDriver, _seed_for
from .rulegame import RuleGame
from .nursery_dialogue import CHILD_BOOT, PROBE_EIDS


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--reps", type=int, default=8)
    ap.add_argument("--eids", type=int, default=len(PROBE_EIDS),
                    help="exam size; default = the 8 PROBE_EIDS. Larger N "
                         "measures the band for a bigger classroom exam.")
    args = ap.parse_args()
    eids = [f"probe/rule-{i}" for i in range(args.eids)]
    from .model_backend import VLLMBackend
    m = VLLMBackend(adapter_path=None)
    game = RuleGame()
    means = []
    for rep in range(args.reps):
        led = Ledger(os.devnull)
        ds = [EpisodeDriver(Episode(eid=e, goal="Induce the rule.",
                                    metric="quiz", intro="A fresh box."),
                            CHILD_BOOT, game, led, budget_ticks=8)
              for e in eids]
        while any(not d.done for d in ds):
            act = [d for d in ds if not d.done]
            outs = m.batch([d.prompt() for d in act],
                           seeds=[_seed_for(d.ep.eid, d.st.tick, 9000 + rep)
                                  for d in act])
            for d, o in zip(act, outs):
                d.consume(o)
        mean = sum(d.summary()["best_score"] for d in ds) / len(ds)
        means.append(mean)
        print(f"[rulegame-noise rep {rep}] mean={mean:.3f}", flush=True)
    res = dict(reps=args.reps, means=means, mean=statistics.mean(means),
               sd=statistics.pstdev(means) if len(means) > 1 else 0.0)
    with open(os.path.expanduser(args.out), "w") as f:
        json.dump(res, f, indent=1)
    print(f"RULEGAME_NOISE mean={res['mean']:.3f} sd={res['sd']:.3f}")


if __name__ == "__main__":
    main()
