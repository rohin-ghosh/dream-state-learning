# One-parent/one-child headline protocol v2 addendum

Date: 2026-09-07

Status: **proposal only**. This file authorizes no implementation, target or
benchmark generation, model/tokenizer call, adapter fit/mount, GPU use,
external access, manuscript claim, or scientific-root spend.

If later deliberated and exactly ratified, this addendum modifies
`one_parent_child_headline_v1.md` only where it says so. All other v1 and
`active_text_fixed_contract_v1.md` bytes remain candidate requirements.

## 1. Immutable topology

One reset frozen target-blind parent policy teaches one child process-level
thinking through tasks and thought-to-action correction. The child must apply
the correction on a fresh homologous task; public-world predicates admit or
reject the child continuation. The parent then disappears completely. The
child enters deployment with Think--Dream--Sleep and its own per-life LoRA.

The U child is an isolated counterfactual branch with no edge to the P dyad.
There is no classroom, cohort, peer exchange, teacher ensemble, shared child
state, stateful parent across children, or population-learning mechanism.
Independent roots are isolated task/life realizations of this same topology,
not different parent policies or base-model identities.

The public system illustration is P1 versus R0. “Equally provisioned” means
equal ordinary **deployment** affordances only. R0 intentionally receives no
P/U childhood checkpoint or fitting compute; therefore P1--R0 is not an
equal-total-compute, equal-history, equal-memory-content, carrier-only, or
component contrast. Parenting causality comes only from U0/U1/P0/P1.

## 2. Root packet and registered population

One confirmation root is one iid draw from a frozen finite-universe packet
distribution `Q`, conditional on the pinned child checkpoint, reset parent
policy, curriculum families, writer, active-text policy, software, hardware
class, and CompilerGym universe. The estimand is

```text
mu_D = E_{R ~ Q}[D_R].
```

`Q` is a canonical JSON schema whose frozen instance contains:

- one root ID and 256-bit root master;
- twelve matched nursery opportunity packets per P/U branch, each containing
  the v1 Codebreaker or RuleShift family, generator parameters, source task,
  fresh homologous application task, legal-action permutation, reset identity,
  and order;
- one uniform sample without replacement of 56 programs from the registered
  eligible CompilerGym universe, followed by a uniform permutation: the first
  48 are the wake deck and the last eight the probe deck;
- all actor, parent, writer, updater, retrieval, environment, probe, and
  diagnostic stochastic keys; and
- the complete P0/P1/U0/U1/R0 service roster and cut schedule.

P and U receive byte-identical nursery tasks/opportunity order inside a root.
All five deployment services receive the same wake/probe identities and order
inside a root. Roots sample independently with replacement from `Q`; program
identities may recur across roots because the complete root draws are
independent. Rejection sampling is allowed only for the prospectively frozen
structural eligibility predicates; the candidate stream, rejection reasons,
and accepted ordinal are receipted. No realized model output, score, store
yield, or fit result can affect assignment.

One root contributes exactly one analysis row. Tasks, probes, cuts, calls,
actions, targets, fits, and samples are repeated measures and never increase
`n`. Inference is conditional on one fixed parent policy and one fixed child
checkpoint. It estimates reproducibility over `Q`, not heterogeneity over
parents, child models, or deployment domains.

## 3. Protocol hash, counter keys, and resumes

`protocol_hash` is SHA-256 over a canonical manifest of every ratified source
path and SHA-256, excluding generated root packets, keys, receipts, artifacts,
and the manifest's own hash. Canonical JSON is UTF-8, NFC-normalized strings,
sorted keys, no insignificant whitespace, and a terminal LF.

For every split/root, then every distinct stochastic coupling group, compute

```text
root_master = HMAC-SHA256(
  key = raw_32_bytes(protocol_hash),
  msg = canonical_json([split, root_id, "root_master"])
)
event_digest = HMAC-SHA256(
  key = root_master,
  msg = canonical_json([
    domain, matched_opportunity_id, stage, call_slot, sample_index, purpose
  ])
)
seed_u64 = little_endian_uint64(event_digest[0:8]).
```

