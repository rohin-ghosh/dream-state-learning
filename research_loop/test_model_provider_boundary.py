"""CPU-only adversarial tests for the isolated model-provider boundary."""

from __future__ import annotations

from dataclasses import replace
import hashlib
import json
import time

from .model_provider_boundary import (
    ExactProviderCall,
    IsolatedModelProviderBoundary,
    ProviderBoundaryError,
    ProviderCallScope,
    ProviderExchange,
    ProviderExpectations,
    receipt_from_bytes,
    sha256_bytes,
)


def _hash(label: str) -> str:
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


def _scope(
    label: str, *, life: str = "life-a", arm: str = "no_feedback",
    round_index: int = 0,
) -> ProviderCallScope:
    return ProviderCallScope(
        call_id=_hash(f"call-{label}-{life}-{arm}-{round_index}"),
        run_id=_hash("run"), life_id=_hash(life), arm=arm,
        round_index=round_index, stage="DREAM", call_index=0,
    )


EXPECTATIONS = ProviderExpectations(
    provider="fake-provider", model="fake-model", model_revision="rev-1",
    tokenizer_id="fake-tokenizer", tokenizer_revision="tok-rev-1",
)


def _call(
    label: str, *, life: str = "life-a", arm: str = "no_feedback",
    round_index: int = 0, request: bytes | None = None,
) -> ExactProviderCall:
    return ExactProviderCall(
        scope=_scope(label, life=life, arm=arm, round_index=round_index),
        request_bytes=request if request is not None else f"request:{label}".encode(),
        config_bytes=b'{"temperature":0.0,"max_output_tokens":16}',
        expectations=EXPECTATIONS,
    )


def _receipt_bytes(
    *, session_id: str, request_id: str, request: bytes, config: bytes,
    response: bytes, override: dict | None = None,
) -> bytes:
    started = time.time_ns()
    value = {
        "schema_version": "provider-call-receipt-v1.0",
        "provider": EXPECTATIONS.provider,
        "model": EXPECTATIONS.model,
        "model_revision": EXPECTATIONS.model_revision,
        "provider_session_id": session_id,
        "provider_request_id": request_id,
        "fresh_session": True,
        "turn_index": 0,
        "request_sha256": sha256_bytes(request),
        "request_byte_count": len(request),
        "config_sha256": sha256_bytes(config),
        "config_byte_count": len(config),
        "raw_response_sha256": sha256_bytes(response),
        "raw_response_byte_count": len(response),
        "provider_started_at_unix_ns": started,
        "provider_ended_at_unix_ns": time.time_ns(),
        "token_evidence": {
            "mode": "EXACT_COUNTS", "source": "PROVIDER_RESPONSE",
            "tokenizer_id": EXPECTATIONS.tokenizer_id,
            "tokenizer_revision": EXPECTATIONS.tokenizer_revision,
            "supplied_token_count": 3, "generated_token_count": 1,
            "supplied_token_ids_sha256": None,
            "generated_token_ids_sha256": None,
        },
    }
    if override:
        value.update(override)
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


class StickySession:
    """Leaks its previous request if incorrectly reused."""

    def __init__(self, serial: int, calls: list[tuple[bytes, bytes]]) -> None:
        self.serial = serial
        self.calls = calls
        self.previous_request: bytes | None = None
        self.closed = False
        self.invoke_count = 0

    def invoke(self, request_bytes: bytes, config_bytes: bytes) -> ProviderExchange:
        assert not self.closed
        self.invoke_count += 1
        self.calls.append((request_bytes, config_bytes))
        response = self.previous_request or b"NO_PRIOR_SESSION_STATE"
        self.previous_request = request_bytes
        return ProviderExchange(
            raw_response_bytes=response,
            provider_receipt_bytes=_receipt_bytes(
                session_id=f"session-{self.serial}",
                request_id=f"request-{self.serial}", request=request_bytes,
                config=config_bytes, response=response,
            ),
        )

    def close(self) -> None:
        self.closed = True


class FreshStickyFactory:
    def __init__(self) -> None:
        self.sessions: list[StickySession] = []
        self.calls: list[tuple[bytes, bytes]] = []

    def open_fresh_session(self) -> StickySession:
        session = StickySession(len(self.sessions), self.calls)
        self.sessions.append(session)
        return session


def _assert_raises(expected: type[Exception], fragment: str, function) -> None:
    try:
        function()
    except expected as exc:
        assert fragment in str(exc), str(exc)
    else:
        raise AssertionError(f"expected {expected.__name__}: {fragment}")


