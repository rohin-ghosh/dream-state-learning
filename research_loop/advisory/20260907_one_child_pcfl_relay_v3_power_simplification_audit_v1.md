# One-child PCFL relay v3: power-simplification audit v1

Date: 2026-09-07

Status: **independent source-only advisory; no authorization**. This document
does not amend note 59 or the incorporated B9--B10 lock, ratify an
architecture, implement code, select/generate a child or root, run a pilot,
call a model/tokenizer, build an adapter, use a GPU, or authorize a claim. It
answers one narrow question: can the exact `TEXT_chain_r`, `LORA_chain_r`, and
`COMPLETE_chain_r` endpoints and their safety/causal content be preserved
without requiring a 75-endpoint all-pass power family and a 32-root
rank-copula pilot?

## Verdict

**YES, with a prospective change to the inferential hierarchy.** There are two
scientifically honest replacements:

1. **Recommended paper-efficient design — three chain-primary decisions,
   fixed `N=112`.** Preserve the three chain definitions byte-for-byte. Treat
   their root-level conjunctions as the primary scientific estimands. This
   preserves every mediator, cut, twin, sham, leakage, reacquisition, writer,
   read, and same-semantics condition *inside the observed end-to-end claim*.
   It does not separately certify the old population thresholds for all 72
   constituent endpoints. At the registered chain alternatives, exact
   binomial enumeration gives each chain at least `.924` marginal power and an
   arbitrary-dependence union-bound power guarantee of `.8087` for passing all
   three.
2. **Full numerical-certification design — eight decisions, fixed `N=192`.**
   Add five preregistered joint guardrail endpoints to the unchanged three
   chains. The joint endpoints imply every old primitive floor/ceiling and
   every paired `.20` SESOI by deterministic dominance. At newly explicit,
   logically coherent joint planning alternatives, exact enumeration gives an
   arbitrary-dependence all-eight power guarantee of `.8483`. This retains the
   literal old population requirements while reducing 75 decisions to eight.

The current 75-decision fixed sequence is already Type-I valid as an
intersection--union test (IUT). Its large sample-size machinery is not needed
for validity; it is needed only to guarantee at least `.80` probability that
**all 75** decisions pass at once. That is a distinct and much stronger
assurance objective than demonstrating an end-to-end relay.

The 32-root rank-copula pilot should be deleted from either replacement. It
cannot safely reduce `N` because the analytic union bound remains binding. It
therefore buys no inferential efficiency, while adding 32 expensive roots and
a high-dimensional dependence model whose uncertainty is not covered by the
200,000-simulation Monte Carlo interval.

## 1. What cannot be obtained for free

No multiplicity trick can preserve all of the following simultaneously while
also promising a much smaller `N`:

- 75 separately thresholded population statements;
- at least `.80` probability that every statement passes;
- the existing marginal planning alternatives; and
- arbitrary, unknown within-root dependence.

The existing `sum_j beta_j <= .20` condition is a correct least-favorable
union-bound guarantee for that literal assurance target. Fixed sequencing and
IUT logic protect Type I error but do not make the joint power failures
disappear. A smaller design must explicitly do at least one of: reduce the
primary claim family, replace marginal claims with joint root-level
estimands, accept less than `.80` all-endpoint assurance, or assume a
dependence model. The recommended replacements reduce/re-express the claim
family; they do not hide an assumption.

## 2. Recommended lean design: the three chains are the claims

Keep Section 10's root variables and failure law exactly:

```text
TEXT_chain_r
LORA_chain_r
COMPLETE_chain_r = TEXT_chain_r * LORA_chain_r
```

Every randomized root stays in every opened denominator and every scientific
failure remains adverse-filled before a chain is constructed. No component
average can manufacture a chain success. Because each chain is a same-root
conjunction, a lower confidence bound on its rate directly supports the
statement that a nontrivial fraction of roots completed **all** registered
conditions simultaneously. This is closer to B9's scientific demand than 72
disconnected marginal successes.

Use one compound confirmatory claim:

```text
H_TEXT:     P(TEXT_chain_r=1)     > .60
H_LORA:     P(LORA_chain_r=1)     > .50
H_COMPLETE: P(COMPLETE_chain_r=1) > .40
```

Test each with the existing one-sided `.05` Clopper--Pearson lower bound. The
compound claim is an IUT: it is released only if all three pass, so no alpha
split is required. Text executes first; failure stops LoRA spending. If text
passes, LoRA runs on all registered roots, including text failures. The three
carrier-specific estimates remain separately visible; `COMPLETE_chain` is
still the same-root product, never the product/minimum of aggregate rates.

At `N=112`, the exact critical counts and planning powers are:

| endpoint | pass count | lower bound at critical count | alternative | exact power |
|---|---:|---:|---:|---:|
| `TEXT_chain` | at least 77/112 | `.6078059092` | `.75` | `.946368580` |
| `LORA_chain` | at least 66/112 | `.5072529569` | `.65` | `.924642972` |
| `COMPLETE_chain` | at least 54/112 | `.4011013344` | `.55` | `.937697709` |

Thus

```text
1 - sum_j (1-power_j) = .808709261
```

is a dependence-free lower bound on the probability that all three pass at
the fixed alternatives. The mathematically first `N` satisfying the `.80`
union-power rule and `.90` marginal rule is 107; 112 is recommended because it
is the existing grid point, gives a small discreteness buffer, and simplifies
root batches. `N=96` is nearly adequate but has only `.89565` exact power for
the LoRA chain and a three-endpoint union lower bound of `.73173`.

### Claim boundary

This design supports only the registered chain-rate statements plus
descriptive decomposition. It does **not** separately claim that every
primitive authentic rate exceeds `.75`, every primitive leakage rate is below
`.10`, or every component mean exceeds `.20`. Those old component thresholds
can be printed as preregistered diagnostics, with intervals, but cannot gate or
rescue the chain claim. No mediation, compression, carrier superiority,
parenting, population, or domain-general claim follows.

If the paper needs the old component population thresholds as confirmatory
claims, use Section 3 instead.

## 3. Full-certification design: compress 75 decisions to eight

Define the following root variables prospectively from the already frozen
primitive fields. `min`/`max` is over the complete named roster and both
carriers; nothing is selected after outcomes.

```text
O_r = o_r

A_ALL_r = min(a_r,TEXT, a_r,LORA)

AUTH_ALL_r = min over k in {TEXT,LORA} of:
  c_auth_rk, t_auth_rk, t_redir_rk,
  q_gap_rk, q_sel_auth_rk, q_rel_auth_rk, gnew_rk,
  d_edge_rk, d_swap_redir_rk, u_auth_min_rk

LEAK_ANY_r = max over k in {TEXT,LORA} of:
  c_der_rk, c_null_rk, t_blind_rk, t_cut_rk, b_leak_rk,
  q_sel_sham_rk, q_rel_sham_rk,
  d_no_rk, d_sham_rk, d_swap_orig_rk, d_off_rk,
  d_leak_rk, u_max_rk

MISMATCH_r = same_mismatch_r
```

The eight-decision compound claim is:

```text
E[O]              > .95
E[A_ALL]          > .80
E[AUTH_ALL]       > .75
E[LEAK_ANY]       < .10
E[MISMATCH]       < .05
E[TEXT_chain]     > .60
E[LORA_chain]     > .50
E[COMPLETE_chain] > .40
```

Each decision uses the existing one-sided `.05` CP construction and the full
compound statement is an IUT. No within-compound alpha division is needed.

### Why this preserves the old requirements

For every positive primitive `X` in `AUTH_ALL`, rootwise
`X_r >= AUTH_ALL_r`. For every forbidden/control primitive `Y` in
`LEAK_ANY`, rootwise `Y_r <= LEAK_ANY_r`. Therefore passing the two joint
bounds implies, simultaneously, every old authentic/redirection floor and
every old `.10` leakage/control ceiling.

