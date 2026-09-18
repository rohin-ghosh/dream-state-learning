# Independent R170 recovery V2 review — 2026-09-17

## Bounded verdict

**APPROVE the reviewed V2 recovery repair at CPU/source level for the single
physical1 boundary. The two V1 pause-recovery blockers are addressed.**
No remaining signal-safety or normal-path handoff blocker was reproduced in
this bounded review. Proceeding to receiving checks is supported; these local
tests are not receiving-host admission, authorization to skip those checks,
GPU/model validation, or proof of delivered replay. One pre-STOP descriptor
leak remains, classified below rather than hidden by expected failures.

**Current integration gate remains unresolved, independently of this recovery
approval.** Main reports that actual scaffold CPU validation failed before
creating physical1/source, with zero signals: old evidence bound plain-context
`dcfd...`, whereas resident source is `b385...`, and the old evidence also
listed unused R145 suffix files. This reviewer has not inspected that baseline
or the separate R173 receiving proof; they are outside this assignment. Local
recovery passes do not resolve that mismatch. There is no R170 signal GO or
delivered-dose claim in this review.

This verdict applies only to the exact sources below and the inherited
one-shot CLI. It is not approval of a generic Recovery service. Only
`REVIEW_V2.md` and `test_recovery_review.py` were added/edited by this reviewer.
V1 review/tests, Main's two runtime files, FAMILY/API, and learning source stayed
unchanged. Main expanded its own tests from 15 to 17 during review; both test
revisions have separate receipts below. No remote, provider, GPU, existing workload, or parent action was
performed. Real signals in tests targeted only newly created owned CPU
sleepers and their test operator, never an inventoried learner.

## Remaining defect and narrow repair

**Nonblocking in the admitted one-shot CLI: partial pipe setup leaks FDs.**
`RECOVERY.py:102` opens the operator pidfd, then two pipes at lines 103–104;
the cleanup `try` begins only at line 105. A first `pipe2` failure leaks the
operator pidfd. A second failure leaks that pidfd and both readiness-pipe
ends. The caller's normal cleanup cannot close these unrecorded locals.
Two strict xfails in `test_recovery_review.py:279` reproduce the omissions.

Both failures occur before watcher launch/readiness and before any STOP.
The original error propagates through the canonical CLI, whose exit releases
the remaining local FDs. The original learner is not paused or retired, no
replay is dispatched, and the path does not retry. This is therefore not a
replacement for the old stranded-learner blocker. It is a real resource-cleanup
defect, and a `RECOVERED_AND_CLEANED` receipt must not be interpreted as proof
that every setup FD was explicitly closed in this case.

Minimal recommended repair: initialize setup descriptors to `None` and move
the `try/finally` before the first acquisition, closing each acquired setup
handle on every exit. No lifecycle/learning rewrite is needed. A repair would
change RECOVERY and its V2 pin, requiring a newly bound focused receipt; this
report does not approve those future bytes. The two xfails are not passes.

## V1 blocker dispositions

1. **Operator-death recovery — PASS within the stated fault model.**
   The helper verifies the exact three already-inventoried process identities,
   inherits those lifecycle pidfds plus an operator pidfd, and starts its
   watcher in a separate session with a minimal environment. Readiness is
   required before STOP, and watcher liveness is checked before each pause.
   The watcher waits on operator death, not a restart/resume deadline; control
   EOF with the operator alive does not trigger recovery. On death it attempts
   only SIGCONT for the three inherited handles, tolerating exited targets and
   continuing past per-handle OSError. It performs no discovery, TERM/KILL,
   restart, sample, admission, or replay.
2. **Interrupted CONT/cleanup — PASS for the reviewed error cases.**
   A failed CONT no longer skips subsequent roles. Cleanup independently
   attempts the remaining resumes, every supplied pidfd, lock close, and
   signal-handler restoration. Errors remain recorded and cause failure,
   rather than being cleared into a success or retry. Watcher errors/nonzero
   exit also prevent a clean-success return. Failed readiness, malformed/EOF
   acknowledgment, watcher launch failure, or a watcher found dead before the
   next pause all refuse that STOP; prior pauses are recovered in cleanup.

