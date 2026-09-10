from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .agents import run_agent
from .architecture_intake import IntakeError, validate_authorized_intake
from .io import append_jsonl, atomic_write_json, load_json, sha256_file, utc_now
from .review_binding import create_binding, verify_binding


TERMINAL = {"complete", "failed", "paused"}


class WorkflowError(RuntimeError):
    pass


@dataclass
class Runtime:
    workflow_path: Path
    workflow: dict[str, Any]
    workspace: Path
    state_dir: Path
    state_path: Path
    events_path: Path
    loaded_workflow_sha256: str


def _architecture_declaration(workflow: dict[str, Any]) -> dict[str, Any]:
    declaration = workflow.get("architecture_intake")
    if declaration is None:
        # Backward-compatible for external/test workflows.  Repository-owned
        # workflows declare the legacy mode explicitly.
        return {"mode": "legacy_undeclared"}
    if not isinstance(declaration, dict):
        raise WorkflowError("architecture_intake must be an object")
    mode = declaration.get("mode")
    if mode == "legacy_no_material_change":
        if set(declaration) != {"mode"}:
            raise WorkflowError(
                "legacy architecture_intake declaration accepts only mode"
            )
        return declaration
    if mode != "material_change":
        raise WorkflowError(f"unknown architecture_intake mode: {mode!r}")
    expected = {"mode", "state", "requested_scope"}
    if set(declaration) != expected:
        raise WorkflowError(
            "material architecture_intake declaration requires exactly "
            "mode, state, and requested_scope"
        )
    state_path = declaration["state"]
    scope = declaration["requested_scope"]
    if not isinstance(state_path, str) or not state_path:
        raise WorkflowError("architecture_intake.state must be a non-empty string")
    if Path(state_path).is_absolute():
        raise WorkflowError("architecture_intake.state must be workspace-relative")
    if (
        not isinstance(scope, list)
        or not scope
        or any(not isinstance(item, str) or not item for item in scope)
        or len(scope) != len(set(scope))
    ):
        raise WorkflowError(
            "architecture_intake.requested_scope must be a non-empty unique string list"
        )
    return declaration


def _workspace_path(runtime: Runtime, relative: str) -> Path:
    candidate = (runtime.workspace / relative).resolve()
    try:
        candidate.relative_to(runtime.workspace)
    except ValueError as exc:
        raise WorkflowError(f"workflow path escapes workspace: {relative}") from exc
    return candidate


def load_runtime(workflow_path: Path) -> Runtime:
    workflow_path = workflow_path.resolve()
    digest_before = sha256_file(workflow_path)
    workflow = load_json(workflow_path)
    digest_after = sha256_file(workflow_path)
    if digest_before != digest_after:
        raise WorkflowError("workflow changed while it was being loaded")
    if workflow.get("schema_version") != 1:
        raise WorkflowError("workflow schema_version must be 1")
    workspace_value = workflow.get("workspace", ".")
    workspace = (workflow_path.parent / workspace_value).resolve()
    state_value = workflow.get("state_dir", ".research_loop")
    state_dir = (workspace / state_value).resolve()
    if workflow.get("architecture_intake") is None:
        repository_workflows = (workspace / "research_loop" / "workflows").resolve()
        try:
            workflow_path.relative_to(repository_workflows)
        except ValueError:
            # Temporary/external callers retain backward compatibility.  A
            # repository-owned workflow may never bypass the gate by omission.
            pass
        else:
            raise WorkflowError(
                "repository workflow must explicitly declare architecture_intake"
            )
    _architecture_declaration(workflow)
    run_name = workflow["name"]
    nodes = workflow.get("nodes", {})
    if workflow.get("start") not in nodes:
        raise WorkflowError("workflow start node is missing")
    for node_id, node in nodes.items():
        for edge in _edges(node):
            if edge is not None and edge not in nodes:
                raise WorkflowError(f"node {node_id} points to missing node {edge}")
    return Runtime(
        workflow_path=workflow_path,
        workflow=workflow,
        workspace=workspace,
        state_dir=state_dir,
        state_path=state_dir / f"{run_name}.state.json",
        events_path=state_dir / f"{run_name}.events.jsonl",
        loaded_workflow_sha256=digest_after,
    )


def _edges(node: dict[str, Any]) -> list[str | None]:
    edges = [node.get("next"), node.get("on_failure"), node.get("on_timeout")]
    edges.extend(node.get("next_by", {}).values())
    return edges


