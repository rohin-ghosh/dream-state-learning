# Node2 storage handoff — 2026-09-19 15:12 UTC

**Urgent: owner-available capacity is zero. No space has been reclaimed.**
The final metadata cut started at 15:12:38 UTC. C0 remains storage-blocked:
its frozen CPU candidate requires 2,981,136,864 available bytes. All 72 frozen
bundle files were rechecked unchanged; no additional C0 work was performed.

## Exact selected archive: complete and fully verified

Main authorized copy/full verification only. The original `ovx_ssh.sh` route
streamed directly through a VM pipe to `ovx4_ssh.sh`; no archive payload was
stored on the VM or node2. The destination is:

`/localhome/local-rohing/node2_retired_duplicate_preservation_20260919_20260919T151113Z`

- Exact selection: all 515 groups in `HASH4G_20260919T150656Z.json`, selection
  SHA256 `ec00b7918d16ac806eb7ebc405b7f150ce83d300946c3a61c44790af8b944e26`.
- 4,120 original paths; 2,060 distinct original inodes; 2,450,844,540 unique
  content bytes. Only the four retired `creative_d1`, `math_d1`,
  `math_transfer_c1`, and `repo_c1` record families contribute selected files.
- Each exact original and preservation alias is listed with SHA256, inode,
  device, size, link count, uid/gid, mode, timestamps and xattrs in destination
  `SOURCE_MANIFEST.jsonl`. Manifest SHA256:
  `e9af879062abaeae7018a403a79ed909c0c5dfa334f549d32df5485238139db0`.
- Archive `retired-node2.tar.gz`: 358,800,975 bytes; SHA256
  `caf4f1733b2ac16493d2f9d46b1e60e1d81a0c953eea1075bb363c1062111874`.
- Destination started with 528,122,732,544 owner-available bytes against a
  conservative 28,827,370,100-byte archive/restore/reserve requirement.
- Mc's actual archive-member verifier checked every member, content hash,
  original numeric ownership, mode, mtime, atime, ctime, xattrs and hardlinks.
  A separate full filesystem extraction checked every file's bytes, original
  uid/gid, permissions, hardlink topology/link counts, mtime, atime and xattrs.
  Destination owner UID is 1352; original file UID/GID 2524 were applied only
  inside the new privileged restore tree. Filesystem ctime/inode/device cannot
  be recreated; their original values remain in the archive and manifest.
- All selected source metadata matched the original hash cut both before and
  after transfer. No original path, contents or metadata were changed.
- Local receipt: `ARCHIVE_FULL_RESTORE_VERIFIED_20260919T151113Z.json`.
  The same receipt is durable at destination `FULL_RESTORE_VERIFIED.json`.

The first destination ending `20260919T151043Z` is a preserved failed attempt:
tar could not obtain no-atime access to `/`. It read no selected payloads.
The successful attempt used the owned home directory as tar's source base.
No failed artifacts were removed or overwritten.

## Concrete reclaim proposal for Main review — NOT executed

The 515 byte-verified groups offer **1,841,565,696 allocated bytes** of potential
reclaim by replacing duplicate inodes while retaining every original pathname.
Source-to-preservation pairs already share inodes and offer **zero additional
reclaim**; the opportunity is across the four different retired clones.

Exact original prefixes:
`/localhome/local-rohing/orch_r153_r201_node2_clones_20260917_operator1/`
followed by each contributing life and `/raw/stream/records/`.
Preservation aliases are beneath:
`/localhome/local-rohing/orch_rohin233_focus_node2_20260918/preserved/`
followed by each contributing life and `/records/`.
The selection and manifest enumerate the filenames; these prefixes alone are
not a mutation allowlist. No model, venv, checkpoint or live journal is selected.

A fresh privileged read at 15:07:51 UTC examined 1,506 processes and 2,251 FDs
against 68,182 retired inodes: no references, errors or races. Historical native
identities were absent. This is a point-in-time proof, not an enduring writer
lock. Any mutation must revalidate it and every exact file/inode/hash binding.

Next actionable step: Main reviews a node2-specific exact-path batch using
Mc's tested atomic hardlink/ledger mechanism, now bound to this node2 archive
and restore proof. Explicit inode/ctime/nlink/atime exceptions remain necessary.
Mc's existing implementation has a node3 path allowlist, a 40-path canary cap,
and a 1 MiB minimum: do not run it unchanged or falsely claim all 515 groups
already satisfy those predicates. No mutator was written or executed here.

Even full estimated reclaim leaves **1,139,571,168 bytes** missing from C0's
budget at zero headroom, before ongoing writes. This is an emergency capacity
increment, not C0 launch clearance or an indefinite storage solution.

## Regenerable-cache result

Named cache/temp roots total only **35,889,152 allocated bytes** at 15:06 UTC:
pip 12,288; Triton 29,077,504; CUDA ComputeCache 4,096; vLLM 12,288;
FlashInfer 6,778,880; torchinductor temp 4,096. uv, ccache, sccache,
torch_extensions and `.cache/triton` were absent. No >2 GB cache was found.
No readable owner-process cache reference or installer was found, but four
processes were inaccessible to that unprivileged cache scan. Compiler caches
may be future runtime dependencies. These are inventory totals, not deletion
clearance. No HF/model, venv or arbitrary-temp contents were inspected.

## Observed growth and limits

The extra caption life's exact source binding is
`/localhome/local-rohing/orch_r229_unparented_caption_20260918/r213_r226_caption_unparented_fork/raw`.
Metadata-only scans observed its stream grow by 118,947,840 bytes over 34.13 s
(15:02:31–15:03:05), **3,485,137 bytes/s**. Its checkpoint allocation stayed
27,425,329,152 bytes. Later, near exhaustion, stream growth slowed to 172,032
bytes over 337.83 s (15:07:03–15:12:41), **509 bytes/s**. Do not extrapolate that
near-full slowdown as normal demand or evidence of healthy execution. No
journal-body replay occurred and not every lost filesystem byte is attributed.

Existing September 17 `physical1/4/7.tar.gz` packets and their declared VM copies
were found with matching sizes and historical verification receipts; they do
not establish full coverage of September 18 retirement state. They were not
deleted, freshly rehashed or used as this archive's proof. Node3 archive proof
was not transferred to node2 by assumption.

Receipts: `CACHE_20260919T150604Z.json`, `HASH4G_20260919T150656Z.json`,
`PRIVILEGED_REFERENCES_20260919T150749Z.json`,
`ARCHIVE_STREAM_VERIFIED_20260919T151113Z.json`,
`ARCHIVE_FULL_RESTORE_VERIFIED_20260919T151113Z.json`, and
`FINAL_METADATA_20260919T151238Z.json`.
`HASH4G_20260919T150644Z.json` predates the successful budget increase: despite
its filename it hashed only 12 groups; its recorded byte limit is authoritative.
