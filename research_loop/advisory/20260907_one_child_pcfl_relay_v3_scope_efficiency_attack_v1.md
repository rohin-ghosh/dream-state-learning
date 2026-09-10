# One-child PCFL relay v3: scope and statistical-efficiency attack v1

Date: 2026-09-07

Status: fresh skeptical-review advisory over the unbound relay-v3 proposal.
This file changes no frozen one-parent packet, relay proposal, statistics lock,
benchmark, implementation, model, tokenizer, child, root, adapter, external
state, or GPU authority. It authorizes no execution or scientific claim.

## Verdict

**REVISE.** The relay-v3 causal topology is unusually careful and is strong
enough to preserve as an architecture candidate. Its confirmatory statistics
are not proportionate to either its paper role or its scientific estimand.
The proposal has turned an audit manifest into a 75-decision scientific claim
family, then powered the conjunction of that family under arbitrary dependence
with a 32-root model pilot and a possible 96--512 confirmation roots. That is
methodologically conservative but scientifically inefficient.

The relay does not test the paper's full objective. It can test, conditional on
one fixed parent-deleted child, whether supported relations from that child's
own public actions are carried, connected, traversed under goals, used to
select a public information action, expanded by a prospectively declared
outcome, and used later through both explicit text and LoRA. It does **not**
test:

- whether parenting improves deployment-time learning curves;
- whether performance grows with lifetime or beats `ACTIVE_TEXT_FIXED` where
  that baseline saturates;
- whether the carrier is physically compressed or even smaller than text;
- whether the parent caused the relay ability;
- autonomous theory invention, populations, or domain generality.

Those exclusions are already admitted by v3. They mean that spending up to 512
roots on this optional relay would over-optimize a secondary mechanism assay
while the one-parent headline remains the submission-critical experiment.

The correct repair is not to weaken the mediator chain. It is to make the
**literal same-root dual-carrier chain itself the sole confirmatory relay
endpoint**, retain all causal cuts, twins, and leakage controls inside that
binary endpoint, and demote its 75 constituent decisions to gates or
descriptive decomposition. Under the proposal's existing `.40` null boundary
and `.55` planning alternative, fixed `N=96` gives approximately `.902` exact
power. No nuisance pilot, rank copula, or upward extension is needed.

## 1. What v3 gets right and must retain

The following are scientifically load-bearing, not removable bureaucracy:

1. One selected terminal child, after deletion of its one parent and every
   nursery artifact. Roots are isolated trials of byte-identical clones, never
   learners, peers, or a cohort.
2. Links originate from the child's own public co-use events and contain only
   minimal canonical adjacency, not hidden authored paths or answers.
3. Text and LoRA receive the same admitted semantics through the same finite
   one-hop read interface, and the actor uses a clean common resolver.
4. Phase B is write-denied and destroyed; Phase C restarts from the common cut;
   Phase D is rebuilt cleanly from the common base and one declared semantic
   slot.
5. Connectedness is challenged by authentic-versus-deranged and
   authentic-versus-truthful-null carriers.
6. Goal traversal is challenged by different same-start goals, the exhaustive
   target-blind controller, necessary-row cuts, and a binding twin that must
   redirect rather than merely damage behavior.
7. Expansion is prospective: the gap, hypotheses, outcome map, and experiment
   are sealed before the public outcome; the outcome selects one already
   committed row.
8. Delayed use is challenged by no-write, truthful sham-write, binding-swap,
   and reachout-off forks, with the D target requiring one old plus one new row.
9. Adapter-off, wrong-life, no-semantic/candidate, unaided-generation,
   source-action-string, passive-channel, and closure controls remain adverse
   rather than disappearing when inconvenient.
10. The same randomized root must clear the whole event sequence for both
    TEXT and LoRA. Aggregate success by disjoint root subsets is insufficient.

The v3 proposal's byte grammar, deterministic admission compilers, finite
adaptive reader closure, clean carrier transactions, reset boundary, and
adverse failure law are appropriate implementation obligations. The error is
making each obligation a separately powered paper claim.

## 2. Why the 75-decision power problem is self-created

The proposal already defines a complete binary observation per root:

```text
COMPLETE_chain_r = TEXT_chain_r * LORA_chain_r.
```

