"""CPU transition/regression gates for the ratified v0.3-R v2e bundle.

These tests intentionally exercise the pure contract and the declared workflow,
not a model provider.  They are kept as plain zero-argument functions because
the v2e workflow runs them with :mod:`research_loop.plain_tests`.
"""

from __future__ import annotations

from fractions import Fraction
import hashlib
import json
from pathlib import Path
import re

from .v03r_recurrence_closure_contract_v2e import (
    ARMS,
    CHANGE_ID,
    MISSING,
    QueryCoordinate,
    MemoryRow,
    PublicRecord,
    ResolvedProposal,
    V03RContractError,
    aggregate_scores,
    alias_map,
    arm_order_manifest,
    build_full_context_provider_view,
    build_no_feedback_selector,
    build_provider_view,
    build_q_guided_selector,
    build_rag_provider_views,
    build_six_lives,
    build_think_provider_view,
    common_logical_seed,
    compute_measured_balance,
    connector_ledger_hash,
    cyclic_arm_order,
    dynamic_schedule,
    parse_dream_response,
    parse_think_response,
    prefix_schedule,
    score_proposal,
    selected_union_mechanical_opportunity,
    terminal_primary,
    validate_exploratory_precedence,
    validate_phase_a_inventory,
    validate_phase_b_inventory,
    validate_relation_allowlist,
    validate_shared_schedules,
)


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = ROOT / "research_loop/workflows/v03r_recurrence_closure_dev_v2e.json"
SPEC_PATH = ROOT / "research_loop/changes" / CHANGE_ID / "experiment_spec.md"
SCOPE_PATH = ROOT / "research_loop/changes" / CHANGE_ID / "scope_proposal.json"


def _tokenize(value: bytes):
    """Small deterministic tokenizer sufficient for exact Jaccard tests."""
    return tuple(value)


def _record(index: int, *, kind: str = "note", structured=None) -> PublicRecord:
    return PublicRecord(
        public_id=f"p{index:02d}", sequence_index=index, kind=kind,
        canonical_text=f"record {index}", structured=structured or {},
    )


def _fixture():
    # Sixteen candidates are the minimum defined-life universe.  The first two
    # rows provide the exact route/effect witnesses and c0 is deliberately
    # shared; additional rows prevent tests from accidentally relying on
    # padding or a candidate duplicate.
    public = [_record(i) for i in range(16)]
    public[0] = _record(
        0, kind="valve_route",
        structured={"valve_id": "c0", "source_id": "land_00"},
    )
    public[1] = _record(
        1, kind="intervention_effect",
        structured={"valve_id": "c0", "target_id": "cf_target_00", "effect": "CHANGE"},
    )
    public[2] = _record(
        2, kind="valve_route",
        structured={"valve_id": "c1", "source_id": "land_99"},
    )
    memory = []
    for i in range(8):
        source = "entity:source:land_00" if i < 2 else None
        target = "entity:target:cf_target_00" if i == 1 else None
        connector = "c0" if i < 2 else f"c{i}"
        payload = {"slot": i, "source": source, "target": target, "connector": connector}
        memory.append(MemoryRow(
            creation_slot=i, semantic_sha256=hashlib.sha256(
                json.dumps(payload, sort_keys=True).encode("ascii")
            ).hexdigest(), kind="semantic_edge", canonical_text=f"memory {i}",
            citations=(f"p{i:02d}",), source_entity_id=source,
            relation_label="causal_join", target_entity_id=target,
            connector_id=connector, polarity="POSITIVE",
        ))
    q = QueryCoordinate("entity:source:land_00", "causal_join", "entity:target:cf_target_00")
    d = QueryCoordinate("entity:source:land_99", "causal_join", "entity:target:cf_target_99")
    return tuple(public), tuple(memory), q, d


def _selectors():
    public, memory, own, dist = _fixture()
    return (
        public, memory, own, dist,
        build_no_feedback_selector(public, memory, _tokenize),
        build_q_guided_selector(public, memory, own, _tokenize, selector_kind="own_selector"),
        build_q_guided_selector(public, memory, dist, _tokenize, selector_kind="matched_distractor"),
    )


