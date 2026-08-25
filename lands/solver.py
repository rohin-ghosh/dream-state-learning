"""CPU ceilings and controls for the Semantic World instrument.

`FactorSolver` is intentionally given the public grammar but not hidden roles,
land transforms, or meta parents.  It recovers those consequences from cited
observations by constraint propagation.
"""

from __future__ import annotations

from dataclasses import dataclass
import itertools
from typing import Callable, Iterable, Mapping, Sequence

from .model import AtomicMemory, Goal, GoalDepth, Observation
from .skins import make_skin
from .world import PALETTES, SemanticWorld, blend_colors


def _color_coordinate(color: str) -> tuple[str, int] | None:
    for palette, colors in PALETTES.items():
        if color in colors:
            return palette, colors.index(color)
    return None


@dataclass(frozen=True)
class SolverDiagnostics:
    valid: bool
    source_components: int
    known_animals: int
    known_lands: int
    meta_examples: int
    meta_candidates: tuple[tuple[str, ...], ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "valid": self.valid,
            "source_components": self.source_components,
            "known_animals": self.known_animals,
            "known_lands": self.known_lands,
            "meta_examples": self.meta_examples,
            "meta_candidates": [list(candidate) for candidate in self.meta_candidates],
        }


class FactorSolver:
    """Infer factor consequences from observations under the public grammar."""

    def __init__(self, world: SemanticWorld, observations: Iterable[Observation]):
        self.source_land_ids = world.source_land_ids
        self.meta_land_id = world.meta_land_id
        self.meta_parent_count = world.config.meta_parent_count
        self._observations = tuple(observations)
        self._valid = True
        self._node_value: dict[tuple[str, str], int] = {}
        self._component: dict[tuple[str, str], int] = {}
        self._land_palette: dict[str, str] = {}
        self._meta_observations: dict[str, str] = {}
        self._meta_candidates: tuple[tuple[str, ...], ...] = ()
        self._fit_source_graph()
        self._fit_meta_rule()

    def _fit_source_graph(self) -> None:
        # Edge equation: animal_role + land_rotation = observed_color_index mod 3.
        adjacency: dict[tuple[str, str], list[tuple[tuple[str, str], int]]] = {}
        seen_cells: dict[tuple[str, str], str] = {}
        for observation in self._observations:
            if observation.land_id == self.meta_land_id:
                previous = self._meta_observations.get(observation.animal_id)
                if previous is not None and previous != observation.color_id:
                    self._valid = False
                self._meta_observations[observation.animal_id] = observation.color_id
                continue
            if observation.land_id not in self.source_land_ids:
                self._valid = False
                continue
            coordinate = _color_coordinate(observation.color_id)
            if coordinate is None:
                self._valid = False
                continue
            palette, index = coordinate
            previous_palette = self._land_palette.get(observation.land_id)
            if previous_palette is not None and previous_palette != palette:
                self._valid = False
            self._land_palette[observation.land_id] = palette
            cell = observation.cell()
            previous_color = seen_cells.get(cell)
            if previous_color is not None and previous_color != observation.color_id:
                self._valid = False
            seen_cells[cell] = observation.color_id
            animal_node = ("animal", observation.animal_id)
            land_node = ("land", observation.land_id)
            adjacency.setdefault(animal_node, []).append((land_node, index))
            adjacency.setdefault(land_node, []).append((animal_node, index))

        component_id = 0
        for start in sorted(adjacency):
            if start in self._node_value:
                continue
            self._node_value[start] = 0
            self._component[start] = component_id
            queue = [start]
            while queue:
                node = queue.pop(0)
                for neighbor, color_index in adjacency[node]:
                    # Both node types use their native variable.  The edge is
                    # symmetric because x + y = color_index (mod 3).
                    expected = (color_index - self._node_value[node]) % 3
                    if neighbor in self._node_value:
                        if self._node_value[neighbor] != expected:
                            self._valid = False
                    else:
                        self._node_value[neighbor] = expected
                        self._component[neighbor] = component_id
                        queue.append(neighbor)
            component_id += 1

    def predict_source(self, animal_id: str, land_id: str) -> str | None:
        if not self._valid:
            return None
        animal_node = ("animal", animal_id)
        land_node = ("land", land_id)
        if animal_node not in self._node_value or land_node not in self._node_value:
            return None
        if self._component[animal_node] != self._component[land_node]:
            return None
        palette = self._land_palette.get(land_id)
        if palette is None:
            return None
        index = (self._node_value[animal_node] + self._node_value[land_node]) % 3
        return PALETTES[palette][index]

    def animal_role_delta(self, left: str, right: str) -> int | None:
        left_node = ("animal", left)
        right_node = ("animal", right)
        if left_node not in self._node_value or right_node not in self._node_value:
            return None
        if self._component[left_node] != self._component[right_node]:
            return None
        return (self._node_value[right_node] - self._node_value[left_node]) % 3

    def land_relation(self, left: str, right: str) -> dict[str, object] | None:
        left_node = ("land", left)
        right_node = ("land", right)
        if left_node not in self._node_value or right_node not in self._node_value:
            return None
        if self._component[left_node] != self._component[right_node]:
            return None
        if left not in self._land_palette or right not in self._land_palette:
            return None
        return {
            "left_palette": self._land_palette[left],
            "right_palette": self._land_palette[right],
            "rotation_delta": (
                self._node_value[right_node] - self._node_value[left_node]
            )
            % 3,
        }

    def _fit_meta_rule(self) -> None:
        if not self._valid or len(self._meta_observations) < 3:
            return
        accepted = []
        for parents in itertools.combinations(
            self.source_land_ids, self.meta_parent_count
        ):
            matches = True
            for animal, observed_color in self._meta_observations.items():
                source_colors = [self.predict_source(animal, land) for land in parents]
                if any(color is None for color in source_colors):
                    matches = False
                    break
                predicted = blend_colors(
                    color for color in source_colors if color is not None
                )
                if predicted != observed_color:
                    matches = False
                    break
            if matches:
                accepted.append(tuple(parents))
        self._meta_candidates = tuple(accepted)

    def predict(self, animal_id: str, land_id: str) -> str | None:
        if land_id != self.meta_land_id:
            return self.predict_source(animal_id, land_id)
        if not self._meta_candidates:
            return None
        predictions = []
        for parents in self._meta_candidates:
            source_colors = [self.predict_source(animal_id, land) for land in parents]
            if any(color is None for color in source_colors):
                return None
            predictions.append(
                blend_colors(color for color in source_colors if color is not None)
            )
        return predictions[0] if len(set(predictions)) == 1 else None

    def diagnostics(self) -> SolverDiagnostics:
        components = set(self._component.values())
        return SolverDiagnostics(
            valid=self._valid,
            source_components=len(components),
            known_animals=sum(kind == "animal" for kind, _ in self._node_value),
            known_lands=sum(kind == "land" for kind, _ in self._node_value),
            meta_examples=len(self._meta_observations),
            meta_candidates=self._meta_candidates,
        )