Every causal cut, twin, control, and mediator is reduced inside that root
before the product is formed. Consequently, arbitrary dependence among the 75
constituent fields is not a nuisance for inference on the complete-chain rate.
It is part of the observed Bernoulli outcome. Across iid roots, inference on

```text
theta_COMPLETE = Pr(COMPLETE_chain_r = 1)
```

requires one exact binomial calculation, not a model of the correlations among
the factors making the indicator one.

The current power construction answers a different and much larger question:
"What N gives at least `.80` probability that all 75 separately thresholded
population claims pass at their planning alternatives?" The relay's paper
claim does not need 75 population claims. It needs evidence that a nontrivial
fraction of the **same roots** completed the exact causal chain through both
carriers. The former does not strengthen the latter enough to justify its
cost.

The rank-copula requirement adds little defensible information:

- The analytic union bound is already declared binding, so the simulation
  cannot reduce N.
- Thirty-two pilot roots give extremely coarse dependence information for 75
  mostly binary, conjunctive fields.
- Hash-breaking binary ties turns within-class identities into artificial
  rank resolution. Spearman dependence on those tie-broken ranks can reflect
  the tie rule as much as biological/scientific covariance.
- The pilot consumes expensive actor/writer observations but is prohibited
  from estimating the only marginal quantity that matters for the proposed
  chain: its success rate.
- Even a perfect dependence model would power separate component claims that
  should not be confirmatory claims in the first place.

Keep the 75-row registry as a machine-readable audit and diagnostic manifest.
Do not treat it as 75 scientific decisions.

## 3. Smallest defensible confirmatory estimand

### 3.1 Root score

Remove the leaked-oracle and deterministic benchmark-integrity objects from
the child outcome; they become pre-execution gates in Section 5. Retain the
current behavioral conjunctions, without dropping controls:

```text
RELAY_rk = a_rk * B_OK_rk * C_OK_rk * D_OK_rk * CTRL_OK_rk

DUAL_RELAY_r = RELAY_r,TEXT
               * RELAY_r,LORA
               * (1 - same_mismatch_r)
```

`B_OK`, `C_OK`, `D_OK`, and `CTRL_OK` retain their v3 definitions. Thus a
successful root still requires authentic connected use, goal-conditioned
traversal, authentic-signal-driven experiment choice, prospective public
outcome admission, controlled write benefit, binding redirection,
reachout-path necessity, and every frozen leakage control for both carriers.
This is not a softer chain; it is the same scientific chain without embedding
a benchmark fixture in the child score.

Missing, malformed, unsupported, unavailable, post-exposure failure, build
failure, read failure, or action failure remains `DUAL_RELAY_r=0`. No root is
dropped or replaced.

### 3.2 Sole confirmatory hypothesis

Use one paper-facing relay hypothesis:

```text
H0: theta_DUAL <= .40
H1: theta_DUAL >  .40
```

where `theta_DUAL=E[DUAL_RELAY_r]` over the frozen valid-root distribution,
conditional on the one fixed child. Test with the v3 one-sided exact
Clopper--Pearson rule at alpha `.05`.

At fixed `N=96`, the exact critical count is `47` dual-chain roots:

```text
Pr[Binomial(96,.40) >= 47] = .0467064790
Pr[Binomial(96,.55) >= 47] = .9016376316
```

Count `46` does not pass (`p=.0704228484`). Thus `N=96` is the smallest member
of the proposal's existing grid that meets its existing approximately `.90`
power objective at the existing `.55` planning alternative. There is no
scientific justification for a blinded move to 128--512 once the estimand is
correctly reduced.

An independently implemented exact-arithmetic receipt must reproduce these
numbers before ratification. These calculations are a design recommendation,
not current execution authority.

### 3.3 Closed release sequence

The minimal closed family has one inferential endpoint:

```text
G0  all deterministic validity and provenance gates pass
G1  explicit-TEXT feasibility gate passes; otherwise LoRA does not open
H1  theta_DUAL > .40 by the fixed exact test
```

`G0` and `G1` are operational validity/spending gates, not contribution
claims and not members of a multiplicity family. `H1` is a family of one and
therefore needs neither a 75-way conjunction-power condition nor a copula.
If `H1` fails, the relay has no positive confirmatory claim; component results
remain diagnostic. No favorable component may be promoted post hoc.

