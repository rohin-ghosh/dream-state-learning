"""Proposal-first compression of the Semantic World v0.2 depth ceiling.

The exhaustive ceiling checks all 57 public source subsets for every target.
This runner asks the frozen model for one ranked candidate frontier, verifies
only that frontier with the same atomic proof leaves, and reports success@k and
unique-self-selection@k.  Hidden state is consulted only after every model
output and self-selection has committed.

The output artifact is also accepted by ``run_lands_v02_finish.py`` because it
contains one dreamed ``parent_memory`` per goal.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re

from alchemy.backend import make_backend
from alchemy.run_lands_v02_branchsearch import (
    BRANCH_ROLE,
    MODEL,
    OPERATOR_DREAM,
    ORDINARY_RECIPES,
    REVISIT,
    canonical_ordinary_cells,
    canonical_workshop,
    coat_labels,
    dedupe_surface,
    operator_episode_packets,
    parse_parents,
    parse_target_animals,
    parse_verdict,
)
from lands.model import WorldConfig
from lands.skins import make_skin
from lands.v02 import SemanticWorldV02


PROPOSE = """Propose a SMALL ranked frontier of source-set hypotheses for one
unresolved confluence. This is an internal planning step, not a final answer.
Use only the public memories below. Do not assume the number of sources from
the two-source demonstrations: a candidate may contain 2 through 6 lands.

DREAMED OPERATOR MEMORY:
{operator_memory}

{ordinary_recipes}

PUBLIC SOURCE LAND VOCABULARY:
{source_lands}

EXACT PUBLIC TARGET LABEL MEMORY:
{target_workshop}

TWO PUBLIC TARGET OBSERVATIONS:
{target_rows}

PUBLIC SOURCE MEMORIES FOR THOSE SAME TWO ANIMALS:
{source_rows}

The source set is shared by both animals, but each animal has its own color in
each source land. Reason with the exact recipe vectors. Rank the most plausible
joint source sets; do not emit every possible subset. A candidate must use only
the source-land vocabulary and must list every land it contains.

