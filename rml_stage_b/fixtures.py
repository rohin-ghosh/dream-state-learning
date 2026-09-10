"""Source-bound four-side J/P selection and exact CPU information certificates."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, replace
from itertools import permutations
from typing import Any, Iterable

from rml_d0.planner import minimum_depth
from rml_d0.targets import make_target
from rml_d0.world import (
    Action,
    GameState,
    TargetHandles,
    TargetSpec,
    action_universe,
    canonical_plan,
    execute,
    initial_state,
    step,
    target_public_record,
    useful_pairs,
)

from .contract import canonical_bytes, digest
from .memory import (
    MemorySnapshot,
    PermittedSourceFacts,
    PretargetSnapshotSeal,
    SourceModuleFacts,
    build_snapshot,
    conditioner_twin_projection,
    extract_permitted_source_facts,
    valve_twin_projection,
)


@dataclass(frozen=True)
class TargetCase:
    target_id: str
    stratum: str
    side: str
    source_projection: str
    spec: TargetSpec
    pair: tuple[int, int]
    plan: tuple[Action, ...]
    public_bytes: bytes
    public_sha256: str
    decision_signature: str
    decisive_signature: str


@dataclass(frozen=True)
class SliceCertificate:
    selection_rule: str
    target_manifest_sha256: str
    none_information_classes: tuple[tuple[str, ...], ...]
    none_best_policy_success_capacity: int
    none_capacity_witness: str
    atoms_information_classes: tuple[tuple[str, ...], ...]
    atoms_best_policy_success_capacity: int
    atoms_capacity_witness: str
    atoms_guaranteed_identifiable_sides: int
    minimum_action_depths: tuple[int, ...]
    predecisive_feedback_vectors: tuple[dict[str, Any], ...]
    diagnostic_detour_vectors: tuple[dict[str, Any], ...]
    planner_enumerator_agree: bool
    ratified_atoms_zero_capacity_consistent: bool


def _shared_module(
    authentic: PermittedSourceFacts, twin: PermittedSourceFacts
) -> tuple[SourceModuleFacts, SourceModuleFacts]:
    twin_map = {module.module_family: module for module in twin.modules}
    candidates = [
        module
        for module in authentic.modules
        if module.module_family in twin_map and module.module_descriptor == "D11"
    ]
    if not candidates:
        candidates = [module for module in authentic.modules if module.module_family in twin_map]
    chosen = min(candidates, key=lambda module: module.module_family)
    return chosen, twin_map[chosen.module_family]


def _target_handles(base: TargetHandles, module: SourceModuleFacts, *, valve_family: str) -> TargetHandles:
    return TargetHandles(
        module_family=module.module_family,
        conditioner_families=module.conditioners_by_code,
        cartridges=base.cartridges,
        exchanger_family=module.exchangers_by_coolant[3],
        valve_family=valve_family,
        loop=base.loop,
        valve=base.valve,
        coolant=base.coolant,
        goal=base.goal,
        sites=base.sites,
    )


def _codes_for_public_order(
    public_order: tuple[str, str, str, str], source_order: tuple[str, str, str, str]
) -> tuple[int, int, int, int]:
    return tuple(source_order.index(family) for family in public_order)  # type: ignore[return-value]


def _case(
    target_id: str,
    stratum: str,
    side: str,
    source_projection: str,
    spec: TargetSpec,
) -> TargetCase:
    pairs = useful_pairs(spec)
    if len(pairs) != 1:
        raise AssertionError("selected target must have one useful pair")
    pair = next(iter(pairs))
    plan = canonical_plan(pair, spec.valve_truth)
    trace = execute(spec, plan)
    planner = minimum_depth(spec)
    if len(trace) != 9 or not trace[-1].state.success or planner.minimum_depth != 9:
        raise AssertionError("selected target is not an exact nine-action target")
    public = canonical_bytes(target_public_record(spec))
    return TargetCase(
        target_id,
        stratum,
        side,
        source_projection,
        spec,
        pair,
        plan,
        public,
        digest(public),
        digest([action.public_record(spec.handles) for action in plan]),
        digest([action.public_record(spec.handles) for action in plan[:7]]),
    )


def build_selected_cases(pretarget_seal: PretargetSnapshotSeal) -> dict[str, TargetCase]:
    """Select targets only after authentic/twin public-source facts are sealed."""
    if not isinstance(pretarget_seal, PretargetSnapshotSeal):
        raise ValueError("target selection requires a verified pretarget snapshot seal")
    pretarget_seal.verify()
    authentic = extract_permitted_source_facts(twin=False)
    twin = extract_permitted_source_facts(twin=True)
    p_h_source = valve_twin_projection(authentic, twin)
    p_twin_source = conditioner_twin_projection(authentic, twin)
    h_module, twin_module = _shared_module(authentic, twin)
    p_h_module = {
        module.module_family: module for module in p_h_source.modules
    }[h_module.module_family]
    p_twin_module = {
        module.module_family: module for module in p_twin_source.modules
    }[h_module.module_family]
    base = make_target(0, 0)
    if base.handles is None:
        raise AssertionError("D0 target allocator returned no handles")

    j_valve = h_module.valves_by_mode[0]
    j_handles = _target_handles(base.handles, h_module, valve_family=j_valve)
    j_h_spec = replace(
        base,
        transforms=(0, 1, 2, 3),
        exchanger=3,
        valve_truth=0,
        budget=9,
        provenance=("OLD", "OLD", "RECENT", "RECENT"),
        handles=j_handles,
    )
    j_twin_spec = replace(
        j_h_spec,
        transforms=_codes_for_public_order(
            j_handles.conditioner_families, twin_module.conditioners_by_code
        ),
        exchanger=twin_module.exchangers_by_coolant.index(j_handles.exchanger_family),
        valve_truth=twin_module.valves_by_mode.index(j_valve),
    )

    # The 2x2 source-derived binding cross reuses exactly the same public
    # family handles on all four sides.
    p_valve = h_module.valves_by_mode[0]
    p_handles = _target_handles(base.handles, h_module, valve_family=p_valve)
    p_h_spec = replace(
        base,
        transforms=(0, 1, 2, 3),
        exchanger=3,
        valve_truth=p_h_module.valves_by_mode.index(p_valve),
        budget=9,
        provenance=(),
        handles=p_handles,
    )
    p_twin_spec = replace(
        p_h_spec,
        transforms=_codes_for_public_order(
            p_handles.conditioner_families, p_twin_module.conditioners_by_code
        ),
        exchanger=p_twin_module.exchangers_by_coolant.index(p_handles.exchanger_family),
        valve_truth=p_twin_module.valves_by_mode.index(p_valve),
    )
    result = {
        case.target_id: case
        for case in (
            _case("J_H", "J", "H", "H", j_h_spec),
            _case("J_TWIN", "J", "TWIN", "FULL_TWIN", j_twin_spec),
            _case("P_H", "P", "H", "VALVE_TWIN", p_h_spec),
            _case("P_TWIN", "P", "TWIN", "CONDITIONER_TWIN", p_twin_spec),
        )
    }
    if len({case.public_bytes for case in result.values()}) != 1:
        raise AssertionError("selected four-side target bytes are not identical")
    if len({case.decision_signature for case in result.values()}) != 4:
        raise AssertionError("selected four-side decision signatures collide")
    return result


def _shortest_success_signatures(case: TargetCase) -> frozenset[str]:
    pair = case.pair
    signatures: set[str] = set()
    for acquire_order in permutations(pair):
        plant = (
            Action("APPLY", pair[0]),
            Action("APPLY", pair[1]),
            Action("CONFIGURE", case.spec.valve_truth),
        )
        for plant_order in permutations(plant):
            actions = (
                Action("MOVE", "LOCKER"),
                Action("ACQUIRE", acquire_order[0]),
                Action("ACQUIRE", acquire_order[1]),
                Action("MOVE", "PLANT"),
                *plant_order,
                Action("RUN"),
                Action("COMMIT"),
            )
            trace = execute(case.spec, actions)
            if trace[-1].state.success:
                signatures.add(digest([action.public_record(case.spec.handles) for action in actions]))
    return frozenset(signatures)


def _best_fixed_capacity(
    ids: Iterable[str], signatures: dict[str, frozenset[str]]
) -> tuple[int, str]:
    ids = tuple(ids)
    candidates = sorted(set().union(*(signatures[target_id] for target_id in ids)))
    scored = [(sum(candidate in signatures[target_id] for target_id in ids), candidate) for candidate in candidates]
    return max(scored)


def _can_succeed_from(spec: TargetSpec, start: GameState) -> bool:
    queue = deque([start])
    seen = {start.quotient_key()}
    while queue:
        state = queue.popleft()
        if state.success:
            return True
        if state.terminal or state.remaining <= 0:
            continue
        for action in action_universe(spec):
            successor = step(spec, state, action).state
            if successor.success:
                return True
            key = successor.quotient_key()
            if not successor.terminal and key not in seen:
                seen.add(key)
                queue.append(successor)
    return False


def _feedback_vectors(cases: dict[str, TargetCase]) -> tuple[dict[str, Any], ...]:
    vectors: list[dict[str, Any]] = []
    for left, right in (("J_H", "J_TWIN"), ("P_H", "P_TWIN")):
        for first, second in permutations(range(4), 2):
            prefix = (
                Action("MOVE", "LOCKER"),
                Action("ACQUIRE", first),
                Action("ACQUIRE", second),
                Action("MOVE", "PLANT"),
            )
            traces = [execute(cases[target_id].spec, prefix) for target_id in (left, right)]
            visible = [
                [(item.result_code, item.text, item.state.quotient_key()) for item in trace]
                for trace in traces
            ]
            vectors.append(
                {
                    "pair": [left, right],
                    "acquire_order": [first, second],
                    "equal_before_binding_action": visible[0] == visible[1],
                }
            )
    return tuple(vectors)


def _detour_vectors(cases: dict[str, TargetCase]) -> tuple[dict[str, Any], ...]:
    vectors: list[dict[str, Any]] = []
    for target_id, case in sorted(cases.items()):
        handles = case.spec.handles
        if handles is None:
            raise AssertionError("missing handles")
        detours = (Action("OBSERVE", handles.module_family),) + tuple(
            Action("MEASURE", measure)
            for measure in ("VISCOSITY", "INHIBITOR", "OUTLET_TEMPERATURE", "PRESSURE")
        )
        for detour in detours:
            successor = step(case.spec, initial_state(case.spec), detour).state
            vectors.append(
                {
                    "target_id": target_id,
                    "action": detour.kind + ":" + str(detour.argument),
                    "remaining": successor.remaining,
                    "successful_continuation_exists": _can_succeed_from(case.spec, successor),
                }
            )
    return tuple(vectors)


def _atoms_visible_hash(snapshot: MemorySnapshot, case: TargetCase) -> str:
    keys = sorted(public_query_anchors(case) & set(snapshot.query_universe))
    row_map = snapshot.row_map()
    return digest(b"".join(row_map[key].serialized for key in keys))


def build_slice_certificate(cases: dict[str, TargetCase] | None = None) -> SliceCertificate:
    """Enumerate actual visible information classes and lucky-policy capacities."""
    if cases is None:
        from .memory import seal_pretarget_snapshot_universe

        cases = build_selected_cases(seal_pretarget_snapshot_universe())
    ids = tuple(sorted(cases))
    signatures = {target_id: _shortest_success_signatures(cases[target_id]) for target_id in ids}
    if any(len(value) != 12 for value in signatures.values()):
        raise AssertionError("D0 shortest-path tie cardinality changed")
    public_classes: dict[str, list[str]] = {}
    for target_id in ids:
        public_classes.setdefault(cases[target_id].public_sha256, []).append(target_id)
    none_classes = tuple(tuple(values) for _, values in sorted(public_classes.items()))
    none_capacity, none_witness = _best_fixed_capacity(ids, signatures)

    authentic = extract_permitted_source_facts(twin=False)
    twin = extract_permitted_source_facts(twin=True)
    atom_snapshots = {
        "H": build_snapshot(authentic, kind="ATOMS"),
    }
    atoms_by_visible: dict[str, list[str]] = {}
    for target_id in ("P_H", "P_TWIN"):
        case = cases[target_id]
        # Both P ATOMS trajectories mount the same presealed atomic source
        # projection; the cross/schema relation is not available in this arm.
        fingerprint = _atoms_visible_hash(atom_snapshots["H"], case)
        atoms_by_visible.setdefault(fingerprint, []).append(target_id)
    atoms_classes = tuple(tuple(values) for _, values in sorted(atoms_by_visible.items()))
    capacities = [_best_fixed_capacity(group, signatures) for group in atoms_classes]
    atoms_capacity, atoms_witness = max(capacities)

    feedback = _feedback_vectors(cases)
    detours = _detour_vectors(cases)
    depths = tuple(minimum_depth(cases[key].spec).minimum_depth or -1 for key in ids)
    manifest = {
        "selection_rule": "SOURCE_SEALED_THEN_LEXICOGRAPHIC_D11_MODULE_J_MODE0_P_MODE2",
        "targets": [
            {"target_id": key, "public_sha256": cases[key].public_sha256, "decision_signature": cases[key].decision_signature}
            for key in ids
        ],
    }
    return SliceCertificate(
        manifest["selection_rule"],
        digest(manifest),
        none_classes,
        none_capacity,
        none_witness,
        atoms_classes,
        atoms_capacity,
        atoms_witness,
        0 if len(atoms_classes) == 1 and len(atoms_classes[0]) == 2 else 2,
        depths,
        feedback,
        detours,
        all(depth == 9 and len(signatures[key]) == 12 for key, depth in zip(ids, depths)),
        atoms_capacity == 0,
    )


def public_query_anchors(case: TargetCase) -> frozenset[str]:
    """Derive keys exclusively from the rendered public target."""
    public = target_public_record(case.spec)
    initial = public["initial_state"]
    module = initial["loop"]["module_family"]
    exchanger = initial["loop"]["exchanger_family"]
    valve = initial["valve"]["valve_family"]
    coolant = initial["coolant"]
    bits = (2 if coolant["viscosity"] == "HIGH" else 0) | (
        1 if coolant["inhibitor"] == "RICH" else 0
    )
    families = [item["conditioner_family"] for item in initial["locker_items"]]
    return frozenset(
        {
            f"pair:{module}:{bits:02b}:{exchanger}",
            f"exchanger:{exchanger}",
            f"valve:{valve}",
            f"schema:{module}",
            *(f"conditioner:{family}" for family in families),
        }
    )
