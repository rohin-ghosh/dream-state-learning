"""
Experiment 3 — Relational value: per-PAIR beats per-ITEM when structure is relational.

Exp 2.5 finding: under nonlinear (conjunctive) outcomes, per-ITEM scalar value
collapses (dP ~1.8) because no single fact is valuable alone — value lives in the
RELATIONSHIP. This tests the fix: define/learn value on PAIRS (relations) and
attribute per-pair. Hypothesis: relational value recovers the causal structure
(the recipe pairs) that per-item value could not.

Same generator as exp2.5: success = ANY structural recipe-pair both present.
Confounded details (sticky partner per structural fact) + random details.
Frequency uninformative (equal marginals). Value model never sees the label.

Signals over the C(F,2) candidate pairs:
  - relational  : L2 logistic regression on PAIR-presence (x_ij = fact_i AND fact_j)
                  -> per-pair coefficient = learned relational value.
  - item_lifted : per-ITEM logreg value, lifted to a pair by product v_i * v_j
                  (best per-item can do). Tests whether item value reconstructs
                  relations.
Metric: dP( true recipe pairs  vs  all other pairs ), AP. The hard distractors are
STRUCT-CONFOUND pairs (co-occur, correlate with success) and STRUCT-STRUCT
non-recipe pairs.

numpy only, CPU.
"""

from __future__ import annotations

import numpy as np
from itertools import combinations

N_STRUCT, N_CONF, N_RAND = 12, 12, 16
N_FACTS = N_STRUCT + N_CONF + N_RAND
STRUCT = np.arange(0, N_STRUCT)
CONF = np.arange(N_STRUCT, N_STRUCT + N_CONF)
PAIRS = list(combinations(range(N_FACTS), 2))
PAIR_IDX = {p: i for i, p in enumerate(PAIRS)}


def gen(rng, n_ep, p=0.4, a=0.7, n_recipes=8):
    recipes = set()
    while len(recipes) < n_recipes:
        i, j = sorted(rng.choice(N_STRUCT, size=2, replace=False))
        recipes.add((int(i), int(j)))
    recipes = list(recipes)
    b = (p - p * a) / (1 - p)
    X = np.zeros((n_ep, N_FACTS))
    for e in range(n_ep):
        s = (rng.random(N_STRUCT) < p).astype(float)
        X[e, STRUCT] = s
        c = np.where(s == 1, rng.random(N_STRUCT) < a, rng.random(N_STRUCT) < b)
        X[e, CONF] = c.astype(float)
        X[e, N_STRUCT + N_CONF:] = (rng.random(N_RAND) < p).astype(float)
    sat = np.zeros(n_ep)
    for (i, j) in recipes:
        sat += X[:, i] * X[:, j]
    logit = np.clip(1.7 * (sat - 1.0), -30, 30)
    y = (rng.random(n_ep) < 1 / (1 + np.exp(-logit))).astype(float)
    return X, y, recipes


def logreg(F, y, l2=1.0, iters=400, lr=0.5):
    n, d = F.shape; w = np.zeros(d); b = 0.0
    for _ in range(iters):
        z = np.clip(F @ w + b, -30, 30)
        g = 1 / (1 + np.exp(-z)) - y
        w -= lr * (F.T @ g / n + l2 * w / n); b -= lr * g.mean()
    return w


def pair_matrix(X):
    n = X.shape[0]
    Fp = np.empty((n, len(PAIRS)))
    for k, (i, j) in enumerate(PAIRS):
        Fp[:, k] = X[:, i] * X[:, j]
    return Fp


def dprime(v, pos_mask):
    s, d = v[pos_mask], v[~pos_mask]
    return (s.mean() - d.mean()) / (np.sqrt(0.5 * (s.var() + d.var())) + 1e-9)


def average_precision(v, pos_mask):
    order = np.argsort(-v); lab = pos_mask[order]
    hits = np.cumsum(lab); prec = hits / (np.arange(len(v)) + 1)
    return (prec * lab).sum() / max(1, lab.sum())


def main():
    SEEDS, N_EP = 20, 3000
    rel = {"dp": [], "ap": []}; itm = {"dp": [], "ap": []}
    with np.errstate(all="ignore"):
        for s in range(SEEDS):
            rng = np.random.default_rng(6000 + s)
            X, y, recipes = gen(rng, N_EP)
            is_recipe = np.zeros(len(PAIRS), bool)
            for (i, j) in recipes:
                is_recipe[PAIR_IDX[(i, j)]] = True
            # relational value: logreg on pair-presence
            Fp = pair_matrix(X)
            v_rel = logreg(Fp, y)
            rel["dp"].append(dprime(v_rel, is_recipe))
            rel["ap"].append(average_precision(v_rel, is_recipe))
            # item value lifted to pairs by product
            v_item = logreg(X, y)
            v_lift = np.array([v_item[i] * v_item[j] for (i, j) in PAIRS])
            itm["dp"].append(dprime(v_lift, is_recipe))
            itm["ap"].append(average_precision(v_lift, is_recipe))

    print(f"Exp3 — relational value | seeds={SEEDS} episodes={N_EP} "
          f"| {N_FACTS} facts, {len(PAIRS)} candidate pairs, 8 true recipe pairs")
    print("metric = separate TRUE RECIPE PAIRS from all other pairs "
          "(hard distractors: struct-confound & struct-struct non-recipe)\n")
    print(f"{'signal':<14} {'dP(recipe vs rest)':>20} {'AP':>10}")
    for name, d in (("relational", rel), ("item_lifted", itm)):
        print(f"{name:<14} {np.mean(d['dp']):>13.2f}±{np.std(d['dp']):<5.2f} "
              f"{np.mean(d['ap']):>7.3f}±{np.std(d['ap']):<5.3f}")
    print(f"\nchance AP ≈ {8/len(PAIRS):.3f} (8 recipe pairs / {len(PAIRS)})")
    rd, idd = np.mean(rel["dp"]), np.mean(itm["dp"])
    print(f"\nRead: if relational dP >> item_lifted dP, then learning value on "
          f"RELATIONS recovers the causal structure that per-item value cannot "
          f"(exp2.5's collapse). relational={rd:.2f} vs item_lifted={idd:.2f}. "
          f"This decides what the value head predicts before ATLAS: per-relation, "
          f"not per-item.")


if __name__ == "__main__":
    main()
