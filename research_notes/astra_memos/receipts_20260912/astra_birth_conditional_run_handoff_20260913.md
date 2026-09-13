# BIRTH conditional runner — EDITSTOP

Final CPU implementation handoff, September 12, 2026. Requested September13
filenames retained. **43 CPU tests PASS in41.913s. No known failing CPU test.**
Main alone handles native integration, launcher implementation and GPU launches.
No source inventory, corpus, trainer, historical artifact, or other agent file
was modified. No Git/native/model/tokenizer/GPU/SSH/network execution occurred.
No level2 module or bridge dependency was added.

## Frozen owned files

- `/tmp/astra_birth_conditional_run_20260913.py`
  SHA256 `072a1333c0411a73ae0fc46c6e70de9afe0bce9b49c74e01bdaae16174195daa`
- `/tmp/test_astra_birth_conditional_run_20260913.py`
  SHA256 `41718101dd3cfe1239f048e9e8686f4086a486bc80cd549cb21945b137c8f62b`
- `/tmp/astra_birth_conditional_run_handoff_20260913.md` — this handoff;
  its hash is returned separately to avoid a self-referential seal.

Exact local regression invocation:

```bash
python3 -B /tmp/test_astra_birth_conditional_run_20260913.py
```

The test source root constant is `/data/home/rohing/dream-state`. For Main's
native CPU regression use importlib to import this test module, set its `SOURCE`
to the reviewed native snapshot path BEFORE unittest loads/runs the suite, then
run `unittest.defaultTestLoader.loadTestsFromModule(module)`. No native tokenizer
or model is loaded by this test suite. Only pure owner audit plus fake tokenizer,
fake training/backend/supervision/process/vacancy receipts are exercised.
One unrelated `ResourceWarning` from existing `nursery_dialogue.py` opening
`parent_prompt.txt` is emitted; no failure and no edit to that source.

## Dependencies and source

- Source supplied at prepare: `~/astra_sources/31b5535ec9f73f7b32fdaf21ccfc3a2a68a948a6`.
- Frozen owner module SHA256:
  `43bf074938e8c4e3a995e43d747ff24f2c6cf70252359cb35134391ff88da74b`.
- Required unchanged local safe-I/O/finite-safetensor/archive helper:
  `/tmp/astra_rulegame_process_write_collect_20260912.py`, SHA256
  `e23160132bf4eac82f220b8066c49de3cf8461e50929f9a82f3eac5e12906892`.
  Only generic primitives are used, never its historical plan/launch APIs.
- Required snapshot vacancy helper `gpu/astra_mini_sudoku_diagnostic.py`, SHA256
  `a586b03bdb9c52f1061aa1e477ae983cc9d45ec0a2cd440642851fd8df8b609f`.
  Called only during Main-operated collection; CPU tests replace vacancy.
- Corpus/diagnostic/trainer/generic capture/source helper hashes are pinned into
  each new plan. The actual reviewed launcher hash is supplied by Main, not
  hardcoded here. Concrete interpreter is `os.path.abspath(sys.executable)`;
  it is NOT resolved through the virtualenv executable symlink.
- HuggingFace tokenizer asset symlinks are followed only to pin their actual
  bytes. The owner's native audit and model file hash checks recheck those
  assets; output/metadata symlinks, hardlinks and special files are rejected.

## Stable API and commands

Protocol: `authored_birth_conditional_run_v1_20260913`.

Public functions:

```python
prepare_fit(source, module_sha256, model, out, device, deadline, lease_end,
            config=None, restart_release=None, restart_sha256=None)
prepare_readout(fit_root, fit_plan_sha256, fit_release, fit_release_sha256,
                out, deadline, lease_end, restart_release=None, restart_sha256=None)
run_controller(root, plan_sha256, allow_gpu=False)
worker(spec, spec_sha256, allow_gpu=False)
status(root, plan_sha256, launch_root=None, launch_sha256=None)
stop(root, plan_sha256)
collect(root, plan_sha256, launch_root, launch_sha256, launcher,
        launcher_sha256, out)
accepted_release(release, release_sha256, plan, plan_sha256)
read_plan(root, plan_sha256)
verify_plan(root, plan_sha256, check_model=True)
controller_command(root, pin, phase, python=None)
worker_command(python, spec, pin)
collection_command(root, pin, launch_root, launch_pin, launcher, launcher_pin,
                   out, python=None)
launch_contract(root, plan, pin, launcher, launcher_sha256)
main(argv=None)
```

