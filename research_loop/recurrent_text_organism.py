"""CPU-only scheduler for the recurrent dream -> memory -> think organism.

The module deliberately stops at deterministic artifacts.  It accepts an
injectable semantic dreamer and thinker, records every bounded call, compiles
accepted semantic items into multiple *write realizations*, and emits traces
validated by :mod:`research_loop.cyclic_organism_contract`.  It never calls a
model, trains an adapter, scores hidden truth, or contains a game solver.

The first frozen fixture is::

    46 WAKE + 22 REACTIVATE + 16 target-blind SLEEP
      -> MEMORY_0 -> identical intermediate THINK_0
      -> 16 target-blind RETURN_SLEEP selected by arm
      -> MEMORY_1 -> fresh final THINK_1

The implementation is round-general even though that fixture has one return
edge.  Thinker feedback is selection-only.  It is never admitted as a
derivation premise, and the matched-distractor control carries no foreign
memory records.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from copy import deepcopy
from dataclasses import dataclass, field
import hashlib
import json
import re
from typing import Any, Literal, Protocol

from .cyclic_organism_contract import (
    PHASES,
    SCHEMA_VERSION as CYCLIC_SCHEMA_VERSION,
    agenda_digest,
    assert_valid_dataset,
    assert_valid_trace,
    concept_semantic_hash,
    derivation_digest,
    edge_semantic_hash,
    experience_payload_hash,
    hypothesis_digest,
    phase_barrier_digest,
    realization_digest,
    realization_state_digest,
    semantic_state_digest,
    sha256_json,
    thinker_state_digest,
    touch_plan_digest,
)
from .goal_conditioned_thinker import (
    digest as hardened_thinker_digest,
    validate_agenda as validate_hardened_thinker_agenda,
)


SCHEMA_VERSION = "recurrent-text-organism-v1.0"
ARM_NAMES = ("no_feedback", "agenda_feedback", "matched_distractor")
SCIENTIFIC_CAUSAL_JOIN_RELATION = "causal_join"
V03R_GPU_P1_BLOCKERS = (
    "rendered-text-and-order-shortcut-audit",
    "public-final-goal-thinker-and-paired-scoring",
)
CALL_STAGES = frozenset({"WAKE", "REACTIVATE", "TARGET_BLIND_SLEEP", "RETURN_SLEEP"})
DECISION_KINDS = frozenset({"PASS", "CREATE_CONCEPT", "CREATE_EDGE", "REINFORCE", "SUPERSEDE"})
AGENDA_KINDS = frozenset({
    "missing_dependency", "conflict", "weak_read", "stalled_chain",
    "provisional_relation",
})
_SAFE_ID = re.compile(r"[^A-Za-z0-9_.:-]+")
_AGENDA_ATOM = re.compile(r"[A-Za-z0-9_.:-]+")


class SchedulerError(ValueError):
    """Raised when a schedule, public input, or injected operation is unsafe."""


def _identifier(value: str) -> str:
    cleaned = _SAFE_ID.sub("-", value.strip()).strip("-")
    if not cleaned:
        raise SchedulerError("identifier cannot normalize to empty")
    return cleaned


def _scope_prefix(world_id: str, skin_id: str, life_id: str) -> str:
    return "rt-" + hashlib.sha256(
        f"{world_id}\0{skin_id}\0{life_id}".encode("utf-8")
    ).hexdigest()[:12]


@dataclass(frozen=True)
class PublicExperience:
    """One immutable public action/observation/outcome event."""

    public_id: str
    sequence_index: int
    action: str
    observation: str
    outcome: str

    @property
    def payload_hash(self) -> str:
        return experience_payload_hash(self.action, self.observation, self.outcome)


@dataclass(frozen=True)
class PublicLife:
    """Public inputs for one logical life; hidden answers are intentionally absent."""

    logical_life_id: str
    world_id: str
    skin_id: str
    split: str
    experiences: tuple[PublicExperience, ...]
    intermediate_goal_id: str
    intermediate_goal: str
    final_goal_id: str
    final_goal: str
    final_goal_forbidden_markers: tuple[str, ...] = ()
    agenda_vocabularies: tuple["AgendaVocabulary", ...] = ()
    model_visible_life_id: str | None = None

    def validate(self) -> None:
        for field_name in (
            "logical_life_id", "world_id", "skin_id", "split",
            "intermediate_goal_id", "intermediate_goal", "final_goal_id", "final_goal",
        ):
            if not str(getattr(self, field_name)).strip():
                raise SchedulerError(f"PublicLife.{field_name} must be non-empty")
        if not self.experiences:
            raise SchedulerError("PublicLife.experiences must be non-empty")
        if self.model_visible_life_id is not None \
                and not self.model_visible_life_id.strip():
            raise SchedulerError("model-visible life id cannot be empty")
        indices = [item.sequence_index for item in self.experiences]
        if indices != list(range(len(self.experiences))):
            raise SchedulerError("public experiences must have contiguous sequence indices")
        ids = [item.public_id for item in self.experiences]
        if len(ids) != len(set(ids)):
            raise SchedulerError("public experience ids must be unique within a life")
        hashes = [item.payload_hash for item in self.experiences]
        if len(hashes) != len(set(hashes)):
            raise SchedulerError("public experience payloads must be unique within a life")
        goal_ids = {self.intermediate_goal_id, self.final_goal_id}
        vocabulary_goals: set[str] = set()
        for vocabulary in self.agenda_vocabularies:
            vocabulary.validate()
            if vocabulary.goal_id not in goal_ids:
                raise SchedulerError("agenda vocabulary binds an unknown public goal")
            if vocabulary.goal_id in vocabulary_goals:
                raise SchedulerError("only one agenda vocabulary is allowed per goal")
            vocabulary_goals.add(vocabulary.goal_id)

    def agenda_vocabulary(self, goal_id: str) -> "AgendaVocabulary | None":
        return next(
            (item for item in self.agenda_vocabularies if item.goal_id == goal_id), None
        )

    @property
    def visible_life_id(self) -> str:
        return self.model_visible_life_id or self.logical_life_id


@dataclass(frozen=True)
class ReturnRoundSpec:
    dream_calls: int
    thinker_budget: int
    reveal_final_goal: bool = False

    def validate(self) -> None:
        if self.dream_calls < 1 or self.thinker_budget < 1:
            raise SchedulerError("return-round dream and thinker budgets must be positive")


@dataclass(frozen=True)
class FrozenSchedule:
    expected_wake_calls: int = 46
    reactivation_calls: int = 22
    target_blind_sleep_calls: int = 16
    initial_thinker_budget: int = 12
    dream_semantic_neighbor_k: int = 6
    full_memory_ceiling: bool = False
    return_rounds: tuple[ReturnRoundSpec, ...] = (
        ReturnRoundSpec(dream_calls=16, thinker_budget=12, reveal_final_goal=True),
    )

    def validate(self) -> None:
        if min(
            self.expected_wake_calls,
            self.reactivation_calls,
            self.target_blind_sleep_calls,
            self.initial_thinker_budget,
            self.dream_semantic_neighbor_k,
        ) < 1:
            raise SchedulerError("all frozen schedule budgets must be positive")
        if not self.return_rounds:
            raise SchedulerError("at least one return round is required")
        for item in self.return_rounds:
            item.validate()
        reveals = [index for index, item in enumerate(self.return_rounds) if item.reveal_final_goal]
        if reveals != [len(self.return_rounds) - 1]:
            raise SchedulerError("only the last return round may reveal the final goal")

    @property
    def round_count(self) -> int:
        return 1 + len(self.return_rounds)

    @property
    def dream_calls_per_arm(self) -> int:
        return (
            self.expected_wake_calls + self.reactivation_calls
            + self.target_blind_sleep_calls
            + sum(item.dream_calls for item in self.return_rounds)
        )


@dataclass(frozen=True)
class PremiseIdentity:
    """Content identity, resolved to a local record only during assembly."""

    kind: Literal["experience", "concept", "semantic_edge"]
    identity: str


@dataclass(frozen=True)
class SemanticDecision:
    """At most one local semantic mutation from one dream call."""

    kind: Literal["PASS", "CREATE_CONCEPT", "CREATE_EDGE", "REINFORCE", "SUPERSEDE"]
    rule: str = ""
    premises: tuple[PremiseIdentity, ...] = ()
    canonical_key: str | None = None
    display_label: str | None = None
    source_semantic_hash: str | None = None
    relation: str | None = None
    target_semantic_hash: str | None = None
    subject_semantic_hash: str | None = None
    superseded_semantic_hash: str | None = None
    mark_supported: bool = False

    @classmethod
    def pass_(cls) -> "SemanticDecision":
        return cls(kind="PASS")

    @classmethod
    def concept(
        cls, *, canonical_key: str, display_label: str, rule: str,
        premises: Sequence[PremiseIdentity], mark_supported: bool = False,
    ) -> "SemanticDecision":
        return cls(
            kind="CREATE_CONCEPT", canonical_key=canonical_key,
            display_label=display_label, rule=rule, premises=tuple(premises),
            mark_supported=mark_supported,
        )

    @classmethod
    def edge(
        cls, *, source_semantic_hash: str, relation: str,
        target_semantic_hash: str, rule: str,
        premises: Sequence[PremiseIdentity], mark_supported: bool = False,
    ) -> "SemanticDecision":
        return cls(
            kind="CREATE_EDGE", source_semantic_hash=source_semantic_hash,
            relation=relation, target_semantic_hash=target_semantic_hash,
            rule=rule, premises=tuple(premises), mark_supported=mark_supported,
        )

    @property
    def conclusion_semantic_hash(self) -> str | None:
        if self.kind in {"CREATE_CONCEPT", "SUPERSEDE"} and self.canonical_key:
            return concept_semantic_hash(self.canonical_key)
        if (
            self.kind in {"CREATE_EDGE", "SUPERSEDE"} and self.source_semantic_hash
            and self.relation and self.target_semantic_hash
        ):
            return edge_semantic_hash(
                self.source_semantic_hash, self.relation, self.target_semantic_hash,
            )
        if self.kind == "REINFORCE":
            return self.subject_semantic_hash
        return None

    def validate(self) -> None:
        if self.kind not in DECISION_KINDS:
            raise SchedulerError(f"unknown semantic decision {self.kind!r}")
        if self.kind == "PASS":
            if any((self.rule, self.premises, self.canonical_key, self.display_label,
                    self.source_semantic_hash, self.relation, self.target_semantic_hash,
                    self.subject_semantic_hash, self.superseded_semantic_hash,
                    self.mark_supported)):
                raise SchedulerError("PASS cannot smuggle semantic content")
            return
        if not self.rule.strip() or not self.premises:
            raise SchedulerError("semantic mutation needs a rule and evidentiary premises")
        if len({(item.kind, item.identity) for item in self.premises}) != len(self.premises):
            raise SchedulerError("duplicate premise identities cannot inflate support")
        if any(item.kind not in {"experience", "concept", "semantic_edge"}
               for item in self.premises):
            raise SchedulerError("only local public/semantic records are evidence")
        if self.kind == "CREATE_CONCEPT":
            if not self.canonical_key or not self.display_label:
                raise SchedulerError("concept creation needs key and label")
        elif self.kind == "SUPERSEDE":
            concept_shape = bool(self.canonical_key and self.display_label)
            edge_shape = bool(
                self.source_semantic_hash and self.relation and self.target_semantic_hash
            )
            if concept_shape == edge_shape or not self.superseded_semantic_hash:
                raise SchedulerError(
                    "SUPERSEDE needs exactly one concept/edge replacement and one prior hash"
                )
        elif self.kind == "CREATE_EDGE":
            if not all((self.source_semantic_hash, self.relation, self.target_semantic_hash)):
                raise SchedulerError("edge creation needs two semantic endpoints and relation")
        elif self.kind == "REINFORCE" and not self.subject_semantic_hash:
            raise SchedulerError("REINFORCE needs an existing semantic hash")


@dataclass(frozen=True)
class MemoryItemView:
    semantic_hash: str
    kind: Literal["concept", "semantic_edge"]
    canonical_text: str
    status: str
    entity_id: str | None = None
    source_entity_id: str | None = None
    relation_id: str | None = None
    target_entity_id: str | None = None


@dataclass(frozen=True)
class AgendaQueryTemplate:
    query_key: str
    kind: str
    left_id: str
    relation_id: str
    right_id: str

    def validate(self) -> None:
        if self.kind not in AGENDA_KINDS:
            raise SchedulerError("agenda template kind is not allowlisted")
        for name in ("query_key", "left_id", "relation_id", "right_id"):
            value = getattr(self, name)
            if not isinstance(value, str) or _AGENDA_ATOM.fullmatch(value) is None:
                raise SchedulerError(f"agenda template {name} must be one opaque atom")


@dataclass(frozen=True)
class AgendaVocabulary:
    goal_id: str
    templates: tuple[AgendaQueryTemplate, ...]
    vocabulary_hash: str

    @classmethod
    def freeze(
        cls, goal_id: str, templates: Sequence[AgendaQueryTemplate],
    ) -> "AgendaVocabulary":
        material = {
            "goal_id": goal_id,
            "templates": [vars(item) for item in templates],
        }
        result = cls(goal_id, tuple(templates), sha256_json(material))
        result.validate()
        return result

    def validate(self) -> None:
        if not self.goal_id.strip() or not self.templates:
            raise SchedulerError("agenda vocabulary needs a goal and templates")
        for item in self.templates:
            item.validate()
        if len({item.query_key for item in self.templates}) != len(self.templates):
            raise SchedulerError("agenda vocabulary query keys must be unique")
        expected = sha256_json({
            "goal_id": self.goal_id,
            "templates": [vars(item) for item in self.templates],
        })
        if self.vocabulary_hash != expected:
            raise SchedulerError("agenda vocabulary hash mismatch")

    def template(self, query_key: str) -> AgendaQueryTemplate | None:
        return next((item for item in self.templates if item.query_key == query_key), None)


@dataclass(frozen=True)
class AgendaQuery:
    query_key: str
    kind: str
    left_id: str
    relation_id: str
    right_id: str
    source_checkpoint_hash: str
    source_goal_id: str
    vocabulary_hash: str

    @property
    def canonical(self) -> str:
        return (
            f"{self.kind.upper()} | LEFT={self.left_id} | "
            f"RELATION={self.relation_id} | RIGHT={self.right_id} | QUERY={self.query_key}"
        )

    def validate(self) -> None:
        if self.kind not in AGENDA_KINDS:
            raise SchedulerError("agenda query kind is not allowlisted")
        for name in (
            "query_key", "left_id", "relation_id", "right_id", "source_goal_id",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or _AGENDA_ATOM.fullmatch(value) is None:
                raise SchedulerError(f"agenda query {name} must be one canonical atom")
        if not re.fullmatch(r"[0-9a-f]{64}", self.source_checkpoint_hash):
            raise SchedulerError("agenda query must bind one checkpoint hash")
        if not re.fullmatch(r"[0-9a-f]{64}", self.vocabulary_hash):
            raise SchedulerError("agenda query must bind one vocabulary hash")


@dataclass(frozen=True)
class DreamRequest:
    logical_life_id: str
    round_index: int
    stage: str
    call_index: int
    trigger_id: str
    visible_experiences: tuple[PublicExperience, ...]
    memory: tuple[MemoryItemView, ...]
    selection_queries: tuple[AgendaQuery, ...]
    selection_mode: str
    selection_donor_life_id: str | None
    declared_semantic_neighbor_k: int
    full_memory_ceiling: bool
    non_evidentiary_selection: Literal[True] = True


@dataclass(frozen=True)
class ThinkerRequest:
    logical_life_id: str
    world_id: str
    skin_id: str
    life_id: str
    round_index: int
    checkpoint_id: str
    checkpoint_hash: str
    checkpoint_semantic_hash: str
    snapshot_compiler_id: str
    snapshot_hash: str
    goal_id: str
    goal: str
    memory: tuple[MemoryItemView, ...]
    operation_budget: int
    agenda_vocabulary: AgendaVocabulary | None
    arm_id: str
    reset_id: str
    fresh_workspace: Literal[True] = True


class ScientificGoalCompilerProtocol(Protocol):
    """Scheduler-owned compiler for one exact public scientific objective."""

    compiler_id: str

    def compile_goal(
        self, request: ThinkerRequest, checkpoint_payload: Mapping[str, Any],
    ) -> Mapping[str, Any]: ...


def compile_canonical_hardened_checkpoint(
    request: ThinkerRequest,
) -> tuple[dict[str, Any], dict[str, str]]:
    """Rebuild the sole hardened checkpoint authorized by ``request``.

    This function belongs to the scheduler trust boundary.  Scientific
    execution objects may carry a copy for audit, but replay never consumes
    that copy.
    """

    from .goal_conditioned_thinker import (
        freeze_checkpoint, make_checkpoint, make_semantic_item,
    )

    concepts = {
        item.entity_id: item for item in request.memory
        if item.kind == "concept" and item.entity_id is not None
    }
    if len(concepts) != sum(
        item.kind == "concept" and item.entity_id is not None
        for item in request.memory
    ):
        raise SchedulerError("committed snapshot has duplicate entity handles")
    relation_ids = {
        item.relation_id for item in request.memory
        if item.kind == "semantic_edge" and item.relation_id is not None
    }
    if request.agenda_vocabulary is not None:
        request.agenda_vocabulary.validate()
        relation_ids.update(
            template.relation_id for template in request.agenda_vocabulary.templates
        )
    relation_ids.add(SCIENTIFIC_CAUSAL_JOIN_RELATION)
    relations = [{
        "relation_id": relation,
        "label": relation.replace("_", " "),
        "cardinality": (
            "ONE" if relation == SCIENTIFIC_CAUSAL_JOIN_RELATION else "MANY"
        ),
        "max_results": (
            1 if relation == SCIENTIFIC_CAUSAL_JOIN_RELATION else 16
        ),
    } for relation in sorted(relation_ids)]
    semantic_to_memory: dict[str, str] = {}
    rows: list[dict[str, Any]] = []
    edge_views = [item for item in request.memory if item.kind == "semantic_edge"]
    for item in sorted(edge_views, key=lambda row: row.semantic_hash):
        if not all((item.source_entity_id, item.relation_id, item.target_entity_id)):
            raise SchedulerError("semantic edge lacks typed checkpoint endpoints")
        if item.source_entity_id not in concepts or item.target_entity_id not in concepts:
            raise SchedulerError("semantic edge endpoint is outside exact checkpoint")
        semantic_id = f"sem:{item.semantic_hash}"
        if semantic_id in semantic_to_memory:
            raise SchedulerError("committed snapshot has duplicate semantic hashes")
        semantic_to_memory[semantic_id] = item.semantic_hash
        linked = sorted(
            f"sem:{other.semantic_hash}"
            for other in edge_views
            if other.semantic_hash != item.semantic_hash
            and item.target_entity_id == other.source_entity_id
        )
        rows.append(make_semantic_item(
            semantic_id,
            kind="semantic_edge",
            subject_entity_id=str(item.source_entity_id),
            relation_id=str(item.relation_id),
            object_entity_id=str(item.target_entity_id),
            content=item.canonical_text,
            status=item.status,
            linked_semantic_ids=linked,
            source_ids=(item.semantic_hash,),
        ))
    checkpoint = make_checkpoint(
        request.checkpoint_id,
        world_id=request.world_id,
        skin_id=request.skin_id,
        life_id=request.life_id,
        round_index=request.round_index,
        source_checkpoint_hash=request.checkpoint_hash,
        entities=[
            {"entity_id": entity_id, "label": view.canonical_text}
            for entity_id, view in sorted(concepts.items())
        ],
        relation_specs=relations,
        items=rows,
    )
    freeze_checkpoint(checkpoint)
    return checkpoint, semantic_to_memory


def compile_trusted_scientific_inputs(
    request: ThinkerRequest,
    goal_compiler: ScientificGoalCompilerProtocol,
) -> tuple[dict[str, Any], dict[str, str], dict[str, Any]]:
    """Compile checkpoint and goal independently of an execution response."""

    compile_goal = getattr(goal_compiler, "compile_goal", None)
    if not callable(compile_goal):
        raise SchedulerError("scientific mode requires a scheduler-owned goal compiler")
    checkpoint, semantic_to_memory = compile_canonical_hardened_checkpoint(request)
    protected_checkpoint = deepcopy(checkpoint)
    goal_value = compile_goal(request, protected_checkpoint)
    if protected_checkpoint != checkpoint:
        raise SchedulerError("scientific goal compiler mutated the trusted checkpoint")
    if not isinstance(goal_value, Mapping):
        raise SchedulerError("scientific goal compiler returned a non-object")
    goal = deepcopy(dict(goal_value))
    # Require the same canonical JSON domain consumed by the hardened machine.
    try:
        json.dumps(goal, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    except (TypeError, ValueError) as exc:
        raise SchedulerError("scientific goal is not canonical JSON") from exc
    return checkpoint, semantic_to_memory, goal


@dataclass(frozen=True)
class ThinkerResult:
    retrieved_semantic_hashes: tuple[str, ...]
    workspace: tuple[str, ...]
    claim: str
    cited_semantic_hashes: tuple[str, ...]
    confidence: float
    disposition: Literal["tentative", "released", "deferred"]
    unresolved_dependency: str | None = None
    attempted_queries: tuple[str, ...] = ()
    missing_semantic_keys: tuple[str, ...] = ()
    agenda_queries: tuple[AgendaQuery, ...] = ()

    def validate(self, request: ThinkerRequest) -> None:
        available = {item.semantic_hash for item in request.memory}
        if not set(self.retrieved_semantic_hashes) <= available:
            raise SchedulerError("thinker retrieved outside the frozen checkpoint")
        if not set(self.cited_semantic_hashes) <= set(self.retrieved_semantic_hashes):
            raise SchedulerError("thinker cited memory it did not retrieve")
        if not self.claim.strip() or not 0 <= self.confidence <= 1:
            raise SchedulerError("thinker result needs a claim and confidence in [0,1]")
        if self.disposition not in {"tentative", "released", "deferred"}:
            raise SchedulerError("unknown thinker disposition")
        if self.unresolved_dependency is None and (
            self.attempted_queries or self.missing_semantic_keys
        ):
            raise SchedulerError("confusion detail requires an unresolved dependency")
        for query in self.agenda_queries:
            query.validate()
            if query.source_checkpoint_hash != request.checkpoint_hash:
                raise SchedulerError("agenda query is not bound to this thinker checkpoint")
            if query.source_goal_id != request.goal_id:
                raise SchedulerError("agenda query is not bound to this thinker goal")
            vocabulary = request.agenda_vocabulary
            if vocabulary is None:
                raise SchedulerError("thinker emitted agenda without a frozen vocabulary")
            vocabulary.validate()
            if query.vocabulary_hash != vocabulary.vocabulary_hash:
                raise SchedulerError("agenda query is not bound to the frozen vocabulary")
            template = vocabulary.template(query.query_key)
            if template is None or (
                query.kind, query.left_id, query.relation_id, query.right_id
            ) != (
                template.kind, template.left_id, template.relation_id, template.right_id
            ):
                raise SchedulerError("agenda query is not an exact registered template")
            checkpoint_entities = {
                item.entity_id for item in request.memory
                if item.kind == "concept" and item.entity_id is not None
            }
            if query.left_id not in checkpoint_entities or query.right_id not in checkpoint_entities:
                raise SchedulerError("agenda query entity is not in the frozen checkpoint")
        if self.agenda_queries and self.unresolved_dependency is None:
            raise SchedulerError("agenda projection requires one typed confusion")
        if len(self.agenda_queries) > 1:
            raise SchedulerError("v1 permits exactly one agenda frontier item per think round")


class SemanticDreamerProtocol(Protocol):
    def dream(self, request: DreamRequest) -> SemanticDecision: ...


class ThinkerProtocol(Protocol):
    def think(self, request: ThinkerRequest) -> ThinkerResult: ...


@dataclass(frozen=True)
class ScientificThinkerExecution:
    """Authoritative hardened-machine execution plus its narrow projection."""

    adapter_id: str
    condition_label: str
    execution_kind: Literal["scripted_ceiling", "model_science"]
    objective_binding: Literal["exact_request_goal", "recurrence_probe_ceiling"]
    result: ThinkerResult
    machine_artifact: Mapping[str, Any]
    agenda_artifact: Mapping[str, Any] | None
    model_call_ledger: tuple[Mapping[str, Any], ...]
    model_call_materials: tuple[Mapping[str, str], ...]
    compiled_checkpoint: Mapping[str, Any]
    compiled_goal: Mapping[str, Any]

    def validate(
        self,
        request: ThinkerRequest,
        *,
        trusted_goal_compiler: ScientificGoalCompilerProtocol,
        trusted_inputs: tuple[
            Mapping[str, Any], Mapping[str, str], Mapping[str, Any]
        ] | None = None,
    ) -> None:
        if trusted_inputs is None:
            trusted_checkpoint, semantic_to_memory, trusted_goal = \
                compile_trusted_scientific_inputs(request, trusted_goal_compiler)
        else:
            trusted_checkpoint = deepcopy(dict(trusted_inputs[0]))
            semantic_to_memory = dict(trusted_inputs[1])
            trusted_goal = deepcopy(dict(trusted_inputs[2]))
        if dict(self.compiled_checkpoint) != trusted_checkpoint:
            raise SchedulerError(
                "execution checkpoint differs from scheduler reconstruction"
            )
        if dict(self.compiled_goal) != trusted_goal:
            raise SchedulerError("execution goal differs from scheduler reconstruction")
        if not self.condition_label.strip():
            raise SchedulerError("scientific thinker condition label is required")
        if self.execution_kind not in {"scripted_ceiling", "model_science"}:
            raise SchedulerError("scientific thinker execution kind is not explicit")
        if self.objective_binding not in {
            "exact_request_goal", "recurrence_probe_ceiling",
        }:
            raise SchedulerError("scientific thinker objective binding is not explicit")
        if self.objective_binding == "recurrence_probe_ceiling":
            if self.execution_kind != "scripted_ceiling":
                raise SchedulerError("model science cannot substitute a recurrence probe")
        elif trusted_goal.get("public_context", {}).get(
            "source_request_goal_id"
        ) != request.goal_id:
            raise SchedulerError("scientific goal is not bound to the requested objective")
        artifact = self.machine_artifact
        if artifact.get("schema_version") != "typed-goal-thinker-v1.1":
            raise SchedulerError("scientific thinker returned the wrong machine schema")
        material = {key: value for key, value in artifact.items() if key != "trace_hash"}
        if artifact.get("trace_hash") != hardened_thinker_digest(material):
            raise SchedulerError("scientific thinker machine artifact hash mismatch")
        scope = artifact.get("scope")
        if scope != {
            "world_id": request.world_id,
            "skin_id": request.skin_id,
            "life_id": request.life_id,
        }:
            raise SchedulerError("scientific thinker machine crossed scope")
        if artifact.get("source_checkpoint_hash") != request.checkpoint_hash:
            raise SchedulerError("scientific thinker is not bound to committed checkpoint")
        from .model_call_ledger import (
            CallMaterials, ImmutableModelCallLedger, record_from_mapping,
        )

        if len(self.model_call_ledger) != len(self.model_call_materials):
            raise SchedulerError("scientific ledger lost exact model-call materials")
        ledger = ImmutableModelCallLedger()
        for record_value, material_value in zip(
            self.model_call_ledger, self.model_call_materials,
        ):
            if set(material_value) != {
                "call_id", "prompt", "prompt_template", "input_payload", "raw_output",
            }:
                raise SchedulerError("model-call material artifact has the wrong schema")
            record = record_from_mapping(record_value)
            if material_value["call_id"] != record.call_id:
                raise SchedulerError("model-call material/record IDs disagree")
            if record.arm != request.arm_id or record.round_index != request.round_index \
                    or record.reset_instance_id != request.reset_id:
                raise SchedulerError("model-call ledger crossed arm/round/reset boundary")
            if record.checkpoint_hash != trusted_checkpoint["checkpoint_hash"] \
                    or record.goal_hash != sha256_json(trusted_goal):
                raise SchedulerError(
                    "model-call ledger is not bound to reconstructed thinker inputs"
                )
            materials = CallMaterials(
                prompt=material_value["prompt"].encode("utf-8"),
                prompt_template=material_value["prompt_template"].encode("utf-8"),
                input_payload=material_value["input_payload"].encode("utf-8"),
                raw_output=material_value["raw_output"].encode("utf-8"),
            )
            ledger = ledger.append(record, materials)
        ledger.assert_reset_isolation()
        # Replay uses only scheduler-reconstructed inputs.  Execution-supplied
        # compiled objects above are redundant attestations, never authority.
        from .goal_conditioned_thinker import (
            ThinkerContractError, ThinkerMachine, canonical_json,
            freeze_checkpoint, parse_operation,
        )

        checkpoint = freeze_checkpoint(trusted_checkpoint)
        if trusted_goal != artifact.get("goal"):
            raise SchedulerError("replay goal differs from authoritative machine goal")
        replay = ThinkerMachine(
            checkpoint, trusted_goal, max_steps=request.operation_budget,
        )
        for record_value, material_value in zip(
            self.model_call_ledger, self.model_call_materials,
        ):
            if replay.terminal is not None:
                raise SchedulerError("model-call ledger continues after thinker terminal")
            public_state = replay.public_state()
            if material_value["input_payload"] != canonical_json(public_state):
                raise SchedulerError("model-call input is not the replayed thinker state")
            expected_prompt = (
                material_value["prompt_template"] + "\n" +
                material_value["input_payload"]
            )
            if material_value["prompt"] != expected_prompt:
                raise SchedulerError("model-call prompt is not template plus exact state")
            record = record_from_mapping(record_value)
            try:
                operation = parse_operation(material_value["raw_output"])
            except ThinkerContractError:
                if record.parser_outcome != "REJECTED":
                    raise SchedulerError("replay parser outcome disagrees with ledger")
                replay.record_rejected_attempt(
                    material_value["raw_output"], ThinkerContractError(
                        "policy output failed strict operation parser"
                    ),
                )
                replay.force_defer("POLICY_ERROR")
                break
            if record.parser_outcome != "PARSED":
                raise SchedulerError("valid replay operation was not ledgered as parsed")
            try:
                replay.apply(operation)
            except ThinkerContractError as exc:
                replay.record_rejected_attempt(operation, exc)
                replay.force_defer("POLICY_ERROR")
                break
        if replay.terminal is None:
            if len(self.model_call_ledger) >= request.operation_budget:
                replay.force_defer("BUDGET_EXHAUSTED")
            else:
                raise SchedulerError("scientific thinker stopped before a terminal state")
        replay_artifact = replay.artifact()
        if replay_artifact != dict(self.machine_artifact):
            raise SchedulerError("scientific machine artifact fails scheduler replay")
        expected_result, expected_agenda = project_replayed_thinker_result(
            replay_artifact,
            request,
            trusted_checkpoint=trusted_checkpoint,
            semantic_to_memory=semantic_to_memory,
        )
        if (
            None if self.agenda_artifact is None else dict(self.agenda_artifact)
        ) != expected_agenda:
            raise SchedulerError(
                "thinker agenda is not the exact mechanical replay projection"
            )
        if type(self.result) is not ThinkerResult or self.result != expected_result:
            raise SchedulerError(
                "thinker result is not the exact mechanical replay projection"
            )
        self.result.validate(request)

    def public_payload(self) -> dict[str, Any]:
        return {
            "adapter_id": self.adapter_id,
            "condition_label": self.condition_label,
            "execution_kind": self.execution_kind,
            "objective_binding": self.objective_binding,
            "machine_artifact": dict(self.machine_artifact),
            "agenda_artifact": (
                dict(self.agenda_artifact) if self.agenda_artifact is not None else None
            ),
            "model_call_ledger": [dict(item) for item in self.model_call_ledger],
            "model_call_materials": [dict(item) for item in self.model_call_materials],
            "compiled_checkpoint": dict(self.compiled_checkpoint),
            "compiled_goal": dict(self.compiled_goal),
        }


class ScientificThinkerMachineProtocol(Protocol):
    adapter_id: str

    def run_machine(self, request: ThinkerRequest) -> ScientificThinkerExecution: ...


def agenda_queries_from_hardened_thinker(
    agenda: Mapping[str, Any], request: ThinkerRequest,
    *, hardened_checkpoint_hash: str | None = None,
    source_checkpoint_hash: str | None = None,
) -> tuple[AgendaQuery, ...]:
    """Map the hardened thinker projection into registry-bound query keys.

    The thinker contributes only a mechanically projected ``subject`` and
    ``relation`` from a NOT_FOUND/CONFLICT read.  The system-owned vocabulary
    selects the unique full query tuple (including the right-hand entity), so
    model text cannot manufacture an allowed-looking answer atom.
    """
    try:
        validate_hardened_thinker_agenda(agenda)
    except Exception as exc:
        raise SchedulerError(f"invalid hardened thinker agenda: {exc}") from exc
    if request.agenda_vocabulary is None:
        raise SchedulerError("hardened agenda has no goal-owned query vocabulary")
    expected_scope = {
        "world_id": request.world_id, "skin_id": request.skin_id,
        "life_id": request.life_id,
    }
    for key, expected in expected_scope.items():
        if agenda.get(key) != expected:
            raise SchedulerError("hardened agenda crosses recipient scope")
    expected_hardened_hash = hardened_checkpoint_hash or request.checkpoint_hash
    expected_source_hash = source_checkpoint_hash or request.checkpoint_semantic_hash
    if agenda.get("checkpoint_id") != request.checkpoint_id \
            or agenda.get("checkpoint_hash") != expected_hardened_hash:
        raise SchedulerError("hardened agenda is not bound to recipient checkpoint")
    if agenda.get("source_checkpoint_hash") != expected_source_hash \
            or agenda.get("round_index") != request.round_index:
        raise SchedulerError("hardened agenda source checkpoint/round mismatch")
    queries: list[AgendaQuery] = []
    kind_map = {"MISSING_DEPENDENCY": "missing_dependency", "CONFLICT": "conflict"}
    for item in agenda["items"]:
        kind = kind_map[item["kind"]]
        matches = [
            template for template in request.agenda_vocabulary.templates
            if template.kind == kind
            and template.query_key == item["query_key"]
            and template.left_id == item["subject_entity_id"]
            and template.relation_id == item["relation_id"]
        ]
        if len(matches) != 1:
            raise SchedulerError("hardened agenda item has no unique system query key")
        template = matches[0]
        queries.append(AgendaQuery(
            query_key=template.query_key, kind=template.kind,
            left_id=template.left_id, relation_id=template.relation_id,
            right_id=template.right_id,
            source_checkpoint_hash=request.checkpoint_hash,
            source_goal_id=request.goal_id,
            vocabulary_hash=request.agenda_vocabulary.vocabulary_hash,
        ))
    return tuple(queries)


def project_replayed_thinker_result(
    artifact: Mapping[str, Any],
    request: ThinkerRequest,
    *,
    trusted_checkpoint: Mapping[str, Any],
    semantic_to_memory: Mapping[str, str],
) -> tuple[ThinkerResult, dict[str, Any] | None]:
    """Mechanically project one already replayed terminal machine artifact.

    No policy- or adapter-authored summary field survives this projection.
    Unknown hardened semantic IDs fail closed instead of being silently
    omitted from the compact scheduler view.
    """

    from .goal_conditioned_thinker import (
        ThinkerContractError, project_non_evidentiary_agenda,
    )

    retrieved_ids = {
        item["semantic_id"]
        for step in artifact.get("trace", [])
        if isinstance(step.get("outcome"), Mapping)
        for item in step["outcome"].get("items", [])
        if isinstance(item, Mapping) and isinstance(item.get("semantic_id"), str)
    }
    unknown_retrieved = retrieved_ids - set(semantic_to_memory)
    if unknown_retrieved:
        raise SchedulerError("replayed thinker retrieved an unknown semantic ID")
    retrieved = tuple(sorted(semantic_to_memory[item_id] for item_id in retrieved_ids))
    terminal = artifact.get("terminal")
    if not isinstance(terminal, Mapping):
        raise SchedulerError("replayed thinker lacks a typed terminal")
    terminal_kind = terminal.get("kind")
    if terminal_kind == "RELEASE":
        support_ids = terminal.get("support_path_semantic_ids")
        if not isinstance(support_ids, list) or any(
            not isinstance(item_id, str) for item_id in support_ids
        ):
            raise SchedulerError("replayed release lacks a typed support path")
        unknown_support = set(support_ids) - set(semantic_to_memory)
        if unknown_support:
            raise SchedulerError("replayed release cites an unknown semantic ID")
        result = ThinkerResult(
            retrieved_semantic_hashes=retrieved,
            workspace=("fresh hardened machine released a directed path",),
            claim=str(terminal["output"]),
            cited_semantic_hashes=tuple(
                semantic_to_memory[item_id] for item_id in support_ids
            ),
            confidence=1.0,
            disposition="released",
        )
        agenda = None
    elif terminal_kind == "REQUEST_DREAM":
        try:
            agenda = project_non_evidentiary_agenda(artifact)
        except ThinkerContractError as exc:
            raise SchedulerError("replayed agenda projection failed") from exc
        queries = agenda_queries_from_hardened_thinker(
            agenda,
            request,
            hardened_checkpoint_hash=str(trusted_checkpoint["checkpoint_hash"]),
            source_checkpoint_hash=request.checkpoint_hash,
        )
        if len(queries) != 1:
            raise SchedulerError("replayed thinker must project exactly one query")
        result = ThinkerResult(
            retrieved_semantic_hashes=retrieved,
            workspace=("fresh hardened machine encountered a typed missing read",),
            claim="one public causal dependency remains unresolved",
            cited_semantic_hashes=(),
            confidence=0.0,
            disposition="deferred",
            unresolved_dependency=queries[0].query_key,
            attempted_queries=(queries[0].query_key,),
            missing_semantic_keys=(queries[0].right_id,),
            agenda_queries=queries,
        )
    elif terminal_kind == "DEFER":
        agenda = None
        result = ThinkerResult(
            retrieved_semantic_hashes=retrieved,
            workspace=("fresh hardened machine deferred without release",),
            claim="committed memory does not support a directed release",
            cited_semantic_hashes=(),
            confidence=0.0,
            disposition="deferred",
        )
    else:
        raise SchedulerError("replayed thinker has an unknown terminal kind")
    result.validate(request)
    return result, agenda


@dataclass(frozen=True)
class FrozenCheckpointView:
    """Scope-neutral committed memory content before a reader is invoked."""

    checkpoint_id: str
    logical_life_id: str
    round_index: int
    semantic_state_hash: str
    checkpoint_hash: str
    semantic_items: tuple[MemoryItemView, ...]


class CheckpointToThinkerSnapshotCompilerProtocol(Protocol):
    """Seam for text, recognition, RAG, or read-only adapter snapshots."""

    compiler_id: str

    def compile(self, checkpoint: FrozenCheckpointView) -> tuple[MemoryItemView, ...]: ...


class AgendaVocabularyCompilerProtocol(Protocol):
    """Public-only compiler invoked after a semantic checkpoint is committed."""

    compiler_id: str

    def compile(
        self, life: PublicLife, checkpoint: FrozenCheckpointView, goal_id: str,
    ) -> AgendaVocabulary | None: ...


class DeterministicTextSnapshotCompiler:
    """CPU gold/text compiler; a ceiling, not autonomous memory reading."""

    compiler_id = "deterministic-gold-text-snapshot-v1"

    def compile(self, checkpoint: FrozenCheckpointView) -> tuple[MemoryItemView, ...]:
        if _semantic_snapshot_hash(checkpoint.semantic_items) != checkpoint.semantic_state_hash:
            raise SchedulerError("checkpoint content changed before snapshot compilation")
        return tuple(checkpoint.semantic_items)


@dataclass(frozen=True)
class FinalExpectation:
    """Private scorer input, kept outside every organism artifact."""

    pair_id: str
    logical_life_id: str
    expected: Any


@dataclass(frozen=True)
class PairedFinalScore:
    n_pairs: int
    both_correct: int
    member_correct: int
    member_total: int

    @property
    def paired_both_correct(self) -> float:
        return self.both_correct / self.n_pairs if self.n_pairs else 0.0

    @property
    def member_accuracy(self) -> float:
        return self.member_correct / self.member_total if self.member_total else 0.0


def score_final_pairs(
    expectations: Sequence[FinalExpectation], predictions: Mapping[str, Any],
) -> PairedFinalScore:
    """Primary paired score; hidden expectations never enter a run artifact."""
    grouped: dict[str, list[FinalExpectation]] = {}
    for item in expectations:
        grouped.setdefault(item.pair_id, []).append(item)
    if not grouped or any(len(items) != 2 for items in grouped.values()):
        raise SchedulerError("every final pair must contain exactly two logical lives")
    member_correct = 0
    both = 0
    for items in grouped.values():
        outcomes = [predictions.get(item.logical_life_id) == item.expected for item in items]
        member_correct += sum(outcomes)
        both += int(all(outcomes))
    return PairedFinalScore(len(grouped), both, member_correct, 2 * len(grouped))


class DeterministicRealizationCompiler:
    """Render write views without creating semantic structure or support."""

    forms = ("canonical", "qa", "reverse", "partial_cue")

    def render(self, semantic: Mapping[str, Any], concepts: Mapping[str, Mapping[str, Any]]) \
            -> tuple[tuple[str, str, str], ...]:
        memory_key = f"memory:{str(semantic['semantic_hash'])[:24]}"
        if "concept_id" in semantic:
            key = str(semantic["canonical_key"])
            label = str(semantic["display_label"])
            return (
                ("canonical", f"Recall durable concept {memory_key}.", label),
                ("qa", f"[{memory_key}] What concept is named by {key}?", label),
                ("reverse", f"[{memory_key}] Which durable key names {label}?", key),
                ("partial_cue", f"[{memory_key}] Complete: {key} means ...", label),
            )
        source = concepts[str(semantic["source_concept_id"])]["display_label"]
        target = concepts[str(semantic["target_concept_id"])]["display_label"]
        relation = str(semantic["relation"])
        statement = f"{source} {relation} {target}"
        return (
            ("canonical", f"Recall durable relation {memory_key}.", statement),
            ("qa", f"[{memory_key}] What relation links {source} to {target}?", relation),
            ("reverse", f"[{memory_key}] What does {source} {relation}?", str(target)),
            ("partial_cue", f"[{memory_key}] Complete: {source} {relation} ...", str(target)),
        )

    def touches(self, semantic: Mapping[str, Any], form: str) -> int:
        # Measured starting recipes: simple concepts receive 24 total touches;
        # relational lines receive 96 total touches.  This is an exposed write
        # budget, not evidence or an independent-support count.
        return 6 if "concept_id" in semantic else 24


@dataclass
class _LogicalSemantic:
    semantic_hash: str
    kind: Literal["concept", "semantic_edge"]
    canonical_text: str
    status: str
    entity_id: str | None = None
    source_entity_id: str | None = None
    relation_id: str | None = None
    target_entity_id: str | None = None


@dataclass
class _LogicalState:
    items: dict[str, _LogicalSemantic] = field(default_factory=dict)
    decisions_by_round: list[list[SemanticDecision]] = field(default_factory=list)

    def clone(self) -> "_LogicalState":
        return _LogicalState(
            items={key: _LogicalSemantic(**vars(value)) for key, value in self.items.items()},
            decisions_by_round=[list(items) for items in self.decisions_by_round],
        )

    def memory_view(self) -> tuple[MemoryItemView, ...]:
        return tuple(
            MemoryItemView(
                item.semantic_hash, item.kind, item.canonical_text, item.status,
                item.entity_id, item.source_entity_id, item.relation_id,
                item.target_entity_id,
            )
            for item in sorted(self.items.values(), key=lambda value: value.semantic_hash)
            if item.status in {"provisional", "supported"}
        )

    def apply(self, decision: SemanticDecision) -> None:
        decision.validate()
        if decision.kind == "PASS":
            return
        conclusion = decision.conclusion_semantic_hash
        if decision.kind in {"CREATE_CONCEPT", "CREATE_EDGE", "SUPERSEDE"}:
            assert conclusion is not None
            if conclusion in self.items:
                raise SchedulerError("duplicate semantic creation must be explicit reinforcement")
            creates_edge = decision.kind == "CREATE_EDGE" or (
                decision.kind == "SUPERSEDE" and decision.source_semantic_hash is not None
            )
            if creates_edge:
                if decision.source_semantic_hash not in self.items \
                        or decision.target_semantic_hash not in self.items:
                    raise SchedulerError("semantic edge endpoints must already exist")
                canonical = (
                    f"{self.items[str(decision.source_semantic_hash)].canonical_text} "
                    f"{decision.relation} "
                    f"{self.items[str(decision.target_semantic_hash)].canonical_text}"
                )
                kind: Literal["concept", "semantic_edge"] = "semantic_edge"
                entity_id = None
                source_entity_id = self.items[str(decision.source_semantic_hash)].entity_id
                relation_id = str(decision.relation)
                target_entity_id = self.items[str(decision.target_semantic_hash)].entity_id
            else:
                canonical = str(decision.display_label)
                kind = "concept"
                entity_id = str(decision.canonical_key)
                source_entity_id = relation_id = target_entity_id = None
            self.items[conclusion] = _LogicalSemantic(
                conclusion, kind, canonical,
                "supported" if decision.mark_supported else "provisional",
                entity_id, source_entity_id, relation_id, target_entity_id,
            )
            if decision.kind == "SUPERSEDE":
                old = self.items.get(str(decision.superseded_semantic_hash))
                if old is None or old.status not in {"provisional", "supported"}:
                    raise SchedulerError("SUPERSEDE target must be a live prior semantic")
                old.status = "superseded"
        elif decision.kind == "REINFORCE":
            item = self.items.get(str(decision.subject_semantic_hash))
            if item is None or item.status not in {"provisional", "supported"}:
                raise SchedulerError("REINFORCE target must be a live prior semantic")
            item.status = "supported"


def _bounded_dream_memory(
    state: _LogicalState,
    *,
    trigger_id: str,
    selection_queries: Sequence[AgendaQuery],
    neighbor_k: int,
    full_memory_ceiling: bool,
) -> tuple[MemoryItemView, ...]:
    """Return a deterministic bounded semantic neighborhood for one dream.

    Query fields only influence ordering.  They never create a record or
    become evidence.  Every returned item already belongs to the committed
    recipient-local semantic state, and the same fixed ``neighbor_k`` applies
    to every experimental arm.  Full-snapshot access is an explicit ceiling.
    """
    memory = state.memory_view()
    if full_memory_ceiling:
        return memory
    query_atoms = {
        atom
        for query in selection_queries
        for atom in (query.left_id, query.relation_id, query.right_id)
    }

    def priority(item: MemoryItemView) -> tuple[int, str]:
        item_atoms = {
            value for value in (
                item.entity_id, item.source_entity_id,
                item.relation_id, item.target_entity_id,
            ) if value is not None
        }
        lexical = sum(atom in item.canonical_text for atom in query_atoms)
        overlap = len(query_atoms & item_atoms) + lexical
        tie = sha256_json({"trigger_id": trigger_id, "semantic_hash": item.semantic_hash})
        return (-overlap, tie)

    return tuple(sorted(memory, key=priority)[:neighbor_k])


def _schedule_calls(
    life: PublicLife, schedule: FrozenSchedule, *, round_index: int,
    stage: str, count: int, state: _LogicalState,
    selection_queries: tuple[AgendaQuery, ...] = (),
    selection_mode: str = "intrinsic", donor_life_id: str | None = None,
    start_call_index: int = 0,
    trigger_offset: int = 0,
) -> list[DreamRequest]:
    requests: list[DreamRequest] = []
    for offset in range(count):
        if stage == "WAKE":
            experience = life.experiences[trigger_offset + offset]
            visible = (experience,)
            trigger_id = experience.public_id
        else:
            # Reactivation/sleep has no *new* experience, but it must retrieve
            # bounded earlier public evidence or it could never independently
            # derive an agenda-selected edge.  Deterministic cycling is only a
            # CPU fixture selector; a later model adapter may supply its own
            # target-blind local retriever under the same visibility contract.
            visible = (
                life.experiences[(trigger_offset + offset) % len(life.experiences)],
            )
            trigger_id = (
                f"{stage.casefold()}-{round_index}-{trigger_offset + offset}"
            )
        bounded_memory = _bounded_dream_memory(
            state, trigger_id=trigger_id, selection_queries=selection_queries,
            neighbor_k=schedule.dream_semantic_neighbor_k,
            full_memory_ceiling=schedule.full_memory_ceiling,
        )
        requests.append(DreamRequest(
            logical_life_id=life.visible_life_id,
            round_index=round_index, stage=stage,
            call_index=start_call_index + offset, trigger_id=trigger_id,
            visible_experiences=visible, memory=bounded_memory,
            selection_queries=selection_queries, selection_mode=selection_mode,
            selection_donor_life_id=donor_life_id,
            declared_semantic_neighbor_k=schedule.dream_semantic_neighbor_k,
            full_memory_ceiling=schedule.full_memory_ceiling,
        ))
    return requests


def deterministic_shuffle_donors(lives: Sequence[PublicLife]) -> dict[str, str]:
    """Derange donors across distinct worlds while preserving skin and split."""
    groups: dict[tuple[str, str], list[PublicLife]] = {}
    for life in lives:
        groups.setdefault((life.skin_id, life.split), []).append(life)
    donors: dict[str, str] = {}
    for key, group in groups.items():
        ordered = sorted(group, key=lambda item: (item.world_id, item.logical_life_id))
        distinct_worlds = {item.world_id for item in ordered}
        if len(distinct_worlds) < 2:
            raise SchedulerError(
                f"shuffled_feedback stratum {key} needs at least two distinct world seeds"
            )
        for index, recipient in enumerate(ordered):
            donor = None
            for shift in range(1, len(ordered) + 1):
                candidate = ordered[(index + shift) % len(ordered)]
                if candidate.world_id != recipient.world_id:
                    donor = candidate
                    break
            if donor is None:
                raise SchedulerError("could not construct a cross-world feedback derangement")
            donors[recipient.logical_life_id] = donor.logical_life_id
    return donors


def _decision_payload(decision: SemanticDecision) -> dict[str, Any]:
    return {
        "kind": decision.kind, "rule": decision.rule,
        "premises": [vars(item) for item in decision.premises],
        "canonical_key": decision.canonical_key, "display_label": decision.display_label,
        "source_semantic_hash": decision.source_semantic_hash,
        "relation": decision.relation, "target_semantic_hash": decision.target_semantic_hash,
        "subject_semantic_hash": decision.subject_semantic_hash,
        "superseded_semantic_hash": decision.superseded_semantic_hash,
        "mark_supported": decision.mark_supported,
    }


def _request_payload(request: DreamRequest) -> dict[str, Any]:
    return {
        "logical_life_id": request.logical_life_id,
        "round_index": request.round_index, "stage": request.stage,
        "call_index": request.call_index, "trigger_id": request.trigger_id,
        "visible_experience_hashes": [item.payload_hash for item in request.visible_experiences],
        "visible_semantic_hashes": [item.semantic_hash for item in request.memory],
        "selection_queries": [vars(item) for item in request.selection_queries],
        "selection_mode": request.selection_mode,
        "selection_donor_life_id": request.selection_donor_life_id,
        "declared_semantic_neighbor_k": request.declared_semantic_neighbor_k,
        "full_memory_ceiling": request.full_memory_ceiling,
        "non_evidentiary_selection": True,
        "final_goal_visible": False,
    }


def _thinker_payload(
    request: ThinkerRequest, result: ThinkerResult,
    execution: ScientificThinkerExecution | None = None,
) -> dict[str, Any]:
    payload = {
        "request": {
            "logical_life_id": request.logical_life_id,
            "world_id": request.world_id, "skin_id": request.skin_id,
            "life_id": request.life_id,
            "round_index": request.round_index,
            "checkpoint_id": request.checkpoint_id,
            "checkpoint_hash": request.checkpoint_hash,
            "checkpoint_semantic_hash": request.checkpoint_semantic_hash,
            "snapshot_compiler_id": request.snapshot_compiler_id,
            "snapshot_hash": request.snapshot_hash,
            "goal_id": request.goal_id, "goal": request.goal,
            "arm_id": request.arm_id, "reset_id": request.reset_id,
            "memory": [vars(item) for item in request.memory],
            "operation_budget": request.operation_budget,
            "agenda_vocabulary": (
                {
                    "goal_id": request.agenda_vocabulary.goal_id,
                    "templates": [vars(item) for item in request.agenda_vocabulary.templates],
                    "vocabulary_hash": request.agenda_vocabulary.vocabulary_hash,
                }
                if request.agenda_vocabulary is not None else None
            ),
            "fresh_workspace": True,
        },
        "result": {
            **vars(result),
            "agenda_queries": [vars(item) for item in result.agenda_queries],
        },
    }
    if execution is not None:
        payload["scientific_execution"] = execution.public_payload()
    return payload


def _execute_thinker(
    thinker: ThinkerProtocol | ScientificThinkerMachineProtocol,
    request: ThinkerRequest,
    *,
    scientific_mode: bool,
    trusted_goal_compiler: ScientificGoalCompilerProtocol | None = None,
) -> tuple[ThinkerResult, ScientificThinkerExecution | None]:
    if scientific_mode:
        runner = getattr(thinker, "run_machine", None)
        if runner is None or not callable(runner):
            raise SchedulerError(
                "scientific mode requires scheduler-owned ThinkerMachine execution; "
                "direct ThinkerResult is forbidden"
            )
        if trusted_goal_compiler is None or not callable(
            getattr(trusted_goal_compiler, "compile_goal", None)
        ):
            raise SchedulerError(
                "scientific mode requires a scheduler-owned trusted goal compiler"
            )
        # Freeze the trusted inputs before invoking adapter-owned code.  This
        # prevents a stateful adapter from mutating a shared compiler and then
        # asking validation to reconstruct against the changed compiler state.
        trusted_inputs = compile_trusted_scientific_inputs(
            request, trusted_goal_compiler,
        )
        execution = runner(request)
        if type(execution) is not ScientificThinkerExecution:
            raise SchedulerError("scientific thinker returned an untyped execution")
        ScientificThinkerExecution.validate(
            execution,
            request,
            trusted_goal_compiler=trusted_goal_compiler,
            trusted_inputs=trusted_inputs,
        )
        return execution.result, execution
    result = thinker.think(request)  # type: ignore[union-attr]
    result.validate(request)
    return result, None


def _run_calls(
    dreamer: SemanticDreamerProtocol, requests: Sequence[DreamRequest],
    state: _LogicalState,
) -> tuple[list[SemanticDecision], list[dict[str, Any]]]:
    decisions: list[SemanticDecision] = []
    records: list[dict[str, Any]] = []
    for request in requests:
        # Refresh memory at each call.  This is the one-node-at-a-time recurrence;
        # the request never receives a final goal or a donor's memory objects.
        refreshed = _bounded_dream_memory(
            state, trigger_id=request.trigger_id,
            selection_queries=request.selection_queries,
            neighbor_k=request.declared_semantic_neighbor_k,
            full_memory_ceiling=request.full_memory_ceiling,
        )
        request = DreamRequest(
            **{**vars(request), "memory": refreshed}
        )
        decision = dreamer.dream(request)
        decision.validate()
        visible_experience_hashes = {
            item.payload_hash for item in request.visible_experiences
        }
        visible_semantics = {
            item.semantic_hash: item.kind for item in request.memory
        }
        for premise in decision.premises:
            if premise.kind == "experience" and premise.identity not in visible_experience_hashes:
                raise SchedulerError("dream cited public experience outside its bounded view")
            if premise.kind in {"concept", "semantic_edge"} and \
                    visible_semantics.get(premise.identity) != premise.kind:
                raise SchedulerError("dream cited semantic memory outside its bounded view")
        state.apply(decision)
        decisions.append(decision)
        payload = {
            "request": _request_payload(request),
            "decision": _decision_payload(decision),
        }
        records.append({**payload, "call_hash": sha256_json(payload)})
    return decisions, records


def _semantic_snapshot_hash(memory: Sequence[MemoryItemView]) -> str:
    return sha256_json([vars(item) for item in memory])


def _freeze_checkpoint_view(
    life: PublicLife, state: _LogicalState, round_index: int,
    snapshot_compiler: CheckpointToThinkerSnapshotCompilerProtocol,
) -> tuple[FrozenCheckpointView, tuple[MemoryItemView, ...], str]:
    semantic_items = state.memory_view()
    semantic_hash = _semantic_snapshot_hash(semantic_items)
    checkpoint_id = f"{life.visible_life_id}:logical-checkpoint-r{round_index}"
    checkpoint_hash = sha256_json({
        "checkpoint_id": checkpoint_id,
        "world_id": life.world_id, "skin_id": life.skin_id,
        "life_id": life.visible_life_id, "round_index": round_index,
        "semantic_state_hash": semantic_hash,
    })
    checkpoint = FrozenCheckpointView(
        checkpoint_id=checkpoint_id,
        logical_life_id=life.visible_life_id, round_index=round_index,
        semantic_state_hash=semantic_hash, checkpoint_hash=checkpoint_hash,
        semantic_items=semantic_items,
    )
    snapshot = tuple(snapshot_compiler.compile(checkpoint))
    available = {item.semantic_hash: vars(item) for item in semantic_items}
    if any(
        item.semantic_hash not in available or vars(item) != available[item.semantic_hash]
        for item in snapshot
    ):
        raise SchedulerError(
            "snapshot compiler changed or introduced a committed semantic row"
        )
    if len({item.semantic_hash for item in snapshot}) != len(snapshot):
        raise SchedulerError("snapshot compiler duplicated semantic records")
    snapshot_hash = sha256_json({
        "compiler_id": snapshot_compiler.compiler_id,
        "checkpoint_semantic_hash": semantic_hash,
        "snapshot": [vars(item) for item in snapshot],
    })
    return checkpoint, snapshot, snapshot_hash


def _assert_goal_blind(calls: Sequence[Mapping[str, Any]], life: PublicLife) -> None:
    material = sha256_json(calls)  # also establishes deterministic serialization
    raw = str(calls)
    markers = (
        life.final_goal_id, life.final_goal, *life.final_goal_forbidden_markers,
    )
    for marker in markers:
        if marker and marker in raw:
            raise SchedulerError(f"final-goal marker leaked before reveal: {marker!r}")
    if not material:
        raise AssertionError("unreachable")


def _build_trace(
    *, life: PublicLife, arm: str, schedule: FrozenSchedule,
    decisions_by_round: Sequence[Sequence[SemanticDecision]],
    thinker_rounds: Sequence[tuple[ThinkerRequest, ThinkerResult]],
    guidance_rounds: Sequence[bool],
    compiler: DeterministicRealizationCompiler,
) -> dict[str, Any]:
    """Materialize one arm into the strict cyclic contract."""
    if len(decisions_by_round) != schedule.round_count \
            or len(thinker_rounds) != schedule.round_count:
        raise SchedulerError("trace materialization needs every round")
    scope_life = f"{life.logical_life_id}:{arm}"
    scope = {"world_id": life.world_id, "skin_id": life.skin_id, "life_id": scope_life}
    prefix = _scope_prefix(**scope)
    barrier_ids = {
        (round_index, phase): f"{prefix}-barrier-r{round_index}-{phase.casefold()}"
        for round_index in range(schedule.round_count) for phase in PHASES
    }

    def common(round_index: int, phase: str) -> dict[str, Any]:
        return {
            **scope, "round_index": round_index,
            "created_barrier_id": barrier_ids[(round_index, phase)],
        }

    experiences: list[dict[str, Any]] = []
    experience_by_identity: dict[str, dict[str, Any]] = {}
    for item in life.experiences:
        record = {
            **common(0, "EXPERIENCE"),
            "experience_id": f"{prefix}-exp-{item.sequence_index:04d}",
            "sequence_index": item.sequence_index,
            "action": item.action, "observation": item.observation,
            "outcome": item.outcome, "payload_hash": item.payload_hash,
        }
        experiences.append(record)
        experience_by_identity[item.payload_hash] = record

    concepts: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    derivations: list[dict[str, Any]] = []
    epistemic_events: list[dict[str, Any]] = []
    semantic_by_hash: dict[str, dict[str, Any]] = {}
    semantic_depth: dict[str, int] = {}
    status: dict[str, str] = {}
    semantic_sequence = 0
    derivation_sequence = 0
    event_sequence = 0

    def semantic_id(record: Mapping[str, Any]) -> str:
        return str(record.get("concept_id", record.get("edge_id")))

    def semantic_kind(record: Mapping[str, Any]) -> str:
        return "concept" if "concept_id" in record else "semantic_edge"

    def resolve_premises(items: Sequence[PremiseIdentity]) -> tuple[list[dict[str, str]], list[dict[str, str]], list[int]]:
        refs: list[dict[str, str]] = []
        identities: list[dict[str, str]] = []
        depths: list[int] = []
        for item in items:
            if item.kind == "experience":
                record = experience_by_identity.get(item.identity)
                if record is None:
                    raise SchedulerError("dream premise is not a local public experience")
                refs.append({"kind": "experience", "id": record["experience_id"]})
                identities.append({"kind": "experience", "identity": record["payload_hash"]})
            else:
                record = semantic_by_hash.get(item.identity)
                if record is None or semantic_kind(record) != item.kind:
                    raise SchedulerError("dream premise is not a local prior semantic")
                sid = semantic_id(record)
                refs.append({"kind": item.kind, "id": sid})
                identities.append({"kind": item.kind, "identity": record["semantic_hash"]})
                depths.append(semantic_depth[sid])
        return refs, identities, depths

    for round_index, round_decisions in enumerate(decisions_by_round):
        step_index = 0
        for decision in round_decisions:
            decision.validate()
            if decision.kind == "PASS":
                continue
            premise_refs, premise_identities, parent_depths = resolve_premises(decision.premises)
            conclusion_hash = decision.conclusion_semantic_hash
            if conclusion_hash is None:
                raise SchedulerError("semantic mutation has no conclusion identity")
            existing = semantic_by_hash.get(conclusion_hash)
            is_reinforcement = decision.kind == "REINFORCE"
            if is_reinforcement:
                if existing is None:
                    raise SchedulerError("reinforcement conclusion does not exist")
                conclusion = existing
            else:
                if existing is not None:
                    raise SchedulerError("duplicate semantic creation in trace")
                creates_edge = decision.kind == "CREATE_EDGE" or (
                    decision.kind == "SUPERSEDE" and decision.source_semantic_hash is not None
                )
                if creates_edge:
                    source = semantic_by_hash.get(str(decision.source_semantic_hash))
                    target = semantic_by_hash.get(str(decision.target_semantic_hash))
                    if source is None or target is None or semantic_kind(source) != "concept" \
                            or semantic_kind(target) != "concept":
                        raise SchedulerError("edge endpoints must be prior local concepts")
                    conclusion = {
                        **common(round_index, "DREAM"),
                        "edge_id": f"{prefix}-edge-{semantic_sequence:05d}",
                        "step_index": step_index,
                        "source_concept_id": semantic_id(source),
                        "relation": decision.relation,
                        "target_concept_id": semantic_id(target),
                        "semantic_hash": conclusion_hash,
                        "derivation_id": f"{prefix}-der-{derivation_sequence:05d}",
                        "initial_status": "provisional",
                    }
                    edges.append(conclusion)
                else:
                    conclusion = {
                        **common(round_index, "DREAM"),
                        "concept_id": f"{prefix}-concept-{semantic_sequence:05d}",
                        "step_index": step_index,
                        "canonical_key": decision.canonical_key,
                        "display_label": decision.display_label,
                        "semantic_hash": conclusion_hash,
                        "derivation_id": f"{prefix}-der-{derivation_sequence:05d}",
                        "initial_status": "provisional",
                    }
                    concepts.append(conclusion)
                semantic_by_hash[conclusion_hash] = conclusion
                semantic_sequence += 1
            sid = semantic_id(conclusion)
            derivation_id = f"{prefix}-der-{derivation_sequence:05d}"
            declared_depth = 1 + max(parent_depths, default=0)
            derivation = {
                **common(round_index, "DREAM"),
                "derivation_id": derivation_id, "step_index": step_index,
                "rule": decision.rule, "conclusion_kind": semantic_kind(conclusion),
                "conclusion_id": sid, "premise_refs": premise_refs,
                "guidance_agenda_ids": (
                    [f"{prefix}-agenda-r{round_index - 1}"]
                    if round_index > 0 and guidance_rounds[round_index] else []
                ),
                "declared_depth": declared_depth,
                "derivation_hash": derivation_digest(
                    decision.rule, conclusion_hash, premise_identities,
                ),
            }
            if not is_reinforcement:
                # Creation record and its derivation must bind atomically.
                conclusion["derivation_id"] = derivation_id
                semantic_depth[sid] = declared_depth
                create = {
                    **common(round_index, "DREAM"),
                    "epistemic_event_id": f"{prefix}-event-{event_sequence:05d}",
                    "step_index": step_index, "event_kind": "CREATE",
                    "subject_kind": semantic_kind(conclusion), "subject_id": sid,
                    "previous_status": None, "new_status": "provisional",
                    "evidence_derivation_id": derivation_id,
                    "replacement_subject_id": None,
                }
                epistemic_events.append(create)
                event_sequence += 1
                status[sid] = "provisional"
                if decision.kind == "SUPERSEDE":
                    old = semantic_by_hash.get(str(decision.superseded_semantic_hash))
                    if old is None:
                        raise SchedulerError("superseded semantic is not local")
                    old_id = semantic_id(old)
                    supersede = {
                        **common(round_index, "DREAM"),
                        "epistemic_event_id": f"{prefix}-event-{event_sequence:05d}",
                        "step_index": step_index, "event_kind": "SUPERSEDE",
                        "subject_kind": semantic_kind(old), "subject_id": old_id,
                        "previous_status": status[old_id], "new_status": "superseded",
                        "evidence_derivation_id": derivation_id,
                        "replacement_subject_id": sid,
                    }
                    epistemic_events.append(supersede)
                    event_sequence += 1
                    status[old_id] = "superseded"
            if is_reinforcement or decision.mark_supported:
                support = {
                    **common(round_index, "DREAM"),
                    "epistemic_event_id": f"{prefix}-event-{event_sequence:05d}",
                    "step_index": step_index, "event_kind": "SUPPORT",
                    "subject_kind": semantic_kind(conclusion), "subject_id": sid,
                    "previous_status": status[sid], "new_status": "supported",
                    "evidence_derivation_id": derivation_id,
                    "replacement_subject_id": None,
                }
                epistemic_events.append(support)
                event_sequence += 1
                status[sid] = "supported"
            derivations.append(derivation)
            derivation_sequence += 1
            step_index += 1

    concepts_by_id = {item["concept_id"]: item for item in concepts}
    realization_specs: list[dict[str, Any]] = []
    touch_plans: list[dict[str, Any]] = []
    order_index = 0
    for semantic in [*concepts, *edges]:
        source_id = semantic_id(semantic)
        round_index = int(semantic["round_index"])
        for form, cue, target in compiler.render(semantic, concepts_by_id):
            realization_id = f"{prefix}-real-{order_index:05d}-{form}"
            realization = {
                **common(round_index, "REALIZE"),
                "realization_id": realization_id,
                "source_kind": semantic_kind(semantic), "source_id": source_id,
                "source_semantic_hash": semantic["semantic_hash"], "form": form,
                "cue_text": cue, "target_text": target,
                "realization_hash": realization_digest(
                    semantic["semantic_hash"], form, cue, target,
                ),
            }
            touches = compiler.touches(semantic, form)
            touch_id = f"{prefix}-touch-{order_index:05d}"
            touch = {
                **common(round_index, "REALIZE"),
                "touch_plan_id": touch_id, "realization_id": realization_id,
                "touches": touches, "weight": 1.0, "order_index": order_index,
                "plan_hash": touch_plan_digest(realization_id, touches, 1.0, order_index),
            }
            realization_specs.append(realization)
            touch_plans.append(touch)
            order_index += 1

    cue_targets: dict[str, str] = {}
    exact_rows: set[tuple[str, str, str]] = set()
    for realization in realization_specs:
        cue = " ".join(str(realization["cue_text"]).split()).casefold()
        target = " ".join(str(realization["target_text"]).split())
        prior = cue_targets.setdefault(cue, target)
        if prior != target:
            raise SchedulerError("realization corpus has one cue with conflicting targets")
        row = (str(realization["form"]), cue, target)
        if row in exact_rows:
            raise SchedulerError("realization corpus contains an exact duplicate row")
        exact_rows.add(row)

    # Reconstruct append-only status at each checkpoint.
    status_by_round: list[dict[str, str]] = []
    running: dict[str, str] = {}
    for round_index in range(schedule.round_count):
        round_events = [item for item in epistemic_events if item["round_index"] == round_index]
        round_events.sort(key=lambda item: (item["step_index"], item["epistemic_event_id"]))
        # CREATE must precede SUPPORT at an identical step; event ids preserve insertion order.
        for event in round_events:
            running[event["subject_id"]] = event["new_status"]
        status_by_round.append(dict(running))

    checkpoints: list[dict[str, Any]] = []
    previous_checkpoint: str | None = None
    semantics_by_id = {semantic_id(item): item for item in [*concepts, *edges]}
    for round_index in range(schedule.round_count):
        included = sorted(
            item_id for item_id, item_status in status_by_round[round_index].items()
            if item_status in {"provisional", "supported"}
        )
        available_realizations = sorted(
            (item for item in realization_specs if item["round_index"] <= round_index),
            key=lambda item: item["realization_id"],
        )
        available_plans = sorted(
            (item for item in touch_plans if item["round_index"] <= round_index),
            key=lambda item: item["touch_plan_id"],
        )
        semantic_payload = [
            {
                "id": item_id,
                "semantic_hash": semantics_by_id[item_id]["semantic_hash"],
                "status": status_by_round[round_index][item_id],
                "derivation_depth": semantic_depth[item_id],
            }
            for item_id in included
        ]
        checkpoint_id = f"{prefix}-checkpoint-r{round_index}"
        semantic_hash = semantic_state_digest(semantic_payload)
        realization_hash = realization_state_digest(available_realizations, available_plans)
        checkpoint = {
            **common(round_index, "CHECKPOINT"),
            "checkpoint_id": checkpoint_id,
            "memory_adapter_id": f"{prefix}-text-memory",
            "previous_checkpoint_id": previous_checkpoint,
            "included_semantic_ids": included,
            "realization_ids": [item["realization_id"] for item in available_realizations],
            "touch_plan_ids": [item["touch_plan_id"] for item in available_plans],
            "semantic_state_hash": semantic_hash,
            "realization_state_hash": realization_hash,
            "adapter_artifact_hash": sha256_json({
                "kind": "deterministic-gold-text-checkpoint",
                "semantic_state_hash": semantic_hash,
                "realization_state_hash": realization_hash,
            }),
        }
        checkpoints.append(checkpoint)
        previous_checkpoint = checkpoint_id

    thinker_states: list[dict[str, Any]] = []
    thinker_hypotheses: list[dict[str, Any]] = []
    thinker_confusions: list[dict[str, Any]] = []
    thinker_desires: list[dict[str, Any]] = []
    agendas: list[dict[str, Any]] = []
    hash_to_id = {
        record["semantic_hash"]: semantic_id(record) for record in [*concepts, *edges]
    }
    for round_index, (request, result) in enumerate(thinker_rounds):
        checkpoint = checkpoints[round_index]
        retrieved = [hash_to_id[item] for item in result.retrieved_semantic_hashes]
        cited = [hash_to_id[item] for item in result.cited_semantic_hashes]
        included = set(checkpoint["included_semantic_ids"])
        query_registry: list[dict[str, str]] = []
        if request.agenda_vocabulary is not None:
            for template in request.agenda_vocabulary.templates:
                subject_id = hash_to_id.get(concept_semantic_hash(template.left_id))
                if subject_id is None or subject_id not in included:
                    continue
                query_registry.append({
                    "query_key": template.query_key,
                    "subject_entity_id": subject_id,
                    "relation_id": template.relation_id,
                })
        query_registry.sort(key=lambda item: item["query_key"])
        state_id = f"{prefix}-think-r{round_index}-s0"
        state = {
            **common(round_index, "THINK"),
            "thinker_state_id": state_id, "step_index": 0,
            "checkpoint_id": checkpoint["checkpoint_id"],
            # Every round starts from a fresh goal-conditioned workspace.
            "parent_state_id": None, "goal": request.goal,
            "retrieved_semantic_ids": retrieved, "workspace": list(result.workspace),
            "query_registry": query_registry,
            "state_hash": thinker_state_digest(
                checkpoint["checkpoint_id"], None, request.goal, retrieved,
                list(result.workspace), query_registry,
            ),
        }
        release_support = [
            item_id for item_id in cited
            if item_id.startswith(f"{prefix}-edge-")
        ] if result.disposition == "released" else []
        hypothesis_id = f"{prefix}-hyp-r{round_index}-h0"
        hypothesis = {
            **common(round_index, "THINK"),
            "hypothesis_id": hypothesis_id, "step_index": 1,
            "thinker_state_id": state_id, "parent_hypothesis_ids": [],
            "claim": result.claim, "cited_semantic_ids": cited,
            "release_support_semantic_ids": release_support,
            "confidence": result.confidence, "disposition": result.disposition,
            "hypothesis_hash": hypothesis_digest(
                state_id, result.claim, cited, result.confidence,
                result.disposition, (), release_support,
            ),
        }
        thinker_states.append(state)
        thinker_hypotheses.append(hypothesis)
        agenda_confusion_ids: list[str] = []
        if result.agenda_queries:
            query = result.agenda_queries[0]
            subject_id = hash_to_id.get(concept_semantic_hash(query.left_id))
            if subject_id is None:
                raise SchedulerError("agenda query subject is absent from cyclic checkpoint")
            confusion_id = f"{prefix}-conf-r{round_index}-agenda0"
            confusion = {
                **common(round_index, "THINK"),
                "confusion_id": confusion_id, "step_index": 2,
                "thinker_state_id": state_id,
                "query_key": query.query_key,
                "subject_entity_id": subject_id,
                "relation_id": query.relation_id,
                "unknown_slot": "object",
            }
            thinker_confusions.append(confusion)
            agenda_confusion_ids.append(confusion_id)
        desire_ids: list[str] = []
        priority_query_keys: list[str] = []
        for query_index, query in enumerate(result.agenda_queries):
            if query_index >= len(agenda_confusion_ids):
                raise SchedulerError("agenda desire lacks a mechanically typed confusion")
            desire_id = f"{prefix}-desire-r{round_index}-{query_index}"
            confusion = thinker_confusions[-1]
            thinker_desires.append({
                **common(round_index, "FEEDBACK"),
                "desire_id": desire_id,
                "source_confusion_id": agenda_confusion_ids[query_index],
                "query_key": confusion["query_key"],
                "subject_entity_id": confusion["subject_entity_id"],
                "relation_id": confusion["relation_id"],
                "unknown_slot": confusion["unknown_slot"],
                "checkpoint_id": checkpoint["checkpoint_id"],
                "checkpoint_semantic_state_hash": checkpoint["semantic_state_hash"],
                "thinker_state_hash": state["state_hash"],
                "priority": query_index + 1,
                "non_evidentiary": True,
            })
            desire_ids.append(desire_id)
            priority_query_keys.append(query.query_key)
        agenda = {
            **common(round_index, "FEEDBACK"),
            "agenda_id": f"{prefix}-agenda-r{round_index}",
            "checkpoint_id": checkpoint["checkpoint_id"],
            "checkpoint_semantic_state_hash": checkpoint["semantic_state_hash"],
            "thinker_state_hash": state["state_hash"],
            "desire_ids": desire_ids,
            "priority_query_keys": priority_query_keys,
            "non_evidentiary": True,
        }
        agenda["agenda_hash"] = agenda_digest(
            checkpoint["checkpoint_id"], checkpoint["semantic_state_hash"],
            state["state_hash"], desire_ids, priority_query_keys,
        )
        agendas.append(agenda)

    trace = {
        "schema_version": CYCLIC_SCHEMA_VERSION,
        "trace_id": f"{prefix}-trace", **scope, "split": life.split,
        "round_count": schedule.round_count,
        "memory_adapter_id": f"{prefix}-text-memory",
        "experiences": experiences, "concepts": concepts,
        "semantic_edges": edges, "derivations": derivations,
        "epistemic_events": epistemic_events,
        "realization_specs": realization_specs, "touch_plans": touch_plans,
        "checkpoints": checkpoints, "thinker_states": thinker_states,
        "thinker_hypotheses": thinker_hypotheses,
        "thinker_confusions": thinker_confusions,
        "thinker_desires": thinker_desires, "agendas": agendas,
        "phase_barriers": [],
    }

    refs: dict[str, list[dict[str, str]]] = {}
    record_specs = {
        "experiences": ("experience", "experience_id"),
        "concepts": ("concept", "concept_id"),
        "semantic_edges": ("semantic_edge", "edge_id"),
        "derivations": ("derivation", "derivation_id"),
        "epistemic_events": ("epistemic_event", "epistemic_event_id"),
        "realization_specs": ("realization_spec", "realization_id"),
        "touch_plans": ("touch_plan", "touch_plan_id"),
        "checkpoints": ("checkpoint", "checkpoint_id"),
        "thinker_states": ("thinker_state", "thinker_state_id"),
        "thinker_hypotheses": ("thinker_hypothesis", "hypothesis_id"),
        "thinker_confusions": ("thinker_confusion", "confusion_id"),
        "thinker_desires": ("thinker_desire", "desire_id"),
        "agendas": ("agenda", "agenda_id"),
    }
    for top_key, (kind, id_key) in record_specs.items():
        for record in trace[top_key]:
            refs.setdefault(record["created_barrier_id"], []).append({
                "kind": kind, "id": record[id_key], "record_hash": sha256_json(record),
            })
    for items in refs.values():
        items.sort(key=lambda item: (item["kind"], item["id"]))
    previous_hash: str | None = None
    for barrier_index in range(schedule.round_count * len(PHASES)):
        round_index, phase_offset = divmod(barrier_index, len(PHASES))
        phase = PHASES[phase_offset]
        barrier_id = barrier_ids[(round_index, phase)]
        record_refs = refs.get(barrier_id, [])
        barrier_hash = phase_barrier_digest(
            scope, barrier_index, round_index, phase, previous_hash, record_refs,
        )
        trace["phase_barriers"].append({
            **scope, "barrier_id": barrier_id, "barrier_index": barrier_index,
            "round_index": round_index, "phase": phase,
            "previous_barrier_hash": previous_hash,
            "record_refs": record_refs, "barrier_hash": barrier_hash,
        })
        previous_hash = barrier_hash
    assert_typed_feedback_sources(trace)
    assert_valid_trace(trace)
    return trace


def assert_typed_feedback_sources(trace: Mapping[str, Any]) -> None:
    """Scheduler-level hardening beyond the general cyclic base contract."""
    confusions = {
        item.get("confusion_id") for item in trace.get("thinker_confusions", [])
        if isinstance(item, Mapping)
    }
    for desire in trace.get("thinker_desires", []):
        if not isinstance(desire, Mapping):
            raise SchedulerError("thinker desire must be an object")
        source = desire.get("source_confusion_id")
        if not isinstance(source, str) or source not in confusions:
            raise SchedulerError(
                "dream agenda desires may source typed confusions only, never hypotheses"
            )


def _normalized_prefix_digest(
    life: PublicLife, initial_calls: Sequence[Mapping[str, Any]],
    thinker_payload: Mapping[str, Any],
) -> str:
    return sha256_json({
        "experience_payload_hashes": [item.payload_hash for item in life.experiences],
        "initial_calls": list(initial_calls),
        "thinker_0": thinker_payload,
    })


def _agenda_signature(queries: Sequence[AgendaQuery]) -> tuple[str, ...]:
    return tuple(item.kind for item in queries)


def _rebind_selection_queries(
    queries: Sequence[AgendaQuery], recipient_request: ThinkerRequest,
) -> tuple[AgendaQuery, ...]:
    """Project foreign *selection keys* through the recipient registry.

    Shuffled feedback is a negative control over agenda selection, not a
    license to carry a donor checkpoint/goal binding into another life.  Only
    the opaque query key and kind cross the control boundary.  The full typed
    tuple is reconstructed from the recipient's frozen vocabulary and bound
    to its checkpoint.  Missing or ambiguous recipient templates fail closed.
    """
    if not queries:
        return ()
    vocabulary = recipient_request.agenda_vocabulary
    if vocabulary is None:
        raise SchedulerError("foreign selection has no recipient agenda vocabulary")
    vocabulary.validate()
    rebound: list[AgendaQuery] = []
    for query in queries:
        matches = [
            template for template in vocabulary.templates
            if template.query_key == query.query_key and template.kind == query.kind
        ]
        if len(matches) != 1:
            raise SchedulerError(
                "foreign selection key has no unique recipient registry binding"
            )
        template = matches[0]
        rebound.append(AgendaQuery(
            query_key=template.query_key,
            kind=template.kind,
            left_id=template.left_id,
            relation_id=template.relation_id,
            right_id=template.right_id,
            source_checkpoint_hash=recipient_request.checkpoint_hash,
            source_goal_id=recipient_request.goal_id,
            vocabulary_hash=vocabulary.vocabulary_hash,
        ))
    return tuple(rebound)


def _matched_distractor_queries(
    own_queries: Sequence[AgendaQuery], recipient_request: ThinkerRequest,
) -> tuple[AgendaQuery, ...]:
    """Select a precommitted recipient-local wrong query of matched type.

    A foreign agenda whose opaque key rebinds to the recipient's own canonical
    query is not a negative control.  V1 therefore uses a public-only matched
    distractor declared in the same frozen vocabulary.  Count, kind, relation,
    checkpoint, goal, and call budget match; the canonical endpoint tuple must
    differ and the distractor relation must initially be absent.
    """
    if not own_queries:
        return ()
    vocabulary = recipient_request.agenda_vocabulary
    if vocabulary is None:
        raise SchedulerError("matched distractor has no recipient agenda vocabulary")
    current_edges = {
        (item.source_entity_id, item.relation_id, item.target_entity_id)
        for item in recipient_request.memory if item.kind == "semantic_edge"
    }
    selected: list[AgendaQuery] = []
    used_keys: set[str] = set()
    for own in own_queries:
        candidates = sorted(
            (
                template for template in vocabulary.templates
                if template.kind == own.kind
                and template.relation_id == own.relation_id
                and template.query_key != own.query_key
                and (template.left_id, template.relation_id, template.right_id)
                    != (own.left_id, own.relation_id, own.right_id)
                and (template.left_id, template.relation_id, template.right_id)
                    not in current_edges
                and template.query_key not in used_keys
            ),
            key=lambda template: template.query_key,
        )
        if not candidates:
            raise SchedulerError(
                "matched distractor needs a distinct absent recipient query"
            )
        template = candidates[0]
        used_keys.add(template.query_key)
        selected.append(AgendaQuery(
            query_key=template.query_key, kind=template.kind,
            left_id=template.left_id, relation_id=template.relation_id,
            right_id=template.right_id,
            source_checkpoint_hash=recipient_request.checkpoint_hash,
            source_goal_id=recipient_request.goal_id,
            vocabulary_hash=vocabulary.vocabulary_hash,
        ))
    return tuple(selected)


def _periodic_reactivation_positions(wake_calls: int, reactivation_calls: int) -> tuple[int, ...]:
    """Evenly place reactivations *after* wake indices, never as a tail batch."""
    return tuple(
        max(0, min(wake_calls - 1, ((index + 1) * wake_calls) //
                   (reactivation_calls + 1) - 1))
        for index in range(reactivation_calls)
    )


def run_recurrent_text_experiment(
    *, lives: Sequence[PublicLife], dreamer: SemanticDreamerProtocol,
    thinker: ThinkerProtocol | ScientificThinkerMachineProtocol,
    schedule: FrozenSchedule = FrozenSchedule(),
    compiler: DeterministicRealizationCompiler | None = None,
    snapshot_compiler: CheckpointToThinkerSnapshotCompilerProtocol | None = None,
    agenda_compiler: AgendaVocabularyCompilerProtocol | None = None,
    scientific_mode: bool = False,
) -> dict[str, Any]:
    """Run deterministic protocol calls and return CPU-only arm artifacts.

    Initial dream decisions and ``THINK_0`` are computed once per logical life
    and cloned across arms.  Subsequent rounds are condition-specific.  The
    matched-distractor arm receives a distinct recipient-local query of the
    same registered kind and budget, never foreign memory or evidence.
    """
    schedule.validate()
    compiler = compiler or DeterministicRealizationCompiler()
    snapshot_compiler = snapshot_compiler or DeterministicTextSnapshotCompiler()
    if not lives:
        raise SchedulerError("at least one public life is required")
    by_id = {life.logical_life_id: life for life in lives}
    if len(by_id) != len(lives):
        raise SchedulerError("logical life ids must be unique")
    for life in lives:
        life.validate()
        actual = len(life.experiences)
        if actual != schedule.expected_wake_calls:
            raise SchedulerError(
                f"declared WAKE budget {schedule.expected_wake_calls} does not match "
                f"actual frozen public episode count {actual} for {life.logical_life_id}"
            )
    prefixes: dict[str, dict[str, Any]] = {}
    for life in lives:
        state = _LogicalState(decisions_by_round=[[] for _ in range(schedule.round_count)])
        call_index = 0
        calls: list[dict[str, Any]] = []
        decisions: list[SemanticDecision] = []
        reactivation_positions = _periodic_reactivation_positions(
            schedule.expected_wake_calls, schedule.reactivation_calls,
        )
        reactivations_after = Counter(reactivation_positions)
        reactivation_index = 0
        for wake_index in range(schedule.expected_wake_calls):
            requests = _schedule_calls(
                life, schedule, round_index=0, stage="WAKE", count=1,
                state=state, start_call_index=call_index,
                trigger_offset=wake_index,
            )
            stage_decisions, stage_calls = _run_calls(dreamer, requests, state)
            decisions.extend(stage_decisions)
            calls.extend(stage_calls)
            call_index += 1
            for _ in range(reactivations_after[wake_index]):
                requests = _schedule_calls(
                    life, schedule, round_index=0, stage="REACTIVATE", count=1,
                    state=state, start_call_index=call_index,
                    trigger_offset=reactivation_index,
                )
                stage_decisions, stage_calls = _run_calls(dreamer, requests, state)
                decisions.extend(stage_decisions)
                calls.extend(stage_calls)
                call_index += 1
                reactivation_index += 1
        if reactivation_index != schedule.reactivation_calls:
            raise SchedulerError("periodic reactivation scheduler lost a call")
        requests = _schedule_calls(
            life, schedule, round_index=0, stage="TARGET_BLIND_SLEEP",
            count=schedule.target_blind_sleep_calls, state=state,
            start_call_index=call_index,
        )
        stage_decisions, stage_calls = _run_calls(dreamer, requests, state)
        decisions.extend(stage_decisions)
        calls.extend(stage_calls)
        call_index += schedule.target_blind_sleep_calls
        state.decisions_by_round[0] = list(decisions)
        logical_checkpoint, memory, snapshot_hash = _freeze_checkpoint_view(
            life, state, 0, snapshot_compiler,
        )
        agenda_vocabulary = life.agenda_vocabulary(life.intermediate_goal_id)
        if agenda_vocabulary is None and agenda_compiler is not None:
            agenda_vocabulary = agenda_compiler.compile(
                life, logical_checkpoint, life.intermediate_goal_id,
            )
        think_request = ThinkerRequest(
            logical_life_id=life.visible_life_id,
            world_id=life.world_id, skin_id=life.skin_id,
            life_id=life.visible_life_id, round_index=0,
            checkpoint_id=logical_checkpoint.checkpoint_id,
            checkpoint_hash=logical_checkpoint.checkpoint_hash,
            checkpoint_semantic_hash=logical_checkpoint.semantic_state_hash,
            snapshot_compiler_id=snapshot_compiler.compiler_id,
            snapshot_hash=snapshot_hash,
            goal_id=life.intermediate_goal_id, goal=life.intermediate_goal,
            memory=memory, operation_budget=schedule.initial_thinker_budget,
            agenda_vocabulary=agenda_vocabulary,
            arm_id="shared_prefix",
            reset_id=sha256_json({
                "life_id": life.visible_life_id, "arm_id": "shared_prefix",
                "round_index": 0, "checkpoint_hash": logical_checkpoint.checkpoint_hash,
            }),
        )
        think_result, think_execution = _execute_thinker(
            thinker, think_request, scientific_mode=scientific_mode,
            trusted_goal_compiler=agenda_compiler,
        )
        think_payload = _thinker_payload(think_request, think_result, think_execution)
        _assert_goal_blind(calls, life)
        prefixes[life.logical_life_id] = {
            "state": state, "calls": calls,
            "think_request": think_request, "think_result": think_result,
            "think_execution": think_execution,
            "think_payload": think_payload,
            "prefix_digest": _normalized_prefix_digest(life, calls, think_payload),
        }

    artifacts: list[dict[str, Any]] = []
    traces: list[dict[str, Any]] = []
    for arm in ARM_NAMES:
        contexts: dict[str, dict[str, Any]] = {}
        for life in lives:
            base = prefixes[life.logical_life_id]
            state: _LogicalState = base["state"].clone()
            contexts[life.logical_life_id] = {
                "life": life,
                "base": base,
                "state": state,
                "calls": list(base["calls"]),
                "decisions_by_round": [list(items) for items in state.decisions_by_round],
                "thinker_rounds": [(base["think_request"], base["think_result"])],
                "scientific_executions": [base["think_execution"]],
                "guidance_rounds": [False for _ in range(schedule.round_count)],
                "prior_result": base["think_result"],
                "call_index": len(base["calls"]),
                "selection_records": [],
            }

        # Run each return edge in lockstep across lives, preserving matched
        # budgets while supporting arbitrary repeated cycles.
        for round_index, return_spec in enumerate(schedule.return_rounds, start=1):
            selections: dict[str, tuple[tuple[AgendaQuery, ...], str | None, str]] = {}
            for life in lives:
                context = contexts[life.logical_life_id]
                prior_result: ThinkerResult = context["prior_result"]
                if arm == "no_feedback":
                    selected: tuple[AgendaQuery, ...] = ()
                    donor_id = None
                    selection_mode = "intrinsic"
                elif arm == "agenda_feedback":
                    selected = prior_result.agenda_queries
                    donor_id = life.logical_life_id
                    selection_mode = "own_agenda"
                    context["guidance_rounds"][round_index] = True
                else:
                    donor_id = None
                    recipient_request: ThinkerRequest = context["thinker_rounds"][-1][0]
                    selected = _matched_distractor_queries(
                        prior_result.agenda_queries, recipient_request,
                    )
                    selection_mode = "matched_distractor"
                    if (
                        len(selected) != len(prior_result.agenda_queries)
                        or _agenda_signature(selected) != _agenda_signature(
                            prior_result.agenda_queries
                        )
                    ):
                        raise SchedulerError(
                            "matched distractor must preserve agenda size and typed signature"
                        )
                selections[life.logical_life_id] = (selected, donor_id, selection_mode)

            for life in lives:
                context = contexts[life.logical_life_id]
                selected, donor_id, selection_mode = selections[life.logical_life_id]
                context["selection_records"].append({
                    "round_index": round_index,
                    "mode": selection_mode,
                    "recipient_logical_life_id": life.logical_life_id,
                    "donor_logical_life_id": donor_id,
                    "queries": [vars(item) for item in selected],
                    "non_evidentiary": True,
                })
                requests = _schedule_calls(
                    life, schedule, round_index=round_index,
                    stage="RETURN_SLEEP", count=return_spec.dream_calls,
                    state=context["state"], selection_queries=selected,
                    selection_mode=selection_mode, donor_life_id=donor_id,
                    start_call_index=context["call_index"],
                )
                round_decisions, round_calls = _run_calls(
                    dreamer, requests, context["state"]
                )
                context["decisions_by_round"][round_index] = round_decisions
                context["calls"].extend(round_calls)
                context["call_index"] += return_spec.dream_calls
                logical_checkpoint, memory, snapshot_hash = _freeze_checkpoint_view(
                    life, context["state"], round_index, snapshot_compiler,
                )
                if return_spec.reveal_final_goal:
                    goal_id, goal = life.final_goal_id, life.final_goal
                else:
                    goal_id, goal = life.intermediate_goal_id, life.intermediate_goal
                agenda_vocabulary = life.agenda_vocabulary(goal_id)
                if agenda_vocabulary is None and agenda_compiler is not None:
                    agenda_vocabulary = agenda_compiler.compile(
                        life, logical_checkpoint, goal_id,
                    )
                # No prior thinker state, workspace, hypothesis, answer, or
                # operation is passed here.  MEMORY_k is the sole bridge.
                request = ThinkerRequest(
                    logical_life_id=life.visible_life_id,
                    world_id=life.world_id, skin_id=life.skin_id,
                    life_id=life.visible_life_id,
                    round_index=round_index,
                    checkpoint_id=logical_checkpoint.checkpoint_id,
                    checkpoint_hash=logical_checkpoint.checkpoint_hash,
                    checkpoint_semantic_hash=logical_checkpoint.semantic_state_hash,
                    snapshot_compiler_id=snapshot_compiler.compiler_id,
                    snapshot_hash=snapshot_hash,
                    goal_id=goal_id, goal=goal, memory=memory,
                    operation_budget=return_spec.thinker_budget,
                    agenda_vocabulary=agenda_vocabulary,
                    arm_id=arm,
                    reset_id=sha256_json({
                        "life_id": life.visible_life_id, "arm_id": arm,
                        "round_index": round_index,
                        "checkpoint_hash": logical_checkpoint.checkpoint_hash,
                    }),
                )
                result, execution = _execute_thinker(
                    thinker, request, scientific_mode=scientific_mode,
                    trusted_goal_compiler=agenda_compiler,
                )
                context["thinker_rounds"].append((request, result))
                context["scientific_executions"].append(execution)
                context["prior_result"] = result

        for life in lives:
            context = contexts[life.logical_life_id]
            base = context["base"]
            calls = context["calls"]
            _assert_goal_blind(calls, life)
            trace = _build_trace(
                life=life, arm=arm, schedule=schedule,
                decisions_by_round=context["decisions_by_round"],
                thinker_rounds=context["thinker_rounds"],
                guidance_rounds=context["guidance_rounds"], compiler=compiler,
            )
            call_counts = Counter(record["request"]["stage"] for record in calls)
            expected_counts = {
                "WAKE": schedule.expected_wake_calls,
                "REACTIVATE": schedule.reactivation_calls,
                "TARGET_BLIND_SLEEP": schedule.target_blind_sleep_calls,
                "RETURN_SLEEP": sum(item.dream_calls for item in schedule.return_rounds),
            }
            if dict(call_counts) != expected_counts:
                raise SchedulerError("dream call ledger does not match frozen budget")
            final_request, final_result = context["thinker_rounds"][-1]
            final_think_payload = _thinker_payload(
                final_request, final_result, context["scientific_executions"][-1],
            )
            artifact = {
                "schema_version": SCHEMA_VERSION,
                "artifact_id": f"{trace['trace_id']}:{arm}",
                "arm": arm, "logical_life_id": life.logical_life_id,
                "world_id": life.world_id, "skin_id": life.skin_id,
                "split": life.split,
                "schedule": {
                    "expected_wake_calls": schedule.expected_wake_calls,
                    "actual_wake_calls": len(life.experiences),
                    "reactivation_calls": schedule.reactivation_calls,
                    "target_blind_sleep_calls": schedule.target_blind_sleep_calls,
                    "dream_semantic_neighbor_k": schedule.dream_semantic_neighbor_k,
                    "full_memory_ceiling": schedule.full_memory_ceiling,
                    "reactivation_after_wake_indices": list(
                        _periodic_reactivation_positions(
                            schedule.expected_wake_calls,
                            schedule.reactivation_calls,
                        )
                    ),
                    "return_rounds": [vars(item) for item in schedule.return_rounds],
                    "total_dream_calls": schedule.dream_calls_per_arm,
                },
                "prefix_digest": base["prefix_digest"],
                "scientific_mode": scientific_mode,
                "controller_condition": (
                    context["scientific_executions"][-1].condition_label
                    if scientific_mode else (
                        "scripted-gold-thinker/read-plan+full-memory ceiling"
                        if schedule.full_memory_ceiling else
                        "scripted-gold-thinker/read-plan ceiling"
                    )
                ),
                "goal_evaluation": {
                    "requested_goal_id": final_request.goal_id,
                    "objective_binding": (
                        context["scientific_executions"][-1].objective_binding
                        if scientific_mode else "scripted_read_plan_ceiling"
                    ),
                    "final_goal_answer_scored": bool(
                        scientific_mode
                        and context["scientific_executions"][-1].objective_binding
                            == "exact_request_goal"
                    ),
                },
                "dream_calls": calls,
                "intermediate_think": base["think_payload"],
                "selection_records": context["selection_records"],
                "final_reveal": {
                    "goal_id": life.final_goal_id, "goal": life.final_goal,
                    "revealed_after_checkpoint_id": trace["checkpoints"][-1]["checkpoint_id"],
                },
                "final_think": final_think_payload,
                "trace": trace,
            }
            artifact["checkpoint_snapshot_bindings"] = [
                {
                    "round_index": round_index,
                    "cyclic_checkpoint_id": trace["checkpoints"][round_index]["checkpoint_id"],
                    "cyclic_semantic_state_hash": trace["checkpoints"][round_index][
                        "semantic_state_hash"
                    ],
                    "logical_checkpoint_id": request.checkpoint_id,
                    "logical_checkpoint_hash": request.checkpoint_hash,
                    "logical_semantic_content_hash": request.checkpoint_semantic_hash,
                    "snapshot_compiler_id": request.snapshot_compiler_id,
                    "snapshot_hash": request.snapshot_hash,
                }
                for round_index, (request, _) in enumerate(context["thinker_rounds"])
            ]
            artifact["round_deltas"] = [
                {
                    "round_index": round_index,
                    "dream_call_hashes": [
                        call["call_hash"] for call in calls
                        if call["request"]["round_index"] == round_index
                    ],
                    "created_semantic_hashes": sorted(
                        item["semantic_hash"]
                        for item in [*trace["concepts"], *trace["semantic_edges"]]
                        if item["round_index"] == round_index
                    ),
                    "derivation_hashes": sorted(
                        item["derivation_hash"] for item in trace["derivations"]
                        if item["round_index"] == round_index
                    ),
                    "realization_hashes": sorted(
                        item["realization_hash"] for item in trace["realization_specs"]
                        if item["round_index"] == round_index
                    ),
                    "touches_added": sum(
                        item["touches"] for item in trace["touch_plans"]
                        if item["round_index"] == round_index
                    ),
                    "checkpoint_id": trace["checkpoints"][round_index]["checkpoint_id"],
                    "checkpoint_semantic_state_hash": trace["checkpoints"][round_index][
                        "semantic_state_hash"
                    ],
                    "thinker_state_hashes": sorted(
                        item["state_hash"] for item in trace["thinker_states"]
                        if item["round_index"] == round_index
                    ),
                    "agenda_hash": trace["agendas"][round_index]["agenda_hash"],
                }
                for round_index in range(schedule.round_count)
            ]
            artifact["artifact_hash"] = sha256_json(artifact)
            artifacts.append(artifact)
            traces.append(trace)

    # Trace IDs/adapters/records are scope-unique across every experimental arm.
    assert_valid_dataset({
        "schema_version": CYCLIC_SCHEMA_VERSION,
        "dataset_id": "recurrent-text-organism-dry-run",
        "traces": traces,
    })
    result = {
        "schema_version": SCHEMA_VERSION,
        "experiment_id": "recurrent-text-organism-dry-run",
        "control_arm": "matched_distractor",
        "artifacts": artifacts,
    }
    result["experiment_hash"] = sha256_json(result)
    return result


def public_life_from_v03r(world: Any, skin_name: str = "aligned") -> PublicLife:
    """Adapt a v0.3-R public export without importing any answer or hidden state."""
    exported = world.precheckpoint_export(skin_name)
    episodes = tuple(
        PublicExperience(
            public_id=str(item["id"]), sequence_index=index,
            action=str(item["phase"]),
            observation=json.dumps({
                "text": item["text"], "public_record": item["public_record"],
            }, sort_keys=True, separators=(",", ":")),
            outcome=str(item["kind"]),
        )
        for index, item in enumerate(exported["episodes"])
    )
    probe = exported["operational_probe"]
    final = world.reveal_final_goal(skin_name)
    # Pair grouping may use a private scorer-side tuple, but only its one-way
    # opaque digest enters model-visible scope.  Neither seed nor latent bit is
    # serialized anywhere in the organism artifact.
    pair_alias = sha256_json({"private_pair_token": str(world.latent_tuple_id)})[:20]
    visible_world_alias = sha256_json({
        "public_probe": exported["operational_probe"],
        "split": str(world.split), "skin": skin_name,
    })[:20]
    visible_life_alias = sha256_json({
        "public_probe": exported["operational_probe"], "skin": skin_name,
    })[:20]
    # The twin discriminator is used only to allocate distinct scorer-side
    # records.  The model-visible alias is a pure function of the identical
    # public precheckpoint and is therefore invariant across latent twins.
    private_life_alias = sha256_json({
        "pair_alias": pair_alias, "private_member_token": str(world.latent_bit),
    })[:20]
    return PublicLife(
        logical_life_id=f"scorer-life-{private_life_alias}",
        world_id=f"world-{visible_world_alias}", skin_id=skin_name,
        split=str(world.split), experiences=episodes,
        intermediate_goal_id=str(probe["probe_id"]),
        intermediate_goal=str(probe["question"]),
        final_goal_id=str(final["goal_id"]), final_goal=str(final["question"]),
        final_goal_forbidden_markers=(str(final["goal_id"]), str(final["question"])),
        model_visible_life_id=f"life-{visible_life_alias}",
    )


def run_v03r_recurrent_dry_run(
    *, worlds: Sequence[Any], dreamer: SemanticDreamerProtocol,
    thinker: ThinkerProtocol | ScientificThinkerMachineProtocol,
    skin_name: str = "aligned",
    schedule: FrozenSchedule = FrozenSchedule(),
    compiler: DeterministicRealizationCompiler | None = None,
    snapshot_compiler: CheckpointToThinkerSnapshotCompilerProtocol | None = None,
    agenda_compiler: AgendaVocabularyCompilerProtocol | None = None,
    scientific_mode: bool = False,
) -> dict[str, Any]:
    """Public-only v0.3-R adapter for the CPU protocol dry run.

    Callers should normally provide both collision twins in one split/skin.
    The generic scheduler enforces the declared WAKE count and uses a distinct
    precommitted recipient-local matched-distractor query.  Scientific mode is
    still only a recurrence-probe ceiling until the explicit GPU-preflight
    blockers reported below are closed.
    """
    lives = tuple(public_life_from_v03r(world, skin_name) for world in worlds)
    result = run_recurrent_text_experiment(
        lives=lives, dreamer=dreamer, thinker=thinker, schedule=schedule,
        compiler=compiler, snapshot_compiler=snapshot_compiler,
        agenda_compiler=agenda_compiler, scientific_mode=scientific_mode,
    )
    result["gpu_preflight"] = {
        "status": "BLOCKED_P1",
        "blockers": list(V03R_GPU_P1_BLOCKERS),
        "cpu_gold_is_not_a_model_result": True,
    }
    result["experiment_hash"] = sha256_json({
        key: value for key, value in result.items() if key != "experiment_hash"
    })
    return result


def assert_v03r_gpu_preflight_ready() -> None:
    """Fail closed until the remaining bounded P1 audit is explicitly closed."""

    if V03R_GPU_P1_BLOCKERS:
        raise SchedulerError(
            "v0.3-R GPU preflight is blocked by P1: "
            + ", ".join(V03R_GPU_P1_BLOCKERS)
        )
