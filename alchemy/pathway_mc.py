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
    out = {k: round(v / tot, 3) for k, v in counts.items()}
    out["n_goals"] = tot
    # SHALLOWNESS: for analogy shapes, how many fully-practiced instances
    # support each? (>=3 = learnable from examples); plus class-evidence
    # density (observations per ingredient / classes to separate)
    shape_support = collections.Counter()
    for item, (d, plan) in idx.items():
        pairs = {tuple(sorted((a, b))) for a, b, _ in plan}
        if pairs and pairs <= seen:
            shape_support[shape_of(w, plan)] += 1
    supports = [shape_support[shape_of(w, plan)]
                for item, (d, plan) in idx.items()
                if shape_of(w, plan) in shape_support]
    out["median_shape_support"] = int(np.median(supports)) if supports else 0
    obs = sum(len(e["log"]) * 2 for e in life)
    out["obs_per_class"] = round(obs / max(len(w.reactive), 1))
    return out

def main():
    for (N, K, tiers, eps, rho) in [
            (96, 6, 3, 1920, 0.8), (128, 8, 3, 1920, 0.8),
            (128, 8, 4, 3840, 0.8), (192, 12, 4, 3840, 0.7),
            (128, 12, 3, 3840, 0.7), (96, 8, 4, 3840, 0.8)]:
        w = AlchemyWorld(n_ingredients=N, n_inert=N//8, seed=0,
                         n_essences=K, max_tier=tiers, rho_fn=rho)
        h = w.sample_holdout(0.3, seed=0)
        life = generate_life(w, ScriptedExplorer(seed=0), eps, inv_size=6,
                             seed=0, holdout=h)
        print(f"N={N} K={K} tiers={tiers} eps={eps}: {classify(w, life, tiers)}")

if __name__ == "__main__":
    main()
