# Red-team 1: StructMem-Bench gameability

Adversarial audit of `structmem_bench/`. Goal of the benchmark: measure whether a
memory method retains RELATIONAL STRUCTURE while shedding EPISODIC DETAIL at a fixed
budget, scored vs ground-truth labels, discriminating real relational retention from
frequency/surprise/per-item/truncation. Methods are *supposed* to observe only
`(X presence, value samples, y outcomes)` — never `fact_type` or `relations`.

Baseline (seeds=30, budget=25, relational outcome) reproduced from `run_benchmark.py`:
per-fact oracle ap_structural=1.000 diagonal=0.994; value_max=0.641/0.596;
frequency=0.352/0.328. Relational learned=0.301 > item_lifted=0.147 (paired t=5.2).

---

## SEVERITY-RANKED SUCCESSFUL BREAKS

### BREAK #1 — CRITICAL: fixed fact-universe LAYOUT leaks the label through the index

`tasks._layout()` assigns fact types to **contiguous, seed-independent index ranges**:
structural = indices `[0,20)`, detail = `[20, 846)`, on *every* seed and every config.
Verified: for seeds 0/5/17 the structural indices are always `min=0 max=19`.

A method that observes **nothing at all** — not X, not value, not y — and simply ranks
facts by index wins the entire per-fact tier:

```python
def score_positional(s, rng):
    return -np.arange(s.cfg.n_facts, dtype=float)   # lower index = "more structural"
```

| metric (seed-mean, B=25)      | positional | oracle | value_max |
|-------------------------------|:----------:|:------:|:---------:|
| ap_structural                 | **1.000**  | 1.000  | 0.641     |
| rare_retention@budget         | **1.000**  | 1.000  | 0.223     |
| recurring_detail_kept@budget↓ | **0.500**  | 0.500  | 0.323     |
| diagonal@budget               | **0.994**  | 0.994  | 0.596     |

The positional method **ties the graph-oracle ceiling exactly** on every headline
per-fact axis, while genuinely-informative methods (value_max) score far lower. It is
the exact analog of the "truncation got 0.80 diagonal in exp0" / "degenerate threshold
in exp1" breaks this project has already suffered.

**The rigor layer does not catch it.** The permutation canary permutes *labels within a
seed*; positional scores are fixed, so permuted-label AP collapses to chance
(`perm_ap=0.032 ≈ chance 0.024`, `canary_ok=True`). The leak is a global
index→type correspondence, not within-seed label leakage, so the canary is blind to it.
This also breaks the **oracle-as-upper-bound** claim (Attack 4): a label-free method
reaches the ceiling, and on `dp_structural` the oracle is a degenerate `+inf`
(zero within-class variance) while positional is finite — the "ceiling" is neither
unique nor well-defined.

**Why it matters:** every per-fact headline number (ap_structural, diagonal, the
frequency-fails-hard-cases story) is reported on a benchmark where the trivial
index-ranking baseline is indistinguishable from the oracle. Any method that even
weakly correlates its score with fact index inherits free, unearned structural AP.

**Minimal fix:** apply a per-seed random permutation of the fact (column) axis in
`tasks.generate`, remapping `X`, `value`, `fact_type`, and `relations` consistently, so
that index carries zero information about type. Concretely, after construction:
```python
perm = rng.permutation(F)
X, value = X[:, perm], value[:, perm]
inv = np.argsort(perm)
ft = ft[perm]                       # relabel via inverse map
relations = sorted((inv[i], inv[j]) if inv[i]<inv[j] else (inv[j], inv[i])
                   for (i, j) in relations)
```
After this, `score_positional` must collapse to `random` (ap≈chance). Add a regression
test asserting exactly that (a "positional canary"), analogous to the existing random
canary — it is the control that would have caught this class of bug.

---

### BREAK #2 — MINOR: `@budget` diagonal is a fill artifact; rankings flip with budget

Budget sweep of `diagonal@budget` (seeds=20):