For `G1`, the current TEXT floor can be retained as a strict benchmark-usability
gate: with `N=96`, require at least `66` `TEXT_chain` roots, equivalent to the
current one-sided exact lower-bound rule against `.60`
(`Pr[Binomial(96,.60)>=66]=.0483740321`). This criterion has approximately
`.934` power at the existing `.75` text planning rate. It is deliberately not
reported as a new text-memory contribution; TEXT is the explicit semantic
positive control for interpreting LoRA.

## 4. Exact compute-saving execution order

The simplified estimand enables large savings without changing the root score.

1. Seal all 96 roots, twins, opportunity tapes, RNG schedules, and their fixed
   order before actor exposure.
2. Run the full TEXT chain on all 96 roots. If fewer than 66 pass, stop as a
   benchmark/interface failure. If fewer than 47 pass, `H1` is mathematically
   impossible even without the stronger TEXT gate; do not build a LoRA.
3. Open LoRA only for roots with `RELAY_TEXT=1`. For every TEXT-failed root,
   set `DUAL_RELAY=0` by logical definition; do not pretend its unexecuted
   marginal LoRA response was observed.
4. Within a LoRA root, execute phases in causal order. As soon as any required
   positive, cut, twin, or control makes `RELAY_LORA=0` irreversibly, adverse-
   fill all downstream chain fields and stop spending on that root.
5. Process roots in the sealed order. Stop and adverse-fill the remaining
   roots when either (a) 47 dual successes have accumulated, which passes even
   if every remaining root is counted as failure, or (b) 50 failures have
   accumulated, which makes 47 successes impossible. The event "47 successes
   before 50 failures" is exactly the fixed-`N=96` binomial rejection event;
   it introduces no optional-success test.
6. Do not estimate a marginal population `LORA_chain` rate from the
   TEXT-success subset. The sole inferential quantity is the unconditional
   96-root dual score with every skipped root counted as zero.

This preserves intention-to-treat for the primary, same-root closure, and the
full causal chain while avoiding LoRA builds on roots that can no longer
contribute to the registered dual outcome. It trades unnecessary diagnostic
completeness for GPU-hour efficiency explicitly, rather than silently.

## 5. Gate-only validation

The following decide whether the instrument is valid enough to expose the
child. They are not stochastic claims about experiential intelligence:

- receipt chronology `P0<R0<PU`, selected-child/deletion receipt, source
  manifests, and capability graph;
- canonical JSON/JSONL grammar, duplicate/unknown-field rejection, total
  `G_atom/G_link/G_new`, collision/conflict law, and byte replay;
- common-core merge equivalence, response masks, optimizer/build transaction,
  deterministic clean rebuilds, mount/off behavior, and rollback;
- text exact-copy reader, LoRA exact-row read canary, typed routing canary,
  common chat/template/model/tokenizer hashes, and resource ceiling;
- actor/world/cache/file/socket/RNG reset and parent/nursery/raw-ledger
  capability denial;
- complete root structural theorem and finite-controller closure in Section 7;
- leaked-oracle solvability and explicit-TEXT feasibility; and
- exact reducer, adverse-fill, sealed-order stopping, critical-count, and
  manifest-replay fixtures.

Failure of a deterministic root theorem before any actor exposure is a
benchmark-construction failure and global stop, not evidence that the child
failed. Do not redraw the root. Repairing the generator requires a new version
and deliberation. Failures after actor exposure retain the adverse-zero law.
This separates instrument invalidity from scientific failure more cleanly than
charging a malformed benchmark instance to the learner.

## 6. Behavioral conditions retained inside the primary

The following must remain actual paired potential-outcome forks inside
`DUAL_RELAY`, not be demoted to CPU assertions:

| scientific question | retained root-level interventions |
|---|---|
| Were useful connections carried rather than atoms merely present? | authentic, projected derangement, truthful matched null |
| Did the fresh goal change traversal? | paired same-start goals, target-blind ceiling, necessary bridge cut, binding twin redirection |
| Did old memory direct acquisition of relevant evidence? | authentic signal, truthful irrelevant sham, pre-outcome declaration/map, reachout-off |
| Did the truthful new row cause later behavior jointly with old experience? | edge write, no-write, truthful sham-write, binding-swap, D minimal-support path |
| Was LoRA rather than wrapper/prior/life-independent state responsible? | exact TEXT semantics, adapter-off, wrong-life, unaided/no-semantic carrier, candidate/source/passive leakage controls |

