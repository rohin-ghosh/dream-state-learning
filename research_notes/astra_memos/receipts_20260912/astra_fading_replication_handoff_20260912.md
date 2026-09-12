# One-phase original-parent plasticity replication — 2026-09-12

**EDIT-STOP.** Only the three assigned sidecar files were created. No repository
edits, Git, network, GPU operations, native model calls, allocation, launch,
or cancellation. Main owns native preparation, vacancy checks, launch/logs,
the ledger, and terminal release verification.

## Files and validation

- `/tmp/astra_fading_replication_20260912.py` — bounded orchestration.
- `/tmp/test_astra_fading_replication_20260912.py` — **24 CPU fixture tests PASS,
  no skips**, about 2 seconds locally.
- `/tmp/astra_fading_replication_handoff_20260912.md` — this handoff.

CPU test command, from the intended source checkout:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 /tmp/test_astra_fading_replication_20260912.py
```

The tests use fake model/material files, deterministic byte-token fixtures,
mocked native model inventory/material verification and GPU occupancy, and no
subprocess or weight loading. They exercise real orchestration/provenance
logic and inherited parameter-state/fresh-optimizer receipt checks. They do
not substitute for Main's native preflight or prove native tensor equality.

Required unchanged helper: `/tmp/astra_fading_sentinel_20260912.py`, SHA256
`7b0686de7b66fcad27a665c0b30054a893af3ee33d053c26fae903fc1ed8af20`.
An alternative location may be supplied with `--helper`, but different bytes
are rejected. The helper was not modified. Reused helpers are `bind`,
`config`, `fit_command`, `state_inventory`, `check_states`, `verify_fit`, and
exclusive plan/JSON writing. The old four-phase controller is never called.

## Frozen experiment and device mapping

| Branch | Original teach parent seed | Continuation optimizer seed | LR | GPU |
| --- | ---: | ---: | ---: | ---: |
| `seed1-rate-0` | 1 | 0 | 0 | 0 |
| `seed1-rate-3e-5` | 1 | 0 | 3e-5 | 1 |
| `seed1-rate-1e-4` | 1 | 0 | 1e-4 | 2 |
| `seed2-rate-0` | 2 | 0 | 0 | 3 |
| `seed2-rate-3e-5` | 2 | 0 | 3e-5 | 4 |
| `seed2-rate-1e-4` | 2 | 0 | 1e-4 | 5 |

Each branch starts directly from its ORIGINAL SEQ099 `fit_teach/adapter`,
not a previous continuation or another rate. Exactly
`continuation-phase-01.json`: 16 items, 4 epochs, batch4, gradaccum1,
**16 updates**, original rank8/alpha16/dropout.05/seven projections/all layers,
max512/no packing. Single warm-started adapter, frozen base, fresh optimizer,
seed0 in every continuation. One fresh-process fixed48 dev readout follows.
No phase02–04 fits, OFF runs, new eval cases, confirmation requests, retries,
automatic resume, stopping/tuning by outcomes, or outcome-dependent scheduling.
This isolates variation in the original parent optimizer seed; the 48 probes
are not 48 independent replications.

Claim label remains
`TASK_ONLY_INTERFERENCE_NOT_PASSIVE_FADING_NOT_CHILD_SLEEP`.
Authored ACT-only interference can overwrite a formatting habit; it is not
passive forgetting, child sleep, or a new claim about cognition/base origin.

## Native preparation (Main only)

Set `SOURCE` to Main's **actual immutable 3a12807f source tree**, not the live
checkout. No guessed source directory is embedded. Import paths are checked;
the existing native material's source hashes must match the selected modules.
The source label is explanatory, not a Git verification; no Git runs.

```sh
PY=/localhome/local-rohing/v2/venv/bin/python
SCRIPT=/tmp/astra_fading_replication_20260912.py
PARENTS="$HOME/astra_diagnostics/astra_fundamental_replications_20260912_attempt1"
MATERIAL="$HOME/astra_diagnostics/astra_fundamental_fading_20260912_attempt1/material"
RUN="$HOME/astra_diagnostics/astra_fundamental_plasticity_replications_20260912_attempt1"
# Set SOURCE, DEADLINE_UNIX, and LEASE_END_UNIX to actual Main-owned values.
# DEADLINE_UNIX must be > now+600; LEASE_END_UNIX >= DEADLINE_UNIX+10.
PYTHONDONTWRITEBYTECODE=1 "$PY" "$SCRIPT" prepare \
  --source-root "$SOURCE" --runroot "$RUN" \
  --parentsroot "$PARENTS" --materialroot "$MATERIAL" \
  --deadline "$DEADLINE_UNIX" --lease-end "$LEASE_END_UNIX"
