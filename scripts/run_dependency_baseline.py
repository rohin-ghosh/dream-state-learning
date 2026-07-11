"""
Baseline evaluation on dependency-graph tasks.

Runs two conditions:
  - zero_memory: model sees only the current task (no prior episodes)
  - rag:         model sees current task + all prior episodes in context

Measures:
  - task_success:          did the model produce a valid action sequence?
  - structural_retention:  did the model respect all dependency edges?
  - detail_noise_rate:     did the model mention noise details (color etc)?

Usage:
    python scripts/run_dependency_baseline.py \
        --tasks data/dependency_tasks/tasks.json \
        --condition zero_memory \
        --output outputs/dependency_baseline/

    python scripts/run_dependency_baseline.py \
        --tasks data/dependency_tasks/tasks.json \
        --condition rag \
        --output outputs/dependency_baseline/
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional

import torch
import typer
from transformers import AutoModelForCausalLM, AutoTokenizer

app = typer.Typer(pretty_exceptions_enable=False)

MODEL_NAME = "Qwen/Qwen2.5-7B-Instruct"


# ---------------------------------------------------------------------------
# Prompt builders
# ---------------------------------------------------------------------------

def build_zero_memory_prompt(task: dict) -> str:
    return f"""You are a physical agent in a room. You must complete a task by taking actions in the correct order.

Scene: {task["scene_description"]}

Task: {task["goal"]}

Think through what dependencies exist between objects, then output the exact sequence of actions you will take.
Format your response as:
REASONING: <your reasoning about object dependencies>
ACTIONS:
- <action 1>
- <action 2>
...
"""


def build_rag_prompt(task: dict, episode_history: list[dict]) -> str:
    history_text = ""
    if episode_history:
        history_text = "PAST EPISODES (for reference):\n"
        for i, ep in enumerate(episode_history[-5:]):  # last 5 episodes
            history_text += f"\nEpisode {i+1}:\n"
            history_text += f"  Scene: {ep['scene_description'][:200]}...\n"
            history_text += f"  Goal: {ep['goal']}\n"
            history_text += f"  Actions taken: {', '.join(ep.get('actions_taken', []))}\n"
            history_text += f"  Success: {ep.get('success', False)}\n"

    return f"""You are a physical agent in a room. You must complete a task by taking actions in the correct order.

{history_text}

CURRENT TASK:
Scene: {task["scene_description"]}
Task: {task["goal"]}

