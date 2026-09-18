# Activation2 Main operational execution

2026-09-17T08:19:36Z. Main explicitly authorized one invitation-only execution
for C1/C2/C4/C5 against the four final activation2 READY hashes. C3 and targeted
replay excluded. This is operational executor authority, not new human ratification.

Exact GO objects and READY bindings: `ACTIVATION2_MAIN_GOS.jsonl`, SHA256
`9ad9f049b84d7491d5652e5ef76aa9d5a2e3b246ff90757820bf85a06d81db6e`.
Each remote GO is `/localhome/local-rohing/orch_r166_retelling_C<N>_20260917_activation2/MAIN_GO.json`.

| Life | GO SHA256 |
| --- | --- |
| C1 | d888f90d0930568d329dcd921282e08efa4f61ae9e19d067485b0b422d9fc37d |
| C2 | 2cee60076c481e1efa8b32aa59ec421c50b2492369315edee759cf20cc147723 |
| C4 | f95123a2cebc39b7adeda4aaf8b70e82fa39d3c418c26e9a21e1a1728436c4e2 |
| C5 | 246ed208da8c3761e5e829ba3467c30ea6120748b37fc3ca8eeda257fef970bb |

GO creation actual timestamp 1789633170.0598636–1789633170.0619352;
each expires exactly 1800 seconds later, before unchanged wall 1789776000.
All remote READY/helper/test/invitation hashes checked before GO creation.
Final helper ae9fec2a97cb59d1555dbf87519dffd19bfb7cf5cc3801e6ad975ecebb0e2a19;
tests 6bca4a95d0e4461b6fb0085c6554cedb974d7f3549f2166c7bcb3321a5c43f34;
89 CPU tests and 59 subtests passed. No source edits after freeze.

Dispatch uses exact successor source, CUDA hidden/offline CPU operator, original
strict scanner/device supervisor, create-only dispatch intent, detached process.
No retry after uncertain dispatch or termination; no parent signals. Actual
checkpoint, successor PID/LOADED, effective invitation, and adoption remain
distinct evidence milestones and are not established by GO creation.

## Actual execution failure — no retry

Dispatched once at Unix 1789633196.0361207–1789633196.0414164:
C1 CPU operator3899193, C2 3899194, C4 3899195, C5 3899196.
Dispatch receipt `ACTIVATION2_MAIN_DISPATCH.jsonl` SHA256
`0bbc9d4fd029e1aaa63fe3320d25f716b48056b0e8fa187897d5ba9900d43988`.

Read-only observation at Unix 1789633207.9643433–1789633207.9718864:
all four operators exited with FileNotFoundError for successor-local
`source/tests/test_orch_r166_corrected_retelling.py`. Failure is in
`execute -> activation_binding -> verify_request -> validate_cpu`, before
lock acquisition, pidfd creation, pause, checkpoint preparation or termination.
No successor native, LOADED, or effective-invitation receipt exists in this attempt.
Full tracebacks and original process identity metadata are preserved in
`ACTIVATION2_STATUS_FIRST.jsonl` SHA256
`ea9904149c11e6e0d7a1aa10026cb01a2fdfdf22e117fe78b87f0fb243fed7e9`.

Original native PID/start ticks remain exact and not stopped:
C1 2578597/14835459 (R), C2 2610332/14878521 (S),
C4 2619696/14891073 (R), C5 2578735/14835679 (R).
All original timer/supervisor identities also match and are sleeping, not stopped.
Parents were untouched. No invitation adoption or checkpoint handoff occurred.

Root cause: stage copies RELATIVE, TEST_RELATIVE and POLICY_RELATIVE but omits
POLICY_TEST_RELATIVE; validate_cpu requires that fourth file relative to the
executing module. Earlier preflight ran from the complete operator source,
so it failed to exercise the exact successor source import environment.
The prior readiness claim was therefore incomplete.

No retry or frozen-source repair was performed. Minimum next repair proposal:
include the exact pinned invitation test in new source inventory and its
predecessor-delta checks, test verification as a subprocess from that staged
successor source, then produce new candidates/readiness and request new Main GO.
Activation2 GOs, sources, dispatch intents and failure logs remain preserved.
