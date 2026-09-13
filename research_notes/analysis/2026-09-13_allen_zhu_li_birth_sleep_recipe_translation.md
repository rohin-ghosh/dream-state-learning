# Allen-Zhu--Li translated to the authored BIRTH + SLEEP recipe

**Date:** 2026-09-13 UTC  
**Scope:** literature-to-current-evidence translation only; no builder source,
fit, job, or scientific claim is changed here.

## Decision

Do **not** change the birth training corpus or fit recipe before the first
bounded fit. The current material already contains the paper's actionable
ingredients. Add one cheap **exact-training-form conditional readout** beside
the already planned held-template readout, so a null can be classified as
failure to fit the supplied map versus failure to extract it under a new
surface.

This is a measurement addition, not another data intervention. In particular,
do not add more paraphrases, increase rank/dose, or alter the loss because of
this paper before seeing the conditional result.

## Direct evidence from the paper

Allen-Zhu and Li study controlled synthetic biographies in small GPT/Llama
models trained from scratch, followed by QA instruction tuning. Their central
separation is important here: above-99% next-token accuracy on the biography
text can coexist with essentially zero QA extraction on people whose QAs were
not used for tuning. Exact source fit is therefore not evidence of accessible
knowledge.

Changing the *encoding data* changes this sharply. Five varied biographies per
person, with different wording and sentence order, raised held-person QA from
`9.7%` to `96.6%` in one reported comparison. Repeating full entity names and
permuting attribute order also helped. Mixed training on biographies and QA
forms yielded `86.6%` and `77.7%` held-person QA in the two reported dataset
families. The paper's mechanistic probes associate this with facts becoming
available earlier and more directly from the entity-name representation. See
the [paper](https://arxiv.org/abs/2309.14316) and especially Results 1--5.

Those are direct results. They do **not** show that the same recipe works for
repeated rank-8 LoRA writes into a pretrained 7B instruction model. They do not
study conditional action policies, old/new retention, locality, child-authored
experience, or lifetime learning. Their LoRA sweeps are downstream QA-tuning
sweeps, not evidence for our rank, learning rate, or sleep dose.

## Smallest valid inference for this repo

The useful prior is not merely "paraphrase more." It is:

> At the time a relation is written, expose its stable key through more than
> one presentation and jointly expose the form in which it must later be used.

That recommendation applies only while every rendering preserves the complete
condition--decision relation. Arbitrary rewriting can strengthen a global
habit while erasing the condition. The paper itself reports that one weak
permutation condition hurt, so augmentation is not automatically beneficial.

## Ingredients already present

| Paper-motivated ingredient | Current repo realization | Evidence/status |
|---|---|---|
| Several views of one relation | BIRTH repeats each PROSPECT semantic source through four train templates and each REVISE source through two; held templates are disjoint. | CPU/native corpus audit passed; fit pending. |
| Stable key stated explicitly | Every row repeats the visible CASE/instance and all decision-relevant named fields rather than relying on pronouns or paragraph position. | Audited for omitted-factor shortcuts. |
| Encode knowledge together with its use form | BIRTH targets are already native-use continuations: `PREDICT`+`ACT` or `COMPARE`+`POLICY`+`NEXT`. There is no late biography-to-QA conversion stage. | Stronger alignment to future readout than narrative-only training, by design; result pending. |
| Cross counterconditions | PROSPECT crosses belief x goal; REVISE crosses expected x observed x prior. AUTH and DERANGED have identical inputs and complementary conditional targets. | Prevents a constant answer from passing. |
| Mix knowledge with other capabilities | Every eight-row optimizer group contains conditional pairs plus truthful addition and copy anchors. | SEQ-113 independently showed that distinct-source interleaving was binding: FOUR_VIEW achieved memory `16/16` and old action `32/32` for all three optimizer seeds, while SINGLE_VIEW failed jointly on one seed. This remains one authored fact world, not birth evidence. |
| Preserve old material during later writes | The provisional SLEEP recipe replays old material. | SEQ-118 retained all `64/64` old-bank readout decisions with replay versus `25/64` without, while both acquired the newest bank `32/32`; one authored seed and unequal new-fact dose. |
| Separate fit from extraction | Q0 already requires exact and held surfaces plus locality. BIRTH has train/dev source and template separation in its corpus/scorer. | The currently stated `384`-call birth plan reads only the `128` dev cases over OFF/AUTH/DERANGED, so the train-form half is not yet executed. |

## The one cheap missing assay

Freeze one exact training rendering for each unique conditional semantic
source:

- `16` PROSPECT sources;
- `32` REVISE sources;
- `48` exact conditional requests per state;
- OFF, AUTH, and DERANGED = `144` extra greedy calls, using the existing strict
  scorer and the same `64`-token ceiling.

Interpret each operation separately rather than pooling its unequal
denominators:

| Exact train form | Held templates | Interpretation |
|---|---|---|
| low | low | acquisition/source-fit failure; do not blame extraction |
| high | low | stored in its fitted surface but not extractable under new wording/identity |
| high | high, locality fails | accessible but unscoped/globalized policy |
| high | high, locality passes | supplied conditional policy installed; still not learning-to-learn |

If generation is unexpectedly ambiguous, teacher-forced gold decision margin
or target NLL on the same 48 prefixes is a secondary diagnostic, not a
replacement success metric.

## Relation to SEQ-113, SEQ-118, and Q0

SEQ-113 already says the current interleaved writer can fit authored facts,
extract them through held lexical forms, and retain one rehearsed old action.
SEQ-118 says allocating fixed later-write budget to replay can prevent old
authored facts from disappearing. These license **provisional ingredients**,
not the claim that SLEEP learns usable conditional cognition.

Q0 remains the tighter mechanism gate because it tests complementary action
maps on identical prompts, exact and held forms, and wrong-condition locality.
The birth fit should proceed because it is already use-shaped and fully
crossed; its exact-form assay tells us where a failure occurs. A favorable
birth result remains Level 1 **trained** behavior. Whether that birth makes the
child **learn** better requires the separate birth-disjoint Level-2 sample.

## Bottom line

Allen-Zhu--Li supports the direction already implemented: varied, explicit,
use-shaped, interleaved encoding. It does not justify another pre-fit recipe
change. Preserve the frozen birth fit, add the `144`-call exact conditional
panel, and use exact/held/locality outcomes to decide whether the next repair
belongs to storage, extraction, or selectivity.
