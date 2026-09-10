# PCFL V6 baseline projection and context-closure preflight repair — v1

Date: 2026-09-10

Status: **source-only advisory**. This file authorizes no source authoring,
execution, implementation, materialization, fixture/root/data generation,
model/tokenizer use, benchmark, training, LoRA, parenting, GPU use, scientific
claim, release, or submission.

## 0. Why V5 must be preserved and forked

The initialized V5 packet received zero deliberation attempts, but its
read-only preflight found two exact defects:

1. its directive asks reviewers to assess the complete V4 chain while its
   workflow omits V4 `human_directive.txt`; and
2. its closed handoff/consumer graph has no typed path for the retained
   `RAW_CONTEXT_RECURRENT`, `RAG_RAW_RECURRENT`, or
   `NATIVE_GRAPH_RECURRENT` baseline data.

The initialized V5 state and hashes are immutable evidence and must not be
refreshed or edited. A successor V6 workflow must include the missing V4
directive and adopt the exact baseline projection below.

## 1. One closed public memory surface

Replace the V5 repair's `HandoffPublicV4` field set by adding exactly one
field, `memory_surface`, after `semantic_cut` and before `carrier`:

```text
HandoffPublicV4 := {
  v:4,
  artifact_type:"pcfl_m0_handoff_public",
  instrument:"PCFL_M0_THIN_V4",
  phase_public_mode:"PATH"|"UNCERTAINTY"|"ACQUIRE"|"DELAYED",
  semantic_cut:"OLD"|"NEW"|"DELAYED",
  memory_surface:PublicMemorySurfaceV4,
  carrier:CarrierV4,
  initial_view:FiniteViewV4,
  action_catalog:ActionCatalogPublicV4,
  budgets:{reads_remaining:u8,relation_attempts_remaining:u8,
           terminal_opportunity_remaining:0|1},
  response_schema:"PCFL_COMMAND_V4",
  pad:string
}
```

`PublicMemorySurfaceV4` is the exact closed tagged union:

```text
PublicMemorySurfaceV4 := {
  mode:"COMMON_READER"|"IDENTITY_NULL_READER"|"RAW_STATIC"|
       "RAG_DETERMINISTIC"|"NATIVE_GRAPH_STATIC"|"NO_MEMORY_SURFACE",
  static_context:null|RawContextPublicV4|NativeGraphPublicV4,
  rag_corpus:null|RagCorpusPublicV4,
  read_protocol:"ANCHOR_CURSOR"|"RAG_AUTO"|"IDENTITY_NULL"|"NONE"
}
```

The legal combinations are exhaustive:

| mode | static_context | rag_corpus | read_protocol | conditions |
|---|---|---|---|---|
| `COMMON_READER` | null | null | `ANCHOR_CURSOR` | applicable P/D phases of AUTH, AUTH_SCRATCH_OFF, ATOMS, DERANGED, BRIDGE_CUT, TWIN_REDIRECT, OLD_CUT, NEW_CUT, NO_PERSIST_NEW, AUTH_NO_FEEDBACK_TAPE |
| `IDENTITY_NULL_READER` | null | null | `IDENTITY_NULL` | REACHOUT_OFF, NO_MEMORY, PASSIVE_SIGNATURE |
| `RAW_STATIC` | `RawContextPublicV4` | null | `NONE` | RAW_CONTEXT |
| `RAG_DETERMINISTIC` | null | `RagCorpusPublicV4` | `RAG_AUTO` | RAG_RAW |
| `NATIVE_GRAPH_STATIC` | `NativeGraphPublicV4` | null | `NONE` | NATIVE_GRAPH |
| `NO_MEMORY_SURFACE` | null | null | `NONE` | every applicable U phase, TARGET_ONLY P/D, and any other applicable phase whose registered condition has neither reader nor baseline memory |

Private condition labels select one legal projection before verification but
are not fields of the public union. The public `mode` reveals only the actual
interface made available to the model. This is intended treatment exposure
for deliberately unequal baselines and carries no root, hidden bit, answer,
preferred path, score, split, or condition identifier.

Mode selection is phase-local. In particular, AUTH's P/D phases use
`COMMON_READER`, while its U phase uses `NO_MEMORY_SURFACE`; the public
uncertainty table remains part of the registered U `initial_view`, not a
memory carrier. A condition with a structurally absent phase produces no
handoff for that phase rather than a dummy memory surface.

