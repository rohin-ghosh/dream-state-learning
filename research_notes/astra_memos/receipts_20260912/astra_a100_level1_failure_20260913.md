# A100 Level1 attempt1 failure — bounded read-only handoff

**EDITSTOP. Infrastructure failures, not efficacy results.** Inspected September 13,
2026, **08:01:25–08:02:11 UTC**, through `gpu/a100_ssh.sh`, UID1395. Only named
attempt receipts/logs, executable paths, and receipt-bound process IDs inspected;
no foreign-process scan, model load, GPU query/work, executable version run,
installation, edit, launch, signal, reboot, root collection, or archive occurred.
This local report is the only new file. Main's node1 fresh-attempt2 placement is
independent; no A100/A40 hardware-parity claim.

## Exact reconciliation

**6 prepared roots; 5 launched controllers; 5 OFF stages started and failed;
5 matching OFF release receipts; 0 cleanup-failure receipts; 0 fit/post stages;
0 request/response files; 0 closed OFF captures; 0 completed roots.** These are
missing readouts, not zero scientific scores. Batch25933 has `started.json` but
no `finished.json`.

| Cell | GPU | Controller / OFF worker | Disposition |
|---|---:|---|---|
| repetition_seed0 | 0 | 26457 / 26845 | OFF failure; release recorded |
| repetition_seed1 | 1 | 26912 / 27524 | OFF failure; release recorded |
| repetition_seed2 | 2 | 27570 / 27963 | OFF failure; release recorded |
| meta_reflection_seed0 | 3 | 28539 / 28954 | OFF failure; release recorded |
| meta_reflection_seed1 | 4 | 29917 / 30911 | OFF failure; release recorded |
| meta_reflection_seed2 | 5 | none / none | Prepared; reservation check stopped launch |

All five OFF stderr logs contain FlashInfer JIT `run_ninja` followed by
`FileNotFoundError: [Errno 2] No such file or directory: 'ninja'`. Stage failure
receipts report engine-core initialization failure; controller failures report
`native worker failed: OFF`. Each release PID/PGID matches its started/launch
receipts. All five controller PIDs, their five worker PIDs, and batch25933 were
absent at inspection. Release is the controller's recorded cleanup/vacancy
check, **not a fresh all-process GPU clearance**.

For meta_reflection_seed2, preparation and plan exist, but precheck, launch,
controller-start and run-stage receipts do not. Its batch failure records
`reservations=[]`, unresolved PIDs26457/26912 (UID1395, PPID25933), empty-cmdline
SHA256, `pid=null`, `controller_may_be_running=false`. This is consistent with
terminated/unreaped children blocking the next same-user reservation scan;
the historic receipt did not record process state, so **Z state is not proven**.

## Executable/toolchain diagnosis

- `~/v2/venv/bin/ninja` **exists and is executable**, 370448 bytes;
  `/usr/bin/ninja` and `/usr/local/bin/ninja` are absent. No reinstall is
  justified by this evidence alone.
- `nvcc` **exists and is executable** at `/usr/local/cuda/bin/nvcc`, resolving
  to `/usr/local/cuda-13.0/bin/nvcc` (30153384 bytes). The CUDA13 alias also
  resolves there. No venv/bin or /usr/bin nvcc exists.
- **Recorded parent PATH/CUDA_HOME could not be recovered:** the launcher and
  batch receipts do not record them; none occurs anywhere in the six plans.
  The batch/controllers have exited, so their `/proc` environments are gone.
  Do not substitute a fresh shell environment for historical evidence.
- The fresh wrapper environment's sanitized PATH directory list is
  `/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/snap/bin`.
  It omits both `~/v2/venv/bin` and `/usr/local/cuda/bin`; `CUDA_HOME` and
  `CUDA_PATH` are unset. Lookup finds neither ninja nor nvcc; gcc/g++/c++ resolve
  under `/usr/bin`. This supports a **PATH/tool-discovery failure**, not a
  missing-installed-ninja conclusion or proof of CUDA/compiler compatibility.
- The inspected launcher/worker source inherits `os.environ` while replacing
  `CUDA_VISIBLE_DEVICES`; an absolute venv Python path does not itself establish
  executable search paths. Existing package/environment checks did not bind
  these tool-search variables.

## Smallest proposed repair — Main only, not applied

1. For a **fresh** A100 attempt, explicitly prepend the existing venv/bin and
   selected CUDA toolkit bin to the parent PATH; set CUDA_HOME to that same
   toolkit root if the JIT toolchain needs it. Record only sanitized tool paths
   and executable identities. Validate resolution in the actual inherited
   launch environment, then let Main perform bounded native preparation;
   file presence alone does not establish successful JIT compilation.
2. Retain and poll/reap **only the batch's own Popen child handles** before
   subsequent reservation scans. Do not broaden denied-environment exceptions
   to arbitrary empty-cmdline, zombie, or Python processes. Historical state
   remains missing; preserve the existing conservative guard and failure roots.

Neither proposal alters the recipe, model, targets, or outcome interpretation.
No repair or retry was performed; leave the five failed roots and sixth
prepared-only root untouched for Main's later evidence archiving.

## Exact evidence locations and pins

A100 batch base:
`/tmp/astra_level1_second_roster_20260913_attempt1_clockfix/batch_a100/`.
Each table cell has `<cell>/launched.json` when launched and its controller log.
Roots are `~/astra_diagnostics/level1_<cell>_20260913_attempt1/`; inspect
`controller_failure.json` and `run/OFF/{launch,started,failure,released}.json`.
No request/response payloads or failed roots were copied.

| Cell | SHA256 of root `run/OFF/stderr.log` |
|---|---|
| repetition_seed0 | `d0d019acc04d505a7ba8a719cd398588bb9349d8819e2cabf3bad2b9ab7bcd54` |
| repetition_seed1 | `9083b9f0175c0217ef464df05f8e3820553e3d4cefe28716152bd1780c84ac6f` |
| repetition_seed2 | `ccfde363cd033f66374873fd54752840b0c9ca482cab836fd26564a572f7aeee` |
| meta_reflection_seed0 | `83ac616bd8e14138d8e09b60422c39dab468dedab13369b795c8c3c27e7ff687` |
| meta_reflection_seed1 | `1a2aec2baac121545049cb9b96960139211e9926edb7b6c9e21ea9e75a81703a` |

Batch `meta_reflection_seed2/failure.json` SHA256:
`43a232f2d13588d44769da8acdc44538a4a938c67d0a7db6e62f093351681977`.
Batch `started.json` SHA256:
`593ec38e7c0b7497e5c15cff41284a4d9d6a5f0ec266292c9fce6ad03552820e`.
Launch-wrapper `/tmp/astra_level1_second_batch_a100_20260913_attempt1.launch/stdout.log`
SHA256: `14098e2f592e9310ffdf2663bf174239999ada548bdf5e3676832335be030868`.

Checks: six roster entries reconciled; five launch/start/failure/release chains;
five matching worker PID/PGID release bindings; six absent completion receipts;
five identical missing-ninja root causes. No native readiness certification.

EDITSTOP.