The manifest represents each intended coupling group once, maps all member
service/call IDs to that group, and asserts exact event-digest/seed equality
within the group. It rejects repeated complete digests or repeated executed
`seed_u64` values **between distinct groups** across every split/root roster.
It receipts root master, 256-bit event digest, executed 64-bit seed, and group
membership.
Integer sampling uses NumPy `PCG64DXSM(seed_u64)` with frozen library/version
hashes. Model/updater backends receive `seed_u64` under a pre-GPU canary that
must prove that the supplied seed is honored and that matched calls retain the
registered marginal law. Disclosure of nondeterminism alone is not a pass.
Writer initialization, row permutation, and dropout each use separate domains.
The environment is deterministic; its key still receipts reset identity.

Coupling law:

- matched P/U nursery actor opportunities share keys; parent-only calls use
  the disjoint `parent_correction` purpose and consume no actor stream;
- matched deployment wake continuations across all five services share keys by
  root/program/call slot, despite their different contexts;
- the five services' same probe/cut/call slots share keys;
- keys differ across cuts, so no probe uniform is reused at another cut;
- P0/P1 cut 0 is one cached evaluation of their byte-identical P checkpoint;
  U0/U1 cut 0 is one cached evaluation of their byte-identical U checkpoint;
  R0 has one separate raw-pinned-actor cut-0 evaluation; and
- structurally absent or treatment-only calls use disjoint purposes and never
  advance another call's stream.

Split names, root IDs, and execution order are globally unique and prebound. A
pre-request infrastructure stop may resume only from a hash-committed boundary
proving no response/action was created. A host, storage, transport, or backend
loss remains administrative missingness unless a valid response or a
protocol-defined service-failure event was durably committed. A committed
model/system event is never retried or replaced. Hardware nondeterminism is
part of the root realization.

## 4. Exact probe value and timing

Every eligible probe program has frozen base instruction count `I_base > 0`.
For probe `q`, service `c`, root `r`, and cut `t`, let `I_best` be the smallest
valid post-pass instruction count among all legal action sequences actually
dispatched under that probe's fixed generated-token budget and twelve-action
fail-safe. The unchanged base pipeline is always a legal incumbent. Compiler
failure, invalid syntax, or an undispatched proposal contributes no candidate;
if there is no valid improving dispatch, `I_best=I_base`.

```text
v_c,r,q(t) = max(0, min(1, (I_base,q - I_best,c,r,q,t) / I_base,q))
V_c,r(t)   = (1/8) * sum_q v_c,r,q(t).
```

Exact parser, compiler, normalization, budget, and scorer bytes are hashed.
At cut 0, use the cached entry measurements defined above. At cuts 16/32/48,
the order is: finish wake program; attempt/merge that program's active-text
update; at the era boundary attempt SLEEP and transactionally commit or
quarantine its candidate; then run the isolated probe panel. Probe artifacts
never enter wake, DREAM, SLEEP, active text, parent input, or a later cut.

Report P-versus-U entry value, floor/ceiling occupancy, all raw root values,
and the descriptive headroom-normalized sensitivity

```text
HG_c,r(t) = [V_c,r(t)-V_c,r(0)] /
            max(0.10, V_search,r - V_c,r(0)),
```

where `V_search,r` is the same root/probe panel's cognition-hidden fixed-seed
search value. No root is matched, removed, regressed, or stratified using entry
value, admitted-row count, active-text yield, or any other post-assignment
quantity.

For the sensitivity only, replace every `G_c,r(t)` in the Section-5 gain-AUC,
`W_P`, `W_U`, and `D` formulas with `HG_c,r(t)` to obtain `hgAUC`, `HW_P`,
`HW_U`, and `HD=HW_P-HW_U`. Report how often the `.10` denominator floor is
active. `HD` is never an alternative primary.

## 5. Primary and fixed-sequence claim family

For `t in {0,16,32,48}` define `G_c,r(t)=V_c,r(t)-V_c,r(0)` and

