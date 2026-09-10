"""Exact finite planners and the Stage-A history/quotient bisimulation check."""

from __future__ import annotations

import hashlib
from collections import deque
from dataclasses import dataclass, replace
from typing import Any

from .canonical import canonical_bytes
from .world import (
    Action,
    GameState,
    TargetSpec,
    action_universe,
    apply_conditioner,
    initial_state,
    step,
)


@dataclass
class Counters:
    states: int = 0
    transitions: int = 0

    def add(self, other: "Counters") -> None:
        self.states += other.states
        self.transitions += other.transitions


@dataclass(frozen=True)
class PlanResult:
    minimum_depth: int | None
    state_count: int
    transition_count: int
    structural_unreachable: bool


@dataclass(frozen=True)
class QuotientComparison:
    states: int
    transitions: int
    depth_summaries: tuple[dict[str, Any], ...]
    literal_vector_sha256: str


def _coolant_reachable(spec: TargetSpec) -> tuple[bool, Counters]:
    available = tuple(
        index
        for index, status in enumerate(spec.statuses)
        if status != 3 and not (spec.forbidden_mask & (1 << index))
    )
    frontier = {(spec.initial_coolant, 0)}
    seen = set(frontier)
    transitions = 0
    for _ in available:
        next_frontier: set[tuple[int, int]] = set()
        for coolant, used in frontier:
            for index in available:
                if used & (1 << index):
                    continue
                transitions += 1
                successor = (
                    apply_conditioner(coolant, spec.transforms[index]),
                    used | (1 << index),
                )
                if successor not in seen:
                    seen.add(successor)
                    next_frontier.add(successor)
        frontier = next_frontier
    reachable = any(coolant == spec.exchanger for coolant, _ in seen)
    return reachable, Counters(states=len(seen), transitions=transitions)


def minimum_depth(spec: TargetSpec) -> PlanResult:
    """Breadth-first exact minimum, with an exact finite impossibility precheck."""

    reachable, structural = _coolant_reachable(spec)
    if not reachable:
        return PlanResult(None, structural.states, structural.transitions, True)

    start = initial_state(spec)
    queue: deque[tuple[GameState, int]] = deque([(start, 0)])
    seen = {start.quotient_key()}
    transitions = structural.transitions
    minimum: int | None = None
    while queue:
        state, depth = queue.popleft()
        if minimum is not None and depth >= minimum:
            break
        if state.terminal or depth >= spec.budget:
            continue
        for action in _progress_actions(spec, state):
            transitions += 1
            successor = step(spec, state, action).state
            if successor.success:
                candidate = depth + 1
                minimum = candidate if minimum is None else min(minimum, candidate)
                continue
            if successor.terminal:
                continue
            key = successor.quotient_key()
            if key not in seen:
                seen.add(key)
                queue.append((successor, depth + 1))

    return PlanResult(minimum, len(seen) + structural.states, transitions, False)


def _progress_actions(spec: TargetSpec, state: GameState) -> tuple[Action, ...]:
    """All non-dominated actions that can lie on a shortest successful path.

    Information actions, STOP, moves to DOCK, illegal actions, and a RUN known
    to trip have no nonterminal successor and can be deleted from a successful
    history without invalidating its suffix.  The complete closed alphabet is
    still exercised by the bisimulation and transition-law tests.
    """

    actions: list[Action] = []
    if state.position != "LOCKER":
        actions.append(Action("MOVE", "LOCKER"))
    if state.position != "PLANT":
        actions.append(Action("MOVE", "PLANT"))
    if state.position == "LOCKER":
        actions.extend(
            Action("ACQUIRE", index)
            for index, status in enumerate(state.statuses)
            if status == 0
        )
    if state.position == "PLANT":
        actions.extend(
            Action("APPLY", index)
            for index, status in enumerate(state.statuses)
            if status == 1 and not (spec.forbidden_mask & (1 << index))
        )
        actions.extend(
            Action("CONFIGURE", mode)
            for mode in range(4)
            if mode != state.valve_mode
        )
        coolant_ok = state.coolant == spec.exchanger
        valve_ok = state.valve_mode == spec.valve_truth
        stable = (
            coolant_ok and valve_ok
            if spec.kind == "FIELD_LOOP"
            else coolant_ok
            if spec.kind == "EXCHANGER_BENCH"
            else valve_ok
        )
        if stable and not state.run_stable:
            actions.append(Action("RUN"))
        if state.run_stable:
            actions.append(Action("COMMIT"))
    return tuple(sorted(actions, key=lambda action: action.tie_bytes(spec.handles)))


