"""Synthetic CPU tests for the approved recurrent micro-dream v0 contract."""

from __future__ import annotations

from copy import deepcopy
import hashlib

from .microdream_contract import (
    SCHEMA_VERSION,
    ContractError,
    assert_valid_dataset,
    assert_valid_trace,
    audit_trace,
    lineage_depth_report,
    validate_dataset,
    validate_trace,
)


def _base_scope(world_id="world-dev-0", skin_id="aligned", life_id="life-0"):
    return {"world_id": world_id, "skin_id": skin_id, "life_id": life_id}


def _call(prompt, output, *, source="model", call_id="call_00000",
          cycle_index=0, kind="proposal"):
    prompt_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
    output_hash = hashlib.sha256(output.encode("utf-8")).hexdigest()
    return {
        "call_id": call_id, "cycle_index": cycle_index, "kind": kind,
        "prompt": prompt, "prompt_sha256": prompt_hash,
        "output": output, "output_sha256": output_hash,
        "seed": 17, "max_tokens": 64, "temperature": 0.0,
        "usage": {
            "prompt_tokens": 3, "output_tokens": 4,
            "original_prompt_tokens": 3, "prompt_truncated": False,
            "source": source,
            "supplied_prompt_token_ids_sha256": hashlib.sha256(
                f"prompt-ids:{prompt}".encode("utf-8")
            ).hexdigest(),
            "output_token_ids_sha256": hashlib.sha256(
                f"output-ids:{output}".encode("utf-8")
            ).hexdigest(),
            "output_sha256": output_hash,
        },
    }


def _node_event(scope, event_id, event_index, cycle_index, trigger, node_id,
                operation, claim, cited_episodes=(), cited_nodes=(),
                depth=1, supersedes=(), cited_experiences=(), *,
                left="fox", relation="resembles", right="raven"):
    edge = ["similarity", left.casefold(), relation.casefold(), right.casefold()]
    return {
        **scope, "event_id": event_id, "event_index": event_index,
        "prev_event_id": None if event_index == 0 else f"ev-{event_index - 1}",
        "cycle_index": cycle_index, "microdream_index": cycle_index,
        "trigger": trigger, "type": "ADD_NODE" if operation == "ADD" else "REVISE_NODE",
        "node_id": node_id, "operation": operation,
        "claim": claim, "claim_kind": "similarity",
        "left": left, "relation": relation, "right": right, "edge": edge,
        "prediction": "NONE",
        "confidence": 0.7, "status": "provisional", "depth": depth,
        "supersedes": list(supersedes),
        "cited_episode_ids": list(cited_episodes),
        "cited_experience_ids": list(cited_experiences),
        "cited_node_ids": list(cited_nodes), "retrieved_node_ids": list(cited_nodes),
        "raw_completion": f"{operation} | CLAIM={claim}",
        "prompt_tokens": 50, "output_tokens": 20, "model_visible": True,
    }


def _corpus_line(scope, line_id, text, edge, node_id, event_ids):
    return {
        **scope, "line_id": line_id, "text": text,
        "edge": list(edge), "claim_kind": edge[0],
        "rendering": "canonical_atomic_v0", "paraphrase_index": 0,
        "exposure_count": 1, "node_ids": [node_id], "model_visible": True,
        "provenance": {**scope, "event_ids": list(event_ids)},
    }


def _restore_pre_revision_corpus(trace):
    scope = _base_scope(trace["world_id"], trace["skin_id"], trace["life_id"])
    trace["corpus"]["lines"] = [
        _corpus_line(
            scope, "line-0", "fox resembles raven.",
            ["similarity", "fox", "resembles", "raven"],
            "node-0", ["ev-0", "ev-1"],
        ),
        _corpus_line(
            scope, "line-1", "raven appears in moonland.",
            ["similarity", "raven", "appears in", "moonland"],
            "node-1", ["ev-2", "ev-3"],
        ),
    ]


