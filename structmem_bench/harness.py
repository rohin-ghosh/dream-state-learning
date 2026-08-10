"""Evaluation harness — runs methods across seeds (and optionally budget/scale
sweeps), aggregates metrics with paired stats, and checks canaries.
"""

from __future__ import annotations

from dataclasses import replace

import numpy as np

from .config import BenchConfig
from .tasks import generate
from . import memory as mem
from . import metrics as met
from . import stats as st


def run_per_fact(cfg: BenchConfig, methods=None, seeds=20, budget=25) -> dict:
    """Run per-fact methods across seeds. Returns {method: {metric: (mean,std,vals)}}."""
    methods = methods or list(mem.PER_FACT)
    raw = {m: {} for m in methods}
    for s in range(seeds):
        rng = np.random.default_rng(10_000 + s)
        stream = generate(cfg, seed=s)
        for m in methods:
            scores = mem.PER_FACT[m](stream, rng)
            mm = met.per_fact_metrics(scores, stream, budget)
            for k, v in mm.items():
                raw[m].setdefault(k, []).append(v)
    agg = {m: {k: (float(np.nanmean(v)), float(np.nanstd(v)), v)
               for k, v in d.items()} for m, d in raw.items()}
    return agg


def run_relational(cfg: BenchConfig, seeds=20) -> dict:
    methods = list(mem.RELATIONAL)
    raw = {m: {} for m in methods}
    for s in range(seeds):
        rng = np.random.default_rng(20_000 + s)
        stream = generate(cfg, seed=s)
        for m in methods:
            pairs, scores = mem.RELATIONAL[m](stream, rng)
            rm = met.relational_metrics(pairs, scores, stream.relations)
            for k, v in rm.items():
                raw[m].setdefault(k, []).append(v)
    agg = {m: {k: (float(np.nanmean(v)), float(np.nanstd(v)), v)
               for k, v in d.items()} for m, d in raw.items()}
    return agg


def check_canaries(cfg: BenchConfig, seeds=20) -> dict:
    """Rigor gate. THREE controls, each of which MUST sit at chance:
      * random-sampler   — catches a broken RNG / metric offset
      * constant-scorer  — catches POSITION LEAKS through tie-breaking (the critical
                           bug): a zero-information all-equal score must NOT beat chance
      * label-permutation on the LEAKIEST real method — catches metric inflation
    If any is materially above chance, the eval is leaking and results are void."""
    chance = None
    rand_ap, const_ap, perm_ap = [], [], []
    for s in range(seeds):
        rng = np.random.default_rng(30_000 + s)
        stream = generate(cfg, seed=s)
        chance = float(stream.is_structural.mean())
        F = stream.cfg.n_facts
        rand_ap.append(met.average_precision(mem.score_random(stream, rng),
                                             stream.is_structural))
        const_ap.append(met.average_precision(np.zeros(F), stream.is_structural))
        # run the permutation canary on the method most prone to ties (surprise)
        surp = mem.score_surprise(stream, rng)
        perm_ap.append(st.permutation_canary_ap(surp, stream.is_structural, rng, 30))
    rand, const, perm = map(lambda v: float(np.nanmean(v)), (rand_ap, const_ap, perm_ap))
    return {
        "chance_base_rate": chance,
        "random_sampler_ap": rand,
        "constant_scorer_ap": const,
        "permutation_ap": perm,
        "random_ok": st.canary_ok(rand, chance),
        "constant_ok": st.canary_ok(const, chance),
        "permutation_ok": st.canary_ok(perm, chance),
    }


def worst_positional_ap(cfg: BenchConfig, seeds=20) -> float:
    """Directly probe the position leak: the AP a ZERO-INFORMATION index-ranking method
    achieves. MUST be ~chance after the layout-permutation fix (was 1.0 when broken)."""
    aps = []
    for s in range(seeds):
        stream = generate(cfg, seed=s)
        idx_score = -np.arange(stream.cfg.n_facts, dtype=float)  # prefer low indices
        aps.append(met.average_precision(idx_score, stream.is_structural))
    return float(np.nanmean(aps))


def paired_vs(agg: dict, metric: str, a: str, b: str) -> dict:
    va = np.array(agg[a][metric][2], float)
    vb = np.array(agg[b][metric][2], float)
    return st.paired_diff(va, vb)


def sanity_frequency_matched(cfg: BenchConfig, seeds=20) -> float:
    """dP(frequency) on the MATCHED-MARGINAL comparison: structural-frequent (SF) vs
    detail-recurring (DR). Both have identical marginal p_present, so frequency CANNOT
    separate them -> MUST be ~0. Guards the exp0/exp2-v1 bug where structure was
    accidentally more frequent. (Global structural-vs-detail is intentionally NOT ~0
    here: frequency legitimately keeps SF and drops one-shot detail — its FAILURE is
    on the hard cases, tested separately.)"""
    from .tasks import SF, DR
    vals = []
    for s in range(seeds):
        stream = generate(cfg, seed=s)
        sc = mem.score_frequency(stream, np.random.default_rng(s))
        mask_sf = stream.fact_type == SF
        mask_dr = stream.fact_type == DR
        both = mask_sf | mask_dr
        vals.append(met.dprime(sc[both], mask_sf[both]))
    return float(np.nanmean(vals))


def frequency_hard_case_failure(cfg: BenchConfig, seeds=20, budget=25) -> dict:
    """Frequency should FAIL the adversarial cases: drop rare-critical structure and
    keep recurring-useless detail. Returns the two designed-failure numbers."""
    rare, dr = [], []
    for s in range(seeds):
        stream = generate(cfg, seed=s)
        sc = mem.score_frequency(stream, np.random.default_rng(s))
        m = met.per_fact_metrics(sc, stream, budget)
        rare.append(m["rare_retention@budget"])
        dr.append(m["recurring_detail_kept@budget"])
    return {"rare_retention": float(np.nanmean(rare)),
            "recurring_detail_kept": float(np.nanmean(dr))}
