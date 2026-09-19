# Final node2 cut — partial cleanup, September 19, 2026

**Stopped truthfully partial. No retry, reset, guard relaxation, further cleanup,
or C0 launch was performed by this audit. Frozen code remains unchanged.**

## Verified result

| Item | Final audited result |
|---|---:|
| Completed | Canary + original batches 1–87 |
| Groups completed | **436 / 515** |
| Original paths accounted for in completed receipts | **3,488** |
| Canonical replacements completed | **2,616** |
| Selected allocated bytes released | **1,835,274,240** |
| Completed-chain records independently checked | **8,803** |
| Uncoalesced | Original batches **88–103**, **79 groups / 632 paths** |
| Pending selected allocated bytes | **6,291,456** — not reclaimed |

Every completed ledger chain, predecessor-success binding, completion receipt,
exact path set, content-hash declaration, and canonical inode/link-count
declaration passed the bounded independent audit. The original failed BATCH9
chain and artifacts remain preserved unchanged. BATCH88 has only admission,
raw-scan diagnostic, and `BATCH_REJECTED_NO_MUTATION` records; batches 89–103
have no execution directories. There is no all-batches-complete receipt.

Fresh node2 reads independently checked **40 paths across five completed groups**
(selection indices 0, 40, 41, 220, 435), including required metadata and eight-link
canonical identities. Five shared inodes were freshly content-hashed, reading
**10,695,661 bytes**. This is a sample, not a fresh rehash of all 3,488 paths.
Local bounded ledger/receipt reads totaled **14,089,978 bytes**. No model,
checkpoint, live journal, environment, or archive payload was read by this cut.

## Preserved stop condition

At **16:02:28 UTC**, BATCH88 retained a full raw scan with no observed writers,
two positively verified other-process exits, and one unresolved entry:
`FileNotFoundError`, PID **2499**, start ticks **1612**,
`live_or_unresolved_process_unreadable`.

The final read of `/proc/2499/comm` and start time identifies **polkitd**, with
start ticks **1612** before and after the read. It is the same live lifetime;
this does **not** prove a safely closed FD or identify which read failed.
Uncertainty remains unwaived. Original BATCH88 target identities/required
metadata in the raw scan are unchanged and retain their original two-link
bindings. No BATCH88 mutation records exist.

## Actual capacity: C0 still blocked

At **16:05:13.702 UTC**, node2 reported `bfree=9,809,257`, `bavail=383,295`,
`frsize=4,096`:

- Owner-available capacity: **1,569,976,320 bytes**.
- Free bytes including reserves: **40,178,716,672**; not an owner budget.
- Reported `bfree − bavail` gap: **38,608,740,352 bytes**.
- C0 conservative startup budget: **2,981,136,864 bytes**.
- Actual C0 shortfall: **1,411,160,544 bytes**, before additional writes.
- Even hypothetical release of every remaining selected byte would leave
  **1,404,869,088 bytes** missing at this cut. No such release is authorized here.

The two-second final sample lost 8,192 owner-available bytes. Filesystem writes
and reservation/accounting mean allocated-byte relief is not identical to new
owner headroom. No root-reserved blocks were used or changed; C0 cannot be
called launch-ready from this cleanup.

## Publishable evidence and source bindings

- Audit: `FINAL_PARTIAL_CLEANUP_AUDIT_20260919.json`, SHA256
  `61240223967f3f1939eceb6a056f69a59bfa7b37155eeaebcb2a3e6dd123c9e8`.
  Includes full per-batch counts/chains, receipt/source hashes, BATCH88 raw
  diagnostic, sampled path evidence, and capacity/PID readings.
- Continuation manifest: `1576b5293d194c15ee4216456e6062cd6bd4b24336efd3b1d77a33185a5b5f64`.
- Continuation runner: `d325cfc7242ae9a6d243bb35c46ad3e30e277372de31dc458a0d5737c9dd9027`.
- Diagnostic wrapper: `48020b62d72eaf28d935eabf9e0ee9f5545d661bfb212111b4803dd6b9ce0692`.
- Original scanner: `3f2e858d2d540759aaef0d7cd56acae56600460a72da039803793dc71d15503c`.
- BATCH88 raw ledger file: `eb4b2767ee52bcca5cea4d7a7a38b48b59b08faa24dea7986f2e483a48554d67`.
- Last successful BATCH87 chain: `e191721a0dcae8a98bcab8d0941689f0b5bfdababad39a7b5405f7e2ca4f8446`.
- Failed BATCH88 chain: `e429d7e113cdaf386ef8e04f570c26644a9511a3867ed46106f34ecc29c46a13`.

All original archive and failure artifacts remain in place. The previously
verified off-node archive was not rehashed in this final bounded audit.
