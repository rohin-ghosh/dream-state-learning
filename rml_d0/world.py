"""Closed finite RML-D0 fluid/thermal transition system."""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import IntEnum
from itertools import combinations
from typing import Any, Iterable

from .canonical import HANDLE_RE, canonical_bytes, coolant_object


class Conditioner(IntEnum):
    T00 = 0  # SET(v,0)
    T01 = 1  # SET(v,1)
    T10 = 2  # SET(i,0)
    T11 = 3  # SET(i,1)


class ValveMode(IntEnum):
    BYPASS = 0
    RECIRCULATE = 1
    PULSE = 2
    DIRECT = 3


VALVE_NAMES = tuple(mode.name for mode in ValveMode)
POSITIONS = ("DOCK", "LOCKER", "PLANT")
MEASURES = ("VISCOSITY", "INHIBITOR", "OUTLET_TEMPERATURE", "PRESSURE")
ITEM_LOCKER = 0
ITEM_INVENTORY = 1
ITEM_CONSUMED = 2
ITEM_ABSENT = 3


def tau_c(code: int) -> int:
    if code not in range(4):
        raise ValueError("conditioner code must be in 0..3")
    return code ^ 1


def tau_v(mode: int) -> int:
    if mode not in range(4):
        raise ValueError("valve mode must be in 0..3")
    return mode ^ 1


def tau_x(exchanger: int) -> int:
    """Registered exchanger twin map: the identity involution."""

    if exchanger not in range(4):
        raise ValueError("exchanger truth must be in 0..3")
    return exchanger


def apply_conditioner(coolant: int, code: int) -> int:
    if coolant not in range(4) or code not in range(4):
        raise ValueError("coolant and code must be in 0..3")
    if code < 2:
        return (coolant & 1) | (code << 1)
    return (coolant & 2) | (code - 2)


@dataclass(frozen=True, order=True)
class Action:
    kind: str
    argument: int | str | None = None

    def public_record(self, handles: "TargetHandles | None" = None) -> dict[str, Any]:
        if self.kind == "MOVE":
            arguments: dict[str, Any] = {"site": str(self.argument)}
        elif self.kind == "ACQUIRE":
            if handles is None:
                raise ValueError("ACQUIRE rendering requires injected handles")
            arguments = {"cartridge": handles.cartridges[int(self.argument)]}
        elif self.kind == "APPLY":
            if handles is None:
                raise ValueError("APPLY rendering requires injected handles")
            arguments = {
                "cartridge": handles.cartridges[int(self.argument)],
                "coolant": handles.coolant,
            }
        elif self.kind == "CONFIGURE":
            if handles is None:
                raise ValueError("CONFIGURE rendering requires injected handles")
            arguments = {"mode": VALVE_NAMES[int(self.argument)], "valve": handles.valve}
        elif self.kind == "MEASURE":
            if handles is None:
                raise ValueError("MEASURE rendering requires injected handles")
            arguments = {"coolant": handles.coolant, "public_test": str(self.argument)}
        elif self.kind == "OBSERVE":
            arguments = {"object_or_site": str(self.argument)}
        elif self.kind == "RUN":
            if handles is None:
                raise ValueError("RUN rendering requires injected handles")
            arguments = {"loop": handles.loop}
        elif self.kind == "COMMIT":
            if handles is None:
                raise ValueError("COMMIT rendering requires injected handles")
            arguments = {"goal": handles.goal}
        else:
            arguments = {}
        return {"action_kind": self.kind, "arguments": arguments}

    def tie_bytes(self, handles: "TargetHandles | None" = None) -> bytes:
        return canonical_bytes(self.public_record(handles))


