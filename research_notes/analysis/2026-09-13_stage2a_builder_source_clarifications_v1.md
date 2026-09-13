# Stage2A Builder source clarifications v1

Recorded September 13, 2026, 21:43 UTC, before scientific material generation,
tokenizer/model use, or inspection of any result from this controller assay.

## Scope and authority

These are explicit, non-material implementation decisions under Rohin's
standing authorization and latest instruction to continue with simple hygiene.
They fill finite source bindings; they do not change H1/H2, the base model,
learning locations, provenance requirements, parent visibility, controls,
exposure budgets, or claim boundaries. They create no new approval gate and
do not implement the deferred final-paper C11 guard.

Parent source contract is Stage2A-v4, SHA256
`ca528cac3505cd4d1202e1df6253213ecc167671823c39a7ae3d1a9979126dd1`,
which imports v3 and v2. This note overrides only the bindings stated below.
Implementations using them must pin this note as well as v4. Existing source
and completed experiments are preserved; no existing evidence is rescored.
All source outputs remain partial until the actual integrated checks pass.

## 1. Finite family-bit encoding

For v2 section 4.1's `u = (3*b + family_bit) mod 4`, bind:

```text
family A -> family_bit 0
family B -> family_bit 1
```

This explicit two-element encoding is selected before any generated target,
model outcome, or null-score selection. It changes no factorial cell, family
assignment, role-list count/hash, or member swap rule. Required checks: every
pair uses its assigned family bit; both members use the same u; the second
relevant candidate is at `(u+2) mod 4`; no outcome-conditioned permutation.

## 2. Intervention-directory range correction

V3 section 4.3 writes `r1=r0+12` after defining `r0=(3*k+t) mod 24`.
That can exceed 23. V2 section 9 already specifies the bounded form.
Use exactly:

```text
r0 = (3*k+t) mod 24
r1 = (r0+12) mod 24
```

This restores the preexisting 24-position route domain. All 32 (t,k) pairs
must have two distinct in-range pinned positions. Preserve each goal pin,
ascending remainder fill, and every other display/target rule. Do not rotate,
search, or retry based on observed null or model scores.

## 3. ATOM task CURRENT is the retained prefix's authentic state

V2 section 6 specifies the exact retained message sequences. For its generic
`U(task)` entries, preserve the original START and GOAL, and render CURRENT
from the recorded state immediately before the first retained actor action.
For the no-action CONTINUE prefix, use the target's recorded current-before
state as already required explicitly by the table.

This resolves the corrective PROSPECT case: its first retained action is a
READ at the observed surprise state, not the initial episode state. Using
the original CURRENT there would make the correct EVENT appear irrelevant.
For mismatch SEEK/CHECK prefixes beginning with the failed READ, use the
state before that READ; its retained WORLD message then supplies the observed
surprise. Do not substitute the later state into that earlier prefix.

CURRENT must be derived from the actual selected trace boundary, never from
target operands, predicted GOT, evaluator answers, or future turns. CLOSED
retains its original task bytes and full authentic prefix. No extra ATOM
message, task-local command, directory, hidden state, or teacher signal is
added. Required tests: both arms yield the same latest public CURRENT/GOAL
at each paired decision; retained action/response bytes are exact slices;
all discarded history stays absent; START is unchanged; future-state and
wrong-boundary mutations fail.

## Disposition

Proceed with source and synthetic CPU tests using these explicit bindings.
Record any concrete contradiction and repair it prospectively; do not hide a
failing check or treat this clarification as evidence of learning. Full source,
independent semantic checking, data construction, and runtime validation are
still unfinished. No scientific-root, model, GPU, or claim qualification is
conferred by this note.
