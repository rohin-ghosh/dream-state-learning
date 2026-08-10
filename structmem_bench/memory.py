"""Memory methods under test. Each returns a per-fact SCORE vector (higher = more
likely kept). Retention at budget K = the top-K facts by score. Relational methods
also expose a per-pair score.

Methods only observe (X presence, value samples, y outcomes) — NEVER fact_type or
relations (those are ground truth used solely for scoring).
"""

from __future__ import annotations

from itertools import combinations

import numpy as np

from .tasks import Stream


# ---- per-fact summaries a method may use ----
def _summaries(s: Stream):
    X, V = s.X, s.value
    count = X.sum(0)                                  # frequency
    last = np.where(X > 0, np.arange(X.shape[0])[:, None], -1).max(0)  # recency
    with np.errstate(invalid="ignore", divide="ignore"):
        vmax = np.where(X > 0, V, -np.inf).max(0)
        vsum = V.sum(0)
        vmean = np.divide(vsum, count, out=np.zeros_like(vsum), where=count > 0)
    vmax = np.where(np.isfinite(vmax), vmax, 0.0)
    return count, last, vmax, vsum, vmean


def _logreg(F, y, l2=1.0, iters=400, lr=0.5):
    # np.errstate guards a spurious numpy-2.0/Apple-Accelerate matmul warning; results
    # are finite (asserted below).
    with np.errstate(all="ignore"):
        n, d = F.shape
        w = np.zeros(d); b = 0.0
        for _ in range(iters):
            z = np.clip(F @ w + b, -30, 30)
            g = 1 / (1 + np.exp(-z)) - y
            w -= lr * (F.T @ g / n + l2 * w / n)
            b -= lr * g.mean()
    assert np.all(np.isfinite(w)), "logreg diverged to non-finite weights"
    return w


# ============================ per-fact methods ============================
def score_random(s: Stream, rng) -> np.ndarray:
    return rng.random(s.cfg.n_facts)


def score_truncation(s: Stream, rng) -> np.ndarray:
    _, last, *_ = _summaries(s)
    return last.astype(float)


def score_frequency(s: Stream, rng) -> np.ndarray:
    count, *_ = _summaries(s)
    return count.astype(float)


def score_surprise(s: Stream, rng) -> np.ndarray:
    """ATLAS-style proxy: novelty = inverse frequency + first-seen bonus. A stand-in
    for gradient-surprise in the abstract tier (surprising = rare/new)."""
    count, last, *_ = _summaries(s)
    # surprising things are rare AND recent-first-seen; monotone in 1/count
    return 1.0 / (count + 1.0)


def score_value_max(s: Stream, rng) -> np.ndarray:
    *_, vmax, _, _ = _summaries(s)
    return vmax


def score_value_mean(s: Stream, rng) -> np.ndarray:
    *_, vmean = _summaries(s)
    return vmean


def score_value_z(s: Stream, rng) -> np.ndarray:
    """z-score = vsum / sqrt(count) = mean * sqrt(count). The SUFFICIENT STATISTIC for
    'is this fact's per-appearance value mean > 0' under value ~ N(mu, 1). Uniquely
    both frequency-neutral (passes the d'=0 canary, unlike max/sum) AND evidence-
    accumulating (uses sample size, unlike mean). Audit finding: this is the value
    aggregation that DOES beat frequency at every d'>0 — correcting exp1's earlier
    'no clean aggregation beats frequency' overcorrection."""
    count, _, _, vsum, _ = _summaries(s)
    with np.errstate(all="ignore"):
        z = np.divide(vsum, np.sqrt(count), out=np.zeros_like(vsum), where=count > 0)
    return z


def score_trained_value(s: Stream, rng) -> np.ndarray:
    """Per-item value trained on outcomes (logreg on presence -> y)."""
    return _logreg(s.X, s.y)


def score_oracle(s: Stream, rng) -> np.ndarray:
    return s.is_structural.astype(float)


PER_FACT = {
    "random": score_random,
    "truncation": score_truncation,
    "frequency": score_frequency,
    "surprise": score_surprise,
    "value_max": score_value_max,
    "value_mean": score_value_mean,
    "value_z": score_value_z,
    "trained_value": score_trained_value,
    "oracle": score_oracle,
}


# ============================ relational methods ============================
def candidate_pairs(s: Stream, min_cooc: int = 3):
    """Enumerate candidate relation pairs, restricted to pairs that CO-OCCUR at least
    `min_cooc` times. This is what any relation-learner would plausibly consider — and
    it excludes the spurious single-co-occurrence pairs created by one-shot details
    (which otherwise explode and dilute the candidate set; red-team / exp3 caveat).
    A true recipe pair co-occurs many times, so it survives; a one-shot coincidence
    does not. Returns (pairs, matrix) where matrix[:,k] = fact_i AND fact_j."""
    X = s.X
    F = s.cfg.n_facts
    with np.errstate(all="ignore"):
        cooc = (X.T @ X)  # (F,F) co-occurrence counts
    pairs = [(i, j) for i, j in combinations(range(F), 2) if cooc[i, j] >= min_cooc]
    if not pairs:  # fall back so the metric is defined on degenerate configs
        pairs = [(i, j) for i, j in combinations(range(F), 2) if cooc[i, j] > 0]
    M = np.empty((X.shape[0], len(pairs)))
    for k, (i, j) in enumerate(pairs):
        M[:, k] = X[:, i] * X[:, j]
    return pairs, M


def score_relational(s: Stream, rng):
    """Learned per-PAIR value: logreg on pair-presence -> y. Returns (pairs, scores)."""
    pairs, M = candidate_pairs(s)
    if len(pairs) == 0:
        return pairs, np.zeros(0)
    w = _logreg(M, s.y)
    return pairs, w


def score_item_lifted(s: Stream, rng):
    """Best per-item value lifted to pairs (baseline for relational eval). A pair is
    valuable iff BOTH facts are individually valuable, so lift by the product of the
    POSITIVE parts (relu-product) — not a raw signed product, under which two strongly
    ANTI-predictive facts would score as high as two predictive ones (audit finding).
    This is a strictly stronger/fairer per-item baseline; relational still beats it."""
    v = score_trained_value(s, rng)
    vp = np.maximum(v, 0.0)
    pairs, _ = candidate_pairs(s)
    scores = np.array([vp[i] * vp[j] for (i, j) in pairs])
    return pairs, scores


RELATIONAL = {
    "relational": score_relational,
    "item_lifted": score_item_lifted,
}
