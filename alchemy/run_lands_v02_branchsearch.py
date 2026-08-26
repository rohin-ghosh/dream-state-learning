"""Model-only branch-and-revisit thinker for Semantic World v0.2.

The harness expands the public source-subset search tree, but it never computes
which branch is correct.  A frozen LLM evaluates each branch from raw public
evidence, then another LLM call revisits the accumulated branch thoughts and
compresses them into a parent memory.  Hidden world state is used only after
generation commits, for diagnostics.

This is deliberately an over-scaffolded thinker ceiling.  If it works, later
ablations can amortize or remove the explicit branching while retaining the
same inspectable state transitions.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re

from alchemy.backend import make_backend
from lands.model import WorldConfig
from lands.skins import make_skin
from lands.v02 import SemanticWorldV02, source_parent_hypotheses


MODEL = "Qwen/Qwen2.5-7B-Instruct"
ORDINARY_RATIO = {
    "red": (1, 0, 0),
    "yellow": (0, 1, 0),
    "blue": (0, 0, 1),
    "orange": (1, 1, 0),
    "green": (0, 1, 1),
    "purple": (1, 0, 1),
}
ORDINARY_RECIPES = (
    "Use these conventional pigment recipes: red=(1,0,0), yellow=(0,1,0), "
    "blue=(0,0,1), orange=(1,1,0), green=(0,1,1), purple=(1,0,1)."
)

OPERATOR_DREAM = """Dream a reusable numerical rule from these public
demonstrations. A feed record names the source lands. For each animal
SEPARATELY, compare its outcome in every source with its demonstrated outcome.
Do not combine different animals with each other.

{ordinary_recipes}

PUBLIC SOURCE AND DEMONSTRATION MEMORIES:
{evidence}

PUBLIC WORKSHOP DICTIONARY:
{workshop}

Workshop definitions override colloquial color mixing: for example, if the
workshop says red-orange=(2,1,0), do not rewrite it as (1,1,0).

Test these finite candidates on all three animals in BOTH demonstrations:
- SUM: add the same animal's source recipe vectors componentwise, then reduce
  only by the greatest common divisor.
- UNION: replace every positive component by 1.
- COPY: copy one source outcome unchanged.
- OTHER: none of the above.

End by choosing exactly one token:
OPERATOR: SUM
or OPERATOR: UNION
or OPERATOR: COPY
or OPERATOR: OTHER
"""

ROLE_DREAM = """Infer which anchor signature the queried animal shares. The
matrix is already aligned by land; compare the QUERY vector with each complete
candidate vector position by position.

SAME-LAND COMPARISON MATRIX:
{comparison}

Check every query observation against frog, cow, and raven at the SAME land.
Choose exactly one row; do not copy the option list. End with one of:
ROLE: FROG-LIKE
ROLE: COW-LIKE
ROLE: RAVEN-LIKE
"""

BRANCH_ROLE = """Evaluate ONE candidate branch for ONE observed target animal.
This is an atomic proof leaf. Do not reason about any other animal and do not
drop a listed source.

DREAMED OPERATOR MEMORY:
{operator_memory}

{ordinary_recipes}

EXACT PUBLIC TARGET LABEL MEMORY:
{target_workshop}

PUBLIC TARGET OBSERVATION:
{target_row}

CANDIDATE SOURCE SET: {candidate}

PUBLIC SOURCE MEMORIES FOR THIS SAME ANIMAL ONLY:
{source_rows}

Copy every listed recipe once, add all components using the dreamed operator,
reduce only by a greatest common divisor, and compare with the exact target
label recipe. End with exactly:
BRANCH: {candidate}
ANIMAL: {animal}
VERDICT: MATCH | MISMATCH
"""

BRANCH = """Evaluate ONE candidate branch in an internal source-set search.
Do not compare it with other candidates. Use the same candidate source set for
both target animals, but use each animal's own source-land colors separately.

DREAMED OPERATOR MEMORY:
{operator_memory}

{ordinary_recipes}

PUBLIC WORKSHOP DICTIONARY:
{workshop}

PUBLIC TARGET OBSERVATIONS:
{target_rows}

CANDIDATE SOURCE SET: {candidate}

PUBLIC SOURCE MEMORIES FOR THE TARGET ANIMALS:
{source_rows}

For each target animal: translate every source color into a recipe, add them
with the dreamed operation, reduce only by a common divisor, and compare to the
EXACT workshop recipe of its target color. A proposed (1,1,1) does not match
(1,3,1). Both animals must match. End with exactly:
BRANCH: {candidate}
VERDICT: MATCH | MISMATCH
"""

REVISIT = """Revisit the accumulated thoughts from an internal branch search.
No external checker has filtered them. Select a parent set only when its branch
shows exact arithmetic for BOTH public target observations. Distrust a verdict
whose written arithmetic contradicts the workshop dictionary.

