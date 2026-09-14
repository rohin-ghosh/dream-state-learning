# ACTIVE_TEXT_NATIVE-v2.2-AUTO(q16,B8192): exact successor contract

**Date:** 2026-09-14 PT
**Status:** candidate proposal source only; not ratified, implemented, or run
**Authority:** none. This memo authorizes no source edit outside this memo,
materialization, tokenizer/model call, benchmark generation, fit, adapter,
parenting, GPU use, scientific claim, release, or submission.

## 0. Closed object

The sole proposed claim-bearing evolving textual-memory opponent is:

```text
ACTIVE_TEXT_NATIVE-v2.2-AUTO(q16,B8192)
```

It is one frozen PCFL child, an append-only branch-local public ledger, exact
automatic lexical retrieval, and exact traversal over a graph made only from
public transitions that the same branch witnessed. It has no learned query,
model reflector, hidden graph, answer/candidate access, supplied exact-address
service, parameter update, or write-back from evaluation.

The access-only sensitivity is exactly:

```text
ACTIVE_TEXT_NATIVE-v2.2-AUTO(q16,B16384)
```

It changes only the per-return/cumulative returned-memory limits from
`512/8192` to `1024/16384` tokens before the same first 16 actor calls. It adds
no actor call, THINK, action, query generation, retry, or generated token.
`q32` is forbidden. Because memory changes later generated histories, this is
a same-turn total-access sensitivity, not a token-level effect at a fixed
history and not proof of saturation.

This successor changes no v2.1 retrieval algorithm. It closes only the fresh
audit's R1--R8 integration and exactness defects. `ACTIVE_LINKED_TEXT_SUPPLIED`
remains a supplied-service ceiling; `TEXT_SAME_SEMANTICS` remains a finite
identical-record carrier diagnostic; `RAW_PUBLIC` is the shared raw-memory
machinery; and `FULL_PUBLIC_HISTORY`/`EXACT_WITNESSED_GRAPH` are certificate
ceilings, not longitudinal opponents.

## 1. Normative bytes, numbers, and hash envelope

Persisted text is strict UTF-8. CR, BOM, invalid UTF-8, Unicode repair, NaN,
infinity, and duplicate JSON keys are forbidden. Newline is one LF byte.
JSON is RFC 8785/JCS. `JCS(x)` is its UTF-8 bytes without LF; JSONL is
`JCS(x)||LF`. SHA-256 is FIPS 180-4, rendered lowercase hexadecimal. Integers
are canonical base 10: no sign or leading zero except `0`. Array order is
meaningful.

Normative schema/tag literals are:

```text
ATN_ROOT_V2 ATN_EVENT_V2 ATN_INTERPRETATION_V2 ATN_DOCUMENT_V2
ATN_TASK_V2 ATN_THINK_V2 ATN_QUERY_V2 ATN_MEMORY_V2 ATN_INDEX_V2
ATN_REGISTRY_V2 ATN_PCFL_L_WIRE_V1
```

For every registry payload `P`, its non-circular identity is:

```text
registry_id = "REG/" + SHA256(b"ATN_REGISTRY_V2\x00" || JCS(P))
registry_record = JCS({"payload":P,"registry_id":registry_id}) || LF
```

There are no optional keys in a printed schema. A field whose value is not
yet available is not represented by a placeholder: the stage remains closed
until the complete record exists and its exact file SHA-256 is bound in the
stage-open receipt.

All arithmetic described as binary64 uses IEEE-754 round-to-nearest,
ties-to-even. Every written `+`, `-`, `*`, or `/` is one binary64 operation,
rounded before the next operation; FMA, contraction, extended registers, fast
math, and reassociation are forbidden. Integer counts are exact unbounded
integers until the explicitly stated integer-to-binary64 conversion.
Diagnostic floats use `float.hex()` lowercase output.

## 2. Roots, branches, and all identities

### 2.1 Statistical root and allocation

One independent lifetime root, conditional on one fixed parent-deleted child,
is one preallocated tuple:

```text
(world_seed_256, writer_seed_256, schedule_seed_256, decode_seed_256,
 root_salt_seed_256)
```

All are 32-byte values sampled before world content. Define:

```text
root_salt = SHA256(root_salt_seed_256 || b"ATN_ROOT_SALT_V2")
```

The world generator cannot receive either salt value. The root forks from the
byte-identical child into `DLT_PERIODIC`, `SLEEP_FROZEN`, and `ATN`. Failures
stay in intention-to-treat; no redraw/re-salt/replacement is allowed. Tasks,
cuts, twins, decodes, mutations, and checkpoints do not increase `n`.

The four certificate roots also are the only reusable-structure/RS8
qualification roots. The mutually disjoint root classes are exactly:

```text
DEV | PROFILE | WRITER_SCALE | CERTIFICATE_PLUS_RS8 | LIFETIME
```

An authentic TSJ prerequisite uses its own already-bound roots and contributes
no observation to any class above.

### 2.2 Equality-only public IDs

At the first public appearance of exact case-sensitive identifier bytes `p`:

```text
OID(p) = b"OID/" || hex(SHA256(root_salt || p)[0:16])
```

There is no normalization or type/role/order/answer/branch bit. The map is
online: future IDs do not exist. Different public IDs colliding in 128 bits
terminate the root `IDENTIFIER_COLLISION`; it remains an ITT failure.

Structured fields are replaced by OIDs directly. In prose, registered IDs are
replaced longest-byte-string first, then lexicographically, only with ASCII
`[A-Za-z0-9_]` boundaries. Overlapping nonidentical matches terminate the root.
OIDs exist only inside ranking/graph arithmetic; actor rendering restores
exact public bytes.

### 2.3 Root-bound event, interpretation, document, and THINK IDs

Event and interpretation bodies are defined in §3. Their IDs are:

```text
event_id = "EV/" + SHA256(b"ATN_EVENT_V2\x00" || root_salt || JCS(event_body))
interpretation_id = "IN/" +
 SHA256(b"ATN_INTERPRETATION_V2\x00" || root_salt || JCS(interpretation_body))
document_id = "DOC/" + SHA256(b"ATN_DOCUMENT_V2\x00" ||
 kind_utf8 || b"\x00" || source_record_id_utf8)
```

DOC inherits the root binding from its EV/IN source. Branch label is excluded:
byte-identical paired evidence within one root retains one identity. The tuple
`(episode_instance,occurrence_index,decision_index)` is globally unique within
one branch. Reuse for a second dispatch is fatal.

THINK is task-local and never enters lifelong storage. Define the exact task
identity before its answer custody opens:

```text
task_body = {"episode_instance":I,"module_public":S,"objective_public":S,
             "occurrence_index":I,"public_task_sha256":HEX64}
task_id = "TASK/" + SHA256(b"ATN_TASK_V2\x00" || root_salt || JCS(task_body))
```

`I` and `S` denote the actual integer and string, not literal metavariables.
Let `call_index` be `1..16`:

```text
think_id = "TH/" + SHA256(b"ATN_THINK_V2\x00" || root_salt ||
 task_id_utf8 || b"\x00" || ASCII(call_index) || b"\x00" || response_bytes)
```

