# Node2 already-applied-wall compatibility candidate

September 19, 2026. **Non-material compatibility repair; isolated, CPU-tested,
uninstalled, and not launch-ready.** All new/changed files are inside this
directory. The historical `post_recovery_node2_sleep_20260919/runtime_candidate/`,
shared restart contract, receiving source snapshots, live files, guards,
deadlines, partial intents and MathB work are untouched. No GPU, restart, remote
mutation, commit or push was performed.

## Exact behavior

This copy accepts only the two observed original plan byte strings captured in
`fixtures/OBSERVED_PLANS.json`: C0 (8,921 bytes) and Astra7 (8,808 bytes). Each life
has an immutable raw-plan SHA-256 and canonical authorization SHA-256 pin in
`interrupted_sleep.py`. It rejects missing/null/deleted authorizations, changed
authorizations even with the same final bound, new extensions, and any changed
plan bytes, including whitespace. Unlike the earlier general proposal, this
assigned candidate deliberately has **no legacy null-authorization fallback**;
the original historical candidate is unchanged.

`applied_wall_validation.py` contains the exact original receiving journal's
`validate_wall_extension` function. A test compares its source text against both
hash-pinned receiving copies. Actual copied-kernel preparation and execution
both call that validator, in addition to checking the exact observed hashes.
There is no permissive alternate schema or deletion of an authorization field.

- Existing authorization, plan and retained state must already specify final
  bound **1789927200 = September 20, 2026, 18:00 UTC**. The observed lease end
  stays 1789980180; its 21600-second safety margin is unchanged.
- The untouched V2 contract authenticates durable COMPLETE and pending state
  and requires both deadlines to equal the plan's final bound. Runtime execution
  rechecks the immutable plan/authorization pins and pending deadline, even if
  a caller supplies a newly hashed candidate envelope.
- Raw plan bytes, the authorization dictionary, history, working state, rows,
  recipe, old-head binding and stable attempt identity are retained. The child
  receives the original plan with its authorization still present.
- This recognizes existing applied state only. It neither calls
  `prepare_wall_extension` nor emits a new `WALL_EXTENDED`. Compatibility metadata
  records both pins and explicitly says `authorization_reapplied=false` and
  `new_extension_event=false`.
- Whole-pending-sleep restart behavior is otherwise unchanged: 48 new, separately
  accounted CPU-fixture updates; C0 counter 8412→8460, Astra7 counter 9644→9692.
  Old unsaved UPDATE receipts are not erased or reused. There is no claim to
  recover unsaved resident RNG, exact resident continuity or identical weights.

## CPU evidence

**99/99 tests passed**, revalidated September 19, 2026, **14:08:57 UTC**:

| Suite | Tests | Result |
|---|---:|---|
| Copied existing runtime regressions | 39 | PASS |
| New observed-wall tests, including actual execution | 20 | PASS |
| Untouched historical V2 contract | 18 | PASS |
| Untouched historical strict replay | 22 | PASS |

Authoritative current receipts:

- `TEST_RECEIPT_1789826937405021103.json`
- `TEST_OUTPUT_1789826937405021103.txt`

The earlier 98-test iteration and first 99-test receipt/output are retained, not
added to the current 99-test count. All runs verified pinned historical candidate
files, contracts, tests and inventory before and after. The latest run also binds every
copied Python source, raw-plan fixture and original receiving source hash; none
changed during testing.