PUBLIC TARGET OBSERVATIONS:
{target_rows}

DREAMED OPERATOR MEMORY:
{operator_memory}

BRANCH THOUGHTS:
{branch_thoughts}

If one branch survives, compress it into memory. If none or several survive,
say AMBIGUOUS rather than inventing certainty. End with exactly one line in
one of these two forms (do not append a verdict):
PARENTS: <comma-separated source lands>
PARENTS: AMBIGUOUS
"""

COMPOSE = """Use these self-generated memories to answer one withheld target
outcome. Recompute the answer from the selected parents and the complete anchor
row corresponding to the query animal's role. A land has a different color for
each role. Use an exact workshop label, never a nearest color.

DREAMED OPERATOR MEMORY:
{operator_memory}

{ordinary_recipes}

QUERY ROLE MEMORY:
{role_memory}

PARENT MEMORY:
{parent_memory}

RETRIEVED PUBLIC ROLE-ROW LEAVES FOR THE SELECTED PARENTS:
{read_plan}

PUBLIC WORKSHOP DICTIONARY:
{workshop}

QUESTION:
{question}

Show the role-row arithmetic. End with exactly:
FINAL: <one color-or-state token>
"""


def dedupe_surface(rows: list[str]) -> list[str]:
    seen: set[str] = set()
    result = []
    for row in rows:
        surface = re.sub(r"^\[[^]]+\]\s*", "", row)
        if surface not in seen:
            seen.add(surface)
            result.append(row)
    return result


def parse_target_animals(rows: list[str]) -> list[str]:
    animals = []
    for row in rows:
        match = re.search(r"you see the ([^.]+)\. Its coat", row, re.IGNORECASE)
        if match and match.group(1).lower() not in {animal.lower() for animal in animals}:
            animals.append(match.group(1))
    return animals


def operator_episode_packets(feed_rows: list[str], anchor_rows: list[str], demo_rows: list[str]) -> str:
    """Group public feed/source/outcome memories without inferring an operator."""
    packets = []
    for feed in feed_rows:
        match = re.search(
            r"streams from ([^.]*) and ([^.]*) jointly feed ([^.]+)\.",
            feed,
            re.IGNORECASE,
        )
        if not match:
            continue
        left, right, target = (value.strip() for value in match.groups())
        sources = [
            row
            for row in anchor_rows
            if left.lower() in row.lower() or right.lower() in row.lower()
        ]
        outcomes = [row for row in demo_rows if target.lower() in row.lower()]
        packets.append(
            f"DEMONSTRATION {target}\nFEED: {feed}\nSOURCE OUTCOMES:\n"
            + "\n".join(sources)
            + "\nDEMONSTRATED OUTCOMES:\n"
            + "\n".join(outcomes)
        )
    return "\n\n".join(packets)


def coat_labels(rows: list[str]) -> set[str]:
    labels = set()
    for row in rows:
        match = re.search(r"Its coat is ([\w-]+)", row, re.IGNORECASE)
        if match:
            labels.add(match.group(1).lower())
    return labels


def canonical_workshop(rows: list[str]) -> str:
    """Losslessly normalize public workshop prose into recognition-friendly reads."""
    memories = []
    for row in rows:
        label_match = re.search(r"labeled ([\w-]+)", row, re.IGNORECASE)
        id_match = re.match(r"\[([^]|]+)", row)
        if not label_match:
            continue
        amounts = []
        for pigment in ("red", "yellow", "blue"):
            amount_match = re.search(
                rf"(\d+) parts? {pigment}", row, re.IGNORECASE
            )
            amounts.append(int(amount_match.group(1)) if amount_match else 0)
        provenance = f" [{id_match.group(1).strip()}]" if id_match else ""
        memories.append(
            f"{label_match.group(1)}=({amounts[0]},{amounts[1]},{amounts[2]})"
            f"{provenance}"
        )
    return "\n".join(memories)


def canonical_ordinary_cells(rows: list[str]) -> str:
    """Losslessly normalize public ordinary-cell prose; perform no inference."""
    memories = []
    for row in rows:
        match = re.search(
            r"visit to ([^,]+), you see the ([^.]+)\. Its coat is ([\w-]+)",
            row,
            re.IGNORECASE,
        )
        id_match = re.match(r"\[([^]|]+)", row)
        if not match:
            continue
        land, animal, color = match.groups()
        ratio = ORDINARY_RATIO.get(color.lower())
        if ratio is None:
            continue
        provenance = id_match.group(1).strip() if id_match else "unknown"
        memories.append(
            f"CELL [{provenance}] | animal={animal} | land={land} | "
            f"color={color} | recipe={ratio}"
        )
    return "\n".join(memories)


def canonical_role_comparison(
    anchor_rows: list[str],
    query_rows: list[str],
    anchor_names: tuple[str, ...],
    query_animal: str,
    land_order: list[str],
) -> str:
    """Align public colors by land; leave the equality decision to the model."""
    cells: dict[tuple[str, str], str] = {}
    for row in anchor_rows + query_rows:
        match = re.search(
            r"visit to ([^,]+), you see the ([^.]+)\. Its coat is ([\w-]+)",
            row,
            re.IGNORECASE,
        )
        if match:
            land, animal, color = match.groups()
            cells[(animal.lower(), land.lower())] = color.lower()
    lines = ["LAND ORDER: " + " | ".join(land_order)]
    for label, animal in zip(
        ("FROG-LIKE", "COW-LIKE", "RAVEN-LIKE"), anchor_names
    ):
        values = [cells.get((animal.lower(), land.lower()), "MISSING") for land in land_order]
        lines.append(f"{label}: " + " | ".join(values))
    query_values = [
        cells.get((query_animal.lower(), land.lower()), "MISSING")
        for land in land_order
    ]
    lines.append(f"QUERY {query_animal}: " + " | ".join(query_values))
    return "\n".join(lines)


def parse_verdict(text: str) -> str:
    matches = re.findall(r"VERDICT:\s*(MATCH|MISMATCH)", text, re.IGNORECASE)
    return matches[-1].upper() if matches else "UNPARSED"


def parse_parents(text: str) -> set[str]:
    matches = re.findall(r"^PARENTS:\s*(.+)$", text, re.IGNORECASE | re.MULTILINE)
    if not matches or matches[-1].strip().upper() == "AMBIGUOUS":
        return set()
    return {
        value.strip().lower().rstrip(".,;:")
        for value in matches[-1].split(",")
        if value.strip()
    }


def parse_role(text: str) -> str | None:
    matches = re.findall(
        r"ROLE:\s*(FROG-LIKE|COW-LIKE|RAVEN-LIKE)", text, re.IGNORECASE
    )
    return matches[-1].upper() if matches else None


def parse_final(text: str) -> str | None:
    matches = re.findall(r"FINAL:\s*([\w-]+)", text, re.IGNORECASE)
    return matches[-1].lower().rstrip(".,;:") if matches else None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skin", choices=("aligned", "neutral", "conflicting"), default="aligned")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--goal-index", type=int, default=0)
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
    goal = world.goals[args.goal_index]
    rendered_goal = world.render_goals(args.skin)[args.goal_index]
    target_land = world.blend_land_surface(goal.land_id, args.skin)
    query_animal = skin.animal(goal.animal_id)
    source_lands = [skin.land(land_id) for land_id in world.source_land_ids]

    workshop_rows = [row for row in lifetime if row.startswith("[v02_lab_")]
    feed_rows = [row for row in lifetime if row.startswith("[v02_feed_")]
    demo_rows = [
        row
        for row in lifetime
        if row.startswith("[v02_obs_") and "| v02_demo_" in row
    ]
    anchor_names = tuple(skin.animal(animal_id) for animal_id in world.anchor_animals)
    anchor_rows = dedupe_surface(
        [
            row
            for row in lifetime
            if any(f"the {animal}.".lower() in row.lower() for animal in anchor_names)
            and any(land.lower() in row.lower() for land in source_lands)
        ]
    )
    operator_evidence = operator_episode_packets(feed_rows, anchor_rows, demo_rows)
    demo_labels = coat_labels(demo_rows)
    operator_workshop = canonical_workshop(
        [
            row
            for row in workshop_rows
            if any(re.search(rf"\b{re.escape(label)}\b", row, re.IGNORECASE) for label in demo_labels)
        ]
    )
    workshop = canonical_workshop(workshop_rows)
    backend = make_backend(args.backend, args.model)

    operator_prompt = OPERATOR_DREAM.format(
        ordinary_recipes=ORDINARY_RECIPES,
        evidence=operator_evidence,
        workshop=operator_workshop,
    )
    operator_memory = backend.generate([operator_prompt], max_tokens=2600)[0]

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
    role_prompt = ROLE_DREAM.format(
        comparison=canonical_role_comparison(
            role_anchor_rows,
            query_rows,
            anchor_names,
            query_animal,
            role_land_order,
        )
    )
    role_memory = backend.generate([role_prompt], max_tokens=1200)[0]

    target_rows = [row for row in lifetime if target_land.lower() in row.lower()]
    target_animals = parse_target_animals(target_rows)
    if len(target_animals) != 2:
        raise RuntimeError(f"expected two public target animals, got {target_animals}")
    target_labels = coat_labels(target_rows)
    target_workshop = canonical_workshop(
        [
            row
            for row in workshop_rows
            if any(re.search(rf"\b{re.escape(label)}\b", row, re.IGNORECASE) for label in target_labels)
        ]
    )

    candidates = source_parent_hypotheses(source_lands)
    branch_prompts = []
    for candidate in candidates:
        source_rows = dedupe_surface(
            [
                row
                for row in lifetime
                if any(land.lower() in row.lower() for land in candidate)
                and any(f"the {animal}.".lower() in row.lower() for animal in target_animals)
            ]
        )
        branch_prompts.append(
            BRANCH.format(
                operator_memory=operator_memory,
                ordinary_recipes=ORDINARY_RECIPES,
                workshop=target_workshop,
                target_rows="\n".join(target_rows),
                candidate=", ".join(candidate),
                source_rows=canonical_ordinary_cells(source_rows),
            )
        )
    branch_outputs = backend.generate(branch_prompts, max_tokens=1500)
    branch_records = [
        {
            "candidate": list(candidate),
            "verdict": parse_verdict(output),
            "text": output,
        }
        for candidate, output in zip(candidates, branch_outputs)
    ]
    matches = [record for record in branch_records if record["verdict"] == "MATCH"]
    if matches:
        branch_thoughts = "\n\n".join(record["text"] for record in matches)
    else:
        branch_thoughts = "NO BRANCH SELF-LABELED MATCH.\n\n" + "\n\n".join(
            record["text"] for record in branch_records
        )
    revisit_prompt = REVISIT.format(
        target_rows="\n".join(target_rows),
        operator_memory=operator_memory,
        branch_thoughts=branch_thoughts,
    )
    parent_memory = backend.generate([revisit_prompt], max_tokens=2200)[0]

    selected_parents = parse_parents(parent_memory)
    selected_role = parse_role(role_memory)
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
    compose_prompt = COMPOSE.format(
        operator_memory=operator_memory,
        ordinary_recipes=ORDINARY_RECIPES,
        role_memory=role_memory,
        parent_memory=parent_memory,
        read_plan=canonical_ordinary_cells(read_plan_rows),
        workshop=workshop,
        question=rendered_goal["question"],
    )
    answer = backend.generate([compose_prompt], max_tokens=1800)[0]

    expected_parents = {
        skin.land(parent).lower() for parent in world.target_parents[goal.land_id]
    }
    wanted = world.ratio_surface(goal.answer_ratio, args.skin).lower()
    got = parse_final(answer)
    true_branch_index = next(
        index
        for index, candidate in enumerate(candidates)
        if {land.lower() for land in candidate} == expected_parents
    )
    report = {
        "schema_version": world.schema_version,
        "condition": "model-only-branch-and-revisit",
        "truth_used_in_prompt": False,
        "model": args.model,
        "skin": args.skin,
        "seed": args.seed,
        "goal_index": args.goal_index,
        "goal_id": goal.id,
        "n_candidates": len(candidates),
        "n_model_matches": len(matches),
        "true_branch_model_verdict": branch_records[true_branch_index]["verdict"],
        "false_match_count": sum(
            record["verdict"] == "MATCH" and index != true_branch_index
            for index, record in enumerate(branch_records)
        ),
        "parent_exact": selected_parents == expected_parents,
        "wanted": wanted,
        "got": got,
        "correct": got == wanted,
        "operator_memory": operator_memory,
        "role_memory": role_memory,
        "selected_role": selected_role,
        "read_plan": canonical_ordinary_cells(read_plan_rows),
        "branch_records": branch_records,
        "parent_memory": parent_memory,
        "answer": answer,
        "prompts": {
            "operator": operator_prompt,
            "role": role_prompt,
            "branches": branch_prompts,
            "revisit": revisit_prompt,
            "compose": compose_prompt,
        },
    }
    output_dir = pathlib.Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    model_slug = re.sub(r"[^a-z0-9]+", "-", args.model.lower()).strip("-")
    path = output_dir / (
        f"lands_v02_branch_{args.skin}_s{args.seed}_g{args.goal_index}_{model_slug}.json"
    )
    path.write_text(json.dumps(report, indent=2) + "\n")
    print(
        f"[v02 branch] {args.skin} s{args.seed} g{args.goal_index}: "
        f"model_matches={len(matches)} true_branch={report['true_branch_model_verdict']} "
        f"false_matches={report['false_match_count']} parent={report['parent_exact']} "
        f"answer={got}/{wanted} correct={report['correct']}",
        flush=True,
    )


if __name__ == "__main__":
    main()