For every registered paired component `D=X-Y`, including `Cbind`, `Cnull`,
`Tgoal`, `Tcut`, `Qselect`, `Qrelevant`, `W0`, `W1`, `Fbind`, and `Freacq`,

```text
E[D] = E[X] - E[Y]
     >= E[AUTH_ALL] - E[LEAK_ANY]
     > .75 - .10
     = .65 > .20.
```

For the worst-control endpoint, rootwise
`Kmin >= u_auth_min - u_max`, so the same implication holds. `Freacq` retains
its total-path-necessity label. `A_ALL` implies both carrier-specific `.80`
retention floors. `MISMATCH` preserves the separate `.05` ceiling. Thus the
eight tests are not a post-hoc multiplicity shortcut; they state a stronger
joint-root certification whose logical consequences include every original
numerical requirement.

### Power and the new planning assumption

Joint minima/maxima do not inherit their marginal planning alternatives under
arbitrary dependence. Consequently this design must newly and explicitly
register the alternatives

```text
O=.99, A_ALL=.90, AUTH_ALL=.85, LEAK_ANY=.02, MISMATCH=.01,
TEXT=.75, LORA=.75, COMPLETE=.75.
```

These are assumptions for planning, not predictions or acceptance
thresholds. They are stronger than saying that every component marginal is
`.85/.02`, because they require joint within-root success. The stronger chain
alternatives are also required for logical coherence: the five joint
guardrails imply by Bonferroni that `P(COMPLETE_chain=1)>=.71` at their
planning values, and rootwise `COMPLETE_chain<=TEXT_chain,LORA_chain`;
retaining the old `.65/.55` LoRA/complete alternatives would therefore
describe an impossible joint distribution. `.75` for all three is simple and
feasible. If scientific judgment cannot defend these joint alternatives
before outcomes, use the lean chain-primary design; do not estimate them from
a selected child's pilot.

At fixed `N=192`, exact binomial enumeration yields:

| decision | exact critical count | marginal power |
|---|---:|---:|
| `O>.95` | at least 188 | `.955143475` |
| `A_ALL>.80` | at least 164 | `.983532273` |
| `AUTH_ALL>.75` | at least 155 | `.956928330` |
| `LEAK_ANY<.10` | at most 12 | `.999849027` |
| `MISMATCH<.05` | at most 4 | `.955143475` |
| `TEXT_chain>.60` | at least 127 | `.997672807` |
| `LORA_chain>.50` | at least 108 | `.999999995` |
| `COMPLETE_chain>.40` | at least 89 | `>.999999999` |

The arbitrary-dependence power lower bound for all eight is

```text
1 - sum_j (1-power_j) = .848269382.
```

The first integer encountered by exact enumeration that clears `.80` is 181;
192 is the existing grid point and still clears the rule despite discrete
nonmonotonicity in exact-test power. This is still
expensive, but it removes 32 pilot roots and caps confirmation at 192 rather
than exposing the study to a 512-root selection.

## 4. Why the rank-copula pilot should not be mandatory

The current simulation cannot strengthen the binding arbitrary-dependence
guarantee:

1. Once `sum beta <= .20`, Bonferroni already guarantees at least `.80` joint
   power for any endpoint dependence. The rank-copula test can only veto a
   sample size that has already passed a stronger assumption-free rule; it
   cannot justify a smaller one.
2. Thirty-two observations cannot identify a 75-dimensional copula. The
   empirical rank matrix has at most 31 nonconstant degrees of rank, tail
   dependence is effectively unobserved, and pairwise Spearman coefficients
   do not identify a multivariate copula.
3. The 99% CP interval around 200,000 simulations covers Monte Carlo error
   conditional on that synthetic copula. It does not cover uncertainty from
   estimating dependence with 32 roots or misspecifying the copula.
4. Remapping chain coordinates separately from their 72 constituents can
   produce decision vectors that preserve selected marginals while not being
   realizable by the deterministic root-level chain formulas. Calling this a
   “decision-dependence model” acknowledges rather than repairs the issue.
