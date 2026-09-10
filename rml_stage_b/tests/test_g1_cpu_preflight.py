"""Six replacement acceptance tests; no model, network, or GPU calls."""

from __future__ import annotations

from dataclasses import replace
import json

from rml_d0.world import execute, resolve_public_action

from rml_stage_b.contract import (
    ALLOWED_FAILURE_CLAIM,
    ALLOWED_PASS_CLAIM,
    DECODING,
    MODEL_ID,
    MODEL_REVISION,
    OUTCOME_STATES,
    RESOURCE_CEILINGS,
    TOKENIZER_REVISION,
    build_opportunity_registry,
    build_roster,
    canonical_bytes,
    digest,
)
from rml_stage_b.fixtures import build_selected_cases, build_slice_certificate
from rml_stage_b.machine import (
    MachineContractError,
    OpportunityEvent,
    OpportunityLedger,
    RmlActionMachine,
    StepRecord,
    dispatch_one,
    operation_bytes,
)
from rml_stage_b.memory import (
    ExactMemoryService,
    MemoryContractError,
    _snapshot_body,
    assert_no_closure_residue,
    build_snapshot,
    conservative_cpu_token_count,
    equivalence_closure,
    extract_permitted_source_facts,
    masked_snapshot,
    seal_pretarget_snapshot_universe,
)
from rml_stage_b.reducer import (
    ReducerError,
    decisive_handles,
    score_frozen_trace,
    score_intervention,
)
from rml_stage_b.review import (
    ReviewApproval,
    ReviewContractError,
    validate_result_language,
    validate_two_phase_reviews,
)
from rml_stage_b.run_cpu_preflight import build_cpu_preflight
from rml_stage_b.runner import run_scripted_cpu_gate
from rml_stage_b.runtime import (
    REQUIRED_HASH_COMPONENTS,
    CanaryReceipt,
    GateResourceUsage,
    RuntimeClosure,
    RuntimeContractError,
    validate_canary_receipt,
)


def _raises(kind, fragment, fn) -> None:
    try:
        fn()
    except kind as exc:
        assert fragment in str(exc), str(exc)
    else:
        raise AssertionError(f"expected {kind.__name__}: {fragment}")


def _normalize_returns(value):
    value = json.loads(json.dumps(value))
    for record in value["history"]:
        if record["returned_row"] is not None:
            record["returned_row"] = "<AUTHORIZED_QUERIED_RETURN>"
    return value


