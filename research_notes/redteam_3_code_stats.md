# Red-team audit: StructMem-Bench code & statistics

Scope: `structmem_bench/{config,tasks,memory,metrics,stats,harness}.py`, `run_benchmark.py`.
Method: adversarial line read + reproducing probes. All probes are self-contained and were run
against the current tree (relational outcome, seeds=30, budget=25).

---

## MOST DANGEROUS ISSUE — contiguous type-layout leaks through stable-sort tie-breaking (CRITICAL)

`tasks._layout` lays facts out **contiguously by type**: structural facts (SF,SR) occupy the
lowest indices `[0, 20)`, all detail follows. Every ranking metric
(`metrics.average_precision`, `metrics.retention_at_budget`) resolves ties with
`np.argsort(-scores, kind="stable")`, whose tie-break is **ascending original index**. Because the
positive class (structural) sits at the lowest indices, **any method that emits tied scores gets its
tied structural facts ranked first for free** — a pure label leak via position.

### Proof 1 — a zero-signal method scores like the oracle
```
CONSTANT scorer (all zeros)  AP_structural = 1.000   (chance base rate = 0.024)
CONSTANT scorer  struct_retention@25 = 1.000
INDEX(position) scorer        AP_structural = 1.000
```
A method with **no information** matches the oracle (AP=1.0, retention=1.0) purely because
structural facts are the lowest 20 indices and land first in every tie group / the top-25 window.
A non-oracle ties the oracle without any signal — violating the benchmark's core guarantee.

### Proof 2 — it inflates the ACTUALLY-REPORTED methods
`frequency` and `surprise` emit integer / heavily-tied scores, so they are directly contaminated.
Comparing the code's stable-sort AP to an unbiased random-tie-break AP:
```
method        stable-sort AP   random-tiebreak AP   inflation
frequency         0.352            0.253             +0.099
surprise          0.277            0.016             +0.261   <-- entirely fake
value_mean        0.172            0.172             +0.000   (continuous, no ties)
random            0.029            0.029             +0.000
```
And on `surprise`'s headline claim (rare-structure retention):
```
surprise rare_retention@25:  stable=0.530   random-tiebreak=0.016   inflation=+0.514
```
**The entire "surprise partially recovers rare structure" result (rare_kept≈0.53) is a layout
artifact.** With correct tie handling it is ≈0.016 (chance). `frequency`'s AP is inflated by ~0.10.

### Proof 3 — benchmark is not invariant to fact ordering (it must be)
Permuting the fact index order (relabeling only) changes reported AP:
```
method        orig_AP  shuffled_AP  delta
frequency      0.352     0.250      +0.102
surprise       0.277     0.015      +0.262
value_max      0.641     0.641      +0.000
trained_value  0.162     0.161      +0.001
oracle         1.000     1.000      +0.000
```
A correct benchmark is invariant to fact relabeling. Continuous-score methods are invariant; every
tied-score method is not. This is the signature of a position leak.

