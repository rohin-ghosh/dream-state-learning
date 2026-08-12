"""S0 sanity gates (SIZING §1/§5) — runnable on DAY 1 of the lease, and on CPU
today via MockTextPlayer. Closes redteam_6 finding #5 (0/5 gates runnable).

gate_calibration: win@manual vs win@no-context — the model↔game difficulty
invariant. Returns pass/fail per gate + the raw rates, so the recalibration
rules of SIZING §5 have their measurements.
"""

from __future__ import annotations

import numpy as np

from game import World
from .llm_player import play_episode


def gate_calibration(backend_factory, n_worlds: int = 3, eps_per_world: int = 10,
                     seed: int = 0, max_steps: int = 60,
                     thresh_manual: float = 0.85, thresh_nomem: float = 0.35,
                     depth: int = 4, **world_kw) -> dict:
    """backend_factory: (world, mode, episode) -> Backend. Fresh per episode so
    per-episode scratch state (MockTextPlayer) can't leak across episodes."""
    wins = {"manual": [], "none": []}
    episodes = []          # per-episode ledger: failures must be attributable
    for w_i in range(n_worlds):
        world = World.generate(f"gate_{w_i}", seed=5000 + seed * 13 + w_i,
                               depth=depth, **world_kw)
        goals = list(world.dag.recipes)
        rng = np.random.default_rng(seed + w_i)
        for e in range(eps_per_world):
            goal = goals[int(rng.integers(len(goals)))]
            for mode in ("manual", "none"):
                b = backend_factory(world, mode, e)
                r = play_episode(world, b, goal, episode_seed=e,
                                 context_mode=mode, max_steps=max_steps)
                wins[mode].append(r["success"])
                episodes.append({"world": world.world_id, "goal": goal,
                                 "depth": int(world.dag.depth_of[goal]),
                                 "mode": mode, "success": bool(r["success"]),
                                 "steps": int(r["steps"]),
                                 "timeout": bool(not r["success"]
                                                 and r["steps"] >= max_steps)})
    win_manual = float(np.mean(wins["manual"]))
    win_none = float(np.mean(wins["none"]))
    return {
        "win_at_manual": win_manual,
        "win_at_none": win_none,
        "gate_reasoning_ok": win_manual >= thresh_manual,
        "gate_knowledge_wall_ok": win_none <= thresh_nomem,
        "room": win_manual - win_none,
        "n_episodes_per_mode": len(wins["manual"]),
        "episodes": episodes,
    }
