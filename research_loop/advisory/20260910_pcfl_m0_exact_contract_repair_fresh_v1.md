# PCFL M0-THIN exact CPU contract repair — fresh v1

Date: 2026-09-10  
Status: **source-only advisory; not ratified; no execution authority**

This document is a fresh repair proposal responding to
`cons_chg_20260910_pcfl_m0_mtext_bound_v2_rework_v1`. It authorizes no code
edit, fixture or root materialization, benchmark generation, CPU run, model or
tokenizer call, training, LoRA/adapter/checkpoint operation, parenting, GPU
use, scientific execution, claim, release, or submission. It is deliberately
limited to the model-free M0-THIN contract. M-TEXT and every learned component
remain separate future changes.

## 0. Ruling

Adopt one clean-room PCFL-specific finite instrument, `PCFL_M0_THIN_V3`.
Do **not** import or call FeltCraft V7. V7 remains cited design evidence only;
there is therefore no successor-authority transfer, oracle path, compatibility
witness, or runtime dependency to approve. This is less risky than attempting
to reuse a small amount of V7 code whose prior authority is terminal and whose
scope audit failed.

M0 has one meaning: approved CPU software either conforms to a completely
frozen finite specification or it does not. A green M0 receipt is not a model,
memory, DREAM, SLEEP, learning, LoRA, lifetime, compression, parenting, or
paper result.

The exact gate order is:

1. **S0 — source contract:** deliberate and ratify the semantic and
   preparation-source bytes. No preparation is run.
2. **P0 — deterministic preparation:** under separate permission, run the
   ratified no-choice materializer and two disjoint checkers. This creates a
   candidate 64-root fixture tree; it does not create scientific data.
3. **F0 — human byte freeze:** bind the resulting file manifest, manifest
   root, checker receipts, source hashes, and runtime identity. Only this step
   makes fixture bytes immutable.
4. **I0 — implementation:** separately authorize the M0 runtime against the
   F0 root.
5. **C0 — CPU conformance:** execute the implementation and acceptance suite;
   obtain independent implementation review and author-side claim review.
6. **H0 — semantic handoff:** freeze a model-free public-payload handoff. It
   does not authorize rendering or model use.
7. A later M-TEXT change must separately bind every renderer, tokenizer,
   chat-template, prompt, parser, session, provider, cache, resource,
   inference, confirmation, and claim choice before any model call.

No receipt can be required before the operation that produces it. No passage
automatically advances to the next gate.

## 1. Closed finite universe

### 1.1 Symbols and roots

The internal node set is exactly `N00..N1f`; the internal relation set is
exactly `R00..R0f`; the experiment set is exactly `E0..E3`; bit outcomes are
exactly `0,1`. No other internal symbol is legal.

The fixed role assignment is:

```text
N00=S   N01=X   N02=Y   N03=B   N04=C   N05=TA  N06=TB  N07=D
N08=H0  N09=H1  N0a=Z0  N0b=Z1 N0c=Q0  N0d=Q1  N0e..N1f=DECOY
```

These role labels are specification mnemonics and never occur in actor-visible
bytes.

The complete root universe is the Cartesian product
`K={0,...,31} x H={0,1}`: exactly 64 roots, ordered by increasing `k`, then
increasing `h`. Define `z(k)=popcount(k) mod 2`. The private root identifier is

```text
sha256("PCFL-M0-ROOT-v3\0" || JCS({"h":h,"k":k}))
```

and is never actor-visible. There is no seed, RNG, search, accepted candidate,
retry, ranking, replacement, or root rejection.

For root `(k,h)`, actor aliases are total bijections:

```text
alias_node(N_i) = "n" + lower_hex2(i XOR k)
alias_rel(R_j)  = "r" + lower_hex2(j XOR (k mod 16))
alias_exp(E_j)  = "e" + lower_hex1(j XOR (k mod 4))
```

Action IDs `c0`, `c1`, `finish`, and `abstain` are fixed across roots.
Specification arrays marked `PRESENTATION` are rotated left by
`k mod len(array)` exactly once. Arrays marked `SET` are sorted by semantic ID
and never rotated. No other ordering transform exists. Probe execution order
is A then B when `k` is even and B then A when `k` is odd; joined output is
always A then B.

For a fixed `k`, roots `(k,0)` and `(k,1)` are twins. Before an ordinary
outcome of a separating action, they have byte-identical actor-visible old
events, carriers, goals, catalogs, costs, padding, presentation, nuisance
state, phase schedule, and reset schedule. Only private `h` differs.

### 1.2 Transition facts and goals

The old transition facts are exactly:

```text
p0: S  -R00-> X       p1: X -R01-> B
p2: S  -R02-> Y       p3: Y -R03-> B
p4: B  -R04-> C       p5: C -R05-> TA
                      p6: C -R06-> TB
q0: Q0 -R0e-> N10     q1: Q1-R0f-> N11
```

Every relation action costs one. Legal paths are simple. The registered
minimum-cost path classes, and no others, are:

```text
A, S->TA: p0,p1,p4,p5 | p2,p3,p4,p5
B, S->TB: p0,p1,p4,p6 | p2,p3,p4,p6
D, S->D : p0,p1,p4,nh | p2,p3,p4,nh
```

The acquired fact is `nh: C -R(07+h)-> D`. It exists only after a correct
commit. Thus A and B are distinct, each requires four atoms, `p4` is a bridge
in every registered path, and D requires old facts plus the newly acquired
fact.

The full calibration table is public old evidence, expressed internally as
anchor-by-experiment outcome counts:

```text
       E0     E1     E2     E3
H0    [1,0]  [0,1]  [1,1]  [1,1]
H1    [0,1]  [1,0]  [1,1]  [1,1]
Z0    [1,1]  [1,1]  [1,0]  [0,1]
Z1    [1,1]  [1,1]  [0,1]  [1,0]
```

Concrete experiment outcomes are `E0=h`, `E1=1-h`, `E2=z`, and `E3=1-z`.
All use the same schema and cost. `E0,E1` separate `h`; `E2,E3` do not.

### 1.3 Exact old and new evidence schedule

Logical sequence numbers are part of semantic identity and never depend on
wall time or branch execution order:

