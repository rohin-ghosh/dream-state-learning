# Scoped PCFL C0 attempt 2: failed-finalization terminal audit

**Date:** 2026-09-13 UTC  
**Audit mode:** independent receipt review only; no model, tokenizer, GPU,
scorer, test, fit, update, process, or source execution  
**Maximum label:**

> **UNUSABLE EXECUTION — ENGINEERING-ONLY CAPTURE (FINALIZATION FAILED)**

## Bottom line

The scientific payload completed before the lifecycle failure. The frozen
report covers all 800 tasks and 800 actor calls, the worker exited with integer
return code zero, and the original outer captured a complete hash inventory.
Those bytes remain useful for diagnosing the PCFL interface and for testing
offline audit tooling.

They are not a usable exploratory result. The only authorized finalization
attempt wrote its once-only claim and then failed while checking release. The
required release attestation, release receipt, final result, and collection do
not exist. Later observations that the process group and GPU were empty cannot
be substituted for the failed observation or used to retry finalization.

This conclusion follows the prospective terminal checklist written while the
worker was live: any lifecycle or finalization failure makes the attempt
`UNUSABLE EXECUTION`. It does not depend on whether the model passed or failed
the registered performance panels.

## Evidence that completed cleanly

The preserved builder entries are commits `2ec3b8e7` and `3df30399`. The
49,879,040-byte evidence capsule is preserved at builder hash
`44473352a9220e4e92475d16194a87f1fc89bd3d6021bbe6caa97a74a2ca20cf`.
Read-only node-2 inspection agrees with those committed receipts:

- Report file SHA-256:
  `c8fac984db75fd123cf5264756572da465baaffeee0fcbe186f849dddd319f2d`.
- Sealed report SHA-256:
  `ba9c04f7ea7f05d14955fac8b422b32c55d14c2510cdf2983abbf778e726e0cb`.
- Capture file SHA-256:
  `9b31501c242a99de53c908fe472bb63f1e309bbfd17b1991e9c2cc9543ff6d3d`.
- The report records 800 tasks, 800 scored tasks, 800 actor attempts, 800
  responses, zero fits, zero updates, no backend error, and exactly 800 calls
  consumed.
- The capture records 5,606 output files: 3,204 native-actor artifacts
  (800 request/render/raw/response quartets plus config, identity, load, and
  close), 1,600 driver request/response files, 800 task files, one manifest,
  and one report.
- `worker_wait.json` records integer return code zero. `worker_release.json`
  records the owned group released. The contemporaneous post-worker GPU query
  records no compute process on the bound GPU.
- `capture_complete.json` is internally honest: `finalized=false`, status
  `CAPTURED_AWAITING_RESERVATION_RELEASE`, zero fits/updates, worker group
  released, GPU compute vacant, and no claim that reservation release was
  exhaustively proved.

The frozen report also says `thresholds_passed=false`. For engineering
diagnosis only, its five positive delayed panels are 0/64 and its positive
reachout panels are 6/32, 5/32, and 8/32. These values did not cause the
terminal verdict and must not be promoted into paper evidence from this
attempt.

## EngineCore SIGTERM: what it does and does not invalidate

The native actor had no supported LLM-level shutdown method. After all 800
task receipts and the report had been fsynced, EngineCore PID 160873 remained
idle and kept worker PID 160440 waiting at exit. Main then sent one SIGTERM
through a pidfd to that exact owned descendant after checking its boot ID,
UID, PID, parent, process group, session, start ticks, and the already-fixed
report hash. The signal receipt is in the sibling
`.engine_release_1344Z` directory, outside the frozen scientific inventory.

This intervention does not make the saved generations semantically
unreadable. It occurred after the final actor response, close receipt, task
rows, and report were fixed; the report byte hash remained unchanged; the
engine log records orderly abort-mode resource teardown; and the worker then
exited zero. It therefore remains reasonable to use the captured responses to
debug prompts, parsing, scoring, and audit code.

It is nevertheless a lifecycle defect. A human-issued post hoc signal was not
the intended native close path. It cannot be called a clean paper execution,
and attempt 3 must turn the same exact-owned cleanup into frozen controller
behavior with receipts rather than repeat the manual intervention.

## Why finalization failed

The only call to `finalize` created `finalize_claim.json` at monotonic time
535497.766918263. Its queue-release check passed. Its next CVD scan, at
535500.648--535500.661, found:

- no visible CVD owner;
- the two exact approved user-init services, still honestly recorded as
  unreadable;
- one additional unreadable same-UID PID, 164452.

Because PID 164452 was neither approved nor readable, the scan correctly
returned `clear=false`, `device_unreserved=false`, and `BLOCKED`. The
finalizer wrote `finalize_failure.json` with `CVD owner remains; release Main
holder before finalization` and stopped before the GPU and second CVD checks.
That error string is broader than the observed fact: no owner was visible;
the exact blocker was unresolved visibility for a same-UID process.

