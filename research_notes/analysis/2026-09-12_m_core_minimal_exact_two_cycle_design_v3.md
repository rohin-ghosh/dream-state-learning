# M-core v3: executable minimal crossed two-cycle relay contract

Date: 2026-09-12 UTC

Status: independent watcher design only. This note supersedes
`2026-09-12_m_core_minimal_exact_two_cycle_design_v2.md`. It changes no builder
source, benchmark, child, model, tokenizer, adapter, checkpoint, job, GPU
state, resource, coordination record, scientific claim, or release. It is a
complete proposed contract, not evidence that the contract has been built or
passed.

## 0. Verdict and exact claim boundary

The two fresh v2 audits are correct. The smallest defensible M experiment
still uses at most **six trained carriers per successful root**, but its DREAM
claim must be narrower and its graph, reader, controls, pad, roots, and tests
must be exact.

The only claim this design can release is:

> In a finite typed benchmark, a qualified writer carried records compiled
> from a crossed contingency in a child's authentic public actions and
> outcomes and from a child-selected pre-blueprint pair set identified by a
> registered public ablation signal. A reset clean actor used typed reads to
> complete two goal-conditioned old-memory traces. After an authentic public
> outcome, a second clean-base cumulative write preserved the required old
> link and added the outcome-specific new row needed for a delayed action.

This is **compiler-mediated crossed experiential binding**, a
**child-selected evidence-indicated pair set**, **typed functional
traversal**, and **two-cycle clean-base cumulative reconstruction**. It is not
evidence of child-specific DREAM intelligence, mechanically unrecoverable
organization, native learned search, in-place adapter expansion, open-world
graph learning, compression, recurrence, retention outside this finite
assay, or a whole-organism/lifetime flywheel.

The public ablation table mechanically determines the useful pair set. A
registered CPU necessity rule therefore reaches 100%. The child may be the
provenance of the sealed selection, but this benchmark cannot attribute that
selection to intelligence unavailable to a mechanical compiler. That
limitation is part of the result, not a failure to be hidden.

The six trained conditions are:

```text
SLEEP-1, run first for every root
  1. FULL_OLD
  2. SOURCE_DERANGED_OLD
  3. DREAM_DERANGED_OLD

SLEEP-2, only for roots surviving every frozen S1 gate
  4. FULL_NEW_h0
  5. FULL_NEW_h1
  6. FULL_OLD_PLUS_PAD
```

No corrupt S1 arm is rebuilt at S2. Source content is isolated at C, link
content at B, first-write dependence at B/C, and old+new reconstruction at D.

## 1. Frozen generator, root, and independent unit

### 1.1 Root law

One root `r` is one source-disjoint potential-outcome object. Before any child
token or outcome, draw with the registered generator version and seed:

```text
k                 root nonce
b ~ Bernoulli(.5) source-contingency orientation
z ~ Bernoulli(.5) nuisance outcome bit, independent of b
{u_A,u_B}         uniform unordered pair from C(8,2)=28
q_0...q_7         eight route cues with route(q_i)=a_i
q_A/q_B assignment fair to q_(u_A)/q_(u_B) within the selected pair
u_D               fair choice from {u_A,u_B}, independent of b,z,h
h                  both potential outcomes h=0 and h=1, not sampled roots
aliases            role-independent uniform permutation from a prequalified
                   token-isomorphic alias pool
event orders       independent registered permutations within fixed strata
condition/device/
inference orders   each root independently draws one Latin rotation from the
                   registered finite rotation set; within that root every
                   arm/control/device position occurs in the balanced schedule
                   and the draw is independent of b,z,u_A,u_B,u_D and outcomes
fit RNG            deterministic function H(protocol, root_id, build_id)
catalog RNG        deterministic function H(protocol, root_id, query ordinal,
                   registered catalog-permutation cell)
```

Alias-pool qualification occurs before role assignment. The pool contains
fixed-length/token-isomorphic triples needed for `n0`, `n1`, and `PAD`, plus
matched aliases for every hit-matched control. A candidate root that cannot
meet exact byte/token-shape constraints is rejected before it receives hidden
roles or enters a sealed manifest. No root is regenerated, replaced, or
relabelled after any child behavior or observed outcome.

Every visible node, action, relation, event, candidate, and row ID is derived
from `(protocol_version,k,object_class,slot,derivation_kind)`. An immutable ID
names exactly one canonical byte string. A deranged/twin payload has a new ID
and audit receipt; changing payload bytes under the same semantic ID is fatal.

### 1.2 Unit and manifests

The independent unit is the root, including both `h` potential-outcome twins.
The two goals, four source probes, catalog permutations, cuts, calls, renders,
and checkpoints are repeated measures and never increase `N`.

Before any fitted DEV outcome, seal one ordered eight-root manifest
`DEV=[D1,...,D8]`. The S1/S2 kill uses exactly `D1,D2`; widening uses exactly
`D3,...,D8`, so eight-root DEV is one nested presealed prefix. A separate
exact-text cohort `TEXT=[T1,...,T8]` is descriptive and is never promoted into
fitted DEV. Confirmation is a fresh source-disjoint ordered iid manifest
`CONF=[C1,...,C16]`, sealed before any confirmation child token.

The manifest binds all root draws, both h twins, all action/event schedules,
all future goal objects, build/condition/device/inference order, fit seeds,
and registered interventions. DEV selects mechanics only and has no
confirmatory inferential standing.

## 2. Complete typed world graph

### 2.1 Public types and graph

The root contains public node types:

```text
Start       S
Lane        U_0 ... U_7
Junction    B
Decision    C
Terminal    T_A, T_B, D
Dead        F_(i,j), F_D
PadSource   P
PadTarget   Q
```

It contains public action types and deterministic transition semantics:

```text
entrance action a_i:
  S --a_i--> U_i

lane action b_j, legal from every U_i:
  U_i --b_j--> B       iff j=i
  U_i --b_j--> F_(i,j) iff j!=i

shared action c:
  B --c--> C

terminal actions t_A,t_B:
  C --t_A--> T_A; C --t_B--> T_B

outcome actions n_0,n_1 in potential-outcome world h:
  C --n_h--> D
  C --n_(1-h)--> F_D

pad action p:
  P --p--> Q
```

