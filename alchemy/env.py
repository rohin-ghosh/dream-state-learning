"""Episode loop + append-only life log (SPEC_V2 §2, §6 State)."""

from __future__ import annotations

import numpy as np

from alchemy.world import AlchemyWorld


def run_episode(world: AlchemyWorld, player, target: str,
                inventory: list, max_steps: int = 12,
                memory_ctx: str = "", plan_items: set = None,
                target_depth: int = 1) -> dict:
    """One life episode. State per step = goal, holdings, last obs, value.
    Value = remaining depth toward the target (0 = crafted) — exact, from
    the true crafting graph (the dream's hindsight signal)."""
    plan_items = plan_items or set()

    def value(holds, crafted):
        if crafted:
            return 0
        prog = max([world.tier_of(h) for h in holds
                    if h in plan_items] or [0])
        return max(1, target_depth - prog)

    holdings = list(inventory)
    log, crafted = [], False
    obs = f"You arrive at the bench. You hold: {', '.join(holdings)}."
    for step in range(max_steps):
        state = {"goal": target, "holdings": list(holdings),
                 "obs": obs, "value": value(holdings, crafted)}
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
                    "obs": obs, "value_after": value(holdings, crafted)})
        if crafted:
            break
    return {"target": target, "inventory": inventory, "log": log,
            "success": crafted, "n_steps": len(log),
            "target_depth": target_depth}


DEPTH_MIX = {1: 0.3, 2: 0.3, 3: 0.25, 4: 0.15}   # chain-depth target mixture


def generate_life(world: AlchemyWorld, player, n_episodes: int,
                  inv_size: int = 8, seed: int = 0,
                  holdout: set = frozenset(),
                  depth_mix: dict = None) -> list:
    """Batched data collection. Targets are depth-mixed chain goals; the
    inventory always contains the base ingredients of one valid plan whose
    base combines avoid holdout pairs (winnable by construction; held-out
    split enforced by the physics, not by luck)."""
    rng = np.random.default_rng(seed)
    names = sorted(world.ingredients)
    depth_mix = depth_mix or DEPTH_MIX
    idx = world.build_chain_index(max(depth_mix))
    # keep targets whose plan's BASE combines avoid holdout entirely
    pools = {d: [] for d in depth_mix}
    for item, (d, plan) in idx.items():
        if d not in pools:
            continue
        base_ings = sorted({x for a, b, _ in plan for x in (a, b)
                            if world.tier_of(x) == 0})
        # ALL pairs among the plan's base ingredients must avoid holdout
        # (they will be co-present in the inventory)
        import itertools as _it
        if any(tuple(sorted(p)) in holdout
               for p in _it.combinations(base_ings, 2)):
            continue
        pools[d].append((item, d, plan, base_ings))
    depths = sorted(depth_mix)
    probs = np.array([depth_mix[d] for d in depths], float)
    probs /= probs.sum()
    episodes = []
    for e in range(n_episodes):
        while True:
            d = depths[int(rng.choice(len(depths), p=probs))]
            if pools[d]:
                break
        target, td, plan, base_ings = pools[d][int(rng.integers(len(pools[d])))]
        inv = list(base_ings)
        rest = [n for n in names if n not in inv]
        rng.shuffle(rest)
        for n in rest:
            if len(inv) >= max(inv_size, len(base_ings)):
                break
            if all(tuple(sorted((n, m))) not in holdout for m in inv):
                inv.append(n)
        plan_items = {p for _, _, p in plan}
        episodes.append(run_episode(
            world, player, target, sorted(inv),
            max_steps=len(plan) + 8, plan_items=plan_items,
            target_depth=td))
    return episodes


def seen_pairs(episodes: list) -> set:
    out = set()
    for ep in episodes:
        for st in ep["log"]:
            _, a, b = st["action"].split(" ")
            out.add(tuple(sorted([a, b])))
    return out
