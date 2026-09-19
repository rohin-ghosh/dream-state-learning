# Astra7 empty intent — isolated reconciliation candidate

**Complete for CPU review, not receiving-ready.** September 19, 2026.
No live mutation, remote read, staging, model/GPU operation, native launch,
restart, git staging/commit/push or node3 edit occurred. Historical runtime,
wall-repair code, original auditor and inventory hashes remain unchanged.

## Explicit mutation requiring Main review

The candidate is limited to Astra7's empty, uncommitted
`00000000000000007808.intent.json.partial`, with exactly the pinned 7807 head,
existing exclusive WRITER lock, unchanged manifest/namespace/identities and no
7808 canonical intent or commit. It rejects nonempty/multiple partials, changed
bindings, missing/busy/replaced locks, occupied evidence targets and history gaps.

The exact CPU-tested operation is:

1. Fsync **PREPARED** evidence containing original pathname, identity, full stat
   metadata, xattrs, empty-byte hash, old-head binding and intended mutation.
2. Hard-link the artifact into a new same-filesystem evidence directory with
   no-overwrite semantics. Preserve the **same inode**, fsync it and the archive
   directory, then write/fsync **LINKED**. Verify both aliases and all bindings.
3. **Explicitly unlink only the original failed temporary name.** Its bytes and
   inode remain in the archive; pre/post metadata retain expected ctime/link-count
   changes. No committed record/intent, pending row or checkpoint is removed.
4. In the CPU fixture, require the original strict auditor to report the exact
   same head, count and saved state, then fsync **RECONCILED**. No new 7808 record,
   sleep completion or driver LEARN completion is fabricated.

Zero length is checked through bound regular-file descriptors without reading
the empty artifact, preserving its original atime. Tests verify mode, all three
timestamps in the original receipt, xattrs, inode, bytes and historical metadata.
The source-name unlink is deliberate and remains **unexecuted on real data**.

There is no automatic retry, rollback or cleanup. Failures before durable LINKED
retain the source name. Failures after unlink retain the archive plus earlier
receipts but return failed/unknown, never success. An incomplete final receipt
must not be treated as success merely because its filename exists. A corrupt
older record fails the full CPU post-audit; it is not fixed or silently skipped.

## Tests and receipts

**132/132 PASS at 14:27:58 UTC**, in 66.5 seconds:

| Suite | Tests |
|---|---:|
| New reconciliation tests | 33 |
| Existing copied runtime regression | 39 |
| Existing exact-wall compatibility | 20 |
| Original restart contract | 18 |
| Original strict replay | 22 |

- `TEST_RECEIPT_1789828078862422699.json` — current result, source pins and protected before/after hashes.
- `TEST_OUTPUT_1789828078862422699.txt` — current detailed test log.
- Earlier `TEST_RECEIPT_1789827928473682753.json` / matching output retain the 131-test iteration; counts are not added together.

The new suite builds one full contiguous **synthetic 7808-record journal**, using
the hash-pinned original journal/stream implementations, with three pending
child rows and an unresolved SLEEP_REQUEST. It tests ordinary original
constructor/auditor rejection before reconciliation and ordinary
constructor/auditor acceptance afterward, with identical retained state. The
held-lock audit adapter does not override original audit/scan methods. Metadata,
in-place races, lock ownership, no-overwrite, missing records and receipt/fsync
failure cases exercise the candidate operation, not just a standalone predicate.

The fixture's record contents/state/checkpoint references are **not real Astra7
records or tensors**. Its last record and failed index match 7807/7808; its earlier
synthetic transition positions do not reproduce the real lifetime. Combining
these suites does not constitute an integrated partial→sleep→driver restoration.

Run from repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B research_loop/workers/replication_sprint_20260919/evidence/node2_recovery/partial_intent/run_cpu_tests.py
```

The runner bounds each suite to 180 seconds. It saves receipts here; legacy suites
use their existing isolated temporary fixtures, not original runtime files.
No bulky journal or checkpoint payload is saved in the handoff.

## Production seam — explicitly not implemented

**Do not use full historical JSON semantic replay as production recovery.** It
is only the CPU test oracle here. The candidate entry point rejects paths outside
local `.cpu-fixture-*` containers and cannot be used as a live repair command.

After review of the link/unlink semantics, the future admitted receiver must:

- Reuse its existing **source-bound raw-prefix hash + COMPLETE semantic-tail
  auditor**, binding the exact current head and entire pending state. No prefix
  or pending rows may be skipped or reset; no multi-hour full historical replay.
- Keep exclusive writer ownership across fresh identity/head verification,
  durable archival reconciliation and bounded post-verification. The CPU helper
  is not the production receiver/guard integration.
- Bind fresh real partial inode/full metadata and live ownership/capacity proof.
  The earlier 13:38:36 UTC inventory did not bind the inode/full metadata and is
  not a fresh execution authorization. Its reference hashes are in PROVENANCE.
- Integrate the pending-sleep kernel, new checkpoint namespace, paired
  `R184_LEARN_COMPLETE`, continuous driver/parent handoff and original admission
  separately. The candidate has restored **neither C0 nor Astra7**.

Flock excludes cooperating original writers, not a hostile same-UID process
ignoring the lock. The unchanged-head and identity checks are not a replacement
for production ownership/admission checks. The optimized receiving audit seam
remains unimplemented; no claim of production latency or receiving readiness.

## Changed files / coordination

All new files are under
`research_loop/workers/replication_sprint_20260919/evidence/node2_recovery/partial_intent/`:

- `reconcile.py` — fixture-only reconciliation and held-lock original-auditor adapter.
- `test_reconcile.py` — 33 new original-auditor integration/failure tests.
- `run_cpu_tests.py` — bounded runner for 33 new plus 99 retained regression tests.
- `PROVENANCE.json` — protected baseline/source pins and limited historical case binding.
- `DESIGN_FOR_MAIN_AND_MC.md` — reusable protocol, exact mutation semantics and production seam for Main/Mc; no claim of Mc approval.
- `README.md` — this scope/result/integration handoff.
- Two timestamped test receipts and their logs listed above.

No code or notes in Mc's node3 scope were edited. **Return to Main for review;
no execution or staging is requested by this candidate.**
