# PCFL D0 exact v2 schema, reader, and compiler manifest

**Change:** `chg_20260901_pcfl_d0_exact_v2`  
**Scope:** D0 reference contracts and fixtures only  
**Schema version literal:** `PCFL_D0_EXACT_V2`

This manifest binds the schema/reader/compiler portion of the successor D0
bundle. It is a design input to deliberation and ratification, not authority to
implement D0, call a model, load weights, train or read a LoRA, use a GPU or
remote service, run a scientific cell, or make a scientific claim. A green D0
test of these artifacts means reference-contract/checker conformance only.

## Bound artifacts

| Path | Bytes | SHA-256 |
|---|---:|---|
| `schemas/pcfl_d0_objects.schema.json` | 45,097 | `cf1cd5445651f5b3476f013a3e71151aa1eff266d0c70ceee212f91ce925f905` |
| `reader_contract.json` | 13,508 | `4634d2f2a53405231d6b6f08d0056cce11e04cabb1ef9ca337d8992ba6e5e1c4` |
| `compiler_contract.json` | 12,609 | `a99651480d9848e31c91785dba1c78027f447cf97b20d8e695a34c0797679020` |
| `golden/canonical_examples.jsonl` | 14,727 | `8d5561f9a768eb26e5ad5968199bf558a78f41f90f602413fa5d56b8e4308e0b` |

The JSONL contains 19 positive, standalone canonical examples: goal, state,
event, workspace, copied and model-derived-transform queries, both read results,
proposal, status, snapshot, a reference to the authoritative standalone
resource ledger, all four compiler views, a complete pre-action twin collision
certificate, a global S-bind manifest, and a memory-only matched-cut twin
intervention certificate. Atom and compiler-view identity hashes in the
examples are recomputable from the normative projections. Certificate digest
members illustrate the closed certificate wire shape; an integrated generator
fixture must replace them with independently computed bytes and hashes.

## Governing sources and resolved v1 concerns

The contract was derived after complete reads of `AGENTS.md`,
`research_notes/47_pcfl_execution_bundle_v1.md`, the v1 THINK, DREAM, and
memory-recognizer prompt files, and the v1 critique and consensus. Within this
successor proposal it makes the consensus-selected resolutions explicit:

- **G02:** exactly four views, everywhere. The stale six-view S-bind wording is
  superseded: `FORWARD_COMPLETION`, `REVERSE_COMPLETION`,
  `INCIDENT_EDGE_RECALL`, and `ONE_MEMORY_STATEMENT`, exactly once each per
  eligible atom.
- **G04:** the primary interface is generic `QUERY_LOCAL(anchor)` only. The
  catalog, forward/reverse incidence, ordering, repeats, item-wide atom dedup,
  discard tombstones, slot placement, copy origins, fresh-instance/family
  bridge, explicit resolver-derived transform anchors, and numeric budgets are
  fixed. Every frozen A2/A3 target must receive
  an exhaustive generic-reachability certificate. Typed query is absent and
  remains a separately reported ceiling.
- **G04 collision:** every paired target requires a complete pre-action
  certificate over the system prompt, goal, state, workspace, last read,
  repeat state, budgets, full resolver input, exposed snapshot handle,
  candidate catalog/order, return envelope, and timing class. The registered
  correct preparation sets must still be disjoint.
- **G05:** S-bind is one claim-level, fixed-point-free global permutation that
  is propagated to identities and every co-reference. Its products are
  explicitly control-corrupted and never lifecycle truth. Twin substitution is
  legal only at a byte-colliding decision cut or as a complete simulator-
  reachable matched-twin-state fork with every changed pointer registered.

## Canonical byte contract

The order is normative:

1. Decode strict UTF-8 while detecting and rejecting duplicate keys.
2. NFC-normalize every member name and string value.
3. Reject any member-name collision created by NFC normalization.
4. Validate the normalized value against the closed schema.
5. Serialize with RFC 8785/JCS.
6. Require the accepted wire bytes to equal those JCS bytes followed by exactly
   one LF.

Consequently a non-NFC wire spelling does not receive a second accepted form:
normalization occurs before JCS and the final byte-equality check rejects the
noncanonical input. Floats, `null`, unknown keys, duplicate keys, invalid
handles, invalid enum spelling, invalid UTF-8, and extra/missing LFs fail
closed. Hash projections omit the final LF unless the field definition
explicitly says it hashes a wire artifact.

## Exact handle and semantic enums

All handles are eight ASCII bytes.