def test_RML_G1_T01_PRETARGET_SNAPSHOT_QUERY_AND_VISIBLE_BYTE_NONINTERFERENCE():
    pretarget_seal = seal_pretarget_snapshot_universe()
    snapshots = pretarget_seal.snapshot_map()
    cases = build_selected_cases(pretarget_seal)
    _raises(
        ValueError,
        "pretarget snapshot seal",
        lambda: build_selected_cases(None),  # type: ignore[arg-type]
    )
    _raises(
        MemoryContractError,
        "seal hash mismatch",
        lambda: build_selected_cases(
            replace(pretarget_seal, manifest_sha256=digest(b"tampered-seal"))
        ),
    )
    seal_name, sealed_snapshot = pretarget_seal.entries[0]
    mutated_row = replace(
        sealed_snapshot.rows[0],
        payload={**sealed_snapshot.rows[0].payload, "forged": True},
    )
    stale_snapshot = replace(
        sealed_snapshot,
        rows=(mutated_row, *sealed_snapshot.rows[1:]),
    )
    stale_entries = tuple(
        (name, stale_snapshot if name == seal_name else snapshot)
        for name, snapshot in pretarget_seal.entries
    )
    _raises(
        MemoryContractError,
        "row serialization/integrity mismatch",
        lambda: build_selected_cases(replace(pretarget_seal, entries=stale_entries)),
    )
    _raises(
        MemoryContractError,
        "row serialization/integrity mismatch",
        lambda: ExactMemoryService(stale_snapshot),
    )

    masked = masked_snapshot(
        sealed_snapshot, (sealed_snapshot.rows[0].handle,), transform="CUT"
    )
    stale_masked = replace(masked, aliases=(*masked.aliases, ("forged", "forged")))
    _raises(
        MemoryContractError,
        "sealed hash",
        lambda: ExactMemoryService(stale_masked),
    )
    masked_mutations = (
        replace(masked, index_entries=(*masked.index_entries, ("forged", "forged"))),
        replace(masked, cache_views=(*masked.cache_views, ("forged", "forged"))),
        replace(masked, derived_views=(*masked.derived_views, ("forged", "forged"))),
        replace(masked, equivalence=(*masked.equivalence, ("forged", ("forged",)))),
        replace(masked, sham_candidate_order=tuple(reversed(masked.sham_candidate_order))),
        replace(masked, query_universe=tuple(reversed(masked.query_universe))),
        replace(masked, renderer_sha256=digest(b"forged-renderer")),
        replace(masked, tokenizer_rendering_sha256=digest(b"forged-tokenizer")),
        replace(masked, source_sha256=digest(b"forged-source")),
        replace(masked, masked_handles=(*masked.masked_handles, "forged")),
    )
    for mutation in masked_mutations:
        _raises(
            MemoryContractError,
            "snapshot",
            lambda mutation=mutation: ExactMemoryService(mutation),
        )
    assert len(snapshots) == 8
    assert len({case.public_bytes for case in cases.values()}) == 1

    # Builder API accepts source facts only.  Hidden target mutations cannot
    # influence its rows/index/query bytes because no target is an input.
    h_source = extract_permitted_source_facts(twin=False)
    sealed = build_snapshot(h_source)
    mutated = replace(cases["J_H"].spec, transforms=(3, 2, 1, 0), valve_truth=3, provenance=("X",) * 4)
    assert build_snapshot(h_source).sealed_sha256 == sealed.sealed_sha256
    assert mutated.transforms != cases["J_H"].spec.transforms
    assert cases["J_H"].public_bytes == cases["J_TWIN"].public_bytes
    _raises(MemoryContractError, "source", lambda: build_snapshot(mutated))  # type: ignore[arg-type]

    # Same exact keys always have the same condition-neutral handles/provenance.
    common_keys = set.intersection(*(set(snapshot.query_universe) for snapshot in snapshots.values()))
    for key in common_keys:
        rows = [snapshot.row_map()[key] for snapshot in snapshots.values()]
        assert len({row.handle for row in rows}) == 1
        assert len({row.public_support for row in rows}) == 1

    visible_key_lists = {
        tuple(RmlActionMachine.start(case).model_visible_value()["public_derived_query_keys"])
        for case in cases.values()
    }
    assert len(visible_key_lists) == 1
    required_prefixes = {"conditioner:", "exchanger:", "pair:", "schema:", "valve:"}
    exposed = next(iter(visible_key_lists))
    assert all(any(key.startswith(prefix) for key in exposed) for prefix in required_prefixes)

    # Prefix-conditional visible bytes differ only in the exact queried return.
    case = cases["J_H"]
    gold = snapshots["H:GOLD"]
    none = masked_snapshot(gold, [row.handle for row in gold.rows], transform="NONE")
    left, right = RmlActionMachine.start(case), RmlActionMachine.start(case)
    keys = sorted(
        key
        for key in {row.key for row in gold.rows} & set(left.allowed_keys)
        if key.startswith("valve:")
    )[:1]
    keys += [next(key for key in sorted(gold.query_universe) if key.startswith("schema:") and key in left.allowed_keys)]
    for key in keys:
        raw = operation_bytes({"kind": "READ", "key": key})
        left = left.advance(raw, ExactMemoryService(gold))
        right = right.advance(raw, ExactMemoryService(none))
        assert _normalize_returns(left.model_visible_value()) == _normalize_returns(right.model_visible_value())

    # R03 operation history is complete, not merely a kind label.  A later
    # call sees the exact prior key even when the same missing key is repeated.
    missing_key = keys[0]
    missing = RmlActionMachine.start(case)
    emitted = {"kind": "READ", "key": missing_key}
    missing = missing.advance(operation_bytes(emitted), ExactMemoryService(none))
    missing = missing.advance(operation_bytes(emitted), ExactMemoryService(none))
    missing_history = missing.model_visible_value()["history"]
    assert [row["operation"] for row in missing_history] == [emitted, emitted]
    assert all(
        json.loads(row["returned_row"])["status"] == "NOT_FOUND"
        for row in missing_history
    )
    assert all(
        canonical_bytes(row["operation"]) == canonical_bytes(emitted)
        for row in missing_history
    )
    visible_text = left.model_visible_bytes().decode("utf-8").casefold()
    for forbidden in ("target_id", "source_projection", "valve_truth", "score", "threshold", "condition_label"):
        assert forbidden not in visible_text

    # Exhaust every operation slot across every pretarget projection with an
    # identical output prefix.  Modulo the exact queried return, all complete
    # model-visible values remain byte-identical.
    all_services = [ExactMemoryService(snapshot) for snapshot in snapshots.values()]
    all_services.append(ExactMemoryService(none))
    machines = [RmlActionMachine.start(case) for _ in all_services]
    anchor_keys = [
        next(key for key in exposed if key.startswith("exchanger:")),
        next(key for key in exposed if key.startswith("pair:")),
        next(key for key in exposed if key.startswith("valve:")),
        next(key for key in exposed if key.startswith("schema:")),
    ]
    for key in anchor_keys:
        raw = operation_bytes({"kind": "READ", "key": key})
        machines = [machine.advance(raw, service) for machine, service in zip(machines, all_services)]
        normalized = [_normalize_returns(machine.model_visible_value()) for machine in machines]
        assert all(value == normalized[0] for value in normalized[1:])
    cited = decisive_handles(case, gold)
    for action in case.plan:
        raw = operation_bytes(
            {"kind": "ENV", "action": action.public_record(case.spec.handles)},
            citations=cited,
        )
        machines = [machine.advance(raw, service) for machine, service in zip(machines, all_services)]
        normalized = [_normalize_returns(machine.model_visible_value()) for machine in machines]
        assert all(value == normalized[0] for value in normalized[1:])


