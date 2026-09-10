# Fresh interpretation A — extractable experiential substrate

Date: 2026-09-08

Status: independent read-only interpretation. No implementation, model work,
or scientific execution.

## Core recommendation

The minimum defensible SLEEP object is a **verified use transition**, not a
raw transcript, generic QA pair, or free model-written principle:

```text
earlier public action/outcome e0
  -> exact later child THINK/action continuation y
  -> public outcome e1 passing a preregistered support rule
```

A single event may support episode-local replay. A generalized rule requires
support from at least two independent episodes or prospective confirmation.

## Evidence is not training dose

Maintain two distinct stores:

- canonical evidence index: one immutable `evidence_id` per valid dispatched
  action/outcome, including failures, with exact life/episode/turn, prompt,
  child response, normalized action, dispatch/reset receipt, public outcome,
  usefulness label, causal parents, and model/tokenizer/template hashes;
- derived training views: each row binds `view_id`, `lesson_id`, ordered
  `evidence_ids`, renderer/version, cue family, prompt/response hashes, loss
  mask, and dose ordinal.

Report unique evidence, supported lessons, compiler views, supervised target
tokens, and exposures separately. Six renderings of one event remain one
experience.

## Minimum supervised target

Supervise only an exact persisted child-generated `THINK_TO_ACT` suffix:

- visible pre-outcome reasoning/prediction;
- exactly one native `ACT:` or typed action envelope;
- terminal EOS;
- an action that was actually dispatched and whose later public outcome
  passed the frozen support criterion.

The outcome, score, parent speech, earlier event, provenance, and prompt
tokens are masked conditioning. Failed actions remain evidence and may be
masked contrast context; they are not positive action labels. Do not train
free principles or generic recall answers in the minimum corpus.

For every accepted target, use a cue ladder:

1. `STATE_ONLY`: current public goal/state, without parent, ledger, brief, or
   source transcript;
2. `EXACT_EVIDENCE`: current state plus the exact earlier public experience;
3. `ALT_EVIDENCE`: the same grounded content with reordered public fields and
   different connective wording.

At higher view counts, add preregistered content-equivalent partial,
contrast/recovery, and second-order renderers. Every view must leave the same
target legal. Preserve the exact native inference template and response-loss
boundary. Add a fixed treatment-independent interface/reasoning anchor pack.

## Diversity versus repetition

Race `1x / 3x / 6x` unique cue views while holding target-token touches fixed:

- `1x`: repeat one renderer six times;
- `3x`: repeat each of three renderers twice;
- `6x`: expose each of six renderers once.

Separately vary total supervised-token exposure at fixed cue diversity. Pick
the smallest view count and exposure passing extraction, behavior, and
preservation gates.

## Assays

1. **Storage/reproduction:** exact-source-prompt target NLL/log probability.
2. **Alternative-cue extraction:** after clean context/KV reset, no ledger,
   RECALL, waking brief, source trace, or parent; freely emit native
   THINK/action under held-out wording/order/partial/contrast cues. Measure
   supported binding, valid dispatch, negative-cue abstention, and
   contradiction handling.
3. **Behavioral use:** fresh homologous tasks with new identifiers and action
   combinations, adapter-only and retrieval-free. Measure first useful
   action, information gain, return/regret, actions-to-success,
   prediction-before-action, and recovery after surprise.

Controls: previous committed child, adapter-off/base, equal-dose repetition,
state-target derangement, action/outcome shuffle, and wrong-life adapter. A
claimed effect should disappear or redirect under binding interventions but
survive matched sham changes.

True delayed retention reserves an early-event sentinel cohort excluded from
later replay. Cumulative replay only tests maintenance under rehearsal.

## Paper transfer boundary

Allen-Zhu and Li support the qualitative claim that fitting source text does
not imply extractability and that diverse wording/order plus the intended
extraction surface can affect accessibility. Their five-biography-plus-
permutation condition moved OOD QA from 9.7% to 96.6%, while a single
permutation could hurt. This motivates a controlled view-dose curve, not an
assumed recipe.

Their mechanism cannot be imported directly: they trained small models from
scratch on 100,000 synthetic biographies, used LoRA later as a QA extractor,
and studied static ground-truth facts. This project adapts an already
post-trained 7B model with all-layer LoRA using correlated, on-policy action
experience. Their name-localization result is not evidence about this
adapter.

## Current-code diagnosis

The active long-life runner calls legacy `compile_sleep` and
`organism_v6.train_adapter`, not `compile_native` and
`train_adapter_v21`. Existing `compile_native` admits loosely on `had_note`,
adds generic recall targets, and drops provenance/type from emitted rows.
`train_adapter_v21` has response-only all-layer training, but reconstructs a
single generic chat turn, truncates targets, silently skips nonfinite batches,
and records attended rather than supervised tokens.

Current own-row absorption, cumulative retention, and format canaries do not
establish extraction/use. Transactional score, behavior/brevity,
native-interface, and generic non-erasure gates remain necessary.

## Falsifiers

- source-row NLL improves but held-out cue extraction does not: fitted, not
  extractable;
- extraction improves but fresh-task action value does not: accessible
  description, not useful experience;
- gain requires textual retrieval, a ledger, waking brief, or source trace:
  contextual retrieval, not parametric extraction;
- gain survives state-target derangement, source shuffle, or wrong-life
  adapter: style/frequency/prior effect, not bound experience;
- diverse views do not beat equal-touch repetition at matched source-row fit:
  no evidence for augmentation in this regime;
- claimed generalization from one favorable event fails prospective
  confirmation: hindsight, not grounded learning;
- interface or generic ability crosses the adverse bound: reject and retain
  the previous child.