All `b_j` are syntactically legal at every `U_i`. A binding-swapped link thus
redirects the actor to a legal but semantically wrong action and reaches a
public dead state; it is not detected by a parser or legality check.

The two Phase-B public goals are:

```text
G_A = {start:S, target:T_A, required_route_cue:q_A}
G_B = {start:S, target:T_B, required_route_cue:q_B}
```

The root defines a hidden role-independent bijection `route(q_i)=a_i`; its
correct two rows are carried by memory, not stated in the goal. Goal success
requires the entrance whose route cue matches the goal and the target-specific
terminal:

```text
G_A unique valid trace: a_(u_A), b_(u_A), c, t_A
G_B unique valid trace: a_(u_B), b_(u_B), c, t_B
```

The public route cue therefore distinguishes which remembered mapping is
needed without exposing the action alias. All other public goal fields are
alpha-renamed matched.

The Phase-D goal is byte-identical across h twins:

```text
G_D = {start:U_(u_D), target:D, required_route_cue:null}
```

Its unique valid trace in world `h` is:

```text
b_(u_D), c, n_h
```

The old link and new row are separately necessary. `h` is absent from the
goal, catalog, request, reset context, and actor process.

### 2.2 Child evidence and DREAM cut

Before any blueprint or Phase-B/C/D goal is available, the child first
performs a common foundation block grounding every `q_i -> a_i` route atom and
the two target/terminal atoms `T_A -> t_A`, `T_B -> t_B`. All eight route
facts receive the same schedule, views, and exposure; the future two goal
cues are not identified. These foundation rows enter every S1 deck unchanged.

The child then performs the same registered evidence schedule for all eight
candidate pairs `(b_i,c)`: one joint trial, one `b_i`-only trial, one `c`-only
trial, and matched nuisance trials. Counts, order strata, type/degree, endpoint
syntax, row schema, byte length, age, recency, and joint reward are balanced.

Formally, public ablation arena `A_i` accepts exactly four committed trial
types: `TEST([b_i,c])`, `TEST([b_i])`, `TEST([c])`, and
`TEST(nuisance_i)`. Each returns one causally later public binary outcome.
There is no free-text score, partial credit, hidden necessity field, or other
arena output. The outcome function over these complete legal trials is the
table below; this arena is evidence for link admission and is not an
alternative traversal edge in the S--D graph.

The complete public ablation outcome table is:

| lane class | joint | b-only | c-only | nuisance explanation |
|---|---:|---:|---:|---|
| `u_A,u_B` | 1 | 0 | 0 | none; both components necessary |
| three decoys | 1 | 1 | 0 | left component explains joint |
| three decoys | 1 | 0 | 1 | right component explains joint |

The left/right decoy assignment and presentation are prebalanced. Every
record follows an authentic child action and a causally later public outcome.
Missing actions remain adverse; the harness never fills them.

At cut `A2`, the child sees the public table and an order-permuted roster of
all eight endpoint-identical pair IDs. It emits exactly one canonical
`SELECT_PAIR_SET` containing two IDs. That exact output is sealed before the
first byte of any:

- support blueprint/handle/argument/menu/expected result;
- Phase-B/C/D goal, hypothesis, action, or outcome;
- theorem, compiler decision, scorer output, hidden role, or expected trace.

After the seal, the child performs fresh support actions for the selected
pairs. The compiler may admit a selected pair only if the new joint and two
single-component public results reproduce the registered necessity pattern.
It cannot propose, rank, replace, repair, or add a pair. Unsupported selections
are adverse failures.

The registered mechanical ablation policy applies exactly the same truth table
to the same public evidence and selects `{u_A,u_B}` on every valid root. It is
the task ceiling. Endpoint join and joint-frequency/recency are tied and use
presealed semantic-independent tie rules. Uniform exact-two selection has
construct probability `1/C(8,2)=1/28`. Report child agreement with the
necessity ceiling and the chance construct; do not test or claim child
superiority over the ceiling.

### 2.3 DREAM derangement

`DREAM_DERANGED_OLD` starts from the child's exact sealed two-pair set. A
presealed fixed-point-free permutation maps each selected lane `i` to a false
lane `pi(i)`. The compiled row keeps its query anchor `U_i` but its action
payload becomes `(b_(pi(i)),c)`. The returned first action is legal at `U_i`
and transitions to `F_(i,pi(i))`.

FULL and DREAM-deranged rows have different immutable row IDs, but after
alpha-renaming the intended payload field their visible training and reader
envelopes match exactly: key/hit/status, schema, field count, citation count,
serialized/token lengths, slot, renderer visits, target mask, deck position,
batch exposure, and optimizer work. Source rows are byte-identical.

This isolates correct child-selected link binding/content. It does not isolate
the intelligence or algorithm that selected the set.

## 3. Authentic crossed source and Phase-C truth

### 3.1 Child action/outcome block

One opaque source situation `X` exposes child actions `L,R`. The child must
execute each exactly four times in a presealed eight-opportunity block. The
occurrence order is independently presealed and presentation-balanced.
`T,O` below are spec labels for opaque public outcome aliases:

```text
b=0: L -> [T,T,T,O] ; R -> [T,O,O,O]
b=1: L -> [T,O,O,O] ; R -> [T,T,T,O]
```

These are fixed empirical event frequencies, `3/4` and `1/4`, not claimed
environmental probabilities. Each outcome is emitted only after the child's
committed action and has its own immutable event ID. Draft actions, parent
text, harness actions, and reordered outcomes are ineligible.

The qualified writer may compile only the representations its qualification
allows. For source, those representations must preserve the forward
action/outcome event and the inverse situation+desired-outcome/action
propensity needed by the registered C query. M does not add a new view recipe.

### 3.2 Crossed source derangement

`SOURCE_DERANGED_OLD` applies a presealed within-situation donor permutation:

```text
L -> [T,T,O,O] ; R -> [T,T,O,O]
```

