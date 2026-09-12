# Result-blind watcher plan: whole-text CE plus frozen-OFF preservation

**Frozen at 2026-09-12 11:50 UTC, after launch receipts but before either
terminal result was available in the repository.** This is an independent
read-only watcher reduction for node-3 controllers `85200` and `85282`. It
does not authorize, alter, restart, stop, or extend either run.

## Exact experiment being audited

The contemporaneous comparison is:

- control: whole-text CE, preservation coefficient `0`, controller `85200`,
  root `astra_A1_preservation_bank0_ts2_lam0_20260912_attempt1`;
- treatment: the identical whole-text CE plus
  `0.1 * KL(p_OFF || p_current)` at one rotating fixed prefix per optimizer
  step, controller `85282`, root
  `astra_A1_preservation_bank0_ts2_lam01_20260912_attempt1`.

The frozen source is commit
`290a9ea03387176f7ba75478552db3eafa844db2`. The files inspected before
outcomes had SHA-256 values:

- `organism_v6/memory_preservation.py`:
  `a361af202a85e041dad119d57da7a54f583045e9472a358ae8a5efd31a32ef9c`;
- `organism_v6/memory_dose.py`:
  `ab98329c433cb085cd53e1c766db350f1bb0fe2efb9181e24a3678c0d31a76e3`;
- `gpu/astra_memory_preservation_diagnostic.py`:
  `33611bfb9b66c8ce26e6aed3b017b1179cfe4bdc912dc25fa76b738b10ec9c4f`;
- prospective specification:
  `7f7923c288bb2221a61b97f4190154d0a959e8e670f8080ef62d15956912e6b2`.

Both preparation receipts declare the same immutable whole-text corpus,
token order, model inventory, rank 8, optimizer seed 2, and tokenizer
preflight: 12,924 items; 9,693 AdamW updates; 749,985 input-token passes;
711,213 shifted supervised-token passes; 249,995 input and 237,071
supervised tokens per epoch; no truncation or boundary crossing. The only
intended treatment difference is the additive preservation gradient and its
extra compute/cache. This is not compute matched.

The 48 treatment anchors are fixed before training: 16 near-car, 16 far-car,
and 16 far-bicycle prefixes. Their owner IDs exclude all IDs found in the
source inputs and all three banks' native cue owner references. The three
families are interleaved, each receiving 3,231 positions. Their content is
still derived from the old synthetic completion-frame surface. They are not
a test of semantic conditional binding.

## Terminal validity checks

I will accept an arm as terminal only if the captured artifacts establish all
of the following:

1. the controller is terminal, the owned worker group is cleaned, and the GPU
   reservation is released without an undisclosed manual intervention;
2. source, input, plan, anchor, model-inventory, tokenizer-order, and launch
   hashes match the prelaunch receipts;
3. `DONE`, `train_meta.json`, `losses.jsonl`, the 1,313-cue native evaluation,
   report, process/cleanup receipts, and a capture manifest are present and
   mutually consistent;
4. each fit has exactly 9,693 finite loss rows and the exact fixed CE dose;
5. coefficient 0 has `kl=null`, `objective=ce`, no cache, and no anchor visits
   on every step;
6. coefficient 0.1 has anchor index `(step-1) mod 48`, the declared visit
   counts (202 for indices 0--44 and 201 for 45--47), finite KL, and
   `objective = ce + 0.1*kl` on every step;
7. every serialized OFF cue score, cue order, and prompt binding is exactly
   equal between the two new arms. OFF drift invalidates a causal ON contrast;
8. the fresh coefficient-0 ON evaluation is compared to the historical A1
   seed-2 result. Any drift is disclosed, and the new coefficient-0 arm—not
   the historical run—remains the primary comparator.

The historical A1 result is a bridge check only: `I_d_frame=1.921469873`,
owner-bootstrap interval `[1.202607550, 2.682502692]`, and
`frame_spill=0.415536920`.

## Independent reduction fixed before results

All headline quantities will be recomputed from the raw serialized cue
probabilities, not copied only from `report.json`.

For each dose-16 owner, normalize the four color probabilities separately for
OFF and ON. Let `a` be that owner's planted color and let `b` be the strongest
alternative under OFF at the owner's frame. Compute the ON-minus-OFF change
in `log(P(a)/P(b))` at the owner's frame and subtract the same change, using
the same `a,b`, at its look-alike `frame_similar` cue. The mean of those 16
paired differences is `I_d_frame`. Its fixed interval is the percentile
interval from 2,000 seed-0 bootstrap resamples of the 16 owners, matching the
prospective metric.

`frame_spill` is the unweighted mean of three family means:

1. absolute normalized planted-color ON-minus-OFF change at the similar-frame
   control for every exposed owner;
2. absolute normalized planted-color ON-minus-OFF change at the own frame for
   dose-0 owners;
3. absolute normalized planted-color ON-minus-OFF change at the bicycle-frame
   control for every exposed owner.

The unchanged G9 gate passes only when the dose-16 `I_d_frame` bootstrap lower
bound is strictly above zero **and** `frame_spill <= 0.03`. I will also
recompute dose-16 correct conditional OFF/ON probabilities, candidate mass,
the frame `dP` curve at doses 0/1/4/16, and G11 abstention means and verdict.
No favorable component substitutes for the conjunctive gate.

Treatment-minus-control contrasts are reported as:

- `delta I_d_frame` (positive favors preservation treatment acquisition);
- `delta frame_spill` (negative favors preservation treatment locality);
- the change in dose-16 correct conditional probability and frame `dP`;
- the complete G9 and G11 verdicts.

For the treatment loss trace I will report mean KL, first-48 mean KL,
last-48 mean KL, and the mean of each anchor's final *pre-update* observation.
Those values prove that a training-time preservation pressure was computed.
They are **not** a terminal preservation assay: the implementation does not
run the final trained adapter over all 48 anchors after the last optimizer
step. Unless a separately captured post-fit anchor sweep with bound code and
inputs appears, final anchor preservation is explicitly **unmeasured**.

## Claim boundary and outcome table

This is one synthetic old-frame bank and one optimizer seed. It cannot support
numeric generality, clean lineage, personal action-outcome learning,
THINK/DREAM/SLEEP, parenting, retention across writes, conditional semantic
binding, deployment behavior, OEL/SDFT reproduction, or a mechanism freeze.

- If treatment passes G9 while preserving acquisition relative to the fresh
  control, the maximum claim is: *on this bounded synthetic old-frame
  development cell, an additive frozen-OFF anchor objective improved measured
  frame locality without erasing the existing surface acquisition*. A fresh
  disjoint confirmation and semantic W0 remain necessary.
- If spill falls but remains above `.03`, or if acquisition/its positive
  interval is lost, the treatment fails. This is a tradeoff diagnostic, not a
  selective-writer result.
- If neither locality nor acquisition improves, the treatment is negative and
  no coefficient sweep follows automatically.
- G11 is expected to fail because frozen OFF already has low abstention and
  the objective teaches no abstention. Preserving that behavior cannot count
  as learning selective abstention.

Whatever the result, semantic W0—opposite actions under different semantic
conditions—remains the decisive writer experiment. This pair can select or
reject a bounded preservation ingredient; it cannot replace W0.