class ObservedLookupSolver:
    def __init__(self, observations: Iterable[Observation]):
        self._cells: dict[tuple[str, str], str] = {}
        for observation in observations:
            previous = self._cells.get(observation.cell())
            if previous is not None and previous != observation.color_id:
                raise ValueError(f"inconsistent witnessed cell {observation.cell()}")
            self._cells[observation.cell()] = observation.color_id

    def predict(self, animal_id: str, land_id: str) -> str | None:
        return self._cells.get((animal_id, land_id))


class OracleSolver:
    """Compute from exported oracle memories rather than calling world.answer."""

    def __init__(self, oracle_memory: Mapping[str, object]):
        self._roles = dict(oracle_memory["animal_roles"])  # type: ignore[arg-type]
        self._land_specs = dict(oracle_memory["land_specs"])  # type: ignore[arg-type]
        self._meta = dict(oracle_memory["meta"])  # type: ignore[arg-type]

    def predict(self, animal_id: str, land_id: str) -> str | None:
        if animal_id not in self._roles:
            return None
        role = int(self._roles[animal_id])

        def source(target_land: str) -> str:
            spec = dict(self._land_specs[target_land])
            return PALETTES[str(spec["palette"])][
                (role + int(spec["rotation"])) % 3
            ]

        if land_id in self._land_specs:
            return source(land_id)
        if land_id == self._meta.get("land_id"):
            parents = tuple(self._meta["parents"])  # type: ignore[arg-type]
            return blend_colors(source(parent) for parent in parents)
        return None


