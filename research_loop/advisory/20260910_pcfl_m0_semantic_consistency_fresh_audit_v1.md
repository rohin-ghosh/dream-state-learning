# PCFL M0/M-TEXT semantic-consistency audit — fresh v1

Date: 2026-09-10  
Status: **source-only independent audit; REWORK; no execution authority**

This audit compares:

- `20260910_pcfl_m0_exact_contract_repair_fresh_v1.md`; and
- the outcome-changing M0 amendments in
  `20260910_pcfl_mtext_supplied_exact_contract_repair_fresh_v1.md`.

It authorizes no implementation, materialization, fixture generation, CPU
benchmark run, model/tokenizer call, training, adapter operation, GPU use,
claim, or release.

## 0. Verdict

**REWORK before successor ratification.** The finite algebra is promising,
but the two advisories do not yet compose into one closed source contract.
The main problems are semantic rather than stylistic:

1. M-TEXT changes M0's wire types and transition outcomes without a version
   bump.
2. `TRUTHFUL_NULL` preserves the authentic link endpoints and link identity,
   so it reveals precisely the graph it is meant to remove.
3. M0 returns one item per read while M-TEXT promises one atom-plus-link
   envelope; neither document freezes which endpoint capabilities a return
   releases. Consequently the claimed eight-read plan is not constructively
   guaranteed.
4. The M0 controller treats a wrong relation and premature `FINISH` as
   invalid actions, while M-TEXT makes them ordinary policy failures. The
   schemas, event slots, expected vectors, and reducer still encode the old
   behavior.
5. Checker-only semantic hashes remain in M0's public carrier even though
   M-TEXT requires target-neutral public slot handles.
6. M-TEXT's `trace_dependence` invokes an all-path-mask model intervention
   that is absent from the nineteen-condition roster and request arithmetic.
7. Per-probe endpoints are later reduced as if they were one binary
   root-condition endpoint, without specifying the conjunction.
8. The M0 `HandoffPublic` and M-TEXT `MTextHandoff` overlap but do not define
   their composition, and the latter appears to require pre-materializing
   model-dependent dynamic checkpoints.
9. Provenance proposals have no total logical position between event 24 and
   event 25 (or event 41 and event 42), despite support requiring strict
   proposal-before-validation chronology.
10. `AUTH_ONE_SHOT_TAPE` cannot in general cite handles returned by reads
    because its complete tape is generated before those handles are exposed.
    It is therefore a no-feedback lower bound, not yet an equal-interface
    recurrence comparator.

These are repairable without widening the intended claim. The successor
should be a single `PCFL_M0_THIN_V4` source contract incorporating the patch
list below, followed by a separately bound M-TEXT contract.

## 1. Closed-type and identity repairs

### P01 — bump every outcome-changing M0 identity

The fixed action catalog, `NO_EFFECT`, read cut, neutral handles, bundled
reader return, and `NO_PERSIST_NEW` alter public semantics. Do not preserve
`instrument:"PCFL_M0_THIN_V3"`, wire `v:3`, or `...-v3\0` hash domains.
The successor must use one new version consistently, recommended:

```text
instrument = PCFL_M0_THIN_V4
wire v = 4
hash domains = PCFL-M0-*-v4\0
```

Root algebra may be described as unchanged, but a V3 runtime or artifact must
fail to load under V4 rather than collide by name.

### P02 — separate checker identities from actor capabilities

M0 currently exposes `atom_id:hex64` and `link_id:hex64` in `Carrier`, while
M-TEXT says those hashes are checker-only and the actor sees `a00..a19` and
`l00..l06`. Freeze two distinct layers:

```text
SemanticAtom / SemanticLink
  checker-only FactKey, semantic hash, evidence-root set, support status

PublicAtomSlot / PublicLinkSlot
  fixed slot handle plus the permitted public payload

PrivateSlotMap
  exact semantic-ID <-> public-slot mapping; never rendered or readable
```

