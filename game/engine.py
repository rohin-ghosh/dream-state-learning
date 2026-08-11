"""FeltCraft — persistent-world text crafting game with ground-truth fact labels.

Adapted from archive/dream_state/environments/minecraft_sim.py (verified July 2026)
with the three v2 upgrades from PREWORK/regime-sweep:
  1. procedural DEEP crafting hierarchies (game/dag.py) — complexity is a knob;
  2. SCRIPT-BEFORE-TEXT fact labelling — every episode emits ground-truth
     STRUCTURAL facts (recipe edges, resource-location bindings) and DETAIL facts
     (per-episode decor, incidental counts) BEFORE text is rendered from them,
     so labels are exact by construction (Ground-Truth-First recipe, 2607.21962);
  3. oracle-value + per-step TD salience hooks on every step.

Interface mirrors the archived sim (LLM-playable): explore / move <loc> /
gather <raw> / craft <item> / inspect.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from .dag import CraftDAG, gen_dag, oracle_value, td_salience, requirements

DECOR_WORDS = ("red", "blue", "mossy", "dusty", "gleaming", "cracked", "ancient",
               "damp", "bright", "faded", "rusty", "polished")


@dataclass
class Fact:
    kind: str        # 'recipe' | 'location' | 'decor' | 'count'
    text: str        # canonical fact string (probe target)
    structural: bool
    step: int = -1   # step index the fact was experienced at (-1 = episode setup)


@dataclass
class World:
    """Persistent across episodes: DAG + fixed resource locations."""
    world_id: str
    dag: CraftDAG
    raw_locations: dict          # raw -> location name
    locations: list              # all location names
    seed: int

    @classmethod
    def generate(cls, world_id: str, seed: int, depth=4, branching=3, n_raw=6,
                 n_locations=8):
        rng = np.random.default_rng(seed)
        dag = gen_dag(seed, depth=depth, branching=branching, n_raw=n_raw)
        locations = [f"site_{i}" for i in range(n_locations)]
        raw_locations = {r: locations[int(rng.integers(n_locations))]
                         for r in dag.raws}
        return cls(world_id=world_id, dag=dag, raw_locations=raw_locations,
                   locations=locations, seed=seed)

    def structural_facts(self) -> list:
        """The world's ground-truth gist: recipe edges + location bindings."""
        fs = [Fact("recipe", f"crafting {it} requires {a} and {b}", True)
              for it, (a, b) in self.dag.recipes.items()]
        fs += [Fact("location", f"{r} is found at {l}", True)
               for r, l in self.raw_locations.items()]
        return fs


