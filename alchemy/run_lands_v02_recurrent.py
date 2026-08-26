"""Verifier-free recurrent dream/think ceiling for Semantic World v0.2.

This is intentionally a prompt-heavy discovery condition.  It tests whether a
frozen model can build the missing multi-hop structure by re-reading its own
provisional memories.  No FactorSolver result, hidden role, parent set, target
answer, or offline verdict is placed in any prompt.

The loop is inspectable text throughout:

  experience -> independent world dreams -> self-synthesis -> per-target dream
  -> evidence-conditioned self-revision -> answer

The only programmatic retrieval is lexical: public rows containing the queried
animal/land are copied beside the full public lifetime.  Offline truth is used
only after all generations commit, to report parent accuracy and answer score.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re

from alchemy.backend import make_backend
from lands.model import WorldConfig
from lands.skins import make_skin
from lands.v02 import SemanticWorldV02


MODEL = "Qwen/Qwen2.5-7B-Instruct"

WORLD_DREAM = """You are asleep after a lifetime in a synthetic world. Build
an inspectable provisional memory that will help your future self answer the
questions. Do not answer the questions yet. Names can suggest hypotheses, but
only observations are evidence.

PUBLIC LIFETIME:
{lifetime}

FUTURE QUESTIONS:
{questions}

Dream slowly across the lifetime. In particular, look for:
- repeated animal behavior that reveals a small number of latent animal roles.
  A role is a COMPLETE six-ordinary-land color signature, not an animal name or
  one remembered color. Frog, cow, and raven have complete anchor signatures;
  classify other animals by matching their partial observations to those rows;
- a numerical recipe for each ordinary color using red/yellow/blue amounts;
- what the two known-source confluence demonstrations do to source outcomes;
- which memories would be needed to infer an unknown confluence's sources.

Write a compact WORLD MEMORY with cited observation IDs. Separate direct facts,
hypotheses, and unresolved items. Do not pretend an unknown source set is known.
"""

SYNTHESIZE = """You are dreaming over two earlier dreams. Re-read the actual
lifetime, find where the dreams agree or hallucinate, and write one corrected
provisional WORLD MEMORY. This is self-reflection, not an oracle: do not add a
fact unless you can derive it from the public lifetime.

PUBLIC LIFETIME:
{lifetime}

DREAM A:
{dream_a}

DREAM B:
{dream_b}

Your memory must make these reusable structures explicit:
1. one literal table whose rows are FROG-LIKE, COW-LIKE, and RAVEN-LIKE and
   whose columns are all six ordinary lands, with a color in every cell;
2. the role of each non-anchor animal, expressed as exactly one of those three
   row names and checked against ALL of that animal's observed ordinary cells;
3. a color-label <-> primitive (red,yellow,blue) recipe dictionary;
4. the confluence operation implied by BOTH known-source demonstrations.

Representation invariants: red=(1,0,0), yellow=(0,1,0), blue=(0,0,1),
orange=(1,1,0), green=(0,1,1), and purple=(1,0,1). A role is never merely
"red" or "fox". Demonstrate the inferred confluence operation numerically on
all three anchor rows in both known-source lands.

End with a SELF-AUDIT listing any uncertain or inconsistent memory lines.
"""

TARGET_DREAM = """You are revisiting one unresolved situation using your
provisional world memory. Everything below is public experience or your own
earlier thought; no external checker has filtered it.

WORLD MEMORY:
{world_memory}

PUBLIC LIFETIME:
{lifetime}

LEXICALLY RETRIEVED ROWS FOR THIS QUESTION:
{retrieved}

QUESTION:
{question}

Work as a careful internal search, not a guess:
1. infer the queried animal's latent role from its ordinary-land observations;
2. identify the TWO OTHER ANCHOR ROLES actually observed in the target
   confluence. These target observations—not the queried animal's ordinary
   observations—are the constraints on the unknown source set. Translate
   their target colors into exact primitive red/yellow/blue recipes;
3. enumerate possible subsets of the six ordinary source lands and apply the
   operation learned from the demonstrations to those TWO observed target
   roles, using the corresponding two rows of the six-land role table;
4. keep a source set only if it predicts both observations exactly;
5. use that source set and the queried role to derive the withheld outcome.

Critical search invariants:
- A land does NOT have one generic color. Each land contributes a different
  color for FROG-LIKE, COW-LIKE, and RAVEN-LIKE. Do separate arithmetic for
  each observed role using its own row of the table.
