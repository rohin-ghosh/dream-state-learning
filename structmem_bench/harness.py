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
    """random-sampler AND label-permutation canaries must both sit at chance."""
    struct_ap_random, perm_ap = [], []
    chance = None
    for s in range(seeds):
        rng = np.random.default_rng(30_000 + s)
        stream = generate(cfg, seed=s)
        chance = float(stream.is_structural.mean())
        r = mem.score_random(stream, rng)
        struct_ap_random.append(met.average_precision(r, stream.is_structural))
        # permutation canary on a REAL method's scores (frequency): permuting labels
        # must destroy any signal
        fr = mem.score_frequency(stream, rng)
        perm_ap.append(st.permutation_canary_ap(fr, stream.is_structural, rng, n_perm=30))
    rand = float(np.nanmean(struct_ap_random))
    perm = float(np.nanmean(perm_ap))
    return {
        "chance_base_rate": chance,
        "random_sampler_ap": rand,
        "permutation_ap": perm,
        "random_ok": st.canary_ok(rand, chance),
        "permutation_ok": st.canary_ok(perm, chance),
    }


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