All preparations return `root`, `plan_sha256`, `phase`, and
`status=PREPARED_NOT_LAUNCHED`; preparation never launches or chains phases.
`deadline` and `lease_end` are timezone-aware ISO8601 strings. Deadline bounds
controller work/cleanup; collection is separately bounded and must precede the
six-hour lease cutoff. Fresh sibling phase/launch/collection directories only.

Main-only preparation, with `PY` set to the concrete native interpreter and
`MODEL`, `DEADLINE`, `LEASE_END` supplied by Main:

```bash
"$PY" -B /tmp/astra_birth_conditional_run_20260913.py prepare-fit \
  --source "$HOME/astra_sources/31b5535ec9f73f7b32fdaf21ccfc3a2a68a948a6" \
  --module-sha256 43bf074938e8c4e3a995e43d747ff24f2c6cf70252359cb35134391ff88da74b \
  --model "$MODEL" \
  --out "$HOME/astra_diagnostics/astra_birth_conditional_20260912_attempt1" \
  --device 0 --deadline "$DEADLINE" --lease-end "$LEASE_END"
```

Default complete Main configuration (optional `--config /absolute/main.json`):

```json
{"seed":0,"lr":0.0001,"epochs":4,"batch_size":8,"fit_seconds":1800,"readout_seconds":2700,"max_updates_per_arm":128}
```

No automatic recipe/dose search. Explicit positive epoch/update limits and
tighter controller bounds may be supplied; seed0/LR1e-4/batch8 stay fixed.
Actual candidate256rows, native audit, recipe, source joins, exposure and
128updates are verified before launch. Failure preserves preparation markers;
the same output cannot be reused.

Main launcher must execute this exact argv, generated by `controller_command`:

```bash
"$PY" -B /tmp/astra_birth_conditional_run_20260913.py fit \
  --root "$FIT_ROOT" --plan-sha256 "$FIT_PLAN_SHA" --allow-gpu
```

Run it as a fresh controller session with `CUDA_VISIBLE_DEVICES=0` continuously
set for the whole controller, including validation and cleanup. Do not run
this command here or bypass Main's launcher. Main's launcher must itself be a
separate fresh short-lived session and remain alive until controller exit.

After fit controller AND launcher exit:

```bash
"$PY" -B /tmp/astra_birth_conditional_run_20260913.py status \
  --root "$FIT_ROOT" --plan-sha256 "$FIT_PLAN_SHA" \
  --launch-root "$FIT_LAUNCH_ROOT" --launch-sha256 "$FIT_LAUNCH_SHA"
env -u CUDA_VISIBLE_DEVICES "$PY" -B /tmp/astra_birth_conditional_run_20260913.py collect \
  --root "$FIT_ROOT" --plan-sha256 "$FIT_PLAN_SHA" \
  --launch-root "$FIT_LAUNCH_ROOT" --launch-sha256 "$FIT_LAUNCH_SHA" \
  --launcher "$REVIEWED_LAUNCHER" --launcher-sha256 "$REVIEWED_LAUNCHER_SHA" \
  --out "$FIT_COLLECTION_ROOT"
```

Collector returns `validation`, `validation_sha256`, `archive`,
`archive_sha256`, `phase_complete`. Only a complete released pair may feed:

```bash
"$PY" -B /tmp/astra_birth_conditional_run_20260913.py prepare-readout \
  --fit-root "$FIT_ROOT" --fit-plan-sha256 "$FIT_PLAN_SHA" \
  --fit-release "$FIT_COLLECTION_ROOT/validation.json" \
  --fit-release-sha256 "$FIT_RELEASE_SHA" --out "$READOUT_ROOT" \
  --deadline "$READOUT_DEADLINE" --lease-end "$LEASE_END"
```

