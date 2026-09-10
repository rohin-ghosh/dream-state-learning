"""A durable, inactive preflight fanout and join coordinator.

The coordinator is the sole writer of its state file and event log.  Branches
receive only a private attempt directory and write a terminal marker there.
This allows a restarted coordinator to consume a completed marker without
repeating an already-finished review or test.
"""

from __future__ import annotations

import json
import os
import tempfile
import threading
import traceback
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping

from .preflight import (
    BranchContext,
    BranchResult,
    ReceiptError,
    RetryClass,
    canonical_json,
    digest_json,
    sha256_path,
)


BRANCHES = ("fable", "sol", "test")


class PreflightError(RuntimeError):
    pass


@dataclass(frozen=True)
class QuorumPolicy:
    """The project's explicit independent-review quorum.

    Sol approval and deterministic tests are mandatory. Fable is accepted when
    it approves, but a missing Fable reviewer falls back to Sol. A Fable
    scientific rejection always blocks.
    """

    accept_fable_unavailable: bool = True
    fable_transient_exhaustion: str = "unavailable"

    def __post_init__(self) -> None:
        if self.fable_transient_exhaustion not in {"unavailable", "blocking"}:
            raise ValueError("fable_transient_exhaustion must be unavailable or blocking")

    def as_dict(self) -> dict[str, Any]:
        return {
            "accept_fable_unavailable": self.accept_fable_unavailable,
            "fable_transient_exhaustion": self.fable_transient_exhaustion,
        }

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any] | None) -> "QuorumPolicy":
        if value is None:
            return cls()
        return cls(
            accept_fable_unavailable=bool(value.get("accept_fable_unavailable", True)),
            fable_transient_exhaustion=str(value.get("fable_transient_exhaustion", "unavailable")),
        )


