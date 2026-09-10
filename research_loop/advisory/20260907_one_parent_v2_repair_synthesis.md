# One-parent/one-child v2 repair synthesis

Date: 2026-09-07

Status: **proposal-only synthesis**. This memo changes no bound protocol,
workflow, manuscript, implementation, benchmark, model, tokenizer, adapter, or
GPU state. It authorizes none of those operations. Adoption requires a new
source-bound architecture-deliberation workflow and exact human ratification.

## Decision preserved

The experiment has one topology:

1. one reset, frozen, target-blind parent teaches one child process-level
   thinking through practice tasks and thought-to-action correction;
2. the child must apply a correction on a fresh homologous task and the public
   world, not the parent, decides whether that continuation is writable;
3. the parent, correction text, nursery state, and all prohibited childhood
   artifacts disappear before deployment;
4. the parented child is deployed with Think--Dream--Sleep and one personal
   per-life LoRA; and
5. its public comparison is an equally provisioned frozen-parameter
   active-memory agent.

There is no classroom, cohort, peer exchange, teacher ensemble, stateful parent
across children, shared memory, or population-learning mechanism. Independent
roots are isolated replications of the same one-parent/one-child topology.

## Why v1 should not be ratified unchanged

Three independent 2026-09-07 audits agree that the topology is sound but the
scientific contract is not yet exact:

- `20260907_manuscript_protocol_consistency_audit_v1.md`: the manuscript
  prematurely calls active text validated, does not print the registered
  gain-AUC primary exactly, and promises undefined secondary endpoints;
- `20260907_one_parent_statistics_attack_v1.md`: the root population and seed
  coupling are undefined, the joint SESOI/power rule is incoherent at a true
  effect of .05, and a positive interaction can occur while writes still harm
  the parented child; and
- `20260907_objective_coverage_audit_v1.md`: the headline can test parenting by
  per-life writes, but CompilerGym behavior alone does not establish connected
  or compressed knowledge inside the LoRA, goal-directed graph traversal, or
  absolute superiority over a baseline at its own plateau.

Therefore workflow
`one_parent_child_headline_v1.deliberation.json` remains a preserved proposal
artifact, not the workflow to ratify or implement. Its zero-attempt state must
remain untouched. A v2 workflow should bind v1 plus the exact repairs below.

## V2 repair A: exact causal and statistical object

### A1. Root population

A confirmation root is one iid draw from a hash-bound root packet distribution
`Q`, conditional on the frozen child checkpoint, frozen reset parent policy,
writer, active-text policy, software, and registered CompilerGym universe.
Each root receives an independently sampled deployment deck of 48 unique wake
programs and eight unique probe programs, without replacement within the root
and disjoint within that root. P0/P1/U0/U1/R0 receive the same assigned deck
and order inside the root. Program identities may recur across roots only as
independent draws from the sealed universe.

One root contributes exactly one row containing all five services and the
derived root statistics. Programs, probes, cuts, continuations, actions,
targets, fits, and decoding samples are repeated measures and never enlarge
`n`. Claims are conditional on one fixed parent policy and one fixed child
checkpoint; roots estimate life/task-realization variability, not variation
over parents or base models.

### A2. Counter-keyed randomness and restart law

Every stochastic event derives its key from

```text
(experiment_hash, split, root_id, domain, matched_opportunity_id,
 stage, call_slot, sample_index, purpose)
```

`domain` separates task/deck generation, actor sampling, parent sampling,
writer order/initialization, environment, active-text update, retrieval, and
probe evaluation. Matched potential calls omit the arm label and share the
same `matched_opportunity_id`; treatment-only calls use a disjoint `purpose`
and cannot advance a global stream. Receipts must show the resolved key and
that the backend honored it.

All confirmation roots and execution order are prebound. A root is never
replaced after any response or outcome exists. Resume is allowed only from a
hash-committed pre-request boundary proving that no continuation or action was
created. Backend/hardware nondeterminism is one realization inside the root,
not a retry permission.

### A3. Exact outcome and cut timing

For service `c`, root `r`, and cut `t in {0,16,32,48}`, `V_c,r(t)` is the mean
over the root's same eight probe programs of the best nonnegative IR reduction
produced under the fixed generated-token budget. A missing or non-dispatched
valid action contributes zero. Cut 0 is evaluated from the exact common P or U
checkpoint before any deployment event; cuts 16/32/48 are evaluated only after
the corresponding active-text updates and the write-on service's committed or
quarantined SLEEP candidate. Probe bytes never return to life.

