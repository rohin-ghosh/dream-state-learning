"""Finish a committed v0.2 parent-memory run with atomic reads.

This continuation never reopens the offline branch labels in its input artifact.
It consumes only the dreamed operator and per-goal parent-memory text.  Roles
are recognized by model calls over public same-land vectors; the model composes
an exact recipe; a lossless lookup in the public workshop converts that recipe
to its surface token.  Hidden state is consulted only after all outputs commit.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re

from alchemy.backend import make_backend
from alchemy.run_lands_v02_branchsearch import (
    ORDINARY_RECIPES,
    canonical_ordinary_cells,
    canonical_role_comparison,
    coat_labels,
    dedupe_surface,
    parse_parents,
    parse_verdict,
)
from lands.model import WorldConfig
from lands.skins import make_skin
from lands.v02 import SemanticWorldV02


ROLE_ATOMIC = """Evaluate one candidate role using exact position-wise
recognition. The vectors use the same land order. Every position must match;
one matching position is insufficient.

PUBLIC COMPARISON MATRIX:
{comparison}

CANDIDATE: {candidate}

End with exactly:
CANDIDATE: {candidate}
VERDICT: MATCH | MISMATCH
"""

ROLE_REVISIT = """Revisit three model-generated role checks against the public
comparison matrix. Choose the one candidate whose vector exactly equals QUERY
at every position. Do not use animal-name similarity.

PUBLIC COMPARISON MATRIX:
{comparison}

ATOMIC CHECKS:
{checks}

End with exactly one:
ROLE: FROG-LIKE
ROLE: COW-LIKE
ROLE: RAVEN-LIKE
ROLE: AMBIGUOUS
"""

COMPOSE_RECIPE = """Compose one withheld outcome from self-generated memories
and losslessly retrieved public leaves. Use every listed parent leaf exactly
once. Add componentwise under SUM and divide only by an integer greatest common
divisor. Do not choose or guess a color word; return only the primitive recipe.

DREAMED OPERATOR MEMORY:
{operator_memory}

{ordinary_recipes}

QUERY ROLE MEMORY:
ROLE: {role}

DREAMED PARENT MEMORY:
{parent_memory}

PUBLIC ROLE-ROW LEAVES FOR THOSE PARENTS:
{read_plan}

QUESTION:
{question}

