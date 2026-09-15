# Frozen initial-adapter reference: implementation candidate, not launched

September 15, 2026. Main owns this follow-on wrapper; it does not replace any
current parenting lane or create another live baseline trio.

`gpu/orch_r118_frozen_seed_reference.py` implements a separately rooted,
evaluation-only reference using the canonical campaign's original initial
adapter and held groups 1–6. It imports the original campaign engine, episode
function, task ordering and validated event-store reconstruction. It does not
reuse the historical stage dispatcher, whose identity resolver would select
trained children rather than the fixed initial adapter.

The intended identity is the previously verified initial adapter state
`d13fabd566e04926f45aa66ee0a30ff7dc88d411430ab3e1fe15dfffeb2fd27f`,
not bare BASE. Each of six groups executes in a fresh process, with two
original sequential tasks, no parent/private context, no optimizer, no
reflection and no training rows. Generation retains the original 8192 context
cap and 512-token ceiling. All attempted calls are precharged against a new
72-call/36,864-generated-token maximum; failures remain charged and are not
retried. Completed episodes are persisted even if a later episode fails.

The frozen feasibility document in
`../orch_r111_parent_20260915/FROZEN_INITIAL_REFERENCE_FEASIBILITY_1353.json`
provides the exact historical PREPARE, COHORT, SOURCE, initial-adapter and
source-file hashes. A future plan must supply their real on-node paths plus
a complete frozen source closure, including this wrapper. No historical file
is rewritten. The original event-store validator reconstructs the complete
historical store; only the selected twelve tasks are presented for evaluation.

## Before any GPU allocation or run

This candidate has **13 passing local CPU tests**, not a native model result.
The tests exercise exact input identities, unchanged adapter files, source
pins, task ordering, parent absence, independent failure preservation, shared
call accounting and fixed wall/lease limits. They do not prove actual model
loading, equivalence of generated responses, GPU release or lease ownership.

Remaining work is explicit:

1. Freeze the complete native dependency closure and run native CPU integration
   checks against the actual canonical inputs and loader/episode hooks.
2. Allocate one genuinely released GPU; verify its ownership, strict admission
   and actual lease. Neither node-5 recovery slots nor the separately allocated
   GPU annotation slot are reserved for this reference.
3. Publish a new plan with a wall of at most one hour, capped by the actual
   lease minus six hours, and the new fixed 72-call budget. External admission
   and deadline supervision must wrap the candidate's supervisor.
4. Run `validate`, then `supervise` from the frozen source with the exact GPU
   UUID and offline environment. Collect actual loaded identities, fresh
   process receipts, unchanged before/after weights and terminal outcomes.
5. Compare only completed, matched task receipts with the existing canonical
   GUIDED/UNPARENTED readouts; retain missing groups explicitly.

No GPU, wall-clock reservation, model call or reference result is claimed by
this publication. It is not authorized to overwrite an old failed readout.

## Scientific limit even after execution

This could close the missing **initial-adapter-matched frozen evaluation**
gap. It cannot equalize historical GUIDED/UNPARENTED sleep doses, control the
different pooled node-5 lineage, demonstrate retained thinking by itself, or
establish causal dependence on parenting. Those remain separate requirements
of the active sprint goal.
