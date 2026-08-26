"""CPU controls for Action World v0.

The parity solver knows the generator family and is therefore a privileged
context-oracle control, not a component of the dream/think headline arm.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Callable

from .model import ActionDepth, Goal, Lifetime
from .world import ActionWorld, FEATURES, _law_candidates


def observed_danger_labels(lifetime: Lifetime) -> dict[str, str]:
    """Recover only danger sides actually revealed by lived experience."""
    labels: dict[str, str] = {}
    for step in lifetime.steps:
        if step.revealed is None:
            continue
        side, status = step.revealed
        labels[step.threshold_id] = side if status == "danger" else (
            "right" if side == "left" else "left"
        )
    return labels


class ParityContextOracle:
    """Privileged algebra-aware solver over public experienced outcomes."""

    def __init__(self, world: ActionWorld):
        labels = observed_danger_labels(world.sample_lifetime())
        labeled_patterns = [
            (world._bits_by_threshold[threshold_id], side)  # evaluator control
            for threshold_id, side in labels.items()
        ]
        candidates = _law_candidates(labeled_patterns)
        if len(candidates) != 1:
            raise ValueError(f"expected one law candidate, found {len(candidates)}")
        self.mask, self.bias = candidates[0]
        self.world = world

    def predict(self, threshold_id: str) -> str:
        bits = self.world._bits_by_threshold[threshold_id]
        parity = self.bias
        for active, bit in zip(self.mask, bits):
            if active:
                parity ^= bit
        return "right" if parity else "left"


def direct_policy(side_for: Callable[[str], str]) -> Callable[[dict], str]:
    def policy(state: dict) -> str:
        if not state["opened"]:
            return "open"
        if state["guarded"] is None:
            side = side_for(state["threshold"]["threshold_id"])
            return f"guard_{side}"
        return "enter"

    return policy


def cautious_policy(state: dict) -> str:
    """General procedure: inspect one side, infer the other if it is clear."""
    if not state["opened"]:
        return "open"
    inspected = state["inspected"]
    if not inspected:
        return "inspect_left"
    if state["guarded"] is None:
        side = "left" if inspected.get("left") == "danger" else "right"
        return f"guard_{side}"
    return "enter"


def observed_lookup_policy(world: ActionWorld) -> Callable[[dict], str]:
    labels = observed_danger_labels(world.sample_lifetime())
    return direct_policy(lambda threshold_id: labels.get(threshold_id, "left"))


def evaluate_world(world: ActionWorld) -> dict:
    oracle_solver = ParityContextOracle(world)
    methods = {
        "observed_lookup": observed_lookup_policy(world),
        "generic_cautious": cautious_policy,
        "parity_context_oracle": direct_policy(oracle_solver.predict),
        "latent_oracle": direct_policy(world.threat_side),
    }
    result = {"methods": {}}
    for method_name, policy in methods.items():
        by_depth = defaultdict(list)
        for goal in world.eval_goals():
            run = world.run_policy(goal, policy)
            by_depth[goal.depth.value].append(run)
        result["methods"][method_name] = {
            "overall": {
                "success_rate": sum(
                    run.success for runs in by_depth.values() for run in runs
                )
                / sum(len(runs) for runs in by_depth.values()),
            },
            "by_depth": {
                depth: {
                    "success_rate": sum(run.success for run in runs) / len(runs),
                    "mean_steps": sum(len(run.actions) for run in runs) / len(runs),
                    "mean_reward": sum(run.total_reward for run in runs) / len(runs),
                }
                for depth, runs in sorted(by_depth.items())
            },
        }
    return result
