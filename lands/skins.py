"""Isomorphic textual skins over one latent Semantic World."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from .model import Goal, GoalDepth, Observation, RenderedGoal, RenderedObservation


INTERNAL_COLORS = (
    "red",
    "yellow",
    "blue",
    "orange",
    "green",
    "purple",
    "brown",
)

_ANIMALS = (
    "cow", "fox", "frog", "raven", "horse", "rabbit", "owl", "turtle",
    "sheep", "tiger", "panda", "dolphin", "lizard", "goat", "otter",
    "badger", "moose", "parrot", "yak", "seal", "deer", "beaver",
    "penguin", "llama", "gecko", "donkey", "swan", "mole", "alpaca",
    "crane",
)
_NEUTRAL_ENTITIES = (
    "mivak", "toren", "pelu", "sarn", "kivra", "dovel", "nema", "zurin",
    "fesk", "luma", "brin", "tovel", "jasu", "wex", "qorin", "havel",
    "prax", "sumi", "kelvo", "narin", "yaro", "bexi", "coval", "tiru",
    "vanna", "resk", "omel", "darsa", "fenic", "julo",
)
_LANDS = (
    "Candyland", "Mandyland", "Dandyland", "Randyland", "Sunnyland",
    "Moonland",
)
_NEUTRAL_LANDS = ("Zorval", "Kethra", "Pelune", "Marnic", "Vosset", "Ibrin")


@dataclass(frozen=True)
class Skin:
    name: str
    animals: Mapping[str, str]
    lands: Mapping[str, str]
    colors: Mapping[str, str]
    meta_land: str
    neutral_ontology: bool = False

    def animal(self, animal_id: str) -> str:
        return self.animals[animal_id]

    def land(self, land_id: str) -> str:
        if land_id == "land_meta":
            return self.meta_land
        return self.lands[land_id]

    def color(self, color_id: str) -> str:
        return self.colors[color_id]

    def decode_color(self, surface: str) -> str | None:
        wanted = surface.strip().lower().rstrip(".!,;:")
        for internal, rendered in self.colors.items():
            if rendered.lower() == wanted:
                return internal
        return None

    def render_observation(self, observation: Observation) -> RenderedObservation:
        animal = self.animal(observation.animal_id)
        land = self.land(observation.land_id)
        color = self.color(observation.color_id)
        if self.neutral_ontology:
            text = (
                f"[{observation.id} | {observation.episode_id}] During the visit "
                f"to zone {land}, "
                f"entity {animal} has state-token {color}."
            )
        else:
            text = (
                f"[{observation.id} | {observation.episode_id}] During the visit "
                f"to {land}, you see "
                f"the {animal}. Its coat is {color}."
            )
        return RenderedObservation(observation.id, observation.episode_id, text)

    def render_goal(self, goal: Goal, *, include_answer: bool = False) -> RenderedGoal:
        animal = self.animal(goal.animal_id)
        land = self.land(goal.land_id)
        answer = self.color(goal.answer_color_id)
        if self.neutral_ontology:
            question = (
                f"In zone {land}, what state-token does entity {animal} have? "
                "Answer with exactly one state-token."
            )
        else:
            question = (
                f"In {land}, what color is the {animal}? "
                "Answer with exactly one color word."
            )
        return RenderedGoal(goal.id, question, answer if include_answer else None)

    def palette_name(self, palette: str) -> str:
        if self.neutral_ontology:
            return "triad-alpha" if palette == "primary" else "triad-beta"
        return palette


def make_skin(name: str, animal_ids: Sequence[str], land_ids: Sequence[str]) -> Skin:
    if len(animal_ids) > len(_ANIMALS):
        raise ValueError(f"skin supports at most {len(_ANIMALS)} animals")
    if len(land_ids) > len(_LANDS):
        raise ValueError(f"skin supports at most {len(_LANDS)} source lands")

    if name == "aligned":
        return Skin(
            name=name,
            animals=dict(zip(animal_ids, _ANIMALS)),
            lands=dict(zip(land_ids, _LANDS)),
            colors={color: color for color in INTERNAL_COLORS},
            meta_land="Blendyland",
        )
    if name == "neutral":
        neutral_colors = ("sava", "norel", "tivik", "pelan", "joru", "wexi", "droma")
        return Skin(
            name=name,
            animals=dict(zip(animal_ids, _NEUTRAL_ENTITIES)),
            lands=dict(zip(land_ids, _NEUTRAL_LANDS)),
            colors=dict(zip(INTERNAL_COLORS, neutral_colors)),
            meta_land="Ulvane",
            neutral_ontology=True,
        )
    if name == "conflicting":
        # A full derangement: conventional words denote the wrong pigments.
        rendered = ("green", "purple", "orange", "blue", "red", "brown", "yellow")
        return Skin(
            name=name,
            animals=dict(zip(animal_ids, _ANIMALS)),
            lands=dict(zip(land_ids, _LANDS)),
            colors=dict(zip(INTERNAL_COLORS, rendered)),
            meta_land="Separateland",
        )
    raise ValueError(f"unknown skin {name!r}; expected aligned, neutral, conflicting")


def all_skin_names() -> tuple[str, ...]:
    return "aligned", "neutral", "conflicting"


def depth_instruction(depth: GoalDepth) -> str:
    return {
        GoalDepth.D0: "situated lookup",
        GoalDepth.D1: "local projection",
        GoalDepth.D2: "cross-palette composition",
        GoalDepth.D3: "meta-rule composition",
    }[depth]
