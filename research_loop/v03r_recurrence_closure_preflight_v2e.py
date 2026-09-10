"""Fail-closed local gates for the frozen v0.3-R recurrence calibration.

This module is deliberately provider-free.  ``static`` validates repository
bytes and declared contracts, ``materialize-review`` creates immutable review
evidence, and ``release`` proves that two approvals covered the same context.
No command in this file can load a model, sync a host, or start science.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import sys
from typing import Any, Iterable

from .architecture_intake import validate_authorized_intake, validate_change
from .freeze import create as create_lock, verify as verify_lock
from .freeze_closure import assert_workflow_freeze_closed
from .io import atomic_write_json, fingerprint, load_json, sha256_file, utc_now
from .review_binding import verify_binding


CHANGE_ID = "chg_20260901_v03r_recurrence_closure_dev_v2e"
CHANGE_DIR = Path("research_loop/changes") / CHANGE_ID
INTAKE = CHANGE_DIR / "intake.state.json"
SCOPE = CHANGE_DIR / "scope_proposal.json"
CHANGE = CHANGE_DIR / "change.json"
ENVELOPE_SHA256 = "8b7b8dd82d304cb83638b13207cb6c05d255b874dc4d363a3299202bcc3a06cd"
MODEL = "Qwen/Qwen2.5-32B-Instruct"
REVISION = "5ede1c97bbab6ce5cda5812749b4c0bdf79b18dd"
REQUIRED_SCOPE = (
    "analysis:bound_postcommit_v03r_closure_v2e",
    "gpu:v03r_recurrence_closure_dev_v2e",
    "implementation:v03r_recurrence_closure_dev_v2e",
    "testing:pre_gpu_v03r_recurrence_closure_dev_v2e",
)
EXPECTED_NUMBERS = {
    "pairs": 1000,
    "shared_dream_calls": 514,
    "max_defined_lives": 6,
    "branch_dream_calls_per_defined_life": 48,
    "max_recurrent_dream_calls": 802,
    "max_think0_calls": 72,
    "exploratory_calls_per_defined_life": 17,
    "max_exploratory_calls": 102,
    "selector_traces_per_defined_life": 48,
    "memory1_per_defined_life": 3,
    "dream_max_output_tokens": 256,
    "canonical_text_max_bytes": 192,
    "zero_science_calls_per_class": 2,
}


class PreflightError(RuntimeError):
    pass


def _safe(root: Path, value: Path | str) -> Path:
    relative = PurePosixPath(str(value))
    if relative.is_absolute() or ".." in relative.parts:
        raise PreflightError(f"path is not repository-relative: {value}")
    candidate = (root / Path(relative.as_posix())).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise PreflightError(f"path escapes repository: {value}") from exc
    return candidate


def _canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _require(flag: bool, message: str) -> None:
    if not flag:
        raise PreflightError(message)


def _load_object(path: Path, label: str) -> dict[str, Any]:
    value = load_json(path)
    if not isinstance(value, dict):
        raise PreflightError(f"{label} must be a JSON object")
    return value


def _validate_envelopes(path: Path, expected_sha: str, calls_per_class: int) -> dict[str, Any]:
    _require(path.is_file(), f"zero-science envelope is missing: {path}")
    _require(sha256_file(path) == expected_sha == ENVELOPE_SHA256, "zero-science envelope hash mismatch")
    resource = _load_object(path, "zero-science envelope")
    _require(resource.get("resource_id") == "v03r-zero-science-envelopes-v2e", "wrong envelope resource ID")
    _require(resource.get("model_contract", {}).get("model") == MODEL, "envelope model mismatch")
    _require(resource.get("model_contract", {}).get("revision") == REVISION, "envelope revision mismatch")
    execution = resource.get("execution", {})
    _require(execution.get("calls_per_class") == calls_per_class == 2, "envelope class cardinality mismatch")
    _require(execution.get("total_calls") == 8, "envelope total call count mismatch")
    _require(execution.get("class_order") == ["dream", "think", "full_context", "rag"], "envelope class order mismatch")
    expected_limits = {
        "dream": (2048, 256), "think": (8192, 128),
        "full_context": (8192, 256), "rag": (2048, 256),
    }
    seen: list[tuple[str, int]] = []
    for class_row in resource.get("classes", []):
        class_id = class_row.get("class_id")
        _require(class_id in expected_limits, f"unknown envelope class: {class_id}")
        _require((class_row.get("input_token_limit"), class_row.get("output_token_limit")) == expected_limits[class_id], f"wrong limits for {class_id}")
        calls = class_row.get("calls")
        _require(isinstance(calls, list) and len(calls) == 2, f"wrong calls for {class_id}")
        for call in calls:
            index = call.get("call_index")
            _require(index in (0, 1), f"wrong call index for {class_id}")
            prefix = resource["generator"]["prefix_template"].format(class_id=class_id, call_index=index)
            raw = (prefix + resource["generator"]["filler_unit"] * call["repetition_count"] + resource["generator"]["suffix"]).encode("ascii")
            _require(len(raw) == call["byte_count"], f"byte count mismatch for {class_id}/{index}")
            _require(_sha(raw) == call["input_bytes_sha256"], f"byte hash mismatch for {class_id}/{index}")
            seed = hashlib.sha256(b"v2d-zero-science-seed\0" + class_id.encode("ascii") + b"\0" + str(index).encode("ascii")).hexdigest()
            _require(seed == call["logical_seed_sha256"], f"seed mismatch for {class_id}/{index}")
            seen.append((class_id, index))
    _require(seen == [(name, index) for name in execution["class_order"] for index in (0, 1)], "envelope call order mismatch")
    policy = resource.get("science_material_policy", {})
    _require(policy.get("public_life_inputs_allowed") is False and policy.get("science_observation") is False, "envelope is not synthetic-only")
    return {"resource_id": resource["resource_id"], "calls": len(seen), "sha256": expected_sha}


def _validate_workflow_contract(root: Path, workflow_path: Path, args: argparse.Namespace) -> tuple[dict[str, Any], dict[str, Any]]:
    workflow = _load_object(workflow_path, "workflow")
    _require(workflow.get("name") == "v03r-recurrence-closure-dev-v2e", "wrong workflow name")
    declaration = workflow.get("architecture_intake", {})
    _require(declaration.get("mode") == "material_change", "workflow is not a material change")
    _require(declaration.get("state") == INTAKE.as_posix(), "workflow intake path mismatch")
    _require(declaration.get("requested_scope") == list(REQUIRED_SCOPE), "workflow requested scope mismatch")
    freeze_inputs = workflow.get("freeze_inputs")
    _require(isinstance(freeze_inputs, list) and freeze_inputs, "workflow has no freeze inputs")
    _require(INTAKE.as_posix() not in freeze_inputs, "mutable intake is frozen into reviewer evidence")
    _require(len(freeze_inputs) == len(set(freeze_inputs)), "duplicate freeze inputs")
    missing = [value for value in freeze_inputs if not _safe(root, value).is_file()]
    _require(not missing, f"declared freeze inputs missing: {missing}")
    closure = assert_workflow_freeze_closed(root, workflow_path)
    nodes = workflow.get("nodes", {})
    _require(nodes.get("v2e_ascii_alias_provisional_dream", {}).get("next") == "v2e_defined_life_exploratory_ceilings", "v2e branch-to-exploratory edge is absent")
    _require(nodes.get("v2e_defined_life_exploratory_ceilings", {}).get("next") == "v2e_phase_a_raw_seal", "v2e exploratory-to-phase-A edge is absent")
    return workflow, closure.to_dict()


def _validate_authority(root: Path, required_scope: Iterable[str] = REQUIRED_SCOPE) -> dict[str, Any]:
    validated = validate_authorized_intake(root, _safe(root, INTAKE))
    requested = list(required_scope)
    _require(requested == list(REQUIRED_SCOPE), "required scopes differ from the canonical four")
    ratification = validated["ratification"]
    proposal = _load_object(_safe(root, SCOPE), "scope proposal")
    _require(ratification["authorized_scope"] == requested == proposal["requested_scope"], "ratification authorized scope mismatch")
    _require(ratification["forbidden_scope"] == proposal["forbidden_scope"], "ratification forbidden scope mismatch")
    _require(ratification.get("implementation_authorized") is True, "implementation is not authorized")
    return validated


def static_preflight(args: argparse.Namespace) -> dict[str, Any]:
    root = args.root.resolve()
    if args.forbid_provider:
        forbidden_loaded = sorted(name for name in sys.modules if name.endswith("model_provider_boundary") or name.endswith("run_v03r_recurrence_closure_v2e"))
        _require(not forbidden_loaded, f"provider/runner imported during static preflight: {forbidden_loaded}")
    _require(args.model == MODEL and args.revision == REVISION, "model/revision mismatch")
    _require(args.expected_device_name == "NVIDIA H100 NVL" and args.minimum_total_memory_mib == 95000, "hardware declaration mismatch")
    _require(args.disable_prefix_caching and args.disable_request_truncation, "cache/truncation must be disabled")
    for field, expected in EXPECTED_NUMBERS.items():
        _require(getattr(args, field) == expected, f"{field} must equal {expected}")
    workflow_path = _safe(root, args.workflow)
    workflow, closure = _validate_workflow_contract(root, workflow_path, args)
    authority = _validate_authority(root)
    change = validate_change(root, _safe(root, CHANGE))
    tests = change.get("acceptance_tests", [])
    _require(len(tests) == 26 and len({row["test_id"] for row in tests}) == 26, "v2e must retain exactly 26 unique acceptance tests")
    envelope = _validate_envelopes(_safe(root, args.zero_science_envelope_resource), args.zero_science_envelope_sha256, args.zero_science_calls_per_class)
    # Validate only the six named public prefixes.  No heldout/final-goal API is
    # called here; the broad 1000-pair population audit already ran in the CPU
    # test node and is declared, not repeated, by this provider-free gate.
    from lands.model import WorldConfig
    from lands.v03r import CounterfactualConfluenceV03R
    schedules = []
    for seed in range(3):
        for twin in (0, 1):
            world = CounterfactualConfluenceV03R(WorldConfig(seed=seed), latent_bit=twin)
            packet = world.precheckpoint_export("aligned")
            _require("final_goal" not in packet and "answer" not in packet, "precheckpoint packet leaked a final goal")
            schedules.append(world.schedule_manifest())
    wake = sum(row["wake_events"] for row in schedules)
    reactivate = sum(row["reactivate_events"] for row in schedules)
    _require(wake + reactivate + 16 * 6 == 514, "six-life shared prefix does not equal 514")
    return {
        "static_integrity": "pass",
        "verified_at": utc_now(),
        "workflow_sha256": sha256_file(workflow_path),
        "freeze_closure": closure,
        "intake_state_sha256": sha256_file(_safe(root, INTAKE)),
        "ratification_sha256": sha256_file(authority["paths"]["ratification"]),
        "acceptance_tests": 26,
        "population_audit_pairs_preceding_test_gate": args.pairs,
        "six_public_lives": len(schedules),
        "envelope": envelope,
    }


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = b"".join(_canonical_json(row) + b"\n" for row in rows)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_bytes(data)
    temporary.replace(path)


def materialize_review(args: argparse.Namespace) -> dict[str, Any]:
    root = args.root.resolve()
    workflow_path = _safe(root, args.workflow)
    workflow, closure = _validate_workflow_contract(root, workflow_path, args)
    authority = _validate_authority(root, args.required_scope)
    _require(args.exclude_intake_from_review, "mutable intake exclusion is mandatory")
    freeze_inputs = [Path(value) for value in workflow["freeze_inputs"]]
    _require(INTAKE not in freeze_inputs, "mutable intake entered freeze inputs")
    closure_doc = {
        **closure,
        "artifact_type": "v03r_v2e_freeze_closure",
        "run_id": args.run_id,
        "created_at": utc_now(),
        "implementation_testing_complete": True,
        "mutable_intake_excluded": True,
    }
    atomic_write_json(args.closure_out, closure_doc)
    all_hashes = fingerprint(freeze_inputs, root)
    resource_rows = [
        {"path": path, "sha256": digest, "kind": "python" if path.endswith(".py") else "resource"}
        for path, digest in sorted(all_hashes.items())
    ]
    resource_doc = {
        "schema_version": 1,
        "artifact_type": "v03r_v2e_resource_closure",
        "run_id": args.run_id,
        "created_at": utc_now(),
        "closed": True,
        "resource_count": len(resource_rows),
        "resources": resource_rows,
    }
    atomic_write_json(args.resource_out, resource_doc)
    evidence_rows = [
        {"schema_version": 1, "run_id": args.run_id, **row}
        for row in resource_rows
    ]
    _write_jsonl(args.evidence_bundle_out, evidence_rows)
    rat_path = authority["paths"]["ratification"]
    consensus_path = authority["paths"]["consensus"]
    evidence = authority["ratification"]["authorization_evidence"]
    binding = {
        "schema_version": 1,
        "artifact_type": "v03r_v2e_ratification_binding",
        "run_id": args.run_id,
        "change_id": CHANGE_ID,
        "created_at": utc_now(),
        "intake_state_path": INTAKE.as_posix(),
        "intake_state_sha256_at_materialization": sha256_file(_safe(root, INTAKE)),
        "ratification_path": str(Path(rat_path).resolve().relative_to(root)),
        "ratification_sha256": sha256_file(rat_path),
        "consensus_sha256": sha256_file(consensus_path),
        "authorization_evidence": evidence,
        "authorized_scope": authority["ratification"]["authorized_scope"],
        "forbidden_scope": authority["ratification"]["forbidden_scope"],
        "implementation_testing_complete": True,
        "analysis_phase": "postcommit_only",
        "gpu_first_use": "zero_science_preflight",
    }
    atomic_write_json(args.ratification_binding_out, binding)
    lock = create_lock(root, args.create_lock, [path.as_posix() for path in freeze_inputs])
    return {
        "review_bundle_closed": True,
        "run_id": args.run_id,
        "lock_sha256": sha256_file(args.create_lock),
        "closure_sha256": sha256_file(args.closure_out),
        "resource_closure_sha256": sha256_file(args.resource_out),
        "evidence_bundle_sha256": sha256_file(args.evidence_bundle_out),
        "ratification_binding_sha256": sha256_file(args.ratification_binding_out),
        "frozen_files": len(lock["files"]),
    }


def _verify_resource_doc(root: Path, path: Path) -> dict[str, Any]:
    doc = _load_object(path, "resource closure")
    _require(doc.get("closed") is True, "resource closure is not closed")
    rows = doc.get("resources")
    _require(isinstance(rows, list) and doc.get("resource_count") == len(rows), "resource closure count mismatch")
    seen: set[str] = set()
    for row in rows:
        relative = row["path"]
        _require(relative not in seen, f"duplicate resource: {relative}")
        seen.add(relative)
        _require(relative != INTAKE.as_posix(), "mutable intake entered resources")
        _require(sha256_file(_safe(root, relative)) == row["sha256"], f"resource changed: {relative}")
    return doc


def _verify_evidence(root: Path, path: Path, resources: dict[str, Any]) -> None:
    lines = path.read_text(encoding="ascii").splitlines()
    expected = resources["resources"]
    _require(len(lines) == len(expected), "review evidence cardinality mismatch")
    for line, resource in zip(lines, expected):
        row = json.loads(line)
        _require(row["path"] == resource["path"] and row["sha256"] == resource["sha256"], "review evidence/resource mismatch")
        _require(row["path"] != INTAKE.as_posix(), "mutable intake entered review evidence")


def release(args: argparse.Namespace) -> dict[str, Any]:
    root = args.root.resolve()
    workflow_path = _safe(root, args.workflow)
    workflow, live_closure = _validate_workflow_contract(root, workflow_path, args)
    authority = _validate_authority(root, args.required_scope)
    _require(args.assert_implementation_testing_complete_before_gpu, "implementation/test completion assertion required")
    _require(args.assert_identical_review_context, "identical review context assertion required")
    _require(args.assert_intake_excluded_from_review, "intake exclusion assertion required")
    verify_lock(root, args.lock)
    closure = _load_object(args.closure, "freeze closure")
    _require(closure.get("closed") is True and closure.get("implementation_testing_complete") is True, "freeze closure/test completion failed")
    _require(closure.get("reachable_python") == live_closure.get("reachable_python"), "freeze closure changed")
    resources = _verify_resource_doc(root, args.resources)
    _verify_evidence(root, args.evidence_bundle, resources)
    binding = _load_object(args.ratification_binding, "ratification binding")
    _require(binding.get("change_id") == CHANGE_ID, "ratification binding change mismatch")
    _require(binding.get("ratification_sha256") == sha256_file(authority["paths"]["ratification"]), "ratification bytes changed")
    _require(binding.get("consensus_sha256") == authority["ratification"]["consensus_sha256"], "consensus binding changed")
    _require(binding.get("authorized_scope") == list(REQUIRED_SCOPE), "bound scope mismatch")
    _require(binding.get("forbidden_scope") == authority["ratification"]["forbidden_scope"], "bound forbidden scope mismatch")
    fable = _load_object(args.fable_review, "independent review binding")
    sol = _load_object(args.sol_review, "advocate review binding")
    verify_binding(root, args.fable_review, required_verdict="approve")
    verify_binding(root, args.sol_review, required_verdict="approve")
    nodes = workflow["nodes"]
    fable_context = nodes["fresh_independent_v2e_review"]["context_files"]
    sol_context = nodes["fresh_author_science_advocate_v2e"]["context_files"]
    _require(fable_context == sol_context, "reviewer context declarations differ")
    _require(INTAKE.as_posix() not in fable_context, "mutable intake entered reviewer context")
    expected = fingerprint([Path(value) for value in fable_context], root)
    for label, review in (("fable", fable), ("sol", sol)):
        reviewed = review.get("reviewed_files", {})
        actual_context = {path: reviewed.get(path) for path in expected}
        _require(actual_context == expected, f"{label} review did not bind the exact common context")
    return {
        "release_closed": True,
        "released_at": utc_now(),
        "lock_sha256": sha256_file(args.lock),
        "ratification_binding_sha256": sha256_file(args.ratification_binding),
        "review_context_files": len(expected),
        "next_permitted_action": "sync_reviewed_bytes_then_zero_science_preflight",
    }


def _common_static(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--workflow", type=Path, required=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    static = sub.add_parser("static")
    _common_static(static)
    static.add_argument("--pairs", type=int, required=True)
    static.add_argument("--model", required=True)
    static.add_argument("--revision", required=True)
    static.add_argument("--expected-device-name", required=True)
    static.add_argument("--minimum-total-memory-mib", type=int, required=True)
    for name in EXPECTED_NUMBERS:
        if name != "pairs":
            static.add_argument("--" + name.replace("_", "-"), type=int, required=True)
    static.add_argument("--zero-science-envelope-resource", type=Path, required=True)
    static.add_argument("--zero-science-envelope-sha256", required=True)
    static.add_argument("--disable-prefix-caching", action="store_true")
    static.add_argument("--disable-request-truncation", action="store_true")
    static.add_argument("--forbid-provider", action="store_true")

    materialize = sub.add_parser("materialize-review")
    _common_static(materialize)
    materialize.add_argument("--run-id", required=True)
    materialize.add_argument("--intake-state", type=Path, required=True)
    materialize.add_argument("--required-scope", action="append", required=True)
    materialize.add_argument("--closure-out", type=Path, required=True)
    materialize.add_argument("--resource-out", type=Path, required=True)
    materialize.add_argument("--evidence-bundle-out", type=Path, required=True)
    materialize.add_argument("--ratification-binding-out", type=Path, required=True)
    materialize.add_argument("--create-lock", type=Path, required=True)
    materialize.add_argument("--exclude-intake-from-review", action="store_true")

    release_parser = sub.add_parser("release")
    _common_static(release_parser)
    release_parser.add_argument("--lock", type=Path, required=True)
    release_parser.add_argument("--closure", type=Path, required=True)
    release_parser.add_argument("--resources", type=Path, required=True)
    release_parser.add_argument("--evidence-bundle", type=Path, required=True)
    release_parser.add_argument("--ratification-binding", type=Path, required=True)
    release_parser.add_argument("--fable-review", type=Path, required=True)
    release_parser.add_argument("--sol-review", type=Path, required=True)
    release_parser.add_argument("--intake-state", type=Path, required=True)
    release_parser.add_argument("--required-scope", action="append", required=True)
    release_parser.add_argument("--assert-implementation-testing-complete-before-gpu", action="store_true")
    release_parser.add_argument("--assert-identical-review-context", action="store_true")
    release_parser.add_argument("--assert-intake-excluded-from-review", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "static":
            result = static_preflight(args)
        elif args.command == "materialize-review":
            _require(args.intake_state.as_posix() == INTAKE.as_posix(), "materialize intake path mismatch")
            result = materialize_review(args)
        else:
            _require(args.intake_state.as_posix() == INTAKE.as_posix(), "release intake path mismatch")
            result = release(args)
    except BaseException as exc:
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}, sort_keys=True), file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
