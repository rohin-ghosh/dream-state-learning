# PCFL-Compose semantic memory and resolver contract v1

**Status:** proposal only; no implementation or run authority.

## Two representation lanes

The primary `OPAQUE_NOTE` lane stores NOTE envelopes. Its model-authored text
is causal through byte-preserved lexical retrieval, but its meaning is never
parsed, truth-scored, normalized, or edited. The separately labeled
`OPERATOR_AST` lane is a structure-assisted open-factor plus matched-independent
diagnostic. It cannot
rescue opaque failure or support the primary result. `audit_explanation` and
reasons in either lane are retained for human audit but never enter a corpus,
index, query result, cut, score, or future training view.

The optional structured lane's active sorts are `TOKEN`, `ACTION`, `OPERATOR`,
`TRAY`, and `BOOL`. Compact term opcodes denote:

| Opcode | Total denotation |
|---|---|
| `TOK`, `VAR` | public literal token; typed bound variable |
| `ACT`, `PACT` | action constructed from two public tokens; public action from one eligible event |
| `EOP`, `PERM` | operator observed in one eligible event; explicit six-slot permutation |
| `CALL`, `OP`, `INV` | call a model-declared function; operator of an action; inverse operator |
| `COMP` | ordered operator composition; element 0 applies first, then element 1 |
| `TRAY`, `APPLY` | literal public tray; apply an operator to a tray |
| `EQ`, `NEQ` | typed equality or inequality |

`PERM.image[input_slot]=output_slot`. The exact extractor, interpreter, target
actor, prediction scorer, and intervention builder use this convention.
`DEFINE`, `ASSERT`, `RULE`, `EXCEPTION`, and `UNRESOLVED` are the only active
statement forms. The model authors every symbol declaration, arity, binding,
variable, guard, permutation, ordered composition, and alternative. The
generic grammar never declares stem/suffix factors, two functions, a gauge,
orientation, a completion equation, a sparse path, or a law menu.

`EOP` is allowed while reasoning about a read public event. Every committed
reusable `DEFINE` or `RULE` must instead be self-contained over explicit
model-authored `PERM` values, public surface tokens, variables, and declared
calls. Target-time Think never dereferences an event. A direct
independent-table program may use a ground `PACT` only for an eligible observed
action and cannot denote an unseen target.

## Canonical bytes and capacity

Canonical JSON is UTF-8 with sorted object keys, no insignificant whitespace,
and separators `(',',':')`; arrays retain authored order. In OPERATOR_AST,
semantic identity is SHA-256 of canonical `s` bytes and record metadata is not
part of the statement hash. In OPAQUE_NOTE, only full canonical NOTE-envelope
byte identity exists; no semantic identity is inferred. Sleep may deduplicate
only the applicable exact-byte/statement hash, retains every original in the
audit log, and unions provenance in a separate compiled envelope without
claiming distinct model outputs were byte-identical.

One opaque note text and one canonical AST record are each at most 256 UTF-8
bytes. An opaque candidate contains at most 13 notes and an AST candidate at
most 13 records. Canonical opaque `notes` or AST `symbols+records` payload is
at most 4,096 bytes; a complete canonical candidate, including predictions and
audit fields, is at most 8,192 bytes. Dream-1's two-candidate commitment is at
most 16,384 bytes. These distinguish the granularity audit's semantic-package
cap from the transport envelope rather than silently applying one number to
three objects.

`fixtures/factorized_13_item_ast.json` is the mandatory 13-item structural
headroom fixture. Under the canonicalizer above it is 2,510 bytes complete,
2,279 bytes for `symbols+records`, and its largest record is 247 bytes. It has
eight first-symbol ground bindings, four second-symbol ground bindings, and
one ordered-composition rule. It is a schema/cap fixture, not a world result or
model output. T06 recomputes these exact counts and rejects any drift.

## Shared recurrent resolver

Dream and Think use the same `RESOLVER_STEP` envelope, parser, and state-update
code. `READ`, `NOTICE`, `CONNECT`, `REVISE`, and `PASS` have byte-identical
semantics in every mode. Mode changes only inputs and terminal permissions:

- `DREAM1`: public source-event handles; may `PREDICT`, `COMMIT`, or `ABSTAIN`.
- `DREAM2`: candidate/public-event handles; may `PREDICT`, `COMMIT`, or
  `ABSTAIN`.
- `THINK`: goal/state/menu plus structured corpus queries; may `USE`, `LOCK`,
  or `ABSTAIN`.

`NOTICE` has at least one premise, `CONNECT` at least two distinct premises,
and cognitive `REVISE` names the replaced node plus new evidence. Node and
record dependency graphs must be acyclic and every committed active statement
must have a path to at least one eligible public event. Citations establish
origin, never truth.