After your scratch work, emit at most {k} lines in best-first order, exactly:
CANDIDATE 1: <comma-separated source lands>
CANDIDATE 2: <comma-separated source lands>
...
"""


def parse_candidate_sets(
    text: str, source_lands: list[str], limit: int
) -> list[tuple[str, ...]]:
    """Parse, canonicalize, and de-duplicate ranked public-land subsets."""
    canonical = {land.casefold(): land for land in source_lands}
    order = {land.casefold(): index for index, land in enumerate(source_lands)}
    result: list[tuple[str, ...]] = []
    seen: set[frozenset[str]] = set()
    for match in re.finditer(
        r"^\s*CANDIDATE(?:\s+\d+)?\s*:\s*(.+?)\s*$",
        text,
        re.IGNORECASE | re.MULTILINE,
    ):
        raw_values = [
            value.strip().rstrip(".;:")
            for value in match.group(1).split(",")
            if value.strip()
        ]
        lowered = [value.casefold() for value in raw_values]
        if not 2 <= len(lowered) <= len(source_lands):
            continue
        if len(set(lowered)) != len(lowered):
            continue
        if any(value not in canonical for value in lowered):
            continue
        key = frozenset(lowered)
        if key in seen:
            continue
        seen.add(key)
        result.append(
            tuple(
                canonical[value]
                for value in sorted(lowered, key=lambda item: order[item])
            )
        )
        if len(result) == limit:
            break
    return result


def token_count(backend, text: str) -> int | None:
    """Count content tokens when the selected backend exposes its tokenizer."""
    if hasattr(backend, "n_tokens"):
        return int(backend.n_tokens(text))
    tokenizer = getattr(backend, "tok", None)
    if tokenizer is not None:
        return len(tokenizer(text)["input_ids"])
    return None


def sum_tokens(backend, texts: list[str]) -> int | None:
    counts = [token_count(backend, text) for text in texts]
    if any(count is None for count in counts):
        return None
    return sum(count for count in counts if count is not None)


def unique_model_match(
    records: list[dict], prefix: int
) -> set[str]:
    matches = [
        record for record in records[:prefix] if record["verdict"] == "MATCH"
    ]
    if len(matches) != 1:
        return set()
    return {land.casefold() for land in matches[0]["candidate"]}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--skin", choices=("aligned", "neutral", "conflicting"), default="aligned"
    )
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--k", type=int, default=12)
    parser.add_argument("--backend", choices=("vllm", "hf"), default="vllm")
    parser.add_argument("--model", default=MODEL)
    parser.add_argument("--output-dir", default="alchemy/v2_out")
    args = parser.parse_args()
    if not 1 <= args.k <= 57:
        raise ValueError("--k must be between 1 and 57")
    if args.skin != "aligned":
        raise ValueError(
            "the current canonical recipe controller is aligned-only; "
            "neutral/conflicting require a model-dreamed recipe gauge"
        )

    world = SemanticWorldV02(WorldConfig(seed=args.seed))
    skin = make_skin(args.skin, world.animal_ids, world.source_land_ids)
    lifetime = world.render_lifetime(args.skin)
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
            if any(f"the {animal}.".casefold() in row.casefold() for animal in anchor_names)
            and any(land.casefold() in row.casefold() for land in source_lands)
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
    proposal_prompts = []
    rendered_goals = world.render_goals(args.skin)
    for goal, rendered_goal in zip(world.goals, rendered_goals):
        target_land = world.blend_land_surface(goal.land_id, args.skin)
        target_rows = [row for row in lifetime if target_land.casefold() in row.casefold()]
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
        source_rows = dedupe_surface(
            [
                row
                for row in lifetime
                if any(land.casefold() in row.casefold() for land in source_lands)
                and any(
                    f"the {animal}.".casefold() in row.casefold()
                    for animal in target_animals
                )
            ]
        )
        proposal_prompts.append(
            PROPOSE.format(
                operator_memory=operator_memory,
                ordinary_recipes=ORDINARY_RECIPES,
                source_lands=" | ".join(source_lands),
                target_workshop=target_workshop,
                target_rows="\n".join(target_rows),
                source_rows=canonical_ordinary_cells(source_rows),
                k=args.k,
            )
        )
        states.append(
            {
                "goal": goal,
                "rendered_goal": rendered_goal,
                "target_rows": target_rows,
                "target_animals": target_animals,
            }
        )

    proposal_outputs = backend.generate(proposal_prompts, max_tokens=2400)
    all_branch_prompts = []
    for state, proposal_output in zip(states, proposal_outputs):
        candidates = parse_candidate_sets(proposal_output, source_lands, args.k)
        state["proposal_output"] = proposal_output
        state["candidates"] = candidates
        state["branch_start"] = len(all_branch_prompts)
        for candidate in candidates:
            for animal in state["target_animals"]:
                target_row = next(
                    row
                    for row in state["target_rows"]
                    if f"the {animal}.".casefold() in row.casefold()
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
                        if any(land.casefold() in row.casefold() for land in candidate)
                        and f"the {animal}.".casefold() in row.casefold()
                    ]
                )
                all_branch_prompts.append(
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
        state["branch_stop"] = len(all_branch_prompts)

    all_branch_outputs = (
        backend.generate(all_branch_prompts, max_tokens=1000)
        if all_branch_prompts
        else []
    )
    revisit_prompts = []
    for state in states:
        outputs = all_branch_outputs[state["branch_start"] : state["branch_stop"]]
        width = len(state["target_animals"])
        records = []
        for candidate_index, candidate in enumerate(state["candidates"]):
            atomic_outputs = outputs[
                candidate_index * width : candidate_index * width + width
            ]
            atomic_verdicts = [parse_verdict(output) for output in atomic_outputs]
            records.append(
                {
                    "candidate": list(candidate),
                    "verdict": (
                        "MATCH"
                        if all(verdict == "MATCH" for verdict in atomic_verdicts)
                        else "MISMATCH"
                        if all(
                            verdict in {"MATCH", "MISMATCH"}
                            for verdict in atomic_verdicts
                        )
                        else "UNPARSED"
                    ),
                    "atomic_verdicts": dict(
                        zip(state["target_animals"], atomic_verdicts)
                    ),
                    "text": "\n\n".join(atomic_outputs),
                }
            )
        state["branch_records"] = records
        matches = [record for record in records if record["verdict"] == "MATCH"]
        branch_thoughts = (
            "\n\n".join(record["text"] for record in matches)
            if matches
            else "NO PROPOSED BRANCH SELF-LABELED MATCH.\n\n"
            + "\n\n".join(record["text"] for record in records)
        )
        revisit_prompts.append(
            REVISIT.format(
                target_rows="\n".join(state["target_rows"]),
                operator_memory=operator_memory,
                branch_thoughts=branch_thoughts,
            )
        )
    parent_memories = backend.generate(revisit_prompts, max_tokens=2200)

    requested_prefixes = tuple(value for value in (1, 2, 4, 8, 12) if value <= args.k)
    if args.k not in requested_prefixes:
        requested_prefixes = (*requested_prefixes, args.k)
    results = []
    for state, parent_memory in zip(states, parent_memories):
        goal = state["goal"]
        expected_parents = {
            skin.land(parent).casefold()
            for parent in world.target_parents[goal.land_id]
        }
        candidates = state["candidates"]
        records = state["branch_records"]
        proposed_sets = [
            {land.casefold() for land in candidate} for candidate in candidates
        ]
        selected_parents = parse_parents(parent_memory)
        success_at = {
            str(prefix): any(
                candidate == expected_parents for candidate in proposed_sets[:prefix]
            )
            for prefix in requested_prefixes
        }
        self_selected_at = {
            str(prefix): unique_model_match(records, prefix) == expected_parents
            for prefix in requested_prefixes
        }
        true_index = next(
            (
                index
                for index, candidate in enumerate(proposed_sets)
                if candidate == expected_parents
            ),
            None,
        )
        results.append(
            {
                "goal_id": goal.id,
                "question": state["rendered_goal"]["question"],
                "n_proposals": len(candidates),
                "success_at": success_at,
                "self_selected_parent_at": self_selected_at,
                "true_proposal_rank": None if true_index is None else true_index + 1,
                "true_branch_model_verdict": (
                    "NOT_PROPOSED" if true_index is None else records[true_index]["verdict"]
                ),
                "false_match_count": sum(
                    record["verdict"] == "MATCH"
                    and {land.casefold() for land in record["candidate"]}
                    != expected_parents
                    for record in records
                ),
                "parent_exact": selected_parents == expected_parents,
                "parent_memory": parent_memory,
                "proposal_output": state["proposal_output"],
                "branch_records": records,
                "prompts": {
                    "proposal": proposal_prompts[len(results)],
                    "branches": all_branch_prompts[
                        state["branch_start"] : state["branch_stop"]
                    ],
                    "revisit": revisit_prompts[len(results)],
                },
            }
        )

    all_prompts = [operator_prompt, *proposal_prompts, *all_branch_prompts, *revisit_prompts]
    all_outputs = [operator_memory, *proposal_outputs, *all_branch_outputs, *parent_memories]
    report = {
        "schema_version": world.schema_version,
        "condition": "model-proposed-topk-atomic-check-revisit",
        "truth_used_in_prompt": False,
        "model": args.model,
        "skin": args.skin,
        "seed": args.seed,
        "max_k": args.k,
        "n": len(results),
        "floor": round(1 / len(results), 3),
        "proposal_success_at": {
            str(prefix): round(
                sum(row["success_at"][str(prefix)] for row in results) / len(results),
                3,
            )
            for prefix in requested_prefixes
        },
        "self_selected_parent_at": {
            str(prefix): round(
                sum(
                    row["self_selected_parent_at"][str(prefix)] for row in results
                )
                / len(results),
                3,
            )
            for prefix in requested_prefixes
        },
        "parent_accuracy_after_revisit": round(
            sum(row["parent_exact"] for row in results) / len(results), 3
        ),
        "call_accounting": {
            "operator": 1,
            "proposal": len(proposal_prompts),
            "atomic_proof_leaf": len(all_branch_prompts),
            "revisit": len(revisit_prompts),
            "total_model_queries": len(all_prompts),
            "exhaustive_atomic_leaf_reference": len(results) * 57 * 2,
            "input_content_tokens": sum_tokens(backend, all_prompts),
            "output_content_tokens": sum_tokens(backend, all_outputs),
        },
        "operator_memory": operator_memory,
        "operator_prompt": operator_prompt,
        "results": results,
    }
    output_dir = pathlib.Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    model_slug = re.sub(r"[^a-z0-9]+", "-", args.model.casefold()).strip("-")
    path = output_dir / (
        f"lands_v02_topk_{args.skin}_s{args.seed}_{model_slug}_k{args.k}.json"
    )
    path.write_text(json.dumps(report, indent=2) + "\n")
    print(
        f"[v02 top-k] {args.skin} s{args.seed}: "
        f"proposal={report['proposal_success_at']} "
        f"self_select={report['self_selected_parent_at']} "
        f"revisit={report['parent_accuracy_after_revisit']} "
        f"leaves={len(all_branch_prompts)}/{len(results) * 57 * 2}",
        flush=True,
    )


if __name__ == "__main__":
    main()
