# v2 semantic and memory contract

## Canonical values and NOTE identity

All structured JSON crosses one boundary: reject duplicate member names,
malformed UTF-8, isolated surrogates and other invalid Unicode scalar values,
NaN/Infinity, and non-I-JSON values; validate the applicable closed Draft
2020-12 schema; then serialize with RFC 8785 JCS. No consumer repairs a failed
value. Raw model response bytes are retained in an audit-only store and never
define a NOTE, node, candidate, corpus, index, or model-visible identity.

`NOTE.text` is a JSON string of valid Unicode scalar values. The stored NOTE
identity is the UTF-8 JCS encoding of the parsed, schema-valid NOTE object. No
Unicode normalization, case conversion, or re-escaping of the parsed value is
performed before that identity is computed. Consequently literal and escaped
JSON spellings which parse to the same string have the same stored NOTE, while
canonically distinct composed and decomposed strings remain distinct. A
separate target-blind lexical index may derive NFC/casefold keys under the
pinned Unicode version; the derived key never replaces or rehashes `NOTE.text`
or its containing object.

The staged-object address input is the following exact byte concatenation:

```text
ASCII("pcfl-v2-staged-object") || 0x00 ||
ASCII(object_type_enum) || 0x00 || uint64_be(jcs_byte_length) || jcs_bytes
```

The first literal plus separator is hexadecimal
`70 63 66 6c 2d 76 32 2d 73 74 61 67 65 64 2d 6f 62 6a 65 63 74 00`.
The candidate-commitment domain is analogously
`ASCII("pcfl-v2-candidate-commit") || 0x00`, whose bytes are
`70 63 66 6c 2d 76 32 2d 63 61 6e 64 69 64 61 74 65 2d 63 6f 6d 6d 69 74 00`.
Stage 0 binds golden vectors for both. These SHA-256 values and all paths,
lengths, variants, cache/deduplication state, and storage identities are
harness-only.

## Nodes, manifests, capabilities, and caps

Every accepted `NOTICE`, `CONNECT`, or workspace-`REVISE` response contains
one complete model-authored closed NOTE or AST node. The harness stores it and
then assigns a fixed-shape, collision-free, current-session opaque node
capability. `PREDICT` carries only an ordered manifest of capabilities for
already-authored nodes, exact A1/A2 or B1/B2 predictions, representation,
provenance, parent/decision where applicable, candidate slot, uncertainty, and
bounded audit explanation. It never repeats or authors NOTE/AST payload bytes.
The pure reducer resolves the ordered references and does not invent, rewrite,
translate, score, or repair semantic content.

After a valid `PREDICT`, the harness materializes the complete candidate and
assigns a fixed-shape, collision-free, current-session opaque object
capability. Public event/raw-A handles are direct fixed labels of event kind and
one-based source ordinal. All opaque model-visible public event/raw-A receipt
refs, Dream-1 candidate handles and candidate-read capabilities, target-memory
handles and memory-read receipt refs, and current-session authored node/object
capabilities are deterministic functions of declared topology and zero-based
issuance/source/resolver ordinals under the dedicated `model_visible_identifier` namespace supplied by
`rng_contract.json`. This contract deliberately does not restate or invent the
namespace's cryptographic derivation. These identifiers are not hashes or
encodings of content, addresses, paths, lengths, lane/condition/intervention,
model bytes, cache, or dedup state. When paired treatments have corresponding
topology and ordinals, their identifier values—not merely counts, shapes, and
order—are byte-identical. An identifier is valid only in its declared session
and only after its corresponding release or accepted operation; collisions,
content/treatment dependence, and paired-value mismatches are terminal.

The one coherent capacity table is:

| object | maximum UTF-8 JCS bytes |
|---|---:|
| NOTE value or AST record | 256 |
| complete workspace node | 512 |
| materialized notes-or-records payload | 2,510 |
| complete materialized candidate envelope | 3,072 |

Container overhead and multibyte UTF-8 count toward the relevant limit. The
schema supplies finite member/string/array bounds; the reducer enforces these
canonical-byte caps and candidate/node/state totals before mutation. Active
candidate count is at most two in Dream-1 and one in Dream-2.

## Reads, delivery, and model-visible envelopes

`event_catalog.schema.json` is an operative closed root union. The validator
registers its local hash-bound dependency
`urn:pcfl:compose:semantic-dsl:v2`; network reference retrieval and unresolved
reference fallback are forbidden. Model-visible read results contain only the
event, candidate, NOTE, AST record, or `NOT_FOUND` value permitted by their
discriminated branch.
`AUDIT_READ_RECEIPT` and `AUDIT_BATCH_RECEIPT` contain digests and byte counts
and never enter cognition.