def compose_atomic_answer(
    world: SemanticWorld,
    goal: Goal,
    skin_name: str = "aligned",
    *,
    resolved: bool = False,
) -> str:
    """Deterministically audit that the emitted one-hop leaves are sufficient.

    This is not a model baseline.  It consumes the same positive atomic memory
    records as the context-oracle prompt and performs only their declared
    arithmetic/union operations.
    """
    skin = make_skin(skin_name, world.animal_ids, world.source_land_ids)
    memories = world.atomic_memories_for(goal, skin_name, resolved=resolved)
    by_kind: dict[str, list[AtomicMemory]] = {}
    for memory in memories:
        by_kind.setdefault(memory.kind, []).append(memory)
    if goal.depth == GoalDepth.D0:
        answer = by_kind["witnessed_cell"][0].answer.rstrip(".").lower()
        decoded = skin.decode_color(answer)
        if decoded is None:
            raise ValueError("D0 atomic answer is not a skin color")
        return decoded

    position_text = by_kind["animal_position"][0].answer.rstrip(".")
    position = int(position_text.rsplit("_", 1)[1])
    palette_tokens = {}
    for memory in by_kind.get("palette_definition", []):
        palette = "primary" if "PRIMARY" in memory.question else "secondary"
        palette_tokens[palette] = tuple(
            token.strip().lower() for token in memory.answer.rstrip(".").split("|")
        )

    def source_from_factor(land_id: str) -> str:
        surface_land = skin.land(land_id)
        factor = next(
            memory
            for memory in by_kind["land_factor"]
            if surface_land in memory.question
        )
        label = factor.answer.rstrip(".")
        palette_name, rotation_text = label.split("_ROTATION_")
        palette_name = palette_name.lower()
        rotation = int(rotation_text)
        token = palette_tokens[palette_name][(position + rotation) % 3]
        decoded = skin.decode_color(token)
        if decoded is None:
            raise ValueError("factor composition emitted an unknown color")
        return decoded

    if goal.depth in (GoalDepth.D1, GoalDepth.D2):
        return source_from_factor(goal.land_id)

    parent_memory = by_kind["meta_parents"][0]
    reverse_lands = {skin.land(land): land for land in world.source_land_ids}
    parent_surfaces = [
        value.strip() for value in parent_memory.answer.rstrip(".").split("|")
    ]
    parent_ids = tuple(reverse_lands[value] for value in parent_surfaces)
    if by_kind["meta_operator"][0].answer != "PIGMENT_UNION.":
        raise ValueError("unsupported atomic meta operator")
    if "pigment_map" not in by_kind:
        raise ValueError("meta context omitted the visible pigment map")

    if resolved:
        source_colors = []
        for parent in parent_ids:
            surface_land = skin.land(parent)
            memory = next(
                memory
                for memory in by_kind["resolved_source_value"]
                if surface_land in memory.question
            )
            decoded = skin.decode_color(memory.answer.rstrip(".").lower())
            if decoded is None:
                raise ValueError("resolved parent emitted an unknown color")
            source_colors.append(decoded)
    else:
        source_colors = [source_from_factor(parent) for parent in parent_ids]
    return blend_colors(source_colors)


