"""Pre-project sizing Monte Carlo (no LLM): for each episode count, what
fraction of HELD-OUT pairs is deducible by an IDEAL learner from the life
log alone? This is the information-availability ceiling — no memory system
can beat it, so it pins the episode scale where the experiment is winnable.

Ideal-learner model (conservative: product evidence only):
- a product observation on (i,j) reveals the pair's rule-family (families
  are unique per essence-pair, so this pins {e_i,e_j} up to labeling)
- two ingredients proved same-class if observed against a common partner
  with the same family (union-find over this evidence)
- held-out pair (a,b) deducible iff some observed pair (a',b') has a~a',
  b~b' under the same-class relation (then its outcome is entailed)

  PYTHONPATH=. .venv/bin/python alchemy/sizing_mc.py
"""

from __future__ import annotations

import json
from collections import defaultdict

import numpy as np

from alchemy.world import AlchemyWorld
from alchemy.env import generate_life, seen_pairs
from alchemy.player import ScriptedExplorer


class UF:
    def __init__(self):
        self.p = {}

    def find(self, x):
        self.p.setdefault(x, x)
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a, b):
        self.p[self.find(a)] = self.find(b)


def ceiling(world, episodes, holdout, transfer=True):
    """transfer=True upgrades the ideal learner: once two ingredients are
    provably same-class (product evidence), ANY observed outcome (including
    nothing/ruin) transfers across the class pair. Still conservative: no
    elimination logic, inert ingredients never get classed."""
    # gather ALL observations: (i,j) -> kind; product ones also give family
    fam, kinds = {}, {}
    for ep in episodes:
        for st in ep["log"]:
            _, a, b = st["action"].split(" ")
            key = tuple(sorted((a, b)))
            if "fuse into" in st["obs"]:
                prod = st["obs"].split("fuse into ")[1].rstrip(".")
                fam[key] = prod.rsplit("-", 1)[0]
                kinds[key] = "product"
            elif "ruined" in st["obs"]:
                kinds[key] = "ruin"
            else:
                kinds[key] = "nothing"
    # same-class evidence: common partner, same family.
    # MIXTURE FIX: fn-stratum families are shared across essence-pairs at
    # equal distance, so they are AMBIGUOUS class evidence — link classes
    # via iid-unique families only (oracle stratum labels; makes this a
    # conservative bound: a geometry-aware learner can deduce strictly more
    # on the fn stratum, up to 1.0 once positions are pinned).
    iid_fams = set()
    for key, st in getattr(world, "pair_stratum", {}).items():
        if st == "iid" and world.rules[key][0] == "product":
            for tier in range(1, getattr(world, "max_tier", 1) + 1):
                p = world.products.get((key, 1, tier)) or \
                    world.products.get((key, 1))
                if p:
                    iid_fams.add(p.rsplit("-", 1)[0])
    if iid_fams:
        fam = {k: f for k, f in fam.items() if f in iid_fams}
    uf = UF()
    by_partner = defaultdict(list)          # partner -> [(other, family)]
    for (a, b), f in fam.items():
        by_partner[a].append((b, f))
        by_partner[b].append((a, f))
    for partner, lst in by_partner.items():
        byfam = defaultdict(list)
        for other, f in lst:
            byfam[f].append(other)
        for others in byfam.values():
            for o in others[1:]:
                uf.union(others[0], o)
    # deducibility of holdout pairs
    classed = set(uf.p)                     # classed via product evidence
    known = defaultdict(set)                # class-pair -> evidence
    for (a, b), f in fam.items():
        known[frozenset((uf.find(a), uf.find(b)))].add(f)
    if transfer:                            # kind-outcomes transfer too,
        for (a, b), k in kinds.items():     # if both endpoints are classed
            if a in classed and b in classed:
                known[frozenset((uf.find(a), uf.find(b)))].add(k)
    # inert elimination (statistical, pre-registered threshold T=8):
    # never product/ruin, AND observed 'nothing' against >=T distinct
    # proven classes => inert (P(reactive) < 0.4^T, negligible)
    T = 8
    reactive_ev = set()
    for (a, b), k in kinds.items():
        if k in ("product", "ruin"):
            reactive_ev.add(a); reactive_ev.add(b)
    nothing_cls = defaultdict(set)
    for (a, b), k in kinds.items():
        if k == "nothing":
            if b in classed:
                nothing_cls[a].add(uf.find(b))
            if a in classed:
                nothing_cls[b].add(uf.find(a))
    inert = {x for x, cs in nothing_cls.items()
             if x not in reactive_ev and len(cs) >= T}
    ded = 0
    for a, b in holdout:
        if a not in world.ingredients or b not in world.ingredients:
            continue
        if a in inert or b in inert:
            ded += 1
            continue
        key = frozenset((uf.find(a), uf.find(b)))
        if known.get(key):
            ded += 1
    # class-recovery purity: fraction of provably-linked pairs that are true
    links, correct = 0, 0
    names = sorted(world.ingredients)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            if uf.find(a) == uf.find(b):
                links += 1
                correct += int(world.essence_of(a) == world.essence_of(b))
    return {"deducible_frac": ded / max(len(holdout), 1),
            "n_inert_found": len(inert),
            "class_links": links,
            "class_purity": correct / max(links, 1)}


def main():
    results = {}
    for E in (960, 1920, 3840, 7680, 15360):
        rows = []
        for seed in range(5):
            w = AlchemyWorld(n_ingredients=1024, n_inert=128, seed=seed, n_essences=96)
            hold = w.sample_holdout(0.3, seed=seed)
            eps = generate_life(w, ScriptedExplorer(seed=seed), E,
                                inv_size=6, seed=seed, holdout=hold)
            c = ceiling(w, eps, hold)
            c["seen_pairs"] = len(seen_pairs(eps))
            c["obs_per_ingredient"] = round(
                sum(len(e["log"]) * 2 for e in eps) / 1024, 1)
            rows.append(c)
        agg = {k: round(float(np.mean([r[k] for r in rows])), 3)
               for k in rows[0]}
        results[E] = agg
        print(f"eps={E:>4}  ceiling={agg['deducible_frac']:.2f}  "
              f"purity={agg['class_purity']:.2f}  "
              f"seen_pairs={agg['seen_pairs']:.0f}  "
              f"obs/ingr={agg['obs_per_ingredient']}")
    import pathlib
    pathlib.Path("alchemy/sizing_mc.json").write_text(
        json.dumps(results, indent=1))


if __name__ == "__main__":
    main()