```text
00..06  discovery occurrences p0..p6, in atom-number order
07..22  calibration records H0E0..H0E3,H1E0..H1E3,Z0E0..Z0E3,Z1E0..Z1E3
23..24  discovery occurrences q0,q1
-- REFERENCE_COMPILE_OLD cut --
25..31  validation occurrences p0..p6, in atom-number order
32..35  probe A ordinary event slots
36..39  probe B ordinary event slots
40      chosen experiment outcome, if any
41      commit outcome, if any
-- REFERENCE_COMPILE_NEW cut --
42      new validation occurrence p4, if a commit occurred
43      new validation occurrence nh, iff acquisition succeeded
44..47  delayed-goal ordinary event slots
```

Calibration is one typed `CALIBRATION` event containing counts, not an
invented sample. Unused logical slots are absent from the public event DAG and
appear only as typed PAD slots in fixed branch/join receipts. Event IDs are
derived from logical location and aliased public payload, never from private
root ID or `h`:

```text
event_id = sha256("PCFL-M0-EVENT-v3\0" || JCS({location,payload}))
```

Consequently pre-separation twin event IDs are identical.

## 2. Canonical encoding and identities

All wire objects are closed JSON objects. Missing, extra, duplicate,
mistyped, out-of-range, non-NFC, BOM-prefixed, floating-point, or
non-round-tripping input rejects. Integers are unsigned and at most
`2^53-1`. Canonical bytes are RFC-8785/JCS UTF-8 with no BOM, surrounding
whitespace, or final newline.

Every schema below contains `v:3` and `pad:string`. Padding is deterministic:
set `pad=""`, JCS-encode, require length at most `B`, set `pad` to exactly
`B-len(encoded)` ASCII underscores, JCS-encode again, and require exact length
`B`; otherwise reject. Fixed bounds are:

```text
Goal 512              Handle 256             Atom 1024
Link 1024             PublicEvent 1024       TransitionRow 2048
ProbeSlot 2048        MemoryReturn 4096       Uncertainty 8192
GoalsComplete 8192    Carrier 65536          FiniteView 131072
CommandResult 135168  HandoffPublic 262144
```

Nested objects retain their own padding. A wire digest is
`sha256(type_ascii || 0x00 || padded_bytes)`. Padding is excluded from the
semantic-key functions below but included in wire digests.

IDs are not hashes of mutable evidence/status fields:

```text
atom_id = sha256("PCFL-M0-ATOM-v3\0" || JCS({kind,src,rel,dst,experiment,
                                             outcome_counts}))
link_id = sha256("PCFL-M0-LINK-v3\0" || JCS({left_atom_id,right_atom_id}))
row_id  = sha256("PCFL-M0-ROW-v3\0"  || JCS({src,via,dst,atom_ids}))
```

Thus adding an independent evidence root or changing a private support state
does not rename a semantic fact. A transformed fact with changed content does
receive a new ID.

### 2.1 Closed public types

```text
Goal := {
  v:3, goal_id:"A"|"B"|"D", start:node_alias, target:node_alias, pad:string
}

Handle := {
  v:3, kind:"NODE"|"ATOM"|"LINK", id:node_alias|hex64, pad:string
}

Atom := {
  v:3, atom_id:hex64, kind:"STEP"|"PREDICT"|"NULL",
  src:null|node_alias, rel:null|relation_alias, dst:null|node_alias,
  experiment:null|experiment_alias,
  outcome_counts:null|[u8,u8], evidence_ids:[hex64], pad:string
}

Link := {
  v:3, link_id:hex64, status:"AUTH"|"EMPTY"|"NULL"|"REVOKED",
  left:null|hex64, right:null|hex64, evidence_ids:[hex64], pad:string
}

PublicEvent := {
  v:3, event_id:hex64, seq:u16, location:closed_location_enum,
  action:relation_alias|experiment_alias|"c0"|"c1"|"calibration",
  before:node_alias,
  outcome:{kind:"NODE"|"BIT"|"CALIBRATION"|"ACQUIRED"|"MISS",
           value:node_alias|0|1|[u8,u8]|
                 {src:node_alias,rel:relation_alias,dst:node_alias}|null},
  after:node_alias, evidence:boolean, pad:string
}

TransitionRow := {
  v:3, row_id:hex64, src:node_alias, via:[relation_alias,relation_alias],
  dst:node_alias, atom_ids:[hex64,hex64], evidence_ids:[hex64], pad:string
}

MemoryReturn := {
  v:3, status:"FOUND"|"NOT_FOUND"|"BLOCKED", fingerprint:hex64,
  anchor:Handle, cursor:u8, item_kind:"ATOM"|"LINK"|"NULL",
  atom:null|Atom, link:null|Link, repeat_count:1|2|3, pad:string
}

Uncertainty := {
  v:3, anchors:[Handle,Handle], prior_counts:[1,1],
  candidates:[{
    action:experiment_alias, cost:1,
    outcome_anchor_counts:[[u8,u8],[u8,u8]], citations:[hex64,hex64]
  },{...},{...},{...}],
  observed:null|{action:experiment_alias,outcome:0|1,
                  posterior_anchor_counts:[u8,u8]}, pad:string
}

ProbeSlot := {v:3,kind:"EVENT"|"PAD",event:null|PublicEvent,pad:string}

GoalsComplete := {
  v:3, type:"GOALS_COMPLETE",
  probes:[
    {probe:"A",goal:Goal,terminal:"SUCCESS"|"ABSTAIN"|"BUDGET",
     events:[ProbeSlot,ProbeSlot,ProbeSlot,ProbeSlot]},
    {probe:"B",goal:Goal,terminal:"SUCCESS"|"ABSTAIN"|"BUDGET",
     events:[ProbeSlot,ProbeSlot,ProbeSlot,ProbeSlot]}
  ], pad:string
}
```

