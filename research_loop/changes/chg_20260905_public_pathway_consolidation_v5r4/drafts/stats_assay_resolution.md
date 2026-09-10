# PPC5r4 statistics/assay resolution draft

Status: integration draft only. This file has no normative, implementation,
run-lock, dispatch, training, GPU, or scientific-release authority. It proposes
replacement text for a future hash-bound PPC5r4 deliberation; it does not amend
PPC5r3 and must not be consumed as a run contract.

## 1. Source and bounded scope

This draft integrates the exact accepted PPC5r3 consensus resolutions
`PPC5R3_CONS_D03` through `D08` and `D13`, together with the related r3
interpretations, critique dispositions, T05--T11/T13/T14 modifications, and the
existing assay freeze matrix. It changes only the population, sampling,
analysis, D1A controls, D1B gate expansion, status reduction, power, and release
language. Controller, receipt-DAG, visibility, authority, and executable-oracle
repairs remain separate r4 work and are prerequisites to using this draft.

The following r3 concepts are deleted rather than aliased:

- exact sealed recipient-life roster as the inferential population;
- randomized arm-label assignment and the `assignment_rule`;
- finite-roster average ITT as a primary estimand;
- paired label-swap/randomization p-values and the sharp additive null;
- mean-direction/margin release checks and inverted additive-effect grids;
- directionally adverse numeric imputation as the paired primary statistic;
- one unindexed D1B SHAM gate; and
- any D1A safety receipt shaped as a two-arm contrast.

Both computational arms are observed. “Treatment” and “control” below are
contrast orientations, not randomized observed-versus-counterfactual labels.

## 2. Consensus defects that r4 must not silently paper over

The r3 consensus selects the statistical family but does not determine all
executable bytes. These are ratification issues, not implementation defaults:

1. **Clopper--Pearson reporting level and numeric encoding are absent.** D04 and
   D05 require exact one-sided bounds but do not fix their tail error
   probability or serialization. Section 6 proposes a prospectively run-locked
   `cp_tail_alpha` and certified outward-rounded rational brackets. Another
   choice requires explicit adjudication.
2. **IID sampling can conflict with roster-wide donor matching.** D04 requires
   IID life/seed bundles and exact binomial inference, while D08 preserves
   recipient-disjoint, no-reuse, one-to-one donor matching. A global
   without-replacement matching or conditioning on existence of a perfect
   roster match generally makes the paired indicators dependent or
   non-identically distributed. Section 3 requires the versioned generator to
   emit an independently matched donor sub-bundle for each recipient bundle.
   If r4 instead retains global matching, exact binomial inference is not
   justified without a new proof or a different test.
3. **The edge gate registry is not byte-complete.** D07 says “one gate per edge”
   but does not define a stable cross-life edge key or its sample membership.
   Section 5 proposes a pre-entropy `path_template_id/edge_position/edge_id`
   registry. Averaging distinct edge keys would violate D07.
4. **The replacement release bytes do not exist in consensus.** D04 invalidates
   the r3 roster/average-ITT strings and D13 requires a fixed qualification,
   but neither supplies literal successor strings. Section 11 supplies
   proposed exact bytes; they are new r4 content and need ratification.
5. **D05 is grammatically ambiguous about a missing D1A safety trial.** This
   draft reads “counts as the adverse event” separately for each required
   safety endpoint: a missing required provider output sets both safety
   indicators to one. If only one indicator was intended, D1A is not total and
   the choice must be re-adjudicated.

## 3. Replacement generator population and IID sampling contract

### 3.1 Target population

The inferential population is the probability distribution `G`, not the
realized sample. One draw from `G` is one complete pre-treatment
`recipient_life_seed_bundle` containing:

- one recipient-life snapshot before any assay arm is executed;
- every prospectively assigned lower unit for D1A--D1D;
- the locked within-life D1B path-length composition and every registered path
  template needed by that life;
- one common-random seed bundle keyed by assay, stage, call ordinal, and any
  other prospectively registered stochastic operation key;
- a recipient-disjoint D1A donor sub-bundle satisfying section 9; and
- no post-treatment result, endpoint, arm output, model score, or release data.

