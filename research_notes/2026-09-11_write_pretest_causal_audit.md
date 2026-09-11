# Write pretest: causal audit and bounded interpretation (2026-09-11)

## Verdict

The running A/B/C family is useful as a **descriptive recipe scout**, but it is
not a mechanism-isolating experiment. Running cells may finish unchanged.
Their results must be described as outcomes of bundled recipes, not as proof
that one isolated write ingredient caused the outcome.

This audit changes no corpus, trainer, adapter, benchmark, or GPU job. It
corrects interpretation and two report bugs only.

## What each comparison really changes

| Contrast | Bounded interpretation |
|---|---|
| A vs A_v3 | Two trainer/dose bundles over the same flat legacy strings. Both supervise each whole string; this is **not** target-only loss versus whole-text loss. |
| B vs Bs | Two-scale context plus a second exposure of almost every child target, more items, more tokens, and more steps versus episode-only. It does not isolate local context. |
| B vs B_match | Full B versus a compile-time pre-EOS target-budget-and-row-selection recipe. Realized loss positions, content, exposure distribution, and steps are not exactly matched. |
| A_v3 vs B_match | Different authored targets, source selection, success filtering, context, itemization, EOS count, realized supervised positions, and training geometry. |
| B vs C | Raw child stream versus a narrow selected NOTE/action/reflection QA corpus, with different template, mask, target mass, and itemization. |
| C vs C_tmem | Two large trainer/adapter bundles. It is not an isolated rank, layer, optimizer, or TMEM test. |

The strongest correction is A/A_v3. `compile_legacy` stores each legacy text
as one all-loss span. The v1 trainer also clones the entire input string into
labels. A_v3 therefore changes epochs, maximum length, batching/step geometry,
seed/order, EOS handling, and packing/fallback, but not the claimed header
versus target loss boundary. The queued 1-epoch/3-epoch crossing can describe
epoch sensitivity inside those bundles; it still cannot identify masking.

## Packing, provenance, and interface bounds

- B/C masking is structurally correct: context labels are ignored, targets
  and EOS carry loss, and segment-first labels are masked.
- On the actual node the packing isolation check returned `NOT_ISOLATED`, so
  the trainer safely fell back to one item per sequence. These cells test
  their corpus/trainer recipes under unpacked training; they do not test
  neighborhood packing.
- Default CompilerGym B/C compilation strips parent rows and the stored
  `=== YOU ===` bootstrap/brief block, excludes held-out rows before
  compilation, and takes C actions from executed ledger rows. A's legacy
  synthesized-string scan is a weaker post-hoc protection.
- C's action question omits much of the decision state and its answer is a raw
  action string rather than the complete native `PREDICT:/ACT:` continuation.
  C collapse therefore diagnoses this narrow QA interface, not all
  extractable-memory or QA-shaped writes.
- A duplicated/collided output cannot become evidence without demonstrating a
  single-writer lineage from hashes and timestamps.

## Report repairs

`write_ab_report.py` now:

1. Treats v1 `train_meta.tokens` as the realized count accumulated across all
   epochs instead of multiplying it by epochs again. The unavailable per-pass
   target/total counts are no longer invented.
2. Uses v3 `train_tokens_seen` as realized token-passes when available and
   marks its backward-compatible estimate otherwise.
3. Calls a replicate “collapsed” only against the same-index OFF replicate,
   and only when generation seed, panel identity, and replicate count match.

The old implementation compared every replicate with the OFF *mean*, which
could create or erase collapse flags when OFF replicates differed.

## Smallest safe continuation

1. Let already-running cells finish; add no opportunistic arms.
2. Freeze source corpus, adapter, manifest, probe, and log hashes for every
   completed cell; quarantine collided outputs.
3. Regenerate summaries from raw receipts with the repaired report and label
   all A/B/C inferences as recipe comparisons.
4. Decide whether a new causal cell is worth its GPU cost only after the
   replication readout.

If one new causal contrast is warranted, the smallest honest two-arm design holds source
targets, target exposure count, item count, optimizer steps, post-collate loss
positions, context budget, and unpacked training fixed. One arm repeats the
same episode-conditioned rendering; the other replaces only its second copy
with a local antecedent rendering. A direct conditional read plus the action
interface canary is the readout.

The full C11 guard remains parked and is neither completed nor enforced by
this audit.