def _create_architecture_binding(runtime: Runtime) -> dict[str, Any]:
    declaration = _architecture_declaration(runtime.workflow)
    workflow_sha256 = sha256_file(runtime.workflow_path)
    if workflow_sha256 != runtime.loaded_workflow_sha256:
        raise WorkflowError("workflow changed after it was loaded")
    if declaration["mode"] != "material_change":
        return {
            "mode": declaration["mode"],
            "workflow_sha256": workflow_sha256,
        }

    intake_state_path = _workspace_path(runtime, declaration["state"])
    try:
        validated = validate_authorized_intake(runtime.workspace, intake_state_path)
    except (IntakeError, OSError, ValueError, KeyError) as exc:
        raise WorkflowError(f"architecture intake authorization failed: {exc}") from exc
    intake_state = validated["state"]
    ratification = validated["ratification"]
    requested = set(declaration["requested_scope"])
    authorized = set(ratification["authorized_scope"])
    forbidden = set(ratification["forbidden_scope"])
    unauthorized = requested - authorized
    prohibited = requested & forbidden
    if unauthorized or prohibited:
        raise WorkflowError(
            "requested architecture scope is not authorized: "
            f"unauthorized={sorted(unauthorized)}, prohibited={sorted(prohibited)}"
        )

    artifact_bindings = [
        {
            "artifact": artifact,
            "path": entry["path"],
            "sha256": entry["sha256"],
        }
        for artifact, entry in sorted(intake_state["artifacts"].items())
    ]
    ratification_path = validated["paths"]["ratification"]
    return {
        "mode": "material_change",
        "change_id": intake_state["change_id"],
        "workflow_sha256": workflow_sha256,
        "intake_state": declaration["state"],
        "intake_state_sha256": sha256_file(intake_state_path),
        "ratification_sha256": sha256_file(ratification_path),
        "consensus_sha256": ratification["consensus_sha256"],
        "requested_scope": sorted(requested),
        "authorized_scope": sorted(authorized),
        "forbidden_scope": sorted(forbidden),
        "artifact_bindings": artifact_bindings,
    }


def _verify_architecture_binding(runtime: Runtime, state: dict[str, Any]) -> None:
    recorded = state.get("architecture_authorization")
    if not isinstance(recorded, dict):
        raise WorkflowError("supervisor state lacks architecture authorization binding")
    current = _create_architecture_binding(runtime)
    if current != recorded:
        raise WorkflowError("architecture authorization bytes or scope changed")


def initialize(runtime: Runtime, force: bool = False) -> dict[str, Any]:
    if runtime.state_path.exists() and not force:
        state = load_json(runtime.state_path)
        current_digest = sha256_file(runtime.workflow_path)
        if state.get("workflow_sha256") != current_digest:
            state["status"] = "paused"
            state["last_result"] = {
                "reason": "workflow changed since this run initialized; start a new run"
            }
            _event(runtime, state, "workflow_binding_failed", {
                "node": state.get("current")
            })
            _save(runtime, state)
            return state
        try:
            _verify_architecture_binding(runtime, state)
        except BaseException as exc:
            state["status"] = "paused"
            state["last_result"] = {
                "reason": f"architecture authorization failed: {type(exc).__name__}: {exc}"
            }
            _event(runtime, state, "architecture_authorization_failed", {
                "node": state.get("current")
            })
            _save(runtime, state)
        return state
    architecture_authorization = _create_architecture_binding(runtime)
    run_id = f"{runtime.workflow['name']}-{time.strftime('%Y%m%dT%H%M%S')}-{uuid.uuid4().hex[:8]}"
    state = {
        "schema_version": 1,
        "workflow": str(runtime.workflow_path),
        "workflow_sha256": sha256_file(runtime.workflow_path),
        "architecture_authorization": architecture_authorization,
        "run_id": run_id,
        "status": "running",
        "current": runtime.workflow["start"],
        "created_at": utc_now(),
        "updated_at": utc_now(),
        "steps": 0,
        "visits": {},
        "approvals": [],
        "bindings": {},
        "last_result": None,
    }
    atomic_write_json(runtime.state_path, state)
    _event(runtime, state, "initialized", {})
    return state


def _event(runtime: Runtime, state: dict[str, Any], kind: str, data: dict[str, Any]) -> None:
    append_jsonl(
        runtime.events_path,
        {"at": utc_now(), "run_id": state["run_id"], "event": kind, **data},
    )


