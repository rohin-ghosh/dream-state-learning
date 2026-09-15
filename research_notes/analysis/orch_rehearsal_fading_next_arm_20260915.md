# Fading rehearsal — next treatment arm, not deployed

## Scope and authority

Rohin104 requests age-decaying rehearsal refreshed by frequent use. Rohin105
(September15,2026, approximately05:40UTC) clarifies the ladder: rehearsal stays
ON throughout levels2–3 childhood; the shipped level4 has NO replay and keeps
only reflection-based sleeps at lower plasticity. Reflection is taught through
parenting and can occur during idle time as well as after experience.

This is a design-only amendment. Keep every running lane's in-batch old-row mix,
two-episode schedule, optimizer, controls, allocation and budget unchanged.
This prospective comparison is not a new baseline triple, foundation change,
deployment authorization, or learning result. The exact raw directive is in
`research_notes/THESIS_RAW_ROHIN_2026-09-11.md`, Message105.

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

During levels2–3, keep a nonzero old-row rehearsal allocation in both current-
mix and fading-mix arms. Age decay changes sampling within those old-row slots;
it does not switch childhood rehearsal off. In particular, an arbitrary late
cycle of a level2 experiment is NOT a level4 deployment transition.

Only at an explicitly registered level4 boundary set old-row replay slots to
zero, rather than renormalizing tiny weights into a hidden perpetual cache.
Both sleeping arms of the level4 deployment test must have zero replay and
fresh own-reflection targets only: no legacy rows, old target reuse, raw-attempt
targets, or teacher transcript targets. The starting checkpoint and lower-
plasticity configuration must be frozen before that separate test. No held-
score-triggered transition or live-lane change is authorized here. See
`orch_level4_reflection_only_design_20260915.md` for the prospective test.

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
trigger. Record level4 as a separate experiment, not an unlabelled late phase
of the level2–3 fading comparison. Removing old slots and allowing only fresh
reflection targets changes both the treatment and presentation accounting.

## Tests before the separate launch

- Weights decay monotonically without genuine use; genuine later TRAIN use
  refreshes exactly the named immutable record.
- Replay reads, fabricated IDs, parent-only mentions and held runs cannot refresh.
- Wrong-outcome records retain their tags and are not silently filtered.
- Identical age/use records have equal probability irrespective of outcome.
- Levels2–3 never disable the configured old-row slots because of age or cycle.
- Both level4 sleeping arms yield exactly zero old-row presentations; every
  supervised target is a newly generated, source-bound own reflection.
- Resume preserves optimizer, record history, RNG, refresh ledger and counters.
- Matched treatment schedules, two-episode ordering, provenance/visibility and
  compact evidence storage pass their existing tests.

No live sampler, optimizer, model checkpoint, GPU allocation or budget is changed
by this design. The author will publish exact source, cohort, ladder boundary,
plasticity and budget bindings before either bounded comparison is launched.