The existing `u_max/u_auth_min/Kmin` roster can remain as one strict root-level
`CTRL_OK` reduction. It should not generate a separate floor, ceiling, and
paired test for every named control. Every constituent result remains visible
in the artifact table.

## 7. CPU theorem obligations

These are universal or deterministic benchmark facts. They belong in a proof
receipt, not a hypothesis family:

1. Every canonical serializer round-trips and every compiler is total over
   its frozen finite input grammar.
2. Proposal/event chronology, public support, and one-bit hidden truth audits
   cannot enter a carrier except through the admitted minimal row.
3. Every root has two different unique length-3/4 B paths, no direct one-row
   solution, and all proper subsets/replacements remain below the oracle
   ceiling.
4. Derangement, null, sham, and D-sham fixtures are truthful, matched on the
   registered strata, and irrelevant under the complete finite policy class.
5. The authentic C relation changes which public experiment is separating;
   its sham does not, and actor-public equipoise is exact before outcome.
6. The D goal's unique minimal semantic support is exactly the named old row
   plus the prospectively selected new row; every feature subset, compound
   row, cache, metadata, reacquisition history, and direct action route lacking
   either member stays below ceiling.
7. The finite adaptive reader enumeration covers hits, misses, malformed and
   unavailable returns, repeats, stopping, timing classes, and all legal
   reacquisition paths; randomized policies reduce to mixtures without new
   observations.
8. Twin involutions change both bindings and the oracle action while
   preserving registered marginals, types, degrees, lengths, slots, and
   resources.
9. Catalog and passive metadata contain no hidden answer channel; text and
   LoRA carriers expose exactly the declared row bytes through the same query
   contract.
10. All 96 sealed root packets pass these checks before model exposure. A
    counterexample invalidates the packet version; roots are never regenerated
    after observing child behavior.

Exhaustive CPU obligations should be tested as broadly as feasible over the
generator seed space in addition to all 96 packets. Their evidentiary unit is
the theorem/test case, not an iid child-performance root.

## 8. Descriptive diagnostics, not confirmatory decisions

Preserve and print the complete v3 endpoint registry, but label it correctly:

- per-carrier `a`, `B_OK`, `C_OK`, `D_OK`, and `CTRL_OK` rates;
- every authentic, deranged/null, blind/cut/twin, sham, no-write/sham-write,
  binding-swap, reachout-off, adapter-off, wrong-life, and leakage cell;
- bounded value-scale contrasts `Cbind_value`, `Tgoal_value`, `Qselect_value`,
  `W0_value`, `W1_value`, `Fbind_value`, and `Freacq_value`;
- individual TEXT and LoRA chain observations where actually executed;
- proposal/admission precision, row-read fidelity, route syntax, failures,
  tokens, calls, bytes, time, memory, and energy; and
- failure location and cumulative survival through A/B/C/D for both carriers.

Point estimates and exact intervals may be shown, but they are
multiplicity-unadjusted decomposition unless a future separately ratified
family says otherwise. They explain *why* the dual endpoint passed or failed;
they cannot rescue a failed `H1` or support a selected component claim.

The 75-item table remains valuable as a conformance matrix. It ceases to be a
75-item promotion ladder.

## 9. Paper-facing role and claim boundary

The relay should appear, if it passes, as a mechanistic experiment downstream
of the actual parenting/lifetime headline. It is not the public `P1` versus
`R0` benchmark and must not delay that critical path. Its one result answers:

> On a nontrivial fraction of registered environments, did the same fixed,
> parent-deleted child complete the predeclared experience-to-action mediator
> chain under both an explicit semantic carrier and a LoRA carrier, including
> causal cuts, binding twins, prospective public acquisition, and later
> old-plus-new use?

Only if `H1` passes may the paper say:

> Conditional on this fixed child and registered PCFL distribution, the exact
> observed relay chain completed through both explicit text and LoRA on more
> than 40% of roots by a one-sided 95% exact lower bound. Successful roots
> required authentic child-generated public relations, goal-specific traversal,
> a memory-directed public experiment, prospective outcome admission, and a
> later action jointly dependent on old and new experience; registered cuts,
> twins, and leakage carriers failed on those same roots.

That statement is stronger and cleaner than separately asserting 75 component
thresholds. It remains narrower than the project's full thesis.

Forbidden even after a pass:

- “compressed experience” or “LoRA is smaller than text.” The existing byte
  receipt shows current all-layer rank-8 adapters are approximately 80.8 MB;
  physical compression requires a separate honest crossover/rate--distortion
  experiment.
- “continual improvement,” “learning curves,” or “beats strong memory.” Those
  belong to the one-parent deployment experiment.
- “parenting caused the relay,” because the relay conditions on one selected
  child.
- “graph in the weights,” “autonomous discovery,” or generalization beyond the
  registered PCFL distribution.

If the ICLR headline is not already sealed, spend only on the relay's CPU
theorems and explicit-TEXT feasibility. A 96-root LoRA relay is justified only
as secondary causal evidence after the parenting/lifetime experiment clears
its writer and spending gates. A small earlier relay run may be labeled
exploratory infrastructure work, never substituted for the fixed confirmation.

## 10. Concrete v3.1 disposition

| v3 element | disposition |
|---|---|
| one child / isolated roots | retain exactly |
| canonical ledger and total compilers | retain as implementation contract |
| root semantic theorem and adaptive closure | retain as CPU validity gate |
| TEXT first, LoRA second | retain, but LoRA only where TEXT leaves the dual endpoint live |
| all B/C/D causal cuts and twins | retain inside `DUAL_RELAY_r` |
| complete leakage-control roster | retain inside one `CTRL_OK` root reduction and report constituents |
| 75 separately thresholded decisions | remove from confirmatory family; preserve as diagnostics/conformance |
| 32-root rank-only nuisance pilot | remove |
| 200,000 rank-copula simulations | remove |
| `[96..512]` upward N selection | replace with fixed `N=96` |
| marginal TEXT/LORA/each-component claims | descriptive unless separately ratified later |
| `COMPLETE_chain` | rename `DUAL_RELAY`; sole confirmatory relay endpoint |
| root/component short-circuiting | allow prospectively with adverse fill and full denominator |
| compression/lifetime/baseline language | keep outside relay |

## Bottom line

The causal architecture is worth keeping. The statistical superstructure is
not. V3 currently spends to prove that every bolt in the instrument clears its
own population threshold, although its scientifically meaningful output is
already one exact, failure-inclusive, same-root conjunction. A fixed 96-root
dual-chain test retains the strongest causal property in the proposal, has
approximately 90% power at the proposal's own planning point, admits aggressive
but honest short-circuiting, and frees the paper's scarce GPU/time budget for
the actual one-parent learning-curve headline.

**Final recommendation: REVISE v3 into this one-primary v3.1 before any formal
ratification. Do not ratify the 75-decision/512-root power lock as the relay's
paper-facing design.**

## Source read receipts

The SHA-256 of this advisory is reported externally after its final bytes are
written. Sources read in full for this attack:

| source | SHA-256 read |
|---|---|
| `research_notes/59_one_child_pcfl_relay_v3_execution_complete_architecture_proposal.md` | `6fc2d3dd4e9b779e76e6168a57424cb5e1cdeb6cff347ebb411b23ea6e4d00a2` |
| `research_loop/advisory/20260907_one_child_pcfl_relay_b9_b10_statistics_power_lock_v1.md` | `136dcf898de6fd97e850bd103bbbb3fee05a885effafa73ed61788c2b0709225` |
| `research_loop/advisory/20260907_one_child_pcfl_relay_v2_final_attack.md` | `5bea4603a67e6c2808f301578574c26616ca33c87a7b381ef1d91d8326f76042` |
| `research_notes/58_one_child_pcfl_relay_v2_executable_contract.md` | `20cad18ac51f1ff81b44a491ceabf609b53eaff3bc5af70d486fd42429a281d9` |
| `research_notes/ICLR_2027_SUBMISSION_CRITICAL_PATH_20260907.md` | `d3b1edb3120c674863f673afc4827da526b99e6a9db3e2e22071f1ff611692e9` |
| `research_notes/56_pcfl_compression_feasibility_adjudication_v1.md` | `95429dea51764970dd6ba32ea517a0eb19c91bffcd96faeb4ef2ce62065db4cd` |
| `research_loop/advisory/20260907_one_child_pcfl_rate_distortion_design_v1.md` | `85a036c6f0244ca60652fe10e89ceb500e3bddd30bc69ef9b045abd8e0d3882e` |