def _save(runtime: Runtime, state: dict[str, Any]) -> None:
    state["updated_at"] = utc_now()
    atomic_write_json(runtime.state_path, state)


def _format(value: str, runtime: Runtime, state: dict[str, Any]) -> str:
    variables = {
        "run_id": state["run_id"],
        "workspace": str(runtime.workspace),
        "state_dir": str(runtime.state_dir),
        "step": str(state["steps"]),
    }
    for node_id, binding in state.get("bindings", {}).items():
        variables[f"{node_id}_binding_sha256"] = binding["sha256"]
    return value.format_map(variables)


def _command(
    runtime: Runtime,
    state: dict[str, Any],
    node_id: str,
    node: dict[str, Any],
) -> tuple[str, dict[str, Any]]:
    visit = state["visits"].get(node_id, 0)
    output_dir = runtime.state_dir / "runs" / state["run_id"] / f"{state['steps']:03d}_{node_id}_{visit}"
    output_dir.mkdir(parents=True, exist_ok=True)
    argv = [_format(part, runtime, state) for part in node["argv"]]
    cwd = runtime.workspace / node.get("cwd", ".")
    stdout_path = output_dir / "stdout.log"
    stderr_path = output_dir / "stderr.log"
    started_ns = time.time_ns()
    timed_out = False
    returncode = -1
    with stdout_path.open("w", encoding="utf-8") as stdout, stderr_path.open(
        "w", encoding="utf-8"
    ) as stderr:
        try:
            proc = subprocess.run(
                argv,
                cwd=cwd,
                stdout=stdout,
                stderr=stderr,
                text=True,
                timeout=node.get("command_timeout_sec", node.get("timeout_sec", 3600)),
                check=False,
            )
            returncode = proc.returncode
        except subprocess.TimeoutExpired:
            timed_out = True
    stdout_text = stdout_path.read_text(encoding="utf-8")
    stderr_text = stderr_path.read_text(encoding="utf-8")
    success = returncode in node.get("success_exit_codes", [0])
    if node.get("stdout_regex"):
        pattern = _format(node["stdout_regex"], runtime, state)
        success = success and bool(re.search(pattern, stdout_text, re.M))
    if node.get("forbid_regex"):
        pattern = _format(node["forbid_regex"], runtime, state)
        success = success and not bool(
            re.search(pattern, stdout_text + "\n" + stderr_text, re.M)
        )
    files = []
    for relative in node.get("require_fresh_files", []):
        path = runtime.workspace / _format(relative, runtime, state)
        fresh = path.is_file() and path.stat().st_mtime_ns >= started_ns
        files.append({"path": str(path), "fresh": fresh})
        success = success and fresh
    result = {
        "argv": argv,
        "returncode": returncode,
        "timed_out": timed_out,
        "stdout": str(stdout_path),
        "stderr": str(stderr_path),
        "required_files": files,
    }
    if timed_out:
        return "timeout", result
    return ("success" if success else "failure"), result


def _poll(
    runtime: Runtime,
    state: dict[str, Any],
    node_id: str,
    node: dict[str, Any],
) -> tuple[str, dict[str, Any]]:
    deadline = time.monotonic() + node.get("timeout_sec", 3600)
    pending_codes = node.get("pending_exit_codes", [75, 76])
    attempt = 0
    last: dict[str, Any] = {}
    while time.monotonic() < deadline:
        attempt += 1
        outcome, result = _command(runtime, state, node_id, node)
        last = result
        if result["returncode"] in pending_codes:
            time.sleep(min(node.get("interval_sec", 30), 60))
            continue
        return outcome, {**result, "poll_attempts": attempt}
    return "timeout", {**last, "poll_attempts": attempt}


