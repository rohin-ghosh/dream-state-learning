"""
Experiment 4 — END-TO-END miniature of the Paper-A architecture, on CPU.

The full loop, with the train/eval separation Rohin insisted on (correcting an
earlier error): the value head trains ONLY on task outcomes; the benchmark's
retention probes are a held-out exam it never sees.

    episodes (+outcomes) ──> value head (trained on outcomes ONLY)
                                    │ write weights
                                    ▼
                  REAL capacity-limited associative memory
                  (superposition; interference is physical, not simulated)
                                    │ retrieval strengths
                                    ▼
                  benchmark probes (ground-truth labels, never seen in training)

Memory model (linear associative / Hopfield-family):
  * Each fact f gets a fixed random unit key k_f ∈ R^d.
  * PER-FACT memory:    M ← Σ_f W_f · k_f k_fᵀ      (auto-associative)
  * RELATIONAL memory:  R ← Σ_(i,j) W_ij · k_i k_jᵀ  (hetero-associative bindings
                          for co-present pairs)
  * Retrieval strength: fact f → k_fᵀ M k_f ; pair (i,j) → k_iᵀ R k_j.
  * With #facts ≫ d, random-key crosstalk ~ O(√(Σ W²)/√d) is REAL interference —
    a fixed write budget must be ALLOCATED (the capital story made physical).

FAIRNESS: every method's total write budget is normalized (Σ|W| = const), so this
is purely a comparison of ALLOCATION policies, not write energy.

Conditions (per-fact memory): uniform (natural repetition), surprise (1/count,
ATLAS-proxy), value_z (untrained noisy tags), trained_item (logreg on outcomes),
oracle. Relational memory: cooc (co-occurrence), trained_rel (pair-logreg on
outcomes), oracle_rel.

Questions:
  Q1 (R1 crux): does outcome-trained weighting survive REAL interference?
  Q2 (capacity): does the advantage GROW as memory shrinks (selection under
     scarcity — the bitter-lesson/capital curve)?
  Q3 (relational): do outcome-trained pair-weights preserve true recipes in a
     binding memory under interference?
  Canary: at value_dprime=0 the untrained value method must NOT beat uniform.

numpy only. Uses structmem_bench for generation + tie-safe metrics + paired stats.
"""

from __future__ import annotations

import numpy as np

from structmem_bench.config import BenchConfig
from structmem_bench.tasks import generate
from structmem_bench.memory import _logreg, candidate_pairs
from structmem_bench.metrics import average_precision
from structmem_bench.stats import paired_diff


# ---------------------------------------------------------------- memory physics
def make_keys(rng, n_facts, d):
    K = rng.normal(0, 1, size=(n_facts, d))
    K /= np.linalg.norm(K, axis=1, keepdims=True)
    return K


def write_per_fact(K, W, budget=100.0):
    """M = Σ W_f k_f k_fᵀ with Σ|W| normalized to `budget`."""
    W = np.maximum(np.asarray(W, float), 0.0)
    s = W.sum()
    if s <= 0:
        W = np.ones_like(W)
        s = W.sum()
    W = W * (budget / s)
    d = K.shape[1]
    M = np.zeros((d, d))
    with np.errstate(all="ignore"):
        M = (K * W[:, None]).T @ K       # Σ w_f k_f k_fᵀ
    return M


def read_per_fact(K, M):
    """Retrieval strength k_fᵀ M k_f for every fact."""
    with np.errstate(all="ignore"):
        return np.einsum("fd,de,fe->f", K, M, K)


def write_pairs(K, pairs, Wp, budget=100.0):
    """R = Σ W_ij k_i k_jᵀ (symmetrized), Σ|W| = budget."""
    Wp = np.maximum(np.asarray(Wp, float), 0.0)
    s = Wp.sum()
    if s <= 0:
        Wp = np.ones_like(Wp)
        s = Wp.sum()
    Wp = Wp * (budget / s)
    d = K.shape[1]
    R = np.zeros((d, d))
    with np.errstate(all="ignore"):
        for w, (i, j) in zip(Wp, pairs):
            if w > 0:
                R += w * np.outer(K[i], K[j])
    return R


def read_pairs(K, R, pairs):
    with np.errstate(all="ignore"):
        return np.array([K[i] @ R @ K[j] for (i, j) in pairs])


# ---------------------------------------------------------------- weight policies
def weights_per_fact(stream, policy):
    X, V, y = stream.X, stream.value, stream.y
    count = X.sum(0)
    if policy == "uniform":            # natural repetition: weight ∝ appearances
        return count
    if policy == "surprise":           # ATLAS-proxy: rare/new imprints harder
        return np.where(count > 0, 1.0, 0.0)   # each fact once, regardless of count
    if policy == "value_z":            # untrained noisy tags, sufficient statistic
        vsum = V.sum(0)
        with np.errstate(all="ignore"):
            return np.maximum(np.divide(vsum, np.sqrt(count),
                                        out=np.zeros_like(vsum), where=count > 0), 0)
    if policy == "trained_item":       # OUTCOME-trained (never sees labels/probes)
        return np.maximum(_logreg(X, y), 0.0)
    if policy == "oracle":
        return stream.is_structural.astype(float)
    raise ValueError(policy)


def weights_pairs(stream, pairs, M_pair, policy):
    if policy == "cooc":
        return M_pair.sum(0)
    if policy == "trained_rel":        # OUTCOME-trained pair values
        return np.maximum(_logreg(M_pair, stream.y), 0.0)
    if policy == "oracle_rel":
        rel = set(map(tuple, stream.relations))
        return np.array([1.0 if (i, j) in rel else 0.0 for (i, j) in pairs])
    raise ValueError(policy)


