"""CPU-only artifact contract for a cyclic dream -> memory -> think organism.

This is deliberately a *contract*, not a model runner.  It represents the
organism as an append-only sequence of committed phases.  Dreaming may create
one local semantic item at a time, realization may render an existing item in
many training forms, and thinking may construct temporary goal-conditioned
hypotheses.  Thinker confusions and desires may steer the next dream agenda,
but they are never evidence.

The distinction is important:

* semantic structure is the graph of unique concepts and edges;
* derivation depth is the provenance DAG over those semantic items;
* realizations/touches are write pressure for an adapter and affect neither;
* thinker hypotheses are temporary working state and affect neither.

Every JSON-shaped record is scope-bound to one life.  The validator is strict
and dependency-free so it can gate artifacts before any GPU/model code exists.
"""

from __future__ import annotations

from collections import Counter, deque
from collections.abc import Mapping, Sequence
import hashlib
import json
import re
from typing import Any, Literal, TypedDict


SCHEMA_VERSION = "cyclic-organism-v1.0"
PHASES = (
    "EXPERIENCE", "DREAM", "REALIZE", "CHECKPOINT", "THINK", "FEEDBACK",
)
SEMANTIC_KINDS = frozenset({"concept", "semantic_edge"})
PREMISE_KINDS = frozenset({"experience", "concept", "semantic_edge"})
REALIZATION_FORMS = frozenset({
    "canonical", "qa", "reverse", "paraphrase", "partial_cue", "contrast",
})
EPISTEMIC_STATUSES = frozenset({
    "provisional", "supported", "contradicted", "superseded",
})
_SHA256 = re.compile(r"[0-9a-f]{64}")
_HANDLE = re.compile(r"[A-Za-z][A-Za-z0-9_.:-]{0,127}")


class ContractError(ValueError):
    """Raised when a cyclic-organism artifact violates this contract."""


class Scope(TypedDict):
    world_id: str
    skin_id: str
    life_id: str


class RecordRef(TypedDict):
    kind: str
    id: str
    record_hash: str


class PremiseRef(TypedDict):
    kind: Literal["experience", "concept", "semantic_edge"]
    id: str


class Experience(TypedDict):
    experience_id: str
    world_id: str
    skin_id: str
    life_id: str
    round_index: int
    sequence_index: int
    action: str
    observation: str
    outcome: str
    payload_hash: str
    created_barrier_id: str


class Concept(TypedDict):
    concept_id: str
    world_id: str
    skin_id: str
    life_id: str
    round_index: int
    step_index: int
    canonical_key: str
    display_label: str
    semantic_hash: str
    derivation_id: str
    initial_status: Literal["provisional"]
    created_barrier_id: str


class SemanticEdge(TypedDict):
    edge_id: str
    world_id: str
    skin_id: str
    life_id: str
    round_index: int
    step_index: int
    source_concept_id: str
    relation: str
    target_concept_id: str
    semantic_hash: str
    derivation_id: str
    initial_status: Literal["provisional"]
    created_barrier_id: str


class Derivation(TypedDict):
    derivation_id: str
    world_id: str
    skin_id: str
    life_id: str
    round_index: int
    step_index: int
    rule: str
    conclusion_kind: Literal["concept", "semantic_edge"]
    conclusion_id: str
    premise_refs: list[PremiseRef]
    guidance_agenda_ids: list[str]
    declared_depth: int
    derivation_hash: str
    created_barrier_id: str


class EpistemicEvent(TypedDict):
    epistemic_event_id: str
    world_id: str
    skin_id: str
    life_id: str
    round_index: int
    step_index: int
    event_kind: Literal["CREATE", "SUPPORT", "CONTRADICT", "SUPERSEDE"]
    subject_kind: Literal["concept", "semantic_edge"]
    subject_id: str
    previous_status: str | None
    new_status: str
    evidence_derivation_id: str
    replacement_subject_id: str | None
    created_barrier_id: str


class RealizationSpec(TypedDict):
    realization_id: str
    world_id: str
    skin_id: str
    life_id: str
    round_index: int
    source_kind: Literal["concept", "semantic_edge"]
    source_id: str
    source_semantic_hash: str
    form: str
    cue_text: str
    target_text: str
    realization_hash: str
    created_barrier_id: str


class TouchPlan(TypedDict):
    touch_plan_id: str
    world_id: str
    skin_id: str
    life_id: str
    round_index: int
    realization_id: str
    touches: int
    weight: float
    order_index: int
    plan_hash: str
    created_barrier_id: str


class MemoryCheckpoint(TypedDict):
    checkpoint_id: str
    world_id: str
    skin_id: str
    life_id: str
    round_index: int
    memory_adapter_id: str
    previous_checkpoint_id: str | None
    included_semantic_ids: list[str]
    realization_ids: list[str]
    touch_plan_ids: list[str]
    semantic_state_hash: str
    realization_state_hash: str
    adapter_artifact_hash: str
    created_barrier_id: str


class ThinkerState(TypedDict):
    thinker_state_id: str
    world_id: str
    skin_id: str
    life_id: str
    round_index: int
    step_index: int
    checkpoint_id: str
    parent_state_id: str | None
    goal: str
    retrieved_semantic_ids: list[str]
    workspace: list[str]
    query_registry: list[dict[str, str]]
    state_hash: str
    created_barrier_id: str


class ThinkerHypothesis(TypedDict):
    hypothesis_id: str
    world_id: str
    skin_id: str
    life_id: str
    round_index: int
    step_index: int
    thinker_state_id: str
    parent_hypothesis_ids: list[str]
    claim: str
    cited_semantic_ids: list[str]
    release_support_semantic_ids: list[str]
    confidence: float
    disposition: Literal["tentative", "released", "deferred"]
    hypothesis_hash: str
    created_barrier_id: str


class ThinkerConfusion(TypedDict):
    confusion_id: str
    world_id: str
    skin_id: str
    life_id: str
    round_index: int
    step_index: int
    thinker_state_id: str
    query_key: str
    subject_entity_id: str
    relation_id: str
    unknown_slot: Literal["object"]
    created_barrier_id: str


class ThinkerDesire(TypedDict):
    desire_id: str
    world_id: str
    skin_id: str
    life_id: str
    round_index: int
    source_confusion_id: str
    query_key: str
    subject_entity_id: str
    relation_id: str
    unknown_slot: Literal["object"]
    checkpoint_id: str
    checkpoint_semantic_state_hash: str
    thinker_state_hash: str
    priority: int
    non_evidentiary: Literal[True]
    created_barrier_id: str


class Agenda(TypedDict):
    agenda_id: str
    world_id: str
    skin_id: str
    life_id: str
    round_index: int
    checkpoint_id: str
    checkpoint_semantic_state_hash: str
    thinker_state_hash: str
    desire_ids: list[str]
    priority_query_keys: list[str]
    non_evidentiary: Literal[True]
    agenda_hash: str
    created_barrier_id: str


class PhaseBarrier(TypedDict):
    barrier_id: str
    world_id: str
    skin_id: str
    life_id: str
    barrier_index: int
    round_index: int
    phase: str
    previous_barrier_hash: str | None
    record_refs: list[RecordRef]
    barrier_hash: str


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def normalize_semantic_text(value: str) -> str:
    return " ".join(value.strip().casefold().split())


def experience_payload_hash(action: str, observation: str, outcome: str) -> str:
    return sha256_json({"action": action, "observation": observation, "outcome": outcome})


def concept_semantic_hash(canonical_key: str) -> str:
    return sha256_json({
        "kind": "concept", "canonical_key": normalize_semantic_text(canonical_key),
    })


def edge_semantic_hash(source_hash: str, relation: str, target_hash: str) -> str:
    return sha256_json({
        "kind": "semantic_edge",
        "source": source_hash,
        "relation": normalize_semantic_text(relation),
        "target": target_hash,
    })


def derivation_digest(rule: str, conclusion_hash: str,
                       premise_identities: Sequence[Mapping[str, str]]) -> str:
    premises = sorted(
        ({"kind": item["kind"], "identity": item["identity"]}
         for item in premise_identities),
        key=lambda item: (item["kind"], item["identity"]),
    )
    return sha256_json({
        "rule": normalize_semantic_text(rule),
        "conclusion_semantic_hash": conclusion_hash,
        "premises": premises,
    })


def realization_digest(source_semantic_hash: str, form: str,
                       cue_text: str, target_text: str) -> str:
    return sha256_json({
        "source_semantic_hash": source_semantic_hash,
        "form": form,
        "cue_text": cue_text,
        "target_text": target_text,
    })


def touch_plan_digest(realization_id: str, touches: int, weight: float,
                      order_index: int) -> str:
    return sha256_json({
        "realization_id": realization_id, "touches": touches,
        "weight": weight, "order_index": order_index,
    })


def thinker_state_digest(checkpoint_id: str, parent_state_id: str | None,
                         goal: str, retrieved_semantic_ids: Sequence[str],
                         workspace: Sequence[str],
                         query_registry: Sequence[Mapping[str, str]] = ()) -> str:
    return sha256_json({
        "checkpoint_id": checkpoint_id, "parent_state_id": parent_state_id,
        "goal": goal, "retrieved_semantic_ids": list(retrieved_semantic_ids),
        "workspace": list(workspace), "query_registry": list(query_registry),
    })