No semantic atom/link hash, root ID, condition name, score, or private slot
map may occur in `FiniteView`, `MemoryReturn`, model-visible carrier rows, or
command dependencies. Public event IDs may remain hashes because they name
ordinary released events, but they are not atom/link capabilities.

The 26 atom slot handles are exactly `a00..a19` and the seven link handles are
exactly `l00..l06`. Presentation rotation permutes slot assignments once at
root preparation; transforms never rename slots.

### P03 — keep semantic identities stable under evidence/status changes

Retain M0's rule that a semantic link key is derived from the ordered pair of
endpoint semantic atom IDs, not its support-root IDs or status. Delete the
M-TEXT sentence saying link identity includes support roots. Support roots
belong in provenance metadata. Otherwise corroborating evidence would rename
the fact, contradicting the stated stable-identity law.

Changing an endpoint FactKey creates a new semantic link ID. Changing only
`AUTH` to `EMPTY`, adding corroboration, or revoking support does not.

### P04 — freeze one action spelling and closed unions

The documents mix `c0/c1` with `COMMIT_0/COMMIT_1`. Choose one spelling in
every catalog, command, event, prompt, golden, scorer, and parser. The least
disruptive choice is:

```text
relation action IDs = the sixteen public relation aliases
experiment action IDs = the four public experiment aliases
commit action IDs = "c0", "c1"
terminal catalog IDs = "finish", "abstain"
command op enums = "READ", "ACT", "FINISH", "ABSTAIN"
```

`action_catalog` is a complete fixed opportunity set, not an executable-
legality oracle:

- path phases: sixteen relation aliases plus `finish,abstain`;
- uncertainty: four experiment aliases plus `abstain`;
- acquire: `c0,c1,abstain`.

The closed `ACT.action_id` union must exclude `finish/abstain`, which have
their own command types. Phase-specific plan validation must state whether a
plan may contain only relation aliases, or experiment followed by commit;
do not leave `public-action-id` undefined.

### P05 — close ordinary failure types

Add `NO_EFFECT` to `PublicEvent.outcome.kind`, with `value:null`. Add an
ordinary path terminal `WRONG_FINISH` (recommended terminal enum `FAILURE`,
failure enum `WRONG_FINISH`) that is a zero-valued policy outcome, not an
instrument-invalidating `ILLEGAL_ACTION`.

`ILLEGAL_ACTION` is then reserved for a syntactically valid command whose ID
is outside the phase's fixed action catalog or whose command kind is wrong
for the phase. A cataloged relation with no outgoing world transition is
ordinary `NO_EFFECT`.

## 2. Padding and carrier repairs

### P06 — retain fixed outer sizes, but rederive every V4 bound

M0's underscore padding algorithm can give exact UTF-8 byte lengths for
closed ASCII padding, but every changed V4 schema must be remeasured. Do not
copy the V3 bounds by assertion. The source contract must contain either the
new exact bounds or a no-choice bound formula and exhaustive positive/
overflow fixtures.

Nested public null, empty, atom, and link records must each have their own
fixed size. `FOUND`, `NOT_FOUND`, `BLOCKED`, and the explicit empty-link
response must have the same `MemoryReturn` outer byte length.

Equal UTF-8 bytes do not imply equal tokenizer tokens. DERANGED/AUTH token
equality remains an M-TEXT preparation check under the frozen tokenizer; it
must not be claimed by M0 or repaired through per-root search.

### P07 — make `TRUTHFUL_NULL` actually connection-neutral

The proposed V3 transform is invalid for its intended role:

```text
preserve AUTH endpoint pairs and link IDs but set status EMPTY
```

Endpoints plus a shared link ID encode the authentic adjacency even if prose
says `EMPTY` does not assert it. Repeating the same empty slot handle when
querying each endpoint leaks the pair as well.

Replace it with an endpoint-null, identity-null public empty record:

```text
PublicEmptyLink := {
  v:4, status:"EMPTY", handle:null, left:null, right:null,
  evidence_ids:[], pad:string
}
```

