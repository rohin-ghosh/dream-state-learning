"""
Generate Minecraft crafting task sequences for Dream-State Learning.

Each world is a persistent environment with fixed resource locations.
Episodes within a world require remembering locations from prior episodes.

Output: data/minecraft_tasks/worlds.json
"""

from __future__ import annotations

import json
import random
from dataclasses import asdict
from pathlib import Path

import typer

from dream_state.environments.minecraft_sim import (
    WorldState,
    get_chain_depth,
    get_goals_by_depth,
    RECIPES,
    RAW_RESOURCES,
)

app = typer.Typer(pretty_exceptions_enable=False)


def generate_episode_sequence(
    world: WorldState,
    n_episodes: int,
    min_depth: int,
    max_depth: int,
    rng: random.Random,
) -> list[dict]:
    """
    Generate a sequence of episodes for a world.
    Later episodes require resources found in earlier episodes.
    """
    from dream_state.environments.minecraft_sim import is_goal_achievable

    by_depth = get_goals_by_depth()
    available_goals = []
    for d in range(min_depth, max_depth + 1):
        available_goals.extend(by_depth.get(d, []))

    # Only keep goals whose full raw-resource closure exists in this world
    available_goals = [g for g in available_goals if is_goal_achievable(g, world)]
    if not available_goals:
        raise ValueError(f"No achievable goals in world {world.world_id} — regenerate world")

    episodes = []
    # Track what resources have been "seen" in prior episodes
    # (simulates what an agent with perfect memory would know)
    resources_seen: set[str] = set()

    for ep_idx in range(n_episodes):
        goal = rng.choice(available_goals)
        from dream_state.environments.minecraft_sim import get_crafting_chain
        chain = get_crafting_chain(goal)
        raw_needed = [item for item in chain if item in RAW_RESOURCES]

        # Cross-episode dependency: later episodes explicitly require
        # resources that were available in prior episodes
        cross_episode_deps = []
        for resource in raw_needed:
            if resource in resources_seen:
                cross_episode_deps.append(resource)

        # Update seen resources
        for loc in world.locations.values():
            resources_seen.update(loc.resources.keys())

        episodes.append({
            "episode_id": f"ep_{ep_idx:03d}",
            "goal_item": goal,
            "chain_depth": get_chain_depth(goal),
            "crafting_chain": chain,
            "raw_resources_needed": list(set(raw_needed)),
            "cross_episode_dependencies": cross_episode_deps,
            "requires_memory": len(cross_episode_deps) > 0,
        })

    return episodes


@app.command()
def main(
    n_worlds: int = typer.Option(5, "--n-worlds", help="Number of persistent worlds"),
    episodes_per_world: int = typer.Option(10, "--episodes-per-world"),
    min_depth: int = typer.Option(2, "--min-depth"),
    max_depth: int = typer.Option(5, "--max-depth"),
    seed: int = typer.Option(42, "--seed"),
    output: Path = typer.Option(Path("data/minecraft_tasks/worlds.json"), "--output"),
):
    output.parent.mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed)

    worlds = []
    for w_idx in range(n_worlds):
        world_seed = rng.randint(0, 99999)
        world = WorldState.generate(f"world_{w_idx:02d}", seed=world_seed)
        episodes = generate_episode_sequence(
            world, episodes_per_world, min_depth, max_depth, rng
        )

        # Count cross-episode dependencies
        n_requires_memory = sum(1 for e in episodes if e["requires_memory"])

        worlds.append({
            "world_id": world.world_id,
            "world_seed": world_seed,
            "biome": world.biome,
            "n_locations": len(world.locations),
            "n_episodes": len(episodes),
            "n_requires_memory": n_requires_memory,
            "episodes": episodes,
            "locations": {
                name: {
                    "coords": list(loc.coords),
                    "biome": loc.biome,
                    "resources": loc.resources,
                }
                for name, loc in world.locations.items()
            },
        })

    with open(output, "w") as f:
        json.dump(worlds, f, indent=2)

    total_eps = sum(w["n_episodes"] for w in worlds)
    total_mem = sum(w["n_requires_memory"] for w in worlds)
    typer.echo(f"Generated {n_worlds} worlds, {total_eps} episodes → {output}")
    typer.echo(f"Episodes requiring cross-episode memory: {total_mem}/{total_eps}")

    typer.echo("\nBy world:")
    for w in worlds:
        typer.echo(
            f"  {w['world_id']} ({w['biome']}): "
            f"{w['n_episodes']} episodes, "
            f"{w['n_requires_memory']} need memory"
        )


if __name__ == "__main__":
    app()