- The demonstrations happen to have two sources, but an unknown target can
  have any source-set size from 2 through 6. Search every size until the exact
  two-role constraints leave a survivor; do not stop after pairs.
- Recipe ratios must match exactly up to a common divisor. For example, an
  observed (1,3,1) cannot be explained by a proposed (1,1,1).

If more than one set survives, say so rather than silently choosing. Show the
candidate elimination and end with exactly these machine-readable lines:
ROLE: FROG-LIKE | COW-LIKE | RAVEN-LIKE
PARENTS: <source land>, <source land>, ...
PREDICTED OBSERVED: <both public target observations, quoted and recomputed>
HIDDEN RECIPE: (<red>, <yellow>, <blue>)
HIDDEN LABEL: <one color-or-state token>
"""

REVISE = """Self-check your own target memory against the raw public evidence
and your earlier world memory. No oracle verdict is available. Recompute the
two observed target outcomes from the proposed source set. If either prediction
does not exactly match, search again and rewrite the memory. Also check the
withheld arithmetic and use an EXACT recipe-label match, never a nearest color.
The proposed parents must reproduce the two colors observed IN THE TARGET LAND.
The queried animal's ordinary-land observations identify its role only; they
are not evidence that those ordinary lands are the target's parents. Reject a
memory that conflates those two uses of evidence.

WORLD MEMORY:
{world_memory}

RELEVANT PUBLIC EVIDENCE:
{retrieved}

QUESTION:
{question}

PROVISIONAL TARGET MEMORY:
{target_memory}

End with the corrected machine-readable lines:
ROLE: FROG-LIKE | COW-LIKE | RAVEN-LIKE
PARENTS: <source land>, <source land>, ...
PREDICTED OBSERVED: <both public target observations, quoted and recomputed>
HIDDEN RECIPE: (<red>, <yellow>, <blue>)
HIDDEN LABEL: <one color-or-state token>
"""

ANSWER = """Answer the question using the two dreamed memories. Treat them as
fallible: briefly check that the target source set predicts its public observed
outcomes and that the final recipe has an exact dictionary label.

WORLD MEMORY:
{world_memory}

TARGET MEMORY:
{target_memory}

QUESTION:
{question}

