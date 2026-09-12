# Selective-writer bottleneck: fresh mechanism audit

**Date:** 2026-09-12
**Status:** independent design audit only. No builder source, model, adapter,
job, GPU process, claim, or launch authority was changed.

## Decision

The smallest plausible path is a **staged three-mechanism sequence**, not a
coefficient, learning-rate, rank, or corpus-size sweep:

1. **conditionalize the learned decision:** the closed Q0 pair-balanced
   common-prefix XOR update;
2. **only if Q0 acquires but spills, conditionalize the parameter update:** a
   hard function-space null update on a disjoint protection bank; and
3. **only after a selective W0, preserve time-separated content:** an
   equal-new-dose OLD/NEW cumulative-replay pair with separately normalized
   losses.

These mechanisms attack different failures. The first removes the coherent
output-dialect loss and forces opposite decisions inside each optimizer unit.
The second asks whether the current LoRA support contains an acquisition
direction that is first-order neutral on existing behavior; unlike KL it has
no preservation coefficient to trade against acquisition. The third supplies
the old gradient while a new bank is learned. It cannot repair a globally
nonselective writer and therefore belongs after W0.

Minimum canary path: **four new fits** (`2` Q0 plus `2` one-map OLD/NEW), with
an optional third Q0 diagnostic. Locality-repair canary path: **six new fits**
(`2` Q0, at most `2` hard-null fits, `2` OLD/NEW), again plus at most one
optional diagnostic. These are not the full two-root/two-map W1 claim count:
fresh two-map W0 confirmation adds `2` fits and the already specified complete
W1 adds `8` new fits. Thus the full fast development+confirmation path is
`12` fits (`14` if the hard-null repair is needed), plus at most one optional
objective diagnostic.

## What the evidence localizes

| observation | implication |
|---|---|
| Authored conditional AUTH and DERANGED maps were each expressed on every development case, but addition exactness fell `16/16 -> 3/16` or `0/16`, exact copy fell `14/16 -> 0/16`, and trained-tag spill reached `13/16--16/16`. | Rank-8 capacity and conditional carriage exist; globally active full-response learning installs the response language outside its owners. |
| Twenty distinct high-dose encounters acquired arbitrary device--colour maps at `14/16`, `16/16`, and `16/16`, while two of three continuations destroyed the inherited arithmetic interface. | Acquisition and coexistence are separable; this is not a capacity argument for higher rank. |
| Lower LR, response-prefix masking, and coefficient-`.1` frozen-OFF KL all reduced update effects, but either left spill far above `.03` or erased registered acquisition. | These treatments scale or oppose substantially the same update; another scalar sweep is low information. |
| Rehearsed compatible habits coexisted perfectly. Later batches containing two distinct memory and two distinct arithmetic sources acquired/extracted `15--16/16` memories while retaining habit and ACT `32/32` in the FOUR_VIEW arm across `3/3` seeds. | Explicit mixed replay and within-update source diversity can support memory/behavior coexistence; they do not establish conditional Q0 specificity or identity-disjoint OLD/NEW retention. |
| In the earlier same-source grouped layout, four lexical views preserved arithmetic at `32/32` where one repeated view gave `0/32`, but both stayed at `4/16` memory. In the later distinct-source layout, both view arms passed at seed 0; across seeds FOUR passed `3/3` and SINGLE `2/3`. | Batch composition was the decisive small-scale acquisition change. Lexical variety is a robustness clue, not a universal acquisition mechanism or substitute for conditional geometry. |

The current all-layer LoRA is active on every prompt, and ordinary response
SFT gives tags, syntax, answer-class mass, and EOS a large gradient shared by
all rows. The key-dependent choice is a smaller residual. Scaling the whole
update or penalizing its consequences need not rotate it toward that residual.
The next tests must change **directional geometry**, then separately test
**replay through time**.

## Intervention 1 — pair-balanced common-prefix Q0

Use the already-adjudicated one-root contract without adding another recipe:
`P_AUTH` and exact-complement `P_DERANGED`, natural maximal token-common
prefix, one four-prompt XOR quartet per update, 128 quartet updates, and the
existing exact/held/interface/locality panels. Each quartet crosses two
opposite-orientation tools with both modes. A global action bias, mode-only
rule, or tool-only rule cannot make all four signed margins correct.

### Exact paired test

- Shared OFF, bitwise-identical initial LoRA tensors, target-free quartet
  order, dropout schedule, root, prompts, and optimizer recipe.
- `P_AUTH` and `P_DERANGED` differ only by the exact complementary target
  signs.
