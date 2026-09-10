"""Plain CPU tests for the recurrent text-organism scheduler."""

from __future__ import annotations

from copy import deepcopy

from lands.model import WorldConfig
from lands.v03r import CounterfactualConfluenceV03R

from .cyclic_organism_contract import compute_metrics, validate_dataset, validate_trace
from .goal_conditioned_thinker import SCHEMA_VERSION as THINKER_SCHEMA_VERSION
from .goal_conditioned_thinker import RESET_POLICY as THINKER_RESET_POLICY
from .goal_conditioned_thinker import digest as thinker_digest
from .recurrent_text_organism import (
    ARM_NAMES,
    AgendaQuery,
    AgendaQueryTemplate,
    AgendaVocabulary,
    DeterministicTextSnapshotCompiler,
    FinalExpectation,
    FrozenSchedule,
    PremiseIdentity,
    PublicExperience,
    PublicLife,
    ReturnRoundSpec,
    SchedulerError,
    SemanticDecision,
    ThinkerRequest,
    ThinkerResult,
    agenda_queries_from_hardened_thinker,
    assert_typed_feedback_sources,
    deterministic_shuffle_donors,
    public_life_from_v03r,
    run_recurrent_text_experiment,
    run_v03r_recurrent_dry_run,
    score_final_pairs,
)
from .cyclic_organism_contract import concept_semantic_hash, edge_semantic_hash


VALVE = concept_semantic_hash("entity:local-valve")
SOURCE = concept_semantic_hash("place:local-source")
TARGET = concept_semantic_hash("place:local-target")
ROUTE = edge_semantic_hash(VALVE, "routes", SOURCE)
EFFECT = edge_semantic_hash(VALVE, "changes", TARGET)


def _life(seed: int, bit: int) -> PublicLife:
    experiences = tuple(
        PublicExperience(
            public_id=f"seed{seed}-bit{bit}-exp-{index:02d}",
            sequence_index=index,
            action=f"public action {seed} {bit} {index}",
            observation=f"public observation {seed} {bit} {index}",
            outcome=f"public outcome {seed} {bit} {index}",
        )
        for index in range(46)
    )
    probe_id = f"probe-{seed}-{bit}"
    vocabulary = AgendaVocabulary.freeze(probe_id, (
        AgendaQueryTemplate(
            query_key="q:local-effect", kind="missing_dependency",
            left_id="entity:local-valve", relation_id="changes",
            right_id="place:local-target",
        ),
        AgendaQueryTemplate(
            query_key="q:matched-distractor", kind="missing_dependency",
            left_id="place:local-source", relation_id="changes",
            right_id="place:local-target",
        ),
    ))
    return PublicLife(
        logical_life_id=f"seed{seed}-bit{bit}",
        world_id=f"world-seed-{seed}", skin_id="aligned", split="development",
        experiences=experiences,
        intermediate_goal_id=probe_id,
        intermediate_goal="Identify one unresolved local dependency; do not solve the final goal.",
        final_goal_id=f"final-goal-{seed}-{bit}",
        final_goal=f"Return the final held-out decision for seed {seed} member {bit}.",
        final_goal_forbidden_markers=(f"private-answer-{seed}-{bit}",),
        agenda_vocabularies=(vocabulary,),
    )


class GoldLocalDreamer:
    """Generic deterministic stub: one local operation or PASS per call."""

    def dream(self, request):
        exp = request.visible_experiences[0]
        premise = (PremiseIdentity("experience", exp.payload_hash),)
        if request.stage == "WAKE" and exp.sequence_index == 0:
            return SemanticDecision.concept(
                canonical_key="entity:local-valve", display_label="the local valve",
                rule="name one witnessed local entity", premises=premise,
            )
        if request.stage == "WAKE" and exp.sequence_index == 1:
            return SemanticDecision.concept(
                canonical_key="place:local-source", display_label="the local source",
                rule="name one witnessed local place", premises=premise,
            )
        if request.stage == "WAKE" and exp.sequence_index == 2:
            return SemanticDecision.concept(
                canonical_key="place:local-target", display_label="the local target",
                rule="name one witnessed local place", premises=premise,
            )
        if request.stage == "WAKE" and exp.sequence_index == 3:
            return SemanticDecision.edge(
                source_semantic_hash=VALVE, relation="routes",
                target_semantic_hash=SOURCE,
                rule="connect one locally witnessed relation",
                premises=(
                    *premise, PremiseIdentity("concept", VALVE),
                    PremiseIdentity("concept", SOURCE),
                ),
            )
        if request.stage == "RETURN_SLEEP" and request.selection_queries \
                and EFFECT not in {item.semantic_hash for item in request.memory}:
            return SemanticDecision.edge(
                source_semantic_hash=VALVE, relation="changes",
                target_semantic_hash=TARGET,
                rule="independently connect one agenda-selected local relation",
                premises=(
                    *premise, PremiseIdentity("concept", VALVE),
                    PremiseIdentity("concept", TARGET),
                    PremiseIdentity("semantic_edge", ROUTE),
                ),
            )
        return SemanticDecision.pass_()


