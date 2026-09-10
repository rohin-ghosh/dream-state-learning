"""Closed four-READ/nine-ENV reducer and immutable opportunity ledger."""

from __future__ import annotations

from dataclasses import dataclass, replace
import json
from typing import Any, Callable, Mapping, Protocol

from rml_d0.canonical import coolant_object
from rml_d0.world import (
    ITEM_CONSUMED,
    ITEM_INVENTORY,
    ITEM_LOCKER,
    VALVE_NAMES,
    ActionDecodeError,
    GameState,
    initial_state,
    resolve_public_action,
    step,
)

from .contract import (
    ENV_SLOTS,
    OUTCOME_STATES,
    READ_SLOTS,
    RESOURCE_CEILINGS,
    OpportunityRegistration,
    build_roster,
    canonical_bytes,
)
from .fixtures import TargetCase, public_query_anchors
from .memory import ExactMemoryService, MemoryContractError, conservative_cpu_token_count


class MachineContractError(ValueError):
    pass


class Provider(Protocol):
    def __call__(self, model_input: bytes, *, opportunity_id: str) -> tuple[bytes, Mapping[str, int]]: ...


@dataclass(frozen=True)
class OpportunityEvent:
    opportunity_id: str
    trajectory_id: str
    slot_index: int
    phase: str
    attempted: bool
    disposition: str
    outcome_state: str | None
    input_tokens: int
    output_tokens: int
    input_bytes: int
    output_bytes: int
    wall_ms: int
    finish_reason: str | None = None