def valid_trace(*, world_id="world-dev-0", skin_id="aligned", life_id="life-0",
                memory_adapter_id="mem-0", split="dev", split_id="split-dev"):
    scope = _base_scope(world_id, skin_id, life_id)
    wake0 = {"kind": "WAKE", "id": "ep-0"}
    wake1 = {"kind": "WAKE", "id": "ep-1"}
    react0 = {"kind": "REACTIVATE", "id": "node-1"}
    outputs = [
        "ADD | KIND=similarity | LEFT=fox | RELATION=resembles | RIGHT=raven | "
        "CLAIM=Fox resembles raven in one local context | CITES=ep-0,obs-0 | "
        "PREDICTION=NONE | CONFIDENCE=0.7",
        "ADD | KIND=similarity | LEFT=raven | RELATION=appears in | RIGHT=moonland | "
        "CLAIM=The later context extends the local relation | "
        "CITES=ep-1,obs-1,node-0 | PREDICTION=NONE | CONFIDENCE=0.7",
        "REVISE | KIND=similarity | LEFT=fox | RELATION=differs from | RIGHT=raven | "
        "CLAIM=The local relation is corrected after reactivation | CITES=node-1,node-0 | "
        "PREDICTION=NONE | CONFIDENCE=0.7 | SUPERSEDES=node-0",
    ]
    checks = [
        "VERDICT=SUPPORTED | REASON=Public evidence agrees | CITES=ep-0,obs-0",
        "VERDICT=SUPPORTED | REASON=Public evidence and memory agree | "
        "CITES=ep-1,obs-1,node-0",
        "VERDICT=SUPPORTED | REASON=Prior memory supports revision | CITES=node-1,node-0",
    ]
    calls = [
        _call("model-prompt-0", outputs[0], call_id="call_00000", cycle_index=0),
        _call("self-check-prompt-0", checks[0], call_id="call_00001",
              cycle_index=0, kind="self_check"),
        _call("model-prompt-1", outputs[1], call_id="call_00002", cycle_index=1),
        _call("self-check-prompt-1", checks[1], call_id="call_00003",
              cycle_index=1, kind="self_check"),
        _call("model-prompt-2", outputs[2], call_id="call_00004", cycle_index=2),
        _call("self-check-prompt-2", checks[2], call_id="call_00005",
              cycle_index=2, kind="self_check"),
    ]
    events = [
        _node_event(scope, "ev-0", 0, 0, wake0, "node-0", "ADD",
                    "Fox resembles raven in one local context", ["ep-0"], depth=1,
                    cited_experiences=["obs-0"]),
        {**scope, "event_id": "ev-1", "event_index": 1, "prev_event_id": "ev-0",
         "cycle_index": 0, "microdream_index": 0, "trigger": wake0,
         "type": "STATUS_CHANGE", "node_id": "node-0", "operation": "SELF_CHECK",
         "previous_status": "provisional", "status": "supported",
         "reason": "Public evidence agrees", "self_check_prompt": "self-check-prompt-0",
         "self_check_raw_completion": checks[0],
         "self_check_prompt_sha256": hashlib.sha256(b"self-check-prompt-0").hexdigest(),
         "self_check_call": deepcopy(calls[1]),
         "cited_episode_ids": ["ep-0"], "cited_experience_ids": ["obs-0"],
         "cited_node_ids": [], "retrieved_node_ids": [], "model_visible": True},
        _node_event(scope, "ev-2", 2, 1, wake1, "node-1", "ADD",
                    "The later context extends the local relation", ["ep-1"],
                    ["node-0"], depth=2, cited_experiences=["obs-1"],
                    left="raven", relation="appears in", right="moonland"),
        {**scope, "event_id": "ev-3", "event_index": 3, "prev_event_id": "ev-2",
         "cycle_index": 1, "microdream_index": 1, "trigger": wake1,
         "type": "STATUS_CHANGE", "node_id": "node-1", "operation": "SELF_CHECK",
         "previous_status": "provisional", "status": "supported",
         "reason": "Public evidence and memory agree",
         "self_check_raw_completion": checks[1],
         "self_check_prompt": "self-check-prompt-1",
         "self_check_prompt_sha256": hashlib.sha256(
             b"self-check-prompt-1"
         ).hexdigest(),
         "self_check_call": deepcopy(calls[3]),
         "cited_episode_ids": ["ep-1"], "cited_experience_ids": ["obs-1"],
         "cited_node_ids": ["node-0"],
         "retrieved_node_ids": ["node-0"], "model_visible": True},
        _node_event(scope, "ev-4", 4, 2, react0, "node-2", "REVISE",
                    "The local relation is corrected after reactivation", [],
                    ["node-1", "node-0"],
                    depth=1, supersedes=["node-0"], relation="differs from"),
        {**scope, "event_id": "ev-5", "event_index": 5, "prev_event_id": "ev-4",
         "cycle_index": 2, "microdream_index": 2, "trigger": react0,
         "type": "STATUS_CHANGE", "node_id": "node-2", "operation": "SELF_CHECK",
         "previous_status": "provisional", "status": "supported",
         "reason": "Prior memory supports revision",
         "self_check_raw_completion": checks[2],
         "self_check_prompt": (
             "self-check-prompt-2\nTHIS IS A REVISION OF THE PRIOR TYPED EDGE:\n"
             "KIND=similarity | LEFT=fox | RELATION=resembles | RIGHT=raven"
         ),
         "self_check_prompt_sha256": hashlib.sha256(
             b"self-check-prompt-2\nTHIS IS A REVISION OF THE PRIOR TYPED EDGE:\n"
             b"KIND=similarity | LEFT=fox | RELATION=resembles | RIGHT=raven"
         ).hexdigest(),
         "self_check_call": deepcopy(calls[5]),
         "cited_episode_ids": [], "cited_experience_ids": [],
         "cited_node_ids": ["node-1", "node-0"],
         "retrieved_node_ids": ["node-1", "node-0"],
         "model_visible": True},
    ]
    events[0]["raw_completion"] = outputs[0]
    events[2]["raw_completion"] = outputs[1]
    events[4]["raw_completion"] = outputs[2]
    calls[5]["prompt"] = events[5]["self_check_prompt"]
    calls[5]["prompt_sha256"] = events[5]["self_check_prompt_sha256"]
    events[5]["self_check_call"] = deepcopy(calls[5])
    return {
        "schema_version": SCHEMA_VERSION, "trace_id": f"trace-{life_id}",
        "condition": "self_check_drift", "split": split, "split_id": split_id, **scope,
        "memory_mode": "mounted" if memory_adapter_id else "none",
        "memory_adapter_id": memory_adapter_id, "loop_adapter_id": "loop-adapter-v0",
        "schedule": {"reactivate_every": 99, "drift_enabled": True,
                     "final_reactivation": True},
        "episodes": [
            {**scope, "episode_id": "ep-0", "episode_index": 0,
             "experience_ids": ["obs-0"]},
            {**scope, "episode_id": "ep-1", "episode_index": 1,
             "experience_ids": ["obs-1"]},
        ],
        "cycles": [
            {**scope, "cycle_id": "cy-0", "cycle_index": 0, "microdream_index": 0,
             "trigger": wake0, "episode_id": "ep-0", "experience_ids": ["obs-0"],
             "retrieved_node_ids": [], "public_state": {"agenda": "find one relation"},
             "model_prompt": "model-prompt-0",
             "model_prompt_sha256": hashlib.sha256(b"model-prompt-0").hexdigest(),
             "proposal_call": deepcopy(calls[0]),
             "operation": {"op_id": "op-0", "kind": "ADD", "model_visible": True,
                           "raw_completion": outputs[0], "claim_kind": "similarity",
                           "left": "fox", "relation": "resembles", "right": "raven",
                           "edge": ["similarity", "fox", "resembles", "raven"],
                           "claim": "Fox resembles raven in one local context",
                           "prediction": "NONE", "confidence": 0.7,
                           "supersedes": [], "cited_episode_ids": ["ep-0"],
                           "cited_experience_ids": ["obs-0"], "cited_node_ids": []},
             "tool_env_result": {"observed": "public observation obs-0"},
             "next_state": {"agenda": "retain the local relation"},
             "model_call_ids": ["call_00000", "call_00001"],
             "event_ids": ["ev-0", "ev-1"]},
            {**scope, "cycle_id": "cy-1", "cycle_index": 1, "microdream_index": 1,
             "trigger": wake1, "episode_id": "ep-1", "experience_ids": ["obs-1"],
             "retrieved_node_ids": ["node-0"], "public_state": {"agenda": "extend memory"},
             "model_prompt": "model-prompt-1",
             "model_prompt_sha256": hashlib.sha256(b"model-prompt-1").hexdigest(),
             "proposal_call": deepcopy(calls[2]),
             "operation": {"op_id": "op-1", "kind": "ADD", "model_visible": True,
                           "raw_completion": outputs[1], "claim_kind": "similarity",
                           "left": "raven", "relation": "appears in", "right": "moonland",
                           "edge": ["similarity", "raven", "appears in", "moonland"],
                           "claim": "The later context extends the local relation",
                           "prediction": "NONE", "confidence": 0.7,
                           "supersedes": [], "cited_episode_ids": ["ep-1"],
                           "cited_experience_ids": ["obs-1"],
                           "cited_node_ids": ["node-0"],
                           "target_tokens": ["ADD", "node-1"], "loss_mask": [1, 1]},
             "tool_env_result": {"observed": "public observation obs-1"},
             "next_state": {"agenda": "self-check the relation"},
             "model_call_ids": ["call_00002", "call_00003"],
             "event_ids": ["ev-2", "ev-3"]},
            {**scope, "cycle_id": "cy-2", "cycle_index": 2, "microdream_index": 2,
             "trigger": react0, "retrieved_node_ids": ["node-1", "node-0"],
             "model_prompt": "model-prompt-2",
             "model_prompt_sha256": hashlib.sha256(b"model-prompt-2").hexdigest(),
             "proposal_call": deepcopy(calls[4]),
             "public_state": {"agenda": "revisit one earlier node"},
             "operation": {"op_id": "op-2", "kind": "REVISE", "model_visible": True,
                           "raw_completion": outputs[2], "claim_kind": "similarity",
                           "left": "fox", "relation": "differs from", "right": "raven",
                           "edge": ["similarity", "fox", "differs from", "raven"],
                           "claim": "The local relation is corrected after reactivation",
                           "prediction": "NONE", "confidence": 0.7,
                           "supersedes": ["node-0"], "cited_episode_ids": [],
                           "cited_experience_ids": [],
                           "cited_node_ids": ["node-1", "node-0"]},
             "tool_env_result": {"observed": "no current episode during reactivation"},
             "next_state": {"agenda": "preserve old and new claims"},
             "model_call_ids": ["call_00004", "call_00005"],
             "event_ids": ["ev-4", "ev-5"]},
        ],
        "events": events,
        "model_calls": deepcopy(calls),
        "corpus": {
            "schema_version": SCHEMA_VERSION, **scope,
            "lines": [
                _corpus_line(
                    scope, "line-0", "raven appears in moonland.",
                    ["similarity", "raven", "appears in", "moonland"],
                    "node-1", ["ev-2", "ev-3"],
                ),
                _corpus_line(
                    scope, "line-1", "fox differs from raven.",
                    ["similarity", "fox", "differs from", "raven"],
                    "node-2", ["ev-4", "ev-5"],
                ),
            ],
        },
    }


