"""Pure scientific contract for the v0.3-R recurrence-closure calibration.

This module deliberately contains no provider, GPU, oracle-admission, final-goal,
or mutable-memory code.  It is the executable boundary shared by the local
preflight, the provider runner, and the two independent artifact verifiers.
All model-dependent inputs are passed in explicitly and all arithmetic is exact.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from functools import cmp_to_key
import hashlib
import json
import math
import re
from typing import Any, Callable, Iterable, Mapping, Sequence


CHANGE_ID = "chg_20260901_v03r_recurrence_closure_dev_v2e"
MODEL_ID = "Qwen/Qwen2.5-32B-Instruct"
MODEL_REVISION = "5ede1c97bbab6ce5cda5812749b4c0bdf79b18dd"
MODEL_DTYPE = "bf16"
ARMS = ("no_feedback", "own_selector", "matched_distractor")
WITNESS_KINDS = (
    "SOURCE_ENDPOINT_MEMORY",
    "TARGET_ENDPOINT_MEMORY",
    "ROUTE_PUBLIC_RECORD",
    "EFFECT_PUBLIC_RECORD",
)
BALANCE_STATES = (
    "EXACT_MEASURED_BALANCE",
    "NEAR_MEASURED_BALANCE",
    "OUT_OF_MEASURED_BALANCE",
)
SHARED_DREAM_CALLS = 514
MAX_THINK_CALLS = 72
BRANCH_CALLS_PER_DEFINED_LIFE = 48
EXPLORATORY_CALLS_PER_DEFINED_LIFE = 17
SELECTOR_TRACES_PER_DEFINED_LIFE = 48
MEMORY1_PER_DEFINED_LIFE = 3
BRANCH_ROUNDS = 16
NEIGHBOR_K = 6
RAW_CONNECTOR_SENTINEL = "V2E_RAW_CONNECTOR_SENTINEL_7Q9X"
RELATION = "causal_join"
MISSING = "MISSING"
PROVISIONAL = "provisional"

DREAM_CONFIG = {
    "temperature": "0.2", "top_p": "0.95", "max_new_tokens": 256,
}
THINK_CONFIG = {
    "temperature": "0", "top_p": "1", "max_new_tokens": 128,
}

_HASH = re.compile(r"[0-9a-f]{64}")
_ALIAS = re.compile(r"(?:E|M|X|C)[0-9]+|N0")
_CITATION = re.compile(r"(?:E|M)[0-9]+")
_SAFE_TEXT = re.compile(r"[ -!#-\[\]-~]+")


class V03RContractError(ValueError):
    """A frozen scientific-contract condition was violated."""


def canonical_json_bytes(value: Any) -> bytes:
    """Content-addressable ASCII JSON used for internal artifacts."""
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def ordered_json_bytes(value: Mapping[str, Any]) -> bytes:
    """ASCII JSON preserving insertion order (used at the model boundary)."""
    return json.dumps(
        value, sort_keys=False, separators=(",", ":"), ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def sha256_bytes(value: bytes) -> str:
    if not isinstance(value, bytes):
        raise V03RContractError("hash input must be exact bytes")
    return hashlib.sha256(value).hexdigest()


def sha256_json(value: Any) -> str:
    return sha256_bytes(canonical_json_bytes(value))


def _exact_keys(value: Mapping[str, Any], expected: Sequence[str], path: str) -> None:
    if list(value) != list(expected):
        raise V03RContractError(
            f"{path} field order/keys differ: expected={list(expected)!r}, "
            f"actual={list(value)!r}"
        )


def _strict_json_object(raw: bytes) -> Mapping[str, Any]:
    if not isinstance(raw, bytes) or not raw or raw.startswith(b"\xef\xbb\xbf"):
        raise V03RContractError("response must be non-empty exact bytes without BOM")
    try:
        text = raw.decode("ascii")
    except UnicodeDecodeError as exc:
        raise V03RContractError("response must be ASCII") from exc
    if text != text.strip() or text.endswith("\n"):
        raise V03RContractError("response may not have surrounding whitespace")
    seen_duplicate = False

    def pairs(rows: list[tuple[str, Any]]) -> dict[str, Any]:
        nonlocal seen_duplicate
        result: dict[str, Any] = {}
        for key, value in rows:
            if key in result:
                seen_duplicate = True
            result[key] = value
        return result

    def reject_constant(value: str) -> None:
        raise V03RContractError(f"nonfinite JSON constant {value!r}")

    try:
        value = json.loads(text, object_pairs_hook=pairs, parse_constant=reject_constant)
    except (json.JSONDecodeError, UnicodeError) as exc:
        raise V03RContractError("response is not one strict JSON object") from exc
    if seen_duplicate or not isinstance(value, Mapping):
        raise V03RContractError("response must be one object with unique keys")
    if raw != ordered_json_bytes(value):
        raise V03RContractError("response is not canonical ordered ASCII JSON")
    return value


def _safe_text(value: Any, path: str, maximum: int) -> str:
    if not isinstance(value, str) or not (1 <= len(value.encode("ascii", "ignore")) <= maximum):
        raise V03RContractError(f"{path} must be 1..{maximum} ASCII bytes")
    try:
        encoded = value.encode("ascii")
    except UnicodeEncodeError as exc:
        raise V03RContractError(f"{path} must be ASCII") from exc
    if any(byte < 0x20 or byte > 0x7E or byte in (0x22, 0x5C) for byte in encoded):
        raise V03RContractError(f"{path} contains a forbidden free-text byte")
    return value


def _alias(value: Any, path: str, prefixes: tuple[str, ...]) -> str:
    if not isinstance(value, str) or _ALIAS.fullmatch(value) is None \
            or not value.startswith(prefixes):
        raise V03RContractError(f"{path} is not a permitted local alias")
    return value


def _citations(value: Any, visible_order: Sequence[str]) -> tuple[str, ...]:
    if not isinstance(value, list) or not 1 <= len(value) <= 7:
        raise V03RContractError("citations must contain 1..7 handles")
    if any(not isinstance(x, str) or _CITATION.fullmatch(x) is None for x in value):
        raise V03RContractError("citations must be E*/M* handles")
    if len(value) != len(set(value)):
        raise V03RContractError("citations must be distinct")
    positions = {alias: i for i, alias in enumerate(visible_order)}
    if any(alias not in positions for alias in value):
        raise V03RContractError("citation is outside the visible call")
    if [positions[x] for x in value] != sorted(positions[x] for x in value):
        raise V03RContractError("citations must follow visible item order")
    return tuple(value)


@dataclass(frozen=True)
class QueryCoordinate:
    source_entity_id: str
    relation_label: str
    target_entity_id: str

    def validate(self) -> None:
        if self.relation_label != RELATION:
            raise V03RContractError("query relation must be causal_join")
        if not self.source_entity_id.startswith("entity:source:"):
            raise V03RContractError("query source is not a typed source endpoint")
        if not self.target_entity_id.startswith("entity:target:"):
            raise V03RContractError("query target is not a typed target endpoint")
        for value in (self.source_entity_id, self.target_entity_id):
            try:
                raw = value.encode("ascii")
            except UnicodeEncodeError as exc:
                raise V03RContractError("query endpoints must be ASCII") from exc
            if not raw or b"\n" in raw:
                raise V03RContractError("query endpoint is empty or contains newline")

    def exact_bytes(self) -> bytes:
        self.validate()
        return (
            self.source_entity_id + "\n" + RELATION + "\n" + self.target_entity_id
        ).encode("ascii")

    @classmethod
    def own_from_probe(cls, probe: Mapping[str, Any]) -> "QueryCoordinate":
        required = {
            "probe_id", "source_entity_id", "target_entity_id", "question",
            "matched_distractor_source_entity_id",
            "matched_distractor_target_entity_id",
        }
        if set(probe) != required:
            raise V03RContractError("public operational probe has the wrong schema")
        result = cls(str(probe["source_entity_id"]), RELATION, str(probe["target_entity_id"]))
        result.validate()
        return result

    @classmethod
    def distractor_from_probe(cls, probe: Mapping[str, Any]) -> "QueryCoordinate":
        own = cls.own_from_probe(probe)
        result = cls(
            str(probe["matched_distractor_source_entity_id"]), RELATION,
            str(probe["matched_distractor_target_entity_id"]),
        )
        result.validate()
        if result == own:
            raise V03RContractError("fixed distractor equals own query")
        return result


@dataclass(frozen=True)
class PublicRecord:
    public_id: str
    sequence_index: int
    kind: str
    canonical_text: str
    structured: Mapping[str, Any]

    def validate(self) -> None:
        if not self.public_id or isinstance(self.sequence_index, bool) \
                or not isinstance(self.sequence_index, int) or self.sequence_index < 0:
            raise V03RContractError("invalid public record identity/order")
        if not self.kind or not isinstance(self.structured, Mapping):
            raise V03RContractError("invalid typed public record")
        self.canonical_text.encode("ascii")

    @property
    def semantic_sha256(self) -> str:
        return sha256_bytes(self.canonical_bytes())

    def canonical_bytes(self) -> bytes:
        self.validate()
        return canonical_json_bytes({
            "public_id": self.public_id, "sequence_index": self.sequence_index,
            "kind": self.kind, "canonical_text": self.canonical_text,
            "structured": dict(self.structured),
        })


@dataclass(frozen=True)
class MemoryRow:
    creation_slot: int
    semantic_sha256: str
    kind: str
    canonical_text: str
    citations: tuple[str, ...] = ()
    entity_id: str | None = None
    source_entity_id: str | None = None
    relation_label: str | None = None
    target_entity_id: str | None = None
    connector_id: str | None = None
    polarity: str = "UNKNOWN"
    status: str = PROVISIONAL

    def validate(self) -> None:
        if isinstance(self.creation_slot, bool) or not isinstance(self.creation_slot, int) \
                or self.creation_slot < 0 or _HASH.fullmatch(self.semantic_sha256) is None:
            raise V03RContractError("invalid memory creation identity")
        if self.kind not in {"concept", "semantic_edge"}:
            raise V03RContractError("memory kind must be concept or semantic_edge")
        if self.status != PROVISIONAL:
            raise V03RContractError("all cognition memory must remain provisional")
        if self.polarity not in {"POSITIVE", "NEGATIVE", "UNKNOWN"}:
            raise V03RContractError("invalid memory polarity")
        self.canonical_text.encode("ascii")
        if len(self.citations) != len(set(self.citations)):
            raise V03RContractError("memory citations must be distinct")

    def canonical_bytes(self) -> bytes:
        self.validate()
        return canonical_json_bytes({
            "creation_slot": self.creation_slot,
            "semantic_sha256": self.semantic_sha256,
            "kind": self.kind,
            "canonical_text": self.canonical_text,
            "citations": list(self.citations),
            "entity_id": self.entity_id,
            "source_entity_id": self.source_entity_id,
            "relation_label": self.relation_label,
            "target_entity_id": self.target_entity_id,
            "connector_id": self.connector_id,
            "polarity": self.polarity,
            "status": self.status,
        })


@dataclass(frozen=True)
class CandidateView:
    trigger: PublicRecord
    neighborhood: tuple[MemoryRow, ...]
    witness_kinds: frozenset[str]
    candidate_structural_opportunity: bool
    canonical_view_sha256: str
    canonical_view_bytes: bytes = field(repr=False)
    rank_components: tuple[Any, ...] = ()
    complete_rank: int = 0
    tie_disposition: str = "unique"

    @property
    def public_citation_count(self) -> int:
        valid = {self.trigger.semantic_sha256, self.trigger.public_id}
        return sum(bool(set(row.citations) & valid) for row in self.neighborhood)


@dataclass(frozen=True)
class SelectorManifest:
    selector_kind: str
    query: QueryCoordinate | None
    complete: tuple[CandidateView, ...]
    selected: tuple[CandidateView, ...]
    selector_code_sha256: str

    def validate(self) -> None:
        if self.selector_kind not in ARMS:
            raise V03RContractError("unknown selector kind")
        if len({item.trigger.public_id for item in self.complete}) != len(self.complete):
            raise V03RContractError("candidate universe contains duplicate triggers")
        if len(self.selected) != BRANCH_ROUNDS:
            raise V03RContractError("defined selector must select exactly sixteen views")
        if self.selected != self.complete[:BRANCH_ROUNDS]:
            raise V03RContractError("selected views are not the first sixteen complete ranks")


@dataclass(frozen=True)
class ParsedDream:
    op: str
    fields: Mapping[str, Any]
    raw: bytes
    raw_sha256: str
    provisional: bool = True


@dataclass(frozen=True)
class ParsedThink:
    op: str
    fields: Mapping[str, Any]
    raw: bytes
    raw_sha256: str


def append_provisional_dream(
    parsed: ParsedDream, *, creation_slot: int,
    raw_to_alias: Mapping[str, str], visible_memory: Sequence[MemoryRow],
) -> MemoryRow | None:
    """Append one parsed proposal without admission, support, or mutation.

    ``raw_to_alias`` is the exact sidecar returned by :func:`build_provider_view`.
    REINFORCE and SUPERSEDE are represented as new rows; the referenced row is
    never changed or deleted.
    """
    if not parsed.provisional:
        raise V03RContractError("DREAM proposal lost provisional status")
    if parsed.op == "PASS":
        return None
    alias_to_raw = {alias: raw for raw, alias in raw_to_alias.items()}
    if len(alias_to_raw) != len(raw_to_alias):
        raise V03RContractError("call alias sidecar is not bijective")
    by_hash = {row.semantic_sha256: row for row in visible_memory}
    fields = parsed.fields
    citations = tuple(alias_to_raw[x] for x in fields["citations"])
    base_payload: dict[str, Any] = {
        "creation_slot": creation_slot, "source_operation_sha256": parsed.raw_sha256,
        "op": parsed.op, "canonical_text": fields["canonical_text"],
        "citations": citations, "status": PROVISIONAL,
    }
    if parsed.op == "CREATE_CONCEPT":
        entity = alias_to_raw[fields["entity_alias"]]
        kind = "concept"
        source = relation = target = connector = None
        polarity = "UNKNOWN"
    elif parsed.op == "CREATE_EDGE":
        entity = None
        kind = "semantic_edge"
        source = alias_to_raw[fields["left_alias"]]
        relation = fields["relation_label"]
        target = alias_to_raw[fields["right_alias"]]
        connector = alias_to_raw[fields["connector_alias"]]
        polarity = fields["polarity"]
    elif parsed.op == "REINFORCE":
        referenced_hash = alias_to_raw[fields["memory_alias"]]
        referenced = by_hash.get(referenced_hash)
        if referenced is None:
            raise V03RContractError("REINFORCE references nonvisible memory")
        entity, kind = referenced.entity_id, referenced.kind
        source, relation = referenced.source_entity_id, referenced.relation_label
        target, connector = referenced.target_entity_id, referenced.connector_id
        polarity = referenced.polarity
        base_payload["reinforces"] = referenced_hash
    else:
        referenced_hash = alias_to_raw[fields["memory_alias"]]
        if referenced_hash not in by_hash:
            raise V03RContractError("SUPERSEDE references nonvisible memory")
        kind = "concept" if fields["replacement_kind"] == "CONCEPT" else "semantic_edge"
        left = alias_to_raw[fields["left_or_entity_alias"]]
        if kind == "concept":
            entity, source, relation, target, connector, polarity = (
                left, None, None, None, None, "UNKNOWN",
            )
        else:
            entity, source = None, left
            relation = fields["relation_label"]
            target = alias_to_raw[fields["right_alias"]]
            connector = alias_to_raw[fields["connector_alias"]]
            polarity = fields["polarity"]
        base_payload["supersedes"] = referenced_hash
    base_payload.update({
        "kind": kind, "entity_id": entity, "source_entity_id": source,
        "relation_label": relation, "target_entity_id": target,
        "connector_id": connector, "polarity": polarity,
    })
    semantic = sha256_json(base_payload)
    row = MemoryRow(
        creation_slot=creation_slot, semantic_sha256=semantic, kind=kind,
        canonical_text=str(fields["canonical_text"]), citations=citations,
        entity_id=entity, source_entity_id=source, relation_label=relation,
        target_entity_id=target, connector_id=connector, polarity=polarity,
        status=PROVISIONAL,
    )
    row.validate()
    return row


def parse_dream_response(
    raw: bytes, *, visible_alias_order: Sequence[str],
    token_ids: Sequence[int] | None = None,
) -> ParsedDream:
    value = _strict_json_object(raw)
    op = value.get("op")
    fields_by_op = {
        "PASS": ("op", "reason_code"),
        "CREATE_CONCEPT": (
            "op", "new_alias", "entity_alias", "concept_type",
            "canonical_text", "citations",
        ),
        "CREATE_EDGE": (
            "op", "left_alias", "relation_label", "right_alias",
            "connector_alias", "polarity", "canonical_text", "citations",
        ),
        "REINFORCE": ("op", "memory_alias", "canonical_text", "citations"),
        "SUPERSEDE": (
            "op", "memory_alias", "replacement_kind", "left_or_entity_alias",
            "relation_label", "right_alias", "connector_alias", "polarity",
            "canonical_text", "citations",
        ),
    }
    if op not in fields_by_op:
        raise V03RContractError("unknown DREAM operation")
    _exact_keys(value, fields_by_op[op], "DREAM")
    if token_ids is not None and len(tuple(token_ids)) > 256:
        raise V03RContractError("DREAM operation exceeds 256 tokenizer IDs")
    if op == "PASS":
        if value["reason_code"] != "NO_BOUNDED_UPDATE":
            raise V03RContractError("PASS has the wrong reason code")
    else:
        _safe_text(value["canonical_text"], "canonical_text", 192)
        citations = _citations(value["citations"], visible_alias_order)
        if op == "CREATE_CONCEPT":
            if value["new_alias"] != "N0":
                raise V03RContractError("new concept alias must be N0")
            _alias(value["entity_alias"], "entity_alias", ("X",))
            _safe_text(value["concept_type"], "concept_type", 64)
        elif op == "CREATE_EDGE":
            _alias(value["left_alias"], "left_alias", ("X", "M", "N"))
            _safe_text(value["relation_label"], "relation_label", 64)
            _alias(value["right_alias"], "right_alias", ("X", "M", "N"))
            _alias(value["connector_alias"], "connector_alias", ("C",))
        elif op == "REINFORCE":
            _alias(value["memory_alias"], "memory_alias", ("M",))
        else:
            _alias(value["memory_alias"], "memory_alias", ("M",))
            if value["replacement_kind"] not in {"CONCEPT", "EDGE"}:
                raise V03RContractError("invalid SUPERSEDE replacement kind")
            _alias(value["left_or_entity_alias"], "left_or_entity_alias", ("X", "M", "N"))
            if value["relation_label"] is not None:
                _safe_text(value["relation_label"], "relation_label", 64)
            if value["right_alias"] is not None:
                _alias(value["right_alias"], "right_alias", ("X", "M", "N"))
            if value["connector_alias"] is not None:
                _alias(value["connector_alias"], "connector_alias", ("C",))
        if op in {"CREATE_EDGE", "SUPERSEDE"} and value["polarity"] not in {
            "POSITIVE", "NEGATIVE", "UNKNOWN", None,
        }:
            raise V03RContractError("invalid DREAM polarity")
        value = dict(value)
        value["citations"] = list(citations)
    return ParsedDream(str(op), dict(value), raw, sha256_bytes(raw), True)


THINK_FIELDS: Mapping[str, tuple[str, ...]] = {
    "FORM_SUBGOAL": ("op", "subgoal"),
    "QUERY": ("op", "source_alias", "relation_label", "target_alias"),
    "FOLLOW": ("op", "memory_alias"),
    "HYPOTHESIZE": ("op", "hypothesis"),
    "PREDICT": ("op", "prediction"),
    "REVISE": ("op", "revision"),
    "BACKTRACK": ("op", "reason_code"),
    "REQUEST_DREAM": ("op", "q"),
    "DEFER": ("op", "reason_code"),
}


def parse_think_response(raw: bytes, *, token_ids: Sequence[int] | None = None) -> ParsedThink:
    value = _strict_json_object(raw)
    op = value.get("op")
    if op not in THINK_FIELDS:
        raise V03RContractError("unknown THINK operation")
    _exact_keys(value, THINK_FIELDS[str(op)], "THINK")
    if token_ids is not None and len(tuple(token_ids)) > 128:
        raise V03RContractError("THINK operation exceeds 128 tokenizer IDs")
    if op == "REQUEST_DREAM":
        q = value["q"]
        if not isinstance(q, Mapping):
            raise V03RContractError("REQUEST_DREAM.q must be one object")
        _exact_keys(q, ("source_entity_id", "relation_label", "target_entity_id"), "THINK.q")
        QueryCoordinate(str(q["source_entity_id"]), str(q["relation_label"]), str(q["target_entity_id"])).validate()
    elif op == "QUERY":
        _alias(value["source_alias"], "source_alias", ("X", "M"))
        _safe_text(value["relation_label"], "relation_label", 64)
        _alias(value["target_alias"], "target_alias", ("X", "M"))
    elif op == "FOLLOW":
        _alias(value["memory_alias"], "memory_alias", ("M",))
    else:
        field_name = THINK_FIELDS[str(op)][1]
        _safe_text(value[field_name], field_name, 192)
    return ParsedThink(str(op), dict(value), raw, sha256_bytes(raw))


def terminal_primary(
    operations: Sequence[ParsedThink], own: QueryCoordinate, *, exhausted: bool = False,
) -> tuple[str, QueryCoordinate | None, str]:
    """Project one terminal-justified THINK prefix into defined/undefined state."""
    if len(operations) > 12:
        raise V03RContractError("THINK_0 exceeds twelve real operations")
    requests = [item for item in operations if item.op == "REQUEST_DREAM"]
    defers = [item for item in operations if item.op == "DEFER"]
    if requests:
        if operations[-1].op != "REQUEST_DREAM" or len(requests) != 1 or defers:
            return "PRIMARY_UNDEFINED", None, "NONSOLE_REQUEST_DREAM"
        q = QueryCoordinate(**requests[0].fields["q"])
        if q != own:
            return "PRIMARY_UNDEFINED", None, "WRONG_REQUEST_DREAM_Q"
        return "DEFINED_CANDIDATE", q, "VALID_REQUEST_DREAM"
    if defers and operations[-1].op == "DEFER":
        return "PRIMARY_UNDEFINED", None, "DEFER"
    if exhausted or len(operations) == 12:
        return "PRIMARY_UNDEFINED", None, "EXHAUSTED"
    return "PRIMARY_UNDEFINED", None, "FAILURE_OR_MALFORMED"


def build_six_lives() -> tuple[dict[str, Any], ...]:
    """Construct only the six frozen aligned development packets."""
    from lands.model import WorldConfig
    from lands.v03r import CounterfactualConfluenceV03R

    rows = []
    for seed in (0, 1, 2):
        for bit in (0, 1):
            world = CounterfactualConfluenceV03R(WorldConfig(seed=seed), latent_bit=bit)
            if world.split != "development":
                raise V03RContractError("frozen six-life set is no longer development-only")
            life_id = f"seed{seed}-bit{bit}"
            rows.append({
                "life_id": life_id, "seed": seed, "collision_twin": bit,
                "skin": "aligned", "public_export": world.precheckpoint_export("aligned"),
                "schedule": prefix_schedule(seed, bit, world.schedule_manifest()),
            })
    return tuple(rows)


def prefix_schedule(seed: int, collision_twin: int, manifest: Mapping[str, Any]) -> dict[str, Any]:
    if seed not in (0, 1, 2) or collision_twin not in (0, 1):
        raise V03RContractError("life is outside the frozen six-life calibration")
    expected = (49, 24) if seed == 1 else (46, 22)
    if (manifest.get("wake_calls"), manifest.get("periodic_reactivate_calls")) != expected:
        raise V03RContractError("v0.3-R schedule drift")
    return {
        "life_id": f"seed{seed}-bit{collision_twin}",
        "wake_calls": expected[0], "reactivate_calls": expected[1],
        "target_blind_sleep_calls": 16,
        "shared_calls": expected[0] + expected[1] + 16,
    }


def validate_shared_schedules(rows: Sequence[Mapping[str, Any]]) -> int:
    if len(rows) != 6 or len({row["life_id"] for row in rows}) != 6:
        raise V03RContractError("shared schedule must contain six unique lives")
    total = sum(int(row["shared_calls"]) for row in rows)
    if total != SHARED_DREAM_CALLS:
        raise V03RContractError("shared schedule is not exactly 514 calls")
    return total


def public_records(public_export: Mapping[str, Any]) -> tuple[PublicRecord, ...]:
    episodes = public_export.get("episodes")
    if not isinstance(episodes, list):
        raise V03RContractError("public export lacks episodes")
    rows = []
    for sequence_index, item in enumerate(episodes):
        if not isinstance(item, Mapping) or set(item) != {
            "id", "episode_id", "phase", "kind", "text", "public_record",
        }:
            raise V03RContractError("public episode schema drift")
        rows.append(PublicRecord(
            str(item["id"]), sequence_index, str(item["kind"]), str(item["text"]),
            dict(item["public_record"]),
        ))
    ids = [x.public_id for x in rows]
    if len(ids) != len(set(ids)) or [x.sequence_index for x in rows] != list(range(len(rows))):
        raise V03RContractError("public IDs/order are not unique and contiguous")
    return tuple(rows)


Tokenize = Callable[[bytes], Sequence[int]]


def token_set_jaccard(left: bytes, right: bytes, tokenize: Tokenize) -> Fraction:
    a = set(int(x) for x in tokenize(left))
    b = set(int(x) for x in tokenize(right))
    if not a and not b:
        return Fraction(1, 1)
    if not a or not b:
        return Fraction(0, 1)
    return Fraction(len(a & b), len(a | b))


def _typed_values(record: PublicRecord | MemoryRow) -> frozenset[str]:
    if isinstance(record, MemoryRow):
        values = {
            x for x in (
                record.entity_id, record.source_entity_id, record.target_entity_id,
            ) if x is not None
        }
        return frozenset(values)
    result: set[str] = set()
    for key, value in record.structured.items():
        if not isinstance(value, str):
            continue
        if key in {"source_id", "land_id"}:
            result.add(f"entity:source:{value}")
        elif key == "target_id":
            result.add(f"entity:target:{value}")
        elif key in {"animal_id", "anchor_id"}:
            result.add(f"entity:animal:{value}")
    return frozenset(result)


def _connector(record: PublicRecord | MemoryRow) -> str | None:
    if isinstance(record, MemoryRow):
        return record.connector_id
    value = record.structured.get("valve_id")
    return str(value) if isinstance(value, str) and value else None


def _polarity(record: PublicRecord | MemoryRow) -> str:
    if isinstance(record, MemoryRow):
        return record.polarity
    effect = record.structured.get("effect")
    return {"CHANGE": "POSITIVE", "STABLE": "NEGATIVE"}.get(str(effect), "UNKNOWN")


def _witnesses(trigger: PublicRecord, memory: Sequence[MemoryRow], q: QueryCoordinate) -> frozenset[str]:
    witnesses: set[str] = set()
    if any(q.source_entity_id in _typed_values(row) for row in memory):
        witnesses.add("SOURCE_ENDPOINT_MEMORY")
    if any(q.target_entity_id in _typed_values(row) for row in memory):
        witnesses.add("TARGET_ENDPOINT_MEMORY")
    if trigger.kind == "valve_route" and q.source_entity_id in _typed_values(trigger):
        witnesses.add("ROUTE_PUBLIC_RECORD")
    if trigger.kind == "intervention_effect" and q.target_entity_id in _typed_values(trigger):
        witnesses.add("EFFECT_PUBLIC_RECORD")
    return frozenset(witnesses)


def _structural_opportunity(
    trigger: PublicRecord, memory: Sequence[MemoryRow], q: QueryCoordinate,
) -> bool:
    items: tuple[PublicRecord | MemoryRow, ...] = (trigger, *memory)
    by_connector: dict[str, dict[str, bool]] = {}
    for item in items:
        connector = _connector(item)
        if connector is None:
            continue
        state = by_connector.setdefault(connector, {
            "source": False, "target": False, "route": False, "effect": False,
        })
        typed = _typed_values(item)
        state["source"] |= q.source_entity_id in typed
        state["target"] |= q.target_entity_id in typed
        if isinstance(item, PublicRecord):
            state["route"] |= item.kind == "valve_route" and q.source_entity_id in typed
            state["effect"] |= item.kind == "intervention_effect" and q.target_entity_id in typed \
                and _polarity(item) in {"POSITIVE", "NEGATIVE"}
    return any(all(state.values()) for state in by_connector.values())


def _view_bytes(trigger: PublicRecord, memory: Sequence[MemoryRow]) -> bytes:
    return canonical_json_bytes({
        "trigger": json.loads(trigger.canonical_bytes()),
        "memory": [json.loads(row.canonical_bytes()) for row in memory],
    })


def _cmp_components(left: Sequence[Any], right: Sequence[Any], *, descending: bool = True) -> int:
    for a, b in zip(left, right):
        if a == b:
            continue
        less = a < b
        if descending:
            return 1 if less else -1
        return -1 if less else 1
    return 0


def _ranked(rows: Sequence[tuple[tuple[Any, ...], tuple[Any, ...], Any]]) -> list[Any]:
    def compare(a: tuple[tuple[Any, ...], tuple[Any, ...], Any], b: tuple[tuple[Any, ...], tuple[Any, ...], Any]) -> int:
        result = _cmp_components(a[0], b[0], descending=True)
        return result or _cmp_components(a[1], b[1], descending=False)
    return [row[2] for row in sorted(rows, key=cmp_to_key(compare))]


def _dedup_inputs(public: Sequence[PublicRecord], memory: Sequence[MemoryRow]) -> None:
    public_keys = [(x.sequence_index, x.public_id) for x in public]
    if len(public_keys) != len(set(public_keys)):
        raise V03RContractError("duplicate public candidate identity")
    memory_keys = [(x.creation_slot, x.semantic_sha256) for x in memory]
    if len(memory_keys) != len(set(memory_keys)):
        raise V03RContractError("duplicate memory identity")
    for row in (*public, *memory):
        row.validate()


def build_no_feedback_selector(
    public: Sequence[PublicRecord], memory: Sequence[MemoryRow], tokenize: Tokenize,
) -> SelectorManifest:
    public = tuple(sorted(public, key=lambda x: (x.sequence_index, x.public_id)))
    memory = tuple(sorted(memory, key=lambda x: (x.creation_slot, x.semantic_sha256)))
    _dedup_inputs(public, memory)
    candidates: list[tuple[tuple[Any, ...], tuple[Any, ...], CandidateView]] = []
    for trigger in public:
        neighborhood_rows = []
        for row in memory:
            shared_citations = len(set(row.citations) & {trigger.public_id, trigger.semantic_sha256})
            shared_endpoints = len(_typed_values(row) & _typed_values(trigger))
            lexical = token_set_jaccard(trigger.canonical_bytes(), row.canonical_bytes(), tokenize)
            neighborhood_rows.append((
                (shared_citations, shared_endpoints, lexical, -row.creation_slot),
                (row.semantic_sha256,), row,
            ))
        neighborhood = tuple(_ranked(neighborhood_rows)[:NEIGHBOR_K])
        view_bytes = _view_bytes(trigger, neighborhood)
        citations = sum(
            bool(set(row.citations) & {trigger.public_id, trigger.semantic_sha256})
            for row in neighborhood
        )
        endpoints = len(set().union(*(_typed_values(x) for x in (trigger, *neighborhood))))
        lexical = token_set_jaccard(
            trigger.canonical_bytes(), b"\n".join(x.canonical_bytes() for x in neighborhood),
            tokenize,
        )
        candidate = CandidateView(
            trigger, neighborhood, frozenset(), False, sha256_bytes(view_bytes), view_bytes,
            (citations, endpoints, lexical, -trigger.sequence_index),
        )
        candidates.append((candidate.rank_components, (candidate.canonical_view_sha256,), candidate))
    ordered = _ranked(candidates)
    complete = tuple(
        CandidateView(**{**item.__dict__, "complete_rank": index + 1})
        for index, item in enumerate(ordered)
    )
    if len(complete) < BRANCH_ROUNDS:
        raise V03RContractError("no-feedback universe has fewer than sixteen candidates")
    result = SelectorManifest(
        "no_feedback", None, complete, complete[:BRANCH_ROUNDS],
        sha256_bytes(build_no_feedback_selector.__code__.co_code),
    )
    result.validate()
    return result


def build_q_guided_selector(
    public: Sequence[PublicRecord], memory: Sequence[MemoryRow], q: QueryCoordinate,
    tokenize: Tokenize, *, selector_kind: str,
) -> SelectorManifest:
    if selector_kind not in {"own_selector", "matched_distractor"}:
        raise V03RContractError("q-guided selector kind is invalid")
    q.validate()
    public = tuple(sorted(public, key=lambda x: (x.sequence_index, x.public_id)))
    memory = tuple(sorted(memory, key=lambda x: (x.creation_slot, x.semantic_sha256)))
    _dedup_inputs(public, memory)
    candidates: list[tuple[tuple[Any, ...], tuple[Any, ...], CandidateView]] = []
    for trigger in public:
        neighborhood_rows = []
        for row in memory:
            endpoint_hits = int(q.source_entity_id in _typed_values(row)) + int(q.target_entity_id in _typed_values(row))
            shared_endpoints = len(_typed_values(row) & _typed_values(trigger))
            shared_citations = len(set(row.citations) & {trigger.public_id, trigger.semantic_sha256})
            lexical = token_set_jaccard(q.exact_bytes(), row.canonical_bytes(), tokenize)
            neighborhood_rows.append((
                (endpoint_hits, shared_endpoints, shared_citations, lexical),
                (row.creation_slot, row.semantic_sha256), row,
            ))
        neighborhood = tuple(_ranked(neighborhood_rows)[:NEIGHBOR_K])
        witnesses = _witnesses(trigger, neighborhood, q)
        opportunity = _structural_opportunity(trigger, neighborhood, q)
        view_bytes = _view_bytes(trigger, neighborhood)
        endpoint_hits = sum(
            int(q.source_entity_id in _typed_values(x)) + int(q.target_entity_id in _typed_values(x))
            for x in (trigger, *neighborhood)
        )
        components = (
            int(opportunity), len(witnesses), endpoint_hits,
            token_set_jaccard(q.exact_bytes(), view_bytes, tokenize),
            -trigger.sequence_index,
        )
        candidate = CandidateView(
            trigger, neighborhood, witnesses, opportunity,
            sha256_bytes(view_bytes), view_bytes, components,
        )
        candidates.append((components, (candidate.canonical_view_sha256,), candidate))
    ordered = _ranked(candidates)
    complete = tuple(
        CandidateView(**{**item.__dict__, "complete_rank": index + 1})
        for index, item in enumerate(ordered)
    )
    if len(complete) < BRANCH_ROUNDS:
        raise V03RContractError("q-guided universe has fewer than sixteen candidates")
    result = SelectorManifest(
        selector_kind, q, complete, complete[:BRANCH_ROUNDS],
        sha256_bytes(build_q_guided_selector.__code__.co_code),
    )
    result.validate()
    return result


def selected_union_mechanical_opportunity(manifest: SelectorManifest) -> bool:
    if manifest.query is None:
        return False
    q = manifest.query
    items: list[PublicRecord | MemoryRow] = []
    for view in manifest.selected:
        items.extend((view.trigger, *view.neighborhood))
    by_connector: dict[str, dict[str, bool]] = {}
    for item in items:
        connector = _connector(item)
        if connector is None:
            continue
        state = by_connector.setdefault(connector, {
            "source": False, "target": False, "route": False, "effect": False,
        })
        typed = _typed_values(item)
        state["source"] |= q.source_entity_id in typed
        state["target"] |= q.target_entity_id in typed
        if isinstance(item, PublicRecord):
            state["route"] |= item.kind == "valve_route" and q.source_entity_id in typed
            state["effect"] |= item.kind == "intervention_effect" and q.target_entity_id in typed \
                and _polarity(item) in {"POSITIVE", "NEGATIVE"}
    return any(all(state.values()) for state in by_connector.values())


@dataclass(frozen=True)
class BalanceSide:
    candidate_set_size: int
    witness_counts: Mapping[str, int]
    witness_available: Mapping[str, bool]
    selected_view_count: int
    source_endpoint_frequency: int
    target_endpoint_frequency: int
    route_provider_position: int | str
    effect_provider_position: int | str
    required_item_ranks: Mapping[str, int | str]
    lexical_overlap: Fraction
    selected_union_mechanical_opportunity: bool
    input_sha256: str
    selector_code_sha256: str


@dataclass(frozen=True)
class MeasuredBalance:
    state: str
    own: BalanceSide
    distractor: BalanceSide
    endpoint_frequency_difference: int | str
    provider_position_difference: int | str
    full_selector_rank_difference: int | str
    lexical_difference: Fraction


def _balance_side(manifest: SelectorManifest, tokenize: Tokenize) -> BalanceSide:
    if manifest.query is None:
        raise V03RContractError("balance only accepts q-guided selectors")
    q = manifest.query
    witness_counts = {
        kind: sum(kind in candidate.witness_kinds for candidate in manifest.complete)
        for kind in WITNESS_KINDS
    }
    source_frequency = sum(
        any(q.source_entity_id in _typed_values(x) for x in (view.trigger, *view.neighborhood))
        for view in manifest.complete
    )
    target_frequency = sum(
        any(q.target_entity_id in _typed_values(x) for x in (view.trigger, *view.neighborhood))
        for view in manifest.complete
    )
    def provider_position(kind: str) -> int | str:
        positions = []
        for slot, view in enumerate(manifest.selected):
            if kind == "ROUTE_PUBLIC_RECORD" and kind in view.witness_kinds:
                positions.append(7 * slot + 1)
            elif kind == "EFFECT_PUBLIC_RECORD" and kind in view.witness_kinds:
                positions.append(7 * slot + 1)
            elif kind in {"SOURCE_ENDPOINT_MEMORY", "TARGET_ENDPOINT_MEMORY"}:
                for item_position, row in enumerate(view.neighborhood, start=2):
                    endpoint = q.source_entity_id if kind.startswith("SOURCE") else q.target_entity_id
                    if endpoint in _typed_values(row):
                        positions.append(7 * slot + item_position)
        return min(positions) if positions else MISSING
    ranks = {
        kind: min(
            (candidate.complete_rank for candidate in manifest.complete if kind in candidate.witness_kinds),
            default=MISSING,
        )
        for kind in WITNESS_KINDS
    }
    joined = b"\n".join(x.canonical_view_bytes for x in manifest.selected)
    return BalanceSide(
        len(manifest.complete), witness_counts,
        {kind: count > 0 for kind, count in witness_counts.items()},
        len(manifest.selected), source_frequency, target_frequency,
        provider_position("ROUTE_PUBLIC_RECORD"), provider_position("EFFECT_PUBLIC_RECORD"),
        ranks, token_set_jaccard(q.exact_bytes(), joined, tokenize),
        selected_union_mechanical_opportunity(manifest),
        sha256_bytes(joined), manifest.selector_code_sha256,
    )


def compute_measured_balance(
    own_manifest: SelectorManifest, distractor_manifest: SelectorManifest,
    tokenize: Tokenize,
) -> MeasuredBalance:
    if own_manifest.selector_kind != "own_selector" \
            or distractor_manifest.selector_kind != "matched_distractor":
        raise V03RContractError("balance requires own and fixed-distractor manifests")
    own = _balance_side(own_manifest, tokenize)
    dist = _balance_side(distractor_manifest, tokenize)
    equality = (
        own.candidate_set_size == dist.candidate_set_size
        and own.witness_counts == dist.witness_counts
        and own.witness_available == dist.witness_available
        and own.selected_view_count == dist.selected_view_count
        and own.selected_union_mechanical_opportunity == dist.selected_union_mechanical_opportunity
    )
    required = [
        own.route_provider_position, own.effect_provider_position,
        dist.route_provider_position, dist.effect_provider_position,
        *own.required_item_ranks.values(), *dist.required_item_ranks.values(),
    ]
    missing = MISSING in required
    endpoint = max(
        abs(own.source_endpoint_frequency - dist.source_endpoint_frequency),
        abs(own.target_endpoint_frequency - dist.target_endpoint_frequency),
    )
    provider: int | str = MISSING if missing else max(
        abs(int(own.route_provider_position) - int(dist.route_provider_position)),
        abs(int(own.effect_provider_position) - int(dist.effect_provider_position)),
    )
    ranks: int | str = MISSING if missing else max(
        abs(int(own.required_item_ranks[kind]) - int(dist.required_item_ranks[kind]))
        for kind in WITNESS_KINDS
    )
    lexical = abs(own.lexical_overlap - dist.lexical_overlap)
    if not missing and equality and endpoint == provider == ranks == 0 and lexical == 0:
        state = "EXACT_MEASURED_BALANCE"
    elif not missing and equality and endpoint <= 1 and int(provider) <= 1 \
            and int(ranks) <= 1 and lexical <= Fraction(1, 10):
        state = "NEAR_MEASURED_BALANCE"
    else:
        state = "OUT_OF_MEASURED_BALANCE"
    return MeasuredBalance(state, own, dist, endpoint, provider, ranks, lexical)


def alias_map(
    namespace: str, object_hashes: Iterable[str], *, view_sha256: str,
    stage: str, logical_round: int,
) -> dict[str, str]:
    if namespace not in {"E", "M", "X", "C"} or _HASH.fullmatch(view_sha256) is None:
        raise V03RContractError("invalid alias derivation input")
    hashes = tuple(object_hashes)
    if len(hashes) != len(set(hashes)) or any(_HASH.fullmatch(x) is None for x in hashes):
        raise V03RContractError("alias objects must have distinct SHA-256 identities")
    def key(obj_hash: str) -> tuple[str, str]:
        material = (
            "v2e-alias\0" + namespace + "\0" + view_sha256 + "\0" + stage
            + "\0" + str(logical_round) + "\0" + obj_hash
        ).encode("ascii")
        return sha256_bytes(material), obj_hash
    return {obj_hash: f"{namespace}{index}" for index, obj_hash in enumerate(sorted(hashes, key=key))}


def connector_ledger_hash(raw_connector_ascii: str) -> str:
    return sha256_bytes(b"connector\0" + raw_connector_ascii.encode("ascii"))


def build_provider_view(view: CandidateView, *, stage: str, logical_round: int) -> tuple[bytes, dict[str, str]]:
    """Render one typed selected view after entity/connector redaction."""
    view_hash = view.canonical_view_sha256
    e_hash = view.trigger.semantic_sha256
    m_hashes = [row.semantic_sha256 for row in view.neighborhood]
    entities = sorted(set().union(*(_typed_values(x) for x in (view.trigger, *view.neighborhood))))
    connectors = sorted({x for x in (_connector(y) for y in (view.trigger, *view.neighborhood)) if x})
    x_hashes = [sha256_bytes(x.encode("ascii")) for x in entities]
    c_hashes = [connector_ledger_hash(x) for x in connectors]
    aliases: dict[str, str] = {}
    aliases.update({view.trigger.public_id: alias_map("E", [e_hash], view_sha256=view_hash, stage=stage, logical_round=logical_round)[e_hash]})
    aliases.update({row.semantic_sha256: alias for row, alias in zip(
        view.neighborhood,
        (alias_map("M", m_hashes, view_sha256=view_hash, stage=stage, logical_round=logical_round)[h] for h in m_hashes),
    )})
    x_aliases = alias_map("X", x_hashes, view_sha256=view_hash, stage=stage, logical_round=logical_round)
    aliases.update({raw: x_aliases[h] for raw, h in zip(entities, x_hashes)})
    c_aliases = alias_map("C", c_hashes, view_sha256=view_hash, stage=stage, logical_round=logical_round)
    aliases.update({raw: c_aliases[h] for raw, h in zip(connectors, c_hashes)})

    def redact(value: Any) -> Any:
        if isinstance(value, Mapping):
            return {key: redact(nested) for key, nested in value.items()}
        if isinstance(value, list):
            return [redact(x) for x in value]
        if isinstance(value, str):
            direct = aliases.get(value)
            if direct is not None:
                return direct
            text = value
            for raw in sorted(aliases, key=len, reverse=True):
                text = text.replace(raw, aliases[raw])
            return text
        return value

    trigger = {
        "alias": aliases[view.trigger.public_id], "kind": view.trigger.kind,
        "text": redact(view.trigger.canonical_text),
        "structured": redact(dict(view.trigger.structured)),
    }
    memory = [{
        "alias": aliases[row.semantic_sha256], "kind": row.kind,
        "text": redact(row.canonical_text), "entity_alias": redact(row.entity_id),
        "source_alias": redact(row.source_entity_id),
        "relation_label": row.relation_label, "target_alias": redact(row.target_entity_id),
        "connector_alias": redact(row.connector_id), "polarity": row.polarity,
        "status": PROVISIONAL,
    } for row in view.neighborhood]
    payload = ordered_json_bytes({
        "stage": stage, "logical_round": logical_round,
        "trigger": trigger, "memory": memory,
    })
    forbidden = [RAW_CONNECTOR_SENTINEL, *entities, *connectors]
    if any(raw.encode("ascii") in payload for raw in forbidden if raw):
        raise V03RContractError("provider view contains a raw identifier/sentinel")
    if any(token in payload for token in (b'q_own', b'q_dist', b'arm', b'target_registry', b'scorer')):
        raise V03RContractError("provider view contains forbidden routing metadata")
    if len(set(aliases.values())) != len(aliases.values()):
        # Reuse is valid only where the exact same raw object is reused.  Values
        # across namespaces cannot collide, hence any duplicate here is a bug.
        raise V03RContractError("provider aliases are not bijective")
    return payload, aliases


def build_think_provider_view(
    probe: Mapping[str, Any], memory: Sequence[MemoryRow], *, step: int,
) -> tuple[bytes, dict[str, str]]:
    """Render THINK_0's public probe plus frozen provisional MEMORY_0.

    The probe's own typed endpoint strings are deliberately model-visible: the
    frozen contract requires a valid REQUEST_DREAM to repeat those exact public
    coordinates.  Distractor fields are withheld from THINK cognition.  Memory
    and connectors remain call-local aliases; no final goal or answer exists.
    """
    own = QueryCoordinate.own_from_probe(probe)
    if isinstance(step, bool) or not isinstance(step, int) or not 0 <= step < 12:
        raise V03RContractError("THINK_0 step must be 0..11")
    memory = tuple(sorted(memory, key=lambda x: (x.creation_slot, x.semantic_sha256)))
    _dedup_inputs((), memory)
    view_sha = sha256_json({
        "probe_id": probe["probe_id"], "own": own.exact_bytes().decode("ascii"),
        "memory": [row.semantic_sha256 for row in memory], "step": step,
    })
    m_hashes = [row.semantic_sha256 for row in memory]
    connectors = sorted({row.connector_id for row in memory if row.connector_id})
    c_hashes = [connector_ledger_hash(x) for x in connectors]
    m_aliases = alias_map("M", m_hashes, view_sha256=view_sha, stage="THINK_0", logical_round=step)
    c_aliases = alias_map("C", c_hashes, view_sha256=view_sha, stage="THINK_0", logical_round=step)
    raw_to_alias: dict[str, str] = {h: m_aliases[h] for h in m_hashes}
    raw_to_alias.update({raw: c_aliases[h] for raw, h in zip(connectors, c_hashes)})
    rows = []
    for row in memory:
        rows.append({
            "alias": m_aliases[row.semantic_sha256], "kind": row.kind,
            "canonical_text": row.canonical_text,
            "entity_id": row.entity_id, "source_entity_id": row.source_entity_id,
            "relation_label": row.relation_label, "target_entity_id": row.target_entity_id,
            "connector_alias": c_aliases[connector_ledger_hash(row.connector_id)] if row.connector_id else None,
            "polarity": row.polarity, "status": PROVISIONAL,
        })
    payload = ordered_json_bytes({
        "mode": "THINK_0", "step": step,
        "public_probe": {
            "probe_id": probe["probe_id"],
            "source_entity_id": own.source_entity_id,
            "target_entity_id": own.target_entity_id,
            "question": probe["question"],
        },
        "memory_0": rows,
        "terminal_contract": {
            "request_relation": RELATION, "max_total_operations": 12,
            "terminal_ops": ["REQUEST_DREAM", "DEFER"],
        },
    })
    for forbidden in (
        "matched_distractor", "final_goal", "answer", "RELEASE", "scorer",
        "ground_truth", RAW_CONNECTOR_SENTINEL,
    ):
        if forbidden.casefold().encode("ascii") in payload.lower():
            raise V03RContractError("THINK provider view contains forbidden material")
    if any(raw.encode("ascii") in payload for raw in connectors):
        raise V03RContractError("THINK provider view leaked a raw connector")
    return payload, raw_to_alias


def build_full_context_provider_view(
    public: Sequence[PublicRecord], memory: Sequence[MemoryRow],
) -> tuple[bytes, dict[str, str], tuple[str, ...]]:
    """Render the one explicitly heterogeneous full-context exploratory ceiling.

    It contains all public rows and MEMORY_0 but no q, final task, truth, score,
    or answer.  It therefore remains a target-absent proposal ceiling rather
    than a matched baseline.
    """
    public = tuple(sorted(public, key=lambda x: (x.sequence_index, x.public_id)))
    memory = tuple(sorted(memory, key=lambda x: (x.creation_slot, x.semantic_sha256)))
    _dedup_inputs(public, memory)
    view_sha = sha256_json({
        "public": [x.semantic_sha256 for x in public],
        "memory": [x.semantic_sha256 for x in memory], "kind": "full_context",
    })
    e_hashes = [row.semantic_sha256 for row in public]
    m_hashes = [row.semantic_sha256 for row in memory]
    entities = sorted(set().union(*(_typed_values(x) for x in (*public, *memory))))
    connectors = sorted({x for x in (_connector(y) for y in (*public, *memory)) if x})
    x_hashes = [sha256_bytes(x.encode("ascii")) for x in entities]
    c_hashes = [connector_ledger_hash(x) for x in connectors]
    e_map = alias_map("E", e_hashes, view_sha256=view_sha, stage="FULL_CONTEXT", logical_round=0)
    m_map = alias_map("M", m_hashes, view_sha256=view_sha, stage="FULL_CONTEXT", logical_round=0)
    x_map = alias_map("X", x_hashes, view_sha256=view_sha, stage="FULL_CONTEXT", logical_round=0)
    c_map = alias_map("C", c_hashes, view_sha256=view_sha, stage="FULL_CONTEXT", logical_round=0)
    raw_to_alias = {row.public_id: e_map[row.semantic_sha256] for row in public}
    raw_to_alias.update({row.semantic_sha256: m_map[row.semantic_sha256] for row in memory})
    raw_to_alias.update({raw: x_map[h] for raw, h in zip(entities, x_hashes)})
    raw_to_alias.update({raw: c_map[h] for raw, h in zip(connectors, c_hashes)})

    def redact(value: Any) -> Any:
        if isinstance(value, Mapping):
            return {key: redact(nested) for key, nested in value.items()}
        if isinstance(value, list):
            return [redact(x) for x in value]
        if isinstance(value, str):
            result = value
            for raw in sorted(raw_to_alias, key=len, reverse=True):
                result = result.replace(raw, raw_to_alias[raw])
            return result
        return value
    public_payload = [{
        "alias": e_map[row.semantic_sha256], "kind": row.kind,
        "text": redact(row.canonical_text), "structured": redact(dict(row.structured)),
    } for row in public]
    memory_payload = [{
        "alias": m_map[row.semantic_sha256], "kind": row.kind,
        "text": redact(row.canonical_text), "entity_alias": redact(row.entity_id),
        "source_alias": redact(row.source_entity_id), "relation_label": row.relation_label,
        "target_alias": redact(row.target_entity_id), "connector_alias": redact(row.connector_id),
        "polarity": row.polarity, "status": PROVISIONAL,
    } for row in memory]
    payload = ordered_json_bytes({
        "stage": "EXPLORATORY_CEILING", "ceiling_kind": "FULL_CONTEXT",
        "public": public_payload, "memory_0": memory_payload,
    })
    for forbidden in (RAW_CONNECTOR_SENTINEL, "q_own", "q_dist", "final_goal", "answer", "scorer"):
        if forbidden.casefold().encode("ascii") in payload.lower():
            raise V03RContractError("full-context ceiling contains forbidden material")
    for raw in (*entities, *connectors):
        if raw.encode("ascii") in payload:
            raise V03RContractError("full-context ceiling leaked raw IDs")
    visible_order = tuple([e_map[x] for x in e_hashes] + [m_map[x] for x in m_hashes])
    return payload, raw_to_alias, visible_order


def build_rag_provider_views(
    own_selector: SelectorManifest,
) -> tuple[tuple[bytes, dict[str, str], tuple[str, ...]], ...]:
    """Render the sixteen frozen own-selector views as RAG exploratory ceilings."""
    if own_selector.selector_kind != "own_selector":
        raise V03RContractError("RAG ceilings must use the frozen own-selector views")
    rows = []
    for logical_round, view in enumerate(own_selector.selected):
        payload, aliases = build_provider_view(
            view, stage="EXPLORATORY_CEILING_RAG", logical_round=logical_round,
        )
        visible = (aliases[view.trigger.public_id], *(
            aliases[row.semantic_sha256] for row in view.neighborhood
        ))
        rows.append((payload, aliases, tuple(visible)))
    if len(rows) != 16:
        raise V03RContractError("RAG exploratory ceiling must contain sixteen calls")
    return tuple(rows)


def common_logical_seed(frozen_run_seed: str, life_id: str, logical_round: int) -> tuple[str, int]:
    if isinstance(logical_round, bool) or not isinstance(logical_round, int) or logical_round < 0:
        raise V03RContractError("logical round must be non-negative")
    material = (
        "v2e-return-seed\0" + frozen_run_seed + "\0" + life_id + "\0" + str(logical_round)
    ).encode("ascii")
    digest = sha256_bytes(material)
    return digest, int(digest[:16], 16) & ((1 << 63) - 1)


def cyclic_arm_order(life_id: str, logical_round: int, sorted_life_ids: Sequence[str]) -> tuple[str, ...]:
    lives = tuple(sorted(sorted_life_ids))
    if life_id not in lives or len(lives) != len(set(lives)):
        raise V03RContractError("life order is missing or duplicate")
    offset = lives.index(life_id) % 3
    rotation = (logical_round + offset) % 3
    return ARMS[rotation:] + ARMS[:rotation]


def arm_order_manifest(life_ids: Sequence[str]) -> tuple[dict[str, Any], ...]:
    lives = tuple(sorted(life_ids))
    rows = []
    physical = 0
    for life in lives:
        for logical_round in range(BRANCH_ROUNDS):
            for position, arm in enumerate(cyclic_arm_order(life, logical_round, lives)):
                rows.append({
                    "physical_index": physical, "life_id": life,
                    "logical_round": logical_round, "position": position, "arm": arm,
                })
                physical += 1
    return tuple(rows)


def dynamic_schedule(defined_life_ids: Sequence[str], think_calls: int) -> dict[str, int]:
    ids = tuple(sorted(defined_life_ids))
    if len(ids) != len(set(ids)) or not 0 <= len(ids) <= 6:
        raise V03RContractError("D must be 0..6 unique lives")
    if isinstance(think_calls, bool) or not isinstance(think_calls, int) \
            or not 0 <= think_calls <= MAX_THINK_CALLS:
        raise V03RContractError("observed THINK count must be 0..72")
    d = len(ids)
    return {
        "D": d,
        "shared_recurrent_dream": SHARED_DREAM_CALLS,
        "branch_recurrent_dream": BRANCH_CALLS_PER_DEFINED_LIFE * d,
        "total_recurrent_dream": SHARED_DREAM_CALLS + BRANCH_CALLS_PER_DEFINED_LIFE * d,
        "think_0": think_calls,
        "exploratory_dream": EXPLORATORY_CALLS_PER_DEFINED_LIFE * d,
        "selector_traces": SELECTOR_TRACES_PER_DEFINED_LIFE * d,
        "memory_1": MEMORY1_PER_DEFINED_LIFE * d,
        "scorer_packets": MEMORY1_PER_DEFINED_LIFE * d,
    }


@dataclass(frozen=True)
class ResolvedProposal:
    proposal_id: str
    left_entity_id: str | None
    relation_bytes: str | None
    right_entity_id: str | None
    connector_id: str | None
    polarity: str | None
    cited_public_ids: tuple[str, ...]
    raw_sha256: str
    legal: bool = True
    pass_or_rejection: str | None = None


@dataclass(frozen=True)
class ClosureScores:
    verbatim_exact_closure: bool
    witness_bound_structural_closure: bool
    allowlist_normalized_closure: bool
    witness_bound_normalized_closure: bool
    normalized_relation: str | None
    unmatched_relation: str | None


def validate_relation_allowlist(value: Mapping[str, Any]) -> dict[str, str | None]:
    if not isinstance(value, Mapping):
        raise V03RContractError("relation allowlist must be an object")
    result: dict[str, str | None] = {}
    for key, target in value.items():
        _safe_text(key, "allowlist key", 64)
        if target is not None:
            _safe_text(target, "allowlist value", 64)
            if target != RELATION:
                raise V03RContractError("allowlist values may only normalize to causal_join")
        result[key] = target
    return result


def _has_bound_witnesses(
    proposal: ResolvedProposal, q: QueryCoordinate,
    public_by_id: Mapping[str, PublicRecord], expected_polarity: str,
) -> bool:
    route_connectors = set()
    effect_connectors = set()
    for citation in proposal.cited_public_ids:
        row = public_by_id.get(citation)
        if row is None:
            continue
        if row.kind == "valve_route" and q.source_entity_id in _typed_values(row):
            route_connectors.add(_connector(row))
        if row.kind == "intervention_effect" and q.target_entity_id in _typed_values(row) \
                and _polarity(row) == expected_polarity:
            effect_connectors.add(_connector(row))
    return proposal.connector_id in (route_connectors & effect_connectors)


def score_proposal(
    proposal: ResolvedProposal, q_own: QueryCoordinate,
    public_by_id: Mapping[str, PublicRecord], allowlist: Mapping[str, Any],
    *, expected_polarity: str,
) -> ClosureScores:
    q_own.validate()
    if expected_polarity not in {"POSITIVE", "NEGATIVE"}:
        raise V03RContractError("expected scorer polarity must be resolved offline")
    normalized = validate_relation_allowlist(allowlist).get(proposal.relation_bytes or "")
    structural = (
        proposal.legal
        and proposal.left_entity_id == q_own.source_entity_id
        and proposal.right_entity_id == q_own.target_entity_id
        and proposal.connector_id is not None
        and proposal.polarity == expected_polarity
    )
    verbatim = structural and proposal.relation_bytes == RELATION
    allowlisted = structural and normalized == RELATION
    witness = _has_bound_witnesses(proposal, q_own, public_by_id, expected_polarity)
    return ClosureScores(
        bool(verbatim), bool(verbatim and witness), bool(allowlisted),
        bool(allowlisted and witness), normalized,
        None if normalized is not None else proposal.relation_bytes,
    )


def comparable_controls(
    *, trigger: PublicRecord, memory: Sequence[MemoryRow], aliases: Mapping[str, str],
) -> Mapping[str, ResolvedProposal | None]:
    """Three deterministic, visible-input-only compiler controls."""
    items: tuple[PublicRecord | MemoryRow, ...] = (trigger, *memory)
    source = next((x for item in items for x in _typed_values(item) if x.startswith("entity:source:")), None)
    target = next((x for item in items for x in _typed_values(item) if x.startswith("entity:target:")), None)
    connectors = [x for x in (_connector(item) for item in items) if x is not None]
    shared = next((x for x in connectors if connectors.count(x) >= 2), None)
    relation = next((item.relation_label for item in memory if item.relation_label), None)
    citations = tuple(item.public_id for item in items if isinstance(item, PublicRecord))
    def proposal(name: str, rel: str | None, connector: str | None) -> ResolvedProposal | None:
        if source is None or target is None or rel is None or connector is None:
            return None
        payload = (name, source, rel, target, connector)
        return ResolvedProposal(
            sha256_json(payload), source, rel, target, connector, "UNKNOWN", citations,
            sha256_json({"control": payload}), True,
        )
    return {
        "visible_byte_constructor": proposal("bytes", relation, connectors[0] if connectors else None),
        "visible_shared_c_join": proposal("shared_c", RELATION, shared),
        "visible_literal_relation_constructor": proposal("literal", relation, shared),
    }


def aggregate_scores(rows: Sequence[tuple[ResolvedProposal, ClosureScores]]) -> dict[str, Any]:
    metric_names = tuple(ClosureScores.__dataclass_fields__)[:4]
    closures = {name: [p.proposal_id for p, score in rows if getattr(score, name)] for name in metric_names}
    proposal_ids = [p.proposal_id for p, _ in rows]
    return {
        "denominator": len(rows),
        "legal_proposals": sum(p.legal for p, _ in rows),
        "passes_or_rejections": sum(not p.legal or p.pass_or_rejection is not None for p, _ in rows),
        "closure_ids": closures,
        "normalization_only_ids": sorted(set(closures["allowlist_normalized_closure"]) - set(closures["verbatim_exact_closure"])),
        "witness_normalization_only_ids": sorted(set(closures["witness_bound_normalized_closure"]) - set(closures["witness_bound_structural_closure"])),
        "unique_semantic_closures": len(set(proposal_ids)),
        "duplicate_proposal_count": len(proposal_ids) - len(set(proposal_ids)),
    }


def validate_phase_a_inventory(inventory: Mapping[str, Any]) -> str:
    """Validate raw cognition cardinalities and absence of scorer material."""
    required = {
        "defined_life_ids", "shared_dream_calls", "branch_dream_calls", "think_calls",
        "exploratory_calls", "selector_traces", "memory1_checkpoints",
        "scorer_material_present", "unique_session_ids", "unique_receipt_ids",
        "phase_a_raw_graph_sha256",
    }
    if set(inventory) != required:
        raise V03RContractError("phase-A inventory schema mismatch")
    expected = dynamic_schedule(inventory["defined_life_ids"], inventory["think_calls"])
    checks = {
        "shared_dream_calls": expected["shared_recurrent_dream"],
        "branch_dream_calls": expected["branch_recurrent_dream"],
        "exploratory_calls": expected["exploratory_dream"],
        "selector_traces": expected["selector_traces"],
        "memory1_checkpoints": expected["memory_1"],
    }
    if any(inventory[key] != value for key, value in checks.items()):
        raise V03RContractError("phase-A D-scaled cardinality mismatch")
    total_provider_calls = (
        expected["total_recurrent_dream"] + expected["think_0"] + expected["exploratory_dream"]
    )
    if inventory["unique_session_ids"] != total_provider_calls \
            or inventory["unique_receipt_ids"] != total_provider_calls:
        raise V03RContractError("phase-A physical session/receipt bijection failed")
    if inventory["scorer_material_present"] is not False:
        raise V03RContractError("scorer material appeared before phase-A seal")
    if _HASH.fullmatch(str(inventory["phase_a_raw_graph_sha256"])) is None:
        raise V03RContractError("phase-A raw graph hash is invalid")
    return sha256_json({"schema_version": "v03r-phase-a-seal-v2e", "inventory": inventory})


def validate_phase_b_inventory(inventory: Mapping[str, Any], *, phase_a_seal_sha256: str) -> str:
    required = {
        "defined_life_ids", "score_packets", "life_rows", "pair_rows",
        "four_metric_rows_per_proposal", "controls_complete", "normalization_gains_complete",
        "exploratory_rows", "terminal_markers", "phase_a_seal_sha256",
    }
    if set(inventory) != required or inventory["phase_a_seal_sha256"] != phase_a_seal_sha256:
        raise V03RContractError("phase-B inventory/seal binding mismatch")
    d = len(tuple(inventory["defined_life_ids"]))
    if inventory["score_packets"] != 3 * d or inventory["life_rows"] != 6 \
            or inventory["pair_rows"] != 3 or inventory["exploratory_rows"] != 17 * d:
        raise V03RContractError("phase-B cardinality mismatch")
    if inventory["four_metric_rows_per_proposal"] is not True \
            or inventory["controls_complete"] is not True \
            or inventory["normalization_gains_complete"] is not True:
        raise V03RContractError("phase-B scoring graph is incomplete")
    if inventory["terminal_markers"] != ["done.json"]:
        raise V03RContractError("phase B requires exactly one done marker")
    return sha256_json({"schema_version": "v03r-phase-b-seal-v2e", "inventory": inventory})


def validate_exploratory_precedence(
    defined_life_ids: Sequence[str], branch_counts: Mapping[str, int],
    memory1_counts: Mapping[str, int], exploratory_counts: Mapping[str, int],
) -> None:
    defined = set(defined_life_ids)
    all_ids = set(branch_counts) | set(memory1_counts) | set(exploratory_counts)
    for life in all_ids:
        if life not in defined:
            if any(mapping.get(life, 0) for mapping in (branch_counts, memory1_counts, exploratory_counts)):
                raise V03RContractError("PRIMARY_UNDEFINED life received D-scaled work")
            continue
        if branch_counts.get(life) != 48 or memory1_counts.get(life) != 3:
            if exploratory_counts.get(life, 0):
                raise V03RContractError("exploratory ceiling ran before complete branch freeze")
            raise V03RContractError("defined life branch is incomplete")
        if exploratory_counts.get(life) != 17:
            raise V03RContractError("defined life requires exactly seventeen exploratory calls")


__all__ = [name for name in globals() if not name.startswith("_")]
