# Node1 expiry reconciliation — September 14, 2026

Requested 12:53 UTC; observations collected **12:54:43–12:59:14 UTC**.
Read-only reconciliation, not a transfer, restore, experiment, or lease action.

## Decision and deadline

**No uncovered run artifact was identified in the documented Node1 preservation scope. No additional transfer or job is indicated.** Keep the existing preserved copies; do not rerun the mirror or the completed verification workers.

Node1 lease end is **September 14, 2026, 23:14 UTC**, per the current user instruction and the recorded handoff. This was not independently checked with the provider. The **September 13, 23:14 UTC preservation deadline** in the earlier note is a different, already-passed checkpoint, not today's lease expiry. Main has directed no new work to Node1; current repair cells are not Node1 preservation dependencies.

Only this note was authored. Trainer/tests, driver, notebook, other contributors' edits, and Git state were not modified. No transfers, extractions, background workers, experiment jobs, model loads, GPU commands, lease operations, or commits were performed. Remote checks were bounded foreground filesystem reads through existing wrappers; endpoints and credentials are deliberately omitted.

## Evidence chronology: the old baseline caveat is closed

1. `research_notes/analysis/2026-09-13_node1_preservation_readiness_2133Z.md` concluded that the documented Builder payload had no demonstrated missing transfer. It retained a **count-only full-baseline limitation**, while separately closing the delta, twelve Level1 adapters, support receipts, and prediction claims.
2. **SEQ-198**, recorded in `research_loop/COORDINATION.md` under **2026-09-14T04:43Z**, supersedes that particular limitation. Independent full-file hashes of Node1 `v6_out` and the existing Node2 mirror completed at **04:25:10 UTC** and **04:25:20 UTC**. Each contained **15,428 regular files / 96,975,926,735 bytes**, with zero missing, extra, payload/type, or metadata differences. This required no transfer.
3. The later watcher entries, including **12:33 UTC**, continue to report Node1 idle and mirror complete. These reports support chronology, not a substitute for the checks below.

Canonical baseline receipt directory:
`gpu_artifacts_local/node1_baseline_verification_20260914_attempt1/`.

Fresh local checks matched the notebook-pinned terminal receipt and its referenced comparison, evidence files, both saved inventories, and initial/final rosters:

| Evidence | SHA256 |
|---|---|
| `terminal_validation.json` | `3f21e04a8037d6c12b2f4882bf1fddc2a052a674129a11d088130e19901d98f5` |
| `comparison.json` | `ed6efa98a11573ca683e2a6fc0a084a2de37513d292279ba4a25243bc6904aa3` |
| Both `node{1,2}_portable_payload_inventory.jsonl` files | `6027a4d1cf06302e656cfbf19ccd88bdb72a564af8efa56eaf2db7e0bd1e836c` |

The two portable inventories were also independently parsed and compared as `relative_path -> (size_bytes, sha256)`: **15,428 matching entries**, summing to the recorded per-node byte count. This revalidates the retained evidence, not a new 97 GB payload rehash.

## Current storage observations

### Baseline source and surviving mirror

Two bounded metadata reads compared every current regular-file path and stat record with that node's saved final roster. The comparison covered size, mode, device, inode, ownership, link count, mtime and ctime; atime was deliberately excluded.

| Location | Observation UTC | Files / bytes | Saved/current regular-file metadata | Files newer than 04:25:20 UTC |
|---|---|---|---|---:|
| Node1 `/localhome/local-rohing/v6_out/` | 12:58:07–12:58:08 | 15,428 / 96,975,926,735 | Exact match | 0 |
| Node2 `/localhome/local-rohing/mirror/node1_v6_out_2026-09-12T23/` | 12:58:09–12:58:10 | 15,428 / 96,975,926,735 | Exact match | 0 |

Both reads completed without scan errors. Digest construction was SHA256 of compact JSON containing the sorted list of `[relative_path, stat_values]`; stat fields, in order, were `st_ctime_ns`, `st_dev`, `st_gid`, `st_ino`, `st_mode`, `st_mtime_ns`, `st_nlink`, `st_size`, `st_uid`.

- Node1 saved/current digest: `92d486b94a943c4bce200b1e9e04611a47fe31dae814dd8fb79d01807fb77311`.
- Node2 saved/current digest: `62967b092bd8c7a5cd9029b65549a49e055744c9b190c4714c788759f6a03e2d`.

Different per-node metadata digests are expected because device/inode/ctime are node-local. Each matches its own earlier roster; payload equality is separately established by the matching saved payload inventories. No full-baseline hashing job was repeated.

### Scoped archives and receipts still survive

**55/55 local SHA256 pin checks passed**, including all 29 objects in the onward manifest, the baseline evidence chain, the delta archive, and all three prediction archives. The local archive bytes, not merely their lengths, were freshly hashed.