@dataclass(frozen=True)
class TargetSpec:
    initial_coolant: int
    transforms: tuple[int, ...]
    exchanger: int
    valve_truth: int
    kind: str = "FIELD_LOOP"
    budget: int = 10
    initial_statuses: tuple[int, ...] | None = None
    forbidden_mask: int = 0
    provenance: tuple[str, ...] = ()
    layout_variant: int = 0
    handles: "TargetHandles | None" = None
    necessity_mask: int = 0

    def __post_init__(self) -> None:
        if self.initial_coolant not in range(4) or self.exchanger not in range(4):
            raise ValueError("coolant/exchanger must be in 0..3")
        if self.valve_truth not in range(4):
            raise ValueError("valve truth must be in 0..3")
        if not self.transforms or any(code not in range(4) for code in self.transforms):
            raise ValueError("transforms must be nonempty codes in 0..3")
        if self.kind not in {"FIELD_LOOP", "EXCHANGER_BENCH", "VALVE_BENCH"}:
            raise ValueError("invalid world kind")
        if not 1 <= self.budget <= 10:
            raise ValueError("budget must be in 1..10")
        statuses = self.statuses
        if len(statuses) != len(self.transforms):
            raise ValueError("one status is required per transform")
        if self.provenance and len(self.provenance) != len(self.transforms):
            raise ValueError("one provenance is required per transform")

    @property
    def statuses(self) -> tuple[int, ...]:
        if self.initial_statuses is None:
            return (ITEM_LOCKER,) * len(self.transforms)
        return self.initial_statuses

    def twin(self) -> "TargetSpec":
        return replace(
            self,
            transforms=tuple(tau_c(code) for code in self.transforms),
            exchanger=tau_x(self.exchanger),
            valve_truth=tau_v(self.valve_truth),
        )


@dataclass(frozen=True)
class GameState:
    position: str
    remaining: int
    coolant: int
    statuses: tuple[int, ...]
    valve_mode: int
    run_stable: bool
    terminal: bool
    failure: str
    necessity_mask: int = 0

    @property
    def success(self) -> bool:
        return self.terminal and self.run_stable and self.failure == "NONE"

    def quotient_key(self) -> tuple[Any, ...]:
        return (
            self.position,
            self.remaining,
            self.coolant,
            self.statuses,
            self.valve_mode,
            self.run_stable,
            self.terminal,
            self.failure,
            self.necessity_mask,
        )


@dataclass(frozen=True)
class TargetHandles:
    module_family: str
    conditioner_families: tuple[str, ...]
    cartridges: tuple[str, ...]
    exchanger_family: str
    valve_family: str
    loop: str
    valve: str
    coolant: str
    goal: str
    sites: tuple[str, str, str]


@dataclass(frozen=True)
class Transition:
    state: GameState
    result_code: str
    text: str


def initial_state(spec: TargetSpec) -> GameState:
    position = "PLANT" if spec.kind != "FIELD_LOOP" else "DOCK"
    return GameState(
        position=position,
        remaining=spec.budget,
        coolant=spec.initial_coolant,
        statuses=spec.statuses,
        valve_mode=-1,
        run_stable=False,
        terminal=False,
        failure="NONE",
        necessity_mask=spec.necessity_mask,
    )


def action_universe(spec: TargetSpec) -> tuple[Action, ...]:
    item_count = len(spec.transforms)
    if spec.handles is None:
        raise ValueError("closed public action universe requires injected handles")
    actions: list[Action] = [Action("MOVE", site) for site in POSITIONS]
    actions.extend(Action("ACQUIRE", index) for index in range(item_count))
    actions.extend(Action("APPLY", index) for index in range(item_count))
    actions.extend(Action("CONFIGURE", mode) for mode in range(4))
    actions.extend(
        [
            Action("RUN"),
            Action("COMMIT"),
            Action("STOP"),
            Action("OBSERVE", spec.handles.module_family),
        ]
    )
    actions.extend(Action("MEASURE", test) for test in MEASURES)
    return tuple(sorted(actions, key=lambda action: action.tie_bytes(spec.handles)))


class ActionDecodeError(ValueError):
    pass


