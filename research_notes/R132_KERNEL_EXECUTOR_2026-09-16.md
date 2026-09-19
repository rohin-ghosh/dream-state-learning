# R132 bounded kernel executor — real gated builder smoke passed

September 16, 2026, 10:04 UTC. Executor/test/note implementation only; no existing
CPU-profile, child, console, scheduler, lease or authentication edits. Main owns
the source/result bridge and integration. No commits/pushes. R136 subsequently
assigns node4 operator ownership; no additional inference launches in this task.

## Ready handoff and exact evidence

Node-local prefix **BASE**:
`/localhome/local-rohing/orch_r132_kernel_executor_20260916T093845Z`.

- Current source closure: `BASE/source_v9`; executor SHA256
  `034ddbdddfea960b97a3461366d9eebfc05a9ff053c9cc7ec497c565cdea66b7`.
- Root-owned runtime: `BASE/runtime_v2`; manifest SHA256
  `72b5447ce7636c5357a651952f59b96cfa024bd5617ba564091fcfc1cd32c3f5`.
  18,630 files / 5,098,446,534 bytes; preparation receipt
  `BASE/receipts/RUNTIME_PREPARE_v2.json`. Full manifest checked at admission.
- Actual **26-check gate passed**: `BASE/probes_v10/GATE.json`, SHA256
  `201c7ca12a222cfcc59ff4708ac8cb00a06387b93e724792f6b2d5613f597242`.
  Raw receipt/stdout/stderr/intent retained under modes basic/output/timeout/
  memory/files/gpu_context. Bound to source, dependencies, harness, task,
  runtime, command template, boot, driver and device identity; expires after1h.
- Real **BUILDER_TEST**, not child-produced, result:
  `BASE/smoke_spool_v2/dc437b48e5be3be5a4d44fa00ce3e5e7967e6609dcec1b0e917d29e27cadcc45/RESULT.json`;
  SHA256 `9e040d5c9860421ad9a4f23f910b21227e51cb68c6fd5349debe40ccfedb50e7`.
  Summary and separate post-job empty UUID census:
  `BASE/receipts/SMOKE_SUMMARY_v2.json`. Cgroup removed, exit0, no capture limit,
  129118 retained output bytes. First compile/launch **1.04746119s**.
- Raw source SHA256
  `0002410963c35d59f2ad79a81430598e51ebabd4cb304f368139a1d6c6d19a88`.
  Request, raw candidate, canonical kernel, immutable inputs, stdout/stderr,
  admission, intent and result all retained. CPU executor/parser/dispatcher/
  confinement/capture/bridge suites: **290 passed** after final repair.

| float32 length | Exact output | Torch ms | Kernel ms | Torch/kernel |
|---|---|---|---|---|
| 1 | PASS | 0.019456 | 0.033792 | 0.575758 |
| 1024 | PASS | 0.018432 | 0.033792 | 0.545455 |
| 65537 | PASS | 0.019456 | 0.033792 | 0.575758 |
| 1048576 | PASS | 0.029696 | 0.041984 | 0.707317 |

This fixture was **slower**, not faster. Times come from the operator-owned
CUDA-event driver, not child reports; they are one engineering observation,
not a general performance claim. Shared-host launch overhead and fixed inputs
limit interpretation. No child submission or console publication is claimed.

First smoke in `BASE/smoke_spool_v1` failed during candidate compilation because
`/sbin/ldconfig` is absent inside the root. Failure bytes remain preserved.
Non-material repair uses fixed `TRITON_LIBCUDA_PATH=/usr/lib/x86_64-linux-gnu`
against the existing read-only system library mount; no extra device/path
grant. Fresh source_v9, full probes_v10, new builder provenance/request and
fresh census preceded the successful second engineering test. No automatic
retry or unsandboxed fallback. Earlier probe/runtime failures also preserved.

## Stable request and measurement contract

`environment_schema()` returns the full example without Torch import/GPU use.
`make_request(source, origin)` and `parse_request(raw: bytes)` validate exactly:

```text
schema="R132_KERNEL_REQUEST_V1", task="triton_add_f32_v1",
source, source_sha256,
origin={kind:"BUILDER_TEST"|"TRAIN_CHILD_RESPONSE",
        record_index:nonnegative integer (not bool), record_sha256:lowerhex64},
request_id
```

Request ID hashes sorted compact ensure_ascii=True UTF-8 JSON excluding itself.
Source nonempty/no NUL/<=65536 UTF-8 bytes; encoded request<=100000 bytes;
duplicate keys, nonfinite JSON, unknown fields, invalid hashes rejected.
No child paths, arguments, imports, devices, shapes or environment overrides.

