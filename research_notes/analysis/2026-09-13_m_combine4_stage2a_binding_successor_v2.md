# Binding successor v2: exact M-COMBINE-4 Stage 2A source contract

**Date:** 2026-09-13 PT  
**Status:** binding design and source/CPU contract. If the root adopts these
exact bytes, Astra may author and CPU-test the source described here. This is
not authority to materialize a scientific root, invoke the real tokenizer or
model, fit or mount an adapter, use a GPU, inspect a sealed downstream root, or
make a scientific claim.  
**Preserves:** the primary question, three model states, 64 train cases, 256
unique targets, D1/D2 doses and gates, claim boundary, and Stage-2A cost caps in
`2026-09-13_m_combine4_stage2a_binding_successor_v1.md`.  
**Supersedes:** v1 wherever it left CHECK schemas, material topology, null
semantics, pair composition, prefix coupling, text separation, protocol bytes,
canaries, topology signatures, scanners, intervention entailments, or later
execution pins unspecified.  
**Closes:** findings A--G in
`2026-09-13_m_combine4_stage2a_implementation_readiness_delta_plan.md`.

## 1. Decision and invariant question

Stage 2A still asks, in order:

1. Can one target-content/topology-disjoint rank-8 birth adapter execute the
   exact-text loop `state + goal -> READ -> returned relation -> STEP -> public
   outcome -> keep/revise -> READ again or STOP` on autonomous held tasks?
2. Does training on coherent accumulated histories help beyond training the
   exact same locally sufficient target decisions as separately reset atoms?

The states remain BASE, CLOSED, and ATOM-LOCAL. CLOSED and ATOM-LOCAL use the
same 256 exact targets and presentation order. Their prefixes intentionally
differ. This is a curriculum-format comparison, not LINKED versus causally
unlinked data and not gradient equivalence.

A positive remains a lab-taught exact-text controller. It is not parenting,
own-life learning, parametric memory, general reasoning, recurrence, or the
Dream--LoRA--Think flywheel. Later stages remain unbound.

## 2. Exact public wire contract

All authored text is strict UTF-8 and ASCII-only. `LF` means byte `0x0a`; CR is
never legal. Actor output contains **no** terminal LF. Service blocks use LF
between lines and no terminal LF. No caller trims, repairs, canonicalizes,
selects a line, strips a fence, or retries.

### 2.1 Opaque identifiers

The only public identifier forms are:

```text
node       M2AN_[A-Z2-7]{12}
query      M2AQ_[A-Z2-7]{12}
event      M2AE_[A-Z2-7]{12}
route-row  M2AI_[A-Z2-7]{12}
port       M2AP_[A-Z2-7]{12}
receipt    M2AR_[A-Z2-7]{12}
```

`M2AN_AAAAAAAAAAAA`, `M2AQ_AAAAAAAAAAAA`, `M2AE_AAAAAAAAAAAA`,
`M2AI_AAAAAAAAAAAA`, `M2AP_AAAAAAAAAAAA`, and `M2AR_AAAAAAAAAAAA`
are reserved invalid sentinels and may never be allocated.

### 2.2 System message, exact bytes

The system message is the following ASCII text, with LF between displayed
lines and no final LF:

```text
You are the actor in M-COMBINE-4.
Return exactly one action and no other bytes. Do not add whitespace, a code fence, CR, or LF.
Legal actions are:
THINK KEEP <event-id>
THINK REVISE <event-or-query-id>
READ INDEX <node-id>
READ RELATION <query-id>
STEP <port-id>
STOP
Identifiers are opaque.
READ INDEX asks the exact service for a ROUTE directory at a public node.
READ RELATION asks the exact service for an EVENT block at an opaque query.
A ROUTE row states that its QUERY is relevant to its FOR goal while AT its state.
An EVENT row is relevant only when both FOR equals the current GOAL and AT equals the latest CURRENT.
For a relevant EVENT, DID is a possible STEP, GOT is its predicted next CURRENT, and RECOVER is a query to use only if the public outcome contradicts GOT.
KEEP means the public CURRENT matched GOT. REVISE means a READ was MISS or irrelevant, or the public CURRENT contradicted GOT.
STOP is correct only when the latest CURRENT equals GOAL.
The service returns registered exact text or MISS. Unsupported actions terminate the task.
```

These are interface semantics, not a task-local command list or a scheduled
route. BASE, CLOSED, and ATOM-LOCAL always receive these identical bytes.

### 2.3 Task and host messages, exact bytes

The initial user message is:

```text
TASK
START {node}
GOAL {node}
CURRENT {node}
```

There is no final LF. Braces above mark renderer substitutions and never enter
material. An accepted THINK receives user content `ACK`. An accepted STEP
receives:

```text
WORLD
CURRENT {node}
```

An accepted READ receives user content `SERVICE` + LF + the exact service
return. A terminal invalid action receives no repair message. The latest WORLD
CURRENT, if any, is authoritative; otherwise the task CURRENT is.

### 2.4 Actor grammar

The entire raw actor output must full-match one of:

```text
THINK KEEP M2AE_[A-Z2-7]{12}
THINK REVISE (?:M2AE|M2AQ)_[A-Z2-7]{12}
READ INDEX M2AN_[A-Z2-7]{12}
READ RELATION M2AQ_[A-Z2-7]{12}
STEP M2AP_[A-Z2-7]{12}
STOP
```

KEEP is event-only. REVISE names the implicated EVENT after a STEP mismatch or
the implicated query after MISS/irrelevance. The static language has the four
command classes THINK/READ/STEP/STOP and never enumerates task-local operands.

### 2.5 Service rows and skins

Skin 0 rows are:

```text
ROUTE {route} AT {node} FOR {goal} QUERY {query}
EVENT {event} AT {node} FOR {goal} DID {port} GOT {node} RECOVER {query} EVIDENCE {receipt}
```

Skin 1 rows are:

```text
ROUTE {route} FOR {goal} QUERY {query} AT {node}
EVENT {event} FOR {goal} AT {node} GOT {node} DID {port} RECOVER {query} EVIDENCE {receipt}
```

One case uses one skin throughout. `READ INDEX n` returns `ROUTES` followed by
exactly 24 ROUTE rows separated by LF. `READ RELATION q` returns `EVENTS`
followed by exactly four EVENT rows separated by LF, or literal `MISS`. There
is no final LF. Row order is part of the bytes. A registered irrelevant block
has four well-formed EVENT rows but zero rows with both `FOR == GOAL` and
`AT == CURRENT`. A useful block has exactly one such row. The service receives
no task, GOAL, scorer, or hidden route; it is a fixed request-to-bytes map.

Every candidate port in a returned EVENT block is a legal public world port at
the EVENT's AT state unless that row is explicitly the pre-authored erroneous
belief in a STEP-mismatch recovery prefix. A legal STEP follows the world's
fixed port transition, which may disagree with a mistaken EVENT's GOT. A
request not in the registry returns `MISS`.

## 3. Deterministic opaque allocation and separation

### 3.1 Seeds and allocation

The fixed master byte string is:

```text
M-COMBINE-4/STAGE2A/V2/2026-09-13
```

The domain labels are exactly `birth_train`, `dose_intervention`,
`dose_chain`, `generic_canary`, `confirmation_reserved`, and
`writer_reserved`. For each domain and kind, allocate the declared number of
tokens by:

```text
digest = SHA256(master || NUL || domain || NUL || kind || NUL ||
                uint32_big_endian(serial))
token  = kind_prefix || first_12_RFC4648_base32_characters(digest)
```

Serials start at zero. A collision or reserved all-A suffix invalidates v2;
do not skip a serial, change a seed, or retry. Public tokens are created before
semantic roles. Assign them by sorting tokens on
`SHA256(master || NUL || domain || NUL || "pool-order" || NUL || token)` and
sorting semantic role keys on
`SHA256(master || NUL || domain || NUL || "role-order" || NUL || role_key)`,
then zip the lists. A role key never enters token generation. Save pool,
role-list, and permutation hashes in evaluator custody, never actor input.

The exact ASCII `kind` strings and prefixes are `node/M2AN_`, `query/M2AQ_`,
`event/M2AE_`, `route/M2AI_`, `port/M2AP_`, and `receipt/M2AR_`. For the first
four domains, the declared count for a kind is exactly the length of the
canonical semantic role-key list produced by sections 4, 9, 10, and 13; no
unused token is allowed except each explicitly named unregistered MISS query.
Role keys are ASCII path strings formed from the literal domain, pair/world
ID, state role, goal index as two decimal digits, block purpose, candidate
slot as one decimal digit, and kind, joined by `/` in that order. Use literal
`-` for an inapplicable component; never omit a component. Sorting is raw
ASCII byte order. The manifest records the complete role-key list so the
independent checker derives the same count. The two reserved domains allocate
exactly 4,096 tokens of each kind from serials `0..4095`; this reserves bytes,
not future task semantics.

Row display order is a separate permutation using the label `display-order`.
Training presentation order is a separate permutation using `target-order`.
No world/case index, family, factorial cell, goal side, route choice, target
class, or display position is an input to public token generation.

For train display only, the permutation seed payload is the ASCII template key
`pair_type/b/family/state_role/block_role`; it deliberately excludes p, flow,
member, public IDs, and target. The permutation is the ascending order of
`SHA256(master || NUL || "display-order" || NUL || template_key || NUL ||
uint32_big_endian(candidate_index))`. Therefore `(p,m)` and recovery match
`(p-1,m)` have identical semantic display-position schedules despite disjoint
identifiers, and causal-pair members share the same schedule.

### 3.2 What “disjoint text” now means

V1's literal zero-text-overlap wording is replaced. Exact concrete identifier
sets must be pairwise disjoint across all six domains. Exact content-bearing
lines after removing the protocol allowlist below must also be pairwise
disjoint for every materialized domain. `confirmation_reserved` and
`writer_reserved` preallocate and seal their ID pools only; their future task
semantics remain unmaterialized and closed.

The only allowed shared lexical atoms are the exact system message, actor
keywords, task/host labels, service headers, row field labels, `MISS`, the
ASCII space, LF, and the identifier type prefixes/regexes in section 2.
Concretely:

```text
THINK KEEP REVISE READ INDEX RELATION STEP STOP TASK START GOAL CURRENT
ACK WORLD SERVICE ROUTES ROUTE AT FOR QUERY EVENTS EVENT DID GOT RECOVER
EVIDENCE MISS CANARY COPY EXACTLY M2AN_ M2AQ_ M2AE_ M2AI_ M2AP_ M2AR_ < > -
```

The line-overlap allowlist is exact: every individual line of the section-2.2
system message plus `TASK`, `ACK`, `WORLD`, `SERVICE`, `ROUTES`, `EVENTS`,
`MISS`, `CANARY`, `COPY EXACTLY`, and `STOP`. The lexical-atom allowlist
artifact includes the exact system bytes and SHA-256, the token list above,
and exactly ASCII space, LF, `_`, `-`, `<`, and `>`. Canonicalized templates
may overlap; a concrete instantiated line outside the exact line allowlist
may not occur in two domains.

Do not inspect, import, hash, or canonicalize a sealed PCFL or GOAL-BRAID
instance. Instead require a committed public namespace certificate stating
that those generators never allocate the reserved ASCII prefix `M2A` and
listing their public forbidden role-core specifications. If that certificate
is absent, ambiguous, or later contradicted, separation fails closed. This is
a construction proof, not a claim that unknown sealed bytes were compared.

## 4. Exact 64-case training factorial

### 4.1 Pair-index allocation

There are 32 `causal_pair_id`s `p00` through `p31`, each with members `m0` and
`m1`, producing 64 cases. Let `p` be the integer and `b = floor(p / 4)`.

```text
p < 16                 goal-switch pair
p >= 16                returned-relation/deep-swap pair

p mod 4 = 0            family A, ordinary
p mod 4 = 1            family A, recovery
p mod 4 = 2            family B, ordinary
p mod 4 = 3            family B, recovery

b mod 2 = 0            final state reached
b mod 2 = 1            final state unresolved
floor(b / 2) mod 2 = 0 skin 0
floor(b / 2) mod 2 = 1 skin 1
```

For goal-switch pairs, `m0` has goal side left and `m1` right. Both members
share identical world, store, identifiers, skin, display order, family, flow,
and terminal class; only the task GOAL, executed path through that fixed
store, target, and evaluator answer differ. For relation/deep-swap pairs, both
members have goal side
`b mod 2`, and share task, identifiers, candidate EVENT/port/destination IDs,
row order, family, flow, skin, and terminal class. Swap the `FOR` values of
candidate EVENT display positions `u` and `(u + 2) mod 4`, where
`u = (3*b + family_bit) mod 4`; this changes the unique relevant row and
therefore the correct STEP. No candidate ID, port, GOT, RECOVER, receipt, or
display position changes.

This yields exactly 32/32 for family, flow, terminal class, goal side, and
skin, and 16 pairs of each causal-pair type. Each causal-pair type contains
four pairs in every family x flow cell. This `p mod 4`, `b mod 2`, and
`floor(b/2) mod 2` table, together with section 4.2's fixed pair list, is the
entire predeclared remainder rotation; there is no generator-chosen remainder
assignment.

### 4.2 Recovery subtype and ordinary matching

Recovery subtype is pair-level and exactly:

```text
STEP/outcome mismatch  p01 p03 p05 p07 p25 p27 p29 p31   = 16 cases
strict MISS            p09 p13 p19 p23                   =  8 cases
irrelevant return      p11 p15 p17 p21                   =  8 cases
```

Within each subtype, family, terminal class, goal side, and skin are each
balanced exactly; causal-pair type is also balanced. The checker must report
those tables.

Every recovery case `(p,m)` has `recovery_match_id = (p-1,m)`. The matched
ordinary case therefore has disjoint public identifiers but the same
causal-pair type, family, terminal class, goal side, skin, semantic route depth,
and display-position schedule. This is a bijection over all 32 recovery and 32
ordinary cases. It is distinct from the within-pair causal matching.

