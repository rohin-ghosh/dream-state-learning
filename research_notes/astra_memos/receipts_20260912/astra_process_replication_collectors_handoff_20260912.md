# Process replication collectors — interface for Main

**EDITSTOP — September 12, 2026. 19 CPU tests PASS in69.269s.**
Implementation complete; Main alone performs native integration/query checks
and launches. No repo, runner, or inherited collector was edited. Frozen runner SHA256:
`96e27f5b8becaa59263f221206dc89a1b7d9a95eba8056810339556d8d9d11dd`.
No historical helper edits, phase chaining, scientific gate, model or tokenizer
loading. Recorded event replay is CPU-only custody, not a new model call.

CLI: `python3 -B /tmp/astra_process_replication_collectors_20260912.py
{write,readout} {status,finish} --fit-seed {0,1} --root ROOT
--plan-sha256 SHA --launch-root LOGS --launch-sha256 SHA
--launcher LAUNCHER --launcher-sha256 SHA [--out FRESH_SIBLING]`.
Readout additionally requires `--write-release VALIDATION_JSON
--write-release-sha256 SHA`. `finish` requires out; status forbids it.

Launcher receipt contract (launch.json): root, plan_sha256, driver_sha256,
launcher_sha256, fit_seed, pid (fresh session leader), started_utc, source,
device, command, gpu.gpu_uuid, continuous_reservation=true, controller_seconds
(write1200/readout1800), cleanup_reserve140, worker_cap_seconds600,
external_collection_margin_seconds300. Optional phase must equal the phase's
frozen version string. Write arms=P,A; readout cells=OFF,P_ON,A_ON. The command
must include explicit `--fit-seed SEED` before `--root`, as in the frozen runner
handoff. Logs contain launch.json, gpu.xml and optional controller.log only.
Readout launch must bind write_plan_sha256, write_release_path and
write_release_sha256; optional write_driver_sha256 must match the frozen runner.

Each successful collection publishes a fresh metadata.tgz plus validation.json;
weights are scanned for finiteness and hashed but are NOT put in the capsule.
Write validation status is COLLECTED_PAIRED_WRITE only for two verified fits;
readout is COLLECTED_PROCESS_READOUT only for all three verified cells.
Full release, aggregate availability, seed/phase, actual launch-to-final-vacancy
time and bounded collection time are explicit. No scientific-pass Boolean.

## Exact separate commands

Set these variables in Main's native environment. `NATIVE_PYTHON` must be the
plan's exact absolute interpreter spelling, without resolving its venv symlink.
`PYTHONPATH` and `ASTRA_SOURCE_ROOT` must point to the exact bound source tree.
Use the actual reviewed launcher hash and actual immutable launch.json hash;
there is deliberately no placeholder launcher hash compiled into the collector.

```bash
COLLECTOR=/tmp/astra_process_replication_collectors_20260912.py
SEED=0
WRITE_ROOT="$HOME/astra_diagnostics/astra_rulegame_process_write_rep_seed0_20260912_attempt1"
WRITE_PLAN_SHA=ff6bbf2834cc300e9e5cb6ec1f36975bc4d7dd1ae29c1bb4936ce887d7fdb43d
```

Main supplied that seed0 root/hash/device2 and reported native prepare SUCCESS;
this collector sidecar did not inspect that remote root. For seed1, explicitly
use its separately prepared root/plan/launch; no seed loop or phase chaining.

Blind write status (does not read terminal score/fit bodies or query the GPU):

```bash
env -u CUDA_VISIBLE_DEVICES PYTHONDONTWRITEBYTECODE=1 \
  "$NATIVE_PYTHON" -B "$COLLECTOR" write status --fit-seed "$SEED" \
  --root "$WRITE_ROOT" --plan-sha256 "$WRITE_PLAN_SHA" \
  --launch-root "$WRITE_LAUNCH_ROOT" --launch-sha256 "$WRITE_LAUNCH_SHA" \
  --launcher "$WRITE_LAUNCHER" --launcher-sha256 "$WRITE_LAUNCHER_SHA"
```

