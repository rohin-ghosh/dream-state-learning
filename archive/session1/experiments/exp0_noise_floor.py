"""
Experiment 0 — Noise floor + minimal structure-vs-detail memory task.

The GATE before any mechanism work. Question: at a fixed memory budget, does a
recurrence-driven retention rule produce structure-up / detail-down retention
ABOVE the noise floor — and does a null rule correctly show NO effect (canary)?

No ATLAS, no LLM, no cluster. numpy only. Runs in seconds.

Task (constructed ground truth):
  - A world has R structural relations (fact IDs S0..S{R-1}) that RECUR: every
    episode restates a random subset of them.
  - Each episode also emits fresh DETAIL facts (unique IDs, appear exactly once).
  - We know exactly which facts are structural vs detail — that's the oracle.

Memory mechanisms (all hold at most BUDGET distinct facts):
  - truncation : keep the most-recently-seen facts        (context-at-fixed-budget)
  - frequency  : keep the most-frequently-seen facts       (recurrence hypothesis)
  - random     : reservoir-sample distinct facts uniformly  (NULL / canary)

Metrics after the stream:
  - structure_retention = fraction of the R structural relations still in memory
  - detail_retention    = fraction of all detail facts seen still in memory
  - diagonal            = structure_retention - detail_retention   (>0 = the effect)

Noise floor = std of the diagonal across seeds. A candidate mechanism's effect is
"real" only if it clears the noise floor. The null must sit at diagonal ~ 0.
"""

from __future__ import annotations

import numpy as np


def gen_stream(rng, n_episodes, n_relations, rel_per_ep, detail_per_ep):
    """Yield a flat stream of (fact_id, is_structural) in episode order."""
    stream = []
    detail_counter = 0
    for _ in range(n_episodes):
        # structural facts that recur: a random subset of the R relations
        rels = rng.choice(n_relations, size=rel_per_ep, replace=False)
        for r in rels:
            stream.append((f"S{r}", True))
        # detail facts: fresh unique IDs, appear exactly once
        for _ in range(detail_per_ep):
            stream.append((f"D{detail_counter}", False))
            detail_counter += 1
    return stream


def run_truncation(stream, budget):
    """Keep the most-recently-seen distinct facts (context at fixed budget)."""
    order = {}  # fact -> last position seen
    for i, (f, _) in enumerate(stream):
        order[f] = i
    kept = sorted(order, key=lambda f: order[f], reverse=True)[:budget]
    return set(kept)


def run_frequency(stream, budget):
    """Keep the most-frequently-seen distinct facts (recurrence hypothesis)."""
    count, last = {}, {}
    for i, (f, _) in enumerate(stream):
        count[f] = count.get(f, 0) + 1
        last[f] = i
    # sort by (count, recency) so ties break toward recent
    kept = sorted(count, key=lambda f: (count[f], last[f]), reverse=True)[:budget]
    return set(kept)


def run_random(stream, budget, rng):
    """Reservoir-sample distinct facts uniformly (NULL / canary)."""
    seen = list({f for f, _ in stream})
    if len(seen) <= budget:
        return set(seen)
    idx = rng.choice(len(seen), size=budget, replace=False)
    return {seen[i] for i in idx}


def retention(memory, stream):
    struct_all = {f for f, s in stream if s}
    detail_all = {f for f, s in stream if not s}
    sr = len(memory & struct_all) / max(1, len(struct_all))
    dr = len(memory & detail_all) / max(1, len(detail_all))
    return sr, dr


def evaluate(mech, n_episodes, seeds, budget, n_relations, rel_per_ep, detail_per_ep):
    rows = []
    for seed in range(seeds):
        rng = np.random.default_rng(seed)
        stream = gen_stream(rng, n_episodes, n_relations, rel_per_ep, detail_per_ep)
        if mech == "truncation":
            mem = run_truncation(stream, budget)
        elif mech == "frequency":
            mem = run_frequency(stream, budget)
        elif mech == "random":
            mem = run_random(stream, budget, rng)
        else:
            raise ValueError(mech)
        sr, dr = retention(mem, stream)
        rows.append((sr, dr, sr - dr))
    a = np.array(rows)
    return a.mean(axis=0), a.std(axis=0)  # (means, stds) over [sr, dr, diag]


def main():
    SEEDS = 20
    BUDGET = 50
    N_RELATIONS = 20
    REL_PER_EP = 4
    DETAIL_PER_EP = 4

    print(f"Exp0 — noise floor | seeds={SEEDS} budget={BUDGET} "
          f"relations={N_RELATIONS} rel/ep={REL_PER_EP} detail/ep={DETAIL_PER_EP}\n")

    for n_ep in (50, 100, 200, 400):
        print(f"=== N_episodes = {n_ep} "
              f"(distinct facts ~ {N_RELATIONS + n_ep*DETAIL_PER_EP}, budget {BUDGET}) ===")
        print(f"{'mechanism':<12} {'struct_ret':>16} {'detail_ret':>16} {'diagonal':>16}")
        diags = {}
        for mech in ("truncation", "frequency", "random"):
            (sr, dr, dg), (srs, drs, dgs) = evaluate(
                mech, n_ep, SEEDS, BUDGET, N_RELATIONS, REL_PER_EP, DETAIL_PER_EP)
            diags[mech] = (dg, dgs)
            print(f"{mech:<12} {sr:>7.3f} ± {srs:<5.3f} "
                  f"{dr:>7.3f} ± {drs:<5.3f} {dg:>7.3f} ± {dgs:<5.3f}")
        # noise-floor verdict
        nf = diags["random"][1]  # std of the null diagonal = a noise-floor proxy
        freq_effect = diags["frequency"][0]
        trunc_effect = diags["truncation"][0]
        print(f"  noise-floor (null diag std) ≈ {nf:.3f}")
        print(f"  frequency diagonal {freq_effect:+.3f} "
              f"({'ABOVE' if abs(freq_effect) > 3*nf else 'below'} 3x noise)")
        print(f"  null (random) diagonal {diags['random'][0]:+.3f} "
              f"(canary — should be ~0)\n")


if __name__ == "__main__":
    main()
