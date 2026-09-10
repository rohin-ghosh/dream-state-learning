# 58 — One-child PCFL relay v2: executable causal contract

Date: 2026-09-07

Status: unbound, proposal-only replacement for note 54. It authorizes no
architecture or source change, target/root generation, implementation,
model/tokenizer call, benchmark or adapter operation, external access, GPU use,
or scientific claim. It may enter a source-bound workflow only after a fresh
independent re-audit. Confirmation requires a later exact power lock; this note
does not invent an `N`.

## Scope invariant

The relay uses one fixed terminal child after its one parent and every nursery
artifact have been deleted. Independent roots are isolated environment trials
of byte-identical clones of that child. They never teach, observe, compete
with, or share state with one another. `WRONG_LIFE` is an isolated negative
carrier from another sealed environment root, not another learner.

The relay is downstream of the parenting headline and cannot rescue it. It
tests whether the same parent-deleted child can:

```text
own public actions -> supported atoms and authentic co-use links
fresh goal -> goal-conditioned traversal of those links
old linked experience -> choose a discriminating public experiment
public outcome -> one prospectively specified supported new row
old + written row -> improve a later hidden goal
```

Compression is not part of this relay. Connected transport, traversal,
acquisition, and delayed use remain separate ordered claims.

## 1. Prospective time line and locks

For a confirmatory label, freeze the following before parenting outcomes are
unblinded:

```text
P0  parenting protocol, child-selection function, and parenting RNG lock
R0  relay generator, interface, score, intervention, and analysis lock
PU  parenting unblind
CS  selected terminal child bytes and deletion receipt sealed
A0  every relay root, opportunity tape, hidden twin, and RNG commitment sealed
A1  Phase-A events sealed; deterministic semantic decks constructed
B   write-denied carrier/traversal forks executed and destroyed
C0  common pre-C state sealed
C1  authentic declaration/action/public outcome sealed
D0  D branches cloned from the identical C1 boundary; interventions activate
D1  fresh D goal revealed; terminal action sealed
```

Only `CS` necessarily occurs after parenting because the checkpoint does not
exist earlier; its selection function is fixed at `P0`. If `R0` occurs after
`PU`, every relay result is exploratory and conditional. No later A0 seal can
restore confirmatory status.

At `R0`, freeze generator code/hash, candidate universe, finite action/read
interfaces, root distribution, targets/twins, intervention algorithms, score
functions, failure values, development roots, analysis code, and a master RNG
commitment. At `A0`, instantiate root bytes without reading child behavior,
logits, stored rows, parenting scores, relay feasibility, or writer output.
Every randomized root remains intention-to-treat; none is regenerated,
replaced, relaxed, or restratified after failure.

## 2. PCFL objects and deterministic semantics

Each root contains a deterministic typed relational world and a counterfactual
twin. Identifiers are independent random handles. The hidden generator emits:

- a public Phase-A opportunity tape `O_A`;
- an eligible atomic relation set `E_A` reachable from that tape;
- two Phase-B goals over one identical public start state;
- one Phase-C binary-valued missing relation and a finite registered set of
  legal separating experiments;
- one Phase-D goal with a mechanically unique minimal proof requiring exactly
  one admitted old relation plus the Phase-C relation;
- type-matched twins, irrelevant truths, derangement slots, and fixed
  interface candidates; and
- an exhaustive truth proof for every registered score and intervention.

The actor never sees hidden truth. All public outcomes are deterministic, so a
valid prospective experiment may support one exact row after one observation.
If a later stochastic variant is introduced, it is a new protocol and must
predeclare its evidence threshold.

### Canonical atoms

A Phase-A public event is:

```text
EVENT(event_id, time, public_state_hash, action_id, outcome_symbol)
```

Before an action, the child may emit one or more typed candidate atoms:

```text
ATOM_PROPOSE(schema, endpoint_1, endpoint_2, value_domain, prediction,
             prior_event_citations)
```