def test_sticky_provider_state_cannot_cross_calls_lives_arms_or_rounds():
    factory = FreshStickyFactory()
    boundary = IsolatedModelProviderBoundary(factory)
    calls = (
        _call("life-a-arm-a-r0", request=b"SENTINEL_LIFE_A_ARM_A_R0"),
        _call(
            "life-a-arm-b-r0", arm="agenda_feedback",
            request=b"SENTINEL_LIFE_A_ARM_B_R0",
        ),
        _call(
            "life-a-arm-b-r1", arm="agenda_feedback", round_index=1,
            request=b"SENTINEL_LIFE_A_ARM_B_R1",
        ),
        _call(
            "life-b-arm-b-r1", life="life-b", arm="agenda_feedback",
            round_index=1, request=b"SENTINEL_LIFE_B_ARM_B_R1",
        ),
    )
    artifacts = tuple(boundary.invoke(call) for call in calls)
    assert all(
        artifact.raw_response_bytes == b"NO_PRIOR_SESSION_STATE"
        for artifact in artifacts
    )
    assert len(factory.sessions) == len(calls) == boundary.completed_session_count
    assert len({id(session) for session in factory.sessions}) == len(calls)
    assert all(session.closed and session.invoke_count == 1 for session in factory.sessions)
    # Scope metadata never crosses the provider seam: calls contain exactly the
    # two input byte strings and none of the opaque routing IDs.
    assert factory.calls == [
        (call.request_bytes, call.config_bytes) for call in calls
    ]
    for call, observed in zip(calls, factory.calls):
        combined = b"\n".join(observed)
        for private_scope_value in (
            call.scope.call_id, call.scope.run_id, call.scope.life_id,
            call.scope.arm, str(call.scope.round_index), call.scope.stage,
        ):
            if private_scope_value not in {"0", "1"}:
                assert private_scope_value.encode() not in combined


def test_reusing_same_local_session_object_fails_before_second_invoke():
    calls: list[tuple[bytes, bytes]] = []
    session = StickySession(0, calls)

    class ReusingFactory:
        def open_fresh_session(self):
            # Simulate an adapter that clears its local closed flag but retains
            # the same session object and its sticky conversation state.
            session.closed = False
            return session

    boundary = IsolatedModelProviderBoundary(ReusingFactory())
    boundary.invoke(_call("first"))
    _assert_raises(
        ProviderBoundaryError, "reused a consumed session object",
        lambda: boundary.invoke(_call("second")),
    )
    assert session.invoke_count == 1


def test_exact_bytes_and_real_boundary_timestamps_are_captured():
    factory = FreshStickyFactory()
    boundary = IsolatedModelProviderBoundary(factory)
    before = time.time_ns()
    artifact = boundary.invoke(_call("bytes", request=b"\x00exact\xffrequest"))
    after = time.time_ns()
    assert artifact.request_bytes == b"\x00exact\xffrequest"
    assert artifact.config_bytes == b'{"temperature":0.0,"max_output_tokens":16}'
    assert artifact.provider_receipt_bytes
    assert before <= artifact.boundary_started_at_unix_ns
    assert artifact.boundary_started_at_unix_ns <= artifact.boundary_ended_at_unix_ns
    assert artifact.boundary_ended_at_unix_ns <= after
    assert artifact.boundary_elapsed_monotonic_ns >= 0
    assert artifact.boundary_started_at.endswith("Z")
    assert artifact.boundary_ended_at.endswith("Z")
    artifact.validate()


def test_request_and_config_receipt_mismatches_fail_closed():
    class MismatchSession:
        def __init__(self, field: str) -> None:
            self.field = field

        def invoke(self, request_bytes: bytes, config_bytes: bytes) -> ProviderExchange:
            response = b"response"
            override = {
                self.field: (
                    "0" * 64 if self.field.endswith("sha256") else 999
                )
            }
            return ProviderExchange(
                response,
                _receipt_bytes(
                    session_id=f"session-{self.field}",
                    request_id=f"request-{self.field}", request=request_bytes,
                    config=config_bytes, response=response, override=override,
                ),
            )

        def close(self) -> None:
            pass

    class Factory:
        def __init__(self, field: str) -> None:
            self.field = field

        def open_fresh_session(self):
            return MismatchSession(self.field)

    for field, fragment in (
        ("request_sha256", "request hash mismatch"),
        ("request_byte_count", "request byte-count mismatch"),
        ("config_sha256", "config hash mismatch"),
        ("config_byte_count", "config byte-count mismatch"),
    ):
        _assert_raises(
            ProviderBoundaryError, fragment,
            lambda field=field: IsolatedModelProviderBoundary(Factory(field)).invoke(
                _call(field)
            ),
        )


