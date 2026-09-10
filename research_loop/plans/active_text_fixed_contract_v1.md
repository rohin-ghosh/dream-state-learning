# `ACTIVE_TEXT_FIXED` exact contract v1

Date: 2026-09-06

Status: **proposal-only supporting contract** for
`one_parent_child_headline_v1.md`. It authorizes no implementation, model or
tokenizer call, benchmark generation, adapter operation, or GPU use.

This file fixes the byte-level update, merge, query, retrieval, and actor-read
surface for the common frozen-parameter active textual memory. Every deployed
service (`R0`, `U0`, `U1`, `P0`, and `P1`) owns a separate instance. No byte or
state crosses services, roots, childhood, or the parent-deletion boundary.

## 1. Canonical serialization

All protocol objects use UTF-8 JSON with:

- object keys sorted lexicographically by Unicode code point;
- compact separators: comma `,` and colon `:` with no surrounding whitespace;
- `ensure_ascii=false`, no NaN/Infinity, and integer numeric fields only;
- Unicode normalized to NFKC before schema validation; and
- exactly one U+000A after each complete JSON object when used as JSONL.

The raw model response is persisted first. A strict JSON parser then accepts
any object-key order, rejects duplicate keys, and canonicalizes the parsed
object exactly once under the rules above before schema, byte-size, and
semantic validation. Thus emitted key order is not itself a validity
condition; every stored, hashed, compared, or re-rendered object is canonical.
Arrays preserve emitted order unless a rule below explicitly sorts them.
Duplicate array values are rejected. Unknown fields, missing fields, wrong
types, and values outside the stated enum or bound reject the whole call. IDs
match `^[a-z][a-z0-9_]{0,63}$`. The merger, not the model, assigns a new
memory ID as `m_` plus the first sixteen lowercase hexadecimal characters of
SHA-256 over the canonical proposed record with `memory_id` set to `null`.
The model emits `reflection_id=null`; after semantic validation the merger
assigns `r_` plus the first sixteen lowercase hexadecimal characters of
SHA-256 over the canonical reflection item with `reflection_id=null`, followed
by U+000A and the NFKC-normalized raw UTF-8 `program_event_id` bytes. An
assigned-ID collision with
nonidentical bytes rejects the call.

The exact model-visible compact output grammar is the complete UTF-8 content
of `research_loop/plans/active_text_fixed_prompt_schema_v1.txt`, including its
single terminal U+000A. That file is a source-bound part of this contract.

## 2. Closed semantic objects

The following objects are shared by `REFLECT`, `CURATE`, and stored records.
Every named field is required, including nullable and empty-array fields.

```text
SCOPE := {
  "level": "PROGRAM" | "PUBLIC_FEATURE" | "CROSS_PROGRAM",
  "keys": [ID, ...]
}

PROPOSITION := {
  "kind": "ACTION_VALIDITY" | "SCORE_EFFECT" | "ACTION_CONTRAST" |
          "PREDICTION_BIAS" | "SCOPE_EXCEPTION" | "PROCESS_ASSOCIATION",
  "subject_action_family": ID,
  "object_action_family": ID | null,
  "relation": "VALID" | "INVALID" | "POSITIVE" |
              "NEUTRAL" | "NEGATIVE" | "BETTER" | "EQUAL" | "WORSE" |
              "OVERPREDICTS" | "UNDERPREDICTS" | "CALIBRATED" |
              "CONTRADICTS" | "SUPPORTS",
  "outcome_class": "IMPROVED" | "UNCHANGED" | "REGRESSED" | "INVALID" |
                   "MIXED" | null,
  "value_ppm": INTEGER | null,
  "exception_basis": "VALIDITY" | "SCORE_SIGN" | null,
  "local_bin": "VALID" | "INVALID" | "POSITIVE" | "NEGATIVE" | null,
  "external_bin": "VALID" | "INVALID" | "POSITIVE" | "NEGATIVE" | null
}

GUIDANCE := {
  "mode": "TRY" | "AVOID" | "COMPARE" | "REVISE" | "NONE",
  "action_families": [ID, ...],
  "condition": "IN_SCOPE" | "AFTER_SURPRISE" | "BEFORE_COMMIT" |
               "ON_CONTRADICTION" | "ALWAYS" | "NONE"
}
```

`value_ppm` is rounded to the nearest integer with ties to even. For
`SCORE_EFFECT` it is signed public score change times one million; for
`PREDICTION_BIAS` it is signed `(prediction - public outcome)` times one
million; it is null for every other kind. The only legal field combinations
are:

| proposition kind | legal relation | object family | outcome/delta | exception fields |
|---|---|---|---|---|
| `ACTION_VALIDITY` | `VALID`, `INVALID` | null | matching outcome, null delta | all null |
| `SCORE_EFFECT` | `POSITIVE`, `NEUTRAL`, `NEGATIVE` | null | non-null outcome and delta | all null |
| `ACTION_CONTRAST` | `BETTER`, `EQUAL`, `WORSE` | required and different | `MIXED`, null delta | all null |
| `PREDICTION_BIAS` | `OVERPREDICTS`, `UNDERPREDICTS`, `CALIBRATED` | null | null outcome, non-null value | all null |
| `SCOPE_EXCEPTION` | `CONTRADICTS` | null | `MIXED`, null delta | all required and consistent |
| `PROCESS_ASSOCIATION` | `SUPPORTS` | null or different | non-null outcome, null delta | all null |

`PROGRAM` scope has exactly one program-event ID. `PUBLIC_FEATURE` has one to
eight public feature IDs. `CROSS_PROGRAM` has an empty key list and requires
support from at least two distinct public program IDs. Hidden compiler state
can never supply a key.

