"""Serializable public and evaluator types for Action World v0."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Mapping


SCHEMA_VERSION = "action-world-v0.1"


class ActionDepth(str, Enum):
    """Increasing demands on experiential action memory."""

    A0 = "A0"  # witnessed threshold: recall the previously revealed danger
    A1 = "A1"  # unseen threshold: execute the generic inspect-and-react policy
    A2 = "A2"  # unseen threshold: infer its danger and cross under a tight budget
    A3 = "A3"  # compose two inferred crossings into one action chain


LEGAL_ACTIONS = (
    "open",
    "inspect_left",
    "inspect_right",
    "guard_left",
    "guard_right",
    "enter",
)


@dataclass(frozen=True)
class WorldConfig:
    seed: int = 0
    n_feature_bits: int = 4
    n_training_patterns: int = 12
    reckless_fraction: float = 0.5
    goals_per_depth: int = 4

    def validate(self) -> None:
        if self.n_feature_bits != 4:
            raise ValueError("v0 fixes n_feature_bits=4 for readable thresholds")
        total = 2 ** self.n_feature_bits
        if not 6 <= self.n_training_patterns <= total - 2:
            raise ValueError("n_training_patterns must leave >=2 held-out patterns")
        if not 0.0 <= self.reckless_fraction <= 1.0:
            raise ValueError("reckless_fraction must be in [0, 1]")
        if self.goals_per_depth < 1:
            raise ValueError("goals_per_depth must be positive")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Threshold:
    id: str
    name: str
    features: tuple[tuple[str, str], ...]
    split: str

    def description(self) -> str:
        values = {key: value for key, value in self.features}
        frame_article = "an" if values["frame"][0].lower() in "aeiou" else "a"
        return (
            f"{self.name} bears a {values['sigil']} sigil, has "
            f"{values['hinge']} hinges and {frame_article} {values['frame']} frame, "
            f"and leaks a {values['draft']} draft."
        )

    def public_dict(self) -> dict[str, Any]:
        return {
            "threshold_id": self.id,
            "name": self.name,
            "features": {key: value for key, value in self.features},
            "description": self.description(),
        }


@dataclass(frozen=True)
class StepRecord:
    id: str
    episode_id: str
    step: int
    threshold_id: str
    action: str
    observation: str
    reward: float
    terminal: bool
    success: bool
    revealed: tuple[str, str] | None = None

    def public_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "step_id": self.id,
            "episode_id": self.episode_id,
            "step": self.step,
            "threshold_id": self.threshold_id,
            "action": self.action,
            "observation": self.observation,
            "reward": self.reward,
            "terminal": self.terminal,
            "success": self.success,
        }
        if self.revealed is not None:
            result["revealed"] = {
                "side": self.revealed[0],
                "status": self.revealed[1],
            }
        return result


@dataclass(frozen=True)
class Episode:
    id: str
    threshold_id: str
    policy_kind: str
    intro: str
    steps: tuple[StepRecord, ...]
    success: bool

    def public_dict(self) -> dict[str, Any]:
        return {
            "episode_id": self.id,
            "threshold_id": self.threshold_id,
            "intro": self.intro,
            "steps": [step.public_dict() for step in self.steps],
            "success": self.success,
        }


@dataclass(frozen=True)
class Lifetime:
    episodes: tuple[Episode, ...]

    @property
    def steps(self) -> tuple[StepRecord, ...]:
        return tuple(step for episode in self.episodes for step in episode.steps)

    def public_dict(self) -> dict[str, Any]:
        return {"episodes": [episode.public_dict() for episode in self.episodes]}


@dataclass(frozen=True)
class Goal:
    id: str
    depth: ActionDepth
    threshold_ids: tuple[str, ...]
    max_steps: int
    question: str
    proof_id: str
    tags: tuple[str, ...] = ()

    def public_dict(self) -> dict[str, Any]:
        return {
            "goal_id": self.id,
            "threshold_ids": list(self.threshold_ids),
            "max_steps": self.max_steps,
            "question": self.question,
            "legal_actions": list(LEGAL_ACTIONS),
            "interactive": True,
        }


@dataclass(frozen=True)
class ProofNode:
    id: str
    kind: str
    depends_on: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()
    payload: Mapping[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind,
            "depends_on": list(self.depends_on),
            "evidence_ids": list(self.evidence_ids),
            "payload": dict(self.payload or {}),
        }


@dataclass(frozen=True)
class ProofGraph:
    id: str
    root_id: str
    depth: ActionDepth
    nodes: tuple[ProofNode, ...]

    def canonical_shape(self) -> str:
        by_id = {node.id: node for node in self.nodes}
        active: set[str] = set()
        memo: dict[str, str] = {}

        def visit(node_id: str) -> str:
            if node_id in memo:
                return memo[node_id]
            if node_id in active:
                raise ValueError(f"{self.id}: proof graph contains a cycle")
            if node_id not in by_id:
                raise ValueError(f"{self.id}: missing dependency {node_id}")
            active.add(node_id)
            node = by_id[node_id]
            children = sorted(visit(child) for child in node.depends_on)
            shape = f"{node.kind}({','.join(children)})"
            active.remove(node_id)
            memo[node_id] = shape
            return shape

        return visit(self.root_id)

    def validate(self, evidence_ids: set[str]) -> None:
        if len({node.id for node in self.nodes}) != len(self.nodes):
            raise ValueError(f"{self.id}: duplicate proof node")
        self.canonical_shape()
        for node in self.nodes:
            unknown = set(node.evidence_ids) - evidence_ids
            if unknown:
                raise ValueError(f"{self.id}: unknown evidence {sorted(unknown)}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "root_id": self.root_id,
            "depth": self.depth.value,
            "canonical_shape": self.canonical_shape(),
            "nodes": [node.to_dict() for node in self.nodes],
        }


@dataclass(frozen=True)
class StepResult:
    action: str
    observation: str
    reward: float
    terminal: bool
    success: bool
    revealed: tuple[str, str] | None = None


@dataclass(frozen=True)
class RunResult:
    goal_id: str
    actions: tuple[str, ...]
    observations: tuple[str, ...]
    total_reward: float
    success: bool
    terminal_reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
