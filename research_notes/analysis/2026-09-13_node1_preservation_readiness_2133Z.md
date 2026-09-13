# Bounded node1 preservation readiness — 2026-09-13 21:33 UTC

## Decision

**No presently demonstrated missing Builder-owned node1 payload in the documented scope. No additional node1 transfer is justified by this audit.** This is a receipt-based custody finding, not certification of the entire node or indefinite durability. The earlier seven-adapter/source-snapshot gap, eleven support receipts, and three prediction claims are closed; do not recopy them as missing.

Node1 preservation deadline is **September 13, 2026, 23:14 UTC**, about **1h40m53s after the native observation**. Node1 lease expiry is **September 14, 2026, 23:14 UTC**; node2 expiry is **September 21, 2026, 08:43 UTC**. These are supplied/runbook dates, not fresh provider verification. The watcher's proposal for another incremental tomorrow concerns lease end, not today's earlier preservation deadline.

All repository-relative paths below are rooted at `/data/home/rohing/dream-state`. No repository or Git changes were made. The only audit-created file is this note. The existing rules edit and untracked junction draft remained present at both status checks.

## Required coverage and evidence

### 1. Older v6_out and actual executed sources

Required scope is the complete selected node1 `/localhome/local-rohing/v6_out/` evidence, not just adapters: corpora, raw outputs, ledgers, intermediate/ancestor/final checkpoints, configs, provenance/selection/parent receipts, original failure/partial evidence and markers. The historical plan specifically prioritizes `ENV`, `analysis`, both `astra_B0_slot_{A,B}_seed9100_20260912_attempt2` roots, `brief_baseline`, `disjoint_panel`, `noise`, `pretest_write_ab_AC`, `src_classrooms`, `src_seed3`, `xnode`, all `pretest_write_ab`, and remaining life trees. Preserve documented absences as absences, not synthetic receipts.

- Baseline: node2 `/localhome/local-rohing/mirror/node1_v6_out_2026-09-12T23/`. Fable's September 13 15:04 UTC entry in `research_loop/COORDINATION.md` reports the 15:02 incremental: 348 regular files / 2,401,668,049 bytes transferred, source and mirror both 15,428 files. This is historical rsync/count evidence, not full-tree member SHA256 or restore verification.
- Exact delta on VM: `gpu_artifacts_local/node1_delta_20260913/astra_node1_delta_20260913_attempt1.tar`, **2,413,762,560 bytes**, saved archive SHA256 **`f01a1526254c7b12924191694f71ada143c31edbaee77dcc0ebc6860ba385118`**. Local length is present/matching; this audit did not rehash the 2.4 GB archive.
- Node2 delta: `/localhome/local-rohing/mirror/node1_delta_20260913_attempt1/astra_node1_delta_20260913_attempt1.tar`.
- The delta's 767 payload files comprise 348 v6_out files, including the seven formerly missing adapters, plus all 419 executed-source files in `astra_sources/0babc3ccbe1f2378a61dd0dac6f18f7371b82176/` and `astra_sources/125ba29df6e1060e4e412742459dd75217193d2e/`. The embedded roster is the 768th member.
- Exact roster: `research_notes/astra_memos/receipts_20260912/astra_node1_preservation_delta_20260913.json`; **fresh SHA256 PASS** `5e7ad05a3f1714d13f8977abb6b1e15c0d862733255f06b914a6b37424b48ffb`.
- Saved verification receipts: `research_notes/astra_memos/receipts_20260912/astra_node1_delta_20260913_attempt1.vm_verify.json` and `research_notes/astra_memos/receipts_20260912/astra_node1_delta_20260913_attempt1.node2_verify.json`. Both say `DELTA_VERIFIED`, `full_member_bytes_verified=true`, `extraction_performed=false`, `DELTA_ONLY_NOT_FULL_MIRROR_RESTORE`; completion times 04:46:51 and 04:47:53 UTC. Fresh receipt-file SHA256s respectively `b842cca26bf55de7c2e08d469a1c937ab5f3c92ecd50742b080a3267e374cfc1` and `fb872dfec95caf7a888444b53653217bbe3b8bb43331280b40a878996799e709` identify the receipts read, not a new remote verification.

Historical weights-excluded receipts on node2/laptop are additional coverage, not an adapter substitute: `v6_out_receipts_2026-09-13T00.tgz`, saved SHA256 `f5a2ef3d9c2af3eaa7067fe072aafd8f7253a0cc3c8153e5fe635db611152b2a`. Those remote/laptop bytes were not reread here.

### 2. Twelve Level1 adapters, diagnostics and collection/source evidence

Required roots under `/localhome/local-rohing/astra_diagnostics/`, with seeds 0, 1, 2 in each family:

- `level1_prediction_seed{0,1,2}_20260913_attempt1`
- `level1_goal_completion_seed{0,1,2}_20260913_attempt1`
- `level1_repetition_seed{0,1,2}_20260913_attempt2`
- `level1_meta_reflection_seed{0,1,2}_20260913_attempt2`