It preserves all eight child actions, four L/four R occurrences, four T/four
O outcomes overall, source situation, surface schedule, row/view count,
visible citation schema/count, ID distribution, serialized/token-length
distribution, padding, render multiplicity, masks, deck positions, batch
exposure, and optimizer work. Only the action--outcome binding and necessarily
derived row IDs change. Authentic event IDs and the donor permutation remain
in an audit-only receipt; neither derivation kind nor donor identity is visible
to training, reader, or actor.

All path/DREAM rows are byte-identical between FULL and SOURCE_DERANGED. All
source rows are byte-identical between FULL and DREAM_DERANGED.

### 3.3 C experiment world and exhaustive admission law

The authentic source orientation defines the target-informative experiment
family. Both h twins share all public bytes through dispatch. `z` is an
independent nuisance bit:

```text
b=0: E0=h, E1=1-h, E2=z, E3=1-z
b=1: E2=h, E3=1-h, E0=z, E1=1-z
```

The public action-to-experiment menu is fixed in every root: source action L
opens family `{E0,E1}` and source action R opens family `{E2,E3}`. It does not
say which family is target-informative. Thus an inverse source READ for desired
T selects the correct family under authentic b, after which the child may
choose either the direct or inverse member while publishing the corresponding
map below.

Before acting, the child must cite its source inverse READ and commit two live
hypotheses, predicted outcome under each, the complete outcome-to-row map, and
one experiment. The only legal maps are:

```text
E0/E2: 0 -> n0 ; 1 -> n1
E1/E3: 0 -> n1 ; 1 -> n0
```

The compiler enumerates all `b,h,z,E,y` cases with this complete admission
table:

| chosen family | observed y | public posterior over h | declaration | truth | result |
|---|---|---|---|---|---|
| target direct | `h` | `{h}` | mapped `n_h` | supported | `ADMIT n_h` |
| target inverse | `1-h` | `{h}` | mapped `n_h` | supported | `ADMIT n_h` |
| nuisance direct | `z` | `{0,1}` | may be syntactically faithful | unidentifiable | `NO_ADMISSION` |
| nuisance inverse | `1-z` | `{0,1}` | may be syntactically faithful | unidentifiable | `NO_ADMISSION` |

`z==h` never creates knowledge. Admission requires both
`DECLARATION_FAITHFUL=1` and a singleton public posterior proving
`WORLD_TRUE=1`. Every one of the `2*2*2*4` `(b,h,z,E)` cases and its unique
public outcome is exhaustively generated at Stage 0. No expected answer,
hidden h, or theorem object enters the compiler capability.

### 3.4 Frozen source scoring

Four destroyed C probes share the S1 carrier and write nothing:

| probe | desired source outcome | action display | family display |
|---|---|---|---|
| C1 | T | L,R | E0,E1,E2,E3 |
| C2 | O | L,R | E0,E1,E2,E3 |
| C3 | T | R,L | registered rotated family aliases |
| C4 | O | R,L | same registered rotation |

The correct semantic action is frozen from the authentic root orientation:

```text
b=0: desired T -> L; desired O -> R
b=1: desired T -> R; desired O -> L
```

SOURCE_DERANGED is scored against these same authentic counterfactual labels;
its `2/4`--`2/4` tie never creates a new truth label. Presentation position is
canonicalized before scoring. One root produces one four-probe mean, never
four independent observations.

## 4. Closed typed reader

### 4.1 Actor/backend boundary

The reset clean actor receives only canonical UTF-8/JCS objects (exact key
order fixed by the schema version):

```text
MemoryCatalog {
  v, legal_query_types, public_anchor_ids,
  public_candidate_schema_digest, reads_remaining
}

RecognitionRequest {
  v, phase, query_type, public_state_id, public_goal_id,
  public_anchor_ids, public_candidate_schema_digest,
  call_ordinal, reads_remaining
}

MemoryReturn {
  v, status: FOUND|MISS|BLOCKED, query_fingerprint,
  row_or_fixed_pad, reads_remaining
}
```

The request object is the complete scorer request; there is no process-global
goal, state, history, or hidden prompt input. `query_fingerprint` is the hash
of `(schema_version,canonical_request_bytes)` only. `BLOCKED` means the query
violated the legal transition table. `MISS` means no candidate cleared the
frozen reader threshold. Both return fixed-length pads and consume one read.

The actor never sees candidate IDs, bank rows, scores, ranks, winner index,
candidate order, thresholds, retries, exceptions, or unpadded latency. It
cannot open/import the generator, compiler, scorer, theorem, audit receipt,
hidden truth, expected trace, or another process/cache/workspace.

The backend alone renders a query-specific 32-slot candidate bank. Its roster
template is sealed at `A0` from the public grammar and role-independent identity
Cartesian products, before role assignment, child outcomes, pair selection,
goals, or theorem construction. For a public request it instantiates all
grammar-legal payload alternatives for that query and fills unused slots with
presealed grammar-valid decoys. It never consults the correct row, expected
trace, outcome twin, or theorem when constructing the bank.

The complete per-query roster law is:

| query | exhaustive semantic alternatives | type-matched fillers | total |
|---|---:|---:|---:|
| `ROUTE_BY_CUE(q)` | all 8 `q -> a_j` rows | 24 reserved entrance rows | 32 |
| `ATOM_SUCCESSOR(U_i)` | all 8 `U_i -> b_j` rows | 24 reserved lane rows | 32 |
| `ATOM_SUCCESSOR(B)` | `B -> c` plus 7 registered shared-action alternatives | 24 reserved shared rows | 32 |
| `LINK_SUCCESSOR(U_i)` | all 8 `U_i -> [b_j,c]` rows | 24 reserved two-action links | 32 |
| `TERMINAL_TO_TARGET(T_x)` | both target-action rows | 30 reserved terminal rows | 32 |
| `SOURCE_INVERSE(X,T/O)` | L and R propensity rows | 30 reserved source actions | 32 |
| `NEW_SUCCESSOR(C,D)` | `n0` and `n1` rows | 30 reserved outcome actions | 32 |

Reserved fillers are generated from the same public type grammar and alias
pool and have matched surface/token strata; they are not selected using root
truth. The public catalog exposes only the common schema digest, never this
roster or its order.

