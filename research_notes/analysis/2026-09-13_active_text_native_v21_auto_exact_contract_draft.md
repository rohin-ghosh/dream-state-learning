# ACTIVE_TEXT_NATIVE-v2.1-AUTO(q16,B8192): exact proposal contract

**Date:** 2026-09-13 PT  
**Status:** candidate proposal source only; not ratified, implemented, or run  
**Authority:** none. This document authorizes no source edit outside this memo,
materialization, tokenizer/model call, benchmark generation, fit, adapter,
parenting, GPU use, scientific claim, release, or submission.

## 0. Closed object and claim role

The sole claim-bearing evolving textual-memory opponent proposed here is:

```text
ACTIVE_TEXT_NATIVE-v2.1-AUTO(q16,B8192)
```

It is one frozen PCFL child with an append-only branch-local public ledger,
deterministic lexical retrieval, and deterministic traversal over a graph
built only from public transitions that this branch actually witnessed. It
does not train, update parameters, call a reflector, ask the actor to write a
query, or import the supplied exact-address service. A stronger result for
this baseline is a valid result.

The access-only sensitivity is exactly:

```text
ACTIVE_TEXT_NATIVE-v2.1-AUTO(q16,B16384)
```

It doubles returned-memory bandwidth from 512 to 1,024 tokens before each of
the same first 16 actor calls. It adds no actor call, generated token, THINK
opportunity, action, query generator, or retry. `q32` is prohibited.

Other names have disjoint roles:

- `ACTIVE_LINKED_TEXT_SUPPLIED`: supplied exact-address service ceiling only;
- `TEXT_SAME_SEMANTICS`: finite identical-record carrier diagnostic only;
- `RAW_PUBLIC`: the common raw-event lexical lane defined below; and
- `FULL_PUBLIC_HISTORY` and `EXACT_WITNESSED_GRAPH`: certificate ceilings,
  not longitudinal opponents.

This proposal closes all nine P0 fields identified by the fresh audit. It
chooses independent world/writer roots conditional on one fixed child and
chooses a common automatic `RAW_PUBLIC` lane for every longitudinal system.

## 1. Normative byte and hash rules

All persisted text is strict UTF-8. CR (`0x0d`), a UTF-8 BOM, invalid UTF-8,
NaN, infinity, and duplicate JSON keys are forbidden. JSON is RFC 8785/JCS.
`JCS(x)` means the exact RFC 8785 UTF-8 bytes with no terminal LF. A JSONL
record is `JCS(x) || 0x0a`. SHA-256 is FIPS 180-4 and lowercase hexadecimal.
Base-10 integers have no sign, decimal point, exponent, or leading zero except
the integer zero. Array order is meaningful. There is no Unicode repair.

The proposal uses these exact ASCII schema literals:

```text
ATN_EVENT_V1
ATN_INTERPRETATION_V1
ATN_DOCUMENT_V1
ATN_QUERY_V1
ATN_MEMORY_V1
ATN_INDEX_V1
ATN_ROOT_V1
```

No implementation/library default is normative. A future implementation must
bind the exact Python/runtime, model revision, tokenizer files, chat template,
context limit, PCFL public renderer, action fullmatch parser, scorer, world
generator, and this file's exact bytes before P1. Those receipts instantiate
this contract; they may not change it.

## 2. Root, branch, and identifier law (P0-3, P0-9)

### 2.1 Statistical unit

The paper estimand is conditional on one fixed, parent-deleted, sealed child.
One independent lifetime root is one preallocated tuple:

```text
(world_seed_256, writer_seed_256, schedule_seed_256, decode_seed_256,
 root_salt_seed_256)
```

All five 256-bit values are sampled before any world content for that root is
generated. The root salt is:

```text
root_salt = SHA256(bytes.fromhex(root_salt_seed_256) ||
                   b"ATN_ROOT_SALT_V1")
```

The world generator is forbidden to receive `root_salt_seed_256` or
`root_salt`. The writer is forbidden to receive world answers beyond ordinary
public experience. The root is then forked from the byte-identical sealed
child into `DLT_PERIODIC`, `SLEEP_FROZEN`, and `ATN`. All failures remain in
intention-to-treat. A task, cut, surface twin, decode, store mutation,
same-history read, or checkpoint is a repeated measure and never increases
`n`. Certificate, DEV, profile, RS8-qualification, and lifetime roots are
mutually disjoint.

### 2.2 Equality-only public identifiers

On the first public appearance of an exact public identifier byte string `p`,
create:

```text
digest = SHA256(root_salt || p)
OID(p) = b"OID/" || lowercase_hex(digest[0:16])
```

`root_salt` is exactly 32 bytes; therefore the concatenation is unambiguous.
`p` is the exact case-sensitive UTF-8 identifier, with no normalization or
prefix/type byte. `OID` exposes 128 hash bits and no type, role, module,
ordinal, action order, answer, branch, or future-inventory bit. The mapping is
created online only; future identifiers are absent. If two distinct `p` map
to one OID, the root terminates `IDENTIFIER_COLLISION`; it is retained as a
failed root and is not re-salted or redrawn.

