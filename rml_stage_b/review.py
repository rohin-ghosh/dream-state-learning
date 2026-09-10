"""Two-phase exact-byte review and mechanical G1 claim firewall."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .contract import validate_claim


class ReviewContractError(ValueError):
    pass


ROLES = frozenset({"INDEPENDENT_REVIEWER", "AUTHOR_SIDE_ADVOCATE"})
PHASES = frozenset({"PRE_GPU", "POST_RUN"})


@dataclass(frozen=True)
class ReviewApproval:
    phase: str
    role: str
    actor_id: str
    bound_sha256: str
    verdict: str
    actor_overlap_disclosed: bool

    def validate(self) -> None:
        if self.phase not in PHASES or self.role not in ROLES:
            raise ReviewContractError("review phase/role is not registered")
        if self.verdict != "APPROVE_EXACT_BYTES":
            raise ReviewContractError("review did not approve exact bytes")
        if not self.actor_id or len(self.actor_id) > 128:
            raise ReviewContractError("review actor id is malformed")


def validate_two_phase_reviews(
    approvals: Iterable[ReviewApproval],
    *,
    implementation_packet_sha256: str,
    immutable_output_sha256: str | None = None,
) -> dict[str, bool]:
    approvals = tuple(approvals)
    for approval in approvals:
        approval.validate()
    pre = [row for row in approvals if row.phase == "PRE_GPU"]
    if {row.role for row in pre} != ROLES or len(pre) != 2:
        raise ReviewContractError("pre-GPU requires exactly both review roles")
    if len({row.actor_id for row in pre}) != 2:
        raise ReviewContractError("independent reviewer and advocate must be distinct actors")
    if any(row.bound_sha256 != implementation_packet_sha256 for row in pre):
        raise ReviewContractError("pre-GPU review is not bound to the implementation packet")
    if any(row.actor_overlap_disclosed for row in pre):
        raise ReviewContractError("pre-GPU roles disclose actor overlap")
    post_complete = False
    post = [row for row in approvals if row.phase == "POST_RUN"]
    if immutable_output_sha256 is not None:
        if {row.role for row in post} != ROLES or len(post) != 2:
            raise ReviewContractError("post-run requires exactly both review roles")
        if len({row.actor_id for row in post}) != 2:
            raise ReviewContractError("post-run reviewer and advocate must be distinct")
        if any(row.bound_sha256 != immutable_output_sha256 for row in post):
            raise ReviewContractError("post-run review is not bound to immutable outputs")
        post_complete = True
    elif post:
        raise ReviewContractError("post-run reviews supplied without immutable output hash")
    return {"pre_gpu_complete": True, "post_run_complete": post_complete}


def validate_result_language(text: str, *, passed: bool) -> None:
    validate_claim(text, passed=passed)
