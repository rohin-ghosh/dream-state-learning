"""CLI for inspecting and exporting Action World v0."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .artifacts import export_world
from .model import ActionDepth, WorldConfig
from .solver import evaluate_world
from .world import ActionWorld


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    inspect = sub.add_parser("inspect")
    inspect.add_argument("--seed", type=int, default=0)

    baselines = sub.add_parser("baselines")
    baselines.add_argument("--seed", type=int, default=0)

    generate = sub.add_parser("generate")
    generate.add_argument("--seed", type=int, default=0)
    generate.add_argument("--output", type=Path, required=True)

    args = parser.parse_args(argv)
    world = ActionWorld(WorldConfig(seed=args.seed))
    if args.command == "inspect":
        first = world.sample_lifetime().episodes[0]
        print(first.intro)
        for step in first.steps:
            print(f"  {step.action} -> {step.observation}")
        for depth in ActionDepth:
            goal = world.eval_goals(depth)[0]
            print(f"{depth.value}: {goal.question}")
        return 0
    if args.command == "baselines":
        print(json.dumps(evaluate_world(world), indent=2, sort_keys=True))
        return 0
    if args.command == "generate":
        print(export_world(world, args.output))
        return 0
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