def resolve_public_action(spec: TargetSpec, record: dict[str, Any]) -> Action:
    """Validate public handle arguments before any state-object mutation."""

    if frozenset(record) != frozenset({"action_kind", "arguments"}):
        raise ActionDecodeError("PublicAction key set mismatch")
    kind = record["action_kind"]
    arguments = record["arguments"]
    if not isinstance(kind, str) or not isinstance(arguments, dict):
        raise ActionDecodeError("malformed PublicAction")
    handles = spec.handles
    if handles is None:
        raise ActionDecodeError("target has no injected public handles")

    def exact(keys: set[str]) -> None:
        if set(arguments) != keys:
            raise ActionDecodeError("action argument key set mismatch")

    if kind == "MOVE":
        exact({"site"})
        action = Action(kind, arguments["site"])
    elif kind in {"ACQUIRE", "APPLY"}:
        exact({"cartridge"} if kind == "ACQUIRE" else {"cartridge", "coolant"})
        if kind == "APPLY" and arguments["coolant"] != handles.coolant:
            raise ActionDecodeError("unknown coolant handle")
        try:
            index = handles.cartridges.index(arguments["cartridge"])
        except (ValueError, TypeError) as exc:
            raise ActionDecodeError("unknown cartridge handle") from exc
        action = Action(kind, index)
    elif kind == "CONFIGURE":
        exact({"valve", "mode"})
        if arguments["valve"] != handles.valve or arguments["mode"] not in VALVE_NAMES:
            raise ActionDecodeError("unknown valve handle or mode")
        action = Action(kind, VALVE_NAMES.index(arguments["mode"]))
    elif kind == "MEASURE":
        exact({"coolant", "public_test"})
        if arguments["coolant"] != handles.coolant or arguments["public_test"] not in MEASURES:
            raise ActionDecodeError("unknown coolant handle or test")
        action = Action(kind, arguments["public_test"])
    elif kind == "RUN":
        exact({"loop"})
        if arguments["loop"] != handles.loop:
            raise ActionDecodeError("unknown loop handle")
        action = Action(kind)
    elif kind == "COMMIT":
        exact({"goal"})
        if arguments["goal"] != handles.goal:
            raise ActionDecodeError("unknown goal handle")
        action = Action(kind)
    elif kind == "OBSERVE":
        exact({"object_or_site"})
        if arguments["object_or_site"] not in {
            handles.module_family,
            *handles.sites,
        }:
            raise ActionDecodeError("unknown observation object/site")
        action = Action(kind, arguments["object_or_site"])
    elif kind == "STOP":
        exact(set())
        action = Action(kind)
    else:
        raise ActionDecodeError("unknown action kind")
    # The renderer must round-trip exactly; this rejects noncanonical aliases.
    if action.public_record(handles) != record:
        raise ActionDecodeError("PublicAction failed exact round trip")
    return action


def step_public(spec: TargetSpec, state: GameState, record: dict[str, Any]) -> Transition:
    try:
        action = resolve_public_action(spec, record)
    except ActionDecodeError:
        return step(spec, state, Action("__MALFORMED__"))
    return step(spec, state, action)


def _terminal(
    state: GameState, failure: str, result_code: str, text: str
) -> Transition:
    return Transition(
        replace(state, terminal=True, failure=failure),
        result_code,
        text,
    )