@dataclass(frozen=True)
class LiteralState:
    """Public literal state richer than the certified nine-field quotient."""

    game: GameState
    action_count: int
    last_result_code: str
    outlet_temperature: str
    pressure: str
    commit_succeeded: bool

    @classmethod
    def initial(cls, spec: TargetSpec) -> "LiteralState":
        return cls(
            game=initial_state(spec),
            action_count=0,
            last_result_code="NONE",
            outlet_temperature="UNKNOWN",
            pressure="IDLE",
            commit_succeeded=False,
        )


def _literal_step(
    spec: TargetSpec, literal: LiteralState, action: Action
) -> tuple[LiteralState, bytes]:
    transition = step(spec, literal.game, action)
    game = transition.state
    successor = LiteralState(
        game=game,
        action_count=spec.budget - game.remaining,
        last_result_code=transition.result_code,
        outlet_temperature="NOMINAL" if game.run_stable else "UNKNOWN",
        pressure="STABLE" if game.run_stable else "IDLE",
        commit_succeeded=game.success,
    )
    state_delta = {
        "action_count": successor.action_count,
        "commit_succeeded": successor.commit_succeeded,
        "coolant": game.coolant,
        "failure_kind": game.failure,
        "item_status": list(game.statuses),
        "last_result_code": successor.last_result_code,
        "outlet_temperature": successor.outlet_temperature,
        "position": game.position,
        "pressure": successor.pressure,
        "remaining_actions": game.remaining,
        "run_stable": game.run_stable,
        "terminal": game.terminal,
        "valve_mode": game.valve_mode,
    }
    outcome = canonical_bytes(
        {
            "action": action.public_record(spec.handles),
            "result_code": transition.result_code,
            "state_delta": state_delta,
            "text": transition.text,
        }
    )
    return successor, outcome


def compare_literal_and_quotient(spec: TargetSpec, depth: int = 6) -> QuotientComparison:
    """Exhaustively compare literal histories with their state quotient.

    Every step uses the complete closed public action alphabet.  Histories are
    deduplicated only by the richer literal state; the check then proves that
    all literal states sharing the registered quotient have identical
    one-step quotient successors and rendered result bytes.
    """

    start = LiteralState.initial(spec)
    literal: set[LiteralState] = {start}
    counters = Counters(states=1)
    actions = action_universe(spec)
    depth_summaries: list[dict[str, Any]] = []

    for _ in range(depth):
        literal_next: set[LiteralState] = set()
        quotient_successors: dict[
            tuple[tuple[Any, ...], Action], tuple[tuple[Any, ...], bytes, str]
        ] = {}
        legal_records: list[dict[str, Any]] = []
        successor_records: list[dict[str, Any]] = []
        for literal_state in literal:
            source_key = literal_state.game.quotient_key()
            for action in actions:
                counters.transitions += 1
                successor, outcome = _literal_step(spec, literal_state, action)
                literal_next.add(successor)
                comparison = (
                    successor.game.quotient_key(),
                    outcome,
                    successor.last_result_code,
                )
                prior = quotient_successors.setdefault((source_key, action), comparison)
                if prior != comparison:
                    raise AssertionError(
                        "one quotient state/action has unequal literal result bytes"
                    )
        for (source_key, action), (successor_key, outcome, result_code) in sorted(
            quotient_successors.items(),
            key=lambda item: canonical_bytes(
                [item[0][0], item[0][1].public_record(spec.handles)]
            ),
        ):
            action_record = action.public_record(spec.handles)
            if result_code not in {"ILLEGAL", "CAP"}:
                legal_records.append({"action": action_record, "source": list(source_key)})
            successor_records.append(
                {
                    "action": action_record,
                    "outcome_sha256": hashlib.sha256(outcome).hexdigest(),
                    "source": list(source_key),
                    "successor": list(successor_key),
                }
            )
        projected = {state.game.quotient_key() for state in literal_next}
        from_transitions = {value[0] for value in quotient_successors.values()}
        if projected != from_transitions:
            raise AssertionError("literal and quotient successor sets differ")
        counters.states += len(literal_next)
        reached_records = sorted(
            (list(key) for key in projected), key=canonical_bytes
        )
        depth_summaries.append(
            {
                "complete_action_count": len(actions),
                "depth": len(depth_summaries) + 1,
                "legal_actions_sha256": hashlib.sha256(
                    canonical_bytes(legal_records)
                ).hexdigest(),
                "literal_state_count": len(literal_next),
                "minimum_terminal_value": int(
                    any(state.game.success for state in literal_next)
                ),
                "reached_sha256": hashlib.sha256(
                    canonical_bytes(reached_records)
                ).hexdigest(),
                "rendered_successors_sha256": hashlib.sha256(
                    canonical_bytes(successor_records)
                ).hexdigest(),
                "quotient_state_count": len(projected),
            }
        )
        literal = literal_next
    summaries = tuple(depth_summaries)
    return QuotientComparison(
        states=counters.states,
        transitions=counters.transitions,
        depth_summaries=summaries,
        literal_vector_sha256=hashlib.sha256(canonical_bytes(list(summaries))).hexdigest(),
    )


