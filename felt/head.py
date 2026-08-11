"""The Felt head — v1 SCORER (per IMPLEMENTATION_SPEC §2.1 [DECIDED]).

An attention-shaped scorer: a learned goal-query q attends over event
representations h_t; per-event salience â_t = σ(q·k_t/√d + b). Trained by
DISTILLATION on oracle TD-salience (spec §2.2), never on benchmark labels
(§2.5 firewall). Numpy reference implementation with manual gradients — the
GPU tier ports this exactly (same losses, same eval), swapping mock event
embeddings for frozen-LLM hidden states.

KVP adoptions (note 23): trained offline on logged traces; evaluated with the
ALL-BUDGETS ranking objective (sum of retention regret over every cutoff).
"""

from __future__ import annotations

import hashlib

import numpy as np



# ---------------------------------------------------------------- embeddings
def hash_embed(text: str, d: int = 64) -> np.ndarray:
    """Deterministic bag-of-words hash embedding for the CPU tier (mock for
    frozen-LLM hidden states). Word-level so action-structure words ('craft',
    'gather') carry consistent signal across episodes/worlds."""
    v = np.zeros(d)
    for w in text.lower().split():
        seed = int.from_bytes(hashlib.md5(w.encode()).digest()[:4], "little")
        rng = np.random.default_rng(seed)
        v += rng.normal(0, 1, d)
    n = np.linalg.norm(v)
    return v / n if n > 0 else v


def embed_events(trajectory: list, d: int = 64) -> np.ndarray:
    """One event = one step (obs+action). Returns (T, d)."""
    return np.stack([hash_embed(f"{s['action']} {s['obs']}", d)
                     for s in trajectory])


# ---------------------------------------------------------------- the head
class FeltHead:
    """σ(q·(h W_k)/√dk + b): one query, one key projection, one bias."""

    def __init__(self, d_h: int = 64, d_k: int = 32, seed: int = 0, lr: float = 0.05):
        rng = np.random.default_rng(seed)
        self.Wk = rng.normal(0, 0.2, (d_h, d_k))
        self.q = rng.normal(0, 0.2, d_k)
        self.b = 0.0
        self.lr = lr
        self.d_k = d_k

    def salience(self, H: np.ndarray) -> np.ndarray:
        with np.errstate(all="ignore"):   # numpy-2/Accelerate false positives
            z = (H @ self.Wk) @ self.q / np.sqrt(self.d_k) + self.b
        assert np.all(np.isfinite(z)), "head produced non-finite scores"
        return 1.0 / (1.0 + np.exp(-np.clip(z, -30, 30)))

    def train_batch(self, H: np.ndarray, target: np.ndarray) -> float:
        """One gradient step of MSE distillation on one episode. target ∈ [0,1]
        = normalized oracle TD-salience per event. Returns loss."""
        T = H.shape[0]
        with np.errstate(all="ignore"):
            K = H @ self.Wk                              # (T, dk)
        z = K @ self.q / np.sqrt(self.d_k) + self.b
        a = 1.0 / (1.0 + np.exp(-np.clip(z, -30, 30)))
        err = a - target                                  # (T,)
        loss = float((err ** 2).mean())
        dz = 2 * err * a * (1 - a) / T                    # (T,)
        with np.errstate(all="ignore"):
            dq = K.T @ dz / np.sqrt(self.d_k)
            dWk = np.outer(H.T @ dz, self.q) / np.sqrt(self.d_k)
        db = dz.sum()
        self.q -= self.lr * dq
        self.Wk -= self.lr * dWk.reshape(self.Wk.shape)
        self.b -= self.lr * db
        return loss


def normalize_salience(traj: list) -> np.ndarray:
    s = np.array([st["salience"] for st in traj], float)
    m = s.max()
    return s / m if m > 0 else s


def train_head_on_dataset(records: list, d_h: int = 64, epochs: int = 30,
                          seed: int = 0) -> "FeltHead":
    head = FeltHead(d_h=d_h, seed=seed)
    rng = np.random.default_rng(seed)
    idx = np.arange(len(records))
    for _ in range(epochs):
        rng.shuffle(idx)
        for i in idx:
            traj = records[i]["trajectory"]
            if len(traj) < 2:
                continue
            H = embed_events(traj, d_h)
            head.train_batch(H, normalize_salience(traj))
    return head


# ---------------------------------------------------------------- evaluation
def all_budgets_regret(scores: np.ndarray, true_salience: np.ndarray) -> float:
    """KVP-style Σ_b regret: for every budget b, the true-salience mass RANKED OUT
    by `scores`, normalized by the oracle ranking's mass. 0 = perfect ranking,
    1 = worst. Budget-free by construction."""
    T = len(scores)
    order = np.argsort(-scores)
    oracle_order = np.argsort(-true_salience)
    total = 0.0
    worst = 0.0
    for b in range(1, T):
        kept = true_salience[order[:b]].sum()
        best = true_salience[oracle_order[:b]].sum()
        total += best - kept
        worst += best
    return float(total / worst) if worst > 0 else 0.0


def eval_head(head: FeltHead, records: list, d_h: int = 64) -> dict:
    regrets, corrs = [], []
    for rec in records:
        traj = rec["trajectory"]
        if len(traj) < 3:
            continue
        H = embed_events(traj, d_h)
        a = head.salience(H)
        t = normalize_salience(traj)
        regrets.append(all_budgets_regret(a, t))
        if t.std() > 0 and a.std() > 0:
            corrs.append(float(np.corrcoef(a, t)[0, 1]))
    return {"all_budgets_regret": float(np.mean(regrets)),
            "salience_corr": float(np.mean(corrs)) if corrs else float("nan"),
            "n": len(regrets)}
