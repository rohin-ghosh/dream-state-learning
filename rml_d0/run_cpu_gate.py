"""Single public command for the authorized Stage-A CPU micro-preflight."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import resource
import sys
import time
from dataclasses import replace
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = Path(__file__).resolve().with_name("stage_a_report.json")
PREDECESSORS = {
    "candidate_b": (
        ROOT / "research_loop/plans/rml_d0_world_candidate_B.md",
        "bd2a3b2bc11dd0b7f9591266ca9b9094e89195a0af581e248bc09e41e481805b",
    ),
    "authorized_change": (
        ROOT / "research_loop/changes/chg_20260901_rml_d0_exact_v2/change.json",
        "bd3fc32b004047d3a3a9e7700193e9feb8f5850541741a4037bf5a1b8d91e748",
    ),
    "consensus": (
        ROOT / "research_loop/changes/chg_20260901_rml_d0_exact_v2/consensus.json",
        "41cfd553e9a27f6ab3c5343c0c6ce32b76f4f0b6ef1838d06f2f9e3c3f7be72c",
    ),
    "human_ratification": (
        ROOT / "research_loop/changes/chg_20260901_rml_d0_exact_v2/human_ratification.json",
        "99a51f736198e670c153c280d7d9658feebc56dfbfb1113204e9b3505ab6ed34",
    ),
    "scope_proposal": (
        ROOT / "research_loop/changes/chg_20260901_rml_d0_exact_v2/scope_proposal.json",
        "ae15bf148190b133c7f44252c1a2e5d5454f059b865fbd35f9f65bfbef7feb17",
    ),
}


def _sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _verify_predecessors() -> tuple[dict[str, str], list[dict[str, Any]]]:
    actual: dict[str, str] = {}
    failures: list[dict[str, Any]] = []
    for name, (path, expected) in PREDECESSORS.items():
        observed = _sha_file(path) if path.is_file() else "MISSING"
        actual[name] = observed
        if observed != expected:
            failures.append(
                {
                    "actual": observed,
                    "code": "NOT_RUN_WRONG_PREDECESSOR",
                    "expected": expected,
                    "name": name,
                }
            )
    return actual, failures


def _canonical_negative_goldens() -> list[str]:
    from .canonical import (
        CanonicalError,
        parse_record_bytes,
        record_bytes,
        strict_loads,
    )

    cases: list[tuple[str, Any]] = [
        ("duplicate_key", lambda: strict_loads(b'{"a":1,"a":2}')),
        ("float", lambda: strict_loads(b'{"a":1.5}')),
        ("null", lambda: strict_loads(b'{"a":null}')),
        ("non_nfc", lambda: strict_loads('{"a":"e\u0301"}')),
        (
            "unknown_key",
            lambda: record_bytes(
                "PublicAction",
                {"action_kind": "STOP", "arguments": {}, "extra": 1},
            ),
        ),
        (
            "lowercase_handle",
            lambda: record_bytes(
                "RecallGoal",
                {
                    "desired_coolant": {"inhibitor": "LEAN", "viscosity": "LOW"},
                    "goal_handle": "GOabcdefabcdef",
                    "goal_kind": "ONE_APPLY_COOLANT",
                },
            ),
        ),
        (
            "short_handle",
            lambda: record_bytes(
                "RecallGoal",
                {
                    "desired_coolant": {"inhibitor": "LEAN", "viscosity": "LOW"},
                    "goal_handle": "GO1234",
                    "goal_kind": "ONE_APPLY_COOLANT",
                },
            ),
        ),
        (
            "missing_lf",
            lambda: parse_record_bytes(
                "PublicAction", b'{"action_kind":"STOP","arguments":{}}'
            ),
        ),
        (
            "two_lf",
            lambda: parse_record_bytes(
                "PublicAction", b'{"action_kind":"STOP","arguments":{}}\n\n'
            ),
        ),
    ]
    rejected: list[str] = []
    for name, function in cases:
        try:
            function()
        except CanonicalError:
            rejected.append(name)
        else:
            raise AssertionError(f"canonical negative case survived: {name}")
    return rejected


def _public_action_goldens() -> dict[str, Any]:
    from .canonical import canonical_bytes
    from .targets import make_target
    from .world import (
        action_universe,
        initial_state,
        resolve_public_action,
        step,
        step_public,
    )

    spec = make_target(0, 0)
    actions = action_universe(spec)
    rendered = []
    for action in actions:
        record = action.public_record(spec.handles)
        if "item_index" in canonical_bytes(record).decode("utf-8"):
            raise AssertionError("internal item index leaked into PublicAction")
        if resolve_public_action(spec, record) != action:
            raise AssertionError("PublicAction did not round-trip")
        rendered.append(record)
    malformed = {
        "action_kind": "OBSERVE",
        "arguments": {"object_or_site": "MF000000000000"},
    }
    start = initial_state(spec)
    bad = step_public(spec, start, malformed)
    if bad.result_code != "ILLEGAL" or bad.state.coolant != start.coolant or bad.state.statuses != start.statuses:
        raise AssertionError("unknown public handle partially mutated state")
    direct = step(spec, start, actions[0])
    return {
        "closed_action_count": len(actions),
        "malformed_handle_no_partial_mutation": True,
        "rendered_sha256": hashlib.sha256(canonical_bytes(rendered)).hexdigest(),
        "sample_result_code": direct.result_code,
    }


def _peak_rss_bytes() -> int:
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(value if platform.system() == "Darwin" else value * 1024)


def _run_subject() -> tuple[dict[str, Any], dict[str, int]]:
    from . import (
        CANDIDATE_B_SHA256,
        CLAIM_FIREWALL,
        PROTOCOL,
        STAGE_A_LIMITS,
    )
    from .bayes import first_accept_toy_goldens
    from .canonical import canonical_bytes, canonical_goldens
    from .certificates import make_certificate, replay_certificate
    from .planner import (
        compare_literal_and_quotient,
        quotient_deletion_witnesses,
    )
    from .probes import (
        EXPECTED_VECTOR_DIGESTS,
        actual_vector_digests,
        mutation_kills,
    )
    from .rng import handle_metamorphic_goldens
    from .schema_reference import schema_chronology_golden
    from .isolation import evaluation_isolation_golden
    from .source import (
        balance_action_only_masses,
        complete_be_goldens,
        validate_balance_source,
    )
    from .targets import (
        bridge_goldens,
        j_cut_goldens,
        make_target,
        p_four_way_golden,
        recall_goldens,
        source_count_golden,
        target_goldens,
        transition_law_goldens,
        valve_balance_goldens,
    )
    from .world import canonical_plan, useful_pairs

    if CANDIDATE_B_SHA256 != PREDECESSORS["candidate_b"][1]:
        raise AssertionError("package Candidate-B binding changed")
    predicted = {
        "states": 220_000,
        "transitions": 1_300_000,
        "wall_ms": 55_000,
    }
    if predicted["transitions"] >= STAGE_A_LIMITS["transitions"] or STAGE_A_LIMITS["workers"] != 1:
        raise AssertionError("before-dispatch resource preflight failed")

    actual_digests = actual_vector_digests()
    if set(actual_digests) != set(EXPECTED_VECTOR_DIGESTS):
        raise AssertionError("oracle vector inventory is incomplete")
    vector_rows = {
        key: {
            "actual": actual_digests[key],
            "expected": EXPECTED_VECTOR_DIGESTS[key],
            "matched": actual_digests[key] == EXPECTED_VECTOR_DIGESTS[key],
        }
        for key in sorted(EXPECTED_VECTOR_DIGESTS)
    }
    if not all(row["matched"] for row in vector_rows.values()):
        raise AssertionError("an independent vector digest differs")

    canonical_rows = canonical_goldens()
    canonical_negative = _canonical_negative_goldens()
    transition = transition_law_goldens()
    public_actions = _public_action_goldens()
    recall = recall_goldens()
    target_rows, target_counts = target_goldens()
    bridges = bridge_goldens()
    source = complete_be_goldens()
    source_counts = source_count_golden()
    valve = valve_balance_goldens()
    if not validate_balance_source(source, balance_action_only_masses(0, 4)):
        raise AssertionError("four-mode balance/source joint validator failed")
    p = p_four_way_golden()
    bayes = first_accept_toy_goldens()
    j_rows, j_counts = j_cut_goldens()
    deletion = quotient_deletion_witnesses(make_target(0, 0))
    handle_meta = handle_metamorphic_goldens()
    schema_chronology = schema_chronology_golden()
    isolation = evaluation_isolation_golden()

    literal_rows: list[dict[str, Any]] = []
    literal_states = 0
    literal_transitions = 0
    certificate_roots: list[dict[str, Any]] = []
    for initial in range(4):
        for mode in range(4):
            authentic = make_target(initial, mode)
            for side, spec in (("H", authentic), ("TWIN", authentic.twin())):
                comparison = compare_literal_and_quotient(spec, 6)
                literal_states += comparison.states
                literal_transitions += comparison.transitions
                target_row = target_rows[initial * 4 + mode]
                side_row = next(row for row in target_row["sides"] if row["side"] == side)
                literal_rows.append(
                    {
                        "depth_summaries": list(comparison.depth_summaries),
                        "initial_coolant": initial,
                        "literal_vector_sha256": comparison.literal_vector_sha256,
                        "minimum_depth": side_row["minimum_depth"],
                        "shortest_tie_count": side_row["shortest_tie_count"],
                        "side": side,
                        "states": comparison.states,
                        "transitions": comparison.transitions,
                        "valve_truth": mode,
                    }
                )
                pair = next(iter(useful_pairs(spec)))
                certificate = make_certificate(spec, canonical_plan(pair, spec.valve_truth))
                if not replay_certificate(spec, certificate):
                    raise AssertionError("compact certificate did not replay")
                if replay_certificate(replace(spec, exchanger=spec.exchanger ^ 1), certificate):
                    raise AssertionError("certificate accepted mutated truth")
                certificate_roots.append(
                    {
                        "initial_coolant": initial,
                        "root_sha256": certificate["root_sha256"],
                        "side": side,
                        "valve_truth": mode,
                    }
                )

    mutations = mutation_kills()
    counters = {
        "states": target_counts.states + j_counts.states + literal_states,
        "transitions": target_counts.transitions + j_counts.transitions + literal_transitions,
    }
    literal_aggregate = hashlib.sha256(canonical_bytes(literal_rows)).hexdigest()
    values = {
        "bayes": bayes,
        "bridge_count": len(bridges),
        "canonical_goldens": canonical_rows,
        "canonical_negative_rejections": canonical_negative,
        "certificate_count": len(certificate_roots),
        "certificate_roots": certificate_roots,
        "deletion_witnesses": deletion,
        "fixture_counts": {
            "bridge_rows": len(bridges),
            "j_base_sides": len(j_rows),
            "j_cut_variants": len(j_rows) * 4,
            "k0_primary_targets": 0,
            "k0_recall_fixtures": 0,
            "literal_target_sides": len(literal_rows),
            "p_completions": len(p["integer_masses"]),
            "recall_fixtures": len(recall),
            "target_pairs": len(target_rows),
            "target_sides": sum(len(row["sides"]) for row in target_rows),
            "valve_omitted_modes": len(valve["cases"]),
        },
        "handle_tape_metamorphics": handle_meta,
        "pair_common_target_mapping_verified": True,
        "evaluation_isolation": isolation,
        "literal_history_aggregate_sha256": literal_aggregate,
        "literal_history_vectors": literal_rows,
        "mutation_dispositions": mutations,
        "oracle_vectors": vector_rows,
        "p_atoms_only": p,
        "preflight": {
            "actual_counters_within_limit": counters["transitions"] < STAGE_A_LIMITS["transitions"],
            "before_dispatch": True,
            "predicted": predicted,
        },
        "protocol_binding": {"candidate_b": CANDIDATE_B_SHA256, "protocol": PROTOCOL},
        "public_actions": public_actions,
        "recall_fixtures": recall,
        "scope_calls": {"gpu": 0, "model": 0, "network": 0},
        "schema_chronology": schema_chronology,
        "source": source,
        "source_symbolic_counts": source_counts,
        "target_goldens": target_rows,
        "transition_law": transition,
        "valve_balance": valve,
        "verdict_label": CLAIM_FIREWALL,
    }
    return values, counters


def _write_report(
    predecessors: dict[str, str],
    values: dict[str, Any],
    failures: list[dict[str, Any]],
    counters: dict[str, int],
    started: float,
) -> tuple[dict[str, Any], int]:
    from . import CLAIM_FIREWALL, PROTOCOL, STAGE, STAGE_A_LIMITS
    from .canonical import record_bytes, record_hash

    wall_ms = int((time.perf_counter() - started) * 1000)
    resource_record = {
        "pair_attempts": 16,
        "peak_rss_bytes": _peak_rss_bytes(),
        "sealed_bytes": 0,
        "stage": STAGE,
        "states": counters["states"],
        "target_attempts": 32,
        "temp_bytes": values.get("evaluation_isolation", {}).get("peak_temp_bytes", 0),
        "transitions": counters["transitions"],
        "wall_ms": wall_ms,
        "workers": 1,
    }
    for key, limit in STAGE_A_LIMITS.items():
        if key in resource_record and resource_record[key] > limit:
            failures.append(
                {
                    "actual": resource_record[key],
                    "code": "RESOURCE_LIMIT",
                    "limit": limit,
                    "name": key,
                }
            )
    report: dict[str, Any] = {}
    for _ in range(4):
        resource_hash = record_hash("ResourceRecord", resource_record)
        report = {
            "claim_firewall": CLAIM_FIREWALL,
            "failures": failures,
            "gate_values": {**values, "resource_record": resource_record},
            "passed": not failures,
            "predecessor_hashes": predecessors,
            "protocol": PROTOCOL,
            "resource_hash": resource_hash,
            "split_hashes": {},
        }
        payload = record_bytes("GateReport", report)
        size = len(payload)
        if resource_record["sealed_bytes"] == size:
            break
        resource_record["sealed_bytes"] = size
    REPORT_PATH.write_bytes(record_bytes("GateReport", report))
    return report, REPORT_PATH.stat().st_size


def main(argv: list[str] | None = None) -> int:
    global __package__
    parser = argparse.ArgumentParser(description="Run the RML-D0 Stage-A CPU micro-preflight")
    parser.add_argument("--stage-a", action="store_true", required=True)
    args = parser.parse_args(argv)
    del args
    started = time.perf_counter()
    predecessors, predecessor_failures = _verify_predecessors()
    if predecessor_failures:
        print(json.dumps({"failures": predecessor_failures, "passed": False}, sort_keys=True))
        return 2
    # Direct-file invocation reaches this point without importing rml_d0.
    # Activate relative package imports only after every predecessor matches.
    if not __package__:
        sys.path.insert(0, str(ROOT))
        __package__ = "rml_d0"
    failures: list[dict[str, Any]] = []
    values: dict[str, Any] = {}
    counters = {"states": 0, "transitions": 0}
    try:
        values, counters = _run_subject()
    except Exception as exc:  # fail closed into the durable report
        failures.append(
            {"code": "STAGE_A_ASSERTION", "message": f"{type(exc).__name__}: {exc}"}
        )
    report, sealed_bytes = _write_report(
        predecessors, values, failures, counters, started
    )
    summary = {
        "passed": report["passed"],
        "peak_rss_bytes": report["gate_values"]["resource_record"]["peak_rss_bytes"],
        "report": str(REPORT_PATH),
        "sealed_bytes": sealed_bytes,
        "sha256": _sha_file(REPORT_PATH),
        "states": counters["states"],
        "transitions": counters["transitions"],
        "wall_ms": report["gate_values"]["resource_record"]["wall_ms"],
    }
    print(json.dumps(summary, sort_keys=True))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
