# Route READY V2_R1 — September 15, 2026, 11:58 UTC

**Main should bind the two `SHARED_CLIENT_READY_V2_R1.json` files.** Exact paths
and SHA256 references are in `SHARED_READY_V2_R1_1158.json` in this directory.
Both are actual node-local files, not planned paths. V1 remains byte-identical.
The first V2 receipts also remain preserved: read-back caught a wrong closure
path paired with the correct manifest hash. That metadata bug is fixed, directly
regression-tested, and re-tested in the distinct frozen `v2r1` source. Do not bind
the first V2 receipts.

## Native evidence and executable

Source: `/localhome/local-rohing/orch_r111_route_shared_source_20260915_v2r1`.
Module: `gpu.orch_r111_route_pair_shared`.

`CPU_SHARED_V2.json` binds all **960 Python files**, the shared entrypoint, the
boundary helper, readiness publisher, and the test execution. Native pytest
reports **164 passed +42 subtests passed, zero failed/skipped**. The XML counts
206 cases; that is not 206 separate top-level tests. Actual tiny Qwen/PEFT rank8,
AdamW/RNG restoration, generation response shape, same-cursor empty START,
boundary pidfds/flock, shared capture/barrier, and exclusion tests ran with CUDA
hidden. The executable's actual `--help` completed successfully.

The validator is `gpu/orch_r111_route_shared_freeze.py`. It refuses skipped or
failed native tests and rejects any changed/added/deleted Python source after
freezing. READY publication validates the entire closure again. Filesystem
immutability is hash-enforced, not an operating-system write-protection claim.

F1 and A1 each retain their 16 TRAIN and 16 excluded IDs, exact original bounds,
and 120-second parent waits. F1's cycle4 candidate currently records 744 optimizer
steps, 55,114 child tokens, 13,580 anchor tokens, and 42 historical training rows.
It is only a candidate: Main must refresh `adoption_inputs` at actual release.
Do not select it as a rollback if the live life advances.

## Original-loop handoff remains unarmed

The prepared original-actor requests remain unchanged and expire at **12:45:23
UTC on September 15, 2026**. There is no AUTH or ARMED file created by this worker.
The controller source and commands have not changed since
`R118_BOUNDARY_COMMANDS.md`. They wait for a complete cycle plus readouts, acquire
the existing reservation lock, reject any raced next-cycle work, preserve the
latest checkpoint/optimizer/carry/ledger, retire supervisor before actor, and
emit exact release references. They do not initialize CONFIG or start a successor.

Only after Main has coordinated all eight runnable clients, create each
branch-specific AUTH.json as documented, bound to that branch's request hash.
Then these are the exact commands, run independently/concurrently:

```bash
bash gpu/ovx3_ssh.sh 'env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 /localhome/local-rohing/v2/venv/bin/python -B /localhome/local-rohing/orch_r111_boundary_candidate_20260915_v2/gpu/orch_r111_route_boundary.py execute --request /localhome/local-rohing/orch_r111_boundary_candidate_20260915_v2/readiness/F1/REQUEST.json --authorization /localhome/local-rohing/orch_r111_boundary_candidate_20260915_v2/readiness/F1/AUTH.json'
```

```bash
bash gpu/ovx3_ssh.sh 'env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 /localhome/local-rohing/v2/venv/bin/python -B /localhome/local-rohing/orch_r111_boundary_candidate_20260915_v2/gpu/orch_r111_route_boundary.py execute --request /localhome/local-rohing/orch_r111_boundary_candidate_20260915_v2/readiness/A1/REQUEST.json --authorization /localhome/local-rohing/orch_r111_boundary_candidate_20260915_v2/readiness/A1/AUTH.json'
```

They are bounded commands, not persistent background polling already launched.
Re-prepare in new directories if identity changes or the requests expire. Any
guard failure before supervisor termination resumes owned stopped processes;
an error after irreversible termination is explicitly marked for owned recovery.
Never signal foreign processes, and never create a fake TERMINAL to suppress
supervisor recovery. CANCEL or normal SIGTERM cancels the controller safely;
do not abruptly SIGKILL it.

## Main's adoption integration

Keep `shared_learner` binding fields `branch`, `root`, `config_sha256`,
`adoption_path`, and `adoption_sha256`. The proposed ADOPTION fields
`checkpoint`, `prior_metrics`, `initial_history`, `source_receipts`, and
`branch_bounds` are compatible with the tested route client. Extra provenance
fields are not prohibited. F1 alone restores the selected optimizer/RNG; A1
loads the common adapter without an optimizer.

When preparing the new route PLAN after release, additionally bind the actual
certificate at top level:

```json
{
  "route_boundary_release": {
    "path": "/absolute/branch/handoff/RELEASED.json",
    "sha256": "ACTUAL_RELEASED_FILE_SHA256"
  }
}
```

This is necessary if the old loop emitted an empty successor START before its
first reservation blocked. V2_R1 preserves that file and resumes the same cycle
and task IDs, writing a separate RESUMED_START receipt. It never silently skips
that unconsumed pair or resets charges. Bind the complete new runtime source
closure, preserve old plan/source bytes in versioned history, and use the
existing fresh strict privileged admission path before a new GPU process.

CONFIG, ADOPTION, all-eight coordination, and Git remain Main-owned. No F1 wait
change, GPU stop, shared initialization, or scientific inference occurred here.
