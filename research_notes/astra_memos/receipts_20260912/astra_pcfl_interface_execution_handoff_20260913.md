# EDITSTOP — interface DEV command and detached outer

**2026-09-13 15:04 UTC. Execution seam complete; ownership released to Main.** Only the four new files listed below were edited, plus this handoff. No driver, native actor, lifecycle helper, own-write file, manuscript, allocation, or other worker file was changed. No native/model/GPU/remote actions or commits. CPU tests include real harmless local child sessions and injected resource observations.

## Frozen owned files

| File | SHA256 |
|---|---|
| `gpu/astra_pcfl_interface_command.py` | `2aefc08d7404622573d601f7aca5e6e6767c8a70a26c095092b472da18b475ab` |
| `gpu/astra_pcfl_interface_outer.py` | `232f61c345363a1996271647e9bd12a5482dc729e6131c4c883bf6136ffd0c63` |
| `tests/test_astra_pcfl_interface_command.py` | `6f45d3a6a619161c831ffe091fcba8d7af58cf4bf57ca54f0c1c3929559df9a1` |
| `tests/test_astra_pcfl_interface_outer.py` | `442546d4c192a5ff288e7cea8ec0d035e15ed2a41de3f90cfed86d4fd886ea90` |

Implementation sizes: command259 lines; outer206 lines. No new general guard framework. The outer directly reuses `validate_allocation`, `check_node`, `check_queue`, `check_cvd`, `check_gpu`, `identity`, `cleanup_owned`, `file_hash` and small custody helpers from `astra_pcfl_zero_fit_outer`; it never invokes its C0 scientific controller or separate finalizer. It does not import or modify own-write command/outer behavior.

Read-only dependency hashes at final verification:

```text
77d088d9d72bfd7fc6cf5bae478f03c2333821d4fbd2a16697ccc2db256b2917  gpu/astra_pcfl_interface_dev.py
915b27d4dfe51623535bae588e54e1e35654a956f164aa23eba74a925a4a23ff  gpu/astra_pcfl_native_actor.py
ed1b8c5f1d866e8e036a33c3fbeb278551021413cb63e5b3a35bb72934dae04e  organism_v6/pcfl_vertical_dev.py
fdd29c64bc73b1602998e6509da9f6d3132b90f9a5d50dceb1ad20ce86128f19  gpu/astra_pcfl_zero_fit_outer.py
```

The driver is Main's **current** version with information-free `CONTINUE: follow the declared turn budgets and commit the final action when ready.` No old driver hash is baked into the implementation/tests. Preparation requires the exact current source map; subsequent drift rejects execution.

## Tests and checks

**PASS: 76 CPU tests**, final run 85.419 seconds:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=tests:. python3 -m unittest -q \
  test_astra_pcfl_interface_command test_astra_pcfl_interface_outer \
  test_astra_pcfl_interface_dev test_astra_pcfl_native_actor
