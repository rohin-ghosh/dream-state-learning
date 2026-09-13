# Node1 evidence migration readiness — September 13, 2026

Assessment requested for 14:25 UTC; finalized approximately **14:28 UTC**. Fresh node1 inventory at **14:26:16.977498 UTC**. All dates/times below are UTC.

## Decision and most urgent action

**Substantial preservation demonstrated; complete migration NOT yet certified.** No newly discovered unpreserved adapter or diagnostic-root ledger in the bounded inventory. All twelve newest node1 adapters and all 3,372 current diagnostic-root files are covered by three previously payload-verified VM archives; fresh source names/sizes and local manifest/listing hashes agree. This is not a fresh payload rehash or restore.

**Most urgent concrete action:** the preservation owner should capture the eleven small original launcher/failure/finish receipts listed in §3 (13,555 bytes total), or produce an existing exact-byte custody receipt, then close the consolidated coverage and restore-verification record before **September 13, 2026, 23:14 UTC**. Do not wait until the lease expires. Arrange onward custody of the three newest VM capsules and transient VM-only support files, without overlapping Main's release-sensitive node2 SSH window.

About 8h46m remain at report time. The preservation deadline is **September 13 23:14**; reported node1 lease expiry is **September 14 23:14**, and its six-hour finish cutoff is **September 14 17:14**. These are distinct. Lease dates come from handoff/runbook, not a fresh provider verification.

## 1. What was actually checked

- Read the living handoff, current coordination, node12 inventory, preservation plan/execution, exact-delta handoff and existing verification receipts. Current coordination still describes a final incremental mirror as future work, not completed verification.
- Used `gpu/a40_ssh.sh` only for bounded node1 filesystem metadata and SHA256 of twenty small, specifically identified Level1 support files (61,002 bytes total). No payload/log contents or secrets were displayed. No GPU/process/environment inspection, job action, artifact transfer, or remote file writes.
- Earlier fresh metadata inventory at 14:23:49 found `/localhome/local-rohing/v6_out/` at 15,428 files and `/localhome/local-rohing/astra_sources/` at 419 files, with no file mtimes newer than the 04:45:57 delta-pack cutoff and no scan errors. `/localhome/local-rohing/astra_writer_roots/` was absent. Counts/mtimes cannot establish byte identity.
- At 14:26:16, enumerated `/localhome/local-rohing/astra_diagnostics/` plus narrowly scoped `/tmp/astra_level1*`: 3,482 files, no scan errors. All **3,372 diagnostic files** are present in the union of three archive manifests with matching lengths; **zero uncovered diagnostic paths, zero size mismatches**.
- Freshly hashed each local capsule's manifest and listing against its saved verification receipt; all six checks match. All three local archive lengths match. Did **not** reread/hash ~1 GB of archive payloads or ~97 GB of old source data.
- No node2 SSH: Main's current own-write stage is release-sensitive and a same-UID observer SSH process can interfere with CVD scanning. No own-write/manuscript work was performed. No repo edits, commits, heavy copies or models.

## 2. Demonstrated custody and newest required evidence

### Older v6_out plus executed-source evidence

Historical full mirror:

- Source `/localhome/local-rohing/v6_out/`.
- Destination node2 `/localhome/local-rohing/mirror/node1_v6_out_2026-09-12T23/`.
- Fable reported rsync rc0 at September 12 23:40: 15,082 destination files / 94,574,269,022 bytes, 218/218 top-level entries. One then-live source ledger delta was acknowledged. This is historical transfer evidence, not full member-hash/restore certification.

The later **04:47 exact delta closes the documented 04:32 differences**, including seven adapters. Do not list those seven as still missing:

- VM `gpu_artifacts_local/node1_delta_20260913/astra_node1_delta_20260913_attempt1.tar`.
- Node2 `/localhome/local-rohing/mirror/node1_delta_20260913_attempt1/astra_node1_delta_20260913_attempt1.tar`.
- Archive 2,413,762,560 bytes; SHA256 `f01a1526254c7b12924191694f71ada143c31edbaee77dcc0ebc6860ba385118`.
- 767 payload files: 348 v6_out files and 419 executed-source files under `/localhome/local-rohing/astra_sources/0babc3ccbe1f2378a61dd0dac6f18f7371b82176/` and `/localhome/local-rohing/astra_sources/125ba29df6e1060e4e412742459dd75217193d2e/`; embedded roster makes 768 members.
- VM verified 04:46:51; node2 verified 04:47:53. Both receipts say `DELTA_VERIFIED`, full member bytes verified, extraction not performed, scope `DELTA_ONLY_NOT_FULL_MIRROR_RESTORE`.
- Exact roster `/tmp/astra_node1_preservation_delta_20260913.json`, SHA256 `5e7ad05a3f1714d13f8977abb6b1e15c0d862733255f06b914a6b37424b48ffb`.

The delta includes the previously missing `off_noise`, `pretest_write_ab_AC`, `pretest_write_ab_Arep` contents and changed `pretest_write_ab_AC/R4_B_seed606/probe_OFF_disjoint.out` and `timings.jsonl`. Fresh counts/mtimes reveal no later growth in this scope, but do not replace current source/destination hashes. Baseline-plus-delta coverage must be certified as a union, not by checking delta alone.

An additional weights-excluded receipts archive exists historically on node2 and laptop: `v6_out_receipts_2026-09-13T00.tgz`, 359,285,253 bytes, SHA256 `f5a2ef3d9c2af3eaa7067fe072aafd8f7253a0cc3c8153e5fe635db611152b2a`. It predates later writes and cannot establish adapter custody. The older 698-weight adapter-only mirror is also insufficient by itself.

### Twelve newest adapters and their complete diagnostic evidence

Exact root families (brace notation expands to seeds 0, 1, 2):

```text
/localhome/local-rohing/astra_diagnostics/level1_prediction_seed{0,1,2}_20260913_attempt1
/localhome/local-rohing/astra_diagnostics/level1_goal_completion_seed{0,1,2}_20260913_attempt1
/localhome/local-rohing/astra_diagnostics/level1_repetition_seed{0,1,2}_20260913_attempt2
/localhome/local-rohing/astra_diagnostics/level1_meta_reflection_seed{0,1,2}_20260913_attempt2
```

Each adapter is `<root>/run/fit/adapter/adapter_model.safetensors`, **80,792,096 bytes**, total **969,505,152 bytes**. Adapter mtimes span approximately 07:51–08:16; collections finish around 08:20. These are newer than, and outside, the old v6_out mirror/delta. Each cell has 274 root files plus seven lifecycle siblings: `<root>.collection_claim.json`, two files beneath `<root>_collected/`, four beneath `<root>_collection_driver/`. All 281 × 12 current files match archive path/length coverage, including raw/training evidence and collection receipts; no score interpretation was needed.

| Cells | VM archive path | Bytes | Existing verification |
|---|---|---:|---|
| prediction + goal_completion, six | `gpu_artifacts_local/level1_first_roster_20260913/node1/node1_first_roster.tar` | 504,350,720 | `VM_ARCHIVE_FULLY_VERIFIED`; all member payloads verified; native membership/metadata stable |
| repetition, three | `gpu_artifacts_local/level1_second_roster_20260913/node1_second_repetition.tar` | 254,648,320 | native and VM payload hashes verified at 08:16:41; no extraction |
| meta_reflection, three | `gpu_artifacts_local/level1_second_roster_20260913/meta_reflection/node1_second_meta_reflection.tar` | 258,232,320 | native and VM payload hashes verified at 08:22:52; no extraction |

Archive SHA256s, in table order:

```text
0d822a18838314346f1fa332ad4ac71234e1d20e59e7f841d81109a1f23226d1
b2e4cf8931afa5fb03768658d4e5cd2aef07db563476c53d2a16f3bb1e7ca6f6
1b69ccab8dd8612767dc0fa2139f934acc09e0ee5bde48181345044879599dc9
```

Total three capsules: **1,017,231,360 bytes**. Each archive directory also contains `node1_archive_manifest.json` and `node1_archive_listing.txt`. First verification is `node1/vm_verification.json`; later two are `node1_vm_verification.json`. Preserve the associated native receipts too. Their receipt-pinned manifest hashes were freshly verified:

```text
6135f75436f195557fafc8b4be916232ad56b963772115775077c326d9d103f0
7d4656318dd2a4d825834d6eed6db612a5b542fb428bc60518ba2bdf61b165e4
58ec5a49440b1fedd925d2b2535edf6409c9002596b42f4a4787259ab46fe03e
```

