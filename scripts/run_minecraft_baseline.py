"""
Minecraft baseline evaluation — zero_memory vs RAG.

Runs Qwen2.5-7B through a sequence of Minecraft crafting episodes.
Measures how well the agent uses cross-episode memory of resource locations.

Key metrics:
  - success_rate:          fraction of episodes where goal item was crafted
  - efficiency:            optimal_steps / actual_steps (1.0 = perfect)
  - location_reuse_rate:   fraction of known locations actually reused
  - structural_accuracy:   did agent follow correct crafting chain order?

Usage:
    python scripts/run_minecraft_baseline.py \
        --worlds data/minecraft_tasks/worlds.json \
        --condition zero_memory \
        --output outputs/minecraft_baseline/

    python scripts/run_minecraft_baseline.py \
        --worlds data/minecraft_tasks/worlds.json \
        --condition rag \
        --output outputs/minecraft_baseline/
"""

from __future__ import annotations

import json
import os
import re
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional

import torch
import typer
from transformers import AutoModelForCausalLM, AutoTokenizer

from dream_state.environments.minecraft_sim import (
    MinecraftSim,
    WorldState,
    compute_optimal_steps,
    get_crafting_chain,
)

app = typer.Typer(pretty_exceptions_enable=False)
MODEL_NAME = "Qwen/Qwen2.5-7B-Instruct"


# ---------------------------------------------------------------------------
# Prompt builders
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are an agent in a Minecraft-like world. Your goal is to craft a target item.
You interact by outputting one action at a time. Valid actions:
  - move <location_name>      (move to a known or new location)
  - explore                   (move to an unknown location)
  - gather <resource>         (pick up resource at current location)
  - craft <item>              (craft item if you have ingredients)
  - inspect                   (look around current location)

