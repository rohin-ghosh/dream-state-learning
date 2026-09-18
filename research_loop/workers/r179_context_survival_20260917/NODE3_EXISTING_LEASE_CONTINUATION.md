# Node3 existing-lease runtime continuation — September 17, 2026

Builder instruction, issued at 10:46 PDT. This is separate from the frozen
R179 source-only scope. It does not acquire, renew, or extend a machine lease.

Authority: Rohin131 orders the non-degraded continual children kept running
and restored after failure; Rohin145/147 retain every non-degraded life.
The user's September16 22:38Z fleet-wide wall order explicitly requests
extension of the remaining children's internal walls. The September17
02:10Z clarification says the internal experiment wall is not evidence of
a hardware reservation ending. This instruction uses only the already-bound
node3 lease; it does not infer permission to pass its ceiling.

The six node3 lives on physical0,1,2,3,4,7 currently bind:

- Previous internal deadline: 1789668000 (September17 11:00 PDT).
- Existing lease and next-reservation ceiling: 1789689600
  (September17 17:00 PDT).
- Existing receipt:
  `/localhome/local-rohing/orch_r118_node3_7_grid_20260915_attempt1/lease_budget_r119_learned/LEASE_BUDGET.json`.
- Receipt SHA256:
  `919e9fb3f9cfd6cadb57af90844319e50eb114068eb52cd75aa3ab715f9c3770`.
- Requested internal deadline: 1789689000 (September17 16:50 PDT),
  ten minutes before that unchanged ceiling.

Use the existing R131 saved-state wall-extension protocol: fresh immutable
configuration, previous-state/deadline hash binding, a new LEASE_BUDGET with
`lease_extended=false`, and an actual WALL_EXTENDED journal event on resume.
Preserve adapter, optimizer, RNG, history/view, targets, dispatch counters,
inbox identity, prior evidence and evaluator budgets. Do not renew, reset,
refund, or delete anything. The source change may additionally contain the
already-approved exact R179 context patch, separately attributed.

Before any learner signal, receiving CPU/state tests, exact owner checks,
device containment, and executable successor preflight must pass. Bind the
specific operator/source/test bytes in a dated Builder launch receipt. The
old source and every expired waiter remain immutable. No replay of consumed
handoff controls is permitted. Final GPU admission must genuinely pass the
unchanged scanner after the prior owner exits.

Prefer the next complete sleep/readout boundary. If the old wall is reached
first, preserve the actual terminal receipt and all journal suffixes, then
use the existing exact-state recovery protocol with explicitly recorded
last-complete checkpoint and suffix disposition. Do not label a rollback,
partial optimizer cycle, or unverified replay as exact uninterrupted
continuation. A recovery-specific CPU proof is required. Report a concrete
unsupported recovery state rather than improvising training or losing data.

This instruction is a bounded internal-budget continuation under the prior
explicit keep-alive orders, not fabricated human ratification of a new
hardware lease. Any change to the evidenced machine ceiling remains outside
this scope and requires the reserved authorization path.