For each candidate the scorer bytes are exactly:

```text
<qualified frozen reader system prefix>
REQUEST\n<JCS RecognitionRequest>\n
CANDIDATE\n<JCS canonical candidate row>\n
ANSWER:
```

The reader uses the exact scorer, YES/NO continuation tokenization, aggregate
function, tie rule, and threshold qualified before M. In the registered
implementation this entire byte sequence and candidate order are written to
an audit-only receipt. The backend returns at most one canonical row: the
unique maximum above threshold, else MISS. It cannot substitute, repair,
compose, or interpret a row. A link row is one stored payload containing two
ordered action IDs; returning it remains one READ.

`<qualified frozen reader system prefix>` above is not editable prose: the M
manifest must embed its exact bytes and SHA-256 together with the qualified
YES/NO token IDs, scoring equation, normalization, tie rule, and threshold.
If any one is absent or selected using M outcomes, the reader is unbound and M
cannot run.

### 4.2 Complete legal query language

No suffix, row-ID, slot, reverse, free-text, wildcard, enumeration, or raw
candidate query exists. The complete query table is:

| query type | legal phase/state | required public anchor | possible row payload |
|---|---|---|---|
| `ROUTE_BY_CUE` | B at S | current goal's `q_A` or `q_B` | one `q_i -> a_j` atom |
| `ATOM_SUCCESSOR` | B at `U_i` or B | current public state ID | one `b_j` or `c` atom |
| `LINK_SUCCESSOR` | B/D at `U_i` | current public state ID | one ordered `(b_j,c)` link |
| `TERMINAL_TO_TARGET` | B at C | current goal target ID | one `t_A` or `t_B` atom |
| `SOURCE_INVERSE` | C only | public X ID + desired T/O alias | one L/R propensity row |
| `NEW_SUCCESSOR` | D at C | current state C + public target D | one `n_0` or `n_1` row |

An anchor is legal only if it is in the current public state/goal, or is an
endpoint exposed by the immediately preceding returned row and then reached
by the corresponding public action. A legal READ may return FOUND or MISS;
all other requests return BLOCKED. Repeats are permitted but consume budget.
An actor may execute only an action cited by a FOUND row in its current trace.
Malformed, uncited, out-of-order, or wrong-state actions score zero.

### 4.3 Exact A/B/D traces and first dependent bytes

Phase-B goal A, FULL, three reads:

```text
1 REQ ROUTE_BY_CUE(state=S,goal=G_A,anchor=q_A)
  RET row(q_A -> a_uA); ACT a_uA; public state U_uA
2 REQ LINK_SUCCESSOR(state=U_uA,goal=G_A,anchor=U_uA)
  RET row(U_uA -> [b_uA,c]); ACT b_uA; ACT c; public state C
3 REQ TERMINAL_TO_TARGET(state=C,goal=G_A,anchor=T_A)
  RET row(T_A -> t_A); ACT t_A; public state T_A
```

Phase-B goal B is byte-identical after alpha-renaming except the registered
goal twin fields:

```text
1 REQ ROUTE_BY_CUE(state=S,goal=G_B,anchor=q_B)
  RET row(q_B -> a_uB); ACT a_uB; public state U_uB
2 REQ LINK_SUCCESSOR(state=U_uB,goal=G_B,anchor=U_uB)
  RET row(U_uB -> [b_uB,c]); ACT b_uB; ACT c; public state C
3 REQ TERMINAL_TO_TARGET(state=C,goal=G_B,anchor=T_B)
  RET row(T_B -> t_B); ACT t_B; public state T_B
```

Because JCS orders keys lexicographically, the first A/B-dependent byte is the
first differing byte inside request 1's `public_anchor_ids` value (`q_A`
versus `q_B`); `public_goal_id` differs later. All preceding bytes and lengths
are identical. Stage 0 records and binds the zero-based offset of that first
different byte as `o_goal` for every alpha-renamed twin and verifies the full
prefix `[0:o_goal)` is byte-identical. The cue does not expose the action
mapping.

Atoms-only B uses exactly four reads:

```text
ROUTE_BY_CUE -> a_u;
ATOM_SUCCESSOR(U_u) -> b_u;
ATOM_SUCCESSOR(B) -> c;
TERMINAL_TO_TARGET -> t_goal.
```

Phase-D h0 and h1 both begin from a sterile reset with byte-identical `G_D`,
catalog, request 1, and actor history:

```text
1 REQ LINK_SUCCESSOR(state=U_uD,goal=G_D,anchor=U_uD)
  RET row(U_uD -> [b_uD,c]); ACT b_uD; ACT c; public state C
2 REQ NEW_SUCCESSOR(state=C,goal=G_D,anchor=[C,D])
  h0 RET row(C ->[n_0]-> D); ACT n_0; public state D
  h1 RET row(C ->[n_1]-> D); ACT n_1; public state D
```

The h0/h1 request bytes are identical. Under JCS, the first outcome-dependent
actor-visible byte is the first differing byte inside `row_or_fixed_pad` in
return 2 (`n_0` versus `n_1`). Stage 0 binds its zero-based offset `o_outcome`
and verifies that the complete actor-visible trace prefix before that offset
is byte-identical across twins. Raw C history/outcome, h, row provenance, and
prior context are absent.

### 4.4 Exhaustive read theorem

Stage 0 constructs the finite labeled transition system over:

```text
(phase,public state,public goal,reads remaining,returned anchors,
 executed action prefix,status history)
```

and enumerates every deterministic adaptive policy by exhaustively exploring
every legal query, every possible FOUND/MISS/BLOCKED return class, every legal
action cited by a return, repeats, early stopping, and all branches. This is a
reachable-state model check, not sampling policies.

It must prove and publish the transition table and digest showing:

1. every READ exposes at most one row and no score/index/order metadata;
2. no atoms-only policy reaches either B terminal in <=3 reads;
3. at least one atoms-only policy reaches each B terminal in exactly 4;
4. FULL reaches each B terminal in exactly 3 and no fewer;
5. D reaches D in exactly 2 only with both the old link and correct new row;
6. removing either D row makes D unreachable within budget;
7. no goal-first, repeated, MISS-branching, returned-endpoint, or other legal
   policy bypasses these minima.