```text
gAUC_r(c)   = [2*G_c,r(16) + 2*G_c,r(32) + G_c,r(48)] / 6
W_P,r       = gAUC_r(P1) - gAUC_r(P0)
W_U,r       = gAUC_r(U1) - gAUC_r(U0)
D_r         = W_P,r - W_U,r
C_public,r  = gAUC_r(P1) - gAUC_r(R0)
L_terminal,r = V_P1,r(48) - V_P1,r(0)
T_R0,r       = V_P1,r(48) - V_R0,r(48).
```

`D` is the sole primary endpoint. Pointwise curves and `I(t)` are descriptive
decompositions. Each inferential rung uses a two-sided root-level Student-t
interval at alpha .05 and passes only when its lower endpoint is above zero
and its observed point estimate reaches that rung's frozen practical margin.
Use the following fixed sequence and stop permanently at the first failure:

1. `D`, margin `.05`: this fixed parenting protocol increased this fixed child
   system's later benefit from enabling personal writes over `Q`;
2. `W_P`, margin `.05`: deployment writes were beneficial, not merely less
   harmful, for the parented system;
3. `L_terminal`, margin `.05`: P1 improved in absolute finite-life value;
4. `C_public`, margin `.05`: the full P1 package gained more during deployment
   than R0; and
5. `T_R0`, margin `.05`: P1 ended above R0 in absolute task value.

This sequence controls only these five superiority sentences. It does not
power the later rungs, local-plateau composite, or terminal mechanism
diagnostics. Rungs 2--5 are precision-gated. P1--R0 remains a full-package
comparison and isolates no single mechanism.

The common numeric `.05` requires separate development justifications on the
gain-AUC interaction, within-system gain, and terminal between-system scales.
Confirmation may not revise it.

## 6. Fixed N and primary operating characteristic

Use fixed `N=32` confirmation roots; do not use the v1 blinded adaptive-N
rule. Development roots and four spending-pilot roots remain excluded.

The primary joint rule is examined at requested `mean(D)=.070`, requested
pre-clipping root SD `.10`, alpha .05 two-sided, and fixed `N=32`. The
deterministic CPU planning script
`research_loop/advisory/one_parent_v2_power_sim.py` uses 300,000 repetitions
and seed 20260907. Named normal, standardized t5, right/left-skew beta, mild
two-point, and rare-negative two-point families are reported separately.

These are conditional planning sensitivities, not a mean/SD power envelope:
mean and SD alone do not determine the small-sample t-rule's power. The adverse
rare-negative mixture is intentionally retained. The paper must print each
named shape's estimated joint pass probability and may not say “at least 80%
power” for the primary, the five-rung conclusion, plateau, safety gates, or
diagnostics. All inferential results are fixed-N precision estimates. The power
script, NumPy/Python versions, invocation, stdout hash, source hash, and exact
post-clipping empirical moments are frozen in the statistics manifest.

## 7. Failures, missingness, and deterministic safety gates

Every assigned root remains in the root roster.

- A completed probe opportunity with no valid dispatched action is an observed
  behavioral failure and scores zero.
- A malformed response, context failure, or rejected tool call is a committed
  per-opportunity service event; that opportunity yields no action candidate
  and the service continues at the next frozen boundary. A nonfinite candidate
  fit, failed transactional canary, or failed candidate mount always
  quarantines that candidate, restores the prior committed adapter, and
  continues. An active-text update failure preserves the prior store and
  continues. Failure to restore an already committed adapter/store because of
  host, storage, transport, or backend loss is administrative missingness, not
  a behavioral zero. There is no discretionary terminal-service branch.
- Administrative/infrastructure missingness outside the assigned service
  (lost artifact, evaluator outage, host loss before a committed request, or
  unrecoverable storage corruption) is never imputed to zero. No root is
  replaced. Any such missing P/U primary cut blocks confirmatory D release;
  missing R0 blocks public/plateau claims. Complete-case and worst-bound
  sensitivity tables may be descriptive only.