- Retain the no-update P/V audit. Run `V_AUTH` only if its natural-prefix
  gradient is prospectively nondegenerate; otherwise the optional third fit
  is the already-specified unary opaque-tool diagnostic after an XOR failure.
- Gate absolute legal branch-token mass and strict action identity as well as
  within-pair choice. Addition/copy outputs are extended controls, never
  compensated by owner accuracy.

### Stop rules and fits

- A finite zero pairwise tangent is `ZERO_XOR_TANGENT_AT_INIT`; launch no
  full fit.
- If either map's first real quartet cannot improve all four signed margins
  and all four analytic-floor grad-dot-delta canaries, stop that worker. Spend
  only the registered one-step complementary diagnostic where required.
- If the canaries pass but either final exact-map gate fails, stop this writer
  family: no more LR, rank, dose, lexical-view, or objective tuning.
- Exact pass / held fail releases a **relation-view extraction** pair, not a
  locality treatment. Exact+held pass / locality fail releases Intervention
  2. A full pass skips Intervention 2 and advances to Intervention 3.
- Fits: `2` mandatory, `3` maximum. Early failure can end after two one-step
  attempts and at most one unary fit.

This is the smallest test of whether eliminating response-dialect gradients
and balancing the conditional directions is sufficient. A pass is one-root
supervised XOR binding, not yet a reliable SLEEP writer.

## Extraction-only branch — relation views, not more paraphrases

This is not part of the default fit count. Use it only when Intervention 1
passes exact storage and locality but fails held extraction. Compare the
passing lexical Q0 recipe to one treatment that replaces seven lexical
paraphrases with seven relation-defined access routes at identical key,
target, encounter, update, and token budgets. Reuse the canonical exact form
in both arms. Run AUTH first; run its complement only if AUTH retains exact
storage, improves held balanced accuracy by at least `.10`, and does not
worsen any scope family by more than `.05`.

Stop after `1--2` new fits. A second null is not a reason to add views or
epochs. The recent grouped-view result makes diversity a credible
anti-interference mechanism, but its `4/16` memory null forbids treating
lexical diversity alone as a writer solution.

## Intervention 2 — hard functional-null LoRA update

Run this only after both Q0 maps pass exact and held acquisition but fail
locality or addition/copy preservation. Reuse the acquired-and-spilling
`P_AUTH` as the paired control. Do not combine this treatment with new views,
rank, initialization, rate, or replay.

Before outcomes, seal a **training protection bank disjoint from every gate
item**. It should contain native addition and exact-copy prompts plus separate
missing-mode, unsupported-mode, neighboring-ID, and wrong-root prompts. Let
`f_N(theta)` contain, for those prompts:

- teacher-forced log probabilities of every token and EOS in the frozen-OFF
  correct addition/copy continuations; and
- natural-prefix within-action choice `q` and absolute legal branch-token
  mass `M` for the scope prompts.

For each quartet, first form the ordinary AdamW proposed parameter delta `u`
from the pairwise loss. Then, before applying it, solve the minimum-change
constraint

```text
u_perp = argmin_v ||v-u||^2  subject to  J_N(theta) v = 0,
J_N = d f_N / d theta
```

using a prospectively fixed FP64 SVD/pseudoinverse tolerance. Apply
`u_perp`, not `u`; recompute `J_N` at every update. The memory-loss coefficient
remains exactly `1.0`. There is no `lambda`, and the protected prompts supply
no task answer. This is an update-space constraint within the existing LoRA,
not a new projection layer, router, hypernetwork, or learned parameter.

### Exact paired test

- Control: the completed, acquiring-but-spilling `P_AUTH` from Intervention
  1. Treatment: `P_PERP_AUTH`, same initialization, quartets, RNG, optimizer
  hyperparameters, and checkpoints; only the proposed Adam delta is projected.
- Before applying the first update, require all four signed XOR margins to
  have positive predicted change above the registered numerical floor after
  projection, while every protected coordinate satisfies the null tolerance.
  Otherwise record `NO_SAFE_LOCAL_DIRECTION_THIS_LORA_SUPPORT` with zero
  applied updates.
- `P_PERP_AUTH` must meet every absolute exact, held, generation, addition,
  copy, and held-out locality gate. Reduced spill with failed acquisition is
  the already-seen tradeoff, not a partial success.
- Only an AUTH absolute pass releases `P_PERP_DERANGED` under the identical
  projector construction. Both maps must pass; the protection-bank prompts
  never enter the held evaluation.

### Stop rules and fits

- No safe first step: stop the branch with `0` completed fits and no alternate
  tolerance/bank/rank.
- AUTH under-writes, fails held extraction, or merely memorizes the protection
  bank: stop after `1` fit.