class GoldThinker:
    """Injectable thinker boundary; no game recipe is embedded in scheduler."""

    def think(self, request: ThinkerRequest) -> ThinkerResult:
        available = {item.semantic_hash for item in request.memory}
        if request.round_index == 0:
            retrieved = (ROUTE,) if ROUTE in available else ()
            return ThinkerResult(
                retrieved_semantic_hashes=retrieved,
                workspace=("one local route is known; its target effect is unresolved",),
                claim="a local target-effect dependency is still missing",
                cited_semantic_hashes=retrieved, confidence=0.4,
                disposition="deferred",
                unresolved_dependency="connect a routed source to one target effect",
                attempted_queries=("which local relation is missing?",),
                missing_semantic_keys=("local-valve -> effect -> local-target",),
                agenda_queries=(AgendaQuery(
                    query_key="q:local-effect",
                    kind="missing_dependency",
                    left_id="entity:local-valve", relation_id="changes",
                    right_id="place:local-target",
                    source_checkpoint_hash=request.checkpoint_hash,
                    source_goal_id=request.goal_id,
                    vocabulary_hash=request.agenda_vocabulary.vocabulary_hash,
                ),),
            )
        if EFFECT in available:
            return ThinkerResult(
                retrieved_semantic_hashes=(ROUTE, EFFECT),
                workspace=("compose the two retrieved local relations",),
                claim="the held-out decision is supported by the refreshed memory",
                cited_semantic_hashes=(ROUTE, EFFECT), confidence=0.9,
                disposition="released",
            )
        retrieved = (ROUTE,) if ROUTE in available else ()
        return ThinkerResult(
            retrieved_semantic_hashes=retrieved,
            workspace=("the refreshed memory still lacks one dependency",),
            claim="the final decision remains underdetermined",
            cited_semantic_hashes=retrieved, confidence=0.2,
            disposition="deferred",
            unresolved_dependency="target effect is absent",
            attempted_queries=("retrieve target effect",),
            missing_semantic_keys=("local target effect",),
        )


class NoAgendaGoldThinker(GoldThinker):
    """Plumbing-only ceiling for public lives without a frozen query registry."""

    def think(self, request: ThinkerRequest) -> ThinkerResult:
        result = super().think(request) if request.round_index != 0 else ThinkerResult(
            retrieved_semantic_hashes=(ROUTE,) if ROUTE in {
                item.semantic_hash for item in request.memory
            } else (),
            workspace=("one unresolved local dependency remains",),
            claim="the operational probe remains unresolved in this plumbing control",
            cited_semantic_hashes=(ROUTE,) if ROUTE in {
                item.semantic_hash for item in request.memory
            } else (),
            confidence=0.2, disposition="deferred",
            unresolved_dependency="typed agenda unavailable",
            attempted_queries=("offline diagnostic only",),
            missing_semantic_keys=("offline diagnostic only",),
            agenda_queries=(),
        )
        return result


def _run():
    lives = [_life(seed, bit) for seed in (0, 1) for bit in (0, 1)]
    return run_recurrent_text_experiment(
        lives=lives, dreamer=GoldLocalDreamer(), thinker=GoldThinker(),
    )


def _artifact(result: dict, arm: str, life_id: str) -> dict:
    return next(
        item for item in result["artifacts"]
        if item["arm"] == arm and item["logical_life_id"] == life_id
    )


def test_v03r_seed0_declares_and_exposes_exact_frozen_46_wake_events():
    for bit in (0, 1):
        world = CounterfactualConfluenceV03R(WorldConfig(seed=0), latent_bit=bit)
        life = public_life_from_v03r(world)
        assert len(life.experiences) == 46
        assert FrozenSchedule().expected_wake_calls == len(life.experiences)
        assert life.final_goal not in str(world.precheckpoint_export("aligned"))