@dataclass(frozen=True)
class OpportunityLedger:
    registry: tuple[OpportunityRegistration, ...]
    events: tuple[OpportunityEvent, ...] = ()
    parent_artifact_seals: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        identities = {row.opportunity_id for row in self.registry}
        if len(identities) != len(self.registry):
            raise MachineContractError("duplicate opportunity identity")
        if len({row.opportunity_id for row in self.events}) != len(self.events):
            raise MachineContractError("opportunity recorded more than once")
        if any(row.opportunity_id not in identities for row in self.events):
            raise MachineContractError("event is outside the frozen registry")
        if len({parent for parent, _ in self.parent_artifact_seals}) != len(
            self.parent_artifact_seals
        ):
            raise MachineContractError("duplicate parent artifact seal")

    def bind_parent_artifact(
        self, parent_trajectory_id: str, artifact_sha256: str
    ) -> "OpportunityLedger":
        if self.events:
            raise MachineContractError("parent artifact seals must freeze before dispatch")
        if (
            len(artifact_sha256) != 64
            or any(character not in "0123456789abcdef" for character in artifact_sha256)
        ):
            raise MachineContractError("parent artifact seal is not SHA-256")
        if parent_trajectory_id not in {row.trajectory_id for row in build_roster()}:
            raise MachineContractError("parent artifact trajectory is unregistered")
        result = OpportunityLedger(
            self.registry,
            self.events,
            (*self.parent_artifact_seals, (parent_trajectory_id, artifact_sha256)),
        )
        return result

    def append(self, event: OpportunityEvent) -> "OpportunityLedger":
        if event.opportunity_id in {row.opportunity_id for row in self.events}:
            raise MachineContractError("opportunity cannot be retried or overwritten")
        registration = next(
            (row for row in self.registry if row.opportunity_id == event.opportunity_id), None
        )
        if registration is None:
            raise MachineContractError("unregistered opportunity")
        if (
            registration.trajectory_id != event.trajectory_id
            or registration.slot_index != event.slot_index
            or registration.phase != event.phase
        ):
            raise MachineContractError("opportunity identity fields changed")
        numeric = (
            event.input_tokens, event.output_tokens, event.input_bytes,
            event.output_bytes, event.wall_ms,
        )
        if any(isinstance(value, bool) or not isinstance(value, int) or value < 0 for value in numeric):
            raise MachineContractError("opportunity accounting must be non-negative integers")
        prior = sorted(
            (row for row in self.events if row.trajectory_id == event.trajectory_id),
            key=lambda row: row.slot_index,
        )
        if [row.slot_index for row in prior] != list(range(event.slot_index)):
            raise MachineContractError("opportunity events must be disposed in slot order")
        if any(
            row.outcome_state in {"INFRASTRUCTURE_FAILURE", "RESOURCE_CEILING_EXCEEDED"}
            for row in self.events
        ) and event.attempted:
            raise MachineContractError("dispatch after global infrastructure/resource failure")
        if prior and prior[-1].outcome_state is not None:
            if event.attempted or not event.disposition.startswith("CANCELLED_"):
                raise MachineContractError("only typed zero-attempt cancellation may follow terminal")
        result = OpportunityLedger(
            self.registry, (*self.events, event), self.parent_artifact_seals
        )
        result.assert_resource_ceiling()
        return result

    def assert_resource_ceiling(self) -> None:
        for event in self.events:
            if event.disposition == "COMPLETED_NONTERMINAL":
                if not event.attempted or event.outcome_state is not None:
                    raise MachineContractError("nonterminal opportunity disposition is inconsistent")
            elif event.outcome_state not in OUTCOME_STATES:
                raise MachineContractError("terminal/cancelled opportunity lacks an authorized outcome")
            per_call_overflow = (
                event.input_tokens > RESOURCE_CEILINGS["input_tokens_per_call"]
                or event.output_tokens > RESOURCE_CEILINGS["output_tokens_per_call"]
                or event.input_bytes > RESOURCE_CEILINGS["input_bytes_per_call"]
                or event.output_bytes > RESOURCE_CEILINGS["output_bytes_per_call"]
                or event.input_tokens + event.output_tokens
                > RESOURCE_CEILINGS["context_tokens_per_call"]
            )
            if per_call_overflow and event.outcome_state != "RESOURCE_CEILING_EXCEEDED":
                raise MachineContractError("untyped per-call resource ceiling overflow")
        totals = {
            "input_tokens": sum(row.input_tokens for row in self.events),
            "output_tokens": sum(row.output_tokens for row in self.events),
            "input_bytes": sum(row.input_bytes for row in self.events),
            "output_bytes": sum(row.output_bytes for row in self.events),
        }
        aggregate_overflow = False
        for name, value in totals.items():
            aggregate_overflow |= value > RESOURCE_CEILINGS[f"{name}_gate"]
        trajectory_ids = {row.trajectory_id for row in self.events}
        for trajectory_id in trajectory_ids:
            rows = [row for row in self.events if row.trajectory_id == trajectory_id]
            for name in totals:
                aggregate_overflow |= (
                    sum(getattr(row, name) for row in rows)
                    > RESOURCE_CEILINGS[f"{name}_per_trajectory"]
                )
        if aggregate_overflow and not any(
            row.outcome_state == "RESOURCE_CEILING_EXCEEDED" for row in self.events
        ):
            raise MachineContractError("aggregate resource overflow lacks a durable typed failure")

    def cancel_suffix(
        self,
        trajectory_id: str,
        after_slot: int,
        *,
        dependency_failed: bool = False,
    ) -> "OpportunityLedger":
        ledger = self
        existing = {row.opportunity_id for row in ledger.events}
        disposition = (
            "CANCELLED_DEPENDENCY_FAILED" if dependency_failed else "CANCELLED_AFTER_TERMINAL"
        )
        for row in self.registry:
            if (
                row.trajectory_id == trajectory_id
                and row.slot_index > after_slot
                and row.opportunity_id not in existing
            ):
                ledger = ledger.append(
                    OpportunityEvent(
                        row.opportunity_id,
                        row.trajectory_id,
                        row.slot_index,
                        row.phase,
                        False,
                        disposition,
                        "CANCELLED",
                        0,
                        0,
                        0,
                        0,
                        0,
                    )
                )
        return ledger

    def reconcile(self, *, require_complete: bool = False) -> dict[str, int]:
        attempted = sum(row.attempted for row in self.events)
        resource_failures = sum(
            not row.attempted and row.outcome_state == "RESOURCE_CEILING_EXCEEDED"
            for row in self.events
        )
        cancelled = sum(row.disposition.startswith("CANCELLED_") for row in self.events)
        if attempted + resource_failures + cancelled != len(self.events):
            raise AssertionError("ledger arithmetic failed")
        if require_complete and len(self.events) != len(self.registry):
            raise MachineContractError("ledger is not fully disposed")
        return {
            "registered": len(self.registry),
            "disposed": len(self.events),
            "dispatched": attempted,
            "zero_attempt_resource_failures": resource_failures,
            "cancelled": cancelled,
        }


