# PCFL v2 minimal exact semantics — fresh Stage-0 proposal

Date: 2026-09-10

Status: **advisory proposal only; not ratified**. This note authorizes no
implementation, data/root generation, model/provider call, scientific run,
child or lineage operation, LoRA/training, GPU use, claim, promotion, or
release. It is a proposed exact-byte target for a later human decision under
`AGENTS.md`.

## Verdict and hard scope

The smallest coherent first surface is a pure, CPU-only finite-state
instrument named `PCFL_STAGE0_V2`. It is always stamped `DEV_NONCLAIM`, has no
accepted-state output, and cannot consume or emit a child, model, adapter,
checkpoint, corpus, parent, clean-source receipt, or scientific split. It
contains only closed semantic records, a finite paired-world fixture law, a
trusted transition function, a finite-view/command boundary, a deterministic
public-evidence reference DREAM, a validating renderer, pure interventions,
synthetic trace scorers, and one root-receipt reducer.

Do **not** call this M or a text ceiling. There is no text-model runner,
prompt, tokenizer, chat template, reader backend, E0, LoRA, L, C, GPU,
network, ancestry guard, CAS journal, broker, or security-platform component.
CPU passage says only that this instrument implements the ratified finite
semantics. It says nothing about learning or actor use.

This is a narrower successor to the unratifiable `PCFL-D0-EXACT-V2` bundle,
not a repair-by-reference to that bundle. In particular it imports none of
that design's tokenizer/window cuts, selected deck, Bayes-over-generator,
derived-transform anchor, power/resource contract, comparator, or performance
fixture.

## 1. Closed finite world and relation algebra

### Universe and registered suite

- Internal symbols are `N00..N1f` (32 nodes), `R00..R0f` (16 action-labelled
  relations), experiments `E0..E3`, and outcomes `0,1`. Semantic roles are
  fixed as `N00=S,N01=X,N02=Y,N03=B,N04=C,N05=TA,N06=TB,N07=D`,
  `N08=H0,N09=H1,N0a=Z0,N0b=Z1`, and `N0c..N0f=E0..E3`; `N10..N1f` are
  reserved decoy nodes. Role names are specification mnemonics, never actor
  strings. No other symbol is legal.
- The complete root universe is the 64 roots `(k,h)` where
  `k in {0,...,31}` and hidden target bit `h in {0,1}`. Paired twins share
  `k`; the nuisance bit is `z = popcount(k) mod 2` and is therefore identical
  within a twin pair.
- The actor sees node alias `n%02x(i XOR k)`, relation alias
  `r%02x(j XOR (k mod 16))`, and experiment alias
  `e%01x(j XOR (k mod 4))`. It never sees `k`, `h`, `z`, an internal symbol,
  a root ID, or an arm name. Declared presentation arrays are cyclically
  rotated by `k mod length`; declared sets are instead sorted. Across the 32
  values
  of `k`, each alias is balanced exactly and each presentation position has
  count difference at most one. Goal A/B execution order alternates by
  `k mod 2`, but the join order is always A then B.
- The two members of every `(k,*)` pair have the same old public ledger,
  carrier, goals, catalogs, costs, record lengths, presentation transform,
  nuisance value, and reset schedule. Only `h` differs.

Let `U` be the disjoint union of the finite node, experiment, and outcome
symbols. The algebra is the finite relation algebra `P(U x U)` with
`empty`, identity, union, intersection, complement relative to `U x U`,
converse, and composition
`R ; S = {(x,z) | exists y: (x,y) in R and (y,z) in S}`. A state-transition
atom is the closed tuple `(atom_id, src, rel, dst, public_event_roots)` and
denotes singleton relation `{(src,dst)}` labelled by `rel`. A prediction atom
is `(hypothesis, experiment, outcome_counts)` where `outcome_counts` is one
of `[1,0]`, `[0,1]`, or `[1,1]`; it is typed and never composes as a state
transition. Every prediction atom uses internal relation `R09` and has no
state-transition destination.

The seven old path atoms are exactly:

```text
p0: S -R00-> X       p1: X -R01-> B
p2: S -R02-> Y       p3: Y -R03-> B
p4: B -R04-> C       p5: C -R05-> TA
                     p6: C -R06-> TB
```

Goal A is `S -> TA`; goal B is `S -> TB`. Their complete minimum-cost path
classes are respectively `{[p0,p1,p4,p5], [p2,p3,p4,p5]}` and
`{[p0,p1,p4,p6], [p2,p3,p4,p6]}`. Every edge costs one, paths must be simple,
and no other path or equivalence rule is legal. Thus no single record closes
a goal; A and B differ; and `p4` is in every legal path. A new successful
acquisition adds exactly `nh: C -R(07+h)-> D`. The delayed goal is always
`S -> D`;
its complete path class replaces `p5/p6` above with `nh`, so every delayed
path requires both old atoms and the new atom.

The old ledger has exactly 32 primitive public events: one discovery event
for each `p0..p6`, the 16 prediction observations below, two typed decoys that
join no path, and one later validation occurrence for each `p0..p6`. The
reference DREAM cut occurs before the seven validation occurrences.
The decoys are exactly `q0:N10 -R0e-> N11` and
`q1:N12 -R0f-> N13`.

```text
       E0     E1     E2     E3
H0    [1,0]  [0,1]  [1,1]  [1,1]
H1    [0,1]  [1,0]  [1,1]  [1,1]
Z0    [1,1]  [1,1]  [1,0]  [0,1]
Z1    [1,1]  [1,1]  [0,1]  [1,0]
```

For a concrete root, experiment outcomes are `E0=h`, `E1=1-h`, `E2=z`, and
`E3=1-z`. All four actions cost one and use the same input/output schema.
In a path phase, a relation action is legal exactly when a registered atom has
the current node as `src` and that relation label; it moves state to `dst` and
emits one ordinary public event. Experiments are legal only in UNCERTAINTY.
`COMMIT_b` is legal only in ACQUIRE; it emits `ACQUIRED` and `nh` iff `b=h`,
otherwise `MISS` and no atom.

## 2. Canonical bytes and the only actor boundary

All records are closed JSON records: missing, extra, duplicate, mistyped, or
out-of-range fields reject. Input must be UTF-8 without BOM, every string must
already be NFC, integers are nonnegative and at most `2^53-1`, and floats are
forbidden. Canonical bytes are RFC-8785/JCS bytes with no leading/trailing
whitespace and no final newline. A wire digest is
`sha256(type || 0x00 || padded_canonical_bytes)`; semantic identity uses the
same formula after replacing `pad` by the empty string. Both use the literal
ASCII type name. Arrays whose order is semantic retain it; sets are arrays
sorted by semantic identity. Parsing is strict and round-trip equality to
canonical bytes is required. Presentation arrays use the registered rotation
and are not subsequently resorted; only declared sets are sorted.

Every visible `Atom`, `Link`, `PublicEvent`, `MemoryReturn`, and
`Uncertainty` record is padded to its type's fixed bound (respectively 256,
192, 256, 768, and 2048 bytes). `pad_to(B,o)` sets `pad` empty, canonicalizes,
then sets `pad` to exactly `B-len(canonical(o))` ASCII underscores and asserts
final length `B`; overflow rejects. `pad` is ignored by semantics and excluded
from semantic identity. Carriers always expose 26 atom slots and seven link
slots; unused slots are typed `NULL` records. This is the complete Stage-0
matched-exposure claim: record counts, record byte lengths, catalogs, costs,
read/action budgets, and return slots. It makes no compute, token, or memory
equivalence claim.

The closed semantic records are:

```text
Goal        {v:2,goal_id:"A"|"B"|"D",start:public-node,target:public-node}
Atom        {v:2,atom_id:hex64,kind:"STEP"|"PREDICT",src:public-node,
             rel:public-relation,dst:null|public-node,
             experiment:null|public-experiment,outcome_counts:null|[u8,u8],
             root_ids:[hex64],pad:string}
Link        {v:2,link_id:hex64,status:"AUTH"|"NULL"|"EMPTY"|"REVOKED",
             left:null|hex64,right:null|hex64,root_ids:[hex64],pad:string}
PublicEvent {v:2,event_id:hex64,seq:u16,action:public-action-id,
             before:public-node,outcome:{kind:"NODE"|"BIT"|"ACQUIRED"|"MISS",
             value:null|public-node|0|1},after:public-node,evidence:boolean,
             pad:string}
TransitionRow {v:2,row_id:hex64,src:public-node,via:[public-relation x 2],
             dst:public-node,atom_ids:[hex64 x 2],root_ids:[hex64],pad:string}
Uncertainty {v:2,anchor:[public-node x 2],prior_counts:[1,1],
             candidates:[{action:public-experiment,cost:1,
             outcome_counts:[[u8,u8],[u8,u8]],citations:[hex64 x 2]} x 4],
             pad:string}
```

`TransitionRow` is only a supported two-atom composition projection; it is
not training data or a write. `Uncertainty.candidates` are sorted by public
action ID, and every citation is one of the 16 public prediction atoms.

The sole actor-readable object is this closed `FiniteView` schema:

```text
FiniteView := {
  v: 2,
  phase: enum,
  state: public-node,
  goal: null | {goal_id:"A"|"B"|"D", start:public-node, target:public-node},
  legal_actions: [public-action-id] (sorted, complete),
  last_event: null | PublicEvent,
  uncertainty: null | Uncertainty,
  memory: null | {
    status:"FOUND"|"NOT_FOUND"|"BLOCKED", fingerprint:hex64,
    atom:null|Atom, links:[Link] (at most one padded slot), repeat_count:1..3
  },
  repeat: {
    fingerprint:null|hex64, count:0..3, limit:2, blocked:boolean,
    last_reset:"ROOT_START"|"PROBE_FORK"|"GOALS_JOIN"|
               "POST_SLEEP"|"DELAYED_RESET"
  },
  joined: null | GoalsComplete,
  workspace: [public object IDs] (at most eight, insertion order),
  budget: {reads_remaining:0..8, actions_remaining:0..4}
}
```

The only commands are the closed records
`{v:2,op:"READ",anchor:public-handle,cursor:0..7,deps:[]}`,
`{v:2,op:"ACT",action_id:public-action-id,deps:[hex64]}`,
`{v:2,op:"FINISH",deps:[hex64]}`, and
`{v:2,op:"ABSTAIN",reason_code:"NO_PATH"|"NO_TARGET_INFO"|"BUDGET_GUARD"}`.
An anchor is legal only if
it is the current public state/goal symbol, a public event field, or an atom or
link returned earlier in the same branch. `deps` contains only earlier public
object IDs and is the constructive-trace edge list. There is no implicit query
builder: command bytes are the agenda. The carrier/index is built before any
goal and cannot read a goal, phase schedule, root, arm, score, future event, or
command. Reader order is semantic-ID order, `cursor` is explicit, and all
FOUND/NOT_FOUND/BLOCKED envelopes have the same fixed size. The actor has no
path, field, handle, callback, error string, filename, environment value, or
object type capable of resolving a private object.

Returned atom/link semantic IDs are intentionally public and may be used as
later anchors; unreturned catalog IDs are not. The acquisition anchor is not
derived by a compiler: it is an exact copy of the already public registered
opaque aliases of the `H0/H1` calibration handles (or `Z0/Z1` in the sham)
and is rendered with the same schema and size; the letters `H` and `Z` never
occur in actor bytes.

## 3. Prefix law, phase join, repeats, and resets

