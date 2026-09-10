"""Deterministic CPU-only contract for recurrent one-edge micro-dream v0.

This module validates JSON-shaped traces; it does not render prompts, load a
model, score a world, or launch a GPU. A cycle has one cognitive operation:
``ADD``, ``REVISE``, ``OPEN_QUESTION``, or ``PASS``. The first two append one
memory-node event, while the latter two may append no memory event. A
self-check ``STATUS_CHANGE`` is an audit event, not a second cognitive
operation.

The trace is intentionally append-only. A revision creates a fresh node with
``supersedes=[old_node_id]`` and leaves the old node available for conflict and
history reads. Depth is derived from cited earlier nodes and is never inferred
from a claimed depth alone.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any
import hashlib
import re

from .microdream_classification import (
    ProposalContext,
    ProposalDecision,
    classify_proposal,
    classify_self_check,
    public_rows_from_prompt,
    public_tokens,
)
from .microdream_prompts import (
    CLAIM_KINDS,
    ParsedMicrodream,
    canonical_edge,
    local_edge_errors,
)


SCHEMA_VERSION = "recurrent-microdream-v0.6"
SPLITS = frozenset({"train", "dev", "test", "holdout"})
TRIGGER_KINDS = frozenset({"WAKE", "REACTIVATE"})
OPERATIONS = frozenset({"ADD", "REVISE", "OPEN_QUESTION", "PASS"})
OBSERVED_OPERATIONS = frozenset({"MALFORMED"})
MEMORY_EVENT_TYPES = frozenset({"ADD_NODE", "REVISE_NODE"})
EVENT_TYPES = MEMORY_EVENT_TYPES | {"STATUS_CHANGE"}
STATUSES = frozenset({"provisional", "supported", "contradicted", "unresolved"})
CONDITIONS = frozenset({
    "no_gate_no_drift", "no_gate_drift",
    "self_check_no_drift", "self_check_drift",
})


class ContractError(ValueError):
    """Raised by assertion helpers when a trace violates the contract."""


_FORBIDDEN_KEY = re.compile(
    r"(?:hidden|secret|ground[_ -]?truth|final[_ -]?answer|answer[_ -]?key|"
    r"proof[_ -]?graph|factor[_ -]?solver|(?:evaluator|scorer|checker)[_ -]?"
    r"(?:label|verdict|score)|offline[_ -]?truth)", re.IGNORECASE,
)
_FORBIDDEN_TEXT = re.compile(
    r"(?:hidden[_ -]?(?:truth|answer|parent|role)|ground[_ -]?truth|"
    r"final[_ -]?answer\s*:|answer[_ -]?key\s*:|proof[_ -]?graph|"
    r"factor[_ -]?solver|(?:evaluator|scorer|checker)[_ -]?"
    r"(?:label|verdict|score)\s*:|offline[_ -]?truth\s*:)", re.IGNORECASE,
)
_SHA256 = re.compile(r"[0-9a-f]{64}")
_CALL_USAGE_FIELDS = frozenset({
    "prompt_tokens", "output_tokens", "original_prompt_tokens",
    "prompt_truncated", "source", "supplied_prompt_token_ids_sha256",
    "output_token_ids_sha256", "output_sha256",
})


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _check_text_hash(value: Any, digest: Any, path: str,
                     errors: list[str]) -> None:
    if not _nonempty(value):
        errors.append(f"{path}: missing exact model-visible text")
        return
    expected = hashlib.sha256(value.encode("utf-8")).hexdigest()
    if digest != expected:
        errors.append(f"{path}_sha256: does not hash the recorded text")


def _check_sha256(value: Any, path: str, errors: list[str]) -> None:
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        errors.append(f"{path}: must be a lowercase SHA-256 digest")


def _check_call_record(
    call: Any, path: str, errors: list[str], *, expected_prompt: Any = None,
    cpu_fixture: bool = False,
) -> None:
    """Validate one exact, model-visible generation call and its token audit."""
    if not isinstance(call, Mapping):
        errors.append(f"{path}: required call object")
        return

    if not _nonempty(call.get("call_id")):
        errors.append(f"{path}.call_id: required non-empty call identifier")
    if not isinstance(call.get("cycle_index"), int) or isinstance(
            call.get("cycle_index"), bool) or call["cycle_index"] < 0:
        errors.append(f"{path}.cycle_index: must be a non-negative integer")
    if call.get("kind") not in {"proposal", "self_check"}:
        errors.append(f"{path}.kind: must be proposal or self_check")

    prompt = call.get("prompt")
    output = call.get("output")
    _check_text_hash(prompt, call.get("prompt_sha256"), f"{path}.prompt", errors)
    _check_text_hash(output, call.get("output_sha256"), f"{path}.output", errors)
    if expected_prompt is not None and prompt != expected_prompt:
        errors.append(f"{path}.prompt: differs from the exact cycle model_prompt")
    # Hash agreement is not a visibility audit: inspect the actual bytes supplied
    # to and returned by the model as well.
    if _nonempty(prompt):
        _visible_errors(prompt, f"{path}.prompt", errors)
    if _nonempty(output):
        _visible_errors(output, f"{path}.output", errors)

    seed = call.get("seed")
    if not isinstance(seed, int) or isinstance(seed, bool) or seed < 0:
        errors.append(f"{path}.seed: must be a non-negative integer")
    max_tokens = call.get("max_tokens")
    if not isinstance(max_tokens, int) or isinstance(max_tokens, bool) or max_tokens <= 0:
        errors.append(f"{path}.max_tokens: must be a positive integer")
    temperature = call.get("temperature")
    if (not isinstance(temperature, (int, float)) or isinstance(temperature, bool)
            or temperature < 0):
        errors.append(f"{path}.temperature: must be a non-negative number")

    usage = call.get("usage")
    if not isinstance(usage, Mapping):
        errors.append(f"{path}.usage: required full usage object")
        return
    for field in sorted(_CALL_USAGE_FIELDS - set(usage)):
        errors.append(f"{path}.usage: missing {field}")
    for field in ("prompt_tokens", "output_tokens", "original_prompt_tokens"):
        value = usage.get(field)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            errors.append(f"{path}.usage.{field}: must be a non-negative integer")
    prompt_tokens = usage.get("prompt_tokens")
    original_tokens = usage.get("original_prompt_tokens")
    if (isinstance(prompt_tokens, int) and not isinstance(prompt_tokens, bool)
            and isinstance(original_tokens, int) and not isinstance(original_tokens, bool)
            and original_tokens < prompt_tokens):
        errors.append(f"{path}.usage: original_prompt_tokens is below prompt_tokens")
    if not isinstance(usage.get("prompt_truncated"), bool):
        errors.append(f"{path}.usage.prompt_truncated: must be boolean")
    source = usage.get("source")
    if source not in {"model", "scripted_fallback"}:
        errors.append(f"{path}.usage.source: must be model or scripted_fallback")
    elif source == "scripted_fallback" and not cpu_fixture:
        errors.append(f"{path}.usage.source: scripted_fallback is allowed only in a CPU fixture")
    if source == "model" and usage.get("prompt_truncated") is not False:
        errors.append(f"{path}.usage.prompt_truncated: model calls must not truncate prompts")
    for field in ("supplied_prompt_token_ids_sha256", "output_token_ids_sha256"):
        _check_sha256(usage.get(field), f"{path}.usage.{field}", errors)
    _check_sha256(usage.get("output_sha256"), f"{path}.usage.output_sha256", errors)
    if _nonempty(output):
        expected_output_hash = hashlib.sha256(output.encode("utf-8")).hexdigest()
        if usage.get("output_sha256") != expected_output_hash:
            errors.append(f"{path}.usage.output_sha256: does not hash the recorded output")
        if call.get("output_sha256") != usage.get("output_sha256"):
            errors.append(f"{path}: call and usage output_sha256 differ")


def canonical_corpus_text(left: str, relation: str, right: str) -> str:
    """Render the only durable textual form of one typed memory edge."""
    return f"{left} {relation} {right}."


def _same_call(left: Any, right: Any) -> bool:
    return isinstance(left, Mapping) and isinstance(right, Mapping) and dict(left) == dict(right)


def _proposal_binding_errors(
    operation: Mapping[str, Any], output: Any, path: str, errors: list[str],
    *, decision: ProposalDecision,
) -> ParsedMicrodream | None:
    """Bind a model completion to the structured operation it allegedly caused."""
    if not isinstance(output, str):
        errors.append(f"{path}: proposal output must be text")
        return None
    parsed = decision.parsed
    kind = operation.get("kind")
    if kind != decision.kind:
        errors.append(
            f"{path}.kind: complete runner classification is {decision.kind}, not {kind}"
        )
    if decision.kind == "MALFORMED":
        # A parseable line can still be malformed.  The shared classifier—not a
        # trace author's structured rewrite—decides whether it has an effect.
        return parsed
    if parsed is None:
        errors.append(f"{path}: structured operation is not parsed from proposal output")
        return None
    expected_kind = parsed.operation.upper()
    if kind != expected_kind:
        errors.append(f"{path}.kind: proposal parses as {expected_kind}, not {kind}")
    if parsed.operation in {"add", "revise"}:
        expected_fields = {
            "claim_kind": parsed.claim_kind,
            "left": parsed.left,
            "relation": parsed.relation,
            "right": parsed.right,
            "claim": parsed.claim,
            "prediction": parsed.prediction,
            "confidence": parsed.confidence,
            "supersedes": list(parsed.supersedes),
        }
        expected_edge = canonical_edge(parsed)
        expected_fields["edge"] = list(expected_edge) if expected_edge is not None else None
    elif parsed.operation == "open_question":
        expected_fields = {
            "claim_kind": parsed.claim_kind,
            "left": parsed.left,
            "relation": parsed.relation,
            "right": parsed.right,
        }
    else:
        expected_fields = {}
    for key, expected in expected_fields.items():
        if operation.get(key) != expected:
            errors.append(f"{path}.{key}: differs from parsed proposal output")
    if parsed.operation in {"add", "revise", "open_question"}:
        recorded_cites: list[str] = []
        for key in ("cited_episode_ids", "cited_experience_ids", "cited_node_ids"):
            value = operation.get(key)
            if not isinstance(value, list):
                errors.append(f"{path}.{key}: required for parsed proposal")
            else:
                recorded_cites.extend(value)
        if len(recorded_cites) != len(parsed.cites) or set(recorded_cites) != set(parsed.cites):
            errors.append(f"{path}: structured citations differ from parsed proposal output")
    return parsed


def _memory_event_binding_errors(event: Mapping[str, Any], parsed: ParsedMicrodream | None,
                                 path: str, errors: list[str]) -> None:
    if parsed is None or parsed.operation not in {"add", "revise"}:
        errors.append(f"{path}: memory event has no matching parsed ADD/REVISE proposal")
        return
    expected_edge = canonical_edge(parsed)
    expected = {
        "operation": parsed.operation.upper(),
        "claim_kind": parsed.claim_kind,
        "left": parsed.left,
        "relation": parsed.relation,
        "right": parsed.right,
        "edge": list(expected_edge) if expected_edge is not None else None,
        "claim": parsed.claim,
        "prediction": parsed.prediction,
        "confidence": parsed.confidence,
        "supersedes": list(parsed.supersedes),
    }
    for key, value in expected.items():
        if event.get(key) != value:
            errors.append(f"{path}.{key}: differs from parsed proposal output")
    recorded_cites: list[str] = []
    for key in ("cited_episode_ids", "cited_experience_ids", "cited_node_ids"):
        value = event.get(key)
        if isinstance(value, list):
            recorded_cites.extend(value)
    if len(recorded_cites) != len(parsed.cites) or set(recorded_cites) != set(parsed.cites):
        errors.append(f"{path}: event citations differ from parsed proposal output")


def _walk(value: Any, path: str = ""):
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_path = f"{path}.{key}" if path else str(key)
            yield key_path, key
            yield from _walk(child, key_path)
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            yield from _walk(child, f"{path}[{index}]")
    else:
        yield path, value


def _scope(trace: Mapping[str, Any]) -> tuple[Any, Any, Any]:
    return tuple(trace.get(key) for key in ("world_id", "skin_id", "life_id"))


def _scope_errors(value: Any, expected: tuple[Any, Any, Any], path: str,
                  errors: list[str]) -> None:
    keys = ("world_id", "skin_id", "life_id")
    if not isinstance(value, Mapping):
        errors.append(f"{path}: must be an object")
        return
    for key, wanted in zip(keys, expected):
        if not _nonempty(value.get(key)):
            errors.append(f"{path}: missing {key}")
        elif value.get(key) != wanted:
            errors.append(f"{path}.{key}: crosses world/skin/life scope")


def _visible_errors(value: Any, path: str, errors: list[str],
                    expected: tuple[Any, Any, Any] | None = None) -> None:
    positions = {"world_id": 0, "skin_id": 1, "life_id": 2}
    for nested_path, item in _walk(value, path):
        if not isinstance(item, str):
            continue
        if _FORBIDDEN_KEY.search(nested_path):
            errors.append(f"{nested_path}: forbidden model-visible field")
        if _FORBIDDEN_TEXT.search(item):
            errors.append(f"{nested_path}: forbidden model-visible text")
        if expected is not None:
            field = nested_path.rsplit(".", 1)[-1]
            position = positions.get(field)
            if position is not None and item != field and item != expected[position]:
                errors.append(f"{nested_path}: cross-world/life state leakage")


def _ids(value: Any, path: str, errors: list[str], *, allow_empty: bool = False) -> list[str]:
    if value is None and allow_empty:
        return []
    if not isinstance(value, list) or (not value and not allow_empty):
        errors.append(f"{path}: must be a {'non-empty ' if not allow_empty else ''}list")
        return []
    result: list[str] = []
    seen: set[str] = set()
    for index, item in enumerate(value):
        if not _nonempty(item):
            errors.append(f"{path}[{index}]: missing non-empty id")
        elif item in seen:
            errors.append(f"{path}[{index}]: duplicate id")
        else:
            seen.add(item)
            result.append(item)
    return result


def _check_tokens(operation: Mapping[str, Any], path: str, errors: list[str]) -> None:
    if "target_tokens" not in operation and "loss_mask" not in operation:
        return
    tokens = operation.get("target_tokens")
    mask = operation.get("loss_mask")
    if not isinstance(tokens, list) or not all(isinstance(x, str) for x in tokens):
        errors.append(f"{path}.target_tokens: must be a list of strings")
    if not isinstance(mask, list) or not all(x in (0, 1) for x in mask):
        errors.append(f"{path}.loss_mask: must be a list of 0/1 integers")
    elif isinstance(tokens, list) and len(tokens) != len(mask):
        errors.append(f"{path}: target_tokens/loss_mask length differs")
    elif isinstance(mask, list) and not any(mask):
        errors.append(f"{path}: operation target has no trainable cognitive tokens")


def _check_temporal_ids(
    *, cited_episode_ids: Any, cited_experience_ids: Any, cited_node_ids: Any,
    retrieved_node_ids: Any,
    path: str, cycle_index: int, episode_index: int | None,
    current_episode_id: str | None, current_experience_ids: set[str],
    episodes: Mapping[str, dict[str, Any]],
    experiences: Mapping[str, tuple[int, str]],
    nodes: Mapping[str, dict[str, Any]], errors: list[str],
) -> tuple[list[str], list[str], list[str], list[str]]:
    episode_ids = _ids(cited_episode_ids, f"{path}.cited_episode_ids", errors,
                       allow_empty=True)
    experience_ids = _ids(cited_experience_ids, f"{path}.cited_experience_ids", errors,
                           allow_empty=True)
    node_ids = _ids(cited_node_ids, f"{path}.cited_node_ids", errors,
                    allow_empty=True)
    retrieved = _ids(retrieved_node_ids, f"{path}.retrieved_node_ids", errors,
                     allow_empty=True)
    for episode_id in episode_ids:
        episode = episodes.get(episode_id)
        if episode is None:
            errors.append(f"{path}: unknown cited episode {episode_id}")
            continue
        cited_index = episode["episode_index"]
        if current_episode_id is None:
            errors.append(f"{path}: REACTIVATE raw episode citations are forbidden")
        elif episode_id != current_episode_id:
            errors.append(f"{path}: WAKE episode citation is outside current episode")
        if episode_index is None or cited_index > episode_index or (
                current_episode_id is None and cited_index >= cycle_index):
            errors.append(f"{path}: cited episode {episode_id} is from the future")
        if current_episode_id == episode_id and not current_experience_ids:
            errors.append(f"{path}: current cited episode has no public experience")
    for node_id in node_ids + retrieved:
        node = nodes.get(node_id)
        if node is None:
            errors.append(f"{path}: unknown node {node_id}")
        elif node["created_cycle"] >= cycle_index:
            errors.append(f"{path}: node {node_id} is from the future or current cycle")
    for experience_id in experience_ids:
        actual = experiences.get(experience_id)
        if actual is None:
            errors.append(f"{path}: unknown cited experience {experience_id}")
            continue
        exp_index, exp_episode_id = actual
        if current_episode_id is None:
            errors.append(f"{path}: REACTIVATE raw experience citations are forbidden")
        elif exp_episode_id != current_episode_id:
            errors.append(f"{path}: WAKE experience citation is outside current episode")
        if episode_index is None or exp_index > episode_index:
            errors.append(f"{path}: cited experience {experience_id} is from the future")
        elif current_episode_id == exp_episode_id and experience_id not in current_experience_ids:
            errors.append(f"{path}: cited experience {experience_id} is not visible in current WAKE")
        elif current_episode_id is None and exp_index >= cycle_index:
            errors.append(f"{path}: cited experience {experience_id} is not earlier than reactivation")
    return episode_ids, experience_ids, node_ids, retrieved


def _event_edge(event: Mapping[str, Any], path: str,
                errors: list[str]) -> tuple[str, str, str, str] | None:
    if event.get("claim_kind") not in CLAIM_KINDS:
        errors.append(f"{path}.claim_kind: must be a supported typed claim kind")
    operation = "revise" if event.get("operation") == "REVISE" else "add"
    parsed = ParsedMicrodream(
        operation=operation,
        claim_kind=event.get("claim_kind"),
        left=event.get("left"),
        relation=event.get("relation"),
        right=event.get("right"),
    )
    for error in local_edge_errors(parsed):
        errors.append(f"{path}.edge: {error}")
    expected = canonical_edge(parsed)
    recorded = event.get("edge")
    if not isinstance(recorded, list) or len(recorded) != 4 or not all(
            isinstance(item, str) and item for item in recorded):
        errors.append(f"{path}.edge: must be the four-string canonical edge")
    elif expected is not None and tuple(recorded) != expected:
        errors.append(f"{path}.edge: does not match canonical typed fields")
    return expected


def _node_depth(*, edge: tuple[str, str, str, str] | None,
                cited_node_ids: Sequence[str], supersedes: Sequence[str],
                event_type: str, nodes: Mapping[str, dict[str, Any]]) -> int:
    """Count semantic path extension, not citations or revision lineage."""
    if event_type == "REVISE_NODE" and len(supersedes) == 1 and supersedes[0] in nodes:
        return int(nodes[supersedes[0]]["depth"])
    if edge is None:
        return 1
    endpoints = {edge[1], edge[3]}
    extending: list[int] = []
    for node_id in cited_node_ids:
        prior = nodes.get(node_id)
        if prior is None or prior.get("edge") is None:
            continue
        prior_edge = tuple(prior["edge"])
        if prior_edge[1:] != edge[1:] and endpoints.intersection({prior_edge[1], prior_edge[3]}):
            extending.append(int(prior["depth"]))
    return 1 + max(extending, default=0)


def _check_node_event(
    event: Mapping[str, Any], path: str, *, event_type: str,
    cycle_index: int, episode_index: int | None, current_episode_id: str | None,
    current_experience_ids: set[str], expected: tuple[Any, Any, Any],
    episodes: Mapping[str, dict[str, Any]], experiences: Mapping[str, tuple[int, str]],
    nodes: dict[str, dict[str, Any]], errors: list[str],
) -> str | None:
    node_id = event.get("node_id")
    if not _nonempty(node_id):
        errors.append(f"{path}: missing non-empty node_id")
        return None
    if node_id in nodes:
        errors.append(f"{path}: node_id already exists; append a new node instead")
    expected_operation = "ADD" if event_type == "ADD_NODE" else "REVISE"
    if event.get("operation") != expected_operation:
        errors.append(f"{path}: {event_type} requires operation {expected_operation}")
    for key in ("claim", "claim_kind", "left", "relation", "right",
                "prediction", "raw_completion"):
        if not isinstance(event.get(key), str) or not event[key].strip():
            errors.append(f"{path}: missing non-empty {key}")
    edge = _event_edge(event, path, errors)
    if edge is not None:
        duplicate_ids = [
            old_id for old_id, old in nodes.items()
            if old.get("edge") is not None and tuple(old["edge"])[1:] == edge[1:]
        ]
        raw_supersedes = event.get("supersedes")
        allowed_duplicate = (
            set(raw_supersedes) if event_type == "REVISE_NODE"
            and isinstance(raw_supersedes, list) else set()
        )
        if any(old_id not in allowed_duplicate for old_id in duplicate_ids):
            errors.append(f"{path}.edge: repeated semantic triple cannot create a new node/depth")
    for key in ("prompt_tokens", "output_tokens"):
        if not isinstance(event.get(key), int) or isinstance(event[key], bool) or event[key] < 0:
            errors.append(f"{path}.{key}: must be a non-negative integer")
    confidence = event.get("confidence")
    if not isinstance(confidence, (int, float)) or isinstance(confidence, bool) or not 0 <= confidence <= 1:
        errors.append(f"{path}.confidence: must be a number in [0, 1]")
    if event.get("status") != "provisional":
        errors.append(f"{path}.status: new model node must start provisional")
    supersedes = _ids(event.get("supersedes"), f"{path}.supersedes", errors,
                      allow_empty=(event_type == "ADD_NODE"))
    if event_type == "REVISE_NODE":
        if len(supersedes) != 1:
            errors.append(f"{path}.supersedes: REVISE must supersede exactly one old node")
        elif supersedes[0] not in nodes:
            errors.append(f"{path}: superseded node does not exist")
        elif supersedes[0] == node_id:
            errors.append(f"{path}: REVISE cannot supersede its new node id")
    elif supersedes:
        errors.append(f"{path}.supersedes: ADD must not supersede a node")
    for key in ("cited_episode_ids", "cited_experience_ids", "cited_node_ids"):
        if key not in event:
            errors.append(f"{path}: missing explicit {key}")
    cited_episode_ids, cited_experience_ids, cited_node_ids, retrieved = _check_temporal_ids(
        cited_episode_ids=event.get("cited_episode_ids"),
        cited_experience_ids=event.get("cited_experience_ids"),
        cited_node_ids=event.get("cited_node_ids"),
        retrieved_node_ids=event.get("retrieved_node_ids"),
        path=path, cycle_index=cycle_index, episode_index=episode_index,
        current_episode_id=current_episode_id,
        current_experience_ids=current_experience_ids, episodes=episodes,
        experiences=experiences, nodes=nodes, errors=errors,
    )
    if not cited_episode_ids and not cited_experience_ids and not cited_node_ids:
        errors.append(f"{path}: node needs at least one cited episode, experience, or node")
    if event_type == "REVISE_NODE" and len(supersedes) == 1:
        superseded_id = supersedes[0]
        if superseded_id not in cited_node_ids:
            errors.append(f"{path}: REVISE must cite its superseded node")
        prior = nodes.get(superseded_id)
        if prior is not None and edge is not None and prior.get("edge") is not None:
            prior_edge = tuple(prior["edge"])
            old_endpoints = {prior_edge[1], prior_edge[3]}
            new_endpoints = {edge[1], edge[3]}
            if not old_endpoints.intersection(new_endpoints):
                errors.append(f"{path}.edge: REVISE cannot replace an unrelated semantic edge")
    depth = event.get("depth")
    expected_depth = _node_depth(
        edge=edge, cited_node_ids=cited_node_ids, supersedes=supersedes,
        event_type=event_type, nodes=nodes,
    )
    if not isinstance(depth, int) or isinstance(depth, bool):
        errors.append(f"{path}.depth: must be an integer")
    elif depth != expected_depth:
        errors.append(f"{path}.depth: expected true depth {expected_depth}, got {depth}")
    if not isinstance(event.get("trigger"), Mapping):
        errors.append(f"{path}.trigger: required trigger object")
    if not isinstance(event.get("model_visible"), bool):
        errors.append(f"{path}: model_visible must be boolean")
    elif event["model_visible"]:
        _visible_errors(event, path, errors, expected)
    nodes[node_id] = {
        "episode_index": episode_index, "created_cycle": cycle_index,
        "depth": depth if isinstance(depth, int) else expected_depth,
        "event_id": event.get("event_id"), "status": "provisional",
        "status_event_id": None,
        "supersedes": supersedes, "edge": edge, "superseded_by": None,
    }
    return node_id


def _check_status_event(
    event: Mapping[str, Any], path: str, *, cycle_index: int,
    episode_index: int | None, current_episode_id: str | None,
    current_experience_ids: set[str], expected: tuple[Any, Any, Any],
    episodes: Mapping[str, dict[str, Any]], experiences: Mapping[str, tuple[int, str]],
    nodes: dict[str, dict[str, Any]], latest_status: dict[str, str],
    errors: list[str], cpu_fixture: bool,
    proposal_decision: ProposalDecision, proposal_context: ProposalContext,
) -> None:
    node_id = event.get("node_id")
    if node_id not in nodes:
        errors.append(f"{path}: STATUS_CHANGE refers to unknown node")
    if event.get("operation") != "SELF_CHECK":
        errors.append(f"{path}: status event must use non-cognitive SELF_CHECK operation")
    self_check_call = event.get("self_check_call")
    legacy_prompt = event.get("self_check_prompt")
    _check_call_record(
        self_check_call, f"{path}.self_check_call", errors,
        expected_prompt=legacy_prompt if legacy_prompt is not None else None,
        cpu_fixture=cpu_fixture,
    )
    if legacy_prompt is not None:
        _check_text_hash(legacy_prompt, event.get("self_check_prompt_sha256"),
                         f"{path}.self_check_prompt", errors)
    status = event.get("status")
    if status not in STATUSES or status == "provisional":
        errors.append(f"{path}.status: self-check status must be supported, contradicted, or unresolved")
    if event.get("previous_status") != latest_status.get(node_id, "provisional"):
        errors.append(f"{path}: status event does not append to current status")
    if status == latest_status.get(node_id):
        errors.append(f"{path}: status event is a no-op mutation")
    parsed_proposal = proposal_decision.parsed
    proposal_cites = (
        parsed_proposal.cites if parsed_proposal is not None else ()
    )
    supersedes = (
        parsed_proposal.supersedes if parsed_proposal is not None else ()
    )
    self_check_decision = classify_self_check(
        self_check_call.get("output", "") if isinstance(self_check_call, Mapping) else "",
        proposal_cites=proposal_cites,
        supersedes=supersedes,
        context=proposal_context,
    )
    parsed_verdict = self_check_decision.verdict
    if (isinstance(self_check_call, Mapping)
            and event.get("self_check_raw_completion") != self_check_call.get("output")):
        errors.append(f"{path}.self_check_raw_completion: differs from self-check call output")
    if not self_check_decision.valid:
        errors.append(
            f"{path}: self-check verdict cites material absent from its bound evidence prompt"
        )
    if parsed_verdict is None:
        errors.append(f"{path}: status event is not parsed from self-check output")
    else:
        parsed_status, parsed_reason, parsed_cites = parsed_verdict
        if status != parsed_status:
            errors.append(f"{path}.status: differs from parsed self-check output")
        if event.get("reason") != parsed_reason:
            errors.append(f"{path}.reason: differs from parsed self-check output")
        recorded_cites: list[str] = []
        for key in ("cited_episode_ids", "cited_experience_ids", "cited_node_ids"):
            value = event.get(key)
            if isinstance(value, list):
                recorded_cites.extend(value)
        if len(recorded_cites) != len(parsed_cites) or set(recorded_cites) != set(parsed_cites):
            errors.append(f"{path}: status citations differ from parsed self-check output")
    for key in ("cited_episode_ids", "cited_experience_ids", "cited_node_ids"):
        if key not in event:
            errors.append(f"{path}: missing explicit {key}")
    _, _, status_cited_nodes, _ = _check_temporal_ids(
        cited_episode_ids=event.get("cited_episode_ids"),
        cited_experience_ids=event.get("cited_experience_ids"),
        cited_node_ids=event.get("cited_node_ids"),
        retrieved_node_ids=event.get("retrieved_node_ids"),
        path=path, cycle_index=cycle_index, episode_index=episode_index,
        current_episode_id=current_episode_id,
        current_experience_ids=current_experience_ids, episodes=episodes,
        experiences=experiences, nodes=nodes, errors=errors,
    )
    node = nodes.get(node_id)
    if node is not None and node.get("supersedes"):
        superseded_id = node["supersedes"][0]
        if superseded_id not in status_cited_nodes:
            errors.append(f"{path}: revision self-check must cite the superseded node")
        prior = nodes.get(superseded_id)
        prompt = self_check_call.get("prompt") if isinstance(self_check_call, Mapping) else None
        if prior is not None and prior.get("edge") is not None and isinstance(prompt, str):
            prior_edge = tuple(prior["edge"])
            prior_line = (
                f"KIND={prior_edge[0]} | LEFT={prior_edge[1]} | "
                f"RELATION={prior_edge[2]} | RIGHT={prior_edge[3]}"
            )
            if "THIS IS A REVISION OF THE PRIOR TYPED EDGE:" not in prompt or prior_line not in prompt:
                errors.append(f"{path}: revision self-check prompt omits the superseded typed edge")
    if not isinstance(event.get("reason"), str) or not event["reason"].strip():
        errors.append(f"{path}.reason: required self-check reason")
    if event.get("model_visible") is not True:
        errors.append(f"{path}: status event must be model-visible")
    else:
        _visible_errors(event, path, errors, expected)
    if node_id in nodes and status in STATUSES:
        latest_status[node_id] = status
        nodes[node_id]["status"] = status
        nodes[node_id]["status_event_id"] = event.get("event_id")
        if status == "supported" and nodes[node_id].get("supersedes"):
            superseded_id = nodes[node_id]["supersedes"][0]
            if superseded_id in nodes:
                nodes[superseded_id]["superseded_by"] = node_id


def _corpus_node_state(trace: Mapping[str, Any]) -> tuple[
        dict[str, dict[str, Any]], list[str]]:
    """Replay final node eligibility and its exact append-only provenance.

    This replay is deliberately independent of the main cycle validator. A
    corpus is a derived artifact, so its membership and provenance must be
    recomputable from the event ledger rather than trusted from the runner.
    """
    gated = trace.get("condition") in {"self_check_no_drift", "self_check_drift"}
    nodes: dict[str, dict[str, Any]] = {}
    for event in trace.get("events", []):
        if not isinstance(event, Mapping):
            continue
        event_type = event.get("type")
        node_id = event.get("node_id")
        if not _nonempty(node_id):
            continue
        if event_type in MEMORY_EVENT_TYPES:
            nodes[node_id] = {
                "creation_event_id": event.get("event_id"),
                "status_event_id": None,
                "status": "provisional",
                "supersedes": list(event.get("supersedes", []))
                if isinstance(event.get("supersedes"), list) else [],
                "superseded_by": None,
            }
            if not gated and event_type == "REVISE_NODE":
                supersedes = nodes[node_id]["supersedes"]
                if len(supersedes) == 1 and supersedes[0] in nodes:
                    nodes[supersedes[0]]["superseded_by"] = node_id
        elif event_type == "STATUS_CHANGE" and node_id in nodes:
            nodes[node_id]["status"] = event.get("status")
            nodes[node_id]["status_event_id"] = event.get("event_id")
            if gated and event.get("status") == "supported":
                supersedes = nodes[node_id]["supersedes"]
                if len(supersedes) == 1 and supersedes[0] in nodes:
                    nodes[supersedes[0]]["superseded_by"] = node_id
    eligible = [
        node_id for node_id, node in nodes.items()
        if node.get("superseded_by") is None
        and (node.get("status") == "supported" if gated
             else node.get("status") == "provisional")
    ]
    return nodes, eligible


def validate_corpus(corpus: Mapping[str, Any], trace: Mapping[str, Any]) -> list[str]:
    """Validate each durable line's node and append-only event provenance."""
    errors: list[str] = []
    expected = _scope(trace)
    if not isinstance(corpus, Mapping):
        return ["corpus: must be an object"]
    if corpus.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"corpus: schema_version must be {SCHEMA_VERSION}")
    _scope_errors(corpus, expected, "corpus", errors)
    lines = corpus.get("lines")
    if not isinstance(lines, list) or not lines:
        errors.append("corpus.lines: must be a non-empty list")
        return errors
    event_to_node: dict[str, str] = {}
    node_to_edge: dict[str, tuple[str, ...]] = {}
    node_to_event: dict[str, str] = {}
    node_to_text: dict[str, str] = {}
    node_to_kind: dict[str, str] = {}
    visible_events: set[str] = set()
    known_nodes: set[str] = set()
    corpus_state, eligible_node_ids = _corpus_node_state(trace)
    for event in trace.get("events", []):
        if isinstance(event, Mapping) and _nonempty(event.get("event_id")):
            event_id = event["event_id"]
            if _nonempty(event.get("node_id")):
                event_to_node[event_id] = event["node_id"]
                known_nodes.add(event["node_id"])
                if event.get("type") in MEMORY_EVENT_TYPES:
                    node_to_event[event["node_id"]] = event_id
                    if all(_nonempty(event.get(key)) for key in ("left", "relation", "right")):
                        node_to_text[event["node_id"]] = canonical_corpus_text(
                            event["left"], event["relation"], event["right"]
                        )
                    if _nonempty(event.get("claim_kind")):
                        node_to_kind[event["node_id"]] = event["claim_kind"]
                if isinstance(event.get("edge"), list):
                    node_to_edge[event["node_id"]] = tuple(event["edge"])
            if event.get("model_visible") is True:
                visible_events.add(event_id)
    line_ids: set[str] = set()
    listed_node_ids: list[str] = []
    for index, line in enumerate(lines):
        path = f"corpus.lines[{index}]"
        if not isinstance(line, Mapping):
            errors.append(f"{path}: line must be an object")
            continue
        _scope_errors(line, expected, path, errors)
        line_id = line.get("line_id")
        if not _nonempty(line_id):
            errors.append(f"{path}: missing line_id")
        elif line_id in line_ids:
            errors.append(f"{path}: duplicate line_id")
        line_ids.add(line_id)
        if not _nonempty(line.get("text")):
            errors.append(f"{path}: text must be non-empty")
        if line.get("model_visible") is not True:
            errors.append(f"{path}: corpus line must be model-visible")
        else:
            _visible_errors(line, path, errors, expected)
        node_ids = _ids(line.get("node_ids"), f"{path}.node_ids", errors)
        if len(node_ids) != 1:
            errors.append(f"{path}.node_ids: canonical corpus line requires exactly one source node")
        for node_id in node_ids:
            if node_id not in known_nodes:
                errors.append(f"{path}: unknown node {node_id}")
            elif node_id not in eligible_node_ids:
                state = corpus_state.get(node_id, {})
                errors.append(
                    f"{path}: source node {node_id} is not condition-eligible, "
                    f"supported when gated, and live "
                    f"(status={state.get('status')}, "
                    f"superseded_by={state.get('superseded_by')})"
                )
        if len(node_ids) == 1:
            listed_node_ids.append(node_ids[0])
        if len(node_ids) == 1 and node_ids[0] in node_to_text:
            if line.get("text") != node_to_text[node_ids[0]]:
                errors.append(f"{path}.text: is not the canonical rendering of its source node")
            if line.get("claim_kind") != node_to_kind.get(node_ids[0]):
                errors.append(f"{path}.claim_kind: differs from its source node")
        if line.get("rendering") != "canonical_atomic_v0":
            errors.append(f"{path}.rendering: must be canonical_atomic_v0")
        if line.get("paraphrase_index") != 0:
            errors.append(f"{path}.paraphrase_index: must be zero")
        if line.get("exposure_count") != 1:
            errors.append(f"{path}.exposure_count: must be one")
        edge = line.get("edge")
        if not isinstance(edge, list) or len(edge) != 4 or not all(
                isinstance(item, str) and item for item in edge):
            errors.append(f"{path}.edge: must be an explicit canonical semantic edge")
        elif len(node_ids) == 1 and node_ids[0] in node_to_edge:
            if tuple(edge) != node_to_edge[node_ids[0]]:
                errors.append(f"{path}.edge: differs from its source node")
        provenance = line.get("provenance")
        if not isinstance(provenance, Mapping):
            errors.append(f"{path}.provenance: required object")
            continue
        _scope_errors(provenance, expected, f"{path}.provenance", errors)
        source_events = _ids(provenance.get("event_ids"), f"{path}.provenance.event_ids", errors)
        expected_events: list[Any] = []
        if len(node_ids) == 1:
            node_id = node_ids[0]
            state = corpus_state.get(node_id, {})
            expected_events = [state.get("creation_event_id", node_to_event.get(node_id))]
            if trace.get("condition") in {"self_check_no_drift", "self_check_drift"}:
                expected_events.append(state.get("status_event_id"))
        if len(node_ids) == 1 and source_events != expected_events:
            errors.append(
                f"{path}.provenance.event_ids: must name exactly the canonical "
                "node-creation/status events"
            )
        for event_id in source_events:
            if event_id not in event_to_node:
                errors.append(f"{path}: unknown provenance event {event_id}")
            elif event_id not in visible_events:
                errors.append(f"{path}: provenance event {event_id} is not model-visible")
            elif event_to_node[event_id] not in node_ids:
                errors.append(f"{path}: event {event_id} does not support a listed node")
    if listed_node_ids != eligible_node_ids:
        errors.append(
            "corpus.lines: must contain every and only condition-eligible live node "
            f"in creation order (expected {eligible_node_ids}, got {listed_node_ids})"
        )
    return errors