Think step by step about what you need to craft the goal item, then output exactly one action.
Format: THOUGHT: <reasoning> ACTION: <single action>"""


def build_zero_memory_prompt(obs: str, history: list[tuple[str, str, str]]) -> str:
    lines = [SYSTEM_PROMPT, "", f"Observation: {obs}", ""]
    for thought, action, next_obs in history[-6:]:
        lines.append(f"THOUGHT: {thought}")
        lines.append(f"ACTION: {action}")
        lines.append(f"Observation: {next_obs}")
        lines.append("")
    lines.append("THOUGHT:")
    return "\n".join(lines)


def build_rag_prompt(obs: str, history: list[tuple[str, str, str]], episode_memory: list[dict]) -> str:
    mem_text = ""
    if episode_memory:
        mem_text = "MEMORY FROM PAST EPISODES:\n"
        for m in episode_memory[-4:]:
            mem_text += f"  - {m['summary']}\n"
        mem_text += "\n"

    lines = [SYSTEM_PROMPT, "", mem_text, f"Observation: {obs}", ""]
    for thought, action, next_obs in history[-6:]:
        lines.append(f"THOUGHT: {thought}")
        lines.append(f"ACTION: {action}")
        lines.append(f"Observation: {next_obs}")
        lines.append("")
    lines.append("THOUGHT:")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Action parser
# ---------------------------------------------------------------------------

def parse_thought_action(response: str) -> tuple[str, str]:
    response = response.strip()
    thought_match = re.search(r"THOUGHT:\s*(.*?)(?:ACTION:|$)", response, re.DOTALL | re.IGNORECASE)
    action_match = re.search(r"ACTION:\s*(.+?)(?:\n|$)", response, re.IGNORECASE)

    thought = thought_match.group(1).strip() if thought_match else response[:100]
    action = action_match.group(1).strip() if action_match else "inspect"
    return thought, action


# ---------------------------------------------------------------------------
# Episode runner
# ---------------------------------------------------------------------------

@dataclass
class EpisodeResult:
    world_id: str
    episode_id: str
    goal_item: str
    chain_depth: int
    condition: str
    success: bool
    steps_taken: int
    optimal_steps: int
    efficiency: float
    requires_memory: bool
    locations_known_at_start: int
    locations_discovered: int
    structural_accuracy: float   # fraction of crafting chain steps attempted in order
    trajectory: list[dict] = field(default_factory=list)


def run_episode(
    sim: MinecraftSim,
    episode: dict,
    model,
    tokenizer,
    condition: str,
    known_locations: dict,
    episode_memory: list[dict],
    device: str,
    max_steps: int = 30,
) -> EpisodeResult:
    world = sim.world
    goal = episode["goal_item"]
    chain = episode["crafting_chain"]

    obs = sim.reset(goal, known_locations=known_locations if condition == "rag" else {})
    optimal = compute_optimal_steps(goal, known_locations, world)

    step_history: list[tuple[str, str, str]] = []
    trajectory = []
    crafted_items: list[str] = []
    locs_at_start = len(known_locations) if condition == "rag" else 0

    for step_i in range(max_steps):
        if condition == "zero_memory":
            prompt = build_zero_memory_prompt(obs, step_history)
        else:
            prompt = build_rag_prompt(obs, step_history, episode_memory)

        inputs = tokenizer(prompt, return_tensors="pt").to(device)
        with torch.inference_mode():
            out_ids = model.generate(
                **inputs,
                max_new_tokens=128,
                do_sample=False,
                pad_token_id=tokenizer.eos_token_id,
            )
        new_ids = out_ids[0, inputs["input_ids"].shape[1]:]
        response = tokenizer.decode(new_ids, skip_special_tokens=True).strip()

        thought, action = parse_thought_action(response)
        next_obs, done, info = sim.step(action)

        if action.startswith("craft"):
            item = action.replace("craft", "").strip().replace(" ", "_")
            if item in chain and "craft" in next_obs.lower() and "missing" not in next_obs.lower():
                crafted_items.append(item)

        trajectory.append({"step": step_i, "thought": thought, "action": action, "obs": next_obs})
        step_history.append((thought, action, next_obs))
        obs = next_obs

        if done:
            break

    success = info.get("success", False)
    steps = sim._agent.steps
    efficiency = min(1.0, optimal / steps) if steps > 0 else 0.0

    # Structural accuracy: fraction of chain items crafted in order
    structural_accuracy = 0.0
    if chain:
        correct_order = 0
        last_idx = -1
        for item in crafted_items:
            if item in chain:
                idx = chain.index(item)
                if idx > last_idx:
                    correct_order += 1
                    last_idx = idx
        structural_accuracy = correct_order / len(chain)

    locs_discovered = len(sim.get_known_locations()) - locs_at_start

    return EpisodeResult(
        world_id=world.world_id,
        episode_id=episode["episode_id"],
        goal_item=goal,
        chain_depth=episode["chain_depth"],
        condition=condition,
        success=success,
        steps_taken=steps,
        optimal_steps=optimal,
        efficiency=efficiency,
        requires_memory=episode.get("requires_memory", False),
        locations_known_at_start=locs_at_start,
        locations_discovered=locs_discovered,
        structural_accuracy=structural_accuracy,
        trajectory=trajectory,
    )


def make_episode_memory_entry(episode: dict, result: EpisodeResult, known_locs: dict) -> dict:
    """Summarize an episode for RAG context in future episodes."""
    loc_strs = [f"{name} at {coords}" for name, coords in known_locs.items()]
    return {
        "episode_id": result.episode_id,
        "goal": result.goal_item,
        "success": result.success,
        "summary": (
            f"Episode {result.episode_id}: crafted {result.goal_item} "
            f"({'success' if result.success else 'failed'}). "
            f"Known locations: {', '.join(loc_strs[:4]) if loc_strs else 'none'}."
        ),
        "known_locations": dict(known_locs),
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

@app.command()
def main(
    worlds: Path = typer.Option(..., "--worlds", "-w", exists=True),
    condition: str = typer.Option(..., "--condition", "-c", help="zero_memory | rag"),
    output: Path = typer.Option(Path("outputs/minecraft_baseline"), "--output", "-o"),
    max_worlds: Optional[int] = typer.Option(None, "--max-worlds"),
    max_episodes: Optional[int] = typer.Option(None, "--max-episodes"),
    model_name: str = typer.Option(MODEL_NAME, "--model"),
    device: str = typer.Option("cuda", "--device"),
):
    assert condition in ("zero_memory", "rag"), "condition must be zero_memory | rag"
    output.mkdir(parents=True, exist_ok=True)

    typer.echo(f"Loading worlds from {worlds}")
    with open(worlds) as f:
        all_worlds = json.load(f)
    if max_worlds:
        all_worlds = all_worlds[:max_worlds]

    typer.echo(f"Loading model {model_name}...")
    hf_token = os.environ.get("HF_TOKEN")
    tokenizer = AutoTokenizer.from_pretrained(model_name, token=hf_token)
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.bfloat16,
        device_map=device,
        token=hf_token,
    )
    model.eval()
    typer.echo("Model loaded.\n")

    all_results: list[EpisodeResult] = []

    for world_data in all_worlds:
        world = WorldState.generate(world_data["world_id"], seed=world_data["world_seed"])
        sim = MinecraftSim(world)
        episodes = world_data["episodes"]
        if max_episodes:
            episodes = episodes[:max_episodes]

        typer.echo(f"World: {world.world_id} ({world.biome}) — {len(episodes)} episodes")

        known_locations: dict = {}
        episode_memory: list[dict] = []

        for ep in episodes:
            typer.echo(f"  [{ep['episode_id']}] goal={ep['goal_item']} depth={ep['chain_depth']} mem={ep['requires_memory']}")
            result = run_episode(
                sim, ep, model, tokenizer,
                condition=condition,
                known_locations=known_locations,
                episode_memory=episode_memory,
                device=device,
            )
            all_results.append(result)

            # Update persistent state
            new_locs = sim.get_known_locations()
            known_locations.update(new_locs)
            episode_memory.append(make_episode_memory_entry(ep, result, known_locations))

            typer.echo(
                f"    success={result.success} steps={result.steps_taken} "
                f"efficiency={result.efficiency:.2f} struct={result.structural_accuracy:.2f}"
            )

    # Aggregate
    n = len(all_results)
    mem_results = [r for r in all_results if r.requires_memory]
    nomem_results = [r for r in all_results if not r.requires_memory]

    def avg(lst, key):
        vals = [getattr(r, key) for r in lst]
        return sum(vals) / len(vals) if vals else 0.0

    typer.echo(f"\n{'='*50}")
    typer.echo(f"CONDITION: {condition}  N={n}")
    typer.echo(f"Overall success rate:       {avg(all_results, 'success'):.3f}")
    typer.echo(f"Overall efficiency:         {avg(all_results, 'efficiency'):.3f}")
    typer.echo(f"Overall struct accuracy:    {avg(all_results, 'structural_accuracy'):.3f}")
    if mem_results:
        typer.echo(f"\nEpisodes REQUIRING memory (n={len(mem_results)}):")
        typer.echo(f"  success rate:    {avg(mem_results, 'success'):.3f}")
        typer.echo(f"  efficiency:      {avg(mem_results, 'efficiency'):.3f}")
    if nomem_results:
        typer.echo(f"\nEpisodes NOT requiring memory (n={len(nomem_results)}):")
        typer.echo(f"  success rate:    {avg(nomem_results, 'success'):.3f}")
        typer.echo(f"  efficiency:      {avg(nomem_results, 'efficiency'):.3f}")

    # Save
    out_file = output / f"{condition}_results.json"
    with open(out_file, "w") as f:
        json.dump({
            "condition": condition,
            "n_episodes": n,
            "overall": {
                "success_rate": avg(all_results, "success"),
                "efficiency": avg(all_results, "efficiency"),
                "structural_accuracy": avg(all_results, "structural_accuracy"),
            },
            "memory_required": {
                "n": len(mem_results),
                "success_rate": avg(mem_results, "success"),
                "efficiency": avg(mem_results, "efficiency"),
            },
            "no_memory_required": {
                "n": len(nomem_results),
                "success_rate": avg(nomem_results, "success"),
                "efficiency": avg(nomem_results, "efficiency"),
            },
            "per_episode": [asdict(r) for r in all_results],
        }, f, indent=2, default=str)

    typer.echo(f"\nResults saved to {out_file}")


if __name__ == "__main__":
    app()
