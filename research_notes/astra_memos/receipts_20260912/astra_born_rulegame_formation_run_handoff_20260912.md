# Born AUTH formation sidecar — EDITSTOP

**24 CPU tests PASS in68.230s.** Separate formation implementation only.
No changes to frozen birth driver/tests/launcher/dependencies, owner role module,
training/source inventories, writer or readout sidecars. No Git, native/model/
tokenizer/GPU/network/SSH execution and no live readout outcome inspection.
Only Main may choose progression after birth readout and authorize a launch.

## Frozen owned files

- `/tmp/astra_born_rulegame_formation_run_20260912.py`
  SHA256 `90919a280f78cce8f41c1ef7bf7b08e722f4ab0b3cf3d278d256bfd91653dda4`
- `/tmp/test_astra_born_rulegame_formation_run_20260912.py`
  SHA256 `1c84849bda1ef7661371f31ed231ea2faf6d3c4b757e4055840037c2f4ea8e61`
- `/tmp/astra_born_rulegame_formation_run_handoff_20260912.md` — this file;
  its SHA is returned separately.

Exact regression command and final log summary:

```bash
python3 -B /tmp/test_astra_born_rulegame_formation_run_20260912.py
```

```text
Ran 24 tests in 68.230s
OK
```

An unrelated existing `nursery_dialogue.py:43` ResourceWarning is emitted.
Tests reuse frozen birth fixture helpers and committed scripted role fixtures;
they never read actual birth/readout run roots or query a GPU/queue. The
isolated `_birth-pin` subprocess is exercised against CPU-authored fixtures.
For native CPU regression, import this test module, set `module.SOURCE` to
the new snapshot before unittest loads/runs its suite. `setUpClass` forwards
that setting to frozen fixture helpers. This is not native model acceptance.

## Source and dependency contract

Concrete new snapshot supplied by Main:

`/localhome/local-rohing/astra_sources/9f51595ec537885543976622b16273903578209e`

Main reports native/local source archive SHA256
`5938bc4dd3ea73a8f2418ed456d9fc6a255a0da58a853fa724fb0850f4911c80`.
No native archive operation was performed here. The old birth fit/readout
snapshot31b5535ec9f73f7b32fdaf21ccfc3a2a68a948a6 remains immutable.

Required unchanged local helpers:

- Birth runner `/tmp/astra_birth_conditional_run_20260913.py`, SHA256
  `072a1333c0411a73ae0fc46c6e70de9afe0bce9b49c74e01bdaae16174195daa`.
- Its safe metadata/safetensor/archive helper
  `/tmp/astra_rulegame_process_write_collect_20260912.py`, SHA256
  `e23160132bf4eac82f220b8066c49de3cf8461e50929f9a82f3eac5e12906892`.
- Committed role module SHA256
  `918b9d46bdb68423d8fe28c6ae92bde27aa4b47d183b72727f88767c36c6376e`.
- Birth corpus SHA remains
  `43bf074938e8c4e3a995e43d747ff24f2c6cf70252359cb35134391ff88da74b`.
- Existing snapshot vacancy helper SHA remains
  `a586b03bdb9c52f1061aa1e477ae983cc9d45ec0a2cd440642851fd8df8b609f`.

No monkeypatch of frozen runtime constants or source modules. The birth
runner's `read_plan`, `accepted_release`, `verify_plan`, `audit_terminal` and
`verify_fit(AUTH)` validate upstream completion. Default preparation executes
that normalization in a separate CPU subprocess, preventing Python's cached
`organism_v6` package from mixing old birth and new formation snapshots.
Every overlapping birth dependency must retain its exact bytes in the newer
snapshot. New role-specific hashes are additionally bound into the new plan.

## Exact normalization joins

`normalized_birth.json` binds:

- Exact user-supplied birth plan hash and released validation file hash.
- Full successful birth terminal, both member receipt joins and finite saved
  fits through the frozen validator, then the exact AUTH fit/adapter.
