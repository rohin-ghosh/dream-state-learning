# Fading sentinel sidecar — 2026-09-12 — EDIT-STOP

## Ownership and validation

Only these deliverables were edited:

- `/tmp/astra_fading_sentinel_20260912.py` (342 lines)
- `/tmp/test_astra_fading_sentinel_20260912.py`
- `/tmp/astra_fading_sentinel_handoff_20260912.md`

28/28 CPU fixture tests PASS, zero skips. CLI `--help` PASS. No GPU use,
network, Git, subprocess training, native tokenizer/model calls, downloads,
or scientific runs were performed. No repository files were edited. Existing
native warm-start 21/21 PASS is Main's previously reported evidence, not a
new test run here. Fixtures mock native preparation/occupancy/supervision;
they are not proof of native runtime success.

Final implementation SHA256:

```
7b0686de7b66fcad27a665c0b30054a893af3ee33d053c26fae903fc1ed8af20  /tmp/astra_fading_sentinel_20260912.py
92a3ebee68f9438ef0b38cc1d4380964006355805405da2db7736affe9cbd8f7  /tmp/test_astra_fading_sentinel_20260912.py
```

Run the CPU tests from the intended source snapshot's working directory:

```bash
PYTHONDONTWRITEBYTECODE=1 python -B /tmp/test_astra_fading_sentinel_20260912.py
```

Coverage: exact native CLI-to-TrainConfig equality, only LR changes, seed0
every phase, separate fixed parent chains, actual seed0/material/source
bindings, rejected stale/symlink/overlapping paths, immutable parents,
token/step/completion receipt checks, fresh optimizer and cumulative steps,
LR0 full saved-parameter equality including dtype, malformed/missing states,
two native supervised workers per phase with a shared lineage budget,
outcome-independent four-phase schedule, 1800-second bound and cleanup alarm,
partial failures/no replay, missing supervision, and failed cleanup.

## Fixed assay

Label: `TASK_ONLY_INTERFERENCE_NOT_PASSIVE_FADING_NOT_CHILD_SLEEP`.
Formal model origin stays `UNRESOLVED_LOCAL_HASHES_ONLY`.
ACT-only alternative targets may overwrite the habit; this is not evidence of
time-alone forgetting, passive fading, or child sleep. No claim changes.

| Rate CLI | Learning rate | Initial CUDA_VISIBLE_DEVICES |
| --- | --- | --- |
| `0` | 0.0 | `4` |
| `3e-5` | 0.00003 | `5` |
| `1e-4` | 0.0001 | `6` |

Every lineage starts from the exact same actual seed0 teach adapter under
`astra_fundamental_teaching_20260912_attempt1/fit_teach/adapter`.
The supplied seed0 plan is pinned to SHA256
`d5a3d0297290184061b5cfcc3bf7fa5ba36a5995fbaedb021df464be7879ec5e`.
The pin was checked against the local seed0 terminal archive's plan, without
reading readout responses. The actual native adapter path and its recorded
fit-result inventory must match, not a guessed or newly fitted checkpoint.

Four immutable, pre-audited corpora in order:
`continuation-phase-01.json` through `continuation-phase-04.json`.
Each phase has 16 examples, 4 epochs, batch 4, accumulation 1, 16 updates.
Total per lineage: 64 additional updates; inherited seed0's 80 steps produce
144 cumulative steps. Rank8/alpha16/dropout0.05, all seven projections,
all layers, AdamW, no packing, max length512, unchanged V3 defaults.
Each phase freshly seeds optimizer/training with seed0 and loads all weights
from the immediately preceding single adapter into one adapter. No nested
adapters, merge, base updates, optimizer resume, or parent overwrites.

Each completed write is followed by a fresh native readout worker process,
then source/native-token/completeness reduction. Exactly the current native
readout module's fixed 48 dev cases: 32 addition and16 memory, seed20260912,
temperature0, max64 output tokens/call. No baseline OFF run, no confirmation
requests, no new evaluations. The four-phase loop never reads action,
adherence, memory, or other behavioral scores to select, stop, or change data.
Only integrity/completeness/time/cleanup failures stop execution honestly.

## Preparation: Main only, CPU/native tokenizer