The semantic key of an item or record is the tuple
`(derived_memory_type,scope,subject_action_family,object_action_family,
exception_basis)`. The final position is null except for `SCOPE_EXCEPTION`.
Exception direction remains in the proposition signature rather than the key,
so a later reverse direction cannot coexist as a second live same-basis record.
At most one nonsuperseded record with a given semantic key may exist in a
service store.

Every public causal-spine and retrievable raw-ledger object has this exact
shape; nullable fields remain present:

```text
PUBLIC_CAUSAL_EVENT := {
  "event_id": ID,
  "program_event_id": ID,
  "ordinal": INTEGER,
  "event_kind": "ASSISTANT" | "ACTION" | "OUTCOME" | "SCORE" |
                "PREDICTION" | "CLOCK",
  "objective": STRING | null,
  "metric": STRING | null,
  "public_feature_ids": [ID, ...],
  "starting_state_id": ID | null,
  "action_family": ID | null,
  "action_args": CANONICAL_JSON_OBJECT | null,
  "prediction_ppm": INTEGER | null,
  "outcome_class": "IMPROVED" | "UNCHANGED" | "REGRESSED" | "INVALID" |
                   null,
  "score_before_ppm": INTEGER | null,
  "score_after_ppm": INTEGER | null,
  "public_text": STRING | null,
  "source_sha256": LOWERCASE_SHA256
}

LEDGER_EVENT_BLOCK := {
  "document_type": "PUBLIC_EVENT_BLOCK",
  "block_id": ID,
  "program_event_id": ID,
  "events": [PUBLIC_CAUSAL_EVENT, ...]
}
```

A block is constructed deterministically for each dispatched action: exactly
one latest preceding same-program `ASSISTANT`, zero or one numeric
`PREDICTION`, exactly one native `ACTION`, exactly one public `OUTCOME`, and
exactly one resulting `SCORE`, ordered by ordinal. Its ID
is `b_` plus the first sixteen hex characters of SHA-256 over its canonical
bytes with `block_id=null`. The block has four or five events, every event is
same-service/same-program, and `public_feature_ids` has at most eight IDs.
`public_text` is complete and at most 128 child-tokenizer tokens; a block with
an overlength event remains in the lossless ledger but is ineligible for the
retrieval index. A complete eligible block is at most 256 child-tokenizer
tokens. It is one BM25 document, never a dense document.
`source_sha256` is the hash of the immutable pre-render message/tool/result
envelope named by `event_id`; it is not a hash of `PUBLIC_CAUSAL_EVENT` itself,
so construction is nonrecursive.

## 3. Exact `REFLECT` schema

One `REFLECT` call emits exactly one object:

```text
{
  "schema_version": 1,
  "program_event_id": ID,
  "items": [
    {
      "reflection_id": null,
      "kind": "SUCCESS" | "FAILURE" | "CONTRADICTION" | "SCOPE_CHANGE",
      "scope": SCOPE,
      "proposition": PROPOSITION,
      "guidance": GUIDANCE,
      "support_event_ids": [ID, ...],
      "counterevidence_event_ids": [ID, ...],
      "related_memory_ids": [ID, ...]
    }, ...
  ]
}
```

`items` has zero to four entries. The model-emitted `reflection_id` is always
null and is replaced by the deterministic merger-assigned ID above. Each
support/counterevidence array has zero to sixteen entries and their union must
be nonempty. Every cited event must be
earlier, public, same-service, and included verbatim in the rendered input.
Related memories must exist, be same-service, and have been included verbatim
inside their exact record receipts.
The `program_event_id` must equal the just-finished public program event.
Support and counterevidence arrays must be disjoint. `related_memory_ids` has
at most sixteen entries. For a non-`PROCESS_ASSOCIATION` item, it equals all
displayed live records with the same semantic key. For a process item, it is
the union of (a) all displayed live same-key records and (b) displayed live
non-process records with exactly the same derived scope whose subject family
equals the process subject or its nonnull object family. The merger sorts the
result lexicographically. If more than sixteen records qualify, the item is
illegal rather than truncated. Semantic keys must be unique across the emitted
`items` array. The strict parser sorts all three ID arrays lexicographically
before reflection-ID assignment and semantic validation.

## 4. Exact `CURATE` schemas and transition law

One `CURATE` call emits exactly:

```text
{"schema_version":1,"program_event_id":ID,"deltas":[DELTA,...]}
```

`deltas` has one to four entries. Each `DELTA` is exactly one of:

```text
ADD := {
  "op":"ADD",
  "record": RECORD_WITH_NULL_MEMORY_ID
}

REVISE := {
  "op":"REVISE",
  "memory_id":ID,
  "prior_record_sha256":LOWERCASE_SHA256,
  "replacement": RECORD_WITH_SAME_MEMORY_ID
}

LINK := {
  "op":"LINK",
  "source_memory_id":ID,
  "target_memory_id":ID,
  "prior_source_sha256":LOWERCASE_SHA256,
  "prior_target_sha256":LOWERCASE_SHA256
}

SUPERSEDE := {
  "op":"SUPERSEDE",
  "memory_id":ID,
  "prior_record_sha256":LOWERCASE_SHA256,
  "replacement": RECORD_WITH_NULL_MEMORY_ID
}

NOOP := {
  "op":"NOOP",
  "reason":"NO_LEGAL_DELTA"
}
```

Operation choice is deterministic. Define a proposition signature as
`(kind,subject_action_family,object_action_family,relation,outcome_class,
exception_basis,local_bin,external_bin)`; `value_ppm` is deliberately excluded
because additional same-bin support may update its median. Process the valid
`REFLECT.items` in emitted order against the immutable pre-`CURATE` store.
Each item
prescribes at most one delta by the first matching rule:

1. If no live same-key record exists, prescribe `ADD`. Its record copies the
   item's scope, proposition, guidance, and evidence arrays exactly, derives
   memory type/status, and has null memory/provenance IDs and empty links.