### 4.3 Exact semantic inventory and candidate-block construction

Each pair root owns disjoint semantic roles. Create nodes `s`, goals
`g00..g23`, wrong-AT nodes `x00..x23`, and the family hubs defined below. For
start and every expected unresolved continuation state `z`, and for every goal
`gj`, create exactly one route role `route/z/gjj`, one useful query role
`query/z/gjj`, one recovery query role `recover/z/gjj`, and their public
blocks. A directory at `z` consists of all 24 route roles. A surprise state
reached only through a contradicted EVENT has no INDEX registry and is served
only by the implicated EVENT's RECOVER query. A useful or recovery query block
contains exactly four candidate slots `c0..c3`.

Let `v(z,j) = (3*j + state_ordinal(z) + skin) mod 4`. In an ordinary or
goal-switch block, candidate `v` has `AT=z, FOR=gj`; `v+1 mod 4` has
`AT=z, FOR=g(j+1 mod 24)`; `v+2 mod 4` has
`AT=xj, FOR=gj`; and `v+3 mod 4` has
`AT=x(j+1 mod 24), FOR=g(j+2 mod 24)`. Thus exactly one row matches both.
`state_ordinal(s)=0`; private hubs use `j+1`; bucket hubs use `25+k`; held
hubs use the section-10 ordinal.

Each candidate owns one event, port, receipt, and RECOVER query. Ports are
unique within a pair root. The fixed world transition for a candidate whose
AT is `z` is `(z, DID) -> GOT`, except the one explicitly named erroneous
belief in a STEP-mismatch prefix. Candidate ports whose AT is a wrong-AT node
are legal only at that wrong-AT node. No other transition exists.

Before a deep-swap override, GOT is total and deterministic. From start, a
reached pair GOT the row's FOR goal and an unresolved pair GOT that family's
hub function for the FOR goal. From a family hub, GOT is the row's FOR goal.
From wrong-AT node `xj`, GOT is `x((j+3) mod 24)`. A non-implicated RECOVER
query is allocated but unregistered and returns MISS. Only the relevant
mistaken EVENT in a mismatch case has a registered RECOVER block. Deep-swap
members then freeze all GOT values and swap FOR only; the special target-block
GOT rules in sections 4.4--4.5 keep both possible relevant rows in the same
terminal class.

For a relation/deep-swap pair, define `u` as in section 4.1 and override the
selected useful/corrective block so member `m0` has its both-matching row at
`u` and its CURRENT-only row at `u+2 mod 4`. Member `m1` swaps only those two
FOR values. The other two candidates retain the GOAL-only/neither pattern.
All candidate IDs and every non-FOR field are byte-identical across members.

For a strict-MISS case, allocate `miss/pXX/mY` as the explicitly unused query;
it is absent from every ROUTE and service registry. For an irrelevant-return
case, the bad query is `query/z/g(j+1 mod 24)` while the task goal is `gj`;
its four rows are generated relative to `g(j+1)`, so zero rows match both task
GOAL and z. For a STEP-mismatch case, allocate one bad-event block with a
both-matching row whose GOT is a distinct predicted node and whose world port
instead reaches a distinct surprise node. Its RECOVER block is AT the surprise
node, FOR the task goal, and uses the same four-slot rule. The target-bearing
corrective block, not the already failed event, receives the deep swap when
the case is in a relation pair.

The selected scored goals are `g((5*b) mod 12)` for left and
`g(12 + ((7*b) mod 12))` for right. Relation-pair members use left when
`b mod 2 = 0` and right otherwise. All other goals are structural distractors.
Within a goal-switch or recovery-matched template, display order is derived
from the shared `display-order` role list and therefore does not depend on flow
or member. Deep-swap members retain it byte-for-byte.

### 4.4 Train topology family A: private spokes

Every case world has 24 semantic goals `g00..g23`, one start `s`, and a
24-row ROUTE directory at every state that can become CURRENT. Each ROUTE maps
one `(state, goal)` to one opaque four-EVENT relation query.

In family A, an unresolved correct or corrective EVENT from `s` reaches a
private hub `a_j` used only by goal `g_j`; a reached EVENT goes directly to
`g_j`. At every private hub, the valid relation for goal `g_k` goes directly
to `g_k`. Candidate events not selected as relevant use distinct legal ports
and destinations, and the family certificate proves every private hub has
selected-goal indegree one.

In every target-bearing block, both rows that can become relevant under a
deep swap share the terminal class: when reached, both GOT the task goal; when
unresolved, one GOT `a_j` and the other GOT `a_(j+1 mod 24)`. Non-target
blocks use `a_k` for their FOR goal k. This makes the STEP target change while
holding reached/unresolved fixed.

### 4.5 Train topology family B: bucket merges

Family B has the same public interface and counts. An unresolved correct or
corrective EVENT for goal `g_j` reaches shared hub `b_(j mod 6)`; a reached
EVENT goes directly to `g_j`. At each shared hub, the valid relation for
`g_k` goes directly to `g_k`. Candidate events use distinct legal ports and
destinations. Every shared hub has four selected-goal predecessors. Thus the
role topology differs from family A even after public IDs and row order are
removed.

The two potentially relevant rows in a target-bearing unresolved block GOT
`b_(j mod 6)` and `b_((j+1) mod 6)`; in a reached block both GOT the task
goal. Non-target blocks use `b_(k mod 6)` for their FOR goal k. The target
block's two ports remain distinct even when their reached GOT is equal.

For both families, the four rows of a useful relation block contain exactly
one row matching task GOAL and CURRENT, one matching CURRENT only, one matching
GOAL only, and one matching neither. The non-relevant FOR goals and AT states
are selected from the same 24-goal/state pools by the opaque permutation.
All four candidate rows in a deep-swap block have destinations in the same
terminal class, so swapping relevance changes STEP without changing
reached/unresolved status.

No train prefix opens a directory or EVENT block beyond the current decision.
The full registry may contain later relations, but it is evaluator/service
custody, not model text.

## 5. Four exact targets per case

### 5.1 Ordinary flow

Before SEEK, the coherent episode has executed `READ INDEX CURRENT` and
received the 24-row ROUTE directory. The four targets are:

1. **SEEK:** `READ RELATION q`, where the unique ROUTE row has both task GOAL
   and latest CURRENT.
2. **PROSPECT:** `STEP p`, where the unique EVENT row in the returned block has
   both task GOAL and latest CURRENT.
3. **STEP-CHECK/KEEP:** after WORLD CURRENT equals that EVENT's GOT,
   `THINK KEEP e` for that EVENT.
4. **CONTINUE/STOP:** after ACK, emit `STOP` when CURRENT equals GOAL;
   otherwise `READ INDEX CURRENT`.

The initial `READ INDEX CURRENT` is actor-issued in autonomous evaluation; it
is present as an executed, loss-masked bootstrap action in train SEEK units.
It is also learned directly as every unresolved CONTINUE target. The host never
forces it during evaluation.

