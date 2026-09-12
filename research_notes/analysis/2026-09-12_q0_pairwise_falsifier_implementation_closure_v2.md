# Q0 pairwise falsifier: implementation closure v2

**Date:** 2026-09-12  
**Status:** final watcher-side implementation handoff; no builder source, model,
GPU process, or run artifact was changed.  
**Primary contract:**
`2026-09-12_pairwise_binding_falsifier_adjudication.md`.  
**Fresh independent reviews:**
`2026-09-12_q0_claim_bearing_implementation_preflight.md` and
`2026-09-12_q0_pairwise_falsifier_mathematical_redteam.md`.

## Decision

The one-root complementary XOR target is implementable and is still the next
claim-bearing writer experiment. Keep the original material, objectives,
quartet schedule, dose, P_AUTH/P_DERANGED qualification gates, locality
families, claim boundary, and 0.75 A40-hour ceiling. Apply the amendments below
as binding precedence where the three source memos differ.

Build a new executor and focused tests. Do not edit the source-hash-pinned
archived Q0, SEQ-089, or gateway executors. The current public-ID-contaminated
Level-1 run is a disposable exploratory diagnostic and cannot select any Q0
knob or release Q0.

## Binding amendments

### 1. The common prefix is a token identity, not a string assumption

For every exact, held, and locality prompt, independently encode both complete
legal continuations and derive their maximal common token prefix `x`. Require:

```text
candidate_0[:k] == candidate_1[:k] == x
candidate_0[k] != candidate_1[k]
decode(x) ends in the declared natural assistant text "ACT: -"
tokenize(the rendered conversation ending at that text) == x
```

The same two divergent branch IDs must occur at the same decision position on
every item. The training and likelihood forward receives exactly `x` and no
later assistant token, target-shaped label/mask, padding, suffix, LF, or EOS.

The frozen user instruction already names both legal actions, so the previous
literal statement that no branch token occurs anywhere in the input is
impossible. The binding prohibition applies to the appended assistant span
after the recorded assistant boundary. Record user and assistant spans and
leave the symmetric frozen user prompt unchanged.

Define every pairing and schedule hash over target-free coordinates only:

```text
(root, tool, mode, template, decision_prefix_hash)
```

AUTH/DERANGED/V/unary must have byte-identical quartet order where compared.
Require disjoint decision-prefix hashes across exact, held, each locality
family, wrong-root, and copy panels except the intended identical prompts
across fitted maps.

### 2. A finite zero pairwise gradient is a scientific tangent result

Missing/disconnected gradients, nonfinite tensors, wrong trainable inventory,
mutated state, or failed cleanup remain nonreportable integrity aborts. A
present, finite pairwise gradient at or below the registered numerical floor
is instead reportable:

```text
ZERO_XOR_TANGENT_AT_INIT
```

Record `norm_P`, `norm_V`, and `norm(V-P)`. Cosine is undefined when either
norm is below the floor; store `null` and take the explicit zero-norm branch.
Do not manufacture a cosine with an epsilon denominator. If P is zero and V
is nonzero, the objective contrast is nondegenerate but the pairwise tangent
is a reportable null. If both are zero, do not run V as a rescue.

The zero-update worker and every later fit must share the same ordered initial
LoRA tensor digest and step-zero logits digest; a seed name alone is
insufficient.

### 3. Directional canaries use analytic error floors

Let `delta = theta_after - theta_before`. Keep LoRA dropout `.05`; the canary
therefore tests the actual registered dropout-active first update against the
dropout-off evaluation function. A miss rejects this exact
seed/quartet/dropout path and is not a claim that every deterministic pairwise
tangent fails.

For each signed dropout-off diagnostic gradient
`h_i = s_i * grad(d_i)` and actual FP32 parameter delta `u`, cast operands to
FP64 before multiplying and compute:

```text
dot_i     = sum_j float64(h_ij) * float64(u_j)
abs_sum_i = sum_j abs(float64(h_ij) * float64(u_j))
```

Gate `dot_i` above a prospectively implemented FP64 summation error bound
`safety * gamma_(n-1) * abs_sum_i`, not merely above zero. Record the bound,
`dot_i`, `abs_sum_i`, and their ratio. Recompute the two output-head products
for each before/after margin in FP64 and require the signed improvement above
its analogous dot-product error bound.

Name the two numerical surfaces separately:

- `z_train32`: BF16 forward logits cast to FP32, used for the registered P/V
  training loss; and
- `d_canary64`: FP64 hidden-state/output-head recomputation, used consistently
  for canary gradients, projections, and before/after gates.

Define the stored Gram matrix as
`G_ij=<s_i grad(d_i), s_j grad(d_j)>` with the same FP64 multiplication and
reduction. Its approximate positive semidefiniteness is an implementation
check; it cannot replace the four directional predicates.

### 4. Locality and identity use closed enums and integer gates

