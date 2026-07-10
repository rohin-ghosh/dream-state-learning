"""
Per-trajectory feature computation for the Dream-State consolidation routing policy.

All four features are normalized to [0, 1] and computable without running
actual LoRA fine-tuning (fast, O(r*d) or less per feature).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field

import numpy as np
import torch
from sentence_transformers import SentenceTransformer

from dream_state.environments.alfworld_env import EpisodeResult
from dream_state.memory.episodic import EpisodicMemory


# ---------------------------------------------------------------------------
# Scalar feature functions
# ---------------------------------------------------------------------------


def utility_score(result: EpisodeResult) -> float:
    """
    Compute a utility score in [0, 1] for the given episode result.

    score = 0.6 * success_binary + 0.4 * efficiency

    where:
        success_binary = 1.0 if result.success else 0.0
        efficiency     = goal_conditions_met / max(steps_taken, 1), clipped to [0, 1]
        goal_conditions_met is estimated as mean(rewards), clipped to [0, 1].
    """
    success_binary: float = 1.0 if result.success else 0.0

    if result.rewards:
        goal_conditions_met = float(np.clip(
            sum(result.rewards) / len(result.rewards), 0.0, 1.0
        ))
    else:
        goal_conditions_met = 0.0

    efficiency = float(np.clip(
        goal_conditions_met / max(result.steps_taken, 1), 0.0, 1.0
    ))

    return float(np.clip(0.6 * success_binary + 0.4 * efficiency, 0.0, 1.0))


def transfer_potential(
    trajectory_embedding: np.ndarray,
    memory: EpisodicMemory,
) -> float:
    """
    Estimate how similar the trajectory is to past successful episodes.

    High transfer_potential means the new trajectory is similar to past
    successes, i.e., it is less novel and a lower priority for parametric
    consolidation.

    Returns 0.5 (neutral) if memory has fewer than 3 entries.
    Otherwise returns cosine similarity between trajectory_embedding and the
    centroid of successful-entry embeddings, scaled to [0, 1]: (sim + 1) / 2.
    """
    if len(memory) < 3:
        return 0.5

    successful_embeddings = [
        e.embedding for e in memory.entries if e.success
    ]

    if not successful_embeddings:
        return 0.5

    centroid = np.mean(successful_embeddings, axis=0).astype(np.float32)

    # Cosine similarity
    traj_norm = np.linalg.norm(trajectory_embedding)
    centroid_norm = np.linalg.norm(centroid)

    if traj_norm == 0.0 or centroid_norm == 0.0:
        return 0.5

    cosine_sim = float(
        np.dot(trajectory_embedding, centroid) / (traj_norm * centroid_norm)
    )
    cosine_sim = float(np.clip(cosine_sim, -1.0, 1.0))

    return float((cosine_sim + 1.0) / 2.0)


def retrieval_cost(result: EpisodeResult) -> float:
    """
    Proxy for how expensive it would be to retrieve this episode at inference
    time (token cost).

    cost = len(result.trajectory_text) / 4000.0, clipped to [0, 1].
    """
    return float(np.clip(len(result.trajectory_text) / 4000.0, 0.0, 1.0))


def interference_risk(
    trajectory_embedding: np.ndarray,
    adapter_basis: np.ndarray | None,
    proj_dim: int = 64,
) -> float:
    """
    Estimate the risk that consolidating this trajectory would interfere with
    existing adapters.

    - If adapter_basis is None: returns 0.0 (no existing adapters).
    - adapter_basis: shape [n_adapters, D] matrix of existing adapter direction
      embeddings.
    - Uses a random projection (R ~ N(0, 1/proj_dim), shape [D, proj_dim],
      columns L2-normalised) to reduce dimensionality.
    - Returns (max_cosine_sim + 1) / 2 where max_cosine_sim is the maximum
      cosine similarity between the projected trajectory and any projected
      adapter row.
    """
    if adapter_basis is None:
        return 0.0

    D = trajectory_embedding.shape[0]

    rng = np.random.default_rng(seed=42)
    R = rng.standard_normal((D, proj_dim)).astype(np.float32) / np.sqrt(proj_dim)

    # Normalize each column of R to unit length
    col_norms = np.linalg.norm(R, axis=0, keepdims=True)
    col_norms = np.where(col_norms == 0.0, 1.0, col_norms)
    R = R / col_norms

    # Project trajectory embedding: shape [proj_dim]
    v = trajectory_embedding.astype(np.float32) @ R

    # Project adapter basis rows: shape [n_adapters, proj_dim]
    A = adapter_basis.astype(np.float32) @ R

    # Cosine similarities between v and each row of A
    v_norm = np.linalg.norm(v)
    if v_norm == 0.0:
        return 0.0

    a_norms = np.linalg.norm(A, axis=1)  # [n_adapters]
    # Avoid division by zero
    safe_norms = np.where(a_norms == 0.0, 1.0, a_norms)

    cosine_sims = (A @ v) / (safe_norms * v_norm)  # [n_adapters]
    max_cosine_sim = float(np.clip(np.max(cosine_sims), -1.0, 1.0))

    return float((max_cosine_sim + 1.0) / 2.0)


# ---------------------------------------------------------------------------
# TrajectoryFeatures dataclass
# ---------------------------------------------------------------------------


@dataclass
class TrajectoryFeatures:
    """Per-trajectory feature vector used by the consolidation routing policy."""

    entry_id: str
    task_type: str
    utility: float
    transfer_potential: float
    retrieval_cost: float
    interference_risk: float
    embedding: np.ndarray

    def to_tensor(self) -> torch.Tensor:
        """Return a [4] float32 tensor of [utility, transfer_potential, retrieval_cost, interference_risk]."""
        return torch.tensor(
            [self.utility, self.transfer_potential, self.retrieval_cost, self.interference_risk],
            dtype=torch.float32,
        )


# ---------------------------------------------------------------------------
# TrajectoryFeatureExtractor
# ---------------------------------------------------------------------------


class TrajectoryFeatureExtractor:
    """
    Encodes trajectories and computes all four consolidation-routing features.

    Parameters
    ----------
    embed_model_name:
        Name of the sentence-transformers model to use for encoding trajectory text.
    proj_dim:
        Dimensionality of the random projection used in interference_risk.
    device:
        Device for the sentence-transformer model ("cuda" or "cpu").
    """

    def __init__(
        self,
        embed_model_name: str,
        proj_dim: int = 64,
        device: str = "cuda",
    ) -> None:
        self.embed_model = SentenceTransformer(embed_model_name, device=device)
        self.proj_dim = proj_dim
        self.device = device

        # Fix the random projection matrix at init time (seed=42) so that the
        # same projection is used across all calls.
        # Actual projection is re-derived inside interference_risk using seed=42,
        # so the matrix here is kept for reference / future use.
        embed_dim = self.embed_model.get_sentence_embedding_dimension()
        rng = np.random.default_rng(seed=42)
        R = rng.standard_normal((embed_dim, proj_dim)).astype(np.float32) / np.sqrt(proj_dim)
        col_norms = np.linalg.norm(R, axis=0, keepdims=True)
        col_norms = np.where(col_norms == 0.0, 1.0, col_norms)
        self._R: np.ndarray = R / col_norms

    def _encode(self, text: str) -> np.ndarray:
        """Return a unit-normalised float32 embedding for *text*."""
        vec = self.embed_model.encode(
            text, convert_to_numpy=True, normalize_embeddings=True
        )
        return vec.astype(np.float32)

    def extract(
        self,
        result: EpisodeResult,
        memory: EpisodicMemory,
        adapter_basis: np.ndarray | None = None,
    ) -> TrajectoryFeatures:
        """
        Compute all four features for *result* and return a TrajectoryFeatures.

        Parameters
        ----------
        result:
            The episode result containing trajectory text, rewards, steps, etc.
        memory:
            Current episodic memory buffer (used for transfer_potential).
        adapter_basis:
            Optional [n_adapters, D] matrix of existing adapter directions
            (used for interference_risk). Pass None if no adapters exist yet.
        """
        embedding = self._encode(result.trajectory_text)

        u = utility_score(result)
        tp = transfer_potential(embedding, memory)
        rc = retrieval_cost(result)
        ir = interference_risk(embedding, adapter_basis, proj_dim=self.proj_dim)

        return TrajectoryFeatures(
            entry_id=str(uuid.uuid4()),
            task_type=result.task_type,
            utility=u,
            transfer_potential=tp,
            retrieval_cost=rc,
            interference_risk=ir,
            embedding=embedding,
        )
