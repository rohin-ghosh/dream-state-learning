# R153 priority — supersedes prior deployment readiness

September 17, 2026. Main is revising the R166 invitation to preserve the same
live object richly, including its correction and next actual move, rather than
only retelling the last mismatch.

The existing CPU.json and HANDOFF.md are historical evidence for the earlier
invitation, not deployment approval for the forthcoming candidate. Preserve
their bytes. Do not deploy or create a new staged closure bound to the old
invitation. No source staging or live action has been performed by this worker.

The helper and tests are implemented; the last completed suite was 218 tests
plus 256 subtests PASS. That result does not validate Main's forthcoming
invitation revision. No new candidate hash is asserted here.

Safe next steps, within the narrowed scope:

1. Keep existing children, parents and natives running. No retirement, restart,
   new child, GPU action, source hotpatch or GO.
2. Await Main's exact revised invitation/test candidate pins. Re-run the helper,
   invitation and related native/journal/containment CPU regressions against
   those bytes before generating a new candidate-specific CPU receipt.
3. Stage only a fresh isolated source tree for the same eligible C1–C5 roots;
   retain the old plan, birth, object/history/carry and optimizer/RNG state.
   Verify that the isolated source delta remains solely the approved pre-sleep
   invitation change plus its explicitly pinned helper dependencies.
4. Do not run `prepare` now: the present helper requires the old recorded owners
   absent. It does not support adopting an invitation in a running process at a
   future boundary, and a naturally reached sleep boundary alone does not meet
   that precondition. No currently authorized activation path is implemented.
   Return the staged candidate to Main; any actual next-boundary adoption must
   first have a separately specified, permitted mechanism. Do not retire an
   owner merely to satisfy this helper.

No retirement, activation supervisor or runtime-scope expansion is proposed.
This note supersedes earlier source-staging readiness for deployment while
preserving the prior code/test evidence unchanged.
