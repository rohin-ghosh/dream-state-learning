# Independent local archive custody audit — actual-record memory attempt1

Date: 2026-09-13 UTC. Scope: archive safety, byte inventories, provenance/adapter bindings, and recorded process/exit custody. **Not a score reduction or scientific-result review. Lovelace owns those reductions; Main owns live process checks and the separate greedy archive.**

## Verdict

**PASS for local archive integrity and internal custody consistency, with explicit evidence limits below.** No duplicate/unsafe member, missing inventoried file, hash mismatch, unmatched raw call, parent-binding mismatch, or inconsistent tensor-hash receipt was found. All three memory roots and their once-collection records are present and internally linked.

This is **not** independent confirmation of live GPU vacancy, historical raw GPU-query results, model execution authenticity, or scientific efficacy. Three controller wait/exit-code receipts exist and record return code 0; worker release is supported by source-bound wrapper attestations, not archived raw process/GPU vacancy observations. Do not turn this audit into a launch authorization, manuscript update, or score approval.

## Exact capsule and reproducibility

- Archive: `gpu_artifacts_local/actual_record_memory_20260913_attempt1/evidence.tar`.
- SHA256: `3ed6579e7e885139d78faf3457eb3bec254215d36b533558ef22f8199ff6a003`.
- Size: **496,957,440 bytes**.
- Effective tar members: **1,166 unique = 1,135 regular files + 31 directories**.
- Independently hashed every regular-file payload. The SHA256 of the sorted compact JSON mapping `{member_name: payload_sha256}` is `80c4913c8595af3ba624566d8675f1a8a74084512993a12661e1b2328394cf22`. Encoding is UTF-8 of `json.dumps(mapping, sort_keys=True, separators=(',', ':'))`, default ASCII escaping, **no terminal newline**. This map digest concerns regular-file names and bytes, not a separate mode/owner attestation; the whole tar hash binds the capsule bytes.
- Reproducible stdlib-only helper: `/tmp/astra_actual_memory_custody_check_20260913.py`, SHA256 `eca1aa67b3dba3527353d47bf3f0bf5826f4e85bc50fde0c26b389620fa2503a`.
- Run from the repository: `python3 -B /tmp/astra_actual_memory_custody_check_20260913.py`. It reads archives and prints checks; it does not write evidence, import project/model code, extract files, or calculate score outcomes.

Archive size, modification time and inode were unchanged across checking. Local whole-archive SHA matches the user's supplied pin; no new remote hash/copy or independent native-to-VM transfer authentication was performed.

### Member safety

Checked exact-name and normalized-name uniqueness; relative paths; absence of traversal, backslashes, drive-style colons and control characters; valid file-data bounds; no regular-file ancestor masquerading as a directory. All members are regular files or directories: **no symlinks, hardlinks, devices, FIFOs, sockets, sparse files, or setuid/setgid modes**. No failure-named artifact occurs in this capsule. No extraction was attempted, and this is not an instruction to execute archived code.

Some stored modes are group-writable (notably 0664 files and 0775 directories). These do not create a path/link safety failure, but the capsule is not thereby an immutable or access-controlled evidence store. Existing permissions were not changed.

## Inventory and raw-call checks

For every seed, independently matched:

1. Spec bytes → `prepare_started.json`/plan spec pins; runner/core/protocol pins → archived source bytes.
2. Prepared receipt → actual `plan.json` SHA256.
3. All five `plan.input_hashes` → actual `calls.json`, `capture.json`, `dataset.json`, `retention.json`, `training.json` member bytes: **15/15** checks.
4. Every `capture_complete.json.stages` entry → the exact set and hashes of regular files under that stage, with no missing or extra files: **1,074/1,074** stage payloads.
5. Each readout's exact request/response filename set → the prepared call IDs; each request → its prepared call plus pinned parameters and fitted adapter route.
6. Saved native prompt/system/token-ID fields and adapter routes → requests; output text → saved `decoded_output`; output-token bounds, stop metadata and timing consistency. These are joins of saved fields, **not** new tokenizer decoding or model-origin authentication.
7. Each collected row's ID, response hash, raw text and finish reason → its archived response: **480/480** joins. No score field, accuracy numerator, or treatment contrast was recomputed.

