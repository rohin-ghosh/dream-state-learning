# Fixed-update replay-allocation scout: terminal audit

**Date:** 2026-09-12  
**Status:** independently read from the completed immutable run artifacts. No
builder source or GPU process was changed by this audit.  
**Run root:**
`/localhome/local-rohing/astra_diagnostics/astra_memory_replay_20260912_attempt1/seed0`

## Result in one minute

The seed-0 scout completed without error and released its GPU. A simple mixed
corpus retained both endpoints under its registered allocation:

| arm | memory encounters/key | dev memory | exact memory | old habit | correct action |
|---|---:|---:|---:|---:|---:|
| `MIXED` | 20 | 14/16 | 13/16 | 32/32 | 32/32 |
| `ALL_MEMORY` | 40 | 16/16 | 16/16 | 0/32 | 0/32 |

`ALL_MEMORY` produced invalid action-format responses on all 32 arithmetic
prompts. `MIXED` produced no invalid action responses on those prompts and no
invalid colour responses on either memory form.

This is useful evidence that one rank-8 adapter can *practically coexist* with
the installed PREDICT-before-ACT interface and most of the arbitrary keyed
map when old behavior is included in the update corpus. It also reproduces
the destructive memory-only failure in this seed. It is not a causal replay
test: the arms do not receive equal memory dose, equal target-token allocation,
or equal compute.

## Bound schedule and accounting

Both descendants start from the same seed-matched taught parent. `MIXED`
contains 16 memory rows and 16 arithmetic rows, trained for 20 epochs and 160
new optimizer steps. It therefore presents each binding 20 times. Its audit
reports 5,000 target-token presentations and 33,080 input-token presentations.

`ALL_MEMORY` contains only the 16 memory rows, trained for 40 epochs and 160
new optimizer steps. It presents each binding 40 times. Its audit reports
1,280 target-token presentations and 28,160 input-token presentations.

Under ordinary union-token averaging, the memory portion of the mixed corpus
has much lower objective mass than in `ALL_MEMORY`; the mixed arm also spends
most target tokens rehearsing arithmetic. Thus the exact contrast bundles
replay, memory dilution, encounter count, and target-token allocation.

## What can and cannot be said

Supported:

- at this seed and schedule, simple mixed replay retained the action interface
  while acquiring most of the 16 arbitrary bindings;
- at the same number of new optimizer steps, memory-only training acquired the
  full map and erased the installed interface; and
- the earlier apparent memory-versus-habit incompatibility is not a hard
  rank-8 capacity limit.

Not supported:

- replay is necessary or uniquely caused the retention;
- equal-memory-dose replay has no acquisition cost;
- the `13/16` exact result meets the later clean successor's `14/16` gate;
- DREAM, experiential SLEEP, conditional cognition, parenting, H1/H2, or a
  lifetime-learning claim.

The already-specified paired successor remains decisive: preserve the known
memory dose in both arms and add a separately averaged habit loss only to the
treatment, `J = L_memory + L_habit`, with paired memory RNG. Run seed 0 first.

## Execution integrity

The terminal record reports `status=COMPLETE`, `error=null`,
`deadline_met=true`, no outcome-selective skips, and verified reservation/GPU
release. Total controller reservation was 954.34 seconds; supervised worker
windows used 722.44 seconds. The run's own claim label is appropriately
limited to `FIXED_UPDATE_REPLAY_ALLOCATION_NOT_EQUAL_MEMORY_DOSE_OR_COMPUTE`.