The deterministic target-blind compiler `G_atom` admits exactly one canonical
row only when a later cited public event is chronological, the action is legal,
the outcome maps uniquely into the declared value domain, and hidden truth is
used only by the offline support checker. Unsupported/ambiguous rows become
`NO_ADMISSION`; they are never repaired or paraphrased.

`S_A = G_atom(A_EVENTS)` is the realized supported atom deck. `E_A` is only
the presealed eligibility set; it is never called learned state. Missing
required atoms score the registered failure value in all affected endpoints.

### Authentic experiential links

An authentic link cannot be a hidden-world gift. Before a Phase-A task action,
the child may emit:

```text
COUSE_PROPOSE(atom_id_1, atom_id_2, intended_operation, citations)
```

`G_link` admits

```text
USE_LINK(link_id, atom_id_1, atom_id_2, event_id)
```

iff both atoms were already admitted, the proposal precedes the cited action,
the action publicly and syntactically consumes both relations, and its outcome
passes the presealed public success predicate. The link records only undirected
co-use adjacency. It contains no goal, target, order, terminal action, answer,
path, policy continuation, or success magnitude.

`L_A = G_link(S_A, A_EVENTS)` is thus learned from this child's own public
behavior. If a supplied/mechanically hidden link variant is ever used, its
claim is explicitly *use of supplied adjacency*, not learned connected
experience.

The root generator precommits a fixed-point-free slot permutation for link
derangement, but applies it deterministically only to realized `L_A`. It must
preserve endpoint types, per-node in/out degree, age bins, row/token lengths,
support/citation affordances, candidate counts, and link count. Failure to
obtain a valid realized derangement scores the root failure; no new permutation
is searched.

## 3. One frozen core, explicit carrier construction

There is no polymorphic `M_A`. Freeze four distinct objects:

```text
A_CORE   = selected child parameters + target-blind allowed deployment state
A_EVENTS = immutable public provenance ledger, audit-only after deck build
S_A      = deterministic admitted atom deck
L_A      = deterministic admitted experiential link deck
```

For each arm, `CARRIER(arm)` is rebuilt from byte-identical `A_CORE` using the
presealed deck assignment, canonical serializer, exposure envelope, and
coupled build RNG. No authentic carrier is mutated in place to create a
control. Text and LoRA carriers use the same semantic deck and one-hop read
contract. LoRA is mounted only for `READ`; the clean frozen resolver/action
policy is common to all arms.

Carrier decks are:

| arm | deck |
|---|---|
| `LINK_AUTH` | `S_A + L_A` |
| `LINK_DERANGED` | `S_A + fixed projected derangement(L_A)` |
| `LINK_NULL` | `S_A +` type/degree/token-matched truthful irrelevant links |
| `BRIDGE_SUB` | `S_A + L_A` except the necessary bridge is replaced at read time by its presealed type-matched twin |
| `ATOMS_ONLY` | `S_A`; descriptive lower-resource diagnostic only |

`LINK_NULL`, not `ATOMS_ONLY`, is the resource-matched no-useful-link control.
All builds report admitted rows, semantic tokens, exposures, labeled tokens,
steps, optimizer slots, fit failures, storage bytes, build calls, and coupled
RNG receipts. Unequal physical resources are reported, never described as
matched.

## 4. Finite public read interface and closure

The only reader operation is:

```text
READ(query_type, anchor_id, selected_candidate_id)
```

At each call, the actor sees the complete fixed candidate-ID list for that
query type and selects one ID. The runtime performs exact syntactic lookup and
copies only that row. It cannot rank relevance, shortlist, validate semantics,
follow another edge, complete a path, generate fallback content, repair a
malformed trace, or retry invisibly. Every candidate scan, resolver call,
batch, retry, latency class, miss, and token is charged.

Candidate membership, order, padding, IDs, lengths, provenance affordances,
hit/miss behavior, and timing class are byte-identical across paired goals,
twins, and arms except the declared read-time semantic substitution. Generator
tests enumerate individual and joint interface features against oracle actions.

Because the interface is finite, the CPU audit enumerates every legal
target-blind nonadaptive query schedule under the registered call/token cap.
If enumeration is too large, the cap or interface must shrink; an unproved
“strong exhaustive controller” is not accepted. The best enumerated schedule
defines the controller ceiling before model execution. Reader-internal scans
count against the same cap.

