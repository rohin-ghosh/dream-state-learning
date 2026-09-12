# Independent audit: node-2 seed-1 child-frame writer snapshot

Date: 2026-09-12
Scope: read-only scientific audit of
`/localhome/local-rohing/v6_out/memory_dose_S1/report` and its recorded
corpus/trainer metadata. No model, GPU, queue, adapter, or running-job state
was changed.

Status: **exploratory diagnostic, incomplete snapshot**. This note authorizes
no scientific claim, implementation, release, or promotion.

## Verdict

The available seed-1 snapshot independently supports only the narrow result
already seen at seed 0: the rank-8 writer can strongly move the planted-colour
completion under the matching canonical cue, but the movement is not selective.
The child-`a` cell reaches `0.822` completion and a positive owner-minus-lookalike
contrast, while its frame spill is `0.423` against a registered maximum of
`0.03`. This is a broad completion habit with an owner-conditioned component,
not a usable memory writer.

The snapshot does **not** replicate the seed-0 ordering. On seed 0 the synthetic
reference F was stronger than child `a` (`0.913` versus `0.628` completion); on
this node-2 seed-1 snapshot child `a` is stronger than F (`0.822` versus `0.451`).
The inversion cannot presently be assigned to material seed or child prose:
the byte-identical seed-1 F corpora produced `0.830` completion on node 1 and
`0.451` on node 2. Cross-node swaps and refits must localize that run effect
before any bridge comparison is promoted.

This is not q11 confirmation. The report currently contains only F and child
`a`; seed-1 `t` has not been fitted or reported. The q11 preregistration names
only seed-1/2 `t` versus `b` as confirmation.

## Snapshot identity and completeness

At inspection, `summary.md` was 8,971 bytes, last modified
`2026-09-12 00:45:18 UTC`, SHA-256
`d0613e9e3055ec44b158c519ca67482eb191be840500da827276511ffd1624f3`.
`report.json` was 75,182 bytes, SHA-256
`3c83699ceed094ae4022e8c63d98a7ceac8d3ce5d3e5ac2c9e9e4a6e77e486ed`.

There are exactly six eval artifacts represented: three banks each for
`F_r16k16` and `CF_r16_a`. Bank-0 evals for `b` and `c` exist, but bank-1/2
evals do not, so the pooler correctly omitted both incomplete cells. Adapters
for F/a are complete in all three banks; b/c were complete only in bank 0 at
inspection.

The global `STAGE_CF_FITS_DONE` marker nevertheless exists. The launcher writes
that global marker after the cells supplied to one invocation finish; split
jobs such as `CF_CELLS=CF_r16_a` can therefore create it before the full default
`a/b/c` family is complete. It is not a valid suite-completion receipt. Future
automation should use cell/bank-scoped receipts or verify the expected eval
manifest rather than trusting this marker.

## Numerical cross-check

These are the displayed per-bank values at dose 16:

| cell | bank | completion OFF -> ON | owner contrast, nats | frame spill |
|---|---:|---:|---:|---:|
| F | 0 | 0.260 -> 0.379 | 1.174 | 0.349 |
| F | 1 | 0.241 -> 0.719 | 1.101 | 0.307 |
| F | 2 | 0.254 -> 0.254 | 0.004 | 0.137 |
| child `a` | 0 | 0.260 -> 0.680 | 1.511 | 0.393 |
| child `a` | 1 | 0.241 -> 0.880 | 1.734 | 0.360 |
| child `a` | 2 | 0.254 -> 0.908 | 3.599 | 0.517 |

Independent arithmetic over the displayed bank cells reproduces every pooled
point estimate (rounding aside):

- F completion: `(0.379 + 0.719 + 0.254) / 3 = 0.4507`, reported `0.451`.
- F contrast: `(1.174 + 1.101 + 0.004) / 3 = 0.7597`, reported `0.760`.
- F spill: `(0.349 + 0.307 + 0.137) / 3 = 0.2643`, reported `0.264`.
- child `a` completion: `(0.680 + 0.880 + 0.908) / 3 = 0.8227`, reported
  `0.822`.
- child `a` contrast: `(1.511 + 1.734 + 3.599) / 3 = 2.2813`, reported
  `2.281`.
- child `a` spill: `(0.393 + 0.360 + 0.517) / 3 = 0.4233`, reported `0.423`.

The report's paired owner-bootstrap intervals are positive for the pooled
contrast (F `0.395--1.191`; child `a` `1.374--3.303`, 48 dose-16 owners each),
but these intervals condition on the fitted adapters. They do not cover
material-seed, generation, training, GPU, or node variability. The direct
cross-node F discrepancy demonstrates that this omitted uncertainty is large,
so the intervals cannot support a population or replication claim.

Raw cue-level recomputation was not completed in this audit: the remote-data
policy permitted reading the existing report and aggregate metadata but denied
export of newly derived cue-level results. Accordingly, the arithmetic above
checks report aggregation, not an independent reimplementation of cue scoring
or bootstrapping.

## Selectivity diagnosis

Both cells fail the actual memory gate by a wide margin:

- F has positive pooled owner contrast but `0.264` spill (`8.8x` the `0.03`
  limit).
- child `a` has the larger contrast and completion, but `0.423` spill
  (`14.1x` the limit).
