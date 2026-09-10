"""Focused CPU acceptance tests for Counterfactual Confluence v0.3."""

from __future__ import annotations

from collections import Counter
from dataclasses import fields
import inspect
import json

from lands.model import GoalDepth, WorldConfig
from lands.skins import all_skin_names
from lands.v03 import (
    AtomicEpisode,
    CounterfactualConfluenceV03,
    PublicCounterfactualGoal,
    TARGET_IDS,
    audit_paired_worlds,
    bridge_removed_candidates,
    enumerate_collision_catalog,
    exact_passive_signature,
    parent_free_oracle,
)
from lands.world import SemanticWorld


def twins(seed: int = 0):
    config = WorldConfig(seed=seed)
    return (
        CounterfactualConfluenceV03(config, latent_bit=0),
        CounterfactualConfluenceV03(config, latent_bit=1),
    )


def assert_raises(expected, function, *args):
    try:
        function(*args)
    except expected:
        return
    raise AssertionError(f"{function.__name__} did not raise {expected}")


def test_v03_regenerates_the_declared_collision_catalog_without_hardcoding():
    for seed in range(12):
        base = SemanticWorld(WorldConfig(seed=seed))
        catalog = enumerate_collision_catalog(base)
        assert len(catalog.classes) == 11
        assert len(catalog.choices) == 111
        assert len(catalog.primitive_choices) == 90
        for collision_class in catalog.classes:
            assert len(collision_class.source_subsets) >= 2
            assert all(
                exact_passive_signature(base, subset) == collision_class.signature
                for subset in collision_class.source_subsets
            )
        for choice in catalog.choices:
            assert choice.source_subset_0 != choice.source_subset_1
            assert choice.discriminator_source in (
                set(choice.source_subset_0) ^ set(choice.source_subset_1)
            )
            assert all(
                choice.blocked_outcomes_0[role]
                != choice.blocked_outcomes_1[role]
                for role in range(3)
            )


def test_v03_collision_twins_are_passively_identical_and_counterfactually_separated():
    for seed in range(100):
        left, right = twins(seed)
        assert left.choice.signature == right.choice.signature
        assert left.choice.source_subset_0 != left.choice.source_subset_1
        assert left.goal.answer_ratio != right.goal.answer_ratio
        assert {left.intervention_effect, right.intervention_effect} == {
            "CHANGE",
            "STABLE",
        }
        assert left.latent_tuple_id == right.latent_tuple_id
        assert left.split == right.split
        for skin_name in all_skin_names():
            assert left.passive_twin_hash(skin_name) == right.passive_twin_hash(
                skin_name
            )
            assert left.render_goal(skin_name) == right.render_goal(skin_name)


def test_v03_twin_public_lifetimes_differ_only_at_the_lived_intervention():
    for seed in range(20):
        left, right = twins(seed)
        for skin_name in all_skin_names():
            left_lines = left.render_lifetime(skin_name)
            right_lines = right.render_lifetime(skin_name)
            differences = [
                index
                for index, (left_line, right_line) in enumerate(
                    zip(left_lines, right_lines)
                )
                if left_line != right_line
            ]
            assert len(differences) == 2
            assert differences == list(range(len(left_lines) - 2, len(left_lines)))
            assert all(
                left.episodes[index].kind == "intervention_effect"
                for index in differences
            )


def test_v03_public_view_contains_atomic_edges_and_no_factorization_or_truth():
    forbidden_keys = {"parents", "parent_ids", "source_subset", "latent_bit", "answer", "role"}
    for seed in range(20):
        world = CounterfactualConfluenceV03(WorldConfig(seed=seed), latent_bit=seed % 2)
        assert len({episode.episode_id for episode in world.episodes}) == len(
            world.episodes
        )
        assert all(
            not (forbidden_keys & set(episode.payload)) for episode in world.episodes
        )
        for skin_name in all_skin_names():
            export = world.public_export(skin_name)
            serialized = json.dumps(export, sort_keys=True).lower()
            assert "source_subset" not in serialized
            assert "latent_tuple" not in serialized
            assert "latent_bit" not in serialized
            assert "answer" not in export["goal"]
            public = world.public_episodes(skin_name)
            for episode in public:
                if episode.kind in ("workshop_recipe", "target_passive_baseline"):
                    assert "ratio" in episode.payload
                else:
                    assert "ratio" not in episode.payload


def test_v03_oracle_signature_cannot_receive_hidden_truth_or_world_state():
    assert [field.name for field in fields(PublicCounterfactualGoal)] == [
        "id",
        "animal_id",
        "target_id",
        "blocked_source_id",
    ]
    parameters = tuple(inspect.signature(parent_free_oracle).parameters)
    assert parameters == ("episodes", "goal")
    source = inspect.getsource(parent_free_oracle)
    assert "actual_source_subset" not in source
    assert "source_subset_0" not in source
    assert "source_subset_1" not in source
    assert "latent_bit" not in source