2. If the sole live same-key record has the same signature and the item
   contains at least one complete support/counter observation identity not
   represented in the prior record, prescribe `REVISE`. The
   replacement preserves memory ID, semantic key, signature, links, and
   supersession provenance; unions old and item evidence; and recomputes
   numeric value, outcome, guidance, and status from the full union.
3. If the sole live same-key record is `CONTRADICTED`, the item has a different
   signature, and the item's own newly rendered evidence derives a
   `PROVISIONAL` or `SUPPORTED` record, prescribe `SUPERSEDE`. The replacement
   copies the item as in `ADD`, points to the old ID, starts with empty links,
   and the old immutable record becomes `SUPERSEDED` atomically.
4. Otherwise, if the item is `PROCESS_ASSOCIATION`, a live same-key/same-
   signature process record exists, and the item adds no evidence, form the
   eligible source set from its `related_memory_ids`: live non-process records
   with the identical scope whose subject family equals the process subject or
   nonnull object. Choose the lexicographically first source lacking a directed
   link to the process record and prescribe exactly that source-to-process
   `LINK`. If the set is empty, prescribe nothing.
5. Otherwise prescribe nothing.

Before `CURATE`, the merger derives the complete list and rejects `REFLECT` if
an item would prescribe `ADD` with ordinary derived status `CONTRADICTED`, if
two prescribed deltas would mutate or create the same memory ID, if a `LINK`
source is also mutated by another prescribed delta, or if any delta would
consume an ID or hash created or changed by another item in the call. This
call-level admissibility check uses deterministic would-be `ADD` IDs and the
immutable pre-call store only.

After semantic acceptance, the merger deterministically constructs the exact
complete canonical `CURATE` object prescribed by that accepted `REFLECT` and
the immutable pre-call store, including the top-level fields, ordered deltas,
complete records, prior hashes, and a sole `NOOP` when no delta is prescribed.
Before measuring that response, the merger applies the complete prescribed
delta list to a temporary copy using the exact commit path: deterministic new
IDs and supersession provenance are assigned, prior evidence is unioned,
links are inserted, all arrays are sorted, derived fields and hashes are
recomputed, and every array cardinality, stored-record length, live-key,
collision, transition, and provenance invariant is checked. The preflight uses
only the accepted `REFLECT`, required public evidence, displayed immutable
record receipts, and the immutable pre-call store. If this unique finalized
transition cannot commit— including support or counterevidence growing from
16 to 17 IDs, a link growing from 16 to 17 targets, or any changed/new
canonical stored record growing from 256 to 257 pinned-child tokens—record
`TRANSITION_UNREPRESENTABLE`, do not call `CURATE`, leave the store unchanged,
and retain the accepted `REFLECT` as a scored audit event. The preflight never
drops prior evidence, a link, provenance, a field, or a prescribed delta.

At the separately authorized pinned-tokenizer gate, output representability is
the number of generated assistant-response suffix token IDs for those exact
canonical JSON bytes under the official pinned chat template, followed by
exactly one pinned EOS token. If that count exceeds the 384-token output cap,
record `OUTPUT_UNREPRESENTABLE`, do not call `CURATE`, leave the store
unchanged, and retain the accepted `REFLECT` as a scored audit event. No item,
delta, record, field, or byte may be omitted or shortened to make it fit.
This deterministic preflight is required for every one- through four-delta
case and is a proposal-time obligation; no tokenizer is called until the
separately authorized tokenizer gate.

When the preflight passes, `CURATE` must emit exactly the complete ordered
prescribed-delta list. If the
list is empty it must emit the sole `NOOP`; `NOOP` is illegal otherwise. Thus
`ADD`, `REVISE`, `SUPERSEDE`, and `LINK` are mutually identified by the
accepted reflection and current store, rather than alternative model choices.
Deltas apply atomically in that prescribed order to a temporary copy; any
mismatch or failure
rejects all deltas. Exact current hashes are required. A `LINK` adds the target
once to the source links and changes nothing else. Self, reverse-substituted,
stale, or superseded links are illegal. The one-live-record-per-semantic-key
invariant is checked after every temporary transition and at commit.

The complete stored record is:

```text
RECORD := {
  "memory_id": ID | null,
  "memory_type": "OBSERVATION" | "ACTION_RULE" | "CONTRAST" |
                 "CALIBRATION" | "EXCEPTION" | "PROCESS_RULE",
  "scope": SCOPE,
  "proposition": PROPOSITION,
  "guidance": GUIDANCE,
  "support_event_ids": [ID, ...],
  "counterevidence_event_ids": [ID, ...],
  "linked_memory_ids": [ID, ...],
  "status": "PROVISIONAL" | "SUPPORTED" | "CONTRADICTED" | "SUPERSEDED",
  "supersedes_memory_id": ID | null
}
```

Every newly cited evidence ID must appear in the valid `REFLECT` object.
Evidence retained by `REVISE` may instead come from the displayed exact prior
record. After the raw output is sealed, the merger resolves only those retained
IDs against the same-service immutable ledger to recompute aggregate fields;
no resolved bytes or score returns to either updater call. `SUPPORTED`
requires at least two complete support observations; cross-program
`SUPPORTED` requires at least two distinct programs. A valid
`SCOPE_EXCEPTION` is specially `SUPPORTED` by its required local support plus
cross-scope contrast even when it has only one local support observation. For
every other kind, `CONTRADICTED` requires ordinary counterevidence.
`SUPERSEDED` is never model-emittable in a new/replacement record. The legal
status transitions for `REVISE` are:

```text
PROVISIONAL -> SUPPORTED | CONTRADICTED
SUPPORTED   -> SUPPORTED | CONTRADICTED
CONTRADICTED-> CONTRADICTED
SUPERSEDED  -> (none)
```

