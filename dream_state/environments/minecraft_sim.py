"""
Minecraft crafting simulator — text-based environment for Dream-State Learning.

Models a persistent world where:
- Resource locations are fixed per world but unknown to the agent initially
- Crafting follows the real Minecraft DAG (subset)
- Agent must remember resource locations across episodes to be efficient
- Cross-episode memory directly impacts performance (steps to goal)

The simulator is purely text-based — no graphics, no Minecraft install needed.
"""

from __future__ import annotations

import random
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Crafting DAG
# ---------------------------------------------------------------------------

# (inputs -> output, quantity)
# inputs: dict of {item: count_needed}
RECIPES: dict[str, tuple[dict[str, int], int]] = {
    # Tier 1 — raw processing
    "oak_planks":       ({"oak_log": 1}, 4),
    "spruce_planks":    ({"spruce_log": 1}, 4),
    "stick":            ({"oak_planks": 2}, 4),
    "torch":            ({"stick": 1, "coal": 1}, 4),
    "charcoal":         ({"oak_log": 1, "furnace": 1}, 1),  # smelting
    # Tier 2 — basic tools
    "crafting_table":   ({"oak_planks": 4}, 1),
    "wooden_pickaxe":   ({"stick": 2, "oak_planks": 3, "crafting_table": 1}, 1),
    "wooden_axe":       ({"stick": 2, "oak_planks": 3, "crafting_table": 1}, 1),
    "wooden_shovel":    ({"stick": 2, "oak_planks": 1, "crafting_table": 1}, 1),
    # Tier 3 — stone tools (requires mining stone with wooden pickaxe)
    "furnace":          ({"cobblestone": 8, "crafting_table": 1}, 1),
    "stone_pickaxe":    ({"stick": 2, "cobblestone": 3, "crafting_table": 1}, 1),
    "stone_axe":        ({"stick": 2, "cobblestone": 3, "crafting_table": 1}, 1),
    "stone_sword":      ({"stick": 1, "cobblestone": 2, "crafting_table": 1}, 1),
    # Tier 4 — iron (requires furnace + iron ore + stone pickaxe)
    "iron_ingot":       ({"iron_ore": 1, "furnace": 1, "coal": 1}, 1),
    "iron_pickaxe":     ({"stick": 2, "iron_ingot": 3, "crafting_table": 1}, 1),
    "iron_sword":       ({"stick": 1, "iron_ingot": 2, "crafting_table": 1}, 1),
    "iron_axe":         ({"stick": 2, "iron_ingot": 3, "crafting_table": 1}, 1),
    # Tier 5 — advanced
    "bucket":           ({"iron_ingot": 3, "crafting_table": 1}, 1),
    "compass":          ({"iron_ingot": 4, "redstone": 1, "crafting_table": 1}, 1),
    "bow":              ({"stick": 3, "string": 3, "crafting_table": 1}, 1),
}

# Raw resources that must be gathered from the world (not crafted)
RAW_RESOURCES = [
    "oak_log", "spruce_log", "cobblestone", "coal", "iron_ore",
    "redstone", "string", "gravel", "sand", "clay",
]

# Which tool is needed to mine each resource efficiently
MINING_REQUIREMENTS: dict[str, Optional[str]] = {
    "oak_log":      "wooden_axe",
    "spruce_log":   "wooden_axe",
    "cobblestone":  "wooden_pickaxe",
    "coal":         "wooden_pickaxe",
    "iron_ore":     "stone_pickaxe",
    "redstone":     "iron_pickaxe",
    "string":       None,   # from spiders, no tool needed
    "gravel":       "wooden_shovel",
    "sand":         "wooden_shovel",
    "clay":         "wooden_shovel",
}

# Biome types and what resources spawn there
BIOME_RESOURCES: dict[str, list[str]] = {
    "forest":   ["oak_log", "spruce_log", "coal", "string"],
    "plains":   ["oak_log", "coal", "string", "gravel"],
    "mountain": ["cobblestone", "coal", "iron_ore", "gravel"],
    "cave":     ["cobblestone", "coal", "iron_ore", "redstone"],
    "swamp":    ["oak_log", "clay", "sand", "string"],
    "desert":   ["sand", "gravel", "coal", "redstone"],
}


# ---------------------------------------------------------------------------
# World state
# ---------------------------------------------------------------------------

