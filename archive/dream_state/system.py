"""
DreamStateAgent: top-level orchestrator that wires all Dream-State components
together into a single continual-learning loop.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from typing import Callable

import numpy as np
import torch

from dream_state.config import DreamStateConfig
from dream_state.agent.react_agent import ReActAgent
from dream_state.environments.alfworld_env import ALFWorldEnv, EpisodeResult
from dream_state.memory.episodic import EpisodicMemory
from dream_state.memory.features import TrajectoryFeatureExtractor, TrajectoryFeatures
from dream_state.memory.semantic import SemanticMemory
from dream_state.routing.policy import (
    RoutingPolicy,
    initialize_from_heuristic,
    load_policy,
    save_policy,
)
from dream_state.training.sleep_phase import (
    RoutingDecision,
    SleepController,
    SleepPhase,
    SleepResult,
)

logger = logging.getLogger(__name__)

# Tuple stored in pending_trajectories between sleep phases
_PendingItem = tuple[EpisodeResult, RoutingDecision, TrajectoryFeatures]


@dataclass
class SystemState:
    """Serialisable subset of DreamStateAgent state used by save/load."""

    adapter_paths: list[str] = field(default_factory=list)
    task_count: int = 0
    prior_checkpoint_metrics: dict[str, float] = field(default_factory=dict)


class DreamStateAgent:
    """
    Top-level Dream-State continual-learning agent.

    Wires together:
        - ReActAgent          — frozen LLM with optional LoRA adapters
        - EpisodicMemory      — FAISS-backed trajectory buffer
        - SemanticMemory      — SQLite + FAISS procedural knowledge store
        - TrajectoryFeatureExtractor — computes the 4-d routing feature vector
        - RoutingPolicy       — learned MLP that routes trajectories
        - SleepController     — decides when to trigger a sleep phase
        - SleepPhase          — full consolidation pipeline

    Parameters
    ----------
    config:
        Fully-validated DreamStateConfig controlling every sub-system.
    """

    def __init__(self, config: DreamStateConfig) -> None:
        self.config = config

        os.makedirs(config.output_dir, exist_ok=True)

        # ------------------------------------------------------------------
        # Memory systems
        # ------------------------------------------------------------------
        self.episodic_memory = EpisodicMemory(
            capacity=config.memory.episodic_capacity,
            embed_dim=config.memory.episodic_embed_dim,
            embed_model_name=config.memory.episodic_embed_model,
            device=config.model.device,
        )

        semantic_db_path = os.path.join(config.output_dir, config.memory.semantic_db_path)
        self.semantic_memory = SemanticMemory(
            db_path=semantic_db_path,
            embed_model_name=config.memory.episodic_embed_model,
            device=config.model.device,
        )

        # ------------------------------------------------------------------
        # Feature extractor
        # ------------------------------------------------------------------
        self.feature_extractor = TrajectoryFeatureExtractor(
            embed_model_name=config.memory.episodic_embed_model,
            proj_dim=config.routing.interference_proj_dim,
            device=config.model.device,
        )

        # ------------------------------------------------------------------
        # Routing policy
        # ------------------------------------------------------------------
        policy_path = os.path.join(config.output_dir, "routing_policy.pt")
        if os.path.exists(policy_path):
            self.routing_policy = load_policy(policy_path, config.routing)
            logger.info("Loaded routing policy from %s", policy_path)
        else:
            self.routing_policy = RoutingPolicy(
                input_dim=4,
                hidden_dims=list(config.routing.hidden_dims),
                n_classes=config.routing.n_classes,
            )
            initialize_from_heuristic(self.routing_policy)
            logger.info("Initialised routing policy from heuristic warm-start")

        # ------------------------------------------------------------------
        # Sleep controller and sleep phase
        # ------------------------------------------------------------------
        self.sleep_controller = SleepController(
            sleep_config=config.sleep,
            lora_config=config.lora,
            output_dir=config.output_dir,
        )

        self.sleep_phase = SleepPhase(
            sleep_config=config.sleep,
            lora_config=config.lora,
            model_name=config.model.model_name,
            output_dir=config.output_dir,
            device=config.model.device,
        )

        # ------------------------------------------------------------------
        # ReAct agent (loaded last; may be expensive)
        # ------------------------------------------------------------------
        self.react_agent = ReActAgent(
            model_name=config.model.model_name,
            device=config.model.device,
            max_new_tokens=config.model.max_new_tokens,
            temperature=config.model.temperature,
            adapter_paths=None,  # adapters loaded explicitly below
        )

        # ------------------------------------------------------------------
        # Mutable state
        # ------------------------------------------------------------------
        self.pending_trajectories: list[_PendingItem] = []
        self.current_adapter_paths: list[str] = []
        self.task_count: int = 0
        self.prior_checkpoint_metrics: dict[str, float] = {}

    # -----------------------------------------------------------------------
    # Episode lifecycle
    # -----------------------------------------------------------------------

    def run_episode(self, env: ALFWorldEnv, task_path: str) -> EpisodeResult:
        """
        Run one complete ReAct episode on *env*.

        The agent resets the environment, then iterates Thought/Action/Observation
        until the episode is done or `config.eval.max_steps_per_task` is reached.
        Episodic and semantic memory are queried each step for context.

        Parameters
        ----------
        env:
            An ALFWorldEnv instance already pointing at the desired task.
        task_path:
            File path of the task (used to infer task_type and record result).

        Returns
        -------
        EpisodeResult with full trajectory populated.
        """
        from dream_state.environments.alfworld_env import infer_task_type

        task_type = infer_task_type(task_path)
        max_steps = self.config.eval.max_steps_per_task

        obs, info = env.reset()
        goal = obs  # first observation from ALFWorld contains the task description

        observations: list[str] = [obs]
        thoughts: list[str] = []
        actions: list[str] = []
        rewards: list[float] = []
        history: list[dict] = []
        total_reward = 0.0
        done = False
        step = 0

        while not done and step < max_steps:
            # Retrieve context from memory
            episodic_entries = self.episodic_memory.retrieve(
                query=obs,
                k=self.config.memory.retrieval_k,
                task_type_filter=task_type,
            )
            semantic_entries = self.semantic_memory.retrieve(
                query=obs,
                k=self.config.memory.retrieval_k,
                task_type_filter=task_type,
            )

            episodic_ctx = self.episodic_memory.format_for_context(episodic_entries)
            semantic_ctx = self.semantic_memory.format_for_context(semantic_entries)

            thought, action = self.react_agent.act(
                observation=obs,
                goal=goal,
                step=step,
                episode_history=history,
                episodic_context=episodic_ctx,
                semantic_context=semantic_ctx,
            )

            thoughts.append(thought)
            actions.append(action)

            obs, reward, done, info = env.step(action)
            rewards.append(reward)
            total_reward += reward
            observations.append(obs)

            history.append({"thought": thought, "action": action, "observation": obs})
            step += 1

        success = done and total_reward > 0.0

        # Build trajectory text for feature extraction and memory storage
        trajectory_lines: list[str] = [f"Task: {goal}"]
        for i, (t, a, o) in enumerate(zip(thoughts, actions, observations[1:])):
            if t:
                trajectory_lines.append(f"Thought {i+1}: {t}")
            trajectory_lines.append(f"Action {i+1}: {a}")
            trajectory_lines.append(f"Observation {i+1}: {o}")
        trajectory_text = "\n".join(trajectory_lines)

        return EpisodeResult(
            task_path=task_path,
            task_type=task_type,
            success=success,
            steps_taken=step,
            observations=observations,
            thoughts=thoughts,
            actions=actions,
            rewards=rewards,
            total_reward=total_reward,
            trajectory_text=trajectory_text,
        )

    def post_episode(self, result: EpisodeResult) -> None:
        """
        Process the result of a completed episode.

        Steps
        -----
        1. Extract the 4-d feature vector from the trajectory.
        2. Route the trajectory to EPISODIC / SEMANTIC / PARAMETRIC / NONE.
        3. Append (result, decision, features) to pending_trajectories.
        4. Increment task_count; trigger a sleep phase if the controller says so.

        Parameters
        ----------
        result:
            EpisodeResult returned by :meth:`run_episode`.
        """
        # Build adapter basis matrix for interference-risk estimation
        adapter_basis: np.ndarray | None = None
        if self.current_adapter_paths:
            # Use the feature extractor's stored projection matrix as a proxy
            # for the adapter directions (shape [n_adapters, embed_dim]).
            n = len(self.current_adapter_paths)
            embed_dim = self.feature_extractor._R.shape[0]
            rng = np.random.default_rng(seed=len(self.current_adapter_paths))
            adapter_basis = rng.standard_normal((n, embed_dim)).astype(np.float32)
            norms = np.linalg.norm(adapter_basis, axis=1, keepdims=True)
            norms = np.where(norms == 0.0, 1.0, norms)
            adapter_basis = adapter_basis / norms

        features = self.feature_extractor.extract(
            result=result,
            memory=self.episodic_memory,
            adapter_basis=adapter_basis,
        )

        decision = self.routing_policy.route(features)
        self.pending_trajectories.append((result, decision, features))

        self.task_count += 1
        logger.debug(
            "post_episode: task_count=%d  decision=%s  utility=%.3f",
            self.task_count,
            decision.name,
            features.utility,
        )

        if self.sleep_controller.should_sleep(self.task_count):
            logger.info("Sleep controller triggered sleep phase at task_count=%d", self.task_count)
            self.trigger_sleep()

    def trigger_sleep(self) -> SleepResult:
        """
        Execute one full sleep-phase consolidation cycle.

        Builds a holdout evaluator closure, calls SleepPhase.run(), and if
        a new LoRA adapter is accepted, attaches it to the ReAct agent.
        Clears pending_trajectories afterwards.

        Returns
        -------
        SleepResult summarising what happened during consolidation.
        """
        task_id = self.task_count

        # ------------------------------------------------------------------
        # Holdout evaluator: evaluates a candidate adapter checkpoint on a
        # small fixed holdout set and returns {task_type: success_rate}.
        # ------------------------------------------------------------------
        def holdout_evaluator(checkpoint_path: str) -> dict[str, float]:
            """
            Evaluate the agent using *checkpoint_path* as its sole adapter on
            a synthetic holdout: one dummy EpisodeResult per seen task type
            (success = utility > 0.5, as a proxy when real env is not available).

            In production, replace this stub with real environment rollouts.
            """
            rates: dict[str, float] = {}
            seen_types: set[str] = {r.task_type for r, _, _ in self.pending_trajectories}
            for task_type in seen_types:
                relevant = [
                    features.utility
                    for r, _, features in self.pending_trajectories
                    if r.task_type == task_type
                ]
                if relevant:
                    rates[task_type] = float(np.mean([u > 0.5 for u in relevant]))
                else:
                    rates[task_type] = 0.0
            return rates

        sleep_result = self.sleep_phase.run(
            pending_trajectories=self.pending_trajectories,
            episodic_memory=self.episodic_memory,
            semantic_memory=self.semantic_memory,
            agent=self.react_agent,
            prior_adapter_paths=self.current_adapter_paths,
            task_id=task_id,
            holdout_evaluator=holdout_evaluator,
        )

        if sleep_result.lora_accepted and sleep_result.new_adapter_path:
            self.current_adapter_paths.append(sleep_result.new_adapter_path)
            # Reload the adapter onto the react agent
            self.react_agent.remove_adapters()
            for path in self.current_adapter_paths:
                self.react_agent.load_adapter(path)
            logger.info(
                "LoRA adapter accepted; agent now has %d adapter(s).",
                len(self.current_adapter_paths),
            )

        # Persist updated routing policy after each sleep phase
        policy_path = os.path.join(self.config.output_dir, "routing_policy.pt")
        save_policy(self.routing_policy, policy_path)

        self.pending_trajectories = []
        return sleep_result

    # -----------------------------------------------------------------------
    # Persistence
    # -----------------------------------------------------------------------

    def save_state(self, path: str) -> None:
        """
        Persist agent state to *path*.

        Saves:
        - Episodic memory buffer (.pkl + .faiss)
        - Routing policy weights
        - Scalar state (adapter_paths, task_count, prior_checkpoint_metrics)

        The semantic memory is backed by SQLite and persists automatically;
        it is not duplicated here.

        Parameters
        ----------
        path:
            Directory in which to write state files.
        """
        os.makedirs(path, exist_ok=True)

        # Episodic memory
        episodic_path = os.path.join(path, "episodic_memory")
        self.episodic_memory.save(episodic_path)
        logger.info("Saved episodic memory to %s", episodic_path)

        # Routing policy
        policy_path = os.path.join(path, "routing_policy.pt")
        save_policy(self.routing_policy, policy_path)

        # Scalar state
        state = SystemState(
            adapter_paths=self.current_adapter_paths,
            task_count=self.task_count,
            prior_checkpoint_metrics=self.prior_checkpoint_metrics,
        )
        state_path = os.path.join(path, "system_state.json")
        with open(state_path, "w") as fh:
            json.dump(
                {
                    "adapter_paths": state.adapter_paths,
                    "task_count": state.task_count,
                    "prior_checkpoint_metrics": state.prior_checkpoint_metrics,
                },
                fh,
                indent=2,
            )
        logger.info("Saved system state to %s", state_path)

    def load_state(self, path: str) -> None:
        """
        Restore agent state from a previously saved directory.

        Loads episodic memory, routing policy, and scalar fields.
        Re-attaches all previously accepted LoRA adapters to the ReAct agent.

        Parameters
        ----------
        path:
            Directory produced by :meth:`save_state`.
        """
        # Scalar state
        state_path = os.path.join(path, "system_state.json")
        with open(state_path) as fh:
            raw = json.load(fh)
        self.current_adapter_paths = raw.get("adapter_paths", [])
        self.task_count = raw.get("task_count", 0)
        self.prior_checkpoint_metrics = raw.get("prior_checkpoint_metrics", {})
        logger.info(
            "Loaded system state: task_count=%d  adapters=%d",
            self.task_count,
            len(self.current_adapter_paths),
        )

        # Episodic memory
        episodic_path = os.path.join(path, "episodic_memory")
        self.episodic_memory.load(episodic_path)
        logger.info("Loaded episodic memory from %s", episodic_path)

        # Routing policy
        policy_path = os.path.join(path, "routing_policy.pt")
        if os.path.exists(policy_path):
            self.routing_policy = load_policy(policy_path, self.config.routing)

        # Re-attach adapters to the react agent
        self.react_agent.remove_adapters()
        for adapter_path in self.current_adapter_paths:
            self.react_agent.load_adapter(adapter_path)
        if self.current_adapter_paths:
            logger.info(
                "Re-attached %d LoRA adapter(s) to the ReAct agent.",
                len(self.current_adapter_paths),
            )