For twin worlds `W(k,0)` and `W(k,1)`, let `V(W,c[0:t])` be the concatenation
of canonical `FiniteView` bytes produced by the same legal public command
history. If the history contains no target-separating action from
`{E0,E1,COMMIT_0,COMMIT_1}`, then
`V(W(k,0),c[0:t]) == V(W(k,1),c[0:t])` byte for byte. On the first `E0/E1`
or COMMIT action, views remain equal through command acceptance; the next
ordinary public outcome may differ. Thereafter a visible differing byte is
legal only if its field has that outcome event as an ancestor in the
controller's public taint DAG. `E2/E3` never permit immediate twin divergence.
Changing private future-goal bytes cannot affect a pre-reveal view; a mutated
fixture rejects rather than rendering at reveal. A score, arm label,
intervention metadata, or private receipt cannot affect any view. An
intervention may first differ only at the declared transformed
carrier slot or dispatch result after the actor reads/uses it.

The exact phase order is:

```text
OLD_DISCOVERY -> DREAM_OLD -> OLD_VALIDATION -> RENDER_OLD
 -> PROBE_A and PROBE_B (isolated forks of RENDER_OLD)
 -> GOALS_JOIN -> UNCERTAINTY -> ACQUIRE
 -> DREAM_NEW -> NEW_VALIDATION -> RENDER_NEW
 -> DELAYED_RESET -> DELAYED_GOAL -> FINAL
```

Illegal transitions emit no public event and mutate no state. Each probe has
four action slots. The only join bytes are:

```text
GoalsComplete := {v:2,type:"GOALS_COMPLETE",probes:[
  {probe:"A",goal:Goal,events:[ProbeSlot x 4]},
  {probe:"B",goal:Goal,events:[ProbeSlot x 4]}
]}
ProbeSlot := {kind:"EVENT",event:PublicEvent} | {kind:"PAD",event:null}
```

The order is always A,B regardless of execution order. These goal bytes and
ordinary public action/outcome events intentionally enter the acquisition
trunk. Nothing else does: no command/retrieval transcript, workspace,
dependency trace, repeat state, hidden correctness, path certificate, score,
termination/failure reason, wall time, execution order, or sibling handle.

`command_fingerprint = sha256("PCFL-CMD-v2\0" || canonical(command))`.
Consecutive identical commands without a reset or non-idempotent public
progress have counts 1, 2, then 3. Counts 1 and 2 return the same semantic
payload (and no duplicate evidence); count 3 returns `BLOCKED` without an
index/environment call. NOT_FOUND obeys the same rule. A lost-response replay
therefore cannot create a new event or evidence root. A different command
starts at count 1. Successful non-idempotent ACT, FINISH, or a reset clears the
fingerprint/count; failed actions do not.

- `PROBE_FORK`: retain the immutable old carrier; start from its checkpoint;
  clear branch public log, workspace, query cache, and repeat state.
- `GOALS_JOIN`: restart the trunk from the same old checkpoint; retain the old
  carrier; append only `GoalsComplete`; clear all branch-local state.
- `POST_SLEEP`: retain old plus admitted new public roots/carrier; clear
  workspace, query cache, and repeat state.
- `DELAYED_RESET`: retain old plus new admitted roots/carrier and nothing
  volatile; reveal the delayed goal only after the reset.

There is no runtime RNG: `k`, order, aliases, and all schedules are immutable
fixture fields. Probe forks cannot write the old checkpoint or one another.

## 4. Provenance, DREAM authorship, and carrier transforms

Provenance has exactly two node forms: primitive `ROOT(event_id,seq,payload)`
and synthetic `SYNTH(kind,seq,payload,parent_ids)`. Edges point from a node to
strictly earlier parents. Raw aliases resolve to canonical IDs before edge or
cycle checks. A node's evidential roots are the set union of primitive
ancestors; shared-root diamonds are legal and count the shared root once.
Self/forward/unknown citations, a cycle after alias collapse, or a synthetic
node offered as a primitive root reject. Synthetic re-expression never adds
evidence.