The readout launcher uses `readout --root "$READOUT_ROOT" --plan-sha256
"$READOUT_PLAN_SHA" --allow-gpu`, otherwise exactly the same contract.
Readout status/collection use their own root/plan/launch/output variables.
No phase is automatically launched after prepare or collect.

Stop: `"$PY" -B /tmp/astra_birth_conditional_run_20260913.py stop --root
"$ROOT" --plan-sha256 "$PLAN_SHA"`. It verifies exact PID/start ticks/argv and
signals only the owned controller; existing supervisor cleans workers. It
does NOT assert GPU/queue release. Collection is still required. Failed
released phases can be explicitly linked on a FRESH preparation using
`--restart-release /prior/validation.json --restart-sha256 SHA`; no automatic
retry, successful-phase restart, in-place resume or silent changed recipe.
Prior failed-attempt costs are recorded separately, not erased.

## Exact launcher receipt contract

Create a fresh sibling launch directory with exclusive writes. Obtain the
static fields by `launch_contract(root, plan, pin, launcher, launcher_sha256)`.
`launch.json` must contain EXACTLY those fields plus the eight dynamic fields:

```text
protocol, phase, root, plan_sha256, driver_sha256,
launcher, launcher_sha256, command, device, controller_seconds,
continuous_reservation,
pid, pgid, session, launcher_pid, launcher_pgid, launcher_session,
started_wall, gpu_uuid
```

- `command` is the exact list from `controller_command`, no shell wrapper in
  the recorded controller argv. `continuous_reservation` must be `true`.
- Controller `pid == pgid == session > 1`; launcher independently
  `launcher_pid == launcher_pgid == launcher_session > 1`, different PID.
- `started_wall` is finite Unix wall seconds before controller start; use the
  selected native GPU's actual UUID in `gpu_uuid`. Device is the plan string.
- `driver_sha256` is the plan sidecar hash. `launcher` is the absolute reviewed
  script path; Main supplies the matching reviewed hash at CLI. No guessed hash.
- After wait/cleanup, exclusive `exit.json` must contain EXACTLY:
  `{"launch_sha256": "<actual launch.json file hash>", "returncode": <int>,
  "ended_wall": <finite Unix seconds>}`. Successful result requires return0;
  failed terminal requires nonzero. Launcher must exit before collection.
- Optional allowed files: `gpu.xml`, `controller.log`, `launcher.log`.
  No other launcher filenames, credentials or environment dumps are archived.

`status` with launcher binds checks launcher/controller/worker PIDs, process
groups, sessions and current descendants, including orphaned group/session
members. It only reads ownership receipts and marker presence, never result
bodies. Collection repeats scope checks and actual native GPU/proc-reservation/
pending+running queue vacancy before acceptance. Do not collect from a parent
environment carrying CUDA_VISIBLE_DEVICES.

## Scientific and evidence contract

- Fresh-base AUTH then DERANGED, one rank8/alpha16/dropout.05 LoRA per fit;
  original supervised V3 trainer unchanged, no warmstart, packing, split, drop
  or target truncation. Workers re-encode against saved exact IDs/labels before
  training. Exactly target-only labels plus one EOS; context/padding masked.
- Native row and optimizer-batch exposure remains in
  `material/native_audit.json`. Fit receipts report actual manifest steps/losses,
  unpadded input/target exposure and audited padded/padding/EOS exposure; saved
  config/meta/manifest/DONE/files join before finite safetensor streaming scan.
- Main's native audit is now locally readable. Independently checked its hash:
  `/tmp/astra_birth_native_audit_20260912_attempt1.json`, SHA256
  `55f8987c448f62d6745ec3b59c245e7ae1db72fafa1c87df9702615794309993`.
  It reports128updates/arm,18352input/2912target per epoch,73408input/
  11648target/93696padded per four-epoch fit. This was JSON inspection, NOT
  a native rerun or authentication of model origin. New prepare explicitly
  re-audits into its new immutable root; it does not mutate that old audit.