def test_RML_G1_T02_CLOSED_PHASE_MACHINE_AND_234_LEDGER():
    pretarget_seal = seal_pretarget_snapshot_universe()
    snapshots = pretarget_seal.snapshot_map()
    cases = build_selected_cases(pretarget_seal)
    case = cases["J_H"]
    snapshot = snapshots["H:GOLD"]
    service = ExactMemoryService(snapshot)
    anchors = sorted(case_key for case_key in RmlActionMachine.start(case).allowed_keys if case_key in snapshot.query_universe)
    keys = [
        next(key for key in anchors if key.startswith("exchanger:")),
        next(key for key in anchors if key.startswith("pair:")),
        next(key for key in anchors if key.startswith("valve:")),
        next(key for key in anchors if key.startswith("schema:")),
    ]
    machine = RmlActionMachine.start(case)
    for index, key in enumerate(keys):
        machine = machine.advance(operation_bytes({"kind": "READ", "key": key}), service)
        assert not machine.terminal
        assert machine.phase == ("ENV" if index == 3 else "READ")
    citations = decisive_handles(case, snapshot)
    for action in case.plan:
        machine = machine.advance(
            operation_bytes({"kind": "ENV", "action": action.public_record(case.spec.handles)}, citations=citations),
            service,
        )
    assert machine.terminal and machine.outcome_state == "SCIENTIFIC_VALID_SUCCESS"
    assert len(machine.records) == 13 and machine.records[3].returned_row is not None
    _raises(MachineContractError, "frozen", lambda: machine.advance(operation_bytes({"kind": "READ", "key": keys[0]}), service))

    repeated = RmlActionMachine.start(case)
    for _ in range(4):
        repeated = repeated.advance(operation_bytes({"kind": "READ", "key": keys[0]}), service)
    assert repeated.phase == "ENV" and not repeated.terminal
    vectors = (
        (b"not-json", False),
        (b"[]", False),
        (operation_bytes({"kind": "ENV", "action": case.plan[0].public_record(case.spec.handles)}), False),
    )
    for raw, truncated in vectors:
        invalid = RmlActionMachine.start(case).advance(raw, service, output_truncated=truncated)
        assert invalid.outcome_state == "MODEL_INVALID"
    truncated = RmlActionMachine.start(case).advance(operation_bytes({"kind": "READ", "key": keys[0]}), service, output_truncated=True)
    assert truncated.outcome_state == "MODEL_INVALID"
    illegal = RmlActionMachine.start(case)
    for key in keys:
        illegal = illegal.advance(operation_bytes({"kind": "READ", "key": key}), service)
    illegal = illegal.advance(operation_bytes({"kind": "ENV", "action": {"action_kind": "MOVE", "arguments": {"site": "UNKNOWN"}}}), service)
    assert illegal.outcome_state == "MODEL_INVALID"
    assert RmlActionMachine.start(case).provider_failure("SIMULATED").outcome_state == "INFRASTRUCTURE_FAILURE"

    registry = build_opportunity_registry(build_roster())
    assert len(registry) == 234
    ledger = OpportunityLedger(registry)
    for trajectory in build_roster():
        first = next(row for row in registry if row.trajectory_id == trajectory.trajectory_id and row.slot_index == 0)
        ledger = ledger.append(OpportunityEvent(first.opportunity_id, first.trajectory_id, 0, "READ", True, "TERMINAL", "MODEL_INVALID", 1, 1, 1, 1, 1))
        ledger = ledger.cancel_suffix(trajectory.trajectory_id, 0)
    assert ledger.reconcile(require_complete=True) == {
        "registered": 234,
        "disposed": 234,
        "dispatched": 18,
        "zero_attempt_resource_failures": 0,
        "cancelled": 216,
    }
    _raises(MachineContractError, "retried", lambda: ledger.append(ledger.events[0]))

    # Predictable pre-call overflow invokes no provider and is zero-attempt.
    calls = {"count": 0}
    def provider(_payload, *, opportunity_id):
        calls["count"] += 1
        return b"{}", {
            "input_tokens": 1,
            "output_tokens": 1,
            "wall_ms": 1,
            "finish_reason": "stop",
        }
    huge = replace(RmlActionMachine.start(case), scratch="x" * 140_000)
    one_registry = tuple(row for row in registry if row.trajectory_id == build_roster()[0].trajectory_id)
    dispatch_service = ExactMemoryService(
        snapshot, authorized_trajectory_id=one_registry[0].trajectory_id
    )
    _, overflow_ledger = dispatch_one(huge, dispatch_service, provider, one_registry[0], OpportunityLedger(one_registry))
    assert calls["count"] == 0 and not overflow_ledger.events[0].attempted
    assert overflow_ledger.events[0].outcome_state == "RESOURCE_CEILING_EXCEEDED"
    overflow_ledger = overflow_ledger.cancel_suffix(one_registry[0].trajectory_id, 0)
    assert overflow_ledger.reconcile(require_complete=True) == {
        "registered": 13, "disposed": 13, "dispatched": 0,
        "zero_attempt_resource_failures": 1, "cancelled": 12,
    }
    # Provider-returned oversize output is one dispatch and a resource failure,
    # never a parser/model-invalid credit.
    output_calls = {"count": 0}
    def oversize_provider(_payload, *, opportunity_id):
        output_calls["count"] += 1
        return b"x" * (int(RESOURCE_CEILINGS["output_bytes_per_call"]) + 1), {
            "input_tokens": 1,
            "output_tokens": 1,
            "wall_ms": 1,
            "finish_reason": "stop",
        }
    _, output_ledger = dispatch_one(RmlActionMachine.start(case), dispatch_service, oversize_provider, one_registry[0], OpportunityLedger(one_registry))
    assert output_calls["count"] == 1 and output_ledger.events[0].attempted
    assert output_ledger.events[0].outcome_state == "RESOURCE_CEILING_EXCEEDED"
    assert output_ledger.events[0].output_bytes == int(RESOURCE_CEILINGS["output_bytes_per_call"]) + 1
    output_ledger = output_ledger.cancel_suffix(one_registry[0].trajectory_id, 0)
    assert output_ledger.reconcile(require_complete=True) == {
        "registered": 13, "disposed": 13, "dispatched": 1,
        "zero_attempt_resource_failures": 0, "cancelled": 12,
    }

    # Registration identity is checked against the live machine before the
    # provider can be called; an ENV registration cannot dispatch slot-0 READ.
    mismatched = next(row for row in one_registry if row.slot_index == 4)
    mismatch_calls = {"count": 0}
    def mismatch_provider(payload, *, opportunity_id):
        mismatch_calls["count"] += 1
        return operation_bytes({"kind": "READ", "key": keys[0]}), {
            "input_tokens": len(payload), "output_tokens": 1,
            "wall_ms": 0, "finish_reason": "stop",
        }
    _raises(
        MachineContractError,
        "slot/phase",
        lambda: dispatch_one(
            RmlActionMachine.start(case), dispatch_service, mismatch_provider,
            mismatched, OpportunityLedger(one_registry), token_counter=len,
        ),
    )
    assert mismatch_calls["count"] == 0
    none_registration = next(
        row for row in registry
        if row.trajectory_id == "NONE_REC:J_H" and row.slot_index == 0
    )
    wrong_condition_service = ExactMemoryService(
        snapshot, authorized_trajectory_id=none_registration.trajectory_id
    )
    _raises(
        MachineContractError,
        "unauthorized for condition",
        lambda: dispatch_one(
            RmlActionMachine.start(case), wrong_condition_service, mismatch_provider,
            none_registration,
            OpportunityLedger(
                tuple(
                    row for row in registry
                    if row.trajectory_id == none_registration.trajectory_id
                )
            ),
            token_counter=len,
        ),
    )
    assert mismatch_calls["count"] == 0
    other_target = next(
        row for row in registry
        if row.trajectory_id == "GOLD_REC:J_TWIN" and row.slot_index == 0
    )
    _raises(
        MachineContractError,
        "active target",
        lambda: dispatch_one(
            RmlActionMachine.start(case), dispatch_service, mismatch_provider,
            other_target, OpportunityLedger(registry), token_counter=len,
        ),
    )
    auth_registration = next(
        row for row in registry
        if row.trajectory_id == "AUTH_REPLAY:J_H" and row.slot_index == 0
    )
    auth_registry = tuple(
        row for row in registry
        if row.trajectory_id == auth_registration.trajectory_id
    )
    unbound_child_service = ExactMemoryService(
        snapshot, authorized_trajectory_id=auth_registration.trajectory_id
    )
    _raises(
        MachineContractError,
        "parent-derived artifact seal",
        lambda: dispatch_one(
            RmlActionMachine.start(case), unbound_child_service, mismatch_provider,
            auth_registration, OpportunityLedger(auth_registry), token_counter=len,
        ),
    )
    assert mismatch_calls["count"] == 0
    parent_seal = digest(b"frozen-parent-artifact")
    parent_bound_ledger = OpportunityLedger(auth_registry).bind_parent_artifact(
        "GOLD_REC:J_H", parent_seal
    )
    wrong_parent_service = ExactMemoryService(
        snapshot,
        authorized_trajectory_id=auth_registration.trajectory_id,
        parent_artifact_sha256=digest(b"wrong-parent"),
    )
    _raises(
        MachineContractError,
        "parent artifact seal mismatch",
        lambda: dispatch_one(
            RmlActionMachine.start(case), wrong_parent_service, mismatch_provider,
            auth_registration, parent_bound_ledger, token_counter=len,
        ),
    )
    second = one_registry[1]
    _raises(
        MachineContractError,
        "slot order",
        lambda: OpportunityLedger(one_registry).append(
            OpportunityEvent(
                second.opportunity_id, second.trajectory_id, 1, "READ", True,
                "COMPLETED_NONTERMINAL", None, 1, 1, 1, 1, 0, "stop",
            )
        ),
    )

    # A provider's tokenizer accounting is independently recomputed, and a
    # length finish is durably classified as a truncated MODEL_INVALID call.
    valid_raw = operation_bytes({"kind": "READ", "key": keys[0]})
    def truncated_provider(payload, *, opportunity_id):
        return valid_raw, {
            "input_tokens": len(payload), "output_tokens": len(valid_raw),
            "wall_ms": 0, "finish_reason": "length",
        }
    truncated_machine, truncated_ledger = dispatch_one(
        RmlActionMachine.start(case), dispatch_service, truncated_provider,
        one_registry[0], OpportunityLedger(one_registry), token_counter=len,
    )
    assert truncated_machine.outcome_state == "MODEL_INVALID"
    assert truncated_ledger.events[0].finish_reason == "length"

    def mismatched_accounting(payload, *, opportunity_id):
        return valid_raw, {
            "input_tokens": len(payload) + 1, "output_tokens": len(valid_raw),
            "wall_ms": 0, "finish_reason": "stop",
        }
    accounting_machine, accounting_ledger = dispatch_one(
        RmlActionMachine.start(case), dispatch_service, mismatched_accounting,
        one_registry[0], OpportunityLedger(one_registry), token_counter=len,
    )
    assert accounting_machine.outcome_state == "INFRASTRUCTURE_FAILURE"
    assert accounting_ledger.events[0].attempted

    # The final registered call crosses the per-call, per-trajectory, and
    # whole-gate output-token ceilings by exactly one.  The dispatched event
    # remains durable and typed instead of disappearing during ledger append.
    boundary_case = cases["P_H"]
    boundary_snapshot = snapshots[f"{boundary_case.source_projection}:GOLD"]
    boundary_service = ExactMemoryService(
        boundary_snapshot,
        authorized_trajectory_id="GOLD_REC:P_H",
    )
    boundary_machine = RmlActionMachine.start(boundary_case)
    boundary_keys = [
        next(key for key in boundary_machine.allowed_keys if key.startswith(prefix))
        for prefix in ("exchanger:", "pair:", "valve:", "schema:")
    ]
    for key in boundary_keys:
        boundary_machine = boundary_machine.advance(
            operation_bytes({"kind": "READ", "key": key}), boundary_service
        )
    for action in boundary_case.plan[:8]:
        boundary_machine = boundary_machine.advance(
            operation_bytes(
                {"kind": "ENV", "action": action.public_record(boundary_case.spec.handles)}
            ),
            boundary_service,
        )
    assert boundary_machine.slot_index == 12 and not boundary_machine.terminal

    boundary_ledger = OpportunityLedger(registry)
    roster = build_roster()
    boundary_trajectory = next(
        trajectory for trajectory in roster
        if trajectory.trajectory_id == "GOLD_REC:P_H"
    )
    for trajectory in roster:
        if trajectory == boundary_trajectory:
            continue
        rows = sorted(
            (row for row in registry if row.trajectory_id == trajectory.trajectory_id),
            key=lambda row: row.slot_index,
        )
        for row in rows:
            terminal = row.slot_index == 12
            boundary_ledger = boundary_ledger.append(
                OpportunityEvent(
                    row.opportunity_id, row.trajectory_id, row.slot_index, row.phase,
                    True, "TERMINAL" if terminal else "COMPLETED_NONTERMINAL",
                    "MODEL_INVALID" if terminal else None,
                    0, 256, 0, 4096, 0, "stop",
                )
            )
    last_rows = sorted(
        (
            row for row in registry
            if row.trajectory_id == boundary_trajectory.trajectory_id
        ),
        key=lambda row: row.slot_index,
    )
    for row in last_rows[:12]:
        boundary_ledger = boundary_ledger.append(
            OpportunityEvent(
                row.opportunity_id, row.trajectory_id, row.slot_index, row.phase,
                True, "COMPLETED_NONTERMINAL", None,
                0, 256, 0, 4096, 0, "stop",
            )
        )
    commit_raw = operation_bytes(
        {"kind": "ENV", "action": boundary_case.plan[-1].public_record(boundary_case.spec.handles)}
    )
    def boundary_counter(payload):
        return 257 if payload == commit_raw else conservative_cpu_token_count(payload)
    def boundary_provider(payload, *, opportunity_id):
        return commit_raw, {
            "input_tokens": boundary_counter(payload),
            "output_tokens": 257,
            "wall_ms": 0,
            "finish_reason": "stop",
        }
    boundary_failed, boundary_ledger = dispatch_one(
        boundary_machine, boundary_service, boundary_provider,
        last_rows[12], boundary_ledger, token_counter=boundary_counter,
    )
    assert boundary_failed.outcome_state == "RESOURCE_CEILING_EXCEEDED"
    assert boundary_ledger.events[-1].attempted
    assert boundary_ledger.events[-1].output_tokens == 257
    assert boundary_ledger.reconcile(require_complete=True) == {
        "registered": 234,
        "disposed": 234,
        "dispatched": 234,
        "zero_attempt_resource_failures": 0,
        "cancelled": 0,
    }


