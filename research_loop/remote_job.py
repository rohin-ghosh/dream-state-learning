"""Execute an immutable sequence of commands and publish atomic markers.

This module is intentionally model-free. A remote launcher may detach it with
nohup, but completion is determined exclusively by the JSON markers it writes,
never by process-name matching.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import traceback
from pathlib import Path
from typing import Any

from .io import atomic_write_json, fingerprint, load_json, utc_now
from .io import sha256_file


def _format_argv(argv: list[str], variables: dict[str, str]) -> list[str]:
    return [part.format_map(variables) for part in argv]


def _relative_key(path: Path, cwd: Path) -> str:
    resolved = path if path.is_absolute() else cwd / path
    return str(resolved.resolve().relative_to(cwd))


def _verify_execution_binding(
    *,
    spec_path: Path,
    spec: dict[str, Any],
    run_id: str,
    cwd: Path,
    lock_path: Path,
    approval_path: Path,
    approval_sha256: str,
    variables: dict[str, str],
) -> dict[str, Any]:
    actual_approval = sha256_file(approval_path)
    if actual_approval != approval_sha256:
        raise RuntimeError(
            f"approval receipt hash mismatch: expected {approval_sha256}, "
            f"got {actual_approval}"
        )
    approval = load_json(approval_path)
    if approval.get("run_id") != run_id or approval.get("verdict") != "approve":
        raise RuntimeError("approval receipt run/verdict mismatch")
    lock_key = _relative_key(lock_path, cwd)
    spec_key = _relative_key(spec_path, cwd)
    reviewed = approval.get("reviewed_files", {})
    for required in (lock_key, spec_key):
        if required not in reviewed:
            raise RuntimeError(f"approval did not review required file: {required}")
    if reviewed[lock_key] != sha256_file(lock_path):
        raise RuntimeError("approved lock bytes changed")
    if reviewed[spec_key] != sha256_file(spec_path):
        raise RuntimeError("approved remote spec bytes changed")
    lock = load_json(lock_path)
    declared = {
        _relative_key(Path(value.format_map(variables)), cwd)
        for value in spec.get("freeze_inputs", [])
    }
    declared.add(spec_key)
    missing = sorted(declared - set(lock["files"]))
    if missing:
        raise RuntimeError(f"remote freeze inputs absent from approved lock: {missing}")
    # The exact receipt is bound to the complete local review context, but
    # reviewer-only notes need not be exported to the execution host. Verify
    # every remotely declared input directly against the approved lock.
    verified_declared = fingerprint([Path(path) for path in declared], cwd)
    mismatched = {
        path: {
            "lock": lock["files"].get(path),
            "current": verified_declared.get(path),
        }
        for path in declared
        if lock["files"].get(path) != verified_declared.get(path)
    }
    if mismatched:
        raise RuntimeError(f"declared remote inputs changed: {mismatched}")
    return {
        "approval_sha256": actual_approval,
        "approved_lock_sha256": sha256_file(lock_path),
        "remote_spec_sha256": sha256_file(spec_path),
        "declared_input_fingerprints": {
            path: verified_declared[path] for path in sorted(declared)
        },
    }


def run_job(
    spec_path: Path,
    run_id: str,
    job_root: Path,
    *,
    lock_path: Path,
    approval_path: Path,
    approval_sha256: str,
) -> int:
    spec: dict[str, Any] = load_json(spec_path)
    job_dir = job_root / run_id
    job_dir.mkdir(parents=True, exist_ok=True)
    started = job_dir / "started.json"
    done = job_dir / "done.json"
    failed = job_dir / "failed.json"
    if done.exists():
        return 0
    if started.exists() and not failed.exists():
        raise RuntimeError(f"job already started without terminal marker: {job_dir}")

    variables = {
        "run_id": run_id,
        "job_dir": str(job_dir),
        "spec_dir": str(spec_path.parent.resolve()),
    }
    cwd = Path(spec.get("cwd", ".")).expanduser().resolve()
    started_ns = time.time_ns()
    try:
        execution_binding = _verify_execution_binding(
            spec_path=spec_path.resolve(), spec=spec, run_id=run_id, cwd=cwd,
            lock_path=lock_path.resolve(), approval_path=approval_path.resolve(),
            approval_sha256=approval_sha256, variables=variables,
        )
    except BaseException as exc:
        atomic_write_json(
            failed,
            {
                "schema_version": 1,
                "run_id": run_id,
                "failed_at": utc_now(),
                "error": f"{type(exc).__name__}: {exc}",
                "traceback": traceback.format_exc(),
            },
        )
        return 1
    frozen_paths = [
        Path(p.format_map(variables)) for p in spec.get("freeze_inputs", [])
    ]
    input_fingerprints = fingerprint(frozen_paths, cwd)
    input_snapshot_root = job_dir / "inputs"
    input_snapshot_paths = []
    input_sources = {}
    snapshot_inputs = [spec_path.resolve(), lock_path.resolve(),
                       approval_path.resolve(), *frozen_paths]
    snapshot_seen = set()
    for frozen in snapshot_inputs:
        resolved = frozen if frozen.is_absolute() else cwd / frozen
        try:
            relative = resolved.relative_to(cwd)
        except ValueError:
            relative = Path(resolved.name)
        destination = input_snapshot_root / relative
        if str(destination) in snapshot_seen:
            continue
        snapshot_seen.add(str(destination))
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(resolved, destination)
        input_snapshot_paths.append(destination)
        input_sources[str(relative)] = str(resolved)
    manifest = {
        "schema_version": 1,
        "run_id": run_id,
        "spec": str(spec_path.resolve()),
        "cwd": str(cwd),
        "pid": os.getpid(),
        "started_at": utc_now(),
        "stages": spec.get("stages", []),
        "input_fingerprints": input_fingerprints,
        "input_snapshot_fingerprints": fingerprint(
            input_snapshot_paths, job_dir
        ),
        "input_sources": input_sources,
        **execution_binding,
    }
    atomic_write_json(started, manifest)

    stage_records: list[dict[str, Any]] = []
    try:
        for index, stage in enumerate(spec["stages"]):
            _verify_execution_binding(
                spec_path=spec_path.resolve(), spec=spec, run_id=run_id,
                cwd=cwd, lock_path=lock_path.resolve(),
                approval_path=approval_path.resolve(),
                approval_sha256=approval_sha256, variables=variables,
            )
            stage_id = stage["id"]
            argv = _format_argv(stage["argv"], variables)
            log_path = job_dir / f"{index:02d}_{stage_id}.log"
            record = {
                "id": stage_id,
                "argv": argv,
                "started_at": utc_now(),
                "log": str(log_path),
            }
            stage_records.append(record)
            with log_path.open("w", encoding="utf-8") as log:
                proc = subprocess.run(
                    argv,
                    cwd=cwd,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    text=True,
                    timeout=stage.get("timeout_sec"),
                    check=False,
                )
            record["finished_at"] = utc_now()
            record["returncode"] = proc.returncode
            atomic_write_json(job_dir / "progress.json", {"stages": stage_records})
            if proc.returncode not in stage.get("success_exit_codes", [0]):
                raise RuntimeError(f"stage {stage_id} exited {proc.returncode}")
            _verify_execution_binding(
                spec_path=spec_path.resolve(), spec=spec, run_id=run_id,
                cwd=cwd, lock_path=lock_path.resolve(),
                approval_path=approval_path.resolve(),
                approval_sha256=approval_sha256, variables=variables,
            )

        artifacts = [Path(p.format_map(variables)) for p in spec.get("artifacts", [])]
        stale = []
        for artifact in artifacts:
            resolved = artifact if artifact.is_absolute() else cwd / artifact
            if not resolved.is_file() or resolved.stat().st_mtime_ns < started_ns:
                stale.append(str(resolved))
        if stale:
            raise RuntimeError(f"missing or stale required artifacts: {stale}")
        snapshot_root = job_dir / "artifacts"
        snapshot_paths = []
        artifact_sources = {}
        for artifact in artifacts:
            resolved = artifact if artifact.is_absolute() else cwd / artifact
            try:
                relative = resolved.relative_to(cwd)
            except ValueError:
                relative = Path(resolved.name)
            destination = snapshot_root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(resolved, destination)
            snapshot_paths.append(destination)
            artifact_sources[str(relative)] = str(resolved)
        artifact_fingerprints = fingerprint(snapshot_paths, job_dir)
        _verify_execution_binding(
            spec_path=spec_path.resolve(), spec=spec, run_id=run_id, cwd=cwd,
            lock_path=lock_path.resolve(), approval_path=approval_path.resolve(),
            approval_sha256=approval_sha256, variables=variables,
        )
        terminal = {
            **manifest,
            "finished_at": utc_now(),
            "stages": stage_records,
            "artifact_fingerprints": artifact_fingerprints,
            "artifact_sources": artifact_sources,
        }
        atomic_write_json(done, terminal)
        return 0
    except BaseException as exc:
        atomic_write_json(
            failed,
            {
                **manifest,
                "failed_at": utc_now(),
                "stages": stage_records,
                "error": f"{type(exc).__name__}: {exc}",
                "traceback": traceback.format_exc(),
            },
        )
        return 1


def status(job_root: Path, run_id: str) -> int:
    job_dir = job_root / run_id
    for name, code in (("done.json", 0), ("failed.json", 2), ("started.json", 75)):
        path = job_dir / name
        if path.exists():
            print(json.dumps(load_json(path), sort_keys=True))
            return code
    print(json.dumps({"run_id": run_id, "status": "not_started"}))
    return 76


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run.add_argument("--spec", type=Path, required=True)
    run.add_argument("--run-id", required=True)
    run.add_argument("--job-root", type=Path, required=True)
    run.add_argument("--lock", type=Path, required=True)
    run.add_argument("--approval", type=Path, required=True)
    run.add_argument("--approval-sha256", required=True)
    probe = sub.add_parser("status")
    probe.add_argument("--run-id", required=True)
    probe.add_argument("--job-root", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.command == "run":
        return run_job(
            args.spec, args.run_id, args.job_root,
            lock_path=args.lock, approval_path=args.approval,
            approval_sha256=args.approval_sha256,
        )
    return status(args.job_root, args.run_id)


if __name__ == "__main__":
    sys.exit(main())
