"""
Sequential evaluation harness for Dream-State Learning.

Runs a continual learning agent through a 48-task curriculum on ALFWorld,
collecting performance metrics after every task.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


@dataclass
class EvalConfig:
    """Configuration for the sequential evaluation harness."""

    n_tasks: int = 48
    n_per_type: int = 8
    ordering: str = "blocked"  # "blocked" | "interleaved" | "random"
    seed: int = 42
    max_steps_per_task: int = 50
    holdout_per_type: int = 5  # tasks reserved for cross-task safety evaluation


# ---------------------------------------------------------------------------
# Result containers
# ---------------------------------------------------------------------------


@dataclass
class EpisodeResult:
    """Result returned by an agent after completing one episode."""

    success: bool
    steps: int
    task_type: str
    task_id: str
    info: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EvalResults:
    """Aggregated results from a full sequential evaluation run."""

    # Ordered list of task-type labels (length == n_tasks)
    task_sequence: List[str]

    # J[task_idx][task_type] = binary success on the training task at that index
    J: Dict[int, Dict[str, float]]

    # J_cross[task_idx][task_type] = success_rate on holdout set for that type,
    # evaluated after training on task_idx
    J_cross: Dict[int, Dict[str, float]]

    # Zero-shot baseline per task type (used for FWT computation)
    baseline_zero_shot: Dict[str, float]


# ---------------------------------------------------------------------------
# Curriculum builder
# ---------------------------------------------------------------------------


# ALFWorld task types (6 canonical types used throughout the literature)
ALFWORLD_TASK_TYPES = [
    "pick_and_place",
    "pick_clean_then_place",
    "pick_heat_then_place",
    "pick_cool_then_place",
    "look_at_obj_in_light",
    "pick_two_obj_and_place",
]


def build_48_task_curriculum(config: EvalConfig) -> List[Dict[str, Any]]:
    """
    Build a 48-task curriculum (6 types x 8 tasks each).

    Parameters
    ----------
    config:
        EvalConfig controlling ordering and random seed.

    Returns
    -------
    List of task descriptor dicts with keys ``task_type`` and ``task_id``.
    """
    import random

    rng = random.Random(config.seed)

    assert len(ALFWORLD_TASK_TYPES) * config.n_per_type == config.n_tasks, (
        f"n_tasks ({config.n_tasks}) must equal "
        f"len(ALFWORLD_TASK_TYPES) * n_per_type "
        f"({len(ALFWORLD_TASK_TYPES)} * {config.n_per_type})"
    )

    # Build per-type task lists
    tasks_by_type: Dict[str, List[Dict[str, Any]]] = {}
    for t_type in ALFWORLD_TASK_TYPES:
        tasks_by_type[t_type] = [
            {"task_type": t_type, "task_id": f"{t_type}_{i:03d}"}
            for i in range(config.n_per_type)
        ]

    if config.ordering == "blocked":
        curriculum: List[Dict[str, Any]] = []
        for t_type in ALFWORLD_TASK_TYPES:
            curriculum.extend(tasks_by_type[t_type])

    elif config.ordering == "interleaved":
        curriculum = []
        for i in range(config.n_per_type):
            for t_type in ALFWORLD_TASK_TYPES:
                curriculum.append(tasks_by_type[t_type][i])

    elif config.ordering == "random":
        curriculum = []
        for t_type in ALFWORLD_TASK_TYPES:
            curriculum.extend(tasks_by_type[t_type])
        rng.shuffle(curriculum)

    else:
        raise ValueError(
            f"Unknown ordering '{config.ordering}'. "
            "Expected 'blocked', 'interleaved', or 'random'."
        )

    return curriculum


# ---------------------------------------------------------------------------
# Main harness
# ---------------------------------------------------------------------------


class SequentialEvalHarness:
    """
    Runs a continual learning agent sequentially through a 48-task curriculum,
    recording per-task and cross-task performance at every step.

    Parameters
    ----------
    env_config_path:
        Path to the ALFWorld environment YAML configuration file.
    agent:
        Object with a ``run_episode(task_descriptor, max_steps) -> EpisodeResult``
        method.
    memory_system:
        External memory / replay buffer attached to the agent.
    sleep_controller:
        Object with ``should_sleep(t_idx: int) -> bool`` and
        ``run_sleep_phase() -> None`` methods.
    eval_config:
        Hyper-parameters for the evaluation run.
    wandb_run:
        Optional active W&B run for metric logging.
    """

    def __init__(
        self,
        env_config_path: str,
        agent: Any,
        memory_system: Any,
        sleep_controller: Any,
        eval_config: EvalConfig,
        wandb_run: Optional[Any] = None,
    ) -> None:
        self.env_config_path = env_config_path
        self.agent = agent
        self.memory_system = memory_system
        self.sleep_controller = sleep_controller
        self.config = eval_config
        self.wandb_run = wandb_run

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self) -> EvalResults:
        """
        Execute the full sequential evaluation loop.

        For each task in the 48-task curriculum:
          a. Run one episode with the agent.
          b. Record binary success in J[t_idx][task_type].
          c. Evaluate on holdout sets for all previously seen task types.
          d. Record cross-task performance in J_cross[t_idx].
          e. Trigger sleep phase if sleep_controller says so.
          f. Log scalars to W&B if a run is attached.

        Returns
        -------
        EvalResults
        """
        curriculum = build_48_task_curriculum(self.config)
        task_sequence = [t["task_type"] for t in curriculum]

        J: Dict[int, Dict[str, float]] = {}
        J_cross: Dict[int, Dict[str, float]] = {}

        # Track which task types have been seen so far
        seen_types: List[str] = []

        # Collect zero-shot baseline before any training
        baseline_zero_shot = self._collect_zero_shot_baseline()

        logger.info(
            "Starting sequential eval: %d tasks, ordering=%s, seed=%d",
            self.config.n_tasks,
            self.config.ordering,
            self.config.seed,
        )

        for t_idx, task_desc in enumerate(curriculum):
            task_type = task_desc["task_type"]
            logger.info("Task %d/%d  type=%s", t_idx + 1, self.config.n_tasks, task_type)

            # ----------------------------------------------------------------
            # a. Run training episode
            # ----------------------------------------------------------------
            episode: EpisodeResult = self.agent.run_episode(
                task_desc, max_steps=self.config.max_steps_per_task
            )

            # ----------------------------------------------------------------
            # b. Record per-task success
            # ----------------------------------------------------------------
            J[t_idx] = {task_type: float(episode.success)}

            # Track newly seen types (in order of first appearance)
            if task_type not in seen_types:
                seen_types.append(task_type)

            # ----------------------------------------------------------------
            # c-d. Cross-task holdout evaluation over all seen types
            # ----------------------------------------------------------------
            J_cross[t_idx] = self._evaluate_cross_task(seen_types)

            # ----------------------------------------------------------------
            # e. Sleep phase
            # ----------------------------------------------------------------
            if self.sleep_controller.should_sleep(t_idx):
                logger.info("Sleep phase triggered after task %d", t_idx)
                self.sleep_controller.run_sleep_phase()

            # ----------------------------------------------------------------
            # f. W&B logging
            # ----------------------------------------------------------------
            if self.wandb_run is not None:
                self._log_to_wandb(t_idx, task_type, episode, J_cross[t_idx])

        results = EvalResults(
            task_sequence=task_sequence,
            J=J,
            J_cross=J_cross,
            baseline_zero_shot=baseline_zero_shot,
        )

        logger.info("Sequential eval complete.")
        print_results_table(results)
        return results

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _collect_zero_shot_baseline(self) -> Dict[str, float]:
        """
        Evaluate the agent on each task type before any training begins.
        Uses ``holdout_per_type`` tasks per type.
        """
        baseline: Dict[str, float] = {}
        for t_type in ALFWORLD_TASK_TYPES:
            success_rate = self._eval_type(t_type)
            baseline[t_type] = success_rate
            logger.debug("Zero-shot baseline  %s = %.3f", t_type, success_rate)
        return baseline

    def _evaluate_cross_task(self, seen_types: List[str]) -> Dict[str, float]:
        """
        Evaluate the agent on holdout sets for every type in *seen_types*.
        Returns a dict mapping task_type -> mean success rate.
        """
        cross: Dict[str, float] = {}
        for t_type in seen_types:
            cross[t_type] = self._eval_type(t_type)
        return cross

    def _eval_type(self, task_type: str) -> float:
        """
        Run ``holdout_per_type`` evaluation episodes for *task_type* and
        return the mean success rate.
        """
        n = self.config.holdout_per_type
        successes = 0
        for i in range(n):
            task_desc = {
                "task_type": task_type,
                "task_id": f"{task_type}_holdout_{i:03d}",
            }
            result: EpisodeResult = self.agent.run_episode(
                task_desc,
                max_steps=self.config.max_steps_per_task,
            )
            successes += int(result.success)
        return successes / n if n > 0 else 0.0

    def _log_to_wandb(
        self,
        t_idx: int,
        task_type: str,
        episode: EpisodeResult,
        cross: Dict[str, float],
    ) -> None:
        """Push per-step metrics to the attached W&B run."""
        log_dict: Dict[str, Any] = {
            "task_idx": t_idx,
            f"success/{task_type}": float(episode.success),
            "steps": episode.steps,
        }
        for tt, rate in cross.items():
            log_dict[f"cross_task/{tt}"] = rate
        self.wandb_run.log(log_dict, step=t_idx)


# ---------------------------------------------------------------------------
# Metric computation
# ---------------------------------------------------------------------------


def _unique_task_types(results: EvalResults) -> List[str]:
    """Return task types in the order they first appeared in the curriculum."""
    seen: List[str] = []
    for t_type in results.task_sequence:
        if t_type not in seen:
            seen.append(t_type)
    return seen


def _last_task_idx(results: EvalResults) -> int:
    """Index of the final task in the curriculum."""
    return len(results.task_sequence) - 1


def compute_fgt(results: EvalResults) -> float:
    """
    Compute the average Forgetting (FGT) metric.

    FGT = (1 / (T-1)) * sum_{i=0}^{T-2}
              [max_{j in i..T-1}(J_cross[j][type_i]) - J_cross[T-1][type_i]]

    where T is the number of unique task types, and *type_i* is the task type
    first introduced at curriculum position *i* (among unique types).

    A positive value indicates forgetting; negative indicates improvement after
    initial learning.
    """
    unique_types = _unique_task_types(results)
    T = len(unique_types)
    if T <= 1:
        return 0.0

    T_last = _last_task_idx(results)
    total = 0.0
    count = 0

    # Map each unique type to the curriculum index where it first appeared
    first_idx: Dict[str, int] = {}
    for idx, t_type in enumerate(results.task_sequence):
        if t_type not in first_idx:
            first_idx[t_type] = idx

    for t_type in unique_types[:-1]:  # exclude the last type (T-2 in 0-indexed)
        i_first = first_idx[t_type]

        # Maximum cross-task performance from first introduction to end
        peak = max(
            results.J_cross[j].get(t_type, 0.0)
            for j in range(i_first, T_last + 1)
            if t_type in results.J_cross.get(j, {})
        ) if any(
            t_type in results.J_cross.get(j, {})
            for j in range(i_first, T_last + 1)
        ) else 0.0

        final = results.J_cross.get(T_last, {}).get(t_type, 0.0)
        total += peak - final
        count += 1

    return total / count if count > 0 else 0.0


def compute_bwt(results: EvalResults) -> float:
    """
    Compute Backward Transfer (BWT).

    BWT = (1 / (T-1)) * sum_{i=0}^{T-2}
              (J_cross[T-1][type_i] - J[i][type_i])

    Positive BWT means performance on old tasks improved after learning new
    ones; negative BWT indicates forgetting.
    """
    unique_types = _unique_task_types(results)
    T = len(unique_types)
    if T <= 1:
        return 0.0

    T_last = _last_task_idx(results)
    total = 0.0
    count = 0

    first_idx: Dict[str, int] = {}
    for idx, t_type in enumerate(results.task_sequence):
        if t_type not in first_idx:
            first_idx[t_type] = idx

    for t_type in unique_types[:-1]:
        i_first = first_idx[t_type]
        final = results.J_cross.get(T_last, {}).get(t_type, 0.0)
        at_learning = results.J.get(i_first, {}).get(t_type, 0.0)
        total += final - at_learning
        count += 1

    return total / count if count > 0 else 0.0


def compute_fwt(results: EvalResults) -> float:
    """
    Compute Forward Transfer (FWT).

    FWT = (1 / (T-1)) * sum_{i=1}^{T-1}
              (J[i][type_i] - baseline_zero_shot[type_i])

    Positive FWT means that learning earlier tasks improved zero-shot
    performance on later tasks.
    """
    unique_types = _unique_task_types(results)
    T = len(unique_types)
    if T <= 1:
        return 0.0

    first_idx: Dict[str, int] = {}
    for idx, t_type in enumerate(results.task_sequence):
        if t_type not in first_idx:
            first_idx[t_type] = idx

    total = 0.0
    count = 0

    for t_type in unique_types[1:]:  # skip the very first type
        i_first = first_idx[t_type]
        at_learning = results.J.get(i_first, {}).get(t_type, 0.0)
        zero_shot = results.baseline_zero_shot.get(t_type, 0.0)
        total += at_learning - zero_shot
        count += 1

    return total / count if count > 0 else 0.0


def compute_mfn(results: EvalResults) -> float:
    """
    Compute Mean Final-task accuracy (MFN).

    MFN = mean of J_cross[T-1].values()

    This is the average accuracy across all task types at the very end of
    training.
    """
    T_last = _last_task_idx(results)
    final_cross = results.J_cross.get(T_last, {})
    if not final_cross:
        return 0.0
    return sum(final_cross.values()) / len(final_cross)


def compute_maa(results: EvalResults) -> float:
    """
    Compute Mean Average Accuracy (MAA).

    MAA is the mean of J_cross[t][task_type] over all (t, task_type) pairs
    where the task_type was already seen at step t.  This captures the area
    under the cross-task performance curve.
    """
    total = 0.0
    count = 0
    for t_idx in sorted(results.J_cross.keys()):
        for rate in results.J_cross[t_idx].values():
            total += rate
            count += 1
    return total / count if count > 0 else 0.0


# ---------------------------------------------------------------------------
# Pretty-print table
# ---------------------------------------------------------------------------


def print_results_table(results: EvalResults) -> None:
    """
    Print a Rich-formatted summary table to the console.

    Falls back to plain text if Rich is not installed.
    """
    fgt = compute_fgt(results)
    bwt = compute_bwt(results)
    fwt = compute_fwt(results)
    mfn = compute_mfn(results)
    maa = compute_maa(results)

    try:
        from rich.console import Console
        from rich.table import Table

        console = Console()

        table = Table(
            title="Dream-State Evaluation Results",
            show_header=True,
            header_style="bold cyan",
        )
        table.add_column("Metric", style="bold", min_width=24)
        table.add_column("Value", justify="right", min_width=10)
        table.add_column("Description", min_width=48)

        rows = [
            ("FGT  (Forgetting)", f"{fgt:+.4f}", "Max seen - final; lower is better"),
            ("BWT  (Backward Transfer)", f"{bwt:+.4f}", "Final - at-learning-time; higher is better"),
            ("FWT  (Forward Transfer)", f"{fwt:+.4f}", "At-learning-time - zero-shot; higher is better"),
            ("MFN  (Mean Final Accuracy)", f"{mfn:.4f}", "Mean accuracy across types at end of training"),
            ("MAA  (Mean Avg Accuracy)", f"{maa:.4f}", "Area under cross-task accuracy curve"),
        ]

        for name, val, desc in rows:
            table.add_row(name, val, desc)

        # Per-type final accuracy sub-table
        T_last = _last_task_idx(results)
        final_cross = results.J_cross.get(T_last, {})
        if final_cross:
            type_table = Table(
                title="Final Cross-Task Accuracy by Type",
                show_header=True,
                header_style="bold magenta",
            )
            type_table.add_column("Task Type", style="bold")
            type_table.add_column("Accuracy", justify="right")
            type_table.add_column("Zero-Shot Baseline", justify="right")
            type_table.add_column("Delta", justify="right")
            for t_type, acc in sorted(final_cross.items()):
                zs = results.baseline_zero_shot.get(t_type, 0.0)
                delta = acc - zs
                type_table.add_row(
                    t_type,
                    f"{acc:.4f}",
                    f"{zs:.4f}",
                    f"{delta:+.4f}",
                )

        console.print(table)
        if final_cross:
            console.print(type_table)

    except ImportError:
        # Fallback: plain text
        separator = "-" * 60
        print(separator)
        print("Dream-State Evaluation Results")
        print(separator)
        print(f"  FGT  (Forgetting)          : {fgt:+.4f}")
        print(f"  BWT  (Backward Transfer)   : {bwt:+.4f}")
        print(f"  FWT  (Forward Transfer)    : {fwt:+.4f}")
        print(f"  MFN  (Mean Final Accuracy) : {mfn:.4f}")
        print(f"  MAA  (Mean Avg Accuracy)   : {maa:.4f}")
        print(separator)
        T_last = _last_task_idx(results)
        final_cross = results.J_cross.get(T_last, {})
        if final_cross:
            print("Final Cross-Task Accuracy by Type:")
            for t_type, acc in sorted(final_cross.items()):
                zs = results.baseline_zero_shot.get(t_type, 0.0)
                print(f"  {t_type:<35} acc={acc:.4f}  zs={zs:.4f}  delta={acc-zs:+.4f}")
        print(separator)