Recurrent Dream obtains each public event through an interactive charged
`READ`: charging and availability validation precede payload release. A fresh
Dream-2 candidate `READ` returns the immutable committed Dream-1 candidate and
assigns the fixed-shape Dream-2-session object capability for that charged read
ordinal. Dream-1 capabilities do not cross the session boundary. Target-time
memory `READ` names the fixed rendered target-memory handle and returns exactly
one unchanged NOTE, one closed AST record, or explicit `NOT_FOUND`, with the
lane-matched query and cursor. Its fixed-shape receipt ref is derived from the
read ordinal, never the result or intervention.

One-shot Dream cannot interactively read. Its renderer mechanically charges
every eligible public event, applies the same event-local extractor, and builds
one ordered `ONE_SHOT_EVENT_BATCH` before invocation. Batch order, event count,
and read charge are model-visible; the canonical byte length and digests exist
only on the non-model `AUDIT_BATCH_RECEIPT`. A noncognitive audit check requires
the batch JCS bytes to equal the source ledger and audit receipt. Dream-1
gets tree events only. Dream-2 gets eligible tree events, raw A, and the
immutable one-shot Dream-1 candidate pool. Neither receives a target packet.
Iterative and one-shot Think receive no source event or extractor record unless
that literal value occurs inside their assigned memory representation.

Every prompt has exactly one `{{INPUT_ENVELOPE_JCS}}` marker. Its replacement
is one length-delimited JCS object containing exactly `contract_version`
(`pcfl-v2`), `mode`, `lane`, `operation_ordinal`, closed `budgets`, closed
`state`, and `last_read_result`, plus only that mode's typed catalog, event
batch, immutable candidate pool, target packet, or AST packet. Irrelevant
members are absent, not populated with ambient state. `last_read_result` is
either the immediately preceding model-visible result or JSON `null`; audit
receipts never appear there. Missing, duplicate, unknown, unused, adjacent, or
unescaped prompt markers fail before invocation.

The assignment/seed ledger's `resolver_ordinal` is exactly zero-based. For an
opportunity with `resolver_ordinal = r`, the rendered pre-operation
`state.resolver_ordinal` is exactly `r`, while the enclosing input
`operation_ordinal` and the model-authored `RESOLVER_STEP.ordinal` are both
exactly `r + 1`. One-shot envelopes use `operation_ordinal = 1` and empty state
`resolver_ordinal = 0`. Thus every field named `operation_ordinal` is one-based;
there is no other offset, and every mismatch fails before state mutation.

Opaque `note_value` is rendered only as a JCS string member under a fixed data
role within that envelope. It is never concatenated into system text, target,
tool, citation, action syntax, or another JSON member. Delimiters, role-like
text, braces, quotes, controls, bidi, and action-like strings can influence the
model as data but cannot create a field, role, capability, citation, or legal
action. This is syntactic isolation, not semantic inertness.

`TARGET_MENU_PACKET` is direct public input released only after corpus freeze;
it is not a pre-Dream catalog handle. The reader receives only its assigned
corpus/index, the fixed target-memory handle, and a Think query. Think receives
the public target/menu, its workspace, fixed target-memory handle, and
model-visible reader result. The actor receives only the public
current tray/menu projection, one schema-valid emitted `USE(stem::suffix)`,
and its sealed transition implementation. `LOCK` is consumed by Think's local
terminal controller and is never serialized on actor IPC—nor does LOCK cause an
actor call. The actor never receives memory, query/receipt, capability,
address, digest, intervention, identity, private truth, or score.

## Terminals and one-shot objects

Dream-1 `COMMIT` names an ordered set of one or two staged current-session
object capabilities. Dream-2 `COMMIT` is exactly one of: `RETAIN` naming the
capability assigned by its charged candidate read and staged RETAIN manifest;
`REPLACE` naming its newly staged replacement; or capability-free `ABSTAIN`.
Every decisive Dream-2 `PREDICT` is legal only after exactly one charged
RAW_A_EVENT read in that Dream-2 session. `PREDICT` includes a nonempty typed
`decision_provenance_receipt_ids` array that resolves only to prior charged
reads and contains the receipt ref of that sole raw-A read, while its manifest
provenance `public_handles` contains the matching raw-A handle; the reducer stores
the array with the staged manifest. Terminal `COMMIT` repeats exactly the
staged decision, the capability issued for that manifest, and that ordered
receipt-ref array. Missing provenance at PREDICT, zero or two raw-A reads,
COMMIT-only provenance, or any COMMIT mismatch is terminal.
Workspace `REVISE` replaces exactly one live workspace node and never a
candidate. Every `ABSTAIN` is terminal, carries no active handle/capability or
payload, and materializes no corpus.

