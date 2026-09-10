"""Strict canonical JSON subset used by the Stage-A records.

The protocol records contain integers but no general JSON numbers, so this is
the RFC-8785/JCS representation for the closed subset actually used here:
objects, arrays, NFC strings, booleans, and signed integers.  Null and floats
fail closed.  Durable records add one LF; hashes cover bytes before that LF.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from collections.abc import Mapping, Sequence
from typing import Any

HANDLE_RE = re.compile(r"^(?:MF|CF|XF|VF|CI|LO|VA|CO|SI|GO|EP|EV)[0-9A-F]{12}$")

RECORD_KEYS = {
    "PublicAction": frozenset({"action_kind", "arguments"}),
    "PublicEvent": frozenset(
        {"action", "event_handle", "result_code", "state_delta", "text"}
    ),
    "RecallGoal": frozenset({"goal_handle", "goal_kind", "desired_coolant"}),
    "RecallFixture": frozenset({"goal", "initial_state", "action_budget"}),
    "ResourceRecord": frozenset(
        {
            "stage",
            "workers",
            "wall_ms",
            "peak_rss_bytes",
            "temp_bytes",
            "sealed_bytes",
            "states",
            "transitions",
            "pair_attempts",
            "target_attempts",
        }
    ),
    "GateReport": frozenset(
        {
            "protocol",
            "predecessor_hashes",
            "split_hashes",
            "gate_values",
            "failures",
            "resource_hash",
            "claim_firewall",
            "passed",
        }
    ),
}


class CanonicalError(ValueError):
    """A record is outside the protocol's closed canonical subset."""


def _validate(value: Any, path: str = "$") -> None:
    if value is None or isinstance(value, float):
        raise CanonicalError(f"{path}: null/floats are forbidden")
    if isinstance(value, bool):
        return
    if isinstance(value, int):
        return
    if isinstance(value, str):
        if unicodedata.normalize("NFC", value) != value:
            raise CanonicalError(f"{path}: string is not NFC")
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str):
                raise CanonicalError(f"{path}: object key is not a string")
            if unicodedata.normalize("NFC", key) != key:
                raise CanonicalError(f"{path}: object key is not NFC")
            _validate(item, f"{path}.{key}")
        return
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        for index, item in enumerate(value):
            _validate(item, f"{path}[{index}]")
        return
    raise CanonicalError(f"{path}: unsupported type {type(value).__name__}")


def canonical_bytes(value: Any) -> bytes:
    """Return JCS bytes without the durable-record LF."""

    _validate(value)
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def record_bytes(record_type: str, value: Mapping[str, Any]) -> bytes:
    expected = RECORD_KEYS.get(record_type)
    if expected is None:
        raise CanonicalError(f"unknown record type {record_type!r}")
    actual = frozenset(value)
    if actual != expected:
        missing = sorted(expected - actual)
        unknown = sorted(actual - expected)
        raise CanonicalError(f"{record_type}: missing={missing}, unknown={unknown}")
    _validate_record_fields(record_type, value)
    return canonical_bytes(value) + b"\n"


def record_hash(record_type: str, value: Mapping[str, Any]) -> str:
    payload = record_bytes(record_type, value)
    return hashlib.sha256(payload[:-1]).hexdigest()


def _validate_record_fields(record_type: str, value: Mapping[str, Any]) -> None:
    if record_type == "PublicAction":
        if not isinstance(value["arguments"], Mapping):
            raise CanonicalError("PublicAction.arguments must be an object")
    elif record_type == "PublicEvent":
        if not HANDLE_RE.fullmatch(str(value["event_handle"])):
            raise CanonicalError("invalid PublicEvent.event_handle")
    elif record_type == "RecallGoal":
        if value["goal_kind"] != "ONE_APPLY_COOLANT":
            raise CanonicalError("invalid RecallGoal.goal_kind")
        if not HANDLE_RE.fullmatch(str(value["goal_handle"])):
            raise CanonicalError("invalid RecallGoal.goal_handle")
        desired = value["desired_coolant"]
        if not isinstance(desired, Mapping) or frozenset(desired) != frozenset(
            {"viscosity", "inhibitor"}
        ):
            raise CanonicalError("invalid RecallGoal.desired_coolant")
        if desired["viscosity"] not in {"LOW", "HIGH"}:
            raise CanonicalError("invalid viscosity")
        if desired["inhibitor"] not in {"LEAN", "RICH"}:
            raise CanonicalError("invalid inhibitor")


def strict_loads(payload: bytes | str) -> Any:
    """Parse JSON while rejecting duplicate keys and the forbidden types."""

    if isinstance(payload, bytes):
        try:
            text = payload.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise CanonicalError("invalid UTF-8") from exc
    else:
        text = payload

    def pairs_hook(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, item in pairs:
            if key in result:
                raise CanonicalError(f"duplicate key {key!r}")
            result[key] = item
        return result

    try:
        value = json.loads(
            text,
            object_pairs_hook=pairs_hook,
            parse_float=lambda _: (_ for _ in ()).throw(
                CanonicalError("floats are forbidden")
            ),
            parse_constant=lambda _: (_ for _ in ()).throw(
                CanonicalError("non-finite numbers are forbidden")
            ),
        )
    except json.JSONDecodeError as exc:
        raise CanonicalError("invalid JSON") from exc
    _validate(value)
    return value


def parse_record_bytes(record_type: str, payload: bytes) -> dict[str, Any]:
    """Validate one durable record, including its one-and-only LF."""

    if not payload.endswith(b"\n") or payload.endswith(b"\n\n"):
        raise CanonicalError("durable record requires exactly one trailing LF")
    value = strict_loads(payload[:-1])
    if not isinstance(value, dict):
        raise CanonicalError("durable record must be an object")
    expected = record_bytes(record_type, value)
    if payload != expected:
        raise CanonicalError("record is not canonical JCS plus one LF")
    return value


def coolant_object(bits: int) -> dict[str, str]:
    if bits not in range(4):
        raise CanonicalError("coolant bits must be in 0..3")
    return {
        "viscosity": "HIGH" if bits & 2 else "LOW",
        "inhibitor": "RICH" if bits & 1 else "LEAN",
    }


def canonical_goldens() -> list[dict[str, Any]]:
    records: list[tuple[str, dict[str, Any]]] = [
        (
            "PublicAction",
            {"action_kind": "MOVE", "arguments": {"site": "LOCKER"}},
        ),
        (
            "RecallGoal",
            {
                "goal_handle": "GO000000000000",
                "goal_kind": "ONE_APPLY_COOLANT",
                "desired_coolant": {"viscosity": "HIGH", "inhibitor": "LEAN"},
            },
        ),
        (
            "RecallGoal",
            {
                "goal_handle": "GO000000000001",
                "goal_kind": "ONE_APPLY_COOLANT",
                "desired_coolant": {"viscosity": "LOW", "inhibitor": "RICH"},
            },
        ),
        (
            "PublicEvent",
            {
                "action": {"action_kind": "STOP", "arguments": {}},
                "event_handle": "EV000000000001",
                "result_code": "STOPPED",
                "state_delta": {"terminal": True},
                "text": "The maintenance attempt stops.",
            },
        ),
    ]
    return [
        {
            "record_type": record_type,
            "bytes_hex": record_bytes(record_type, record).hex(),
            "sha256": record_hash(record_type, record),
        }
        for record_type, record in records
    ]