def test_v03r_public_lives_flow_through_full_cpu_schedule_without_hidden_truth():
    worlds = [
        CounterfactualConfluenceV03R(WorldConfig(seed=seed), latent_bit=bit)
        for seed in (0, 2) for bit in (0, 1)
    ]
    result = run_v03r_recurrent_dry_run(
        worlds=worlds, dreamer=GoldLocalDreamer(), thinker=NoAgendaGoldThinker(),
    )
    assert len(result["artifacts"]) == 12
    assert result["control_arm"] == "matched_distractor"
    for item in result["artifacts"]:
        assert item["schedule"]["actual_wake_calls"] == 46
        assert item["controller_condition"].endswith("ceiling")
        assert validate_trace(item["trace"]) == []


def test_declared_wake_budget_must_equal_actual_frozen_event_count():
    short = deepcopy(_life(0, 0))
    object.__setattr__(short, "experiences", short.experiences[:-1])
    try:
        run_recurrent_text_experiment(
            lives=[short, _life(1, 0)], dreamer=GoldLocalDreamer(), thinker=GoldThinker(),
        )
    except SchedulerError as exc:
        assert "declared WAKE budget 46" in str(exc)
        assert "actual frozen public episode count 45" in str(exc)
    else:
        raise AssertionError("episode-count mismatch was silently padded/accepted")


def test_all_arms_share_exact_prefix_and_identical_intermediate_think():
    result = _run()
    for life_id in ("seed0-bit0", "seed0-bit1", "seed1-bit0", "seed1-bit1"):
        artifacts = [_artifact(result, arm, life_id) for arm in ARM_NAMES]
        assert len({item["prefix_digest"] for item in artifacts}) == 1
        assert len({
            item["intermediate_think"]["request"]["checkpoint_semantic_hash"]
            for item in artifacts
        }) == 1
        assert len({
            str(item["intermediate_think"]["result"]) for item in artifacts
        }) == 1
        prefix_lengths = [
            sum(call["request"]["stage"] != "RETURN_SLEEP" for call in item["dream_calls"])
            for item in artifacts
        ]
        assert prefix_lengths == [84, 84, 84]


def test_frozen_call_budgets_are_matched_across_every_arm():
    result = _run()
    for item in result["artifacts"]:
        counts = {}
        for call in item["dream_calls"]:
            stage = call["request"]["stage"]
            counts[stage] = counts.get(stage, 0) + 1
        assert counts == {
            "WAKE": 46, "REACTIVATE": 22,
            "TARGET_BLIND_SLEEP": 16, "RETURN_SLEEP": 16,
        }
        assert item["schedule"]["total_dream_calls"] == 100
        assert item["schedule"]["actual_wake_calls"] == 46
        assert item["schedule"]["reactivation_after_wake_indices"] == list(
            range(1, 44, 2)
        )
        stages = [call["request"]["stage"] for call in item["dream_calls"]]
        assert stages[:68].count("WAKE") == 46
        assert stages[:68].count("REACTIVATE") == 22
        assert stages[68:84] == ["TARGET_BLIND_SLEEP"] * 16
        assert [call["request"]["call_index"] for call in item["dream_calls"]] == \
            list(range(100))


def test_scheduler_supports_arbitrary_repeated_return_rounds_in_lockstep():
    schedule = FrozenSchedule(return_rounds=(
        ReturnRoundSpec(dream_calls=2, thinker_budget=4, reveal_final_goal=False),
        ReturnRoundSpec(dream_calls=3, thinker_budget=5, reveal_final_goal=True),
    ))
    result = run_recurrent_text_experiment(
        lives=[_life(seed, bit) for seed in (0, 1) for bit in (0, 1)],
        dreamer=GoldLocalDreamer(), thinker=GoldThinker(), schedule=schedule,
    )
    for item in result["artifacts"]:
        assert item["trace"]["round_count"] == 3
        assert len(item["trace"]["checkpoints"]) == 3
        assert len(item["trace"]["agendas"]) == 3
        assert len(item["selection_records"]) == 2
        assert len(item["dream_calls"]) == 89
        assert item["final_think"]["request"]["operation_budget"] == 5
        assert item["final_think"]["request"]["fresh_workspace"] is True
        assert validate_trace(item["trace"]) == []


