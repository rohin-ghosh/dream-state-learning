# Final skeptic audit: PCFL vertical DEV v2

**Date:** 2026-09-13 UTC  
**Role:** fresh independent final skeptic  
**Evidence cut:** `273bf42c` plus the current uncommitted worktree inventory  
**Scope:** design audit only. I changed no builder source, test, benchmark,
model, tokenizer, adapter, lineage, job, GPU allocation, threshold, or claim.

## Verdict: REWORK

The eight-world collision cube, child-span custody, atoms control, two readout
types, two-SLEEP chronology, candidate-free route scorer, and bounded DEV claim
are the right minimum experiment. I found no reason to return to Q0, add a rank
sweep, add parenting, or redesign the opaque route labels.

The document is nevertheless not implementation-ready. Two underspecified
boundaries can make a successful run non-causal, and one exact writer/readout
contradiction can make a sound mechanism fail for the wrong reason. These are
small protocol repairs, not a new ladder. The fit roster can remain fourteen.

## 1. Fatal: the training unit cannot implement the declared memory API

Section 8 makes two calls set-valued:

```text
READ EVENTS_AT <node_id>
READ LINKS_FROM <event_id>
```

and requires the complete sorted set in one response. This matters in the
actual world: `S_L` has two EVENTS, `B` has two EVENTS, `e3` has two outgoing
LINKs at S1, and `e1` has two outgoing LINKs after S2. Section 10 instead
creates eight wrapped examples **per individual child row**, with one physical
row as each target. Consequently the same address-level input either has two
different one-row targets or is never trained to emit the required multirow
answer. The advertised `12 rows x 8` / `15 rows x 8` arithmetic therefore does
not train the service that Sections 8 and 12 score.

This is not merely a likely negative result. It confounds writer failure with
an internally contradictory request/target relation.

### Minimal repair

Freeze a query-to-response materialization table before any fit:

- `READ EVENT e` targets exactly the one admitted EVENT span for `e`;
- `READ EVENTS_AT n` targets the exact concatenation of **all** admitted EVENT
  spans at `n`, sorted by event ID;
- `READ LINKS_FROM e` targets the exact concatenation of **all** admitted LINK
  spans from `e`, sorted by link ID; and
- absent addresses target exactly `MISS` only if `MISS` is intentionally part
  of the qualified writer. Otherwise unseen-address behavior remains an
  empirical refusal gate rather than a secretly supplied memory target.

Concatenation is thinker/compiler safe: the compiler adds no field and only
groups exact admitted child spans, an operation Section 3 already permits.
Bind the multirow separator and parser bytes. Every control must be matched at
the **query-response shape** level, not merely by the number of semantic rows.
For `S1_ATOMS`, LINK calls must have the prospectively declared no-link result;
neutral dose padding belongs under a disjoint never-called training request,
not as a fake response to `READ LINKS_FROM`.

After this materialization, recount examples, loss-active target tokens,
optimizer updates, and the profiled resource cap. Do not preserve `1,860`
updates merely because that number was in the prose. The number of fits need
not change.

## 2. Fatal: cross-SLEEP visibility does not yet distinguish memory from RAG

Section 3 says that when proposing a LINK the child “sees only previously
accepted public events.” That is safe during initial OLD formation, while
those events are still causally present in the child's ordinary active
context. It is not safe after S1 reset. If the harness reinserts the accepted
OLD EVENT table before the child authors `l4/l5`, the child can form NEW links
from an external textual ledger. S1 parametric memory is then unnecessary for
the claimed expansion seam.

### Minimal repair

Bind visibility separately by phase:

1. During initial OLD formation, the child may use prior events still present
   in its causal wake context.
2. After S1 and active-context reset, the native lineage receives only the
   ordinary goal/probe interface, its own newly generated thought state, the
   public probe outcome, the new executed-event receipt, and the same fixed
   target-free commitment request/grammar used at formation. No OLD receipt,
   admitted row, event roster, link roster, memory-service return, or compiler
   state is injected.
3. The mounted S1 child must itself reproduce any OLD identifier used in a NEW
   LINK. A separate mechanistic fork may use goal-blind local reads, but every
   raw return must be logged and that fork must not become the native lineage.
4. The two R continuations restore the exact same sealed native pre-outcome
   child state; only the ordinary public result differs.

Without this phase-specific contract, a pass supports “RAG-assisted child
serialization followed by LoRA transport,” not autonomous knowledge
expansion.

