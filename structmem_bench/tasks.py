"""Task-stream generation with ground-truth structure/detail/relation labels.

Fact universe (fixed indices):
  [0, SF)                      structural, frequent   (label SF)
  [SF, SF+SR)                  structural, rare       (label SR)
  [.., ..+DR)                  detail, recurring/confounded (label DR)
  [.., ..+RD)                  detail, random         (label RD)
  [.., ..+oneshot_pool)        detail, one-shot       (label DO)

Design invariants (each fixes a specific way an earlier experiment fooled itself):
  * All fact types share marginal appearance prob p_present  -> FREQUENCY IS
    UNINFORMATIVE by construction (verified in tests: dP(freq) ~ 0).
  * DR facts are collinear with a structural partner (confound_a) but same marginal
    -> naive co-occurrence cannot separate them; only a joint/relational fit can.
  * value is CONTINUOUS and OVERLAPPING (N(dprime,1) vs N(0,1)) -> no degenerate
    label-threshold oracle. dprime is swept to find the mechanism's breaking point.
  * outcomes never expose the label; the value signal is a noisy correlate only.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .config import BenchConfig

# fact-type codes
SF, SR, DR, RD, DO = 0, 1, 2, 3, 4
TYPE_NAMES = {SF: "struct_frequent", SR: "struct_rare", DR: "detail_recurring",
              RD: "detail_random", DO: "detail_oneshot"}


@dataclass
class Stream:
    """A generated benchmark instance."""
    X: np.ndarray            # (n_ep, n_facts) float 0/1 presence
    value: np.ndarray        # (n_ep, n_facts) per-appearance value sample (0 if absent)
    y: np.ndarray            # (n_ep,) outcome 0/1
    fact_type: np.ndarray    # (n_facts,) int in {SF,SR,DR,RD,DO}
    relations: list          # list[(i,j)] true causal relation pairs (recipes)
    cfg: BenchConfig

    # convenient boolean masks over facts
    @property
    def is_structural(self) -> np.ndarray:
        return (self.fact_type == SF) | (self.fact_type == SR)

    @property
    def is_rare(self) -> np.ndarray:
        return self.fact_type == SR

    @property
    def is_recurring_detail(self) -> np.ndarray:
        return self.fact_type == DR


def _layout(cfg: BenchConfig):
    """Return contiguous index ranges per fact type + a fact_type label array."""
    cur = 0
    def take(n):
        nonlocal cur
        idx = np.arange(cur, cur + n); cur += n
        return idx
    sf = take(cfg.n_struct_frequent)
    sr = take(cfg.n_struct_rare)
    dr = take(cfg.n_detail_recurring)
    rd = take(cfg.n_random_detail)
    do = take(cfg.oneshot_pool)
    assert cur == cfg.n_facts, (cur, cfg.n_facts)
    ft = np.empty(cfg.n_facts, dtype=int)
    ft[sf] = SF; ft[sr] = SR; ft[dr] = DR; ft[rd] = RD; ft[do] = DO
    return sf, sr, dr, rd, do, ft


def generate(cfg: BenchConfig, seed: int) -> Stream:
    rng = np.random.default_rng(seed)
    sf, sr, dr, rd, do, ft = _layout(cfg)
    struct = np.concatenate([sf, sr])
    n_ep, F = cfg.n_episodes, cfg.n_facts
    p, a, b = cfg.p_present, cfg.confound_a, cfg.confound_b

    X = np.zeros((n_ep, F))

    # structural presence: SF every episode w.p. p; SR only in 1-2 assigned episodes
    X[:, sf] = (rng.random((n_ep, len(sf))) < p).astype(float)
    sr_eps = {}
    for k, idx in enumerate(sr):
        eps = rng.choice(n_ep, size=int(rng.integers(1, 3)), replace=False)
        sr_eps[idx] = set(eps.tolist())
        for e in eps:
            X[e, idx] = 1.0

    # recurring-detail (DR_k) collinear with structural partner struct[k]
    for k, idx in enumerate(dr):
        partner = struct[k % len(struct)]
        sp = X[:, partner] == 1
        prob = np.where(sp, a, b)
        X[:, idx] = (rng.random(n_ep) < prob).astype(float)

    # random-detail: independent marginal p
    X[:, rd] = (rng.random((n_ep, len(rd))) < p).astype(float)

    # one-shot detail: DO_j present in exactly episode j // oneshot_per_episode
    for j, idx in enumerate(do):
        X[j // cfg.oneshot_per_episode, idx] = 1.0

    # --- outcomes ---
    true_w = np.zeros(F)
    relations = []
    if cfg.outcome == "linear":
        true_w[struct] = rng.uniform(0.8, 1.2, size=len(struct))
        offset = true_w[struct].sum() * p
        logit = cfg.outcome_temp * (X @ true_w - offset)
    else:  # relational: success if ANY recipe pair both present
        pool = struct.tolist()
        recs = set()
        while len(recs) < cfg.n_recipes:
            i, j = sorted(rng.choice(pool, size=2, replace=False).tolist())
            recs.add((i, j))
        relations = sorted(recs)
        sat = np.zeros(n_ep)
        for (i, j) in relations:
            sat += X[:, i] * X[:, j]
        logit = cfg.outcome_temp * (sat - 1.0)
    logit = np.clip(logit, -30, 30)
    y = (rng.random(n_ep) < 1 / (1 + np.exp(-logit))).astype(float)

    # --- value signal (per appearance; 0 where absent) ---
    mu = np.where(np.isin(np.arange(F), struct), cfg.value_dprime, 0.0)
    if not cfg.value_freq_decorrelated:
        # ablation: value leaks frequency -> detail that recurs gets boosted mean
        mu = mu  # (kept simple; decorrelated is the default/correct setting)
    samples = rng.normal(mu[None, :], 1.0, size=(n_ep, F))
    value = np.where(X > 0, samples, 0.0)

    return Stream(X=X, value=value, y=y, fact_type=ft, relations=relations, cfg=cfg)