The death watcher cannot resurrect a target already retired, repair lost
signal permission, or survive destruction of the watcher/node itself. Session
detachment is not independent cgroup survival. This is not approval against
simultaneous operator-and-watcher destruction or a shared cgroup teardown.

## Edge-case evidence

- The author's real CPU matrix passes. Its retirement prefixes use
  supervisor-first order; the actual lower handoff retires actor, timer,
  supervisor. Independent real CPU tests add the actual actor-first one-,
  two-, and three-retired prefixes. All surviving targets resume after the
  owned operator's SIGKILL; retired targets remain exited, with no restart.
- A real watcher receiving `D` while targets remain stopped refuses to disarm.
  After control EOF it stays alive without CONT while the operator lives, then
  performs death recovery. Normal author disarm confirms all targets running
  or exited and produces a zero-signal disarm receipt. A disarm check that
  cannot establish safety can conservatively fail/wait for operator death;
  it does not silently resume while the operator continues retirement.
- Poisoning the readiness receipt writer prevents STOP even after the watcher
  becomes ready; cleanup still closes handles and disarms. Poisoning the final
  cleanup receipt fails only after cleanup attempts. Such I/O errors may mask
  the original diagnostic or prevent a durable failure receipt; they do not
  create successful handoff/replay permission.
- Real watcher process inspection confirms a separate session and only PATH,
  PYTHONDONTWRITEBYTECODE, and empty CUDA_VISIBLE_DEVICES in the launch
  environment. Provider credentials are not forwarded. Readiness metadata
  carries the already-staged process identity records, not a new environment
  or provider census.

## Source, namespace, CLI and guard

- Independent code-object comparison proves exactly the expected handoff AST
  delta: pause call, mismatch-resume call, and outer-finally cleanup. Every
  other family function matches the V1 private-family version, including
  defaults and private globals. All original stage/source/identity/pidfd/
  shared-lock/readout/retirement/admission/monitor code is retained.
- The V2 adapter executes pinned V1 in the V2 namespace. The family and its
  bootstrap commands retain V2 `__file__`, while Recovery.arm points to the
  copied sibling RECOVERY.py, not a repository fallback. Wrong V1, RECOVERY,
  FAMILY, or API bytes refuse before bootstrap action. A fresh local Python
  subprocess reaches V2's inherited `supervise` entry with its recovery object
  present. The probe stops before any real lifecycle action.
- Physical1 still uses original creative `contained-native`, then guard
  `native`; no new need for OPERATOR `--action contained` exists. The physical1
  scope function and current source/life/UUID constants are retained from V1.
  Old V1-bound CPU/STAGED metadata is not interchangeable with V2: receiving
  provenance and successor/validation argv must bind the V2 path and digest.
- Guard reference parity is repaired for the reviewed reference contract:
  relative, traversal, symlink alias, malformed digest/type, and extra fields
  refuse. Valid patches equal the reviewed driver's bytes, and AST equality
  after restoring the one terminal call proves all other guard checks remain.
  The two frozen V1 guard xfails in the combined suite remain historical V1
  findings, not unfixed V2 guard findings.

Source approval assumes a fresh immutable operator package. File-hash checks
before importlib execution do not constitute atomic custody against concurrent
replacement or stale bytecode; do not substitute a mutable/cache-contaminated
package. Main's concurrently prepared scaffold, actual receiving paths and
package permissions, full receiving CPU checks, source closure, live identity,
pidfd permissions, lease/admission, and containment remain receiving evidence
obligations. This review neither reads nor approves a future scaffold artifact.

## Timing and claim boundary

Unchanged: at most 600 seconds of active boundary acquisition, subject to the
original lease margin; the original paused readout may wait up to 180 seconds;
the subsequent baseline monitor is 1200 seconds. The watcher adds no timeout
resume, cadence change, or learner signal outside death recovery.

No launch/dose wall-clock ETA follows from these tests. Four extras still
belong only to frozen source_cycle + 1 under the original arm/GO conditions.
Missed boundaries/expired or consumed arms do not authorize catch-up. The
baseline monitor is not R168 dose accounting. Actual targeted updates and
checkpoint/journal evidence remain necessary for a delivered-dose claim;
parent retelling remains a separate path.