`closed_location_enum` is exactly the logical labels in section 1.3. A STEP
atom has non-null `src,rel,dst`; a PREDICT atom has non-null
`src,rel,experiment,outcome_counts` and null `dst`; a NULL atom has all
semantic fields null and an empty evidence list. Evidence lists are SET arrays
sorted by event ID. An AUTH/EMPTY link has two non-null endpoints; a NULL link
has null endpoints; REVOKED is never in an authentic readable carrier but is
available in provenance receipts and expected-reject fixtures.
NODE events carry their destination alias, BIT events carry one bit,
CALIBRATION events carry counts, ACQUIRED carries the complete public
`{src,rel,dst}` FactKey for `nh`, and MISS carries null. This is the only rule
that turns the commit event into a candidate new STEP fact; no private field is
consulted after the public event is formed.

### 2.2 Carrier and handoff types

Every carrier is a closed record with exactly 26 atom slots and seven link
slots:

```text
Carrier := {
  v:3, cut:"OLD"|"NEW"|"DELAYED",
  atoms:[Atom x 26], links:[Link x 7],
  exposure:{atom_slots:26,link_slots:7,read_cost:1,action_cost:1}, pad:string
}
```

Authentic atom slot order is `p0..p6`, the 16 calibration atoms in the
sequence order above, `q0,q1`, then `nh-or-NULL`. Authentic link slot order is

```text
0 (p0,p1)  1 (p2,p3)  2 (p1,p4)  3 (p3,p4)
4 (p4,p5)  5 (p4,p6)  6 (p4,nh)-or-NULL
```

`HandoffPublic` is the only M0 output a future renderer may consume:

```text
HandoffPublic := {
  v:3, instrument:"PCFL_M0_THIN_V3", instrument_contract_digest:hex64,
  fixture_manifest_root:hex64,
  semantic_cut:"OLD"|"NEW"|"DELAYED", carrier:Carrier,
  initial_view:FiniteView, allowed_command_schemas:["READ","ACT","FINISH",
  "ABSTAIN"], public_payload_digest:hex64, pad:string
}
```

`public_payload_digest` is computed by setting that field to 64 ASCII zeroes,
padding and encoding the object, hashing
`"PCFL-M0-HANDOFF-v3\0" || bytes`, then replacing the zeroes with the digest
and repadding. Strict verification repeats that procedure.

The enclosing nonpublic receipt contains root ID, transform ID, expected
scores, and HandoffPublic wire digest. None of those private fields may enter
`HandoffPublic`. M0 defines no prose, prompt, renderer, tokenizer, parser,
model, provider, session, transcript, KV/cache, retry, or resource envelope.
A later M-TEXT packet must bind those bytes and prove rendered
noninterference; it may not mutate this semantic payload.

## 3. Commands, reader, and actor-visible state

The command union is exact:

```text
READ    {v:3,op:"READ",anchor:Handle,cursor:u8,deps:[]}
ACT     {v:3,op:"ACT",action_id:relation_alias|experiment_alias|"c0"|"c1",
         deps:[hex64]}
FINISH  {v:3,op:"FINISH",deps:[hex64]}
ABSTAIN {v:3,op:"ABSTAIN",
         reason:"NO_PATH"|"NO_TARGET_INFO"|"BUDGET_GUARD"}
```

`cursor` is `0..7`. `deps` is a SET array of distinct earlier public atom or
link IDs returned in the same branch; it may not cite commands, future items,
sibling branches, joined state, or private objects.

The complete readable index is constructed from carrier bytes before any
goal is revealed. It receives no root ID, `h`, `z`, goal, phase schedule,
probe order, arm/transform label, score, future event, command history, or
receipt. Index keys and candidate lists are:

```text
NODE a -> all non-NULL atoms with src==a or dst==a
ATOM x -> all non-NULL links with left==x or right==x
LINK y -> the two endpoint atoms of y
```

Candidates are sorted by semantic ID. `cursor=i` returns candidate `i`, or
NOT_FOUND if absent. A REACHOUT_OFF transformed dispatch returns BLOCKED for
an ATOM-to-LINK query and is otherwise identical. No fuzzy search, implicit
query builder, ranking, embedding, hidden catalog, fallback, or callback
exists.

The actor-visible catalog is a fixed 64-slot PRESENTATION array of
`Handle|null`. Its non-null members are exactly the distinct union of current
state, visible goal endpoints, visible uncertainty anchors, and atom/link IDs
returned earlier in the same branch. If more than 64 would be required, the
command causing overflow returns BUDGET and does not add an item. A READ
anchor must byte-equal a non-null catalog member. An unknown, internal, future,
or sibling handle is PRIVATE_HANDLE; unreturned carrier identities are not
capabilities.

```text
FiniteView := {
  v:3,
  phase:"PROBE_A"|"PROBE_B"|"UNCERTAINTY"|"ACQUIRE"|"DELAYED_GOAL"|"FINAL",
  state:node_alias, goal:null|Goal,
  legal_actions:[public_action_id],
  last_event:null|PublicEvent, uncertainty:null|Uncertainty,
  memory:null|MemoryReturn, joined:null|GoalsComplete,
  catalog:[Handle|null x 64], workspace:[hex64|null x 32],
  repeat:{fingerprint:null|hex64,count:0|1|2|3,limit:2,
          blocked:boolean,last_reset:"ROOT_START"|"PROBE_FORK"|
          "GOALS_JOIN"|"POST_COMPILE"|"DELAYED_RESET"},
  budget:{reads_remaining:u8,actions_remaining:u8}, pad:string
}

CommandResult := {
  v:3,status:"OK"|"NOT_FOUND"|"BLOCKED"|"ABSTAIN"|"ERROR",
  failure:"NONE"|closed_failure_code, advanced:boolean,
  result_event:null|PublicEvent, view:FiniteView, pad:string
}
```

`legal_actions` is a sorted complete SET of relation/experiment/commit action
IDs currently legal. `finish` is included only at the goal target; `abstain`
is always present in actor phases. READ is legal iff reads remain. `workspace`
is insertion order of distinct returned object IDs, padded with nulls.
Catalog construction is deterministic after every command: sort the distinct
legal Handles by `(kind,id)`, rotate that non-null sequence left by
`k mod count` when count is nonzero, then append nulls to 64 slots. Previously
returned handles never become legal merely because they occur in immutable
carrier bytes; they enter the catalog only through an actual FOUND return.

## 4. Closed controller and transition precedence

The automatic controller phase order is:

```text
OLD_DISCOVERY -> REFERENCE_COMPILE_OLD -> OLD_VALIDATION -> RENDER_OLD
-> fork PROBE_A / PROBE_B from the same immutable OLD checkpoint
-> GOALS_JOIN -> UNCERTAINTY -> ACQUIRE
-> REFERENCE_COMPILE_NEW -> NEW_VALIDATION -> RENDER_NEW
-> DELAYED_RESET -> DELAYED_GOAL -> FINAL
```

The actor-dispatch table is closed:

| Phase | Command | Additional precondition | Atomic effect | Next phase |
|---|---|---|---|---|
| PROBE_A/B, DELAYED_GOAL | READ | reads > 0; catalog anchor | consume one read on first dispatch; set `memory`; on FOUND add distinct item ID to workspace/catalog; set no event | same |
| PROBE_A/B, DELAYED_GOAL | ACT relation | action in legal set; actions > 0 | consume one action; emit assigned slot event; move state; clear `memory` | same, or BUDGET terminal after the fourth non-goal state |
| PROBE_A/B, DELAYED_GOAL | FINISH | state equals visible target | mark SUCCESS; clear repeat/cache; emit no event | branch closed or FINAL |
| any actor phase | ABSTAIN | none | mark ABSTAIN; clear repeat/cache; emit no event | branch closed or next automatic phase |
| UNCERTAINTY | READ | reads > 0; catalog anchor | same READ rule | UNCERTAINTY |
| UNCERTAINTY | ACT experiment | action in legal set; actions=1 | consume action; emit seq-40 BIT; populate observed posterior; clear `memory` | ACQUIRE |
| ACQUIRE | READ | reads > 0; catalog anchor | same READ rule | ACQUIRE |
| ACQUIRE | ACT c0/c1 | action in legal set; actions=1 | consume action; emit seq-41 ACQUIRED or MISS; clear `memory` | REFERENCE_COMPILE_NEW |

Any op/phase pair not in the table fails PHASE before semantic dispatch.
For READ, NOT_FOUND and REACHOUT_OFF/BLOCKED are response statuses, consume
one read on their first dispatch, add nothing to workspace/catalog, and set
`memory` to the fixed-size return. The second identical replay consumes
nothing; the third is REPEAT_BLOCKED. A non-READ command always sets `memory`
to null. `last_event` is the latest ordinary event in the current branch and
changes only on a successful ACT. A reset sets it null. `joined` is null in
the probes, equals canonical GoalsComplete in UNCERTAINTY and ACQUIRE, and is
cleared at POST_COMPILE.

The two probe forks execute serially in the root's registered order but cannot
read or write one another. Each starts at S with 32 READs and four relation
ACTs. A legal relation ACT exists iff an authentic world fact has current
`src` and the requested relation; it consumes one action, moves to `dst`, and
emits its fixed-slot ordinary event. Reaching the visible target makes FINISH
legal. FINISH is uncharged and succeeds only at target. ABSTAIN closes the
branch. If a fourth ACT leaves the actor away from target, the branch closes
as BUDGET. Wrong but schema-legal relation actions are ILLEGAL_ACTION, consume
no semantic progress, and invalidate the root.

After both branches close, GOALS_JOIN restores the OLD trunk checkpoint and
appends only the canonical `GoalsComplete` object. It starts UNCERTAINTY at S
with 32 reads and one experiment ACT. A legal experiment consumes that ACT,
emits the sequence-40 BIT event, and transitions to ACQUIRE with the posterior
shown in `Uncertainty.observed` and one commit ACT. ABSTAIN skips acquisition.
A legal `c0` or `c1` emits sequence 41; it yields ACQUIRED and admits `nh` iff
the chosen bit equals `h`, otherwise MISS and no new atom. It does not move the
actor state. ABSTAIN admits nothing.

REFERENCE_COMPILE_NEW then runs over admitted public evidence. If any commit
occurred, NEW_VALIDATION emits fresh p4 at sequence 42; if acquisition
succeeded it also emits fresh nh at sequence 43. RENDER_NEW renders supported
state only. DELAYED_RESET starts S, reveals goal D, retains admitted old and
new carrier state, and grants 32 READs and four relation ACTs. Its command
rules match a probe. FINAL emits one root receipt and accepts no command.

The 19 registered control cells are not serialized through one mutable actor.
The materializer freezes four immutable checkpoints per root: OLD before any
probe, JOIN after the two AUTH reference probes, ACQUIRED after authentic cue
and correct commit, and DELAYED after new support. Each PATH cell is an
isolated fork of OLD with its named carrier transform and goal. Both AUTH
reference probes alone produce JOIN. Each CUE cell is an isolated fork of JOIN.
DELAYED cells are isolated forks of DELAYED, which is descended only from the
AUTH cue/acquisition path. A cell cannot write a sibling checkpoint, and its
events, retrievals, repeat state, failures, and scores never become another
cell's input. This preserves one environment-root reducer unit while making
the interventions causally well-defined.

### 4.1 Command failure precedence

For every command, the first matching condition wins; lower conditions are
not evaluated and no partial mutation is committed:

1. bytes cannot strict-parse/canonical-round-trip -> `MALFORMED`;
2. required frozen artifact missing or digest mismatch -> `MISSING_ARTIFACT`;
3. controller already FINAL or op unavailable in phase -> `PHASE`;
4. READ anchor is not a current catalog capability, or deps cite a forbidden
   object -> `PRIVATE_HANDLE`;
5. the exact same non-advancing command has already been served twice ->
   `REPEAT_BLOCKED`;
6. relevant read/action budget is zero -> `BUDGET`;
7. action ID is not in the exact legal set, FINISH is premature, or deps are
   not chronologically earlier -> `ILLEGAL_ACTION`;
8. dispatch/transition invariant fails -> `INTERNAL_ERROR`;
9. otherwise execute and atomically commit.

Closed failure codes are:

```text
ABSTAIN BUDGET ILLEGAL_ACTION MALFORMED MISSING_ARTIFACT PHASE
PRIVATE_HANDLE REPEAT_BLOCKED PROVENANCE_REJECT SUPPORT_REJECT INTERNAL_ERROR
```