Headline release also requires zero provenance/firewall/resource-parity
violations and 100% pass of every predeclared transactional native-action,
DREAM-restoration, mount, and generic-anchor canary. These are deterministic
system validity gates, not favorable statistical endpoints. Free typed routing,
typed-forced proposal quality, action cardinality, dream requests, and generic
quality are reported at every cut, but no undefined statistical “non-erasure”
claim is added. The strict task endpoint prices any behavioral degradation.

## 8. Strong-reference and local-plateau composite

R0 may be called a **strong active-memory comparator** only if every once-only
`ACTIVE_TEXT_FIXED` semantic, retrieval, use, and headroom certificate passes.
Otherwise it remains an active-memory reference and no strong-baseline or
plateau sentence is released.

After all five superiority rungs pass, a sixth fixed-sequence composite may
release only this sentence: “R0 showed a registered local plateau over
programs 16--48 under this updater/read/action budget, while P1 continued
improving and ended higher.” Define

```text
s1_R0,r = V_R0,r(32) - V_R0,r(16)
s2_R0,r = V_R0,r(48) - V_R0,r(32)
late_P1,r = V_P1,r(48) - V_P1,r(32)
late_delta,r = late_P1,r - [V_R0,r(48)-V_R0,r(32)]
H_r = V_search,r - V_R0,r(48).
```

The composite is an intersection-union test and passes only if:

- the 90% two-sided root-level Student-t intervals for both `s1_R0` and
  `s2_R0` lie wholly inside `[-.05,.05]` (two alpha-.05 TOST equivalence
  tests; `.05` is separately justified as the smallest meaningful 16-program
  change);
- the one-sided 95% lower bound for mean `H` is above `.10`;
- the one-sided 95% lower bound for mean `late_P1` is above zero; and
- the one-sided 95% lower bound for mean `late_delta` is above zero and its
  point estimate is at least `.05`.

Because the composite null is the union of component failures and the claim is
released only when every component rejects at alpha .05 after rungs 1--5,
fixed-sequence intersection-union testing controls its claim-family error.
This is not global, intrinsic, representational, or active-memory saturation.

## 9. Exact experiential-text diagnostics

From immutable same-service public artifacts define:

- `OWN_OBSERVATION`: one non-probe native action actually dispatched by that
  service and its public outcome/score block;
- `EVIDENCE_UNIT`: one nonsuperseded live active-text record derived
  exclusively from eligible preceding same-service OWN_OBSERVATION blocks;
- `SUPPORTED_UNIT`: an EVIDENCE_UNIT whose exact live status is `SUPPORTED`;
- `AUTHENTIC_LINK`: one directed link committed before the query whose source
  and target are both live SUPPORTED_UNITs;
- `TRAVERSED_LINK(q)`: the source is an intact fused seed, the target is absent
  from the pre-expansion packed seed set, the target is added only by the
  source-to-target one-hop expansion, both complete supported records are
  rendered before action, and their evidence/link commits precede the query;
- `support_onset(key)`: the earliest immutable commit ordinal after which the
  sole live record for a key first satisfies SUPPORTED_UNIT;
- `authentic_link_onset(source,target)`: the earliest immutable ordinal after
  which the directed link exists and both current endpoints satisfy
  SUPPORTED_UNIT;
- `ERA_EXPANSION(t)`: exact counts whose support/authentic-link onset lies in
  the era of newly supported semantic keys, cross-program supported units, and
  authentic links; and
- `LATER_RETURNED(t)`: exact counts of those units present in a complete
  pre-action retrieval receipt at a later cut.

Later supersession, contradiction, or endpoint-status loss remains in the
lifecycle table and determines whether an object is live at cut `t`; it never
moves onset backward or creates a second new object. These failure-inclusive counts establish what the explicit textual layer
stored and returned. They do not prove private use, child-directed expansion,
a graph inside weights, or useful connection without the intervention below.

