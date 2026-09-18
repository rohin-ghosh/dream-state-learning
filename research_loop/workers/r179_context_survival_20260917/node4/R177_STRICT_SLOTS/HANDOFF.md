# R177 NODE4 strict-slot handoff — Ampere / Bacon / Main

Ready: 2026-09-17 19:01 UTC. New work stays inside the assigned NODE4 write set.
Rohin167 explicitly allocates physical2 to Ampere judge training and physical5
to Bacon's local Qwen V-tool. This is a non-material outer containment operator,
not a new permission gate, benchmark change, judge validation or model-load claim.

## Receiving proof and immutable pins

Receiving bundle: `/localhome/local-rohing/orch_r177_strict_slots_20260917_v1`.
Local source: this directory; exact transported bytes: `bundle_v1/`.
Receiving receipts copied without modification into `receipts_v1/`.

| Artifact | SHA256 |
| --- | --- |
| `slot_policy.py` | `6c69c690d4e2491255a3a12370b1143515a4d223456880e889fd24eafaea0c51` |
| `test_slot_policy.py` | `65317f2b03303f3805da338120df7f4f9a173c077d572c67c93733ab20159820` |
| `BUNDLE.json` | `d26f808fcce89c9d5674d69484bcbac614608761b1f2602d04ee6e5935b49aec` |
| `CPU_RECEIVING.json` | `6f3e64ea84142858af042b3656abf0ed7bc592cc449c6f1112d50fc53d4afdd7` |
| physical2 `CONTAINMENT.json` | `dfcd7f16cb5df2a8e670c478d466ec1958c7c74299053f9b492598a576f1bf92` |
| physical5 `CONTAINMENT.json` | `726565711acefb91301f416e7f5d2bcfd0ff881a6edb7627c3f4530cbfe017a3` |

18 local CPU regressions and the same18 actual-receiving regressions PASS.
Both actual strict-service probes passed at18:58:26 UTC, nonroot UID/GID2524,
empty capability sets, NoNewPrivileges, exact systemd cgroup, no inherited NVIDIA
FDs, target open/close, **all seven foreign minors denied**. No torch/model load.

| Owner | Physical | Kernel minor | Exact UUID | Probe path below bundle |
| --- | --- | --- | --- | --- |
| Ampere | 2 | 1 | `GPU-35dcea35-12bc-f2f3-d5d2-d2eaa8bacdd8` | `attempts/probe_2_1789671506809013676/CONTAINMENT.json` |
| Bacon | 5 | 6 | `GPU-2e7eb3b8-9b0b-3729-f5ff-2bbdad6a4a30` | `attempts/probe_5_1789671506802072866/CONTAINMENT.json` |

Original privileged admission checks also passed at18:58:36–38 UTC:
`attempts/check_2_1789671515234246026/ORIGINAL_ADMISSION.json` and
`attempts/check_5_1789671515658224658/ORIGINAL_ADMISSION.json`.
These historical clear reports are **not reusable launch admission**.
Every launch runs the same unchanged scanner/reconciliation again, preserves the
whole original report and requires actual clear/root/UUID/minor evidence before
the strict service starts. No busy-preflight exceptions, filtered blockers,
synthetic clear, quiet-window retries or legacy0/1 guard rebinding are used here.

## Exact launch templates

Run on NODE4, using the remote handoff scripts under
`/localhome/local-rohing/orch_r177_strict_slots_handoff_20260917_v1/`.
They are foreground one-shot launchers: use the owner's existing bounded command
runner/session, not repeated calls after a failure. Every attempt/exit is retained.

Ampere:

```bash
bash /localhome/local-rohing/orch_r177_strict_slots_handoff_20260917_v1/ampere_launch.sh /localhome/local-rohing/orch_r177_ampere_judge_20260917/released_all_v4
```

At18:59 UTC, v4 has `PASS_CPU_NOT_TRAINING`, matching inventory SHA
`ae63319aa8ce8a81968985b32632f9ade7c5ff8d832b835b8819ed0ff6138a01`.
The old v1 CPU failure is preserved and does not block v4. Confirm the owner has
not already dispatched this root before invoking its one-time training harness.
The template binds its current inventory, TRAIN_CONFIG, CPU_GATE and entire
Python source closure, then calls `released_receiving.py train` directly after
strict containment and fresh original admission. Do **not** nest another
`physical2_confinement.py dispatch-train` inside this service: its sudo would
correctly fail under NoNewPrivileges. The workload retains its own CPU, model,
dataset, capacity,7200-second/2000-step and contamination checks. Outer service
budget7300 seconds includes setup; it does not increase the inner training cap.
Neither this worker nor this script changes judge data or trains a model itself
until Ampere explicitly invokes the executable launcher.

Bacon:

```bash
bash /localhome/local-rohing/orch_r177_strict_slots_handoff_20260917_v1/bacon_launch.sh "$RECEIVING_ROOT" "$PYTHON_IMPORT_ROOT" "$ACTUAL_PYTHON_ENTRYPOINT" "$EXISTING_SERVICE_CONFIG" --your-existing-loader-arguments
```

Set the four variables to Bacon's real tested files inside
`/localhome/local-rohing/orch_r177_local_qwen_vision_20260917/`; no guessed loader
or synthetic observations are supplied. `$PYTHON_IMPORT_ROOT` can be the existing
`cpu_stage1/source` directory when appropriate. The current processor receipt
and CPU source are not a launched service. Outer local-Qwen budget3600 seconds,
fixed one-GPU UUID, offline HF/Transformers, no hosted fallback. The owner retains
the DEVELOPMENT-only image/question contract and factual smoke gate.

For additional bound configuration files, use `slot_policy.py prepare` directly
with repeated `--bind /absolute/owned/file`; arguments after `--` become the exact
Python entrypoint argv. `prepare` prints JSON containing the immutable CONFIG
path. `launch --config PATH` accepts that exact path only. It validates current
host, lease bytes, source closure, same-boot probe and finite wall, performs one
privileged scan, enters a unique strict service and repeats containment checks
before `exec`. It never signals another service or native owner.

## Remaining scope and status

No broad permission wait remains for2/5. Ampere/Bacon still own their workload
CPU/data/model gates and actual launch; this handoff supplies the outer policy.
This worker has not loaded either model or claimed scoring/vision validity.

Physical0/1/3/4 originals and their verified handoff waiters remain alive as of
18:59:09 UTC; zero actual R179 loads or completed retained-sleep proofs yet. Four
clean-expiry controllers remain active and can rearm once for90 minutes only on
clean no-retirement expiry and exact current-owner/source revalidation. No live
learner is placed on2/5. No dead/retired life needs recovery at that observation.

Host remains `[REDACTED_HOST]`; hard wall remains2026-09-18 18:00 UTC/1789754400.
Original learner sources, saved states, runs, journals and guards are untouched.