Run from the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B research_loop/workers/replication_sprint_20260919/evidence/node2_recovery/runtime_repair/run_cpu_tests.py
```

The runner has a 120-second bound per suite and writes exclusive receipts and
temporary fixtures only here. No installed runtime or admission code is invoked.

New tests exercise the actual copied `prepare_candidate` and
`finish_interrupted_sleep`, not just a stand-alone compatibility contract:

- Both exact plans complete a synthetic pending sleep with all old state/files
  preserved, original validator calls observed, and an extension-helper trap
  never called; no additional wall event or paired driver LEARN is published.
- Re-signed candidate/contract envelopes cannot authorize modified plan bytes,
  a new authorization/deadline, field deletion, the other life's plan, a changed
  compatibility receipt or a changed pending deadline. Rejection precedes child
  construction, attempt creation and journal publication.
- Changed but re-authenticated COMPLETE/pending deadlines still fail the
  original V2 equality check. Expiration still blocks; no deadline is extended.
- Astra7's exact plan passes compatibility, but execution wired to the original
  physical journal auditor still rejects a zero-byte 7808 intent partial. The
  synthetic partial's pathname, inode, bytes and hash remain unchanged.

## Evidence limits

Only the **raw plan bytes** are captured operational inputs. Checkpoint payloads,
rows, records, working state and the training child in these tests are synthetic
CPU fixtures. The journal state transitions and stream restore checks use
hash-pinned original source. A test-only mapping of `candidate.Path` redirects
the exact original root to a temporary receiving-fixture root without rewriting
the plan. That mapping is **not** part of runtime code or a deployment change.

No real checkpoint tensors were loaded, no real full journal was scanned and no
historical `WALL_EXTENDED` event was located. The positive fixture validates
preservation of the synthetic old prefix, **not** the existence/identity of that
real historical event. Authenticating an observed plan is not a substitute for
checking its applied authorization through verified retained history.

Historical preserved-state inventory remains the **13:38:36 UTC** cut in
`../INVENTORY.json`; this CPU work is not a new operational-status receipt.

## Narrow integration next

Main can now integrate **only this exact-plan compatibility check and its
original-validator copy** into a separate candidate of the original confined
receiving path. Keep the original plan bytes and both hash pins; route already
applied state to recognition, never to another `prepare_wall_extension` call.
Before that route can execute, bind the real historical `WALL_EXTENDED` receipt
and unchanged COMPLETE/pending/checkpoint/old-head references through the
original verified journal. Missing or mismatched applied-history evidence must
remain an integration blocker, not be satisfied by the plan alone.

Still blocked, deliberately not changed here:

1. Current disk capacity and exclusive receiving ownership; no failed-artifact
   deletion or journal-tail reduction is authorized by this candidate.
2. Astra7's zero-byte 7808 partial-intent reconciliation. Original open/audit
   refusal is retained and tested through execution.
3. Original pending-sleep dispatcher/driver integration, paired
   `R184_LEARN_COMPLETE`, next-cycle handoff, recovery-checkpoint namespace and
   parent/readout/observer compatibility.
4. Real checkpoint/tail/source-closure and applied-history verification plus
   original confinement, lease/allocation and fresh receiving admission.

No guard, partial-intent or live integration implementation is supplied. Passing
these CPU tests does not resolve the other blockers or authorize a launch.

## Changed-path inventory

All paths below are relative to
`research_loop/workers/replication_sprint_20260919/evidence/node2_recovery/runtime_repair/`:

| Path | Purpose |
|---|---|
| `interrupted_sleep.py` | Isolated existing-kernel copy; only applied-wall compatibility/receipts added |
| `applied_wall_validation.py` | Exact original receiving validator function copy |
| `receiving_fixture.py` | Existing CPU fixture adapted to captured original plan bytes |
| `test_interrupted_sleep.py` | Existing 39 regressions, with isolated receiving-root mapping/plan fixture adaptations |
| `test_applied_wall.py` | 20 new exact-plan, runtime-tampering, validator-parity and partial-intent tests |
| `run_cpu_tests.py` | Bounded local runner and before/after provenance verification |
| `fixtures/OBSERVED_PLANS.json` | Two exact raw plans, base64-encoded, with source paths and hashes |
| `COPY_PROVENANCE.json` | Historical candidate/contract/test/inventory pins and bounded read provenance |
| `TEST_RECEIPT_1789826673791112117.json` | Retained initial 98-test iteration |
| `TEST_OUTPUT_1789826673791112117.txt` | Initial 98-test log |
| `TEST_RECEIPT_1789826748323909209.json` | First 99-test receipt and source hashes |
| `TEST_OUTPUT_1789826748323909209.txt` | First 99-test log |
| `TEST_RECEIPT_1789826937405021103.json` | Current 99-test revalidation receipt and source hashes |
| `TEST_OUTPUT_1789826937405021103.txt` | Current 99-test revalidation log |
| `README.md` | This handoff, scope, limitations and integration next step |