Structured public fields are replaced by their OIDs directly. In child prose,
registered identifiers are replaced longest-byte-string first, then
lexicographically, only when both adjacent bytes (if present) are not ASCII
`[A-Za-z0-9_]`. Overlapping nonidentical matches terminate the root. OIDs are
used only for ranking/graph arithmetic. Actor rendering restores the exact
original public bytes. Hash/event/document/citation IDs are never treated as
world identifiers.

## 3. Authoritative ledger and lifecycle (P0-1)

### 3.1 One public dispatch, one event

Every ordinary action actually dispatched by a scientific branch produces
one body with exactly these keys:

```json
{
  "action_public":"UTF8_STRING",
  "decision_index":0,
  "episode_instance":0,
  "module_public":"UTF8_STRING_OR_EMPTY",
  "objective_public":"UTF8_STRING_OR_EMPTY",
  "occurrence_index":0,
  "outcome_public":"UTF8_STRING",
  "public_status":"UTF8_STRING_OR_EMPTY",
  "schema":"ATN_EVENT_V1",
  "state_before_public":"UTF8_STRING_OR_EMPTY",
  "transition":null
}
```

For an ordinary public transition receipt, `transition` instead is exactly:

```json
{"destination":"PUBLIC_ID","port":"PUBLIC_ID",
 "receipt":"PUBLIC_ID","source":"PUBLIC_ID"}
```

Every nonempty transition field must occur verbatim in the already-visible
action or outcome receipt and must be derivable by the frozen public receipt
parser. Otherwise `transition` is `null`; no hidden parser may fill it. Invalid
actions and negative outcomes are retained. Private scores, routes, answers,
necessity labels, future fields, evaluator labels, cut labels, and arm labels
are absent.

Let `body_bytes=JCS(body)` and:

```text
event_id = "EV/" + SHA256(b"ATN_EVENT_V1\x00" || body_bytes)
```

The authoritative event JSONL record is exactly
`JCS({"body":body,"event_id":event_id}) || 0x0a`.
The scientific root and branch are custody metadata in an outer manifest and
never indexed or actor-rendered. Re-ingesting the same dispatch receipt is a
fatal duplicate-ingest error. Different real dispatches remain different via
their episode/occurrence/decision coordinates even when their text matches.

The raw event becomes visible to the same episode at its next ordinary actor
continuation. It is invisible to sibling episodes until every member of that
batch round has either dispatched once or terminated. At that barrier, queued
events commit in ascending
`(module_public UTF-8 bytes, episode_instance, occurrence_index,
decision_index, event_id)` order. Device completion, Python consumption,
cache, and insertion order never alter visibility.

### 3.2 Exact child interpretations

Only an ordinary child turn at a predeclared common formation opportunity may
create an interpretation. There is no ATN-only generation and no reflector.
The accepted one-line physical grammars are:

```text
EVENT E_[A-Z2-7]{10} AT N_[A-Z2-7]{10} DID P_[A-Z2-7]{10} GOT N_[A-Z2-7]{10} EVIDENCE R_[A-Z2-7]{10}
LINK L_[A-Z2-7]{10} FROM E_[A-Z2-7]{10} THEN E_[A-Z2-7]{10} VIA N_[A-Z2-7]{10} EVIDENCE R_[A-Z2-7]{10},R_[A-Z2-7]{10}
MODEL S_[A-Z2-7]{10} AFFINE4X2 A [01]{8} B [01]{2} EVIDENCE R_[A-Z2-7]{10}(,R_[A-Z2-7]{10}){7}
```

The full raw response must match one grammar with no CR/LF. `MODEL` receipt
IDs must be in public ordinal order. A mechanical validator checks only
syntax, root, already-public cited receipts, and source-evidence consistency.
For `MODEL`, consistency is checked against the eight public source outcomes
only; target descriptors, target labels, affine parameters, candidates, and
the solver are inaccessible.

Each attempted child turn produces one interpretation body:

```json
{
  "attempt_bytes":"EXACT_CHILD_UTF8",
  "creation_frontier":0,
  "episode_instance":0,
  "occurrence_index":0,
  "public_reason":"EXACT_ACTOR_VISIBLE_REASON_OR_EMPTY",
  "public_status":"ACCEPTED_OR_REJECTED",
  "schema":"ATN_INTERPRETATION_V1",
  "source_event_ids":["EV/HEX64"]
}
```

`interpretation_id = "IN/" +
SHA256(b"ATN_INTERPRETATION_V1\x00" || JCS(body))`. The exact attempt is stored
as `JCS({"body":body,"interpretation_id":interpretation_id}) || 0x0a`, once.
A rejection reason is included only if those exact bytes were returned
to the ordinary actor at that frontier; private validator codes remain only
in the custody log. Accepted and rejected attempts are lexical documents.
They never create graph edges.

Interpretations become eligible only at the common authenticated SLEEP/
formation barrier, in ascending `(creation_frontier, episode_instance,
occurrence_index, interpretation_id)` order. They cannot become visible
mid-batch. Query text, retrieval output, compiler paraphrases, DREAM replay,
optimizer presentations, canaries, probes, exams, certificates, reports, and
evaluator products never become documents.

### 3.3 Duplicate and supersession law

Every unique dispatch and every unique child turn appears exactly once.
Re-ingestion of an existing event/interpretation ID fails closed. Semantically
similar but genuinely distinct public experiences remain distinct. This
version has no mutation or supersession operation: every document remains
live forever, and any non-null supersession field or deletion request is
`UNSUPPORTED_MUTATION`. Evaluation descendants are read-only and leave the
ledger, index, cache, and query-state roots byte-identical to run-skipped
controls.

