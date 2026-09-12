# Grouped lexical-views root-0 terminal post-audit (2026-09-12)

## Result

The registered `SINGLE_VIEW` versus `FOUR_VIEW` root-0 pair completed.  Both
arms began from the same seed-0 teaching-parent adapter and received the same
16 memory sources, 16 arithmetic sources, target bytes, source multiplicity,
10 epochs, 320 new optimizer updates, rank 8, and learning rate `3e-4`.

| arm | dev arithmetic | dev memory | exact memory | answer mode |
|---|---:|---:|---:|---|
| `SINGLE_VIEW` | `0/32` | `4/16` | `4/16` | only blue/green; arithmetic generations became repeated color words |
| `FOUR_VIEW` | `32/32` | `4/16` | `4/16` | all 16 memory answers were `yellow` |

The preregistered progression gate required FOUR_VIEW memory at least `15/16`
on both panels, habit at least `30/32`, and action-format adherence at least
`31/32`.  Memory failed decisively, so roots 1--2 must not auto-progress.

## What it establishes

At this root and dose, four fixed lexical phrasings prevented the catastrophic
unrelated-task collapse caused by repeating one wording: `32/32` versus
`0/32` arithmetic.  This is strong directional evidence that input-surface
diversity changes interference and can act as a regularizer.

It does **not** establish storage, extraction, replay, dreaming, retention, or
semantic re-perception.  Both arms remained at `4/16` on both memory panels
and each collapsed to a narrow color prior.  There is no positive memory-view
effect to replicate.

## Exact estimand caveat

All four copies/views of one source were forced into the same batch.  With the
trainer's mean causal-LM loss, SINGLE_VIEW collapses four identical source
gradients before one Adam step while FOUR_VIEW averages four lexical gradients
before that step.  Each source therefore participates in ten source-specific
optimizer updates, not forty temporally separated replay encounters.

The run estimates **same-batch lexical-gradient diversity**.  A positive
arithmetic-preservation contrast cannot be called temporal varied perception,
and the memory null does not falsify Rohin's stronger hypothesis that revisiting
one event through distinct semantic views across time improves extraction.

## Next-action ruling

Preserve this as a useful anti-collapse diagnostic.  Do not expand roots under
its failed gate.  If the replay hypothesis is revisited, use the already
specified scattered schedule (four distinct source-specific optimizer steps
per epoch) and compare lexical views with relation-defined semantic views.
That successor is downstream of the selective Q0 writer and equal-dose
OLD/NEW coexistence gates; it should not displace them on the paper critical
path.

## Immutable artifact

Run root:
`~/astra_diagnostics/astra_varied_memory_replay_20260912_attempt1/fits_root0_attempt1/run`

Controller status `COMPLETE`; plan SHA-256
`2120bb93d0458b789bb3db408e57dd077f528cfadec35691b0e5fb27889756ca`;
reserved wall time `1013.65` seconds; all worker cleanup and release checks
passed.