Only `SUPERSEDE` may enter `SUPERSEDED`. A `REVISE` replacement may not cite a
future event or discard any prior support/counterevidence ID, although the
merger may move an ID between those arrays when the recomputed proposition
requires it. A `SUPERSEDE` replacement may omit old evidence because the old
immutable record and explicit provenance edge retain it; it must cite only
currently rendered evidence that derives the replacement as `PROVISIONAL` or
`SUPPORTED`. IDs within every stored array are sorted lexicographically by the
merger.
Stored support and counterevidence arrays are disjoint and have at most sixteen
IDs each; `linked_memory_ids` has at most sixteen IDs; scope has at most eight
keys. After assignment, sorting, link application, and supersession fields,
the complete stored canonical record must remain at most 256 pinned-child-
tokenizer tokens. An oversize transition atomically rejects the whole call.

For `ADD`, `supersedes_memory_id` must be null. `REVISE` and `LINK` preserve
the prior value. For `SUPERSEDE`, the old record must not already be
superseded, and the replacement's `supersedes_memory_id` must equal the old
ID; no other operation may create or alter that provenance edge.

## 5. Semantics and deterministic actor rendering

The updater never writes free prose into the active store. It chooses the
closed typed objects above. The merger recomputes each proposition from cited
public events and rejects it unless every field passes the following total
evidence-faithfulness law.

An evidence observation is reconstructed only from one eligible
`LEDGER_EVENT_BLOCK`, and citation sets are exact rather than extensible.
For each represented block, `ACTION_VALIDITY` cites only its ACTION+OUTCOME
IDs; `SCORE_EFFECT` only ACTION+SCORE; `ACTION_CONTRAST` only ACTION+SCORE for
both blocks in each pair; `PREDICTION_BIAS` only
ACTION+PREDICTION+SCORE; `SCOPE_EXCEPTION` only ACTION+OUTCOME under its
derived `VALIDITY` basis or ACTION+SCORE under `SCORE_SIGN`; and
`PROCESS_ASSOCIATION` only ACTION+OUTCOME for every block in its sequence.
No assistant, clock, unused prediction, duplicate result, or other event ID is
legal. Partial or cross-block joins are illegal. The merger groups exact IDs
by immutable `block_id` before computing observation counts, medians, modes,
pairs, or sequences, so an action event is never treated as if it contained a
later result. For support counts and novelty, an observation identity is one
`block_id` for single-block kinds and scope-exception sides, one ordered
`(subject_block_id,object_block_id)` for `ACTION_CONTRAST`, or the complete
one-/two-block tuple for `PROCESS_ASSOCIATION`. Every proposition requires at
least one complete support
observation. `PROVISIONAL` therefore means exactly one support observation and
no counterevidence; no zero-support record is legal.

First derive scope by one precedence rule; the model cannot choose a narrower
or broader equivalent. Let `P` be the set of program-event IDs among complete
support observations, and let `F` be the lexicographically sorted exact
intersection of the action events' `public_feature_ids` across all support
observations. If `|P|=1`, scope is `PROGRAM` with the sole program ID as its
only key. Otherwise, if `|P|>=2` and `F` is nonempty, scope is
`PUBLIC_FEATURE` with all and only the IDs in `F` as keys. Otherwise scope is
`CROSS_PROGRAM` with no keys. More than eight IDs in `F` rejects the proposed
unit rather than truncating it. Every ordinary counterevidence observation
must be outside the support-observation set, use the same derived scope
variables, and fall in the proposition-specific counter bin below. It uses the
subject action family except for `ACTION_CONTRAST`, whose complete counter-pair
contains both declared families. `SCOPE_EXCEPTION` uses its separate ordered
local-versus-external construction below.

Ordinary counter-scope membership is exact. For `PROGRAM`, every constituent
counter block has the sole keyed `program_event_id`. For `PUBLIC_FEATURE`,
every constituent counter action event contains every exact scope key. For
`CROSS_PROGRAM`, no program or feature restriction is added beyond complete,
distinct observations and the proposition-specific family/bin rule. A paired
contrast or process counter group applies the membership test to every block
in the pair/sequence. Counter observations never participate in support-scope
derivation.

Then recompute the proposition:

- `ACTION_VALIDITY`: support action events all use the subject family and have
  the claimed `VALID` (non-`INVALID`) or `INVALID` outcome. `outcome_class`
  equals `INVALID` only for the latter and otherwise equals the modal public
  outcome with ties broken `IMPROVED`, `UNCHANGED`, `REGRESSED`; `value_ppm`
  and object family are null. Counterevidence uses the opposite validity.
- `SCORE_EFFECT`: support events all use the subject family. `value_ppm` is the
  median of `score_after_ppm-score_before_ppm` (for an even count, integer
  mean of the middle pair with ties to even). Relation and `outcome_class` are
  deterministically `POSITIVE/IMPROVED` for value greater than zero,
  `NEUTRAL/UNCHANGED` for zero, or `NEGATIVE/REGRESSED` for below zero;
  object family is null. Counterevidence has the opposite strict sign; for a
  neutral claim, any nonzero delta is counterevidence.
- `ACTION_CONTRAST`: for each cited starting-state ID there must be exactly one
  complete subject-family block and exactly one complete object-family block
  in the same program; any duplicate or unmatched block rejects the claim.
  Sort these unique pairs by `(program_event_id,starting_state_id)` and compare
  public score deltas.
  The median paired difference deterministically yields `BETTER`, `EQUAL`, or
  `WORSE`; outcome is `MIXED`, value null. Counterevidence is a valid matched
  pair with the opposite strict ordering (or any non-equality for `EQUAL`).
