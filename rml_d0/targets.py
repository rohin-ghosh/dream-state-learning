"""Exhaustive Stage-A target, bridge, valve, P, and J micro-goldens."""

from __future__ import annotations

import hashlib
from collections import Counter
from dataclasses import replace
from fractions import Fraction
from itertools import permutations
from typing import Any

from .canonical import canonical_bytes
from .planner import Counters, minimum_depth, necessity_disposition
from .rng import draw_target_handles, stage_a_bridge_tape, stage_a_target_tape
from .world import (
    ITEM_ABSENT,
    ITEM_INVENTORY,
    ITEM_LOCKER,
    Action,
    Conditioner,
    GameState,
    TargetSpec,
    canonical_plan,
    execute,
    initial_state,
    action_universe,
    step,
    target_public_record,
    tau_c,
    tau_v,
    useful_pairs,
)


def make_target(initial_coolant: int, valve_truth: int) -> TargetSpec:
    handles = draw_target_handles(stage_a_target_tape(), 4)
    return TargetSpec(
        initial_coolant=initial_coolant,
        transforms=(0, 1, 2, 3),
        exchanger=initial_coolant ^ 3,
        valve_truth=valve_truth,
        handles=handles,
    )


def transition_law_goldens() -> dict[str, Any]:
    spec = make_target(0, 0)
    start = initial_state(spec)
    cases: list[str] = []

    same_move = step(spec, start, Action("MOVE", "DOCK"))
    if same_move.result_code != "ILLEGAL" or same_move.state.position != "DOCK":
        raise AssertionError("MOVE to current position is not no-partial ILLEGAL")
    cases.append("move_current_illegal")

    at_locker = step(spec, start, Action("MOVE", "LOCKER")).state
    acquired = step(spec, at_locker, Action("ACQUIRE", 0))
    if acquired.result_code != "ACQUIRED" or acquired.state.statuses[0] != ITEM_INVENTORY:
        raise AssertionError("ACQUIRE law failed")
    cases.append("acquire")

    at_plant = step(spec, acquired.state, Action("MOVE", "PLANT")).state
    applied = step(spec, at_plant, Action("APPLY", 0))
    if applied.result_code != "APPLIED" or applied.state.coolant != 0:
        raise AssertionError("APPLY law failed")
    cases.append("apply")

    configured = step(spec, at_plant, Action("CONFIGURE", 0))
    if configured.result_code != "CONFIGURED" or configured.state.valve_mode != 0:
        raise AssertionError("CONFIGURE law failed")
    cases.append("configure")

    ready = GameState(
        position="PLANT",
        remaining=3,
        coolant=spec.exchanger,
        statuses=spec.statuses,
        valve_mode=spec.valve_truth,
        run_stable=False,
        terminal=False,
        failure="NONE",
    )
    stable = step(spec, ready, Action("RUN"))
    if stable.result_code != "RUN_STABLE" or not stable.state.run_stable:
        raise AssertionError("FIELD_LOOP stable RUN failed")
    cases.append("field_run_stable")

    tripped = step(spec, replace(ready, coolant=ready.coolant ^ 1), Action("RUN"))
    if tripped.result_code != "RUN_TRIPPED" or tripped.state.failure != "LOOP_TRIPPED":
        raise AssertionError("FIELD_LOOP tripped RUN failed")
    cases.append("field_run_tripped")

    exchanger_spec = replace(spec, kind="EXCHANGER_BENCH", budget=2)
    exchanger_ready = replace(ready, valve_mode=-1, remaining=2)
    if step(exchanger_spec, exchanger_ready, Action("RUN")).result_code != "RUN_STABLE":
        raise AssertionError("certified-bypass exchanger ignored coolant")
    cases.append("exchanger_bypass")

    valve_spec = replace(spec, kind="VALVE_BENCH", budget=2)
    valve_ready = replace(ready, coolant=ready.coolant ^ 1, remaining=2)
    if step(valve_spec, valve_ready, Action("RUN")).result_code != "RUN_STABLE":
        raise AssertionError("valve bench did not ignore exchanger")
    cases.append("valve_bench")

    committed = step(spec, stable.state, Action("COMMIT"))
    if committed.result_code != "COMMITTED" or not committed.state.success:
        raise AssertionError("COMMIT law failed")
    cases.append("commit")

    stopped = step(spec, stable.state, Action("STOP"))
    if stopped.result_code != "STOPPED" or stopped.state.success or stopped.state.run_stable:
        raise AssertionError("STOP did not yield zero terminal state")
    cases.append("stop")

    observed = step(spec, start, Action("OBSERVE", spec.handles.module_family))
    if observed.result_code != "OBSERVED":
        raise AssertionError("OBSERVE law failed")
    cases.append("observe")

    measured_state = replace(start, coolant=3, run_stable=True)
    expected_values = {
        "VISCOSITY": "HIGH",
        "INHIBITOR": "RICH",
        "OUTLET_TEMPERATURE": "NOMINAL",
        "PRESSURE": "STABLE",
    }
    for measure, value in expected_values.items():
        measured = step(spec, measured_state, Action("MEASURE", measure))
        if measured.text != f"Gauge {measure} reads {value}.":
            raise AssertionError(f"MEASURE {measure} did not render its public value")
        cases.append(f"measure_{measure.lower()}")

    capped = step(
        spec,
        replace(start, remaining=0),
        Action("OBSERVE", spec.handles.module_family),
    )
    if capped.result_code != "CAP" or capped.state.failure != "CAP":
        raise AssertionError("cap-exceeding action did not fail closed")
    cases.append("cap")

    post_terminal = step(
        spec, committed.state, Action("OBSERVE", spec.handles.module_family)
    )
    if post_terminal.result_code != "ILLEGAL" or post_terminal.state.success:
        raise AssertionError("post-terminal action retained prior success")
    cases.append("post_terminal_illegal_zero")

    if len(action_universe(spec)) != 23:
        raise AssertionError("closed four-item action universe cardinality changed")
    return {"action_universe_cardinality": 23, "cases": cases}