Coverage includes each root's `run/fit/adapter/adapter_model.safetensors`, complete diagnostic/raw/training evidence, `.collection_claim.json`, `_collected/`, `_collection_driver/`, exact pinned source bundles and batch receipts. The earlier inventory establishes 12 adapters / 969,505,152 adapter bytes and 3,372 diagnostic-root/lifecycle files; those counts were reused, not recounted.

| VM archive | Saved archive SHA256 | Local bytes checked |
|---|---|---:|
| `gpu_artifacts_local/level1_first_roster_20260913/node1/node1_first_roster.tar` | `0d822a18838314346f1fa332ad4ac71234e1d20e59e7f841d81109a1f23226d1` | 504,350,720 |
| `gpu_artifacts_local/level1_second_roster_20260913/node1_second_repetition.tar` | `b2e4cf8931afa5fb03768658d4e5cd2aef07db563476c53d2a16f3bb1e7ca6f6` | 254,648,320 |
| `gpu_artifacts_local/level1_second_roster_20260913/meta_reflection/node1_second_meta_reflection.tar` | `1b69ccab8dd8612767dc0fa2139f934acc09e0ee5bde48181345044879599dc9` | 258,232,320 |

Each archive's directory contains `node1_archive_manifest.json` and `node1_archive_listing.txt`. Verification receipts are respectively `vm_verification.json`, `node1_vm_verification.json`, `node1_vm_verification.json`. Existing receipts record full member-payload verification. This audit freshly checked all three manifests and listings against sealed pins; all six PASS. Manifest SHA256s in table order: `6135f75436f195557fafc8b4be916232ad56b963772115775077c326d9d103f0`, `7d4656318dd2a4d825834d6eed6db612a5b542fb428bc60518ba2bdf61b165e4`, `58ec5a49440b1fedd925d2b2535edf6409c9002596b42f4a4787259ab46fe03e`. No repeat hashing of the 1.02 GB capsule payloads.

### 3. Eleven original support receipts and nine support files

`gpu_artifacts_local/node1_receipt_delta_20260913_attempt1/manifest.json` enumerates the exact eleven native paths: receipt/stdout pairs for the original batch, fallback and parentfix launches; parentfix finished receipt; original batch started receipt; prediction-seed0 prepare log/failure receipt; fallback finished receipt. These total **13,555 payload bytes**, including original failures.

- Archive `gpu_artifacts_local/node1_receipt_delta_20260913_attempt1/receipt_delta.tar`: **fresh SHA256 PASS** `d1926ac3b291639fffed74e79f48ff7e83e5f33a74ea37968ddc2c062de115ba`, 51,200 bytes.
- Manifest: **fresh SHA256 PASS** `4c2ddeafc25f989efc962bbca3b3f945e9823ea261229b3d21e6b1bf7e417f04`.
- `gpu_artifacts_local/node1_receipt_delta_20260913_attempt1/verification.json` records VM preservation and a full scoped restore at 14:29:48 UTC, all eleven payloads verified.

The nine additional support objects are the original node1-parentfix batch script, generic Level1 batch script, perception/reflection material script, and three `update_judgement_seed*.json` plus three `contradiction_seed*.json` roster files. Exact source/destination paths and pins are in the onward manifest below. All nine current VM source-file hashes match its pins.

### 4. Node3 onward custody of the preceding newest evidence

`gpu_artifacts_local/node1_onward_node3_20260913_attempt1/final_custody_receipt.json` records **29 objects / 1,018,616,159 bytes**, four archives fully restored, 3,490 restored regular members including the receipt manifest, and nine support files rehashed. Destination: node3 `/localhome/local-rohing/mirror/node1_onward_20260913_attempt1/`. Verified 14:41:33 UTC; persisted receipts independently read back 14:41:55 UTC.

Fresh checks of local persisted evidence, all PASS:

- `gpu_artifacts_local/node1_onward_node3_20260913_attempt1/onward_manifest.json` and `node3_onward_manifest.json`: `63264ed62c9cf4a7d0d4becc0549290b77568202d49f3931d1e77c1c47cca9c1`.
- `gpu_artifacts_local/node1_onward_node3_20260913_attempt1/node3_transfer_receipt.json`: `aafe6f2a137f13310d4ca23d94e651b0c887f7a59527bc845a7ceb7e0269602f`.
- `gpu_artifacts_local/node1_onward_node3_20260913_attempt1/node3_verification.json`: `c89444c64fd2b07d6e1590bd03e82b51c64cae602f5a63601c2db92b48dce140`.

All **25 non-archive objects** referenced by the onward manifest were freshly hash-checked at their current VM source paths and matched; all four archive lengths matched. This does not claim a fresh node3 read or extend the node3 receipt to the older delta or later prediction capsules.

### 5. Later prediction transfer: primary, failures, source/batch, missing claims

`research_notes/analysis/2026-09-13_level1_prediction_transfer_result.md` lines 59–65 identifies both verified VM archives. Fresh whole-archive SHA256 checks PASS:

| VM archive | Fresh SHA256 | Bytes |
|---|---|---:|
| `gpu_artifacts_local/prediction_transfer_primary_20260913/evidence.tar` | `365cfdbe817c41f5bedf4099a35d0e836d788eeec75edc687addc92dfb295b69` | 17,520,640 |
| `gpu_artifacts_local/prediction_transfer_20260913_attempt1/evidence.tar` | `0928686137e8a61db60cc91952c407920117e136285b847ee71a8afa68e508bf` | 17,264,640 |
| `gpu_artifacts_local/node1_prediction_claims_20260913_attempt1/evidence.tar` | `70e0887801f8e47e6e9934f81b18a6433f5135fd7b6104eed9b1fbe0757bfe34` | 10,240 |

Archive indices confirm original seed0/1/2 attempt1 roots, primary seed0/1 attempt2 and seed2 attempt1 roots/collections, executed source bundle, batch evidence and retry support. No raw scoring/retention recount was performed.

The small claims archive contains exactly three regular 201-byte members, freshly read and hashed:

- `prediction_transfer_seed0_20260913_attempt2.collection_claim.json`: `b13e3b51d737a90a38b9887baff45e17b6d87abeeb5422ef8dd40b49eb41be10`.
- `prediction_transfer_seed1_20260913_attempt2.collection_claim.json`: `eb885aa1b93f3ab20aebd045e961936562772d6177c46f904eabc055cfc1ea28`.
- `prediction_transfer_seed2_20260913_attempt1.collection_claim.json`: `58fffb8bac810b6d8925c69b5068b4a5ee726751f0475da7cd9f90b8547f618f`.

`research_loop/COORDINATION.md` lines 16990–16998 and `research_notes/astra_memos/ASTRA_HANDOFF_2026-09-12.md` lines 136–139 record Main's closure of Kepler's only three uncovered files from the 5,294-file audit. This audit relies on that supplied/recorded prior result; it did not rediscover a standalone 5,294-row roster or rehash those files. Fresh member hashes identify the preserved bytes; the prior comparison to Kepler's expected member hashes is Main's recorded verification.

## Single current native observation

Exactly one invocation through `bash gpu/a40_ssh.sh`, bounded by 24-second local and 8-second remote timeouts. Native metadata scan ran **21:33:06.444532–21:33:06.619456 UTC**, completed successfully, no scan errors, no omitted matching entries. No remote payload bytes or hashes read, no process/GPU/environment inspection, no copying/writing/job actions.

- `v6_out`: **zero file mtime/ctime later than September 13 15:02 UTC** (last watcher incremental start).
- `astra_sources`, `astra_diagnostics` and existing `/tmp` entries prefixed `astra_level1`, `astra_prediction_transfer`, `prediction_transfer`: **zero file mtime/ctime later than September 13 20:24 UTC** (recorded handoff/closure checkpoint, not a claimed exact Kepler scan time).
- `astra_writer_roots` absent. Home `astra_*` top-level entries were diagnostics, sources, and the already-preserved delta tar/pack receipt; no new similarly named home root observed.

This was a late-change metadata filter, not a duplicate full-file hash audit or a raw retention recount. It does not detect deletions, establish payload equality, reconstruct the exact prior scan cutoff, cover unrelated paths, or prevent future writes.

## Remaining risks and smallest action

1. **No demonstrated current Builder transfer gap.** Keep existing VM capsules and receipts; do not recopy the closed seven-adapter/419-source/eleven-receipt/three-claim gaps. No node1 payload transfer is presently required by the available evidence.
2. **Historical full baseline is not fully hash/restore-certified.** The 15,428 count plus rsync receipt is weaker than whole-tree content verification. The delta and four newest scoped restores do not upgrade that baseline. Do not claim every owner's node1 files are protected.
3. **Future/unknown changes remain a risk.** If Main creates further node1 evidence, the smallest required transfer is only its newly identified stable delta plus exact path/size/SHA256 and independent destination verification. Do not wait until September 14 for material required by the September 13 23:14 preservation deadline.
4. **VM custody is not indefinite off-lease storage.** The 29-object node3 receipt excludes the later prediction archives. If another surviving-node copy of those is desired, the smallest complete later-prediction bundle is the two existing evidence tars plus the three-claim tar, **34,795,520 bytes**, with their listed hashes; transfer from the VM, not by reacquiring node1 raw files. This is optional redundancy, not repair of an established missing-VM-payload gap. Node2/node3 themselves are leased; provider dates and permanent custody were not checked here.
5. **Read-only boundary held.** No node2/node3 SSH, launches, kills, copies, model/tokenizer loads, new tests, Git mutations, or repository edits. Never invoked `gpu/migrate_node1_to_node2.sh`; it remains inappropriate for preservation because of its destructive job behavior.

Supporting historical scopes/runbooks: `/tmp/astra_node1_preservation_plan_20260912.md`, `/tmp/astra_node1_migration_status_20260913_1425.md`, `research_notes/astra_memos/receipts_20260912/astra_node12_inventory_20260913.md`, `research_notes/astra_memos/receipts_20260912/astra_node1_receipt_preservation_handoff_20260913.md`, and `research_notes/astra_memos/receipts_20260912/astra_node1_onward_node3_handoff_20260913.md`. Old statements of gaps in these documents are superseded only to the exact scope proven by the later receipts above.
