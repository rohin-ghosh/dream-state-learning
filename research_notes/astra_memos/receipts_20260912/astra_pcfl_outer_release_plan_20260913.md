# PCFL C0 800-task outer/release plan — 2026-09-13

Read-only source inspection; this memo is a proposal for Main, not executable
outer code or launch authorization. No driver, actor, tests, archive, source
snapshot, model, native process or remote inventory was modified or run.

## 1. Smallest integration and current API

Use one fresh C0 diagnostic worker, not 800 cold model loads, behind the existing
reservation-holder / CPU-controller / isolated-worker lifecycle. Add only a
Main-owned entry shim, custody receipts and once-only finalization/archive glue.
Do not invoke the old full-assay Runtime constructor, any memory runner's
worker/controller/collector, or a fit path. The zero-fit driver deliberately
reuses only task expansion and task/scoring behavior from the old runtime.

Current `gpu/astra_pcfl_zero_fit_dev.py` exposes these **Python APIs**, not a CLI:

```python
plan = build_tasks(root_wires)
measurements = measure_tokenizer(plan, tokenizer, tokenizer_binding(actor_config),
                                synthetic=False)
manifest = build_manifest(plan, measurements, actor_config,
                          wall_seconds=wall_cap, device_seconds=device_cap,
                          output_dir=output_dir, test_only=False)
validation = validate_manifest(manifest, tokenizer)
report = Diagnostic(manifest, tokenizer).run()
final = finalize_release(report, receipt)
```

`run` is a method, not the top-level function suggested in the still-early
`/tmp/astra_pcfl_zero_fit_handoff_20260913.md`. There is no `prepare`, `controller`,
`collect`, `main` or argparse entry point in the inspected driver. Consequently,
`python .../astra_pcfl_zero_fit_dev.py --...` is **not** a launch command.
The Main shim must call the APIs above and write their returned artifacts;
`finalize_release` itself does not write a file or enforce once-only invocation.

`root_wires` must contain excluded/0…excluded/3 in that exact order, with the
actual qualified opaque inventory. The plan contains 800 fixed tasks: 640
delayed and 160 reachout; 704 single-call tasks plus 96 ACTIVE_LINKED_TEXT
service tasks, hence **1952 maximum conditional actor calls**, not 800 fixed
generation calls. Keep 12 READs, cumulative 2048 actor-output and 4096 returned
tokens per task. Unused conditional call slots are not missing mandatory calls.
Zero fits, updates and adapters; material is explicitly researcher-authored
excluded-root ceiling material, not child formation or authentic replay.

The actor is `gpu/astra_pcfl_native_actor.NativeActor(config)`; constructing it
validates schema only and loads nothing. `start`, or an initial `generate` or
`count_tokens`, loads the native session. **Do not use actor.count_tokens for
CPU-only preparation.** Use an offline tokenizer independently. The worker's
`Diagnostic.run` already calls actor.start and closes in finally.

Actor config has exactly these fields:
`schema, model_path, model_binding, source_files, tokenizer_files,
chat_template_sha256, tokenizer_probe, environment, gpu_uuid, engine,
output_dir, deadline, device_seconds_cap, max_input_tokens, max_output_tokens,
max_calls`. Preserve `native.ENGINE` and the existing sampling constants;
`max_calls=1952`, `max_output_tokens=2048`, device cap equals the manifest's,
actor output is precisely `<diagnostic-output>/actor`. CVD must be the exact
GPU UUID, not a historical numeric visibility value. Native model binding is
the existing matched 14-file public-revision receipt for Qwen2.5-7B-Instruct,
revision `a09a35458c702b33eeacc393d103063234e8bc28`, with C0/LoRA=None.

## 2. Freeze/transfer and Main's command sequence

All host alias, interpreter, GPU index/UUID, boot, UID, lease, model receipt,
source/output paths and caps come from Main's freshly checked allocation and
input records. No node address, user-home path, historical UUID or SSH credential
from the old wrappers is reusable as an unverified literal.