`DREAM_REF_CPU_V2` is the sole link author. At each DREAM cut it receives only
the admitted public primitive/synthetic DAG as of that sequence. In semantic
ID order it proposes every and only not-already-supported/revoked pair of
state atoms `(a,b)` with `a.dst == b.src`, recording its then-current primitive roots and the composite
prediction `(a.src,b.dst)`. It receives no goal, future schedule, twin bit,
arm, oracle, score, or intervention. A proposal is renderable only after later
primitive validation occurrences independently confirm both atoms and their
root set is disjoint from the proposal's root set. A later primitive event for
the same `(src,rel)` with another `dst` permanently marks the proposal
`REVOKED`; revoked links are not rendered. `RENDER_*` validates, pads, and
serializes only; it cannot create or repair a proposal. At CPU stage this
identifies reference-producer bytes, not child or cognitive authorship.
For the new link, `NEW_VALIDATION` is exactly the two-action public recheck
`B -R04-> C` followed by the already selected `C -R(07+h)-> D`; these create
fresh primitive event IDs after `DREAM_NEW` and expose no future goal.

The authentic old link slots, in order, are
`[(p0,p1),(p2,p3),(p1,p4),(p3,p4),(p4,p5),(p4,p6),NULL]`.
Pure carrier variants are:

- `ATOMS`: all seven link slots NULL;
- `AUTH`: the six links above, with slot 7 reserved for the later `p4->nh`;
- `TRUTHFUL_NULL`: identical slots explicitly stating no asserted link;
- `DERANGED`: `[(p0,p4),(p2,p4),(p1,p5),(p3,p6),(p4,p1),(p4,p3),NULL]`,
  all noncomposable;
- `BRIDGE_CUT`: AUTH with slots 3--6 NULL (all links incident to `p4`);
- `TWIN_REDIRECT`: AUTH with only the public destinations of `p5` and `p6`
  exchanged;
- `UNCERTAINTY_SHAM`: AUTH unchanged, but the public acquisition anchor is
  `Z0/Z1` rather than `H0/H1`;
- `REACHOUT_OFF`: AUTH unchanged, but READ-link dispatch returns BLOCKED;
- `OLD_CUT` / `NEW_CUT`: at delayed evaluation, mask respectively slots 1--6
  or reserved slot 7.

Every transform is total and may change only the named fields. Arm labels and
transform receipts remain private. Semantic padding, catalogs, budgets, and
slot counts are unchanged.

## 5. Constructive and uncertainty scores

A trace DAG contains public goal/state nodes, returned atom/link nodes, and
commands; edges are exactly command `deps`. A legal path score is one iff ACT
edges, in order, cite all atoms and authentic adjacent links of one complete
registered path class and the environment accepts the action sequence. Answer
score is separately one iff the terminal public state equals the goal target.
No answer, path, or shortcut score substitutes for another.

`trace_dependence=1` only if both registered counterfactuals pass:

1. masking the union of atoms/links in **all** successful path-equivalence
   classes makes the same trace fail path validation or abstain; and
2. substituting `TWIN_REDIRECT` while keeping the pre-read public prefix and
   command algorithm fixed changes the trace's decisive action to the twin's
   correct action. Retaining the old action is scored as a shortcut.

The scorer never asks the generator for a preferred parent path. Synthetic
fixtures include both legal alternatives, redundant-path masking, copied
answers, answer-only traces, cyclic deps, post-action deps, and twin-invariant
guesses.

Two deterministic conformance scripts, never called actors or models, supply
the positive and sham traces. `SCRIPT_PATH_V2` performs depth-first search in
public semantic-ID order using only legal READ returns, explores explicit
cursors, chooses the first complete minimum-cost path matching the visible
goal, and emits its ACTs with the returned atom/link IDs as deps.
`SCRIPT_CUE_V2` reads the prediction table only from the visible
`Uncertainty` projection and its public calibration citations, computes the
exact posterior below, chooses the
lexicographically least public experiment alias among tied maximizers, and
issues `COMMIT_b` only when the target-bit posterior is singleton; otherwise
it ABSTAINS. Both fit the declared budgets. They exist solely to test the
transition, trace, intervention, and reducer code.

