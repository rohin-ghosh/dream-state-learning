# Fading rehearsal — next treatment arm, not deployed

## Scope and authority

Rohin104 requests age-decaying rehearsal refreshed by frequent use, followed by
no replay at the older lower-plasticity stage. Keep the current in-batch old-row
mix unchanged now. This is a prospective parenting treatment comparison, not a
new baseline triple, a foundation change, or a claimed learning result.

## Proposed rule

Each retained record carries its creation cycle, last genuine TRAIN-use cycle,
and immutable provenance and outcome tags. At cycle `cycle`, the replay weight
is `2 ** (-(cycle - last_train_use_cycle) / half_life_cycles)`, with an initial
half-life of two sleep cycles. New records start at weight one. Genuine reuse
refreshes the use cycle; frequent reuse therefore keeps a record available.
Count use only when an existing record is actually retrieved into a later TRAIN
episode's child-visible context. Rehearsal sampling, copying a record, evaluation,
or a parent merely mentioning its ID cannot refresh it. Log every refresh.

Keep the current new/old slot fraction and optimizer-update allowance fixed;
change only the sampling distribution inside the old-row slots. Sampling
probability is proportional to the record weight, not its correctness or held
performance. Recompute using log weights to avoid numerical underflow. Negative
outcome examples retain their failure tags, source context and selection rights;
neither success nor failure changes the age rule. Archive all records even after
their sampling weight falls; forgetting in rehearsal is not evidence deletion.

At the prospectively fixed lower-plasticity stage, set old-row replay slots to
zero, rather than renormalizing tiny weights into a hidden perpetual cache.
The transition cycle and learning-rate/plasticity setting must be declared
before launch; no held-score-triggered transition. This document does not choose
or activate that transition in the running lanes.

## Comparison and readout

Use two parental treatments with the same starting child, parent style/provider,
two-episode cycle schedule, TRAIN/held task streams and native/parent budgets:
current mix versus fading mix. These are treatment variants, not two additional
control triples. Reuse the single canonical baseline only with its stated
cross-task/control limitations. Keep outcome losses distinct from thinking
measures and do not call outcome-conditioned positive cross-entropy a negative
gradient objective.

Per cycle, report default child tokens, substantive approaches and rejected
paths, repetition, coherence, taught-to-next-cycle change, and parent-free
retention. Also report actual old/new presentations, record ages/use-refreshes,
sampling probabilities, parameter changes, and generation/parent/sleep/readout
wall times. Outcomes are recorded as ancillary evidence, not an intervention
trigger. Record the no-replay stage separately because removing old slots changes
the treatment as well as the number of presentations.

## Tests before the separate launch

- Weights decay monotonically without genuine use; genuine later TRAIN use
  refreshes exactly the named immutable record.
- Replay reads, fabricated IDs, parent-only mentions and held runs cannot refresh.
- Wrong-outcome records retain their tags and are not silently filtered.
- Identical age/use records have equal probability irrespective of outcome.
- The lower-plasticity stage yields exactly zero old-row presentations.
- Resume preserves optimizer, record history, RNG, refresh ledger and counters.
- Matched treatment schedules, two-episode ordering, provenance/visibility and
  compact evidence storage pass their existing tests.

No live sampler, optimizer, model checkpoint, GPU allocation or budget is changed
by this design. The author will publish exact source, cohort, transition and
budget bindings before the bounded comparison is launched.