Bounded write finish (fresh sibling output, no overwrite/retry):

```bash
env -u CUDA_VISIBLE_DEVICES PYTHONDONTWRITEBYTECODE=1 \
  "$NATIVE_PYTHON" -B "$COLLECTOR" write finish --fit-seed "$SEED" \
  --root "$WRITE_ROOT" --plan-sha256 "$WRITE_PLAN_SHA" \
  --launch-root "$WRITE_LAUNCH_ROOT" --launch-sha256 "$WRITE_LAUNCH_SHA" \
  --launcher "$WRITE_LAUNCHER" --launcher-sha256 "$WRITE_LAUNCHER_SHA" \
  --out "$WRITE_COLLECTION_ROOT"
```

**Stop for Main review and independently operated readout preparation/launch.**
Only the successful write collection's validation receipt can bind the later
readout launch. Hash `$WRITE_COLLECTION_ROOT/validation.json` as
`WRITE_RELEASE_SHA`; the readout launcher must record exactly that path/hash.

Blind readout status:

```bash
env -u CUDA_VISIBLE_DEVICES PYTHONDONTWRITEBYTECODE=1 \
  "$NATIVE_PYTHON" -B "$COLLECTOR" readout status --fit-seed "$SEED" \
  --root "$READOUT_ROOT" --plan-sha256 "$READOUT_PLAN_SHA" \
  --launch-root "$READOUT_LAUNCH_ROOT" --launch-sha256 "$READOUT_LAUNCH_SHA" \
  --launcher "$READOUT_LAUNCHER" --launcher-sha256 "$READOUT_LAUNCHER_SHA" \
  --write-release "$WRITE_COLLECTION_ROOT/validation.json" \
  --write-release-sha256 "$WRITE_RELEASE_SHA"
```

Bounded readout finish:

```bash
env -u CUDA_VISIBLE_DEVICES PYTHONDONTWRITEBYTECODE=1 \
  "$NATIVE_PYTHON" -B "$COLLECTOR" readout finish --fit-seed "$SEED" \
  --root "$READOUT_ROOT" --plan-sha256 "$READOUT_PLAN_SHA" \
  --launch-root "$READOUT_LAUNCH_ROOT" --launch-sha256 "$READOUT_LAUNCH_SHA" \
  --launcher "$READOUT_LAUNCHER" --launcher-sha256 "$READOUT_LAUNCHER_SHA" \
  --write-release "$WRITE_COLLECTION_ROOT/validation.json" \
  --write-release-sha256 "$WRITE_RELEASE_SHA" --out "$READOUT_COLLECTION_ROOT"
```

## Launcher argv and additional details

Write controller argv, including exact flag order:

```text
[plan.python, "-B", "/tmp/astra_rulegame_process_replication_20260912.py",
 "write", "--fit-seed", str(seed), "--root", str(root),
 "--plan-sha256", plan_sha256, "--allow-gpu"]
```

Readout uses `evaluate` and its own root/plan hash; otherwise identical ordering.
`pid` must be the controller itself, started as a fresh session leader, not an
intermediate wrapper. Worker receipts are separately bound to actual frozen
`_write-worker` / `_readout-worker` argv (these obtain seed from pinned plans).
`fit_seed` is required as an integer0/1; a legacy `seed` field alone is insufficient.
`source` and `device` must exactly equal plan fields, including device string.
`started_utc` must be timezone-aware and no later than controller.started_wall.
If optional `phase` is supplied, its exact values are:
`rulegame_process_fit_seed_write_v1_20260912` and
`rulegame_process_fit_seed_readout_v1_20260912`.
The launcher receipt may include further nonsensitive metadata; the launch
directory may not contain unknown files or directories. Do not put collector
output inside the launch directory or run root.

## Public Python API

- `settings(values) -> config`: validates paths, explicit phase/seed and pins;
  paths become absolute `Path` objects. Values use underscores, not CLI hyphens.
