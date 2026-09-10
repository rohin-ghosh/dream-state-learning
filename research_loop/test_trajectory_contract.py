"""CPU-only synthetic tests for the inactive LOOP-adapter data contract."""

from __future__ import annotations

from copy import deepcopy

from .trajectory_contract import (
    SCHEMA_VERSION,
    ContractError,
    assert_valid_dataset,
    assert_valid_trajectory,
    training_tokens,
    validate_dataset,
)


SCOPE = {"world_id": "w-dev-00", "skin_id": "aligned", "life_id": "life-00"}


def _record(phase: str, number: int, previous: str | None, **extra):
    record = {
        **SCOPE,
        "record_id": f"r-{number}",
        "transition_id": f"t-{number // 4}",
        "prev_record_id": previous,
        "phase": phase,
        "model_visible": True,
        "provenance": {
            "world_id": SCOPE["world_id"],
            "skin_id": SCOPE["skin_id"],
            "life_id": SCOPE["life_id"],
            "source_ids": [f"obs-{number // 4}"],
        },
        "tokens": [phase],
        "loss_mask": [0],
    }
    record.update(extra)
    return record


def valid_trace(
    *, world_id: str = "w-dev-00", life_id: str = "life-00",
    memory_adapter_id: str | None = "mem-life-00", split: str = "dev",
    split_id: str = "dev-worlds-v02",
):
    scope = {"world_id": world_id, "skin_id": "aligned", "life_id": life_id}
    records = []
    previous = None
    phases = (
        ("PUBLIC_STATE", {"state": {"goal": "find next dependency", "budget": 12}}, [0]),
        ("ASSISTANT_OPERATION", {
            "operation": "QUERY", "query": {"kind": "atomic", "args": "fox at source-0"},
        }, [1, 1]),
        ("TOOL/ENV_RESULT", {"result": {"observation": "public color token: blue"}}, [0]),
        ("NEXT_STATE", {"state": {"resolved": ["obs-0"], "remaining": ["parent"]}}, [0]),
    )
    for number, (phase, payload, mask) in enumerate(phases):
        record = {
            **scope,
            "record_id": f"{life_id}-r{number}",
            "transition_id": "t-0",
            "prev_record_id": previous,
            "phase": phase,
            "model_visible": True,
            "provenance": {
                "world_id": world_id, "skin_id": "aligned", "life_id": life_id,
                "source_ids": ["obs-0"],
            },
            "tokens": [phase, "cognitive"][:len(mask)],
            "loss_mask": mask,
            **payload,
        }
        if phase == "ASSISTANT_OPERATION":
            record["tokens"] = ["QUERY", "atomic"]
        previous = record["record_id"]
        records.append(record)
    return {
        "schema_version": SCHEMA_VERSION,
        "trace_id": f"trace-{life_id}",
        "split": split,
        "split_id": split_id,
        **scope,
        "memory_mode": "mounted" if memory_adapter_id else "none",
        "memory_adapter_id": memory_adapter_id,
        "loop_adapter_id": "loop-bc-v0",
        "delayed_outcome": {"success": True, "efficiency": 0.75, "steps": 1},
        "records": records,
    }


def test_accepts_causal_trace_and_masks_only_operation_tokens():
    trace = valid_trace()
    assert_valid_trajectory(trace)
    assert training_tokens(trace) == ["QUERY", "atomic"]


def test_accepts_no_memory_control_with_null_memory_adapter():
    trace = valid_trace(memory_adapter_id=None)
    assert_valid_trajectory(trace)


def test_rejects_hidden_answer_in_model_visible_state():
    trace = valid_trace()
    trace["records"][0]["state"]["final_answer"] = "blue"
    assert any("forbidden" in error for error in validate_dataset([trace]))


def test_rejects_checker_artifact_and_direct_answer_operation():
    trace = valid_trace()
    trace["records"][0]["state"]["proof_graph"] = {"parents": ["p0"]}
    trace["records"][1]["operation"] = "ANSWER"
    errors = validate_dataset([trace])
    assert any("forbidden" in error for error in errors)
    assert any("operation must be" in error for error in errors)


def test_rejects_non_causal_order_and_environment_loss_mask():
    trace = valid_trace()
    trace["records"][1]["phase"] = "NEXT_STATE"
    trace["records"][2]["loss_mask"] = [1]
    errors = validate_dataset([trace])
    assert any("expected phase" in error for error in errors)
    assert any("only assistant" in error for error in errors)


def test_rejects_missing_split_id():
    trace = valid_trace()
    del trace["split_id"]
    assert any("split_id" in error for error in validate_dataset([trace]))


def test_rejects_cross_world_record_state_leakage():
    first = valid_trace(world_id="w-train-00", life_id="life-a", split="train", split_id="train")
    second = valid_trace(world_id="w-test-00", life_id="life-b", split="test", split_id="test")
    second["records"][0]["record_id"] = first["records"][0]["record_id"]
    errors = validate_dataset([first, second])
    assert any("crosses world/life scope" in error for error in errors)


def test_rejects_nested_state_from_another_world():
    trace = valid_trace()
    trace["records"][3]["state"]["world_id"] = "w-other"
    assert any("cross-world/life state leakage" in error for error in validate_dataset([trace]))


def test_rejects_world_in_multiple_splits():
    first = valid_trace(world_id="shared-world", life_id="life-a", split="train", split_id="train")
    second = valid_trace(world_id="shared-world", life_id="life-b", split="test", split_id="test")
    assert any("multiple splits" in error for error in validate_dataset([first, second]))


def test_rejects_non_reset_memory_adapter_across_lives():
    first = valid_trace(world_id="w-0", life_id="life-a", memory_adapter_id="mem-shared")
    second = valid_trace(world_id="w-1", life_id="life-b", memory_adapter_id="mem-shared")
    assert any("reused across lives" in error for error in validate_dataset([first, second]))


def test_rejects_memory_adapter_change_within_life():
    first = valid_trace(world_id="w-0", life_id="life-a", memory_adapter_id="mem-a")
    second = valid_trace(world_id="w-0", life_id="life-a", memory_adapter_id="mem-b")
    assert any("changes within a life" in error for error in validate_dataset([first, second]))


def test_assertion_raises_for_invalid_trace():
    trace = valid_trace()
    trace["records"][3]["prev_record_id"] = "deleted-record"
    try:
        assert_valid_trajectory(trace)
    except ContractError:
        pass
    else:
        raise AssertionError("invalid append-only chain was accepted")
