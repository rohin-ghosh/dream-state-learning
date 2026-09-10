"""Hash-bound deterministic runtime and absolute resource/canary validation."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Mapping

from .contract import (
    DECODING,
    MODEL_ID,
    MODEL_REVISION,
    RESOURCE_CEILINGS,
    TOKENIZER_REVISION,
    build_opportunity_registry,
    build_roster,
    digest,
)
from .machine import validate_operation
from .memory import conservative_cpu_token_count


_HASH = re.compile(r"^[0-9a-f]{64}$")


class RuntimeContractError(ValueError):
    pass


REQUIRED_HASH_COMPONENTS = (
    "tokenizer_files",
    "chat_template",
    "system_prompt",
    "user_prompt_renderer",
    "operation_schema",
    "row_schema",
    "parser",
    "stop_bytes",
    "target_condition_order",
    "target_manifest",
    "source",
    "builder_outputs",
    "reducer",
    "runner",
    "container",
    "backend",
    "cuda",
    "driver",
    "runtime",
    "reset_procedure",
    "failure_policy",
)


@dataclass(frozen=True)
class GateResourceUsage:
    a40_gpu_hours: float
    wall_seconds_from_canary: int
    stored_artifact_bytes: int
    incremental_external_usd: float

    def validate(self) -> None:
        values = (
            self.a40_gpu_hours,
            self.wall_seconds_from_canary,
            self.stored_artifact_bytes,
            self.incremental_external_usd,
        )
        if any(isinstance(value, bool) or value < 0 for value in values):
            raise RuntimeContractError("resource usage must be non-negative")
        if self.a40_gpu_hours > RESOURCE_CEILINGS["a40_gpu_hours"]:
            raise RuntimeContractError("aggregate A40 GPU-hour ceiling exceeded")
        if self.wall_seconds_from_canary > RESOURCE_CEILINGS["gpu_wall_seconds"]:
            raise RuntimeContractError("GPU wall-time ceiling exceeded")
        if self.stored_artifact_bytes > RESOURCE_CEILINGS["artifact_bytes"]:
            raise RuntimeContractError("artifact storage ceiling exceeded")
        if self.incremental_external_usd != 0.0:
            raise RuntimeContractError("incremental external spend must remain USD 0.00")


@dataclass(frozen=True)
class RuntimeClosure:
    model_id: str
    model_revision: str
    tokenizer_revision: str
    decoding: Mapping[str, Any]
    component_hashes: Mapping[str, str]
    process_reset: str
    kv_reset: str
    cache_reset: str
    incremental_external_usd: float

    def validate(self) -> str:
        if (self.model_id, self.model_revision, self.tokenizer_revision) != (
            MODEL_ID,
            MODEL_REVISION,
            TOKENIZER_REVISION,
        ):
            raise RuntimeContractError("model/tokenizer revision is not the ratified pin")
        if dict(self.decoding) != DECODING:
            raise RuntimeContractError("decoding bytes differ from the deterministic lock")
        if set(self.component_hashes) != set(REQUIRED_HASH_COMPONENTS):
            raise RuntimeContractError("runtime closure component set is incomplete")
        if any(_HASH.fullmatch(value) is None for value in self.component_hashes.values()):
            raise RuntimeContractError("runtime closure contains a non-SHA256 component")
        if (self.process_reset, self.kv_reset, self.cache_reset) != (
            "FRESH_PROCESS_PER_TRAJECTORY",
            "EMPTY_KV_BEFORE_FIRST_SLOT",
            "EMPTY_READER_AND_BACKEND_CACHE",
        ):
            raise RuntimeContractError("fresh process/KV/cache reset lock differs")
        if self.incremental_external_usd != RESOURCE_CEILINGS["incremental_external_usd"]:
            raise RuntimeContractError("incremental external spend must be USD 0.00")
        return digest(
            {
                "model_id": self.model_id,
                "model_revision": self.model_revision,
                "tokenizer_revision": self.tokenizer_revision,
                "decoding": dict(self.decoding),
                "component_hashes": dict(self.component_hashes),
                "process_reset": self.process_reset,
                "kv_reset": self.kv_reset,
                "cache_reset": self.cache_reset,
                "incremental_external_usd": self.incremental_external_usd,
                "resource_ceilings": dict(RESOURCE_CEILINGS),
            }
        )


@dataclass(frozen=True)
class CanaryReceipt:
    runtime_closure_sha256: str
    canary_input_sha256: str
    registered_target_hashes: tuple[str, ...]
    raw_output: bytes
    model_loaded: bool
    tokenizer_loaded: bool
    backend_deterministic: bool
    scientific_opportunities_consumed: int
    input_tokens: int
    output_tokens: int
    input_bytes: int
    output_bytes: int


def validate_canary_receipt(receipt: CanaryReceipt, closure: RuntimeClosure) -> dict[str, Any]:
    closure_hash = closure.validate()
    if receipt.runtime_closure_sha256 != closure_hash:
        raise RuntimeContractError("canary runtime hash differs")
    if receipt.canary_input_sha256 in set(receipt.registered_target_hashes):
        raise RuntimeContractError("canary overlaps a registered scientific target")
    if not (receipt.model_loaded and receipt.tokenizer_loaded and receipt.backend_deterministic):
        raise RuntimeContractError("canary load/tokenizer/determinism check failed")
    if receipt.scientific_opportunities_consumed != 0:
        raise RuntimeContractError("canary consumed a scientific opportunity")
    validate_operation(
        __import__("json").loads(receipt.raw_output),
        token_counter=conservative_cpu_token_count,
    )
    limits = {
        "input_tokens_per_call": receipt.input_tokens,
        "output_tokens_per_call": receipt.output_tokens,
        "input_bytes_per_call": receipt.input_bytes,
        "output_bytes_per_call": receipt.output_bytes,
    }
    if any(value > RESOURCE_CEILINGS[name] for name, value in limits.items()):
        raise RuntimeContractError("canary exceeded an absolute per-call ceiling")
    return {
        "canary_valid": True,
        "runtime_closure_sha256": closure_hash,
        "scientific_opportunities_consumed": 0,
    }


def cpu_runtime_manifest() -> dict[str, Any]:
    """Return the exact prospective closure without claiming a GPU canary ran."""
    roster = build_roster()
    registry = build_opportunity_registry(roster)
    return {
        "model_id": MODEL_ID,
        "model_revision": MODEL_REVISION,
        "tokenizer_revision": TOKENIZER_REVISION,
        "decoding": DECODING,
        "resource_ceilings": dict(RESOURCE_CEILINGS),
        "trajectory_count": len(roster),
        "registered_opportunity_count": len(registry),
        "maximum_scientific_dispatches": len(registry),
        "actual_gpu_canary_run": False,
        "runtime_hashes_bound": False,
        "gpu_dispatch_ready": False,
    }