## 3. Fatal for the expansion claim: reachout has no frozen endpoint or
memory-causality contrast

Section 12.2 says only “from the untouched S1_AUTH state.” It never decides
whether the lineage action is emitted by the native mounted child or by the
clean actor plus memory service. It also drops the predecessor audits'
requirement that the exact text/graph ceilings solve the reachout endpoint and
that no-memory shortcuts stay at chance. The current zero-fit table scores
only delayed routes.

The collision cube proves equal outcome entropy. It does not prove that S1
memory caused the child to choose the useful probe. A surface policy can pass
eight repeated renders unless the order/cue controls and an actual no-memory
contrast are frozen. Moreover both current future goals (`G_R0` and `G_R1`)
make the same `H -> S_R` probe useful, so this world does not identify a claim
that the **choice of experiment changes with the goal**.

### Minimal repair

- Make the single lineage-entering reachout a one-shot action by the native
  mounted `S1_AUTH` child from the sterile post-S1 context described above.
- Run a read-only mechanistic reachout panel with the clean actor plus the
  S1_AUTH service. On that panel, prospectively cut the critical OLD event
  group, and run OFF and wrong-root controls. These cost inference, not fits.
- Restore reachout to the four excluded-root zero-fit closure: exact graph,
  full child text, and active linked text must pass; NONE/OFF, wrong-root, and
  every registered order/ID/fixed-choice projection must remain at its frozen
  ceiling. Bind the eight-view probe-order balance exactly.
- Define `VS_REACHOUT_FAIL` as failure of the native primary or of the
  mechanistic memory-dependence gate, rather than allowing one endpoint to
  compensate for the other.
- For this DEV, say **task-relevant expansion after a revealed goal**, not
  “goal-conditioned experiment selection.” Goal-conditioned traversal is
  still tested by the old-route goal swaps. If changing the experiment with
  the goal is required, the world needs a second goal for which the other
  probe is useful; that is a material construct expansion and is not needed
  for the minimum claim.

## 4. Implementation-blocking control ambiguities

These require exact disposition but no additional fitted arm.

### `S1_ATOMS`

The universal LINK-read gate in Section 12.1 cannot apply to `S1_ATOMS`, which
has no LINK target. Declare its LINK result (`MISS` or a registered refusal),
and state whether ATOMS may spend the same twelve reads composing from EVENTs.
The comparison must use identical actor budgets.

Define the link-added-value estimand explicitly:

```text
Delta_link_service = route(S1_AUTH service) - route(S1_ATOMS service)
Delta_link_native  = route(S1_AUTH native)  - route(S1_ATOMS native)
```

Service-only success permits “stored links improved the tested parametric
memory service.” Native added-value language requires the native delta too.
Otherwise retain `EVENT_COMPOSITION_ONLY`. A bare `AUTH - ATOMS` has no
defined endpoint in the current document.

### Artifact custody

Section 11 says synthetic control adapters and corpora are “destroyed after
scoring,” while Sections 14–15 require immutable sealing, one reduction, fit
hashes, and evidence preservation. Destruction prevents independent replay and
contradicts the custody contract. Replace it with: controls are immutably
sealed and quarantined from authentic lineage, retained through reduction and
claim closure, and archived or deleted only under a separately logged
retention policy. Quarantine, not deletion, supplies contamination safety.

### Lifetime language

Section 16 calls `SLEEP_FROZEN` an “identical THINK history.” That is
impossible in an on-policy comparison once mounted memory changes actions.
Freeze identical starting checkpoint, opportunity schedule, random tape,
budgets, and shadow SLEEP transaction; let each arm own its resulting history.
Reserve “same history” for the separate inference-only carrier table. This
does not alter DEV, but it must be corrected before DEV is allowed to release
the lifetime campaign.

## 5. What does *not* need repair

- `EVENT` and `LINK` are admittedly derivable from receipts and endpoints.
  `S1_ATOMS` plus the narrowed branch label handles this honestly.
- The two R branches are nested counterfactual continuations, not independent
  roots. The document already treats them that way.
- Two DEV roots are debugging units, not a confidence interval.
- Clean-base cumulative S2 fitting is a legitimate replay-based second SLEEP;
  it need not warm-start from S1 weights if the architecture's frozen writer
  is cumulative reconstruction.
- The native endpoint need not prove separate parameter-level OLD and NEW
  mediation in DEV; the current disclaimer is correct.
- Compression, parenting, rank/plasticity sweeps, and long-lifetime
  superiority remain downstream.

