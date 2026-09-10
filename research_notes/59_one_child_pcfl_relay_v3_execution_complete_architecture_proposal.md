# 59 — One-child PCFL relay v3: execution-complete architecture proposal

Date: 2026-09-07

Status: **unbound proposal only**. This file resolves the architectural choices
left open in note 58. It authorizes no change to a frozen one-parent packet, no
implementation, source edit, target or root generation, tokenizer/model call,
benchmark operation, adapter build, pilot, external access, GPU use, execution,
paper claim, or scientific promotion. The word *complete* means that the
proposal leaves no B1--B10 design choice to an implementer; it does not mean
that any governance or execution gate has passed.

This proposal is a separate optional E2/E4/E5 assay. It is not a v3 amendment
to the parenting protocol, is not on the parenting critical path, cannot delay
or rescue the parenting headline, and never changes the upstream child,
selection function, active-text contract, root packet, statistics, or claim.

## Verdict and invariant scope

**PASS as an execution-complete architecture candidate; NOT AUTHORIZED for
ratification or execution.** All ten architectural blockers B1--B10 from the
final v2 attack receive one choice below. The remaining gates are procedural
and evidentiary: the durable deliberation, exact human ratification, scoped
implementation, CPU/static conformance, actual prospective lock receipts,
fresh independent review plus author-side advocate, a resource gate, and a
separate pre-GPU/run authorization.

The causal unit is exactly one selected terminal child after its one parent and
all nursery artifacts have been deleted. A root is an isolated environment
trial of a byte-identical clone of that child. Arm forks are potential-outcome
clones, not children or learners. There is no classroom, peer, cohort,
population of children, shared memory, cross-root update, ensemble, or
cross-root communication. `WRONG_LIFE` is a carrier made from a disjoint
environment root of the same fixed child and is capability-inaccessible to the
assayed root except through its assigned frozen reader.

All inference is conditional on this child and the registered PCFL root
distribution. Compression, total-state efficiency, parenting causality,
domain-general creativity, autonomous theory invention, and superiority over
the upstream `ACTIVE_TEXT_FIXED` system are outside scope.

## 1. B1 — locks, pilot, and receipts

### 1.1 Single chronology

The only confirmatory chronology is:

```text
P0  upstream parenting protocol and child-selection function sealed
R0  these v3 bytes, relay manifests, statistics/power law, and master seeds sealed
PU  upstream parenting outcomes unblinded
CS  the selected terminal child and parent/nursery deletion receipt sealed
DV0 disjoint DEV and POWER_PILOT identities sealed without child observations
DV1 optional authorized DEV/POWER_PILOT completed; blinded reducer sealed
N0  fixed N-grid rule returns one final N in [96..512] or STOP; N ratified
A0  confirmation roots/twins/opportunity tapes/RNG commitments sealed
A1  Phase-A public ledger sealed and both compilers completed
B0  write-denied B forks cloned, executed, sealed, and destroyed
C0  exact common pre-C snapshot sealed
C2  authentic signal read, declaration, and selected experiment dispatch sealed
C3  AUTH public outcome and canonical new row sealed
D0  D arms built from the common clean base and declared decks
D1  one fresh D goal revealed; all terminal outcomes sealed
```

`P0`, `R0`, and `PU` each require an external immutable receipt containing the
event name, UTC timestamp, monotone governance sequence number, artifact
manifest root, signer identity, signature, and predecessor-receipt SHA-256.
The confirmatory label is legal only when signature verification and the
predecessor chain prove `P0 < R0 < PU`. Missing, incomparable, backfilled, or
post-`PU` relay receipts make the entire relay exploratory forever; neither
`CS`, `DV0`, nor `A0` repairs that fact.

At `R0`, freeze exact bytes or SHA-256s for: this proposal; root generator;
typed interfaces; schemas; compiler and scorer tables; all potential outcomes;
failure values; control registry; finite-controller enumerator; carrier
serializer and builder; model/tokenizer/chat template; optimizer; DEV/pilot
algorithm; allowed pilot fields; fixed N-grid selection rule; analysis program;
resource ceilings; root-distribution version; master RNG commitment; and the
full ordered confirmation decision registry in Section 11.

At `A0`, the final-N confirmation roots are iid draws with replacement from
the frozen root-generator seed distribution, excluding all DEV/pilot IDs by
the presealed hash predicate. A seed collision is a global pre-exposure stop,
not redraw permission. Instantiation cannot inspect child behavior, proposals,
admissions, carrier output, feasibility, or score. Every root remains
intention-to-treat and is never regenerated, replaced, or restratified.

### 1.2 Pilot firewall and prospective sample-size rule

There are 8 generator DEV roots and 32 `POWER_PILOT` roots, all disjoint from
confirmation and permanently excluded from inference. Neither set may change a
schema, endpoint, score, floor, ceiling, SESOI, failure value, control,
intervention, multiplicity rule, planning alternative, or root eligibility.

The pilot reducer receives the already registered, failure-filled root vector
but releases only:

- the fixed count and pre-exposure administrative failures;
- anonymized adverse-to-favorable within-endpoint ranks with the exact
  hash-derived row/tie ordering in the incorporated statistics lock;
- the endpoint-by-endpoint Spearman rank-correlation matrix; and
- build/read time, token, byte, and memory quantiles to a separate resource
  principal that cannot pass them to the sample-size reducer.

It releases no root ID, mean, median, sign, arm rate, discordance direction,
chain rate, success count, p-value, favorable subset, trace, carrier output, or
semantic content. The exact `R0` mapping evaluates:

```text
N_GRID = [96,128,160,192,256,320,384,512]
FINAL_N = smallest N passing the exact marginal union-bound power rule,
          the chain-power rules, and the mandatory rank-copula simulation
          in the incorporated statistics lock
if no member passes or the independent resource ceiling is lower: STOP
```

This is the only blinded upward extension, and it occurs before confirmation
root generation and `A0`. The selected final N, power stdout, reducer/code
hashes, and allowed pilot-output receipt require exact human ratification at
`N0`. There is no confirmation-stage extension, internal-pilot re-estimation,
early success/futility stop, root replacement, or promising-zone rule. This
removes the v2 collision: every endpoint, alternative, confidence rule, grid,
and mapping is fixed at `R0`; later pilot ranks can choose only the predeclared
N or STOP.

## 2. B2 — one byte grammar and total compilers

### 2.1 Canonical bytes

Every relay object is strict UTF-8 canonical JSON. Before validation, strings
are Unicode NFKC normalized. Stored objects use keys sorted lexicographically
by Unicode code point, compact `,` and `:` separators, `ensure_ascii=false`, no
NaN/Infinity, and integers only. JSONL adds exactly one U+000A after every
object. Parsers reject duplicate keys, unknown fields, missing fields, booleans
as integers, invalid UTF-8, non-NFKC strings, duplicate array elements, and
trailing bytes. Arrays retain declared order except the explicitly sorted ID
arrays below. IDs match `^[a-z][a-z0-9_]{0,63}$`; hashes are 64 lowercase hex
characters. Every field shown is required.

`A_LEDGER_V3` is a single append-only JSONL byte string. Its `ordinal` values
start at zero and increase by exactly one across all three record types:

```text
PUBLIC_EVENT := {
  "action_args": CANONICAL_JSON_OBJECT,
  "action_family": ID,
  "action_id": ID,
  "actor_response_sha256": SHA256,
  "event_id": ID,
  "kind": "PUBLIC_EVENT",
  "ordinal": INTEGER,
  "outcome_symbol": ID,
  "public_state_after_sha256": SHA256,
  "public_state_before_sha256": SHA256,
  "root_public_id": ID,
  "schema_version": 3
}

ATOM_PROPOSE := {
  "action_id": ID,
  "atom_slot_id": ID,
  "endpoint_1": ID,
  "endpoint_2": ID,
  "kind": "ATOM_PROPOSE",
  "ordinal": INTEGER,
  "prediction": ID,
  "prior_event_citations": [ID, ...],
  "proposal_id": ID,
  "schema": ID,
  "schema_version": 3,
  "support_event_id": ID,
  "value_domain": [ID, ID]
}

COUSE_PROPOSE := {
  "atom_ids": [ID, ID],
  "citations": [ID, ...],
  "intended_operation": ID,
  "kind": "COUSE_PROPOSE",
  "link_slot_id": ID,
  "ordinal": INTEGER,
  "proposal_id": ID,
  "schema_version": 3,
  "support_action_id": ID,
  "support_event_id": ID
}
```