def _score_goals(
    goals: Sequence[Goal], predictor: Callable[[Goal], str | None]
) -> dict[str, object]:
    by_depth: dict[str, dict[str, float | int]] = {}
    for depth in GoalDepth:
        subset = [goal for goal in goals if goal.depth == depth]
        predictions = [predictor(goal) for goal in subset]
        answered = sum(prediction is not None for prediction in predictions)
        correct = sum(
            prediction == goal.answer_color_id
            for goal, prediction in zip(subset, predictions)
        )
        total = len(subset)
        by_depth[depth.value] = {
            "total": total,
            "answered": answered,
            "correct": correct,
            "coverage": round(answered / total, 6) if total else 0.0,
            "accuracy": round(correct / total, 6) if total else 0.0,
            "conditional_accuracy": round(correct / answered, 6) if answered else 0.0,
        }
    total = len(goals)
    answered = sum(int(row["answered"]) for row in by_depth.values())
    correct = sum(int(row["correct"]) for row in by_depth.values())
    return {
        "overall": {
            "total": total,
            "answered": answered,
            "correct": correct,
            "coverage": round(answered / total, 6) if total else 0.0,
            "accuracy": round(correct / total, 6) if total else 0.0,
            "conditional_accuracy": round(correct / answered, 6) if answered else 0.0,
        },
        "by_depth": by_depth,
    }


def evaluate_world(world: SemanticWorld) -> dict[str, object]:
    """Run CPU instrument baselines.  Abstention counts as incorrect."""
    observations = world.sample_lifetime().observations
    goals = world.eval_goals()
    budget = world.config.context_observation_budget
    lookup = ObservedLookupSolver(observations)
    recent = FactorSolver(world, observations[-budget:])
    full = FactorSolver(world, observations)
    oracle = OracleSolver(world.oracle_memory())

    def best_window_prediction(goal: Goal) -> str | None:
        predictions = []
        for start in range(0, max(1, len(observations) - budget + 1)):
            solver = FactorSolver(world, observations[start:start + budget])
            prediction = solver.predict(goal.animal_id, goal.land_id)
            if prediction is not None:
                predictions.append(prediction)
        # A deployable window selector has no answer key: require consensus.
        return predictions[0] if predictions and len(set(predictions)) == 1 else None

    def oracle_window_ceiling(goal: Goal) -> str | None:
        # Explicit upper bound: did *any* contiguous budget-sized window carry
        # enough evidence?  This may inspect the answer and is not a baseline.
        for start in range(0, max(1, len(observations) - budget + 1)):
            solver = FactorSolver(world, observations[start:start + budget])
            prediction = solver.predict(goal.animal_id, goal.land_id)
            if prediction == goal.answer_color_id:
                return prediction
        return None

    methods = {
        "observed_lookup": _score_goals(
            goals, lambda goal: lookup.predict(goal.animal_id, goal.land_id)
        ),
        "recent_context": _score_goals(
            goals, lambda goal: recent.predict(goal.animal_id, goal.land_id)
        ),
        "best_window_consensus": _score_goals(goals, best_window_prediction),
        "oracle_selected_window_ceiling": _score_goals(goals, oracle_window_ceiling),
        "full_lifetime_factor": _score_goals(
            goals, lambda goal: full.predict(goal.animal_id, goal.land_id)
        ),
        "oracle_structure": _score_goals(
            goals, lambda goal: oracle.predict(goal.animal_id, goal.land_id)
        ),
    }
    floors = {}
    for depth in GoalDepth:
        subset = world.eval_goals(depth)
        counts = {
            color: sum(goal.answer_color_id == color for goal in subset)
            for color in sorted({goal.answer_color_id for goal in subset})
        }
        majority = max(counts.values()) if counts else 0
        floors[depth.value] = {
            "counts": counts,
            "majority_accuracy": round(majority / len(subset), 6) if subset else 0.0,
        }
    return {
        "world_fingerprint": world.world_fingerprint(),
        "context_observation_budget": budget,
        "methods": methods,
        "majority_floors": floors,
        "diagnostics": {
            "recent_context": recent.diagnostics().to_dict(),
            "full_lifetime_factor": full.diagnostics().to_dict(),
        },
    }
