# PERSIST-CODE — terminal L1 screen, 2026-09-14

Status: **DEALLOCATED after completed negative screen.** Main owns the ordered
result SEQ and board/state update; no SEQ pre-reserved. A1004–5 released.

## Observation and evidence

| Same eight L1 tasks | RICH | TERSE | Fixed `sum(values)` reference |
|---|---:|---:|---:|
| Entire task's 16 tests pass | **0/8** | **2/8** | **0/8** |
| Native calls | 40 | 35 | 0 |
| Own records written | 0 | 2 | 0 |
| Oracle-error → changed successful repair → own record | 0 | 1 | 0 |
| Generated tokens | 12,831 | 976 | 0 |

TERSE successes are ledger_004 and ledger_006. All earlier accepted functions
remain regression-green. Both arms start/end at verified37ec with unchanged
frozen base, zero updates/fits. Maximum observed prompts320 RICH/499 TERSE;
generated176–512 RICH/21–39 TERSE, within1536+512 caps. Equal ceilings are
**not equal realized compute**. Rich generation used about13 times the tokens.

CPU receipt replay independently recomputes all oracle feedback, successful
functions and stored-record hashes/bytes, task roster, call counts, token caps,
source hashes, prefix/scaffold separation, and state receipts: PASS both arms.
This is an author-side deterministic replay, not an external reader verdict.
Prospective rich>terse survival gate fails. Zero rich targets admitted; no fit.

## Interpretation and falsification

The bounded protocol does **not** show rich-prompted persistence improves
success or yields usable rich trajectories. It does not disprove persistent
learning: RICH created no successful function/record, so the intended reuse
mechanism was never exercised there. No weights changed; no sleep comparison,
parent-removal transfer, retention battery, or H1/H2 result is claimed.

The dominant observed obstacle is interface comprehension and grounded
articulation, not lack of GPU capacity. RICH produced28 invalid/missing JSON
actions and3 truncations; only9 parsed actions, all outcome-failing. Whole-text
diagnostic review of first/last turns in all8 episodes (16/40) finds recurring
confusion between empty self-record memory and the unknown task input, false
feedback diagnoses, and invented arithmetic. Remaining24 semantic labels stay
UNREVIEWED, never silently PASS. See the separate bound semantic review.

Strongest concrete record finding: TERSE's successful ledger_006 repair passes
16 tests, but its subsequent own-record recipe returns12 instead of27 on the
same task's `[-5,-4,-3]`. Event provenance and task success do not guarantee
record correctness. The other record remains valid on its originating tests.

Attempted falsification of a pure namespace explanation: posthoc CPU-only
replacement of `xs` with `values` in parsed recorded expressions rescues one
RICH task and two additional TERSE tasks. No raw target was changed. Namespace
ambiguity contributes but does not establish that the full gap is superficial.

## Assumptions and next compute

- Selected exposed-DEV37ec, one deterministic greedy realization, small toy
  integer-pipeline family; not a clean birth lineage or untouched transfer set.
- Append-only functions share helper semantics and self-records, not a full
  mutable multi-module repository. Existing accepted functions are not callable
  by later tasks. The screen cannot isolate records from prompting/inference.
- General function input `values`, helper-doc placeholder `xs`, and the empty
  record list are plausibly confusable. This is a genuine interface limitation
  in this protocol, not permission to reinterpret failed native outputs.
- Stop/deallocate both slots; no larger corpus/fit or repeated identical run.
  Cheapest new discriminating hypothesis: explicitly separated function-input
  and memory namespaces, crossed with record-visible versus record-cleared
  replay. Preregister a small same-family follow-up before any new GPU use;
  do not treat this proposal as an admitted run or a persistence benefit.
- Future learning comparison remains guided+sleep vs frozen twin AND
  unparented+sleep, with parent-free evaluation. Autonomous collection is not
  a prerequisite. Consolidation remains the same child prompted from its own
  experience; no elaborate compiler was built.

L2proposal `structured-text-ledger-v1` and heldL3proposal
`dependency-build-graph-v1` remain unimplemented/unmined pending Rohin.

## Operations and peer message

Native attempt2 source `47515604d0b81a44458cbbabf0e029671f6e0ab1`;
preGPU `228bb902`; guards154288/154289, native154363/154360. RICH finished
22:22:33Z; TERSE22:13:22Z; both guardian exit0 and release-CVD scan clear.
All four owned PIDs absent and GPU4/5 physically0MiB with no compute apps at
22:23:03Z. No kill or lease change. Attempt2 guarded assigned wall time
787GPU-seconds =0.2186GPU-hours; preserved attempt1 failed-accounting overhead
99GPU-seconds =0.0275GPU-hours; combined **0.2461GPU-hours**. These are wall
allocations, not measured GPU utilization. Attempt1's2calls are excluded from
the75-call comparison, retained as infrastructure failure, not scientific null.

Peer message: **check the child's lesson itself against its successful event;
do not admit it from success/provenance alone. Separate self-record memory
from formal function inputs in the interface.** Off-the-shelf collectors were
never blocked by this worker; no other GPU or peer source was changed.

Evidence root: `research_notes/analysis/orch_persist_code_20260914_attempt2/`.
Terminal capsule SHA256:
`33a9421ce15d494d1b3b792a01ea1ad9dd988ae98db9c73aec3c9e43f3c44940`.
`REDUCTION.json`, `POSTHOC_ALIAS_DIAGNOSTIC.json`, `terminal.tar.gz` and expanded
`terminal/{RICH,TERSE}/` preserve exact receipts. Remote identical evidence:
`/localhome/local-rohing/data/orch_persist_code_20260914_attempt2`.
Attempt1 terminal capsule841e44d4472959a2 and old source/preflight remain intact.