For `TRUTHFUL_NULL`, any legal atom-anchor query at cursor zero may return
this same canonical empty record, with a typed-null atom and an empty grants
set; higher cursors return `NOT_FOUND`. The return is query-local and grants
no reusable link capability. The internal carrier still has seven fixed slot
positions for exposure accounting, but no public slot ID or endpoint from a
null/empty/cut slot is released through the reader.

This control may differ from `ATOMS` by explicitly returning “no supported
connection.” It must not be advertised as matched authentic retrieval
content. The primary connectivity contrasts remain AUTH versus ATOMS,
DERANGED, BRIDGE_CUT, and REACHOUT_OFF.

### P08 — define slots separately from their optional records

Use a carrier layout such as:

```text
CarrierAtomSlot := {slot:a00..a19, record:PublicAtom|null, pad:string}
CarrierLinkSlot := {slot:l00..l06, record:PublicAuthLink|null, pad:string}
```

The slot key exists in the private/public-handoff carrier for fixed exposure,
but it becomes an actor capability only when a non-null record is returned.
This prevents a cut/null slot from becoming a hidden graph pointer merely
because its stable position is known to the controller.

## 3. Exact reader and visibility repair

### P09 — replace both incompatible `MemoryReturn` definitions

V3's `item_kind` one-of atom/link conflicts with M-TEXT's one-atom-plus-one-
link envelope. Freeze the bundled form explicitly:

```text
MemoryReturnV4 := {
  v:4,
  status:"FOUND"|"NOT_FOUND"|"BLOCKED",
  fingerprint:hex64,
  anchor:PublicHandle,
  cursor:u8,
  atom:PublicAtom|TypedNullAtom,
  link:PublicAuthLink|PublicEmptyLink|TypedNullLink,
  grants:[PublicHandle],
  repeat_count:1|2|3,
  pad:string
}
```

`grants` is a sorted, duplicate-free, closed list and is the sole authority
for adding atom/link capabilities to catalog/workspace. Merely mentioning a
node alias inside an Atom does **not** grant a NODE capability.

The common reader has these exact candidate laws, all based only on the
carrier, anchor, cursor, `reader_open`, and repeat state:

1. `NODE n`: enumerate non-null public atoms whose `src==n` or `dst==n`,
   sorted by public atom slot handle. Return the selected atom, typed-null
   link, and grant only that atom handle.
2. `ATOM a`: enumerate readable `AUTH` links whose `left==a`, sorted by
   public link slot handle. Return the selected link **and its right endpoint
   atom in the same envelope**; grant the link handle and right-atom handle.
   This is the explicit connected-memory operation.
3. `LINK l`: cursor zero returns its left endpoint atom and cursor one its
   right endpoint atom, each bundled with the same link; other cursors are
   `NOT_FOUND`.
4. In `ATOMS`/cut cells, ATOM and LINK queries have no candidates. In
   `TRUTHFUL_NULL`, the special query-local empty response in P07 is allowed.
   In `REACHOUT_OFF`, every ATOM-to-link dispatch returns `BLOCKED` without
   consulting an index.

Candidate order must use actor-visible slot handles, not private semantic
hash order. Otherwise the cursor agenda is an invisible controller choice.

### P10 — prove the eight-read plan constructively

Under P09, either registered four-edge goal path is obtainable in no more
than six reads:

1. read start node `S` -> one of `p0,p2`;
2. read goal target -> terminal atom `p5` or `p6`;
3. read the chosen start atom -> its next atom plus link (`p1/l0` or
   `p3/l1`);
4. read that atom -> `p4` plus `l2` or `l3`;
5. read `p4`, cursor zero -> one terminal atom plus `l4` or `l5`;
6. only if it was the other goal, read `p4`, cursor one.

The result contains the four STEP atoms and all three adjacent AUTH links
needed by the constructive citation rule. Eight reads therefore leave two
slots for a benign retrieval mistake without changing the causal mechanism.

This proof depends on the bundled successor return and public-handle order;
it is false under the current one-item/cursor ambiguity and therefore must be
a source-contract theorem plus exhaustive golden test.

### P11 — prove ATOMS cannot crawl

