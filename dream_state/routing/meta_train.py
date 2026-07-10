"""
Meta-learning training loop for the Dream-State consolidation routing policy.

Meta-objective: train the routing policy such that routing decisions for a task
sequence S_meta maximise downstream FWT + BWT on held-out evaluation tasks.

Approach: REINFORCE (policy gradient) outer loop.
  - Inner loop  : lightweight surrogate simulation of future task performance.
  - Outer loop  : gradient on routing policy parameters from reward = FWT + BWT.
"""

from __future__ import annotations

import json
import logging
import random
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler

from dream_state.config import LoRAConfig, RoutingConfig
from dream_state.memory.features import TrajectoryFeatures
from dream_state.training.sleep_phase import RoutingDecision

if TYPE_CHECKING:
    from dream_state.agent.react_agent import ReActAgent
    from dream_state.memory.episodic import EpisodicMemory

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# RoutingPolicy
# ---------------------------------------------------------------------------

_N_FEATURES = 4  # utility, transfer_potential, retrieval_cost, interference_risk
_N_CLASSES = 4   # EPISODIC, SEMANTIC, PARAMETRIC, NONE

# Heuristic prior logits: bias toward EPISODIC, penalise PARAMETRIC slightly.
_HEURISTIC_LOGITS = torch.tensor([0.5, 0.2, -0.2, 0.0], dtype=torch.float32)


class RoutingPolicy(nn.Module):
    """
    Small MLP that maps a 4-d trajectory feature vector to a categorical
    distribution over the four consolidation routing classes.

    Parameters
    ----------
    hidden_dims:
        Widths of the hidden layers.  Defaults to [128, 64, 32].
    n_classes:
        Number of output classes (default 4).
    """

    def __init__(
        self,
        hidden_dims: list[int] | None = None,
        n_classes: int = _N_CLASSES,
    ) -> None:
        super().__init__()
        if hidden_dims is None:
            hidden_dims = [128, 64, 32]

        layers: list[nn.Module] = []
        in_dim = _N_FEATURES
        for h in hidden_dims:
            layers += [nn.Linear(in_dim, h), nn.ReLU()]
            in_dim = h
        layers.append(nn.Linear(in_dim, n_classes))
        self.net = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.distributions.Categorical:
        """Return a Categorical distribution given feature tensor x (shape [..., 4])."""
        logits = self.net(x)
        return torch.distributions.Categorical(logits=logits)

    def sample_decision(
        self, features: TrajectoryFeatures
    ) -> tuple[RoutingDecision, torch.Tensor]:
        """
        Sample a routing decision for a single trajectory.

        Returns
        -------
        decision:
            The sampled :class:`RoutingDecision`.
        log_prob:
            Log-probability of the sampled decision (scalar tensor, grad-enabled).
        """
        x = features.to_tensor().unsqueeze(0)  # [1, 4]
        dist = self(x)
        action = dist.sample()                 # [1]
        log_prob = dist.log_prob(action)       # [1]
        decision = RoutingDecision(int(action.item()))
        return decision, log_prob.squeeze(0)

    def entropy(self, features_batch: torch.Tensor) -> torch.Tensor:
        """
        Compute the mean entropy of the policy over a batch of feature vectors.

        Parameters
        ----------
        features_batch:
            Tensor of shape [B, 4].

        Returns
        -------
        Scalar tensor.
        """
        dist = self(features_batch)
        return dist.entropy().mean()

    def initialize_from_heuristic(self) -> None:
        """
        Bias the output layer so that the initial logit ordering follows the
        heuristic prior: EPISODIC > SEMANTIC > NONE > PARAMETRIC.

        Achieved by adding _HEURISTIC_LOGITS to the output-layer bias in-place.
        """
        with torch.no_grad():
            out_layer: nn.Linear = self.net[-1]  # type: ignore[assignment]
            out_layer.bias.add_(_HEURISTIC_LOGITS.to(out_layer.bias.device))


# ---------------------------------------------------------------------------
# RolloutEpisode
# ---------------------------------------------------------------------------