def hypothesis_digest(thinker_state_id: str, claim: str,
                      cited_semantic_ids: Sequence[str], confidence: float,
                      disposition: str,
                      parent_hypothesis_ids: Sequence[str] = (),
                      release_support_semantic_ids: Sequence[str] = ()) -> str:
    return sha256_json({
        "thinker_state_id": thinker_state_id, "claim": claim,
        "cited_semantic_ids": list(cited_semantic_ids),
        "confidence": confidence, "disposition": disposition,
        "parent_hypothesis_ids": list(parent_hypothesis_ids),
        "release_support_semantic_ids": list(release_support_semantic_ids),
    })


def agenda_digest(
    checkpoint_id: str,
    checkpoint_semantic_state_hash: str,
    thinker_state_hash: str,
    desire_ids: Sequence[str],
    priority_query_keys: Sequence[str],
) -> str:
    return sha256_json({
        "checkpoint_id": checkpoint_id,
        "checkpoint_semantic_state_hash": checkpoint_semantic_state_hash,
        "thinker_state_hash": thinker_state_hash,
        "desire_ids": list(desire_ids),
        "priority_query_keys": list(priority_query_keys),
        "non_evidentiary": True,
    })


def phase_barrier_digest(scope: Mapping[str, str], barrier_index: int,
                         round_index: int, phase: str,
                         previous_barrier_hash: str | None,
                         record_refs: Sequence[Mapping[str, str]]) -> str:
    return sha256_json({
        **{key: scope[key] for key in ("world_id", "skin_id", "life_id")},
        "barrier_index": barrier_index, "round_index": round_index,
        "phase": phase, "previous_barrier_hash": previous_barrier_hash,
        "record_refs": list(record_refs),
    })


_COMMON = {"world_id", "skin_id", "life_id", "round_index", "created_barrier_id"}
_SPECS: dict[str, tuple[str, str, frozenset[str], frozenset[str]]] = {
    "experiences": ("experience", "experience_id", frozenset(_COMMON | {
        "experience_id", "sequence_index", "action", "observation", "outcome",
        "payload_hash",
    }), frozenset(_COMMON | {"experience_id", "sequence_index", "action",
                             "observation", "outcome", "payload_hash"})),
    "concepts": ("concept", "concept_id", frozenset(_COMMON | {
        "concept_id", "step_index", "canonical_key", "display_label", "semantic_hash",
        "derivation_id", "initial_status",
    }), frozenset(_COMMON | {"concept_id", "step_index", "canonical_key",
                             "display_label", "semantic_hash", "derivation_id",
                             "initial_status"})),
    "semantic_edges": ("semantic_edge", "edge_id", frozenset(_COMMON | {
        "edge_id", "step_index", "source_concept_id", "relation",
        "target_concept_id", "semantic_hash", "derivation_id", "initial_status",
    }), frozenset(_COMMON | {"edge_id", "step_index", "source_concept_id",
                             "relation", "target_concept_id", "semantic_hash",
                             "derivation_id", "initial_status"})),
    "derivations": ("derivation", "derivation_id", frozenset(_COMMON | {
        "derivation_id", "step_index", "rule", "conclusion_kind", "conclusion_id",
        "premise_refs", "guidance_agenda_ids", "declared_depth", "derivation_hash",
    }), frozenset(_COMMON | {"derivation_id", "step_index", "rule",
                             "conclusion_kind", "conclusion_id", "premise_refs",
                             "guidance_agenda_ids", "declared_depth",
                             "derivation_hash"})),
    "epistemic_events": ("epistemic_event", "epistemic_event_id", frozenset(_COMMON | {
        "epistemic_event_id", "step_index", "event_kind", "subject_kind",
        "subject_id", "previous_status", "new_status", "evidence_derivation_id",
        "replacement_subject_id",
    }), frozenset(_COMMON | {"epistemic_event_id", "step_index", "event_kind",
                             "subject_kind", "subject_id", "previous_status",
                             "new_status", "evidence_derivation_id",
                             "replacement_subject_id"})),
    "realization_specs": ("realization_spec", "realization_id", frozenset(_COMMON | {
        "realization_id", "source_kind", "source_id", "source_semantic_hash", "form",
        "cue_text", "target_text", "realization_hash",
    }), frozenset(_COMMON | {"realization_id", "source_kind", "source_id",
                             "source_semantic_hash", "form", "cue_text", "target_text",
                             "realization_hash"})),
    "touch_plans": ("touch_plan", "touch_plan_id", frozenset(_COMMON | {
        "touch_plan_id", "realization_id", "touches", "weight", "order_index",
        "plan_hash",
    }), frozenset(_COMMON | {"touch_plan_id", "realization_id", "touches",
                             "weight", "order_index", "plan_hash"})),
    "checkpoints": ("checkpoint", "checkpoint_id", frozenset(_COMMON | {
        "checkpoint_id", "memory_adapter_id", "previous_checkpoint_id",
        "included_semantic_ids", "realization_ids", "touch_plan_ids",
        "semantic_state_hash", "realization_state_hash", "adapter_artifact_hash",
    }), frozenset(_COMMON | {"checkpoint_id", "memory_adapter_id",
                             "previous_checkpoint_id", "included_semantic_ids",
                             "realization_ids", "touch_plan_ids", "semantic_state_hash",
                             "realization_state_hash", "adapter_artifact_hash"})),
    "thinker_states": ("thinker_state", "thinker_state_id", frozenset(_COMMON | {
        "thinker_state_id", "step_index", "checkpoint_id", "parent_state_id", "goal",
        "retrieved_semantic_ids", "workspace", "query_registry", "state_hash",
    }), frozenset(_COMMON | {"thinker_state_id", "step_index", "checkpoint_id",
                             "parent_state_id", "goal", "retrieved_semantic_ids",
                             "workspace", "query_registry", "state_hash"})),
    "thinker_hypotheses": ("thinker_hypothesis", "hypothesis_id", frozenset(_COMMON | {
        "hypothesis_id", "step_index", "thinker_state_id", "parent_hypothesis_ids", "claim",
        "cited_semantic_ids", "release_support_semantic_ids", "confidence", "disposition",
        "hypothesis_hash",
    }), frozenset(_COMMON | {"hypothesis_id", "step_index", "thinker_state_id",
                             "parent_hypothesis_ids", "claim", "cited_semantic_ids",
                             "release_support_semantic_ids", "confidence", "disposition",
                             "hypothesis_hash"})),
    "thinker_confusions": ("thinker_confusion", "confusion_id", frozenset(_COMMON | {
        "confusion_id", "step_index", "thinker_state_id", "query_key",
        "subject_entity_id", "relation_id", "unknown_slot",
    }), frozenset(_COMMON | {"confusion_id", "step_index", "thinker_state_id",
                             "query_key", "subject_entity_id", "relation_id",
                             "unknown_slot"})),
    "thinker_desires": ("thinker_desire", "desire_id", frozenset(_COMMON | {
        "desire_id", "source_confusion_id", "query_key", "subject_entity_id",
        "relation_id", "unknown_slot", "checkpoint_id",
        "checkpoint_semantic_state_hash", "thinker_state_hash", "priority",
        "non_evidentiary",
    }), frozenset(_COMMON | {"desire_id", "source_confusion_id", "query_key",
                             "subject_entity_id", "relation_id", "unknown_slot",
                             "checkpoint_id", "checkpoint_semantic_state_hash",
                             "thinker_state_hash", "priority", "non_evidentiary"})),
    "agendas": ("agenda", "agenda_id", frozenset(_COMMON | {
        "agenda_id", "checkpoint_id", "checkpoint_semantic_state_hash",
        "thinker_state_hash", "desire_ids", "priority_query_keys",
        "non_evidentiary", "agenda_hash",
    }), frozenset(_COMMON | {"agenda_id", "checkpoint_id",
                             "checkpoint_semantic_state_hash", "thinker_state_hash",
                             "desire_ids", "priority_query_keys", "non_evidentiary",
                             "agenda_hash"})),
}

_PHASE_FOR_KIND = {
    "experience": "EXPERIENCE",
    "concept": "DREAM", "semantic_edge": "DREAM", "derivation": "DREAM",
    "epistemic_event": "DREAM",
    "realization_spec": "REALIZE", "touch_plan": "REALIZE",
    "checkpoint": "CHECKPOINT",
    "thinker_state": "THINK", "thinker_hypothesis": "THINK",
    "thinker_confusion": "THINK",
    "thinker_desire": "FEEDBACK", "agenda": "FEEDBACK",
}


def _is_nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_int(value: Any, *, minimum: int = 0) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= minimum


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _check_sha(value: Any, path: str, errors: list[str]) -> None:
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        errors.append(f"{path}: must be a lowercase SHA-256 digest")


def _duplicates(values: Sequence[Any]) -> set[Any]:
    counts = Counter(values)
    return {value for value, count in counts.items() if count > 1}


def _scope(trace: Mapping[str, Any]) -> dict[str, Any]:
    return {key: trace.get(key) for key in ("world_id", "skin_id", "life_id")}


def _exact_record_errors(record: Mapping[str, Any], allowed: frozenset[str],
                         required: frozenset[str], path: str,
                         errors: list[str]) -> None:
    for key in sorted(required - set(record)):
        errors.append(f"{path}: missing required field {key}")
    for key in sorted(set(record) - allowed):
        errors.append(f"{path}: forbidden or unknown field {key}")


