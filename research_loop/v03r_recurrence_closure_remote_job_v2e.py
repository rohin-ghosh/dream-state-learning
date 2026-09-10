"""Fail-closed remote entry points for the ratified v2e workflow.

The runner owns phase-A/phase-B cognition.  This wrapper permits only its
available sealed synthetic preflight; it refuses to invent a science scheduler
when the runner does not expose the required phase entry points.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Sequence

from .architecture_intake import validate_authorized_intake
from .freeze import verify as verify_lock
from .io import atomic_write_json, load_json, sha256_file, utc_now
from .review_binding import verify_binding


CHANGE_ID = "chg_20260901_v03r_recurrence_closure_dev_v2e"
MODEL = "Qwen/Qwen2.5-32B-Instruct"
REVISION = "5ede1c97bbab6ce5cda5812749b4c0bdf79b18dd"
ENVELOPE_SHA256 = "8b7b8dd82d304cb83638b13207cb6c05d255b874dc4d363a3299202bcc3a06cd"
REQUIRED_SCOPE = [
    "analysis:bound_postcommit_v03r_closure_v2e",
    "gpu:v03r_recurrence_closure_dev_v2e",
    "implementation:v03r_recurrence_closure_dev_v2e",
    "testing:pre_gpu_v03r_recurrence_closure_dev_v2e",
]
INTAKE = Path("research_loop/changes/chg_20260901_v03r_recurrence_closure_dev_v2e/intake.state.json")
_RUN_ID = re.compile(r"[0-9a-f]{64}")


class RemoteJobError(RuntimeError):
    pass


def _require(value: bool, message: str) -> None:
    if not value:
        raise RemoteJobError(message)


def _read(path: Path, label: str) -> dict[str, Any]:
    _require(path.is_file(), f"{label} is missing: {path}")
    value = load_json(path)
    _require(isinstance(value, dict), f"{label} must be a JSON object")
    return value


def _job_dir(job_root: Path, run_id: str) -> Path:
    _require(_RUN_ID.fullmatch(run_id) is not None, "run_id must be lowercase SHA-256")
    return job_root.resolve() / run_id / "job"


def _verify_release(root: Path, args: argparse.Namespace) -> None:
    verify_lock(root, args.lock)
    authority = validate_authorized_intake(root, args.intake_state)
    ratification = authority["ratification"]
    _require(ratification.get("change_id") == CHANGE_ID, "wrong ratified change")
    _require(ratification.get("authorized_scope") == REQUIRED_SCOPE, "ratification scope mismatch")
    binding = _read(args.ratification_binding, "ratification binding")
    _require(binding.get("run_id") == args.run_id, "ratification binding run mismatch")
    _require(binding.get("change_id") == CHANGE_ID, "ratification binding change mismatch")
    _require(binding.get("authorized_scope") == REQUIRED_SCOPE, "ratification binding scope mismatch")
    _require(binding.get("ratification_sha256") == sha256_file(authority["paths"]["ratification"]), "ratification bytes changed")
    for label, path in (("fable", args.fable_review), ("sol", args.sol_review)):
        review = _read(path, f"{label} review")
        _require(review.get("run_id") == args.run_id, f"{label} review run mismatch")
        verify_binding(root, path, required_verdict="approve")


def _validate_zero_args(args: argparse.Namespace) -> None:
    _require(args.model == MODEL and args.revision == REVISION, "model/revision mismatch")
    _require(args.expected_device_name == "NVIDIA H100 NVL", "device mismatch")
    _require(args.minimum_total_memory_mib == 95000, "minimum device memory mismatch")
    _require(args.expected_known_total_memory_mib == 95830 and args.exact_device_count == 1, "frozen device inventory mismatch")
    _require(args.envelope_sha256 == ENVELOPE_SHA256 and args.exact_calls_per_class == 2, "zero-science envelope mismatch")
    _require(args.disable_prefix_caching and args.disable_request_truncation, "cache/truncation must be disabled")
    _require(all((args.synthetic_only, args.exercise_maximum_envelopes, args.require_peak_allocation_telemetry, args.require_reset_telemetry, args.require_no_active_sequences, args.require_unique_session_ids, args.require_unique_receipt_ids)), "all zero-science assertions are mandatory")


def _validate_h100(args: argparse.Namespace) -> None:
    try:
        import torch
    except ImportError as exc:  # pragma: no cover - exercised on the GPU host
        raise RemoteJobError("torch is required for the H100 preflight") from exc
    _require(torch.cuda.is_available(), "CUDA is unavailable")
    _require(torch.cuda.device_count() == 1, "exactly one CUDA device is required")
    properties = torch.cuda.get_device_properties(0)
    total_mib = properties.total_memory // (1024 * 1024)
    _require(properties.name == args.expected_device_name, "CUDA device name mismatch")
    _require(total_mib >= args.minimum_total_memory_mib, "CUDA device is below the minimum capacity")
    _require(total_mib == args.expected_known_total_memory_mib, "CUDA device total differs from frozen H100 inventory")
    _require(torch.cuda.is_bf16_supported(), "CUDA device lacks bf16 support")


def zero_science_preflight(args: argparse.Namespace) -> dict[str, Any]:
    _validate_zero_args(args)
    _validate_h100(args)
    root = Path.cwd().resolve()
    _verify_release(root, args)
    job_dir = _job_dir(args.job_root, args.run_id)
    _require(args.out.resolve() == job_dir / "zero_science_preflight.json", "preflight output must be the workflow's immutable job seal")
    _require(not args.out.exists(), "zero-science preflight cannot be repeated")
    raw = args.envelope_resource.read_bytes()
    _require(hashlib.sha256(raw).hexdigest() == ENVELOPE_SHA256, "zero-science resource bytes changed")
    resource = json.loads(raw.decode("ascii"))
    _require(resource.get("resource_id") == "v03r-zero-science-envelopes-v2e", "wrong zero-science resource")
    _require(resource.get("execution", {}).get("calls_per_class") == 2 and resource["execution"].get("total_calls") == 8, "wrong zero-science call count")
    policy = resource.get("science_material_policy", {})
    _require(policy.get("public_life_inputs_allowed") is False and policy.get("science_observation") is False, "preflight is not synthetic-only")
    from . import run_v03r_recurrence_closure_v2e as runner
    result = runner.run_zero_science_batch(SimpleNamespace(
        envelope_resource=str(args.envelope_resource), envelope_sha256=args.envelope_sha256,
        model=args.model, revision=args.revision, engine_kind="vllm", run_id=args.run_id,
        out=str(args.out),
    ))
    _require(result.get("zero_science_preflight") == "pass", "runner did not pass zero-science preflight")
    _require(result.get("resource_sha256") == ENVELOPE_SHA256, "runner sealed a different zero-science resource")
    _require(isinstance(result.get("calls"), list) and len(result["calls"]) == 8, "runner did not record eight preflight calls")
    return result


def _failed_launch_marker(args: argparse.Namespace, message: str) -> None:
    job_dir = _job_dir(args.job_root, args.run_id)
    job_dir.mkdir(parents=True, exist_ok=True)
    done, failed = job_dir / "done.json", job_dir / "failed.json"
    _require(not done.exists() and not failed.exists(), "a terminal marker already exists")
    atomic_write_json(failed, {
        "schema_version": 1, "run_id": args.run_id, "change_id": CHANGE_ID,
        "failed_at": utc_now(), "error": message,
        "science_calls_started": False,
    })


def start_science(args: argparse.Namespace) -> int:
    _require(args.model == MODEL and args.revision == REVISION, "model/revision mismatch")
    _require(args.disable_prefix_caching and args.disable_request_truncation, "cache/truncation must be disabled")
    expected = (514, 48, 17, 48, 3, 6, 72)
    observed = (args.shared_dream_calls, args.branch_dream_calls_per_defined_life, args.exploratory_calls_per_defined_life, args.selector_traces_per_defined_life, args.memory1_per_defined_life, args.max_defined_lives, args.max_think0_calls)
    _require(observed == expected, "science schedule mismatch")
    _require(args.phase_a_before_scorer and args.analysis_scope_after_phase_a and args.offline_scorer_only, "phase-boundary assertions are mandatory")
    _verify_release(Path.cwd().resolve(), args)
    seal = _read(args.zero_science_seal, "zero-science seal")
    _require(seal.get("zero_science_preflight") == "pass" and seal.get("resource_sha256") == ENVELOPE_SHA256, "valid zero-science seal is required")
    from . import run_v03r_recurrence_closure_v2e as runner
    if not callable(getattr(runner, "run_phase_a", None)) or not callable(getattr(runner, "run_phase_b", None)):
        _failed_launch_marker(args, "v2e science runner lacks callable phase-A/phase-B entrypoints; no science call was launched")
        raise RemoteJobError("v2e science runner is incomplete; refusing to launch science")
    raise RemoteJobError("remote science launch is unavailable pending a complete runner-owned entrypoint")


def status(args: argparse.Namespace) -> int:
    job_dir = _job_dir(args.job_root, args.run_id)
    for name, code in (("done", 0), ("failed", 2), ("started", 75)):
        path = job_dir / f"{name}.json"
        if path.is_file():
            print(json.dumps(_read(path, f"{name} marker"), sort_keys=True))
            return code
    print(json.dumps({"run_id": args.run_id, "status": "not_started"}, sort_keys=True))
    return 76


def _common(parser: argparse.ArgumentParser, *, intake_required: bool) -> None:
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--job-root", type=Path, required=True)
    parser.add_argument("--lock", type=Path, required=True)
    parser.add_argument("--ratification-binding", type=Path, required=True)
    parser.add_argument("--fable-review", type=Path, required=True)
    parser.add_argument("--sol-review", type=Path, required=True)
    parser.add_argument(
        "--intake-state", type=Path, required=intake_required,
        default=None if intake_required else INTAKE,
    )
    parser.add_argument("--model", required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--expected-device-name", required=True)
    parser.add_argument("--minimum-total-memory-mib", type=int, required=True)
    parser.add_argument("--disable-prefix-caching", action="store_true")
    parser.add_argument("--disable-request-truncation", action="store_true")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    zero = sub.add_parser("zero-science-preflight")
    _common(zero, intake_required=False)
    zero.add_argument("--envelope-resource", type=Path, required=True)
    zero.add_argument("--envelope-sha256", required=True)
    zero.add_argument("--exact-calls-per-class", type=int, required=True)
    zero.add_argument("--expected-known-total-memory-mib", type=int, required=True)
    zero.add_argument("--exact-device-count", type=int, required=True)
    for name in ("synthetic-only", "exercise-maximum-envelopes", "require-peak-allocation-telemetry", "require-reset-telemetry", "require-no-active-sequences", "require-unique-session-ids", "require-unique-receipt-ids"):
        zero.add_argument("--" + name, action="store_true")
    zero.add_argument("--out", type=Path, required=True)
    science = sub.add_parser("start-science")
    _common(science, intake_required=True)
    science.add_argument("--zero-science-seal", type=Path, required=True)
    science.add_argument("--zero-science-envelope-sha256", required=True)
    for name in ("shared_dream_calls", "branch_dream_calls_per_defined_life", "exploratory_calls_per_defined_life", "selector_traces_per_defined_life", "memory1_per_defined_life", "max_defined_lives", "max_think0_calls"):
        science.add_argument("--" + name.replace("_", "-"), type=int, required=True)
    for name in ("phase-a-before-scorer", "analysis-scope-after-phase-a", "offline-scorer-only"):
        science.add_argument("--" + name, action="store_true")
    probe = sub.add_parser("status")
    probe.add_argument("--run-id", required=True)
    probe.add_argument("--job-root", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "zero-science-preflight":
            print(json.dumps(zero_science_preflight(args), sort_keys=True))
            return 0
        if args.command == "start-science":
            return start_science(args)
        return status(args)
    except BaseException as exc:
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}, sort_keys=True), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
