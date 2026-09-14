# Parallel scale inventory — September 14, 2026

## Scope and immediate result

Read-only worker inventory, observed **17:51:59–17:53:34 UTC**, following Main's
Rohin66 delegation. **Main retains all assignments, launches and stop decisions.**
No experiment/model/tokenizer was loaded; no GPU work, transfers, remote writes,
launches, kills, reservations or package changes were commanded. Only this note
was authored. Node labels and wrapper paths intentionally replace endpoints.

- **Node3:** all eight A40s, including previously problematic index7, currently
  visible; completed GPU and compute queries, no compute rows, no visible CVD
  owners. Existing local Qwen7B cache and venv; checked 37ec adapter/current
  source paths absent. Eight *candidate* slots, not eight delegated reservations.
- **A100:** all eight A100 80GB PCIe devices visible and idle under the same
  observations. Cache and venv available; checked 37ec/source paths absent.
- **Node2:** GPU0 remains Main's breadth collection resource. GPUs3–7 are idle
  candidates with the already-available parent/evidence environment; no worker
  assignment is made here. GPUs1–2 were also idle at the instant, but outside the
  requested additional-slot scope and not offered as unreserved resources.

GPU vacancy is time-local, **not a reservation or a guarantee of launch safety**.
Main's subsequent message schedules the next two1632-update fits on node2
GPU0/1; both are excluded from parallel worker assignment. The portable-bundle
worker owns staging; this inventory neither duplicates nor performs that work.
The `/proc` inspection emitted only PID, command identity and CUDA/NVIDIA device
visibility values; inaccessible environments were skipped. Thus absence of an
observable CVD owner does not prove absence of another user's reservation.
No service-exception/queue/reservation admission was performed. Main must repeat
the applicable physical/CVD admission checks immediately before assigning work.

## Access and applicable instructions

These exact minimal commands succeeded and returned `ACCESS_OK`:

```bash
bash gpu/ovx2_ssh.sh 'printf "ACCESS_OK\n"'
bash gpu/a100_ssh.sh 'printf "ACCESS_OK\n"'
```

The earlier node2 inventory also successfully used `gpu/ovx_ssh.sh`.
Wrappers use key-authenticated SSH with `BatchMode=yes`, `ConnectTimeout=15`,
and `ServerAliveInterval=30`; they source the existing managed host configuration.
That configuration and key/credential contents were not displayed or inspected.

Local root AGENTS instructions apply; no nested AGENTS files were found under
`gpu/` or `research_notes/`. On node3 and A100, no AGENTS files existed at the
checked root/localhome/home levels, while
`/localhome/local-rohing/dream-state/AGENTS.md` existed. Both remote copies contain
the earlier research deliberation contract without the newer local standing-
authorization section. This read-only inventory makes no architectural change;
remote stale instructions are not treated as authority to expand this delegation.

## Physical GPU and process snapshot

GPU table and compute-app queries both returned **exit0** on every checked node.
Every node3 device reported 1 MiB used and 0% utilization; every A100 device
reported 0 MiB and 0%. Both compute-app queries returned zero rows.

### Node3 — 17:51:59 UTC

Each device is an A40 with 46,068 MiB reported memory.

| Index | UUID | Observation |
|---|---|---|
| 0 | `GPU-0ee6f753-c61e-e18a-8aea-acccd3042939` | Idle candidate |
| 1 | `GPU-71e5a3e2-e9c8-5caf-70d8-73794ac34821` | Idle candidate |
| 2 | `GPU-41a86250-88eb-ed8a-ddfe-9d6f93515da1` | Idle candidate |
| 3 | `GPU-e1277146-04f2-c38f-d1ae-1a98132f907e` | Idle candidate |
| 4 | `GPU-f484c608-a2d4-0c26-dee1-a06cc5ae69e4` | Idle candidate |
| 5 | `GPU-bc211959-642d-664b-3581-42a0dbe434e9` | Idle candidate |
| 6 | `GPU-1a83d900-1e95-c7b4-9b12-8117399697f8` | Idle candidate |
| 7 | `GPU-319224de-e668-1822-d80b-4b24d15968ae` | Visible, idle candidate; no repair inferred |

### A100 — 17:52:01 UTC

Each device is an A100 80GB PCIe with 81,920 MiB reported memory.

| Index | UUID | Observation |
|---|---|---|
| 0 | `GPU-ff5f84e9-c70e-272d-a8e0-eb20aad05ac6` | Idle candidate |
| 1 | `GPU-604c4ea8-8c29-099e-76ed-571ec7d9be4b` | Idle candidate |
| 2 | `GPU-8e15ce78-4e9c-4c48-724f-2b753c6c2296` | Idle candidate |
| 3 | `GPU-631f3e6a-fbce-0ec5-b934-f08dd64634f8` | Idle candidate |
| 4 | `GPU-31583768-d90f-520c-51ed-5dac761526d0` | Idle candidate |
| 5 | `GPU-c1650c7f-ac26-f1a0-2ab8-c7354a6f27c9` | Idle candidate |
| 6 | `GPU-6de3930d-104a-f969-7d36-009271368dd1` | Idle candidate |
| 7 | `GPU-f0405a96-813d-7ac7-d641-3ec31d103037` | Idle candidate |

