"""CPU-only P0 conformance tests for the v0.3-R scientific recurrence."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
import json

from lands.model import WorldConfig
from lands.v03r import CounterfactualConfluenceV03R

from .goal_conditioned_thinker import digest as hardened_digest, validate_agenda
from .model_call_ledger import record_from_mapping
from .recurrent_text_organism import (
    DeterministicTextSnapshotCompiler,
    FrozenSchedule,
    MemoryItemView,
    SchedulerError,
    assert_v03r_gpu_preflight_ready,
    public_life_from_v03r,
    run_v03r_recurrent_dry_run,
    sha256_json,
)
from .scientific_thinker_adapter import (
    CAUSAL_JOIN_RELATION,
    HardenedThinkerMachineAdapter,
    ScriptedRecurrencePolicy,
    V03RGoldSemanticDreamer,
    V03RPublicAgendaCompiler,
)


def _run(worlds):
    lives = [public_life_from_v03r(world) for world in worlds]
    compiler = V03RPublicAgendaCompiler(
        {
            life.logical_life_id: world.precheckpoint_export("aligned")
            for life, world in zip(lives, worlds)
        },
        visible_aliases={
            life.logical_life_id: life.visible_life_id for life in lives
        },
    )
    result = run_v03r_recurrent_dry_run(
        worlds=worlds,
        dreamer=V03RGoldSemanticDreamer(),
        thinker=HardenedThinkerMachineAdapter(
            compiler, ScriptedRecurrencePolicy(),
        ),
        agenda_compiler=compiler,
        scientific_mode=True,
    )
    return result, lives


class _CapturingMachineAdapter:
    """Retain typed requests/executions while preserving the real adapter."""

    adapter_id = "test-capturing-scientific-adapter"

    def __init__(self, inner):
        self.inner = inner
        self.calls = []

    def run_machine(self, request):
        execution = self.inner.run_machine(request)
        self.calls.append((request, execution))
        return execution


def _capture_scientific_calls(world):
    life = public_life_from_v03r(world)
    compiler = V03RPublicAgendaCompiler(
        {life.logical_life_id: world.precheckpoint_export("aligned")},
        visible_aliases={life.logical_life_id: life.visible_life_id},
    )
    capture = _CapturingMachineAdapter(HardenedThinkerMachineAdapter(
        compiler, ScriptedRecurrencePolicy(),
    ))
    run_v03r_recurrent_dry_run(
        worlds=[world], dreamer=V03RGoldSemanticDreamer(),
        thinker=capture, agenda_compiler=compiler, scientific_mode=True,
    )
    return compiler, capture.calls


def _assert_execution_rejected(execution, request, compiler, message):
    try:
        execution.validate(request, trusted_goal_compiler=compiler)
    except SchedulerError as exc:
        assert message in str(exc)
    else:
        raise AssertionError("adversarial scientific execution was accepted")


def _artifact(result, arm, logical_life_id):
    return next(
        item for item in result["artifacts"]
        if item["arm"] == arm and item["logical_life_id"] == logical_life_id
    )


def _model_facing_think_request(artifact):
    return artifact["intermediate_think"]["request"]


def test_v03r_gold_recurrence_is_not_found_request_dream_edge_then_fresh_release():
    worlds = [
        CounterfactualConfluenceV03R(WorldConfig(seed=0), latent_bit=bit)
        for bit in (0, 1)
    ]
    result, lives = _run(worlds)
    assert len(result["artifacts"]) == 6
    for life in lives:
        agenda = _artifact(result, "agenda_feedback", life.logical_life_id)
        no_feedback = _artifact(result, "no_feedback", life.logical_life_id)
        distractor = _artifact(result, "matched_distractor", life.logical_life_id)
        initial_machine = agenda["intermediate_think"]["scientific_execution"][
            "machine_artifact"
        ]
        assert initial_machine["trace"][0]["outcome"]["status"] == "NOT_FOUND"
        assert initial_machine["terminal"]["kind"] == "REQUEST_DREAM"
        assert initial_machine["trace"][0]["operation"]["object_entity_id"] is None
        final_machine = agenda["final_think"]["scientific_execution"][
            "machine_artifact"
        ]
        assert final_machine["terminal"]["kind"] == "RELEASE"
        assert final_machine["terminal"]["support_path_semantic_ids"]
        final_execution = agenda["final_think"]["scientific_execution"]
        assert final_execution["objective_binding"] == "recurrence_probe_ceiling"
        assert final_execution["compiled_goal"]["public_context"]["probe_id"] != \
            agenda["final_think"]["request"]["goal_id"]
        assert agenda["goal_evaluation"]["final_goal_answer_scored"] is False
        assert "not a final-goal answer" in agenda["controller_condition"]
        assert agenda["final_think"]["request"]["reset_id"] != \
            agenda["intermediate_think"]["request"]["reset_id"]
        own_edges = [
            edge for edge in agenda["trace"]["semantic_edges"]
            if edge["relation"] == CAUSAL_JOIN_RELATION
        ]
        assert len(own_edges) == 1
        assert no_feedback["trace"]["semantic_edges"] == []
        assert no_feedback["final_think"]["scientific_execution"][
            "machine_artifact"
        ]["terminal"]["kind"] == "DEFER"
        assert distractor["final_think"]["scientific_execution"][
            "machine_artifact"
        ]["terminal"]["kind"] == "DEFER"
        assert len(distractor["trace"]["semantic_edges"]) == 1


def test_public_probe_vocabulary_has_no_answer_valve_or_operation_and_wrong_is_distinct():
    world = CounterfactualConfluenceV03R(WorldConfig(seed=0), latent_bit=0)
    result, lives = _run([world])
    item = _artifact(result, "agenda_feedback", lives[0].logical_life_id)
    request = item["intermediate_think"]["request"]
    vocabulary = request["agenda_vocabulary"]
    serialized = json.dumps(vocabulary, sort_keys=True).casefold()
    for forbidden in (
        "answer_valve", "next_operation", "subtract", "stable", "change",
        "keep_passive", "final_answer",
    ):
        assert forbidden not in serialized
    templates = vocabulary["templates"]
    assert len(templates) == 2
    assert templates[0]["relation_id"] == templates[1]["relation_id"] == \
        CAUSAL_JOIN_RELATION
    assert (
        templates[0]["left_id"], templates[0]["relation_id"], templates[0]["right_id"],
    ) != (
        templates[1]["left_id"], templates[1]["relation_id"], templates[1]["right_id"],
    )


def test_latent_twins_share_visible_scope_and_vocabulary_despite_different_truth():
    worlds = [
        CounterfactualConfluenceV03R(WorldConfig(seed=0), latent_bit=bit)
        for bit in (0, 1)
    ]
    assert worlds[0].goal.answer_ratio != worlds[1].goal.answer_ratio
    result, lives = _run(worlds)
    assert lives[0].logical_life_id != lives[1].logical_life_id
    assert lives[0].visible_life_id == lives[1].visible_life_id
    requests = [
        _artifact(result, "agenda_feedback", life.logical_life_id)[
            "intermediate_think"
        ]["request"]
        for life in lives
    ]
    assert requests[0]["logical_life_id"] == requests[1]["logical_life_id"]
    assert requests[0]["life_id"] == requests[1]["life_id"]
    assert requests[0]["agenda_vocabulary"] == requests[1]["agenda_vocabulary"]


def test_model_visible_ids_and_complete_think_request_ignore_private_member_mutation():
    original = CounterfactualConfluenceV03R(WorldConfig(seed=0), latent_bit=0)
    mutated = deepcopy(original)
    mutated.latent_bit = "PRIVATE_MEMBER_SENTINEL"
    mutated.latent_tuple_id = "PRIVATE_PAIR_SENTINEL"
    left, left_lives = _run([original])
    right, right_lives = _run([mutated])
    assert left_lives[0].logical_life_id != right_lives[0].logical_life_id
    assert left_lives[0].visible_life_id == right_lives[0].visible_life_id
    left_item = _artifact(left, "agenda_feedback", left_lives[0].logical_life_id)
    right_item = _artifact(right, "agenda_feedback", right_lives[0].logical_life_id)
    assert _model_facing_think_request(left_item) == _model_facing_think_request(right_item)
    assert "PRIVATE_MEMBER_SENTINEL" not in json.dumps(left, sort_keys=True)
    assert "PRIVATE_MEMBER_SENTINEL" not in json.dumps(right, sort_keys=True)
    assert "PRIVATE_PAIR_SENTINEL" not in json.dumps(left, sort_keys=True)
    assert "PRIVATE_PAIR_SENTINEL" not in json.dumps(right, sort_keys=True)


def test_scientific_mode_rejects_direct_precompleted_thinker_result():
    from .test_recurrent_text_organism import NoAgendaGoldThinker

    world = CounterfactualConfluenceV03R(WorldConfig(seed=0), latent_bit=0)
    try:
        run_v03r_recurrent_dry_run(
            worlds=[world], dreamer=V03RGoldSemanticDreamer(),
            thinker=NoAgendaGoldThinker(), scientific_mode=True,
        )
    except SchedulerError as exc:
        assert "direct ThinkerResult is forbidden" in str(exc)
    else:
        raise AssertionError("scientific mode accepted a precompleted thinker result")


def test_every_dream_view_is_one_public_event_plus_fixed_bounded_semantic_neighbors():
    world = CounterfactualConfluenceV03R(WorldConfig(seed=0), latent_bit=0)
    result, _ = _run([world])
    schedule = FrozenSchedule()
    for item in result["artifacts"]:
        assert item["schedule"]["dream_semantic_neighbor_k"] == \
            schedule.dream_semantic_neighbor_k
        assert item["schedule"]["full_memory_ceiling"] is False
        for call in item["dream_calls"]:
            request = call["request"]
            assert len(request["visible_experience_hashes"]) == 1
            assert len(request["visible_semantic_hashes"]) <= \
                schedule.dream_semantic_neighbor_k
            assert request["declared_semantic_neighbor_k"] == \
                schedule.dream_semantic_neighbor_k


def test_scientific_execution_persists_strict_ledger_and_exact_call_materials():
    world = CounterfactualConfluenceV03R(WorldConfig(seed=0), latent_bit=0)
    result, _ = _run([world])
    for item in result["artifacts"]:
        for phase in ("intermediate_think", "final_think"):
            execution = item[phase]["scientific_execution"]
            records = execution["model_call_ledger"]
            materials = execution["model_call_materials"]
            assert records and len(records) == len(materials)
            for record, material in zip(records, materials):
                parsed = record_from_mapping(record)
                assert parsed.call_id == material["call_id"]
                assert parsed.reset_instance_id == item[phase]["request"]["reset_id"]
                assert material["prompt"] == (
                    material["prompt_template"] + "\n" + material["input_payload"]
                )


def test_realization_corpus_has_no_normalized_cue_collision_or_duplicate_row():
    world = CounterfactualConfluenceV03R(WorldConfig(seed=0), latent_bit=0)
    result, _ = _run([world])
    for item in result["artifacts"]:
        seen_cues = {}
        seen_rows = set()
        for row in item["trace"]["realization_specs"]:
            cue = " ".join(row["cue_text"].split()).casefold()
            target = " ".join(row["target_text"].split()).casefold()
            assert seen_cues.setdefault(cue, target) == target
            exact = (row["form"], cue, target)
            assert exact not in seen_rows
            seen_rows.add(exact)


def test_gpu_preflight_explicitly_records_remaining_p1_shortcut_audit():
    world = CounterfactualConfluenceV03R(WorldConfig(seed=0), latent_bit=0)
    result, _ = _run([world])
    assert result["gpu_preflight"] == {
        "status": "BLOCKED_P1",
        "blockers": [
            "rendered-text-and-order-shortcut-audit",
            "public-final-goal-thinker-and-paired-scoring",
        ],
        "cpu_gold_is_not_a_model_result": True,
    }
    try:
        assert_v03r_gpu_preflight_ready()
    except SchedulerError as exc:
        assert "rendered-text-and-order-shortcut-audit" in str(exc)
        assert "public-final-goal-thinker-and-paired-scoring" in str(exc)
    else:
        raise AssertionError("GPU preflight ignored an explicitly open P1")


def test_snapshot_compiler_cannot_mutate_a_row_under_an_existing_hash():
    class MutatingSnapshot(DeterministicTextSnapshotCompiler):
        compiler_id = "adversarial-mutating-snapshot"

        def compile(self, checkpoint):
            rows = list(checkpoint.semantic_items)
            rows[0] = replace(rows[0], canonical_text="laundered replacement")
            return tuple(rows)

    world = CounterfactualConfluenceV03R(WorldConfig(seed=0), latent_bit=0)
    try:
        run_v03r_recurrent_dry_run(
            worlds=[world], dreamer=V03RGoldSemanticDreamer(),
            thinker=object(), snapshot_compiler=MutatingSnapshot(),
        )
    except SchedulerError as exc:
        assert "changed or introduced" in str(exc)
    else:
        raise AssertionError("snapshot compiler mutated a committed row")


def test_scheduler_rejects_every_compact_result_field_mutation_after_exact_replay():
    world = CounterfactualConfluenceV03R(WorldConfig(seed=0), latent_bit=0)
    compiler, calls = _capture_scientific_calls(world)
    request, execution = next(
        (request, execution) for request, execution in calls
        if execution.result.agenda_queries
    )
    release_request, release_execution = next(
        (request, execution) for request, execution in calls
        if execution.result.disposition == "released"
    )
    result = execution.result
    available_hash = request.memory[0].semantic_hash
    mutations = {
        "retrieved_semantic_hashes": replace(
            result, retrieved_semantic_hashes=(available_hash,),
        ),
        "workspace": replace(result, workspace=("forged workspace",)),
        "claim": replace(result, claim="forged but locally well-typed claim"),
        "confidence": replace(result, confidence=0.5),
        "disposition": replace(result, disposition="tentative"),
        "unresolved_dependency": replace(
            result, unresolved_dependency="q:forged-dependency",
        ),
        "attempted_queries": replace(result, attempted_queries=()),
        "missing_semantic_keys": replace(result, missing_semantic_keys=()),
    }
    release_result = release_execution.result
    mutations["cited_semantic_hashes"] = replace(
        release_result, cited_semantic_hashes=(),
    )
    for field_name, mutated_result in mutations.items():
        selected_request = (
            release_request if field_name == "cited_semantic_hashes" else request
        )
        selected_execution = (
            release_execution if field_name == "cited_semantic_hashes" else execution
        )
        # These summaries pass the old local shape/subset checks; exact replay
        # projection, rather than incidental schema invalidity, must reject them.
        mutated_result.validate(selected_request)
        _assert_execution_rejected(
            replace(selected_execution, result=mutated_result),
            selected_request,
            compiler,
            "exact mechanical replay projection",
        )


def test_scheduler_rejects_registered_distractor_substituted_for_replayed_agenda():
    world = CounterfactualConfluenceV03R(WorldConfig(seed=0), latent_bit=0)
    compiler, calls = _capture_scientific_calls(world)
    request, execution = next(
        (request, execution) for request, execution in calls
        if execution.result.agenda_queries
    )
    vocabulary = request.agenda_vocabulary
    assert vocabulary is not None
    own_query = execution.result.agenda_queries[0]
    distractor = next(
        item for item in vocabulary.templates if item.query_key != own_query.query_key
    )
    substituted_query = replace(
        own_query,
        query_key=distractor.query_key,
        kind=distractor.kind,
        left_id=distractor.left_id,
        relation_id=distractor.relation_id,
        right_id=distractor.right_id,
    )
    substituted_result = replace(
        execution.result,
        unresolved_dependency=substituted_query.query_key,
        attempted_queries=(substituted_query.query_key,),
        missing_semantic_keys=(substituted_query.right_id,),
        agenda_queries=(substituted_query,),
    )
    substituted_result.validate(request)

    substituted_agenda = deepcopy(dict(execution.agenda_artifact))
    substituted_item = substituted_agenda["items"][0]
    substituted_item["query_key"] = distractor.query_key
    substituted_item["subject_entity_id"] = distractor.left_id
    substituted_item["relation_id"] = distractor.relation_id
    substituted_agenda["agenda_hash"] = hardened_digest({
        key: value for key, value in substituted_agenda.items()
        if key != "agenda_hash"
    })
    # It is a valid registered query and a valid standalone agenda.  Only
    # mechanical reconstruction from the replayed confusion distinguishes it.
    validate_agenda(substituted_agenda)
    _assert_execution_rejected(
        replace(
            execution,
            result=substituted_result,
            agenda_artifact=substituted_agenda,
        ),
        request,
        compiler,
        "exact mechanical replay projection",
    )


def test_scheduler_rejects_adapter_checkpoint_injection_with_consistent_machine_trace():
    class CheckpointInjectingAdapter:
        adapter_id = "test-checkpoint-injecting-adapter"

        def __init__(self, inner):
            self.inner = inner

        def run_machine(self, request):
            vocabulary = request.agenda_vocabulary
            assert vocabulary is not None
            own = next(
                item for item in vocabulary.templates
                if item.query_key == "q:causal-join:own"
            )
            forged_hash = sha256_json({
                "attack": "adapter-only-causal-edge",
                "source": own.left_id,
                "target": own.right_id,
            })
            forged_edge = MemoryItemView(
                semantic_hash=forged_hash,
                kind="semantic_edge",
                canonical_text="adapter-only supported causal join",
                status="supported",
                source_entity_id=own.left_id,
                relation_id=own.relation_id,
                target_entity_id=own.right_id,
            )
            forged_request = replace(
                request, memory=(*request.memory, forged_edge),
            )
            # The inner adapter builds a fully hash-consistent checkpoint,
            # ledger, machine trace, and RELEASE from the injected edge.
            return self.inner.run_machine(forged_request)

    world = CounterfactualConfluenceV03R(WorldConfig(seed=0), latent_bit=0)
    life = public_life_from_v03r(world)
    compiler = V03RPublicAgendaCompiler(
        {life.logical_life_id: world.precheckpoint_export("aligned")},
        visible_aliases={life.logical_life_id: life.visible_life_id},
    )
    attacker = CheckpointInjectingAdapter(HardenedThinkerMachineAdapter(
        compiler, ScriptedRecurrencePolicy(),
    ))
    try:
        run_v03r_recurrent_dry_run(
            worlds=[world], dreamer=V03RGoldSemanticDreamer(),
            thinker=attacker, agenda_compiler=compiler, scientific_mode=True,
        )
    except SchedulerError as exc:
        assert "differs from scheduler reconstruction" in str(exc)
    else:
        raise AssertionError("scheduler trusted an adapter-injected checkpoint edge")


def test_scheduler_rejects_adapter_goal_injection_with_consistent_machine_trace():
    class GoalInjectingCompiler:
        compiler_id = "test-goal-injecting-compiler"

        def __init__(self, trusted):
            self.trusted = trusted

        def compile_goal(self, request, checkpoint_payload):
            goal = deepcopy(dict(
                self.trusted.compile_goal(request, checkpoint_payload)
            ))
            goal["task"] = "adapter-authored replacement objective"
            return goal

    world = CounterfactualConfluenceV03R(WorldConfig(seed=0), latent_bit=0)
    life = public_life_from_v03r(world)
    trusted_compiler = V03RPublicAgendaCompiler(
        {life.logical_life_id: world.precheckpoint_export("aligned")},
        visible_aliases={life.logical_life_id: life.visible_life_id},
    )
    attacker = HardenedThinkerMachineAdapter(
        GoalInjectingCompiler(trusted_compiler), ScriptedRecurrencePolicy(),
    )
    try:
        run_v03r_recurrent_dry_run(
            worlds=[world], dreamer=V03RGoldSemanticDreamer(),
            thinker=attacker, agenda_compiler=trusted_compiler,
            scientific_mode=True,
        )
    except SchedulerError as exc:
        assert "goal differs from scheduler reconstruction" in str(exc)
    else:
        raise AssertionError("scheduler trusted an adapter-injected goal")
