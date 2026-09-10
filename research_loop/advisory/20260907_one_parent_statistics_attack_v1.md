# One-parent/one-child statistics attack v1

Date: 2026-09-07

Status: **read-only statistical advisory**. This memo authorizes no change to
the bound plan or manuscript, no task or benchmark generation, no model or
tokenizer call, no adapter operation, no GPU use, no network access, and no
scientific claim. Any adopted repair must pass the `AGENTS.md` deliberation,
exact-byte ratification, implementation review, and scientific-run gate.

Audited bytes:

- `research_loop/plans/one_parent_child_headline_v1.md`, SHA-256
  `e356bcecc0cdec3199cf8ecb23c2dc9790a59a11ee6dc8f81b1bfd399c7cf4d5`;
- `paper/iclr2027_experience_models/main.tex`, SHA-256
  `3ad83dc406cdf2331a7ce833e1566002942fd21ed6b447313fe7315f6f83dc59`.

## Verdict

**REVISE BEFORE RATIFICATION OR CONFIRMATION.** The plan has the right
experimental skeleton: one matched factorial root, childhood checkpoints
forked byte-identically into write-off/write-on services, root-level collapse,
a genuine parenting-by-write interaction, and a correctly weighted
trapezoidal gain-AUC. It also correctly says that `P1-R0` is a package contrast
and cannot identify parenting.

The statistical contract is nevertheless not ready to support the sentence
“parenting taught learning.” The current bytes do not define what a root is a
sample from, do not bind a root/seed hierarchy or treatment-neutral coupling,
do not reconcile the manuscript's multiple “primary endpoints” with the
plan's single interaction, leave primary missingness and non-erasure gates
open, and call the study powered under a rule whose joint success probability
at the SESOI cannot exceed approximately one half. A positive interaction by
itself can also be produced by parenting making writes less harmful while
writes remain harmful in the parented child. That is effect modification, not
evidence that the parented child learned beneficially.

## Disposition by statistical issue

| issue | verdict | disposition |
|---|---|---|
| independent unit | **PASS IN PRINCIPLE / REVISE BYTES** | One full matched root is the unit. The plan says this, but neither file defines the root packet or sampling population precisely enough to justify iid root inference. |
| one-parent generalization | **REVISE** | With one fixed parent policy and one fixed child checkpoint, inference is conditional on those two artifacts. Roots replicate seeded lives/tasks, not parents or model identities. |
| root/seed hierarchy and common randomness | **REVISE** | “Counter-keyed common RNG opportunities” is a principle, not an executable coupling law. Bind key namespaces, marginal distributions, matched-call behavior, and root independence. |
| gain-AUC algebra | **PASS** | At equally spaced cuts, `[2G16+2G32+G48]/6` is the normalized trapezoidal AUC because `G0=0`. Call it gain-AUC, not generic nAUC. |
| causal difference-in-differences | **PASS WITH CLAIM REPAIR** | `D` is the within-root causal interaction of the complete childhood parenting protocol with deployment write permission, conditional on exact factorial execution. It is not a parent-population effect or a process-code mechanism effect. |
| repeated measures | **PASS IN PRINCIPLE / REVISE ANALYSIS CONTRACT** | Programs, cuts, calls, actions, fits, and services do not increase `n`. Seal the one-row-per-root analysis table and prevent any task-level standard error. |
| SESOI and power | **REVISE — BLOCKING** | The variance buckets approximate power for a significance-only rule, not the registered joint rule that also requires `estimate >= .05`. The SESOI's scale and scientific basis are also not sealed. |
| multiple endpoints and claims | **REVISE — BLOCKING** | The manuscript declares two primary endpoints plus many secondary endpoints while the plan names one primary root statistic. The non-erasure gates and saturation claim form additional unallocated tests. |
| saturation | **REVISE WORDING OR ADD A DOSE EXPERIMENT** | Two locally equivalent time increments at one budget can establish a local plateau, not saturation of active text. Search headroom and P1 growth do not identify why P0 flattened. |
| `P1-R0` versus causal `D` | **PASS IN PLAN / REVISE PAPER EMPHASIS** | `D` identifies parenting-by-write; `P1-P0` identifies the parented closed-loop write effect; `P1-R0` isolates nothing. The public two-agent story must not outrun this hierarchy. |
| evidence for “parenting taught learning” | **REVISE — BLOCKING** | Require both a practically/statistically positive `D` and a beneficial parented write effect, plus the sealed exclusion, deletion, parity, and transfer evidence listed below. |