The sidecar imports only from the explicit source snapshot and rejects mixed
import roots. Source hashes must match the committed material's source
hashes, including the warm-start trainer. Copying the script unchanged is OK;
editing script/source/material after preparation invalidates the plan.

Set these variables from actual native locations/evidence, not examples of
guessed model paths:

- `SOURCE`: immutable native repository snapshot containing the current
  continuation material, V3 warm-start trainer, native readout and dependencies.
- `MATERIAL`: completed native continuation `audit-native` output, not injected
  tokenizer fixtures or raw material emission.
- `SEED0_ROOT`: actual native `astra_fundamental_teaching_20260912_attempt1` root.
- `RUNROOT`: fresh, nonexistent output directory outside all protected inputs.
- `DEADLINE`: Main's absolute Unix campaign cutoff; must leave over1800 seconds
  at preparation and must not exceed `LEASE_END`.
- `LEASE_END`: actual lease end as Unix float, recorded separately.

```bash
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONDONTWRITEBYTECODE=1 \
python -B /tmp/astra_fading_sentinel_20260912.py prepare \
  --source-root "$SOURCE" --materialroot "$MATERIAL" \
  --seed0-plan "$SEED0_ROOT/plan.json" \
  --startingadapter "$SEED0_ROOT/fit_teach/adapter" \
  --deadline "$DEADLINE" --lease-end "$LEASE_END" --runroot "$RUNROOT"
```

There is deliberately NO `--model` override: the model comes from the actual
seed0 plan and must exactly equal the authenticated native material's model
path and file hashes. Preparation checks current model hashes and seed0 fit
inventory, native material verifier, all four phase-file hashes, exact seed0
recipe/case IDs, parent completion, sources, and original fit cleanup. It then
uses native `readout.prepare` to freeze one 48-case tokenizer/template plan;
this performs CPU tokenizer work but no model inference. New phase readout
plans reuse these frozen requests/renderings/token IDs with the actual
post-write adapter hashes/identity and the effective lineage deadline.

Python entry points (call `bind(source_root)` first):

```
prepare(materialroot, startingadapter, seed0_plan, source_root, deadline, lease_end, runroot)
run_one_rate(root, rate, allow_gpu=False)
verify(root)
```

## Launch: Main's allocation and ledger only

Before ANY launch, Main declares the separate **90 A40-minute fading budget**
(three30-minute lineage bounds), resolves contention with other tasks, runs
the FULL existing `check_free` for all intended devices BEFORE spawning any
controller, and retains each device's external ledger reservation across the
controller's entire lifetime, including all CPU and between-worker gaps.
The sidecar does not allocate resources, launch sibling controllers, import
or call full `check_free`, or modify Main's external ledger. Its local
`reservation.json` is an ownership/accounting receipt, NOT an external lock.

Commands for Main's separate launcher, only after those checks:

```bash
CUDA_VISIBLE_DEVICES=4 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONDONTWRITEBYTECODE=1 \
python -B /tmp/astra_fading_sentinel_20260912.py run-one-rate \
  --source-root "$SOURCE" --runroot "$RUNROOT" --rate 0 --allow-gpu

CUDA_VISIBLE_DEVICES=5 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONDONTWRITEBYTECODE=1 \
python -B /tmp/astra_fading_sentinel_20260912.py run-one-rate \
  --source-root "$SOURCE" --runroot "$RUNROOT" --rate 3e-5 --allow-gpu

CUDA_VISIBLE_DEVICES=6 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONDONTWRITEBYTECODE=1 \
python -B /tmp/astra_fading_sentinel_20260912.py run-one-rate \
  --source-root "$SOURCE" --runroot "$RUNROOT" --rate 1e-4 --allow-gpu
```

Main may spawn those controllers concurrently via its own launcher. The
sidecar checks the inherited CUDA_VISIBLE_DEVICES exactly; it does not set it
after startup. Native `base.supervise` performs compute occupancy checks
before and after each worker, which do not reject the GPU-free controller.
Every fit/readout worker uses the SAME lineage root for native aggregate
receipt accounting, rather than resetting the budget for each readout.

At controller start:

```
effective_deadline = min(started_unix + 1800, prepared_DEADLINE, real_LEASE_END - 10)
```