1. **Freeze locally, then transfer source bytes once.** Wait for driver/actor
   owners' final pins and tests. Package the exact source tree, scope/world/
   inventory notes, Main shim, selected lifecycle helpers and tests with a
   relative-path file-size/SHA256 manifest. Include transitive
   `organism_v6/pcfl_vertical_prepare.py`, imported by the runtime: the driver's
   seven-file `source_snapshot()` does not itself include it. Add its byte pin
   and the shim/helper pins to `actor.source_files` (a permitted superset), and
   to the outer archive manifest. No live-tree import fallback or source edit.
2. Main transfers the immutable tar and its expected SHA using its configured
   transport to the allocation-selected host. Verify tar bytes before unpacking
   into a **fresh** source directory; reject absolute/escaping members and
   symlink/hardlink escapes, then verify the exact file manifest. Do not deploy
   by pasting source in SSH heredocs, overlaying an existing source directory,
   or copying an obsolete CPU-smoke archive that lacks the final driver.
3. **CPU prepare on that host**, CVD empty and offline. Load the tokenizer from
   the bound local model, measure all applicable actual tokens, build tasks and
   manifest, then `validate_manifest(manifest, tokenizer)`. Save them with
   exclusive creation. The native absolute source paths belong here:
   `source_snapshot()` keys are resolved absolute paths. Do not reuse a laptop
   manifest then rewrite paths after sealing. Record exact prepared file hashes
   as well as the internal canonical seals. No model engine starts here.
4. **Fresh launch check and claim, then one holder.** Check the current boot/UID,
   roster index→UUID, reservation/queue state, complete GPU process vacancy,
   lease end and remaining budget; exclusively create a sibling launcher claim.
   The holder advertises `CUDA_VISIBLE_DEVICES=<UUID>` and never loads a model.
   It launches the CPU controller with empty CVD. Preserve the holder identity
   and launch receipt before acknowledging launch to Main.
5. **One isolated diagnostic worker.** Controller rechecks allocation/source/
   manifest pins and vacancy, then spawns the worker via the frozen interpreter
   and shim, `start_new_session=True`, CVD UUID. The worker loads only the
   offline tokenizer before constructing Diagnostic, then calls `.run()` once.
   Convert report status to process return code explicitly: run() can return a
   FAILED report without raising. Complete negative panels are valid completed
   measurements, not execution errors and not grounds for another generation.
6. **Release before finalize.** Wait with the cleanup reserve subtracted from
   the hard deadline, clean/reap only recorded owned worker processes/groups,
   establish GPU vacancy, persist raw release evidence, and exit the controller.
   The holder preserves controller rc and exits; Main reconciles its exit and
   reservation removal. No absent holder-exit receipt means automatic release.
7. **CPU-only once finalization/collection.** In an empty-CVD process on the
   original host, exclusively claim a fresh collected directory, validate the
   completed inventory/receipts below, create the release attestation, call
   `finalize_release`, and write `final.json`, collection receipt and byte
   inventory. No call to Diagnostic, actor.start/count_tokens/generate, or the
   previous experiment's collector. A proposed separate 180s collector cap
   follows existing lifecycle practice; Main must explicitly bind it, because
   the driver imposes no collector deadline itself.
8. **Archive once, verify mirror.** After every writer is closed, create a new
   evidence tar containing frozen source/input material, driver and actor
   artifacts, all launcher/controller/worker/release/collection receipts,
   stdout/stderr and every failure/anomaly. List relative member sizes/hashes,
   hash the tar, transfer its exact bytes back using Main's configured
   transport, and verify tar and all extracted member hashes. Preserve native
   absolute path strings inside evidence. On the local mirror do not rewrite
   paths/reseal manifests or call finalize_release against invented native
   paths; its evidence-path dereference is why finalization happens natively.

Proposed **Main shim command contract**, not commands currently implemented by
the driver (no such shim was authored in this task):

```sh
env CUDA_VISIBLE_DEVICES='' PYTHONPATH="$SOURCE" "$PY" -B "$MAIN_SHIM" prepare --inputs "$INPUTS" --inputs-sha256 "$INPUTS_SHA"
env CUDA_VISIBLE_DEVICES='' PYTHONPATH="$SOURCE" "$PY" -B "$MAIN_SHIM" launch --manifest "$MANIFEST" --manifest-sha256 "$MANIFEST_SHA" --allocation "$ALLOCATION"
# launch detaches one UUID-visible holder; it owns one empty-CVD controller,
# which owns one UUID-visible isolated worker. Never relaunch on lost stdout.
env CUDA_VISIBLE_DEVICES='' PYTHONPATH="$SOURCE" "$PY" -B "$MAIN_SHIM" collect --manifest "$MANIFEST" --manifest-sha256 "$MANIFEST_SHA" --report-sha256 "$REPORT_SHA" --out "$COLLECTED"
```

