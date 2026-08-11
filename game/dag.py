"""Procedural crafting DAG with configurable depth/branching + exact oracle value.

Regime-sweep verdict (exp5): the trained-signal window is widest with RICH, DEEP
recipe structure and long horizons — so depth/branching are first-class knobs here,
not a fixed recipe book.

Oracle value = exact remaining-cost to goal (BFS-style closure over the DAG +
location knowledge). Per-step TD salience = V(s_t) − V(s_{t+1}) — positive on
progress. This is the ZERO-COST perfect value signal for Stage 1 (mechanism
isolation); the learned value net replicates it later (signal-learnability result).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import numpy as np


@dataclass(frozen=True)
class CraftDAG:
    """recipes: item -> (ing_a, ing_b). raws: gatherable leaves."""
    recipes: dict            # str -> tuple[str, str]
    raws: tuple              # tuple[str, ...]
    depth_of: dict           # str -> int (0 for raws)

    def items(self):
        return list(self.raws) + list(self.recipes)

    def max_depth(self) -> int:
        return max(self.depth_of.values())


def gen_dag(seed: int, depth: int = 4, branching: int = 3, n_raw: int = 6) -> CraftDAG:
    """Layered DAG: `branching` new craftable items per depth level; each requires
    two ingredients, at least one from the immediately-previous level (forces real
    chains, not shallow fan-in)."""
    rng = np.random.default_rng(seed)
    raws = tuple(f"raw_{i}" for i in range(n_raw))
    levels = {0: list(raws)}
    recipes, depth_of = {}, {r: 0 for r in raws}
    for d in range(1, depth + 1):
        levels[d] = []
        below = [it for dd in range(d) for it in levels[dd]]
        prev = levels[d - 1]
        for b in range(branching):
            name = f"c{d}_{b}"
            a = prev[int(rng.integers(len(prev)))]          # forces chain depth
            other = a
            while other == a:                               # no dup-ingredient recipes
                other = below[int(rng.integers(len(below)))]
            recipes[name] = (a, other)
            depth_of[name] = d
            levels[d].append(name)
    return CraftDAG(recipes=recipes, raws=raws, depth_of=depth_of)


def requirements(dag: CraftDAG, item: str, have: Optional[dict] = None) -> dict:
    """Multiset of RAW gathers + craft steps still needed for `item`, given
    inventory `have` (counts). Returns {'crafts': [...], 'raw_needs': {raw: n}}."""
    have = dict(have or {})
    crafts, raw_needs = [], {}

    def need(it):
        if have.get(it, 0) > 0:
            have[it] -= 1
            return
        if it in dag.recipes:
            a, b = dag.recipes[it]
            need(a); need(b)
            crafts.append(it)
        else:
            raw_needs[it] = raw_needs.get(it, 0) + 1

    need(item)
    return {"crafts": crafts, "raw_needs": raw_needs}


def oracle_value(dag: CraftDAG, goal: str, inventory: dict,
                 raw_locations: dict, known_locations: set,
                 current_loc: Optional[str]) -> float:
    """NEAR-EXACT heuristic remaining cost to craft `goal` (V=0 iff done; never
    negative). Cost model: craft=1, gather=1/unit, move=1 per distinct needed
    location != current, discovery=2 per distinct needed location NOT YET KNOWN
    (a heuristic constant — true discovery cost is search-order dependent).
    NOT strictly monotone under play: explore randomness and detours can raise V
    transiently; consumers should use the SIGNED TD (logged by the engine) when
    setbacks matter, and the clipped salience only as a progress signal."""
    if inventory.get(goal, 0) > 0:
        return 0.0
    req = requirements(dag, goal, inventory)
    cost = len(req["crafts"])                       # craft steps
    cost += sum(req["raw_needs"].values())          # gather steps
    locs_needed = {raw_locations[r] for r in req["raw_needs"]
                   if raw_locations.get(r) is not None}
    cost += 2.0 * sum(1 for l in locs_needed
                      if l not in known_locations)  # discovery per DISTINCT loc
    cost += sum(1 for l in locs_needed if l != current_loc)   # moves
    return float(cost)


def td_salience(v_before: float, v_after: float) -> float:
    """Per-step oracle salience: progress made this step (>=0 clipped)."""
    return max(0.0, v_before - v_after)