def recall_goldens() -> list[dict[str, Any]]:
    spec = TargetSpec(
        initial_coolant=0,
        transforms=(0, 1, 2, 3),
        exchanger=3,
        valve_truth=0,
        kind="EXCHANGER_BENCH",
        budget=1,
        initial_statuses=(ITEM_INVENTORY,) * 4,
    )
    rows: list[dict[str, Any]] = []
    for desired, correct_index in ((2, 1), (1, 3)):
        successes = []
        for index in range(4):
            transition = step(spec, initial_state(spec), Action("APPLY", index))
            if transition.state.coolant == desired:
                successes.append(index)
        if successes != [correct_index]:
            raise AssertionError("RecallFixture does not have one correct APPLY")
        rows.append(
            {
                "action_budget": 1,
                "correct_item": correct_index,
                "desired_coolant": desired,
                "inventory_count": 4,
                "position": "PLANT",
            }
        )
    return rows


def target_goldens() -> tuple[list[dict[str, Any]], Counters]:
    rows: list[dict[str, Any]] = []
    counters = Counters()
    for initial in range(4):
        for mode in range(4):
            authentic = make_target(initial, mode)
            twin = authentic.twin()
            if authentic.handles is not twin.handles:
                raise AssertionError("target twin did not copy the injected handle object")
            authentic_pairs = useful_pairs(authentic)
            twin_pairs = useful_pairs(twin)
            if len(authentic_pairs) != 1 or len(twin_pairs) != 1:
                raise AssertionError("target does not have one useful pair per side")
            authentic_pair = next(iter(authentic_pairs))
            twin_pair = next(iter(twin_pairs))
            if set(authentic_pair) & set(twin_pair):
                raise AssertionError("twin useful pairs are not disjoint")
            if twin.valve_truth != tau_v(authentic.valve_truth):
                raise AssertionError("twin valve mode is wrong")
            if canonical_bytes(target_public_record(authentic)) != canonical_bytes(
                target_public_record(twin)
            ):
                raise AssertionError("target-visible twin bytes do not collide")

            side_results: list[dict[str, Any]] = []
            for side_name, spec, pair in (
                ("H", authentic, authentic_pair),
                ("TWIN", twin, twin_pair),
            ):
                plan = minimum_depth(spec)
                counters.states += plan.state_count
                counters.transitions += plan.transition_count
                if plan.minimum_depth != 9:
                    raise AssertionError(f"{side_name} minimum depth is not nine")
                trace = execute(spec, canonical_plan(pair, spec.valve_truth))
                if len(trace) != 9 or not trace[-1].state.success:
                    raise AssertionError("registered nine-action plan failed")

                successes: list[tuple[tuple[int, int], int]] = []
                for candidate_pair in useful_pairs(spec):
                    for candidate_mode in range(4):
                        candidate_trace = execute(
                            spec, canonical_plan(candidate_pair, candidate_mode)
                        )
                        if candidate_trace[-1].state.success:
                            successes.append((candidate_pair, candidate_mode))
                if successes != [(pair, spec.valve_truth)]:
                    raise AssertionError("registered pair/mode is not unique")
                shortest_plans: list[tuple[bytes, tuple[Action, ...]]] = []
                for acquire_order in permutations(pair):
                    operations = (
                        Action("APPLY", pair[0]),
                        Action("APPLY", pair[1]),
                        Action("CONFIGURE", spec.valve_truth),
                    )
                    for plant_order in permutations(operations):
                        actions = (
                            Action("MOVE", "LOCKER"),
                            Action("ACQUIRE", acquire_order[0]),
                            Action("ACQUIRE", acquire_order[1]),
                            Action("MOVE", "PLANT"),
                            *plant_order,
                            Action("RUN"),
                            Action("COMMIT"),
                        )
                        if not execute(spec, actions)[-1].state.success:
                            raise AssertionError("a shortest tie failed")
                        signature = canonical_bytes(
                            [action.public_record(spec.handles) for action in actions]
                        )
                        shortest_plans.append((signature, actions))
                shortest_plans.sort(key=lambda item: item[0])
                if len(shortest_plans) != 12 or len(
                    {signature for signature, _ in shortest_plans}
                ) != 12:
                    raise AssertionError("shortest tie cardinality is not twelve")
                side_results.append(
                    {
                        "canonical_tie_sha256": hashlib.sha256(
                            shortest_plans[0][0]
                        ).hexdigest(),
                        "minimum_depth": plan.minimum_depth,
                        "pair": list(pair),
                        "side": side_name,
                        "shortest_tie_count": len(shortest_plans),
                        "valve_mode": spec.valve_truth,
                    }
                )
            rows.append(
                {
                    "exchanger": authentic.exchanger,
                    "initial_coolant": initial,
                    "sides": side_results,
                    "visible_sha256": hashlib.sha256(
                        canonical_bytes(target_public_record(authentic))
                    ).hexdigest(),
                }
            )
    return rows, counters