def _record_catalog(trace: Mapping[str, Any], errors: list[str]) -> tuple[
        dict[str, tuple[str, Mapping[str, Any]]],
        dict[str, list[Mapping[str, Any]]],
    ]:
    catalog: dict[str, tuple[str, Mapping[str, Any]]] = {}
    by_kind: dict[str, list[Mapping[str, Any]]] = {}
    scope = _scope(trace)
    for top_key, (kind, id_key, allowed, required) in _SPECS.items():
        records = trace.get(top_key)
        if not isinstance(records, list):
            errors.append(f"{top_key}: must be a list")
            records = []
        typed: list[Mapping[str, Any]] = []
        for index, record in enumerate(records):
            path = f"{top_key}[{index}]"
            if not isinstance(record, Mapping):
                errors.append(f"{path}: must be an object")
                continue
            typed.append(record)
            _exact_record_errors(record, allowed, required, path, errors)
            record_id = record.get(id_key)
            if not _is_nonempty(record_id):
                errors.append(f"{path}.{id_key}: required non-empty identifier")
            elif record_id in catalog:
                errors.append(f"{path}.{id_key}: duplicate global record id {record_id}")
            else:
                catalog[record_id] = (kind, record)
            for key, expected in scope.items():
                if record.get(key) != expected:
                    errors.append(f"{path}.{key}: cross-life/scope mismatch")
            if not _is_int(record.get("round_index")):
                errors.append(f"{path}.round_index: must be a non-negative integer")
            if not _is_nonempty(record.get("created_barrier_id")):
                errors.append(f"{path}.created_barrier_id: required")
        by_kind[kind] = typed
    return catalog, by_kind


def _barrier_errors(trace: Mapping[str, Any], catalog: Mapping[str, tuple[str, Mapping[str, Any]]],
                    errors: list[str]) -> tuple[dict[str, Mapping[str, Any]], dict[str, int]]:
    barriers = trace.get("phase_barriers")
    if not isinstance(barriers, list):
        errors.append("phase_barriers: must be a list")
        return {}, {}
    round_count = trace.get("round_count")
    if not _is_int(round_count, minimum=1):
        errors.append("round_count: must be a positive integer")
        round_count = 0
    if len(barriers) != round_count * len(PHASES):
        errors.append("phase_barriers: must contain every immutable phase in every round")
    barrier_by_id: dict[str, Mapping[str, Any]] = {}
    barrier_index: dict[str, int] = {}
    previous_hash: str | None = None
    scope = _scope(trace)
    expected_refs_by_barrier: dict[str, list[dict[str, str]]] = {}
    for record_id, (kind, record) in catalog.items():
        barrier_id = record.get("created_barrier_id")
        expected_refs_by_barrier.setdefault(str(barrier_id), []).append(
            {"kind": kind, "id": record_id, "record_hash": sha256_json(record)}
        )
    for refs in expected_refs_by_barrier.values():
        refs.sort(key=lambda item: (item["kind"], item["id"]))

    for index, barrier in enumerate(barriers):
        path = f"phase_barriers[{index}]"
        if not isinstance(barrier, Mapping):
            errors.append(f"{path}: must be an object")
            continue
        allowed = frozenset({
            "barrier_id", "world_id", "skin_id", "life_id", "barrier_index",
            "round_index", "phase", "previous_barrier_hash", "record_refs",
            "barrier_hash",
        })
        _exact_record_errors(barrier, allowed, allowed, path, errors)
        barrier_id = barrier.get("barrier_id")
        if not _is_nonempty(barrier_id):
            errors.append(f"{path}.barrier_id: required")
            continue
        if barrier_id in barrier_by_id:
            errors.append(f"{path}.barrier_id: duplicate {barrier_id}")
        barrier_by_id[barrier_id] = barrier
        barrier_index[barrier_id] = index
        for key, expected in scope.items():
            if barrier.get(key) != expected:
                errors.append(f"{path}.{key}: cross-life/scope mismatch")
        expected_round = index // len(PHASES)
        expected_phase = PHASES[index % len(PHASES)]
        if barrier.get("barrier_index") != index:
            errors.append(f"{path}.barrier_index: immutable order requires {index}")
        if barrier.get("round_index") != expected_round:
            errors.append(f"{path}.round_index: immutable order requires {expected_round}")
        if barrier.get("phase") != expected_phase:
            errors.append(f"{path}.phase: immutable order requires {expected_phase}")
        if barrier.get("previous_barrier_hash") != previous_hash:
            errors.append(f"{path}.previous_barrier_hash: broken append-only chain")
        refs = barrier.get("record_refs")
        if not isinstance(refs, list):
            errors.append(f"{path}.record_refs: must be a list")
            refs = []
        for ref_index, ref in enumerate(refs):
            if not isinstance(ref, Mapping) or set(ref) != {"kind", "id", "record_hash"}:
                errors.append(
                    f"{path}.record_refs[{ref_index}]: exact kind/id/record_hash ref required"
                )
        if refs != sorted(refs, key=lambda item: (
                str(item.get("kind")), str(item.get("id")))):
            errors.append(f"{path}.record_refs: must be canonical sorted order")
        if refs != expected_refs_by_barrier.get(barrier_id, []):
            errors.append(f"{path}.record_refs: not an exact manifest of committed records")
        expected_hash = phase_barrier_digest(
            scope, index, expected_round, expected_phase, previous_hash, refs,
        )
        if barrier.get("barrier_hash") != expected_hash:
            errors.append(f"{path}.barrier_hash: content or phase mutation")
        previous_hash = barrier.get("barrier_hash") if _is_nonempty(
            barrier.get("barrier_hash")) else expected_hash

    for record_id, (kind, record) in catalog.items():
        barrier_id = record.get("created_barrier_id")
        barrier = barrier_by_id.get(str(barrier_id))
        if barrier is None:
            errors.append(f"{kind} {record_id}: created_barrier_id is unknown")
            continue
        if barrier.get("phase") != _PHASE_FOR_KIND[kind]:
            errors.append(f"{kind} {record_id}: record committed in wrong phase")
        if barrier.get("round_index") != record.get("round_index"):
            errors.append(f"{kind} {record_id}: record round differs from barrier")
    return barrier_by_id, barrier_index