| Seed | WRITE fit files | WRITE readout files | LR0 fit files | LR0 readout files | Raw pairs per arm | Total raw pairs |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 12 | 183 | 12 | 183 | 88 | 176 |
| 1 | 12 | 159 | 12 | 159 | 76 | 152 |
| 2 | 12 | 159 | 12 | 159 | 76 | 152 |
| **Total** | **36** | **501** | **36** | **501** | — | **480** |

Thus the capsule contains **480 requests and 480 responses** for memory readout. Per-arm prepared inventories are 14 exact + 14 paraphrase + 48 held + 12 canary for seed0, and 8 + 8 + 48 + 12 for each of seeds1/2. These are custody/workload counts, not passing-score counts.

Each root has one expected `*_collected/collection.json`, one `scores.json`, and one separate collection claim with `retry: false`. The collection's completion and scores hashes match actual member bytes; report plan/parent/formation metadata and copied fit manifests/parameter receipts also match. This establishes the archived once-collection chain, **not proof that no other collection could have happened outside this capsule**.

## Original capture, source and parent bindings

The current capsule contains the three new source files, specs and memory protocol, but is not a standalone copy of every inherited dependency or original parent. The following existing local archives were independently rehashed and read in memory to resolve inherited bindings:

| Existing local archive | SHA256 | Use |
| --- | --- | --- |
| `gpu_artifacts_local/real_record_20260913/astra_real_record_20260913_attempt2.tar` | `71671dc02e175be0dafba595aa4e9ef30c409953a0366cc082b4d7e319c055c0` | Original formation plan, completion, collection, upstream learner bindings and captures |
| `gpu_artifacts_local/level1_second_roster_20260913/node2_second_perception.tar` | `addc2e61ce05f2b622482adde82f16c2c571db6dd072b0fb7750a4d6dc559a3a` | Three original parents: plan/collection/completion, six-file adapter inventories, train manifests, material and pinned helper/source bytes |
| `gpu_artifacts_local/real_record_20260913/astra_actual_record_frozen_sources_20260913.tar` | `e2ec97cad381ae4686be3830d02bd7533a20406bb5eb84164a92d369a144b749` | Formation runtime and inherited source dependencies |

The memory plans' parent objects equal the original formation plan's three corresponding perception bindings. All parent adapter inventories match the original archived six files. Parent collection/completion/score-file pins are linked correctly; original score files were hash-bound only, not reduced. Retention objects equal the respective archived parent materials. The five pinned parent source files match both inherited local source archives. The model/source/environment/template bindings remain equal to the original formation plan; actual base-model weight files, Python interpreter bytes and live installations were not loaded or independently rehashed in this audit.

### Capture serialization distinction — preserved, not a corruption

The three new `capture.json` files **do not have the same file hashes as the original formation files**. They are object-identical reserializations using the archived memory runner's compact sorted JSON writer with a newline. The checker verified the writer's exact serialization from each original parsed object equals the new file bytes. Every nested raw request/response string is preserved by that object equality; there is no evidence here of edited answers or new formation.

| Seed | Original formation file SHA256 | New memory `capture.json` SHA256 |
| --- | --- | --- |
| 0 | `386d81c58391fca926df28f4d006bbcfbf555957a434cc0f8c56f984ff7edd56` | `e2f12e2fcaf390520ecb4fa56897f8be1783fa50415cef2c87ce1e71e6e15410` |
| 1 | `60a926a769c6e83b526c5dc9e28a4e7765591d97a36fb7fc62cd3452d09c82bf` | `7d91ed7815056b466b01705363c46f2e550ea30e0305beb653d704c7be8286b8` |
| 2 | `26d918346b97f31f1ec0ab4bfe5077ca7d5c8bf6796b1eac22fe88870d6417d0` | `55381211c155cf1770bb3d0278f1beb08e0f6387ff1af0ace3eea3851a16e733` |

An embedded semantic `capture_sha256` must not be confused with either file SHA. No full formation-score replay was performed.

### Adapter and tensor receipt consistency

