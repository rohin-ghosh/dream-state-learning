# Fresh audit: cumulative memory diagnostic

Date: 2026-09-12 UTC
Audit cut: local `main` at `04f9b788`; no remote/GPU access, model execution,
job mutation, or builder/coordination edit.

## Verdict

**Conditionally adequate for a descriptive, one-seed, synthetic
fresh-base cumulative-replay comparison; inadequate for sequential or
unrehearsed retention, catastrophic-forgetting, pure-interference, H1/H2, or
mechanism claims.**

The supplied design has three distinct fits:

- `A1 = Fit(base, OLD)` (historical; 12,924 items, 9,693 updates),
- `AN = Fit(base, NEW)` (1,536 updates), and
- `A2 = Fit(base, OLD + NEW)` (11,229 updates).

Thus `A2` does not inherit, update, or preserve `A1` parameters. OLD is shown
again to a fresh adapter. The strongest valid result is therefore that one
fresh-base LoRA can **reconstruct/carry both replayed banks at once under the
observed corpus mixture**. Calling that sequential retention or survival of
an old memory through new-only learning would be false.

Subject to the exact-union checks below, `A2 - A1` on OLD and `A2 - AN` on NEW
are useful paired, within-bank descriptions of what changes when the other
bank is added to this specific fresh-base training protocol. They are not
pure interference effects: the cumulative fit has more total updates and
tokens, a different batch/order path, and a different corpus mixture. A
negative contrast may be called a **mixture-associated decrement** (or
operational interference under this exact replay schedule), never forgetting
or an identified interference mechanism.

There is also a prior-evidence blocker to the word *memory*. The locally
preserved A1 fingerprint with these counts and optimizer seed 2 has
`I_d_frame = 1.921469873`, paired-owner interval
`[1.202607550, 2.682502692]`, but frame spill `0.415536920` against the frozen
`.03` ceiling; G9 and G11 fail. If the live manifest hash-binds that exact A1,
it is a nonselective acquisition/frame-habit reference, not a qualified
selective OLD memory. No A2 result can retroactively turn A1 into a selective
memory baseline. It can at most show preservation, reduction, or coexistence
of that measured nonselective signal unless both bank-specific absolute
selectivity requirements are independently met.

At this audit cut, `gpu/astra_memory_cumulative_diagnostic.py`, its focused
test, and a cumulative-diagnostic memo were not present locally under those
names or discoverable by a repository search for the stage names. Therefore
the audit below binds the supplied live-manifest facts and the frozen local
memory-dose definitions, not unseen implementation bytes. A later code audit
must resolve every item in “Implementation acceptance checks”; absence is not
evidence that the live run violated them.

The supplied label `A2` here means `Fit(base, OLD + NEW)`. It must not be
conflated with the older repository campaign label “A2 / CF_r16_b,” which used
a different source family and is explicitly not a material-matched A1-minus-A2
effect.

## Dose arithmetic and the comparison it actually creates

With batch size 4 and three epochs, and assuming no dropped/partial batches or
gradient accumulation, the update counts imply:

| fit | items inferred from updates | updates | share of cumulative items |
|---|---:|---:|---:|
| `A1: OLD` | 12,924 | 9,693 | 86.32% |
| `AN: NEW` | 2,048 | 1,536 | 13.68% |
| `A2: OLD+NEW` | 14,972 | 11,229 | 100% |

The arithmetic is exactly additive: `9,693 + 1,536 = 11,229` and
`12,924 + 2,048 = 14,972`. OLD therefore contains 6.3105 times as many items
as NEW. `A2` has 15.85% more updates than `A1` and 7.3105 times as many as
`AN`. These item counts are not token counts. The historical OLD fit records
749,985 input-token passes and 711,213 shifted supervised-token passes; the
terminal manifest must separately report NEW and both A2 bank contributions.

If and only if A2 contains the exact occurrence multiset of A1 plus AN, with
identical token IDs, labels, weights, truncation outcomes, and three
presentations of every focal row, focal-bank *nominal row/token dose* is
matched for these two comparisons:

- OLD: `A2` versus `A1`;
- NEW: `A2` versus `AN`.

Even then, total optimization heat is not matched. Adding the other bank
changes update count, Adam state trajectory, dropout draws, batch neighbours,
and usually position/order. Consequently the current contrast estimates the
whole operational effect of **adding the other corpus under the implemented
training schedule**, not a content-only or capacity-only interference effect.

## Fixed estimands

Use the frozen memory-dose owner as the unit. For dose-16 owner `i` in bank
`B`, define `x(a,B,i)` as the existing `I_d_frame` primitive for adapter `a`:

```text
  [ON_a - OFF log-odds(correct vs fixed OFF alternative | owner frame)]
- [ON_a - OFF log-odds(same pair | the matched unseen look-alike frame)].
```

The alternative must be selected once under the bank's immutable OFF record
and held fixed for every adapter. Let

```text
M(a,B) = mean_i x(a,B,i),       i = the 16 dose-16 owners in B.
```

The required cross-fit contrasts are paired on the same owners:

```text
D_old   = M(A2, OLD) - M(A1, OLD)
D_new   = M(A2, NEW) - M(AN, NEW)
D_repeat(B) = M(A1_after, B) - M(A1_before, B).
```

Bootstrap `D_old` and `D_new` by resampling owner indices once per draw and
carrying both adapters' values together. Do not subtract separately
bootstrapped marginal intervals. Use the inherited 2,000-draw, seed-0
percentile procedure for comparability and retain full precision. These are
within-bank owner intervals only; they do not include optimizer-seed, source
bank, training-run, or model uncertainty.

Also report the scale-free descriptive ratios
`R_old = M(A2,OLD)/M(A1,OLD)` and
`R_new = M(A2,NEW)/M(AN,NEW)`, with paired-bootstrap intervals, only when the
single-bank denominator is positive, bounded away from zero, and passes the
same absolute selectivity gate. A ratio with a null/negative or G9-failing
denominator is not a retention statistic. The signed paired difference remains
primary.

The earlier W1 design used an 80% relative-carriage ruler. If, and only if,
the live memo bound that ruler before seeing outcomes, report
`M(A2,B) - 0.8*M(single_B,B)` and the per-owner count satisfying the same
inequality. Otherwise show 80% only as a clearly labelled inherited
sensitivity analysis; do not invent a retrospective pass/fail threshold.

## What each comparison can and cannot establish

| question | necessary terminal comparison | maximum valid reading | invalid reading |
|---|---|---|---|
| Was OLD measurably installed in the historical fit? | `A1_before` versus the immutable OLD OFF records, with absolute binding/locality gates | OLD single-bank acquisition under one corpus/seed | long-term or selective memory if spill/G11 fail |
| Was OLD carried in the cumulative adapter? | `A2` versus OLD OFF, plus paired `D_old` and any prebound relative ruler | replay-supported OLD reconstruction/carriage in A2 | survival of A1 weights, unrehearsed retention, or forgetting |
| Was NEW acquired by itself? | `AN` versus NEW OFF, with absolute gates | NEW single-bank acquisition under one corpus/seed | equivalence to OLD learnability |
| Was NEW carried in the cumulative adapter? | `A2` versus NEW OFF, plus paired `D_new` | NEW acquisition/carriage with OLD replayed | forward transfer or isolated proactive interference |
| Did adding NEW reduce the OLD signal? | paired `D_old`, after exact-union and repeat-control checks | mixture-associated OLD decrement for this replay schedule | catastrophic/retroactive forgetting or a capacity mechanism |
| Did adding OLD reduce the NEW signal? | paired `D_new`, after the same checks | mixture-associated NEW decrement for this replay schedule | isolated proactive interference or proof OLD blocked learning |
| Did one adapter carry both? | the **intersection**, not average, of A2's complete OLD and NEW bank gates | descriptive two-bank cumulative-replay coexistence | equal-strength memory, sequential retention, or general coexistence |
| Did A1 “retain” while AN/A2 ran? | `A1_after` versus `A1_before` | evaluator/artifact stability only | a learning-retention result; A1's weights never changed |

The following comparisons are scientifically non-identifying here:

1. `M(A1,OLD)` versus `M(AN,NEW)` cannot compare memory strength or bank
   difficulty: corpora differ by 6.31x in items, their supervised-token masses
   are not supplied, and the content/owners may differ.
2. OLD versus NEW inside A2 cannot establish preferential retention,
   importance, or forgetting. It compares unequal corpora and doses.
3. An item-, cue-, or token-pooled A2 mean cannot establish coexistence. OLD
   would dominate it. OLD and NEW are two co-primary bank endpoints joined by
   an AND rule.
4. `A1_before - A1_after` cannot be used as evidence of memory survival; a
   deterministic static adapter should be byte- and score-identical.
5. `A2 - A1` or `A2 - AN` alone cannot distinguish useful sharing, harmful
   cross-bank gradients, extra update heat, batch order, token normalization,
   or optimizer-seed effects.
6. Equality or a confidence interval containing zero is “no detected
   mixture-associated change,” never evidence of no interference.