# ---------------------------------------------------------------- experiment
def run_per_fact(cfg, d, seeds, policies):
    ap = {p: [] for p in policies}
    for s in range(seeds):
        stream = generate(cfg, seed=s)
        rng = np.random.default_rng(50_000 + s)
        K = make_keys(rng, cfg.n_facts, d)
        for p in policies:
            W = weights_per_fact(stream, p)
            M = write_per_fact(K, W)
            strengths = read_per_fact(K, M)
            ap[p].append(average_precision(strengths, stream.is_structural))
    return {p: np.array(v) for p, v in ap.items()}


def run_relational(cfg, d, seeds, policies):
    ap = {p: [] for p in policies}
    for s in range(seeds):
        stream = generate(cfg, seed=s)
        rng = np.random.default_rng(60_000 + s)
        K = make_keys(rng, cfg.n_facts, d)
        pairs, M_pair = candidate_pairs(stream)
        rel = set(map(tuple, stream.relations))
        positive = np.array([(i, j) in rel for (i, j) in pairs])
        if positive.sum() == 0:
            continue
        for p in policies:
            Wp = weights_pairs(stream, pairs, M_pair, p)
            R = write_pairs(K, pairs, Wp)
            strengths = read_pairs(K, R, pairs)
            ap[p].append(average_precision(strengths, positive))
    return {p: np.array(v) for p, v in ap.items()}


def fmt(a):
    return f"{a.mean():.3f}±{a.std():.3f}"


def main():
    SEEDS = 20
    cfg = BenchConfig(outcome="relational", n_recipes=4, n_episodes=300)
    chance = cfg.n_structural / cfg.n_facts

    print("=" * 78)
    print("Exp4 — end-to-end: outcome-trained value → interference memory → probes")
    print(f"seeds={SEEDS} | facts={cfg.n_facts} | chance AP ≈ {chance:.3f}")
    print("=" * 78)

    # Q1+Q2: per-fact memory, capacity sweep
    POL = ["uniform", "surprise", "value_z", "trained_item", "oracle"]
    print("\n[Q1/Q2: PER-FACT associative memory — AP(structural) vs capacity d]")
    print(f"{'d':>5} " + " ".join(f"{p:>14}" for p in POL) + f"{'trained−uniform':>18}")
    for d in (16, 32, 64, 128, 256):
        res = run_per_fact(cfg, d, SEEDS, POL)
        pd = paired_diff(res["trained_item"], res["uniform"])
        print(f"{d:>5} " + " ".join(f"{fmt(res[p]):>14}" for p in POL)
              + f"  {pd['mean']:+.3f} (t={pd['t']:.1f}{'*' if pd['sig'] else ''})")

    # Canary: at d'=0, value methods must NOT beat uniform
    print("\n[CANARY: value_dprime=0 — value_z must NOT beat uniform]")
    cfg0 = BenchConfig(outcome="relational", n_recipes=4, n_episodes=300,
                       value_dprime=0.0)
    res0 = run_per_fact(cfg0, 64, SEEDS, ["uniform", "value_z", "trained_item"])
    c1 = paired_diff(res0["value_z"], res0["uniform"])
    print(f"  value_z − uniform @d'=0: {c1['mean']:+.3f} (t={c1['t']:.1f}) "
          f"{'OK (≈0/neg)' if c1['mean'] < 0.05 else 'LEAK?'}")
    c2 = paired_diff(res0["trained_item"], res0["uniform"])
    print(f"  trained − uniform @d'=0: {c2['mean']:+.3f} (t={c2['t']:.1f}) "
          f"(trained may retain outcome signal — outcomes still carry structure)")

    # Q3: relational binding memory
    RPOL = ["cooc", "trained_rel", "oracle_rel"]
    print("\n[Q3: RELATIONAL binding memory — AP(true recipe pairs) vs capacity d]")
    print(f"{'d':>5} " + " ".join(f"{p:>14}" for p in RPOL) + f"{'trained−cooc':>16}")
    for d in (16, 32, 64, 128):
        res = run_relational(cfg, d, SEEDS, RPOL)
        pd = paired_diff(res["trained_rel"], res["cooc"])
        print(f"{d:>5} " + " ".join(f"{fmt(res[p]):>14}" for p in RPOL)
              + f"  {pd['mean']:+.3f} (t={pd['t']:.1f}{'*' if pd['sig'] else ''})")

    # Scale sweep: advantage vs data horizon at fixed capacity
    print("\n[SCALE: trained−uniform advantage vs n_episodes @ d=64]")
    for ne in (100, 200, 400, 800):
        cfgn = BenchConfig(outcome="relational", n_recipes=4, n_episodes=ne)
        res = run_per_fact(cfgn, 64, SEEDS, ["uniform", "trained_item"])
        pd = paired_diff(res["trained_item"], res["uniform"])
        print(f"  n_ep={ne:>4}: {pd['mean']:+.3f} (t={pd['t']:.1f}"
              f"{'*' if pd['sig'] else ''})   [#facts={cfgn.n_facts}]")

    print("\n[READ] trained_item/trained_rel see ONLY (presence, outcome). The AP "
          "probes (ground-truth labels) are the held-out exam. Interference is "
          "physical (random-key crosstalk in R^d). If trained weighting wins and "
          "the win grows as d shrinks, allocation-under-scarcity is doing the work.")


if __name__ == "__main__":
    main()