def _retag(trace: dict, prefix: str) -> dict:
    mapping = {old: f"{prefix}-{old}" for old in (
        "ep-0", "ep-1",
        "cy-0", "cy-1", "cy-2", "ev-0", "ev-1", "ev-2", "ev-3", "ev-4", "ev-5",
        "line-0", "line-1", "line-2", "node-0", "node-1", "node-2",
    )}

    def replace(value):
        if isinstance(value, dict):
            return {key: replace(child) for key, child in value.items()}
        if isinstance(value, list):
            return [replace(child) for child in value]
        if isinstance(value, str):
            for old, new in mapping.items():
                value = value.replace(old, new)
        return mapping.get(value, value)

    result = replace(trace)
    for cycle in result["cycles"]:
        cycle["model_prompt_sha256"] = hashlib.sha256(
            cycle["model_prompt"].encode("utf-8")
        ).hexdigest()
    call_objects = list(result["model_calls"])
    call_objects.extend(cycle["proposal_call"] for cycle in result["cycles"])
    call_objects.extend(
        event["self_check_call"] for event in result["events"]
        if event.get("type") == "STATUS_CHANGE"
    )
    for call in call_objects:
        call["prompt_sha256"] = hashlib.sha256(call["prompt"].encode("utf-8")).hexdigest()
        output_hash = hashlib.sha256(call["output"].encode("utf-8")).hexdigest()
        call["output_sha256"] = output_hash
        call["usage"]["output_sha256"] = output_hash
    for event in result["events"]:
        if event.get("type") == "STATUS_CHANGE":
            event["self_check_prompt_sha256"] = hashlib.sha256(
                event["self_check_prompt"].encode("utf-8")
            ).hexdigest()
    return result


