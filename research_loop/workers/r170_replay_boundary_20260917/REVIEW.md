# R170 independent operator review — 2026-09-17

## Verdict

**NOT READY for signal-bearing handoff: unresolved pause-recovery safety.**
No normal-path adapter or physical1 CLI-transition failure was reproduced in
the scoped CPU probes. This is not deployment approval, receiving-host
admission, a live process-identity observation, or evidence of delivered dose.
Main reports the operator remains undeployed. This reviewer performed no
remote actions, real lifecycle signals, GPU work, restarts, or parent changes.
Only this report and `test_operator_review.py` are reviewer-owned R170 files.

## Bounded repair list

1. **Blocking — operator death can strand the exact paused lifecycle.**
   `gpu/orch_r144_node3_target_handoff.py:623` retains the original handoff;
   its first pause is at line 677 and recovery is in the Python `finally` at
   line 727. SIGTERM/SIGHUP are handled, but SIGKILL, OOM kill, or abrupt
   interpreter death bypass that recovery. There is no independent death
   watcher. Death after a STOP can leave the native actor, timeout, or native
   supervisor stopped; normal exception-path tests cannot certify this case.

   Narrow recommendation: before the first STOP, require readiness from a
   detached operator-pidfd death watcher holding the three already-validated
   lifecycle pidfds. On operator death, attempt SIGCONT on only those exact
   handles. No discovery, conversation-parent targeting, TERM/KILL, restart,
   re-admission, or replay. Disarm only after confirmed recovery or target
   exits. Confirm that watcher launch failure prevents STOP, ordinary live
   operator waiting does not trigger recovery, and operator death at every
   pause/retirement prefix cannot leave a surviving target stopped.

   Do not copy an unrelated 30-second timeout watchdog unchanged: this
   lifecycle may legitimately wait up to 180 seconds for paused readout
   completion. A timeout CONT while the operator continues towards retirement
   introduces a race. Operator-death-only recovery is the smaller change.
   A watcher cannot resurrect actors already retired by TERM; partial
   retirement still needs a preserved failure receipt/manual disposition,
   never automatic replay or a claim of successful handoff.

2. **Recovery-path defect — one failed CONT skips remaining recovery.**
   Operator5 `BOUNDARY_API.py:414` catches only `ProcessLookupError`.
   A `PermissionError` or another non-ESRCH signal error aborts the remaining
   CONT attempts; the caller's `finally` then skips descriptor/lock cleanup
   and signal-handler restoration. The independent test reproduces this
   without real signals. Include per-handle best-effort CONT and unconditional
   resource cleanup in the same narrow recovery repair; preserve/report
   failures rather than calling failed recovery successful. This is not a
   demonstrated normal-path permission failure on the inventoried lane.

These are recovery changes, not requests to redesign admission, scientific
runtime, recipe, cadence, lease, or conversation-parent management. Any repair
changes the bound candidate and requires a new focused review/CPU receipt.

## Dispositions that do not block this lane

