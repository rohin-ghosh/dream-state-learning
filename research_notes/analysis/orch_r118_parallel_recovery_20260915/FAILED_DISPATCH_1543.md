# Failed startup, preserved — September 15, 2026

The dispatcher started at 15:43:35 UTC and failed at 15:43:37 UTC with
`fresh_owner_command_failed_F1`. The session never issued all-eight GO.
This is not a successful recovery, shared sleep, or learning result.

Main's route-broker preflight failed, but a subsequent shell command ran because
the commands were separated by a newline rather than conditional execution.
That was an orchestration error. The eight owner commands were spawned; model
initialization and successful bootstrap are distinct, and neither is a new
generation call. GRID's later audit records model loading followed by exit
before bootstrap, with no new generation/provider charges or optimizer steps.
Other family receipts must be read separately; do not generalize GRID's receipt.

Observed startup failures:

- F1's broker was alive, but its recorded parent PID became stale after
  reparenting. The original binding is preserved; Poincare corrected the live
  identity without changing provider, prompt, counters or validator.
- A1's privileged scan rejected the CPU launch processes' CUDA-visible UUID
  reservations. A CPU-only launcher must not advertise a reserved compute GPU.
- Both math scans rejected transient process-identity changes. Any correction
  must prove the relevant processes exited or changed identity; no blanket
  scanner waiver is authorized.

The original session's FAILED receipt, launch flags, scans and guards remain
intact. No blind redispatch, old input replay, deletion or quota reset is allowed.
Main authorizes narrowly scoped startup-repair preparation in separate execution
namespaces through 16:10 UTC, preserving the same committed generation-1 child,
pending experience, original TRAIN cutoff 16:55 UTC and family hard bounds.
This preparation does not extend training time or authorize standalone workers
to launch GPUs. A new all-eight session requires actual release/custody evidence.

`gpu/orch_r118_checked_dispatch.py` prevents the shell fall-through in future
launches: every preflight uses checked, bounded execution, and any nonzero exit,
timeout or missing command prevents spawning the dispatcher. Seven local and
seven native standard-library regression tests pass. The first pytest invocations
could not run because pytest was absent in those environments; the final tests
use unittest and require no installed pytest package. Native tested source is
`/localhome/local-rohing/orch_r118_checked_dispatch_20260915_1549`.

The readout-visibility answer remains unchanged: open turns exist under their
actual filenames and complete generated text is captured, but route held
behavior is predominantly protocol-only. Retained thinking and a causal
parenting benefit remain unproven.