ABSTAIN, BUDGET, REPEAT_BLOCKED, and a correctly expected SUPPORT_REJECT are
registered adverse outcomes and occupy their cells with unfinished metrics
zero. ILLEGAL_ACTION, MALFORMED, MISSING_ARTIFACT, PHASE, PRIVATE_HANDLE, or
PROVENANCE_REJECT invalidate that root. INTERNAL_ERROR invalidates the entire
suite. An expected-reject unit fixture passes only by returning its registered
code and unchanged pre-state; it never turns that code into a valid main-root
outcome.

## 5. Repeat, fork, join, and reset laws

The command fingerprint is

```text
sha256("PCFL-M0-CMD-v3\0" || JCS(command))
```

Repeat state applies only when the preceding command produced no
non-idempotent public progress. The first exact command is dispatched and its
semantic payload cached; a second consecutive copy returns the same payload
with repeat count two, consumes no additional budget, and creates no event or
evidence; a third returns BLOCKED/count three without index or environment
dispatch. A different command, successful relation/experiment/commit ACT,
successful FINISH, or any reset clears fingerprint, cache, and count. A
failed or NOT_FOUND command does not clear them. This makes a lost-response
replay idempotent without creating evidence.

Reset retention is exact:

| Boundary | Retained | Destroyed |
|---|---|---|
| ROOT_START | frozen root spec, old public evidence/carrier | all volatile state |
| PROBE_FORK | immutable OLD checkpoint and carrier | branch log, catalog additions, workspace, query cache, repeat state, deps |
| GOALS_JOIN | OLD checkpoint/carrier plus canonical GoalsComplete only | both complete branch transcripts except joined allowlist, execution order, sibling handles, correctness, scores, failures, paths, timings |
| POST_COMPILE | old plus admitted new public evidence and carrier | query cache, repeat state, transient compiler workspace |
| DELAYED_RESET | old plus admitted new evidence/carrier only | raw command history, retrieved returns, catalog additions, workspace, deps, branch traces, provider/session/cache state (none exists in M0) |

The exact GOALS_JOIN allowlist is the public Goal, terminal enum, and four
fixed `ProbeSlot`s for A followed by B. Injection of any command text,
retrieval, workspace, dependency, repeat, hidden correctness, path
certificate, score, failure detail, wall time, execution order, padding
channel, or sibling handle causes the join object to reject. Goal and ordinary
public action/outcome bytes intentionally survive; nothing else does.

## 6. Prefix noninterference and taint

For twins `(k,0)` and `(k,1)`, replay the same legal public command bytes. The
pre-dispatch FiniteView and command-acceptance decision must be identical until
the ordinary public outcome of the first separating action in
`{E0,E1,c0,c1}`; the CommandResult containing that ordinary outcome may first
differ. `E2,E3` cannot immediately separate twins. After a
separating outcome, a differing actor-visible field is legal only if the
controller's public taint DAG contains a path from that exact outcome event to
the field.

The only taint-generating sources are ordinary public event fields. Private
`h`, root ID, `z`, future goal, arm/transform ID, expected answer, score,
golden, receipt, file path, error detail, timing, runtime identity, and test
order are forbidden sources. Mutating each forbidden source either leaves all
pre-entitlement public bytes unchanged or makes the private fixture fail
preflight; it can never silently alter a view. Transform-induced differences
may first appear only in the exact transformed carrier field or registered
reader dispatch result after the actor reaches it.

## 7. Provenance, support, revocation, and reference compilation

M0 evidence nodes are exactly:

```text
ROOT  {kind:"ROOT",event_id:hex64,seq:u16,payload_digest:hex64}
SYNTH {kind:"SYNTH",synth_kind:"PAIR_PROPOSAL"|"REEXPRESSION",
       seq:u16,payload_digest:hex64,parent_ids:[hex64]}
ALIAS {kind:"ALIAS",source_id:hex64,target_id:hex64}
```

Node ID is the tagged JCS hash of all fields except its own ID. ROOT may be
created only from an admitted evidence=true PublicEvent. SYNTH adds no
evidential root. Main fixtures contain no aliases; aliases exist only in the
conformance suite.

Alias preprocessing is exact: require every source and target to exist;
require `target_id < source_id` lexicographically; process sources in ascending
order, following targets to a non-ALIAS node; reject self-reference, unknown
targets, multiple targets for one source, or any cycle; replace every citation
by its resolved sink before chronology, cycle, and root-set checks. This order
is the only alias-collapse rule.

All parent edges point from a SYNTH node to strictly earlier sequence nodes.
Unknown, self, same-sequence, or forward parents reject. After alias collapse,
a directed cycle rejects. A node's evidential-root set is the SET union of its
primitive ROOT ancestors; a shared-root diamond is legal and the root counts
once. A SYNTH object offered as a primitive root rejects.

`REFERENCE_COMPILE_{OLD,NEW}_V3` is a deterministic conformance compiler, not
an agent, child, DREAM, or learned writer. At its cut it receives only the
admitted public provenance DAG as of that sequence. In atom-ID order, it emits
one pending pair proposal for every and only distinct STEP-atom pair `(a,b)`
with `a.dst==b.src`, excluding an already proposed or permanently revoked
pair. Proposal parents are the then-current primitive discovery roots of `a`
and `b`. It receives no goal, future schedule, root ID, `h`, `z`, arm,
transform, oracle, expected path, score, or command history.

A proposal becomes SUPPORTED only if all conditions hold:

1. both endpoints are STEP facts and composition is exact;
2. the proposal existed before validation;
3. after proposal sequence, at least one newly admitted ROOT independently
   repeats each exact endpoint FactKey;
4. each validation-root set is disjoint from the proposal's evidential-root
   set; and
5. no accepted contradiction exists.

The AUTH Link evidence list is the sorted union of proposal discovery and
later validation roots. Its TransitionRow is the exact two-step composition.
Insufficient, reused, synthetic-only, noncomposable, or prematurely cited
support returns SUPPORT_REJECT and admits neither Link nor Row.

A contradiction is an admitted later STEP root with the same `(src,rel)` and
a different `dst`. Events are applied in increasing `(seq,event_id)` order.
Bad provenance rejects the whole candidate batch before any mutation. For a
valid batch, contradiction permanently changes every proposal depending on
that FactKey to REVOKED. Revocation has precedence over support at the same
or later cut and cannot be repaired by more matching evidence. An identical
repeat is corroboration, not contradiction. RENDER validates and serializes
SUPPORTED items only; it cannot propose, support, repair, or un-revoke.

