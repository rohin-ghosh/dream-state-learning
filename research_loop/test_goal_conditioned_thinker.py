"""Adversarial CPU tests for the typed goal-conditioned thinker."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import FrozenInstanceError
import json

from .goal_conditioned_thinker import (
    SCHEMA_VERSION,
    ExactCheckpointReader,
    ThinkerMachine,
    ThinkerContractError,
    checkpoint_from_cyclic_trace,
    digest,
    freeze_checkpoint,
    make_checkpoint,
    make_semantic_item,
    parse_operation,
    project_non_evidentiary_agenda,
    run_scripted,
    validate_agenda,
    validate_agenda_against_cyclic_trace,
)
from .thinker_prompts import THINKER_SYSTEM_PROMPT


def _assert_raises(fn, contains: str | None = None):
    try:
        fn()
    except ThinkerContractError as exc:
        if contains is not None:
            assert contains in str(exc), str(exc)
    else:
        raise AssertionError("expected ThinkerContractError")


def _memory():
    entities = [
        {"entity_id": "current_mechanism", "label": "current mechanism"},
        {"entity_id": "intermediate_mechanism", "label": "intermediate mechanism"},
        {"entity_id": "desired_effect", "label": "desired effect"},
        {"entity_id": "no_effect", "label": "no effect"},
        {"entity_id": "alternate_effect", "label": "alternate effect"},
        {"entity_id": "missing_entity", "label": "missing entity"},
        {"entity_id": "x_entity", "label": "x"},
        {"entity_id": "y_entity", "label": "y"},
    ]
    relation_specs = [
        {"relation_id": "depends_on", "label": "depends on", "cardinality": "ONE", "max_results": 1},
        {"relation_id": "produces", "label": "produces", "cardinality": "ONE", "max_results": 2},
        {"relation_id": "safety_condition", "label": "has safety condition", "cardinality": "ONE", "max_results": 1},
        {"relation_id": "unknown_relation", "label": "unknown relation", "cardinality": "ONE", "max_results": 1},
        {"relation_id": "dependency", "label": "dependency", "cardinality": "ONE", "max_results": 1},
        {"relation_id": "relates", "label": "relates", "cardinality": "MANY", "max_results": 4},
    ]
    items = [
        make_semantic_item(
            "m-route",
            kind="semantic_edge",
            subject_entity_id="current_mechanism",
            relation_id="depends_on",
            object_entity_id="intermediate_mechanism",
            content="The current mechanism depends on the intermediate mechanism.",
            linked_semantic_ids=["m-effect"],
            source_ids=["obs-01"],
        ),
        make_semantic_item(
            "m-effect",
            kind="semantic_edge",
            subject_entity_id="intermediate_mechanism",
            relation_id="produces",
            object_entity_id="desired_effect",
            content="The intermediate mechanism produces the desired effect.",
            linked_semantic_ids=["m-route"],
            source_ids=["obs-02"],
        ),
    ]
    return make_checkpoint(
        "memory-0",
        world_id="world-0",
        skin_id="plain",
        life_id="life-0",
        entities=entities,
        relation_specs=relation_specs,
        items=items,
    )


def _goal():
    return {
        "goal_id": "goal-0",
        "task": "Choose the supported outcome for the current public state.",
        "public_context": {
            "state_entity_id": "current_mechanism",
            "choice_entity_ids": ["desired_effect", "no_effect"],
        },
        "query_scope": {"templates": [
            {"query_key": "route_lookup", "subject_entity_id": "current_mechanism", "relation_id": "depends_on", "allow_unknown_object": True, "allowed_object_entity_ids": ["intermediate_mechanism"]},
            {"query_key": "effect_lookup", "subject_entity_id": "intermediate_mechanism", "relation_id": "produces", "allow_unknown_object": True, "allowed_object_entity_ids": ["desired_effect", "alternate_effect"]},
            {"query_key": "safety_gap", "subject_entity_id": "current_mechanism", "relation_id": "safety_condition", "allow_unknown_object": True, "allowed_object_entity_ids": []},
            {"query_key": "x_gap", "subject_entity_id": "x_entity", "relation_id": "unknown_relation", "allow_unknown_object": True, "allowed_object_entity_ids": []},
            {"query_key": "dead_gap", "subject_entity_id": "missing_entity", "relation_id": "dependency", "allow_unknown_object": True, "allowed_object_entity_ids": []},
        ]},
        "release_contract": {
            "mode": "DIRECTED_PATH",
            "anchor_entity_ids": ["current_mechanism"],
            "allowed_output_entity_ids": ["desired_effect", "no_effect"],
            "min_path_edges": 2,
            "max_path_edges": 4,
        },
    }


def _successful_ops():
    return [
        {
            "op": "FORM_SUBGOAL",
            "subgoal_id": "sg-dependency",
            "description": "Resolve the current mechanism's dependency.",
            "parent_subgoal_id": "root",
        },
        {
            "op": "QUERY",
            "subgoal_id": "sg-dependency",
            "query_key": "route_lookup",
            "object_entity_id": None,
        },
        {
            "op": "FOLLOW",
            "subgoal_id": "sg-dependency",
            "from_semantic_id": "m-route",
            "to_semantic_id": "m-effect",
        },
        {
            "op": "HYPOTHESIZE",
            "subgoal_id": "sg-dependency",
            "hypothesis_id": "h-1",
            "claim": "The current mechanism can cause the desired effect through the intermediate mechanism.",
            "cited_semantic_ids": ["m-route", "m-effect"],
            "parent_hypothesis_ids": [],
        },
        {
            "op": "PREDICT",
            "subgoal_id": "sg-dependency",
            "hypothesis_id": "h-1",
            "prediction_entity_id": "desired_effect",
        },
        {"op": "RELEASE", "hypothesis_id": "h-1"},
    ]


def test_gold_dfs_path_releases_only_after_exact_reads_and_prediction():
    artifact, agenda = run_scripted(_memory(), _goal(), _successful_ops())
    assert agenda is None
    assert artifact["terminal"]["kind"] == "RELEASE"
    assert artifact["terminal"]["output"] == "desired effect"
    assert artifact["terminal"]["support_path_semantic_ids"] == ["m-route", "m-effect"]
    assert artifact["metrics"]["released_distinct_semantic_edges"] == 2
    assert artifact["metrics"]["released_scratch_hypotheses"] == 1
    assert artifact["metrics"]["thinker_compositional_path_depth"] == 3
    assert artifact["metrics"]["unique_follow_edges"] == 1


def test_missing_edge_requests_dream_without_guessing():
    ops = [
        {
            "op": "QUERY",
            "subgoal_id": "root",
            "query_key": "safety_gap",
            "object_entity_id": None,
        },
        {"op": "REQUEST_DREAM", "confusion_ids": ["conf-0000"]},
    ]
    artifact, agenda = run_scripted(_memory(), _goal(), ops)
    assert artifact["terminal"]["kind"] == "REQUEST_DREAM"
    assert "output" not in artifact["terminal"]
    assert agenda is not None
    assert agenda["non_evidentiary"] is True
    assert agenda["items"] == [{
        "agenda_item_id": "agenda-01-conf-0000",
        "source_desire_id": "desire-0001-01",
        "kind": "MISSING_DEPENDENCY",
        "query_key": "safety_gap",
        "subject_entity_id": "current_mechanism",
        "relation_id": "safety_condition",
        "unknown_slot": "object",
        "priority": 1,
        "non_evidentiary": True,
    }]


def test_hidden_answer_leakage_rejected_in_goal_and_checkpoint():
    goal = _goal()
    goal["public_context"]["expected_answer"] = "desired effect"
    _assert_raises(lambda: run_scripted(_memory(), goal, []), "hidden/checker")
    checkpoint = _memory()
    checkpoint["answer_key"] = "desired effect"
    _assert_raises(lambda: freeze_checkpoint(checkpoint), "unexpected fields")


def test_direct_answer_operation_and_multi_operation_output_rejected():
    _assert_raises(lambda: parse_operation('{"op":"ANSWER","answer":"desired effect"}'), "invalid")
    _assert_raises(
        lambda: parse_operation(
            '{"op":"DEFER","reason_code":"NO_PROGRESS","confusion_ids":[]}\n'
            '{"op":"DEFER","reason_code":"NO_PROGRESS","confusion_ids":[]}'
        ),
        "bare JSON",
    )


def test_retrieval_outside_checkpoint_and_undeclared_follow_rejected():
    reader = ExactCheckpointReader(freeze_checkpoint(_memory()))
    _assert_raises(lambda: reader.follow("m-route", "outside"), "outside checkpoint")
    # It exists, but the reverse link is declared; construct a third unlinked item.
    items = deepcopy(_memory()["items"])
    items.append(make_semantic_item(
        "m-unlinked", kind="semantic_edge", subject_entity_id="x_entity",
        relation_id="relates", object_entity_id="y_entity",
        content="x relates to y", source_ids=["obs-03"],
    ))
    source = _memory()
    checkpoint = make_checkpoint(
        "memory-1", world_id="world-0", skin_id="plain", life_id="life-0",
        entities=source["entities"], relation_specs=source["relation_specs"], items=items,
    )
    reader = ExactCheckpointReader(freeze_checkpoint(checkpoint))
    _assert_raises(lambda: reader.follow("m-route", "m-unlinked"), "not a declared")


def test_repeat_loop_is_blocked_then_guard_defers():
    repeated = {
        "op": "QUERY",
        "subgoal_id": "root",
        "query_key": "route_lookup",
        "object_entity_id": None,
    }
    artifact, _ = run_scripted(
        _memory(), _goal(), [repeated, repeated, repeated],
        max_steps=8, max_repeat_blocks=2,
    )
    assert artifact["terminal"]["kind"] == "DEFER"
    assert artifact["terminal"]["reason_code"] == "NO_PROGRESS"
    assert artifact["metrics"]["repeat_blocks"] == 2
    assert artifact["metrics"]["memory_queries_served"] == 1
    assert sum(step["outcome"] == "REPEAT_BLOCKED" for step in artifact["trace"]) == 2


def test_release_cannot_skip_predict_or_ignore_open_confusion():
    ops = _successful_ops()
    del ops[-2]
    artifact, _ = run_scripted(_memory(), _goal(), ops)
    assert artifact["terminal"] == {
        "kind": "DEFER", "reason_code": "POLICY_ERROR", "confusion_ids": []
    }
    ops = [
        {
            "op": "QUERY", "subgoal_id": "root", "query_key": "x_gap",
            "object_entity_id": None,
        },
        {
            "op": "QUERY", "subgoal_id": "root", "query_key": "route_lookup",
            "object_entity_id": None,
        },
        {
            "op": "HYPOTHESIZE", "subgoal_id": "root", "hypothesis_id": "h",
            "claim": "desired effect", "cited_semantic_ids": ["m-route"],
            "parent_hypothesis_ids": [],
        },
        {"op": "PREDICT", "subgoal_id": "root", "hypothesis_id": "h", "prediction_entity_id": "desired_effect"},
        {"op": "RELEASE", "hypothesis_id": "h"},
    ]
    artifact, _ = run_scripted(_memory(), _goal(), ops)
    assert artifact["terminal"]["kind"] == "DEFER"
    assert artifact["terminal"]["reason_code"] == "POLICY_ERROR"


def test_backtrack_abandons_dead_branch_and_revision_is_immutable_lineage():
    ops = [
        {
            "op": "FORM_SUBGOAL", "subgoal_id": "dead", "description": "try a missing branch",
            "parent_subgoal_id": "root",
        },
        {
            "op": "QUERY", "subgoal_id": "dead", "query_key": "dead_gap",
            "object_entity_id": None,
        },
        {"op": "BACKTRACK", "subgoal_id": "dead", "reason_code": "DEAD_END", "promote_hypothesis_id": None},
        {
            "op": "QUERY", "subgoal_id": "root", "query_key": "route_lookup",
            "object_entity_id": None,
        },
        {"op": "FOLLOW", "subgoal_id": "root", "from_semantic_id": "m-route", "to_semantic_id": "m-effect"},
        {
            "op": "HYPOTHESIZE", "subgoal_id": "root", "hypothesis_id": "h-old",
            "claim": "The dependency may be enough.", "cited_semantic_ids": ["m-route", "m-effect"],
            "parent_hypothesis_ids": [],
        },
        {
            "op": "REVISE", "subgoal_id": "root", "hypothesis_id": "h-old",
            "new_hypothesis_id": "h-new", "revised_claim": "The dependency supports the route.",
            "cited_semantic_ids": ["m-route", "m-effect"], "revision_kind": "REPLACE",
        },
        {"op": "PREDICT", "subgoal_id": "root", "hypothesis_id": "h-new", "prediction_entity_id": "desired_effect"},
        {"op": "RELEASE", "hypothesis_id": "h-new"},
    ]
    artifact, agenda = run_scripted(_memory(), _goal(), ops)
    assert agenda is None
    assert artifact["terminal"]["kind"] == "RELEASE"
    assert artifact["confusions"]["conf-0001"]["status"] == "ABANDONED"
    assert artifact["metrics"]["released_scratch_hypotheses"] == 2
    assert artifact["metrics"]["released_hypothesis_lineage_depth"] == 2


def test_conflict_read_returns_exact_items_but_agenda_drops_candidate_objects():
    items = deepcopy(_memory()["items"])
    items.append(make_semantic_item(
        "m-effect-alt", kind="semantic_edge", subject_entity_id="intermediate_mechanism",
        relation_id="produces", object_entity_id="alternate_effect",
        content="The intermediate mechanism also has an alternate recorded effect.",
        source_ids=["obs-04"],
    ))
    source = _memory()
    checkpoint = make_checkpoint(
        "memory-conflict", world_id="world-0", skin_id="plain", life_id="life-0",
        entities=source["entities"], relation_specs=source["relation_specs"], items=items,
    )
    ops = [
        {
            "op": "QUERY", "subgoal_id": "root", "query_key": "effect_lookup",
            "object_entity_id": None,
        },
        {"op": "REQUEST_DREAM", "confusion_ids": ["conf-0000"]},
    ]
    artifact, agenda = run_scripted(checkpoint, _goal(), ops)
    result = artifact["trace"][0]["outcome"]
    assert result["status"] == "CONFLICT"
    assert {item["object_entity_id"] for item in result["items"]} == {
        "desired_effect", "alternate_effect"
    }
    assert agenda is not None
    serialized = json.dumps(agenda)
    assert "desired effect" not in serialized
    assert "alternate effect" not in serialized


def test_many_cardinality_is_not_conflict_and_checkpoint_bound_is_enforced():
    source = _memory()
    items = deepcopy(source["items"])
    items.extend([
        make_semantic_item(
            "m-many-1", kind="semantic_edge", subject_entity_id="x_entity",
            relation_id="relates", object_entity_id="y_entity",
            content="x relates to y", source_ids=["obs-many-1"],
        ),
        make_semantic_item(
            "m-many-2", kind="semantic_edge", subject_entity_id="x_entity",
            relation_id="relates", object_entity_id="desired_effect",
            content="x also relates to the desired effect", source_ids=["obs-many-2"],
        ),
    ])
    checkpoint = make_checkpoint(
        "memory-many", world_id="world-0", skin_id="plain", life_id="life-0",
        entities=source["entities"], relation_specs=source["relation_specs"], items=items,
    )
    result = ExactCheckpointReader(freeze_checkpoint(checkpoint)).retrieve({
        "query_id": "query-manual", "query_key": "many_lookup",
        "subject_entity_id": "x_entity", "relation_id": "relates",
        "object_entity_id": None,
    })
    assert result["status"] == "FOUND"
    assert len(result["items"]) == 2

    over_bound = deepcopy(items)
    for index, object_id in enumerate(
        ("current_mechanism", "intermediate_mechanism", "no_effect"), start=3
    ):
        over_bound.append(make_semantic_item(
            f"m-many-{index}", kind="semantic_edge", subject_entity_id="x_entity",
            relation_id="relates", object_entity_id=object_id,
            content=f"bounded relation item {index}", source_ids=[f"obs-many-{index}"],
        ))
    _assert_raises(lambda: make_checkpoint(
        "memory-over-bound", world_id="world-0", skin_id="plain", life_id="life-0",
        entities=source["entities"], relation_specs=source["relation_specs"],
        items=over_bound,
    ), "bound is 4")


def test_agenda_schema_rejects_answer_rationale_and_evidence_fields():
    artifact, agenda = run_scripted(_memory(), _goal(), [
        {
            "op": "QUERY", "subgoal_id": "root", "query_key": "safety_gap",
            "object_entity_id": None,
        },
        {"op": "REQUEST_DREAM", "confusion_ids": ["conf-0000"]},
    ])
    assert agenda is not None
    for field, value in (
        ("answer", "desired effect"),
        ("rationale", "because the desired effect is correct"),
        ("evidence", ["m-route"]),
    ):
        corrupt = deepcopy(agenda)
        corrupt["items"][0][field] = value
        corrupt["agenda_hash"] = "0" * 64
        _assert_raises(lambda corrupt=corrupt: validate_agenda(corrupt), "unexpected fields")
    # Trace mutation cannot be laundered through projection either.
    corrupt_trace = deepcopy(artifact)
    corrupt_trace["terminal"]["answer"] = "desired effect"
    _assert_raises(lambda: project_non_evidentiary_agenda(corrupt_trace), "trace hash mismatch")


def test_feedback_laundering_from_hypothesis_or_candidate_query_rejected():
    illegal = [
        {
            "op": "QUERY", "subgoal_id": "root", "query_key": "effect_lookup",
            "object_entity_id": "desired_effect",
        },
        # An invented confusion id cannot turn a candidate into a dream request.
        {"op": "REQUEST_DREAM", "confusion_ids": ["conf-0000"]},
    ]
    artifact, agenda = run_scripted(_memory(), _goal(), illegal)
    assert agenda is None
    assert artifact["terminal"]["kind"] == "DEFER"
    assert artifact["terminal"]["reason_code"] == "POLICY_ERROR"
    _assert_raises(
        lambda: parse_operation(json.dumps({
            "op": "REQUEST_DREAM", "confusion_ids": [],
            "hypothesis_id": "h", "rationale": "this answer seems right",
        })),
        "unexpected fields",
    )


def test_checkpoint_is_immutable_after_freeze_and_serialized_mutation_fails():
    source = _memory()
    frozen = freeze_checkpoint(source)
    original_hash = frozen.checkpoint_hash
    source["items"][0]["content"] = "mutated after freeze"
    assert frozen.items[0].content != "mutated after freeze"
    assert frozen.checkpoint_hash == original_hash
    _assert_raises(lambda: freeze_checkpoint(source), "semantic_hash: mismatch")
    try:
        setattr(frozen.items[0], "content", "mutate")
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError("frozen checkpoint item was mutated")


def test_budget_exhaustion_defers_instead_of_forcing_answer():
    operations = [
        {
            "op": "FORM_SUBGOAL", "subgoal_id": "sg1",
            "description": "inspect one dependency", "parent_subgoal_id": "root",
        },
        {
            "op": "FORM_SUBGOAL", "subgoal_id": "sg2",
            "description": "inspect a deeper dependency", "parent_subgoal_id": "sg1",
        },
    ]
    artifact, _ = run_scripted(_memory(), _goal(), operations, max_steps=2)
    assert artifact["terminal"]["kind"] == "DEFER"
    assert artifact["terminal"]["reason_code"] == "BUDGET_EXHAUSTED"
    assert "output" not in artifact["terminal"]


def test_policy_cannot_supply_free_text_query_or_query_id():
    _assert_raises(lambda: parse_operation(json.dumps({
        "op": "QUERY", "subgoal_id": "root", "query_key": "safety_gap",
        "object_entity_id": None, "query_id": "answer_is_red",
        "subject": "the answer is red", "relation": "please establish",
    })), "unexpected fields")


def test_abandoned_hypothesis_cannot_be_released_or_reused():
    ops = [
        {"op": "FORM_SUBGOAL", "subgoal_id": "old", "description": "old branch", "parent_subgoal_id": "root"},
        {"op": "QUERY", "subgoal_id": "old", "query_key": "route_lookup", "object_entity_id": None},
        {"op": "FOLLOW", "subgoal_id": "old", "from_semantic_id": "m-route", "to_semantic_id": "m-effect"},
        {"op": "HYPOTHESIZE", "subgoal_id": "old", "hypothesis_id": "h-old", "claim": "old claim", "cited_semantic_ids": ["m-route", "m-effect"], "parent_hypothesis_ids": []},
        {"op": "PREDICT", "subgoal_id": "old", "hypothesis_id": "h-old", "prediction_entity_id": "desired_effect"},
        {"op": "BACKTRACK", "subgoal_id": "old", "reason_code": "DEAD_END", "promote_hypothesis_id": None},
        {"op": "RELEASE", "hypothesis_id": "h-old"},
    ]
    artifact, _ = run_scripted(_memory(), _goal(), ops)
    assert artifact["terminal"]["kind"] == "DEFER"
    assert artifact["terminal"]["reason_code"] == "POLICY_ERROR"
    assert artifact["rejected_attempts"][-1]["error"] == \
        "RELEASE requires a live active-branch hypothesis"


def test_resolved_branch_requires_explicit_promotion_for_cross_branch_reuse():
    ops = [
        {"op": "FORM_SUBGOAL", "subgoal_id": "child", "description": "resolve child", "parent_subgoal_id": "root"},
        {"op": "QUERY", "subgoal_id": "child", "query_key": "route_lookup", "object_entity_id": None},
        {"op": "FOLLOW", "subgoal_id": "child", "from_semantic_id": "m-route", "to_semantic_id": "m-effect"},
        {"op": "HYPOTHESIZE", "subgoal_id": "child", "hypothesis_id": "h-child", "claim": "resolved child path", "cited_semantic_ids": ["m-route", "m-effect"], "parent_hypothesis_ids": []},
        {"op": "BACKTRACK", "subgoal_id": "child", "reason_code": "REVISE_PLAN", "promote_hypothesis_id": "h-child"},
        {"op": "HYPOTHESIZE", "subgoal_id": "root", "hypothesis_id": "h-root", "claim": "use promoted child", "cited_semantic_ids": ["m-route", "m-effect"], "parent_hypothesis_ids": ["h-child"]},
        {"op": "PREDICT", "subgoal_id": "root", "hypothesis_id": "h-root", "prediction_entity_id": "desired_effect"},
        {"op": "RELEASE", "hypothesis_id": "h-root"},
    ]
    artifact, _ = run_scripted(_memory(), _goal(), ops)
    assert artifact["terminal"]["kind"] == "RELEASE"
    assert artifact["trace"][4]["operation"]["promote_hypothesis_id"] == "h-child"


def test_valid_diamond_hypothesis_dag_is_not_a_cycle():
    ops = [
        {"op": "QUERY", "subgoal_id": "root", "query_key": "route_lookup", "object_entity_id": None},
        {"op": "FOLLOW", "subgoal_id": "root", "from_semantic_id": "m-route", "to_semantic_id": "m-effect"},
        {"op": "HYPOTHESIZE", "subgoal_id": "root", "hypothesis_id": "h0", "claim": "base", "cited_semantic_ids": ["m-route"], "parent_hypothesis_ids": []},
        {"op": "HYPOTHESIZE", "subgoal_id": "root", "hypothesis_id": "h1", "claim": "left", "cited_semantic_ids": ["m-route"], "parent_hypothesis_ids": ["h0"]},
        {"op": "HYPOTHESIZE", "subgoal_id": "root", "hypothesis_id": "h2", "claim": "right", "cited_semantic_ids": ["m-effect"], "parent_hypothesis_ids": ["h0"]},
        {"op": "HYPOTHESIZE", "subgoal_id": "root", "hypothesis_id": "h3", "claim": "join", "cited_semantic_ids": ["m-route", "m-effect"], "parent_hypothesis_ids": ["h1", "h2"]},
        {"op": "PREDICT", "subgoal_id": "root", "hypothesis_id": "h3", "prediction_entity_id": "desired_effect"},
        {"op": "RELEASE", "hypothesis_id": "h3"},
    ]
    artifact, _ = run_scripted(_memory(), _goal(), ops)
    assert artifact["terminal"]["kind"] == "RELEASE"
    assert artifact["metrics"]["released_scratch_hypotheses"] == 4


def test_repeat_block_is_visible_and_changes_public_state_hash():
    machine = ThinkerMachine(freeze_checkpoint(_memory()), _goal(), max_steps=4)
    operation = {
        "op": "QUERY", "subgoal_id": "root", "query_key": "route_lookup",
        "object_entity_id": None,
    }
    machine.apply(operation)
    blocked = machine.apply(operation)
    state = machine.public_state()
    assert blocked["outcome"] == "REPEAT_BLOCKED"
    assert blocked["state_before_hash"] != blocked["state_after_hash"]
    assert state["repeat_blocks"] == 1
    assert state["last_transition_notice"]["kind"] == "REPEAT_BLOCKED"


def test_wrong_output_without_supported_path_fails_closed():
    ops = _successful_ops()
    ops[-2] = {
        "op": "PREDICT", "subgoal_id": "sg-dependency", "hypothesis_id": "h-1",
        "prediction_entity_id": "no_effect",
    }
    artifact, _ = run_scripted(_memory(), _goal(), ops)
    assert artifact["terminal"]["kind"] == "DEFER"
    assert artifact["terminal"]["reason_code"] == "POLICY_ERROR"
    assert "supported directed path" in artifact["rejected_attempts"][-1]["error"]


def test_paraphrase_hypothesis_chain_cannot_inflate_certified_depth():
    ops = [
        {"op": "QUERY", "subgoal_id": "root", "query_key": "route_lookup", "object_entity_id": None},
        {"op": "FOLLOW", "subgoal_id": "root", "from_semantic_id": "m-route", "to_semantic_id": "m-effect"},
    ]
    parent = []
    for index in range(8):
        hypothesis_id = f"rewrite{index}"
        ops.append({
            "op": "HYPOTHESIZE", "subgoal_id": "root", "hypothesis_id": hypothesis_id,
            "claim": f"stylistic rewrite {index}",
            "cited_semantic_ids": ["m-route", "m-effect"],
            "parent_hypothesis_ids": parent,
        })
        parent = [hypothesis_id]
    ops.extend([
        {"op": "PREDICT", "subgoal_id": "root", "hypothesis_id": "rewrite7", "prediction_entity_id": "desired_effect"},
        {"op": "RELEASE", "hypothesis_id": "rewrite7"},
    ])
    artifact, _ = run_scripted(_memory(), _goal(), ops, max_steps=16)
    assert artifact["metrics"]["released_scratch_hypotheses"] == 8
    assert artifact["metrics"]["released_support_bearing_hypotheses"] == 1
    assert artifact["metrics"]["released_support_hypothesis_depth"] == 1
    assert artifact["metrics"]["thinker_compositional_path_depth"] == 3


def test_memory1_thinker_is_fresh_and_agenda_cannot_be_loaded_as_evidence():
    intermediate, agenda = run_scripted(_memory(), _goal(), [
        {
            "op": "QUERY", "subgoal_id": "root", "query_key": "safety_gap",
            "object_entity_id": None,
        },
        {"op": "REQUEST_DREAM", "confusion_ids": ["conf-0000"]},
    ])
    assert agenda is not None
    assert intermediate["trace_hash"] == agenda["thinker_trace_hash"]

    memory_1 = _memory()
    memory_1["checkpoint_id"] = "memory-1"
    memory_1["checkpoint_hash"] = ""
    # Rebuild rather than edit a committed hash: MEMORY_1 is a new phase
    # artifact, not a mutation of MEMORY_0.
    memory_1 = make_checkpoint(
        "memory-1", world_id="world-0", skin_id="plain", life_id="life-0",
        entities=memory_1["entities"], relation_specs=memory_1["relation_specs"],
        items=memory_1["items"], round_index=1,
    )
    final = ThinkerMachine(freeze_checkpoint(memory_1), _goal())
    fresh = final.public_state()
    assert fresh["checkpoint_id"] == "memory-1"
    assert fresh["frames"] == {
        "root": {
            "subgoal_id": "root",
            "description": _goal()["task"],
            "parent_subgoal_id": None,
            "status": "ACTIVE",
            "created_step": -1,
        }
    }
    assert fresh["retrieved"] == {}
    assert fresh["hypotheses"] == {}
    assert fresh["confusions"] == {}
    assert fresh["desires"] == {}
    assert fresh["rejected_attempts"] == []
    assert intermediate["trace_hash"] not in json.dumps(fresh)
    assert agenda["agenda_hash"] not in json.dumps(fresh)

    leaked_goal = _goal()
    leaked_goal["public_context"]["agenda"] = agenda
    _assert_raises(
        lambda: ThinkerMachine(freeze_checkpoint(memory_1), leaked_goal),
        "hidden/checker field forbidden",
    )


def test_cyclic_checkpoint_thinker_agenda_bridge_is_fresh_and_scope_bound():
    from .test_cyclic_organism_contract import valid_trace

    cyclic = valid_trace("bridge")
    checkpoint = checkpoint_from_cyclic_trace(
        cyclic,
        round_index=0,
        relation_specs=[
            {"relation_id": "routes", "label": "routes", "source_relation": "routes", "cardinality": "ONE", "max_results": 1},
            {"relation_id": "changes", "label": "changes", "source_relation": "changes", "cardinality": "ONE", "max_results": 1},
        ],
    )
    goal = {
        "goal_id": "bridge_goal",
        "task": "Identify the missing target effect without answering a final task.",
        "public_context": {"state_entity_id": "bridge-concept-valve"},
        "query_scope": {"templates": [{
            "query_key": "target_effect",
            "subject_entity_id": "bridge-concept-valve",
            "relation_id": "changes",
            "allow_unknown_object": True,
            "allowed_object_entity_ids": [],
        }]},
        "release_contract": {
            "mode": "DIRECTED_PATH",
            "anchor_entity_ids": ["bridge-concept-valve"],
            "allowed_output_entity_ids": ["bridge-concept-source"],
            "min_path_edges": 1,
            "max_path_edges": 2,
        },
    }
    _, agenda = run_scripted(checkpoint, goal, [
        {"op": "QUERY", "subgoal_id": "root", "query_key": "target_effect", "object_entity_id": None},
        {"op": "REQUEST_DREAM", "confusion_ids": ["conf-0000"]},
    ])
    assert agenda is not None
    validate_agenda_against_cyclic_trace(agenda, cyclic, round_index=0)

    stale = deepcopy(agenda)
    stale["source_checkpoint_hash"] = "0" * 64
    stale["agenda_hash"] = digest({
        key: value for key, value in stale.items() if key != "agenda_hash"
    })
    _assert_raises(
        lambda: validate_agenda_against_cyclic_trace(stale, cyclic, round_index=0),
        "stale or substituted checkpoint",
    )


def test_prompt_is_generic_and_contains_all_typed_controls():
    for operation in (
        "FORM_SUBGOAL", "QUERY", "FOLLOW", "HYPOTHESIZE", "PREDICT", "REVISE",
        "BACKTRACK", "REQUEST_DREAM", "RELEASE", "DEFER",
    ):
        assert operation in THINKER_SYSTEM_PROMPT
    for forbidden in ("candy", "land", "color", "mixture", "parent set", "role recipe"):
        assert forbidden not in THINKER_SYSTEM_PROMPT.casefold()
    assert "there is no answer operation" in THINKER_SYSTEM_PROMPT.casefold()
