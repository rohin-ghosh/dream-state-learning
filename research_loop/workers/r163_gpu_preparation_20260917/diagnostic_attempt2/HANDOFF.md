# R163 diagnostic attempt2 — control2 CPU-ready, NO GO

September 17, 2026, 07:30 UTC. Only this new preparation tree and the new remote
root were written. Old attempt1, candidate3 failure, GOs, results, learners,
services and physical6 were untouched. No model construction, CUDA allocation,
GPU dispatch, reservation or signals occurred. This is disposable numerical
diagnostic preparation, not scientific fit or promotion.

## Current exact pins

Remote root: `/localhome/local-rohing/orch_r163_numerical_diagnostic_20260917_attempt2`.
Use **control2 only**. Original `control/` remains preserved with its 08:15 wall.
Control2 prospectively tightens the wall to **08:00 UTC, 1789632000**;
earliest dispatch **07:30 UTC, 1789630200**, maximum runtime 1800 seconds.
No extra wait is necessary now. Runtime is the remaining integer seconds to
the bound wall; an expired window refuses, without retry.

All paths below are under remote `control2/`, with byte-exact local copies in
`received/control2/`:

| File | SHA256 |
| --- | --- |
| FINAL_CPU_RECEIPT.json | bd92196177edce2900ca62cd55aef7e88f0fe8af49cd84d01de9c0d666625359 |
| PREPARED_EXECUTION.json | 6a7a66e8f8e7537a53d48ff291704b1298cd8d548d12deb458d7604feb2875dc |
| PLAN.json | 5db8da2aec53bf269d00a4d4dcedf0438eed2422d8137a50587562d18435a805 |
| GUARD.json | 0b67718bdfce0b6a0ed457752a4ecd15a6f2628130e108658efb80fc88e85009 |
| SOURCE_PINS.json | c2ff1378082b72242021d024508657e6343395ac43c07f14cf2c2553f68adde4 |
| admitted_probe.py | 696e3ce336a62dbf604eda1ebe5a870582cd612121260fc7bbd7e9388259e1eb |
| RECEIVING_CPU_TESTS_with_support.log | a1cccb87d8267c8731dad66268997fde10c2f9a075f43385e671b6b05dfd4ab8 |

The 2158-file manifest binds 2157 independent copied source files plus the
version-specific external admission operator. It derives from the prior
manifest SHA71ea6c8b9a878f81e753e09869122ca60eb493b1e3f7c48cc4de18aa957718e9;
every predecessor entry was checked before copying. Only two selected-source
files differ from that selected candidate3 closure:

- Probe `gpu/orch_r163_executor_probe.py`: b8ab9d80cd415de914116000d71c513001bec11a1fc62ae26bc064ada3b00f9e.
- Test `tests/test_orch_r163_executor_probe.py`: 43c1d340941611c9fafbd290a3b2c2131f7163740a77c56eaabd1211aa8ed90b.

Unchanged executor b033fbe4f1e8db5fa071e6c47678706f6e2b054d54a505947d8e4161075bea15;
driver 01c1ab05546a5c808aa140ac4e53c53ca0c3d3f96ce776e49581ec8d037fbc3f;
standalone guard 4be0fd5ac06bf447e9ae425ad940efbd203a1d6c3cfb88ad8b4dec0db449bea3.
Original source manifest and all other candidate5 files are preserved.
Control2 changes only receiving control paths and prospective time bindings,
not diagnostic logic, tolerances, native code, guard or physical admission.

## CPU and hardware evidence

- Control2 receiving **24 tests + 12 subtests PASS, 7.59s**: 11 actual-Torch
  probe cases, 6 driver cases, 7 external admission cases. Exact command is the
  recorded preparation invocation; tests are `control2/test_admitted_probe.py`,
  `selected_source/tests/test_orch_r163_probe_driver.py`, and
  `selected_source/tests/test_orch_r163_executor_probe.py`.
- Actual selected imports, entire source manifest and native plan validation,
  standalone guard validation, strict physical5 containment command construction
  PASS. No containment command or scanner was executed during preparation.
- Upstream CPU_attempt5 SHA1305259144365da616219077aeed6c2013589b141ab76f80f4a7ecb80288db9d
  is preserved. Galileo diagnostic-only readiness PASS reviewed at report line394;
  no real7B cause, numerical pass or GPU GO is inferred.
- Receiving venv initially lacked pytest; preserved failure log. An exact local
  pytest-support archive was copied under the new root only, without installation.
  Subsequent CPU runs use that test-only path, not the prospective GPU runtime.
- Reverified hostname `[REDACTED_HOST]`, UID/GID2524, physical5 NVIDIA A40,
  UUID `GPU-bc211959-642d-664b-3581-42a0dbe434e9`, device major195/minor5,
  46068 MiB total / 1 MiB used / 0% utilization at preparation observation.
  This snapshot is NOT admission: the original privileged full scanner must
  still return clear with zero blocking reasons at dispatch.
- Exact existing lease receipt SHA919e9fb3f9cfd6cadb57af90844319e50eb114068eb52cd75aa3ab715f9c3770:
  runtime lease ceiling September18 00:00 UTC, existing hardwall September17
  18:00 UTC. Control2 ends ten hours before that stricter hardwall. No lease
  extension; provider booking independently unverified.
- Rehashed 11,516,280 bytes of local model metadata against original preparation
  pins and checked anchor manifest only. No base weights, optimizer/checkpoint
  files, actual anchor rows or held data were opened/copied. Source closure is
  approximately28.4MB. Preparation bound remains 1GiB; no ongoing reads/polls.
  No claim of kernel-wide dependency/page-cache I/O measurement is made.

## Exact minimal GO schema and operator proposal — Main only

No GO file was created. Main supplies JSON with exactly these required fields:

```json
{
  "schema": "R163_NODE3_NUMERICAL_GO_V1",
  "issuer": "Main",
  "decision": "GO",
  "not_before_unix": 1789630200,
  "expires_unix": 1789632000,
  "binding": "COPY OBJECT VERBATIM FROM control2/PREPARED_EXECUTION.json required_GO_binding"
}
```

The placeholder must be replaced with the full JSON object, not a string.
GO must be independently authorized and pinned by Main. After exact verification
and new GO only, Main's detached dispatch would invoke through `gpu/ovx2_ssh.sh`:

```bash
env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
  /localhome/local-rohing/v2/venv/bin/python -B \
  /localhome/local-rohing/orch_r163_numerical_diagnostic_20260917_attempt2/control2/admitted_probe.py \
  supervise --main-go "$EXACT_MAIN_GO_PATH" --main-go-sha256 "$EXACT_MAIN_GO_SHA256"
```

Preserve the original dispatch requirement: initiating SSH shell/parent gone,
then five seconds before scanner entry. No dispatch occurred here. The wrapper
takes the shared physical5 lock, creates new-root `attempt1/` exactly once,
runs the unchanged full privileged scanner, and requires the unchanged strict
physical5 systemd/device checks before driver entry. Inner `attempt1/` is merely
the one-shot directory inside this NEW attempt2 root, never the old attempt1.
Any refusal/failure is preserved with no automatic retry. The plan's new
`validation_run1/` and dispatch directory were both absent on final CPU check.
