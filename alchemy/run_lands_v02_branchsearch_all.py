"""Run the model-only v0.2 branch thinker over all twelve targets in one load."""

from __future__ import annotations

import argparse
import json
import pathlib
import re

from alchemy.backend import make_backend
from alchemy.run_lands_v02_branchsearch import (
    BRANCH_ROLE,
    COMPOSE,
    MODEL,
    OPERATOR_DREAM,
    ORDINARY_RECIPES,
    REVISIT,
    ROLE_DREAM,
    canonical_ordinary_cells,
    canonical_role_comparison,
    canonical_workshop,
    coat_labels,
    dedupe_surface,
    operator_episode_packets,
    parse_final,
    parse_parents,
    parse_role,
    parse_target_animals,
    parse_verdict,
)
from lands.model import WorldConfig
from lands.skins import make_skin
from lands.v02 import SemanticWorldV02, source_parent_hypotheses


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skin", choices=("aligned", "neutral", "conflicting"), default="aligned")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--backend", choices=("vllm", "hf"), default="vllm")
    parser.add_argument("--model", default=MODEL)
    parser.add_argument("--output-dir", default="alchemy/v2_out")
    args = parser.parse_args()
    if args.skin != "aligned":
        raise ValueError(
            "the current canonical recipe controller is aligned-only; "
            "neutral/conflicting require a model-dreamed recipe gauge"
        )

    world = SemanticWorldV02(WorldConfig(seed=args.seed))
    skin = make_skin(args.skin, world.animal_ids, world.source_land_ids)
    lifetime = world.render_lifetime(args.skin)
    rendered_goals = world.render_goals(args.skin)
    source_lands = [skin.land(land_id) for land_id in world.source_land_ids]
    anchor_names = tuple(skin.animal(animal_id) for animal_id in world.anchor_animals)

    workshop_rows = [row for row in lifetime if row.startswith("[v02_lab_")]
    workshop = canonical_workshop(workshop_rows)
    feed_rows = [row for row in lifetime if row.startswith("[v02_feed_")]
    demo_rows = [
        row
        for row in lifetime
        if row.startswith("[v02_obs_") and "| v02_demo_" in row
    ]
    anchor_rows = dedupe_surface(
        [
            row
            for row in lifetime
            if any(f"the {animal}.".lower() in row.lower() for animal in anchor_names)
            and any(land.lower() in row.lower() for land in source_lands)
        ]
    )
    demo_labels = coat_labels(demo_rows)
    operator_workshop = canonical_workshop(
        [
            row
            for row in workshop_rows
            if any(
                re.search(rf"\b{re.escape(label)}\b", row, re.IGNORECASE)
                for label in demo_labels
            )
        ]
    )
    operator_prompt = OPERATOR_DREAM.format(
        ordinary_recipes=ORDINARY_RECIPES,
        evidence=operator_episode_packets(feed_rows, anchor_rows, demo_rows),
        workshop=operator_workshop,
    )
    backend = make_backend(args.backend, args.model)
    operator_memory = backend.generate([operator_prompt], max_tokens=2600)[0]

    states = []
    role_prompts = []
    for goal, rendered_goal in zip(world.goals, rendered_goals):
        target_land = world.blend_land_surface(goal.land_id, args.skin)
        query_animal = skin.animal(goal.animal_id)
        query_rows = dedupe_surface(
            [row for row in lifetime if f"the {query_animal}.".lower() in row.lower()]
        )
        query_lands = {
            land
            for land in source_lands
            if any(land.lower() in row.lower() for row in query_rows)
        }
        role_land_order = [land for land in source_lands if land in query_lands]
        role_anchor_rows = [
            row
            for row in anchor_rows
            if any(land.lower() in row.lower() for land in role_land_order)
        ]
        role_prompts.append(
            ROLE_DREAM.format(
                comparison=canonical_role_comparison(
                    role_anchor_rows,
                    query_rows,
                    anchor_names,
                    query_animal,
                    role_land_order,
                )
            )
        )
        target_rows = [row for row in lifetime if target_land.lower() in row.lower()]
        target_animals = parse_target_animals(target_rows)
        if len(target_animals) != 2:
            raise RuntimeError(f"expected two public target animals, got {target_animals}")
        target_labels = coat_labels(target_rows)
        target_workshop = canonical_workshop(
            [
                row
                for row in workshop_rows
                if any(
                    re.search(rf"\b{re.escape(label)}\b", row, re.IGNORECASE)
                    for label in target_labels
                )
            ]
        )
        states.append(
            {
                "goal": goal,
                "rendered_goal": rendered_goal,
                "target_rows": target_rows,
                "target_animals": target_animals,
                "target_workshop": target_workshop,
                "query_rows": query_rows,
            }
        )

    role_memories = backend.generate(role_prompts, max_tokens=1200)
    candidates = source_parent_hypotheses(source_lands)
    for state, role_memory in zip(states, role_memories):
        state["role_memory"] = role_memory
        branch_prompts = []
        for candidate in candidates:
            for animal in state["target_animals"]:
                target_row = next(
                    row
                    for row in state["target_rows"]
                    if f"the {animal}.".lower() in row.lower()
                )
                target_label = next(iter(coat_labels([target_row])))
                target_workshop = canonical_workshop(
                    [
                        row
                        for row in workshop_rows
                        if re.search(
                            rf"\b{re.escape(target_label)}\b", row, re.IGNORECASE
                        )
                    ]
                )
                source_rows = dedupe_surface(
                    [
                        row
                        for row in lifetime
                        if any(land.lower() in row.lower() for land in candidate)
                        and f"the {animal}.".lower() in row.lower()
                    ]
                )
                branch_prompts.append(
                    BRANCH_ROLE.format(
                        operator_memory=operator_memory,
                        ordinary_recipes=ORDINARY_RECIPES,
                        target_workshop=target_workshop,
                        target_row=target_row,
                        candidate=", ".join(candidate),
                        source_rows=canonical_ordinary_cells(source_rows),
                        animal=animal,
                    )
                )
        branch_outputs = backend.generate(branch_prompts, max_tokens=1000)
        records = []
        width = len(state["target_animals"])
        for candidate_index, candidate in enumerate(candidates):
            start = candidate_index * width
            atomic_outputs = branch_outputs[start : start + width]
            atomic_verdicts = [parse_verdict(output) for output in atomic_outputs]
            records.append(
                {
                    "candidate": list(candidate),
                    "verdict": (
                        "MATCH"
                        if all(verdict == "MATCH" for verdict in atomic_verdicts)
                        else "MISMATCH"
                        if all(verdict in {"MATCH", "MISMATCH"} for verdict in atomic_verdicts)
                        else "UNPARSED"
                    ),
                    "atomic_verdicts": dict(
                        zip(state["target_animals"], atomic_verdicts)
                    ),
                    "text": "\n\n".join(atomic_outputs),
                }
            )
        state["branch_prompts"] = branch_prompts
        state["branch_records"] = records

    revisit_prompts = []
    for state in states:
        matches = [
            record for record in state["branch_records"] if record["verdict"] == "MATCH"
        ]
        branch_thoughts = (
            "\n\n".join(record["text"] for record in matches)
            if matches
            else "NO BRANCH SELF-LABELED MATCH.\n\n"
            + "\n\n".join(record["text"] for record in state["branch_records"])
        )
        state["n_model_matches"] = len(matches)
        revisit_prompts.append(
            REVISIT.format(
                target_rows="\n".join(state["target_rows"]),
                operator_memory=operator_memory,
                branch_thoughts=branch_thoughts,
            )
        )
    parent_memories = backend.generate(revisit_prompts, max_tokens=2200)

    compose_prompts = []
    for state, parent_memory in zip(states, parent_memories):
        state["parent_memory"] = parent_memory
        selected_parents = parse_parents(parent_memory)
        selected_role = parse_role(state["role_memory"])
        role_to_anchor = {
            "FROG-LIKE": anchor_names[0],
            "COW-LIKE": anchor_names[1],
            "RAVEN-LIKE": anchor_names[2],
        }
        chosen_anchor = role_to_anchor.get(selected_role or "")
        read_plan_rows = [
            row
            for row in anchor_rows
            if chosen_anchor is not None
            and f"the {chosen_anchor}.".lower() in row.lower()
            and any(parent in row.lower() for parent in selected_parents)
        ]
        if not read_plan_rows:
            read_plan_rows = anchor_rows
        state["selected_parents"] = selected_parents
        state["selected_role"] = selected_role
        state["read_plan"] = canonical_ordinary_cells(read_plan_rows)
        compose_prompts.append(
            COMPOSE.format(
                operator_memory=operator_memory,
                ordinary_recipes=ORDINARY_RECIPES,
                role_memory=state["role_memory"],
                parent_memory=parent_memory,
                read_plan=state["read_plan"],
                workshop=workshop,
                question=state["rendered_goal"]["question"],
            )
        )
    answers = backend.generate(compose_prompts, max_tokens=1800)

    results = []
    for state, answer in zip(states, answers):
        goal = state["goal"]
        expected_parents = {
            skin.land(parent).lower() for parent in world.target_parents[goal.land_id]
        }
        true_index = next(
            index
            for index, candidate in enumerate(candidates)
            if {land.lower() for land in candidate} == expected_parents
        )
        records = state["branch_records"]
        wanted = world.ratio_surface(goal.answer_ratio, args.skin).lower()
        got = parse_final(answer)
        result = {
            "goal_id": goal.id,
            "question": state["rendered_goal"]["question"],
            "n_model_matches": state["n_model_matches"],
            "true_branch_model_verdict": records[true_index]["verdict"],
            "false_match_count": sum(
                record["verdict"] == "MATCH" and index != true_index
                for index, record in enumerate(records)
            ),
            "parent_exact": state["selected_parents"] == expected_parents,
            "selected_role": state["selected_role"],
            "wanted": wanted,
            "got": got,
            "correct": got == wanted,
            "role_memory": state["role_memory"],
            "branch_records": records,
            "parent_memory": state["parent_memory"],
            "read_plan": state["read_plan"],
            "answer": answer,
            "prompts": {
                "role": role_prompts[len(results)],
                "branches": state["branch_prompts"],
                "revisit": revisit_prompts[len(results)],
                "compose": compose_prompts[len(results)],
            },
        }
        results.append(result)

    report = {
        "schema_version": world.schema_version,
        "condition": "model-only-branch-and-revisit-all",
        "truth_used_in_prompt": False,
        "model": args.model,
        "skin": args.skin,
        "seed": args.seed,
        "n": len(results),
        "accuracy": round(sum(row["correct"] for row in results) / len(results), 3),
        "parent_accuracy": round(
            sum(row["parent_exact"] for row in results) / len(results), 3
        ),
        "true_branch_recall": round(
            sum(row["true_branch_model_verdict"] == "MATCH" for row in results)
            / len(results),
            3,
        ),
        "total_false_matches": sum(row["false_match_count"] for row in results),
        "floor": round(1 / len(results), 3),
        "operator_memory": operator_memory,
        "operator_prompt": operator_prompt,
        "results": results,
    }
    output_dir = pathlib.Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    model_slug = re.sub(r"[^a-z0-9]+", "-", args.model.lower()).strip("-")
    path = output_dir / f"lands_v02_branch_all_{args.skin}_s{args.seed}_{model_slug}.json"
    path.write_text(json.dumps(report, indent=2) + "\n")
    print(
        f"[v02 branch all] {args.skin} s{args.seed}: acc={report['accuracy']} "
        f"parents={report['parent_accuracy']} true_branch={report['true_branch_recall']} "
        f"false_matches={report['total_false_matches']} floor={report['floor']}",
        flush=True,
    )


if __name__ == "__main__":
    main()
