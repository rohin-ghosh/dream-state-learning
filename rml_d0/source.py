"""Literal Stage-A source schedule and complete cutwise BE byte oracle."""

from __future__ import annotations

import hashlib
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Iterable

from .canonical import HANDLE_RE, canonical_bytes, coolant_object
from .rng import HandleTape, sealed_fixture_values
from .world import VALVE_NAMES, apply_conditioner, tau_c, tau_v


DESCRIPTORS = ("D00", "D01", "D10", "D11")
PHRASES = {
    "D00": "ribbed brass panel",
    "D01": "matte ceramic panel",
    "D10": "crosshatched alloy panel",
    "D11": "smooth graphite panel",
}
PUBLIC_STATE_KEYS = frozenset(
    {
        "layout", "position", "action_count", "remaining_actions", "terminal",
        "failure_kind", "goal_handle", "coolant", "inventory", "locker_items",
        "consumed_items", "loop", "valve", "run_stable", "commit_succeeded",
        "last_result_code",
    }
)
SOURCE_RESET_KEYS = frozenset(
    {"episode_handle", "bench_kind", "initial_public_state", "permitted_action_count"}
)
PUBLIC_EVENT_KEYS = frozenset(
    {"action", "event_handle", "result_code", "state_delta", "text"}
)
CARTRIDGE_KEYS = frozenset(
    {
        "instance_handle", "conditioner_family", "module_family",
        "module_descriptor", "module_phrase", "location", "consumed",
    }
)


@dataclass(frozen=True)
class LogicalRow:
    era: int
    module_id: int
    family_module_id: int
    descriptor: str
    family_descriptor: str
    bench_kind: str
    action_kind: str
    relation_kind: str
    reset_start: int
    state_start: int
    mode: int
    truth: int
    conditioner: int
    bypass: bool
    episode_key: str
    step_number: int = 1
    permitted_action_count: int = 1

    @property
    def draw_prefixes(self) -> tuple[str, ...]:
        if self.step_number == 2:
            return ("EV",)
        common = ("EP", "GO", "CO", "LO", "VA")
        inventory = ("CI",) if self.action_kind == "APPLY" else ()
        return common + inventory + ("EV",)


@dataclass(frozen=True)
class ModuleHandles:
    module: str
    conditioners: tuple[str, str, str, str]
    valves: tuple[str, str, str, str]
    exchangers: tuple[str, str, str, str]


def _module_rows(
    era: int, module_id: int, descriptor: str, dense: bool, sparse_mu: int = 0
) -> list[LogicalRow]:
    def episode(label: str) -> str:
        return f"E{era}:M{module_id}:{label}"

    rows = [
        LogicalRow(
            era, module_id, module_id, descriptor, descriptor,
            "CONDITIONER_BENCH", "OBSERVE", "SELF", 0, 0, -1, -1, -1,
            False, episode("OBSERVE")
        )
    ]
    for code in range(4):
        for start in (0, 3):
            rows.append(
                LogicalRow(
                    era, module_id, module_id, descriptor, descriptor,
                    "CONDITIONER_BENCH", "APPLY", "SELF", start, start,
                    -1, -1, code, False, episode(f"CF{code}:{start}")
                )
            )
    for truth in range(4):
        if not dense and truth == sparse_mu:
            continue
        for mode in range(4):
            rows.append(
                LogicalRow(
                    era, module_id, module_id, descriptor, descriptor,
                    "VALVE_BENCH", "RUN", "SELF", 0, 0, mode, truth, -1,
                    False, episode(f"VF{truth}:{mode}")
                )
            )
    for truth in range(4):
        for start in range(4):
            rows.append(
                LogicalRow(
                    era, module_id, module_id, descriptor, descriptor,
                    "EXCHANGER_BENCH", "RUN", "SELF", start, start, -1,
                    truth, -1, True, episode(f"XF{truth}:{start}")
                )
            )
    if len(rows) != (41 if dense else 37):
        raise AssertionError("module row expansion cardinality changed")
    return rows


def _balance_rows(era: int, module_id: int, mu: int) -> list[LogicalRow]:
    return [
        LogicalRow(
            era, module_id, module_id, "D11", "D11", "VALVE_BENCH", "RUN",
            "SELF", 0, 0, mode, mu, -1, False,
            f"E{era}:BALANCE:{mode}"
        )
        for mode in range(4)
    ]