`G` is identified by `generator_name`, `generator_version`, canonical generator
specification bytes, sampler executable hash, dependency hashes, support
definition, and `generator_hash`. The generator manifest also binds `N`, where
`1 <= N <= 20`, the complete gate registry, the within-life lower-unit registry
and canonical order, the fixed path-length composition, all gate membership,
and the entropy-source contract. Numeric margins, null probabilities, ceilings,
missingness limits, alpha, and `cp_tail_alpha` are later populated run-lock
values, never outcome-derived values.

Every gate membership set `M_g` is a nonempty fixed set of sample ordinals
chosen before any sample entropy is obtained. Membership may not depend on a
generated life, constructability, observed status, missingness, endpoint, or
arm output. `G` must supply every required lower unit for each ordinal in
`M_g`. D1A safety uses all ordinals `0..N-1`. This fixed-membership rule makes
the units used by a gate IID draws from the same `G`; a content-selected or
post-generation stratum is not an implementation-equivalent substitute.

### 3.2 Sampling algorithm

The sampler performs the following once, before any model or training call:

1. Seal the complete generator manifest and populated run lock.
2. For sample ordinals `i = 0,...,N-1`, obtain one 256-bit value `E_i`
   from the locked source whose contract states that its draws are independent
   and uniform. Draws are not conditioned on being unequal; an entropy-value
   collision is retained. Record a source-signed entropy receipt containing source ID,
   source version, ordinal, acquisition time/round, raw-byte commitment, and
   predecessor manifest hash. Receipts audit the declared source and draw;
   they do not convert an untrusted deterministic seed into mathematical
   independence.
3. Compute `B_i = G(E_i, generator_manifest_hash)` exactly once. A generator
   error, malformed bundle, identity-contract failure, unmet required lower unit, or
   failed construction becomes `CONSTRUCTION_FAIL` for the dependent assay or
   run. It is never discarded, redrawn, replaced, or moved to another gate.
4. Seal one self-hashed sample receipt binding ordinal, entropy receipt,
   generator hash, complete pre-treatment bundle hash, snapshot hash,
   lower-unit manifest hash, donor sub-bundle hash, and seed-bundle hash.
5. Instantiate every required arm as a byte-identical clone of the
   assay-specific snapshot. Map arm IDs to clone IDs in canonical arm-ID order;
   there is no random arm-label assignment. Execute all required arms and keep
   every sampled life in its prospective gate membership.

Within a life, corresponding extant stochastic calls use the same seed. A
canonical seed key is the tuple
`(recipient_life_id, assay_id, stage_id, operation_key, call_ordinal)` and must
exclude arm/condition labels. The seed is the big-endian integer represented by
`SHA256("PPC5R4_COMMON_SEED" || 0x00 || canonical(seed_key) || 0x00 || E_i)`.
An absent call consumes no seed and never shifts a later ordinal. Seeds and
life contents from different sample ordinals may share no mutable state.

The `N` complete bundles are the sole independent units. Items, queries,
clones, endpoints, and edges are repeated measures. A single run seed expanded
into all lives, global adaptive rejection sampling, donor swapping across
sampled recipients, or exclusion after seeing any arm is nonconforming.

## 4. Direct paired exceedance estimands

For paired gate `g` and sampled life `i in M_g`, let `A_{iga}` be the arithmetic
mean of the observed endpoint over exactly the prospectively assigned lower
units for arm `a`, in the locked lexicographic order. Each lower unit receives
equal weight inside the life and each life receives one Bernoulli trial. A
clean no-action result contributes observed zero. If any required observation
is genuinely missing, `A` and the paired difference are null for descriptive
magnitude reporting.

Orient every contrast so larger is beneficial and define the direct observed
paired difference:

```text
d_ig = A_ig,treatment - A_ig,control
Z_ig = 1  iff every required arm/lower unit is nonmissing
                and d_ig > margin_g
       0  otherwise
X_g  = sum_{i in M_g} Z_ig
N_g  = |M_g|
pi_g = Pr_G(Z_ig = 1)
```

The primary estimand is `pi_g`, the generator probability that the directly
observed paired benefit strictly exceeds its registered margin with all
required observations present. The primary hypotheses are
`H0_g: pi_g <= pi0_g` versus `H1_g: pi_g > pi0_g`. `pi0_g` and `margin_g` are
gate-specific, prospective, exact run-lock values. Equality `d_ig = margin_g`
is failure (`Z_ig=0`); missing is failure (`Z_ig=0`). There is no arm-label
swap, counterfactual imputation, sharp additive null, or primary mean-effect
test.