**Not demonstrated:** onward node2/durable-storage copies of these three newest capsules. This does not negate their demonstrated VM custody. No new diagnostic-root adapter/ledger transfer gap was found in the bounded census; byte-preserving mutation after archival remains unchecked.

## 3. Exact remaining support-evidence gaps

Of 29 paths outside the capsule member union, nine are the three native archive/manifest/listing triplets themselves, already represented by local archive evidence. Twenty are small support files. Nine have fresh byte-identical VM `/tmp` counterparts (listed next); **eleven have neither capsule coverage nor matching local files in the bounded search**. This is “not demonstrably mirrored,” not proof that no other copy exists anywhere.

The eleven must be retained as original historical evidence, especially the original failure; no successful replacement receipt should be synthesized. Paths are absolute on node1:

| Path | Bytes | Fresh source SHA256 |
|---|---:|---|
| `/tmp/astra_level1_batch_node1_20260913_attempt1.launch/receipt.json` | 193 | `a224394a967d33936f0c92c42b918704a2b0e366567d66668ba319979ec2fd34` |
| `/tmp/astra_level1_batch_node1_20260913_attempt1.launch/stdout.log` | 342 | `13c8058b657ffabdcbd16566118da9d9ff32bc636f5119b8bf6c9cd4f09406bf` |
| `/tmp/astra_level1_a40_fallback_20260913_attempt2.launch/receipt.json` | 523 | `b19f93889dde87fa5bdbca04e480a484f2b25892800d6939431fd274f256561e` |
| `/tmp/astra_level1_a40_fallback_20260913_attempt2.launch/stdout.log` | 5,563 | `9b51623c61b13ec042ab6109238613085b3f6b5955c8d3b82dc8d6b9eb31dd4f` |
| `/tmp/astra_level1_batch_node1_parentfix_20260913_attempt1.launch/receipt.json` | 203 | `9bbdbd7516572196538e4edc05f5134f151e473541aca9d441e6fa399ee1c4df` |
| `/tmp/astra_level1_batch_node1_parentfix_20260913_attempt1.launch/stdout.log` | 5,563 | `cf335529c7c3e58548a129d3108fd81d5810c2fe911bf6a3707c455b924d18a0` |
| `/tmp/astra_level1_roster_20260913_attempt1/batch_node1_parentfix/finished.json` | 80 | `ce3ff67b23672c97b5816dbc54ffeb14a00fbed904c523a5e8d893c4984a020e` |
| `/tmp/astra_level1_roster_20260913_attempt1/batch_node1/started.json` | 128 | `f1575437ec754f69be9531f73e69fd00da43a6955b8470307c7ae343434bd54b` |
| `/tmp/astra_level1_roster_20260913_attempt1/batch_node1/prediction_seed0/prepare.log` | 736 | `3aae1451ea1096c413e42c1c8faea8d8b49c005a8623b1a39c8baaac18eff8de` |
| `/tmp/astra_level1_roster_20260913_attempt1/batch_node1/prediction_seed0/failure.json` | 144 | `f93ae956209601dfaae15444341fec229513edbe92f53285a2696375d2d426f0` |
| `/tmp/astra_level1_a40_fallback_roster_20260913_attempt2/batch_node1/finished.json` | 80 | `eaa0f838c9b525e953c098949c6f2e08b3471d1a034e6171a921a51e8c577c7d` |

The nine other files have byte-identical local files at the same `/tmp` paths, but no durable archive coverage was established. Total **47,447 bytes**. Include them in the final support capsule rather than treating transient `/tmp` as durable preservation:

```text
/tmp/astra_level1_batch_node1_parentfix_20260913.py
/tmp/astra_level1_batch_20260913.py
/tmp/astra_level1_perception_reflection_material_20260913.py
/tmp/astra_level1_roster_20260913_attempt1/update_judgement_seed{0,1,2}.json
/tmp/astra_level1_roster_20260913_attempt1/contradiction_seed{0,1,2}.json
```

Local matching search was restricted to `/tmp/astra_level1*` and the two Level1 archive families in `gpu_artifacts_local/`; it did not unpack archives or search every possible evidence store. No arbitrary home/tmp sweep, credential files, raw scientific outcomes or manuscript analysis was required.