Before acquisition the prior is uniform on the four `(h,z)` states. After
experiment `e` and outcome `y`, the posterior is the exact subset satisfying
the four equations in section 1. `realized_information=1` iff the posterior's
projection onto `h` has cardinality one; otherwise zero. Thus the tied
target-separating set is exactly `{E0,E1}` and `{E2,E3}` is nonseparating for
`h`; all actions and outcomes remain balanced. `experiment_choice=1` iff the
chosen action is in `{E0,E1}`. `acquisition_value=1` iff the subsequent equal-
cost command `COMMIT_b` has `b=h` and emits `nh`; a miss emits no atom.
`delayed_value=1` requires a valid delayed old-plus-new constructive trace.
The sham is truthful uncertainty about `z`: its tied maximizing set is
`{E2,E3}`, but following it yields zero target information. Choice,
information, acquisition, and delayed value are four noncompensatory fields.

## 6. Root reducer and failures

`reduce_stage0_root` accepts exactly one finalized canonical receipt for each
of the 64
registered root IDs. A root receipt contains every registered carrier/cut
cell once plus the separate path, answer, trace-dependence, shortcut-free,
experiment-choice, realized-information, acquisition, delayed, provenance,
prefix, reset, and transform-specificity bits. Probes, paths, calls, events,
branches, and cells are nested repeated measures and can never increase `N`.
Duplicate, missing, foreign, reordered, non-FINAL, or schema-noncanonical
receipts reject the whole reduction. There is no suite-level conditional
stopping, cell omission, or retry; a protocol-defined adverse terminal still
occupies its cell with zeroes. Reproducibility reruns must be byte-identical
but are not extra units.

The positive AUTH reference trace must have every positive field equal one.
ATOMS/NULL/DERANGED/BRIDGE_CUT/REACHOUT_OFF must have constructive trace zero;
TWIN_REDIRECT must change the decisive action and punish an unchanged answer;
UNCERTAINTY_SHAM must give target choice/information/acquisition/delayed zero
for the registered cue-following fixture; OLD_CUT and NEW_CUT must each give
delayed value zero. A root passes only if every observed bit equals this full
expected profile. Suite pass is the AND of all 64 root passes; no averaging,
margin, exclusion, or compensation exists.

Failure codes are closed:
`ABSTAIN`, `BUDGET`, `ILLEGAL_ACTION`, `MALFORMED`, `PRIVATE_HANDLE`,
`MISSING_ARTIFACT`, `PROVENANCE_REJECT`, `SUPPORT_REJECT`, and
`INTERNAL_ERROR`. Any non-OK code sets all unfinished behavioral fields to
zero. ABSTAIN/BUDGET and a grounded SUPPORT_REJECT are valid adverse outcomes;
ILLEGAL/MALFORMED/PRIVATE/MISSING/PROVENANCE invalidate the root and fail the
suite; INTERNAL_ERROR invalidates the suite. A support rejection admits no
link/new row and therefore forces acquisition/delayed zero. No failed cell is
dropped, rerun, or replaced.

## 7. Preimplementation byte-materialization gate

The equations above close the semantic choice set, but this advisory is not
by itself an exact-byte ratification packet. Before implementation authority,
a new deliberation artifact must contain, rather than promise to generate:

- canonical bytes and non-placeholder digests for all 64 root specifications,
  their 32-event ledgers, aliases/orders, paired-world certificates, both
  complete path classes, and distinct `WORLD_TWIN_PREFIX` and
  `CARRIER_TWIN_REDIRECT` certificates;
- canonical bytes/digests for every carrier/cut, phase view, join, reset,
  provenance status, uncertainty posterior, expected root vector, accepted
  golden, and expected-reject golden used below;
- a complete transition-table digest and the exact materializer and independent
  checker source/runtime identities. The implementation may verify this deck;
  it may not search seeds, accept/reject candidates, rank worlds, choose cuts,
  or replace a fixture after seeing a test result.

No renderer or tokenizer is permitted or required: complete-event cuts are
the phase/event boundaries above. No timing, energy, memory, power, or
throughput threshold is part of Stage 0, so no unspecified performance fixture
or host-power certificate can become a hidden gate. `DEV_NONCLAIM` is an
output-ineligibility label, not a scientific DEV split or lineage-authority
permission. The current task intentionally generates none of these bytes; the
missing materialized manifest is why this note remains advisory and cannot yet
be ratified or implemented.