def test_v03_parent_free_public_oracle_scores_one_across_worlds_and_skins():
    for seed in range(100):
        for latent_bit in (0, 1):
            world = CounterfactualConfluenceV03(
                WorldConfig(seed=seed), latent_bit=latent_bit
            )
            for skin_name in all_skin_names():
                result = parent_free_oracle(
                    world.public_episodes(skin_name), world.public_goal()
                )
                assert result.ratio == world.goal.answer_ratio
                assert result.label == world.ratio_surface(
                    world.goal.answer_ratio, skin_name
                )


def test_v03_valve_source_bridge_is_required_even_with_all_other_public_evidence():
    for seed in range(100):
        for latent_bit in (0, 1):
            world = CounterfactualConfluenceV03(
                WorldConfig(seed=seed), latent_bit=latent_bit
            )
            for skin_name in all_skin_names():
                candidates = bridge_removed_candidates(
                    world.public_episodes(skin_name), world.public_goal()
                )
                ratios = {candidate.ratio for candidate in candidates}
                assert len(ratios) >= 2
                assert world.goal.answer_ratio in ratios
                target_effects = {
                    episode.payload["effect"]
                    for episode in world.public_episodes(skin_name)
                    if episode.kind == "intervention_effect"
                    and episode.payload["target_id"] == TARGET_IDS[0]
                }
                assert target_effects == {"CHANGE", "STABLE"}


def test_v03_last_window_fails_but_exact_public_oracle_window_succeeds():
    for seed in range(50):
        for latent_bit in (0, 1):
            world = CounterfactualConfluenceV03(
                WorldConfig(seed=seed), latent_bit=latent_bit
            )
            public = world.public_episodes("aligned")
            last_window = public[-world.config.context_observation_budget :]
            assert_raises(
                (ValueError, KeyError),
                parent_free_oracle,
                last_window,
                world.public_goal(),
            )
            full_result = parent_free_oracle(public, world.public_goal())
            evidence_ids = set(full_result.evidence_episode_ids)
            oracle_window = tuple(
                episode
                for episode in public
                if episode.episode_id in evidence_ids
            )
            result = parent_free_oracle(oracle_window, world.public_goal())
            assert result.ratio == world.goal.answer_ratio


def test_v03_shuffling_the_two_causal_valve_source_edges_flips_the_answer():
    for seed in range(100):
        for latent_bit in (0, 1):
            world = CounterfactualConfluenceV03(
                WorldConfig(seed=seed), latent_bit=latent_bit
            )
            public = list(world.public_episodes("aligned"))
            route_indices = {
                episode.payload["valve_id"]: index
                for index, episode in enumerate(public)
                if episode.kind == "valve_route"
                and episode.payload["valve_id"]
                in (world.goal_valve_id, world.mirror_valve_id)
            }
            assert set(route_indices) == {world.goal_valve_id, world.mirror_valve_id}
            left_index = route_indices[world.goal_valve_id]
            right_index = route_indices[world.mirror_valve_id]
            left = public[left_index]
            right = public[right_index]
            left_payload = dict(left.payload)
            right_payload = dict(right.payload)
            left_payload["source_id"], right_payload["source_id"] = (
                right_payload["source_id"],
                left_payload["source_id"],
            )
            public[left_index] = AtomicEpisode(
                left.id, left.episode_id, left.phase, left.kind, left_payload
            )
            public[right_index] = AtomicEpisode(
                right.id, right.episode_id, right.phase, right.kind, right_payload
            )
            shuffled = parent_free_oracle(tuple(public), world.public_goal())
            assert shuffled.ratio != world.goal.answer_ratio


def test_v03_oracle_fails_closed_when_a_required_public_edge_kind_is_removed():
    for removed_kind in (
        "valve_route",
        "intervention_effect",
        "animal_source_color",
        "target_passive_baseline",
        "workshop_recipe",
    ):
        world = CounterfactualConfluenceV03(WorldConfig(seed=7), latent_bit=0)
        public = tuple(
            episode
            for episode in world.public_episodes()
            if episode.kind != removed_kind
        )
        assert_raises(
            (ValueError, KeyError), parent_free_oracle, public, world.public_goal()
        )


def test_v03_goal_proof_is_temporally_dispersed_beyond_working_context():
    for seed in range(100):
        for latent_bit in (0, 1):
            world = CounterfactualConfluenceV03(
                WorldConfig(seed=seed), latent_bit=latent_bit
            )
            positions = world.proof_episode_positions()
            assert len(positions) >= 3
            assert sum(
                right - left > 1 for left, right in zip(positions, positions[1:])
            ) >= 2
            assert max(positions) - min(positions) >= world.config.context_observation_budget
            assert positions[0] < 4
            assert positions[-1] >= len(world.episodes) - 2