`value_domain`, `atom_ids`, and citation arrays are lexicographically sorted;
the two values/IDs must differ. Endpoints are ordered by the registered schema,
not sorted. `prior_event_citations` and `citations` may be empty and have at
most eight IDs. A proposal is emitted before its named action and event; event
IDs and action IDs are opportunity-tape public handles committed at `A0`, so a
future support handle is not a post-outcome citation.

The only carrier rows are:

```text
ATOM_ROW := {
  "endpoint_1": ID,
  "endpoint_2": ID,
  "row_id": ID,
  "row_kind": "ATOM",
  "schema": ID,
  "value": ID
}

USE_LINK_ROW := {
  "atom_ids": [ID, ID],
  "row_id": ID,
  "row_kind": "USE_LINK"
}
```

The ID is `a_` or `l_` plus the first 16 hex characters of SHA-256 over the
canonical object with `row_id=null`. Carrier rows contain no proposal prose,
prediction, `intended_operation`, citations, event/action/proposal/slot IDs,
public-state hashes, chronology, joint-event layout, success magnitude, goal,
target, path order, answer, or policy continuation. Only the canonical fields
above cross into a carrier.

### 2.2 `G_atom_v3`

The exact inputs are `(A_LEDGER_V3, OPPORTUNITY_MANIFEST,
ACTION_SCHEMA_TABLE, OUTCOME_MAP_TABLE)`. All four hashes are in the `R0/A0`
chain. For every `ATOM_PROPOSE`, in ordinal order:

1. resolve its slot, action, and support event uniquely in the opportunity
   manifest; require proposal ordinal `<` event ordinal and every prior citation
   to resolve to a `PUBLIC_EVENT` with lower ordinal;
2. require the support event's action ID to equal the proposal action ID and
   require its before-state hash, family, and canonical args to pass the slot's
   public legality predicate;
3. require the sorted two-value domain to equal the schema table domain and
   require `prediction` to be a member;
4. map `(schema, action_family, canonical action_args, outcome_symbol)` through
   the total `OUTCOME_MAP_TABLE`; `UNMAPPED` is failure, and the mapped value
   must equal `prediction`; and
5. construct the exact row above.

Hidden world truth is not an input to admission. After candidate construction,
an offline capability-isolated support audit compares the row to hidden truth
and emits only `TRUE` or `FALSE` to the root scorer; `FALSE` changes the result
to `TRUTH_MISMATCH` and cannot return to the child, compiler, writer, reader, or
actor.

Within an atom slot, zero valid candidate rows is `NO_ADMISSION`; one distinct
row admits the earliest-byte-identical proposal and labels later identical
ones `DUPLICATE_NO_ADMISSION`; two or more distinct valid rows label every
proposal in the slot `CONFLICT_NO_ADMISSION`. An ID collision with nonidentical
bytes is `ID_COLLISION`. The compiler returns one status for every proposal and
slot, never repairs, paraphrases, searches, or calls a model.

After each public event, the same compiler may evaluate only the immutable
ledger prefix and return the child a canonical
`{"proposal_id":ID,"row_id":ID|null,"status":ID}` receipt. This lets a later
`COUSE_PROPOSE` name an already admitted atom without asking the child to
compute a hash. No row payload, truth-audit bit, hidden rejection reason, score,
or future status is returned. At `A1`, a byte-for-byte replay over the sealed
complete ledger must reproduce every prefix receipt or the root fails.

### 2.3 `G_link_v3`

Inputs are `(A_LEDGER_V3, admitted ATOM_ROW table, OPPORTUNITY_MANIFEST,
ACTION_SCHEMA_TABLE, SUCCESS_SYMBOL_TABLE)`. A proposal is valid iff:

1. both atom rows were admitted from two support events with ordinals below
   the link proposal and `citations` is exactly those two distinct event IDs in
   lexicographic order;
2. the named co-use event is the first later `PUBLIC_EVENT` with both exact
   named support handles and its action is legal;
3. `intended_operation` equals the action schema's one canonical operation;
4. that schema names exactly two JSON Pointer paths in `action_args`; extraction
   at those paths yields the two ordered `(schema,endpoint_1,endpoint_2,value)`
   tuples represented by the proposed atoms, unordered between atoms but exact
   within each atom; no third relation-argument path is present; and
5. the public outcome symbol belongs to the presealed success-symbol set for
   that action family.

This is the entire syntactic co-use predicate. Hidden truth is again a one-bit
offline audit only. Per-link-slot conflict, duplicate, collision, and total
status behavior is identical to `G_atom_v3`. The admitted row records only
undirected adjacency between the sorted atom IDs.

### 2.4 Deck partitions and failure propagation

`A0` partitions opportunity slots, before behavior, into `CORE`,
`NULL_RESERVE`, and `D_SHAM_RESERVE`. `S_A` and `L_A` are admitted rows from
`CORE`. Reserve rows are compiled by the same laws but are capability-hidden
from every earlier actor/carrier. The root manifest lists every required core
atom/link, reserve link, and D-sham slot. A missing, false, conflicted,
colliding, or malformed required row sets every endpoint whose hidden proof or
control requires it to its registered failure value; the root remains in all
denominators. No opportunity or root is regenerated.

## 3. Root theorem and intervention fixtures

Each root/twin pair is deterministic conditional on its `A0` bytes. Opaque
handles are sampled without replacement and independently of semantics. The
generator supplies an offline proof object, never actor-visible, establishing:

- two same-start B goals with different unique paths of 3 or 4 carrier rows,
  including one required experiential link and no one-row/direct-action answer;
- a fixed-point-free type-, degree-, length-, and slot-preserving derangement;
- one authentic C signal link, one matched sham signal, exactly two live
  hypotheses, and a finite legal experiment menu with exactly one maximally
  informative experiment under the authentic signal;
- one new binary row selected by the complete pre-outcome outcome map;
- a disjoint D goal whose unique minimal semantic support is exactly one named
  old row plus that new row;
- a D twin that changes both bindings and the oracle action while preserving
  types, marginals, counts, lengths, slots, legal menus, and resource classes;
  and
- every null/reserve/sham fact is true but irrelevant to B, C, and D under the
  complete adaptive policy class in Section 5.

The CPU theorem enumerates all legal actions and semantic row subsets. For B,
every proper subset of each necessary path, every path with one necessary row
replaced, and every catalog/direct-action route has oracle value at most .25.
For D, the old+new pair has oracle value at least .90; every semantic subset
missing either member, even with every nuisance channel enabled, has value at
most .25. A root failing any theorem check is a scored failure, not an
exclusion.

## 4. B3/B7 — exact carrier state transitions

### 4.1 Common core and merge receipt

`A_CORE` is a relay-private clone of the selected parent-deleted child. If the
upstream checkpoint contains a mounted childhood adapter, the relay clone
materializes it once into the base parameters using the pinned deterministic
merge named at `R0`; no nursery corpus or optimizer is retained. The merged
clone must match the selected checkpoint on a presealed 64-prompt typed canary:
exact greedy token IDs and action bytes on every prompt and maximum absolute
float32 logit difference `<=1e-5`. Failure is global `NO_GO`. The upstream
checkpoint and packet remain byte-untouched. The relay then has one effective
base and at most one active relay LoRA.

The common immutable objects are:

```text
A_CORE       effective child weights/config/tokenizer/chat template
A_LEDGER_V3  audit-only public Phase-A provenance
DECK_A_AUTH  sorted S_A followed by sorted L_A
CATALOG_V3   fixed query/anchor/candidate slots and passive metadata
```

Deck order is `(row_kind,row_id)`. Catalog metadata contains only query type,
opaque anchor/candidate ID, schema/type, fixed ordinal, fixed maximum return
class, and readable bit. It contains no payload/hash/length, hit bit, support,
provenance, binding, target, arm, outcome, error, timing, or build state.

### 4.2 Text carrier

`TEXT_BUILD(deck,d_slot)` creates exactly:

```text
TEXT_CARRIER_V3 := {
  "catalog_sha256": SHA256,
  "rows": [TEXT_SLOT, ...],
  "schema_version": 3
}

TEXT_SLOT := {
  "candidate_id": ID,
  "payload": ATOM_ROW | USE_LINK_ROW | null,
  "slot_ordinal": INTEGER
}
```

Slots appear in strictly increasing ordinal order and candidate IDs are the
catalog values at those ordinals. Occupied payloads are exact carrier rows;
padding is literal JSON `null`. Unknown/missing/duplicate slots fail the build.
The file is immutable,
fsynced, hashed, reopened read-only in a fresh process, and checked against the
deck manifest. Text `READ` copies the indexed row exactly; a pad returns
`MISS`. `TEXT_SAME_SEMANTICS` is this carrier. It is a relay-local explicit
semantic carrier, not the upstream on-policy `ACTIVE_TEXT_FIXED` updater and
does not support a strong-baseline claim.

### 4.3 LoRA carrier and exact writer transaction

`LORA_BUILD(deck,d_slot,build_seed)` always starts from byte-identical
`A_CORE`, a fresh rank-8 all-layer attention+MLP LoRA (`alpha=16`, dropout 0),
and a zero-state AdamW optimizer. Initial A matrices use the pinned framework's
Kaiming-uniform algorithm and the committed seed; B matrices are zero.
Optimizer fields are `lr=0.00001`, `betas=(0.9,0.999)`, `eps=0.00000001`,
`weight_decay=0`, global gradient-norm clip 1.0, bf16 forward/backward, float32
optimizer state, batch size 1, no shuffle, packing, accumulation, scheduler,
early stopping, retry, or data-dependent branch. Deterministic-kernel failure
aborts.

For each occupied old row and the reserved D slot, the exact masked input is
the pinned chat template over one system message `PCFL_MEMORY_READER_V3` and
one canonical user object:

```text
{"anchor_id":ID,"candidate_id":ID,"op":"READ","query_type":ID,"schema_version":3}
```

The response-only target is the UTF-8 concatenation
`<PCFL_ROW_V3>\n`, the canonical carrier row, `\n</PCFL_ROW_V3>`, and exactly
one EOS token. Prompt/system/template tokens are masked. Each occupied row has
four consecutive exposures. The global order is reserved D-slot exposures
`0..3` first, then occupied old rows by `(row slot, exposure 0..3)`. A reserved
padding slot has the same fully rendered token length and executes the first
four positions with every token masked, a defined zero gradient, and an AdamW
step. At those first positions all moments are zero and weight decay is zero,
so padding changes no parameter while advancing the same optimizer counters as
a semantic D slot. Its target IDs come from the `R0` `PAD_TARGET_TABLE`: for
each finite D-slot token-length class, the table contains one task-disjoint
ASCII padding suffix of exactly that token count, no valid row delimiter, IDs,
endpoints, values, action, outcome, or goal. The root is invalid unless EDGE
and SHAM suffixes occupy the predeclared class. Each complete sequence is at
most 2,048 tokens
and target suffix at most 256; overflow, zero labels on a semantic row,
nonfinite values, skipped steps, target mismatch, or interrupted publication
aborts the arm.

There are no anchor, nursery, parent, raw-event, policy, goal, hypothesis, or
auxiliary training targets. Loss is averaged per response suffix and then
equally across occupied semantic positions; token length does not reweight
rows. All framework/model/tokenizer/kernel versions are `R0` hashes.

Publication is transactional: write to a fresh arm-private temporary path,
finish training, run typed-routing and row-read canaries, hash every
file, stop the trainer, mount in a fresh reader process, and atomically publish
only on all-pass. Failure publishes nothing and gives that arm its failure
score. No previous or partial adapter is mounted.

Every build receipt contains the hashes of `A_CORE`, deck/catalog, ordered
examples and token IDs, response masks, build seed, trainable
tensor names/shapes/dtypes in lexical order, initial/final adapter tensors,
initial/final optimizer state, step/clip/loss ledger, temporary and published
file manifest roots, process IDs, mount/off bytes, canary outputs, and actual
tokens/steps/time/bytes/energy.

### 4.4 Phase carriers

For carrier `k in {TEXT,LORA}`:

```text
B_AUTH_BUILD_k = BUILD_k(DECK_A_AUTH, PAD_D)
B_AUTH_k       = fresh read-only clone of B_AUTH_BUILD_k before any B call
B_DERANGED_k  = BUILD_k(S_A + DERANGE(L_A), PAD_D)
B_NULL_k       = BUILD_k(S_A + LINK_NULL_PROJECT(L_NULL_RESERVE), PAD_D)
C_AUTH_k       = independent fresh read-only clone of B_AUTH_BUILD_k
C_SHAM_k       = independent clone of B_AUTH_BUILD_k with only C signal-return substitution
C_REACH_PREFIX_k = independent clone of B_AUTH_BUILD_k; no change before experiment dispatch

D_EDGE_k       = BUILD_k(DECK_A_AUTH, G_new_row)
D_NOWRITE_k    = BUILD_k(DECK_A_AUTH, PAD_D)
D_SHAM_k       = BUILD_k(DECK_A_AUTH, D_SHAM_ROW)
D_SWAP_k       = BUILD_k(DECK_A_AUTH, G_new_row), then read-time D binding swap
D_REACHOFF_k   = BUILD_k(DECK_A_AUTH, PAD_D)
```

`C_AUTH`, `C_SHAM`, and `C_REACH_PREFIX` have identical carrier bytes;
`C_SHAM` differs only at the declared signal return and `C_REACH_PREFIX` only
later at experiment dispatch. `B_BRIDGE_CUT/TWIN` are independent read-only
clones of `B_AUTH_BUILD` with only their Section-6 read/world substitutions;
they are not additional builds or mutable descendants.

All `BUILD_k` calls are clean-base rebuilds. No D arm inherits adapter bytes,
optimizer slots, mutable text state, cache, mount, or RNG from Phase C or
another arm. The identical old deck, number/order of positions,
build calls, seeds, catalog, and slot byte class are used; only the declared D
slot target/mask differs. Thus `W0/W1/Fbind` compare one semantic-slot
assignment and its resulting carrier, not unknown incremental optimizer state.

`D_SHAM_ROW` is the lexicographically first valid `D_SHAM_RESERVE` atom after
matching schema, endpoint types, value-domain cardinality, canonical byte and
token class, public support/citation class, catalog slot, and exposure count.
It must be true, previously uncarried, and theorem-proved irrelevant to D.
Missing or nonunique minimum after the fixed lexicographic tie rule is root
failure. Its public citations remain audit-only.

`LINK_NULL_PROJECT` builds a bipartite graph between authentic link slots and
admitted `NULL_RESERVE` links. An edge exists only on exact schema, endpoint
types, degree, age bin, canonical byte/token class, support/citation class, and
catalog/resource stratum, and only if the CPU theorem proves zero utility for
all B/C/D goals under Section 5. The projection is the lexicographically first
perfect matching obtained by exhaustive permutations in authentic-slot order.
No realized behavior-dependent search criterion exists. No perfect matching is
root failure. These are the child's truthful public reserve co-use links, not
hidden-authored experiential links.

Atomic retention is scored on every required core atom in row-slot order:

```text
ATOM_OK_k,r,j = 1[one charged READ returns the exact canonical atom row
                   and its sealed one-row atomic action has public value >=.75]
Aret_k,r = arithmetic mean_j ATOM_OK_k,r,j
```

There is no best-of retry or selected atom subset. Missing/malformed returns,
illegal actions, and carrier/build failure are zero.

## 5. B5 — finite adaptive reader closure

The only reader action is:

```text
READ(query_type, anchor_id, selected_candidate_id)
```

Each episode permits at most four calls. Each call selects exactly one
candidate; batches are illegal. The runtime performs one exact lookup and one
copy/strict LoRA parse. There is no ranking, shortlist, semantic validation,
automatic follow, fallback generation, hidden retry, repair, or second
resolver. Repeated identical calls are legal but each consumes a call and the
fixed 256-return-token charge. `STOP` burns remaining call/token positions.
Miss, `UNAVAILABLE`, malformed LoRA response, timeout, and success each use the
same presealed public timing class and logical charge; actual physical cost is
reported privately to the resource ledger and is not actor-visible.

At decision `t=0..4`, the controller history is exactly:

```text
H_t = (public goal and state bytes,
       fixed catalog metadata,
       prior selected query/anchor/candidate triples,
       result class in {HIT,MISS,UNAVAILABLE,MALFORMED},
       exact returned canonical row or EMPTY,
       charged call/token counters,
       equality/type relations among seen opaque handles)
```

No wall clock, payload hash/length, cache, path, address, logits, hidden truth,
arm, target, twin, build state, receipt, raw ledger, or root seed enters `H_t`.

A legal target-blind policy is **exactly** a deterministic function from a
reachable handle-renaming-equivalence class of `H_t` to one legal `READ`, one
legal terminal `ACT(public_action_id)`, or `STOP` (registered failure). At
depth four only terminal `ACT` or `STOP` is legal. Raw opaque ID spellings are
erased; equality, registered type, catalog
ordinal, and returned finite row symbols remain. The dynamic program expands
all legal actions at every reachable abstract history through depth four,
memoizes identical abstract states, and computes the maximum terminal score.
It therefore includes adaptive query choice after hits, misses, errors,
returned rows, and charged timing classes; stopping; repeats; and every legal
reacquisition path. Batches and runtime retries do not exist. A randomized
policy is a mixture of deterministic policies, and expected score is linear,
so its maximum is attained by an enumerated deterministic policy. Any
controller RNG is represented exactly by one pre-action mixture key; it
observes no additional field and creates no history class. This is the
machine-checkable reduction closing randomized controllers.

Policy selection occurs once on the eight disjoint DEV roots. A joint
finite-horizon dynamic program evaluates each shared handle-equivariant policy
on the mean of all DEV goals, selects the maximum, and breaks ties by the
lexicographically smallest canonical policy table. Its bytes and hash seal at
`DV1` before confirmation identities exist. Confirmation `CTRL_FULL_r` is the
score of that one frozen policy; no confirmation-root outcome selects a
policy. For every proper field subset, repeat the same DEV-only selection after
erasing those fields and seal one policy. `CTRL_FEATURE_SUBSET_MAX_r` is the
maximum confirmation score over this presealed finite roster, a deliberately
adverse fixed endpoint. An empty/malformed controller has the adverse leakage
value rather than disappearing. DEV may optimize enumerator implementation
speed only; neither history abstraction nor policy class changes. If exact
joint enumeration does not fit the separately ratified CPU ceiling, the
interface/cap must be redesigned under a new deliberation; approximation is
forbidden. The leaked-oracle controller is a separate positive fixture
whose history adds the hidden proof and expected action; it is never an actor
or negative controller.

In D, catalog bytes and passive metadata are identical in every arm and contain
no new binding. A fixed reserved slot exists in all arms; `D_EDGE` returns the
new row there, `D_SHAM` its sham row, and `D_NOWRITE/D_REACHOFF` a matched
`MISS`. The statement “catalog contains no answer” applies to metadata and
control contents, not to the declared semantic return of the selected D-edge
slot.

## 6. B4 — Phase-B potential outcomes and algebra

Phase B writes nothing. Forks start from the same `A_CORE`, public state, goal,
catalog, actor state, and coupled non-goal exogenous bytes; only carrier deck or
declared read substitution differs. After B, every fork is destroyed and C
starts from `C0`, never a B descendant.

For goal `g in {g0,g1}` and intervention `z`, define:

```text
V_B(z,g)    = clipped public terminal action value in [0,1]
PATH_B(z,g) = 1 iff the exact emitted GOAL_ANCHOR/READ/FOLLOW sequence,
              with no omitted/extra row, equals the hidden required path
Y_B(z,g)    = PATH_B(z,g) * V_B(z,g)
```

Malformed/missing trace, wrong goal/state handle, unreturned follow ID,
additional semantic hop, illegal/undispatched terminal action, timeout, carrier
failure, or missing required row gives `PATH_B=0`, `V_B=0`, and `Y_B=0`.
Within root, `mean_g` is the arithmetic mean over the two presealed goals; no
goal is dropped.

The five intervention names are complete:

- `B_AUTH`: authentic carrier and authentic world;
- `B_DERANGED`: independently rebuilt projected-deranged carrier;
- `B_NULL`: independently rebuilt matched truthful-null carrier;
- `B_BRIDGE_CUT`: authentic carrier, but the first attempted return of every
  proof-necessary bridge slot is replaced by matched `MISS`;
- `B_BRIDGE_TWIN`: authentic carrier, but all registered bridge-slot returns
  and the world are changed by the sealed twin involution.

There is no `BRIDGE_SUB` name. Define:

```text
CONNECTED_AUTH_r      = mean_g Y_B(B_AUTH,g)
CONNECTED_DERANGED_r = mean_g Y_B(B_DERANGED,g)
CONNECTED_NULL_r      = mean_g Y_B(B_NULL,g)
Cbind_value_r = CONNECTED_AUTH_r - CONNECTED_DERANGED_r
Cnull_value_r = CONNECTED_AUTH_r - CONNECTED_NULL_r

GOAL_PATH_r = mean_g 1[first READ belongs to Q_g
                       and exact path equals P_g
                       and V_B(B_AUTH,g) >= .75]
CTRL_FULL_r = mean_g best adaptive target-blind DP score
Tgoal_value_r = GOAL_PATH_r - CTRL_FULL_r

Tcut_value_r = mean_g (Y_B(B_AUTH,g) - Y_B(B_BRIDGE_CUT,g))
```

`Q_g` is the exact nonempty set of query triples whose returned first row is on
`P_g`, enumerated by the hidden proof at `A0`. `Q0 != Q1`; a common first query
or common exhaustive suffix fails the corresponding indicator. The paired
goals share actor/base/carrier bytes and a registered paired RNG distribution:
one presealed root RNG tape is addressed by `(phase,logical_call,token_index)`,
never by goal or arm. Thus every non-goal random/exogenous byte is coupled.

For the twin, let `a_auth(g)` and `P_g` be the authentic oracle action/path and
`a_twin(g)` and `tau(P_g)` their distinct twin versions. Define:

```text
REDIRECT_g = 1[emitted path = tau(P_g)
               and emitted action = a_twin(g)
               and twin-world value(a_twin(g)) >= .75
               and twin-world value(a_auth(g)) = 0
               and emitted path != P_g]
STUBBORN_g = 1[emitted path = P_g or emitted action = a_auth(g)]
Ttwin_value_r = mean_g (REDIRECT_g - STUBBORN_g)
```

The generator additionally evaluates every proper subset of every required
path, every simultaneous multi-row cut, every alternative direct action, and
every nuisance-feature combination. `B_SUBSET_MAX_r` is their maximum oracle
score and must be at most .25. A single named bridge is not sufficient.

## 7. B6 — Phase-C signal and reachout timing

### 7.1 Authentic and sham signal

At `A0`, each root names one exact tuple
`C_SIGNAL=(query_type,anchor_id,candidate_id,auth_link_id,sham_link_id)`.
From byte-identical `C0` clones, the actor sees the same goal/state/catalog and
must issue that exact `READ` as its first semantic read. A different/missing
read is failure in all C arms; the harness does not search for a later match.
Intervention activates only while returning this selected slot:

- `AUTH_SIGNAL` returns the canonical authentic old `USE_LINK_ROW`;
- `SHAM_SIGNAL` returns the presealed canonical truthful irrelevant reserve
  link under the same catalog ID and passive resource signatures.

The sham matcher requires exact schema, endpoint types, support bit, citation
cardinality/age bins, legality, row/link counts, degree, canonical byte/token
class, query/catalog slot, action menu, return/result/timing class, and exposure
count. Both links have offline public-evidence posterior 1 for their own
relation because their cited deterministic public success events occurred.
Before and after either signal, the registered actor-public posterior over the
missing C value is exactly `(1/2,1/2)`; neither link answers it. Before the
read, the public posterior over which matched link occupies the slot is also
`(1/2,1/2)`. The authentic relation selects which public experiment is
separating; the sham relation concerns a theorem-independent variable.
Failure of any equality/equipoise predicate is root failure, never sham search.

The pre- and post-read actor-public information sets are exact:

```text
I_C_pre  = public C goal/state + fixed catalog + charged counters
I_C_post = I_C_pre + selected READ triple + one returned canonical row
           + fixed result/timing class
```