Verified all six fitted adapter file inventories; fit routes and readout identity receipts; fit training-corpus pins against actual `training.json`; manifest configuration equality; immutable parent before/after file maps; fresh-optimizer and initialized-state receipt fields; and parent/phase/cumulative step lineage. Collected manifest and parameter-diagnostic copies equal the original fit receipts.

Used only `struct`, JSON and SHA256 to parse safetensors headers and hash named byte ranges. Checked extents, contiguous non-overlapping coverage, F32 dtype, shapes and per-tensor hashes against manifests. **No safetensors library, PyTorch, tensor arithmetic, model load, norm calculation or changed-element recount was invoked.**

- Three original parents: **392 tensor payloads each** (1,176 source payloads).
- Six final adapters: **392 each** (2,352 final payloads).
- Source and initialized inventories are equal, with no dtype conversions; the two arms share the same initialized inventory for each seed.
- Every WRITE final has 392 changed tensor hashes; every LR0 final has zero. LR0 serialized adapter-file hashes also equal the corresponding archived parent's file hash.
- Recorded positive WRITE versus zero LR0 delta/changed-element receipts are consistent with these hash comparisons. Exact reported L2 norms and changed-element counts are **not independently certified** here; only receipt equality, finiteness and qualitative consistency were checked.

| Seed | Original parent = LR0 adapter file SHA256 | WRITE adapter file SHA256 |
| --- | --- | --- |
| 0 | `8bfe8b9d647b58b064733ed24d8aaa97cd79d7012795232305838a23ac415432` | `9ff3540ad1ade90045e55e6ac63dee85263ba64316e7d5bbed906e03ac6c6155` |
| 1 | `c9700a2f46b36e64ce9e1845cd4601d3d0da086afbaba9efbc93012af936e0e2` | `a3da34176657cbc25a85fe24b9c2bde695ea4af96dcb63e789280af0dabe8cdc` |
| 2 | `5d198acfc7bf2f2c552b6b180688bce5d7fe00b1afd2eea7d056fc44a2e505da` | `9a2fe30b5783c8945d7fdac875e450b0c79d461a4ae0e5c157f0bda86ebb35a2` |

These are provenance/control consistency observations, not a learning or retention result.

## Recorded exit and release custody

All **12 distinct worker PIDs** have matching launch/started/released identities, stage names and plan bindings. PID = PGID, positive start ticks, and expected pinned worker commands agree. Holder/controller commands and identities, GPU allocation fields, empty reservation/unresolved lists, chronological control timestamps and controller cap receipts are consistent. Controller stdout binds the actual completion-file hash. No failure/cleanup-failure artifact is present.

The archived custodian's `hold` function waits for its controller child and writes the resulting return code to `exit.json`. Therefore these are **recorded controller wait results**, not guessed exit codes and not wait receipts for the holder itself:

| Seed | Holder PID | Controller PID | Recorded controller return code | Exit receipt timestamp, UTC |
| --- | ---: | ---: | ---: | --- |
| 0 | 30950 | 30952 | 0 | 2026-09-13T09:05:38.658822+00:00 |
| 1 | 31023 | 31024 | 0 | 2026-09-13T09:04:28.381606+00:00 |
| 2 | 31094 | 31095 | 0 | 2026-09-13T09:04:41.091225+00:00 |

