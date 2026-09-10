"""Subject-independent vectors and executable Stage-A mutation kills."""

from __future__ import annotations

import hashlib
import copy
from dataclasses import replace
from typing import Any

from .bayes import (
    first_accept_toy_goldens,
    heterogeneous_posterior_solver,
    validate_attempt_solver,
    validate_heterogeneous_solver,
)
from .canonical import canonical_bytes, canonical_goldens
from .planner import QUOTIENT_FIELDS, minimum_depth, quotient_deletion_witnesses
from .rng import (
    STAGE_A_TARGET_TAPE_VALUES,
    handle_metamorphic_goldens,
    injected_handle_allocator,
    validate_handle_allocator,
)
from .source import (
    balance_action_only_masses,
    validate_balance_source,
    validate_complete_be,
)
from .targets import (
    bridge_goldens,
    bridge_oracle_vectors,
    j_inventory_oracle_vector,
    make_target,
    p_four_way_golden,
    source_count_golden,
    target_oracle_vectors,
    validate_bridge_rows,
    bridge_validation_errors,
    compile_p_atoms,
    evaluate_p_atoms,
    validate_j_spec,
    validate_p_completion,
    _j_target,
)
from .world import TargetHandles, apply_conditioner, target_public_record, tau_c, tau_v, useful_pairs


EXPECTED_VECTOR_DIGESTS = {
    "conditioner_table": "316aac145f65bd5d9362e03a6fca1338a662cc0843f43e8fb96badadffd4c944",
    "valve_table": "4d836dd079900c096afdef06d32fc09711f494f5126f0407a5d021793e92d5ac",
    "nw_target_00": "e422c5cc4bdf893308b3e260553e5a665948ba5f34c4ac8294365f861d54ee9a",
    "bridge_table": "f096c7ca5d2f4b8cf614963ec7fe4a997c8d757057c89ca10bf494b6fa3d5b8a",
    "bridge_result": "c9c9d05dda01d0f8bdc7d09b73d4ea99020039d2a135b67c5fba0e4ab554ff64",
    "source_counts": "a5860239f79a5f97b84f82b758e5fa242c9932a0a22d69f441fce68407a6335c",
    "p_atoms": "45e104c62cca1d3ec115ce3e2fc20465e03cca3e6016d7da92dd9d9a668fc917",
    "j_inventory": "8593c0f7b57d01c59f30eb074353f6f988b23594bf6e25618ef0363b20edbb4b",
    "first_accept": "8ba883f19c7c6fee04e42c9bc64488ef9359a65e684c53799a74253fab08d704",
    "quotient_fields": "927ae08326f7341dc37db6a5798b7d8d8224beda8f6ce6b92e571f65457b1aca",
    "recall_goal_high_lean": "61ce382efad86108f7708d506d6ef7d447b26ffb713e64e46b22b9cb0504ec8b",
    "recall_goal_low_rich": "ed4e557cac54ab2cd1a2d08aebb9b95b0dbffbc98f58a3d5e966d2cf66f30f8d",
}


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def actual_vector_digests() -> dict[str, str]:
    target = target_oracle_vectors()
    bridge = bridge_oracle_vectors()
    from .targets import p_oracle_vector

    canonical = canonical_goldens()
    actual = {
        "conditioner_table": digest(target["conditioner_table"]),
        "valve_table": digest(target["valve_table"]),
        "nw_target_00": digest(target["nw_target_00"]),
        "bridge_table": digest(bridge["table"]),
        "bridge_result": digest(bridge["result_vector"]),
        "source_counts": digest(source_count_golden()),
        "p_atoms": digest(p_oracle_vector()),
        "j_inventory": digest(j_inventory_oracle_vector()),
        "first_accept": digest(first_accept_toy_goldens()["oracle_vector"]),
        "quotient_fields": digest(list(QUOTIENT_FIELDS)),
        "recall_goal_high_lean": canonical[1]["sha256"],
        "recall_goal_low_rich": canonical[2]["sha256"],
    }
    if set(actual) != set(EXPECTED_VECTOR_DIGESTS):
        raise AssertionError("oracle vector key set is incomplete")
    return actual


def _wrong_twin(spec):
    return replace(
        spec,
        transforms=tuple(tau_c(code) for code in spec.transforms),
        exchanger=spec.exchanger ^ 0b10,
        valve_truth=tau_v(spec.valve_truth),
    )


