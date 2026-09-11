# Cell F next-action advisory — owner memory must relay into action

Date: 2026-09-11

Status: **independent advisory only; not ratified and not authorized for
implementation or execution.** Written before the running equal-exposure
`F_r16k4` and `F_r16k16` results were available. The full C11 guard remains
deferred to the final paper-grade C11 run.

## Why another repetition cell is not automatically next

Bank 0 of `F_r16k1` proves that sixteen repetitions of one completion frame
can drive the colour-candidate mass to approximately one. It does not prove
owner-bound memory: its frame spill is 0.439 and its owner-versus-similar
interaction interval crosses zero. The running `k1/k4/k16` comparison already
holds total rendering count fixed and asks the useful open question: does
surface diversity turn that broad completion habit into owner specificity?

Allen-Zhu and Li's controlled biography experiments motivate this exact
comparison: multiple diverse renderings and changed ordering can make stored
knowledge extractable, while token-level memorization alone need not. Their
result does not establish that a 7B all-layer LoRA trained on a lived ledger
will yield agent-usable memory. Cell F is our test of that transfer, not a
replication claim.

## Frozen decision table for the running screen

| Equal-exposure result | Reading | Next action |
|---|---|---|
| At least one K has a positive owner term, positive owner-versus-similar interval, every spill component <= 0.03, non-collapsed mass, dose rise >= 0.10, and no bank-direction reversal | Canonical owner binding is plausible | Select the **lowest** passing K and propose F-Relay |
| Diversity lowers spill but also erases the owner gain, so no K passes | Regularization/dilution tradeoff, not usable memory | Stop Cell F for this sprint; no automatic `F_r64k16` |
| Owner gain stays large but any spill component remains above 0.03 | Broad completion habit | Stop Cell F for this sprint; no automatic `F_r64k16` |
| Interaction is positive while the owner term is null or negative | Control suppression artifact | Stop |
| Normalized gain accompanies candidate-mass collapse | Scoring artifact | Stop |
| Every owner term is null | No extraction in this heavily replayed R16 regime | Stop for this sprint; do not claim global impossibility |
| Artifact identity is invalid or same-node banks reverse direction | Inconclusive | Repair and replay the same frozen screen; select nothing |

The thresholds above are advisory selection rules, not Cell F's existing
automatic labels. A result cannot be rescued by averaging a failed spill
component with easier controls.

## Conditional F-Relay proposal

F-Relay runs only if one K passes the full conjunction above.

1. Materialize one untouched 64-owner development bank and two colour-balanced
   counterfactual owner-to-colour maps over the same owners and schedules.
2. Train the frozen K, R=16 recipe separately on each map; cross-mount the two
   adapters so each adapter is also the other's wrong-life control.
3. Repeat the read after two matched unrelated writes to measure retention.
4. Preserve the similar-owner, dose-zero, bicycle/wrong-relation, mass,
   interface, and development non-harm controls.
5. Add free completion from the canonical prefix.
6. Add an **action relay**: each trial supplies a newly permuted
   colour-to-action codebook. The child must recover the hidden owner's colour
   and issue the corresponding valid action. Use both an assisted-prefix
   localization condition and an autonomous-recall condition.

The action codebook is newly permuted per trial so no fixed colour-to-action
routine can solve it. Own-map advantage over the cross-mounted wrong-life
adapter is necessary. Recall without action is a surface association; action
without owner specificity is a habit.

## Advisory admission rule

Before any F-Relay run, ordinary architecture deliberation and exact-byte
ratification must bind its materials and numerical rule. The independent
reviewer's proposed starting rule is:

- free-completion and autonomous-action accuracy at least 0.80 and at least
  +0.30 over adapter-off, with paired lower interval bounds above zero;
- own-map advantage over wrong-life at least +0.30;
- every spill component at most 0.03;
- at least 75% of the action gain retained after unrelated writes;
- 100% parseable canary actions; and
- development performance no worse than one frozen noise width.

These numbers are candidates for prospective binding, not current claims.
If no K qualifies, F-Relay is `NOT_RUN`, the factual carrier remains strong
retrieved text for the parenting canary, and GPU time moves to the writer
failure characterization rather than higher synthetic repetition.

## Result addendum — 2026-09-11

The equal-exposure diversity screen is terminal. The frozen summarizer was
applied without modifying the assay or thresholds. The three equal-exposure
bank-0 cells and the already-running bank-0 exposure sensitivity preserve a
large matching-owner completion gain, but all four remain `frame-habit`
because mean spill is more than ten times the 0.03 limit:

| cell | matching-owner dP | I_d_frame [95% CI] | mean spill | label |
|---|---:|---:|---:|---|
| `F_r16k1` | 0.6595 | 0.8997 [-0.106, 1.939] | 0.4389 | frame-habit |
| `F_r16k4` | 0.5826 | 1.8216 [1.100, 2.580] | 0.3446 | frame-habit |
| `F_r16k16` | 0.6058 | 2.3607 [1.400, 3.398] | 0.3326 | frame-habit |
| `F_r64k16` | 0.6049 | 2.4230 [1.463, 3.472] | 0.3583 | frame-habit |

Increasing surface diversity from one to sixteen forms strengthens the
owner-versus-similar interaction and reduces spill somewhat. It does not make
the learned continuation selective. Increasing repetition from 16 to 64 at
sixteen forms does not rescue it: owner gain is essentially unchanged and
spill rises from 0.3326 to 0.3583. `F_r64k16` had already been materialized in
the running queue; it is reported as a sensitivity cell, not as authority for
another escalation.

The frozen decision is therefore exercised: **stop Cell F for this sprint.**
Do not run F-Relay, another repetition level, or a confirmation bank. The
useful result is bounded: diversity produces a stronger owner-specific
component inside a still-broad completion habit. The next writer test must
ask whether several condition-specific action bindings can coexist without
action flooding; it must not be another larger Cell-F write.

Stopping after bank 0 is not an optimistic early stop. Even if two additional
equal-weight banks had exactly zero spill, the pooled spill implied by these
bank-0 cells would still be 0.111 to 0.146, well above 0.03. No possible
remaining-bank result could make this family pass its frozen spill gate.

Artifact identities used for this read:

- source `organism_v6/memory_dose.py`:
  `db3222e61f0a8219bfc0f40f22ade532bb72bd3d83a299a02c25d65cebbbaf0e`
- bank 0:
  `b8069c4e62f4e655453ca47c556ebd145be77071dab8db807e6ffbff51a06ed6`
- manifest:
  `7fa542e6035753684920105da37da67e4cca2a78c72a40d5257ed360c704abcb`
- evals `F_r16k1`, `F_r16k4`, `F_r16k16`, `F_r64k16`, respectively:
  `95b7c986be201a187036a11373a24f8df73433e2e76be58f3c79018b0ad80529`,
  `a40cbc3f28c57a5c268d1db63b05c3e699cf5c4dd01de302283bf3bdb5566755`,
  `2599ca865bbe010b6fba8c2a5e1188d454cda351f3f31cfe8296140b70dc35fc`,
  `bce48ce5420d9c6c6d2efd14a443327efe64bd7e88d577c0b9216eb200baff8a`.