def test_accepts_wake_reactivate_and_true_depth():
    trace = valid_trace()
    assert_valid_trace(trace)
    assert validate_trace(trace) == []


def test_reactivation_has_no_fake_current_episode_or_experience():
    trace = valid_trace()
    cycle = trace["cycles"][2]
    assert "episode_id" not in cycle and "experience_ids" not in cycle
    assert cycle["trigger"] == {"kind": "REACTIVATE", "id": "node-1"}


def test_accepts_explicit_current_wake_experience_provenance():
    trace = valid_trace()
    assert trace["events"][0]["cited_experience_ids"] == ["obs-0"]
    assert trace["events"][2]["cited_experience_ids"] == ["obs-1"]
    assert_valid_trace(trace)


def test_rejects_future_or_unseen_experience_citations():
    future = valid_trace()
    future["events"][0]["cited_experience_ids"] = ["obs-1"]
    errors = validate_trace(future)
    assert any("from the future" in error for error in errors)

    unseen = valid_trace()
    unseen["events"][0]["cited_experience_ids"] = ["obs-not-visible"]
    errors = validate_trace(unseen)
    assert any("unknown cited experience" in error for error in errors)

    future_episode = valid_trace()
    scope = _base_scope()
    future_episode["episodes"].append({
        **scope, "episode_id": "ep-2", "episode_index": 2,
        "experience_ids": ["obs-2"],
    })
    future_episode["events"][4]["cited_episode_ids"] = ["ep-2"]
    errors = validate_trace(future_episode)
    assert any("cited episode ep-2 is from the future" in error for error in errors)