Goal-only, state-only, identifier-only, candidate-only, passive-signature,
source-action-string, unaided-generative, adapter-off, wrong-life, and every
proper visible-feature-subset controller must remain below prospectively frozen
ceilings. A leaked oracle must reach its floor.

## 5. Phase A — acquisition and writer/read gates

The child selects legal information actions on `O_A`; the harness does not
choose its decisive action. DREAM may propose atoms/links, but only `G_atom`
and `G_link` admit them from cited public chronology.

Before later phases can release:

- atom proposal precision, admission precision, canonical row fidelity,
  adapter/text read fidelity, and retained atomic task value clear absolute
  floors;
- every accepted row has public provenance and exact compiler receipt;
- the native child response, typed dispatch, public result, response-only
  supervision mask, cumulative clean-base build, mount/off state, and rollback
  hashes are complete; and
- parent/nursery bytes and hidden truth are absent from every model-visible or
  supervised target.

Failure stays in all downstream denominators.

## 6. Phase B — connectedness and goal-conditioned traversal

Phase B forks from the same `A_CORE/S_A/L_A` cut, writes nothing, and is
destroyed afterward. Phase C restores the exact common `C0` state.

For each of the two same-start goals `g0,g1`, the hidden proof defines a
different relevant multi-relation path `P0,P1`. Before decisive action, the
child must emit an exact typed trace:

```text
GOAL_ANCHOR(goal_public_id, state_public_id)
READ(... selected_candidate_id ...)
FOLLOW(selected_returned_atom_or_link_id)
...
ACT(public_action_id)
```

No semantic repair is allowed. Define bounded root scores:

```text
CONNECTED_AUTH = mean_g 1[all selected authentic rows form P_g
                          and terminal action is oracle-valid]
Cbind = CONNECTED_AUTH - CONNECTED_DERANGED
Cnull = CONNECTED_AUTH - CONNECTED_NULL

Tgoal = mean(1[first_query(g0) in Q0 and path(g0)=P0],
             1[first_query(g1) in Q1 and path(g1)=P1])
        - BEST_ENUMERATED_TARGET_BLIND_SCHEDULE
Tcut  = action_value(AUTH) - action_value(BRIDGE_CUT)
Ttwin = twin_valid_action_value(BRIDGE_TWIN)
```

Both goals must clear absolute action/path floors; first-query divergence
followed by the same exhaustive suffix fails `Tgoal`. `BRIDGE_CUT` masks the
necessary returned row with a byte-matched miss. `BRIDGE_TWIN` substitutes a
truthful matched twin and must redirect the decisive action to the twin-valid
action rather than merely reduce success.

Connected transport releases only if atomic fidelity remains above floor and
both `Cbind` and `Cnull` pass. Goal-conditioned traversal additionally requires
`Tgoal`, `Tcut`, and `Ttwin`; no single final score stands in for these.

## 7. Phase C — prospective, memory-directed experiment

From identical `C0`, activate either `AUTH_SIGNAL`, `SHAM_SIGNAL`, or
`REACHOUT_OFF` only at the read boundary.

`SHAM_SIGNAL` substitutes a presealed true irrelevant relation from the same
world, matched on schema, endpoint types, record/link counts, degree, age,
support, citations, candidates, query, tokens, and legal action menu. It does
not inject a false fact, alter hidden truth, or reveal assignment.

Before action, the child must emit:

```text
GAP(schema, endpoints, cited_old_rows)
HYPOTHESES(value=h0, value=h1)
PREDICT_MAP(experiment=e,
            public_outcome_o0 -> CANONICAL_ROW(schema,endpoints,h0),
            public_outcome_o1 -> CANONICAL_ROW(schema,endpoints,h1))
ACT(e)
```

The schema/endpoints/value domain and complete outcome→row map are committed
before observation. The child chooses `e`; the harness only dispatches the
typed legal action. After the deterministic public outcome, compiler `G_new`
selects exactly its already committed row and adds the public event citation.
It cannot paraphrase, infer endpoints/family, read D, or consume post-outcome
DREAM prose. Invalid, ambiguous, unavailable, out-of-domain, or uncommitted
outcomes yield `NO_ADMISSION` and the registered failure value.

