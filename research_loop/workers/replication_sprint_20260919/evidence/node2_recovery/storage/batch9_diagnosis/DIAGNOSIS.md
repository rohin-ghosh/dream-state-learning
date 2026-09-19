# BATCH9 admission failure — read-only cut, 2026-09-19 15:46 UTC

**The original error is not attributable to a specific PID, FD, or errno from
the surviving record. Do not bypass it or replay completed batches.**

## Preserved original evidence

- Exact batch: `../coalescence_remaining/BATCH_0009.json`, raw/canonical SHA256
  `722ad53ce435564128ff2b2e6e32b8d8495c2c83f3f091f2c28f72d222cbd45e`;
  selection indices 41–45, five groups, 40 paths.
- `../coalescence_remaining/EXECUTION/BATCH_0009/LEDGER.jsonl` records
  `BATCH_REJECTED_NO_MUTATION`, stage `ADMISSION`, at **15:44:17.642343 UTC**;
  reason `complete_privileged_no_writer_snapshot_required`.
- The original `node2_scope.privileged_writer_fds` parses scanner stdout and then
  validates it before returning. Failure throws away that parsed result, and the
  outer ledger saves only exception type/reason. Neither original stdout nor an
  exact failing process/error was retained.
- Source-path inference, not recovered raw evidence: with the frozen scanner's
  successful privileged return and constant scope/protocol fields, this rejection
  points to a nonempty `inaccessible_or_exited` list. Its actual entry is unknown.

## Fresh diagnostics, not a mutation retry

1. `RAW_SCAN_20260919T154546_585004Z.json`, SHA256
   `6bc14bdc362375dec3c8ec9f54cdf8b75b0a3f1cedec08ce0545ee030353a42b`:
   one invocation of the byte-identical original privileged scanner on exactly
   BATCH9's 40 paths, before any validation. Exit 0; 1,500 processes, 2,196 FDs;
   **zero writers and zero inaccessible/unresolved processes**. Exact stdout and
   stderr are retained as base64, along with parsed output and path metadata.
2. `TRACED_SCAN_20260919T154645_429806Z.json`, SHA256
   `8947aeccc453ff82008f166589d26b6fd113da82ab23d8a58ac116700598501d`:
   eight bounded scans in 3.882 seconds, using `sys.settrace` around the unchanged
   original scanner. All eight have **zero writers and zero unresolved entries**.
   Observed exceptions are ENOENT while obtaining a disappearing process's
   initial `/proc/PID/stat`; the original scanner positively verifies those PID
   exits. **No closed-FD exception or inaccessible live process was reproduced.**
   Tracing can alter timing, so these samples cannot establish the historical
   failure's cause or retroactively approve it.

All 40 target paths retain the original reviewed inode/device, size, owner/group,
mode, mtime, ctime, and two-link bindings in both diagnostic captures. No journal
body was read. No WRITER lock was acquired, coalescer invoked, file changed,
retry scheduled, rollback performed, or native/parent/GPU signalled.

Owner-available bytes were **147,357,696** in the first read and **146,919,424**
after the traced reads. These are fresh readings, not available launch budgets.

## Narrow next step

The evidence supports repairing **diagnostic preservation**, not ignoring an
error class. A future isolated candidate should durably ACK the full raw scanner
stdout/stderr, parse status, target binding, and scan identities **before**
running the unchanged admission predicate, on both pass and fail. Tests must
prove live-unreadable results still reject and a durable-ledger failure prevents
admission/mutation. Preserve PID/start, phase, FD, errno, filename and lifetime
evidence in future failed-scan diagnostics where observable. No production repair
or policy relaxation is made here.

Canary and remaining batches **1–8 are completed and must never replay**.
Any separately reviewed continuation must exclude those groups and start from
the still-unmodified failed batch only under a new Main binding. The old runner
and all its frozen source, manifests, execution directories and failed artifacts
remain untouched.