def test_final_goal_is_absent_from_every_dream_and_only_revealed_after_memory1():
    result = _run()
    for item in result["artifacts"]:
        life = _life(
            int(item["logical_life_id"].split("-")[0].removeprefix("seed")),
            int(item["logical_life_id"].split("bit")[1]),
        )
        calls = str(item["dream_calls"])
        assert life.final_goal_id not in calls
        assert life.final_goal not in calls
        assert all(call["request"]["final_goal_visible"] is False
                   for call in item["dream_calls"])
        assert item["final_reveal"]["revealed_after_checkpoint_id"] == \
            item["trace"]["checkpoints"][-1]["checkpoint_id"]
        assert item["final_think"]["request"]["goal"] == life.final_goal


def test_matched_distractor_is_distinct_recipient_typed_and_selection_only():
    result = _run()
    for item in result["artifacts"]:
        selection = item["selection_records"][0]
        if item["arm"] == "matched_distractor":
            assert selection["mode"] == "matched_distractor"
            assert selection["donor_logical_life_id"] is None
            assert selection["non_evidentiary"] is True
            assert [query["kind"] for query in selection["queries"]] == [
                "missing_dependency"
            ]
            # The wrong tuple is precommitted in the recipient's public-only
            # registry and remains bound to the same checkpoint/goal.
            intermediate = item["intermediate_think"]["request"]
            selected_query = selection["queries"][0]
            own_query = item["intermediate_think"]["result"]["agenda_queries"][0]
            assert (
                selected_query["left_id"], selected_query["relation_id"],
                selected_query["right_id"],
            ) != (
                own_query["left_id"], own_query["relation_id"], own_query["right_id"],
            )
            assert selected_query["source_checkpoint_hash"] == \
                intermediate["checkpoint_hash"]
            assert selected_query["source_goal_id"] == intermediate["goal_id"]
            assert selected_query["vocabulary_hash"] == \
                intermediate["agenda_vocabulary"]["vocabulary_hash"]
        # The strict cyclic trace independently proves every dream premise is
        # recipient-local and that agendas cannot occur in premise_refs.
        assert validate_trace(item["trace"]) == []
        assert all(
            premise["kind"] in {"experience", "concept", "semantic_edge"}
            for derivation in item["trace"]["derivations"]
            for premise in derivation["premise_refs"]
        )


def test_agenda_queries_must_be_typed_atomic_and_bound_to_think_checkpoint():
    class UnboundThinker(GoldThinker):
        def think(self, request):
            result = super().think(request)
            if request.round_index != 0:
                return result
            return ThinkerResult(
                **{
                    **vars(result),
                    "agenda_queries": (AgendaQuery(
                        query_key="q:local-effect",
                        kind="missing_dependency",
                        left_id="ANSWER_IS_X", relation_id="changes",
                        right_id="place:local-target",
                        source_checkpoint_hash=request.checkpoint_hash,
                        source_goal_id=request.goal_id,
                        vocabulary_hash=request.agenda_vocabulary.vocabulary_hash,
                    ),),
                }
            )

    try:
        run_recurrent_text_experiment(
            lives=[_life(0, 0), _life(1, 0)],
            dreamer=GoldLocalDreamer(), thinker=UnboundThinker(),
        )
    except SchedulerError as exc:
        assert "registered template" in str(exc) or "frozen checkpoint" in str(exc)
    else:
        raise AssertionError("free-form/unbound agenda was accepted")


def test_scheduler_rejects_hypothesis_sourced_desire_even_if_base_contract_allows_it():
    trace = deepcopy(_artifact(_run(), "agenda_feedback", "seed0-bit0")["trace"])
    desire = trace["thinker_desires"][0]
    hypothesis = next(
        item for item in trace["thinker_hypotheses"]
        if item["round_index"] == desire["round_index"]
    )
    desire["source_confusion_id"] = hypothesis["hypothesis_id"]
    try:
        assert_typed_feedback_sources(trace)
    except SchedulerError as exc:
        assert "typed confusions only" in str(exc)
    else:
        raise AssertionError("free hypothesis was accepted as dream-selection source")


