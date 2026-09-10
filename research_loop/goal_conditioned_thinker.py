"""CPU-only typed DFS thinker contract for the interleaved organism.

This is a control-plane reference, not a game solver or science result.  It
certifies the information flow of a narrow, goal-conditioned thinker over one
immutable semantic-memory checkpoint:

``goal -> subgoal -> exact query/follow -> scratch hypothesis -> prediction
       -> release | backtrack | request-dream | defer``

Memory reads use goal-declared query templates over checkpoint-declared entity
and relation handles.  The policy never supplies agenda-bound prose or query
IDs. Reads return exact bounded checkpoint items or ``NOT_FOUND``/``CONFLICT``.
Thinker hypotheses remain scratch state.  A request for later dreaming can be
projected only from mechanically created missing/conflict records, and the
projection deliberately drops candidate objects, hypotheses, answers,
rationales, citations, and evidence.  It is therefore a selection signal, not
a premise that a future dream may cite.

Release is deliberately fail-closed: v1 certifies only a supported directed
semantic-edge path from a public anchor handle to a public output handle.  A
domain whose answer is not licensed by that structural rule must DEFER rather
than treating a citation as semantic entailment.

``REQUEST_DREAM`` ends the current thinker.  The next checkpoint always starts
a fresh replan; resuming scratch state across the dream boundary is a future
ablation, not a v1 behavior.

The implementation is dependency-free and deterministic so it can be used as
a CPU contract gate before any text-model or LoRA run.  Its scripted policy is
an oracle read-plan ceiling, not an autonomous thinker or science result.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass
import hashlib
import json
import re
from types import MappingProxyType
from typing import Any, Iterable, Mapping, Sequence


SCHEMA_VERSION = "typed-goal-thinker-v1.1"
RESET_POLICY = "FRESH_REPLAN_AFTER_DREAM"
MAX_READ_RESULTS = 16
OPERATIONS = frozenset({
    "FORM_SUBGOAL",
    "QUERY",
    "FOLLOW",
    "HYPOTHESIZE",
    "PREDICT",
    "REVISE",
    "BACKTRACK",
    "REQUEST_DREAM",
    "RELEASE",
    "DEFER",
})
TERMINAL_OPERATIONS = frozenset({"REQUEST_DREAM", "RELEASE", "DEFER"})
ITEM_KINDS = frozenset({"concept", "semantic_edge"})
EPISTEMIC_STATUSES = frozenset({"supported", "provisional"})
CARDINALITIES = frozenset({"ONE", "MANY"})
DEFER_REASONS = frozenset({
    "INSUFFICIENT_MEMORY",
    "UNRESOLVED_CONFLICT",
    "NO_PROGRESS",
    "BUDGET_EXHAUSTED",
    "POLICY_ERROR",
})
BACKTRACK_REASONS = frozenset({"DEAD_END", "CONFLICT", "LOW_VALUE", "REVISE_PLAN"})
REVISION_KINDS = frozenset({"ADD_SUPPORT", "DROP_SUPPORT", "REPLACE", "RESOLVE_CONFLICT"})
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_HANDLE = re.compile(r"^[A-Za-z][A-Za-z0-9_.:-]{0,127}$")
_NORMALIZE = re.compile(r"\s+")
_FORBIDDEN_INPUT_KEY = re.compile(
    r"(?:hidden|secret|expected|ground[_ -]?truth|answer[_ -]?key|"
    r"final[_ -]?answer|proof[_ -]?graph|factor[_ -]?solver|scorer|"
    r"evaluator|verdict|agenda|desire|confusion|hypothesis|scratch|"
    r"thinker[_ -]?(?:state|trace|confidence)|prior[_ -]?(?:think|trace)|"
    r"intermediate[_ -]?think)",
    re.IGNORECASE,
)
_FORBIDDEN_INPUT_TEXT = re.compile(
    r"(?:final[_ -]?answer\s*:|answer[_ -]?key\s*:|hidden[_ -]?truth\s*:|"
    r"proof[_ -]?graph\s*:|factor[_ -]?solver\s*:|offline[_ -]?truth\s*:)",
    re.IGNORECASE,
)


class ThinkerContractError(ValueError):
    """Raised when an artifact or state transition violates the contract."""


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def normalize(value: str) -> str:
    return _NORMALIZE.sub(" ", value.strip().casefold())


def _require_nonempty(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ThinkerContractError(f"{path}: must be a non-empty string")
    return value.strip()


def _require_handle(value: Any, path: str) -> str:
    value = _require_nonempty(value, path)
    if _HANDLE.fullmatch(value) is None:
        raise ThinkerContractError(f"{path}: must be an opaque typed handle")
    return value


def _require_exact_keys(value: Mapping[str, Any], allowed: set[str], path: str) -> None:
    extra = set(value) - allowed
    missing = allowed - set(value)
    if extra:
        raise ThinkerContractError(f"{path}: unexpected fields {sorted(extra)}")
    if missing:
        raise ThinkerContractError(f"{path}: missing fields {sorted(missing)}")


def _walk(value: Any, path: str = "") -> Iterable[tuple[str, Any]]:
    if isinstance(value, Mapping):
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else str(key)
            yield child_path, key
            yield from _walk(child, child_path)
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            yield from _walk(child, f"{path}[{index}]")
    else:
        yield path, value


def _reject_hidden_inputs(value: Any, path: str) -> None:
    for nested_path, item in _walk(value, path):
        if _FORBIDDEN_INPUT_KEY.search(nested_path):
            raise ThinkerContractError(f"{nested_path}: hidden/checker field forbidden")
        if isinstance(item, str) and _FORBIDDEN_INPUT_TEXT.search(item):
            raise ThinkerContractError(f"{nested_path}: hidden/checker text forbidden")


@dataclass(frozen=True)
class FrozenEntitySpec:
    entity_id: str
    label: str


@dataclass(frozen=True)
class FrozenRelationSpec:
    relation_id: str
    label: str
    cardinality: str
    max_results: int


@dataclass(frozen=True)
class FrozenSemanticItem:
    semantic_id: str
    kind: str
    subject_entity_id: str
    relation_id: str
    object_entity_id: str
    content: str
    status: str
    linked_semantic_ids: tuple[str, ...]
    source_ids: tuple[str, ...]
    semantic_hash: str

    def public_payload(self) -> dict[str, Any]:
        """The exact payload returned by a memory read."""

        return asdict(self)


@dataclass(frozen=True)
class FrozenMemoryCheckpoint:
    schema_version: str
    checkpoint_id: str
    world_id: str
    skin_id: str
    life_id: str
    round_index: int
    source_checkpoint_hash: str
    entities: tuple[FrozenEntitySpec, ...]
    relation_specs: tuple[FrozenRelationSpec, ...]
    items: tuple[FrozenSemanticItem, ...]
    semantic_state_hash: str
    checkpoint_hash: str

    @property
    def scope(self) -> tuple[str, str, str]:
        return (self.world_id, self.skin_id, self.life_id)


def semantic_item_hash(payload: Mapping[str, Any]) -> str:
    material = {
        key: payload[key]
        for key in (
            "semantic_id",
            "kind",
            "subject_entity_id",
            "relation_id",
            "object_entity_id",
            "content",
            "status",
            "linked_semantic_ids",
            "source_ids",
        )
    }
    return digest(material)


def make_semantic_item(
    semantic_id: str,
    *,
    kind: str,
    subject_entity_id: str,
    relation_id: str,
    object_entity_id: str,
    content: str,
    status: str = "supported",
    linked_semantic_ids: Sequence[str] = (),
    source_ids: Sequence[str] = (),
) -> dict[str, Any]:
    """Build a JSON-shaped item with a content-addressed semantic hash."""

    payload = {
        "semantic_id": semantic_id,
        "kind": kind,
        "subject_entity_id": subject_entity_id,
        "relation_id": relation_id,
        "object_entity_id": object_entity_id,
        "content": content,
        "status": status,
        "linked_semantic_ids": list(linked_semantic_ids),
        "source_ids": list(source_ids),
    }
    payload["semantic_hash"] = semantic_item_hash(payload)
    return payload


def freeze_checkpoint(payload: Mapping[str, Any]) -> FrozenMemoryCheckpoint:
    """Validate and copy a JSON checkpoint into immutable tuples.

    Mutating the caller's source dictionary after this function returns cannot
    change the reader's checkpoint.  Item hashes, state hash, and checkpoint
    hash make any serialized mutation visible at the next freeze boundary.
    """

    if not isinstance(payload, Mapping):
        raise ThinkerContractError("checkpoint: must be an object")
    _require_exact_keys(
        payload,
        {
            "schema_version",
            "checkpoint_id",
            "world_id",
            "skin_id",
            "life_id",
            "round_index",
            "source_checkpoint_hash",
            "entities",
            "relation_specs",
            "items",
            "semantic_state_hash",
            "checkpoint_hash",
        },
        "checkpoint",
    )
    if payload["schema_version"] != SCHEMA_VERSION:
        raise ThinkerContractError(f"checkpoint.schema_version: must be {SCHEMA_VERSION}")
    for field in ("checkpoint_id", "world_id", "skin_id", "life_id"):
        _require_nonempty(payload[field], f"checkpoint.{field}")
    if not isinstance(payload["round_index"], int) or isinstance(payload["round_index"], bool) \
            or payload["round_index"] < 0:
        raise ThinkerContractError("checkpoint.round_index: non-negative integer required")
    if not isinstance(payload["source_checkpoint_hash"], str) or \
            _SHA256.fullmatch(payload["source_checkpoint_hash"]) is None:
        raise ThinkerContractError("checkpoint.source_checkpoint_hash: sha256 required")
    _reject_hidden_inputs(payload, "checkpoint")

    entity_rows = payload["entities"]
    if not isinstance(entity_rows, list) or not entity_rows:
        raise ThinkerContractError("checkpoint.entities: non-empty list required")
    entities: list[FrozenEntitySpec] = []
    entity_ids: set[str] = set()
    for index, row in enumerate(entity_rows):
        path = f"checkpoint.entities[{index}]"
        if not isinstance(row, Mapping):
            raise ThinkerContractError(f"{path}: object required")
        _require_exact_keys(row, {"entity_id", "label"}, path)
        entity_id = _require_handle(row["entity_id"], f"{path}.entity_id")
        label = _require_nonempty(row["label"], f"{path}.label")
        if entity_id in entity_ids:
            raise ThinkerContractError(f"{path}.entity_id: duplicate")
        entity_ids.add(entity_id)
        entities.append(FrozenEntitySpec(entity_id, label))

    relation_rows = payload["relation_specs"]
    if not isinstance(relation_rows, list) or not relation_rows:
        raise ThinkerContractError("checkpoint.relation_specs: non-empty list required")
    relation_specs: list[FrozenRelationSpec] = []
    relation_ids: set[str] = set()
    relation_by_id: dict[str, FrozenRelationSpec] = {}
    for index, row in enumerate(relation_rows):
        path = f"checkpoint.relation_specs[{index}]"
        if not isinstance(row, Mapping):
            raise ThinkerContractError(f"{path}: object required")
        _require_exact_keys(row, {"relation_id", "label", "cardinality", "max_results"}, path)
        relation_id = _require_handle(row["relation_id"], f"{path}.relation_id")
        label = _require_nonempty(row["label"], f"{path}.label")
        if row["cardinality"] not in CARDINALITIES:
            raise ThinkerContractError(f"{path}.cardinality: invalid")
        if not isinstance(row["max_results"], int) or isinstance(row["max_results"], bool) \
                or not 1 <= row["max_results"] <= MAX_READ_RESULTS:
            raise ThinkerContractError(
                f"{path}.max_results: must be in [1,{MAX_READ_RESULTS}]"
            )
        if relation_id in relation_ids:
            raise ThinkerContractError(f"{path}.relation_id: duplicate")
        relation_ids.add(relation_id)
        spec = FrozenRelationSpec(
            relation_id, label, row["cardinality"], row["max_results"]
        )
        relation_specs.append(spec)
        relation_by_id[relation_id] = spec

    rows = payload["items"]
    if not isinstance(rows, list):
        raise ThinkerContractError("checkpoint.items: must be a list")

    items: list[FrozenSemanticItem] = []
    ids: set[str] = set()
    triples: set[tuple[str, str, str]] = set()
    item_fields = {
        "semantic_id",
        "kind",
        "subject_entity_id",
        "relation_id",
        "object_entity_id",
        "content",
        "status",
        "linked_semantic_ids",
        "source_ids",
        "semantic_hash",
    }
    for index, row in enumerate(rows):
        path = f"checkpoint.items[{index}]"
        if not isinstance(row, Mapping):
            raise ThinkerContractError(f"{path}: must be an object")
        _require_exact_keys(row, item_fields, path)
        for field in ("semantic_id", "subject_entity_id", "relation_id", "object_entity_id"):
            _require_handle(row[field], f"{path}.{field}")
        _require_nonempty(row["content"], f"{path}.content")
        if row["kind"] not in ITEM_KINDS:
            raise ThinkerContractError(f"{path}.kind: invalid")
        if row["status"] not in EPISTEMIC_STATUSES:
            raise ThinkerContractError(f"{path}.status: checkpoint items must be active")
        for field in ("linked_semantic_ids", "source_ids"):
            values = row[field]
            if not isinstance(values, list) or not all(isinstance(v, str) and v for v in values):
                raise ThinkerContractError(f"{path}.{field}: must be non-empty string ids")
            if len(values) != len(set(values)):
                raise ThinkerContractError(f"{path}.{field}: duplicate ids")
        if row["semantic_id"] in ids:
            raise ThinkerContractError(f"{path}.semantic_id: duplicate")
        ids.add(row["semantic_id"])
        if row["subject_entity_id"] not in entity_ids or row["object_entity_id"] not in entity_ids:
            raise ThinkerContractError(f"{path}: semantic endpoints must be declared entities")
        if row["relation_id"] not in relation_ids:
            raise ThinkerContractError(f"{path}.relation_id: undeclared relation")
        triple = (
            row["subject_entity_id"], row["relation_id"], row["object_entity_id"]
        )
        if triple in triples:
            raise ThinkerContractError(f"{path}: duplicate semantic triple")
        triples.add(triple)
        if row["semantic_hash"] != semantic_item_hash(row):
            raise ThinkerContractError(f"{path}.semantic_hash: mismatch")
        items.append(
            FrozenSemanticItem(
                semantic_id=row["semantic_id"],
                kind=row["kind"],
                subject_entity_id=row["subject_entity_id"],
                relation_id=row["relation_id"],
                object_entity_id=row["object_entity_id"],
                content=row["content"],
                status=row["status"],
                linked_semantic_ids=tuple(row["linked_semantic_ids"]),
                source_ids=tuple(row["source_ids"]),
                semantic_hash=row["semantic_hash"],
            )
        )
    for item in items:
        missing = set(item.linked_semantic_ids) - ids
        if missing:
            raise ThinkerContractError(
                f"checkpoint item {item.semantic_id}: unknown links {sorted(missing)}"
            )
    grouped: dict[tuple[str, str], int] = {}
    for item in items:
        key = (item.subject_entity_id, item.relation_id)
        grouped[key] = grouped.get(key, 0) + 1
    for (subject_id, relation_id), count in grouped.items():
        limit = relation_by_id[relation_id].max_results
        if count > limit:
            raise ThinkerContractError(
                f"checkpoint: {subject_id}/{relation_id} has {count} items; bound is {limit}"
            )
    state_material = [item.public_payload() for item in sorted(items, key=lambda x: x.semantic_id)]
    expected_state_hash = digest({
        "entities": [asdict(item) for item in sorted(entities, key=lambda x: x.entity_id)],
        "relation_specs": [
            asdict(item) for item in sorted(relation_specs, key=lambda x: x.relation_id)
        ],
        "items": state_material,
    })
    if payload["semantic_state_hash"] != expected_state_hash:
        raise ThinkerContractError("checkpoint.semantic_state_hash: mismatch")
    checkpoint_material = {
        "schema_version": SCHEMA_VERSION,
        "checkpoint_id": payload["checkpoint_id"],
        "world_id": payload["world_id"],
        "skin_id": payload["skin_id"],
        "life_id": payload["life_id"],
        "round_index": payload["round_index"],
        "source_checkpoint_hash": payload["source_checkpoint_hash"],
        "semantic_state_hash": expected_state_hash,
    }
    if payload["checkpoint_hash"] != digest(checkpoint_material):
        raise ThinkerContractError("checkpoint.checkpoint_hash: mismatch")
    return FrozenMemoryCheckpoint(
        schema_version=SCHEMA_VERSION,
        checkpoint_id=payload["checkpoint_id"],
        world_id=payload["world_id"],
        skin_id=payload["skin_id"],
        life_id=payload["life_id"],
        round_index=payload["round_index"],
        source_checkpoint_hash=payload["source_checkpoint_hash"],
        entities=tuple(entities),
        relation_specs=tuple(relation_specs),
        items=tuple(items),
        semantic_state_hash=expected_state_hash,
        checkpoint_hash=payload["checkpoint_hash"],
    )


def make_checkpoint(
    checkpoint_id: str,
    *,
    world_id: str,
    skin_id: str,
    life_id: str,
    entities: Sequence[Mapping[str, Any]],
    relation_specs: Sequence[Mapping[str, Any]],
    items: Sequence[Mapping[str, Any]],
    round_index: int = 0,
    source_checkpoint_hash: str | None = None,
) -> dict[str, Any]:
    rows = [deepcopy(dict(item)) for item in items]
    entity_rows = [deepcopy(dict(item)) for item in entities]
    relation_rows = [deepcopy(dict(item)) for item in relation_specs]
    state_hash = digest({
        "entities": sorted(entity_rows, key=lambda row: row["entity_id"]),
        "relation_specs": sorted(relation_rows, key=lambda row: row["relation_id"]),
        "items": sorted(rows, key=lambda row: row["semantic_id"]),
    })
    source_hash = source_checkpoint_hash or digest({
        "kind": "synthetic-cpu-checkpoint-source",
        "checkpoint_id": checkpoint_id,
        "world_id": world_id,
        "skin_id": skin_id,
        "life_id": life_id,
        "round_index": round_index,
        "semantic_state_hash": state_hash,
    })
    base = {
        "schema_version": SCHEMA_VERSION,
        "checkpoint_id": checkpoint_id,
        "world_id": world_id,
        "skin_id": skin_id,
        "life_id": life_id,
        "round_index": round_index,
        "source_checkpoint_hash": source_hash,
        "entities": entity_rows,
        "relation_specs": relation_rows,
        "items": rows,
        "semantic_state_hash": state_hash,
    }
    base["checkpoint_hash"] = digest({
        key: base[key] for key in base
        if key not in {"items", "entities", "relation_specs"}
    })
    # Ensure helpers never emit an artifact their own strict reader rejects.
    freeze_checkpoint(base)
    return base


class ExactCheckpointReader:
    """An immutable structured reader over one frozen checkpoint."""

    def __init__(self, checkpoint: FrozenMemoryCheckpoint):
        self._checkpoint = checkpoint
        self._by_id = MappingProxyType({item.semantic_id: item for item in checkpoint.items})
        self._relation_specs = MappingProxyType({
            item.relation_id: item for item in checkpoint.relation_specs
        })

    @property
    def checkpoint(self) -> FrozenMemoryCheckpoint:
        return self._checkpoint

    def retrieve(self, query: Mapping[str, Any]) -> dict[str, Any]:
        _require_exact_keys(
            query,
            {"query_id", "query_key", "subject_entity_id", "relation_id", "object_entity_id"},
            "query",
        )
        _require_handle(query["query_id"], "query.query_id")
        _require_handle(query["query_key"], "query.query_key")
        subject = _require_handle(query["subject_entity_id"], "query.subject_entity_id")
        relation = _require_handle(query["relation_id"], "query.relation_id")
        if relation not in self._relation_specs:
            raise ThinkerContractError("query.relation_id: outside checkpoint declaration")
        obj = query["object_entity_id"]
        if obj is not None:
            _require_handle(obj, "query.object_entity_id")
        matches = [
            item
            for item in self._checkpoint.items
            if item.subject_entity_id == subject
            and item.relation_id == relation
            and (obj is None or item.object_entity_id == obj)
        ]
        spec = self._relation_specs[relation]
        if len(matches) > spec.max_results:
            raise ThinkerContractError("query result exceeds frozen relation bound")
        if not matches:
            status = "NOT_FOUND"
        elif obj is None and spec.cardinality == "ONE" and len(matches) > 1:
            status = "CONFLICT"
        else:
            status = "FOUND"
        exact_items = [item.public_payload() for item in sorted(matches, key=lambda item: item.semantic_id)]
        result = {
            "query_id": query["query_id"],
            "query_key": query["query_key"],
            "subject_entity_id": subject,
            "relation_id": relation,
            "object_entity_id": obj,
            "cardinality": spec.cardinality,
            "max_results": spec.max_results,
            "checkpoint_id": self._checkpoint.checkpoint_id,
            "checkpoint_hash": self._checkpoint.checkpoint_hash,
            "status": status,
            "items": exact_items,
        }
        result["result_hash"] = digest(result)
        return result

    def follow(self, source_id: str, target_id: str) -> dict[str, Any]:
        if source_id not in self._by_id:
            raise ThinkerContractError("FOLLOW source is outside checkpoint")
        if target_id not in self._by_id:
            raise ThinkerContractError("FOLLOW target is outside checkpoint")
        if target_id not in self._by_id[source_id].linked_semantic_ids:
            raise ThinkerContractError("FOLLOW target is not a declared checkpoint link")
        item = self._by_id[target_id]
        result = {
            "checkpoint_id": self._checkpoint.checkpoint_id,
            "checkpoint_hash": self._checkpoint.checkpoint_hash,
            "status": "FOUND",
            "items": [item.public_payload()],
            "followed_from": source_id,
        }
        result["result_hash"] = digest(result)
        return result


_OP_FIELDS: dict[str, set[str]] = {
    "FORM_SUBGOAL": {"op", "subgoal_id", "description", "parent_subgoal_id"},
    "QUERY": {"op", "subgoal_id", "query_key", "object_entity_id"},
    "FOLLOW": {"op", "subgoal_id", "from_semantic_id", "to_semantic_id"},
    "HYPOTHESIZE": {
        "op", "subgoal_id", "hypothesis_id", "claim", "cited_semantic_ids",
        "parent_hypothesis_ids",
    },
    "PREDICT": {"op", "subgoal_id", "hypothesis_id", "prediction_entity_id"},
    "REVISE": {
        "op", "subgoal_id", "hypothesis_id", "new_hypothesis_id", "revised_claim",
        "cited_semantic_ids", "revision_kind",
    },
    "BACKTRACK": {"op", "subgoal_id", "reason_code", "promote_hypothesis_id"},
    "REQUEST_DREAM": {"op", "confusion_ids"},
    "RELEASE": {"op", "hypothesis_id"},
    "DEFER": {"op", "reason_code", "confusion_ids"},
}


def parse_operation(raw: str) -> dict[str, Any]:
    """Parse one bare JSON object; prose, arrays, and direct answers fail."""

    try:
        value = json.loads(raw)
    except (TypeError, json.JSONDecodeError) as exc:
        raise ThinkerContractError("operation: must be one bare JSON object") from exc
    if not isinstance(value, dict):
        raise ThinkerContractError("operation: must be one JSON object")
    validate_operation(value)
    return value


def validate_operation(operation: Mapping[str, Any]) -> None:
    if not isinstance(operation, Mapping):
        raise ThinkerContractError("operation: must be an object")
    op = operation.get("op")
    if op not in OPERATIONS:
        raise ThinkerContractError(f"operation.op: invalid; allowed={sorted(OPERATIONS)}")
    _require_exact_keys(operation, _OP_FIELDS[op], f"operation.{op}")
    if op == "FORM_SUBGOAL":
        for field in ("subgoal_id", "description"):
            _require_nonempty(operation[field], f"operation.{op}.{field}")
        if operation["parent_subgoal_id"] is not None:
            _require_nonempty(operation["parent_subgoal_id"], "operation.FORM_SUBGOAL.parent_subgoal_id")
    elif op == "QUERY":
        for field in ("subgoal_id", "query_key"):
            _require_handle(operation[field], f"operation.QUERY.{field}")
        if operation["object_entity_id"] is not None:
            _require_handle(
                operation["object_entity_id"], "operation.QUERY.object_entity_id"
            )
    elif op == "FOLLOW":
        for field in ("subgoal_id", "from_semantic_id", "to_semantic_id"):
            _require_nonempty(operation[field], f"operation.FOLLOW.{field}")
    elif op == "HYPOTHESIZE":
        for field in ("subgoal_id", "hypothesis_id", "claim"):
            _require_nonempty(operation[field], f"operation.HYPOTHESIZE.{field}")
        for field in ("cited_semantic_ids", "parent_hypothesis_ids"):
            if not isinstance(operation[field], list) or not all(
                isinstance(value, str) and value for value in operation[field]
            ):
                raise ThinkerContractError(f"operation.HYPOTHESIZE.{field}: string-id list required")
            if len(operation[field]) != len(set(operation[field])):
                raise ThinkerContractError(f"operation.HYPOTHESIZE.{field}: duplicates forbidden")
    elif op == "PREDICT":
        for field in ("subgoal_id", "hypothesis_id", "prediction_entity_id"):
            _require_handle(operation[field], f"operation.PREDICT.{field}")
    elif op == "REVISE":
        for field in ("subgoal_id", "hypothesis_id", "new_hypothesis_id", "revised_claim", "revision_kind"):
            _require_nonempty(operation[field], f"operation.REVISE.{field}")
        if operation["revision_kind"] not in REVISION_KINDS:
            raise ThinkerContractError("operation.REVISE.revision_kind: invalid")
        ids = operation["cited_semantic_ids"]
        if not isinstance(ids, list) or not all(isinstance(value, str) and value for value in ids):
            raise ThinkerContractError("operation.REVISE.cited_semantic_ids: string-id list required")
    elif op == "BACKTRACK":
        _require_nonempty(operation["subgoal_id"], "operation.BACKTRACK.subgoal_id")
        if operation["reason_code"] not in BACKTRACK_REASONS:
            raise ThinkerContractError("operation.BACKTRACK.reason_code: invalid")
        if operation["promote_hypothesis_id"] is not None:
            _require_handle(
                operation["promote_hypothesis_id"],
                "operation.BACKTRACK.promote_hypothesis_id",
            )
    elif op == "REQUEST_DREAM":
        values = operation["confusion_ids"]
        if not isinstance(values, list) or not values or not all(isinstance(value, str) and value for value in values):
            raise ThinkerContractError("operation.REQUEST_DREAM.confusion_ids: non-empty id list required")
    elif op == "RELEASE":
        _require_nonempty(operation["hypothesis_id"], "operation.RELEASE.hypothesis_id")
    elif op == "DEFER":
        if operation["reason_code"] not in DEFER_REASONS:
            raise ThinkerContractError("operation.DEFER.reason_code: invalid")
        values = operation["confusion_ids"]
        if not isinstance(values, list) or not all(isinstance(value, str) and value for value in values):
            raise ThinkerContractError("operation.DEFER.confusion_ids: string-id list required")


def operation_fingerprint(operation: Mapping[str, Any]) -> str:
    """Hash semantic operation content, excluding disposable output ids.

    Without this normalization a policy could evade the repeat guard merely by
    renaming ``q-1`` to ``q-2`` while asking the identical question—the exact
    failure observed in the historical sequential thinker.
    """

    validate_operation(operation)
    material = deepcopy(dict(operation))
    for field in ("hypothesis_id", "new_hypothesis_id", "subgoal_id"):
        material.pop(field, None)
    if material["op"] == "FORM_SUBGOAL":
        material["description"] = normalize(material["description"])
    if material["op"] == "QUERY":
        material["query_key"] = normalize(material["query_key"])
        if material["object_entity_id"] is not None:
            material["object_entity_id"] = normalize(material["object_entity_id"])
    if material["op"] in {"HYPOTHESIZE", "REVISE"}:
        claim_key = "claim" if material["op"] == "HYPOTHESIZE" else "revised_claim"
        material[claim_key] = normalize(material[claim_key])
        material["cited_semantic_ids"] = sorted(material["cited_semantic_ids"])
    return digest(material)


def _validate_goal(goal: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(goal, Mapping):
        raise ThinkerContractError("goal: must be an object")
    _require_exact_keys(
        goal, {"goal_id", "task", "public_context", "query_scope", "release_contract"},
        "goal",
    )
    _require_handle(goal["goal_id"], "goal.goal_id")
    _require_nonempty(goal["task"], "goal.task")
    if not isinstance(goal["public_context"], Mapping):
        raise ThinkerContractError("goal.public_context: must be an object")
    query_scope = goal["query_scope"]
    if not isinstance(query_scope, Mapping):
        raise ThinkerContractError("goal.query_scope: object required")
    _require_exact_keys(query_scope, {"templates"}, "goal.query_scope")
    templates = query_scope["templates"]
    if not isinstance(templates, list) or not templates or len(templates) > 64:
        raise ThinkerContractError("goal.query_scope.templates: 1..64 templates required")
    query_keys: set[str] = set()
    for index, template in enumerate(templates):
        path = f"goal.query_scope.templates[{index}]"
        if not isinstance(template, Mapping):
            raise ThinkerContractError(f"{path}: object required")
        _require_exact_keys(
            template,
            {
                "query_key", "subject_entity_id", "relation_id",
                "allow_unknown_object", "allowed_object_entity_ids",
            },
            path,
        )
        for field in ("query_key", "subject_entity_id", "relation_id"):
            _require_handle(template[field], f"{path}.{field}")
        if template["query_key"] in query_keys:
            raise ThinkerContractError(f"{path}.query_key: duplicate")
        query_keys.add(template["query_key"])
        if not isinstance(template["allow_unknown_object"], bool):
            raise ThinkerContractError(f"{path}.allow_unknown_object: bool required")
        allowed_objects = template["allowed_object_entity_ids"]
        if not isinstance(allowed_objects, list) or not all(
            isinstance(item, str) and _HANDLE.fullmatch(item) for item in allowed_objects
        ) or len(allowed_objects) != len(set(allowed_objects)):
            raise ThinkerContractError(
                f"{path}.allowed_object_entity_ids: unique typed-handle list required"
            )
        if not template["allow_unknown_object"] and not allowed_objects:
            raise ThinkerContractError(f"{path}: template permits no legal object")

    contract = goal["release_contract"]
    if not isinstance(contract, Mapping):
        raise ThinkerContractError("goal.release_contract: object required")
    _require_exact_keys(
        contract,
        {
            "mode", "anchor_entity_ids", "allowed_output_entity_ids",
            "min_path_edges", "max_path_edges",
        },
        "goal.release_contract",
    )
    if contract["mode"] != "DIRECTED_PATH":
        raise ThinkerContractError("goal.release_contract.mode: only DIRECTED_PATH is certified")
    for field in ("anchor_entity_ids", "allowed_output_entity_ids"):
        values = contract[field]
        if not isinstance(values, list) or not values or not all(
            isinstance(item, str) and _HANDLE.fullmatch(item) for item in values
        ) or len(values) != len(set(values)):
            raise ThinkerContractError(f"goal.release_contract.{field}: unique handles required")
    minimum = contract["min_path_edges"]
    maximum = contract["max_path_edges"]
    if not isinstance(minimum, int) or isinstance(minimum, bool) or minimum < 1:
        raise ThinkerContractError("goal.release_contract.min_path_edges: positive int required")
    if not isinstance(maximum, int) or isinstance(maximum, bool) or \
            not minimum <= maximum <= MAX_READ_RESULTS:
        raise ThinkerContractError("goal.release_contract.max_path_edges: invalid bound")
    _reject_hidden_inputs(goal, "goal")
    return deepcopy(dict(goal))


def _bind_goal_to_checkpoint(
    goal: Mapping[str, Any], checkpoint: FrozenMemoryCheckpoint,
) -> dict[str, Mapping[str, Any]]:
    entities = {item.entity_id for item in checkpoint.entities}
    relations = {item.relation_id for item in checkpoint.relation_specs}
    templates: dict[str, Mapping[str, Any]] = {}
    for template in goal["query_scope"]["templates"]:
        if template["subject_entity_id"] not in entities:
            raise ThinkerContractError("goal query template subject is outside checkpoint")
        if template["relation_id"] not in relations:
            raise ThinkerContractError("goal query template relation is outside checkpoint")
        if not set(template["allowed_object_entity_ids"]) <= entities:
            raise ThinkerContractError("goal query template object is outside checkpoint")
        templates[template["query_key"]] = template
    contract_entities = set(goal["release_contract"]["anchor_entity_ids"]) | set(
        goal["release_contract"]["allowed_output_entity_ids"]
    )
    if not contract_entities <= entities:
        raise ThinkerContractError("goal release contract entity is outside checkpoint")
    return templates


def _new_confusion(
    step_index: int,
    subgoal_id: str,
    query: Mapping[str, Any],
    result_status: str,
) -> dict[str, Any]:
    # Candidate objects are deliberately not copied. Only an unknown-slot query
    # can become a dream agenda; a failed candidate test is not a missing fact.
    payload = {
        "confusion_id": f"conf-{step_index:04d}",
        "subgoal_id": subgoal_id,
        "query_id": query["query_id"],
        "query_key": query["query_key"],
        "kind": "MISSING_DEPENDENCY" if result_status == "NOT_FOUND" else "CONFLICT",
        "subject_entity_id": query["subject_entity_id"],
        "relation_id": query["relation_id"],
        "unknown_slot": "object",
        "object_was_unknown": query["object_entity_id"] is None,
        "status": "OPEN",
        "created_step": step_index,
    }
    payload["confusion_hash"] = digest(payload)
    return payload


class ThinkerMachine:
    """Deterministic transition machine shared by scripted and model policies."""

    def __init__(
        self,
        checkpoint: FrozenMemoryCheckpoint,
        goal: Mapping[str, Any],
        *,
        max_steps: int = 16,
        max_repeat_blocks: int = 2,
    ):
        if not isinstance(max_steps, int) or max_steps < 1:
            raise ThinkerContractError("max_steps: must be a positive integer")
        if not isinstance(max_repeat_blocks, int) or max_repeat_blocks < 1:
            raise ThinkerContractError("max_repeat_blocks: must be a positive integer")
        self.reader = ExactCheckpointReader(checkpoint)
        self.goal = _validate_goal(goal)
        self.query_templates = _bind_goal_to_checkpoint(self.goal, checkpoint)
        self.max_steps = max_steps
        self.max_repeat_blocks = max_repeat_blocks
        self.frames: dict[str, dict[str, Any]] = {
            "root": {
                "subgoal_id": "root",
                "description": self.goal["task"],
                "parent_subgoal_id": None,
                "status": "ACTIVE",
                "created_step": -1,
            }
        }
        self.stack: list[str] = ["root"]
        self.retrieved: dict[str, dict[str, Any]] = {}
        self.hypotheses: dict[str, dict[str, Any]] = {}
        self.confusions: dict[str, dict[str, Any]] = {}
        self.desires: dict[str, dict[str, Any]] = {}
        self.trace: list[dict[str, Any]] = []
        self.seen_fingerprints: set[str] = set()
        self.repeat_blocks = 0
        self.last_transition_notice: dict[str, Any] | None = None
        self.terminal: dict[str, Any] | None = None
        self.follow_edges: list[tuple[str, str]] = []
        self.rejected_attempts: list[dict[str, Any]] = []

    @property
    def active_subgoal_id(self) -> str:
        return self.stack[-1]

    def _state_material(self) -> dict[str, Any]:
        return {
            "goal": self.goal,
            "checkpoint_id": self.reader.checkpoint.checkpoint_id,
            "checkpoint_hash": self.reader.checkpoint.checkpoint_hash,
            "frames": self.frames,
            "stack": self.stack,
            "retrieved": self.retrieved,
            "hypotheses": self.hypotheses,
            "confusions": self.confusions,
            "desires": self.desires,
            "terminal": self.terminal,
            "follow_edges": self.follow_edges,
            "rejected_attempts": self.rejected_attempts,
            "repeat_blocks": self.repeat_blocks,
            "last_transition_notice": self.last_transition_notice,
            "reset_policy": RESET_POLICY,
        }

    def public_state(self) -> dict[str, Any]:
        """Return model-visible state plus exact operation schemas."""

        state = deepcopy(self._state_material())
        state.update({
            "schema_version": SCHEMA_VERSION,
            "step_index": len(self.trace),
            "budget_remaining": max(0, self.max_steps - len(self.trace)),
            "active_subgoal_id": self.active_subgoal_id,
            "operation_fields": {key: sorted(value) for key, value in sorted(_OP_FIELDS.items())},
        })
        state["state_hash"] = digest(state)
        return state

    def _require_active(self, subgoal_id: str) -> None:
        if subgoal_id != self.active_subgoal_id:
            raise ThinkerContractError(
                f"operation targets {subgoal_id}, but active DFS branch is {self.active_subgoal_id}"
            )

    def _walk_hypothesis_lineage(self, hypothesis_id: str) -> tuple[set[str], set[str], int]:
        """Return lineage IDs, citations, and depth for a DAG.

        ``visiting`` detects an actual recursion-stack cycle while ``completed``
        memoizes shared ancestry.  A diamond is therefore visited once rather
        than falsely rejected as a cycle.
        """

        visiting: set[str] = set()
        completed: set[str] = set()
        citations: set[str] = set()
        depth_cache: dict[str, int] = {}

        def visit(current: str) -> int:
            if current in visiting:
                raise ThinkerContractError("hypothesis lineage cycle")
            if current in completed:
                return depth_cache[current]
            if current not in self.hypotheses:
                raise ThinkerContractError("hypothesis lineage references unknown parent")
            visiting.add(current)
            hypothesis = self.hypotheses[current]
            parent_depths = [visit(parent) for parent in hypothesis["parent_hypothesis_ids"]]
            citations.update(hypothesis["cited_semantic_ids"])
            visiting.remove(current)
            completed.add(current)
            depth_cache[current] = 1 + max(parent_depths, default=0)
            return depth_cache[current]

        depth = visit(hypothesis_id)
        return completed, citations, depth

    def _cited_item_ids(self, hypothesis_id: str) -> set[str]:
        return self._walk_hypothesis_lineage(hypothesis_id)[1]

    def _release_support_path(
        self, prediction_entity_id: str, cited_semantic_ids: set[str],
    ) -> list[str]:
        contract = self.goal["release_contract"]
        if prediction_entity_id not in contract["allowed_output_entity_ids"]:
            raise ThinkerContractError("PREDICT output is outside the public release contract")
        by_id = {item.semantic_id: item for item in self.reader.checkpoint.items}
        outgoing: dict[str, list[FrozenSemanticItem]] = {}
        for semantic_id in sorted(cited_semantic_ids):
            item = by_id[semantic_id]
            if item.kind != "semantic_edge" or item.status != "supported":
                continue
            outgoing.setdefault(item.subject_entity_id, []).append(item)
        for values in outgoing.values():
            values.sort(key=lambda item: item.semantic_id)
        minimum = contract["min_path_edges"]
        maximum = contract["max_path_edges"]
        queue: list[tuple[str, tuple[str, ...], frozenset[str]]] = [
            (anchor, (), frozenset({anchor}))
            for anchor in sorted(contract["anchor_entity_ids"])
        ]
        cursor = 0
        while cursor < len(queue):
            entity_id, path, visited_entities = queue[cursor]
            cursor += 1
            if entity_id == prediction_entity_id and minimum <= len(path) <= maximum:
                return list(path)
            if len(path) >= maximum:
                continue
            for item in outgoing.get(entity_id, []):
                if item.object_entity_id in visited_entities:
                    continue
                queue.append((
                    item.object_entity_id,
                    (*path, item.semantic_id),
                    visited_entities | {item.object_entity_id},
                ))
        raise ThinkerContractError(
            "RELEASE lacks a supported directed path licensed by the public contract"
        )

    def apply(self, operation: Mapping[str, Any], *, emitter: str = "policy") -> dict[str, Any]:
        if self.terminal is not None:
            raise ThinkerContractError("trace is already terminal")
        if sum(step["emitter"] == "policy" for step in self.trace) >= self.max_steps \
                and emitter == "policy":
            raise ThinkerContractError("policy budget exhausted")
        validate_operation(operation)
        operation = deepcopy(dict(operation))
        before_hash = digest(self._state_material())
        fingerprint = operation_fingerprint(operation)
        if fingerprint in self.seen_fingerprints and emitter == "policy":
            self.repeat_blocks += 1
            self.last_transition_notice = {
                "kind": "REPEAT_BLOCKED",
                "reason_code": "DUPLICATE_OPERATION",
                "operation_fingerprint": fingerprint,
                "operation": operation,
            }
            step = {
                "step_id": f"think-step-{len(self.trace):04d}",
                "step_index": len(self.trace),
                "emitter": emitter,
                "operation": operation,
                "outcome": "REPEAT_BLOCKED",
                "checkpoint_id": self.reader.checkpoint.checkpoint_id,
                "checkpoint_hash": self.reader.checkpoint.checkpoint_hash,
                "state_before_hash": before_hash,
            }
            self.trace.append(step)
            step["state_after_hash"] = digest(self._state_material())
            step["step_hash"] = digest({key: value for key, value in step.items() if key != "step_hash"})
            return deepcopy(step)
        self.seen_fingerprints.add(fingerprint)
        self.last_transition_notice = None

        op = operation["op"]
        outcome: Any = "APPLIED"
        if op == "FORM_SUBGOAL":
            parent = operation["parent_subgoal_id"]
            if parent != self.active_subgoal_id:
                raise ThinkerContractError("FORM_SUBGOAL must descend from active branch")
            subgoal_id = operation["subgoal_id"]
            if subgoal_id in self.frames:
                raise ThinkerContractError("FORM_SUBGOAL id already exists")
            self.frames[subgoal_id] = {
                "subgoal_id": subgoal_id,
                "description": operation["description"],
                "parent_subgoal_id": parent,
                "status": "ACTIVE",
                "created_step": len(self.trace),
            }
            self.frames[parent]["status"] = "SUSPENDED"
            self.stack.append(subgoal_id)
        elif op == "QUERY":
            self._require_active(operation["subgoal_id"])
            template = self.query_templates.get(operation["query_key"])
            if template is None:
                raise ThinkerContractError("QUERY key is outside the goal-declared scope")
            object_entity_id = operation["object_entity_id"]
            if object_entity_id is None:
                if not template["allow_unknown_object"]:
                    raise ThinkerContractError("QUERY template does not allow an unknown object")
            elif object_entity_id not in template["allowed_object_entity_ids"]:
                raise ThinkerContractError("QUERY object is outside the declared template")
            query = {
                "query_id": f"query-{len(self.trace):04d}",
                "query_key": template["query_key"],
                "subject_entity_id": template["subject_entity_id"],
                "relation_id": template["relation_id"],
                "object_entity_id": object_entity_id,
            }
            result = self.reader.retrieve(query)
            self.retrieved[result["result_hash"]] = result
            outcome = result
            if result["status"] in {"NOT_FOUND", "CONFLICT"}:
                confusion = _new_confusion(
                    len(self.trace), operation["subgoal_id"], query, result["status"]
                )
                self.confusions[confusion["confusion_id"]] = confusion
        elif op == "FOLLOW":
            self._require_active(operation["subgoal_id"])
            source = operation["from_semantic_id"]
            already_retrieved = {
                item["semantic_id"]
                for result in self.retrieved.values()
                for item in result["items"]
            }
            if source not in already_retrieved:
                raise ThinkerContractError("FOLLOW source was not retrieved")
            result = self.reader.follow(source, operation["to_semantic_id"])
            self.retrieved[result["result_hash"]] = result
            edge = (source, operation["to_semantic_id"])
            if edge not in self.follow_edges:
                self.follow_edges.append(edge)
            outcome = result
        elif op == "HYPOTHESIZE":
            self._require_active(operation["subgoal_id"])
            hypothesis_id = operation["hypothesis_id"]
            if hypothesis_id in self.hypotheses:
                raise ThinkerContractError("HYPOTHESIZE id already exists")
            retrieved_ids = {
                item["semantic_id"]
                for result in self.retrieved.values()
                for item in result["items"]
            }
            citations = set(operation["cited_semantic_ids"])
            if not citations or not citations <= retrieved_ids:
                raise ThinkerContractError("HYPOTHESIZE may cite only retrieved memory and needs support")
            parents = operation["parent_hypothesis_ids"]
            if any(parent not in self.hypotheses for parent in parents):
                raise ThinkerContractError("HYPOTHESIZE parent is unknown")
            for parent_id in parents:
                parent = self.hypotheses[parent_id]
                same_branch = (
                    parent["subgoal_id"] == operation["subgoal_id"]
                    and parent["status"] == "TENTATIVE"
                )
                governed_promotion = (
                    parent["status"] == "PROMOTED"
                    and parent.get("promoted_to_subgoal_id") == operation["subgoal_id"]
                )
                if not (same_branch or governed_promotion):
                    raise ThinkerContractError(
                        "HYPOTHESIZE parent must be live on this branch or explicitly promoted"
                    )
            self.hypotheses[hypothesis_id] = {
                "hypothesis_id": hypothesis_id,
                "subgoal_id": operation["subgoal_id"],
                "claim": operation["claim"],
                "cited_semantic_ids": list(operation["cited_semantic_ids"]),
                "parent_hypothesis_ids": list(parents),
                "prediction": None,
                "created_step": len(self.trace),
                "status": "TENTATIVE",
                "promoted_to_subgoal_id": None,
            }
        elif op == "PREDICT":
            self._require_active(operation["subgoal_id"])
            hypothesis_id = operation["hypothesis_id"]
            if hypothesis_id not in self.hypotheses:
                raise ThinkerContractError("PREDICT hypothesis is unknown")
            if self.hypotheses[hypothesis_id]["subgoal_id"] != operation["subgoal_id"]:
                raise ThinkerContractError("PREDICT hypothesis belongs to another branch")
            if self.hypotheses[hypothesis_id]["status"] != "TENTATIVE":
                raise ThinkerContractError("PREDICT requires a live hypothesis")
            if self.hypotheses[hypothesis_id]["prediction"] is not None:
                raise ThinkerContractError("PREDICT cannot overwrite a prediction; REVISE instead")
            if operation["prediction_entity_id"] not in \
                    self.goal["release_contract"]["allowed_output_entity_ids"]:
                raise ThinkerContractError("PREDICT output is outside public choices")
            self.hypotheses[hypothesis_id]["prediction"] = operation["prediction_entity_id"]
        elif op == "REVISE":
            self._require_active(operation["subgoal_id"])
            old_id = operation["hypothesis_id"]
            new_id = operation["new_hypothesis_id"]
            if old_id not in self.hypotheses or new_id in self.hypotheses:
                raise ThinkerContractError("REVISE requires known old and unused new ids")
            if self.hypotheses[old_id]["subgoal_id"] != operation["subgoal_id"] or \
                    self.hypotheses[old_id]["status"] != "TENTATIVE":
                raise ThinkerContractError("REVISE requires a live active-branch hypothesis")
            retrieved_ids = {
                item["semantic_id"]
                for result in self.retrieved.values()
                for item in result["items"]
            }
            citations = set(operation["cited_semantic_ids"])
            if not citations or not citations <= retrieved_ids:
                raise ThinkerContractError("REVISE may cite only retrieved memory and needs support")
            self.hypotheses[old_id]["status"] = "SUPERSEDED"
            self.hypotheses[new_id] = {
                "hypothesis_id": new_id,
                "subgoal_id": operation["subgoal_id"],
                "claim": operation["revised_claim"],
                "cited_semantic_ids": list(operation["cited_semantic_ids"]),
                "parent_hypothesis_ids": [old_id],
                "prediction": None,
                "created_step": len(self.trace),
                "status": "TENTATIVE",
                "promoted_to_subgoal_id": None,
                "revision_kind": operation["revision_kind"],
            }
        elif op == "BACKTRACK":
            self._require_active(operation["subgoal_id"])
            if len(self.stack) == 1:
                raise ThinkerContractError("cannot BACKTRACK past root")
            removed = self.active_subgoal_id
            promoted_id = operation["promote_hypothesis_id"]
            parent_subgoal_id = self.frames[removed]["parent_subgoal_id"]
            assert parent_subgoal_id is not None
            if promoted_id is not None:
                hypothesis = self.hypotheses.get(promoted_id)
                if hypothesis is None or hypothesis["subgoal_id"] != removed or \
                        hypothesis["status"] != "TENTATIVE":
                    raise ThinkerContractError(
                        "BACKTRACK promotion requires a live hypothesis owned by the branch"
                    )
                if any(
                    confusion["subgoal_id"] == removed and confusion["status"] == "OPEN"
                    for confusion in self.confusions.values()
                ):
                    raise ThinkerContractError(
                        "BACKTRACK cannot promote across an unresolved branch confusion"
                    )
                hypothesis["status"] = "PROMOTED"
                hypothesis["promoted_to_subgoal_id"] = parent_subgoal_id
                self.frames[removed]["status"] = "RESOLVED"
            else:
                self.frames[removed]["status"] = "ABANDONED"
            for hypothesis_id, hypothesis in self.hypotheses.items():
                owned = hypothesis["subgoal_id"] == removed
                promoted_here = hypothesis.get("promoted_to_subgoal_id") == removed
                if (owned or promoted_here) and hypothesis_id != promoted_id \
                        and hypothesis["status"] in {"TENTATIVE", "PROMOTED"}:
                    hypothesis["status"] = "ABANDONED"
                    hypothesis["promoted_to_subgoal_id"] = None
            self.stack.pop()
            self.frames[self.active_subgoal_id]["status"] = "ACTIVE"
            for confusion in self.confusions.values():
                if confusion["subgoal_id"] == removed and confusion["status"] == "OPEN":
                    confusion["status"] = "ABANDONED"
        elif op == "REQUEST_DREAM":
            requested = operation["confusion_ids"]
            if len(requested) != 1:
                raise ThinkerContractError("REQUEST_DREAM emits exactly one bounded agenda item")
            for confusion_id in requested:
                confusion = self.confusions.get(confusion_id)
                if confusion is None or confusion["status"] != "OPEN":
                    raise ThinkerContractError("REQUEST_DREAM requires an open confusion")
                if not confusion["object_was_unknown"]:
                    raise ThinkerContractError("candidate-valued query cannot become dream evidence/request")
            desire_ids = []
            for priority, confusion_id in enumerate(requested, start=1):
                confusion = self.confusions[confusion_id]
                desire = {
                    "desire_id": f"desire-{len(self.trace):04d}-{priority:02d}",
                    "source_confusion_id": confusion_id,
                    "kind": confusion["kind"],
                    "query_key": confusion["query_key"],
                    "subject_entity_id": confusion["subject_entity_id"],
                    "relation_id": confusion["relation_id"],
                    "unknown_slot": "object",
                    "priority": priority,
                    "non_evidentiary": True,
                    "created_step": len(self.trace),
                }
                desire["desire_hash"] = digest(desire)
                self.desires[desire["desire_id"]] = desire
                desire_ids.append(desire["desire_id"])
            self.terminal = {
                "kind": "REQUEST_DREAM",
                "confusion_ids": list(requested),
                "desire_ids": desire_ids,
            }
        elif op == "RELEASE":
            hypothesis_id = operation["hypothesis_id"]
            hypothesis = self.hypotheses.get(hypothesis_id)
            if hypothesis is None or hypothesis["status"] != "TENTATIVE" or \
                    hypothesis["subgoal_id"] != self.active_subgoal_id:
                raise ThinkerContractError("RELEASE requires a live active-branch hypothesis")
            if hypothesis["prediction"] is None:
                raise ThinkerContractError("RELEASE requires an explicit PREDICT step")
            open_here = [
                confusion
                for confusion in self.confusions.values()
                if confusion["status"] == "OPEN" and confusion["subgoal_id"] in self.stack
            ]
            if open_here:
                raise ThinkerContractError("RELEASE forbidden with unresolved active-branch confusion")
            cited = self._cited_item_ids(hypothesis_id)
            if not cited:
                raise ThinkerContractError("RELEASE requires a cited memory path")
            support_path = self._release_support_path(hypothesis["prediction"], cited)
            hypothesis["status"] = "RELEASED"
            entity_labels = {
                item.entity_id: item.label for item in self.reader.checkpoint.entities
            }
            self.terminal = {
                "kind": "RELEASE",
                "hypothesis_id": hypothesis_id,
                "output_entity_id": hypothesis["prediction"],
                "output": entity_labels[hypothesis["prediction"]],
                "support_path_semantic_ids": support_path,
            }
        elif op == "DEFER":
            requested = operation["confusion_ids"]
            if any(confusion_id not in self.confusions for confusion_id in requested):
                raise ThinkerContractError("DEFER cites unknown confusion")
            self.terminal = {
                "kind": "DEFER",
                "reason_code": operation["reason_code"],
                "confusion_ids": list(requested),
            }

        step = {
            "step_id": f"think-step-{len(self.trace):04d}",
            "step_index": len(self.trace),
            "emitter": emitter,
            "operation": operation,
            "outcome": outcome,
            "checkpoint_id": self.reader.checkpoint.checkpoint_id,
            "checkpoint_hash": self.reader.checkpoint.checkpoint_hash,
            "state_before_hash": before_hash,
        }
        self.trace.append(step)
        step["state_after_hash"] = digest(self._state_material())
        step["step_hash"] = digest({key: value for key, value in step.items() if key != "step_hash"})
        return deepcopy(step)

    def record_rejected_attempt(self, operation: Any, error: Exception) -> None:
        """Preserve an invalid policy proposal without applying its contents."""

        record = {
            "attempt_index": len(self.rejected_attempts),
            "step_index": len(self.trace),
            "raw_operation": deepcopy(operation),
            "error_type": type(error).__name__,
            "error": str(error),
            "checkpoint_hash": self.reader.checkpoint.checkpoint_hash,
        }
        record["attempt_hash"] = digest(record)
        self.rejected_attempts.append(record)

    def force_defer(self, reason_code: str) -> None:
        if self.terminal is not None:
            return
        self.apply(
            {
                "op": "DEFER",
                "reason_code": reason_code,
                "confusion_ids": sorted(
                    confusion_id
                    for confusion_id, confusion in self.confusions.items()
                    if confusion["status"] == "OPEN"
                ),
            },
            emitter="guard",
        )

    def _hypothesis_lineage(self, hypothesis_id: str) -> set[str]:
        return self._walk_hypothesis_lineage(hypothesis_id)[0]

    def _hypothesis_depth(self, hypothesis_id: str) -> int:
        return self._walk_hypothesis_lineage(hypothesis_id)[2]

    def _support_bearing_hypotheses(
        self, hypothesis_id: str, support_path: Sequence[str],
    ) -> tuple[set[str], int]:
        """Count only hypotheses that introduce a previously unused path edge."""

        path = set(support_path)
        visited: set[str] = set()
        introduced: set[str] = set()
        support_hypotheses: set[str] = set()
        support_depth: dict[str, int] = {}

        def visit(current: str) -> int:
            if current in visited:
                return support_depth[current]
            parent_depth = max(
                (visit(parent) for parent in self.hypotheses[current]["parent_hypothesis_ids"]),
                default=0,
            )
            novel = (
                set(self.hypotheses[current]["cited_semantic_ids"]) & path
            ) - introduced
            if novel:
                introduced.update(novel)
                support_hypotheses.add(current)
                support_depth[current] = parent_depth + 1
            else:
                support_depth[current] = parent_depth
            visited.add(current)
            return support_depth[current]

        depth = visit(hypothesis_id)
        return support_hypotheses, depth

    def metrics(self) -> dict[str, Any]:
        metrics = {
            "policy_steps": sum(step["emitter"] == "policy" for step in self.trace),
            "guard_steps": sum(step["emitter"] == "guard" for step in self.trace),
            "memory_queries": sum(step["operation"]["op"] == "QUERY" for step in self.trace),
            "memory_queries_served": sum(
                step["operation"]["op"] == "QUERY" and isinstance(step["outcome"], Mapping)
                for step in self.trace
            ),
            "not_found": sum(
                isinstance(step["outcome"], Mapping) and step["outcome"].get("status") == "NOT_FOUND"
                for step in self.trace
            ),
            "conflicts": sum(
                isinstance(step["outcome"], Mapping) and step["outcome"].get("status") == "CONFLICT"
                for step in self.trace
            ),
            "repeat_blocks": self.repeat_blocks,
            "rejected_attempts": len(self.rejected_attempts),
            "unique_follow_edges": len(set(self.follow_edges)),
            "terminal_kind": self.terminal["kind"] if self.terminal else None,
            "released_distinct_semantic_items": 0,
            "released_distinct_semantic_edges": 0,
            "released_scratch_hypotheses": 0,
            "released_support_bearing_hypotheses": 0,
            "released_hypothesis_lineage_depth": 0,
            "released_support_hypothesis_depth": 0,
            "thinker_compositional_path_depth": 0,
        }
        if self.terminal and self.terminal["kind"] == "RELEASE":
            hypothesis_id = self.terminal["hypothesis_id"]
            cited = self._cited_item_ids(hypothesis_id)
            lineage = self._hypothesis_lineage(hypothesis_id)
            hypothesis_depth = self._hypothesis_depth(hypothesis_id)
            support_path = self.terminal["support_path_semantic_ids"]
            support_hypotheses, support_hypothesis_depth = \
                self._support_bearing_hypotheses(hypothesis_id, support_path)
            # The headline uses only the certified support path and hypotheses
            # that introduce a new path edge. Irrelevant citations and chains of
            # paraphrase-only rewrites cannot increase it.
            metrics.update({
                "released_distinct_semantic_items": len(cited),
                "released_distinct_semantic_edges": len(support_path),
                "released_scratch_hypotheses": len(lineage),
                "released_support_bearing_hypotheses": len(support_hypotheses),
                "released_hypothesis_lineage_depth": hypothesis_depth,
                "released_support_hypothesis_depth": support_hypothesis_depth,
                "thinker_compositional_path_depth": (
                    len(support_path) + support_hypothesis_depth
                ),
            })
        return metrics

    def artifact(self) -> dict[str, Any]:
        if self.terminal is None:
            raise ThinkerContractError("cannot freeze a non-terminal thinker trace")
        body = {
            "schema_version": SCHEMA_VERSION,
            "goal": self.goal,
            "scope": {
                "world_id": self.reader.checkpoint.world_id,
                "skin_id": self.reader.checkpoint.skin_id,
                "life_id": self.reader.checkpoint.life_id,
            },
            "checkpoint_id": self.reader.checkpoint.checkpoint_id,
            "checkpoint_hash": self.reader.checkpoint.checkpoint_hash,
            "round_index": self.reader.checkpoint.round_index,
            "source_checkpoint_hash": self.reader.checkpoint.source_checkpoint_hash,
            "reset_policy": RESET_POLICY,
            "trace": self.trace,
            "terminal": self.terminal,
            "confusions": self.confusions,
            "desires": self.desires,
            "rejected_attempts": self.rejected_attempts,
            "metrics": self.metrics(),
        }
        body["trace_hash"] = digest(body)
        return deepcopy(body)


class ScriptedGoldPolicy:
    """Oracle read-plan ceiling for CPU fixtures; not an autonomous thinker."""

    def __init__(self, operations: Sequence[Mapping[str, Any]]):
        self._operations = tuple(deepcopy(dict(operation)) for operation in operations)
        self._index = 0

    def next_operation(self, _public_state: Mapping[str, Any]) -> dict[str, Any]:
        if self._index >= len(self._operations):
            raise StopIteration
        operation = deepcopy(self._operations[self._index])
        self._index += 1
        return operation


def run_scripted(
    checkpoint_payload: Mapping[str, Any],
    goal: Mapping[str, Any],
    operations: Sequence[Mapping[str, Any]],
    *,
    max_steps: int = 16,
    max_repeat_blocks: int = 2,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    """Run a deterministic gold path and return ``(trace, agenda_or_none)``."""

    machine = ThinkerMachine(
        freeze_checkpoint(checkpoint_payload),
        goal,
        max_steps=max_steps,
        max_repeat_blocks=max_repeat_blocks,
    )
    policy = ScriptedGoldPolicy(operations)
    exhausted_budget = True
    for _ in range(max_steps):
        if machine.terminal is not None:
            exhausted_budget = False
            break
        if machine.repeat_blocks >= max_repeat_blocks:
            machine.force_defer("NO_PROGRESS")
            exhausted_budget = False
            break
        try:
            operation = policy.next_operation(machine.public_state())
        except StopIteration:
            machine.force_defer("POLICY_ERROR")
            exhausted_budget = False
            break
        try:
            machine.apply(operation)
        except ThinkerContractError as exc:
            machine.record_rejected_attempt(operation, exc)
            machine.force_defer("POLICY_ERROR")
            exhausted_budget = False
            break
        if machine.repeat_blocks >= max_repeat_blocks and machine.terminal is None:
            machine.force_defer("NO_PROGRESS")
            exhausted_budget = False
            break
    if machine.terminal is None and exhausted_budget:
        machine.force_defer("BUDGET_EXHAUSTED")
    artifact = machine.artifact()
    agenda = project_non_evidentiary_agenda(artifact) if artifact["terminal"]["kind"] == "REQUEST_DREAM" else None
    return artifact, agenda


def project_non_evidentiary_agenda(trace: Mapping[str, Any]) -> dict[str, Any]:
    """Mechanically project unresolved slots; never copy model free text.

    The input must be a committed REQUEST_DREAM trace.  Only confusion records
    created by checkpoint reads are eligible.  The projection uses an exact
    allowlist and binds to both trace and checkpoint hashes.
    """

    if not isinstance(trace, Mapping) or trace.get("schema_version") != SCHEMA_VERSION:
        raise ThinkerContractError("agenda source: invalid thinker artifact")
    trace_hash = trace.get("trace_hash")
    if not isinstance(trace_hash, str) or not _SHA256.fullmatch(trace_hash):
        raise ThinkerContractError("agenda source: missing trace hash")
    material = {key: deepcopy(value) for key, value in trace.items() if key != "trace_hash"}
    if digest(material) != trace_hash:
        raise ThinkerContractError("agenda source: trace hash mismatch")
    terminal = trace.get("terminal")
    if not isinstance(terminal, Mapping) or terminal.get("kind") != "REQUEST_DREAM":
        raise ThinkerContractError("agenda source: terminal must be REQUEST_DREAM")
    confusions: dict[str, Mapping[str, Any]] = {}
    for step in trace.get("trace", []):
        outcome = step.get("outcome") if isinstance(step, Mapping) else None
        operation = step.get("operation") if isinstance(step, Mapping) else None
        if (
            isinstance(operation, Mapping)
            and operation.get("op") == "QUERY"
            and isinstance(outcome, Mapping)
            and outcome.get("status") in {"NOT_FOUND", "CONFLICT"}
            and operation.get("object_entity_id") is None
        ):
            query = {
                "query_id": outcome.get("query_id"),
                "query_key": outcome.get("query_key"),
                "subject_entity_id": outcome.get("subject_entity_id"),
                "relation_id": outcome.get("relation_id"),
                "object_entity_id": outcome.get("object_entity_id"),
            }
            confusion = _new_confusion(
                step["step_index"], operation["subgoal_id"], query, outcome["status"]
            )
            confusions[confusion["confusion_id"]] = confusion
    requested = terminal.get("confusion_ids")
    if not isinstance(requested, list) or len(requested) != 1:
        raise ThinkerContractError("agenda source: exactly one requested confusion required")
    artifact_confusions = trace.get("confusions")
    artifact_desires = trace.get("desires")
    if not isinstance(artifact_confusions, Mapping) or not isinstance(artifact_desires, Mapping):
        raise ThinkerContractError("agenda source: missing typed confusion/desire records")
    desire_ids = terminal.get("desire_ids")
    if not isinstance(desire_ids, list) or len(desire_ids) != len(requested):
        raise ThinkerContractError("agenda source: desire/confusion cardinality mismatch")
    request_steps = [
        step
        for step in trace.get("trace", [])
        if isinstance(step, Mapping)
        and isinstance(step.get("operation"), Mapping)
        and step["operation"].get("op") == "REQUEST_DREAM"
    ]
    if len(request_steps) != 1:
        raise ThinkerContractError("agenda source: exactly one terminal request step required")
    request_step_index = request_steps[0].get("step_index")
    items = []
    for priority, (confusion_id, desire_id) in enumerate(zip(requested, desire_ids), start=1):
        confusion = confusions.get(confusion_id)
        if confusion is None:
            raise ThinkerContractError("agenda source: request is not backed by a read confusion")
        recorded_confusion = artifact_confusions.get(confusion_id)
        if not isinstance(recorded_confusion, Mapping) or recorded_confusion != confusion:
            raise ThinkerContractError("agenda source: confusion record does not match read result")
        desire = artifact_desires.get(desire_id)
        if not isinstance(desire, Mapping):
            raise ThinkerContractError("agenda source: missing desire record")
        expected_desire = {
            "desire_id": desire_id,
            "source_confusion_id": confusion_id,
            "kind": confusion["kind"],
            "query_key": confusion["query_key"],
            "subject_entity_id": confusion["subject_entity_id"],
            "relation_id": confusion["relation_id"],
            "unknown_slot": "object",
            "priority": priority,
            "non_evidentiary": True,
            "created_step": request_step_index,
        }
        expected_desire["desire_hash"] = digest(expected_desire)
        if desire != expected_desire:
            raise ThinkerContractError("agenda source: desire is not a mechanical confusion projection")
        item = {
            "agenda_item_id": f"agenda-{priority:02d}-{confusion_id}",
            "source_desire_id": desire_id,
            "kind": confusion["kind"],
            "query_key": confusion["query_key"],
            "subject_entity_id": confusion["subject_entity_id"],
            "relation_id": confusion["relation_id"],
            "unknown_slot": "object",
            "priority": priority,
            "non_evidentiary": True,
        }
        items.append(item)
    agenda = {
        "schema_version": SCHEMA_VERSION,
        "agenda_id": f"agenda-{trace_hash[:16]}",
        "world_id": trace["scope"]["world_id"],
        "skin_id": trace["scope"]["skin_id"],
        "life_id": trace["scope"]["life_id"],
        "checkpoint_id": trace["checkpoint_id"],
        "checkpoint_hash": trace["checkpoint_hash"],
        "source_checkpoint_hash": trace["source_checkpoint_hash"],
        "round_index": trace["round_index"],
        "thinker_trace_hash": trace_hash,
        "reset_policy": RESET_POLICY,
        "items": items,
        "non_evidentiary": True,
    }
    agenda["agenda_hash"] = digest(agenda)
    validate_agenda(agenda)
    return agenda


def validate_agenda(agenda: Mapping[str, Any]) -> None:
    """Validate the deliberately narrow cognitive-feedback schema."""

    if not isinstance(agenda, Mapping):
        raise ThinkerContractError("agenda: must be an object")
    _require_exact_keys(
        agenda,
        {
            "schema_version", "agenda_id", "world_id", "skin_id", "life_id",
            "checkpoint_id", "checkpoint_hash", "source_checkpoint_hash", "round_index",
            "thinker_trace_hash", "reset_policy", "items", "non_evidentiary", "agenda_hash",
        },
        "agenda",
    )
    if agenda["schema_version"] != SCHEMA_VERSION or agenda["non_evidentiary"] is not True:
        raise ThinkerContractError("agenda: wrong schema or evidentiary flag")
    if agenda["reset_policy"] != RESET_POLICY:
        raise ThinkerContractError("agenda: v1 requires a fresh post-dream replan")
    if not isinstance(agenda["round_index"], int) or isinstance(agenda["round_index"], bool) \
            or agenda["round_index"] < 0:
        raise ThinkerContractError("agenda.round_index: non-negative int required")
    for field in ("agenda_id", "world_id", "skin_id", "life_id", "checkpoint_id"):
        _require_nonempty(agenda[field], f"agenda.{field}")
    for field in (
        "checkpoint_hash", "source_checkpoint_hash", "thinker_trace_hash", "agenda_hash",
    ):
        if not isinstance(agenda[field], str) or not _SHA256.fullmatch(agenda[field]):
            raise ThinkerContractError(f"agenda.{field}: sha256 required")
    if not isinstance(agenda["items"], list) or len(agenda["items"]) != 1:
        raise ThinkerContractError("agenda.items: exactly one item required")
    item_fields = {
        "agenda_item_id", "source_desire_id", "kind", "query_key",
        "subject_entity_id", "relation_id", "unknown_slot", "priority", "non_evidentiary",
    }
    for index, item in enumerate(agenda["items"]):
        if not isinstance(item, Mapping):
            raise ThinkerContractError(f"agenda.items[{index}]: object required")
        _require_exact_keys(item, item_fields, f"agenda.items[{index}]")
        if item["kind"] not in {"MISSING_DEPENDENCY", "CONFLICT"}:
            raise ThinkerContractError(f"agenda.items[{index}].kind: invalid")
        if item["unknown_slot"] != "object" or item["non_evidentiary"] is not True:
            raise ThinkerContractError(f"agenda.items[{index}]: invalid slot/evidence flag")
        for field in (
            "agenda_item_id", "source_desire_id", "query_key",
            "subject_entity_id", "relation_id",
        ):
            _require_handle(item[field], f"agenda.items[{index}].{field}")
        if not isinstance(item["priority"], int) or item["priority"] < 1:
            raise ThinkerContractError(f"agenda.items[{index}].priority: positive int required")
    material = {key: deepcopy(value) for key, value in agenda.items() if key != "agenda_hash"}
    if agenda["agenda_hash"] != digest(material):
        raise ThinkerContractError("agenda.agenda_hash: mismatch")


def checkpoint_from_cyclic_trace(
    trace: Mapping[str, Any],
    *,
    round_index: int,
    relation_specs: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Compile one validated cyclic checkpoint into the exact thinker snapshot.

    ``relation_specs`` is an explicit bridge declaration with exact fields
    ``relation_id``, ``label``, ``source_relation``, ``cardinality``, and
    ``max_results``.  No relation vocabulary is inferred from a goal or policy.
    """

    from .cyclic_organism_contract import assert_valid_trace, sha256_json

    assert_valid_trace(trace)
    if not isinstance(round_index, int) or isinstance(round_index, bool) or round_index < 0:
        raise ThinkerContractError("bridge.round_index: non-negative integer required")
    checkpoints = [
        item for item in trace["checkpoints"] if item["round_index"] == round_index
    ]
    if len(checkpoints) != 1:
        raise ThinkerContractError("bridge: exactly one cyclic checkpoint required for round")
    checkpoint = checkpoints[0]
    included = set(checkpoint["included_semantic_ids"])

    bridge_relations: dict[str, dict[str, Any]] = {}
    frozen_relation_rows: list[dict[str, Any]] = []
    for index, row in enumerate(relation_specs):
        path = f"bridge.relation_specs[{index}]"
        if not isinstance(row, Mapping):
            raise ThinkerContractError(f"{path}: object required")
        _require_exact_keys(
            row,
            {"relation_id", "label", "source_relation", "cardinality", "max_results"},
            path,
        )
        source_relation = normalize(_require_nonempty(row["source_relation"], f"{path}.source_relation"))
        if source_relation in bridge_relations:
            raise ThinkerContractError(f"{path}.source_relation: duplicate")
        bridge_relations[source_relation] = dict(row)
        frozen_relation_rows.append({
            "relation_id": row["relation_id"],
            "label": row["label"],
            "cardinality": row["cardinality"],
            "max_results": row["max_results"],
        })

    concepts = {
        item["concept_id"]: item for item in trace["concepts"]
        if item["concept_id"] in included
    }
    entities = [
        {"entity_id": concept_id, "label": item["display_label"]}
        for concept_id, item in sorted(concepts.items())
    ]
    status: dict[str, str] = {}
    for event in trace["epistemic_events"]:
        if event["round_index"] <= round_index:
            status[event["subject_id"]] = event["new_status"]
    derivations = {item["derivation_id"]: item for item in trace["derivations"]}
    live_edges = [
        item for item in trace["semantic_edges"] if item["edge_id"] in included
    ]
    edge_ids = {item["edge_id"] for item in live_edges}
    linked: dict[str, list[str]] = {edge_id: [] for edge_id in edge_ids}
    for left in live_edges:
        for right in live_edges:
            if left["edge_id"] != right["edge_id"] and \
                    left["target_concept_id"] == right["source_concept_id"]:
                linked[left["edge_id"]].append(right["edge_id"])
    items: list[dict[str, Any]] = []
    for edge in sorted(live_edges, key=lambda item: item["edge_id"]):
        source_relation = normalize(edge["relation"])
        declaration = bridge_relations.get(source_relation)
        if declaration is None:
            raise ThinkerContractError(
                f"bridge: cyclic relation {edge['relation']!r} lacks a declaration"
            )
        derivation = derivations[edge["derivation_id"]]
        source_ids = [premise["id"] for premise in derivation["premise_refs"]]
        items.append(make_semantic_item(
            edge["edge_id"],
            kind="semantic_edge",
            subject_entity_id=edge["source_concept_id"],
            relation_id=declaration["relation_id"],
            object_entity_id=edge["target_concept_id"],
            content=(
                f"{concepts[edge['source_concept_id']]['display_label']} "
                f"{declaration['label']} "
                f"{concepts[edge['target_concept_id']]['display_label']}"
            ),
            status=status.get(edge["edge_id"], "provisional"),
            linked_semantic_ids=sorted(linked[edge["edge_id"]]),
            source_ids=source_ids,
        ))
    return make_checkpoint(
        checkpoint["checkpoint_id"],
        world_id=trace["world_id"],
        skin_id=trace["skin_id"],
        life_id=trace["life_id"],
        entities=entities,
        relation_specs=frozen_relation_rows,
        items=items,
        round_index=round_index,
        source_checkpoint_hash=sha256_json(checkpoint),
    )


def validate_agenda_against_cyclic_trace(
    agenda: Mapping[str, Any], trace: Mapping[str, Any], *, round_index: int,
) -> None:
    """Reject stale/cross-scope thinker feedback before cyclic scheduling."""

    from .cyclic_organism_contract import assert_valid_trace, sha256_json

    validate_agenda(agenda)
    assert_valid_trace(trace)
    checkpoints = [
        item for item in trace["checkpoints"] if item["round_index"] == round_index
    ]
    if len(checkpoints) != 1:
        raise ThinkerContractError("agenda bridge: missing cyclic checkpoint round")
    checkpoint = checkpoints[0]
    for field in ("world_id", "skin_id", "life_id"):
        if agenda[field] != trace[field]:
            raise ThinkerContractError("agenda bridge: cross-scope feedback")
    if agenda["round_index"] != round_index:
        raise ThinkerContractError("agenda bridge: stale thinker round")
    if agenda["checkpoint_id"] != checkpoint["checkpoint_id"] or \
            agenda["source_checkpoint_hash"] != sha256_json(checkpoint):
        raise ThinkerContractError("agenda bridge: stale or substituted checkpoint")
