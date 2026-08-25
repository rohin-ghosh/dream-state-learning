"""Command-line entry points for CPU generation and validation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .artifacts import export_world
from .model import WorldConfig
from .solver import evaluate_world
from .world import SemanticWorld


def _world(seed: int) -> SemanticWorld:
    return SemanticWorld(WorldConfig(seed=seed))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    generate = sub.add_parser("generate", help="export a model/evaluator dataset")
    generate.add_argument("--seed", type=int, default=0)
    generate.add_argument("--output", type=Path, required=True)

    baselines = sub.add_parser("baselines", help="run CPU ceilings")
    baselines.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2])

    inspect = sub.add_parser("inspect", help="print one rendered sample")
    inspect.add_argument("--seed", type=int, default=0)
    inspect.add_argument(
        "--skin", choices=("aligned", "neutral", "conflicting"), default="aligned"
    )
    inspect.add_argument(
        "--include-answers",
        action="store_true",
        help="explicit evaluator-only opt-in",
    )

    args = parser.parse_args(argv)
    if args.command == "generate":
        output = export_world(_world(args.seed), args.output)
        print(output)
        return 0
    if args.command == "baselines":
        result = {
            str(seed): evaluate_world(_world(seed)) for seed in args.seeds
        }
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    if args.command == "inspect":
        world = _world(args.seed)
        rendered = world.render(args.skin, include_answers=args.include_answers)
        print(rendered.observations[0].text)
        print(rendered.observations[-1].text)
        for goal in rendered.goals[:2] + rendered.goals[-2:]:
            suffix = f" -> {goal.answer}" if goal.answer is not None else ""
            print(f"{goal.goal_id}: {goal.question}{suffix}")
        return 0
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