| budget | positional | oracle | value_max | frequency | trained_value |
|:------:|:----------:|:------:|:---------:|:---------:|:-------------:|
| 20     | 1.000      | 1.000  | 0.580     | 0.260     | 0.129         |
| 25     | 0.994      | 0.994  | 0.602     | 0.336     | 0.123         |
| 60     | 0.952      | 0.952  | 0.657     | **0.952** | 0.125         |
| 100    | 0.903      | 0.903  | 0.693     | 0.903     | 0.127         |

Two problems: (a) at budget ≥ 60 **frequency reaches the oracle's diagonal** (0.952,
0.903) — the "frequency fails" headline is budget-dependent and vanishes once the budget
comfortably exceeds the ~20 structural facts; (b) the value_max-vs-frequency ranking
**flips** between B=25 (value_max 0.602 > freq 0.336) and B=60 (freq 0.952 > value_max
0.657). This confirms the `@budget` metrics reward budget size relative to the (fixed,
small) structural-fact count rather than pure method quality.

The spec already flags this and designates budget-free AP as the real metric — so this
is only MINOR *on its own*. But note the escape hatch (AP) is exactly what BREAK #1
destroys, so in combination the per-fact tier has no un-gamed headline number left.

**Minimal fix:** report AP as primary (already intended) AND, for the @budget story,
fix budget as a fraction of `n_structural` and report the sweep, never a single budget;
or replace diagonal@B with a budget-integrated area. Ensure the "frequency fails"
claim is stated at the budget regime where structural facts exceed the budget.

---

## ATTACKS THAT FAILED (benchmark HELD) — good news

### Relational AP is NOT trivially gameable (Attack 2)

Target: learned `relational` ap_relational=0.301, `item_lifted`=0.147. Naive tricks:

| method                    | ap_relational |
|---------------------------|:-------------:|
| positional-pairs (both idx<20) | 0.087   |
| raw co-occurrence count        | 0.006   |
| struct-positional + cooc tiebreak | 0.096 |
| **learned relational**         | **0.301** |
| item_lifted                    | 0.147   |

Ranking *all* structural-involving pairs (positional-pairs) scores only 0.087 because
the 8 true recipes are a small subset of the ~C(20,2) structural pairs; you cannot get
relational AP by "keep everything structural." Pure co-occurrence is near-zero (by
design: DR confounds have matched marginals, and structural pairs co-occur no more than
chance absent the recipe). The learned pairwise fit genuinely recovers *which*
structural pairs are recipes. The relational headline (relational > item_lifted, and
both > trivial) **holds against gaming** — the one axis that is actually load-bearing
for the paper's novelty is sound. (Caveat: this is only meaningful once BREAK #1 is
fixed, because the relational tier still lives on the same fixed-index universe;
re-verify after permuting indices.)

### Frequency uninformative-on-matched-facts sanity holds

`dP(SF vs DR, matched)=-0.061 ≈ 0` — the collinear-confound construction is correct;
frequency genuinely cannot separate matched-marginal facts. No break here.

---

## SUMMARY

| # | attack | result | severity |
|---|--------|--------|----------|
| 1 | fixed layout / positional index exploit (per-fact) | **BROKEN** — blind index method ties oracle on all per-fact metrics, passes canary | **CRITICAL** |
| 3 | `@budget` diagonal fill artifact / ranking flip | **BROKEN** — frequency reaches oracle diagonal at large B; value/freq order flips | MINOR |
| 4 | oracle not a strict upper bound | **BROKEN** (consequence of #1) — positional ties/matches oracle; oracle dp is degenerate +inf | (folds into #1) |
| 2 | relational AP gaming (positional / co-occurrence) | HELD — learned relational 0.301 vs best trivial 0.096 | — |

**Bottom line:** the *relational* tier (the paper's actual novelty) is robust to gaming,
but the entire *per-fact* tier — every ap_structural / diagonal number and the
"frequency fails / oracle ceiling" narrative — is invalidated by a zero-information
index-ranking baseline, because fact type is a fixed function of column index and the
canaries cannot see it. **Fix #1 (per-seed column permutation + a positional canary
test) is mandatory before any per-fact result can be reported.**