The offline posterior sees only the actor-public information set at the action
seal. It scores after the seal and has no edge back into life:

```text
Qgap       = valid supported gap + two live hypotheses
Qselect    = selected legal registered separating experiment
Qrelevant  = target-relevant expected information gain of sealed experiment
Qauth-sham = each AUTH score minus its SHAM counterpart
```

AUTH must clear absolute floors and both `Qselect` and `Qrelevant` contrasts
must pass. Entropy reduction about an irrelevant variable earns zero.

`REACHOUT_OFF` preserves authentic old memory but replaces the registered
information action with a public `UNAVAILABLE` result after identical time and
resource charge. It creates no supported new row. Its path continues to D from
a fresh common environment state with the old carrier only and a matched
no-semantic build schedule. It estimates total acquisition necessity, never a
controlled write effect and is not pooled with AUTH/SHAM.

## 8. Phase D — one truthful row as the only new carrier

Clone `EDGE_WRITE`, `NO_WRITE`, `SHAM_WRITE`, and `NEW_BIND_SWAP` only after a
byte-identical AUTH declaration, action, public outcome, canonical `G_new` row,
and event-seal receipt exist.

- `EDGE_WRITE`: adds exactly that one canonical supported row.
- `NO_WRITE`: adds no new semantic row; runs the same build calls, schedule,
  examples, tokens, steps, slots, and coupled randomness using only pre-C
  rehearsal/padding whose targets are masked. Realized gradients are not
  falsely claimed identical.
- `SHAM_WRITE`: adds one presealed genuinely supported irrelevant public row,
  matched on schema/type/support/citation/length/candidates/exposure, plus the
  same rehearsal envelope.
- `NEW_BIND_SWAP`: builds the authentic `EDGE_WRITE` carrier, then applies a
  fixed-point-free endpoint binding permutation only at READ. It never trains
  a false row through the truthful writer.

The writer receives only the canonical row plus allowed pre-C rehearsal. It
never receives the C goal, hypotheses, raw outcome prose, complete trace,
terminal policy, D bytes, or target action.

Before D, reset and hash actor state, world state, inventory, clocks, counters,
rewards, observation cache, file descriptors, process environment, RNG state,
reader/index/cache state, mount state, errors/retries, and candidate catalog.
The D start generator counterfactually matches all Phase-C physical effects.
Raw/audit ledgers are capability-inaccessible, not merely omitted from prompts.
Each branch starts a fresh process from `A_CORE` plus only its assigned carrier.

The fresh D goal is revealed after this reset. Its handles are new, and the
candidate universe contains no answer-bearing binding. Exhaustive CPU closure
enumerates every proper subset and combination of old row, new row, C action,
C outcome, declaration/hypotheses, passive signatures, candidates/metadata,
and every legal reacquisition history under cap. Only authentic old plus
authentic new carrier may reach the oracle floor; masking either cut must
change value, and the binding twin must redirect the action.

Define:

```text
W0    = delayed_value(EDGE_WRITE) - delayed_value(NO_WRITE)
W1    = delayed_value(EDGE_WRITE) - delayed_value(SHAM_WRITE)
Fbind = delayed_value(EDGE_WRITE) - delayed_value(NEW_BIND_SWAP)
Freacq = delayed_value(EDGE_WRITE_AUTH_PATH)
         - delayed_value(REACHOUT_OFF_CONTINUATION)
```

`W0/W1/Fbind` are controlled after the common AUTH outcome. `Freacq` is a total
path effect with a different C history and is interpreted separately.

## 9. Carrier sequence and claim release

First run the entire relay with explicit semantic text through the same finite
one-hop READ interface. If the leaked oracle succeeds but the exact-text relay
cannot, the benchmark/interface is invalid and no LoRA result is interpreted.

