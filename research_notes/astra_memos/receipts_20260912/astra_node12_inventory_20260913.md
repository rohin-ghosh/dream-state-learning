# Node1/node2 read-only operations inventory — 2026-09-13 UTC

## Final priority: node2 placement facts

Status: **bounded inventory complete; node2 model payloads verified; blanket GPU clearance NOT established**. Main owns all launches, kills, preparation, transfer and Git. This sidecar has made no remote changes, contacted no node3, downloaded nothing, and inspected no routing-secret contents. All remote reads use only `bash gpu/a40_ssh.sh` or `bash gpu/ovx_ssh.sh`. Only this report and the subsequently authorized `/tmp/astra_node1_preservation_delta_20260913.json` were written. Last native operation completed **2026-09-13T04:35:19.022974Z**. Main will separately reserve its writer slots; these observations do not reserve them.

**Immediate handoff:** node2 model **14/14 actual payload SHA256s and sizes match** the exact local official-binding receipt; 15,242,807,270 bytes read, stable across each read. Native model/venv paths are ready for Main's independent CPU/native preparation. At 04:33:53Z all eight GPUs again had zero compute-app rows and no readable same-UID CUDA reservation; persistent unreadable `systemd`/`sd-pam` identities are pinned below, not excluded. The exact node1 preservation roster has **346 missing + 2 changed files, 7 missing adapter weights, and 419 source-snapshot members**, with actual source payload hashes.

### Node2 GPU/process snapshot

Observed 2026-09-13T04:29:11.913093Z–04:29:25.691102Z. Both NVIDIA queries exited 0 (6.825s and 6.917s), each allowed 60s. All eight A40s: total 46,068 MiB, used 0 MiB, reported free 45,489 MiB, utilization 0%, compute mode Default. **Zero used memory alone is not evidence of availability.** Compute-app query returned zero rows across the node. No active life, model server, writer, controller or CUDA reservation appeared in readable same-user processes.

**Refreshed 04:33:39.085698Z–04:33:53.378783Z:** UUID/index mapping unchanged; every GPU still used 0 MiB, reported free 45,489 MiB, utilization 0%; compute-app query again empty. Queries exited 0 in 7.595s and 6.662s with 60s timeout each. Environment scan again 13 same-UID processes / 10 readable / 3 unreadable / 0 vanished; no readable CUDA reservation. Only workload-pattern match was the existing queue runner. Exact `pending` and `running` directory listings were empty, not just `.job` glob counts.

| Node2 index | Exact physical UUID | Reservation/clearance status |
|---|---|---|
| 0 | `GPU-c70cba10-6ab6-a287-e2db-51dccd617ab0` | No observed compute PID/readable-env reservation; unreadable-env gap |
| 1 | `GPU-e7a322fc-fe84-919f-7534-cdfefb6ce1e4` | Same |
| 2 | `GPU-d2db2a6a-a308-1782-bf41-e41411d8dc05` | Same |
| 3 | `GPU-c9450d3d-0455-f034-b9bf-7f8956e44733` | Same |
| 4 | `GPU-d304a15c-516a-16a0-a926-a560304077cc` | Same |
| 5 | `GPU-0cc84073-37a0-4f7a-e555-11671425bd03` | Same |
| 6 | `GPU-a064bca2-bddc-73ad-faf1-a4fbcb49fecf` | Same |
| 7 | `GPU-7c213554-a6c0-5c5a-1117-0422c8eee4ed` | Same |

UID 2524: 13 same-user processes, 10 readable environments, 3 unreadable. Readable environments contained none of `CUDA_VISIBLE_DEVICES`, `NVIDIA_VISIBLE_DEVICES`, `CUDA_DEVICE_ORDER`, `VIRTUAL_ENV`, `CONDA_PREFIX`, `HF_HOME`, `HUGGINGFACE_HUB_CACHE`, `TRANSFORMERS_CACHE`, `HF_HUB_OFFLINE`, `TRANSFORMERS_OFFLINE`, `PYTHONPATH`. Unreadable PIDs: **36935 (`systemd`), 36938 (`(sd-pam)`), 4004946 (`sshd`, inventory connection)**. These were recorded, not bypassed or silently excluded. A positive all-process reservation clearance cannot be issued from these observations. Snapshot does not reserve any GPU and must be refreshed by Main's existing prelaunch gate.