The arithmetic mean of complete `d_ig` values, quantiles, magnitude intervals,
and complete-case counts are descriptive only. They cannot create, rescue,
block, or relabel a release.

## 5. Exact gate registry and orientations

The paired gate registry is closed as follows.

| Assay | Gate | Beneficial paired difference |
|---|---|---|
| D1A | `D1A_READER_GT_ADAPTER_OFF` | READER_LORA correct supported selection minus ADAPTER_OFF |
| D1A | `D1A_READER_GT_WRONG_LIFE` | READER_LORA minus prospectively dose/opportunity-matched WRONG_LIFE_ADAPTER |
| D1A | `D1A_READER_GT_BINDING_SHUFFLE` | READER_LORA minus MATCHED_BINDING_SHUFFLED_READER |
| D1C | `D1C_AUTHENTIC_GT_RECENCY` | AUTHENTIC_DREAM_CONTEXT action value minus RECENCY_CONTEXT |
| D1C | `D1C_AUTHENTIC_GT_PERMUTED` | AUTHENTIC_DREAM_CONTEXT action value minus PERMUTED_CONTEXT |
| D1D | `D1D_SELECTION_GT_RECENCY` | DREAM_TO_SLEEP supported selection minus RECENCY_TO_SLEEP |
| D1D | `D1D_SELECTION_GT_PERMUTED` | DREAM_TO_SLEEP supported selection minus HASH_PERMUTED_TO_SLEEP |
| D1D | `D1D_ACTION_GT_RECENCY` | DREAM_TO_SLEEP action value minus RECENCY_TO_SLEEP |
| D1D | `D1D_ACTION_GT_PERMUTED` | DREAM_TO_SLEEP action value minus HASH_PERMUTED_TO_SLEEP |

D1B has two assay-wide timing gates, preserving the r3 orientations:

- `D1B_AUTHENTIC_GT_ONE_SHOT`: AUTHENTIC_PATH action value minus ONE_SHOT_READ;
- `D1B_AUTHENTIC_GT_OPEN_LOOP`: AUTHENTIC_PATH action value minus OPEN_LOOP.

For every presealed edge key
`e = (path_template_id, edge_position, edge_id)` in canonical path-template
then edge-position order, expand three additional gates:

```text
D1B_AUTHENTIC_GT_CUT[e]   : AUTHENTIC_PATH - CUT[e]
D1B_AUTHENTIC_GT_TWIN[e]  : AUTHENTIC_PATH - TWIN[e]
D1B_SHAM_NONINFERIOR[e]   : SHAM[e] - AUTHENTIC_PATH
```

Each edge key binds its own source event, source-preimage hash, CUT ID, TWIN ID,
SHAM ID, intervention receipts, gate membership, margin, and `pi0`. The SHAM
margin is the registered noninferiority margin (normally nonpositive); its
benefit orientation is never reversed. There is no averaging across edge keys,
and no passing edge can rescue another edge. The timing gates retain their
prospectively registered within-life lower-unit aggregation and do not replace
the edge gates.

## 6. Exact binomial p-values, bounds, and ties

All locked probabilities and alpha values are reduced nonnegative integer
rationals `(numerator, denominator)` with positive denominator. Reducers compare
rationals by integer cross multiplication; binary floating point is not an
authority-bearing representation. Require `0 < alpha < 1`,
`0 < cp_tail_alpha < 1`, and every null probability, safety ceiling, and
missingness ceiling in `[0,1]`.

For paired gate `g`, with `pi0_g = a/b`, compute the inclusive upper-tail
p-value

```text
p_g = Pr[Binomial(N_g, pi0_g) >= X_g]
    = sum(k=X_g..N_g) C(N_g,k) a^k (b-a)^(N_g-k) / b^N_g.
```

This is the correct tail for `H0: pi_g <= pi0_g` against `pi_g > pi0_g`; the
supremum over the composite null occurs at `pi0_g`. Counting `X_g` itself in
the tail and putting equality in the null both count ties against release.

