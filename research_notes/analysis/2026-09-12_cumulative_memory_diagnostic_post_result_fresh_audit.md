# Fresh post-result audit: cumulative memory diagnostic

Date: 2026-09-12 UTC

Scope: read-only scientific audit of the synced cumulative preparer/reducer,
its focused tests and prior preparation audit, plus the exact compact terminal
values supplied by Main. The complete terminal capture is not local, so I did
not independently rehash raw evaluations, adapters, or cleanup receipts and
did not run a reducer, test, model, GPU, network, or remote command. Current
diagnostic source SHA-256 is
`62e58de3fe27bd63b6d1b737bcc8071e95bce9cc343562aff7e5eb901b7cd112`,
matching the prepared-source audit.

## Verdict

**The run is a valid terminal descriptive comparison, but it is a negative
qualification result for selective cumulative memory.** The strongest
defensible claim is:

> In one synthetic bank and optimizer seed, a rank-8 adapter freshly fitted
> from the base on OLD+NEW produced positive candidate-normalized target
> shifts on both replayed canonical car-completion panels. Its OLD shift was
> `0.209910`, 49.3% of the OLD-only adapter's `0.425674`; its NEW shift was
> `0.359223`, 53.4% of the NEW-only adapter's `0.673276`. The cumulative
> adapter therefore showed simultaneous but substantially attenuated,
> nonselective bank-associated responses. It did not qualify selective memory
> coexistence.

This is not warm-start or unrehearsed retention: `A1 = Fit(base, OLD)`,
`AN = Fit(base, NEW)`, and `A2 = Fit(base, OLD+NEW)` are three fresh-base fits.
OLD is reconstructed from replay in A2; no A1 tensor or optimizer state
survives NEW learning.

The stage/custody facts strengthen the narrow comparison: all six fixed stages
completed, every cleanup receipt passes, and A1-before/A1-after raw scores are
exactly equal. Thus temporal scorer/reload drift is not an available
explanation for the measured A1-to-A2 differences. The repeat is a no-update
control, not retention evidence.

## What the paired effects show

| canonical completion endpoint | single-bank effect | A2 effect | A2 / single | signed change |
|---|---:|---:|---:|---:|
| OLD, `A1 -> A2` | 0.425674 | 0.209910 | 0.493124 | -0.215764 |
| NEW, `AN -> A2` | 0.673276 | 0.359223 | 0.533545 | -0.314053 |

These are approximately 50.7% and 46.6% attenuations. Because focal OLD rows
receive three epochs in A1 and A2 and focal NEW rows receive three epochs in
AN and A2, the contrasts describe what happens when the other corpus is added
under this exact blocked replay recipe. They may be called
**mixture-associated attenuation** or operational interference in this one
schedule.

They do not identify a pure interference mechanism. A2 has 11,229 updates,
versus 9,693 for A1 and 1,536 for AN; OLD precedes NEW within every epoch; and
the total token mass, Adam trajectory, dropout sequence, and batch history
differ. The experiment has no equal-heat sham-corpus or alternate-order arm.
“Catastrophic forgetting,” dilution per token, capacity exhaustion, recency,
or optimizer competition are therefore not separately identified.

Most importantly, neither positive A2 shift is a selective-memory pass. A1
and A2 both fail G9 frame selectivity (spill `0.4155` and `0.2869`), G10 dose
monotonicity, G11 abstention, and G5 unrelated-control locality. A2's passes
of G1_d_p, G3, G4, and G9_mass show a real target-related probability response
with intact candidate mass; they do not override the locality failures. The
NEW reduced endpoint also needs its already-recorded bicycle/abstention
supplement before any car-specific reading; the primary reducer summarizes
NEW car cues but omits those specificity controls.

## Is `native_fact_retention_fraction = 1.169` valid?

**Valid arithmetic and useful as a secondary surface diagnostic; invalid as a
headline memory-retention fraction.**

The reducer computes this value as:

