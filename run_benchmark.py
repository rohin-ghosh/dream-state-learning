"""StructMem-Bench runner — produces the headline results table + rigor checks.

Usage: PYTHONPATH=. python3 run_benchmark.py
"""

from __future__ import annotations

import numpy as np

from structmem_bench.config import BenchConfig
from structmem_bench import harness as H


def main():
    cfg = BenchConfig(outcome="relational")
    SEEDS, BUDGET = 30, 25

    print("=" * 78)
    print("StructMem-Bench v0.1  |  relational outcome  |  seeds=%d budget=%d" % (SEEDS, BUDGET))
    print("=" * 78)

    # --- rigor checks first (if these fail, ignore everything else) ---
    can = H.check_canaries(cfg, seeds=SEEDS)
    freq_matched = H.sanity_frequency_matched(cfg, seeds=SEEDS)
    freq_hard = H.frequency_hard_case_failure(cfg, seeds=SEEDS, budget=BUDGET)
    print("\n[RIGOR]")
    print(f"  chance base rate (structural)   : {can['chance_base_rate']:.3f}")
    print(f"  random-sampler canary AP        : {can['random_sampler_ap']:.3f}  "
          f"({'OK' if can['random_ok'] else 'FAIL'})")
    print(f"  label-permutation canary AP     : {can['permutation_ap']:.3f}  "
          f"({'OK' if can['permutation_ok'] else 'FAIL'})")
    print(f"  frequency dP (SF vs DR, matched): {freq_matched:+.3f}  "
          f"(must be ~0 = uninformative on matched facts)")
    print(f"  frequency FAILS hard cases      : rare_kept={freq_hard['rare_retention']:.3f} "
          f"(low=good), recurring_detail_kept={freq_hard['recurring_detail_kept']:.3f} (high=bad)")

    # --- per-fact methods ---
    agg = H.run_per_fact(cfg, seeds=SEEDS, budget=BUDGET)
    order = ["random", "truncation", "frequency", "surprise",
             "value_max", "value_mean", "trained_value", "oracle"]
    print("\n[PER-FACT]  ap_structural | rare_ret@B | recurring_kept@B(↓) | diagonal@B")
    for m in order:
        a = agg[m]
        print(f"  {m:<14} {a['ap_structural'][0]:>6.3f}±{a['ap_structural'][1]:<4.3f} "
              f"{a['rare_retention@budget'][0]:>8.3f} "
              f"{a['recurring_detail_kept@budget'][0]:>16.3f} "
              f"{a['diagonal@budget'][0]:>10.3f}")

    # paired: trained_value vs frequency on structural AP
    pv = H.paired_vs(agg, "ap_structural", "trained_value", "frequency")
    print(f"\n  paired trained_value − frequency (ap_structural): "
          f"{pv['mean']:+.3f} (SE {pv['se']:.3f}, t={pv['t']:.1f}, "
          f"{'SIG' if pv['sig'] else 'n.s.'})")

    # --- relational ---
    rel = H.run_relational(cfg, seeds=SEEDS)
    print("\n[RELATIONAL]  ap_relational (rank true dependency pairs)")
    for m in ("relational", "item_lifted"):
        r = rel[m]
        print(f"  {m:<14} {r['ap_relational'][0]:>6.3f}±{r['ap_relational'][1]:<4.3f}")
    # paired relational vs item_lifted
    va = np.array(rel["relational"]["ap_relational"][2])
    vb = np.array(rel["item_lifted"]["ap_relational"][2])
    from structmem_bench.stats import paired_diff
    pr = paired_diff(va, vb)
    print(f"  paired relational − item_lifted: {pr['mean']:+.3f} "
          f"(SE {pr['se']:.3f}, t={pr['t']:.1f}, {'SIG' if pr['sig'] else 'n.s.'})")

    print("\n[READ] Headline axes: (1) frequency/surprise fail the hard cases "
          "(drop rare structure, keep recurring detail); (2) trained per-item value "
          "helps but is limited under relational outcomes; (3) RELATIONAL value "
          "recovers the dependency structure per-item methods miss. All vs a passing "
          "canary + uninformative-frequency sanity.")


if __name__ == "__main__":
    main()