- `PREDICTION_BIAS`: every support prediction is linked to its subsequent
  subject-family outcome. `value_ppm` is the median
  `prediction_ppm-score_after_ppm`; absolute value at most the frozen integer
  calibration threshold first yields `CALIBRATED`, otherwise positive yields
  `OVERPREDICTS` and negative yields `UNDERPREDICTS`. Object and outcome are null.
  Counterevidence lies in a different one of those three bins.
- `SCOPE_EXCEPTION`: `object_action_family` is always null. All complete
  support observations use the subject family in exactly one program; hence
  the derived scope is that `PROGRAM`. All complete counter observations use
  that subject family in at least one different program. Support observations
  must agree internally on one validity bin (`VALID` versus `INVALID`) or one
  strict score-sign bin (`POSITIVE` versus `NEGATIVE`), counter observations
  must agree internally on the opposite bin using the same basis, and neutral
  score effects are ineligible. Basis precedence is deterministic: use
  `VALIDITY` whenever support and counter observations occupy opposite
  validity bins; only otherwise may opposite strict score signs derive
  `SCORE_SIGN`. `local_bin` is the support bin under that basis, and
  `external_bin` is its exact
  opposite from the counter observations. These counter observations are
  constitutive contrast evidence for the exception, not evidence against it.
  Relation is `CONTRADICTS`, outcome `MIXED`, and value null. Any mixed basis,
  mixed bin, same-program counter observation, non-opposite external bin, or
  unmatched action family rejects the unit. This typed direction distinguishes
  local-valid/external-invalid from its reverse and is actor-visible.
- `PROCESS_ASSOCIATION`: use all cited complete blocks exactly once. If
  `object_action_family` is null, every cited block must use the subject family
  and forms one complete sequence by itself; its own terminal outcome is that
  sequence's outcome. If the object is nonnull and different, then within each
  program all cited blocks, sorted by terminal ordinal, must partition into
  disjoint subject-then-object pairs. The object block must be the next action
  block in the immutable public history after its subject block, with no
  intervening action, and the object's own terminal outcome is the pair's
  outcome. An unmatched, duplicated, reversed, reused, or extraneous cited
  block rejects the unit. Relation is `SUPPORTS`; proposition outcome is the
  modal sequence outcome with ties broken `IMPROVED`, `UNCHANGED`, `REGRESSED`,
  `INVALID`; value is null. Counterevidence is independently partitioned by
  the same antecedent rule and derived scope, uses every cited counter block
  exactly once, and has a modal outcome different from the claimed one. The
  deterministic actor renderer labels this an association, never a causal
  fact.

`memory_type` is derived, never freely chosen:

```text
ACTION_VALIDITY -> OBSERVATION
SCORE_EFFECT -> ACTION_RULE
ACTION_CONTRAST -> CONTRAST
PREDICTION_BIAS -> CALIBRATION
SCOPE_EXCEPTION -> EXCEPTION
PROCESS_ASSOCIATION -> PROCESS_RULE
```

Guidance is also total. `VALID` and `POSITIVE` require
`TRY/[subject]/IN_SCOPE`; `INVALID` and `NEGATIVE` require
`AVOID/[subject]/IN_SCOPE`; `NEUTRAL` requires `NONE/[]/NONE`; every contrast
requires `COMPARE/[subject,object]/IN_SCOPE`; prediction bias requires
`REVISE/[subject]/AFTER_SURPRISE`; scope exception requires
`REVISE/[subject]/ON_CONTRADICTION`; process association requires
`REVISE/[subject]/AFTER_SURPRISE`. Array order is exactly the order shown.
`NONE` is legal only with an empty action array and `condition=NONE`; every
other mode has the stated nonempty cardinality and condition. These checks use
public bytes only and return one admission bit; no hidden truth or semantic
score returns to the model.

`REFLECT.kind` is derived after the proposition: `SCOPE_EXCEPTION` maps to
`SCOPE_CHANGE`; otherwise any nonempty counterevidence maps to
`CONTRADICTION`; otherwise `VALID`, `POSITIVE`, `BETTER`, `CALIBRATED`, or
`SUPPORTS` maps to `SUCCESS`; all remaining relations map to `FAILURE`.
Stored status is also derived, not selected. A valid `SCOPE_EXCEPTION` is
`SUPPORTED` because its counter array is constitutive cross-scope contrast.
For every other kind, any counterevidence produces `CONTRADICTED`; otherwise
two or more complete support observations produce `SUPPORTED`; otherwise the
required single support observation produces `PROVISIONAL`. `SUPERSEDED` is
created only by the merger during the named operation. Every model-emitted
kind or new/replacement status must equal the derived value or the call is
rejected. Because evidence cannot be discarded by `REVISE`, a contradicted
record can only remain `CONTRADICTED`; replacing it with a newly supported or
provisional proposition requires `SUPERSEDE`.

The actor-visible representation is produced by a frozen deterministic
renderer, not by the updater. A retrieved document is exactly one canonical
live `RECORD` or one canonical eligible `LEDGER_EVENT_BLOCK`; records may come
from fused lexical+dense ranking, while event blocks are lexical-only. The
literal insertion bytes are:

```text
<ACTIVE_TEXT_FIXED schema_version="1">
{"documents":[CANONICAL_RECORD_OR_EVENT_BLOCK,...]}
</ACTIVE_TEXT_FIXED>
```

The document array is in final retrieval/one-hop expansion order and the whole
wrapper object is canonical compact JSON on one line. The opening tag, JSON,
and closing tag are separated by exactly one U+000A; there is no terminal
newline after the closing tag. If retrieval returns zero documents, the entire
block is omitted. This structured block is inserted immediately after the
public objective/metric block and before the current program trace. No other
memory text is inserted.

## 6. Exact prompt contents

Every live record shown to either updater is wrapped as:

```text
RECORD_RECEIPT := {
  "record": RECORD,
  "record_sha256": LOWERCASE_SHA256
}
```

