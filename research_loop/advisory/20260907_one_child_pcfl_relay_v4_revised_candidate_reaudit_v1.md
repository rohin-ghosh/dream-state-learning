# One-child PCFL relay v4 revised candidate: independent re-audit v1

Date: 2026-09-07

Status: **source-only independent advisory; no authorization**. This review
does not edit or supersede relay v2/v3/v4, ratify a design, implement code,
select or generate a child/root, run a model, build an adapter, use a GPU, or
authorize a scientific claim.

## Verdict

**PASS as an unbound information-efficient architecture candidate; NOT
AUTHORIZED for execution.** The revised bytes remove the same-confirmation
`66/96` TEXT gate that caused the prior power defect. Conditional on the
disjoint DEV gate passing and confirmation opening, the sole stochastic
confirmation release event is now exactly `x_R>=47` among 96 fixed roots. Its
reported null tail and `.55` power are exact. TEXT-first execution,
LoRA-only-on-TEXT-success, within-root failure short-circuiting, and early
success/futility are monotone evaluations of that fixed-denominator event and
do not create outcome selection or another confirmation threshold.

The eight-root DEV gate does affect whether the optional confirmation study is
ever opened, but v4 states this explicitly and correctly limits `.9016376` to
confirmation-decision power conditional on opening. It neither pools DEV roots
nor changes `N`, the critical count, prompts, adapters, endpoints, or any other
scientific choice. Under the fixed-child iid/disjoint-root contract, conditioning
on this DEV gate does not change the exact confirmation test.

No hidden stochastic confirmation gate, impossible stopping rule, material
resource-arithmetic error, or scientific-chain weakening remains in the
reviewed source. The candidate's own governance, implementation, receipt,
review, resource, and run-authorization gates remain genuinely open.

## 1. Source receipts

The revised candidate's SHA-256 is
`38f1212c8a2fe9197b4fee69f564134fc571f4cf690e1deeee8ab279c6bb571f`,
matching the requested digest.

| source | SHA-256 read |
|---|---|
| relay v3 proposal | `6fc2d3dd4e9b779e76e6168a57424cb5e1cdeb6cff347ebb411b23ea6e4d00a2` |
| information/GPU-hour attack | `8c615314c6d099c202e80deebf4249468e9e39146e7c9348c148a034f2608c6d` |
| scope-efficiency attack | `36d88113403652dc8631b645fdeebff9fc425350ee2c8eeeede1d682f7029568` |
| power-simplification audit | `e5486edbe47ecfdd4543d45386ed367cee4ad82c21c43d277f4cc5788fc999fa` |
| prior v4 final attack | `4fc8a3b798dfd7b1e9a73a3e1be8436453b10817eb72ecafa521bab69659b1d6` |

## 2. Exact confirmation statistics and DEV scope

For the sole confirmation hypothesis

```text
H0: P(R=1) <= .40
N = 96
reject iff X_R >= 47,
```

direct binomial enumeration gives

```text
Pr[Binomial(96,.40) >= 47] = .046706479040617
Pr[Binomial(96,.55) >= 47] = .9016376315926115.
```

Thus 47 is the first strict one-sided `.05` rejecting count and the stated
`.55` confirmation power is correct. There is one confirmation endpoint and
no confirmation-sample TEXT floor, marginal LoRA claim, component promotion
family, nuisance pilot, copula, adaptive `N`, or extension. Multiplicity and
cross-endpoint dependence machinery are unnecessary for this claim.

The full process has two stochastic stages:

```text
DEV_GO = 1[X_TEXT,DEV >= 6 and X_R,DEV >= 4]
CONFIRM_PASS = 1[X_R,CONF >= 47]
PROGRAM_RELEASE = DEV_GO * CONFIRM_PASS,
```

plus deterministic/integrity gates. V4 does not call `.9016376` the
unconditional `PROGRAM_RELEASE` power. This distinction is important and is
now stated correctly. At the inherited illustrative nested planning marginals
`P(TEXT_chain)=.75` and `P(R)=.55`, exact enumeration gives

```text
Pr(DEV_GO) = .590492690820313
Pr(PROGRAM_RELEASE) = .532410431223975
```

when DEV and confirmation roots are independent conditional on the fixed
child. These numbers are not acceptance targets and need not appear in v4,
but they show the practical cost of the intentionally strict resource gate.
The gate is not hidden and is not inferential evidence. If a future packet
wants a high unconditional probability of reaching a claim, it must power
that larger two-stage objective separately; that is not the estimand selected
here.

