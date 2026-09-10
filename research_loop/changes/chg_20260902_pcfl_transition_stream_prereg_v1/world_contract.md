# PCFL Transition-Path world contract

Status: proposed material design. This file is inert until the exact successor
intake is ratified. It specifies only the P0/P1 preflight; it is not a final
paper benchmark and is not evidence.

## 1. Construct and non-constructs

The preflight asks one narrow question: can a pinned resolver use
target-blind, mechanically compiled public transition witnesses to execute a
fresh four-move path whose required bindings were witnessed at two different
source epochs?

It measures fixed-source acquisition/retention and action-use of transition
bindings through dependent reverse traversal. It does not identify autonomous
dreaming, a learned compiler, learned graph organization, LoRA transport,
compression, on-policy evidence acquisition, a self-improving flywheel,
general long-lifetime competence, or a paper benchmark. A flat atom bag and an
exact public graph are mandatory controls. The reverse index and all index
construction/work bytes count as external memory.

## 2. Deterministic world family

One world-life has eight persistent full binary trees. Each tree has depth four,
15 internal state classes, and 16 leaf state classes. Every internal class has
the same two world-global opaque action IDs. For internal node `u`, an
independent hidden bit `b[u]` selects which action reaches the topological left
child; the other action reaches the right child. Thus a tree contains exactly
15 independent transition-binding bits and a root-to-leaf D4 path requires
four independent bits.

Topology-side names `left` and `right`, tree indices, node coordinates, hidden
bits, and support-age classes exist only in the trusted constructor/certifier.
Every public state, action, episode, event, and target handle is an independently
permuted fixed-width 18-character lowercase ASCII token. No token contains a
tree, depth, path, era, twin, side, target, or answer marker. The ID-permutation,
source-order, target-allocation, and binding-bit streams are domain-separated.
P0 holds the first three fixed while exhaustively enumerating the four decisive
bits, so the target-only prior is an exact combinatorial result rather than an
assumption about a hash function.

The generator order is total and rejection-free:

1. Allocate topology, opaque-ID permutations, node-age templates, source order,
   target topology, goal pairs, and cut/sham sets without binding bits.
2. Sample all binding bits once.
3. Derive the authentic hidden transition table and its twin.
4. Seal the target/certificate manifest and its SHA-256 before emitting any
   public source event.
5. Emit the fixed source deck. No observed outcome changes a later action,
   target, ordering decision, retry, or retained record.

No target is rejected or replaced. A duplicate, malformed record, missing
support, compiler omission, read failure, timeout, parse failure, or runtime
failure remains attached to its assigned world-life and target.

## 3. Whole-life twins

For hidden world `H`, `tau(H)` complements all 120 node bits and changes nothing
else: opaque IDs, topology, global action IDs, source start-state schedule,
chosen source actions, source event count/order/shape, age templates, target
inputs, goal-pair allocation, caps, and cut/sham positions are identical.
Observed source next states differ because the bindings differ. Applying `tau`
twice returns `H` exactly.

The indivisible unit is `(pair_root, H, tau(H))`. H and tau sides are nested,
as are targets, goal twins, arms, reads, actions, and any provider calls. No
nested observation is an independent replication.

## 4. Source policy and public event schema

The source policy is a deterministic, target-unaware coverage deck. For each of
the 120 internal nodes it starts two fresh one-step practice specimens at that
node and executes each global action exactly once. The action order inside a
node block and the order of node blocks are sealed by the source-order stream.
Every choice has propensity `1`; propensities live in the private policy ledger
and never select or weight a target. The public outcome from one action is
recorded before the next presealed event, but the policy never branches on it
and never retries.

Each node has a presealed age class. All `old` node blocks occur before snapshot
`M0`; all `recent` node blocks occur between `M0` and `M1`. No old node is
revisited after `M0`. The two different actions are two direct witnessed edges,
not a proposal/verification pair. Any repeated deterministic observation in a
future design would be only repeated evidence and must never be called
independent verification.

Each life therefore assigns exactly 240 source action slots. A valid slot is
serialized as one JCS JSON object plus one LF with exactly these fields:

```json
{
  "schema_version": 1,
  "event_id": "eeeeeeeeeeeeeeeeee",
  "episode_id": "pppppppppppppppppp",
  "state_id": "ssssssssssssssssss",
  "available_action_ids": ["aaaaaaaaaaaaaaaaaa", "bbbbbbbbbbbbbbbbbb"],
  "chosen_action_id": "aaaaaaaaaaaaaaaaaa",
  "outcome": {
    "kind": "ARRIVED",
    "next_state_id": "tttttttttttttttttt"
  },
  "cost": 1
}
```

`available_action_ids` is lexicographically sorted. An assigned environment
failure occupies the same slot and shape with `kind="ENV_ERROR"` and an
all-zero 18-character sentinel for `next_state_id`; there is no retry. The
public stream contains no rule statement, transition-table row, proof, path,
depth, age, tree/cohort ID, target/goal, support label, twin side, optimal
action, or score. Line position is the only chronology signal.

The immutable source bytes for a world side are shared by every arm using that
side. Evaluation actions never enter the source deck, compiler, `M0`, or `M1`.

## 5. Support and coverage denominators

For a node, its binding becomes `introduced` when its first assigned source
slot is emitted. It becomes `supported` only after valid `ARRIVED` events for
both global actions have been observed. An individual edge is witnessed by its
own valid event. `compiled` means the canonical edge atom is present;
`readable` means both registered lookup directions return its exact atom hash;
`action-usable` means an assigned target using it receives value one.

Allocated, introduced, supported, compiled, readable, and action-usable counts
are all reported, never substituted for one another. Target inclusion is based
only on the presealed topology/age template, never any realized denominator.

## 6. Target input, depth, age, and goal pairs

Every public target input is one JCS object with the same caps and shape:

```json
{
  "schema_version": 1,
  "current_state_id": "ssssssssssssssssss",
  "available_action_ids": ["aaaaaaaaaaaaaaaaaa", "bbbbbbbbbbbbbbbbbb"],
  "goal_state_id": "gggggggggggggggggg",
  "limits": {
    "memory_reads": 4,
    "moves": 4,
    "commit": 1
  }
}
```

The hidden manifest, not the public input, records `D1`/`D4` and
`new`/`old`/`cross-era`.

- D1: start is the goal leaf's direct parent. The unique successful path has
  one binding-dependent move followed by `COMMIT`; exact target-only value is
  `1/2`.
- D4: start is the root and the goal is a depth-four leaf. The unique
  successful path has four binding-dependent moves followed by `COMMIT`; exact
  target-only value is `1/16`.
- new: every decisive node binding is supported between `M0` and `M1`.
- old: every decisive node binding is supported before `M0` and is not
  revisited afterward.
- cross-era D4: one ordinary root-to-leaf path in one persistent tree has
  exactly two old and two recent node bindings. There is no public handoff,
  portal, transfer action, reset, join card, or target-specific transition.
  The two recent depth positions range once each over the six lexicographically
  ordered subsets of size two from `{0,1,2,3}` across the six P1 pair roots.
- D1 cross-era is structurally absent because one decisive binding cannot have
  two support ages. It is recorded as `STRUCTURALLY_ABSENT`, not zero and not
  `NOT_RUN`.

For each target, a goal twin keeps every public byte fixed except the
fixed-width `goal_state_id`. The paired goals are leaves in opposite root-child
subtrees, so the correct first action must differ. In P0 fixtures, D1 and every
D4 age cell have goal pairs. In P1, both goals are run in the authentic and
target-only arms; registered sparse interventions use the primary goal only.

Target allocation is independent of binding bits. Holding the exact public
target bytes, topology/age allocation, and ID permutation fixed while
enumerating the decisive bits yields each length-`d` global-action sequence
exactly once. The exact target-only Bayes value is therefore `2^-d`, including
after conditioning on age cell and goal member. H/tau target bytes are
identical. A fitted shortcut screen uses only disjoint P0 roots and can never
replace this exact orbit certificate.

## 7. Canonical compiler and memory objects

`WCANON-T1` is a deterministic witness canonicalizer, not DREAM and not a
learned, prompted, verifier-assisted, or goal-conditioned writer. It consumes
only a sealed public prefix (`M0` or `M1`). For every valid `ARRIVED` event it
emits the immutable atom

```text
TRANSITION(parent_state_id, chosen_action_id, child_state_id,
           provenance_event_id, provenance_event_sha256)
```