def _semantic_and_derivation_errors(
    trace: Mapping[str, Any], catalog: Mapping[str, tuple[str, Mapping[str, Any]]],
    by_kind: Mapping[str, list[Mapping[str, Any]]],
    barrier_index: Mapping[str, int], errors: list[str],
) -> tuple[dict[str, int], dict[str, str], dict[str, str]]:
    experiences = {item["experience_id"]: item for item in by_kind["experience"]
                   if _is_nonempty(item.get("experience_id"))}
    concepts = {item["concept_id"]: item for item in by_kind["concept"]
                if _is_nonempty(item.get("concept_id"))}
    edges = {item["edge_id"]: item for item in by_kind["semantic_edge"]
             if _is_nonempty(item.get("edge_id"))}
    semantics: dict[str, Mapping[str, Any]] = {**concepts, **edges}
    semantic_kind = {**{key: "concept" for key in concepts},
                     **{key: "semantic_edge" for key in edges}}
    semantic_hashes: dict[str, str] = {}

    for exp_id, exp in experiences.items():
        for field in ("action", "observation", "outcome"):
            if not isinstance(exp.get(field), str):
                errors.append(f"experience {exp_id}.{field}: must be text")
        if all(isinstance(exp.get(field), str) for field in ("action", "observation", "outcome")):
            expected = experience_payload_hash(exp["action"], exp["observation"], exp["outcome"])
            if exp.get("payload_hash") != expected:
                errors.append(f"experience {exp_id}.payload_hash: content mismatch")
        if not _is_int(exp.get("sequence_index")):
            errors.append(f"experience {exp_id}.sequence_index: must be non-negative integer")

    if _duplicates([exp.get("sequence_index") for exp in experiences.values()]):
        errors.append("experiences: duplicate sequence_index")

    for concept_id, concept in concepts.items():
        if not _is_int(concept.get("step_index")):
            errors.append(f"concept {concept_id}.step_index: must be non-negative integer")
        if not _is_nonempty(concept.get("canonical_key")):
            errors.append(f"concept {concept_id}.canonical_key: required")
            continue
        if not _is_nonempty(concept.get("display_label")):
            errors.append(f"concept {concept_id}.display_label: required")
        expected = concept_semantic_hash(concept["canonical_key"])
        if concept.get("semantic_hash") != expected:
            errors.append(f"concept {concept_id}.semantic_hash: canonical identity mismatch")
        semantic_hashes[concept_id] = expected
        if concept.get("initial_status") != "provisional":
            errors.append(f"concept {concept_id}.initial_status: must be provisional")

    for edge_id, edge in edges.items():
        if not _is_int(edge.get("step_index")):
            errors.append(f"semantic_edge {edge_id}.step_index: must be non-negative integer")
        source = concepts.get(str(edge.get("source_concept_id")))
        target = concepts.get(str(edge.get("target_concept_id")))
        if source is None or target is None:
            errors.append(f"semantic_edge {edge_id}: endpoints must be local concepts")
            continue
        if not _is_nonempty(edge.get("relation")):
            errors.append(f"semantic_edge {edge_id}.relation: required")
            continue
        expected = edge_semantic_hash(
            semantic_hashes.get(str(edge.get("source_concept_id")), ""),
            edge["relation"],
            semantic_hashes.get(str(edge.get("target_concept_id")), ""),
        )
        if edge.get("semantic_hash") != expected:
            errors.append(f"semantic_edge {edge_id}.semantic_hash: canonical identity mismatch")
        semantic_hashes[edge_id] = expected
        if edge.get("initial_status") != "provisional":
            errors.append(f"semantic_edge {edge_id}.initial_status: must be provisional")

    duplicates = _duplicates([item.get("semantic_hash") for item in semantics.values()])
    if duplicates:
        errors.append("semantics: duplicate semantic hashes cannot create paraphrase nodes/depth")

    derivations = {item["derivation_id"]: item for item in by_kind["derivation"]
                   if _is_nonempty(item.get("derivation_id"))}
    conclusion_to_creation: dict[str, str] = {}
    ordered = sorted(derivations.items(), key=lambda pair: (
        barrier_index.get(str(pair[1].get("created_barrier_id")), 10**9),
        pair[1].get("step_index", 10**9), pair[0],
    ))
    depths: dict[str, int] = {}
    derivation_hashes: dict[str, str] = {}
    derivation_depths: dict[str, int] = {}
    evidence_identities_by_conclusion: dict[str, set[str]] = {}
    seen_derivation_hashes: set[str] = set()
    for derivation_id, derivation in ordered:
        path = f"derivation {derivation_id}"
        if not _is_int(derivation.get("step_index")):
            errors.append(f"{path}.step_index: must be non-negative integer")
        conclusion_id = derivation.get("conclusion_id")
        conclusion_kind = derivation.get("conclusion_kind")
        conclusion = semantics.get(str(conclusion_id))
        if conclusion is None or semantic_kind.get(str(conclusion_id)) != conclusion_kind:
            errors.append(f"{path}: conclusion must be one local semantic item")
            continue
        is_creation = conclusion.get("derivation_id") == derivation_id
        conclusion_position = (
            barrier_index.get(str(conclusion.get("created_barrier_id")), 10**9),
            conclusion.get("step_index", 10**9),
        )
        derivation_position = (
            barrier_index.get(str(derivation.get("created_barrier_id")), 10**9),
            derivation.get("step_index", 10**9),
        )
        if is_creation:
            if conclusion_position != derivation_position:
                errors.append(f"{path}: creation derivation must commit atomically")
            if str(conclusion_id) in conclusion_to_creation:
                errors.append(f"{path}: semantic conclusion has multiple creation derivations")
            conclusion_to_creation[str(conclusion_id)] = derivation_id
        elif derivation_position <= conclusion_position:
            errors.append(
                f"{path}: reinforcement derivation must commit after semantic creation"
            )
        premises = derivation.get("premise_refs")
        if not isinstance(premises, list) or not premises:
            errors.append(f"{path}.premise_refs: at least one evidentiary premise required")
            premises = []
        identities: list[dict[str, str]] = []
        parent_depths: list[int] = []
        for premise_index, premise in enumerate(premises):
            ppath = f"{path}.premise_refs[{premise_index}]"
            if not isinstance(premise, Mapping) or set(premise) != {"kind", "id"}:
                errors.append(f"{ppath}: exact kind/id premise required")
                continue
            kind = premise.get("kind")
            premise_id = premise.get("id")
            if kind not in PREMISE_KINDS:
                errors.append(
                    f"{ppath}: thinker/agenda/realization records are non-evidentiary"
                )
                continue
            entry = catalog.get(str(premise_id))
            if entry is None or entry[0] != kind:
                errors.append(f"{ppath}: missing or cross-life premise")
                continue
            premise_record = entry[1]
            if kind in SEMANTIC_KINDS and str(premise_id) == str(conclusion_id):
                errors.append(f"{ppath}: reinforcement cannot cite its own conclusion")
            conclusion_barrier = barrier_index.get(str(derivation.get("created_barrier_id")), 10**9)
            premise_barrier = barrier_index.get(str(premise_record.get("created_barrier_id")), 10**9)
            if premise_barrier > conclusion_barrier or (
                premise_barrier == conclusion_barrier
                and kind in SEMANTIC_KINDS
                and premise_record.get("step_index", 10**9) >= derivation.get("step_index", -1)
            ):
                errors.append(f"{ppath}: future or same-step semantic citation")
            if kind == "experience":
                identities.append({"kind": kind, "identity": str(premise_record.get("payload_hash"))})
            else:
                identities.append({"kind": kind, "identity": str(premise_record.get("semantic_hash"))})
                if str(premise_id) not in depths:
                    errors.append(f"{ppath}: semantic premise has no earlier derivation depth")
                else:
                    parent_depths.append(depths[str(premise_id)])
        expected_depth = 1 + max(parent_depths, default=0)
        if derivation.get("declared_depth") != expected_depth:
            errors.append(f"{path}.declared_depth: derived value is {expected_depth}")
        derivation_depths[derivation_id] = expected_depth
        if is_creation:
            depths[str(conclusion_id)] = expected_depth
        if not _is_nonempty(derivation.get("rule")):
            errors.append(f"{path}.rule: required")
            rule = ""
        else:
            rule = derivation["rule"]
        expected_hash = derivation_digest(
            rule, semantic_hashes.get(str(conclusion_id), ""), identities,
        )
        if derivation.get("derivation_hash") != expected_hash:
            errors.append(f"{path}.derivation_hash: provenance mismatch")
        if expected_hash in seen_derivation_hashes:
            errors.append(f"{path}: duplicate derivation hash cannot add support or depth")
        seen_derivation_hashes.add(expected_hash)
        derivation_hashes[derivation_id] = expected_hash
        evidence_identity = sha256_json(sorted(
            identities, key=lambda item: (item["kind"], item["identity"])
        ))
        prior_identities = evidence_identities_by_conclusion.setdefault(
            str(conclusion_id), set()
        )
        if evidence_identity in prior_identities:
            errors.append(
                f"{path}: repeated evidence identity cannot add independent support"
            )
        prior_identities.add(evidence_identity)
        guidance = derivation.get("guidance_agenda_ids")
        if not isinstance(guidance, list):
            errors.append(f"{path}.guidance_agenda_ids: must be a list")
            guidance = []
        for agenda_id in guidance:
            entry = catalog.get(str(agenda_id))
            if entry is None or entry[0] != "agenda":
                errors.append(f"{path}.guidance_agenda_ids: unknown/cross-life agenda")
                continue
            agenda = entry[1]
            if barrier_index.get(str(agenda.get("created_barrier_id")), 10**9) >= \
                    barrier_index.get(str(derivation.get("created_barrier_id")), -1):
                errors.append(f"{path}.guidance_agenda_ids: guidance must precede dream")
            # Guidance is intentionally absent from both depth and derivation hash.

    if set(conclusion_to_creation) != set(semantics):
        errors.append("semantics: every semantic item needs exactly one creation derivation")
    return depths, semantic_hashes, derivation_hashes


