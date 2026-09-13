# PCFL v2.2 runtime — early interface binding (2026-09-13)

Implementation in progress; CPU/scripted path only. No model/tokenizer/profile
measurement, native readiness, scientific pass, or launch authorization.

## Minimal assembly API

`gpu.astra_pcfl_vertical_dev.Runtime(contract, backend, ..., scripted=False)`
will consume the preparer's detached sealed JSON. Loaded core/preparer APIs
remain module attributes, never keys in scientific registry/data objects.
The default path fails closed on the preparer's unresolved execution evidence;
an explicit scripted backend runs CPU tests, never authentic native evidence.

`run_initial()` orders construct -> all 800 four-excluded-root zero-fit tasks
(640 delayed + 160 reachout, including deterministic text READ service) ->
disposable exact-child formation -> CAL_LOW fit/readout boundary. No DEV fits
or later stages are callable through this initial implementation. Full DAG,
v2.2 budgets and conditional CAL_HIGH rule are reported, not declared executed.

Backend generation API: `generate(request, limits)` returns exact text, prompt
and output token counts, elapsed A40-device seconds and request identity. The
request contains public messages only, never private world/oracle or ideal
training rows. Limits include remaining task/stage/device-time ceilings.
`close()` must return an owned-process release receipt even on exceptions.
Backend calls are injected; runtime has no subprocess/model-loading path.

Main must bind every concrete runtime request/render and its stage/item/seed/
mount/work-row IDs before generation, including adaptive public-history render
templates and all actor continuation/lookup slots. No post-output slot choice,
parser change, smaller denominator, or retry is permitted. Current preparer
work rows do not yet supply a complete runtime expansion; native release stays
blocked, rather than treating test schedules as prepared native contracts.

Core owns public world/session/admission/scoring; prepare owns exact banks,
replay and batches; train owns the 200-update response-only writer. Runtime
must independently run the public CPU scorer on scripted raw outputs, replay
actual world receipts, and reject CEILING_FIXTURE/CONTROL rows in CAL AUTH.
No generic old training wrapper is compatible with the writer contract.

## Current dependency gaps

Preparer currently reports `execution_contract_valid=False` and named missing
interfaces even for its validated bridge. Core reports only partial construct
certification. Train module/handoff is not present at this interface cut.
An explicit synthetic test mode is not a waiver of these gates. Main retains
native process/lease/profile/tokenizer verification and final assembly.

PCFL is substrate/own-experience-chain work, not parenting, amortization,
H1/H2, or mission completion. Matched parent removal remains separate.

---

## Author handoff / EDITSTOP — implemented boundary

The final interface below supersedes the prospective description above.
Only the two assigned repository paths and this handoff were written. Local
Git status/HEAD were read; no pull/network, staging, commit, push, model/native
operation, download, collector, process launch, or manuscript edit occurred.
Main's concurrently advancing HEAD was `f15dec6c` at final status inspection.
The unrelated dirty rules file and all concurrent component files were left
untouched. The final rules observation was SHA256
`2c82a32c5e52d5f8b4fa34714b9388cc29d011da9505816613466501dd133e07`;
this is an observation, not a claim that others cannot subsequently edit it.

### What executes

- `prepare_scripted_plan(contract)` expands exactly 640 delayed and 160
  reachout task slots over all four excluded roots, before any output. It
  creates a **SCRIPTED_TEST_ONLY** plan, not a production execution contract.
  Actor seeds, renderer, strict parser, shared budgets and control thresholds
  are fixed before outputs; there are no outcome-selected retry slots.
- `Runtime(contract, backend, scripted=True, clock=..., deadline=...,
  profile_receipts=...).run_initial(formation=None)` calls the actual public
  core construct audit and exact route/probe scorers. The construct report
  remains partial, not a certified production construct. All 800 scored task
  denominators remain fixed; a resource failure retains missing tasks rather
  than reducing denominators. Panels and raw records are returned in memory.