Define `G_c,r(t)=V_c,r(t)-V_c,r(0)` and

```text
gAUC_r(c) = [2*G_c,r(16) + 2*G_c,r(32) + G_c,r(48)] / 6
W_P,r     = gAUC_r(P1) - gAUC_r(P0)
W_U,r     = gAUC_r(U1) - gAUC_r(U0)
D_r       = W_P,r - W_U,r
C_public,r = gAUC_r(P1) - gAUC_r(R0)
L_terminal,r = V_P1,r(48) - V_P1,r(0)
T_R0,r       = V_P1,r(48) - V_R0,r(48)
```

`D` on gain-AUC is the sole primary endpoint. Pointwise curves are descriptive
decompositions, not alternative primaries.

### A4. Fixed claim hierarchy

Use two-sided 95% root-level Student-t intervals, intention-to-treat roots,
and a fixed sequence that stops at the first failed rung:

1. `mean(D)>0` and the point estimate is at least .05: this parent protocol
   changed the later benefit of personal writes;
2. `mean(W_P)>0` and the point estimate is at least .05: deployment writes were
   beneficial, not merely less harmful, in the parented child;
3. `mean(L_terminal)>0` and the point estimate is at least .05: P1 improved in
   absolute value over its finite life;
4. `mean(C_public)>0` and the point estimate is at least .05: the full P1
   package gained more from deployment than R0; and
5. `mean(T_R0)>0` and the point estimate is at least .05: P1 ended above R0 in
   absolute task value.

This fixed sequence controls the family for the five released superiority
sentences. A favorable later statistic cannot rescue a failed earlier rung.
In particular, P1--R0 is a full-package public contrast, never the parenting
effect.

The .05 threshold is a minimum observed practical effect on the normalized IR
reduction scale, not the effect at which the study is claimed to have 80%
power. Before roots are opened, development must justify it against the
floor-to-search-reference span. Power calculations must simulate the complete
joint interval-plus-estimate rule at a stated design alternative greater than
.05, using the frozen bounded-outcome reducer. If maximum feasible `N=32`
cannot reach the stated operating characteristics, call the result
precision-limited rather than powered. The v1 adaptive SD rule is not reused
without an exact simulation, variance-bound equation, and complete routing
table.

### A5. Failure and non-erasure

Every prebound root is present in the one-row-per-root table. Invalid or absent
probe actions score zero; a missing cut scores zero for that service/cut and is
flagged. Quarantined writes keep the previous active adapter but remain assigned
outcomes. Root exclusion, target-yield matching, and seed replacement are
forbidden.

Before confirmation, bind numeric margins and reducers for strict typed
routing, typed-forced proposal quality, DREAM publication/restoration, generic
behavior, and task action cardinality. These are required safety/non-erasure
gates, not additional favorable endpoints. Undefined early-slope, backward-
retention, forgetting, or broad forward-transfer claims are removed from the
abstract unless their exact panels and reducers enter the v2 source binding.

## V2 repair B: local plateau and public outperformance

Never use bare `saturation`. The only eligible statement is a **registered
local plateau under this 48-program resource envelope**.

The public plateau comparator is preselected as R0. Define

```text
s1_R0,r = V_R0,r(32) - V_R0,r(16)
s2_R0,r = V_R0,r(48) - V_R0,r(32).
```

The local-plateau sentence is released only if both separate two-sided 95%
intervals lie wholly inside the prebound equivalence band, the cognition-hidden
10,000-sequence search reference remains at least .10 above R0 at cut 48,
`T_R0` passes rung 5, P1's last-era increment has a positive one-sided 95%
lower bound, and the P1-minus-R0 last-era increment has a positive one-sided
95% lower bound with point estimate at least .05. Failure permits curves and
resource frontiers only. This does not identify representational saturation or
general saturation of active memory.

P0 may receive the same descriptive plateau reducer because it is the
parent-matched write-off cell, but it cannot be substituted after results are
seen for the preselected public R0 claim.

## V2 repair C: experiential objects and zero-call diagnostics

Define from immutable live artifacts:

- `OWN_OBSERVATION`: a same-service non-probe native action and public outcome;
- `SUPPORTED_UNIT`: a nonsuperseded live active-text record whose cited own
  observations all precede the scored query;
- `AUTHENTIC_LINK`: a directed link between live supported units committed
  before the query;
- `TRAVERSED_LINK`: an authentic seed-to-target link for which both complete
  records were actually returned before the scored action; and
