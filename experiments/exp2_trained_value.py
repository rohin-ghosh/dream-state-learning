"""
Experiment 2 — Can a value function TRAINED ON OUTCOMES clear the bar Exp 1 set?

Exp 1 (corrected): a value signal helps consolidation ONLY if high-discriminability
AND decorrelated from frequency. Rohin's fix: TRAIN the value function on task
outcomes. This tests whether outcome-training produces such a signal, on CPU, in
seconds, BEFORE any ATLAS/GPU work.

DESIGN (v2 — fixes the flaw that frequency separated structure in v1):
  - ALL fact types share the SAME marginal appearance prob (0.4) → frequency is
    UNINFORMATIVE by construction (d'_freq ~ 0). Structure is revealed ONLY through
    its causal effect on outcomes.
  - CONFOUNDED details: a sticky partner per structural fact, positively correlated
    with it but with identical marginal (collinearity, the hard case). A naive
    co-occurrence signal cannot separate these from structure; a trained joint
    model must.
  - RANDOM details: pure distractors.
  - Outcome: success ~ Bernoulli(sigmoid(scale*(sum present structural weight -
    offset))). Details have ZERO causal weight.
  The value model never sees the struct/detail label — only (presence, outcome).

Signals: true_value (oracle ceiling) | frequency (now-uninformative floor) |
naive_cred = P(succ|present)-P(succ|absent) (untrained) | trained = L2 logistic
regression coefficients (TRAINED, disentangles collinearity via the joint fit).

Key metric = d'(structural vs CONFOUNDED detail): the disentangling test. Gate to
proceed to ATLAS: trained d'(struct vs confounded) >= 2.0 AND naive fails it
(shows training — not co-occurrence — is what separates causal value).

numpy only, CPU.
"""

from __future__ import annotations

import numpy as np

N_STRUCT, N_CONF, N_RAND = 15, 15, 20
N_FACTS = N_STRUCT + N_CONF + N_RAND
STRUCT = np.arange(0, N_STRUCT)
CONF = np.arange(N_STRUCT, N_STRUCT + N_CONF)
RAND = np.arange(N_STRUCT + N_CONF, N_FACTS)
IS_STRUCT = np.zeros(N_FACTS, bool); IS_STRUCT[STRUCT] = True
IS_CONF = np.zeros(N_FACTS, bool); IS_CONF[CONF] = True


def gen(rng, n_ep, p=0.4, a=0.7):
    """a = P(confounded detail present | its structural fact present); b derived so
    marginal(conf) = p exactly. a=p -> no correlation; a->1 -> near-perfect
    collinearity (naive credit cannot separate; only a joint fit can)."""
    b = (p - p * a) / (1 - p)
    true_w = np.zeros(N_FACTS, float)
    true_w[STRUCT] = rng.uniform(0.8, 1.2, N_STRUCT)
    X = np.zeros((n_ep, N_FACTS), float)
    for e in range(n_ep):
        s = (rng.random(N_STRUCT) < p).astype(float)
        X[e, STRUCT] = s
        c = np.where(s == 1, rng.random(N_STRUCT) < a, rng.random(N_STRUCT) < b)
        X[e, CONF] = c.astype(float)
        X[e, RAND] = (rng.random(N_RAND) < p).astype(float)
    offset = true_w[STRUCT].sum() * p                    # center logit at 0
    logit = np.clip(1.5 * (X @ true_w - offset), -30, 30)
    y = (rng.random(n_ep) < 1 / (1 + np.exp(-logit))).astype(float)
    return X, y, true_w


def train_logreg(X, y, l2=1.0, iters=500, lr=0.5):
    n, d = X.shape
    w = np.zeros(d); b = 0.0
    for _ in range(iters):
        z = np.clip(X @ w + b, -30, 30)
        g = 1 / (1 + np.exp(-z)) - y
        w -= lr * (X.T @ g / n + l2 * w / n)
        b -= lr * g.mean()
    return w


def naive_credit(X, y):
    out = np.zeros(N_FACTS)
    for f in range(N_FACTS):
        pres = X[:, f] == 1
        if 0 < pres.sum() < len(y):
            out[f] = y[pres].mean() - y[~pres].mean()
    return out


