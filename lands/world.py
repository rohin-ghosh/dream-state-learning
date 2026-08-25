"""Deterministic latent generator and public Semantic World interface."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import itertools
import json
import random
from typing import Any, Iterable, Sequence

from .model import (
    AtomicMemory,
    Episode,
    Goal,
    GoalDepth,
    Lifetime,
    MemoryClaim,
    Observation,
    ProofGraph,
    ProofNode,
    RenderedWorld,
    VerificationBudget,
    VerificationResult,
    WorldConfig,
)
from .skins import INTERNAL_COLORS, all_skin_names, make_skin


PALETTES: dict[str, tuple[str, str, str]] = {
    "primary": ("red", "yellow", "blue"),
    "secondary": ("orange", "green", "purple"),
}
PIGMENTS: dict[str, frozenset[str]] = {
    "red": frozenset("R"),
    "yellow": frozenset("Y"),
    "blue": frozenset("B"),
    "orange": frozenset(("R", "Y")),
    "green": frozenset(("Y", "B")),
    "purple": frozenset(("R", "B")),
    "brown": frozenset(("R", "Y", "B")),
}
COLOR_FOR_PIGMENTS = {pigments: color for color, pigments in PIGMENTS.items()}


@dataclass(frozen=True)
class LandSpec:
    palette: str
    rotation: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def blend_colors(colors: Iterable[str]) -> str:
    pigments: frozenset[str] = frozenset()
    for color in colors:
        pigments = pigments | PIGMENTS[color]
    try:
        return COLOR_FOR_PIGMENTS[pigments]
    except KeyError as exc:
        raise ValueError(f"unsupported pigment union {sorted(pigments)}") from exc


class SemanticWorld:
    """One hidden world with three isomorphic textual renderings.

    Construction also freezes the lifetime and goal split.  No method here
    calls a language model or mutates the world.
    """

    def __init__(self, config: WorldConfig | None = None):
        self.config = config or WorldConfig()
        self.config.validate()
        self._rng = random.Random(self.config.seed)
        self.animal_ids = tuple(
            f"animal_{index:02d}" for index in range(self.config.n_animals)
        )
        self.source_land_ids = tuple(
            f"land_{index:02d}" for index in range(self.config.n_source_lands)
        )
        self.meta_land_id = "land_meta"

        roles = [index % 3 for index in range(self.config.n_animals)]
        self._rng.shuffle(roles)
        self.animal_roles = dict(zip(self.animal_ids, roles))

        transformations = [
            LandSpec(palette, rotation)
            for palette in ("primary", "secondary")
            for rotation in range(3)
        ]
        self._rng.shuffle(transformations)
        self.land_specs = dict(zip(self.source_land_ids, transformations))
        self.meta_parents = self._select_identifiable_meta_parents()
        self.meta_operator = "pigment_union"

        self.anchor_animals = tuple(
            next(animal for animal in self.animal_ids if self.animal_roles[animal] == role)
            for role in range(3)
        )
        self.eval_animals = tuple(
            animal for animal in self.animal_ids if animal not in self.anchor_animals
        )

        self._observed_source_lands: dict[str, tuple[str, str]] = {}
        self._d1_targets: dict[str, str] = {}
        self._d2_targets: dict[str, str] = {}
        self._choose_sparse_cells()
        self._lifetime = self._build_lifetime()
        self._goals, self._proofs = self._build_goals_and_proofs()
        self._validate()

    # ------------------------------------------------------------------ truth
    def source_color_for_role(self, role: int, land_id: str) -> str:
        spec = self.land_specs[land_id]
        return PALETTES[spec.palette][(role + spec.rotation) % 3]

    def source_color(self, animal_id: str, land_id: str) -> str:
        return self.source_color_for_role(self.animal_roles[animal_id], land_id)

    def answer(self, animal_id: str, land_id: str) -> str:
        if animal_id not in self.animal_roles:
            raise KeyError(f"unknown animal {animal_id}")
        if land_id in self.land_specs:
            return self.source_color(animal_id, land_id)
        if land_id == self.meta_land_id:
            return blend_colors(
                self.source_color(animal_id, parent) for parent in self.meta_parents
            )
        raise KeyError(f"unknown land {land_id}")

    def _meta_signature(self, parents: Sequence[str]) -> tuple[str, str, str]:
        return tuple(
            blend_colors(self.source_color_for_role(role, land) for land in parents)
            for role in range(3)
        )

    def _select_identifiable_meta_parents(self) -> tuple[str, ...]:
        candidates = list(
            itertools.combinations(self.source_land_ids, self.config.meta_parent_count)
        )
        by_signature: dict[tuple[str, str, str], list[tuple[str, ...]]] = {}
        for parents in candidates:
            by_signature.setdefault(self._meta_signature(parents), []).append(parents)
        identifiable = [
            group[0]
            for signature, group in sorted(by_signature.items())
            if len(group) == 1 and len(set(signature)) >= 2
        ]
        if not identifiable:
            raise RuntimeError("no uniquely identifiable meta parent set")
        return tuple(self._rng.choice(identifiable))

    # --------------------------------------------------------------- evidence
    def _lands_for_palette(self, palette: str) -> list[str]:
        return sorted(
            land for land, spec in self.land_specs.items() if spec.palette == palette
        )

    def _choose_sparse_cells(self) -> None:
        # There are four non-anchor animals per role at the default size.  Put
        # half of every role in each observed palette.  Within each role/palette
        # pair, target rotations 0 and 1.  This yields exactly two examples of
        # every rendered source color in D0, D1, and D2.
        by_role = {
            role: [animal for animal in self.eval_animals if self.animal_roles[animal] == role]
            for role in range(3)
        }
        if any(len(animals) % 2 for animals in by_role.values()):
            raise ValueError(
                "n_animals must leave an even number of eval animals per role"
            )
        for role, animals in by_role.items():
            half = len(animals) // 2
            assignments = ["primary"] * half + ["secondary"] * half
            for within_role, (animal, observed_palette) in enumerate(
                zip(animals, assignments)
            ):
                same_by_rotation = {
                    self.land_specs[land].rotation: land
                    for land in self._lands_for_palette(observed_palette)
                }
                other_palette = (
                    "secondary" if observed_palette == "primary" else "primary"
                )
                other_by_rotation = {
                    self.land_specs[land].rotation: land
                    for land in self._lands_for_palette(other_palette)
                }
                palette_local_index = (
                    within_role if observed_palette == "primary" else within_role - half
                )
                target_rotation = palette_local_index % 3
                d1_target = same_by_rotation[target_rotation]
                observed = tuple(
                    same_by_rotation[rotation]
                    for rotation in range(3)
                    if rotation != target_rotation
                )
                self._observed_source_lands[animal] = observed  # type: ignore[assignment]
                self._d1_targets[animal] = d1_target
                self._d2_targets[animal] = other_by_rotation[target_rotation]

    def _build_lifetime(self) -> Lifetime:
        phases: list[tuple[str, list[tuple[str, str, bool]]]] = []

        calibration = [
            (animal, land, False)
            for land in self.source_land_ids
            for animal in self.anchor_animals
        ]
        phases.append(("calibration", calibration))

        meta_support = [
            (animal, self.meta_land_id, False) for animal in self.anchor_animals
        ]
        phases.append(("meta_support", meta_support))

        # A repeated but uninformative visit creates an auditable temporal gap.
        buffer_cell = (self.anchor_animals[0], self.source_land_ids[0], True)
        phases.append(
            ("dispersion_buffer", [buffer_cell] * self.config.dispersion_buffer)
        )

        sparse = []
        for animal in self.eval_animals:
            sparse.extend(
                (animal, land, False)
                for land in self._observed_source_lands[animal]
            )
        phases.append(("sparse_lifetime", sparse))

        episodes: list[Episode] = []
        observation_index = 0
        episode_index = 0
        per_episode = self.config.observations_per_episode
        for phase, cells in phases:
            for start in range(0, len(cells), per_episode):
                episode_id = f"episode_{episode_index:04d}"
                records = []
                for step, (animal, land, repeated) in enumerate(cells[start:start + per_episode]):
                    records.append(
                        Observation(
                            id=f"obs_{observation_index:05d}",
                            episode_id=episode_id,
                            step=step,
                            animal_id=animal,
                            land_id=land,
                            color_id=self.answer(animal, land),
                            phase=phase,
                            repeated=repeated,
                        )
                    )
                    observation_index += 1
                episodes.append(Episode(episode_id, phase, tuple(records)))
                episode_index += 1
        return Lifetime(tuple(episodes))

    # ----------------------------------------------------------------- proofs
    def _cell_evidence(self) -> dict[tuple[str, str], tuple[str, ...]]:
        result: dict[tuple[str, str], list[str]] = {}
        for observation in self._lifetime.observations:
            result.setdefault(observation.cell(), []).append(observation.id)
        return {cell: tuple(ids) for cell, ids in result.items()}

    def _witness_node(self, prefix: str, animal: str, land: str) -> ProofNode:
        evidence = self._cell_evidence()[(animal, land)][0]
        return ProofNode(
            id=f"{prefix}_witness_{animal}_{land}",
            kind="witnessed_cell",
            evidence_ids=(evidence,),
            payload={"animal_id": animal, "land_id": land},
        )

    def _build_goals_and_proofs(self) -> tuple[tuple[Goal, ...], dict[str, ProofGraph]]:
        goals: list[Goal] = []
        proofs: dict[str, ProofGraph] = {}
        cell_evidence = self._cell_evidence()
        goal_index = 0

        # D0 uses distinct witnessed cells, excluding repeated buffer copies.
        for animal in self.eval_animals:
            available = sorted(
                cell for cell in cell_evidence if cell[0] == animal
            )
            if len(available) < self.config.d0_per_animal:
                raise RuntimeError(f"not enough D0 cells for {animal}")
            for cell in available[:self.config.d0_per_animal]:
                goal_id = f"goal_{goal_index:04d}"
                proof_id = f"proof_{goal_id}"
                witness = self._witness_node(proof_id, *cell)
                root = ProofNode(
                    id=f"{proof_id}_root",
                    kind="answer_from_witness",
                    depends_on=(witness.id,),
                )
                proof = ProofGraph(proof_id, root.id, GoalDepth.D0, (witness, root))
                goal = Goal(
                    goal_id,
                    GoalDepth.D0,
                    cell[0],
                    cell[1],
                    self.answer(*cell),
                    proof_id,
                    ("witnessed",),
                )
                goals.append(goal)
                proofs[proof_id] = proof
                goal_index += 1

        # D1: a local same-palette rectangle.
        bridge_anchor = self.anchor_animals[0]
        for animal in self.eval_animals:
            support_land = self._observed_source_lands[animal][0]
            target_land = self._d1_targets[animal]
            goal_id = f"goal_{goal_index:04d}"
            proof_id = f"proof_{goal_id}"
            animal_obs = self._witness_node(proof_id + "_animal", animal, support_land)
            anchor_source = self._witness_node(
                proof_id + "_anchor_source", bridge_anchor, support_land
            )
            anchor_target = self._witness_node(
                proof_id + "_anchor_target", bridge_anchor, target_land
            )
            delta = ProofNode(
                id=f"{proof_id}_local_delta",
                kind="same_palette_land_delta",
                depends_on=(anchor_source.id, anchor_target.id),
            )
            root = ProofNode(
                id=f"{proof_id}_root",
                kind="local_projection",
                depends_on=(animal_obs.id, delta.id),
            )
            proof = ProofGraph(
                proof_id,
                root.id,
                GoalDepth.D1,
                (animal_obs, anchor_source, anchor_target, delta, root),
            )
            goals.append(
                Goal(
                    goal_id,
                    GoalDepth.D1,
                    animal,
                    target_land,
                    self.answer(animal, target_land),
                    proof_id,
                    ("held_out", "same_palette"),
                )
            )
            proofs[proof_id] = proof
            goal_index += 1

        # D2: preserve animal role while moving to the other palette system.
        for animal in self.eval_animals:
            observed_lands = self._observed_source_lands[animal]
            target_land = self._d2_targets[animal]
            goal_id = f"goal_{goal_index:04d}"
            proof_id = f"proof_{goal_id}"
            animal_nodes = tuple(
                self._witness_node(proof_id + f"_animal_{i}", animal, land)
                for i, land in enumerate(observed_lands)
            )
            role_calibration_nodes = tuple(
                self._witness_node(
                    proof_id + f"_role_anchor_{i}", anchor, observed_lands[0]
                )
                for i, anchor in enumerate(self.anchor_animals)
            )
            role = ProofNode(
                id=f"{proof_id}_role",
                kind="animal_role",
                depends_on=tuple(
                    node.id for node in animal_nodes + role_calibration_nodes
                ),
            )
            target_anchor_nodes = tuple(
                self._witness_node(
                    proof_id + f"_target_anchor_{i}", anchor, target_land
                )
                for i, anchor in enumerate(self.anchor_animals)
            )
            target_transform = ProofNode(
                id=f"{proof_id}_target_transform",
                kind="land_palette_transform",
                depends_on=tuple(node.id for node in target_anchor_nodes),
            )
            # One anchor witnessed in both palette systems entitles invariance.
            observed_palette = self.land_specs[observed_lands[0]].palette
            other_palette_land = next(
                land for land in self.source_land_ids
                if self.land_specs[land].palette != observed_palette
            )
            bridge_nodes = (
                self._witness_node(
                    proof_id + "_bridge_a", bridge_anchor, observed_lands[0]
                ),
                self._witness_node(
                    proof_id + "_bridge_b", bridge_anchor, other_palette_land
                ),
            )
            bridge = ProofNode(
                id=f"{proof_id}_palette_bridge",
                kind="cross_palette_invariance",
                depends_on=tuple(node.id for node in bridge_nodes),
            )
            root = ProofNode(
                id=f"{proof_id}_root",
                kind="cross_palette_projection",
                depends_on=(role.id, target_transform.id, bridge.id),
            )
            nodes = animal_nodes + role_calibration_nodes + (role,) + target_anchor_nodes + (
                target_transform,
            ) + bridge_nodes + (bridge, root)
            proof = ProofGraph(proof_id, root.id, GoalDepth.D2, nodes)
            goals.append(
                Goal(
                    goal_id,
                    GoalDepth.D2,
                    animal,
                    target_land,
                    self.answer(animal, target_land),
                    proof_id,
                    ("held_out", "cross_palette"),
                )
            )
            proofs[proof_id] = proof
            goal_index += 1

        # D3: derive each parent value and compose through the meta operator.
        meta_support_ids = tuple(
            observation.id
            for observation in self._lifetime.observations
            if observation.animal_id in self.anchor_animals
            and not observation.repeated
        )
        for animal in self.eval_animals:
            goal_id = f"goal_{goal_index:04d}"
            proof_id = f"proof_{goal_id}"
            role_evidence = tuple(
                self._witness_node(proof_id + f"_role_{i}", animal, land)
                for i, land in enumerate(self._observed_source_lands[animal])
            )
            role_calibration = tuple(
                self._witness_node(
                    proof_id + f"_role_anchor_{i}",
                    anchor,
                    self._observed_source_lands[animal][0],
                )
                for i, anchor in enumerate(self.anchor_animals)
            )
            role = ProofNode(
                id=f"{proof_id}_role",
                kind="animal_role",
                depends_on=tuple(
                    node.id for node in role_evidence + role_calibration
                ),
            )
            source_nodes = []
            transform_nodes = []
            anchor_nodes = []
            for index, parent in enumerate(self.meta_parents):
                witnesses = tuple(
                    self._witness_node(
                        proof_id + f"_parent_{index}_anchor_{j}", anchor, parent
                    )
                    for j, anchor in enumerate(self.anchor_animals)
                )
                anchor_nodes.extend(witnesses)
                transform = ProofNode(
                    id=f"{proof_id}_parent_{index}_transform",
                    kind="land_palette_transform",
                    depends_on=tuple(node.id for node in witnesses),
                )
                transform_nodes.append(transform)
                source_nodes.append(
                    ProofNode(
                        id=f"{proof_id}_parent_{index}_value",
                        kind="source_projection",
                        depends_on=(role.id, transform.id),
                    )
                )
            meta_rule = ProofNode(
                id=f"{proof_id}_meta_rule",
                kind="meta_parent_blend_rule",
                evidence_ids=meta_support_ids,
                payload={"parent_count": len(self.meta_parents)},
            )
            root = ProofNode(
                id=f"{proof_id}_root",
                kind="pigment_union",
                depends_on=(meta_rule.id,) + tuple(node.id for node in source_nodes),
            )
            nodes = (
                role_evidence
                + role_calibration
                + (role,)
                + tuple(anchor_nodes)
                + tuple(transform_nodes)
                + tuple(source_nodes)
                + (meta_rule, root)
            )
            proof = ProofGraph(proof_id, root.id, GoalDepth.D3, nodes)
            goals.append(
                Goal(
                    goal_id,
                    GoalDepth.D3,
                    animal,
                    self.meta_land_id,
                    self.answer(animal, self.meta_land_id),
                    proof_id,
                    ("held_out", "meta", "second_order"),
                )
            )
            proofs[proof_id] = proof
            goal_index += 1

        return tuple(goals), proofs

    # ------------------------------------------------------------- public API
    def sample_lifetime(self) -> Lifetime:
        return self._lifetime

    def eval_goals(self, depth: GoalDepth | str | None = None) -> tuple[Goal, ...]:
        if depth is None:
            return self._goals
        normalized = depth if isinstance(depth, GoalDepth) else GoalDepth(depth)
        return tuple(goal for goal in self._goals if goal.depth == normalized)

    def proof_for(self, goal: Goal | str) -> ProofGraph:
        if isinstance(goal, str):
            match = next((candidate for candidate in self._goals if candidate.id == goal), None)
            if match is None:
                raise KeyError(f"unknown goal {goal}")
            goal = match
        return self._proofs[goal.proof_id]

    def oracle_memory(self) -> dict[str, Any]:
        return {
            "schema_version": "lands-oracle-v0.1",
            "animal_roles": dict(sorted(self.animal_roles.items())),
            "land_specs": {
                land: spec.to_dict() for land, spec in sorted(self.land_specs.items())
            },
            "meta": {
                "land_id": self.meta_land_id,
                "operator": self.meta_operator,
                "parents": list(self.meta_parents),
            },
        }

    def oracle_structure(self, skin: str = "aligned") -> tuple[str, ...]:
        rendered = make_skin(skin, self.animal_ids, self.source_land_ids)
        memories = [
            "Ordinary-land rule: each animal keeps one palette position. "
            "Each land selects a three-color palette and rotates its positions; "
            "combine the animal position and land rotation modulo three."
        ]
        positions = ("first", "second", "third")
        for animal in self.animal_ids:
            memories.append(
                f"{rendered.animal(animal)} keeps the {positions[self.animal_roles[animal]]} "
                "position in every ordinary land's palette."
            )
        for land in self.source_land_ids:
            spec = self.land_specs[land]
            palette = ", ".join(rendered.color(color) for color in PALETTES[spec.palette])
            memories.append(
                f"{rendered.land(land)} uses the {rendered.palette_name(spec.palette)} "
                f"palette [{palette}] with rotation {spec.rotation}."
            )
        parents = ", ".join(rendered.land(land) for land in self.meta_parents)
        memories.append(
            f"{rendered.land(self.meta_land_id)} blends the paint pigments of each "
            f"animal's colors from these parent lands: {parents}. Pigment union is "
            "associative and commutative; all three primary pigments make brown."
        )
        return tuple(memories)

    def atomic_memories_for(
        self,
        goal: Goal | str,
        skin: str = "aligned",
        *,
        resolved: bool = False,
    ) -> tuple[AtomicMemory, ...]:
        """Return positive, one-hop QA leaves sufficient for this goal.

        `resolved=True` materializes each D3 parent source value so the clean
        base only performs the final pigment union.  The unresolved form is
        the stricter factor-composition oracle.
        """
        if isinstance(goal, str):
            goal = next((candidate for candidate in self._goals if candidate.id == goal), None)
            if goal is None:
                raise KeyError(f"unknown goal {goal}")
        rendered = make_skin(skin, self.animal_ids, self.source_land_ids)
        observations = self._lifetime.observations

        def evidence_for(animal: str | None = None, land: str | None = None) -> tuple[str, ...]:
            return tuple(
                observation.id
                for observation in observations
                if (animal is None or observation.animal_id == animal)
                and (land is None or observation.land_id == land)
                and not observation.repeated
            )

        def merge_evidence(*groups: Sequence[str]) -> tuple[str, ...]:
            return tuple(dict.fromkeys(
                evidence_id for group in groups for evidence_id in group
            ))

        memories: list[AtomicMemory] = []
        animal_name = rendered.animal(goal.animal_id)
        land_name = rendered.land(goal.land_id)
        if goal.depth == GoalDepth.D0:
            memories.append(
                AtomicMemory(
                    f"{goal.id}_witness",
                    "witnessed_cell",
                    f"What color was {animal_name} in {land_name}?",
                    rendered.color(goal.answer_color_id).upper() + ".",
                    evidence_for(goal.animal_id, goal.land_id),
                )
            )
            return tuple(memories)

        role_land = self._observed_source_lands[goal.animal_id][0]
        role_evidence = merge_evidence(
            evidence_for(animal=goal.animal_id),
            *(
                evidence_for(animal=anchor, land=role_land)
                for anchor in self.anchor_animals
            ),
        )
        memories.append(
            AtomicMemory(
                f"{goal.id}_animal_position",
                "animal_position",
                f"Which position abstraction describes {animal_name}?",
                f"POSITION_{self.animal_roles[goal.animal_id]}.",
                role_evidence,
            )
        )
        memories.append(
            AtomicMemory(
                f"{goal.id}_source_rule",
                "public_source_rule",
                "How do an animal position and an ordinary-land transformation determine color?",
                "ADD_POSITION_AND_ROTATION_MOD_3_THEN_INDEX_THE_LAND_PALETTE.",
            )
        )

        target_lands = (
            (goal.land_id,)
            if goal.depth in (GoalDepth.D1, GoalDepth.D2)
            else self.meta_parents
        )
        if goal.depth == GoalDepth.D3 and resolved:
            for index, parent in enumerate(self.meta_parents):
                memories.append(
                    AtomicMemory(
                        f"{goal.id}_resolved_parent_{index}",
                        "resolved_source_value",
                        f"What color does {animal_name} have in {rendered.land(parent)}?",
                        rendered.color(self.source_color(goal.animal_id, parent)).upper() + ".",
                        merge_evidence(role_evidence, evidence_for(land=parent)),
                    )
                )
        else:
            emitted_palettes: set[str] = set()
            for index, land in enumerate(target_lands):
                spec = self.land_specs[land]
                memories.append(
                    AtomicMemory(
                        f"{goal.id}_land_factor_{index}",
                        "land_factor",
                        f"Which transformation abstraction describes {rendered.land(land)}?",
                        f"{spec.palette.upper()}_ROTATION_{spec.rotation}.",
                        evidence_for(land=land),
                    )
                )
                if spec.palette not in emitted_palettes:
                    palette = " | ".join(
                        rendered.color(color).upper() for color in PALETTES[spec.palette]
                    )
                    memories.append(
                        AtomicMemory(
                            f"{goal.id}_palette_{spec.palette}_{spec.rotation}",
                            "palette_definition",
                            f"Which visible tokens form the {spec.palette.upper()} palette?",
                            palette + ".",
                        )
                    )
                    emitted_palettes.add(spec.palette)

        if goal.depth == GoalDepth.D3:
            parents = " | ".join(rendered.land(parent) for parent in self.meta_parents)
            meta_evidence = merge_evidence(
                *(evidence_for(animal=anchor) for anchor in self.anchor_animals)
            )
            memories.extend(
                (
                    AtomicMemory(
                        f"{goal.id}_meta_parents",
                        "meta_parents",
                        f"Which ordinary lands feed {land_name}?",
                        parents + ".",
                        meta_evidence,
                    ),
                    AtomicMemory(
                        f"{goal.id}_meta_operator",
                        "meta_operator",
                        f"How does {land_name} combine its parent colors?",
                        "PIGMENT_UNION.",
                        meta_evidence,
                    ),
                )
            )
            pigment_parts = []
            for color in INTERNAL_COLORS:
                token = rendered.color(color).upper()
                components = "+".join(sorted(PIGMENTS[color]))
                pigment_parts.append(f"{token}={components}")
            memories.append(
                AtomicMemory(
                    f"{goal.id}_pigment_map",
                    "pigment_map",
                    "Which pigment components do the visible color tokens denote?",
                    " | ".join(pigment_parts) + ".",
                )
            )
        return tuple(memories)

    def context_oracle(
        self,
        goal: Goal | str,
        skin: str = "aligned",
        *,
        resolved: bool = False,
    ) -> str:
        """Goal-conditioned oracle block without an evaluator answer key.

        A D0 exact-witness leaf necessarily contains the target fact; deeper
        conditions contain only composable proof leaves.
        """
        if isinstance(goal, str):
            goal = next((candidate for candidate in self._goals if candidate.id == goal), None)
            if goal is None:
                raise KeyError(f"unknown goal {goal}")
        rendered_goal = make_skin(skin, self.animal_ids, self.source_land_ids).render_goal(goal)
        lines = ["Verified atomic memory reads:"]
        lines.extend(f"- {memory.qa_line()}" for memory in self.atomic_memories_for(
            goal, skin, resolved=resolved
        ))
        lines.append("")
        lines.append(rendered_goal.question)
        return "\n".join(lines)

    def render(
        self,
        skin: str = "aligned",
        *,
        include_answers: bool = False,
    ) -> RenderedWorld:
        """Return the public surface view.

        Answers require an explicit evaluator-only opt-in.  Latent structure,
        proof graphs, and oracle memories are never attached to this object.
        """
        rendered = make_skin(skin, self.animal_ids, self.source_land_ids)
        return RenderedWorld(
            skin=skin,
            observations=tuple(
                rendered.render_observation(observation)
                for observation in self._lifetime.observations
            ),
            goals=tuple(
                rendered.render_goal(goal, include_answer=include_answers)
                for goal in self._goals
            ),
        )

    def verify_claim(
        self,
        claim: MemoryClaim,
        evidence_ids: Sequence[str],
        *,
        allow_counterfactual: bool = False,
        budget: VerificationBudget | None = None,
    ) -> VerificationResult:
        from .verifier import ClaimVerifier

        return ClaimVerifier(self).verify(
            claim,
            evidence_ids,
            allow_counterfactual=allow_counterfactual,
            budget=budget,
        )

    def start_reachout(
        self,
        skin: str = "aligned",
        *,
        max_actions: int | None = None,
        allow_eval_targets: bool = False,
    ):
        """Open a priced active-experience session over public surface names."""
        from .reachout import ReachoutSession

        return ReachoutSession(
            self,
            skin,
            max_actions=max_actions,
            allow_eval_targets=allow_eval_targets,
        )

    def world_fingerprint(self) -> str:
        payload = {
            "config": self.config.to_dict(),
            "oracle": self.oracle_memory(),
            "goals": [goal.to_dict() for goal in self._goals],
            "observations": [o.to_dict() for o in self._lifetime.observations],
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(encoded).hexdigest()

    def manifest_summary(self) -> dict[str, Any]:
        return {
            "config": self.config.to_dict(),
            "world_fingerprint": self.world_fingerprint(),
            "n_observations": len(self._lifetime.observations),
            "n_episodes": len(self._lifetime.episodes),
            "goal_counts": {
                depth.value: len(self.eval_goals(depth)) for depth in GoalDepth
            },
            "goal_kind_counts": {
                depth.value: {
                    color: sum(
                        goal.answer_color_id == color for goal in self.eval_goals(depth)
                    )
                    for color in INTERNAL_COLORS
                    if any(
                        goal.answer_color_id == color for goal in self.eval_goals(depth)
                    )
                }
                for depth in GoalDepth
            },
            "skins": list(all_skin_names()),
        }

    # --------------------------------------------------------------- integrity
    def _validate(self) -> None:
        evidence_ids = set(self._lifetime.observation_map())
        witnessed = self._lifetime.witnessed_cells()
        for goal in self._goals:
            if self.answer(goal.animal_id, goal.land_id) != goal.answer_color_id:
                raise ValueError(f"{goal.id}: stale answer")
            if goal.depth == GoalDepth.D0 and goal.cell() not in witnessed:
                raise ValueError(f"{goal.id}: D0 cell was not witnessed")
            if goal.depth != GoalDepth.D0 and goal.cell() in witnessed:
                raise ValueError(f"{goal.id}: held-out cell leaked into lifetime")
            self._proofs[goal.proof_id].validate(evidence_ids)
        shapes_by_depth = {
            depth: {self.proof_for(goal).canonical_shape() for goal in self.eval_goals(depth)}
            for depth in GoalDepth
        }
        for left, right in itertools.combinations(GoalDepth, 2):
            if shapes_by_depth[left] & shapes_by_depth[right]:
                raise ValueError(f"proof shapes overlap for {left} and {right}")
        for skin_name in all_skin_names():
            view = self.render(skin_name)
            raw_text = "\n".join(observation.text for observation in view.observations)
            forbidden = tuple(self.animal_ids) + tuple(self.source_land_ids) + (
                self.meta_land_id,
                "animal_role",
                "land_palette_transform",
                "proof_goal",
            )
            if any(token in raw_text for token in forbidden):
                raise ValueError(f"{skin_name} raw text leaks latent identifiers")


def load_default(seed: int = 0) -> SemanticWorld:
    return SemanticWorld(WorldConfig(seed=seed))