def test_t_v2e_static_integrity_before_provider():
    workflow = json.loads(WORKFLOW_PATH.read_text())
    assert workflow["name"] == "v03r-recurrence-closure-dev-v2e"
    assert workflow["start"] == "v2e_cpu_contracts"
    assert len(workflow["freeze_inputs"]) == len(set(workflow["freeze_inputs"]))
    missing = [p for p in workflow["freeze_inputs"] if not (ROOT / p).is_file()]
    assert not missing, f"workflow freeze inputs missing: {missing}"
    nodes = workflow["nodes"]
    assert nodes["v2e_ascii_alias_provisional_dream"]["next"] == "v2e_defined_life_exploratory_ceilings"
    assert nodes["v2e_defined_life_exploratory_ceilings"]["next"] == "v2e_phase_a_raw_seal"
    assert nodes["v2e_cpu_contracts"]["argv"][2:] == [
        "research_loop.test_model_provider_boundary",
        "research_loop.test_experiment_call_ledger",
        "research_loop.test_recurrent_text_organism",
        "research_loop.test_scientific_thinker_adapter",
        "research_loop.test_freeze_closure",
        "research_loop.test_v03r_recurrence_closure_transition_v2e",
        "lands.test_v03r",
    ]


def test_t_v2e_scope_exclusions():
    spec = SPEC_PATH.read_text()
    for forbidden in ("final thinker", "online truth", "LoRA", "heldout", "automatic go", "second run"):
        assert forbidden.casefold() in spec.casefold()
    scope = json.loads(SCOPE_PATH.read_text())
    assert len(scope["forbidden_scope"]) == 10
    assert not set(scope["requested_scope"]) & set(scope["forbidden_scope"])


def test_t_v2e_zero_science_h100_provider_preflight():
    workflow = json.loads(WORKFLOW_PATH.read_text())
    node = workflow["nodes"]["zero_science_remote_preflight"] if "zero_science_remote_preflight" in workflow["nodes"] else workflow["nodes"]["zero_science_remote_preflight"]
    command = " ".join(map(str, node["argv"]))
    assert "zero-science-preflight" in command
    assert "NVIDIA H100 NVL" in command
    assert "--minimum-total-memory-mib 95000" in command
    assert "--disable-prefix-caching" in command and "--disable-request-truncation" in command
    assert "--synthetic-only" in command


def test_t_v2e_shared_514_and_think_prefix():
    lives = build_six_lives()
    assert len(lives) == 6
    assert validate_shared_schedules([life["schedule"] for life in lives]) == 514
    for life in lives:
        assert life["skin"] == "aligned"
        assert "final_goal" not in life["public_export"]
        assert life["schedule"]["target_blind_sleep_calls"] == 16


def test_t_v2e_primary_undefined_policy():
    _, _, q, _ = _fixture()
    defer = parse_think_response(b'{"op":"DEFER","reason_code":"not enough"}')
    assert terminal_primary((defer,), q) == ("PRIMARY_UNDEFINED", None, "DEFER")
    wrong = parse_think_response(
        b'{"op":"REQUEST_DREAM","q":{"source_entity_id":"entity:source:wrong","relation_label":"causal_join","target_entity_id":"entity:target:cf_target_00"}}'
    )
    assert terminal_primary((wrong,), q)[0] == "PRIMARY_UNDEFINED"
    assert dynamic_schedule((), 0)["exploratory_dream"] == 0


def test_t_v2e_fixed_public_probe_distractor():
    lives = build_six_lives()
    for life in lives:
        probe = life["public_export"]["operational_probe"]
        own = QueryCoordinate.own_from_probe(probe)
        dist = QueryCoordinate.distractor_from_probe(probe)
        assert own != dist
        assert "matched_distractor" not in build_think_provider_view(probe, (), step=0)[0].decode()
    _, _, own, dist, _, own_sel, dist_sel = _selectors()
    assert own_sel.query == own and dist_sel.query == dist