### 5.2 Recovery flow and distinct CHECK schemas

The bad action is loss-masked input and never a target.

**READ-CHECK/MISS** in its ATOM-LOCAL form contains latest CURRENT and GOAL,
the issued bad `READ RELATION q_bad`, and literal `MISS`. Its target is
`THINK REVISE q_bad`. The local CHECK does not include a directory or
corrective query. CLOSED retains the authentic earlier 24-row directory,
after which the child guessed the unregistered bad query; that directory
contains the correct query as one of 24 public alternatives.

**READ-CHECK/irrelevant** in its ATOM-LOCAL form contains latest CURRENT and
GOAL, the issued bad query, and its exact four-EVENT return. Zero rows match
both GOAL and CURRENT; that local, protocol-defined predicate is the complete
irrelevance proof. Its target is `THINK REVISE q_bad`. The irrelevant return
does not name, return, or derive the corrective query. CLOSED again retains
the earlier directory with 24 alternatives.

**STEP-CHECK/mismatch** contains the selected EVENT, issued STEP, its GOT
prediction, and the public WORLD CURRENT, which differs from GOT. Its target
is `THINK REVISE e_bad`. The implicated EVENT's RECOVER field is an authentic
one-step contingency fact, not a command; no other recovery route is present.

After ACK, the remaining recovery targets are:

2. **SEEK:** for READ failures, select the proper relation query from the
   already observed 24-row directory; for a STEP mismatch, issue
   `READ RELATION` on the implicated EVENT's RECOVER query.
3. **PROSPECT:** STEP through the unique relevant EVENT in that exact return.
4. **CONTINUE/STOP:** compare the corrective WORLD CURRENT directly with GOAL;
   emit STOP if equal, else READ INDEX CURRENT.

The corrective STEP's outcome is public, but recovery cases do not insert an
authored or unsupervised KEEP line merely to make the history look symmetric.
The fourth target is locally sufficient from CURRENT and GOAL. This preserves
four targets rather than silently creating a fifth.

### 5.3 Exact totals

```text
READ   96 = 64 SEEK + 32 unresolved CONTINUE
STEP   64
THINK  64 = 32 KEEP + 32 REVISE
STOP   32
TOTAL 256
```

## 6. CLOSED and ATOM-LOCAL serialization

Create one immutable `TargetUnit` first. Both arm records reference the same
unit ID, exact assistant target bytes, target SHA-256, public identifier
assignment, command class, and candidate/answer index. One unit contains one
assistant target. All prior roles and bytes are loss-masked.

CLOSED is the authentic accumulated transcript ending immediately before that
decision. ATOM-LOCAL is a new chat containing the same system message and the
following exact role sequence. Here `S/U/A` means system/user/assistant, the
task is the exact section-2.3 task bytes, every READ/STEP/THINK is exact
section-2.4 actor bytes, and every service/world/ACK is the exact section-2.3
user message. There are no additional messages:

| target | ATOM-LOCAL role/content sequence after `S(system)` |
|---|---|
| ordinary SEEK or SEEK after READ failure | `U(task); A(READ INDEX CURRENT); U(SERVICE LF ROUTES-block)` |
| SEEK after STEP mismatch | `U(task); A(READ RELATION q_bad); U(SERVICE LF EVENTS-block); A(STEP p_bad); U(WORLD-block); A(THINK REVISE e_bad); U(ACK)` |
| PROSPECT | `U(task); A(READ RELATION q); U(SERVICE LF EVENTS-block)` |
| STEP-CHECK KEEP/REVISE | `U(task); A(READ RELATION q); U(SERVICE LF EVENTS-block); A(STEP p); U(WORLD-block)` |
| READ-CHECK MISS | `U(task); A(READ RELATION q_bad); U(SERVICE LF MISS)` |
| READ-CHECK irrelevant | `U(task); A(READ RELATION q_bad); U(SERVICE LF EVENTS-block)` |
| CONTINUE/STOP | `U(task re-rendered with START unchanged and CURRENT equal to latest public state)` |

ATOM-LOCAL contains no earlier episode turn beyond the table and every unit
resets. It is locally conditional, not causally unlinked.

### 6.1 What is exactly coupled

Exact equality is required for target bytes/tokens including target EOS,
target identifier multiset and tokenization, target-command counts, unit and
presentation order, batch slot, target tokens per batch, LoRA initialization
bytes, optimizer class/defaults, LR schedule, dropout probability, per-update
RNG start seed, update number, and decode order/seeds. No padding record counts
as a target.

Identifier-token marginals mean **target-side only**. CLOSED's additional
historical identifiers make whole-prefix equality impossible. Report, by arm,
prefix bytes, tokens, roles, identifier occurrences, padding tokens, total
sequence tokens/update, and their differences. Do not add inert facts to
ATOM-LOCAL to imitate CLOSED.

### 6.2 Honest RNG/dropout and optimizer semantics

`same dropout tape` now means the same declared probability and same numeric
RNG state at the start of each paired update, not identical elementwise masks.
Before paired update `u`, restore the CUDA and CPU generator state derived from
`low64(SHA256(master || NUL || "dropout" || NUL ||
uint32_big_endian(u)))`, interpreted unsigned big-endian, by calling
`torch.manual_seed` and `torch.cuda.manual_seed_all` immediately before the
forward in both arms. Save pre- and post-forward RNG-state hashes. Different
prefix shapes consume different random draws, so post-state and masks may
differ; report that fact and never call the masks identical.

Both arms begin from one byte-identical initialized adapter copied into two
lineages. They use separate AdamW states initialized identically. Their
moments properly diverge with gradients. “Same optimizer tape” means identical
optimizer implementation/defaults, step indices, batch-target tape, constant
LR, and no skipped/nonfinite step—not identical moment tensors.

D1 and D2 are one logical training stream per lineage. At D1 preserve adapter,
optimizer, data cursor, update number, and all CPU/CUDA RNG states. If D2 opens,
resume those exact states at update 257; a weight-only fresh-optimizer restart
is forbidden.

## 7. Exact presentation tape

The internal unit ID is exact ASCII `pXX/mY/uZ`, where `XX` is two decimal
digits, `Y` is `0` or `1`, and `Z` is chronological target slot `0..3`
(ordinary SEEK/PROSPECT/CHECK/CONTINUE and recovery
CHECK/SEEK/PROSPECT/CONTINUE). Order the 256 unit IDs once by ascending
`SHA256(master || NUL || "target-order" || NUL || unit_id)`, breaking the
cryptographically impossible digest tie by raw unit-ID bytes. For presentation
`r` in `0..7`, rotate that order left by
`(73*r) mod 256`; concatenate presentations in increasing `r`; group adjacent
units into batches of four. Both arms use the identical unit-ID/target tape.

D1 consumes rotations 0--3: 1,024 unit occurrences and 256 updates per arm.
D2, if opened, appends rotations 4--7: 2,048 cumulative unit occurrences and
512 cumulative updates per arm. Updates are numbered from 1; D2's first update
is 257. Every batch receipt records its four unit IDs,
target hashes, target token counts, arm prefix token counts, update number,
presentation indices, and RNG-start hash.