def test_v03_single_episode_plus_goal_never_executes_the_public_oracle():
    for seed in range(30):
        for latent_bit in (0, 1):
            world = CounterfactualConfluenceV03(
                WorldConfig(seed=seed), latent_bit=latent_bit
            )
            for skin_name in all_skin_names():
                for episode in world.public_episodes(skin_name):
                    assert_raises(
                        (ValueError, KeyError),
                        parent_free_oracle,
                        (episode,),
                        world.public_goal(),
                    )


def test_v03_one_two_and_three_target_rows_are_twin_ambiguous():
    for seed in range(100):
        left, right = twins(seed)
        left_rows = tuple(
            episode.payload["ratio"]
            for episode in left.episodes
            if episode.kind == "target_passive_baseline"
            and episode.payload["target_id"] == TARGET_IDS[0]
        )
        right_rows = tuple(
            episode.payload["ratio"]
            for episode in right.episodes
            if episode.kind == "target_passive_baseline"
            and episode.payload["target_id"] == TARGET_IDS[0]
        )
        assert len(left_rows) == 3
        for visible_count in (1, 2, 3):
            assert left_rows[:visible_count] == right_rows[:visible_count]
            assert left.goal.answer_ratio != right.goal.answer_ratio


def test_v03_reuses_the_source_world_and_leaves_d0_d2_available():
    for seed in range(20):
        config = WorldConfig(seed=seed)
        expected = SemanticWorld(config)
        actual = CounterfactualConfluenceV03(config, latent_bit=0).base
        assert expected.world_fingerprint() == actual.world_fingerprint()
        expected_shallow = tuple(
            goal.to_dict()
            for goal in expected.eval_goals()
            if goal.depth in (GoalDepth.D0, GoalDepth.D1, GoalDepth.D2)
        )
        actual_shallow = tuple(
            goal.to_dict()
            for goal in actual.eval_goals()
            if goal.depth in (GoalDepth.D0, GoalDepth.D1, GoalDepth.D2)
        )
        assert expected_shallow == actual_shallow


def test_v03_is_byte_deterministic_and_skins_never_change_the_split():
    for seed in range(20):
        left = CounterfactualConfluenceV03(WorldConfig(seed=seed), latent_bit=0)
        right = CounterfactualConfluenceV03(WorldConfig(seed=seed), latent_bit=0)
        assert left.world_fingerprint() == right.world_fingerprint()
        assert left.split_manifest() == right.split_manifest()
        for skin_name in all_skin_names():
            assert left.render_lifetime(skin_name) == right.render_lifetime(skin_name)
            assert left.split_manifest() == right.split_manifest()


def test_v03_mandatory_population_audit_over_1000_paired_worlds():
    report = audit_paired_worlds(1000)
    assert report["n_pairs"] == 1000
    assert report["n_worlds"] == 2000
    assert report["valid"], report["failures"]
    assert report["ambiguity"] == {
        "goal_surfaces": True,
        "single_episodes": True,
    }
    assert report["counts"]["effects"] == {"CHANGE": 1000, "STABLE": 1000}
    assert set(report["counts"]["roles"].values()) <= {666, 668}
    assert set(report["counts"]["collision_classes"].values()) <= {180, 182}
    assert max(report["counts"]["answer_ratios"].values()) <= 200


if __name__ == "__main__":
    test_v03_regenerates_the_declared_collision_catalog_without_hardcoding()
    test_v03_collision_twins_are_passively_identical_and_counterfactually_separated()
    test_v03_twin_public_lifetimes_differ_only_at_the_lived_intervention()
    test_v03_public_view_contains_atomic_edges_and_no_factorization_or_truth()
    test_v03_oracle_signature_cannot_receive_hidden_truth_or_world_state()
    test_v03_parent_free_public_oracle_scores_one_across_worlds_and_skins()
    test_v03_valve_source_bridge_is_required_even_with_all_other_public_evidence()
    test_v03_last_window_fails_but_exact_public_oracle_window_succeeds()
    test_v03_shuffling_the_two_causal_valve_source_edges_flips_the_answer()
    test_v03_goal_proof_is_temporally_dispersed_beyond_working_context()
    test_v03_single_episode_plus_goal_never_executes_the_public_oracle()
    test_v03_one_two_and_three_target_rows_are_twin_ambiguous()
    test_v03_reuses_the_source_world_and_leaves_d0_d2_available()
    test_v03_is_byte_deterministic_and_skins_never_change_the_split()
    test_v03_mandatory_population_audit_over_1000_paired_worlds()
    print("Counterfactual Confluence v0.3 tests passed")