def _bridge_rows(
    era: int,
    old_module_id: int,
    old_descriptor: str,
    recent_module_id: int,
    recent_descriptor: str,
) -> list[LogicalRow]:
    rows: list[LogicalRow] = []
    for trial, code in enumerate((0, 1)):
        after_apply = apply_conditioner(0, code)
        episode_key = f"E{era}:BRIDGE:{trial}"
        rows.append(
            LogicalRow(
                era, recent_module_id, old_module_id, recent_descriptor,
                old_descriptor, "EXCHANGER_BENCH", "APPLY", "OLD_TO_RECENT",
                0, 0, -1, 0, code, True, episode_key, 1, 2
            )
        )
        rows.append(
            LogicalRow(
                era, recent_module_id, recent_module_id, recent_descriptor,
                recent_descriptor, "EXCHANGER_BENCH", "RUN", "OLD_TO_RECENT",
                0, after_apply, -1, 0, code, True, episode_key, 2, 2
            )
        )
    return rows


def expand_logical_schedule(
    balance_mode_count: int = 4,
) -> tuple[tuple[LogicalRow, ...], tuple[int, ...], tuple[int, ...]]:
    """Expand exact K0..K3 rows; two-mode is the isolated M2 mutant."""

    if balance_mode_count not in {2, 4}:
        raise ValueError("balance mode count must be two or four")
    rows: list[LogicalRow] = []
    cumulative: list[int] = []
    cumulative_mappings: list[int] = []
    module_id = 0
    dense_counts = (3, 2, 5, 11)
    mapping_total = 0
    for era, dense_count in enumerate(dense_counts):
        if era == 0:
            dense_descriptors = ("D00", "D01", "D10")
        else:
            dense_descriptors = tuple(
                ["D11"]
                + [DESCRIPTORS[index % 4] for index in range(dense_count - 1)]
            )
        first_dense_id = module_id
        for descriptor in dense_descriptors:
            rows.extend(_module_rows(era, module_id, descriptor, True))
            module_id += 1
            mapping_total += 12
        if era:
            mu = era % 4
            rows.extend(_module_rows(era, module_id, "D11", False, mu))
            module_id += 1
            mapping_total += 11
            balance = _balance_rows(era, first_dense_id, mu)
            if balance_mode_count == 2:
                permitted = {mu, tau_v(mu)}
                balance = [row for row in balance if row.mode in permitted]
            rows.extend(balance)
            rows.extend(_bridge_rows(era, 0, "D00", first_dense_id, "D11"))
        cumulative.append(len(rows))
        cumulative_mappings.append(mapping_total)
    expected_events = (
        (123, 250, 500, 996)
        if balance_mode_count == 4
        else (123, 248, 496, 990)
    )
    if tuple(cumulative) != expected_events:
        raise AssertionError("literal source schedule count changed")
    if tuple(cumulative_mappings) != (36, 71, 142, 285):
        raise AssertionError("literal mapping count changed")
    return tuple(rows), tuple(cumulative), tuple(cumulative_mappings)


def _allocate_modules(rows: Iterable[LogicalRow]) -> dict[int, ModuleHandles]:
    module_ids = sorted({row.module_id for row in rows} | {row.family_module_id for row in rows})
    prefixes = tuple(
        prefix
        for _ in module_ids
        for prefix in ("MF", "CF", "CF", "CF", "CF", "VF", "VF", "VF", "VF", "XF", "XF", "XF", "XF")
    )
    tape = HandleTape(sealed_fixture_values("source-persistent-ledger", prefixes))
    result: dict[int, ModuleHandles] = {}
    for module_id in module_ids:
        result[module_id] = ModuleHandles(
            tape.draw("MF"),
            tuple(tape.draw("CF") for _ in range(4)),  # type: ignore[arg-type]
            tuple(tape.draw("VF") for _ in range(4)),  # type: ignore[arg-type]
            tuple(tape.draw("XF") for _ in range(4)),  # type: ignore[arg-type]
        )
    if tape.remaining:
        raise AssertionError("persistent source tape not consumed")
    return result