Report the exact one-sided Clopper--Pearson lower bound `L_g` at locked tail
error `cp_tail_alpha = gamma`: `L_g=0` if `X_g=0`; otherwise `L_g` is the unique
value in `(0,1]` satisfying
`Pr[Binomial(N_g,L_g) >= X_g] = gamma`. The mathematical bound is defined by
this equation. For canonical bytes, record a certified rational bracket
`[L_lo,L_hi]` at the run-locked decimal scale `s`, where
`L_lo=floor(10^s L_g)/10^s` and `L_hi=ceil(10^s L_g)/10^s` (equal endpoints
when the root is exactly on the grid), and publish the outward conservative
`L_lo`; both independent reducers must prove
`upper_tail(X_g;N_g,L_lo) <= gamma <= upper_tail(X_g;N_g,L_hi)` and produce the
same bracket. The bound is reported and never substitutes for the p-value or
multiplicity reducer.

For all hypothesis tests, `p_value <= threshold` rejects; equality to the
p-value threshold passes. This does not weaken the strict life-level
`d_ig > margin_g` rule or the composite null including `pi_g = pi0_g`.

A paired result receipt contains at least: gate ID and kind; endpoint; ordered
arm roles; generator and membership hashes; `N_g`, `X_g`; exact margin and
`pi0`; missing-failure count; exact p-value numerator/denominator; CP tail
alpha and certified lower-bound bracket; strict comparison rule; and all
source observation hashes. It contains no randomized-assignment or inverted
mean-effect field.

## 7. D1A one-sample safety trials

Each generated life has exactly one D1A primary safety query designated in the
sealed pre-treatment bundle before entropy-dependent arm results. Only the
READER_LORA result for this one query contributes to the two safety gates; no
pooling over other D1A queries is permitted.

For life `i`, define separate indicators on the same designated trial:

```text
F_i = 1 iff READER_LORA returns FOUND but not the registered supported row
Q_i = 1 iff READER_LORA returns NOT_FOUND
```

For an observed valid provider response, `F_i` and `Q_i` are mutually
exclusive. If the required provider output is genuinely missing, set both
`F_i=1` and `Q_i=1` and also mark the life missing for the READER_LORA arm. An
invalid or integrity-failed cell is a blocker, not a safety event.

For safety endpoint `s in {FALSE_SELECTION, NOT_FOUND}`, use all `N` lives,
`X_s=sum_i S_i`, and locked ceiling `c_s`. Test
`H0_s: p_s >= c_s` versus `H1_s: p_s < c_s` with

```text
p_safety = Pr[Binomial(N,c_s) <= X_s]
         = sum(k=0..X_s) C(N,k) c_s^k (1-c_s)^(N-k).
```

The lower tail is correct: smaller adverse-event counts favor safety, and the
supremum over `p_s >= c_s` occurs at the boundary `c_s`. The observed safety
gate also requires `X_s/N < c_s`; equality to the ceiling fails. The inclusive
tail counts `X_s` against release. The p-value enters the D1A maximum-p
conjunction exactly like every paired gate p-value.

Report the one-sided Clopper--Pearson upper bound `U_s` at `gamma`: `U_s=1` if
`X_s=N`; otherwise `U_s` is the unique value satisfying
`Pr[Binomial(N,U_s) <= X_s] = gamma`. Serialize a certified rational bracket
using `floor(10^s U_s)/10^s` and `ceil(10^s U_s)/10^s`, and publish the outward
conservative upper endpoint; certify
`lower_tail(X_s;N,U_lo) >= gamma >= lower_tail(X_s;N,U_hi)`. The
`one_sample_safety_result` has endpoint, generator/sample hashes, `N`, count,
exact ceiling, exact lower-tail p-value, CP upper-bound bracket, observed-rate
direction result, and missingness result. It has no treatment arm, control arm,
paired difference, margin-exceedance indicator, or paired-effect interval.

## 8. Total missing, no-action, and status mapping

The primary reducer uses exactly four mutually exclusive analysis classes:

| Analysis class | Raw condition | Endpoint and continuation | Missing | Blocker |
|---|---|---|---:|---:|
| observed | successful provider/action endpoint | observed value; continue as scheduled | false | false |
| observed no-action failure | integrity-clean assigned path ends without an action | raw and analysis action value `0`; no retry | false | false |
| explicit missing failure | a required model/provider call genuinely returns no output | emit one typed missing observation; raw endpoint may be null; retain any later observed endpoint descriptively, no retry; paired `Z=0` | true | false |
| integrity blocker | preassignment construction/presence failure or post-seal mismatch | no observation enters inference | false | true |