## 6. Strongest permitted claim after the repairs

If both DEV roots pass every unchanged gate after these repairs, the strongest
honest statement is:

> In two development worlds, a scaffolded child converted its own public
> action/outcome receipts into exact typed commitments that a rank-8 personal
> write carried after context reset. Candidate-free local reads and the native
> mounted child supported goal-conditioned route traversal. The native child
> then selected a predeclared task-relevant experiment, authored new
> commitments from the public result without textual OLD-memory reinjection,
> retained OLD competence through a cumulative second write, and solved
> one-shot tasks whose generator made OLD and NEW jointly identifying.

Append “stored LINK organization added value” only for the endpoint(s) on
which the prospectively defined AUTH-minus-ATOMS contrast passes. Otherwise
say EVENT composition. This remains a two-root mechanism-development result:
no frequency, lifetime improvement, memory-baseline superiority, compression,
autonomous memory initiation, parenting, or native parameter-mediation claim.

## Release ruling

**REWORK, then implement.** The shortest acceptable successor is a patch to
the existing v2 design resolving the query-group writer, post-S1 visibility,
reachout endpoint/controls, ATOMS estimand, artifact retention, and lifetime
wording. It does not require another broad deliberation, a new diagnostic
ladder, more than fourteen fits, or any change to Q0/L1 scheduling.

---

## Re-audit addendum: v2.1 at `29bcd1ed`

**Re-audit verdict: REWORK (one causal-control repair, two exact wording
repairs).** The patch resolves the six requested defects in substance, and its
full-arm query counts and arithmetic are correct. It introduces one new
control treatment that must be removed before implementation: address-specific
synthetic `MISS` targets.

### Repair-by-repair verification

1. **Query-level writer/readout alignment — resolved for AUTH/full arms.**
   `READ EVENT` now targets one exact child span; `READ EVENTS_AT` and
   `READ LINKS_FROM` target complete sorted concatenations with a bound LF
   separator. For S1, `8` individual EVENT calls + `6` distinct source-node
   calls + `3` distinct link-source calls = **17**. For S2, adding `e8` gives
   `9` individual EVENT calls, still `6` source nodes because `e8` shares `H`,
   and `4` link sources because `e8` is new = **19**. These counts are exact.
2. **Post-S1 visibility — resolved.** The native continuation is sterile and
   the fixed target-free grammar is the only formation scaffold. OLD IDs in
   NEW links must come from the mounted child; the service fork cannot enter
   lineage.
3. **Reachout endpoint and causality — resolved at DEV scope.** The primary is
   explicitly one-shot native. The eight-view native and service panels, old
   cut, OFF, wrong-root, and excluded-root zero-fit reachout closure are
   noncompensatory. `7/8` versus controls `<=4/8`, with a `>=3/8` delta, is
   arithmetically coherent. The claim is correctly narrowed to task-relevant
   expansion, not goal-switched experiment choice.
4. **ATOMS estimand — structurally resolved.** Service and native deltas are
   now distinct, budget-matched estimands; endpoint-specific language is
   correct. The particular trained-MISS construction still needs repair below.
5. **Artifact custody — resolved.** Controls are sealed and quarantined, not
   destroyed.
6. **Lifetime history language — resolved.** On-policy arms own divergent
   histories; only the inference-only carrier table is same-history.

The 20-slot arithmetic is also correct as optimization arithmetic:

```text
20 slots x 8 views = 160 examples/epoch
160 / batch 4 x 5 epochs = 200 updates/fit
14 fits x 200 = 2,800 updates
14 fits x 30 A40-minutes = 420 A40-minutes = 7 A40-hours
```

### Remaining causal-control defect: do not teach false absence at treatment
addresses

`S1_ATOMS` is now explicitly trained to emit `MISS` for the three authentic
link-source addresses. `S2_OLD_REPLAY` is trained to emit `MISS` for addresses
of the future NEW event. Those are not neutral equal-work controls:

- ATOMS learns an explicit false/no-link disposition exactly where AUTH learns
  true links. AUTH-minus-ATOMS can therefore be caused by negative-target
  poisoning rather than added value from stored links.
- OLD_REPLAY receives future NEW address identities and is explicitly taught
  absence there. FULL-minus-OLD_REPLAY can therefore be caused by a
  future-address negative map rather than acquisition of NEW semantics. This
  is especially avoidable because neutral padding already equalizes examples
  and loss-active tokens.

