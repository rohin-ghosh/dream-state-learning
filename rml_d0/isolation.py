"""Executable subprocess isolation and actual run-vs-skip source sealing."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from .canonical import canonical_bytes


DENIED_CAPABILITIES = (
    "generator",
    "gpu",
    "model",
    "network",
    "scorer",
    "source_write",
)


def actual_source_snapshot() -> dict[str, Any]:
    """Seal actual Stage-A source/schema/target/tape artifacts."""

    from .rng import STAGE_A_TARGET_TAPE_VALUES
    from .schema_reference import schema_chronology_golden
    from .source import complete_be_goldens
    from .targets import make_target
    from .world import target_public_record

    source = complete_be_goldens()
    chronology = schema_chronology_golden()
    target = make_target(0, 0)
    return {
        "commitment_status_chain": chronology["final_chain_sha256"],
        "source_event_seals": source["cutwise_be_sha256"],
        "source_schedule_counts": source["literal_event_counts"],
        "source_state": {
            "bridge_distinct": source["bridge_distinct_across_trials"],
            "cutwise_be_equal": source["cutwise_be_equal"],
        },
        "suffix_intent": "DETERMINISTIC_SOURCE_SUFFIX_V1",
        "tape_cursors": {
            "source_events": source["literal_event_counts"][-1],
            "target_handle_tape": len(STAGE_A_TARGET_TAPE_VALUES),
        },
        "target_descriptor_sha256": hashlib.sha256(
            canonical_bytes(target_public_record(target))
        ).hexdigest(),
        "target_handles": list(STAGE_A_TARGET_TAPE_VALUES),
    }


def deterministic_suffix(snapshot: dict[str, Any]) -> dict[str, str]:
    """The sole source-suffix path; it has no evaluator input."""

    fields = (
        "source_event_seals",
        "source_state",
        "source_schedule_counts",
        "commitment_status_chain",
        "tape_cursors",
        "suffix_intent",
        "target_descriptor_sha256",
        "target_handles",
    )
    hashes = {
        field: hashlib.sha256(canonical_bytes(snapshot[field])).hexdigest()
        for field in fields
    }
    hashes["final_hash"] = hashlib.sha256(canonical_bytes(hashes)).hexdigest()
    return hashes


def _run_disposable(snapshot: dict[str, Any], life_id: int) -> dict[str, Any]:
    worker = Path(__file__).resolve().with_name("isolation_worker.py")
    snapshot_bytes = canonical_bytes(snapshot)
    with tempfile.TemporaryDirectory(prefix=f"rml_d0_eval_{life_id}_") as temp_dir:
        descriptor = Path(temp_dir) / "source_snapshot.json"
        descriptor.write_bytes(snapshot_bytes)
        descriptor.chmod(0o444)
        request = {
            "life_id": life_id,
            "snapshot": snapshot,
            "source_descriptor_path": str(descriptor),
            "temp_canary": str(Path(temp_dir) / f"TEMP_LIFE_{life_id}"),
        }
        completed = subprocess.run(
            [sys.executable, "-I", "-S", str(worker)],
            input=canonical_bytes(request),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            close_fds=True,
            cwd=temp_dir,
            env={"PATH": os.environ.get("PATH", ""), "PYTHONHASHSEED": "0"},
            timeout=10,
        )
        if completed.returncode != 0:
            raise AssertionError(
                f"disposable evaluator failed: {completed.stderr.decode('utf-8', 'replace')}"
            )
        if descriptor.read_bytes() != snapshot_bytes:
            raise AssertionError("evaluation subprocess changed source descriptor")
        return json.loads(completed.stdout)


def evaluation_isolation_golden() -> dict[str, Any]:
    snapshot = actual_source_snapshot()
    snapshot_before = canonical_bytes(snapshot)
    skip_hashes = deterministic_suffix(snapshot)
    audit = _run_disposable(snapshot, 0)
    run_hashes = deterministic_suffix(snapshot)
    second_audit = _run_disposable(snapshot, 1)
    if snapshot_before != canonical_bytes(snapshot) or run_hashes != skip_hashes:
        raise AssertionError("evaluation changed actual deterministic suffix inputs")
    if set(audit["denied"]) != set(DENIED_CAPABILITIES) or not all(
        audit["denied"].values()
    ):
        raise AssertionError("a denied evaluation capability was callable")
    if not audit["snapshot_unchanged"]:
        raise AssertionError("disposable snapshot changed")
    if audit["audit_only_hash"] == second_audit["audit_only_hash"]:
        raise AssertionError("cross-life process/cache/temp/fd canaries collided")
    return {
        "audit_only_sink": True,
        "capability_attempts_denied": audit["denied"],
        "cross_life_canary_categories": [
            "events", "handles", "caches", "temp_paths", "processes", "file_descriptors"
        ],
        "evaluator_subprocess_isolated": True,
        "peak_temp_bytes": len(snapshot_before),
        "run_hashes": run_hashes,
        "run_skip_equal": True,
        "skip_hashes": skip_hashes,
        "snapshot_sha256": hashlib.sha256(snapshot_before).hexdigest(),
        "source_descriptor_unchanged": True,
    }