Every atomic envelope uses the dedicated closed `one_shot_resolver_state`,
with phase, `resolver_ordinal=0`, empty `action_prefix`, and `OPEN`; the shared
recurrent `resolver_state` is forbidden because it exposes capability arrays.
One-shot Dream has no node/capability registry. `ONE_SHOT_DREAM1` returns up to
two complete candidates and selects an ordered one-or-two pool by slots defined
inside that same response, or abstains with empty candidates/selection.
Every one-shot candidate, NOTE, and AST-record provenance object has exactly
one member, `public_handles`; capability-named fields and node/object capability
values are rejected, including inside the immutable Dream-1 pool delivered to
one-shot Dream-2.
`ONE_SHOT_DREAM2` RETAIN selects an immutable input `source_dream1_slot`
directly, repeats no candidate bytes, and carries exact terminal B1/B2
predictions. REPLACE carries and selects its sole response-local `D2C01`
candidate with exact B1/B2. ABSTAIN carries neither. It never echoes a harness
capability.
Its non-ABSTAIN `decision_provenance_receipt_ids` resolves to stable public
receipt refs in its event batch and contains at least one raw-A receipt.
Only after an atomic REPLACE validates may the harness address its new selected
bytes. One-shot Think receives only the dedicated closed
`one_shot_ast_memory_packet`; each record is a `one_shot_ast_record` with
`one_shot_provenance`, never the recurrent capability-bearing record. Its
`ONE_SHOT_PLAN` citations use only `one_shot_citation_ref`, whose sole schema
alternative is a public event/raw-A handle; node/object capabilities are not
legal citations. The plan contains exactly four typed, menu-valid `USE` actions
followed by terminal `LOCK`. The executor dispatches only the four USE actions
to the actor; it applies LOCK locally to terminate Think.

## Lane boundary and named runtime rules

Opaque Sleep performs only schema/JCS/cap/provenance/integrity checks and
target-blind indexing. Opaque READ uses literal NFC/casefold alphanumeric and
public `stem::suffix` tokens, ranks by token overlap then audit-only digest, and
returns the unchanged NOTE or `NOT_FOUND`. It has no embedding, synonym or
relation table, semantic parser, model, judgement, truth label, target rank,
no-solution classifier, or content score. At T0 only the target-independent
sham constructor, seed, input projection, and assignments are frozen. The sham
bytes and their receipt materialize after the T2 authentic-corpus freeze and
before any T3 target packet or query becomes visible. The resulting sham is
neither semantically corrupted nor false.

AST remains a separate closed diagnostic representation. Only AST may receive
denotation, true/false substitutions, no-solution scans, minimum-read or
alternate-world witnesses, and record cuts. AST and opaque sessions, nodes,
candidates, corpora, indexes, readers, actions, and reports never mix or rescue
one another.

The reducer and Stage-0 fixtures enforce these named rules in addition to JSON
Schema: `SEM-R01_CANONICAL_BOUNDARY`, `SEM-R02_NOTE_IDENTITY`,
`SEM-R03_LOCAL_SCHEMA_REGISTRY`, `SEM-R04_READ_BEFORE_REVEAL`,
`SEM-R05_CAPABILITY_FRESHNESS`, `SEM-R06_NODE_ANCESTRY`,
`SEM-R07_MANIFEST_ONLY_PREDICT`, `SEM-R08_EXACT_PREDICTION_SET`,
`SEM-R09_PHASE_ALLOWLIST`, `SEM-R10_COMMIT_OWNERSHIP`,
`SEM-R11_ONESHOT_CAUSALITY`, `SEM-R12_CANONICAL_BYTE_CAPS`,
`SEM-R13_LANE_ISOLATION`, `SEM-R14_PROMPT_MARKERS`,
`SEM-R15_ACTOR_FIREWALL`, `SEM-R16_ORDINAL_MAPPING`,
`SEM-R17_DETERMINISTIC_IDENTIFIERS`, and `SEM-R18_DREAM2_RAW_A_PREDICT`.
Any failure is the row's first terminal failure,
mutates no state, and cannot trigger repair or a second scientific attempt.
