# Fresh source-readiness audit: TWO-SLEEP-JUNCTION-v4

**Date:** 2026-09-13 PT

**Role:** fresh adversarial source-readiness reviewer

**Object:** commit `ca1cc8fab8c65477459033d93eca5fcab764fe8b`, file
`research_notes/analysis/2026-09-13_two_sleep_own_experience_junction_source_contract_v4.md`,
verified SHA-256
`57cdeb290573acb4edf68a1a4c1cbf12ae64eee6f0dc31730cc264cc79ae848a`.

**Basis:** the v3 fresh audit and the exact TSJ-v3/M-COMBINE-v2 imports named
by v4. This was a documentation/repository audit only. I did not edit
scientific source, materialize identifiers or a root, invoke a tokenizer or
model, train or mount an adapter, inspect a worker, or use a GPU.

## Verdict

**GO_CPU_SOURCE after adoption of the exact v4 bytes.**

```text
REWORK_TSJ_V4  = FALSE
GO_CPU_SOURCE  = TRUE_AFTER_ADOPTION
GO_PREPARE     = FALSE_PENDING_TWO_CPU_IMPLEMENTATIONS_AND_SOURCE_AUDIT
GO_MATERIALIZE = FALSE
GO_TOKENIZER   = FALSE_EXCEPT_UNDER_LATER_GO_PREPARE
GO_MODEL       = FALSE
GO_FIT_OR_GPU  = FALSE
GO_CLAIM       = FALSE
```

V4 closes P0.A--P0.E without changing the paired XOR estimand or weakening a
gate. A CPU author can now implement dummy-ID/fake-tokenizer generators,
schemas, ledgers, solvers and two independent checkers without choosing
scientific semantics in code. This verdict is not the later fresh audit of
those as-yet-unwritten source bytes and grants no preparation or execution.

## P0.A--P0.E verification

| blocker | result | verification |
|---|---|---|
| P0.A invariant slots/hashes | **PASS** | Slots 00--15 are semantic and pre-transform. Every compiled arm orders by repeat, view, integer slot; row hashes are receipts, never sort keys. AUTH/treatment/address/provenance hashes are mandatory per slot. RAW explicitly retains its separate solved assignment and makes no paired-dropout claim. |
| P0.B fillers/islands | **PASS** | i0--i3 and IL0/IL1 are exact. AF0--AF5 give a total four-link S1/six-link S2 ATOM map with fixed request addresses, parents, reuse and provenance. CB0 is the sole equal-byte cut block; MF0 is the sole OLD_FILLER replacement for slots 12--15. The superseded unnamed pools are expressly removed. |
| P0.C sole ledger/gates | **PASS** | P10/P50 ATOM are gates, matching the generated truth predicates. P05 imports a zero-call BIRTH subset baseline. P31/P71 now bind every denominator, absolute minimum, per-metric BIRTH-minus-one rule, call order, alias and EMPTY-slot behavior. No new model row is introduced. |
| P0.D GO_PREPARE | **PASS** | CPU source/checker work is authorized first. Only after two implementations and a fresh source audit may one sealed deterministic CPU root plus the pinned tokenizer produce hashes, scans, RAW witness and batch/FLOP receipts. Model weights, child calls, formation, scoring, adapters, optimization, CUDA/GPU and alternate roots remain forbidden. |
| P0.E literal pins | **PASS** | The six disjoint anchored byte regexes close THINK and command parsing. Four exact invalid request bytes and the 4,096-per-kind reserved inventory are fixed. World/stage/stream encodings, digest slice and endian conversion connect the literal writer seeds to all streams. `imported_parameter_count` and `FLOP_STOP` are defined as a stopping proxy, not profiler identity or feasibility evidence. |

## Cross-checks and regenerated caps

The semantic-slot tapes retain exactly 12 S1 and 16 S2 memory units. Filler
replacement changes neither presentations nor updates. P05 is receipt import
only, ATOM changes role from diagnostic to gate without adding a rollout, and
preservation canaries remain aliases. Therefore the canonical roster remains:

```text
route rollouts/world       12 + 18 + 16 + 22 = 68
actor calls/world          68 * 22 = 1,496
native reader calls        (16 + 18) * 10 = 340
cold/canary calls          7 * 60 + 6 * 70 = 840
formation calls            20 + 6 = 26
incremental preservation   2 * (32 + 8 * 29) = 528
model calls/world          1,496 + 340 + 840 + 26 + 528 = 3,230
model calls/pair           6,460
```

The output-token arithmetic also reproduces:

```text
actor                       68 * 4,096 = 278,528
route reader                    340 * 160 = 54,400
cold/canary                                  154,368
formation                                       2,880
incremental preservation                       81,920
generated tokens/world                        572,096
generated tokens/pair                       1,144,192
```

Fit and training maxima remain internally consistent:

```text
fits                         13/world, 26/pair
D1                           24,656 updates; 98,624 presentations/pair
D2                           31,312 updates; 125,248 presentations/pair
D1 max padded tokens         98,624 * 16,384 = 1,615,855,616
D2 max padded tokens        125,248 * 16,384 = 2,052,063,232
```

The 248 GPU-hour and 72-hour limits are correctly labeled hard stops rather
than feasibility claims. The exact tokenizer witness will give lower actual
padded-token work under GO_PREPARE; it cannot increase these maxima.

## No new blocking contradiction found

The following remain prospective fail-closed outcomes, not source gaps:

- upstream BIRTH or its reduced imported subset may fail its bound gates;
- concrete IDs may fail token-length, overlap, per-slot padding or transform
  equality;
- the whole-unit RAW integer program may be UNSAT;
- supplied/active/ATOM ceilings, authentic formation, native writes,
  controller preservation or root-local causal controls may fail; and
- the hard FLOP/GPU/wall/resource stops may make execution infeasible.

Each outcome stops the fixed version without reseeding, replacement, dropped
controls, denominator change or claim rescue. Private CP support rows are
explicitly non-presented control provenance; AF0--AF5 alone occupy the ATOM
memory LINK slots, so they do not silently increase the 12/16 presentation
counts. Cut-address MISS behavior and MF0 addresses are likewise explicit.

## Gate boundary

This audit opens only the source/checker phase described by v4 Section 7 after
the repository records adoption of these exact bytes. It does not itself
assert that two independent implementations exist or pass. `GO_PREPARE`
requires their exact source/test/spec hashes, CPU receipts, mutation tests and
a new independent source audit. Scientific model calls, fits, GPUs and claims
remain closed after preparation until their separately stated gates and
explicit opening are satisfied.
