"""Serializable types for Semantic World v0."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Iterable, Mapping


SCHEMA_VERSION = "lands-v0.1"


class GoalDepth(str, Enum):
    D0 = "D0"
    D1 = "D1"
    D2 = "D2"
    D3 = "D3"


@dataclass(frozen=True)
class WorldConfig:
    seed: int = 0
    n_animals: int = 15
    n_source_lands: int = 6
    meta_parent_count: int = 3
    observations_per_episode: int = 3
    context_observation_budget: int = 12
    dispersion_buffer: int = 24
    d0_per_animal: int = 1
    max_reachout_actions: int = 6

    def validate(self) -> None:
        if self.n_animals < 9:
            raise ValueError("n_animals must be >= 9 so every depth has support")
        if self.n_animals % 6 != 3:
            raise ValueError(
                "v0 requires n_animals % 6 == 3 for exact role/palette balance"
            )
        if self.n_animals > 30:
            raise ValueError("v0 textual skins currently support at most 30 animals")
        if self.n_source_lands != 6:
            raise ValueError(
                "v0 fixes n_source_lands=6 (primary/secondary x 3 rotations)"
            )
        if self.meta_parent_count != 3:
            raise ValueError(
                "v0 fixes meta_parent_count=3; pairwise pigment unions are not "
                "uniquely identifiable under the six-land factor design"
            )
        if self.observations_per_episode < 1:
            raise ValueError("observations_per_episode must be positive")
        if self.context_observation_budget < 4:
            raise ValueError("context_observation_budget must be >= 4")
        if self.dispersion_buffer <= self.context_observation_budget:
            raise ValueError(
                "dispersion_buffer must exceed context_observation_budget"
            )
        if self.d0_per_animal != 1:
            raise ValueError("v0 fixes d0_per_animal=1 to keep depth/kind balance exact")
        if self.max_reachout_actions < 0:
            raise ValueError("max_reachout_actions cannot be negative")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Observation:
    id: str
    episode_id: str
    step: int
    animal_id: str
    land_id: str
    color_id: str
    phase: str
    repeated: bool = False

    def cell(self) -> tuple[str, str]:
        return self.animal_id, self.land_id

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Episode:
    id: str
    phase: str
    observations: tuple[Observation, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "phase": self.phase,
            "observations": [o.to_dict() for o in self.observations],
        }


@dataclass(frozen=True)
class Lifetime:
    episodes: tuple[Episode, ...]

    @property
    def observations(self) -> tuple[Observation, ...]:
        return tuple(o for episode in self.episodes for o in episode.observations)

    def observation_map(self) -> dict[str, Observation]:
        return {o.id: o for o in self.observations}

    def witnessed_cells(self) -> set[tuple[str, str]]:
        return {o.cell() for o in self.observations}

    def subset(self, observation_ids: Iterable[str]) -> "Lifetime":
        wanted = set(observation_ids)
        episodes = []
        for episode in self.episodes:
            selected = tuple(o for o in episode.observations if o.id in wanted)
            if selected:
                episodes.append(Episode(episode.id, episode.phase, selected))
        return Lifetime(tuple(episodes))

    def to_dict(self) -> dict[str, Any]:
        return {"episodes": [episode.to_dict() for episode in self.episodes]}


@dataclass(frozen=True)
class Goal:
    id: str
    depth: GoalDepth
    animal_id: str
    land_id: str
    answer_color_id: str
    proof_id: str
    tags: tuple[str, ...] = ()

    def cell(self) -> tuple[str, str]:
        return self.animal_id, self.land_id

    def to_dict(self, include_answer: bool = True) -> dict[str, Any]:
        result: dict[str, Any] = {
            "id": self.id,
            "depth": self.depth.value,
            "animal_id": self.animal_id,
            "land_id": self.land_id,
            "proof_id": self.proof_id,
            "tags": list(self.tags),
        }
        if include_answer:
            result["answer_color_id"] = self.answer_color_id
        return result


@dataclass(frozen=True)
class ProofNode:
    id: str
    kind: str
    depends_on: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()
    payload: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind,
            "depends_on": list(self.depends_on),
            "evidence_ids": list(self.evidence_ids),
            "payload": dict(self.payload),
        }


@dataclass(frozen=True)
class ProofGraph:
    id: str
    root_id: str
    depth: GoalDepth
    nodes: tuple[ProofNode, ...]

    def validate(self, known_evidence_ids: set[str]) -> None:
        by_id = {node.id: node for node in self.nodes}
        if len(by_id) != len(self.nodes):
            raise ValueError(f"{self.id}: duplicate proof node")
        if self.root_id not in by_id:
            raise ValueError(f"{self.id}: root is missing")
        for node in self.nodes:
            unknown_nodes = set(node.depends_on) - set(by_id)
            if unknown_nodes:
                raise ValueError(f"{self.id}: unknown dependencies {unknown_nodes}")
            unknown_evidence = set(node.evidence_ids) - known_evidence_ids
            if unknown_evidence:
                raise ValueError(f"{self.id}: unknown evidence {unknown_evidence}")
        self.canonical_shape()  # also detects cycles

    def canonical_shape(self) -> str:
        """Canonical dependency topology, intentionally ignoring payload IDs."""
        by_id = {node.id: node for node in self.nodes}
        active: set[str] = set()
        memo: dict[str, str] = {}

        def visit(node_id: str) -> str:
            if node_id in memo:
                return memo[node_id]
            if node_id in active:
                raise ValueError(f"{self.id}: cyclic proof graph")
            active.add(node_id)
            node = by_id[node_id]
            children = sorted(visit(child) for child in node.depends_on)
            shape = f"{node.kind}({','.join(children)})"
            active.remove(node_id)
            memo[node_id] = shape
            return shape

        return visit(self.root_id)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "root_id": self.root_id,
            "depth": self.depth.value,
            "canonical_shape": self.canonical_shape(),
            "nodes": [node.to_dict() for node in self.nodes],
        }


@dataclass(frozen=True)
class MemoryClaim:
    """Typed dream claim.  `payload` uses internal IDs, never model prose."""

    id: str
    kind: str
    payload: Mapping[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "kind": self.kind, "payload": dict(self.payload)}


# Short public alias used in the integration contract.
Claim = MemoryClaim


@dataclass
class VerificationBudget:
    max_counterfactual_queries: int = 0
    used_counterfactual_queries: int = 0

    @property
    def remaining(self) -> int:
        return max(0, self.max_counterfactual_queries - self.used_counterfactual_queries)

    def consume(self) -> bool:
        if self.remaining <= 0:
            return False
        self.used_counterfactual_queries += 1
        return True


@dataclass
class ReachoutBudget:
    max_actions: int
    used_actions: int = 0

    @property
    def remaining(self) -> int:
        return max(0, self.max_actions - self.used_actions)

    def consume(self) -> bool:
        if self.remaining <= 0:
            return False
        self.used_actions += 1
        return True


@dataclass(frozen=True)
class VerificationResult:
    accepted: bool
    status: str
    mode: str
    reason: str
    counterfactual_queries: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RenderedObservation:
    observation_id: str
    episode_id: str
    text: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RenderedGoal:
    goal_id: str
    question: str
    answer: str | None = None

    def to_dict(self, include_answer: bool = False) -> dict[str, Any]:
        result: dict[str, Any] = {
            "goal_id": self.goal_id,
            "question": self.question,
        }
        if include_answer and self.answer is not None:
            result["answer"] = self.answer
        return result


@dataclass(frozen=True)
class RenderedWorld:
    skin: str
    observations: tuple[RenderedObservation, ...]
    goals: tuple[RenderedGoal, ...]

    def to_dict(self, include_answers: bool = False) -> dict[str, Any]:
        return {
            "skin": self.skin,
            "observations": [o.to_dict() for o in self.observations],
            "goals": [g.to_dict(include_answers) for g in self.goals],
        }


@dataclass(frozen=True)
class AtomicMemory:
    """One adapter-readable proof leaf: one question, one canonical answer."""

    id: str
    kind: str
    question: str
    answer: str
    evidence_ids: tuple[str, ...] = ()

    def qa_line(self) -> str:
        return f"Q: {self.question} A: {self.answer}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind,
            "question": self.question,
            "answer": self.answer,
            "evidence_ids": list(self.evidence_ids),
            "qa_line": self.qa_line(),
        }
