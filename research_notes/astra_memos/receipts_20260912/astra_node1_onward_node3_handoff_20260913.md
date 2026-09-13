# Node1 bounded onward preservation to node3 — September 13, 2026

**COMPLETE for the requested scope.** Transfer finished **14:41:28 UTC**; node3 full scoped restore verification passed **14:41:33 UTC**; persisted destination receipts were independently read back to VM at **14:41:55 UTC**. No node2 SSH occurred.

## Destinations and custody seals

Fresh surviving node3 destination:

`/localhome/local-rohing/mirror/node1_onward_20260913_attempt1/`

Fresh VM execution/receipt directory:

`/data/home/rohing/dream-state/gpu_artifacts_local/node1_onward_node3_20260913_attempt1/`

Transferred **29 scoped objects / 1,018,616,159 bytes**, plus the **10,764-byte onward manifest**. This includes exactly the three newest Level1 archives (**1,017,231,360 bytes**), their twelve associated metadata/receipt files, five eleven-receipt custody objects, and nine support files (**47,447 bytes**). No full ~97 GB baseline recopy.

| Persisted node3 object, relative to destination | SHA256 |
|---|---|
| `onward_manifest.json` | `63264ed62c9cf4a7d0d4becc0549290b77568202d49f3931d1e77c1c47cca9c1` |
| `transfer_receipt.json` | `aafe6f2a137f13310d4ca23d94e651b0c887f7a59527bc845a7ceb7e0269602f` |
| `verification.json` | `c89444c64fd2b07d6e1590bd03e82b51c64cae602f5a63601c2db92b48dce140` |
| `storage_precheck.json` | `82e6fe100020fcf42fbc5c72c4ea0ce0df4247b1a95c11ba5a6338b9875bca02` |

The onward manifest maps **every exact VM source path to its node3 relative destination, size and SHA256**. It is byte-identical on VM and node3. Remote persisted receipts were read back byte-for-byte and saved locally as `node3_onward_manifest.json`, `node3_transfer_receipt.json`, `node3_verification.json`, and `node3_storage_precheck.json`. The final local summary is `final_custody_receipt.json`. The raw verification command output is separately preserved as `verify.json`; its JSON serialization differs from the remote persisted receipt, so use the persisted receipt hash above for that object.

## Four archives, unchanged bytes

Paths below are relative to the exact node3 destination above.

| Archive | Bytes | Source and node3 SHA256 |
|---|---:|---|
| `capsules/first_roster/node1_first_roster.tar` | 504,350,720 | `0d822a18838314346f1fa332ad4ac71234e1d20e59e7f841d81109a1f23226d1` |
| `capsules/repetition/node1_second_repetition.tar` | 254,648,320 | `b2e4cf8931afa5fb03768658d4e5cd2aef07db563476c53d2a16f3bb1e7ca6f6` |
| `capsules/meta_reflection/node1_second_meta_reflection.tar` | 258,232,320 | `1b69ccab8dd8612767dc0fa2139f934acc09e0ee5bde48181345044879599dc9` |
| `capsules/eleven_receipts/receipt_delta.tar` | 51,200 | `d1926ac3b291639fffed74e79f48ff7e83e5f33a74ea37968ddc2c062de115ba` |

VM sources for the three Level1 archives, unchanged:

```text
/data/home/rohing/dream-state/gpu_artifacts_local/level1_first_roster_20260913/node1/node1_first_roster.tar
/data/home/rohing/dream-state/gpu_artifacts_local/level1_second_roster_20260913/node1_second_repetition.tar
/data/home/rohing/dream-state/gpu_artifacts_local/level1_second_roster_20260913/meta_reflection/node1_second_meta_reflection.tar
```

Each Level1 destination directory also contains `node1_archive_manifest.json`, `node1_archive_listing.txt`, and `node1_native_receipt.json`. Its VM receipt is `vm_verification.json` for `first_roster`, and `node1_vm_verification.json` for the other two. The first-roster native receipt came from the source directory's parent `level1_first_roster_20260913/node1_native_receipt.json`; this relocation is explicit in the onward manifest.

`capsules/eleven_receipts/` also contains the original `manifest.json`, `verification.json`, `input_inventory.json`, and `native_capture.json` from VM `gpu_artifacts_local/node1_receipt_delta_20260913_attempt1/`. Its manifest remains sealed at `4c2ddeafc25f989efc962bbca3b3f945e9823ea261229b3d21e6b1bf7e417f04`; original verification remains sealed at `ac3ef660ff979f14f1fc21558c314a323f4a209186a4564a234ea3f07a5130dc`. Eleven original source receipt/log payloads total 13,555 bytes. Original failure evidence is unchanged; no successful replacement receipt was synthesized.

## Nine former VM /tmp support counterparts

Each exact source `/tmp/...` is stored as `support/tmp/...` beneath the node3 destination. All nine matched their previously recorded node1/VM equality hashes before transfer and were rehashed on node3. No new node1 read was necessary.

