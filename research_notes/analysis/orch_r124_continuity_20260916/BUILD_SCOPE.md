# R124/R125 bounded continuity prototype

[Builder / Main] September 16, 2026, 05:31 UTC.

Read raw Messages 124 and 125 after fetching origin/main through `e8a6eb58`.
The latest request is a simple continual child that Rohin can talk to, with
accurate LoRA/context/token awareness. R125 permits oldest-context removal in
v0; child-authored compaction is to be taught, not assumed already learned.
The watcher's birth prompt is a draft, not an empirically established set of
adapter laws or an already running system.

This is an invariant-preserving, builder-authorized implementation experiment
under AGENTS.md standing authorization. It is not a new paper benchmark or
claim and does not wait for the historical R121 four-condition deliberation.

## Implementation boundary

- Standalone TRAIN-only history and scheduler; no live F1/F2/F4 source mutation,
  checkpoint reset, parent replay, or change to existing FINAL reservations.
- Preserve raw event provenance and immutable historical attribution. Only
  current child outputs can become training targets; prior history, human
  input, parent guidance and environment observations are masked input.
- Continue at software generation boundaries without inserting fabricated
  child-authored `Next:` text or claiming uninterrupted KV-cache computation.
- Nonblocking incoming human/parent events are appended once at a boundary.
  Scheduler-generated cost/context notices are environment events, never
  disguised as the child's output.
- Pin system/birth context. Explicit oldest-event eviction records a receipt;
  strict no-eviction mode remains available. A child-authored compaction path
  retains exact source/frontier binding and does not certify summary truth.
- Evaluation is a separate, empty-context path and never enters TRAIN history,
  compaction, parent inputs or replay.
- Resource access needs enforced process/filesystem/GPU isolation, not a
  textual shell allowlist. No arbitrary child shell execution is enabled by
  this prototype, and no four-GPU resource grant is claimed before admission.
- CPU tests establish scheduler/provenance mechanics only. Actual model load,
  sleep optimizer integration, sandboxed experiments and console deployment
  require their own concrete runtime checks and launch receipts.

No benefit, consciousness, subjective continuity or successful learning is
claimed. Level-1 paper scope remains; SEAL is optional, not a blocker.
