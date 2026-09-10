"""Counterfactual Confluence v0.3-R: repaired paired causal instrument.

V0.3-R preserves the v0.3 collision construction but closes three benchmark
loopholes before any model run:

* a *pair* is the primary scoring unit -- both latent twins must be correct;
* control interventions are sampled independently of the twin bit, remain
  identical across twins, and are not a complementary mirror of the answer;
* the final counterfactual goal is revealed only after an operational,
  non-answer probe and a frozen pre-goal checkpoint.

The public solution still uses only local lived edges.  No parent set is
exported or consumed by the oracle.  This module is CPU-only acceptance
infrastructure; it is not a model result.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
import itertools
import json
import random
from typing import Any, Iterable, Mapping, Sequence

from .model import WorldConfig
from .skins import all_skin_names, make_skin
from .v02 import RATIO_FOR_COLOR, PigmentRatio, normalize_ratio
from .v03 import (
    AtomicEpisode,
    CollisionChoice,
    CounterfactualConfluenceV03,
    CounterfactualGoal,
    OracleResult,
    PublicCounterfactualGoal,
    TARGET_IDS,
    VALVE_IDS,
    _payload,
    _sha256,
    bridge_removed_candidates,
    enumerate_collision_catalog,
    exact_passive_signature,
    parent_free_oracle,
    source_ratio_for_role,
)
from .world import SemanticWorld


@dataclass(frozen=True)
class ControlIntervention:
    """A paired-invariant intervention sampled independently of latent bit."""

    valve_id: str
    source_id: str
    effect: str


@dataclass(frozen=True)
class OperationalProbe:
    """Intermediate agenda check; its answer is an entity, never goal truth."""

    id: str
    source_id: str
    target_id: str
    answer_valve_id: str
    next_operation: str


@dataclass(frozen=True)
class PublicOperationalProbe:
    id: str
    source_id: str
    target_id: str


@dataclass(frozen=True)
class PairedScore:
    n_pairs: int
    both_correct: int

    @property
    def accuracy(self) -> float:
        return self.both_correct / self.n_pairs if self.n_pairs else 0.0


def _eligible_choices(base: SemanticWorld) -> tuple[CollisionChoice, ...]:
    """Keep choices with two controls whose truth is invariant across twins."""
    all_sources = set(base.source_land_ids)
    choices = []
    for choice in enumerate_collision_catalog(base).choices:
        left = set(choice.source_subset_0)
        right = set(choice.source_subset_1)
        invariant_sources = (left & right) | (all_sources - (left | right))
        if len(invariant_sources) >= 2:
            choices.append(choice)
    return tuple(choices)


class CounterfactualConfluenceV03R(CounterfactualConfluenceV03):
    """One side of a repaired, paired Counterfactual Confluence life."""

    schema_version = "lands-v0.3r-counterfactual-confluence"

    def __init__(
        self,
        config: WorldConfig | None = None,
        *,
        latent_bit: int | None = None,
    ):
        # This intentionally spells out selection rather than constructing a
        # v0.3 object and mutating it.  The old instrument stays byte-stable.
        self.config = config or WorldConfig()
        self.config.validate()
        self.base = SemanticWorld(self.config)
        self.animal_ids = self.base.animal_ids
        self.source_land_ids = self.base.source_land_ids
        self.anchor_animals = self.base.anchor_animals
        self.eval_animals = self.base.eval_animals
        self.latent_bit = self.config.seed & 1 if latent_bit is None else latent_bit
        if self.latent_bit not in (0, 1):
            raise ValueError("latent_bit must be 0 or 1")

        self.catalog = enumerate_collision_catalog(self.base)
        eligible = _eligible_choices(self.base)
        class_ids = tuple(sorted({choice.collision_class_id for choice in eligible}))
        if len(class_ids) < 5:
            raise RuntimeError("too few collision classes survive v0.3-R controls")
        self.goal_role = self.config.seed % 3
        class_index = self.config.seed % len(class_ids)
        desired_class = class_ids[class_index]
        pool = tuple(
            choice for choice in eligible if choice.collision_class_id == desired_class
        )
        # Preserve v0.3's anti-majority preference without weakening class or
        # role stratification.  Two-answer paired scoring remains mandatory.
        brown = RATIO_FOR_COLOR["brown"]
        non_brown = tuple(
            choice
            for choice in pool
            if choice.blocked_outcomes_0[self.goal_role] != brown
            and choice.blocked_outcomes_1[self.goal_role] != brown
        )
        if non_brown:
            pool = non_brown
        self.choice = pool[(self.config.seed // len(class_ids)) % len(pool)]

        rng = random.Random(self.config.seed ^ 0xC0F1_030F)
        valve_order = list(VALVE_IDS)
        rng.shuffle(valve_order)
        self.goal_valve_id = valve_order[0]
        self.mirror_valve_id = valve_order[1]  # compatibility name; not a mirror arm
        self.actual_source_subset = self.choice.actual_subset(self.latent_bit)
        self.intervention_effect = (
            "CHANGE"
            if self.choice.discriminator_source in self.actual_source_subset
            else "STABLE"
        )

        left = set(self.choice.source_subset_0)
        right = set(self.choice.source_subset_1)
        common_sources = left & right
        invariant_sources = sorted(
            common_sources | (set(self.source_land_ids) - (left | right))
        )
        sampled_controls = rng.sample(invariant_sources, 2)
        self.control_interventions = tuple(
            ControlIntervention(
                valve_order[index + 1],
                source_id,
                "CHANGE" if source_id in common_sources else "STABLE",
            )
            for index, source_id in enumerate(sampled_controls)
        )
        if self.choice.discriminator_source in {
            control.source_id for control in self.control_interventions
        }:
            raise RuntimeError("primary and control sources overlap")
        # One independent distractor intervention and two distractor passive
        # rows restore the ratified seed-0 46-event life with semantic evidence,
        # not inert padding.  Selection is independent of the primary latent
        # bit, hence byte-identical across the paired goal twins.
        self._distractors = self._select_distractors()
        self.distractor_valve_id = valve_order[3]
        distractor_choice, distractor_side = self._distractors[0]
        self.distractor_effect = (
            "CHANGE"
            if distractor_choice.discriminator_source
            in distractor_choice.actual_subset(distractor_side)
            else "STABLE"
        )

        self.goal_animal = next(
            animal
            for animal in self.eval_animals
            if self.base.animal_roles[animal] == self.goal_role
        )
        self._goal_surface_slot = self.animal_ids[-1]
        self.goal = CounterfactualGoal(
            id="v03r_goal_0000",
            animal_id=self.goal_animal,
            target_id=TARGET_IDS[0],
            blocked_source_id=self.choice.discriminator_source,
            answer_ratio=self.choice.outcome_for(self.latent_bit, self.goal_role),
            role=self.goal_role,
        )
        self.operational_probe = OperationalProbe(
            id="v03r_probe_0000",
            source_id=self.choice.discriminator_source,
            target_id=TARGET_IDS[0],
            answer_valve_id=self.goal_valve_id,
            next_operation=(
                "SUBTRACT_SOURCE_CONTRIBUTION"
                if self.intervention_effect == "CHANGE"
                else "KEEP_PASSIVE_BASELINE"
            ),
        )

        tuple_material = {
            "source_role_table": {
                source: [
                    self.base.source_color_for_role(role, source)
                    for role in range(3)
                ]
                for source in self.source_land_ids
            },
            "collision_class_id": self.choice.collision_class_id,
            "source_subset_0": self.choice.source_subset_0,
            "source_subset_1": self.choice.source_subset_1,
            "discriminator_source": self.choice.discriminator_source,
            "goal_role": self.goal_role,
            "goal_animal": self.goal_animal,
            "control_sources": [
                control.source_id for control in self.control_interventions
            ],
            "paired_invariant_distractors": [
                {
                    "collision_class_id": choice.collision_class_id,
                    "source_subset_0": choice.source_subset_0,
                    "source_subset_1": choice.source_subset_1,
                    "discriminator_source": choice.discriminator_source,
                    "side": side,
                }
                for choice, side in self._distractors
            ],
        }
        self.latent_tuple_id = _sha256(tuple_material)
        # Group the exact public passive feature before splitting.  Thus an
        # exact-signature memorizer cannot see a heldout key during training,
        # while collision classes/answers remain represented on both sides.
        passive_split_key = tuple(
            sorted(
                (anchor_id, self.choice.signature[role])
                for role, anchor_id in enumerate(self.anchor_animals)
            )
        )
        self.split = (
            "heldout"
            if int(_sha256(passive_split_key)[:8], 16) % 5 == 0
            else "development"
        )

        self._ratio_labels = self._build_ratio_labels()
        self.episodes = self._build_episodes()
        self._validate_local()

    def _needed_ratios(self) -> tuple[PigmentRatio, ...]:
        ratios = set(RATIO_FOR_COLOR.values())
        ratios.update(normalize_ratio(ratio) for ratio in self.choice.signature)
        ratios.update(self.choice.blocked_outcomes_0)
        ratios.update(self.choice.blocked_outcomes_1)
        for choice, side in self._distractors:
            ratios.update(normalize_ratio(ratio) for ratio in choice.signature)
            ratios.update(
                choice.blocked_outcomes_0 if side == 0 else choice.blocked_outcomes_1
            )
        return tuple(sorted(ratios))

    def _build_episodes(self) -> tuple[AtomicEpisode, ...]:
        route_records = [
            self._episode(
                "valve_route",
                "route_experience",
                valve_id=self.goal_valve_id,
                source_id=self.choice.discriminator_source,
            )
        ]
        effect_records = [
            self._episode(
                "intervention_effect",
                "intervention_experience",
                valve_id=self.goal_valve_id,
                target_id=TARGET_IDS[0],
                effect=self.intervention_effect,
            )
        ]
        for control in self.control_interventions:
            route_records.append(
                self._episode(
                    "valve_route",
                    "route_experience",
                    valve_id=control.valve_id,
                    source_id=control.source_id,
                )
            )
            effect_records.append(
                self._episode(
                    "intervention_effect",
                    "intervention_experience",
                    valve_id=control.valve_id,
                    target_id=TARGET_IDS[0],
                    effect=control.effect,
                )
            )
        distractor_choice, _ = self._distractors[0]
        route_records.append(
            self._episode(
                "valve_route",
                "route_experience",
                valve_id=self.distractor_valve_id,
                source_id=distractor_choice.discriminator_source,
            )
        )
        effect_records.append(
            self._episode(
                "intervention_effect",
                "intervention_experience",
                valve_id=self.distractor_valve_id,
                target_id=TARGET_IDS[1],
                effect=self.distractor_effect,
            )
        )

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

        observations = tuple(
            observation
            for observation in self.base.sample_lifetime().observations
            if observation.animal_id == self.goal_animal
            and observation.land_id in self.source_land_ids
            and not observation.repeated
        )
        if len(observations) != 2:
            raise RuntimeError("goal animal must have two dispersed role observations")
        for observation in observations:
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
        for distractor_index, (choice, _side) in enumerate(
            self._distractors, start=1
        ):
            role = distractor_index % 3
            ratio = choice.signature[role]
            filler.append(
                self._episode(
                    "target_passive_baseline",
                    "passive_control",
                    target_id=TARGET_IDS[distractor_index],
                    anchor_id=self.anchor_animals[role],
                    label=self.ratio_surface(normalize_ratio(ratio), "aligned"),
                    ratio=ratio,
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

        rng = random.Random(self.config.seed ^ 0xE913_030F)
        rng.shuffle(route_records)
        rng.shuffle(filler)
        # All four routes occur early and are exchangeable.  Effects are at
        # least one full working window apart; the primary effect is randomly
        # assigned to one of the two latest slots, never adjacent to its route.
        non_effect = [*route_records, *filler]
        gap = self.config.context_observation_budget + 1
        # The earliest invariant control may precede learning its route.  That
        # is a legitimate temporally reversed association and lets even the
        # shortest valid life keep four effects a full window apart.
        effect_slots = (0, gap, 2 * gap, 3 * gap)
        if effect_slots[-1] >= len(non_effect) + len(effect_records):
            raise RuntimeError("not enough informative episodes to disperse interventions")
        primary = effect_records[0]
        controls = effect_records[1:]
        late_slots = [effect_slots[2], effect_slots[3]]
        primary_slot = rng.choice(late_slots)
        control_slots = [slot for slot in effect_slots if slot != primary_slot]
        rng.shuffle(controls)
        by_slot = {primary_slot: primary}
        by_slot.update(zip(control_slots, controls))
        ordered: list[tuple[str, str, dict[str, Any]]] = []
        source_index = 0
        total = len(non_effect) + len(effect_records)
        for position in range(total):
            if position in by_slot:
                ordered.append(by_slot[position])
            else:
                ordered.append(non_effect[source_index])
                source_index += 1

        return tuple(
            AtomicEpisode(
                id=f"v03r_edge_{index:04d}",
                episode_id=f"v03r_episode_{index:04d}",
                phase=phase,
                kind=kind,
                payload=payload,
            )
            for index, (kind, phase, payload) in enumerate(ordered)
        )

    def public_operational_probe(self) -> PublicOperationalProbe:
        return PublicOperationalProbe(
            id=self.operational_probe.id,
            source_id=self.operational_probe.source_id,
            target_id=self.operational_probe.target_id,
        )

    def render_operational_probe(self, skin_name: str = "aligned") -> dict[str, str]:
        skin = make_skin(skin_name, self.animal_ids, self.source_land_ids)
        source = skin.land(self.operational_probe.source_id)
        target = self.target_surface(self.operational_probe.target_id, skin_name)
        question = (
            f"Determine whether committed experience supports a causal join from "
            f"{source} to {target}. If it does not, request that missing typed join."
        )
        distractor_choice, _ = self._distractors[0]
        # The entity handles are public query coordinates, not the answer.
        # They identify the two endpoints whose missing causal join the
        # intermediate thinker may request.  Valve identity, operation,
        # intervention result, and final counterfactual truth remain absent.
        return {
            "probe_id": self.operational_probe.id,
            "source_entity_id": f"entity:source:{self.operational_probe.source_id}",
            "target_entity_id": f"entity:target:{self.operational_probe.target_id}",
            "matched_distractor_source_entity_id": (
                f"entity:source:{distractor_choice.discriminator_source}"
            ),
            "matched_distractor_target_entity_id": f"entity:target:{TARGET_IDS[1]}",
            "question": question,
        }

    def operational_probe_oracle(self) -> tuple[str, str]:
        routes = [
            episode
            for episode in self.public_episodes()
            if episode.kind == "valve_route"
            and _payload(episode, "source_id") == self.operational_probe.source_id
        ]
        if len(routes) != 1:
            raise ValueError("operational probe route is not unique")
        valve_id = str(_payload(routes[0], "valve_id"))
        effects = [
            episode
            for episode in self.public_episodes()
            if episode.kind == "intervention_effect"
            and _payload(episode, "valve_id") == valve_id
            and _payload(episode, "target_id") == self.operational_probe.target_id
        ]
        if len(effects) != 1:
            raise ValueError("operational probe intervention is not unique")
        operation = (
            "SUBTRACT_SOURCE_CONTRIBUTION"
            if _payload(effects[0], "effect") == "CHANGE"
            else "KEEP_PASSIVE_BASELINE"
        )
        return valve_id, operation

    def precheckpoint_export(self, skin_name: str = "aligned") -> dict[str, Any]:
        """Public life plus agenda probe, with the final paired goal absent."""
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
                    # Exact structured form of the same public observation.
                    # This is intentionally model-visible: it removes brittle
                    # skin-specific parsing without exposing any field that is
                    # unavailable in the rendered episode.
                    "public_record": dict(episode.payload),
                }
                for episode in self.episodes
            ],
            "operational_probe": self.render_operational_probe(skin_name),
        }

    def precheckpoint_fingerprint(self, skin_name: str = "aligned") -> str:
        """Sidecar integrity hash; deliberately absent from model-visible data."""
        return _sha256(self.precheckpoint_export(skin_name))

    def reveal_final_goal(self, skin_name: str = "aligned") -> dict[str, str]:
        return self.render_goal(skin_name, include_answer=False)

    def schedule_manifest(self) -> dict[str, int]:
        """Report the frozen life budget instead of assuming every seed is 46.

        The ratified first calibration uses seed 0 (46 WAKE, 22 periodic
        REACTIVATE).  Recipe support varies across later seeds, so future
        multi-seed schedulers must consume these actual per-life counts while
        matching arms within each frozen world.
        """
        wake_calls = len(self.episodes)
        return {
            "episode_count": wake_calls,
            "wake_calls": wake_calls,
            "periodic_reactivate_calls": 2 * (wake_calls // 4),
        }

    def local_window_oracle_successes(
        self, skin_name: str = "aligned"
    ) -> tuple[tuple[int, int], ...]:
        public = self.public_episodes(skin_name)
        budget = self.config.context_observation_budget
        successes = []
        for start in range(len(public)):
            window = public[start : start + budget]
            try:
                parent_free_oracle(window, self.public_goal())
            except (ValueError, KeyError):
                continue
            successes.append((start, start + len(window)))
        return tuple(successes)

    def edge_removal_ablation(self, skin_name: str = "aligned") -> dict[str, bool]:
        """Return whether the oracle improperly survives each missing edge family."""
        public = self.public_episodes(skin_name)
        goal = self.public_goal()
        cases: dict[str, tuple[AtomicEpisode, ...]] = {
            "valve_route": tuple(
                episode
                for episode in public
                if not (
                    episode.kind == "valve_route"
                    and _payload(episode, "source_id") == goal.blocked_source_id
                )
            ),
            "intervention_effect": tuple(
                episode
                for episode in public
                if not (
                    episode.kind == "intervention_effect"
                    and _payload(episode, "valve_id") == self.goal_valve_id
                    and _payload(episode, "target_id") == goal.target_id
                )
            ),
            "animal_role": tuple(
                episode for episode in public if episode.kind != "animal_source_color"
            ),
            "target_baseline": tuple(
                episode for episode in public if episode.kind != "target_passive_baseline"
            ),
            "source_calibration": tuple(
                episode
                for episode in public
                if not (
                    episode.kind == "source_anchor_color"
                    and _payload(episode, "source_id") == goal.blocked_source_id
                )
            ),
            "workshop": tuple(
                episode for episode in public if episode.kind != "workshop_recipe"
            ),
        }
        survived = {}
        for name, episodes in cases.items():
            try:
                parent_free_oracle(episodes, goal)
            except (ValueError, KeyError):
                survived[name] = False
            else:
                survived[name] = True
        return survived

    def _validate_local(self) -> None:
        if exact_passive_signature(self.base, self.choice.source_subset_0) != self.choice.signature:
            raise RuntimeError("left passive collision failed")
        if exact_passive_signature(self.base, self.choice.source_subset_1) != self.choice.signature:
            raise RuntimeError("right passive collision failed")
        if self.oracle().ratio != self.goal.answer_ratio:
            raise RuntimeError("public-only oracle failed")
        if self.operational_probe_oracle() != (
            self.operational_probe.answer_valve_id,
            self.operational_probe.next_operation,
        ):
            raise RuntimeError("operational probe oracle failed")
        if self.local_window_oracle_successes():
            raise RuntimeError("a local working window contains the complete proof")
        if any(self.edge_removal_ablation().values()):
            raise RuntimeError("oracle survived a required edge removal")
        effect_positions = [
            index
            for index, episode in enumerate(self.episodes)
            if episode.kind == "intervention_effect"
        ]
        if min(
            right - left for left, right in zip(effect_positions, effect_positions[1:])
        ) <= self.config.context_observation_budget:
            raise RuntimeError("intervention effects are not temporally dispersed")
        primary_index = next(
            index
            for index, episode in enumerate(self.episodes)
            if episode.kind == "intervention_effect"
            and _payload(episode, "valve_id") == self.goal_valve_id
        )
        route_index = next(
            index
            for index, episode in enumerate(self.episodes)
            if episode.kind == "valve_route"
            and _payload(episode, "valve_id") == self.goal_valve_id
        )
        if primary_index - route_index <= self.config.context_observation_budget:
            raise RuntimeError("primary route and outcome fit in one local window")
        controls = {
            (control.valve_id, control.source_id, control.effect)
            for control in self.control_interventions
        }
        if len(controls) != 2 or not {item[2] for item in controls} <= {"CHANGE", "STABLE"}:
            raise RuntimeError("paired-invariant controls are malformed")
        distractor_routes = [
            episode
            for episode in self.episodes
            if episode.kind == "valve_route"
            and _payload(episode, "valve_id") == self.distractor_valve_id
        ]
        distractor_effects = [
            episode
            for episode in self.episodes
            if episode.kind == "intervention_effect"
            and _payload(episode, "valve_id") == self.distractor_valve_id
            and _payload(episode, "target_id") == TARGET_IDS[1]
        ]
        if len(distractor_routes) != 1 or len(distractor_effects) != 1:
            raise RuntimeError("paired-invariant distractor intervention is malformed")
        if _payload(distractor_effects[0], "effect") != self.distractor_effect:
            raise RuntimeError("distractor effect disagrees with its independent world")
        passive_control_targets = {
            _payload(episode, "target_id")
            for episode in self.episodes
            if episode.kind == "target_passive_baseline"
            and episode.phase == "passive_control"
        }
        if passive_control_targets != {TARGET_IDS[1], TARGET_IDS[2]}:
            raise RuntimeError("paired-invariant passive controls are incomplete")
        for episode in self.episodes:
            if any(key in episode.payload for key in ("parents", "source_subset", "latent_bit")):
                raise RuntimeError("public episode leaks hidden factorization")


def score_paired_predictions(
    pairs: Sequence[tuple[CounterfactualConfluenceV03R, CounterfactualConfluenceV03R]],
    predictions: Mapping[tuple[int, int], PigmentRatio],
) -> PairedScore:
    """Score only when both members of a latent pair are correct."""
    both = 0
    for left, right in pairs:
        key_left = (left.config.seed, 0)
        key_right = (right.config.seed, 1)
        if (
            predictions.get(key_left) == left.goal.answer_ratio
            and predictions.get(key_right) == right.goal.answer_ratio
        ):
            both += 1
    return PairedScore(len(pairs), both)


def _feature_components(world: CounterfactualConfluenceV03R) -> dict[str, Any]:
    """Public-only shortcut features; notably excludes valve-route joins."""
    public = world.public_episodes("aligned")
    goal = world.public_goal()
    return {
        "goal": (goal.animal_id, goal.target_id, goal.blocked_source_id),
        "passive": tuple(
            sorted(
                (
                    _payload(episode, "anchor_id"),
                    tuple(_payload(episode, "ratio")),
                )
                for episode in public
                if episode.kind == "target_passive_baseline"
                and _payload(episode, "target_id") == goal.target_id
            )
        ),
        "effects": tuple(
            sorted(
                (
                    _payload(episode, "valve_id"),
                    _payload(episode, "target_id"),
                    _payload(episode, "effect"),
                )
                for episode in public
                if episode.kind == "intervention_effect"
            )
        ),
        "source": tuple(
            sorted(
                (
                    _payload(episode, "anchor_id"),
                    _payload(episode, "source_id"),
                    _payload(episode, "label"),
                )
                for episode in public
                if episode.kind == "source_anchor_color"
            )
        ),
        "role": tuple(
            sorted(
                (
                    _payload(episode, "source_id"),
                    _payload(episode, "label"),
                )
                for episode in public
                if episode.kind == "animal_source_color"
                and _payload(episode, "animal_id") == goal.animal_id
            )
        ),
    }


def _fit_lookup(
    train: Sequence[CounterfactualConfluenceV03R], names: Sequence[str]
) -> tuple[dict[Any, PigmentRatio], PigmentRatio]:
    global_counts = Counter(world.goal.answer_ratio for world in train)
    global_label = sorted(global_counts, key=lambda label: (-global_counts[label], label))[0]
    buckets: dict[Any, Counter[PigmentRatio]] = defaultdict(Counter)
    for world in train:
        parts = _feature_components(world)
        key = tuple(parts[name] for name in names)
        buckets[key][world.goal.answer_ratio] += 1
    table = {
        key: sorted(counts, key=lambda label: (-counts[label], label))[0]
        for key, counts in buckets.items()
    }
    return table, global_label


def trained_shortcut_audit(
    pairs: Sequence[tuple[CounterfactualConfluenceV03R, CounterfactualConfluenceV03R]],
) -> dict[str, Any]:
    train = [world for pair in pairs for world in pair if world.split == "development"]
    test_pairs = [pair for pair in pairs if pair[0].split == "heldout"]
    test = [world for pair in test_pairs for world in pair]
    if not train or not test:
        raise ValueError("shortcut audit needs nonempty development and heldout sets")
    feature_names = ("goal", "passive", "effects", "source", "role")
    reports: dict[str, Any] = {}
    for size in range(1, len(feature_names) + 1):
        for names in itertools.combinations(feature_names, size):
            table, fallback = _fit_lookup(train, names)
            predictions: dict[tuple[int, int], PigmentRatio] = {}
            correct = 0
            for world in test:
                parts = _feature_components(world)
                key = tuple(parts[name] for name in names)
                prediction = table.get(key, fallback)
                predictions[(world.config.seed, world.latent_bit)] = prediction
                correct += prediction == world.goal.answer_ratio
            paired = score_paired_predictions(test_pairs, predictions)
            reports["+".join(names)] = {
                "individual_accuracy": correct / len(test),
                "paired_both_correct_accuracy": paired.accuracy,
                "seen_key_fraction": sum(
                    tuple(_feature_components(world)[name] for name in names) in table
                    for world in test
                )
                / len(test),
            }
    _, majority_label = _fit_lookup(train, ())
    majority_correct = sum(world.goal.answer_ratio == majority_label for world in test)
    majority_predictions = {
        (world.config.seed, world.latent_bit): majority_label for world in test
    }
    return {
        "n_development_worlds": len(train),
        "n_heldout_worlds": len(test),
        "n_heldout_pairs": len(test_pairs),
        "majority_accuracy": majority_correct / len(test),
        "majority_paired_both_correct_accuracy": score_paired_predictions(
            test_pairs, majority_predictions
        ).accuracy,
        "predictors": reports,
    }


def audit_paired_worlds_r(n_pairs: int = 1000) -> dict[str, Any]:
    """Run population, leakage, paired-score, and shortcut audits."""
    if n_pairs < 8:
        raise ValueError("v0.3-R population audit needs at least eight pairs")
    pairs = [
        (
            CounterfactualConfluenceV03R(WorldConfig(seed=seed), latent_bit=0),
            CounterfactualConfluenceV03R(WorldConfig(seed=seed), latent_bit=1),
        )
        for seed in range(n_pairs)
    ]
    failures: list[dict[str, Any]] = []
    answers: Counter[PigmentRatio] = Counter()
    effects: Counter[str] = Counter()
    classes: Counter[str] = Counter()
    roles: Counter[int] = Counter()
    splits: Counter[str] = Counter()
    oracle_predictions: dict[tuple[int, int], PigmentRatio] = {}
    single_features: dict[tuple[str, str], set[PigmentRatio]] = defaultdict(set)

    for left, right in pairs:
        errors = []
        if left.choice.signature != right.choice.signature:
            errors.append("passive_collision")
        if left.goal.answer_ratio == right.goal.answer_ratio:
            errors.append("paired_answer_separation")
        if left.render_goal() != right.render_goal():
            errors.append("paired_goal_identity")
        if left.control_interventions != right.control_interventions:
            errors.append("control_not_pair_invariant")
        differing = [
            index
            for index, (a, b) in enumerate(zip(left.episodes, right.episodes))
            if a.to_dict() != b.to_dict()
        ]
        if len(differing) != 1:
            errors.append(f"paired_lifetime_differences:{len(differing)}")
        elif left.episodes[differing[0]].kind != "intervention_effect":
            errors.append("paired_difference_not_primary_effect")
        for world in (left, right):
            try:
                oracle = world.oracle()
                oracle_predictions[(world.config.seed, world.latent_bit)] = oracle.ratio
            except Exception as exc:
                errors.append(f"oracle:{type(exc).__name__}")
                continue
            if oracle.ratio != world.goal.answer_ratio:
                errors.append("oracle_wrong")
            if world.local_window_oracle_successes():
                errors.append("local_window_sufficient")
            if any(world.edge_removal_ablation().values()):
                errors.append("edge_removal_survived")
            if world.operational_probe_oracle() != (
                world.operational_probe.answer_valve_id,
                world.operational_probe.next_operation,
            ):
                errors.append("operational_probe")
            precheckpoint = json.dumps(world.precheckpoint_export(), sort_keys=True)
            final = world.render_goal()["question"]
            if "v03r_goal_0000" in precheckpoint or final in precheckpoint:
                errors.append("final_goal_visible_precheckpoint")
            answers[world.goal.answer_ratio] += 1
            effects[world.intervention_effect] += 1
            classes[world.choice.collision_class_id] += 1
            roles[world.goal_role] += 1
            splits[world.split] += 1
            for episode in world.episodes:
                body = world.render_episode(episode, "aligned").split("] ", 1)[1]
                single_features[(episode.kind, body)].add(world.goal.answer_ratio)
        if errors:
            failures.append({"seed": left.config.seed, "errors": sorted(set(errors))})

    paired_oracle = score_paired_predictions(pairs, oracle_predictions)
    if paired_oracle.both_correct != n_pairs:
        failures.append({"population": "paired_oracle", "errors": ["not_1.0"]})
    ambiguous_single = all(len(values) >= 2 for values in single_features.values())
    if not ambiguous_single:
        failures.append(
            {
                "population": "single_episode",
                "errors": [
                    f"{sum(len(values) < 2 for values in single_features.values())}_sufficient"
                ],
            }
        )

    shortcuts = trained_shortcut_audit(pairs)
    passive = shortcuts["predictors"]["passive"]["individual_accuracy"]
    majority = shortcuts["majority_accuracy"]
    passive_gate = passive <= majority + 0.02
    if not passive_gate:
        failures.append(
            {
                "population": "passive_development_to_heldout_gate",
                "errors": [f"{passive:.6f}>{majority:.6f}+0.02"],
            }
        )
    max_answer = max(answers.values()) / (2 * n_pairs)
    if max_answer > 0.12:
        failures.append(
            {"population": "answer_balance", "errors": [f"majority={max_answer:.6f}"]}
        )

    return {
        "schema_version": CounterfactualConfluenceV03R.schema_version,
        "n_pairs": n_pairs,
        "n_worlds": 2 * n_pairs,
        "valid": not failures,
        "failures": failures,
        "paired_both_correct": {"public_oracle": paired_oracle.accuracy},
        "ambiguity": {
            "single_episode": ambiguous_single,
            "local_window_oracle_successes": 0,
        },
        "passive_gate": {
            "development_to_heldout_accuracy": passive,
            "majority_accuracy": majority,
            "threshold": majority + 0.02,
            "passed": passive_gate,
        },
        "counts": {
            "answers": {str(key): value for key, value in sorted(answers.items())},
            "effects": dict(sorted(effects.items())),
            "classes": dict(sorted(classes.items())),
            "roles": dict(sorted(roles.items())),
            "splits": dict(sorted(splits.items())),
        },
        "shortcut_predictors": shortcuts,
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
        print(json.dumps(audit_paired_worlds_r(args.pairs), indent=2, sort_keys=True))
        return
    world = CounterfactualConfluenceV03R(
        WorldConfig(seed=args.seed), latent_bit=args.latent_bit
    )
    print("\n".join(world.render_lifetime(args.skin)))
    print("\nOPERATIONAL PROBE")
    print(json.dumps(world.render_operational_probe(args.skin), indent=2))
    print("\nFINAL GOAL (revealed after checkpoint)")
    print(json.dumps(world.render_goal(args.skin, include_answer=True), indent=2))


if __name__ == "__main__":
    _main()