def _event_tape(rows: Iterable[LogicalRow]) -> HandleTape:
    prefixes = tuple(prefix for row in rows for prefix in row.draw_prefixes)
    return HandleTape(sealed_fixture_values("source-episode-event-ledger", prefixes))


def _cartridge(
    instance: str, family: str, module: str, descriptor: str
) -> dict[str, Any]:
    return {
        "conditioner_family": family,
        "consumed": False,
        "instance_handle": instance,
        "location": "INVENTORY",
        "module_descriptor": descriptor,
        "module_family": module,
        "module_phrase": PHRASES[descriptor],
    }


def _initial_public_state(
    row: LogicalRow,
    handles: ModuleHandles,
    family_handles: ModuleHandles,
    episode_handles: dict[str, str],
) -> dict[str, Any]:
    family = family_handles.conditioners[row.conditioner] if row.action_kind == "APPLY" else ""
    inventory = (
        [_cartridge(episode_handles["cartridge"], family, family_handles.module, row.family_descriptor)]
        if row.action_kind == "APPLY" else []
    )
    exchanger_family = handles.exchangers[row.truth] if row.truth >= 0 and row.bench_kind == "EXCHANGER_BENCH" else handles.exchangers[0]
    valve_family = handles.valves[row.truth] if row.truth >= 0 and row.bench_kind == "VALVE_BENCH" else handles.valves[0]
    return {
        "action_count": 0,
        "commit_succeeded": False,
        "consumed_items": [],
        "coolant": {
            "handle": episode_handles["coolant"],
            **coolant_object(row.reset_start),
            "outlet_temperature": "UNKNOWN",
            "pressure": "IDLE",
        },
        "failure_kind": "NONE",
        "goal_handle": episode_handles["goal"],
        "inventory": inventory,
        "last_result_code": "NONE",
        "layout": row.bench_kind,
        "locker_items": [],
        "loop": {
            "certified_bypass": row.bypass,
            "exchanger_family": exchanger_family,
            "handle": episode_handles["loop"],
            "module_descriptor": row.descriptor,
            "module_family": handles.module,
        },
        "position": "PLANT",
        "remaining_actions": row.permitted_action_count,
        "run_stable": False,
        "terminal": False,
        "valve": {
            "handle": episode_handles["valve"],
            "mode": "UNSET" if row.mode < 0 else VALVE_NAMES[row.mode],
            "valve_family": valve_family,
        },
    }


def _draw_episode(row: LogicalRow, tape: HandleTape) -> dict[str, str]:
    handles = {
        "episode": tape.draw("EP"),
        "goal": tape.draw("GO"),
        "coolant": tape.draw("CO"),
        "loop": tape.draw("LO"),
        "valve": tape.draw("VA"),
        "cartridge": "",
    }
    if row.action_kind == "APPLY":
        handles["cartridge"] = tape.draw("CI")
    return handles


def _normalization_map(
    row: LogicalRow,
    modules: dict[int, ModuleHandles],
    episode: dict[str, str],
    event_handle: str,
) -> dict[str, str]:
    result = {value: value[:2] for value in (*episode.values(), event_handle) if value}
    reset_module = modules[row.module_id]
    family_module = modules[row.family_module_id]
    result[reset_module.module] = f"MF:{'RECENT' if row.relation_kind == 'OLD_TO_RECENT' else row.relation_kind}:{row.descriptor}"
    result[family_module.module] = f"MF:{'OLD' if row.relation_kind == 'OLD_TO_RECENT' else row.relation_kind}:{row.family_descriptor}"
    for prefix, values, descriptor, role in (
        ("CF", family_module.conditioners, row.family_descriptor, "OLD" if row.relation_kind == "OLD_TO_RECENT" else row.relation_kind),
        ("VF", reset_module.valves, row.descriptor, "RECENT" if row.relation_kind == "OLD_TO_RECENT" else row.relation_kind),
        ("XF", reset_module.exchangers, row.descriptor, "RECENT" if row.relation_kind == "OLD_TO_RECENT" else row.relation_kind),
    ):
        for value in values:
            result[value] = f"{prefix}:{role}:{descriptor}"
    if row.relation_kind == "OLD_TO_RECENT":
        old_module = modules[0]
        result[old_module.module] = "MF:OLD:D00"
        for value in old_module.conditioners:
            result[value] = "CF:OLD:D00"
    return result