The vanished PID was not retrospectively identified. Contemporaneous public
metadata did identify the analogous new unreadable PID 165118 as the
foreground observer's own `sshd` parent, and the later transient PID 164788
also disappeared when its observation ended. This strongly supports a
lifecycle bug: running the release scan inside a foreground SSH session causes
the scan to encounter the session's same-UID `sshd`, whose environment is not
readable. It does not prove what PID 164452's environment contained, and it is
not permission to whitelist all `sshd` processes. Such a process could in
principle have selected a GPU, which is why fail-closed behavior was correct.

## Why attempt 2 cannot be upgraded

No honest recovery can turn this attempt into a finalized result:

1. `finalize_claim.json` and `finalize_failure.json` already record the sole
   finalization attempt. The implementation's exclusive-create semantics also
   mechanically refuse a second claim.
2. The later post-failure and detached observations explicitly say
   `original_finalization_failed=true`, `diagnostic_usable=false`, and
   `CURRENT_RESOURCE_OBSERVATION_NOT_ORIGINAL_FINALIZATION`.
3. Those later observations establish only that the resource was empty at a
   later time. They cannot fill the missing first-finalization GPU/CVD/group
   chain at the original time.
4. Deleting the failure, replacing the claim, manufacturing release receipts,
   or invoking a modified finalizer would violate immutability and the
   once-only rule.

Permitted use is therefore narrow: preserve the bytes; use them to find
interface, parser, prompt, lifecycle, and analyzer defects; and label every
derived table as engineering analysis of an unfinalized capture. If any
development choice is made after reading these outcomes, later evaluative
claims require fresh sealed material. Attempt 2 cannot support a paper number,
an effect estimate, a passed/failed C0 claim, learning, LoRA, memory,
parenting, H1/H2, full-v2.2, strong-memory, recurrence, or C11 evidence.

## Exact attempt-3 detached-finalizer requirements

Attempt 3 should change lifecycle only. It must not become a score-driven
retry.

### Before execution

1. Freeze the identical actor, model, tokenizer, prompts, roots, opaque IDs,
   task order, scorer, thresholds, seed, and zero-fit policy. Use fresh output,
   outer, launcher, allocation, and claim paths. Record the lifecycle-only
   source delta before any output is visible.
2. Implement EngineCore teardown in the frozen controller. It may signal only
   a proven descendant of the owned isolated worker, using full
   boot/UID/PID/PPID/PGID/SID/start-tick identity and pidfd semantics, and only
   after the 800 task rows, native close, and report have been fixed and
   rehashed. Preserve before/signal/after receipts in the bound lifecycle
   inventory. No human signal is part of the run.
3. Install a host-local detached finalizer before the result exists. A
   predeclared user service or equivalent isolated session is preferable. Pin
   its interpreter, source hash, argv, environment, unit/cgroup identity, and
   output paths. Set `CUDA_VISIBLE_DEVICES` to the explicit empty string;
   detach stdin; redirect and close stdout/stderr and every transport file
   descriptor; create a new session; and forbid an SSH ancestor.

### Handoff and one-shot claim

4. The foreground launcher must return and its exact SSH transport identity
   must be absent before finalization eligibility. The detached service must
   record its own PID/PGID/SID/start/boot/UID, parent/cgroup, ancestor chain,
   and the disappearance of the launcher's exact transport identity. A fixed
   sleep alone is not proof.
5. The detached service may wait read-only for `capture_complete.json` and for
   transport clearance, but it must not create `finalize_claim.json` until
   those prerequisites pass. After it exclusively creates that claim, it gets
   exactly one call to the pinned finalizer and no retry branch.
6. The capture hash passed to finalization must be computed and recorded from
   the immutable capture bytes. The original run deadline remains in force;
   neither waiting nor detachment starts a new clock.

### Release proof

7. In the detached process, repeat the full chain in order: input/source and
   capture rehash; output-inventory equality; worker exit-zero and group
   absence; release queue; same-UID CVD scan; global and selected-GPU compute
   query; second same-UID CVD scan; final group/identity check.
8. Keep the exact user-manager/PAM exceptions and reject every other
   unreadable same-UID process. Do not add a general `sshd`, foreground
   observer, or transient-process exception. If an unrelated SSH session is
   present at the one-shot scan, the run fails closed.
9. Only the detached finalizer may create the cross-linked release
   attestation, release receipt, final result, and collection. A later
   observer may verify them but may not repair or supplement a failed chain.
10. Add adversarial CPU coverage for: launcher SSH still alive; inherited pipe
    keeps transport alive; finalizer has an SSH ancestor; extra unreadable
    same-UID process; capture mutation while waiting; second finalizer start;
    original-deadline exhaustion; stale/reused transport PID; EngineCore
    identity drift; signal before fixed report; and missing final receipt.

If attempt 3 passes this lifecycle unchanged, it may recover the deliberately
narrow exploratory C0 execution label. Because attempt-2 panel outputs are now
known and the same fixed material would be rerun, attempt 3 is not an
independent replication and must not be presented as one. The final C11 run
still needs the prospectively complete guard and fresh sealed evaluative
material.
