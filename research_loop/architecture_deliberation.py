"""Durable, fresh-context architecture deliberation before implementation.

This runner operationalizes the policy enforced by :mod:`architecture_intake`:

    verbatim directive -> graph/loop/claim/visibility/test proposal
      -> two independent interpretations -> cross-critique -> consensus
      -> HUMAN REQUIRED

It deliberately has no ratification transition.  Human approval remains a
separate, evidence-bound action in ``architecture_intake.py``; implementation
workflows must then present that approved intake to ``supervisor.py``.

The CLI uses the existing Codex, Claude, and Fable-mailbox transports.  Tests
and embedding callers may inject another executor with the same narrow
function signature.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import sys
import tempfile
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Optional

from .agents import run_agent
from .architecture_intake import (
    IntakeError,
    _load_verified_state,
    initialize_intake,
    record_consensus,
    record_critique,
    record_interpretation,
    validate_change,
    validate_consensus,
    validate_critique,
    validate_interpretation,
)
from .io import atomic_write_json, load_json, sha256_file, utc_now
from .supervisor import Lock, WorkflowError


class DeliberationError(RuntimeError):
    """A workflow, provenance, transport, or stage-validation failure."""


class RoleExecutionError(DeliberationError):
    """All configured executors failed, retaining every durable attempt."""

    def __init__(self, role: str, attempts: list[dict[str, Any]]):
        self.role = role
        self.attempts = attempts
        details = "; ".join(item["error"] for item in attempts)
        super().__init__(f"all executors failed for {role}: {details}")


Executor = Callable[
    [str, dict[str, Any], Path, Path, int],
    tuple[int, Optional[dict[str, Any]]],
]


STAGES = {
    "advocate": {
        "prompt": "research_loop/prompts/architecture_advocate.md",
        "schema": "research_loop/schemas/architecture_change.schema.json",
        "artifact": "change.json",
    },
    "systems": {
        "prompt": "research_loop/prompts/architecture_systems_interpreter.md",
        "schema": "research_loop/schemas/architecture_interpretation.schema.json",
        "artifact": "interpretation_systems.json",
    },
    "benchmark": {
        "prompt": "research_loop/prompts/architecture_benchmark_interpreter.md",
        "schema": "research_loop/schemas/architecture_interpretation.schema.json",
        "artifact": "interpretation_benchmark.json",
    },
    "critique": {
        "prompt": "research_loop/prompts/architecture_adversarial_reviewer.md",
        "schema": "research_loop/schemas/architecture_critique.schema.json",
        "artifact": "critique.json",
    },
    "consensus": {
        "prompt": "research_loop/prompts/architecture_adjudicator.md",
        "schema": "research_loop/schemas/architecture_consensus.schema.json",
        "artifact": "consensus.json",
    },
}

PHASE_TO_STAGE = {
    "advocate_pending": "advocate",
    "interpretations_pending": "interpretations",
    "critique_pending": "critique",
    "consensus_pending": "consensus",
}

ALLOWED_EXECUTOR_FIELDS = {
    "provider",
    "model",
    "reasoning_effort",
    "timeout_sec",
    "provider_attempts",
    "provider_attempt_timeout_sec",
    "mailbox_poll_sec",
    "max_context_chars_per_file",
}
ALLOWED_PROVIDERS = {"codex", "claude", "fable_mailbox"}


@dataclass(frozen=True)
class DeliberationRuntime:
    workflow_path: Path
    workflow: dict[str, Any]
    workspace: Path
    output_dir: Path
    state_path: Path
    intake_state_path: Path
    run_dir: Path
    workflow_sha256: str


def _root_path(root: Path, relative: str, label: str) -> Path:
    if not isinstance(relative, str) or not relative:
        raise DeliberationError(f"{label} must be a non-empty root-relative path")
    if Path(relative).is_absolute():
        raise DeliberationError(f"{label} must be root-relative: {relative}")
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise DeliberationError(f"{label} escapes workspace: {relative}") from exc
    return candidate


def _relative(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError as exc:
        raise DeliberationError(f"path is outside workspace: {path}") from exc


def _strict_keys(value: dict[str, Any], expected: set[str], label: str) -> None:
    unknown = set(value) - expected
    missing = expected - set(value)
    if unknown or missing:
        raise DeliberationError(
            f"{label} keys mismatch: missing={sorted(missing)}, unknown={sorted(unknown)}"
        )


def _validate_executor_config(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise DeliberationError(f"{label} must be an object")
    unknown = set(value) - ALLOWED_EXECUTOR_FIELDS
    if unknown:
        raise DeliberationError(f"{label} has unsupported fields: {sorted(unknown)}")
    provider = value.get("provider")
    if provider not in ALLOWED_PROVIDERS:
        raise DeliberationError(f"{label} has unsupported provider: {provider!r}")
    for field in (
        "timeout_sec", "provider_attempts", "provider_attempt_timeout_sec",
        "max_context_chars_per_file",
    ):
        if field in value and (not isinstance(value[field], int) or value[field] <= 0):
            raise DeliberationError(f"{label}.{field} must be a positive integer")
    if "mailbox_poll_sec" in value and (
        not isinstance(value["mailbox_poll_sec"], (int, float))
        or value["mailbox_poll_sec"] <= 0
    ):
        raise DeliberationError(f"{label}.mailbox_poll_sec must be positive")
    return dict(value)


def load_deliberation_runtime(workflow_path: Path) -> DeliberationRuntime:
    workflow_path = workflow_path.resolve()
    before = sha256_file(workflow_path)
    workflow = load_json(workflow_path)
    after = sha256_file(workflow_path)
    if before != after:
        raise DeliberationError("deliberation workflow changed while loading")
    if not isinstance(workflow, dict):
        raise DeliberationError("deliberation workflow must be a JSON object")
    expected = {
        "schema_version", "workflow_kind", "name", "workspace", "change_id",
        "directive_file", "context_files", "output_dir", "state_path",
        "intake_state_path", "run_dir", "roles",
    }
    _strict_keys(workflow, expected, "deliberation workflow")
    if workflow["schema_version"] != 1:
        raise DeliberationError("deliberation workflow schema_version must be 1")
    if workflow["workflow_kind"] != "architecture_deliberation":
        raise DeliberationError("workflow_kind must be architecture_deliberation")
    if not isinstance(workflow["name"], str) or not workflow["name"]:
        raise DeliberationError("workflow name must be non-empty")
    change_id = workflow["change_id"]
    if not isinstance(change_id, str) or not change_id or any(
        char not in "abcdefghijklmnopqrstuvwxyz0123456789._-" for char in change_id
    ):
        raise DeliberationError("change_id must use lowercase [a-z0-9._-]")

    workspace = (workflow_path.parent / workflow["workspace"]).resolve()
    if not workspace.is_dir():
        raise DeliberationError(f"workspace is missing: {workspace}")
    _relative(workspace, workflow_path)
    directive = _root_path(workspace, workflow["directive_file"], "directive_file")
    if not directive.is_file():
        raise DeliberationError(f"directive file is missing: {directive}")
    contexts = workflow["context_files"]
    if not isinstance(contexts, list) or any(not isinstance(item, str) for item in contexts):
        raise DeliberationError("context_files must be a list of root-relative paths")
    all_sources = [workflow["directive_file"], *contexts]
    if len(all_sources) != len(set(all_sources)):
        raise DeliberationError("directive_file and context_files must be unique")
    for relative in contexts:
        path = _root_path(workspace, relative, "context_file")
        if not path.is_file():
            raise DeliberationError(f"context file is missing: {relative}")

    roles = workflow["roles"]
    if not isinstance(roles, dict):
        raise DeliberationError("roles must be an object")
    _strict_keys(roles, set(STAGES), "roles")
    for role, role_value in roles.items():
        if not isinstance(role_value, dict) or set(role_value) != {"executors"}:
            raise DeliberationError(f"roles.{role} must contain only executors")
        executors = role_value["executors"]
        if not isinstance(executors, list) or not executors:
            raise DeliberationError(f"roles.{role}.executors must be non-empty")
        for index, executor in enumerate(executors):
            _validate_executor_config(executor, f"roles.{role}.executors[{index}]")

    output_dir = _root_path(workspace, workflow["output_dir"], "output_dir")
    state_path = _root_path(workspace, workflow["state_path"], "state_path")
    intake_state = _root_path(
        workspace, workflow["intake_state_path"], "intake_state_path"
    )
    run_dir = _root_path(workspace, workflow["run_dir"], "run_dir")
    if len({output_dir, state_path, intake_state, run_dir}) != 4:
        raise DeliberationError("output, state, intake-state, and run paths must differ")
    for config_path in (
        Path(STAGES[role][field])
        for role in STAGES
        for field in ("prompt", "schema")
    ):
        if not (workspace / config_path).is_file():
            raise DeliberationError(f"required deliberation resource is missing: {config_path}")
    return DeliberationRuntime(
        workflow_path=workflow_path,
        workflow=workflow,
        workspace=workspace,
        output_dir=output_dir,
        state_path=state_path,
        intake_state_path=intake_state,
        run_dir=run_dir,
        workflow_sha256=after,
    )


def _source_bindings(runtime: DeliberationRuntime) -> list[dict[str, str]]:
    result = []
    for relative in [
        runtime.workflow["directive_file"], *runtime.workflow["context_files"]
    ]:
        path = _root_path(runtime.workspace, relative, "source")
        result.append({"path": relative, "sha256": sha256_file(path)})
    return result


def initialize_deliberation(runtime: DeliberationRuntime) -> dict[str, Any]:
    if runtime.state_path.exists():
        return _load_runner_state(runtime)
    adopted_proposal = _adoptable_proposal(runtime)
    now = utc_now()
    state = {
        "schema_version": 1,
        "workflow_kind": "architecture_deliberation",
        "run_id": f"{runtime.workflow['name']}-{time.strftime('%Y%m%dT%H%M%S')}-{uuid.uuid4().hex[:8]}",
        "workflow_path": _relative(runtime.workspace, runtime.workflow_path),
        "workflow_sha256": runtime.workflow_sha256,
        "change_id": runtime.workflow["change_id"],
        "phase": "advocate_pending",
        "status": "running",
        "human_required": True,
        "implementation_authorized": False,
        "source_bindings": _source_bindings(runtime),
        "artifacts": {"advocate": adopted_proposal} if adopted_proposal else {},
        "attempt_counts": {role: 0 for role in STAGES},
        "attempts": [],
        "created_at": now,
        "updated_at": now,
        "last_error": None,
    }
    atomic_write_json(runtime.state_path, state)
    return state


def _verify_source_bindings(runtime: DeliberationRuntime, state: dict[str, Any]) -> None:
    if state.get("workflow_sha256") != runtime.workflow_sha256:
        raise DeliberationError("workflow bytes changed after deliberation initialized")
    if state.get("source_bindings") != _source_bindings(runtime):
        raise DeliberationError("directive or durable context changed after initialization")


def _canonical_path(runtime: DeliberationRuntime, role: str) -> Path:
    return runtime.output_dir / STAGES[role]["artifact"]


def _expected_context_bindings(runtime: DeliberationRuntime) -> dict[str, str]:
    return {entry["path"]: entry["sha256"] for entry in _source_bindings(runtime)}


def _require_context_bindings(runtime: DeliberationRuntime, artifact: dict[str, Any]) -> None:
    entries = artifact.get("context_files", [])
    paths = [entry.get("path") for entry in entries]
    if len(paths) != len(set(paths)):
        raise DeliberationError("artifact context_files contain duplicate paths")
    actual = {entry.get("path"): entry.get("sha256") for entry in entries}
    expected = _expected_context_bindings(runtime)
    if actual != expected:
        raise DeliberationError(
            "artifact must bind the exact verbatim directive and durable context: "
            f"expected={expected}, actual={actual}"
        )


def _runner_lock_path(runtime: DeliberationRuntime) -> Path:
    return runtime.state_path.with_suffix(runtime.state_path.suffix + ".lock")


def _adoptable_proposal(runtime: DeliberationRuntime) -> dict[str, str] | None:
    """Validate the sole canonical artifact a fresh runner may adopt."""
    canonical = _canonical_path(runtime, "advocate")
    downstream = [
        _canonical_path(runtime, role)
        for role in ("systems", "benchmark", "critique", "consensus")
    ]
    runner_lock = _runner_lock_path(runtime)
    if (
        runtime.intake_state_path.exists()
        or runner_lock.exists()
        or any(path.exists() for path in downstream)
    ):
        raise DeliberationError(
            "deliberation artifacts exist without runner state; refuse ambiguous adoption"
        )
    if not canonical.exists():
        return None
    if not canonical.is_file():
        raise DeliberationError("canonical advocate artifact is not a regular file")
    # Validate in place. Adoption binds these exact bytes and never rewrites
    # the manually authored proposal.
    try:
        _validate_stage_result(runtime, "advocate", canonical)
    except (IntakeError, OSError, ValueError, KeyError) as exc:
        raise DeliberationError(
            "deliberation artifacts exist without runner state; refuse adoption "
            f"of invalid canonical advocate artifact: {exc}"
        ) from exc
    return {
        "path": _relative(runtime.workspace, canonical),
        "sha256": sha256_file(canonical),
    }


def _synchronize_with_intake(
    runtime: DeliberationRuntime, state: dict[str, Any]
) -> dict[str, Any]:
    """Reconstruct runner progress from the authoritative intake state.

    This also closes the small crash window between an intake transition and a
    runner-state write: valid exact artifacts are adopted, never guessed.
    """
    if not runtime.intake_state_path.exists():
        if state["phase"] != "advocate_pending":
            raise DeliberationError("runner claims progress but intake state is missing")
        artifacts = state.get("artifacts", {})
        if artifacts:
            if set(artifacts) != {"advocate"}:
                raise DeliberationError(
                    "runner has unexpected artifacts before intake initialization"
                )
            entry = artifacts["advocate"]
            canonical = _canonical_path(runtime, "advocate")
            if (
                not isinstance(entry, dict)
                or set(entry) != {"path", "sha256"}
                or entry["path"] != _relative(runtime.workspace, canonical)
                or not canonical.is_file()
                or entry["sha256"] != sha256_file(canonical)
            ):
                raise DeliberationError(
                    "adopted canonical proposal is missing or its bytes changed"
                )
        return state
    try:
        intake = _load_verified_state(runtime.workspace, runtime.intake_state_path)
    except (IntakeError, OSError, ValueError, KeyError) as exc:
        raise DeliberationError(f"intake state is invalid: {exc}") from exc
    if intake["change_id"] != runtime.workflow["change_id"]:
        raise DeliberationError("intake change_id differs from workflow")

    role_entries: dict[str, dict[str, str]] = {}
    for key, entry in intake["artifacts"].items():
        path = _root_path(runtime.workspace, entry["path"], "intake artifact")
        expected_role: str | None = None
        if key == "architecture_change":
            expected_role = "advocate"
        elif key == "architecture_critique":
            expected_role = "critique"
        elif key == "architecture_consensus":
            expected_role = "consensus"
        elif key.startswith("architecture_interpretation:"):
            perspective = load_json(path).get("perspective")
            if perspective not in {"systems", "benchmark"}:
                raise DeliberationError(
                    f"unexpected interpretation perspective in intake: {perspective!r}"
                )
            expected_role = perspective
        elif key == "architecture_human_ratification":
            # A separate human may ratify after this runner pauses.  The runner
            # still never treats that as its own implementation authorization.
            continue
        if expected_role is None:
            raise DeliberationError(f"unexpected intake artifact: {key}")
        canonical = _canonical_path(runtime, expected_role)
        if path != canonical.resolve():
            raise DeliberationError(
                f"intake {key} is not at canonical deliberation path: {path}"
            )
        role_entries[expected_role] = {
            "path": entry["path"], "sha256": entry["sha256"]
        }

    count = len({role for role in role_entries if role in {"systems", "benchmark"}})
    if "advocate" not in role_entries:
        raise DeliberationError("intake lacks the architecture proposal")
    if intake["phase"] == "collecting_interpretations":
        phase = "interpretations_pending" if count < 2 else "critique_pending"
    elif intake["phase"] == "awaiting_consensus":
        if count < 2 or "critique" not in role_entries:
            raise DeliberationError("awaiting-consensus intake is structurally incomplete")
        phase = "consensus_pending"
    elif intake["phase"] in {"human_required", "human_approved"}:
        if "consensus" not in role_entries:
            raise DeliberationError("human-stage intake lacks consensus")
        phase = "human_required"
    else:
        raise DeliberationError(f"unsupported intake phase: {intake['phase']}")
    state["artifacts"] = role_entries
    state["phase"] = phase
    if phase == "human_required":
        state["status"] = "human_required"
    return state


def _load_runner_state(runtime: DeliberationRuntime) -> dict[str, Any]:
    try:
        state = load_json(runtime.state_path)
    except BaseException as exc:
        raise DeliberationError(f"cannot load runner state: {exc}") from exc
    required = {
        "schema_version", "workflow_kind", "run_id", "workflow_path",
        "workflow_sha256", "change_id", "phase", "status", "human_required",
        "implementation_authorized", "source_bindings", "artifacts",
        "attempt_counts", "attempts", "created_at", "updated_at", "last_error",
    }
    if not isinstance(state, dict) or set(state) != required:
        raise DeliberationError("runner state fields are malformed")
    if state["schema_version"] != 1 or state["workflow_kind"] != "architecture_deliberation":
        raise DeliberationError("runner state version/kind is invalid")
    if state["change_id"] != runtime.workflow["change_id"]:
        raise DeliberationError("runner state change_id differs from workflow")
    if state["workflow_path"] != _relative(runtime.workspace, runtime.workflow_path):
        raise DeliberationError("runner state workflow path differs")
    if state["human_required"] is not True or state["implementation_authorized"] is not False:
        raise DeliberationError("deliberation runner may never authorize implementation")
    if state["phase"] not in {*PHASE_TO_STAGE, "human_required"}:
        raise DeliberationError(f"invalid runner phase: {state['phase']!r}")
    if state["status"] not in {"running", "paused", "human_required"}:
        raise DeliberationError(f"invalid runner status: {state['status']!r}")
    _verify_source_bindings(runtime, state)
    before = (state["phase"], state["status"], dict(state["artifacts"]))
    state = _synchronize_with_intake(runtime, state)
    after = (state["phase"], state["status"], dict(state["artifacts"]))
    if before != after:
        _save_runner_state(runtime, state)
    return state


def _save_runner_state(runtime: DeliberationRuntime, state: dict[str, Any]) -> None:
    state["updated_at"] = utc_now()
    atomic_write_json(runtime.state_path, state)


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def _role_context_files(runtime: DeliberationRuntime, role: str) -> list[str]:
    source = [runtime.workflow["directive_file"], *runtime.workflow["context_files"]]
    if role == "advocate":
        return source
    change = _relative(runtime.workspace, _canonical_path(runtime, "advocate"))
    if role in {"systems", "benchmark"}:
        return [change, *source]
    interpretations = [
        _relative(runtime.workspace, _canonical_path(runtime, "systems")),
        _relative(runtime.workspace, _canonical_path(runtime, "benchmark")),
    ]
    if role == "critique":
        return [change, *interpretations, *source]
    critique = _relative(runtime.workspace, _canonical_path(runtime, "critique"))
    if role == "consensus":
        return [change, *interpretations, critique, *source]
    raise DeliberationError(f"unknown deliberation role: {role}")


def _stage_brief(runtime: DeliberationRuntime, role: str) -> str:
    bindings = _source_bindings(runtime)
    lines = [
        "# Bound stage brief",
        "",
        f"Expected change_id: `{runtime.workflow['change_id']}`.",
        "The artifact context_files must list exactly these durable sources",
        "(path and SHA-256; purpose text may be concise):",
    ]
    lines.extend(f"- `{item['path']}` `{item['sha256']}`" for item in bindings)
    if role in {"systems", "benchmark"}:
        lines.extend([
            "",
            f"Set interpretation_id to `{runtime.workflow['change_id']}.{role}`.",
            f"Set perspective to `{role}`.",
            "You have not received the other interpretation. Do not infer or imitate it.",
        ])
    if role == "critique":
        lines.extend([
            "",
            "Bind both supplied independent interpretations exactly; neither may be omitted.",
        ])
    if role == "consensus":
        change = load_json(_canonical_path(runtime, "advocate"))
        critique = load_json(_canonical_path(runtime, "critique"))
        interpretation_paths = [
            _canonical_path(runtime, "systems"),
            _canonical_path(runtime, "benchmark"),
        ]
        upstream = []
        for path in interpretation_paths:
            interpretation = load_json(path)
            upstream.extend(
                item["disagreement_id"]
                for item in interpretation["disagreements_with_proposal"]
            )
        lines.extend([
            "",
            "The terminal state is human_required even if your recommendation is proceed.",
            "You cannot create or imply human ratification.",
            "Registered acceptance-test IDs (disposition every and only these):",
            *[f"- `{item['test_id']}`" for item in change["acceptance_tests"]],
            "Critique concern IDs (disposition every and only these):",
            *[f"- `{item['concern_id']}`" for item in critique["concerns"]],
            "Upstream disagreement IDs (disposition every and only these):",
            *[f"- `{item}`" for item in upstream],
            "Every concern/upstream `resolution_id` must equal a disagreement_id",
            "that you define in your own top-level `disagreements` array; do not",
            "invent separate R_* identifiers.",
        ])
    lines.extend([
        "",
        "All supplied files are read-only. Output only the required JSON object.",
        "Do not edit files, launch jobs, or authorize implementation.",
    ])
    return "\n".join(lines) + "\n"


def _default_executor(
    role: str,
    node: dict[str, Any],
    workspace: Path,
    output_dir: Path,
    timeout_sec: int,
) -> tuple[int, dict[str, Any] | None]:
    del role
    return run_agent(node, workspace, output_dir, timeout_sec)


def _record_attempt(
    runtime: DeliberationRuntime,
    state: dict[str, Any],
    value: dict[str, Any],
) -> None:
    state["attempts"].append(value)
    _save_runner_state(runtime, state)


def _reserve_executor_ordinals(
    runtime: DeliberationRuntime,
    state: dict[str, Any],
    roles: list[str],
) -> dict[str, int]:
    """Reserve attempt-number ranges before starting any external process.

    A hard process crash can therefore leave gaps, but can never reuse a
    mailbox request ID or overwrite an earlier attempt directory on resume.
    """
    bases: dict[str, int] = {}
    for role in roles:
        bases[role] = state["attempt_counts"][role]
        state["attempt_counts"][role] += len(
            runtime.workflow["roles"][role]["executors"]
        )
    _save_runner_state(runtime, state)
    return bases


def _execute_role(
    runtime: DeliberationRuntime,
    state: dict[str, Any],
    role: str,
    executor: Executor,
    ordinal_base: int,
) -> tuple[dict[str, Any], list[dict[str, Any]], Path]:
    attempts: list[dict[str, Any]] = []
    candidates = runtime.workflow["roles"][role]["executors"]
    base_prompt = (runtime.workspace / STAGES[role]["prompt"]).read_text(encoding="utf-8")
    for candidate_index, candidate in enumerate(candidates):
        ordinal = ordinal_base + candidate_index + 1
        output_dir = runtime.run_dir / state["run_id"] / role / f"{ordinal:03d}_{candidate_index}"
        prompt_path = output_dir / "bound_prompt.md"
        _atomic_write_text(prompt_path, base_prompt + "\n\n" + _stage_brief(runtime, role))
        node = dict(candidate)
        timeout_sec = int(node.pop("timeout_sec", 3600))
        node.update({
            "prompt_file": _relative(runtime.workspace, prompt_path),
            "schema_file": STAGES[role]["schema"],
            "context_files": _role_context_files(runtime, role),
            "allow_write": False,
            "run_id": state["run_id"],
            "node_id": role,
            "request_id": f"{state['run_id']}-{role}-{ordinal}",
        })
        started = utc_now()
        try:
            code, value = executor(role, node, runtime.workspace, output_dir, timeout_sec)
            if code != 0 or not isinstance(value, dict):
                raise DeliberationError(
                    f"executor returned code={code}, object={isinstance(value, dict)}"
                )
            result_path = output_dir / "result.json"
            if result_path.exists():
                if load_json(result_path) != value:
                    raise DeliberationError("executor result file differs from returned value")
            else:
                atomic_write_json(result_path, value)
            _validate_stage_result(runtime, role, result_path)
        except BaseException as exc:
            attempts.append({
                "role": role,
                "ordinal": ordinal,
                "provider": candidate["provider"],
                "started_at": started,
                "finished_at": utc_now(),
                "status": "failed",
                "output_dir": _relative(runtime.workspace, output_dir),
                "error": f"{type(exc).__name__}: {exc}",
            })
            continue
        attempts.append({
            "role": role,
            "ordinal": ordinal,
            "provider": candidate["provider"],
            "started_at": started,
            "finished_at": utc_now(),
            "status": "validated",
            "output_dir": _relative(runtime.workspace, output_dir),
            "result_sha256": sha256_file(result_path),
            "fresh_context_mode": (
                {
                    "codex": "codex_exec_ephemeral",
                    "claude": "claude_one_shot",
                    "fable_mailbox": "fable_fresh_subagent_contract",
                }[candidate["provider"]]
                if executor is _default_executor
                else "injected_executor_contract"
            ),
        })
        return value, attempts, result_path
    raise RoleExecutionError(role, attempts)


def _validate_stage_result(
    runtime: DeliberationRuntime, role: str, result_path: Path
) -> dict[str, Any]:
    change_path = _canonical_path(runtime, "advocate")
    if role == "advocate":
        artifact = validate_change(runtime.workspace, result_path)
        if artifact["change_id"] != runtime.workflow["change_id"]:
            raise DeliberationError("advocate output change_id differs from workflow")
        _require_context_bindings(runtime, artifact)
        return artifact
    if not change_path.is_file():
        raise DeliberationError("proposal is missing before downstream deliberation")
    if role in {"systems", "benchmark"}:
        artifact = validate_interpretation(runtime.workspace, result_path, change_path)
        if artifact["interpretation_id"] != f"{runtime.workflow['change_id']}.{role}":
            raise DeliberationError(f"{role} interpretation_id is not canonical")
        if artifact["perspective"] != role:
            raise DeliberationError(f"{role} output has wrong perspective")
        _require_context_bindings(runtime, artifact)
        return artifact
    interpretation_paths = [
        _canonical_path(runtime, "benchmark"),
        _canonical_path(runtime, "systems"),
    ]
    # architecture_intake sorts interpretation artifact keys, so use the same
    # deterministic perspective order for exact hash bindings.
    if role == "critique":
        artifact = validate_critique(
            runtime.workspace, result_path, change_path, interpretation_paths
        )
        _require_context_bindings(runtime, artifact)
        return artifact
    if role == "consensus":
        critique_path = _canonical_path(runtime, "critique")
        return validate_consensus(
            runtime.workspace, result_path, change_path,
            interpretation_paths, critique_path,
        )
    raise DeliberationError(f"unknown role: {role}")


def _promote(runtime: DeliberationRuntime, role: str, value: dict[str, Any]) -> Path:
    destination = _canonical_path(runtime, role)
    if destination.exists():
        if load_json(destination) != value:
            raise DeliberationError(f"refuse to overwrite existing {role} artifact")
        return destination
    atomic_write_json(destination, value)
    _validate_stage_result(runtime, role, destination)
    return destination


def _advance_advocate(
    runtime: DeliberationRuntime, state: dict[str, Any], executor: Executor
) -> None:
    canonical = _canonical_path(runtime, "advocate")
    if canonical.exists() and not runtime.intake_state_path.exists():
        _validate_stage_result(runtime, "advocate", canonical)
    elif not canonical.exists():
        base = _reserve_executor_ordinals(runtime, state, ["advocate"])["advocate"]
        value, attempts, _ = _execute_role(
            runtime, state, "advocate", executor, base
        )
        for attempt in attempts:
            _record_attempt(runtime, state, attempt)
        canonical = _promote(runtime, "advocate", value)
    initialize_intake(runtime.workspace, canonical, runtime.intake_state_path)
    state = _synchronize_with_intake(runtime, state)
    state["last_error"] = None
    _save_runner_state(runtime, state)


def _advance_interpretations(
    runtime: DeliberationRuntime, state: dict[str, Any], executor: Executor
) -> None:
    intake = _load_verified_state(runtime.workspace, runtime.intake_state_path)
    recorded = {
        load_json(_root_path(runtime.workspace, entry["path"], "interpretation"))["perspective"]
        for key, entry in intake["artifacts"].items()
        if key.startswith("architecture_interpretation:")
    }
    missing = [role for role in ("systems", "benchmark") if role not in recorded]
    # Recover an exact validated artifact promoted immediately before a hard
    # crash, without asking a fresh model to regenerate different bytes over
    # the same canonical path.
    for role in list(missing):
        canonical = _canonical_path(runtime, role)
        if not canonical.exists():
            continue
        _validate_stage_result(runtime, role, canonical)
        record_interpretation(runtime.workspace, runtime.intake_state_path, canonical)
        missing.remove(role)
    produced: dict[str, tuple[dict[str, Any], list[dict[str, Any]]]] = {}
    if missing:
        bases = _reserve_executor_ordinals(runtime, state, missing)
        # The independent interpretations run concurrently and receive the
        # same proposal/source bytes, never each other's result.
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(missing)) as pool:
            futures = {
                pool.submit(
                    _execute_role, runtime, state, role, executor, bases[role]
                ): role
                for role in missing
            }
            failures: list[str] = []
            for future, role in [(future, role) for future, role in futures.items()]:
                try:
                    value, attempts, _ = future.result()
                    produced[role] = (value, attempts)
                except BaseException as exc:
                    if isinstance(exc, RoleExecutionError):
                        for attempt in exc.attempts:
                            _record_attempt(runtime, state, attempt)
                    failures.append(f"{role}: {type(exc).__name__}: {exc}")
            for role in missing:
                if role in produced:
                    for attempt in produced[role][1]:
                        _record_attempt(runtime, state, attempt)
            if failures:
                raise DeliberationError("independent interpretation failure: " + "; ".join(failures))
        ids = [value[0]["interpretation_id"] for value in produced.values()]
        perspectives = [value[0]["perspective"] for value in produced.values()]
        if len(ids) != len(set(ids)) or len(perspectives) != len(set(perspectives)):
            raise DeliberationError("independent interpretations are not identifier-distinct")
        for role in missing:
            value = produced[role][0]
            canonical = _promote(runtime, role, value)
            record_interpretation(runtime.workspace, runtime.intake_state_path, canonical)
    state = _synchronize_with_intake(runtime, state)
    state["last_error"] = None
    _save_runner_state(runtime, state)


def _advance_single(
    runtime: DeliberationRuntime,
    state: dict[str, Any],
    role: str,
    executor: Executor,
) -> None:
    canonical = _canonical_path(runtime, role)
    if not canonical.exists():
        base = _reserve_executor_ordinals(runtime, state, [role])[role]
        value, attempts, _ = _execute_role(
            runtime, state, role, executor, base
        )
        for attempt in attempts:
            _record_attempt(runtime, state, attempt)
        canonical = _promote(runtime, role, value)
    else:
        _validate_stage_result(runtime, role, canonical)
    if role == "critique":
        record_critique(runtime.workspace, runtime.intake_state_path, canonical)
    elif role == "consensus":
        record_consensus(runtime.workspace, runtime.intake_state_path, canonical)
    else:
        raise DeliberationError(f"invalid single stage: {role}")
    state = _synchronize_with_intake(runtime, state)
    state["last_error"] = None
    _save_runner_state(runtime, state)


def run_to_human_required(
    runtime: DeliberationRuntime,
    *,
    executor: Executor | None = None,
    once: bool = False,
) -> dict[str, Any]:
    executor = executor or _default_executor
    state = initialize_deliberation(runtime)
    lock_path = _runner_lock_path(runtime)
    with Lock(lock_path):
        state = _load_runner_state(runtime)
        if state["phase"] == "human_required":
            state["status"] = "human_required"
            _save_runner_state(runtime, state)
            return state
        state["status"] = "running"
        state["last_error"] = None
        _save_runner_state(runtime, state)
        while state["phase"] != "human_required":
            phase = state["phase"]
            try:
                if phase == "advocate_pending":
                    _advance_advocate(runtime, state, executor)
                elif phase == "interpretations_pending":
                    _advance_interpretations(runtime, state, executor)
                elif phase == "critique_pending":
                    _advance_single(runtime, state, "critique", executor)
                elif phase == "consensus_pending":
                    _advance_single(runtime, state, "consensus", executor)
                else:
                    raise DeliberationError(f"unknown phase: {phase}")
                state = _load_runner_state(runtime)
            except BaseException as exc:
                if isinstance(exc, RoleExecutionError):
                    for attempt in exc.attempts:
                        _record_attempt(runtime, state, attempt)
                state["status"] = "paused"
                state["last_error"] = f"{type(exc).__name__}: {exc}"
                _save_runner_state(runtime, state)
                return state
            if once:
                break
        if state["phase"] == "human_required":
            state["status"] = "human_required"
            state["human_required"] = True
            state["implementation_authorized"] = False
            _save_runner_state(runtime, state)
    return state


def status(runtime: DeliberationRuntime) -> dict[str, Any]:
    if runtime.state_path.exists():
        return _load_runner_state(runtime)

    # Keep a clean status probe observational.  The same preflight is still
    # applied so malformed, stale, or conflicting artifacts fail closed, but
    # no runner/intake state is written here.
    adopted_proposal = _adoptable_proposal(runtime)
    return {
        "workflow_kind": "architecture_deliberation",
        "change_id": runtime.workflow["change_id"],
        "phase": "advocate_pending",
        "status": "uninitialized",
        "human_required": True,
        "implementation_authorized": False,
        "adoptable_proposal_sha256": (
            adopted_proposal["sha256"] if adopted_proposal else None
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workflow", type=Path)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init")
    run_parser = sub.add_parser("run")
    run_parser.add_argument("--once", action="store_true")
    sub.add_parser("status")
    args = parser.parse_args(argv)
    try:
        runtime = load_deliberation_runtime(args.workflow)
        if args.command == "init":
            result = initialize_deliberation(runtime)
        elif args.command == "run":
            result = run_to_human_required(runtime, once=args.once)
        else:
            result = status(runtime)
    except (DeliberationError, WorkflowError, IntakeError, OSError, ValueError, KeyError) as exc:
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}))
        return 1
    print(json.dumps({"ok": True, "state": result}, indent=2, sort_keys=True))
    return 0 if result["status"] != "paused" else 1


if __name__ == "__main__":
    sys.exit(main())
