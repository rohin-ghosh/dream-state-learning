"""Inactive, provider-free primitives for durable preflight fanout.

This module deliberately does not know how to contact a reviewer, test runner, or
remote machine.  Callers inject those operations into ``supervisor_fanout``.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Mapping


class RetryClass(str, Enum):
    """A result classification with an intentionally narrow retry policy."""

    TRANSIENT = "transient"
    UNAVAILABLE = "unavailable"
    PERMANENT_FAILURE = "permanent_failure"
    SCIENTIFIC_REJECTION = "scientific_rejection"

    @property
    def retryable(self) -> bool:
        # A rejection is scientific evidence, not an infrastructure incident.
        return self is RetryClass.TRANSIENT


@dataclass(frozen=True)
class BranchResult:
    """The serializable terminal value returned by one isolated branch."""

    status: str
    retry_class: RetryClass | None = None
    evidence: Mapping[str, Any] = field(default_factory=dict)
    detail: str | None = None

    @property
    def accepted(self) -> bool:
        return self.status in {"approved", "passed"}

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "retry_class": self.retry_class.value if self.retry_class else None,
            "evidence": dict(self.evidence),
            "detail": self.detail,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "BranchResult":
        retry = value.get("retry_class")
        return cls(
            status=str(value["status"]),
            retry_class=RetryClass(retry) if retry is not None else None,
            evidence=dict(value.get("evidence", {})),
            detail=value.get("detail"),
        )


@dataclass(frozen=True)
class BranchContext:
    """Inputs visible to a branch.  The branch gets no coordinator state handle."""

    branch: str
    attempt_id: str
    attempt_dir: Path
    frozen_manifest: Mapping[str, Any]


class ReceiptError(RuntimeError):
    pass


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode(
        "utf-8"
    )


def digest_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()