class FeltCraft:
    """One episode = one goal in a persistent world. Memory of prior episodes
    (known locations, recipes seen) is the AGENT's job — the env resets agent
    state each episode except what the caller injects via `known_locations`."""

    def __init__(self, world: World, max_steps: int = 60):
        self.w = world
        self.max_steps = max_steps
        self._rng = None
        self.reset_called = False

    # ------------------------------------------------------------ episode API
    def reset(self, goal: str, episode_seed: int = 0,
              known_locations: Optional[set] = None) -> dict:
        assert goal in self.w.dag.recipes, f"goal {goal} not craftable"
        self._rng = np.random.default_rng(self.w.seed * 100_003 + episode_seed)
        self.goal = goal
        self.inventory: dict = {}
        self.current_loc: Optional[str] = None
        self.known_locations: set = set(known_locations or ())
        self.steps = 0
        self.done = False
        self.success = False
        self.episode_facts: list = []
        self.trajectory: list = []
        # per-episode DETAIL decor (script-before-text). Emitted as facts only when
        # a site is VISITED (so every fact has a real step and real head salience —
        # redteam_4 fix: the 0.05 fallback constant was carrying the whole result).
        self._episode_seed = episode_seed
        self.decor = {l: DECOR_WORDS[int(self._rng.integers(len(DECOR_WORDS)))]
                      for l in self.w.locations}
        self._decor_emitted = set()
        self._V = self._value()
        obs = self._render_obs("You arrive. " + self._goal_text())
        return {"obs": obs, "oracle_V": self._V}

    def step(self, action: str) -> dict:
        assert not self.done, "episode finished"
        self.steps += 1
        act = action.strip().lower()
        v_before = self._V
        msg = self._exec(act)
        self._V = self._value()
        sal = td_salience(v_before, self._V)
        if self.inventory.get(self.goal, 0) > 0:
            self.done, self.success = True, True
            msg += f" GOAL COMPLETE: you crafted {self.goal}!"
        elif self.steps >= self.max_steps:
            self.done = True
            msg += " (out of time)"
        obs = self._render_obs(msg)
        rec = {"obs": obs, "action": act, "oracle_V": self._V,
               "salience": sal, "done": self.done, "success": self.success}
        self.trajectory.append(rec)
        return rec

    # ------------------------------------------------------------- internals
    def _exec(self, act: str) -> str:
        w = self.w
        if act.startswith("explore"):
            unknown = [l for l in w.locations if l not in self.known_locations]
            if not unknown:
                return "Nothing new to explore."
            loc = unknown[int(self._rng.integers(len(unknown)))]
            self.known_locations.add(loc)
            self.current_loc = loc
            here = [r for r, l in w.raw_locations.items() if l == loc]
            for r in here:   # discovering a binding = experiencing a structural fact
                self.episode_facts.append(
                    Fact("location", f"{r} is found at {loc}", True, self.steps))
            self._emit_decor(loc)
            return (f"You explore and find {loc} ({self.decor[loc]}). "
                    f"Resources here: {', '.join(here) or 'none'}.")
        if act.startswith("move"):
            # Sites are visible landmarks: move works on any VALID site name.
            # (Knowledge must be ACTIONABLE — a remembered/manual-known binding lets
            # you go straight there; what visiting teaches you is the CONTENTS.)
            target = act.split(None, 1)[1].strip() if " " in act else ""
            if target not in w.locations:
                return f"There is no site called {target or '<nothing>'}."
            self.current_loc = target
            first_visit = target not in self.known_locations
            self.known_locations.add(target)
            here = [r for r, l in w.raw_locations.items() if l == target]
            if first_visit:
                for r in here:   # seeing contents = experiencing the binding
                    self.episode_facts.append(
                        Fact("location", f"{r} is found at {target}", True,
                             self.steps))
                self._emit_decor(target)
            return (f"You move to {target} ({self.decor[target]}). "
                    f"Resources here: {', '.join(here) or 'none'}.")
        if act.startswith("gather"):
            res = act.split(None, 1)[1].strip() if " " in act else ""
            if res not in w.dag.raws:
                return f"{res or '<nothing>'} is not a gatherable resource."
            if self.current_loc != w.raw_locations[res]:
                return f"No {res} here."
            self.inventory[res] = self.inventory.get(res, 0) + 1
            self.episode_facts.append(
                Fact("count", f"gathered {res} at step {self.steps} of episode {self._episode_seed}",
                     False, self.steps))
            return f"You gather 1 {res}. Inventory: {self._inv_text()}."
        if act.startswith("craft"):
            item = act.split(None, 1)[1].strip() if " " in act else ""
            if item not in w.dag.recipes:
                return f"{item or '<nothing>'} has no recipe."
            a, b = w.dag.recipes[item]
            if self.inventory.get(a, 0) < 1 or self.inventory.get(b, 0) < 1:
                return (f"Crafting {item} requires {a} and {b} — you lack "
                        f"{'both' if not self.inventory.get(a) and not self.inventory.get(b) else (a if not self.inventory.get(a) else b)}.")
            self.inventory[a] -= 1
            self.inventory[b] -= 1
            self.inventory[item] = self.inventory.get(item, 0) + 1
            self.episode_facts.append(   # using a recipe = experiencing the edge
                Fact("recipe", f"crafting {item} requires {a} and {b}", True, self.steps))
            return f"You craft {item}. Inventory: {self._inv_text()}."
        if act.startswith("inspect"):
            return (f"Goal: craft {self.goal}. At: {self.current_loc or 'nowhere'}. "
                    f"Known: {sorted(self.known_locations)}. "
                    f"Inventory: {self._inv_text()}.")
        return "Unknown action. Use: explore | move <loc> | gather <raw> | craft <item> | inspect."

    def _emit_decor(self, loc: str) -> None:
        if loc in self._decor_emitted:
            return
        self._decor_emitted.add(loc)
        self.episode_facts.append(
            Fact("decor", f"{loc} looked {self.decor[loc]} during episode "
                 f"{self._episode_seed}", False, self.steps))

    def _value(self) -> float:
        return oracle_value(self.w.dag, self.goal, self.inventory,
                            self.w.raw_locations, self.known_locations,
                            self.current_loc)

    def _goal_text(self) -> str:
        return f"Your goal: craft {self.goal}."

    def _inv_text(self) -> str:
        items = [f"{k}x{v}" for k, v in self.inventory.items() if v > 0]
        return ", ".join(items) or "empty"

    def _render_obs(self, msg: str) -> str:
        return f"[step {self.steps}] {msg}"