In ATOMS, the initial catalog grants only current-state and visible-goal node
handles. Reading them can expose a first-edge atom and terminal-edge atom.
Their internal `src/dst` strings do not grant new NODE capabilities. With no
AUTH link, an ATOM read cannot return the intervening atom. After the first
relation action, `reader_open=false`, even after `NO_EFFECT`. Thus ATOMS
cannot walk state-by-state and reconstruct a plan before acting.

Add an exhaustive capability-reachability test: before the first action,
the closure of all legal ATOMS reads must exclude `p1,p3,p4` and every AUTH
link. Run it for both goals, all 64 roots, every cursor, and every presentation
rotation. This is a semantic necessity test, not a model result.

### P12 — close catalog and release semantics

The catalog contains exactly:

- current state NODE handle;
- visible goal start/target NODE handles;
- explicitly declared uncertainty NODE handles and, if intended, its public
  citation handles;
- atom/link handles in a prior `MemoryReturn.grants` in the same branch.

No node aliases inside returned Atom/Link payloads, semantic hashes, null-slot
positions, sibling returns, carrier bytes, or public-event fields grant a
capability unless the source contract names them above. The two advisories
currently disagree about public-event fields; choose one rule. Recommendation:
events grant only their explicit node aliases, never atom/link handles.

`workspace` is insertion order of distinct granted atom/link handles. Catalog
presentation is a deterministic permutation of this set plus declared node
handles. A return that would exceed capacity fails before mutation.

### P13 — update uncertainty citations

Actor-visible `Uncertainty.citations` cannot remain checker semantic atom
hashes under the neutral-handle law. Rename them `citation_handles` and use
the relevant `a00..a19` handles, or keep opaque public event IDs and state
that they are evidence citations rather than READ capabilities. If atom
handles are chosen, explicitly add them to the uncertainty-start catalog.
Do not mix the two identity spaces.

## 4. Transition and checkpoint-DAG repair

### P14 — replace the legal-action controller rule

Delete “a legal relation ACT exists iff an authentic world fact has current
src.” All sixteen relation aliases are syntactically callable in every path
state. Dispatch is:

- outgoing registered relation: consume one action, emit `NODE`, move state;
- other cataloged relation: consume one action, emit `NO_EFFECT`, keep state;
- either case: increment `world_actions_taken`, close reader, clear transient
  memory, and occupy the next fixed attempt slot;
- fourth nonterminal relation attempt: close as `BUDGET` if not at target.

`NO_EFFECT.evidence=false`; it never becomes a provenance ROOT. Successful
observed transitions have the contract's declared evidence flag.

Premature `FINISH` closes as ordinary `WRONG_FINISH`, emits no invented world
fact, and scores zero. `ABSTAIN` remains ordinary. Neither invalidates the
instrument.

### P15 — freeze all phase budgets and reader cuts

Replace every path-phase “32 reads” with exactly eight in V4 reference
scripts, views, goldens, expected vectors, and tests. Relation actions remain
four, plus one uncharged terminal command opportunity. The first relation
attempt, successful or not, closes the reader for that path phase.

The successor must separately state exact uncertainty and acquisition read,
action, and call budgets. M-TEXT allows four combined turns but M0 still
grants 32 reads in each phase. Recommended narrow rule: uncertainty starts
with two reads and one experiment action; acquisition inherits remaining
turn/read state and has one commit action; the combined phase has four model
calls maximum. If the displayed `Uncertainty` object makes reads unnecessary,
zero is also defensible—but one exact choice must replace both numbers.

### P16 — freeze the cross-condition checkpoint graph

The documents alternate between a sequential “one policy life” and isolated
control forks. Freeze a DAG. Recommended:

```text
OLD(root)
  -> isolated PATH_A(c) and PATH_B(c) for each registered path condition

JOIN_REFERENCE(root)
  -> CUE(c) for AUTH and uncertainty controls

ACQUIRED_AUTH(root, actual AUTH cue result)
  -> DELAYED_AUTH / OLD_CUT / NEW_CUT forks

CUE_NO_PERSIST(root)
  -> DELAYED_NO_PERSIST
```

