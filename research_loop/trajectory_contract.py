"""Contract for training a reusable dream/think LOOP adapter.

The v0.2 runners pre-date this contract and emit compact tuples such as
``("MEMORY", query, result)``.  Those artifacts remain useful curriculum, but
the long-sequence adapter dataset uses an append-only, causal JSON shape.  A
transition is always:

    PUBLIC_STATE -> ASSISTANT_OPERATION -> TOOL/ENV_RESULT -> NEXT_STATE

This module is intentionally dependency-free.  It validates data before a
tokenizer or trainer sees it; hidden world truth is never needed by the model
and therefore has no place in a model-visible field or target.
"""

from __future__ import annotations

from typing import Any, Iterable, Mapping, Sequence
import re


SCHEMA_VERSION = "loop-adapter-trajectory-v0.1"
PHASES = ("PUBLIC_STATE", "ASSISTANT_OPERATION", "TOOL/ENV_RESULT", "NEXT_STATE")
SPLITS = {"train", "dev", "test", "holdout"}
OPERATIONS = {
    "RETRIEVE", "QUERY", "NOTICE", "HYPOTHESIZE", "PREDICT", "REVISE",
    "COMPRESS", "REVISIT", "DEFER", "ACT", "RELEASE", "STOP",
}
COGNITIVE_OPERATIONS = OPERATIONS - {"ACT"}


class ContractError(ValueError):
    """Raised when a trajectory violates the data contract."""


# Keys and phrases that must never be in model-visible inputs or operation
# targets.  The scorer may retain these in a sidecar, but the learner cannot.
_FORBIDDEN_KEY = re.compile(
    r"(?:hidden|secret|truth|final[_ -]?answer|answer[_ -]?key|proof[_ -]?graph|"
    r"factor[_ -]?solver|evaluator|verdict|label|memory[_ -]?adapter|"
    r"loop[_ -]?adapter)", re.IGNORECASE,
)
_FORBIDDEN_TEXT = re.compile(
    r"(?:hidden[_ -]?(?:truth|answer|parent|role)|final[_ -]?answer\s*:|"
    r"answer[_ -]?key\s*:|proof[_ -]?graph|factor[_ -]?solver|"
    r"evaluator[_ -]?(?:label|verdict)|(?:ground|offline)[_ -]?truth\s*:)",
    re.IGNORECASE,
)


def _walk(value: Any, path: str = "") -> Iterable[tuple[str, Any]]:
    """Yield every nested key/path and scalar value for leakage checks."""
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


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _check_public(
    value: Any,
    path: str,
    errors: list[str],
    scope: tuple[str, str, str] | None = None,
) -> None:
    """Reject truth/checker leakage in model-visible input or target data."""
    for nested_path, item in _walk(value, path):
        if isinstance(item, str):
            if _FORBIDDEN_KEY.search(nested_path):
                errors.append(f"{nested_path}: forbidden hidden/checker field")
            if _FORBIDDEN_TEXT.search(item):
                errors.append(f"{nested_path}: forbidden hidden/checker text")
            if scope is not None:
                field = nested_path.rsplit(".", 1)[-1]
                expected = {"world_id": 0, "skin_id": 1, "life_id": 2}.get(field)
                # _walk yields mapping keys as well as scalar values.  Do not
                # compare the key token ``world_id`` to the scoped value.
                if expected is not None and item != field and item != scope[expected]:
                    errors.append(f"{nested_path}: cross-world/life state leakage")


def _check_provenance(
    provenance: Any,
    scope: tuple[str, str, str],
    path: str,
    errors: list[str],
) -> None:
    if not isinstance(provenance, Mapping):
        errors.append(f"{path}: provenance must be an object")
        return
    for key in ("source_ids", "parent_ids"):
        if key in provenance and not isinstance(provenance[key], list):
            errors.append(f"{path}.{key}: must be a list")
    # Provenance may point to public observations or earlier records, but an
    # id must be explicitly scoped so it cannot silently cross a life.
    for key in ("world_id", "skin_id", "life_id"):
        if key in provenance and provenance[key] != scope[{"world_id": 0, "skin_id": 1, "life_id": 2}[key]]:
            errors.append(f"{path}.{key}: crosses trajectory scope")


def _check_masks(record: Mapping[str, Any], phase: str, path: str, errors: list[str]) -> None:
    tokens = record.get("tokens")
    mask = record.get("loss_mask")
    if not isinstance(tokens, list) or not all(isinstance(token, str) for token in tokens):
        errors.append(f"{path}: tokens must be a list of strings")
    if not isinstance(mask, list) or not all(isinstance(bit, int) and bit in (0, 1) for bit in mask):
        errors.append(f"{path}: loss_mask must be a list of 0/1 integers")
    elif isinstance(tokens, list) and len(mask) != len(tokens):
        errors.append(f"{path}: loss_mask length must equal tokens length")
    if phase != "ASSISTANT_OPERATION" and isinstance(mask, list) and any(mask):
        errors.append(f"{path}: only assistant cognitive/action tokens may train")
    if phase == "ASSISTANT_OPERATION" and isinstance(mask, list) and not any(mask):
        errors.append(f"{path}: assistant operation must expose trainable tokens")


