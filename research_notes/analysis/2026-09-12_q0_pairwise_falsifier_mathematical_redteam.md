# Fresh mathematical red-team: adjudicated Q0 pairwise-binding falsifier

**Date:** 2026-09-12  
**Scope:** independent mathematical and protocol audit only. I did not edit
builder code, run a tokenizer/model, or launch/alter GPU work.  
**Primary object:**
`2026-09-12_pairwise_binding_falsifier_adjudication.md` at the repository
state named in the commit containing this memo.

## Verdict

**The bounded scientific target is sound, but the contract needs four small
repairs before implementation can be called decisive.** The pairwise loss is
correct; complete XOR quartets eliminate constant-, mode-, tool-, template-,
and root-only policies as passing explanations; the complementary AUTH and
DERANGED fits plus held strict generation make the final qualification much
stronger than another carrier or global-habit test. A finite lookup table over
the eight opaque tools and two modes can pass, but that is the intended
one-root conditional-writer primitive, not a shortcut around its bounded
claim.

The four required repairs are:

1. make the decision prefix and schedule identity token-level and strictly
   target-independent;
2. treat a finite zero/near-zero XOR gradient as a scientific result, not an
   integrity abort;
3. put analytic numerical floors under both first-step directional predicates
   and make the dropout-qualified interpretation exact; and
4. define the small-denominator locality counts and action-identity sentinel
   explicitly.

One optional but high-information stop-rule repair is also recommended: if
the first AUTH quartet misses, spend one already-registered DERANGED canary
step before the unary diagnostic. That distinguishes a map-specific first-step
basin from a symmetric XOR-tangent failure without adding a fourth fit or a
full failed fit.

With these amendments, a pass supports exactly the adjudicated label:
supervised complementary arbitrary tool-by-mode binding on one finite root,
with held wording extraction and registered decision/interface locality. It
still does not support connected knowledge, compression, experiential SLEEP,
parenting, root/seed robustness, or the paper's lifetime claim.

## 1. Pairwise objective: algebra is correct

Let

```text
d = z_mem2reg - z_gvn
s = +1 for mem2reg, -1 for gvn
L_P = softplus(-s*d)
L_V = logsumexp(z) - z_target
M = p(mem2reg) + p(gvn).
```

Then

```text
L_P = -log(p_target / M)
L_V - L_P = -log(M).
```

So `P` contains exactly the within-pair branch-choice pressure, while `V`
adds pressure to move probability mass from the rest of the vocabulary into
the two branch tokens. The proposed `R` and cosine audit therefore asks a
well-defined question. It does **not** compare two sources of binding
information: both see the same binding labels, and their only objective
difference is legal-branch-mass normalization.

The sign in the canary is also correct if and only if
`delta_theta = theta_after - theta_before`:

```text
s * <grad_theta d, delta_theta> > 0
```

is the first-order condition that the signed margin improved. The
implementation receipt must state this delta convention; reversing the
subtraction silently reverses every conclusion.

Balanced labels prevent a constant action rule from *passing* but do not make
its gradient vanish. The adjudication already corrects this point and should
retain that wording.

## 2. The common-prefix definition needs one exact token-level assertion

The archived native response IDs indicate the intended boundary is real:
both actions share the three response tokens for `ACT: -`, then diverge at
the recorded branch IDs. But byte/text prefixing is not generally equivalent
to tokenizer prefixing because BPE tokenization can merge across a string
boundary.

For every exact, held, and locality item, preparation should derive—not
assume—the maximal common **token** prefix `x` of the two complete candidate
encodings and require all of:

```text
candidate_0_ids[:k] == candidate_1_ids[:k] == x
candidate_0_ids[k] != candidate_1_ids[k]
decode(x) ends in the declared natural "ACT: -" prefix
tokenize(the complete rendered conversation ending at prefix_text) == x
```

It should also require the two divergent IDs to be the same registered pair
on every item and prove that forwarding `x` alone is the operation used by
both training objectives. No branch token, suffix, LF, EOS, pad, or
target-shaped tensor may enter that forward.