Path-condition transcripts must not silently become cue inputs. If
`JOIN_REFERENCE` uses canonical reference traces, say so and label it supplied
public history. If the same model's AUTH path traces are meant to survive the
join, then every downstream prompt becomes path-performance-dependent and
the condition/request roster must say that explicitly.

For an end-to-end “observed then later used” claim, `delayed_integration`
must be zero unless that root's registered AUTH acquisition actually
succeeded. If delayed cells instead start from an oracle-prepared acquired
checkpoint, relabel the endpoint “supplied-new integration” and do not call it
the model's acquisition.

### P17 — register `NO_PERSIST_NEW` in M0

The outcome-changing transform must exist in M0 source, goldens, transform
allowlists, and CPU tests before M-TEXT uses it. Either add
`DELAYED:NO_PERSIST_NEW` as a twentieth M0 root-receipt cell and update every
`x19` schema/vector, or state that it is a separately enumerated M0 transform
fixture outside the root score. The first option is clearer. It removes both
the new atom and new link after reset while preserving the ordinary
acquisition event in the pre-reset trace.

## 5. Provenance repair

### P18 — create a real total logical order for SYNTH nodes

`SYNTH.seq:u16` has no legal value strictly after event 24 and strictly before
validation event 25; the same problem occurs between 41 and 42. Replace bare
sequence comparison with a closed total coordinate, for example:

```text
order = {event_seq:u16, lane:"EVENT"|"POST_EVENT_SYNTH", ordinal:u16}
```

and freeze ordering such that old proposals are after event 24 and before
event 25, while new proposals are after event 41 and before event 42. Every
parent must be strictly earlier in this total order. IDs hash the complete
coordinate. Tests cover same-event, forward, duplicate, and cross-cut parents.

### P19 — close proposal parent/support sets

For each proposal, define its parent roots as the complete deduplicated set of
primitive ROOT evidence supporting each endpoint **as of the proposal cut**.
Later validation roots must be strictly post-proposal and disjoint from that
set. State whether old validation roots already supporting `p4` are included
in the new `p4,nh` proposal's parent set (recommend yes: all roots as of cut).
Then the fresh seq-42 p4 and seq-43 nh occurrences provide the required later
disjoint validation.

Keep transformed carriers outside provenance admission. DERANGED and
BINDING_TWIN may carry checker-side synthetic semantic IDs, but cannot create
ROOT/SYNTH support or be recompiled.

## 6. Scoring and reducer repair

### P20 — define root-condition endpoint conjunctions

Section 8 says every endpoint is binary at `(root,condition)`, but
`plan_valid`, `answer_success`, and `constructive_path` are probe-local.
Freeze both probe-local names and root composites, for example:

```text
answer_A, answer_B
plan_A, plan_B
constructive_A, constructive_B
both_answer = answer_A & answer_B
both_plan = plan_A & plan_B
two_goal_traversal = answer_A & constructive_A &
                     answer_B & constructive_B & join_clean
```

Use only named root composites in `b_e`, confirmation gates, and adverse
bounds. “Plan is a prefix and reaches target” should become exact equality:
the declared pre-action plan is one complete registered minimum path, and the
successful executed relation sequence equals it with no `NO_EFFECT` before
`FINISH`.

Add the omitted DEV reducer explicitly:

```text
R_DEV_e(c) = sum_{k=0}^{7} min(e(k,0,c),e(k,1,c)) / 8
```

### P21 — do not score an unregistered all-path-mask model run

M-TEXT defines `trace_dependence` using a model all-path-mask intervention,
but no such condition appears in the nineteen-cell roster or 589-call
arithmetic. Choose one of two exact repairs:

1. add `ALL_PATH_MASK_RECURRENT`, recalculate all calls/tokens/resources, and
   bind it before execution; or
2. recommended for the narrow assay, use the already registered
   `BRIDGE_CUT_RECURRENT`, after M0 proves that the cut intersects every legal
   path class.

Under option 2:

```text
trace_dependence(root) =
  AUTH has constructive two-goal traversal
  AND BRIDGE_CUT destroys the registered construction
  AND TWIN_REDIRECT changes the terminal goal-specific relation action
      for each AUTH-successful probe
```

The TWIN result is paired to AUTH and is not recursively scored within the
already transformed cell. If AUTH never reaches the decisive state, the
paired change bit is zero.

### P22 — keep raw and causally credited information distinct

Retain M0's good repair: sham can accidentally commit correctly for one twin,
so report raw acquisition/delayed success separately from realized target
information, belief revision, acquisition credit, and delayed credit. The
twin-min reducer will make the balanced sham block fail, but the raw per-root
receipt must not rewrite chance success to zero.

For the claimed end-to-end endpoint use:

```text
delayed_integration_credit =
  acquisition_success & realized_information & belief_revision &
  old_used & new_used & delayed_answer & constructive_delayed
```

### P23 — resolve the native-graph superiority contradiction

Section 9 correctly excludes `NATIVE_GRAPH` from the practical baseline that
AUTH must beat because it is a labeled ceiling. Section 13 incorrectly says
failure to beat raw/RAG/**native graph** removes superiority language. Delete
native graph from that requirement. Report it as a ceiling only.

The `-0.05` adverse bound should be described exactly for 16 blocks: because
rates move in `1/16`, it permits no net lost block (`-1/16=-0.0625` fails).
This is acceptable, but should not be presented as an approximately five-
point tolerance.

### P24 — relabel or repair the one-shot tape comparator

The current tape is generated before any READ result yet later commands may
cite only actually returned handles. It therefore cannot generally construct
a valid memory-dependent tape. Equal output-token allowance does not fix the
information mismatch.

Fast repair: retain it as `AUTH_NO_FEEDBACK_TAPE`, explicitly a structural
lower bound for interactivity, and do not use it to identify the value of
scratch recurrence. `AUTH_SCRATCH_OFF` remains the clean explicit-scratch
ablation because it receives the same successive public outcomes.

If a true one-call planning comparator is required, separately define a
goal-independent deterministic prefetch whose exact eight return envelopes
are supplied before its one call. That changes the interface and requires a
new matched condition; it cannot be inferred during implementation.

## 7. Handoff and materialization repair

### P25 — define one layered handoff, not two competing public records

Make V4 `HandoffPublic` the canonical semantic payload. Define
`MTextHandoff` as a checker/controller receipt that hashes one exact
`HandoffPublic` plus renderer/model-projection contract hashes. State which
fields are model-visible (normally only rendered `FiniteView` and permitted
scratch) and which are reader/controller inputs. Do not embed the full
carrier in the model message merely because it is inside the public handoff.

Neutral public handles must already exist in `HandoffPublic`; the renderer
may not replace semantic hashes ad hoc.

### P26 — distinguish static frozen inputs from dynamic execution outputs

The fixture manifest can freeze roots, carriers, phase-start checkpoints,
schemas, transition tables, reader tables/predicates, transforms, and expected
reference vectors. It cannot pre-freeze the exact post-command checkpoint of
an unknown model trajectory unless the complete finite state graph is
explicitly enumerated.

Choose and state one approach:

- recommended: freeze static phase starts plus the complete transition/
  reader functions; dynamic `FiniteView`, `CommandResult`, and per-call
  handoffs are content-addressed execution receipts derived from them; or
- materialize the exhaustive reachable state graph and bind every node.

Do not use the phrase “each root/condition/phase checkpoint has exactly one
frozen record” for model-dependent states under the first approach.

### P27 — reconcile the gate-order wording

The source gate may ratify a no-choice materializer without already possessing
its output. The later F0/implementation packet must contain the actual 64-root
bytes, manifest root, checker receipts, and mutation results. Rewrite M-TEXT
§2.3's “successor ratification packet must contain actual bytes” to name the
specific later byte-freeze gate, otherwise it contradicts M0's S0 -> P0 -> F0
order.

Retain the zero-V7 dependency and two disjoint checkers. Checker agreement is
reproducibility plus invariant evidence, not proof of the human specification.

## 8. Mandatory successor tests

In addition to the existing proposed registry, the successor needs these
explicit tests before it is source-closed:

1. `M0V4-VERSION-DOMAIN-SEPARATION`: every V3 artifact rejects under V4.
2. `M0V4-ACTOR-HASH-DENIAL`: no semantic atom/link hash reaches any actor
   projection or dependency.
3. `M0V4-ACTION-CATALOG-NONORACLE`: every path state exposes the same 16
   relations plus terminal opportunities; wrong relations yield `NO_EFFECT`.
4. `M0V4-WRONG-FINISH-ORDINARY`: premature finish is a behavioral zero and
   does not invalidate a root.
5. `M0V4-TRUTHFUL-NULL-NONCONNECTING`: endpoints, shared IDs, support roots,
   and cross-query identity cannot reconstruct AUTH adjacency.
6. `M0V4-BUNDLED-RETURN-ROUNDTRIP`: every NODE/ATOM/LINK cursor has one exact
   atom-plus-link envelope and exact grants.
7. `M0V4-AUTH-EIGHT-READ-CONSTRUCTION`: both legal alternatives for both
   goals are constructively available within eight reads on all 64 roots.
8. `M0V4-ATOMS-CAPABILITY-CLOSURE`: exhaustive pre-action ATOMS reads cannot
   expose any middle-path atom or link.
9. `M0V4-READER-CLOSE-ON-NO-EFFECT`: the first successful or unsuccessful
   relation attempt closes reads identically.
10. `M0V4-PUBLIC-CURSOR-ORDER`: candidate order is a function only of public
    handles and allowed reader arguments.
11. `M0V4-SYNTH-BETWEEN-CUTS`: proposal chronology is strictly between old/
    new evidence and validation under the total order.
12. `M0V4-NO-PERSIST-NEW`: acquisition is visible pre-reset and neither new
    atom nor link survives the reset.
13. `M0V4-CHECKPOINT-DAG-ISOLATION`: path, cue, delayed, and control forks
    match the frozen dependency DAG with no sibling contamination.
14. `MTEXT-ROOT-ENDPOINT-CLOSURE`: every probe-local endpoint maps to one
    named binary root composite before reduction.
15. `MTEXT-TRACE-CONDITION-ROSTER`: every behavioral counterfactual invoked
    by a score has an enumerated condition and accounted requests, or uses the
    registered bridge/twin conditions exactly.
16. `MTEXT-TAPE-FUTURE-HANDLE-DENIAL`: a pre-observation tape cannot cite a
    future capability and is not mislabeled a matched recurrence assay.
17. `MTEXT-STATIC-DYNAMIC-HANDOFF`: frozen inputs and dynamic execution
    receipts are disjoint and hash-linked.
18. `MTEXT-NATIVE-CEILING-LABEL`: native graph can bound performance but is
    never silently added to the raw/RAG superiority gate.

Mutation coverage must include each `NO_EFFECT`/wrong-finish field, every
grant, every public/private handle substitution, every EMPTY endpoint/shared-
identity leak, every reader-open transition, every checkpoint-parent edge,
and every probe-to-root reducer mapping.

## 9. What remains valid

The audit does **not** reject the project decomposition or the narrow claim.
The following pieces survive largely intact:

- the exact 64-root no-RNG algebra and twin construction;
- two independent goal paths sharing a necessary bridge;
- target-versus-nuisance experiment controls and raw-versus-credited outcomes;
- delayed old-plus-new integration after a sterile reset;
- fixed resource accounting and deterministic finite-census reduction;
- clean-room, zero-V7 runtime dependency;
- strict source -> preparation -> byte freeze -> implementation -> CPU ->
  model-DEV -> confirmation gate order; and
- the claim ceiling: supplied connected text only, with no DREAM, SLEEP,
  LoRA, learning, parenting, compression, or lifetime claim.

The smallest safe next contract is therefore not a larger redesign. It is a
V4 consolidation of these amendments with the bundled reader, true null
control, exact checkpoint DAG, and closed reducer above.