def _epistemic_errors(
    by_kind: Mapping[str, list[Mapping[str, Any]]],
    semantic_hashes: Mapping[str, str], derivation_hashes: Mapping[str, str],
    barrier_index: Mapping[str, int], errors: list[str],
) -> tuple[dict[str, str], list[tuple[int, str, str]]]:
    semantics = set(semantic_hashes)
    semantic_kinds = {
        **{str(item.get("concept_id")): "concept" for item in by_kind["concept"]},
        **{str(item.get("edge_id")): "semantic_edge" for item in by_kind["semantic_edge"]},
    }
    derivations = {
        str(item.get("derivation_id")): item for item in by_kind["derivation"]
    }
    semantic_records = {
        **{str(item.get("concept_id")): item for item in by_kind["concept"]},
        **{str(item.get("edge_id")): item for item in by_kind["semantic_edge"]},
    }
    reinforcement_ids = {
        derivation_id for derivation_id, derivation in derivations.items()
        if semantic_records.get(str(derivation.get("conclusion_id")), {}).get(
            "derivation_id"
        ) != derivation_id
    }
    events = by_kind["epistemic_event"]
    last_order = (-1, -1)
    status: dict[str, str] = {}
    created: set[str] = set()
    support_derivations_by_subject: dict[str, set[str]] = {}
    consumed_reinforcements: Counter[str] = Counter()
    status_timeline: list[tuple[int, str, str]] = []
    for index, event in enumerate(events):
        event_id = event.get("epistemic_event_id")
        barrier = barrier_index.get(str(event.get("created_barrier_id")), 10**9)
        step = event.get("step_index")
        if not _is_int(step):
            errors.append(f"epistemic_event {event_id}.step_index: must be non-negative integer")
            step = 10**9
        order = (barrier, step)
        if order < last_order:
            errors.append("epistemic_events: append-only event order is not monotonic")
        last_order = order
        subject_id = str(event.get("subject_id"))
        if subject_id not in semantics:
            errors.append(f"epistemic_event {event_id}: unknown/cross-life semantic subject")
            continue
        if event.get("subject_kind") != semantic_kinds.get(subject_id):
            errors.append(f"epistemic_event {event_id}: subject kind mismatch")
        kind = event.get("event_kind")
        old = status.get(subject_id)
        if event.get("previous_status") != old:
            errors.append(f"epistemic_event {event_id}.previous_status: append-only mismatch")
        new = event.get("new_status")
        if new not in EPISTEMIC_STATUSES:
            errors.append(f"epistemic_event {event_id}.new_status: invalid")
        valid_transition = False
        if kind == "CREATE":
            valid_transition = old is None and new == "provisional"
            created.add(subject_id)
        elif kind == "SUPPORT":
            valid_transition = old in {"provisional", "supported"} and new == "supported"
        elif kind == "CONTRADICT":
            valid_transition = old in {"provisional", "supported"} and new == "contradicted"
        elif kind == "SUPERSEDE":
            replacement = event.get("replacement_subject_id")
            valid_transition = (
                old in {"provisional", "supported"} and new == "superseded"
                and replacement in semantics and replacement != subject_id
            )
        else:
            errors.append(f"epistemic_event {event_id}.event_kind: invalid")
        if not valid_transition:
            errors.append(f"epistemic_event {event_id}: invalid epistemic transition")
        derivation_id = event.get("evidence_derivation_id")
        if derivation_id not in derivation_hashes:
            errors.append(f"epistemic_event {event_id}: evidence derivation is not local")
        else:
            expected_subject = (
                event.get("replacement_subject_id") if kind == "SUPERSEDE" else subject_id
            )
            if derivations[str(derivation_id)].get("conclusion_id") != expected_subject:
                errors.append(
                    f"epistemic_event {event_id}: evidence derivation does not bind subject"
                )
            semantic = semantic_records[subject_id]
            semantic_position = (
                barrier_index.get(str(semantic.get("created_barrier_id")), 10**9),
                semantic.get("step_index", 10**9),
            )
            derivation = derivations[str(derivation_id)]
            derivation_position = (
                barrier_index.get(str(derivation.get("created_barrier_id")), 10**9),
                derivation.get("step_index", 10**9),
            )
            event_position = (barrier, step)
            if event_position < derivation_position:
                errors.append(f"epistemic_event {event_id}: cites a future derivation")
            if kind == "CREATE":
                if derivation_id != semantic.get("derivation_id"):
                    errors.append(
                        f"epistemic_event {event_id}: CREATE must cite creation derivation"
                    )
                if event_position != semantic_position:
                    errors.append(
                        f"epistemic_event {event_id}: CREATE must commit with semantic item"
                    )
            elif kind == "SUPPORT":
                already = support_derivations_by_subject.setdefault(subject_id, set())
                if str(derivation_id) in already:
                    errors.append(
                        f"epistemic_event {event_id}: repeated evidence cannot inflate support"
                    )
                already.add(str(derivation_id))
                if str(derivation_id) in reinforcement_ids:
                    consumed_reinforcements[str(derivation_id)] += 1
        replacement = event.get("replacement_subject_id")
        if kind != "SUPERSEDE" and replacement is not None:
            errors.append(f"epistemic_event {event_id}: replacement only valid for SUPERSEDE")
        if isinstance(new, str):
            status[subject_id] = new
            status_timeline.append((barrier, subject_id, new))
    if created != semantics:
        errors.append("epistemic_events: every semantic item needs exactly one CREATE")
    for derivation_id in sorted(reinforcement_ids):
        if consumed_reinforcements[derivation_id] != 1:
            errors.append(
                f"derivation {derivation_id}: reinforcement needs exactly one SUPPORT event"
            )
    return status, status_timeline


def _status_at(semantic_ids: Sequence[str], timeline: Sequence[tuple[int, str, str]],
               barrier: int) -> dict[str, str]:
    state: dict[str, str] = {}
    wanted = set(semantic_ids)
    for event_barrier, subject_id, status in timeline:
        if event_barrier >= barrier:
            break
        if subject_id in wanted:
            state[subject_id] = status
    return state


def semantic_state_digest(items: Sequence[Mapping[str, Any]]) -> str:
    canonical = sorted((dict(item) for item in items), key=lambda item: item["id"])
    return sha256_json(canonical)


def realization_state_digest(realizations: Sequence[Mapping[str, Any]],
                             touch_plans: Sequence[Mapping[str, Any]]) -> str:
    return sha256_json({
        "realizations": sorted(
            ({"id": item["realization_id"], "hash": item["realization_hash"]}
             for item in realizations), key=lambda item: item["id"]),
        "touch_plans": sorted(
            ({"id": item["touch_plan_id"], "hash": item["plan_hash"]}
             for item in touch_plans), key=lambda item: item["id"]),
    })


def _realization_checkpoint_errors(
    trace: Mapping[str, Any], catalog: Mapping[str, tuple[str, Mapping[str, Any]]],
    by_kind: Mapping[str, list[Mapping[str, Any]]], barrier_index: Mapping[str, int],
    semantic_hashes: Mapping[str, str], depths: Mapping[str, int],
    status_timeline: Sequence[tuple[int, str, str]], errors: list[str],
) -> dict[str, Mapping[str, Any]]:
    realizations = {item["realization_id"]: item for item in by_kind["realization_spec"]
                    if _is_nonempty(item.get("realization_id"))}
    touch_plans = {item["touch_plan_id"]: item for item in by_kind["touch_plan"]
                   if _is_nonempty(item.get("touch_plan_id"))}
    checkpoints = {item["checkpoint_id"]: item for item in by_kind["checkpoint"]
                   if _is_nonempty(item.get("checkpoint_id"))}
    semantic_records = {key: catalog[key][1] for key in semantic_hashes if key in catalog}

    for realization_id, realization in realizations.items():
        source_id = str(realization.get("source_id"))
        source = semantic_records.get(source_id)
        if source is None or catalog[source_id][0] != realization.get("source_kind"):
            errors.append(f"realization_spec {realization_id}: source is not a local semantic")
            continue
        if realization.get("source_semantic_hash") != semantic_hashes[source_id]:
            errors.append(f"realization_spec {realization_id}: source hash mismatch")
        if realization.get("form") not in REALIZATION_FORMS:
            errors.append(f"realization_spec {realization_id}.form: invalid")
        if not isinstance(realization.get("cue_text"), str) or not isinstance(
                realization.get("target_text"), str):
            errors.append(f"realization_spec {realization_id}: cue/target must be text")
        else:
            expected = realization_digest(
                semantic_hashes[source_id], realization.get("form", ""),
                realization["cue_text"], realization["target_text"],
            )
            if realization.get("realization_hash") != expected:
                errors.append(f"realization_spec {realization_id}: realization hash mismatch")
        if barrier_index.get(str(source.get("created_barrier_id")), 10**9) >= \
                barrier_index.get(str(realization.get("created_barrier_id")), -1):
            errors.append(f"realization_spec {realization_id}: source must predate realization")
        realization_barrier = barrier_index.get(
            str(realization.get("created_barrier_id")), 10**9
        )
        source_state = _status_at([source_id], status_timeline, realization_barrier)
        if source_state.get(source_id) not in {"provisional", "supported"}:
            errors.append(
                f"realization_spec {realization_id}: source is not live at realization"
            )

    plans_by_realization: Counter[str] = Counter()
    for plan_id, plan in touch_plans.items():
        realization_id = str(plan.get("realization_id"))
        if realization_id not in realizations:
            errors.append(f"touch_plan {plan_id}: unknown/cross-life realization")
            continue
        plans_by_realization[realization_id] += 1
        if not _is_int(plan.get("touches"), minimum=1):
            errors.append(f"touch_plan {plan_id}.touches: must be positive integer")
        if not _is_number(plan.get("weight")) or plan.get("weight", 0) <= 0:
            errors.append(f"touch_plan {plan_id}.weight: must be positive number")
        if not _is_int(plan.get("order_index")):
            errors.append(f"touch_plan {plan_id}.order_index: must be non-negative integer")
        if all(key in plan for key in ("realization_id", "touches", "weight", "order_index")):
            expected = touch_plan_digest(
                plan["realization_id"], plan["touches"], plan["weight"], plan["order_index"],
            )
            if plan.get("plan_hash") != expected:
                errors.append(f"touch_plan {plan_id}.plan_hash: content mismatch")
    if set(plans_by_realization) != set(realizations) or any(
            count != 1 for count in plans_by_realization.values()):
        errors.append("touch_plans: every realization needs exactly one plan")

    if len(checkpoints) != trace.get("round_count"):
        errors.append("checkpoints: exactly one checkpoint required per round")
    prior_checkpoint: str | None = None
    for round_index in range(trace.get("round_count", 0)):
        matches = [item for item in checkpoints.values() if item.get("round_index") == round_index]
        if len(matches) != 1:
            continue
        checkpoint = matches[0]
        checkpoint_id = checkpoint["checkpoint_id"]
        if checkpoint.get("memory_adapter_id") != trace.get("memory_adapter_id"):
            errors.append(f"checkpoint {checkpoint_id}: memory adapter mismatch")
        if checkpoint.get("previous_checkpoint_id") != prior_checkpoint:
            errors.append(f"checkpoint {checkpoint_id}: previous checkpoint chain mismatch")
        prior_checkpoint = checkpoint_id
        cp_barrier = barrier_index.get(str(checkpoint.get("created_barrier_id")), 10**9)
        state = _status_at(list(semantic_hashes), status_timeline, cp_barrier)
        expected_semantic_ids = sorted(
            item_id for item_id, item_status in state.items()
            if item_status in {"provisional", "supported"}
        )
        if checkpoint.get("included_semantic_ids") != expected_semantic_ids:
            errors.append(f"checkpoint {checkpoint_id}: semantic manifest is not exact live state")
        semantic_payload = [
            {"id": item_id, "semantic_hash": semantic_hashes[item_id],
             "status": state[item_id], "derivation_depth": depths[item_id]}
            for item_id in expected_semantic_ids
        ]
        if checkpoint.get("semantic_state_hash") != semantic_state_digest(semantic_payload):
            errors.append(f"checkpoint {checkpoint_id}.semantic_state_hash: mismatch")
        available_realizations = sorted(
            (item for item in realizations.values()
             if barrier_index.get(str(item.get("created_barrier_id")), 10**9) < cp_barrier),
            key=lambda item: item["realization_id"],
        )
        available_plans = sorted(
            (item for item in touch_plans.values()
             if barrier_index.get(str(item.get("created_barrier_id")), 10**9) < cp_barrier),
            key=lambda item: item["touch_plan_id"],
        )
        expected_realization_ids = [item["realization_id"] for item in available_realizations]
        expected_plan_ids = [item["touch_plan_id"] for item in available_plans]
        realized_sources = {item["source_id"] for item in available_realizations}
        if not set(expected_semantic_ids).issubset(realized_sources):
            errors.append(
                f"checkpoint {checkpoint_id}: live semantic item lacks a realization/touch path"
            )
        if checkpoint.get("realization_ids") != expected_realization_ids:
            errors.append(f"checkpoint {checkpoint_id}: realization manifest is not exact")
        if checkpoint.get("touch_plan_ids") != expected_plan_ids:
            errors.append(f"checkpoint {checkpoint_id}: touch-plan manifest is not exact")
        expected_realization_hash = realization_state_digest(
            available_realizations, available_plans,
        )
        if checkpoint.get("realization_state_hash") != expected_realization_hash:
            errors.append(f"checkpoint {checkpoint_id}.realization_state_hash: mismatch")
        _check_sha(checkpoint.get("adapter_artifact_hash"),
                   f"checkpoint {checkpoint_id}.adapter_artifact_hash", errors)
    return checkpoints


