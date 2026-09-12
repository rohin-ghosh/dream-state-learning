# Fresh post-audit: terminal semantic objective null

Date: 2026-09-12 UTC

Scope: read-only scientific audit of `2026-09-12_semantic_objective_terminal_reduction.md` and the previously inspected training contracts. The immutable implementation and report were not synced locally: `gpu/astra_semantic_objective_probe.py` is absent. I therefore rely on the recorded source SHA-256 `98a90f33...d41`, test SHA-256 `0a327ab0...e0`, report SHA-256 `4ca53169...659`, stage counts, and independent reduction; I cannot independently rehash or line-audit those three unavailable artifacts. No model, GPU, network, test, builder file, coordination file, or M-core file was touched.

## Verdict

**PASS for the narrow executed-recipe null; REWORK for the mechanistic null.** It is valid to report:

> In the reproduced root1/W+/seed-1, 256-update instance, replacing ordinary full-response CE with ordinary one-live-decision-token full-vocabulary CE did not improve conditional behavior on the 128 exact training prompts.

That statement is unusually well supported for a single run: both trained arms generated the identical constant `-gvn` action on all 128 prompts, were each 64/128 correct, agreed on every final teacher-forced margin sign, and had mean signed margins `0.029296875` (full) versus `0.025390625` (decision-only). The decision arm moved (`update_norm=1.4330553267`) and did not merely fail to update. This is a substantive null for the **composite objective substitution actually executed**, not a threshold artifact.

It is not valid to conclude that nondecision gradients are harmless, that “the response objective” is not a bottleneck in general, or that pairwise conditional learning cannot work. The exact claim remains one root, map, seed, dose, initialization, implementation, and exact-form population.

## Which pre-run blockers were closed

| Concern | Terminal evidence | Disposition |
|---|---|---|
| Historical full-response reproduction | Initial LoRA digest `49b7cb...0565`, final tensor digest `31f101...787`, mean/first/final losses and update norm all reproduce; only serialization tree hash differs | **Closed at the learned-tensor/trajectory-summary level.** This is adequate to connect the contemporary control to the historical failure. A full 256-value trace was not quoted, but the exact final tensor digest is stronger than qualitative reproduction. |
| Device/runtime and dtype confounding | Both fits ran on the same pinned GPU/runtime; LoRA parameters, gradients and Adam states were FP32 | **Closed for the recorded run.** |
| Complete execution/evaluation accounting | Five stages once, 512 updates, 384 generations, 384 dropout-off decision-prefix forwards, zero held queries, cleanup/controller checks | **Closed.** The previously implicit margin-forward budget is now explicit. |
| No-update explanation | Decision arm update norm and one-token mean loss are recorded | **Closed.** Nonzero movement does not itself establish useful conditional gradients, but it rules out a vacuous zero-update null. |
| Cross-arm identical initialization, optimizer membership and dropout stream | The reduction names the historical control's initial digest and common device/runtime, but does not explicitly quote the decision arm's initial digest, ordered optimizer membership, or pre-forward CUDA RNG equality; source/report bytes are unavailable here | **Not independently closed by this post-audit.** The identical final behavioral null is still descriptive evidence, but initialization/RNG sensitivity remains a possible false-negative modifier. |
| BF16 target-length shape sensitivity | No training-path equal-shape or prefix-invariance certificate is reported | **Open.** The result validly tests the unchanged natural-shape stack; it does not isolate an idealized causal objective from this known structural exposure. |

## Why the broad null does not follow

For response length \(N\in\{8,7\}\), the full arm uses

\[
L_F=(\ell_d+\sum_j\ell_j)/N,
\]

while the executed decision arm uses \(L_D=\ell_d\). The intervention removed nondecision gradients, increased the decision coefficient by 7--8x, removed 1/8-versus-1/7 target-dependent weighting, and changed AdamW moment/epsilon/weight-decay interactions. A null composite contrast can hide opposing component effects; the scaling ambiguity matters for nulls as well as positives. Therefore the result weakens the practical proposal “switch to ordinary one-token CE,” but does not falsify the narrower hypothesis that nondecision gradients interfere when the decision term's original coefficient is held fixed.

The final decision-prefix measurement is much cleaner than the old unequal-candidate likelihood scoring, but training still forwarded target-dependent 8-versus-7-token natural sequences. The prior BF16 finding was an inference-scoring observation, not proof of corrupted dropout-active training. Still, without an equal-shape certificate it remains an alternative implementation condition under which both objectives may have failed. Finally, exact rows cannot distinguish key-rule learning from memorization; a null there is evidence of failure to acquire usable exact associations, not a general capacity result.