Define generated identity before results as:

```text
MEM2REG | GVN | OTHER_SINGLE(exact string) | INVALID | MULTIPLE
```

`A` means exactly one of MEM2REG/GVN. Record every OFF->ON enum transition.
Encode the `.05` discrete gates as literal counts:

- missing-mode `n=8`: zero A or identity changes;
- unsupported-mode `n=8`: zero;
- neighbor-ID `n=16`: zero;
- wrong-root `n=64`: at most three; and
- mutually opposite AUTH/DERANGED wrong-root outputs: at most three of 64.

Keep the separate itemwise `q` and absolute legal branch-token mass `M`
means `<=.05` and tails `<=.10`. These establish registered branch-choice,
branch-mass, generation, and interface locality—not global distributional
locality.

### 5. Optional arms cannot veto the primary P qualification

Only OFF, P_AUTH, and P_DERANGED enter the primary XOR qualification. Apply
all copy/interface/locality gates to both P states. Evaluate V_AUTH or
P_UNARY_TOOL on identical panels, but their failures affect only their
registered diagnostic qualifier. Merely running an optional diagnostic cannot
turn an otherwise passing P conjunction into a primary failure.

If V_AUTH misses its first-update canary, preserve the update, do not retry,
and attach:

```text
EARLY_V_AUTH_QUARTET_STOP
OBJECTIVE_CONTRAST_AMBIGUOUS
```

The primary P label is unchanged.

### 6. Early AUTH failure still receives one DERANGED diagnostic step

Use this fixed lifecycle, still within three attempted fits:

1. CPU/native material seal and no-update objective audit.
2. Contemporary OFF and mandatory 8/8 copy check.
3. Start P_AUTH. If its first quartet passes, continue uninterrupted through
   update 128 and evaluate.
4. If AUTH passes its canary, run P_DERANGED normally. If AUTH misses, stop it
   after update 1 and run exactly the registered DERANGED first-quartet canary
   step, then stop DERANGED regardless because qualification is impossible.
5. In the early-XOR-failure branch, the third and final attempt may be
   P_UNARY_TOOL under its fixed canary. Do not run V.
6. If both P canaries pass, complete both. Run V_AUTH iff the pre-fit audit
   found a nondegenerate P/V contrast. If the contrast is degenerate and an
   exact P acquisition gate later fails, use the third attempt for unary;
   otherwise stop at two fits.

This distinguishes `FIRST_STEP_MAP_ASYMMETRY` from
`BOTH_MAP_FIRST_STEP_MISS` without allowing a complementary-map failure to
qualify the writer. No fourth fit, alternate seed/quartet/rank/rate, pause,
resume, checkpoint selection, or retry is allowed.

## Concrete builder handoff

Create at minimum:

```text
gpu/astra_pairwise_q0.py
tests/test_astra_pairwise_q0.py
```

Reuse frozen root-1 material, render/model/process-custody helpers, strict
generation, canonical hashing, and clean-base/adapter inventory checks. Do not
reuse the old row-wise trainer, native `output.loss`, unequal-shape BF16
candidate scorer, old reducer, Level-1 corpus, or a fitted adapter.

The new executor must implement:

- target-free maximal-token-prefix materialization and the 32 frozen XOR
  quartets repeated four times;
- explicit P/V FP32 losses from natural-prefix logits;
- no-update gradient audit with the zero-gradient branch above;
- uninterrupted quartet training, snapshots at 32/64/128, and analytic
  first-update canaries;
- one contemporary OFF, strict exact/held generation, natural-prefix q/M,
  four locality panels, eight-copy panel, and fixed denominators;
- a pure reducer reconstructing all material and enforcing the original
  noncompensatory thresholds plus the amendments above; and
- terminal integrity/science labels, run accounting, immutable raw records,
  replay, cleanup, and verified GPU release.

Before launch, run the focused Linux suite plus untouched archived regression
suites. Tests must cover token-boundary mutations, target-dependent schedule
hashes, zero/near-zero gradients, FP64 error-bound equality and adjacent
failure, all four canary cheap-policy failures, RNG/state mutation, exact
snapshot/update counts, every reducer boundary, optional-arm non-veto, every
early-stop branch, and sealed replay. The earlier macOS failures from `/var`
symlink policy and missing GNU `timeout` are not an admissible Linux result.

## Claim and next action

A full pass establishes only that one deterministic rank-8 recipe installs
and extracts complementary finite `(opaque tool, mode)->action` bindings on
one supplied root under the registered locality surface. A lookup table can
pass by design. It is not connected/compressed knowledge, child experience,
DREAM/SLEEP, parenting, root robustness, H1/H2, or lifetime improvement.

Only a full P_AUTH+P_DERANGED pass releases the repaired Level-1 material.
The clean equal-memory-dose replay successor remains a parallel L0 safety
question; it does not outrank Q0.