`record_sha256` is SHA-256 over the UTF-8 bytes of the complete canonical
`RECORD` object with no leading or terminal byte. The receipt itself is then
canonicalized normally. The merger verifies the receipt against the immutable
pre-call store; `REVISE` and `SUPERSEDE` copy that visible digest into
`prior_record_sha256`, while `LINK` copies the two visible source/target
digests. A digest not present beside the exact displayed record is illegal.
The store is version-locked from prompt rendering through atomic commit, so a
concurrent hash change aborts without retry.

The pinned tokenizer's official chat template is used once. Its system message
for both calls is the following UTF-8 text (without the fence or a terminal
newline):

```text
You maintain one agent's external playbook using only public, cited experience. Emit exactly one compact JSON object matching ACTIVE_TEXT_FIXED schema version 1. Do not emit markdown, commentary, hidden-state claims, future claims, uncited claims, or fields outside the schema. A malformed, unsupported, overflowing, or out-of-scope object is discarded without retry.
```

The complete schema file from Section 1 is placed in every updater call; the
model does not need repository access. User-message bytes are concatenations
below, where `||` means byte concatenation and quoted `\n` is one U+000A. The
result has no terminal newline.

```text
REFLECT_USER =
  "OP=REFLECT\nSCHEMA:\n"
  || PROMPT_SCHEMA_FILE_BYTES
  || "CALIBRATION_THRESHOLD_PPM=50000\n"
  || "PROGRAM_EVENT_ID=" || PROGRAM_EVENT_ID
  || "\nOBJECTIVE_METRIC_CLOCK:\n" || CANONICAL_CONTEXT_HEADER_JSON
  || "\nCURRENT_PROGRAM_CAUSAL_SPINE:\n" || CAUSAL_SPINE_JSONL_OR_EMPTY
  || "\nRAW_ASSISTANT_EVENTS:\n" || RAW_ASSISTANT_EVENT_JSONL_OR_EMPTY
  || "\nPRIOR_RETRIEVAL:\n" || PRIOR_DOCUMENT_JSONL_OR_EMPTY
  || "\nReturn schema_version, program_event_id, and zero to four items."

CURATE_USER =
  "OP=CURATE\nSCHEMA:\n"
  || PROMPT_SCHEMA_FILE_BYTES
  || "CALIBRATION_THRESHOLD_PPM=50000\n"
  || "PROGRAM_EVENT_ID=" || PROGRAM_EVENT_ID
  || "\nVALID_REFLECT:\n" || CANONICAL_REFLECT_JSON
  || "\nCITED_EVENTS_AND_RELATED_RECORDS:\n"
  || CITED_EVENT_AND_RECORD_JSONL_OR_EMPTY
  || "\nReturn schema_version, program_event_id, and one to four atomic deltas. Use one NOOP when no legal update is supported."
```

`CITED_EVENT_AND_RECORD_JSONL_OR_EMPTY` is one deterministic union derived
after `REFLECT` acceptance. It contains (a) the complete event block for every
support/counter event ID in any item, (b) the sole live full-store same-key
record consulted for each item whether or not it appeared in prior retrieval,
and (c) every live record named by `related_memory_ids`, including every
process-link source/target candidate. Deduplicate blocks by `block_id` and
records by `memory_id`. Render complete blocks first, sorted by
`(program_event_id,ACTION.ordinal,block_id)`, then complete `RECORD_RECEIPT`s
sorted by `record.memory_id`. There is no retrieval-rank fallback for a record
surfaced only at CURATE. If this entire required union or the accepted REFLECT
cannot fit its fixed partition, record `INPUT_OVERFLOW`, do not call `CURATE`,
leave the store unchanged, and retain the accepted `REFLECT` as a scored audit
event. After this input check, apply Section 4's exact prescribed-output
preflights in this fixed order: finalized transition feasibility, then exact
output length. `TRANSITION_UNREPRESENTABLE` and `OUTPUT_UNREPRESENTABLE` have
the same no-call/no-update disposition. Nothing is omitted, truncated,
summarized, or borrowed from another partition to avoid any receipt.

`PROMPT_SCHEMA_FILE_BYTES` includes its single terminal newline, so the literal
calibration line begins immediately after the schema file's
terminal newline. `50000` is the frozen integer corresponding to 0.05 public
score units; it is not tuned. The context header is exactly:

```text
{"clock":{"generated_tokens_budget":INTEGER,"generated_tokens_used":INTEGER,"program_index":INTEGER},"metric":STRING,"objective":STRING}
```

Every causal/raw assistant item is one canonical `PUBLIC_CAUSAL_EVENT`; every
prior/cited record is one canonical `RECORD_RECEIPT`, while a cited event block
is one canonical `LEDGER_EVENT_BLOCK`. JSONL items
appear in chronological ordinal order for events and frozen retrieval rank for
records, with one terminal U+000A after each object. `(empty)` is the exact
ASCII content of an empty `*_OR_EMPTY` placeholder. Strings live inside their
canonical JSON objects and therefore receive exactly ordinary JSON escaping;
complete canonical objects inserted into the outer prompt are never escaped a
second time. Required event/document inclusion, partition packing, output
caps, no-retry law, and overflow behavior are those in the headline plan.

Before tokenization, exact user bytes are wrapped only by the pinned official
Qwen2.5 chat template with the system content above, one user message, and one
empty assistant generation prefix. No extra system message, newline, BOS/EOS,
schema retrieval, or repository content may be inserted outside that pinned
template. Fully rendered tokenizer IDs are receipted before generation.

## 7. Retrieval query, documents, and accounting

Actor/probe retrieval and the single updater-side `REFLECT` retrieval use the
same unprefixed query bytes:

```text
objective={NFKC_PUBLIC_OBJECTIVE}
metric={NFKC_PUBLIC_METRIC}
last_action_families={SECOND_LAST_FAMILY}|{LAST_FAMILY}
latest_outcome={PUBLIC_OUTCOME_CLASS}
```