def _validate_call_reconciliation(trace: Mapping[str, Any], errors: list[str], *,
                                  cpu_fixture: bool) -> None:
    """Require a bijection between top-level calls and every nested call slot."""
    calls = trace.get("model_calls")
    cycles = trace.get("cycles")
    events = trace.get("events")
    if not isinstance(calls, list):
        errors.append("trace.model_calls: must be a complete call ledger")
        return
    if not isinstance(cycles, list) or not isinstance(events, list):
        return
    by_id: dict[str, Mapping[str, Any]] = {}
    for index, call in enumerate(calls):
        path = f"model_calls[{index}]"
        _check_call_record(call, path, errors, cpu_fixture=cpu_fixture)
        if not isinstance(call, Mapping):
            continue
        call_id = call.get("call_id")
        expected_id = f"call_{index:05d}"
        if call_id != expected_id:
            errors.append(f"{path}.call_id: expected append-only id {expected_id}")
        if isinstance(call_id, str):
            if call_id in by_id:
                errors.append(f"{path}.call_id: duplicate call identifier")
            by_id[call_id] = call

    events_by_cycle: dict[int, list[Mapping[str, Any]]] = {}
    for event in events:
        if isinstance(event, Mapping) and isinstance(event.get("cycle_index"), int):
            events_by_cycle.setdefault(event["cycle_index"], []).append(event)
    consumed: list[str] = []
    gated = trace.get("condition") in {"self_check_no_drift", "self_check_drift"}
    for cycle_index, cycle in enumerate(cycles):
        path = f"cycles[{cycle_index}]"
        if not isinstance(cycle, Mapping):
            continue
        nested: list[tuple[str, Mapping[str, Any]]] = []
        proposal = cycle.get("proposal_call")
        if isinstance(proposal, Mapping):
            nested.append(("proposal", proposal))
        operation = cycle.get("operation")
        if isinstance(operation, Mapping) and isinstance(operation.get("self_check_call"), Mapping):
            nested.append(("self_check", operation["self_check_call"]))
        for event in events_by_cycle.get(cycle_index, []):
            if event.get("type") == "STATUS_CHANGE" and isinstance(
                    event.get("self_check_call"), Mapping):
                nested.append(("self_check", event["self_check_call"]))
        if (isinstance(operation, Mapping)
                and isinstance(operation.get("self_check_call"), Mapping)
                and operation.get("self_check_raw_completion")
                != operation["self_check_call"].get("output")):
            errors.append(
                f"{path}.operation.self_check_raw_completion: differs from self-check call output"
            )
        proposal_slots = [call for kind, call in nested if kind == "proposal"]
        check_slots = [call for kind, call in nested if kind == "self_check"]
        if len(proposal_slots) != 1:
            errors.append(f"{path}: requires exactly one nested proposal call")
        expected_check = (
            gated and isinstance(operation, Mapping)
            and operation.get("kind") in {"ADD", "REVISE"}
        )
        if len(check_slots) != (1 if expected_check else 0):
            errors.append(
                f"{path}: condition/operation requires exactly "
                f"{1 if expected_check else 0} nested self-check call(s)"
            )
        ids = cycle.get("model_call_ids")
        if not isinstance(ids, list) or not all(isinstance(value, str) for value in ids):
            errors.append(f"{path}.model_call_ids: must be the exact nested call-id list")
            ids = []
        nested_ids = [call.get("call_id") for _, call in nested]
        if ids != nested_ids:
            errors.append(f"{path}.model_call_ids: differs from nested calls in execution order")
        for expected_kind, call in nested:
            call_id = call.get("call_id")
            top = by_id.get(call_id) if isinstance(call_id, str) else None
            if top is None:
                errors.append(f"{path}: nested {expected_kind} call is missing from model_calls")
                continue
            if not _same_call(call, top):
                errors.append(f"{path}: nested {expected_kind} call differs from model_calls ledger")
            if top.get("cycle_index") != cycle_index:
                errors.append(f"{path}: nested {expected_kind} call has wrong cycle_index")
            if top.get("kind") != expected_kind:
                errors.append(f"{path}: nested call kind differs from its semantic slot")
            consumed.append(call_id)
    if len(consumed) != len(set(consumed)):
        errors.append("trace.model_calls: one call is consumed by multiple nested slots")
    missing = sorted(set(by_id).difference(consumed))
    if missing:
        errors.append("trace.model_calls: unconsumed call records: " + ", ".join(missing))
    unknown = sorted(set(consumed).difference(by_id))
    if unknown:
        errors.append("trace.model_calls: nested calls absent from ledger: " + ", ".join(unknown))


