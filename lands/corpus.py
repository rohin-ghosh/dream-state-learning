"""Measured G-series exposure recipe over one-hop Semantic World memories."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .model import AtomicMemory, GoalDepth
from .world import SemanticWorld


RULE_KINDS = frozenset(
    {
        "public_source_rule",
        "palette_definition",
        "meta_parents",
        "meta_operator",
        "pigment_map",
    }
)


@dataclass(frozen=True)
class CorpusRecipe:
    duplicates_per_fact: int = 8
    rule_exposure_multiplier: int = 3
    expected_epochs: int = 25

    def validate(self) -> None:
        if min(
            self.duplicates_per_fact,
            self.rule_exposure_multiplier,
            self.expected_epochs,
        ) < 1:
            raise ValueError("corpus recipe values must be positive")


@dataclass(frozen=True)
class CorpusRecord:
    kind: str
    qa_line: str
    duplicates: int
    expected_touches: int
    evidence_ids: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "kind": self.kind,
            "qa_line": self.qa_line,
            "duplicates": self.duplicates,
            "expected_touches": self.expected_touches,
            "evidence_ids": list(self.evidence_ids),
        }


@dataclass(frozen=True)
class CorpusBundle:
    skin: str
    recipe: CorpusRecipe
    records: tuple[CorpusRecord, ...]
    lines: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "skin": self.skin,
            "recipe": {
                "duplicates_per_fact": self.recipe.duplicates_per_fact,
                "rule_exposure_multiplier": self.recipe.rule_exposure_multiplier,
                "expected_epochs": self.recipe.expected_epochs,
            },
            "records": [record.to_dict() for record in self.records],
            "n_unique": len(self.records),
            "n_training_lines": len(self.lines),
        }


def build_atomic_corpus(
    world: SemanticWorld,
    skin: str = "aligned",
    *,
    depths: Iterable[GoalDepth | str] = tuple(GoalDepth),
    resolved_d3: bool = False,
    recipe: CorpusRecipe | None = None,
) -> CorpusBundle:
    """Deduplicate atomic QA lines and apply the measured exposure recipe."""
    recipe = recipe or CorpusRecipe()
    recipe.validate()
    normalized_depths = {
        depth if isinstance(depth, GoalDepth) else GoalDepth(depth) for depth in depths
    }
    memories: list[AtomicMemory] = []
    for goal in world.eval_goals():
        if goal.depth not in normalized_depths:
            continue
        memories.extend(
            world.atomic_memories_for(
                goal,
                skin,
                resolved=resolved_d3 and goal.depth == GoalDepth.D3,
            )
        )

    deduplicated: dict[str, dict[str, object]] = {}
    for memory in memories:
        line = memory.qa_line()
        entry = deduplicated.setdefault(
            line,
            {
                "kind": memory.kind,
                "evidence_ids": set(),
            },
        )
        if entry["kind"] != memory.kind:
            raise ValueError(f"one QA line has conflicting kinds: {line}")
        entry["evidence_ids"].update(memory.evidence_ids)  # type: ignore[union-attr]

    records = []
    lines = []
    for qa_line, entry in sorted(deduplicated.items()):
        kind = str(entry["kind"])
        multiplier = recipe.rule_exposure_multiplier if kind in RULE_KINDS else 1
        duplicates = recipe.duplicates_per_fact * multiplier
        records.append(
            CorpusRecord(
                kind=kind,
                qa_line=qa_line,
                duplicates=duplicates,
                expected_touches=duplicates * recipe.expected_epochs,
                evidence_ids=tuple(sorted(entry["evidence_ids"])),  # type: ignore[arg-type]
            )
        )
        lines.extend([qa_line] * duplicates)
    return CorpusBundle(skin, recipe, tuple(records), tuple(lines))