No proposal/citation/event/root/arm/target/build metadata is present.

### 7.2 Declaration and scores

After the signal and before an outcome, the child emits exactly:

```text
GAP(schema,endpoints,cited_old_row_ids)
HYPOTHESES(value=h0,value=h1)
PREDICT_MAP(experiment=e,
            public_outcome_o0 -> CANONICAL_ROW(schema,endpoints,h0),
            public_outcome_o1 -> CANONICAL_ROW(schema,endpoints,h1))
ACT(e)
```

The two hypotheses and outcomes are in lexicographic order, distinct, and
complete. `G_new_v3` receives only these sealed canonical bytes, the dispatched
typed action, and the later public event. It requires exact action equality and
uses the total presealed map to select one already committed row, adding no
field beyond the `ATOM_ROW` grammar. Invalid syntax/action, missing map member,
`UNAVAILABLE`, ambiguous/unknown outcome, inconsistent endpoint/domain, or
truth mismatch yields `NO_ADMISSION`. It cannot read D, post-outcome prose,
hidden truth except the terminal one-bit audit, or a model.

Its audit-only `G_NEW_RECEIPT` contains the selected pre-outcome map-entry hash,
the exact `support_event_id`, action/event ordinals, compiler status, row hash,
and one-bit truth audit. None of those receipt/citation fields enters the
carrier row or returns to the actor.

The offline posterior is computed only after the action seal from the finite
root truth table and `I_C_post`; no value returns to life. Root scores are:

```text
Qgap_z      = 1[exact supported gap, two live hypotheses, old citations]
Qselect_z   = 1[legal dispatched experiment maximizes target EIG]
Qrelevant_z = target EIG(e) in bits, clipped to [0,1]
Qselect_value_AS  = Qselect_AUTH - Qselect_SHAM
Qrelevant_value_AS= Qrelevant_AUTH - Qrelevant_SHAM
```

Irrelevant-variable information gain is zero. Missing/malformed/undispatched
objects and any compiler failure score zero.

### 7.3 Single `REACHOUT_OFF` boundary

`REACHOUT_OFF` does **not** alter the signal read. It forks from the exact
sealed `C2` state after authentic signal receipt, declaration, predictions,
and typed experiment selection but immediately before public dispatch. Prefix
bytes through `ACT(e)` and the RNG-counter position are identical to AUTH.

At dispatch, AUTH executes `e`; `REACHOUT_OFF` returns canonical public
`UNAVAILABLE` without executing it. Both consume the same logical action,
time, token, resolver, and resource charges. The counterfactual D-start world
is generated from the same presealed function of the C pre-dispatch world and
then overwrites every physical side effect unrelated to the semantic outcome,
so inventory, clock, reward, files, and opportunities match AUTH. It uses the
same D target, twin, catalog, candidate IDs, RNG tape, process-reset law, and
old deck. `G_new_v3(UNAVAILABLE)=NO_ADMISSION`; `D_REACHOFF` executes the exact
clean old-deck plus masked-padding build and emits a `NO_SEMANTIC_BUILD` receipt.
Any prefix mismatch, charge mismatch, new row, or build mismatch sets
`Freacq` to its failure value. This is a total acquisition-path intervention,
not a controlled write contrast.

## 8. B7 — Phase-D writer, reset, and literal closure

`EDGE_WRITE`, `NO_WRITE`, `SHAM_WRITE`, and `NEW_BIND_SWAP` fork only after the
AUTH public outcome, `G_new_v3` row, compiler receipt, and event seal exist.
They receive the exact D builds in Section 4.4. `NEW_BIND_SWAP` trains only the
truthful authentic row and applies the presealed fixed-point-free endpoint
permutation at READ; no false target enters the writer.

Before D goal reveal, every arm starts a fresh process and resets/hashes actor
messages, KV/cache, world, inventory, clocks, counters, rewards, observation
cache, files and descriptors, environment variables, sockets, RNG cursor,
reader/index/cache, mount, errors/retries, and catalog. Raw ledgers, C response,
action, outcome, hypotheses, compiler receipt, build receipt, and audit objects
are capability-denied. Actor-visible bytes are only the fresh D goal/state,
fixed catalog, charged counters, and assigned carrier returns.

The literal closure feature registry is:

```text
F_D = {OLD_REQUIRED_ROW, NEW_REQUIRED_ROW, ALL_OTHER_OLD_ROWS,
       COMPOUND_OLD_ROWS, C_SIGNAL_ROW, C_ACTION, C_OUTCOME,
       C_GAP_HYPOTHESES, ACTOR_PROCESS_CACHE, READER_CACHE,
       RAW_AUDIT_LEDGER, CARRIER_METADATA, CATALOG_METADATA,
       MOUNT_BUILD_STATUS, PASSIVE_TIMING_ERRORS, REACQUISITION_HISTORY}
```

For each generated root, the CPU closure constructs all `2^16` active/passive
feature masks. `ALL_OTHER_OLD_ROWS` and `COMPOUND_OLD_ROWS` are themselves
expanded over every semantic subset generated by the root. For each mask,
`REACQUISITION_HISTORY` expands the complete Section-5 adaptive-history DAG,
including hits, misses, malformed/unavailable returns, repeats, stopping, and
the one final action. B and D permit no nonterminal world action; an attempted
world action ends the episode and is scored as its terminal action. The oracle
and every feature-
subset controller are evaluated for every member. Enumeration order is
increasing 16-bit mask, then semantic-subset bitset, then history-DAG node ID.

The unique-minimal-support receipt requires:

```text
oracle(OLD_REQUIRED_ROW + NEW_REQUIRED_ROW) >= .90
max oracle(any mask lacking OLD_REQUIRED_ROW or NEW_REQUIRED_ROW) <= .25
cut either row changes the unique oracle terminal action
the binding twin redirects to its distinct twin action
no catalog/passive/control content contains the new binding
```

This covers compound rows, combinations of C artifacts, all caches/build
signatures, and every reacquisition route. Any counterexample is root failure
and a generator-version NO-GO before scientific execution if found in CPU
fixtures.

Define delayed scores with exact trace/path law as in B:

```text
Y_D(z) = exact_required_D_path(z) * clipped_terminal_value(z)
W0_value_r    = Y_D(D_EDGE) - Y_D(D_NOWRITE)
W1_value_r    = Y_D(D_EDGE) - Y_D(D_SHAM)
Fbind_value_r = Y_D(D_EDGE) - Y_D(D_SWAP)
Freacq_value_r= Y_D(D_EDGE_AUTH_PATH) - Y_D(D_REACHOFF)
```

All quantities suffixed `_value` are exact bounded raw potential-outcome
summaries and are reported descriptively. The confirmatory components without
that suffix are the strict binary paired reductions in Sections 10--11; an
implementation may not substitute one scale for the other.

Failure of a positive arm gives it zero; failure of a negative/control arm
gives it one, so a technical failure cannot create a favorable contrast.
`W0/W1/Fbind` are controlled post-AUTH effects. `Freacq` is separately labeled
the total effect of the authentic reachable acquisition path.

## 9. B8 — named-control acceptance registry

All logical calls use four READ slots, 256 returned-token charge per slot, the
same catalog, action menu, public state, and counter-key schedule. Physical
tokens, model calls, training work, bytes, latency, and energy are always
reported by arm; unequal resources are never called matched.

Section 10 compiles every repeated raw cell to a strict binary positive or
leakage predicate. A positive root field is one only when every registered
cell succeeds; a control root field is one when any registered cell leaks.
Malformed/missing/build failure is therefore 0 for a positive and 1 for a
control. Paired differences cannot improve through technical failure.

For every named control `name`, `u_auth_rk[name]` is the strict positive field
on the task-matched authentic carrier and `u_rk[name]` is the strict leakage
field on the same cells under the named intervention. The frozen roster is:

```text
goal_only, state_only, identifier_only, candidate_only, passive_signature,
source_action_string, unaided_generative
```

LoRA additionally has `wrong_life` and `adapter_off`. Every pair has the exact
same goal, public start, cell order, action menu, and coupled exogenous bytes;
only the named visibility/carrier intervention differs.