#### Unreadable-process identities, not blanket exemptions

Re-read after model hashing at **04:34:33.882014Z**. Both persistent daemons have the same identity tuples as the 04:33:53Z scan. This supports distinguishing the fixed session-daemon pair from new writer processes, but **does not reveal their environments or grant an exclusion**.

| PID | comm | PPID | `/proc/PID/stat` start_ticks (field 22) | `/proc` owner UID / real,effective,saved,fs UIDs | `exe` readlink | `environ` |
|---:|---|---:|---:|---|---|---|
| 36935 | `systemd` | 1 | 4243834 | 2524 / 2524,2524,2524,2524 | PermissionError | PermissionError |
| 36938 | `(sd-pam)` | 36935 | 4243835 | 2524 / 2524,2524,2524,2524 | PermissionError | PermissionError |
| 4006398 | `sshd` (hash-inventory session parent) | 4006351 | 50249943 | 2524 / 2524,2524,2524,2524 | PermissionError | PermissionError |

Exact raw-cmdline SHA256s: systemd `3127082f907652bfa48e38fddcaf16c3e73b2da5a2d64602eafe88869c222925`; sd-pam `971490059d839d27af3ded30a476216b92689d837b0236a700723fb13640e370`; inventory sshd `33000acd013adbf8dbb593c9baf3f7acaa8911db00e85f90a5abc6cd25afcc44`. Initial sanitized argv[0] for systemd was `/usr/lib/systemd/systemd`; that is **not** a successful `/proc/PID/exe` verification. No arbitrary environment values were printed.

The preceding GPU-refresh session had sshd PID **4006199**, PPID 4006152, start_ticks 50245804; the original session had PID 4004946. Each is session-specific and may exit when its wrapper call returns. No post-disconnect absence claim is made. Later metadata sessions can create different sshd PIDs. **Never turn this inventory session identity into an exemption for all sshd or all unreadable processes.** Queue runner identity at refresh: PID1823897, PPID1, start_ticks38585717, UID2524, cmdline SHA256 `0f805a1a3fdf823a1289c5e03b560d55ef73f59b9d3486f1b56ac3d0d54d9455`.

Queue runner PID **1823897** is alive, environment readable with no CUDA selection. At 04:30:58Z, `~/queue/pending` and `~/queue/running` each contained **0 .job files**; done 62, failed 7, rejected 4. Last state-changing runner line: 03:11:59Z, last job `fable_fill_offnoise_n2_s1010` done rc=0, runner-reported pending=0/running=0. The runner remains capable of accepting subsequent jobs; this is not an exclusive allocation. No current active life identity observed; absence of a `LIFE_DONE` file elsewhere is not an active process.

### Node2 runtime and model: no download needed

- Python: `/localhome/local-rohing/v2/venv/bin/python`, executable and resolves to `/usr/bin/python3.12`; `-B --version` succeeded with **Python 3.12.3** at 04:31:40Z.
- Installed package metadata: torch 2.13.0; transformers 5.5.3; peft 0.20.0; accelerate 1.14.0; vLLM 0.27.1; triton 3.7.1; safetensors 0.8.0. Imports/native module compatibility not tested by sidecar.
- Frozen base path: `/localhome/local-rohing/.cache/huggingface/hub/models--Qwen--Qwen2.5-7B-Instruct/snapshots/a09a35458c702b33eeacc393d103063234e8bc28`.
- All **14 snapshot files** exist with readable symlink targets. Initial small-file hashes and shard pathname/size checks were superseded by **actual complete SHA256 reads of all 14 files at 04:34:20.437023Z–04:34:33.882014Z**, taking 13.445s. All 14 sizes and hashes matched the exact local official-binding receipt; all size/mtime/inode tuples were stable across each read. Total file bytes 15,242,807,270. Index references exactly four available shards; tensor total size 15,231,233,024 bytes (different from complete file bytes because of headers and non-weight files).
- Node2 available filesystem bytes at 04:31:40Z: **556,249,194,496** (`df -B1 --output=size,used,avail,pcent,target`). This is disk, not GPU memory.

