#!/usr/bin/env python3
"""Deterministic planning simulation for the one-parent v2 primary D rule.

This is a CPU-only design aid.  It does not read scientific artifacts and is
not a confirmation reducer.  The joint primary planning rule is:

  lower endpoint of a two-sided 95% Student-t interval > 0
  AND observed mean(D) >= 0.05.

The simulation evaluates fixed N=32 at the design alternative mean(D)=0.070
under several standardized root-distribution shapes.  It is a named-shape
sensitivity, not a claim that mean and SD define a power envelope.  Later
fixed-sequence rungs are precision-gated.
"""
from __future__ import annotations

import argparse
import json

import numpy as np


T975_DF31 = 2.039513446396408
GAUC_WITH_CACHED_ENTRY_COMPARISON_BOUND = 5.0 / 6.0
D_MIN = -5.0 / 3.0
D_MAX = 5.0 / 3.0
assert D_MAX == 2.0 * GAUC_WITH_CACHED_ENTRY_COMPARISON_BOUND
assert D_MIN == -D_MAX


def draws(rng: np.random.Generator, family: str, shape: tuple[int, int]) -> np.ndarray:
    if family == "normal":
        return rng.normal(size=shape)
    if family == "t5":
        return rng.standard_t(5, size=shape) / np.sqrt(5.0 / 3.0)
    if family == "beta2_5":
        return (rng.beta(2, 5, size=shape) - 2.0 / 7.0) / np.sqrt(10.0 / (49.0 * 8.0))
    if family == "beta5_2":
        return (rng.beta(5, 2, size=shape) - 5.0 / 7.0) / np.sqrt(10.0 / (49.0 * 8.0))
    if family == "two_point_p20":
        # Mean zero and variance one: P(2)=.2, P(-.5)=.8.
        return np.where(rng.random(size=shape) < 0.2, 2.0, -0.5)
    if family == "rare_negative_p0136":
        # An adverse standardized two-point mixture. Rare negative roots can
        # defeat a small-sample t lower bound despite the same mean and SD.
        p = 0.0136
        rare = -np.sqrt((1.0 - p) / p)
        common = np.sqrt(p / (1.0 - p))
        return np.where(rng.random(size=shape) < p, rare, common)
    raise ValueError(f"unknown family: {family}")


def simulate(*, seed: int, repetitions: int, n: int, mean: float, sd: float, family: str) -> dict:
    if n != 32:
        raise ValueError("this sealed planning version supports fixed N=32 only")
    rng = np.random.default_rng(seed)
    z = draws(rng, family, (repetitions, n))
    # D is a difference of two differences of gain-AUC values and is bounded
    # by construction.  Clipping affects only extreme heavy-tail sensitivity
    # draws; the empirical mean/SD below disclose the resulting distribution.
    x = np.clip(mean + sd * z, D_MIN, D_MAX)
    sample_mean = x.mean(axis=1)
    sample_sd = x.std(axis=1, ddof=1)
    lower = sample_mean - T975_DF31 * sample_sd / np.sqrt(n)
    passed = (lower > 0.0) & (sample_mean >= 0.05)
    return {
        "family": family,
        "n": n,
        "requested_preclip_mean": mean,
        "requested_preclip_sd": sd,
        "repetitions": repetitions,
        "pass_probability": float(passed.mean()),
        "ci_positive_probability": float((lower > 0.0).mean()),
        "estimate_ge_0_05_probability": float((sample_mean >= 0.05).mean()),
        "empirical_draw_mean": float(x.mean()),
        "empirical_draw_sd": float(x.std()),
        "minimum_draw": float(x.min()),
        "maximum_draw": float(x.max()),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=20260907)
    ap.add_argument("--repetitions", type=int, default=300_000)
    args = ap.parse_args()
    families = [
        "normal",
        "t5",
        "beta2_5",
        "beta5_2",
        "two_point_p20",
        "rare_negative_p0136",
    ]
    rows = []
    for sd in (0.075, 0.10, 0.125):
        for index, family in enumerate(families):
            rows.append(
                simulate(
                    seed=args.seed + 100 * int(sd * 1000) + index,
                    repetitions=args.repetitions,
                    n=32,
                    mean=0.070,
                    sd=sd,
                    family=family,
                )
            )
    for index, family in enumerate(families):
        rows.append(
            simulate(
                seed=args.seed + 90_000 + index,
                repetitions=args.repetitions,
                n=32,
                mean=0.0,
                sd=0.10,
                family=family,
            )
        )
    print(
        json.dumps(
            {
                "schema_version": 1,
                "seed": args.seed,
                "joint_rule": "two_sided_95pct_t_lower_gt_0 AND estimate_ge_0.05",
                "t_0.975_df31": T975_DF31,
                "feasible_D_range": [D_MIN, D_MAX],
                "primary_only": True,
                "rows": rows,
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