The fixed 32-slot bank matches scan geometry. `32 > read budget` is not used
as a lower-bound proof.

### 4.5 Exact actor-side noninterference

No mutual-information claim over root-unique aliases is made. Stage 0 instead
proves these exact finite properties for every generated factor cell and
registered alpha-renaming:

1. Catalog, request, fingerprint, counter, error, and pad bytes are pure
   functions only of allowed public history, request, and remaining budget.
2. Candidate score vector, winner index, order, threshold, retries, and raw
   timing are backend-only. Calls are padded to the frozen duration bucket;
   timeout/exception is a root failure, never actor information.
3. In every answer-changing hit-matched twin/derangement, actor-visible
   metadata is byte-identical after registered alpha-renaming; only the named
   canonical row payload differs. Status, serialized/token length, query
   count, and legal-action class match.
4. `MISS` controls are declared availability interventions and excluded from
   any hit-matched assertion.
5. The generator proof shows opaque alias assignment is independent of
   `b,z,u_A,u_B,u_D,h`, condition, and correct action.

`CATALOG_PERMUTE` must preserve all FULL returned semantics/actions for every
registered permutation. `READ_BINDING_SWAP` on a FULL hit must preserve the
entire envelope while replacing only the row ID/payload, and must redirect the
next cited action to the registered legal wrong action. These are model-level
acceptance cells, not CPU transform claims.

Endpoint chance levels are reported only for named constructs: binary source
choice `.5`, one lane of eight `.125`, and exact two of eight `1/28`. There is
no universal `.25` proxy ceiling.

## 5. Writer inheritance and exact trained decks

### 5.1 Qualified writer only

M inherits **exactly** the writer recipe `W*` that has already passed W0 and
the old/new coexistence canary. If Q0 qualifies, `W*=Q0`; if a prospectively
registered repair qualifies, `W*` is exactly that repair. M does not assume
cross-view, paraphrase, replay, rank, dose, masking, or preservation choices
that W did not qualify, and it adds none after observing M.

No M LoRA fit may begin before `W*`, its tokenizer, renderer, rank, optimizer,
learning rate, steps, masks, reader scorer/threshold, and coexistence gate are
frozen by their own evidence. Every M build starts from the same immutable
birth checkpoint and is a clean-base reconstruction.

### 5.2 S1 decks: three fits

| build | source material | pair/link material | isolated purpose |
|---|---|---|---|
| `FULL_OLD` | authentic 3:1/1:3 child events | supported child-selected links | positive old carrier |
| `SOURCE_DERANGED_OLD` | crossed 2:2/2:2 derived material | exact authentic links | source binding at C |
| `DREAM_DERANGED_OLD` | exact authentic source | hit-matched fixed-point-free link bindings | link content at B |

Every deck also contains the exact same grounded foundation rows for all eight
`q_i -> a_i` route mappings and both `T_A/T_B -> t_A/t_B` terminal mappings.
The exact deck-diff receipt must show that only the named canonical target
payloads and necessarily new derived IDs differ. Visible provenance fields
are generic fixed-count opaque citation slots with role-independent ID
distributions. True donor/derivation/provenance is audit-only. Every deck
matches row/view count, serialized and token-length histograms, target masks,
renderer multiplicities, visits, deck positions, batches, optimizer steps,
and fit seed law.

SOURCE_DERANGED must preserve FULL B traces. DREAM_DERANGED must preserve FULL
C source traces. Any unrelated-action/interface drop beyond `W*`'s frozen
bound invalidates the root; generic corrupt-carrier damage is never semantic
evidence.

### 5.3 S2 target-like gradient-bearing PAD: three fits

At A0 the root seals a disconnected authentic child event `P --p--> Q` and a
canonical row `d_pad`. Its compilation release is reserved for the S2 control.
It is truthful and root-specific but cannot satisfy any B, C, or D predicate,
and neither P nor Q is a legal B/C/D actor anchor.

The alias generator selects a prequalified token-isomorphic triple for
`n_0,n_1,d_pad`. All three rows have exactly the same:

- canonical field/schema and visible citation count;
- serialized input bytes length and tokenized input length;
- serialized target bytes length and tokenized target length;
- supervised-token count and exact loss-mask positions;
- renderer count and visits per view;
- reserved deck position and presentation stratum;
- batch exposure, number of optimizer steps, and fit RNG law; and
- 32-slot reader envelope and carrier-validation query shape.

The targets are gradient-bearing; `d_pad` is never loss-masked padding. The
Stage-0 receipt publishes row, token, mask, visit, deck, batch, and step diffs
for all three and requires every diff outside payload token IDs to be zero. If
this exact match fails, the root is structurally invalid before fitting; no
extra pad fit is added.

All three S2 builds reconstruct from birth using the exact FULL old deck plus
one reserved-slot row:

| build | one S2 row | public support |
|---|---|---|
| `FULL_NEW_h0` | `n0` | truthful h0 C action/outcome/admission |
| `FULL_NEW_h1` | `n1` | truthful h1 C action/outcome/admission |
| `FULL_OLD_PLUS_PAD` | `d_pad` | disconnected authentic P action/outcome |

The old+pad carrier is one matched baseline evaluated in both h repeated-
measure worlds. It has no h-dependent input or row. A root that fails the
upstream FULL C admission is adverse-filled and skips all three S2 fits by the
predeclared futility rule; it never leaves a denominator.

## 6. Chronology and exact inference controls

### 6.1 Two cycles

```text
A0 seal root, both h worlds, manifests, future objects and orders
A1 child performs source, eight-lane ablation, and pad-source actions;
   public outcomes append immutable events
A2 child SELECT_PAIR_SET is sealed at the first canonical byte boundary
A3 reveal support arena; child performs fresh validation actions; compiler
   admits only selected and independently supported links
S1 fit FULL_OLD, SOURCE_DERANGED_OLD, DREAM_DERANGED_OLD from birth with W*
B  sterile-reset A/B goal twins and reader controls
C-p four sterile destroyed source inverse probes; no writes
C  FULL only: declaration -> experiment action -> public outcome -> admission
S2 fit FULL_NEW_h0, FULL_NEW_h1, FULL_OLD_PLUS_PAD from birth with W*
D  sterile-reset delayed h twins and reader/cut controls
```

