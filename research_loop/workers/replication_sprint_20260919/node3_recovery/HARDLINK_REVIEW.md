# Hardlink assessment and execution review

## 2026-09-19 14:12 UTC — canary done; all remaining work unexecuted

The original read-only assessment below is historical. The complete archive
and filesystem restore passed. Main then authorized exact canary
`c36db2e09f6918416a0276c353b30931361f4bad90d89bff49bd351292ba4f83`:
6 replacements,9 file paths preserved and verified,17,084,416 observed free
bytes gained, **owner f_bavail still0**. The6 parent-directory mtimes advanced
as an entry-operation side effect; the9 file mtimes and required metadata are
preserved. This distinction is explicitly submitted to Main before more work.
See `CANARY_RESULT_AND_REMAINING_REVIEW.md` for receipts, the exact remaining
proposal and its metadata caveat. No other batches ran.

## Original read-only assessment — 2026-09-19 13:47:30 UTC

**No hardlinks, replacements, deletions or remapping performed.**

The completed remote source manifest contains85,620 entries, SHA256
`9086338288c21d3100d6312e9a5ec4a828b3f1acda5737dc1c99c2ccae438268`.
It covers only the three approved retired directories. The bounded analysis
streamed that manifest from ovx4 to node3, not an experiment extraction onto the VM.

## Exact requested equivalence and physical-block accounting

- 1,659 eligible groups match **SHA256, size, UID, GID, mode, mtime_ns and xattrs**.
- Files are at least1MiB; every candidate is still the same regular nonredirected
  source file, checked against its manifest device/inode, size, ownership,
  permissions, mtime, ctime, nlink and xattrs. No candidate group failed those checks.
- Potential allocated blocks released: **35,280,035,840 bytes** (35.28GB).
  Logical duplicate content:35,273,422,040 bytes. These are different measures.
- Existing hardlinked extra paths:0. Inodes with links outside the eligible
  path set:0. Each losing inode is counted once using current `st_blocks*512`.
- Exact canonical paths and every proposed replacement path, original inode,
  link count, metadata and allocated bytes are in `HARDLINK_ELIGIBLE_PATHS.json`.
- Actual reclaimed bytes: **0**. Node3 owner-available space remains **0**.
  No estimate treats root-reserved blocks as usable owner capacity.

## Important limitation: not literally every metadata field can stay unchanged

Atomic hardlink coalescing could preserve every path and byte plus the listed
equivalence fields, but **necessarily changes inode identity, ctime and nlink**.
Furthermore, **none** of the1,659 groups has identical current atime across
all copies; one shared inode cannot retain distinct per-path atimes. Independent
future edits also become shared writes. Thus the answer to “all original
metadata unchanged” is **no**, without an explicit metadata exception or
out-of-band restoration manifest. Original metadata is captured by the archive
manifest; that is not the same as retaining it on each live source pathname.

Only explicitly immutable retired copies should even be considered. If Main
approves that narrower lossless-content definition after full archive/restore
verification, immediately rehash candidate bytes and recheck metadata, PID/FD
use, links, device and free blocks before any separately authorized replacement.
This report does not authorize execution or include an execution script.

## Archived provenance check

`RETIRED_PROVENANCE_AND_FDS_v2.json` inspects40 retirement/manifests/receipts,
depth<=3 and size<=4MiB, with no size/parser skips. **No inode/st_ino/st_dev,
ctime or nlink fields were found** in those documents; provenance there uses
paths/content hashes/sizes. Original journal readers cache inode identity while
open, so absence of a live reader/writer remains important. No writer FD in
these directories was found among readable owner processes. Five process
inspections were permission-denied and one raced with exit; this is a bounded
check, not proof against every external dependency or inaccessible process.

The complete original archive COPY is still transferring. Do not coalesce
source files while its metadata-preserving copy is in flight.