def _expand_side(
    rows: tuple[LogicalRow, ...], twin: bool
) -> list[tuple[dict[str, Any], dict[str, Any], dict[str, str]]]:
    modules = _allocate_modules(rows)
    tape = _event_tape(rows)
    episodes: dict[str, tuple[dict[str, str], dict[str, Any]]] = {}
    expanded: list[tuple[dict[str, Any], dict[str, Any], dict[str, str]]] = []
    for row in rows:
        if row.step_number == 1:
            episode_handles = _draw_episode(row, tape)
            state = _initial_public_state(
                row, modules[row.module_id], modules[row.family_module_id], episode_handles
            )
            reset = {
                "bench_kind": row.bench_kind,
                "episode_handle": episode_handles["episode"],
                "initial_public_state": state,
                "permitted_action_count": row.permitted_action_count,
            }
            episodes[row.episode_key] = (episode_handles, reset)
        else:
            episode_handles, reset = episodes[row.episode_key]
        event_handle = tape.draw("EV")
        conditioner = tau_c(row.conditioner) if twin and row.conditioner >= 0 else row.conditioner
        truth = tau_v(row.truth) if twin and row.bench_kind == "VALVE_BENCH" else row.truth
        family_module = modules[row.family_module_id]
        reset_module = modules[row.module_id]
        if row.action_kind == "OBSERVE":
            action = {"action_kind": "OBSERVE", "arguments": {"object_or_site": reset_module.module}}
            result_code = "OBSERVED"
            text = f"The {PHRASES[row.descriptor]} service board is visible."
            coolant_after, stable, terminal, failure = row.state_start, False, False, "NONE"
        elif row.action_kind == "APPLY":
            action = {"action_kind": "APPLY", "arguments": {"cartridge": episode_handles["cartridge"], "coolant": episode_handles["coolant"]}}
            result_code = "APPLIED"
            coolant_after = apply_conditioner(row.state_start, conditioner)
            public = coolant_object(coolant_after)
            text = f"The coolant gauge reads viscosity {public['viscosity']}; inhibitor {public['inhibitor']}."
            stable, terminal, failure = False, False, "NONE"
        else:
            action = {"action_kind": "RUN", "arguments": {"loop": episode_handles["loop"]}}
            state_start = (
                apply_conditioner(row.reset_start, conditioner)
                if row.relation_kind == "OLD_TO_RECENT" and row.step_number == 2
                else row.state_start
            )
            stable = row.mode == truth if row.bench_kind == "VALVE_BENCH" else state_start == truth
            result_code = "RUN_STABLE" if stable else "RUN_TRIPPED"
            text = "The loop runs with stable pressure and nominal outlet temperature." if stable else "The loop trips before stabilization."
            coolant_after, terminal, failure = state_start, not stable, "NONE" if stable else "LOOP_TRIPPED"
        initial_state = reset["initial_public_state"]
        consumed = (
            [episode_handles["cartridge"]]
            if row.action_kind == "APPLY" or row.step_number == 2
            else []
        )
        state_delta = {
            **initial_state,
            "action_count": row.step_number,
            "consumed_items": consumed,
            "coolant": {
                **initial_state["coolant"],
                **coolant_object(coolant_after),
                "outlet_temperature": "NOMINAL" if stable else "UNKNOWN",
                "pressure": "STABLE" if stable else "IDLE",
            },
            "failure_kind": failure,
            "inventory": [],
            "last_result_code": result_code,
            "remaining_actions": row.permitted_action_count - row.step_number,
            "run_stable": stable,
            "terminal": terminal,
        }
        event = {
            "action": action,
            "event_handle": event_handle,
            "result_code": result_code,
            "state_delta": state_delta,
            "text": text,
        }
        norm = _normalization_map(row, modules, episode_handles, event_handle)
        expanded.append((reset, event, norm))
    if tape.remaining:
        raise AssertionError("source episode/event tape not consumed")
    return expanded


