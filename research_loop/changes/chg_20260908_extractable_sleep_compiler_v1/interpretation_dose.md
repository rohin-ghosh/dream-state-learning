# Fresh interpretation B — sleep cadence and dose causal design

Date: 2026-09-08

Status: independent read-only interpretation. No implementation, model work,
or scientific execution.

## Bottom line

Existing large-one-shot versus periodic results do not identify a frequency
effect. They vary writer, trainer, corpus, optimizer dose, seeds, evaluation
RNG, and the data-generating policy. The valid statement is narrower:

> A 12,031-row pooled `compile_native` + v2.1 one-shot configuration often
> scored below base, while periodic old-compiler/v1 lives were initially
> positive and became materially harmful late in 3/9 lives. Frequency is not
> isolated.

## What cadence changes in the current system

1. **Availability:** more sleeps deploy weights and waking briefs sooner,
   create more gate decisions, and expose later wake episodes to them.
2. **Future evidence:** earlier adapters and briefs alter later thoughts,
   actions, outcomes, notes, and recalls. A no-sleep arm therefore produces a
   different ledger.
3. **Rendered views:** periodic compilation preserves transient selections
   and generated principles/briefs that one terminal compile may omit.
4. **Replay weighting:** surviving views encode semantic dose that is not the
   same as unique evidence count.
5. **Optimizer work:** corpus size, epochs, batch size, truncation, loss mask,
   target tokens, and updates differ across the compared recipes.
6. **Initialization/RNG:** every sleep initializes a fresh LoRA from base; old
   v1 has no trainer-seed receipt, and v2.1 does not record its seed.
7. **Gate paths:** candidate selection and rollback change which adapter
   generates later experience.

The current long-life compiler also recompiles the full ledger, has
occurrence-aliasing and unseeded generation risks, and allows rejected sleeps'
corpora/briefs to affect later states. These are alternative causal paths.

Because every accepted sleep trains a fresh LoRA from the clean base, discarded
intermediate adapters do not directly accumulate into the terminal weights.
If final corpus, row order, initialization, trainer, dose, and RNG are exact,
there is no useful separate “many clean-base writes” endpoint: earlier writes
matter only through later experience, compilation, briefs, or selection.

## Stage 1 — frozen-ledger decomposition

First bind one writer; do not compare the old life path with the intended
native writer. Use two frozen ledger roots crossed with two explicit training
seeds. Prefer nested 300- and 1,200-evidence sets and defer 12k until justified.

Within each block train:

| Cell | Evidence | Corpus construction | Final optimizer budget |
|---|---:|---|---|
| `L1-R` | 300 | one terminal render | replay-weighted to match `H1` |
| `H1` | 1,200 | one terminal compile | natural |
| `H1-R` | same 1,200 | exact H1 rows repeated/reweighted | match `H4` |
| `H4` | same 1,200 | four chronological snapshots preserving historical views | natural, matched to H1-R |

Match initialization seed within blocks and randomize execution order. Record
model/tokenizer/template/source/corpus/ledger hashes, compiler and trainer
seeds, evidence IDs, view IDs, loss-bearing target tokens, optimizer updates,
and exact row order.

Evaluate every adapter and base on the same programs and four fixed inference
seeds. Primary outcome: paired task score over base. Secondary: chunks per
episode, DONE-first, valid action, source-row NLL, and held-out-cue NLL.

Contrasts:

- `H1 - L1-R`: unique-evidence breadth at fixed optimizer dose;
- `H1-R - H1`: replay/update-token effect at fixed evidence/views;
- `H4 - H1-R`: historical-view composition at fixed evidence and dose;
- `H4 - H1`: total frozen-ledger compiler-cadence effect.

This is sixteen moderate fits: four cells x two ledger roots x two training
seeds.

## Stage 2 — prospective total cadence effect

Only run if a frequency claim matters and Stage 1 identifies a viable writer.
Randomize matched life pairs:

- `K4`: sleeps at episodes 32, 64, 96, 128;
- `K1`: no write or sleep brief before episode 128; one terminal sleep.

Start with four paired life seeds and extend to eight only under a frozen stop
rule. Match program order, occurrence-aware generation seeds, trainer-seed
schedule, writer/trainer/rank, probe seeds, gates, and episode budget. Probe
both arms every 32 episodes.

At episode 128, also train a standardized one-shot adapter from each K4
ledger. Then:

- natural `K4 - K1`: total sleep-package cadence including changed evidence,
  briefs, view history, availability, and selection;
- standardized one-shot `K4-ledger - K1-ledger`: future-evidence component
  under a common terminal writer;
- natural `K4 - standardized K4-ledger`: historical rendering/availability
  conditional on the same periodic ledger;
- checkpoint AUC: value or harm from earlier availability.

Without a brief-only arm, call the result sleep-package cadence, not
weight-update cadence.

## Replication and stopping

Use a practical margin of 0.03 with the training block/root as the inferential
unit, never probe programs or checkpoints.

- interim at four blocks/pairs, maximum eight;
- interim benefit/harm only if a two-sided 99% paired interval lies wholly
  above +0.03 or below -0.03;
- final practical benefit/harm only if the 95% interval lies beyond the
  relevant margin;
- equivalence only if the final 90% interval lies inside [-0.03, +0.03];
  otherwise unresolved;
- safety-stop after two independent blocks with adapter-minus-base <= -0.10,
  chunks/episode below half base, or DONE-first collapse.

Do not escalate to 12k until the matched 300/1,200 comparison is unresolved
or shows a monotone dose signal.

## Reusable and non-reusable evidence

Reusable: completed R2 ledgers and chronological corpora for old-writer
conditional analysis; verified nested existing corpora; base panels and
trajectories for variance/safety calibration; source hashes and trainer
receipts.

Not confirmatory: old v1 adapters for a v2.1 claim; large one-shot cells as
periodic comparators; standalone probes without seeded generation; R2
adapter-off probes as no-sleep counterfactual lives; own-row absorption or
cumulative retention as frequency evidence.

## Falsifiers

- identical terminal corpus/seed producing different clean-base terminal
  adapters falsifies assumed statelessness/determinism, not evidence for
  useful sleep frequency;
- large-evidence harm requires `H1 - L1-R < -0.03` beyond uncertainty;
- replay harm requires `H1-R - H1 < -0.03`;
- historical-view benefit requires `H4 - H1-R > +0.03`;
- “frequent sleep is better overall” requires prospective `K4-K1 > +0.03`;
- mediation by improved future evidence requires standardized K4-ledger
  adapters to beat standardized K1-ledger adapters;
- safe ungated periodic old-writer sleep is already falsified by late harm in
  3/9 lives.