The observed no-action row includes MODEL STOP, BUDGET_EXHAUSTED, ERROR_LIMIT,
TOKEN_LIMIT, PARSE_ERROR, READ_LIMIT, ACTION_LIMIT, INVALID_DOMAIN,
INVALID_REFERENCE, PREDICTION_REQUIRED, PREDICTION_MISMATCH, INVALID_ACTION,
and SCHEDULE_VIOLATION,
and absent or invalid OPEN_LOOP commitment when an output was received but no
valid commitment was produced. Intermediate errors do not create an extra
endpoint: if an action later executes, use its observed action value. A truly
missing model output remains explicit missing even if the same schedule would
otherwise have ended with no action.

Normalize provider absence to the single raw status
`PROVIDER_MISSING_NO_RETRY`. `DREAM_MISSING_NO_RETRY`,
`MODEL_MISSING_NO_RETRY`, and `PROVIDER_MISSING_NO_RETRY` mark every dependent
gate-life missing and force its paired indicator to zero. In D1A's designated
safety trial, provider missing additionally sets both adverse-event indicators
to one as section 7 specifies.

These are nonmissing assigned-policy states. They continue deterministically
and retain actual downstream outcomes and resource dose:

- PUBLISH_EMPTY, VALID_EMPTY, ABSTAIN, and DREAM_INVALID_OUTPUT install the
  contractually specified empty/no view;
- TRAIN_FAILED installs adapter-off;
- `NO_ROOTS_SELECTED` is the aggregate state for an empty selected-root list;
- `NO_ADMITTED_ROOTS` is the aggregate state for a nonempty nominee list with
  zero admitted representatives; and
- mixed nominee projection failures remain per-nominee receipts while the
  aggregate root receipt determines the arm state.

`PROJECTION_REJECTED` is never an arm-level aggregate status. `WRITER_EMPTY` is
not a free alternative spelling for the two root states. If at least one root
was admitted, deterministic failure to render any required row is RUN_INVALID.

Every required artifact is presence/hash/shape checked before assay
assignment. Absence or incompatibility then is CONSTRUCTION_FAIL and no model
dispatch occurs. Disappearance or mismatch after sealing is RUN_INVALID. In
particular, a wrong-life adapter manifest can never become an analyzable
`MISSING` arm outcome. CONSTRUCTION_FAIL and RUN_INVALID produce no observation
and block the dependent assay before inference. Any raw status absent from the
closed assay/arm/stage/endpoint cross-product is RUN_INVALID, never an inferred
default.

For each required arm, missing count is the number of sampled lives with at
least one prospectively required missing observation, denominator all assigned
lives for that arm. The arm passes when `missing_count/N <= missing_limit`;
equality is allowed. Missingness is both a separate gate and, for paired gates,
already an adverse `Z=0`; this is intentional, not double imputation.

## 9. D1A wrong-life matching versus D1D total policy

Before D1A provider-assay assignment, the recipient's authentic adapter and
its dedicated donor adapter must both be present and hash-valid. A donor edge
exists only under exact equality of all of the following prospective fields:

- base, tokenizer, adapter-shape, recipe-family, mount-interface, and rank
  hashes/values;
- row count, total training tokens, and update count;
- ordered per-row token-count vector and ordered per-row byte-class vector;
- candidate-table cardinality;
- eligible equivalence-class count before capacity and after capacity;
- support-multiplicity histogram; and
- row byte-class/token-class histogram.

The opportunity signature is target-blind and excludes recipient identity,
targets, PROBE/future outcomes, scores, action outcomes, and all post-training
performance. Matching is prospective, recipient-disjoint, one-to-one, without
donor reuse, adaptive replacement, or fallback. The generator construction in
section 3 must make each recipient/donor pair an independent unit while the
sealed matching validator recomputes exact equality and unique use. No perfect
match before assignment is CONSTRUCTION_FAIL; post-seal absence or mismatch is
RUN_INVALID.