| Kind | Form |
|---|---|
| mission | `M[0-9A-Z]{7}` |
| specimen instance | `X[0-9A-Z]{7}` |
| site instance | `S[0-9A-Z]{7}` |
| route instance | `R[0-9A-Z]{7}` |
| public event | `E[0-9A-Z]{7}` |
| public root/source block | `B[0-9A-Z]{7}` |
| preparation instance | `P[0-9A-Z]{7}` |
| exposed snapshot coordinate | `Q[0-9A-Z]{7}` |
| specimen class | `X[0-9A-Z]{7}`; NodeRef kind distinguishes it from an instance |
| preparation family | `P[0-9A-Z]{7}`; NodeRef kind distinguishes it from an instance |
| site family | `S[0-9A-Z]{7}`; NodeRef kind distinguishes it from an instance |
| route family | `R[0-9A-Z]{7}`; NodeRef kind distinguishes it from an instance |

Trait keys are exactly `T0`, `T1`, `T2`, `T3`; values are `ZERO` or `ONE`.
Transform-template values are `SET_T0_0`, `SET_T0_1`, `SET_T1_0`,
`SET_T1_1`, `SET_T2_0`, and `SET_T2_1`. Predicate-template values are `F0`,
`F1`, `F2`, and `F3`, with frozen public meanings `t0 AND t3`, `t0 OR t3`,
`t1 XOR t3`, and `(NOT t0) AND (NOT t3)`. Route-requirement values are `G0`,
`G1`, and `G2`, with frozen public meanings `t0=1`, `t1=0`, and `t2=1`.
Relations are exactly `PREPARATION_TRANSFORM`,
`SITE_PREDICATE`, and `ROUTE_REQUIREMENT`.

A NodeRef has exactly `kind` and `value`, with the kind/value pairing enforced
by schema. A canonical atom has exactly `atom_id`, `object`, `relation`, and
`subject`. Its ID is:

```text
sha256(NFC-before-JCS({"object":...,"relation":...,"subject":...}))
```

The digest input has no LF. Preparation families can point only to transforms,
site families only to site predicates, and route families only to route
requirements.

The reusable mapping endpoint kinds are exactly `PREPARATION_FAMILY` to
`TRANSFORM_TEMPLATE`, `SITE_FAMILY` to `PREDICATE_TEMPLATE`, and
`ROUTE_FAMILY` to `ROUTE_REQUIREMENT`. Instance/family prefix reuse is never
resolved by the string alone; the schema-valid NodeRef kind is mandatory.

The exposed `Q` snapshot handle is deliberately an opaque per-life namespace
coordinate, not a content hash. Paired isolated lives can therefore expose the
same `Q` bytes while resolving distinct authentic twin memories; the private
content digests remain in the audit-only snapshot manifest and never enter the
reader input.

## Closed object keys

Every object also has the exact literal `schema_version`; all keys below are
required unless a schema `oneOf` selects a smaller variant.

| `object_type` | Exact top-level data keys besides `schema_version` |
|---|---|
| `PUBLIC_GOAL` | `mission_handle`, `object_type`, `objective`, `site_handle`, `specimen_handle` |
| `PUBLIC_STATE` | `applied_preparations`, `budget`, `inventory`, `last_public_outcome`, `object_type`, `site`, `specimen`, `step_index`, `surveyed_route` |
| `PUBLIC_EVENT` | `action`, `event_handle`, `event_index`, `intervention_cluster_root`, `object_type`, `outcome`, `source_block_handle`, `token_end`, `token_start` |
| `SEMANTIC_WORKSPACE` | `discarded_edge_slots`, `memory_slots`, `object_type`, `outcome_slots`, `path`, `typed_nodes` |
| `READER_QUERY` | `already_returned_candidate_ids`, `anchor`, `copy_origin`, `object_type`, `operation`, `query_index`, `snapshot_handle` |
| `READ_RETURN` | FOUND: `atom`, `object_type`, `result`; NOT_FOUND: `object_type`, `result` |
| `CLAIM_PROPOSAL` | `atom`, `object_type`, `parents`, `prediction`, `proposal_id`, `roots` |
| `STATUS_EVENT` | `atom_id`, `claim_id`, `evidence_root_handles`, `event_ordinal`, `object_type`, `parent_claim_ids`, `prediction_event_handles`, `reason`, `snapshot_handle`, `status_event_id`, `transition` |
| `SNAPSHOT_MANIFEST` | `adapter`, `artifact_digests`, `compiler_input_atom_ids`, `cut`, `eligible_atom_ids`, `object_type`, `sealed`, `snapshot_handle`, `source_prefix_sha256` |
| `RESOURCE_RECEIPT_REF` | `ledger_path`, `ledger_sha256`, `object_type`, `summary` |
| `COMPILED_VIEW` | `anchor`, `atom`, `completion`, `control_taint`, `edge_count`, `object_type`, `prompt`, `view_id`, `view_kind` |
| `PREACTION_TWIN_COLLISION_CERTIFICATE` | `certificate_id`, `components`, `different_correct_assignments`, `left_world_commitment`, `object_type`, `registered_answers`, `right_world_commitment`, `valid` |
| `S_BIND_MANIFEST` | the global map plus exact alias/answer/candidate/root/return digests, lifecycle taint, four-view counts, envelope equality, and root audit fields bound in schema |
| `TWIN_INTERVENTION_CERTIFICATE` | `all_unlisted_bytes_equal`, `changed_pointers`, `collision_certificate_id`, `intervention_id`, `mode`, `object_type`, `replayed_reachable`, `source_cut_sha256`, `twin_cut_sha256`, `valid` |

