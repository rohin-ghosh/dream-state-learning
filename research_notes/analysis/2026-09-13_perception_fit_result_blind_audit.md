# Result-blind audit: authored perception fit and anchor withdrawal

**Date:** 2026-09-13 UTC  
**Role:** independent watcher-side scientific auditor  
**Experiment:** `perception_fit_20260913_attempt1`  
**State at authorship:** result blind. I did not open or enumerate `run/`, any
worker/controller log, adapter, response, completion, collection, score, or
partial metric. I did not query the live process or GPU. I changed no builder
source, test, model, adapter, job, or device state.

## Bottom line before results

This is a valid, inexpensive **bootstrap/interface diagnostic** if its runtime
receipts close. It asks whether twelve author-written examples make a model
better at turning a visible action, prior prediction, and public outcome into
one exact record, and whether putting a behavioral anchor in the *training
context* changes that behavior after the anchor is removed.

It is worth its registered budget: two 12-update fits and 72 short greedy
readouts, serially bounded by 2,700 seconds on one A40 (at most 0.75 A40-hour).
That is a good information/GPU-hour trade because it can decide whether an
anchor-conditioned birth/bootstrap is worth carrying into later work.

It is not on its own evidence for the Dream--LoRA--Think thesis. It contains no
executed child experience, child-authored memory, DREAM, SLEEP, repeated
consolidation, parent, connected knowledge, traversal, expansion, later action,
lifetime curve, compression, or memory-baseline contest. Do not replicate this
line merely to make it look paper-sized. Replicate only if a large clean effect
would actually change the bootstrap used in the endogenous event-memory path.

## Frozen bytes and material inspected

I inspected only the static registered material:

- remote plan SHA-256
  `f5f2315d5fa35029249f77b075943fa2c0a36b2691037a7700b50cefbe48c837`;
- frozen runner SHA-256
  `f62da57d1a66cd287b72ac8ad8b8724601062813653a63d3dcd6cd8a3b69cd51`;
- frozen CPU-test source SHA-256
  `4d9a1128518944337a63800bae82025763993378c69c94d3608e8fc6bd5dc96e`;
- corpus, RuleGame interface, and trainer source hashes, which match the local
  reviewed bytes: `078ceba0...`, `e6055da4...`, and `7bbf165f...`;
- the four prepared **input** artifacts, whose observed hashes exactly match
  `plan.json`: absent train `f5322f7b...`, present train `d0f4ebcf...`, DEV
  `3c749c6b...`, and calls `dba68677...`.

The inputs contain 12 train and 12 DEV rows in each anchor rendering. Train and
DEV have disjoint row IDs, rendered inputs, exact targets, selected triples,
and selected-event bytes. Both contain the same six intentional semantic cases
twice: matched/mismatched/unavailable crossed with True/False outcome. Train
uses two triples and a one-event template; DEV uses two different triples, a
different wrapper, and a preceding distractor event.

Both fits supervise exactly 372 target-plus-EOS token IDs per epoch and use the
same row order. All context tokens are loss-masked; the native EOS is manually
supervised and `TrainConfig.add_eos=False` correctly prevents a second EOS.
There is no truncation in the prepared encodings. The absent arm has 3,024
total input IDs per epoch and the present arm 3,444, so target exposure is
matched but total context/compute is not. That 420-token difference is part of
the anchor treatment and must not be hidden.

## Exact experiment, in plain language

There are two fresh rank-8 LoRA fits:

1. **fitAbsent:** twelve record examples under Qwen's generic system message;
2. **fitPresent:** the same twelve targets, order, four epochs, and 12 optimizer
   updates, but with this exact system message replacing the generic system:

   > Keep observations, prior predictions, and later outcomes distinct. Report
   > only what the public record supports. Do not invent a prediction when none
   > was stated. Compare an explicit prediction with its matching outcome; do
   > not infer a hidden rule. Follow the requested record format.

The anchor is input context and receives no direct loss. Each fit sees 48 row
presentations, uses rank 8 / alpha 16 / dropout .05 / LR `1e-4`, and starts from
a separately loaded clean base. The response target is one exact JSON record.

There are six immediate DEV cells, each with the same 12 paired public
situations:

| short name | actual cell | weights | anchor at readout |
|---|---|---|---|
| `O0` | `OFF__absent` | no adapter | absent |
| `O1` | `OFF__present` | no adapter | present |
| `N0` | `fitAbsent__absent` | ordinary record-practice adapter | absent |
| `N1` | `fitAbsent__present` | ordinary record-practice adapter | present |
| `P0` | `fitPresent__absent` | anchor-conditioned record adapter | withdrawn |
| `P1` | `fitPresent__present` | anchor-conditioned record adapter | present |

All six readouts use the same LoRA-enabled vLLM engine. OFF supplies no
`LoRARequest`, so the old enabled-versus-disabled engine confound is removed.
Each cell gets a fresh process and engine; generation is greedy with seed 0 and
192 output tokens. Raw captures must close before scoring.

## What the score measures

