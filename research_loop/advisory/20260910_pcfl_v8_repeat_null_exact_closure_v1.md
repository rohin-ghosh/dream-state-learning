# PCFL V8 repeat/null exact closure — v1

Date: 2026-09-10

Status: **source-only advisory**. This authorizes no source authoring,
execution, implementation, preparation, materialization, fixture/root/data
generation, model/tokenizer use, benchmark, training, LoRA, parenting, GPU
use, scientific claim, release, or submission.

## 0. Disposition

The V7 packet was initialized but never run. Fresh read-only preflight found
only two byte-level defects: V7 widened an inherited three-valued repeat count
to `1..8`, and it named but did not define the null RAG document. Preserve V7
unchanged and fork. This advisory replaces only the conflicting repeat-count
clauses and the undefined null-document clauses in the V7 baseline closure.
It adds no condition, phase, request opportunity, model call, generated token,
root, topology, endpoint, gate, or claim.

## 1. One repeat rule for every public memory return

The inherited closed field remains exactly:

```text
repeat_count:1|2|3
```

For any legal memory request, including `ANCHOR_CURSOR`,
`BLOCKED_ANCHOR_CURSOR`, `PASSIVE_NULL_ANCHOR_CURSOR`, and zero-argument
`RAG_READ`, let `n_prior` be the number of prior legal requests in the same
phase whose request identity is byte-identical to the current one. Then:

```text
repeat_count = min(3, 1 + n_prior)
```

For anchor/cursor protocols, request identity is the ordered pair of the exact
public `anchor_utf8` bytes and integer `cursor`. For `RAG_READ`, request
identity is the exact public query UTF-8 bytes produced by the registered V7
query constructor. A BLOCKED post-action `RAG_READ` uses the registered
zero-length query bytes, so all such requests in one phase share one identity.
The counter resets at every phase boundary and condition/root reset. Malformed
requests still reject before incrementing a counter.

Thus the first, second, and every third-or-later identical request report 1,
2, and 3 respectively. The registered maximum of eight request opportunities
does not widen the field. All request and RAG fingerprints use this saturated
`repeat_count`; no unsaturated count enters a return, fingerprint, padding,
tokenization, resource charge, or model-visible byte.

Replace V7 positive repeat fixtures `1 and 8` by exact sequences covering
eight identical requests with visible counts `[1,2,3,3,3,3,3,3]`, plus an
interleaved two-identity sequence proving independent counters. Mutations for
visible counts 0 or 4..255, use of the unsaturated ordinal in a fingerprint,
failure to reset, or cross-identity/cross-phase sharing must fail closed.

## 2. Exact null RAG slot

`NULL_RAG_DOCUMENT` is exactly the JSON literal:

```json
null
```

The closed slot schema is therefore:

```text
RagSlotPublicV4 := {
  rank:0|1|2|3,
  document:RagDocumentPublicV4|null,
  score_e12:u64,
  pad:string
}
```

Every returned `slots` array has length four and slot ordinal `j` has
`rank=j`. A null slot has `document:null`, `score_e12:0`, and the exact inert
per-slot padding derived by the existing fixed-size V4 padding rule. A real
slot has a non-null document and its registered nonnegative `score_e12`; real
slots precede null slots. `NOT_FOUND` and `BLOCKED` have four null slots.
`FOUND` has one to four real slots followed by enough null slots to reach four.
No alternate null object, omitted document key, sentinel handle, empty object,
empty string, `rank:null`, or nonzero null score is legal.

Golden fixtures must include the exact JCS UTF-8 bytes and fixed-size padded
bytes for: one null slot at each rank; a four-null `NOT_FOUND`; a four-null
`BLOCKED`; and FOUND returns with one, two, three, and four real documents.
Mutations of literal type, key presence/order under JCS, rank, score, padding,
real-before-null order, or slot count must fail closed.

## 3. Successor boundary

A successor must preserve the initialized zero-attempt V7 state, bind the
fresh V7 preflight as negative evidence, and bind this advisory. It may ask a
fresh five-role deliberation only whether the already enumerated inert V8
source/spec/checker/test bytes may be authored next. It may not author or
execute them, prepare/materialize data, implement M0/M-TEXT, load a model or
tokenizer, run a benchmark, train, operate LoRA/adapters/checkpoints, parent a
child, use GPUs, acquire resources, make a scientific claim, release, or
submit.