```text
A2 OLD dose-16 held-out-fact-paraphrase d_p
------------------------------------------------
A1 OLD dose-16 held-out-fact-paraphrase d_p
```

Here `d_p` is the mean ON-minus-OFF candidate-normalized correct-colour
probability gain over the native OLD *fact paraphrases*. It is not the
canonical completion-frame effect shown above, not `I_d_frame`, not an
owner-versus-look-alike selectivity interaction, and not generated accuracy.
The code forms a ratio of aggregate means, supplies no paired-owner interval,
and only checks that the denominator exceeds the generic `.05` minimum-gain
floor.

Accordingly, `1.169` says only that this one OLD paraphrase-surface gain was
16.9% larger in A2 than A1. Simultaneously, the canonical frame-surface gain
fell to `0.493` of A1. This endpoint reversal is scientifically useful: it
shows that “retention” is highly rendering/metric dependent and is consistent
with probability redistribution or broad response learning. Because G5 and
G9 fail, the paraphrase gain may include unrelated/global shifts rather than
selective owner memory.

The number also does not instantiate the original semantic meaning of native
G7, which was a later checkpoint after interference sleeps relative to an
earlier checkpoint. Here it compares two separately initialized fresh-base
fits and one added session-5 replay block. Mechanically feeding `1.169` into
`evaluate_gates(..., retention=...)` may make the augmented G7 predicate clear
its `.75` threshold, but that must be reported only as a mechanically computed
**OLD paraphrase-gain ratio**. It cannot support “116.9% of memory retained,”
rescue failed G9/G10/G11/G5, or contradict the 49.3% frame-effect ratio.

For future reports, `old_paraphrase_gain_ratio` would be the unambiguous label;
the canonical frame ratio, paired owner changes, G9/G10/G11/G5, and NEW
specificity supplement should remain adjacent to it.

## Does this change the next architecture or benchmark decision?

**No architecture choice is identified, but this result closes the current
synthetic cumulative-replay cell and reinforces the existing benchmark pivot.**

- Do not select warm-start training, two adapters, a new rank, a new dose, or
  an interleaving policy from this result. Those require a direct matched
  comparison; this run contains none.
- Do not run more unchanged car-frame cumulative fits merely to seek a better
  ratio. The current whole-text frame recipe already shows the conjunction
  that matters: target response survives, roughly half-strength on the
  canonical surfaces, while locality, dose ordering, and abstention remain
  failed.
- Continue the already-motivated move toward grounded, task-aligned records
  and a readout that requires correct later use/non-use. The car diagnostic
  remains useful as a regression/locality panel, not the decisive benchmark
  for the THINK--DREAM--SLEEP claim.
- If the next decision really is fresh-base cumulative versus incremental or
  interleaved replay, run a prospectively matched test with the same OLD/NEW
  token budgets, order/heat controls, multiple optimizer seeds, and an
  unchanged selective endpoint. This result alone cannot decide it.

The evidence ledger should therefore move this slot from “unrun” to
**executed descriptive negative**: joint replay produced simultaneous
bank-associated signal and substantial mixture-associated attenuation, but no
qualified selective coexistence, sequential retention, G3 closure, mechanism
freeze, parenting, H1/H2, or clean-lineage result.

## Allowed and forbidden terminal wording

Allowed:

> A single fresh-base OLD+NEW replay fit showed positive candidate-normalized
> shifts on both synthetic canonical completion panels, retaining 49.3% and
> 53.4% of the corresponding single-bank effects; both signals remained
> nonselective and the native locality/dose/abstention gates failed.

Forbidden:

- “A2 retained 116.9% of OLD memory.”
- “OLD memory survived NEW training.”
- “Cumulative coexistence passed.”
- “The run proves catastrophic forgetting” or identifies its mechanism.
- “No interference” based on the paraphrase ratio.
- Any optimizer-seed generality, H1/H2, parenting, behavioral-use, or
  architecture-freeze claim.