def test_RML_G1_T03_D0_WORLD_PLUS_NEW_TRACE_REDUCER_AND_SLICE_CERTIFICATE():
    pretarget_seal = seal_pretarget_snapshot_universe()
    cases = build_selected_cases(pretarget_seal)
    certificate = build_slice_certificate(cases)
    assert certificate.none_best_policy_success_capacity == 1
    assert certificate.atoms_best_policy_success_capacity == 1
    assert certificate.atoms_guaranteed_identifiable_sides == 0
    assert certificate.atoms_capacity_witness
    assert not certificate.ratified_atoms_zero_capacity_consistent
    assert all(certificate.minimum_action_depths[index] == 9 for index in range(4))
    assert all(row["equal_before_binding_action"] for row in certificate.predecisive_feedback_vectors)
    assert all(not row["successful_continuation_exists"] for row in certificate.diagnostic_detour_vectors)
    assert certificate.planner_enumerator_agree

    scripted = run_scripted_cpu_gate()
    assert scripted.report["local_check_passed"]
    parent = scripted.traces["GOLD_REC:J_H"]
    assert (
        parent.citations_returned_before_use
        and parent.citation_semantic_entailment
        and parent.decisive_citations_minimal
    )
    # Single-field mutation vectors: late/unreturned citation and empty parent.
    mutated = replace(parent, citations_returned_before_use=False)
    row = score_intervention(
        mutated,
        scripted.traces["AUTH_REPLAY:J_H"],
        scripted.traces["SHAM_REC:J_H"],
        scripted.traces["CUT_REC:J_H"],
        scripted.traces["TWIN_REC:J_H"],
        cases["J_H"],
        cases["J_TWIN"],
    )
    assert not row.replay_exact and not row.cut_behavior_disrupted
    snapshot = pretarget_seal.snapshot_map()["H:GOLD"]
    decisive = decisive_handles(cases["J_H"], snapshot)
    closure = equivalence_closure(snapshot, decisive)
    cut = masked_snapshot(snapshot, decisive, transform="CUT")
    assert_no_closure_residue(cut, closure)
    contaminated = replace(cut, cache_views=(*cut.cache_views, (next(iter(closure)), decisive[0])))
    _raises(MemoryContractError, "residue", lambda: assert_no_closure_residue(contaminated, closure))
    assert all(
        row.cut_citation_invalid_secondary for row in scripted.interventions.values()
    )
    # Handle equality alone is insufficient: mutate pair semantics while
    # retaining keys/handles and require entailment/minimality to fail.
    pair_handle = decisive[0]
    row_by_handle = snapshot.handle_map()
    pair_row = row_by_handle[pair_handle]
    wrong_payload = {
        **pair_row.payload,
        "families": ["CF000000000000", "CF000000000001"],
    }
    wrong_serialized = canonical_bytes(
        {
            "handle": pair_row.handle,
            "payload": wrong_payload,
            "public_support": list(pair_row.public_support),
            "status": "ROW",
        }
    )
    wrong_row = replace(
        pair_row,
        payload=wrong_payload,
        serialized=wrong_serialized,
        token_count=conservative_cpu_token_count(wrong_serialized),
    )
    wrong_snapshot = replace(
        snapshot,
        rows=tuple(wrong_row if row.handle == pair_handle else row for row in snapshot.rows),
        snapshot_id="",
        sealed_sha256="",
    )
    wrong_seal = digest(_snapshot_body(wrong_snapshot))
    wrong_snapshot = replace(
        wrong_snapshot,
        snapshot_id=digest({"mount_sha256": wrong_seal}),
        sealed_sha256=wrong_seal,
    )
    wrong_machine = scripted.machines["GOLD_REC:J_H"]
    wrong_records = tuple(
        replace(record, returned_row=wrong_serialized)
        if record.returned_handle == pair_handle
        else record
        for record in wrong_machine.records
    )
    rescored = score_frozen_trace(
        "GOLD_REC:J_H", "GOLD_REC", cases["J_H"],
        replace(wrong_machine, records=wrong_records), wrong_snapshot,
    )
    assert not rescored.citation_semantic_entailment
    assert not rescored.decisive_citations_minimal

    parent_machine = scripted.machines["GOLD_REC:J_H"]
    pair_index = next(
        index
        for index, record in enumerate(parent_machine.records)
        if record.returned_handle == pair_handle
    )
    # Status mutation: a NOT_FOUND handle is never evidence.
    status_records = list(parent_machine.records)
    status_records[pair_index] = replace(status_records[pair_index], returned_status="NOT_FOUND")
    _raises(
        ReducerError,
        "sealed service",
        lambda: score_frozen_trace(
            "GOLD_REC:J_H", "GOLD_REC", cases["J_H"],
            replace(parent_machine, records=tuple(status_records)), snapshot,
        ),
    )
    # Exact returned payload mutation cannot be repaired by the snapshot index.
    payload_records = list(parent_machine.records)
    payload_records[pair_index] = replace(
        payload_records[pair_index], returned_row=payload_records[pair_index].returned_row + b" "  # type: ignore[operator]
    )
    _raises(
        ReducerError,
        "sealed service",
        lambda: score_frozen_trace(
            "GOLD_REC:J_H", "GOLD_REC", cases["J_H"],
            replace(parent_machine, records=tuple(payload_records)), snapshot,
        ),
    )
    # Late availability and overcitation both fail mechanical credit.
    late_records = list(parent_machine.records)
    late_records[pair_index] = replace(late_records[pair_index], slot_index=12)
    _raises(
        ReducerError,
        "slot/phase order",
        lambda: score_frozen_trace(
            "GOLD_REC:J_H", "GOLD_REC", cases["J_H"],
            replace(parent_machine, records=tuple(late_records)), snapshot,
        ),
    )
    extra_handle = next(
        record.returned_handle
        for record in parent_machine.records
        if record.returned_handle is not None and record.returned_handle not in decisive
    )
    over_records = list(parent_machine.records)
    env_index = next(index for index, record in enumerate(over_records) if record.phase == "ENV")
    over_citations = (*over_records[env_index].citations, extra_handle)
    over_records[env_index] = replace(
        over_records[env_index],
        citations=over_citations,
        raw_output=operation_bytes(
            over_records[env_index].operation,  # type: ignore[arg-type]
            scratch=over_records[env_index].scratch,
            citations=over_citations,
        ),
    )
    over_score = score_frozen_trace(
        "GOLD_REC:J_H", "GOLD_REC", cases["J_H"],
        replace(parent_machine, records=tuple(over_records)), snapshot,
    )
    assert not over_score.decisive_citations_minimal

    raw_records = list(parent_machine.records)
    raw_records[env_index] = replace(raw_records[env_index], raw_output=b"{}")
    _raises(
        ReducerError, "record raw output does not parse",
        lambda: score_frozen_trace(
            "GOLD_REC:J_H", "GOLD_REC", cases["J_H"],
            replace(parent_machine, records=tuple(raw_records)), snapshot,
        ),
    )

    # Citations cannot be laundered after the actions they support.  This is
    # otherwise a fully self-consistent successful trace with both decisive
    # handles cited only on final COMMIT.
    laundered_records = []
    for index, record in enumerate(parent_machine.records):
        citations = decisive if index == len(parent_machine.records) - 1 else ()
        if record.operation is not None:
            raw_output = operation_bytes(
                record.operation, scratch=record.scratch, citations=citations
            )
        else:
            raw_output = record.raw_output
        laundered_records.append(
            replace(record, citations=citations, raw_output=raw_output)
        )
    laundered = score_frozen_trace(
        "GOLD_REC:J_H", "GOLD_REC", cases["J_H"],
        replace(parent_machine, records=tuple(laundered_records)), snapshot,
    )
    assert laundered.legal_commit_success
    assert not laundered.citations_returned_before_use
    assert not laundered.decisive_citations_minimal

    pair_handle, valve_handle = decisive
    pair_support = next(
        record.slot_index
        for record in parent_machine.records
        if record.action_record is not None
        and record.action_record["action_kind"] == "ACQUIRE"
        and record.action_record["arguments"]["cartridge"]
        in {cases["J_H"].spec.handles.cartridges[index] for index in cases["J_H"].pair}  # type: ignore[union-attr]
    )
    valve_support = next(
        record.slot_index
        for record in parent_machine.records
        if record.action_record is not None
        and record.action_record["action_kind"] == "CONFIGURE"
    )
    run_slot = next(
        record.slot_index
        for record in parent_machine.records
        if record.action_record is not None
        and record.action_record["action_kind"] == "RUN"
    )

    def cite_first_at(pair_slot, valve_slot):
        changed = []
        for record in parent_machine.records:
            citations = tuple(
                handle
                for handle, slot in ((pair_handle, pair_slot), (valve_handle, valve_slot))
                if record.slot_index == slot
            )
            changed.append(
                replace(
                    record,
                    citations=citations,
                    raw_output=record.raw_output
                    if record.operation is None
                    else operation_bytes(
                        record.operation, scratch=record.scratch, citations=citations
                    ),
                )
            )
        return score_frozen_trace(
            "GOLD_REC:J_H", "GOLD_REC", cases["J_H"],
            replace(parent_machine, records=tuple(changed)), snapshot,
        )

    assert cite_first_at(pair_support, valve_support).citations_returned_before_use
    assert not cite_first_at(pair_support + 1, valve_support).citations_returned_before_use
    assert not cite_first_at(pair_support, valve_support + 1).citations_returned_before_use
    assert not cite_first_at(run_slot, run_slot).citations_returned_before_use

    # Terminal state/outcome labels are never trusted: unchanged action bytes
    # cannot be promoted by copying a successful state into a failed machine.
    failed_machine = scripted.machines["NONE_REC:J_TWIN"]
    forged = replace(
        failed_machine,
        state=parent_machine.state,
        outcome_state="SCIENTIFIC_VALID_SUCCESS",
    )
    _raises(
        ReducerError,
        "state disagrees",
        lambda: score_frozen_trace(
            "NONE_REC:J_TWIN", "NONE_REC", cases["J_TWIN"], forged,
            scripted.snapshots["NONE_REC:J_TWIN"],
        ),
    )
    _raises(
        ReducerError,
        "outcome label disagrees",
        lambda: score_frozen_trace(
            "GOLD_REC:J_H", "GOLD_REC", cases["J_H"],
            replace(parent_machine, outcome_state="SCIENTIFIC_VALID_NONSUCCESS"),
            snapshot,
        ),
    )
    first_env = next(
        index for index, record in enumerate(parent_machine.records)
        if record.phase == "ENV"
    )
    mutation_vectors = []
    changed = list(parent_machine.records)
    changed[first_env] = replace(changed[first_env], action_record={})
    mutation_vectors.append((tuple(changed), "ENV operation fields disagree"))
    changed = list(parent_machine.records)
    changed[first_env] = replace(changed[first_env], result_code="FORGED")
    mutation_vectors.append((tuple(changed), "result disagrees"))
    changed = list(parent_machine.records)
    changed[first_env] = replace(changed[first_env], result_text="forged text")
    mutation_vectors.append((tuple(changed), "result disagrees"))
    changed = list(parent_machine.records)
    changed[first_env] = replace(changed[first_env], phase="READ")
    mutation_vectors.append((tuple(changed), "slot/phase order"))
    changed = list(parent_machine.records)
    changed[first_env], changed[first_env + 1] = changed[first_env + 1], changed[first_env]
    mutation_vectors.append((tuple(changed), "slot/phase order"))
    for records, fragment in mutation_vectors:
        _raises(
            ReducerError,
            fragment,
            lambda records=records: score_frozen_trace(
                "GOLD_REC:J_H", "GOLD_REC", cases["J_H"],
                replace(parent_machine, records=records), snapshot,
            ),
        )

    precommit_state = execute(cases["J_H"].spec, cases["J_H"].plan[:8])[-1].state
    _raises(
        ReducerError,
        "froze before a terminal condition",
        lambda: score_frozen_trace(
            "GOLD_REC:J_H", "GOLD_REC", cases["J_H"],
            replace(
                parent_machine,
                records=parent_machine.records[:-1],
                state=precommit_state,
                outcome_state="SCIENTIFIC_VALID_SUCCESS",
                terminal_reason="COMMITTED",
            ),
            snapshot,
        ),
    )

    # TWIN executes in the actual world, terminates valid-nonsuccess there,
    # and the same bytes plus the registered COMMIT succeed in the twin world.
    for target_id, twin_id in (("J_H", "J_TWIN"), ("P_H", "P_TWIN")):
        twin_trace = scripted.traces[f"TWIN_REC:{target_id}"]
        assert twin_trace.outcome_state == "SCIENTIFIC_VALID_NONSUCCESS"
        assert not twin_trace.d0_terminal_success
        emitted = tuple(
            resolve_public_action(cases[twin_id].spec, dict(action))
            for action in twin_trace.action_records
        )
        replayed = execute(cases[twin_id].spec, (*emitted, cases[twin_id].plan[-1]))
        assert replayed[-1].state.success
        assert digest(list(twin_trace.action_records[:7])) == cases[twin_id].decisive_signature

    # The sham inventory/order is source-sealed and unchanged by target data.
    assert snapshot.sham_candidate_order == build_snapshot(extract_permitted_source_facts()).sham_candidate_order
    # Reducer is an offline pure sink and cannot alter the frozen trace or any
    # model-visible byte.
    frozen_machine = scripted.machines["GOLD_REC:J_H"]
    before = frozen_machine.model_visible_bytes()
    _ = score_frozen_trace("GOLD_REC:J_H", "GOLD_REC", cases["J_H"], frozen_machine, snapshot)
    assert before == frozen_machine.model_visible_bytes()