- `status(config)`: launch/plan/worker ownership and terminal-marker readiness;
  no terminal result bodies, weights, metrics or vacancy query. Returned `launch`
  is internal context; CLI removes it.
- `finish(config)`: installs a300s real-time watchdog, exclusively creates out,
  performs full collection, and returns the validation summary (without file map).
- `cli_command(config, action)`: returns the exact Python/sidecar argv for either
  action. Tests feed this generated argv into real `main(argv)` parsing/dispatch.
- `audit_write`/`audit_readout` are internal post-release metadata checks, not
  launch or native APIs. `collect` is the internal untimed implementation;
  production callers MUST use `finish` or CLI, never `collect` directly.

The frozen runner is loaded by its exact SHA256. The collector instantiates
`WritePhase(plan.fit_seed)` / `ReadoutPhase(plan.fit_seed)` only after checking
that the pinned plan agrees with the explicit CLI FIT seed and phase protocol.
It does not add a module-level historical checked_plan shim or monkeypatch any
production module. Source/reference/material/model hashes and saved-fit receipts
are checked by the frozen seed-aware APIs, not recast as historical seed2 data.

## What is checked

- Whole recorded ownership: controller/worker PIDs, process groups, sessions,
  and transitive descendants from `/proc`; two terminal markers are rejected.
  This is recorded-scope evidence, not a sandbox against unknown escaped processes.
- Actual vacancy twice: pinned `check_free(plan.device)` checks GPU UUID/XML,
  absence of GPU processes, own-process CUDA reservations and pending/running
  queue jobs. Its existing narrowly reconciled system-service rules are unchanged.
  Collector cannot run with CUDA_VISIBLE_DEVICES set. No kills or cleanup claims
  substitute for observed vacancy. Main must retain actual launcher ownership.
- Write: seed-aware original-reference/source/Main-review/material custody,
  exact two-source own-wake fit/forward receipts,12epochs/12updates per arm,
  fresh-base seed0/1 config, masked/full-target exposure and saved adapter metadata.
  Both fits must validate before a completed write aggregate is available.
- Saved safetensors: bounded CPU streaming scan of all F32/F16/BF16 LoRA payloads
  for NaN/Inf and exact hashes, plus frozen driver shape/config checks. Readout
  rechecks both saved adapters. No torch/model load and no weight export.
- Readout: same-seed successful bounded write release, earlier final vacancy
  (nonoverlapping reservations), write archive and final release XML hashes;
  exact fresh OFF/P_ON/A_ON specs/ownership, source-bound identity and capture
  inventories, saved native-audit/cleanup receipts, all recorded calls, task
  replay, fixed24 denominators/invalid-zero handling, source process metrics,
  persistent-output diagnostics and exact controller receipts.
- The collector deliberately NEVER calls frozen `ReadoutPhase.audit_cell`,
  because it reloads a native tokenizer. Instead it uses the pure recorded-event
  `diagnostic.check_capture`, then `phase.process_metrics`; saved native-audit
  receipts remain custody evidence, **not an independent tokenizer/decode rerun**.
  `accepted_writes(..., native=False)` / `material_custody(..., native=False)`
  are explicit. No model generation, tokenizer replay, training or new criterion.
- Readout raw costs: paired request/response IDs,96call/27600token ceilings,
  role limits, token-ID metadata lengths, monotone per-call clocks and worker
  bounds. Existing record harm and all-F/conditional limitations remain separate;
  no C11 framework, tolerance, rescue gate or scientific-pass field is added.

## Publication, failure and costs

Success produces `started.json`, `audit.json`, `custody.json`, `release.xml`,
`release.json`, `metadata.tgz`, `final_release.xml`, `validation.json` in one
new exclusive sibling directory. The tar contains strictly enumerated metadata
and the initial release evidence; validation.json separately hashes the tar and
the final release XML. Readout tar also includes the pinned write validation.
Validation's `files` hashes every archive member; validate with the inherited
safe archive checker. The validation receipt itself must be hashed externally
for subsequent use. No promise that weights or excluded raw write material are
inside the capsule: `custody.json` records their native-only hashes/exclusions.