## 1. The root is the unit, but its probability space is missing

The plan's statement that tasks, checkpoints, actions, samples, and fits are
repeated measures is correct. A root must contain the complete matched object:

1. one presealed exogenous root packet;
2. the cloned parented and unparented childhood branches;
3. both childhood write histories and terminal childhood checkpoints;
4. the exact `P0/P1` and `U0/U1` forks;
5. all five isolated deployment trajectories and all four probe cuts; and
6. exactly one scalar each for `D_r`, `C_active,r`, and `C_public,r`.

The analysis dataset must therefore have one row per assigned confirmation
root. The eight probe programs reduce to `V_{c,r}(t)` before inference. No
mixed model, task bootstrap, repeated decoding, adapter restart, or probe count
may silently enlarge the denominator.

What is not defined is the population behind `E[D_r]`. All roots share a
pinned child checkpoint, parent policy, updater, curriculum, writer, and code.
If they also share fixed wake and probe programs, a root-level t interval is
conditional on that fixed panel and reflects only the remaining seeded-life
variation. It does not cover sampling of CompilerGym programs. If fresh decks
are sampled independently per root, the interval may cover the registered
joint distribution of tasks and life randomness. The plan must choose.

**Precise repair.** Add the following estimand before any root identities are
created:

> A confirmation root is an iid draw from the hash-bound root-packet
> distribution `Q`, conditional on the frozen child checkpoint, frozen parent
> policy, frozen software, and registered CompilerGym universe. The primary
> estimand is `mu_D = E_{R~Q}[D_R]`. If program panels are fixed across roots,
> replace `Q` with the seeded-life distribution conditional on the named fixed
> panels and prohibit program-population language.

Prefer fresh 48-program wake and eight-program probe decks per root, sampled
from a sealed universe without replacement within a root and independently
across roots. The same assigned opportunities are paired across cells within
that root. If the same program identities are crossed over roots, either keep
the claim explicitly panel-conditional or use a predeclared crossed
root/program analysis that accounts for both sources of variation; a root-only
t interval cannot supply task-population generalization in that case.

## 2. “One parent/one child” is topology, not the sampling unit

The manuscript alternates between “one parent and one child,” “one child is
parented,” and “independently raised child lives.” With 20 or 32 confirmatory
roots, the experiment does not literally have one statistical child. Each
root instantiates the same one-parent/one-child topology using the same child
checkpoint and same parent policy. Those roots are stochastic life/task
replications of fixed software artifacts.

There is `n_parent=1` and `n_child_checkpoint=1`. No root count estimates
between-parent or between-base-model heterogeneity. Even a perfect result
supports only:

> Under this frozen parent policy, child checkpoint, curriculum, writer,
> resource layer, and registered root distribution, parenting changed the
> benefit of later personal writes.

It does not support a “general parenting effect,” an average effect over
parents, an average effect over child models, or a claim that an arbitrary
parent can teach an arbitrary child. To make those claims, sample multiple
parents as independent clusters and multiple child checkpoints or identities,
with replication within parent, then model the hierarchy. That is a different
and much larger experiment.

**Precise repair.** Replace the manuscript's suggestion that multiple lives
under the same fixed parent establish a “general parenting effect.” Say that
they establish reproducibility over registered life/task realizations for one
fixed parent-child policy pair. If only one full root is run, call it a case
study; if many roots are run, do not call tasks within a root replications of
parenting.

## 3. Seal a real root/seed hierarchy

Common randomness is variance reduction, not replication. It is valid only if
each arm retains the correct marginal distribution and treatment-induced calls
cannot shift later draws. The current phrase “counter-keyed common RNG
opportunities rather than one shifting global RNG” does not say:

- how the 32 root masters are obtained or proven independent;
- which nursery tasks, deployment decks, program orders, decoding uniforms,
  writer initialization/order, environment randomness, and probe calls share
  a key across arms;
- what happens when a call exists in one branch but not another;
- whether the same random variate is used across cuts and services;
- whether a backend actually honors the offered seed; or
- whether hardware nondeterminism is one realization inside a root or an
  illicit retry source.

**Precise repair.** Seal a manifest and deterministic key derivation over at
least

```text
(experiment_hash, split, root_id, domain, matched_opportunity_id,
 stage, call_slot, sample_index, purpose)
```

where `domain` separates task generation, deck/order generation, model
sampling, writer order/initialization, environment, active-text updater, and
probe evaluation. Corresponding potential calls use the same
`matched_opportunity_id` without an arm label; unmatched treatment-specific
calls use a disjoint purpose key and cannot consume a global stream. Every
receipt records the resolved key and proves that the backend honored it.