## 4. Exact searchable documents and graph (P0-4, P0-8)

### 4.1 Actor row and ranking row

Each event creates one `RAW_PUBLIC` document. Each interpretation creates one
of `EVENT_INTERPRETATION`, `LINK_INTERPRETATION`,
`MODEL_INTERPRETATION`, or `REJECTED_INTERPRETATION`. Its immutable ID is:

```text
document_id = "DOC/" +
 SHA256(b"ATN_DOCUMENT_V1\x00" || kind_utf8 || b"\x00" ||
        source_record_id_utf8)
```

The exact actor-visible row is:

```text
MEMORY <JCS({"citation":document_id,"kind":kind,
             "payload":public_payload,
             "sources":ordered_source_event_ids,
             "status":public_status})>\n
```

For `RAW_PUBLIC`, `public_payload` contains only `module_public`,
`action_public`, `outcome_public`, `public_status`, and `transition` from the
event. For interpretation documents it is the exact `attempt_bytes` and, when
nonempty, exact `public_reason`. Root/branch/cut/score metadata is absent.
The ranking row is the same row after structural public-ID replacement by OID.
Every row, including its LF, must encode to at most 384 pinned-child tokens;
otherwise the root is `BASELINE_INVALID_ROW` rather than silently dropping or
truncating the row.

The authoritative document JSONL record is exactly the JCS serialization of
the following object plus one LF; the quoted metavariables below describe
types and are not literal wire values, and there are no optional keys:

```json
{"creation_frontier":0,"document_id":"DOC/HEX64",
 "episode_instance":0,"kind":"ONE_KIND_ABOVE","occurrence_index":0,
 "payload":"PUBLIC_PAYLOAD_OBJECT_OR_STRING","schema":"ATN_DOCUMENT_V1",
 "source_event_ids":["EV/HEX64"],"source_record_id":"EV_OR_IN_ID",
 "status":"ACCEPTED_OR_REJECTED_OR_EXACT_PUBLIC_STATUS"}
```

For RAW, `source_event_ids=[event_id]`, `source_record_id=event_id`, and
`status` is its exact public status (empty is legal). For interpretations,
sources/status are copied exactly from the interpretation record. The only
two payload shapes are exactly:

```json
{"action":"UTF8","module":"UTF8","outcome":"UTF8",
 "public_status":"UTF8","transition":null}
{"attempt":"UTF8","public_reason":"UTF8"}
```

The first is RAW (with the event's non-null transition object substituted
when present); the second is every interpretation kind.

`creation_frontier` is the presealed schedule's monotonically increasing
public barrier integer. It begins at zero and increments by one at every
global batch or authenticated formation barrier. Same-episode next-turn
visibility uses a task-local overlay until that event's global barrier; the
overlay is destroyed at commit. The schedule, not process completion, supplies
the integer.

### 4.2 `AUTO_WITNESSED_GRAPH`

The graph is a directed simple graph containing a vertex for each live
`RAW_PUBLIC` document and each OID in its non-null transition. For witnessed
`source --port--> destination`, add exactly these six unit-weight arcs:

```text
OID(source)      -> DOC(event)
DOC(event)       -> OID(source)
OID(port)        -> DOC(event)
DOC(event)       -> OID(port)
OID(destination) -> DOC(event)
DOC(event)       -> OID(destination)
```

Identical arcs collapse to one. This bidirectional incidence permits forward
and backward access while the document payload preserves transition direction.
There are no event-to-event, raw-co-occurrence, inferred transitive, child
LINK, MODEL, receipt-only, goal, answer, candidate, family, hidden-world,
cut-registry, or evaluator edges. Graph construction receives only eligible
public event bodies. Thus it can connect witnessed transitions through a
shared public symbol, but it cannot know an unwitnessed edge.

`MODEL_INTERPRETATION` is included now, not by a later silent extension. It is
a lexical cited document searchable by public SERIES and descriptor language.
It never becomes a graph vertex/edge or an affine-solver feature. RS8 gives
the same MODEL formation opportunity to all carriers. Candidate scoring, if
run, constructs automatic query 1 once before candidates are appended and
then scores the four continuations with zero condition-specific generated
queries. The claim-bearing integrated-route panel remains candidate-free.

## 5. Exact automatic query (P0-2)

Before actor calls 1 through 16, build one query from only these three inputs:

1. exact current `objective_public`;
2. exact current `state_public`; and
3. exact previously accepted task-local `THINK` responses, oldest to newest.

The retriever API has no argument or filesystem/API capability for a correct
answer, route, candidate list/order, necessary bundle, cut, carrier/arm,
adapter, future task/inventory, hidden world, evaluator, score, report, or
certificate registry. The task renderer supplies a separate
`retrieval_public_projection`; it contains objective/state only and is hashed
before candidates or answer custody is opened.

The exact query object is:

```json
{"objective":"UTF8_STRING_OR_EMPTY","schema":"ATN_QUERY_V1",
 "state":"UTF8_STRING_OR_EMPTY","think":["EXACT THINK RESPONSE"]}
```

