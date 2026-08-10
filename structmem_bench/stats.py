"""Statistical rigor layer — the thing that makes the benchmark trustworthy.

Implements the three guards learned across exp0/exp1-corrected:
  * noise floor        — spread of a metric across seeds (min detectable effect)
  * canaries           — controls that MUST collapse to chance; if they don't, the
                         eval is leaking the label (a real failure, unlike a random
                         sampler that structurally cannot fail)
  * paired comparison  — per-seed differences between two methods (valid because
                         every method sees the identical stream per seed)
"""

from __future__ import annotations

import numpy as np


def paired_diff(a: np.ndarray, b: np.ndarray) -> dict:
    """Paired per-seed difference a - b. Returns mean, se, t, and significance."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = a - b
    d = d[np.isfinite(d)]
    n = len(d)
    if n < 2:
        return {"mean": float(d.mean()) if n else float("nan"),
                "se": float("nan"), "t": float("nan"), "n": n, "sig": False}
    mean = float(d.mean())
    se = float(d.std(ddof=1) / np.sqrt(n))
    if se == 0.0:
        # identical (or constant-offset) inputs: an exactly-zero mean is NO effect;
        # a nonzero constant offset is a real (degenerate) effect.
        t = 0.0 if mean == 0.0 else np.inf
    else:
        t = mean / se
    return {"mean": mean, "se": se, "t": float(t),
            "n": n, "sig": bool(np.isfinite(t) and abs(t) > 3.0) or
                             (not np.isfinite(t) and mean != 0.0)}


def noise_floor(metric_by_seed: np.ndarray) -> float:
    """Std across seeds of a metric = minimum detectable effect proxy."""
    v = np.asarray(metric_by_seed, float)
    v = v[np.isfinite(v)]
    return float(v.std(ddof=1)) if len(v) > 1 else float("nan")


def canary_ok(canary_ap: float, chance: float, tol: float = 0.05) -> bool:
    """A canary passes iff its AP is within `tol` of chance (base rate). If it sits
    materially above chance, the eval is leaking the label."""
    if not np.isfinite(canary_ap):
        return False
    return abs(canary_ap - chance) <= tol


def permutation_canary_ap(scores: np.ndarray, positive: np.ndarray, rng,
                          n_perm: int = 50) -> float:
    """Mean AP when the positive labels are permuted — must ~= chance (base rate).
    A stronger canary than a random sampler: it directly tests the scoring path for
    label leakage."""
    from .metrics import average_precision
    aps = []
    for _ in range(n_perm):
        perm = rng.permutation(positive)
        aps.append(average_precision(scores, perm))
    return float(np.nanmean(aps))