def step(spec: TargetSpec, state: GameState, action: Action) -> Transition:
    """Execute one syntactically closed action with no partial illegal mutation."""

    if state.terminal:
        return _terminal(
            replace(state, run_stable=False),
            "ILLEGAL",
            "ILLEGAL",
            "The maintenance attempt ends after an invalid operation.",
        )
    if state.remaining <= 0:
        return _terminal(
            state, "CAP", "CAP", "The maintenance attempt ends at the action cap."
        )
    base = replace(state, remaining=state.remaining - 1)

    def illegal() -> Transition:
        return _terminal(
            base,
            "ILLEGAL",
            "ILLEGAL",
            "The maintenance attempt ends after an invalid operation.",
        )

    if action.kind == "MOVE":
        if action.argument not in POSITIONS or action.argument == state.position:
            result = illegal()
        else:
            result = Transition(
                replace(base, position=str(action.argument)),
                "MOVED",
                f"The technician is now at {action.argument}.",
            )
    elif action.kind == "ACQUIRE":
        index = int(action.argument) if isinstance(action.argument, int) else -1
        if (
            state.position != "LOCKER"
            or spec.handles is None
            or index not in range(len(state.statuses))
            or state.statuses[index] != ITEM_LOCKER
        ):
            result = illegal()
        else:
            statuses = list(state.statuses)
            statuses[index] = ITEM_INVENTORY
            result = Transition(
                replace(base, statuses=tuple(statuses)),
                "ACQUIRED",
                f"Cartridge {spec.handles.cartridges[index]} is now in inventory.",
            )
    elif action.kind == "CONFIGURE":
        mode = int(action.argument) if isinstance(action.argument, int) else -1
        if state.position != "PLANT" or spec.handles is None or mode not in range(4):
            result = illegal()
        else:
            result = Transition(
                replace(base, valve_mode=mode),
                "CONFIGURED",
                f"Valve {spec.handles.valve} is set to {VALVE_NAMES[mode]}.",
            )
    elif action.kind == "APPLY":
        index = int(action.argument) if isinstance(action.argument, int) else -1
        if (
            state.position != "PLANT"
            or index not in range(len(state.statuses))
            or state.statuses[index] != ITEM_INVENTORY
            or spec.forbidden_mask & (1 << index)
        ):
            result = illegal()
        else:
            statuses = list(state.statuses)
            statuses[index] = ITEM_CONSUMED
            coolant = apply_conditioner(state.coolant, spec.transforms[index])
            public = coolant_object(coolant)
            result = Transition(
                replace(
                    base,
                    statuses=tuple(statuses),
                    coolant=coolant,
                ),
                "APPLIED",
                "The coolant gauge reads viscosity "
                f"{public['viscosity']}; inhibitor {public['inhibitor']}.",
            )
    elif action.kind == "RUN":
        if state.position != "PLANT":
            result = illegal()
        else:
            coolant_ok = state.coolant == spec.exchanger
            valve_ok = state.valve_mode == spec.valve_truth
            stable = (
                coolant_ok and valve_ok
                if spec.kind == "FIELD_LOOP"
                else coolant_ok
                if spec.kind == "EXCHANGER_BENCH"
                else valve_ok
            )
            if stable:
                result = Transition(
                    replace(base, run_stable=True),
                    "RUN_STABLE",
                    "The loop runs with stable pressure and nominal outlet temperature.",
                )
            else:
                result = _terminal(
                    base,
                    "LOOP_TRIPPED",
                    "RUN_TRIPPED",
                    "The loop trips before stabilization.",
                )
    elif action.kind == "COMMIT":
        if state.position == "PLANT" and state.run_stable and spec.handles is not None:
            result = _terminal(
                base,
                "NONE",
                "COMMITTED",
                f"Maintenance goal {spec.handles.goal} is complete.",
            )
        else:
            result = _terminal(
                base,
                "BAD_COMMIT",
                "BAD_COMMIT",
                "The maintenance attempt ends after an invalid commit.",
            )
    elif action.kind == "STOP":
        result = _terminal(
            replace(base, run_stable=False),
            "NONE",
            "STOPPED",
            "The maintenance attempt stops.",
        )
    elif action.kind == "OBSERVE":
        if spec.handles is None or action.argument not in {
            spec.handles.module_family,
            *spec.handles.sites,
        }:
            result = illegal()
        else:
            result = Transition(
                base,
                "OBSERVED",
                "The ribbed brass panel service board is visible.",
            )
    elif action.kind == "MEASURE":
        if action.argument not in MEASURES:
            result = illegal()
        else:
            public = coolant_object(state.coolant)
            values = {
                "VISCOSITY": public["viscosity"],
                "INHIBITOR": public["inhibitor"],
                "OUTLET_TEMPERATURE": "NOMINAL" if state.run_stable else "UNKNOWN",
                "PRESSURE": "STABLE" if state.run_stable else "IDLE",
            }
            result = Transition(
                base,
                "MEASURED",
                f"Gauge {action.argument} reads {values[str(action.argument)]}.",
            )
    else:
        result = illegal()
    return result