- `pin.completion_receipt_sha256` = SHA256 of original birth `run/result.json`.
- Separate `auth_receipt_sha256` = SHA256 of birth `run/AUTH/receipt.json`.
- Exact whole adapter file inventory plus the configured child loader identity
  subset (`adapter_config.json` and safetensor weights); same base files.
- Original birth source/driver/module hashes; immutable upstream evidence and
  capsule/vacancy hashes; `full_release=true`, `both_fits_complete=true`.
- Origin `SOURCE_AUTHORED_BIRTH_NOT_CLEAN`, model origin
  `UNRESOLVED_LOCAL_HASHES_ONLY`, `component_pass_required=false`.

The exact owner `completed_birth_adapter_pin_v1` is `normalized.pin` and its
value hash is `normalized.pin_sha256` using `diagnostic.value_hash`, NOT the
normalization JSON file's byte hash. Only AUTH is accepted by this sidecar.
No component scores, sleep material or evaluator annotations enter that pin.
Wrong/partial release, changed upstream evidence/adapter, wrong source or an
existing output root fails closed. No in-place retry or automatic new sample.
Reuse of the immutable AUTH adapter in explicitly chosen downstream phases
is expected; substituting a modified/written adapter is not accepted.

Read-only inspection of Main's permitted local fit validation confirmed SHA
`d403b48b645dcc5ebd971a6527108f21287fd722981f128c8780c58a2f1cf770`, completed
release flags, plan776871..., and capsule SHA
`d2460cb3be9b357ae1beecad84ae9bcfc7e76b61d296fb7b359ae9e68d8e2474`.
This inspected path/technical metadata only, not readout outcomes. Runtime
validation uses original native canonical paths, NOT renamed downloaded copies.

## Main commands — not executed here

Set `PY` to the exact native birth interpreter. Its spelling is preserved by
`os.path.abspath(sys.executable)`, without resolving a venv executable symlink.
Choose a fresh formation root and timezone-aware `DEADLINE`/`LEASE_END`.

```bash
SOURCE=/localhome/local-rohing/astra_sources/9f51595ec537885543976622b16273903578209e
FIT_ROOT=/localhome/local-rohing/astra_diagnostics/astra_birth_conditional_fit_seed0_20260912_attempt1
FIT_RELEASE=/localhome/local-rohing/astra_diagnostics/astra_birth_conditional_fit_seed0_20260912_attempt1_collection/validation.json
"$PY" -B /tmp/astra_born_rulegame_formation_run_20260912.py prepare \
  --source "$SOURCE" \
  --role-sha256 918b9d46bdb68423d8fe28c6ae92bde27aa4b47d183b72727f88767c36c6376e \
  --fit-root "$FIT_ROOT" \
  --fit-plan-sha256 776871143e25027479ae2c2d375687fc383abb113b1bb2fcf0cb1077700d03fa \
  --fit-release "$FIT_RELEASE" \
  --fit-release-sha256 d403b48b645dcc5ebd971a6527108f21287fd722981f128c8780c58a2f1cf770 \
  --out "$FORMATION_ROOT" --device "$DEVICE" \
  --deadline "$DEADLINE" --lease-end "$LEASE_END" --controller-seconds 900
```

Prepare is CPU metadata validation only: no native tokenizer, model or teacher
generation. It returns `root`, `plan_sha256`, `phase=formation`,
`status=PREPARED_NOT_LAUNCHED`. Old source31b lacks the born module and is not a
formation source. Preparation writes an exclusive start marker and preserves
failure; it never launches. Normalizer subprocess timeout300s is CPU work,
not a GPU reservation forecast.

Only AFTER Main chooses progression and owns a released GPU, the new Main
launcher runs this EXACT controller argv in a fresh session:

```bash
"$PY" -B /tmp/astra_born_rulegame_formation_run_20260912.py formation \
  --root "$FORMATION_ROOT" --plan-sha256 "$FORMATION_PLAN_SHA" --allow-gpu
```

Main keeps `CUDA_VISIBLE_DEVICES=$DEVICE` set continuously for the controller,
including verification and cleanup. There is no requirement to use currently
live GPU0; device is separately supplied to the new immutable plan. Do not
reuse or modify the live birth/readout launcher script.

```bash
"$PY" -B /tmp/astra_born_rulegame_formation_run_20260912.py status \
  --root "$FORMATION_ROOT" --plan-sha256 "$FORMATION_PLAN_SHA" \
  --launch-root "$FORMATION_LAUNCH_ROOT" --launch-sha256 "$FORMATION_LAUNCH_SHA"
env -u CUDA_VISIBLE_DEVICES "$PY" -B /tmp/astra_born_rulegame_formation_run_20260912.py collect \
  --root "$FORMATION_ROOT" --plan-sha256 "$FORMATION_PLAN_SHA" \
  --launch-root "$FORMATION_LAUNCH_ROOT" --launch-sha256 "$FORMATION_LAUNCH_SHA" \
  --launcher "$REVIEWED_FORMATION_LAUNCHER" --launcher-sha256 "$REVIEWED_FORMATION_LAUNCHER_SHA" \
  --out "$FORMATION_COLLECTION_ROOT"
```

Launch and collection roots must be separate fresh siblings of formation root.
Collection returns `validation`, `validation_sha256`, `archive`,
`archive_sha256`, `phase_complete`. No automatic fit/write/readout or retry.
Main uses the existing owned controller SIGTERM/supervisor cleanup boundary
when stopping; no generic PID-kill or new stop/restart framework is introduced.

## Launcher contract and bounds

`launch_contract(root, plan, pin, launcher, launcher_sha256)` returns the
static fields. Bind the actual separately reviewed new launcher hash, never
a guessed hash or the unrelated birth/readout launch hash.

Exclusive `launch.json` contains exactly:

```text
protocol, phase, root, plan_sha256, driver_sha256,
launcher, launcher_sha256, command, device, controller_seconds,
continuous_reservation, pid, pgid, session,
launcher_pid, launcher_pgid, launcher_session, started_wall, gpu_uuid
```

Protocol `born_auth_rulegame_formation_run_v1_20260912`, phase `formation`.
`command` equals `controller_command(root,pin,python)`; controller and launcher
are distinct fresh sessions, each PID=PGID=session>1. Set
`continuous_reservation=true`, actual UUID, and Unix wall start before the
controller but after accepted birth release. After wait/cleanup, exclusive
`exit.json` has exactly `launch_sha256`, integer `returncode`, `ended_wall`.
Optional log files: `gpu.xml`, `controller.log`, `launcher.log`. Both launcher
and controller must exit before collecting. No environment/credential dumps.

- Formation controller default/max900s, optionally narrower at prepare.
- One existing supervised worker<=600s, backend load<=180s, call<=120s,
  existing cleanup140s. The same process may hold child/teacher roles.
- Separate collection<=300s; launch-to-verified-release<=controller cap+300
  (default1200s). Worker/load/call/cleanup intervals are nested, not additive.
- Six-hour lease cutoff preserved; bounds are upper limits, not forecasts.
- Parent-death ownership is inherited from frozen birth `owned_worker`;
  actual child supervision is the unchanged diagnostic supervisor. Main owns
  the outer launcher, continuous reservation and stop decision.

## Capture/release interface for Einstein and Ampere

Public consumer function:

```python
verified_release(root, plan_sha256, release, release_sha256)
```

It verifies completed release/capsule/vacancy/evidence hashes, normalized birth
custody, current adapter/source pins, exact saved formation receipt and role
replay. It loads no model/tokenizer and issues no native query. It returns:

```text
root, plan, release, formation_receipt,
capture_path, binding, binding_sha256, normalized_birth
```