| Seed / stage | PID = PGID | Start ticks | `released.json` SHA256 |
| --- | ---: | ---: | --- |
| 0 WRITE_fit | 31093 | 51826761 | `d34c34185bc68353dea54e176df35f77264d017fbdbd09634a13bfb6cf7fee6a` |
| 0 WRITE_readout | 32368 | 51834535 | `9074d5f65cfe31170e6bbdb953add9e5e6565c2c96dca77c64c82c583c380c10` |
| 0 LR0_fit | 35918 | 51851807 | `760657c745b30b5ed7a16e7306c1a3dcec77ba8f8afa8e90f10e43ac342cba36` |
| 0 LR0_readout | 37299 | 51860272 | `c576d0869d89cf921dfd8b55cc079cd62eaf217704c440a231aff42c692c3b35` |
| 1 WRITE_fit | 31349 | 51828557 | `52db90577739c28af3c038e77d080f6b4c25ee348f817eeb8b1ad17fb0918822` |
| 1 WRITE_readout | 32624 | 51836662 | `c5606f47e149b83e2c34961ac15e4992611d2652debf5b2ab7c7aa32465d75dc` |
| 1 LR0_fit | 35623 | 51848566 | `c8e420eb7c8eb1ae1c3af9f1e7d6549178984ecd034577750c1b82ddaa53c47b` |
| 1 LR0_readout | 37038 | 51858094 | `af72f68e52eaaa65b9b844c12ed1b5e2bc0237e058c029b4d07f0035a82656bb` |
| 2 WRITE_fit | 31405 | 51829019 | `d0b563ff96c0ccdbc32139f932c13fe7e67690cfd03495aba7de896c187ee480` |
| 2 WRITE_readout | 32494 | 51835965 | `d3b440f4d6bfffc0a55a3bdca234a87232dfb56b17730f324e8c53372216892e` |
| 2 LR0_fit | 35686 | 51849820 | `8c4d1bc15f77bd52f98240b18355418dacbdb41798b3388a978d96fbfa0205b5` |
| 2 LR0_readout | 37109 | 51858941 | `d30a194be3a33d08589de8bdcf17e50ce6910f6cd4e6a28291990f1982a9670b` |

**Important limits:** each worker release JSON contains only `identity` and `stage`: no observation timestamp, raw all-process GPU XML/query, explicit group-absence result, or standalone worker return code. The pinned runner writes that receipt after its cleanup and GPU-vacancy checks; its successful controller path requires worker `wait() == 0`. This supplies source-bound internal attestation, not independently inspectable raw release evidence. `released.json` is emitted from a `finally` cleanup path, so it must not alone be treated as proof that the worker succeeded. The completion chain and actual controller exit receipt are the additional evidence here.

Tar member modification times are packaging metadata, not independent release timestamps. The holder/controller source records an expected boot and allocation, but the capsule does not carry an independently verifiable observed-boot/raw final vacancy witness. No current `/proc`, remote process, or NVIDIA query was performed. Main's separately timed current process checks cannot retroactively prove all historical release events, and this archive cannot prove the GPUs remain vacant now.

## Limits/anomalies and smallest correction

| ID / severity | Evidence / disposition | Smallest correction or next evidence |
| --- | --- | --- |
| C1 / Medium evidence limit, not a payload-integrity failure | Complete worker release receipt set and three controller exit receipts are internally consistent, but raw historical GPU/group-release observations and explicit per-worker exit-code receipts are absent. | Describe the existing evidence as wrapper-attested historical release plus recorded controller exits. Main may preserve its separately timestamped process/GPU observations in a **new, separately pinned** receipt; do not rewrite this capsule or infer historical/live release from that later check. Future launchers can persist raw checks and per-worker wait results if separately authorized. |
| C2 / Low, resolved serialization distinction | All three memory capture file hashes differ from the original formation files, although parsed objects and exact pinned-writer reserialization match. | Label them object-preserving reserialized captures and retain both file pins as above; do not call them byte-identical copies. No data repair is needed. |
| C3 / Low portability limit | Original parents and inherited dependencies are resolved from three pre-existing local archives, not wholly contained in this capsule. | Carry this audit's three archive pins alongside the capsule. If a standalone delivery is later required, make a separately versioned manifest/package; do not modify the current tar. |
| C4 / Scope limit | A unique archived claim with `retry: false` and matching collection chain does not establish global once-only execution. Saved token/system/route metadata and unsigned hashes are consistency evidence, not independent runtime authentication. | Keep “archived once-collection chain verified” wording and the authentication limit; no score rerun or native operation is requested by this audit. |

No hard custody mismatch was found. No repair was applied. None of these findings authorizes repository changes, a rerun, or a launch.

## Exact source and control-chain hashes

New source members and protocol:

| Member | SHA256 |
| --- | --- |
| `astra_memory_pairs_main_20260913.py` | `5df4a3c00016ad07305658e2febc642a1182d1944106d70b92b463235ede2dbe` |
| `astra_real_record_memory_run_20260913.py` | `7028fa9a9b277adc6edfec2398d1885d6c55ec33eb67a1bd51ac36b37e02215e` |
| `astra_real_record_memory_core_20260913.py` | `2c5538f5b63cbb4e592f40822561b4d62595ab3c9d7d193f084b91f9a064e8ef` |
| `astra_memory_pairs_20260913_attempt1/protocol.md` | `c056a0fb6c97d1ba93b4d2a0fa07cb70f806cfa64fef2df1769d78e80334a716` |