Show the arithmetic, then end with exactly:
FINAL_RECIPE: (<red>, <yellow>, <blue>)
"""


def parse_role_revisit(text: str) -> str | None:
    matches = re.findall(
        r"ROLE:\s*(FROG-LIKE|COW-LIKE|RAVEN-LIKE|AMBIGUOUS)",
        text,
        re.IGNORECASE,
    )
    if not matches or matches[-1].upper() == "AMBIGUOUS":
        return None
    return matches[-1].upper()


def parse_recipe(text: str) -> tuple[int, int, int] | None:
    matches = re.findall(
        r"FINAL_RECIPE:\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)",
        text,
        re.IGNORECASE,
    )
    return tuple(map(int, matches[-1])) if matches else None  # type: ignore[return-value]


def public_workshop_map(rows: list[str]) -> dict[tuple[int, int, int], str]:
    mapping = {}
    for row in rows:
        label_match = re.search(r"labeled ([\w-]+)", row, re.IGNORECASE)
        if not label_match:
            continue
        amounts = []
        for pigment in ("red", "yellow", "blue"):
            amount_match = re.search(
                rf"(\d+) parts? {pigment}", row, re.IGNORECASE
            )
            amounts.append(int(amount_match.group(1)) if amount_match else 0)
        mapping[tuple(amounts)] = label_match.group(1).lower()
    return mapping


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-artifact", required=True)
    parser.add_argument("--model", default="Qwen/Qwen2.5-32B-Instruct")
    parser.add_argument("--backend", choices=("vllm", "hf"), default="vllm")
    parser.add_argument("--output-dir", default="alchemy/v2_out")
    args = parser.parse_args()

    prior = json.loads(pathlib.Path(args.input_artifact).read_text())
    skin_name = prior["skin"]
    seed = prior["seed"]
    world = SemanticWorldV02(WorldConfig(seed=seed))
    skin = make_skin(skin_name, world.animal_ids, world.source_land_ids)
    lifetime = world.render_lifetime(skin_name)
    rendered_goals = world.render_goals(skin_name)
    source_lands = [skin.land(land_id) for land_id in world.source_land_ids]
    anchor_names = tuple(skin.animal(animal_id) for animal_id in world.anchor_animals)
    anchor_rows = dedupe_surface(
        [
            row
            for row in lifetime
            if any(f"the {animal}.".lower() in row.lower() for animal in anchor_names)
            and any(land.lower() in row.lower() for land in source_lands)
        ]
    )
    workshop_rows = [row for row in lifetime if row.startswith("[v02_lab_")]
    workshop_map = public_workshop_map(workshop_rows)
    prior_by_goal = {row["goal_id"]: row for row in prior["results"]}
    backend = make_backend(args.backend, args.model)

    states = []
    atomic_prompts = []
    role_candidates = ("FROG-LIKE", "COW-LIKE", "RAVEN-LIKE")
    for goal, rendered_goal in zip(world.goals, rendered_goals):
        query_animal = skin.animal(goal.animal_id)
        query_rows = dedupe_surface(
            [row for row in lifetime if f"the {query_animal}.".lower() in row.lower()]
        )
        query_lands = [
            land
            for land in source_lands
            if any(land.lower() in row.lower() for row in query_rows)
        ]
        role_anchor_rows = [
            row
            for row in anchor_rows
            if any(land.lower() in row.lower() for land in query_lands)
        ]
        comparison = canonical_role_comparison(
            role_anchor_rows, query_rows, anchor_names, query_animal, query_lands
        )
        for candidate in role_candidates:
            atomic_prompts.append(
                ROLE_ATOMIC.format(comparison=comparison, candidate=candidate)
            )
        states.append(
            {
                "goal": goal,
                "rendered_goal": rendered_goal,
                "comparison": comparison,
                "parent_memory": prior_by_goal[goal.id]["parent_memory"],
            }
        )

    atomic_outputs = backend.generate(atomic_prompts, max_tokens=700)
    revisit_prompts = []
    for index, state in enumerate(states):
        outputs = atomic_outputs[index * 3 : index * 3 + 3]
        verdicts = [parse_verdict(output) for output in outputs]
        matching = [
            candidate
            for candidate, verdict in zip(role_candidates, verdicts)
            if verdict == "MATCH"
        ]
        state["atomic_role_outputs"] = outputs
        state["atomic_role_verdicts"] = dict(zip(role_candidates, verdicts))
        state["recognized_role"] = matching[0] if len(matching) == 1 else None
        revisit_prompts.append(
            ROLE_REVISIT.format(
                comparison=state["comparison"], checks="\n\n".join(outputs)
            )
        )
    revisit_outputs = backend.generate(revisit_prompts, max_tokens=900)

    compose_prompts = []
    role_to_anchor = {
        "FROG-LIKE": anchor_names[0],
        "COW-LIKE": anchor_names[1],
        "RAVEN-LIKE": anchor_names[2],
    }
    for state, revisit in zip(states, revisit_outputs):
        role = state["recognized_role"] or parse_role_revisit(revisit)
        parents = parse_parents(state["parent_memory"])
        chosen_anchor = role_to_anchor.get(role or "")
        read_plan_rows = [
            row
            for row in anchor_rows
            if chosen_anchor is not None
            and f"the {chosen_anchor}.".lower() in row.lower()
            and any(parent in row.lower() for parent in parents)
        ]
        state["role_revisit"] = revisit
        state["selected_role"] = role
        state["selected_parents"] = parents
        state["read_plan"] = canonical_ordinary_cells(read_plan_rows)
        compose_prompts.append(
            COMPOSE_RECIPE.format(
                operator_memory=prior["operator_memory"],
                ordinary_recipes=ORDINARY_RECIPES,
                role=role or "AMBIGUOUS",
                parent_memory=state["parent_memory"],
                read_plan=state["read_plan"],
                question=state["rendered_goal"]["question"],
            )
        )
    compose_outputs = backend.generate(compose_prompts, max_tokens=1200)

    results = []
    for state, compose_output in zip(states, compose_outputs):
        goal = state["goal"]
        recipe = parse_recipe(compose_output)
        got = workshop_map.get(recipe) if recipe else None
        wanted = world.ratio_surface(goal.answer_ratio, skin_name).lower()
        expected_role = (
            "FROG-LIKE",
            "COW-LIKE",
            "RAVEN-LIKE",
        )[world.base.animal_roles[goal.animal_id]]
        expected_parents = {
            skin.land(parent).lower() for parent in world.target_parents[goal.land_id]
        }
        results.append(
            {
                "goal_id": goal.id,
                "selected_role": state["selected_role"],
                "role_correct": state["selected_role"] == expected_role,
                "parent_exact": state["selected_parents"] == expected_parents,
                "recipe": recipe,
                "wanted": wanted,
                "got": got,
                "correct": got == wanted,
                "parent_memory": state["parent_memory"],
                "comparison": state["comparison"],
                "atomic_role_verdicts": state["atomic_role_verdicts"],
                "atomic_role_outputs": state["atomic_role_outputs"],
                "role_revisit": state["role_revisit"],
                "read_plan": state["read_plan"],
                "compose_output": compose_output,
            }
        )

    report = {
        "schema_version": world.schema_version,
        "condition": "committed-parent-memory+atomic-role+recipe-lookup",
        "truth_used_in_prompt": False,
        "input_artifact": args.input_artifact,
        "model": args.model,
        "skin": skin_name,
        "seed": seed,
        "n": len(results),
        "accuracy": round(sum(row["correct"] for row in results) / len(results), 3),
        "role_accuracy": round(
            sum(row["role_correct"] for row in results) / len(results), 3
        ),
        "parent_accuracy": round(
            sum(row["parent_exact"] for row in results) / len(results), 3
        ),
        "floor": round(1 / len(results), 3),
        "results": results,
        "prompts": {
            "atomic_roles": atomic_prompts,
            "role_revisits": revisit_prompts,
            "compose": compose_prompts,
        },
    }
    output_dir = pathlib.Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    model_slug = re.sub(r"[^a-z0-9]+", "-", args.model.lower()).strip("-")
    path = output_dir / f"lands_v02_finish_{skin_name}_s{seed}_{model_slug}.json"
    path.write_text(json.dumps(report, indent=2) + "\n")
    print(
        f"[v02 finish] {skin_name} s{seed}: acc={report['accuracy']} "
        f"roles={report['role_accuracy']} parents={report['parent_accuracy']} "
        f"floor={report['floor']}",
        flush=True,
    )


if __name__ == "__main__":
    main()
