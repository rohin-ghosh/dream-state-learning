# PCFL M0 + M-TEXT-SUPPLIED V8 — repeat/null-closed source-authoring candidate

Date: 2026-09-10

Status: **source-only proposal for fresh deliberation**. It authorizes no
source authoring/import/execution/checking, implementation, preparation,
materialization, fixture/root/data generation, model/tokenizer use, benchmark,
training, LoRA, parenting, GPU use, resource acquisition, scientific claim,
release, or submission.

## 0. Decision

V5, V6, and V7 were initialized but never run. Their fresh read-only
preflights caught exact packet defects before any formal model call. V8 keeps
the finite PCFL experiment unchanged and closes only V7's last two byte-level
defects: repeat-count saturation and the exact null RAG document.

## 1. Normative stack

V8 inherits the exact V7 stack in
`pcfl_m0_mtext_exact_v7_source_authoring_candidate.md`, SHA-256
`ab1aee14de83c82ded3ff5c22cf763d5cb875ed47a20491dd33547aad953874b`,
including its complete bound V4/V5/V6 inputs and all endpoint, provenance,
resource, handoff, baseline, claim, and authority closures.

The V7 fresh preflight at SHA-256
`88a1deeb8c2ecaef1370c7206b35419cccadb114c280feffcf84faa15f513ec6`
is preserved negative evidence. Its two blockers are replaced exactly by
`20260910_pcfl_v8_repeat_null_exact_closure_v1.md`, SHA-256
`5c5321a7d208830a4f1c2fd5b04669ca56207e6403d57a68483954fe2057d597`.

That V8 advisory wins only for V7 clauses that state `repeat_count` is `1..8`,
V7's undefined `NULL_RAG_DOCUMENT`, and their directly dependent fixtures,
fingerprints, padding, schemas, and mutations. All other V7/V6/V5/V4 clauses
remain exact. Missing or conflicting bytes require `REWORK`; no implementer
may choose a reading.

## 2. Exact repeat behavior

Every model-visible memory-return repeat count has the inherited type
`1|2|3`. For each byte-identical request identity within one phase, the first,
second, and every later legal request return `1`, `2`, and `3`. Counters are
independent by identity and reset at phase and condition/root boundaries.

Anchor/cursor request identity is its exact public anchor bytes plus cursor.
RAG request identity is its exact deterministic public query bytes; post-action
BLOCKED RAG reads use the registered zero-length query. The saturated visible
count, never the unsaturated request ordinal, enters fingerprints and returns.
The eight-opportunity maximum is unchanged.

## 3. Exact null RAG behavior

An empty RAG document is the JSON literal `null`. Every RAG return has four
slots whose ranks equal their array ordinals `0..3`. Null slots have
`document:null`, `score_e12:0`, and exact inert fixed-size padding. Real slots
precede null slots. NOT_FOUND and BLOCKED contain four null slots; FOUND
contains one to four real slots and enough trailing null slots to reach four.

Independent goldens cover saturation through eight identical reads,
interleaved request identities, counter resets, literal null bytes, every null
rank, four-null returns, and FOUND returns with one through four real rows.
The registered mutations reject unsaturated/illegal counts, alternate null
sentinels, missing keys, wrong rank/score/order/padding/count, and fingerprint
or reset drift.

## 4. What does not change

V8 adds no condition, phase, request, generated token, root, topology,
endpoint, gate, or claim. It retains exactly:

- the 18-condition/501-slot/148,224-generated-token-per-root registry;
- the 64 deterministic roots and 16/32/16 finite split;
- the seven phase-local public memory modes and their exact typed routes;
- the V7 deterministic public RAG query, 50-digit Decimal BM25, integer
  ranking, four-slot return, and closed consumer graph;
- all inherited reader, action, provenance, reset, resource,
  algebra-shortcut, producer/scorer-neutrality, bridge/twin, applicability,
  gate, and claim rules;
- test IDs `-00..-19` and `-23..-27`, with 20..22 unused;
- zero FeltCraft V7 runtime reuse; and
- a maximum future claim about supplied memory use in one fixed finite
  topology/model only—not DREAM, SLEEP, LoRA, learning, retention, parenting,
  compression, lifetime improvement, generalization, or the organism.

## 5. Exact source plan and authority

V8's separately bound `source_authoring_plan.json` has exactly 24 sorted
literal paths: 23 manifest members and one nonauthoritative manifest output.
It keeps V7's validated roles, media types, maxima, and filenames under a
V8-scoped directory. The planned source must encode the V8 repeat/null closure;
no extra member is implied.

Fresh consensus may only recommend `SOURCE_CANDIDATE_AUTHORING_AUTHORITY`.
Only a later exact human grant could authorize writing and hashing the 23
listed inert files and their nonauthoritative manifest. It still could not
import, syntax-check through an interpreter, execute, test, or materialize
them.

Actual source bytes require a later exact-byte review, deliberation, and human
`PREPARATION_EXECUTION_AUTHORITY` before one deterministic CPU preparation.
No stage self-promotes.

## 6. Requested decision and stop

The V8 five-role workflow must determine whether the inherited exact stack,
V8 closure, source plan, and source-authoring-only boundary leave any
outcome-changing choice. If so, `REWORK`. If not, it may recommend proceeding
and must stop at `human_required`.

No source authoring or execution, preparation, implementation,
materialization, fixture/root/data generation, model/tokenizer use, benchmark,
training, LoRA, parenting, GPU use, resource acquisition, scientific claim,
release, or submission is requested or implied.
