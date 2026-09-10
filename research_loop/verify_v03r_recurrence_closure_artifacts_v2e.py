"""Fail-closed artifact gates for the frozen v0.3-R v2e calibration.

The module deliberately does not import the runner, provider boundary, model,
or scoring code.  It validates already-written bytes only.  ``phase-a`` seals
the scorer-free raw graph; ``phase-b`` validates the offline graph against that
seal and is the only command here allowed to create ``done.json``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import uuid
from typing import Any, Iterable, Mapping

from .v03r_recurrence_closure_contract_v2e import (
    CHANGE_ID,
    V03RContractError,
    canonical_json_bytes,
    sha256_json,
    validate_phase_a_inventory,
    validate_phase_b_inventory,
)


SCHEMA_VERSION = "v03r-recurrence-closure-artifact-v2e"
RAW_FILES = (
    "required_inventory.json",
    "run_manifest.json",
    "environment.json",
    "primary_definition_and_D.json",
    "undefined_lives.jsonl",
    "measured_balance.json",
    "candidate_universes.jsonl",
    "call_ledger.jsonl",
    "selector_traces.jsonl",
    "proposals.jsonl",
    "exploratory_ceilings.json",
)
SCORED_FILES = (
    "deterministic_controls.jsonl",
    "postcommit_closure_scores.jsonl",
    "normalization_only_gain.json",
    "metrics.json",
)
PHASE_A_SEAL = "phase_a_raw_seal.json"
PHASE_B_SEAL = "phase_b_scored_graph.json"
_HEX64 = set("0123456789abcdef")
_ARTIFACT_TYPE = re.compile(r"^[a-z0-9_]{1,96}$")


class ArtifactVerificationError(RuntimeError):
    """Raised for an invalid, incomplete, or phase-inappropriate artifact graph."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ArtifactVerificationError(message)