def _thinker_feedback_errors(
    trace: Mapping[str, Any], catalog: Mapping[str, tuple[str, Mapping[str, Any]]],
    by_kind: Mapping[str, list[Mapping[str, Any]]], checkpoints: Mapping[str, Mapping[str, Any]],
    barrier_index: Mapping[str, int], errors: list[str],
) -> None:
    states = {item["thinker_state_id"]: item for item in by_kind["thinker_state"]
              if _is_nonempty(item.get("thinker_state_id"))}
    hypotheses = {item["hypothesis_id"]: item for item in by_kind["thinker_hypothesis"]
                  if _is_nonempty(item.get("hypothesis_id"))}
    confusions = {item["confusion_id"]: item for item in by_kind["thinker_confusion"]
                  if _is_nonempty(item.get("confusion_id"))}
    desires = {item["desire_id"]: item for item in by_kind["thinker_desire"]
               if _is_nonempty(item.get("desire_id"))}
    agendas = {item["agenda_id"]: item for item in by_kind["agenda"]
               if _is_nonempty(item.get("agenda_id"))}

    for state_id, state in states.items():
        if not _is_int(state.get("step_index")):
            errors.append(f"thinker_state {state_id}.step_index: must be non-negative integer")
        checkpoint = checkpoints.get(str(state.get("checkpoint_id")))
        if checkpoint is None or checkpoint.get("round_index") != state.get("round_index"):
            errors.append(f"thinker_state {state_id}: must read this round's checkpoint")
            continue
        parent_id = state.get("parent_state_id")
        if parent_id is not None:
            parent = states.get(str(parent_id))
            if parent is None or parent.get("round_index") != state.get("round_index") or \
                    parent.get("step_index", 10**9) >= state.get("step_index", -1):
                errors.append(f"thinker_state {state_id}: parent must be earlier in same think phase")
        retrieved = state.get("retrieved_semantic_ids")
        workspace = state.get("workspace")
        if not isinstance(retrieved, list) or not all(isinstance(item, str) for item in retrieved):
            errors.append(f"thinker_state {state_id}.retrieved_semantic_ids: string list required")
            retrieved = []
        if not set(retrieved).issubset(set(checkpoint.get("included_semantic_ids", []))):
            errors.append(f"thinker_state {state_id}: retrieves outside checkpoint")
        if not isinstance(workspace, list) or not all(isinstance(item, str) for item in workspace):
            errors.append(f"thinker_state {state_id}.workspace: text list required")
            workspace = []
        registry = state.get("query_registry")
        if not isinstance(registry, list):
            errors.append(f"thinker_state {state_id}.query_registry: list required")
            registry = []
        registry_keys: set[str] = set()
        for index, query in enumerate(registry):
            qpath = f"thinker_state {state_id}.query_registry[{index}]"
            if not isinstance(query, Mapping) or set(query) != {
                "query_key", "subject_entity_id", "relation_id"
            }:
                errors.append(f"{qpath}: exact typed query declaration required")
                continue
            if any(
                not isinstance(query[field], str) or _HANDLE.fullmatch(query[field]) is None
                for field in ("query_key", "subject_entity_id", "relation_id")
            ):
                errors.append(f"{qpath}: opaque typed handles required")
            if query["query_key"] in registry_keys:
                errors.append(f"{qpath}.query_key: duplicate")
            registry_keys.add(query["query_key"])
            if query["subject_entity_id"] not in checkpoint.get("included_semantic_ids", []):
                errors.append(f"{qpath}.subject_entity_id: outside checkpoint")
        if not isinstance(state.get("goal"), str):
            errors.append(f"thinker_state {state_id}.goal: text required")
        else:
            expected = thinker_state_digest(
                str(state.get("checkpoint_id")), parent_id, state["goal"], retrieved, workspace,
                registry,
            )
            if state.get("state_hash") != expected:
                errors.append(f"thinker_state {state_id}.state_hash: mismatch")

    for hypothesis_id, hypothesis in hypotheses.items():
        state = states.get(str(hypothesis.get("thinker_state_id")))
        if state is None or state.get("round_index") != hypothesis.get("round_index"):
            errors.append(f"thinker_hypothesis {hypothesis_id}: unknown/cross-round state")
            continue
        cited = hypothesis.get("cited_semantic_ids")
        if not isinstance(cited, list) or not all(isinstance(item, str) for item in cited):
            errors.append(f"thinker_hypothesis {hypothesis_id}: cited semantic list required")
            cited = []
        if not set(cited).issubset(set(state.get("retrieved_semantic_ids", []))):
            errors.append(f"thinker_hypothesis {hypothesis_id}: cites memory not retrieved")
        release_support = hypothesis.get("release_support_semantic_ids")
        if not isinstance(release_support, list) or not all(
                isinstance(item, str) for item in release_support):
            errors.append(
                f"thinker_hypothesis {hypothesis_id}.release_support_semantic_ids: string list required"
            )
            release_support = []
        if len(release_support) != len(set(release_support)):
            errors.append(f"thinker_hypothesis {hypothesis_id}: duplicate release support")
        if not set(release_support) <= set(cited):
            errors.append(f"thinker_hypothesis {hypothesis_id}: release support not cited")
        parents = hypothesis.get("parent_hypothesis_ids")
        if not isinstance(parents, list) or not all(isinstance(item, str) for item in parents):
            errors.append(
                f"thinker_hypothesis {hypothesis_id}.parent_hypothesis_ids: string list required"
            )
            parents = []
        if len(parents) != len(set(parents)):
            errors.append(f"thinker_hypothesis {hypothesis_id}: duplicate hypothesis parent")
        for parent_id in parents:
            parent = hypotheses.get(parent_id)
            if parent is None or parent.get("round_index") != hypothesis.get("round_index") or \
                    parent.get("step_index", 10**9) >= hypothesis.get("step_index", -1):
                errors.append(
                    f"thinker_hypothesis {hypothesis_id}: parent must be earlier same-round hypothesis"
                )
        if not _is_number(hypothesis.get("confidence")) or not 0 <= hypothesis.get("confidence", -1) <= 1:
            errors.append(f"thinker_hypothesis {hypothesis_id}.confidence: must be in [0,1]")
        if hypothesis.get("disposition") not in {"tentative", "released", "deferred"}:
            errors.append(f"thinker_hypothesis {hypothesis_id}.disposition: invalid")
        if hypothesis.get("disposition") == "released" and not release_support:
            errors.append(f"thinker_hypothesis {hypothesis_id}: released path support required")
        if hypothesis.get("disposition") != "released" and release_support:
            errors.append(
                f"thinker_hypothesis {hypothesis_id}: only released hypotheses carry path support"
            )
        semantic_edges = {
            item["edge_id"]: item for item in by_kind["semantic_edge"]
            if _is_nonempty(item.get("edge_id"))
        }
        if any(item_id not in semantic_edges for item_id in release_support):
            errors.append(f"thinker_hypothesis {hypothesis_id}: support must be semantic edges")
        if release_support and all(item_id in semantic_edges for item_id in release_support):
            pending = [release_support[0]]
            connected = {release_support[0]}
            support_set = set(release_support)
            while pending:
                current_id = pending.pop()
                current = semantic_edges[current_id]
                endpoints = {current["source_concept_id"], current["target_concept_id"]}
                for candidate_id in support_set - connected:
                    candidate = semantic_edges[candidate_id]
                    if endpoints & {
                        candidate["source_concept_id"], candidate["target_concept_id"]
                    }:
                        connected.add(candidate_id)
                        pending.append(candidate_id)
            if connected != support_set:
                errors.append(
                    f"thinker_hypothesis {hypothesis_id}: release support must be connected"
                )
        if not isinstance(hypothesis.get("claim"), str):
            errors.append(f"thinker_hypothesis {hypothesis_id}.claim: text required")
        else:
            expected = hypothesis_digest(
                state["thinker_state_id"], hypothesis["claim"], cited,
                hypothesis.get("confidence"), str(hypothesis.get("disposition")),
                parents, release_support,
            )
            if hypothesis.get("hypothesis_hash") != expected:
                errors.append(f"thinker_hypothesis {hypothesis_id}.hypothesis_hash: mismatch")

    for confusion_id, confusion in confusions.items():
        state = states.get(str(confusion.get("thinker_state_id")))
        if state is None or state.get("round_index") != confusion.get("round_index"):
            errors.append(f"thinker_confusion {confusion_id}: unknown/cross-round state")
            continue
        if confusion.get("unknown_slot") != "object":
            errors.append(f"thinker_confusion {confusion_id}.unknown_slot: must be object")
        registry = {
            item["query_key"]: item for item in state.get("query_registry", [])
            if isinstance(item, Mapping) and _is_nonempty(item.get("query_key"))
        }
        declaration = registry.get(str(confusion.get("query_key")))
        if declaration is None or any(
            confusion.get(field) != declaration.get(field)
            for field in ("query_key", "subject_entity_id", "relation_id")
        ):
            errors.append(
                f"thinker_confusion {confusion_id}: not a mechanical registered query"
            )

    for desire_id, desire in desires.items():
        if desire.get("non_evidentiary") is not True:
            errors.append(f"thinker_desire {desire_id}: must remain non-evidentiary")
        confusion = confusions.get(str(desire.get("source_confusion_id")))
        if confusion is None or confusion.get("round_index") != desire.get("round_index"):
            errors.append(f"thinker_desire {desire_id}: source must be same-round confusion")
            continue
        state = states.get(str(confusion.get("thinker_state_id")))
        checkpoint = checkpoints.get(str(state.get("checkpoint_id"))) if state else None
        if state is None or checkpoint is None:
            errors.append(f"thinker_desire {desire_id}: source state/checkpoint missing")
            continue
        if any(
            desire.get(field) != confusion.get(field)
            for field in ("query_key", "subject_entity_id", "relation_id", "unknown_slot")
        ):
            errors.append(f"thinker_desire {desire_id}: not a mechanical confusion projection")
        if desire.get("checkpoint_id") != checkpoint.get("checkpoint_id") or \
                desire.get("checkpoint_semantic_state_hash") != checkpoint.get("semantic_state_hash") or \
                desire.get("thinker_state_hash") != state.get("state_hash"):
            errors.append(f"thinker_desire {desire_id}: stale checkpoint/state binding")
        if not _is_int(desire.get("priority"), minimum=1):
            errors.append(f"thinker_desire {desire_id}.priority: must be positive integer")

    if len(agendas) != trace.get("round_count"):
        errors.append("agendas: exactly one feedback agenda required per round")
    for agenda_id, agenda in agendas.items():
        if agenda.get("non_evidentiary") is not True:
            errors.append(f"agenda {agenda_id}: must remain non-evidentiary")
        desire_ids = agenda.get("desire_ids")
        query_keys = agenda.get("priority_query_keys")
        if not isinstance(desire_ids, list) or not all(isinstance(item, str) for item in desire_ids):
            errors.append(f"agenda {agenda_id}.desire_ids: string list required")
            desire_ids = []
        if not isinstance(query_keys, list) or not all(
                isinstance(item, str) and _HANDLE.fullmatch(item) is not None
                for item in query_keys):
            errors.append(f"agenda {agenda_id}.priority_query_keys: typed handle list required")
            query_keys = []
        round_desires = sorted(
            (
                (item.get("priority", 10**9), item_id, item)
                for item_id, item in desires.items()
                if item.get("round_index") == agenda.get("round_index")
            ),
            key=lambda row: (row[0], row[1]),
        )
        expected_desires = [item_id for _, item_id, _ in round_desires]
        if desire_ids != expected_desires:
            errors.append(f"agenda {agenda_id}: desire manifest is not exact")
        if len(round_desires) > 1:
            errors.append(f"agenda {agenda_id}: v1 permits at most one agenda item")
        if [priority for priority, _, _ in round_desires] != list(
                range(1, len(round_desires) + 1)):
            errors.append(f"agenda {agenda_id}: desire priorities must be contiguous")
        expected_query_keys = [item["query_key"] for _, _, item in round_desires]
        if query_keys != expected_query_keys:
            errors.append(f"agenda {agenda_id}: priority keys are not mechanical")
        state = next(
            (item for item in states.values() if item.get("state_hash") == agenda.get("thinker_state_hash")),
            None,
        )
        checkpoint = checkpoints.get(str(agenda.get("checkpoint_id")))
        if state is None or state.get("round_index") != agenda.get("round_index") or \
                checkpoint is None or checkpoint.get("round_index") != agenda.get("round_index") or \
                state.get("checkpoint_id") != agenda.get("checkpoint_id") or \
                agenda.get("checkpoint_semantic_state_hash") != checkpoint.get("semantic_state_hash"):
            errors.append(f"agenda {agenda_id}: stale checkpoint/state binding")
        if agenda.get("agenda_hash") != agenda_digest(
            str(agenda.get("checkpoint_id")),
            str(agenda.get("checkpoint_semantic_state_hash")),
            str(agenda.get("thinker_state_hash")),
            desire_ids,
            query_keys,
        ):
            errors.append(f"agenda {agenda_id}.agenda_hash: mismatch")