Actual node2 shard payload results (the ten other payload hashes also match the receipt):

| File | Actual bytes | Actual SHA256 | Match / stable |
|---|---:|---|---|
| `model-00001-of-00004.safetensors` | 3,945,441,440 | `a1333e6293854747c481288ea83b348226af178dd565c49b6f9495ba1966aba7` | Yes / yes |
| `model-00002-of-00004.safetensors` | 3,864,726,352 | `f5d25a2772cb825164a2a2c0fb6d51a87e282abf21e4dd75bc5cfb3cd0ea6185` | Yes / yes |
| `model-00003-of-00004.safetensors` | 3,864,726,424 | `8efdec4c1bc12317ae1a38dc42b595ce777738a64deea3fcb8a0a91381bcdfd5` | Yes / yes |
| `model-00004-of-00004.safetensors` | 3,556,377,672 | `1a72d403cdf0c1ec3cb7f289f17b394a01e64394c2e9b3c0f94dbce3faf879bd` | Yes / yes |

### Public binding availability

Already available in the **local VM checkout**, not freshly fetched:

- `research_notes/astra_memos/receipts_20260912/astra_qwen_public_binding_receipt_20260913_attempt1.json` — 3,399 bytes; SHA256 `e87abf9c83845a32bb5df3828901dde1929e86a57fa0278158d4101b7df9a019`.
- Receipt checked at 2026-09-13T01:48:48.855692Z; revision `a09a35458c702b33eeacc393d103063234e8bc28`; status `PUBLIC_REVISION_FILES_MATCHED_PROSPECTIVE_BINDING`; 14 files. `clean_lineage_certified=false`, `historical_receipts_changed=false`. This does not erase contamination labels or certify historical lineages.
- `research_notes/astra_memos/receipts_20260912/astra_qwen_official_metadata_20260913_attempt1.txt` — exists, 10,417 bytes; actual SHA256 **verified at 04:33:53.439279Z** as `8aebd0fc61d42917fedbf3c6dd08e39c36eac4c92478c88f2accabadae78de3b`, matching the receipt. An optional whole-text JSON decoding attempt failed; the raw-byte SHA256 check succeeded. This sidecar did not refetch or reinterpret the original metadata acquisition.
- `research_notes/astra_memos/receipts_20260912/astra_constraint_model_pins_20260912.json` — 1,508 bytes; SHA256 `1eabd0c22cc9857aac467edfb766666bff7c3650dafe5241515435c445965139`.

**Native receipt gap:** the exact public-binding receipt and constraint-pin paths beneath `/localhome/local-rohing/dream-state/research_notes/astra_memos/receipts_20260912/` are absent on both node1 and node2. No `*qwen*` receipt candidates found in their `astra_sources` or repo `research_notes`. Their presence on the VM must not be misreported as availability to a node-local preparation process. No receipt/source was copied by sidecar.

### Three bounded roots: what Main can and cannot infer

Each requested 10,800-second root is 3 hours. There are eight physically identified, apparently unoccupied node2 devices, but **zero unconditionally cleared slots from this sidecar**, because the same-user environment scan is incomplete. Node2 lease end supplied by user: **2026-09-21T08:43:00Z**. Node1 lease end **2026-09-14T23:14:00Z**, transfer deadline **2026-09-13T23:14:00Z**. These dates are user-supplied, not allocation-control-plane verified. No new allocation.

The inventory supports Main selecting three distinct UUIDs only after its existing reservation gate resolves the recorded unreadable-process gap, the new module passes CPU/native preparation, and exact new output roots are checked nonexistent and distinct. No root names were supplied; no names have been allocated or created here. Old life/adapter/diagnostic paths must not be reused. This is not a launch proposal or permission to override Main's gate.

At 04:33:53Z, node2 `/localhome/local-rohing/astra_diagnostics` and `/localhome/local-rohing/astra_writer_roots` did **not** exist. This is a namespace observation, not suggested root names or a claim about future availability. Existing canonical node2 lives in `~/v6_out` include R2_B seeds2/3/4/7/8, R3_B seeds503/504/505, R4_B seeds600/601/602/603, RP_B seeds400/401; all had top-level `LIFE_DONE` at 04:30:58Z. None was an observed running process. Other historic diagnostics and lineages also exist in `v6_out`; leave all existing paths untouched.

