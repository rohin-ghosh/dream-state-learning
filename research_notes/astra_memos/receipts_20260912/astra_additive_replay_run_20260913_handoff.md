# Additive replay runner — EDITSTOP

September 13, 2026. Final 18 runner CPU tests PASS6.361s;10 core tests PASS1.206s.
No native/model/network/GPU/Git operation or launch by this author. Main owns
native tiny Torch acceptance, preparation, allocation, outer custody and launch.
Trainer API is implemented exactly as Beauvoir published, not the superseded
suggestion. Core and trainer EDITSTOP pins are both bound and integration-tested.
CLI help passes. Native tiny Torch acceptance/preparation remain Main-only
prerequisites, not established here.

Final owned runner pins:
- `/tmp/astra_additive_replay_run_20260913.py`:
  `ca54e7e1971d89224bb8dec8f3518d0a6a73ec4d1abe6f29278bab335b1618a5`
- `/tmp/test_astra_additive_replay_run_20260913.py`:
  `9d7fee6f3e1af9bbae8170abeee86747dfe344bf2d727c7962e9cdc448fe53b3`
- Handoff hash returned separately to avoid self-reference.

## Stable API and closed spec

```python
prepare(root, spec_path, spec_sha256, allow_native=False)
verify(root, plan_sha256, native=False) -> (memory, plan, bound)
allocation(plan)
worker(root, plan_sha256, stage, allow_gpu=False)
controller(root, plan_sha256, allow_gpu=False)
collect(root, plan_sha256, completion_sha256, out)
```

Single original seed per root. Stages fixed ADDITIVE_fit,ADDITIVE_readout,
MEMORY_ONLY_fit,MEMORY_ONLY_readout, four fresh processes. For outer integration,
use the THREE-value `verify` return (as old own-repair), NOT alignment's two-value
return. `bound["probe"].gpu_state(plan)` and `allocation(plan)` are retained.

Exactly these spec keys:

```text
runner_sha256
repair_runtime
core
trainer
protocol
repair_history
seed
fit_seed
gpu_index
gpu_uuid
expected_boot_id
lease_end
```

`repair_runtime`, `core`, `trainer`, `protocol` each have exactly `path,sha256`.
`repair_history` has exactly `root,plan_sha256,completion_sha256,collection,
scores_sha256`; its `collection` has `path,sha256` naming actual collection.json.
All paths absolute native paths. Main supplies current original completed
own-repair root+once-collected scores and fresh allocation/boot/lease fields.
`seed` and `fit_seed` must be identical strict integers0/1/2. No extra upstream
bindings are guessed: the old repair plan supplies its frozen memory/lower/
capture/source dependencies; their actual old verify path is reused unchanged.

Pins:
- repair_runtime `/tmp/astra_own_replay_repair_run_20260913.py`:
  `f1e3782378959f0c2552eaf9646a6b8827b876652a535d3248e38fe28371c4fe`
- core `/tmp/astra_additive_replay_core_20260913.py`:
  `b58e4c90e2abdd26648475c9fb1fe92e3bc3fef2fa7664ecaaa69fc93591076a`
- trainer `/tmp/astra_additive_replay_train_20260913.py`:
  `3f2e73ef69b12c8db211e1d3043e4559713e036ffe09571ab8bc4c5199a426a0`
- protocol native copy of `ASTRA_ADDITIVE_REPLAY_DEV_2026-09-13.md`:
  `724d5a6e1aea7dca4b0ae42aec6e2fd0252b98646f7c903432927263f2c391e9`

No tiny Torch result is invented. Its acceptance remains Main's explicit
prelaunch prerequisite, followed by native tokenizer preparation on all3roots.

## Source and trainer seam

`bind` calls pinned old `verify` and `validate_completed`, then verifies actual
completion/once-collection joins, raw score cells and manifests, original
recipient and all24admitted observations. It never calls old worker/controller/
collector/admit and never modifies a plan or module global. Five historical
panels LOWER/HIGH/LR0/REPLAY/EXTRA_MEMORY are imported without new inference.

Actual old `training_EXTRA_MEMORY.json` and `training_REPLAY.json` FILE hashes
are re-read and compared with the old plan before `prepare_pair`; no reserialized
JSON hash is substituted as a byte pin. Both original flat encodings go intact
to Beauvoir's accepted `prepare_pair(...,seed=...,source_pins=...)` API. Runner
checks returned primary/replay objects, fixed24pairs and all executed token/dose
counts against independently checked core material. One common `paired.json`
is used by both arms; exact old occurrence IDs/order remain historical labels,
not falsely renamed as new sources.

Fresh fit loads the frozen base and original perception parent, not any repair
descendant. Calls `run_training(paired,tok,base,cfg,out,arm=...,init_adapter=...,
expected_parent_files=...,trainer=frozen_trainer,corpus_sha=...)` exactly.
Every config field, including legacy note, is copied unchanged from old
EXTRA_MEMORY; LR3e-5,8passes,batch1/grad_accum1,rank8alpha16dropout.05.
Parent/source/initialized tensors and optimizer defaults must match history;
fresh empty optimizer and nonzero finite adapter changes are required.