def validate_trace(trace: Any) -> list[str]:
    """Return all deterministic contract violations for one life trace."""
    errors: list[str] = []
    if not isinstance(trace, Mapping):
        return ["trace: must be an object"]
    allowed_top = frozenset({
        "schema_version", "trace_id", "world_id", "skin_id", "life_id", "split",
        "round_count", "memory_adapter_id", "phase_barriers", *_SPECS.keys(),
    })
    _exact_record_errors(trace, allowed_top, allowed_top, "trace", errors)
    if trace.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version: expected {SCHEMA_VERSION}")
    for field in ("trace_id", "world_id", "skin_id", "life_id", "split",
                  "memory_adapter_id"):
        if not _is_nonempty(trace.get(field)):
            errors.append(f"{field}: required non-empty text")

    catalog, by_kind = _record_catalog(trace, errors)
    _, barrier_index = _barrier_errors(trace, catalog, errors)
    depths, semantic_hashes, derivation_hashes = _semantic_and_derivation_errors(
        trace, catalog, by_kind, barrier_index, errors,
    )
    _, timeline = _epistemic_errors(
        by_kind, semantic_hashes, derivation_hashes, barrier_index, errors,
    )
    checkpoints = _realization_checkpoint_errors(
        trace, catalog, by_kind, barrier_index, semantic_hashes, depths, timeline, errors,
    )
    _thinker_feedback_errors(
        trace, catalog, by_kind, checkpoints, barrier_index, errors,
    )
    return errors


def assert_valid_trace(trace: Any) -> None:
    errors = validate_trace(trace)
    if errors:
        raise ContractError("\n".join(errors))


def validate_dataset(dataset: Any) -> list[str]:
    """Validate multiple lives and enforce dataset-wide life isolation."""
    if not isinstance(dataset, Mapping):
        return ["dataset: must be an object"]
    if set(dataset) != {"schema_version", "dataset_id", "traces"}:
        return ["dataset: exact schema_version/dataset_id/traces fields required"]
    errors: list[str] = []
    if dataset.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"dataset.schema_version: expected {SCHEMA_VERSION}")
    if not _is_nonempty(dataset.get("dataset_id")):
        errors.append("dataset.dataset_id: required")
    traces = dataset.get("traces")
    if not isinstance(traces, list) or not traces:
        errors.append("dataset.traces: non-empty list required")
        return errors
    seen_lives: set[tuple[Any, Any, Any]] = set()
    seen_trace_ids: set[Any] = set()
    seen_adapters: set[Any] = set()
    global_record_ids: set[str] = set()
    for index, trace in enumerate(traces):
        child_errors = validate_trace(trace)
        errors.extend(f"traces[{index}]: {error}" for error in child_errors)
        if not isinstance(trace, Mapping):
            continue
        life = (trace.get("world_id"), trace.get("skin_id"), trace.get("life_id"))
        if life in seen_lives:
            errors.append(f"traces[{index}]: duplicate evaluation life {life}")
        seen_lives.add(life)
        trace_id = trace.get("trace_id")
        if trace_id in seen_trace_ids:
            errors.append(f"traces[{index}]: duplicate trace_id")
        seen_trace_ids.add(trace_id)
        adapter = trace.get("memory_adapter_id")
        if adapter in seen_adapters:
            errors.append(f"traces[{index}]: memory adapter reused across lives")
        seen_adapters.add(adapter)
        for top_key, (_, id_key, _, _) in _SPECS.items():
            records = trace.get(top_key, [])
            if not isinstance(records, list):
                continue
            for record in records:
                if not isinstance(record, Mapping):
                    continue
                record_id = record.get(id_key)
                if isinstance(record_id, str) and record_id in global_record_ids:
                    errors.append(f"traces[{index}]: global record id reused across lives: {record_id}")
                elif isinstance(record_id, str):
                    global_record_ids.add(record_id)
        for barrier in trace.get("phase_barriers", []):
            if isinstance(barrier, Mapping):
                barrier_id = barrier.get("barrier_id")
                if isinstance(barrier_id, str) and barrier_id in global_record_ids:
                    errors.append(f"traces[{index}]: global barrier id reused across lives: {barrier_id}")
                elif isinstance(barrier_id, str):
                    global_record_ids.add(barrier_id)
    return errors


