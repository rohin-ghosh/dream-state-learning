"""
Experiment 1 (CORRECTED) — value aggregation vs frequency under OVERLAPPING value.

This replaces exp1_value_vs_frequency.py, whose results were shown (by adversarial
code review) to be closed-form artifacts of binary value magnitudes (HIGH=1.0 >
LOW=0.3 makes `max` a label-threshold, not a ranking). Fixes applied:

1. HIGH/LOW ratio → CONTINUOUS OVERLAPPING value. Per appearance a fact draws
   value ~ N(mu, 1); mu = d' for structural, 0 for detail. Sweep d' (discrimin-
   ability). d'=0 is a REAL canary: value carries no type info → must collapse to
   chance. This is the parameter that actually decides whether a mechanism exists.
2. Budget-free primary metric: AVERAGE PRECISION (AP) of ranking structural facts
   by each mechanism's score. Removes the budget-fill artifact entirely. Retention
   at several budgets reported secondarily for concreteness.
3. Real canary = d'=0 (not the old random-sampler that structurally could not
   fail). value must drop to the structural base rate (~0.024).
4. PAIRED per-seed test: value_mean − frequency AP difference across seeds, mean
   ± standard error (identical stream per seed → valid pairing).
5. No oracle headline: d'=∞-like well-separated case is labelled a CEILING, not
   the result.

Extra: aggregation sweep {max, mean, sum}. Under overlap, `max` is frequency-
biased (max of many draws inflates frequent facts — incl. useless recurring
distractors), so we expect MEAN (frequency-neutral) to be the aggregation that
actually works. This directly re-tests the earlier "max is load-bearing" claim.

numpy only, local, seconds.
"""

from __future__ import annotations

import numpy as np

SF_N, SR_N, DR_N = 10, 10, 10
POS = ("SF", "SR")  # structural = positive class for scoring


def gen_stream(rng, n_ep, dprime, sf_prob=0.3, dr_prob=0.3, do_per_ep=4):
    stream = []
    sr_eps = {i: set(rng.choice(n_ep, size=int(rng.integers(1, 3)), replace=False))
              for i in range(SR_N)}
    do = 0
    for ep in range(n_ep):
        apps = []
        for i in range(SF_N):
            if rng.random() < sf_prob:
                apps.append((f"SF{i}", "SF"))
        for i in range(SR_N):
            if ep in sr_eps[i]:
                apps.append((f"SR{i}", "SR"))
        for i in range(DR_N):
            if rng.random() < dr_prob:
                apps.append((f"DR{i}", "DR"))
        for _ in range(do_per_ep):
            apps.append((f"DO{do}", "DO")); do += 1
        for fact, typ in apps:
            mu = dprime if typ in POS else 0.0
            stream.append((fact, typ, rng.normal(mu, 1.0)))
    return stream


def summarize(stream):
    count, last, vmax, vsum, n, typ = {}, {}, {}, {}, {}, {}
    for i, (f, t, v) in enumerate(stream):
        count[f] = count.get(f, 0) + 1
        last[f] = i
        vmax[f] = max(vmax.get(f, -1e9), v)
        vsum[f] = vsum.get(f, 0.0) + v
        n[f] = n.get(f, 0) + 1
        typ[f] = t
    vmean = {f: vsum[f] / n[f] for f in vsum}
    return count, last, vmax, vsum, vmean, typ


def score_map(mech, count, last, vmax, vsum, vmean, facts, rng):
    if mech == "frequency":  return {f: count[f] for f in facts}
    if mech == "truncation": return {f: last[f] for f in facts}
    if mech == "value_max":  return {f: vmax[f] for f in facts}
    if mech == "value_sum":  return {f: vsum[f] for f in facts}
    if mech == "value_mean": return {f: vmean[f] for f in facts}
    if mech == "random":     return {f: rng.random() for f in facts}
    raise ValueError(mech)


def average_precision(sc, typ):
    order = sorted(sc, key=lambda f: sc[f], reverse=True)
    n_pos = sum(1 for f in sc if typ[f] in POS)
    hits, ap = 0, 0.0
    for k, f in enumerate(order, 1):
        if typ[f] in POS:
            hits += 1
            ap += hits / k
    return ap / max(1, n_pos)