def test_enforces_wake_raw_locality_and_reactivation_raw_forbidden():
    prior_episode = valid_trace()
    prior_episode["events"][2]["cited_episode_ids"] = ["ep-0"]
    prior_episode["events"][2]["cited_experience_ids"] = ["obs-0"]
    errors = validate_trace(prior_episode)
    assert any("WAKE episode citation is outside current episode" in error for error in errors)
    assert any("WAKE experience citation is outside current episode" in error for error in errors)

    reactivate = valid_trace()
    reactivate["events"][4]["cited_episode_ids"] = ["ep-1"]
    reactivate["events"][4]["cited_experience_ids"] = ["obs-1"]
    errors = validate_trace(reactivate)
    assert any("REACTIVATE raw episode citations are forbidden" in error for error in errors)
    assert any("REACTIVATE raw experience citations are forbidden" in error for error in errors)


def test_cited_nodes_must_be_retrieved_and_event_retrieval_must_match_cycle():
    cycle_mismatch = valid_trace()
    cycle_mismatch["cycles"][1]["retrieved_node_ids"] = []
    errors = validate_trace(cycle_mismatch)
    assert any("cited_node_ids must be a subset of cycle retrieval" in error for error in errors)

    event_mismatch = valid_trace()
    event_mismatch["events"][2]["retrieved_node_ids"] = []
    errors = validate_trace(event_mismatch)
    assert any("retrieved_node_ids must exactly equal cycle retrieval" in error for error in errors)


def test_rejects_reactivation_with_fake_episode_or_missing_trigger_retrieval():
    trace = valid_trace()
    trace["cycles"][2]["episode_id"] = "ep-1"
    trace["cycles"][2]["experience_ids"] = ["obs-1"]
    trace["cycles"][2]["retrieved_node_ids"] = []
    errors = validate_trace(trace)
    assert any("must not carry a current episode" in error for error in errors)
    assert any("must not carry current experience" in error for error in errors)
    assert any("must retrieve its triggering node" in error for error in errors)


def test_pass_and_open_question_allow_zero_memory_events():
    for operation in ("PASS", "OPEN_QUESTION"):
        trace = valid_trace()
        trace["cycles"][2]["operation"] = {
            "op_id": "op-2", "kind": operation, "model_visible": True,
        }
        if operation == "OPEN_QUESTION":
            trace["cycles"][2]["operation"].update({
                "claim_kind": "similarity", "left": "fox",
                "relation": "resembles", "right": "raven",
                "cited_episode_ids": [], "cited_experience_ids": [],
                "cited_node_ids": ["node-1"],
            })
            output = (
                "OPEN_QUESTION | KIND=similarity | LEFT=fox | "
                "RELATION=resembles | RIGHT=raven | CITES=node-1"
            )
        else:
            output = "PASS"
        trace["cycles"][2]["operation"]["raw_completion"] = output
        call = _call("model-prompt-2", output, call_id="call_00004", cycle_index=2)
        trace["cycles"][2]["proposal_call"] = deepcopy(call)
        trace["cycles"][2]["model_call_ids"] = ["call_00004"]
        trace["cycles"][2]["event_ids"] = []
        trace["events"] = trace["events"][:4]
        trace["model_calls"] = trace["model_calls"][:4] + [call]
        _restore_pre_revision_corpus(trace)
        assert_valid_trace(trace)


def test_malformed_operation_is_recorded_as_noncompliance_not_pass():
    trace = valid_trace()
    trace["cycles"][2]["operation"] = {
        "op_id": "op-2", "kind": "MALFORMED", "model_visible": True,
        "raw_completion": "ADD | malformed extra line",
        "parse_error": "expected exactly one strict operation line",
    }
    trace["cycles"][2]["event_ids"] = []
    call = _call(
        "model-prompt-2", "ADD | malformed extra line",
        call_id="call_00004", cycle_index=2,
    )
    trace["cycles"][2]["proposal_call"] = deepcopy(call)
    trace["cycles"][2]["model_call_ids"] = ["call_00004"]
    trace["events"] = trace["events"][:4]
    trace["model_calls"] = trace["model_calls"][:4] + [call]
    _restore_pre_revision_corpus(trace)
    assert_valid_trace(trace)
    finding = audit_trace(trace)["protocol_noncompliance"]
    assert len(finding) == 1
    assert finding[0]["op_id"] == "op-2"
    assert trace["cycles"][2]["operation"]["kind"] == "MALFORMED"


def test_add_requires_exactly_one_memory_event():
    trace = valid_trace()
    trace["cycles"][0]["event_ids"] = []
    trace["events"].pop(0)
    trace["corpus"]["lines"].pop(0)
    errors = validate_trace(trace)
    assert any("ADD" in error and "exactly 1 memory event" in error for error in errors)


def test_revision_appends_new_node_and_preserves_old_node():
    trace = valid_trace()
    revision = trace["events"][4]
    assert revision["type"] == "REVISE_NODE"
    assert revision["node_id"] == "node-2"
    assert revision["supersedes"] == ["node-0"]
    assert_valid_trace(trace)
    trace["events"][4]["node_id"] = "node-0"
    errors = validate_trace(trace)
    assert any("node_id already exists" in error for error in errors)
    assert any("cannot supersede its new node id" in error for error in errors)