## 8. Forward-answer and route-leak scanner

### 8.1 Exact normalization

All material is already ASCII. For scanning only:

1. reject invalid UTF-8, non-ASCII, CR, NUL, or Unicode rather than repairing;
2. split on LF without dropping empty lines;
3. uppercase ASCII;
4. collapse each run of space or tab to one space;
5. create a compact companion form by removing `_`, `-`, space, `<`, and `>`.

Run literal-line, normalized-line, exact-identifier, and compact-identifier
scans. No case folding or normalization is applied to actor parsing.

### 8.2 Allowed causal occurrences versus leakage

The full next actor action may never occur in any prefix form outside the
fixed protocol grammar. The system's standalone literal `STOP` grammar line
is the sole exact-full-target exception and is recorded as protocol, never as
a scheduled answer. A concrete target action containing an ID has no such
exception. Its operand may occur only in the following typed public facts:

```text
SEEK operand       QUERY field of ROUTE rows already returned by the service
PROSPECT operand   DID field of EVENT rows already returned by the service
CHECK operand      issued query or selected EVENT already in the transcript
CONTINUE operand   latest public CURRENT
```

Those are the causal inputs being tested, not teacher answers. Every allowed
occurrence receives a field-path receipt. An occurrence in system prose,
authored child THINK, evaluator text, scheduled-action field, hidden route,
future service block, or unrelated task field is a hard failure.

For each unit, the forbidden ledger additionally contains all future ports,
queries, events, and non-task destination IDs not yet returned; every
registered route beyond the current one-step EVENT; evaluator labels; the
normalized/compact forms of the next full action; and declared semantic
aliases. START, GOAL, and the latest public CURRENT are explicit task-fact
exceptions, never scheduled-action exceptions. An authored child THINK may
name only the already implicated event/query and may never name a later query,
port, non-task destination, command, or route.

The ROUTES directory reveals 24 candidate queries but no candidate port,
destination, recovery query, or later route. An EVENTS block reveals only four
one-step candidates and their mismatch contingency. The next state's directory
does not enter text until the actor reaches and reads that state. Thus no
prefix contains a full scheduled route.

For STEP-mismatch recovery, RECOVER is allowed only in the implicated EVENT
already read; it is used only after an observed contradiction. For READ
failure, the irrelevant/MISS block contains no corrective query. CLOSED may
retain an earlier authentic directory that includes the correct query among 24
candidates; ATOM READ-CHECK omits it because it is unnecessary to judge the
failure. This is an explicit history-treatment residual, not hidden teacher
text.

## 9. Held intervention panels

Use domain `dose_intervention`, family C below, fresh IDs, and eight pairs per
transition. Each pair has one canonical semantic object, a named mutation,
and a JSON-pointer allowlist. The renderer hashes all fields outside that
allowlist and requires equality.

Number pairs `k0..k7` within transition number `t=0..3` in the order below.
Use skin `floor(k/4)`, world rotation `(5*k + 3*t + 1) mod 8`, left goal
`g((3*k+t) mod 12)`, right goal `g(12+((5*k+t) mod 12))`, ROUTE target
positions `(3*k+t) mod 24` and `(3*k+t+12) mod 24`, and EVENT candidate
positions `k mod 4` and `(k+2) mod 4`. Fill every non-designated row with
section 4.3 and the fixed opaque/display permutations. These formulas, rather
than a search for passing null scores, create the panel.

1. **SEEK/goal:** same task except GOAL, same CURRENT, identical 24-row ROUTES
   bytes and entire store. The two goals select different QUERY operands.
   Allowed rendered diffs: task `/GOAL`, target bytes/hash, evaluator answer.
2. **PROSPECT/relation:** same task, request, four EVENT/port/destination/
   recovery/receipt IDs and display order. Swap only the FOR values of two
   EVENT rows that both have AT equal to CURRENT; before the swap one has FOR
   equal to GOAL and the other a decoy goal. The unique relevant row and STEP
   change. Allowed diffs: those two `/EVENTS/*/FOR` fields, target bytes/hash,
   evaluator answer.
3. **CHECK/outcome:** same task, implicated EVENT, STEP, GOT, and pre-outcome
   transcript. Change WORLD CURRENT between GOT and a fixed alternate legal
   node. KEEP changes to REVISE on the same event ID. Allowed diffs: WORLD
   `/CURRENT`, target command/hash, evaluator answer.
4. **CONTINUE/STOP:** use a locally sufficient fresh task with identical
   START, CURRENT, store, and no prior route text. Change GOAL between CURRENT
   and a different goal. STOP changes to `READ INDEX CURRENT`. Allowed diffs:
   task `/GOAL`, target bytes/hash, evaluator answer.

No “entailed bytes” wildcard exists beyond those lists. Exact command,
operand, typed validity, member correctness, and pair-both correctness are
separate fields. The scripted oracle must score all 64 members and 32 pairs.

## 10. Held autonomous family C and exact strata

Family C is a held two-step crossing weave and never appears in birth train.
Every world has 24 goals, one start, eight predicted hubs `h0..h7`, and eight
disjoint surprise hubs `w0..w7`. For goal index `j` and world rotation `r`:

```text
predicted first hub = h_((5*j + r) mod 8)
surprise first hub  = w_((7*j + r) mod 8)
```

Family C uses the same 24-row directories and four-candidate EVENT blocks as
section 4.3. Its state ordinals are start `0`, predicted hub `100+k`, surprise
hub `108+k`, and wrong-AT node `200+j`. Non-relevant rows use the same
CURRENT-only/GOAL-only/neither construction. At a predicted hub the relevant
second-hop EVENT GOT its FOR goal. No INDEX request is registered at a surprise
hub, so `READ INDEX surprise` returns MISS; only the registered RECOVER query
from the contradicted first EVENT has a relevant EVENT from that surprise hub
to that goal.

An expected task's first relevant EVENT GOT and world transition both reach
the predicted hub. A mismatch task's EVENT GOT names the predicted hub while
its legal port actually reaches the surprise hub; that EVENT's RECOVER query
returns a block with one relevant EVENT from the surprise hub to the goal. In
expected tasks, the predicted hub's INDEX and selected relation lead to the
goal. Thus every task takes exactly two legal STEPs.

There are 16 causal-twin worlds `h00..h15`, two scored goals per world, and 32
tasks. Let `h` be the world index:

```text
goal left index        (5*h) mod 12
goal right index       12 + ((7*h) mod 12)
outcome mismatch       floor(h / 4) mod 2
skin                   floor(h / 8)
world rotation r       (3*h + 1) mod 8
```

The twins share exact world/store/IDs/display order and differ only in task
GOAL and its logically selected route. The four predeclared eight-task strata
are `(expected, skin0)`, `(mismatch, skin0)`, `(expected, skin1)`, and
`(mismatch, skin1)`. Each contains four worlds and both goal sides.