```

The existing material is only verified/read, never recreated or overwritten.
All four material files are frozen/inventoried, but only phase01 is consumed.
Model path comes from the pinned original seed1 plan; model inventories must
equal both parents and existing native material. No downloaded/default model.

Exact original plan, teach verified receipt, and teach readout-plan SHA256
pins are embedded from the locally available terminal capsule:

```
seed1 plan:     f2aaa20ab53b7cd3221580f3098da68f0381bd6a120967b6cfa085eedb769252
seed1 fit:      248fee8d701b435c334aafd2551b93ef6da25de137ac71510fa5bb5c49129335
seed1 readout:  f5cc61263806bff26d7b77ca267b70b21507bf2e1feeea78dc4eb510675a7e7a
seed2 plan:     54e44fc9e7193405b85b4a49b44c73ba50e3b075832b406a9538df77d0ad0fae
seed2 fit:      fc5f2337f981ce71fe43a931bcff530019b843936f69104d6883cbb00001599c
seed2 readout:  eea6c81b77aa745e440a68503a9984d52264b8b02932c512baa27dda368ba825
```

Preparation validates actual adapter inventory, original config/80 steps,
original fit/readout supervision and backend cleanup, all48 raw request and
response pairs, response hashes, exact rendered bytes/input IDs, and native
output-token decoding. It does not score/select parents using outcomes.
The new readout inherits exact `cases`, `requests`, and `native_inputs` from
its original parent readout, changing only adapter identity, device/deadline,
and explicitly current source hashes. Both parents must have identical inputs.
Original readout sources remain recorded, not silently presented as current.

Native paths are deliberately strict: adapter paths must match the original
receipts. A local metadata-only capsule is not a runnable relocated parent;
missing weights/receipts or changed native absolute paths fail before output.

## Main launch interface and limits

Main must declare the **150 A40-minute total plasticity cap** and perform full
vacancy checks on GPUs0..5 **before** spawning controllers. Prior reservation
57.68 + six10-minute branches =117.68 A40min, leaving32.32 for the declared
audit/other margin. The script does not independently know campaign spending.

One launch example (not executed by this author):

```sh
CUDA_VISIBLE_DEVICES=0 PYTHONDONTWRITEBYTECODE=1 "$PY" "$SCRIPT" run \
  --source-root "$SOURCE" --runroot "$RUN" \
  --branch seed1-rate-0 --allow-gpu
```

Launch each remaining branch with its exact table device/name. There is no
all-GPU launcher or configurable device mapping; Main provides external logs
and concurrent controllers. The inherited device must match exactly. Keep
the full ledger reservation across CPU preparation and both worker gaps.
The controller does **not** perform full `check_free`; existing native
`base.supervise` performs device occupancy checks before each worker.

Outer branch deadline is `min(CLI_start+600, DEADLINE_UNIX, LEASE_END_UNIX-10)`.
The clock includes CLI setup/import time; the controller arms its cleanup
alarm before input rehashing/worker execution, at effective deadline minus
**140 seconds**. Native supervise applies its existing worker bound and
remaining lease minus140 cleanup (and10-second safety). Thus600 seconds is
the whole branch, **not600 per fit plus600 per readout**. A short available
window fails rather than extending. Main's external watchdog remains needed
for uncatchable controller death or an import/OS stall before alarm setup;
never assume release from a missing terminal file.

Each successful branch has exactly two successful supervised receipts, complete
48-case reduction, unchanged original parent/source/material/model inventories,
unchanged child after readout, and verified GPU/owned-process-group cleanup.
The inherited fit verifier requires exact16 updates/token accounting/no
truncation, one adapter/frozen base, initialized loaded-state check, fresh
optimizer with zero initial state entries/no restore/save, and cumulative
parent80→96 steps. LR0 additionally requires exact full serialized LoRA tensor
inventory equality (keys/shapes/dtypes/value hashes) before, initialized, and
after save; legitimate new manifests need not match the parent tree.
Base is frozen and its bound on-disk files are rehashed; this is not an
independent full in-memory base-tensor dump.

## Outputs and terminal status

Root: exclusively created `plan.json`, `plan.sha256.json`. Schema1 includes
`parents` (original plans/native inputs/provenance and inventories), `branches`,
`rates`, `optimizer_seed:0`, `phase`, model/source/material hashes,
`branch_seconds:600`, `cleanup_seconds:140`, real lease and deadline.

Each branch exclusively creates `reservation.json`, `phase.json`, `adapter/`,
`fit-worker/`, `fit-result.json`, `readout/` (native raw tokens/requests/responses,
supervision and reduction), and `terminal.json`. Terminal records wall-clock
reservation cost, worker summed cost, parent/fit lineage, error, release and
deadline flags. Monetary cost is unknown, not fabricated.

```sh
PYTHONDONTWRITEBYTECODE=1 "$PY" "$SCRIPT" status \
  --source-root "$SOURCE" --runroot "$RUN"
```

Status reports `COMPLETE`, `FAILED_PARTIAL_NO_RETRY`, `NOT_STARTED`, or
`NONTERMINAL_OR_ABANDONED`; status is a receipt display, not a fresh scientific
re-audit. Missing/partial results are never zeros. Existing branch paths
always prevent another launch. Failed branches do not automatically cancel,
rerun, or decide the fate of other branches. Main owns follow-up decisions.

**Remaining limitations:** no native preparation or run performed here;
weights/state and actual runtime feasibility inside600 seconds await Main.
The historical source label and formal model origin are not authenticated
beyond explicit file inventories. Existing native ownership/supervision
behavior is reused without editing the archived/live helper or repo.

**EDIT-STOP.**