def test_rejects_future_node_and_false_depth():
    trace = valid_trace()
    trace["events"][0]["cited_node_ids"] = ["node-1"]
    trace["events"][0]["depth"] = 9
    errors = validate_trace(trace)
    assert any("unknown node" in error or "future" in error for error in errors)
    assert any("true depth" in error for error in errors)


def test_repeated_edge_and_revision_lineage_cannot_inflate_semantic_depth():
    repeated = valid_trace()
    repeated["events"][2].update({
        "left": "fox", "relation": "resembles", "right": "raven",
        "edge": ["similarity", "fox", "resembles", "raven"],
        "depth": 2,
    })
    repeated["corpus"]["lines"][0]["edge"] = [
        "similarity", "fox", "resembles", "raven"
    ]
    errors = validate_trace(repeated)
    assert any("expected true depth 1, got 2" in error for error in errors)

    revision = valid_trace()
    revision["events"][4]["depth"] = 2
    errors = validate_trace(revision)
    assert any("expected true depth 1, got 2" in error for error in errors)


def test_supported_lineage_depth_does_not_inherit_unresolved_raw_depth():
    trace = {
        "events": [
            {
                "type": "ADD_NODE", "node_id": "node-a", "status": "provisional",
                "edge": ["similarity", "fox", "resembles", "raven"],
                "depth": 1, "supersedes": [], "cited_node_ids": [],
            },
            {
                "type": "STATUS_CHANGE", "node_id": "node-a", "status": "unresolved",
            },
            {
                "type": "ADD_NODE", "node_id": "node-b", "status": "provisional",
                "edge": ["causal", "raven", "predicts", "moonland"],
                "depth": 2, "supersedes": [], "cited_node_ids": ["node-a"],
            },
            {
                "type": "STATUS_CHANGE", "node_id": "node-b", "status": "supported",
            },
        ]
    }
    report = lineage_depth_report(trace)
    assert report["max_raw_depth"] == 2
    assert report["by_node"]["node-a"]["supported_lineage_depth"] == 0
    assert report["by_node"]["node-b"]["supported_lineage_depth"] == 1
    assert report["max_supported_lineage_depth"] == 1


def test_contract_rejects_list_encoded_edge_and_missing_corpus_edge():
    trace = valid_trace()
    trace["events"][2]["right"] = "raven/fox"
    trace["events"][2]["edge"] = [
        "similarity", "raven", "appears in", "raven/fox"
    ]
    trace["corpus"]["lines"][0]["edge"] = [
        "similarity", "raven", "appears in", "raven/fox"
    ]
    errors = validate_trace(trace)
    assert any("one canonical atom" in error or "list/coordination" in error
               for error in errors)

    missing = valid_trace()
    del missing["corpus"]["lines"][0]["edge"]
    errors = validate_trace(missing)
    assert any("explicit canonical semantic edge" in error for error in errors)


def test_rejects_status_noop_or_wrong_append_predecessor():
    trace = valid_trace()
    trace["events"][1]["prev_event_id"] = None
    trace["events"][1]["previous_status"] = "supported"
    errors = validate_trace(trace)
    assert any("append-only ledger" in error for error in errors)
    assert any("current status" in error for error in errors)


def test_rejects_forbidden_visible_artifacts():
    trace = valid_trace()
    trace["cycles"][0]["public_state"]["hidden_truth"] = "node-0"
    trace["cycles"][1]["operation"]["proof_graph"] = {"node-0": "node-1"}
    trace["cycles"][1]["operation"]["target_tokens"] = ["final_answer: blue"]
    errors = validate_trace(trace)
    assert sum("forbidden model-visible" in error for error in errors) >= 3


def test_rejects_hidden_answer_in_exact_prompt_even_with_correct_hashes():
    trace = valid_trace()
    prompt = "public context\nFINAL_ANSWER: raven"
    digest = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
    trace["cycles"][0]["model_prompt"] = prompt
    trace["cycles"][0]["model_prompt_sha256"] = digest
    trace["cycles"][0]["proposal_call"]["prompt"] = prompt
    trace["cycles"][0]["proposal_call"]["prompt_sha256"] = digest
    errors = validate_trace(trace)
    assert any("model_prompt: forbidden model-visible text" in error for error in errors)
    assert any("proposal_call.prompt: forbidden model-visible text" in error for error in errors)