- ACTIVE_LINKED_TEXT performs real CPU `read_query` lookups, preserving exact
  returned bytes and source hashes. No memory-model call occurs. It enforces
  cumulative 12 reads, 2,048 actor tokens and 4,096 returned tokens per task;
  there is one terminal commitment and no intermediate ROUTE feedback.
  WRONG_ROOT false-row checks use the actual `score_memory_response` API,
  not just an incorrect-route count. Reachout fixtures expose OLD memory only.
- Passing scripted ceilings yields `AWAITING_DISPOSABLE_EXACT_CHILD_SPANS`.
  If a supplied subsequent formation bundle is present, `audit_formation`
  replays its 8 EXPLORE / 8 EVENT / 4 LINK opportunities through the real
  `WorldSession`, strict admitters and required-bank formation report, then
  the real preparer `validate_formation_binding`. Source SHA, exact UTF-8
  bounds, temporal order, action/author prompt hashes, chronological handles,
  support and frozen fields must agree. No ideal/control row is substituted.
- Passing that replay yields **`CAL_LOW_BINDING_REQUIRED`**, not a fit or a
  writer qualification. It emits corpus/source identity, LR `3e-5`, clean C0,
  200 updates, 1,800s fit cap and 3,600s readout cap. It does **not** call the
  writer. `fits_executed=updates_executed=0` is invariant here. CAL and all
  downstream DEV stages are explicitly `NOT_IMPLEMENTED`, never marked done.

The stage DAG includes optional HIGH only after valid, safe LOW acquisition
failure, then DEV OLD, four S1 fits/root, readout, gated reachout, R0/R1 NEW,
three S2 fits/root, readout, seal/reduce. Tests exercise the preparer's actual
conservative `calibration_transition`; no local alternative HIGH selector
exists. The report carries frozen cuts/work-registry hash, missing expansion,
and separate budget ceilings. v2.2 campaign ceilings are 15/16 fits and
3,000/3,200 updates; 19/20 A40-hours are protocol upper bounds, not measured
runtime or a claim that this incomplete executor consumes the full campaign.

### Exact backend and receipt interfaces

Backend is injected and lazy; constructing it must not acquire resources.
`scripted` must be the Boolean `True`. Methods:

```text
generate(request, limits) -> {
  request_sha256, text, prompt_tokens, output_tokens, device_seconds
}
count_tokens(text) -> nonnegative integer
close() -> {owned_group_released: bool, gpu_vacant: bool, ...}
```

Requests contain only opaque request ID, public messages, seed and C0 mount;
no private cell, oracle, scorer, candidate answer, or service registry is
passed to `generate`. Limits carry remaining actor/returned/read allowance,
deadline and remaining aggregate device seconds. These backend-reported
counts and release fields are **synthetic test receipts**, not authenticated
tokenizer/hardware measurements. Cleanup runs in `finally`, including failed
calls and stage errors. Failed calls retain their attempt and mark unknown
device cost; failed release overrides success without erasing prior status.
Each driver is single-use, with no retry or recollection entry point.

Formation bundle keys are `contract_sha256`, `root` (`disposable/0`), `corpus`,
and `generations` (exactly 20 ordered records). Each generation record has
`id`, `kind`, `raw`, `sha256`, `span=[byte_start,byte_end]`, `started`, `ended`,
and `prompt_sha256`. Original payloads and separate exact span bindings are
retained. This is byte/support replay, **not native capture authentication**;
all reports retain `native_custody_verified=False`. Rows with extracted spans
must have their full-generation provenance bound by Main before writer use;
the runtime does not invent `CHILD_NATIVE` or capture receipts. The writer's
native payload schema is intentionally not fabricated from these test records.

### Production blockers / no implicit promotion