Compression is not a confirmatory headline in this protocol version. The
active-text contract must still emit deterministic compact/raw storage
accounting, but “compression” or “shorter code” is withheld until a separate
source-bound workflow freezes one canonical expanded-equivalent grammar,
complete shared-cost accounting, denotation equality oracle, rate threshold,
functional non-loss test, reducer, and uncertainty rule. Retaining the raw
ledger forbids complete-system storage-compression language.

## 10. Two secondary terminal diagnostics replacing LEAFE_STYLE_FINAL

The optional LEAFE-style comparator is removed. The following diagnostics run
only on the 32 locked confirmation roots after all headline root counts,
artifacts, and primary decisions are immutable. They cannot change root
eligibility or any headline result.

### 10.1 Link contribution

At each interactive continuation, each branch constructs its query from its
own current objective, metric, last two actions, and latest outcome. Rank that
query against the immutable authentic index and freeze that continuation's
pre-expansion fused seed IDs/ranks. Keep the authentic store/index/embeddings
unchanged. A separate read-only adjacency overlay creates actor-visible copies
of seed records whose **only** changed field is `linked_memory_ids`, expands
from those displayed links, and otherwise returns byte-identical authentic
target records. Diagnostic copies are render artifacts, never stored records,
index replacements, or valid commits.

The overlay operates on every eligible edge instance. Sort edges by
`(source_id,target_id,edge_ordinal)` within an exact bucket of endpoint record
type, status, scope, and pinned-tokenizer target-record token length. Sort the
corresponding target stubs lexicographically and try cyclic rotations in
ascending offset. Select the first rotation with no original target, self-link,
duplicate target per source, already-linked replacement, missing target, or
superseded target. This preserves source out-degree, target in-degree, endpoint
fields, exact target token lengths, packed document cardinality, and total
returned tokens. If no rotation also preserves the frozen pack order class
under the 1,024-token cap, the probe is infeasible. The overlay is never
committed or returned to life. Selection uses pre-action receipts, never probe
score or hidden solution.

If no eligible TRAVERSED_LINK or exact bucket derangement exists for a probe,
its paired contribution is zero. Administrative missingness blocks this
secondary claim. Under the same common-RNG terminal probe calls and failure
values, define

```text
K_link,r = mean_q[v_intact,r,q(48) - v_overlay,r,q(48)].
```

### 10.2 Correct action--outcome binding contribution

Preserve the authentic P1 ledger and every authentic row-conditioning byte.
For shadow admission only, each action block exposes the exact primitive tuple

```text
(dispatch_valid, compiler_valid, outcome_class, normalized_public_score)
```

where enums and the rational normalized score use the frozen public scorer.
Action/program IDs, chronology, prediction, prior incumbent, raw public text,
event IDs/ordinals/hashes, and REVISION references remain recipient-authentic;
the shadow reducer recomputes positive-improvement, prediction-residual,
surprise, non-inferiority, and recovery bits from the donor tuple plus those
recipient-authentic fields. It never reparses or semantically reinterprets raw
text.

Within each `(root,era,normalized_action_family)` stratum, sort recipient block
IDs lexicographically and rotate the same sorted list of donor tuples forward
by exactly one position, producing a no-fixed-point cycle when size is at least
two.
It does not mutate event IDs, ordinals, hashes, REVISION references, active
text, or any live artifact, and it never conditions on original outcome
validity or score-effect bin. The shadow bits select terminal deployment slots;
authentic childhood rows, every selected unmodified authentic child response
suffix, fixed rehearsal fills, anchors,
four-exposure schedule, optimizer, clean base, and terminal P1 active-text store
remain unchanged.

If a stratum has fewer than two items it remains unchanged and is reported. If
no slot identity changes in a root, its paired contribution is zero. Define

```text
K_binding,r = V_intact_P1,r(48) - V_shadow_write,r(48).
```

