# Blinded pre-result audit: CF_r16_t/u

Date: 2026-09-11 (America/Los_Angeles)

Status: read-only scientific audit at repository `590be6ed`, after the q11
preregistration (`d95f22dc`) and implementation (`e882a68d`) but before reading
any `CF_r16_t/u` generation, corpus, fit, evaluation, or report result. I did
not execute a model or GPU. The local checkout contains the seed-0 summaries
for F/a/b/c but no raw seed-0 child-frame run directory, so the actual
generation-to-bank joins, hashes, budgets, and adapter identities remain
uncleared here.

## Verdict

The generated data can remain a useful mechanism scout, but the currently
queued `report` command is **not a q11 confirmatory report**. Seed 0 is
exploratory by preregistration, and the recorded queue runs t/u only on that
seed before its report. More importantly, the present extractor and report do
not implement several frozen q11 endpoints and uncertainty rules. A landed
generic bridge table must therefore not be assigned B/S/N or used for the
q11 permitted claims.

No fatal defect is evident in the basic t/b rendering, corpus, training, or
teacher-forced evaluation path. The raw JSON is potentially sufficient for a
later blinded re-analysis. The endpoint/report mismatches below are fatal to
claiming that the queued report itself executes the preregistration.

## Exact causal questions

- `t-b` changes the **whole positive rendering prompt**. Both arms use the
  frozen named base model, the same planted events and nominal event seeds,
  R=16, an occurrence writer, no negative rows, the same requested corpus
  budget/rank/training seed within a run, and the same evaluation bank. The
  old free-aspect request is replaced, not merely supplemented, by a factual
  restatement request. Thus the estimand is the effect of the complete prompt
  procedure, including its changed prose length, filler displacement, item
  count/optimizer steps, format compliance, repair, and one realized
  generation/fit. It is not the isolated effect of owner mention, relation
  mention, or a mediator.
- A positive `t-b` can support only: immediate instruction-conditioned
  generation made this repaired, bounded write corpus more compatible with
  canonical owner-colour completion on these synthetic materials. The lesson
  is present on every authoring prompt. There is no lesson-free authoring
  transfer probe, retained writing behaviour, adaptive parent, learned child
  checkpoint, or deployment learning curve. It cannot show that the child
  learned how to remember, that parenting survived removal, or that
  self-authorship caused storage.
- `u` is secondary. Relative to c it changes both positive and absence
  prompts and independently regenerates both corpora. Relative to t it adds
  negatives but does not reuse t's exact positive bytes. Neither `u-c` nor
  `u-t` isolates negative teaching or negative dose; u is a composite variant
  check only.

Nominal event seeds are variant-invariant, but historical b and newly queued t
are generated in different calls/model loads. Existing b/c artifacts already
show that identical positive prompts and per-event seeds did not yield matched
texts. Q11 correctly conditions its owner intervals on the realized
generation and fit; it does not cover generation, training, node, or material
seed randomness. “The prompt caused” must retain that conditional scope unless
generation-run effects are independently excluded.

## Authorship, repair, and loss

For b/t (and c/u positives), the harness supplies the verified observation and
the exact answer in the generation prompt. `split_child_rendering` removes an
exact terminal canonical sentence; on a miss, `_complete_lines` retains the
child text and `render_child_frame` appends the harness-computed correct
target. Short output is re-prompted once and then padded by repeating usable
lines; completely empty output becomes R target-only repaired rows. Negative
rows are repaired analogously.

Every child-frame item is bare `context + target` with
`mask_context=False`; `encode_item` therefore places loss on all child prose
and on the canonical ending. The generation prompt and authorship metadata are
absent from training. On an exact hit the trained bytes equal the normalized
child line; on a miss the correct ending is researcher-supplied. Given equal
bytes the trainer cannot detect who wrote the ending. “Child-authored frames”
must therefore be read as frozen-model-generated prefix prose under a
harness-labelled and repaired frame, not autonomous perception or provenance.

## Preregistered endpoints versus executable endpoints

