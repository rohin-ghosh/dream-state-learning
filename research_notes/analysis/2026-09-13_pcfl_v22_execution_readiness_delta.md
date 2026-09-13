# PCFL v2.2 execution-readiness delta

**Date:** 2026-09-13 UTC  
**Scope:** fresh committed-worktree audit after the earlier v2.2 readiness memo;
static inspection only, with no model, tokenizer, benchmark, training, adapter,
or GPU execution

## Verdict

**No prior execution blocker is closed: 0/5 closed, 5/5 still open.** The
scientific direction remains sound, but the committed repository still has no
PCFL vertical runtime or tests. The builder's `PCFLworld20CPUtestsPASS` report
is explicitly labelled a **partial fixture only, not model-ready** in
`research_loop/COORDINATION.md`; no corresponding source or receipt is present
in the committed worktree, so it does not change execution readiness.

## Delta against the five earlier blockers

| blocker | current disposition | exact current evidence |
|---|---|---|
| A. One machine-readable v2.2 source of truth | **OPEN** | No new controlling JSON/run spec exists. The unchanged prose delta still coexists with v2.1 PAD/equal-token bindings; no validator rejects those obsolete fields. |
| B. Exact score-bearing renderers/parsers | **OPEN** | No executable or bound exact renders for the zero-fit projections or 64-item retention panel, no semantic/refusal parser, literal ninth wrapper, or frozen wrong-block candidate universe was added. |
| C. Replay identities and joint batch schedule | **OPEN** | The prose defines `root_skeleton_hash`, counterpart logic, and scheduling rules, but no enumerated pre-output replay/counterpart map, support-span collision solver, sealed five-epoch assignments, or tests exist. |
| D. Literal `CAL_HIGH` trigger | **OPEN** | The unchanged v2.2 text still licenses HIGH after LOW misses any semantic, locality, canary, or refusal threshold. It does not bind the conservative rule from the readiness audit: HIGH only after a valid, safe LOW passes locality/refusal/generic canary/PCFL retention and misses EVENT/LINK acquisition. The new lower-LR evidence supports LOW-first but cannot resolve this protocol ambiguity. |
| E. Causal cuts and complete request/resource inventory | **OPEN** | No exact LINK/OLD/NEW cut map, locality address roster, updated request expansion, or profiled device-time receipt was added. The 960/1,024 retention calls and diagnostic work therefore remain outside an executable inventory. |

## Implementation check

All five paths named by the build ledger are still absent:

```text
MISSING organism_v6/pcfl_vertical_dev.py
MISSING gpu/astra_pcfl_vertical_dev.py
MISSING organism_v6/pcfl_vertical_train.py
MISSING tests/test_pcfl_vertical_dev.py
MISSING tests/test_astra_pcfl_vertical_dev.py
```

`organism_v6/train_adapter_v3.py` is byte-identical to the earlier audit
(`7bbf165f...749fad7`). It still uses generic epoch shuffling, skips nonfinite
loss batches, has no gradient clipping, and emits no per-update
loss/gradient/RNG/tensor receipt. Its newer warm-start machinery is useful
elsewhere but does not close PCFL's sealed clean-base writer contract.

## Single highest-value next closure

Build and test **one executable preparation contract**, rather than adding
another prose amendment. It should combine A--E into a single machine-readable
v2.2 run spec plus pure CPU materializer/validator that, before any native
output:

1. rejects every PAD/equal-token/v2.1-only field;
2. emits exact renderer/parser/wrapper/diagnostic bindings;
3. materializes the root skeleton, counterpart/replay/cut/address maps and
   all five sealed support-disjoint batch schedules;
4. encodes the conservative `CAL_HIGH` state machine; and
5. expands every request/update/token/device-time row and fails if the cap is
   not feasible.

This is the narrowest closure that converts the already-good scientific design
into an auditable executable input. Runtime/model code should consume its
hash-bound output rather than re-decide any score-bearing choice. Until that
contract and its CPU tests exist in the committed tree, a PCFL GPU launch would
still be scientifically underdetermined.

## Evidence cut

Audited at initial current-worktree HEAD
`d9a0baa65996a9023f71cde2730c4608b5e53def`. The controlling v2.2 repair
(`683fcba7...275dfca`) and prospective binding register
(`5d7920ea...3e0badd`) are unchanged from the earlier readiness audit.