## Node1 GPU/runtime snapshot

Read-only snapshot **04:28:40.128481Z–04:28:55.674468Z**, not refreshed after Main prioritized node2. GPU query exit0/7.692s; compute-app query exit0/7.778s, empty. Each A40: total46,068MiB, used0MiB, free45,486MiB, utilization0%, Default mode. No readable same-user CUDA reservations. **These are candidate physical identities, not cleared slots.**

| Node1 index | Exact physical UUID |
|---|---|
| 0 | `GPU-5b370d4d-bdcc-21d5-cf06-e9bea52e602d` |
| 1 | `GPU-4b071167-a06a-773c-f947-60cb8c2f7512` |
| 2 | `GPU-35dcea35-12bc-f2f3-d5d2-d2eaa8bacdd8` |
| 3 | `GPU-4d0f10af-119f-10bb-a28f-f7b7703a3b14` |
| 4 | `GPU-f83fb491-34ce-4176-5852-c94652151a9f` |
| 5 | `GPU-2e7eb3b8-9b0b-3729-f5ff-2bbdad6a4a30` |
| 6 | `GPU-06b31c8f-7a96-d812-23f3-df3444d95397` |
| 7 | `GPU-6eac3b9d-551a-d786-f598-04ef6d701c98` |

Node1 UID2524:13 processes,10 readable environments,3 unreadable: PID2210434 systemd,2210439 sd-pam,2851305 inventory sshd. No exemptions applied; no writer/life/model-server process observed. Queue runner **207904** remains alive/readable with no CUDA selection. At04:30:13Z pending0/running0/done33/failed10/rejected9; last state change03:21:26Z reported pending0/running0, no lives/compute/own reservations. No launch/kill/queue edit performed.

Node1 has the same executable **`/localhome/local-rohing/v2/venv/bin/python`**, Python3.12.3 and package metadata versions as node2, verified04:31:39Z. Same 7B revision path and ten non-weight SHA256s; all four expected shard sizes and content-addressed blob names exist. **Node1 shard payloads were not rehashed.** Disk available2,744,807,968,768bytes. Existing 14B/32B/AWQ cache directories were only inventoried, not selected or loaded.

Historic node1 canonical lives with no top-level `LIFE_DONE` at04:30:46Z: R5_B seeds700/701/702/703, RP_B_seed402, R_B seeds1/2. They had no observed live worker; do not infer failure, resumption eligibility, or permission to duplicate them from marker absence. Their artifacts remain untouched.

## Node1 custody: already verified material risk

Metadata comparison at 04:32:07Z–04:32:11Z, regular files recursively, exact relative paths/sizes/nanosecond mtimes, no symlinks/errors:

| Tree | Files | Bytes | Adapter weights | Adapter bytes |
|---|---:|---:|---:|---:|
| Node1 `~/v6_out` | 15,428 | 96,975,926,735 | 753 | 90,458,428,888 |
| Node2 `~/mirror/node1_v6_out_2026-09-12T23` | 15,082 | 94,574,269,022 | 746 | 88,197,329,712 |
| Node2 `~/mirror/node1_adapters_2026-09-12` | 3,719 | 76,194,875,875 | 698 | 76,193,721,808 |
| Node2 own `~/v6_out` | 14,139 | 91,045,930,028 | 734 | 83,936,726,544 |

**The dated full mirror is stale:** 346 source files absent (2,401,655,352 bytes), including **7 adapter weights**; 2 additional files differ in size and mtime. No mirror-only files. Missing scopes: `off_noise` (42 files), `pretest_write_ab_AC` (17 files), `pretest_write_ab_Arep` (287 files). Top-level `off_noise` and `pretest_write_ab_Arep` are completely absent. Changed existing files: `pretest_write_ab_AC/R4_B_seed606/probe_OFF_disjoint.out` (11,697 vs 9,560 bytes), and `pretest_write_ab_AC/R4_B_seed606/timings.jsonl` (1,000 vs 776 bytes). No changed adapter sizes/mtimes among files present on both sides; this is not a full payload-hash comparison.