The task-local receipt is exactly
`JCS({"call_index":i,"response_sha256":SHA256(response_bytes),
"task_id":task_id,"think_id":think_id})||LF`. Kept and dropped query THINKs
are listed by these IDs.

## 3. Total append-only ledger

### 3.1 Public transition parser: the only graph ingress

The later-lifetime common wire is `PCFL-L-WIRE-v1`; §7 binds all arms to it.
Only either of these anchored action families paired with the anchored outcome
can create a non-null transition:

```regex
\AEXPLORE (PCLN_[A-Z2-7]{12}) (PCLP_[A-Z2-7]{12})\z
\APROBE (PCLQ_[A-Z2-7]{12})\z
```

and exact outcome bytes, with no final LF:

```regex
\APUBLIC_OUTCOME\nSOURCE (PCLN_[A-Z2-7]{12})\nPORT (PCLP_[A-Z2-7]{12})\nDEST (PCLN_[A-Z2-7]{12})\nRECEIPT (PCLR_[A-Z2-7]{12})\z
```

Regex captures are `(action_source,action_port)`, `(probe)`, and
`(source,port,destination,receipt)`. A transition is returned iff:

1. exactly one action-family fullmatch and the outcome fullmatch succeed;
2. for EXPLORE, action source/port equal outcome source/port byte-for-byte;
   for PROBE, its probe ID was root-local and public before dispatch;
3. source and port were root-local public IDs before dispatch (a PROBE may
   publicly reveal which already-known port it exercised, but not create it);
4. destination and receipt are either already root-local or make their first
   public appearance in this exact outcome;
5. the receipt has no prior dispatch mapping; and
6. every captured ID belongs to this root's public namespace registry.

Otherwise return `transition=null`. There is no substring scan, multi-match
choice, field reorder, joining across messages, normalization, repair, or
world-object fallback. A grammar ambiguity (one byte string accepted by more
than one registered action/outcome family) terminates `WIRE_AMBIGUITY`. Other
final action families and negative/error outcomes always return null. The
graph builder receives only this parser result, exact action/outcome hashes,
and event ID; it cannot import the world transition object.

Before P1 source promotion, an independently authored golden registry must
bind exact input bytes, expected captures/null/terminal code, and output hash
for: valid PCFL-L EXPLORE; valid PCFL-L PROBE; valid current TSJ
`STEP TS3P_...` plus its exact four-line
`PUBLIC_OUTCOME`; swapped SOURCE/PORT lines; decoy IDs before/after fields;
duplicate/repeated fields; partial/truncated bytes; extra/final LF; unknown
receipt; future destination; mixed-root IDs; action/outcome mismatch;
cross-message halves; two matching receipts; negative outcome; and all other
legal final families. TSJ is evaluated through the compatibility adapter in
§7.3, never directly by the lifetime runtime.

### 3.2 Event record and visibility

Every dispatched ordinary action creates one body with exactly these keys:

```json
{"action_public":"UTF8","decision_index":0,"episode_instance":0,
 "module_public":"UTF8_OR_EMPTY","objective_public":"UTF8_OR_EMPTY",
 "occurrence_index":0,"outcome_public":"UTF8",
 "public_status":"UTF8_OR_EMPTY","schema":"ATN_EVENT_V2",
 "state_before_public":"UTF8_OR_EMPTY","transition":null}
```

`transition` is replaced only by the parser's exact object:
`{"destination":"ID","port":"ID","receipt":"ID","source":"ID"}`.
Invalid actions and negative outcomes remain events. Private answers, routes,
scores, labels, future fields, and evaluator data are absent. The record is
`JCS({"body":body,"event_id":event_id})||LF`.

The event is visible to the same task only at its next actor continuation. It
is invisible to siblings until every member of the presealed batch round has
dispatched once or terminated. At that barrier, queued events commit by
ascending `(module_public UTF-8 bytes,episode_instance,occurrence_index,
decision_index,event_id)`. Completion/device/cache order cannot affect it.

### 3.3 Interpretation grammar, sources, rejection, and visibility

Only an ordinary child turn at a predeclared common formation opportunity may
attempt an interpretation. No ATN-only generation or reflector exists. The
PCFL-L anchored physical grammars, with no CR/LF, are:

```regex
\AEVENT (PCLE_[A-Z2-7]{12}) SOURCE (PCLN_[A-Z2-7]{12}) PORT (PCLP_[A-Z2-7]{12}) DEST (PCLN_[A-Z2-7]{12}) PROVENANCE (PCLR_[A-Z2-7]{12})\z
\ALINK (PCLL_[A-Z2-7]{12}) FIRST (PCLE_[A-Z2-7]{12}) SECOND (PCLE_[A-Z2-7]{12}) VIA (PCLN_[A-Z2-7]{12}) PROVENANCE (PCLR_[A-Z2-7]{12}),(PCLR_[A-Z2-7]{12})\z
\AMODEL (PCLS_[A-Z2-7]{12}) AFFINE4X2 A ([01]{8}) B ([01]{2}) EVIDENCE (PCLR_[A-Z2-7]{12})(,(PCLR_[A-Z2-7]{12})){7}\z
```

For MODEL, expand the final repeated capture into exactly eight receipt IDs;
they must occur in ascending public ordinal. After a full grammar parse,
resolve receipt occurrences literally left-to-right through the already-public
one-to-one receipt-to-event map. Record every successfully resolved event ID,
in occurrence order, including duplicates. If no grammar fullmatches or no
receipt resolves, record `[]`. Acceptance requires respectively exactly
`1/2/8` resolved, pairwise-distinct, root-local event IDs.

EVENT fields must byte-equal the cited public transition. Its new PCLE handle
must be root-local and unused. LINK FIRST/SECOND must name accepted EVENT
handles; the two cited receipts must correspond to them in that order and
`destination(FIRST)==VIA==source(SECOND)`. Its PCLL handle must be unused.
MODEL checks its proposed bits only against the eight cited public outcomes;
no target descriptor, target label, hidden family, candidate, route, or solver
is available. Any failure reports only `MODEL_INCONSISTENT`.

RS8 exposes this same MODEL formation opportunity to DLT, SLEEP_FROZEN, and
ATN. In its finite candidate diagnostic, automatic query 1 is constructed
once before four candidate continuations are appended; scoring those four
continuations creates zero additional queries or actor calls. The integrated
route panel remains candidate-free.

Every attempt receives exactly one status and one reason from the first
applicable row of this precedence table:

| priority | predicate | status | public reason |
|---:|---|---|---|
| 1 | no unique full grammar parse | `REJECTED` | `FORMAT` |
| 2 | any cited receipt fails public resolution | `REJECTED` | `UNRESOLVED_PUBLIC_REFERENCE` |
| 3 | wrong count, repeated source, or MODEL receipt order | `REJECTED` | `SOURCE_SET` |
| 4 | proposed handle already exists | `REJECTED` | `DUPLICATE_HANDLE` |
| 5 | EVENT/LINK public-field inconsistency | `REJECTED` | `PUBLIC_EVIDENCE_MISMATCH` |
| 6 | MODEL public-evidence inconsistency | `REJECTED` | `MODEL_INCONSISTENT` |
| 7 | all acceptance predicates pass | `ACCEPTED` | empty string |