| name | exact construction/intervention time | root potential outcome | decision |
|---|---|---|---|
| `TEXT_EXPLICIT` | Section-4 text carrier for every phase | all `*_TEXT` positive/control fields | must clear the complete ordered text sequence |
| `TEXT_SAME_SEMANTICS` | same row IDs, canonical row bytes, slots, catalog, read cap, goals, worlds, and arm decks as paired LoRA; carrier alone is text | `same_mismatch_r` is 1 on any exact read/action semantic mismatch | mismatch-rate CP upper bound `<.05`; no superiority claim |
| `LORA_AUTH` | Section-4 LoRA build, mounted only during READ | all `*_LORA` positive/control fields | must clear the complete ordered LoRA sequence |
| `ADAPTER_OFF` | at each LoRA READ, identical process with relay adapter disabled and no text carrier | `u_LORA[adapter_off]` and paired authentic field | leakage-rate CP upper bound `<.10`; paired `Kmin` LCB `>.20` |
| `WRONG_LIFE` | at build seal, map the type/ordinal slots of a same-child disjoint-root carrier onto the assayed catalog while retaining its disjoint semantic handles; no other state crosses | `u_LORA[wrong_life]` and paired authentic field | leakage-rate CP upper bound `<.10`; paired `Kmin` LCB `>.20` |
| `GOAL_ONLY` | show only public goal plus empty carrier/catalog-neutral padding | `u_k[goal_only]` | worst-control rules |
| `STATE_ONLY` | show only public start state plus empty carrier/catalog-neutral padding | `u_k[state_only]` | worst-control rules |
| `IDENTIFIER_ONLY` | show only handle equality/type/ordinal fields with semantics erased | `u_k[identifier_only]` | worst-control rules |
| `CANDIDATE_ONLY` | catalog visible, every READ returns matched `MISS` | `u_k[candidate_only]` | worst-control rules |
| `PASSIVE_SIGNATURE` | show catalog plus timing/error/build/resource classes, semantics erased | `u_k[passive_signature]` | worst-control rules |
| `UNAIDED_GENERATIVE_READ` | no carrier; base is prompted with the exact READ wrapper and may emit one row under identical output cap | `u_k[unaided_generative]` | worst-control rules |
| `SOURCE_ACTION_STRING` | at read time return only NFKC public `action_family` plus canonical `action_args` from the source event, with IDs/citations/outcome removed and matched charge | `u_k[source_action_string]` | worst-control rules |
| `LEAKED_ORACLE` | CPU positive fixture adds hidden required path and action after all ordinary bytes seal; never model-visible | `o_r` | CP lower bound `>.95` |
| `LINK_NULL` | independent `B_NULL` build from deterministic truthful reserve projection | `c_null_rk`, `Cnull_rk` | leakage CP upper `<.10`; paired bound `>.20` |
| `DERANGEMENT` | independent `B_DERANGED` build before B | `c_der_rk`, `Cbind_rk` | leakage CP upper `<.10`; paired bound `>.20` |
| `BRIDGE_CUT` | mask every proof-necessary bridge return with `MISS` at B read dispatch | `t_cut_rk`, `Tcut_rk` | leakage CP upper `<.10`; paired bound `>.20` |
| `BRIDGE_TWIN` | substitute all registered bridge rows and twin world together at B read dispatch | `t_redir_rk`, `Ttwin_rk` | redirection CP lower `>.75`; original action is forbidden inside predicate |
| `NO_WRITE` | clean D build with old deck and masked pad in reserved slot | `d_no_rk`, `W0_rk` | leakage CP upper `<.10`; paired bound `>.20` |
| `SHAM_WRITE` | clean D build with supported uncarried irrelevant row in reserved slot | `d_sham_rk`, `W1_rk` | leakage CP upper `<.10`; paired bound `>.20` |
| `NEW_BIND_SWAP` | authentic clean D build, fixed endpoint permutation only at READ | `d_swap_orig_rk`, `d_swap_redir_rk`, `Fbind_rk` | original upper `<.10`; redirect lower `>.75`; paired bound `>.20` |
| `REACHOUT_OFF` | deny already selected C experiment only at public dispatch; old-deck masked D build | `d_off_rk`, `Freacq_rk` | leakage CP upper `<.10`; paired bound `>.20`, separate total-path label |

The `WRONG_LIFE` slot map is the unique ascending-ordinal bijection within
`(row_kind,schema,endpoint types,token-length class)`. Current-root catalog and
candidate IDs remain visible; returned payloads retain the source root's
disjoint semantic handles. Absence of a perfect bijection is adverse root
failure, not a new search or root replacement.

`u_auth_min=min_name u_auth[name]`, `u_max=max_name u[name]`, and
`Kmin=min_name(u_auth[name]-u[name])` are the fixed worst-control reductions.
Every named pair is still printed. The full adaptive and every proper
visible-feature-subset controller feed `b_leak`/`d_leak`; any success makes the
root leakage field one. No comparison in this relay is a comparison to
upstream `ACTIVE_TEXT_FIXED` or `R0`, and no LoRA-versus-text superiority family
exists.

## 10. B9 — per-root temporal chains

Every repeated raw cell has a binary predicate. For a positive field, average
the fixed cells and set the root field to one iff that average is exactly one.
For leakage/control, set the root field to one iff any cell leaks. This yields
the exact primitive roster `o,a,c_auth,c_der,c_null,t_auth,t_blind,t_cut,
t_redir,b_leak,q_gap,q_sel_auth,q_sel_sham,q_rel_auth,q_rel_sham,gnew,
d_edge,d_no,d_sham,d_swap_orig,d_swap_redir,d_off,d_leak,u_auth[name],u[name]`
for each applicable carrier. `same_mismatch_r` is one iff any paired
`TEXT_SAME_SEMANTICS` versus LoRA read returns different canonical semantics
or yields a different paired semantic-action predicate.

The failure-inclusive same-root chain is:

```text
B_OK_rk = c_auth_rk
          * (1-c_der_rk) * (1-c_null_rk)
          * t_auth_rk * (1-t_blind_rk) * (1-t_cut_rk)
          * t_redir_rk * (1-b_leak_rk)

C_OK_rk = q_gap_rk * q_sel_auth_rk * (1-q_sel_sham_rk)
          * q_rel_auth_rk * (1-q_rel_sham_rk) * gnew_rk

D_OK_rk = d_edge_rk * (1-d_no_rk) * (1-d_sham_rk)
          * (1-d_swap_orig_rk) * d_swap_redir_rk
          * (1-d_off_rk) * (1-d_leak_rk)

CTRL_OK_rk = u_auth_min_rk * (1-u_max_rk)

TEXT_chain_r = o_r * a_r,TEXT * B_OK_r,TEXT * C_OK_r,TEXT
               * D_OK_r,TEXT * CTRL_OK_r,TEXT

LORA_chain_r = o_r * a_r,LORA * B_OK_r,LORA * C_OK_r,LORA
               * D_OK_r,LORA * CTRL_OK_r,LORA
               * (1-same_mismatch_r)

COMPLETE_chain_r = TEXT_chain_r * LORA_chain_r
```

Phase B is the same root's destroyed fork and C restarts from its exact `C0`;
“same chain” means one sealed root and its coupled potential-outcome forks in
temporal order, not one mutable branch through B/C/D. The products require the
same root to clear acquisition/retention, connected use, traversal, C gap and
experiment, relevant public information gain, truthful admission/write, D
two-row use, cuts/twins, reachout, and every named control. Aggregate component
success cannot set a root's chain to one.

`TEXT_chain`, `LORA_chain`, and `COMPLETE_chain` are their arithmetic means over
the final selected N. Their respective exact-binomial minima are `.60`, `.50`,
and `.40`. `COMPLETE_chain` is not the product or minimum of aggregate rates.
Text must finish and pass before LoRA opens; LoRA still runs all N roots,
including text-chain failures. Population component tests remain additionally
necessary and cannot substitute for the chain.

## 11. B10 — exact statistics and power lock

### 11.1 Unit, values, and failure inclusion

The independent unit is one sealed root/twin pair conditional on the fixed
child. Goals, arms, twins, calls, carrier builds, and seeds are repeated
measures reduced inside the root by Section 10. Every primitive statistical
field is binary; paired components are in `{-1,0,1}`. Public continuous values
and within-root means remain descriptive only.

