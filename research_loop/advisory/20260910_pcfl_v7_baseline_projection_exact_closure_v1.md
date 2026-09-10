# PCFL V7 exact baseline-interface closure — v1

Date: 2026-09-10

Status: **source-only advisory**. This authorizes no source authoring,
execution, implementation, preparation, materialization, fixture/root/data
generation, model/tokenizer use, benchmark, training, LoRA, parenting, GPU
use, scientific claim, release, or submission.

## 0. Disposition

The V6 packet was initialized but not run. Fresh read-only preflight confirmed
that V6 closed the missing-context defect and introduced the right typed
baseline surface, but found three exactness gaps: missing consumer edges for
mode/protocol selection, conflated BLOCKED versus passive-null returns, and an
underspecified deterministic RAG function. Preserve V6 unchanged and fork.

This advisory replaces V6 baseline-repair sections 1, 2, 3, and 5 only where
the exact definitions below are stricter. It adds no model condition, call,
token, root, endpoint, gate, or claim.

## 1. Exact phase-local memory modes

`PublicMemorySurfaceV4` remains the same four-field closed object, but `mode`
and `read_protocol` use these exact enums:

```text
mode:
  "COMMON_READER" | "BLOCKED_READER" | "PASSIVE_NULL_READER" |
  "RAW_STATIC" | "RAG_DETERMINISTIC" | "NATIVE_GRAPH_STATIC" |
  "NO_MEMORY_SURFACE"

read_protocol:
  "ANCHOR_CURSOR" | "BLOCKED_ANCHOR_CURSOR" |
  "PASSIVE_NULL_ANCHOR_CURSOR" | "RAG_AUTO" | "NONE"
```

The complete legal mode table is:

| phase-local conditions | mode | static_context | rag_corpus | read_protocol |
|---|---|---|---|---|
| applicable P/D of AUTH, AUTH_SCRATCH_OFF, ATOMS, DERANGED, BRIDGE_CUT, TWIN_REDIRECT, OLD_CUT, NEW_CUT, NO_PERSIST_NEW, AUTH_NO_FEEDBACK_TAPE | `COMMON_READER` | null | null | `ANCHOR_CURSOR` |
| applicable P/D of REACHOUT_OFF and NO_MEMORY | `BLOCKED_READER` | null | null | `BLOCKED_ANCHOR_CURSOR` |
| applicable P/D of PASSIVE_SIGNATURE | `PASSIVE_NULL_READER` | null | null | `PASSIVE_NULL_ANCHOR_CURSOR` |
| applicable P/D of RAW_CONTEXT | `RAW_STATIC` | `RawContextPublicV4` | null | `NONE` |
| applicable P/D of RAG_RAW | `RAG_DETERMINISTIC` | null | `RagCorpusPublicV4` | `RAG_AUTO` |
| applicable P/D of NATIVE_GRAPH | `NATIVE_GRAPH_STATIC` | `NativeGraphPublicV4` | null | `NONE` |
| applicable P/D of TARGET_ONLY | `BLOCKED_READER` | null | null | `BLOCKED_ANCHOR_CURSOR` |
| every applicable U phase | `NO_MEMORY_SURFACE` | null | null | `NONE` |

A structurally absent phase emits no handoff. Any other combination rejects.
The public mode/protocol reveal only the actual interface; they never contain
a private condition ID, root, h, split, transform, answer, score, or oracle.

### 1.1 BLOCKED versus PASSIVE_NULL

`BLOCKED_READER` accepts the ordinary public anchor/cursor READ grammar so the
registered read opportunities remain real. Every legal pre-action request:

- consumes one READ opportunity;
- performs no carrier/index lookup;
- returns `MemoryReturnV4.status="BLOCKED"`, the public request-derived
  fingerprint, echoed public anchor/cursor, `NULL_ATOM`, `NULL_LINK`, empty
  grants, the public repeat count, and fixed inert padding.

`PASSIVE_NULL_READER` accepts the same grammar and consumes the same
opportunity, but returns `status="NOT_FOUND"` with the same remaining null/
empty shape. It performs no lookup. This is the condition-independent passive
signature inherited by PASSIVE_SIGNATURE and is not interchangeable with a
disabled/BLOCKED interface.

For TARGET_ONLY's one-shot tape, syntactically listed READ commands are
executed open-loop against `BLOCKED_READER` and count against its 24 P/D READ
opportunities, but no return is fed back into the already completed model
call. Its U phase has no READ opportunity. This preserves the registered
4-call/24-READ opportunity roster without granting memory or feedback.

For both readers:

```text
request_fingerprint = lower_hex(
  SHA256("PCFL-MEMORY-REQUEST-v4\0" ||
         uint16be(len(anchor_utf8)) || anchor_utf8 ||
         uint16be(cursor) || uint16be(repeat_count)))
```

`repeat_count` is `1..8`; an out-of-range/malformed request is a registered
structural error. The fingerprint is independent of carrier, condition,
route, private metadata, score, and truth.