Prebind the confirmation root IDs and order. Root masters must be independent
under the generator. Predeclare that a post-dispatch crash, malformed action,
nonfinite fit, or failed mount is an assigned-root outcome/missingness event,
not permission to choose a new seed. Resume only from a pre-request committed
boundary proving that no response or action occurred.

For the entry cut, do not independently re-estimate identical forks. Evaluate
the exact common parented checkpoint once for `P0/P1` and the exact common
unparented checkpoint once for `U0/U1`, or use byte-identical, counter-matched
probe calls and assert equality. Otherwise baseline subtraction adds avoidable
Monte Carlo noise and can manufacture an apparent post-entry difference.

## 4. What gain-AUC and `D` do—and do not—identify

The gain-AUC formula is correct for equal 16-program intervals:

```text
gAUC_r(c) = (2*G16 + 2*G32 + G48)/6,  with G0 = 0.
```

It is the average trapezoidal **change from that cell's own entry**, not area
under raw value. The manuscript should use the exact name `gain-AUC` and bind
the per-program normalization, clipping, failure value, aggregation order,
and whether `V(16/32/48)` is measured before or after the write at that cut.
The present “mean best nonnegative held-out IR instruction reduction” floors
negative values and takes a best-of budget, so the outcome is bounded,
censored, and potentially skewed. A t interval may remain the registered
root-level analysis, but the raw `D_r` vector, a robust root-level sensitivity
interval, and floor/ceiling occupancy must be reported.

Define

```text
W_P,r = gAUC_r(P1) - gAUC_r(P0)
W_U,r = gAUC_r(U1) - gAUC_r(U0)
D_r   = W_P,r - W_U,r.
```

Under an exact full factorial execution, `D` is a causal interaction for the
complete parenting protocol, including all downstream changes in actions,
admitted rows, adapters, and active-text stores. It needs no observational
parallel-trends assumption because both intervention combinations are run
from cloned checkpoints. But it is scale-dependent and does not isolate one
lesson, “meta-intelligence,” target quality, or a LoRA carrier mechanism.
Entry subtraction removes an intercept difference; it does not remove
floor/ceiling compression or the possibility that parenting produces more
learnable later experience.

**Precise repair.** Preseal a target-blind development headroom criterion,
retain all assigned confirmation roots regardless of entry value, report
`P0-U0` entry differences, and add one predeclared headroom-normalized
sensitivity analysis. Never match, exclude, or adjust on realized entry score,
store yield, admitted-row count, or other post-treatment variables.

## 5. The registered power language is wrong for the registered success rule

The `N=20, SD=.075` and `N=32, SD=.10` buckets are recognizable
approximately-80%-power calculations for rejecting zero with a two-sided
root-level t test when the true mean is `.05`. They are not approximately 80%
power for the actual joint rule:

1. the 95% interval is positive; and
2. the observed point estimate is at least `.05`.

At a true effect exactly equal to `.05`, the estimate is at least `.05` only
about half the time under the planning model. The joint success probability
therefore cannot exceed approximately 50%, no matter how often the interval
excludes zero. An 80% upper confidence bound on SD also does not turn an
approximate conditional calculation into a guaranteed 80%-powered design.

The adaptive rule is incomplete when some intended contrasts have SD upper
bounds below a threshold and others exceed `.10`, and the main text does not
say whether `D`, `C_active`, and `C_public` all drive sample size. It also lacks
the exact chi-square/other SD-bound formula and assumptions. Missing roots can
make the nominal N differ from analyzed N.

**Precise repair.** Choose one of these coherent contracts and simulate its
operating characteristics under the bounded/skewed outcome distributions seen
in development:

- retain the joint success rule, but power it as a joint rule at a design
  alternative strictly larger than `.05`; report that `.05` is the minimum
  observed estimate, not the effect size at which power is 80%; or
- treat `.05` as the design alternative for a significance-only primary test,
  remove `estimate >= .05` from confirmatory success, and separately describe
  whether the estimate reaches practical importance; or
- test a minimum-effect null such as `mu_D <= .05`, which requires a one-sided
  lower confidence bound above `.05` and a larger sample powered at a stated
  alternative above `.05`.

Use only `SD(D)` to choose N for the primary claim. Let higher-rung contrasts
inherit the chosen N and report their achieved precision, unless the study is
explicitly powered for all of them using a fully specified maximum-N rule.
Bind the variance-bound equation, the exact routing for every threshold
combination, the analyzed-N requirement, and simulation code before the first
12 roots. If the maximum feasible N does not reach the declared operating
characteristics, call the study precision-limited rather than powered.

