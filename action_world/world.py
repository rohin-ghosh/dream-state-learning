"""Deterministic action-conditioned world with evaluator separation.

Action World v0 is intentionally small.  It isolates three capabilities that
the original Alchemy environment entangled:

* transfer a generic inspect-before-commit procedure to a new threshold;
* infer a world-specific danger law from experienced action consequences;
* compose inferred crossings into a longer action chain.

The hidden law never appears in public text.  A session returns consequences
only for actions actually taken, which is environment feedback rather than an
in-loop counterfactual verifier.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import random
from typing import Callable, Iterable

from .model import (
    ActionDepth,
    Episode,
    Goal,
    LEGAL_ACTIONS,
    Lifetime,
    ProofGraph,
    ProofNode,
    RunResult,
    StepRecord,
    StepResult,
    Threshold,
    WorldConfig,
)


FEATURES: tuple[tuple[str, tuple[str, str]], ...] = (
    ("sigil", ("sun", "moon")),
    ("hinge", ("brass", "iron")),
    ("frame", ("oak", "stone")),
    ("draft", ("warm", "cold")),
)

THRESHOLD_NAMES = (
    "Ash Gate",
    "Birch Gate",
    "Cedar Gate",
    "Dawn Gate",
    "Elm Gate",
    "Flint Gate",
    "Grove Gate",
    "Harbor Gate",
    "Ivy Gate",
    "Juniper Gate",
    "Keystone Gate",
    "Lantern Gate",
    "Moss Gate",
    "North Gate",
    "Orchard Gate",
    "Pine Gate",
)


def _bit_patterns(width: int) -> tuple[tuple[int, ...], ...]:
    return tuple(itertools.product((0, 1), repeat=width))


def _law_candidates(
    labeled_patterns: Iterable[tuple[tuple[int, ...], str]],
) -> tuple[tuple[tuple[int, ...], int], ...]:
    labels = tuple(labeled_patterns)
    width = len(labels[0][0]) if labels else len(FEATURES)
    result = []
    for mask in _bit_patterns(width):
        if not any(mask):
            continue
        for bias in (0, 1):
            good = True
            for bits, side in labels:
                parity = bias
                for active, bit in zip(mask, bits):
                    if active:
                        parity ^= bit
                predicted = "right" if parity else "left"
                if predicted != side:
                    good = False
                    break
            if good:
                result.append((mask, bias))
    return tuple(result)


class ActionSession:
    """One interactive attempt.  Only consequences of executed actions leak."""

    def __init__(
        self,
        world: "ActionWorld",
        goal: Goal,
        episode_id: str | None = None,
    ):
        self.world = world
        self.goal = goal
        self.episode_id = episode_id
        self.threshold_index = 0
        self.opened = False
        self.guarded: str | None = None
        self.inspected: dict[str, str] = {}
        self.steps_used = 0
        self.terminal = False
        self.success = False
        self.terminal_reason = "running"
        self.actions: list[str] = []
        self.observations: list[str] = []
        self.total_reward = 0.0

    @property
    def threshold(self) -> Threshold:
        return self.world.thresholds[self.goal.threshold_ids[self.threshold_index]]

    def intro(self) -> str:
        if len(self.goal.threshold_ids) == 1:
            prefix = "You need to cross one unfamiliar threshold."
        else:
            prefix = (
                f"You need to cross a corridor of {len(self.goal.threshold_ids)} "
                "thresholds in order."
            )
        return f"{prefix} {self.threshold.description()}"

    def snapshot(self) -> dict:
        return {
            "goal_id": self.goal.id,
            "threshold_index": self.threshold_index,
            "threshold_count": len(self.goal.threshold_ids),
            "threshold": self.threshold.public_dict(),
            "opened": self.opened,
            "guarded": self.guarded,
            "inspected": dict(self.inspected),
            "steps_used": self.steps_used,
            "steps_remaining": self.goal.max_steps - self.steps_used,
            "legal_actions": list(LEGAL_ACTIONS),
            "terminal": self.terminal,
            "success": self.success,
        }

    def _finish_step(
        self,
        action: str,
        observation: str,
        reward: float,
        revealed: tuple[str, str] | None = None,
    ) -> StepResult:
        self.actions.append(action)
        self.observations.append(observation)
        self.total_reward += reward
        if not self.terminal and self.steps_used >= self.goal.max_steps:
            self.terminal = True
            self.success = False
            self.terminal_reason = "budget_exhausted"
            observation += " Your action budget is exhausted before the crossing is complete."
            reward -= 0.5
            self.total_reward -= 0.5
            self.observations[-1] = observation
        return StepResult(
            action=action,
            observation=observation,
            reward=reward,
            terminal=self.terminal,
            success=self.success,
            revealed=revealed,
        )

    def step(self, action: str) -> StepResult:
        if self.terminal:
            raise RuntimeError("cannot act after the session is terminal")
        if action not in LEGAL_ACTIONS:
            raise ValueError(f"unknown action {action!r}; legal={LEGAL_ACTIONS}")
        self.steps_used += 1
        cost = -0.02

        if action == "open":
            if self.opened:
                return self._finish_step(
                    action, f"{self.threshold.name} is already open.", cost
                )
            self.opened = True
            return self._finish_step(
                action,
                f"You open {self.threshold.name}. The passage beyond is still partly occluded.",
                cost,
            )

        if action.startswith("inspect_"):
            side = action.removeprefix("inspect_")
            if not self.opened:
                return self._finish_step(
                    action,
                    "The closed threshold blocks your view; you learn nothing.",
                    cost,
                )
            status = (
                "danger" if self.world.threat_side(self.threshold.id) == side else "clear"
            )
            self.inspected[side] = status
            if status == "danger":
                observation = f"You inspect the {side} approach. A raider is waiting there."
            else:
                observation = f"You inspect the {side} approach. It is clear."
            return self._finish_step(action, observation, cost, (side, status))

        if action.startswith("guard_"):
            side = action.removeprefix("guard_")
            if not self.opened:
                return self._finish_step(
                    action,
                    "You cannot cover an approach while the threshold is closed.",
                    cost,
                )
            self.guarded = side
            return self._finish_step(
                action,
                f"You prepare to defend against an attack from the {side}.",
                cost,
            )

        # enter
        if not self.opened:
            return self._finish_step(
                action, "The closed threshold stops you.", cost
            )
        danger = self.world.threat_side(self.threshold.id)
        if self.guarded != danger:
            self.terminal = True
            self.success = False
            self.terminal_reason = "attacked"
            return self._finish_step(
                action,
                f"You enter without covering the {danger}. A concealed raider attacks you.",
                -1.0,
            )

        crossed_name = self.threshold.name
        self.threshold_index += 1
        if self.threshold_index == len(self.goal.threshold_ids):
            self.terminal = True
            self.success = True
            self.terminal_reason = "crossed"
            return self._finish_step(
                action,
                f"You cover the dangerous side and cross {crossed_name} safely.",
                1.0,
            )

        self.opened = False
        self.guarded = None
        self.inspected = {}
        return self._finish_step(
            action,
            (
                f"You cover the dangerous side and cross {crossed_name} safely. "
                f"Ahead, {self.threshold.description()}"
            ),
            cost,
        )

    def result(self) -> RunResult:
        return RunResult(
            goal_id=self.goal.id,
            actions=tuple(self.actions),
            observations=tuple(self.observations),
            total_reward=round(self.total_reward, 6),
            success=self.success,
            terminal_reason=self.terminal_reason,
        )


Policy = Callable[[dict], str]


class ActionWorld:
    """One hidden causal world and its frozen lifetime/evaluation split."""

    def __init__(self, config: WorldConfig | None = None):
        self.config = config or WorldConfig()
        self.config.validate()
        self._rng = random.Random(self.config.seed)

        masks = [
            mask
            for mask in _bit_patterns(self.config.n_feature_bits)
            if 2 <= sum(mask) <= 3
        ]
        self._law_mask = tuple(self._rng.choice(masks))
        self._law_bias = self._rng.randrange(2)

        patterns = list(_bit_patterns(self.config.n_feature_bits))
        split: tuple[list[tuple[int, ...]], list[tuple[int, ...]]] | None = None
        for _ in range(256):
            self._rng.shuffle(patterns)
            training = list(patterns[: self.config.n_training_patterns])
            held_out = list(patterns[self.config.n_training_patterns :])
            labels = [(bits, self._side_for_bits(bits)) for bits in training]
            if len(_law_candidates(labels)) == 1:
                split = training, held_out
                break
        if split is None:
            raise RuntimeError("could not construct an identifiable training split")
        self.training_patterns, self.held_out_patterns = map(tuple, split)

        names = list(THRESHOLD_NAMES)
        self._rng.shuffle(names)
        ordered_patterns = list(self.training_patterns) + list(self.held_out_patterns)
        self.thresholds: dict[str, Threshold] = {}
        self._bits_by_threshold: dict[str, tuple[int, ...]] = {}
        for index, bits in enumerate(ordered_patterns):
            threshold_id = f"threshold_{index:02d}"
            feature_values = tuple(
                (feature, values[bit]) for (feature, values), bit in zip(FEATURES, bits)
            )
            split_name = (
                "experience" if index < len(self.training_patterns) else "evaluation"
            )
            self.thresholds[threshold_id] = Threshold(
                threshold_id, names[index], feature_values, split_name
            )
            self._bits_by_threshold[threshold_id] = bits
        self.training_threshold_ids = tuple(
            threshold.id
            for threshold in self.thresholds.values()
            if threshold.split == "experience"
        )
        self.eval_threshold_ids = tuple(
            threshold.id
            for threshold in self.thresholds.values()
            if threshold.split == "evaluation"
        )

        self._lifetime = self._build_lifetime()
        self._goals, self._proofs = self._build_goals_and_proofs()
        self._validate()

    # --------------------------------------------------------------- hidden
    def _side_for_bits(self, bits: tuple[int, ...]) -> str:
        parity = self._law_bias
        for active, bit in zip(self._law_mask, bits):
            if active:
                parity ^= bit
        return "right" if parity else "left"

    def threat_side(self, threshold_id: str) -> str:
        """Evaluator/environment truth.  Never include it in model context."""
        return self._side_for_bits(self._bits_by_threshold[threshold_id])

    # ------------------------------------------------------------- lifetime
    def _training_goal(self, threshold_id: str, max_steps: int = 4) -> Goal:
        threshold = self.thresholds[threshold_id]
        return Goal(
            id=f"training_{threshold_id}_{max_steps}",
            depth=ActionDepth.A1,
            threshold_ids=(threshold_id,),
            max_steps=max_steps,
            question=f"Cross {threshold.name} safely.",
            proof_id="training_only",
        )

    def _episode_from_actions(
        self,
        episode_id: str,
        threshold_id: str,
        policy_kind: str,
        actions: Iterable[str],
        max_steps: int,
    ) -> Episode:
        session = ActionSession(
            self, self._training_goal(threshold_id, max_steps), episode_id=episode_id
        )
        intro = session.intro()
        steps = []
        for action in actions:
            result = session.step(action)
            steps.append(
                StepRecord(
                    id=f"step_{len(self._all_step_ids):05d}",
                    episode_id=episode_id,
                    step=len(steps),
                    threshold_id=threshold_id,
                    action=action,
                    observation=result.observation,
                    reward=result.reward,
                    terminal=result.terminal,
                    success=result.success,
                    revealed=result.revealed,
                )
            )
            self._all_step_ids.append(steps[-1].id)
            if result.terminal:
                break
        return Episode(
            id=episode_id,
            threshold_id=threshold_id,
            policy_kind=policy_kind,
            intro=intro,
            steps=tuple(steps),
            success=session.success,
        )

    def _build_lifetime(self) -> Lifetime:
        episodes = []
        self._all_step_ids: list[str] = []
        episode_index = 0
        for threshold_id in self.training_threshold_ids:
            if self._rng.random() < self.config.reckless_fraction:
                episodes.append(
                    self._episode_from_actions(
                        f"episode_{episode_index:04d}",
                        threshold_id,
                        "reckless",
                        ("open", "enter"),
                        max_steps=2,
                    )
                )
                episode_index += 1

            danger = self.threat_side(threshold_id)
            inspected_status = "danger" if danger == "left" else "clear"
            guarded = "guard_left" if inspected_status == "danger" else "guard_right"
            episodes.append(
                self._episode_from_actions(
                    f"episode_{episode_index:04d}",
                    threshold_id,
                    "cautious",
                    ("open", "inspect_left", guarded, "enter"),
                    max_steps=4,
                )
            )
            episode_index += 1

        # Temporal dispersion: related policies and feature patterns are not
        # handed to the dreamer as an aligned table.
        self._rng.shuffle(episodes)
        return Lifetime(tuple(episodes))

    # ---------------------------------------------------------------- goals
    def _question(self, threshold_ids: tuple[str, ...], max_steps: int) -> str:
        descriptions = " ".join(
            self.thresholds[threshold_id].description()
            for threshold_id in threshold_ids
        )
        return (
            f"Cross {len(threshold_ids)} threshold(s) in order without being attacked, "
            f"using at most {max_steps} actions. {descriptions} "
            f"At each step choose one of: {', '.join(LEGAL_ACTIONS)}."
        )

    def _build_goals_and_proofs(self) -> tuple[tuple[Goal, ...], dict[str, ProofGraph]]:
        goals: list[Goal] = []
        proofs: dict[str, ProofGraph] = {}
        n = self.config.goals_per_depth
        if len(self.eval_threshold_ids) < 2:
            raise ValueError("A3 requires at least two held-out thresholds")

        by_threshold: dict[str, list[str]] = {}
        for step in self._lifetime.steps:
            by_threshold.setdefault(step.threshold_id, []).append(step.id)
        all_experience_ids = tuple(step.id for step in self._lifetime.steps)

        def add_goal(
            depth: ActionDepth,
            threshold_ids: tuple[str, ...],
            max_steps: int,
            tags: tuple[str, ...],
        ) -> None:
            goal_id = f"goal_{len(goals):04d}"
            proof_id = f"proof_{goal_id}"
            nodes: list[ProofNode] = []
            if depth == ActionDepth.A0:
                evidence = ProofNode(
                    f"{proof_id}_experience",
                    "witnessed_action_outcomes",
                    evidence_ids=tuple(by_threshold[threshold_ids[0]]),
                )
                root = ProofNode(
                    f"{proof_id}_root",
                    "replay_direct_crossing",
                    depends_on=(evidence.id,),
                )
                nodes.extend((evidence, root))
            elif depth == ActionDepth.A1:
                evidence = ProofNode(
                    f"{proof_id}_experience",
                    "cross_threshold_contrasts",
                    evidence_ids=all_experience_ids,
                )
                schema = ProofNode(
                    f"{proof_id}_schema",
                    "inspect_then_guard_schema",
                    depends_on=(evidence.id,),
                )
                root = ProofNode(
                    f"{proof_id}_root",
                    "adaptive_unseen_crossing",
                    depends_on=(schema.id,),
                )
                nodes.extend((evidence, schema, root))
            else:
                evidence = ProofNode(
                    f"{proof_id}_experience",
                    "feature_conditioned_outcomes",
                    evidence_ids=all_experience_ids,
                )
                law = ProofNode(
                    f"{proof_id}_law",
                    "infer_world_danger_law",
                    depends_on=(evidence.id,),
                )
                crossing_nodes = []
                for index, threshold_id in enumerate(threshold_ids):
                    crossing = ProofNode(
                        f"{proof_id}_crossing_{index}",
                        "predict_and_cross_unseen_threshold",
                        depends_on=(law.id,),
                        payload={"threshold_id": threshold_id},
                    )
                    crossing_nodes.append(crossing)
                root = ProofNode(
                    f"{proof_id}_root",
                    "compose_action_chain" if len(crossing_nodes) > 1 else "direct_crossing",
                    depends_on=tuple(node.id for node in crossing_nodes),
                )
                nodes.extend((evidence, law, *crossing_nodes, root))
            proof = ProofGraph(proof_id, root.id, depth, tuple(nodes))
            goal = Goal(
                id=goal_id,
                depth=depth,
                threshold_ids=threshold_ids,
                max_steps=max_steps,
                question=self._question(threshold_ids, max_steps),
                proof_id=proof_id,
                tags=tags,
            )
            goals.append(goal)
            proofs[proof_id] = proof

        for index in range(n):
            add_goal(
                ActionDepth.A0,
                (self.training_threshold_ids[index % len(self.training_threshold_ids)],),
                3,
                ("witnessed", "tight_budget"),
            )
        for index in range(n):
            threshold_id = self.eval_threshold_ids[index % len(self.eval_threshold_ids)]
            add_goal(
                ActionDepth.A1,
                (threshold_id,),
                4,
                ("held_out_pattern", "adaptive_inspection"),
            )
        for index in range(n):
            threshold_id = self.eval_threshold_ids[index % len(self.eval_threshold_ids)]
            add_goal(
                ActionDepth.A2,
                (threshold_id,),
                3,
                ("held_out_pattern", "law_required", "tight_budget"),
            )
        for index in range(n):
            left = self.eval_threshold_ids[index % len(self.eval_threshold_ids)]
            right = self.eval_threshold_ids[(index + 1) % len(self.eval_threshold_ids)]
            add_goal(
                ActionDepth.A3,
                (left, right),
                6,
                ("held_out_patterns", "law_required", "action_chain"),
            )
        return tuple(goals), proofs

    # --------------------------------------------------------------- public
    def sample_lifetime(self) -> Lifetime:
        return self._lifetime

    def eval_goals(self, depth: ActionDepth | str | None = None) -> tuple[Goal, ...]:
        if depth is None:
            return self._goals
        wanted = ActionDepth(depth)
        return tuple(goal for goal in self._goals if goal.depth == wanted)

    def proof_for(self, goal: Goal | str) -> ProofGraph:
        selected = goal if isinstance(goal, Goal) else next(
            candidate for candidate in self._goals if candidate.id == goal
        )
        return self._proofs[selected.proof_id]

    def start(self, goal: Goal | str) -> ActionSession:
        selected = goal if isinstance(goal, Goal) else next(
            candidate for candidate in self._goals if candidate.id == goal
        )
        return ActionSession(self, selected)

    def run_policy(self, goal: Goal | str, policy: Policy) -> RunResult:
        session = self.start(goal)
        while not session.terminal:
            action = policy(session.snapshot())
            session.step(action)
        return session.result()

    def run_actions(self, goal: Goal | str, actions: Iterable[str]) -> RunResult:
        session = self.start(goal)
        for action in actions:
            if session.terminal:
                break
            session.step(action)
        if not session.terminal:
            session.terminal_reason = "plan_ended"
        return session.result()

    def public_bundle(self) -> dict:
        return {
            "schema_version": "action-world-v0.1",
            "lifetime": self._lifetime.public_dict(),
            "goals": [goal.public_dict() for goal in self._goals],
            "thresholds": [
                threshold.public_dict() for threshold in self.thresholds.values()
            ],
            "action_interface": {
                "legal_actions": list(LEGAL_ACTIONS),
                "feedback": "consequences of executed actions only",
                "counterfactual_queries": 0,
            },
        }

    def evaluator_bundle(self) -> dict:
        return {
            "schema_version": "action-world-v0.1",
            "config": self.config.to_dict(),
            "law_mask": list(self._law_mask),
            "law_bias": self._law_bias,
            "thresholds": [
                {
                    **threshold.public_dict(),
                    "split": threshold.split,
                    "bits": list(self._bits_by_threshold[threshold.id]),
                    "threat_side": self.threat_side(threshold.id),
                }
                for threshold in self.thresholds.values()
            ],
            "goals": [
                {
                    **goal.public_dict(),
                    "depth": goal.depth.value,
                    "proof_id": goal.proof_id,
                    "tags": list(goal.tags),
                }
                for goal in self._goals
            ],
            "proofs": [self.proof_for(goal).to_dict() for goal in self._goals],
        }

    def leakage_scan(self, text: str) -> tuple[str, ...]:
        forbidden = ("law_mask", "law_bias", "threat_side", "parity")
        lowered = text.lower()
        return tuple(token for token in forbidden if token in lowered)

    def world_fingerprint(self) -> str:
        payload = json.dumps(self.evaluator_bundle(), sort_keys=True).encode()
        return hashlib.sha256(payload).hexdigest()

    # ------------------------------------------------------------- integrity
    def _validate(self) -> None:
        if set(self.training_patterns) & set(self.held_out_patterns):
            raise ValueError("experience/evaluation feature patterns overlap")
        if len(_law_candidates(
            (bits, self._side_for_bits(bits)) for bits in self.training_patterns
        )) != 1:
            raise ValueError("training experience does not identify the hidden law")
        evidence_ids = {step.id for step in self._lifetime.steps}
        for goal in self._goals:
            self._proofs[goal.proof_id].validate(evidence_ids)
        public = json.dumps(self.public_bundle(), sort_keys=True)
        leaked = self.leakage_scan(public)
        if leaked:
            raise ValueError(f"public bundle leaks evaluator fields: {leaked}")