**Severity: CRITICAL.** It changes the qualitative conclusions (surprise's rare-structure recovery
is fabricated; frequency's ranking is over-credited).

---

## CRITICAL GAP — the rigor layer cannot catch method-level leakage

The permutation canary is the one guard that *would* catch this: run on the constant scorer's own
scores it correctly collapses to chance —
```
perm-canary AP on constant-score method = 0.029  (== chance)
```
But `harness.check_canaries` **only ever applies the permutation canary to `frequency`**, never to
the methods under test. The random-sampler canary uses continuous random scores (no ties) so it is
structurally blind to the leak. Net effect: **a maximally-leaking method passes all rigor checks**
(random-sampler OK, permutation OK — because permutation is computed on a different method) while
reporting AP=1.0. The canary suite as wired can only catch a broken RNG, not method-level label
leakage. This is exactly the failure mode the rigor layer claims to prevent.

**Severity: CRITICAL** (it is what lets Issue #1 go undetected).

---

## Confirmed-correct items

- **No explicit label leakage into methods.** Every `memory.py` method receives only `s.X`,
  `s.value`, `s.y` (plus `cfg` sizes). None reads `fact_type`, `relations`, or `is_structural`.
  `score_oracle` reads `is_structural` but is the labelled oracle by design. The leak is via metric
  tie-break, not via a method reading labels.
- **Generator value signal does not leak the label** beyond the intended `N(dprime,1)` vs `N(0,1)`
  noisy correlate; `value` is zeroed where `X==0` (test_value_never_reveals_absent covers it).
- **`average_precision` formula is the standard (non-interpolated) AP** — `Σ precision@rank_of_pos /
  n_pos`; correct base-rate/empty handling (returns NaN for n_pos==0). Its *only* defect is the
  tie-break above.
- **`dprime`** pooled-std form is sane; NaN-guards for empty class.
- **Pairing is valid.** `run_per_fact` and `run_relational` both build streams with
  `generate(cfg, seed=s)`; every method in a given call sees the *identical* stream per seed, and the
  two reported paired tests (trained_value−frequency within run_per_fact; relational−item_lifted
  within run_relational) are each computed within one harness call, so they are genuinely paired on
  the same stream. The differing method-RNG offsets (10000+s / 20000+s) only affect `score_random`.
- **Determinism holds; results finite.** trained_value reproduces bit-for-bit across re-generation;
  all logreg weights finite. The `np.errstate(all="ignore")` matmul-warning suppression does not hide
  corruption — outputs verified finite (the `assert np.all(np.isfinite(w))` is real, and probes
  confirm finiteness).
- **`sanity_frequency_matched`** (SF vs DR, matched marginal) ≈ 0 (−0.061) as claimed; `confound_b`
  derivation makes DR's marginal equal `p_present`.

---

## Lower-severity findings

- **`noise_floor` is defined but never wired in** (`stats.noise_floor` has zero call sites outside
  its def). The "minimum detectable effect" guard advertised in the module docstring is not actually
  reported by `run_benchmark.py`. MEDIUM (dead rigor claim).
- **`|t|>3` threshold + uncontrolled multiple comparisons.** `sig` uses a hard `|t|>3` (≈p<0.005 at
  n=30) — defensible as a single threshold, but several paired comparisons are computed with no
  correction and the threshold is arbitrary/undocumented. LOW. Prefer reporting the t/df and a CI, or
  a corrected α.
- **`retention_at_budget` returns 1.0 when `budget >= len(scores)`** — correct, but combined with the
  tie leak the top-K window itself is position-biased (Proof 1). Covered by the fix below.
- **`_summaries` recency `last`** returns −1 for a never-present fact; harmless given every fact
  appears ≥1×, but relies on that invariant.

---

## Minimal fixes

**Fix A (root cause — remove the position/tie leak). Two equivalent options:**

1. *Randomize the layout at generation* (smallest, keeps metrics untouched): in `tasks.generate`,
   after building everything, apply a per-seed permutation to the fact axis of `X`, `value`,
   `fact_type` and remap `relations`. This decouples the contiguous label layout from the sort
   tie-break. Verified: doing so drops `surprise` AP 0.277→0.015 and rare_ret 0.530→0.016.

2. *Make the metrics tie-safe* (more principled — fixes it regardless of layout): in
   `average_precision` and `retention_at_budget`, break ties randomly (pass an rng and add a random
   sort key via `np.lexsort((rng.random(n), -scores))`) or, better, compute **tie-averaged** AP
   (average precision across each equal-score group) so the result is deterministic *and* unbiased.
   Prefer this over option 1 because it also protects budget retention and any future layout.

**Fix B (close the canary gap):** in `check_canaries`, run the permutation canary on **every method
under test** (or add an assertion loop), not just `frequency`. Any method whose permutation AP sits
above chance is leaking — this is what catches Issue #1's constant/tied scorers. Optionally also add
the constant-scorer as an explicit canary method (must sit at chance).

**Fix C (tests):** add a **layout-invariance test** — assert reported AP/retention are unchanged
(within noise) under a random fact-index permutation. None of the current tests exercise tied-score
methods under permutation (`test_permutation_destroys_real_signal` only uses the perfectly-separated
oracle, which has no cross-class ties), which is why this shipped.

**Fix D (minor):** wire `noise_floor` into the report or drop the claim; document/justify the `|t|>3`
threshold and note the number of comparisons.