For each `K` use the one-sided root-level Student-t p-value for null mean at
most zero. Sort by `(p_value, hypothesis_name)` with ASCII hypothesis-name ties;
the smaller p-value must be at most `.025`, then the larger at most `.05`.
Each claim is released only if its Holm test rejects and its own observed mean
is at least `.05`. The two one-sided secondary hypotheses therefore form a
Holm family at alpha .05; they are precision-gated, not powered.
All 32 roots remain in both reducers, with zero contribution for an infeasible
intervention and no favorable root filtering. `K_link` can support only the
functional contribution of explicit goal-conditioned one-hop active-text
links. `K_binding` can support only that correct outcome binding affected a
fixed-history terminal compilation. Neither establishes a graph or outcomes
represented inside the LoRA, an on-policy mediated effect, or compression.

Narrow replacement ceilings are 128 calls, 16,384 generated output tokens,
128 query embeddings, 131,072 returned active-text tokens, 128 possible native
dispatches, and one clean-base terminal fit/root with at most 81,920 labeled
and 655,360 attended tokens. The overlay uses zero updater calls, zero new
record embeddings, and zero live-store/index mutation. Diagnostic actor input,
clone/overlay bytes, CPU/index work, wall/GPU time, latency, and energy require
an exact resource-manifest addendum and measured p95 lease gate; therefore this
is only within the former optional comparator's call/output/fit envelope, not
yet whole-resource-neutral.

## 11. Separate carrier and expansion experiments

CompilerGym cannot prove connected/compressed knowledge inside an
undifferentiated LoRA. A later controlled carrier experiment may claim only
**parametric transport and behavioral use of authentic connected experiential
code**, never a human-interpretable graph inside weights. It requires compact
linked, denotationally equivalent expanded-linked, atoms-only, marginal/degree-
preserving binding derangement, and necessary-bridge-cut carriers; same-corpus
active text, adapter-off, and sterile within-root twin/binding controls; own
prospectively dispatched action--public-outcome provenance; identical policy
supervision; and one frozen resolver on fresh at-least-two-edge compositions
with no direct stored answer.

Goal-directed knowledge expansion is a different relay: existing memory must
change a child information-seeking action, that action must create a new public
outcome, a later write must admit it, and a still-later fresh goal must benefit
under sham/binding/write-off interventions. Neither experiment is a classroom,
another parent, or a rescue for the headline. Each requires its own later
workflow, power/resource manifest, and ratification.

## 12. Manuscript consequences after ratification

- `ACTIVE_TEXT_FIXED` is a prospectively fixed candidate until its once-only
  certificates pass; every service has the same updater/retriever policy and
  an isolated on-policy store.
- Print exact `gAUC` and `D`; the four-cell interaction leads causal results.
  P1 versus R0 is labeled a full-package public illustration.
- Name Codebreaker and RuleShift, three cycles, four opportunities/cycle, the
  fresh application task, and the closed three-code/NO_CORRECTION surface.
- State the complete fresh-process deletion audit and fixed-slot cumulative
  clean-base writer.
- Describe active-text `REFLECT` as an attempt with conditional/no-call
  `CURATE`; retrieval returns complete typed records plus lexical-only public
  event blocks.
- State that roots replicate `Q` for one fixed reset parent/child policy pair,
  not parents or child models.
- Keep wrong-child or general-process shams out of guaranteed-null captions.
- Use singular “strong active-memory comparator” and the exact deployment-only
  parity qualifications.
- Remove undefined early-slope, backward-retention, forgetting, and broad
  forward-transfer claims unless separately ratified.
- Parent identity, figures, results, citations, reproducibility receipts,
  systems/versions, and AI-use verification stay pending until immutable
  evidence exists.

## 13. Gate and scope

The v1 external workflow remains preserved at zero attempts and should not be
run. A replacement workflow must bind v1, this addendum, the three independent
audits, all three cross-critiques, the power script/receipt, and a new scoped
proposal. Exact human approval of that workflow authorizes deliberation only.

Even a deliberation PASS cannot authorize implementation. After consensus,
Rohin must ratify exact source bytes and implementation scope; only then may a
new namespace and CPU/static fixtures be implemented. Parent/child/tokenizer/
benchmark/adapter/GPU execution remains behind fresh implementation review and
a separate exact pre-GPU authorization.