def target_oracle_vectors() -> dict[str, Any]:
    conditioner_table: list[dict[str, Any]] = []
    for initial in range(4):
        authentic = make_target(initial, 0)
        twin = authentic.twin()
        h_pair = next(iter(useful_pairs(authentic)))
        twin_pair = next(iter(useful_pairs(twin)))
        conditioner_table.append(
            {
                "h_pair": [Conditioner(authentic.transforms[index]).name for index in h_pair],
                "r": f"{authentic.exchanger:02b}",
                "twin_pair": [
                    Conditioner(authentic.transforms[index]).name for index in twin_pair
                ],
                "u": f"{initial:02b}",
            }
        )
    valve_table = [
        {"h": name, "twin": ("RECIRCULATE", "BYPASS", "DIRECT", "PULSE")[index]}
        for index, name in enumerate(("BYPASS", "RECIRCULATE", "PULSE", "DIRECT"))
    ]
    first = conditioner_table[0]
    nw_target_00 = {
        "h_mode": "BYPASS",
        "h_pair": first["h_pair"],
        "minimum_depth": 9,
        "r": first["r"],
        "twin_mode": "RECIRCULATE",
        "twin_pair": first["twin_pair"],
        "u": first["u"],
    }
    return {
        "conditioner_table": conditioner_table,
        "nw_target_00": nw_target_00,
        "valve_table": valve_table,
    }