@dataclass(frozen=True)
class StepRecord:
    slot_index: int
    phase: str
    raw_output: bytes
    operation: Mapping[str, Any] | None
    scratch: str
    citations: tuple[str, ...]
    returned_row: bytes | None
    returned_handle: str | None
    returned_status: str | None
    action_record: Mapping[str, Any] | None
    result_code: str | None
    result_text: str | None


@dataclass(frozen=True)
class RmlActionMachine:
    case: TargetCase
    state: GameState
    records: tuple[StepRecord, ...] = ()
    scratch: str = ""
    allowed_keys: frozenset[str] = frozenset()
    terminal: bool = False
    outcome_state: str | None = None
    terminal_reason: str | None = None

    @classmethod
    def start(cls, case: TargetCase) -> "RmlActionMachine":
        return cls(case=case, state=initial_state(case.spec), allowed_keys=public_query_anchors(case))

    @property
    def slot_index(self) -> int:
        return len(self.records)

    @property
    def phase(self) -> str:
        return "READ" if self.slot_index < READ_SLOTS else "ENV"

    @property
    def frozen(self) -> bool:
        return self.terminal

    def model_visible_value(self) -> dict[str, Any]:
        """Complete model-visible value; condition, target id, truth, and score absent."""

        history = []
        for record in self.records:
            history.append(
                {
                    "citations": list(record.citations),
                    # Preserve the complete emitted operation.  In particular,
                    # later calls must see the exact prior READ key; the action
                    # is already contained in an ENV operation and is not
                    # duplicated in a second history field.
                    "operation": record.operation,
                    "result_code": record.result_code,
                    "result_text": record.result_text,
                    "returned_row": None
                    if record.returned_row is None
                    else record.returned_row.decode("utf-8"),
                    "scratch": record.scratch,
                    "slot_index": record.slot_index,
                }
            )
        return {
            "allowed_operation": self.phase,
            "history": history,
            "public_target": json.loads(self.case.public_bytes),
            "public_state": render_public_state(self.case, self.state),
            "query_key_grammar": {
                "conditioner": "conditioner:{conditioner_family}",
                "exchanger": "exchanger:{exchanger_family}",
                "pair": "pair:{module_family}:{initial_coolant_bits}:{exchanger_family}",
                "schema": "schema:{module_family}",
                "valve": "valve:{valve_family}",
            },
            "public_derived_query_keys": sorted(public_query_anchors(self.case)),
            "scratch": self.scratch,
            "slot_index": self.slot_index,
        }

    def model_visible_bytes(self) -> bytes:
        return canonical_bytes(self.model_visible_value())

    def _terminal_invalid(self, raw: bytes, reason: str) -> "RmlActionMachine":
        record = StepRecord(
            self.slot_index,
            self.phase,
            raw,
            None,
            self.scratch,
            (),
            None,
            None,
            None,
            None,
            None,
            None,
        )
        return replace(
            self,
            records=(*self.records, record),
            terminal=True,
            outcome_state="MODEL_INVALID",
            terminal_reason=reason,
        )

    def provider_failure(self, reason: str) -> "RmlActionMachine":
        if self.terminal:
            raise MachineContractError("cannot fail a frozen trajectory")
        record = StepRecord(
            self.slot_index,
            self.phase,
            b"",
            None,
            self.scratch,
            (),
            None,
            None,
            None,
            None,
            None,
            None,
        )
        return replace(
            self,
            records=(*self.records, record),
            terminal=True,
            outcome_state="INFRASTRUCTURE_FAILURE",
            terminal_reason=reason,
        )

    def resource_failure(self, reason: str) -> "RmlActionMachine":
        failed = self.provider_failure(reason)
        return replace(failed, outcome_state="RESOURCE_CEILING_EXCEEDED")

    def advance(
        self,
        raw: bytes,
        service: ExactMemoryService,
        *,
        output_truncated: bool = False,
        token_counter: Callable[[bytes], int] = conservative_cpu_token_count,
    ) -> "RmlActionMachine":
        if self.terminal:
            raise MachineContractError("cannot advance a frozen trajectory")
        if output_truncated:
            return self._terminal_invalid(raw, "TRUNCATED_OUTPUT")
        try:
            value = _strict_json(raw)
            operation, scratch, citations = validate_operation(value, token_counter=token_counter)
        except (MachineContractError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            return self._terminal_invalid(raw, f"MALFORMED:{exc}")
        kind = operation["kind"]
        if kind != self.phase:
            return self._terminal_invalid(raw, "WRONG_PHASE")
        if self.phase == "READ":
            key = operation["key"]
            if key not in self.allowed_keys:
                return self._terminal_invalid(raw, "QUERY_KEY_ORIGIN")
            try:
                returned = service.read(key)
            except MemoryContractError as exc:
                return self._terminal_invalid(raw, f"READ_ERROR:{exc}")
            parsed_return = json.loads(returned)
            handle = parsed_return["handle"]
            allowed = set(self.allowed_keys)
            payload = parsed_return.get("payload", {})
            for field in ("next_key",):
                candidate = payload.get(field)
                if isinstance(candidate, str):
                    if candidate not in service.query_universe:
                        return self._terminal_invalid(raw, "QUERY_KEY_EXPANSION_OUTSIDE_SEAL")
                    allowed.add(candidate)
            record = StepRecord(
                self.slot_index,
                "READ",
                raw,
                operation,
                scratch,
                citations,
                returned,
                handle,
                str(parsed_return["status"]),
                None,
                None,
                None,
            )
            # A fourth return is appended and makes the *next* slot ENV.
            prior_rows = [item.returned_row for item in self.records if item.returned_row is not None]
            total_row_bytes = sum(len(item) for item in prior_rows) + len(returned)
            total_row_tokens = sum(token_counter(item) for item in prior_rows) + token_counter(returned)
            if total_row_bytes > RESOURCE_CEILINGS["row_bytes_per_trajectory"] or total_row_tokens > RESOURCE_CEILINGS["row_tokens_per_trajectory"]:
                return self.resource_failure("ROW_TRAJECTORY_CEILING")
            return replace(
                self,
                records=(*self.records, record),
                scratch=scratch,
                allowed_keys=frozenset(allowed),
            )

        action_record = operation["action"]
        try:
            action = resolve_public_action(self.case.spec, dict(action_record))
        except (ActionDecodeError, TypeError, ValueError) as exc:
            return self._terminal_invalid(raw, f"ILLEGAL_ACTION:{exc}")
        transition = step(self.case.spec, self.state, action)
        if transition.result_code == "ILLEGAL":
            return self._terminal_invalid(raw, "ILLEGAL_ACTION")
        record = StepRecord(
            self.slot_index,
            "ENV",
            raw,
            operation,
            scratch,
            citations,
            None,
            None,
            None,
            action_record,
            transition.result_code,
            transition.text,
        )
        records = (*self.records, record)
        terminal = transition.state.terminal or len(records) == READ_SLOTS + ENV_SLOTS
        outcome: str | None = None
        reason: str | None = None
        if terminal:
            success = (
                len(records) == READ_SLOTS + ENV_SLOTS
                and transition.result_code == "COMMITTED"
                and transition.state.success
            )
            outcome = "SCIENTIFIC_VALID_SUCCESS" if success else "SCIENTIFIC_VALID_NONSUCCESS"
            reason = transition.result_code if transition.state.terminal else "NINTH_ENV_WITHOUT_COMMIT"
        return replace(
            self,
            state=transition.state,
            records=records,
            scratch=scratch,
            terminal=terminal,
            outcome_state=outcome,
            terminal_reason=reason,
        )


def _strict_json(raw: bytes) -> Mapping[str, Any]:
    if not isinstance(raw, bytes) or len(raw) > RESOURCE_CEILINGS["output_bytes_per_call"]:
        raise MachineContractError("output bytes exceed ceiling")

    def pairs(values: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in values:
            if key in result:
                raise MachineContractError("duplicate JSON key")
            result[key] = value
        return result

    value = json.loads(raw.decode("utf-8"), object_pairs_hook=pairs)
    if not isinstance(value, Mapping):
        raise MachineContractError("operation output must be one JSON object")
    return value


def validate_operation(
    value: Mapping[str, Any], *, token_counter: Callable[[bytes], int]
) -> tuple[Mapping[str, Any], str, tuple[str, ...]]:
    if set(value) != {"operation", "scratch", "citations"}:
        raise MachineContractError("output must have exact operation/scratch/citations fields")
    operation = value["operation"]
    scratch = value["scratch"]
    citations = value["citations"]
    if not isinstance(operation, Mapping) or not isinstance(scratch, str) or not isinstance(citations, list):
        raise MachineContractError("operation, scratch, or citations has wrong type")
    scratch_bytes = scratch.encode("utf-8")
    if len(scratch_bytes) > RESOURCE_CEILINGS["scratch_bytes"] or token_counter(scratch_bytes) > RESOURCE_CEILINGS["scratch_tokens"]:
        raise MachineContractError("scratch exceeds ratified ceiling")
    if len(citations) > 16 or any(not isinstance(item, str) or len(item) > 64 for item in citations):
        raise MachineContractError("citations are malformed")
    if len(set(citations)) != len(citations):
        raise MachineContractError("duplicate citation handle")
    kind = operation.get("kind")
    if kind == "READ":
        if set(operation) != {"kind", "key"} or not isinstance(operation["key"], str):
            raise MachineContractError("READ must contain exactly kind/key")
    elif kind == "ENV":
        if set(operation) != {"kind", "action"} or not isinstance(operation["action"], Mapping):
            raise MachineContractError("ENV must contain exactly kind/action")
    else:
        raise MachineContractError("operation kind must be READ or ENV")
    return operation, scratch, tuple(citations)


def operation_bytes(
    operation: Mapping[str, Any], *, scratch: str = "", citations: tuple[str, ...] = ()
) -> bytes:
    return canonical_bytes(
        {"operation": dict(operation), "scratch": scratch, "citations": list(citations)}
    )


def _validate_service_binding(
    service: ExactMemoryService,
    trajectory_id: str,
    condition: str,
    case: TargetCase,
    expected_parent_artifact_sha256: str | None,
) -> None:
    if service.authorized_trajectory_id != trajectory_id:
        raise MachineContractError("memory service is not authorized for this trajectory")
    snapshot = service.snapshot
    parent_required = condition in {"AUTH_REPLAY", "SHAM_REC", "CUT_REC", "TWIN_REC"}
    parent_hash = service.parent_artifact_sha256
    if parent_required:
        if (
            not isinstance(parent_hash, str)
            or len(parent_hash) != 64
            or any(character not in "0123456789abcdef" for character in parent_hash)
        ):
            raise MachineContractError("intervention service lacks a parent-derived artifact seal")
        if parent_hash != expected_parent_artifact_sha256:
            raise MachineContractError("intervention service parent artifact seal mismatch")
    elif parent_hash is not None:
        raise MachineContractError("non-intervention service carries a parent artifact")

    base_gold = (
        snapshot.transform == "BASE"
        and snapshot.kind == "GOLD"
        and snapshot.projection == case.source_projection
    )
    pair_key = next(key for key in public_query_anchors(case) if key.startswith("pair:"))
    valve_key = next(key for key in public_query_anchors(case) if key.startswith("valve:"))
    keys = set(snapshot.query_universe)
    valid = False
    if condition == "GOLD_REC":
        valid = base_gold
    elif condition == "NONE_REC":
        valid = (
            snapshot.transform == "NONE"
            and snapshot.kind == "GOLD"
            and snapshot.projection == "H"
            and not snapshot.rows
        )
    elif condition == "ATOMS_REC":
        valid = (
            case.stratum == "P"
            and snapshot.transform == "BASE"
            and snapshot.kind == "ATOMS"
            and snapshot.projection == "H"
        )
    elif condition == "AUTH_REPLAY":
        valid = base_gold
    elif condition == "SHAM_REC":
        valid = (
            snapshot.transform == "SHAM"
            and snapshot.kind == "GOLD"
            and snapshot.projection == case.source_projection
            and snapshot.parent_sha256 is not None
            and {pair_key, valve_key} <= keys
        )
    elif condition == "CUT_REC":
        valid = (
            snapshot.transform == "CUT"
            and snapshot.kind == "GOLD"
            and snapshot.projection == case.source_projection
            and snapshot.parent_sha256 is not None
            and not ({pair_key, valve_key} & keys)
        )
    elif condition == "TWIN_REC":
        twin_projection = {"J_H": "FULL_TWIN", "P_H": "CONDITIONER_TWIN"}.get(
            case.target_id
        )
        valid = (
            twin_projection is not None
            and snapshot.transform == "BASE"
            and snapshot.kind == "GOLD"
            and snapshot.projection == twin_projection
        )
    if not valid:
        raise MachineContractError("memory service projection is unauthorized for condition")


def dispatch_one(
    machine: RmlActionMachine,
    service: ExactMemoryService,
    provider: Provider,
    registration: OpportunityRegistration,
    ledger: OpportunityLedger,
    *,
    token_counter: Callable[[bytes], int] = conservative_cpu_token_count,
) -> tuple[RmlActionMachine, OpportunityLedger]:
    """Dispatch once, enforce exact resources, and never retry."""

    if machine.terminal:
        raise MachineContractError("cannot dispatch an opportunity after terminal")
    if registration not in ledger.registry:
        raise MachineContractError("dispatch registration is outside the ledger")
    roster_row = next(
        (row for row in build_roster() if row.trajectory_id == registration.trajectory_id),
        None,
    )
    if roster_row is None or roster_row.target_id != machine.case.target_id:
        raise MachineContractError("dispatch trajectory is not bound to the active target")
    _validate_service_binding(
        service,
        registration.trajectory_id,
        roster_row.condition,
        machine.case,
        None
        if roster_row.parent_id is None
        else dict(ledger.parent_artifact_seals).get(roster_row.parent_id),
    )
    if registration.slot_index != machine.slot_index or registration.phase != machine.phase:
        raise MachineContractError("dispatch registration disagrees with machine slot/phase")
    prior_slots = sorted(
        row.slot_index
        for row in ledger.events
        if row.trajectory_id == registration.trajectory_id
    )
    if prior_slots != list(range(machine.slot_index)):
        raise MachineContractError("dispatch opportunity is out of trajectory order")
    if any(
        row.outcome_state in {"INFRASTRUCTURE_FAILURE", "RESOURCE_CEILING_EXCEEDED"}
        for row in ledger.events
    ):
        raise MachineContractError("gate is frozen after infrastructure/resource failure")

    model_input = machine.model_visible_bytes()
    history_payload = canonical_bytes(machine.model_visible_value()["history"])
    history_bytes = len(history_payload)
    history_tokens = token_counter(history_payload)
    input_tokens = token_counter(model_input)
    prior_trajectory = [
        row for row in ledger.events if row.trajectory_id == registration.trajectory_id
    ]
    predictable_overflow = (
        len(model_input) > RESOURCE_CEILINGS["input_bytes_per_call"]
        or input_tokens > RESOURCE_CEILINGS["input_tokens_per_call"]
        or history_bytes > RESOURCE_CEILINGS["history_bytes_per_call"]
        or history_tokens > RESOURCE_CEILINGS["history_tokens_per_call"]
        or sum(row.input_bytes for row in prior_trajectory) + len(model_input)
        > RESOURCE_CEILINGS["input_bytes_per_trajectory"]
        or sum(row.input_tokens for row in prior_trajectory) + input_tokens
        > RESOURCE_CEILINGS["input_tokens_per_trajectory"]
        or sum(row.input_bytes for row in ledger.events) + len(model_input)
        > RESOURCE_CEILINGS["input_bytes_gate"]
        or sum(row.input_tokens for row in ledger.events) + input_tokens
        > RESOURCE_CEILINGS["input_tokens_gate"]
    )
    finish_reason: str | None = None
    if predictable_overflow:
        next_machine = machine.resource_failure("INPUT_BYTES_PER_CALL")
        output_tokens = 0
        wall_ms = 0
        raw = b""
        attempted = False
    else:
        try:
            raw, accounting = provider(model_input, opportunity_id=registration.opportunity_id)
            attempted = True
        except BaseException as exc:
            attempted = True
            next_machine = machine.provider_failure(f"{type(exc).__name__}:{exc}")
            raw = b""
            output_tokens = 0
            wall_ms = 0
        else:
            if not isinstance(raw, bytes) or not isinstance(accounting, Mapping):
                raw = b"" if not isinstance(raw, bytes) else raw
                output_tokens = token_counter(raw)
                wall_ms = 0
                next_machine = machine.provider_failure("MALFORMED_PROVIDER_ACCOUNTING")
            else:
                required_accounting = {
                    "input_tokens", "output_tokens", "wall_ms", "finish_reason"
                }
                values_well_typed = (
                    set(accounting) == required_accounting
                    and all(
                        isinstance(accounting[name], int)
                        and not isinstance(accounting[name], bool)
                        and accounting[name] >= 0
                        for name in ("input_tokens", "output_tokens", "wall_ms")
                    )
                    and accounting["finish_reason"] in {"stop", "length"}
                )
                output_tokens = token_counter(raw)
                wall_ms = (
                    int(accounting["wall_ms"])
                    if values_well_typed
                    else 0
                )
                finish_reason = (
                    str(accounting["finish_reason"])
                    if values_well_typed
                    else None
                )
                trajectory_output_tokens = (
                    sum(row.output_tokens for row in prior_trajectory) + output_tokens
                )
                trajectory_output_bytes = (
                    sum(row.output_bytes for row in prior_trajectory) + len(raw)
                )
                limits_broken = (
                    output_tokens > RESOURCE_CEILINGS["output_tokens_per_call"]
                    or len(raw) > RESOURCE_CEILINGS["output_bytes_per_call"]
                    or input_tokens + output_tokens
                    > RESOURCE_CEILINGS["context_tokens_per_call"]
                    or trajectory_output_tokens
                    > RESOURCE_CEILINGS["output_tokens_per_trajectory"]
                    or trajectory_output_bytes
                    > RESOURCE_CEILINGS["output_bytes_per_trajectory"]
                    or sum(row.output_tokens for row in ledger.events) + output_tokens
                    > RESOURCE_CEILINGS["output_tokens_gate"]
                    or sum(row.output_bytes for row in ledger.events) + len(raw)
                    > RESOURCE_CEILINGS["output_bytes_gate"]
                )
                if limits_broken:
                    next_machine = machine.resource_failure("PER_CALL_OR_AGGREGATE_RESOURCE_CEILING")
                elif (
                    not values_well_typed
                    or accounting["input_tokens"] != input_tokens
                    or accounting["output_tokens"] != output_tokens
                ):
                    next_machine = machine.provider_failure("ACCOUNTING_MISMATCH")
                else:
                    next_machine = machine.advance(
                        raw,
                        service,
                        output_truncated=finish_reason == "length",
                        token_counter=token_counter,
                    )
    event = OpportunityEvent(
        registration.opportunity_id,
        registration.trajectory_id,
        registration.slot_index,
        registration.phase,
        attempted,
        (
            "RESOURCE_CEILING_EXCEEDED_BEFORE_DISPATCH"
            if not attempted
            else "TERMINAL"
            if next_machine.terminal
            else "COMPLETED_NONTERMINAL"
        ),
        next_machine.outcome_state if next_machine.terminal else None,
        input_tokens,
        output_tokens,
        len(model_input),
        len(raw),
        wall_ms,
        finish_reason,
    )
    return next_machine, ledger.append(event)


def render_public_state(case: TargetCase, state: GameState) -> dict[str, Any]:
    """Render ordinary state only; no transforms, truth, indices, or score."""
    handles = case.spec.handles
    if handles is None:
        raise MachineContractError("public state requires handles")
    inventory = [
        handles.cartridges[index]
        for index, status in enumerate(state.statuses)
        if status == ITEM_INVENTORY
    ]
    locker = [
        handles.cartridges[index]
        for index, status in enumerate(state.statuses)
        if status == ITEM_LOCKER
    ]
    consumed = [
        handles.cartridges[index]
        for index, status in enumerate(state.statuses)
        if status == ITEM_CONSUMED
    ]
    return {
        "commit_succeeded": state.success,
        "consumed_items": consumed,
        "coolant": {"handle": handles.coolant, **coolant_object(state.coolant)},
        "failure_kind": state.failure,
        "inventory": inventory,
        "locker_items": locker,
        "position": state.position,
        "remaining_actions": state.remaining,
        "run_stable": state.run_stable,
        "terminal": state.terminal,
        "valve": {
            "handle": handles.valve,
            "mode": "UNSET" if state.valve_mode < 0 else VALVE_NAMES[state.valve_mode],
        },
    }
