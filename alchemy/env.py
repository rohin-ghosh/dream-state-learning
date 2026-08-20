"""Episode loop + append-only life log (SPEC_V2 §2, §6 State)."""

from __future__ import annotations

import numpy as np

from alchemy.world import AlchemyWorld


def run_episode(world: AlchemyWorld, player, target: str,
                inventory: list, max_steps: int = 12,
                memory_ctx: str = "") -> dict:
    """One life episode. State per step = goal, holdings, last obs, value.
    Value = 0 if crafted else 1 (depth-1 targets); logged every step."""
    holdings = list(inventory)
    log, crafted = [], False
    obs = f"You arrive at the bench. You hold: {', '.join(holdings)}."
    for step in range(max_steps):
        state = {"goal": target, "holdings": list(holdings),
                 "obs": obs, "value": 0 if crafted else 1}
        a, b = player.pick_pair(state, memory_ctx)
        if a is None:
            break
        kind, prod, obs = world.combine_text(a, b)
        if kind == "product":
            if prod not in holdings:
                holdings.append(prod)
            if prod == target:
                crafted = True
        log.append({"step": step, "action": f"combine {a} {b}",
                    "obs": obs, "value_after": 0 if crafted else 1})
        if crafted:
            break
    return {"target": target, "inventory": inventory, "log": log,
            "success": crafted, "n_steps": len(log)}


def generate_life(world: AlchemyWorld, player, n_episodes: int,
                  inv_size: int = 8, seed: int = 0,
                  holdout: set = frozenset()) -> list:
    """Batched data collection: inventory always contains a recipe for the
    target (winnable by construction) and NEVER both members of a holdout
    pair (held-out split enforced by the physics, not by luck)."""
    rng = np.random.default_rng(seed)
    names = sorted(world.ingredients)
    targets = [t for t in world.craftable_targets()
               if any(tuple(sorted(p)) not in holdout
                      for p in world.recipe_pairs_for(t))]
    episodes = []
    for e in range(n_episodes):
        target = targets[int(rng.integers(len(targets)))]
        recipes = [p for p in world.recipe_pairs_for(target)
                   if tuple(sorted(p)) not in holdout]
        a, b = recipes[int(rng.integers(len(recipes)))]
        inv = [a, b]
        rest = [n for n in names if n not in inv]
        rng.shuffle(rest)
        for n in rest:
            if len(inv) >= inv_size:
                break
            if all(tuple(sorted((n, m))) not in holdout for m in inv):
                inv.append(n)
        episodes.append(run_episode(world, player, target, sorted(inv)))
    return episodes


def seen_pairs(episodes: list) -> set:
    out = set()
    for ep in episodes:
        for st in ep["log"]:
            _, a, b = st["action"].split(" ")
            out.add(tuple(sorted([a, b])))
    return out