## Required terminal evaluation matrix

Score the same frozen cue bytes, candidate bytes, OFF alternatives, and parser
for every cell below. No cell may borrow another bank's OFF through an assumed
equivalence.

| state | OLD panel | NEW panel | role |
|---|---|---|---|
| OFF | required | required | immutable within-bank reference |
| `A1_before` | required | required | OLD acquisition plus NEW cross-bank control |
| `AN` | required | required | OLD cross-bank control plus NEW acquisition |
| `A2` | required | required | simultaneous bank carriage |
| `A1_after` | required | required | full-record repeat/drift control |

`A1_before` and `A1_after` must have identical A1 adapter-tree hash, request
manifest, model/tokenizer identity, OFF arrays, ON arrays, cue order, and
reduced primitives. Teacher-forced scoring here is intended to be
deterministic. A mismatch is `EVALUATOR_OR_CUSTODY_DRIFT`, not biological
forgetting; diagnose it before interpreting `D_old` or `D_new`. Comparing only
rounded headlines is insufficient.

The off-diagonal cells `A1 on NEW` and `AN on OLD` are mandatory. A nominally
single-bank fit that changes the other bank is evidence of cross-bank habit or
shortcut behavior, and weakens any bank-specific acquisition interpretation.
Report full four-colour signed shifts or per-cue total variation in addition
to target-colour shifts, because the preserved prior audit showed that a large
“spill” number can include broad colour-prior redistribution; it does not by
itself identify owner-level leakage.

## Terminal statistics and unchanged controls

For each adapter-by-bank cell report, at full precision:

- all 1,313 expected cue records, 64 owners, and 16 owners at each dose
  0/1/4/16; no prompt/template is an independent statistical unit;
- dose-16 `I_d_frame` mean, the 16 owner values, and the paired-owner 95%
  interval, with owner-frame term 1 and look-alike-frame term 2 separately;
- correct candidate-normalized probability OFF to ON, raw correct probability,
  candidate-set mass OFF/ON, and the minimum owner mass;
- the complete dose curve at 0/1/4/16 and the unchanged G10 monotonic/rise
  result;
- frame-spill components separately—unexposed-owner, similar-ID, and bicycle—
  plus their existing equal-stratum mean, not a cue-count-weighted pool;
- G9 frame binding exactly as frozen: paired-owner interval lower bound `> 0`
  **and** frame spill `<= .03`; positive acquisition alone never passes;
- G9 candidate-mass, G11 abstention (where evaluable), in-context/repaint
  revision controls, truncation/boundary counts, and every primitive gate;
- for `D_old`, `D_new`, and any prebound 80% ruler: paired owner values,
  estimate, interval, denominator eligibility, and per-owner counts;
- signed change by target colour and the cross-bank/off-diagonal diagnostics;
  do not explain an absolute spill aggregate with one post-hoc mechanism.

There is only one training seed per state unless the manifest proves
otherwise. The terminal report must say that 16-owner intervals quantify
within-bank item heterogeneity, not seed-to-seed reliability. `A1_after` is a
repeat measurement, not an independent fit. The local dose evidence already
shows large deterministic optimizer-seed dependence on identical bytes, so an
unmatched or unrecorded A1/AN/A2 training seed makes cross-fit contrasts
descriptive across both seed and corpus. Ideally all three are seed 2 to match
the historical A1; regardless, record the actual seeds and never silently
call them matched.

## Implementation acceptance checks for the eventual synced bytes

Before using the terminal report, a code/test/memo review must verify:

1. **Identity and immutability:** exact Qwen2.5-7B base/tokenizer hashes;
   rank/alpha/dropout/target modules; learning rate, optimizer, epochs, batch
   size, max length; A1 source run/seal and adapter-tree hash; no modification
   of A1 or its evaluation records.
2. **Exact corpus relation:** OLD and NEW source hashes; owner, look-alike,
   and cue identity disjointness; `Counter(A2 items) = Counter(A1 items) +
   Counter(AN items)`; no deduplication, silent sampling, loss-weight change,
   padding substitution, or row omission.
3. **Token-dose projection:** per fit and per bank, input tokens, shifted
   supervised tokens, masked tokens, occurrence weights, truncations,
   boundary straddles, batches/epoch, optimizer updates, and any partial batch.
   For shared rows, token IDs/labels/weights must match byte-for-byte between
   single and cumulative fits.