There are no missing cells. Missing, malformed, unsupported, unavailable,
compiler rejection, absent matched deck/sham/derangement, fit/mount/read/action
failure, post-exposure timeout, or receipt failure is zero for a positive, one
for a leakage/mismatch, and zero for a chain. Those adverse values propagate
before contrasts. All outcomes seal before scoring.

An infrastructure cell may be relaunched at most twice after the initial
attempt only when it failed before any actor-visible byte, gradient/update,
reader return, public dispatch/outcome, or branch-specific state and every
pre-dispatch hash/counter is unchanged. A third failure is adverse-filled.
Post-exposure failure, hardware substitution, root regeneration, new seed,
rollback after output, complete-case analysis, and root replacement are
forbidden. A code/hash/capability violation invalidates the study rather than
becoming an ordinary zero.

### 11.2 Decision thresholds

All floor/ceiling/SESOI values are exact decimals representing rationals:

```text
leaked-oracle rate floor                        .95
Phase-A retention rate floor                    .80
other authentic/redirection rate floor          .75
every leakage/control/mismatch rate ceiling     .10
same-semantics mismatch ceiling                 .05
paired causal-component SESOI                   .20
TEXT_chain minimum                              .60
LORA_chain minimum                              .50
COMPLETE_chain minimum                          .40
```

A positive contrast passes only when its lower confidence endpoint exceeds
`.20`, not merely zero. A floor passes only when its lower endpoint exceeds the
floor. A control passes only when its upper endpoint is strictly below its
ceiling. The fixed power alternatives are respectively `.99`, `.90`, `.85`,
`.02`, `.01`, paired probabilities `(.80,.18,.02)` for `(+1,0,-1)`, and chain
rates `.75/.65/.55`. Pilot outcomes cannot move them.

### 11.3 Confidence construction

For `x` binary successes among N, use one-sided Clopper--Pearson bounds:

```text
CP_L(x,N,gamma) = 0 if x=0 else BetaQuantile(gamma;x,N-x+1)
CP_U(x,N,gamma) = 1 if x=N else BetaQuantile(1-gamma;x+1,N-x)
```

`BetaQuantile` is the smallest real whose regularized incomplete-beta CDF
reaches the requested probability. Calculations use correctly rounded binary64
plus a directed-rounding decimal enclosure of width at most `1e-12`; both ends
must lie strictly beyond a decision boundary or the endpoint fails. Floors use
`CP_L(x,N,.05)` and ceilings use `CP_U(x,N,.05)`.

For paired `D_r in {-1,0,1}`, let `n_plus=count(D=1)` and
`n_minus=count(D=-1)` and define:

```text
L_delta = CP_L(n_plus,N,.025) - CP_U(n_minus,N,.025)
```

The Bonferroni union bound gives at least 95% finite-sample coverage for
`E[D]`; ties remain in N. A component passes only if `L_delta>.20`. There is no
Student-t, bootstrap, asymptotic binomial, task-level, seed-level, mixed-model,
covariate, or outlier fallback.

### 11.4 Ordered confirmatory family

After deterministic provenance/deletion/generator/oracle/closure/resource gates
pass, test the exact fixed sequence:

```text
V0       oracle floor and all nonstatistical integrity receipts
TXT-A    a_TEXT
TXT-C    c_auth; c_der/c_null; Cbind/Cnull
TXT-T    t_auth/t_redir; t_blind/t_cut/b_leak; Tgoal/Tcut
TXT-Q    q_gap/q_sel_auth/q_rel_auth/gnew; sham ceilings; Q contrasts
TXT-W    d_edge; d_no/d_sham; W0/W1
TXT-FB   d_swap_redir/d_swap_orig/Fbind
TXT-FR   d_off/Freacq, total-path label only
TXT-CTL  u_auth_min/d_leak/u_max/Kmin
TXT-CH   TEXT_chain > .60
LRA-A    a_LORA
LRA-C    c_auth; c_der/c_null; Cbind/Cnull
LRA-T    t_auth/t_redir; t_blind/t_cut/b_leak; Tgoal/Tcut
LRA-Q    q_gap/q_sel_auth/q_rel_auth/gnew; sham ceilings; Q contrasts
LRA-W    d_edge; d_no/d_sham; W0/W1
LRA-FB   d_swap_redir/d_swap_orig/Fbind
LRA-FR   d_off/Freacq, total-path label only
LRA-CTL  u_auth_min/d_leak/u_max/Kmin/same_mismatch
LRA-CH   LORA_chain > .50
BOTH-CH  COMPLETE_chain > .40
```

Each tier is an intersection-union test: every listed component uses one-sided
alpha .05 and the tier passes only if all pass. Because the tier null is the
union of component nulls, no within-tier split is needed. Fixed sequence
controls the probability of releasing any false higher-tier claim at .05.
Failure stops higher language permanently but does not erase descriptive lower
results.

This is also the execution order: complete and reduce all text roots before
opening LoRA, then run LoRA on every final-N root. No component claim is
released outside the sequence. A new standalone, unordered, subgroup,
carrier-advantage, or superiority claim requires a separately ratified family;
no post-outcome Holm family is invented here.

### 11.5 Exact endpoint registry

Sections 1--10 of
`research_loop/advisory/20260907_one_child_pcfl_relay_b9_b10_statistics_power_lock_v1.md`
at SHA-256
`136dcf898de6fd97e850bd103bbbb3fee05a885effafa73ed61788c2b0709225`
are incorporated as the normative statistics packet, with the B1--B8 raw-cell
objects supplied by Sections 2--9 here. If a summary in this note differs, the
hashed statistics packet governs statistics only; this note governs topology,
grammar, carrier, intervention, writer, reader, and raw-cell construction. Any
true cross-boundary inconsistency is `NO_GO`, not discretionary precedence.
The sole explicit integration override is Section 11.7's logically coherent
joint simulation of the three chain coordinates; it replaces independent
per-endpoint inverse-CDF mapping for those three coordinates only.

The statistics manifest contains exactly 75 ordered decisions: one V0 oracle
decision, 36 text decisions, 37 LoRA decisions, and one `BOTH-CH`. It prints
every endpoint ID, raw-cell roster, formula, carrier/phase, direction,
threshold, failure value, and rung. `u_auth_min`, `u_max`, and `Kmin` each count
once because they are fixed worst-control endpoints; every named constituent
is still reported. An alias may reuse a raw cell but never removes its named
endpoint.

### 11.6 Exact marginal and conjunctive power

For every candidate N in the Section-1 grid, enumerate `x=0..N` under each
floor/ceiling/chain endpoint's exact binomial planning alternative and sum only
counts that pass Section 11.3. For each paired component, enumerate every
`(n_plus,n_zero,n_minus)` summing to N under `(.80,.18,.02)` and sum only states
whose `L_delta>.20`. No normal or Monte Carlo approximation enters marginal
power.

For the literal 75-decision family, let `beta_j(N)=1-power_j(N)`. The binding
arbitrary-dependence gate is `sum_j beta_j(N)<=.20`, which guarantees at least
.80 conjunctive power by the union bound. Each of the three chain endpoints
must also have marginal power at least .90. These assumptions are planning
points, not acceptance thresholds or predictions.

### 11.7 Required dependence simulation and final N

A valid 32-root nuisance pilot is mandatory. Its firewall emits only the
anonymized endpoint ranks and Spearman matrix specified in the incorporated
lock. For each candidate N, run exactly 200,000 rank-copula simulations. The
SHA-256 counter-mode RNG, rejection-free uniform construction, tie/row hashes,
rank-to-uniform formula, decision-coded inverse CDFs, and left-continuous
mapping are the exact bytes in that lock; no library PRNG or pilot marginal
effect is available.

The construction resamples one complete pilot rank row per synthetic root and
uses one common uniform within that row, preserving observed rank dependence
while replacing every marginal with its fixed planning alternative. Let `s_N`
be simulations passing the entire ordered conjunction. Simulation passes iff
`CP_L(s_N,200000,.01)>=.80`.

The three chain coordinates are never simulated independently. Form the pilot
categorical state `(TEXT_chain,LORA_chain)` ordered
`(0,0)<(0,1)<(1,0)<(1,1)`, rank those states with the same sealed tie law, and
map its rank-copula uniform through the exact planning probabilities
`.15,.10,.20,.55` in that order. Set simulated
`COMPLETE_chain=TEXT_chain*LORA_chain`. This produces marginals
`.75,.65,.55` and makes an impossible complete-without-both synthetic root
unrepresentable.