def test_cyclic_feedback_shadow_contains_only_registered_typed_query_handles():
    trace = _artifact(_run(), "agenda_feedback", "seed0-bit0")["trace"]
    state = next(item for item in trace["thinker_states"] if item["round_index"] == 0)
    own_registry = next(
        item for item in state["query_registry"]
        if item["query_key"] == "q:local-effect"
    )
    assert own_registry == {
        "query_key": "q:local-effect",
        "subject_entity_id": next(
            item["concept_id"] for item in trace["concepts"]
            if item["semantic_hash"] == VALVE
        ),
        "relation_id": "changes",
    }
    confusion = trace["thinker_confusions"][0]
    desire = trace["thinker_desires"][0]
    agenda = trace["agendas"][0]
    assert set(confusion) >= {
        "query_key", "subject_entity_id", "relation_id", "unknown_slot",
    }
    assert not ({"unresolved_dependency", "attempted_queries", "missing_semantic_keys"}
                & set(confusion))
    assert not ({"target_query", "source_thinker_ids"} & set(desire))
    assert desire["source_confusion_id"] == confusion["confusion_id"]
    assert desire["query_key"] == confusion["query_key"] == "q:local-effect"
    assert agenda["priority_query_keys"] == [desire["query_key"]]
    assert "priority_queries" not in agenda


def test_checkpoint_to_thinker_snapshot_compiler_is_explicit_and_injectable():
    class AuditedCompiler(DeterministicTextSnapshotCompiler):
        compiler_id = "audited-test-snapshot-compiler"

        def __init__(self):
            self.seen = []

        def compile(self, checkpoint):
            self.seen.append((checkpoint.logical_life_id, checkpoint.round_index,
                              checkpoint.semantic_state_hash))
            return super().compile(checkpoint)

    compiler = AuditedCompiler()
    result = run_recurrent_text_experiment(
        lives=[_life(0, 0), _life(1, 0)],
        dreamer=GoldLocalDreamer(), thinker=GoldThinker(),
        snapshot_compiler=compiler,
    )
    assert len(compiler.seen) == 2 + 3 * 2  # shared THINK_0, then one per arm/life
    for item in result["artifacts"]:
        assert item["controller_condition"] == \
            "scripted-gold-thinker/read-plan ceiling"
        assert all(
            binding["snapshot_compiler_id"] == compiler.compiler_id
            for binding in item["checkpoint_snapshot_bindings"]
        )
        assert all(binding["cyclic_checkpoint_id"]
                   for binding in item["checkpoint_snapshot_bindings"])


def test_hardened_thinker_agenda_maps_through_unique_system_registry_key():
    class CaptureThinker(GoldThinker):
        def __init__(self):
            self.requests = []

        def think(self, request):
            self.requests.append(request)
            return super().think(request)

    thinker = CaptureThinker()
    run_recurrent_text_experiment(
        lives=[_life(0, 0), _life(1, 0)],
        dreamer=GoldLocalDreamer(), thinker=thinker,
    )
    request = next(item for item in thinker.requests if item.round_index == 0)
    agenda = {
        "schema_version": THINKER_SCHEMA_VERSION,
        "agenda_id": "agenda-test",
        "world_id": request.world_id, "skin_id": request.skin_id,
        "life_id": request.life_id,
        "checkpoint_id": request.checkpoint_id,
        "checkpoint_hash": request.checkpoint_hash,
        "source_checkpoint_hash": request.checkpoint_semantic_hash,
        "round_index": request.round_index,
        "thinker_trace_hash": "1" * 64,
        "reset_policy": THINKER_RESET_POLICY,
        "items": [{
            "agenda_item_id": "agenda-item-1",
            "source_desire_id": "desire-1",
            "kind": "MISSING_DEPENDENCY",
            "query_key": "q:local-effect",
            "subject_entity_id": "entity:local-valve", "relation_id": "changes",
            "unknown_slot": "object", "priority": 1,
            "non_evidentiary": True,
        }],
        "non_evidentiary": True,
    }
    agenda["agenda_hash"] = thinker_digest(agenda)
    queries = agenda_queries_from_hardened_thinker(agenda, request)
    assert len(queries) == 1
    assert queries[0].query_key == "q:local-effect"
    assert queries[0].right_id == "place:local-target"
    assert queries[0].source_checkpoint_hash == request.checkpoint_hash


def test_dream_cannot_cite_a_public_event_outside_its_bounded_local_view():
    class LeakingDreamer(GoldLocalDreamer):
        def dream(self, request):
            if request.stage == "RETURN_SLEEP" and request.selection_queries:
                return SemanticDecision.edge(
                    source_semantic_hash=VALVE, relation="changes",
                    target_semantic_hash=TARGET, rule="attempt foreign evidence",
                    premises=(PremiseIdentity("experience", "f" * 64),),
                )
            return super().dream(request)

    try:
        run_recurrent_text_experiment(
            lives=[_life(0, 0), _life(1, 0)],
            dreamer=LeakingDreamer(), thinker=GoldThinker(),
        )
    except SchedulerError as exc:
        assert "outside its bounded view" in str(exc)
    else:
        raise AssertionError("foreign/unseen public evidence was accepted")