A row passes only if a strict parser accepts exactly one JSON object with the
four requested keys and all four values are correct:

- `try`: copy the selected executed triple, not the distractor;
- `observed`: copy its returned Boolean;
- `predicted`: copy the explicit pre-action prediction, or `null` when absent;
- `relation`: compute matched, mismatched, or unavailable.

The user prompt itself supplies the complete JSON schema and the relation
definition. Therefore this is not free discovery of a recording ontology. It
is held-wrapper record execution under explicit instructions. A gain can be
format/schema, distractor selection, field copying, null handling, relation
calculation, or some combination. The terminal audit must report those failure
types separately from all-or-nothing accuracy; otherwise a formatting shift can
be misreported as better perception.

## Causal contrasts frozen before results

Use paired row indicators and report both directional flips, not only score
differences. For cells `X,Y`, report `X-only / Y-only / both / neither` and the
net difference `(X-only - Y-only)/12`. The fit is the experimental unit; the 12
DEV rows are repeated measurements, not 12 independent learner replications.
Do not attach a learner-level p-value to them.

1. **Prompt elicitation in the untrained base:** `O1 - O0`.
2. **Ordinary target-practice transfer without an anchor:** `N0 - O0`.
3. **Ordinary target-practice effect while prompted:** `N1 - O1`.
4. **Primary anchor-training increment after withdrawal:** `P0 - N0`.
   This is the cleanest planned contrast because targets, order, dose, model,
   and readout prompt match; the treatment is the exact training-system bundle.
5. **Anchor-training increment while the anchor remains visible:** `P1 - N1`.
6. **Residual readout-prompt dependence:** `O1-O0`, `N1-N0`, and `P1-P0`
   separately. Do not pool them.
7. The descriptive interaction
   `(P0-N0) - (P1-N1)` may localize whether any training-anchor advantage is
   concentrated after withdrawal, but one fit seed cannot support an
   inferential difference-in-differences claim.

Never use `P0-O0` alone as evidence for anchor internalization: that bundles
ordinary target practice with the training anchor. Never use `P1-O0`: that
bundles training, mounted weights, and a live prompt.

## Pre-result engineering classifications

The runner intentionally has `automatic_pass=False`. The following are
interpretation rules, not post-hoc acceptance code or confidence intervals.

### Operational high fidelity

A fitted cell is ready to be considered for a downstream compiler only at
`12/12` strict records, zero length finishes, and no schema/field failure. This
is a deterministic public-record primitive; downstream provenance cannot
safely treat a missed event as a correct memory.

### Directional replication candidate

A cell is merely worth repeating when it reaches at least `10/12`, gets at
least `5/6` on each held triple, covers every one of the six semantic cases at
least once, has no length finish, and obtains at least three more paired wins
than losses versus its relevant comparator. This is an engineering screen, not
a paper claim.

An **anchor-associated withdrawal candidate** specifically requires all of:

- `P0 = 12/12` operational fidelity;
- at least three net paired wins for `P0` over `N0`;
- `P0` no more than one item below `P1`; and
- field-level review showing that the gain is not only removal of extra prose
  while selected-event, observation, prediction, or relation errors persist.

Even this only earns independent fit seeds plus a content-matched anchor
control. It does not earn the word *internalized* in a headline.

An **ordinary bootstrap candidate** requires `N0 = 12/12` and at least three
net paired wins over `O0`. If `N0` and `P0` are both high and differ by fewer
than three net items, the economical reading is that authored record practice
works but the anchor has no demonstrated incremental value.

Treat a fitted state as an **adverse signal** if, under the same readout anchor,
it loses at least two more paired rows than it gains versus OFF, introduces any
length truncation, or creates a systematic schema/field failure absent in OFF.
Because there is no generic locality panel, `no adverse signal here` is not a
general no-harm finding.

## Complete result map

| observed pattern | allowed interpretation | interpretation forbidden |
|---|---|---|
| `O1 >> O0`, fitted cells add nothing | The instruction elicits record behavior in context. | Weight learning, persistence, or a need for bootstrap. |
| `N0 >> O0`, `P0 ~= N0` | Ordinary authored record practice changes immediate prompt-free record behavior; anchor adds no resolved benefit. | Anchor internalization or parenting. |
| `P0 >> N0`, with the strict gates above | The exact anchor-conditioned training bundle improves immediate record behavior after that anchor is withdrawn, on this one corpus/seed. | Semantic anchor internalization, retention, or general meta-cognition. |
| `P1` high but `P0` low | The learned state remains dependent on a live anchor, or the anchor and fit interact. | Parent-absent transfer. |
| `N0` and `P0` both high | The target examples themselves are sufficient for this schema at this dose. | An anchor-specific mechanism. |
| all fitted cells near their OFF counterparts | No detectable immediate benefit from these two 12-row recipes on this DEV panel. | LoRA cannot store the skill; parenting/sleep cannot work. |
| fitted cells worse than matched OFF | This exact tiny-corpus/high-LR bootstrap may interfere with record execution. | General LoRA harm or a failure of experiential learning. |
| only syntax/extra-prose failures improve | Interface discipline improved. | Better event perception or semantic judgement. |
| field copying improves but relation remains wrong | Public-field retention/selection improved, not comparison. | Reflection, belief revision, or connected reasoning. |
| relation improves with correct copied fields | The bounded explicit comparison rule became more reliably executable. | Hidden-rule learning or general reasoning. |
| `P0 > P1` | The live anchor conflicts with the learned behavior or reflects run noise. | Stronger internalization because prompt removal helped. |