End with exactly:
FINAL: <one color-or-state token>
"""


def final_token(text: str) -> str | None:
    matches = re.findall(r"FINAL:\s*([\w-]+)", text, flags=re.IGNORECASE)
    return matches[-1].lower().rstrip(".,;:") if matches else None


def proposed_parents(text: str) -> set[str]:
    matches = re.findall(r"^PARENTS:\s*(.+)$", text, flags=re.IGNORECASE | re.MULTILINE)
    if not matches:
        return set()
    return {
        item.strip().lower().rstrip(".,;:")
        for item in matches[-1].split(",")
        if item.strip()
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skin", choices=("aligned", "neutral", "conflicting"), default="aligned")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--backend", choices=("vllm", "hf"), default="vllm")
    parser.add_argument("--model", default=MODEL)
    parser.add_argument("--output-dir", default="alchemy/v2_out")
    parser.add_argument("--goal-index", type=int)
    parser.add_argument("--world-memory-from")
    args = parser.parse_args()

    world = SemanticWorldV02(WorldConfig(seed=args.seed))
    skin = make_skin(args.skin, world.animal_ids, world.source_land_ids)
    lifetime_rows = world.render_lifetime(args.skin)
    lifetime = "\n".join(lifetime_rows)
    rendered_goals = world.render_goals(args.skin)
    questions = "\n".join(f"- {row['question']}" for row in rendered_goals)
    backend = make_backend(args.backend, args.model)

    if args.world_memory_from:
        prior = json.loads(pathlib.Path(args.world_memory_from).read_text())
        world_memory = prior["world_memory"]
        dreams = []
        dream_prompt = None
        synthesis_prompt = None
    else:
        dream_prompt = WORLD_DREAM.format(lifetime=lifetime, questions=questions)
        dreams = backend.generate([dream_prompt, dream_prompt], max_tokens=3200)
        synthesis_prompt = SYNTHESIZE.format(
            lifetime=lifetime, dream_a=dreams[0], dream_b=dreams[1]
        )
        world_memory = backend.generate([synthesis_prompt], max_tokens=4200)[0]

    selected = list(zip(world.goals, rendered_goals))
    if args.goal_index is not None:
        selected = [selected[args.goal_index]]
    selected_rendered = [rendered for _, rendered in selected]

    target_prompts = []
    retrieved_rows = []
    for goal, rendered in selected:
        animal = skin.animal(goal.animal_id)
        land = world.blend_land_surface(goal.land_id, args.skin)
        retrieved = "\n".join(
            row for row in lifetime_rows if animal.lower() in row.lower() or land.lower() in row.lower()
        )
        retrieved_rows.append(retrieved)
        target_prompts.append(
            TARGET_DREAM.format(
                world_memory=world_memory,
                lifetime=lifetime,
                retrieved=retrieved,
                question=rendered["question"],
            )
        )
    target_memories = backend.generate(target_prompts, max_tokens=3600)

    revision_prompts = [
        REVISE.format(
            world_memory=world_memory,
            retrieved=retrieved,
            question=rendered["question"],
            target_memory=target_memory,
        )
        for retrieved, rendered, target_memory in zip(
            retrieved_rows, selected_rendered, target_memories
        )
    ]
    revised_memories = backend.generate(revision_prompts, max_tokens=3000)

    answer_prompts = [
        ANSWER.format(
            world_memory=world_memory,
            target_memory=target_memory,
            question=rendered["question"],
        )
        for rendered, target_memory in zip(selected_rendered, revised_memories)
    ]
    answers = backend.generate(answer_prompts, max_tokens=1200)

    results = []
    for (goal, rendered), target_memory, revised, answer in zip(
        selected, target_memories, revised_memories, answers
    ):
        wanted = world.ratio_surface(goal.answer_ratio, args.skin).lower()
        got = final_token(answer)
        expected_parents = {
            skin.land(parent).lower() for parent in world.target_parents[goal.land_id]
        }
        initial_parents = proposed_parents(target_memory)
        revised_parents = proposed_parents(revised)
        results.append(
            {
                "goal_id": goal.id,
                "question": rendered["question"],
                "wanted": wanted,
                "got": got,
                "correct": got == wanted,
                "initial_parent_exact": initial_parents == expected_parents,
                "revised_parent_exact": revised_parents == expected_parents,
                "initial_parent_count": len(initial_parents),
                "revised_parent_count": len(revised_parents),
                "target_memory": target_memory,
                "revised_memory": revised,
                "answer": answer,
            }
        )

    answer_accuracy = sum(row["correct"] for row in results) / len(results)
    initial_parent_accuracy = sum(row["initial_parent_exact"] for row in results) / len(results)
    revised_parent_accuracy = sum(row["revised_parent_exact"] for row in results) / len(results)
    report = {
        "schema_version": world.schema_version,
        "condition": "verifier-free-recurrent-scaffolded",
        "truth_used_in_prompt": False,
        "model": args.model,
        "skin": args.skin,
        "seed": args.seed,
        "answer_accuracy": round(answer_accuracy, 3),
        "floor": round(1 / len(world.goals), 3),
        "initial_parent_accuracy": round(initial_parent_accuracy, 3),
        "revised_parent_accuracy": round(revised_parent_accuracy, 3),
        "n": len(results),
        "world_dreams": dreams,
        "world_memory": world_memory,
        "results": results,
        "prompts": {
            "world_dream": dream_prompt,
            "synthesis": synthesis_prompt,
            "targets": target_prompts,
            "revisions": revision_prompts,
            "answers": answer_prompts,
        },
    }
    output_dir = pathlib.Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    model_slug = re.sub(r"[^a-z0-9]+", "-", args.model.lower()).strip("-")
    goal_suffix = "" if args.goal_index is None else f"_g{args.goal_index}"
    path = output_dir / (
        f"lands_v02_recurrent_{args.skin}_s{args.seed}_{model_slug}{goal_suffix}.json"
    )
    path.write_text(json.dumps(report, indent=2) + "\n")
    print(
        f"[v02 recurrent] {args.skin} s{args.seed}: answer={answer_accuracy:.3f} "
        f"parents(initial/revised)={initial_parent_accuracy:.3f}/{revised_parent_accuracy:.3f} "
        f"floor={1 / len(world.goals):.3f}",
        flush=True,
    )


if __name__ == "__main__":
    main()
