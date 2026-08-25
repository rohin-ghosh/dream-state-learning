"""Pathway-induction sizing (CPU): classify goals as LOOKUP / ANALOGY /
NOVEL given a life, sweep world params for the V3 design target —
analogy goals plentiful and SHALLOW.
  lookup : every pair in the goal's plan was observed in the life
  analogy: plan SHAPE (tier-structure signature) was fully practiced —
           some same-shape plan had ALL its steps observed — but this
           goal's own pairs were not all seen
  novel  : neither
  PYTHONPATH=. python alchemy/pathway_mc.py
"""
from __future__ import annotations
import collections
import numpy as np
from alchemy.world import AlchemyWorld
from alchemy.env import generate_life, seen_pairs
from alchemy.player import ScriptedExplorer

def shape_of(w, plan):
    return tuple(sorted((w.tier_of(a), w.tier_of(b)) for a, b, _ in plan))

def classify(w, life, max_depth=4):
    seen = {tuple(sorted(p)) for p in seen_pairs(life)}
    idx = w.build_chain_index(max_depth)
    practiced_shapes = set()
    for item, (d, plan) in idx.items():
        pairs = {tuple(sorted((a, b))) for a, b, _ in plan}
        if pairs and pairs <= seen:
            practiced_shapes.add(shape_of(w, plan))
    counts = collections.Counter()
    for item, (d, plan) in idx.items():
        pairs = {tuple(sorted((a, b))) for a, b, _ in plan}
        if pairs <= seen:
            counts["lookup"] += 1
        elif shape_of(w, plan) in practiced_shapes:
            counts["analogy"] += 1
        else:
            counts["novel"] += 1
    tot = sum(counts.values()) or 1
    return {k: round(v / tot, 3) for k, v in counts.items()} | {"n_goals": tot}

def main():
    for (N, K, tiers, eps) in [(1024, 96, 4, 3840), (256, 16, 3, 3840),
                               (128, 8, 3, 1920), (128, 12, 4, 3840),
                               (256, 8, 4, 3840)]:
        w = AlchemyWorld(n_ingredients=N, n_inert=N//8, seed=0,
                         n_essences=K, max_tier=tiers, rho_fn=0.6)
        h = w.sample_holdout(0.3, seed=0)
        life = generate_life(w, ScriptedExplorer(seed=0), eps, inv_size=6,
                             seed=0, holdout=h)
        print(f"N={N} K={K} tiers={tiers} eps={eps}: {classify(w, life, tiers)}")

if __name__ == "__main__":
    main()