```

Breakdown: **14 new command + 8 new outer + 20 existing driver + 34 existing native-actor tests**. Prepare and outer `--help` smoke checks passed. Pytest is unavailable in this interpreter; no package installation was performed. Early test-only assertion/venv-fixture errors were fixed before the final passing run.

Coverage includes default NativeActor selection and no-LoRA engine; all four exact stage call ceilings; A1 handshake success despite zero route successes; completed failed ceilings returning0; backend/shutdown failure without completion; unchanged raw failure evidence; native-kind admission versus injected captures; load/close/count joins; all64 initial prompt measurements including an oversized64th prompt; original root/source/roster pin drift; offline tokenizer flags; finite deadlines; fresh-only output; real worker identity and fixed argv binding; nonzero/signal/timeout; unknown PID never invoking cleanup/signaling; post-worker release failures; queue/CVD/lease checks. Existing tests preserve later token/turn budget stops, original raw strings,64 denominators, slot accounting and replay behavior.

## Preparation contract — Main supplies actual values

`command.prepare(spec_path, spec_file_sha256, output, stage)` writes one prospective stage manifest into a **fresh absolute output directory**, disjoint from sources/model/input files. The independently file-pinned spec has exactly these fields:

| Field | Required value/type |
|---|---|
| `schema` | `pcfl.interface.command.v1/spec` |
| `model_path` | Main's absolute existing offline base-model directory |
| `model_binding` | `{"path": absolute_original_public_binding_receipt, "sha256": actual_file_hash}` |
| `roots_file` | `{"path": absolute_original_roots_json, "sha256": independently_recorded_file_hash}` |
| `shutdown_binding` | `{"path": absolute_installed_EngineCore_shutdown_source_file, "sha256": actual_file_hash}` |
| `gpu_uuid` | Main's fixed allocation UUID |
| `environment` | Exact `native.environment_identity()` object: `python`, `version`, `packages`; **not** the own-write `{native, peft_version}` envelope |
| `expires_monotonic` | Positive future numeric absolute monotonic cutoff on the same boot |
| `boot_id` | Main's current boot identity |
| `source_files` | Exact `command.source_files()` dictionary evaluated from the intended executed source snapshot |

The source map covers the actual command and outer, driver/default actor/core, lifecycle helper and its imported driver/runtime source. It is location-specific: stage the intended source tree first, compute its source map there, then hash the completed spec file independently. No source-path or actual input-path guessing is performed by the seam.

**Original roots supplied by Main, not read remotely by this worker:**

```text
/tmp/astra_pcfl_c0_inventory_20260913_attempt1/roots.json
SHA256 bcca78ae2abadb2a5f9680dc70ed55327185614198a4b873a5f3e487b2ed443e
Original C0 manifest file SHA256 ef2adf4146b525fc9a13e9759137daffefe526373a9f6deda3c37fbd07d6eaa6
```

Main independently confirmed equality with original C0 `plan.roots`. The command consumes the original roots file as a JSON **list of four root wires**, in exact excluded/0–3 order, not a new wrapper object or allocator output. The original C0 manifest hash is provenance supplied by Main, not an additional field accepted in this closed spec. Original root-file bytes are pinned, copied verbatim, and rechecked at preparation, stage entry, runtime identity verification and terminal validation. No reselection.

Preparation is CPU/offline only, requires explicitly empty CVD and all offline flags, has a180-second bound, and verifies the public model/tokenizer/environment identity without starting an actor. It measures **all64 initial system/user message pairs with the actual offline tokenizer**, rejecting input/context incompatibility before stage creation. It preserves `spec.input.json`, `roots.input.json`, `roster.json`, `identity.json`, `measurements.json`, then writes sealed `manifest.json`. Injected preparation is explicitly labeled and cannot launch native work.

## Exact CLI

Main chooses the real venv/source/input/output variables; these are templates, **not commands executed by this worker**:

```sh
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HUB_DISABLE_TELEMETRY=1 VLLM_NO_USAGE_STATS=1
export PYTHONDONTWRITEBYTECODE=1
CUDA_VISIBLE_DEVICES="" PYTHONPATH="$SOURCE_ROOT" "$PYTHON" -B -m gpu.astra_pcfl_interface_command prepare \
  --spec "$SPEC" --spec-sha256 "$SPEC_FILE_SHA256" \
  --output "$FRESH_STAGE_ROOT" --stage "$STAGE"
```

Allowed stage names only: `A1_READ_DISCLOSED`, `A2_DIRECT`, `A3_THINK`, `ACTIVE_THINK`. One manifest binds one stage; there is no stage loop, resume or retry. Main then independently hashes `manifest.json` and supplies a separately pinned allocation.

Launch the following **inside Main's detached launcher**, not a foreground SSH finalizer:

```sh
CUDA_VISIBLE_DEVICES="" PYTHONPATH="$SOURCE_ROOT" "$PYTHON" -B -m gpu.astra_pcfl_interface_outer \
  --manifest "$FRESH_STAGE_ROOT/manifest.json" --manifest-sha256 "$MANIFEST_FILE_SHA256" \
  --allocation "$ALLOCATION" --allocation-sha256 "$ALLOCATION_FILE_SHA256" \
  --outer-sha256 232f61c345363a1996271647e9bd12a5482dc729e6131c4c883bf6136ffd0c63 \
  --outer "$FRESH_OUTER_DIR" --stage "$STAGE"