The native supervisor retains its600-second worker ceiling,140-second
cleanup reserve, load/call bounds for readouts, and process-group cleanup.
A controller alarm fires at effective_deadline minus140 seconds, including
during CPU verification, to enter cleanup before the hard endpoint.
Source/model/parent/material audits and gaps count in the controller's
monotonic reserved_seconds. Worker reserved_seconds are also reported
separately; do NOT add these to the controller total (double counting).
There is no guarantee all eight workers finish within1800 seconds; insufficient
time leads to an explicit partial failure, not a skipped readout or retry.
Main should retain its outer ownership/watchdog protections as usual.

## Artifacts and interpretation

Prepared root:

```
plan.json + plan.sha256.json
readout-template/plan.json + plan.sha256.json
```

Plan schema1 binds source_root/source_hashes, model/model_files,
startingadapter/parent_files, seed0_plan/seed0_plan_sha256/seed0_fit_sha256,
materialroot/material_files, cases, rates/configs, devices, real_lease_end,
deadline, lineage_seconds1800, worker_seconds600, and readout_template_files.

Each `rate-<rate>/` contains:

```
reservation.json
continuation-phase-01/ ... continuation-phase-04/
  phase.json                 # actual parent, recipe, deadlines
  fit-worker/                # native stdout/process/supervision receipts
  adapter/                   # fresh V3 adapter and warm-start manifest
  fit-result.json            # parent/output hashes, parameter equality, tokens
  readout/                   # sealed native plan, raw calls/tokens/cleanup/reduction
  result.json                # phase fit + both costs + bound reduction hash
terminal.json
```

LR0 checks every serialized LoRA parameter's complete key set, shape, dtype,
and tensor byte hash against the immediately preceding parent, the native
trainer's source/initialized inventories, and its final-state inventory.
Saved tensors are actually loaded on CPU using safetensors or
`torch.load(weights_only=True)`, checked finite and LoRA-only. LR0 rejects
even dtype conversion differences. It does NOT compare entire output artifact
trees to parents: new manifests/lineage metadata legitimately differ.
Base freezing is checked via native warm-start trainability receipts and
unchanged bound base file hashes; the sidecar does not serialize/re-hash the
entire frozen base's live in-memory tensors.

`COMPLETE` requires all four phase results, all eight native supervision
receipts, exact complete native readouts, verified process-group/GPU cleanup,
and meeting the effective deadline. Failure yields
`FAILED_PARTIAL_NO_RETRY`, retaining evidence. Fresh paths are exclusive;
there is no overwrite, retry, automatic resume, replay, or outcome tuning.
Do not rerun a started rate on the same root, even if no phase finished.

Status (CPU; no occupancy query or launching):

```bash
PYTHONDONTWRITEBYTECODE=1 python -B /tmp/astra_fading_sentinel_20260912.py status \
  --source-root "$SOURCE" --runroot "$RUNROOT"
```

Absent terminal receipts are `NOT_STARTED` or `NONTERMINAL_OR_ABANDONED`, never
scientific zeros or evidence of release. Abrupt SIGKILL/host failure can
prevent a terminal receipt and normal supervisor cleanup; Main must resolve
owned worker groups and GPU/ledger state explicitly. Status is not a live
health/cleanup detector. Monetary billing is not inferred; native readout
token costs and actual reserved seconds are retained.

## Remaining limitations / handoff

- Main must run native CPU preparation/token/parent checks on the actual
  immutable snapshot and decide whether/when to launch; this sidecar has not
  been run against native weights here.
- Actual LoRA tensor loader paths and native training/readout execution were
  not exercised by these dependency-free CPU fixtures. Existing native V3
  warm-start evidence is reused, not replaced by mocked orchestration tests.
- Timing is bounded but not forecast-proven. Repeated native model/source
  hashing and CPU adapter state audits count in the lineage wall reservation.
- Native base path is never guessed. Changed seed0 plan/source/material,
  copied-to-a-different-path parents, stale outputs, or mixed snapshots fail
  rather than being silently repaired.
- Full allocation checks, atomic external ledger ownership, separate budget
  declaration, outer watchdog, launch/release operations, and any later paired
  seed1/2 decision remain Main's responsibility. This script supports only
  the seed0 sentinel, not a sweep or replication framework.

EDIT-STOP: deliverables ready; no further edits to these or other scopes.