## 8. Exact Stage-0 acceptance suite

After the materialization gate, all tests are CPU property tests over the
complete frozen 64-root universe and all named variants; no sampled, generated,
or replacement root is permitted.

1. `S0-MANIFEST-00`: verify every required byte/digest is present and real,
   both independent checkers reproduce the frozen transition-table digest,
   and the runtime contains no selection, tokenizer, model, performance, or
   network dependency.
2. `S0-ALGEBRA-01`: enumerate the algebra and exact path classes; prove no
   single-record closure, A/B distinction, bridge necessity, and delayed
   old-plus-new necessity.
3. `S0-PREFIX-01`: prove twin visible-prefix byte equality, all declared
   balance laws, E2/E3 nondivergence, first-separating-outcome divergence, and
   public-taint closure; mutate each forbidden private field in turn.
4. `S0-BYTES-01`: golden canonical bytes for every closed type and phase,
   strict round trips, fixed pads, semantic IDs, Unicode/duplicate/float/
   unknown-field negatives, and zero model-facing artifacts.
5. `S0-CAPABILITY-01`: enumerate every actor-view field, anchor, catalog,
   ordering, cursor, padding, status, and error path; prove no private handle
   resolves and goals/schedules cannot alter DREAM, carrier, index, or reader
   ordering. Only actor command bytes may select a legal public anchor.
6. `S0-PHASE-JOIN-01`: exhaust legal and illegal histories; byte-diff the
   exact GOALS_COMPLETE projection; inject workspace, retrieval, trace,
   correctness, failure, order, timing, and sibling fields and require reject.
7. `S0-REPEAT-RESET-01`: exhaust FOUND, NOT_FOUND, BLOCKED, lost-response
   replay, progress, budget, every reset, both fork orders, and cross-branch
   mutation attempts.
8. `S0-PROVENANCE-DREAM-01`: proposal-before-support, disjoint later roots,
   root dedupe, aliases, synthetic non-evidence, legal diamonds, true cycles,
   descendant citations, contradictions/revocation, and proof that renderer or
   goal/private mutations cannot author a link.
9. `S0-CARRIERS-01`: compare the complete exposure vector and prove each
   authentic/null/deranged/bridge/twin/sham/reachout/old/new transform changes
   only its declared semantic target.
10. `S0-UNCERTAINTY-01`: enumerate all `(k,h)`, actions, outcomes, posteriors,
   ties, costs, aliases, and shams; separately verify choice, realized
   information, acquisition, and delayed values.
11. `S0-TRACE-01`: accept both legal path classes and legal diamonds; reject
    answer-only, copied, cyclic, post-hoc, atom-masked, all-path-masked,
    bridge-cut, and twin-invariant shortcut traces.
12. `S0-REDUCER-01`: adversarial missing/duplicate/nested/reordered/foreign/
    malformed/failure receipts, all adverse mappings, `N=64`, no retry or
    conditional stop, and deterministic byte-identical replay.

Passage yields only a hash-bound `DEV_NONCLAIM` software receipt. Any test
failure blocks Stage-0 completion; it cannot be repaired by a later model or
scientific result.

## Ratification boundary

This proposal deliberately resolves only the consensus's CPU semantic
blockers: exact finite relations, paired histories, public capabilities and
queries, join bytes, repeat/reset state, provenance and reference-DREAM
authorship, constructive credit, uncertainty, carrier isolation, failures,
root reduction, and canonical CPU bytes. Recurrence/model baselines,
noncompensatory scientific endpoints, statistical contracts, confirmation
feedback, lineage authority, transaction/CAS, E0 binding, transport/resource
factorials, L, C, accumulation, online flywheels, and negative scientific
claim dispositions remain absent because they have no Stage-0 claim to
govern. They require new exact proposals and human approval; none is silently
defaulted here. The next permissible architecture step is therefore the
materialized, independently checked Stage-0 manifest—not implementation and
not revival of the earlier D0 bundle.
