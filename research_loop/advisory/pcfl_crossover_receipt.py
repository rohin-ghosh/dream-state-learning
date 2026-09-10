#!/usr/bin/env python3
"""Model-free physical-carrier receipt for PEFT safetensors adapters.

This script never imports a model, tokenizer, torch, PEFT, or safetensors. It
reads the immutable safetensors header and hashes the on-disk artifacts. The
result distinguishes the serialized life-specific code, tensor payload that
must be mounted for acting, common configuration sidecars, and rate crossover
requirements. It is an accounting instrument, not an E3 experiment.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
from collections import Counter
from pathlib import Path
from typing import Any


DTYPE_BYTES = {
    "BOOL": 1,
    "U8": 1,
    "I8": 1,
    "F8_E4M3": 1,
    "F8_E5M2": 1,
    "U16": 2,
    "I16": 2,
    "F16": 2,
    "BF16": 2,
    "U32": 4,
    "I32": 4,
    "F32": 4,
    "U64": 8,
    "I64": 8,
    "F64": 8,
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def product(values: list[int]) -> int:
    out = 1
    for value in values:
        out *= value
    return out


EXPECTED_MODULES = {
    "q_proj",
    "k_proj",
    "v_proj",
    "o_proj",
    "gate_proj",
    "up_proj",
    "down_proj",
}
MODULE_BRANCH = {
    "q_proj": "self_attn",
    "k_proj": "self_attn",
    "v_proj": "self_attn",
    "o_proj": "self_attn",
    "gate_proj": "mlp",
    "up_proj": "mlp",
    "down_proj": "mlp",
}
TENSOR_NAME = re.compile(
    r"^base_model\.model\.model\.layers\.(?P<layer>0|[1-9][0-9]*)\."
    r"(?P<branch>self_attn|mlp)\."
    r"(?P<module>q_proj|k_proj|v_proj|o_proj|gate_proj|up_proj|down_proj)\."
    r"lora_(?P<side>A|B)\.weight$"
)


def strict_denominator_min(
    numerator: int, rate_numerator: int, rate_denominator: int
) -> int:
    """Smallest integer D with numerator/D < rate_numerator/rate_denominator."""
    if numerator < 0 or rate_numerator <= 0 or rate_denominator <= 0:
        raise ValueError("invalid exact-rate inputs")
    return (numerator * rate_denominator) // rate_numerator + 1


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object key: {key!r}")
        result[key] = value
    return result


def inspect_adapter(
    path: Path,
    native_context_tokens: int,
    include_tensors: bool,
    expected_layers: int,
    expected_rank: int | None,
    expected_dtype: str,
    hidden_size: int,
    kv_size: int,
    intermediate_size: int,
) -> dict[str, Any]:
    file_bytes = path.stat().st_size
    with path.open("rb") as handle:
        header_len_bytes = handle.read(8)
        if len(header_len_bytes) != 8:
            raise ValueError(f"{path}: truncated safetensors length prefix")
        header_len = struct.unpack("<Q", header_len_bytes)[0]
        if header_len <= 0 or 8 + header_len > file_bytes:
            raise ValueError(f"{path}: invalid safetensors header length {header_len}")
        header_raw = handle.read(header_len)
        if len(header_raw) != header_len:
            raise ValueError(f"{path}: truncated safetensors JSON header")
    try:
        header = json.loads(header_raw, object_pairs_hook=reject_duplicate_keys)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"{path}: invalid safetensors JSON header: {exc}") from exc
    if not isinstance(header, dict):
        raise ValueError(f"{path}: safetensors header must be a JSON object")
    if header.get("__metadata__") != {"format": "pt"}:
        raise ValueError(f"{path}: unexpected safetensors metadata")
    tensors = {key: value for key, value in header.items() if key != "__metadata__"}
    if not tensors:
        raise ValueError(f"{path}: no tensors")

    dtype_counts: Counter[str] = Counter()
    dtype_numel: Counter[str] = Counter()
    module_counts: Counter[str] = Counter()
    rank_candidates: list[int] = []
    payload_bytes_from_offsets = 0
    payload_bytes_from_shapes = 0
    total_numel = 0
    max_end = 0
    tensor_rows = []
    pair_specs: dict[tuple[int, str], dict[str, list[int]]] = {}
    intervals: list[tuple[int, int, str]] = []

    for name, spec in sorted(tensors.items()):
        match = TENSOR_NAME.fullmatch(name)
        if match is None:
            raise ValueError(f"{path}: unexpected tensor namespace: {name}")
        layer = int(match.group("layer"))
        branch = match.group("branch")
        module = match.group("module")
        side = match.group("side")
        if layer < 0 or layer >= expected_layers:
            raise ValueError(f"{path}: unexpected layer {layer} in {name}")
        if branch != MODULE_BRANCH[module]:
            raise ValueError(f"{path}: module {module} appears under branch {branch}")
        if not isinstance(spec, dict) or set(spec) != {"dtype", "shape", "data_offsets"}:
            raise ValueError(f"{path}: invalid tensor schema for {name}")
        dtype = spec["dtype"]
        if dtype not in DTYPE_BYTES:
            raise ValueError(f"{path}: unsupported dtype {dtype!r} for {name}")
        if dtype != expected_dtype:
            raise ValueError(
                f"{path}: expected dtype {expected_dtype}, found {dtype} for {name}"
            )
        if (
            not isinstance(spec["shape"], list)
            or len(spec["shape"]) != 2
            or any(
                not isinstance(item, int) or isinstance(item, bool) or item <= 0
                for item in spec["shape"]
            )
        ):
            raise ValueError(f"{path}: invalid non-positive 2-D shape for {name}")
        if (
            not isinstance(spec["data_offsets"], list)
            or len(spec["data_offsets"]) != 2
            or any(
                not isinstance(item, int) or isinstance(item, bool)
                for item in spec["data_offsets"]
            )
        ):
            raise ValueError(f"{path}: invalid data offsets for {name}")
        shape = list(spec["shape"])
        start, end = list(spec["data_offsets"])
        if start < 0 or end <= start:
            raise ValueError(f"{path}: negative, reversed, or empty interval for {name}")
        numel = product(shape)
        expected = numel * DTYPE_BYTES[dtype]
        actual = end - start
        if actual != expected:
            raise ValueError(
                f"{path}: {name} payload {actual} != shape/dtype bytes {expected}"
            )
        total_numel += numel
        payload_bytes_from_offsets += actual
        payload_bytes_from_shapes += expected
        max_end = max(max_end, end)
        intervals.append((start, end, name))
        dtype_counts[dtype] += 1
        dtype_numel[dtype] += numel
        module_counts[module] += 1
        key = (layer, module)
        if side in pair_specs.setdefault(key, {}):
            raise ValueError(f"{path}: duplicate LoRA side {side} for layer/module {key}")
        pair_specs[key][side] = shape
        if side == "A":
            rank_candidates.append(shape[0])
        else:
            rank_candidates.append(shape[1])
        tensor_rows.append(
            {
                "name": name,
                "dtype": dtype,
                "shape": shape,
                "data_offsets": [start, end],
                "numel": numel,
                "bytes": actual,
            }
        )

    data_start = 8 + header_len
    data_buffer_bytes = file_bytes - data_start
    previous_end = 0
    for start, end, name in sorted(intervals):
        if start != previous_end:
            kind = "overlap" if start < previous_end else "gap"
            raise ValueError(
                f"{path}: tensor data partition {kind} before {name}: "
                f"expected start {previous_end}, got {start}"
            )
        previous_end = end
    if previous_end != data_buffer_bytes or max_end != data_buffer_bytes:
        raise ValueError(
            f"{path}: tensor partition ends at {previous_end}, data buffer is {data_buffer_bytes}"
        )
    if payload_bytes_from_offsets != data_buffer_bytes:
        raise ValueError(f"{path}: summed tensor payload does not equal data buffer")

    expected_pairs = {
        (layer, module)
        for layer in range(expected_layers)
        for module in EXPECTED_MODULES
    }
    if set(pair_specs) != expected_pairs:
        missing = sorted(expected_pairs - set(pair_specs))
        extra = sorted(set(pair_specs) - expected_pairs)
        raise ValueError(f"{path}: layer/module mismatch; missing={missing}, extra={extra}")
    for key, sides in sorted(pair_specs.items()):
        if set(sides) != {"A", "B"}:
            raise ValueError(f"{path}: incomplete A/B pair for {key}: {sorted(sides)}")
        a_shape, b_shape = sides["A"], sides["B"]
        if a_shape[0] != b_shape[1]:
            raise ValueError(f"{path}: inconsistent A/B rank for {key}: {a_shape}, {b_shape}")
    ranks = sorted(set(rank_candidates))
    if len(ranks) != 1:
        raise ValueError(f"{path}: inconsistent ranks {ranks}")
    if expected_rank is not None and ranks != [expected_rank]:
        raise ValueError(f"{path}: expected rank {expected_rank}, found {ranks}")
    rank = ranks[0]
    output_size = {
        "q_proj": hidden_size,
        "k_proj": kv_size,
        "v_proj": kv_size,
        "o_proj": hidden_size,
        "gate_proj": intermediate_size,
        "up_proj": intermediate_size,
        "down_proj": hidden_size,
    }
    input_size = {
        "q_proj": hidden_size,
        "k_proj": hidden_size,
        "v_proj": hidden_size,
        "o_proj": hidden_size,
        "gate_proj": hidden_size,
        "up_proj": hidden_size,
        "down_proj": intermediate_size,
    }
    for (layer, module), sides in sorted(pair_specs.items()):
        expected_a = [rank, input_size[module]]
        expected_b = [output_size[module], rank]
        if sides["A"] != expected_a or sides["B"] != expected_b:
            raise ValueError(
                f"{path}: wrong Qwen projection shape for layer {layer} {module}; "
                f"expected A={expected_a}, B={expected_b}, "
                f"found A={sides['A']}, B={sides['B']}"
            )
    expected_numel = expected_layers * rank * sum(
        input_size[module] + output_size[module] for module in EXPECTED_MODULES
    )
    if total_numel != expected_numel:
        raise ValueError(
            f"{path}: expected {expected_numel} total elements, found {total_numel}"
        )

    config = path.parent / "adapter_config.json"
    discovered_sidecars = []
    if config.exists():
        discovered_sidecars.append(
            {
                "path": str(config.resolve()),
                "bytes": config.stat().st_size,
                "sha256": sha256_file(config),
            }
        )
    sidecar_bytes = sum(item["bytes"] for item in discovered_sidecars)
    known_file_subtotal_bytes = file_bytes + sidecar_bytes
    native_8x_tokens = native_context_tokens * 8

    tensor_manifest_json = json.dumps(
        tensor_rows, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    result = {
        "path": str(path.resolve()),
        "sha256": sha256_file(path),
        "file_bytes": file_bytes,
        "header_prefix_bytes": 8,
        "header_json_bytes": header_len,
        "tensor_count": len(tensors),
        "total_numel": total_numel,
        "rank_candidates": ranks,
        "dtype_tensor_counts": dict(sorted(dtype_counts.items())),
        "dtype_numel": dict(sorted(dtype_numel.items())),
        "module_leaf_counts": dict(sorted(module_counts.items())),
        "tensor_payload_bytes": payload_bytes_from_offsets,
        "serialized_tensor_payload_bytes_from_header": payload_bytes_from_shapes,
        "hypothetical_bf16_tensor_payload_floor_bytes": total_numel * 2,
        "serialization_overhead_bytes": file_bytes - payload_bytes_from_offsets,
        "metadata": header.get("__metadata__", {}),
        "tensor_manifest_sha256": hashlib.sha256(tensor_manifest_json).hexdigest(),
        "discovered_config_sidecars": discovered_sidecars,
        "adapter_safetensors_file_bytes": file_bytes,
        "discovered_config_sidecar_bytes": sidecar_bytes,
        "known_serialized_file_subtotal_bytes": known_file_subtotal_bytes,
        "rate_crossover": {
            "expanded_bytes_min_for_adapter_file_ratio_lt_0.50": strict_denominator_min(
                file_bytes, 1, 2
            ),
            "raw_bytes_min_for_adapter_file_ratio_lt_0.35": strict_denominator_min(
                file_bytes, 7, 20
            ),
            "expanded_bytes_min_for_known_file_subtotal_ratio_lt_0.50": strict_denominator_min(
                known_file_subtotal_bytes, 1, 2
            ),
            "raw_bytes_min_for_known_file_subtotal_ratio_lt_0.35": strict_denominator_min(
                known_file_subtotal_bytes, 7, 20
            ),
            "native_context_tokens": native_context_tokens,
            "eight_x_native_context_tokens": native_8x_tokens,
            "required_expanded_bytes_per_token_at_8x_for_adapter_file_ratio_lt_0.50": (
                strict_denominator_min(file_bytes, 1, 2) / native_8x_tokens
            ),
        },
    }
    if include_tensors:
        result["tensors"] = tensor_rows
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--native-context-tokens", type=int, default=16_384)
    parser.add_argument("--include-tensors", action="store_true")
    parser.add_argument("--expected-layers", type=int, default=28)
    parser.add_argument("--hidden-size", type=int, default=3584)
    parser.add_argument("--kv-size", type=int, default=512)
    parser.add_argument("--intermediate-size", type=int, default=18944)
    parser.add_argument(
        "--expected-ranks",
        help="comma-separated expected rank for each positional adapter path",
    )
    parser.add_argument(
        "--expected-dtypes",
        default="F32",
        help="one dtype for all paths or comma-separated dtype per path",
    )
    args = parser.parse_args()
    expected_ranks: list[int | None]
    if args.expected_ranks:
        expected_ranks = [int(item) for item in args.expected_ranks.split(",")]
        if len(expected_ranks) != len(args.paths):
            parser.error("--expected-ranks must contain one rank per adapter path")
    else:
        expected_ranks = [None] * len(args.paths)
    expected_dtypes = args.expected_dtypes.split(",")
    if len(expected_dtypes) == 1:
        expected_dtypes *= len(args.paths)
    if len(expected_dtypes) != len(args.paths):
        parser.error("--expected-dtypes must contain one dtype or one per adapter path")
    records = [
        inspect_adapter(
            path,
            args.native_context_tokens,
            args.include_tensors,
            args.expected_layers,
            expected_rank,
            expected_dtype,
            args.hidden_size,
            args.kv_size,
            args.intermediate_size,
        )
        for path, expected_rank, expected_dtype in zip(
            args.paths, expected_ranks, expected_dtypes
        )
    ]
    print(
        json.dumps(
            {
                "schema": "pcfl_physical_carrier_intercept_receipt_v4",
                "model_free": True,
                "tokenizer_free": True,
                "validation_profile": {
                    "namespace_template": (
                        "base_model.model.model.layers.{layer}."
                        "{self_attn|mlp}.{module}.lora_{A|B}.weight"
                    ),
                    "expected_layers": args.expected_layers,
                    "hidden_size": args.hidden_size,
                    "kv_output_size": args.kv_size,
                    "intermediate_size": args.intermediate_size,
                    "module_branches": dict(sorted(MODULE_BRANCH.items())),
                    "expected_ranks_by_path": {
                        str(path): rank
                        for path, rank in zip(args.paths, expected_ranks)
                    },
                    "expected_dtypes_by_path": {
                        str(path): dtype
                        for path, dtype in zip(args.paths, expected_dtypes)
                    },
                },
                "accounting_notes": {
                    "adapter_file": "complete serialized safetensors file, not a complete life-state census",
                    "known_file_subtotal": "adapter file plus discovered sibling adapter_config.json only",
                    "payload": "serialized tensor payload inferred from validated header; runtime residency unobserved",
                    "common_state": "base model may be shared but is not inspected or counted by this script",
                    "retained_state": "historical checkpoints, runtime buffers, indices, prompts, and other auxiliaries unobserved",
                    "rate": "strict integer denominator requirements only; actual generated denominators/rates absent",
                },
                "adapters": records,
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