def _bridge_trial(initial: int, exchanger: int, code: int) -> tuple[str, str]:
    spec = TargetSpec(
        initial_coolant=initial,
        transforms=(code,),
        exchanger=exchanger,
        valve_truth=0,
        kind="EXCHANGER_BENCH",
        budget=2,
        initial_statuses=(ITEM_INVENTORY,),
    )
    trace = execute(spec, (Action("APPLY", 0), Action("RUN")))
    if len(trace) != 2:
        raise AssertionError("bridge trial did not execute two actions")
    return trace[0].result_code, trace[1].result_code


def bridge_goldens() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    tape = stage_a_bridge_tape()

    def reset_record() -> dict[str, Any]:
        episode = tape.draw("EP")
        goal = tape.draw("GO")
        coolant = tape.draw("CO")
        loop = tape.draw("LO")
        valve = tape.draw("VA")
        cartridge = tape.draw("CI")
        return {
            "certified_bypass": True,
            "coolant_handle": coolant,
            "episode_handle": episode,
            "goal_handle": goal,
            "layout": "EXCHANGER_BENCH",
            "loop_handle": loop,
            "object_handle": cartridge,
            "valve_handle": valve,
        }

    for bit in range(2):
        for accepted_value in range(2):
            for other_value in range(2):
                initial_bits = [0, 0]
                initial_bits[1 - bit] = other_value
                exchanger_bits = [0, 0]
                exchanger_bits[bit] = accepted_value
                exchanger_bits[1 - bit] = other_value
                initial = (initial_bits[0] << 1) | initial_bits[1]
                exchanger = (exchanger_bits[0] << 1) | exchanger_bits[1]
                code_a = accepted_value if bit == 0 else 2 + accepted_value
                code_b = (1 - accepted_value) if bit == 0 else 2 + (1 - accepted_value)
                h = (
                    _bridge_trial(initial, exchanger, code_a),
                    _bridge_trial(initial, exchanger, code_b),
                )
                twin = (
                    _bridge_trial(initial, exchanger, tau_c(code_a)),
                    _bridge_trial(initial, exchanger, tau_c(code_b)),
                )
                if tuple(run for _, run in h) != ("RUN_STABLE", "RUN_TRIPPED"):
                    raise AssertionError("authentic bridge contrast failed")
                if tuple(run for _, run in twin) != ("RUN_TRIPPED", "RUN_STABLE"):
                    raise AssertionError("twin bridge contrast failed")
                # The two fresh resets are consumed from one independent,
                # presealed tape.  No row ordinal or selector metadata enters
                # any handle value.
                reset_a = reset_record()
                reset_b = reset_record()
                handle_values_a = {v for k, v in reset_a.items() if k.endswith("handle")}
                handle_values_b = {v for k, v in reset_b.items() if k.endswith("handle")}
                if handle_values_a & handle_values_b:
                    raise AssertionError("bridge trials share a reset/object handle")
                rows.append(
                    {
                        "accepted_value": accepted_value,
                        "bit": "v" if bit == 0 else "i",
                        "exchanger": exchanger,
                        "h_runs": [run for _, run in h],
                        "initial": initial,
                        "other_value": other_value,
                        "reset_a": reset_a,
                        "reset_b": reset_b,
                        "twin_runs": [run for _, run in twin],
                    }
                )
    if tape.remaining:
        raise AssertionError("bridge handle tape was not consumed exactly")
    return rows


def validate_bridge_rows(rows: list[dict[str, Any]]) -> bool:
    return not bridge_validation_errors(rows)


