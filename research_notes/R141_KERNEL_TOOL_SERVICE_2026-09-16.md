# R141 kernel tool service — CPU-tested staging handoff, 2026-09-16

## Scope and status

Non-material operator plumbing under the standing builder authorization; no
scientific, learning, visibility, benchmark, executor, runtime or sandbox-policy
change. This work owns only:

- `gpu/orch_r141_kernel_tool_service.py`
- `tests/test_orch_r141_kernel_tool_service.py`
- this note.

**Not deployed. No GPU commands or child requests were executed by this worker.**
All GPU boundaries in tests are synthetic. Existing bridge dispatch, executor
locking, admission/gate validators, journal persistence and Tool publication are
exercised on local synthetic data. Other workers' changes are preserved. No held
readouts, credentials, remote hosts, leases or users were inspected or changed.

Main's supplied live observations (not independently observed here):

- Original kernel0 is
  `/localhome/local-rohing/orch_r132_kernel_child_20260916_attempt1/run1`.
- Executor root is
  `/localhome/local-rohing/orch_r132_kernel_executor_20260916T093845Z`.
  Existing `source_v9/gpu/orch_r132_kernel_executor.py` SHA-256 is
  `034ddbdddfea960b97a3461366d9eebfc05a9ff053c9cc7ec497c565cdea66b7`;
  runtime is `runtime_v2`. The local executor has this same hash.
- Main refreshed `probes_r141_v1/GATE.json` at **12:46:22 UTC on September 16**:
  26 checks passed and assigned contexts were empty. Approximate expiry is
  13:46 UTC; the 150-second admission reserve cuts off earlier, around 13:43.
  **Use the actual pinned receipt timestamps, never these approximations.**
- Main answered the documentation/interface request in committed response 833
  via Tool `33c3ec69f066429cb588aa4051ccf7db` at 12:46:25 UTC. Do not duplicate it.
- At Main's 12:58 UTC update the latest audited prefix was 982, 39 responses,
  still in sleep, with no exact request after 940. This is **not** a cursor to
  adopt automatically: Main must select the latest audited prefix at deployment.
  Malformed `pythonexperiment`, pseudocode and ordinary prose remain inert.

## Exact behavior and safety boundaries

1. Static operator configuration pins one root, journal manifest/id and the
   **file bytes** of the manually selected predecessor `start_index - 1`.
   The cursor hash-chain extends that prefix; no historical scan or backfill.
   Generic positive indices are supported for other journals. For **this**
   deployment Main must choose a prefix after response 833, and after everything
   Main has already audited/handled. Do not deploy with the test fixture index.
2. The service follows numbered journal records, not partial/intent files,
   files referenced by metadata, held artifacts or child-supplied paths. Every
   traversed record must match its schema, index, journal id and canonical hash,
   and the previous cursor hash. Supported non-request lifecycle records are
   `COMMITTED`, `INBOX`, `UPDATE`, `CHECKPOINT`, `LOADED`, `TERMINAL`,
   `SLEEP_REQUEST`, `SLEEP_COMPLETE`, `COMPACTION`, `COMPACTION_SKIPPED`,
   `TARGET_ELIGIBILITY`, `PRESENTATION`, `WALL_EXTENDED`.
   Their referenced checkpoint/readout paths are never opened. A child wall
   extension does not extend the service wall or the lease.
3. `REQUEST.split != TRAIN` stops service before advancing to its response.
   Exact candidates require the existing REQUEST → RESPONSE → COMMITTED hash,
   request/source joins, terminal/nontruncated generation, and exact source.
   After those joins verify, ordinary capped/incomplete generations produce
   an immutable local `NO_EXECUTION_<index>.json` and are skipped. No Tool or
   GPU action follows them, even if their text contains a complete-looking fence.
   Prose/plain code, malformed, nested and multiple fences likewise get only a
   local no-execution disposition. **No optional malformed-envelope feedback is
   implemented**, to keep the exact-request loop narrow.
4. A live RESPONSE with COMMITTED not yet visible is retained as a READY pending
   index plus exact response-file hash. Poll it again, including after a clean
   READY restart. Do not create an action intent, acquire the GPU lock, run a
   census, publish, or advance past it. Changed pending bytes stop the service.
5. Before runtime validation, census or dispatch, persist a per-response INTENT,
   budget reservations, original record snapshots and exact request/source.
   The gate/runtime are checked before census. Under the **same existing
   executor lock**, inspect the previous job receipt, verify UUID/device mapping,
   obtain a bounded fixed-command XML process census of only the assigned UUID,
   and write a fresh source-bound admission. Unknown/busy census fails closed.