## Bound pins and receipts

| File | SHA256 |
| --- | --- |
| OPERATOR_RECOVERY_V2.py | `1a9b78c6044014ad1b69929e9a65cd34bbdc79130c77861a4152491f072f0dd4` |
| RECOVERY.py | `4864af9e8e21aa3fa5fc0b141bddbb09900908aabf52d8141a730375b3c7553a` |
| Current test_recovery.py (17 tests) | `06748e9c1bb909f2b42082ac2b1f92e241d6ed49705df9374b27492739e70b11` |
| Frozen OPERATOR.py | `e2c0307936d8be5cde38633464641e921761369bf5c2ca3f65f960f69dbdd69f` |
| Frozen FAMILY source | `014e23e330db36f0ef6a8da23f75084a7685e7e0663a1e9540759dac7fc0da5c` |
| Frozen operator5 API | `f128becb34d95b6875e4283baa49b3504e2c6c589e67b93e858e07c98f593e60` |
| test_recovery_review.py | `56d9fb2316c14e1fb8e6e3e4351c1a863fb3a3871ba99c9f5832764bac9811ce` |

Final V2-focused run: **44 passed, 2 xfailed** (27 independent passes plus the
17 author tests, including the added full reverse-AST comparison and
stopped-target disarm refusal). Receipt `/tmp/r170-recovery-v2-final.uyezUF`,
2026-09-17 15:03:36–15:03:40 UTC; all its source hashes verified unchanged
after the run. It runs the two V2 test files only, with the same CPU environment
and pytest flags shown below.

- Final focused CPU.log: `b78ef0a25f5f519d48571926c1e48c84f8d8f12c72c533c530d5343d1a448759`
- Final focused CPU.xml: `0413a9a00ac254c5f0557c4c583bc5e38cb23eadd25bdbe3bfd156cde7a9bd6f`

Earlier V2-focused run: **42 passed, 2 xfailed**, with the author's 15-test
revision `d149847f1cd886b4c24e417390fe657929d31d9a01be445e14f018c8c81cae37`.
Earlier combined unchanged-family/driver/native regression run:
**234 passed, 1 skipped, 4 xfailed, 105 subtests passed** in 7.46 seconds.
The skip is the unavailable actual Torch CPU dependency. Two xfails are the
V2 pre-STOP FD leak; two are the deliberately frozen V1 reference-validation
findings. Neither group is silently counted as success.

Earlier combined receipt: `/tmp/r170-recovery-v2-review.tCIaAC`,
2026-09-17 15:00:03–15:00:11 UTC. All manifest sources, including the unchanged
V1 review/tests and the then-current author files, verified unchanged immediately
after that run. A later check correctly detected Main's test-file expansion;
runtime pins did not change. The final focused receipt binds the expanded tests.

```bash
TMPDIR=/tmp CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH=/tmp/r136-pytest-support python3 -B -m pytest -p no:cacheprovider \
  research_loop/workers/r170_replay_boundary_20260917/test_recovery_review.py \
  research_loop/workers/r170_replay_boundary_20260917/test_recovery.py \
  research_loop/workers/r170_replay_boundary_20260917/test_operator_review.py \
  tests/test_orch_r144_node3_target_handoff.py \
  tests/test_orch_r142_allocator_boundary_rollout.py \
  tests/test_orch_r168_targeted_replay_driver.py \
  tests/test_orch_r168_targeted_replay_driver_review.py \
  tests/test_orch_r168_targeted_replay_native.py \
  tests/test_orch_r168_targeted_replay.py -q --tb=short -rs -rx \
  --junitxml=/tmp/r170-recovery-v2-review.tCIaAC/CPU.xml
```

- CPU.log: `92e400b11f0d7e0cbc1e41c7e924300b084f3b551d906f4c21917b1db741ab8c`
- CPU.xml: `1e8f908a5abfc4915d2a11eb6fa1cbf7f22dba803884da4e199cdb04798bddc8`

No scientific claim, replay dispatch, or restored-parent change accompanies
this CPU/source approval.