Absent values are the literal `NONE`. Each source field is first NFKC
normalized; any resulting U+000A or `|` is then replaced by one ASCII space,
runs of whitespace collapse to one ASCII space, and outer whitespace is
stripped. The lexical
ranker consumes exactly those unprefixed bytes. The dense query consumes the
UTF-8 bytes of `Represent this sentence for searching relevant passages:`
followed by one byte `0x20`, then immediately the unprefixed query. The prefix
therefore ends in exactly one ASCII space and contains no newline.

Each dense document is the complete canonical live `RECORD` JSON. Query and
document tokenization use the pinned BGE tokenizer with special tokens,
`max_length=512`, right truncation, and no padding for single examples.
Truncation counts and original/tokenized lengths are receipted. BM25 always
uses the full untruncated bytes. Returned actor records are complete and never
truncated, even when their dense index representation was truncated.
For the updater-side `REFLECT` retrieval only, each returned record is wrapped
in its current `RECORD_RECEIPT`; lexical event blocks remain bare. Wrapping
does not change rank, packing order, or the 1,024-token returned-document cap.

Only current records whose status is not `SUPERSEDED` are searchable. A
successful `SUPERSEDE` removes the old document from both indices without
embedding a tombstone and embeds only the replacement. `REVISE` embeds the
replacement current record; `LINK` embeds the changed source; `ADD` embeds the
new record. At most one delta in a `CURATE` object may mutate a given memory
ID, and each of the at most four deltas changes or creates at most one live
dense document. Index replacement is transactional with store commit; failure
rolls both back and there is no retry or background re-index.
During one-hop expansion, a link whose target is absent or `SUPERSEDED` is
retained in the source record for audit provenance but contributes no returned
document and is not redirected to a replacement. A new directed link to the
replacement requires a later valid `LINK` delta. The missing target is counted
and receipted, never silently substituted.

There is exactly one retrieval query before each of 2,880 deployment wake and
1,280 probe continuations, giving 4,160 actor/probe query embeddings per root.
There is exactly one additional query before each of 240 `REFLECT` calls,
giving 240 updater query embeddings. `CURATE` performs no query and creates no
query embedding. Thus the hard total is 4,400 query embeddings/root. At most
four `ADD`, `REVISE`, `LINK`, or `SUPERSEDE` deltas after each program change
at most 960 live-record embeddings/root. Dense embeddings and physical lexical
index operations are accounted separately. Each record delta performs at most
one BM25 live-document insertion and one removal, for at most 960 inserts plus
960 removals/root. Every dispatched deployment-wake action creates at most one
eligible raw-event-block insertion. Probe actions are written only to the
sealed evaluation artifact and never enter the life ledger, store, updater, or
either index; a model-free golden fixture enforces zero persistent probe
mutations. Because one native action envelope is
permitted per each of the twelve wake continuations/program, the five services
add at most `5*48*12=2,880` raw-block inserts/root. Record plus raw-block
indexing therefore performs at most 3,840 inserts and 960 removals, or 4,800
physical BM25 mutations/root. Existing unchanged records are not
re-embedded or re-tokenized; superseded records remain only in the append-only
audit ledger.

## 8. Development and once-only semantic certificate

Development/tuning fixtures and the certificate are disjoint generator seeds
and immutable ID namespaces. After the updater, merger, schemas, prompts,
renderer, query construction, tokenizer/checkpoint revisions, retrieval code,
and thresholds freeze, run the strength certificate once on 100 sealed cases.
Each case contains exact gold `REFLECT` items and exactly one gold `CURATE`
class whose fields are mechanically derivable from its public fixture events
by Section 5. The eight exhaustive `CURATE_CLASS` values are:

```text
ADD_PROVISIONAL, ADD_SUPPORTED,
REVISE_SUPPORTED, REVISE_CONTRADICTED,
LINK,
SUPERSEDE_PROVISIONAL, SUPERSEDE_SUPPORTED,
NOOP
```

For a valid record-bearing delta, its class is its operation joined to the
replacement record's derived status. No other operation/status combination is
legal. The sealed manifest fixes all 100 class labels before the run and has
at least eight cases of every class and at least eight record-bearing cases of
every proposition kind.

Before sealing those cases, deterministic model-free fixtures must cover:
first-seen ordinary `ADD_CONTRADICTED` rejection; redundant within-block event
ID rejection; no revision from an already represented observation identity;
admissible and conflicting multi-item calls; a full-store same-key record
absent from REFLECT retrieval but surfaced with its receipt for CURATE; a
directional process link; and a contract-valid gold-different certificate
commit. They must additionally cover exact prescribed-output boundaries for
one, two, three, and four deltas; a 384-token inclusive pass; a 385-token
`OUTPUT_UNREPRESENTABLE` no-call; and a valid gold-different reflection whose
required CURATE input overflows. Finalized-transition fixtures must cover
16-to-17 support IDs, 16-to-17 counterevidence IDs, 16-to-17 links, and a
256-to-257 stored-record boundary for each applicable `ADD`, `REVISE`, `LINK`,
and `SUPERSEDE` path. Any failure blocks the once-only call.