- Seed-1 F bank 2 is effectively a null write at the owner cue
  (`0.254 -> 0.254`, contrast `0.004`), while the other two F banks move.
- Neither cell learns abstention: `P(" not")` is approximately zero on
  unsupported frames.

Thus a higher canonical-cue completion score tracks a stronger global frame
habit at least as much as selective owner binding. Owner-minus-lookalike
contrast alone is insufficient: the adapter can retain an owner-conditioned
component while moving unsupported owner, bicycle, and unexposed frames by
large amounts.

## Corpus, dose, and provenance audit

The completed F/a cells are tightly matched on several important quantities:

- 420 synthetic source events and 420 unique event IDs per bank.
- 5,376 fact renderings, 1,344 lesson items, and 4,096 colour-balanced filler
  items per bank.
- occurrence-preserving writer, chronological ordering, rank 8, learning rate
  `1e-4`, three epochs, batch size 4, train seed 0.
- 250,000 HF-token corpus budget per bank and about 750,000 actual input tokens
  over three epochs (`749,964--750,000`).
- zero recorded token-boundary straddles; examples are padded as distinct batch
  rows, not concatenation-packed, so this trainer has no cross-example packing
  attention path.
- Adapter `corpus_sha` and `items_sha` match the corresponding corpus metadata
  for every completed bank.

But F versus child `a` is a whole-rendering-package contrast, not an isolated
authorship or semantic-restatement contrast:

- F uses 16 total repetitions cycling across 16 synthetic templates; `a` uses
  16 frozen-child perceptions and the harness appends the canonical endpoint
  every time.
- `a` is therefore not unrepaired self-authorship and not lived child
  articulation. The source events are researcher-planted and disposable.
- Full-token loss is used on the child prose and appended endpoint.
- Relevant content size differs: F records about `219--221k` content tokens per
  bank; child `a` about `202k`. Token-budget padding consequently adds roughly
  `3.4--3.6k` generic filler items to `a` versus `2.1--2.2k` to F.
- Total and supervised tokens are close, but item count and optimizer-step
  count are not: F has `12,924--13,016` items and `9,693--9,762` steps; `a`
  has `14,242--14,388` items and `10,683--10,791` steps. That is a roughly 10%
  step-count difference at fixed token exposure.

The child generations are retained and hashed. Each bank has 336 events and
5,376 renderings; distinctness is `0.871--0.882`, exact within-event echoes are
zero, planted-colour drift is `0.016--0.018`, and no line was padded. However,
these seed-1 corpora were built before the colour/owner/relation mention fields
were added to the aggregate diagnostics, so those fields are absent. A frozen,
pre-result stripping/reanalysis path is required before making any semantic
claim about what child `a` wrote. For q11 specifically, names-both must be
recomputed from the retained raw b/t generations with the preregistered
denominator and blinded semantic audit.

The artifacts record model name, prompt text inside `generations.json`, corpus
and item hashes, train seed, hyperparameters, and source event IDs. They do not
record a git commit, exact model/tokenizer revision, node/GPU identity, CUDA
determinism settings, or environment lock in the trainer/report metadata. Given
the measured cross-node divergence, those omissions are now scientifically
material.

One reporting defect should be fixed before any table is reused: the snapshot
summary header says `token budget 65536`, inherited from the base corpus index,
while the F/a corpus files record the actual bridge budget of `250000` HF
tokens. The trainer then consumes about 750k input tokens over three epochs.
The cell metadata is correct; the report-level header is misleading.

## Cross-seed and cross-node interpretation

| run | F completion / contrast / spill | child `a` completion / contrast / spill |
|---|---|---|
| seed 0, node 2 | `0.913 / 2.836 / 0.427` | `0.628 / 1.797 / 0.292` |
| seed 1, node 2 | `0.451 / 0.760 / 0.264` | `0.822 / 2.281 / 0.423` |

The supported statement is: both material runs show canonical-cue assimilation
with large unsupported spill, and the F-versus-child ordering is unstable. Do
not say child prose replicated, outperformed synthetic writing, or closed the
bridge.

More strongly, the exact seed-1 F corpus bytes produce very different outcomes
on the two nodes (`0.830 / 2.013` on node 1 versus `0.451 / 0.760` on node 2).
The bank-2 final train loss is also higher on node 2 (`1.3072` versus `1.2201`),
but loss alone does not identify whether the discrepancy arises during fitting
or evaluation. The already-queued adapter-swap, same-node re-evaluation, and
same-seed refit tests are the correct next checks. Until they land, do not pool
nodes or treat nominal train seed 0 as deterministic replication.

## Permitted conclusion and next action

Permitted now:

> On a second synthetic material seed, canonical completion training again
> produced a recoverable owner-conditioned component, but neither the
> synthetic nor child-rendered writer was selective; F-versus-child ordering
> and byte-identical F outcomes were unstable across runs/nodes.

Not permitted: selective memory, self-authored memory, learned parenting,
seed-1 confirmation of q11, or a child-prose advantage.

Highest-value immediate action is diagnostic, not another representation
sweep: finish the byte-identical cross-node swap/refit localization, then let
the already-running b/c suite finish without changing it. Only after training
and evaluation reproducibility are bounded should t be interpreted under the
q11 preregistration or a bridge result be used to choose the next writer.
