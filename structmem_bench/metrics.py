"""Metrics — all scored against ground-truth labels, programmatically (no LLM judge).

Primary metric is budget-free Average Precision (AP): does the method RANK the
target class above the rest, independent of any budget cutoff. Budget-dependent
retention is also provided for concreteness (with the caveat that it mixes ranking
quality with fill policy — see exp1-corrected lessons).
"""

from __future__ import annotations

import numpy as np


def average_precision(scores: np.ndarray, positive: np.ndarray) -> float:
    """AP treating `positive` (bool mask) as the relevant class."""
    assert scores.shape == positive.shape
    n_pos = int(positive.sum())
    if n_pos == 0 or len(scores) == 0:
        return float("nan")
    order = np.argsort(-scores, kind="stable")
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
    """Fraction of the target class that lands in the top-`budget` by score."""
    n_target = int(target.sum())
    if n_target == 0:
        return float("nan")
    if budget >= len(scores):
        return 1.0
    keep = set(np.argsort(-scores, kind="stable")[:budget].tolist())
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
