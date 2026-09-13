# Own-write CLI glue — EDITSTOP, September 13, 2026

Own only new command/tests and this handoff. No native calls, remote access,
model execution or edits to the three worker modules. Main owns allocation,
fresh subprocesses, outer hard timeout and release/collection.

## Final CLI/API

`prepare --spec PATH --spec-sha256 FILE_SHA --out FRESH_ROOT`

`formation|fit --manifest PATH --manifest-sha256 FILE_SHA`

`readout --manifest PATH --manifest-sha256 FILE_SHA --arm AUTH_WRITE|NO_WRITE_C0`

Python functions have these same positional arguments; tests inject tokenizer,
identity/environment readers and actor/trainer/base factories. Production CLI
has no mock flags. No controller, launches, retries or collection entry.

Spec closed keys: `schema='pcfl.own_write.command.v1/spec'`, `model_path`,
`model_binding={path,sha256}`, `base_state_receipt={path,sha256}`,
`shutdown_binding={path,sha256}`, `gpu_uuid`, `environment`, `expires_monotonic`,
`boot_id`. Environment is `{native: NativeActor.environment_identity(),
peft_version: actual installed PEFT version}`. All seeds fixed 0, all stage
caps1800s, prepare180s. Source hashes are measured from imported source, sealed
at prepare and checked again in each stage, not hardcoded while workers edit.

Main CPU base receipt seam (confirmed against the locally available attempt2
producer script; no native receipt or outcomes fetched by this worker):

```text
schema = pcfl.own_write.cpu_base_state.v1
status = COMPLETE
base_state_sha256 = actual pcfl_vertical_train._state_hash(base.state_dict())
model_binding_sha256 = SHA256 of original official model receipt file
model_files = exact 14 filename -> SHA256 mapping
dtype = bfloat16
device = cpu
environment = spec.environment
```

It must be actual clean-C0 CPU tensor evidence, not a placeholder or adapter
hash. This command never loads base weights in prepare. The native fit factory
loads the pinned local base in bf16 and the existing writer independently checks
its tensor hash and absence of an adapter.

Prepare fixes disposable/0 salt0 O=R=D=0, actions a0,b,c,d,f0,u,a1,f1;
links (0,1),(1,2),(3,4),(3,7). It seals the Meitner schedule before generation
and the same 17 queries × W0..W8 roster for each readout arm (153 each).
Structural-only token measurements never become writer material; after native
formation the writer consumes actual replayed raw child rows only.

Stage deadline = min(sealed expiry, stage entry monotonic +1800), so verification,
cold load and close are included without expiring later stages1800s after prepare.
Resolved actor configs are archived before first call; output/input caps and all
choices remain fixed. Main must enforce the hard cap externally. Both readouts
must run in separate fresh processes. Formation lazily starts NativeActor,
explicitly verifies/calls EngineCore.shutdown, then calls actor.close even on
errors. ReadoutActor already owns that explicit shutdown seam.

The cold-start timing note is resolved in the inspected final scoped writer:
it now checks `generation_started >= load.ready_at`. This author made no
changes to that writer or the shared numerical loop.

## Ready for Main preparation

Owned final byte pins:

| File | SHA-256 |
|---|---|
| `gpu/astra_pcfl_own_write_command.py` | `cc5a9ec055537b6cd847804ec2212f2666a46023803d542da2fe3a4d2c8f80dc` |
| `tests/test_astra_pcfl_own_write_command.py` | `dcc2557bbae396f275de99c4ae65eee982c6e193b7affb4d7819f9c488f6df51` |

Final focused command, executed locally with injected CPU fixtures only:

```sh
PYTHONDONTWRITEBYTECODE=1 timeout 180 python3 -m unittest discover -s tests -p test_astra_pcfl_own_write_command.py -q
```

**20 tests PASS, 16.558s; no skips.** AST and trailing-whitespace checks pass.
Tests use real worker formation/admission/replay and readout actor code with
injected synthetic sessions/tokenizers. The command fit-dispatch test mocks
writer binding/numerical execution and creates explicitly synthetic adapter
files; it is NOT native fitting or numerical parity evidence. Main separately
reports 14/14 real tiny CPU numerical tests PASS with no skips, 16.970s, on
source5fb67f58. That Main result is not re-executed or independently claimed here.

Supply this exact native receipt pin in `spec.base_state_receipt`:

```json
{
  "path": "/localhome/local-rohing/astra_diagnostics/pcfl_cpu_base_state_20260913_attempt2/base_state.json",
  "sha256": "a46209082c36635c0bd03a384462454211d773ed7257265395e89d878d6063bd"
}
```