## 4. Owner transfer and verification plan — NOT EXECUTED

1. **Now:** reserve a preservation owner and safe transfer window. Screen the explicitly listed support files for export-sensitive content without displaying secrets. Retain original failures and exact bytes; if restricted content is found, record a secure-custody exception rather than silently omit it. Package the eleven unproven files plus the nine transient local counterparts into a fresh, versioned support capsule with exact source-relative paths, sizes and SHA256s. Recheck source metadata/hash stability. No kills or stage retries.
2. **Before any larger copy:** refresh available bytes/inodes/quota and competing growth on the actual staging/destination filesystems. Historical free-space figures are not current capacity approval. Reuse the existing three VM capsules (~1.02 GB) instead of recopying twelve adapters from node1. Transfer archive + manifest + listing + native/VM verification receipts as one custody unit to an owner-selected durable location. Node2 is an additional leased copy, not indefinite retention. A possible fresh node2 destination is `/localhome/local-rohing/mirror/node1_final_20260913T<UTC>/` — **proposed, not observed**. Use it only when Main confirms SSH will not disturb release checks.
3. **Close old-tree coverage:** reconcile an exact current node1 roster against the dated full mirror overlaid logically with the verified delta. Every required path needs exact relative identity, length and payload SHA256; same basenames, aggregate counts, timestamps or archive-only hashes are insufficient. Preserve original baseline/delta objects rather than overwrite them. Copy only confirmed missing/changed files to a fresh delta, and explicitly document any unavailable old-baseline hash evidence.
4. **Verify destination:** independently check transferred archive hashes against the recorded pins, safely validate archive members (no escaping paths, unapproved links or special files), then stream-check every member against its manifest. Check roster equality, not only archive integrity. Write a receipt binding source cut, object/path, bytes, hashes, destination, verification time and every exclusion/failure. This report does not substitute for that receipt.
5. **Restore test without GPU:** in an owner-approved fresh sandbox with sufficient space, extract representative checkpoint/config plus accompanying lifecycle/ledger evidence from both old and newest scopes; verify restored bytes and referenced source/config paths. No model loading or science run is necessary. Do not claim complete full-tree restoration from a sample; record the exact sample and remaining limits.
6. **By September 13 23:14:** publish one consolidated coverage ledger binding baseline, exact delta, three new capsules, support capsule, restore results and onward custody. Reinventory owner-identified late-writing roots for a final stable incremental cut. If any scope remains unresolved, name it explicitly; do not label migration complete from historical rsync success alone.

**Do not execute `gpu/migrate_node1_to_node2.sh` for this assessment/preservation step.** It is a legacy migration/relaunch script with broad job-killing behavior, not a safe read-only inventory wrapper. Do not delete source evidence, use destructive synchronization, or create replacement completion/release attestations.

## 5. Evidence references and limits

- `research_notes/astra_memos/ASTRA_HANDOFF_2026-09-12.md` (living handoff; current header advanced to 14:27 while assessing).
- `research_loop/COORDINATION.md`: lines 7525 (full mirror), 7595 (receipt archive), 9189–9197 (exact delta), 10330–10456 (Level1 collection), 13305 (14:02 final incremental mirror still planned). Line positions are current-read references, not immutable pins.
- `/tmp/astra_node12_inventory_20260913.md` and its archived receipt copy.
- `/tmp/astra_node1_preservation_plan_20260912.md`, `/tmp/astra_node1_preservation_execution_20260912.md`, `/tmp/astra_preserve_node1_delta_handoff_20260913.md`.
- `/tmp/astra_node1_delta_20260913_attempt1.vm_verify.json`; `gpu_artifacts_local/node1_delta_20260913/astra_node1_delta_20260913_attempt1.node2_verify.json`.
- The three capsule manifests/listings/verification receipts identified in §2.

Scope is the known required node1 evidence trees plus narrowly identified Level1 runtime support. It is not a whole-node filesystem audit, present-day node2 hash check, full restore, storage durability guarantee or scientific validation. Metadata inventories were sequential, not an atomic snapshot. Fresh small-file hash equality establishes the observed bytes only, not future retention. **No evidence transfer was performed by this sidecar.**