### Node2 — 17:53:33 UTC

| Index | UUID | Observation |
|---|---|---|
| 0 | `GPU-c70cba10-6ab6-a287-e2db-51dccd617ab0` | Main breadth; do not assign |
| 3 | `GPU-c9450d3d-0455-f034-b9bf-7f8956e44733` | 0 MiB, 0%, idle candidate |
| 4 | `GPU-d304a15c-516a-16a0-a926-a560304077cc` | 0 MiB, 0%, idle candidate |
| 5 | `GPU-0cc84073-37a0-4f7a-e555-11671425bd03` | 0 MiB, 0%, idle candidate |
| 6 | `GPU-a064bca2-bddc-73ad-faf1-a4fbcb49fecf` | 0 MiB, 0%, idle candidate |
| 7 | `GPU-7c213554-a6c0-5c5a-1117-0422c8eee4ed` | 0 MiB, 0%, idle candidate |

Only compute PID **411252** appeared, using 15,642 MiB on GPU0. The GPU table
reported 15,651 MiB / 92%. Visible CVD records were timeout PID411251 and Python
PID411252, both bound to GPU0's exact UUID and module
`gpu.astra_goal_breadth_collection`. Main supplied guardian410134; its lifetime
was not independently checked here. On-disk expose and teach results existed,
with80 and192 call files; baseline had106 call files and neither RESULT nor
FAILED yet. This is a progress snapshot, not a new scientific outcome claim.

## Storage, memory and runtime

`/`, `/tmp`, and `/localhome` resolved to the same reported filesystem on each
node. Reported available disk was **744G node3**, **2.7T A100**, **458G node2**.
MemAvailable was respectively **1,045,320,716 kB**, **1,044,931,560 kB**, and
**1,039,860,844 kB**. Node3/A100 had no swap. These are point-in-time capacity
readings, not memory reservations.

All three nodes have `/localhome/local-rohing/v2/venv/bin/python`; node3/A100
reported Python3.12.3. Distribution metadata matched across the three nodes:

| Distribution | Recorded installed version |
|---|---|
| torch | 2.13.0 |
| transformers | 5.5.3 |
| tokenizers | 0.22.2 |
| peft | 0.20.0 |
| safetensors | 0.8.0 |
| accelerate | 1.14.0 |

These were `importlib.metadata` reads, **not imports of those packages**.
Imported Torch CUDA build suffix, CUDA initialization and native-runtime parity
remain untested; matching distribution versions is not a native prepare PASS.

## Frozen base and tokenizer availability

The same snapshot directory exists on node3/A100 and is the model path bound in
node2's current breadth prepare evidence:

```text
/localhome/local-rohing/.cache/huggingface/hub/models--Qwen--Qwen2.5-7B-Instruct/snapshots/a09a35458c702b33eeacc393d103063234e8bc28
```

On node3 and A100, all four index-referenced safetensor shards resolve as files.
Their sizes, in shard order, are **3,945,441,440; 3,864,726,352; 3,864,726,424;
3,556,377,672 bytes**. Tokenizer JSON/config, vocab, merges, generation config,
model config and shard index are present. Model config reports `qwen2`,
`Qwen2ForCausalLM`, hidden_size3584,28 layers,bfloat16. Its historical
`transformers_version=4.43.1` is model metadata, not the installed runtime version.

Small-file hashes were identical between node3 and A100:

| File | SHA256 |
|---|---|
| `config.json` | `7463bb0ea78315365e6c6b74de4e73bbcc8359dfb0c5a737584e077d42c0b03c` |
| `model.safetensors.index.json` | `624bf7c47cd12468fdc16e38a47cf4f19e0415b859a223ba3c027eed2f0e1028` |
| `tokenizer.json` | `c0382117ea329cdf097041132f6d735924b697924d6f6fc3945713e96ce87539` |
| `tokenizer_config.json` | `5b5d4f65d0acd3b2d56a35b56d374a36cbc1c8fa5cf3b3febbbfabf22f359583` |

Full shard hashes, frozen tensor hash and tokenizer encoding behavior were not
rechecked. Existing cache presence avoids an assumed mandatory15GB retransmit;
Main still needs the normal file/base/tokenizer checks before use.

## Parent37ec and migration boundary

Node2 has the completed parent at:

```text
/tmp/astra_event_two_hop_lesson_20260914_attempt1/train/adapter
```