The `.05` SESOI itself needs a frozen justification on the exact gain-AUC
scale: five percentage points of what denominator, relative to what oracle-to-
floor span, and why it changes scientific interpretation. Development data
may justify this before sealing; confirmation data may not revise it.

## 6. Endpoint multiplicity is unresolved

The plan names `D` on gain-AUC as primary. The manuscript instead calls both
held-out task value and normalized AUC “primary endpoints,” then lists early
slope, value/token, routing, proposal quality, forward transfer, retention,
and forgetting. It leaves a “joint success rule” TBD. These are not harmless
wording differences: they permit selecting the most favorable timepoint or
endpoint after seeing results.

The plan's fixed sequence `D -> C_active -> C_public`, with testing stopped at
the first failure, is a valid conservative gate for those three claims if each
null, sidedness, alpha, and success threshold is fixed. It does not
automatically cover:

- several `I(t)` timepoint tests;
- terminal value or early slope;
- the two undefined non-erasure endpoints;
- forward transfer, retention, and forgetting; or
- the separate plateau/saturation claim family.

**Precise repair.** Make `mean(D_r)` on gain-AUC the sole primary endpoint.
State that raw value curves and `I(16), I(32), I(48)` are repeated descriptive
decompositions with simultaneous intervals, not additional primary tests.
Keep `C_active` and `C_public` in the fixed sequence. Define exact numeric
non-erasure margins and make clear whether they are necessary co-primary
gates; if so, power and multiplicity must include them. Label all remaining
behavioral endpoints descriptive or put them into a named Holm/max-t family.

Either add the local-plateau claim as the next prospectively gated composite
test in the hierarchy, allocate alpha to it separately, or call it descriptive.
Do not run it as an unadjusted second confirmatory family after inspecting the
same roots.

## 7. “Saturation” is not identified

The plan's equivalence requirement is much better than interpreting a
nonsignificant slope as a plateau. With the same probes paired across cuts,
two intervals wholly inside `[-.05,.05]` can support this bounded statement:

> `P0+ACTIVE_TEXT_FIXED` changed by less than the registered equivalence
> margin over programs 16–32 and 32–48 on this panel and budget.

It cannot support “active text saturated.” There is only one update/read
budget, one lifetime horizon, and one updater. A plateau can result from probe
clipping, poor retrieval, delayed learning, depleted action opportunity,
optimizer dynamics, or the chosen program order. A fixed-seed 10,000-sequence
compiler reference shows objective headroom, not that P0 could access that
headroom or had exhausted its representational/resource capacity. P1 growth
shows treatment separation, not the cause of P0's local flatness.

**Precise repair.** Use “registered local plateau under this 48-program
resource envelope” everywhere and forbid the bare word “saturation.” If a
saturation claim is scientifically necessary, add prospectively randomized
higher P0 update/read/action budgets (at least two levels beyond the nominated
budget) and show equivalence of their gains while an attainable reference
preserves headroom. That is a new experiment, not a wording tweak.

Also bind whether the equivalence margin `.05` is the same scientific margin
as the gain-AUC SESOI; the quantities differ. Report the joint covariance of
`s1` and `s2`, all root values, and floor/ceiling occupancy.

## 8. `P1-R0` is public packaging, not parenting causality

The three contrasts answer different questions:

- `D`: did the complete parenting protocol change the later closed-loop
  effect of enabling writes?
- `C_active=P1-P0`: did writes beneficially change a parented agent already
  equipped with the common active-text mechanism?
- `C_public=P1-R0`: did the full parented/practice-written/continual package
  gain more over its own entry than the raw-actor frozen-parameter
  active-memory reference?

`C_public` includes childhood practice writes, parenting, deployment writes,
different on-policy experience, and different later active-text contents. It
isolates no component and cannot rescue a failed `D`. Because it compares
gain-AUC, it is not itself terminal system superiority; the raw terminal
contrast `V_P1(48)-V_R0(48)` is a separate package-level quantity.

**Precise repair.** The abstract, figures, results headings, and captions must
lead with the four-cell root-level interaction. A two-agent `P1` versus `R0`
figure may remain as the public system illustration only if its caption says
“full-package contrast; non-causal for parenting.” Never title it the parenting
effect. Report entry, raw terminal value, gain-AUC, and their different
interpretations separately.

## 9. Exact sealed evidence required for “parenting taught learning”

