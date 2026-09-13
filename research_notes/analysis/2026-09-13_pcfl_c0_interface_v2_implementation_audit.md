# PCFL C0 interface v2 implementation audit

**Date:** 2026-09-13  
**Role:** fresh read-only implementation auditor  
**Normative contract:**
`research_notes/analysis/2026-09-13_pcfl_c0_dev_interface_repair_v2_closure.md`
(`df6565ff`)  
**Verdict:** **STOP BEFORE EVERY NATIVE MODEL CALL.** The present source is a
useful partial controller prototype, but it does not implement the closed v2
experiment. Passing its current CPU tests would not qualify A1 or any later
rung.

No builder-owned file was edited, no model/tokenizer was loaded, and no GPU or
scientific run was executed in this audit.

## 1. Authoritative snapshot inspected

Read-only inspection used the helper VM worktree at 2026-09-13T15:06Z. The
interface command/outer files and their tests were untracked there; the DEV
driver was present. Exact file hashes:

| file | SHA-256 |
|---|---|
| `gpu/astra_pcfl_interface_dev.py` | `e31d9ee43705c3eb2754bcc8085ed5d739771acea15e13fda4dfe19b0dc26f10` |
| `gpu/astra_pcfl_interface_command.py` | `2aefc08d7404622573d601f7aca5e6e6767c8a70a26c095092b472da18b475ab` |
| `gpu/astra_pcfl_interface_outer.py` | `232f61c345363a1996271647e9bd12a5482dc729e6131c4c883bf6136ffd0c63` |
| `tests/test_astra_pcfl_interface_dev.py` | `8d0628385c225f67250361886a81ac62562e62264e0b4f1ce34cecf97a84dabb` |
| `tests/test_astra_pcfl_interface_command.py` | `a4389f698f31bcbbe34efe208dca043f86a7cfd787aca277148880a47be95962` |
| `tests/test_astra_pcfl_interface_outer.py` | `442546d4c192a5ff288e7cea8ec0d035e15ed2a41de3f90cfed86d4fd886ea90` |

The audit also inspected the invoked READ/ROUTE/PROBE grammars, graph scorer,
task renderer, query materializer, and service dispatcher in
`organism_v6/pcfl_vertical_dev.py`.

## 2. What is already sound

The partial implementation preserves several important v2 properties:

- C0 is clean-base only and the actor binding rejects a LoRA mount.
- A1/A2/A3 use the same 64 excluded-root task cells; A2/A3 share user task,
  case identity, seed, and exact graph material.
- The public prompt discloses all three READ forms, and READ dispatch uses the
  existing full-match grammar.
- Registered reads return exact registered row blocks including terminal LF;
  valid unregistered reads return exact `MISS`.
- Raw generations, token IDs, prompt render, capture files, chronology, and
  source/model identity are joined and replay-validated.
- Sixth THINK and twelfth READ are legal; seventh/thirteenth fail. Actor and
  returned-token caps do not trigger a forced answer.
- A live builder revision during this audit repaired all-whitespace THINK
  acceptance and added same-task current-rung gates, including the frozen
  56/64 overlap counterexample and served-READ-then-failure cases.
- Fences, multiline commands, trailing LF, repaired routes, and semantic
  rescue are not accepted.
- Lifecycle code requires a fresh output, offline local model, clean C0 load,
  verified owned-process shutdown, and post-run GPU/CVD release.

These are worthwhile building blocks. They do not overcome the blockers
below.

## 3. Native-call blockers

### B1 — the frozen continuation bytes differ

Contract section 2 freezes:

```text
CONTINUE: think again, issue one permitted READ if reads are enabled, or commit the final action.
```

The implementation instead defines at DEV line 22:

```text
CONTINUE: follow the declared turn budgets and commit the final action when ready.
```

This changes the intervention being tested. Replace it exactly and bind its
UTF-8 hash before A1.

### B2 — current-rung joint gating is repaired, but the required reducer
contract is still incomplete

DEV lines 212--235 now compute same-task handshake, thought+route, and
thought+read+route counts. The accompanying tests correctly reject the 56/64
marginal-overlap counterexample and a served READ followed by task failure.
That removes the earlier functional joint-gate defect for the four prototype
stages.

The physical per-task record still does not explicitly compute or store the
v2 fields:

- `invalid_turn` and `cap_failure`;
- `interface_complete`;
- `think_route_success`; and
- `registered_nonmiss_read`.

Those fields, rather than reason-string reconstruction, must drive every
downstream delayed/reachout gate and be present in the immutable task record.
The complete panel reducer, donor-ID checks, RA/RB strata, alias map, and
confirmation dispositions remain absent.