Ranking bytes are `JCS(query)` after OID replacement. Missing objective or
state uses the empty string; no other sentinel is legal. The objective+state
query with an empty `think` array must be at most 1,024 pinned-child tokens.
The total query cap is 2,048 tokens, `add_special_tokens=false`. Starting with
the newest THINK, retain the largest suffix of whole THINK strings that keeps
the complete JCS query at or below 2,048 tokens, then restore chronological
order. Oldest whole THINK records are dropped first; no record or token is
partially truncated. The kept/dropped record IDs and token IDs are receipted.
If the empty-THINK query exceeds 1,024 or 2,048 tokens, the task is invalid;
objective/state are never truncated.

Query term frequency is binary: repeated query tokens count once. Query text
is task-local ephemeral state and never enters lifelong storage.

## 6. Frozen retrieval and packing arithmetic (P0-5)

### 6.1 Lexing and BM25

Apply Unicode NFKC, then Unicode lowercase, then extract maximal ASCII runs
matching `[a-z0-9_/]+`. The result, in occurrence order, is the lexical token
sequence. Document term frequency is ordinary count. Query term frequency is
one. All live documents share one document-frequency universe. With `N`
documents, document length `dl`, mean length `avgdl`, `k1=1.2`, `b=0.75`:

```text
idf(t) = ln(1 + (N - df(t) + 0.5)/(df(t) + 0.5))
BM25(d,q) = sum_t idf(t) * tf(t,d)*(k1+1) /
            (tf(t,d) + k1*(1-b+b*dl/avgdl))
```

If `N=0`, return the canonical miss. If `N>0` and all documents are empty,
`avgdl=1.0`. Documents with score exactly `0.0` are absent from the positive
set. Compute in IEEE-754 binary64 in the sealed CPython environment, using
`math.log`, no FMA, and sorted lexical-token/document-ID order. Serialize
diagnostic floats with `float.hex()`. Exact bit equality is a tie; there is no
epsilon tie.

Let `L(d)=BM25(d)/sum_positive BM25`. If the denominator is zero, `L=0`.
Every BM25 and normalization sum accumulates in ascending lexical-token then
document-ID order.

### 6.2 PPR and fusion

For ATN, select the top 16 positive-BM25 graph document vertices, ordered by
descending BM25 then ascending `document_id`. Their restart weights are BM25
normalized over those seeds. If none exists, graph mass is absent.

When seeds exist, start `p[0]=restart` and run exactly 20 iterations in
ascending vertex-ID order:

```text
p[n+1] = 0.20*restart +
         0.80*(transpose(P)*p[n] + dangling_mass*restart)
```

`P` is row-stochastic over outgoing arcs sorted by destination ID. Parallel
arcs have already collapsed. Accumulation order is ascending source ID then
destination ID. Let `G(d)` be `p[20]` renormalized over graph document
vertices. If its denominator is zero, `G=0`.

If graph seeds exist, every document has `S(d)=0.5*L(d)+0.5*G(d)` (non-graph
documents have `G=0`). If graph seeds do not exist, `S(d)=L(d)`. The common
`RAW_PUBLIC` lane indexes only raw documents and uses `S(d)=L(d)` with no PPR.

### 6.3 Complete-row MMR pack

One retrieval block is exactly:

```text
MEMORY_BEGIN ATN_MEMORY_V1
<zero or more complete MEMORY rows>
MEMORY_END
```

including the LF after every displayed line. With zero selected rows, insert
the exact line `MISS\n` between begin and end. The entire block, wrappers and
rows included, is charged to the return cap.

If any positive-BM25 `RAW_PUBLIC` row fits, select the highest-BM25 raw row
first (ties: newer frontier, then smaller document ID). Then greedily select
from all unselected positive-`S` documents by:

```text
MMR(d) = 0.8*S(d) - 0.2*max_j Jaccard(tokens(d),tokens(j))
```

For an empty selected set similarity is zero; empty-union Jaccard is zero.
At each step ties use higher `S`, newer `(creation_frontier,
episode_instance,occurrence_index)`, then smaller document ID. A row that does
not fit is permanently skipped for this retrieval; continue to the next row.
Rows are never truncated or split. A document occurs at most once within a
block but may recur on later calls. Stop when no remaining complete row fits.
Scores/ranks/OIDs/cache data are not rendered.

The primary per-call block cap is 512 tokenizer tokens and cumulative cap is
8,192. The sensitivity per-call cap is 1,024 and cumulative cap 16,384. A
MISS/repeat/unused opportunity is charged; no replacement call occurs. Exact
ranking/packing bytes, including floats, empty, ties, overflow, restart, and
wrong-root cases require independent byte goldens.

## 7. Common raw lane and actor transport (P0-6, P0-7)

### 7.1 One raw lifecycle

`DLT_PERIODIC`, `SLEEP_FROZEN`, and ATN receive the exact same event ledger,
visibility frontier, automatic query, q16/B8192 envelope, BM25 implementation,
and raw document bytes on their own branches. DLT and SLEEP_FROZEN retrieve
`RAW_PUBLIC` only. ATN uses the same single envelope to rank raw plus child
interpretation documents and `AUTO_WITNESSED_GRAPH`; it receives no extra
memory tokens. No separately duplicated `RAW_RAG` arm exists.

