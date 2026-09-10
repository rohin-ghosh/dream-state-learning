"""Counterfactual Confluence v0.3, a CPU-only causal-memory instrument.

The v0.2 confluence task admitted a target-local shortcut: the visible target
colors determined the held-out color.  V0.3 instead samples *collision twins*.
Two different hidden source subsets have the same exact passive three-role
signature, but react differently when one named source is blocked.  The only
public discriminator is a temporally separated valve intervention.

This module deliberately keeps hidden source subsets inside the generator and
out of every public episode, goal, and oracle input.  The public oracle follows
atomic edges only: valve->source, valve->target effect, animal->role evidence,
source->role contribution, target->passive baseline, and workshop recipes.
It is an acceptance instrument, not a model result.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from functools import reduce
import hashlib
import itertools
import json
from math import gcd
import random
from typing import Any, Iterable, Mapping, Sequence

from .model import WorldConfig
from .skins import all_skin_names, make_skin
from .v02 import RATIO_FOR_COLOR, RATIO_SURFACES, PigmentRatio, normalize_ratio
from .world import SemanticWorld


TARGET_IDS = ("cf_target_00", "cf_target_01", "cf_target_02")
VALVE_IDS = ("valve_00", "valve_01", "valve_02", "valve_03")

_TARGET_SURFACES = {
    "aligned": {
        TARGET_IDS[0]: "Confluenceland",
        TARGET_IDS[1]: "Braidedland",
        TARGET_IDS[2]: "Mosaicland",
    },
    "neutral": {
        TARGET_IDS[0]: "Ulvaren",
        TARGET_IDS[1]: "Nestrik",
        TARGET_IDS[2]: "Pavorel",
    },
    "conflicting": {
        TARGET_IDS[0]: "Stillland",
        TARGET_IDS[1]: "Singleland",
        TARGET_IDS[2]: "Plainland",
    },
}
_VALVE_SURFACES = {
    "aligned": {
        VALVE_IDS[0]: "copper valve",
        VALVE_IDS[1]: "silver valve",
        VALVE_IDS[2]: "amber valve",
        VALVE_IDS[3]: "violet valve",
    },
    "neutral": {
        VALVE_IDS[0]: "gate q7",
        VALVE_IDS[1]: "gate m4",
        VALVE_IDS[2]: "gate x2",
        VALVE_IDS[3]: "gate r8",
    },
    "conflicting": {
        VALVE_IDS[0]: "sealed valve",
        VALVE_IDS[1]: "isolated valve",
        VALVE_IDS[2]: "bypass valve",
        VALVE_IDS[3]: "direct valve",
    },
}


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _ratio_add(ratios: Iterable[PigmentRatio]) -> PigmentRatio:
    material = tuple(ratios)
    if not material:
        raise ValueError("cannot add an empty source set")
    return tuple(
        sum(ratio[channel] for ratio in material) for channel in range(3)
    )  # type: ignore[return-value]


def _ratio_subtract(left: PigmentRatio, right: PigmentRatio) -> PigmentRatio:
    result = tuple(left[index] - right[index] for index in range(3))
    if any(value < 0 for value in result) or not any(result):
        raise ValueError(f"invalid pigment subtraction: {left} - {right}")
    return result  # type: ignore[return-value]


def _is_primitive(signature: Sequence[PigmentRatio]) -> bool:
    return all(reduce(gcd, ratio) == 1 for ratio in signature)


def source_ratio_for_role(
    base: SemanticWorld, role: int, source_id: str
) -> PigmentRatio:
    """Return the exact source contribution for one latent role."""
    return RATIO_FOR_COLOR[base.source_color_for_role(role, source_id)]


def exact_passive_signature(
    base: SemanticWorld, source_subset: Sequence[str]
) -> tuple[PigmentRatio, PigmentRatio, PigmentRatio]:
    """Exact unnormalized three-role signature of a hidden source subset."""
    if not source_subset:
        raise ValueError("a passive signature needs at least one source")
    return tuple(
        _ratio_add(source_ratio_for_role(base, role, source) for source in source_subset)
        for role in range(3)
    )  # type: ignore[return-value]


def blocked_outcome(
    base: SemanticWorld,
    source_subset: Sequence[str],
    blocked_source: str,
    role: int,
) -> PigmentRatio:
    """Normalized role outcome after a named source is closed."""
    remaining = tuple(source for source in source_subset if source != blocked_source)
    return normalize_ratio(
        _ratio_add(source_ratio_for_role(base, role, source) for source in remaining)
    )


@dataclass(frozen=True)
class CollisionClass:
    id: str
    signature: tuple[PigmentRatio, PigmentRatio, PigmentRatio]
    source_subsets: tuple[tuple[str, ...], ...]


@dataclass(frozen=True)
class CollisionChoice:
    collision_class_id: str
    signature: tuple[PigmentRatio, PigmentRatio, PigmentRatio]
    source_subset_0: tuple[str, ...]
    source_subset_1: tuple[str, ...]
    discriminator_source: str
    blocked_outcomes_0: tuple[PigmentRatio, PigmentRatio, PigmentRatio]
    blocked_outcomes_1: tuple[PigmentRatio, PigmentRatio, PigmentRatio]

    @property
    def primitive_passive_signature(self) -> bool:
        return _is_primitive(self.signature)

    def actual_subset(self, latent_bit: int) -> tuple[str, ...]:
        if latent_bit == 0:
            return self.source_subset_0
        if latent_bit == 1:
            return self.source_subset_1
        raise ValueError("latent_bit must be 0 or 1")

    def outcome_for(self, latent_bit: int, role: int) -> PigmentRatio:
        if role not in (0, 1, 2):
            raise ValueError("role must be 0, 1, or 2")
        if latent_bit == 0:
            return self.blocked_outcomes_0[role]
        if latent_bit == 1:
            return self.blocked_outcomes_1[role]
        raise ValueError("latent_bit must be 0 or 1")


@dataclass(frozen=True)
class CollisionCatalog:
    classes: tuple[CollisionClass, ...]
    choices: tuple[CollisionChoice, ...]

    @property
    def primitive_choices(self) -> tuple[CollisionChoice, ...]:
        # Retained as an audit statistic.  V0.3 samples the full catalog and
        # exposes exact passive gauge amounts, so non-primitive signatures do
        # not lose the magnitude needed for causal subtraction.
        return tuple(choice for choice in self.choices if choice.primitive_passive_signature)


def enumerate_collision_catalog(base: SemanticWorld) -> CollisionCatalog:
    """Regenerate exact collision classes and discriminator choices.

    No count is hard-coded here.  The default six-source construction happens
    to yield 11 classes and 111 choices; tests audit those design facts.
    """
    hypotheses = tuple(
        subset
        for size in range(2, len(base.source_land_ids) + 1)
        for subset in itertools.combinations(base.source_land_ids, size)
    )
    by_signature: dict[
        tuple[PigmentRatio, PigmentRatio, PigmentRatio], list[tuple[str, ...]]
    ] = defaultdict(list)
    for subset in hypotheses:
        by_signature[exact_passive_signature(base, subset)].append(tuple(subset))

    classes: list[CollisionClass] = []
    choices: list[CollisionChoice] = []
    for signature, group_list in sorted(by_signature.items()):
        if len(group_list) < 2:
            continue
        group = tuple(sorted(group_list))
        class_id = f"collision_{_sha256(signature)[:12]}"
        classes.append(CollisionClass(class_id, signature, group))
        for left_index, source_subset_0 in enumerate(group):
            for source_subset_1 in group[left_index + 1 :]:
                for discriminator_source in sorted(
                    set(source_subset_0) ^ set(source_subset_1)
                ):
                    outcomes_0 = tuple(
                        blocked_outcome(
                            base, source_subset_0, discriminator_source, role
                        )
                        for role in range(3)
                    )
                    outcomes_1 = tuple(
                        blocked_outcome(
                            base, source_subset_1, discriminator_source, role
                        )
                        for role in range(3)
                    )
                    if not all(
                        outcomes_0[role] != outcomes_1[role] for role in range(3)
                    ):
                        continue
                    choices.append(
                        CollisionChoice(
                            collision_class_id=class_id,
                            signature=signature,
                            source_subset_0=source_subset_0,
                            source_subset_1=source_subset_1,
                            discriminator_source=discriminator_source,
                            blocked_outcomes_0=outcomes_0,  # type: ignore[arg-type]
                            blocked_outcomes_1=outcomes_1,  # type: ignore[arg-type]
                        )
                    )
    return CollisionCatalog(tuple(classes), tuple(choices))


@dataclass(frozen=True)
class AtomicEpisode:
    """One public fact/event per episode; payload is public structured data."""

    id: str
    episode_id: str
    phase: str
    kind: str
    payload: Mapping[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "episode_id": self.episode_id,
            "phase": self.phase,
            "kind": self.kind,
            "payload": dict(self.payload),
        }


@dataclass(frozen=True)
class CounterfactualGoal:
    id: str
    animal_id: str
    target_id: str
    blocked_source_id: str
    answer_ratio: PigmentRatio
    role: int


@dataclass(frozen=True)
class PublicCounterfactualGoal:
    """Goal fields available to the agent; deliberately excludes truth/role."""

    id: str
    animal_id: str
    target_id: str
    blocked_source_id: str


@dataclass(frozen=True)
class OracleResult:
    ratio: PigmentRatio
    label: str
    role_anchor_id: str
    intervention_effect: str
    evidence_episode_ids: tuple[str, ...]


def _payload(episode: AtomicEpisode, key: str) -> Any:
    if key not in episode.payload:
        raise KeyError(f"{episode.id} is missing public field {key}")
    return episode.payload[key]


def parent_free_oracle(
    episodes: Sequence[AtomicEpisode], goal: PublicCounterfactualGoal
) -> OracleResult:
    """Solve solely from public atomic edges, without a source-subset object."""
    workshop_by_label: dict[str, PigmentRatio] = {}
    workshop_episode: dict[str, str] = {}
    for episode in episodes:
        if episode.kind != "workshop_recipe":
            continue
        label = str(_payload(episode, "label"))
        ratio = tuple(_payload(episode, "ratio"))
        if len(ratio) != 3:
            raise ValueError("workshop ratio must have three channels")
        typed_ratio: PigmentRatio = ratio  # type: ignore[assignment]
        if label in workshop_by_label and workshop_by_label[label] != typed_ratio:
            raise ValueError(f"ambiguous workshop label {label}")
        workshop_by_label[label] = typed_ratio
        workshop_episode[label] = episode.episode_id

    routes = [
        episode
        for episode in episodes
        if episode.kind == "valve_route"
        and _payload(episode, "source_id") == goal.blocked_source_id
    ]
    effect_pairs = []
    for route in routes:
        valve_id = _payload(route, "valve_id")
        for effect in episodes:
            if (
                effect.kind == "intervention_effect"
                and _payload(effect, "valve_id") == valve_id
                and _payload(effect, "target_id") == goal.target_id
            ):
                effect_pairs.append((route, effect))
    if len(effect_pairs) != 1:
        raise ValueError("public valve/source/target path is not unique")
    route_episode, effect_episode = effect_pairs[0]
    effect_name = str(_payload(effect_episode, "effect"))
    if effect_name not in ("CHANGE", "STABLE"):
        raise ValueError(f"unknown public intervention effect {effect_name}")

    anchor_rows = [
        episode for episode in episodes if episode.kind == "source_anchor_color"
    ]
    animal_rows = [
        episode
        for episode in episodes
        if episode.kind == "animal_source_color"
        and _payload(episode, "animal_id") == goal.animal_id
    ]
    if len(animal_rows) < 2:
        raise ValueError("goal animal lacks dispersed role evidence")
    anchor_ids = sorted({_payload(row, "anchor_id") for row in anchor_rows})
    matching_anchors = []
    role_evidence_ids = [row.episode_id for row in animal_rows]
    for anchor_id in anchor_ids:
        matches = True
        for animal_row in animal_rows:
            source_id = _payload(animal_row, "source_id")
            candidates = [
                row
                for row in anchor_rows
                if _payload(row, "anchor_id") == anchor_id
                and _payload(row, "source_id") == source_id
            ]
            if len(candidates) != 1:
                raise ValueError("anchor/source calibration is incomplete")
            role_evidence_ids.append(candidates[0].episode_id)
            if _payload(candidates[0], "label") != _payload(animal_row, "label"):
                matches = False
        if matches:
            matching_anchors.append(anchor_id)
    if len(matching_anchors) != 1:
        raise ValueError("goal animal role is not uniquely supported")
    role_anchor_id = str(matching_anchors[0])

    baseline_rows = [
        episode
        for episode in episodes
        if episode.kind == "target_passive_baseline"
        and _payload(episode, "target_id") == goal.target_id
        and _payload(episode, "anchor_id") == role_anchor_id
    ]
    contribution_rows = [
        episode
        for episode in anchor_rows
        if _payload(episode, "source_id") == goal.blocked_source_id
        and _payload(episode, "anchor_id") == role_anchor_id
    ]
    if len(baseline_rows) != 1 or len(contribution_rows) != 1:
        raise ValueError("public baseline or source contribution is not unique")
    baseline_episode = baseline_rows[0]
    contribution_episode = contribution_rows[0]
    baseline_label = str(_payload(baseline_episode, "label"))
    contribution_label = str(_payload(contribution_episode, "label"))
    try:
        # Passive target episodes publicly report an exact three-channel gauge
        # reading.  This preserves subtraction magnitude for collision classes
        # such as (2,2,2), whose categorical color alone would normalize to
        # (1,1,1) and erase how much material was present.
        baseline_ratio = tuple(_payload(baseline_episode, "ratio"))
        if len(baseline_ratio) != 3:
            raise ValueError("passive gauge ratio must have three channels")
        baseline_ratio = baseline_ratio  # type: ignore[assignment]
        contribution_ratio = workshop_by_label[contribution_label]
    except KeyError as exc:
        raise ValueError(f"missing public workshop recipe for {exc.args[0]}") from exc
    if workshop_by_label.get(baseline_label) != normalize_ratio(baseline_ratio):
        raise ValueError("passive gauge label disagrees with public workshop")

    if effect_name == "CHANGE":
        answer_ratio = normalize_ratio(
            _ratio_subtract(baseline_ratio, contribution_ratio)
        )
    else:
        answer_ratio = normalize_ratio(baseline_ratio)
    labels = [label for label, ratio in workshop_by_label.items() if ratio == answer_ratio]
    if len(labels) != 1:
        raise ValueError("counterfactual outcome has no unique public workshop label")
    answer_label = labels[0]
    evidence = {
        route_episode.episode_id,
        effect_episode.episode_id,
        baseline_episode.episode_id,
        contribution_episode.episode_id,
        workshop_episode[baseline_label],
        workshop_episode[contribution_label],
        workshop_episode[answer_label],
        *role_evidence_ids,
    }
    return OracleResult(
        ratio=answer_ratio,
        label=answer_label,
        role_anchor_id=role_anchor_id,
        intervention_effect=effect_name,
        evidence_episode_ids=tuple(sorted(evidence)),
    )


def bridge_removed_candidates(
    episodes: Sequence[AtomicEpisode], goal: PublicCounterfactualGoal
) -> tuple[OracleResult, ...]:
    """Enumerate answers when valve/source routes are deliberately withheld.

    This is the CPU form of the mandatory bridge-removed baseline.  It removes
    every route edge, then treats each observed target-valve effect in turn as
    the unknown route for the goal source.  A valid task must leave at least
    two distinct answers, including the truth, until the lived route edge is
    restored.
    """
    route_free = tuple(episode for episode in episodes if episode.kind != "valve_route")
    target_effects = tuple(
        episode
        for episode in route_free
        if episode.kind == "intervention_effect"
        and _payload(episode, "target_id") == goal.target_id
    )
    results: dict[PigmentRatio, OracleResult] = {}
    for index, effect in enumerate(target_effects):
        hypothetical_route = AtomicEpisode(
            id=f"bridge_removed_hypothesis_{index:03d}",
            episode_id=f"bridge_removed_hypothesis_{index:03d}",
            phase="analysis_only",
            kind="valve_route",
            payload={
                "valve_id": _payload(effect, "valve_id"),
                "source_id": goal.blocked_source_id,
            },
        )
        try:
            result = parent_free_oracle(
                (*route_free, hypothetical_route), goal
            )
        except (ValueError, KeyError):
            continue
        results[result.ratio] = result
    return tuple(results[ratio] for ratio in sorted(results))


class CounterfactualConfluenceV03:
    """One side of a paired, deterministic Counterfactual Confluence world."""

    schema_version = "lands-v0.3-counterfactual-confluence"

    def __init__(
        self,
        config: WorldConfig | None = None,
        *,
        latent_bit: int | None = None,
    ):
        self.config = config or WorldConfig()
        self.base = SemanticWorld(self.config)
        self.animal_ids = self.base.animal_ids
        self.source_land_ids = self.base.source_land_ids
        self.anchor_animals = self.base.anchor_animals
        self.eval_animals = self.base.eval_animals
        self.latent_bit = self.config.seed & 1 if latent_bit is None else latent_bit
        if self.latent_bit not in (0, 1):
            raise ValueError("latent_bit must be 0 or 1")

        self.catalog = enumerate_collision_catalog(self.base)
        if not self.catalog.choices:
            raise RuntimeError("no collision choices exist")
        # Cycle collision classes exactly (within one pair) rather than
        # sampling in proportion to their unequal numbers of concrete choices.
        # The choice within a class then varies independently across seeds.
        collision_class_ids = tuple(
            sorted({choice.collision_class_id for choice in self.catalog.choices})
        )
        self.goal_role = self.config.seed % 3
        desired_class = collision_class_ids[
            self.config.seed % len(collision_class_ids)
        ]
        candidate_pool = tuple(
            choice
            for choice in self.catalog.choices
            if choice.collision_class_id == desired_class
        )
        if not candidate_pool:
            raise RuntimeError(f"no collision choice for class {desired_class}")
        # Two collision classes necessarily contribute one brown passive side.
        # Elsewhere avoid adding an unnecessary brown change-side answer when
        # another discriminator in the same class and role is available.  This
        # preserves class/role stratification while keeping majority accuracy
        # below ten percent rather than letting a generic brown guess dominate.
        brown = RATIO_FOR_COLOR["brown"]
        non_brown = tuple(
            choice
            for choice in candidate_pool
            if choice.blocked_outcomes_0[self.goal_role] != brown
            and choice.blocked_outcomes_1[self.goal_role] != brown
        )
        if non_brown:
            candidate_pool = non_brown
        choice_index = (self.config.seed // len(collision_class_ids)) % len(candidate_pool)
        self.choice = candidate_pool[choice_index]
        left_only = sorted(
            set(self.choice.source_subset_0) - set(self.choice.source_subset_1)
        )
        right_only = sorted(
            set(self.choice.source_subset_1) - set(self.choice.source_subset_0)
        )
        if not left_only or not right_only:
            raise RuntimeError("collision pair lacks a bidirectional symmetric difference")
        if self.choice.discriminator_source in left_only:
            mirror_candidates = right_only
        else:
            mirror_candidates = left_only
        self.mirror_source = mirror_candidates[
            (self.config.seed // len(collision_class_ids)) % len(mirror_candidates)
        ]
        self.goal_valve_id = VALVE_IDS[self.config.seed % 2]
        self.mirror_valve_id = VALVE_IDS[1 - (self.config.seed % 2)]
        self.actual_source_subset = self.choice.actual_subset(self.latent_bit)
        self.intervention_effect = (
            "CHANGE"
            if self.choice.discriminator_source in self.actual_source_subset
            else "STABLE"
        )
        # Cross collision class and goal role deterministically.  The selected
        # internal eval animal is rendered through one fixed public animal slot
        # (a bijective swap, not an alias collision), preventing rare surface
        # cells from making an intervention episode answer-sufficient while
        # retaining exact role balance.
        self.goal_animal = next(
            animal
            for animal in self.eval_animals
            if self.base.animal_roles[animal] == self.goal_role
        )
        self._goal_surface_slot = self.animal_ids[-1]
        self.goal = CounterfactualGoal(
            id="v03_goal_0000",
            animal_id=self.goal_animal,
            target_id=TARGET_IDS[0],
            blocked_source_id=self.choice.discriminator_source,
            answer_ratio=self.choice.outcome_for(self.latent_bit, self.goal_role),
            role=self.goal_role,
        )

        tuple_material = {
            "source_role_table": {
                source: [
                    self.base.source_color_for_role(role, source) for role in range(3)
                ]
                for source in self.source_land_ids
            },
            "collision_class_id": self.choice.collision_class_id,
            "source_subset_0": self.choice.source_subset_0,
            "source_subset_1": self.choice.source_subset_1,
            "discriminator_source": self.choice.discriminator_source,
            "goal_role": self.goal_role,
            "goal_animal": self.goal_animal,
        }
        self.latent_tuple_id = _sha256(tuple_material)
        self.split = "heldout" if int(self.latent_tuple_id[:8], 16) % 5 == 0 else "development"

        self._distractors = self._select_distractors()
        self._ratio_labels = self._build_ratio_labels()
        self.episodes = self._build_episodes()
        self._validate_local()

    def _select_distractors(self) -> tuple[tuple[CollisionChoice, int], ...]:
        alternatives = tuple(
            choice
            for choice in self.catalog.choices
            if choice != self.choice
            and choice.discriminator_source != self.choice.discriminator_source
        )
        rng = random.Random(self.config.seed ^ 0xC0F1_0303)
        selected = rng.sample(list(alternatives), 2)
        # Independent of the main latent bit, so paired public distractors are
        # byte-identical and cannot leak which twin was sampled.
        return tuple((choice, rng.randrange(2)) for choice in selected)

    def _needed_ratios(self) -> tuple[PigmentRatio, ...]:
        ratios = set(RATIO_FOR_COLOR.values())
        ratios.update(self.choice.signature)
        ratios.update(self.choice.blocked_outcomes_0)
        ratios.update(self.choice.blocked_outcomes_1)
        for choice, side in self._distractors:
            ratios.update(choice.signature)
            ratios.update(
                choice.blocked_outcomes_0 if side == 0 else choice.blocked_outcomes_1
            )
        return tuple(sorted({normalize_ratio(ratio) for ratio in ratios}))

    def _build_ratio_labels(self) -> dict[str, dict[PigmentRatio, str]]:
        ratios = self._needed_ratios()
        base_ratio_to_color = {ratio: color for color, ratio in RATIO_FOR_COLOR.items()}
        rich = tuple(ratio for ratio in ratios if ratio not in base_ratio_to_color)
        aligned_rich = {
            ratio: RATIO_SURFACES.get(ratio, f"mixture-{index:02d}")
            for index, ratio in enumerate(rich)
        }
        labels: dict[str, dict[PigmentRatio, str]] = {}
        for skin_name in all_skin_names():
            skin = make_skin(skin_name, self.animal_ids, self.source_land_ids)
            mapping = {
                ratio: skin.color(color) for ratio, color in base_ratio_to_color.items()
            }
            if skin_name == "aligned":
                mapping.update(aligned_rich)
            elif skin_name == "neutral":
                mapping.update({ratio: f"vexa{index:02d}" for index, ratio in enumerate(rich)})
            else:
                shifted = rich[1:] + rich[:1] if len(rich) > 1 else rich
                mapping.update(
                    {ratio: aligned_rich[shifted[index]] for index, ratio in enumerate(rich)}
                )
            if len(set(mapping.values())) != len(mapping):
                raise RuntimeError(f"non-bijective ratio labels in skin {skin_name}")
            labels[skin_name] = mapping
        return labels

    def ratio_surface(self, ratio: PigmentRatio, skin_name: str) -> str:
        normalized = normalize_ratio(ratio)
        try:
            return self._ratio_labels[skin_name][normalized]
        except KeyError as exc:
            raise KeyError(f"ratio {normalized} is absent from {skin_name} workshop") from exc

    def animal_surface(self, animal_id: str, skin_name: str) -> str:
        """Render a bijective animal-name swap that fixes the goal surface."""
        skin = make_skin(skin_name, self.animal_ids, self.source_land_ids)
        if animal_id == self.goal_animal:
            return skin.animal(self._goal_surface_slot)
        if animal_id == self._goal_surface_slot:
            return skin.animal(self.goal_animal)
        return skin.animal(animal_id)

    def target_surface(self, target_id: str, skin_name: str) -> str:
        return _TARGET_SURFACES[skin_name][target_id]

    def valve_surface(self, valve_id: str, skin_name: str) -> str:
        return _VALVE_SURFACES[skin_name][valve_id]

    def _episode(
        self, kind: str, phase: str, **payload: Any
    ) -> tuple[str, str, dict[str, Any]]:
        return kind, phase, payload

    def _build_episodes(self) -> tuple[AtomicEpisode, ...]:
        records: list[tuple[str, str, dict[str, Any]]] = []
        main_route = self._episode(
            "valve_route",
            "early_route",
            valve_id=self.goal_valve_id,
            source_id=self.choice.discriminator_source,
        )
        main_effect = self._episode(
            "intervention_effect",
            "late_intervention",
            valve_id=self.goal_valve_id,
            target_id=TARGET_IDS[0],
            effect=self.intervention_effect,
        )
        mirror_effect_name = (
            "CHANGE" if self.mirror_source in self.actual_source_subset else "STABLE"
        )
        mirror_route = self._episode(
            "valve_route",
            "early_route_control",
            valve_id=self.mirror_valve_id,
            source_id=self.mirror_source,
        )
        mirror_effect = self._episode(
            "intervention_effect",
            "late_intervention_control",
            valve_id=self.mirror_valve_id,
            target_id=TARGET_IDS[0],
            effect=mirror_effect_name,
        )

        early_routes: list[tuple[str, str, dict[str, Any]]] = [
            main_route,
            mirror_route,
        ]
        filler: list[tuple[str, str, dict[str, Any]]] = []
        for role, anchor_id in enumerate(self.anchor_animals):
            for source_id in self.source_land_ids:
                ratio = source_ratio_for_role(self.base, role, source_id)
                filler.append(
                    self._episode(
                        "source_anchor_color",
                        "source_experience",
                        anchor_id=anchor_id,
                        source_id=source_id,
                        label=self.ratio_surface(ratio, "aligned"),
                        ratio=ratio,
                    )
                )

        sampled_lifetime = self.base.sample_lifetime()
        animal_observations = tuple(
            observation
            for observation in sampled_lifetime.observations
            if observation.animal_id == self.goal_animal
            and observation.land_id in self.source_land_ids
            and not observation.repeated
        )
        if len(animal_observations) != 2:
            raise RuntimeError("goal animal must have exactly two sparse source visits")
        for observation in animal_observations:
            ratio = RATIO_FOR_COLOR[observation.color_id]
            filler.append(
                self._episode(
                    "animal_source_color",
                    "role_experience",
                    animal_id=self.goal_animal,
                    source_id=observation.land_id,
                    label=self.ratio_surface(ratio, "aligned"),
                    ratio=ratio,
                )
            )

        for role, anchor_id in enumerate(self.anchor_animals):
            ratio = self.choice.signature[role]
            filler.append(
                self._episode(
                    "target_passive_baseline",
                    "passive_target",
                    target_id=TARGET_IDS[0],
                    anchor_id=anchor_id,
                        label=self.ratio_surface(normalize_ratio(ratio), "aligned"),
                    ratio=ratio,
                )
            )

        for distractor_index, (choice, side) in enumerate(self._distractors, start=1):
            target_id = TARGET_IDS[distractor_index]
            valve_id = VALVE_IDS[distractor_index + 1]
            actual = choice.actual_subset(side)
            effect = "CHANGE" if choice.discriminator_source in actual else "STABLE"
            early_routes.append(
                self._episode(
                    "valve_route",
                    "distractor_route",
                    valve_id=valve_id,
                    source_id=choice.discriminator_source,
                )
            )
            filler.extend(
                (
                    self._episode(
                        "target_passive_baseline",
                        "distractor_target",
                        target_id=target_id,
                        anchor_id=self.anchor_animals[distractor_index % 3],
                        label=self.ratio_surface(
                            normalize_ratio(choice.signature[distractor_index % 3]),
                            "aligned",
                        ),
                        ratio=choice.signature[distractor_index % 3],
                    ),
                    self._episode(
                        "intervention_effect",
                        "distractor_intervention",
                        valve_id=valve_id,
                        target_id=target_id,
                        effect=effect,
                    ),
                )
            )

        for ratio in self._needed_ratios():
            filler.append(
                self._episode(
                    "workshop_recipe",
                    "workshop",
                    ratio=ratio,
                    label=self.ratio_surface(ratio, "aligned"),
                )
            )

        # Replace the old repeated-land buffer with useful but shuffled atomic
        # experiences.  Pin the causal bridge first and its outcome last so no
        # allowed local context can contain the complete proof.
        rng = random.Random(self.config.seed ^ 0xE913_0303)
        rng.shuffle(early_routes)
        rng.shuffle(filler)
        late_effects = [main_effect, mirror_effect]
        rng.shuffle(late_effects)
        ordered = [*early_routes, *filler, *late_effects]
        episodes = []
        for index, (kind, phase, payload) in enumerate(ordered):
            # Store canonical aligned labels in the structured public record;
            # renderers substitute the selected skin using the public ratio.
            episodes.append(
                AtomicEpisode(
                    id=f"v03_edge_{index:04d}",
                    episode_id=f"v03_episode_{index:04d}",
                    phase=phase,
                    kind=kind,
                    payload=payload,
                )
            )
        return tuple(episodes)

    def _label_for_episode(self, episode: AtomicEpisode, skin_name: str) -> str:
        ratio = tuple(_payload(episode, "ratio"))
        return self.ratio_surface(ratio, skin_name)  # type: ignore[arg-type]

    def render_episode(self, episode: AtomicEpisode, skin_name: str) -> str:
        skin = make_skin(skin_name, self.animal_ids, self.source_land_ids)
        prefix = f"[{episode.id} | {episode.episode_id}]"
        if episode.kind == "valve_route":
            valve = self.valve_surface(str(_payload(episode, "valve_id")), skin_name)
            source = skin.land(str(_payload(episode, "source_id")))
            if skin_name == "neutral":
                return f"{prefix} A traced conduit shows {valve} routes the stream from zone {source}."
            return f"{prefix} A traced pipe shows the {valve} routes the stream from {source}."
        if episode.kind == "intervention_effect":
            valve = self.valve_surface(str(_payload(episode, "valve_id")), skin_name)
            target = self.target_surface(str(_payload(episode, "target_id")), skin_name)
            effect = _payload(episode, "effect")
            if skin_name == "neutral":
                return f"{prefix} Closing {valve} made zone {target}'s measured state {effect}."
            return f"{prefix} When you closed the {valve}, the mixture in {target} was {effect}."
        if episode.kind == "source_anchor_color":
            animal = self.animal_surface(str(_payload(episode, "anchor_id")), skin_name)
            source = skin.land(str(_payload(episode, "source_id")))
            label = self._label_for_episode(episode, skin_name)
            if skin_name == "neutral":
                return f"{prefix} In zone {source}, entity {animal} has state-token {label}."
            return f"{prefix} In {source}, the {animal}'s coat is {label}."
        if episode.kind == "animal_source_color":
            animal = self.animal_surface(str(_payload(episode, "animal_id")), skin_name)
            source = skin.land(str(_payload(episode, "source_id")))
            label = self._label_for_episode(episode, skin_name)
            if skin_name == "neutral":
                return f"{prefix} In zone {source}, entity {animal} has state-token {label}."
            return f"{prefix} In {source}, the {animal}'s coat is {label}."
        if episode.kind == "target_passive_baseline":
            animal = self.animal_surface(str(_payload(episode, "anchor_id")), skin_name)
            target = self.target_surface(str(_payload(episode, "target_id")), skin_name)
            label = self._label_for_episode(episode, skin_name)
            ratio = tuple(_payload(episode, "ratio"))
            pigments = tuple(skin.color(color) for color in ("red", "yellow", "blue"))
            gauge = ", ".join(
                f"{count} {pigment}"
                for count, pigment in zip(ratio, pigments)
                if count
            )
            if skin_name == "neutral":
                return (
                    f"{prefix} With all valves open, the gauge for entity {animal} "
                    f"in zone {target} reads {gauge}; its state-token is {label}."
                )
            return (
                f"{prefix} With every valve open, the gauge for the {animal} in "
                f"{target} reads {gauge}; its color is {label}."
            )
        if episode.kind == "workshop_recipe":
            ratio = tuple(_payload(episode, "ratio"))
            label = self._label_for_episode(episode, skin_name)
            pigments = tuple(skin.color(color) for color in ("red", "yellow", "blue"))
            ingredients = ", ".join(
                f"{count} part{'s' if count != 1 else ''} {pigment}"
                for count, pigment in zip(ratio, pigments)
                if count
            )
            if skin_name == "neutral":
                return f"{prefix} A calibration mixture containing {ingredients} is assigned state-token {label}."
            return f"{prefix} The workshop labels a mixture of {ingredients} as {label}."
        raise ValueError(f"unknown v0.3 episode kind {episode.kind}")

    def render_lifetime(self, skin_name: str = "aligned") -> tuple[str, ...]:
        if skin_name not in all_skin_names():
            raise ValueError(f"unknown skin {skin_name}")
        return tuple(self.render_episode(episode, skin_name) for episode in self.episodes)

    def render_goal(
        self, skin_name: str = "aligned", *, include_answer: bool = False
    ) -> dict[str, str]:
        skin = make_skin(skin_name, self.animal_ids, self.source_land_ids)
        animal = self.animal_surface(self.goal.animal_id, skin_name)
        source = skin.land(self.goal.blocked_source_id)
        target = self.target_surface(self.goal.target_id, skin_name)
        if skin_name == "neutral":
            question = (
                f"If the stream from zone {source} is closed, what state-token will "
                f"entity {animal} settle into in zone {target}? Answer with exactly "
                "one state-token."
            )
        else:
            question = (
                f"If the stream from {source} is closed, what color will the "
                f"{animal} settle into in {target}? Answer with exactly one color."
            )
        result = {"goal_id": self.goal.id, "question": question}
        if include_answer:
            result["answer"] = self.ratio_surface(self.goal.answer_ratio, skin_name)
        return result

    def public_episodes(self, skin_name: str = "aligned") -> tuple[AtomicEpisode, ...]:
        """Return public structured edges with skin-correct labels and no parents."""
        result = []
        for episode in self.episodes:
            payload = dict(episode.payload)
            if "ratio" in payload:
                payload["label"] = self.ratio_surface(tuple(payload["ratio"]), skin_name)
                # Only workshop text exposes pigment quantities.  Other lived
                # episodes expose an opaque outcome label, so their structured
                # public edge must not smuggle the decoded ratio to the oracle.
                if episode.kind not in ("workshop_recipe", "target_passive_baseline"):
                    del payload["ratio"]
            result.append(
                AtomicEpisode(
                    id=episode.id,
                    episode_id=episode.episode_id,
                    phase=episode.phase,
                    kind=episode.kind,
                    payload=payload,
                )
            )
        return tuple(result)

    def public_goal(self) -> PublicCounterfactualGoal:
        return PublicCounterfactualGoal(
            id=self.goal.id,
            animal_id=self.goal.animal_id,
            target_id=self.goal.target_id,
            blocked_source_id=self.goal.blocked_source_id,
        )

    def public_export(self, skin_name: str = "aligned") -> dict[str, Any]:
        goal = self.render_goal(skin_name, include_answer=False)
        return {
            "schema_version": self.schema_version,
            "skin": skin_name,
            "episodes": [
                {
                    "id": episode.id,
                    "episode_id": episode.episode_id,
                    "phase": episode.phase,
                    "kind": episode.kind,
                    "text": self.render_episode(episode, skin_name),
                }
                for episode in self.episodes
            ],
            "goal": goal,
        }

    def split_manifest(self) -> dict[str, str]:
        """Dataset-builder metadata kept outside the model-visible export."""
        return {"latent_tuple_id": self.latent_tuple_id, "split": self.split}

    def passive_twin_hash(self, skin_name: str = "aligned") -> str:
        target_rows = [
            self.render_episode(episode, skin_name)
            for episode in self.episodes
            if episode.kind == "target_passive_baseline"
            and _payload(episode, "target_id") == self.goal.target_id
        ]
        return _sha256(
            {"target_rows": target_rows, "goal": self.render_goal(skin_name)}
        )

    def world_fingerprint(self) -> str:
        return _sha256(
            {
                "schema_version": self.schema_version,
                "config": self.config.to_dict(),
                "latent_tuple_id": self.latent_tuple_id,
                "latent_bit": self.latent_bit,
                "effect": self.intervention_effect,
                "answer": self.goal.answer_ratio,
                "episodes": [episode.to_dict() for episode in self.episodes],
            }
        )

    def oracle(self, skin_name: str = "aligned") -> OracleResult:
        return parent_free_oracle(self.public_episodes(skin_name), self.public_goal())

    def proof_episode_positions(self, skin_name: str = "aligned") -> tuple[int, ...]:
        oracle_result = self.oracle(skin_name)
        by_episode = {
            episode.episode_id: index for index, episode in enumerate(self.episodes)
        }
        return tuple(sorted(by_episode[episode_id] for episode_id in oracle_result.evidence_episode_ids))

    def _validate_local(self) -> None:
        if self.choice.source_subset_0 == self.choice.source_subset_1:
            raise RuntimeError("collision twins are identical")
        if exact_passive_signature(self.base, self.choice.source_subset_0) != self.choice.signature:
            raise RuntimeError("left twin does not match collision signature")
        if exact_passive_signature(self.base, self.choice.source_subset_1) != self.choice.signature:
            raise RuntimeError("right twin does not match collision signature")
        if not all(
            self.choice.blocked_outcomes_0[role] != self.choice.blocked_outcomes_1[role]
            for role in range(3)
        ):
            raise RuntimeError("counterfactual twins are not separated for every role")
        if any("parent" in episode.kind.lower() for episode in self.episodes):
            raise RuntimeError("public episode kind exposes a parent representation")
        for episode in self.episodes:
            if len(episode.payload) != len(set(episode.payload)):
                raise RuntimeError("malformed atomic payload")
            if any(key in episode.payload for key in ("parents", "source_subset", "latent_bit")):
                raise RuntimeError("public episode exposes hidden factorization")
        if self.oracle("aligned").ratio != self.goal.answer_ratio:
            raise RuntimeError("public-only oracle failed")
        bridge_candidates = bridge_removed_candidates(
            self.public_episodes("aligned"), self.public_goal()
        )
        if (
            len({candidate.ratio for candidate in bridge_candidates}) < 2
            or self.goal.answer_ratio
            not in {candidate.ratio for candidate in bridge_candidates}
        ):
            raise RuntimeError("valve/source bridge is not causally necessary")
        positions = self.proof_episode_positions("aligned")
        gaps = tuple(right - left for left, right in zip(positions, positions[1:]))
        if len(positions) < 3 or sum(gap > 1 for gap in gaps) < 2:
            raise RuntimeError("proof does not span distinct atomic episodes")
        if max(positions) - min(positions) < self.config.context_observation_budget:
            raise RuntimeError("proof fits inside the forbidden observation window")


def _episode_surface_feature(world: CounterfactualConfluenceV03, episode: AtomicEpisode, skin: str) -> tuple[str, str]:
    # Drop record IDs so ambiguity measures semantic content, not bookkeeping.
    rendered = world.render_episode(episode, skin)
    body = rendered.split("] ", 1)[1]
    return episode.kind, body


def audit_paired_worlds(n_pairs: int = 1000) -> dict[str, Any]:
    """Audit mandatory invariants over deterministic paired latent worlds."""
    if n_pairs < 1:
        raise ValueError("n_pairs must be positive")
    failures: list[dict[str, Any]] = []
    effects: Counter[str] = Counter()
    roles: Counter[int] = Counter()
    classes: Counter[str] = Counter()
    discriminator_sources: Counter[str] = Counter()
    answer_ratios: Counter[PigmentRatio] = Counter()
    splits: Counter[str] = Counter()
    single_episode_answers: dict[tuple[str, str, str], set[str]] = defaultdict(set)
    surface_goal_answers: dict[tuple[str, str], set[str]] = defaultdict(set)

    for seed in range(n_pairs):
        config = WorldConfig(seed=seed)
        twins = (
            CounterfactualConfluenceV03(config, latent_bit=0),
            CounterfactualConfluenceV03(config, latent_bit=1),
        )
        left, right = twins
        local_errors = []
        if left.choice.signature != right.choice.signature or left.choice.source_subset_0 == left.choice.source_subset_1:
            local_errors.append("collision")
        if not all(
            left.choice.blocked_outcomes_0[role] != left.choice.blocked_outcomes_1[role]
            for role in range(3)
        ):
            local_errors.append("counterfactual_separation")
        for skin in all_skin_names():
            if left.passive_twin_hash(skin) != right.passive_twin_hash(skin):
                local_errors.append(f"passive_twin_hash:{skin}")
            if left.render_goal(skin) != right.render_goal(skin):
                local_errors.append(f"goal_twin_identity:{skin}")
        left_rows = tuple(
            episode.payload["ratio"]
            for episode in left.episodes
            if episode.kind == "target_passive_baseline"
            and episode.payload["target_id"] == TARGET_IDS[0]
        )
        right_rows = tuple(
            episode.payload["ratio"]
            for episode in right.episodes
            if episode.kind == "target_passive_baseline"
            and episode.payload["target_id"] == TARGET_IDS[0]
        )
        if left_rows != right_rows or left.goal.answer_ratio == right.goal.answer_ratio:
            local_errors.append("signature_ambiguity")
        for count in (1, 2, 3):
            if left_rows[:count] != right_rows[:count] or left.goal.answer_ratio == right.goal.answer_ratio:
                local_errors.append(f"visible_{count}_row_ambiguity")
        if left.latent_tuple_id != right.latent_tuple_id or left.split != right.split:
            local_errors.append("balance_and_split")
        for twin in twins:
            try:
                if twin.oracle("aligned").ratio != twin.goal.answer_ratio:
                    local_errors.append("parent_free_oracle")
            except Exception as exc:  # fail closed and retain the exact reason
                local_errors.append(f"parent_free_oracle:{type(exc).__name__}")
            bridge_candidates = bridge_removed_candidates(
                twin.public_episodes("aligned"), twin.public_goal()
            )
            bridge_ratios = {candidate.ratio for candidate in bridge_candidates}
            if len(bridge_ratios) < 2 or twin.goal.answer_ratio not in bridge_ratios:
                local_errors.append("bridge_removed_ambiguity")
            positions = twin.proof_episode_positions("aligned")
            if max(positions) - min(positions) < twin.config.context_observation_budget:
                local_errors.append("temporal_gap")
            effects[twin.intervention_effect] += 1
            roles[twin.goal_role] += 1
            classes[twin.choice.collision_class_id] += 1
            discriminator_sources[twin.choice.discriminator_source] += 1
            answer_ratios[twin.goal.answer_ratio] += 1
            splits[twin.split] += 1
            for skin in all_skin_names():
                goal_question = twin.render_goal(skin)["question"]
                answer = twin.ratio_surface(twin.goal.answer_ratio, skin)
                surface_goal_answers[(skin, goal_question)].add(answer)
                public_episodes = twin.public_episodes(skin)
                for episode, public_episode in zip(twin.episodes, public_episodes):
                    kind, body = _episode_surface_feature(twin, episode, skin)
                    single_episode_answers[(goal_question, kind, body)].add(answer)
                    # Even the full typed oracle must be unable to answer from
                    # one isolated episode plus the public goal.
                    try:
                        parent_free_oracle((public_episode,), twin.public_goal())
                    except (ValueError, KeyError):
                        pass
                    else:
                        local_errors.append(f"single_episode_oracle:{skin}:{episode.id}")
        if local_errors:
            failures.append({"seed": seed, "errors": sorted(set(local_errors))})

    ambiguous_goal_surfaces = all(len(answers) >= 2 for answers in surface_goal_answers.values())
    ambiguous_single_episodes = all(
        len(answers) >= 2 for answers in single_episode_answers.values()
    )
    if not ambiguous_goal_surfaces:
        failures.append({"population": "surface_goal", "errors": ["surface_name_prediction"]})
    if not ambiguous_single_episodes:
        bad = sum(len(answers) < 2 for answers in single_episode_answers.values())
        failures.append(
            {"population": "single_episode", "errors": [f"{bad}_answer_sufficient_features"]}
        )

    # The generator schedules roles and discriminator internal IDs exactly or
    # within one pair.  Effect is exactly balanced by construction.  Collision
    # classes and answers are reported rather than falsely called uniform: the
    # finite catalog has unequal class multiplicities.
    # The animal-role shuffle and discriminator choice are deterministic but
    # not forced to exact equality; fail if either deviates by more than five
    # percentage points.  Collision-class and intervention arms are explicitly
    # stratified and therefore must be exact/within one pair.
    allowed_population_skew = max(2, (2 * n_pairs) // 20)
    role_balance = max(roles.values()) - min(roles.values()) <= allowed_population_skew
    source_balance = (
        max(discriminator_sources.values()) - min(discriminator_sources.values())
        <= allowed_population_skew
    )
    effect_balance = effects == {"CHANGE": n_pairs, "STABLE": n_pairs}
    class_balance = max(classes.values()) - min(classes.values()) <= 2
    heldout_fraction = splits.get("heldout", 0) / (2 * n_pairs)
    split_balance = 0.15 <= heldout_fraction <= 0.25
    answer_majority_floor = max(answer_ratios.values()) / (2 * n_pairs) <= 0.10
    # Color-channel words must not become an answer prior.  Every non-symmetric
    # ratio is required to appear with all of its cyclic RGB rotations.
    answer_support = set(answer_ratios)
    answer_rotation_balance = all(
        ratio[0] == ratio[1] == ratio[2]
        or {
            ratio,
            (ratio[1], ratio[2], ratio[0]),
            (ratio[2], ratio[0], ratio[1]),
        }
        <= answer_support
        for ratio in answer_support
    )
    if not (
        role_balance
        and source_balance
        and effect_balance
        and class_balance
        and split_balance
        and answer_majority_floor
        and answer_rotation_balance
    ):
        failures.append(
            {
                "population": "balance",
                "errors": [
                    name
                    for name, passed in (
                        ("roles", role_balance),
                        ("discriminator_sources", source_balance),
                        ("effects", effect_balance),
                        ("collision_classes", class_balance),
                        ("development_heldout_split", split_balance),
                        ("answer_majority", answer_majority_floor),
                        ("answer_rotation_support", answer_rotation_balance),
                    )
                    if not passed
                ],
            }
        )
    return {
        "schema_version": CounterfactualConfluenceV03.schema_version,
        "n_pairs": n_pairs,
        "n_worlds": 2 * n_pairs,
        "valid": not failures,
        "failures": failures,
        "counts": {
            "effects": dict(sorted(effects.items())),
            "roles": dict(sorted(roles.items())),
            "collision_classes": dict(sorted(classes.items())),
            "discriminator_sources": dict(sorted(discriminator_sources.items())),
            "answer_ratios": {str(key): value for key, value in sorted(answer_ratios.items())},
            "splits": dict(sorted(splits.items())),
        },
        "ambiguity": {
            "goal_surfaces": ambiguous_goal_surfaces,
            "single_episodes": ambiguous_single_episodes,
        },
    }


def _main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    audit_parser = subparsers.add_parser("audit")
    audit_parser.add_argument("--pairs", type=int, default=1000)
    render_parser = subparsers.add_parser("render")
    render_parser.add_argument("--seed", type=int, default=0)
    render_parser.add_argument("--latent-bit", type=int, choices=(0, 1), default=0)
    render_parser.add_argument("--skin", choices=all_skin_names(), default="aligned")
    args = parser.parse_args()
    if args.command == "audit":
        print(json.dumps(audit_paired_worlds(args.pairs), indent=2, sort_keys=True))
        return
    world = CounterfactualConfluenceV03(
        WorldConfig(seed=args.seed), latent_bit=args.latent_bit
    )
    print("\n".join(world.render_lifetime(args.skin)))
    print("\nGOAL")
    print(json.dumps(world.render_goal(args.skin, include_answer=True), indent=2))


if __name__ == "__main__":
    _main()
