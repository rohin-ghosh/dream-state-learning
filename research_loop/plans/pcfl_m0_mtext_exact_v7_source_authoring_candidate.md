# PCFL M0 + M-TEXT-SUPPLIED V7 — exact baseline-closed source-authoring candidate

Date: 2026-09-10

Status: **source-only proposal for fresh deliberation**. It authorizes no
source authoring/import/execution/checking, implementation, preparation,
materialization, fixture/root/data generation, model/tokenizer use, benchmark,
training, LoRA, parenting, GPU use, resource acquisition, scientific claim,
release, or submission.

## 0. Decision

V5 and V6 were initialized but never run. Their read-only preflights found and
preserved exact packet defects before any formal model call. V7 keeps the
finite PCFL experiment unchanged and closes the last baseline-interface bytes:
mode/protocol routing, BLOCKED versus passive-null behavior, TARGET_ONLY read
semantics, and deterministic RAG query/scoring/return/fingerprint behavior.

## 1. Normative stack

V7 inherits the exact V6 stack in
`pcfl_m0_mtext_exact_v6_source_authoring_candidate.md`, SHA-256
`74134a0545816d1cfd9edeb3229d77bc83261fa6582cd0f8dd459df1102d822f`,
including all bound V4/V5 inputs and V6's complete-context and typed-baseline
repairs.

The V6 preflight at SHA-256
`69910384ead946bfb407eda8d79963c3e98918f5873be6b09b339483d65924f6`
is preserved negative evidence. Its three baseline blockers are replaced by
`20260910_pcfl_v7_baseline_projection_exact_closure_v1.md`, SHA-256
`6ca612e41e3462ca6997cabcd089439a8d24be06ca7d37b5e29183ec362dd272`.

That V7 advisory wins only for V6 baseline-repair sections 1, 2, 3, and 5.
This candidate replaces only the change/workflow/source-plan identities and
decision boundary with V7. All other V6/V5/V4 clauses remain exact. Missing or
conflicting bytes require `REWORK`; no implementer may choose a reading.

## 2. Closed memory interfaces

The phase-local public memory modes are now exactly:

```text
COMMON_READER
BLOCKED_READER
PASSIVE_NULL_READER
RAW_STATIC
RAG_DETERMINISTIC
NATIVE_GRAPH_STATIC
NO_MEMORY_SURFACE
```

The complete condition/phase table in the V7 advisory determines one legal
mode, typed static/RAG payload, and read protocol.

- REACHOUT_OFF and NO_MEMORY accept normal anchor/cursor reads but always
  return fixed `BLOCKED` without lookup.
- PASSIVE_SIGNATURE accepts the same reads but returns fixed `NOT_FOUND` null
  envelopes without lookup. It is no longer conflated with BLOCKED.
- TARGET_ONLY's P/D tape may list the 24 registered reads; they execute
  open-loop against BLOCKED and no return can feed the completed call.
- Every U phase has no memory interface.
- RAW and native graph are typed static public surfaces.
- RAG exposes only zero-argument `RAG_READ`; the model cannot author a query.

The consumer graph now explicitly routes public `mode` and `read_protocol`
through a typed projector to the public controller and model turn. It also has
closed BLOCKED and PASSIVE_NULL reader nodes. No private handoff, carrier
content, score, oracle, condition, route, scratch, or session data reaches
those nodes.

## 3. Exact deterministic RAG

RAG documents are the chronological public primitive rows. Handles are
exactly `d00..dff`; 257 rows reject. Scoring bytes are JCS public-event bytes
without inert padding. Query bytes are the ordered public current-state,
goal-start, goal-target, and optional last-event alias fields joined by one
space plus one LF. ASCII `[a-z0-9]+` tokenization preserves order and
multiplicity.

BM25 is no longer a host-default phrase. It uses 50-digit Decimal arithmetic,
ROUND_HALF_EVEN, exact `k1=1.2`, `b=0.75`, the complete registered IDF/TF
equations, and integer `score_e12` quantization. Ranking is descending integer
score then ascending public document handle. Returns contain exactly four
typed slots. Empty corpus, BLOCKED post-action behavior, repeat counts 1..8,
null padding, and domain-separated length-delimited fingerprints are exact.

Independent golden reproduction and mutations cover query ordering and
multiplicity, scoring precision/rounding/traps, ties, slots, fingerprints,
free-text query injection, semantic-ID ranking, post-action lookup, hidden
inputs, delayed U-output borrowing, and uncharged work.

## 4. What does not change

V7 adds no condition, phase, request, token, root, topology, endpoint, gate,
or claim. It retains exactly:

- the 18-condition/501-slot/148,224-generated-token-per-root registry;
- the 64 deterministic roots and 16/32/16 finite split;
- all reader, action, provenance, reset, resource, algebra-shortcut,
  producer/scorer-neutrality, bridge/twin, applicability, gate, and claim
  rules in the inherited stack;
- test IDs `-00..-19` and `-23..-27`, with 20..22 unused;
- zero FeltCraft V7 runtime reuse (the PCFL packet's V7 version label does not
  create a dependency on the unrelated FeltCraft V7 tree); and
- a maximum future claim about supplied memory use in one fixed finite
  topology/model only—not DREAM, SLEEP, LoRA, learning, retention, parenting,
  compression, lifetime improvement, generalization, or the organism.

## 5. Exact source plan and authority

V7's separately bound `source_authoring_plan.json` has exactly 24 sorted
literal paths: 23 manifest members and one nonauthoritative manifest output.
It keeps the previously validated roles/media/maxima while using V7-scoped
paths. The planned handoff/object schemas, projection allowlist, consumer
graph, runtime/resource files, test spec, and mutation file must encode the
exact V7 baseline closure; no extra member is implied.

Fresh consensus may only recommend `SOURCE_CANDIDATE_AUTHORING_AUTHORITY`.
Only a later exact human grant could authorize writing/hashing those inert
files and the nonauthoritative manifest. It still could not import,
syntax-check through an interpreter, execute, test, or materialize them.

Actual source bytes require a new exact-byte review, deliberation, and human
`PREPARATION_EXECUTION_AUTHORITY` before one deterministic CPU preparation.
No stage self-promotes.

## 6. Requested decision and stop

The V7 five-role workflow must determine whether the exact inherited stack,
V7 closure, source plan, and source-authoring-only boundary leave any
outcome-changing choice. If so, `REWORK`. If not, it may recommend proceeding
and must stop at `human_required`.

No source authoring or execution, preparation, implementation,
materialization, fixture/root/data generation, model/tokenizer use, benchmark,
training, LoRA, parenting, GPU use, resource acquisition, scientific claim,
release, or submission is requested or implied.
