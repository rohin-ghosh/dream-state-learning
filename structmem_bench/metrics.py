"""Metrics — all scored against ground-truth labels, programmatically (no LLM judge).

Primary metric is budget-free Average Precision (AP): does the method RANK the
target class above the rest, independent of any budget cutoff. Budget-dependent
retention is also provided for concreteness (with the caveat that it mixes ranking
quality with fill policy — see exp1-corrected lessons).
"""

from __future__ import annotations

import numpy as np

# Fixed tie-break seed. Ranking metrics MUST break score ties with an order that is
# uncorrelated with fact index/type — otherwise contiguous type layouts leak the
# label through stable-sort tie-breaking (red-team CRITICAL). A fixed random tie
# order is deterministic (reproducible) AND unbiased w.r.t. type.
_TIE_SEED = 20240817


def _order_desc(scores: np.ndarray) -> np.ndarray:
    """Indices sorting `scores` descending, ties broken by a fixed RANDOM order
    (not by index). Deterministic given _TIE_SEED."""
    scores = np.asarray(scores, float)
    tie = np.random.default_rng(_TIE_SEED).random(len(scores))
    # lexsort: last key is primary -> sort by -scores (desc), break ties by `tie`.
    return np.lexsort((tie, -scores))


def average_precision(scores: np.ndarray, positive: np.ndarray) -> float:
    """AP treating `positive` (bool mask) as the relevant class. Tie-safe."""
    assert scores.shape == positive.shape
    n_pos = int(positive.sum())
    if n_pos == 0 or len(scores) == 0:
        return float("nan")
    order = _order_desc(scores)
    lab = positive[order]
    hits = np.cumsum(lab)
    prec = hits / (np.arange(len(scores)) + 1)
    return float((prec * lab).sum() / n_pos)


def dprime(scores: np.ndarray, positive: np.ndarray) -> float:
    p, n = scores[positive], scores[~positive]
    if len(p) == 0 or len(n) == 0:
        return float("nan")
    pooled = np.sqrt(0.5 * (p.var() + n.var())) + 1e-9
    return float((p.mean() - n.mean()) / pooled)


def retention_at_budget(scores: np.ndarray, target: np.ndarray, budget: int) -> float:
    """Fraction of the target class that lands in the top-`budget` by score. Tie-safe."""
    n_target = int(target.sum())
    if n_target == 0:
        return float("nan")
    if budget >= len(scores):
        return 1.0
    keep = set(_order_desc(scores)[:budget].tolist())
    got = sum(1 for i in np.where(target)[0] if i in keep)
    return got / n_target


def per_fact_metrics(scores: np.ndarray, stream, budget: int) -> dict:
    struct = stream.is_structural
    detail = ~struct
    rare = stream.is_rare
    dr = stream.is_recurring_detail
    return {
        "ap_structural": average_precision(scores, struct),
        "dp_structural": dprime(scores, struct),
        "struct_retention@budget": retention_at_budget(scores, struct, budget),
        "rare_retention@budget": retention_at_budget(scores, rare, budget),
        "detail_retention@budget": retention_at_budget(scores, detail, budget),
        "recurring_detail_kept@budget": retention_at_budget(scores, dr, budget),
        "diagonal@budget": (retention_at_budget(scores, struct, budget)
                            - retention_at_budget(scores, detail, budget)),
    }


# ---------------- paradigm-ported metrics (benchmark v2) ----------------

def retention_by_age(scores: np.ndarray, target: np.ndarray, last_seen: np.ndarray,
                     n_episodes: int, budget: int, n_buckets: int = 4) -> dict:
    """FORGETTING CURVE (Ebbinghaus port): retention@budget of `target` facts,
    stratified by memory AGE = episodes since last appearance. Returns
    {bucket_label: retention}, oldest first. Buckets are age quantiles over the
    target class so each has mass."""
    tgt = np.where(target)[0]
    if len(tgt) == 0:
        return {}
    age = n_episodes - 1 - last_seen[tgt]
    keep = set(_order_desc(scores)[:budget].tolist()) if budget < len(scores) \
        else set(range(len(scores)))
    # FIXED buckets as fractions of the horizon, so results aggregate across seeds
    fracs = np.linspace(0, 1, n_buckets + 1)
    edges = (fracs * n_episodes).astype(int)
    out = {}
    for b in range(n_buckets):
        lo, hi = edges[b], edges[b + 1]
        mask = (age >= lo) & (age <= hi if b == n_buckets - 1 else age < hi)
        facts = tgt[mask]
        if len(facts) == 0:
            continue
        got = sum(1 for f in facts if f in keep)
        out[f"age {int(fracs[b]*100)}-{int(fracs[b+1]*100)}%"] = got / len(facts)
    return out


def retention_by_importance(scores: np.ndarray, importance: np.ndarray,
                            budget: int) -> dict:
    """IMPORTANCE-STRATIFIED retention (open axis): retention@budget grouped by
    ground-truth importance level (e.g. recipe-degree). importance: int per fact,
    -1 = not applicable (detail). Returns {level: retention}."""
    keep = set(_order_desc(scores)[:budget].tolist()) if budget < len(scores) \
        else set(range(len(scores)))
    out = {}
    for lvl in sorted(set(importance[importance >= 0].tolist())):
        facts = np.where(importance == lvl)[0]
        got = sum(1 for f in facts if f in keep)
        out[f"importance={lvl}"] = got / len(facts)
    return out


def gist_verbatim_paired(scores: np.ndarray, stream, budget: int,
                         rng=None, n_probes: int = 200) -> dict:
    """GIST/VERBATIM PAIRED PROBE (fuzzy-trace port — the unported paradigm).
    For each probe: sample an EPISODE, then within that same episode sample one
    GIST fact (structural, present) and one VERBATIM fact (detail, present).
    Score whether each is retained at budget. Pairing within-episode controls for
    exposure: both facts were experienced together; only their TYPE differs.
    Returns P(gist retained), P(verbatim retained), and the DISSOCIATION
    (gist − verbatim) — the FTT signature."""
    rng = rng or np.random.default_rng(0)
    keep = set(_order_desc(scores)[:budget].tolist()) if budget < len(scores) \
        else set(range(len(scores)))
    X = stream.X
    struct = stream.is_structural
    g_hits, v_hits, n = 0, 0, 0
    episodes = rng.choice(X.shape[0], size=min(n_probes, X.shape[0]), replace=False)
    for e in episodes:
        present = np.where(X[e] > 0)[0]
        g_c = present[struct[present]]
        v_c = present[~struct[present]]
        if len(g_c) == 0 or len(v_c) == 0:
            continue
        g = int(rng.choice(g_c)); v = int(rng.choice(v_c))
        g_hits += g in keep
        v_hits += v in keep
        n += 1
    if n == 0:
        return {"gist": float("nan"), "verbatim": float("nan"),
                "dissociation": float("nan"), "n_probes": 0}
    return {"gist": g_hits / n, "verbatim": v_hits / n,
            "dissociation": g_hits / n - v_hits / n, "n_probes": n}


def relational_metrics(pairs, scores: np.ndarray, relations) -> dict:
    """Score how well a per-pair method ranks the TRUE relation pairs."""
    if len(pairs) == 0:
        return {"ap_relational": float("nan"), "dp_relational": float("nan")}
    rel_set = set(map(tuple, relations))
    positive = np.array([(i, j) in rel_set for (i, j) in pairs])
    return {
        "ap_relational": average_precision(scores, positive),
        "dp_relational": dprime(scores, positive),
        "n_candidate_pairs": len(pairs),
        "n_true_relations": int(positive.sum()),
    }
