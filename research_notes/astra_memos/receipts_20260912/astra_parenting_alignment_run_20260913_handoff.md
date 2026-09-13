# Parenting alignment inference runner

September 13, 2026. EDITSTOP — runner and CPU fixtures frozen against final core.
Only this handoff, the new runner, and its matching test are owned. No native
preparation, GPU/model execution, result retrieval, launch or collection occurred.
Main owns all native operations. This adopts only proposal sections 1–3, no SLEEP.

## Coordination status

Main's outer interface is compatible without changes: `verify -> (plan, bound)`;
`bound["probe"].gpu_state(plan)`; `allocation(plan)`; `plan["limits"]["fits"]`
and `plan["limits"]["updates"]` are zero. Root naming is not hardcoded.
Closed spec keys remain as accepted below. Native Python comes from the original
parent plan: `/localhome/local-rohing/v2/venv/bin/python`.

Runner uses Beauvoir's base APIs and has passing 104-call/all-invalid fixtures.
Main supplied final core EDITSTOP; source checks require its exact digest below.
Core test digest reported by Main:
`639bf348f931cf5223e71093ce7a6c740785cd1b43207236bbd9bf45f0d17195`.

## Stable API

```python
prepare(root, spec_path, spec_sha256, allow_native=False)
verify(root, plan_sha256, native=False) -> (plan, bound)
allocation(plan)
worker(root, plan_sha256, arm, allow_gpu=False)
controller(root, plan_sha256, allow_gpu=False)
collect(root, plan_sha256, completion_sha256, out)
```

Single seed, fixed arm order `ALIGNED`, `SWAPPED`, `NO_PARENT`; states are
`perception_seedN_ARM`. Each arm is a fresh subprocess and cold adapter load.
Main's three single-seed invocations cover all three original pre-memory roots.
Never initialize from memory/coaching/replay descendants. No fit code exists.

Core seam used directly, no wrappers or monkeypatches:

```python
deps = core.load_dependencies(source_root, protocol_path=protocol_path)
manifest = core.build_manifest(deps, prior_ids=prior_task_ids)
capture = core.run_phase(state, backend_callback, deps, binding=identity)
audit = core.replay_validate(capture, deps)
summary = core.summarize(captures, deps)
```

Identity binds original `producer` learner seed, parent plan, adapter inventory,
base files, route and inference parameters. Backend callback returns only
`request_id`, `state`, untouched `raw`, `finish_reason`. Full native receipts
are saved separately. No teacher targets/repairs, fence repair, retries or
filtering of a failed restatement. Task-local reset and current-restatement-only
visibility are delegated to the pinned core and replayed for every task slot.

## Closed specification

Exactly these keys:

```text
runner_sha256
core
protocol
capture_runtime
parented_runtime
parent_source
native
public
archive
source_root
prior_task_ids
seed
gpu_index
gpu_uuid
expected_boot_id
lease_end
```

`core`, `protocol`, `capture_runtime`, `parented_runtime`, `parent_source`,
`native`, `public`, `archive`, `prior_task_ids` each have exactly
`{"path": "/absolute/native/path", "sha256": "full digest"}`.
`source_root` is an absolute string. `prior_task_ids` binds a JSON array of
unique nonempty strings; Main's supplied 284-ID inventory hash is
`bcfb7aed8ac07b4c90698f796046270f40bccd3a33bcf3f81e0cf51a3adfcf7e`.
The runner checks the bound inventory's actual bytes and disjointness, not an
invented native pathname. `seed` must be integer 0, 1, or 2; `gpu_index` is an
integer; `gpu_uuid` is the Main-allocated UUID. `expected_boot_id` is the current
boot UUID; `lease_end` is a finite Unix timestamp. Main supplies these values
after fresh reservation/placement checks. Holder CVD retains the allocation;
controller CVD must be empty; each worker CVD is exactly the bound GPU UUID.

Required pins and source names:

| Binding | Source | SHA256 |
|---|---|---|
| protocol | native copy of `ASTRA_PARENTING_ALIGNMENT_DEV_2026-09-13.md` | `5c53d6aa850b3a3a409c255ab9b28ce3b090f7325f35688437e42a86b1cccce5` |
| core | `/tmp/astra_parenting_alignment_core_20260913.py` | `71311d3d9add1f485289c6ee6824ef758393193ee05bcc088674d12697b11010` |
| capture_runtime | `/tmp/astra_own_source_replay_capture_20260913.py` | `1142593afb544dec2344c77788f6dbb624f519897b0bb65e135a9e8eb1910107` |
| parented_runtime | `/tmp/astra_parented_record_run_20260913.py` | `54cad8a6eeb5ae8af08213efe60f4c8047879991ca77f7a30d8be548659699f8` |
| parent_source | `/tmp/astra_own_source_replay_core_20260913.py` | `f64e65a462afe7c2ed28d3dae16289d12bfc62b624b8d4900ff66a713f105f1a` |
| native | `/tmp/astra_level1_real_record_run_20260913.py` | `3c03304ee5309517ce34f91b121594f0070b37bfb14f31f429f915d8310cc20e` |
| public | `/tmp/astra_birth_skill_probe_run_20260913.py` | `59874c678ce1b36feaa1969721c0dcc761b4fa05072a6231892269991201052c` |
| archive | original `node2_second_perception.tar` | `addc2e61ce05f2b622482adde82f16c2c571db6dd072b0fb7750a4d6dc559a3a` |

