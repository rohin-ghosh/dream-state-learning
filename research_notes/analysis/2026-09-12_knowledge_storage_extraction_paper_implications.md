# What *Knowledge Storage and Extraction* actually implies for SLEEP

Date: 2026-09-12

Source: Allen-Zhu and Li, *Physics of Language Models: Part 3.1, Knowledge
Storage and Extraction*, arXiv:2309.14316v3 (2024).

Status: literature-to-design audit only. No writer recipe, source, job, or
claim is changed or authorized here.

## The useful result

The paper separates **fitting source text** from **extracting its knowledge in
a different query form**. In its controlled biography setting, a model can
memorize the training sentences while later QA remains near zero. Diversity at
the original encoding stage changes this sharply: multiple biographies,
sentence permutations, and repeated full names make later extraction much
easier. One reported comparison moves held-person QA accuracy from `9.7%` for
single biographies to `96.6%` for five diverse entries. Mixed biography+QA
training also teaches a common extraction convention before every person's QA
has been seen.

This is directly relevant to DREAM/SLEEP at the level of **data geometry**:
the sleeping writer should not see only one canonical narration of an event.
It should repeatedly see the same grounded relation through several uses, with
the stable situation/event key made explicit in every view.

## What it does not prove for this project

The headline experiments pretrain small controlled models from scratch and
then instruction-finetune QA. They do not demonstrate repeated deployment-time
LoRA writes into a 7B instruction model, selective native actions, interface
preservation, old/new retention, or a child-authored experiential compiler.
Their augmentation result is therefore a strong design prior, not evidence
that paraphrases will repair our writer.

More paraphrases can amplify the wrong thing. Our current failure is not only
poor extraction: the fitted relation spills into the wrong condition. Repeating
an unscoped action sentence in five styles may create a stronger global habit.
Every augmented row must preserve the complete condition--action--outcome
binding and be paired with counterconditions where the action should not fire.

The paper's LoRA rank sweeps also do not select rank 8 or 16 for us. They tune
query/value and embedding ranks inside a different pretrain/fine-tune protocol;
our rank must still be chosen from acquisition, locality, retention, and
interface behavior under the actual cumulative writer.

## Concrete consequences for the current writer ladder

1. **Keep storage and extraction separate.** Score the exact trained
   continuation first, then identity-disjoint renderings, then native action.
   Low train-form loss is never absorption by itself.
2. **Do not add augmentation before localization.** Run canonical semantic W0
   first. Add the registered cross-view `X0` only if the row is stored in its
   training view but not extractable in a fresh view. If locality already
   fails, diversity is not the isolated repair.
3. **Use stable explicit keys.** The paper's repeated-full-name effect suggests
   repeating our opaque situation/event key in every declarative, forward,
   inverse, and connection view rather than replacing it with pronouns or
   relying on paragraph position.
4. **Mix relation and use forms during SLEEP.** Once W0 qualifies, a grounded
   event may be rendered as:

   ```text
   situation + executed action -> public outcome
   situation + desired outcome -> executed action
   situation + candidate action -> predict public outcome
   situation + contraindication -> withhold that action
   ```

   These are not invented facts. They are reversible, provenance-bound views
   of the same public event or explicitly supported countercondition.
5. **Hold semantic exposure fixed in comparisons.** Compare canonical versus
   diverse decks at equal per-binding supervised target tokens and identical
   condition/countercondition balance. Otherwise “diversity” is just more dose.
6. **Test delayed use, not recitation.** The meaningful endpoint remains a
   goal-conditioned native action under a fresh rendering and sterile context.
   Exact sentence reproduction is a diagnostic only.

## Bottom line

The paper supports DREAM as a **grounded view generator** and supports mixed
memory/use forms during SLEEP. It does not support indiscriminate paraphrasing
or relaxing the selective-writer gate. The right loop is:

```text
one immutable public event
-> several reversible keyed views plus counterconditions
-> one conservative cumulative write
-> exact storage, fresh-form extraction, native use, and wrong-condition tests
```

That is already the logic of W0 followed conditionally by X0. The literature
strengthens that order; it does not justify another broad recipe sweep.

