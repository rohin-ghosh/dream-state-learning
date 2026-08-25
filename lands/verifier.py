"""Evidence-entitled dream claim verification with priced engine access."""

from __future__ import annotations

from typing import Sequence, TYPE_CHECKING

from .model import MemoryClaim, Observation, VerificationBudget, VerificationResult
from .solver import FactorSolver

if TYPE_CHECKING:
    from .world import SemanticWorld


class ClaimVerifier:
    def __init__(
        self,
        world: "SemanticWorld",
        additional_evidence: Sequence[Observation] = (),
    ):
        self.world = world
        self.additional_evidence = tuple(additional_evidence)

    def verify(
        self,
        claim: MemoryClaim,
        evidence_ids: Sequence[str],
        *,
        allow_counterfactual: bool = False,
        budget: VerificationBudget | None = None,
    ) -> VerificationResult:
        observation_map = self.world.sample_lifetime().observation_map()
        for observation in self.additional_evidence:
            if observation.id in observation_map:
                return VerificationResult(
                    False,
                    "invalid_evidence",
                    "none",
                    f"duplicate evidence id: {observation.id}",
                )
            observation_map[observation.id] = observation
        unknown = set(evidence_ids) - set(observation_map)
        if unknown:
            return VerificationResult(
                False,
                "invalid_evidence",
                "none",
                f"unknown evidence ids: {sorted(unknown)}",
            )
        cited = tuple(observation_map[evidence_id] for evidence_id in evidence_ids)
        if claim.kind == "cell":
            return self._verify_cell(
                claim,
                cited,
                allow_counterfactual=allow_counterfactual,
                budget=budget,
            )
        if claim.kind == "meta_rule":
            return self._verify_meta_rule(claim, cited)
        if claim.kind == "animal_equiv":
            return self._verify_animal_equiv(claim, cited)
        if claim.kind == "land_relation":
            return self._verify_land_relation(claim, cited)
        return VerificationResult(
            False,
            "invalid_schema",
            "none",
            f"unsupported claim kind {claim.kind!r}",
        )

    def _verify_cell(
        self,
        claim: MemoryClaim,
        cited,
        *,
        allow_counterfactual: bool,
        budget: VerificationBudget | None,
    ) -> VerificationResult:
        required = {"animal_id", "land_id", "color_id"}
        if set(claim.payload) != required:
            return VerificationResult(
                False,
                "invalid_schema",
                "none",
                f"cell claim requires exactly {sorted(required)}",
            )
        animal = str(claim.payload["animal_id"])
        land = str(claim.payload["land_id"])
        color = str(claim.payload["color_id"])
        if animal not in self.world.animal_ids:
            return VerificationResult(False, "invalid_schema", "none", "unknown animal")
        if land not in self.world.source_land_ids + (self.world.meta_land_id,):
            return VerificationResult(False, "invalid_schema", "none", "unknown land")

        witnessed = [
            observation
            for observation in cited
            if observation.animal_id == animal and observation.land_id == land
        ]
        if witnessed:
            accepted = all(observation.color_id == color for observation in witnessed)
            return VerificationResult(
                accepted,
                "accepted" if accepted else "rejected",
                "witnessed",
                "cited exact observation matches"
                if accepted
                else "cited exact observation contradicts claim",
            )

        solver = FactorSolver(self.world, cited)
        predicted = solver.predict(animal, land)
        if predicted is not None:
            accepted = predicted == color
            return VerificationResult(
                accepted,
                "accepted" if accepted else "rejected",
                "entailed",
                f"cited evidence entails {predicted}",
            )

        if not allow_counterfactual:
            return VerificationResult(
                False,
                "unsupported",
                "none",
                "claim is neither witnessed nor entailed by cited evidence",
            )
        if budget is None or not budget.consume():
            return VerificationResult(
                False,
                "budget_exhausted",
                "counterfactual",
                "counterfactual engine query was not budgeted",
            )
        truth = self.world.answer(animal, land)
        accepted = truth == color
        return VerificationResult(
            accepted,
            "accepted" if accepted else "rejected",
            "counterfactual",
            f"priced engine query returned {truth}",
            counterfactual_queries=1,
        )

    def _verify_meta_rule(self, claim: MemoryClaim, cited) -> VerificationResult:
        required = {"operator", "parents"}
        if set(claim.payload) != required:
            return VerificationResult(
                False,
                "invalid_schema",
                "none",
                f"meta_rule requires exactly {sorted(required)}",
            )
        operator = str(claim.payload["operator"])
        parents = tuple(str(parent) for parent in claim.payload["parents"])
        if operator != "pigment_union":
            return VerificationResult(
                False, "invalid_schema", "none", "v0 supports only pigment_union"
            )
        if (
            len(parents) != self.world.config.meta_parent_count
            or len(set(parents)) != len(parents)
            or any(parent not in self.world.source_land_ids for parent in parents)
        ):
            return VerificationResult(
                False, "invalid_schema", "none", "invalid meta parent set"
            )
        solver = FactorSolver(self.world, cited)
        diagnostics = solver.diagnostics()
        candidates = {tuple(sorted(candidate)) for candidate in diagnostics.meta_candidates}
        proposed = tuple(sorted(parents))
        if not candidates:
            return VerificationResult(
                False,
                "unsupported",
                "none",
                "cited evidence does not identify any executable meta rule",
            )
        if proposed not in candidates:
            return VerificationResult(
                False,
                "rejected",
                "entailed",
                "proposed rule contradicts cited meta examples",
            )
        if len(candidates) != 1:
            return VerificationResult(
                False,
                "underdetermined",
                "none",
                f"claim is one of {len(candidates)} evidence-consistent rules",
            )
        return VerificationResult(
            True,
            "accepted",
            "entailed",
            "cited lived evidence uniquely identifies the meta rule",
        )

    def _verify_animal_equiv(self, claim: MemoryClaim, cited) -> VerificationResult:
        if set(claim.payload) != {"left", "right"}:
            return VerificationResult(
                False, "invalid_schema", "none", "animal_equiv requires left/right"
            )
        left, right = str(claim.payload["left"]), str(claim.payload["right"])
        if (
            left == right
            or left not in self.world.animal_ids
            or right not in self.world.animal_ids
        ):
            return VerificationResult(
                False, "invalid_schema", "none", "invalid animal pair"
            )
        delta = FactorSolver(self.world, cited).animal_role_delta(left, right)
        if delta is None:
            return VerificationResult(
                False, "unsupported", "none", "cited evidence does not connect the animals"
            )
        accepted = delta == 0
        return VerificationResult(
            accepted,
            "accepted" if accepted else "rejected",
            "entailed",
            "animals share one latent role" if accepted else f"role delta is {delta}",
        )

    def _verify_land_relation(self, claim: MemoryClaim, cited) -> VerificationResult:
        required = {
            "left",
            "right",
            "left_palette",
            "right_palette",
            "rotation_delta",
        }
        if set(claim.payload) != required:
            return VerificationResult(
                False, "invalid_schema", "none", "land_relation schema mismatch"
            )
        left, right = str(claim.payload["left"]), str(claim.payload["right"])
        if left >= right:
            return VerificationResult(
                False,
                "invalid_schema",
                "none",
                "land relation must use canonical internal order",
            )
        if left not in self.world.source_land_ids or right not in self.world.source_land_ids:
            return VerificationResult(False, "invalid_schema", "none", "unknown land")
        relation = FactorSolver(self.world, cited).land_relation(left, right)
        if relation is None:
            return VerificationResult(
                False, "unsupported", "none", "cited evidence does not connect the lands"
            )
        proposed = {
            "left_palette": str(claim.payload["left_palette"]),
            "right_palette": str(claim.payload["right_palette"]),
            "rotation_delta": int(claim.payload["rotation_delta"]),
        }
        accepted = relation == proposed
        return VerificationResult(
            accepted,
            "accepted" if accepted else "rejected",
            "entailed",
            "cited evidence entails the canonical land relation"
            if accepted
            else f"cited evidence entails {relation}",
        )