Dream-1 `PREDICT` stages one candidate and exactly `A1,A2`; `COMMIT` copies the
ordered staged candidates. Dream-2 `PREDICT` stages exactly one RETAIN/REVISE
choice and `B1,B2`. RETAIN's representation payload is byte-identical to one
candidate package previously obtained through `READ`: NOTE envelopes for
`OPAQUE_NOTE`, or symbol declarations and records for `OPERATOR_AST`. REVISE
cites a read parent plus public evidence. Dream-2 `COMMIT` has no predictions
and repeats the most recent staged decision, parent IDs, representation
payload, and citations byte-for-byte. The harness then mechanically emits the
standalone DREAM2 artifact containing those bytes plus the already-staged
predictions. ABSTAIN has no active memory fields. PASS mutates nothing. Every
invalid combination is malformed, charges its predeclared slot, and does not
change state.

Dream-2 receives only a handle catalog with candidate IDs, hashes, byte counts,
and order; contents and predictions require explicit candidate-package READs.
The typed reader returns exactly one immutable event or candidate package, or
`NOT_FOUND`. It never compares, infers, ranks, or recommends.

## Sleep, interpreter, and truth boundary

Sleep receives a registry of eligible public event/action IDs and literal
surface tokens, never a private target list. It checks schema, sorts,
declarations, public-reference closure, provenance acyclicity, IDs, caps, and
canonical bytes. It may not evaluate a program, solve a missing binding,
materialize an event operator, infer an inverse, choose a gauge, complete an
action table, add a record, paraphrase, or rank. Changing every private target
manifest must leave Sleep admission, compiled bytes, and indexes identical.

The frozen offline interpreter performs only type checking, substitution of
model-authored definitions, and explicitly denoted finite operator operations.
It never completes undefined terms. Hidden truth enters only after authentic
candidate/corpus/action hashes freeze, when denotations are compared in the
terminal scorer. Exact metrics are prospective A/B trays, well-typedness,
program-level evidence consistency, complete operator accuracy/coverage, and
executed actions. Gauge-dependent DEFINE records are never assigned misleading
standalone truth.

The neutral recurrent opaque arm uses the same NOTE envelope and runs only on
the untouched factorized and matched independent roots. Its exact A/B
predictions, actions, and costs diagnose dependence on explicit process
vocabulary. No opaque note receives a semantic score.

## Exact query and postings

The one shared `READ` transition accepts representation-specific query
payloads. For `OPAQUE_NOTE`, NFC-normalize and case-fold query and NOTE text,
split both into maximal Unicode alphanumeric tokens, and preserve each literal
public `stem::suffix` token plus its already-public two parts. Rank by
descending exact token intersection and then SHA-256 of the unchanged
canonical NOTE envelope; zero overlap is `NOT_FOUND`, and a zero-based cursor
returns the next note. There is no semantic posting or interpretation.

For `OPERATOR_AST`, the query gives up to two exact matches over
`PUBLIC_TOKEN`, `PUBLIC_ACTION`, `RECORD_ID`, `SYMBOL_ID`, or
`STATEMENT_FORM`, an optional statement form, and a zero-based cursor. Sleep
derives postings only by literal AST traversal. Each posting list is ordered
by SHA-256 of the unchanged canonical record bytes; the cursor returns one
record or `NOT_FOUND`. In both representations, query bytes, examined posting
hashes, cursor, returned bytes, calls, and tokens are counted. No embeddings,
paraphrase/stemming, free-text relation normalization, learned ranking,
target-aware prefetch, hidden scan, or solution packet exists.

## Interventions

Whole-corpus authentic/antipode/wrong-life and equal-byte target-independent
sham swaps are valid for SELF. A separate private terminal
`intervention_builder`, invoked only after authentic corpus and target hashes
freeze, may additionally select structured AST nodes by preregistered patterns
for order reversal, orientation deletion, decisive binding replacement, and
matched sham edits. Zero or multiple selector matches is an unavailable cut,
never a manual/LLM choice. Receipts record input hash, selector, node IDs,
replacement source, output hash, and byte delta. Cut artifacts and timings can
reach only isolated cut actors and the terminal scorer; authentic hashes must
be unchanged afterward.

On the independent-table family, the exact program declares unseen targets
unidentifiable. ORACLE_SCHEMA_TEXT and ORIENTATION_DELETED are
`NOT_APPLICABLE`; no hidden target transformation is ever injected as memory.
CLASS_INFORMED_TEXT is a deliberately misspecified-family diagnostic there,
not a ceiling.