The DLT arm may additionally use its learned adapter; SLEEP_FROZEN may not
promote post-fork writes; ATN freezes its inherited parameters and learns only
by appending public documents. Consequently the comparison is between total
systems with a shared raw textual floor, not a pure substrate comparison.

### 7.2 Exact LF-framed physical turn

The exact common system message bytes, excluding a terminal LF, are:

```text
You are the PCFL actor. Use only the public task, public state, your earlier accepted THINK lines, and any cited MEMORY rows shown in this task. Identifiers are opaque and case-sensitive. Respond with exactly one physical line: either THINK followed by nonempty reasoning, or one final action matching the task's printed final grammar. Never combine thought and action. Never invent or repair an identifier. No external READ command is available; memory is inserted automatically. A malformed, multiple, late, or wrong-family action receives no repair or retry.
```

The first user message is exactly this length-framed concatenation, with each
`<N>` replaced by the UTF-8 byte length in canonical decimal and each blob
inserted verbatim:

```text
PCFL_TASK_V1
OBJECTIVE_UTF8_BYTES <N>
<objective_public>
STATE_UTF8_BYTES <N>
<state_public>
PUBLIC_TASK_UTF8_BYTES <N>
<public_task_bytes>
FINAL_GRAMMAR_UTF8_BYTES <N>
<one exact allowed final fullmatch grammar>
```

Before each of actor calls 1--16, append one user message exactly:

```text
AUTOMATIC_MEMORY_V1
<complete retrieval block>
Respond now with exactly one permitted physical line.
```

For direct FULL/EXACT ceilings the presealed direct mount is appended once
before call 1 and the retrieval block is the canonical MISS block thereafter.
The FULL mount is exactly:

```text
FULL_PUBLIC_HISTORY_BEGIN
<every eligible MEMORY row in creation-frontier/episode/occurrence/document-ID order>
FULL_PUBLIC_HISTORY_END
```

with one LF after every line, including the last. The EXACT mount is exactly:

```text
EXACT_WITNESSED_GRAPH_BEGIN
WITNESS <document_id> <source_public_id> --<port_public_id>--> <destination_public_id>
EXACT_WITNESSED_GRAPH_END
```

with one WITNESS line per non-null RAW transition, ordered by creation
frontier then document ID, and one LF after every line. These projections use
only public event records. If either direct mount cannot fit the 32,768-token
context with the common output reserve, its ceiling fails; it is never
truncated.
For `NONE_SHAM`, insert only a presealed target-independent 512-token neutral
block at the same 16 positions. Define candidate `SHAM(n)`, for integer
`n=0..65535`, as the strict UTF-8 bytes below with `(" neutral" repeated n)`
substituted for `<R>`:

```text
MEMORY_BEGIN ATN_MEMORY_V1
SHAM context-position control only.<R>
MEMORY_END
```

including the final LF. Under the pinned tokenizer with
`add_special_tokens=false`, choose the smallest `n` whose complete block is
exactly 512 tokens. Failure to find one before root materialization stops the
certificate. The same chosen bytes are used at every sham position and
contain no public identifier, task word, answer, candidate, or root byte.
This is an equal-position/full-primary-bandwidth context sensitivity, not a
scored replacement baseline.

Generation uses LF as a stop string and excludes the LF from returned bytes.
The complete decoded response must be strict UTF-8 and contain no CR or LF;
there is no trimming, normalization, extraction, fence removal, or repair.
`THINK` is valid iff it begins with exact ASCII `THINK ` and its remainder has
at least one non-whitespace Unicode code point. A task-final response must
fullmatch the one grammar printed in the task. The exact available final
grammar languages are:

```text
ROUTE N_[A-Z2-7]{10} N_[A-Z2-7]{10} : P_[A-Z2-7]{10}(,P_[A-Z2-7]{10})*
PROBE Q_[A-Z2-7]{10}
EXPLORE N_[A-Z2-7]{10} P_[A-Z2-7]{10}
EVENT E_[A-Z2-7]{10} AT N_[A-Z2-7]{10} DID P_[A-Z2-7]{10} GOT N_[A-Z2-7]{10} EVIDENCE R_[A-Z2-7]{10}
LINK L_[A-Z2-7]{10} FROM E_[A-Z2-7]{10} THEN E_[A-Z2-7]{10} VIA N_[A-Z2-7]{10} EVIDENCE R_[A-Z2-7]{10},R_[A-Z2-7]{10}
MODEL S_[A-Z2-7]{10} AFFINE4X2 A [01]{8} B [01]{2} EVIDENCE R_[A-Z2-7]{10}(,R_[A-Z2-7]{10}){7}
```

These specify regex languages; literal spaces are one ASCII space and neither
regex delimiters nor a terminal LF appears in model text. Only the one printed
family is legal for that task.

Calls 1--16 may end the task with a legal final or continue with THINK. After
a valid THINK, append its exact assistant bytes; the next automatic memory
message is the only continuation. If call 16 is THINK, append exactly this
user message and make one unassisted call 17:

```text
FINAL_OPPORTUNITY_V1
No more THINK responses are permitted. Return exactly one final action matching the task's printed final grammar.
```

Call 17 must be a legal final. The cumulative actual actor-output cap is 2,048
pinned-tokenizer tokens across all calls; each call requests
`min(256,2048-used)` tokens. A zero remainder, invalid turn, backend
truncation, context overflow, extra call, or nonfinal call 17 fails the task.
All conditions share task bytes, prompts, stop bytes, fullmatch parser,
16+1 calls, generated-token cap, terminal opportunities, decode addresses,
and scorer. Automatic retrieval consumes no actor call or output token.

