"""SMOKE TEST (SPEC_V2 bottom line): 6 ingredients, 20 episodes, one arm,
NO measurement claims. Proves: env -> episodes -> dreamer -> LoRA -> read ->
eval script all run end to end, and times each stage.

  PYTHONPATH=. .venv/bin/python alchemy/run_smoke.py \
      --model Qwen/Qwen2.5-0.5B-Instruct
"""

from __future__ import annotations

import argparse
import json
import pathlib
import time

from alchemy.world import AlchemyWorld
from alchemy.env import generate_life, seen_pairs
from alchemy.player import ScriptedExplorer
from alchemy import dreamer, lora_mem, evals


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="Qwen/Qwen2.5-0.5B-Instruct")
    ap.add_argument("--eps", type=int, default=20)
    ap.add_argument("--rank", type=int, default=16)
    ap.add_argument("--out", default="alchemy/smoke_out")
    a = ap.parse_args()
    out = pathlib.Path(a.out); out.mkdir(parents=True, exist_ok=True)
    t = {}; t0 = time.time()

    world = AlchemyWorld(n_ingredients=8, n_inert=1, seed=7)
    holdout = world.sample_holdout(frac=0.3, seed=7)
    eps = generate_life(world, ScriptedExplorer(seed=1), a.eps, inv_size=5,
                        holdout=holdout)
    t["episodes_s"] = round(time.time() - t0, 1)
    print(f"[smoke] {len(eps)} eps, success rate "
          f"{sum(e['success'] for e in eps) / len(eps):.2f}, "
          f"{t['episodes_s']}s")
    (out / "episodes.json").write_text(json.dumps(eps, indent=1))

    t0 = time.time()
    model, tok = lora_mem.load_base(a.model)
    t["load_s"] = round(time.time() - t0, 1)

    t0 = time.time()
    corpus = dreamer.dumb_dream(eps)
    dreamed = dreamer.llm_dream(eps, model, tok, world)
    t["dream_s"] = round(time.time() - t0, 1)
    leaks = [l for l in corpus + dreamed if world.leakage_scan(l)]
    print(f"[smoke] corpus dumb={len(corpus)} dreamed={len(dreamed)} "
          f"G2 leaks={len(leaks)} ({t['dream_s']}s)")
    (out / "corpus.json").write_text(json.dumps(
        {"dumb": corpus, "dreamed": dreamed}, indent=1))

    t0 = time.time()
    adapted = lora_mem.train_lora(model, tok, corpus + dreamed, rank=a.rank)
    t["lora_s"] = round(time.time() - t0, 1)

    t0 = time.time()
    seen = seen_pairs(eps)
    assert not (seen & holdout), "G-split violated: holdout pair was seen"
    seen_l, _ = evals.split_pairs(world, seen)
    ask = lambda q: lora_mem.read(adapted, tok, q)
    res = {"seen": evals.eval_pairs(ask, world, seen_l[:10]),
           "held_out": evals.eval_pairs(ask, world, sorted(holdout)[:10])}
    t["eval_s"] = round(time.time() - t0, 1)

    res["timings"] = t
    res["g2_leaks"] = len(leaks)
    (out / "smoke_results.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))
    print("[smoke] PLUMBING COMPLETE — numbers above are NOT measurements.")


if __name__ == "__main__":
    main()