At OLD cut the authentic supported links are slots 0..5. At NEW cut, if nh
was acquired, p4 and nh are revalidated after the proposal and slot 6 becomes
supported. If nh was not acquired, slot 6 remains NULL. These rules are
relation-specific and exhaustive.

## 8. Pure carrier interventions

Interventions apply **after** authentic support/rendering. They never enter
the provenance store, never masquerade as newly supported memories, and are
identified only in a private transform receipt. Public schemas, slot counts,
padding bounds, catalogs, budgets, and costs remain unchanged.

Transforms are total and exact:

- `AUTH`: identity.
- `ATOMS`: replace every Link slot with canonical NULL.
- `TRUTHFUL_NULL`: preserve AUTH endpoint pairs and link IDs but set status
  EMPTY and evidence list empty; an endpoint query may return the explicit
  EMPTY statement.
- `DERANGED`: replace slots 0..5 by public-status AUTH links for pairs
  `(p0,p4),(p2,p4),(p1,p5),(p3,p6),(p4,p1),(p4,p3)`; recompute link IDs and
  use the sorted union of endpoint evidence IDs. These pairs are deliberately
  noncomposable and would fail re-admission; intervention output is never
  re-admitted. Slot 6 retains its cut-appropriate NULL/new value.
- `BRIDGE_CUT`: replace slots 2,3,4,5 (every old link incident to p4) with
  canonical NULL; retain slots 0,1 and cut-appropriate slot 6.
- `BINDING_TWIN`: clone atom p5 with destination TB and p6 with destination
  TA, recompute those two atom IDs, and update link slots 4 and 5 to cite the
  cloned IDs. Preserve their evidence lists exactly, making the false binding
  detectable to the private checker but not by a transform label. No other
  atom or link changes.
- `UNCERTAINTY_SHAM`: carrier bytes equal AUTH; replace public uncertainty
  anchors H0/H1 and their candidate citations/counts with Z0/Z1 equivalents.
- `REACHOUT_OFF`: bytes equal AUTH; only ATOM-to-LINK READ dispatch returns
  BLOCKED.
- `OLD_CUT`: at delayed evaluation replace link slots 0..5 with NULL and
  retain slot 6.
- `NEW_CUT`: at delayed evaluation retain slots 0..5 and replace slot 6 with
  NULL.

For each transform, an allowlist enumerates the exact JSON pointers above.
The transform test compares canonical decoded trees and fails if any other
pointer or any fixed exposure field changes. `BINDING_TWIN` is a carrier
binding counterfactual, not the `(k,0)/(k,1)` private-world twin.

## 9. Deterministic reference traces and scores

Reference scripts exist only to prove the CPU instrument. They are not models
or scientific baselines.

`SCRIPT_PATH_V3` uses only FiniteView, legal commands, and returned objects.
It enumerates READ cursors and performs depth-first graph search in public
semantic-ID order. A candidate edge is usable only when the STEP atoms and
every adjacent AUTH link were actually returned. It chooses the first complete
minimum-cost path to the visible target, emits relation ACTs in path order,
and cites the corresponding returned atom and adjacent-link IDs. If no such
path is visible after exhaustive cursor traversal within 32 reads, it
ABSTAINS. It never reads the private path
table.

`SCRIPT_CUE_V3` reads only public Uncertainty. For each candidate action and
outcome it normalizes the displayed anchor counts, chooses an experiment that
minimizes expected posterior anchor entropy, and breaks ties by public action
ID. It commits `c0/c1` only when the displayed anchor posterior is singleton;
otherwise it ABSTAINS. It has no private knowledge of whether anchors encode
H or nuisance Z.

Scores are separate bits; no averaging or substitution is permitted:

- `answer`: terminal public state equals visible goal target.
- `constructive_path`: accepted ACT order matches one registered path class
  and each ACT deps-cites all path atoms plus all adjacent AUTH links.
- `all_path_mask_dependence`: masking the union of atoms and links in **all**
  legal path classes makes the fixed script fail construction or abstain.
- `binding_counterfactual_change`: replacing AUTH by BINDING_TWIN under the
  same pre-read prefix changes the decisive terminal relation action.
- `shortcut_free`: both previous counterfactuals hold.
- `experiment_choice`: selected internal action is E0 or E1.
- `realized_target_information`: the true posterior projection onto `h` after
  the observed experiment is singleton.
- `raw_acquired`: commit happens to equal `h` and ACQUIRED is emitted.
- `acquisition_credit`: `raw_acquired AND realized_target_information`.
- `raw_delayed`: delayed goal is actually reached.
- `delayed_credit`: `raw_delayed AND acquisition_credit AND
  constructive_path`.

The distinction between raw and credited outcomes repairs an impossibility in
the prior draft: a Z-sham guess is accidentally correct on 32 of 64 roots.
Those roots must report `raw_acquired=1` (and may report `raw_delayed=1`) while
`realized_target_information=acquisition_credit=delayed_credit=0`. Chance
success is preserved rather than silently rewritten as failure.

## 10. Exact registered cells and expected vector

Every root receipt contains these 19 cells exactly once, in this order:

```text
PATH:A:AUTH PATH:A:ATOMS PATH:A:TRUTHFUL_NULL PATH:A:DERANGED
PATH:A:BRIDGE_CUT PATH:A:BINDING_TWIN PATH:A:REACHOUT_OFF
PATH:B:AUTH PATH:B:ATOMS PATH:B:TRUTHFUL_NULL PATH:B:DERANGED
PATH:B:BRIDGE_CUT PATH:B:BINDING_TWIN PATH:B:REACHOUT_OFF
CUE:AUTH CUE:UNCERTAINTY_SHAM
DELAYED:AUTH DELAYED:OLD_CUT DELAYED:NEW_CUT
```