`RESOURCE_RECEIPT_REF` is not a second resource ledger. Its digest/path points
to the sole authoritative `resource_ledger.schema.json` artifact owned by this
successor bundle; its five summary counters are convenience receipts only.

The public goal has no route, preparation, rule, terminal action, predicate,
answer, candidate, or suggested subgoal. The public state contains public
bindings and observations only. The workspace has no notes, rationale,
confidence, proof, agenda, hidden ID, or chain-of-thought field. Proposal
closure excludes truth/status/importance/confidence/proof/goal/target/action
keys. Read-return closure excludes candidate ID, rank, score, provenance,
confidence, backend, count, token count, truncation, latency, alternative, and
orientation.

## Copy-origin and generic query contract

The only primary query is `QUERY_LOCAL`. It carries exactly one NodeRef anchor
and one closed `copy_origin`. In `COPIED` mode, the runtime resolves the cited
pointer in a sealed `GOAL`, `STATE`, `OUTCOME_SLOT`, `READ_SLOT`, or `PATH_SLOT`
and requires the source scalar to byte-equal `anchor.value` after
NFC-before-JCS. Substring, concatenation, description lookup, alias expansion,
inferred family, hidden lookup, coercion, and goal-derived search strings are
invalid.

`MODEL_DERIVED_TRANSFORM` is the sole non-copy mode. The resolver selects one
of the six frozen `TRANSFORM_TEMPLATE` enums and cites exactly one earlier
predicate/requirement path slot, optionally the already selected first-transform
path slot for the second A3 derivation, plus the exact current public trait slots
used in its reasoning. The runtime checks syntax and that those cited public slots
exist. It never computes, corrects, scores, confirms, or provides feedback on
the transform. A wrong derived anchor consumes its query and operation normally.
Only an offline trace checker may later test logical entailment under the frozen
F0..F3/G0..G2 ontology for composition credit. This is explicit resolver
reasoning, not a target-specific literal, projection oracle, or hidden join.

Fresh target handles reach reusable memory through public bindings, not a
reader join:

```text
PREPARATION instance --public state--> PREPARATION_FAMILY --QUERY_LOCAL--> transform
SITE instance        --public state--> SITE_FAMILY --QUERY_LOCAL--> predicate
ROUTE instance       --SURVEY outcome--> ROUTE_FAMILY --QUERY_LOCAL--> requirement
```

The catalog is frozen before target generation and contains every syntactically
legal true and false one-edge atom over reusable family vocabulary. Each atom
is indexed under its subject (`FORWARD`) and the same atom ID under its object
(`REVERSE`). The reverse entry is not a second atom and not an inverse causal
claim. Incident ordering is the exact byte tuple in `reader_contract.json`.
The reader receives only the opaque snapshot coordinate, canonical query, and
runtime-maintained already-returned IDs.

On FOUND, the runtime returns only the canonical atom. The same query advances
to the next ordered eligible unseen atom. NOT_FOUND blocks the same fingerprint
for the rest of the item/snapshot. Dedup is global within item by atom ID across
anchors, both index directions, views, repeats, workspace eviction, and path
discard. Eviction never resurrects a return. BACKTRACK records immutable
slot IDs for the removed edge and later path ordinals as permanent item-local
tombstones; those slots are not reused. UPDATE_PATH copies one atom, then clears its memory
slot. There is no automatic overwrite; a full four-slot memory yields
`BLOCKED_MEMORY_FULL`, never NOT_FOUND. A backend error is an item failure and
never a negative return.

## Numeric budgets and reachability

THINK has exactly four `QUERY_LOCAL` operations, four FOUND returns, eighteen
total resolver operations, six world actions, four memory slots, six outcome
slots, sixteen typed nodes, and four active path edges per item. Every query, path
update, backtrack, world action, defer, stop, proposal, or blocked output costs
one resolver operation; a world action also costs one action. The second
blocked output ends the item at value zero.

