"""Immutable, CPU-only provenance ledger for model calls.

This module is deliberately independent of the recurrent scheduler.  It does
not call a provider, parse a model response, inspect scorer state, or decide a
task action.  A caller supplies the exact bytes used at the model boundary;
the ledger binds those bytes to a frozen record and returns a new append-only
ledger value.

The only model-visible scope field is ``model_visible_scope_id``.  It must be
an opaque digest, not a world seed, latent bit, answer label, or game role.
Internal run/life identifiers are opaque as well so that accidentally placing
one in a prompt does not reveal benchmark structure.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from datetime import datetime
import hashlib
import json
from pathlib import PurePosixPath
import re
from typing import Any, Literal, Mapping, Protocol, Sequence


SCHEMA_VERSION = "model-call-ledger-v1.0"
ABSENT_HASH = hashlib.sha256(b"ABSENT").hexdigest()

_HASH = re.compile(r"[0-9a-f]{64}")
_ARM = re.compile(r"[a-z][a-z0-9_]{0,63}")
_STAGE = re.compile(r"[A-Z][A-Z0-9_]{0,63}")
_COMPONENT = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:/@+\-]{0,255}")
_PARSER_OUTCOMES = frozenset({"PARSED", "REJECTED", "ERROR"})
_TOKEN_MODES = frozenset({"TOKEN_IDS", "EXACT_COUNTS"})
_TOKEN_PROVENANCE = frozenset({
    "PROVIDER_RESPONSE", "LOCAL_TOKENIZER", "MODEL_ADAPTER",
})
_FORBIDDEN_KEY_FRAGMENTS = (
    "latent", "answer", "scorer", "private", "oracle", "ground_truth",
)


class LedgerError(ValueError):
    """Raised when a call cannot be recorded without weakening provenance."""


def sha256_bytes(value: bytes) -> str:
    if not isinstance(value, bytes):
        raise LedgerError("hashed call material must be exact bytes")
    return hashlib.sha256(value).hexdigest()


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _require_hash(value: Any, path: str) -> None:
    if not isinstance(value, str) or _HASH.fullmatch(value) is None:
        raise LedgerError(f"{path} must be one lowercase SHA-256 digest")


def _require_component(value: Any, path: str) -> None:
    if not isinstance(value, str) or _COMPONENT.fullmatch(value) is None:
        raise LedgerError(f"{path} must be one bounded component identifier")


def _require_exact_keys(value: Mapping[str, Any], expected: set[str], path: str) -> None:
    actual = set(value)
    if actual != expected:
        raise LedgerError(
            f"{path} must have exact fields; missing={sorted(expected - actual)}, "
            f"extra={sorted(actual - expected)}"
        )


def _reject_forbidden_keys(value: Any, path: str = "record") -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            lowered = str(key).casefold()
            if any(fragment in lowered for fragment in _FORBIDDEN_KEY_FRAGMENTS):
                raise LedgerError(f"{path}.{key}: hidden/scorer/private fields are forbidden")
            _reject_forbidden_keys(nested, f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, nested in enumerate(value):
            _reject_forbidden_keys(nested, f"{path}[{index}]")


def _parse_timestamp(value: str, path: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise LedgerError(f"{path} must be an RFC3339 UTC timestamp ending in Z")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise LedgerError(f"{path} is not a valid RFC3339 timestamp") from exc
    if parsed.utcoffset() is None or parsed.utcoffset().total_seconds() != 0:
        raise LedgerError(f"{path} must be UTC")
    return parsed


@dataclass(frozen=True)
class CallMaterials:
    """Exact byte strings hashed into one ledger record."""

    prompt: bytes
    prompt_template: bytes
    input_payload: bytes
    raw_output: bytes

    def validate(self) -> None:
        for field in fields(self):
            if not isinstance(getattr(self, field.name), bytes):
                raise LedgerError(f"materials.{field.name} must be exact bytes")


@dataclass(frozen=True)
class TokenAccounting:
    """Either exact token IDs or provider/adapter-certified exact counts."""

    mode: Literal["TOKEN_IDS", "EXACT_COUNTS"]
    provenance: Literal["PROVIDER_RESPONSE", "LOCAL_TOKENIZER", "MODEL_ADAPTER"]
    tokenizer_id: str
    tokenizer_revision: str
    supplied_token_ids: tuple[int, ...] | None
    generated_token_ids: tuple[int, ...] | None
    supplied_token_count: int
    generated_token_count: int

    def validate(self) -> None:
        if self.mode not in _TOKEN_MODES:
            raise LedgerError("token_accounting.mode is invalid")
        if self.provenance not in _TOKEN_PROVENANCE:
            raise LedgerError("token_accounting.provenance is invalid")
        _require_component(self.tokenizer_id, "token_accounting.tokenizer_id")
        _require_component(self.tokenizer_revision, "token_accounting.tokenizer_revision")
        for name in ("supplied_token_count", "generated_token_count"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise LedgerError(f"token_accounting.{name} must be a non-negative integer")
        if self.mode == "TOKEN_IDS":
            if not isinstance(self.supplied_token_ids, tuple) or not isinstance(
                self.generated_token_ids, tuple
            ):
                raise LedgerError("TOKEN_IDS mode requires supplied and generated ID tuples")
            for name in ("supplied_token_ids", "generated_token_ids"):
                values = getattr(self, name)
                if any(
                    isinstance(item, bool) or not isinstance(item, int)
                    or item < 0 or item > 2**31 - 1
                    for item in values
                ):
                    raise LedgerError(f"token_accounting.{name} contains an invalid token ID")
            if self.supplied_token_count != len(self.supplied_token_ids) or \
                    self.generated_token_count != len(self.generated_token_ids):
                raise LedgerError("token ID lengths do not match the declared exact counts")
        elif self.supplied_token_ids is not None or self.generated_token_ids is not None:
            raise LedgerError("EXACT_COUNTS mode must not include token ID arrays")


@dataclass(frozen=True)
class DecodingConfig:
    """Small provider-neutral decoding surface used for matched controls."""

    temperature: float
    top_p: float
    max_output_tokens: int
    stop_sequences: tuple[str, ...]

    def validate(self) -> None:
        if isinstance(self.temperature, bool) or not isinstance(
            self.temperature, (int, float)
        ) or not 0 <= float(self.temperature) <= 100:
            raise LedgerError("decoding_config.temperature must be in [0,100]")
        if isinstance(self.top_p, bool) or not isinstance(self.top_p, (int, float)) \
                or not 0 < float(self.top_p) <= 1:
            raise LedgerError("decoding_config.top_p must be in (0,1]")
        if isinstance(self.max_output_tokens, bool) or not isinstance(
            self.max_output_tokens, int
        ) or not 1 <= self.max_output_tokens <= 1_000_000:
            raise LedgerError("decoding_config.max_output_tokens is invalid")
        if not isinstance(self.stop_sequences, tuple) or len(self.stop_sequences) > 32 \
                or any(not isinstance(item, str) or len(item) > 1024
                       for item in self.stop_sequences):
            raise LedgerError("decoding_config.stop_sequences is invalid")


@dataclass(frozen=True)
class ModelCallRecord:
    """One immutable and fully bound model call."""

    schema_version: str
    call_id: str
    run_id: str
    life_id: str
    arm: str
    round_index: int
    stage: str
    call_index: int
    model_visible_scope_id: str
    provider: str
    model: str
    model_revision: str
    prompt_hash: str
    prompt_template_hash: str
    input_hash: str
    raw_output_hash: str
    raw_output_artifact_path: str | None
    parser_id: str
    parser_version: str
    parser_outcome: Literal["PARSED", "REJECTED", "ERROR"]
    parser_error: str | None
    token_accounting: TokenAccounting
    decoding_seed: int
    decoding_config: DecodingConfig
    started_at: str
    ended_at: str
    reset_instance_id: str
    checkpoint_hash: str
    goal_hash: str
    vocabulary_hash: str

    def validate(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise LedgerError("record schema_version mismatch")
        for name in (
            "call_id", "run_id", "life_id", "model_visible_scope_id",
            "reset_instance_id", "checkpoint_hash", "goal_hash", "vocabulary_hash",
            "prompt_hash", "prompt_template_hash", "input_hash", "raw_output_hash",
        ):
            _require_hash(getattr(self, name), f"record.{name}")
        if len({
            self.call_id, self.run_id, self.life_id,
            self.model_visible_scope_id, self.reset_instance_id,
        }) != 5:
            raise LedgerError("call/run/life/visible/reset opaque IDs must be distinct")
        if not isinstance(self.arm, str) or _ARM.fullmatch(self.arm) is None:
            raise LedgerError("record.arm must be a bounded lowercase handle")
        if not isinstance(self.stage, str) or _STAGE.fullmatch(self.stage) is None:
            raise LedgerError("record.stage must be a bounded uppercase handle")
        for name in ("round_index", "call_index", "decoding_seed"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise LedgerError(f"record.{name} must be a non-negative integer")
        for name in ("provider", "model", "model_revision", "parser_id", "parser_version"):
            _require_component(getattr(self, name), f"record.{name}")
        if self.parser_outcome not in _PARSER_OUTCOMES:
            raise LedgerError("record.parser_outcome is invalid")
        if self.parser_outcome == "PARSED":
            if self.parser_error is not None:
                raise LedgerError("a parsed call cannot carry parser_error")
        elif not isinstance(self.parser_error, str) or not self.parser_error.strip() \
                or len(self.parser_error) > 4096:
            raise LedgerError("a rejected/error call requires a bounded parser_error")
        if self.raw_output_artifact_path is not None:
            if not isinstance(self.raw_output_artifact_path, str) \
                    or not self.raw_output_artifact_path.strip():
                raise LedgerError("raw output artifact path must be a non-empty relative path")
            path = PurePosixPath(self.raw_output_artifact_path)
            if path.is_absolute() or ".." in path.parts or "\x00" in self.raw_output_artifact_path:
                raise LedgerError("raw output artifact path must be relative and traversal-free")
        self.token_accounting.validate()
        self.decoding_config.validate()
        started = _parse_timestamp(self.started_at, "record.started_at")
        ended = _parse_timestamp(self.ended_at, "record.ended_at")
        if ended < started:
            raise LedgerError("record.ended_at precedes started_at")

    @property
    def position(self) -> tuple[str, str, str, int, str, int]:
        return (
            self.run_id, self.life_id, self.arm,
            self.round_index, self.stage, self.call_index,
        )


@dataclass(frozen=True)
class ArmLedgerSummary:
    run_id: str
    life_id: str
    arm: str
    call_count: int
    call_shape_hash: str
    template_sequence_hash: str
    model_sequence_hash: str
    decoding_sequence_hash: str
    supplied_token_counts: tuple[int, ...]
    generated_token_counts: tuple[int, ...]
    parsed_calls: int
    rejected_calls: int
    error_calls: int
    reset_instance_count: int


@dataclass(frozen=True)
class ImmutableModelCallLedger:
    """Persistent append-only ledger; failed appends cannot mutate prior state."""

    schema_version: str = SCHEMA_VERSION
    records: tuple[ModelCallRecord, ...] = ()

    def __post_init__(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise LedgerError("ledger schema_version mismatch")
        if not isinstance(self.records, tuple):
            raise LedgerError("ledger records must be an immutable tuple")
        call_ids: set[str] = set()
        positions: set[tuple[str, str, str, int, str, int]] = set()
        reset_scopes: dict[str, tuple[str, str, str, int]] = {}
        for record in self.records:
            if not isinstance(record, ModelCallRecord):
                raise LedgerError("ledger records must be ModelCallRecord values")
            record.validate()
            if record.call_id in call_ids:
                raise LedgerError("duplicate model call_id")
            if record.position in positions:
                raise LedgerError("duplicate model call position")
            call_ids.add(record.call_id)
            positions.add(record.position)
            scope = (record.run_id, record.life_id, record.arm, record.round_index)
            previous = reset_scopes.setdefault(record.reset_instance_id, scope)
            if previous != scope:
                raise LedgerError("reset_instance_id reused across life/arm/round scope")

    def append(
        self, record: ModelCallRecord, materials: CallMaterials,
        *, forbidden_input_markers: Sequence[bytes | str] = (),
    ) -> "ImmutableModelCallLedger":
        """Validate everything first, then return one new ledger atomically."""

        record.validate()
        materials.validate()
        validate_model_input_taint(materials, forbidden_input_markers)
        expected = {
            "prompt_hash": sha256_bytes(materials.prompt),
            "prompt_template_hash": sha256_bytes(materials.prompt_template),
            "input_hash": sha256_bytes(materials.input_payload),
            "raw_output_hash": sha256_bytes(materials.raw_output),
        }
        for name, value in expected.items():
            if getattr(record, name) != value:
                raise LedgerError(f"record.{name} does not match supplied exact bytes")
        return ImmutableModelCallLedger(self.schema_version, (*self.records, record))

    def assert_reset_isolation(self, *, require_per_call_reset: bool = False) -> None:
        """Assert reset IDs never cross life/arm/round; optionally one per call."""

        owners: dict[str, tuple[str, str, str, int]] = {}
        for record in self.records:
            owner = (record.run_id, record.life_id, record.arm, record.round_index)
            previous = owners.setdefault(record.reset_instance_id, owner)
            if previous != owner:
                raise LedgerError("reset_instance_id reused across life/arm/round scope")
        if require_per_call_reset and len(owners) != len(self.records):
            raise LedgerError("per-call reset assertion failed")

    def arm_summaries(self) -> tuple[ArmLedgerSummary, ...]:
        grouped: dict[tuple[str, str, str], list[ModelCallRecord]] = {}
        for record in self.records:
            grouped.setdefault((record.run_id, record.life_id, record.arm), []).append(record)
        summaries: list[ArmLedgerSummary] = []
        for (run_id, life_id, arm), rows in sorted(grouped.items()):
            rows.sort(key=lambda item: (item.round_index, item.stage, item.call_index))
            shape = [(item.round_index, item.stage, item.call_index) for item in rows]
            templates = [item.prompt_template_hash for item in rows]
            models = [
                (item.provider, item.model, item.model_revision) for item in rows
            ]
            decoding = [
                (
                    item.decoding_seed,
                    item.decoding_config.temperature,
                    item.decoding_config.top_p,
                    item.decoding_config.max_output_tokens,
                    item.decoding_config.stop_sequences,
                )
                for item in rows
            ]
            outcomes = [item.parser_outcome for item in rows]
            summaries.append(ArmLedgerSummary(
                run_id=run_id, life_id=life_id, arm=arm, call_count=len(rows),
                call_shape_hash=_sha256_json(shape),
                template_sequence_hash=_sha256_json(templates),
                model_sequence_hash=_sha256_json(models),
                decoding_sequence_hash=_sha256_json(decoding),
                supplied_token_counts=tuple(
                    item.token_accounting.supplied_token_count for item in rows
                ),
                generated_token_counts=tuple(
                    item.token_accounting.generated_token_count for item in rows
                ),
                parsed_calls=outcomes.count("PARSED"),
                rejected_calls=outcomes.count("REJECTED"),
                error_calls=outcomes.count("ERROR"),
                reset_instance_count=len({item.reset_instance_id for item in rows}),
            ))
        return tuple(summaries)

    def assert_matched_arms(
        self, required_arms: Sequence[str], *, require_supplied_token_match: bool = True,
    ) -> tuple[ArmLedgerSummary, ...]:
        """Fail unless every life has the same scheduled/model call envelope.

        Generated token counts and parser outcomes are reported but not forced
        equal: they are outcomes.  Call shape, template, model, decoding, and
        (by default) supplied-token counts are controlled exposures.
        """

        arms = tuple(required_arms)
        if not arms or len(set(arms)) != len(arms) or any(
            not isinstance(item, str) or _ARM.fullmatch(item) is None for item in arms
        ):
            raise LedgerError("required_arms must be unique bounded arm handles")
        summaries = self.arm_summaries()
        grouped: dict[tuple[str, str], dict[str, ArmLedgerSummary]] = {}
        for summary in summaries:
            grouped.setdefault((summary.run_id, summary.life_id), {})[summary.arm] = summary
        if not grouped:
            raise LedgerError("cannot match arms in an empty ledger")
        for scope, by_arm in grouped.items():
            if set(by_arm) != set(arms):
                raise LedgerError(f"life {scope} does not contain exactly the required arms")
            reference = by_arm[arms[0]]
            for arm in arms[1:]:
                candidate = by_arm[arm]
                for name in (
                    "call_count", "call_shape_hash", "template_sequence_hash",
                    "model_sequence_hash", "decoding_sequence_hash",
                ):
                    if getattr(candidate, name) != getattr(reference, name):
                        raise LedgerError(f"matched-arm {name} differs for life {scope}")
                if require_supplied_token_match and \
                        candidate.supplied_token_counts != reference.supplied_token_counts:
                    raise LedgerError(
                        f"matched-arm supplied token exposure differs for life {scope}"
                    )
        return summaries


class ModelCallLedgerProtocol(Protocol):
    """Narrow scheduler seam; implementations must preserve persistent append."""

    schema_version: str
    records: tuple[ModelCallRecord, ...]

    def append(
        self, record: ModelCallRecord, materials: CallMaterials,
        *, forbidden_input_markers: Sequence[bytes | str] = (),
    ) -> "ModelCallLedgerProtocol": ...

    def assert_reset_isolation(self, *, require_per_call_reset: bool = False) -> None: ...

    def arm_summaries(self) -> tuple[ArmLedgerSummary, ...]: ...


def validate_model_input_taint(
    materials: CallMaterials, forbidden_markers: Sequence[bytes | str],
) -> None:
    """Reject private/scorer sentinels from model inputs, never from outputs.

    A model may independently generate a held-out string, so ``raw_output`` is
    intentionally excluded.  Prompt, prompt template, and serialized input are
    the potential harness-to-model taint channels.
    """

    materials.validate()
    inputs = (materials.prompt, materials.prompt_template, materials.input_payload)
    for marker in forbidden_markers:
        if isinstance(marker, str):
            encoded = marker.encode("utf-8")
        elif isinstance(marker, bytes):
            encoded = marker
        else:
            raise LedgerError("forbidden input marker must be bytes or str")
        if not encoded:
            raise LedgerError("forbidden input marker cannot be empty")
        if any(encoded in value for value in inputs):
            raise LedgerError("private/scorer marker appears in model input material")


def record_from_mapping(value: Mapping[str, Any]) -> ModelCallRecord:
    """Strict JSON boundary: unknown, hidden, and missing fields fail closed."""

    if not isinstance(value, Mapping):
        raise LedgerError("record must be an object")
    _reject_forbidden_keys(value)
    record_fields = {field.name for field in fields(ModelCallRecord)}
    _require_exact_keys(value, record_fields, "record")
    token_value = value["token_accounting"]
    decoding_value = value["decoding_config"]
    if not isinstance(token_value, Mapping) or not isinstance(decoding_value, Mapping):
        raise LedgerError("nested token/decoding values must be objects")
    token_fields = {field.name for field in fields(TokenAccounting)}
    decoding_fields = {field.name for field in fields(DecodingConfig)}
    _require_exact_keys(token_value, token_fields, "record.token_accounting")
    _require_exact_keys(decoding_value, decoding_fields, "record.decoding_config")
    token = TokenAccounting(
        **{
            **dict(token_value),
            "supplied_token_ids": (
                tuple(token_value["supplied_token_ids"])
                if isinstance(token_value["supplied_token_ids"], list)
                else token_value["supplied_token_ids"]
            ),
            "generated_token_ids": (
                tuple(token_value["generated_token_ids"])
                if isinstance(token_value["generated_token_ids"], list)
                else token_value["generated_token_ids"]
            ),
        }
    )
    decoding = DecodingConfig(
        **{
            **dict(decoding_value),
            "stop_sequences": (
                tuple(decoding_value["stop_sequences"])
                if isinstance(decoding_value["stop_sequences"], list)
                else decoding_value["stop_sequences"]
            ),
        }
    )
    record = ModelCallRecord(
        **{
            **dict(value),
            "token_accounting": token,
            "decoding_config": decoding,
        }
    )
    record.validate()
    return record


def record_to_mapping(record: ModelCallRecord) -> dict[str, Any]:
    """Return the exact JSON-compatible record representation."""

    record.validate()
    return {
        **{
            field.name: getattr(record, field.name)
            for field in fields(ModelCallRecord)
            if field.name not in {"token_accounting", "decoding_config"}
        },
        "token_accounting": {
            field.name: getattr(record.token_accounting, field.name)
            for field in fields(TokenAccounting)
        },
        "decoding_config": {
            field.name: getattr(record.decoding_config, field.name)
            for field in fields(DecodingConfig)
        },
    }


def build_record(
    *, materials: CallMaterials, call_id: str, run_id: str, life_id: str, arm: str,
    round_index: int, stage: str, call_index: int, model_visible_scope_id: str,
    provider: str, model: str, model_revision: str,
    raw_output_artifact_path: str | None, parser_id: str, parser_version: str,
    parser_outcome: Literal["PARSED", "REJECTED", "ERROR"],
    parser_error: str | None, token_accounting: TokenAccounting,
    decoding_seed: int, decoding_config: DecodingConfig,
    started_at: str, ended_at: str, reset_instance_id: str,
    checkpoint_hash: str, goal_hash: str, vocabulary_hash: str,
) -> ModelCallRecord:
    """Construct a record while computing all byte-material hashes locally."""

    materials.validate()
    record = ModelCallRecord(
        schema_version=SCHEMA_VERSION, call_id=call_id, run_id=run_id,
        life_id=life_id, arm=arm, round_index=round_index, stage=stage,
        call_index=call_index, model_visible_scope_id=model_visible_scope_id,
        provider=provider, model=model, model_revision=model_revision,
        prompt_hash=sha256_bytes(materials.prompt),
        prompt_template_hash=sha256_bytes(materials.prompt_template),
        input_hash=sha256_bytes(materials.input_payload),
        raw_output_hash=sha256_bytes(materials.raw_output),
        raw_output_artifact_path=raw_output_artifact_path,
        parser_id=parser_id, parser_version=parser_version,
        parser_outcome=parser_outcome, parser_error=parser_error,
        token_accounting=token_accounting, decoding_seed=decoding_seed,
        decoding_config=decoding_config, started_at=started_at, ended_at=ended_at,
        reset_instance_id=reset_instance_id, checkpoint_hash=checkpoint_hash,
        goal_hash=goal_hash, vocabulary_hash=vocabulary_hash,
    )
    record.validate()
    return record