The execution context limit is fixed to 32,768 tokens for this named
configuration. Preflight reserves 256 output tokens before admitting input;
no task/state/THINK/memory byte may be silently truncated. Every prompt stores
exact kept input IDs, output reserve, output IDs, memory IDs, and prefix hash.

## 8. Candidate/target blindness and same-history law

Before every retrieval, the retriever process receives only: frozen config,
root salt/mapping, eligible branch ledger, `objective_public`, `state_public`,
accepted local THINK bytes, and tokenizer. It runs in an allowlisted process
with no other path/network capability. Mutation of candidate order/text,
answer, hidden graph, necessary-bundle/cut registry, future world, carrier
label, evaluator, report, or certificate result at fixed public bytes must
leave query, ranks, block bytes, and hashes identical.

At a same-DLT-history cut, a disposable read-only ATN contains exactly once
every DLT public event and exact DLT child interpretation eligible at that
frontier under sections 3--4. It contains no DLT DREAM/compiler prose,
optimizer replay, adapter state, latent proposition, answer, inferred hidden
edge, or evaluator output. It uses DLT-created interpretations and ATN access,
so this is named a **same-history conditional system/access contrast**, never
a pure carrier or DREAM contrast.

Truthful-twin and necessary-cut stores are generated and sealed before actor
execution. The runtime retriever sees only the resulting public documents,
not the mutation label or hidden registry. Wrong-root stores retain the donor
salt/mapping and may never translate donor OIDs with the recipient salt.

## 9. Certificate roots, conditions, gates, and access sensitivity

Use four fresh, permanently excluded roots conditional on the one fixed
child. Each root has exactly:

```text
2 information strata (opaque binding, reusable structure)
x 4 endpoints (route, same-evidence/different-goal,
               delayed OLD+NEW, expansion)
x 2 presealed surface/order twins
= 16 tasks/root; 64 tasks/condition
```

No reusable task contains an identical answer row. The four endpoint families
map respectively to the preassigned `ATOM`, `BRIDGE_EVENT`, `OLD`, and `NEW`
cuts, so each cut family has exactly four designated cases/root. The older
`LINK`-cut requirement is deliberately not inherited: the strong automatic
witnessed graph must not depend on a child LINK document. `BRIDGE_EVENT`
removes the preassigned public bridge event document and its six witnessed
arcs. Child-LINK causality remains a separate DLT mechanism test. Every store is padded
prospectively with eligible public distractors to the exact 571-semantic-block
cut-4 cardinality and registered token/type marginals. Actor-visible and
model-free maximum-load checks use those exact stores.

If both bandwidths fit P3, run these ten conditions once:

1. `FULL_PUBLIC_HISTORY` (all eligible public rows, chronological direct mount);
2. `EXACT_WITNESSED_GRAPH` (all exact public witnessed edges, direct mount);
3. primary ATN q16/B8192;
4. common `RAW_PUBLIC` q16/B8192;
5. `NONE_SHAM`;
6. ATN truthful binding twin q16/B8192;
7. ATN registered necessary cut q16/B8192;
8. ATN irrelevant same-root store q16/B8192;
9. ATN wrong-root store q16/B8192; and
10. ATN q16/B16384 access-only sensitivity.

FULL and EXACT mounts are deterministic projections of public witnessed
records only; neither may consult hidden routes/answers. The exact graph is an
explicit actor-readable adjacency rendering, not a solver. If B16384 fails P3
fit, condition 10 is mechanically omitted, P4 has nine conditions, access
saturation is unmeasured, and primary certification may continue.

The mutations are exact and presealed. Each cut case names exactly one public
source `event_id`; cutting it removes its RAW document, every interpretation
document whose `source_event_ids` contains it, and its six witnessed arcs.
The cut registry is custody-only and is inaccessible to query/ranking. A truthful twin replaces only the
registered public binding rows with a second fully public, internally
consistent outcome tape while keeping task bytes and row counts fixed, then
recomputes event/document hashes and graph from those public bytes. A cut
is applied before indexing. `IRRELEVANT_STORE` contains 571 eligible same-root public
blocks from preallocated unused modules with no public identifier or lexical
task token shared with the queried module. `WRONG_ROOT_STORE` uses the next
certificate root cyclically `(0<-1<-2<-3<-0)`, retaining the donor salt,
identifiers, rows, and graph. The runtime receives none of the mutation names.

All cases stay in the denominator. Primary certification is
`GO_STRONG_NAMED_CONFIG` iff all are true:

- model-free P1/P2 identity, leakage, restart, and source gates remain exact;
- FULL, EXACT, and primary ATN each succeed on at least 60/64, with no root
  below 14/16;
- each has legal finals on at least 61/64;
- every returned citation/source join is exact and no false citation occurs;
- primary ATN returns the complete preassigned necessary public bundle
  somewhere in B8192 for at least 60/64, no root below 14/16;
- among FULL-solved cases, primary ATN loses at most three pooled and at most
  one on any root;
- truthful twins redirect the registered action on at least 12/16 per root;
- relative to the primary, each `ATOM/BRIDGE_EVENT/OLD/NEW` cut family changes success to failure on at
  least three of its four designated cases on every root;
