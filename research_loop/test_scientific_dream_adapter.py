"""CPU adversarial tests for the provider-bound scientific dream adapter."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
import hashlib
import json
import time

from .model_provider_boundary import (
    IsolatedModelProviderBoundary,
    ProviderCallScope,
    ProviderExchange,
    ProviderExpectations,
    sha256_bytes,
)
from .recurrent_text_organism import (
    AgendaQuery,
    DreamRequest,
    MemoryItemView,
    PremiseIdentity,
    PublicExperience,
    SCIENTIFIC_CAUSAL_JOIN_RELATION,
    SemanticDecision,
)
from .scientific_dream_adapter import (
    ScientificDreamAdapter,
    ScientificDreamConfig,
    ScientificDreamError,
    V03RMechanicalSemanticAdmission,
    canonical_target_blind_request,
)


def _hash(label: str) -> str:
    return hashlib.sha256(label.encode()).hexdigest()


SOURCE_HASH = _hash("source")
TARGET_HASH = _hash("target")
ROUTE_HASH = _hash("route-c1")
EFFECT_HASH = _hash("effect-c1")
WRONG_ROUTE_HASH = _hash("route-c2")
SOURCE_ENTITY = "entity:source:public_source"
TARGET_ENTITY = "entity:target:public_target"


def _memory() -> tuple[MemoryItemView, ...]:
    return (
        MemoryItemView(
            SOURCE_HASH, "concept", SOURCE_ENTITY, "supported",
            entity_id=SOURCE_ENTITY,
        ),
        MemoryItemView(
            TARGET_HASH, "concept", TARGET_ENTITY, "supported",
            entity_id=TARGET_ENTITY,
        ),
        MemoryItemView(
            ROUTE_HASH, "concept",
            f"route_record connector=connector_1 source={SOURCE_ENTITY}",
            "supported", entity_id="record:route:connector_1",
        ),
        MemoryItemView(
            EFFECT_HASH, "concept",
            f"effect_record connector=connector_1 target={TARGET_ENTITY} observed=changed",
            "supported", entity_id="record:effect:connector_1",
        ),
        MemoryItemView(
            WRONG_ROUTE_HASH, "concept",
            f"route_record connector=connector_2 source={SOURCE_ENTITY}",
            "supported", entity_id="record:route:connector_2",
        ),
    )


def _query() -> AgendaQuery:
    return AgendaQuery(
        query_key="q:private-control-name",
        kind="missing_dependency", left_id=SOURCE_ENTITY,
        relation_id=SCIENTIFIC_CAUSAL_JOIN_RELATION, right_id=TARGET_ENTITY,
        source_checkpoint_hash=_hash("checkpoint"),
        source_goal_id="private-final-goal-id",
        vocabulary_hash=_hash("vocabulary"),
    )


def _request(
    *, logical_life: str = "LOGICAL_LIFE_SENTINEL",
    selection_mode: str = "agenda_feedback_CONTROL_SENTINEL",
    donor: str | None = "DONOR_LIFE_SENTINEL",
    memory: tuple[MemoryItemView, ...] | None = None,
) -> DreamRequest:
    return DreamRequest(
        logical_life_id=logical_life, round_index=1, stage="RETURN_SLEEP",
        call_index=3, trigger_id="TRIGGER_CONTROL_SENTINEL",
        visible_experiences=(PublicExperience(
            "public-record-id", 4, "inspect public mechanism",
            "public observation", "public outcome",
        ),),
        memory=memory if memory is not None else _memory(),
        selection_queries=(_query(),), selection_mode=selection_mode,
        selection_donor_life_id=donor, declared_semantic_neighbor_k=6,
        full_memory_ceiling=False, non_evidentiary_selection=True,
    )


EXPECTATIONS = ProviderExpectations(
    provider="fake-provider", model="fake-model", model_revision="rev-1",
    tokenizer_id="fake-tokenizer", tokenizer_revision="tok-rev-1",
)
CONFIG = ScientificDreamConfig(temperature=0.0, top_p=1.0, max_output_tokens=128, seed=7)


def _scope(label: str = "call") -> ProviderCallScope:
    return ProviderCallScope(
        call_id=_hash(label), run_id=_hash("run"), life_id=_hash("life"),
        arm="agenda_feedback", round_index=1, stage="RETURN_SLEEP", call_index=3,
    )


def _scope_at(label: str, *, round_index: int, stage: str,
              call_index: int) -> ProviderCallScope:
    return ProviderCallScope(
        call_id=_hash(label), run_id=_hash("run"), life_id=_hash("life"),
        arm="agenda_feedback", round_index=round_index, stage=stage,
        call_index=call_index,
    )


def _witness(
    label: str, outcome: str, public_record: dict,
    *, observation_extra: dict | None = None,
) -> PublicExperience:
    observation = {"text": f"public witness {label}", "public_record": public_record}
    if observation_extra:
        observation.update(observation_extra)
    return PublicExperience(
        f"public-{label}", 0, "observe",
        json.dumps(observation, sort_keys=True, separators=(",", ":")), outcome,
    )


def _concept_response(
    experience: PublicExperience, canonical_key: str, display_label: str,
    *, premises: list[dict[str, str]] | None = None,
) -> bytes:
    return json.dumps({
        "kind": "CREATE_CONCEPT", "canonical_key": canonical_key,
        "display_label": display_label,
        "rule": "compress exactly one public witnessed record",
        "premises": premises if premises is not None else [{
            "kind": "experience", "identity": experience.payload_hash,
        }],
    }, sort_keys=True, separators=(",", ":")).encode()


def _edge_response(
    *, route_hash: str = ROUTE_HASH, effect_hash: str = EFFECT_HASH,
    source_hash: str = SOURCE_HASH, target_hash: str = TARGET_HASH,
    relation: str = SCIENTIFIC_CAUSAL_JOIN_RELATION,
    extra: dict | None = None, premise_kind: str = "concept",
) -> bytes:
    value = {
        "kind": "CREATE_EDGE", "source_semantic_hash": source_hash,
        "relation": relation, "target_semantic_hash": target_hash,
        "rule": "join a witnessed route and effect over one public connector",
        "premises": [
            {"kind": "concept", "identity": source_hash},
            {"kind": "concept", "identity": target_hash},
            {"kind": premise_kind, "identity": route_hash},
            {"kind": "concept", "identity": effect_hash},
        ],
    }
    if extra:
        value.update(extra)
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


class ResponseFactory:
    def __init__(self, responses: list[bytes]) -> None:
        self.responses = list(responses)
        self.calls: list[tuple[bytes, bytes]] = []
        self.serial = 0

    def open_fresh_session(self):
        serial = self.serial
        self.serial += 1
        factory = self

        class Session:
            def invoke(self, request_bytes: bytes, config_bytes: bytes):
                factory.calls.append((request_bytes, config_bytes))
                response = factory.responses.pop(0)
                started = time.time_ns()
                receipt = {
                    "schema_version": "provider-call-receipt-v1.0",
                    "provider": EXPECTATIONS.provider,
                    "model": EXPECTATIONS.model,
                    "model_revision": EXPECTATIONS.model_revision,
                    "provider_session_id": f"session-{serial}",
                    "provider_request_id": f"request-{serial}",
                    "fresh_session": True, "turn_index": 0,
                    "request_sha256": sha256_bytes(request_bytes),
                    "request_byte_count": len(request_bytes),
                    "config_sha256": sha256_bytes(config_bytes),
                    "config_byte_count": len(config_bytes),
                    "raw_response_sha256": sha256_bytes(response),
                    "raw_response_byte_count": len(response),
                    "provider_started_at_unix_ns": started,
                    "provider_ended_at_unix_ns": time.time_ns(),
                    "token_evidence": {
                        "mode": "EXACT_COUNTS", "source": "PROVIDER_RESPONSE",
                        "tokenizer_id": EXPECTATIONS.tokenizer_id,
                        "tokenizer_revision": EXPECTATIONS.tokenizer_revision,
                        "supplied_token_count": 100, "generated_token_count": 30,
                        "supplied_token_ids_sha256": None,
                        "generated_token_ids_sha256": None,
                    },
                }
                return ProviderExchange(
                    response,
                    json.dumps(receipt, sort_keys=True, separators=(",", ":")).encode(),
                )

            def close(self):
                pass

        return Session()


def _adapter(response: bytes):
    factory = ResponseFactory([response])
    adapter = ScientificDreamAdapter(
        IsolatedModelProviderBoundary(factory), EXPECTATIONS,
        V03RMechanicalSemanticAdmission(),
    )
    return adapter, factory


def _assert_raises(expected: type[Exception], fragment: str, function) -> None:
    try:
        function()
    except expected as exc:
        assert fragment in str(exc), str(exc)
    else:
        raise AssertionError(f"expected {expected.__name__}: {fragment}")


def test_target_blind_bytes_exclude_life_arm_donor_control_goal_and_scorer_ids():
    request = _request()
    encoded = canonical_target_blind_request(request)
    lowered = encoded.lower()
    for forbidden in (
        b"logical_life", b"logical_life_sentinel", b"agenda_feedback",
        b"control_sentinel", b"donor_life_sentinel", b"private-final-goal-id",
        b"q:private-control-name", b"trigger_control_sentinel", b"scorer",
        b"final_goal", b"answer_valve", b"ground_truth",
    ):
        assert forbidden not in lowered
    payload = json.loads(encoded)
    assert payload["selection_focus"] == [{
        "kind": "missing_dependency", "left_id": SOURCE_ENTITY,
        "relation_id": SCIENTIFIC_CAUSAL_JOIN_RELATION,
        "right_id": TARGET_ENTITY,
    }]
    assert payload["constraints"]["selection_focus_is_evidence"] is False
    twin = _request(
        logical_life="OTHER_PRIVATE_LIFE", selection_mode="matched_distractor",
        donor="OTHER_PRIVATE_DONOR",
    )
    assert canonical_target_blind_request(twin) == encoded


def test_provider_receives_only_exact_canonical_request_and_config_bytes():
    adapter, factory = _adapter(b'{"kind":"PASS"}')
    result = adapter.execute(_request(), _scope(), CONFIG)
    assert factory.calls == [(
        canonical_target_blind_request(_request()), CONFIG.exact_bytes(),
    )]
    assert result.provider_artifact.request_bytes == factory.calls[0][0]
    assert result.provider_artifact.config_bytes == factory.calls[0][1]
    assert result.parser_outcome == "PARSED"
    assert result.admitted_decision == SemanticDecision.pass_()


def test_direct_completed_decision_is_forbidden_before_provider_call():
    adapter, factory = _adapter(b'{"kind":"PASS"}')
    _assert_raises(
        ScientificDreamError, "forbids a direct completed",
        lambda: adapter.execute(
            _request(), _scope(), CONFIG,
            direct_completed_decision=SemanticDecision.pass_(),
        ),
    )
    assert factory.calls == []


def test_valid_causal_join_is_supported_only_by_mechanical_admission():
    adapter, _ = _adapter(_edge_response())
    result = adapter.execute(_request(), _scope(), CONFIG)
    assert result.parser_outcome == "PARSED"
    assert result.proposed_decision is not None
    assert result.proposed_decision.mark_supported is False
    assert result.admission_outcome == "ADMITTED_SUPPORTED"
    assert result.admitted_decision is not None
    assert result.admitted_decision.mark_supported is True
    assert result.admitted_decision.relation == SCIENTIFIC_CAUSAL_JOIN_RELATION
    try:
        result.admission_reason = "changed"  # type: ignore[misc]
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError("scientific result is not immutable")


def test_public_witness_chain_supports_four_concepts_then_causal_join():
    source_experience = _witness(
        "source", "source_anchor_color",
        {
            "anchor_id": "animal_00", "source_id": "public_source",
            "label": "red", "ratio": [1, 0, 0],
        },
    )
    target_experience = _witness(
        "target", "target_passive_baseline",
        {
            "target_id": "public_target", "anchor_id": "animal_00",
            "label": "purple", "ratio": [1, 0, 1],
        },
    )
    route_experience = _witness(
        "route", "valve_route",
        {"valve_id": "connector_1", "source_id": "public_source"},
    )
    effect_experience = _witness(
        "effect", "intervention_effect",
        {
            "valve_id": "connector_1", "target_id": "public_target",
            "effect": "CHANGE",
        },
    )
    concepts = (
        (
            source_experience, SOURCE_ENTITY, SOURCE_ENTITY,
        ),
        (
            target_experience, TARGET_ENTITY, TARGET_ENTITY,
        ),
        (
            route_experience,
            f"record:route:connector_1:{SOURCE_ENTITY}",
            f"route_record connector=connector_1 source={SOURCE_ENTITY}",
        ),
        (
            effect_experience,
            f"record:effect:connector_1:{TARGET_ENTITY}:CHANGE",
            f"effect_record connector=connector_1 target={TARGET_ENTITY} observed=CHANGE",
        ),
    )
    responses = [
        _concept_response(experience, key, label)
        for experience, key, label in concepts
    ]
    factory = ResponseFactory(responses)
    adapter = ScientificDreamAdapter(
        IsolatedModelProviderBoundary(factory), EXPECTATIONS,
        V03RMechanicalSemanticAdmission(),
    )
    memory: list[MemoryItemView] = []
    admitted_by_key: dict[str, MemoryItemView] = {}
    for index, (experience, key, label) in enumerate(concepts):
        request = replace(
            _request(), round_index=0, stage="WAKE", call_index=index,
            visible_experiences=(experience,), memory=tuple(memory),
            selection_queries=(), selection_mode="none",
            selection_donor_life_id=None,
        )
        result = adapter.execute(
            request,
            _scope_at(
                f"witness-{index}", round_index=0, stage="WAKE",
                call_index=index,
            ),
            CONFIG,
        )
        assert result.parser_outcome == "PARSED"
        assert result.admission_outcome == "ADMITTED_SUPPORTED"
        decision = result.admitted_decision
        assert decision is not None and decision.mark_supported is True
        assert decision.canonical_key == key and decision.display_label == label
        semantic_hash = decision.conclusion_semantic_hash
        assert semantic_hash is not None
        view = MemoryItemView(
            semantic_hash, "concept", label, "supported", entity_id=key,
        )
        memory.append(view)
        admitted_by_key[key] = view

    source_view = admitted_by_key[SOURCE_ENTITY]
    target_view = admitted_by_key[TARGET_ENTITY]
    route_view = admitted_by_key[f"record:route:connector_1:{SOURCE_ENTITY}"]
    effect_view = admitted_by_key[
        f"record:effect:connector_1:{TARGET_ENTITY}:CHANGE"
    ]
    factory.responses.append(_edge_response(
        source_hash=source_view.semantic_hash,
        target_hash=target_view.semantic_hash,
        route_hash=route_view.semantic_hash,
        effect_hash=effect_view.semantic_hash,
    ))
    edge_request = replace(
        _request(), visible_experiences=(), memory=tuple(memory),
        round_index=1, stage="RETURN_SLEEP", call_index=0,
    )
    edge_result = adapter.execute(
        edge_request,
        _scope_at("causal-edge", round_index=1, stage="RETURN_SLEEP", call_index=0),
        CONFIG,
    )
    assert edge_result.parser_outcome == "PARSED"
    assert edge_result.admission_outcome == "ADMITTED_SUPPORTED"
    assert edge_result.admitted_decision is not None
    assert edge_result.admitted_decision.mark_supported is True
    assert len(factory.calls) == 5


def test_public_witness_concept_mutations_fail_mechanical_admission():
    valid_record = {
        "anchor_id": "animal_00", "source_id": "public_source",
        "label": "red", "ratio": [1, 0, 0],
    }
    valid_experience = _witness(
        "valid-source", "source_anchor_color", valid_record,
    )
    extra_experience = _witness(
        "extra-route", "valve_route",
        {"valve_id": "connector_1", "source_id": "public_source"},
    )
    mutations = (
        (
            _witness("wrong-kind", "animal_source_color", valid_record),
            SOURCE_ENTITY, SOURCE_ENTITY, None,
            "kind cannot witness",
        ),
        (
            _witness(
                "extra-field", "source_anchor_color",
                {**valid_record, "unexpected": "not-public-schema"},
            ),
            SOURCE_ENTITY, SOURCE_ENTITY, None, "exact fields",
        ),
        (
            valid_experience, "entity:source:wrong", SOURCE_ENTITY, None,
            "canonical key does not match",
        ),
        (
            valid_experience, SOURCE_ENTITY, "wrong display label", None,
            "display label does not match",
        ),
        (
            valid_experience, SOURCE_ENTITY, SOURCE_ENTITY,
            [
                {"kind": "experience", "identity": valid_experience.payload_hash},
                {"kind": "experience", "identity": extra_experience.payload_hash},
            ],
            "exactly one experience witness",
        ),
        (
            _witness(
                "extra-observation", "source_anchor_color", valid_record,
                observation_extra={"unexpected": "not-public-schema"},
            ),
            SOURCE_ENTITY, SOURCE_ENTITY, None, "exact fields",
        ),
        (
            _witness(
                "wrong-anchor", "source_anchor_color",
                {**valid_record, "anchor_id": "animal_01"},
            ),
            SOURCE_ENTITY, SOURCE_ENTITY, None, "animal_00 anchor",
        ),
    )
    for index, (experience, key, label, premises, reason) in enumerate(mutations):
        visible = (
            (experience, extra_experience)
            if premises is not None else (experience,)
        )
        adapter, _ = _adapter(
            _concept_response(experience, key, label, premises=premises)
        )
        request = replace(
            _request(), round_index=0, stage="WAKE", call_index=0,
            visible_experiences=visible, memory=(), selection_queries=(),
            selection_mode="none", selection_donor_life_id=None,
        )
        result = adapter.execute(
            request,
            _scope_at(
                f"mutation-{index}", round_index=0, stage="WAKE", call_index=0,
            ),
            CONFIG,
        )
        assert result.parser_outcome == "PARSED"
        assert result.admission_outcome == "REJECTED"
        assert result.admitted_decision is None
        assert reason in result.admission_reason


def test_wrong_connector_and_wrong_endpoint_are_parsed_but_not_admitted():
    alternate_source_hash = _hash("alternate-source")
    alternate_source = MemoryItemView(
        alternate_source_hash, "concept", "entity:source:other", "supported",
        entity_id="entity:source:other",
    )
    for response, request, reason in (
        (
            _edge_response(route_hash=WRONG_ROUTE_HASH), _request(),
            "connectors do not match",
        ),
        (
            _edge_response(source_hash=alternate_source_hash),
            _request(memory=(*_memory(), alternate_source)),
            "route/effect records do not match edge endpoints",
        ),
    ):
        adapter, _ = _adapter(response)
        result = adapter.execute(request, _scope(), CONFIG)
        assert result.parser_outcome == "PARSED"
        assert result.admission_outcome == "REJECTED"
        assert result.admitted_decision is None
        assert reason in result.admission_reason


def test_out_of_view_and_agenda_only_citations_never_reach_admission():
    for response, fragment in (
        (
            _edge_response(route_hash=_hash("not-in-view")),
            "outside bounded view",
        ),
        (
            _edge_response(premise_kind="agenda"),
            "premise kind is not local evidence",
        ),
    ):
        adapter, _ = _adapter(response)
        result = adapter.execute(_request(), _scope(), CONFIG)
        assert result.parser_outcome == "REJECTED"
        assert result.proposed_decision is None
        assert result.admitted_decision is None
        assert fragment in str(result.parser_error)


def test_mark_supported_and_answer_bearing_fields_are_strictly_rejected():
    for extra in (
        {"mark_supported": True},
        {"answer_valve_id": "answer-bearing"},
        {"final_answer": "changed"},
        {"scorer_truth": True},
    ):
        adapter, _ = _adapter(_edge_response(extra=extra))
        result = adapter.execute(_request(), _scope(), CONFIG)
        assert result.parser_outcome == "REJECTED"
        assert result.admission_outcome == "REJECTED"
        assert result.admitted_decision is None
        assert "exact fields" in str(result.parser_error)


def test_unrelated_or_provisional_route_effect_memory_cannot_support_join():
    unrelated = tuple(
        replace(
            item,
            canonical_text=(
                "effect_record connector=connector_1 "
                "target=entity:target:other observed=changed"
            ),
        ) if item.semantic_hash == EFFECT_HASH else item
        for item in _memory()
    )
    provisional = tuple(
        replace(item, status="provisional")
        if item.semantic_hash == ROUTE_HASH else item
        for item in _memory()
    )
    for memory, reason in (
        (unrelated, "do not match edge endpoints"),
        (provisional, "must already be supported"),
    ):
        adapter, _ = _adapter(_edge_response())
        result = adapter.execute(_request(memory=memory), _scope(), CONFIG)
        assert result.parser_outcome == "PARSED"
        assert result.admission_outcome == "REJECTED"
        assert reason in result.admission_reason


def test_non_causal_local_proposal_remains_provisional_and_cannot_gain_support():
    response = json.dumps({
        "kind": "CREATE_CONCEPT", "canonical_key": "concept:new-local",
        "display_label": "one local abstraction", "rule": "compress local evidence",
        "premises": [{
            "kind": "experience",
            "identity": _request().visible_experiences[0].payload_hash,
        }],
    }, sort_keys=True, separators=(",", ":")).encode()
    adapter, _ = _adapter(response)
    result = adapter.execute(_request(), _scope(), CONFIG)
    assert result.parser_outcome == "PARSED"
    assert result.admission_outcome == "ADMITTED_PROVISIONAL"
    assert result.admitted_decision is not None
    assert result.admitted_decision.mark_supported is False


def test_reinforce_cannot_launder_model_selected_support():
    response = json.dumps({
        "kind": "REINFORCE", "subject_semantic_hash": SOURCE_HASH,
        "rule": "model asks to strengthen this memory",
        "premises": [{"kind": "concept", "identity": SOURCE_HASH}],
    }, sort_keys=True, separators=(",", ":")).encode()
    adapter, _ = _adapter(response)
    result = adapter.execute(_request(), _scope(), CONFIG)
    assert result.parser_outcome == "PARSED"
    assert result.proposed_decision is not None
    assert result.proposed_decision.mark_supported is False
    assert result.admission_outcome == "REJECTED"
    assert result.admitted_decision is None
    assert "independent mechanical support policy" in result.admission_reason


def test_scope_position_mismatch_fails_before_provider_call():
    adapter, factory = _adapter(b'{"kind":"PASS"}')
    _assert_raises(
        ScientificDreamError, "scope does not match",
        lambda: adapter.execute(
            _request(), replace(_scope(), round_index=0), CONFIG,
        ),
    )
    assert factory.calls == []
