from __future__ import annotations

import json
import os
import signal
import subprocess
import time
import uuid
from pathlib import Path
from typing import Any

from .io import atomic_write_json, load_json, sha256_file


COMMON_BOUNDARY = """
AUTONOMY BOUNDARY
- Work only inside the supplied repository and task.
- Do not contact people, acquire resources, change leases, publish, push, or
  alter evaluation labels.
- Do not weaken a falsifier or silently change a scientific goalpost.
- Treat offline truth as reporting-only unless the frozen protocol explicitly
  says otherwise.
- Return the requested structured decision. Escalate material scientific
  choices instead of guessing what Rohin would prefer.
""".strip()


def build_prompt(node: dict[str, Any], workspace: Path) -> str:
    prompt_path = workspace / node["prompt_file"]
    parts = [prompt_path.read_text(encoding="utf-8"), COMMON_BOUNDARY]
    for relative in node.get("context_files", []):
        path = workspace / relative
        text = path.read_text(encoding="utf-8")
        max_chars = int(node.get("max_context_chars_per_file", 200_000))
        if len(text) > max_chars:
            text = text[-max_chars:]
            prefix = f"[truncated to final {max_chars} characters]\n"
        else:
            prefix = ""
        parts.append(
            f"\n--- FILE: {relative} | SHA-256: {sha256_file(path)} ---\n"
            f"{prefix}{text}"
        )
    return "\n\n".join(parts)


def _normalize_claude(value: Any) -> dict[str, Any]:
    if isinstance(value, dict) and isinstance(value.get("structured_output"), dict):
        return value["structured_output"]
    if isinstance(value, dict) and isinstance(value.get("result"), str):
        try:
            parsed = json.loads(value["result"])
        except json.JSONDecodeError:
            pass
        else:
            if isinstance(parsed, dict):
                return parsed
    if isinstance(value, dict):
        return value
    raise ValueError("agent output was not a JSON object")


def _codex_response_schema(value: Any) -> Any:
    """Return the strict-schema subset accepted by Codex structured output.

    The repository's full Draft-2020 schemas remain authoritative and are
    validated locally after generation.  Codex's response-format endpoint
    rejects some otherwise-valid assertion keywords (currently
    ``uniqueItems``), so the generation hint must omit those keywords rather
    than weakening the local acceptance gate.
    """
    if isinstance(value, dict):
        normalized = {
            key: _codex_response_schema(child)
            for key, child in value.items()
            if key not in {"$schema", "uniqueItems"}
        }
        if "type" not in normalized:
            candidates = None
            if "const" in normalized:
                candidates = [normalized["const"]]
            elif isinstance(normalized.get("enum"), list) and normalized["enum"]:
                candidates = normalized["enum"]
            if candidates is not None:
                inferred = {_typename_for_schema(item) for item in candidates}
                if len(inferred) == 1:
                    normalized["type"] = inferred.pop()
        return normalized
    if isinstance(value, list):
        return [_codex_response_schema(child) for child in value]
    return value


def _typename_for_schema(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, dict):
        return "object"
    if isinstance(value, list):
        return "array"
    if isinstance(value, str):
        return "string"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    raise TypeError(f"unsupported JSON schema literal: {type(value).__name__}")