def execute(spec: TargetSpec, actions: Iterable[Action]) -> list[Transition]:
    state = initial_state(spec)
    transitions: list[Transition] = []
    for action in actions:
        transition = step(spec, state, action)
        transitions.append(transition)
        state = transition.state
        if state.terminal:
            break
    return transitions


def useful_pairs(spec: TargetSpec) -> frozenset[tuple[int, int]]:
    pairs: set[tuple[int, int]] = set()
    available = [
        index
        for index, status in enumerate(spec.statuses)
        if status != ITEM_ABSENT and not (spec.forbidden_mask & (1 << index))
    ]
    for left, right in combinations(available, 2):
        for order in ((left, right), (right, left)):
            coolant = spec.initial_coolant
            for index in order:
                coolant = apply_conditioner(coolant, spec.transforms[index])
            if coolant == spec.exchanger:
                pairs.add(tuple(sorted((left, right))))
    return frozenset(pairs)


def canonical_plan(pair: tuple[int, int], mode: int) -> tuple[Action, ...]:
    left, right = pair
    return (
        Action("MOVE", "LOCKER"),
        Action("ACQUIRE", left),
        Action("ACQUIRE", right),
        Action("MOVE", "PLANT"),
        Action("APPLY", left),
        Action("APPLY", right),
        Action("CONFIGURE", mode),
        Action("RUN"),
        Action("COMMIT"),
    )


def target_public_record(spec: TargetSpec) -> dict[str, Any]:
    if spec.handles is None:
        raise ValueError("target public rendering requires an injected handle tape")
    handles = spec.handles
    if len(handles.conditioner_families) != len(spec.transforms) or len(
        handles.cartridges
    ) != len(spec.transforms):
        raise ValueError("injected target handle cardinality mismatch")
    items = [
        {
            "conditioner_family": handles.conditioner_families[index],
            "consumed": False,
            "instance_handle": handles.cartridges[index],
            "location": "LOCKER",
            "module_descriptor": "D11",
            "module_family": handles.module_family,
            "module_phrase": "ribbed brass panel",
        }
        for index in range(len(spec.transforms))
        if spec.statuses[index] != ITEM_ABSENT
    ]
    initial = {
        "action_count": 0,
        "commit_succeeded": False,
        "consumed_items": [],
        "coolant": {
            "handle": handles.coolant,
            **coolant_object(spec.initial_coolant),
            "outlet_temperature": "UNKNOWN",
            "pressure": "IDLE",
        },
        "failure_kind": "NONE",
        "goal_handle": handles.goal,
        "inventory": [],
        "last_result_code": "NONE",
        "layout": "FIELD_LOOP",
        "locker_items": items,
        "loop": {
            "certified_bypass": False,
            "exchanger_family": handles.exchanger_family,
            "handle": handles.loop,
            "module_descriptor": "D11",
            "module_family": handles.module_family,
        },
        "position": "DOCK",
        "remaining_actions": spec.budget,
        "run_stable": False,
        "terminal": False,
        "valve": {
            "handle": handles.valve,
            "mode": "UNSET",
            "valve_family": handles.valve_family,
        },
    }
    return {
        "action_budget": spec.budget,
        "goal": {
            "goal_handle": handles.goal,
            "goal_kind": "STABLE_RUN_AND_COMMIT",
        },
        "initial_state": initial,
    }
