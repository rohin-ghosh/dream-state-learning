"""
Sleep-phase orchestrator for the Dream-State Learning system.

Triggered after every K tasks to run the full consolidation pipeline:
  routing -> semantic distillation -> LoRA fine-tuning -> checkpoint safety
  evaluation -> accept/revert.
"""

from __future__ import annotations

import json
import logging
import os
from collections import defaultdict
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Callable

from dream_state.config import LoRAConfig, SleepConfig
from dream_state.memory.episodic import EpisodicMemory
from dream_state.memory.features import TrajectoryFeatures
from dream_state.memory.semantic import SemanticMemory
from dream_state.agent.react_agent import ReActAgent
from dream_state.environments.alfworld_env import EpisodeResult

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# RoutingDecision
# ---------------------------------------------------------------------------


class RoutingDecision(IntEnum):
    """Consolidation routing decision for a single trajectory."""

    EPISODIC = 0
    SEMANTIC = 1
    PARAMETRIC = 2
    NONE = 3


# ---------------------------------------------------------------------------
# SleepResult
# ---------------------------------------------------------------------------


@dataclass
class SleepResult:
    """Summary of a completed sleep-phase consolidation run."""

    n_episodic: int
    n_semantic: int
    n_parametric: int
    n_skipped: int
    lora_accepted: bool
    new_adapter_path: str | None
    checkpoint_delta: dict[str, float] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# SleepController
# ---------------------------------------------------------------------------


class SleepController:
    """Decides whether a sleep phase should be triggered at a given task index."""

    def __init__(
        self,
        sleep_config: SleepConfig,
        lora_config: LoRAConfig,
        output_dir: str,
    ) -> None:
        self.sleep_config = sleep_config
        self.lora_config = lora_config
        self.output_dir = output_dir

    def should_sleep(self, task_idx: int) -> bool:
        """Return True if a sleep phase should be triggered after *task_idx*.

        A sleep phase fires whenever task_idx is a positive multiple of
        ``sleep_config.trigger_every_k_tasks``.

        Args:
            task_idx: Zero-based index of the most recently completed task.

        Returns:
            True iff task_idx > 0 and task_idx is divisible by K.
        """
        k = self.sleep_config.trigger_every_k_tasks
        return task_idx > 0 and task_idx % k == 0


# ---------------------------------------------------------------------------
# SleepPhase
# ---------------------------------------------------------------------------


