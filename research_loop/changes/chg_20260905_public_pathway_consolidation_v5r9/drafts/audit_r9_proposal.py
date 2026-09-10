#!/usr/bin/env python3
"""Read-only structural audit for PPC5r9 proposal artifacts.

This is not a fixture executor and conveys no implementation, model, run, or
claim authority. It validates the closed JSON-Schema subset used by proposal
registries, self hashes, typed raw-manifest targets, and core fixed counts.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads((ROOT / "contracts.schema.json").read_text())


def canonical(value) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True,
                       separators=(",", ":")) + "\n").encode()


def self_hash(value: dict) -> str:
    body = copy.deepcopy(value)
    body.pop("self_hash", None)
    prefix = (value["contract"].encode() + b"\0"
              + str(value["schema_version"]).encode() + b"\0"
              + value["artifact_type"].encode() + b"\0")
    return hashlib.sha256(prefix + canonical(body)).hexdigest()


def resolve(node):
    while isinstance(node, dict) and "$ref" in node:
        ref = node["$ref"]
        if not ref.startswith("#/$defs/"):
            raise AssertionError(f"nonlocal ref {ref}")
        node = SCHEMA["$defs"][ref.rsplit("/", 1)[1]]
    return node


def validate(value, schema, path="$", stack=()):
    schema = resolve(schema)
    marker = (id(schema), id(value))
    if marker in stack:
        return
    stack = stack + (marker,)
    for clause in schema.get("allOf", []):
        validate(value, clause, path, stack)
    if "oneOf" in schema:
        successes = []
        errors = []
        for option in schema["oneOf"]:
            try:
                validate(value, option, path, stack)
                successes.append(option)
            except AssertionError as error:
                errors.append(str(error))
        assert len(successes) == 1, f"{path}: oneOf matches={len(successes)}; {errors[:2]}"
    if "const" in schema:
        assert value == schema["const"], f"{path}: const mismatch"
    if "enum" in schema:
        assert value in schema["enum"], f"{path}: not in enum"
    expected_type = schema.get("type")
    if expected_type == "object" or any(
        key in schema for key in ("properties", "required", "additionalProperties")
    ):
        assert isinstance(value, dict), f"{path}: not object"
        required = schema.get("required", [])
        assert not (set(required) - set(value)), f"{path}: missing {sorted(set(required)-set(value))}"
        props = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            assert not (set(value) - set(props)), f"{path}: extra {sorted(set(value)-set(props))}"
        for key, child in value.items():
            if key in props:
                validate(child, props[key], f"{path}.{key}", stack)
    elif expected_type == "array":
        assert isinstance(value, list), f"{path}: not array"
        assert len(value) >= schema.get("minItems", 0), f"{path}: too short"
        if "maxItems" in schema:
            assert len(value) <= schema["maxItems"], f"{path}: too long"
        if schema.get("uniqueItems"):
            enc = [canonical(item) for item in value]
            assert len(enc) == len(set(enc)), f"{path}: duplicate items"
        prefix = schema.get("prefixItems", [])
        for index, child_schema in enumerate(prefix):
            if index < len(value):
                validate(value[index], child_schema, f"{path}[{index}]", stack)
        items = schema.get("items")
        if isinstance(items, dict):
            for index, child in enumerate(value[len(prefix):], len(prefix)):
                validate(child, items, f"{path}[{index}]", stack)
        elif items is False:
            assert len(value) <= len(prefix), f"{path}: extra tuple items"
    elif expected_type == "string":
        assert isinstance(value, str), f"{path}: not string"
        if "minLength" in schema:
            assert len(value) >= schema["minLength"], f"{path}: too short"
        if "maxLength" in schema:
            assert len(value) <= schema["maxLength"], f"{path}: too long"
        if "pattern" in schema:
            assert re.search(schema["pattern"], value), f"{path}: pattern mismatch"
    elif expected_type == "integer":
        assert isinstance(value, int) and not isinstance(value, bool), f"{path}: not integer"
        if "minimum" in schema:
            assert value >= schema["minimum"], f"{path}: below minimum"
        if "maximum" in schema:
            assert value <= schema["maximum"], f"{path}: above maximum"
    elif expected_type == "boolean":
        assert isinstance(value, bool), f"{path}: not boolean"
    elif expected_type == "null":
        assert value is None, f"{path}: not null"


FILES = [
    "controller_registry.json", "transition_cause_registry.json",
    "status_registry.json", "visibility_registry.json", "gate_registry.json",
    "evidence_role_registry.json", "dependency_registry.json",
    "claim_registry.json", "resource_registry.json",
    "allowed_dispatch_registry.json", "authority_registry.json",
    "contract_schema_registry.json", "object_inventory.json",
    "raw_contract_schema_manifest.json", "raw_schema_edge_extractor_manifest.json",
    "raw_inventory_edge_extractor_manifest.json",
    "raw_visibility_edge_extractor_manifest.json",
]

objects = {}
for name in FILES:
    value = json.loads((ROOT / name).read_text())
    assert value["lifecycle_state"] == "PROPOSAL_ONLY", (
        f"{name}: authored registry must remain proposal-only"
    )
    validate(value, SCHEMA["$defs"][value["artifact_type"].lower()], name)
    assert value["self_hash"] == self_hash(value), f"{name}: self-hash mismatch"
    objects[value["self_hash"]] = value

for value in objects.values():
    if value["artifact_type"] == "RAW_BYTE_MANIFEST":
        raw = (ROOT.parents[2] / value["relative_path"]).read_bytes()
        assert len(raw) == value["byte_length"]
        assert hashlib.sha256(raw).hexdigest() == value["raw_sha256"]

visibility = objects[next(key for key, value in objects.items()
                          if value["artifact_type"] == "VISIBILITY_REGISTRY")]
assert len(visibility["cells"]) == 195
assert len(visibility["allowed_edges"]) == 84
assert sum(cell["visibility"] == "FORBIDDEN" for cell in visibility["cells"]) == 111
assert any(edge["concrete_role"] == "INTERVENTION_EMISSION_TO_PUBLIC_VIEW"
           for edge in visibility["allowed_edges"])
controller = objects[next(key for key, value in objects.items()
                          if value["artifact_type"] == "CONTROLLER_REGISTRY")]
assert controller["terminal_error_count"] == 3
assert all(transition["counter_input"] in (0, 1, 2)
           for row in controller["rows"] for transition in row["result_transitions"])
controller_keys = [
    (row["row_key"], transition["accepted_result"], transition["counter_input"],
     transition["queue_input_class"])
    for row in controller["rows"] for transition in row["result_transitions"]
]
assert len(controller_keys) == len(set(controller_keys)) == controller["reachable_state_count"]
assert all(transition["counter_output"] == 3 and transition["terminal_intent"]
           for row in controller["rows"] for transition in row["result_transitions"]
           if transition["accepted_result"] == "ERROR" and transition["counter_input"] == 2)
assert all(
    (transition["next_phase"], transition["result_specific_queue_effect"],
     transition["queue_output_rule"])
    == (("TERMINAL", "NONE", "PRESERVE") if transition["queue_input_class"] == "EMPTY"
        else ("FINALIZE_QUEUE", "FINALIZE_QUEUE", "FINALIZE_ALL_TO_EMPTY"))
    for row in controller["rows"] for transition in row["result_transitions"]
    if transition["terminal_intent"]
)
print(f"proposal audit passed: {len(FILES)} files, "
      f"{sum(bool(item.get('x-top-level-artifact')) for item in SCHEMA['$defs'].values())} "
      "types, 195 visibility cells")