Supply all variables from sealed Main records; also set
`HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`, `HF_HUB_DISABLE_TELEMETRY=1`,
`VLLM_NO_USAGE_STATS=1`, `PYTHONDONTWRITEBYTECODE=1` in each native process.
Historical `memory.offline()` additionally sets the existing spawn/dataset/
do-not-track environment. The transfer/archive commands remain Main's existing
configured transport, not a newly invented host/credential command here.

## 3. Exact finalization receipt and what it does NOT prove

`finalize_release(report, receipt)` requires the following **seven keys only**:

```json
{
  "report_sha256": "report's internal sha256 seal, not report.json file SHA",
  "gpu_uuid": "exact report.gpu_uuid",
  "owned_group_released": true,
  "gpu_vacant": true,
  "elapsed_seconds_from_start": 0.0,
  "evidence_path": "absolute native path to release attestation JSON",
  "evidence_sha256": "SHA256 of that file's exact bytes"
}
```

The `0.0` above is a type illustration, **not** a valid measured value or
default. Fill it with the measured interval defined below. The attestation
file must decode to **exactly the first five keys and their identical values**;
it cannot contain extra PID, timestamp, raw GPU data, schema or inventory
fields. The finalizer hashes that file and canonical-compares its JSON against
the five fields. Write richer process evidence separately and bind both files
in the outer collection inventory, rather than smuggling extra keys here.

The report must retain schema `PCFL_C0_ZERO_FIT_DIAGNOSTIC_V1/report`, 800 tasks,
fits/updates zero and full_v22_release false. The final object has
`schema=.../final`, `report`, `outer_release`, `diagnostic_usable`,
`cpu_test_complete`, and `full_v22_release=False`, plus its seal. Usable means
native `COMPLETE_AWAITING_OUTER_RELEASE` plus accepted attestation; **it does
not mean thresholds passed**. Report panels and `thresholds_passed` remain
separate and unchanged.

This is an attestation API, not a GPU/process verifier or once-collector. It
does not independently inspect `/proc`, nvidia-smi, child return codes, a boot,
the actor archive, or the truth of the supplied booleans. Main must establish
those facts before calling it. Actor `close.json` deliberately leaves
`owned_group_released` and `gpu_vacant` null; do not overwrite it. An unavailable
native shutdown method is not evidence of vacancy, even if close returned
without an exception; process exit and the outer checks remain necessary.

## 4. Release, failure and time accounting

Persist boot ID, UID, exact argv and environment binding, PID, PGID, parent,
start ticks, launch monotonic/Unix times, manifest/source pins and the exact
integer rc for holder/controller/worker. Check `type(rc) is int` before rc==0;
bool True/False are not process receipts. Keep the diagnostic's report status,
error and backend_close independently. There is no justification for discarding
partial raw bytes or turning launcher transport errors into native success.

Before launch, the existing `reservations(config,index,uuid)` scans current
same-user CVD reservations and unresolved processes, checks boot/UID/roster,
and checks the shared queue. It has historical machine-specific queue and
exception bindings: reuse only on a freshly confirmed compatible allocation,
not by importing an old wrapper's global GPU/host values. The holder itself
is an intentional reservation; do not expect that vacancy-only reservation
scan to pass unmodified while the holder is alive.

GPU release requires a successful bounded all-process query of the assigned
index, exact UUID match and a present, genuinely empty processes element.
Existing `probe.gpu_state(plan)` uses nvidia-smi XML and rejects query failure
and UUID drift, but does not persist its raw output. Preserve the exact
command/stdout/stderr/rc/time independently. Empty memory usage or absence of
the actor PID alone is insufficient; check the owned process group as well.
Do not kill an unrelated process merely because it occupies the allocated GPU.