def _schedule_errors(trace: Mapping[str, Any], errors: list[str]) -> None:
    """Validate the frozen WAKE/reactivation cadence encoded by the condition."""
    schedule = trace.get("schedule")
    if not isinstance(schedule, Mapping):
        errors.append("trace.schedule: required frozen schedule object")
        return
    every = schedule.get("reactivate_every")
    if not isinstance(every, int) or isinstance(every, bool) or every < 1:
        errors.append("trace.schedule.reactivate_every: must be a positive integer")
        return
    drift = trace.get("condition") in {"no_gate_drift", "self_check_drift"}
    if schedule.get("drift_enabled") is not drift:
        errors.append("trace.schedule.drift_enabled: differs from condition")
    if schedule.get("final_reactivation") is not drift:
        errors.append("trace.schedule.final_reactivation: differs from condition")
    cycles = trace.get("cycles")
    episodes = trace.get("episodes")
    if not isinstance(cycles, list) or not isinstance(episodes, list):
        return
    episode_ids = [
        episode.get("episode_id") for episode in episodes if isinstance(episode, Mapping)
    ]
    if not episode_ids:
        return
    events_by_cycle: dict[int, list[Mapping[str, Any]]] = {}
    for event in trace.get("events", []):
        if isinstance(event, Mapping) and isinstance(event.get("cycle_index"), int):
            events_by_cycle.setdefault(event["cycle_index"], []).append(event)
    gated = trace.get("condition") in {"self_check_no_drift", "self_check_drift"}
    schedule_nodes: dict[str, dict[str, Any]] = {}

    def newest() -> str | None:
        allowed = {"supported", "unresolved"} if gated else {"provisional"}
        for node_id in reversed(schedule_nodes):
            node = schedule_nodes[node_id]
            if node.get("superseded_by") is None and node.get("status") in allowed:
                return node_id
        return None

    expected_trigger: tuple[str, str, str] | None = ("WAKE", str(episode_ids[0]), "wake")
    wake_count = 0
    for cycle_index, cycle in enumerate(cycles):
        if not isinstance(cycle, Mapping) or not isinstance(cycle.get("trigger"), Mapping):
            continue
        actual = cycle["trigger"]
        if expected_trigger is None:
            errors.append(f"trace.schedule: unexpected extra cycle {cycle_index}")
            purpose = "extra"
        else:
            expected_kind, expected_id, purpose = expected_trigger
            if actual.get("kind") != expected_kind or actual.get("id") != expected_id:
                errors.append(
                    f"trace.schedule: cycle {cycle_index} expected "
                    f"{expected_kind}({expected_id}), got "
                    f"{actual.get('kind')}({actual.get('id')})"
                )

        for event in events_by_cycle.get(cycle_index, []):
            event_type = event.get("type")
            node_id = event.get("node_id")
            if event_type in MEMORY_EVENT_TYPES and isinstance(node_id, str):
                supersedes = event.get("supersedes")
                schedule_nodes[node_id] = {
                    "status": "provisional", "supersedes": supersedes,
                    "superseded_by": None,
                }
                if (not gated and event_type == "REVISE_NODE"
                        and isinstance(supersedes, list) and len(supersedes) == 1
                        and supersedes[0] in schedule_nodes):
                    schedule_nodes[supersedes[0]]["superseded_by"] = node_id
            elif event_type == "STATUS_CHANGE" and isinstance(node_id, str) \
                    and node_id in schedule_nodes:
                status = event.get("status")
                schedule_nodes[node_id]["status"] = status
                supersedes = schedule_nodes[node_id].get("supersedes")
                if (status == "supported" and isinstance(supersedes, list)
                        and len(supersedes) == 1 and supersedes[0] in schedule_nodes):
                    schedule_nodes[supersedes[0]]["superseded_by"] = node_id

        if purpose == "wake":
            wake_count += 1
            candidate = newest()
            if drift and wake_count % every == 0 and candidate is not None:
                expected_trigger = ("REACTIVATE", candidate, "periodic")
            elif wake_count < len(episode_ids):
                expected_trigger = ("WAKE", str(episode_ids[wake_count]), "wake")
            elif drift and candidate is not None:
                expected_trigger = ("REACTIVATE", candidate, "final")
            else:
                expected_trigger = None
        elif purpose == "periodic":
            candidate = newest()
            if wake_count < len(episode_ids):
                expected_trigger = ("WAKE", str(episode_ids[wake_count]), "wake")
            elif drift and candidate is not None:
                expected_trigger = ("REACTIVATE", candidate, "final")
            else:
                expected_trigger = None
        elif purpose == "final":
            expected_trigger = None
    if expected_trigger is not None:
        errors.append(
            f"trace.schedule: missing required {expected_trigger[0]}({expected_trigger[1]}) "
            "at end of trace"
        )


