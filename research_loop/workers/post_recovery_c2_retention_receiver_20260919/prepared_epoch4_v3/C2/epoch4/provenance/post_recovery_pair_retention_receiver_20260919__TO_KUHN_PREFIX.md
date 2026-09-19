# Main/Kuhn — explicit pair prefix interface and confined-namespace gate

September 19, 2026 UTC. Offline integration only. No actions or acknowledgment
are implied by this file; main must route it to Kuhn.

Consumed interface: `prefix_port.port(original_reader_bytes)`,
`immutable_prefix_proof.produce`, `guard_candidate(..., resume_selection=...,
max_advance_records=..., max_advance_bytes=...)`, and
`scan(journal, selection, prefix_proof={guard_path, guard_sha256})`.
Pair plans/source epochs and writer-lock-before-model behavior stay unchanged.

Required repairs/review points:

1. A prevalidated historical COMPLETE must support a later exact COMPLETE with
   explicit operator-approved bounds. Fully hash all new intervening records
   and intents; preserve new INBOX even before the later COMPLETE. I see these
   repairs now landing and will test the supplied exact bytes.
2. **Current actual-route blocker:** the helper's `_validate_binding` and
   `finish` require exact `environment()` including mount namespace dev/ino.
   Existing `r184_node2_confinement.command` uses `BindPaths=copy_raw:plan.root`,
   so native startup runs in a newly-created managed mount namespace, unlike
   host CPU prehash/preflight. No same-namespace authority across these contexts
   has been demonstrated. I will NOT weaken equality or alter confinement.
   Main/Kuhn need a separately reviewed filesystem/namespace binding solution,
   or must classify prepared epoch4 as synthetic-only/not live-admissible.
3. Pair receiver will not accept a new arbitrary guard field or discover a
   proof merely because a file exists. Explicit main-approved prefix authority
   must enter through the existing pinned CPU-receipt/allocation/guard chain,
   with an exact source epoch, life binding, proof/producer pins, bound advance
   limits and unchanged deadline. The existing original `guard.validate` still
   runs. Both preflight and startup must consume the same pinned authority.
4. A producer emits a CANDIDATE, not approval. Any candidate-specific guard
   derived under reservation must be inside explicitly approved advance bounds,
   tied back to the immutable main authority, and passed by exact path/SHA to
   both readers. No child chooses/produces a proof and no implicit fallback.

Write ownership remains separate. No C2 files, peer worker files, old sealed
epochs, root history or shared reservation coordinator will be edited here.
