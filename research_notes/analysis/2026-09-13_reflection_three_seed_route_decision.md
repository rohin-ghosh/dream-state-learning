# Reflection birth slice: three-seed route decision

**Date:** 2026-09-13 UTC  
**Status:** independent scalar-table interpretation of completed excluded-DEV
roots; no new model call, fit, adapter, benchmark, or GPU work  
**Frozen protocol:**
`research_notes/astra_memos/ASTRA_REFLECTION_PROTOCOL_2026-09-13.md`  
**Collected report:**
`/tmp/astra_reflection_three_seed_report_20260913_attempt2.json` on the Astra
host, SHA-256
`42aed54229f515540fb878a4610597195fa84e26b4df9dfd8db97de8c284433b`

## Decision

Use **teacher-withdrawn/context-distilled inputs** as the leading Level-1 route
for a future fresh-material comparison. Stop this exact 12-row reflection
family; it has already supplied the route-selection information it can.

This does not release a birth adapter, parenting claim, self-learning claim,
or authentic lineage. The targets were researcher-authored fixtures and the
panel is a 12-item near-transfer A/B choice task. The result is evidence about
how to present a small post-training corpus, not evidence that the child
created useful training material from experience.

## Exact action-choice result

Every cell had 12/12 syntactically valid answers in each learner seed.

| fitted adapter / evaluation context | seed 0 | seed 1 | seed 2 |
|---|---:|---:|---:|
| OFF / correction withdrawn | 7/12 | 7/12 | 7/12 |
| OFF / correction present | 9/12 | 9/12 | 9/12 |
| fit-withdrawn / correction withdrawn | 9/12 | 9/12 | 9/12 |
| fit-withdrawn / correction present | 9/12 | 9/12 | 9/12 |
| fit-present / correction withdrawn | 9/12 | 9/12 | 8/12 |
| fit-present / correction present | 7/12 | 7/12 | 7/12 |

The primary parent-absent deltas against OFF were therefore:

```text
fit-withdrawn: +2/12, +2/12, +2/12
fit-present:   +2/12, +2/12, +1/12
```

The sharper interaction is that the fit-withdrawn adapter was invariant to
restoring the correction paragraph (`9/12` in every cell), whereas the
fit-present adapter fell to `7/12` in every seed when that paragraph was
present. This is consistent with the teacher-visible training context becoming
part of the learned cue rather than producing a more independent procedure.
It does not establish that mechanism internally, and the deterministic OFF
repeat is one shared base observation rather than three independent controls.

## Restatement metric

Exact authored-string restatement was `0/12` in every one of the 18 cells.
The protocol explicitly forbids treating this as semantic prose failure:
truthful paraphrases also score zero. There is therefore no quantified semantic
restatement result, and it must not be averaged with the action panel.

## Consequence for the bootstrap and parenting design

The bounded operational hypothesis is now:

> Let a teacher influence the child's wake-time continuation, but when testing
> an authored Level-1 bootstrap, train the child to reproduce the useful child
> continuation from the teacher-withdrawn source state. Keep teacher text out
> of target tokens and test action again after teacher removal.

That is context-distilled supervised post-training. It is still **trained**,
not learned. In an authentic Level-2 lineage the semantic target must instead
be an exact child-authored span grounded in its public action/outcome history;
the compiler may strip/mask context but may not originate or repair meaning.

Do not spend another GPU round on this same fixture. If Level 1 remains useful
after the authentic vertical slice is underway, compare teacher-withdrawn
continuations against the other predeclared authored routes on fresh collision
material with a semantic derangement, action-only parent-absent endpoint,
locality/no-harm gates, and independent learner seeds.

## Claim boundary

Supported: under one small authored SFT recipe, the withdrawn-input adapter
improved strict parent-absent procedure choice by two items in all three
preselected learner seeds.

Not supported: semantic reflection acquisition, teacher benefit, parenting,
persistence across sleeps, child-authored data, closed-loop learning,
generalization, or H1/H2.
