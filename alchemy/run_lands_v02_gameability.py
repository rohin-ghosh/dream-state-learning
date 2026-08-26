"""First model contact for the Semantic World v0.2 D3 diagnostic.

This runner deliberately precedes dreaming or LoRA training.  It asks whether
the clean model can solve the identifiable game when the complete public
lifetime is visible.  `direct` is minimally instructed; `scaffolded` names a
generic factor/operator search procedure without supplying the operator or
parents; `oracle-resolved` supplies exact per-goal leaves and tests only final
ratio composition.
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
import pathlib
import re

from alchemy.backend import make_backend
from lands.model import WorldConfig
from lands.skins import make_skin
from lands.v02 import SemanticWorldV02


MODEL = "Qwen/Qwen2.5-7B-Instruct"

DIRECT = """You have lived the following experiences in a world whose rules
must be learned from observations. Names may be suggestive but are not rules.

EXPERIENCE:
{lifetime}

QUESTION:
{question}

Use as much scratch reasoning as necessary. End with exactly:
FINAL: <one color-or-state token>"""

SCAFFOLDED = """You have lived the following experiences in a world whose
rules must be inferred rather than assumed from names.

EXPERIENCE:
{lifetime}

Solve the question by building a compact world model:
1. Find animals that occupy the same latent role from their repeated behavior.
2. Compare the known-source special lands to infer one reusable operation over
   source outcomes. Preserve multiplicity if the demonstrations require it.
3. For the queried target, use its observed roles to test possible source sets;
   do not assume it simply copies an ordinary land.
4. Derive the queried animal's source outcomes and apply the inferred operation.
Check the prediction against every relevant observed case before answering.

QUESTION:
{question}

Show the chain. End with exactly:
FINAL: <one color-or-state token>"""

ORACLE_RESOLVED = """Use only these resolved structural memory reads:
{memories}

The three-number recipe means amounts of red, yellow, and blue pigment. Add
every listed source recipe componentwise and reduce by their greatest common divisor.
Map the resulting primitive recipe to the declared answer vocabulary.

QUESTION:
{question}

Show the arithmetic. End with exactly:
FINAL: <one color-or-state token>"""


def score(world: SemanticWorldV02, skin: str, text: str, wanted) -> bool:
    expected = world.ratio_surface(wanted, skin).lower()
    match = re.search(r"FINAL:\s*([\w-]+)", text, flags=re.IGNORECASE)
    if match:
        return match.group(1).lower().rstrip(".,;:") == expected
    hits = [m.start() for m in re.finditer(rf"\b{re.escape(expected)}\b", text.lower())]
    return bool(hits)


def oracle_memories(world: SemanticWorldV02, skin_name: str, goal) -> str:
    skin = make_skin(skin_name, world.animal_ids, world.source_land_ids)
    parents = world.target_parents[goal.land_id]
    rows = [
        f"BLEND OPERATOR: add pigment amounts and reduce the ratio.",
        "TARGET PARENTS: " + " | ".join(skin.land(parent) for parent in parents),
    ]
    for parent in parents:
        ratio = world.source_ratio_for_role(goal.hidden_role, parent)
        rows.append(
            f"SOURCE VALUE: {skin.animal(goal.animal_id)} in {skin.land(parent)} "
            f"has recipe {ratio}."
        )
    answer_ratios = sorted({candidate.answer_ratio for candidate in world.goals})
    for ratio in answer_ratios:
        rows.append(
            f"RECIPE LABEL: primitive recipe {ratio} is called "
            f"{world.ratio_surface(ratio, skin_name)}."
        )
    rows.append(
        "ANSWER VOCABULARY: "
        + " | ".join(world.ratio_surface(ratio, skin_name) for ratio in answer_ratios)
    )
    return "\n".join(f"- {row}" for row in rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode", choices=("direct", "scaffolded", "oracle-resolved"), required=True
    )
    parser.add_argument("--skin", choices=("aligned", "neutral", "conflicting"), default="aligned")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--backend", choices=("vllm", "hf"), default="vllm")
    parser.add_argument("--model", default=MODEL)
    parser.add_argument("--output-dir", default="alchemy/v2_out")
    args = parser.parse_args()

    world = SemanticWorldV02(WorldConfig(seed=args.seed))
    rendered_goals = {row["goal_id"]: row["question"] for row in world.render_goals(args.skin)}
    lifetime = "\n".join(world.render_lifetime(args.skin))
    prompts = []
    for goal in world.goals:
        question = rendered_goals[goal.id]
        if args.mode == "direct":
            prompts.append(DIRECT.format(lifetime=lifetime, question=question))
        elif args.mode == "scaffolded":
            prompts.append(SCAFFOLDED.format(lifetime=lifetime, question=question))
        else:
            prompts.append(
                ORACLE_RESOLVED.format(
                    memories=oracle_memories(world, args.skin, goal),
                    question=question,
                )
            )

    backend = make_backend(args.backend, args.model)
    outputs = []
    for start in range(0, len(prompts), 12):
        outputs.extend(backend.generate(prompts[start : start + 12], max_tokens=2200))
    correct = [
        score(world, args.skin, output, goal.answer_ratio)
        for output, goal in zip(outputs, world.goals)
    ]
    by_target = {}
    for land_id in world.target_parents:
        indices = [index for index, goal in enumerate(world.goals) if goal.land_id == land_id]
        by_target[world.blend_land_surface(land_id, args.skin)] = round(
            sum(correct[index] for index in indices) / len(indices), 3
        )
    answers = Counter(goal.answer_ratio for goal in world.goals)
    floor = max(answers.values()) / len(world.goals)
    report = {
        "schema_version": world.schema_version,
        "mode": args.mode,
        "skin": args.skin,
        "seed": args.seed,
        "accuracy": round(sum(correct) / len(correct), 3),
        "floor": round(floor, 3),
        "n": len(correct),
        "by_target": by_target,
        "prompt_tokens": backend.n_tokens(prompts[0]) if hasattr(backend, "n_tokens") else None,
        "outputs": [
            {
                "goal_id": goal.id,
                "correct": ok,
                "wanted": world.ratio_surface(goal.answer_ratio, args.skin),
                "text": output,
            }
            for goal, ok, output in zip(world.goals, correct, outputs)
        ],
    }
    output_dir = pathlib.Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"lands_v02_{args.mode}_{args.skin}_s{args.seed}.json"
    path.write_text(json.dumps(report, indent=2) + "\n")
    print(
        f"[v02] {args.mode} {args.skin} s{args.seed}: "
        f"acc={report['accuracy']} floor={report['floor']} "
        f"targets={by_target} prompt_tokens={report['prompt_tokens']}",
        flush=True,
    )


if __name__ == "__main__":
    main()