The first goal/outcome-dependent byte boundaries from Section 4 are stored in
the trace receipt. Raw A/C events, child context, DREAM text, scores, cache,
workspace state, and prior process state cannot cross a sterile reset.

### 6.2 Inference-only control definitions

These add no trained fits:

| control | exact intervention | required result |
|---|---|---|
| `S1_OFF` | unmount carrier in B and C; identical public history/catalog/budget | every carrier-dependent B/C trace fails |
| `CATALOG_PERMUTE` | backend candidate order only; actor catalog bytes fixed | FULL payloads/actions invariant for all registered orders |
| `READ_BINDING_SWAP` | replace a FULL FOUND payload with hit/status/length/query/legal-action-matched false row | next cited action redirects to registered legal wrong action; no interface damage |
| `GOAL_ONLY` | complete public goal and ordinary catalog/API visible, carrier absent, reader MISS | B/D carrier-dependent trace fails |
| `CATALOG_ONLY` | catalog visible, goal-neutral matched prompt, carrier absent | target trace fails |
| `WRONG_ROOT` | source-disjoint carrier with fixed slot mapping | every root-specific trace fails |
| `LINK_CUT_B` | at B only, suppress required link return to matched fixed-pad MISS | B link availability is necessary |
| `OLD_CUT_D` | at D only, suppress old link return after S2 | old half of delayed conjunction is necessary |
| `NEW_CUT_D` | at D only, suppress new-row return after S2 | new half of delayed conjunction is necessary |
| `NO_SLEEP2` | mount FULL_OLD at D | diagnostic absence of new write; not equal-work causal baseline |
| `OLD_PLUS_PAD` | mount trained FULL_OLD_PLUS_PAD at D | equal-work S2 causal baseline fails both h traces |
| `TEXT_FULL` | exact FULL rows in text carrier behind identical API | complete assay ceiling passes |
| `TEXT_ATOMS_READ4` | exact atomic rows in text carrier, B budget four | both goals pass in exactly four reads |

`LINK_CUT_B` and `OLD_CUT_D` are distinct availability interventions at
different cycles/endpoints: the former establishes first-cycle B reliance on
the selected link; the latter establishes that the preserved old link remains
necessary when combined with the new row at D. Neither is a hit-matched
content intervention; `READ_BINDING_SWAP` supplies that control.

All carrier-free controls are run with identical charged scorer calls, fixed
pads, query budgets, error behavior, and padded duration. A MISS difference is
reported as intended availability, never as content noninterference.

## 7. Exact scorer and root variables

### 7.1 Canonical trace scorer

Each endpoint emits one JCS trace object:

```text
Trace {
  protocol, root_id, condition, h_or_null, goal_id,
  ordered_events: [
    {kind:READ, exact_request_bytes, exact_return_bytes},
    {kind:ACT, action_id, cited_row_id, pre_state, public_outcome, post_state}
  ],
  terminal_state, reads_used, malformed_count
}
```

The scorer is a pure function of this object and the presealed public root
graph. It reads no model text beyond canonical READ/ACT objects. A trace scores
1 only if every action is canonical, legal, in order, cites the immediately
available returned row, follows the public transition, respects the budget,
and reaches the exact target. Any permissive parse, semantic repair,
uncited/extra action, malformed object, wrong endpoint, or process failure is
0.

Define:

```text
Y_B(r,K,g) in {0,1}  valid B trace for build/control K and g in {A,B}
Y_C(r,K,j) in {0,1}  correct authentic source label on probe j=1..4
Y_D(r,K,h) in {0,1}  valid D trace for h in {0,1}
```

`Y_C` uses Section 3.4's authentic label even for SOURCE_DERANGED. Source
accuracy is the mean of four repeated forks. No deranged tie is relabelled.

### 7.2 Root-level causal scalars

Missing/skipped/process-failed cells receive endpoint value 0. The fixed
root-level scalars are:

```text
S_r = mean_j Y_C(r,FULL_OLD,j)
      - mean_j Y_C(r,SOURCE_DERANGED_OLD,j)

M_r = min_g [Y_B(r,FULL_OLD,g)
             - Y_B(r,DREAM_DERANGED_OLD,g)]

U_r = min(
        min_g [Y_B(r,FULL_OLD,g) - Y_B(r,S1_OFF,g)],
        mean_j Y_C(r,FULL_OLD,j) - mean_j Y_C(r,S1_OFF,j)
      )

W_r = min_h [Y_D(r,FULL_NEW_h,h)
             - Y_D(r,FULL_OLD_PLUS_PAD,h)]

F_r = min_h min(
        Y_D(r,FULL_NEW_h,h) - Y_D(r,OLD_CUT_D_h,h),
        Y_D(r,FULL_NEW_h,h) - Y_D(r,NEW_CUT_D_h,h),
        Y_D(r,FULL_NEW_h,h) - Y_D(r,READ_BINDING_SWAP_D_h,h),
        Y_D(r,FULL_NEW_h,h) - Y_D(r,WRONG_ROOT_h,h)
      )
```

For `U_r`, the S1_OFF C condition uses the same desired-outcome probes and
strict returned-row/action dependency. `FULL_NEW_h` means the carrier whose
truthful new row matches that h world; it is never a runtime row substitution.

### 7.3 Noncompensatory `R_r`

`R_r=1` only if every item below passes on the same presealed root:

1. Generator, complete graph, immutable-ID, exact-text, finite-reader model
   check, noninterference, air-gap, reset, prefix, and token/work receipts pass.
2. Every source/ablation/support/pad-source row follows the child's committed
   action and causally later public outcome; no harness/parent/draft action is
   used.
3. The child's sealed pair set precedes blueprint visibility, equals the two
   evidence-indicated lanes, and both fresh support tests admit the exact
   selected links. Agreement with the mechanical ceiling is reported.