D1D is categorically different. Its primary DREAM_TO_SLEEP contrasts are total
policy contrasts inclusive of assignment-induced eligible roots, selected and
admitted rows, tokens, updates, training success/failure, publication,
adapter-off continuation, inference, and resources. Do not pad, cross-arm
truncate, dose-match, stratify on, regress on, normalize by, or condition on
any realized mediator. The common prospective capacity and training recipe
remain part of each policy as frozen; no additional truncation may equalize
realized arms. Mediators and resources are reported descriptively only and
cannot rescue or block the primary contrast except through their already
specified policy status or integrity rules.

## 10. Assay composition, Holm, and aligned power

If an assay has no integrity/global/local blocker and every non-p-value gate
passes, its p-value is the maximum exact p-value of every registered gate,
including each expanded D1B edge gate and both D1A safety gates. Otherwise the
assay is BLOCKED and has no substitutable p-value. A mean direction check is
not retained.

Apply Holm to the four assay p-values sorted ascending, with claim ID
lexicographic as the exact tie-break. At ordered position `j=1..4`, reject while
`p_(j) <= alpha/(5-j)`; equality passes. Stop at the first failure. The
intersection releases only if all four assays reject and every global gate
passes; it adds no fifth test.

Power is computed for a sufficient event using the same statistics as release.
For every paired gate, define

```text
k_g = min{x in 0..N_g : upper_tail(x;N_g,pi0_g) <= alpha/4}.
```

If the set is empty, paired-gate power is zero. Otherwise, under the locked
worst-case joint success probability `q_g = Pr_G(d_ig > margin_g and all
required observations present)`, compute
`power_g = Pr[Binomial(N_g,q_g) >= k_g]`. A separate benefit probability and
arm-missing probability are insufficient unless the run lock also fixes their
joint law or a proved conservative lower bound for `q_g`.

For each D1A safety endpoint, define

```text
k_s = max{x in 0..N : lower_tail(x;N,c_s) <= alpha/4 and x/N < c_s}.
```

An empty set gives zero power. Under the locked worst-case adverse-event
probability `r_s`, including missing safety output as adverse, compute
`power_s = Pr[Binomial(N,r_s) <= k_s]`.

For each arm missingness gate with ceiling `lambda_a`, define
`k_a = floor(N*lambda_a)` using exact rational arithmetic and compute
`power_a = Pr[Binomial(N,m_a) <= k_a]` under its locked worst-case per-life
missing probability `m_a`. This gate has no invented hypothesis-test p-value;
its observed reducer is the registered `<=` count rule.

Let `R` contain every paired gate, both safety gates, and every registered arm
missingness gate, expanded per edge and per arm exactly once. The familywise
power lower bound is

```text
power_lower = max(0, 1 - sum_{r in R}(1-power_r)).
```

No independence across gates is assumed. The sufficient event “all paired and
safety p-values are at most alpha/4 and all missingness counts pass” makes each
assay maximum p-value at most alpha/4, which implies all four Holm rejections.
Construction, integrity, fixture, authority, and runtime-validity prerequisites
are deterministic blockers, not probability inputs. The power statement is
therefore conditional on all of them passing; if any is unresolved, the power
receipt is BLOCKED rather than assigning it probability one.

Every power receipt binds the same generator, `N_g`, membership, margin,
`pi0`, ceiling, tail, inclusivity, critical count, missing rule, gate registry,
and rational alpha used by the observed reducer. Boundary fixtures must cover
counts immediately below, at, and above every critical count.

## 11. Proposed literal release and overlap bytes

These are proposed exact r4 strings. They replace, rather than supplement, the
invalid r3 finite-roster/average-ITT strings after ratification.

`PPC5_D1A_SUPPORTED_SELECTION`

> Under the locked PPC5 recipient-life/seed generator G and complete-table provider assay, each registered paired READER_LORA supported-selection benefit strictly exceeded its margin with probability above its registered pi0 under G: the comparisons with the identical ADAPTER_OFF provider, the prospectively dose-and-opportunity-matched WRONG_LIFE_ADAPTER, and MATCHED_BINDING_SHUFFLED_READER all passed; the one-sample false-selection and NOT_FOUND safety gates also passed. This is candidate-conditioned selection with external semantic support, not closed-book storage or autonomous recall.

`PPC5_D1B_OBSERVABLE_EDGE_DEPENDENCE`

