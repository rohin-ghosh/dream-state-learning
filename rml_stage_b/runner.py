"""Provider-free scripted CPU runner and model-provider orchestration seam."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from rml_d0.world import Action

from .contract import build_opportunity_registry, build_roster
from .fixtures import TargetCase, build_selected_cases, public_query_anchors
from .machine import RmlActionMachine, operation_bytes
from .memory import (
    ExactMemoryService,
    MemorySnapshot,
    assert_no_closure_residue,
    equivalence_closure,
    masked_snapshot,
    seal_pretarget_snapshot_universe,
)
from .reducer import (
    InterventionScore,
    TraceScore,
    decisive_handles,
    evaluate_exact_gate,
    score_frozen_trace,
    score_intervention,
)


@dataclass(frozen=True)
class ScriptedGateResult:
    traces: dict[str, TraceScore]
    interventions: dict[str, InterventionScore]
    report: dict
    machines: dict[str, RmlActionMachine]
    snapshots: dict[str, MemorySnapshot]


def _read_keys(case: TargetCase) -> tuple[str, str, str, str]:
    anchors = public_query_anchors(case)
    return (
        next(key for key in anchors if key.startswith("exchanger:")),
        next(key for key in anchors if key.startswith("pair:")),
        next(key for key in anchors if key.startswith("valve:")),
        next(key for key in anchors if key.startswith("schema:")),
    )


def _run_script(
    case: TargetCase,
    snapshot: MemorySnapshot,
    actions: Iterable[Action],
    *,
    citations: tuple[str, ...],
) -> RmlActionMachine:
    machine = RmlActionMachine.start(case)
    service = ExactMemoryService(snapshot)
    for key in _read_keys(case):
        machine = machine.advance(
            operation_bytes({"kind": "READ", "key": key}, scratch="bounded"), service
        )
        if machine.terminal:
            return machine
    for action in actions:
        machine = machine.advance(
            operation_bytes(
                {"kind": "ENV", "action": action.public_record(case.spec.handles)},
                scratch="bounded",
                citations=citations,
            ),
            service,
        )
        if machine.terminal:
            return machine
    return machine


def _empty(snapshot: MemorySnapshot) -> MemorySnapshot:
    return masked_snapshot(snapshot, [row.handle for row in snapshot.rows], transform="NONE")


def build_sham_snapshot(
    snapshot: MemorySnapshot, decisive: tuple[str, ...]
) -> tuple[MemorySnapshot, tuple[str, ...]]:
    """Mask unopened nondecisive classes with exact count/byte/token matching."""
    by_handle = snapshot.handle_map()
    selected: list[str] = []
    unavailable = set(decisive)
    ordered_rows = [by_handle[handle] for handle in snapshot.sham_candidate_order]
    for handle in decisive:
        source = by_handle[handle]
        candidate = next(
            (
                row
                for row in ordered_rows
                if row.handle not in unavailable
                and len(row.serialized) == len(source.serialized)
                and row.token_count == source.token_count
                and row.payload.get("relation") == source.payload.get("relation")
            ),
            None,
        )
        if candidate is None:
            raise ValueError("no presealed byte/token-matched nondecisive sham class")
        selected.append(candidate.handle)
        unavailable.add(candidate.handle)
    return masked_snapshot(snapshot, selected, transform="SHAM"), tuple(selected)


def run_scripted_cpu_gate() -> ScriptedGateResult:
    """Exercise all 18 registered trajectories without any model/provider call."""
    pretarget_seal = seal_pretarget_snapshot_universe()
    snapshots = pretarget_seal.snapshot_map()
    cases = build_selected_cases(pretarget_seal)
    roster = build_roster()
    if len(build_opportunity_registry(roster)) != 234:
        raise AssertionError("opportunity registry drift")
    machines: dict[str, RmlActionMachine] = {}
    execution_cases: dict[str, TargetCase] = {}
    used_snapshots: dict[str, MemorySnapshot] = {}
    gold_scores: dict[str, TraceScore] = {}
    fixed_plan = cases["J_H"].plan

    # Parents must freeze before any trace-derived CUT construction.
    for registration in roster:
        if registration.condition != "GOLD_REC":
            continue
        case = cases[registration.target_id]
        snapshot = snapshots[f"{case.source_projection}:GOLD"]
        citations = decisive_handles(case, snapshot)
        machine = _run_script(case, snapshot, case.plan, citations=citations)
        machines[registration.trajectory_id] = machine
        execution_cases[registration.trajectory_id] = case
        used_snapshots[registration.trajectory_id] = snapshot
        gold_scores[registration.trajectory_id] = score_frozen_trace(
            registration.trajectory_id, registration.condition, case, machine, snapshot
        )

    for registration in roster:
        if registration.condition == "GOLD_REC":
            continue
        case = cases[registration.target_id]
        parent_case = cases[registration.target_id]
        base = snapshots[f"{case.source_projection}:GOLD"]
        citations: tuple[str, ...] = ()
        actions = fixed_plan
        if registration.condition == "NONE_REC":
            snapshot = _empty(snapshots["H:GOLD"])
        elif registration.condition == "ATOMS_REC":
            snapshot = snapshots["H:ATOMS"]
        elif registration.condition in {"AUTH_REPLAY", "SHAM_REC", "CUT_REC", "TWIN_REC"}:
            parent_id = registration.parent_id
            if parent_id is None:
                raise AssertionError("intervention has no parent")
            parent_snapshot = used_snapshots[parent_id]
            parent_case = cases[registration.target_id]
            decisive = decisive_handles(parent_case, parent_snapshot)
            if registration.condition == "AUTH_REPLAY":
                snapshot = parent_snapshot
                actions = parent_case.plan
                citations = decisive
            elif registration.condition == "SHAM_REC":
                snapshot, _ = build_sham_snapshot(parent_snapshot, decisive)
                actions = parent_case.plan
                citations = decisive
            elif registration.condition == "CUT_REC":
                closure = equivalence_closure(parent_snapshot, decisive)
                snapshot = masked_snapshot(parent_snapshot, decisive, transform="CUT")
                assert_no_closure_residue(snapshot, closure)
                twin_id = "J_TWIN" if registration.target_id == "J_H" else "P_TWIN"
                actions = cases[twin_id].plan
                citations = decisive
            else:
                twin_id = "J_TWIN" if registration.target_id == "J_H" else "P_TWIN"
                snapshot = snapshots[f"{cases[twin_id].source_projection}:GOLD"]
                actions = cases[twin_id].plan
                citations = decisive_handles(cases[twin_id], snapshot)
        else:
            raise AssertionError("unexpected condition")
        execution_case = case
        machine = _run_script(execution_case, snapshot, actions, citations=citations)
        machines[registration.trajectory_id] = machine
        execution_cases[registration.trajectory_id] = execution_case
        used_snapshots[registration.trajectory_id] = snapshot

    scores = {
        registration.trajectory_id: score_frozen_trace(
            registration.trajectory_id,
            registration.condition,
            execution_cases[registration.trajectory_id],
            machines[registration.trajectory_id],
            used_snapshots[registration.trajectory_id],
        )
        for registration in roster
    }
    interventions: dict[str, InterventionScore] = {}
    for target_id in ("J_H", "P_H"):
        parent_id = f"GOLD_REC:{target_id}"
        twin_id = "J_TWIN" if target_id == "J_H" else "P_TWIN"
        interventions[parent_id] = score_intervention(
            scores[parent_id],
            scores[f"AUTH_REPLAY:{target_id}"],
            scores[f"SHAM_REC:{target_id}"],
            scores[f"CUT_REC:{target_id}"],
            scores[f"TWIN_REC:{target_id}"],
            cases[target_id],
            cases[twin_id],
        )
    return ScriptedGateResult(
        scores,
        interventions,
        evaluate_exact_gate(scores, interventions),
        machines,
        used_snapshots,
    )