- irrelevant and wrong-root conditions each differ from NONE in success count
  and legal-final count by at most 3/64, and wrong-root has zero donor citation;
- FULL-minus-NONE and EXACT-minus-NONE success are each at least 7/64
  (the integer realization of headroom >=.10); and
- reusable-structure primary ATN succeeds on at least 30/32.

Failure of FULL/EXACT is `TASK_OR_ACTOR_INVALID`. Failure of primary ATN is
`BASELINE_INVALID`; it can never count as a DLT win. RAW has no threshold.
The primary is never selected from these results.

For the sensitivity define per root normalized-utility difference
`d_r=U_B16384-U_B8192` over that root's same 16 tasks and
`d=mean(d_r)`. `d>0.05` is `NO_ACCESS_PLATEAU`; a non-fit is
`ACCESS_SENSITIVITY_UNMEASURED`. Neither invalidates an otherwise passing
q16/B8192 named comparator. A flat four-root difference is descriptive only
and never licenses “saturated.” A significant negative sensitivity is
degradation, not plateau.

## 10. Exact stages, costs, and stops

### P0: this proposal

Zero model/tokenizer calls, fits, updates, GPU-hours, scientific roots, and
materialized benchmark rows. A fresh audit must find one value/algorithm for
all nine P0 fields. Any undefined default, normative import from
`ACTIVE_TEXT_FIXED`, supplied-address lookup, target/candidate input, hidden
edge, model reflector, or unresolved either/or is `REWORK_P0`.

### P1: store/index, CPU only

Implement the event/interpretation ledger, OIDs, documents, RAW BM25, graph,
PPR, fusion, MMR, packing, citations, barriers, and immutable rebuild. Zero
model/tokenizer calls, fits, updates, and GPU-hours. Hard resource ceiling:
8 CPU-hours, 16 GiB peak RAM, 5 GiB persisted fixtures. Exceeding it stops P1.
An independent checker must reconstruct byte-identical roots without importing
generator helpers. Any lifecycle, taint, rename, order, restart, cache,
store-swap, graph, packing, overflow, or run/skip mismatch stops P1.

### P2: common actor integration, CPU/injected only

Implement the exact transport and inject recorded responses; no model call,
fit, update, or GPU use. Hard ceiling: 4 CPU-hours, 16 GiB RAM, 5 GiB fixtures.
Cap-1/cap/cap+1, malformed/mixed, empty/full, wrong-root, context, terminal,
and run/skip tests must all pass. Any carrier-specific parser, retry, fallback,
generation opportunity, private byte, or backend truncation stops P2.

### P3: prompt/device profile, excluded technical material

After P2 and an authentic TSJ pass, profile store loads 0, 157, and 571 at
actor positions 1, 8, and 16, cold and warm, with three repeats:

```text
3 loads * 3 positions * 2 thermal states * 3 repeats = 54 calls/bandwidth
```

Run primary B8192 first (54 calls); if it fits, run B16384 (54 calls). Maximum
is 108 calls, 27,648 generated tokens, zero fits/updates, and four A40-hours
(two per bandwidth). These calls are profiling only and never enter `n` or a
store. Any truncation fails that bandwidth. Let `t_max` be maximum occupied
device seconds/call across the applicable exact profiles. Before P4 set its
reservation to `ceil(1.5*calls_max*t_max/360)/10` A40-hours; if this exceeds
24.0, stop P4 rather than shrink access.

### P4: maximum-load certificate

With B16384: 10*64=640 tasks, at most 10,880 actor calls and 1,310,720
generated tokens. Six B8192 retrieval conditions plus one B16384 condition
return at most:

```text
6*64*8192 + 1*64*16384 = 4,194,304 tokens.
```

Without a fitting B16384: 9*64=576 tasks, at most 9,792 calls, 1,179,648
generated tokens, and `6*64*8192=3,145,728` returned tokens. Direct FULL/
EXACT input and sham input are counted separately from returned-memory tokens.
The reservation is the P3 formula and never exceeds 24 A40-hours. A partial
root is a retained failure; no redraw/retry/drop.

### P5: five-cut lifetime, staged

Only after PCFL DEV, writer-scale qualification, authentic TSJ, and P4 primary
pass, run the ATN on-policy branch at five cuts:

```text
16 roots * 5 cuts * 40 tasks = 3,200 tasks
3,200 * 17 = 54,400 max calls
3,200 * 2,048 = 6,553,600 max generated tokens
3,200 * 8,192 = 26,214,400 max returned-memory tokens.
```

DLT_PERIODIC and SLEEP_FROZEN run from the byte-identical fork with their
common RAW_PUBLIC lanes; their costs are reported separately. Test root-first
lifetime AUC, terminal utility, retention/acquisition/recombination/expansion,
legality, citations, required rows, and native resources.

Per-root utility at cut `c` is the arithmetic mean of the 40 registered
task-utility values in `[0,1]`. Five-cut normalized AUC is
`(0.5*U0+U1+U2+U3+0.5*U4)/4`. For 16 root-paired differences, sample SD uses
denominator 15 and the one-sided 95% lower bound is
`mean - 1.7530503556925547*SD/4`. The positive conjunction is, separately for
DLT-minus-SLEEP_FROZEN and DLT-minus-on-policy-ATN: mean AUC difference at
least `.05`, that lower bound greater than zero, mean terminal difference
greater than zero, and earliest-cohort retention difference at least `-.05`.
If either contrast fails, stop the same-history spend.