def scripted_noisy_play(env: FeltCraft, goal: str, episode_seed: int = 0,
                        known_locations: Optional[set] = None,
                        detour_rate: float = 0.25, seed: int = 0):
    """Solver + DETOURS: with prob detour_rate per episode, first executes a
    sub-plan crafting a random depth-1 item NOT on the goal path (gather its raws,
    craft it). Detour events are real craft/gather/move events with ~ZERO oracle
    salience (no goal progress) — the within-action-type variance that makes
    salience ≠ action-type (redteam_4 fix: breaks the type≡label degeneracy)."""
    rng = np.random.default_rng(seed * 7919 + episode_seed)
    env.reset(goal, episode_seed, known_locations)
    w = env.w
    if rng.random() < detour_rate:
        on_path = set(requirements(w.dag, goal, {})["crafts"]) | {goal}
        d1 = [i for i in w.dag.recipes if w.dag.depth_of[i] == 1
              and i not in on_path]
        if d1:
            item = d1[int(rng.integers(len(d1)))]
            a, b = w.dag.recipes[item]
            for raw in (a, b):
                loc = w.raw_locations[raw]
                if env.current_loc != loc and not env.done:
                    env.step(f"move {loc}")
                if not env.done:
                    env.step(f"gather {raw}")
            if not env.done:
                env.step(f"craft {item}")
    _solve(env, goal)
    return env


def scripted_optimal_play(env: FeltCraft, goal: str, episode_seed: int = 0,
                          known_locations: Optional[set] = None):
    """Deterministic solver: explore until needed raws known, gather, craft in
    dependency order. Used for tests + optimal-trajectory generation."""
    env.reset(goal, episode_seed, known_locations)
    _solve(env, goal)
    return env


def _solve(env: FeltCraft, goal: str):
    w = env.w
    while not env.done:
        need = requirements(w.dag, goal, env.inventory)
        missing_raws = [r for r, n in need["raw_needs"].items()
                        for _ in range(n)]
        if missing_raws:
            r = missing_raws[0]
            loc = w.raw_locations[r]
            if loc not in env.known_locations:
                env.step("explore")
            elif env.current_loc != loc:
                env.step(f"move {loc}")
            else:
                env.step(f"gather {r}")
            continue
        craftable = [c for c in need["crafts"]
                     if all(env.inventory.get(i, 0) >= 1 for i in w.dag.recipes[c])]
        if craftable:
            env.step(f"craft {craftable[0]}")
        else:
            env.step("inspect")   # should not happen; avoids infinite loop
            break