@dataclass
class Location:
    coords: tuple[int, int]
    biome: str
    resources: dict[str, int]   # resource -> quantity available
    visited: bool = False
    name: str = ""

    def __post_init__(self):
        if not self.name:
            self.name = f"{self.biome}_{self.coords[0]}_{self.coords[1]}"


@dataclass
class WorldState:
    """Persistent world — locations and their resources are fixed across episodes."""
    world_id: str
    biome: str
    locations: dict[str, Location]    # location_name -> Location
    seed: int

    @classmethod
    def generate(cls, world_id: str, seed: int, n_locations: int = 8) -> "WorldState":
        rng = random.Random(seed)
        biome = rng.choice(list(BIOME_RESOURCES.keys()))
        available = BIOME_RESOURCES[biome]

        locations = {}
        for i in range(n_locations):
            coords = (rng.randint(0, 20), rng.randint(0, 20))
            loc_biome = biome if rng.random() < 0.6 else rng.choice(list(BIOME_RESOURCES.keys()))
            loc_resources = {}
            for res in BIOME_RESOURCES[loc_biome]:
                if rng.random() < 0.5:
                    loc_resources[res] = rng.randint(2, 8)
            loc = Location(
                coords=coords,
                biome=loc_biome,
                resources=loc_resources,
                name=f"{loc_biome}_{i}",
            )
            locations[loc.name] = loc

        return cls(world_id=world_id, biome=biome, locations=locations, seed=seed)


@dataclass
class AgentState:
    """Per-episode agent state — resets each episode but memory persists externally."""
    inventory: dict[str, int] = field(default_factory=dict)
    current_location: str = "spawn"
    known_locations: dict[str, tuple[int, int]] = field(default_factory=dict)
    steps: int = 0
    log: list[str] = field(default_factory=list)

    def has(self, item: str, count: int = 1) -> bool:
        return self.inventory.get(item, 0) >= count

    def add(self, item: str, count: int = 1):
        self.inventory[item] = self.inventory.get(item, 0) + count

    def remove(self, item: str, count: int = 1):
        self.inventory[item] = max(0, self.inventory.get(item, 0) - count)


# ---------------------------------------------------------------------------
# Episode result
# ---------------------------------------------------------------------------

@dataclass
class MinecraftEpisodeResult:
    world_id: str
    episode_id: str
    goal_item: str
    goal_depth: int          # crafting chain depth
    success: bool
    steps_taken: int
    optimal_steps: int       # minimum steps if agent knew all locations
    efficiency: float        # optimal_steps / steps_taken (1.0 = perfect)
    inventory_final: dict[str, int]
    locations_discovered: list[str]
    trajectory_text: str
    crafting_chain: list[str]   # the dependency chain for this goal


# ---------------------------------------------------------------------------
# Simulator
# ---------------------------------------------------------------------------