def validate_source_records(
    expanded: list[tuple[dict[str, Any], dict[str, Any], dict[str, str]]]
) -> bool:
    for reset, event, _ in expanded:
        if frozenset(reset) != SOURCE_RESET_KEYS or frozenset(event) != PUBLIC_EVENT_KEYS:
            return False
        initial = reset["initial_public_state"]
        successor = event["state_delta"]
        if frozenset(initial) != PUBLIC_STATE_KEYS or frozenset(successor) != PUBLIC_STATE_KEYS:
            return False
        for state in (initial, successor):
            if state["coolant"]["pressure"] not in {"IDLE", "STABLE"}:
                return False
            if state["coolant"]["outlet_temperature"] not in {"UNKNOWN", "NOMINAL"}:
                return False
            if any(frozenset(item) != CARTRIDGE_KEYS for item in state["inventory"] + state["locker_items"]):
                return False
        canonical_bytes(reset)
        canonical_bytes(event)
    return True


def _normalize(value: Any, mapping: dict[str, str]) -> Any:
    if isinstance(value, dict):
        return {key: _normalize(item, mapping) for key, item in value.items()}
    if isinstance(value, list):
        return [_normalize(item, mapping) for item in value]
    if isinstance(value, str) and HANDLE_RE.fullmatch(value):
        return mapping[value]
    return value


def _be(reset: dict[str, Any], event: dict[str, Any], mapping: dict[str, str]) -> bytes:
    return canonical_bytes(
        {"event": _normalize(event, mapping), "reset": _normalize(reset, mapping)}
    )


def _handles_in(value: Any) -> set[str]:
    if isinstance(value, dict):
        return set().union(*(_handles_in(item) for item in value.values()), set())
    if isinstance(value, list):
        return set().union(*(_handles_in(item) for item in value), set())
    if isinstance(value, str) and HANDLE_RE.fullmatch(value):
        return {value} if value[:2] in {"EP", "GO", "CO", "LO", "VA", "CI", "EV"} else set()
    return set()


def valve_mu_be_goldens() -> list[dict[str, Any]]:
    """Byte-compare dense+sparse+balance for every omitted valve truth."""

    result: list[dict[str, Any]] = []
    for mu in range(4):
        rows = tuple(
            _module_rows(1, 0, "D11", True)
            + _module_rows(1, 1, "D11", False, mu)
            + _balance_rows(1, 0, mu)
        )
        h = _expand_side(rows, False)
        twin = _expand_side(rows, True)
        h_bytes = sorted(
            _be(*item)
            for row, item in zip(rows, h)
            if row.bench_kind == "VALVE_BENCH" and row.action_kind == "RUN"
        )
        twin_bytes = sorted(
            _be(*item)
            for row, item in zip(rows, twin)
            if row.bench_kind == "VALVE_BENCH" and row.action_kind == "RUN"
        )
        if h_bytes != twin_bytes:
            raise AssertionError(f"mu={mu} complete valve BE differs")
        result.append(
            {
                "be_equal": True,
                "be_sha256": hashlib.sha256(b"".join(h_bytes)).hexdigest(),
                "mu": mu,
                "row_count": len(h_bytes),
            }
        )
    return result