Within each four-world stratum, the correct initial query display positions
for left/right members are respectively `[0,6,12,18]` and `[3,9,15,21]`.
The relevant EVENT row position is `(h + member) mod 4`. Second-hop directory
positions are `(initial_position + 12) mod 24`. Opaque lexical positions are
separately audited, not acceptance-tuned.

The held absent tuple is exactly:

```text
(family=C_crossing_weave, actual_route_depth=2,
 goal_switch_pair=true, first_outcome=mismatch, skin=1)
```

It supplies eight tasks and is absent from train because family C is absent.

The registered candidate-address set is the 24 distinct relation queries in
the first ROUTES return; recursively reachable later/RECOVER queries are
additional, never substitutes. The minimal sufficient READ set is:

```text
expected: READ INDEX start, selected READ RELATION,
          READ INDEX predicted-hub, selected READ RELATION             = 4
mismatch: READ INDEX start, selected READ RELATION,
          selected READ RELATION RECOVER                               = 3
```

The evaluator derives these sets from public rows and public outcomes but does
not expose them. The actor chooses every action; there is no forced first READ,
candidate ranking, host path, repair, or carried conversation. Successful
rollouts may contain at most one pre-first-STEP READ outside the sufficient
set. The first STEP is deliberately unresolved, so its outcome must receive
exactly one correct KEEP or REVISE. The second STEP reaches GOAL and is followed
directly by STOP; no redundant terminal KEEP is required. Score READ classes,
first STEP, full route, first-outcome CHECK command/operand, strict typing,
goal arrival, exact STOP, and whole-chain success separately.

Limits remain `8 THINK / 12 READ / 8 STEP / 1 STOP / 4,096 generated actor
tokens`, at most 29 calls.

## 11. Exact null contract

### 11.1 Nine total one-turn surface nulls

For a panel member, construct public candidates without the answer:

```text
SEEK       all 24 READ RELATION actions in ROUTE display order
PROSPECT   all 4 STEP actions in EVENT display order
CHECK      KEEP and REVISE on the already implicated public ID
CONTINUE   STOP and READ INDEX latest-CURRENT
```

Append the phase-appropriate reserved all-A syntactically valid sentinel.
The exact sentinels are `READ RELATION M2AQ_AAAAAAAAAAAA` for SEEK,
`STEP M2AP_AAAAAAAAAAAA` for PROSPECT,
`THINK KEEP M2AE_AAAAAAAAAAAA` for CHECK, and
`READ INDEX M2AN_AAAAAAAAAAAA` for CONTINUE/STOP. They full-match the actor
grammar but are deliberately absent from every registry/world and cannot be
correct. Do not append a second sentinel.
Each null returns a total ranking over that list:

```text
N0 sentinel_first       sentinel, then display order
N1 display_first        display order, then sentinel
N2 display_last         reverse display order, then sentinel
N3 lexical_first        ascending raw action bytes
N4 lexical_last         descending raw action bytes
N5 shortest_first       ascending (byte_length, raw action bytes)
N6 goal_digest          ascending SHA256(GOAL_bytes || NUL || action_bytes)
N7 current_digest       ascending SHA256(CURRENT_bytes || NUL || action_bytes)
N8 character_columns    ascending (operand_byte[0], operand_byte[5],
                                  operand_byte[-1], raw action bytes)
```

For N8, STOP has the empty operand and every missing indexed byte is integer
zero; nonempty operands use raw ASCII bytes. All SHA-256 digests compare as
unsigned 32-byte big-endian strings.

For a singleton, emit its rank-zero action. For every unordered pair `(Na,Nb)`
with `a < b`, rank each candidate by:

```text
(rank_Na + rank_Nb,
 max(rank_Na, rank_Nb),
 SHA256("NPAIR" || NUL || name_Na || NUL || name_Nb || NUL || action_bytes))
```

and emit the minimum. This defines all 36 pairs, is order-independent, and has
an exact tie rule. Null code may parse only the public panel bytes used above;
it may not import an oracle, evaluator answer, semantic role, mutation label,
or hidden registry.

Every singleton and pair must execute on every intervention member and achieve
pair-both-correct `<=4/8` separately for SEEK, PROSPECT, CHECK, and
CONTINUE/STOP. A failure invalidates v2. Do not reseed or reorder until it
passes.

The old `direct_goal` rule is not a null here: matching ROUTE FOR/AT is the
intended SEEK relation. Likewise matching EVENT FOR/AT is the intended
PROSPECT relation. The interventions, not a mislabeled intended policy, test
whether those fields control output.

### 11.2 Autonomous schedules, separate from one-turn nulls

Execute these six complete actors on all 32 held chains:

1. `S_DISPLAY0`: INDEX latest CURRENT when no directory is present; choose
   ROUTE row 0, EVENT row 0, always KEEP, and STOP after two STEPs.
2. `S_LEXICAL`: same state machine, choosing lexicographically smallest QUERY
   and port and always KEEP; STOP after two STEPs.
3. `S_POSITION`: choose row `SHA256(GOAL)[0] mod n` at each choice, always KEEP,
   and STOP after two STEPs.
4. `S_READ_ALL12`: after INDEX, READ candidate relations in display order
   until a row matching public GOAL/CURRENT is observed or the READ cap is
   reached; use that row's STEP, perform the true public match/mismatch CHECK,
   use RECOVER after mismatch, and otherwise repeat from the new CURRENT.
5. `S_STOP1`: use display-row 0 choices, always KEEP, STOP after one STEP.
6. `S_STOP2`: use display-row 0 choices, always KEEP, STOP after two STEPs.

All malformed/no-candidate/cap states terminate; no policy receives a hidden
route. `S_READ_ALL12` spends one READ on INDEX, so it can inspect at most 11 of
24 initial relation candidates. Every schedule must score whole-chain
`<=16/32` and causal-twin-pair-both `<=8/16`. Save full traces. These schedules
are not included in the 36 one-turn pair combinations.

## 12. Topology core, signatures, surfaces, and scanner gates

Build the role graph with typed vertices STATE, GOAL, QUERY, EVENT, PORT, and
RECEIPT and labelled directed edges:

```text
(STATE,GOAL)-INDEXES->QUERY
QUERY-CONTAINS->EVENT
EVENT-FOR->GOAL
EVENT-AT->STATE
EVENT-DID->PORT
EVENT-GOT->STATE
EVENT-RECOVER->QUERY
(STATE,PORT)-WORLD->STATE
```

The decision core is canonical JSON containing phase, flow/recovery subtype,
family motif, terminal class, actual route depth, goal side, skin, relevant
candidate display position, predicted/actual match bit, typed vertex counts,
and the public-input induced subgraph with concrete IDs replaced by typed
roles. It excludes domain/case names and target bytes.

Root the graph at the first irreversible EVENT/PORT pair. For radii 0, 1, 2,
and 3, take the undirected-radius induced vertices while retaining directed
edge labels and distinguished CURRENT/GOAL/root roles. Canonicalize by the
lexicographically least adjacency serialization across permutations within
equal typed roles. The rooted signature is the ordered four-hash vector, not
an individual radius hash. Require zero equality of the full decision-core
hash or full four-hash vector between birth train and dose-DEV. Radius-zero
components may match because generic action semantics intentionally match.