class MinecraftSim:
    """
    Text-based Minecraft crafting simulator.

    Each episode has a goal item. The agent must gather resources and craft
    the item following the crafting DAG. Resource locations are fixed in the
    world but the agent must discover/remember them.
    """

    MAX_STEPS = 40

    def __init__(self, world: WorldState):
        self.world = world
        self._agent: Optional[AgentState] = None
        self._goal: Optional[str] = None
        self._done: bool = False
        self._trajectory: list[str] = []

    def reset(self, goal_item: str, known_locations: Optional[dict] = None) -> str:
        """Start a new episode. known_locations injects prior memory."""
        self._goal = goal_item
        self._done = False
        self._trajectory = []
        self._agent = AgentState()
        if known_locations:
            self._agent.known_locations = dict(known_locations)

        obs = self._make_observation()
        self._trajectory.append(f"GOAL: {goal_item}")
        self._trajectory.append(f"OBS: {obs}")
        return obs

    def step(self, action: str) -> tuple[str, bool, dict]:
        """Execute action, return (observation, done, info)."""
        if self._done:
            return "Episode already done.", True, {}

        self._agent.steps += 1
        action = action.strip().lower()
        self._trajectory.append(f"ACTION: {action}")

        obs, success = self._execute(action)

        if success and self._goal in self._agent.inventory:
            self._done = True
            obs += f"\nYou have crafted {self._goal}! Goal complete."

        if self._agent.steps >= self.MAX_STEPS:
            self._done = True
            obs += "\nMax steps reached."

        self._trajectory.append(f"OBS: {obs}")
        return obs, self._done, {"success": self._goal in self._agent.inventory}

    def get_known_locations(self) -> dict[str, tuple[int, int]]:
        return dict(self._agent.known_locations)

    def get_trajectory_text(self) -> str:
        return "\n".join(self._trajectory)

    def _execute(self, action: str) -> tuple[str, bool]:
        agent = self._agent
        world = self.world

        # move <location_name> or move to <coords>
        if action.startswith("move"):
            return self._handle_move(action)

        # pick_up <resource> or gather <resource>
        elif action.startswith(("pick_up", "gather", "mine", "chop")):
            return self._handle_gather(action)

        # craft <item>
        elif action.startswith("craft"):
            return self._handle_craft(action)

        # explore — move to an unknown location
        elif action.startswith("explore"):
            return self._handle_explore()

        # inspect or look
        elif action.startswith(("inspect", "look")):
            return self._handle_inspect()

        # place <item>
        elif action.startswith("place"):
            parts = action.split()
            item = parts[1] if len(parts) > 1 else ""
            if agent.has(item):
                obs = f"You place the {item} here."
                return obs, True
            return f"You don't have {item}.", False

        else:
            return f"Unknown action: '{action}'. Try: move, gather, craft, inspect.", False

    def _handle_explore(self) -> tuple[str, bool]:
        agent = self._agent
        world = self.world
        unvisited = [n for n, l in world.locations.items() if not l.visited]
        if not unvisited:
            return "You have explored all locations in this area.", False
        loc_name = unvisited[0]
        loc = world.locations[loc_name]
        loc.visited = True
        agent.current_location = loc_name
        agent.known_locations[loc_name] = loc.coords
        res_list = ", ".join(f"{r} x{q}" for r, q in loc.resources.items() if q > 0) or "nothing useful"
        return (
            f"You explore and discover {loc_name} at {loc.coords}. Biome: {loc.biome}. "
            f"You see: {res_list}. "
            f"Known locations: {list(agent.known_locations.keys())}."
        ), True

    def _handle_move(self, action: str) -> tuple[str, bool]:
        agent = self._agent
        world = self.world
        parts = action.replace("move to", "move").replace("go to", "move").split()

        # move to known location by name
        target = " ".join(parts[1:]).strip()
        if not target:
            return "Specify where to move.", False

        # find matching location
        matched = None
        for loc_name, loc in world.locations.items():
            if target in loc_name or loc_name in target:
                matched = loc_name
                break
        # also check known_locations by name
        if not matched and target in agent.known_locations:
            # find location at those coords
            coords = agent.known_locations[target]
            for loc_name, loc in world.locations.items():
                if loc.coords == coords:
                    matched = loc_name
                    break

        if not matched:
            # exploring unknown area — random discovery
            unvisited = [n for n, l in world.locations.items() if not l.visited]
            if unvisited:
                matched = unvisited[0]
            else:
                return "No new locations to explore.", False

        loc = world.locations[matched]
        loc.visited = True
        agent.current_location = matched
        agent.known_locations[matched] = loc.coords

        res_list = ", ".join(f"{r} x{q}" for r, q in loc.resources.items() if q > 0) or "nothing useful"
        return (
            f"You move to {matched} {loc.coords}. Biome: {loc.biome}. "
            f"You see: {res_list}."
        ), True

    def _handle_gather(self, action: str) -> tuple[str, bool]:
        agent = self._agent
        world = self.world
        parts = action.split()
        resource = " ".join(parts[1:]).strip().replace(" ", "_")

        if not resource:
            return "Specify what to gather.", False

        loc = world.locations.get(agent.current_location)
        if not loc:
            return "You are at spawn. Move to a location first.", False

        available = loc.resources.get(resource, 0)
        if available <= 0:
            return f"No {resource} here.", False

        # Check tool requirement
        required_tool = MINING_REQUIREMENTS.get(resource)
        if required_tool and not agent.has(required_tool):
            return (
                f"You need a {required_tool} to gather {resource} efficiently. "
                f"You can try but it takes much longer (+3 steps)."
            ), False

        qty = min(available, 4)
        loc.resources[resource] -= qty
        agent.add(resource, qty)
        return f"You gather {qty}x {resource}. Inventory: {self._inv_str()}.", True

    def _handle_craft(self, action: str) -> tuple[str, bool]:
        agent = self._agent
        parts = action.replace("craft ", "").strip()
        item = parts.replace(" ", "_")

        if item not in RECIPES:
            close = [k for k in RECIPES if parts.replace("_", " ") in k.replace("_", " ")]
            hint = f" Did you mean: {close[0]}?" if close else ""
            return f"Unknown recipe: {item}.{hint}", False

        inputs, qty_out = RECIPES[item]
        missing = []
        for ingredient, needed in inputs.items():
            if ingredient == "crafting_table":
                if not agent.has("crafting_table") and agent.current_location == "spawn":
                    missing.append("crafting_table (place one first)")
            elif not agent.has(ingredient, needed):
                have = agent.inventory.get(ingredient, 0)
                missing.append(f"{ingredient} (need {needed}, have {have})")

        if missing:
            return f"Missing ingredients: {', '.join(missing)}.", False

        for ingredient, needed in inputs.items():
            if ingredient != "crafting_table":
                agent.remove(ingredient, needed)
        agent.add(item, qty_out)
        return f"You craft {qty_out}x {item}. Inventory: {self._inv_str()}.", True

    def _handle_inspect(self) -> tuple[str, bool]:
        agent = self._agent
        world = self.world
        loc = world.locations.get(agent.current_location)
        if not loc:
            lines = ["You are at spawn."]
            lines.append(f"Inventory: {self._inv_str()}")
            lines.append(f"Known locations: {list(agent.known_locations.keys())}")
            return "\n".join(lines), True

        res_list = ", ".join(f"{r} x{q}" for r, q in loc.resources.items() if q > 0) or "depleted"
        return (
            f"Location: {loc.name} {loc.coords}, biome: {loc.biome}. "
            f"Resources: {res_list}. "
            f"Inventory: {self._inv_str()}. "
            f"Known locations: {list(agent.known_locations.keys())}."
        ), True

    def _make_observation(self) -> str:
        agent = self._agent
        chain = get_crafting_chain(self._goal)
        chain_str = " → ".join(chain)
        known_str = (
            ", ".join(f"{n} at {c}" for n, c in agent.known_locations.items())
            if agent.known_locations else "none"
        )
        return (
            f"World: {self.world.world_id} ({self.world.biome} biome). "
            f"Goal: craft {self._goal}. "
            f"Crafting chain: {chain_str}. "
            f"Known locations from memory: {known_str}. "
            f"Inventory: {self._inv_str() or 'empty'}. "
            f"You are at spawn."
        )

    def _inv_str(self) -> str:
        return ", ".join(f"{k} x{v}" for k, v in self._agent.inventory.items() if v > 0) or "empty"