Simple hygiene rejects symlink/hardlink/special/unknown files, credential-like
payloads/fields, duplicate/nonfinite JSON, changed manifests/hashes, extra calls,
unsafe archive members, oversized files/trees and source changes during packing.
Source/run artifacts are never edited. Archive creation uses O_EXCL, validates
all members, then rechecks source inventories, phase plans, release and hashes.

Failed/partial phase with safe stable metadata can return
`COLLECTED_FAILURE_NO_AGGREGATE`, full_release=true, aggregate_available=false.
No aggregate is computed unless every required member and completed terminal
validate. Structural/custody/vacancy/timeout/budget errors raise, preserve
`failure.json` and any already-created partial files/archive, and publish no
validation.json. A partial archive alone is NEVER an accepted collection.
There is no retry loop, output overwrite, substitute phase/member, next-phase
launch, or automatic promotion. Do not blindly retry a failed collection under
a new directory; Main must inspect the preserved failure first.

Each `finish` is bounded by SIGALRM300s including checking/packing. Successful
publication additionally requires launch→final observed vacancy≤1500s for
write,≤2100s for readout, and final vacancy before the six-hour lease cutoff.
Readout adds ONLY the two separately released stage intervals and requires
≤3600s=60aggregate A40min/seed. Controller1200/1800, cleanup140, workers600,
training and generation times are nested and must not be added to those totals.
CPU gaps after verified write release and before readout launch are excluded;
unwitnessed idle gaps before collection are conservatively included. The bounded
checks may leave technical partial artifacts; no completion-time guarantee.

## Tests and hashes

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover \
  -s /tmp -p 'test_astra_process_replication_collectors_20260912.py' -v
```

19 tests PASS in69.269s. Fixtures use frozen runner APIs and generated worker
commands, with mock training/backends/ownership and vacancy; no native/GPU query
ran. Generated collector CLI argv is actually parsed and dispatched through
`main`, including both phases and FIT seeds0/1. Coverage includes successful
finite write/readout capsules; scope barriers; missing/mismatched/failed members;
nonfinite payloads; phase/seed/plan/launcher/write-release/XML mismatches;
unknown/credential/symlink files; metadata changes after packing; initial/final
release failure;1500s stage overrun;300s timer/restoration; no overwrites/retries,
no tokenizer/model/fit/native audit/phase chaining during collection.

Final source SHA256:
- `/tmp/astra_process_replication_collectors_20260912.py`:
  `fe80cfbbef70b2dc09b103d1de555eb7bdd359135be2bd9f59b9acc9d9bf39f8`
- `/tmp/test_astra_process_replication_collectors_20260912.py`:
  `f21f84a8569cd3562287f7deabefaa6bacbddd263f1a8e5f8898e3ab00881d6a`
- Frozen reusable helper `/tmp/astra_rulegame_process_write_collect_20260912.py`:
  `e23160132bf4eac82f220b8066c49de3cf8461e50929f9a82f3eac5e12906892`
- Pinned vacancy checker `gpu/astra_mini_sudoku_diagnostic.py` in plan.source_root:
  `a586b03bdb9c52f1061aa1e477ae983cc9d45ec0a2cd440642851fd8df8b609f`

The frozen runner and its original writer/readout dependencies must remain
available at their hash-bound paths as documented in its own handoff. The new
collector only imports the write collector's safe I/O/hash/archive/finite-scan
helpers; its old hard-coded plan/seed/launcher/GPU binding functions are unused.
Handoff hash is reported externally, not self-embedded.

Outstanding: Main native collector tests with the actual reviewed launcher,
real immutable source/reference roots, actual `/proc`/GPU/queue reconciliation,
and collection-cost feasibility. Main's27CPU/native runner PASS and218s native
seed0 preparation PASS are Main-reported, not new collector-native acceptance.
No new behavioral result, learned conditional prediction, clean lineage,
G3/P1/G5/H1/H2 or utility claim follows from this engineering custody.

**EDITSTOP. Main sole integrator/native/GPU/Git operator.**
