from __future__ import annotations

import json
import os
import sys
import threading
import time
from pathlib import Path

from research_loop.io import load_json, sha256_file
from research_loop.io import atomic_write_json
from research_loop.agents import _codex_response_schema, run_agent
from research_loop.freeze import create as create_freeze
from research_loop.freeze import verify as verify_freeze
from research_loop.remote_job import run_job, status
from research_loop.review_binding import create_binding
from research_loop.supervisor import Lock, WorkflowError, initialize, load_runtime, step
from research_loop.watchdog import main as watchdog_main
from research_loop.capture_environment import cuda_runtime_metadata


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def test_codex_response_schema_drops_only_unsupported_generation_assertions() -> None:
    full = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "artifact_type": {"const": "architecture_change"},
            "verdict": {"enum": ["approve", "reject"]},
            "reads": {
                "type": "array",
                "uniqueItems": True,
                "items": {"type": "string", "minLength": 1},
            }
        },
    }
    assert _codex_response_schema(full) == {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "artifact_type": {
                "const": "architecture_change",
                "type": "string",
            },
            "verdict": {
                "enum": ["approve", "reject"],
                "type": "string",
            },
            "reads": {
                "type": "array",
                "items": {"type": "string", "minLength": 1},
            }
        },
    }
    assert full["properties"]["reads"]["uniqueItems"] is True


def approve_job(
    root: Path,
    spec: Path,
    run_id: str,
    frozen: list[str],
    review_only: list[Path] | None = None,
):
    lock = root / f"{run_id}.lock.json"
    create_freeze(root, lock, [*frozen, spec.name])
    prompt = root / "review.md"
    prompt.write_text("review", encoding="utf-8")
    schema = root / "schema.json"
    write_json(schema, {"type": "object"})
    result = root / "review-result.json"
    write_json(result, {"verdict": "approve"})
    approval = root / f"{run_id}.approval.json"
    create_binding(
        root, approval, run_id=run_id, node_id="review",
        review_result=result, prompt_file=prompt, schema_file=schema,
        context_files=[lock, spec, *(review_only or [])], route_field="verdict",
    )
    return lock, approval


def test_remote_job_writes_done_and_fingerprints_fresh_artifact() -> None:
    import tempfile
    temp = tempfile.TemporaryDirectory()
    tmp_path = Path(temp.name)
    worker = tmp_path / "worker.py"
    worker.write_text(
        "from pathlib import Path\nPath('result.json').write_text('{\\\"ok\\\": true}')\n",
        encoding="utf-8",
    )
    spec = tmp_path / "spec.json"
    write_json(
        spec,
        {
            "schema_version": 1,
            "cwd": str(tmp_path),
            "freeze_inputs": ["worker.py"],
            "stages": [{"id": "work", "argv": [sys.executable, "worker.py"]}],
            "artifacts": ["result.json"],
        },
    )
    root = tmp_path / "jobs"
    lock, approval = approve_job(tmp_path, spec, "run-1", ["worker.py"])
    assert run_job(
        spec, "run-1", root, lock_path=lock, approval_path=approval,
        approval_sha256=sha256_file(approval),
    ) == 0
    done = load_json(root / "run-1" / "done.json")
    assert done["run_id"] == "run-1"
    assert "artifacts/result.json" in done["artifact_fingerprints"]
    assert (root / "run-1" / "artifacts" / "result.json").is_file()
    assert status(root, "run-1") == 0
    temp.cleanup()


def test_cuda_runtime_metadata_has_stable_schema() -> None:
    metadata = cuda_runtime_metadata()
    assert {"torch_cuda_build", "cudnn_runtime", "cuda_available", "nvcc"} <= set(metadata)


def test_remote_job_does_not_require_reviewer_only_context_on_worker() -> None:
    import tempfile
    temp = tempfile.TemporaryDirectory()
    tmp_path = Path(temp.name)
    worker = tmp_path / "worker.py"
    worker.write_text(
        "from pathlib import Path\nPath('result.json').write_text('{}')\n",
        encoding="utf-8",
    )
    private_notes = tmp_path / "private-review-notes.md"
    private_notes.write_text("reviewer context stays local", encoding="utf-8")
    spec = tmp_path / "spec.json"
    write_json(spec, {
        "schema_version": 1,
        "cwd": str(tmp_path),
        "freeze_inputs": ["worker.py"],
        "stages": [{"id": "work", "argv": [sys.executable, "worker.py"]}],
        "artifacts": ["result.json"],
    })
    jobs = tmp_path / "jobs"
    lock, approval = approve_job(
        tmp_path, spec, "private-review-context", ["worker.py"],
        review_only=[private_notes],
    )
    private_notes.unlink()
    assert run_job(
        spec, "private-review-context", jobs, lock_path=lock,
        approval_path=approval, approval_sha256=sha256_file(approval),
    ) == 0
    done = load_json(jobs / "private-review-context" / "done.json")
    assert "private-review-notes.md" not in done["declared_input_fingerprints"]
    temp.cleanup()