The schedule hash needs the same repair in wording. The digest currently says
it consumes four “source-row hashes.” If those hashes include the AUTH target,
then target complementation can change the DERANGED order. Define the schedule
identity over a target-free tuple such as

```text
(root, tool, mode, template, decision_prefix_hash)
```

and require byte-identical quartet order for AUTH, DERANGED, V, and unary
where applicable. The map and target may appear in result provenance, but not
in pair selection, canary selection, or schedule construction.

Finally, assert disjoint decision-prefix hashes between exact, held, each
locality family, wrong-root, and copy panels except where prompt identity is
deliberately shared across fitted maps. This makes every fixed denominator
auditable and prevents one prompt from serving two nominally independent
families.

## 3. Quartet construction really excludes the advertised cheap policies

For paired tools with orientations zero and one, a quartet contains

```text
orientation 0:  m0 -> 0, m1 -> 1
orientation 1:  m0 -> 1, m1 -> 0.
```

Within every optimizer update, action, mode, orientation, and tool counts are
balanced. Therefore:

- a constant action is correct on `2/4`;
- a mode-only rule is correct on `2/4`;
- a tool/orientation-only rule is correct on `2/4`;
- a template-only or root-only rule is correct on `2/4`; and
- a prompt-independent logit shift cannot make all four signed first-step
  margins increase.

The same ceilings are `64/128` exact and `32/64` held on the full balanced
surface. They are far below `116/128` and `52/64`. An additive logit model
`b_tool + c_mode` also cannot realize the XOR: the orientation-zero pair
requires `c_1 > c_0`, while the orientation-one pair requires `c_0 > c_1`.

The complementary-map double-correct gates further exclude a fixed policy
shared by both adapters. A whole-prompt or `(tool,mode)` lookup table can pass;
that is not evidence of compositional or connected knowledge, but it is valid
evidence that this LoRA writer can store and retrieve the finite conditional
map. The claim boundary already says this and must remain attached to every
result.

For scale only—not as an IID p-value—the fair-coin upper tails are about
`7.76e-23` for `>=116/128` and `2.28e-7` for `>=52/64`. The forms are
correlated within sixteen keys and one root, so these numbers must not be used
as inferential significance. The independent generalization unit is at most
the opaque tool/key, not each paraphrase.

## 4. Finite zero gradients are a reportable negative

The precheck currently makes “zero `g_P`” a nonreportable abort. That is
mathematically wrong for this falsifier. A present, finite, correctly computed
zero pairwise gradient from a balanced XOR quartet is exactly a possible
scientific outcome: at this initialization and LoRA tangent, the conditional
directions cancel.

Separate these cases:

- missing gradient, disconnected graph, nonfinite tensor, wrong parameter
  inventory, or failed source/input receipt -> nonreportable integrity abort;
- present finite `g_P` whose norm is at or below a registered numerical floor
  -> reportable `ZERO_XOR_TANGENT_AT_INIT` for that quartet/path;
- nonzero `g_P` -> compute `R` and cosine normally.

Cosine is undefined when either norm is effectively zero. Do not manufacture
it with an epsilon denominator and then classify it as ordinary degeneracy.
Record `(norm_P, norm_V, norm_difference)` and use an explicit zero-norm
branch. If `P` is zero and `V` is not, the objectives are nondegenerate but
the mandatory P canary is already scientifically disfavored. If both are
zero, no vocabulary fit can rescue the local tangent.

The no-update audit worker must also have the exact same ordered initial LoRA
tensor digest and step-zero logits digest as every later fit. “Same seed” is
not enough for an audit that assigns the optional third fit.

## 5. The canary needs numerical floors, not merely `> 0`

The adjudication correctly rejects a repeated-forward empirical epsilon.
Bit-identical forwards only prove determinism; they do not make an arbitrarily
small positive dot product or one-ULP recomputed margin scientifically
directional.

For each stored FP32 diagnostic gradient `h_i = s_i grad(d_i)` and FP32
parameter delta `u`, compute

```text
dot_i = sum_j float64(h_ij) * float64(u_j)
abs_sum_i = sum_j abs(float64(h_ij) * float64(u_j)).
```