The conditional exact test remains valid because the child is already fixed,
the DEV and confirmation identities are disjoint, all 96 confirmation
identities and their order seal before exposure, and DEV is forbidden to alter
any confirmation choice. A DEV failure yields no confirmation and no claim;
it does not trigger new DEV roots, a replacement child, a redesigned threshold,
or a favorable confirmation bank.

## 3. Short-circuit and stopping proof

The confirmation computation preserves the fixed-96 event:

1. TEXT runs on all 96 roots. Because `R=TEXT_chain*LORA_chain`, every
   TEXT-failed root has known `R=0` under every unobserved marginal LoRA
   potential outcome. Skipping its LoRA branch therefore creates no missing
   primary datum and cannot support a marginal LoRA claim.
2. For a TEXT-success root, LoRA runs in the presealed order. Once a required
   positive, cut, twin, mismatch, chronology, provenance, truth-audit, or
   negative-control factor fails irreversibly, the conjunction is permanently
   zero. Field-specific adverse fill and stopping cannot manufacture `R=1`.
3. Reaching 47 literal successes permits success with every unexecuted root
   assigned zero. This is the ordinary fixed-N rejection event, not an interim
   boundary with a second alpha spend.
4. Fifty accumulated primary failures leave at most 46 successes among 96.
   Equivalently, after TEXT is complete, futility holds exactly when current
   successes plus unattempted TEXT-success roots is below 47. The two v4
   futility descriptions are consistent, not competing rules.
5. Every `R=1` root still executes every retained v3 mediator, intervention,
   carrier and named control for both carriers. Early stopping saves work only
   on roots already fixed at zero or after the study's fixed rejection event
   is logically determined.

Repository/hash/capability violations invalidate the study rather than
selectively adverse-filling it; this is an integrity condition, not a second
scientific success route. Ordinary missing or post-exposure technical failures
remain adverse zeros as stated.

## 4. Resource arithmetic

The quoted baseline is arithmetically correct:

```text
(320 confirmation + 32 nuisance-pilot roots) * 8 builds = 2,816 builds.
```

At the inherited confirmation planning marginals,

```text
E[TEXT successes] = 96 * .75 = 72
72 attempted roots * 5 distinct builds = 360 builds
47 / (.55/.75) = 64.0909 attempted roots
64.0909 * 5 = 320.4545, approximately 321 builds.
```

The resulting reductions are `1-360/2816=.87216` and
`1-321/2816=.88601`, supporting the stated approximate 87--89% confirmation
build reduction. The 321 figure is a simple negative-binomial planning
heuristic. Exact finite-boundary enumeration gives about `63.03` attempted
LoRA roots, or `315.16` five-build opportunities, unconditionally at the same
planning law; conditional on eventual confirmation success it gives about
`63.33` roots, or `316.65` opportunities. These small differences make v4's
rounded 321--360 range conservative rather than materially wrong.

The planning expectation is not a resource ceiling. Up to 96 confirmation
roots can require LoRA attempts, so the pre-run ceiling must be capable of 480
distinct build transactions, plus the separately reported eight-root DEV cost
of up to 40. V4 does not claim otherwise and leaves the exact resource/run
authorization open. Excluding DEV from the 87--89% confirmation comparison is
fair because v3 also retained a separate eight-root DEV set; the deleted 32
roots were the scientific nuisance pilot and are properly included only in the
v3 baseline.

## 5. Remaining boundaries

The five-build transaction alias remains valid only under v4's exact
input/seed/optimizer/output/software/mount/clone equivalence and fresh
read-only process isolation. `D_SWAP` remains a distinct read-time potential
outcome of the shared `EDGE` bytes. No semantic-only alias is permitted.

The maximum scientific statement remains an observed/intervention-tested
same-root dual-carrier relay rate conditional on one fixed child and the
registered root distribution. Demoted component rates cannot rescue the
primary. The source correctly excludes causal mediation, parenting causality,
compression, a graph readable inside weights, lifetime improvement,
autonomous invention, LoRA-over-TEXT superiority, and superiority to
`ACTIVE_TEXT_FIXED`.

Before any ratified successor executes, it must directly bind the exact v3
chain formulas it imports, freeze the DEV/confirmation disjointness proof,
alias equivalence classes, adverse-fill ledger and dependency order, and clear
every remaining governance and authorization gate listed by v4. These are
prospective closure obligations, not defects in this unbound candidate.

**Final disposition: PASS as an unbound candidate; no execution authority.**

The SHA-256 of this advisory is reported externally after its final bytes are
written; it is not self-embedded.