def _check_record(
    record: Any,
    expected_phase: str,
    index: int,
    previous_id: str | None,
    scope: tuple[str, str, str],
    errors: list[str],
) -> str | None:
    path = f"records[{index}]"
    if not isinstance(record, Mapping):
        errors.append(f"{path}: record must be an object")
        return previous_id
    if record.get("phase") != expected_phase:
        errors.append(f"{path}: expected phase {expected_phase}")
    record_id = record.get("record_id")
    if not _nonempty(record_id):
        errors.append(f"{path}: missing non-empty record_id")
    elif previous_id is not None and record.get("prev_record_id") != previous_id:
        errors.append(f"{path}: prev_record_id does not continue append-only chain")
    elif previous_id is None and record.get("prev_record_id") not in (None, ""):
        errors.append(f"{path}: first record cannot have a predecessor")
    if record.get("world_id") != scope[0] or record.get("skin_id") != scope[1] or record.get("life_id") != scope[2]:
        errors.append(f"{path}: record identity differs from trajectory scope")
    if not isinstance(record.get("model_visible"), bool):
        errors.append(f"{path}: model_visible must be boolean")
    _check_masks(record, expected_phase, path, errors)
    provenance = record.get("provenance")
    if provenance is None:
        errors.append(f"{path}: missing provenance")
    else:
        _check_provenance(provenance, scope, f"{path}.provenance", errors)
    if record.get("model_visible"):
        _check_public(record, path, errors, scope)

    if expected_phase == "ASSISTANT_OPERATION":
        operation = record.get("operation")
        if not isinstance(operation, str) or operation not in OPERATIONS:
            errors.append(f"{path}: operation must be one of {sorted(OPERATIONS)}")
        if isinstance(operation, str):
            if operation in {"QUERY", "RETRIEVE", "REVISIT"} and not isinstance(record.get("query"), Mapping):
                errors.append(f"{path}: {operation} requires a query object")
            if operation == "ACT" and not isinstance(record.get("action"), Mapping):
                errors.append(f"{path}: ACT requires an action object")
            if operation == "ACT" and isinstance(record.get("action"), Mapping):
                _check_public(record["action"], f"{path}.action", errors, scope)
        if record.get("model_visible") is not True:
            errors.append(f"{path}: assistant operation must be model-visible target")
    elif record.get("model_visible") is not True:
        errors.append(f"{path}: causal state/result records must be model-visible inputs")
    return record_id if _nonempty(record_id) else previous_id


def validate_trajectory(trajectory: Mapping[str, Any]) -> list[str]:
    """Return all violations in one trajectory; an empty list means valid."""
    errors: list[str] = []
    if not isinstance(trajectory, Mapping):
        return ["trajectory: must be an object"]
    if trajectory.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"trajectory: schema_version must be {SCHEMA_VERSION}")
    split = trajectory.get("split")
    if split not in SPLITS:
        errors.append("trajectory: split must be train, dev, test, or holdout")
    for key in ("split_id", "world_id", "skin_id", "life_id", "trace_id"):
        if not _nonempty(trajectory.get(key)):
            errors.append(f"trajectory: missing non-empty {key}")
    memory_id = trajectory.get("memory_adapter_id")
    memory_mode = trajectory.get("memory_mode", "mounted")
    if memory_mode not in {"mounted", "none"}:
        errors.append("trajectory: memory_mode must be mounted or none")
    if memory_mode == "mounted" and not _nonempty(memory_id):
        errors.append("trajectory: mounted memory adapter must have memory_adapter_id")
    if memory_mode == "none" and memory_id is not None:
        errors.append("trajectory: memory_mode=none requires null memory_adapter_id")
    if not _nonempty(trajectory.get("loop_adapter_id")):
        errors.append("trajectory: missing non-empty loop_adapter_id")
    outcome = trajectory.get("delayed_outcome")
    if not isinstance(outcome, Mapping):
        errors.append("trajectory: missing delayed_outcome object")
    else:
        for key in ("success", "efficiency"):
            if key not in outcome:
                errors.append(f"trajectory.delayed_outcome: missing {key}")
        if "success" in outcome and not isinstance(outcome["success"], bool):
            errors.append("trajectory.delayed_outcome.success must be boolean")
        if "efficiency" in outcome and not isinstance(outcome["efficiency"], (int, float)):
            errors.append("trajectory.delayed_outcome.efficiency must be numeric")
        # Outcome is scorer-side metadata.  It is intentionally not a record
        # and must never be copied into a model-visible target.
        # The outcome is scorer-side and can contain no model-visible state;
        # still run the denylist to prevent accidental target construction.
        _check_public(outcome, "trajectory.delayed_outcome", errors)
    records = trajectory.get("records")
    if not isinstance(records, list) or not records:
        errors.append("trajectory: records must be a non-empty list")
        return errors
    scope = (trajectory.get("world_id"), trajectory.get("skin_id"), trajectory.get("life_id"))
    seen_ids: set[str] = set()
    previous: str | None = None
    if len(records) % len(PHASES):
        errors.append("records: must contain complete four-phase transitions")
    transition_ids: dict[int, str] = {}
    for index, record in enumerate(records):
        phase = PHASES[index % len(PHASES)]
        previous = _check_record(record, phase, index, previous, scope, errors)
        if isinstance(record, Mapping) and _nonempty(record.get("record_id")):
            if record["record_id"] in seen_ids:
                errors.append(f"records[{index}]: duplicate record_id")
            seen_ids.add(record["record_id"])
        if isinstance(record, Mapping):
            transition = record.get("transition_id")
            if not _nonempty(transition):
                errors.append(f"records[{index}]: missing non-empty transition_id")
            else:
                transition_index = index // len(PHASES)
                old_transition = transition_ids.setdefault(transition_index, transition)
                if old_transition != transition:
                    errors.append(f"records[{index}]: transition_id changes within transition")
    # A trace cannot be a hidden answer shortcut.  Require at least one
    # operation and prevent direct final-answer targets by construction.
    if not any(isinstance(r, Mapping) and r.get("phase") == "ASSISTANT_OPERATION" for r in records):
        errors.append("records: no assistant operation")
    return errors