## 2. Complete mode/protocol consumer edges

Add these exact edges to the closed consumer graph:

```text
VERIFIED_PUBLIC.memory_surface.{mode,read_protocol}
  -> MEMORY_INTERFACE_PROJECTOR
MEMORY_INTERFACE_PROJECTOR -> PUBLIC_CONTROLLER
PUBLIC_CONTROLLER -> ModelTurnPublicV4.{memory_mode,read_protocol}

PUBLIC_CONTROLLER.{anchor,cursor,reader_open,repeat_state}
  -> BLOCKED_READER
BLOCKED_READER -> PUBLIC_CONTROLLER

PUBLIC_CONTROLLER.{anchor,cursor,reader_open,repeat_state}
  -> PASSIVE_NULL_READER
PASSIVE_NULL_READER -> PUBLIC_CONTROLLER
```

`ModelTurnPublicV4` therefore replaces `memory_mode` alone by the exact pair:

```text
memory_mode:HandoffPublicV4.memory_surface.mode,
read_protocol:HandoffPublicV4.memory_surface.read_protocol,
```

The renderer consumes those two typed fields from `ModelTurnPublicV4` and
selects one registered public instruction fragment from a closed static map:

```text
ANCHOR_CURSOR              -> advertise READ(anchor,cursor)
BLOCKED_ANCHOR_CURSOR      -> advertise READ(anchor,cursor), documented BLOCKED
PASSIVE_NULL_ANCHOR_CURSOR -> advertise READ(anchor,cursor), documented NOT_FOUND
RAG_AUTO                   -> advertise RAG_READ with no arguments
NONE                       -> advertise no memory command
```

The map and rendered fragments remain deferred to the separately frozen exact
M-TEXT source bytes; the selection rule is fixed here. An unadvertised memory
command is structurally invalid. The response schema remains one closed union
`PCFL_COMMAND_V4`; protocol selects the legal variant, not arbitrary prose.

`MEMORY_INTERFACE_PROJECTOR`, `BLOCKED_READER`, and
`PASSIVE_NULL_READER` receive no private handoff field, carrier content,
hidden bit, answer, score, scorer/oracle, split, condition, transform, route,
model scratch, or session/cache identity. All other edges remain forbidden.

## 3. Byte-exact deterministic RAG

### 3.1 Documents and handles

`RagCorpusPublicV4.documents` has at most 256 rows. For zero-based chronological
ordinal `i`, `public_document_handle` is exactly `"d" + lower_hex2(i)`; hence
the grammar is `^d[0-9a-f]{2}$`. Handles are unique and consecutive. Each
document's scoring bytes are JCS UTF-8 of its `PublicPrimitiveEventV4` after
removing the inert `pad` field, with no BOM and no trailing LF. Retrieval
tokens are the non-overlapping matches of ASCII regex `[a-z0-9]+` after ASCII
lowercasing those bytes, in byte order. Padding never enters retrieval.

Corpus construction is sealed before goal release. Its document bytes,
handles, token lists, document frequencies, and average length cannot depend
on goal, answer, preferred path, score, scorer/oracle, split, condition display
name, model output, or dispatch order.

### 3.2 Query bytes

At each legal `RAG_READ`, form the ordered field vector:

```text
[current_public_state_alias,
 released_public_goal_start_alias,
 released_public_goal_target_alias,
 last_event.src_alias if present,
 last_event.relation_or_experiment_alias if present,
 last_event.dst_or_outcome_alias if present]
```

Absent optional fields are omitted; present fields are never deduplicated.
Every field must match its closed lowercase public-alias grammar. Query bytes
are ASCII fields joined by one byte `0x20`, followed by one LF byte `0x0a`.
Query tokens are `[a-z0-9]+` matches in order; multiplicity is preserved and
each occurrence contributes separately to the score. No other prompt text,
scratch, model output, free-text query, carrier field, or private value enters.

### 3.3 Exact BM25 arithmetic

Use Python-standard decimal semantics as a normative arithmetic definition,
not a host default:

```text
context precision = 50 significant decimal digits
rounding = ROUND_HALF_EVEN
traps = DivisionByZero, InvalidOperation, Overflow
k1 = Decimal("1.2")
b  = Decimal("0.75")
half = Decimal("0.5")

N = number of documents
dl(d) = number of retrieval-token occurrences in d
avgdl = sum_d dl(d) / N
df(t) = number of documents containing t at least once
f(t,d) = number of occurrences of t in d
idf(t) = ln(Decimal(1) + (N - df(t) + half) / (df(t) + half))
tf(t,d) = f(t,d) * (k1 + Decimal(1)) /
          (f(t,d) + k1 * (Decimal(1) - b + b * dl(d) / avgdl))
raw_score(d,q) = sum over every query-token occurrence t of idf(t)*tf(t,d)
score_e12 = integer value of
            (raw_score * Decimal(10)^12).to_integral_value(ROUND_HALF_EVEN)
```

