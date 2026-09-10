"""Fail-closed, CPU-only boundary for isolated model-provider calls.

The provider sees exactly two values: the exact request bytes and exact
configuration bytes.  Run, life, arm, round, and checkpoint bookkeeping stay
outside the provider call.  A new provider session is opened, used once, and
closed for every invocation.  The returned byte-for-byte response and receipt
are retained and bound to locally observed wall-clock and monotonic timing.

This file intentionally does not integrate with a runner, thinker, ledger, or
workflow.  Provider adapters remain responsible for making
``open_fresh_session`` a genuinely history-free remote session; this boundary
also rejects reuse of either a local session object or a provider session ID.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import re
import time
from typing import Any, Literal, Mapping, Protocol


SCHEMA_VERSION = "model-provider-boundary-v1.0"
RECEIPT_SCHEMA_VERSION = "provider-call-receipt-v1.0"

_HASH = re.compile(r"[0-9a-f]{64}")
_COMPONENT = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:/@+\-]{0,255}")
_ARM = re.compile(r"[a-z][a-z0-9_]{0,63}")
_STAGE = re.compile(r"[A-Z][A-Z0-9_]{0,63}")
_TOKEN_MODES = frozenset({"EXACT_COUNTS", "TOKEN_ID_HASHES"})


class ProviderBoundaryError(ValueError):
    """Raised when provider isolation or byte provenance cannot be proven."""


def sha256_bytes(value: bytes) -> str:
    if not isinstance(value, bytes):
        raise ProviderBoundaryError("provider material must be exact bytes")
    return hashlib.sha256(value).hexdigest()


def _require_hash(value: Any, path: str) -> None:
    if not isinstance(value, str) or _HASH.fullmatch(value) is None:
        raise ProviderBoundaryError(f"{path} must be one lowercase SHA-256 digest")


def _require_component(value: Any, path: str) -> None:
    if not isinstance(value, str) or _COMPONENT.fullmatch(value) is None:
        raise ProviderBoundaryError(f"{path} must be one bounded component identifier")


def _require_non_negative_integer(value: Any, path: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ProviderBoundaryError(f"{path} must be a non-negative integer")


def _require_exact_keys(value: Mapping[str, Any], expected: set[str], path: str) -> None:
    actual = set(value)
    if actual != expected:
        raise ProviderBoundaryError(
            f"{path} must have exact fields; missing={sorted(expected - actual)}, "
            f"extra={sorted(actual - expected)}"
        )


def _pairs_without_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ProviderBoundaryError(f"provider receipt contains duplicate key {key!r}")
        result[key] = value
    return result


def _reject_json_constant(value: str) -> None:
    raise ProviderBoundaryError(f"provider receipt contains invalid JSON constant {value}")


@dataclass(frozen=True)
class ProviderCallScope:
    """Boundary-only routing metadata that is never passed to the provider."""

    call_id: str
    run_id: str
    life_id: str
    arm: str
    round_index: int
    stage: str
    call_index: int

    def validate(self) -> None:
        for name in ("call_id", "run_id", "life_id"):
            _require_hash(getattr(self, name), f"scope.{name}")
        if not isinstance(self.arm, str) or _ARM.fullmatch(self.arm) is None:
            raise ProviderBoundaryError("scope.arm must be a bounded lowercase handle")
        if not isinstance(self.stage, str) or _STAGE.fullmatch(self.stage) is None:
            raise ProviderBoundaryError("scope.stage must be a bounded uppercase handle")
        _require_non_negative_integer(self.round_index, "scope.round_index")
        _require_non_negative_integer(self.call_index, "scope.call_index")


@dataclass(frozen=True)
class ProviderExpectations:
    """Metadata checked after the call, never supplied as a side channel."""

    provider: str
    model: str
    model_revision: str
    tokenizer_id: str
    tokenizer_revision: str

    def validate(self) -> None:
        for name in (
            "provider", "model", "model_revision", "tokenizer_id",
            "tokenizer_revision",
        ):
            _require_component(getattr(self, name), f"expectations.{name}")


@dataclass(frozen=True)
class ExactProviderCall:
    """Exact provider inputs plus boundary-only validation context."""

    scope: ProviderCallScope
    request_bytes: bytes
    config_bytes: bytes
    expectations: ProviderExpectations

    def validate(self) -> None:
        self.scope.validate()
        self.expectations.validate()
        for name in ("request_bytes", "config_bytes"):
            value = getattr(self, name)
            if not isinstance(value, bytes):
                raise ProviderBoundaryError(f"call.{name} must be exact bytes")
            if not value:
                raise ProviderBoundaryError(f"call.{name} cannot be empty")


@dataclass(frozen=True)
class ProviderExchange:
    """The two exact byte strings returned by a provider session."""

    raw_response_bytes: bytes
    provider_receipt_bytes: bytes

    def validate(self) -> None:
        if not isinstance(self.raw_response_bytes, bytes):
            raise ProviderBoundaryError("raw provider response must be exact bytes")
        if not isinstance(self.provider_receipt_bytes, bytes) \
                or not self.provider_receipt_bytes:
            raise ProviderBoundaryError("provider receipt must be non-empty exact bytes")


class FreshProviderSessionProtocol(Protocol):
    """One-shot session.  ``invoke`` has no metadata or history argument."""

    def invoke(self, request_bytes: bytes, config_bytes: bytes) -> ProviderExchange: ...

    def close(self) -> None: ...


class FreshProviderFactoryProtocol(Protocol):
    """Adapter seam that must create a genuinely history-free session."""

    def open_fresh_session(self) -> FreshProviderSessionProtocol: ...


@dataclass(frozen=True)
class ProviderTokenEvidence:
    """Provider-reported token evidence preserved in the exact receipt."""

    mode: Literal["EXACT_COUNTS", "TOKEN_ID_HASHES"]
    source: Literal["PROVIDER_RESPONSE"]
    tokenizer_id: str
    tokenizer_revision: str
    supplied_token_count: int
    generated_token_count: int
    supplied_token_ids_sha256: str | None
    generated_token_ids_sha256: str | None

    def validate(self) -> None:
        if self.mode not in _TOKEN_MODES:
            raise ProviderBoundaryError("receipt.token_evidence.mode is invalid")
        if self.source != "PROVIDER_RESPONSE":
            raise ProviderBoundaryError(
                "receipt.token_evidence.source must be PROVIDER_RESPONSE"
            )
        _require_component(self.tokenizer_id, "receipt.token_evidence.tokenizer_id")
        _require_component(
            self.tokenizer_revision, "receipt.token_evidence.tokenizer_revision"
        )
        _require_non_negative_integer(
            self.supplied_token_count, "receipt.token_evidence.supplied_token_count"
        )
        _require_non_negative_integer(
            self.generated_token_count, "receipt.token_evidence.generated_token_count"
        )
        hashes = (
            self.supplied_token_ids_sha256, self.generated_token_ids_sha256,
        )
        if self.mode == "TOKEN_ID_HASHES":
            for index, value in enumerate(hashes):
                _require_hash(value, f"receipt.token_evidence.token_id_hash[{index}]")
        elif any(value is not None for value in hashes):
            raise ProviderBoundaryError(
                "EXACT_COUNTS token evidence cannot carry token-ID hashes"
            )


@dataclass(frozen=True)
class ProviderReceipt:
    """Strict parsed view of the provider's exact receipt bytes."""

    schema_version: str
    provider: str
    model: str
    model_revision: str
    provider_session_id: str
    provider_request_id: str
    fresh_session: bool
    turn_index: int
    request_sha256: str
    request_byte_count: int
    config_sha256: str
    config_byte_count: int
    raw_response_sha256: str
    raw_response_byte_count: int
    provider_started_at_unix_ns: int
    provider_ended_at_unix_ns: int
    token_evidence: ProviderTokenEvidence

    def validate(self) -> None:
        if self.schema_version != RECEIPT_SCHEMA_VERSION:
            raise ProviderBoundaryError("provider receipt schema_version mismatch")
        for name in (
            "provider", "model", "model_revision", "provider_session_id",
            "provider_request_id",
        ):
            _require_component(getattr(self, name), f"receipt.{name}")
        if self.fresh_session is not True:
            raise ProviderBoundaryError("provider receipt does not certify a fresh session")
        if self.turn_index != 0 or isinstance(self.turn_index, bool):
            raise ProviderBoundaryError("fresh provider session must execute turn_index 0")
        for name in ("request_sha256", "config_sha256", "raw_response_sha256"):
            _require_hash(getattr(self, name), f"receipt.{name}")
        for name in (
            "request_byte_count", "config_byte_count", "raw_response_byte_count",
            "provider_started_at_unix_ns", "provider_ended_at_unix_ns",
        ):
            _require_non_negative_integer(getattr(self, name), f"receipt.{name}")
        if self.provider_started_at_unix_ns <= 0:
            raise ProviderBoundaryError("provider start timestamp must be a real Unix time")
        if self.provider_ended_at_unix_ns < self.provider_started_at_unix_ns:
            raise ProviderBoundaryError("provider end timestamp precedes provider start")
        self.token_evidence.validate()

    def validate_binding(
        self, call: ExactProviderCall, raw_response_bytes: bytes,
    ) -> None:
        self.validate()
        call.validate()
        expected_metadata = {
            "provider": call.expectations.provider,
            "model": call.expectations.model,
            "model_revision": call.expectations.model_revision,
        }
        for name, expected in expected_metadata.items():
            if getattr(self, name) != expected:
                raise ProviderBoundaryError(f"provider receipt {name} metadata mismatch")
        if self.token_evidence.tokenizer_id != call.expectations.tokenizer_id:
            raise ProviderBoundaryError("provider receipt tokenizer_id metadata mismatch")
        if self.token_evidence.tokenizer_revision != \
                call.expectations.tokenizer_revision:
            raise ProviderBoundaryError(
                "provider receipt tokenizer_revision metadata mismatch"
            )
        materials = (
            ("request", call.request_bytes, self.request_sha256,
             self.request_byte_count),
            ("config", call.config_bytes, self.config_sha256,
             self.config_byte_count),
            ("raw_response", raw_response_bytes, self.raw_response_sha256,
             self.raw_response_byte_count),
        )
        for name, value, expected_hash, expected_length in materials:
            if sha256_bytes(value) != expected_hash:
                raise ProviderBoundaryError(f"provider receipt {name} hash mismatch")
            if len(value) != expected_length:
                raise ProviderBoundaryError(f"provider receipt {name} byte-count mismatch")