> Under the locked PPC5 recipient-life/seed generator G and presealed decisive-path benchmark, every registered paired AUTHENTIC_PATH benefit over its edge-specific CUT and TWIN strictly exceeded its margin with probability above its registered pi0 under G, every edge-specific SHAM-minus-AUTHENTIC noninferiority contrast did likewise, and the AUTHENTIC_PATH benefits over ONE_SHOT_READ and OPEN_LOOP did likewise. This is observable behavioral dependence on every separately tested interleaved edge response and does not reveal private cognition.

`PPC5_D1C_DREAM_CONTEXT_POLICY`

> Under the locked PPC5 recipient-life/seed generator G and benchmark, the paired AUTHENTIC_DREAM_CONTEXT benefit over each of RECENCY_CONTEXT and PERMUTED_CONTEXT strictly exceeded its registered margin with probability above its registered pi0 under G, inclusive of selected cardinality, order, focus, prompt-token, and failure or abstention consequences. This is a total context-policy result, not a pure context-content result.

`PPC5_D1D_DREAM_TO_SLEEP_TOTAL_POLICY`

> Under the locked PPC5 recipient-life/seed generator G and benchmark, each registered paired DREAM_TO_SLEEP benefit over RECENCY_TO_SLEEP and HASH_PERMUTED_TO_SLEEP, for supported candidate selection and normalized downstream action, strictly exceeded its margin with probability above its registered pi0 under G. This is an unadjusted total-policy result inclusive of assignment-induced evidence dose, training, publication, inference, failure, and resource differences, not a fixed-dose root-quality result.

`PPC5_NONMEDIATIONAL_FOUR_ASSAY_INTERSECTION`

> All four separately identified PPC5 assays passed under the locked recipient-life/seed generator G: supported candidate selection, observable every-edge interleaved-response dependence, frozen DREAM context-policy value, and DREAM_TO_SLEEP total-policy value. This is a non-mediational four-assay intersection, not an end-to-end learning mechanism.

Attach this exact fixed qualification to every released component, intersection,
and export package in a separate immutable `qualification_text` field:

> This result is confined to the locked generator and target-informed constructed benchmark. The attached overlap manifest reports the presealed ACQUIRE/PROBE, alias-family, item-family, semantic-family, and cross-donor overlap counts and strata. Those strata are descriptive and neither rescue nor block release. This result makes no claim of novelty, zero-overlap generalization, or naturalistic path structure.

Every release/export receipt must bind non-null
`overlap_manifest_hash` and `construction_scope_receipt_hash`, the exact
component or intersection text, the exact fixed qualification, and the full r3
forbidden-claim list. A missing, stale, or mismatched receipt hash is an
integrity/release blocker; the numerical overlap values themselves never change
pass logic. The release reducer emits no paraphrase, alias, truncation, merged
headline, finite-roster average-effect wording, or mechanism claim.

The forbidden-claim list remains exactly:

- closed-book storage;
- autonomous recall;
- learned THINK;
- learned DREAM;
- continual improvement;
- schema compression;
- lifetime scaling;
- flywheel;
- parenting;
- population learning; and
- cultural inheritance.

## 12. Required schema/fixture consequences

A conforming successor must add closed, self-hashed objects for the generator
manifest, each life/entropy sample, paired exceedance result, one-sample safety
result, missingness result, power gate/family result, edge gate registry, and
overlap/construction-qualified release. Role-labeled hashes and exact
cardinality/order replace generic hash arrays.

T05 must cover one designated safety trial per life, both event mappings,
missing-as-adverse, both exact lower tails, strict ceiling equality failure, and
upper-bound edge cases. T06 must prove the complete D1A matching signature and
IID-compatible donor construction while proving no D1D adjustment. T07/T08
must enumerate all edge-key CUT/TWIN/SHAM mappings and gates. T11 must calibrate
all status rows, strict margin ties, inclusive binomial tails, exact rational
p-values, CP endpoint cases, assay maxima, Holm ties, and critical counts in two
independent reducers. T13 must bind `G` and every entropy/life receipt. T14 must
replay all sampled lives without exclusion and reject old average-ITT or
unqualified release bytes.

Nothing in this draft makes those tests pass or grants authority to implement
or execute them.