def _hash(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _is_hash(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and set(value) <= _HEX64


def _read_canonical_json(path: Path, label: str) -> dict[str, Any]:
    _require(path.is_file(), f"missing {label}: {path}")
    raw = path.read_bytes()
    try:
        value = json.loads(raw.decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ArtifactVerificationError(f"{label} is not ASCII JSON: {path}") from exc
    _require(isinstance(value, dict), f"{label} is not a JSON object: {path}")
    _require(canonical_json_bytes(value) == raw, f"{label} is not canonical JSON: {path}")
    return value


def _read_canonical_jsonl(path: Path, label: str) -> list[dict[str, Any]]:
    _require(path.is_file(), f"missing {label}: {path}")
    raw = path.read_bytes()
    _require(not raw.startswith(b"\xef\xbb\xbf"), f"{label} has a BOM: {path}")
    _require(not raw or raw.endswith(b"\n"), f"{label} must end at a complete JSONL record: {path}")
    if not raw:
        return []
    result: list[dict[str, Any]] = []
    for number, line in enumerate(raw.splitlines(), start=1):
        _require(line, f"{label} contains a blank JSONL record at line {number}")
        try:
            value = json.loads(line.decode("ascii"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ArtifactVerificationError(f"{label} line {number} is not ASCII JSON") from exc
        _require(isinstance(value, dict), f"{label} line {number} is not an object")
        _require(canonical_json_bytes(value) == line, f"{label} line {number} is not canonical JSON")
        result.append(value)
    return result


def _artifact_envelope(value: Mapping[str, Any], *, phase: str,
                       run_id: str | None = None) -> tuple[str, dict[str, Any]]:
    required = {
        "schema_version", "run_id", "change_id", "phase", "artifact_type",
        "payload", "payload_sha256", "provenance",
    }
    _require(set(value) == required, "artifact envelope has missing or extra fields")
    _require(value["schema_version"] == SCHEMA_VERSION, "artifact schema version mismatch")
    _require(_is_hash(value["run_id"]), "artifact run_id is not a 64-character lowercase hash")
    if run_id is not None:
        _require(value["run_id"] == run_id, "artifact run_id differs within the job")
    _require(value["change_id"] == CHANGE_ID, "artifact change_id mismatch")
    _require(value["phase"] == phase, f"artifact has wrong phase: expected {phase}")
    _require(isinstance(value["artifact_type"], str)
             and _ARTIFACT_TYPE.fullmatch(value["artifact_type"]) is not None,
             "artifact type violates the frozen schema")
    _require(isinstance(value["payload"], dict), "artifact payload is not an object")
    _require(value["payload_sha256"] == sha256_json(value["payload"]), "artifact payload hash mismatch")
    provenance = value["provenance"]
    _require(isinstance(provenance, dict) and set(provenance) == {
        "lock_sha256", "ratification_binding_sha256", "created_after_phase_a",
    }, "artifact provenance schema mismatch")
    _require(_is_hash(provenance["lock_sha256"]), "artifact lock hash is invalid")
    _require(_is_hash(provenance["ratification_binding_sha256"]), "artifact ratification hash is invalid")
    _require(provenance["created_after_phase_a"] is (phase != "PHASE_A"),
             "artifact phase/provenance barrier mismatch")
    return str(value["run_id"]), dict(provenance)


def _verify_raw_artifacts(artifacts: Path) -> tuple[str, dict[str, Any], dict[str, str], dict[str, Any]]:
    run_id: str | None = None
    inventory: dict[str, Any] | None = None
    common_provenance: dict[str, Any] | None = None
    digests: dict[str, str] = {}
    for filename in RAW_FILES:
        path = artifacts / filename
        if filename.endswith(".jsonl"):
            rows = _read_canonical_jsonl(path, filename)
            for row in rows:
                row_run_id, provenance = _artifact_envelope(
                    row, phase="PHASE_A", run_id=run_id,
                )
                run_id = run_id or row_run_id
                if common_provenance is None:
                    common_provenance = provenance
                _require(provenance == common_provenance, "raw artifacts have mixed provenance")
        else:
            row = _read_canonical_json(path, filename)
            row_run_id, provenance = _artifact_envelope(
                row, phase="PHASE_A", run_id=run_id,
            )
            run_id = run_id or row_run_id
            if common_provenance is None:
                common_provenance = provenance
            _require(provenance == common_provenance, "raw artifacts have mixed provenance")
            if filename == "required_inventory.json":
                inventory = dict(row["payload"])
        digests[filename] = _hash(path.read_bytes())
    _require(run_id is not None, "raw graph has no run-bound records")
    _require(inventory is not None, "raw graph lacks required inventory")
    _require(common_provenance is not None, "raw graph has no provenance")
    return run_id, inventory, digests, common_provenance


def _assert_directory_exact(artifacts: Path, expected: Iterable[str]) -> None:
    _require(artifacts.is_dir(), f"artifacts directory is missing: {artifacts}")
    actual = {path.name for path in artifacts.iterdir()}
    expected_names = set(expected)
    _require(actual == expected_names,
             f"artifact set is not exact: missing={sorted(expected_names - actual)!r}, "
             f"unexpected={sorted(actual - expected_names)!r}")
    _require(all(path.is_file() for path in artifacts.iterdir()), "artifact directory may not contain subdirectories")


def _write_once(path: Path, value: Mapping[str, Any]) -> None:
    _require(not path.exists(), f"refusing to overwrite immutable artifact: {path}")
    encoded = canonical_json_bytes(value)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.{uuid.uuid4().hex}.tmp")
    with temporary.open("xb") as handle:
        handle.write(encoded)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _failure_marker(job_dir: Path, exc: BaseException) -> None:
    """Best-effort terminal failure record; never replaces an existing marker."""
    done = job_dir / "done.json"
    failed = job_dir / "failed.json"
    if done.exists() or failed.exists():
        return
    try:
        _write_once(failed, {
            "schema_version": "v03r-recurrence-closure-verifier-v2e",
            "artifact_type": "artifact_verification_failure",
            "change_id": CHANGE_ID,
            "error": f"{type(exc).__name__}: {exc}",
        })
    except BaseException:
        pass


def verify_phase_a(args: argparse.Namespace) -> dict[str, Any]:
    artifacts = args.job_dir / "artifacts"
    _require(not (args.job_dir / "done.json").exists(), "done marker exists before phase-A verification")
    _require(not (args.job_dir / "failed.json").exists(), "job is already terminally failed")
    _require((args.shared_dream_calls, args.branch_dream_calls_per_defined_life,
              args.max_recurrent_dream_calls, args.max_think0_calls,
              args.exploratory_calls_per_defined_life, args.max_exploratory_calls,
              args.selector_traces_per_defined_life, args.memory1_per_defined_life,
              args.max_defined_lives) == (514, 48, 802, 72, 17, 102, 48, 3, 6),
             "phase-A CLI differs from the frozen v2e schedule")
    _require(args.require_primary_undefined_terminals and args.require_scorer_absent_before_seal,
             "phase-A terminal/scorer assertions are mandatory")
    _assert_directory_exact(artifacts, RAW_FILES)
    run_id, inventory, raw_digests, provenance = _verify_raw_artifacts(artifacts)
    try:
        seal_sha256 = validate_phase_a_inventory(inventory)
    except V03RContractError as exc:
        raise ArtifactVerificationError(f"invalid phase-A inventory: {exc}") from exc
    _require(len(inventory["defined_life_ids"]) <= args.max_defined_lives,
             "defined life count exceeds frozen maximum")
    _require(inventory["shared_dream_calls"] == args.shared_dream_calls,
             "shared DREAM count differs from CLI contract")
    _require(inventory["branch_dream_calls"] <= args.max_recurrent_dream_calls - args.shared_dream_calls,
             "branch DREAM count exceeds CLI contract")
    _require(inventory["think_calls"] <= args.max_think0_calls,
             "THINK prefix count exceeds CLI contract")
    _require(inventory["exploratory_calls"] <= args.max_exploratory_calls,
             "exploratory call count exceeds CLI contract")
    _require(inventory["scorer_material_present"] is False, "scorer material appeared before phase-A seal")
    seal_payload = {
        "inventory": inventory,
        "raw_artifact_sha256": raw_digests,
        "phase_a_inventory_seal_sha256": seal_sha256,
    }
    seal = {
        "schema_version": SCHEMA_VERSION,
        "artifact_type": "phase_a_raw_seal",
        "change_id": CHANGE_ID,
        "run_id": run_id,
        "phase": "PHASE_A",
        "payload": seal_payload,
        "payload_sha256": sha256_json(seal_payload),
        "provenance": provenance,
    }
    _write_once(artifacts / PHASE_A_SEAL, seal)
    return {"phase_a": "pass", "run_id": run_id, "defined_lives": len(inventory["defined_life_ids"]),
            "phase_a_seal_sha256": seal_sha256}


def _read_phase_a_seal(path: Path, artifacts: Path) -> tuple[str, dict[str, Any], str, dict[str, Any]]:
    seal = _read_canonical_json(path, "phase-A seal")
    run_id, provenance = _artifact_envelope(seal, phase="PHASE_A")
    _require(seal["artifact_type"] == "phase_a_raw_seal", "phase-A seal identity mismatch")
    payload = seal["payload"]
    _require(set(payload) == {"inventory", "raw_artifact_sha256", "phase_a_inventory_seal_sha256"},
             "phase-A seal payload schema mismatch")
    _require(isinstance(payload["inventory"], dict) and isinstance(payload["raw_artifact_sha256"], dict),
             "phase-A seal payload types are invalid")
    try:
        expected_seal = validate_phase_a_inventory(payload["inventory"])
    except V03RContractError as exc:
        raise ArtifactVerificationError(f"phase-A seal inventory is invalid: {exc}") from exc
    _require(payload["phase_a_inventory_seal_sha256"] == expected_seal, "phase-A seal digest mismatch")
    raw_digests = {name: _hash((artifacts / name).read_bytes()) for name in RAW_FILES}
    _require(payload["raw_artifact_sha256"] == raw_digests, "phase-A raw artifact bytes changed")
    return run_id, dict(payload["inventory"]), expected_seal, provenance


def verify_phase_b(args: argparse.Namespace) -> dict[str, Any]:
    artifacts = args.job_dir / "artifacts"
    _require(not (args.job_dir / "done.json").exists(), "done marker exists before phase-B verification")
    _require(not (args.job_dir / "failed.json").exists(), "job is already terminally failed")
    _require(args.expected_score_metrics == 4
             and args.require_comparable_control_per_selected_slot
             and args.require_common_control_metrics
             and args.forbid_residual_subtraction
             and args.require_single_terminal_marker,
             "all frozen phase-B assertions are mandatory")
    _assert_directory_exact(artifacts, (*RAW_FILES, PHASE_A_SEAL, *SCORED_FILES))
    _require(args.phase_a_seal.resolve() == (artifacts / PHASE_A_SEAL).resolve(),
             "phase-A seal path is not the job's immutable seal")
    run_id, phase_a, phase_a_sha, phase_a_provenance = _read_phase_a_seal(args.phase_a_seal, artifacts)
    metrics = _read_canonical_json(artifacts / "metrics.json", "metrics.json")
    metric_run_id, metric_provenance = _artifact_envelope(metrics, phase="PHASE_B", run_id=run_id)
    _require(metric_run_id == run_id, "metrics run binding mismatch")
    _require(metric_provenance["lock_sha256"] == phase_a_provenance["lock_sha256"]
             and metric_provenance["ratification_binding_sha256"] == phase_a_provenance["ratification_binding_sha256"],
             "phase-B metrics do not bind phase-A authority")
    inventory = dict(metrics["payload"])
    try:
        phase_b_sha = validate_phase_b_inventory(inventory, phase_a_seal_sha256=phase_a_sha)
    except V03RContractError as exc:
        raise ArtifactVerificationError(f"invalid phase-B inventory: {exc}") from exc
    _require(inventory["defined_life_ids"] == phase_a["defined_life_ids"], "phase B changed defined-life set/order")
    _require(args.expected_score_metrics == 4 and inventory["four_metric_rows_per_proposal"] is True,
             "four closure metrics are not complete")
    _require(inventory["controls_complete"] is True, "comparable controls are incomplete")
    _require(inventory["four_metric_rows_per_proposal"] is True, "common control metrics are incomplete")
    _require(inventory["normalization_gains_complete"] is True, "normalization-only gain graph is incomplete")
    for filename in SCORED_FILES:
        path = artifacts / filename
        rows = _read_canonical_jsonl(path, filename) if filename.endswith(".jsonl") else [_read_canonical_json(path, filename)]
        for row in rows:
            _, provenance = _artifact_envelope(row, phase="PHASE_B", run_id=run_id)
            _require(provenance == metric_provenance, "scored artifacts have mixed provenance")
    phase_b_payload = {
        "phase_a_inventory_seal_sha256": phase_a_sha,
        "inventory": inventory,
        "scored_artifact_sha256": {name: _hash((artifacts / name).read_bytes()) for name in SCORED_FILES},
        "phase_b_inventory_seal_sha256": phase_b_sha,
    }
    phase_b = {
        "schema_version": SCHEMA_VERSION,
        "artifact_type": "phase_b_scored_graph",
        "change_id": CHANGE_ID,
        "run_id": run_id,
        "phase": "PHASE_B",
        "payload": phase_b_payload,
        "payload_sha256": sha256_json(phase_b_payload),
        "provenance": metric_provenance,
    }
    _write_once(artifacts / PHASE_B_SEAL, phase_b)
    if args.require_single_terminal_marker:
        _require(not (args.job_dir / "failed.json").exists(), "failed marker exists before done")
        done_payload = {
            "phase_a_inventory_seal_sha256": phase_a_sha,
            "phase_b_inventory_seal_sha256": phase_b_sha,
            "next_action": "human_stop_required",
        }
        _write_once(args.job_dir / "done.json", {
            "schema_version": SCHEMA_VERSION,
            "artifact_type": "done",
            "change_id": CHANGE_ID,
            "run_id": run_id,
            "phase": "TERMINAL",
            "payload": done_payload,
            "payload_sha256": sha256_json(done_payload),
            "provenance": metric_provenance,
        })
    return {"phase_b": "pass", "run_id": run_id, "phase_b_seal_sha256": phase_b_sha,
            "terminal": "done.json" if args.require_single_terminal_marker else "not_written"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    phase_a = sub.add_parser("phase-a")
    phase_a.add_argument("--job-dir", type=Path, required=True)
    phase_a.add_argument("--shared-dream-calls", type=int, required=True)
    phase_a.add_argument("--branch-dream-calls-per-defined-life", type=int, required=True)
    phase_a.add_argument("--max-recurrent-dream-calls", type=int, required=True)
    phase_a.add_argument("--max-think0-calls", type=int, required=True)
    phase_a.add_argument("--exploratory-calls-per-defined-life", type=int, required=True)
    phase_a.add_argument("--max-exploratory-calls", type=int, required=True)
    phase_a.add_argument("--selector-traces-per-defined-life", type=int, required=True)
    phase_a.add_argument("--memory1-per-defined-life", type=int, required=True)
    phase_a.add_argument("--max-defined-lives", type=int, required=True)
    phase_a.add_argument("--require-primary-undefined-terminals", action="store_true")
    phase_a.add_argument("--require-scorer-absent-before-seal", action="store_true")
    phase_b = sub.add_parser("phase-b")
    phase_b.add_argument("--job-dir", type=Path, required=True)
    phase_b.add_argument("--phase-a-seal", type=Path, required=True)
    phase_b.add_argument("--expected-score-metrics", type=int, required=True)
    phase_b.add_argument("--require-comparable-control-per-selected-slot", action="store_true")
    phase_b.add_argument("--require-common-control-metrics", action="store_true")
    phase_b.add_argument("--forbid-residual-subtraction", action="store_true")
    phase_b.add_argument("--require-single-terminal-marker", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = verify_phase_a(args) if args.command == "phase-a" else verify_phase_b(args)
    except BaseException as exc:
        _failure_marker(args.job_dir, exc)
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}, sort_keys=True), file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