Final N is the smallest grid member passing the analytic union-bound rule,
all three chain-power rules, and this simulation. If none through 512 passes,
pilot/firewall evidence is incomplete, or the independent resource ceiling is
lower, confirmation stops. No confirmation roots exist until that selected N
and the complete power receipt are separately ratified. There is no later
extension.

### 11.8 Required power receipt

Before confirmation root generation, a separately ratified `N0` receipt must
contain: v3/analysis/power-program hashes; `P0/R0/PU/DV0/DV1` receipt hashes;
pilot-root manifest and disjointness proof; firewall/tie/row/rank-correlation
hashes; 75-endpoint ordered manifest; every exact binomial/multinomial marginal
power; union-bound sum; three chain powers; all eight candidate-N simulation
counts and 99% lower bounds; RNG/source/runtime hashes; selected `FINAL_N` or
`STOP`; resource comparison; and explicit zero confirmation-stage extension.
A `PASS` is necessary but cannot itself authorize root generation, a model
call, or GPU work.

This adopted lock is deliberately conservative. Its 75-decision conjunction,
32-root nuisance pilot, and 200,000 rank-copula simulations per candidate N are
substantial planning machinery; they are retained because B9/B10 demand an
all-mediators claim with arbitrary-dependence protection, not because more
multiplicity is scientifically desirable. No optional Holm/superiority family
is added. The lock assumes iid roots from the frozen distribution and that the
B1--B8 raw predicates are mechanically decidable. Sections 2--9 supply the
candidate definitions; future CPU conformance and actual receipts must verify
those assumptions before the power rule can select N.

## 12. Execution graph and kill gates

The optional relay may begin only after the parenting headline artifacts are
sealed or independently stopped. It has no incoming edge that can delay an
upstream parenting decision and no outgoing edge that can rescue one.

Before any relay scientific execution:

1. complete the AGENTS.md deliberation with at least two fresh interpretations,
   adversarial cross-critique, adjudicated concern-by-concern consensus, and
   exact human ratification of a replacement packet derived from these bytes;
2. verify actual `P0<R0<PU` receipts or permanently mark the relay exploratory;
3. implement only in a new namespace under separately ratified scope and pass
   byte/schema/compiler/carrier/writer/reader/reset/firewall/closure golden
   CPU fixtures, without touching a frozen one-parent packet;
4. seal text-first feasibility, complete control resource manifests, fixed
   interface/candidate and writer canaries, and the exact `N0` power receipt;
5. obtain a fresh rejection-capable independent review and a separate
   author-side scientific advocate over exact source, fixtures, manifests, and
   receipts; the advocate cannot override rejection; and
6. receive a separate exact human run/pre-GPU authorization. No green CPU,
   pilot, reviewer, or power receipt implies that authorization.

Any changed schema, compiler, outcome map, carrier transition, writer target,
reader history, controller class, signal/reachout boundary, D closure feature,
control, score, threshold, sample size, or claim requires a new deliberation.

## 13. B1--B10 closure ledger

| blocker | v3 single disposition |
|---|---|
| B1 | `P0<R0<PU` signed predecessor receipts; all design bytes and fixed N-grid/STOP rule at R0; rank-only blinded pilot; selected N ratified before A0; no confirmation-stage extension. |
| B2 | one strict JSONL ledger with `PUBLIC_EVENT`, `ATOM_PROPOSE`, `COUSE_PROPOSE`; total compiler inputs, chronology, public syntactic predicates, duplicate/conflict/failure law; minimal carrier rows only. |
| B3 | text and LoRA Phase C use immutable authentic A carriers; every D arm is a clean-base rebuild from the same old deck with one reserved semantic/pad slot; exact null projection and receipts. |
| B4 | five unambiguous B interventions; exact `V/PATH/Y`, connected, goal, cut, and redirection algebra; all necessary subsets/coupled RNG. |
| B5 | depth-four adaptive history DAG includes rows, misses/errors, timing class, repeats, stopping, and reacquisition; deterministic policies are exhaustive, randomized policies reduce by linearity, and one best policy per visibility mask is frozen on DEV before confirmation; fixed D slot semantics. |
| B6 | exact authentic/sham signal tuple and matcher/posterior; sham acts at signal return; reachout acts only at already-selected experiment dispatch with identical prefix/charges/world/target/RNG. |
| B7 | exact response-only examples, masking, clean rebuild, optimizer, transaction/rollback/hash law; supported previously uncarried sham row; literal 16-feature power-set plus adaptive-history closure. |
| B8 | every named text/LoRA/off/wrong-life/reader/oracle/link/bridge/write/binding/reachout control has construction, time, resource law, potential outcome, floor/ceiling, paired margin, and adverse failure value. |
| B9 | strict failure-inclusive same-root text/LoRA mediator products; `COMPLETE_chain_r` is their product; exact-binomial minima are `.60/.50/.40`. |
| B10 | exact binary/paired root reductions and CP bounds; IUT fixed sequence with no optional family; 75 decisions; rank-only 32-root nuisance pilot; exact marginal/union power plus mandatory 200,000-run rank-copula rule; final N selected from `[96..512]` and ratified before A0; no confirmation-stage extension. |

No B1--B10 architecture blocker remains in this candidate. Governance,
implementation evidence, actual lock/power/resource receipts, independent
review, and human execution authority remain intentionally unsatisfied.

## 14. Claim boundary

Only after an exactly ratified successor implements these choices, every gate
passes, and the complete fixed sequence through `BOTH-CH` passes may the relay
support:

> Conditional on one fixed parent-deleted child and the registered PCFL root
> distribution, authentic relations compiled from that child's own public
> actions were transported and used through its relay LoRA; fresh goals changed
> traversal, old memory changed a public information-seeking action, and the
> prospectively mapped public outcome, after a controlled semantic write,
> improved a later goal that required both named old and new experience.

This language is unavailable now. It does not imply compression, a readable
graph inside weights, parenting causality, another child, a classroom,
population learning, unbounded autonomy, universal continual improvement,
equal physical resources, or superiority to `ACTIVE_TEXT_FIXED`/R0.

## 15. Source read receipts

| source | SHA-256 read for this proposal |
|---|---|
| `AGENTS.md` | `1e3c413f3adbf172c409bc642bbf8242a736b0209461b6a7f81203450772f54e` |
| `research_notes/58_one_child_pcfl_relay_v2_executable_contract.md` | `20cad18ac51f1ff81b44a491ceabf609b53eaff3bc5af70d486fd42429a281d9` |
| `research_loop/advisory/20260907_one_child_pcfl_relay_v2_final_attack.md` | `5bea4603a67e6c2808f301578574c26616ca33c87a7b381ef1d91d8326f76042` |
| `research_loop/advisory/20260907_one_child_pcfl_relay_b9_b10_statistics_power_lock_v1.md` | `136dcf898de6fd97e850bd103bbbb3fee05a885effafa73ed61788c2b0709225` |
| `research_notes/DREAM_LORA_THINK_FULL_EVIDENCE_STACK_20260907.md` | `f50d9f4da29ff25ba3cb20ea59ac5cd912ad26854e2bab04e6cd4913662cc737` |
| `research_loop/plans/active_text_fixed_contract_v1.md` | `0fbb16b124f640c0adcecc46d2270a7ee11e6c63866885d56e3b0e3468ed09c7` |
| `research_loop/plans/one_parent_child_headline_v1.md` | `e356bcecc0cdec3199cf8ecb23c2dc9790a59a11ee6dc8f81b1bfd399c7cf4d5` |
| `research_loop/plans/one_parent_child_headline_v2_addendum.md` | `3c13492bb1378e07d966597efb9eb72f3c8742631a1e7ef1cb7b8977a5039cff` |
| `research_loop/plans/one_parent_child_headline_v2_diagnostic_resources_v0.md` | `422e124d1d3b6112f537dba4264f185f40a31888d91178a32e16778d8f84c35e` |
| `research_loop/plans/one_parent_child_headline_v3_spending_repair.md` | `632008a3306da4e09e6cfb73563f398aab5f6abf81e31b32de249ee177a81cd3` |

The SHA-256 of this proposal is reported externally after its final bytes are
written; it is not self-embedded.