def test_remote_job_rejects_stale_artifact() -> None:
    import tempfile
    temp = tempfile.TemporaryDirectory()
    tmp_path = Path(temp.name)
    artifact = tmp_path / "old.json"
    artifact.write_text("{}", encoding="utf-8")
    spec = tmp_path / "spec.json"
    write_json(
        spec,
        {
            "schema_version": 1,
            "cwd": str(tmp_path),
            "stages": [{"id": "noop", "argv": [sys.executable, "-c", "pass"]}],
            "artifacts": ["old.json"],
        },
    )
    root = tmp_path / "jobs"
    lock, approval = approve_job(tmp_path, spec, "run-2", [])
    assert run_job(
        spec, "run-2", root, lock_path=lock, approval_path=approval,
        approval_sha256=sha256_file(approval),
    ) == 1
    failure = load_json(root / "run-2" / "failed.json")
    assert "stale required artifacts" in failure["error"]
    temp.cleanup()


def test_supervisor_routes_failed_contract_to_human_pause() -> None:
    import tempfile
    temp = tempfile.TemporaryDirectory()
    tmp_path = Path(temp.name)
    workflow = tmp_path / "workflow.json"
    write_json(
        workflow,
        {
            "schema_version": 1,
            "name": "test-flow",
            "workspace": ".",
            "state_dir": ".state",
            "start": "contract",
            "nodes": {
                "contract": {
                    "kind": "command",
                    "argv": [sys.executable, "-c", "print('old interface')"],
                    "stdout_regex": "--samples",
                    "next": "done",
                    "on_failure": "human",
                },
                "human": {
                    "kind": "human",
                    "instructions": "repair the interface",
                    "next": "done",
                },
                "done": {"kind": "end", "status": "complete"},
            },
        },
    )
    runtime = load_runtime(workflow)
    state = initialize(runtime)
    state = step(runtime, state)
    assert state["current"] == "human"
    state = step(runtime, state)
    assert state["status"] == "paused"
    assert state["last_result"]["reason"] == "repair the interface"
    temp.cleanup()


def test_workflow_rejects_missing_edge() -> None:
    import tempfile
    temp = tempfile.TemporaryDirectory()
    tmp_path = Path(temp.name)
    workflow = tmp_path / "workflow.json"
    write_json(
        workflow,
        {
            "schema_version": 1,
            "name": "bad",
            "start": "a",
            "nodes": {"a": {"kind": "command", "argv": ["true"], "next": "missing"}},
        },
    )
    try:
        load_runtime(workflow)
    except WorkflowError as exc:
        assert "missing node" in str(exc)
    else:
        raise AssertionError("missing workflow edge was accepted")
    temp.cleanup()


def test_result_schema_is_strict_for_codex_structured_output() -> None:
    schema = load_json(Path(__file__).parent / "schemas" / "result.schema.json")

    def visit(node):
        if isinstance(node, dict):
            if node.get("type") == "object":
                assert node.get("additionalProperties") is False
            for value in node.values():
                visit(value)
        elif isinstance(node, list):
            for value in node:
                visit(value)

    visit(schema)


def test_freeze_detects_post_review_change() -> None:
    import tempfile
    temp = tempfile.TemporaryDirectory()
    root = Path(temp.name)
    tracked = root / "tracked.txt"
    tracked.write_text("reviewed", encoding="utf-8")
    lock = root / "lock.json"
    create_freeze(root, lock, ["tracked.txt"])
    assert verify_freeze(root, lock)["files"]
    tracked.write_text("changed", encoding="utf-8")
    try:
        verify_freeze(root, lock)
    except RuntimeError as exc:
        assert "frozen inputs changed" in str(exc)
    else:
        raise AssertionError("post-review change was not detected")
    temp.cleanup()


def test_remote_job_rejects_replacement_lock_after_approval() -> None:
    import tempfile
    temp = tempfile.TemporaryDirectory()
    root = Path(temp.name)
    worker = root / "worker.py"
    worker.write_text("print('old')\n", encoding="utf-8")
    spec = root / "spec.json"
    write_json(spec, {
        "schema_version": 1,
        "cwd": str(root),
        "freeze_inputs": ["worker.py"],
        "stages": [{"id": "work", "argv": [sys.executable, "worker.py"]}],
        "artifacts": [],
    })
    lock, approval = approve_job(root, spec, "replace-lock", ["worker.py"])
    worker.write_text("print('changed')\n", encoding="utf-8")
    create_freeze(root, lock, ["worker.py", "spec.json"])
    jobs = root / "jobs"
    assert run_job(
        spec, "replace-lock", jobs, lock_path=lock,
        approval_path=approval, approval_sha256=sha256_file(approval),
    ) == 1
    failure = load_json(jobs / "replace-lock" / "failed.json")
    assert "approved lock bytes changed" in failure["error"]
    temp.cleanup()