Think through what dependencies exist between objects based on your past experience, then output the exact sequence of actions.
Format your response as:
REASONING: <your reasoning about object dependencies>
ACTIONS:
- <action 1>
- <action 2>
...
"""


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------

@dataclass
class TaskResult:
    task_id: str
    dep_type: str
    complexity: int
    condition: str
    raw_response: str
    actions_predicted: list[str]
    dependencies_respected: list[bool]
    structural_retention: float   # fraction of dependency edges respected
    detail_noise_mentioned: bool  # did model mention irrelevant details
    task_success: bool
    latency_s: float


def parse_actions(response: str) -> list[str]:
    actions = []
    in_actions = False
    for line in response.split("\n"):
        line = line.strip()
        if line.upper().startswith("ACTIONS:"):
            in_actions = True
            continue
        if in_actions and line.startswith("-"):
            actions.append(line.lstrip("- ").strip())
        elif in_actions and line and not line.startswith("-"):
            break
    return actions


def check_dependency_respected(dep: dict, actions: list[str]) -> bool:
    """Check if the action sequence respects a dependency edge."""
    source = dep["source"].lower()
    target = dep["target"].lower()
    dep_type = dep["dep_type"]

    actions_lower = [a.lower() for a in actions]

    if dep_type == "blocking":
        # source must be picked up/moved before target
        source_idx = next((i for i, a in enumerate(actions_lower) if source in a and ("pick" in a or "move" in a or "place" in a)), None)
        target_idx = next((i for i, a in enumerate(actions_lower) if target in a and ("pick" in a or "move" in a)), None)
        if source_idx is None or target_idx is None:
            return False
        return source_idx < target_idx

    elif dep_type == "paired":
        # both source and target must appear in actions
        source_present = any(source in a for a in actions_lower)
        target_present = any(target in a for a in actions_lower)
        return source_present and target_present

    elif dep_type == "sequential":
        # source must be opened before target is accessed
        source_idx = next((i for i, a in enumerate(actions_lower) if source in a and "open" in a), None)
        target_idx = next((i for i, a in enumerate(actions_lower) if target in a), None)
        if source_idx is None or target_idx is None:
            return False
        return source_idx < target_idx

    elif dep_type == "location_memory":
        # original location must appear in actions
        return source in " ".join(actions_lower)

    return False


def check_noise_mentioned(task: dict, response: str) -> bool:
    response_lower = response.lower()
    for detail in task.get("noise_details", []):
        # check if any noise keyword appears in reasoning section
        reasoning = response_lower.split("actions:")[0] if "actions:" in response_lower else response_lower
        if any(word in reasoning for word in detail.lower().split() if len(word) > 3):
            return True
    return False


def evaluate_task(
    task: dict,
    model,
    tokenizer,
    condition: str,
    episode_history: list[dict],
    device: str = "cuda",
) -> TaskResult:
    if condition == "zero_memory":
        prompt = build_zero_memory_prompt(task)
    else:
        prompt = build_rag_prompt(task, episode_history)

    inputs = tokenizer(prompt, return_tensors="pt").to(device)
    t0 = time.time()
    with torch.inference_mode():
        output_ids = model.generate(
            **inputs,
            max_new_tokens=512,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id,
        )
    latency = time.time() - t0

    new_ids = output_ids[0, inputs["input_ids"].shape[1]:]
    response = tokenizer.decode(new_ids, skip_special_tokens=True).strip()

    actions = parse_actions(response)
    deps = task.get("dependencies", [])
    dep_results = [check_dependency_respected(d, actions) for d in deps]
    structural_retention = sum(dep_results) / len(dep_results) if dep_results else 1.0
    noise_mentioned = check_noise_mentioned(task, response)
    success = structural_retention == 1.0 and len(actions) > 0

    return TaskResult(
        task_id=task["task_id"],
        dep_type=task["metadata"].get("type", "unknown"),
        complexity=task["complexity"],
        condition=condition,
        raw_response=response,
        actions_predicted=actions,
        dependencies_respected=dep_results,
        structural_retention=structural_retention,
        detail_noise_mentioned=noise_mentioned,
        task_success=success,
        latency_s=round(latency, 2),
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

@app.command()
def main(
    tasks: Path = typer.Option(..., "--tasks", "-t", exists=True),
    condition: str = typer.Option(..., "--condition", "-c", help="zero_memory | rag"),
    output: Path = typer.Option(Path("outputs/dependency_baseline"), "--output", "-o"),
    max_tasks: Optional[int] = typer.Option(None, "--max-tasks", "-n"),
    model_name: str = typer.Option(MODEL_NAME, "--model"),
):
    assert condition in ("zero_memory", "rag"), "condition must be zero_memory or rag"

    output.mkdir(parents=True, exist_ok=True)

    typer.echo(f"Loading tasks from {tasks}")
    with open(tasks) as f:
        all_tasks = json.load(f)

    if max_tasks:
        all_tasks = all_tasks[:max_tasks]

    typer.echo(f"Loading model {model_name}...")
    hf_token = os.environ.get("HF_TOKEN")
    tokenizer = AutoTokenizer.from_pretrained(model_name, token=hf_token)
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.bfloat16,
        device_map="cuda",
        token=hf_token,
    )
    model.eval()
    typer.echo("Model loaded.")

    results = []
    episode_history = []

    for i, task in enumerate(all_tasks):
        typer.echo(f"[{i+1}/{len(all_tasks)}] {task['task_id']} (complexity={task['complexity']})")
        result = evaluate_task(task, model, tokenizer, condition, episode_history)
        results.append(result)

        # Update episode history for RAG
        episode_history.append({
            "scene_description": task["scene_description"],
            "goal": task["goal"],
            "actions_taken": result.actions_predicted,
            "success": result.task_success,
        })

        typer.echo(f"  structural_retention={result.structural_retention:.2f}  success={result.task_success}  latency={result.latency_s}s")

    # Aggregate metrics
    by_type: dict[str, list] = {}
    by_complexity: dict[int, list] = {}
    for r in results:
        by_type.setdefault(r.dep_type, []).append(r)
        by_complexity.setdefault(r.complexity, []).append(r)

    typer.echo("\n=== RESULTS ===")
    typer.echo(f"Condition: {condition}  N={len(results)}")
    typer.echo(f"Overall structural retention: {sum(r.structural_retention for r in results)/len(results):.3f}")
    typer.echo(f"Overall task success:         {sum(r.task_success for r in results)/len(results):.3f}")
    typer.echo(f"Noise detail mention rate:    {sum(r.detail_noise_mentioned for r in results)/len(results):.3f}")

    typer.echo("\nBy type:")
    for dep_type, rs in sorted(by_type.items()):
        sr = sum(r.structural_retention for r in rs) / len(rs)
        succ = sum(r.task_success for r in rs) / len(rs)
        typer.echo(f"  {dep_type}: retention={sr:.3f}  success={succ:.3f}  n={len(rs)}")

    typer.echo("\nBy complexity:")
    for complexity, rs in sorted(by_complexity.items()):
        sr = sum(r.structural_retention for r in rs) / len(rs)
        succ = sum(r.task_success for r in rs) / len(rs)
        typer.echo(f"  complexity={complexity}: retention={sr:.3f}  success={succ:.3f}  n={len(rs)}")

    # Save
    out_file = output / f"{condition}_results.json"
    with open(out_file, "w") as f:
        json.dump({
            "condition": condition,
            "n_tasks": len(results),
            "overall": {
                "structural_retention": sum(r.structural_retention for r in results) / len(results),
                "task_success": sum(r.task_success for r in results) / len(results),
                "noise_mention_rate": sum(r.detail_noise_mentioned for r in results) / len(results),
            },
            "by_type": {
                dep_type: {
                    "structural_retention": sum(r.structural_retention for r in rs) / len(rs),
                    "task_success": sum(r.task_success for r in rs) / len(rs),
                    "n": len(rs),
                }
                for dep_type, rs in by_type.items()
            },
            "by_complexity": {
                str(c): {
                    "structural_retention": sum(r.structural_retention for r in rs) / len(rs),
                    "task_success": sum(r.task_success for r in rs) / len(rs),
                    "n": len(rs),
                }
                for c, rs in by_complexity.items()
            },
            "per_task": [asdict(r) for r in results],
        }, f, indent=2)

    typer.echo(f"\nResults saved to {out_file}")


if __name__ == "__main__":
    app()