def validate_complete_be(
    balance_mode_count: int = 4,
) -> dict[str, Any]:
    rows, cumulative, cumulative_mappings = expand_logical_schedule(balance_mode_count)
    h = _expand_side(rows, False)
    twin = _expand_side(rows, True)
    if not validate_source_records(h) or not validate_source_records(twin):
        raise AssertionError("source record schema is not closed")
    cut_digests: list[str] = []
    equality: list[bool] = []
    for end in cumulative:
        h_groups: dict[tuple[int, str, str, str], list[bytes]] = defaultdict(list)
        twin_groups: dict[tuple[int, str, str, str], list[bytes]] = defaultdict(list)
        for row, h_item, twin_item in zip(rows[:end], h[:end], twin[:end]):
            key = (row.era, row.bench_kind, row.action_kind, row.relation_kind)
            h_groups[key].append(_be(*h_item))
            twin_groups[key].append(_be(*twin_item))
        same = set(h_groups) == set(twin_groups) and all(
            sorted(h_groups[key]) == sorted(twin_groups[key]) for key in h_groups
        )
        equality.append(same)
        vector = [
            {"group": list(key), "multiset_sha256": hashlib.sha256(b"".join(sorted(h_groups[key]))).hexdigest(), "row_count": len(h_groups[key])}
            for key in sorted(h_groups)
        ]
        cut_digests.append(hashlib.sha256(canonical_bytes(vector)).hexdigest())
    bridge_pairs: list[dict[str, Any]] = []
    bridge_trial_handle_sets: list[set[str]] = []
    for index, row in enumerate(rows):
        if row.relation_kind == "OLD_TO_RECENT" and row.step_number == 1:
            next_row = rows[index + 1]
            if next_row.episode_key != row.episode_key or next_row.step_number != 2:
                raise AssertionError("bridge episode adjacency changed")
            reset_a, event_a, _ = h[index]
            reset_b, event_b, _ = h[index + 1]
            initial_a = reset_a["initial_public_state"]
            initial_b = reset_b["initial_public_state"]
            shared = reset_a == reset_b and all(
                initial_a[key] == initial_b[key]
                for key in ("goal_handle", "coolant", "loop", "valve")
            )
            trial_handles = _handles_in(reset_a) | _handles_in(event_a) | _handles_in(event_b)
            bridge_trial_handle_sets.append(trial_handles)
            bridge_pairs.append(
                {
                    "episode_key": row.episode_key,
                    "result_codes": [event_a["result_code"], event_b["result_code"]],
                    "twin_result_codes": [twin[index][1]["result_code"], twin[index + 1][1]["result_code"]],
                    "shared_within_trial": shared,
                    "step_action_counts": [event_a["state_delta"]["action_count"], event_b["state_delta"]["action_count"]],
                    "step_remaining_actions": [event_a["state_delta"]["remaining_actions"], event_b["state_delta"]["remaining_actions"]],
                }
            )
    distinct_across = all(
        not (left & right)
        for index, left in enumerate(bridge_trial_handle_sets)
        for right in bridge_trial_handle_sets[index + 1 :]
    )
    return {
        "bridge_distinct_across_trials": distinct_across,
        "bridge_shared_within_trial": bridge_pairs,
        "cumulative_mappings": list(cumulative_mappings),
        "cutwise_be_equal": equality,
        "cutwise_be_sha256": cut_digests,
        "literal_event_counts": list(cumulative),
    }


def balance_action_only_masses(mu: int, balance_mode_count: int = 4) -> list[int]:
    if mu not in range(4) or balance_mode_count not in {2, 4}:
        raise ValueError("invalid balance mutant")
    modes = range(4) if balance_mode_count == 4 else (mu, tau_v(mu))
    masses = [0, 0, 0, 0]
    # Six local orderings are the only non-common factor in the registered
    # metadata/selected-handle enumeration.
    for mode in modes:
        masses[mode] += 6
    return masses


def validate_balance_source(result: dict[str, Any], masses: list[int]) -> bool:
    return (
        result["literal_event_counts"] == [123, 250, 500, 996]
        and result["cumulative_mappings"] == [36, 71, 142, 285]
        and result["cutwise_be_equal"] == [True, True, True, True]
        and masses == [6, 6, 6, 6]
    )


def complete_be_goldens() -> dict[str, Any]:
    result = validate_complete_be(4)
    if result["cutwise_be_equal"] != [True, True, True, True]:
        raise AssertionError("complete cutwise BE multiset mismatch")
    if not all(row["shared_within_trial"] for row in result["bridge_shared_within_trial"]):
        raise AssertionError("bridge actions do not share their trial reset")
    if not result["bridge_distinct_across_trials"]:
        raise AssertionError("bridge trials reuse a reset handle")
    if len(result["bridge_shared_within_trial"]) != 6:
        raise AssertionError("three eras must contain two bridge trials each")
    for pair_index, row in enumerate(result["bridge_shared_within_trial"]):
        trial = pair_index % 2
        expected_h = ["APPLIED", "RUN_STABLE" if trial == 0 else "RUN_TRIPPED"]
        expected_twin = ["APPLIED", "RUN_TRIPPED" if trial == 0 else "RUN_STABLE"]
        if row["result_codes"] != expected_h or row["twin_result_codes"] != expected_twin:
            raise AssertionError("source bridge outcome swap changed")
        if row["step_action_counts"] != [1, 2] or row["step_remaining_actions"] != [1, 0]:
            raise AssertionError("source bridge step accounting changed")
    result["all_mu_complete_be"] = valve_mu_be_goldens()
    return result