No other status/reason literal is legal. The public feedback, when the common
formation interface exposes it, is exactly `STATUS <status> REASON <reason>`;
for accepted attempts the last byte is the space after `REASON`. Private
diagnostics stay in custody and never enter a document.

The body has exactly:

```json
{"attempt_bytes":"EXACT_CHILD_UTF8","creation_frontier":0,
 "episode_instance":0,"occurrence_index":0,"public_reason":"FINITE_LITERAL",
 "public_status":"ACCEPTED_OR_REJECTED","schema":"ATN_INTERPRETATION_V2",
 "source_event_ids":["RESOLVED_IDS_IN_LITERAL_ORDER"]}
```

The record is `JCS({"body":body,"interpretation_id":interpretation_id})||LF`.
All attempts, including rejection, occur exactly once. They become eligible
only at the common authenticated formation/SLEEP barrier, sorted by
`(creation_frontier,episode_instance,occurrence_index,interpretation_id)`.
They never appear mid-batch.

### 3.4 Lifecycle

Re-ingesting an EV/IN or reusing a dispatch coordinate fails closed. Similar
real events remain distinct. There is no mutation/supersession: every document
remains live; deletion or non-null supersession is `UNSUPPORTED_MUTATION`.
Query, retrieval, DREAM/compiler prose, replay, optimizer presentations,
canaries, probes, exams, certificates, reports, and evaluator output never
become documents. Evaluation descendants are read-only, and their ledger,
index, cache, query-state, and file roots must equal run-skipped controls.

## 4. Documents and witnessed graph

Each event creates one `RAW_PUBLIC` document. Each attempt creates exactly one
of `EVENT_INTERPRETATION`, `LINK_INTERPRETATION`, `MODEL_INTERPRETATION`, or
`REJECTED_INTERPRETATION`. Actor row:

```text
MEMORY <JCS({"citation":document_id,"kind":kind,"payload":public_payload,
             "sources":ordered_source_event_ids,"status":public_status})>\n
```

RAW payload is exactly `{"action":...,"module":...,"outcome":...,
"public_status":...,"transition":...}`. Interpretation payload is exactly
`{"attempt":attempt_bytes,"public_reason":public_reason}`. The ranking row
is the actor row after public-ID-to-OID replacement. A complete row including
LF must be at most 384 pinned-child tokens or the root is
`BASELINE_INVALID_ROW`; no truncation/drop occurs.

The document JSONL object has exactly:

```json
{"creation_frontier":0,"document_id":"DOC/HEX64","episode_instance":0,
 "kind":"KIND","occurrence_index":0,"payload":"SHAPE_ABOVE",
 "schema":"ATN_DOCUMENT_V2","source_event_ids":["EV/HEX64"],
 "source_record_id":"EV_OR_IN_ID","status":"PUBLIC_STATUS"}
```

For RAW, source events is `[event_id]`, source record is EV, and status is the
event's exact public status. For an interpretation, all three copy its IN
record. `creation_frontier` starts at zero and increments once per global
batch or authenticated formation barrier. Same-task pending evidence lives in
a task-local overlay destroyed at commit.

`AUTO_WITNESSED_GRAPH` is a directed simple graph. For every live RAW document
with parsed `source --port--> destination`, create vertices for the document
and three OIDs and exactly six unit arcs:

```text
OID(source) <-> DOC(event)
OID(port) <-> DOC(event)
OID(destination) <-> DOC(event)
```

Each `<->` is the two directed arcs. Duplicate arcs collapse. There are no
event-event, co-occurrence, inferred/transitive, child-LINK, MODEL, receipt,
goal, answer, candidate, family, hidden-world, cut, or evaluator edges.
Interpretations never create graph topology. MODEL is a lexical cited row
only; it is not a graph vertex or affine-solver feature.

## 5. Automatic target-blind query

Before calls 1--16, construct a query only from current exact public objective,
current exact public state, and earlier accepted task-local THINK bytes. The
retriever API has no answer, candidate/order, target label, route, necessary
bundle/cut, condition/arm, adapter, future state/inventory, hidden world,
evaluator, score, report, or certificate path. The renderer supplies a hashed
retrieval projection containing objective and state only before answer/candidate
custody opens.

The object is:

```json
{"objective":"UTF8_OR_EMPTY","schema":"ATN_QUERY_V2",
 "state":"UTF8_OR_EMPTY","think":["EXACT_THINK_BYTES"]}
```

Ranking bytes are JCS after OID replacement. The objective+state empty-THINK
query must be at most 1,024 pinned-tokenizer tokens. Total cap is 2,048 with
`add_special_tokens=false`. Starting newest-first, retain the largest suffix
of whole THINKs for which the complete JCS query stays within 2,048; restore
chronological order. Drop oldest whole records first, never partial bytes.
Receipt kept/dropped `think_id`s and exact token IDs. Over-cap base query makes
the task invalid. Query term frequency is binary. Query text is ephemeral.

## 6. Singular ranking, graph diffusion, and packing

### 6.1 Tokens and BM25

`lex(bytes)` strictly decodes UTF-8, applies Unicode NFKC, Unicode lowercase,
then returns maximal ASCII `[a-z0-9_/]+` runs in occurrence order. For every
document, `tokens(d)=lex(exact ranking-row bytes including its terminal LF)`.
Document TF is count; query TF is one. `dl=len(tokens(d))`.

Let `N` be live documents and `SUMDL` the exact integer sum of `dl` in
ascending document ID. If `N=0`, return MISS. If `N>0` and `SUMDL=0`, set
`avgdl=1.0`; otherwise
`avgdl=fl(binary64(SUMDL)/binary64(N))`.

For query terms in ascending UTF-8 token bytes, compute:

```text
idf = log(fl(1.0 + fl(fl(binary64(N-df)+0.5) /
                         fl(binary64(df)+0.5))))
norm = fl(1.0-0.75 + fl(0.75 * fl(binary64(dl)/avgdl)))
den = fl(binary64(tf) + fl(1.2 * norm))
num = fl(fl(binary64(tf) * 2.2) * idf)
term_score = fl(num / den)
```

`math.log` in the sealed runtime is used. A document score begins `+0.0` and
adds term scores in that token order. Documents score independently in
ascending document ID. Zero scores are not positive. The lexical denominator
starts `+0.0` and adds positive document scores in ascending document ID;
`L(d)=fl(score/denominator)`, or zero when denominator is zero.

### 6.2 PPR and fusion

Choose at most 16 positive-BM25 graph-document seeds by descending BM25 then
ascending document ID. Restart denominator sums their BM25 in ascending
document ID. Each restart weight is one binary64 division.

Vertices and each outgoing destination list sort by UTF-8 vertex ID. For each
row, `P(u,v)=fl(1.0/binary64(outdegree(u)))`. Initialize `p0=restart`. For each
of exactly 20 iterations:

