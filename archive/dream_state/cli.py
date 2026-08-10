"""
Dream-State Learning — command-line interface.

Commands
--------
train   Run the full continual-learning training loop.
eval    Evaluate a saved checkpoint without triggering sleep phases.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Optional

import typer

app = typer.Typer(
    name="dream-state",
    help="Dream-State Learning continual agent for ALFWorld.",
    add_completion=False,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# train
# ---------------------------------------------------------------------------


@app.command()
def train(
    config_path: str = typer.Argument(..., help="Path to the YAML configuration file."),
    resume: bool = typer.Option(
        False,
        "--resume",
        help="Resume from a previous run saved in config.output_dir.",
    ),
) -> None:
    """
    Run the Dream-State continual-learning training loop.

    Loads the config from CONFIG_PATH, builds a 48-task ALFWorld curriculum,
    runs the DreamStateAgent through all tasks (with sleep phases), and saves
    results + metrics to config.output_dir.
    """
    from dream_state.config import load_config, save_config
    from dream_state.environments.alfworld_env import ALFWorldEnv, build_48_task_curriculum
    from dream_state.eval.harness import (
        EvalConfig,
        SequentialEvalHarness,
        compute_bwt,
        compute_fgt,
        compute_fwt,
        compute_maa,
        compute_mfn,
        print_results_table,
    )
    from dream_state.system import DreamStateAgent

    # ------------------------------------------------------------------
    # Load config
    # ------------------------------------------------------------------
    config = load_config(config_path)
    os.makedirs(config.output_dir, exist_ok=True)

    # Persist config next to outputs for reproducibility
    save_config(config, os.path.join(config.output_dir, "config.yaml"))

    # ------------------------------------------------------------------
    # Build agent
    # ------------------------------------------------------------------
    agent = DreamStateAgent(config)

    if resume:
        state_dir = os.path.join(config.output_dir, "agent_state")
        if os.path.exists(state_dir):
            logger.info("Resuming from %s", state_dir)
            agent.load_state(state_dir)
        else:
            logger.warning(
                "--resume specified but no saved state found at %s; starting fresh.",
                state_dir,
            )

    # ------------------------------------------------------------------
    # Build ALFWorld environment and 48-task curriculum
    # ------------------------------------------------------------------
    # The ALFWorld config path is expected alongside the dream-state config
    # or overridable via an env variable.
    alfworld_config_path = os.environ.get(
        "ALFWORLD_CONFIG",
        os.path.join(os.path.dirname(config_path), "alfworld_config.yaml"),
    )

    env = ALFWorldEnv(
        config_path=alfworld_config_path,
        split="train",
        max_steps=config.eval.max_steps_per_task,
    )

    all_tasks = env.get_all_tasks()
    curriculum = build_48_task_curriculum(
        all_tasks=all_tasks,
        ordering=config.eval.ordering,
        n_per_type=config.eval.n_per_type,
        seed=config.eval.seed,
    )

    # ------------------------------------------------------------------
    # Run harness: a thin adapter that calls agent.run_episode / post_episode
    # in order, mimicking what SequentialEvalHarness.run() does for the
    # training tasks.  SequentialEvalHarness also needs a run_episode
    # compatible with its own EpisodeResult dataclass, so we wrap agent.
    # ------------------------------------------------------------------
    eval_config = EvalConfig(
        n_tasks=len(curriculum),
        n_per_type=config.eval.n_per_type,
        ordering=config.eval.ordering,
        seed=config.eval.seed,
        max_steps_per_task=config.eval.max_steps_per_task,
        holdout_per_type=config.sleep.holdout_per_type,
    )

    # Adapter to satisfy SequentialEvalHarness interface
    class _AgentAdapter:
        def __init__(self, inner: DreamStateAgent, env_: ALFWorldEnv, tasks: list[str]) -> None:
            self._agent = inner
            self._env = env_
            self._tasks = tasks
            self._cursor = 0

        def run_episode(self, task_desc: dict, max_steps: int) -> "EpisodeResult":  # type: ignore[override]
            from dream_state.eval.harness import EpisodeResult as HarnessResult

            # Map the task_id from the harness back to the actual file path
            task_path = (
                self._tasks[self._cursor % len(self._tasks)]
                if self._tasks
                else task_desc.get("task_id", "unknown")
            )
            self._cursor += 1
            result = self._agent.run_episode(self._env, task_path)
            self._agent.post_episode(result)
            return HarnessResult(
                success=result.success,
                steps=result.steps_taken,
                task_type=result.task_type,
                task_id=result.task_path,
            )

    class _NoOpSleepController:
        """Sleep is already driven by agent.post_episode; harness should not re-trigger."""

        def should_sleep(self, t_idx: int) -> bool:  # noqa: ARG002
            return False

        def run_sleep_phase(self) -> None:
            pass

    adapter = _AgentAdapter(agent, env, curriculum)
    harness = SequentialEvalHarness(
        env_config_path=alfworld_config_path,
        agent=adapter,
        memory_system=agent.episodic_memory,
        sleep_controller=_NoOpSleepController(),
        eval_config=eval_config,
    )

    logger.info("Starting training run — %d tasks", len(curriculum))
    results = harness.run()

    # ------------------------------------------------------------------
    # Save agent state
    # ------------------------------------------------------------------
    state_dir = os.path.join(config.output_dir, "agent_state")
    agent.save_state(state_dir)
    logger.info("Agent state saved to %s", state_dir)

    # ------------------------------------------------------------------
    # Save results JSON
    # ------------------------------------------------------------------
    results_path = os.path.join(config.output_dir, "eval_results.json")
    results_json = {
        "task_sequence": results.task_sequence,
        "J": {str(k): v for k, v in results.J.items()},
        "J_cross": {str(k): v for k, v in results.J_cross.items()},
        "baseline_zero_shot": results.baseline_zero_shot,
        "metrics": {
            "FGT": compute_fgt(results),
            "BWT": compute_bwt(results),
            "FWT": compute_fwt(results),
            "MFN": compute_mfn(results),
            "MAA": compute_maa(results),
        },
    }
    with open(results_path, "w") as fh:
        json.dump(results_json, fh, indent=2)
    logger.info("Results saved to %s", results_path)

    # ------------------------------------------------------------------
    # Print metrics table
    # ------------------------------------------------------------------
    print_results_table(results)
    env.close()


# ---------------------------------------------------------------------------
# eval
# ---------------------------------------------------------------------------


@app.command()
def eval(
    checkpoint_dir: str = typer.Argument(
        ..., help="Directory produced by the train command (contains config.yaml + agent_state/)."
    ),
    ordering: str = typer.Option(
        "blocked",
        "--ordering",
        help="Task ordering: blocked | interleaved | easy_to_hard | random.",
    ),
    seed: int = typer.Option(42, "--seed", help="Random seed for curriculum sampling."),
) -> None:
    """
    Evaluate a saved Dream-State checkpoint without triggering sleep phases.

    Loads the config from CHECKPOINT_DIR/config.yaml, restores agent state,
    and runs one pass through the curriculum measuring task success rates.
    """
    from dream_state.config import load_config
    from dream_state.environments.alfworld_env import ALFWorldEnv, build_48_task_curriculum
    from dream_state.eval.harness import (
        EvalConfig,
        SequentialEvalHarness,
        print_results_table,
    )
    from dream_state.system import DreamStateAgent

    config_yaml = os.path.join(checkpoint_dir, "config.yaml")
    if not os.path.exists(config_yaml):
        typer.echo(f"Error: config.yaml not found in {checkpoint_dir}", err=True)
        raise typer.Exit(code=1)

    config = load_config(config_yaml)
    # Override ordering and seed from CLI args
    config.eval.ordering = ordering
    config.eval.seed = seed

    # ------------------------------------------------------------------
    # Restore agent
    # ------------------------------------------------------------------
    agent = DreamStateAgent(config)
    state_dir = os.path.join(checkpoint_dir, "agent_state")
    if os.path.exists(state_dir):
        agent.load_state(state_dir)
    else:
        logger.warning("No agent_state directory found at %s; running from scratch.", state_dir)

    # ------------------------------------------------------------------
    # Build environment and curriculum
    # ------------------------------------------------------------------
    alfworld_config_path = os.environ.get(
        "ALFWORLD_CONFIG",
        os.path.join(checkpoint_dir, "alfworld_config.yaml"),
    )

    env = ALFWorldEnv(
        config_path=alfworld_config_path,
        split="eval_out_of_distribution",
        max_steps=config.eval.max_steps_per_task,
    )

    all_tasks = env.get_all_tasks()
    curriculum = build_48_task_curriculum(
        all_tasks=all_tasks,
        ordering=ordering,
        n_per_type=config.eval.n_per_type,
        seed=seed,
    )

    eval_config = EvalConfig(
        n_tasks=len(curriculum),
        n_per_type=config.eval.n_per_type,
        ordering=ordering,
        seed=seed,
        max_steps_per_task=config.eval.max_steps_per_task,
        holdout_per_type=config.sleep.holdout_per_type,
    )

    # ------------------------------------------------------------------
    # Eval-only adapter: no post_episode / sleep
    # ------------------------------------------------------------------
    class _EvalAdapter:
        def __init__(self, inner: DreamStateAgent, env_: ALFWorldEnv, tasks: list[str]) -> None:
            self._agent = inner
            self._env = env_
            self._tasks = tasks
            self._cursor = 0

        def run_episode(self, task_desc: dict, max_steps: int) -> "EpisodeResult":  # type: ignore[override]
            from dream_state.eval.harness import EpisodeResult as HarnessResult

            task_path = (
                self._tasks[self._cursor % len(self._tasks)]
                if self._tasks
                else task_desc.get("task_id", "unknown")
            )
            self._cursor += 1
            result = self._agent.run_episode(self._env, task_path)
            # NOTE: no post_episode call — eval mode only
            return HarnessResult(
                success=result.success,
                steps=result.steps_taken,
                task_type=result.task_type,
                task_id=result.task_path,
            )

    class _NoOpSleepController:
        def should_sleep(self, t_idx: int) -> bool:  # noqa: ARG002
            return False

        def run_sleep_phase(self) -> None:
            pass

    harness = SequentialEvalHarness(
        env_config_path=alfworld_config_path,
        agent=_EvalAdapter(agent, env, curriculum),
        memory_system=agent.episodic_memory,
        sleep_controller=_NoOpSleepController(),
        eval_config=eval_config,
    )

    logger.info("Starting eval-only run — ordering=%s  seed=%d", ordering, seed)
    results = harness.run()
    print_results_table(results)
    env.close()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app()