Only on that positive conjunction, run the disposable fixed-DLT-history view:
another 3,200 tasks, 54,400 calls, 6,553,600 generated tokens, and 26,214,400
returned tokens. A superiority statement from this view additionally requires
DLT-minus-fixed-history-ATN mean AUC at least `.05`, its one-sided 95% lower
bound greater than zero, mean terminal difference greater than zero, and
earliest-cohort retention difference at least `-.05`. It uses no new
independent root. Per view, reservation is
`ceil(1.5*54400*t_max/360)/10` A40-hours and must not exceed 80.0; otherwise
defer the superiority claim. No favorable-cut selection is allowed.

### P6: practical local plateau, optional and gated

Only after positive P5, add two novelty-growing on-policy cuts:

```text
16*2*40 = 1,280 tasks; <=21,760 calls;
<=2,621,440 generated; <=10,485,760 returned tokens.
```

Then rerun only the terminal ATN endpoint at q16/B16384:

```text
16*40 = 640 tasks; <=10,880 calls;
<=1,310,720 generated; <=10,485,760 returned tokens.
```

An optional seven-cut same-history curve costs another 1,280 tasks/21,760
calls but is not needed for the on-policy text plateau. Reserve at most 32
A40-hours for two cuts and 16 for terminal doubled access, replaced by the
same P3 formula.

“Practical local plateau” requires scheduled new eligible evidence in both
intervals, old retention, oracle headroom >=.10, no invalid root, and four
simultaneous root-level equivalence intervals wholly inside `[-.05,+.05]`:
the per-root OLS slope through cut indices `(4,5,6)`, increment `U5-U4`,
increment `U6-U5`, and terminal `B16384-B8192`. Familywise confidence is 90%
by Bonferroni: each two-sided interval is
`mean +/- 2.4898797034798896*SD/4` (Student t, df=15, quantile .9875). A
doubled-access interval wholly below zero is degradation, not plateau; a
positive nonequivalent gain or non-fitting sensitivity is no plateau. No P6
result generalizes outside this finite PCFL regime.

## 11. Claim firewall

After P4 alone, the maximum statement is:

> The frozen ACTIVE_TEXT_NATIVE-v2.1-AUTO(q16,B8192) configuration was a
> source-faithful, restartable, maximum-load-usable textual-memory opponent on
> four excluded PCFL roots.

After positive on-policy P5 only:

> Conditional on the fixed child and under the registered finite PCFL lives,
> DLT exceeded this exact evolving text-memory system as a total on-policy
> system.

After the positive fixed-history view:

> The same-DLT-history conditional system/access contrast also favored DLT.

Only P6 permits a **practical local plateau of the named ATN configuration**.
Nothing here establishes superiority to external memory generally, a pure
text/parameter carrier effect, DREAM/compiler value, recurrence, parenting,
autonomous retrieval-policy learning, physical compression, internal neural
graphs, independently raised-child population effects, open-world discovery,
or general continual learning. Those require their separately registered
controls. A text win or tie is valid and must be reported.

## 12. Closure inventory and unresolved decisions

The nine P0 fields are resolved as follows:

1. canonical event/document/lifecycle/duplicate/supersession/rejection: §3--4;
2. automatic query fields/order/escaping/caps/sentinels/truncation: §5;
3. equality-only online salted identifiers: §2.2;
4. public-event-only directed topology and graph: §4.2;
5. exact BM25/PPR/fusion/MMR/packing/empty/overflow arithmetic: §6;
6. common RAW_PUBLIC lane: §7.1;
7. common LF-framed 16+1 transport/prompt partition: §7.2;
8. lexical-only RS8 MODEL lane with no extra generation: §4.2; and
9. independent world/writer roots conditional on one fixed child: §2.1.

The q16/B16384 access-only sensitivity and its fit/execute/report stop tree are
resolved in §§0, 6.3, 9, and 10.

**Genuinely unresolved human choices: none.** Future receipts must supply the
already-chosen child/model/tokenizer/task-renderer/scorer byte hashes, and a
fresh reviewer must decide whether this proposal is exact enough to promote.
Those are evidence gates, not design choices. This memo itself grants no
promotion or execution authority.

## Evidence reconciled (informative, not normative imports)

- `research_notes/analysis/2026-09-13_active_linked_text_readiness_fresh_audit.md`
- `research_notes/analysis/2026-09-13_active_text_native_v2_adversarial_audit.md`
- `research_notes/analysis/2026-09-13_active_text_native_v2_executable_design.md`
- `research_notes/analysis/2026-09-13_pcfl_strong_external_memory_fairness_audit.md`
- `research_notes/analysis/2026-09-12_text_memory_baseline_readiness_audit.md`
- `research_notes/analysis/2026-09-13_pcfl_reusable_affine_gate_stratum.md`
- `research_notes/analysis/2026-09-13_pcfl_c0_dev_interface_repair_v2_closure.md`
- `research_notes/2026-09-11_active_text_role_closure_amendment_v1.md`
- `research_notes/2026-09-11_active_text_compression_design_adjudication.md`
