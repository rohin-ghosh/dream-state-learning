# C2 epoch2 — concrete local bundle ready; no remote staging or restart

Selected output: **prepared_epoch2_v2** (September 19, 2026 UTC).
`prepared_epoch2_v1` is retained earlier evidence; use v2's tightened standalone
guard-template verifier. Their runtime source bytes are identical.

## Exact closure and receipts

- `prepared_epoch2_v2/C2/epoch2/source/`: 184 Python files plus exact
  `context/R153_STARTUP.md`, files 0444/directories 0555, no symlinks.
- `prepared_epoch2_v2/C2/epoch2/EPOCH2_SOURCE.json`: complete source staging
  declaration, every pin and local origin, old native/guard/journal observation,
  original-to-epoch2 five-file delta and epoch1-to-epoch2 two-file delta.
- `prepared_epoch2_v2/C2_EPOCH2_BUNDLE.tar.gz`: verified portable bundle including
  source, standalone tools, plan template, CPU receipts and node invocations.
- `prepared_epoch2_v2/C2/epoch2/cpu/LOCAL_SOURCE_CPU.json`: **36 pass** = 17 unchanged
  retention case bodies, 5 existing contracts and 14 receiving integration tests.
- `epoch2_tools/PREPARER_TESTS.log`: **18 pass**, including exact preimage recovery,
  path/symlink/overwrite refusals, recipe preservation and historical point reads.
- `prepared_epoch2_v2/READY.json` and `EPOCH2_VALIDATION.json`: selected readiness
  and final independent hash/mode/archive verification. Earlier 142-hook-test
  receipts and all five retention ports remain unchanged.

All 183 epoch1 preimages were found locally and matched their staged hashes:
180 from the existing C2 source snapshot, three from the tested C2 retention port.
The extra runtime source is added only to the new local closure. There is no
remote source read, stage, live-source edit, signal, service-manager invocation,
parent delivery, bridge update, or dispatch in this work.

Manifest SHA256:
`399e47a4be85b62b7b1410a077ec45a80cb27f0425eb85f9f0ad25b7a46b2d7c`

Archive SHA256:
`0aa46ef3ae30e4f0d982bdf0faffa7412aae0460b09db22ae7088e093cde2d62`

Additional changes beyond epoch1:

| File | Before | After |
| --- | --- | --- |
| `gpu/orch_r125_continual_native.py` | `1bf18d5f34d2f027be1c79120ec654afe9869e647150245a29c8a19ebda81ff6` | `004042397f5bdec18bdd5cb26b30ed102ee94d70db1e4cea7ee85ff1936b2ebb` |
| `gpu/c2_retention_runtime.py` | absent | `350802c5c996c3f5856fbb84f771f663df364a67abe87b809ada15840c7591e1` |

The three retention changes are already present in epoch1. Thus the approved
old-live-to-epoch2 delta has five entries, not five additional edits to epoch1.

## Standalone source-specific CPU invocation

The bundle needs no import from this worker or the larger repository. All helper
bytes are copied into `C2/epoch2/tools/` and pinned outside the 184-file runtime
closure. The checkpoint/tail helper uses its same-directory `cpu_probe.py` and
`boundary.py`; the latter is the exact existing read-only boundary implementation.
The 17 retention case bodies are unchanged; only their bootstrap is rebound to
the exact tested source. Loaded GPU/organism modules are checked to remain there.

From this repository, the actual-source synthetic suite can be rerun with:

```bash
BUNDLE="$PWD/research_loop/workers/post_recovery_c2_retention_receiver_20260919/prepared_epoch2_v2/C2/epoch2"
CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 python3 -B \
  "$BUNDLE/tools/source_checks.py" --source "$BUNDLE/source" \
  --manifest "$BUNDLE/EPOCH2_SOURCE.json"
```

`C2/epoch2/CPU_INVOCATIONS.json` contains complete node-side argv arrays for
source verification, checkpoint, current-tail and synthetic source tests. The
proposed source destination is:
`/localhome/local-rohing/orch_retention_20260919/C2/epoch2/source`.
Only Main transports/stages it, to a new unused path, preserving epoch1.

The checkpoint helper defaults to the historically pinned COMPLETE **11502**,
SHA `9c59fe6c59a01948b6ffe894aaa681010346ccc671c2f774a10fe7399a49080f`.
It verifies that exact COMPLETE, matching LEARN and intents by bounded point reads,
then the original adapter/optimizer/RNG/state on CPU. This default is NOT a
current-handoff boundary. Selecting a newer completed checkpoint requires both
`--complete-index` and `--complete-sha256` from authentic evidence. Tail mode
requires a current COMPLETE/LEARN and otherwise refuses once without retry/signal.
No real C2 optimizer payload or node guard has been validated locally.

## Original r188 route — mandatory, unchanged

The only eventual launch route is the original
`/localhome/local-rohing/v2/venv/bin/python -B -m gpu.r188_node5_confinement dispatch --config <Main's actual receiving GUARD>`
with the new immutable source on PYTHONPATH and outer CUDA visibility empty.
This command was NOT invoked. A naked `orch_r125_continual_guard dispatch`, a new
service configuration, a capability/device-policy relaxation or bypass is not
an equivalent route.

Pinned r188 remains
`75eed0e5e57cd7463e46fa10adeeebdb80b9ef1ce5e76a9b527c034d1e8e6481`.
It requires actual `RECEIVING_CPU.json` matching the full new source pins, its
once-only outer claim, confinement probe, fresh privileged clear admission,
then the unchanged strict service: uid/gid2524, NoNewPrivileges, empty capability
sets, strict device policy allowing only GPU minor1 and required control devices.
Assigned UUID remains `GPU-7fc4e5b2-060c-ada8-8f91-3fe262c3573c`.
Old guard/stream/reader and `gpu/r184_cpu_bridge.py` are byte-identical.
The old bridge service/socket/guard are not changed or restarted here.

## Remaining blockers, owned by Main

1. Transport/stage and reverify the full closure; fresh exact old-native identity,
   five-delta source authority, builder/allocation and uid2524 access evidence.
2. Exact historical WALL_EXTENDED record + intent, current COMPLETE/LEARN,
   actual node checkpoint/guard/tail CPU proof and real receiving controls.
3. Parent delivery fence, zero in-flight work, preserved ledgers and Main's old
   bridge/parent rebinding readiness; explicit post-LOADED owner adoption only.
4. Original r188 admission/dispatch capability, and **actual reader latency gate**.

Main reports both pair read-only scans timed out at 90 seconds at 01:48 UTC.
That is not a C2 measurement, and these short synthetic tests certify no large
journal latency. The C2 reader is unchanged at
`972456b7d6cb026cc922e067114701d4f157fa6ed775e4406ecb52c86eef7d3e`:
it hashes retained prefix bytes, not O(tail), with no historical-body replay
fallback. **Main owns scanner/anchor repair; this worker did not duplicate it.**
Any later reader repair requires a newly pinned closure and authority, not an
in-place change to this sealed five-delta artifact.

Hard end stays **1789927200**. Neither local readiness nor the CPU helper output
authorizes live handoff, wall extension, bridge restart or parent rebinding.