If `N=0`, return NOT_FOUND without evaluating `avgdl`. A nonempty corpus with
`avgdl=0`, a trapped decimal condition, negative/out-of-u64 `score_e12`, or an
unrepresentable input rejects the fixture/runtime; it is never approximated.
Rank by descending `score_e12`, then ascending raw ASCII document-handle bytes.
Return the first four, padding with typed null slots when fewer exist.

### 3.4 Closed return and fingerprint

```text
RagReturnPublicV4 := {
  v:4,
  status:"FOUND"|"NOT_FOUND"|"BLOCKED",
  fingerprint:hex64,
  query_tokens:[string,...],
  slots:[RagSlotPublicV4,RagSlotPublicV4,
         RagSlotPublicV4,RagSlotPublicV4],
  repeat_count:u8,
  pad:string
}

RagSlotPublicV4 := {
  rank:0|1|2|3,
  document:RagDocumentPublicV4|NULL_RAG_DOCUMENT,
  score_e12:u64|0,
  pad:string
}
```

For FOUND, at least one real document exists; real slots are rank-ordered and
null slots follow. NOT_FOUND has four null slots when `N=0` but retains the
publicly constructed query tokens. After the first relation attempt, including
NO_EFFECT, status is BLOCKED, no query construction/scoring/corpus lookup
occurs, query_tokens is empty, and all slots are null. Null slots have score
zero. `repeat_count` is `1..8`. All records
are closed; exact per-type fixed padding is derived under the existing V4 size
rule and later human-frozen before execution.

For an open request:

```text
fingerprint = lower_hex(
  SHA256("PCFL-RAG-QUERY-v4\0" ||
         uint32be(len(query_utf8)) || query_utf8 ||
         uint16be(repeat_count)))
```

For BLOCKED, replace `query_utf8` by the zero-length string but retain the same
domain, length field, and repeat encoding. No corpus hash, document score,
private route, condition, truth, or semantic ID enters the fingerprint.

## 4. Closed RAG consumer graph

Retain V6's RAG edges, with the exact inputs renamed:

```text
VERIFIED_PUBLIC.memory_surface.rag_corpus -> RAG_RETRIEVER
PUBLIC_CONTROLLER.{current_public_state,released_public_goal,
                   last_ordinary_public_event,reader_open,repeat_state}
  -> RAG_RETRIEVER
RAG_RETRIEVER -> PUBLIC_CONTROLLER
PUBLIC_CONTROLLER -> ModelTurnPublicV4.last_public_result
```

The retriever implementation receives the verified typed fields, not generic
objects. It has no edge from the model response except the parsed zero-argument
`RAG_READ` trigger. The model cannot alter the query. Corpus construction and
indexing are producer-side and goal-blind; the dynamic query is intentionally
goal-aware and fully public. Swapping public goals may change query/return
bytes but must leave the sealed corpus/index bytes identical.

## 5. Replacement acceptance test 19

`MTEXTV4-BASELINE-PUBLIC-PROJECTION-AND-RESET-19` now passes only if, for every
applicable root/phase:

1. the exact seven-mode table and mode/protocol combinations validate;
2. mode/protocol flow through the typed projector into controller and
   `ModelTurnPublicV4` and select only the registered command fragment;
3. BLOCKED, PASSIVE_NULL, TARGET_ONLY open-loop BLOCKED, static RAW/native,
   and RAG behavior match their distinct registered opportunities;
4. document handles/bytes/tokens, query field order/bytes/tokens, Decimal BM25,
   score quantization/order, four-slot return, and both fingerprint preimages
   match independent golden vectors;
5. first-action read cut, delayed supplied-fixture origin, reset survivor
   allowlist, rendered size/token caps, and resource charges pass; and
6. every V6 leakage mutation plus mutations of mode/protocol edges, BLOCKED
   versus NOT_FOUND, query ordering/multiplicity, pad tokenization, IDF/TF,
   decimal precision/rounding/traps, score quantization, tie order, slot/null
   order, fingerprint domain/length/repeat, TARGET_ONLY feedback, and generic
   object access fails closed.

Positive fixtures include empty, one-, fewer-than-four-, exactly-four-, and
greater-than-four-document corpora; duplicate query tokens; exact score ties;
and repeat counts 1 and 8. Reject fixtures include 257 documents, malformed/
duplicate/nonconsecutive handles, zero-token nonempty corpus, decimal trap,
rank overflow, free-text query, semantic-ID tie use, post-action lookup,
private query field, and U-output-derived delayed corpus.

The independent checker must reproduce query bytes, integer scores, ranks,
return bytes, and fingerprints without importing the retriever. Test 19 is
required before any baseline model call or practical-baseline clause.

## 6. Successor boundary

A successor must preserve the zero-attempt V5 and V6 states, include their
fresh preflight audits as context, and bind this advisory. It may deliberate
whether inert source may be authored next; it cannot author or execute it.