def test_RML_G1_T04_HASHED_DETERMINISTIC_RUNTIME_AND_ABSOLUTE_RESOURCE_CANARY():
    hashes = {name: digest(name.encode()) for name in REQUIRED_HASH_COMPONENTS}
    closure = RuntimeClosure(
        MODEL_ID,
        MODEL_REVISION,
        TOKENIZER_REVISION,
        DECODING,
        hashes,
        "FRESH_PROCESS_PER_TRAJECTORY",
        "EMPTY_KV_BEFORE_FIRST_SLOT",
        "EMPTY_READER_AND_BACKEND_CACHE",
        0.0,
    )
    closure_hash = closure.validate()
    cases = build_selected_cases(seal_pretarget_snapshot_universe())
    raw = operation_bytes({"kind": "READ", "key": "schema:canary"})
    receipt = CanaryReceipt(
        closure_hash,
        digest(b"disjoint-nonscientific-grammar-canary"),
        tuple(case.public_sha256 for case in cases.values()),
        raw,
        True,
        True,
        True,
        0,
        8,
        8,
        64,
        len(raw),
    )
    assert validate_canary_receipt(receipt, closure)["canary_valid"]
    _raises(RuntimeContractError, "scientific opportunity", lambda: validate_canary_receipt(replace(receipt, scientific_opportunities_consumed=1), closure))
    _raises(RuntimeContractError, "absolute per-call ceiling", lambda: validate_canary_receipt(replace(receipt, output_tokens=int(RESOURCE_CEILINGS["output_tokens_per_call"]) + 1), closure))
    _raises(RuntimeContractError, "decoding", lambda: replace(closure, decoding={**DECODING, "temperature": 1}).validate())
    GateResourceUsage(24, 10_800, 2 * 1024**3, 0.0).validate()
    _raises(RuntimeContractError, "GPU-hour", lambda: GateResourceUsage(24.01, 1, 1, 0.0).validate())
    _raises(RuntimeContractError, "storage", lambda: GateResourceUsage(1, 1, 2 * 1024**3 + 1, 0.0).validate())


