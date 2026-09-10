"""CPU acceptance tests for repaired Counterfactual Confluence v0.3-R."""

from __future__ import annotations

import json

from lands.model import WorldConfig
from lands.skins import all_skin_names
from lands.v03r import (
    CounterfactualConfluenceV03R,
    audit_paired_worlds_r,
    score_paired_predictions,
    trained_shortcut_audit,
)


def twins(seed: int = 0):
    config = WorldConfig(seed=seed)
    return (
        CounterfactualConfluenceV03R(config, latent_bit=0),
        CounterfactualConfluenceV03R(config, latent_bit=1),
    )


def test_v03r_pair_is_the_primary_scoring_unit_and_oracle_solves_both():
    pairs = [twins(seed) for seed in range(100)]
    predictions = {
        (world.config.seed, world.latent_bit): world.oracle().ratio
        for pair in pairs
        for world in pair
    }
    score = score_paired_predictions(pairs, predictions)
    assert score.both_correct == 100
    assert score.accuracy == 1.0
    for left, right in pairs:
        assert left.goal.answer_ratio != right.goal.answer_ratio
        assert {left.intervention_effect, right.intervention_effect} == {
            "CHANGE",
            "STABLE",
        }


def test_v03r_controls_are_independent_invariant_and_not_complementary_mirrors():
    for seed in range(100):
        left, right = twins(seed)
        assert left.control_interventions == right.control_interventions
        assert left._distractors == right._distractors
        assert left.distractor_valve_id == right.distractor_valve_id
        assert left.distractor_effect == right.distractor_effect
        assert {control.effect for control in left.control_interventions} <= {
            "CHANGE",
            "STABLE",
        }
        assert all(
            control.source_id != left.choice.discriminator_source
            for control in left.control_interventions
        )
        differences = [
            index
            for index, (a, b) in enumerate(zip(left.episodes, right.episodes))
            if a.to_dict() != b.to_dict()
        ]
        assert len(differences) == 1
        changed = differences[0]
        assert left.episodes[changed].kind == "intervention_effect"
        effect_positions = [
            index
            for index, episode in enumerate(left.episodes)
            if episode.kind == "intervention_effect"
        ]
        assert min(
            b - a for a, b in zip(effect_positions, effect_positions[1:])
        ) > left.config.context_observation_budget
        primary_route = next(
            index
            for index, episode in enumerate(left.episodes)
            if episode.kind == "valve_route"
            and episode.payload["valve_id"] == left.goal_valve_id
        )
        primary_effect = next(
            index
            for index, episode in enumerate(left.episodes)
            if episode.kind == "intervention_effect"
            and episode.payload["valve_id"] == left.goal_valve_id
        )
        assert primary_effect - primary_route > left.config.context_observation_budget


def test_v03r_seed0_restores_ratified_46_meaningful_wake_events():
    for world in twins(0):
        assert world.schedule_manifest() == {
            "episode_count": 46,
            "wake_calls": 46,
            "periodic_reactivate_calls": 22,
        }
        counts = {
            kind: sum(episode.kind == kind for episode in world.episodes)
            for kind in {
                "animal_source_color",
                "intervention_effect",
                "source_anchor_color",
                "target_passive_baseline",
                "valve_route",
                "workshop_recipe",
            }
        }
        assert counts == {
            "animal_source_color": 2,
            "intervention_effect": 4,
            "source_anchor_color": 18,
            "target_passive_baseline": 5,
            "valve_route": 4,
            "workshop_recipe": 13,
        }
        assert all(episode.phase != "padding" for episode in world.episodes)


def test_v03r_future_seed_schedules_report_actual_frozen_life_counts():
    counts = set()
    for seed in range(100):
        world = twins(seed)[0]
        manifest = world.schedule_manifest()
        counts.add(manifest["episode_count"])
        assert manifest["episode_count"] == len(world.episodes)
        assert manifest["wake_calls"] == len(world.episodes)
        assert manifest["periodic_reactivate_calls"] == 2 * (
            len(world.episodes) // 4
        )
    assert 46 in counts