def _atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    """Atomically replace a JSON file and fsync both data and its directory."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, sort_keys=True, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def _load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


class PreflightCoordinator:
    """Coordinates Fable, Sol, and deterministic-test preflight branches.

    This is intentionally not wired into an active workflow. ``operations``
    are injected callables, making the mechanism testable with no providers.
    """

    def __init__(
        self,
        state_dir: Path,
        workflow_path: Path,
        lock_path: Path,
        spec: Mapping[str, Any],
        *,
        max_attempts: int = 2,
        quorum_policy: QuorumPolicy | None = None,
    ) -> None:
        if max_attempts < 1:
            raise ValueError("max_attempts must be at least one")
        self.state_dir = state_dir.resolve()
        self.workflow_path = workflow_path.resolve()
        self.lock_path = lock_path.resolve()
        self.spec = dict(spec)
        self.max_attempts = max_attempts
        self.quorum_policy = quorum_policy or QuorumPolicy()
        self.manifest_path = self.state_dir / "preflight-freeze.json"
        self.state_path = self.state_dir / "preflight.state.json"
        self.events_path = self.state_dir / "preflight.events.jsonl"
        self.receipt_path = self.state_dir / "preflight.receipt.json"
        self._state_lock = threading.Lock()

    def freeze_once(self) -> dict[str, Any]:
        """Capture hashes exactly once; later calls use the existing manifest."""
        self.state_dir.mkdir(parents=True, exist_ok=True)
        requested = {
            "workflow_path": str(self.workflow_path),
            "lock_path": str(self.lock_path),
            "spec_sha256": digest_json(self.spec),
        }
        if self.manifest_path.exists():
            frozen = _load_json(self.manifest_path)
            if {key: frozen.get(key) for key in requested} != requested:
                raise PreflightError("preflight already frozen for different inputs")
            return frozen
        if not self.workflow_path.is_file() or not self.lock_path.is_file():
            raise PreflightError("workflow and lock must exist before freezing")
        frozen = {
            "schema_version": 1,
            **requested,
            "workflow_sha256": sha256_path(self.workflow_path),
            "lock_sha256": sha256_path(self.lock_path),
        }
        # Exclusive creation is important: a competing coordinator must consume
        # the winner's capture rather than silently make another freeze.
        try:
            fd = os.open(self.manifest_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            return self.freeze_once()
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(frozen, handle, sort_keys=True, indent=2)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            directory_fd = os.open(self.state_dir, os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        except BaseException:
            # Creation failed before a durable complete manifest; it is safe to
            # remove only this exact new file.
            try:
                self.manifest_path.unlink()
            except FileNotFoundError:
                pass
            raise
        return frozen

    def _state(self) -> dict[str, Any]:
        if self.state_path.exists():
            return _load_json(self.state_path)
        return {"schema_version": 1, "branches": {}, "joined": False}

    def _save_state(self, state: Mapping[str, Any]) -> None:
        _atomic_json(self.state_path, state)

    def _event(self, event: str, **data: Any) -> None:
        # This is called only by coordinator methods, never branch callables.
        self.events_path.parent.mkdir(parents=True, exist_ok=True)
        record = {"event": event, **data}
        with self.events_path.open("a", encoding="utf-8") as handle:
            handle.write(canonical_json(record).decode("utf-8") + "\n")
            handle.flush()
            os.fsync(handle.fileno())

    def _attempt_root(self, branch: str) -> Path:
        return self.state_dir / "branches" / branch / "attempts"

    def _terminal_markers(self, branch: str) -> list[Path]:
        return sorted(self._attempt_root(branch).glob("*/terminal.json"))

    def _consume_terminal(self, branch: str) -> tuple[str, BranchResult, Path] | None:
        markers = self._terminal_markers(branch)
        if not markers:
            return None
        marker = markers[-1]
        payload = _load_json(marker)
        return str(payload["attempt_id"]), BranchResult.from_dict(payload["result"]), marker

    def _record_terminal(self, branch: str, attempt_id: str, result: BranchResult) -> Path:
        marker = self._attempt_root(branch) / attempt_id / "terminal.json"
        _atomic_json(marker, {"attempt_id": attempt_id, "branch": branch, "result": result.as_dict()})
        return marker

    def _next_attempt(self, branch: str) -> tuple[str, Path]:
        root = self._attempt_root(branch)
        root.mkdir(parents=True, exist_ok=True)
        number = len(list(root.glob("*"))) + 1
        attempt_id = f"{branch}-{number:04d}-{uuid.uuid4().hex[:10]}"
        directory = root / attempt_id
        staging = root / f".{attempt_id}.staging"
        staging.mkdir()
        # Publish the initialized attempt directory with a single rename.  A
        # coordinator can therefore only discover a complete ``started.json``.
        _atomic_json(staging / "started.json", {"attempt_id": attempt_id, "branch": branch})
        os.replace(staging, directory)
        directory_fd = os.open(root, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
        return attempt_id, directory

    def _accept(self, branch: str, result: BranchResult) -> bool:
        return result.status == ("passed" if branch == "test" else "approved")

    def execute_branch(self, branch: str, operation: Callable[[BranchContext], BranchResult]) -> BranchResult:
        """Run or recover one branch.  Retry only explicit transient failures."""
        if branch not in BRANCHES:
            raise ValueError(f"unsupported preflight branch: {branch}")
        frozen = self.freeze_once()
        with self._state_lock:
            recovered = self._consume_terminal(branch)
            if recovered is not None:
                attempt_id, result, marker = recovered
                state = self._state()
                state["branches"][branch] = {
                    "attempt_id": attempt_id,
                    "terminal": str(marker),
                    "result": result.as_dict(),
                    "recovered": True,
                }
                self._save_state(state)
                self._event("branch_recovered", branch=branch, attempt_id=attempt_id)
                return result
        for _ in range(self.max_attempts):
            attempt_id, attempt_dir = self._next_attempt(branch)
            self._event("branch_started", branch=branch, attempt_id=attempt_id)
            try:
                result = operation(BranchContext(branch, attempt_id, attempt_dir, frozen))
                if not isinstance(result, BranchResult):
                    raise TypeError("branch operation must return BranchResult")
            except BaseException as exc:
                result = BranchResult(
                    status="failed",
                    retry_class=RetryClass.TRANSIENT,
                    detail=f"{type(exc).__name__}: {exc}",
                    evidence={"exception": traceback.format_exc(limit=1)},
                )
            marker = self._record_terminal(branch, attempt_id, result)
            with self._state_lock:
                state = self._state()
                state["branches"][branch] = {
                    "attempt_id": attempt_id,
                    "terminal": str(marker),
                    "result": result.as_dict(),
                    "recovered": False,
                }
                self._save_state(state)
                self._event("branch_terminal", branch=branch, attempt_id=attempt_id, status=result.status)
            if self._accept(branch, result) or not (result.retry_class and result.retry_class.retryable):
                return result
        return result

    def _evaluate_quorum(self, results: Mapping[str, BranchResult]) -> dict[str, Any]:
        """Make the fallback decision explicit and serializable."""
        sol_ok = results["sol"].status == "approved"
        test_ok = results["test"].status == "passed"
        fable = results["fable"]
        fable_ok = False
        reason = "blocking_failure"
        effective_retry = fable.retry_class.value if fable.retry_class else None
        if fable.status == "approved":
            fable_ok, reason = True, "approved"
        elif fable.retry_class is RetryClass.SCIENTIFIC_REJECTION or fable.status == "rejected":
            reason = "scientific_rejection_blocking"
        elif fable.retry_class is RetryClass.UNAVAILABLE:
            fable_ok = self.quorum_policy.accept_fable_unavailable
            reason = "unavailable_accepted" if fable_ok else "unavailable_blocking"
        elif fable.retry_class is RetryClass.TRANSIENT:
            # The branch only reaches join after all allowed retries.  Map that
            # terminal condition visibly; it is never an implicit approval.
            if self.quorum_policy.fable_transient_exhaustion == "unavailable":
                effective_retry = RetryClass.UNAVAILABLE.value
                fable_ok = self.quorum_policy.accept_fable_unavailable
                reason = "transient_exhausted_as_unavailable" if fable_ok else "unavailable_blocking"
            else:
                reason = "transient_exhausted_blocking"
        return {
            "accepted": sol_ok and test_ok and fable_ok,
            "policy": self.quorum_policy.as_dict(),
            "branches": {
                "sol": {"required": True, "accepted": sol_ok, "status": results["sol"].status},
                "test": {"required": True, "accepted": test_ok, "status": results["test"].status},
                "fable": {
                    "required": False,
                    "accepted": fable_ok,
                    "status": fable.status,
                    "retry_class": fable.retry_class.value if fable.retry_class else None,
                    "effective_retry_class": effective_retry,
                    "reason": reason,
                },
            },
        }

    def _make_receipt(self, frozen: Mapping[str, Any], results: Mapping[str, BranchResult]) -> dict[str, Any]:
        terminals = {
            branch: self._consume_terminal(branch)
            for branch in BRANCHES
        }
        assert all(terminals.values())
        payload = {
            "schema_version": 1,
            "frozen_manifest_sha256": digest_json(frozen),
            "workflow_sha256": frozen["workflow_sha256"],
            "lock_sha256": frozen["lock_sha256"],
            "spec_sha256": frozen["spec_sha256"],
            "quorum_policy": self.quorum_policy.as_dict(),
            "quorum": self._evaluate_quorum(results),
            "fable_approval": results["fable"].as_dict(),
            "sol_approval": results["sol"].as_dict(),
            "deterministic_test_evidence": results["test"].evidence,
            "terminal_sha256": {
                branch: sha256_path(terminals[branch][2]) for branch in BRANCHES  # type: ignore[index]
            },
        }
        return {**payload, "receipt_sha256": digest_json(payload)}

    def run_preflight(self, operations: Mapping[str, Callable[[BranchContext], BranchResult]]) -> dict[str, Any]:
        if set(operations) != set(BRANCHES):
            raise PreflightError("operations must provide exactly fable, sol, and test")
        frozen = self.freeze_once()
        # All three independent operations are submitted before the join examines
        # results.  The context manager waits for each branch to reach terminal.
        with ThreadPoolExecutor(max_workers=3, thread_name_prefix="preflight") as pool:
            futures = {branch: pool.submit(self.execute_branch, branch, operations[branch]) for branch in BRANCHES}
            results = {branch: future.result() for branch, future in futures.items()}
        quorum = self._evaluate_quorum(results)
        accepted = bool(quorum["accepted"])
        with self._state_lock:
            state = self._state()
            state["joined"] = accepted
            state["quorum"] = quorum
            if accepted:
                receipt = self._make_receipt(frozen, results)
                _atomic_json(self.receipt_path, receipt)
                state["receipt"] = str(self.receipt_path)
                self._event("join_approved", receipt_sha256=receipt["receipt_sha256"])
            else:
                state["receipt"] = None
                self._event("join_blocked", branches={key: value.status for key, value in results.items()}, quorum=quorum)
            self._save_state(state)
        return {"joined": accepted, "results": results, "receipt": self.receipt_path if accepted else None}

    def verify_receipt(self) -> dict[str, Any]:
        if not self.receipt_path.is_file():
            raise ReceiptError("preflight receipt is missing")
        receipt = _load_json(self.receipt_path)
        claimed = receipt.pop("receipt_sha256", None)
        if not isinstance(claimed, str) or claimed != digest_json(receipt):
            raise ReceiptError("preflight receipt content hash is invalid")
        frozen = self.freeze_once()
        for key in ("workflow_sha256", "lock_sha256", "spec_sha256"):
            if receipt.get(key) != frozen.get(key):
                raise ReceiptError(f"preflight receipt does not bind frozen {key}")
        if receipt.get("frozen_manifest_sha256") != digest_json(frozen):
            raise ReceiptError("preflight receipt does not bind the frozen manifest")
        if receipt.get("quorum_policy") != self.quorum_policy.as_dict():
            raise ReceiptError("preflight receipt quorum policy differs from this coordinator")
        results: dict[str, BranchResult] = {}
        for branch in BRANCHES:
            terminal = self._consume_terminal(branch)
            if terminal is None:
                raise ReceiptError(f"preflight terminal evidence is missing for {branch}")
            results[branch] = terminal[1]
        expected_quorum = self._evaluate_quorum(results)
        if not expected_quorum["accepted"] or receipt.get("quorum") != expected_quorum:
            raise ReceiptError("preflight receipt quorum evidence is invalid")
        terminal_hashes = receipt.get("terminal_sha256")
        if not isinstance(terminal_hashes, dict):
            raise ReceiptError("preflight receipt lacks terminal evidence hashes")
        for branch in BRANCHES:
            terminal = self._consume_terminal(branch)
            if terminal is None or terminal_hashes.get(branch) != sha256_path(terminal[2]):
                raise ReceiptError(f"preflight terminal evidence changed for {branch}")
        return receipt