```text
/tmp/astra_level1_batch_node1_parentfix_20260913.py
/tmp/astra_level1_batch_20260913.py
/tmp/astra_level1_perception_reflection_material_20260913.py
/tmp/astra_level1_roster_20260913_attempt1/update_judgement_seed0.json
/tmp/astra_level1_roster_20260913_attempt1/update_judgement_seed1.json
/tmp/astra_level1_roster_20260913_attempt1/update_judgement_seed2.json
/tmp/astra_level1_roster_20260913_attempt1/contradiction_seed0.json
/tmp/astra_level1_roster_20260913_attempt1/contradiction_seed1.json
/tmp/astra_level1_roster_20260913_attempt1/contradiction_seed2.json
```

Exact sizes and all nine SHA256s are in the sealed onward manifest. They are no longer evidenced only by transient VM `/tmp` copies; a verified node3 mirror copy now exists.

## Verification actually performed

- **Storage/freshness:** node3 preflight at 14:40:36 found the proposed destination absent, its existing ancestor writable, **800,477,016,064 free bytes** and **58,057,632 available inodes**. Freshness and capacity were rechecked immediately by the receiver. Required free space was at least three times selected transfer bytes plus 1 GiB, comfortably allowing full scoped restores. At final readback, **798,438,408,192 bytes remained free**. These are filesystem observations, not a provider quota or lease guarantee.
- **Source pins:** recomputed SHA256s of all four VM archives against independent recorded pins; source manifests/listings against their existing receipt pins; nine support files against prior recorded node1/VM equality pins. All 29 sources were hashed with stable local inode/size/mtime/ctime checks. Source payloads were neither rewritten nor deleted.
- **Transfer:** streamed only an explicitly enumerated tar over approved `gpu/ovx2_ssh.sh`; no staging copy of the gigabyte bundle on VM, no direct host addresses in command logs. Receiver exclusively created the fresh destination, required the independently pinned onward manifest, rejected unexpected/duplicate/nonregular/escaping file entries, and verified each destination size/hash. No unrestricted extraction or overwrite of an existing mirror.
- **Destination rehash:** separately reread and rehashed all 29 transferred objects. All four archive hashes match their original pins at both ends.
- **Full scoped restores:** validated each archive's regular-member roster against its own manifest, rejected duplicates and unsafe paths/types, and wrote every regular member to a fresh isolated restore directory. Rehashed all restored payloads against their original manifest. Level1 total archive-member counts match the native manifests. No adapter loading, GPU use, scoring or model execution.

| Restore directory, relative to node3 destination | Regular files restored and verified | Total archive members |
|---|---:|---:|
| `restore_verification/first_roster/` | 1,730 | 1,784 |
| `restore_verification/repetition/` | 874 | 901 |
| `restore_verification/meta_reflection/` | 874 | 901 |
| `restore_verification/eleven_receipts/` | 12: eleven payloads plus manifest | 12 |

**3,490 regular archive members fully restored and hash-verified**, including the eleven-receipt manifest, plus the nine standalone support files rehashed. These counts describe archive members, not globally deduplicated scientific observations: overlapping source/runtime evidence across capsules remains preserved separately. Empty directory restoration and filesystem permissions/ownership fidelity are not claimed; payload path/byte fidelity is verified for every regular member.

## Command logs, interruption, and boundaries

Local `commands.jsonl` records exact approved-wrapper argv, executed inline helper code, CWD and timestamps for node3 check, receive, verify and metadata readback. Outputs and stderr files are retained; successful command stderr files are empty. Helper: `/tmp/astra_node1_onward_node3_20260913.py`, with its executed hash bound in the onward manifest and full executed source retained in the command log.

An initial local shell time limit interrupted source hashing **before any transfer or remote writes began**. Only the read-only capacity check had completed. `pretransfer_interruption.json` preserves that fact. Resume was permitted only from the exact three-file local pre-transfer checkpoint and performed one transfer into the still-fresh remote directory; no completed/partial destination was overwritten or deleted.

No node2 SSH, GPU/job/process actions, model calls, source deletion, credentials/connection settings disclosure, tracked repository edits or commits. The new VM evidence directory is git-ignored. Existing capsules, original receipts, sources and other agents' files remain untouched. This handoff is for Main to log; no notebook edit was made here.

## Remaining full-mirror limitations

This establishes **node3 onward custody of the requested newest evidence**, including full scoped restores, before the **September 13, 2026, 23:14 UTC** preservation deadline. It does not certify the older ~94.6 GB full mirror or ~97 GB node1 tree, reconcile all later writers, or copy the old 2.4 GB delta to node3. The historical baseline-plus-delta full-coverage/hash/restore questions in the migration assessment remain open. Node3 is a surviving leased node, not a guarantee of permanent storage; no fresh provider lease validation or indefinite off-lease custody is claimed.

Main's next action: register the sealed onward manifest and node3 verification receipt in the consolidated migration ledger, retain both VM and node3 copies, and separately resolve the older full-mirror/late-write/permanent-custody scope without interfering with node2's live formation.