4. **Order and seed:** exact ordered occurrence hashes per epoch, whether A2
   is blocked or interleaved, batch membership, data-loader/dropout/optimizer
   seeds, gradient accumulation, scheduler, and initialization seed. If A2 is
   OLD-then-NEW, recency/order is part of the estimand and must be named.
5. **Evaluation completeness:** the full matrix above; immutable per-bank OFF;
   fixed OFF-selected alternatives; exact cue/candidate order; no missing-value
   zero imputation; A1 before/after raw equality; all stages complete exactly
   once.
6. **Reduction:** paired cross-adapter owner bootstrap, separate bank reports,
   no 1,313-cue pseudo-replication, no OLD-heavy pooled pass, all primitive
   values and failure precedence emitted, and no threshold tuning after
   outcomes.
7. **Custody:** preparation/source/manifest/report hashes, adapter-tree hashes,
   timestamps, stage return codes, cleanup/failure receipts, no partial-stage
   splice, no rescue/refit-to-pass, and preservation of any failure root.

The stage names supplied—`A1_before`, `fit_AN`, `fit_A2`, `AN`, `A2`,
`A1_after`—are sensible only if they implement this full matrix and seal each
stage's inputs/outputs. Stage completion alone does not establish scientific
eligibility.

## Interpretation rules and terminal language

Apply these in order:

1. Any identity, corpus-union, token-dose, stage, or custody mismatch makes the
   affected comparison **non-interpretable**. Preserve the raw result; do not
   repair it by relabelling.
2. Any A1 before/after raw mismatch is evaluator/custody drift. It blocks
   fine-grained cross-fit claims until explained; it is never retention loss.
3. A positive `I_d_frame` interval with spill above `.03` is a
   **nonselective frame/colour response**, not bank memory. Lower spill with
   erased acquisition is also not a selective-memory success.
4. Call OLD or NEW *acquired/carried as a selective binding* only when that
   adapter-bank cell passes its unchanged absolute binding/locality gate.
   Report G10/G11 separately; “guide-like” requires every gate that the live
   memo prospectively assigned to that term.
5. `D_old < 0` or `D_new < 0` with a paired interval wholly below zero is a
   **detected mixture-associated decrement**. An interval overlapping zero is
   inconclusive. An interval wholly above zero is mixture-associated
   enhancement. None identifies why.
6. Use **descriptive two-bank cumulative-replay coexistence** only if the one
   A2 adapter independently meets the prebound absolute standard on both OLD
   and NEW, with no pooled compensation and with qualifying single-bank
   references. If only one bank qualifies, name only that bank. If either
   spills, say “simultaneous nonselective response” rather than coexistence of
   memories.
7. Even the strongest outcome remains one optimizer seed, one unequal bank
   mixture, synthetic planted data, fresh-base replay, and a rank-8
   Qwen2.5-7B diagnostic. It freezes no mechanism and bears no H1/H2,
   parenting, clean-lineage, developmental, or general-memory claim.

## Controls required for stronger claims

To establish **sequential/unrehearsed retention**, start from the actual A1
adapter, train it on NEW with OLD entirely withheld, and score the identical
OLD panel immediately before and after. Pair that path with `A1 -> matched
sham` having the same update count, supervised tokens, lengths, label masks,
and order; also measure NEW acquisition. This is a different experiment.

To isolate **content-specific fresh-base interference**, use heat-matched
arms such as `OLD+NEW`, `OLD+sham_NEW`, and `sham_OLD+NEW`, where shams match
the displaced bank's item count, input/supervised-token mass, format,
marginals, and exact batch positions without carrying its bindings. Run
multiple predeclared optimizer seeds and independent bank draws. Equal-size
or explicitly reweighted banks are additionally needed before comparing OLD
and NEW strength or claiming preferential retention.

## Local evidence anchors

- `research_notes/astra_memos/ASTRA_BANK0_DIAGNOSTIC_2026-09-12.md`:
  authoritative A1 seed-2 counts, endpoint, spill decomposition, bootstrap
  unit, and gate failure.
- `research_notes/astra_memos/ASTRA_PAPER_CLAIM_MAP_2026-09-12.md`, C03:
  all 15 historical A1/A2 artifacts fail G9 and do not form a material-matched
  A1-minus-A2 effect.
- `research_notes/analysis/2026-09-12_w1_cumulative_replay_readiness_audit.md`:
  prior 80% ruler and the established claim boundary that clean-base
  OLD+NEW replay is coexistence/reconstruction, not sequential retention.
- `organism_v6/memory_dose.py` at the audit cut: frozen owner-level
  `I_d_frame`, spill, G9/G10/G11, candidate-mass, and interpretation
  definitions.