def test_requires_complete_exact_proposal_call_per_cycle():
    missing = valid_trace()
    del missing["cycles"][0]["proposal_call"]
    assert any("proposal_call: required call object" in error
               for error in validate_trace(missing))

    incomplete = valid_trace()
    del incomplete["cycles"][0]["proposal_call"]["usage"]["output_token_ids_sha256"]
    assert any("missing output_token_ids_sha256" in error
               for error in validate_trace(incomplete))

    wrong_output = valid_trace()
    wrong_output["cycles"][0]["proposal_call"]["output"] = "PASS"
    errors = validate_trace(wrong_output)
    assert any("output_sha256: does not hash the recorded text" in error for error in errors)
    assert any("raw_completion: differs from proposal_call output" in error for error in errors)


def test_model_call_rejects_truncation_and_scripted_fallback_is_cpu_only():
    truncated = valid_trace()
    truncated["cycles"][0]["proposal_call"]["usage"]["prompt_truncated"] = True
    assert any("model calls must not truncate prompts" in error
               for error in validate_trace(truncated))

    non_fixture = valid_trace()
    non_fixture["cycles"][0]["proposal_call"]["usage"]["source"] = "scripted_fallback"
    assert any("allowed only in a CPU fixture" in error
               for error in validate_trace(non_fixture))

    fixture = valid_trace()
    fixture["cpu_fixture"] = True
    fixture["cycles"][0]["proposal_call"]["usage"]["source"] = "scripted_fallback"
    fixture["model_calls"][0]["usage"]["source"] = "scripted_fallback"
    assert_valid_trace(fixture)
    findings = audit_trace(fixture)["protocol_noncompliance"]
    assert any(item["kind"] == "scripted_fallback" and item["call"] == "proposal_call"
               for item in findings)


def test_status_change_requires_audited_self_check_call():
    missing = valid_trace()
    del missing["events"][1]["self_check_call"]
    assert any("self_check_call: required call object" in error
               for error in validate_trace(missing))

    hidden = valid_trace()
    prompt = "self check with HIDDEN_ANSWER: raven"
    digest = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
    hidden["events"][1]["self_check_prompt"] = prompt
    hidden["events"][1]["self_check_prompt_sha256"] = digest
    hidden["events"][1]["self_check_call"]["prompt"] = prompt
    hidden["events"][1]["self_check_call"]["prompt_sha256"] = digest
    assert any("self_check_call.prompt: forbidden model-visible text" in error
               for error in validate_trace(hidden))

    fallback = valid_trace()
    fallback["cpu_fixture"] = True
    fallback["events"][1]["self_check_call"]["usage"]["source"] = "scripted_fallback"
    fallback["model_calls"][1]["usage"]["source"] = "scripted_fallback"
    assert_valid_trace(fallback)
    assert any(item["kind"] == "scripted_fallback" and item["call"] == "self_check_call"
               for item in audit_trace(fallback)["protocol_noncompliance"])


def test_open_question_is_typed_and_rejects_freeform_question():
    trace = valid_trace()
    cycle = trace["cycles"][2]
    cycle["operation"] = {
        "op_id": "op-2", "kind": "OPEN_QUESTION", "model_visible": True,
        "question": "Could anything be related?",
        "cited_episode_ids": [], "cited_experience_ids": [],
        "cited_node_ids": ["node-0"],
    }
    cycle["proposal_call"] = _call(
        "model-prompt-2", "OPEN_QUESTION | QUESTION=Could anything be related? | CITES=node-0"
    )
    cycle["event_ids"] = []
    trace["events"].pop()
    trace["corpus"]["lines"].pop()
    errors = validate_trace(trace)
    assert any("freeform OPEN_QUESTION text is forbidden" in error for error in errors)
    assert any("required typed OPEN_QUESTION field" in error for error in errors)


def test_revision_must_cite_superseded_and_cannot_replace_unrelated_edge():
    uncited = valid_trace()
    uncited["events"][4]["cited_node_ids"] = []
    assert any("must cite its superseded node" in error for error in validate_trace(uncited))

    unrelated = valid_trace()
    unrelated["events"][4].update({
        "left": "sun", "relation": "warms", "right": "stone",
        "edge": ["similarity", "sun", "warms", "stone"],
    })
    unrelated["corpus"]["lines"][1]["edge"] = [
        "similarity", "sun", "warms", "stone"
    ]
    errors = validate_trace(unrelated)
    assert any("cannot replace an unrelated semantic edge" in error for error in errors)
    unrelated["events"][4]["depth"] = 2
    errors = validate_trace(unrelated)
    assert any("expected true depth 1, got 2" in error for error in errors)


def test_rejects_nested_scope_leak_and_shared_memory_adapter():
    first = valid_trace(world_id="world-0", life_id="life-a", memory_adapter_id="mem-a",
                        split="train", split_id="train-worlds")
    second = valid_trace(world_id="world-1", life_id="life-b", memory_adapter_id="mem-a",
                         split="dev", split_id="dev-worlds")
    second["cycles"][0]["next_state"]["world_id"] = "world-0"
    second = _retag(second, "second")
    errors = validate_dataset([first, second])
    assert any("cross-world/life state leakage" in error for error in errors)
    assert any("reused across lives" in error for error in errors)