6. The admission binds request id/source/origin, static config/closure, gate and
   census hashes. It uses the existing lease receipt verbatim and a hard wall no
   later than lease-end minus its existing margin (at least six hours), the
   service UTC deadline, and the remaining monotonic deadline. Admission expiry
   is capped by **gate expiry**, that wall, and census observation + 210 seconds.
   There is no gate renewal or new lease authority.
7. **Release the census lock before calling `bridge.dispatch`.** Do not wrap
   dispatch in another flock of that file: `executor.run_request` takes its own
   nonreentrant lock. The unchanged executor rejects admission older than the
   previous job finish, retains the lock through execution, revalidates admission
   immediately before launch, and rechecks runtime/gate/device identity.
   A slow repeated runtime validation ages the census: final admission validation
   then refuses launch if older than 60 seconds, or if less than 150 seconds of
   admission/gate/lease/service wall remain. The service also rejects a census
   already over 30 seconds old at admission construction. This is deliberately
   fail-closed rather than refreshing evidence inside the executor.
8. Persist `DISPATCH_PUBLICATION_INTENT` before calling the unchanged
   `gpu.orch_r132_kernel_bridge.dispatch`. That one call owns both dispatch and
   **exact existing bridge Tool publication**. Do not independently republish.
   AST-invalid exact requests go through the bridge's real `REQUEST_REJECTED`
   path, preserving its original `REQUEST.json`, `RESULT.json` and Tool receipt;
   no GPU is launched for those candidates. Envelope/parser failures that cannot
   construct an existing bridge request stop without inventing a substitute.
9. Only a returned, persisted `BRIDGE_RECEIPT.json` allows the cursor to advance.
   Any unfinished INTENT or DISPATCH_PUBLICATION_INTENT is poisoned on restart;
   the service will not infer nonexecution from a missing result or infer failed
   delivery from a missing delivery receipt. `TEARDOWN_UNVERIFIED` and
   `DISPATCH_FAILED_NO_RETRY` stop after preserving bridge delivery. Existing
   uncertain executor-lock receipts also require Main reconciliation.

### Custody assumptions, not new enforcement

Main must exclusively reserve physical index 2 / actual minor 1 /
`GPU-35dcea35-12bc-f2f3-d5d2-d2eaa8bacdd8` on a40r for this window. **No other
owner may touch it**, including through a different lock. Set the two authority
flags only after establishing that operational reservation. The unchanged lock
detects competing cooperating dispatches, but is advisory: it does not prevent
an unrelated host process from opening the GPU. No new host privileges or
access policy are introduced to pretend otherwise.

The trusted host journal publisher remains append-only, and staged source,
runtime and receipt trees remain frozen for the service lifetime. Hash checks
detect observed replacement, not a hostile same-UID operator deliberately
rewriting files between instructions. Children cannot select operator paths or
edit them through this tool. Main must not edit/reuse a bound namespace, prefix,
source or admission while the service is running.

## Finite budgets

- `wall_seconds`: integer 1–1800, persisted UTC and monotonic deadlines; neither
  restarting READY state nor a child lifecycle record renews them. An in-process
  hard alarm interrupts blocking work. Existing executor owned-job cleanup may
  take its bounded teardown interval after an alarm; abrupt termination can
  leave an uncertain owned job, never permission to replay. The unchanged unit
  retains its own RuntimeMaxSec/teardown limits. The child is never signaled.
- `max_polls`: includes **every sparse UPDATE/sleep/metadata record**, not just
  responses, and every missing-record or pending-commit poll. Idle/pending polls
  sleep `poll_seconds`; lifecycle traversal does not add a sleep per record.
- `max_calls`: attempted bridge transactions, including accepted ASTs, exact AST
  rejections, and conservatively reserved intents that fail preparation. No
  automatic retry loop can consume another call for the same response.
- Read accounting is **conservative logical reservations, not syscall tracing**:
  each poll reserves 100 reads / 160 MiB; each committed response inspection
  adds 100 / 1 GiB; an exact candidate reserves manifest sizing (configured
  maximum runtime files + 1 reads / 4 MiB), then 300 + three times the actual
  runtime-file count / 1 GiB + three times its bytes for repeated validation,
  origin, gate and bridge work. Runtime sizing is itself capped at configured
  files/bytes (absolute maxima 50,000 files / 64 GiB).
  Fixed bounded configuration/namespace bootstrap reads are outside the loop
  counters. Individual journal records are bounded at 32 MiB; manifests at
  4 MiB; gate/results at 1 MiB; lease/admissions at 64 KiB. Accounting refuses
  an operation *before* exceeding a reservation budget; it need not consume the
  actual reserved bytes. Small metadata still consumes the full poll reservation.