in canonical byte order. It neither uses complement inference nor consults
hidden topology. Conflicting children for the same `(parent, action)` are
retained append-only, marked `CONTRADICTED`, and made unreadable; omissions and
errors remain in coverage denominators. Corpus bytes freeze before arm
assignment.

Three public-evidence objects are distinguished:

1. `LINKED_TEXT`: canonical atoms plus a reverse index `child -> atom_id` and a
   forward index `(parent, action) -> atom_id`.
2. `FLAT_ATOM_BAG`: the byte-identical atoms in a target-independent order with
   no stored adjacency or endpoint index. Its reader scans every atom.
3. `EXACT_PUBLIC_GRAPH`: the exact adjacency structure reconstructed
   mechanically from eligible public atoms. It is a deterministic ceiling and
   strong sufficient-statistic control, never an oracle built from hidden
   truth.

Index keys, pointers, serialization, caches, and construction/query work are
information-bearing state and are counted. If `FLAT_ATOM_BAG` matches linked
text, link organization is unnecessary. If the exact graph dominates, that is
reported. Neither outcome permits a connected-memory or graph-discovery claim.

## 8. Reader and resolver interface

The typed reader has two exact operations:

```text
PREDECESSOR(child_state_id) -> one immutable transition atom | NOT_FOUND
SUCCESSOR(parent_state_id, action_id) -> one immutable transition atom | NOT_FOUND
```

`LINKED_TEXT` uses its indices. `FLAT_ATOM_BAG` implements the same return
semantics by a complete counted scan. The model-facing P1 resolver receives
only `PREDECESSOR`; `SUCCESSOR` is used by P0 reachability and typed-controller
certification. A response has a fixed schema and fixed-width fields. A
`NOT_FOUND` response uses fixed sentinel fields; ranks, candidate counts,
filenames, timing, cache hits, and scan progress are never model-visible.

For a valid D4 authentic read, query 0 must name the public goal. Every later
query must name the parent returned by the immediately preceding atom. After
four successful dependent reads, the final parent must equal the public start.
This is a reverse traversal of connected transition content; a request for all
life atoms, all candidates, an unbounded search result, a state not visible in
the target or preceding return, or more than four reads is rejected.

The pinned model then emits one strict JSON operation list containing four
`MOVE(global_action_id)` operations and one `COMMIT`, with no prose, state IDs,
answer string, proof, or hidden score. The model session closes before
execution. The executor applies each move to the actual world state in order;
`COMMIT` returns one only at the goal. Wrong branches cannot be repaired within
four moves. Only the executed public state trajectory and terminal return are
scored. A plausible plan string, citation, or reported leaf receives no
credit. This is a sealed batch action episode, not an interactive/on-policy
episode; target outcomes never cause later evidence or recompilation.

## 9. Decisive interventions

- Whole-life cross: run H targets with `M1_tau` and tau targets with `M1_H`.
  Directional credit requires the emitted path to fail in the actual world and
  succeed when replayed in the memory-matched counterpart world.
- Lagged snapshot: use `M0` on a cross-era target. The two recent bindings are
  absent by construction.
- Old cut: before reader construction remove both outgoing action atoms,
  forward/reverse entries, candidates, and caches for the two old decisive
  nodes.
- New cut: the same operation for the two recent decisive nodes.
- Both cut: remove all four decisive node bindings.
- Sham-old, sham-new, and sham-both: remove the same number of complete node
  bindings with matching depth and age from distractor trees that lie on no
  assigned goal path. A depth-zero sham comes from a distractor-tree root.

Cuts are defined from the sealed environment certificate before any model
output. Removing a displayed citation is not a cut. P1 contains no LoRA, so no
claim about a distributed-weight intervention is available.

## 10. Split roots

Roots are derived by SHA-256 domain separation over the literal UTF-8 prefix
`pcfl-transition-path-v1`, split name, and zero-padded decimal index. P0 may
materialize only `p0-fixture/000000` through `p0-fixture/000031`. P1 may
materialize only `p1-canary/000000` through `p1-canary/000005`; these six roots
are never used to modify generator, compiler, prompt, reader, thresholds, or
code. Pair index `j` receives recent-depth subset `j` in lexicographic order.
No confirmation roots are allocated by this change.

The P1 target/compiler split is enforced causally: the trusted allocator seals
the target manifest, the compiler receives only source bytes, and target bytes
are released to a fresh resolver process only after the corpus and arm object
hashes freeze.
