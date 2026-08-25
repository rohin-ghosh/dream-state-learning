"""Priced, provenance-preserving experiments beyond the fixed lifetime."""

from __future__ import annotations

from typing import TYPE_CHECKING, Sequence

from .model import (
    MemoryClaim,
    Observation,
    ReachoutBudget,
    RenderedObservation,
    VerificationBudget,
    VerificationResult,
)
from .skins import make_skin

if TYPE_CHECKING:
    from .world import SemanticWorld


class ReachoutSession:
    """A small active-experience budget with a public surface interface.

    Exact evaluation cells are blocked by default.  Each permitted action
    creates a new provenance-bearing observation that can support subsequent
    witnessed or entailed claims.  This is world experience, never a free
    verifier/oracle query.
    """

    def __init__(
        self,
        world: "SemanticWorld",
        skin_name: str = "aligned",
        *,
        max_actions: int | None = None,
        allow_eval_targets: bool = False,
    ):
        self.world = world
        self.skin_name = skin_name
        self.skin = make_skin(skin_name, world.animal_ids, world.source_land_ids)
        limit = world.config.max_reachout_actions if max_actions is None else max_actions
        if limit < 0:
            raise ValueError("max_actions cannot be negative")
        self.budget = ReachoutBudget(limit)
        self.allow_eval_targets = allow_eval_targets
        self._animal_for = {
            surface: internal for internal, surface in self.skin.animals.items()
        }
        self._land_for = {
            surface: internal for internal, surface in self.skin.lands.items()
        }
        self._land_for[self.skin.meta_land] = world.meta_land_id
        self._observations: list[Observation] = []
        self._rendered: list[RenderedObservation] = []
        self._eval_cells = {goal.cell() for goal in world.eval_goals()}

    def policy(self) -> dict[str, object]:
        return {
            "action_grammar": "VISIT | animal=<animal> | land=<land>",
            "max_actions": self.budget.max_actions,
            "exact_evaluation_targets_allowed": self.allow_eval_targets,
            "accounting": "each visit is one additional experience",
        }

    def act(self, animal: str, land: str) -> RenderedObservation:
        """Visit one surface cell and return its newly witnessed outcome."""
        if animal not in self._animal_for:
            raise ValueError(f"unknown surface animal {animal!r}")
        if land not in self._land_for:
            raise ValueError(f"unknown surface land {land!r}")
        animal_id = self._animal_for[animal]
        land_id = self._land_for[land]
        if not self.allow_eval_targets and (animal_id, land_id) in self._eval_cells:
            raise PermissionError("exact evaluation target visits are disabled")
        if not self.budget.consume():
            raise RuntimeError("reachout action budget exhausted")

        index = len(self._observations)
        cell = (animal_id, land_id)
        previously_seen = cell in self.world.sample_lifetime().witnessed_cells() or any(
            observation.cell() == cell for observation in self._observations
        )
        observation = Observation(
            id=f"reachout_obs_{index:05d}",
            episode_id=f"reachout_episode_{index:04d}",
            step=0,
            animal_id=animal_id,
            land_id=land_id,
            color_id=self.world.answer(animal_id, land_id),
            phase="reachout",
            repeated=previously_seen,
        )
        rendered = self.skin.render_observation(observation)
        self._observations.append(observation)
        self._rendered.append(rendered)
        return rendered

    @property
    def rendered_observations(self) -> tuple[RenderedObservation, ...]:
        return tuple(self._rendered)

    @property
    def evidence_ids(self) -> tuple[str, ...]:
        return tuple(observation.id for observation in self._observations)

    def verify_claim(
        self,
        claim: MemoryClaim,
        evidence_ids: Sequence[str],
        *,
        allow_counterfactual: bool = False,
        budget: VerificationBudget | None = None,
    ) -> VerificationResult:
        from .verifier import ClaimVerifier

        return ClaimVerifier(self.world, self._observations).verify(
            claim,
            evidence_ids,
            allow_counterfactual=allow_counterfactual,
            budget=budget,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "skin": self.skin_name,
            "policy": self.policy(),
            "used_actions": self.budget.used_actions,
            "remaining_actions": self.budget.remaining,
            "observations": [record.to_dict() for record in self._rendered],
        }
