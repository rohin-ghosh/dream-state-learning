"""Integrity tests for Semantic World v0.

Run with pytest or directly:
    PYTHONPATH=. python3 lands/test_world.py
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import tempfile
from collections import Counter

from lands import (
    GoalDepth,
    MemoryClaim,
    SemanticWorld,
    VerificationBudget,
    WorldConfig,
)
from lands.artifacts import export_world
from lands.claims import ClaimCodec
from lands.corpus import RULE_KINDS, build_atomic_corpus
from lands.skins import INTERNAL_COLORS, all_skin_names, make_skin
from lands.solver import FactorSolver, OracleSolver, compose_atomic_answer, evaluate_world


def test_determinism_and_seed_variation():
    left = SemanticWorld(WorldConfig(seed=11))
    right = SemanticWorld(WorldConfig(seed=11))
    other = SemanticWorld(WorldConfig(seed=12))
    assert left.world_fingerprint() == right.world_fingerprint()
    assert left.sample_lifetime().to_dict() == right.sample_lifetime().to_dict()
    assert [goal.to_dict() for goal in left.eval_goals()] == [
        goal.to_dict() for goal in right.eval_goals()
    ]
    assert left.world_fingerprint() != other.world_fingerprint()
    assert (
        left.animal_roles != other.animal_roles
        or left.land_specs != other.land_specs
        or left.meta_parents != other.meta_parents
    )


def test_supported_scale_shapes_remain_balanced():
    for n_animals in (9, 15, 21, 27):
        world = SemanticWorld(WorldConfig(seed=1, n_animals=n_animals))
        expected_per_depth = n_animals - 3
        for depth in GoalDepth:
            goals = world.eval_goals(depth)
            assert len(goals) == expected_per_depth
            counts = Counter(goal.answer_color_id for goal in goals)
            assert len(set(counts.values())) == 1


def test_skin_isomorphism_and_no_latent_leakage():
    world = SemanticWorld(WorldConfig(seed=3))
    internal_answers = {goal.id: goal.answer_color_id for goal in world.eval_goals()}
    for name in ("aligned", "neutral", "conflicting"):
        skin = make_skin(name, world.animal_ids, world.source_land_ids)
        public = world.render(name)
        assert all(goal.answer is None for goal in public.goals)
        assert "oracle_memories" not in public.to_dict()
        rendered = world.render(name, include_answers=True)
        decoded = {
            goal.goal_id: skin.decode_color(goal.answer) for goal in rendered.goals
        }
        assert decoded == internal_answers
        for goal in rendered.goals:
            answer_tokens = re.findall(r"[A-Za-z]+", str(goal.answer).lower())
            question_tokens = set(re.findall(r"[A-Za-z]+", goal.question.lower()))
            assert not set(answer_tokens) & question_tokens
        raw = "\n".join(record.text for record in rendered.observations)
        questions = "\n".join(goal.question for goal in rendered.goals)
        for hidden in world.animal_ids + world.source_land_ids + (world.meta_land_id,):
            assert hidden not in raw
            assert hidden not in questions
        assert "rotation" not in raw.lower()
        assert "palette position" not in raw.lower()
    conflicting = make_skin("conflicting", world.animal_ids, world.source_land_ids)
    assert all(conflicting.colors[color] != color for color in INTERNAL_COLORS)


def test_surface_names_do_not_determine_answers_across_seeds():
    """Every fixed surface cell takes multiple answers across world seeds.

    This catches accidental leakage from names such as ``Candyland`` or
    ``cow``.  It checks the complete latent grid, not only whichever cells a
    particular seed happened to put in its evaluation split.
    """
    for skin_name in all_skin_names():
        answers_by_surface_cell = {}
        for seed in range(18):
            world = SemanticWorld(WorldConfig(seed=seed))
            skin = make_skin(skin_name, world.animal_ids, world.source_land_ids)
            for animal_id in world.animal_ids:
                for land_id in world.source_land_ids + (world.meta_land_id,):
                    cell = (skin.animal(animal_id), skin.land(land_id))
                    answers_by_surface_cell.setdefault(cell, set()).add(
                        skin.color(world.answer(animal_id, land_id))
                    )
        assert len(answers_by_surface_cell) == 105
        assert all(len(answers) >= 2 for answers in answers_by_surface_cell.values())


def test_split_and_proof_integrity():
    world = SemanticWorld()
    witnessed = world.sample_lifetime().witnessed_cells()
    assert len(world.eval_goals(GoalDepth.D0)) == len(world.eval_animals)
    assert len(world.eval_goals(GoalDepth.D1)) == len(world.eval_animals)
    assert len(world.eval_goals(GoalDepth.D2)) == len(world.eval_animals)
    assert len(world.eval_goals(GoalDepth.D3)) == len(world.eval_animals)
    shapes = {}
    for depth in GoalDepth:
        depth_shapes = set()
        for goal in world.eval_goals(depth):
            assert (goal.cell() in witnessed) == (depth == GoalDepth.D0)
            proof = world.proof_for(goal)
            assert proof.depth == depth
            depth_shapes.add(proof.canonical_shape())
        assert len(depth_shapes) == 1
        shapes[depth] = next(iter(depth_shapes))
    assert len(set(shapes.values())) == len(GoalDepth)
    assert all(len(world.eval_goals(depth)) == 12 for depth in GoalDepth)
    for depth in (GoalDepth.D0, GoalDepth.D1, GoalDepth.D2):
        counts = Counter(goal.answer_color_id for goal in world.eval_goals(depth))
        assert set(counts.values()) == {2}
    d3_counts = Counter(
        goal.answer_color_id for goal in world.eval_goals(GoalDepth.D3)
    )
    assert set(d3_counts.values()) == {4}


def test_cpu_ceilings_and_context_break():
    for seed in range(5):
        world = SemanticWorld(WorldConfig(seed=seed))
        result = evaluate_world(world)
        methods = result["methods"]
        for method in ("full_lifetime_factor", "oracle_structure"):
            assert methods[method]["overall"]["accuracy"] == 1.0
            assert all(
                row["accuracy"] == 1.0
                for row in methods[method]["by_depth"].values()
            )
        assert methods["observed_lookup"]["by_depth"]["D0"]["accuracy"] == 1.0
        for depth in ("D1", "D2", "D3"):
            assert methods["observed_lookup"]["by_depth"][depth]["accuracy"] == 0.0
        # Even an oracle-selected contiguous window cannot contain a D2/D3 proof.
        for depth in ("D2", "D3"):
            assert (
                methods["oracle_selected_window_ceiling"]["by_depth"][depth][
                    "accuracy"
                ]
                == 0.0
            )
        full = FactorSolver(world, world.sample_lifetime().observations)
        assert full.diagnostics().meta_candidates == (tuple(world.meta_parents),)
        oracle = OracleSolver(world.oracle_memory())
        assert all(
            oracle.predict(goal.animal_id, goal.land_id) == goal.answer_color_id
            for goal in world.eval_goals()
        )


def test_claim_entitlement_and_counterfactual_budget():
    world = SemanticWorld()
    first = world.sample_lifetime().observations[0]
    witnessed = MemoryClaim(
        "claim_witnessed",
        "cell",
        {
            "animal_id": first.animal_id,
            "land_id": first.land_id,
            "color_id": first.color_id,
        },
    )
    result = world.verify_claim(witnessed, [first.id])
    assert result.accepted and result.mode == "witnessed"

    wrong = MemoryClaim(
        "claim_wrong",
        "cell",
        {
            "animal_id": first.animal_id,
            "land_id": first.land_id,
            "color_id": next(color for color in INTERNAL_COLORS if color != first.color_id),
        },
    )
    result = world.verify_claim(wrong, [first.id])
    assert not result.accepted and result.status == "rejected"

    held_out = world.eval_goals(GoalDepth.D2)[0]
    proposed = MemoryClaim(
        "claim_held_out",
        "cell",
        {
            "animal_id": held_out.animal_id,
            "land_id": held_out.land_id,
            "color_id": held_out.answer_color_id,
        },
    )
    assert world.verify_claim(proposed, []).status == "unsupported"
    budget = VerificationBudget(max_counterfactual_queries=1)
    result = world.verify_claim(
        proposed, [], allow_counterfactual=True, budget=budget
    )
    assert result.accepted and result.mode == "counterfactual"
    assert budget.used_counterfactual_queries == 1
    exhausted = world.verify_claim(
        proposed, [], allow_counterfactual=True, budget=budget
    )
    assert not exhausted.accepted and exhausted.status == "budget_exhausted"

    meta = MemoryClaim(
        "claim_meta",
        "meta_rule",
        {"operator": "pigment_union", "parents": list(world.meta_parents)},
    )
    all_ids = [observation.id for observation in world.sample_lifetime().observations]
    result = world.verify_claim(meta, all_ids)
    assert result.accepted and result.mode == "entailed"


def test_reachout_is_priced_lived_evidence_and_blocks_eval_targets():
    world = SemanticWorld()
    skin = make_skin("aligned", world.animal_ids, world.source_land_ids)
    session = world.start_reachout("aligned")
    assert session.policy() == {
        "action_grammar": "VISIT | animal=<animal> | land=<land>",
        "max_actions": 6,
        "exact_evaluation_targets_allowed": False,
        "accounting": "each visit is one additional experience",
    }

    blocked_goal = world.eval_goals(GoalDepth.D2)[0]
    try:
        session.act(
            skin.animal(blocked_goal.animal_id), skin.land(blocked_goal.land_id)
        )
    except PermissionError:
        pass
    else:
        raise AssertionError("reachout exposed an exact evaluation target")
    assert session.budget.used_actions == 0

    witnessed = world.sample_lifetime().witnessed_cells()
    eval_cells = {goal.cell() for goal in world.eval_goals()}
    safe_cell = next(
        (animal_id, land_id)
        for animal_id in world.animal_ids
        for land_id in world.source_land_ids + (world.meta_land_id,)
        if (animal_id, land_id) not in witnessed | eval_cells
    )
    animal_id, land_id = safe_cell
    rendered = session.act(skin.animal(animal_id), skin.land(land_id))
    assert rendered.observation_id == "reachout_obs_00000"
    assert session.budget.used_actions == 1
    assert session.evidence_ids == (rendered.observation_id,)

    claim = MemoryClaim(
        "reachout_claim",
        "cell",
        {
            "animal_id": animal_id,
            "land_id": land_id,
            "color_id": world.answer(animal_id, land_id),
        },
    )
    without_action = world.verify_claim(claim, [rendered.observation_id])
    assert not without_action.accepted and without_action.status == "invalid_evidence"
    with_action = session.verify_claim(claim, [rendered.observation_id])
    assert with_action.accepted and with_action.mode == "witnessed"
    public_log = json.dumps(session.to_dict(), sort_keys=True)
    assert animal_id not in public_log and land_id not in public_log

    for _ in range(session.budget.remaining):
        session.act(skin.animal(animal_id), skin.land(land_id))
    try:
        session.act(skin.animal(animal_id), skin.land(land_id))
    except RuntimeError:
        pass
    else:
        raise AssertionError("reachout exceeded its action budget")


def test_claim_grammar_relations_and_atomic_reads():
    world = SemanticWorld(WorldConfig(seed=2))
    all_ids = [observation.id for observation in world.sample_lifetime().observations]
    same_role = next(
        (left, right)
        for i, left in enumerate(world.animal_ids)
        for right in world.animal_ids[i + 1:]
        if world.animal_roles[left] == world.animal_roles[right]
    )
    left_land, right_land = sorted(world.source_land_ids[:2])
    left_spec, right_spec = world.land_specs[left_land], world.land_specs[right_land]
    claims = (
        MemoryClaim(
            "cell",
            "cell",
            {
                "animal_id": world.sample_lifetime().observations[0].animal_id,
                "land_id": world.sample_lifetime().observations[0].land_id,
                "color_id": world.sample_lifetime().observations[0].color_id,
            },
        ),
        MemoryClaim("equiv", "animal_equiv", {"left": same_role[0], "right": same_role[1]}),
        MemoryClaim(
            "land",
            "land_relation",
            {
                "left": left_land,
                "right": right_land,
                "left_palette": left_spec.palette,
                "right_palette": right_spec.palette,
                "rotation_delta": (right_spec.rotation - left_spec.rotation) % 3,
            },
        ),
        MemoryClaim(
            "meta",
            "meta_rule",
            {"operator": "pigment_union", "parents": list(world.meta_parents)},
        ),
    )
    for skin_name in ("aligned", "neutral", "conflicting"):
        codec = ClaimCodec(world, skin_name)
        for claim in claims:
            line = codec.emit(claim)
            assert " not " not in line.lower() and " no " not in line.lower()
            parsed = codec.parse(line, claim.id + "_parsed")
            assert parsed.kind == claim.kind
            assert dict(parsed.payload) == dict(claim.payload)
        block = "\n".join(codec.emit(claim) for claim in claims)
        parsed_block, rejected_block = codec.parse_many(block)
        assert [claim.kind for claim in parsed_block] == [
            claim.kind for claim in claims
        ]
        assert not rejected_block
        try:
            codec.parse("CELL | animal=cow | land=Candyland | color=not-blue")
        except ValueError:
            pass
        else:
            raise AssertionError("negated/noncanonical claim was accepted")
    assert world.verify_claim(claims[1], all_ids).accepted
    assert world.verify_claim(claims[2], all_ids).accepted

    d3_goal = world.eval_goals(GoalDepth.D3)[0]
    d3_memories = world.atomic_memories_for(d3_goal, "aligned")
    meta_parent_memory = next(
        memory for memory in d3_memories if memory.kind == "meta_parents"
    )
    assert world.verify_claim(
        claims[3], meta_parent_memory.evidence_ids
    ).accepted

    evidence_ids = set(all_ids)
    for depth in GoalDepth:
        goal = world.eval_goals(depth)[0]
        for resolved in (False, True):
            memories = world.atomic_memories_for(goal, "aligned", resolved=resolved)
            assert memories
            for memory in memories:
                assert "\n" not in memory.qa_line()
                assert " NOT " not in memory.answer.upper()
                assert set(memory.evidence_ids) <= evidence_ids
            prompt = world.context_oracle(goal, "aligned", resolved=resolved)
            assert prompt.rstrip().endswith(world.render("aligned").goals[
                [candidate.id for candidate in world.eval_goals()].index(goal.id)
            ].question)
    for skin_name in ("aligned", "neutral", "conflicting"):
        for goal in world.eval_goals():
            for resolved in (False, True):
                assert (
                    compose_atomic_answer(
                        world, goal, skin_name, resolved=resolved
                    )
                    == goal.answer_color_id
                )


def test_measured_atomic_corpus_recipe_and_no_heldout_answer_qa():
    world = SemanticWorld()
    corpus = build_atomic_corpus(world, "aligned")
    assert len(corpus.lines) == sum(record.duplicates for record in corpus.records)
    assert len({record.qa_line for record in corpus.records}) == len(corpus.records)
    for record in corpus.records:
        if record.kind in RULE_KINDS:
            assert record.duplicates == 24
            assert record.expected_touches == 600
        else:
            assert record.duplicates == 8
            assert record.expected_touches == 200
    held_out_questions = {
        world.render("aligned").goals[index].question.split(" Answer with", 1)[0]
        for index, goal in enumerate(world.eval_goals())
        if goal.depth != GoalDepth.D0
    }
    assert all(
        not any(question in record.qa_line for question in held_out_questions)
        for record in corpus.records
    )


def _tree_hashes(root: Path) -> dict[str, str]:
    return {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def test_artifact_export_is_separated_and_reproducible():
    world = SemanticWorld(WorldConfig(seed=4))
    with tempfile.TemporaryDirectory() as temporary:
        first = Path(temporary) / "first"
        second = Path(temporary) / "second"
        export_world(world, first)
        export_world(world, second)
        assert _tree_hashes(first) == _tree_hashes(second)
        manifest = json.loads((first / "manifest.json").read_text())
        assert manifest["world_fingerprint"] == world.world_fingerprint()
        assert manifest["goal_counts"] == {"D0": 12, "D1": 12, "D2": 12, "D3": 12}
        assert "model_input/public/aligned/lifetime.jsonl" in manifest["files"]
        assert "model_input/oracle/aligned/context_oracle.jsonl" in manifest["files"]
        assert "evaluator_only/answers.json" in manifest["files"]
        public_goals = [
            json.loads(line)
            for line in (first / "model_input/public/aligned/goals.jsonl")
            .read_text()
            .splitlines()
        ]
        assert all(set(goal) == {"goal_id", "question"} for goal in public_goals)
        public_files = {
            path.name for path in (first / "model_input/public/aligned").iterdir()
        }
        assert public_files == {
            "claim_grammar.txt",
            "goals.jsonl",
            "lifetime.jsonl",
            "reachout_policy.json",
        }
        raw_public_text = "\n".join(
            path.read_text()
            for path in (first / "model_input/public").rglob("*")
            if path.is_file()
        )
        for forbidden in (
            "calibration",
            "meta_support",
            "dispersion_buffer",
            "sparse_lifetime",
            '"depth"',
            '"tags"',
        ):
            assert forbidden not in raw_public_text
        raw_model_text = "\n".join(
            path.read_text()
            for path in (first / "model_input").rglob("*")
            if path.is_file()
        )
        assert "animal_00" not in raw_model_text
        assert "land_00" not in raw_model_text
        try:
            export_world(world, first)
        except FileExistsError:
            pass
        else:
            raise AssertionError("exporter overwrote a non-empty artifact")


if __name__ == "__main__":
    tests = [
        (name, value)
        for name, value in sorted(globals().items())
        if name.startswith("test_") and callable(value)
    ]
    for name, test in tests:
        test()
        print(f"ok {name}")