### 1.1 Exact raw context

```text
RawContextPublicV4 := {
  schema:"PCFL_RAW_CONTEXT_V4",
  rows:[PublicPrimitiveEventV4,...],
  order:"CHRONOLOGICAL_POSITION",
  pad:string
}
```

Rows are every and only condition-entitled primitive public evidence row at
the phase cut, sorted by the closed provenance position. They contain no
SYNTH link, semantic hash, checker field, score, answer, future event, root,
split, condition, or private provenance. At delayed entry the new public rows
come only from the same supplied canonical correct-acquisition fixture as the
D carrier; they never come from a U model receipt.

### 1.2 Exact native graph ceiling

```text
NativeGraphPublicV4 := {
  schema:"PCFL_NATIVE_GRAPH_V4",
  atoms:[PublicAtom,...],
  links:[PublicAuthLink,...],
  order:"PUBLIC_CAPABILITY_HANDLE",
  pad:string
}
```

It contains every and only authentic condition-entitled atom and supported
link at the phase cut, ordered by neutral public handles. It contains no
semantic hash, goal rank, preferred path, answer, score, root, split,
condition, or checker/oracle field. It is an explicit unequal-resource
ceiling, never an equal-resource control.

### 1.3 Exact deterministic RAG corpus and retrieval

```text
RagCorpusPublicV4 := {
  schema:"PCFL_RAG_CORPUS_V4",
  documents:[RagDocumentPublicV4,...],
  order:"CHRONOLOGICAL_POSITION",
  pad:string
}

RagDocumentPublicV4 := {
  public_document_handle:string,
  event:PublicPrimitiveEventV4,
  pad:string
}
```

The documents are byte-equivalent public primitive rows to RAW_STATIC, with
neutral handles assigned in chronological order. The fixed retrieval query is
constructed only from the current public state alias, released public goal
start/target aliases, and last ordinary public event aliases. Tokenization is
lowercase ASCII `[a-z0-9]+`; BM25 uses `k1=1.2`, `b=0.75`, root-local document
frequency, top four, and chronological public document handle as the final tie
breaker. Goal dependence in this separately labeled baseline query is intended
and must be receipt-visible; carrier/index bytes remain sealed before goal
release.

The command schema advertises one `RAG_READ` form only when
`read_protocol="RAG_AUTO"`. `RAG_READ` takes no model-authored query or anchor.
Each invocation recomputes the fixed query from the current public state/goal/
last-event tuple and returns four fixed-size document slots. Up to eight
pre-action invocations are charged per applicable path phase; repeats return
the same documents plus the public repeat count. The first relation attempt,
including `NO_EFFECT`, closes RAG access. A post-close request returns the same
fixed-size `BLOCKED` envelope without lookup. No RAG output grants a common-
reader atom/link capability or can populate connected-trace endpoints.

`RAW_STATIC` and `NATIVE_GRAPH_STATIC` advertise no read form and have zero
READ opportunities. An unadvertised memory command is structurally invalid;
it does not create a hidden retrieval path.

## 2. Exact model projection

Replace `ModelTurnPublicV4` with:

```text
ModelTurnPublicV4 := {
  v:4,
  prompt_mode:HandoffPublicV4.phase_public_mode,
  memory_mode:HandoffPublicV4.memory_surface.mode,
  static_memory:null|RawContextPublicV4|NativeGraphPublicV4,
  view:HandoffPublicV4.initial_view,
  action_catalog:HandoffPublicV4.action_catalog,
  budgets:HandoffPublicV4.budgets,
  last_public_result:null|PublicTransitionResultV4|MemoryReturnV4|
                     RagReturnPublicV4,
  scratch:null|string,
  response_schema:HandoffPublicV4.response_schema,
  pad:string
}
```

`static_memory` is non-null exactly for RAW_STATIC and NATIVE_GRAPH_STATIC and
is rendered unchanged on every request in that phase. It is null for all other
modes. `rag_corpus` is never rendered directly. A `RagReturnPublicV4` may
appear only after a valid pre-action `RAG_READ` and contains exactly four
fixed-size document slots plus status, public query fingerprint, repeat count,
and inert padding. The fingerprint hashes only the public query terms and
repeat count; no corpus hash, private route, condition, score, or semantic ID
is included.

The existing rule remains: the carrier and semantic cut are never dumped into
the prompt; no private handoff field is model-visible.