# ---------------------------------------------------------------------------
# Crafting chain utilities
# ---------------------------------------------------------------------------

def get_crafting_chain(item: str, visited: Optional[set] = None) -> list[str]:
    """Return the full dependency chain for crafting an item (DFS)."""
    if visited is None:
        visited = set()
    if item in visited or item not in RECIPES:
        return [item]
    visited.add(item)
    chain = []
    inputs, _ = RECIPES[item]
    for ingredient in inputs:
        if ingredient != "crafting_table" and ingredient in RECIPES:
            chain.extend(get_crafting_chain(ingredient, visited))
    chain.append(item)
    return chain


def get_chain_depth(item: str) -> int:
    return len(get_crafting_chain(item))


def get_goals_by_depth() -> dict[int, list[str]]:
    """Group craftable items by chain depth."""
    by_depth: dict[int, list[str]] = {}
    for item in RECIPES:
        d = get_chain_depth(item)
        by_depth.setdefault(d, []).append(item)
    return by_depth


def compute_optimal_steps(goal: str, known_locations: dict, world: WorldState) -> int:
    """
    Estimate minimum steps to craft goal given known locations.
    Known locations skip exploration steps.
    """
    chain = get_crafting_chain(goal)
    raw_needed = [item for item in chain if item in RAW_RESOURCES]
    steps = 0
    for resource in set(raw_needed):
        if any(resource in loc.resources and loc.resources[resource] > 0
               for loc in world.locations.values()):
            loc_name = next(
                n for n, l in world.locations.items()
                if resource in l.resources and l.resources[resource] > 0
            )
            if loc_name in known_locations:
                steps += 2  # move + gather
            else:
                steps += 4  # explore + move + gather (unknown)
    steps += len(chain)  # one craft step per item in chain
    return steps