5. The simulation adds code, hashes, receipt paths, and a post-child pilot
   surface without changing the exact binomial estimands, confidence bounds,
   or worst-case guarantee.

Keep the eight DEV roots for generator/interface/resource canaries if useful,
but do not let scientific outcomes from them select `N`. Runtime/token/memory
quantiles may go only to a resource stop. Binary chain power has no nuisance
variance parameter once its null boundary and planning alternative are fixed.

## 5. Paired inference, adverse roots, and sequential alternatives

### Paired components

The existing Bonferroni difference of two CP discordance bounds is finite-
sample valid but conservative. An exact unconditional trinomial inversion over
`(n_plus,n_zero,n_minus)` could shorten a confidence interval for an individual
paired risk difference. A label-randomization/sign test would be exact for a
sharp exchangeable-label null only if authentic/control assignment were
actually randomized; it does not by itself certify the `.20` population SESOI.
Neither method solves the 75-way joint-power problem. The eight-decision
dominance construction is simpler and stronger for the proposed compound
claim.

### Adverse roots

Both replacements retain intention-to-treat root denominators, adverse fills,
the exact relaunch boundary, no replacements, and the frozen iid root
distribution. The planning alternatives are unconditional rates *after*
scientific and post-exposure failures receive adverse values. This is the
correct way to assure performance on adverse roots; a favorable-root pilot is
not.

### Sequential designs

An alpha-safe group-sequential or e-process design is possible, but not the
recommended first repair. For example, a Bernoulli likelihood-ratio
supermartingale with fixed null boundary `p0`, registered alternative `q`, and
threshold `1/.05` gives an anytime-valid chain test under `p<=p0`; roots could
be inspected only at predeclared batch boundaries and stop on success or a
resource futility rule. This preserves Type I error but needs a new exact power
and expected-cost lock, and simple likelihood-ratio boundaries need roughly
128--160 maximum roots for `.89--.96` marginal power at the current chain
alternatives. A fixed 112-root chain design is both more powerful at its cap
and far easier to audit. Sequentialization should be considered only after
per-root GPU cost is measured by non-scientific canaries.

No blinded internal pilot is needed. If a later design truly needs an adaptive
maximum, use prospectively calibrated alpha-spending or an anytime-valid test
on confirmation roots; do not use a 32-root empirical copula as a sample-size
oracle.

## 6. Recommendation to the architecture deliberation

For the optional post-parenting relay, adopt the **112-root chain-primary
design** unless the paper explicitly needs the old component population
thresholds. It is the highest information-per-GPU-hour design: the exact
end-to-end objects already contain the causal/safety anatomy, the compound
claim has >.80 worst-case planned power, and failed text stops all LoRA cost.
Report every component for diagnosis without turning all 72 into publication
gates.

If exact component floors/ceilings/SESOIs are non-negotiable, adopt the
**eight-decision, 192-root joint-certification design**. Do not retain the
75-endpoint power union and do not run the 32-root rank-copula pilot. The new
joint endpoints, their planning alternatives, and the chosen fixed `N` are
material changes and must pass the complete `AGENTS.md` deliberation and exact
human ratification path before implementation or execution.

## Source receipts

| source | SHA-256 |
|---|---|
| `AGENTS.md` | `1e3c413f3adbf172c409bc642bbf8242a736b0209461b6a7f81203450772f54e` |
| `research_notes/59_one_child_pcfl_relay_v3_execution_complete_architecture_proposal.md` | `6fc2d3dd4e9b779e76e6168a57424cb5e1cdeb6cff347ebb411b23ea6e4d00a2` |
| `research_loop/advisory/20260907_one_child_pcfl_relay_b9_b10_statistics_power_lock_v1.md` | `136dcf898de6fd97e850bd103bbbb3fee05a885effafa73ed61788c2b0709225` |
| `research_loop/advisory/20260907_one_child_pcfl_relay_v2_final_attack.md` | `5bea4603a67e6c2808f301578574c26616ca33c87a7b381ef1d91d8326f76042` |

The SHA-256 of this advisory is reported externally after final bytes are
written; it is not self-embedded.
