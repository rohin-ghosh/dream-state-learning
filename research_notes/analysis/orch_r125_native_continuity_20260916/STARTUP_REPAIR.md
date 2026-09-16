# Native startup repair — September 16, 2026

The first supervisor obtained privileged admission on ovx3 physical2:
`clear=true`, no blockers, documented1MiB idle baseline. Timeout-parent
PID20340 dispatched at06:09:15.806 UTC. Native startup exited before model
construction with `FileNotFoundError` while creating `run1/stream`: the native
run root did not yet exist. No native model call, generation or optimizer
update occurred. The earlier launch is not a running-child receipt.

Non-material root-cause repair: create the run directory before opening the
exclusive journal. Existing journals still cannot be recreated or overwritten.
A new regression starts from an absent run directory and executes the synthetic
full loop. Local expanded suite:202 tests and202 subtests PASS.

The old source and all control receipts remain untouched. Next dispatch uses
`source_v2` and `control2` under the same node-local attempt parent, with fresh
source/plan/allocation hashes and fresh privileged admission. `run1` remains the
intended life root; no model or life existed there to reset. Native evidence
will be reported only after actual execution. Same lease wall, prompts, loss
mix, evaluation visibility and experiment-tools-disabled contract.
