# Adversarial audit: Astra's proposed two-habit continuation

**Date:** 2026-09-12  
**Status:** watcher advice only; no builder code or run changed.

## Verdict

Astra's `INPUT -> PREDICT -> ACT` versus
`PREDICT -> ACT -> INPUT` proposal is a useful **level-zero compatible-
coexistence sentinel**, after one important control repair. It is not Rohin's
full "two behaviours, then intertwined" test and must not replace the existing
PROSPECT/REVISE Level-1 protocol.

The proposed run asks a narrow but timely question: after ACT-only updates
erased the old PREDICT habit without replay, can one rank-8 adapter acquire a
second compatible output convention while the old convention is explicitly
rehearsed? That is a legitimate first replay/coexistence endpoint. But INPUT is
only faithful operand copying, and changing the order of three lines tests
ordered co-expression. It does not show that INPUT causally informs PREDICT,
that an outcome changes policy, or that two cognitive operations intertwine.

Run it only under the repaired gates below and name the result accordingly.
Then use the already specified PROSPECT/REVISE experiment for Level 1.

## The control defect to repair before launch

The current advancement rule requires `J(T) >= 28/32` and `J(C) <= 4/32`,
where J is the treatment order. That is insufficient: C could emit no INPUT
at all and still look like a successful ordering control.

Freeze two symmetric own-map scores:

- `J_T`: exactly `INPUT(correct operands) -> PREDICT -> ACT`;
- `J_C`: exactly `PREDICT -> ACT -> INPUT(correct operands)`.

Each descendant must acquire **its own** assigned order and reject the other.
This changes only the scorer/gate, not the proposed corpora.

## Minimal states and gates

Keep the proposed three states per original seed:

- **H:** immutable inherited PREDICT-before-ACT parent, no continuation;
- **T:** H plus the INPUT-before-PREDICT-before-ACT continuation;
- **C:** H plus the token/content-matched PREDICT-before-ACT-before-INPUT
  continuation.

The existing three trainer roots and fixed LR `1e-4` are acceptable for this
sentinel. The direct-conflict plasticity result does not select `1e-4` over
`3e-5`; therefore report this as one concrete replayed continuation recipe,
not as an optimized plasticity setting. Root 0 should gate roots 1--2.

Before fitting, require:

1. exact H adapter hashes and clean lineage;
2. paired T/C rows with identical source information, target-token multiset,
   row count, update count, EOS/loss masking, and no truncation;
3. exact operand-copy scoring derived from source rows, never model answers;
4. stateless fixed readouts with raw outputs preserved.

Root 0 advances only if all of the following hold:

- H precondition: old PREDICT-before-ACT form `>= 30/32`, correct ACT
  `>= 31/32`, and treatment-order INPUT `<= 4/32`;
- T: `J_T >= 28/32` and cross-order `J_C <= 4/32`;
- C: `J_C >= 28/32` and cross-order `J_T <= 4/32`;
- both descendants retain PREDICT before ACT on `>= 30/32` and correct ACT on
  `>= 31/32`;
- INPUT contains the exact displayed operands on every counted own-map pass;
- on the 16 memory/no-phase prompts, new INPUT/PREDICT/ACT tag spill rises by
  no more than `1/16` versus H, and validity does not fall by more than `.05`.

Require the same per-root gates for the final three-root descriptive result.
Do not pool the 96 prompts as independent learners. If either T or C fails its
own map, the ordering contrast fails even if the other branch looks perfect.

No extra branch is needed now. H supplies the inherited reference; the
completed ACT-only continuation supplies the zero-replay/direct-conflict
endpoint; T/C test the compatible full-rehearsal endpoint. Together they
bracket the phenomenon but do **not** estimate an optimal replay fraction.

## Claim boundary and builder handoff

A positive result permits only:

> A previously installed global output habit remained expressible while the
> same adapter acquired a second compatible, source-faithful ordered output
> convention under explicit rehearsal.

It does not establish conditional intelligence, outcome-sensitive revision,
memory extraction, causal use of the INPUT line, parenting, DREAM/SLEEP, or
intertwined cognition. Call it **L0 coexistence**, not Level 1.

After it passes, the smallest honest Level-1 test remains the existing memo's
single-adapter pair:

1. **PROSPECT:** use a public belief card to predict a consequence, then act;
2. **REVISE:** compare the prediction with a counterfactual public outcome and
   KEEP or SWITCH the next action.

AUTH, token/marginal-matched DERANGED, and OFF are necessary there because the
claim is input-selective conditional use rather than syntax. First qualify
both behaviours separately in one interleaved/replayed corpus; then probe the
three-turn chain with zero new training. Add chain demonstrations only if the
parts pass and spontaneous composition fails.

One correction is needed before executing that older memo: its LR prerequisite
mentions retention after **unrelated** updates. The completed fading sentinel
used directly contradictory ACT-only targets, so it cannot satisfy or falsify
that prerequisite. Select the Level-1 LR prospectively from an actual
acquisition-plus-compatible-replay result; do not relabel direct overwriting as
unrelated interference.

**Builder recommendation:** repair the symmetric C own-map gate, run root 0,
expand to roots 1--2 only on pass, and stop treating this sentinel as the
intertwining experiment. Its value is a cheap check that compatible replay can
support two conventions in one adapter before spending on conditional
PROSPECT/REVISE.