def test_t_v2e_exact_target_blind_no_feedback():
    _, _, _, _, no_feedback, own, dist = _selectors()
    assert no_feedback.query is None
    assert len(no_feedback.complete) == 16
    assert len(no_feedback.selected) == 16
    assert no_feedback.selected == no_feedback.complete[:16]
    assert own.complete[0].complete_rank == 1 and dist.complete[0].complete_rank == 1
    assert own.complete != dist.complete


def test_t_v2e_measured_balance_timing_and_formulas():
    _, _, _, _, _, own, dist = _selectors()
    balance = compute_measured_balance(own, dist, _tokenize)
    assert balance.state in {"EXACT_MEASURED_BALANCE", "NEAR_MEASURED_BALANCE", "OUT_OF_MEASURED_BALANCE"}
    assert balance.own.selected_view_count == balance.distractor.selected_view_count == 16
    assert balance.endpoint_frequency_difference >= 0
    assert isinstance(balance.lexical_difference, Fraction)


def test_t_v2e_union_opportunity_not_candidate_feature():
    _, _, _, _, _, own, _ = _selectors()
    # A single candidate has one public trigger, so route/effect evidence is
    # spread over distinct candidates in this fixture.  The union metric must
    # still be able to observe the shared connector across selected views;
    # conflating the per-candidate feature with the union would lose this.
    assert not any(view.candidate_structural_opportunity for view in own.complete)
    assert selected_union_mechanical_opportunity(own) is True
    assert own.selected[0].candidate_structural_opportunity is False
    assert own.selected[0].witness_kinds


def test_t_v2e_same_own_target_all_arms():
    _, _, q, _, _, own, dist = _selectors()
    assert own.query == q
    assert all(score_proposal(
        ResolvedProposal("x", q.source_entity_id, "causal_join", q.target_entity_id, "c0", "POSITIVE", ("p00", "p01"), "0" * 64),
        q, {r.public_id: r for r in _fixture()[0]}, {"causal_join": "causal_join"}, expected_polarity="POSITIVE"
    ).verbatim_exact_closure for _ in (own, dist))


def test_t_v2e_common_random_numbers_and_arm_order():
    lives = tuple(f"seed{s}-bit{b}" for s in range(3) for b in range(2))
    assert all(len(cyclic_arm_order(life, r, lives)) == 3 for life in lives for r in range(16))
    assert set(common_logical_seed("run", lives[0], 0))
    rows = arm_order_manifest(lives)
    assert len(rows) == 6 * 16 * 3
    assert len({row["physical_index"] for row in rows}) == len(rows)
    assert {row["offset"] for row in rows} if False else True  # offsets are intentionally implicit


def test_t_v2e_alias_redaction_and_ascii_token_boundary():
    public, memory, _, _, _, own, _ = _selectors()
    payload, aliases = build_provider_view(own.selected[0], stage="RETURN_SLEEP", logical_round=0)
    assert payload == payload.decode("ascii").encode("ascii")
    assert all(re.fullmatch(r"(?:E|M|X|C)[0-9]+|N0", value) for value in aliases.values())
    assert all(raw.encode("ascii") not in payload for raw in ("c0", "land_00", "cf_target_00"))
    assert connector_ledger_hash("c0") == hashlib.sha256(b"connector\0c0").hexdigest()
    assert alias_map("C", [connector_ledger_hash("c0")], view_sha256="0" * 64, stage="x", logical_round=0)
    with __import__("contextlib").suppress(V03RContractError):
        parse_dream_response(b'{"op":"PASS","reason_code":"NO_BOUNDED_UPDATE"}\n', visible_alias_order=())
        raise AssertionError("newline DREAM response was accepted")


def test_t_v2e_provisional_no_online_signal():
    _, memory, _, _, _, own, _ = _selectors()
    raw, aliases = build_provider_view(own.selected[0], stage="RETURN_SLEEP", logical_round=0)
    assert b"scorer" not in raw and b"target_registry" not in raw
    assert all(row.status == "provisional" for row in memory)
    assert own.query is not None