- **Omitted `contained` action — not a physical1 defect.** Original
  `contained_command` at `gpu/orch_r144_node3_target_handoff.py:201` reexecutes
  OPERATOR with `--action contained` only for physical0/2, both outside this
  adapter's admitted scope. Physical1 uses `gpu.orch_r133_node3_handoff
  contained-native`; that wrapper generates the timer/guard `native` command.
  Do not add other-lane CLI actions merely to silence this finding.
- **Operator4 versus operator5 API — resolved.** The two files are byte-for-byte
  identical, both SHA256 `f128becb34d95b6875e4283baa49b3504e2c6c589e67b93e858e07c98f593e60`.
  The review fixture now explicitly copies the operator5 file, matching both
  OPERATOR and FAMILY pins.
- **Guard-clone reference validation — acknowledged parity gap, not a
  reproduced valid-input handoff failure.** `OPERATOR.py:65` yields exactly
  `driver.patch_guard` bytes for valid bindings, including both key orders,
  but omits the driver's canonical-path/hash checks. Two strict expected
  failures demonstrate acceptance of a relative path and an invalid digest.
  They are not passes. The scoped artifact path still must pass bound metadata
  reads and actual receiving `driver._admit`; direct generic use of this
  helper is not approved. Fixing validation parity is a narrow optional repair,
  not justification to alter the preserved guard lifecycle.

## What the CPU review establishes

- Exact copied FAMILY functions retain shared private execution globals,
  defaults, closures, and critical code. Only `lane_scope`, `verify_source`,
  `old_modules`, `saved_evidence`, and `validate_new` are replaced/wrapped;
  the captured originals still use the private family namespace. Scope and
  staged-source root changes do not modify the original module on disk.
- Physical1/current source/current life/UUID only; reject other physicals,
  bool/float aliases, recovery/wall extension, unrelated recipe/lease changes,
  source-byte or pin-set drift, wrong row/dose, and non-immediate target cycle.
  The retained guard validator rejects extra unlisted Python source, which
  the adapter's listed-file loop alone does not census.
- Source closure, fresh receiving validation, and original identity checks
  precede lock/pidfd acquisition. Exact saved cycle/state hash/path must match
  selection before the original bundle verifier and before any pause. The
  lower saved-boundary/checkpoint/experiment/history verification is retained;
  CPU fixtures are not actual AdamW/RNG tensor restoration evidence.
- Valid guard patch AST is unchanged except for its single terminal native
  call. Original confinement/admission/startup binding remains, together with
  original HANDOFF_ONCE/DISPATCH_ONCE and refusal to readmit after possible
  dispatch. Receiving preflight calls `driver._admit`, not `driver.run`, in a
  fresh CUDA-hidden subprocess. No four-extra dose occurs during preflight.
- Earlier R168 driver/native reviews and their focused suites remain applicable
  to their unchanged pins: one private-native bridge, retained lower lifecycle,
  single-use root/cycle dose, and no retry after uncertain updates or commit.
  See `research_loop/workers/R168_TARGETED_DRIVER_REVIEW.md` and
  `research_loop/workers/R168_TARGETED_NATIVE_REVIEW.md` for those separate bounds.

## Actual subprocess CLI probes

The added probes run new local Python processes against exact copied entry
scripts, not just an inspected namespace. They establish successful parsing
and dispatch through:

```text
OPERATOR.py --action supervise --output ATTEMPT
  -> python -B -m gpu.orch_r133_node3_handoff contained-native --config GUARD
  -> timeout ... python -B -m gpu.orch_r125_continual_guard native --config GUARD