- AUTH passes: run DERANGED once; any failure ends the branch. Do not sweep a
  soft coefficient after a hard-null failure.
- Fits: `1` normally, `2` maximum. Because Jacobian construction may dominate
  wall time, profile and cap compute independently; do not infer its cost from
  ordinary-fit timing.

This asks the question the KL result could not: does a nonzero conditional
direction exist inside the registered LoRA support that is locally orthogonal
to old behavior? Its claim remains finite-panel functional preservation, not
global distributional locality.

## Intervention 3 — equal-dose OLD/NEW cumulative replay

Run only after a two-map selective W0 recipe exists. Use an identity-disjoint
NEW bank under the same map and recipe. The already-qualified OLD singleton is
the OLD reference; evaluate it on NEW without fitting. Then run:

1. `NEW_ONLY`, from clean base, at the exact per-key dose that qualified OLD;
2. `OLD_PLUS_NEW`, from clean base, pairing one OLD and one NEW quartet at
   every update and optimizing

```text
J_t = mean(L_OLD,t) + mean(L_NEW,t)
```

with no `/2`, union-token mean, adaptive weighting, or shared dropout stream.
Thus NEW has the same coefficient, encounters, and row order in both fitted
states; OLD receives the same dose it received in its singleton. Extra replay
compute is reported rather than disguised by weakening either memory.

### Exact paired test, stop rules, and fits

- First require `NEW_ONLY` to pass the complete W0 gate and be neutral on OLD.
  If it fails, stop after `1` fit: the NEW bank did not reproduce the writer.
- Run `OLD_PLUS_NEW` once. Require OLD and NEW separately to retain every
  absolute W0 gate, per-key median gain at least `.8` of its singleton, at
  least `12/16` keys and `6/8` per stratum retaining `.8` of singleton gain,
  native addition/copy preservation, and held locality. No bank average may
  hide forgetting.
- Any cumulative failure stops replay-weight, ordering, epoch, or adapter
  search. It localizes interference under an already-selective writer.
- Fits: `2` new fits for the one-map coexistence canary; `3` only if the OLD
  singleton must be freshly reproduced for byte-level trainer parity. A
  complementary-map coexistence replication is downstream, not required to
  interpret this canary.

A pass establishes explicit-replay reconstruction of two supplied,
identity-disjoint banks in one LoRA. It does not establish unrehearsed
retention, sequential optimizer-state continuity, child-authored experience,
or DREAM/SLEEP.

## Explicit non-selections

- **No more LR, prefix-mask, or scalar preservation sweep:** all have already
  traced the acquisition--locality frontier without leaving it.
- **No rank increase:** rank 8 acquired complete authored maps and high-dose
  arbitrary keys; capacity is not the localized defect.
- **No unbalanced labels or easier keys:** either enables the shortcut the
  gate is designed to reject.
- **No broad `Q/X x 0/A` factorial:** the ordered failure label selects the
  mechanism. Views answer extraction; hard-null updates answer locality.
- **No task-family router as writer evidence:** a frozen external gate could
  trivially switch the adapter off for addition/copy, but then the router
  supplies the selectivity. It is an engineering fallback, not evidence that
  one LoRA learned selective scope.
- **No W1 before W0:** the new `3/3` memory+habit result makes replay credible,
  but replay can preserve a global dialect perfectly and still leave the
  writer scientifically unusable.

## Evidence basis

- `2026-09-12_conditional_root0_terminal_postaudit.md`
- `2026-09-12_lower_lr_writer_terminal_audit.md`
- `2026-09-12_prefix_mask_terminal_independent_audit.md`
- `2026-09-12_preservation_pair_terminal_independent_audit.md`
- `2026-09-12_grouped_lexical_views_root0_terminal_postaudit.md`
- `ASTRA_INTERLEAVED_MEMORY_READOUT_2026-09-12.md`
- `ASTRA_INTERLEAVED_REPLICATIONS_2026-09-12.md`
- `2026-09-12_high_dose_memory_continuation_terminal_audit.md`
- `2026-09-12_fixed_update_replay_allocation_terminal_audit.md`
- `2026-09-12_two_habit_coexistence_adversarial_audit.md`
- `2026-09-12_q0_pairwise_falsifier_implementation_closure_v2.md`
- `2026-09-12_post_v10r2_writer_recipe_factorial.md`
- current `organism_v6/multikey_writer_gateway_simple.py`,
  `organism_v6/train_adapter_v21.py`, and `organism_v6/lora_svd_init.py`
- current ICLR submission checklist and coordination ledger through the
  conditional, grouped-view, and interleaved-replay terminal audits.
