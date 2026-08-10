"""
Consolidation routing policy for Dream-State Learning.

Maps trajectory features [utility, transfer_potential, retrieval_cost,
interference_risk] to a routing decision: EPISODIC | SEMANTIC | PARAMETRIC | NONE.
"""

from __future__ import annotations

import logging
from typing import Optional

import torch
import torch.nn as nn
import torch.nn.functional as F

from dream_state.config import RoutingConfig
from dream_state.memory.features import TrajectoryFeatures
from dream_state.training.sleep_phase import RoutingDecision

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# RoutingPolicy
# ---------------------------------------------------------------------------


class RoutingPolicy(nn.Module):
    """4-layer MLP routing policy for consolidation decisions.

    Architecture
    ------------
    input (4) -> [Linear -> LayerNorm -> ReLU -> Dropout(0.1)] x len(hidden_dims)
              -> Linear -> logits (n_classes)

    Parameters
    ----------
    input_dim:
        Dimension of the input feature vector (default 4).
    hidden_dims:
        Sequence of hidden layer widths (default [128, 64, 32]).
    n_classes:
        Number of routing classes (default 4: EPISODIC, SEMANTIC, PARAMETRIC, NONE).
    """

    def __init__(
        self,
        input_dim: int = 4,
        hidden_dims: list[int] = [128, 64, 32],
        n_classes: int = 4,
    ) -> None:
        super().__init__()

        layers: list[nn.Module] = []
        in_dim = input_dim
        for h_dim in hidden_dims:
            linear = nn.Linear(in_dim, h_dim)
            nn.init.kaiming_uniform_(linear.weight, nonlinearity="relu")
            nn.init.zeros_(linear.bias)
            layers.extend([
                linear,
                nn.LayerNorm(h_dim),
                nn.ReLU(),
                nn.Dropout(p=0.1),
            ])
            in_dim = h_dim

        head = nn.Linear(in_dim, n_classes)
        nn.init.kaiming_uniform_(head.weight, nonlinearity="relu")
        nn.init.zeros_(head.bias)
        layers.append(head)

        self.net = nn.Sequential(*layers)
        self.n_classes = n_classes

    def forward(self, features: torch.Tensor) -> torch.Tensor:
        """Compute routing logits.

        Parameters
        ----------
        features:
            Float tensor of shape [batch_size, 4] or [4].

        Returns
        -------
        torch.Tensor
            Logits of shape [batch_size, n_classes] or [n_classes].
        """
        squeezed = features.dim() == 1
        x = features.unsqueeze(0) if squeezed else features
        logits = self.net(x)
        return logits.squeeze(0) if squeezed else logits

    def route(
        self,
        features: TrajectoryFeatures,
        temperature: float = 1.0,
    ) -> RoutingDecision:
        """Route a single trajectory to a consolidation store.

        At temperature=0 uses greedy argmax; otherwise samples from the
        softmax distribution scaled by temperature.

        Parameters
        ----------
        features:
            Feature dataclass for one trajectory.
        temperature:
            Sampling temperature. 0 => greedy argmax.

        Returns
        -------
        RoutingDecision
        """
        self.eval()
        with torch.no_grad():
            x = features.to_tensor()
            logits = self.forward(x)  # [n_classes]

            if temperature == 0.0:
                idx = int(logits.argmax().item())
            else:
                probs = F.softmax(logits / temperature, dim=-1)
                idx = int(torch.multinomial(probs, num_samples=1).item())

        return RoutingDecision(idx)

    def route_batch(
        self,
        features_list: list[TrajectoryFeatures],
        temperature: float = 1.0,
    ) -> list[RoutingDecision]:
        """Route a batch of trajectories.

        Parameters
        ----------
        features_list:
            List of TrajectoryFeatures, one per trajectory.
        temperature:
            Sampling temperature passed to each routing call.

        Returns
        -------
        list[RoutingDecision]
        """
        self.eval()
        with torch.no_grad():
            x = torch.stack([f.to_tensor() for f in features_list])  # [B, 4]
            logits = self.forward(x)  # [B, n_classes]

            if temperature == 0.0:
                indices = logits.argmax(dim=-1).tolist()
            else:
                probs = F.softmax(logits / temperature, dim=-1)  # [B, n_classes]
                indices = torch.multinomial(probs, num_samples=1).squeeze(1).tolist()

        return [RoutingDecision(int(i)) for i in indices]


# ---------------------------------------------------------------------------
# HeuristicRouter
# ---------------------------------------------------------------------------


class HeuristicRouter:
    """Deterministic rule-based router for baseline comparison and warm-start.

    Rules (evaluated in order)
    --------------------------
    1. utility > 0.7 and interference_risk < 0.4  -> PARAMETRIC
    2. utility > 0.4 and transfer_potential > 0.6  -> SEMANTIC
    3. utility > 0.3                               -> EPISODIC
    4. otherwise                                   -> NONE
    """

    def route(self, features: TrajectoryFeatures) -> RoutingDecision:
        """Deterministically route one trajectory.

        Parameters
        ----------
        features:
            Feature dataclass for the trajectory.

        Returns
        -------
        RoutingDecision
        """
        u = features.utility
        tp = features.transfer_potential
        ir = features.interference_risk

        if u > 0.7 and ir < 0.4:
            return RoutingDecision.PARAMETRIC
        elif u > 0.4 and tp > 0.6:
            return RoutingDecision.SEMANTIC
        elif u > 0.3:
            return RoutingDecision.EPISODIC
        else:
            return RoutingDecision.NONE