1. compute `dangling` by adding `p[u]` for zero-outdegree `u` in ascending ID;
2. for each destination `v` ascending, compute `incoming` from sources `u`
   ascending as repeated `incoming=fl(incoming+fl(P(u,v)*p[u]))`;
3. compute `carry=fl(incoming+fl(dangling*restart[v]))`;
4. set `pnext[v]=fl(fl(0.20*restart[v])+fl(0.80*carry))`.

Missing restart values are exact `+0.0`. Swap complete vectors only after all
destinations. After iteration 20, sum graph-document masses by ascending
document ID and divide each once to get `G`, or zero if denominator zero.
When graph seeds exist `S=fl(fl(0.5*L)+fl(0.5*G))`; otherwise `S=L`.
RAW_PUBLIC uses only L and never PPR.

### 6.3 MMR and complete rows

For token sets A/B, compute exact integer intersection `i` and union `u`;
Jaccard is `+0.0` if `u=0`, otherwise
`fl(binary64(i)/binary64(u))`. MMR is evaluated exactly:

```text
MMR(d)=fl(fl(0.8*S(d))-fl(0.2*max_similarity))
```

One block is exactly:

```text
MEMORY_BEGIN ATN_MEMORY_V2
<complete MEMORY rows>
MEMORY_END
```

Every displayed line has LF. With no rows, insert `MISS\n`. Wrappers count.
If a positive-BM25 RAW row fits, select the highest BM25 first (ties: newest
frontier, then smallest ID). Thereafter greedily select unselected positive-S
documents by higher MMR, higher S, newer `(frontier,episode,occurrence)`, then
smaller ID. Similarity maximum scans selected IDs ascending. A non-fitting row
is skipped permanently for that retrieval; continue. Never split/truncate.
One document occurs at most once per block.

Primary per-return/cumulative caps are `512/8192`; sensitivity caps are
`1024/16384`. Token count is the pinned child tokenizer over exact complete
block bytes with `add_special_tokens=false`. A MISS/repeat/unused opportunity
is charged and never replaced.

### 6.4 Independent goldens

Before P1 source promotion, one independent golden registry must contain exact
fixture bytes, expected `float.hex()` at every intermediate operation, ordered
IDs, chosen/skipped rows, final block bytes/hash, and expected terminal code
for: empty; one document; term/document ties; all-empty documents; dangling
vertex; non-graph MODEL; graph-only-positive document; duplicate arcs;
row-exact-cap; row-overflow; overflow-then-later-fit; empty-set Jaccard;
MMR tie/skip; wrong-root; and immutable rebuild. The author/checker cannot
import implementation helpers. Its registry ID and file SHA are mandatory in
the P1 stage-open receipt. Failure of any byte/hex value stops P1.

## 7. One actual later-lifetime PCFL-L wire

### 7.1 Common runtime binding

`PCFL-L-WIRE-v1` is the only later-lifetime actor/formation wire. All three
on-policy arms use it; no runtime chooses Stage2A versus TSJ semantics. Its
identifier namespaces are exactly:

```text
PCLN_ node | PCLP_ port | PCLE_ event-handle | PCLL_ link-handle
PCLQ_ probe | PCLR_ receipt | PCLS_ series
```

Each suffix is 12 uppercase base32 `[A-Z2-7]` characters. Namespace and token
length receipts are presealed before root generation. Stage2A (`M2A...`) and
TSJ (`TS3...`) remain unchanged prerequisite mechanism tests and are never
silently used as the lifetime transport.

The exact system bytes, no terminal LF, are:

```text
You are the PCFL-L actor. Use only the public task, public state, your earlier accepted THINK lines, and cited MEMORY rows shown in this task. Identifiers are opaque and case-sensitive. Respond with exactly one physical line: THINK followed by nonempty reasoning, or one final line matching the task's printed grammar. Never combine thought and action. Never invent, translate, or repair an identifier. Memory is inserted automatically; no READ command exists. A malformed, multiple, late, or wrong-family line receives no retry.
```

The first user message is this length-framed concatenation:

```text
PCFL_L_TASK_V1
OBJECTIVE_UTF8_BYTES <N>
<objective>
STATE_UTF8_BYTES <N>
<state>
PUBLIC_TASK_UTF8_BYTES <N>
<public_task>
FINAL_GRAMMAR_UTF8_BYTES <N>
<one exact final regex>
```

For the direct certificate ceilings, the presealed mount appears once before
call 1 and all 16 automatic-memory positions contain canonical MISS. FULL is:

```text
FULL_PUBLIC_HISTORY_BEGIN
<all eligible MEMORY rows sorted frontier/episode/occurrence/document-ID>
FULL_PUBLIC_HISTORY_END
```

EXACT is:

```text
EXACT_WITNESSED_GRAPH_BEGIN
WITNESS <document_id> <source_id> --<port_id>--> <destination_id>
EXACT_WITNESSED_GRAPH_END
```

Every line has LF. EXACT has one row per non-null RAW transition sorted by
frontier then document ID. Both are deterministic public-record projections;
neither may consult an answer or hidden solver. They are never truncated; a
context non-fit fails that ceiling. NONE uses one presealed neutral block at
all 16 positions. For integer `n=0..65535`, form:
`MEMORY_BEGIN ATN_MEMORY_V2\nSHAM context-position control only.` followed by
`" neutral"` repeated `n`, then `\nMEMORY_END\n`; select the smallest `n`
whose pinned-tokenizer length is exactly 512. No solution stops P3. The bytes
contain no task/root/identifier/candidate/answer token.

`<N>` is UTF-8 byte length. Before calls 1--16 append exactly:

```text
AUTOMATIC_MEMORY_V2
<complete memory block>
Respond now with exactly one permitted physical line.
```

Generation stops on LF and excludes it. Decoded bytes are strict UTF-8 with no
CR/LF and no trim/extract/repair. THINK is exact prefix `THINK ` plus at least
one non-whitespace code point. The one printed final grammar is chosen from:

```regex
\AROUTE PCLN_[A-Z2-7]{12} PCLN_[A-Z2-7]{12} : PCLP_[A-Z2-7]{12}(,PCLP_[A-Z2-7]{12})*\z
\APROBE PCLQ_[A-Z2-7]{12}\z
\AEXPLORE PCLN_[A-Z2-7]{12} PCLP_[A-Z2-7]{12}\z
```

Formation tasks print exactly one grammar from §3.3 instead. Calls 1--16 may
THINK or finalize. After THINK on call 16, append:

```text
FINAL_OPPORTUNITY_V2
No more THINK responses are permitted. Return exactly one final line matching the task's printed grammar.
```

Call 17 must finalize. Total actor output is at most 2,048 pinned-tokenizer
tokens; each call requests `min(256,2048-used)`. Zero remainder, malformed,
truncated, context-overflow, wrong family, or nonfinal 17 is task failure.
There is no retry. All conditions share task bytes, prompt, stop, parser,
16+1 calls, cap, decode address, and scorer. Context is 32,768 tokens with 256
reserved for output; no input is truncated. Every prompt receipts input/output
token IDs, reserve, memory IDs, and prefix hash.

### 7.2 Common RAW_PUBLIC parity