The compiler also selects these negative targets using the very addresses on
which the later causal evaluation is performed. Presealing them does not make
them ordinary old replay.

**Minimal repair:** do not train address-specific `MISS` in either causal
control. Materialize:

```text
S1_AUTH/TWIN/PERMUTE: 17 scored query blocks + 3 PAD = 20
S1_ATOMS:              14 EVENT query blocks + 6 PAD = 20
S2_FULL_R0/R1:         19 scored query blocks + 1 PAD = 20
S2_OLD_REPLAY:         17 OLD query blocks + 3 PAD = 20
```

At evaluation, missing LINK/NEW addresses are held-out calls. Score exact
`MISS` if produced, but the noncompensatory requirement should be **zero usable
false rows**; do not require exact `MISS` unless a generic refusal curriculum
is supplied identically to every arm at non-treatment addresses and reported
as a common interface scaffold. ATOMS may use all twelve reads to compose from
EVENTs. OLD_REPLAY may only use OLD returns. All target-token deficits remain
filled in the parser-disjoint PAD requests, so the fit count, 20 slots, 200
updates/fit, 2,800 total updates, and 17-hour cap remain unchanged.

This repair changes the table headers from fixed `17/19 scored` for every arm
to the per-arm counts above; the manifest must bind actual scored and PAD
counts.

### Two exact wording repairs

1. Section 14's “profile one S1 and one S2 fit” must say these are the first
   registered fits inside the fourteen-fit roster, retained as scientific
   roots if they complete. No disposable profiling fits exist outside the
   `14` / `2,800` / `7 A40-hour` cap.
2. Section 17 currently both says exact materialization failure stops as
   `VS_ASSAY_INVALID` and suggests switching to per-token loss weights. Bind
   the former for v2.1: no weighted-loss fallback is allowed inside this
   version. Any such fallback requires a newly versioned prospective design.
   Also require stage-total target-token equality, not obsolete per-row
   equality, because grouped blocks intentionally have different lengths.

### Final disposition

After removing treatment-address `MISS` targets and applying the two wording
repairs, **PASS**. I found no new leakage, thinker/compiler crossing, invalid
unit, arithmetic error, missing native endpoint, infeasible added fit, or
claim expansion. The strongest permitted claim remains Section 6 above.

---

## Final re-audit addendum: v2.1 at `2ae2c62b`

**Verdict: PASS.**

The remaining causal-control defect is removed without changing the
scientific fit roster or resource ceiling:

- S1 full arms contain exactly `17` semantic blocks + `3` PAD; ATOMS contains
  exactly `14` EVENT-bearing blocks + `6` PAD.
- S2 FULL contains exactly `19` semantic blocks + `1` PAD; OLD_REPLAY contains
  exactly `17` OLD blocks + `3` PAD.
- ATOMS LINK addresses and OLD_REPLAY NEW addresses are held out. Neither arm
  is trained on a false `MISS`. Exact refusal is reported if generated; the
  causal safety gate is zero usable false rows.
- All arms still have `20 x 8 = 160` examples per epoch, `200` updates per fit,
  `14` fits, and `2,800` total updates. Parser-disjoint padding, not a semantic
  negative, equalizes active target tokens.
- Per-token weighting, approximate work matching, duplicated semantic calls,
  and false-MISS fallback are prohibited in this version.
- The profiled `S1_AUTH` and `S2_FULL_R0` are registered scientific fits inside
  the fourteen-fit cap; there are no disposable profile fits.

The full-arm query counts independently recompute: S1 is `8 READ EVENT + 6
READ EVENTS_AT + 3 READ LINKS_FROM = 17`; S2 is `9 + 6 + 4 = 19` because the
new event shares source node `H` but adds one individual EVENT address and one
LINK-source address. ATOMS removes the three LINK blocks; OLD_REPLAY removes
the two NEW-dependent address blocks and retains the seventeen OLD blocks.

The post-S1 native visibility contract, reachout ceilings and causal cuts,
endpoint-specific AUTH-minus-ATOMS estimands, artifact retention, and
on-policy lifetime wording remain intact. I found no remaining fatal leakage,
shortcut, thinker/compiler crossing, invalid causal claim, missing baseline/native
endpoint, unit error, arithmetic error, or infeasible extra fit.

One non-blocking editorial singular remains: Section 11.1 says “The three
stage-level padding responses,” although ATOMS has six. Implement from the
explicit per-arm table; changing that phrase to “The registered stage-level
padding responses” would remove the typo but does not alter or block the
protocol.