- `max_request_bytes` cumulatively reserves encoded exact requests before
  admission. The unchanged request parser's per-request cap is 100,000 bytes.
- `max_output_bytes` reserves 4 MiB per call for bounded capture/result/Tool
  receipt/census output, not the preserved input-journal snapshots. Actual kernel
  capture retains at most 1 MiB; the new census at most 64 KiB with a ten-second
  command timeout. Journal evidence storage is separately finite: at most three
  32 MiB snapshots per reserved call plus small per-response disposition files;
  spool input/runtime resource limits remain the executor's existing ones.
- Gate unusable/expired, lease wall, source/hash change, unreadable data, busy
  lock/census or any budget exhaustion stops **only this service**. No launch
  alone is labeled inference success, correctness, or speedup; the existing
  bridge's measurement/status qualifications are unchanged.

## Main-only additive staging and configuration

These are **instructions, not actions performed by this worker**. Finish tests
and Main's operator review first. The refreshed `source_v9` does not currently
contain the bridge. Stage the new service plus the **unchanged** bridge and its
console/helper dependency closure additively. Never overwrite an existing file
with different bytes, patch the executor, or rebuild the runtime/gate.

1. Use the existing frozen `source_v9` as the import root, if all existing files
   needed below already have the required compatible bytes. Add only missing
   files. If an existing dependency differs, stop and reconcile it with Main;
   do not silently replace a gate-bound helper with the current working copy.
   A new staging directory is also possible only if Main preserves every
   executor policy-identity component and the gate still validates unchanged.
2. The service's read-only `closure()` enumerates the actual loaded local source
   paths and hashes. Expected project files (including the otherwise unchanged
   R140 utility module used for exact fence parsing and durable file helpers):

   ```text
   gpu/__init__.py
   gpu/orch_r141_kernel_tool_service.py
   gpu/orch_r140_pilot_tool_service.py
   gpu/orch_r132_kernel_bridge.py
   gpu/orch_r132_kernel_executor.py
   gpu/orch_r127_pilot_console.py
   gpu/orch_r125_stream_console.py
   gpu/orch_r125_stream_journal.py
   gpu/orch_r125_cpu_experiment.py
   gpu/orch_r125_cpu_confinement_probe.py
   gpu/orch_r125_bounded_capture.py
   organism_v6/__init__.py
   organism_v6/orch_r125_experiment_request.py
   organism_v6/orch_r125_continual_stream.py
   organism_v6/orch_r124_train_history.py
   ```

   The executor, capture, CPU helpers, request parser, host tools, driver, boot,
   command/harness/task, runtime manifest and devices must still match the
   existing gate identity. Adding a bridge/console/service must not change them.
   The local unchanged bridge hash at handoff is
   `d04b646738cf04499f94e94c9d12d6bae9b025377a8b477fce6960cad637b347`.
3. Select and audit the most recent eligible predecessor **manually**. Retain its
   bytes/hash, select `start_index = predecessor_index + 1`, and exclude all old
   requests and Main's response-833 documentation interaction. Do not use 983
   merely because this note mentions prefix 982. The service never selects a
   live cursor or derives authorization from a recent filename.
4. Main creates a private operator config file (0600 or stricter), outside the
   child root. Parent directories for **fresh, disjoint, nonexistent** state
   and spool paths must already exist. Set `source_root` to the actual staged
   import root and `lease_receipt_path` to the already approved existing receipt.
   Do not create/change a lease. Fill the following template; placeholders are
   deliberately invalid until Main chooses them:

   ```json
   {
     "root": "/localhome/local-rohing/orch_r132_kernel_child_20260916_attempt1/run1",
     "source_root": "/localhome/local-rohing/orch_r132_kernel_executor_20260916T093845Z/source_v9",
     "runtime_root": "/localhome/local-rohing/orch_r132_kernel_executor_20260916T093845Z/runtime_v2",
     "gate_path": "/localhome/local-rohing/orch_r132_kernel_executor_20260916T093845Z/probes_r141_v1/GATE.json",
     "lease_receipt_path": "MAIN_SELECT_EXISTING_RECEIPT_ABSOLUTE_PATH",
     "state": "MAIN_SELECT_FRESH_PRIVATE_STATE_ABSOLUTE_PATH",
     "spool": "MAIN_SELECT_FRESH_PRIVATE_SPOOL_ABSOLUTE_PATH",
     "start_index": "MAIN_SELECT_AUDITED_PREDECESSOR_PLUS_ONE",
     "executor_lock": "/localhome/local-rohing/.orch_r132_kernel_gpu1.lock",
     "gpu_uuid": "GPU-35dcea35-12bc-f2f3-d5d2-d2eaa8bacdd8",
     "device_minor": 1,
     "main_authorized": true,
     "exclusive_gpu_custody": true,
     "wall_seconds": 1800,
     "poll_seconds": 1,
     "max_polls": 3000,
     "max_calls": 4,
     "max_reads": 2000000,
     "max_read_bytes": 1099511627776,
     "max_request_bytes": 400000,
     "max_output_bytes": 16777216,
     "max_runtime_files": 50000,
     "max_runtime_bytes": 34359738368
   }
   ```