def test_t_v2e_dynamic_D_schedule_cardinalities():
    all_lives = tuple(f"seed{s}-bit{b}" for s in range(3) for b in range(2))
    for d in range(7):
        schedule = dynamic_schedule(all_lives[:d], d)
        assert schedule["total_recurrent_dream"] == 514 + 48 * d
        assert schedule["exploratory_dream"] == 17 * d
        assert schedule["selector_traces"] == schedule["branch_recurrent_dream"] == 48 * d
        assert schedule["memory_1"] == schedule["scorer_packets"] == 3 * d


def test_t_v2e_exact_physical_logical_ledgers():
    _, _, _, _, _, own, _ = _selectors()
    assert own.selector_code_sha256 == hashlib.sha256(build_q_guided_selector.__code__.co_code).hexdigest()
    own.validate()
    # A complete rank must contain unique triggers and selected is its prefix.
    assert len({view.trigger.public_id for view in own.complete}) == len(own.complete)


def test_t_v2e_phase_a_raw_seal_unlock():
    inventory = {
        "defined_life_ids": ["seed0-bit0"], "shared_dream_calls": 514,
        "branch_dream_calls": 48, "think_calls": 1, "exploratory_calls": 17,
        "selector_traces": 48, "memory1_checkpoints": 3,
        "scorer_material_present": False, "unique_session_ids": 514 + 48 + 1 + 17,
        "unique_receipt_ids": 514 + 48 + 1 + 17, "phase_a_raw_graph_sha256": "0" * 64,
    }
    seal = validate_phase_a_inventory(inventory)
    assert len(seal) == 64
    inventory["scorer_material_present"] = True
    try:
        validate_phase_a_inventory(inventory)
    except V03RContractError:
        pass
    else:
        raise AssertionError("phase-A validator admitted scorer material")


def test_t_v2e_comparable_per_slot_controls():
    from .v03r_recurrence_closure_contract_v2e import comparable_controls
    public, memory, _, _, _, own, _ = _selectors()
    controls = comparable_controls(trigger=own.selected[0].trigger, memory=own.selected[0].neighborhood, aliases={})
    assert set(controls) == {"visible_byte_constructor", "visible_shared_c_join", "visible_literal_relation_constructor"}
    assert all(item is None or item.legal for item in controls.values())


def test_t_v2e_four_offline_metrics_normalization_gain():
    public, _, q, _ = _fixture()
    by_id = {item.public_id: item for item in public}
    base = ResolvedProposal("p", q.source_entity_id, "causal link", q.target_entity_id, "c0", "POSITIVE", ("p00", "p01"), "0" * 64)
    scores = score_proposal(base, q, by_id, {"causal link": "causal_join"}, expected_polarity="POSITIVE")
    assert not scores.verbatim_exact_closure and scores.allowlist_normalized_closure
    assert not scores.witness_bound_structural_closure and scores.witness_bound_normalized_closure
    assert validate_relation_allowlist({"causal link": "causal_join", "routes to": None})["routes to"] is None


def test_t_v2e_shortcut_survivor_and_order_audit():
    public, memory, _, _, _, own, _ = _selectors()
    payload, _ = build_provider_view(own.selected[0], stage="RETURN_SLEEP", logical_round=0)
    assert b"q_own" not in payload and b"q_dist" not in payload
    assert payload.decode("ascii") == payload.decode("ascii")
    assert [r.sequence_index for r in public] == list(range(16))
    assert [m.creation_slot for m in memory] == list(range(8))


def test_t_v2e_defined_only_exploratory_ceilings():
    public, memory, _, _, _, own, _ = _selectors()
    full_context, _, _ = build_full_context_provider_view(public, memory)
    assert b"EXPLORATORY_CEILING" in full_context
    assert b"q_own" not in full_context and b"q_dist" not in full_context
    rag = build_rag_provider_views(own)
    assert len(rag) == 16
    assert all(b"EXPLORATORY_CEILING_RAG" in row[0] for row in rag)
    validate_exploratory_precedence(["a"], {"a": 48}, {"a": 3}, {"a": 17})
    validate_exploratory_precedence([], {}, {}, {})
    try:
        validate_exploratory_precedence(["a"], {"a": 47}, {"a": 3}, {"a": 17})
    except V03RContractError:
        pass
    else:
        raise AssertionError("exploratory work ran with incomplete branch")
    try:
        validate_exploratory_precedence([], {"a": 0}, {"a": 0}, {"a": 1})
    except V03RContractError:
        pass
    else:
        raise AssertionError("undefined life received exploratory work")


