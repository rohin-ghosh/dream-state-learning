# One-child PCFL relay v4: independent final attack v1

Date: 2026-09-07

Status: **source-only independent advisory; no authorization**. This review
does not edit or supersede relay v2/v3/v4, ratify a design, implement code,
select or generate a child/root, run a model, build an adapter, use a GPU, or
authorize a scientific claim.

## Verdict

**REVISE.** The one-endpoint simplification is scientifically legitimate, the
`47/96` exact-binomial arithmetic is correct, and the proposed monotone
short-circuits and five-build alias graph can preserve the fixed-denominator
dual-chain estimand. However, v4 combines that bare endpoint test with a
same-confirmation-sample `TEXT_chain >= 66/96` gate and still calls
`.9016376315926115` the design's exact power. That is not the power of the
specified release procedure. At the inherited planning marginals
`P(TEXT_chain=1)=.75` and `P(R=1)=.55`, its exact gated power is only
`.867804286674669`. The proposal must either remove/relocate the 66-success
gate, report and accept the lower gated power, or repower the joint gate before
ratification.

No other hidden weakening of the successful-root scientific chain was found.
The remaining gates are demanding but not internally impossible on the bytes
reviewed. V4 is correctly labeled unbound and unauthorized; a successor must
bind the exact inherited v3 chain formulas and transaction-equivalence proof.

## 1. Source and arithmetic receipts

The reviewed v4 bytes have SHA-256
`997182641666c8e3a5c8252defdf0ee0eb2c88634c3b1d25d8c7f6b9ba0cd2dc`,
matching the requested digest. Its three cited advisory digests also match:

| source | SHA-256 read |
|---|---|
| relay v3 proposal | `6fc2d3dd4e9b779e76e6168a57424cb5e1cdeb6cff347ebb411b23ea6e4d00a2` |
| information/GPU-hour attack | `8c615314c6d099c202e80deebf4249468e9e39146e7c9348c148a034f2608c6d` |
| scope-efficiency attack | `36d88113403652dc8631b645fdeebff9fc425350ee2c8eeeede1d682f7029568` |
| power-simplification audit | `e5486edbe47ecfdd4543d45386ed367cee4ad82c21c43d277f4cc5788fc999fa` |

For the bare primary `H0: P(R=1)<=.40`, the first rejecting count at `N=96`
is indeed 47:

```text
Pr[Binomial(96,.40) >= 47] = .046706479040617
Pr[Binomial(96,.55) >= 47] = .9016376315926115
```

Count 66 is likewise the correct strict one-sided `.05` exact threshold for
`P(TEXT_chain)>.60`:

```text
Pr[Binomial(96,.60) >= 66] = .04837403208657833
Pr[Binomial(96,.75) >= 66] = .9344414934229096
```

The problem is composition, not either marginal calculation. Since
`R=TEXT_chain*LORA_chain`, the inherited planning marginals imply the unique
nested categories

```text
P(R=1)                         = .55
P(TEXT_chain=1, R=0)          = .20
P(TEXT_chain=0)               = .25.
```

V4 releases only on both `X_R>=47` and `X_TEXT>=66`. Exact multinomial
enumeration gives

```text
Pr[X_R>=47 and X_TEXT>=66] = .867804286674669,
```

with `.0338333449179464` probability mass where the registered `R` test would
pass but G1 suppresses it. If only `P(R)=.55` is registered, gated power is not
identified at all from that marginal; over nested laws it can be as low as
`.00414534415580139` when `TEXT_chain=R`. Thus `.9016376` may be described as
the marginal power of the bare H1 test, not as the power of v4's full pass
rule. For reference, retaining both gates at `N=112` with their exact critical
counts `X_R>=54` and `X_TEXT>=77` gives gated power `.904869300394127` at the
same `.55/.75` marginals, but choosing that repair is a new design decision.

## 2. Selection, stopping, and the fixed denominator

The proposed compute savings do not themselves introduce favorable-root
selection for the sole primary:

- TEXT executes on all 96 sealed roots. When TEXT fails, `R=0` is known by the
  registered product, regardless of the unobserved marginal LoRA outcome.
  Skipping LoRA there therefore creates no missing primary datum and does not
  support a marginal LoRA claim.
- Within a LoRA attempt, a prospectively ordered irreversible factor failure
  fixes the product at zero. Stopping that root and adverse-filling all later
  fields cannot convert failure to success.
- Processing TEXT-success roots in sealed order and stopping at 47 observed
  complete successes is exactly a computational evaluation of the fixed-96
  rejection event when every unexecuted root is recorded as zero. Stopping
  after 50 total primary failures, or when the remaining TEXT-success roots
  cannot reach 47, is exact futility.
- The 66-TEXT G1 gate is conservative for Type I error: the actual rejection
  event is a subset of `X_R>=47`. It does not create a false-positive or
  multiplicity defect. It does, however, alter power and must not be hidden
  behind the bare-binomial power number.

