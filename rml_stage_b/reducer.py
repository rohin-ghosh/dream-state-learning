"""Post-freeze trace/intervention reducer, separate from D0 authorities."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from typing import Any, Mapping

from rml_d0.world import VALVE_NAMES, execute, initial_state, resolve_public_action, step

from .contract import READ_SLOTS, SLOTS_PER_TRAJECTORY, canonical_bytes, digest
from .fixtures import TargetCase, public_query_anchors
from .machine import RmlActionMachine, _strict_json, validate_operation
from .memory import ExactMemoryService, MemorySnapshot, conservative_cpu_token_count


class ReducerError(ValueError):
    pass


def _strict_artifact_json(raw: bytes) -> Mapping[str, Any]:
    def pairs(values: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in values:
            if key in result:
                raise ReducerError("duplicate frozen-artifact JSON key")
            result[key] = value
        return result

    value = json.loads(raw.decode("utf-8"), object_pairs_hook=pairs)
    if not isinstance(value, Mapping):
        raise ReducerError("frozen trace artifact must be an object")
    return value


@dataclass(frozen=True)
class TraceScore:
    trajectory_id: str
    condition: str
    outcome_state: str
    d0_terminal_success: bool
    action_signature: str
    action_records: tuple[Mapping[str, Any], ...]
    operation_signature: str
    returned_handles: tuple[str, ...]
    cited_handles: tuple[str, ...]
    citations_returned_before_use: bool
    citation_semantic_entailment: bool
    decisive_citations_minimal: bool
    legal_commit_success: bool
    frozen_artifact_sha256: str

    @property
    def scientific_valid(self) -> bool:
        return self.outcome_state in {
            "SCIENTIFIC_VALID_SUCCESS",
            "SCIENTIFIC_VALID_NONSUCCESS",
        }


def decisive_keys(case: TargetCase) -> tuple[str, str]:
    anchors = public_query_anchors(case)
    pair = next(key for key in anchors if key.startswith("pair:"))
    valve = next(key for key in anchors if key.startswith("valve:"))
    return pair, valve


def decisive_handles(case: TargetCase, snapshot: MemorySnapshot) -> tuple[str, str]:
    rows = snapshot.row_map()
    try:
        return tuple(rows[key].handle for key in decisive_keys(case))  # type: ignore[return-value]
    except KeyError as exc:
        raise ReducerError("decisive source relation absent") from exc


def freeze_trace_artifact(machine: RmlActionMachine) -> bytes:
    """Serialize the complete reducer input before any scientific scoring."""
    if not machine.frozen or machine.outcome_state is None:
        raise ReducerError("only a frozen trajectory can be serialized")
    return canonical_bytes(
        {
            "case_public_sha256": machine.case.public_sha256,
            "outcome_state": machine.outcome_state,
            "records": [
                {
                    "action_record": record.action_record,
                    "citations": list(record.citations),
                    "operation": record.operation,
                    "phase": record.phase,
                    "raw_output_hex": record.raw_output.hex(),
                    "result_code": record.result_code,
                    "result_text": record.result_text,
                    "returned_handle": record.returned_handle,
                    "returned_row_hex": None
                    if record.returned_row is None
                    else record.returned_row.hex(),
                    "returned_status": record.returned_status,
                    "scratch": record.scratch,
                    "slot_index": record.slot_index,
                }
                for record in machine.records
            ],
            "scratch": machine.scratch,
            "state": asdict(machine.state),
            "terminal": machine.terminal,
            "terminal_reason": machine.terminal_reason,
        }
    )


def _state_value(state: Any) -> dict[str, Any]:
    value = asdict(state)
    value["statuses"] = list(value["statuses"])
    return value


def _validate_and_replay_artifact(
    artifact_bytes: bytes, case: TargetCase, snapshot: MemorySnapshot
) -> tuple[Mapping[str, Any], list[Mapping[str, Any]], Any, str]:
    """Reject any artifact that disagrees with exact parsing or D0 replay."""
    try:
        artifact = _strict_artifact_json(artifact_bytes)
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ReducerError(f"malformed frozen trace artifact: {exc}") from exc
    if set(artifact) != {
        "case_public_sha256", "outcome_state", "records", "scratch", "state",
        "terminal", "terminal_reason",
    }:
        raise ReducerError("frozen trace artifact has wrong fields")
    if artifact["case_public_sha256"] != case.public_sha256 or artifact["terminal"] is not True:
        raise ReducerError("frozen trace artifact is not bound to the case/terminal state")
    records = artifact["records"]
    if not isinstance(records, list) or not records or len(records) > SLOTS_PER_TRAJECTORY:
        raise ReducerError("frozen trace record count is invalid")
    state = initial_state(case.spec)
    allowed_keys = set(public_query_anchors(case))
    service = ExactMemoryService(snapshot)
    actions: list[Mapping[str, Any]] = []
    exceptional_terminal = False
    for expected_slot, record in enumerate(records):
        if not isinstance(record, Mapping):
            raise ReducerError("frozen trace record is not an object")
        if set(record) != {
            "action_record", "citations", "operation", "phase", "raw_output_hex",
            "result_code", "result_text", "returned_handle", "returned_row_hex",
            "returned_status", "scratch", "slot_index",
        }:
            raise ReducerError("frozen trace record fields changed")
        expected_phase = "READ" if expected_slot < READ_SLOTS else "ENV"
        if record["slot_index"] != expected_slot or record["phase"] != expected_phase:
            raise ReducerError("frozen trace slot/phase order changed")
        if state.terminal:
            raise ReducerError("frozen trace contains an event after D0 terminal")
        try:
            raw = bytes.fromhex(record["raw_output_hex"])
        except (TypeError, ValueError) as exc:
            raise ReducerError("frozen trace raw output is not exact bytes") from exc
        operation = record["operation"]
        if operation is None:
            if expected_slot != len(records) - 1 or artifact["outcome_state"] not in {
                "MODEL_INVALID", "INFRASTRUCTURE_FAILURE", "RESOURCE_CEILING_EXCEEDED",
            }:
                raise ReducerError("non-scientific terminal record is inconsistent")
            if any(
                record[name] is not None
                for name in (
                    "action_record", "result_code", "result_text", "returned_handle",
                    "returned_row_hex", "returned_status",
                )
            ):
                raise ReducerError("non-scientific terminal record carries forged evidence")
            exceptional_terminal = True
            continue
        try:
            parsed = _strict_json(raw)
            parsed_operation, parsed_scratch, parsed_citations = validate_operation(
                parsed, token_counter=conservative_cpu_token_count
            )
        except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ReducerError(f"record raw output does not parse: {exc}") from exc
        if (
            dict(parsed_operation) != dict(operation)
            or parsed_scratch != record["scratch"]
            or list(parsed_citations) != record["citations"]
            or parsed_operation.get("kind") != expected_phase
        ):
            raise ReducerError("record raw operation fields disagree")
        if expected_phase == "READ":
            key = parsed_operation["key"]
            if key not in allowed_keys:
                raise ReducerError("replayed query key has no authorized origin")
            returned = service.read(key)
            try:
                returned_value = json.loads(returned)
                recorded_return = bytes.fromhex(record["returned_row_hex"])
            except (TypeError, ValueError, json.JSONDecodeError) as exc:
                raise ReducerError("recorded memory return is malformed") from exc
            if (
                recorded_return != returned
                or record["returned_handle"] != returned_value["handle"]
                or record["returned_status"] != returned_value["status"]
                or any(record[name] is not None for name in ("action_record", "result_code", "result_text"))
            ):
                raise ReducerError("recorded memory return disagrees with sealed service")
            next_key = returned_value.get("payload", {}).get("next_key")
            if next_key is not None:
                if next_key not in snapshot.query_universe:
                    raise ReducerError("returned next_key is outside the sealed query universe")
                allowed_keys.add(next_key)
        else:
            if any(
                record[name] is not None
                for name in ("returned_handle", "returned_row_hex", "returned_status")
            ) or record["action_record"] != parsed_operation["action"]:
                raise ReducerError("recorded ENV operation fields disagree")
            try:
                action = resolve_public_action(case.spec, dict(record["action_record"]))
            except (TypeError, ValueError) as exc:
                raise ReducerError("recorded public action is invalid") from exc
            transition = step(case.spec, state, action)
            if transition.result_code == "ILLEGAL":
                raise ReducerError("recorded scientific trace contains an illegal action")
            if record["result_code"] != transition.result_code or record["result_text"] != transition.text:
                raise ReducerError("recorded result disagrees with independent D0 replay")
            state = transition.state
            actions.append(record["action_record"])
    if artifact["scratch"] != records[-1]["scratch"] or artifact["state"] != _state_value(state):
        raise ReducerError("terminal scratch/state disagrees with replay")
    if exceptional_terminal:
        replay_outcome = str(artifact["outcome_state"])
        if state.success:
            raise ReducerError("non-scientific artifact cannot carry successful D0 state")
        if not isinstance(artifact["terminal_reason"], str) or not artifact["terminal_reason"]:
            raise ReducerError("non-scientific artifact lacks a terminal reason")
    else:
        terminal = state.terminal or len(records) == SLOTS_PER_TRAJECTORY
        if not terminal:
            raise ReducerError("scientific artifact froze before a terminal condition")
        replay_outcome = (
            "SCIENTIFIC_VALID_SUCCESS"
            if len(records) == SLOTS_PER_TRAJECTORY
            and records[-1]["result_code"] == "COMMITTED"
            and state.success
            else "SCIENTIFIC_VALID_NONSUCCESS"
        )
        if artifact["outcome_state"] != replay_outcome:
            raise ReducerError("terminal outcome label disagrees with independent D0 replay")
        expected_reason = (
            records[-1]["result_code"] if state.terminal else "NINTH_ENV_WITHOUT_COMMIT"
        )
        if artifact["terminal_reason"] != expected_reason:
            raise ReducerError("terminal reason disagrees with independent D0 replay")
    return artifact, actions, state, replay_outcome


def score_frozen_trace(
    trajectory_id: str,
    condition: str,
    case: TargetCase,
    machine: RmlActionMachine,
    snapshot: MemorySnapshot,
) -> TraceScore:
    """Freeze first, then score only an independently replayed artifact."""
    artifact_bytes = freeze_trace_artifact(machine)
    artifact, actions, replay_state, replay_outcome = _validate_and_replay_artifact(
        artifact_bytes, case, snapshot
    )
    records = artifact["records"]
    returned_at: dict[str, int] = {}
    returned_exact: dict[str, bytes] = {}
    for record in records:
        if (
            record["returned_handle"] is not None
            and record["returned_row_hex"] is not None
            and record["returned_status"] == "ROW"
        ):
            returned_at.setdefault(record["returned_handle"], record["slot_index"])
            returned_exact.setdefault(
                record["returned_handle"], bytes.fromhex(record["returned_row_hex"])
            )
    cited_at: dict[str, int] = {}
    for record in records:
        if record["phase"] == "ENV":
            for handle in record["citations"]:
                cited_at.setdefault(handle, record["slot_index"])
    cited = tuple(sorted(cited_at))
    try:
        pair_handle, valve_handle = decisive_handles(case, snapshot)
        expected = frozenset((pair_handle, valve_handle))
    except ReducerError:
        expected = frozenset()
        pair_handle = valve_handle = ""
    support_boundaries: dict[str, int] = {}
    if expected:
        for record in records:
            if record["phase"] != "ENV" or record["action_record"] is None:
                continue
            action = resolve_public_action(case.spec, dict(record["action_record"]))
            if (
                pair_handle not in support_boundaries
                and action.kind in {"ACQUIRE", "APPLY"}
                and action.argument in case.pair
            ):
                support_boundaries[pair_handle] = record["slot_index"]
            if valve_handle not in support_boundaries and action.kind == "CONFIGURE":
                support_boundaries[valve_handle] = record["slot_index"]
    timing = bool(expected) and all(
        handle in returned_at
        and handle in cited_at
        and handle in support_boundaries
        and returned_at[handle] < support_boundaries[handle]
        and cited_at[handle] <= support_boundaries[handle]
        for handle in expected
    ) and all(
        handle in returned_at and returned_at[handle] < slot
        for handle, slot in cited_at.items()
    )
    semantic_entailment = False
    if expected:
        rows = snapshot.row_map()
        pair_key, valve_key = decisive_keys(case)
        if pair_key in rows and valve_key in rows and case.spec.handles is not None:
            expected_families = {
                case.spec.handles.conditioner_families[index] for index in case.pair
            }
            semantic_entailment = (
                set(rows[pair_key].payload.get("families", ())) == expected_families
                and rows[pair_key].payload.get("relation") == "joint_conditioner_pair"
                and rows[valve_key].payload.get("mode") == VALVE_NAMES[case.spec.valve_truth]
                and rows[valve_key].payload.get("relation") == "stable_mode"
                and returned_exact.get(rows[pair_key].handle) == rows[pair_key].serialized
                and returned_exact.get(rows[valve_key].handle) == rows[valve_key].serialized
            )
    minimal = (
        bool(expected)
        and frozenset(cited) == expected
        and semantic_entailment
        and timing
    )
    operations = [
        {
            "operation": record["operation"],
            "scratch": record["scratch"],
            "citations": list(record["citations"]),
            "return": None
            if record["returned_row_hex"] is None
            else bytes.fromhex(record["returned_row_hex"]).decode("utf-8"),
        }
        for record in records
    ]
    return TraceScore(
        trajectory_id,
        condition,
        replay_outcome,
        replay_state.success,
        digest(actions),
        tuple(actions),
        digest(operations),
        tuple(sorted(returned_at)),
        cited,
        timing,
        semantic_entailment,
        minimal,
        replay_outcome == "SCIENTIFIC_VALID_SUCCESS" and replay_state.success,
        digest(artifact_bytes),
    )


@dataclass(frozen=True)
class InterventionScore:
    parent_id: str
    replay_exact: bool
    sham_preserved: bool
    cut_behavior_disrupted: bool
    cut_citation_invalid_secondary: bool
    twin_redirected: bool


def score_intervention(
    parent: TraceScore,
    replay: TraceScore,
    sham: TraceScore,
    cut: TraceScore,
    twin: TraceScore,
    actual_case: TargetCase,
    twin_case: TargetCase,
) -> InterventionScore:
    if (
        not parent.scientific_valid
        or not parent.legal_commit_success
        or not parent.citations_returned_before_use
        or not parent.citation_semantic_entailment
        or not parent.decisive_citations_minimal
    ):
        return InterventionScore(parent.trajectory_id, False, False, False, False, False)
    replay_exact = (
        replay.scientific_valid
        and replay.legal_commit_success
        and replay.operation_signature == parent.operation_signature
        and replay.action_signature == parent.action_signature
    )
    sham_preserved = (
        sham.scientific_valid
        and sham.legal_commit_success
        and sham.action_signature == parent.action_signature
    )
    cut_disrupted = (
        cut.scientific_valid
        and not cut.legal_commit_success
        and cut.action_signature != parent.action_signature
    )
    cut_citation_invalid = not cut.citations_returned_before_use
    try:
        actual_actions = tuple(resolve_public_action(actual_case.spec, dict(record)) for record in twin.action_records)
        actual_trace = execute(actual_case.spec, actual_actions)
        actual_success = bool(actual_trace and actual_trace[-1].state.success)
        twin_actions = tuple(resolve_public_action(twin_case.spec, dict(record)) for record in twin.action_records)
        # The actual world can terminate at RUN before COMMIT.  The registered
        # twin decisive prefix must nevertheless be exact and have the one-step
        # COMMIT continuation in the twin world.
        twin_prefix_trace = execute(twin_case.spec, twin_actions)
        twin_full_trace = execute(
            twin_case.spec,
            (*twin_actions, twin_case.plan[-1])
            if len(twin_actions) == 8
            else twin_actions,
        )
        twin_valid_continuation = bool(twin_full_trace and twin_full_trace[-1].state.success)
    except (TypeError, ValueError):
        actual_success = False
        twin_valid_continuation = False
    decisive_prefix = digest(list(twin.action_records[:7]))
    twin_redirected = (
        twin.scientific_valid
        and not twin.legal_commit_success
        and decisive_prefix == twin_case.decisive_signature
        and twin_valid_continuation
        and not actual_success
    )
    return InterventionScore(
        parent.trajectory_id,
        replay_exact,
        sham_preserved,
        cut_disrupted,
        cut_citation_invalid,
        twin_redirected,
    )


def evaluate_exact_gate(
    traces: Mapping[str, TraceScore], interventions: Mapping[str, InterventionScore]
) -> dict[str, Any]:
    """Apply exact registered denominators; invalid failures never help controls."""
    by_condition: dict[str, list[TraceScore]] = {}
    for trace in traces.values():
        by_condition.setdefault(trace.condition, []).append(trace)

    def successes(condition: str) -> int:
        return sum(
            trace.scientific_valid and trace.legal_commit_success
            for trace in by_condition.get(condition, [])
        )

    gold = by_condition.get("GOLD_REC", [])
    none = by_condition.get("NONE_REC", [])
    atoms = by_condition.get("ATOMS_REC", [])
    exact = {
        "gold_success_4_of_4": len(gold) == 4 and successes("GOLD_REC") == 4,
        "gold_minimal_paths_4_of_4": len(gold) == 4
        and all(
            trace.scientific_valid
            and trace.citations_returned_before_use
            and trace.decisive_citations_minimal
            for trace in gold
        ),
        "none_success_at_most_1_of_4": len(none) == 4
        and all(trace.scientific_valid for trace in none)
        and successes("NONE_REC") <= 1,
        "p_atoms_success_0_of_2": len(atoms) == 2
        and all(trace.scientific_valid for trace in atoms)
        and successes("ATOMS_REC") == 0,
        "auth_replay_2_of_2": len(interventions) == 2
        and all(row.replay_exact for row in interventions.values()),
        "sham_preservation_2_of_2": len(interventions) == 2
        and all(row.sham_preserved for row in interventions.values()),
        "cut_disruption_2_of_2": len(interventions) == 2
        and all(row.cut_behavior_disrupted for row in interventions.values()),
        "twin_redirection_2_of_2": len(interventions) == 2
        and all(row.twin_redirected for row in interventions.values()),
    }
    return {
        "local_check_passed": all(exact.values()),
        "exact_predicates": exact,
        "counts": {
            condition: {
                "registered": len(rows),
                "scientific_valid": sum(row.scientific_valid for row in rows),
                "success": successes(condition),
            }
            for condition, rows in sorted(by_condition.items())
        },
        "inference_firewall": (
            "nested deterministic-fixture exposures; no confidence interval, p-value, "
            "independence, reliability, or population estimate"
        ),
    }