@dataclass
class RolloutEpisode:
    """A single (features, decision, log_prob, reward) tuple from a rollout."""

    features: TrajectoryFeatures
    decision: RoutingDecision
    log_prob: torch.Tensor
    reward: float  # downstream FWT + BWT signal for this decision


# ---------------------------------------------------------------------------
# RolloutSimulator
# ---------------------------------------------------------------------------


class RolloutSimulator:
    """
    Lightweight surrogate that estimates the downstream reward for a routing
    decision without running the full agent + sleep-phase pipeline.

    The surrogate is a Ridge regression model predicting ``future_task_success``
    from a feature vector composed of:
      - 4-d trajectory feature vector
      - one-hot routing decision (4 dims)
      - normalised memory size (1 dim)

    Total input dimension: 9.
    """

    _INPUT_DIM = 9  # 4 features + 4 one-hot decision + 1 memory size

    def __init__(self) -> None:
        self._model = Ridge(alpha=1.0)
        self._scaler = StandardScaler()
        self._fitted = False

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_input(
        self,
        features_vec: np.ndarray,
        routing_decision: int,
        memory_size: int,
        max_memory_size: float = 2000.0,
    ) -> np.ndarray:
        """Assemble the 9-d input vector for the surrogate."""
        one_hot = np.zeros(_N_CLASSES, dtype=np.float32)
        one_hot[routing_decision] = 1.0
        mem_norm = float(np.clip(memory_size / max(max_memory_size, 1.0), 0.0, 1.0))
        return np.concatenate(
            [features_vec.astype(np.float32), one_hot, [mem_norm]], axis=0
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def fit(self, rollout_data: list[dict]) -> None:
        """
        Fit the surrogate model from collected baseline rollout data.

        Parameters
        ----------
        rollout_data:
            List of dicts, each with keys:
              ``features_vec``         — array-like of length 4
              ``routing_decision``     — int in [0, 3]
              ``memory_size``          — int
              ``actual_future_success`` — float in [0, 1]
        """
        if not rollout_data:
            logger.warning("RolloutSimulator.fit called with empty rollout_data; skipping.")
            return

        X_rows = []
        y_rows = []
        for sample in rollout_data:
            features_vec = np.array(sample["features_vec"], dtype=np.float32)
            routing_decision = int(sample["routing_decision"])
            memory_size = int(sample["memory_size"])
            future_success = float(sample["actual_future_success"])

            x = self._build_input(features_vec, routing_decision, memory_size)
            X_rows.append(x)
            y_rows.append(future_success)

        X = np.stack(X_rows)           # [N, 9]
        y = np.array(y_rows)           # [N]

        X_scaled = self._scaler.fit_transform(X)
        self._model.fit(X_scaled, y)
        self._fitted = True
        logger.info("RolloutSimulator fitted on %d samples.", len(rollout_data))

    def simulate(
        self,
        features: TrajectoryFeatures,
        decision: RoutingDecision,
        memory_size: int,
    ) -> float:
        """
        Return the predicted future_task_success reward for the given decision.

        Falls back to a simple heuristic if the surrogate has not been fitted.

        Returns
        -------
        float in [0, 1].
        """
        features_vec = np.array(
            [features.utility, features.transfer_potential,
             features.retrieval_cost, features.interference_risk],
            dtype=np.float32,
        )
        x = self._build_input(features_vec, int(decision), memory_size)

        if not self._fitted:
            # Heuristic fallback: reward utility, penalise interference.
            return float(np.clip(features.utility * (1.0 - features.interference_risk), 0.0, 1.0))

        x_scaled = self._scaler.transform(x.reshape(1, -1))
        pred = float(self._model.predict(x_scaled)[0])
        return float(np.clip(pred, 0.0, 1.0))


# ---------------------------------------------------------------------------
# MetaTrainer
# ---------------------------------------------------------------------------


class MetaTrainer:
    """
    Meta-learning trainer for the consolidation routing policy using REINFORCE.

    Parameters
    ----------
    policy:
        The :class:`RoutingPolicy` to be meta-trained.
    routing_config:
        Hyper-parameters for the routing policy (meta_lr, entropy_coeff, …).
    lora_config:
        LoRA configuration (kept for future inner-loop integration).
    device:
        PyTorch device string.
    """

    def __init__(
        self,
        policy: RoutingPolicy,
        routing_config: RoutingConfig,
        lora_config: LoRAConfig,
        device: str = "cuda",
    ) -> None:
        self.policy = policy.to(device)
        self.routing_config = routing_config
        self.lora_config = lora_config
        self.device = device

        # Exponential moving-average baseline for REINFORCE variance reduction.
        self._baseline: float = 0.0
        self._baseline_beta: float = 0.9

    # ------------------------------------------------------------------
    # Rollout collection
    # ------------------------------------------------------------------

    def collect_rollout(
        self,
        task_sequences: list[list[TrajectoryFeatures]],
        policy: RoutingPolicy,
        simulator: "RolloutSimulator",
    ) -> list[RolloutEpisode]:
        """
        Collect rollout episodes from the surrogate simulator.

        For each task sequence and each trajectory within it, samples a routing
        decision from the policy, queries the simulator for a reward signal, and
        records the resulting :class:`RolloutEpisode`.

        Parameters
        ----------
        task_sequences:
            List of task sequences; each sequence is a list of
            :class:`TrajectoryFeatures`.
        policy:
            The routing policy to sample decisions from (stochastic).
        simulator:
            The :class:`RolloutSimulator` surrogate for reward estimation.

        Returns
        -------
        List of :class:`RolloutEpisode` objects (one per trajectory).
        """
        rollouts: list[RolloutEpisode] = []
        policy.train()  # enable stochastic sampling

        for sequence in task_sequences:
            memory_size = 0  # simulate growing memory within the sequence
            for features in sequence:
                with torch.enable_grad():
                    decision, log_prob = policy.sample_decision(features)

                reward = simulator.simulate(features, decision, memory_size)

                rollouts.append(
                    RolloutEpisode(
                        features=features,
                        decision=decision,
                        log_prob=log_prob,
                        reward=reward,
                    )
                )

                # Update simulated memory size (EPISODIC decisions grow buffer).
                if decision == RoutingDecision.EPISODIC:
                    memory_size = min(memory_size + 1, 2000)

        return rollouts

    # ------------------------------------------------------------------
    # Meta-gradient update
    # ------------------------------------------------------------------

    def meta_update(
        self,
        rollouts: list[RolloutEpisode],
        optimizer: torch.optim.Optimizer,
    ) -> dict[str, float]:
        """
        Perform a single REINFORCE meta-update.

        Loss:
            L = -mean(log_prob * (reward - baseline)) - entropy_coeff * H(pi)

        Baseline: exponential moving average of rewards (beta=0.9).

        Parameters
        ----------
        rollouts:
            Episodes collected by :meth:`collect_rollout`.
        optimizer:
            The Adam optimiser for policy parameters.

        Returns
        -------
        dict with keys ``policy_loss``, ``entropy``, ``mean_reward``.
        """
        if not rollouts:
            return {"policy_loss": 0.0, "entropy": 0.0, "mean_reward": 0.0}

        rewards = torch.tensor(
            [ep.reward for ep in rollouts], dtype=torch.float32, device=self.device
        )
        mean_reward = float(rewards.mean().item())

        # Update EMA baseline.
        self._baseline = (
            self._baseline_beta * self._baseline
            + (1.0 - self._baseline_beta) * mean_reward
        )
        baseline = self._baseline

        # REINFORCE loss.
        log_probs = torch.stack([ep.log_prob for ep in rollouts]).to(self.device)
        advantages = rewards - baseline
        policy_loss = -(log_probs * advantages).mean()

        # Entropy regularisation (computed over a fresh forward pass).
        features_batch = torch.stack(
            [ep.features.to_tensor() for ep in rollouts]
        ).to(self.device)
        entropy = self.policy.entropy(features_batch)

        total_loss = policy_loss - self.routing_config.entropy_coeff * entropy

        optimizer.zero_grad()
        total_loss.backward()
        optimizer.step()

        return {
            "policy_loss": float(policy_loss.item()),
            "entropy": float(entropy.item()),
            "mean_reward": mean_reward,
        }

    # ------------------------------------------------------------------
    # Training loop
    # ------------------------------------------------------------------

    def train(
        self,
        rollout_data_path: str,
        n_meta_epochs: int = 100,
        n_sequences_per_epoch: int = 8,
    ) -> RoutingPolicy:
        """
        Full meta-training loop.

        Steps
        -----
        1. Load pre-collected rollout data from *rollout_data_path*.
        2. Fit the :class:`RolloutSimulator` surrogate on that data.
        3. Build task sequences from the rollout data.
        4. Initialise the policy from the heuristic prior.
        5. For each meta-epoch:
           a. Sample *n_sequences_per_epoch* task sequences.
           b. Collect rollouts.
           c. Perform :meth:`meta_update`.
           d. Track the best policy by mean reward.
           e. Log to wandb every 10 epochs (if available).
        6. Return the best policy.

        Parameters
        ----------
        rollout_data_path:
            Path to the JSON file produced by :func:`collect_baseline_rollouts`.
        n_meta_epochs:
            Number of outer-loop gradient steps.
        n_sequences_per_epoch:
            Number of task sequences sampled per epoch.

        Returns
        -------
        The best :class:`RoutingPolicy` (by mean reward) seen during training.
        """
        # --- Load rollout data -------------------------------------------
        with open(rollout_data_path) as fh:
            raw_data: list[dict] = json.load(fh)

        if not raw_data:
            raise ValueError(f"Rollout data at {rollout_data_path} is empty.")

        # --- Fit surrogate -----------------------------------------------
        simulator = RolloutSimulator()
        simulator.fit(raw_data)

        # --- Build task sequences from rollout records -------------------
        # Each record becomes a single-trajectory sequence; we group records
        # into fixed-length sequences for the meta-loop.
        seq_len = max(1, len(raw_data) // max(n_sequences_per_epoch, 1))
        all_sequences: list[list[TrajectoryFeatures]] = []
        for i in range(0, len(raw_data), seq_len):
            chunk = raw_data[i : i + seq_len]
            seq: list[TrajectoryFeatures] = []
            for record in chunk:
                fv = np.array(record["features_vec"], dtype=np.float32)
                tf = TrajectoryFeatures(
                    entry_id=str(i),
                    task_type=record.get("task_type", "unknown"),
                    utility=float(fv[0]),
                    transfer_potential=float(fv[1]),
                    retrieval_cost=float(fv[2]),
                    interference_risk=float(fv[3]),
                    embedding=fv,
                )
                seq.append(tf)
            if seq:
                all_sequences.append(seq)

        if not all_sequences:
            raise ValueError("Could not construct any task sequences from rollout data.")

        # --- Initialise policy -------------------------------------------
        self.policy.initialize_from_heuristic()
        optimizer = torch.optim.Adam(
            self.policy.parameters(), lr=self.routing_config.meta_lr
        )

        best_policy_state = {k: v.clone() for k, v in self.policy.state_dict().items()}
        best_mean_reward: float = -float("inf")

        # --- Try importing wandb (optional) ------------------------------
        try:
            import wandb as _wandb
            _use_wandb = _wandb.run is not None
        except ImportError:
            _use_wandb = False

        # --- Meta-training loop ------------------------------------------
        for epoch in range(n_meta_epochs):
            # Sample a subset of sequences.
            n_available = len(all_sequences)
            n_sample = min(n_sequences_per_epoch, n_available)
            sampled = random.sample(all_sequences, n_sample)

            rollouts = self.collect_rollout(sampled, self.policy, simulator)
            metrics = self.meta_update(rollouts, optimizer)

            mean_reward = metrics["mean_reward"]
            if mean_reward > best_mean_reward:
                best_mean_reward = mean_reward
                best_policy_state = {
                    k: v.clone() for k, v in self.policy.state_dict().items()
                }
                logger.debug(
                    "Epoch %d: new best mean_reward=%.4f", epoch, best_mean_reward
                )

            if (epoch + 1) % 10 == 0:
                logger.info(
                    "Meta-epoch %d/%d  policy_loss=%.4f  entropy=%.4f  "
                    "mean_reward=%.4f  best=%.4f",
                    epoch + 1,
                    n_meta_epochs,
                    metrics["policy_loss"],
                    metrics["entropy"],
                    mean_reward,
                    best_mean_reward,
                )
                if _use_wandb:
                    import wandb
                    wandb.log(
                        {
                            "meta/epoch": epoch + 1,
                            "meta/policy_loss": metrics["policy_loss"],
                            "meta/entropy": metrics["entropy"],
                            "meta/mean_reward": mean_reward,
                            "meta/best_mean_reward": best_mean_reward,
                        }
                    )

        # Restore best policy.
        self.policy.load_state_dict(best_policy_state)
        logger.info(
            "Meta-training complete. Best mean_reward=%.4f over %d epochs.",
            best_mean_reward,
            n_meta_epochs,
        )
        return self.policy


# ---------------------------------------------------------------------------
# collect_baseline_rollouts
# ---------------------------------------------------------------------------


def collect_baseline_rollouts(
    env_config: str,
    agent: "ReActAgent",
    memory: "EpisodicMemory",
    n_sequences: int = 50,
    output_path: str = "rollout_data.json",
) -> None:
    """
    Run *n_sequences* task sequences with random routing decisions and record
    (features_vec, routing_decision, memory_size, future_task_success) tuples.

    The collected data is saved to *output_path* as a JSON array and can be
    passed directly to :meth:`RolloutSimulator.fit` or to
    :meth:`MetaTrainer.train`.

    Parameters
    ----------
    env_config:
        Path to the ALFWorld / environment configuration YAML used to build
        task sequences for evaluation.
    agent:
        The :class:`ReActAgent` instance to run episodes with.
    memory:
        The :class:`EpisodicMemory` instance tracking current memory state.
    n_sequences:
        Number of random-policy rollout sequences to run.
    output_path:
        Destination JSON file path.
    """
    from dream_state.environments.alfworld_env import AlfWorldEnv
    from dream_state.memory.features import (
        TrajectoryFeatureExtractor,
        utility_score,
    )

    env = AlfWorldEnv(env_config)
    extractor = TrajectoryFeatureExtractor(
        embed_model_name="sentence-transformers/all-mpnet-base-v2",
        device="cpu",
    )

    records: list[dict] = []
    rng = random.Random(42)

    for seq_idx in range(n_sequences):
        # Sample a random task sequence length (2–6 tasks).
        seq_len = rng.randint(2, 6)
        seq_records: list[dict] = []
        future_successes: list[float] = []

        # First pass: run tasks and collect features.
        episode_results = []
        for _ in range(seq_len):
            result = env.run_episode(agent=agent, memory=memory)
            features = extractor.extract(result=result, memory=memory)
            # Assign a random routing decision (Phase 0 baseline).
            decision = rng.randint(0, _N_CLASSES - 1)

            seq_records.append(
                {
                    "features_vec": [
                        features.utility,
                        features.transfer_potential,
                        features.retrieval_cost,
                        features.interference_risk,
                    ],
                    "routing_decision": decision,
                    "memory_size": len(memory),
                    "task_type": features.task_type,
                    # Placeholder; filled below with look-ahead success.
                    "actual_future_success": 0.0,
                }
            )
            episode_results.append(result)

            # Add to episodic memory regardless (random policy doesn't consolidate).
            memory.add(
                trajectory_text=result.trajectory_text,
                task_type=result.task_type,
                success=result.success,
                utility_score=utility_score(result),
            )

        # Estimate future success as the mean utility of the *next* task in the
        # sequence (lookahead proxy).  For the last task, use the task's own utility.
        for i, rec in enumerate(seq_records):
            if i + 1 < len(episode_results):
                future_result = episode_results[i + 1]
                rec["actual_future_success"] = utility_score(future_result)
            else:
                rec["actual_future_success"] = utility_score(episode_results[i])

        records.extend(seq_records)
        logger.info(
            "Baseline rollout sequence %d/%d complete (%d records so far).",
            seq_idx + 1,
            n_sequences,
            len(records),
        )

    with open(output_path, "w") as fh:
        json.dump(records, fh, indent=2)

    logger.info(
        "Saved %d baseline rollout records to %s.", len(records), output_path
    )
