"""Inactive adapter from existing reviewer/test interfaces to preflight fanout.

Nothing imports or invokes this module from an active workflow.  A future
workflow may supply a reviewed JSON configuration to its CLI.  The adapter's
small surface makes provider and subprocess calls injectable for unit tests.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Mapping, Optional, Sequence, Tuple

from .agents import run_agent
from .preflight import BranchContext, BranchResult, RetryClass, digest_json
from .supervisor_fanout import PreflightCoordinator, QuorumPolicy


AgentRunner = Callable[[Dict[str, Any], Path, Path, int], Tuple[int, Optional[Dict[str, Any]]]]
CommandRunner = Callable[..., subprocess.CompletedProcess[str]]


class IntegrationError(RuntimeError):
    pass


@dataclass(frozen=True)
class IntegrationConfig:
    workspace: Path
    state_dir: Path
    workflow_path: Path
    lock_path: Path
    spec: Mapping[str, Any]
    fable_node: Mapping[str, Any]
    sol_node: Mapping[str, Any]
    test_node: Mapping[str, Any]
    max_attempts: int = 2
    quorum_policy: QuorumPolicy = QuorumPolicy()


def _resolve(base: Path, value: str) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (base / path).resolve()


def load_config(path: Path) -> IntegrationConfig:
    """Load a future, separate integration config; no active-workflow defaults."""
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if value.get("schema_version") != 1:
        raise IntegrationError("integration config schema_version must be 1")
    base = path.parent.resolve()
    workspace = _resolve(base, str(value.get("workspace", ".")))
    required = ("state_dir", "workflow", "lock", "spec", "fable", "sol", "tests")
    missing = [key for key in required if key not in value]
    if missing:
        raise IntegrationError(f"integration config missing: {', '.join(missing)}")
    fable = dict(value["fable"])
    sol = dict(value["sol"])
    tests = dict(value["tests"])
    if fable.get("provider") != "fable_mailbox":
        raise IntegrationError("fable.provider must be fable_mailbox")
    if sol.get("provider") != "codex":
        raise IntegrationError("sol.provider must be codex")
    if not isinstance(tests.get("argv"), list) or not tests["argv"]:
        raise IntegrationError("tests.argv must be a non-empty command list")
    if not isinstance(value["spec"], dict):
        raise IntegrationError("spec must be an object")
    return IntegrationConfig(
        workspace=workspace,
        state_dir=_resolve(workspace, str(value["state_dir"])),
        workflow_path=_resolve(workspace, str(value["workflow"])),
        lock_path=_resolve(workspace, str(value["lock"])),
        spec=dict(value["spec"]),
        fable_node=fable,
        sol_node=sol,
        test_node=tests,
        max_attempts=int(value.get("max_attempts", 2)),
        quorum_policy=QuorumPolicy.from_mapping(value.get("quorum")),
    )


def _review_result(branch: str, returncode: int, value: Mapping[str, Any] | None) -> BranchResult:
    if returncode != 0 or value is None:
        if branch == "fable" and returncode in {75, 124}:
            return BranchResult(
                "failed",
                RetryClass.UNAVAILABLE,
                detail="Fable mailbox unavailable or did not respond before its deadline",
                evidence={"returncode": returncode, "provider": "fable_mailbox"},
            )
        retry = RetryClass.TRANSIENT if returncode in {75, 76, 124} else RetryClass.PERMANENT_FAILURE
        return BranchResult(
            "failed",
            retry,
            detail=f"{branch} reviewer exited with {returncode}",
            evidence={"returncode": returncode},
        )
    verdict = value.get("verdict")
    evidence = {
        "provider": "fable_mailbox" if branch == "fable" else "codex",
        "review_sha256": digest_json(value),
        "verdict": verdict,
    }
    if verdict == "approve":
        return BranchResult("approved", evidence=evidence)
    if verdict in {"reject", "escalate"}:
        return BranchResult(
            "rejected",
            RetryClass.SCIENTIFIC_REJECTION,
            detail=f"{branch} reviewer verdict: {verdict}",
            evidence=evidence,
        )
    return BranchResult(
        "failed",
        RetryClass.PERMANENT_FAILURE,
        detail=f"{branch} reviewer returned unsupported verdict: {verdict!r}",
        evidence=evidence,
    )


def reviewer_operation(
    branch: str,
    node: Mapping[str, Any],
    workspace: Path,
    *,
    agent_runner: AgentRunner = run_agent,
) -> Callable[[BranchContext], BranchResult]:
    """Adapt the existing ``run_agent`` contracts into an isolated branch."""
    expected_provider = "fable_mailbox" if branch == "fable" else "codex"
    if node.get("provider") != expected_provider:
        raise IntegrationError(f"{branch} node must use provider {expected_provider}")

    def operation(context: BranchContext) -> BranchResult:
        attempt_node = dict(node)
        # ``run_agent`` requires a unique mailbox request ID.  Binding it to the
        # attempt also makes recovery artifacts independently auditable.
        attempt_node.update({
            "run_id": f"preflight-{context.attempt_id}",
            "node_id": f"preflight_{branch}",
            "request_id": f"preflight-{context.attempt_id}",
        })
        timeout = int(attempt_node.get("timeout_sec", 600))
        try:
            returncode, value = agent_runner(attempt_node, workspace, context.attempt_dir, timeout)
        except TimeoutError as exc:
            retry = RetryClass.UNAVAILABLE if branch == "fable" else RetryClass.TRANSIENT
            return BranchResult("failed", retry, detail=f"{branch} timeout: {exc}")
        except OSError as exc:
            retry = RetryClass.UNAVAILABLE if branch == "fable" else RetryClass.TRANSIENT
            return BranchResult("failed", retry, detail=f"{branch} provider unavailable: {exc}")
        except BaseException as exc:
            return BranchResult(
                "failed", RetryClass.PERMANENT_FAILURE,
                detail=f"{branch} provider adapter error: {type(exc).__name__}: {exc}",
            )
        return _review_result(branch, returncode, value)

    return operation


def _hash_text(value: str | bytes | None) -> str:
    if isinstance(value, str):
        value = value.encode("utf-8")
    return hashlib.sha256(value or b"").hexdigest()


def test_operation(
    node: Mapping[str, Any],
    workspace: Path,
    *,
    command_runner: CommandRunner = subprocess.run,
) -> Callable[[BranchContext], BranchResult]:
    """Adapt a deterministic test command to the third preflight branch."""
    argv = list(node.get("argv", []))
    if not argv or not all(isinstance(part, str) for part in argv):
        raise IntegrationError("test argv must contain only strings")
    timeout = int(node.get("timeout_sec", 600))
    cwd = _resolve(workspace, str(node.get("cwd", ".")))
    transient_codes = {int(code) for code in node.get("transient_exit_codes", [75, 76, 124])}

    def operation(context: BranchContext) -> BranchResult:
        try:
            completed = command_runner(
                argv, cwd=cwd, text=True, capture_output=True, timeout=timeout, check=False
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            return BranchResult(
                "failed", RetryClass.TRANSIENT,
                detail=f"deterministic test infrastructure error: {type(exc).__name__}: {exc}",
            )
        evidence = {
            "argv": argv,
            "returncode": completed.returncode,
            "stdout_sha256": _hash_text(completed.stdout),
            "stderr_sha256": _hash_text(completed.stderr),
            "attempt_id": context.attempt_id,
        }
        if completed.returncode == 0:
            return BranchResult("passed", evidence=evidence)
        retry = RetryClass.TRANSIENT if completed.returncode in transient_codes else RetryClass.PERMANENT_FAILURE
        return BranchResult(
            "failed", retry,
            detail=f"deterministic test command exited with {completed.returncode}",
            evidence=evidence,
        )

    return operation


def build_operations(
    config: IntegrationConfig,
    *,
    agent_runner: AgentRunner = run_agent,
    command_runner: CommandRunner = subprocess.run,
) -> dict[str, Callable[[BranchContext], BranchResult]]:
    return {
        "fable": reviewer_operation("fable", config.fable_node, config.workspace, agent_runner=agent_runner),
        "sol": reviewer_operation("sol", config.sol_node, config.workspace, agent_runner=agent_runner),
        "test": test_operation(config.test_node, config.workspace, command_runner=command_runner),
    }


def run_config(
    config: IntegrationConfig,
    *,
    agent_runner: AgentRunner = run_agent,
    command_runner: CommandRunner = subprocess.run,
) -> dict[str, Any]:
    """Run the inactive fanout and verify its receipt before returning success."""
    coordinator = PreflightCoordinator(
        config.state_dir, config.workflow_path, config.lock_path, config.spec,
        max_attempts=config.max_attempts, quorum_policy=config.quorum_policy,
    )
    outcome = coordinator.run_preflight(
        build_operations(config, agent_runner=agent_runner, command_runner=command_runner)
    )
    result = {
        "joined": outcome["joined"],
        "results": {branch: value.as_dict() for branch, value in outcome["results"].items()},
        "receipt": str(outcome["receipt"]) if outcome["receipt"] else None,
    }
    if outcome["joined"]:
        result["verified_receipt"] = coordinator.verify_receipt()
    return result


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True, help="separately reviewed inactive integration config")
    parser.add_argument("--verify-receipt", action="store_true", help="verify only; do not call reviewers or tests")
    args = parser.parse_args(argv)
    try:
        config = load_config(args.config.resolve())
        if args.verify_receipt:
            coordinator = PreflightCoordinator(
                config.state_dir, config.workflow_path, config.lock_path, config.spec,
                max_attempts=config.max_attempts, quorum_policy=config.quorum_policy,
            )
            result: Mapping[str, Any] = {"verified_receipt": coordinator.verify_receipt()}
        else:
            result = run_config(config)
    except BaseException as exc:
        print(f"preflight integration error: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0 if result.get("joined", True) else 2


if __name__ == "__main__":
    sys.exit(main())