def validate_trace(trace: Mapping[str, Any]) -> list[str]:
    """Return all deterministic violations in one micro-dream trace."""
    errors: list[str] = []
    if not isinstance(trace, Mapping):
        return ["trace: must be an object"]
    if trace.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"trace: schema_version must be {SCHEMA_VERSION}")
    if trace.get("split") not in SPLITS:
        errors.append("trace: split must be train, dev, test, or holdout")
    if trace.get("condition") not in CONDITIONS:
        errors.append("trace: condition must be one frozen honesty-ladder condition")
    cpu_fixture = trace.get("cpu_fixture", False)
    if not isinstance(cpu_fixture, bool):
        errors.append("trace.cpu_fixture: must be boolean when present")
        cpu_fixture = False
    for key in ("trace_id", "split_id", "world_id", "skin_id", "life_id", "loop_adapter_id"):
        if not _nonempty(trace.get(key)):
            errors.append(f"trace: missing non-empty {key}")
    memory_mode = trace.get("memory_mode", "mounted")
    memory_id = trace.get("memory_adapter_id")
    if memory_mode not in {"mounted", "none"}:
        errors.append("trace: memory_mode must be mounted or none")
    if memory_mode == "mounted" and not _nonempty(memory_id):
        errors.append("trace: mounted memory requires memory_adapter_id")
    if memory_mode == "none" and memory_id is not None:
        errors.append("trace: memory_mode=none requires null memory_adapter_id")
    _schedule_errors(trace, errors)
    expected = _scope(trace)
    episode_list = trace.get("episodes")
    if not isinstance(episode_list, list) or not episode_list:
        errors.append("trace.episodes: must be a non-empty list")
        return errors
    episodes: dict[str, dict[str, Any]] = {}
    experiences: dict[str, tuple[int, str]] = {}
    for index, episode in enumerate(episode_list):
        path = f"episodes[{index}]"
        _scope_errors(episode, expected, path, errors)
        if not isinstance(episode, Mapping):
            continue
        if episode.get("episode_index") != index:
            errors.append(f"{path}: episode_index must be contiguous")
        episode_id = episode.get("episode_id")
        if not _nonempty(episode_id):
            errors.append(f"{path}: missing episode_id")
            continue
        if episode_id in episodes:
            errors.append(f"{path}: duplicate episode_id")
        episodes[episode_id] = dict(episode)
        exp_ids = _ids(episode.get("experience_ids"), f"{path}.experience_ids", errors)
        for experience_id in exp_ids:
            if experience_id in experiences:
                errors.append(f"{path}: experience {experience_id} appears twice")
            experiences[experience_id] = (index, episode_id)

    cycles = trace.get("cycles")
    events = trace.get("events")
    if not isinstance(cycles, list) or not cycles:
        errors.append("trace.cycles: must be a non-empty list")
        return errors
    if not isinstance(events, list):
        errors.append("trace.events: must be a list")
        events = []
    events_by_cycle: dict[int, list[Mapping[str, Any]]] = {}
    for event in events:
        if isinstance(event, Mapping) and isinstance(event.get("cycle_index"), int):
            events_by_cycle.setdefault(event["cycle_index"], []).append(event)

    nodes: dict[str, dict[str, Any]] = {}
    event_ids: set[str] = set()
    referenced_event_ids: set[str] = set()
    seen_cycle_ids: set[str] = set()
    latest_status: dict[str, str] = {}
    visible_lifetime_rows: list[str] = []
    event_cursor = 0
    previous_event_id: str | None = None
    for cycle_index, cycle in enumerate(cycles):
        path = f"cycles[{cycle_index}]"
        _scope_errors(cycle, expected, path, errors)
        if not isinstance(cycle, Mapping):
            continue
        if cycle.get("cycle_index") != cycle_index or cycle.get("microdream_index") != cycle_index:
            errors.append(f"{path}: cycle/microdream index must be contiguous")
        cycle_id = cycle.get("cycle_id")
        if not _nonempty(cycle_id):
            errors.append(f"{path}: missing cycle_id")
        elif cycle_id in seen_cycle_ids:
            errors.append(f"{path}: duplicate cycle_id")
        if _nonempty(cycle_id):
            seen_cycle_ids.add(cycle_id)
        trigger = cycle.get("trigger")
        if not isinstance(trigger, Mapping) or trigger.get("kind") not in TRIGGER_KINDS or not _nonempty(trigger.get("id")):
            errors.append(f"{path}.trigger: must be WAKE/REACTIVATE with an id")
            trigger = {}
        trigger_kind = trigger.get("kind")
        trigger_id = trigger.get("id")
        episode_id = cycle.get("episode_id")
        current_experience_ids: set[str] = set()
        episode_index: int | None = None
        current_episode_id: str | None = None
        if trigger_kind == "WAKE":
            if not _nonempty(episode_id) or episode_id != trigger_id:
                errors.append(f"{path}: WAKE must name its current episode as trigger id")
            episode = episodes.get(trigger_id)
            if episode is None:
                errors.append(f"{path}: WAKE refers to unknown episode")
            else:
                episode_index = episode["episode_index"]
                if episode_index > cycle_index:
                    errors.append(f"{path}: WAKE episode is from the future")
                current_episode_id = trigger_id
                current_experience_ids = set(_ids(
                    cycle.get("experience_ids"), f"{path}.experience_ids", errors
                ))
                if not current_experience_ids.issubset(set(episode.get("experience_ids", []))):
                    errors.append(f"{path}: WAKE experience is not in its current episode")
        elif trigger_kind == "REACTIVATE":
            if episode_id is not None:
                errors.append(f"{path}: REACTIVATE must not carry a current episode")
            if cycle.get("experience_ids") not in (None, []):
                errors.append(f"{path}: REACTIVATE must not carry current experience")
            trigger_node = nodes.get(trigger_id)
            if trigger_node is None:
                errors.append(f"{path}: REACTIVATE trigger node must be an earlier node")
            else:
                episode_index = cycle_index
                current_episode_id = None
        public_state = cycle.get("public_state", {})
        _check_text_hash(cycle.get("model_prompt"),
                         cycle.get("model_prompt_sha256"),
                         f"{path}.model_prompt", errors)
        if _nonempty(cycle.get("model_prompt")):
            _visible_errors(cycle["model_prompt"], f"{path}.model_prompt", errors)
        if trigger_kind == "WAKE":
            visible_lifetime_rows.extend(
                public_rows_from_prompt(cycle.get("model_prompt"))
            )
        proposal_call = cycle.get("proposal_call")
        _check_call_record(
            proposal_call, f"{path}.proposal_call", errors,
            expected_prompt=cycle.get("model_prompt"), cpu_fixture=cpu_fixture,
        )
        proposal_output = (
            proposal_call.get("output") if isinstance(proposal_call, Mapping) else None
        )
        for field_name, value in (("public_state", public_state),
                                   ("tool_env_result", cycle.get("tool_env_result", {})),
                                   ("next_state", cycle.get("next_state", {}))):
            if not isinstance(value, Mapping):
                errors.append(f"{path}.{field_name}: must be an object")
            else:
                _visible_errors(value, f"{path}.{field_name}", errors, expected)
        retrieved_ids = _ids(cycle.get("retrieved_node_ids"), f"{path}.retrieved_node_ids", errors,
                             allow_empty=True)
        for node_id in retrieved_ids:
            if node_id not in nodes or nodes[node_id]["created_cycle"] >= cycle_index:
                errors.append(f"{path}: retrieved node is not temporally available")
                continue
            if nodes[node_id].get("superseded_by") is not None:
                errors.append(f"{path}: retrieved node was already superseded")
            if (trace.get("condition") in {"self_check_no_drift", "self_check_drift"}
                    and latest_status.get(node_id, "provisional")
                    not in {"supported", "unresolved"}):
                errors.append(f"{path}: gated retrieval used a node without a valid self-check status")
        if trigger_kind == "REACTIVATE" and trigger_id not in retrieved_ids:
            errors.append(f"{path}: REACTIVATE must retrieve its triggering node")
        visible_ids = set(retrieved_ids) | current_experience_ids
        if current_episode_id is not None:
            visible_ids.add(current_episode_id)
        proposal_context = ProposalContext(
            visible_ids=frozenset(visible_ids),
            episode_ids=frozenset(episodes),
            experience_ids=frozenset(experiences),
            node_ids=frozenset(nodes),
            retrieved_node_ids=tuple(retrieved_ids),
            nodes=nodes,
            public_tokens=public_tokens(visible_lifetime_rows),
            trigger_node_id=trigger_id if trigger_kind == "REACTIVATE" else None,
        )
        proposal_decision = classify_proposal(proposal_output, proposal_context)
        operation = cycle.get("operation")
        if not isinstance(operation, Mapping):
            errors.append(f"{path}.operation: exactly one operation object is required")
            operation = {}
        if "operations" in cycle or "operations" in operation:
            errors.append(f"{path}: more than one cognitive operation is forbidden")
        if operation.get("kind") not in OPERATIONS | OBSERVED_OPERATIONS:
            errors.append(f"{path}.operation.kind: must be ADD, REVISE, OPEN_QUESTION, PASS, or MALFORMED")
        if not _nonempty(operation.get("op_id")):
            errors.append(f"{path}.operation: missing op_id")
        if operation.get("model_visible") is not True:
            errors.append(f"{path}.operation: operation target must be model-visible")
        else:
            _visible_errors(operation, f"{path}.operation", errors, expected)
        _check_tokens(operation, f"{path}.operation", errors)
        if operation.get("raw_completion") != proposal_output:
            errors.append(f"{path}.operation.raw_completion: differs from proposal_call output")
        if operation.get("kind") == "MALFORMED":
            if not _nonempty(operation.get("raw_completion")):
                errors.append(f"{path}.operation: MALFORMED requires raw_completion")
            if not _nonempty(operation.get("parse_error")):
                errors.append(f"{path}.operation: MALFORMED requires parse_error")
        parsed_proposal = _proposal_binding_errors(
            operation, proposal_output, f"{path}.operation", errors,
            decision=proposal_decision,
        )
        if operation.get("kind") == "OPEN_QUESTION":
            if "question" in operation:
                errors.append(f"{path}.operation.question: freeform OPEN_QUESTION text is forbidden")
            for key in ("claim_kind", "left", "relation", "right"):
                if not _nonempty(operation.get(key)):
                    errors.append(f"{path}.operation.{key}: required typed OPEN_QUESTION field")
            if operation.get("claim_kind") not in CLAIM_KINDS:
                errors.append(f"{path}.operation.claim_kind: must be a supported typed claim kind")
            question_edge = ParsedMicrodream(
                operation="add", claim_kind=operation.get("claim_kind"),
                left=operation.get("left"), relation=operation.get("relation"),
                right=operation.get("right"),
            )
            for error in local_edge_errors(question_edge):
                errors.append(f"{path}.operation.edge: {error}")
            for key in ("cited_episode_ids", "cited_experience_ids", "cited_node_ids"):
                if key not in operation:
                    errors.append(f"{path}.operation: missing explicit {key}")
            _check_temporal_ids(
                cited_episode_ids=operation.get("cited_episode_ids"),
                cited_experience_ids=operation.get("cited_experience_ids"),
                cited_node_ids=operation.get("cited_node_ids"),
                retrieved_node_ids=cycle.get("retrieved_node_ids"),
                path=f"{path}.operation", cycle_index=cycle_index,
                episode_index=episode_index, current_episode_id=current_episode_id,
                current_experience_ids=current_experience_ids,
                episodes=episodes, experiences=experiences, nodes=nodes,
                errors=errors,
            )
            if not any(operation.get(key) for key in (
                    "cited_episode_ids", "cited_experience_ids", "cited_node_ids")):
                errors.append(f"{path}.operation: OPEN_QUESTION requires at least one citation")
            if not set(operation.get("cited_node_ids", [])) <= set(retrieved_ids):
                errors.append(f"{path}.operation: cited_node_ids must be a subset of cycle retrieval")
            if trigger_kind == "REACTIVATE":
                if trigger_id not in operation.get("cited_node_ids", []):
                    errors.append(
                        f"{path}.operation: REACTIVATE OPEN_QUESTION must cite its trigger"
                    )
                trigger_node = nodes.get(trigger_id)
                question_edge = (
                    canonical_edge(question_edge)
                    if all(_nonempty(getattr(question_edge, field)) for field in (
                        "claim_kind", "left", "relation", "right"
                    )) else None
                )
                if (trigger_node is not None and trigger_node.get("edge") is not None
                        and question_edge is not None):
                    trigger_edge = tuple(trigger_node["edge"])
                    if not {question_edge[1], question_edge[3]}.intersection(
                            {trigger_edge[1], trigger_edge[3]}):
                        errors.append(
                            f"{path}.operation: REACTIVATE OPEN_QUESTION is unrelated to its trigger"
                        )

        cycle_event_ids = _ids(cycle.get("event_ids"), f"{path}.event_ids", errors, allow_empty=True)
        for event_id in cycle_event_ids:
            if event_id in referenced_event_ids:
                errors.append(f"{path}: event {event_id} is referenced by two cycles")
            referenced_event_ids.add(event_id)
        cycle_events = events_by_cycle.get(cycle_index, [])
        if len(cycle_event_ids) != len(cycle_events):
            errors.append(f"{path}: event_ids do not match events for this cycle")
        event_map = {event.get("event_id"): event for event in cycle_events}
        memory_events = 0
        cycle_memory_events: list[Mapping[str, Any]] = []
        cycle_status_events: list[Mapping[str, Any]] = []
        for event_id in cycle_event_ids:
            event = event_map.get(event_id)
            if event is None:
                errors.append(f"{path}: unknown event_id {event_id}")
                continue
            event_path = f"events[{event.get('event_index', '?')}]"
            _scope_errors(event, expected, event_path, errors)
            if event.get("event_index") != event_cursor:
                errors.append(f"{event_path}: event_index must be append-only and contiguous")
            if event.get("prev_event_id") != previous_event_id:
                errors.append(f"{event_path}: prev_event_id does not continue append-only ledger")
            if event.get("cycle_index") != cycle_index or event.get("microdream_index") != cycle_index:
                errors.append(f"{event_path}: event cycle index mismatch")
            if event.get("trigger") != dict(trigger):
                errors.append(f"{event_path}: event trigger differs from cycle trigger")
            if event.get("retrieved_node_ids") != retrieved_ids:
                errors.append(f"{event_path}: retrieved_node_ids must exactly equal cycle retrieval")
            if not set(event.get("cited_node_ids", [])) <= set(retrieved_ids):
                errors.append(f"{event_path}: cited_node_ids must be a subset of cycle retrieval")
            event_key = event.get("event_id")
            if not _nonempty(event_key):
                errors.append(f"{event_path}: missing event_id")
            elif event_key in event_ids:
                errors.append(f"{event_path}: duplicate event_id")
            if _nonempty(event_key):
                event_ids.add(event_key)
            event_type = event.get("type")
            if event_type not in EVENT_TYPES:
                errors.append(f"{event_path}: unknown event type")
            elif event_type in MEMORY_EVENT_TYPES:
                memory_events += 1
                cycle_memory_events.append(event)
                if event.get("raw_completion") != proposal_output:
                    errors.append(f"{event_path}.raw_completion: differs from proposal_call output")
                _memory_event_binding_errors(event, parsed_proposal, event_path, errors)
                checked_node_id = _check_node_event(
                    event, event_path, event_type=event_type,
                    cycle_index=cycle_index, episode_index=episode_index,
                    current_episode_id=current_episode_id,
                    current_experience_ids=current_experience_ids,
                    expected=expected, episodes=episodes, experiences=experiences,
                    nodes=nodes, errors=errors,
                )
                if trigger_kind == "REACTIVATE" and trigger_id not in event.get("cited_node_ids", []):
                    errors.append(f"{event_path}: REACTIVATE must cite its triggering node")
                if (trigger_kind == "REACTIVATE" and trigger_id in nodes
                        and isinstance(event.get("edge"), list)
                        and len(event["edge"]) == 4
                        and nodes[trigger_id].get("edge") is not None):
                    new_edge = tuple(event["edge"])
                    trigger_edge = tuple(nodes[trigger_id]["edge"])
                    if not {new_edge[1], new_edge[3]}.intersection(
                            {trigger_edge[1], trigger_edge[3]}):
                        errors.append(
                            f"{event_path}: REACTIVATE edge does not locally extend its trigger"
                        )
                if (event_type == "REVISE_NODE" and checked_node_id is not None
                        and trace.get("condition") in {"no_gate_no_drift", "no_gate_drift"}):
                    supersedes = event.get("supersedes")
                    if isinstance(supersedes, list) and len(supersedes) == 1 \
                            and supersedes[0] in nodes:
                        nodes[supersedes[0]]["superseded_by"] = checked_node_id
                if _nonempty(event_key):
                    latest_status[event.get("node_id")] = "provisional"
            else:
                cycle_status_events.append(event)
                _check_status_event(
                    event, event_path, cycle_index=cycle_index,
                    episode_index=episode_index, current_episode_id=current_episode_id,
                    current_experience_ids=current_experience_ids,
                    expected=expected, episodes=episodes, experiences=experiences,
                    nodes=nodes, latest_status=latest_status, errors=errors,
                    cpu_fixture=cpu_fixture,
                    proposal_decision=proposal_decision,
                    proposal_context=proposal_context,
                )
            if _nonempty(event_key):
                previous_event_id = event_key
            event_cursor += 1
        expected_memory_events = {"ADD": 1, "REVISE": 1,
                                  "OPEN_QUESTION": 0, "PASS": 0,
                                  "MALFORMED": 0}.get(operation.get("kind"))
        if expected_memory_events is not None and memory_events != expected_memory_events:
            errors.append(f"{path}: {operation.get('kind')} requires exactly "
                          f"{expected_memory_events} memory event(s), got {memory_events}")
        gated_cycle = trace.get("condition") in {"self_check_no_drift", "self_check_drift"}
        if cycle_status_events:
            if (not gated_cycle or operation.get("kind") not in {"ADD", "REVISE"}
                    or len(cycle_memory_events) != 1):
                errors.append(
                    f"{path}: STATUS_CHANGE requires one gated ADD/REVISE node "
                    "created in the same cycle"
                )
            if len(cycle_status_events) != 1:
                errors.append(f"{path}: at most one STATUS_CHANGE is allowed per cycle")
            if len(cycle_memory_events) == 1:
                created = cycle_memory_events[0]
                status_event = cycle_status_events[0]
                if status_event.get("node_id") != created.get("node_id"):
                    errors.append(
                        f"{path}: STATUS_CHANGE node_id must equal the sole node "
                        "created by this cycle"
                    )
                if status_event.get("prev_event_id") != created.get("event_id"):
                    errors.append(
                        f"{path}: STATUS_CHANGE must immediately append to its "
                        "node-creation event"
                    )

    if len(referenced_event_ids) != len(events):
        errors.append("trace.events: every event must belong to exactly one cycle")
    for index, event in enumerate(events):
        if isinstance(event, Mapping) and event.get("event_index") != index:
            errors.append(f"events[{index}]: event_index must be contiguous")
    _validate_call_reconciliation(trace, errors, cpu_fixture=cpu_fixture)
    _, eligible_corpus_nodes = _corpus_node_state(trace)
    if trace.get("corpus") is not None:
        errors.extend(validate_corpus(trace["corpus"], trace))
    elif eligible_corpus_nodes:
        errors.append(
            "trace.corpus: missing corpus for condition-eligible live nodes "
            + ", ".join(eligible_corpus_nodes)
        )
    return errors