| Preserved payload | Fresh verification | Recorded SHA256 |
|---|---|---|
| VM `gpu_artifacts_local/node1_delta_20260913/astra_node1_delta_20260913_attempt1.tar` | 2,413,762,560 bytes, match | `f01a1526254c7b12924191694f71ada143c31edbaee77dcc0ebc6860ba385118` |
| VM `gpu_artifacts_local/level1_first_roster_20260913/node1/node1_first_roster.tar` | 504,350,720 bytes, match | `0d822a18838314346f1fa332ad4ac71234e1d20e59e7f841d81109a1f23226d1` |
| VM `gpu_artifacts_local/level1_second_roster_20260913/node1_second_repetition.tar` | 254,648,320 bytes, match | `b2e4cf8931afa5fb03768658d4e5cd2aef07db563476c53d2a16f3bb1e7ca6f6` |
| VM `gpu_artifacts_local/level1_second_roster_20260913/meta_reflection/node1_second_meta_reflection.tar` | 258,232,320 bytes, match | `1b69ccab8dd8612767dc0fa2139f934acc09e0ee5bde48181345044879599dc9` |
| VM `gpu_artifacts_local/node1_receipt_delta_20260913_attempt1/receipt_delta.tar` | 51,200 bytes, match | `d1926ac3b291639fffed74e79f48ff7e83e5f33a74ea37968ddc2c062de115ba` |
| VM `gpu_artifacts_local/prediction_transfer_primary_20260913/evidence.tar` | 17,520,640 bytes, match | `365cfdbe817c41f5bedf4099a35d0e836d788eeec75edc687addc92dfb295b69` |
| VM `gpu_artifacts_local/prediction_transfer_20260913_attempt1/evidence.tar` | 17,264,640 bytes, match | `0928686137e8a61db60cc91952c407920117e136285b847ee71a8afa68e508bf` |
| VM `gpu_artifacts_local/node1_prediction_claims_20260913_attempt1/evidence.tar` | 10,240 bytes, match | `70e0887801f8e47e6e9934f81b18a6433f5135fd7b6104eed9b1fbe0757bfe34` |

Independent current destination reads also passed, using no-follow/no-atime file opens and SHA256, without extracting or copying anything:

- **Node2 delta**, `/localhome/local-rohing/mirror/node1_delta_20260913_attempt1/astra_node1_delta_20260913_attempt1.tar`: **1/1**, 2,413,762,560 bytes, same delta hash, **12:59:12–12:59:14 UTC**. The retained delta roster covers the earlier 348 changed baseline files plus **419 executed-source files** outside `v6_out`.
- **Node3 onward destination**, `/localhome/local-rohing/mirror/node1_onward_20260913_attempt1/`: **29/29 objects**, 1,018,616,159 bytes, matching each manifest pin, **12:59:10–12:59:11 UTC**. This includes the three Level1 capsules, eleven-receipt capsule, their supporting receipts, and nine support files.

Onward evidence remains under `gpu_artifacts_local/node1_onward_node3_20260913_attempt1/`. Both local manifests hash to `63264ed62c9cf4a7d0d4becc0549290b77568202d49f3931d1e77c1c47cca9c1`. The recorded September 13 custody receipt reports four scoped restores / 3,490 regular members; this audit checked current archived objects but **did not repeat those restores**. The newer prediction archives are not claimed to be included in that 29-object Node3 bundle.

## Artifacts since preservation

A **12:58:37 UTC** Node1 metadata scan inspected **37 scoped roots**: `astra_sources`, `astra_diagnostics`, the possible `astra_writer_roots`, and existing `/tmp` entries prefixed `astra_`, `prediction_transfer`, or `node1_baseline_verification`. The cutoff was the earlier readiness observation, **September 13, 21:33:06 UTC**—earlier than today's baseline check.

- `astra_sources`: **419 regular files / 11,018,858 bytes**, none with later mtime/ctime.
- `astra_diagnostics`: **4,548 regular files / 1,016,392,022 bytes**, none with later mtime/ctime.
- `astra_writer_roots`: absent; no absence was filled with invented evidence.
- The only later files found were **nine preservation-verification files**, not new science output, under `/tmp/node1_baseline_verification_20260914_attempt1/`: `initial_roster.jsonl`, `final_roster.jsonl`, `inventory.jsonl`, `summary.json`, `launch.json`, `scope.json`, `runner.log`, `inventory.py`, and `started.json`.
- Those nine files already exist in the VM baseline receipt directory's `node1/` subdirectory. A fresh **12:59:09 UTC** source-versus-VM SHA256/size comparison passed **9/9**, totaling **26,855,200 bytes**. They therefore introduce **no uncovered delta**.
- No scan errors were reported. The home-directory `astra_*` entries were the already-known diagnostics, sources, delta archive and delta pack receipt.

## Smallest action and limits

**Smallest required action now: none.** Retain the surviving VM capsules and Node2/Node3 copies. Do not recopy closed gaps, rerun verification workers, move live repair cells, or delay current science for a new custody exercise.

If someone subsequently writes Node1 run evidence before **23:14 UTC**, only that newly identified stable delta needs preservation, with exact path/size/hash and a destination check. No such payload was found here. The later prediction bundle's current VM copy is verified; an additional off-VM copy would be optional redundancy, not repair of a demonstrated Node1-expiry gap.

This is scoped evidence, not certification of every owner's files or indefinite custody. The fresh baseline check compared regular-file metadata with previously hashed payloads; it did not rehash 97 GB, validate every directory/symlink, provide an atomic snapshot, or run application restores. Supplemental late-change scanning is not a historical deletion audit and excludes unrelated paths. Node2/Node3 are themselves leased; permanent archival guarantees and provider lease terms were not reverified. These limitations do not reopen the specific closed transfer gaps.