def retention(sc, typ, budget):
    facts = list(sc)
    mem = set(facts) if len(facts) <= budget else \
        set(sorted(facts, key=lambda f: sc[f], reverse=True)[:budget])
    S = {f for f in typ if typ[f] in POS}
    SR = {f for f in typ if typ[f] == "SR"}
    DR = {f for f in typ if typ[f] == "DR"}
    return (len(mem & S) / max(1, len(S)),
            len(mem & SR) / max(1, len(SR)),
            len(mem & DR) / max(1, len(DR)))


def main():
    SEEDS, N_EP = 30, 200
    MECHS = ("truncation", "frequency", "value_sum", "value_max", "value_mean", "random")
    DPRIMES = (3.0, 1.5, 0.5, 0.0)   # last is the real canary

    base_rate = (SF_N + SR_N)  # positives; total facts ~830 → base ≈ 0.024
    print(f"Exp1-CORRECTED | seeds={SEEDS} N_ep={N_EP} | primary metric = "
          f"Average Precision (budget-free), structural=positive\n"
          f"(random/chance AP ≈ base rate ≈ {base_rate}/~830 ≈ 0.024)\n")

    for d in DPRIMES:
        tag = "  <-- CANARY (no type info; must → chance)" if d == 0.0 else \
              ("  <-- CEILING (well separated)" if d == 3.0 else "")
        print(f"===== d' = {d} {tag} =====")
        ap = {m: [] for m in MECHS}
        for s in range(SEEDS):
            rng = np.random.default_rng(2000 + s)
            stream = gen_stream(rng, N_EP, d)
            cnt, lst, vmx, vsm, vmn, typ = summarize(stream)
            facts = list(cnt)
            for m in MECHS:
                sc = score_map(m, cnt, lst, vmx, vsm, vmn, facts, rng)
                ap[m].append(average_precision(sc, typ))
        arr = {m: np.array(ap[m]) for m in MECHS}
        for m in MECHS:
            print(f"  {m:<11} AP = {arr[m].mean():.3f} ± {arr[m].std():.3f}")
        # paired test: value_mean vs frequency (identical streams per seed)
        diff = arr["value_mean"] - arr["frequency"]
        se = diff.std(ddof=1) / np.sqrt(SEEDS)
        t = diff.mean() / se if se > 0 else float("inf")
        print(f"  paired value_mean − frequency = {diff.mean():+.3f} "
              f"(SE {se:.3f}, t≈{t:.1f}, {'SIG' if abs(t) > 3 else 'n.s.'})")
        # also value_max vs frequency to re-test the old claim
        diff2 = arr["value_max"] - arr["frequency"]
        se2 = diff2.std(ddof=1) / np.sqrt(SEEDS)
        t2 = diff2.mean() / se2 if se2 > 0 else float("inf")
        print(f"  paired value_max  − frequency = {diff2.mean():+.3f} "
              f"(SE {se2:.3f}, t≈{t2:.1f}, {'SIG' if abs(t2) > 3 else 'n.s.'})\n")

    # budget sweep for the headline comparison at moderate overlap d'=1.5
    print("=== budget sweep @ d'=1.5 (readout = structural retention) ===")
    print(f"{'budget':>7} {'frequency':>12} {'value_max':>12} {'value_mean':>12}")
    for budget in (15, 20, 25, 40):
        got = {m: [] for m in ("frequency", "value_max", "value_mean")}
        for s in range(SEEDS):
            rng = np.random.default_rng(2000 + s)
            stream = gen_stream(rng, N_EP, 1.5)
            cnt, lst, vmx, vsm, vmn, typ = summarize(stream)
            facts = list(cnt)
            for m in got:
                sc = score_map(m, cnt, lst, vmx, vsm, vmn, facts, rng)
                got[m].append(retention(sc, typ, budget)[0])
        print(f"{budget:>7} "
              f"{np.mean(got['frequency']):>12.3f} "
              f"{np.mean(got['value_max']):>12.3f} "
              f"{np.mean(got['value_mean']):>12.3f}")


if __name__ == "__main__":
    main()