def bridge_validation_errors(rows: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    if len(rows) != 8:
        errors.append("row_count")
    for ordinal, row in enumerate(rows):
        if row.get("h_runs") != ["RUN_STABLE", "RUN_TRIPPED"]:
            errors.append(f"row_{ordinal}_h_result_vector")
        if row.get("twin_runs") != ["RUN_TRIPPED", "RUN_STABLE"]:
            errors.append(f"row_{ordinal}_twin_result_vector")
        reset_a, reset_b = row.get("reset_a", {}), row.get("reset_b", {})
        if not reset_a.get("certified_bypass") or not reset_b.get("certified_bypass"):
            errors.append(f"row_{ordinal}_not_certified_bypass")
        if reset_a.get("layout") != "EXCHANGER_BENCH" or reset_b.get("layout") != "EXCHANGER_BENCH":
            errors.append(f"row_{ordinal}_layout")
        handles_a = {value for key, value in reset_a.items() if key.endswith("handle")}
        handles_b = {value for key, value in reset_b.items() if key.endswith("handle")}
        if handles_a & handles_b:
            errors.append(f"row_{ordinal}_shared_reset_object_handle")
    return errors


def bridge_oracle_vectors() -> dict[str, Any]:
    table: list[dict[str, Any]] = []
    for bit in range(2):
        for accepted_value in range(2):
            for other_value in range(2):
                reset = other_value if bit == 0 else other_value << 1
                exchanger = (
                    (accepted_value << 1) | other_value
                    if bit == 0
                    else (other_value << 1) | accepted_value
                )
                code_a = accepted_value if bit == 0 else 2 + accepted_value
                code_b = (1 - accepted_value) if bit == 0 else 3 - accepted_value
                table.append(
                    {
                        "a_code": Conditioner(code_a).name,
                        "b_code": Conditioner(code_b).name,
                        "bit": "v" if bit == 0 else "i",
                        "exchanger": f"{exchanger:02b}",
                        "reset": f"{reset:02b}",
                        "set_value": accepted_value,
                        "z": other_value,
                    }
                )
    return {
        "result_vector": {
            "h_results": ["APPLIED", "RUN_STABLE", "APPLIED", "RUN_TRIPPED"],
            "twin_results": [
                "APPLIED",
                "RUN_TRIPPED",
                "APPLIED",
                "RUN_STABLE",
            ],
        },
        "table": table,
    }


def source_count_golden() -> dict[str, Any]:
    dense_modules = (3, 2, 5, 11)
    sparse_modules = (0, 1, 1, 1)
    balance_events = (0, 4, 4, 4)
    bridge_events = (0, 4, 4, 4)
    cumulative_events: list[int] = []
    cumulative_mappings: list[int] = []
    event_total = 0
    mapping_total = 0
    for dense, sparse, balance, bridge in zip(
        dense_modules, sparse_modules, balance_events, bridge_events
    ):
        event_total += dense * 41 + sparse * 37 + balance + bridge
        mapping_total += dense * 12 + sparse * 11
        cumulative_events.append(event_total)
        cumulative_mappings.append(mapping_total)
    result = {
        "cumulative_events": cumulative_events,
        "cumulative_mappings": cumulative_mappings,
        "schema_status_cumulative": [0, 5, 16, 39],
        "schema_status_new": [0, 5, 11, 23],
    }
    if result["cumulative_events"] != [123, 250, 500, 996] or result[
        "cumulative_mappings"
    ] != [36, 71, 142, 285]:
        raise AssertionError("symbolic source expansion changed")
    return result


def _valve_be(truths: tuple[int, ...]) -> Counter[tuple[int, str]]:
    result: Counter[tuple[int, str]] = Counter()
    for truth in truths:
        for mode in range(4):
            result[(mode, "RUN_STABLE" if mode == truth else "RUN_TRIPPED")] += 1
    return result


def valve_balance_goldens() -> dict[str, Any]:
    cases: list[dict[str, Any]] = []
    action_only_counts = [0, 0, 0, 0]
    for mu in range(4):
        local = tuple(mode for mode in range(4) if mode != mu)
        authentic = _valve_be(local + (mu,))
        twin = _valve_be(tuple(tau_v(mode) for mode in local + (mu,)))
        if authentic != twin:
            raise AssertionError("four-mode valve balance marginal differs")
        stable_by_mode = [authentic[(mode, "RUN_STABLE")] for mode in range(4)]
        trip_by_mode = [authentic[(mode, "RUN_TRIPPED")] for mode in range(4)]
        if stable_by_mode != [1, 1, 1, 1] or trip_by_mode != [3, 3, 3, 3]:
            raise AssertionError("valve balance is not one-stable/three-trip")
        for _ in permutations(local):
            action_only_counts[mu] += 1
        cases.append(
            {
                "mu": mu,
                "stable_by_mode": stable_by_mode,
                "trip_by_mode": trip_by_mode,
            }
        )
    if action_only_counts != [6, 6, 6, 6]:
        raise AssertionError("action-only posterior is not exactly uniform")
    return {"action_only_integer_masses": action_only_counts, "cases": cases}


def p_four_way_golden() -> dict[str, Any]:
    base = make_target(0, 0)
    pair = next(iter(useful_pairs(base)))
    return evaluate_p_atoms(compile_p_atoms(base, retain_grammar=False), pair)


def compile_p_atoms(
    base: TargetSpec, retain_grammar: bool
) -> list[tuple[TargetSpec, int]]:
    """Compile fixed accepted-target atoms; the flag exists only for M7."""

    truths = (base.valve_truth,) if retain_grammar else range(4)
    return [(replace(base, valve_truth=truth), 1) for truth in truths]


def evaluate_p_atoms(
    atoms: list[tuple[TargetSpec, int]], pair: tuple[int, int]
) -> dict[str, Any]:
    public_hashes: set[str] = set()
    success_matrix: list[list[int]] = []
    weights: list[int] = []
    for completion, weight in atoms:
        public_hashes.add(
            hashlib.sha256(canonical_bytes(target_public_record(completion))).hexdigest()
        )
        row: list[int] = []
        for guessed_mode in range(4):
            trace = execute(completion, canonical_plan(pair, guessed_mode))
            row.append(int(trace[-1].state.success))
        if sum(row) != 1:
            raise AssertionError("P completion does not have exactly one successful mode")
        success_matrix.append(row)
        weights.append(weight)
    if len(public_hashes) != 1:
        raise AssertionError("P completion changed target-visible bytes")
    total_weight = sum(weights)
    value = max(
        Fraction(
            sum(weight * row[mode] for weight, row in zip(weights, success_matrix)),
            total_weight,
        )
        for mode in range(4)
    )
    return {
        "integer_masses": weights,
        "optimal_value": [value.numerator, value.denominator],
        "success_matrix": success_matrix,
        "visible_sha256": next(iter(public_hashes)),
    }


def validate_p_completion(golden: dict[str, Any]) -> bool:
    matrix = golden.get("success_matrix")
    return (
        golden.get("integer_masses") == [1, 1, 1, 1]
        and golden.get("optimal_value") == [1, 4]
        and matrix == [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]
        and isinstance(golden.get("visible_sha256"), str)
    )


def validate_j_spec(spec: TargetSpec) -> bool:
    if spec.provenance.count("OLD") != 2 or spec.provenance.count("RECENT") != 2:
        return False
    old_codes = {spec.transforms[index] for index, age in enumerate(spec.provenance) if age == "OLD"}
    recent_codes = {spec.transforms[index] for index, age in enumerate(spec.provenance) if age == "RECENT"}
    if old_codes not in ({0, 1}, {2, 3}) or recent_codes not in ({0, 1}, {2, 3}) or old_codes == recent_codes:
        return False
    pairs = useful_pairs(spec)
    return len(pairs) == 1 and {
        spec.provenance[index] for index in next(iter(pairs))
    } == {"OLD", "RECENT"}


def p_oracle_vector() -> dict[str, Any]:
    golden = p_four_way_golden()
    return {
        "completion_modes": ["BYPASS", "RECIRCULATE", "PULSE", "DIRECT"],
        "completion_weights": golden["integer_masses"],
        "schema_value": [1, 1],
        "witness_graph_value": golden["optimal_value"],
    }


def _j_target(initial: int, old_bit: int, side: int) -> TargetSpec:
    old_codes = (0, 1) if old_bit == 0 else (2, 3)
    recent_codes = (2, 3) if old_bit == 0 else (0, 1)
    codes = old_codes + recent_codes
    if side:
        codes = tuple(tau_c(code) for code in codes)
    return TargetSpec(
        initial_coolant=initial,
        transforms=codes,
        exchanger=initial ^ 3,
        valve_truth=tau_v(0) if side else 0,
        provenance=("OLD", "OLD", "RECENT", "RECENT"),
        handles=draw_target_handles(stage_a_target_tape(), 4),
    )


def j_cut_goldens() -> tuple[list[dict[str, Any]], Counters]:
    rows: list[dict[str, Any]] = []
    counters = Counters()
    for initial in range(4):
        for old_bit in range(2):
            for side in range(2):
                base = _j_target(initial, old_bit, side)
                if not validate_j_spec(base):
                    raise AssertionError("J inventory/provenance validator failed")
                pair_set = useful_pairs(base)
                if len(pair_set) != 1:
                    raise AssertionError("J base does not have one pair")
                pair = next(iter(pair_set))
                if {base.provenance[index] for index in pair} != {"OLD", "RECENT"}:
                    raise AssertionError("J pair is not connected old-to-new")
                base_plan = minimum_depth(base)
                counters.states += base_plan.state_count
                counters.transitions += base_plan.transition_count
                if base_plan.minimum_depth != 9:
                    raise AssertionError("J base minimum is not nine")
                correct_old = next(
                    index for index in pair if base.provenance[index] == "OLD"
                )
                statuses_remove_old = list(base.statuses)
                statuses_remove_old[correct_old] = ITEM_ABSENT
                statuses_recent_only = tuple(
                    ITEM_LOCKER if age == "RECENT" else ITEM_ABSENT
                    for age in base.provenance
                )
                statuses_old_only = tuple(
                    ITEM_LOCKER if age == "OLD" else ITEM_ABSENT
                    for age in base.provenance
                )
                variants = (
                    replace(
                        base,
                        initial_statuses=tuple(statuses_remove_old),
                        necessity_mask=1,
                    ),
                    replace(
                        base,
                        forbidden_mask=1 << correct_old,
                        necessity_mask=2,
                    ),
                    replace(
                        base,
                        initial_statuses=statuses_recent_only,
                        necessity_mask=3,
                    ),
                    replace(
                        base,
                        initial_statuses=statuses_old_only,
                        necessity_mask=4,
                    ),
                )
                variant_results: list[dict[str, Any]] = []
                for variant_index, variant in enumerate(variants, 1):
                    if necessity_disposition(initial_state(variant)) != (
                        f"REGISTERED_CUT_{variant_index}"
                    ):
                        raise AssertionError("J necessity mask lost its certificate identity")
                    result = minimum_depth(variant)
                    counters.states += result.state_count
                    counters.transitions += result.transition_count
                    if result.minimum_depth is not None:
                        raise AssertionError(f"J cut variant {variant_index} succeeds")
                    variant_results.append(
                        {
                            "structural_unreachable": result.structural_unreachable,
                            "variant": variant_index,
                        }
                    )
                rows.append(
                    {
                        "initial_coolant": initial,
                        "old_bit": "v" if old_bit == 0 else "i",
                        "pair": list(pair),
                        "side": "TWIN" if side else "H",
                        "variants": variant_results,
                    }
                )
    return rows, counters


def j_inventory_oracle_vector() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for initial in range(4):
        for old_bit in range(2):
            authentic = _j_target(initial, old_bit, 0)
            twin = authentic.twin()
            h_pair = next(iter(useful_pairs(authentic)))
            twin_pair = next(iter(useful_pairs(twin)))

            def named(pair: tuple[int, int], age: str) -> str:
                index = next(i for i in pair if authentic.provenance[i] == age)
                return Conditioner(authentic.transforms[index]).name

            rows.append(
                {
                    "h_old": named(h_pair, "OLD"),
                    "h_recent": named(h_pair, "RECENT"),
                    "old_bit": "v" if old_bit == 0 else "i",
                    "twin_old": named(twin_pair, "OLD"),
                    "twin_recent": named(twin_pair, "RECENT"),
                    "u": f"{initial:02b}",
                }
            )
    return rows