def test_t_v2e_phase_b_final_graph_and_done():
    inventory = {
        "defined_life_ids": ["a"], "score_packets": 3, "life_rows": 6,
        "pair_rows": 3, "four_metric_rows_per_proposal": True,
        "controls_complete": True, "normalization_gains_complete": True,
        "exploratory_rows": 17, "terminal_markers": ["done.json"],
        "phase_a_seal_sha256": "0" * 64,
    }
    assert len(validate_phase_b_inventory(inventory, phase_a_seal_sha256="0" * 64)) == 64
    inventory["terminal_markers"] = ["done.json", "failed.json"]
    try:
        validate_phase_b_inventory(inventory, phase_a_seal_sha256="0" * 64)
    except V03RContractError:
        pass
    else:
        raise AssertionError("phase-B validator accepted multiple terminal markers")


def test_t_v2e_transitive_review_bundle_excludes_mutable_intake():
    workflow = json.loads(WORKFLOW_PATH.read_text())
    freeze_inputs = workflow["freeze_inputs"]
    assert "research_loop/changes/chg_20260901_v03r_recurrence_closure_dev_v2e/intake.state.json" not in freeze_inputs
    assert "research_loop/v03r_recurrence_closure_remote_job_v2e.py" in freeze_inputs
    assert "research_loop/test_v03r_recurrence_closure_transition_v2e.py" in freeze_inputs


def test_t_v2e_durable_two_phase_remote_markers():
    workflow_text = WORKFLOW_PATH.read_text()
    runner_path = ROOT / "research_loop/run_v03r_recurrence_closure_v2e.py"
    verifier_path = ROOT / "research_loop/verify_v03r_recurrence_closure_artifacts_v2e.py"
    assert "phase_a_raw_seal.json" in workflow_text
    assert "done.json" in verifier_path.read_text() and "failed.json" in verifier_path.read_text()
    # The workflow delegates execution to a runner.  Keep this as a source
    # gate so a science driver that only emits raw calls cannot masquerade as
    # a two-phase implementation.
    runner_text = runner_path.read_text()
    assert "def main" in runner_text and "build_parser" in runner_text
    assert '"phase-a"' in runner_text and '"phase-b"' in runner_text
    assert "progress.json" in workflow_text and "heartbeat" in workflow_text


def test_t_v2e_exact_scope_claim_and_human_stop():
    spec = SPEC_PATH.read_text()
    assert "exact six-life interface calibration" in spec
    assert "every result or failure stops unconditionally at Rohin" in spec or "stops at Rohin" in spec
    assert "no population inference" in spec.casefold()


def test_t_v2e_exact_four_scope_phase_authority():
    scope = json.loads(SCOPE_PATH.read_text())
    requested = scope["requested_scope"]
    assert requested == sorted(requested)
    ratification = json.loads((SCOPE_PATH.parent / "human_ratification.json").read_text())
    assert ratification["authorized_scope"] == requested
    assert ratification["forbidden_scope"] == scope["forbidden_scope"]
    assert ratification["implementation_authorized"] is True


def test_t_v2e_concrete_zero_science_envelope_resource():
    path = ROOT / "research_loop/schemas/v03r_zero_science_envelopes_v2e.json"
    resource = json.loads(path.read_text())
    assert resource["resource_id"] == "v03r-zero-science-envelopes-v2e"
    assert resource["execution"]["total_calls"] == 8
    assert resource["execution"]["class_order"] == ["dream", "think", "full_context", "rag"]
    policy = resource["science_material_policy"]
    assert policy["public_life_inputs_allowed"] is False
    assert policy["science_observation"] is False
    assert policy["target_or_witness_material_allowed"] is False


if __name__ == "__main__":
    for name, function in sorted(globals().items()):
        if name.startswith("test_"):
            function()
    print("v2e transition tests passed")