Then use the fixed-rank LoRA only for READ with the clean resolver/actor.
Required LoRA diagnostics are adapter-off, wrong-life, candidate-only,
unaided-generative read, cut, twin/binding swap, atomic retention, and
`TEXT_SAME_SEMANTICS`. Text success cannot rescue a failed LoRA transport
clause; LoRA failure cannot erase a valid text semantic relay.

Ordered release is:

```text
Aret
 -> Cbind AND Cnull AND authentic absolute floor
 -> Tgoal AND Tcut AND Ttwin AND exhaustive ceiling
 -> Qgap floor AND Qselect contrast AND Qrelevant contrast
 -> W0 AND W1
 -> Fbind
 -> Freacq (separate total-path necessity clause)
 -> complete TEXT chain
 -> complete LoRA chain + carrier diagnostics
```

Every root remains in every downstream denominator. No selected maximum or
later endpoint rescues an earlier failure.

## 10. Exact statistics gate, deliberately not guessed here

The independent unit is one sealed PCFL/twin pair root conditional on the one
fixed child. Targets, twin sides, calls, phases, and technical/adapter seeds are
repeated measures averaged by a frozen rule inside the root.

Before any confirmation root is generated, use only disjoint `PCFL-13` DEV and
an explicitly exploratory text-oracle/writer pilot to freeze:

- every bounded root-level score and aggregation above;
- absolute AUTH floors, negative-control ceilings, and SESOIs;
- one-sided/two-sided tests or intervals and exact confidence construction;
- ordered intersection-union/familywise handling;
- missing-cell/failure values and infrastructure-only resume rules;
- complete-chain `pi_min` and confidence rule;
- a simulation-based power function using the least favorable conjunctive
  endpoint and observed within-root covariance; and
- the final fixed `N` plus a blinded nuisance-only extension rule.

The lower confidence endpoint must exceed the registered SESOI, not merely
zero. A provisional `N=32` is deleted. If pilot information cannot power the
least favorable conjunction within the resource ceiling, the relay does not
advance. Any post-pilot change requires a new bound deliberation and exact
human ratification before confirmation.

## 11. Pre-execution kill gates

1. `P0/R0` prospective locks and child-selection rule precede parenting
   unblinding, or label the relay exploratory.
2. Parent/nursery deletion and `A_CORE` equality/capability receipts pass.
3. CPU generator audits prove root uniqueness, twins, all interventions,
   deterministic compilers, derangement projection, finite-interface closure,
   and D unique dependence on every generated root.
4. Leaked oracle clears floors; enumerated exhaustive and every side-channel
   controller remain below frozen ceilings.
5. Exact text relay clears feasibility and all phase-isolation/reset receipts.
6. Writer/read instrument, response-only masks, support, native dialect,
   transactional build/mount/off/rollback, and atomic retention pass.
7. Carrier decks/exposures/candidates and all resource vectors are hash-bound;
   no false row enters the truthful writer.
8. Exact statistics/power lock and fixed `N` exist; no provisional sample size
   authorizes dispatch.
9. A fresh rejection-capable reviewer and a separate author-side advocate
   dispose every concern; Rohin ratifies exact bytes and separately authorizes
   any model/benchmark/GPU execution.

## Claim boundary

Highest safe positive language, only after the complete ordered LoRA chain:

> Conditional on one fixed parent-deleted child and this registered PCFL
> distribution, authentic relations compiled from the child's own public
> actions were carried through its per-life LoRA, traversed differently under
> fresh goals, changed which public experiment it selected, and—after the
> prospectively declared public outcome was written—improved a later goal that
> required both old and new experience.

No compression, classroom, population learning, autonomous theory invention,
universal continual improvement, or unrestricted baseline-superiority claim
follows.

## Disposition of the v1 re-audit

This v2 adopts R1--R12 from
`research_loop/advisory/20260907_one_child_pcfl_relay_repair_reaudit_v1.md`
(SHA-256
`d2c29021df9ba322facc0b0b136170121dee8495229801161ca24e23e841e31c`).
Note 54 remains unchanged as the attacked artifact and is superseded only as a
candidate proposal. This v2 remains unratified until independently re-audited.