def receipt_from_bytes(value: bytes) -> ProviderReceipt:
    """Parse a strict receipt while preserving ``value`` separately as evidence."""

    if not isinstance(value, bytes) or not value:
        raise ProviderBoundaryError("provider receipt must be non-empty exact bytes")
    try:
        decoded = value.decode("utf-8", errors="strict")
        mapping = json.loads(
            decoded,
            object_pairs_hook=_pairs_without_duplicates,
            parse_constant=_reject_json_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProviderBoundaryError("provider receipt must be strict UTF-8 JSON") from exc
    if not isinstance(mapping, Mapping):
        raise ProviderBoundaryError("provider receipt root must be an object")
    fields = {
        "schema_version", "provider", "model", "model_revision",
        "provider_session_id", "provider_request_id", "fresh_session",
        "turn_index", "request_sha256", "request_byte_count", "config_sha256",
        "config_byte_count", "raw_response_sha256", "raw_response_byte_count",
        "provider_started_at_unix_ns", "provider_ended_at_unix_ns",
        "token_evidence",
    }
    _require_exact_keys(mapping, fields, "provider receipt")
    token_mapping = mapping["token_evidence"]
    if not isinstance(token_mapping, Mapping):
        raise ProviderBoundaryError("provider receipt token_evidence must be an object")
    token_fields = {
        "mode", "source", "tokenizer_id", "tokenizer_revision",
        "supplied_token_count", "generated_token_count",
        "supplied_token_ids_sha256", "generated_token_ids_sha256",
    }
    _require_exact_keys(token_mapping, token_fields, "provider receipt token_evidence")
    token_evidence = ProviderTokenEvidence(**dict(token_mapping))
    receipt = ProviderReceipt(
        **{key: item for key, item in mapping.items() if key != "token_evidence"},
        token_evidence=token_evidence,
    )
    receipt.validate()
    return receipt


@dataclass(frozen=True)
class ProviderCallArtifact:
    """Complete immutable evidence for one isolated provider call."""

    schema_version: str
    scope: ProviderCallScope
    expectations: ProviderExpectations
    request_bytes: bytes
    config_bytes: bytes
    raw_response_bytes: bytes
    provider_receipt_bytes: bytes
    request_sha256: str
    config_sha256: str
    raw_response_sha256: str
    provider_receipt_sha256: str
    receipt: ProviderReceipt
    boundary_started_at_unix_ns: int
    boundary_ended_at_unix_ns: int
    boundary_elapsed_monotonic_ns: int

    def validate(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise ProviderBoundaryError("provider call artifact schema_version mismatch")
        call = ExactProviderCall(
            scope=self.scope, request_bytes=self.request_bytes,
            config_bytes=self.config_bytes, expectations=self.expectations,
        )
        call.validate()
        for name in (
            "raw_response_bytes", "provider_receipt_bytes",
        ):
            if not isinstance(getattr(self, name), bytes):
                raise ProviderBoundaryError(f"artifact.{name} must be exact bytes")
        expected_hashes = {
            "request_sha256": sha256_bytes(self.request_bytes),
            "config_sha256": sha256_bytes(self.config_bytes),
            "raw_response_sha256": sha256_bytes(self.raw_response_bytes),
            "provider_receipt_sha256": sha256_bytes(self.provider_receipt_bytes),
        }
        for name, expected in expected_hashes.items():
            if getattr(self, name) != expected:
                raise ProviderBoundaryError(f"artifact {name} byte binding mismatch")
        reparsed = receipt_from_bytes(self.provider_receipt_bytes)
        if reparsed != self.receipt:
            raise ProviderBoundaryError("artifact parsed receipt does not match receipt bytes")
        self.receipt.validate_binding(call, self.raw_response_bytes)
        for name in (
            "boundary_started_at_unix_ns", "boundary_ended_at_unix_ns",
            "boundary_elapsed_monotonic_ns",
        ):
            _require_non_negative_integer(getattr(self, name), f"artifact.{name}")
        if self.boundary_started_at_unix_ns <= 0:
            raise ProviderBoundaryError("boundary start timestamp must be a real Unix time")
        if self.boundary_ended_at_unix_ns < self.boundary_started_at_unix_ns:
            raise ProviderBoundaryError("boundary end timestamp precedes boundary start")

    @property
    def boundary_started_at(self) -> str:
        return _rfc3339_from_unix_ns(self.boundary_started_at_unix_ns)

    @property
    def boundary_ended_at(self) -> str:
        return _rfc3339_from_unix_ns(self.boundary_ended_at_unix_ns)


def _rfc3339_from_unix_ns(value: int) -> str:
    seconds, remainder = divmod(value, 1_000_000_000)
    rendered = datetime.fromtimestamp(seconds, timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    return f"{rendered}.{remainder:09d}Z"


class IsolatedModelProviderBoundary:
    """Open exactly one fresh provider session for every call."""

    def __init__(self, factory: FreshProviderFactoryProtocol) -> None:
        if factory is None or not callable(getattr(factory, "open_fresh_session", None)):
            raise ProviderBoundaryError("factory must implement open_fresh_session")
        self._factory = factory
        self._consumed_session_objects: list[FreshProviderSessionProtocol] = []
        self._provider_session_ids: set[str] = set()

    @property
    def completed_session_count(self) -> int:
        return len(self._provider_session_ids)

    def invoke(self, call: ExactProviderCall) -> ProviderCallArtifact:
        call.validate()
        boundary_started = time.time_ns()
        monotonic_started = time.monotonic_ns()
        try:
            session = self._factory.open_fresh_session()
        except Exception as exc:
            raise ProviderBoundaryError("provider failed to open a fresh session") from exc
        if session is None or not callable(getattr(session, "invoke", None)) \
                or not callable(getattr(session, "close", None)):
            raise ProviderBoundaryError("factory returned an invalid provider session")
        if any(session is previous for previous in self._consumed_session_objects):
            raise ProviderBoundaryError("provider factory reused a consumed session object")
        # Retain the object before invocation so even a failed call cannot reuse it.
        self._consumed_session_objects.append(session)
        try:
            try:
                exchange = session.invoke(call.request_bytes, call.config_bytes)
            except Exception as exc:
                raise ProviderBoundaryError("isolated provider invocation failed") from exc
        finally:
            try:
                session.close()
            except Exception as exc:
                raise ProviderBoundaryError("fresh provider session close failed") from exc
        monotonic_ended = time.monotonic_ns()
        boundary_ended = time.time_ns()
        if not isinstance(exchange, ProviderExchange):
            raise ProviderBoundaryError("provider session returned an invalid exchange")
        exchange.validate()
        receipt = receipt_from_bytes(exchange.provider_receipt_bytes)
        if receipt.provider_session_id in self._provider_session_ids:
            raise ProviderBoundaryError("provider reused a provider_session_id")
        # Consume the provider ID before binding checks; a failed/mismatched call
        # must never make that session eligible for reuse.
        self._provider_session_ids.add(receipt.provider_session_id)
        receipt.validate_binding(call, exchange.raw_response_bytes)
        artifact = ProviderCallArtifact(
            schema_version=SCHEMA_VERSION, scope=call.scope,
            expectations=call.expectations, request_bytes=call.request_bytes,
            config_bytes=call.config_bytes,
            raw_response_bytes=exchange.raw_response_bytes,
            provider_receipt_bytes=exchange.provider_receipt_bytes,
            request_sha256=sha256_bytes(call.request_bytes),
            config_sha256=sha256_bytes(call.config_bytes),
            raw_response_sha256=sha256_bytes(exchange.raw_response_bytes),
            provider_receipt_sha256=sha256_bytes(exchange.provider_receipt_bytes),
            receipt=receipt,
            boundary_started_at_unix_ns=boundary_started,
            boundary_ended_at_unix_ns=boundary_ended,
            boundary_elapsed_monotonic_ns=monotonic_ended - monotonic_started,
        )
        artifact.validate()
        return artifact