def mutation_kills() -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []

    # M1: registered x->x identity is replaced by x xor 10.
    m1_failures = 0
    for initial in range(4):
        for mode in range(4):
            authentic = make_target(initial, mode)
            mutant = _wrong_twin(authentic)
            pairs = useful_pairs(mutant)
            registered = (
                len(pairs) == 1
                and not (set(next(iter(useful_pairs(authentic)))) & set(next(iter(pairs))))
                and minimum_depth(mutant).minimum_depth == 9
            )
            m1_failures += int(not registered)
    results.append({"id": "M1", "killed": m1_failures == 16, "witness_count": m1_failures})

    # M2: two exposed balance modes change both literal totals and support.
    two_mode_source = validate_complete_be(2)
    two_mode_support = balance_action_only_masses(0, 2)
    m2_survived = validate_balance_source(two_mode_source, two_mode_support)
    results.append({"id": "M2", "killed": not m2_survived, "witness_count": 2})

    # M3a: a side-derived goal handle destroys target-visible collision.
    spec = make_target(0, 0)
    twin = spec.twin()
    assert twin.handles is not None
    mutated_handles = replace(twin.handles, goal="GO00000000CF00")
    changed = replace(twin, handles=mutated_handles)
    m3a = canonical_bytes(target_public_record(spec)) != canonical_bytes(target_public_record(changed))
    results.append({"id": "M3a", "killed": m3a, "witness_count": 1})
    meta = handle_metamorphic_goldens()

    def metadata_derived_allocator(
        tape_values: tuple[str, ...], metadata: tuple[object, ...]
    ) -> tuple[str, ...]:
        values = list(injected_handle_allocator(tape_values, metadata))
        values[0] = "MF" + hashlib.sha256(canonical_bytes(list(metadata))).hexdigest()[:12].upper()
        return tuple(values)

    results.append({"id": "M3b", "killed": not validate_handle_allocator(metadata_derived_allocator), "witness_count": 2})

    # M4: all-current provenance cannot satisfy the explicit connected table.
    j_base = _j_target(0, 0, 0)
    all_current = replace(j_base, provenance=("RECENT",) * 4)
    results.append({"id": "M4", "killed": not validate_j_spec(all_current), "witness_count": 1})

    bayes = first_accept_toy_goldens()["oracle_vector"]
    def uniform_position_mutant(cap, acceptance):
        accepted = 1 - (1 - acceptance) ** cap
        return [accepted / cap for _ in range(cap)], 1 - accepted

    m5a_errors = validate_attempt_solver(uniform_position_mutant)
    results.append({"id": "M5a", "killed": bool(m5a_errors), "rejection_reasons": m5a_errors, "witness_count": len(m5a_errors)})

    def global_cap_cancellation_mutant(cap, acceptance0, acceptance1):
        del cap
        from math import gcd
        denominator = acceptance0.denominator * acceptance1.denominator
        raw = (
            acceptance0.numerator * (denominator // acceptance0.denominator),
            acceptance1.numerator * (denominator // acceptance1.denominator),
        )
        divisor = gcd(*raw)
        return raw[0] // divisor, raw[1] // divisor

    m5b_errors = validate_heterogeneous_solver(global_cap_cancellation_mutant)
    if validate_heterogeneous_solver(heterogeneous_posterior_solver):
        raise AssertionError("registered heterogeneous solver failed its oracle")
    results.append({"id": "M5b", "killed": bool(m5b_errors), "rejection_reasons": m5b_errors, "witness_count": len(m5b_errors)})
    def handle_role_mutant(tape_values: tuple[str, ...]) -> int:
        sequence = injected_handle_allocator(tape_values, ("K1", "N", 0, 0, "H"))
        return int(sequence[1] < "CF800000000000")

    substituted = list(STAGE_A_TARGET_TAPE_VALUES)
    substituted[1] = "CF000000ABCDEF"
    m5c_changed = handle_role_mutant(STAGE_A_TARGET_TAPE_VALUES) != handle_role_mutant(tuple(substituted))
    results.append({"id": "M5c", "killed": m5c_changed, "witness_count": 2})

    deletion = quotient_deletion_witnesses(spec)
    results.append({"id": "M6", "killed": len(deletion) == 9 and all(row["observable_bytes_differ"] for row in deletion), "witness_count": len(deletion)})

    p = p_four_way_golden()
    p_base = make_target(0, 0)
    p_pair = next(iter(useful_pairs(p_base)))
    p_mutant = evaluate_p_atoms(
        compile_p_atoms(p_base, retain_grammar=True), p_pair
    )
    p_reasons = []
    if p_mutant["integer_masses"] != [1, 1, 1, 1]:
        p_reasons.append("completion_weights")
    if p_mutant["optimal_value"] != [1, 4]:
        p_reasons.append("atoms_only_value")
    if len(p_mutant["success_matrix"]) != 4:
        p_reasons.append("completion_count")
    results.append({"id": "M7", "killed": not validate_p_completion(p_mutant), "rejection_reasons": p_reasons, "witness_count": len(p_reasons)})

    bridges = bridge_goldens()
    fewer = bridges[:-1]
    shared = copy.deepcopy(bridges)
    for key in tuple(shared[0]["reset_b"]):
        if key.endswith("handle"):
            shared[0]["reset_b"][key] = shared[0]["reset_a"][key]
    valve_sensitive = copy.deepcopy(bridges)
    valve_sensitive[0]["reset_a"]["certified_bypass"] = False
    m8_errors = {
        "fewer": bridge_validation_errors(fewer),
        "shared": bridge_validation_errors(shared),
        "valve_sensitive": bridge_validation_errors(valve_sensitive),
    }
    m8 = (
        "row_count" in m8_errors["fewer"]
        and any("shared_reset_object_handle" in reason for reason in m8_errors["shared"])
        and any("not_certified_bypass" in reason for reason in m8_errors["valve_sensitive"])
    )
    results.append({"id": "M8", "killed": m8, "rejection_reasons": m8_errors, "witness_count": 3})

    mutated_table = list(target_oracle_vectors()["conditioner_table"])
    mutated_table[0] = {**mutated_table[0], "r": "01"}
    results.append({"id": "M9", "killed": digest(mutated_table) != EXPECTED_VECTOR_DIGESTS["conditioner_table"], "witness_count": 1})

    if not all(row["killed"] for row in results):
        raise AssertionError("at least one required mutation survived")
    return results