The cast must happen **before multiplication**, not only before the reduction.
Require `dot_i` to exceed a prospective floating-point accumulation bound,
for example `gamma_(n-1) * abs_sum_i` with a fixed safety multiplier, rather
than merely exceed zero. Store the bound and ratio `dot_i / abs_sum_i`.

For the observed before/after margin, recompute the two output-head products
from the recorded hidden states and head rows in FP64 (the operation is tiny:
four prompts by two rows), store native BF16/FP32 logits separately, and gate
the signed difference only above its analogous two-dot error bound. This is
the analytic version of the numerical safeguard the red-team intended.

There is also an interpretation issue from LoRA dropout `.05`. The diagnostic
`grad(d)` is computed dropout-off, while the actual update is produced by one
dropout-active quartet. That is a valid test of whether the *actual sampled
update* improves the deterministic evaluation function, but a miss does not
show that the deterministic pairwise objective lacks a conditional tangent.
It only rejects this exact seed/quartet/dropout update path.

Use one of two clean contracts, chosen before execution:

1. retain dropout `.05`, keep the existing dual predicates, and label a miss
   `REGISTERED_FIRST_QUARTET_UPDATE_MISS` rather than a general local-gradient
   failure; or
2. set LoRA dropout to zero in every Q0 fit and audit so the diagnostic and
   update functions coincide.

The first is the minimal change and preserves the intended writer recipe.
The second gives a cleaner deterministic tangent assay but changes that
recipe. Do not silently mix the interpretations.

The signed Gram matrix should be defined explicitly as

```text
G_ij = <s_i grad(d_i), s_j grad(d_j)>
```

using the same ordered trainable inventory and FP64 multiply/reduction rule.
It is diagnostic; positive semidefiniteness within a registered numerical
tolerance is a useful implementation check, not a qualification gate.

## 6. Exact and held gates are strong but not statistical replications

The corrected integer thresholds are internally consistent:

- exact: `116/128`, recalls `56/64` each, validity `122/128`, fourteen of
  sixteen key-mode cells at `>=7/8`, and complementary double-correct
  `112/128`;
- held: `52/64`, recalls `24/32` each, validity `61/64`, twelve of sixteen
  key-mode cells with positive median signed margin, and complementary
  double-correct `48/64`.

These are fixed-surface engineering gates. The 128 and 64 rows are repeated
wordings over only sixteen `(tool,mode)` cells and eight tools, not 192 IID
samples. Report raw counts and per-tool/key distributions; do not attach a
binomial confidence interval over prompt forms or call one root robust.

For an even number of held forms per key, define the median convention
explicitly (the arithmetic mean of the two central ordered values is the
usual choice). Otherwise two implementations can disagree at the zero
boundary.

## 7. Locality algebra is useful; its discrete rules need exact definitions

The pair `(q,M)` reconstructs both registered branch-token probabilities:

```text
p_mem2reg = q*M
p_gvn = (1-q)*M.
```

Gating both therefore closes the normalized-binary-TV loophole that affected
earlier work. It does not constrain arbitrary redistribution among all other
vocabulary tokens. Consequently the pass claim should say **registered
branch-choice, legal-mass, generation, and interface locality**, not global
distributional locality. A broader claim would require a full-vocabulary
divergence or larger unrelated-behavior panel.

Define strict action identity over a closed enum, for example

```text
{MEM2REG, GVN, OTHER_SINGLE(exact_action), INVALID, MULTIPLE}
```

before computing `I`. Otherwise “identity differs” is undefined when OFF or
ON is invalid or emits a third native action. `A` should remain the indicator
for exactly one of the two registered legal branches; report every transition
between enum values.

The `.05` discrete gates imply exact counts that should be encoded directly:

- for `n=8` and `n=16`, `mean |A_ON-A_OFF| <= .05` permits **zero** status
  changes, and the same is true for `I`;
- for `n=64`, it permits at most **three** changes;
- the wrong-root mutually-opposite fraction `.05` likewise permits at most
  **three of 64**.

State those integers in the contract and test equality boundaries. Do not
round a displayed decimal and then compare it. Retain the per-item `.10`
tails for `q` and `M` and compute all means as itemwise absolute differences,
never the absolute value of a signed mean.

## 8. Multiple-fit release logic: one cheap improvement

