"""
Experiment 1 — Does value-weighting beat frequency where frequency must fail?

Exp 0 showed a trivial task where even truncation gets the structure/detail
diagonal (structure recurs, detail doesn't → frequency wins for free). That does
NOT discriminate a real mechanism. This task is built so frequency PROVABLY
fails, and asks whether a value-weighted rule — using only a NOISY, runtime-
available value signal (never the ground-truth label) — recovers.

Two adversarial cases frequency cannot handle:
  1. recurring-but-useless details (DR): appear often (high count) but must be
     dropped. Frequency wrongly keeps them.
  2. rare-but-critical structure (SR): appear once/twice (low count) but must be
     kept. Frequency wrongly drops them.

Fact types (ground truth, used ONLY for scoring — never shown to a mechanism):
  SF : structural, frequent      (keep)
  SR : structural, RARE          (keep — the hard case)
  DR : detail, RECURRING useless (drop — the distractor)
  DO : detail, one-shot          (drop)
Readout target = all structural (SF ∪ SR): "can memory answer the structural
query needed to act."

Value signal (runtime-available, NOISY, dopaminergic one-shot MAX imprint):
  On each appearance a fact may be tagged. Structural facts get a HIGH-magnitude
  tag with prob p_hit (co-occurrence with reward); details get a LOW-magnitude
  tag with prob p_fa (false alarm). value_score(fact) = MAX tag ever received
  (one strong reward event suffices — this is what lets a RARE structural fact
  beat a RECURRING useless one, which frequency cannot do). We SWEEP p_hit to
  show where value stops winning — no perfect oracle.

Mechanisms (keep <= BUDGET distinct facts):
  truncation | frequency | value | random(null canary)

numpy only, local, seconds.
"""

from __future__ import annotations

import numpy as np

SF_N, SR_N, DR_N = 10, 10, 10          # pool sizes
HIGH, LOW = 1.0, 0.3                    # value tag magnitudes (LOW<HIGH by design)


def gen_stream(rng, n_ep, p_hit, p_fa, sf_prob=0.3, dr_prob=0.3, do_per_ep=4):
    """Return list of (fact, type, value_tag) in stream order.

    value_tag is the runtime signal a mechanism may use; `type` is ground truth
    used ONLY for scoring.
    """
    stream = []
    # rare structural: each SR fact appears in exactly 1-2 random episodes
    sr_eps = {i: set(rng.choice(n_ep, size=int(rng.integers(1, 3)), replace=False))
              for i in range(SR_N)}
    do_counter = 0
    for ep in range(n_ep):
        app_ers = []
        # frequent structural
        for i in range(SF_N):
            if rng.random() < sf_prob:
                app_ers.append((f"SF{i}", "SF"))
        # rare structural
        for i in range(SR_N):
            if ep in sr_eps[i]:
                app_ers.append((f"SR{i}", "SR"))
        # recurring useless detail
        for i in range(DR_N):
            if rng.random() < dr_prob:
                app_ers.append((f"DR{i}", "DR"))
        # one-shot detail
        for _ in range(do_per_ep):
            app_ers.append((f"DO{do_counter}", "DO"))
            do_counter += 1
        # assign noisy value tags
        for fact, typ in app_ers:
            structural = typ in ("SF", "SR")
            if structural:
                tag = HIGH if rng.random() < p_hit else 0.0
            else:
                tag = LOW if rng.random() < p_fa else 0.0
            stream.append((fact, typ, tag))
    return stream


def summarize(stream):
    """Per-fact: count, last position, MAX value tag, SUM value tag."""
    count, last, vmax, vsum, typ = {}, {}, {}, {}, {}
    for i, (f, t, v) in enumerate(stream):
        count[f] = count.get(f, 0) + 1
        last[f] = i
        vmax[f] = max(vmax.get(f, 0.0), v)
        vsum[f] = vsum.get(f, 0.0) + v
        typ[f] = t
    return count, last, vmax, vsum, typ


def keep(mech, count, last, vmax, vsum, budget, rng):
    facts = list(count)
    if len(facts) <= budget:
        return set(facts)
    if mech == "truncation":
        key = lambda f: last[f]
    elif mech == "frequency":
        key = lambda f: (count[f], last[f])
    elif mech == "value":            # MAX imprint (dopaminergic one-shot)
        key = lambda f: (vmax[f], last[f])
    elif mech == "value_sum":        # accumulative — ablation: ≈ frequency?
        key = lambda f: (vsum[f], last[f])
    elif mech == "random":
        idx = rng.choice(len(facts), size=budget, replace=False)
        return {facts[i] for i in idx}
    else:
        raise ValueError(mech)
    return set(sorted(facts, key=key, reverse=True)[:budget])


def score(mem, typ):
    by = lambda t: {f for f, tt in typ.items() if tt == t}
    SF, SR, DR = by("SF"), by("SR"), by("DR")
    STRUCT = SF | SR
    return {
        "struct_all": len(mem & STRUCT) / max(1, len(STRUCT)),   # readout: keep
        "struct_rare": len(mem & SR) / max(1, len(SR)),          # hard case: keep
        "dr_kept": len(mem & DR) / max(1, len(DR)),              # distractor: DROP
    }


def evaluate(mech, n_ep, seeds, budget, p_hit, p_fa):
    rows = []
    for s in range(seeds):
        rng = np.random.default_rng(1000 + s)
        stream = gen_stream(rng, n_ep, p_hit, p_fa)
        count, last, vmax, vsum, typ = summarize(stream)
        mem = keep(mech, count, last, vmax, vsum, budget, rng)
        m = score(mem, typ)
        rows.append([m["struct_all"], m["struct_rare"], m["dr_kept"]])
    a = np.array(rows)
    return a.mean(0), a.std(0)


def main():
    SEEDS, BUDGET, N_EP, P_FA = 20, 25, 200, 0.10
    print(f"Exp1 — value vs frequency | seeds={SEEDS} budget={BUDGET} "
          f"N_ep={N_EP} p_fa={P_FA}")
    print("readout = struct_all (keep↑) | struct_rare (keep↑) | dr_kept (drop↓)\n")

    for p_hit in (1.0, 0.7, 0.4):
        print(f"===== value-signal quality p_hit = {p_hit} =====")
        print(f"{'mech':<11} {'struct_all':>15} {'struct_rare':>15} {'dr_kept↓':>15}")
        res = {}
        for mech in ("truncation", "frequency", "value_sum", "value", "random"):
            mean, std = evaluate(mech, N_EP, SEEDS, BUDGET, p_hit, P_FA)
            res[mech] = (mean, std)
            print(f"{mech:<11} {mean[0]:>7.3f}±{std[0]:<5.3f} "
                  f"{mean[1]:>7.3f}±{std[1]:<5.3f} {mean[2]:>7.3f}±{std[2]:<5.3f}")
        # verdict: value vs frequency on the readout, vs noise floor
        nf = res["random"][1][0]                         # null std on struct_all
        gap = res["value"][0][0] - res["frequency"][0][0]  # value - frequency readout
        canary = res["random"][0]
        print(f"  noise floor (null struct_all std) ≈ {nf:.3f}")
        print(f"  value − frequency on readout = {gap:+.3f} "
              f"({'ABOVE' if abs(gap) > 3*nf else 'below'} 3x noise)")
        print(f"  canary(random): struct_all={canary[0]:.3f} struct_rare={canary[1]:.3f} "
              f"dr_kept={canary[2]:.3f} (should be moderate & type-agnostic)\n")


if __name__ == "__main__":
    main()