Frozen world root is `/tmp/astra_level1_real_record_source_20260913_attempt1`.
The original archive is authenticated via pinned `parent_source.original_inputs`;
its exact original plan bytes supply environment/base/chat-template/engine pins.
No old outcome collector is invoked. The new bundle snapshots all direct modules,
protocol/prior inventory, transitive old parented/formation/projector/Level1
material/trainer/lifecycle helpers, and the union of pinned public-world sources.
Original model/adapter/archive are read-only referenced inputs, not copied weights.

## Native commands — Main only

After staging final source dependencies and creating the closed spec, use the
original native Python and empty CVD for preparation/controller/collection:

```bash
PY=/localhome/local-rohing/v2/venv/bin/python
RUNNER=/tmp/astra_parenting_alignment_run_20260913.py
ROOT=/localhome/local-rohing/astra_diagnostics/parenting_alignment_seed0_20260913_attempt1
CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 "$PY" -B "$RUNNER" prepare \
  --root "$ROOT" --spec-path "$SPEC" --spec-sha256 "$SPEC_SHA256" --allow-native
```

Preparation returns `plan_sha256`, `seed`, `states`, `limits`, `prepare_seconds`.
Main's holder launches this command while maintaining its own reservation:

```bash
CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 "$PY" -B "$RUNNER" controller \
  --root "$ROOT" --plan-sha256 "$PLAN_SHA256" --allow-gpu
```

On success only, Main's once-only orchestration uses returned `completion_sha256`:

```bash
CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 "$PY" -B "$RUNNER" collect \
  --root "$ROOT" --plan-sha256 "$PLAN_SHA256" \
  --completion-sha256 "$COMPLETION_SHA256" --out "${ROOT}_collected"
```

Do not call `worker` directly; controller binds its exact command, process group,
PID/startticks, exit and release receipts. No command above was executed here.
Native CPU prepare is Main-only and remains required before launch. Main owns
fresh physical UUID checks, shared reservation checks, and holder receipts.

## Budgets, custody and outputs

- Prepare180 seconds, controller3600 seconds, collection180 seconds, each from
  its own entry including runtime bootstrap/verification. Controller budget
  includes all workers and cleanup. Six-hour lease finish margin is mandatory.
- Three cold states; 36/36/32 maximum calls; 104 per seed /312 campaign.
  Restate160, wake256, record384 output-token caps; temperature0/generation seed0.
  Four contacts per lesson arm, all16 tasks per arm including invalid/uncalled.
- Native preflight checks exact original chat template and static context limits.
  Equal lesson multisets are required; individual P/C literal lengths may differ.
  Every actual dynamic context is rendered before generation, never truncated,
  then independently re-rendered from saved raw history during collection.
- Native output receipts retain raw text, decoded text, native token IDs, route,
  finish, timestamps and source-bound request. Malformed/length outputs are
  outcomes. Decode/route/source/native-custody faults abort and preserve files.
- Owned process-group cleanup and fresh GPU vacancy are checked after each arm;
  stage and cleanup failure receipts both survive. All three process identities,
  starts/exits/releases, dynamic calls, all16 task records and failures replay.
  Stage spans must fall inside controller-entry/deadline receipts.
- `plan.json`, `manifest.json`, `preflight.json`, `original_plan.json`, `spec.json`,
  `sources/`, `source_snapshot/`, preparation receipts preserve input bindings.
  `run/ARM/` contains launch/start/identity, numbered request/response receipts,
  `capture.json`, `core_calls.json`, `closed.json`, done/exit/release and logs.
  Controller writes `capture_complete.json` only after all states replay/close.
- Collector validates everything before a once-only sibling collection claim;
  a failure after claim never authorizes retry. It writes `alignment_report.json`
  (full raw captures, replay audits, source/parent pins, per-arm and total actual
  token/call/generation costs, core summary, preflight), then `collection.json`
  binding report/completion hashes and elapsed collection time.
- A single-seed summary is deliberately a partial three-root vector. Native
  custody checks are separate from CPU core's unverified-native identity label.
  No outcome threshold gates capture/collection; no fit or promotion authorization.

## CPU verification and limits

24 runner tests PASS (6.011 seconds, final pinned-core check): real public
core replay with mock tokenizer/backend, full104/all-invalid56 calls, malformed
restatements/records, length finishes, all16 slots, dynamic prompt/timing tamper,
source snapshots/drift, boolean exit rejection, controller-entry span, bootstrap
budget accounting, failed precheck/no spawn, CVD/own cleanup, simultaneous faults,
once collection, partial summary, forbidden fit/old-controller calls.

```bash
PYTHONDONTWRITEBYTECODE=1 timeout 90s python3 -B -m unittest discover \
  -s /tmp -p 'test_astra_parenting_alignment_run_20260913.py' -q
```

Final owned source pins:
- Runner: `712248f1fc86b026e68e9cfbc791d3b441c6ded53db82f7622f8f2cd2b8b8c2a`
- Tests: `c1434e0acbf53a44e534d8a810263db8227eb59126e03a712c4c83df16660c0a`
- Handoff hash is returned separately to avoid self-reference.

Mock tokenizer tests do not certify native token lengths or GPU identity. Main's
native CPU preflight and launch-time custody remain necessary. Conservative
finite/lexical restatement scoring is not unrestricted semantic understanding.
The experiment estimates immediate task alignment of a lesson-to-restatement
package, not persistent learning, restatement mediation, H1/H2, or improved
retention. SWAPPED may interfere/help, NO_PARENT is not token-matched, and
second-delivery/order differences are descriptive. Zero fits/updates throughout.