For the following tables, `R0`, `R1`, `R2` denote `real_record_memory_seed0_20260913_attempt1`, `real_record_memory_seed1_20260913_attempt1`, `real_record_memory_seed2_20260913_attempt1` respectively, as tar member roots. `_collected` and `.launcher` are suffixes on those root names, not subdirectories.

| Member | SHA256 |
| --- | --- |
| `astra_memory_pairs_20260913_attempt1/seed0.json` | `c7e2564dff21f6a21c35591f5742aa0c98dcb7257b2ef050ac0207284c65facf` |
| `astra_memory_pairs_20260913_attempt1/seed0_prepared.json` | `019e36d8af42ca4f646ff6e5306b0cb508ca3a5b20c68a7e9bd787077f648820` |
| `R0/plan.json` | `66fb0ae06fce25feb04c422add3062f8665be9bafaa72efdb348365fa82208c1` |
| `R0/capture_complete.json` | `08deffd0a0baa3bcad110884d250893f8470ae320afd13a3d71e20a651da4972` |
| `R0.collection_claim.json` | `f42bcd4b136d682fff40877c44820597ee1dbe8f6f537437228a54dbbf1b15ce` |
| `R0_collected/collection.json` | `fbbc8ddf580e2141c01a3b73477605e7e5a77bc8e638126475950ea1f105dfab` |
| `R0_collected/scores.json` | `b56a0caa16259e29860efa284d283610ab9bfa9064c64f121fe7cc34266b72bf` |
| `R0.launcher/launched.json` | `c7b28fbd15575371a41acdc11071d45a171aa751fda052c7cff5b3fd303968d6` |
| `R0.launcher/controller.json` | `1f1898bc9682d6ab087e8a60e8e25e5cd9c2cee1fb34a7dd5d50a0aef0cbf523` |
| `R0.launcher/exit.json` | `e9cc4697f69aa2d100099925acd7bcb2fe02842ed8c1336f21a3f95a70038a6e` |
| `astra_memory_pairs_20260913_attempt1/seed1.json` | `191b1ee01871c19ae1c4312b4591aebb18849327b36f3bca2d367a21addf707b` |
| `astra_memory_pairs_20260913_attempt1/seed1_prepared.json` | `c848cb4da070c28344f2f0b73ae499a9409c65a15549719c994458f3b64e87ce` |
| `R1/plan.json` | `9886ef9f19869f69649ee894e15c1fb47dfc85e301ee728adfbefc4df2c9c52b` |
| `R1/capture_complete.json` | `56d19072b3f9474631c4b0d61ca23a21fde490ad80a9dd197f310ecd7023ff92` |
| `R1.collection_claim.json` | `b15197ce3c8e225f686b4d2bafe0742b60f87b3fdc848e88b35ec14f220b881d` |
| `R1_collected/collection.json` | `f0ac6662ccb6b6cb9477503fa7214578a1dade4e376e8b1e6c4395e2ae5c6268` |
| `R1_collected/scores.json` | `5fe7638aa86e718b36ea00f9a97b9e36acbed4b464c968737acbc86447c71979` |
| `R1.launcher/launched.json` | `55c6ca2f12fbd99af477a853ed7918c69ec19fa413f5a186967e3d60e078c8ed` |
| `R1.launcher/controller.json` | `015e28d1cffec91dc605f990db3af54f293d4906e81b67b7f17c44c478edf038` |
| `R1.launcher/exit.json` | `6de65a5c7014ce0628faf56c1f51a27e9c503aa8d573fddb78f6feb18b136d2e` |
| `astra_memory_pairs_20260913_attempt1/seed2.json` | `39b2719ca4d1d8bef79e0715a3e54120c6396aaf3e1dd7d2608d76cb06f32cbf` |
| `astra_memory_pairs_20260913_attempt1/seed2_prepared.json` | `2aa1176d1b515d96be372ff1c86323cbc2cd94e8d22bd4a4e47ac471f5257248` |
| `R2/plan.json` | `48f64f78aa6953baa72067602bf3043c0a8fb5531750f0433c6fdd8ef76dc5ea` |
| `R2/capture_complete.json` | `e7ef9be2d572251e64c5973305fdcad0112d9569498c79c6646848049850987f` |
| `R2.collection_claim.json` | `24cd9ec8fb6e8bfcf1c80bf2c66ac195bffeb24c0c5289f94b65ca6bc645df17` |
| `R2_collected/collection.json` | `f0333bdd6854a27fc1a8825db852ec5976c3b50db667d9b762e2e489634d882a` |
| `R2_collected/scores.json` | `a0182417e86e85ab6a874c7e98d77fd5952e2bb036fe1a2e35d6e7289ecb0cef` |
| `R2.launcher/launched.json` | `dc3db6f9033310903090f1268355d500c02481ae8e256b22a23d3bf2bcfcd61c` |
| `R2.launcher/controller.json` | `10fa8e0070bc7a8406b46f3e2c38d805d6d4c60e5c78cd1d9feafe456f67a63e` |
| `R2.launcher/exit.json` | `3d877c98abaf4cc277a5ce503f2546f1cbb2237af5973c3778304516901550b2` |