1. The latest laptop audit is
   `research_notes/analysis/2026-09-13_pcfl_distractor_and_opaque_id_production_bindings.md`
   (SHA256 `bcdae11f3eb5c0653b842f16bbf5ba1e34cc5ffdbdc62689aca1ce2ca0f6eecf`).
   Production D endpoints/outcomes/transition and relevant public-result bytes
   are unresolved. The runtime does not fill them. New core defaults reject
   these production paths. Only `prepare_scripted_plan` passes the core's
   explicit `fixture_only=True`; the resulting plan is never native-ready.
2. `scripted=False` always fails closed, even with a claimed-green validator.
   There is no native CLI, process/LoRA loader or GPU dispatch. The preparer
   still reports `execution_contract_valid=False` and missing closure seams.
3. Complete per-request/render/profile/tokenizer/input-cap/cold-load and
   continuation-slot expansion is not supplied by this synthetic plan. Its
   stable test seeds/reachout service instruction are not approved production
   bindings. Full shortcut/false-choice certification is also outstanding.
4. Disposable formation generation dispatch, real capture custody and writer
   assembly are not implemented. The worker consumes already-supplied spans;
   the 20 replayed generation receipts are not 20 new runtime model calls.
5. CAL fit/readout and all subsequent DEV stages are unimplemented. Main must
   bind the writer objective/layout, native C0 state, seeds, masks, source
   captures, exact batches and complete readout roster, plus process/lease
   and actual profile/tokenizer evidence. The existing L2 loader/controller
   patterns were inspected but not reused as an incompatible hidden loader;
   generic old training/shuffle/PAD semantics were not imported.

This is a tested initial **scripted execution and custody-replay boundary**,
not a completed native runtime. Do not use its fixture success as a scientific
gate, production binding, author training source, or permission to launch.

### Validation

Command actually run:

```text
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest tests.test_astra_pcfl_vertical_dev -q
Ran 22 tests in 14.116s — OK
```

Tests use scripted generations and mocked process-release receipts only.
The 800-task end-to-end path executes unmocked public route/probe scorers;
the service and false-row tests execute unmocked public lookup/memory scorers.
Formation tests execute unmocked admissions, required-bank and formation-bank
validation. Most fixtures explicitly mock the preparer's full-contract
validation because they are deliberately partial. A separate test uses the
preparer worker's synthetic fixture and **unmocked** build/validate bridge;
another proves the real validator rejects the partial fixture before calls.
No test result asserts native readiness. Loaded modules `core_api` and
`prepare_api` never occupy data-registry keys (the additive module/dict
overwrite failure is specifically regression-tested).

Additional checks: Python AST parsing and direct trailing-whitespace checks
pass for both owned files. Read-only `git diff --check` passed, but these new
files are untracked, so the direct checks—not that Git command—cover them.
No PDF/build/install or source-model hash work was performed.

### File-byte pins for review

Owned files:

- `gpu/astra_pcfl_vertical_dev.py`:
  `026c6a8c50f551d874a605e1975f5fe2189643fcbd5e6694c0ad2d2fea0544b1`
- `tests/test_astra_pcfl_vertical_dev.py`:
  `5a5e81688d2c9598d6cbc9d1e285b10d7258589e9d358ea509475b19fbf12af5`

Observed concurrent dependency versions (not ownership/freeze assertions):

- core `03cc4fea5f606f223c15289b4cc86db9f9534bcddb5d3f298b39a0b06b09ab4f`
- preparer `e80266c4241116dc5701f8a394590645229ca089318903545ad064a1835e26a4`
- writer `ba4446e211c7606ce8ccbb29598f9a007412ef0dc3c716c886415c1c364dd436`
- core registries canonical digest:
  `caceddbaab84390196b8d1b219062440a4e7b49e640665b463f1bf83a43e8f03`

Core/preparer APIs changed during work; tests were rerun after adopting the
required-bank formation gate and explicit fixture-only render flags. Main
should rerun the scoped test command after any further dependency change.