`capture_path` is `$ROOT/run/formation/data/capture.json`, EXACT committed role
module schema (`born_rulegame_formation_v1`, `interaction_v3`). It retains
`binding`, `binding_sha256`, monotonic `cutoff`, `calls`, `events`, `result`;
success remains `AWAITING_MAIN_AUDIT`, NOT scientific approval.

Paths and joins:

```text
plan.json + plan.sha256.json
normalized_birth.json
run/controller.json
run/formation/worker/{process.json,supervision.json,stdout.log}
run/formation/data/{isolation.json,backend.ready.json,backend.cleanup.json}
run/formation/data/calls/NNNN.{request,response}.json
run/formation/data/{capture_barrier.json,capture.json,manifest.json}
run/formation/receipt.json
run/result.json OR run/failure.json
```

`run/result.json` binds `receipt_sha256` and `supervision_sha256`;
`formation/receipt.json` binds capture/manifest/binding hashes and exact replay.
Separate `validation.json` requires `COLLECTED_RELEASED`, `phase_complete=true`,
`full_release=true`, the expected collector/plan hashes, and NO
`collection_failure.json`. Validation additionally seals terminal, evidence,
capsule inventory and final vacancy XML. A released failed attempt is preserved
but cannot feed `verified_release` or a write comparison.

This is NOT a legacy single-identity `check_capture`/exporter input. Consumers
must use the role-aware capture and source joins; don't rewrite it as teacher
and child sharing one identity. This runner does not export/select process
material or change wrong-prediction handling, source slots, teacher exclusion
or warm-start/write contracts. Those remain Einstein's disjoint scope and
Main's semantic/source review. `send_input` was unavailable here; the early
interface was supplied in chat for Main to relay, not falsely claimed sent.

## Capture, provenance and limitations

Unchanged interaction_v3 P/A formation: two prescribed lesson positions per
arm, max40wake+12record+4parent+4restate calls (60),18480 output-token ceiling.
Existing per-role seed/temperature/token/stop rules remain untouched. Invalid
outputs can end tasks early; these are caps, not a fabricated60-call minimum.
No retry/substitution or new seeds. Fixed OFF base parent; exact birth AUTH
LoRA on wake/restate/record via one native role backend/engine and explicit
per-request `lora_request=None` versus the immutable born-child LoRARequest.

`JournalBackend` durably writes each request and returned full envelope/raw
text/token/finish/stop/loader/route record. At the owner's second backend
verification, ALL actual raw pairs are sealed in `capture_barrier.json` BEFORE
the owner's existing postcapture replay. The role module's game/parser/events
and replay are unchanged. Partial exceptions preserve journal and, when
available, the owner's `FormationFailure.partial`; no result is promoted.
No separate evaluation panel, write, fit or downstream readout is run.

Status is blind to terminal bodies; it checks ownership and marker presence.
Collector waits for the whole owned launcher/controller/worker/session and
descendant scope, checks native GPU vacancy/proc reservations/queues using
the existing helper, and rechecks vacancy after safe archive creation.
Ordinary hygiene only: exclusive root/output/collection claim, no overwrites,
allowlisted files, credential/symlink/hardlink/special-file rejection, bounded
metadata sizes, changed-hash rejection. Failed collection and partial capsule
remain preserved without blind retry. No new C11 framework.

Capsule is metadata/full raw calls only; it does NOT include adapter bytes.
Finite AUTH weights and both birth completion receipts are checked upstream.
Local hashes are not base-origin authentication, clean ancestry, semantic
teacher-no-leakage certification, efficacy, persistent learning, or any
P1/G3/G5/H1/H2 result. Participation without component success can only be
Main's explicitly exploratory choice. Native one-engine routing/timing,
real snapshot normalization and actual process/GPU release still require
Main integration;24CPU tests do not claim those were run here.

**EDITSTOP. Main owns native snapshot, new launcher, launch and progression.**