def assert_valid_trajectory(trajectory: Mapping[str, Any]) -> None:
    errors = validate_trajectory(trajectory)
    if errors:
        raise ContractError("invalid trajectory:\n- " + "\n- ".join(errors))


def validate_dataset(trajectories: Sequence[Mapping[str, Any]]) -> list[str]:
    """Validate traces plus whole-world splits and per-life adapter isolation."""
    errors: list[str] = []
    world_splits: dict[str, str] = {}
    life_scopes: dict[str, tuple[str, str, str]] = {}
    life_memory: dict[str, str | None] = {}
    record_scopes: dict[str, tuple[str, str, str]] = {}
    for index, trajectory in enumerate(trajectories):
        errors.extend(f"trajectory[{index}]: {error}" for error in validate_trajectory(trajectory))
        if not isinstance(trajectory, Mapping):
            continue
        world_id, skin_id, life_id = (trajectory.get(key) for key in ("world_id", "skin_id", "life_id"))
        split = trajectory.get("split")
        if _nonempty(world_id) and split in SPLITS:
            old_split = world_splits.setdefault(world_id, split)
            if old_split != split:
                errors.append(f"world {world_id}: appears in multiple splits ({old_split}, {split})")
        scope = (world_id, skin_id, life_id)
        if _nonempty(life_id):
            old_scope = life_scopes.setdefault(life_id, scope)
            if old_scope != scope:
                errors.append(f"life {life_id}: crosses world/skin scope")
            old_memory = life_memory.setdefault(life_id, trajectory.get("memory_adapter_id"))
            if old_memory != trajectory.get("memory_adapter_id"):
                errors.append(f"life {life_id}: memory adapter changes within a life")
        memory_id = trajectory.get("memory_adapter_id")
        if _nonempty(memory_id):
            for other_life, other_memory in life_memory.items():
                if other_life != life_id and other_memory == memory_id:
                    errors.append(f"memory adapter {memory_id}: reused across lives (not reset)")
        for record in trajectory.get("records", []) if isinstance(trajectory.get("records"), list) else []:
            if isinstance(record, Mapping) and _nonempty(record.get("record_id")):
                record_id = record["record_id"]
                old_scope = record_scopes.setdefault(record_id, scope)
                if old_scope != scope:
                    errors.append(f"record {record_id}: crosses world/life scope")
    return errors


def assert_valid_dataset(trajectories: Sequence[Mapping[str, Any]]) -> None:
    errors = validate_dataset(trajectories)
    if errors:
        raise ContractError("invalid trajectory dataset:\n- " + "\n- ".join(errors))


def training_tokens(trajectory: Mapping[str, Any]) -> list[str]:
    """Return only cognitive/action tokens after validation."""
    assert_valid_trajectory(trajectory)
    tokens: list[str] = []
    for record in trajectory["records"]:
        tokens.extend(token for token, bit in zip(record["tokens"], record["loss_mask"]) if bit)
    return tokens


__all__ = [
    "COGNITIVE_OPERATIONS", "ContractError", "OPERATIONS", "PHASES",
    "SCHEMA_VERSION", "assert_valid_dataset", "assert_valid_trajectory",
    "training_tokens", "validate_dataset", "validate_trajectory",
]