1. **Names-both mismatch (claim-blocking).** Q11 freezes 5,376 intended raw
   line slots per cell/bank, missing slots scored zero, malformed/extra output
   retained and flagged. Both `child_diagnostics` and
   `cf_mention_rates.py` instead score the consolidated `generations.json`
   `lines`: retries can replace missing lines, padding duplicates a usable
   line into missing slots, and extra raw lines are truncated without an
   extra-line rate. Consequently the current `relation_mention_rate` is not
   the frozen B endpoint. No current code gives its per-bank t-b interval.
2. **Names-both is only lexical co-mention.** The matcher correctly uses
   case-insensitive whole words and strips an exact terminal frame. It does
   not establish the owner-colour relation, correctness, non-negation, or
   grounding. A malformed suffix that escapes exact stripping contains both
   answer words and passes; a wrong relation or an invented second colour can
   also pass. Both words and the exact relation are already exposed in the
   prompt. The proxy is valid only as a manipulation check for co-mention,
   never as a mediator or semantic result. The preregistered reproducible,
   blinded 100-line-per-arm-per-bank semantic/stripping audit has no sampler,
   manifest, or report path yet.
3. **Storage/reference decisions absent (claim-blocking).** The unchanged
   evaluator does provide, per dose-16 owner, candidate-normalized planted
   colour probability at the bare canonical prefix, plus the owner versus
   look-alike log-odds interaction in nats and raw P(` not`). These are
   teacher-forced four-colour candidate measures, not open-ended exact-sentence
   generation. But `report_command` never forms owner-paired `C_t-C_b` or
   `C_F-C_t`, one-sided bounds, the 0.05 non-inferiority test, t-b specificity
   or false-abstention contrasts, or spill bounds.
4. **Wrong resampling/aggregation for q11 (claim-blocking).** The current
   generic report uses 2,000-draw two-sided percentile bootstraps on a flat
   list of owner values. Banks within a material seed deliberately reuse the
   same owner pool, with reassigned dose/colour, so bank-owner rows are not
   independent. Q11 requires 10,000 paired owner-cluster draws preserving
   cross-bank owner dependence, bank means within seed, equal seed weights,
   seed-1/2 confirmation, leave-one-seed-out summaries, conjunction decisions,
   and one-sided bounds. There is no cross-run q11 analysis implementation.

## Integrity conditions not cleared by the repository

- On-disk generation reuse validates only variant, R, and negative count. It
  does not bind bank/arm/sleep event identities and colours, rendered prompt,
  model revision, tokenizer/chat template, software version, node, or sampling
  configuration. `generations_sha` covers only positive parsed lines, not raw
  output, prompts, negative rows, or model identity. The q11 archive contract
  therefore requires a direct raw-artifact join/hash audit before use.
- The runbook reuses an existing corpus based only on requested token budget,
  skips any adapter with `DONE`, and skips an existing eval tag; it does not at
  those resume points rebind corpus SHA to generation SHA, adapter SHA to the
  current corpus/config, or eval to the intended adapter. This is a latent
  stale-artifact risk, not evidence that this queue is stale.
- `CF_ALLOW_OVER_BUDGET=1` is the child-frame runbook default. If any t/u
  content itself exceeds 250k tokens, it is still trained, breaking the
  nominal budget match. Even below budget, changed prose length changes the
  number of short filler items and optimizer steps. Actual corpus/train token
  counts, item counts, truncation, rank, seed, final checkpoint, model revision,
  node, and all SHAs must be disclosed rather than inferred from the command.
- Seed 1 and seed 2 are distinct material seeds, but each run couples material,
  generation, and training seed. The three banks inside a seed are dependent;
  the cross-node seed-1 a/b/c run is a node diagnostic, not replication and not
  evidence against a t-specific node interaction.

## Pre-result claim gate

The queued seed-0 report may be described only as exploratory. Do not call B,
S, N, “landed,” grounded relation restatement, a clean negative ablation,
parenting, transfer, retention, or learned self-improvement from it. Before
any q11 decision, freeze an analysis that implements the raw-slot endpoint and
semantic audit, paired arm contrasts, shared-owner 10,000-draw bootstrap,
seed-balanced one-sided decisions and all guardrails; then verify the archived
artifact joins/configs without excluding or rerunning outcomes. If that cannot
be done blind, report the generic outputs as exploratory mechanism diagnostics
and retire the confirmatory wording.
