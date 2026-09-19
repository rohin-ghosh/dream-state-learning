# Storage recovery options for Main review — September 19, 2026

**Read-only census complete; no files removed, archived, moved or overwritten.**
The latest disk read at approximately 13:28UTC still has zero owner-available
bytes. Node3 natives remain absent. This document does not authorize cleanup.

## Cache candidates: exact bounded reference checks

| Exact path | Allocated bytes | Classification |
| --- | ---: | --- |
| `/localhome/local-rohing/.triton/cache` | 14,057,472 | generated compiler kernels/intermediate representations; review before removing |
| `/localhome/local-rohing/.cache/flashinfer` | 6,791,168 | generated compiler/runtime cache; review before removing |
| `/localhome/local-rohing/.cache/matplotlib` | 176,128 | generated font metadata; review before removing |

Total: **21,024,768 bytes, about 20MiB**. All three are real directories owned by
UID2524, not symlinks. `CACHE_REFERENCE_AUDIT.json` records 547 individual file
hashes, sizes, realpaths, ownership, and scan scope. Exact-path searches found
zero references in **1,619 original pinned source/control files**, with no
file-size omissions. No readable owner process FD referenced these directories.
Five process FD inspections were inaccessible or raced with exit, so universal
absence of live use is **not** claimed. Compiler packages can also resolve
their default caches dynamically: a missing literal reference is not a proof
that a cache will never be used again.

**Recommendation:** do not spend the recovery window deleting these tiny caches.
Even if Main approves and fresh reference checks clear them, they offer only
20MiB and may regenerate immediately. This is not a sufficient bootstrap for
a 155MiB optimizer file, adapter files, tens-of-MiB state records and continuing
eight-life journal growth. The filesystem's reserved blocks are not ordinary
owner headroom; deleting a small cache cannot be assumed to make `f_bavail`
positive. No reserve change is proposed.

Pip, uv, npm, Maven, Gradle, torch-download and torch-extension cache directories
at the checked owner-default paths are absent. `/tmp/torchinductor_local-rohing`
is only 4,096 bytes. Other owned `/tmp` entries are experiment bundles, dumps,
operator scripts, sockets or run directories, not disposable downloads.

## Explicitly protected: not cleanup candidates

| Exact path or family | Allocated bytes | Why preserved |
| --- | ---: | --- |
| `/localhome/local-rohing/v2/venv` | 8,613,822,464 | original native's interpreter and packages; native traceback confirms use |
| `/localhome/local-rohing/.cache/huggingface/hub/models--Qwen--Qwen2.5-7B-Instruct` | 15,242,907,648 | every original kept PLAN binds its snapshot `a09a35458c702b33eeacc393d103063234e8bc28` |
| `/localhome/local-rohing/.cache/huggingface/hub/models--Qwen--Qwen2.5-14B-Instruct` | 29,551,820,800 | model cache, not disposable download; historical/recovery dependencies not cleared |
| `/localhome/local-rohing/.local/share/compiler_gym` | 1,503,227,904 | LLVM binaries, benchmark datasets and runtime inputs, not an expendable cache |
| `/localhome/local-rohing/astra_diagnostics` | 18,068,537,344 | experiment results and tensors |
| `/localhome/local-rohing/research_loop` | approximately 22.7GB | prior experiment workers and preserved state |
| `/localhome/local-rohing/mirror` | 2,038,382,592 | restore-verification and capsule evidence |
| `/localhome/local-rohing/astra_sources` and original per-life source roots | approximately 6.16GB plus per-life copies | operator code/provenance; pinned bundles remain protected |

All eight kept roots, checkpoint files, journals, pending-row sources, inboxes,
failed checkpoint attempts, partial intents and control receipts remain intact.
No current or historical model was reclassified as removable simply because
its GPU process is absent.

## Lossless archival candidates: preserve, do not delete

All paths below start with `/localhome/local-rohing/orch_r205_node3_20260918/`.

| Directory | Allocated bytes | Evidence and limitation |
| --- | ---: | --- |
| `r225_siege_retirement_20260918` | 37,055,873,024 | pre-signal and final preserved siege copies; contains checkpoint and journal evidence |
| `r233_retirement_20260918T1144Z` | 20,625,596,416 | `RETIREMENT.json` plus per-life rows and preserved directories |
| `r224_challenger_retirement_20260918` | 9,074,589,696 | preserved challenger retirement; not failed-run trash |

The exact-path check found no references from the eight kept original controls
and pinned sources, and no readable owner FD under these three archives. This
does **not** clear references from every historical audit/probe or another host.
Allocated sizes are not guaranteed reclaim amounts or compression estimates.

For a concrete first archive, the scout's
`r225_siege_retirement_20260918/r213_siege_scout_fork/pre_signal` copy is about
5.266GB. Its raw data contains **4.129GB of checkpoints** and **1.121GB of stream
data**, so treating the entire copy as highly compressible JSON would be wrong.
The neighboring `FINAL_MANIFEST.json` has 4,416 file entries and declares
`raw_tail_unchanged: true`; all contents must be verified against their exact
own copy before any archival promotion. An original-versus-copy JOURNAL stat
shows different inodes with link count1, not an assumed hardlink alias.

### Existing-storage constraint

Already mounted on node3: the full ext4 root; its read-only system bind;
the EFI boot volume; and tmpfs/system virtual mounts. **There is no separate
mounted durable data volume with writable headroom.** EFI is a boot partition,
not a research-archive destination. RAM/tmpfs is not durable storage. Autofs
mountpoints are not evidence of an existing accessible archive volume; none
was triggered. `tar`, `gzip`, `xz` and `zstd` are installed, but installing or
launching a new storage service is neither necessary nor authorized.

Small cache removal cannot be advertised as enough room to stage an archive.
Writing a same-volume compressed copy with zero owner headroom is not a viable
plan. A VM extraction is also inappropriate: the VM must retain code/receipts,
not multi-GB copies of the node's experimental data.

### Proposed lossless archive procedure — not executed

1. Main designates an owned durable destination with measured headroom on
   **existing leased storage**, if one exists, and approves the exact retired
   copy and scope. No new service, lease or mount is proposed here.
2. Recheck process identities, source immutability, references and ownership;
   record a complete per-path SHA256/size/mode/owner/timestamp/symlink manifest.
3. Stream a lossless archive directly to that destination, retaining originals.
   Preserve file names, raw bytes, hardlink/symlink relationships, permissions,
   relevant xattrs and original retirement manifests. Never import credentials.
4. Verify the destination archive hash and independently extract/stream-check
   every member against the source manifest. Retain both source and destination
   identities, checksums and a tested restoration procedure as small receipts.
5. **Archiving alone does not recover source capacity.** Source removal,
   replacement or remapping is a separate explicit Main decision and is not
   authorized by this workstream's no-deletion instruction. Protected journals,
   checkpoints and failed artifacts must never silently disappear.

The concrete question for Main is therefore destination and preservation scope,
not permission to delete an apparent 44.8GB “cache.” That 44.8GB is model data.

## Receipts

- `STORAGE_CENSUS_20260919.txt`, `STORAGE_DETAIL_20260919.txt`
- `STORAGE_RETIRED_AND_TEMP_20260919.txt`, `STORAGE_CACHE_CHECKS_20260919.txt`
- `CACHE_REFERENCE_AUDIT.json`: exact cache file hashes and bounded reference checks
- `STORAGE_ARCHIVE_CANDIDATES_20260919.txt`, `STORAGE_ARCHIVE_LAYOUT_20260919.txt`