def _agent(
    runtime: Runtime,
    state: dict[str, Any],
    node_id: str,
    node: dict[str, Any],
) -> tuple[str, dict[str, Any]]:
    visit = state["visits"].get(node_id, 0)
    output_dir = runtime.state_dir / "runs" / state["run_id"] / f"{state['steps']:03d}_{node_id}_{visit}"
    formatted_node = dict(node)
    for field in ("prompt_file", "schema_file"):
        formatted_node[field] = _format(node[field], runtime, state)
    formatted_node["context_files"] = [
        _format(value, runtime, state) for value in node.get("context_files", [])
    ]
    if node.get("context_catalog"):
        catalog_path = runtime.workspace / _format(
            node["context_catalog"], runtime, state
        )
        catalog = load_json(catalog_path)
        profile = node["context_profile"]
        catalog_files = catalog.get("profiles", {}).get(profile)
        if not isinstance(catalog_files, list):
            raise WorkflowError(f"missing context catalog profile: {profile}")
        formatted_node["context_files"] = list(dict.fromkeys([
            _format(node["context_catalog"], runtime, state),
            *catalog_files, *formatted_node["context_files"]
        ]))
    formatted_node["run_id"] = state["run_id"]
    formatted_node["node_id"] = node_id
    if node.get("request_id"):
        formatted_node["request_id"] = _format(
            node["request_id"], runtime, state
        )
    reviewed_paths = [
        runtime.workspace / formatted_node["prompt_file"],
        runtime.workspace / formatted_node["schema_file"],
        *[runtime.workspace / path for path in formatted_node["context_files"]],
    ]
    before = {str(path.resolve()): sha256_file(path) for path in reviewed_paths}
    code, value = run_agent(
        formatted_node,
        runtime.workspace,
        output_dir,
        timeout_sec=node.get("timeout_sec", 3600),
    )
    if code != 0 or value is None:
        return "failure", {"returncode": code, "output_dir": str(output_dir)}
    after = {str(path.resolve()): sha256_file(path) for path in reviewed_paths}
    if before != after:
        return "failure", {
            "returncode": code,
            "output_dir": str(output_dir),
            "reason": "reviewed files changed while the agent was running",
        }
    binding_result = None
    if node.get("binding_file"):
        binding_path = runtime.workspace / _format(
            node["binding_file"], runtime, state
        )
        result_path = output_dir / "result.json"
        binding_result = create_binding(
            runtime.workspace,
            binding_path,
            run_id=state["run_id"],
            node_id=node_id,
            review_result=result_path,
            prompt_file=reviewed_paths[0],
            schema_file=reviewed_paths[1],
            context_files=reviewed_paths[2:],
            route_field=node.get("route_field", "verdict"),
        )
        state["bindings"][node_id] = {
            "path": str(binding_path),
            "sha256": sha256_file(binding_path),
            "verdict": binding_result.get("verdict"),
        }
    route_field = node.get("route_field")
    outcome = str(value.get(route_field)) if route_field else "success"
    return outcome, {
        "returncode": code,
        "output_dir": str(output_dir),
        "value": value,
        "binding": binding_result,
    }


def _verify_approved_bindings(runtime: Runtime, state: dict[str, Any]) -> None:
    for node_id, record in state.get("bindings", {}).items():
        if record.get("verdict") != "approve":
            continue
        path = Path(record["path"])
        actual = sha256_file(path) if path.is_file() else None
        if actual != record["sha256"]:
            raise WorkflowError(
                f"approved review binding for {node_id} changed: {path}"
            )
        verify_binding(runtime.workspace, path, required_verdict="approve")


def step(runtime: Runtime, state: dict[str, Any], dry_run: bool = False) -> dict[str, Any]:
    if state["status"] in TERMINAL:
        return state
    current = state["current"]
    try:
        _verify_architecture_binding(runtime, state)
    except BaseException as exc:
        state["status"] = "paused"
        state["last_result"] = {
            "reason": f"architecture authorization failed: {type(exc).__name__}: {exc}"
        }
        _event(runtime, state, "architecture_authorization_failed", {"node": current})
        _save(runtime, state)
        return state
    try:
        _verify_approved_bindings(runtime, state)
    except BaseException as exc:
        state["status"] = "paused"
        state["last_result"] = {
            "reason": f"approved review binding failed: {type(exc).__name__}: {exc}"
        }
        _event(runtime, state, "review_binding_failed", {"node": current})
        _save(runtime, state)
        return state
    node = runtime.workflow["nodes"][current]
    visits = state["visits"].get(current, 0) + 1
    state["visits"][current] = visits
    max_visits = node.get("max_visits", 1)
    if visits > max_visits:
        state["status"] = "paused"
        state["last_result"] = {"reason": f"node {current} exceeded max_visits={max_visits}"}
        _event(runtime, state, "visit_limit", {"node": current})
        _save(runtime, state)
        return state
    state["steps"] += 1
    global_limit = runtime.workflow.get("max_steps", 50)
    if state["steps"] > global_limit:
        state["status"] = "paused"
        state["last_result"] = {"reason": f"workflow exceeded max_steps={global_limit}"}
        _save(runtime, state)
        return state
    _event(runtime, state, "node_started", {"node": current, "kind": node["kind"]})

    if dry_run:
        outcome, result = "success", {"dry_run": True}
    elif node["kind"] == "command":
        outcome, result = _command(runtime, state, current, node)
    elif node["kind"] == "poll":
        outcome, result = _poll(runtime, state, current, node)
    elif node["kind"] == "agent":
        outcome, result = _agent(runtime, state, current, node)
    elif node["kind"] == "human":
        if current not in state["approvals"]:
            state["status"] = "paused"
            state["last_result"] = {"reason": node["instructions"]}
            _event(runtime, state, "human_required", {"node": current})
            _save(runtime, state)
            return state
        outcome, result = "success", {"approved": True}
    elif node["kind"] == "end":
        state["status"] = node.get("status", "complete")
        state["last_result"] = {"message": node.get("message", "")}
        _event(runtime, state, "terminal", {"node": current, "status": state["status"]})
        _save(runtime, state)
        return state
    else:
        raise WorkflowError(f"unknown node kind: {node['kind']}")

    state["last_result"] = {"node": current, "outcome": outcome, **result}
    next_node = node.get("next_by", {}).get(outcome)
    if next_node is None:
        if outcome == "success":
            next_node = node.get("next")
        elif outcome == "timeout":
            next_node = node.get("on_timeout", node.get("on_failure"))
        else:
            next_node = node.get("on_failure")
    _event(runtime, state, "node_finished", {"node": current, "outcome": outcome, "next": next_node})
    if next_node is None:
        state["status"] = "failed" if outcome != "success" else "complete"
    else:
        state["current"] = next_node
    _save(runtime, state)
    return state


