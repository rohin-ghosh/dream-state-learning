# Bounded node2 cleanup — September 19, 2026

## Result

**Safely reclaimed 1,410,416,640 allocated bytes on node2 at 21:07:42 UTC
(14:07:42 PDT).** Exactly three redundant retired transport archives were
unlinked. Both immediate filesystem-free and owner-available increases equal
the reclaimed allocation exactly. All independent final verification checks
passed. This is an operational storage result, not a scientific result or a
GPU-launch authorization.

## Exact deletion manifest

All deleted paths have this unchanged original parent:

`/localhome/local-rohing/orch_r188_node2_rehome_20260917t2344z/final_transport/`

| Deleted basename | Logical bytes | Allocated bytes released | SHA-256 of source and surviving copy |
| --- | ---: | ---: | --- |
| `physical1.tar.gz` | 446,285,546 | 446,291,968 | `02573d8662e104cdd2c383cb7faf27cf2e211179d3c393ad067375d599518c5d` |
| `physical4.tar.gz` | 501,934,896 | 501,940,224 | `3630109c365523d4832ae0dff54be60e28daff163d4b0fc7c2ad0ed0baee9fd1` |
| `physical7.tar.gz` | 462,178,412 | 462,184,448 | `8d17625319dc59f999d408d0c6fa74fc6c7f0c5ca9a3b9f5366a2c1a5a51b6a3` |
| **Total** | **1,410,398,854** | **1,410,416,640** | |

The independently verified surviving files retain the same basenames under:

`/data/home/rohing/dream-state-orch/research_loop/workers/rohin174_parenting_20260917/node3/r188/final_relocation_20260917t2350z/`

These are existing archive files, not new ordinary Git blobs. `git ls-files`
returned no tracked entry for any survivor. Nothing was added to Git, moved
onto the VM, extracted to disk, uploaded, committed, or pushed. Protected
checkpoint/optimizer/RNG/history material remains byte-identical inside these
verified surviving archives. The deletion does not claim that these September
17 snapshots cover later September 18 retirement state.

`DELETION_MANIFEST.json` contains every exact absolute source/survivor path,
hash, size, inode identity, link count, timestamps, source bindings, and expected
allocation. It was saved before execution. `PREDELETE_RECEIPT.json` was saved
before the explicit machine acknowledgement permitting the exact unlinks.

## Before/after free-space receipt

Filesystem: original node2 `/dev/nvme1n1p2`, host `ipp2-ovx-p2-08`.
All values below are bytes, from `statvfs`, with 4,096-byte fragments.

| Sample (UTC, September 19) | Owner available | Free including reserves |
| --- | ---: | ---: |
| Immediately before deletion, 21:07:42.093765 | 1,322,688,512 | 39,931,428,864 |
| After unlinks and closing every controlled descriptor, 21:07:42.153342 | 2,733,105,152 | 41,341,845,504 |
| **Immediate increase** | **1,410,416,640** | **1,410,416,640** |
| Independent later read, 21:08:21.709661 | 2,732,843,008 | 41,341,583,360 |

The later 262,144-byte decrease is concurrent filesystem change, not a
retraction of the measured deletion result and not attributed to any process.
Reserves were neither changed nor used as an owner budget. No local reclaim is
claimed. The execution-window local available-space samples are retained in
`DELETION_RECEIPT.json`; local receipt writes and other activity are not remote
reclaim. No persistent Python cache was created; tests used disposable synthetic
temporary fixtures only.

## Safety evidence

- Used only the original `gpu/ovx_ssh.sh` and its existing authenticated node2
  account. No credential files were displayed, copied, borrowed, or changed.
- Fresh SHA-256 of each remote archive and independently read local survivor
  matched before selection. Both sides were rehashed for execution; every local
  survivor was independently rehashed again after deletion. Sizes and full
  file identities stayed bound. `O_NOATIME` avoided changing evidence atimes.
- All 73,255 tar members were validated without extraction. All regular-file
  payloads were streamed; gzip integrity was checked through EOF, and 28
  hardlinks resolved to already validated archive-internal payloads. No
  symlinks, unsafe link targets, or unverified forward links were accepted.
- Original writer scan was clean. The deletion scanner strengthened that
  unchanged scanner to include **all** FD access modes and all mappings.
  Both deletion scans covered 1,514 processes with **zero unresolved entries**.
  The only references were this cleanup's three exact PID/start-time/FD-bound
  read-only descriptors. Any other reader, writer, mapping, changed lifetime,
  or inaccessible live process would have stopped deletion. No genuine
  uncertainty was waived. The historical BATCH88 failure remains unchanged.