The older adapter-only mirror is not a substitute: 55 current adapter files absent, 11,709 total source files absent. It cannot certify custody of ledgers, transcripts, controls, source, or subsequent writes.

Outside `v6_out`: node1 `~/astra_sources` contains **419 files / 11,018,858 bytes** in source directories `0babc3ccbe1f2378a61dd0dac6f18f7371b82176` and `125ba29df6e1060e4e412742459dd75217193d2e`. Neither dated mirror scope includes this directory; node2 own `~/astra_sources` contains only `f2e5b65e9c5dc3f7b7cdf15cb1b97b114ad4994d` (209 files / 5,429,948 bytes). Off-node custody of node1's two executed source snapshots has not been established.

Node1 and node2 both have the 359,285,253-byte weights-excluded receipts archive `v6_out_receipts_2026-09-13T00.tgz`; native node2 path `~/mirror/node1_receipts_2026-09-13/v6_out_receipts_2026-09-13T00.tgz`. Both checksum sidecars claim SHA256 `f5a2ef3d9c2af3eaa7067fe072aafd8f7253a0cc3c8153e5fe635db611152b2a`; direct archive hash/structure checking was **not performed**, deliberately omitted after Main narrowed the task. Date labels and old completion markers do not certify the later source delta. No backup transfer was performed.

### Exact preservation roster delivered

`/tmp/astra_node1_preservation_delta_20260913.json` — **433,009 bytes**, SHA256 **`5e7ad05a3f1714d13f8977abb6b1e15c0d862733255f06b914a6b37424b48ffb`**, schema `astra.node1_preservation_delta.v1`, status `READ_ONLY_ROSTER_HASHED_STABLE`.

- After the initial complete metadata comparison, only its **three known delta scopes** were rechecked, 04:35:14Z–04:35:16Z. No broad rescan of other experiments. The missing346/changed2 counts and exact file roster remained unchanged.
- JSON contains **every missing and changed relative path**, exact source/mirror sizes and nanosecond mtimes, mode and symlink flag, and **actual source-payload SHA256** for all348 files. Reads were stable; each hash is bound to the reconciled stat tuple. No scan/hash errors. Seven missing adapter weights total **2,261,099,176 bytes**. Missing total2,401,655,352bytes; changed source12,697bytes vs mirror10,336bytes. Source-to-mirror byte deficit2,401,657,713bytes is not the same as the full payload size required to replace changed files.
- JSON also inventories/hashes **every member of both exact node1 `astra_sources` snapshots**:419 files /11,018,858bytes. This preserves the **roster and hashes**, not snapshot payloads. Main's future capsule/transfer remains necessary; neither snapshots nor adapter payloads were copied by sidecar.
- `0babc3ccbe1f2378a61dd0dac6f18f7371b82176`:210 files /5,579,472bytes; canonical member-manifest SHA256 `6806c85d35c5fc04aee2d5509c9d96dd5d24af407abd2321b3a985b6ec120b14`.
- `125ba29df6e1060e4e412742459dd75217193d2e`:209 files /5,439,386bytes; canonical member-manifest SHA256 `db59afe66db00f3e49b4f2facd638d0bc0dcb4c8534900da9d78f207feb5ae04`.
- Member-manifest hash serialization is `json.dumps(snapshot['files'], sort_keys=True, separators=(',', ':')).encode()`; sorted by snapshot-relative path. JSON includes exact wrapper argv, timestamps, exit statuses and SHA256s of read-only stdin programs. No routing values or file contents are embedded.

**Custody urgency at 2026-09-13T04:35:19Z:** node1 transfer deadline is **18h38m41s away**; lease end **42h38m41s away**. The current dated mirror omits real payloads and source custody is not established. A 3-hour root fits the supplied lease time in arithmetic only; this is not a scheduler or custody approval. Node2 is a leased second copy, not permanent preservation. Main owns the new capsule and all transfers/verification.

## Commands, times, status and limits

Transport for every native command: `bash gpu/a40_ssh.sh` (node1) or `bash gpu/ovx_ssh.sh` (node2), followed by `-o StrictHostKeyChecking=yes -o UpdateHostKeys=no -o ControlMaster=no -o ControlPath=none -o LogLevel=ERROR 'python3 -B -'`, with read-only Python on stdin. Transport stderr is withheld rather than exposing routing data. No direct SSH invocation, Git, signal, GPU workload, package import/download or remote file write by sidecar.