Prepared input hashes, independently matched to actual member bytes:

| Member | SHA256 |
| --- | --- |
| `R0/calls.json` | `24cc010b8c25b4cbdc1bbaf489288bf35a005bb3a0b88ed3c8e0603724015cd5` |
| `R0/capture.json` | `e2f12e2fcaf390520ecb4fa56897f8be1783fa50415cef2c87ce1e71e6e15410` |
| `R0/dataset.json` | `c5af0aae08087ba39bbe4a3552a548b2c03b5e00c7636a5ad2b0fc5ded207988` |
| `R0/retention.json` | `69d5967ed2fc6f093978b6366c25565c61b1307fd840109d78974c71d21c1c2e` |
| `R0/training.json` | `57bd1e4a6f95f57406834f506cf366ef9fcbfdc7a5cc926ccf5bba53721ca010` |
| `R1/calls.json` | `3e400843bb6b3d61f28687f4ef646a0c8fe885b401e36e8cee30e98065d2a69c` |
| `R1/capture.json` | `7d91ed7815056b466b01705363c46f2e550ea30e0305beb653d704c7be8286b8` |
| `R1/dataset.json` | `a5575a8b9936264e40c6096d7555ce1e125084cc48465865ee5acb6ca94db8fa` |
| `R1/retention.json` | `69d5967ed2fc6f093978b6366c25565c61b1307fd840109d78974c71d21c1c2e` |
| `R1/training.json` | `a8ea5076f10d4d6a5d7671d8cefdb20c030ce1039b7dbe90c3b1232f44dfaecb` |
| `R2/calls.json` | `6ffbf94fd6b50d6f930b941c475e49ad21f154bd64ea1ffc57914e1509d293c6` |
| `R2/capture.json` | `55381211c155cf1770bb3d0278f1beb08e0f6387ff1af0ace3eea3851a16e733` |
| `R2/dataset.json` | `c8e853a528ebe6b0517e63482b22918624a647249586c20afaf3eedc1eea0d1a` |
| `R2/retention.json` | `69d5967ed2fc6f093978b6366c25565c61b1307fd840109d78974c71d21c1c2e` |
| `R2/training.json` | `3721229bb53ba4d422cf64dad58f6191cb2224f9a2b51d3fc4f71e8c737c2f62` |

All individual stage/adapter/response hashes remain bound by the exact completion inventories above and the whole regular-file map digest. No additional result file was generated or modified to carry those checks.

## Actions and outputs

Created only:

- `/tmp/astra_actual_memory_custody_audit_20260913.md` — this audit.
- `/tmp/astra_actual_memory_custody_check_20260913.py` — separately scoped optional stdlib helper.

No archive extraction; no imported/executed archive code; no native/model/GPU/tokenizer calls; no remote or live-process checks; no score reduction; no evidence repair; no repository edits, staging, commits, or changes to another agent's files. The older throughSEQ151 manuscript acceptance and R1 addendum are not updated by this separate custody audit.