def test_rejects_missing_split_id_and_world_split_leakage():
    first = valid_trace(world_id="world-shared", life_id="life-a", split="train",
                        split_id="train-worlds")
    second = valid_trace(world_id="world-shared", life_id="life-b", split="test",
                         split_id="test-worlds")
    second["split_id"] = None
    errors = validate_dataset([first, second])
    assert any("missing non-empty split_id" in error for error in errors)
    assert any("multiple splits" in error for error in errors)


def test_rejects_corpus_line_without_node_or_supporting_event():
    trace = valid_trace()
    trace["corpus"]["lines"][0]["node_ids"] = ["missing-node"]
    trace["corpus"]["lines"][0]["provenance"]["event_ids"] = ["ev-1"]
    errors = validate_trace(trace)
    assert any("unknown node" in error for error in errors)
    assert any("does not support" in error for error in errors)


def test_dataset_accepts_distinct_life_adapters_and_holdout_world():
    train = valid_trace(world_id="world-train", life_id="life-train",
                        memory_adapter_id="mem-train", split="train",
                        split_id="train-worlds")
    holdout = _retag(valid_trace(world_id="world-holdout", life_id="life-holdout",
                                 memory_adapter_id="mem-holdout", split="holdout",
                                 split_id="holdout-worlds"), "holdout")
    assert_valid_dataset([train, holdout])


def test_assert_helper_raises_for_bad_depth():
    trace = valid_trace()
    trace["events"][2]["depth"] = 99
    try:
        assert_valid_trace(trace)
    except ContractError:
        pass
    else:
        raise AssertionError("invalid depth was accepted")


def test_recorded_outputs_bind_operation_event_and_self_check_fields_exactly():
    operation = valid_trace()
    operation["cycles"][0]["operation"]["right"] = "moonland"
    assert any("right: differs from parsed proposal output" in error
               for error in validate_trace(operation))

    event = valid_trace()
    event["events"][0]["claim"] = "A different structured claim"
    assert any("events[0].claim: differs from parsed proposal output" in error
               for error in validate_trace(event))

    status = valid_trace()
    status["events"][1]["reason"] = "A rewritten reason"
    assert any("reason: differs from parsed self-check output" in error
               for error in validate_trace(status))

    citations = valid_trace()
    citations["events"][1]["cited_experience_ids"] = []
    assert any("status citations differ from parsed self-check output" in error
               for error in validate_trace(citations))


def test_condition_schedule_and_call_ledger_are_bijective():
    condition = valid_trace()
    condition["schedule"]["drift_enabled"] = False
    assert any("drift_enabled: differs from condition" in error
               for error in validate_trace(condition))

    omitted = valid_trace()
    omitted["cycles"].pop()
    omitted["events"] = omitted["events"][:4]
    omitted["model_calls"] = omitted["model_calls"][:4]
    omitted["corpus"]["lines"].pop()
    assert any("missing required REACTIVATE(node-1)" in error
               for error in validate_trace(omitted))

    missing = valid_trace()
    missing["model_calls"].pop()
    assert any("missing from model_calls" in error or "absent from ledger" in error
               for error in validate_trace(missing))

    duplicate = valid_trace()
    duplicate["cycles"][1]["model_call_ids"][0] = "call_00000"
    assert any("differs from nested calls in execution order" in error
               for error in validate_trace(duplicate))

    leftover = valid_trace()
    extra = deepcopy(leftover["model_calls"][-1])
    extra["call_id"] = "call_00006"
    leftover["model_calls"].append(extra)
    assert any("unconsumed call records" in error for error in validate_trace(leftover))

    nested = valid_trace()
    nested["events"][1]["self_check_call"]["reason"] = "not a call field"
    assert any("nested self_check call differs from model_calls ledger" in error
               for error in validate_trace(nested))


def test_corpus_text_and_provenance_are_exactly_one_canonical_memory_event():
    text = valid_trace()
    text["corpus"]["lines"][0]["text"] = "A polished paraphrase."
    assert any("not the canonical rendering" in error for error in validate_trace(text))

    many_nodes = valid_trace()
    many_nodes["corpus"]["lines"][0]["node_ids"] = ["node-0", "node-1"]
    assert any("requires exactly one source node" in error
               for error in validate_trace(many_nodes))

    wrong_event = valid_trace()
    wrong_event["corpus"]["lines"][0]["provenance"]["event_ids"] = ["ev-1"]
    assert any("must name exactly the canonical node-creation/status events" in error
               for error in validate_trace(wrong_event))