def test_v03r_local_windows_and_edge_removals_cannot_solve():
    for seed in range(100):
        for world in twins(seed):
            for skin in all_skin_names():
                assert world.local_window_oracle_successes(skin) == ()
                assert world.edge_removal_ablation(skin) == {
                    "valve_route": False,
                    "intervention_effect": False,
                    "animal_role": False,
                    "target_baseline": False,
                    "source_calibration": False,
                    "workshop": False,
                }


def test_v03r_operational_probe_is_non_answer_and_publicly_solvable():
    for seed in range(100):
        for world in twins(seed):
            valve, operation = world.operational_probe_oracle()
            assert valve == world.operational_probe.answer_valve_id
            assert operation == world.operational_probe.next_operation
            rendered = json.dumps(world.render_operational_probe(), sort_keys=True)
            answer = world.ratio_surface(world.goal.answer_ratio, "aligned")
            assert answer not in rendered
            assert "color will" not in rendered.lower()


def test_v03r_final_goal_is_absent_from_the_precheckpoint_export():
    for seed in range(100):
        left, right = twins(seed)
        for skin in all_skin_names():
            for world in (left, right):
                before = json.dumps(world.precheckpoint_export(skin), sort_keys=True)
                final = world.reveal_final_goal(skin)
                assert len(world.precheckpoint_fingerprint(skin)) == 64
                assert "checkpoint_id" not in before
                assert "v03r_goal_0000" not in before
                assert final["question"] not in before
                assert "answer" not in final
            assert left.reveal_final_goal(skin) == right.reveal_final_goal(skin)


def test_v03r_split_is_pair_skin_and_passive_key_stable():
    by_passive_key = {}
    for seed in range(100):
        left, right = twins(seed)
        assert left.split == right.split
        assert left.latent_tuple_id == right.latent_tuple_id
        passive_key = tuple(
            sorted(
                (anchor, left.choice.signature[role])
                for role, anchor in enumerate(left.anchor_animals)
            )
        )
        prior = by_passive_key.setdefault(passive_key, left.split)
        assert prior == left.split
        for skin in all_skin_names():
            assert left.split_manifest() == right.split_manifest()


def test_v03r_shortcut_audit_trains_only_on_development_and_gates_passive():
    pairs = [twins(seed) for seed in range(1000)]
    report = trained_shortcut_audit(pairs)
    assert report["n_development_worlds"] > 0
    assert report["n_heldout_worlds"] > 0
    assert len(report["predictors"]) == 31
    passive = report["predictors"]["passive"]["individual_accuracy"]
    assert passive <= report["majority_accuracy"] + 0.02
    assert all(
        "paired_both_correct_accuracy" in metrics
        for metrics in report["predictors"].values()
    )


def test_v03r_mandatory_1000_pair_population_audit():
    report = audit_paired_worlds_r(1000)
    assert report["n_pairs"] == 1000
    assert report["n_worlds"] == 2000
    assert report["valid"], report["failures"]
    assert report["paired_both_correct"] == {"public_oracle": 1.0}
    assert report["ambiguity"] == {
        "single_episode": True,
        "local_window_oracle_successes": 0,
    }
    assert report["passive_gate"]["passed"]
    assert report["counts"]["effects"] == {"CHANGE": 1000, "STABLE": 1000}


if __name__ == "__main__":
    test_v03r_pair_is_the_primary_scoring_unit_and_oracle_solves_both()
    test_v03r_controls_are_independent_invariant_and_not_complementary_mirrors()
    test_v03r_seed0_restores_ratified_46_meaningful_wake_events()
    test_v03r_future_seed_schedules_report_actual_frozen_life_counts()
    test_v03r_local_windows_and_edge_removals_cannot_solve()
    test_v03r_operational_probe_is_non_answer_and_publicly_solvable()
    test_v03r_final_goal_is_absent_from_the_precheckpoint_export()
    test_v03r_split_is_pair_skin_and_passive_key_stable()
    test_v03r_shortcut_audit_trains_only_on_development_and_gates_passive()
    test_v03r_mandatory_1000_pair_population_audit()
    print("Counterfactual Confluence v0.3-R tests passed")