Source is **AST-allowlisted Triton only**, one `@triton.jit` function:
`add_kernel(left, right, output, size: tl.constexpr, BLOCK: tl.constexpr)`.
Fixed offsets/mask, SSA locals, bounded arithmetic/pure tl operations, masked
loads only from left/right+offsets and stores only to output+offsets. Imports,
loops, pointer rebinding, arbitrary top-level code/calls/attribute escapes and
host launch functions rejected. Raw source stays data; the trusted driver loads
only the operator-emitted canonical definition with trusted triton/tl globals.
This removes arbitrary candidate Python's ability to monkeypatch allclose,
events or reference timing; it is not a compiler/driver security proof.

Reference is `torch.add(left,right,out=output)` for contiguous float32 lengths
1,1024,65537,1048576; inputs `((index%257)-128)/8`, `((index%251)-125)/16`.
Host owns BLOCK256/grid, compilation, synchronization, three warmups and median
of20 CUDA-event measurements. Host independently decompresses bounded complete
outputs and checks every float32 byte. Errors preserve phase and traceback.
`timing_origin=TRUSTED_DRIVER_CUDA_EVENTS`, `timing_is_child_reported=false`,
`speedup_claim_authorized=false`. Raw output remains treated as untrusted data.

`run_request(raw, *, spool, runtime_root, gate_path, admission_path,
origin_verifier=None)` is Main bridge's interface. Child origin additionally
requires the trusted verifier's committed TRAIN request/response/commit hashes.
Gate, lease, fresh census and runtime admission precede dispatch. Admission
schema `R132_KERNEL_ADMISSION_V1` requires Main authorization, exact UUID/minor,
observed_unix<=60s old, expires_unix, hard_wall_unix, lease path/hash and>=150s
headroom. Fresh observation must postdate last attempted job. Operator booleans
are not authentication: never expose admission/spool paths to the child.

## Actual confinement and limits

Only assigned a40r **physical2**, UUID
`GPU-35dcea35-12bc-f2f3-d5d2-d2eaa8bacdd8`, PCI0000:41:00.0,
**actual minor1**. `/dev/nvidia1`195:1, shared ctl195:255 and uvm508:0.
GPU0 child protected; GPU7 occupied/not used. Exact device map rechecked.

Systemd transient root with DynamicUser, zero caps/NNP, private devices,
network/IPC, strict device cgroup/BPF, read-only runtime/reference/input,
no homes/credentials/shared working files, restricted process/FD views.
Device probe proves EPERM against synthetic195:254, never opens another
tenant's GPU. Inspector retains repeated DeviceAllow entries and checks BPF.
CUDA_VISIBLE_DEVICES is supplemental selection, not confinement.

Internet IPv4/IPv6 denied. CUDA needs **job-local abstract AF_UNIX** IPC;
AF_UNIX is allowed only within private namespaces. Actual negative connections
to synthetic host filesystem and abstract sockets both fail. No host socket
mount. This is isolation from host/external networking, not a claim that the
process cannot create any socket. PrivateIPC additionally separates IPC.

CPU200%, RAM4GiB/swap0, tasks64, service90s/stop2s, capture120s/1MiB,
files64MiB, private /work tmpfs512MiB. DynamicUser's implicit PrivateTmp defeated
earlier tmpfs policies: final /tmp and /var/tmp are explicit empty read-only
binds; actual write denial and /work ENOSPC verified. No host output mount.
Actual timeout/descendant, OOM, output, file/scratch and GPU-context-timeout
cleanup probes pass. Per-GPU lock, unique roots, no replay/retries, only owned
RootDirectory-matching unit cleanup. Per-job result conservatively records
GPU-context proof false; separate smoke census confirms empty afterward.

These gates establish observed boundaries on this boot/profile, not absence
of kernel/driver/Triton vulnerabilities. Shared control ioctls, arbitrary GPU
hang recovery and hardware-side noninterference are not proven. The bounded
loop-free add AST is the only supported task; do not widen it or interpret
the gate as authorization for arbitrary Python/CUDA or runaway kernels.

## Main runtime, model and lease handoff

Inference Python: `/localhome/local-rohing/v2/venv/bin/python`.
Sandbox uses `/usr/bin/python3 -I` plus sealed runtime_v2; successful smoke
reports **Torch2.13.0+cu130 / Triton3.7.1**. Model snapshot, never sandbox-mounted:
`/localhome/local-rohing/.cache/huggingface/hub/models--Qwen--Qwen2.5-7B-Instruct/snapshots/a09a35458c702b33eeacc393d103063234e8bc28`
(four shards observed; no model load by executor).

Existing lease: `/localhome/local-rohing/orch_rich_hot_node1_20260915_attempt1/LEASE.json`,
SHA256 `ac20665cb03ba0e2f8eebb0f7e441383334fbbf20b4a4e7125757ce7413ea8e6`.
No literal lease_end_unix: conservative UTC end converts to **1789776000**
(September19 00:00UTC), margin21600 gives hard wall **1789754400**
(September18 18:00UTC). No lease action or invented receipt.

Main may stage its independently owned verified publisher/bridge against
source_v9 now. Fresh gate/admission/census required; no valid committed child
candidate has yet been demonstrated. No inference child launch in this task.