New `check_fit` checks explicit new trainer/objective/protocol/pair/source pins,
exact executed epoch/occurrence IDs, applicable component losses and their SUM,
finite losses, full304/256/256step dose, no skipped/truncated/split rows, original
target/EOS accounting, combined forward tokens and LoRA warm-start invariants.
It does not monkeypatch the old128step guard or assert equal compute.

## Lifecycles, clocks and costs

Main holds reservation with holder CVD set; controller CVD is empty, workers
receive the bound UUID. Fresh boot/lease+vacancy checks precede each isolated
process; PID/PGID/startticks, launch/start/done/exit/release and raw outputs are
retained. Process-group cleanup and GPU vacancy required, with both initial and
cleanup failures preserved. No retries or recollection.

Clocks start at function entry: prepare180, controller7200including verification
and cleanup, collector180. Six-hour lease-finish margin. Campaign ceiling8A40h
including preparation is Main's outer allocation responsibility. Limits are
2fits608/512/512updates176/152/152calls per root;6fits1632updates480calls total.
ADDITIVE executes192extra observation forward/backwards per root; MEMORY_ONLY0.
No new capture/teacher calls. Different compute/time/RNG consumption is explicit.

Cold readout reuses frozen memory `capture_readout`, `route_for`, `build_calls`,
`score_calls`, original tokens/scorers: exact+paraphrase and48held+12canary.
Full call/route/output/timing inventories are checked after every process is
closed. Collector uses frozen `screen` (exact>=8/7/5 and no lost LR0-correct
held/canary items) and unchanged evaluator-only constant-target diagnostic.
Scores/harms never gate execution or select roots. Historical controls have
zero incremental cost and are explicitly noncontemporaneous.

## Native commands — Main only, not executed here

```bash
PY=/localhome/local-rohing/v2/venv/bin/python
RUNNER=/tmp/astra_additive_replay_run_20260913.py
CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 "$PY" -B "$RUNNER" prepare \
  --root "$ROOT" --spec-path "$SPEC" --spec-sha256 "$SPEC_SHA256" --allow-native
CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 "$PY" -B "$RUNNER" controller \
  --root "$ROOT" --plan-sha256 "$PLAN_SHA256" --allow-gpu
CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 "$PY" -B "$RUNNER" collect \
  --root "$ROOT" --plan-sha256 "$PLAN_SHA256" \
  --completion-sha256 "$COMPLETION_SHA256" --out "${ROOT}_collected"
```

Preparation returns plan hash/counts/limits. Success returns completion hash.
Only Main's once-orchestrator collects after success and release. Worker CLI is
internal; `--stage` values are the fixed four stages. Native roots/spec locations
are Main inputs, not inferred from a local archive path.

## Artifacts, tests and limitations

New root: material.json, paired.json, training_ADDITIVE.json,
training_MEMORY_ONLY.json, calls.json, spec/plan, immutable source/upstream/
repair snapshots and preparation receipts. Each run stage preserves process
receipts, logs, training outputs or every raw readout request/response.
capture_complete.json is written only after all four stages validate.

Once collector writes scores.json with cells/fits/parameter norms, component
training costs, imported histories, bindings, unchanged screens and constants;
collection.json binds report/completion hashes and collection_seconds. Original
flat prepared token counters are memory-only legacy fields; `token_accounting`
is the explicit combined breakdown and manifest `train_tokens_seen` is combined
actual tokens. Fit manifests retain timing/peak-memory fields where measured.

```bash
PYTHONDONTWRITEBYTECODE=1 timeout 90s python3 -B -m unittest discover \
  -s /tmp -p 'test_astra_additive_replay_run_20260913.py' -q
```

18 tests cover actual trainer.prepare_pair compatibility on3archived input
banks, raw file pins vs reserialized objects, both full memory objectives,
wrong summed loss/order/token/warm/dose/nonfinite checks, explicit trainer call,
original recipient, prepare/verify, full four-stage mock validation, cold native
receipt joins, boolean exit rejection, no-spawn precheck, CVD and own cleanup,
dual failure receipts, stop-on-failure, entry clocks, once-collection and history
reuse. Initial test fixture used an overbroad protected directory and was fixed;
no production guard was relaxed. No actual fit/output was generated by tests.

Torch gradient/parity and native tokenizer/GPU identity remain Main checks.
Success would support only this one objective-package/operating point, not
parenting, repeated cycles, clean-lineage qualification or H1/H2. Fresh MEMORY_ONLY
drift from old EXTRA_MEMORY needs diagnosis before causal attribution. No
automatic promotion, dose ladder or recipe sweep exists.
