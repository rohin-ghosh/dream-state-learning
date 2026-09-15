# Two-episode parenting observer repair and late-cycle evidence

Measured 2026-09-15 06:53–07:00 UTC; published by Builder on September 15.

## Scope and provenance

Non-material repair: the observer assumed eight experience episodes and only
cycles 2–3. It now reads immutable episode denominators and planned IDs, checks
duplicates/foreign IDs and saved-to-next-input adapter identity, and discovers
later cycles. Historical eight-episode fallback and write-once evidence remain.
No live model, prompt, training, benchmark, parent visibility or budget changes.
Six observer regression tests pass. The old live observer was not hotpatched.

An isolated native CPU reduction emitted 16 previously missed sleep-to-next-
original-attempt joins. V2 also checks saved/loaded/after identities, distinct
readout process, frozen base, and parent-free readout. Native evidence remains
on A100 under `/localhome/local-rohing/orch_l2_observer_repair_20260915`.
`LATE_CYCLES_V2.json` SHA256:
`97307eae5a404b9bd44e7e4c03fd13f812dd60097c5c2f37b5e3469ddf07b507`.
The committed compact reductions contain hashes/metrics, not raw transcripts.

## Thinking and cycle time first

| Lane / latest complete cycle | Mean held tokens | Full cycle seconds | Readout seconds | Updates this sleep | Ancillary correct |
|---|---:|---:|---:|---:|---:|
| MICRO C7 | 278.375 | 1147.955 | 214.546 | 434 | 8/8 |
| CREATIVE C6 | 320 | 898.503 | 227.346 | 502 | 7/8 |
| Training-wheels C3 | 309.75 | 1266.687 | 226.626 | 422 | 6/8 |

Early C1 token means were 274.125, 286.5, and 309.75 respectively. These
different-task cycle comparisons are descriptive, not matched causal effects.
All listed held readouts had zero truncation. Full cycle includes experience,
parenting, reflection, sleep and readout; this table does not separately identify
parent latency or prove a before/after speedup against the old eight-episode lane.

Author read the first two held responses at early/latest cycles in each lane
(12 responses). Algebra checks appeared early and late; box calculations were
linear. The system asks for reasoning/checks and algebra questions explicitly
request checking: terminal checks cannot be claimed as spontaneous default
departures-and-returns. No measured retained branching advantage is established.
Adapter joins establish inheritance, not semantic uptake; alternating task
families can leave immediate-next-cycle same-family comparisons empty.

## Preserved feedback-use failure

Post-hoc single case, not a prevalence estimate: CREATIVE C6 TRAIN E10 derived
684 using the false equality 31×21=657. The product is 651; the corrected
candidate is 678. The parent explicitly requested recomputation and remainder
checks. Full guidance reached reflection without input truncation, but reflection
repeated 684 and attributed the incorrect outcome to presentation. Independently,
684 modulo 31 is 2 and modulo 37 is 18.

Both incorrect attempt and reflection were retained as INCORRECT-tagged records,
55 presentations each. This is positive-likelihood SFT on outcome-tagged records,
**not negative-gradient training**. Evidence is in
`FEEDBACK_C6_FAILURE_COMPACT.json`. No running lane was stopped or tuned because
of this outcome. A prospective interactive-feedback treatment is separate.

## Status

Parenting-dependent retained improvement remains unproven. These receipts repair
observation and preserve a failure; they do not promote the scientific claim.
