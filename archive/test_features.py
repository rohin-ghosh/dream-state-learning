"""
Unit tests for dream_state.memory.features.

All tests use mock EpisodeResult objects so that no model downloads or
GPU/FAISS infrastructure are required.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

import numpy as np
import pytest
import torch


# ---------------------------------------------------------------------------
# Minimal EpisodeResult stub (mirrors dream_state.environments.alfworld_env)
# ---------------------------------------------------------------------------

@dataclass
class _MockEpisodeResult:
    """Minimal stand-in for EpisodeResult used by feature functions."""

    task_path: str = "mock/task"
    task_type: str = "pick"
    success: bool = True
    steps_taken: int = 5
    observations: List[str] = field(default_factory=list)
    thoughts: List[str] = field(default_factory=list)
    actions: List[str] = field(default_factory=list)
    rewards: List[float] = field(default_factory=lambda: [1.0])
    total_reward: float = 1.0
    trajectory_text: str = "pick up the apple and place it in the fridge"


# ---------------------------------------------------------------------------
# Import the functions under test
# ---------------------------------------------------------------------------

from dream_state.memory.features import (
    TrajectoryFeatures,
    interference_risk,
    retrieval_cost,
    utility_score,
)


# ---------------------------------------------------------------------------
# test_utility_score_success
# ---------------------------------------------------------------------------


def test_utility_score_success() -> None:
    """A successful episode must yield utility >= 0.6."""
    result = _MockEpisodeResult(
        success=True,
        steps_taken=3,
        rewards=[1.0, 1.0, 1.0],
        total_reward=3.0,
        trajectory_text="some trajectory",
    )
    score = utility_score(result)
    assert score >= 0.6, f"Expected utility >= 0.6 for success, got {score}"


# ---------------------------------------------------------------------------
# test_utility_score_failure
# ---------------------------------------------------------------------------


def test_utility_score_failure() -> None:
    """A failed episode with zero rewards must yield utility < 0.4."""
    result = _MockEpisodeResult(
        success=False,
        steps_taken=10,
        rewards=[0.0] * 10,
        total_reward=0.0,
        trajectory_text="failed trajectory",
    )
    score = utility_score(result)
    assert score < 0.4, f"Expected utility < 0.4 for failure, got {score}"


# ---------------------------------------------------------------------------
# test_retrieval_cost_normalization
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "text",
    [
        "",                                   # empty trajectory
        "short",                              # very short
        "x" * 2000,                          # mid-length
        "x" * 4000,                          # exactly at normalisation bound
        "x" * 8000,                          # exceeds bound — should clip to 1.0
    ],
)
def test_retrieval_cost_normalization(text: str) -> None:
    """retrieval_cost must always return a value in [0, 1]."""
    result = _MockEpisodeResult(
        success=True,
        steps_taken=1,
        rewards=[0.0],
        total_reward=0.0,
        trajectory_text=text,
    )
    cost = retrieval_cost(result)
    assert 0.0 <= cost <= 1.0, f"retrieval_cost={cost} out of [0, 1] for text length {len(text)}"


# ---------------------------------------------------------------------------
# test_interference_risk_no_adapters
# ---------------------------------------------------------------------------


def test_interference_risk_no_adapters() -> None:
    """When adapter_basis is None, interference_risk must return exactly 0.0."""
    embedding = np.random.default_rng(0).standard_normal(768).astype(np.float32)
    risk = interference_risk(embedding, adapter_basis=None, proj_dim=64)
    assert risk == 0.0, f"Expected 0.0 with no adapters, got {risk}"


# ---------------------------------------------------------------------------
# test_to_tensor_shape
# ---------------------------------------------------------------------------


def test_to_tensor_shape() -> None:
    """TrajectoryFeatures.to_tensor() must return a 1-D float32 tensor of length 4."""
    features = TrajectoryFeatures(
        entry_id="test-id",
        task_type="pick",
        utility=0.8,
        transfer_potential=0.5,
        retrieval_cost=0.3,
        interference_risk=0.1,
        embedding=np.zeros(768, dtype=np.float32),
    )
    tensor = features.to_tensor()
    assert isinstance(tensor, torch.Tensor), "to_tensor() must return a torch.Tensor"
    assert tensor.dtype == torch.float32, f"Expected float32, got {tensor.dtype}"
    assert tensor.shape == (4,), f"Expected shape (4,), got {tensor.shape}"
    # Verify the values are packed in the documented order
    assert torch.allclose(
        tensor,
        torch.tensor([0.8, 0.5, 0.3, 0.1], dtype=torch.float32),
    ), f"Unexpected tensor values: {tensor.tolist()}"
