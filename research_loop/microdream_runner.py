"""Deterministic, model-agnostic recurrent microdream life driver.

The driver consumes only a :mod:`microdream_world` public export.  It has no
world solver, goal, answer, or scorer path.  A caller injects a completion
function, which makes this module useful for CPU contract tests as well as a
later frozen model adapter.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping, Sequence
import hashlib
import re
from typing import Any

from .microdream_classification import (
    ProposalContext,
    classify_proposal,
    classify_self_check,
    public_tokens,
)
from .microdream_contract import SCHEMA_VERSION, assert_valid_trace, canonical_corpus_text
from .microdream_prompts import (
    ParsedMicrodream,
    canonical_edge,
    render_microdream_prompt,
    render_self_check_prompt,
)


CONDITIONS = frozenset({
    "no_gate_no_drift", "no_gate_drift",
    "self_check_no_drift", "self_check_drift",
})
Generate = Callable[[str, int, float, int], tuple[str, Mapping[str, Any]]]
class MicrodreamRunError(ValueError):
    """Raised when a public export or injected generator violates the driver contract."""


def _scope(world: Mapping[str, Any]) -> tuple[str, str, str]:
    values = tuple(world.get(key) for key in ("world_id", "skin_id", "life_id"))
    if not all(isinstance(value, str) and value.strip() for value in values):
        raise MicrodreamRunError("world export must provide world_id, skin_id, and life_id")
    return values  # type: ignore[return-value]


def _usage_counts(
    usage: Mapping[str, Any] | None, prompt: str, output: str,
) -> tuple[int, int, dict[str, str]]:
    """Read usage counts and explicitly identify any scripted fallback."""
    usage = usage or {}
    prompt_value = usage.get("prompt_tokens", usage.get("input_tokens"))
    output_value = usage.get("output_tokens", usage.get("completion_tokens"))
    prompt_exact = (isinstance(prompt_value, int)
                    and not isinstance(prompt_value, bool) and prompt_value >= 0)
    output_exact = (isinstance(output_value, int)
                    and not isinstance(output_value, bool) and output_value >= 0)
    prompt_tokens = prompt_value if prompt_exact else len(prompt.split())
    output_tokens = output_value if output_exact else len(output.split())
    return prompt_tokens, output_tokens, {
        "prompt_tokens": "usage" if prompt_exact else "scripted_fallback",
        "output_tokens": "usage" if output_exact else "scripted_fallback",
    }


def _call_generate(generate: Generate, prompt: str, *, max_tokens: int,
                   temperature: float, seed: int) -> tuple[str, Mapping[str, Any]]:
    result = generate(prompt, max_tokens, temperature, seed)
    if not isinstance(result, tuple) or len(result) != 2:
        raise MicrodreamRunError("generate must return (text, usage)")
    text, usage = result
    if not isinstance(text, str) or not isinstance(usage, Mapping):
        raise MicrodreamRunError("generate must return (string, mapping)")
    return text, usage


def _row_ids(episode: Mapping[str, Any]) -> tuple[str, ...]:
    rows = episode.get("rows")
    if not isinstance(rows, list) or not rows:
        raise MicrodreamRunError("each public episode must contain non-empty rows")
    ids: list[str] = []
    for row in rows:
        if not isinstance(row, Mapping) or not isinstance(row.get("row_id"), str):
            raise MicrodreamRunError("public episode rows must contain row_id")
        ids.append(row["row_id"])
    return tuple(ids)


def _row_texts(episode: Mapping[str, Any]) -> tuple[str, ...]:
    rows = episode.get("rows")
    assert isinstance(rows, list)
    texts: list[str] = []
    for row in rows:
        if not isinstance(row, Mapping) or not isinstance(row.get("row"), str):
            raise MicrodreamRunError("public episode rows must contain exact row text")
        texts.append(row["row"])
    return tuple(texts)


def _terms(text: str) -> set[str]:
    return {token.lower() for token in re.findall(r"[A-Za-z0-9_-]+", text)}


def _node_prompt(node: Mapping[str, Any]) -> str:
    supersedes = ",".join(node.get("supersedes", ())) or "none"
    superseded_by = node.get("superseded_by", "none")
    conflicts = ",".join(node.get("conflicts", ())) or "none"
    return (
        f"{node['node_id']} | {node['claim_kind']} | "
        f"{node['left']} {node['relation']} {node['right']} | "
        f"status={node['status']} depth={node['depth']} supersedes={supersedes} "
        f"superseded_by={superseded_by} conflicts={conflicts}"
    )


def _node_edge_text(node: Mapping[str, Any]) -> str:
    return f"{node['left']} {node['relation']} {node['right']}"


def _retrieve(nodes: Mapping[str, dict[str, Any]], visible_text: Iterable[str], *,
              limit: int, trigger_id: str | None = None,
              allowed_statuses: set[str] | None = None) -> list[str]:
    """Deterministic bounded lexical retrieval, always retaining a reactivation trigger."""
    if limit < 1:
        return []
    query_terms = set().union(*(_terms(text) for text in visible_text))
    ranked: list[tuple[int, int, str]] = []
    for ordinal, (node_id, node) in enumerate(nodes.items()):
        if node.get("superseded_by") is not None or node.get("status") == "superseded":
            continue
        if allowed_statuses is not None and node.get("status") not in allowed_statuses:
            continue
        overlap = len(query_terms & _terms(_node_edge_text(node)))
        ranked.append((-overlap, ordinal, node_id))
    ranked.sort()
    chosen = [node_id for _, _, node_id in ranked[:limit]]
    trigger_active = (
        trigger_id is not None
        and trigger_id in nodes
        and nodes[trigger_id].get("superseded_by") is None
        and nodes[trigger_id].get("status") != "superseded"
        and (allowed_statuses is None or nodes[trigger_id].get("status") in allowed_statuses)
    )
    if trigger_active and trigger_id not in chosen:
        if len(chosen) >= limit:
            chosen[-1] = trigger_id
        else:
            chosen.append(trigger_id)
    # Preserve lexical rank except for a required trigger append/replace.
    return chosen[:limit]


def _edge_depth(parsed: ParsedMicrodream, cited_nodes: Sequence[str],
                nodes: Mapping[str, Mapping[str, Any]]) -> int:
    """Measure semantic path growth, not mere citation/revision lineage."""
    edge = canonical_edge(parsed)
    assert edge is not None
    if parsed.operation == "revise" and parsed.supersedes:
        return int(nodes[parsed.supersedes[0]]["depth"])
    endpoints = {edge[1], edge[3]}
    extending: list[int] = []
    for node_id in cited_nodes:
        prior = nodes[node_id]
        prior_edge = tuple(prior["edge"])
        if prior_edge[1:] != edge[1:] and endpoints.intersection({prior_edge[1], prior_edge[3]}):
            extending.append(int(prior["depth"]))
    return 1 + max(extending, default=0)


def _public_source_map(episodes: Sequence[Mapping[str, Any]]) -> dict[str, str]:
    result: dict[str, str] = {}
    for episode in episodes:
        episode_id = episode["episode_id"]
        texts = _row_texts(episode)
        ids = _row_ids(episode)
        result[episode_id] = "\n".join(texts)
        for row_id, text in zip(ids, texts):
            if row_id in result:
                raise MicrodreamRunError(f"duplicate public citation id {row_id}")
            result[row_id] = text
    return result


def _typed_edge_line(parsed: ParsedMicrodream) -> str:
    """The only proposal material exposed to self-check."""
    assert parsed.operation in {"add", "revise"}
    return (
        f"KIND={parsed.claim_kind} | LEFT={' '.join((parsed.left or '').casefold().split())} | "
        f"RELATION={' '.join((parsed.relation or '').casefold().split())} | "
        f"RIGHT={' '.join((parsed.right or '').casefold().split())}"
    )


def _node_line(parsed: ParsedMicrodream) -> str:
    # Only the typed local edge becomes durable text/LoRA material. The
    # free-form rationale/prediction stays in the audit trace and cannot smuggle
    # a multi-edge solution into later retrieval or training.
    assert parsed.left is not None and parsed.relation is not None and parsed.right is not None
    return canonical_corpus_text(parsed.left, parsed.relation, parsed.right)


def run_recurrent_life(
    world: Mapping[str, Any],
    generate: Generate,
    *,
    condition: str,
    split: str = "dev",
    split_id: str = "microdream-dev",
    trace_id: str | None = None,
    loop_adapter_id: str = "loop-adapter-v0",
    memory_adapter_id: str | None = "memory-adapter-v0",
    max_tokens: int = 128,
    temperature: float = 0.0,
    seed: int = 0,
    retrieval_limit: int = 3,
    reactivate_every: int = 2,
) -> dict[str, Any]:
    """Run one bounded public life and return ``{'trace', 'corpus'}``.

    Drift schedules a reactivation after each fixed episode interval and one
    final post-life reactivation.  Reactivation has no current episode or
    experience IDs; its trigger node is always in the bounded retrieval set.
    """
    if condition not in CONDITIONS:
        raise MicrodreamRunError(f"unknown condition {condition!r}")
    if retrieval_limit < 1 or reactivate_every < 1 or max_tokens < 1:
        raise MicrodreamRunError("retrieval_limit, reactivate_every, and max_tokens must be positive")
    world_id, skin_id, life_id = _scope(world)
    raw_episodes = world.get("episodes")
    if not isinstance(raw_episodes, list) or not raw_episodes:
        raise MicrodreamRunError("world export must contain non-empty episodes")
    episodes: list[dict[str, Any]] = []
    experience_ids: set[str] = set()
    for index, item in enumerate(raw_episodes):
        if not isinstance(item, Mapping) or item.get("episode_index") != index:
            raise MicrodreamRunError("public episodes must preserve contiguous episode order")
        episode_id = item.get("episode_id")
        if not isinstance(episode_id, str) or not episode_id.strip():
            raise MicrodreamRunError("public episodes require episode_id")
        if any(existing["episode_id"] == episode_id for existing in episodes):
            raise MicrodreamRunError("public episode IDs must be unique")
        ids = _row_ids(item)
        if experience_ids.intersection(ids):
            raise MicrodreamRunError("public experience IDs must be unique")
        experience_ids.update(ids)
        episodes.append(dict(item))
    source_map = _public_source_map(episodes)
    episode_ids = {str(item["episode_id"]) for item in episodes}
    trace_id = trace_id or f"microdream:{life_id}"
    memory_id = memory_adapter_id if memory_adapter_id is not None else None
    trace: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "trace_id": trace_id,
        "condition": condition,
        "split": split,
        "split_id": split_id,
        "world_id": world_id,
        "skin_id": skin_id,
        "life_id": life_id,
        "memory_mode": "mounted" if memory_id is not None else "none",
        "memory_adapter_id": memory_id,
        "loop_adapter_id": loop_adapter_id,
        "schedule": {
            "reactivate_every": reactivate_every,
            "drift_enabled": condition in {"no_gate_drift", "self_check_drift"},
            "final_reactivation": condition in {"no_gate_drift", "self_check_drift"},
        },
        "episodes": [],
        "cycles": [],
        "events": [],
        "model_calls": [],
        "corpus": None,
    }
    nodes: dict[str, dict[str, Any]] = {}
    events: list[dict[str, Any]] = []
    cycles: list[dict[str, Any]] = []
    # Agenda entries are populated only by accepted canonical typed questions.
    agenda: list[str] = []
    visible_lifetime_rows: list[str] = []
    model_calls: list[dict[str, Any]] = trace["model_calls"]
    drift = condition in {"no_gate_drift", "self_check_drift"}
    self_check = condition in {"self_check_no_drift", "self_check_drift"}
    cycle_index = 0
    event_index = 0

    def record_call(*, kind: str, prompt: str, output: str,
                    usage: Mapping[str, Any], call_seed: int) -> tuple[dict[str, Any], int, int]:
        prompt_tokens, output_tokens, count_sources = _usage_counts(usage, prompt, output)
        finish_reason = usage.get("finish_reason")
        truncated = bool(
            usage.get("truncated") is True
            or finish_reason in {"length", "max_tokens"}
        )
        required_usage = {
            "prompt_tokens", "output_tokens", "original_prompt_tokens",
            "prompt_truncated", "source", "supplied_prompt_token_ids_sha256",
            "output_token_ids_sha256", "output_sha256",
        }
        if required_usage <= set(usage):
            exact_usage = dict(usage)
        else:
            # Scripted CPU generators have no tokenizer. Preserve their complete
            # mapping and label the deterministic whitespace/hash stand-ins.
            exact_usage = {
                "prompt_tokens": prompt_tokens,
                "output_tokens": output_tokens,
                "original_prompt_tokens": prompt_tokens,
                "prompt_truncated": truncated,
                "source": "scripted_fallback",
                "supplied_prompt_token_ids_sha256": hashlib.sha256(
                    prompt.encode("utf-8")
                ).hexdigest(),
                "output_token_ids_sha256": hashlib.sha256(
                    output.encode("utf-8")
                ).hexdigest(),
                "output_sha256": hashlib.sha256(output.encode("utf-8")).hexdigest(),
                "raw_usage": dict(usage),
                "token_count_source": count_sources,
            }
        if exact_usage.get("source") == "scripted_fallback":
            trace["cpu_fixture"] = True
        call_record = {
            "call_id": f"call_{len(model_calls):05d}",
            "cycle_index": cycle_index,
            "kind": kind,
            "prompt": prompt,
            "output": output,
            "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
            "output_sha256": hashlib.sha256(output.encode("utf-8")).hexdigest(),
            "seed": call_seed,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "usage": exact_usage,
        }
        model_calls.append(call_record)
        return call_record, prompt_tokens, output_tokens

    def run_cycle(*, trigger_kind: str, trigger_id: str, current_episode: Mapping[str, Any] | None,
                  trigger_node_id: str | None = None) -> None:
        nonlocal cycle_index, event_index
        current_rows = _row_texts(current_episode) if current_episode is not None else ()
        current_ids = _row_ids(current_episode) if current_episode is not None else ()
        retrieval_cues = list(current_rows)
        retrieval_cues.extend(agenda)
        if trigger_node_id is not None:
            retrieval_cues.append(_node_edge_text(nodes[trigger_node_id]))
        retrieved_ids = _retrieve(
            nodes, retrieval_cues, limit=retrieval_limit,
            trigger_id=trigger_node_id,
            allowed_statuses={"supported", "unresolved"} if self_check else None,
        )
        visible_ids = set(current_ids) | set(retrieved_ids)
        if current_episode is not None:
            visible_ids.add(str(current_episode["episode_id"]))
        retrieved_lines = tuple(_node_prompt(nodes[node_id]) for node_id in retrieved_ids)
        prompt = render_microdream_prompt(
            trigger="wake" if trigger_kind == "WAKE" else "reactivate",
            trigger_id=trigger_id,
            current_episode_rows=current_rows,
            retrieved_nodes=retrieved_lines,
            agenda=agenda,
        )
        proposal_seed = seed + cycle_index
        raw, usage = _call_generate(generate, prompt, max_tokens=max_tokens,
                                    temperature=temperature, seed=proposal_seed)
        proposal_call, proposal_prompt_tokens, proposal_output_tokens = record_call(
            kind="proposal", prompt=prompt, output=raw, usage=usage,
            call_seed=proposal_seed,
        )
        proposal_context = ProposalContext(
            visible_ids=frozenset(visible_ids),
            episode_ids=frozenset(episode_ids),
            experience_ids=frozenset(experience_ids),
            node_ids=frozenset(nodes),
            retrieved_node_ids=tuple(retrieved_ids),
            nodes=nodes,
            public_tokens=public_tokens(visible_lifetime_rows),
            trigger_node_id=trigger_node_id,
        )
        decision = classify_proposal(raw, proposal_context)
        parsed = decision.parsed
        op_id = f"op_{cycle_index:05d}"
        cycle_trigger = {"kind": trigger_kind, "id": trigger_id}
        base_cycle: dict[str, Any] = {
            "world_id": world_id, "skin_id": skin_id, "life_id": life_id,
            "cycle_id": f"cycle_{cycle_index:05d}", "cycle_index": cycle_index,
            "microdream_index": cycle_index, "trigger": cycle_trigger,
            "episode_id": str(current_episode["episode_id"]) if current_episode is not None else None,
            "experience_ids": list(current_ids) if current_episode is not None else [],
            "public_state": {"agenda": list(agenda), "public_experience_ids": list(current_ids)},
            "retrieved_node_ids": retrieved_ids,
            "tool_env_result": {"observed_experience_ids": list(current_ids)},
            "model_prompt": prompt,
            "model_prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
            "proposal_call": proposal_call,
            "next_state": {"agenda": list(agenda)},
            "operation": {"op_id": op_id, "model_visible": True},
            "model_call_ids": [model_calls[-1]["call_id"]],
            "event_ids": [],
        }
        operation = base_cycle["operation"]
        operation["kind"] = decision.kind
        operation["raw_completion"] = raw
        if decision.kind == "MALFORMED":
            operation["parse_error"] = decision.error
        elif parsed is not None and parsed.operation == "open_question":
            operation.update({
                "claim_kind": parsed.claim_kind,
                "left": parsed.left, "relation": parsed.relation, "right": parsed.right,
                "cited_episode_ids": list(decision.cited_episode_ids),
                "cited_experience_ids": list(decision.cited_experience_ids),
                "cited_node_ids": list(decision.cited_node_ids),
            })
            assert decision.question is not None
            if decision.question not in agenda:
                    agenda.append(decision.question)
                    del agenda[:-8]
        elif parsed is not None and parsed.operation in {"add", "revise"}:
                assert decision.edge is not None
                edge = decision.edge
                cited = (
                    list(decision.cited_episode_ids),
                    list(decision.cited_experience_ids),
                    list(decision.cited_node_ids),
                )
                operation.update({
                    "claim_kind": parsed.claim_kind,
                    "left": parsed.left, "relation": parsed.relation, "right": parsed.right,
                    "edge": list(edge),
                    "claim": parsed.claim, "prediction": parsed.prediction,
                    "confidence": parsed.confidence,
                    "cited_episode_ids": cited[0],
                    "cited_experience_ids": cited[1],
                    "cited_node_ids": cited[2],
                    "supersedes": list(parsed.supersedes),
                })
                node_id = f"node_{len(nodes):05d}"
                event_id = f"event_{event_index:05d}"
                cited_nodes = cited[2]
                depth = _edge_depth(parsed, cited_nodes, nodes)
                event: dict[str, Any] = {
                    "world_id": world_id, "skin_id": skin_id, "life_id": life_id,
                    "event_id": event_id, "event_index": event_index,
                    "prev_event_id": events[-1]["event_id"] if events else None,
                    "cycle_index": cycle_index, "microdream_index": cycle_index,
                    "trigger": cycle_trigger,
                    "type": "ADD_NODE" if parsed.operation == "add" else "REVISE_NODE",
                    "operation": parsed.operation.upper(), "node_id": node_id,
                    "claim": parsed.claim, "claim_kind": parsed.claim_kind,
                    "left": parsed.left, "relation": parsed.relation,
                    "right": parsed.right, "edge": list(edge),
                    "prediction": parsed.prediction, "raw_completion": raw,
                    "prompt_tokens": proposal_prompt_tokens,
                    "output_tokens": proposal_output_tokens,
                    "confidence": parsed.confidence, "status": "provisional",
                    "supersedes": list(parsed.supersedes),
                    "cited_episode_ids": cited[0],
                    "cited_experience_ids": cited[1],
                    "cited_node_ids": cited_nodes,
                    "retrieved_node_ids": retrieved_ids,
                    "depth": depth, "model_visible": True,
                }
                events.append(event)
                base_cycle["event_ids"].append(event_id)
                nodes[node_id] = {
                    "node_id": node_id, "claim": parsed.claim,
                    "claim_kind": parsed.claim_kind,
                    "left": parsed.left, "relation": parsed.relation,
                    "right": parsed.right, "edge": list(edge),
                    "depth": depth, "status": "provisional",
                    "supersedes": list(parsed.supersedes),
                    "conflicts": [],
                    "event_id": event_id, "line": _node_line(parsed),
                    "cited_episode_ids": cited[0],
                    "cited_experience_ids": cited[1],
                    "cited_node_ids": cited_nodes,
                }
                if parsed.operation == "revise":
                    old_id = parsed.supersedes[0]
                    if tuple(nodes[old_id]["edge"]) != edge:
                        nodes[node_id]["conflicts"] = [old_id]
                    # A gated revision is only a proposal until its self-check
                    # supports it.  Do not erase the currently durable memory
                    # merely because a replacement was proposed.  Ungated arms
                    # intentionally retain every parsed operation, so their
                    # revision commits immediately.
                    if not self_check:
                        nodes[old_id]["superseded_by"] = node_id
                        nodes[old_id]["status"] = "superseded"
                event_index += 1
                if self_check:
                    cited_material = [
                        source_map[item] if item in source_map else _node_prompt(nodes[item])
                        for item in parsed.cites
                    ]
                    check_prompt = render_self_check_prompt(
                        canonical_typed_edge=_typed_edge_line(parsed),
                        cited_public_material=cited_material,
                        superseded_typed_edge=(
                            "KIND={claim_kind} | LEFT={left} | RELATION={relation} | RIGHT={right}".format(
                                **nodes[parsed.supersedes[0]]
                            )
                            if parsed.operation == "revise" else None
                        ),
                    )
                    check_seed = seed + 100000 + cycle_index
                    check_raw, check_usage = _call_generate(
                        generate, check_prompt, max_tokens=max_tokens,
                        temperature=temperature, seed=check_seed,
                    )
                    check_call, check_prompt_tokens, check_output_tokens = record_call(
                        kind="self_check", prompt=check_prompt, output=check_raw,
                        usage=check_usage, call_seed=check_seed,
                    )
                    base_cycle["model_call_ids"].append(model_calls[-1]["call_id"])
                    check_decision = classify_self_check(
                        check_raw,
                        proposal_cites=parsed.cites,
                        supersedes=parsed.supersedes,
                        context=proposal_context,
                    )
                    if check_decision.valid:
                        assert check_decision.verdict is not None
                        verdict = check_decision.verdict
                        status_event_id = f"event_{event_index:05d}"
                        status_event = {
                            "world_id": world_id, "skin_id": skin_id, "life_id": life_id,
                            "event_id": status_event_id, "event_index": event_index,
                            "prev_event_id": events[-1]["event_id"],
                            "cycle_index": cycle_index, "microdream_index": cycle_index,
                            "trigger": cycle_trigger, "type": "STATUS_CHANGE",
                            "operation": "SELF_CHECK", "node_id": node_id,
                            "previous_status": "provisional", "status": verdict[0],
                            "reason": verdict[1], "self_check_raw_completion": check_raw,
                            "self_check_call": check_call,
                            "self_check_prompt": check_prompt,
                            "self_check_prompt_sha256": hashlib.sha256(
                                check_prompt.encode("utf-8")
                            ).hexdigest(),
                            "prompt_tokens": check_prompt_tokens, "output_tokens": check_output_tokens,
                            "cited_episode_ids": list(check_decision.cited_episode_ids),
                            "cited_experience_ids": list(check_decision.cited_experience_ids),
                            "cited_node_ids": list(check_decision.cited_node_ids),
                            "retrieved_node_ids": retrieved_ids,
                            "model_visible": True,
                        }
                        events.append(status_event)
                        base_cycle["event_ids"].append(status_event_id)
                        nodes[node_id]["status"] = verdict[0]
                        if parsed.operation == "revise" and verdict[0] == "supported":
                            old_id = parsed.supersedes[0]
                            nodes[old_id]["superseded_by"] = node_id
                            nodes[old_id]["status"] = "superseded"
                        event_index += 1
                    else:
                        operation["self_check_raw_completion"] = check_raw
                        operation["self_check_call"] = check_call
                        operation["self_check_prompt"] = check_prompt
                        operation["self_check_prompt_sha256"] = hashlib.sha256(
                            check_prompt.encode("utf-8")
                        ).hexdigest()
                        operation["self_check_parse_error"] = check_decision.error
        base_cycle["next_state"] = {"agenda": list(agenda)}
        cycles.append(base_cycle)
        cycle_index += 1

    def newest_reactivation_node() -> str | None:
        allowed = {"supported", "unresolved"} if self_check else {"provisional"}
        for node_id in reversed(nodes):
            node = nodes[node_id]
            if (node.get("superseded_by") is None
                    and node.get("status") in allowed):
                return node_id
        return None

    for episode_position, episode in enumerate(episodes):
        visible_lifetime_rows.extend(_row_texts(episode))
        run_cycle(trigger_kind="WAKE", trigger_id=str(episode["episode_id"]), current_episode=episode)
        trigger = newest_reactivation_node()
        if drift and (episode_position + 1) % reactivate_every == 0 and trigger is not None:
            run_cycle(trigger_kind="REACTIVATE", trigger_id=trigger,
                      current_episode=None, trigger_node_id=trigger)
    trigger = newest_reactivation_node()
    if drift and trigger is not None:
        run_cycle(trigger_kind="REACTIVATE", trigger_id=trigger,
                  current_episode=None, trigger_node_id=trigger)

    corpus_lines: list[dict[str, Any]] = []
    status_event_ids = {
        event["node_id"]: event["event_id"] for event in events
        if event["type"] == "STATUS_CHANGE"
    }
    for event in events:
        if event["type"] not in {"ADD_NODE", "REVISE_NODE"}:
            continue
        node = nodes[event["node_id"]]
        if node.get("superseded_by") is not None:
            continue
        if self_check and node["status"] != "supported":
            continue
        corpus_lines.append({
            "world_id": world_id, "skin_id": skin_id, "life_id": life_id,
            "line_id": f"line_{len(corpus_lines):05d}", "text": node["line"],
            "edge": list(node["edge"]), "claim_kind": node["claim_kind"],
            "rendering": "canonical_atomic_v0", "paraphrase_index": 0,
            "exposure_count": 1,
            "node_ids": [node["node_id"]], "model_visible": True,
            "provenance": {
                "world_id": world_id, "skin_id": skin_id, "life_id": life_id,
                "event_ids": [node["event_id"]] + (
                    [status_event_ids[node["node_id"]]] if self_check else []
                ),
            },
        })
    corpus = None
    if corpus_lines:
        corpus = {
            "schema_version": SCHEMA_VERSION,
            "world_id": world_id, "skin_id": skin_id, "life_id": life_id,
            "lines": corpus_lines,
        }
    trace["episodes"] = [
        {
            "world_id": world_id, "skin_id": skin_id, "life_id": life_id,
            "episode_id": str(episode["episode_id"]), "episode_index": index,
            "experience_ids": list(_row_ids(episode)),
        } for index, episode in enumerate(episodes)
    ]
    trace["cycles"] = cycles
    trace["events"] = events
    trace["corpus"] = corpus
    assert_valid_trace(trace)
    return {"trace": trace, "corpus": corpus}


run_life = run_recurrent_life


__all__ = ["CONDITIONS", "MicrodreamRunError", "run_life", "run_recurrent_life"]