## 3. Consumer-graph additions

The V5 handoff consumer graph remains closed, with exactly these additional
edges:

```text
VERIFIED_PUBLIC.memory_surface.static_context -> BASELINE_STATIC_PROJECTOR
BASELINE_STATIC_PROJECTOR -> ModelTurnPublicV4.static_memory

VERIFIED_PUBLIC.memory_surface.rag_corpus -> RAG_RETRIEVER
PUBLIC_CONTROLLER.{current_public_state,released_public_goal,
                   last_ordinary_public_event,reader_open,repeat_state}
  -> RAG_RETRIEVER
RAG_RETRIEVER -> PUBLIC_CONTROLLER
PUBLIC_CONTROLLER -> ModelTurnPublicV4.last_public_result
```

`BASELINE_STATIC_PROJECTOR` is a typed identity projection and receives no
private envelope. `RAG_RETRIEVER` receives no carrier, semantic ID, hidden bit,
answer, score, scorer/oracle, split, condition, transform label, route,
filename, session/cache state, model scratch, or free-text model query.

All other new edges remain forbidden. In particular:

```text
MTextHandoffV4 -> BASELINE_STATIC_PROJECTOR|RAG_RETRIEVER
SEALED_SCORER_CHECKER -> BASELINE_STATIC_PROJECTOR|RAG_RETRIEVER
RagCorpusPublicV4 -> RENDERER|MODEL
RawContextPublicV4|NativeGraphPublicV4 -> COMMON_READER
CarrierV4 -> RAG_RETRIEVER
MODEL.scratch|MODEL.output -> RAG_RETRIEVER query construction
```

## 4. Reset, accounting, and leakage rules

RAW/RAG/NATIVE delayed phases retain only their separately declared immutable
external public memory surface from the supplied D fixture. They do not retain
model messages, scratch, commands, tool returns, prior retrieval results,
query state, caches, KV state, sessions, RNG, timing, filenames, U model
outputs, or acquisition transcripts. This is a labeled alternative-channel
survivor and never evidence that the PCFL carrier was the sole surviving
channel.

The future M-TEXT boundary must prove all static contexts and RAG returns fit
the frozen 65,536-byte/8,192-input-token request caps without truncation. The
resource vector charges raw/native static bytes and tokens on every rendered
request, RAG corpus/index storage and build, every retrieval invocation,
postings/documents examined, returned bytes/tokens, and CPU time. No shared
CAS or warm cache makes an arm free.

For every root, phase, and baseline, mutate each private/root/h/condition/
split/transform/answer/score/scorer/oracle/route/session/timing/cache field and
require no change to public corpus/static bytes, document handles/order,
query terms, BM25 scores/order, returns, padding, errors, rendered bytes, or
token IDs. The one allowed query mutation is a released public goal/state/
last-event change; its exact changed query/return receipt must be accounted
and cannot change the sealed corpus/index.

Inject model free text into the RAG query, a semantic-hash tie breaker, a U
model output into D baseline memory, a SYNTH link into RAW/RAG, a checker field
into native graph, a hidden cache survivor, an uncharged index operation, and
a direct corpus-to-renderer edge. Every mutation must fail before model use.

## 5. Replacement acceptance test

Register the distinct test:

```text
MTEXTV4-BASELINE-PUBLIC-PROJECTION-AND-RESET-19
```

It passes only if the legal-mode table, exact tagged union, static projection,
deterministic RAG query/ranking/return, closed consumer edges, no-free-query
rule, first-action read cut, delayed supplied-fixture origin, reset survivor
allowlist, rendered limits, leakage mutations, and complete resource charges
all pass for every applicable root/phase. Any missing route, untyped generic
dictionary, illegal mode combination, private influence, truncation, hidden
retrieval, model-authored RAG query, uncharged work, or U-to-D borrowing fails
closed.

V5's intentionally unused test number 19 is now occupied by this exact
successor repair. Test numbers 20..22 remain unused. This adds no condition,
root, model call, token allowance, scientific clause, or efficiency claim.

## 6. Exact successor effect

A successor V6 must:

- include V4 `human_directive.txt` in its context list;
- include the frozen zero-attempt V5 workflow and state as negative/preflight
  evidence;
- make this advisory a normative replacement/addition to V5 sections 4 and
  10 only; and
- preserve every other V5 choice and hash-bound source-authoring boundary.

This repair authorizes nothing by itself.