Certificate gold operations are single-valued by applying the exact operation-
selection law in Section 4, not a separate fixture convention. `ADD` fixtures
have no live gold-key record and exactly one or at least two support
observations for their provisional or supported class. `REVISE` fixtures have
exactly one live same-key/same-signature record plus new evidence that uniquely
derives a supported or contradicted final status while preserving all prior
evidence. `SUPERSEDE` fixtures have exactly one live same-key contradicted
record plus exactly one or at least two newly rendered, internally consistent
observations deriving a different signature as the unique provisional or
supported replacement. `LINK` fixtures contain one valid process reflection,
its live same-key/same-signature process record, no new evidence, and exactly
one eligible unlinked non-process source under the directional rule. `NOOP`
fixtures make every selection rule return no delta. Each fixture displays only
the exact evidence and records required by its gold operation. Generator
rejection enforces these conditions before a case can enter the sealed set.
The generator also constructs the exact gold second-call user bytes and exact
gold prescribed canonical `CURATE` response before sealing, then executes the
complete gold transition on a temporary store through the same production
commit path. A case is rejected unless every fixed input partition fits, every
gold transition invariant and final cardinality/record-length bound passes,
and the gold assistant-response suffix plus exactly one EOS token fits the
384-token output cap under the pinned tokenizer. Thus every sealed gold unit
is executable, while a model-produced gold-different reflection may still
reach the explicit no-call dispositions below.

Scoring is total and has two ledgers, one for `REFLECT` and one for `CURATE`.
A raw empty response, JSON parse failure, or parsed top level that violates any
top-level rule—including schema version, program ID, unknown/missing fields,
required-array type, or array cardinality—produces exactly one false-positive
attempt and no element scoring. For `REFLECT`, that attempt enters the single
REFLECT proposition+guidance precision denominator and every unrecovered gold
item is a false negative. For `CURATE`, it is assigned to that fixture's
presealed `CURATE_CLASS`, so malformed LINK and record cases cannot escape
their respective precision denominators, and the missing gold unit is a false
negative.

When the top level is valid, every array element is one predicted unit. A
valid element is classified by its derived `CURATE_CLASS`. Every invalid
element whose declared operation and replacement status identify exactly one
class is a false positive in that attempted class; every other invalid element
is a false positive in the fixture's gold class. An exact first match to the
gold unit is one true positive. A wrong-class unit is one false positive in
its predicted class; a same-class but field-wrong unit is one false positive
in that class. Every extra or duplicate unit is another false positive. If no
exact unit matched, the fixture contributes one false negative in its gold
class. A correct sole `NOOP` is one `NOOP` true positive; an illegal co-emitted
`NOOP` invalidates the top level under the atomic schema.
REFLECT elements follow the same exact-match/extra/missing rule in the one
REFLECT ledger. An emitted record or reflection is exact only when every
scope, proposition, outcome, value, type/kind, guidance, evidence, transition,
hash, and provenance field matches the mechanically recomputed gold bytes.

For each `CURATE_CLASS`, `precision=TP/(TP+FP)` and
`recall=TP/(TP+FN)`; a zero denominator yields zero. Per-class
`F1=2*precision*recall/(precision+recall)`, also zero when its denominator is
zero. Macro-F1 is the unweighted mean of the eight class F1 values. Micro
precision pools all eight class confusion counts. Record-bearing precision
pools the six ADD/REVISE/SUPERSEDE classes; LINK precision uses the LINK class;
and REFLECT precision uses its separate ledger. At least 0.95 precision is
required for REFLECT, record-bearing CURATE, LINK, and the pooled CURATE
ledger; macro-F1 must be at least 0.85.

The certificate executes the actual dependency. Each case starts from its own
presealed isolated temporary store. The model's raw `REFLECT` is parsed and
scored first. If invalid, `CURATE` is not invoked, its gold class receives one
false negative and no predicted unit, and the store remains unchanged. If
valid, only that accepted canonical model-produced `REFLECT`—never a gold
reflection—is used to construct the exact required CURATE input and exact
prescribed canonical output against the immutable pre-call store. If the
required input exceeds a fixed partition, record `INPUT_OVERFLOW`; otherwise
run the finalized-transition preflight and record
`TRANSITION_UNREPRESENTABLE` if it cannot commit; otherwise record
`OUTPUT_UNREPRESENTABLE` if the prescribed response plus EOS exceeds 384
pinned-tokenizer tokens. In any of these cases `CURATE` is not invoked, the store
remains unchanged, the emitted reflection is scored normally, the fixture's
presealed gold CURATE class receives exactly one false negative, and no CURATE
false positive is added because no second call occurred; the case is never
excluded. Otherwise the accepted reflection is passed to `CURATE`. The raw
`CURATE` is scored, and only an exact
schema/semantic/operation-valid object commits atomically to that case's
temporary store. The commit validator has no access to certificate gold: a
contract-valid path commits even when it differs from the gold reflection or
gold delta, and is then scored predicted-versus-gold. Only schema/semantic
invalidity or mismatch to the prescribed delta list derived from the accepted
model reflection and pre-call store prevents commit. Gold is opened only after
raw responses and the post-commit store are sealed. Cases never share stores,
IDs, records, indices, or ordering effects.

Reusable-record recall has an independent exact gold set: the final canonical
records from every non-NOOP gold `ADD`, `REVISE`, and `SUPERSEDE` fixture.
Each is keyed by its semantic key and exact derived status, proposition,
guidance, citations, and provenance. Recall is the number of distinct gold
records matched exactly in that fixture's post-commit temporary store, summed
across isolated cases, divided by the number of gold records; duplicate
matches within a case count once. It must be at least 0.80. A zero
emitted-unit denominator in any required precision class fails rather than
producing a perfect or undefined score.

A failed once-only certificate cannot be repaired and rescored on those cases.
Repair creates a new version and a newly generated, separately sealed
certificate set; the failed version and all outputs remain public. The
certificate score never admits a scientific-life row or returns to an updater.

Before any development strength call, publish SHA-256 for this entire contract
and for exact extracted bytes of both prompt templates, the system message,
schema/transition tables, query template and dense prefix, canonicalization
rules, and actor insertion template. Ten model-free golden fixtures must hash
the fully instantiated `REFLECT`, `CURATE`, query, store, and actor-input bytes.
Any mismatch blocks the word **strong** and scientific-root spending.