def run_agent(
    node: dict[str, Any],
    workspace: Path,
    output_dir: Path,
    timeout_sec: int,
) -> tuple[int, dict[str, Any] | None]:
    provider = node["provider"]
    schema_path = (workspace / node["schema_file"]).resolve()
    schema = load_json(schema_path)
    prompt = build_prompt(node, workspace)
    output_dir.mkdir(parents=True, exist_ok=True)
    stdout_path = output_dir / "stdout.log"
    stderr_path = output_dir / "stderr.log"
    result_path = output_dir / "result.json"
    raw_result_path = output_dir / "raw_result.txt"
    allow_write = bool(node.get("allow_write", False))

    if provider == "fable_mailbox":
        from .fable_transport import validate_against_schema

        request_id = node.get("request_id") or (
            f"{output_dir.parent.name}-{output_dir.name}-{uuid.uuid4().hex[:8]}"
        )
        inbox = workspace / ".research_loop" / "handoffs" / "inbox"
        outbox = workspace / ".research_loop" / "handoffs" / "outbox"
        request_path = inbox / f"{request_id}.request.json"
        response_path = outbox / f"{request_id}.response.json"
        if request_path.exists() or response_path.exists():
            raise FileExistsError(f"mailbox request id already exists: {request_id}")
        context_paths = [
            node["prompt_file"], node["schema_file"],
            *node.get("context_files", []),
        ]
        request = {
            "request_id": request_id,
            "run_id": node.get("run_id", request_id),
            "node_id": node.get("node_id", "fresh_review"),
            "prompt_path": node["prompt_file"],
            "response_schema_path": node["schema_file"],
            "context_files": [
                {"path": relative,
                 "sha256": sha256_file(workspace / relative)}
                for relative in context_paths
            ],
            "autonomy_boundary": COMMON_BOUNDARY,
        }
        atomic_write_json(request_path, request)
        deadline = time.monotonic() + timeout_sec
        while time.monotonic() < deadline and not response_path.is_file():
            time.sleep(min(float(node.get("mailbox_poll_sec", 5)), 30.0))
        if not response_path.is_file():
            return 75, None
        value = load_json(response_path)
        schema_errors = validate_against_schema(value, schema)
        if schema_errors:
            raise ValueError(f"Fable mailbox schema errors: {schema_errors}")
        raw_result_path.write_text(
            json.dumps(value, indent=2) + "\n", encoding="utf-8"
        )
        atomic_write_json(result_path, value)
        return 0, value

    if provider == "codex":
        sandbox = "workspace-write" if allow_write else "read-only"
        codex_schema_path = output_dir / "codex-response-schema.json"
        atomic_write_json(codex_schema_path, _codex_response_schema(schema))
        command = [
            "codex",
            "exec",
            "--ephemeral",
            "-C",
            str(workspace),
            "-s",
            sandbox,
            "--output-schema",
            str(codex_schema_path),
            "--output-last-message",
            str(raw_result_path),
            "-",
        ]
        if node.get("model"):
            command[2:2] = ["--model", node["model"]]
        if node.get("reasoning_effort"):
            command[2:2] = [
                "--config",
                f'model_reasoning_effort="{node["reasoning_effort"]}"',
            ]
    elif provider == "claude":
        claude_schema = dict(schema)
        # Claude CLI validates a supported schema subset and rejects the
        # otherwise-standard draft declaration URI.
        claude_schema.pop("$schema", None)
        tools = "Read,Edit,Write,Glob,Grep,Bash" if allow_write else "Read,Glob,Grep"
        permission = "acceptEdits" if allow_write else "dontAsk"
        command = [
            "claude",
            "-p",
            "--output-format",
            "json",
            "--json-schema",
            json.dumps(claude_schema, separators=(",", ":")),
            "--permission-mode",
            permission,
            "--tools",
            tools,
        ]
    else:
        raise ValueError(f"unsupported agent provider: {provider}")

    attempts = int(node.get("provider_attempts", 1))
    attempt_timeout = min(
        timeout_sec, int(node.get("provider_attempt_timeout_sec", timeout_sec))
    )
    proc = None
    for attempt in range(1, attempts + 1):
        with stdout_path.open("a", encoding="utf-8") as stdout, stderr_path.open(
            "a", encoding="utf-8"
        ) as stderr:
            stdout.write(f"\n[provider attempt {attempt}/{attempts}]\n")
            stderr.write(f"\n[provider attempt {attempt}/{attempts}]\n")
            stdout.flush()
            stderr.flush()
            child = None
            try:
                child = subprocess.Popen(
                    command,
                    cwd=workspace,
                    stdin=subprocess.PIPE,
                    stdout=stdout,
                    stderr=stderr,
                    text=True,
                    start_new_session=True,
                )
                child.communicate(input=prompt, timeout=attempt_timeout)
                proc = subprocess.CompletedProcess(command, child.returncode)
            except subprocess.TimeoutExpired:
                if child is not None:
                    try:
                        os.killpg(child.pid, signal.SIGTERM)
                        child.wait(timeout=10)
                    except (ProcessLookupError, subprocess.TimeoutExpired):
                        try:
                            os.killpg(child.pid, signal.SIGKILL)
                        except ProcessLookupError:
                            pass
                stderr.write(f"provider attempt timed out after {attempt_timeout}s\n")
                if attempt == attempts:
                    return 124, None
                time.sleep(min(5 * attempt, 30))
                continue
        if proc.returncode == 0:
            break
        error_text = stderr_path.read_text(encoding="utf-8").lower()
        retryable = any(term in error_text for term in (
            "capacity", "rate limit", "temporarily unavailable",
            "overloaded", "service unavailable",
        ))
        if not retryable or attempt == attempts:
            break
        time.sleep(min(5 * attempt, 30))
    assert proc is not None
    if proc.returncode != 0:
        return proc.returncode, None

    if provider == "codex":
        value = json.loads(raw_result_path.read_text(encoding="utf-8"))
    else:
        value = _normalize_claude(json.loads(stdout_path.read_text(encoding="utf-8")))
        raw_result_path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    if not isinstance(value, dict):
        raise ValueError("structured agent response must be a JSON object")
    atomic_write_json(result_path, value)
    return 0, value