Each on-policy branch uses byte-identical ledger schema, visibility clock,
query projection, BM25 implementation, complete-row packing, and q16/B8192
limits. Ledger contents are branch-local consequences of that branch's
committed actions and may diverge after the fork. Only an explicitly labeled
fixed-DLT-history disposable descendant receives DLT evidence.

DLT and SLEEP_FROZEN rank only their own RAW_PUBLIC documents. ATN ranks its
own RAW_PUBLIC plus eligible interpretations/graph within the same single
512/8192 envelope; it receives no second raw call/budget. DLT may use its
adapter, SLEEP_FROZEN mounts no post-fork write, and ATN parameters remain
frozen. This is a total-system comparison with a shared raw mechanism, not
identical post-fork information or a pure carrier comparison.

### 7.3 Exact TSJ compatibility boundary

The compatibility adapter exists only at injected P2. Its inputs are exact
decoded payload bytes after the TSJ transport has removed its one framing LF;
the adapter itself removes nothing. It accepts current TSJ:

```regex
\ASTEP (TS3P_[A-Z2-7]{12})\z
\APUBLIC_OUTCOME\nSOURCE (TS3N_[A-Z2-7]{12})\nPORT (TS3P_[A-Z2-7]{12})\nDEST (TS3N_[A-Z2-7]{12})\nRECEIPT (TS3R_[A-Z2-7]{12})\z
\AEVENT (TS3E_[A-Z2-7]{12}) SOURCE (TS3N_[A-Z2-7]{12}) PORT (TS3P_[A-Z2-7]{12}) DEST (TS3N_[A-Z2-7]{12}) PROVENANCE (TS3V_[A-Z2-7]{12})\z
\ALINK (TS3L_[A-Z2-7]{12}) FIRST (TS3E_[A-Z2-7]{12}) SECOND (TS3E_[A-Z2-7]{12}) VIA (TS3N_[A-Z2-7]{12}) PROVENANCE (TS3V_[A-Z2-7]{12})\z
```

TSJ STEP lacks an explicit source. The adapter may obtain source only from the
same exact outcome's SOURCE field; it verifies action port equals outcome PORT
and applies §3.1's remaining root/chronology rules. It then emits the same
ATN event body shape. For TSJ EVENT, the adapter selects the unique prior
public transition whose source/port/destination equal the three printed
fields; zero or multiple matches reject `PUBLIC_EVIDENCE_MISMATCH`. For TSJ
LINK, FIRST and SECOND resolve through already-accepted TSJ EVENT handles and
must satisfy FIRST.DEST=VIA=SECOND.SOURCE. Thus source IDs come only from
public event/accepted-row joins; the TS3V provenance surface never supplies a
hidden edge. No MODEL is synthesized. Namespace strings remain TS3 bytes and
receive OIDs in their own TSJ root. Any other TSJ action/row is rejected.

Injected goldens must prove accept/reject and byte-level body identity for the
TSJ examples in the source contract whose current exact file SHA-256 is
`57cdeb290573acb4edf68a1a4c1cbf12ae64eee6f0dc31730cc264cc79ae848a`.
This binds a boundary test, not current execution or scientific success. The
current fresh-readiness audit file SHA-256 is
`81fe33eeb333dcdb9e0dc3acaff6955804e7b06bc5faa0261785c47ff19f0ee8`.
Neither Stage2A nor TSJ source is modified.

## 8. Candidate blindness, fixed history, and public BRIDGE_EVENT proof

The retriever process receives only frozen config, root-local public mapping,
eligible branch ledger, objective/state, accepted local THINK, and tokenizer,
under an allowlist with no other file/network access. At fixed public bytes,
mutating candidate/answer/hidden graph/cut/future/carrier/evaluator/report data
must leave query, ranking, blocks, and hashes identical.

At a same-DLT-history cut, disposable ATN receives exactly once each eligible
DLT public event and child interpretation, and no DLT DREAM prose, optimizer
state/replay, adapter state, latent proposition, hidden answer/edge, or
evaluator output. This is a **same-history conditional system/access
contrast**, not pure carrier or DREAM evidence.

Before P4, a custody-only cut registry must identify four case families per
root: ATOM, BRIDGE_EVENT, OLD, NEW. For BRIDGE_EVENT the independent checker:

1. parses only already-public event bytes using §3.1;
2. builds the public directed transition multigraph sorted by event ID;
3. enumerates every simple source-to-goal path of at most `V-1` transition
   edges, expanding destinations and events in ascending UTF-8 ID;
4. proves the named event occurs in every successful public witness path;
5. proves no other real dispatch at that frontier has the same exact
   `(source,port,destination)` tuple;
6. deletes the RAW document, every interpretation citing its event ID, and
   its six incidence arcs, then proves zero successful public witness paths;
7. proves task bytes and every non-descendant public record are byte-identical.

The checker sees no hidden actor-time solver. A separate sealed generator
oracle may verify custody truth before execution, but only the public-path
certificate above can set `bridge_event_public_necessary=true`. Failure stops
the root before actor execution; the event is never favorably reselected.

## 9. Exact registries and source-faithful material schedule

### 9.1 Required registries

These six complete registry records must exist before their named stage opens:

1. `ROOT_REGISTRY`: class, root ID, five seed hashes, salt commitment, fixed
   child hash, and branch labels.
2. `WIRE_GOLDEN_REGISTRY`: every §3.1/§7.3 case with exact bytes, expected
   parse/body/status, and independent checker hash.
3. `RANKING_GOLDEN_REGISTRY`: every §6.4 case and every expected float/byte.
4. `CERTIFICATE_LOAD_CUT_REGISTRY`: four root IDs; 16 task IDs/root; stratum,
   endpoint, twin, necessary bundle IDs; ATOM/BRIDGE_EVENT/OLD/NEW cut event;
   571-block chronological store manifest; exact kind/token marginals;
   truthful/irrelevant/wrong-root donor manifests; public-path proof hash.
5. `LIFETIME_REGISTRY`: 16 root IDs; branch forks; module/cohort IDs; exact
   opportunity schedule; cuts; 40 task IDs/cut; utility component; earliest
   cohort; potential-outcome-tape hash; formation and store manifests.
6. `TSJ_PREREQUISITE_RECEIPT`: source-contract SHA above, source/runtime/root
   hashes, terminal verdict, all native/formation/chronology result hashes,
   independent-checker hash, and exact receipt-file SHA.

Payload keys are exactly:

```json
{"contract_sha256":"HEX64","created_utc":"RFC3339Z",
 "entries":["SCHEMA-SPECIFIC JCS OBJECTS"],"generator_sha256":"HEX64",
 "independent_checker_sha256":"HEX64","kind":"ONE_LITERAL",
 "schema":"ATN_REGISTRY_V2","scorer_sha256":"HEX64"}
```

`entries` is a JCS array of one of these exact record shapes; `S` means UTF-8
string, `I` a nonnegative integer, `B` Boolean, and `[S]` an ordered string
array. No extra or omitted key is legal:

```text
ROOT:
 {root_id:S,root_class:S,world_seed_commitment:S,writer_seed_commitment:S,
  schedule_seed_commitment:S,decode_seed_commitment:S,
  root_salt_commitment:S,child_sha256:S,branch_labels:[S]}

WIRE_GOLDEN:
 {case_id:S,profile:S,action_hex:S,outcome_hex:S,formation_hex:S,
  expected_disposition:S,expected_transition_jcs_hex:S,
  expected_source_event_ids:[S],expected_body_sha256:S}

RANKING_GOLDEN:
 {case_id:S,fixture_sha256:S,expected_float_hex:[S],
  expected_ranked_document_ids:[S],expected_selected_document_ids:[S],
  expected_block_hex:S,expected_block_sha256:S,expected_disposition:S}

CERTIFICATE_ROOT:
 {root_id:S,task_manifest_sha256:S,store_manifest_sha256:S,
  marginal_manifest_sha256:S,mutation_manifest_sha256:S,
  bridge_proof_manifest_sha256:S,truthful_twin_manifest_sha256:S,
  irrelevant_store_manifest_sha256:S,wrong_root_donor_root_id:S}

LIFETIME_ROOT:
 {root_id:S,fork_manifest_sha256:S,module_manifest_sha256:S,
  opportunity_manifest_sha256:S,cut_manifest_sha256:S,
  exam_manifest_sha256:S,potential_outcome_tape_sha256:S,
  formation_manifest_sha256:S,store_manifest_sha256:S}

TSJ_PREREQUISITE:
 {source_contract_sha256:S,source_tree_sha256:S,runtime_sha256:S,
  root_manifest_sha256:S,terminal_verdict:S,native_results_sha256:S,
  formation_results_sha256:S,chronology_results_sha256:S,
  independent_checker_sha256:S,receipt_file_sha256:S}
```

Every referenced manifest is one JCS array with exactly one of these row
shapes (again no optional keys):

```text
TASK:
 {task_id:S,root_id:S,stratum:S,endpoint:S,twin:I,cut_index:I,
  utility_component:S,objective_sha256:S,state_sha256:S,
  public_task_sha256:S,answer_custody_sha256:S,
  necessary_document_ids:[S]}

STORE:
 {root_id:S,branch:S,cut_index:I,semantic_block_index:I,
  creation_frontier:I,document_ids:[S],document_bytes_sha256:S,
  kind_counts_sha256:S,token_count:I,source_attempt_ids:[S]}

MARGINAL:
 {root_id:S,cut_index:I,total_blocks:I,total_documents:I,
  total_tokens:I,kind_counts_sha256:S,length_histogram_sha256:S}

MUTATION:
 {root_id:S,task_id:S,family:S,removed_event_id:S,
  removed_document_ids:[S],removed_arc_sha256:S,
  unchanged_public_bytes_sha256:S,mutated_store_sha256:S}

BRIDGE_PROOF:
 {root_id:S,task_id:S,bridge_event_id:S,frontier:I,
  public_graph_sha256:S,all_path_ids_sha256:S,path_count:I,
  paths_containing_bridge:I,duplicate_transition_count:I,
  cut_graph_sha256:S,cut_path_count:I,
  non_descendant_bytes_unchanged:B,public_necessary:B,
  checker_sha256:S}

OPPORTUNITY:
 {root_id:S,branch:S,cohort:I,module_id:S,opportunity_index:I,
  opportunity_kind:S,stage:S,task_id:S,scheduled_frontier:I,
  potential_outcome_sha256:S}

CUT:
 {root_id:S,cut_index:I,cumulative_modules:I,
  cumulative_acquisition_opportunities:I,
  cumulative_formation_opportunities:I,cumulative_semantic_blocks:I,
  earliest_cohort_module_ids:[S],exam_task_ids:[S]}

FORMATION:
 {root_id:S,branch:S,task_id:S,attempt_id:S,status:S,reason:S,
  source_event_ids:[S],attempt_sha256:S,admitted_block_ids:[S]}
```

`kind_counts_sha256`, histogram, path-list, and arc-list files are JCS arrays
of respectively `{"count":I,"kind":S}`, `{"count":I,"tokens":I}`,
`{"event_ids":[S],"path_id":S}`, and `{"destination":S,"source":S}`.
Thus no referenced manifest can add a hidden semantic field. The answer
custody hash is unavailable to runtime and exists only to prove precommit.

`generator_sha256` is the exact source-tree hash that creates public material;
`scorer_sha256` is the exact source-tree hash that evaluates it. Registry ID
plus file SHA enter the stage-open receipt. A missing referenced file, hash
mismatch, schema mismatch, or noncanonical JCS closes the stage.
Runtime query/index/actor processes receive none of registries 4--6 except the
public task projection and eligible public rows explicitly listed by the
visibility clock.

### 9.2 Lifetime schedule and exact acquisition/formation counts

The reconciled source-plan bytes are SHA-256
`caf05324dfd7ecf0a386105e6a6f6a5464641f48f7880044efcf9e4e4b09254c`.
This section is normative where it makes the later wire/costs more exact; the
instantiated LIFETIME_REGISTRY and all referenced manifest file hashes must be
bound before P5, so prose labels alone can never select a schedule.

The actual later-lifetime PCFL-L schedule is fixed to 33 modules: one entry
module plus four cohorts of eight. Every module has eight OLD public
acquisitions and twelve OLD interpretation opportunities. The entry module
and one preselected module in each later cohort additionally have one NEW
acquisition and three NEW formation opportunities. Missing/malformed attempts
consume their opportunity and remain in the denominator.

Exactly one reusable-structure module per root, the first in cohort 1's
schedule-seed permutation, is also the RS8 source module. Its eight OLD
acquisitions are the eight calibration outcomes. Its eight EVENT formations
cite them. Its lexicographically last irrelevant-island LINK formation slot
is typed as the one MODEL formation instead; the other three LINK slots and
every necessary route LINK are unchanged. Therefore it still has twelve OLD
formation tasks and the global 411 count does not change. The MODEL task may
use THINK calls inside the same 16+1 envelope and must finalize once; there is
no extra reflector, retry, or uncharged generation. Opaque modules have no
MODEL. The type substitution and source receipt IDs are presealed in the
opportunity/type-marginal registries before outcomes.

Thus per branch through cut 4:

```text
OLD acquisition tasks      = 33*8       = 264
NEW acquisition tasks      = 5*1        =   5
all acquisition tasks                    = 269
OLD formation tasks        = 33*12      = 396
NEW formation tasks        = 5*3        =  15
all formation tasks                      = 411
all acquisition+formation tasks          = 680
maximum calls              = 680*17     = 11,560
maximum generated tokens   = 680*2,048  = 1,392,640
maximum returned memory    = 680*8,192  = 5,570,560
maximum input tokens       = 11,560*32,512 = 375,838,720
```

These tasks produce the already-fixed cumulative semantic-block write counts:

```text
S1,S2,cut1,cut2,cut3,cut4 = 17,19,157,295,433,571.
```