def test_remote_job_stops_after_mid_job_frozen_mutation() -> None:
    import tempfile
    temp = tempfile.TemporaryDirectory()
    root = Path(temp.name)
    tracked = root / "tracked.txt"
    tracked.write_text("reviewed", encoding="utf-8")
    mutate = root / "mutate.py"
    mutate.write_text(
        "from pathlib import Path\nPath('tracked.txt').write_text('changed')\n",
        encoding="utf-8",
    )
    marker = root / "should-not-run.txt"
    spec = root / "spec.json"
    write_json(spec, {
        "schema_version": 1,
        "cwd": str(root),
        "freeze_inputs": ["tracked.txt", "mutate.py"],
        "stages": [
            {"id": "mutate", "argv": [sys.executable, "mutate.py"]},
            {"id": "later", "argv": [sys.executable, "-c",
             "from pathlib import Path; Path('should-not-run.txt').write_text('bad')"]},
        ],
        "artifacts": [],
    })
    lock, approval = approve_job(
        root, spec, "mid-mutation", ["tracked.txt", "mutate.py"]
    )
    jobs = root / "jobs"
    assert run_job(
        spec, "mid-mutation", jobs, lock_path=lock,
        approval_path=approval, approval_sha256=sha256_file(approval),
    ) == 1
    assert not marker.exists()
    temp.cleanup()


def test_supervisor_rejects_resume_after_workflow_mutation() -> None:
    import tempfile
    temp = tempfile.TemporaryDirectory()
    root = Path(temp.name)
    workflow = root / "workflow.json"
    value = {
        "schema_version": 1, "name": "resume", "workspace": ".",
        "state_dir": ".state", "start": "done",
        "nodes": {"done": {"kind": "end", "status": "complete"}},
    }
    write_json(workflow, value)
    runtime = load_runtime(workflow)
    initialize(runtime)
    value["max_steps"] = 2
    write_json(workflow, value)
    changed_runtime = load_runtime(workflow)
    state = initialize(changed_runtime)
    assert state["status"] == "paused"
    assert "workflow changed" in state["last_result"]["reason"]
    temp.cleanup()


def test_fable_mailbox_round_trip_is_structured_and_hashed() -> None:
    import tempfile
    temp = tempfile.TemporaryDirectory()
    root = Path(temp.name)
    (root / "prompt.md").write_text("review", encoding="utf-8")
    write_json(root / "schema.json", {
        "type": "object",
        "additionalProperties": False,
        "required": ["verdict"],
        "properties": {"verdict": {"enum": ["approve", "reject"]}},
    })
    (root / "context.txt").write_text("frozen", encoding="utf-8")
    request_id = "mailbox-test"

    def responder():
        request_path = (
            root / ".research_loop" / "handoffs" / "inbox"
            / f"{request_id}.request.json"
        )
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline and not request_path.is_file():
            time.sleep(0.01)
        assert request_path.is_file()
        request = load_json(request_path)
        hashes = {item["path"]: item["sha256"]
                  for item in request["context_files"]}
        assert hashes["context.txt"] == sha256_file(root / "context.txt")
        response_path = (
            root / ".research_loop" / "handoffs" / "outbox"
            / f"{request_id}.response.json"
        )
        atomic_write_json(response_path, {"verdict": "approve"})

    thread = threading.Thread(target=responder)
    thread.start()
    code, result = run_agent({
        "provider": "fable_mailbox",
        "request_id": request_id,
        "run_id": "run",
        "node_id": "review",
        "prompt_file": "prompt.md",
        "schema_file": "schema.json",
        "context_files": ["context.txt"],
        "mailbox_poll_sec": 0.01,
    }, root, root / "output", timeout_sec=5)
    thread.join(timeout=5)
    assert code == 0 and result == {"verdict": "approve"}
    temp.cleanup()


def test_watchdog_completes_terminal_workflow_and_writes_heartbeat() -> None:
    import tempfile
    temp = tempfile.TemporaryDirectory()
    root = Path(temp.name)
    workflow = root / "workflow.json"
    write_json(workflow, {
        "schema_version": 1,
        "name": "watchdog-test",
        "workspace": ".",
        "state_dir": ".state",
        "start": "done",
        "nodes": {"done": {"kind": "end", "status": "complete"}},
    })
    assert watchdog_main([
        str(workflow), "--interval-sec", "0.01", "--heartbeat-sec", "0.01"
    ]) == 0
    heartbeat = load_json(root / ".state" / "watchdog-test.watchdog.json")
    assert heartbeat["status"] == "complete"
    temp.cleanup()


def test_lock_reclaims_only_provably_dead_owner() -> None:
    import tempfile
    temp = tempfile.TemporaryDirectory()
    root = Path(temp.name)
    lock_path = root / "worker.lock"
    lock_path.write_text("99999999\n", encoding="utf-8")
    with Lock(lock_path):
        assert int(lock_path.read_text(encoding="utf-8")) > 0
    assert not lock_path.exists()

    lock_path.write_text(f"{os.getpid()}\n", encoding="utf-8")
    try:
        with Lock(lock_path):
            raise AssertionError("live lock was reclaimed")
    except WorkflowError as exc:
        assert "lock already exists" in str(exc)
    else:
        raise AssertionError("live lock was accepted")
    temp.cleanup()
