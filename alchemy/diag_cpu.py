"""CPU diagnostics (no GPU): (1) retrieval hit-rate — for held-out pairs,
does top-12 TF-IDF even SURFACE the deduction-relevant evidence?
(2) task lookup-vs-induction — were eval-game recipes literally seen?
  PYTHONPATH=. python alchemy/diag_cpu.py --seed 2 --run alchemy/v2_out
"""
from __future__ import annotations
import argparse, json
import numpy as np
from alchemy.world import AlchemyWorld
from alchemy.env import generate_life, seen_pairs
from alchemy.player import ScriptedExplorer
from alchemy.rag import TfidfIndex
from alchemy.evals import Q
from alchemy.dreamer import dumb_dream

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=2)
    ap.add_argument("--eps", type=int, default=3840)
    a = ap.parse_args()
    w = AlchemyWorld(n_ingredients=1024, n_inert=128, seed=a.seed,
                     n_essences=96, max_tier=4, rho_fn=0.4)
    h = w.sample_holdout(0.3, seed=a.seed)
    life = generate_life(w, ScriptedExplorer(seed=a.seed), a.eps,
                         inv_size=6, seed=a.seed, holdout=h)
    seen = seen_pairs(life)
    corpus = dumb_dream(life)
    idx = TfidfIndex(corpus)
    # --- (1) retrieval surfacing: does top-12 mention BOTH ingredients,
    # and does it include a same-partner pair for each (class evidence)?
    rng = np.random.default_rng(5)
    hp = sorted(h); rng.shuffle(hp)
    both = ev = 0; n = 300
    partners = {}
    for (x, y) in seen:
        partners.setdefault(x, set()).add(y)
        partners.setdefault(y, set()).add(x)
    for x, y in hp[:n]:
        hits = idx.topk(Q.format(a=x, b=y), 12)
        hx = any(x in l for l in hits); hy = any(y in l for l in hits)
        both += hx and hy
        # class evidence surfaced = a hit shows x (or y) with a partner
        # that ALSO co-occurs with the other side somewhere in the log
        exy = False
        for l in hits:
            for p_ in partners.get(x, ()):
                if p_ in l and p_ in partners.get(y, set()):
                    exy = True
        ev += exy
    print(f"[diag] retrieval: both-mentioned {both/n:.2f}, "
          f"shared-partner evidence surfaced {ev/n:.2f} (n={n})")
    # --- (2) task goals: lookup vs induction
    probe = generate_life(w, ScriptedExplorer(seed=a.seed + 1), 200,
                          inv_size=6, seed=a.seed + 50_000, holdout=h)
    look = indu = 0
    for ep in probe:
        t = ep["target"]
        recipes = w.recipe_pairs_for(t) if w.tier_of(t) == 1 else []
        idxc = w.build_chain_index(4)
        plan = idxc.get(t, (0, []))[1]
        plan_pairs = {tuple(sorted((p[0], p[1]))) for p in plan}
        if plan_pairs and plan_pairs <= seen:
            look += 1
        else:
            indu += 1
    print(f"[diag] task goals @E={a.eps}: recipe fully seen (lookup) "
          f"{look/200:.2f}, requires unseen step (induction) {indu/200:.2f}")

if __name__ == "__main__":
    main()