For both AUTH path cells:
`answer=constructive_path=all_path_mask_dependence=`
`binding_counterfactual_change=shortcut_free=1`. All cue/delayed fields are
zero. For each BINDING_TWIN path cell, only
`binding_counterfactual_change=1`; answer, construction, and shortcut_free are
zero because shortcut_free is defined on the AUTH trace and its paired
counterfactual, not recursively on an already transformed trace. For ATOMS,
TRUTHFUL_NULL, DERANGED, BRIDGE_CUT, and REACHOUT_OFF path
cells all behavioral bits are zero because the fixed script abstains or
cannot construct a valid linked trace.

For CUE:AUTH,
`experiment_choice=realized_target_information=raw_acquired=`
`acquisition_credit=1`; other bits are zero. For CUE:UNCERTAINTY_SHAM,
`experiment_choice=realized_target_information=acquisition_credit=0`,
`raw_acquired=1 iff z==h`, and all other bits are zero.

For DELAYED:AUTH, when AUTH acquisition preceded it,
`answer=constructive_path=raw_delayed=delayed_credit=1`. For OLD_CUT and
NEW_CUT, those four bits are zero. Other bits are zero. Separate root-level
invariants `manifest,prefix,join,repeat_reset,provenance,transform_specificity`
must all be one.

If a registered adverse terminal occurs, the cell remains present with its
terminal/failure code and every unfinished bit zero. No cell may be dropped,
rerun, replaced, or averaged away.

## 11. Root receipt and reducer

```text
CellReceipt := {
  v:3,cell_id:registered_cell_enum,
  terminal:"SUCCESS"|"ABSTAIN"|"BUDGET"|"BLOCKED"|"INVALID",
  failure:closed_failure_code|"NONE",
  bits:{answer:0|1,constructive_path:0|1,all_path_mask_dependence:0|1,
        binding_counterfactual_change:0|1,shortcut_free:0|1,
        experiment_choice:0|1,realized_target_information:0|1,
        raw_acquired:0|1,acquisition_credit:0|1,
        raw_delayed:0|1,delayed_credit:0|1},
  trace_digest:hex64
}

RootReceipt := {
  v:3,instrument_contract_digest:hex64,fixture_manifest_root:hex64,
  root_id:hex64,state:"FINAL",
  cells:[CellReceipt x 19],
  invariants:{manifest:0|1,prefix:0|1,join:0|1,repeat_reset:0|1,
              provenance:0|1,transform_specificity:0|1},
  public_handoff_digests:[hex64 x 19],receipt_digest:hex64
}
```

`receipt_digest` hashes the record with that field temporarily set to 64 zero
characters. `reduce_m0_v3` accepts exactly one canonical RootReceipt for each
of the 64 frozen root IDs. Receipt array order is the frozen `(k,h)` order and
cell order is section 10. Missing, duplicate, foreign, reordered,
noncanonical, wrong-manifest, wrong-cell, non-FINAL, digest-mismatched, or
schema-invalid input fails the suite before scoring. Nested goals, paths,
calls, branches, events, aliases, interventions, reruns, and cells never
increase `N`; M0's engineering root count is exactly 64 and is not a later
scientific sample-size claim.

A root conforms only if every cell equals its root-specific expected vector,
every invariant is one, and no invalidating failure occurred. Suite passage
is Boolean AND across all 64 roots. There is no mean, margin, retry,
replacement, conditional stop, missingness rule, favorable subset, or
promotion on partial passage. Reproducibility reruns must be byte-identical
and are not additional roots.

## 12. Deterministic materialization and durable freeze

The finite semantics contain no discretionary selection, but exact fixture
bytes still must exist before runtime implementation. P0 preparation is a
separate authorized operation with this closed output tree:

```text
pcfl_m0_frozen/<manifest_root>/
  contract.json
  schemas/<type>.schema.json
  transitions/controller_table.json
  roots/00-0.json ... roots/31-1.json
  roots/<root>/events.json
  roots/<root>/carriers/<cut>-<transform>.json
  roots/<root>/expected_vector.json
  rejects/<fixture_id>.json
  handoff/handoff_schema.json
  manifest_entries.json

pcfl_m0_attestations/<manifest_root>/
  checker_a_receipt.json
  checker_b_receipt.json
  PREPARATION_RECEIPT.json
```

Paths are ASCII and lexicographically sorted. File bytes are JCS with no final
newline. `manifest_entries.json` contains `{path,sha256,length}` for every
immutable fixture file except itself. The manifest root is

```text
sha256("PCFL-M0-MANIFEST-v3\0" || JCS(manifest_entries))
```

Checker A is constructive: it independently enumerates the algebra, roots,
events, carriers, and expected vectors from the frozen contract. Checker B is
predicate-based: it imports neither materializer nor Checker A, reads only
candidate bytes plus separately frozen schemas/transition predicates, and
checks all algebraic, state, visibility, provenance, intervention, and
expected-vector invariants. The two implementations must have disjoint source
files and no imports from each other. Agreement is described as reproducible
construction plus independent invariant checking—not proof that the shared
human specification is true. A mutation bank must demonstrate that Checker B
rejects at least one mutation of every semantic field and every accepted
concern class.

P0 has no CLI choice other than an empty staging destination. It refuses any
existing nonempty destination and has no seed, filter, range, root selector,
retry, overwrite, resume-as-success, model/tokenizer/network call, or
performance-dependent branch. Each file is created exclusively, fsynced, and
verified; the staging directory is fsynced. Both checkers run against that
tree and write receipts into a separate attestation staging directory. Any
crash leaves a non-authoritative staging tree.

Promotion to frozen storage is a single atomic rename to the computed
manifest-root directory after both checkers pass. If that destination exists,
every byte must already match or the operation fails; nothing overwrites it.
Checker and preparation receipts are then atomically placed in the separate
attestation directory and bind the already immutable root; timestamps and
runtime metadata therefore cannot change fixture identity. `CURRENT`,
symlinks, mtimes, permissions, filenames outside the manifest, and latest-run
conventions confer no authority. Every consumer names the exact manifest root
and rehashes every file. Duplicate preparation yielding the same root is
reproducibility evidence only. Partial, malformed, or digest-mismatched output
is never loadable.

PREPARATION_RECEIPT binds contract hash, materializer source hash, Checker A
and B source hashes, mutation-bank hash, executable/runtime identity, OS and
stdlib identities, manifest root, start/end monotonic timestamps, and exit
status. Runtime identity is audit metadata, not an outcome-dependent gate;
canonical fixture identity is the manifest root. F0 requires a new explicit
human approval naming the exact manifest root before I0.

