# Prospective C2 sampling diagnostic

**Declared before any new GPU dispatch in this sprint.** This is an
invariant-preserving builder experiment, not a claim of independently
replicated training or an authorization to bypass source/custody admission.

## Question

Does the descriptive ordering observed for the selected historical C2
checkpoints persist under two new generation seeds, with the evaluation
protocol otherwise unchanged?

## Fixed design

- Conditions: preserved frozen base, C2 sleep51, C2 sleep117.
- New generation seeds: **23301 and 23302**, shared across conditions.
- Original three DEVELOPMENT scenes; original tokenizer, decoder, prompts,
  THINK/ACT cell contract, no-format extraction, scoring and novelty rule.
- Original adopted rank8/step15625 judge and its private reference panels,
  retained exclusively in scorer custody. No panel content reaches a parent.
- Exactly the original cap of1,024 generated tokens per scene/seed:
  six cells and6,144 generated tokens per condition;18,432 across all three.
- No parent messages, parameter updates, developmental transcript, or live
  working state in these disposable evaluation copies. Do not stop or modify
  the source lives. Preserve the exact source adapters and histories.
- Separate protocol/run identity, config/source hashes, claim ledger and
  diagnostic epoch. Do not rewrite or relaunch original completed jobs, relax
  existing lease limits, or reinterpret a platform denial as a retryable error.

The CPU preparation is bound in
`replication/C2_SAMPLING_CANDIDATE_V2.json` and `replication/REPORT.md`.
Final executable source hashes and actual admission receipts must additionally
be recorded before launch. Those preparations alone are not a run receipt.

## Endpoints and reporting

Report each source/seed separately: actual generated tokens, ACT opportunities,
distinct scored caption strings, distinct accepted strings, operational new
pixels, and unscored/error outcomes with their reasons. Deduplicate by the
existing scene/caption identity before counting; do not count replayed
`new_pixel` statuses as new discoveries. An ACT with no scored string does
not necessarily mean no caption: distinguish extraction absence, judge
rejection without rank, and execution/transport failure where the original
receipts permit it.

Primary descriptive contrast: within each seed, sleep51 minus base in
distinct operational new pixels at the fixed token budget. Report sleep117
minus base and sleep51 minus sleep117 alongside it. Publish all cells and
failures, not only the favorable seed or checkpoint. Never score an unknown
execution as zero or silently replace a failed cell with a rerun.

## What this cannot establish

There are still only historical source lineages. Sampling seeds are not
independent training replications; these are exposed development tasks, not
held-out game transfer. The selected sleep51 checkpoint is not a preregistered
optimal age. Judge acceptance is not certified humor, and a positive result
does not isolate parenting, tapering, or the effect of consolidation.

Execution readiness additionally requires the real shared GPU claims,
confinement, fresh device/lease/source proof, receiving CPU checks and a dated
Builder entry. These implement existing invariants, not a new human-approval
gate. If blocked, report the concrete blocker without changing the experiment
silently.