4. All three S1 carriers pass registered row extraction, canonical interface,
   unrelated-action non-harm, carrier-origin, and wrong-root gates.
5. FULL passes both B goals in exactly three reads; TEXT_ATOMS_READ4 passes in
   exactly four; GOAL_TWIN redirects request/payload/path/action.
6. `S1_OFF`, `GOAL_ONLY`, `CATALOG_ONLY`, `LINK_CUT_B`, and WRONG_ROOT fail
   their carrier/link-dependent B traces. Every registered CATALOG_PERMUTE
   preserves FULL B. READ_BINDING_SWAP redirects to its legal wrong action and
   fails semantically without interface/parser damage.
7. DREAM_DERANGED fails both link-dependent B traces while preserving FULL's
   source endpoint; SOURCE_DERANGED preserves both FULL B traces. Thus `M_r>0`.
8. FULL source accuracy is 1.0, desired T/O redirects the semantic action and
   family, SOURCE_DERANGED is scored against the frozen authentic labels and
   has lower accuracy by at least .25, DREAM_DERANGED matches FULL, and
   `S_r>0`, `U_r>0`.
9. In both h worlds, FULL makes a canonical declaration, selects a target-
   family experiment, receives the authentic public outcome, and admits
   exactly `n_h`; nuisance choice/coincidence never admits a row.
10. Both FULL_NEW carriers extract/retain every registered critical old row,
    extract only their own truthful new row, preserve B, and pass interface/
    non-harm/canary gates. OLD_PLUS_PAD extracts `d_pad`, retains old rows, and
    exposes no D-usable new row.
11. Both h FULL_NEW traces reach D in exactly two reads with distinct final
    actions. OLD_PLUS_PAD, NO_SLEEP2, OLD_CUT_D, NEW_CUT_D, WRONG_ROOT, and the
    D binding swap fail. `W_r>0` and `F_r>0`.
12. TEXT_FULL passes every constructive endpoint; all positive model traces
    have complete carrier-origin receipts; no raw event/DREAM/C byte survives
    reset.

Later success cannot compensate for any earlier failure. A global structural
failure invalidates the instrument. A root-local child, execution, fit, or
process failure is adverse-filled and remains in all denominators.

## 8. Stages, tests, and stopping

### 8.1 Stage 0: deterministic closure, zero fits

Exhaust the full finite factor space, not a 64-fixture sample:

- every `(b,h,z,E)` admission case and every route/lane/goal/h trace;
- every candidate template, alias-pool class, catalog order, hit-matched
  derangement, immutable ID, and exact byte/token/work equality;
- the actor/backend boundary and all exact noninterference equalities;
- every adaptive legal READ policy and the 3-read/4-read/2-read minima;
- every scorer mutation, cut, carrier-free route, reset, and air-gap denial.

Publish the generator version, manifest digests, complete typed graph,
canonical schemas/example bytes, reachable-state/model-check digest, root
truth table, and zero-diff receipts. Any failure stops M before text/model work.

### 8.2 Stage 1: exact-text feasibility, separate roots

Run `T1...T4`. Stop on any structural failure or fewer than 2/4 complete
roots. If 2/4 or 3/4, run `T5...T8` and require at least 6/8. If 4/4, the
text feasibility gate passes. This stage tests the task/API and child sealing;
it is descriptive only and cannot select fitted DEV roots.

### 8.3 Stage 2: two-root staged kill

On exactly `D1,D2`, first fit only the three S1 builds: **six fits**. Both
roots must satisfy every S1 gate, including positive `S_r,M_r,U_r`, orthogonal
control equivalences, reader controls, interface/non-harm, and exact traces.
Any failure stops before S2.

Only then fit the three S2 builds for each root: **six additional fits**. Both
roots must satisfy S2 extraction/retention, pad matching, both h outcomes,
positive `W_r,F_r`, all D cuts, and `R_r=1`. Any failure stops widening.

### 8.4 Stage 3: nested eight-root DEV

Run `D3...D8` with S1 first per root and S2 only after the frozen upstream
gate. Upstream failures skip futile S2 fits but remain zeros. Require at least
6/8 joint `R_r=1`, every registered component direction on at least 6/8 roots,
and zero structural failures. Freeze all mechanics afterward; DEV is not
confirmatory evidence.

### 8.5 Stage 4: fixed sixteen-root confirmation

Run all `C1...C16` in their presealed order without replacement, extension,
early-success stopping, or outcome-dependent reruns. Each confirmation root
is an iid draw of the complete generator object, including an independent
Latin-rotation draw; each root's internal schedule remains balanced across
arms/controls/device positions. Upstream S1 failures may skip S2 compute but
remain adverse zeros.

For every root compute `S_r,M_r,U_r,W_r,F_r,R_r` once. The co-primary ordered
hypotheses are:

```text
H_S: Pr(S_r>0) <= .5
H_M: Pr(M_r>0) <= .5
H_U: Pr(U_r>0) <= .5
H_W: Pr(W_r>0) <= .5
H_R: Pr(R_r=1) <= .5
```

Test them in the fixed sequence `S -> M -> U -> W -> R`, each with the exact
one-sided binomial test at alpha `.05`, stopping confirmatory rejection at the
first non-rejection. This fixed-sequence gatekeeping controls familywise type-I
error at `.05`; no alpha split is needed. Zero, missing, skipped, and failed
roots are non-successes. Treatment labels are not randomized, so no sign-flip
or treatment-randomization test is claimed.

For `n=16`, each tested component needs at least 12 positive roots:

```text
P[Binomial(16,.5) >= 12] = 2517/65536 = .0384063720703125.
```

Report for each component the count, exact p-value, one-sided 95% Clopper--
Pearson lower bound for `Pr(delta>0)`, and all 16 scalar magnitudes/failure
reasons. The intervals are componentwise and interpreted only under the frozen
gatekeeping order; they are not simultaneous intervals. `F_r` and each named
control are mandatory parts of `R_r` and are also tabulated descriptively.