For the narrow operational claim—*this frozen parenting protocol taught this
fixed child system to benefit more from later personal writes on a fresh
registered environment*—the minimum sealed evidence is the conjunction below.
No single favorable `P1` curve suffices.

### Before confirmation

1. Hashes of the fixed parent policy/weights/decoder, child checkpoint,
   minimal birth prompt, closed correction templates, nursery generators,
   target-blind split, deployment writer, active-text mechanism, scoring code,
   and deletion/firewall tests.
2. A root manifest binding the population `Q`, all confirmation root IDs and
   order, deck/program/probe identities, seed keys, arm/cut coupling, and the
   no-replacement/restart law.
3. A statistics manifest binding `V`, failure values, clipping, entry timing,
   gain-AUC, `D`, the sole primary null, sidedness, alpha, SESOI rationale,
   fixed hierarchy, non-erasure margins, missingness handling, sample-size
   algorithm, and exact analysis code.
4. Target-blind development evidence of usable score headroom and variance,
   followed by immutable freeze; development and four spending-pilot roots
   remain excluded from confirmation.
5. Proof that `P0/P1` share identical parented entry checkpoint bytes and
   `U0/U1` share identical unparented entry checkpoint bytes, with identical
   resource contracts and paired exogenous opportunities.

### From every assigned confirmation root

6. Intent-to-treat inclusion of every prebound root; a complete disposition
   for crashes, invalid actions, missing cuts, quarantined fits, and resumes;
   no seed/root replacement after any response or outcome exists.
7. Byte receipts proving parent deletion and absence of correction text,
   nursery transcript/ledger, rehearsal rows, probe results, cross-root state,
   and hidden target information from deployment life and writers.
8. Childhood treatment-fidelity receipts: parent code and cited prior public
   evidence, U neutral input, equal slot/exposure/optimizer opportunity,
   absolute-law admission, neutral-shadow attribution, and the complete
   correction-to-application funnel. These establish what treatment occurred;
   they are not extra statistical replicates.
9. The complete one-row-per-root table, all raw `V_{c,r}(t)` values, `W_P,r`,
   `W_U,r`, `D_r`, routing/proposal measures, missingness flags, and artifact
   hashes, released only after N locks.

### Required confirmatory pattern

10. A positive, practically adequate root-level `D` under the prospectively
    powered joint rule, showing that parenting changed the benefit of writes.
11. A positive, practically adequate `C_active=W_P`, showing that writes were
    actually beneficial in the parented child. `D>0` alone is insufficient:
    for example `W_P=-.01` and `W_U=-.10` gives a favorable `D=.09` while the
    parented child is still harmed by writing.
12. Fresh held-out gains occur only after deployment experience/writes and are
    not an entry-only difference; report `P0-U0` entry competence, all curves,
    floor/ceiling occupancy, and the headroom-normalized sensitivity.
13. Registered non-erasure gates pass. Adapter removal and same-corpus carrier
    diagnostics may support a parametric-carrier interpretation, but they do
    not create parenting causality and must not replace items 10–12.
14. `P1-R0`, if positive, is reported only as corroborating full-package
    performance after items 10–13 pass. It is neither necessary nor sufficient
    for “parenting taught learning.”

Even this conjunction supports an operational, distribution-bound statement.
It does not prove that the named process lesson is the unique mediator, that
the effect generalizes to other parents/children/models/tasks, or that the
child acquired a domain-general learning algorithm. Parenting can legitimately
improve which deployment experiences are generated and admitted; because
those are post-treatment mediators, the headline `D` is a total
parenting-by-write interaction, not a controlled direct effect independent of
inherited competence or data quality.

## Required byte changes, in priority order

1. **Define the root packet, sampling distribution, and conditional scope.**
2. **Seal the root/seed/common-randomness and restart manifest.**
3. **Make gain-AUC interaction `D` the sole primary endpoint in both files.**
4. **Repair the SESOI/power contract using operating-characteristic
   simulation for the actual joint rule.**
5. **Bind primary missingness/failure values and the one-row-per-root reducer.**
6. **Define and account for non-erasure and all secondary endpoint families.**
7. **Require both positive `D` and positive `C_active` before saying parenting
   taught beneficial learning.**
8. **Replace saturation with local-plateau language unless a resource-dose
   experiment is added.**
9. **Keep `P1-R0` explicitly subordinate and package-level in every paper
   surface.**

Until all nine are exact, source-bound, and independently re-audited, the
appropriate paper language is **proposed causal design**, not powered causal
evidence.
