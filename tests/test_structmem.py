"""Tests for StructMem-Bench. These encode the DESIGN INVARIANTS — each guards a
specific way an earlier experiment fooled itself. Run: python3 -m pytest tests/ -q
(or python3 tests/test_structmem.py for a plain run).
"""

from __future__ import annotations

import numpy as np

from structmem_bench.config import BenchConfig
from structmem_bench import tasks, memory, metrics, harness, stats


def _cfg(**kw):
    return BenchConfig(**kw)


# ---------- config / generation ----------
def test_fact_universe_sizes():
    c = _cfg()
    s = tasks.generate(c, seed=0)
    assert s.X.shape == (c.n_episodes, c.n_facts)
    assert s.value.shape == s.X.shape
    assert s.y.shape == (c.n_episodes,)
    # counts by type match config
    assert (s.fact_type == tasks.SF).sum() == c.n_struct_frequent
    assert (s.fact_type == tasks.SR).sum() == c.n_struct_rare
    assert (s.fact_type == tasks.DR).sum() == c.n_detail_recurring
    assert (s.fact_type == tasks.DO).sum() == c.oneshot_pool


def test_determinism():
    c = _cfg()
    a = tasks.generate(c, seed=3)
    b = tasks.generate(c, seed=3)
    assert np.array_equal(a.X, b.X) and np.array_equal(a.y, b.y)
    assert np.array_equal(a.value, b.value)


def test_value_never_reveals_absent():
    s = tasks.generate(_cfg(), seed=1)
    # value must be exactly 0 wherever a fact is absent
    assert np.all(s.value[s.X == 0] == 0.0)


def test_oneshot_appear_once():
    s = tasks.generate(_cfg(), seed=2)
    do = s.fact_type == tasks.DO
    assert np.all(s.X[:, do].sum(0) == 1.0)


def test_rare_are_rare():
    s = tasks.generate(_cfg(), seed=4)
    sr = s.fact_type == tasks.SR
    assert np.all(s.X[:, sr].sum(0) <= 2)


# ---------- load-bearing invariant: frequency can't separate matched facts ----------
def test_frequency_cannot_separate_matched():
    # SF and DR share identical marginal -> frequency dP ~ 0 (guards the biased-
    # generator bug where structure was accidentally more frequent)
    dp = harness.sanity_frequency_matched(_cfg(), seeds=20)
    assert abs(dp) < 0.5, f"frequency separated matched-marginal facts (dP={dp})"


def test_frequency_fails_hard_cases():
    # the designed failure: frequency drops rare-critical structure AND keeps
    # recurring-useless detail. If it doesn't fail these, the benchmark is trivial.
    h = harness.frequency_hard_case_failure(_cfg(), seeds=20, budget=25)
    assert h["rare_retention"] < 0.5, f"frequency kept rare structure: {h}"
    assert h["recurring_detail_kept"] > 0.5, f"frequency dropped recurring detail: {h}"


# ---------- canaries must actually be able to fail, and must pass here ----------
def test_canaries_pass():
    c = harness.check_canaries(_cfg(), seeds=15)
    assert c["random_ok"], f"random canary above chance: {c}"
    assert c["permutation_ok"], f"permutation canary above chance: {c}"


def test_permutation_destroys_real_signal():
    # The permutation canary must reduce a GENUINELY predictive score to chance when
    # labels are shuffled — proving AP reflects real structure, not metric inflation.
    # (Oracle predicts labels perfectly on true labels; under permutation -> chance.)
    s = tasks.generate(_cfg(), seed=7)
    oracle = s.is_structural.astype(float)
    rng = np.random.default_rng(0)
    chance = float(s.is_structural.mean())
    true_ap = metrics.average_precision(oracle, s.is_structural)
    perm_ap = stats.permutation_canary_ap(oracle, s.is_structural, rng, n_perm=40)
    assert true_ap > 0.9, f"oracle should score ~1 on true labels, got {true_ap}"
    assert stats.canary_ok(perm_ap, chance), \
        f"permuted AP {perm_ap} should collapse to chance {chance}"


# ---------- oracle ceiling / random floor ordering ----------
def test_oracle_beats_random():
    agg = harness.run_per_fact(_cfg(), methods=["oracle", "random"], seeds=15)
    assert agg["oracle"]["ap_structural"][0] > agg["random"]["ap_structural"][0] + 0.3


# ---------- metrics behave ----------
def test_ap_bounds_and_perfect():
    scores = np.array([3.0, 2.0, 1.0, 0.0])
    pos = np.array([True, True, False, False])
    assert abs(metrics.average_precision(scores, pos) - 1.0) < 1e-9
    # reversed ranking -> low AP
    assert metrics.average_precision(-scores, pos) < 0.75


def test_retention_budget_monotone():
    s = tasks.generate(_cfg(), seed=5)
    sc = memory.score_oracle(s, np.random.default_rng(0))
    r_small = metrics.retention_at_budget(sc, s.is_structural, 5)
    r_big = metrics.retention_at_budget(sc, s.is_structural, 100)
    assert r_big >= r_small