An A2 reference path reads site family to predicate, derives a transform, reads
that transform in reverse to its preparation family, performs two path updates,
and uses three actions: seven operations. An A3 reference path reads site and
route forward, independently derives the two required transform templates,
reads each transform in reverse to a preparation family, performs four path
updates, and uses six actions: fourteen operations. Four operations remain for
adaptive backtrack/defer/stop. This removes the v1 eight-operation dead-end
while retaining four bounded generic reads. Every accepted target, both
twins, every target-legal anchor acquisition order, the canonical incident
order, repeated-FOUND prefixes, tombstones, and budget transitions must pass
the exhaustive reachability certificate before the generator version is
usable.

DREAM has four preallocated samples per replay bundle. Each sample has two
queries, five total resolver operations, two backtracks, and zero world
actions. This permits two query/update pairs and one proposal. A malformed
sample consumes its slot and is not replaced.

## Exactly four compiler views

Eligible input is the alias-resolved, atom-ID-deduplicated set whose latest
status at the sealed snapshot is `SUPPORTED`. No other status and no tainted
control produces authentic positive data. Old/new and relation buckets use the
exact round-robin and atom-ID ordering in `compiler_contract.json`.

For every eligible atom the compiler emits, in order:

1. `FORWARD_COMPLETION`: subject + relation completes the object.
2. `REVERSE_COMPLETION`: object + relation completes the subject.
3. `INCIDENT_EDGE_RECALL`: a generic subject anchor completes the one full edge.
4. `ONE_MEMORY_STATEMENT`: one full edge and nothing else.

The exact ASCII templates and `kind:value` NodeRef rendering are bound in the
compiler contract and represented in the golden JSONL. Each view contains the
same one atom and `edge_count=1`; no target, status, proof, provenance, plan,
terminal action, or multi-edge closure is legal. The compiler emits one of each
view. Later training repetitions, if separately authorized, are recipe
exposures and never support.

## Coherent S-bind

S-bind begins only after the authentic atom set, aliases, root projections,
four views, candidate membership, answer slots, returns, corpus manifest, and
training envelope are frozen. It forms the exact strata in the compiler
contract and deterministically chooses the smallest legal cyclic shift over
atom-ID-sorted claims. Every row must change both donor claim and object. The
source/donor map is a bijection. If a stratum cannot derange, only the declared
single adjacent answer-token-length-bin merge is legal; otherwise the control
fixture/generator is invalid before model calls.

The map is applied once at canonical-claim level. The rebound object produces a
new atom ID, and that same mapping rewrites aliases, tainted control root
projections, all four views, candidate/query membership, answer slots, read
returns, and manifests. Authentic roots, lifecycle logs, snapshots, and corpus
remain byte-unchanged. Control products carry
`CONTROL_CORRUPTED_S_BIND` and `NOT_A_LIFECYCLE_CLAIM`; they cannot masquerade
as SUPPORTED truth or add support. A root audit requires every rebound atom to
match its rewritten control root projection while every authentic root byte
remains unchanged. The object multiset, answer marginals, four view counts,
candidate counts, registered strata, and full training envelope are preserved.

## Valid twin interventions

`MEMORY_ONLY_AT_COLLIDING_CUT` is legal only when a certificate proves every
non-memory byte collides at the exact decision cut. It changes only the complete
registered minimal cut of memory atoms and dependent path copies, cuts all
redundant cited paths, and requires the decisive operation to become the
registered twin-valid action or unordered set.

If prior swapped actions have made public states diverge, memory-only
substitution is forbidden. `MATCHED_TWIN_STATE_FORK` independently replays the
twin simulator to the matched decision index and takes the complete reachable
twin goal/state/outcomes/repeat/budget/memory/path. Every changed canonical JSON
pointer is registered; every unlisted byte collides. The action is judged
against that coherent twin state and is not described as a memory-only effect.
Editing only traits, retaining impossible original outcomes, or otherwise
creating a hybrid state invalidates the certificate.

## Validation obligations

Before these bytes are proposed for ratification, validation must establish:

- all three `.json` files parse as JSON and the schema itself is Draft 2020-12
  well formed;
- all 19 JSONL lines parse, match exactly one top-level schema branch, contain
  no unknown key, and equal their sorted integer-only RFC-8785/JCS form plus LF;
- the four example atom/view digests recompute;
- every file has exactly one terminal LF and no CR;
- forbidden primary query keys and forbidden read/proposal/workspace keys fail;
- wrong handle prefixes, lowercase handles, floats, nulls, duplicates,
  non-NFC spellings, normalized-key collisions, and bad LF counts fail;
- four-view cardinality, compiler ordering, S-bind global co-reference, root
  compatibility, collision equality, and matched-state reachability are checked
  semantically in addition to JSON Schema validation.

None of these validations promotes D0 or supplies evidence about a future
model, recognizer, provider, A-MEM backend, LoRA, trained substrate, or
scientific mechanism. Those exact systems must rerun their separately
authorized black-box/process and causal-credit audits.