def validate_dataset(traces: Sequence[Mapping[str, Any]]) -> list[str]:
    """Validate traces plus world splits, globally unique IDs, and life reset."""
    if not isinstance(traces, Sequence) or isinstance(traces, (str, bytes)):
        return ["dataset: must be a sequence of traces"]
    errors: list[str] = []
    seen: dict[str, set[str]] = {key: set() for key in
                                  ("trace_id", "episode_id", "cycle_id", "event_id",
                                   "node_id", "line_id")}
    worlds: dict[str, str] = {}
    split_ids: dict[str, str] = {}
    life_scopes: dict[str, tuple[Any, Any, Any]] = {}
    life_memory: dict[str, str | None] = {}
    memory_lives: dict[str, str] = {}
    for index, trace in enumerate(traces):
        errors.extend(f"trace[{index}]: {error}" for error in validate_trace(trace))
        if not isinstance(trace, Mapping):
            continue
        value = trace.get("trace_id")
        if _nonempty(value) and value in seen["trace_id"]:
            errors.append(f"trace_id {value}: reused across traces")
        if _nonempty(value):
            seen["trace_id"].add(value)
        world_id, skin_id, life_id = _scope(trace)
        split = trace.get("split")
        split_id = trace.get("split_id")
        if _nonempty(world_id) and split in SPLITS:
            old = worlds.setdefault(world_id, split)
            if old != split:
                errors.append(f"world {world_id}: appears in multiple splits ({old}, {split})")
        if _nonempty(split_id) and split in SPLITS:
            old = split_ids.setdefault(split_id, split)
            if old != split:
                errors.append(f"split_id {split_id}: crosses split boundaries")
        scope = (world_id, skin_id, life_id)
        if _nonempty(life_id):
            old_scope = life_scopes.setdefault(life_id, scope)
            if old_scope != scope:
                errors.append(f"life {life_id}: crosses world/skin scope")
            memory = trace.get("memory_adapter_id")
            old_memory = life_memory.setdefault(life_id, memory)
            if old_memory != memory:
                errors.append(f"life {life_id}: memory adapter changes within a life")
            if _nonempty(memory):
                old_life = memory_lives.setdefault(memory, life_id)
                if old_life != life_id:
                    errors.append(f"memory adapter {memory}: reused across lives")
        for key, values in (
            ("episode_id", [e.get("episode_id") for e in trace.get("episodes", [])
                             if isinstance(e, Mapping)]),
            ("cycle_id", [c.get("cycle_id") for c in trace.get("cycles", []) if isinstance(c, Mapping)]),
            ("event_id", [e.get("event_id") for e in trace.get("events", []) if isinstance(e, Mapping)]),
            ("node_id", [e.get("node_id") for e in trace.get("events", [])
                          if isinstance(e, Mapping) and e.get("type") in MEMORY_EVENT_TYPES]),
            ("line_id", [l.get("line_id") for l in trace.get("corpus", {}).get("lines", [])
                          if isinstance(trace.get("corpus"), Mapping) and isinstance(l, Mapping)]),
        ):
            for item in values:
                if _nonempty(item) and item in seen[key]:
                    errors.append(f"{key} {item}: reused across traces")
                if _nonempty(item):
                    seen[key].add(item)
    return errors