```

The physical1 payload is produced by the actual frozen `contained_command`,
creative containment builder, and original allocator wrapper. The next native
payload is captured from the actual creative `contained_native` body using an
inert Popen. Strict containment properties remain in the generated command.
`OPERATOR.py --action contained` really exits with argparse status 2, but is
not a reachable command on this scoped chain.

Safety/coverage limit: subprocesses substitute the local Python executable
and stop at the selected function's entry using a test-only hook. Native and
preservation imports are inert; external subprocesses, signals, sockets, and
NVIDIA device opens are denied inside these probes. No sudo, systemd service,
timeout process, GPU containment verification, model load, or live native
startup is executed. The supervisor command matches the original handoff's
spawn expression; the retiring handoff itself is not performed. Thus parser
success is not receiving-host startup/admission success.

## Timing and observation limits

The operator permits at most 600 seconds of active boundary acquisition,
further shortened by the retained lease margin. CPU preflights and the
subsequent original 1200-second monitor are separate. Neither bound shortens
the learner's baseline cadence (reported approximately two hours).

The extra dose belongs only to frozen `source_cycle + 1`, subject to valid
selection/GO admission. A missed source boundary refuses before STOP; expired
or consumed arms do not authorize catch-up. There is no credible wall-clock
ETA from these CPU tests or from an undeployed operator.

The inherited monitor can report `TARGET_POLICY_NEW_SLEEP_COMPLETE` from
baseline LOADED/R144 eligibility/next sleep completion with no R168 accounting;
an independent test demonstrates this. That status, or a monitor timeout,
does not establish four delivered extras. Require actual targeted accounting
and checkpoint/journal evidence before making that statement. Main's parallel
parent retelling is a different path, not a substitute for this dose.

## Bound sources and CPU receipt

Reviewed OPERATOR SHA256:
`e2c0307936d8be5cde38633464641e921761369bf5c2ca3f65f960f69dbdd69f`.

| Source | SHA256 |
| --- | --- |
| Frozen R144 family | `014e23e330db36f0ef6a8da23f75084a7685e7e0663a1e9540759dac7fc0da5c` |
| Operator5 boundary API | `f128becb34d95b6875e4283baa49b3504e2c6c589e67b93e858e07c98f593e60` |
| Local creative wrapper | `c249b3d8cd413267556cf200acfcaf9668f8c3096c705ea2adc40b0054b1b692` |
| Original guard | `4be0fd5ac06bf447e9ae425ad940efbd203a1d6c3cfb88ad8b4dec0db449bea3` |
| R168 driver | `43295e6b98ebb10c7e99247e8b26720948b25556d5da13e34759c1f2d0088351` |
| R168 native integration | `12e512ba08be73a1881bc75c52f60458163aa929c5b0bc682814c9c0bf93e304` |
| R168 arm | `4ff5a30e5602149bdde4d320c768fe23ef309070f88cff455e605080bf7c49b3` |

Pinned supported archived native remains
`cdb54252763472fd21ea12fd7694b208d968422c375dbf0647088cde736e6d48`.
These are local source evidence, not an independent deployed-source census.

Final combined run: **192 passed, 1 skipped, 2 xfailed, 105 subtests passed**
in 4.26 seconds, 2026-09-17 14:39:42–14:39:46 UTC. The independent sidecar alone
also ran successfully: **70 passed, 2 xfailed**. No expected failure is waived.

```bash
TMPDIR=/tmp CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH=/tmp/r136-pytest-support python3 -B -m pytest -p no:cacheprovider \
  research_loop/workers/r170_replay_boundary_20260917/test_operator_review.py \
  tests/test_orch_r144_node3_target_handoff.py \
  tests/test_orch_r142_allocator_boundary_rollout.py \
  tests/test_orch_r168_targeted_replay_driver.py \
  tests/test_orch_r168_targeted_replay_driver_review.py \
  tests/test_orch_r168_targeted_replay_native.py \
  tests/test_orch_r168_targeted_replay.py -q --tb=short -rs -rx \
  --junitxml=/tmp/r170-operator-final-review.ADbVxx/CPU.xml
```

`TMPDIR=/tmp` avoids the environment's symlinked default temporary directory,
which correctly fails canonical-confinement fixtures. Receipt directory:
`/tmp/r170-operator-final-review.ADbVxx`, containing source manifest, start/end
timestamps, CPU log, and JUnit XML. All recorded source hashes were verified
unchanged after the run, including Main's OPERATOR/ASSEMBLY/test_assembly;
hashing the latter two is not an independent assembly review.

- `CPU.log`: `8056d4ae5650a4fb5f77ee2daafa337f47986ab729bbb30f873944a0284fb8b8`
- `CPU.xml`: `dc723673fbd2d7f5e753955f64bc05c6b189ad9f96f452042ab999c2b0b0bc8b`
- Review tests: `4ca8e1f781031d07a3542188acb9513e19e52cdb563030240ac8014ed5149b75`

Receiving source custody, actual full receiving CPU startup/admission,
pidfd/permission/containment reality, and the pause-recovery repair remain
unproven by this report. Restored conversation parents remain untouched.