- Archive descriptors were held with nonblocking exclusive advisory locks,
  while survivor descriptors were held read-only with shared locks. Locks
  were not substituted for the full process scan. Each original single-link
  inode and anchored parent identity was rechecked immediately before unlink.
  Each unlink removed the last link; all controlled descriptors were closed
  before the final space sample. No mutation ran as root: unlinks used the
  original UID 2524. Existing privileged access was used only for read-only
  process scans; no access-control setting was changed.
- Final independent reads confirmed all three deleted paths absent, all three
  surviving archives unchanged, the original retirement receipt unchanged,
  and the original three `physical*.VERIFIED.json` receipts unchanged.

## Bounded exclusions and remaining candidates

The original report's 11,179 other metadata-matched groups, with a historical
137,367,552-byte allocation ceiling, were **not** fully reinventoried or
declared deletion-ready. Three existing groups, totaling 24 paths, were sampled
read-only and independently content-hashed; their cross-inode payloads matched.
Their potential allocation reduction is only 36,864 bytes. Removing record
paths outright would discard history locations; any subsequent reclamation
must preserve those locations and separately establish full archive coverage,
writer protection, and exact current inode bindings. This task did not
implement or execute a new record coalescer.

The already frozen 515-group plan, its remaining batches, original canary,
live records, preserved histories, failure evidence, reserves, running
processes, leases, and C2 caption/behavior analysis were untouched. No new GPU
run, model change, learning-loop change, or scientific-claim change occurred.
No further cache sweep or deletion is pending in this bounded operation.

## Tests and preserved rejection

`CPU_ARCHIVE_TESTS_2.json`: **17 CPU tests passed**, covering hash mismatch,
missing copies, symlinks, bounds, unsafe archives, valid and invalid hardlinks,
exact archive paths, unresolved live processes, external readers, and exact
controlled read-only descriptor accounting.

The first preparation rejected legitimate tar hardlinks rather than accepting
an unverified archive structure. `PREPARE_REJECTION_1.json` preserves that
failure and its exact member-metadata diagnosis. The non-material parser repair
requires every hardlink to point to an already streamed archive payload;
regression tests cover that rule. Preparation then passed, before any deletion.
No failed live-writer gate was retried, relaxed, or overridden.

`AUDIT_RECEIPT.json` is explicitly the pre-deletion, zero-reclaim audit snapshot;
its zero is not the final outcome. The authoritative execution result is
`DELETION_RECEIPT.json`, independently checked by `FINAL_VERIFICATION.json`.
All local changed paths are enumerated in `CHANGED_PATHS.md`.

## User authorization and scope

This is a non-material operational storage cleanup under the user's explicit
authorization. The material architecture-deliberation path is not invoked;
no scientific invariant or acceptance boundary was changed. Applicable
instructions were checked in the repository scope, archive-survivor ancestors,
and the remote archive ancestors; no additional nested AGENTS instructions
were found in those paths.

Verbatim directive:

> User explicitly authorizes deleting redundant unimportant files, preserving important evidence in repo/archive. Do a bounded storage cleanup audit and, ONLY for conclusively redundant non-live copies with an independently verified surviving identical copy, perform safe cleanup with an exact deletion manifest and before/after free-space receipt. Main is analyzing C2 captions; do not duplicate that. Scope: node2 original gpu/ovx_ssh.sh and existing retired-only candidates in research_loop/workers/replication_sprint_20260919/evidence/node2_recovery/storage/coalescence_remaining/NEXT_RECLAIM_REPORT.md, plus obviously disposable local temporary caches attributable to this work. Do not delete unique checkpoints/optimizer/RNG/histories/failure evidence, mutate live records, alter reserves, borrow credentials, reset processes, or move multi-GB data onto VM. Important bulky state belongs in verified artifact storage, NOT ordinary Git blobs. Respect original retired/live boundaries. If an archive is a candidate, fresh remote + surviving-copy SHA verification is necessary; historical path presence alone isn't enough. Do not waive a genuine live-writer uncertainty or access control. Write code/receipts directly only under research_loop/workers/replication_sprint_20260919/storage_cleanup_20260919_evening/ using apply_patch and list changed paths; no commit/push. Report actual bytes recovered or exact minimal remaining blocker and safe candidates. Read relevant AGENTS. CPU/provenance only; no new GPU runs.