def test_response_receipt_and_provider_metadata_mismatches_fail_closed():
    class DamagedSession:
        def __init__(self, override: dict) -> None:
            self.override = override

        def invoke(self, request_bytes: bytes, config_bytes: bytes) -> ProviderExchange:
            response = b"response"
            return ProviderExchange(
                response,
                _receipt_bytes(
                    session_id=f"session-{len(json.dumps(self.override))}",
                    request_id="request-damaged", request=request_bytes,
                    config=config_bytes, response=response, override=self.override,
                ),
            )

        def close(self) -> None:
            pass

    class Factory:
        def __init__(self, override: dict) -> None:
            self.override = override

        def open_fresh_session(self):
            return DamagedSession(self.override)

    for override, fragment in (
        ({"raw_response_sha256": "0" * 64}, "raw_response hash mismatch"),
        ({"raw_response_byte_count": 999}, "raw_response byte-count mismatch"),
        ({"model_revision": "wrong-revision"}, "model_revision metadata mismatch"),
        ({"provider": "wrong-provider"}, "provider metadata mismatch"),
        ({"fresh_session": False}, "does not certify a fresh session"),
        ({"turn_index": 1}, "turn_index 0"),
    ):
        _assert_raises(
            ProviderBoundaryError, fragment,
            lambda override=override: IsolatedModelProviderBoundary(
                Factory(override)
            ).invoke(_call("damaged")),
        )


def test_exact_receipt_bytes_and_parsed_receipt_cannot_diverge():
    artifact = IsolatedModelProviderBoundary(FreshStickyFactory()).invoke(
        _call("receipt")
    )
    damaged_bytes = artifact.provider_receipt_bytes.replace(
        b'"generated_token_count":1', b'"generated_token_count":2',
    )
    _assert_raises(
        ProviderBoundaryError, "provider_receipt_sha256 byte binding mismatch",
        lambda: replace(artifact, provider_receipt_bytes=damaged_bytes).validate(),
    )
    reparsed = receipt_from_bytes(damaged_bytes)
    _assert_raises(
        ProviderBoundaryError, "parsed receipt does not match receipt bytes",
        lambda: replace(
            artifact, provider_receipt_bytes=damaged_bytes,
            provider_receipt_sha256=sha256_bytes(damaged_bytes),
            receipt=artifact.receipt,
        ).validate(),
    )
    assert reparsed.token_evidence.generated_token_count == 2


def test_duplicate_receipt_keys_and_duplicate_provider_session_ids_fail_closed():
    receipt = _receipt_bytes(
        session_id="session-duplicate", request_id="request-duplicate",
        request=b"request", config=b"config", response=b"response",
    )
    duplicate = receipt[:-1] + b',"provider":"fake-provider"}'
    _assert_raises(
        ProviderBoundaryError, "duplicate key",
        lambda: receipt_from_bytes(duplicate),
    )

    class DuplicateIdFactory(FreshStickyFactory):
        def open_fresh_session(self):
            session = StickySession(7, self.calls)
            self.sessions.append(session)
            return session

    boundary = IsolatedModelProviderBoundary(DuplicateIdFactory())
    boundary.invoke(_call("one"))
    _assert_raises(
        ProviderBoundaryError, "reused a provider_session_id",
        lambda: boundary.invoke(_call("two")),
    )


def test_invalid_token_evidence_and_non_byte_inputs_fail_closed():
    invalid_call = replace(_call("bad-input"), request_bytes="not-bytes")
    _assert_raises(
        ProviderBoundaryError, "request_bytes must be exact bytes",
        lambda: IsolatedModelProviderBoundary(FreshStickyFactory()).invoke(invalid_call),
    )

    class BadTokenSession:
        def invoke(self, request_bytes: bytes, config_bytes: bytes) -> ProviderExchange:
            response = b"response"
            receipt = json.loads(_receipt_bytes(
                session_id="session-token", request_id="request-token",
                request=request_bytes, config=config_bytes, response=response,
            ))
            receipt["token_evidence"]["source"] = "ESTIMATED"
            return ProviderExchange(
                response,
                json.dumps(receipt, sort_keys=True, separators=(",", ":")).encode(),
            )

        def close(self) -> None:
            pass

    class BadTokenFactory:
        def open_fresh_session(self):
            return BadTokenSession()

    _assert_raises(
        ProviderBoundaryError, "must be PROVIDER_RESPONSE",
        lambda: IsolatedModelProviderBoundary(BadTokenFactory()).invoke(
            _call("bad-token")
        ),
    )