No immutable fixture file contains `fixture_manifest_root`; that would make
the manifest self-referential. `expected_vector.json` contains root ID, cell
vectors, and invariants only. At runtime the loader receives the separately
ratified manifest root, rehashes the tree, and places it into RootReceipt and
HandoffPublic outputs. Their digests are execution outputs, not inputs to the
fixture manifest. `instrument_contract_digest` is the ordinary SHA-256 of the
already frozen `contract.json` bytes and is safe to embed in fixture records.

## 13. CPU acceptance suite

After F0 and separately authorized implementation, C0 runs these exhaustive
tests over all 64 roots and all named variants; sampling is forbidden:

1. `M0V3-MANIFEST-01`: strict file inventory, schema/digest/root verification,
   disjoint checker/import graph, mutation-bank coverage, crash/partial/
   duplicate freeze cases, and no V7/model/tokenizer/network dependency.
2. `M0V3-UNIVERSE-02`: exact 64 roots, alias bijections/balance, fixed event
   schedule, path classes, bridge necessity, and old-plus-new delayed
   necessity.
3. `M0V3-SCHEMA-03`: positive golden for every type; unknown/missing/
   duplicate/float/non-NFC/BOM/range/pad/order/identity negatives; exact
   HandoffPublic projection.
4. `M0V3-TRANSITION-04`: exhaustive legal state-command product and every
   automatic edge; failure precedence; atomic no-partial-mutation failures;
   FINISH/ABSTAIN/budget semantics.
5. `M0V3-PREFIX-05`: twin byte equality until separating outcome, E2/E3
   nonseparation, public-taint descendants only, and single-field mutations of
   every forbidden private source.
6. `M0V3-QUERY-06`: exhaustive catalog capabilities, node/atom/link candidate
   lists, cursor/order/padding/status, goal/phase/arm/score independence,
   unreturned/private/sibling/future handles, and REACHOUT_OFF.
7. `M0V3-JOIN-07`: both probe orders and all terminal patterns; exact A/B
   canonical output; reject mutation by every non-allowlisted branch field.
8. `M0V3-REPEAT-RESET-08`: FOUND, NOT_FOUND, BLOCKED, lost-response replay,
   cache/budget behavior, progress clears, all reset retain/destroy sets, and
   cross-fork write attempts.
9. `M0V3-PROVENANCE-09`: proposal-before-validation, disjoint later roots,
   root dedupe, alias normalization, shared-root legal diamond, self/forward/
   unknown/cyclic rejects, synthetic non-evidence, contradiction ordering,
   irreversible revocation, and batch atomicity.
10. `M0V3-CARRIERS-10`: exact AUTH/ATOMS/TRUTHFUL_NULL/DERANGED/BRIDGE_CUT/
    BINDING_TWIN/UNCERTAINTY_SHAM/REACHOUT_OFF/OLD_CUT/NEW_CUT pointer
    allowlists, equal exposure fields, and rejection on any extra mutation.
11. `M0V3-UNCERTAINTY-11`: all `(k,h)`, outcomes, displayed and true
    posteriors, ties, aliases, equal costs, authentic and sham behavior, and
    the 32 accidental sham acquisitions with zero causal credit.
12. `M0V3-TRACE-12`: both path alternatives, legal diamonds, answer-only,
    copied/post-hoc/cyclic deps, single-path vs all-path masking, bridge cut,
    and unchanged-decision binding shortcuts.
13. `M0V3-REDUCER-13`: exact 19-cell vector, all adverse mappings, missing/
    duplicate/foreign/reordered/nonfinal/malformed receipts, `N=64`, no retry,
    and byte-identical reruns.
14. `M0V3-HANDOFF-14`: prove public/private field disjointness, immutable
    semantic-payload digests, and fail closed if any future renderer attempts
    to consume a private receipt field.
15. `M0V3-INDEPENDENT-15`: a fresh implementation reviewer and a separate
    scientific-claim advocate bind reports to exact source/test/manifest/
    receipt hashes. Neither may promote M-TEXT or a claim.

Passage yields only a `DEV_NONCLAIM` CPU conformance receipt. Any failure
blocks H0. It cannot be compensated by a later model result.

## 14. Disposition of the v2 consensus concerns

This repair closes M0-side concerns as follows:

- exact finite universe and byte preparation: sections 1, 2, and 12;
- possible gate order: section 0;
- V7 authority/circular dependency: clean-room, no runtime reuse;
- checker circularity: constructive versus predicate implementations plus
  mutation evidence and modest claim wording;
- query agenda, branch release, repeat, and reset: sections 3--5;
- rendered/model boundary: an exact model-free handoff plus explicit deferral,
  never an optional post-hoc M0 choice;
- provenance/support/revocation: section 7;
- answer/path laundering: exact reference scripts, all-path masks, binding
  counterfactual, raw-versus-credited sham outcomes;
- durability and root reduction: sections 10--12;
- exact CPU falsifiers: section 13.

The consensus's M-TEXT recurrence, resource-factorial, endpoint, held-out
split, inference, confirmation, clean-session, provider, renderer/tokenizer,
and online-learning concerns are **not** silently solved here. They are outside
M0 and must appear as new registered tests in a separate M-TEXT proposal.

## 15. Irreducible choices still open

There are no intentionally open M0 semantic choices in this proposal. The
following governance/execution facts cannot be supplied by source-only
reasoning and therefore remain explicit future human gates:

1. approve or reject the clean-room/no-V7-dependency ruling;
2. approve exact preparation materializer, Checker A, Checker B, mutation
   bank, allowed output paths, and runtime bytes before P0;
3. after P0, inspect and ratify the actual F0 manifest root and every canonical
   fixture byte before runtime implementation;
4. approve the later M0 implementation file allowlist and test commands;
5. select independent reviewer identities after implementation; and
6. separately choose every M-TEXT model-facing and statistical parameter.

Those are gates, not defaults. In particular, this advisory cannot be treated
as the absent exact-byte F0 artifact and cannot authorize materialization or
implementation merely because the semantics are now closed.