def test_each_final_think_has_fresh_state_and_no_think0_scratch_parent():
    result = _run()
    for item in result["artifacts"]:
        trace = item["trace"]
        final_state = next(
            state for state in trace["thinker_states"] if state["round_index"] == 1
        )
        first_state = next(
            state for state in trace["thinker_states"] if state["round_index"] == 0
        )
        assert final_state["parent_state_id"] is None
        assert item["final_think"]["request"]["fresh_workspace"] is True
        assert final_state["workspace"] != first_state["workspace"]
        assert first_state["goal"] != final_state["goal"]


def test_phase_barriers_checkpoint_hashes_and_life_isolation_are_exact():
    result = _run()
    traces = [item["trace"] for item in result["artifacts"]]
    dataset = {
        "schema_version": traces[0]["schema_version"],
        "dataset_id": "all-arms", "traces": traces,
    }
    assert validate_dataset(dataset) == []
    assert len({trace["memory_adapter_id"] for trace in traces}) == len(traces)
    damaged = deepcopy(traces[0])
    damaged["checkpoints"][0]["semantic_state_hash"] = "0" * 64
    errors = validate_trace(damaged)
    assert any("semantic_state_hash: mismatch" in error for error in errors)
    assert any("record_refs: not an exact manifest" in error for error in errors)


def test_round_deltas_bind_calls_semantics_realizations_checkpoint_think_and_agenda():
    item = _artifact(_run(), "agenda_feedback", "seed0-bit0")
    assert len(item["round_deltas"]) == 2
    first, second = item["round_deltas"]
    assert len(first["dream_call_hashes"]) == 84
    assert len(second["dream_call_hashes"]) == 16
    assert len(first["created_semantic_hashes"]) == 4
    assert second["created_semantic_hashes"] == [EFFECT]
    assert len(first["realization_hashes"]) == 16
    assert len(second["realization_hashes"]) == 4
    assert first["checkpoint_id"] == item["trace"]["checkpoints"][0]["checkpoint_id"]
    assert second["agenda_hash"] == item["trace"]["agendas"][1]["agenda_hash"]
    assert first["thinker_state_hashes"] and second["thinker_state_hashes"]


def test_realization_fanout_changes_write_count_not_semantic_structure_or_depth():
    result = _run()
    agenda = _artifact(result, "agenda_feedback", "seed0-bit0")["trace"]
    metrics = compute_metrics(agenda)
    assert metrics["structure"]["concept_count"] == 3
    assert metrics["structure"]["edge_count"] == 2
    assert metrics["realization_count"] == 4 * (
        metrics["structure"]["concept_count"] + metrics["structure"]["edge_count"]
    )
    assert metrics["derivation_lineage_depth"] == 3
    assert metrics["semantic_structural_hops"] == 2
    no_feedback = _artifact(result, "no_feedback", "seed0-bit0")["trace"]
    no_metrics = compute_metrics(no_feedback)
    assert no_metrics["structure"]["concept_count"] == 3
    assert no_metrics["structure"]["edge_count"] == 1
    assert no_metrics["realization_count"] == 16


def test_pair_scoring_uses_both_members_as_primary_unit():
    expectations = [
        FinalExpectation("pair0", "seed0-bit0", "A"),
        FinalExpectation("pair0", "seed0-bit1", "B"),
        FinalExpectation("pair1", "seed1-bit0", "C"),
        FinalExpectation("pair1", "seed1-bit1", "D"),
    ]
    score = score_final_pairs(expectations, {
        "seed0-bit0": "A", "seed0-bit1": "wrong",
        "seed1-bit0": "C", "seed1-bit1": "D",
    })
    assert score.n_pairs == 2
    assert score.both_correct == 1
    assert score.paired_both_correct == 0.5
    assert score.member_correct == 3
    assert score.member_accuracy == 0.75


def test_shuffle_donor_rejects_only_latent_twins_of_one_seed():
    try:
        deterministic_shuffle_donors([_life(0, 0), _life(0, 1)])
    except SchedulerError as exc:
        assert "distinct world seeds" in str(exc)
    else:
        raise AssertionError("latent twins were accepted as shuffled negative controls")