The cumulative scheduled semantic assignments at the five scored cuts are
exactly `15,114,213,312,411`; S1 before the entry NEW continuation has 12.
The entry module is the earliest cohort. In each later cohort, the designated
NEW/expansion module is the first module in the schedule-seed permutation,
sealed before any outcome. Each cut exam has 40 actor tasks: 8 earliest, 8
newest, 8 recombination, and 8 expansion pairs of two sequential tasks
(probe then delayed action), hence 16 expansion tasks. The lifetime registry
binds their IDs and ordering.

Semantic blocks are compiler/training units derived from admitted child rows;
they are not extra observations or model calls. Replay, paraphrase, wrapper,
packing, and optimizer presentations add zero acquisition/formation calls.
The lifetime registry binds every opportunity-to-event/attempt/block join and
all absent/rejected rows.

Certificate stores use the same one-root 680-task maximum and schedule. The
pinned ordinary child emits every proposed “ideal child text” row from a
target-free public formation prompt under §7's 16+1 envelope. Only exact
source-valid accepted rows enter; no renderer, repair, resampling, or hidden
answer fills a missing row, and formation failure remains a root failure.
“Ideal” therefore names the registered expected row shape, not supplied
content. Four roots cost at most
2,720 tasks, 46,240 calls, 5,570,560 generated tokens, 22,282,240 returned
memory tokens, and 1,503,354,880 input tokens before scored P4 evaluation.

## 10. Certificate and statistics

Each of four combined certificate/RS8 roots has:

```text
2 strata * 4 endpoints * 2 twins = 16 tasks; 64/condition.
```

The four endpoints map prospectively to ATOM, BRIDGE_EVENT, OLD, and NEW.
Stores are padded prospectively to exactly 571 blocks with registry-bound
kind/token marginals. No reusable task has an identical answer row.

If P3 fits both bandwidths, P4 conditions are FULL, EXACT, primary ATN,
RAW_PUBLIC, NONE_SHAM, truthful twin, necessary cut, irrelevant same-root,
wrong-root, and B16384 sensitivity. If sensitivity does not fit, it is omitted
mechanically and marked unmeasured. FULL/EXACT are deterministic public-only
projections, not solvers. A cut deletes one named event, all citing
interpretations, and its arcs before indexing. Wrong-root retains donor salt.

Certificate gates are: FULL/EXACT/ATN each `>=60/64`, no root `<14/16`;
legal finals `>=61/64`; exact citations and zero false citations; necessary
bundle `>=60/64`, no root `<14/16`; at most three pooled and one/root ATN loss
among FULL-solvable; truthful redirection `>=12/16/root`; each cut family
causes at least `3/4/root` success-to-failure; irrelevant and wrong-root each
within `3/64` of NONE success/legal counts and zero donor citations; FULL and
EXACT headroom over NONE each `>=7/64`; reusable ATN `>=30/32`.

P4 failure of FULL/EXACT is `TASK_OR_ACTOR_INVALID`; ATN failure is
`BASELINE_INVALID`, never a DLT win. For sensitivity, per-root
`d_r=U_B16384-U_B8192`; mean `>0.05` is `NO_ACCESS_PLATEAU`. Any four-root
flatness is descriptive only.

At P5, compute `u_old`, `u_new`, and `u_cross` by summing their eight task
utilities in ascending task ID from `+0.0` and dividing by `8.0`. Compute
`u_expand` as `fl(fl(mean_8_probe+mean_8_delayed)/2.0)`, with each inner mean
formed the same way. Then
`U=fl(fl(fl(fl(u_old+u_new)+u_cross)+u_expand)/4.0)`.
This preserves equal component weight despite expansion using 16 tasks.
Five-cut AUC is
`fl(fl(fl(fl(fl(0.5*U0)+U1)+U2)+U3)+fl(0.5*U4))/4.0`, with written left-to-
right rounding and a final binary64 division. Root-paired differences sort by
root ID. Their mean sums from `+0.0` then divides by `16.0`; variance sums
`fl((d-mean)*(d-mean))` in that order, divides by `15.0`, then uses the sealed
runtime `sqrt`. The one-sided 95% lower bound is evaluated left-to-right as
`mean-fl(1.7530503556925547*fl(SD/4.0))`.
Positive DLT-vs-SF and DLT-vs-ATN each require mean AUC `>=.05`, lower bound
`>0`, terminal mean `>0`, earliest-cohort retention `>=-.05`. Only then run
fixed-DLT-history ATN, with the same gate for a superiority statement.

## 11. Stages, total costs, and stopping rules

### P0--P2: proposal, CPU source, injected integration

P0 is this memo: zero source/model/tokenizer/GPU/scientific execution. A fresh
reviewer must pass all 11 items in §13.

P1 implements store/index only: zero model/tokenizer/GPU; at most 8 CPU-hours,
16 GiB RAM, 5 GiB fixtures. It cannot open until ROOT, WIRE, and RANKING golden
registries are bound. Any byte/order/restart/cache/run-skip mismatch stops.

P2 implements PCFL-L plus TSJ injected compatibility: zero model/tokenizer/GPU;
at most 4 CPU-hours, 16 GiB RAM, 5 GiB fixtures. Cap/malformed/mixed/context/
terminal/run-skip tests must pass. No carrier-specific retry or opportunity.

### P3: excluded device profile

Prefixes at actor positions 1/8/16 are fixed injected technical transcripts,
not generated calls and never stored. Loads 0/157/571, positions 1/8/16,
cold/warm, three repeats cost `3*3*2*3=54` calls per bandwidth. B8192 first;
then B16384 if it fits. Both: 108 calls and 27,648 generated tokens, zero fits.
Profile limit is four A40-hours. If B16384 fits, later `calls_max=10,880`; if
not, `calls_max=9,792`. With maximum occupied seconds/call `t_max`, P4 reserve
is `ceil(1.5*calls_max*t_max/360)/10` A40-hours and may not exceed 24.0.

### P4: certificate, including material acquisition

The shared material prerequisite is §9.2 and must finish before scoring.

With B16384, material plus evaluation totals are:

```text
tasks 2,720+640=3,360; calls <=46,240+10,880=57,120
generated <=5,570,560+1,310,720=6,881,280
returned <=22,282,240+4,194,304=26,476,544
input <=57,120*32,512=1,857,085,440 tokens.
```

Without it: `3,296 tasks`, `<=56,032 calls`, `<=6,750,208 generated`,
`<=25,427,968 returned`, and `<=1,821,712,384 input` tokens. The material
prerequisite receives a separate profile-derived reservation
`ceil(1.5*46240*t_material/360)/10`, capped at 80 A40-hours; exceeding it stops
P4. Scored evaluation retains the 24-hour cap above. Partial roots fail ITT.

### P5: five-cut lifetime, including acquisition/formation

Sixteen roots times three branches times 680 scheduled material tasks gives:

```text
material tasks=32,640; calls<=554,880; generated<=66,846,720
returned<=267,386,880; input<=18,040,258,560.
```

All three on-policy five-cut evaluations cost `3*3,200=9,600 tasks`,
`<=163,200 calls`, `<=19,660,800 generated`, `<=78,643,200 returned`.
Primary total: `42,240 tasks`, `<=718,080 calls`, `<=86,507,520 generated`,
`<=346,030,080 returned`, `<=23,346,216,960 input` tokens, plus the separately
bound DLT optimizer schedule. Fixed-history ATN, only after the positive gate,
adds 3,200 tasks/54,400 calls/6,553,600 generated/26,214,400 returned and
1,768,652,800 input. Total then is 772,480 calls, 93,061,120 generated,
372,244,480 returned, and 25,114,869,760 input tokens.

