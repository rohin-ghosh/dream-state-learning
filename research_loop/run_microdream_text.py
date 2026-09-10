"""Run one bounded, text-only recurrent microdream life.

This entry point deliberately has no scoring or latent-world path.  It exports
the public Semantic World lifetime, gives that export to the recurrent driver,
and atomically publishes an auditable artifact directory.  A memory LoRA is
never mounted in this condition; it is the pre-transport text control.
"""

from __future__ import annotations

import argparse
from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
from typing import Any, Protocol

from alchemy.backend import make_backend
from lands.skins import all_skin_names
from research_loop.microdream_classification import (
    ProposalContext,
    classify_proposal,
    classify_self_check,
    public_tokens,
)
from research_loop.microdream_contract import audit_trace
from research_loop.microdream_prompts import (
    parse_microdream,
    render_microdream_prompt,
    render_self_check_prompt,
)
from research_loop.microdream_runner import CONDITIONS, _node_prompt, run_recurrent_life
from research_loop.microdream_world import export_semantic_world


DEFAULT_MODEL = "Qwen/Qwen2.5-32B-Instruct"
DEFAULT_REVISION = "5ede1c97bbab6ce5cda5812749b4c0bdf79b18dd"
ARTIFACT_SCHEMA_VERSION = "recurrent-microdream-text-dev-v0.2"
PUBLIC_WORLD_FAMILY = "semantic_world_v0.2"
_EXACT_USAGE_FIELDS = frozenset({
    "prompt_tokens", "output_tokens", "original_prompt_tokens",
    "prompt_truncated", "source", "prompt_token_ids_sha256",
    "supplied_prompt_token_ids_sha256", "output_token_ids",
    "output_token_ids_sha256", "decoded_output", "decoded_output_sha256",
    "output_sha256",
})


class Backend(Protocol):
    """The narrow backend surface used by this text-only runner."""

    last_usage: Sequence[Mapping[str, Any]]

    def generate(
        self,
        prompts: Sequence[str],
        *,
        max_tokens: int,
        temperature: float,
        seed: int,
    ) -> Sequence[str]: ...


Runner = Callable[..., dict[str, Any]]
Exporter = Callable[[int, str], dict[str, Any]]