class Lock:
    def __init__(self, path: Path):
        self.path = path
        self.fd: int | None = None

    def __enter__(self) -> "Lock":
        self.path.parent.mkdir(parents=True, exist_ok=True)
        for attempt in range(2):
            try:
                self.fd = os.open(
                    self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY
                )
                break
            except FileExistsError as exc:
                if attempt or not self._reclaim_stale_owner():
                    raise WorkflowError(
                        f"supervisor lock already exists: {self.path}"
                    ) from exc
        assert self.fd is not None
        os.write(self.fd, f"{os.getpid()}\n".encode())
        return self

    def _reclaim_stale_owner(self) -> bool:
        """Remove a lock only when its recorded process is provably absent."""
        try:
            owner_text = self.path.read_text(encoding="utf-8").strip()
            owner_pid = int(owner_text)
        except (FileNotFoundError, OSError, TypeError, ValueError):
            return False
        if owner_pid <= 0:
            return False
        try:
            os.kill(owner_pid, 0)
        except ProcessLookupError:
            try:
                self.path.unlink()
            except FileNotFoundError:
                pass
            return True
        except PermissionError:
            return False
        return False

    def __exit__(self, *_: object) -> None:
        if self.fd is not None:
            os.close(self.fd)
        try:
            self.path.unlink()
        except FileNotFoundError:
            pass


def run(runtime: Runtime, once: bool = False, dry_run: bool = False) -> dict[str, Any]:
    state = initialize(runtime)
    if state["status"] == "paused":
        state["status"] = "running"
    with Lock(runtime.state_dir / f"{runtime.workflow['name']}.lock"):
        while state["status"] not in TERMINAL:
            state = step(runtime, state, dry_run=dry_run)
            if once:
                break
    return state


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("workflow", type=Path)
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init")
    init.add_argument("--force", action="store_true")
    execute = sub.add_parser("run")
    execute.add_argument("--once", action="store_true")
    execute.add_argument("--dry-run", action="store_true")
    sub.add_parser("status")
    approve = sub.add_parser("approve")
    approve.add_argument("node")
    args = parser.parse_args(argv)
    runtime = load_runtime(args.workflow)
    if args.command == "init":
        state = initialize(runtime, force=args.force)
    elif args.command == "run":
        state = run(runtime, once=args.once, dry_run=args.dry_run)
    elif args.command == "status":
        state = initialize(runtime)
    else:
        state = initialize(runtime)
        if state["current"] != args.node:
            raise WorkflowError(f"current node is {state['current']}, not {args.node}")
        if args.node not in state["approvals"]:
            state["approvals"].append(args.node)
        state["status"] = "running"
        _event(runtime, state, "approved", {"node": args.node})
        _save(runtime, state)
    print(json.dumps(state, indent=2, sort_keys=True))
    return 0 if state["status"] != "failed" else 1


if __name__ == "__main__":
    sys.exit(main())