Before launch, profile acquisition, formation, and evaluation separately and
bind `t_material`/`t_max`. Material and primary evaluation reservations use
the same 1.5x formula, each capped at 80 A40-hours. Exceeding a cap defers P5;
it never shrinks q/B, roots, cuts, tasks, or formation.

### P6: optional plateau

Only after positive P5, extend only the ATN on-policy branches by two cohorts
of eight modules. Each cohort adds 65 acquisition and 99 formation tasks, and
the cumulative semantic blocks become 709 then 847. Across 16 roots:

```text
material tasks = 16*2*164 = 5,248
material calls <=89,216; generated<=10,747,904
returned<=42,991,616; input<=2,900,590,592.
```

Two added-cut evaluations cost 1,280 tasks, <=21,760 calls, <=2,621,440
generated, <=10,485,760 returned, and <=707,461,120 input. Terminal B16384
adds 640 tasks/10,880 calls/1,310,720 generated/10,485,760 returned/353,730,560
input. P6 total is therefore 7,168 tasks, <=121,856 calls, <=14,680,064
generated, <=63,963,136 returned, and <=3,961,782,272 input tokens. Its
material/evaluation/doubled-access reservations are separately profile-derived
and capped at 32/32/16 A40-hours; a cap failure stops rather than shrinks it.
An optional seven-cut same-history curve is outside this contract.

Practical local plateau requires scheduled new evidence, old retention,
oracle headroom >=.10, no invalid root, and four Bonferroni-family 90%
equivalence intervals inside `[-.05,+.05]`: OLS slope over cuts 4/5/6,
`U5-U4`, `U6-U5`, and terminal B16384-B8192. Each interval is
`mean +/- 2.4898797034798896*SD/4`. Negative doubled-access degradation is not
plateau. No result extends beyond this finite PCFL regime.

For equally spaced cut indices 4/5/6, each root's OLS slope is exactly
`fl(fl(U6-U4)/2.0)`; the two increments and bandwidth difference are one
binary64 subtraction each. Each family's mean/SD uses the root-ID order and
algorithm in §10. Interval lower then upper endpoints are evaluated as one
multiply followed by one subtract or add; all four families must pass.

Stage order is immutable: deterministic P1, injected P2, authentic TSJ
receipt, P3, combined certificate/RS8 P4, P5 on-policy, conditional fixed-
history, optional P6. A failed prerequisite stops descendants; skipped cells
cannot be promoted; no favorable root/cut selection occurs.

## 12. Claim firewall

After P4 alone, at most:

> The frozen ACTIVE_TEXT_NATIVE-v2.2-AUTO(q16,B8192) configuration was a
> source-faithful, restartable, maximum-load-usable textual-memory opponent on
> four excluded PCFL roots.

After positive on-policy P5 only:

> Conditional on the fixed child and registered finite PCFL lives, DLT
> exceeded this exact evolving text-memory system as a total on-policy system.

After the gated fixed-history view only:

> The same-DLT-history conditional system/access contrast also favored DLT.

P6 alone can license “practical local plateau of this named configuration.”
Nothing licenses a pure carrier result, physical compression, general
external-memory superiority, DREAM/compiler value, recurrence, parenting,
learned retrieval policy, open-world discovery, universal saturation, or
general continual learning. A text win/tie is valid and must be reported.

## 13. Eleven-item self-audit

The nine P0 fields resolve once each: lifecycle/rejection in §§3--4; automatic
query in §5; equality-only/root-bound IDs in §2; public-only topology in
§§3.1/4; singular retrieval arithmetic in §6; common RAW in §7.2; the common
16+1 PCFL-L transport in §7; lexical-only RS8 MODEL in §§3.3/4; and statistical
roots in §2.1. No field imports an implementation default.

1. **PASS in proposal:** EV/IN include root salt; DOC inherits it (§2.3).
2. **PASS:** every attempt has total source/status/reason rules; accepted
   counts are 1/2/8; reject sources follow literal successful resolution (§3.3).
3. **PASS as exact pre-source gate:** parser is printed; exhaustive named
   allow/deny golden bytes and independent registry are mandatory (§3.1).
4. **PASS:** task-local TH IDs and receipts are exact (§2.3).
5. **PASS as exact pre-source gate:** token bytes, conversions, evaluation
   order, no-FMA arithmetic, PPR sums, Jaccard, and goldens are singular (§6).
6. **PASS:** same RAW machinery and branch-local contents are explicit (§7.2).
7. **PASS as later-lifetime binding:** one PCFL-L wire is exact for all three
   arms; TSJ compatibility is field-exact and Stage2A/TSJ stay unchanged (§7).
8. **PASS:** certificate and RS8 use the same four roots; all other root
   classes are disjoint (§2.1).
9. **PASS as stage gate:** root/wire/ranking/load-cut/lifetime/TSJ schemas,
   digest law, source hashes, and stage-open bindings are explicit (§9).
10. **PASS:** acquisition/formation and evaluation maxima are separate and
    summed in P4/P5 (§§9.2,11).
11. **PASS as prospective source gate:** BRIDGE_EVENT must satisfy exhaustive
    public-path necessity before actor execution (§8).

The self-audit is not ratification. A fresh independent reviewer must inspect
these exact bytes and may return REWORK.

## 14. Unresolved decisions and evidence still absent

**Genuinely unresolved human design choices: none.** The core remains
q16/B8192 with q16/B16384 access-only sensitivity.

Evidence not yet produced is deliberately stage-gated: instantiated
machine-readable registry records, independent golden bytes, PCFL-L source
and injected tests, an authentic TSJ completion receipt,
material/generator/scorer hashes,
tokenizer/model/runtime hashes, profile times, and actual scientific results.
These are required receipts, not permission or post-result choices. Their
absence means `GO_CPU_SOURCE=false` until a fresh audit promotes this proposal;
it does not reopen the algorithm.

## Evidence reconciled (informative only)

- `research_notes/analysis/2026-09-14_active_text_native_v21_auto_exact_contract_fresh_audit.md`
- `research_notes/analysis/2026-09-13_active_text_native_v21_auto_exact_contract_draft.md`
- `research_notes/analysis/2026-09-13_active_text_native_v2_adversarial_audit.md`
- `research_notes/analysis/2026-09-13_pcfl_dev_to_paper_grade_successor.md`
- `research_notes/analysis/2026-09-13_two_sleep_own_experience_junction_source_contract_v4.md`
- `research_notes/analysis/2026-09-13_two_sleep_own_experience_junction_v4_fresh_source_readiness_audit.md`
- `research_notes/analysis/2026-09-13_m_combine4_stage2a_binding_successor_v5.md`
- `research_notes/analysis/2026-09-13_pcfl_reusable_affine_gate_stratum.md`
- `research_notes/64_iclr_paper_core_and_benchmark_v2.md`
