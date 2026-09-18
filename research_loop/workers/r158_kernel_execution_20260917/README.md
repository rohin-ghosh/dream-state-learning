# R158 actual kernel-sidecar renewal

**FINAL05:03UTC:** services ended cleanly05:02:39UTC; actual PIDs gone and
custody locks available verified, observer/collector also ended. Kernel4 nudge
rendered and produced one genuine child C++ request, rejected before GPU launch;
two later responses truncated. Kernel0 nudge not rendered during this window.
**No child GPU kernel execution.** See `FINAL_CLOSURE.md` for receipts and final
new-vs-inherited counters. All live-status notes below are historical.

**Fresh04:52UTC update:** phase2 is live, calls0, deadline05:02:39UTC. Original
observer failed04:26:53UTC; the old04:24 local snapshot was stale. Repaired
read-only observer159584 and local metadata collector3332017 are running;
publication confirmed, no rendering/child execution yet. See
`FOLLOWUP_20260917T0447Z.md` for exact audit, reserved-vs-actual I/O and closure checks.

**Update04:23UTC:** One exact Main-authorized Astra nudge was published per
kernel0/4 at04:21:32UTC. No rendered inclusion or child execution yet; CPU-only
observer4134329 is running. See `ASTRA_NUDGE_PUBLICATION.md`. Do not resend.
The earlier04:17 status below predates this authorization/publication.

## Observed status — September 17, 2026, 04:17:31 UTC

Actual activation occurred at **04:12:39.476 UTC**. Supervisor4042560 and
sidecars4048159(kernel0)/4048160(kernel4) remain live. Both scanners are READY,
calls0, with no intent, refusal, terminal or bridge result. Current cursors
are3536/3418. **No genuine new child kernel execution/result is claimed.**
The metadata observation is `STATUS_20260917T0418Z.json`; its authoritative
`observed_unix` is1789618651.3422837 (04:17:31 UTC), not the rounded filename.

Remote immutable root:
`/localhome/local-rohing/orch_r158_kernel_execution_20260917t0402z`.

## Actual gates and custody

- Local and on-node CPU tests: **198 passed +21 subtests**; CPU-only execution.
- New actual GPU2 confinement gate: **all26 checks PASS**, observed04:12:39.318UTC,
  expires05:12:39.318UTC. No expired R155 gate reused. Trusted confinement probes
  are not child executions; no standalone fixture kernel was dispatched.
- Assigned executor remains physical2/minor1,
  UUID`GPU-35dcea35-12bc-f2f3-d5d2-d2eaa8bacdd8`.
- Prior R155 workers cleanly terminated03:06:48UTC, calls0/no pending, matching
  terminal/state and exited processes. Original custody locks were verified
  available before activation; the new supervisor holds them and passes their
  descriptors to its workers. No competing scanner or duplicate launch.
- Original lease receipt remains pinned; conservative effective cutoff is
  September18 18:00UTC, retaining the original6h reserve. No extension inferred.
- Source pins and child0/4 PID/starttick/command identities remain unchanged.
  Child0 PID2709461/start14646722; child4 PID3496993/start15201156.
  No child restart, checkpoint/recipe/source edits, or action on retired5.

## Bounded future-only service

New frontiers3527/3410 follow committed UPDATE3526/3409. Original R155 final
cursors3419/3303 and accumulated resource counters are preserved as evidence;
the audited offline gap is not replayed. The unchanged R148 path uses the
R153 forgiving first-code-block policy, fresh per-request census/admission,
and the original executor lock. No unknown/refused intent is retried.

The service has at most2 calls per life total and2 phases of1500seconds.
Phase1 ends04:37:39UTC. A second phase requires a clean matching terminal,
no pending fields, remaining call budget and a gate valid for the full phase.
The bounded campaign ends approximately05:02:40UTC if it renews; no third phase.
The live processes own this observation window; no additional launcher is needed.

## Why no child result yet / Main action

Recent audited kernel0 responses3460/3464/3467 had no exact request. Kernel4
response3319 passed fence/origin checks but contained C++ and failed the actual
kernel AST (`invalid_kernel_AST`);3323/3326 were truncated. None was dispatched.
Observed response bursts were approximately2–3minutes apart,36–59seconds per
generation, followed by long ordinary sleep training. Both children were in
sleep training at the initial audit; no future response time is guaranteed.

`PARENT_SAFE_INTERFACE.md` contains the exact connected bounded Triton float32
vector-add signature/prefix and one grounded console nudge **Main can send now**.
This worker has sent no parent/console message, supplied no complete kernel for
the child, accessed no held content, or claimed a model submission/result.

## Original-byte receipts

`receipts/` contains downloaded original-byte CPU/preflight/probe/activation and
scanner-start artifacts; `predecessor/` contains original R155 terminal evidence.
The transport JSON files are not substitutes for original-byte receipt hashes.

| Receipt | SHA256 |
|---|---|
|`receipts/CPU_GATE.json`|`b151056a47bbc66c12d914792dc364c5bc03f520f6854a0d4ab1d51f77327477`|
|`receipts/PRE_GPU_PREFLIGHT.json`|`7075016c0468cb652f89cadb03c31c447b62f02cdfe35ee2c4c61f76218f0b71`|
|`receipts/probes/GATE.json`|`d551e3c7158496d783f162d4f2acaa9c1ef2066174d972d8e25b3e95c6f8e9b5`|
|`receipts/ACTIVATION.json`|`496ad1ad429f67b79c9a8be05c1f807ed0f0b2959a1767e54ab875b553dae6f3`|
|`KERNEL_AST_AUDIT.json`|`261c85c38c9698220946703a2d5b8f2f44154003380711523afc036e0599563d`|

Implementation frozen SHA256:
`gpu/orch_r158_kernel_execution.py`:
`e559cf71dc39aae5e9628254c63ac1f8f52f06e3472068e7727f0d14c3fdc37c`.
Tests SHA256:
`ed0ff23eae81820c0d68c5e2ab9a4ff98522fc498540f1aec1ffba3ff25e6030`.