Serial uninterrupted workers are the right lifecycle. The optional V fit
should remain an objective diagnostic only when the initialization contrast
is nondegenerate; its outcome cannot replace the complementary P pair.

The only information-efficiency weakness is the rule “AUTH canary miss -> do
not launch DERANGED.” Since AUTH and DERANGED are exact complements and base
alignment is a known nuisance, one AUTH first-step miss is not enough to know
whether the reverse map has the same tangent failure. The cheapest more
decisive rule is:

1. if AUTH passes, continue it uninterrupted as written, then attempt
   DERANGED;
2. if AUTH misses after one step, seal it, then run exactly the registered
   first DERANGED canary step but do not complete DERANGED because
   qualification is already impossible;
3. use the remaining third fit for unary when allowed by the predeclared
   objective/diagnostic rule.

This stays within three attempted fits and adds only one optimizer update in
the early-failure branch. It distinguishes `BOTH_MAP_FIRST_STEP_MISS` from
`FIRST_STEP_MAP_ASYMMETRY`. Neither qualifies the writer, but the distinction
changes the next representation diagnosis.

The V/P degeneracy rule is conservative rather than invalid: declaring a
contrast nondegenerate when even one row/quartet crosses a threshold may spend
an unnecessary V fit, but cannot create a false writer pass. Record the
distribution and aggregate full-schedule gradient in addition to the
all-row/all-quartet Boolean so the efficiency decision can be explained.

## 9. Final shortcut audit and minimal disposition

The following cannot pass the full conjunction:

| strategy | ceiling/reason |
|---|---|
| constant action | `64/128` exact, one recall zero |
| mode only | `64/128`; opposite orientations cancel within every quartet |
| tool/orientation only | `64/128`; modes cancel within every tool |
| template/root only | `64/128`; labels balanced within those features |
| emit both actions | zero-multiple-actions rule |
| teacher-forced branch only | strict unprefilled generation remains mandatory |
| one lucky map | complementary AUTH/DERANGED qualification is noncompensatory |
| broad wrong-root policy | per-family `q`, `M`, `A`, `I`, and opposite-map gates |

A finite keyed lookup table plus a wording normalizer can pass. That is the
primitive being tested. Therefore the decisive interpretation is:

> On one frozen root and initialization, this supervised LoRA recipe can or
> cannot install a finite complementary `(opaque tool, mode) -> action` table
> that survives held wording and does not measurably redirect the registered
> local scope/interface panels.

Do not use Q0 itself as evidence for connections, compression, traversal,
expansion, recurrence, or lifetime learning. A pass only releases the already
ordered Level-1 and exact W-H1 gates; it does not shorten them.

## Minimal pre-launch amendment list

1. Bind maximal token-prefix/concatenation identity and target-free schedule
   hashes; assert panel prefix disjointness.
2. Replace finite-zero-gradient integrity aborts with reportable tangent-null
   labels and define zero-norm cosine handling.
3. Bind the audit initialization to the fit initialization.
4. Compute FP64 products and reductions with prospective error bounds for
   projection and observed-margin gates; define the dropout interpretation.
5. Define signed Gram algebra, held-median convention, strict action enum, and
   integer locality limits.
6. Prefer the one-step DERANGED diagnostic after an AUTH canary miss.

No new root, rank, rate, training dose, paraphrase arm, fourth fit, or broader
claim is needed.

## Evidence read

- `research_notes/analysis/2026-09-12_pairwise_binding_falsifier_adjudication.md`
- `research_notes/analysis/2026-09-12_pairbalanced_common_prefix_falsifier_scientific_redteam.md`
- `research_notes/analysis/2026-09-12_binding_writer_gate_priority_decision.md`
- `research_notes/analysis/2026-09-12_binding_writer_failure_diagnosis_and_minimal_falsifier.md`
- `research_notes/analysis/2026-09-12_pairwise_writer_path_fresh_audit.md`
- `research_notes/analysis/2026-09-12_semantic_w0_writer_terminal_independent_audit.md`
- `research_loop/COORDINATION.md` through the Q0 adjudication and subsequent
  L0/memory/Level-1 preparation entries visible at review time.