QUOTIENT_FIELDS = (
    "position",
    "remaining_actions",
    "coolant_bits",
    "item_status[4]",
    "valve_mode",
    "run_stable",
    "terminal",
    "failure_kind",
    "necessity_mask",
)


def necessity_disposition(state: GameState) -> str:
    return "BASE" if state.necessity_mask == 0 else f"REGISTERED_CUT_{state.necessity_mask}"


def _observable_bytes(spec: TargetSpec, state: GameState, action: Action) -> bytes:
    transition = step(spec, state, action)
    return canonical_bytes(
        {
            "action": action.public_record(spec.handles),
            "failure_kind": transition.state.failure,
            "result_code": transition.result_code,
            "state": list(transition.state.quotient_key()[:-1]),
            "success": transition.state.success,
            "text": transition.text,
        }
    )


def quotient_deletion_witnesses(spec: TargetSpec) -> list[dict[str, Any]]:
    """Give one explicit collision caused by deleting each quotient field."""

    base = initial_state(spec)
    ready = GameState(
        position="PLANT",
        remaining=2,
        coolant=spec.exchanger,
        statuses=spec.statuses,
        valve_mode=spec.valve_truth,
        run_stable=False,
        terminal=False,
        failure="NONE",
    )
    pairs = (
        (
            replace(base, position="DOCK"),
            replace(base, position="LOCKER"),
            "ACQUIRE legality",
        ),
        (replace(ready, remaining=1), ready, "attainable terminal value"),
        (ready, replace(ready, coolant=ready.coolant ^ 1), "RUN coolant predicate"),
        (
            replace(base, position="PLANT", statuses=(1,) + base.statuses[1:]),
            replace(base, position="PLANT", statuses=(2,) + base.statuses[1:]),
            "ACQUIRE/APPLY legality",
        ),
        (ready, replace(ready, valve_mode=tau_wrong(spec.valve_truth)), "RUN valve predicate"),
        (replace(ready, remaining=1), replace(ready, remaining=1, run_stable=True), "COMMIT legality"),
        (base, replace(base, terminal=True), "post-terminal legality"),
        (
            replace(base, terminal=True, failure="ILLEGAL"),
            replace(base, terminal=True, failure="LOOP_TRIPPED"),
            "public failure outcome",
        ),
        (base, replace(base, necessity_mask=1), "J certificate disposition"),
    )
    actions = (
        Action("ACQUIRE", 0),
        Action("RUN"),
        Action("RUN"),
        Action("APPLY", 0),
        Action("RUN"),
        Action("COMMIT"),
        Action("OBSERVE", spec.handles.module_family if spec.handles else ""),
        None,
        None,
    )
    witnesses: list[dict[str, Any]] = []
    for index, (left, right, discriminator) in enumerate(pairs):
        left_key = left.quotient_key()
        right_key = right.quotient_key()
        if left_key[index] == right_key[index]:
            raise AssertionError("deletion witness does not differ at named field")
        if left_key[:index] + left_key[index + 1 :] != right_key[:index] + right_key[index + 1 :]:
            raise AssertionError("deletion witness differs outside named field")
        if index == 1:
            left_run = step(spec, left, Action("RUN")).state
            right_run = step(spec, right, Action("RUN")).state
            left_final = step(spec, left_run, Action("COMMIT"))
            right_final = step(spec, right_run, Action("COMMIT"))
            observed = [left_final.state.success, right_final.state.success]
            if observed != [False, True]:
                raise AssertionError("remaining-actions witness did not change value")
            observable_hashes = [
                canonical_bytes({"success": value}).hex() for value in observed
            ]
        elif index == 7:
            observable_hashes = [
                canonical_bytes({"failure_kind": left.failure}).hex(),
                canonical_bytes({"failure_kind": right.failure}).hex(),
            ]
        elif index == 8:
            dispositions = [necessity_disposition(left), necessity_disposition(right)]
            if dispositions[0] == dispositions[1]:
                raise AssertionError("necessity-mask witness has one disposition")
            observable_hashes = [canonical_bytes(value).hex() for value in dispositions]
        else:
            action = actions[index]
            assert action is not None
            observable_hashes = [
                _observable_bytes(spec, left, action).hex(),
                _observable_bytes(spec, right, action).hex(),
            ]
        if observable_hashes[0] == observable_hashes[1]:
            raise AssertionError("deletion collision lacks a distinguishing observable")
        witnesses.append(
            {
                "deleted_field": QUOTIENT_FIELDS[index],
                "discriminator": discriminator,
                "observable_bytes_differ": True,
                "reduced_keys_collide": True,
            }
        )
    return witnesses


def tau_wrong(mode: int) -> int:
    return mode ^ 1