| UTC time | Read-only command / operation | Status |
|---|---|---|
| 04:28:00 | `pwd`; `date -u`; read applicable local `AGENTS.md`, `CLAUDE.md`, and the two allowed wrapper scripts, not their sourced routing file | Exit 0 |
| 04:28–04:29 | `nvidia-smi --query-gpu=index,uuid,name,memory.total,memory.used,memory.free,utilization.gpu,compute_mode --format=csv,noheader,nounits` on each node | Exit 0; 60s timeout each |
| 04:28–04:29 | `nvidia-smi --query-compute-apps=gpu_uuid,pid,process_name,used_gpu_memory --format=csv,noheader,nounits` on each node | Exit 0; zero rows; 60s timeout each |
| 04:28–04:29 | Same-UID `/proc/[0-9]*/{comm,cmdline,environ}` read; `cwd`/`exe` readlink; CUDA/runtime environment-key allowlist only | 10 readable, 3 unreadable per node; no exclusions |
| 04:29–04:30 | Read remote instructions, queue-runner code; enumerate queues, sources, model snapshots, life markers and backup file metadata | Exit 0; broad early output was truncated, important facts separately re-queried |
| 04:30–04:31 | Local receipt discovery via `rg`; JSON selected-key inspection; SHA256 local receipt files | Exit 0; no network retrieval |
| 04:31:39–04:31:40 | Native `v2/venv/bin/python -B --version`; venv/package metadata; snapshot stat/readlink and ten small-file SHA256s; exact receipt existence checks; `df -B1 --output=size,used,avail,pcent,target` | Exit 0 |
| 04:32:07–04:32:11 | Read-only `os.walk` + stat for native source/mirror trees, compare JSON manifests in local process memory; no manifest files written | Exit 0; no scan errors/symlinks |
| 04:33:39–04:33:53 | Node2 repeated GPU/index/UUID and compute-app queries (60s each), same-UID CUDA env scan, exact process stat/UID tuples, empty queue directory listings, namespace existence checks | Exit0; compute rows0; unreadable envs3 retained |
| 04:33:53 | Local official-metadata raw-byte SHA256 comparison | Match; subsequent optional whole-text JSON parse failed, overall combined shell exit1; no remote operation failed |
| 04:34:20–04:34:33 | Node2 Python `hashlib.sha256` streams every one of14 model files,8MiB chunks, compares exact official receipt SHA256/size; re-read fixed-daemon and inventory-parent identities | Exit0;14/14 match;15,242,807,270bytes;13.445s; all stable; exe/env PermissionErrors retained |
| 04:35:14–04:35:16 | Targeted metadata recheck of `off_noise`, `pretest_write_ab_AC`, `pretest_write_ab_Arep` on node1 vs dated node2 full mirror | Both exit0;346 missing/2 changed unchanged |
| 04:35:16–04:35:19 | Node1 source-payload SHA256 for348 delta files plus419 exact `astra_sources` members; before/after stability and earlier-stat binding | Exit0; all stable; no errors; roster saved locally via `apply_patch` |

Applicable instructions: local project `AGENTS.md` and `CLAUDE.md` read; no deeper files found in local `gpu`, `research_loop`, `research_notes`; remote scoped instruction search covered repo, `v6_out`, queues, source snapshots and mirror trees. Remote repo `AGENTS.md` is the older deliberation contract (SHA256 `1e3c413f3adbf172c409bc642bbf8242a736b0209461b6a7f81203450772f54e`); remote `CLAUDE.md` absent where checked. This task remains strictly read-only regardless of broader builder authorization.

Remaining gaps are explicit: unreadable same-user daemon environments/executables; no GPU reservation by sidecar; no CPU/native preparation of the new module; no node1 weight-payload rehash; no freshly certified full-mirror payload equality or archive restore; no executed capsule/transfer/onward durable custody. The new exact delta roster and node2 full-model hash comparison are complete. No reset, reboot, kill, launch, allocation or Git operation was proposed or executed.
