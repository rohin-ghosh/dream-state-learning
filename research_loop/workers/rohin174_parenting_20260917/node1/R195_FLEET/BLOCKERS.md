# Node1 blockers for Main — 2026-09-17 19:06 PDT

## Current disposition — 2026-09-17 19:26 PDT

CPU gate blocker resolved and Main's tested versioned existing-life CPU root
policy verified in the SHA599f44… overlay archive. READY.json file hash is
197df5…; no unresolved checksum issue. **No node1 retirement authorized.**
Preserve current lives; candidates and sandbox binding returned in
R201_MAIN_RETURN_20260918T0226Z.md. C2 snapshot/context and exact named slot are
still unbound here. Earlier implementation-pending notes below are historical.

**No deployment. Main code-test READY is still outstanding.**

## Update — 2026-09-17 19:13 PDT: CPU gate blocker cleared

Follow-up user authorization allowed the existing trusted CPU-only probe on a
fresh isolated path after the bounded legacy search found no reusable gate.
All five existing probe modes and three fixed smoke cases PASS on node1;
actual gate reverified and all spawned units/cgroups stopped. Binding:
`/localhome/local-rohing/orch_r153_cpu_smoke_20260918t0212z/gate`, digest
`ca755cbd60be96fa310bff0c8149ed8777159e0e09dbd437c076190f7577356d`.
See CPU_GATE_READY.json and CPU_SANDBOX_BINDING.md. No new framework or live
source change. The historical absence finding below is no longer the blocker.

**Remaining:** Main's final versioned R184 same-life `cpu_once` root policy and
final runtime tests/READY. Default R153 validation must remain unchanged.
No native handoff has been started; no live learner/GPU calls were made.

## Concrete ACT execution incompatibility in the currently visible runtime

At 2026-09-18 02:06:38 UTC, read-only inspection found:

1. `gpu/orch_r184_think_act_learn.py` routes ACT execution through
   `gpu.orch_r153_community_transport.cpu_once`, passing the existing life root.
2. `gpu/orch_r153_community_transport.py:75` (`remote_root`) requires a canonical
   root with an `r153` path component. All six node1 roots are unchanged
   `/localhome/local-rohing/orch_r136_a100_<life>_20260916_attempt1/run1`.
   Therefore the current transport rejects them before dispatch, even if the
   code is valid. Renaming/rebirth/symlinking a life to fit this guard is not an
   acceptable repair.
3. The same transport requires an actual bound CPU confinement receipt at
   `/localhome/local-rohing/orch_r153_cpu_smoke_YYYYMMDDtHHMMz/gate`.
   Read-only maxdepth1 directory discovery on node1 found **no existing
   `orch_r153_cpu_smoke_*` directory**. This establishes only absence at those
   accepted locations, not absence of every possible CPU sandbox on the host.

Main's READY must supply a same-root-compatible execution path and the actual
node1 existing confinement binding, or explicitly resolve the capability
limitation. Do not copy a node5 gate hash, fabricate a receipt, create new
infrastructure here, bypass isolation, or claim execution from R184_ACT's
`TOOL_OUTCOME_UNKNOWN_NO_RETRY` status. This operator does not edit runtime.

## Operator reuse constraints, not additional authorization gates

- R181/R179 ownership, pidfd, saved checkpoint, full stream/optimizer/RNG
  verification and strict admission helpers are available. Their old source
  hashes, actor identities, R181-specific behavioral tests and first-COMMITTED
  observer cannot authorize/prove the new R184/R193/R195/R197/R198 runtime.
- Incoming six lives currently use R181, with terminal SLEEP_COMPLETE windows;
  no R184_LEARN_COMPLETE tail is needed for this first transition. If a later
  retry involves R184, the legacy helper rejects its metadata tail; do not
  weaken it to admit new work or roll back to a stale checkpoint.
- Final source closure/config/CPU receipt is still Main-owned and not READY.
  A moving working tree is not the deployable source binding.

Report path is the worker-to-Main handoff. COORDINATION remains Main-owned.
