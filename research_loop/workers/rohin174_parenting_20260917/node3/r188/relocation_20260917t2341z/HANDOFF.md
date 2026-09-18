# NODE3 six preserved exact-state packets

Verified persistent local storage, September17,2026. Originals remain live; no destination continuation is launched.

| Life | Saved cycle | COMPLETE record | Archive bytes |
|---|---:|---:|---:|
| support_free | 45 | 5840 | 317945658 |
| creative_reread | 45 | 5674 | 332259906 |
| brain_free | 44 | 5321 | 349460067 |
| brain_guided | 41 | 5022 | 344169694 |
| creative_free | 42 | 5206 | 359107456 |
| creative_select | 43 | 5376 | 340677168 |

Each `physicalN.VERIFIED.json` binds the archive SHA256, gzip CRC/path checks, original COMPLETE record/state/checkpoint hashes, effective R179+R181+cache source, and original logical-root mapping. `FILES.json` inside each archive has per-file hashes except opaque readout artifacts. No readout contents were inspected.

Restore requirements: extract into owned receiving storage; preserve original logical-root namespace for inbox source paths; retain all record/intent pairs; bind receiving host, GPU UUID/minor, existing lease, and an explicitly authorized receiving deadline. Original packets retain NODE3 16:50/17:00 and are not directly runnable beyond that deadline. Frozen model weights remain an external pinned dependency.

Parent custody remains on the original local parents. Reconcile original final journal/inbox and pending publications before switching transport; no duplicated baseline or unknown-publication retry. Current parent states/receipts remain under the owned node3 tree. Packets are snapshots while originals run, not lossless claims covering later live updates. Source stop/final delta and per-life target assignment are still required for actual continuation.