```

Allocation shape deliberately reuses the existing lifecycle schema **`pcfl.zero_fit_outer.v2/allocation`**, not a new allocation framework. Its `outer_sha256` must equal the new interface outer hash. Python must be an actual venv interpreter matching the manifest's native environment. UUID, boot, UID, pinned queue contents/coordination and exact existing service exceptions follow the unchanged helpers. No generic unreadable-process/SSH exception was added.

The outer constructs the only worker argv, without caller-supplied command text:

```text
<allocation.python> -B -m gpu.astra_pcfl_interface_command stage
  --manifest <pinned manifest path> --manifest-sha256 <independent file hash>
  --deadline <outer absolute monotonic deadline minus120 seconds>
```

Main should use the outer for native work, not invoke the stage directly. The stage subcommand is exposed for this one fixed child and validates its finite deadline itself. The outer waits4 seconds before checks, including that wait inside **3600 seconds total**, reserves **120 seconds** for cleanup/release/collection, and respects the greater of six hours or allocation lease margin. It injects only the allocated UUID into worker CVD, pinned source-root PYTHONPATH, offline flags and spawn multiprocessing settings. Worker uses `start_new_session=True`, DEVNULL stdin and fresh stdout/stderr files. The controller itself does not daemonize; Main owns detached startup.

## Scientific outcomes versus lifecycle outcomes

- Native stage runs a **fresh default NativeActor**, no LF actor, LoRA, fit, source rewriting, parser relaxation or prompt repair. It never starts/counts tokens on that actor before `driver.run_stage`; the latter owns lazy generation startup.
- The driver remains the sole stage-threshold/scoring authority. Possible calls are **832 /64 /448 /1216**, not mandatory observed calls. The command records actual attempt count, separate possible-call cap, verified prompt/output tokens and unchanged task-reason counts. A1's64-task handshake gate is not a route-success ceiling. A2/A3/ACTIVE thresholds are not reimplemented in the wrapper.
- `COMPLETE` means all tasks were scored and infrastructure/custody checks passed, **not** that the supplied-memory ceiling passed. Malformed/wrong answers and later budget stops retain their distinct original reasons. Valid completed native science failures exit0 and can collect as `COMPLETED` with `stage_gate_passed=false`. No padding calls, forced64 wrong-answer label or salvaged final call.
- Native completion requires **NATIVE kind for every actual identity/raw capture**, exact original sidecar joins and same PID/config. Injected CPU evidence remains labeled and cannot be admitted through the native outer. Load-ready precedes generation-start; load identity/config and original close sidecars bind to the same actor. Close consumed calls must equal actual attempts; token-count calls must be zero. Every captured request/render/raw/response file is compared back to original actor bytes.
- Installed `actor._session.llm.llm_engine.engine_core.shutdown()` is explicitly inspected and matched to Main's pinned actual source file before invocation, followed by actor close in a nested finally path. Shutdown/close/infrastructure failures preserve the report/partial sidecars and `failure.json`, and do not write completion. Unverifiable failed-stage token usage is labeled unavailable/partial, never asserted zero.
- The command replays the exact report, writes `replay.json`, `custody.json`, and a sealed `completed.json` binding all stage file hashes. It explicitly requires outer release and does not assert GPU vacancy.
- The **same detached outer** always invokes existing `cleanup_owned` only for its spawned, verified PID/PGID/SID/UID/boot/start-tick identity; unknown identity is recorded as failure and never killed. It records exit/signal/events and once-only current post-worker queue/GPU/CVD observations, checks report/actor/worker/completion joins and writes a sealed fresh `collection.json`. There is no foreground finalizer or retry. Successful science completion cannot override failed release observation.

## Main next step and limits

Main owns current native preparation, allocation/launch, release-sensitive observation windows, collection and notebook logging. Generate the spec/source map for the actual transferred source tree and independently pin files there; prepare one stage, inspect the64 actual-token measurements and identity receipt, then launch only via the detached outer with a fresh stage/outer directory. No native preparation or stage has been executed by this worker.

This is supplied-memory interface DEV on preserved excluded roots: **no full assay, H1/H2, learning, C11 or causal qualification**. CPU fixtures test lifecycle behavior, not actual model success. The original C0 and own-write failures/artifacts remain untouched.
