"""Provider-bound, target-blind scientific dream proposal adapter.

This module is deliberately disjoint from the recurrent scheduler.  It
serializes only the bounded public view already present in ``DreamRequest``,
calls a fresh provider session through :mod:`model_provider_boundary`, parses
exactly one typed local proposal, and applies an independent admission policy.

The model can propose a mutation and local citations.  It cannot set
``mark_supported``.  For the v0.3-R ``causal_join`` relation, support is granted
only by a mechanical route/effect join over supported recipient-local memory.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
import json
import re
from typing import Any, Literal, Mapping, Protocol

from .model_provider_boundary import (
    ExactProviderCall,
    IsolatedModelProviderBoundary,
    ProviderCallArtifact,
    ProviderCallScope,
    ProviderExpectations,
)
from .recurrent_text_organism import (
    DreamRequest,
    MemoryItemView,
    PremiseIdentity,
    SCIENTIFIC_CAUSAL_JOIN_RELATION,
    SchedulerError,
    SemanticDecision,
)


REQUEST_SCHEMA_VERSION = "scientific-dream-request-v1.0"
CONFIG_SCHEMA_VERSION = "scientific-dream-config-v1.0"
RESULT_SCHEMA_VERSION = "scientific-dream-execution-v1.0"

_ATOM = re.compile(r"[A-Za-z0-9_.:\-]+")
_HASH = re.compile(r"[0-9a-f]{64}")
_ROUTE = re.compile(
    r"route_record connector=([A-Za-z0-9_.:\-]+) "
    r"source=([A-Za-z0-9_.:\-]+)"
)
_EFFECT = re.compile(
    r"effect_record connector=([A-Za-z0-9_.:\-]+) "
    r"target=([A-Za-z0-9_.:\-]+) observed=([A-Za-z0-9_.:\-]+)"
)
_KINDS = frozenset({
    "PASS", "CREATE_CONCEPT", "CREATE_EDGE", "REINFORCE", "SUPERSEDE",
})
_V03R_WITNESS_KINDS = frozenset({
    "source_anchor_color", "target_passive_baseline", "valve_route",
    "intervention_effect",
})
_V03R_CONCEPT_PREFIXES = (
    "entity:source:", "entity:target:", "record:route:", "record:effect:",
)


class ScientificDreamError(ValueError):
    """Raised when a scientific dream call cannot preserve its boundary."""


def _canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
    ).encode("utf-8")


def _pairs_without_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ScientificDreamError(f"model proposal contains duplicate key {key!r}")
        result[key] = value
    return result


def _reject_json_constant(value: str) -> None:
    raise ScientificDreamError(f"model proposal contains invalid JSON constant {value}")


def _require_exact_keys(value: Mapping[str, Any], expected: set[str], path: str) -> None:
    actual = set(value)
    if actual != expected:
        raise ScientificDreamError(
            f"{path} must have exact fields; missing={sorted(expected - actual)}, "
            f"extra={sorted(actual - expected)}"
        )


def _require_text(value: Any, path: str, *, atom: bool = False) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > 4096:
        raise ScientificDreamError(f"{path} must be bounded non-empty text")
    if atom and _ATOM.fullmatch(value) is None:
        raise ScientificDreamError(f"{path} must be one canonical atom")
    return value


def _public_experience_payload(item: Any) -> dict[str, Any]:
    return {
        "citation": {"kind": "experience", "identity": item.payload_hash},
        "sequence_index": item.sequence_index,
        "action": item.action,
        "observation": item.observation,
        "outcome": item.outcome,
    }


def _memory_payload(item: MemoryItemView) -> dict[str, Any]:
    return {
        "citation": {"kind": item.kind, "identity": item.semantic_hash},
        "canonical_text": item.canonical_text,
        "status": item.status,
        "entity_id": item.entity_id,
        "source_entity_id": item.source_entity_id,
        "relation_id": item.relation_id,
        "target_entity_id": item.target_entity_id,
    }


def canonical_target_blind_request(request: DreamRequest) -> bytes:
    """Compile exact model bytes from only the already-bounded request view.

    Logical life, trigger, arm/selection-mode, donor, query/control keys,
    checkpoint/goal bindings, full-memory condition labels, and any scorer
    state are intentionally absent.  A selection query contributes only its
    semantic focus tuple; it is explicitly non-evidentiary.
    """

    if not isinstance(request, DreamRequest):
        raise ScientificDreamError("scientific dream input must be DreamRequest")
    if request.stage not in {
        "WAKE", "REACTIVATE", "TARGET_BLIND_SLEEP", "RETURN_SLEEP",
    }:
        raise ScientificDreamError("dream request has an unknown stage")
    for name in ("round_index", "call_index", "declared_semantic_neighbor_k"):
        value = getattr(request, name)
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ScientificDreamError(f"dream request {name} is invalid")
    if request.non_evidentiary_selection is not True:
        raise ScientificDreamError("dream selection must remain non-evidentiary")
    experiences = sorted(
        request.visible_experiences,
        key=lambda item: (item.sequence_index, item.payload_hash),
    )
    if len({item.payload_hash for item in experiences}) != len(experiences):
        raise ScientificDreamError("bounded dream view repeats an experience")
    memory = sorted(request.memory, key=lambda item: item.semantic_hash)
    if len({item.semantic_hash for item in memory}) != len(memory):
        raise ScientificDreamError("bounded dream view repeats a semantic item")
    for item in memory:
        if item.kind not in {"concept", "semantic_edge"} \
                or _HASH.fullmatch(item.semantic_hash) is None:
            raise ScientificDreamError("bounded memory contains an invalid semantic item")
    focuses = []
    for query in request.selection_queries:
        try:
            query.validate()
        except SchedulerError as exc:
            raise ScientificDreamError("selection focus is not a typed agenda query") from exc
        focuses.append({
            "kind": query.kind,
            "left_id": query.left_id,
            "relation_id": query.relation_id,
            "right_id": query.right_id,
        })
    payload = {
        "schema_version": REQUEST_SCHEMA_VERSION,
        "task": "propose_exactly_one_local_semantic_mutation",
        "stage": request.stage,
        "round_index": request.round_index,
        "call_index": request.call_index,
        "visible_experiences": [_public_experience_payload(item) for item in experiences],
        "bounded_memory": [_memory_payload(item) for item in memory],
        "selection_focus": sorted(
            focuses,
            key=lambda item: (
                item["kind"], item["left_id"], item["relation_id"], item["right_id"],
            ),
        ),
        "constraints": {
            "one_typed_proposal": True,
            "local_citations_only": True,
            "selection_focus_is_evidence": False,
            "model_may_assign_support": False,
        },
        "view_budget": {
            "experience_count": len(experiences),
            "semantic_item_count": len(memory),
            "declared_semantic_neighbor_k": request.declared_semantic_neighbor_k,
        },
    }
    result = _canonical_json_bytes(payload)
    forbidden_keys = (
        b"logical_life", b"arm_id", b"selection_mode", b"donor",
        b"control", b"final_goal", b"scorer", b"answer_valve",
        b"ground_truth", b"query_key", b"source_goal_id",
        b"source_checkpoint_hash", b"vocabulary_hash", b"trigger_id",
    )
    lowered = result.lower()
    if any(marker in lowered for marker in forbidden_keys):
        raise ScientificDreamError("target-blind request contains a forbidden identifier")
    excluded_identifiers = [
        request.logical_life_id, request.trigger_id, request.selection_mode,
        request.selection_donor_life_id,
    ]
    for query in request.selection_queries:
        excluded_identifiers.extend((
            query.query_key, query.source_checkpoint_hash, query.source_goal_id,
            query.vocabulary_hash,
        ))
    for identifier in excluded_identifiers:
        if isinstance(identifier, str) and identifier \
                and identifier.casefold().encode("utf-8") in lowered:
            raise ScientificDreamError(
                "target-blind request collides with excluded routing metadata"
            )
    return result


@dataclass(frozen=True)
class ScientificDreamConfig:
    temperature: float
    top_p: float
    max_output_tokens: int
    seed: int

    def validate(self) -> None:
        if isinstance(self.temperature, bool) or not isinstance(
            self.temperature, (int, float)
        ) or not 0 <= float(self.temperature) <= 100:
            raise ScientificDreamError("temperature must be in [0,100]")
        if isinstance(self.top_p, bool) or not isinstance(
            self.top_p, (int, float)
        ) or not 0 < float(self.top_p) <= 1:
            raise ScientificDreamError("top_p must be in (0,1]")
        if isinstance(self.max_output_tokens, bool) or not isinstance(
            self.max_output_tokens, int
        ) or not 1 <= self.max_output_tokens <= 1_000_000:
            raise ScientificDreamError("max_output_tokens is invalid")
        if isinstance(self.seed, bool) or not isinstance(self.seed, int) or self.seed < 0:
            raise ScientificDreamError("seed must be a non-negative integer")

    def exact_bytes(self) -> bytes:
        self.validate()
        return _canonical_json_bytes({
            "schema_version": CONFIG_SCHEMA_VERSION,
            "temperature": float(self.temperature),
            "top_p": float(self.top_p),
            "max_output_tokens": self.max_output_tokens,
            "seed": self.seed,
        })


def _local_premises(value: Any, request: DreamRequest) -> tuple[PremiseIdentity, ...]:
    if not isinstance(value, list) or not value or len(value) > 32:
        raise ScientificDreamError("proposal premises must be one bounded non-empty list")
    experience_ids = {item.payload_hash for item in request.visible_experiences}
    memory_kinds = {item.semantic_hash: item.kind for item in request.memory}
    premises: list[PremiseIdentity] = []
    for index, row in enumerate(value):
        if not isinstance(row, Mapping):
            raise ScientificDreamError(f"proposal.premises[{index}] must be an object")
        _require_exact_keys(row, {"kind", "identity"}, f"proposal.premises[{index}]")
        kind = row["kind"]
        identity = row["identity"]
        if kind not in {"experience", "concept", "semantic_edge"}:
            raise ScientificDreamError("proposal premise kind is not local evidence")
        if not isinstance(identity, str) or _HASH.fullmatch(identity) is None:
            raise ScientificDreamError("proposal premise identity must be one semantic hash")
        if kind == "experience":
            if identity not in experience_ids:
                raise ScientificDreamError("proposal cites experience outside bounded view")
        elif memory_kinds.get(identity) != kind:
            raise ScientificDreamError("proposal cites semantic memory outside bounded view")
        premises.append(PremiseIdentity(kind, identity))
    if len({(item.kind, item.identity) for item in premises}) != len(premises):
        raise ScientificDreamError("proposal repeats a premise")
    return tuple(premises)


def parse_local_proposal(raw_response: bytes, request: DreamRequest) -> SemanticDecision:
    """Strictly parse one response object into an unsupported local proposal."""

    if not isinstance(raw_response, bytes):
        raise ScientificDreamError("raw model response must be exact bytes")
    try:
        text = raw_response.decode("utf-8", errors="strict")
        value = json.loads(
            text, object_pairs_hook=_pairs_without_duplicates,
            parse_constant=_reject_json_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ScientificDreamError("model response must be one strict UTF-8 JSON object") from exc
    if not isinstance(value, Mapping):
        raise ScientificDreamError("model response must be one proposal object")
    kind = value.get("kind")
    if kind not in _KINDS:
        raise ScientificDreamError("model proposal kind is not allowlisted")
    if kind == "PASS":
        _require_exact_keys(value, {"kind"}, "PASS proposal")
        return SemanticDecision.pass_()
    if kind == "CREATE_CONCEPT":
        _require_exact_keys(
            value,
            {"kind", "canonical_key", "display_label", "rule", "premises"},
            "CREATE_CONCEPT proposal",
        )
        decision = SemanticDecision.concept(
            canonical_key=_require_text(value["canonical_key"], "canonical_key", atom=True),
            display_label=_require_text(value["display_label"], "display_label"),
            rule=_require_text(value["rule"], "rule"),
            premises=_local_premises(value["premises"], request),
            mark_supported=False,
        )
    elif kind == "CREATE_EDGE":
        _require_exact_keys(
            value,
            {
                "kind", "source_semantic_hash", "relation",
                "target_semantic_hash", "rule", "premises",
            },
            "CREATE_EDGE proposal",
        )
        decision = SemanticDecision.edge(
            source_semantic_hash=_require_text(
                value["source_semantic_hash"], "source_semantic_hash", atom=True,
            ),
            relation=_require_text(value["relation"], "relation", atom=True),
            target_semantic_hash=_require_text(
                value["target_semantic_hash"], "target_semantic_hash", atom=True,
            ),
            rule=_require_text(value["rule"], "rule"),
            premises=_local_premises(value["premises"], request),
            mark_supported=False,
        )
    elif kind == "REINFORCE":
        _require_exact_keys(
            value, {"kind", "subject_semantic_hash", "rule", "premises"},
            "REINFORCE proposal",
        )
        decision = SemanticDecision(
            kind="REINFORCE",
            subject_semantic_hash=_require_text(
                value["subject_semantic_hash"], "subject_semantic_hash", atom=True,
            ),
            rule=_require_text(value["rule"], "rule"),
            premises=_local_premises(value["premises"], request),
            mark_supported=False,
        )
    else:
        concept_fields = {
            "kind", "canonical_key", "display_label", "superseded_semantic_hash",
            "rule", "premises",
        }
        edge_fields = {
            "kind", "source_semantic_hash", "relation", "target_semantic_hash",
            "superseded_semantic_hash", "rule", "premises",
        }
        if set(value) == concept_fields:
            decision = SemanticDecision(
                kind="SUPERSEDE",
                canonical_key=_require_text(
                    value["canonical_key"], "canonical_key", atom=True,
                ),
                display_label=_require_text(value["display_label"], "display_label"),
                superseded_semantic_hash=_require_text(
                    value["superseded_semantic_hash"],
                    "superseded_semantic_hash", atom=True,
                ),
                rule=_require_text(value["rule"], "rule"),
                premises=_local_premises(value["premises"], request),
                mark_supported=False,
            )
        elif set(value) == edge_fields:
            decision = SemanticDecision(
                kind="SUPERSEDE",
                source_semantic_hash=_require_text(
                    value["source_semantic_hash"], "source_semantic_hash", atom=True,
                ),
                relation=_require_text(value["relation"], "relation", atom=True),
                target_semantic_hash=_require_text(
                    value["target_semantic_hash"], "target_semantic_hash", atom=True,
                ),
                superseded_semantic_hash=_require_text(
                    value["superseded_semantic_hash"],
                    "superseded_semantic_hash", atom=True,
                ),
                rule=_require_text(value["rule"], "rule"),
                premises=_local_premises(value["premises"], request),
                mark_supported=False,
            )
        else:
            raise ScientificDreamError("SUPERSEDE proposal has the wrong exact shape")
    memory_by_hash = {item.semantic_hash: item for item in request.memory}
    if decision.kind in {"CREATE_EDGE", "SUPERSEDE"} \
            and decision.source_semantic_hash is not None:
        for endpoint in (
            decision.source_semantic_hash, decision.target_semantic_hash,
        ):
            item = memory_by_hash.get(str(endpoint))
            if item is None or item.kind != "concept":
                raise ScientificDreamError("edge endpoint is outside local concept memory")
    if decision.kind == "REINFORCE" \
            and decision.subject_semantic_hash not in memory_by_hash:
        raise ScientificDreamError("reinforcement subject is outside local memory")
    if decision.kind == "SUPERSEDE" \
            and decision.superseded_semantic_hash not in memory_by_hash:
        raise ScientificDreamError("superseded subject is outside local memory")
    try:
        decision.validate()
    except SchedulerError as exc:
        raise ScientificDreamError("typed proposal violates SemanticDecision") from exc
    if decision.mark_supported:
        raise ScientificDreamError("model proposal cannot assign support")
    return decision


@dataclass(frozen=True)
class AdmissionResult:
    outcome: Literal["ADMITTED_PROVISIONAL", "ADMITTED_SUPPORTED", "REJECTED"]
    decision: SemanticDecision | None
    reason: str


class SemanticAdmissionProtocol(Protocol):
    def admit(self, proposal: SemanticDecision, request: DreamRequest) -> AdmissionResult: ...


class V03RMechanicalSemanticAdmission:
    """Mechanical support gate for one public route/effect causal join."""

    @staticmethod
    def _experience_by_hash(request: DreamRequest) -> dict[str, Any]:
        return {item.payload_hash: item for item in request.visible_experiences}

    @staticmethod
    def _strict_public_record(experience: Any) -> Mapping[str, Any]:
        try:
            observation = json.loads(
                experience.observation,
                object_pairs_hook=_pairs_without_duplicates,
                parse_constant=_reject_json_constant,
            )
        except (json.JSONDecodeError, ScientificDreamError) as exc:
            raise ScientificDreamError(
                "v0.3-R witness observation must be strict JSON"
            ) from exc
        if not isinstance(observation, Mapping):
            raise ScientificDreamError("v0.3-R witness observation must be an object")
        _require_exact_keys(
            observation, {"text", "public_record"}, "v0.3-R witness observation",
        )
        if not isinstance(observation["text"], str) or not observation["text"].strip():
            raise ScientificDreamError("v0.3-R witness text must be non-empty")
        record = observation["public_record"]
        if not isinstance(record, Mapping):
            raise ScientificDreamError("v0.3-R witness public_record must be an object")
        return record

    @staticmethod
    def _ratio_fields(record: Mapping[str, Any], path: str) -> None:
        label = record.get("label")
        ratio = record.get("ratio")
        if not isinstance(label, str) or not label.strip():
            raise ScientificDreamError(f"{path}.label must be non-empty text")
        if not isinstance(ratio, list) or len(ratio) != 3 or any(
            isinstance(item, bool) or not isinstance(item, int) or item < 0
            for item in ratio
        ):
            raise ScientificDreamError(
                f"{path}.ratio must be three non-negative public counts"
            )

    def _admit_public_concept(
        self, proposal: SemanticDecision, request: DreamRequest,
    ) -> AdmissionResult | None:
        assert proposal.kind == "CREATE_CONCEPT"
        experiences = self._experience_by_hash(request)
        cited_experiences = [
            experiences.get(item.identity)
            for item in proposal.premises if item.kind == "experience"
        ]
        cited_witness_kind = any(
            item is not None and item.outcome in _V03R_WITNESS_KINDS
            for item in cited_experiences
        )
        has_v03r_key = str(proposal.canonical_key).startswith(_V03R_CONCEPT_PREFIXES)
        if not cited_witness_kind and not has_v03r_key:
            return None
        if len(proposal.premises) != 1 \
                or proposal.premises[0].kind != "experience":
            return AdmissionResult(
                "REJECTED", None,
                "v0.3-R public concept requires exactly one experience witness",
            )
        experience = experiences.get(proposal.premises[0].identity)
        if experience is None:
            return AdmissionResult(
                "REJECTED", None, "v0.3-R concept witness is outside bounded view",
            )
        kind = experience.outcome
        if kind not in _V03R_WITNESS_KINDS:
            return AdmissionResult(
                "REJECTED", None, "experience kind cannot witness a v0.3-R concept",
            )
        try:
            record = self._strict_public_record(experience)
            if kind == "source_anchor_color":
                _require_exact_keys(
                    record, {"anchor_id", "source_id", "label", "ratio"},
                    "source_anchor_color public_record",
                )
                self._ratio_fields(record, "source_anchor_color public_record")
                if record["anchor_id"] != "animal_00":
                    raise ScientificDreamError(
                        "source endpoint requires the public animal_00 anchor"
                    )
                source_id = _require_text(
                    record["source_id"], "source_anchor_color.source_id", atom=True,
                )
                canonical_key = f"entity:source:{source_id}"
                display_label = canonical_key
            elif kind == "target_passive_baseline":
                _require_exact_keys(
                    record, {"target_id", "anchor_id", "label", "ratio"},
                    "target_passive_baseline public_record",
                )
                self._ratio_fields(record, "target_passive_baseline public_record")
                if record["anchor_id"] != "animal_00":
                    raise ScientificDreamError(
                        "target endpoint requires the public animal_00 anchor"
                    )
                target_id = _require_text(
                    record["target_id"], "target_passive_baseline.target_id", atom=True,
                )
                canonical_key = f"entity:target:{target_id}"
                display_label = canonical_key
            elif kind == "valve_route":
                _require_exact_keys(
                    record, {"valve_id", "source_id"}, "valve_route public_record",
                )
                connector = _require_text(
                    record["valve_id"], "valve_route.valve_id", atom=True,
                )
                source_id = _require_text(
                    record["source_id"], "valve_route.source_id", atom=True,
                )
                source = f"entity:source:{source_id}"
                canonical_key = f"record:route:{connector}:{source}"
                display_label = f"route_record connector={connector} source={source}"
            else:
                _require_exact_keys(
                    record, {"valve_id", "target_id", "effect"},
                    "intervention_effect public_record",
                )
                connector = _require_text(
                    record["valve_id"], "intervention_effect.valve_id", atom=True,
                )
                target_id = _require_text(
                    record["target_id"], "intervention_effect.target_id", atom=True,
                )
                effect = _require_text(
                    record["effect"], "intervention_effect.effect", atom=True,
                )
                target = f"entity:target:{target_id}"
                canonical_key = f"record:effect:{connector}:{target}:{effect}"
                display_label = (
                    f"effect_record connector={connector} target={target} "
                    f"observed={effect}"
                )
        except ScientificDreamError as exc:
            return AdmissionResult("REJECTED", None, str(exc))
        if proposal.canonical_key != canonical_key:
            return AdmissionResult(
                "REJECTED", None,
                "v0.3-R concept canonical key does not match its public witness",
            )
        if proposal.display_label != display_label:
            return AdmissionResult(
                "REJECTED", None,
                "v0.3-R concept display label does not match its public witness",
            )
        admitted = replace(proposal, mark_supported=True)
        admitted.validate()
        return AdmissionResult(
            "ADMITTED_SUPPORTED", admitted,
            f"one exact public {kind} record witnesses this concept",
        )

    def admit(self, proposal: SemanticDecision, request: DreamRequest) -> AdmissionResult:
        if proposal.mark_supported:
            return AdmissionResult("REJECTED", None, "proposal attempted to assign support")
        if proposal.kind == "CREATE_CONCEPT":
            witnessed = self._admit_public_concept(proposal, request)
            if witnessed is not None:
                return witnessed
        if proposal.kind == "REINFORCE":
            return AdmissionResult(
                "REJECTED", None,
                "REINFORCE requires an independent mechanical support policy",
            )
        if proposal.kind == "SUPERSEDE" and \
                proposal.relation == SCIENTIFIC_CAUSAL_JOIN_RELATION:
            return AdmissionResult(
                "REJECTED", None, "causal_join cannot enter through SUPERSEDE",
            )
        if proposal.kind != "CREATE_EDGE" \
                or proposal.relation != SCIENTIFIC_CAUSAL_JOIN_RELATION:
            return AdmissionResult("ADMITTED_PROVISIONAL", proposal, "local typed proposal")
        memory = {item.semantic_hash: item for item in request.memory}
        source = memory.get(str(proposal.source_semantic_hash))
        target = memory.get(str(proposal.target_semantic_hash))
        if source is None or target is None or source.kind != "concept" \
                or target.kind != "concept" or not source.entity_id or not target.entity_id:
            return AdmissionResult("REJECTED", None, "causal_join endpoints are not local concepts")
        cited = [memory.get(item.identity) for item in proposal.premises]
        if any(item is None for item in cited) or any(
            premise.kind != "concept" for premise in proposal.premises
        ):
            return AdmissionResult(
                "REJECTED", None, "causal_join requires only local concept citations",
            )
        if len(cited) != 4 or len({item.semantic_hash for item in cited if item}) != 4:
            return AdmissionResult(
                "REJECTED", None, "causal_join requires exactly four distinct citations",
            )
        cited_items = [item for item in cited if item is not None]
        if source not in cited_items or target not in cited_items:
            return AdmissionResult(
                "REJECTED", None, "causal_join must cite both endpoint concepts",
            )
        route_rows = []
        effect_rows = []
        for item in cited_items:
            if item.status != "supported":
                return AdmissionResult(
                    "REJECTED", None, "causal_join citations must already be supported",
                )
            route = _ROUTE.fullmatch(item.canonical_text)
            effect = _EFFECT.fullmatch(item.canonical_text)
            if route is not None:
                route_rows.append((item, route.groups()))
            if effect is not None:
                effect_rows.append((item, effect.groups()))
        if len(route_rows) != 1 or len(effect_rows) != 1:
            return AdmissionResult(
                "REJECTED", None, "causal_join needs one route and one effect record",
            )
        _, (route_connector, route_source) = route_rows[0]
        _, (effect_connector, effect_target, _observed) = effect_rows[0]
        if route_connector != effect_connector:
            return AdmissionResult(
                "REJECTED", None, "route and effect connectors do not match",
            )
        if route_source != source.entity_id or effect_target != target.entity_id:
            return AdmissionResult(
                "REJECTED", None, "route/effect records do not match edge endpoints",
            )
        admitted = replace(proposal, mark_supported=True)
        admitted.validate()
        return AdmissionResult(
            "ADMITTED_SUPPORTED", admitted,
            "one supported local route/effect pair witnesses the causal join",
        )


@dataclass(frozen=True)
class ScientificDreamExecution:
    schema_version: str
    provider_artifact: ProviderCallArtifact
    parser_outcome: Literal["PARSED", "REJECTED"]
    parser_error: str | None
    proposed_decision: SemanticDecision | None
    admission_outcome: Literal[
        "ADMITTED_PROVISIONAL", "ADMITTED_SUPPORTED", "REJECTED"
    ]
    admission_reason: str
    admitted_decision: SemanticDecision | None

    def __post_init__(self) -> None:
        if self.schema_version != RESULT_SCHEMA_VERSION:
            raise ScientificDreamError("scientific dream result schema mismatch")
        self.provider_artifact.validate()
        if self.parser_outcome == "PARSED":
            if self.proposed_decision is None or self.parser_error is not None:
                raise ScientificDreamError("parsed result lacks one proposal")
            self.proposed_decision.validate()
            if self.proposed_decision.mark_supported:
                raise ScientificDreamError("parsed model proposal assigned support")
        elif self.parser_outcome == "REJECTED":
            if self.proposed_decision is not None or not self.parser_error:
                raise ScientificDreamError("rejected parse lacks bounded error")
        else:
            raise ScientificDreamError("unknown parser outcome")
        if self.admission_outcome == "REJECTED":
            if self.admitted_decision is not None:
                raise ScientificDreamError("rejected admission carried a decision")
        elif self.admitted_decision is None:
            raise ScientificDreamError("successful admission lacks a decision")
        if not isinstance(self.admission_reason, str) or not self.admission_reason:
            raise ScientificDreamError("admission outcome lacks a reason")


class ScientificDreamAdapter:
    """Provider-only scientific path; completed decisions are forbidden."""

    def __init__(
        self, boundary: IsolatedModelProviderBoundary,
        expectations: ProviderExpectations,
        admission: SemanticAdmissionProtocol,
    ) -> None:
        self._boundary = boundary
        self._expectations = expectations
        self._admission = admission

    def execute(
        self, request: DreamRequest, scope: ProviderCallScope,
        config: ScientificDreamConfig,
        *, direct_completed_decision: SemanticDecision | None = None,
    ) -> ScientificDreamExecution:
        if direct_completed_decision is not None:
            raise ScientificDreamError(
                "scientific mode forbids a direct completed semantic decision"
            )
        if scope.round_index != request.round_index or scope.stage != request.stage \
                or scope.call_index != request.call_index:
            raise ScientificDreamError("provider scope does not match dream call position")
        exact_request = canonical_target_blind_request(request)
        exact_config = config.exact_bytes()
        provider_artifact = self._boundary.invoke(ExactProviderCall(
            scope=scope, request_bytes=exact_request, config_bytes=exact_config,
            expectations=self._expectations,
        ))
        try:
            proposal = parse_local_proposal(
                provider_artifact.raw_response_bytes, request,
            )
        except ScientificDreamError as exc:
            return ScientificDreamExecution(
                RESULT_SCHEMA_VERSION, provider_artifact, "REJECTED", str(exc),
                None, "REJECTED", "strict typed parser rejected provider output", None,
            )
        admitted = self._admission.admit(proposal, request)
        return ScientificDreamExecution(
            RESULT_SCHEMA_VERSION, provider_artifact, "PARSED", None, proposal,
            admitted.outcome, admitted.reason, admitted.decision,
        )
