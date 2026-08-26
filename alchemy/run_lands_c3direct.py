"""LoRA-direct cell for the dreamed-memory substrate×read-protocol matrix.

The adapter is already trained by `run_lands_c3p2.py`.  This runner keeps it
mounted and asks every held-out goal directly, using the same pairwise answer
instructions as the context-direct arm.  No atomic query plan, candidate
recognition, or clean-base unmount is used.
"""

from __future__ import annotations

import argparse
import json
import pathlib

from alchemy.backend import make_backend
from alchemy.run_lands_c012 import PAIRWISE_SUFFIX, depth_report, score_output
from lands import SemanticWorld, WorldConfig
from lands.skins import make_skin


MODEL = "Qwen/Qwen2.5-7B-Instruct"
ADAPTER_DIRECT_SUFFIX = PAIRWISE_SUFFIX.replace(
    "Use ONLY the memory reads above as facts.",
    "Use facts recalled from your mounted consolidated-memory adapter.",
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skin", default="aligned")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--tag", default="_e")
    parser.add_argument("--lora", help="existing adapter directory")
    parser.add_argument("--model", default=MODEL)
    args = parser.parse_args()

    world = SemanticWorld(WorldConfig(seed=args.seed))
    goals = world.eval_goals()
    skin = make_skin(args.skin, world.animal_ids, world.source_land_ids)
    rendered = world.render(args.skin)
    questions = {goal.goal_id: goal.question for goal in rendered.goals}
    lora_path = pathlib.Path(
        args.lora
        or f"alchemy/v2_out/lands_c3p2{args.tag}_lora_{args.skin}_s{args.seed}"
    )
    if not lora_path.is_dir():
        raise SystemExit(f"adapter does not exist: {lora_path}")

    prompts = []
    for goal in goals:
        prompts.append(
            "Your past consolidated memories are stored in the currently "
            "mounted memory adapter. Retrieve whatever facts are needed from "
            "those weights.\n\n"
            + questions[goal.id]
            + ADAPTER_DIRECT_SUFFIX
        )
    backend = make_backend(
        "vllm", args.model, enable_lora=True, max_lora_rank=64
    )
    outputs = backend.generate(
        prompts, max_tokens=900, lora_path=str(lora_path.resolve())
    )

    outcomes = [
        score_output(skin, output, goal.answer_color_id)[0]
        for goal, output in zip(goals, outputs)
    ]
    report = depth_report(world, goals, outcomes)
    report["adapter"] = str(lora_path)
    report["read_protocol"] = "direct_generation_adapter_mounted"
    report["samples"] = outputs[:3]
    output_path = pathlib.Path(
        f"alchemy/v2_out/lands_c3direct{args.tag}_{args.skin}_s{args.seed}.json"
    )
    output_path.write_text(json.dumps(report, indent=2) + "\n")
    print(
        f"[c3direct{args.tag}] {args.skin} s{args.seed}: "
        + " ".join(
            f"{depth}={values['acc']}"
            for depth, values in report.items()
            if isinstance(values, dict)
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
