"""
Experiment 5 — REGIME SWEEP: where is the differentiation window widest?

Purpose: set the LLM-tier game at the configuration where value-driven allocation
most visibly beats the best non-value baseline — BEFORE spending GPU. (Rohin's
scoping: baseline context aged out; surprise/frequency memory keeps the wrong
things; policy-attention keeps just enough. Find where that window is widest.)

WINDOW := AP_structural(value policy) − max(AP of uniform, frequency, truncation)
in the physical interference memory (exp4 machinery). Reported for both
value_z (per-event tags ~ oracle-ish salience) and trained_item (outcome-trained),
plus oracle ceiling for context.

Sweep: data horizon (n_episodes) × memory capacity (d) × confound strength ×
recipe count. CPU, minutes.
"""

from __future__ import annotations

import numpy as np

from structmem_bench.config import BenchConfig
from structmem_bench.tasks import generate
from structmem_bench.metrics import average_precision
from experiments.exp4_end_to_end import make_keys, write_per_fact, read_per_fact, \
    weights_per_fact

POLICIES = ("uniform", "frequency", "value_z", "trained_item", "oracle")


def weights_frequency(stream):
    return stream.X.sum(0)


def run_config(cfg, d, seeds):
    ap = {p: [] for p in POLICIES}
    for s in range(seeds):
        stream = generate(cfg, seed=s)
        rng = np.random.default_rng(90_000 + s)
        K = make_keys(rng, cfg.n_facts, d)
        for p in POLICIES:
            if p == "frequency":
                W = weights_frequency(stream)
            else:
                W = weights_per_fact(stream, p if p != "frequency" else "uniform")
            M = write_per_fact(K, W)
            ap[p].append(average_precision(read_per_fact(K, M),
                                           stream.is_structural))
    return {p: float(np.mean(v)) for p, v in ap.items()}


def main():
    SEEDS = 12
    rows = []
    print("Exp5 — regime sweep | window = value − best(non-value) on AP_structural")
    print(f"{'n_ep':>5} {'d':>5} {'conf_a':>7} {'recipes':>8} | "
          f"{'best_base':>9} {'value_z':>8} {'trained':>8} {'oracle':>7} | "
          f"{'WINDOW(z)':>9} {'WINDOW(tr)':>10}")
    with np.errstate(all="ignore"):
        for n_ep in (200, 400, 800):
            for d in (32, 64, 128):
                for conf_a in (0.7, 0.9):
                    for n_rec in (4, 8):
                        cfg = BenchConfig(outcome="relational", n_recipes=n_rec,
                                          n_episodes=n_ep, confound_a=conf_a)
                        r = run_config(cfg, d, SEEDS)
                        base = max(r["uniform"], r["frequency"])
                        wz = r["value_z"] - base
                        wt = r["trained_item"] - base
                        rows.append((n_ep, d, conf_a, n_rec, base, r["value_z"],
                                     r["trained_item"], r["oracle"], wz, wt))
                        print(f"{n_ep:>5} {d:>5} {conf_a:>7} {n_rec:>8} | "
                              f"{base:>9.3f} {r['value_z']:>8.3f} "
                              f"{r['trained_item']:>8.3f} {r['oracle']:>7.3f} | "
                              f"{wz:>+9.3f} {wt:>+10.3f}")

    rows.sort(key=lambda x: -x[8])
    print("\nTOP-5 configs by value_z window (candidate LLM-tier game settings):")
    for r in rows[:5]:
        print(f"  n_ep={r[0]} d={r[1]} conf_a={r[2]} recipes={r[3]} "
              f"window_z={r[8]:+.3f} window_trained={r[9]:+.3f} oracle={r[7]:.3f}")
    rows.sort(key=lambda x: -x[9])
    print("TOP-3 by trained window:")
    for r in rows[:3]:
        print(f"  n_ep={r[0]} d={r[1]} conf_a={r[2]} recipes={r[3]} "
              f"window_trained={r[9]:+.3f}")


if __name__ == "__main__":
    main()
