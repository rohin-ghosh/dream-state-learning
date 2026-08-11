"""Fast-weight MLP memory (ATLAS-style substrate) with value-modulated writes.

Memory = the weights of a small 2-layer MLP trained to map fact-keys to
fact-values (M(k) ≈ v). Write = weighted gradient steps (a sleep batch ≈ the
Omega-rule window spirit); read = forward pass; probe = retrieval cosine.
SURPRISE is native (per-item pre-write loss = gradient-magnitude proxy) and KEPT,
per spec §3.1: write weight w_i = surprise_i × (1 + β·a_i), where a_i is the
head's salience. β=0 recovers the surprise-only (stock-substrate) baseline.

Numpy, manual backprop — the reference contract for the GPU/torch port.
Upgrades exp4's linear store to a real MLP: nonlinear capacity, real interference.
"""

from __future__ import annotations

import numpy as np

np.seterr(all="ignore")  # spurious Accelerate warnings; finiteness asserted in tests


class FastWeightMemory:
    def __init__(self, d_key: int = 32, d_val: int = 32, hidden: int = 64,
                 seed: int = 0, lr: float = 0.15, decay: float = 1e-3):
        rng = np.random.default_rng(seed)
        self.W1 = rng.normal(0, 0.3, (d_key, hidden))
        self.b1 = np.zeros(hidden)
        self.W2 = rng.normal(0, 0.3, (hidden, d_val))
        self.b2 = np.zeros(d_val)
        self.lr = lr
        self.decay = decay

    # ------------------------------------------------------------- forward
    def read(self, K: np.ndarray) -> np.ndarray:
        """(N, d_key) -> (N, d_val)."""
        Z = np.maximum(0, K @ self.W1 + self.b1)
        return Z @ self.W2 + self.b2

    def surprise(self, K: np.ndarray, V: np.ndarray) -> np.ndarray:
        """Per-item pre-write loss (gradient-magnitude proxy): how unexpected is
        this association to the current weights."""
        err = self.read(K) - V
        return (err ** 2).mean(axis=1)

    # ------------------------------------------------------------- write
    def write_batch(self, K: np.ndarray, V: np.ndarray, weights: np.ndarray,
                    steps: int = 20) -> None:
        """Sleep-batch consolidation: `steps` gradient steps on the WEIGHTED
        associative loss Σ_i w_i ||M(k_i) − v_i||², plus weight decay (the
        substrate's native forgetting)."""
        w = np.maximum(np.asarray(weights, float), 0.0)
        if w.sum() <= 0:
            return
        w = w / w.mean()                       # scale-free: only allocation matters
        n = len(K)
        for _ in range(steps):
            Z1 = K @ self.W1 + self.b1
            A1 = np.maximum(0, Z1)
            pred = A1 @ self.W2 + self.b2
            err = (pred - V) * w[:, None] / n
            gW2 = A1.T @ err + self.decay * self.W2
            gb2 = err.sum(0)
            dA1 = err @ self.W2.T
            dZ1 = dA1 * (Z1 > 0)
            gW1 = K.T @ dZ1 + self.decay * self.W1
            gb1 = dZ1.sum(0)
            self.W1 -= self.lr * gW1
            self.b1 -= self.lr * gb1
            self.W2 -= self.lr * gW2
            self.b2 -= self.lr * gb2

    # ------------------------------------------------------------- probes
    def probe(self, K: np.ndarray, V: np.ndarray) -> np.ndarray:
        """Retrieval quality per fact: cosine(M(k_i), v_i). This is the
        benchmark's parametric probe_fact — 'did the weights retain fact X'."""
        pred = self.read(K)
        num = (pred * V).sum(axis=1)
        den = np.linalg.norm(pred, axis=1) * np.linalg.norm(V, axis=1) + 1e-9
        return num / den


def value_modulated_weights(surprise: np.ndarray, salience: np.ndarray,
                            beta: float) -> np.ndarray:
    """Spec §3.1: w_i = surprise_i × (1 + β·a_i). β=0 = stock substrate."""
    return surprise * (1.0 + beta * np.maximum(salience, 0.0))