5. From that staged import root, with bytecode writes disabled, Main may run
   **read-only** `pins` and `check` below. `pins` emits a complete config with
   exact source-file hashes, journal id/manifest, predecessor file, runtime
   manifest, gate and lease hashes. Review and save the output as a **new private
   file**, never overwrite an already bound config or redirect onto its input.

   ```bash
   PYTHONDONTWRITEBYTECODE=1 python3 -m gpu.orch_r141_kernel_tool_service pins --config /ABSOLUTE/DRAFT.json
   PYTHONDONTWRITEBYTECODE=1 python3 -m gpu.orch_r141_kernel_tool_service check --config /ABSOLUTE/PINNED.json
   ```

   `check` reports `STATIC_PINS_CHECKED_NOT_ADMITTED`: it is not a fresh census,
   full live runtime/device gate, scientific acceptance, or launch authorization.
   Before any later run, Main must also check that the current gate is still
   usable, exclusive GPU custody holds, the lease-minus-margin has headroom,
   `/usr/bin/nvidia-smi` is the existing available tool, and no orphan service or
   executor intent needs reconciliation.
6. **Future Main-only operation, not authorized/executed by this coding task:**
   in a separate operator process/terminal, not a child wrapper, the entry point
   is `python3 -m gpu.orch_r141_kernel_tool_service run --config /ABSOLUTE/PINNED.json`
   with `PYTHONDONTWRITEBYTECODE=1`. Do not use an auto-restart supervisor or change
   permissions/policy to make it work. No request means no census and no GPU
   dispatch. A stale gate stops the service; leave the child running. Do not
   renew the gate automatically to rescue a missed deployment window.

## Restart and reconciliation

Retain CONFIG, PREDECESSOR, STATE, the spool SERVICE_OWNER, per-response INTENT,
original records/source, CENSUS, EXECUTOR_LOCK_BEFORE, ADMISSION,
DISPATCH_PUBLICATION_INTENT, BRIDGE_RECEIPT, and existing bridge spool artifacts.
Existing STOPPED state stays stopped. Only READY may resume with the **same
config, paths, counters and original deadlines**. A failure before namespace
initialization completes may leave an incomplete namespace; preserve it for Main.

For any orphan/uncertain intent Main must reconcile executor ownership/status,
spool request/result and actual inbox receipt before deciding a new audited
prefix. Missing evidence is not proof that a dispatch or Tool publication did
not occur. Never delete STATE/lock/spool, allocate a fresh namespace to replay
the same response, regenerate its admission, or manually republish its result
as an automatic repair. This worker cannot reconcile live GPU uncertainty.

## CPU verification

**Result: 298 passed in 20.98 seconds** across the four suites below (75 new
sidecar cases, 120 unchanged executor/bridge cases, 103 existing R140 service
cases). This is engineering readiness for Main's staging review, not a live
gate, deployed service, GPU execution or scientific claim.

Local test command (the base Python had no pytest; dependencies were isolated
with uv's cache under `/tmp/orch-r141-uv-cache`):

```bash
UV_CACHE_DIR=/tmp/orch-r141-uv-cache uv run --no-project --with pytest python -m pytest -q \
  tests/test_orch_r141_kernel_tool_service.py \
  tests/test_orch_r132_kernel_executor.py \
  tests/test_orch_r132_kernel_bridge.py \
  tests/test_orch_r140_pilot_tool_service.py
```

Coverage includes the real active StreamJournal lifecycle (INBOX, truncated
generation, compaction, sleep request, UPDATE/CHECKPOINT, sleep completion and
later exact generation), real bridge accepted/rejected receipts and attributed
console, pending live tails and READY restart, no replay after uncertain
execution/publication, source/journal/gate/lease failures, stale census across
repeated runtime validation, gate-expiry admission cap, advisory-lock race
rejection, bounded XML census using a real CPU subprocess/capture, generic
manually pinned starts, two distinct admissions, and wall/poll/read/call/output
limits. Synthetic correctness measurements in tests are fixtures, not GPU results.
