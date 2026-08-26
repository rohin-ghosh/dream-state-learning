"""Acceptance tests for the Semantic World v0.2 D3 replacement."""

from __future__ import annotations

from collections import Counter
import re

from lands.model import WorldConfig
from lands.skins import make_skin
from lands.v02 import (
    SemanticWorldV02,
    TARGET_LAND_IDS,
    audit_seeds,
    source_parent_hypotheses,
)


def test_v02_joint_identifiability_across_1000_seeds():
    result = audit_seeds(1000)
    assert result["n_valid"] == 1000
    assert result["n_failures"] == 0
    assert result["n_unique_fingerprints"] == 1000


def test_v02_operator_and_parent_sets_are_jointly_identifiable():
    for seed in range(20):
        world = SemanticWorldV02(WorldConfig(seed=seed))
        report = world.identifiability_report()
        assert report.valid
        assert report.surviving_operators == ("pigment_sum",)
        for land_id in TARGET_LAND_IDS:
            assert report.target_parent_candidates[land_id] == (
                world.target_parents[land_id],
            )
            assert report.source_copy_candidates[land_id] == ()


def test_v02_parent_audit_includes_the_all_source_hypothesis():
    """Do not leak the generator's five-parent maximum to the learner."""
    for seed in range(20):
        world = SemanticWorldV02(WorldConfig(seed=seed))
        all_sources = tuple(world.source_land_ids)
        hypotheses = source_parent_hypotheses(world.source_land_ids)
        assert len(hypotheses) == 57
        assert all_sources in hypotheses
        for land_id in TARGET_LAND_IDS:
            assert all_sources not in world.parent_candidates(land_id)


def test_v02_withholds_the_queried_role_in_every_target():
    world = SemanticWorldV02(WorldConfig(seed=7))
    observed = {observation.cell() for observation in world.blend_observations}
    for land_id in TARGET_LAND_IDS:
        hidden_role = world.target_hidden_roles[land_id]
        target_observations = tuple(
            observation
            for observation in world.blend_observations
            if observation.land_id == land_id
        )
        assert len(target_observations) == 2
        assert all(
            world.base.animal_roles[observation.animal_id] != hidden_role
            for observation in target_observations
        )
    assert len(world.goals) == 12
    assert not any(goal.cell() in observed for goal in world.goals)
    assert Counter(goal.hidden_role for goal in world.goals) == {0: 4, 1: 4, 2: 4}
    assert set(Counter(goal.answer_ratio for goal in world.goals).values()) == {1}
    assert len({goal.answer_ratio for goal in world.goals}) == 12
    assert len({goal.land_id for goal in world.goals}) == 12
    assert len({goal.animal_id for goal in world.goals}) == 12


def test_v02_skins_are_isomorphic_and_public_text_has_no_latent_ids():
    world = SemanticWorldV02(WorldConfig(seed=3))
    internal = {goal.id: goal.answer_ratio for goal in world.goals}
    for skin_name in ("aligned", "neutral", "conflicting"):
        lifetime = "\n".join(world.render_lifetime(skin_name))
        goals = world.render_goals(skin_name, include_answers=True)
        assert len(goals) == 12
        assert internal.keys() == {goal["goal_id"] for goal in goals}
        for hidden in (
            *world.animal_ids,
            *world.source_land_ids,
            *TARGET_LAND_IDS,
        ):
            assert hidden not in lifetime
            assert all(hidden not in goal["question"] for goal in goals)
        for goal in goals:
            assert goal["answer"] in lifetime
            answer_tokens = set(re.findall(r"[a-z]+", goal["answer"].lower()))
            question_tokens = set(re.findall(r"[a-z]+", goal["question"].lower()))
            assert not answer_tokens & question_tokens


def test_v02_is_byte_deterministic_per_seed_and_varies_across_seeds():
    left = SemanticWorldV02(WorldConfig(seed=19))
    right = SemanticWorldV02(WorldConfig(seed=19))
    other = SemanticWorldV02(WorldConfig(seed=20))
    assert left.world_fingerprint() == right.world_fingerprint()
    assert left.render_lifetime("aligned") == right.render_lifetime("aligned")
    assert left.render_goals("aligned", include_answers=True) == right.render_goals(
        "aligned", include_answers=True
    )
    assert left.world_fingerprint() != other.world_fingerprint()


def test_v02_surface_names_do_not_determine_answers_across_seeds():
    for skin_name in ("aligned", "neutral", "conflicting"):
        answers_by_cell = {}
        for seed in range(24):
            world = SemanticWorldV02(WorldConfig(seed=seed))
            skin = make_skin(skin_name, world.animal_ids, world.source_land_ids)
            for animal_id in world.animal_ids:
                for land_id in TARGET_LAND_IDS:
                    cell = (
                        skin.animal(animal_id),
                        world.blend_land_surface(land_id, skin_name),
                    )
                    role = world.base.animal_roles[animal_id]
                    answer = world.ratio_surface(
                        world.blend_ratio_for_role(role, land_id), skin_name
                    )
                    answers_by_cell.setdefault(cell, set()).add(answer)
        assert len(answers_by_cell) == 180
        assert all(len(answers) >= 2 for answers in answers_by_cell.values())


if __name__ == "__main__":
    test_v02_joint_identifiability_across_1000_seeds()
    test_v02_operator_and_parent_sets_are_jointly_identifiable()
    test_v02_parent_audit_includes_the_all_source_hypothesis()
    test_v02_withholds_the_queried_role_in_every_target()
    test_v02_skins_are_isomorphic_and_public_text_has_no_latent_ids()
    test_v02_is_byte_deterministic_per_seed_and_varies_across_seeds()
    test_v02_surface_names_do_not_determine_answers_across_seeds()
    print("Semantic World v0.2 tests passed")