- `EXPANSION(t)`: counts of supported semantic keys, cross-program units,
  authentic links, and subsequently used units at each registered cut.

These failure-inclusive counts operationalize the complete agent's textual
experience layer. They do not prove a graph inside the LoRA or child-directed
expansion.

For compression, construct a deterministic `EXPANDED_EQUIVALENT` for each live
compact record set: all observation-level typed instances needed to reproduce
the same denotation, scope, status, links, and provenance. Verify exact reducer
equality and charge complete UTF-8 bytes and pinned tokens for schemas,
dictionaries, IDs, provenance, links, indices, renderer, and expansion
machinery. Report the retained raw ledger separately. A short actor-facing code
is not a complete-system storage reduction while the raw ledger remains.

The rate and functional non-loss thresholds must be frozen after development
and before scientific records. A fixed LoRA rank or record-size cap is not
evidence of compression.

## V2 repair D: replace the optional batch comparator

Replace the optional descriptive `LEAFE_STYLE_FINAL` allocation with two
prebound terminal diagnostics after headline root count and primary artifacts
are immutable:

1. `P1_LINK_DERANGED_READ` uses no fit. It preserves seed ranks, record
   inventory and non-link fields, link count/degrees/types/scope/status,
   returned-document count and token bucket, then applies a no-fixed-point link
   derangement in a read-only cloned terminal store. Under common-RNG terminal
   probes, intact P1 must beat the derangement and receipts must show that the
   authentic target was returned before action. This can support connection and
   goal-conditioned one-hop traversal in the explicit active-text layer only.
2. `P1_FIXED_HISTORY_ACTION_OUTCOME_DERANGED_WRITE` uses one clean-base
   terminal fit. It deranges complete outcome+score bundles across action
   blocks within root, era, and normalized action family, then reruns the
   unchanged writer law, fixed slots, rehearsal fills, anchors, optimizer, and
   transactional gates. Intact P1 superiority can show that correct personal
   action--outcome binding matters to terminal compilation on a fixed authentic
   history. It does not establish connection or compression.

These replace rather than accompany the optional batch comparator: at most 128
terminal calls, 16,384 generated output tokens, and one fit/root versus its
160-call, 45,056-token, one-fit allowance. Neither diagnostic affects root
count, eligibility, or the headline contrasts.

## What remains a separate controlled mechanism assay

CompilerGym cannot identify connected/compressed knowledge **inside the
LoRA**. That claim requires a separately sealed compositional carrier panel
with compact linked, denotationally equivalent expanded linked, atoms-only,
degree/marginal-preserving binding derangement, and leave-one-necessary-bridge-
out carriers; same-corpus active text, adapter-off, and wrong/twin-life controls;
and one frozen resolver under byte-identical decision supervision.

This panel is a second experiment, not another childhood or population. It may
reuse the already developed controlled-world/PPC machinery after a fresh
shortcut/leakage audit. It must be designed and powered separately and may not
rescue a failed parenting/lifetime headline. Without it, the paper must say
only that the complete system formed a shorter connected actor-facing textual
code and that repeated outcome-gated LoRA writes improved action; it may not
say the adapter itself contains a connected graph.

## Manuscript corrections after ratification

- Call `ACTIVE_TEXT_FIXED` a prospectively fixed candidate until all once-only
  strength certificates pass; say each service has the same frozen policy but
  an isolated on-policy store.
- Print exact gain-AUC and `D`; lead figures/results with the four-cell
  interaction. A P1-versus-R0 figure is the public full-package illustration.
- State the closed three-code parent surface and fresh-task/public-world
  admission, not unconstrained “process-level credit assignment.”
- State the full fresh-process deletion audit and fixed-slot clean-base writer.
- Distinguish one-parent/one-child topology from many independent stochastic
  life/task roots under one fixed parent/child policy pair.
- Use singular “strong active-memory comparator” unless another named method
  is actually implemented prospectively.
- Delete undefined secondary endpoints rather than inventing them after data.

## Next gate

The next valid external deliberation input is a v2 workflow binding:

1. the latest Rohin directive fixing the one-parent/no-classroom topology;
2. the v1 plan and active-text contract as preserved base proposals;
3. the three independent 2026-09-07 audits; and
4. this repair synthesis.

No implementation or scientific-root execution may begin until five-role
deliberation reaches consensus, exact bytes/scope are ratified by Rohin, CPU
fixtures pass, and fresh independent implementation/scientific reviews pass.