`12/16 R` is the bounded reliability test only; it does not replace `S,M,U,W`.
The child exact-pair count is reported against the deterministic necessity
ceiling and, descriptively, the registered `Binomial(16,1/28)` chance
construct. No child-versus-mechanical superiority test is run.

## 9. Fatal shortcuts

Any global occurrence invalidates the instrument; a demonstrably root-local
occurrence adverse-fills that root:

1. role/root/goal/order/fit seed selected or regenerated after behavior;
2. public ablation evidence, endpoint syntax, frequency, or roster exposes
   anything beyond the declared mechanically determinative necessity table;
3. blueprint/future goal/action/outcome/theorem visible before the exact child
   selection seal;
4. compiler proposes, ranks, replaces, repairs, or adds a link;
5. source actions/outcomes are not authentic, repeated, ordered child events,
   or the derangement fails the exact crossed 2:2/2:2 contract;
6. source or link derangement changes any non-named row, visible provenance,
   hit/status/length/query/legal-action geometry, mask, dose, or work;
7. audit-only provenance/donor/derivation/role enters training, reader, actor,
   or scorer bytes;
8. public candidate bank construction consults truth, theorem, correct row,
   expected trace, future goal, child outcome, or pair selection;
9. actor sees score/index/order/timing/candidate metadata, or a query exists
   outside the complete legal table;
10. the exhaustive adaptive-policy check fails any read minimum or bypass;
11. carrier-free, S1_OFF, catalog permutation, binding swap, cut, wrong-root,
    or exact-text control misses its frozen result;
12. binding swap wins by illegal syntax/action rather than legal semantic
    redirection;
13. PAD is masked, repeated old data, ungrounded, queryable from B/C/D, or
    differs in tokens/masks/visits/position/batches/steps from n0/n1;
14. one runtime substitution impersonates the two truthful S2 adapters, or
    both new rows enter one carrier;
15. nuisance coincidence admits a row without singleton public posterior;
16. raw experience, DREAM, C outcome, cache, context, workspace, or query
    state crosses a sterile reset;
17. LoRA is mounted outside the typed READ transaction while the effect is
    called memory carriage;
18. reader/actor/compiler substitutes, repairs, or semantically completes a
    positive row;
19. M changes or tunes `W*`, reader, rank, dose, mask, threshold, or any knob
    on M results;
20. failed roots are retried, dropped, permissively reparsed, or replaced;
21. twins, goals, probes, calls, renders, or checkpoints are counted as roots;
22. generic corruption/non-harm damage is counted as semantic specificity;
23. clean-base cumulative reconstruction is called in-place growth; or
24. parenting/final-gym/another root or lineage contaminates the fixed child.

## 10. Exact fit arithmetic and resource reporting

```text
S1 per root:                    3 fits
S2 per upstream survivor:       3 fits
maximum per complete root:      6 fits

two-root S1 kill:               2*3 = 6 fits
two-root full kill:             2*6 = 12 fits total
eight-root nested DEV maximum:  8*6 = 48 fits total
sixteen-root confirmation max: 16*6 = 96 fits
DEV + confirmation maximum:          144 fits
```

If `t_fit` is the measured device-time for one exact `W*` deck, maximum
training cost is `N_fit*t_fit`, with actual cost reduced only by the presealed
S1 futility rule. Report action, inference, reset, validation, serialization,
and process-start overhead separately from measured logs. Do not publish an
all-in GPU-hour range, ideal packing bound, or wall-time promise before the
exact implementation is timed. Aggregate device-time and serial critical path
are different quantities.

## 11. Pre-fit self-audit disposition

This v3 disposes the two fresh audits as follows:

- DREAM is narrowed to the child-selected pair set indicated by registered
  public ablation evidence; intelligence/mechanical-unrecoverability language
  is deleted.
- The complete typed graph, public goal constraints, action semantics, legal
  queries, canonical scorer/trace objects, exact A/B/D traces, and first
  dependent bytes are published.
- Mutual information and universal `.25` proxies are replaced by exact
  actor-side noninterference and endpoint-specific chance constructs.
- Every adaptive legal READ policy is covered by a finite reachable-state
  model check proving FULL=3, atoms=4, and D=2.
- S1_OFF, catalog permutation, binding swap, carrier-free, cuts, wrong-root,
  and exact-text controls are literal fields of noncompensatory `R_r`.
- SOURCE_DERANGED uses the authentic counterfactual label, complete repeated
  nuisance/admission truth is enumerated, and derivation provenance is
  audit-only.
- `FULL_OLD_PLUS_PAD` is a truthful disconnected, gradient-bearing target-like
  row exactly matched on tokens, masks, positions, visits, batches, steps, and
  reader envelope.
- DEV is one presealed nested eight-root prefix; the root/order/generator law
  is frozen; text roots and confirmation roots are separate.
- `M_r` and `W_r` use conservative minima, all source scoring is fixed, exact
  binomial/Clopper--Pearson tests and multiplicity are specified, and the
  `12/16` reliability test remains distinct from component causality.
- `LINK_CUT_B` and `OLD_CUT_D` have different phases and estimands.
- Unsupported GPU-hour and wall-time bounds are removed.
- M inherits the actually qualified writer `W*`; no W0 result is assumed.

No additional standing trained condition is required. No M fit is ready until
`W*`, the old/new canary, Stage-0 closure, and exact-text feasibility all pass.

## Source lineage

- `research_notes/analysis/2026-09-12_m_core_v2_statistics_visibility_audit.md`;
- `research_notes/analysis/2026-09-12_m_core_v2_fresh_adversarial_audit.md`;
- `research_notes/analysis/2026-09-12_m_core_minimal_exact_two_cycle_design_v2.md`;
- `research_notes/analysis/2026-09-12_m_core_revised_three_condition_adversarial_audit.md`;
- `research_notes/analysis/2026-09-12_think_dream_sleep_minimum_decisive_program_audit.md`;
- `research_notes/analysis/2026-09-12_connected_relay_scaffolding_adversarial_review.md`;
- `research_notes/2026-09-12_end_to_end_goal_closure_synthesis.md`;
- `research_notes/2026-09-11_pcfl_relay_readiness_rework.md`.
