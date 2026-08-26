"""Verifier-free arithmetic revision over committed v0.2 finish memories."""

from __future__ import annotations

import argparse
import json
import pathlib
import re

from alchemy.backend import make_backend
from alchemy.run_lands_v02_finish import parse_recipe, public_workshop_map
from lands.model import WorldConfig
from lands.v02 import SemanticWorldV02


RECHECK = """Recheck one composition you previously attempted. This is not an
external verdict; recompute from the committed public leaves. First count the
number of CELL lines. Then make three explicit lists containing the red value
from every line, the yellow value from every line, and the blue value from every
line. Sum each list. Reduce only if all three totals share an integer divisor.
Do not reuse the previous answer without doing those checks.

COMMITTED ROLE: {role}

COMMITTED PARENT MEMORY:
{parent_memory}

COMMITTED PUBLIC READ PLAN:
{read_plan}

PREVIOUS COMPOSITION THOUGHT (fallible):
{previous}

End with exactly:
FINAL_RECIPE: (<red>, <yellow>, <blue>)
"""


def parse_component_ledger(text: str) -> tuple[int, int, int] | None:
    """Read the explicit component totals before any later serialization drift."""
    match = re.search(
        r"The sums are\s*(\d+)\s*,\s*(\d+)\s*,(?:\s*and)?\s*(\d+)",
        text,
        re.IGNORECASE,
    )
    return tuple(map(int, match.groups())) if match else None  # type: ignore[return-value]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-artifact", required=True)
    parser.add_argument("--model", default="Qwen/Qwen2.5-32B-Instruct")
    parser.add_argument("--backend", choices=("vllm", "hf"), default="vllm")
    parser.add_argument("--output-dir", default="alchemy/v2_out")
    args = parser.parse_args()

    prior = json.loads(pathlib.Path(args.input_artifact).read_text())
    world = SemanticWorldV02(WorldConfig(seed=prior["seed"]))
    workshop_rows = [
        row
        for row in world.render_lifetime(prior["skin"])
        if row.startswith("[v02_lab_")
    ]
    workshop_map = public_workshop_map(workshop_rows)
    prompts = [
        RECHECK.format(
            role=row["selected_role"],
            parent_memory=row["parent_memory"],
            read_plan=row["read_plan"],
            previous=row["compose_output"],
        )
        for row in prior["results"]
    ]
    backend = make_backend(args.backend, args.model)
    outputs = backend.generate(prompts, max_tokens=1200)

    results = []
    for goal, prior_row, output in zip(world.goals, prior["results"], outputs):
        ledger_recipe = parse_component_ledger(output)
        emitted_recipe = parse_recipe(output)
        recipe = ledger_recipe or emitted_recipe
        got = workshop_map.get(recipe) if recipe else None
        wanted = world.ratio_surface(goal.answer_ratio, prior["skin"]).lower()
        results.append(
            {
                "goal_id": goal.id,
                "recipe": recipe,
                "ledger_recipe": ledger_recipe,
                "emitted_recipe": emitted_recipe,
                "wanted": wanted,
                "got": got,
                "correct": got == wanted,
                "prior_recipe": prior_row["recipe"],
                "read_plan": prior_row["read_plan"],
                "output": output,
            }
        )
    report = {
        "schema_version": world.schema_version,
        "condition": "verifier-free-componentwise-revision",
        "truth_used_in_prompt": False,
        "input_artifact": args.input_artifact,
        "model": args.model,
        "skin": prior["skin"],
        "seed": prior["seed"],
        "n": len(results),
        "accuracy": round(sum(row["correct"] for row in results) / len(results), 3),
        "floor": round(1 / len(results), 3),
        "results": results,
        "prompts": prompts,
    }
    output_dir = pathlib.Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    model_slug = re.sub(r"[^a-z0-9]+", "-", args.model.lower()).strip("-")
    path = output_dir / (
        f"lands_v02_recipe_recheck_{prior['skin']}_s{prior['seed']}_{model_slug}.json"
    )
    path.write_text(json.dumps(report, indent=2) + "\n")
    print(
        f"[v02 recipe recheck] {prior['skin']} s{prior['seed']}: "
        f"acc={report['accuracy']} floor={report['floor']}",
        flush=True,
    )


if __name__ == "__main__":
    main()
