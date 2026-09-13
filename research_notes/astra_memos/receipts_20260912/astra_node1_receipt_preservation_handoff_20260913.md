# Node1 eleven-receipt preservation handoff — 2026-09-13

**COMPLETE for the authorized eleven-file scope only.** VM preservation and full scoped restore verified at **2026-09-13 14:29:48 UTC**. This closes the eleven small original launcher/failure/finish receipt custody gaps identified in `/tmp/astra_node1_migration_status_20260913_1425.md`; it does not certify the remaining node1 migration.

## Custody location and seals

Fresh destination, created exclusively (no reuse or overwrite):

`/data/home/rohing/dream-state/gpu_artifacts_local/node1_receipt_delta_20260913_attempt1/`

| Object | Description / SHA256 |
|---|---|
| `manifest.json` | Exact eleven absolute node1 source paths, byte counts, SHA256s, VM relative paths, source identity/mtime/ctime observations and provenance bindings. SHA256 `4c2ddeafc25f989efc962bbca3b3f945e9823ea261229b3d21e6b1bf7e417f04` |
| `receipt_delta.tar` | **51,200 bytes**, twelve regular members: the manifest and eleven original payloads. SHA256 `d1926ac3b291639fffed74e79f48ff7e83e5f33a74ea37968ddc2c062de115ba` |
| `verification.json` | `VM_PRESERVED_AND_FULL_SCOPED_RESTORE_VERIFIED`. SHA256 `ac3ef660ff979f14f1fc21558c314a323f4a209186a4564a234ea3f07a5130dc` |
| `native_capture.json` | Original bounded transport envelope, including source observations and base64 payload bytes. SHA256 `1db1bab613b4fc34cc7fddfe1b9a40beab578a6e46cb8dc226cf964db193a959` |
| `input_inventory.json` | Prior report's independently recorded path/size/hash pins, report SHA256, helper SHA256 and approved-wrapper SHA256; written before remote access. |
| `payload/tmp/...` | Eleven original receipt/log files preserving their exact source-relative paths and bytes. |
| `restore_verification/` | Fresh full-scope restore of the archive: the manifest plus all eleven payloads. |
| `transport.stderr` | Empty, zero bytes. SSH/wrapper exit code 0. |

All eleven payloads total **13,555 bytes**. No source file was normalized, repaired or replaced; original failure/log evidence is preserved unchanged. Files were created with restrictive local umask 077. The destination is git-ignored; no tracked repository edits or commits were made.

## Exact authorized source roster

Each source is on node1; each full SHA256 is recorded in `manifest.json` and matches the previously recorded report pin.

| Absolute source path | Bytes |
|---|---:|
| `/tmp/astra_level1_batch_node1_20260913_attempt1.launch/receipt.json` | 193 |
| `/tmp/astra_level1_batch_node1_20260913_attempt1.launch/stdout.log` | 342 |
| `/tmp/astra_level1_a40_fallback_20260913_attempt2.launch/receipt.json` | 523 |
| `/tmp/astra_level1_a40_fallback_20260913_attempt2.launch/stdout.log` | 5,563 |
| `/tmp/astra_level1_batch_node1_parentfix_20260913_attempt1.launch/receipt.json` | 203 |
| `/tmp/astra_level1_batch_node1_parentfix_20260913_attempt1.launch/stdout.log` | 5,563 |
| `/tmp/astra_level1_roster_20260913_attempt1/batch_node1_parentfix/finished.json` | 80 |
| `/tmp/astra_level1_roster_20260913_attempt1/batch_node1/started.json` | 128 |
| `/tmp/astra_level1_roster_20260913_attempt1/batch_node1/prediction_seed0/prepare.log` | 736 |
| `/tmp/astra_level1_roster_20260913_attempt1/batch_node1/prediction_seed0/failure.json` | 144 |
| `/tmp/astra_level1_a40_fallback_roster_20260913_attempt2/batch_node1/finished.json` | 80 |

## Execution and restore verification

1. Parsed only the eleven path/size/SHA256 rows from the existing migration report; asserted exactly eleven distinct paths and 13,555 bytes. Required fresh destination creation. Bound report/helper/wrapper hashes before transfer.
2. Used only existing `gpu/a40_ssh.sh`, with existing host-key checking, no host-key updates and no connection multiplexing. Python was supplied on stdin with `-B`; no remote script, archive or temporary file was created. No node2 connection occurred.
3. Read only the eleven authorized regular files, rejecting symlink paths/nonregular files and oversized inputs. Checked descriptor/path inode/device/size/mtime/ctime stability around each read. Matched every payload to its prior report size/SHA256, then reread all eleven to verify unchanged identities and hashes across the bounded capture.
4. Native stable-read window: **14:29:48.259698–14:29:48.260697 UTC**. This records sequential stable reads, not a general atomic whole-node snapshot. Transport output was preserved locally. VM decoding, writes and subsequent rereads all matched the independent pins.
5. Built the fresh tar from the exact manifest and eleven payloads. Validated precisely twelve unique regular members, exact member roster, no absolute/escaping member paths, and no links/special files. Restored every member into the fresh `restore_verification/` directory without unrestricted tar extraction.
6. Verified all **11/11 restored payload lengths and SHA256s**, plus byte-identical restored manifest. A separate local verification pass independently reparsed the original report pins and compared the manifest, tar member roster/payloads, preserved VM payloads and restored files. **PASS: 11 files / 13,555 bytes**. Archive and manifest hashes also match the final verification receipt. No failure marker exists.

Helper retained for provenance: `/tmp/astra_node1_receipt_preserve_20260913.py`. It is fresh-only and must not be rerun against this completed attempt directory. No additional native collection or retry is needed for these eleven files.

## Scope and next action

- No remote writes/deletions, GPU commands, job/process inspection or signaling, model calls, heavy artifacts, node2 SSH, or original receipt modification. Only the eleven authorized source files were read/transferred; the nine other support files and adapters from the earlier assessment were deliberately excluded.
- Verification is complete for these eleven payloads and their restore, **not** for the old baseline mirror, all node1 artifacts, or permanent off-VM retention. The earlier report remains an immutable earlier assessment; this handoff closes its eleven-receipt gap without editing it.
- Main/preservation owner should incorporate this capsule and verification receipt into the consolidated migration ledger. Arrange onward custody only after coordination; **no node2 copy is claimed**. Preserve the capsule directory together, including its provenance/verification records, rather than copying only loose logs.
- Overall preservation deadline remains **September 13, 2026, 23:14 UTC**; reported lease expiry is **September 14, 2026, 23:14 UTC**. Remaining baseline/restore/onward-custody questions from the broader assessment are unchanged.
