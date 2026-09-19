# Next retired-only capacity cut — 2026-09-19 15:43 UTC

**No additional archive-verified reclaim is ready.** This read excludes all
4,120 paths selected by the frozen 515-group plan, including the executed canary.
The remaining manifest and runner are unchanged; this worker did not execute them.

## Source-bound inventory

- `../NEXT_RETIRED_20260919T1543.json`: metadata-only census of the five lives in
  the exact original `PRESERVATION.public.json`, SHA256
  `9481707cb24918cfa54b1da663ec8c6ca0a576697e2a79c10913b5f013f9f52c`.
- 11,179 additional matching-metadata groups total **137,367,552 potential
  allocated bytes**. Content equality is not established, and they are outside
  the fully verified 515-group archive. Even their entire metadata ceiling is
  insufficient to close the C0 gap. No large additional non-checkpoint file was
  found at the bounded retired-root/stream/preservation directory levels; the
  largest were required preservation inventories, not verified duplicate copies.
- Three old transport archives occupy **1,410,416,640 allocated bytes** under
  `/localhome/local-rohing/orch_r188_node2_rehome_20260917t2344z/final_transport/`:
  `physical1.tar.gz`, `physical4.tar.gz`, and `physical7.tar.gz`. Their declared
  VM copies exist under
  `research_loop/workers/rohin174_parenting_20260917/node3/r188/final_relocation_20260917t2350z/`.
  Presence is not fresh verification. These archives contain protected checkpoint
  material, have different recorded payload hashes, and are **not an additional
  same-filesystem identical-file group eligible for the current coalescer**.
  No payload was opened, moved, removed, or rewritten. Any proposed cleanup needs
  a separately reviewed scope and current copy/restore/in-use evidence; it is not
  authorized by the remaining-batch binding.

## Owner capacity, not filesystem free space

`CAPACITY_THRESHOLD_20260919T1541.json` records a read-only `statvfs` and
`tune2fs -l` check of `/dev/nvme1n1p2` (ext4); no reservation was changed or used.

- At **15:41:20.827 UTC**, `bfree=9,370,340`, `bavail=0`, `frsize=4,096`.
  Free space including reserves: **38,380,912,640 bytes**; owner available: **0**.
- Superblock reserved blocks: **9,421,866**, block size **4,096**; reserved
  threshold: **38,591,963,136 bytes**. The superblock-reserve deficit was
  **211,050,496 bytes**, not zero.
- Remaining selected release is **1,831,120,896 bytes**, not all available to the
  owner. Ignoring future writes and any additional allocator/other limits gives
  an optimistic owner ceiling of **1,620,070,400 bytes** and an optimistic C0
  shortfall of **1,361,066,464 bytes** against its **2,981,136,864-byte** budget.
- The five-second pre-batch sample consumed **28,672 bytes** net, about
  **5,716 bytes/second**. This is short-window filesystem change, not a process
  attribution or a reliable long-horizon growth forecast. From the earlier
  15:12 metadata cut to this cut, allowing for the known 10,444,800-byte canary
  release, observed net consumption was **209,088,512 bytes**; other filesystem
  activity is not independently classified.
- At **15:43:28.311 UTC**, the next-set census still reported owner available
  **0**, and free space including reserves **38,413,479,936 bytes**. Main's
  concurrent batch execution can affect this value, so this is not used as a
  growth estimate or a substitute for Main's final post-batch capacity receipt.

## Blocker

The currently proven archived duplicate set is exhausted by the already frozen
plan. Within this bounded retired-only read, there is no proven extra source
large enough for C0. Do not stage C0 or promise 1.84 GB of owner headroom based on
allocated-byte release. The next decision requires a separately identified and
verified retired-only source; root reserves and live/model/checkpoint changes
remain excluded.
