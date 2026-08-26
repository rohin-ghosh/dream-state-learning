"""Integrity tests for Action World v0.

Run directly or with pytest:
    PYTHONPATH=. python3 action_world/test_world.py
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from action_world import ActionDepth, ActionWorld, WorldConfig
from action_world.artifacts import export_world
from action_world.solver import (
    ParityContextOracle,
    cautious_policy,
    direct_policy,
    evaluate_world,
    observed_danger_labels,
)


def test_determinism_and_seed_variation():
    left = ActionWorld(WorldConfig(seed=5))
    right = ActionWorld(WorldConfig(seed=5))
    other = ActionWorld(WorldConfig(seed=6))
    assert left.world_fingerprint() == right.world_fingerprint()
    assert left.sample_lifetime().public_dict() == right.sample_lifetime().public_dict()
    assert left.world_fingerprint() != other.world_fingerprint()


def test_public_bundle_has_no_hidden_law_or_answers():
    world = ActionWorld()
    public = json.dumps(world.public_bundle(), sort_keys=True)
    assert not world.leakage_scan(public)
    for forbidden in ("law_mask", "law_bias", "threat_side", "parity"):
        assert forbidden not in public.lower()
    assert all(
        not {"answer", "depth", "proof_id", "tags"} & set(goal.public_dict())
        for goal in world.eval_goals()
    )
    assert "policy_kind" not in public
    assert '"split"' not in public


def test_experience_eval_patterns_are_disjoint_and_law_is_identifiable():
    world = ActionWorld(WorldConfig(seed=11))
    assert not set(world.training_patterns) & set(world.held_out_patterns)
    solver = ParityContextOracle(world)
    assert all(
        solver.predict(threshold_id) == world.threat_side(threshold_id)
        for threshold_id in world.thresholds
    )
    observed = observed_danger_labels(world.sample_lifetime())
    assert set(observed) == set(world.training_threshold_ids)
    assert not set(observed) & set(world.eval_threshold_ids)


def test_lived_cautious_and_reckless_episodes_have_real_consequences():
    world = ActionWorld(WorldConfig(seed=2, reckless_fraction=1.0))
    cautious = [
        episode for episode in world.sample_lifetime().episodes
        if episode.policy_kind == "cautious"
    ]
    reckless = [
        episode for episode in world.sample_lifetime().episodes
        if episode.policy_kind == "reckless"
    ]
    assert len(cautious) == len(world.training_threshold_ids)
    assert len(reckless) == len(world.training_threshold_ids)
    assert all(episode.success for episode in cautious)
    assert all(not episode.success for episode in reckless)
    assert all("attacks you" in episode.steps[-1].observation for episode in reckless)


def test_depths_separate_procedure_law_and_chain():
    world = ActionWorld(WorldConfig(seed=7))
    solver = ParityContextOracle(world)
    oracle_policy = direct_policy(solver.predict)

    # Generic inspect-and-react transfers to unseen thresholds at A1.
    assert all(
        world.run_policy(goal, cautious_policy).success
        for goal in world.eval_goals(ActionDepth.A1)
    )
    # The same four-action policy cannot meet the tight A2/A3 budgets.
    assert all(
        not world.run_policy(goal, cautious_policy).success
        for depth in (ActionDepth.A2, ActionDepth.A3)
        for goal in world.eval_goals(depth)
    )
    # The inferred world law enables direct three-action crossings and chains.
    assert all(
        world.run_policy(goal, oracle_policy).success
        for goal in world.eval_goals()
    )


def test_wrong_guard_is_attacked_and_action_budget_is_real():
    world = ActionWorld(WorldConfig(seed=3))
    goal = world.eval_goals(ActionDepth.A2)[0]
    danger = world.threat_side(goal.threshold_ids[0])
    wrong = "right" if danger == "left" else "left"
    result = world.run_actions(goal, ("open", f"guard_{wrong}", "enter"))
    assert not result.success
    assert result.terminal_reason == "attacked"
    assert result.total_reward < 0

    timeout = world.run_actions(goal, ("open", "inspect_left", "guard_left"))
    assert not timeout.success
    assert timeout.terminal_reason == "budget_exhausted"


def test_proof_shapes_and_baselines():
    world = ActionWorld(WorldConfig(seed=13))
    shapes = {}
    evidence_ids = {step.id for step in world.sample_lifetime().steps}
    for depth in ActionDepth:
        depth_shapes = set()
        for goal in world.eval_goals(depth):
            proof = world.proof_for(goal)
            proof.validate(evidence_ids)
            depth_shapes.add(proof.canonical_shape())
        assert len(depth_shapes) == 1
        shapes[depth] = next(iter(depth_shapes))
    assert len(set(shapes.values())) == len(ActionDepth)

    result = evaluate_world(world)["methods"]
    assert result["latent_oracle"]["overall"]["success_rate"] == 1.0
    assert result["parity_context_oracle"]["overall"]["success_rate"] == 1.0
    assert result["generic_cautious"]["by_depth"]["A1"]["success_rate"] == 1.0
    assert result["generic_cautious"]["by_depth"]["A2"]["success_rate"] == 0.0
    assert result["generic_cautious"]["by_depth"]["A3"]["success_rate"] == 0.0


def test_depth_separation_is_stable_across_100_world_seeds():
    for seed in range(100):
        methods = evaluate_world(ActionWorld(WorldConfig(seed=seed)))["methods"]
        assert methods["latent_oracle"]["overall"]["success_rate"] == 1.0
        assert methods["parity_context_oracle"]["overall"]["success_rate"] == 1.0
        assert methods["generic_cautious"]["by_depth"]["A1"]["success_rate"] == 1.0
        assert methods["generic_cautious"]["by_depth"]["A2"]["success_rate"] == 0.0
        assert methods["generic_cautious"]["by_depth"]["A3"]["success_rate"] == 0.0


def test_artifact_export_separates_public_and_evaluator_files():
    world = ActionWorld(WorldConfig(seed=17))
    with tempfile.TemporaryDirectory() as directory:
        output = export_world(world, Path(directory) / "world")
        public_text = "\n".join(
            path.read_text()
            for path in (output / "model_input" / "public").glob("*")
        )
        assert not world.leakage_scan(public_text)
        latent = json.loads((output / "evaluator_only" / "latent_world.json").read_text())
        assert "law_mask" in latent and "law_bias" in latent
        manifest = json.loads((output / "manifest.json").read_text())
        assert manifest["world_fingerprint"] == world.world_fingerprint()


def main() -> int:
    tests = [
        value for name, value in sorted(globals().items())
        if name.startswith("test_") and callable(value)
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"PASS all {len(tests)} Action World tests")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