Timeout handling: spawn the worker in a new session; bind PGID=worker PID and
start ticks immediately. On timeout/error, recheck identity before signaling
that owned group only, TERM then bounded wait, KILL then bounded reap; retain
the timeout and cleanup receipts. If identity is missing/reused, fail cleanup
closed rather than widening the kill. Never use pkill/python-name/user-wide
or GPU-occupant-wide killing. The holder must have a finite supervisory deadline
and a durable ledger of controller and worker identities: worker sessions are
separate, so killing the controller's group alone may leave vLLM alive. Existing
worker owner-watchdog patterns are reusable by Main; do not rely solely on
post-return actor clocks to interrupt a stuck LLM constructor/generate call.

Timing must preserve these nonadditive scopes:

- `Diagnostic.started_monotonic` is sampled at constructor entry **before**
  manifest/tokenizer replay validation; actor cold load and shutdown follow.
  `wall_seconds_through_close` includes that validation, loading, generation,
  between-call work and close. Offline tokenizer creation before constructor
  is outside this report interval; include it in separate outer elapsed time.
- Actor `load.json` records operation_started, model_load_started and ready_at;
  call raw/response artifacts record generation timing; close has accumulated
  `elapsed_actor_seconds`. These are wall intervals, not active GPU utilization.
  Do not add them again to driver/controller elapsed time.
- Record `elapsed_seconds_from_start = release_verified_monotonic -
  report.started_monotonic` on the same native boot/monotonic clock, with release
  verified after worker exit/owned-group cleanup/GPU query. Finalizer requires
  it to be at least wall_seconds_through_close and at most
  min(report.wall_cap, report.device_cap). Include holder final removal in the
  separately measured reservation/controller total and keep that within the
  Main hard envelope as well. Never replace elapsed by summed generation time.
- Bind actor.deadline in the **native host's monotonic domain** before outputs;
  do not copy a laptop monotonic value or extend it after seeing results.
  Controller deadline is no later than actor.deadline, entry+wall/device cap,
  and lease-finish-minus-margin. Reserve time for startup verification, query,
  TERM/KILL/reap and release persistence, not just model work. The scope permits
  at most 36000s inference, with tighter Main-selected caps; do not automatically
  choose the maximum. Historical allocation helpers require six hours remaining
  after controller+collector; use the bound applicable Main margin, not a stale
  lease timestamp from a previous experiment.

If hard timeout prevents report.json from being written, retain the manifest's
800-task denominator and all partial task/call files as incomplete evidence.
Do not manufacture a complete driver report, post-hoc placeholders or a release
success. Driver-generated failure reports already retain all 800 result slots,
marking unscored tasks `NOT_SCORED`. Preserve them unchanged. A failed collector
gets its own retained failure/claim; any future collection-only repair needs
separate explicit handling, never rerun generation or erase the first attempt.

## 5. Minimal once-collector checks and archive inventory

Require matching frozen sources, manifest/measurement seals, native test_only
false, original C0/model/tokenizer/config identity, complete report seal and
native/controller/holder exit receipts. Validate all 800 ordered task IDs against
the plan, each scored task file, and conditional call IDs/turns/budgets. Join
driver `call_NNNN_request.json` / `_response.json` to actor
`call_NNNN.request.json`, `.render.json`, `.raw.json`, `.response.json` using
request hashes and token/raw hashes, not filenames alone. Keep count receipts,
identity/load/config/close and error files. Native raw artifacts include output
IDs, finish/stop reasons and timing in `.raw.json`; the actor `.response.json`
adds `raw_utf8_sha256`, `raw_hex`, `decoded`, and nested `response`. The driver's public
response has only request_sha256/text/prompt_tokens/output_tokens/device_seconds.
Do not invent an additional finish-reason scoring gate or normalize raw text.

The driver prechecks the 800 initial renders, then checks each dynamically
realized continuation against the pinned transcript rule. Future continuation
bytes cannot be frozen before child outputs; the presealed call slots/rule and
actual render/token receipts together are the binding. A collector validates
them without re-generating outputs. Preserve original scores/thresholds; any
pure replay validation must reuse the pinned runtime/core, not a new scorer.

