# v2 shared resolver reducer

The reducer consumes only schema-valid JCS envelopes. Its state is the closed
tuple

```text
(phase, lane, resolver_ordinal, operations_remaining, reads_remaining,
 raw_output_tokens_remaining, workspace_nodes, node_capability_map,
 staged_object_map, candidate_catalog, public_handle_receipts,
 last_model_read_result, query_cursor, action_prefix, terminal_status)
```

`resolver_ordinal` is the zero-based number `r` for the next recurrent
opportunity. The rendered `resolver_state.resolver_ordinal` is exactly `r`;
the enclosing `INPUT_ENVELOPE.operation_ordinal` and accepted model-authored
`RESOLVER_STEP.ordinal` are both exactly `r+1`. This is the sole mapping to the
zero-based `resolver_ordinal` in `rng_contract.json`, and every field named
`operation_ordinal` is one-based.

Capabilities and other model-visible identifiers are fixed-shape,
deterministically ordinal-derived session tokens held in maps, never content
addresses. The derivation is owned by the dedicated
`model_visible_identifier` namespace supplied by `rng_contract.json`; this
reducer contract does not design or restate its HMAC. Public event/raw-A
handles are direct kind-plus-one-based-source-ordinal labels. Their opaque
receipt refs, Dream-1 candidate handles and read capabilities,
target-memory handles and read receipt refs, and authored node/object
capabilities use only declared topology and ordinals. Values are byte-identical
across corresponding paired treatments when topology corresponds. Content,
treatment, model output, digests, paths, lengths, lane variants, cache state,
and dedup state are forbidden identifier inputs; a collision or paired-value
mismatch is terminal.

## Transition order

For every recurrent opportunity the harness first decrements the operation and
raw-token budgets. It parses with duplicate-key/Unicode/I-JSON rejection,
canonicalizes, validates the root branch of `semantic_dsl.schema.json`, checks
the named rules below, and only then mutates semantic state. Malformed,
wrong-phase, over-cap, unavailable, stale, or otherwise illegal output becomes
the first terminal failure, remains fully charged, and cannot be repaired or
retried as a scientific call.
Before invocation it also checks the exact ordinal equality
`state.resolver_ordinal = resolver_ordinal` and
`INPUT_ENVELOPE.operation_ordinal = RESOLVER_STEP.ordinal =
resolver_ordinal + 1`; no zero-based ordinal is emitted as a model operation.

`READ` decrements the read budget before availability validation or disclosure.
Dream-1 accepts only readable TREE_EVENT handles. Dream-2 accepts readable
TREE_EVENT/RAW_A_EVENT handles and fresh Dream-2-local candidate handles. A
candidate read returns the exact immutable Dream-1 object and assigns the
Dream-2-session object capability determined by that read ordinal and used for
RETAIN; no Dream-1 capability
crosses the fresh-session boundary. Think accepts only a lexical query in
OPAQUE_NOTE or an AST query in OPERATOR_AST and returns the exact lane value or
`NOT_FOUND`; its READ must name the fixed target-memory handle rendered for the
session. The model sees only the applicable model-visible read result;
audit-only digest/length receipts never enter state rendered to cognition.

Every one-shot envelope starts with the dedicated closed capability-free state
(`resolver_ordinal=0`, empty action prefix, `OPEN`), never recurrent
`resolver_state`. One-shot Dream uses no interactive reducer trace. Before its sole invocation,
the harness mechanically charges each eligible public event and creates one
ordered `ONE_SHOT_EVENT_BATCH`. Dream-1 batches contain tree events only;
Dream-2 batches contain eligible tree events and raw A and travel with the
immutable one-shot Dream-1 pool. Count, order, charge, and bytes must match the
sealed source ledger and audit receipt, but byte length and digests exist only
in the audit sibling and are absent from the model-visible batch.

`NOTICE` accepts one visible premise and adds one complete model-authored node.
`CONNECT` accepts exactly two distinct visible premises and adds one complete
model-authored node. Workspace `REVISE` names exactly one live node, supplies
one or more valid visible premises, and atomically replaces that node. After
each accepted node operation the harness stores the exact JCS node and assigns
the current-session node capability determined by that authoring ordinal. Node
slots are live-state unique.
`PASS` changes no semantic state.

`PREDICT` is manifest-only. Dream-1 selects an ordered nonempty set of already
authored node capabilities into unused slot C01 or C02 and emits exact ordered
A1/A2 trays. Dream-2 stages exactly one C01 manifest with exact ordered B1/B2
trays and is decisive only after exactly one charged RAW_A_EVENT read in that
Dream-2 session. It carries a nonempty
`decision_provenance_receipt_ids` array resolving only to earlier charged reads
and containing the receipt ref of that sole raw-A read, and its manifest
provenance `public_handles` contains the matching raw-A handle. RETAIN cites the
capability assigned by a charged candidate read and has no new node list;
REPLACE cites that parent and selects a nonempty ordered list of current
Dream-2 nodes. The reducer resolves references without authoring, rewriting,
translating, or scoring content, validates canonical caps, stores the immutable
complete candidate together with the manifest decision and ordered decision
provenance array, and returns the current-session object capability determined
by the PREDICT ordinal.

Dream-1 terminal `COMMIT` names an ordered set of one or two distinct staged
object capabilities. The order is the corpus candidate order. Dream-2 terminal
`COMMIT` names exactly one capability and its decision must equal the staged
manifest: RETAIN selects the immutable read candidate payload; REPLACE selects
the new staged payload. Its decision, capability, and ordered
`decision_provenance_receipt_ids` must byte-for-byte equal the values stored at
PREDICT; provenance first introduced, omitted, reordered, or changed at COMMIT
is rejected. `ABSTAIN` in either Dream phase is capability-free and
materializes no corpus. Candidate replacement is never spelled `REVISE`.

