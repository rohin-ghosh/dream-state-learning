# Bounded independent runtime CPU review — EDITSTOP

## Final result

**43 runtime tests PASS, 8.612s, exit0.** No expected failures or skips.
The two final fixture mismatches are corrected: preparation's fake identity now
equals the normalized original AUTH child, and controller assertions inspect the
per-state worker argument while permitting the intentional shared `run` accounting
root. `formation.common.scan_text` is mocked explicitly. Tests are frozen; Main
owns the runtime and native execution decision.

Exact runtime tested (same hash before/after final run):

`/tmp/astra_birth_protocol_probe_run_20260913.py`
`4be56ece2036574b71ee3df8a609a06c04cf5011d02ed17316677b8bb0bd702c`

Owned test file:

`/tmp/test_astra_birth_protocol_probe_run_20260913.py`
`b7bdafdf0938082ab37a3379e455d5eb0b174772c4b615f8c2ef649e0f99587c`

Final CPU log:

`/tmp/astra_birth_protocol_probe_runtime_cpu_20260913_frozen.log`
`6704a7e553eeabb7fb0af1c23af56b11b62a5c093fb7438db7515683cad8b6c5`

Command (from source-root checkout; no subprocess/native backend is invoked by
the tests):

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B /tmp/test_astra_birth_protocol_probe_run_20260913.py -v
```

This is43 runtime tests, not64: Main's combined count includes the21 material tests.
No need to rerun or expand either suite on this reviewer's behalf.

## Findings and disposition

Earlier runtime bytes accepted empty/partial capture manifests, contradictory
barrier metadata, failure artifacts, changed identity file manifests, stale raw
hash receipts, negative call durations, changed usage receipts, and output text
inconsistent with output token IDs. Collection also lacked launcher-plan binding,
worker-liveness checks, and a direct-function elapsed-budget check. These were
reproduced with synthetic evidence and reported, not patched by this reviewer.

**Main's current repairs close every reproduced gap in the frozen suite:**

- Exact capture manifest coverage and hashes; no failure artifact; full backend,
  model-file and adapter-file metadata match; all32 responses before any scoring.
- Barrier OFF/AUTH/count binding; canonical raw requests and sampling settings;
  actual prepared native prompt text/input IDs and output budget validation.
- Request/response content hashes, nonnegative bounded call duration, recorded
  usage equality, existing tokenizer-based `audit_native_calls` output decoding.
- Backend close and supervisor release receipts; failed controller, live owned
  process, changed GPU UUID and mismatched launcher-plan binding reject collection.
- Direct collection over300s rejects; current CLI also wraps collection in the
  existing `formation.birth.collection_window` (read inspection, not real timer
  execution in this suite).
- Metadata archive membership and every archived member's digest verified by CPU
  roundtrip; symlinks and scanner rejection prevent archive creation.

The suite also verifies both successful fixture captures close exactly once,
controller capture-only behavior/no scoring, failed-second-worker preservation
without a barrier, explicit GPU opt-in for execution/start, worker device matching,
native prompt preparation, AUTH-only adapter binding, custody recheck, context and
lease-margin rejection, CPU log rejection, and fresh-session/offline launch flags.

## Boundaries and commands

Existing command separation remains `prepare`, `start`, internal `_launch`,
`_controller`, `_worker`, and `collect`; no automatic collection or scoring in the
controller. `command(...)` retains interpreter, `-B`, exact runtime path, root and
plan hash. The fixture launcher intercepts Popen and never creates a process.
Collection creates a metadata archive outside the root plus its validation JSON;
capture evidence, audit and release are included. No new runner/guard/framework
was authored here.

Fixtures use real pure material generation, generic capture, response validation,
native-input rendering interface, usage accounting, token/text audit, reducer and
tar/hash code with a character tokenizer and scripted responses. Fake model and
adapter names/hashes are fixtures only, never source substitutes for a native run.
Custody, GPU availability, process liveness, supervisor windows, backend creation,
and metadata scanner policy are mocked. Scanner invocation/rejection is tested;
its actual sensitivity policy is not independently audited. Native imports/model
loads, GPU, network, Git, real process launch, real cleanup timers and live captures
were not exercised. No native-runtime or scientific outcome proof is claimed.

Preserve the accepted data-review caveat: public_contract_correct is formatting-
sensitive, and instruction_compliant is reference-serialization compliance, not
a pure semantic truth measure. No data/reducer semantics were changed by this
reviewer. Preserve SOURCE_AUTHORED_PROTOCOL_PRACTICE_NOT_CLEAN and
UNRESOLVED_LOCAL_HASHES_ONLY; no induction, H1/H2/generalG3/P1 or clean-lineage claim.

Only the owned test file and this review were authored, with separate CPU logs.
Earlier logs retain intermediate fixture failures and older runtime failures;
the final pinned log above is authoritative for this bounded acceptance report.
**EDITSTOP. Main retains all launch decisions.**