@dataclass(frozen=True)
class TextRunConfig:
    output_dir: Path
    backend: str = "vllm"
    model: str = DEFAULT_MODEL
    revision: str = DEFAULT_REVISION
    condition: str = "self_check_drift"
    seed: int = 0
    skin: str = "aligned"
    split: str = "dev"
    split_id: str = "recurrent-microdream-text-dev"
    max_output_tokens: int = 128
    temperature: float = 0.0
    retrieval_limit: int = 3
    reactivate_every: int = 2
    max_model_len: int = 32768
    gpu_util: float = 0.85

    def validate(self) -> None:
        if self.backend not in {"hf", "vllm"}:
            raise ValueError(f"unsupported backend {self.backend!r}")
        if self.condition not in CONDITIONS:
            raise ValueError(f"unsupported condition {self.condition!r}")
        if self.skin not in all_skin_names():
            raise ValueError(f"unsupported skin {self.skin!r}")
        for name in ("model", "revision", "split", "split_id"):
            if not getattr(self, name).strip():
                raise ValueError(f"{name} must be non-empty")
        if self.split != "dev":
            raise ValueError("recurrent microdream text artifacts are dev-only (split must be 'dev')")
        for name in (
            "max_output_tokens", "retrieval_limit", "reactivate_every",
            "max_model_len",
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise ValueError(f"{name} must be a positive integer")
        if self.temperature < 0:
            raise ValueError("temperature must be non-negative")
        if not 0 < self.gpu_util <= 1:
            raise ValueError("gpu_util must be in (0, 1]")


def _canonical_json(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def _canonical_jsonl(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=True, sort_keys=True,
                   separators=(",", ":")) + "\n"
    ).encode("utf-8")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(directory: Path, name: str, value: Any) -> None:
    path = directory / name
    path.write_bytes(_canonical_json(value))


def _write_jsonl(directory: Path, name: str, rows: Sequence[Mapping[str, Any]]) -> None:
    path = directory / name
    path.write_bytes(b"".join(_canonical_jsonl(row) for row in rows))


def _sha256_canonical(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=True, sort_keys=True,
                   separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _bundle_binding_error(message: str) -> None:
    raise RuntimeError(f"bundle binding failed: {message}")


def _validate_public_export_hashes(public_export: Mapping[str, Any]) -> None:
    """Verify the public lifetime records before they become model input."""
    if not isinstance(public_export, Mapping):
        _bundle_binding_error("public_export must be an object")
    episodes = public_export.get("episodes")
    life = public_export.get("life")
    if not isinstance(episodes, list) or not episodes:
        _bundle_binding_error("public_export.episodes must be a non-empty list")
    if not isinstance(life, Mapping):
        _bundle_binding_error("public_export.life must be an object")

    all_rows: list[Mapping[str, Any]] = []
    seen_row_ids: set[str] = set()
    expected_row_index = 0
    for episode_index, episode in enumerate(episodes):
        path = f"public_export.episodes[{episode_index}]"
        if not isinstance(episode, Mapping):
            _bundle_binding_error(f"{path} must be an object")
        episode_id = episode.get("episode_id")
        rows = episode.get("rows")
        if (not isinstance(episode_id, str) or not episode_id
                or episode.get("episode_index") != episode_index
                or not isinstance(rows, list) or not rows):
            _bundle_binding_error(f"{path} has invalid episode identity or rows")
        if episode.get("first_row_index") != expected_row_index:
            _bundle_binding_error(f"{path}.first_row_index is not temporal")
        for row_position, row in enumerate(rows):
            row_path = f"{path}.rows[{row_position}]"
            if not isinstance(row, Mapping):
                _bundle_binding_error(f"{row_path} must be an object")
            row_id = row.get("row_id")
            text = row.get("row")
            if (not isinstance(row_id, str) or not row_id
                    or row_id in seen_row_ids
                    or row.get("episode_id") != episode_id
                    or row.get("row_index") != expected_row_index
                    or not isinstance(text, str) or not text):
                _bundle_binding_error(f"{row_path} has invalid public provenance")
            if row.get("row_sha256") != _sha256_text(text):
                _bundle_binding_error(f"{row_path}.row_sha256 does not hash its row")
            seen_row_ids.add(row_id)
            all_rows.append(row)
            expected_row_index += 1
        if episode.get("episode_sha256") != _sha256_canonical(rows):
            _bundle_binding_error(f"{path}.episode_sha256 does not hash its rows")

    life_payload = [{
        "row_id": row["row_id"],
        "episode_id": row["episode_id"],
        "row": row["row"],
        "row_sha256": row["row_sha256"],
    } for row in all_rows]
    if life.get("row_count") != len(all_rows):
        _bundle_binding_error("public_export.life.row_count is wrong")
    if life.get("episode_count") != len(episodes):
        _bundle_binding_error("public_export.life.episode_count is wrong")
    if life.get("row_order") != "render_lifetime_first_seen":
        _bundle_binding_error("public_export.life.row_order is wrong")
    if life.get("row_ids") != [row["row_id"] for row in all_rows]:
        _bundle_binding_error("public_export.life.row_ids do not match rows")
    if life.get("row_hashes") != [row["row_sha256"] for row in all_rows]:
        _bundle_binding_error("public_export.life.row_hashes do not match rows")
    if life.get("life_sha256") != _sha256_canonical(life_payload):
        _bundle_binding_error("public_export.life.life_sha256 does not hash rows")


def _apply_cycle_events(nodes: dict[str, dict[str, Any]],
                        events: Sequence[Mapping[str, Any]], *,
                        self_check: bool) -> None:
    """Replay only the node state which is rendered into later prompts."""
    for event in events:
        event_type = event.get("type")
        if event_type in {"ADD_NODE", "REVISE_NODE"}:
            node_id = event.get("node_id")
            if not isinstance(node_id, str) or not node_id or node_id in nodes:
                _bundle_binding_error("event has an invalid or duplicate node_id")
            required = ("claim_kind", "left", "relation", "right", "depth")
            if any(key not in event for key in required):
                _bundle_binding_error(f"event {node_id} cannot replay node state")
            supersedes = event.get("supersedes", [])
            if not isinstance(supersedes, list) or not all(
                    isinstance(value, str) for value in supersedes):
                _bundle_binding_error(f"event {node_id} has invalid supersedes")
            node = {
                "node_id": node_id,
                "claim_kind": event["claim_kind"],
                "left": event["left"],
                "relation": event["relation"],
                "right": event["right"],
                "edge": [
                    str(event["claim_kind"]).casefold(),
                    " ".join(str(event["left"]).casefold().split()),
                    " ".join(str(event["relation"]).casefold().split()),
                    " ".join(str(event["right"]).casefold().split()),
                ],
                "depth": event["depth"],
                "status": event.get("status", "provisional"),
                "supersedes": list(supersedes),
                "conflicts": [],
            }
            nodes[node_id] = node
            if event_type == "REVISE_NODE":
                if len(supersedes) != 1 or supersedes[0] not in nodes:
                    _bundle_binding_error(f"revision {node_id} cannot find its prior node")
                previous = nodes[supersedes[0]]
                old_edge = (previous["claim_kind"], previous["left"],
                            previous["relation"], previous["right"])
                new_edge = (node["claim_kind"], node["left"],
                            node["relation"], node["right"])
                if old_edge != new_edge:
                    node["conflicts"] = [supersedes[0]]
                if not self_check:
                    previous["superseded_by"] = node_id
                    previous["status"] = "superseded"
        elif event_type == "STATUS_CHANGE":
            node_id = event.get("node_id")
            status = event.get("status")
            if not isinstance(node_id, str) or node_id not in nodes or not isinstance(status, str):
                _bundle_binding_error("status event cannot replay node state")
            node = nodes[node_id]
            node["status"] = status
            if status == "supported" and len(node.get("supersedes", [])) == 1:
                previous = nodes.get(node["supersedes"][0])
                if previous is None:
                    _bundle_binding_error(f"status event {node_id} cannot find revised node")
                previous["superseded_by"] = node_id
                previous["status"] = "superseded"


def _typed_edge_from_completion(raw_completion: Any) -> tuple[Any, str, tuple[str, ...]]:
    """Recover the exact normalized edge and citation order used by the runner."""
    if not isinstance(raw_completion, str):
        _bundle_binding_error("self-check has no proposal completion")
    parsed = parse_microdream(raw_completion)
    if parsed is None or parsed.operation not in {"add", "revise"}:
        _bundle_binding_error("self-check proposal is not an ADD or REVISE completion")
    fields = (parsed.claim_kind, parsed.left, parsed.relation, parsed.right)
    if not all(isinstance(value, str) and value for value in fields):
        _bundle_binding_error("self-check proposal lacks a canonical typed edge")
    typed_edge = (
        f"KIND={' '.join(parsed.claim_kind.casefold().split())} | "
        f"LEFT={' '.join(parsed.left.casefold().split())} | "
        f"RELATION={' '.join(parsed.relation.casefold().split())} | "
        f"RIGHT={' '.join(parsed.right.casefold().split())}"
    )
    return parsed, typed_edge, tuple(parsed.cites)


def _verify_self_check_binding(
    *, cycle_index: int, cycle: Mapping[str, Any], cycle_events: Sequence[Mapping[str, Any]],
    nodes: Mapping[str, Mapping[str, Any]], public_sources: Mapping[str, str],
    episode_ids: frozenset[str], experience_ids: frozenset[str],
) -> None:
    """Re-render a self-check from the proposal and cited material exactly."""
    operation = cycle.get("operation")
    if not isinstance(operation, Mapping):
        _bundle_binding_error(f"cycle {cycle_index} has no operation for self-check replay")
    parsed, typed_edge, cited_ids = _typed_edge_from_completion(
        operation.get("raw_completion")
    )
    cited_material: list[str] = []
    for cited_id in cited_ids:
        if cited_id in public_sources:
            cited_material.append(public_sources[cited_id])
        elif cited_id in nodes:
            cited_material.append(_node_prompt(nodes[cited_id]))
        else:
            _bundle_binding_error(
                f"cycle {cycle_index} self-check cites unavailable material {cited_id!r}"
            )
    prior_edge = None
    if parsed.operation == "revise":
        if len(parsed.supersedes) != 1 or parsed.supersedes[0] not in nodes:
            _bundle_binding_error(f"cycle {cycle_index} revision has no replayable prior edge")
        prior = nodes[parsed.supersedes[0]]
        prior_edge = (
            f"KIND={prior['claim_kind']} | LEFT={prior['left']} | "
            f"RELATION={prior['relation']} | RIGHT={prior['right']}"
        )
    expected_prompt = render_self_check_prompt(
        canonical_typed_edge=typed_edge,
        cited_public_material=cited_material,
        superseded_typed_edge=prior_edge,
    )

    calls: list[tuple[str, Mapping[str, Any]]] = []
    for event in cycle_events:
        if event.get("type") == "STATUS_CHANGE" and "self_check_call" in event:
            calls.append(("event", event))
    if "self_check_call" in operation:
        calls.append(("operation", operation))
    if len(calls) != 1:
        _bundle_binding_error(f"cycle {cycle_index} must have exactly one self-check call")
    source_name, source = calls[0]
    call = source.get("self_check_call")
    if not isinstance(call, Mapping) or call.get("prompt") != expected_prompt:
        _bundle_binding_error(
            f"cycle {cycle_index} self-check call prompt is not its rendered evidence"
        )
    legacy_prompt = source.get("self_check_prompt")
    if legacy_prompt != expected_prompt:
        _bundle_binding_error(
            f"cycle {cycle_index} {source_name} self-check prompt is not its rendered evidence"
        )
    decision = classify_self_check(
        call.get("output"),
        proposal_cites=cited_ids,
        supersedes=parsed.supersedes,
        context=ProposalContext(
            visible_ids=frozenset(cited_ids),
            episode_ids=episode_ids,
            experience_ids=experience_ids,
            node_ids=frozenset(nodes),
            retrieved_node_ids=tuple(cycle.get("retrieved_node_ids", ())),
            nodes=nodes,
            public_tokens=frozenset(),
            trigger_node_id=None,
        ),
    )
    if source_name == "event" and not decision.valid:
        _bundle_binding_error(
            f"cycle {cycle_index} status transition came from an invalid self-check verdict"
        )
    if source_name == "operation" and decision.valid:
        _bundle_binding_error(
            f"cycle {cycle_index} valid self-check verdict was discarded as a parse error"
        )


def _verify_bundle_binding(public_export: Mapping[str, Any], trace: Mapping[str, Any],
                           public_export_sha256: str) -> None:
    """Prove each recorded proposal prompt came from the committed public life."""
    _validate_public_export_hashes(public_export)
    if trace.get("public_export_sha256") != public_export_sha256:
        _bundle_binding_error("trace public_export_sha256 does not match public_export")
    for key in ("world_id", "skin_id", "life_id"):
        if trace.get(key) != public_export.get(key):
            _bundle_binding_error(f"trace {key} differs from public_export")
    raw_cycles = trace.get("cycles")
    raw_events = trace.get("events")
    if not isinstance(raw_cycles, list) or not isinstance(raw_events, list):
        _bundle_binding_error("trace must contain cycles and events lists")
    episodes = {episode["episode_id"]: episode for episode in public_export["episodes"]}
    public_sources: dict[str, str] = {}
    experience_ids: set[str] = set()
    for episode in public_export["episodes"]:
        rows = episode["rows"]
        public_sources[episode["episode_id"]] = "\n".join(
            row["row"] for row in rows
        )
        for row in rows:
            public_sources[row["row_id"]] = row["row"]
            experience_ids.add(row["row_id"])
    events_by_cycle: dict[int, list[Mapping[str, Any]]] = {}
    for event in raw_events:
        if not isinstance(event, Mapping) or not isinstance(event.get("cycle_index"), int):
            _bundle_binding_error("trace event has no cycle index")
        events_by_cycle.setdefault(event["cycle_index"], []).append(event)

    nodes: dict[str, dict[str, Any]] = {}
    visible_lifetime_rows: list[str] = []
    for cycle_index, cycle in enumerate(raw_cycles):
        if not isinstance(cycle, Mapping) or cycle.get("cycle_index") != cycle_index:
            _bundle_binding_error("trace cycle index is not contiguous")
        trigger = cycle.get("trigger")
        if not isinstance(trigger, Mapping):
            _bundle_binding_error(f"cycle {cycle_index} has no trigger")
        trigger_kind, trigger_id = trigger.get("kind"), trigger.get("id")
        if trigger_kind not in {"WAKE", "REACTIVATE"} or not isinstance(trigger_id, str):
            _bundle_binding_error(f"cycle {cycle_index} has invalid trigger")
        if trigger_kind == "WAKE":
            episode = episodes.get(trigger_id)
            if episode is None or cycle.get("episode_id") != trigger_id:
                _bundle_binding_error(f"cycle {cycle_index} cannot bind its public episode")
            current_rows = [row["row"] for row in episode["rows"]]
            current_ids = [row["row_id"] for row in episode["rows"]]
            visible_lifetime_rows.extend(current_rows)
        else:
            if cycle.get("episode_id") is not None:
                _bundle_binding_error(f"cycle {cycle_index} reactivation has an episode")
            current_rows = []
            current_ids = []
        retrieved_ids = cycle.get("retrieved_node_ids")
        if not isinstance(retrieved_ids, list) or not all(
                isinstance(node_id, str) and node_id in nodes for node_id in retrieved_ids):
            _bundle_binding_error(f"cycle {cycle_index} has unreplayable retrieval")
        public_state = cycle.get("public_state")
        agenda = public_state.get("agenda") if isinstance(public_state, Mapping) else None
        if not isinstance(agenda, list) or not all(isinstance(value, str) for value in agenda):
            _bundle_binding_error(f"cycle {cycle_index} has unreplayable agenda")
        expected_prompt = render_microdream_prompt(
            trigger="wake" if trigger_kind == "WAKE" else "reactivate",
            trigger_id=trigger_id,
            current_episode_rows=current_rows,
            retrieved_nodes=[_node_prompt(nodes[node_id]) for node_id in retrieved_ids],
            agenda=agenda,
        )
        if cycle.get("model_prompt") != expected_prompt:
            _bundle_binding_error(f"cycle {cycle_index} model_prompt is not its rendered state")
        proposal_call = cycle.get("proposal_call")
        if not isinstance(proposal_call, Mapping) or proposal_call.get("prompt") != expected_prompt:
            _bundle_binding_error(f"cycle {cycle_index} proposal_call prompt is not its rendered state")
        proposal_context = ProposalContext(
            visible_ids=frozenset(current_ids) | frozenset(retrieved_ids) |
            ({trigger_id} if trigger_kind == "WAKE" else set()),
            episode_ids=frozenset(episodes),
            experience_ids=frozenset(experience_ids),
            node_ids=frozenset(nodes),
            retrieved_node_ids=tuple(retrieved_ids),
            nodes=nodes,
            public_tokens=public_tokens(visible_lifetime_rows),
            trigger_node_id=trigger_id if trigger_kind == "REACTIVATE" else None,
        )
        proposal_decision = classify_proposal(proposal_call.get("output"), proposal_context)
        cycle_events = events_by_cycle.get(cycle_index, [])
        operation = cycle.get("operation")
        if (not isinstance(operation, Mapping)
                or operation.get("kind") != proposal_decision.kind):
            _bundle_binding_error(
                f"cycle {cycle_index} structured operation differs from complete runner classification"
            )
        if (trace.get("condition") in {"self_check_no_drift", "self_check_drift"}
                and isinstance(operation, Mapping)
                and operation.get("kind") in {"ADD", "REVISE"}):
            _verify_self_check_binding(
                cycle_index=cycle_index, cycle=cycle, cycle_events=cycle_events,
                nodes=nodes, public_sources=public_sources,
                episode_ids=frozenset(episodes),
                experience_ids=frozenset(experience_ids),
            )
        _apply_cycle_events(
            nodes, cycle_events,
            self_check=trace.get("condition") in {"self_check_no_drift", "self_check_drift"},
        )


def _exact_usage_or_raise(usage: Mapping[str, Any], output: str) -> dict[str, Any]:
    """Accept only model-ID-backed usage records, never heuristic fallbacks."""
    missing = sorted(_EXACT_USAGE_FIELDS.difference(usage))
    if missing:
        raise RuntimeError("backend exact usage is missing fields: " + ", ".join(missing))
    for key in ("prompt_tokens", "output_tokens", "original_prompt_tokens"):
        value = usage[key]
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise RuntimeError(f"backend exact usage has invalid {key}")
    if usage["original_prompt_tokens"] < usage["prompt_tokens"]:
        raise RuntimeError("backend exact usage original prompt count is smaller than supplied count")
    if not isinstance(usage["prompt_truncated"], bool):
        raise RuntimeError("backend exact usage prompt_truncated must be boolean")
    if usage["prompt_truncated"]:
        raise RuntimeError("backend exact usage rejects truncated prompts")
    if not isinstance(usage["source"], str) or not usage["source"].strip():
        raise RuntimeError("backend exact usage source must be non-empty")
    if usage["source"].strip().lower().endswith("fallback"):
        raise RuntimeError("backend exact usage rejects fallback source")
    for key in ("prompt_token_ids_sha256", "supplied_prompt_token_ids_sha256",
                "output_token_ids_sha256", "decoded_output_sha256", "output_sha256"):
        value = usage[key]
        if not isinstance(value, str) or len(value) != 64 or any(
                character not in "0123456789abcdef" for character in value):
            raise RuntimeError(f"backend exact usage has invalid {key}")
    output_ids = usage["output_token_ids"]
    if (not isinstance(output_ids, list)
            or any(isinstance(value, bool) or not isinstance(value, int)
                   for value in output_ids)):
        raise RuntimeError("backend exact usage output_token_ids must be integer IDs")
    if len(output_ids) != usage["output_tokens"]:
        raise RuntimeError("backend exact usage output token count does not match IDs")
    if not isinstance(usage["decoded_output"], str):
        raise RuntimeError("backend exact usage decoded_output must be text")
    if usage["decoded_output"] != output:
        raise RuntimeError("backend exact usage decoded_output differs from backend output")
    if usage["output_token_ids_sha256"] != _sha256_canonical(output_ids):
        raise RuntimeError("backend exact usage output token ID hash mismatch")
    if usage["prompt_token_ids_sha256"] != usage["supplied_prompt_token_ids_sha256"]:
        raise RuntimeError("backend exact usage prompt token ID hash aliases differ")
    if usage["decoded_output_sha256"] != _sha256_canonical(output):
        raise RuntimeError("backend exact usage decoded output hash mismatch")
    if usage["output_sha256"] != hashlib.sha256(output.encode("utf-8")).hexdigest():
        raise RuntimeError("backend exact usage output hash mismatch")
    return dict(usage)


def _backend_generate(backend: Backend) -> Callable[[str, int, float, int], tuple[str, Mapping[str, Any]]]:
    """Adapt the batch backend to one prompt while preserving exact usage.

    Usage metadata is neither estimated nor normalized here.  A model-facing
    run is invalid if the backend cannot report exactly one usage record for
    its exactly one prompt.
    """

    exact_calls: list[dict[str, Any]] = []

    def generate(prompt: str, max_tokens: int, temperature: float, seed: int):
        outputs = backend.generate(
            [prompt],
            max_tokens=max_tokens,
            temperature=temperature,
            seed=seed,
        )
        if not isinstance(outputs, Sequence) or isinstance(outputs, (str, bytes)):
            raise RuntimeError("backend.generate must return a sequence of outputs")
        if len(outputs) != 1 or not isinstance(outputs[0], str):
            raise RuntimeError("one prompt must yield exactly one text output")
        usage = backend.last_usage
        if not isinstance(usage, Sequence) or isinstance(usage, (str, bytes)):
            raise RuntimeError("backend.last_usage must be a sequence")
        if len(usage) != 1 or not isinstance(usage[0], Mapping):
            raise RuntimeError("one prompt must yield exactly one exact usage record")
        exact_usage = _exact_usage_or_raise(usage[0], outputs[0])
        exact_calls.append({
            "backend_call_index": len(exact_calls),
            "prompt": prompt,
            "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
            "output": outputs[0],
            "output_sha256": hashlib.sha256(outputs[0].encode("utf-8")).hexdigest(),
            "seed": seed,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "usage": exact_usage,
        })
        return outputs[0], exact_usage

    # This is intentionally an attribute rather than a runner API change:
    # the frozen runner only consumes counts, while the publisher needs the
    # complete ID-derived audit data for its plan-aligned JSONL artifact.
    generate.exact_calls = exact_calls  # type: ignore[attr-defined]

    return generate


def _make_model_backend(config: TextRunConfig) -> Backend:
    kwargs: dict[str, Any] = {"revision": config.revision}
    if config.backend == "vllm":
        kwargs.update({
            "enable_lora": False,
            "max_len": config.max_model_len,
            "gpu_util": config.gpu_util,
        })
    return make_backend(config.backend, config.model, **kwargs)


def _config_manifest(config: TextRunConfig, *, public_export_sha256: str) -> dict[str, Any]:
    arguments = asdict(config)
    arguments["output_dir"] = str(config.output_dir)
    return {
        "schema_version": ARTIFACT_SCHEMA_VERSION,
        "run_kind": "recurrent_microdream_text_only_dev",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "public_export_sha256": public_export_sha256,
        "model": {
            "backend": config.backend,
            "name": config.model,
            "revision": config.revision,
            "pinned": True,
        },
        "world": {"seed": config.seed, "skin": config.skin},
        "condition": config.condition,
        "split": {"name": config.split, "id": config.split_id},
        "budgets": {
            "max_output_tokens_per_call": config.max_output_tokens,
            "retrieval_limit": config.retrieval_limit,
            "reactivate_every_episodes": config.reactivate_every,
            "max_model_len": config.max_model_len,
            "gpu_util": config.gpu_util,
            "temperature": config.temperature,
        },
        "memory_mode": "text_only_no_lora",
        "public_export_only": True,
        "offline_scoring": False,
        "arguments": arguments,
    }


def _reconcile_backend_calls(
    trace: Mapping[str, Any], exact_calls: Sequence[Mapping[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Bind every backend invocation bijectively to the runner's call ledger."""
    model_calls = trace.get("model_calls")
    if not isinstance(model_calls, list):
        _bundle_binding_error("trace.model_calls is not a list")
    if len(model_calls) != len(exact_calls):
        _bundle_binding_error(
            "backend call count differs from trace.model_calls "
            f"({len(exact_calls)} != {len(model_calls)})"
        )
    reconciled: dict[str, dict[str, Any]] = {}
    for index, (recorded, backend_call) in enumerate(zip(model_calls, exact_calls)):
        if not isinstance(recorded, Mapping) or not isinstance(backend_call, Mapping):
            _bundle_binding_error(f"call {index} is not an object")
        call_id = recorded.get("call_id")
        expected_id = f"call_{index:05d}"
        if call_id != expected_id or call_id in reconciled:
            _bundle_binding_error(f"call {index} has invalid or duplicate call_id")
        if backend_call.get("backend_call_index") != index:
            _bundle_binding_error(f"backend call {index} has wrong execution index")
        for key in (
            "prompt", "prompt_sha256", "output", "output_sha256", "seed",
            "max_tokens", "temperature", "usage",
        ):
            if recorded.get(key) != backend_call.get(key):
                _bundle_binding_error(
                    f"backend call {index} {key} differs from trace model call"
                )
        reconciled[call_id] = {"call_id": call_id, **dict(backend_call)}
    return reconciled


def _publish_artifacts(
    output_dir: Path,
    *,
    public_export: Mapping[str, Any],
    result: Mapping[str, Any],
    manifest: Mapping[str, Any],
    exact_calls: Sequence[Mapping[str, Any]],
) -> Path:
    """Publish a complete new directory with one final rename."""
    output_dir = output_dir.expanduser().resolve()
    parent = output_dir.parent
    parent.mkdir(parents=True, exist_ok=True)
    if os.path.lexists(output_dir):
        raise FileExistsError(f"refusing to overwrite output directory: {output_dir}")

    public_export_sha256 = _sha256_canonical(public_export)
    trace = result["trace"]
    if result.get("corpus") != trace.get("corpus"):
        _bundle_binding_error("result corpus differs from audited trace corpus")
    _verify_bundle_binding(public_export, trace, public_export_sha256)
    if manifest.get("public_export_sha256") != public_export_sha256:
        _bundle_binding_error("run manifest public_export_sha256 does not match public_export")
    contract_audit = audit_trace(trace)
    if contract_audit.get("valid") is not True:
        _bundle_binding_error("trace failed the deterministic recurrent contract audit")
    generations_by_id = _reconcile_backend_calls(trace, exact_calls)

    staging = Path(tempfile.mkdtemp(prefix=f".{output_dir.name}.staging-", dir=parent))
    try:
        episodes = {
            "schema_version": public_export.get("schema_version"),
            "world_id": public_export.get("world_id"),
            "skin_id": public_export.get("skin_id"),
            "life_id": public_export.get("life_id"),
            "episodes": public_export.get("episodes"),
        }
        _write_json(staging, "public_export.json", public_export)
        _write_json(staging, "public_episodes.json", episodes)
        _write_json(staging, "trace.json", result["trace"])
        _write_json(staging, "contract_audit.json", contract_audit)
        corpus = result.get("corpus")
        if corpus is not None:
            _write_json(staging, "corpus.json", corpus)
        scope = {
            "world_id": public_export.get("world_id"),
            "world_family": public_export.get("world_family"),
            "skin_id": public_export.get("skin_id"),
            "life_id": public_export.get("life_id"),
        }
        _write_jsonl(staging, "episodes.jsonl", [
            {"schema_version": ARTIFACT_SCHEMA_VERSION, **scope, "episode": episode}
            for episode in public_export.get("episodes", [])
        ])
        events_by_cycle: dict[int, list[Mapping[str, Any]]] = {}
        if isinstance(trace, Mapping):
            for event in trace.get("events", []):
                if isinstance(event, Mapping) and isinstance(event.get("cycle_index"), int):
                    events_by_cycle.setdefault(event["cycle_index"], []).append(event)
        consumed_generation_ids: set[str] = set()
        def calls_for_cycle(cycle: Mapping[str, Any]) -> list[Mapping[str, Any]]:
            call_ids = cycle.get("model_call_ids")
            if not isinstance(call_ids, list) or not all(
                    isinstance(call_id, str) for call_id in call_ids):
                _bundle_binding_error("cycle model_call_ids is not a string list")
            records: list[Mapping[str, Any]] = []
            for call_id in call_ids:
                if call_id in consumed_generation_ids:
                    _bundle_binding_error(f"serialized generation {call_id} is consumed twice")
                record = generations_by_id.get(call_id)
                if record is None:
                    _bundle_binding_error(f"serialized generation {call_id} is missing")
                consumed_generation_ids.add(call_id)
                records.append(record)
            return records

        cycles = trace.get("cycles", []) if isinstance(trace, Mapping) else []
        microdream_rows = [
            {
                "schema_version": ARTIFACT_SCHEMA_VERSION,
                **scope,
                "cycle": cycle,
                "events": events_by_cycle.get(cycle.get("cycle_index"), []),
                "generations": calls_for_cycle(cycle),
            }
            for cycle in cycles if isinstance(cycle, Mapping)
        ]
        if consumed_generation_ids != set(generations_by_id):
            leftover = sorted(set(generations_by_id).difference(consumed_generation_ids))
            _bundle_binding_error(
                "unserialized backend generations remain: " + ", ".join(leftover)
            )
        _write_jsonl(staging, "microdreams.jsonl", microdream_rows)
        _write_json(staging, "corpus_manifest.json", {
            "schema_version": ARTIFACT_SCHEMA_VERSION,
            **scope,
            "corpus": corpus,
            "lines": [] if corpus is None else corpus.get("lines", []),
        })
        _write_json(staging, "run_manifest.json", manifest)

        payload_names = sorted(path.name for path in staging.iterdir() if path.is_file())
        hashes = {
            "algorithm": "sha256",
            "files": {name: _sha256(staging / name) for name in payload_names},
        }
        _write_json(staging, "sha256s.json", hashes)

        # os.rename publishes the populated directory as one filesystem event.
        # Recheck immediately before it so ordinary callers cannot overwrite.
        if os.path.lexists(output_dir):
            raise FileExistsError(f"refusing to overwrite output directory: {output_dir}")
        os.rename(staging, output_dir)
    except BaseException:
        if staging.exists():
            shutil.rmtree(staging)
        raise
    return output_dir


def run_text_dev(
    config: TextRunConfig,
    *,
    backend: Backend | None = None,
    exporter: Exporter = export_semantic_world,
    runner: Runner = run_recurrent_life,
) -> Path:
    """Execute one public-only text condition and publish its artifacts."""
    config.validate()
    output_dir = config.output_dir.expanduser().resolve()
    if os.path.lexists(output_dir):
        raise FileExistsError(f"refusing to overwrite output directory: {output_dir}")

    # The public exporter is the only experiment-world value passed to the
    # recurrent generator.  This module has no goal, answer, solver, or scorer.
    public_export = exporter(config.seed, config.skin)
    if public_export.get("world_family") != PUBLIC_WORLD_FAMILY:
        raise ValueError(
            f"public export world_family must be {PUBLIC_WORLD_FAMILY!r}"
        )
    _validate_public_export_hashes(public_export)
    public_export_sha256 = _sha256_canonical(public_export)
    model_backend = backend if backend is not None else _make_model_backend(config)
    generate = _backend_generate(model_backend)
    result = runner(
        public_export,
        generate,
        condition=config.condition,
        split=config.split,
        split_id=config.split_id,
        trace_id=(
            f"microdream-text:{config.split_id}:{config.seed}:"
            f"{config.skin}:{config.condition}"
        ),
        loop_adapter_id=f"frozen-text:{config.model}@{config.revision}",
        memory_adapter_id=None,
        max_tokens=config.max_output_tokens,
        temperature=config.temperature,
        seed=config.seed,
        retrieval_limit=config.retrieval_limit,
        reactivate_every=config.reactivate_every,
    )
    trace = result.get("trace")
    if not isinstance(trace, dict):
        _bundle_binding_error("runner result must contain a trace object")
    # The runner is deliberately frozen; the CLI records the cross-artifact
    # identity after it returns, then independently proves every proposal
    # prompt before any artifact staging directory is created.
    trace["public_export_sha256"] = public_export_sha256
    _verify_bundle_binding(public_export, trace, public_export_sha256)
    return _publish_artifacts(
        output_dir,
        public_export=public_export,
        result=result,
        manifest=_config_manifest(
            config, public_export_sha256=public_export_sha256,
        ),
        exact_calls=generate.exact_calls,  # type: ignore[attr-defined]
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True,
                        help="new artifact directory; existing paths are refused")
    parser.add_argument("--backend", choices=("hf", "vllm"), default="vllm")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--revision", default=DEFAULT_REVISION)
    parser.add_argument("--condition", choices=sorted(CONDITIONS),
                        default="self_check_drift")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--skin", choices=all_skin_names(), default="aligned")
    parser.add_argument("--split", default="dev")
    parser.add_argument("--split-id", default="recurrent-microdream-text-dev")
    parser.add_argument("--max-output-tokens", type=int, default=128)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--retrieval-limit", type=int, default=3)
    parser.add_argument("--reactivate-every", type=int, default=2)
    parser.add_argument("--max-model-len", type=int, default=32768)
    parser.add_argument("--gpu-util", type=float, default=0.85)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    config = TextRunConfig(
        output_dir=args.out,
        backend=args.backend,
        model=args.model,
        revision=args.revision,
        condition=args.condition,
        seed=args.seed,
        skin=args.skin,
        split=args.split,
        split_id=args.split_id,
        max_output_tokens=args.max_output_tokens,
        temperature=args.temperature,
        retrieval_limit=args.retrieval_limit,
        reactivate_every=args.reactivate_every,
        max_model_len=args.max_model_len,
        gpu_util=args.gpu_util,
    )
    path = run_text_dev(config)
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
