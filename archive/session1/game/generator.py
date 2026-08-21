"""Rollout infrastructure — batch worlds/goals/curricula + trajectory JSONL logs.

"A fuck ton of synthetic games" (PREWORK item 3): worlds are cheap, episodes are
seeded and replayable, and every trajectory carries per-step oracle values +
salience + the episode's ground-truth fact list — everything the head's offline
training (KVP-style) and the benchmark probes need, in one schema.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import numpy as np

from .engine import World, FeltCraft, scripted_optimal_play


def make_worlds(n: int, seed: int = 0, **world_kw) -> list:
    return [World.generate(f"world_{i:04d}", seed=seed * 10_007 + i, **world_kw)
            for i in range(n)]


def curriculum_goals(world: World, n_episodes: int, seed: int = 0,
                     max_depth: Optional[int] = None) -> list:
    """Goal per episode, depth-weighted toward deep items as episodes progress
    (regime verdict: rich/deep structure is where the window lives)."""
    rng = np.random.default_rng(seed)
    items = list(world.dag.recipes)
    depths = np.array([world.dag.depth_of[i] for i in items], float)
    if max_depth:
        keep = depths <= max_depth
        items = [i for i, k in zip(items, keep) if k]
        depths = depths[keep]
    goals = []
    for e in range(n_episodes):
        ramp = 0.5 + 1.5 * (e / max(1, n_episodes - 1))     # deepen over time
        w = depths ** ramp
        goals.append(items[int(rng.choice(len(items), p=w / w.sum()))])
    return goals


def trajectory_record(world: World, episode_idx: int, goal: str,
                      env: FeltCraft) -> dict:
    return {
        "world": world.world_id,
        "episode": episode_idx,
        "goal": goal,
        "success": env.success,
        "steps": env.steps,
        "trajectory": env.trajectory,           # obs/action/oracle_V/salience per step
        "facts": [{"kind": f.kind, "text": f.text, "structural": f.structural}
                  for f in env.episode_facts],
        "known_locations_end": sorted(env.known_locations),
    }


def generate_dataset(out_path: str, n_worlds: int = 4, episodes_per_world: int = 50,
                     seed: int = 0, agent: str = "scripted", max_steps: int = 60,
                     carry_locations: bool = True, **world_kw) -> dict:
    """Generate a JSONL dataset of played episodes. agent='scripted' uses the
    optimal solver (for oracle traces / head-training targets); the LLM tier will
    plug a model in via the same loop. carry_locations = the agent remembers
    site locations across episodes within a world (cross-episode memory ON)."""
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    n_success = n_total = 0
    with open(out, "w") as f:
        for world in make_worlds(n_worlds, seed=seed, **world_kw):
            known: set = set()
            goals = curriculum_goals(world, episodes_per_world, seed=seed)
            for e, goal in enumerate(goals):
                env = FeltCraft(world, max_steps=max_steps)
                if agent == "scripted":
                    scripted_optimal_play(env, goal, episode_seed=e,
                                          known_locations=known if carry_locations else None)
                else:
                    raise NotImplementedError("LLM agent plugs in at the GPU tier")
                if carry_locations:
                    known |= env.known_locations
                rec = trajectory_record(world, e, goal, env)
                f.write(json.dumps(rec) + "\n")
                n_success += env.success
                n_total += 1
    return {"path": str(out), "episodes": n_total,
            "success_rate": n_success / max(1, n_total)}