Its train result reports COMPLETE and adapter state
`37ec37884e4b0b679edd1dba1be1dec3474589e992649f3a33e7e3b1ec78b8c0`.
The result-file SHA256 read here is
`860ea1e95274b9a5c651c8c0ea2e640ecf47d94299eb5dd310ecb138eec78bc7`.
The three adapter files were independently byte-hashed in this inventory and
matched that result's recorded manifest:

| File | Bytes | SHA256 |
|---|---:|---|
| `adapter_model.safetensors` | 80,792,096 | `3f7029b84d41f0715ee8d11c8fc12540717bc24029abd7d03e999f79ee3ec5f1` |
| `adapter_config.json` | 1,263 | `8570d55121e5624b693201d2c013abba927917e51fc6abbccb94d22016da7683` |
| `README.md` | 5,416 | `1b1a685a0798f66ef71e870c1b87713d92814d912c47297127c119e751d3ea33` |

This verifies bytes against a saved manifest, not a fresh tensor-state load.
On node3/A100 the standard lesson root, old goal-pair collection root and new
breadth collection root were absent. A bounded depth4 search of `/tmp` and the
user home found no `*two_hop_lesson*` paths; deeper/differently named copies are
**unknown**, not proved absent.

Both nodes have `/localhome/local-rohing/dream-state`, but the checked files
`gpu/astra_goal_breadth_collection.py`,
`organism_v6/experienced_event_goal_breadth.py`, and
`gpu/astra_experienced_event_microloop.py` were absent there. Do not assume that
old tree is the current frozen source. Other archived source locations were not
exhaustively searched.

**Practical migration distinction, for Main's decision:**

1. Runtime essentials are the current source archive/commit marker, the small
   37ec adapter/config, and verified existing local base/tokenizer/runtime.
   The whole historical adapter forest is not a computational prerequisite.
2. The **unchanged current collector's admission** additionally calls through
   `prior.load_inputs` / `memory.load_inputs`, verifies source receipts and
   prior exposures, and traverses the known base-after, campaign, audit, repair,
   cycle, lesson, transfer and prior-goal collection paths. Source+adapter alone
   will therefore **not** pass that loader. Transfer its selected evidence
   closure, preserving required paths/manifests; do not silently skip checks.
3. Relevant top-level roots are the existing CLI paths for
   `astra_adult_cycle2_20260914_attempt1`,
   `astra_reader_audit_lesson_20260914_attempt1`,
   `astra_actual_reader_audit_20260914_attempt1`,
   `astra_selected_reader_repair_20260914_attempt1`,
   `astra_fresh_reader_cycle_20260914_attempt2`,
   `astra_event_two_hop_lesson_20260914_attempt1`,
   `astra_event_two_hop_transfer_20260914_attempt2`, and
   `astra_goal_pair_collection_20260914_attempt1`. This inventory did not compute
   or migrate an exhaustive minimal transitive payload; its size is **unknown**.
4. Node2 slots3–7 avoid that cross-node staging prerequisite. Node3/A100 are
   plausible parallel collection/articulation/critique capacity after Main's
   source/adapter/evidence staging and task assignment, without needing to wait
   for breadth *scores*. This is an option, not authorization to duplicate the
   existing learner's sequential stages or mutate its treatment.

## Lease grounding and unresolved clocks

No provider/lease control plane was queried. Dates below are local runbook
evidence, not independently refreshed lease attestations.

| Node | Grounded record | Scheduling interpretation |
|---|---|---|
| node2 | Launch prompt §15/addendum: September21,01:43 Pacific; coordination correction: **September21,08:43 UTC**, epoch1789980180 | Six-hour finish cutoff **September21,02:43 UTC** |
| node3 | Launch prompt addendum: September25,20:03 Pacific; September13 resource audit: **September26,03:03 UTC** | Six-hour finish cutoff **September25,21:03 UTC**; wrapper's older “September19” comment conflicts and is stale relative to these later records |
| A100 | Wrapper: September13,05:05 UTC through September26; coordination explicitly says exact expiry clock unresolved | Use the recorded conservative **September26,00:00 UTC** date-floor only as an early scheduling bound, not asserted expiry; corresponding six-hour cutoff **September25,18:00 UTC**. Exact provider time remains unknown |

Evidence locations: `research_notes/ASTRA_LAUNCH_PROMPT_2026-09-12.md` lines275,
340,363; `research_notes/analysis/2026-09-13_pcfl_vertical_dev_v2_resource_launch_audit.md`
lines27–35; `research_loop/COORDINATION.md` lines9590 and10242–10263; the three
named SSH wrappers. A100 GPU-hours must be reported as A100 GPU-hours, not silently
treated as A40 cost. Historical resource restrictions from specific older
protocols are not new assignments for this task.

**Release:** no capacity was claimed. Main can use this snapshot to assign the
next independent bounded work and select any required staging. All unknowns
above remain open rather than being promoted to readiness guarantees.
