# v2 supplied event extractor and delivery contract

**Identifier:** `pcfl-v2-slot-permutation-extractor-r2`. This is a normative,
hash-bound source specification, not implementation or execution authority. A
later literal refinement must have its source hash bound in the executable-
freeze receipt.

## Pure event-local function

Input is exactly one released public event value:

```text
{before:[six distinct public labels],
 action:"USE(stem::suffix)",
 after:[the same six labels, each exactly once]}
```

Reject before extraction unless the object is closed, both trays contain six
distinct valid public labels, the two label sets are equal, and the
action is the canonical typed string `USE(stem::suffix)`, where stem and suffix
each match `[A-Za-z0-9][A-Za-z0-9_-]{0,31}` under the semantic action schema;
there is no slot or public-label field. The releasing event validator must
already have established that the action belongs to the public action registry
and legal source schedule. The extractor receives no registry/schedule input
and does not compare the action to a tray label.
For each `i=0..5`, find the unique `j` with `before[i] == after[j]` and
return exactly `[j0,j1,j2,j3,j4,j5]`. The result must be a permutation of
`[0,1,2,3,4,5]`. Equality is exact decoded Unicode-scalar equality; no Unicode
normalization, casefold, sorting, inference, or label rewriting occurs.

The action is retained only as public event provenance and is validated for
closed syntax. `slot_permutation` is computed solely from equality between the
`before` and `after` arrays; changing action stem/suffix while keeping a valid
event and the two arrays fixed cannot change the extracted permutation.

The function is pure and stateless. Its signature cannot accept history,
cache, root, family, h/q/z, graph, target, goal, certificate, comparator,
orientation, corpus, query, score, seed, or private data. It cannot emit an
inverse/decomposition/closure, shortest word, path, factor/group/gauge name,
cross-event statistic, confidence, digest, or identity metadata. Global public
label relabeling leaves its integer output unchanged.

## Exactly two learned public-event delivery modes

1. **`INTERACTIVE_CHARGED_EVENT` (recurrent Dream only).** The pre-READ
   catalog contains no payload or extraction. When Dream emits a legal READ,
   the harness charges that handle, releases exactly its raw event, invokes the
   function once, and returns one model-visible `EVENT_READ_RECEIPT` containing
   the raw event and `slot_permutation`. Its fixed-shape non-content
   `receipt_ref` is deterministically derived from the charged read's
   zero-based resolver ordinal under the `model_visible_identifier` namespace
   supplied by `rng_contract.json`; this contract does not define that
   namespace's cryptographic derivation. Digest, byte count, timing, parser
   state, and error details are an audit-only sibling and never enter a prompt.

2. **`SEALED_CHARGED_EVENT_BATCH` (one-shot Dream only).** Before the one-shot
   request, a mechanical non-model builder traverses the already eligible
   source-event ledger in ascending event ordinal. For each event it performs
   the same release, charge, validation, and one invocation above, then appends
   the same model-visible event payload to the batch. The closed model-visible
   batch records exactly `artifact:"ONE_SHOT_EVENT_BATCH"`, `phase`,
   `delivery:"MECHANICALLY_CHARGED_PREINPUT"`, ordered `events`,
   and `charged_read_count`; it contains no `jcs_byte_count`, byte length, or
   digest. Each item's `handle_id` is the direct fixed label of event kind plus
   one-based source ordinal. Its opaque fixed-shape `receipt_ref` is derived
   from the zero-based source/issuance ordinal in the dedicated
   `model_visible_identifier` namespace. An `AUDIT_BATCH_RECEIPT` sibling
   records source ledger SHA-256, batch JCS SHA-256, ordered receipt refs,
   charged-read count, and canonical payload byte count; it never enters the
   model input. The phase input envelope carries the separately typed budget.
   Stage 0 requires event order, count, raw bytes, extracted values, total
   bytes, and charges to equal the source ledger exactly. No event is omitted,
   duplicated, reordered, summarized, or exposed without a charge.

For paired treatments with corresponding event topology and ordinals, public
TREE_EVENT/RAW_A_EVENT handles and receipt-ref values are byte-identical. Any
content-, h/q-, condition-, lane-variant-, address-, length-, cache-, timing-,
or score-dependent identifier is invalid. This identity rule depends on the
namespace contract in `rng_contract.json` and adds no extractor input or output.

These are the only learned source-event modes. Recurrent and structured
one-shot Think receive no source event, extractor output, extraction receipt,
or batch; their only historical input is the permitted frozen NOTE/AST
representation. `EXACT_PROGRAM` and `OBSERVED` may call this same pure function
as direct CPU interfaces, never as learned-lane reads or model calls.

No catalog, workspace, candidate, pre-READ prompt, unread event, target packet,
or target-time Think input contains `slot_permutation`. Stage 0 must bind the
contract/source hashes and prove all legal S6 outputs, malformed rejection,
label equivariance, event locality, no cache/state, identical factor/null code
paths, interactive/batch byte equality, unread-extractor absence, and the q
conditional null after rendering, extraction, handle assignment, and exact
reader/batch serialization. Negative fixtures inject each forbidden input and
output field and must fail at the closed function boundary.

The only permitted claim is that the learned resolver used **supplied local
permutations**. This is not raw tray perception, schema/operator/factor
discovery, autonomous algebra extraction, or an unseen-target oracle.