## Minimum pairwise follow-up at no greater GPU budget

Use one final two-arm, common-prefix comparison. It has the same 512 main updates, 384 generations, and 384 decision-prefix evaluations as the terminal probe, but shorter forward sequences; retain the 1,800-second cap. Do not rerun full-response CE.

For every original row, form exactly one input ending at the three-token common response prefix immediately before token `10536` (`-mem2reg`) versus `21404` (`-gvn`). No gold decision token, suffix, LF, EOS, or target-dependent future length appears in the input. Let

\[
d_i=z_i(10536)-z_i(21404),\qquad
s_i=+1\ \text{for mem2reg gold, }-1\ \text{for gvn gold},\qquad
m_i=s_i d_i.
\]

Both arms use identical input IDs, masks, initial tensors, row order, dropout stream, AdamW settings and 256 updates:

- **Vocab-decision control:** \(L_V=-\log\operatorname{softmax}(z_i)_{gold}\).
- **Paired-action treatment:** \(L_P=\operatorname{softplus}(-m_i)\), equivalently negative log probability of the correct token after normalizing only the two legal action tokens.

This isolates all-vocabulary competition versus the explicit correct/incorrect action contrast on the same logits and removes target-dependent future shape from both arms. Pairwise CE does not introduce label information absent from one-token CE; it only concentrates optimization on the relevant rival. A P-only win would therefore support an optimization-focus explanation, not discovery of a previously missing semantic relation.

Runtime bindings must include identical actual initial LoRA tensor digests for V and P, ordered trainable/optimizer membership, pre-forward CUDA RNG-state digests, base/runtime/device hashes, and FP32 metric computation from the same last-prefix logits. Any mismatch makes the causal contrast invalid. Evaluate shared OFF, V and P on the same 128 exact prompts: 384 ordinary generations and 384 dropout-off common-prefix forwards total. Report paired correct/incorrect discordance, both label recalls, all 16 key-mode cells, all eight templates, action concentration and strict validity.

### One-update gradient/log-odds canary

Before the full fits, deterministically select the lowest-hash `(slot, template)` whose `m0`/`m1` prompts tokenize to an equal-length pair; the two modes have opposite gold actions. On the clean P model, after snapshotting its initial LoRA tensors, optimizer-empty state and RNG state:

1. Evaluate both dropout-off raw log odds \(d\) repeatedly without an update; define the numerical floor \(\epsilon\) as the maximum repeated-evaluation spread and require the repeats to satisfy the deterministic-runtime contract.
2. Compute each example's gradient and their balanced mean-loss gradient. Require finite, nonzero gradients and positive predicted directional derivatives for both signed margins under the balanced descent direction.
3. Apply exactly one real AdamW update to the mean of the two pairwise losses. Re-evaluate dropout-off. If mem2reg is gold for row `a` and gvn for row `b`, require \(\Delta d_a>\epsilon\) and \(\Delta d_b<-\epsilon\), equivalently both signed margins increase beyond the measured floor. Opposite raw-log-odds movement rules out a pure global action-bias shift.
4. Record gradient norms/cosines by LoRA A/B projection, parameter/update dtypes, update norm, logits and RNG receipts. Restore the snapshotted initial tensors and RNG, recreate the empty optimizer, and require exact digest/state equality before the real fit. The canary supplies no training checkpoint or selected pair.

**Canary stop rule:** any index/shape/hash/RNG mismatch, nonfinite or zero gradient, failed directional derivative, or failure of the two raw log odds to move in opposite correct directions stops the follow-up before either 256-update fit. No alternate pair, LR adjustment, retry, or canary-selected seed is allowed. The two-example canary plus shorter main sequences remains below the prior GPU-work envelope without increasing its wall-clock cap.

### Final decision and stop rule

Predeclare acquisition, without modifying Q0, as all of:

- generated balanced accuracy at least `0.80`, both gold-action recalls at least `0.75`, and every template at least `12/16` correct;
- positive median signed common-prefix margin in at least `12/16` key-mode cells; and
- positive P-minus-V mean signed-margin change separately within both gold-action classes, so a global preference cannot supply the contrast.

Interpret outcomes as follows: P passes and V fails supports pairwise optimization focus for this instance; both pass implicates the old target-suffix/shape or loss-construction path rather than pairwise specificity; V passes and P fails rejects the pairwise proposal; neither passes is the terminal stop. On canary failure or final neither-pass, stop semantic-writer rank/LR/heat/paraphrase/objective tuning and revisit the carrier/representation or task construction. A passing exact-row result authorizes only a separately preregistered held/spill test; it is not writer qualification, generalization, retention, parenting, or H1/H2 evidence.