For every train and dose decision, table normalized action index and command
against family, flow, recovery subtype, terminal class, goal side, skin,
actual depth, candidate display position, identifier byte length, all 12
identifier character columns, and later exact tokenizer length. Emit all
predeclared pairwise feature tables and Bayes-best collision accuracy. These
are diagnostics; the causal interventions and executed null caps are the
decisive shortcut gates.

## 13. Sixteen exact generic canaries

Canaries use the same system and actor parser, a disjoint `generic_canary` ID
pool, and user bytes:

```text
CANARY
COPY EXACTLY
{action}
```

There is no final LF. IDs are allocated by section 3. The ordered targets are:

```text
c00-c01  READ INDEX <node>
c02-c03  READ RELATION <query>
c04-c07  STEP <port>
c08-c09  THINK KEEP <event>
c10-c11  THINK REVISE <event>
c12-c15  STOP
```

Each non-STOP target uses a fresh canary identifier. This is explicitly a
copy/strict-interface retention panel, not composition evidence. Exact action
and strict parser validity are the same score. BASE and both fitted arms use
the same order and decode seed per canary.

## 14. Custody and independent checker

Before validating an actor response, append an immutable attempt containing
call index, exact raw bytes or typed non-string encoding, generation request,
declared/actual token counts, truncation/finish reason, pre-state, parser
disposition, operation/operand if parsed, response bytes, post-state, accepted
flag, and terminal reason. Keep accepted service/world receipts separately.
Invalid attempts remain failures and remain auditable.

The canonical material manifest contains complete task/store/world objects,
all target units and paired render hashes, ID-pool/permutation receipts,
factor/matching tables, intervention allowed-diff receipts, oracle and null
traces, core/signature/surface tables, scanner ledgers, presentation tape,
cost calculation, source/spec/config hashes, and artifact lineage. No summary
hash substitutes for objects.

An independent checker consumes canonical JSON only and must not import the
generator, renderer, service, oracle, scorer, decision-core helper, or null
implementation. It independently reconstructs service returns, legal world
transitions, relevant rows, expected targets, route witnesses, factor counts,
core/signatures, scans, null rankings/pairs/schedules, and costs. Mutation
tests flip one byte in every artifact class and require rejection.

## 15. Source/CPU gate before any materialization

Source authoring should create a separate Stage-2A module and checker; preserve
the current tiny fixture and `NO_GO_PARTIAL_SOURCE_ONLY` tests unchanged. The
exact planned paths are `organism_v6/composition_birth_stage2a.py`,
`organism_v6/composition_birth_stage2a_checker.py`,
`tests/test_composition_birth_stage2a.py`, and
`tests/test_composition_birth_stage2a_checker.py`. The in-memory CPU gate is:

1. exact deterministic regeneration and 64/256/factor/subtype/matching counts;
2. opaque pool/permutation and namespace-certificate checks;
3. exact target, batch, presentation, initialization-spec, and RNG-start
   coupling plus honest prefix residuals;
4. CLOSED coherence and every ATOM-LOCAL schema above;
5. literal/normalized/compact forward-answer scans and adversarial injections;
6. strict actor/service/world parsing, fuzzing, budgets, and lossless custody;
7. 64/64 intervention oracle, 32/32 chain oracle, exact STOP, witness bounds,
   and READ-class reconciliation;
8. all nine one-turn nulls, all 36 order-independent pairs, and all six
   autonomous schedules executed under their caps;
9. exact topology cores/four-radius vectors, held tuple, surface tables, and
   zero forbidden equality;
10. 16 exact canaries and scorer;
11. D1/D2 state-machine tests for every branch and preserved D1 custody;
12. independent checker agreement plus one-byte mutation rejection; and
13. programmatic cost closure.

Use a fake tokenizer only to exercise interface types; label all such counts
synthetic. Passing CPU tests does not authorize or constitute a scientific
root. A fresh independent source audit must bind the exact source/test/spec
hashes before materialization can be requested.

## 16. Later execution pins

The later preparation contract is frozen now, but values produced by source
or tokenizer execution cannot be fabricated in this document.

- Base and tokenizer repository:
  `Qwen/Qwen2.5-7B-Instruct`.
- Immutable revision:
  `a09a35458c702b33eeacc393d103063234e8bc28`.
- A pre-existing authenticated receipt must list SHA-256 for every loaded
  config, tokenizer, template, and weight/shard file. Local path strings are
  not identity. Missing authentication fails closed.
- Runtime versions: torch `2.13.0+cu130`, transformers `5.5.3`, PEFT `0.20.0`,
  vLLM `0.27.1`; CUDA/driver/GPU UUID and source wheel hashes are captured.
- Chat serialization uses the pinned tokenizer's exact chat template with the
  section-2 role messages. Loss is only on target assistant content plus its
  EOS; system/user/earlier assistant bytes and role headers are `-100`.
  Preparation records context/target boundary IDs and round-trip bytes for all
  512 paired train records.
- Training: all-layer LoRA over `q_proj,k_proj,v_proj,o_proj,gate_proj,up_proj,
  down_proj`; rank 8, alpha 16, dropout .05, bf16; batch 4, gradient
  accumulation 1; no example packing, truncation, splitting, skipped batch,
  scheduler, warmup, gradient scaler, or gradient clipping. LoRA bias is none,
  task type is causal LM, gradient checkpointing is enabled, padding is right
  padding with the pinned tokenizer's declared pad ID, and maximum model/
  training context is 16,384 tokens. Any sequence that does not fit is a
  preparation failure.
- Optimizer: `torch.optim.AdamW`, LR `3e-5`, betas `(0.9,0.999)`, eps `1e-8`,
  weight decay `.01`, amsgrad false, maximize false, capturable false, and no
  differentiable mode; `foreach=false` and `fused=false`. LR is constant.
- Adapter initialization uses
  `low64(SHA256(master || NUL || "adapter-init"))` as the CPU/CUDA torch seed,
  PEFT's pinned default Kaiming-A/zero-B initialization, and one saved initial
  adapter copied byte-for-byte to both arms. Preparation rejects any initial
  parameter hash difference.
- A D1 checkpoint includes adapter, optimizer, cursor, update number, and exact
  CPU/CUDA RNG states. D2 restores all of them. Existing weight-only
  fresh-optimizer continuation paths are ineligible.
- Real preparation must prove every rendered train sequence fits the pinned
  context with zero truncation and must record tokens/update by arm. Source
  code must not guess a padding equivalence.
- Readout uses greedy decoding: temperature `0`, top-p `1`, top-k disabled,
  repetition penalty `1`, no stop string, one sequence. Max generated tokens
  are 4,096 per autonomous task aggregate and 256 per intervention/canary
  call. Each autonomous call requests
  `min(256, 4096-cumulative_generated, 16384-context_tokens)`; a zero allowance
  or length finish terminates. Per-call seeds are
  `low64(SHA256(master || NUL || "decode" || NUL || panel || NUL ||
  uint32_big_endian(call_index)))`; identical calls across states reuse the
  seed even though greedy decoding should not consume it.