The execution contract should say explicitly that all unexecuted cells after
either success **or futility** receive the v3 field-specific adverse value,
and that unexecuted continuous diagnostics are marked unobserved rather than
presented as measured values. This is a receipt/wording repair, not a change to
the primary test.

## 3. Five-build aliasing and potential outcomes

The proposed collapse from eight named builds to five distinct LoRA
transactions preserves the v3 potential outcomes, subject to the byte-level
gate v4 already requires:

```text
AUTH_OLD_PAD : B_AUTH/C_AUTH/C_SHAM/C_REACH_PREFIX/
               D_NOWRITE/D_REACHOFF via fresh read-only clones
EDGE         : D_EDGE and D_SWAP via fresh read-only clones, with only the
               sealed read-time binding permutation in D_SWAP
DERANGED     : its own carrier build
NULL         : its own carrier build
SHAM         : its own carrier build
```

V3 requires deterministic kernels, a clean `A_CORE`, identical input ordering,
seed and optimizer state for the aliased members, and phase/arm isolation.
Under those requirements, rebuilding a byte-identical transaction adds a
training replicate, not a distinct intervention. A single immutable published
artifact plus a fresh process/mount/cache/RNG reset for every arm is the proper
coupled construction. `D_SWAP` remains a distinct potential-outcome arm
because its intervention occurs at READ, not BUILD.

The alias is invalid if any complete build input, seed, optimizer state,
software/kernel version, output bytes, intervention bytes, logical charges, or
reset law differs. V4's rule that semantic similarity alone never licenses an
alias is therefore necessary. Its identical-negative-call alias is also safe
only when the complete actor-visible input, intervention and RNG hashes match
prospectively and every carrier-named score/receipt remains printed.

## 4. Scientific content and claim boundary

V4 retains `R_r=TEXT_chain_r*LORA_chain_r` and explicitly imports the v3
failure-inclusive chain. On a root counted `R=1`, the v3 formula still requires
all of the following for both carriers: required truthful admitted rows and
exact reads; authentic connected use; deranged and truthful-null failure;
distinct goal-conditioned paths; target-blind, necessary-cut and closure
failure; binding-twin redirection; gap/two-hypothesis/pre-outcome-map emission;
authentic separating experiment and sham failure; truthful new-row admission;
delayed edge success; no-write, sham-write and reachout-off failure; D binding
redirection; all seven general named controls for both carriers; adapter-off
and wrong-life for LoRA; and the TEXT/LoRA same-semantics condition. The
deterministic root theorem,
truth-audit separation, reset and capability obligations remain study gates.
No component average or success on a different root can manufacture `R=1`.

Demoting the 72 component statements and the marginal TEXT/LoRA chain rates
removes their population floors, ceilings and SESOI claims; it does not remove
their root-level predicates from `R`. This is an honest narrowing of the claim,
not a weaker successful-root definition. The power-simplification advisory's
`N=112` recommendation applies when separate TEXT and LoRA population-rate
claims are retained; v4 explicitly declines those claims, so `N=96` is valid
for the bare dual endpoint.

The exclusions are appropriately candid. Even after a pass, the relay does
not identify parenting causality, a population of children, causal mediation,
compression or physical efficiency, a readable graph in weights, lifetime
learning-curve improvement, autonomous invention, LoRA-over-TEXT superiority,
or superiority to `ACTIVE_TEXT_FIXED`. The positive language should remain
"complete observed/intervention-tested relay chain" and conditional on the
one fixed child and frozen root distribution. Component diagnostics cannot
rescue a failed dual primary.

## 5. Minimum repair before deliberation

Choose and bind exactly one of these dispositions:

1. Keep fixed `N=96`, delete the same-sample `66/96` promotion gate, and stop
   before LoRA only when fewer than 47 TEXT roots leave H1 mathematically live;
   retain explicit-TEXT feasibility as a disjoint pre-confirmation DEV/resource
   gate. Then `.9016376315926115` is the exact primary procedure power at
   `P(R)=.55`.
2. Keep both `66/96` and `47/96`, register the joint nested planning law, and
   report `.867804286674669` as the full gated power, explicitly accepting
   that it misses the inherited `.90` planning objective.
3. Keep both scientific-sample gates and repower prospectively; for example,
   `N=112` clears `.90` at the inherited nested planning marginals, subject to
   a fresh exact receipt and resource decision.

The ratified successor must directly hash-bind the v3 source/formulas it
imports, freeze the alias-equivalence classes and within-root dependency order,
and state adverse-fill behavior for every early exit. Until then the current
candidate remains, as it says, unbound and unauthorized.

**Final disposition: REVISE.**

The SHA-256 of this advisory is reported externally after its final bytes are
written; it is not self-embedded.