- Readout OFF/AUTH/DERANGED uses128 IDENTICAL requests each:32PROSPECT,
  64REVISE,16ADDITION,16COPY;384calls total, greedy temperature0, generation
  seed20260912, max64tokens/call. Each cell has its own process/backend/base
  and appropriate adapter. No parent prompts, online updates or logits phase.
- ALL384 paired request/response records, native token IDs, identity/cleanup/
  isolation/usage/manifests must close BEFORE any score_outputs invocation.
  Missing OFF or any other cell fails; invalid outputs remain denominators.
  Raw finish_reason/stop_reason/output IDs remain; flags distinguish limit,
  length finish and tokenizer EOS observations without inventing missing EOS.
- Descriptive registered counts for BOTH trained arms: PROSPECT29/32,
  REVISE58/64; each registered goal/belief twin15/16 and each
  expected/observed/prior_action twin29/32, strict own-map paired flips.
  Each anchor requires max(ceil(.95*N), OFFinstruction_compliant-1), here16/16,
  with zero tag spill. Full raw/semantic/exact/component/stratum/twin rows for
  ALL cells are retained; AUTH semantic and DERANGED assigned-map metrics
  remain separate. OFF is complete baseline evidence, not a dropped cell.
- No automatic L1 verdict, full-core verdict, clean-lineage or deployment-gym
  readiness claim. This is the authored conditional/locality BIRTH component,
  NOT own wake and NOT_CLEAN. Origin remains UNRESOLVED_LOCAL_HASHES_ONLY.
  Same conditional presentations asSEQ108 do NOT isolate anchor-induced
  gradient dilution or cost differences. Level2 bridge testing is separate.

## Collection, caps and limitations

Existing supervisor600s worker/load180/call120/cleanup140 unchanged. Each
member gets its own existing supervisor accounting scope; a single outer
controller caps fit1800/readout2700. Worker parent-death watchdog stays active
through source/model verification, model work and cleanup. Main owns launcher
supervision and reservation. Normal stop uses controller SIGTERM; SIGKILL or
missing terminal is never falsely accepted as released completion.

Each collector has an inclusive300s timer, exclusive per-root claim and fresh
output; failure/partial archive is preserved without accepted validation or
blind retry. Failed phases may have release evidence but no aggregate or
phase_complete flag. Successful phases recheck saved aggregate after the
all-member barrier. Collection does not load tokenizer/model, fit or generate.

Costs use launch-to-final-release wall intervals: fit<=2100s,
readout<=3000s, their sum<=5100s (upper bound, NOT forecast). Training, calls,
load, worker and controller intervals are NESTED, never added together. Idle
delay before collection is included in its phase launch-to-release interval.
Six-hour lease cutoff remains independent. Main can narrow phase caps.

Safe archive includes exact allowlisted metadata and full response/call
records; unknown files/directories, credentials, duplicate/nonfinite JSON,
changed hashes and symlink/hardlink/special metadata fail closed. Metadata
limits32MiB/file,256MiB total,2048entries. Finite weights are inspected and
hashed, EXCLUDED from capsule: **no weights-in-capsule promise**. Validation
separately binds capsule, exact inventory and final vacancy XML. This is
local hash custody, not external attestation, semantic contamination proof
or independent full frozen-base tensor verification.

CPU coverage includes actual CLI parsing/dispatch/generated commands,
mock-supervised controller run, worker exact masks/fresh trainer call,
candidate/source/native count mismatch, partial fits/cells and scoring
barrier, readout usage/identity, finite weights, recipe/lease/phase/launcher
joins, full collection, unknown/credential/symlink failures, second-vacancy
failure preserving capsule, timeout, stop PID reuse, parent death and
restart restrictions. Native prepare/fit/backend/launcher compatibility and
actual timing/release remain Main integration work; no claim these43CPU
tests independently established native acceptance.

**EDITSTOP. No additional implementation or tests planned.**