- BASE/CLOSED/ATOM use identical task and call order. No retries, repairs,
  best-of, output trimming, or BASE rerun at D2.

The tokenizer preparation must report target token counts per batch,
identifier tokenization, padding and total sequence-token residuals before a
fit. Any mismatch invalidates preparation.

## 17. D1/D2 gates and branch

V1 gates remain exact. Per fitted arm, acquisition requires pair-both-correct
`>=6/8` separately for SEEK, PROSPECT, CHECK, and CONTINUE/STOP; strict typed
`>=60/64`; canaries `>=15/16`; fitted-arm canary gap `<=1/16`; and every
source/custody/coupling/scan/loss/parser receipt green.

An acquired arm qualifies on 32 autonomous tasks only with all:

```text
whole chains                              >=26/32
arm - BASE                                >= 8/32
causal twin pairs both correct            >=12/16
useful READ before first STEP             >=28/32
strict typed validity                     >=30/32
each exact eight-task stratum             >= 6/8
each autonomous null schedule             <=16/32
off-witness pre-first-STEP READs/success   <=1
verified goal arrival then exact STOP      required
```

D2 opens only under v1's finite-loss, valid-custody/coupling, canary, and
underfit/no-chain conditions. Continue both fitted lineages from exact D1
states. D2 is terminal. Both arms must acquire for a curriculum contrast or
advancement. If ATOM-LOCAL qualifies, select it. Select CLOSED only if CLOSED
qualifies and acquired ATOM-LOCAL fails chains; mention coherent-history
benefit only at CLOSED minus ATOM-LOCAL `>=8/32`. Otherwise stop as bound.

## 18. Cost closure

The exact cap is unchanged:

| Stage-2A work | D1 | D2 addition | terminal |
|---|---:|---:|---:|
| fit invocations | 2 | 2 continuations | 4 |
| optimizer updates across arms | 512 | 512 | 1,024 |
| autonomous rollouts | 96 | 64 | 160 |
| autonomous actor-call cap | 2,784 | 1,856 | 4,640 |
| intervention calls | 192 | 128 | 320 |
| canary calls | 48 | 32 | 80 |
| all model calls | 3,024 | 2,016 | 5,040 |
| generated-token cap | 454,656 | 303,104 | 757,760 |
| reader-model calls | 0 | 0 | 0 |

Training token work and GPU-hours remain unbound until real tokenization.
Record sequence tokens/update, seconds/update, actual actor tokens, engine
load, and peak GPU memory.

## 19. Goal/route leakage reconciliation

This design intentionally places the immediate operand in a causal public
fact: QUERY among 24 ROUTE candidates, DID among four EVENT candidates,
implicated ID in the executed transcript, or latest CURRENT. Removing those
facts would destroy the transition being tested. The operand is never rendered
as its complete next action, never placed in an authored child hint, and never
selected by the host.

The goal does not encode or equal a query. It is an independently permuted
node token. The directory maps 24 opaque goals to 24 opaque queries, and the
actor must select the matching relation. The directory contains no ports or
destinations. The relation block contains one-step candidates only. A later
directory is unavailable until the actor changes CURRENT and asks for it.
RECOVER is a contingent one-step address usable only after a public mismatch.
Therefore neither GOAL bytes nor any one service return exposes a full route.

The system prompt states stable row semantics but no case-specific choice. A
high BASE score is possible; that is measured rather than hidden. The required
arm-minus-BASE margin prevents a birth claim without headroom.

## 20. Self-audit

### Preserved exactly

- 64 cases, 32 causal pairs, four targets/case, and 256 unique targets;
- command totals READ 96 / STEP 64 / THINK 64 / STOP 32;
- CLOSED versus ATOM-LOCAL and BASE;
- D1 four presentations and D2 eight cumulative presentations;
- intervention counts, autonomous counts, thresholds, selection branch, and
  terminal cost caps;
- response-only loss, all-layer rank-8 recipe, exact-text service, autonomous
  actor, strict failure, claim boundary, and later-stage stop.

### Closed contradictions

- READ-CHECK and STEP-CHECK now have distinct complete local schemas.
- Irrelevance is zero matching `(FOR,AT)` rows and needs no corrective query.
- Nine one-turn nulls and 36 pairs are total; autonomous schedules are
  separately total and scored.
- Family A/B/C, the held tuple, four strata, pair allocation, recovery table,
  and recovery matching are exact.
- Coupling is target-side; prefix residuals and shape-dependent dropout masks
  are explicit.
- Impossible unknown-text comparison is replaced by a literal allowlist,
  disjoint concrete M2A pools, and public namespace/spec certificates.
- System/task/host/parser/service bytes, canaries, core/signature algorithm,
  normalization, and intervention diff paths are frozen.
- Base, revision, training optimizer, continuation custody, and decode config
  are predeclared while real file/token hashes remain a later fail-closed
  receipt.

### Remaining prospective risks, not specification gaps

1. The frozen null root may fail one of its caps because opaque lexical hashes
   are not acceptance-tuned. Correct response: v2 NO-GO and a newly reviewed
   spec, never reseeding.
2. The system semantics may let BASE solve the chains. Correct response: the
   arm-minus-BASE gate fails; do not weaken the prompt after seeing BASE.
3. The 24-row/4-EVENT prefixes may tokenize longer than expected. Correct
   response: preparation NO-GO on any truncation, not a larger context chosen
   after outcomes.
4. The synthetic FOR/AT join is narrow. A pass supports only the stated
   exact-text controller, not general planning.
5. The one-turn nulls are not exhaustive. The held single-variable pairs are
   the decisive causal defense and autonomous chains remain required.

### Arithmetic self-check

An independent local Python enumeration of the formulas in sections 4, 7,
10, and 18 returned:

```text
SELF_AUDIT_PASS rows=64 factors=32/32 recovery=16/8/8
positions_under_readall=4/8 costs=3024+2016
tokens=454656+303104
```

The factor formula yields 32/32 for every required binary train factor. The
fixed recovery table yields 16 mismatch, 8 MISS, and 8 irrelevant cases, with
each subtype balanced on family, terminal, goal side, and skin. D1 is
`2 * 256 = 512` updates; D2 adds the same. Readout arithmetic is
`96*29 + 192 + 48 = 3,024` calls at D1 and
`64*29 + 128 + 32 = 2,016` additional calls at D2. Token caps are
`96*4096 + 240*256 = 454,656` and
`64*4096 + 160*256 = 303,104`.

## Final ruling

**GO for Stage-2A source and in-memory CPU-test authoring after root adoption
of this exact memo hash.** The A--G design gaps are closed sufficiently for
Astra to implement without choosing scientific semantics in code. Preserve
the tiny fixture separately. Scientific materialization, the real tokenizer,
model calls, fitting, GPUs, and claims remain closed pending the complete CPU
gate, fresh independent source audit, authenticated execution pins, and a
separate recorded opening.