### B3 — exact terminal text is rejected merely because finish reason is
`length`

DEV lines 275--277 reject every response whose backend finish reason is not
`stop` before parsing it; the corresponding DEV test enshrines that
behavior. V2 dispatches the complete decoded bytes after receipt and expressly
allows a valid terminal response to exhaust the actor budget. A strict exact
ROUTE/PROBE that ends exactly on the requested token cap must be scored;
nonterminal/truncated output still fails through the grammar or exhaustion
rules. The finish receipt remains logged, not an extra semantic gate.

### B4 — READ delivery does not prospectively test the next rendered context

DEV lines 285--295 check only the 4,096 returned-token cap, mark the block
delivered, and append it. Context overflow is discovered only before the next
generation. V2 requires checking the complete candidate conversation first
and failing **without appending/delivering** the service response if that
response would make the next render overflow. Add boundary fixtures for both
returned-token and rendered-context limits.

### B5 — an extra 14,336-token input cap is not in the v2 controller

DEV lines 100--101 and 246 plus command lines 68--69/104 impose a separate
`input_tokens <= 14336` rule in addition to
`input_tokens + requested_headroom <= max_model_len`. V2 specifies the latter
frozen model-context check, not this lower independent failure surface. Remove
the extra cap or obtain a successor closure that explicitly freezes it; it
cannot silently change which histories are executable.

### B6 — most of the required pre-A1 experiment does not exist

`STAGES` contains only A1, A2, A3, and a generic `ACTIVE_THINK`. The current
tests explicitly require `A4_SCAFFOLD` to be rejected. Missing before A1 are:

- the prebound neutral A4 scaffold and its namespace/nonmembership proof;
- conditional A4 eligibility and A3/A4 terminal selection;
- both complete A3- and A4-selected downstream prompt catalogs;
- delayed EXACT/FULL/EVENT/ACTIVE/NATIVE/OLD/NEW/NONE/WRONG panels;
- direct and active reachout panels with exact PROBE handling;
- the order-only, no-ordinal, equal-token-length RA/RB template;
- four blinded confirmation roots, generator/allocation commitments,
  disjointness proofs, and immutable release capsule;
- FULL/NATIVE byte-equality proof and physical-call alias map; and
- the named terminal dispositions and roots-burned behavior.

V2 deliberately requires these materials to be generated and hash-bound
**before the first A1 call**, so A1 cannot be run as an isolated preliminary
stage under this closure.

### B7 — the execution topology and budgets are stage-local rather than the
frozen P00--P09 partitions

The outer/command code launches one fresh stage with a 3,600-second allowance.
V2 binds A1+A2+A3 together as P00 (1,344 slots total, 3,600 seconds), A4 alone
as conditional P01 (448 slots, 1,800 seconds), and P02--P09 with exact unique
registries and alias arithmetic. The present code could give A1, A2, and A3 a
separate hour each and has no cross-stage predecessor/disposition check.

Implement one command per frozen partition, exact
13,952-logical/13,056-unique maximum accounting, explicit `NOT_REACHED`
reasons, conditional P01 prohibition/selection, and no restart/replay of a
completed task. Require `actor.max_calls == len(unique_call_slot_registry) <=
1952`, not merely `>= possible_calls`.

### B8 — required records and boundary tests are incomplete

The result schema has no explicit generation counter, terminal state/family,
invalid-turn flag, cap-failure flag, joint gates, root start/goal check,
relevant-Q result, donor-ID use, logical aliases, or confirmation commitments.
No code handles PROBE terminal tasks. Tests do not cover every counter at
cap-1/cap/cap+1, A4 eligibility/skip, the overlap counterexample, FULL/NATIVE
aliasing, RA/RB 16/0 rejection, predecessor refusal, or confirmation root
burning. These are acceptance requirements, not optional diagnostics.

## 4. Exact disposition

**`STOP_TYPED_INTERFACE_IMPLEMENTATION_NOT_V2`** (audit label, not a new
scientific terminal label).

Do not issue A1, A2, A3, A4, panel, or confirmation native model calls from
these file hashes. The minimal repair order is:

1. fix exact per-turn semantics (B1, B3--B5) and their boundary tests;
2. implement the combined same-task reducer and v2 records;
3. materialize the entire pre-A1 A3/A4 and confirmation catalogs;
4. implement P00--P09 orchestration, aliasing, conditional selection, and
   terminal dispositions; then
5. run the full CPU preparation/checklist from closure section 11 against the
   final source hashes.

Only a clean receipt covering all five items makes the first native A1 call
scientifically admissible. This stop is narrow: it does not block the separate
EVENT-only write localizer, whose claims and source path remain independent.