class SleepPhase:
    """Full consolidation pipeline executed during a sleep phase.

    Steps
    -----
    a. Episodic consolidation  — store EPISODIC trajectories in episodic memory.
    b. Semantic consolidation  — distil SEMANTIC trajectories into semantic memory.
    c. Parametric consolidation — LoRA fine-tune on PARAMETRIC trajectories with
       backward-transfer-weighted (BWT) accept/revert logic.
    """

    # File that persists accepted checkpoint metrics between sleep phases.
    _PRIOR_METRICS_FILENAME = "prior_checkpoint_metrics.json"

    def __init__(
        self,
        sleep_config: SleepConfig,
        lora_config: LoRAConfig,
        model_name: str,
        output_dir: str,
        device: str = "cuda",
    ) -> None:
        self.sleep_config = sleep_config
        self.lora_config = lora_config
        self.model_name = model_name
        self.output_dir = output_dir
        self.device = device

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def run(
        self,
        pending_trajectories: list[tuple[EpisodeResult, RoutingDecision, TrajectoryFeatures]],
        episodic_memory: EpisodicMemory,
        semantic_memory: SemanticMemory,
        agent: ReActAgent,
        prior_adapter_paths: list[str],
        task_id: int,
        holdout_evaluator: Callable[[str], dict[str, float]],
    ) -> SleepResult:
        """Execute one full sleep-phase consolidation cycle.

        Args:
            pending_trajectories: Triples of (EpisodeResult, RoutingDecision,
                TrajectoryFeatures) accumulated since the last sleep phase.
            episodic_memory: Live episodic memory buffer to write into.
            semantic_memory: Live semantic memory store to distil into.
            agent: The ReAct agent whose ``_generate`` method is used for LLM
                calls during semantic distillation.
            prior_adapter_paths: LoRA adapter checkpoints accepted so far; used
                as the orthogonal-regularisation anchors during LoRA training.
            task_id: Numeric identifier for the current sleep cycle, used to
                name the new LoRA checkpoint directory.
            holdout_evaluator: Callable that accepts a checkpoint path and
                returns a dict mapping task_type -> success_rate.

        Returns:
            A :class:`SleepResult` summarising what happened.
        """
        n_episodic = 0
        n_semantic = 0
        n_parametric = 0
        n_skipped = 0
        lora_accepted = False
        new_adapter_path: str | None = None
        checkpoint_delta: dict[str, float] = {}

        # Partition trajectories by routing decision.
        episodic_entries: list[tuple[EpisodeResult, TrajectoryFeatures]] = []
        semantic_entries: list[tuple[EpisodeResult, TrajectoryFeatures]] = []
        parametric_entries: list[tuple[EpisodeResult, TrajectoryFeatures]] = []

        for episode, decision, features in pending_trajectories:
            if decision == RoutingDecision.EPISODIC:
                episodic_entries.append((episode, features))
            elif decision == RoutingDecision.SEMANTIC:
                semantic_entries.append((episode, features))
            elif decision == RoutingDecision.PARAMETRIC:
                parametric_entries.append((episode, features))
            else:
                n_skipped += 1

        # ------------------------------------------------------------------
        # a. Episodic consolidation
        # ------------------------------------------------------------------
        for episode, features in episodic_entries:
            trajectory_text = episode.trajectory_text
            episodic_memory.add(
                trajectory_text=trajectory_text,
                task_type=episode.task_type,
                success=episode.success,
                utility_score=features.utility,
            )
            n_episodic += 1

        logger.info("Sleep phase: added %d entries to episodic memory.", n_episodic)

        # ------------------------------------------------------------------
        # b. Semantic consolidation
        # ------------------------------------------------------------------
        # Group SEMANTIC trajectories by task_type; only distil groups >= 2.
        by_task_type: dict[str, list[EpisodeResult]] = defaultdict(list)
        for episode, _features in semantic_entries:
            by_task_type[episode.task_type].append(episode)

        for task_type, group in by_task_type.items():
            if len(group) < 2:
                logger.debug(
                    "Skipping semantic distillation for task_type=%s (only %d entry).",
                    task_type,
                    len(group),
                )
                n_skipped += len(group)
                continue

            semantic_memory.distill_from_episodes(
                llm_fn=agent._generate,
                episodes=group,
                task_type=task_type,
            )
            n_semantic += len(group)
            logger.info(
                "Sleep phase: distilled %d episodes for task_type=%s.",
                len(group),
                task_type,
            )

        # ------------------------------------------------------------------
        # c. Parametric consolidation (LoRA fine-tuning)
        # ------------------------------------------------------------------
        if len(parametric_entries) < self.sleep_config.min_trajectories_for_lora:
            logger.info(
                "Insufficient PARAMETRIC trajectories (%d < %d); "
                "routing to episodic memory instead.",
                len(parametric_entries),
                self.sleep_config.min_trajectories_for_lora,
            )
            for episode, features in parametric_entries:
                trajectory_text = episode.trajectory_text
                episodic_memory.add(
                    trajectory_text=trajectory_text,
                    task_type=episode.task_type,
                    success=episode.success,
                    utility_score=features.utility,
                )
                n_episodic += 1
        else:
            n_parametric = len(parametric_entries)
            trajectories = [ep for ep, _ in parametric_entries]

            # Import here to avoid a hard circular dependency at module load.
            from dream_state.training.lora_trainer import OLoRATrainer

            trainer = OLoRATrainer(
                base_model_name=self.model_name,
                lora_config_=self.lora_config,
                output_dir=self.output_dir,
                device=self.device,
            )

            checkpoint_path = trainer.fine_tune(
                trajectories=trajectories,
                task_id=task_id,
                prior_adapter_paths=prior_adapter_paths,
            )

            logger.info("Sleep phase: LoRA fine-tuning produced checkpoint at %s.", checkpoint_path)

            # Evaluate the candidate checkpoint.
            checkpoint_metrics: dict[str, float] = holdout_evaluator(checkpoint_path)

            # Load prior accepted checkpoint metrics (empty on first run).
            prior_metrics = self._load_prior_metrics()

            # Compute BWT delta for each task type seen in the prior run.
            for task_type, prior_rate in prior_metrics.items():
                candidate_rate = checkpoint_metrics.get(task_type, 0.0)
                checkpoint_delta[task_type] = candidate_rate - prior_rate

            # Accept/revert logic.
            if checkpoint_delta:
                worst_delta = min(checkpoint_delta.values())
                mean_delta = sum(checkpoint_delta.values()) / len(checkpoint_delta)

                if worst_delta < self.lora_config.revert_threshold_bwt:
                    logger.warning(
                        "LoRA checkpoint REVERTED: worst BWT delta %.4f < threshold %.4f.",
                        worst_delta,
                        self.lora_config.revert_threshold_bwt,
                    )
                    lora_accepted = False
                    new_adapter_path = prior_adapter_paths[-1] if prior_adapter_paths else None
                elif mean_delta >= 0.0:
                    logger.info(
                        "LoRA checkpoint ACCEPTED: mean BWT delta %.4f >= 0.", mean_delta
                    )
                    lora_accepted = True
                    new_adapter_path = checkpoint_path
                    self._save_prior_metrics(checkpoint_metrics)
                else:
                    logger.warning(
                        "LoRA checkpoint REVERTED: mean BWT delta %.4f < 0.", mean_delta
                    )
                    lora_accepted = False
                    new_adapter_path = prior_adapter_paths[-1] if prior_adapter_paths else None
            else:
                # No prior tasks to compare against — unconditionally accept.
                logger.info(
                    "LoRA checkpoint ACCEPTED: no prior metrics to compare (first sleep phase)."
                )
                lora_accepted = True
                new_adapter_path = checkpoint_path
                self._save_prior_metrics(checkpoint_metrics)

        return SleepResult(
            n_episodic=n_episodic,
            n_semantic=n_semantic,
            n_parametric=n_parametric,
            n_skipped=n_skipped,
            lora_accepted=lora_accepted,
            new_adapter_path=new_adapter_path,
            checkpoint_delta=checkpoint_delta,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _prior_metrics_path(self) -> str:
        return os.path.join(self.output_dir, self._PRIOR_METRICS_FILENAME)

    def _load_prior_metrics(self) -> dict[str, float]:
        """Load previously accepted checkpoint metrics from disk, or return {}."""
        path = self._prior_metrics_path()
        if not os.path.exists(path):
            return {}
        try:
            with open(path) as fh:
                return json.load(fh)
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("Could not load prior checkpoint metrics (%s); starting fresh.", exc)
            return {}

    def _save_prior_metrics(self, metrics: dict[str, float]) -> None:
        """Persist accepted checkpoint metrics to disk for the next sleep phase."""
        os.makedirs(self.output_dir, exist_ok=True)
        path = self._prior_metrics_path()
        with open(path, "w") as fh:
            json.dump(metrics, fh, indent=2)
        logger.debug("Saved prior checkpoint metrics to %s.", path)