Think `USE` is accepted only when its exact `USE(stem::suffix)` string occurs
in the current public legal menu; the actor receives that public USE but no
resolver/memory state. `LOCK` terminates Think locally, causes no actor call,
and is never actor IPC. Think `ABSTAIN` is also terminal and
capability-free. A successful recurrent D4 trace is exactly four accepted USE
actions followed by local LOCK; early lock, fifth action, illegal action, malformed
action, or abstention is retained with endpoint zero.

Atomic `ONE_SHOT_DREAM1` and `ONE_SHOT_DREAM2` never use capabilities. Dream-1
selected slots and Dream-2 REPLACE's D2C01 slot must exist in the same response
and agree with candidate slots and ordering. One-shot RETAIN directly selects
an immutable input `source_dream1_slot`, repeats no candidate, and supplies
exact terminal B1/B2 predictions. REPLACE cites its source Dream-1 slot and
carries one complete response-local D2C01 candidate with exact B1/B2. Both
decisions carry nonempty
`decision_provenance_receipt_ids` resolving to stable batch receipt refs and at
least one raw-A event. Atomic `ONE_SHOT_PLAN` is
OPERATOR_AST-only and must contain exactly four typed legal USE actions and
terminal LOCK before open-loop execution. Its input uses only the dedicated
one-shot AST packet/record definitions and its citations resolve only to public
handles. Every one-shot candidate, NOTE, and record provenance object contains
only `public_handles`; capability-named members or values and every recurrent
capability-bearing state/record/citation alternative are rejected, including
in the immutable Dream-1 input pool.
The executor sends each USE to the actor and consumes terminal LOCK locally.

## Phase caps and named reducer checks

Dream-1 has 32 operations, 13 reads, and at most two staged candidates.
Dream-2 has 16 operations, 8 reads, and at most one staged candidate. Iterative
D1 has 10 opportunities and 4 records; iterative D4 has 31 opportunities and
13 records. Dream phase raw-output budgets begin at 8,192 and 4,096 tokens.
Before recurrent Dream generation the prospective cap is
`min(2048, raw_output_tokens_remaining)`; after parse the accepted limits are
512 tokens for READ/node operations, 2,048 for PREDICT, and 256 for PASS or a
terminal. Recurrent Think always requests at most 512. Canonical byte limits
are 256 per NOTE/AST record, 512 per node, 2,510 per materialized payload, and
3,072 per complete candidate, including container overhead and multibyte UTF-8.

The following checks are mandatory executable reducer rules rather than JSON
Schema claims:

- `RED-R01_PHASE_OPERATION`: Dream permits READ/NOTICE/CONNECT/REVISE/PASS/
  PREDICT/COMMIT/ABSTAIN, never USE/LOCK; Think permits READ/NOTICE/CONNECT/
  REVISE/PASS/USE/LOCK/ABSTAIN, never PREDICT/COMMIT.
- `RED-R02_READ_BEFORE_REVEAL`: charge and validate catalog/query before any
  payload or extractor result is produced.
- `RED-R03_REFERENCE_OWNERSHIP`: every premise, parent, node capability, and
  object capability is live, previously issued, lane/session local, and not
  reordered, stale, unread, or future-authored.
- `RED-R04_ANCESTRY`: provenance is valid, transitive, acyclic, and contains no
  unread, private, target-time-during-Dream, other-session, or other-lane value.
- `RED-R05_MANIFEST_MATERIALIZATION`: PREDICT contains references/metadata only;
  materialization is the exact ordered projection of prior authored nodes.
- `RED-R06_EXACT_PREDICTIONS`: Dream-1 has A1 then A2 exactly; Dream-2 has B1
  then B2 exactly; identifiers are neither missing, duplicated, nor reordered.
- `RED-R07_COMMIT_SET`: Dream-1 commits ordered K=1..2; Dream-2 commits one
  staged object consistent with RETAIN/REPLACE; ABSTAIN has no capability.
- `RED-R08_CANONICAL_CAPS`: JCS bytes, strings, arrays, live tuples, operations,
  reads, actions, raw/accepted tokens, and phase remainders remain within cap.
- `RED-R09_LANE_FIREWALL`: NOTE and AST values, state, readers, candidates,
  corpora, actions, and diagnostic-only fields never cross lanes.
- `RED-R10_TERMINAL_MONOTONICITY`: after COMMIT, ABSTAIN, LOCK, or any first
  failure, no further operation, mutation, disclosure, or scientific retry is
  accepted.
- `RED-R11_ORDINAL_MAPPING`: for zero-based resolver ordinal `r`, the state
  `resolver_ordinal` is `r` and every input/output operation ordinal is exactly
  `r+1`.
- `RED-R12_DETERMINISTIC_IDENTIFIERS`: public event handles are direct
  kind/source-ordinal labels; all named opaque handles, receipt refs, and
  capabilities are fixed-shape, non-content, namespace- and ordinal-derived,
  and value-identical for corresponding paired topology.
- `RED-R13_DREAM2_RAW_A_PREDICT`: decisive Dream-2 PREDICT follows exactly one
  charged RAW_A_EVENT read, stages its receipt ref, and COMMIT exactly repeats
  the staged decision/capability/provenance tuple.
- `RED-R14_ACTOR_USE_ONLY`: only USE crosses Think-to-actor IPC; LOCK is a local
  Think terminal and never invokes the actor.