def assert_valid_dataset(dataset: Any) -> None:
    errors = validate_dataset(dataset)
    if errors:
        raise ContractError("\n".join(errors))


def compute_metrics(trace: Mapping[str, Any]) -> dict[str, Any]:
    """Compute structural and provenance depth on deliberately separate axes.

    ``semantic_structural_hops`` is the largest finite shortest-path distance
    in the undirected concept graph, so cyclic hub walks cannot inflate it.
    ``derivation_lineage_depth`` is the maximum validated provenance-DAG
    depth; ``supported_derivation_depth`` additionally requires SUPPORT for
    the derivation and every semantic creation premise.  The conservative
    ``independent_support_depth`` is a deterministic set-packing lower bound
    over pairwise-disjoint transitive public-experience hashes for one semantic
    item. ``thinker_compositional_depth`` counts only connected certified
    release-support edges plus hypothesis transformations that introduce a new
    support edge; irrelevant citations and paraphrase chains cannot inflate it.
    ``realization_count`` counts write views only.  Realizations, touches,
    desires, and agendas can never enter any of the first five calculations.
    """
    assert_valid_trace(trace)
    concepts = {item["concept_id"] for item in trace["concepts"]}
    adjacency = {item: set() for item in concepts}
    for edge in trace["semantic_edges"]:
        left, right = edge["source_concept_id"], edge["target_concept_id"]
        adjacency[left].add(right)
        adjacency[right].add(left)
    distances: list[int] = []
    components = 0
    globally_seen: set[str] = set()
    for start in sorted(concepts):
        if start not in globally_seen:
            components += 1
            component_queue = deque([start])
            globally_seen.add(start)
            while component_queue:
                node = component_queue.popleft()
                for neighbor in adjacency[node] - globally_seen:
                    globally_seen.add(neighbor)
                    component_queue.append(neighbor)
        queue = deque([(start, 0)])
        seen = {start}
        while queue:
            node, distance = queue.popleft()
            distances.append(distance)
            for neighbor in adjacency[node] - seen:
                seen.add(neighbor)
                queue.append((neighbor, distance + 1))
    derivations = {item["derivation_id"]: item for item in trace["derivations"]}
    semantics = {
        **{item["concept_id"]: item for item in trace["concepts"]},
        **{item["edge_id"]: item for item in trace["semantic_edges"]},
    }
    derivation_depths = [item["declared_depth"] for item in derivations.values()]
    support_derivation_ids = {
        item["evidence_derivation_id"] for item in trace["epistemic_events"]
        if item["event_kind"] == "SUPPORT"
    }

    # A supported lineage is conservative: the derivation itself must have a
    # SUPPORT event and every semantic premise's immutable creation derivation
    # must also have one.  Alternative reinforcement is never silently chosen
    # to make a lineage look deeper.
    supported_cache: dict[str, bool] = {}

    def lineage_is_supported(derivation_id: str) -> bool:
        if derivation_id in supported_cache:
            return supported_cache[derivation_id]
        if derivation_id not in support_derivation_ids:
            supported_cache[derivation_id] = False
            return False
        derivation = derivations[derivation_id]
        for premise in derivation["premise_refs"]:
            if premise["kind"] in SEMANTIC_KINDS:
                parent_creation = semantics[premise["id"]]["derivation_id"]
                if not lineage_is_supported(parent_creation):
                    supported_cache[derivation_id] = False
                    return False
        supported_cache[derivation_id] = True
        return True

    supported_depths = [
        derivation["declared_depth"]
        for derivation_id, derivation in derivations.items()
        if lineage_is_supported(derivation_id)
    ]

    experiences = {item["experience_id"]: item for item in trace["experiences"]}
    root_cache: dict[str, frozenset[str]] = {}

    def root_evidence(derivation_id: str) -> frozenset[str]:
        if derivation_id in root_cache:
            return root_cache[derivation_id]
        roots: set[str] = set()
        for premise in derivations[derivation_id]["premise_refs"]:
            if premise["kind"] == "experience":
                roots.add(experiences[premise["id"]]["payload_hash"])
            elif premise["kind"] in SEMANTIC_KINDS:
                roots.update(root_evidence(semantics[premise["id"]]["derivation_id"]))
        result = frozenset(roots)
        root_cache[derivation_id] = result
        return result

    support_by_semantic: dict[str, set[str]] = {}
    for event in trace["epistemic_events"]:
        if event["event_kind"] in {"CREATE", "SUPPORT"}:
            support_by_semantic.setdefault(event["subject_id"], set()).add(
                event["evidence_derivation_id"]
            )
    independent_support_by_semantic: dict[str, int] = {}
    for semantic_id, supporting in support_by_semantic.items():
        # Deterministic greedy set packing is a conservative lower bound: it
        # can undercount overlapping alternatives, but it cannot call shared
        # root evidence independent.  Smaller root sets are considered first.
        candidates = sorted(
            ((root_evidence(item), item) for item in supporting if root_evidence(item)),
            key=lambda pair: (len(pair[0]), tuple(sorted(pair[0])), pair[1]),
        )
        used: set[str] = set()
        count = 0
        for roots, _ in candidates:
            if used.isdisjoint(roots):
                used.update(roots)
                count += 1
        independent_support_by_semantic[semantic_id] = count

    hypotheses = {
        item["hypothesis_id"]: item for item in trace["thinker_hypotheses"]
    }

    def released_path_size(hypothesis_id: str) -> int:
        support_edges = set(hypotheses[hypothesis_id]["release_support_semantic_ids"])
        introduced: set[str] = set()
        completed: set[str] = set()
        support_depth: dict[str, int] = {}

        def visit(current_id: str) -> int:
            if current_id in completed:
                return support_depth[current_id]
            current = hypotheses[current_id]
            parent_depth = max(
                (visit(parent) for parent in current["parent_hypothesis_ids"]),
                default=0,
            )
            novel = (set(current["cited_semantic_ids"]) & support_edges) - introduced
            if novel:
                introduced.update(novel)
                support_depth[current_id] = parent_depth + 1
            else:
                support_depth[current_id] = parent_depth
            completed.add(current_id)
            return support_depth[current_id]

        return len(support_edges) + visit(hypothesis_id)

    thinker_depths = [
        released_path_size(hypothesis_id)
        for hypothesis_id, hypothesis in hypotheses.items()
        if hypothesis["disposition"] == "released"
    ]
    derivation_lineage_depth = max(derivation_depths, default=0)
    supported_derivation_depth = max(supported_depths, default=0)
    semantic_structural_hops = max(distances, default=0)
    independent_support_depth = max(independent_support_by_semantic.values(), default=0)
    thinker_compositional_depth = max(thinker_depths, default=0)
    realization_count = len(trace["realization_specs"])
    return {
        "derivation_lineage_depth": derivation_lineage_depth,
        "supported_derivation_depth": supported_derivation_depth,
        "semantic_structural_hops": semantic_structural_hops,
        "independent_support_depth": independent_support_depth,
        "thinker_compositional_depth": thinker_compositional_depth,
        "realization_count": realization_count,
        "structure": {
            "concept_count": len(trace["concepts"]),
            "edge_count": len(trace["semantic_edges"]),
            "unique_semantic_hashes": len({
                item["semantic_hash"]
                for item in [*trace["concepts"], *trace["semantic_edges"]]
            }),
            "component_count": components,
            "max_shortest_path": semantic_structural_hops,
        },
        "derivation": {
            "derivation_count": len(derivation_depths),
            "max_depth": derivation_lineage_depth,
            "supported_max_depth": supported_derivation_depth,
            "independent_support_by_semantic": dict(sorted(
                independent_support_by_semantic.items()
            )),
            "depth_histogram": dict(sorted(Counter(derivation_depths).items())),
        },
        "realization": {
            "spec_count": realization_count,
            "total_touches": sum(item["touches"] for item in trace["touch_plans"]),
            "forms": dict(sorted(Counter(
                item["form"] for item in trace["realization_specs"]
            ).items())),
        },
        "thinker": {
            "state_count": len(trace["thinker_states"]),
            "hypothesis_count": len(trace["thinker_hypotheses"]),
            "confusion_count": len(trace["thinker_confusions"]),
            "desire_count": len(trace["thinker_desires"]),
            "compositional_depth": thinker_compositional_depth,
        },
    }
