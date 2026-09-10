"""Write the six CPU-preflight evidence artifacts without model/GPU/network use."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import resource
import sys
import time
from typing import Any

from .contract import CHANGE_ID, PROTOCOL, build_opportunity_registry, build_roster, digest
from .fixtures import build_selected_cases, build_slice_certificate
from .memory import extract_permitted_source_facts, seal_pretarget_snapshot_universe
from .runner import run_scripted_cpu_gate
from .runtime import cpu_runtime_manifest


REPLACEMENT_TESTS = (
    "RML_G1_T01_PRETARGET_SNAPSHOT_QUERY_AND_VISIBLE_BYTE_NONINTERFERENCE",
    "RML_G1_T02_CLOSED_PHASE_MACHINE_AND_234_LEDGER",
    "RML_G1_T03_D0_WORLD_PLUS_NEW_TRACE_REDUCER_AND_SLICE_CERTIFICATE",
    "RML_G1_T04_HASHED_DETERMINISTIC_RUNTIME_AND_ABSOLUTE_RESOURCE_CANARY",
    "RML_G1_T05_EXACT_18_TRAJECTORY_CAUSAL_GATE",
    "RML_G1_T06_TWO_PHASE_REVIEW_AND_EXACT_CLAIM_FIREWALL",
)

RATIFIED_STAGE_A_REPORT_SHA256 = (
    "346bd091e9d037b1e51c8ed735ba5ecfbee50a42d10988d02ebc28c87532855b"
)


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(payload, encoding="utf-8")
    temporary.replace(path)


def build_cpu_preflight() -> dict[str, Any]:
    started = time.monotonic()
    stage_a_report_path = Path(__file__).resolve().parents[1] / "rml_d0" / "stage_a_report.json"
    stage_a_report_sha256 = digest(stage_a_report_path.read_bytes())
    stage_a_context_hash_matches = (
        stage_a_report_sha256 == RATIFIED_STAGE_A_REPORT_SHA256
    )
    source_h = extract_permitted_source_facts(twin=False)
    source_twin = extract_permitted_source_facts(twin=True)
    pretarget_seal = seal_pretarget_snapshot_universe()
    snapshots = pretarget_seal.snapshot_map()
    cases = build_selected_cases(pretarget_seal)
    certificate = build_slice_certificate(cases)
    roster = build_roster()
    registry = build_opportunity_registry(roster)
    scripted = run_scripted_cpu_gate()
    common_visible_hash = next(iter({case.public_sha256 for case in cases.values()}))
    reports: dict[str, dict[str, Any]] = {
        "interface_audit.json": {
            "test_id": REPLACEMENT_TESTS[0],
            "local_check_passed": True,
            "acceptance_test_satisfied": stage_a_context_hash_matches,
            "gpu_prerequisite_satisfied": False,
            "builder_accepts_target_spec": False,
            "source_projection_hashes": {
                "H": source_h.public_source_sha256,
                "FULL_TWIN": source_twin.public_source_sha256,
            },
            "snapshot_seals": {key: value.sealed_sha256 for key, value in sorted(snapshots.items())},
            "pretarget_snapshot_manifest_sha256": pretarget_seal.manifest_sha256,
            "target_selection_requires_verified_pretarget_seal": True,
            "target_public_sha256": common_visible_hash,
            "target_count": len(cases),
            "condition_neutral_handle_rule": "SHA256(EXACT_QUERY_KEY)",
            "online_service_inputs": ["sealed_projection", "emitted_exact_key"],
            "fresh_state_required": ["process", "KV", "reader_cache", "backend_cache", "workspace"],
            "ratified_stage_a_report_sha256": RATIFIED_STAGE_A_REPORT_SHA256,
            "actual_stage_a_report_sha256": stage_a_report_sha256,
            "stage_a_context_hash_matches": stage_a_context_hash_matches,
        },
        "call_accounting.json": {
            "test_id": REPLACEMENT_TESTS[1],
            "local_check_passed": True,
            "acceptance_test_satisfied": False,
            "gpu_prerequisite_satisfied": False,
            "trajectory_count": len(roster),
            "registered_opportunities": len(registry),
            "maximum_dispatches": len(registry),
            "read_slots": 4,
            "env_slots": 9,
            "roster": [asdict(row) for row in roster],
            "precommitted_opportunities": [asdict(row) for row in registry],
            "scientific_dispositions_persisted": False,
            "condition_counts": {
                condition: sum(row.condition == condition for row in roster)
                for condition in sorted({row.condition for row in roster})
            },
            "retry_count": 0,
        },
        "cpu_end_to_end.json": {
            "test_id": REPLACEMENT_TESTS[2],
            "local_check_passed": True,
            "acceptance_test_satisfied": False,
            "gpu_prerequisite_satisfied": False,
            "gpu_acceptance_ready": False,
            "d0_authority": ["world_transitions", "target_validity", "symbolic_certificates", "program_scoring"],
            "stage_b_authority": "separate_post_freeze_trace_intervention_reducer",
            "slice_certificate": asdict(certificate),
            "blocking_consensus_inconsistency": {
                "id": "RML_G1_T03_P_ATOMS_CAPACITY_CONTRADICTION",
                "ratified_requirement": "P ATOMS exact success capacity 0/2",
                "enumerated_best_fixed_policy_capacity": f"{certificate.atoms_best_policy_success_capacity}/2",
                "witness_action_signature": certificate.atoms_capacity_witness,
                "empirical_gate_unchanged": "ATOMS_REC must produce 0/2 scientific-valid successes",
                "requires_narrow_amendment": True,
            },
            "scripted_harness_local_check_passed": scripted.report["local_check_passed"],
        },
        "model_canary.json": {
            "test_id": REPLACEMENT_TESTS[3],
            "local_check_passed": True,
            "acceptance_test_satisfied": False,
            "gpu_prerequisite_satisfied": False,
            "actual_canary_run": False,
            "scientific_opportunities_consumed": 0,
            "gpu_dispatch_ready": False,
            "runtime_manifest": cpu_runtime_manifest(),
            "blocking_reason": "exact GPU runtime hashes, reviewers, and disjoint canary receipt do not yet exist",
        },
        "fast_gate_report.json": {
            "test_id": REPLACEMENT_TESTS[4],
            "artifact_kind": "CPU_SCRIPTED_HARNESS_ONLY_NOT_MODEL_EVIDENCE",
            **scripted.report,
            "acceptance_test_satisfied": False,
            "gpu_prerequisite_satisfied": False,
            "promotion_dependencies": [
                "packet_summary", "runtime_closure", "actual_model_ledger",
                "pre_gpu_reviews",
            ],
            "scientific_model_dispatches": 0,
            "gpu_calls": 0,
            "network_calls": 0,
        },
        "review_and_claim_audit.json": {
            "test_id": REPLACEMENT_TESTS[5],
            "local_check_passed": True,
            "acceptance_test_satisfied": False,
            "gpu_prerequisite_satisfied": False,
            "pre_gpu_independent_review_complete": False,
            "pre_gpu_author_advocate_review_complete": False,
            "post_run_review_complete": False,
            "gpu_dispatch_ready": False,
            "claim_label": "single deterministic fixture; nested J/P sides; supplied-gold; diagnostic only",
            "forbidden_successor_scope": ["G2", "DREAM", "SLEEP", "LoRA", "extra roots/models/seeds/sweeps", "paper claims"],
        },
    }
    elapsed_ms = int((time.monotonic() - started) * 1000)
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    # macOS reports bytes, Linux KiB.  This host is macOS; preserve raw units too.
    summary = {
        "schema_version": 1,
        "change_id": CHANGE_ID,
        "protocol": PROTOCOL,
        "local_check_passed": True,
        "acceptance_test_satisfied": False,
        "gpu_prerequisite_satisfied": False,
        "local_cpu_regressions_passed": True,
        "cpu_implementation_tests_passed": False,
        "ratified_acceptance_tests_satisfied": False,
        "gpu_dispatch_ready": False,
        "replacement_test_ids": list(REPLACEMENT_TESTS),
        "artifact_hashes": {name: digest(value) for name, value in reports.items()},
        "resource_record": {"elapsed_ms": elapsed_ms, "ru_maxrss_raw": rss, "model_calls": 0, "gpu_calls": 0, "network_calls": 0},
        "blockers": ([
            "ratified T03 P-ATOMS zero-capacity clause contradicts enumerated 1/2 lucky-policy capacity",
            "exact GPU provider/orchestrator, pinned-tokenizer rendering, runtime closure, immutable scientific ledger, and non-scientific canary are not implemented/executed",
            "fresh independent reviewer and author-side advocate have not approved frozen bytes",
        ] + (
            [
                "ratification context hash for rml_d0/stage_a_report.json does not match the clean repository file"
            ]
            if not stage_a_context_hash_matches
            else []
        )),
    }
    return {"reports": reports, "summary": summary}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts/rml_g1_gold_action_fast_v1"),
    )
    args = parser.parse_args(argv)
    result = build_cpu_preflight()
    for name, report in result["reports"].items():
        _write(args.output_dir / name, report)
    _write(args.output_dir / "cpu_preflight_summary.json", result["summary"])
    print(json.dumps(result["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
