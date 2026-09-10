"""Frozen roster, outcome taxonomy, grammar, and resource envelope for G1."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Mapping


CHANGE_ID = "chg_20260903_rml_g1_gold_action_fast_v1"
PROTOCOL = "RML-STAGE-B-GOLD-ACTION-FAST-V1"
MODEL_ID = "Qwen/Qwen2.5-32B-Instruct"
MODEL_REVISION = "5ede1c97bbab6ce5cda5812749b4c0bdf79b18dd"
TOKENIZER_REVISION = MODEL_REVISION
READ_SLOTS = 4
ENV_SLOTS = 9
SLOTS_PER_TRAJECTORY = READ_SLOTS + ENV_SLOTS

CONDITIONS = (
    "GOLD_REC",
    "NONE_REC",
    "ATOMS_REC",
    "AUTH_REPLAY",
    "SHAM_REC",
    "CUT_REC",
    "TWIN_REC",
)
OUTCOME_STATES = frozenset(
    {
        "SCIENTIFIC_VALID_SUCCESS",
        "SCIENTIFIC_VALID_NONSUCCESS",
        "MODEL_INVALID",
        "INFRASTRUCTURE_FAILURE",
        "RESOURCE_CEILING_EXCEEDED",
        "CANCELLED",
    }
)

# Exact R09 bounds.  Values are copied, not recomputed or relaxed.
RESOURCE_CEILINGS: Mapping[str, int | float] = {
    "input_tokens_per_call": 16_384,
    "input_bytes_per_call": 131_072,
    "output_tokens_per_call": 256,
    "output_bytes_per_call": 4_096,
    "context_tokens_per_call": 16_640,
    "row_tokens_per_return": 256,
    "row_bytes_per_return": 4_096,
    "row_tokens_per_trajectory": 1_024,
    "row_bytes_per_trajectory": 16_384,
    "scratch_tokens": 128,
    "scratch_bytes": 2_048,
    "history_tokens_per_call": 8_192,
    "history_bytes_per_call": 65_536,
    "input_tokens_per_trajectory": 212_992,
    "output_tokens_per_trajectory": 3_328,
    "input_bytes_per_trajectory": 1_703_936,
    "output_bytes_per_trajectory": 53_248,
    "input_tokens_gate": 3_833_856,
    "output_tokens_gate": 59_904,
    "input_bytes_gate": 30_670_848,
    "output_bytes_gate": 958_464,
    "a40_gpu_hours": 24,
    "gpu_wall_seconds": 3 * 60 * 60,
    "artifact_bytes": 2 * 1024**3,
    "incremental_external_usd": 0.0,
}

DECODING = {
    "do_sample": False,
    "temperature": 0,
    "top_p": 1,
    "num_beams": 1,
    "num_return_sequences": 1,
    "max_new_tokens": 256,
    "fallback": False,
    "seed": 0,
    "tie_policy": "BACKEND_DETERMINISTIC_ARGMAX",
}

ALLOWED_PASS_CLAIM = (
    "one pinned frozen Qwen2.5-32B model used supplied target-independent "
    "connected rows through the exact registered recurrent interface on all "
    "four nested J/P sides of one deterministic fixture, with two prospective "
    "exact replay/sham/cut/twin fixture checks"
)
ALLOWED_FAILURE_CLAIM = (
    "the exact renderer, key language, four-read/nine-action generic recurrent "
    "interface failed on the selected deterministic fixture"
)
FORBIDDEN_CLAIM_TERMS = frozenset(
    {
        "adaptive-key necessity",
        "benchmark",
        "compression",
        "dream",
        "efficiency",
        "flywheel",
        "generalization",
        "learning",
        "lora",
        "memory superiority",
        "paper evidence",
        "reliability",
        "saturation",
        "scaling",
        "sleep",
    }
)


def canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        .encode("utf-8")
        + b"\n"
    )


def digest(value: Any) -> str:
    payload = value if isinstance(value, bytes) else canonical_bytes(value)
    return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True)
class TrajectoryRegistration:
    trajectory_id: str
    condition: str
    target_id: str
    parent_id: str | None = None

    def __post_init__(self) -> None:
        if self.condition not in CONDITIONS:
            raise ValueError("unregistered G1 condition")


@dataclass(frozen=True)
class OpportunityRegistration:
    opportunity_id: str
    trajectory_id: str
    slot_index: int
    phase: str


def build_roster() -> tuple[TrajectoryRegistration, ...]:
    """Return the exact repaired 18-trajectory roster in dispatch order."""

    four = ("J_H", "J_TWIN", "P_H", "P_TWIN")
    rows: list[TrajectoryRegistration] = []
    for condition in ("GOLD_REC", "NONE_REC"):
        rows.extend(
            TrajectoryRegistration(f"{condition}:{target}", condition, target)
            for target in four
        )
    rows.extend(
        TrajectoryRegistration(f"ATOMS_REC:{target}", "ATOMS_REC", target)
        for target in ("P_H", "P_TWIN")
    )
    for condition in ("AUTH_REPLAY", "SHAM_REC", "CUT_REC", "TWIN_REC"):
        for target in ("J_H", "P_H"):
            parent = f"GOLD_REC:{target}"
            rows.append(
                TrajectoryRegistration(
                    f"{condition}:{target}", condition, target, parent_id=parent
                )
            )
    result = tuple(rows)
    counts = {condition: sum(row.condition == condition for row in result) for condition in CONDITIONS}
    if counts != {
        "GOLD_REC": 4,
        "NONE_REC": 4,
        "ATOMS_REC": 2,
        "AUTH_REPLAY": 2,
        "SHAM_REC": 2,
        "CUT_REC": 2,
        "TWIN_REC": 2,
    } or len(result) != 18:
        raise AssertionError("G1 roster drift")
    return result


def build_opportunity_registry(
    roster: tuple[TrajectoryRegistration, ...] | None = None,
) -> tuple[OpportunityRegistration, ...]:
    rows: list[OpportunityRegistration] = []
    for trajectory in roster or build_roster():
        for slot in range(SLOTS_PER_TRAJECTORY):
            phase = "READ" if slot < READ_SLOTS else "ENV"
            identity = digest(
                {
                    "protocol": PROTOCOL,
                    "trajectory_id": trajectory.trajectory_id,
                    "slot_index": slot,
                    "phase": phase,
                }
            )
            rows.append(
                OpportunityRegistration(identity, trajectory.trajectory_id, slot, phase)
            )
    result = tuple(rows)
    if len(result) != 234 or len({row.opportunity_id for row in result}) != 234:
        raise AssertionError("G1 must register exactly 234 distinct opportunities")
    return result


def validate_claim(text: str, *, passed: bool) -> None:
    allowed = ALLOWED_PASS_CLAIM if passed else ALLOWED_FAILURE_CLAIM
    if text != allowed:
        raise ValueError("result text is not the exact claim-firewall whitelist entry")
    lowered = text.casefold()
    if any(term in lowered for term in FORBIDDEN_CLAIM_TERMS):
        raise ValueError("result text crosses the G1 claim firewall")