def test_RML_G1_T05_EXACT_18_TRAJECTORY_CAUSAL_GATE():
    result = run_scripted_cpu_gate()
    assert len(result.traces) == 18 and len(result.interventions) == 2
    assert result.report["local_check_passed"]
    assert all(result.report["exact_predicates"].values())
    invalid = replace(result.traces["NONE_REC:J_H"], outcome_state="MODEL_INVALID")
    from rml_stage_b.reducer import evaluate_exact_gate
    damaged = dict(result.traces)
    damaged[invalid.trajectory_id] = invalid
    assert not evaluate_exact_gate(damaged, result.interventions)["exact_predicates"]["none_success_at_most_1_of_4"]
    wrong_twin = replace(result.interventions["GOLD_REC:J_H"], twin_redirected=False)
    interventions = dict(result.interventions)
    interventions["GOLD_REC:J_H"] = wrong_twin
    assert not evaluate_exact_gate(result.traces, interventions)["local_check_passed"]


def test_RML_G1_T06_TWO_PHASE_REVIEW_AND_EXACT_CLAIM_FIREWALL():
    packet, output = digest(b"packet"), digest(b"immutable-output")
    approvals = (
        ReviewApproval("PRE_GPU", "INDEPENDENT_REVIEWER", "reviewer-a", packet, "APPROVE_EXACT_BYTES", False),
        ReviewApproval("PRE_GPU", "AUTHOR_SIDE_ADVOCATE", "advocate-b", packet, "APPROVE_EXACT_BYTES", False),
        ReviewApproval("POST_RUN", "INDEPENDENT_REVIEWER", "reviewer-c", output, "APPROVE_EXACT_BYTES", False),
        ReviewApproval("POST_RUN", "AUTHOR_SIDE_ADVOCATE", "advocate-d", output, "APPROVE_EXACT_BYTES", False),
    )
    assert validate_two_phase_reviews(approvals, implementation_packet_sha256=packet, immutable_output_sha256=output) == {"pre_gpu_complete": True, "post_run_complete": True}
    _raises(ReviewContractError, "distinct actors", lambda: validate_two_phase_reviews((approvals[0], replace(approvals[1], actor_id="reviewer-a")), implementation_packet_sha256=packet))
    validate_result_language(ALLOWED_PASS_CLAIM, passed=True)
    validate_result_language(ALLOWED_FAILURE_CLAIM, passed=False)
    _raises(ValueError, "whitelist", lambda: validate_result_language("RML learned and generalized", passed=True))
    packet = build_cpu_preflight()
    assert not packet["summary"]["ratified_acceptance_tests_satisfied"]
    assert packet["summary"]["local_check_passed"]
    assert not packet["summary"]["acceptance_test_satisfied"]
    assert not packet["summary"]["gpu_prerequisite_satisfied"]
    for report in packet["reports"].values():
        assert {"local_check_passed", "acceptance_test_satisfied", "gpu_prerequisite_satisfied"} <= set(report)
        assert not report["acceptance_test_satisfied"]
        assert not report["gpu_prerequisite_satisfied"]
        assert report.get("passed") is not True
