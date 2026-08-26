"""Semantic World v0.2 meta-composition diagnostic.

V0's D0-D2 instrument remains unchanged.  This module replaces only the
underspecified D3 mechanic with an additive-pigment curriculum in which:

* two known-parent demonstration lands identify the shared blend operator;
* twelve target lands hide their parent sets and one role outcome each;
* no target outcome signature can be copied from an ordinary land; and
* the operator and every target parent set are jointly identifiable within a
  declared family of simpler competing operators.

The module is deliberately CPU-only.  It is the acceptance instrument for a
later GPU integration, not a model result.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from functools import reduce
import hashlib
import itertools
import json
from math import gcd
import random
from typing import Callable, Iterable, Sequence

from .model import WorldConfig
from .skins import make_skin
from .world import SemanticWorld


PigmentRatio = tuple[int, int, int]

RATIO_FOR_COLOR: dict[str, PigmentRatio] = {
    "red": (1, 0, 0),
    "yellow": (0, 1, 0),
    "blue": (0, 0, 1),
    "orange": (1, 1, 0),
    "green": (0, 1, 1),
    "purple": (1, 0, 1),
    "brown": (1, 1, 1),
}
COLOR_FOR_RATIO = {ratio: color for color, ratio in RATIO_FOR_COLOR.items()}

RATIO_SURFACES: dict[PigmentRatio, str] = {
    **{ratio: color for color, ratio in RATIO_FOR_COLOR.items()},
    (2, 1, 0): "red-orange",
    (1, 2, 0): "yellow-orange",
    (0, 2, 1): "yellow-green",
    (0, 1, 2): "blue-green",
    (2, 0, 1): "red-purple",
    (1, 0, 2): "blue-purple",
    (3, 1, 1): "red-brown",
    (1, 3, 1): "yellow-brown",
    (1, 1, 3): "blue-brown",
    (2, 3, 1): "ochre",
    (1, 2, 3): "slate",
    (3, 1, 2): "russet",
    (3, 3, 2): "amber-brown",
    (2, 3, 3): "teal-brown",
    (3, 2, 3): "plum-brown",
}

DEMO_LAND_IDS = ("blend_demo_00", "blend_demo_01")
TARGET_LAND_IDS = tuple(f"blend_target_{index:02d}" for index in range(12))

_ALIGNED_BLEND_LANDS = {
    DEMO_LAND_IDS[0]: "Mixingland",
    DEMO_LAND_IDS[1]: "Swirlland",
    **dict(
        zip(
            TARGET_LAND_IDS,
            (
                "Blendyland", "Meldyland", "Fusionland", "Braidedland",
                "Confluxland", "Mosaicland", "Alloyland", "Weaveland",
                "Prismaland", "Grandblend", "Tapestryland", "Synthesisland",
            ),
        )
    ),
}
_NEUTRAL_BLEND_LANDS = {
    DEMO_LAND_IDS[0]: "Arvane",
    DEMO_LAND_IDS[1]: "Corthel",
    **dict(
        zip(
            TARGET_LAND_IDS,
            (
                "Ulvane", "Nestri", "Pavrix", "Doreth", "Kalune", "Vossin",
                "Embral", "Jorvik", "Quorin", "Selnar", "Tavrek", "Wexora",
            ),
        )
    ),
}
_CONFLICTING_BLEND_LANDS = {
    DEMO_LAND_IDS[0]: "Stillland",
    DEMO_LAND_IDS[1]: "Plainland",
    **dict(
        zip(
            TARGET_LAND_IDS,
            (
                "Separateland", "Sololand", "Dividerland", "Partland",
                "Apartland", "Singleland", "Isleland", "Splitland",
                "Lonefield", "Unmixland", "Breakland", "SiloLand",
            ),
        )
    ),
}


def normalize_ratio(values: Sequence[int]) -> PigmentRatio:
    """Reduce a non-empty pigment-count vector to its primitive ratio."""
    if len(values) != 3 or any(value < 0 for value in values):
        raise ValueError("a pigment ratio must contain three non-negative counts")
    if not any(values):
        raise ValueError("an empty pigment mixture has no color")
    divisor = reduce(gcd, values)
    return tuple(value // divisor for value in values)  # type: ignore[return-value]


def pigment_sum(ratios: Iterable[PigmentRatio]) -> PigmentRatio:
    """Add pigment amounts and preserve their relative multiplicity."""
    material = tuple(ratios)
    if not material:
        raise ValueError("cannot mix zero colors")
    return normalize_ratio(
        tuple(sum(ratio[index] for ratio in material) for index in range(3))
    )


def pigment_union(ratios: Iterable[PigmentRatio]) -> PigmentRatio:
    """The lossy Boolean-union operator used by Semantic World v0."""
    material = tuple(ratios)
    if not material:
        raise ValueError("cannot mix zero colors")
    return tuple(
        int(any(ratio[index] for ratio in material)) for index in range(3)
    )  # type: ignore[return-value]


@dataclass(frozen=True)
class BlendObservation:
    id: str
    episode_id: str
    animal_id: str
    land_id: str
    ratio: PigmentRatio

    def cell(self) -> tuple[str, str]:
        return self.animal_id, self.land_id


@dataclass(frozen=True)
class FeedRelation:
    id: str
    episode_id: str
    blend_land_id: str
    parent_land_ids: tuple[str, str]


@dataclass(frozen=True)
class BlendClassObservation:
    id: str
    episode_id: str
    blend_land_id: str


@dataclass(frozen=True)
class BlendGoal:
    id: str
    animal_id: str
    land_id: str
    answer_ratio: PigmentRatio
    hidden_role: int

    def cell(self) -> tuple[str, str]:
        return self.animal_id, self.land_id


@dataclass(frozen=True)
class IdentifiabilityReport:
    seed: int
    valid: bool
    surviving_operators: tuple[str, ...]
    target_parent_candidates: dict[str, tuple[tuple[str, ...], ...]]
    source_copy_candidates: dict[str, tuple[str, ...]]
    hidden_role_examples: dict[str, int]
    goal_answer_counts: dict[str, int]

    def to_dict(self) -> dict[str, object]:
        result = asdict(self)
        result["target_parent_candidates"] = {
            land: [list(candidate) for candidate in candidates]
            for land, candidates in self.target_parent_candidates.items()
        }
        result["source_copy_candidates"] = {
            land: list(candidates)
            for land, candidates in self.source_copy_candidates.items()
        }
        return result


class SemanticWorldV02:
    """D3-v0.2 wrapper around an unchanged Semantic World v0 source world."""

    schema_version = "lands-v0.2-meta"
    operator = "pigment_sum"

    def __init__(self, config: WorldConfig | None = None):
        self.config = config or WorldConfig()
        self.base = SemanticWorld(self.config)
        self.animal_ids = self.base.animal_ids
        self.source_land_ids = self.base.source_land_ids
        self.anchor_animals = self.base.anchor_animals
        self.eval_animals = self.base.eval_animals

        land_for = {
            (spec.palette, spec.rotation): land
            for land, spec in self.base.land_specs.items()
        }
        # Same-rotation primary/secondary pairs visibly distinguish additive
        # mixing from Boolean union because multiplicity creates rich colors.
        self.demo_parents: dict[str, tuple[str, str]] = {
            DEMO_LAND_IDS[0]: (
                land_for[("primary", 0)],
                land_for[("secondary", 0)],
            ),
            DEMO_LAND_IDS[1]: (
                land_for[("primary", 1)],
                land_for[("secondary", 1)],
            ),
        }
        # Twelve independently queried targets span 2/3/4/5-parent mixtures.
        # Every set is uniquely recoverable from either two of its three role
        # outcomes even when the solver searches all subset sizes 2..5.
        ordered_lands = (
            land_for[("primary", 0)],
            land_for[("primary", 1)],
            land_for[("primary", 2)],
            land_for[("secondary", 0)],
            land_for[("secondary", 1)],
            land_for[("secondary", 2)],
        )

        def parent_set(*indices: int) -> tuple[str, ...]:
            return tuple(sorted(ordered_lands[index] for index in indices))

        target_specs = [
            # Pair targets use the cross-rotation orbit, distinct from both
            # same-rotation demonstration pairs.
            (parent_set(0, 5), 0),
            (parent_set(1, 3), 1),
            (parent_set(2, 4), 2),
            (parent_set(0, 3, 5), 0),
            (parent_set(1, 3, 4), 1),
            (parent_set(2, 4, 5), 2),
            (parent_set(0, 1, 3, 4), 0),
            (parent_set(1, 2, 4, 5), 1),
            (parent_set(0, 2, 3, 5), 2),
            (parent_set(0, 1, 3, 4, 5), 0),
            (parent_set(1, 2, 3, 4, 5), 1),
            (parent_set(0, 2, 3, 4, 5), 2),
        ]
        target_rng = random.Random(self.config.seed ^ 0x5EED_02D3)
        target_rng.shuffle(target_specs)
        self.target_parents: dict[str, tuple[str, ...]] = {
            land: parents
            for land, (parents, hidden_role) in zip(TARGET_LAND_IDS, target_specs)
        }
        self.target_hidden_roles = {
            land: hidden_role
            for land, (parents, hidden_role) in zip(TARGET_LAND_IDS, target_specs)
        }
        self.lab_ratios = tuple(
            sorted(ratio for ratio in RATIO_SURFACES if ratio not in COLOR_FOR_RATIO)
        )
        self.feed_relations = self._build_feed_relations()
        self.target_class_observations = tuple(
            BlendClassObservation(
                id=f"v02_class_{index:03d}",
                episode_id=f"v02_target_{index:03d}",
                blend_land_id=land_id,
            )
            for index, land_id in enumerate(TARGET_LAND_IDS)
        )
        self.blend_observations = self._build_blend_observations()
        self.goals = self._build_goals()
        report = self.identifiability_report()
        if not report.valid:
            raise RuntimeError(f"invalid Semantic World v0.2 design: {report.to_dict()}")

    def source_ratio_for_role(self, role: int, land_id: str) -> PigmentRatio:
        return RATIO_FOR_COLOR[self.base.source_color_for_role(role, land_id)]

    def blend_ratio_for_role(self, role: int, land_id: str) -> PigmentRatio:
        if land_id in self.demo_parents:
            parents: Sequence[str] = self.demo_parents[land_id]
        elif land_id in self.target_parents:
            parents = self.target_parents[land_id]
        else:
            raise KeyError(f"unknown blend land {land_id}")
        return pigment_sum(
            self.source_ratio_for_role(role, parent) for parent in parents
        )

    def answer_ratio(self, animal_id: str, land_id: str) -> PigmentRatio:
        return self.blend_ratio_for_role(self.base.animal_roles[animal_id], land_id)

    def _build_feed_relations(self) -> tuple[FeedRelation, ...]:
        return tuple(
            FeedRelation(
                id=f"v02_feed_{index:03d}",
                episode_id=f"v02_demo_{index:03d}",
                blend_land_id=land,
                parent_land_ids=tuple(sorted(parents)),
            )
            for index, (land, parents) in enumerate(sorted(self.demo_parents.items()))
        )

    def _build_blend_observations(self) -> tuple[BlendObservation, ...]:
        observations: list[BlendObservation] = []
        index = 0
        for land_id in DEMO_LAND_IDS:
            for role, animal_id in enumerate(self.anchor_animals):
                observations.append(
                    BlendObservation(
                        id=f"v02_obs_{index:04d}",
                        episode_id=f"v02_demo_{DEMO_LAND_IDS.index(land_id):03d}",
                        animal_id=animal_id,
                        land_id=land_id,
                        ratio=self.blend_ratio_for_role(role, land_id),
                    )
                )
                index += 1
        for land_id in TARGET_LAND_IDS:
            hidden_role = self.target_hidden_roles[land_id]
            for role, animal_id in enumerate(self.anchor_animals):
                if role == hidden_role:
                    continue
                observations.append(
                    BlendObservation(
                        id=f"v02_obs_{index:04d}",
                        episode_id=f"v02_target_{TARGET_LAND_IDS.index(land_id):03d}",
                        animal_id=animal_id,
                        land_id=land_id,
                        ratio=self.blend_ratio_for_role(role, land_id),
                    )
                )
                index += 1
        return tuple(observations)

    def _build_goals(self) -> tuple[BlendGoal, ...]:
        goals = []
        available = {
            role: [
                animal
                for animal in self.eval_animals
                if self.base.animal_roles[animal] == role
            ]
            for role in range(3)
        }
        for land_id in TARGET_LAND_IDS:
            hidden_role = self.target_hidden_roles[land_id]
            animal_id = available[hidden_role].pop(0)
            goals.append(
                BlendGoal(
                    id=f"v02_goal_{len(goals):04d}",
                    animal_id=animal_id,
                    land_id=land_id,
                    answer_ratio=self.answer_ratio(animal_id, land_id),
                    hidden_role=hidden_role,
                )
            )
        if any(available.values()):
            raise RuntimeError("v0.2 target assignment did not consume every eval animal")
        return tuple(goals)

    def _operator_predictions(
        self,
        operator: str,
        ratios: Sequence[PigmentRatio],
    ) -> tuple[PigmentRatio, ...]:
        if operator == "pigment_sum":
            return (pigment_sum(ratios),)
        if operator == "pigment_union":
            return (pigment_union(ratios),)
        if operator == "copy_any_parent":
            return tuple(ratios)
        if operator == "constant_brown":
            return (RATIO_FOR_COLOR["brown"],)
        raise ValueError(f"unknown candidate operator {operator}")

    def surviving_operators(self) -> tuple[str, ...]:
        candidates = (
            "pigment_sum",
            "pigment_union",
            "copy_any_parent",
            "constant_brown",
        )
        surviving = []
        observed = {observation.cell(): observation.ratio for observation in self.blend_observations}
        for operator in candidates:
            matches = True
            for land_id, parents in self.demo_parents.items():
                for role, animal_id in enumerate(self.anchor_animals):
                    parent_ratios = [
                        self.source_ratio_for_role(role, parent) for parent in parents
                    ]
                    if observed[(animal_id, land_id)] not in self._operator_predictions(
                        operator, parent_ratios
                    ):
                        matches = False
                        break
                if not matches:
                    break
            if matches:
                surviving.append(operator)
        return tuple(surviving)

    def parent_candidates(self, land_id: str) -> tuple[tuple[str, ...], ...]:
        hidden_role = self.target_hidden_roles[land_id]
        observed_by_role = {
            self.base.animal_roles[observation.animal_id]: observation.ratio
            for observation in self.blend_observations
            if observation.land_id == land_id
        }
        assert hidden_role not in observed_by_role
        matches = []
        for parent_count in range(2, len(self.source_land_ids)):
            for parents in itertools.combinations(self.source_land_ids, parent_count):
                if all(
                    pigment_sum(
                        self.source_ratio_for_role(role, parent) for parent in parents
                    )
                    == ratio
                    for role, ratio in observed_by_role.items()
                ):
                    matches.append(tuple(parents))
        return tuple(matches)

    def source_copy_candidates(self, land_id: str) -> tuple[str, ...]:
        observed_by_role = {
            self.base.animal_roles[observation.animal_id]: observation.ratio
            for observation in self.blend_observations
            if observation.land_id == land_id
        }
        return tuple(
            source_land
            for source_land in self.source_land_ids
            if all(
                self.source_ratio_for_role(role, source_land) == ratio
                for role, ratio in observed_by_role.items()
            )
        )

    def identifiability_report(self) -> IdentifiabilityReport:
        operators = self.surviving_operators()
        parent_candidates = {
            land: self.parent_candidates(land) for land in TARGET_LAND_IDS
        }
        source_copies = {
            land: self.source_copy_candidates(land) for land in TARGET_LAND_IDS
        }
        hidden_examples = {
            land: sum(
                self.base.animal_roles[observation.animal_id]
                == self.target_hidden_roles[land]
                for observation in self.blend_observations
                if observation.land_id == land
            )
            for land in TARGET_LAND_IDS
        }
        answer_counts: dict[str, int] = {}
        for goal in self.goals:
            label = self.ratio_surface(goal.answer_ratio, "aligned")
            answer_counts[label] = answer_counts.get(label, 0) + 1

        ordinary_signatures = {
            tuple(self.source_ratio_for_role(role, land) for role in range(3))
            for land in self.source_land_ids
        }
        target_signatures = {
            land: tuple(self.blend_ratio_for_role(role, land) for role in range(3))
            for land in TARGET_LAND_IDS
        }
        demo_signatures = {
            tuple(self.blend_ratio_for_role(role, land) for role in range(3))
            for land in DEMO_LAND_IDS
        }
        observed_ratios = {observation.ratio for observation in self.blend_observations}
        observed_cells = {observation.cell() for observation in self.blend_observations}
        valid = (
            operators == ("pigment_sum",)
            and all(
                candidates == (tuple(self.target_parents[land]),)
                for land, candidates in parent_candidates.items()
            )
            and not any(source_copies.values())
            and all(signature not in ordinary_signatures for signature in target_signatures.values())
            and all(signature not in demo_signatures for signature in target_signatures.values())
            and len(set(target_signatures.values())) == len(TARGET_LAND_IDS)
            and all(count == 0 for count in hidden_examples.values())
            and not any(goal.cell() in observed_cells for goal in self.goals)
            and all(goal.answer_ratio in observed_ratios for goal in self.goals)
            and all(goal.answer_ratio in self.lab_ratios for goal in self.goals)
            and {
                observation.blend_land_id
                for observation in self.target_class_observations
            }
            == set(TARGET_LAND_IDS)
            and len(self.goals) == 12
            and len(answer_counts) == 12
            and set(answer_counts.values()) == {1}
        )
        return IdentifiabilityReport(
            seed=self.config.seed,
            valid=valid,
            surviving_operators=operators,
            target_parent_candidates=parent_candidates,
            source_copy_candidates=source_copies,
            hidden_role_examples=hidden_examples,
            goal_answer_counts=answer_counts,
        )

    def blend_land_surface(self, land_id: str, skin_name: str) -> str:
        mapping = {
            "aligned": _ALIGNED_BLEND_LANDS,
            "neutral": _NEUTRAL_BLEND_LANDS,
            "conflicting": _CONFLICTING_BLEND_LANDS,
        }.get(skin_name)
        if mapping is None:
            raise ValueError(f"unknown skin {skin_name!r}")
        return mapping[land_id]

    def ratio_surface(self, ratio: PigmentRatio, skin_name: str) -> str:
        base_color = COLOR_FOR_RATIO.get(ratio)
        if base_color is not None:
            skin = make_skin(skin_name, self.animal_ids, self.source_land_ids)
            return skin.color(base_color)
        if ratio not in RATIO_SURFACES:
            return f"red{ratio[0]}-yellow{ratio[1]}-blue{ratio[2]}"
        if skin_name == "aligned":
            return RATIO_SURFACES[ratio]
        ordered = tuple(sorted(r for r in RATIO_SURFACES if r not in COLOR_FOR_RATIO))
        index = ordered.index(ratio)
        if skin_name == "neutral":
            return f"vexa{index:02d}"
        if skin_name == "conflicting":
            return RATIO_SURFACES[ordered[(index + 1) % len(ordered)]]
        raise ValueError(f"unknown skin {skin_name!r}")

    def render_lifetime(self, skin_name: str = "aligned") -> tuple[str, ...]:
        skin = make_skin(skin_name, self.animal_ids, self.source_land_ids)
        source_by_phase: dict[str, list[str]] = {}
        for observation, rendered in zip(
            self.base.sample_lifetime().observations,
            self.base.render(skin_name).observations,
        ):
            if observation.land_id in self.source_land_ids:
                source_by_phase.setdefault(observation.phase, []).append(rendered.text)

        lab_lines = []
        pigment_surfaces = tuple(skin.color(color) for color in ("red", "yellow", "blue"))
        for index, ratio in enumerate(self.lab_ratios):
            ingredients = ", ".join(
                f"{count} part{'s' if count != 1 else ''} {pigment}"
                for count, pigment in zip(ratio, pigment_surfaces)
                if count
            )
            label = self.ratio_surface(ratio, skin_name)
            if skin_name == "neutral":
                text = (
                    f"[v02_lab_{index:03d} | v02_lab] A calibration mixture "
                    f"containing {ingredients} is assigned state-token {label}."
                )
            else:
                text = (
                    f"[v02_lab_{index:03d} | v02_lab] In the color workshop, "
                    f"a mixture containing {ingredients} is labeled {label}."
                )
            lab_lines.append(text)
        relation_lines = []
        for relation in self.feed_relations:
            left, right = (skin.land(parent) for parent in relation.parent_land_ids)
            child = self.blend_land_surface(relation.blend_land_id, skin_name)
            if skin_name == "neutral":
                text = (
                    f"[{relation.id} | {relation.episode_id}] A conduit report says "
                    f"zones {left} and {right} jointly feed zone {child}."
                )
            else:
                text = (
                    f"[{relation.id} | {relation.episode_id}] You discover that "
                    f"streams from {left} and {right} jointly feed {child}."
                )
            relation_lines.append(text)

        target_class_lines = []
        for observation in self.target_class_observations:
            land = self.blend_land_surface(observation.blend_land_id, skin_name)
            if skin_name == "neutral":
                text = (
                    f"[{observation.id} | {observation.episode_id}] A structural "
                    f"survey classifies zone {land} in the same confluence class "
                    "as the demonstrated jointly-fed zones; its source zones are "
                    "not directly observed."
                )
            else:
                text = (
                    f"[{observation.id} | {observation.episode_id}] A structural "
                    f"survey classifies {land} in the same confluence class as "
                    "the demonstrated jointly-fed lands; its source lands are "
                    "not directly observed."
                )
            target_class_lines.append(text)

        demo_observation_lines = []
        target_observation_lines = []
        for observation in self.blend_observations:
            animal = skin.animal(observation.animal_id)
            land = self.blend_land_surface(observation.land_id, skin_name)
            color = self.ratio_surface(observation.ratio, skin_name)
            if skin_name == "neutral":
                text = (
                    f"[{observation.id} | {observation.episode_id}] During the visit "
                    f"to zone {land}, entity {animal} has state-token {color}."
                )
            else:
                text = (
                    f"[{observation.id} | {observation.episode_id}] During the visit "
                    f"to {land}, you see the {animal}. Its coat is {color}."
                )
            destination = (
                demo_observation_lines
                if observation.land_id in DEMO_LAND_IDS
                else target_observation_lines
            )
            destination.append(text)
        return (
            tuple(source_by_phase.get("calibration", ()))
            + tuple(lab_lines)
            + tuple(relation_lines)
            + tuple(demo_observation_lines)
            + tuple(source_by_phase.get("dispersion_buffer", ()))
            + tuple(source_by_phase.get("sparse_lifetime", ()))
            + tuple(target_class_lines)
            + tuple(target_observation_lines)
        )

    def render_goals(
        self,
        skin_name: str = "aligned",
        *,
        include_answers: bool = False,
    ) -> tuple[dict[str, str], ...]:
        skin = make_skin(skin_name, self.animal_ids, self.source_land_ids)
        rendered = []
        for goal in self.goals:
            animal = skin.animal(goal.animal_id)
            land = self.blend_land_surface(goal.land_id, skin_name)
            if skin_name == "neutral":
                question = (
                    f"In zone {land}, what state-token does entity {animal} have? "
                    "Answer with exactly one state-token."
                )
            else:
                question = (
                    f"In {land}, what color is the {animal}? "
                    "Answer with exactly one color word."
                )
            row = {"goal_id": goal.id, "question": question}
            if include_answers:
                row["answer"] = self.ratio_surface(goal.answer_ratio, skin_name)
            rendered.append(row)
        return tuple(rendered)

    def world_fingerprint(self) -> str:
        material = {
            "schema_version": self.schema_version,
            "config": self.config.to_dict(),
            # Deliberately exclude v0's retired meta-land from the v0.2
            # fingerprint. Only the shared source world and new meta layer are
            # part of this instrument.
            "animal_roles": self.base.animal_roles,
            "land_specs": {
                land: spec.to_dict() for land, spec in self.base.land_specs.items()
            },
            "demo_parents": self.demo_parents,
            "target_parents": self.target_parents,
            "target_hidden_roles": self.target_hidden_roles,
        }
        return hashlib.sha256(
            json.dumps(material, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()


def audit_seeds(n_seeds: int = 1000) -> dict[str, object]:
    """Run the v0.2 joint-identifiability invariant over many worlds."""
    failures = []
    fingerprints = set()
    for seed in range(n_seeds):
        world = SemanticWorldV02(WorldConfig(seed=seed))
        report = world.identifiability_report()
        if not report.valid:
            failures.append(report.to_dict())
        fingerprints.add(world.world_fingerprint())
    return {
        "schema_version": SemanticWorldV02.schema_version,
        "n_seeds": n_seeds,
        "n_valid": n_seeds - len(failures),
        "n_failures": len(failures),
        "n_unique_fingerprints": len(fingerprints),
        "failures": failures,
    }


def _main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    audit_parser = subparsers.add_parser("audit")
    audit_parser.add_argument("--seeds", type=int, default=1000)
    render_parser = subparsers.add_parser("render")
    render_parser.add_argument("--seed", type=int, default=0)
    render_parser.add_argument(
        "--skin", choices=("aligned", "neutral", "conflicting"), default="aligned"
    )
    args = parser.parse_args()
    if args.command == "audit":
        print(json.dumps(audit_seeds(args.seeds), indent=2, sort_keys=True))
        return
    world = SemanticWorldV02(WorldConfig(seed=args.seed))
    print("\n".join(world.render_lifetime(args.skin)))
    print("\nGOALS")
    print(json.dumps(world.render_goals(args.skin), indent=2))


if __name__ == "__main__":
    _main()