## Integrity gates before any interpretation

The terminal reviewer must first establish all of the following:

1. The exact plan, runner, probe driver, corpus/interface/trainer sources,
   model inventory, native environment, and four prepared-input hashes match
   the registered bytes above.
2. Both fits load fresh unwrapped bases; only LoRA A/B tensors are trainable;
   adapters and optimizers are not reused or merged.
3. Each fit contains exactly 12 items, four epochs, 12 optimizer updates, 48
   presentations, zero skipped/nonfinite/truncated/split rows, finite losses,
   the expected token accounting, and one complete rank-8 adapter.
4. The two fits have identical supervised IDs and row order. Report the
   unequal total prompt exposure: 3,024 versus 3,444 IDs per epoch.
5. DEV rows never enter loss or checkpoint selection. Metadata, proofs, case
   labels, target hashes, and DEV answers never enter model-visible text.
6. All eight stages use distinct owned process groups; every worker releases;
   all 72 requests and raw responses are present, immutable, correctly routed,
   untruncated or explicitly counted, and captured before any score exists.
7. OFF readouts genuinely use the same LoRA-enabled engine with no adapter
   request. Fitted readouts load the registered, unchanged adapter.
8. Collection reproduces all six `12` denominators and strict scores directly
   from the raw text. Report raw failure categories and every matched flip.
9. Any timeout, missing cell, wrong mount, source/input mutation, dev leakage,
   selected retry/checkpoint, nonfinite fit, or failed release outranks efficacy
   and makes the run nonreportable rather than a zero.

The nested inherited binding retains the old label
`perception_DEV12_anchor_NO_FIT`, while the top-level frozen scope correctly
states `twofits_sixreadouts_v1`. This is a provenance-label ambiguity, not a
cognitive confound. Do not cite the inherited NO_FIT receipt as attesting or
authorizing the fits; use the top-level plan, runner hash, and builder's standing
authorization. Preserve both labels in the terminal record rather than silently
renaming either.

## Leakage and attribution boundaries

- The anchor gives the desired procedure directly. That is the experimental
  treatment, not hidden-answer leakage, but success is instructed behavior.
- The ordinary user prompt independently supplies the full output schema and
  exact relation mapping in every cell. The anchor does not uniquely teach
  those rules.
- The present training arm replaces Qwen's generic system text and is 35 input
  IDs longer per row. Without an equal-length, content-neutral or scrambled
  system control, `P-N` identifies the **whole exact anchor bundle**, not its
  semantics apart from length, system-positioning, or generic-system removal.
- Train and DEV are disjoint at the recorded source level, but share the same
  six-case grammar and authored construction. Positive transfer is only across
  held triples/wrapper/distractor instances of this schema.
- The records are author-written hypothetical public situations, not outcomes
  generated by a child acting in a world. No result is experiential authorship.
- One immediate readout has no retention interval, competing later sleep, or
  forgetting test. Call it *anchor-withdrawn* or *prompt-free immediate
  transfer*, not persistent memory.
- One fit per arm means optimizer/GPU nondeterminism is inseparable from the
  treatment at the learner level. Greedy repeated rows do not repair that.
- No copy/locality/generic-agent panel exists, so no fit is certified safe as a
  broad birth adapter even if record accuracy is perfect.

## What would be needed for a real internalization claim

Only if the one-root anchor-associated withdrawal candidate is large and clean:

1. repeat at least three independently trained seeds from the same frozen base;
2. add a token-length/system-position matched active-neutral or semantically
   scrambled anchor during training and readout;
3. use new authored templates and domains rather than only new triples;
4. preserve a generic interface/locality panel; and
5. test after intervening unrelated training or sleeps, not only immediately.

Even that would establish durable acquisition of a bounded recording
disposition. To contribute to the actual paper objective, the next bridge must
replace author-supplied rows with a child's own precommitted action and public
outcome, preserve an exact provenance chain through compile/write, withdraw
the source, and show a separate clean actor can use the memory later. That is
the proposed endogenous addressed-event gate, not this bootstrap diagnostic.

## Final budget ruling

**Proceed/finish this already-live bounded run; do not expand it.** Its maximum
0.75 A40-hour is justified by a crisp bootstrap decision. A null or prompt-only
result closes the anchor-fit idea at this dose. A generic-practice result says
use the simpler bootstrap. A large anchor-associated withdrawal result earns a
small controlled replication. In every case, the high-value paper path remains
the endogenous event-row writer and later connected/traversal/lifetime ladder.