def protocol_noncompliance(trace: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Report observed non-model/fault outputs without rewriting the trace."""
    if not isinstance(trace, Mapping):
        return []
    findings: list[dict[str, Any]] = []
    for cycle in trace.get("cycles", []):
        if not isinstance(cycle, Mapping):
            continue
        operation = cycle.get("operation")
        if isinstance(operation, Mapping) and operation.get("kind") == "MALFORMED":
            findings.append({
                "kind": "malformed_output",
                "cycle_index": cycle.get("cycle_index"),
                "op_id": operation.get("op_id"),
                "raw_completion": operation.get("raw_completion"),
                "parse_error": operation.get("parse_error"),
            })
        proposal_call = cycle.get("proposal_call")
        if (isinstance(proposal_call, Mapping)
                and isinstance(proposal_call.get("usage"), Mapping)
                and proposal_call["usage"].get("source") == "scripted_fallback"):
            findings.append({
                "kind": "scripted_fallback",
                "cycle_index": cycle.get("cycle_index"),
                "call": "proposal_call",
            })
    for event in trace.get("events", []):
        if not isinstance(event, Mapping) or event.get("type") != "STATUS_CHANGE":
            continue
        call = event.get("self_check_call")
        if (isinstance(call, Mapping) and isinstance(call.get("usage"), Mapping)
                and call["usage"].get("source") == "scripted_fallback"):
            findings.append({
                "kind": "scripted_fallback",
                "cycle_index": event.get("cycle_index"),
                "event_id": event.get("event_id"),
                "call": "self_check_call",
            })
    return findings


def lineage_depth_report(trace: Mapping[str, Any]) -> dict[str, Any]:
    """Separate raw structural depth from fully model-supported lineage depth.

    Raw depth intentionally records local graph growth through provisional or
    unresolved nodes.  A paper-facing supported lineage may only traverse nodes
    whose final self-check status is ``supported``; otherwise a later supported
    edge could misleadingly inherit depth from an unresolved chain.
    """
    memory_events: list[Mapping[str, Any]] = []
    statuses: dict[str, str] = {}
    for event in trace.get("events", []) if isinstance(trace, Mapping) else []:
        if not isinstance(event, Mapping):
            continue
        node_id = event.get("node_id")
        if not isinstance(node_id, str):
            continue
        if event.get("type") in MEMORY_EVENT_TYPES:
            memory_events.append(event)
            statuses[node_id] = str(event.get("status", "provisional"))
        elif event.get("type") == "STATUS_CHANGE" and isinstance(event.get("status"), str):
            statuses[node_id] = event["status"]

    supported_depths: dict[str, int] = {}
    rows: dict[str, dict[str, Any]] = {}
    edges: dict[str, tuple[str, str, str, str]] = {}
    for event in memory_events:
        node_id = event["node_id"]
        raw_edge = event.get("edge")
        edge = (
            tuple(raw_edge) if isinstance(raw_edge, list) and len(raw_edge) == 4
            and all(isinstance(value, str) for value in raw_edge) else None
        )
        if edge is not None:
            edges[node_id] = edge  # type: ignore[assignment]
        status = statuses.get(node_id, "provisional")
        supported_depth = 0
        if status == "supported" and edge is not None:
            supersedes = event.get("supersedes")
            if isinstance(supersedes, list) and len(supersedes) == 1:
                supported_depth = max(1, supported_depths.get(supersedes[0], 0))
            else:
                endpoints = {edge[1], edge[3]}
                extending = []
                cited = event.get("cited_node_ids")
                if isinstance(cited, list):
                    for prior_id in cited:
                        prior_edge = edges.get(prior_id)
                        prior_depth = supported_depths.get(prior_id, 0)
                        if (prior_edge is not None and prior_depth > 0
                                and prior_edge[1:] != edge[1:]
                                and endpoints.intersection({prior_edge[1], prior_edge[3]})):
                            extending.append(prior_depth)
                supported_depth = 1 + max(extending, default=0)
        supported_depths[node_id] = supported_depth
        raw_depth = event.get("depth")
        rows[node_id] = {
            "final_status": status,
            "raw_depth": raw_depth if isinstance(raw_depth, int) else None,
            "supported_lineage_depth": supported_depth,
        }
    raw_values = [
        row["raw_depth"] for row in rows.values() if isinstance(row["raw_depth"], int)
    ]
    return {
        "by_node": rows,
        "max_raw_depth": max(raw_values, default=0),
        "max_supported_lineage_depth": max(supported_depths.values(), default=0),
    }


def audit_trace(trace: Mapping[str, Any]) -> dict[str, Any]:
    """Return structural validity and observed protocol deviations separately."""
    errors = validate_trace(trace)
    return {
        "valid": not errors,
        "errors": errors,
        "protocol_noncompliance": protocol_noncompliance(trace),
        "lineage_depth": lineage_depth_report(trace),
    }


def assert_valid_trace(trace: Mapping[str, Any]) -> None:
    errors = validate_trace(trace)
    if errors:
        raise ContractError("invalid micro-dream trace:\n- " + "\n- ".join(errors))


def assert_valid_dataset(traces: Sequence[Mapping[str, Any]]) -> None:
    errors = validate_dataset(traces)
    if errors:
        raise ContractError("invalid micro-dream dataset:\n- " + "\n- ".join(errors))


__all__ = [
    "ContractError", "EVENT_TYPES", "MEMORY_EVENT_TYPES", "OBSERVED_OPERATIONS", "OPERATIONS",
    "SCHEMA_VERSION", "STATUSES", "TRIGGER_KINDS", "assert_valid_dataset",
    "assert_valid_trace", "audit_trace", "lineage_depth_report", "protocol_noncompliance", "validate_corpus",
    "validate_dataset", "validate_trace",
]