# ---------------------------------------------------------------------------
# initialize_from_heuristic
# ---------------------------------------------------------------------------


def initialize_from_heuristic(
    policy: RoutingPolicy,
    n_samples: int = 1000,
    lr: float = 1e-3,
    epochs: int = 50,
) -> RoutingPolicy:
    """Warm-start a RoutingPolicy by imitating the HeuristicRouter.

    Generates *n_samples* synthetic feature vectors drawn uniformly from
    [0, 1]^4, labels them with HeuristicRouter, then trains *policy* with
    cross-entropy loss for *epochs* passes over the dataset.

    Parameters
    ----------
    policy:
        The RoutingPolicy to warm-start (modified in-place and returned).
    n_samples:
        Number of synthetic samples to generate.
    lr:
        Adam learning rate.
    epochs:
        Number of full passes over the synthetic dataset.

    Returns
    -------
    RoutingPolicy
        The same policy object after warm-start training.
    """
    heuristic = HeuristicRouter()

    # Generate synthetic features as plain floats so we can call HeuristicRouter
    # without constructing full TrajectoryFeatures dataclasses (only 4 scalars
    # are needed by the heuristic and by to_tensor).
    import dataclasses
    import numpy as np

    rng = torch.Generator()
    rng.manual_seed(42)
    raw = torch.rand(n_samples, 4, generator=rng)  # [N, 4]

    # Build minimal TrajectoryFeatures stubs for heuristic labelling.
    labels: list[int] = []
    for i in range(n_samples):
        u, tp, rc, ir = raw[i].tolist()
        stub = TrajectoryFeatures(
            entry_id="",
            task_type="",
            utility=u,
            transfer_potential=tp,
            retrieval_cost=rc,
            interference_risk=ir,
            embedding=np.zeros(1, dtype=np.float32),
        )
        labels.append(int(heuristic.route(stub)))

    label_tensor = torch.tensor(labels, dtype=torch.long)  # [N]

    policy.train()
    optimizer = torch.optim.Adam(policy.parameters(), lr=lr)

    for epoch in range(epochs):
        optimizer.zero_grad()
        logits = policy(raw)  # [N, n_classes]
        loss = F.cross_entropy(logits, label_tensor)
        loss.backward()
        optimizer.step()

        if (epoch + 1) % 10 == 0:
            logger.info(
                "initialize_from_heuristic: epoch %d/%d  loss=%.4f",
                epoch + 1,
                epochs,
                loss.item(),
            )

    policy.eval()
    logger.info("initialize_from_heuristic: warm-start complete.")
    return policy


# ---------------------------------------------------------------------------
# save_policy / load_policy
# ---------------------------------------------------------------------------


def save_policy(policy: RoutingPolicy, path: str) -> None:
    """Serialize policy weights and architecture config to *path*.

    Parameters
    ----------
    policy:
        The RoutingPolicy to save.
    path:
        Destination file path (e.g. ``"routing_policy.pt"``).
    """
    # Infer hidden_dims from the Sequential structure.
    hidden_dims: list[int] = []
    for module in policy.net:
        if isinstance(module, nn.LayerNorm):
            hidden_dims.append(module.normalized_shape[0])

    # Recover input_dim from the first Linear layer.
    first_linear = next(m for m in policy.net if isinstance(m, nn.Linear))
    input_dim = first_linear.in_features

    torch.save(
        {
            "state_dict": policy.state_dict(),
            "input_dim": input_dim,
            "hidden_dims": hidden_dims,
            "n_classes": policy.n_classes,
        },
        path,
    )
    logger.info("Saved RoutingPolicy to %s.", path)


def load_policy(path: str, config: RoutingConfig) -> RoutingPolicy:
    """Load a RoutingPolicy from *path*, using *config* for defaults.

    Architecture parameters stored in the checkpoint take precedence over
    *config* values; *config* is used only if the checkpoint pre-dates the
    storage of those fields.

    Parameters
    ----------
    path:
        Path to a checkpoint produced by :func:`save_policy`.
    config:
        RoutingConfig whose fields are used as fallback architecture params.

    Returns
    -------
    RoutingPolicy
        Policy with weights loaded, set to eval mode.
    """
    checkpoint = torch.load(path, map_location="cpu", weights_only=False)

    input_dim: int = checkpoint.get("input_dim", 4)
    hidden_dims: list[int] = checkpoint.get("hidden_dims", list(config.hidden_dims))
    n_classes: int = checkpoint.get("n_classes", config.n_classes)

    policy = RoutingPolicy(
        input_dim=input_dim,
        hidden_dims=hidden_dims,
        n_classes=n_classes,
    )
    policy.load_state_dict(checkpoint["state_dict"])
    policy.eval()
    logger.info("Loaded RoutingPolicy from %s.", path)
    return policy
