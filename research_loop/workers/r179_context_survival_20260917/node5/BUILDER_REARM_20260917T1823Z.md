# [Builder] NODE5 no-signal waiter rearm — 2026-09-17 18:23 UTC

Non-material lifecycle rearm within the unchanged R179 saved-boundary scope.
Only expired CPU waiters are superseded; no consumed attempt is replayed.
The original native sources, walls, confinement and invitations remain bound.
Fresh waiters may wait at most 7200 seconds, additionally clipped by the
unchanged model wall and the operator's existing safety margin. This is not a
lease extension or a GPU/model launch receipt.

Exact Main scope SHA256:
`85441db890036947f6bc242e66ef15db750a683d73fe02d06778ebe996d4fb54`.
Exact policy SHA256:
`b36949c2d93662b876b6519eee9dddba0e5af94a294e1f570f37685cd9604a2b`.
Unchanged rollout operator SHA256:
`e59649d3fd1fde7514f75e7af9d557d6f7f1ecee504403d47a610ccac5405b80`.

51 local targeted CPU tests PASS, including saved-state restoration,
controller transfer, observer attribution and C4 typed readmission regressions.
Each fresh attempt independently passed receiving operator tests, actual-source
CPU restoration/provenance and a strict CPU-only device service. The device
proofs report no Torch import and no model load. Existing GPU device admission
and exact saved-boundary retirement remain mandatory before a successor.

| Lane | Expired attempt | Fresh attempt | READY SHA256 | DEVICE_CPU SHA256 |
| --- | --- | --- | --- | --- |
| pilot | 4 | 5 | 8fd597fc355d7c1fc549ebee90abbad8faefb7805578930c1c3eb447b0a061f5 | c5262238ad03e38808732fe59cc3a20f87cc14d039c4d344add65bb8fed4d068 |
| run1 | 3 | 4 | 5f39d20756b73b286186bce43394353a17f189d641d5af2940ce39c8d297dd1f | 85b5cc862abd8bddab0fdbb398c9f3436caa49470e09267bf4ce1685842f4ce0 |
| repo_reader | 2 | 3 | 935b6e73bf803f8c2cd6a23648c32d14cbac529167c53f91b2da3e8ce900b930 | db58a5b0be4052c0ca1132e5a5934e16228ca27e71dbbbd0c8c4ec310082fb23 |

Before each fresh start, verify the predecessor's terminal timeout, exact old
operator absence, absence of termination/retirement/LAUNCH receipts and the
fresh READY/device pins. Retain all predecessor evidence unchanged. The
repo_reader uses its original recovered-root bind mount; no console turn is
sent. C1/C4 recoveries and C2/C5 controller operators are not restarted here.

Local prior-state evidence: `ROLLOUT_METADATA_1789669289064122920.json`.
Receiving roots: `/localhome/local-rohing/orch_r179_context_<lane>_20260917_attempt<fresh>`.
Fresh actual start receipts are recorded separately after execution.