# ---------- relational: learned pairs beat item-lifted when deps are concentrated ----
def test_relational_beats_item_lifted_when_concentrated():
    # With few, pivotal dependencies (default n_recipes=4), relational value beats
    # per-item lifting. (The advantage is regime-dependent — it grows as recipes
    # decrease; see the recipe-count sweep. It does NOT hold for many diffuse recipes,
    # which is honestly reported, not hidden.)
    c = _cfg(outcome="relational", n_recipes=4)
    agg = harness.run_relational(c, seeds=15)
    rel = agg["relational"]["ap_relational"][0]
    itm = agg["item_lifted"]["ap_relational"][0]
    assert rel > itm + 0.05, f"relational {rel:.3f} not > item_lifted {itm:.3f}"


def test_relational_advantage_is_significant():
    # Robust invariant: given adequate data, relational value's advantage over
    # per-item lifting is statistically significant (paired across seeds). The
    # MAGNITUDE depends on data adequacy + dependency concentration (characterized in
    # the runner's sweep), but the SIGN is robust.
    c = _cfg(outcome="relational", n_recipes=4, n_episodes=300)
    agg = harness.run_relational(c, seeds=30)
    va = np.array(agg["relational"]["ap_relational"][2])
    vb = np.array(agg["item_lifted"]["ap_relational"][2])
    d = stats.paired_diff(va, vb)
    assert d["mean"] > 0 and d["sig"], f"relational advantage not significant: {d}"


# ---------- the position-leak regression: a blind index method must NOT win ----------
def test_positional_leak_closed():
    ap = harness.worst_positional_ap(_cfg(), seeds=15)
    chance = 20 / _cfg().n_facts
    assert ap < chance + 0.05, f"index-ranking method scores {ap} >> chance {chance}"


def test_constant_scorer_canary():
    c = harness.check_canaries(_cfg(), seeds=15)
    assert c["constant_ok"], f"constant-scorer canary above chance: {c}"


# ---------- value_z: the sufficient statistic (audit fix) ----------
def test_value_z_passes_canary_at_dprime_zero():
    # frequency-neutral: with NO value signal (d'=0), value_z must sit at chance.
    c = _cfg(value_dprime=0.0)
    aps = []
    for s in range(15):
        stream = tasks.generate(c, seed=s)
        aps.append(metrics.average_precision(memory.score_value_z(stream, None),
                                             stream.is_structural))
    chance = 20 / c.n_facts
    assert np.nanmean(aps) < chance + 0.05, f"value_z leaks at d'=0: {np.nanmean(aps)}"


def test_value_z_beats_frequency_when_signal_present():
    # the corrected claim: a frequency-NEUTRAL, evidence-accumulating aggregation
    # beats frequency at d'>0 (contra exp1-corrected's overcorrection).
    agg = harness.run_per_fact(_cfg(value_dprime=1.5),
                               methods=["value_z", "frequency"], seeds=20)
    d = stats.paired_diff(np.array(agg["value_z"]["ap_structural"][2]),
                          np.array(agg["frequency"]["ap_structural"][2]))
    assert d["mean"] > 0.2 and d["sig"], f"value_z should beat frequency: {d}"


def test_value_z_not_frequency_contaminated():
    # unlike value_max/value_sum, value_z must NOT beat chance at d'=0 (frequency
    # contamination test).
    agg = harness.run_per_fact(_cfg(value_dprime=0.0),
                               methods=["value_z", "value_max"], seeds=15)
    chance = 20 / _cfg().n_facts
    assert agg["value_z"]["ap_structural"][0] < chance + 0.05
    assert agg["value_max"]["ap_structural"][0] > agg["value_z"]["ap_structural"][0]


# ---------- linear outcome base rate (audit fix #1) ----------
def test_linear_outcome_base_rate_sane():
    c = _cfg(outcome="linear")
    rates = [tasks.generate(c, seed=s).y.mean() for s in range(15)]
    mr = float(np.mean(rates))
    assert 0.2 < mr < 0.8, f"linear base rate degenerate: {mr}"


# ---------- DR-partner invariant across distractor count (audit fix #2) ----------
def test_frequency_uninformative_across_dr_count():
    for ndr in (5, 8, 10):
        dp = harness.sanity_frequency_matched(_cfg(n_detail_recurring=ndr), seeds=15)
        assert abs(dp) < 0.5, f"frequency leaked at n_detail_recurring={ndr}: dP={dp}"


def test_dr_count_over_sf_rejected():
    # config must REJECT a setting that would silently break the frequency invariant
    raised = False
    try:
        _cfg(n_detail_recurring=15, n_struct_frequent=10)
    except AssertionError:
        raised = True
    assert raised, "config should reject n_detail_recurring > n_struct_frequent"


# ---------- paired stats ----------
def test_paired_diff_zero_when_identical():
    a = np.array([0.5, 0.6, 0.7])
    d = stats.paired_diff(a, a.copy())
    assert abs(d["mean"]) < 1e-9 and not d["sig"]


if __name__ == "__main__":
    import traceback
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = 0
    for fn in fns:
        try:
            fn(); passed += 1; print(f"PASS {fn.__name__}")
        except Exception:
            print(f"FAIL {fn.__name__}"); traceback.print_exc()
    print(f"\n{passed}/{len(fns)} passed")