def dprime(v, pos_mask, neg_mask):
    s, d = v[pos_mask], v[neg_mask]
    pooled = np.sqrt(0.5 * (s.var() + d.var())) + 1e-9
    return (s.mean() - d.mean()) / pooled


def average_precision(v):
    order = np.argsort(-v)
    lab = IS_STRUCT[order]
    hits = np.cumsum(lab)
    prec = hits / (np.arange(len(v)) + 1)
    return (prec * lab).sum() / max(1, lab.sum())


def main():
    SEEDS, N_EP = 30, 2000
    sig = ("true_value", "frequency", "naive_cred", "trained")
    M = {s: {"dp_all": [], "dp_conf": [], "dp_rand": [], "ap": [], "fc": []} for s in sig}
    succ = []
    with np.errstate(all="ignore"):
        for s in range(SEEDS):
            rng = np.random.default_rng(3000 + s)
            X, y, true_w = gen(rng, N_EP)
            succ.append(y.mean())
            freq = X.sum(0)
            vals = {"true_value": true_w, "frequency": freq.copy(),
                    "naive_cred": naive_credit(X, y), "trained": train_logreg(X, y)}
            for name, v in vals.items():
                assert np.all(np.isfinite(v)), f"{name} non-finite"
                M[name]["dp_all"].append(dprime(v, IS_STRUCT, ~IS_STRUCT))
                M[name]["dp_conf"].append(dprime(v, IS_STRUCT, IS_CONF))
                M[name]["dp_rand"].append(dprime(v, IS_STRUCT, np.isin(np.arange(N_FACTS), RAND)))
                M[name]["ap"].append(average_precision(v))
                M[name]["fc"].append(np.corrcoef(v, freq)[0, 1])

    print(f"Exp2 — trained value (v2, frequency made uninformative) | seeds={SEEDS} "
          f"episodes={N_EP} | success {np.mean(succ):.2f}")
    print(f"facts: {N_STRUCT} struct | {N_CONF} confounded (collinear) | {N_RAND} random\n")
    print(f"{'signal':<12} {'dP(all)':>9} {'dP(vs conf)':>12} {'dP(vs rand)':>12} "
          f"{'AP':>7} {'corr_freq':>10}")
    for name in sig:
        f = lambda k: np.mean(M[name][k])
        print(f"{name:<12} {f('dp_all'):>9.2f} {f('dp_conf'):>12.2f} "
              f"{f('dp_rand'):>12.2f} {f('ap'):>7.3f} {f('fc'):>10.2f}")

    frq = np.mean(M["frequency"]["dp_all"])
    print(f"\n--- sanity: frequency dP(all) = {frq:.2f} (must be ~0 = uninformative) ---")

    # confound-strength sweep: where does naive break but trained hold?
    print("\n=== confound-strength sweep: dP(structural vs CONFOUNDED detail) ===")
    print("(higher a = stronger collinearity; naive uses marginals, trained uses "
          "the joint fit)")
    print(f"{'a=P(c|s)':>9} {'naive_cred':>12} {'trained':>10} {'advantage':>11}")
    with np.errstate(all="ignore"):
        for a in (0.4, 0.7, 0.9, 0.99):
            na_l, tr_l = [], []
            for s in range(SEEDS):
                rng = np.random.default_rng(4000 + s)
                X, y, _ = gen(rng, N_EP, a=a)
                na_l.append(dprime(naive_credit(X, y), IS_STRUCT, IS_CONF))
                tr_l.append(dprime(train_logreg(X, y), IS_STRUCT, IS_CONF))
            na_m, tr_m = np.mean(na_l), np.mean(tr_l)
            print(f"{a:>9} {na_m:>12.2f} {tr_m:>10.2f} {tr_m - na_m:>11.2f}")
    print("\nRead: a=0.4 is no confound (both fine). As a->1 the confounded detail "
          "becomes a near-copy of its structural fact: naive co-occurrence credit "
          "collapses (cannot separate a copy), while the trained joint fit holds "
          "longer by exploiting the episodes where they differ. The gap = what "
          "TRAINING buys over co-occurrence counting. At a=0.99 (near-perfect "
          "collinearity) even training degrades — an honest limit.")


if __name__ == "__main__":
    main()