Its Main-reported tensor hash is
`a2367093892219a833eea1bc7b3e0e2069bcaecad335df357809679d272f4992`.
The tensor hash is **not** the receipt file hash. Prepare checks the receipt's
model/environment/dtype/device join; the real writer checks loaded base tensors.
Attempt1 remains untouched. Shutdown binding remains the installed native path
specified by Main, with SHA
`7f5e1ac1a999faf36eab7d0c184bea7c93ae5e92234c39a148a809fd6e89840c`.

## Invocation and output layout

Set `PYTHONPATH` to the frozen source root and all four offline flags to `1`:
`HF_HUB_OFFLINE`, `TRANSFORMERS_OFFLINE`, `HF_HUB_DISABLE_TELEMETRY`,
`VLLM_NO_USAGE_STATS`. Prepare requires `CUDA_VISIBLE_DEVICES=''`; each actual
execution command requires CVD equal to the manifest's single UUID. Main alone
chooses allocations and invokes native commands. Illustrative command forms:

```sh
"$PY" -B "$SOURCE/gpu/astra_pcfl_own_write_command.py" prepare --spec "$SPEC" --spec-sha256 "$SPEC_FILE_SHA" --out "$FRESH_ROOT"
"$PY" -B "$SOURCE/gpu/astra_pcfl_own_write_command.py" formation --manifest "$MANIFEST" --manifest-sha256 "$MANIFEST_FILE_SHA"
"$PY" -B "$SOURCE/gpu/astra_pcfl_own_write_command.py" fit --manifest "$MANIFEST" --manifest-sha256 "$MANIFEST_FILE_SHA"
"$PY" -B "$SOURCE/gpu/astra_pcfl_own_write_command.py" readout --manifest "$MANIFEST" --manifest-sha256 "$MANIFEST_FILE_SHA" --arm AUTH_WRITE
"$PY" -B "$SOURCE/gpu/astra_pcfl_own_write_command.py" readout --manifest "$MANIFEST" --manifest-sha256 "$MANIFEST_FILE_SHA" --arm NO_WRITE_C0
```

Each is a separate process; do not run both native readout arms in one process.
Native prepare does not instantiate model weights or call an actor generation.
It loads only the actual tokenizer and reuses NativeActor's local source/model
file identity verifier. All successful-branch structural strings in token
measurements are explicitly measurement-only and never passed as fit targets.

CLI prints `manifest_sha256` (actual file SHA) after prepare, and
`completion_sha256` (actual file SHA) after a stage. `seal_sha256` is the internal
JSON seal and is separately named. All `--*-sha256` flags take **file hashes**.
Python APIs return their full manifest/completion objects instead of CLI summaries.

Prepare creates `spec.json` (original exact bytes), `measurements.json`,
`manifest.json`, or `prepare_failure.json`. Later commands exclusively create:

- `formation/`: entry, resolved formation config, `records/` and `actor/`,
  explicit `shutdown.json`, `actor_close.json`, exact-child deterministic
  service17 items/calls0, and stage completion or preserved failure.
- `fit/`: entry, existing writer output under `write/`, saved final
  `write/adapter`, byte/size-pinned `adapter.json`, completion or failure.
- `readout_AUTH_WRITE/` and `readout_NO_WRITE_C0/`: entry, config, actor raw
  sidecars, each returned raw response, close and scores, completion or failure.

Successful upstream directories become immutable: later stages rehash their
complete file inventory. **Keep external controller stdout/stderr/release
receipts outside these directories.** Main's controller must not pre-create a
stage directory; command owns its fresh claim. An existing stage directory
blocks a retry, including after failure. No cleanup deletes failures.

READ scores keep the original scorer dictionary and add strict_stop and
semantic_stop; malformed/length answers are preserved, not regenerated. The
full frozen153 roster remains in the config on exceptions; incomplete stages
have no successful completion or partial-score pass. Both arms have identical
LoRA-enabled engine settings and roster but NO_WRITE_C0 mounts no adapter.
Its zero fits are not a matched-update LR0 control. Total planned work is
20 formation +306 readout calls, one fit/200 updates; deterministic service
calls are zero. No additional inference, teacher capture or collection occurs.

Completion means worker work/close completed inside the bound1800s stage
interval, not GPU release. Receipt explicitly says `outer_release_required=True`
and `gpu_released=False`. Main enforces hard timeout, process identity and owned
release externally, including fit process termination; command has no generic
controller, process killer, reservation manager or recollector.

Coverage includes fixed salt0/chronology/roster/schedule, CPU-only preparation,
512-token rejection without redraw, original raw child payload forwarding,
separate final-adapter/no-adapter routes, explicit shutdown and shutdown error,
failed formation/readout preservation, all planned denominators, stop/content
separation, source/environment/expiry/base/shutdown pin failures, boolean
update-count rejection, no retry, close-inclusive caps, and CLI file/seal hash
distinction. Only the two new owned source/test files and this handoff changed.
No remote/native/GPU/model calls, C0 outcomes, leases, commits or other-owner
edits. All command edits stop here; Main takes review/integration ownership.