The finalizer does not implement these joins. A Main adapter is still required;
the previous alignment collector is an example of once-claim/fresh-output/
failure/inventory ordering, not a callable PCFL validator. Archive transport
anomalies separately from scientific completion. A lost stdout/SSH reply means
reconcile exact receipts/process identities, not launch again.

## 6. Read-only source pins / reusable locations

Observed current bytes (driver is still another owner's working file; Main
must take that owner's final EDITSTOP, not treat this snapshot as its freeze):

| Path | SHA256 |
|---|---|
| `gpu/astra_pcfl_zero_fit_dev.py` | `b0100efe123604dde2900127663a3eda299bc60cc8fe1d40f10c045e48d73638` |
| `tests/test_astra_pcfl_zero_fit_dev.py` | `03734def7a90b16c32a4fd68428d85ff3242a966d43b32a6487c4c05437231b5` |
| `gpu/astra_pcfl_native_actor.py` | `f6aae63e79213c24523201452e7f7de880167c4fb273db18de83f93a3a4f7a26` |
| `gpu/astra_pcfl_vertical_dev.py` | `026c6a8c50f551d874a605e1975f5fe2189643fcbd5e6694c0ad2d2fea0544b1` |
| `organism_v6/pcfl_vertical_dev.py` | `ed1b8c5f1d866e8e036a33c3fbeb278551021413cb63e5b3a35bb72934dae04e` |
| `organism_v6/pcfl_vertical_prepare.py` | `c07ba9b684299a8d6cf6c7b45bbdbb95ed6f3e04db9e8de6e926791610b55c61` |
| `research_notes/astra_memos/ASTRA_PCFL_ZERO_FIT_SCOPE_2026-09-13.md` | `c674b152b6147f6f8a698af065c33648eaeea7a309bbb531e2b59d022c19f29c` |
| `research_notes/astra_memos/ASTRA_PCFL_PRODUCTION_WORLD_BINDING_2026-09-13.md` | `ac2013fe44c3f9bdfdca43defca0d8b19baa39209fab443b74abc128391fea91` |
| `research_notes/analysis/2026-09-13_pcfl_vertical_dev_v2_exact_inference_inventory.md` | `599944f3f351d3d9fe19c7257c4d540d188d728d6eb9f14869c20fb5c80c492b` |

Exact inspected reuse points:

- `/tmp/astra_memory_pairs_main_20260913.py`: `launch`, `hold`, exclusive `write`;
  SHA `5df4a3c00016ad07305658e2febc642a1182d1944106d70b92b463235ede2dbe`.
- `/tmp/astra_level1_next_batch_20260913.py`: `identity`, `reservations`;
  SHA `03ac5f43f19e3a54ed57c7362085ff2d96d7a06c2d9f7fc354c5789e84f8f6c2`.
- `/tmp/astra_real_record_memory_run_20260913.py`: `offline`, `budget`,
  `identity`, `cleanup_owned`, `run_stage`;
  SHA `7028fa9a9b277adc6edfec2398d1885d6c55ec33eb67a1bd51ac36b37e02215e`.
- `/tmp/astra_birth_skill_probe_run_20260913.py`: `gpu_state`, `group_alive`,
  `cleanup`, worker ownership/watchdog pattern;
  SHA `59874c678ce1b36feaa1969721c0dcc761b4fa05072a6231892269991201052c`.
- `/tmp/astra_parenting_alignment_run_20260913.py`: `controller`, `collect`
  for custody/lifecycle patterns only;
  SHA `712248f1fc86b026e68e9cfbc791d3b441c6ded53db82f7622f8f2cd2b8b8c2a`.
- `/tmp/astra_own_source_replay_main_20260913.py`: detached holder and explicit
  once-collector invocation pattern; SHA
  `b259d87ed78332b3a14dab38abdf45eac14b36b3fb89fce2745d3d76b1f01a4c`.
- `gpu/astra_pcfl_cpu_smoke.py`: `run` checks source manifest before/after a
  fresh-output CPU operation; not a diagnostic launcher/collector;
  SHA `488d441805f1f9ea92921668f63a550f28dcbce747c7c0259024eeb1fcdb55d9`.

No tests were executed for this read-only task, no outcomes were inspected,
and no resource availability was queried. This memo does not certify that any
GPU is free, that a native tokenizer qualifies, or that C0 meets any threshold.
