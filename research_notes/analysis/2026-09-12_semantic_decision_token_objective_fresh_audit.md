# Fresh audit: semantic decision-token objective probe

Date: 2026-09-12 UTC
Scope: read-only review of section A of `ASTRA_OBJECTIVE_AND_CHECK_PROBES_2026-09-12.md`, `astra_semantic_training_audit_20260912.md`, and the directly relevant frozen training/scoring contracts. No model, GPU, network, test, or builder-code action was performed. No M-core file was changed.

## Verdict

**REWORK before launch.** The proposed pair can causally compare two *compound training recipes* for one deterministic root1/W+/seed-1 instance, provided the runtime pairing is enforced. As written, it does not isolate “nondecision response supervision impedes conditional acquisition,” and “decision-only advantage supports an objective bottleneck” has no prospective decision rule. A positive result would currently admit objective scaling/length reweighting, BF16 sequence-shape sensitivity, device/RNG mismatch, and exact-prompt memorization as alternative readings.

The useful core should be retained: same 128 rows, order, initialization, optimizer and 256 updates; one full-response arm; one label-mask arm; dropout-off decision margins plus ordinary generation; no held-form selection, retry, or historical relabeling. No extra fit, update, generation, or wall-clock allowance is needed for the minimum repair below.

## What the current contrast does and does not identify

For a row with response length \(N\in\{8,7\}\), original batch-one loss is

\[
L_F=(\ell_d+\sum_j\ell_j)/N,
\]

where \(\ell_d\) is first-divergent-token CE. Ordinary one-live-label causal CE is

\[
L_D=\ell_d.
\]

Thus section A changes three things together: it removes nondecision gradients, multiplies the decision contribution by 7 or 8, and removes the action-dependent 1/8-versus-1/7 row weighting. AdamW is only approximately invariant to a *constant* gradient rescaling; this rescaling varies with the target, while epsilon, moment histories, and decoupled weight decay further prevent an exact invariance argument. A B-over-A result can therefore establish only that the composite substitution \(L_F\rightarrow L_D\) helped this run. It cannot locate the cause in tail-gradient interference or even show that masking, rather than decision reweighting, supplied the benefit. The source memo acknowledges tail-versus-length ambiguity, but “objective bottleneck” remains too broad to be a discriminating causal conclusion.

## Blocking issues

### Causal and optimization

1. **The treatment is composite.** The loss equations above are the main isolation failure. “Only the label mask changes” is byte-level truth, not optimization-level isolation.
2. **Pairing is asserted, not operationally bound.** A common seed does not by itself prove identical LoRA tensors, ordered optimizer membership, dropout streams, base/runtime, or device. Running arms on different GPUs would confound treatment with device. Run both on the same pinned physical GPU/runtime, reset through the identical pre-forward path, compare actual initial tensor/name/shape/dtype hashes, and record matching CUDA RNG-state hashes immediately before each training forward. Any arm-specific stochastic operation before forward invalidates the pair.
3. **The historical control is too weak.** “Qualitative” reproduction is insufficient for attributing the historical root1/W+ failure. Under the claimed same deterministic recipe, arm A should reproduce the archived initial hash, 256-step coordinates/loss trace, final adapter digest, and 128 exact-prompt actions within a predeclared exact/tolerance contract. Otherwise the contemporary A/B pair may remain internally descriptive, but it does not explain the historical result.
4. **One seed/map/root has no robustness estimand.** With only two fits, this can be a deterministic case study for root1/W+/seed 1. It cannot support a task-wide, optimizer-seed, opposite-mapping, or root-general objective claim. This limitation cannot be repaired without more fits; narrow the claim instead.

### Implementation

5. **Known unequal-shape exposure is not controlled.** The action continuations have 8 versus 7 tokens. The repository already records BF16 eager shared-prefix logits changing with total future sequence length for these semantic candidates, while equal-shape padding removed the discrepancy. That result was measured in scoring, not dropout-active training, so it is an unexcluded training-path confound rather than proof of a bad fit. Nevertheless, decision loss at label `P+3` is computed from a full tensor whose length is target-dependent. Before launch, either right-pad both arms to the same per-prompt candidate-pair length with masked pad attention/loss and certify prefix invariance on the actual native path, or obtain a native training-path certificate showing that the decision logits/gradients are invariant to aligned future padding within a declared tolerance. A natural unequal-shape run cannot uniquely support a semantic-objective mechanism.
6. **The planned metrics lack exact definitions.** For every row, bind the discovered common-prefix length rather than trusting hard-coded `P+3`; assert exactly one decision label and that shifted logit `P+2` predicts it. Define full CE, decision CE, and nondecision CE as pre-update quantities with token counts and reduction equations. Validate the reconstructed full CE against the model's actual training loss in arm A. Define signed margin as `logit(gold)-logit(other)` from the same decision history. “Nondecision NLL” must state whether it is a per-row mean or token-pooled quantity; report sums and denominators so both are recoverable.
7. **Initialization and evaluation costs/receipts are incomplete.** CPU checks cannot prove actual CUDA initialization identity or optimizer-state dtype. Cross-arm runtime receipts must do so. The budget lists 384 generations but not the dropout-off teacher-forced forwards needed for 128 initialization and 256 final margins; enumerate and cap those forwards rather than leaving an implicit evaluation budget.

### Measurement and interpretation

8. **There is no prospective support criterion.** “Decision-only advantage” could mean one extra correct row or a global-prior fluctuation. Predeclare the A/B estimand and categorical outcomes. At minimum, support requires B to show both correct-direction teacher-forced margins across key-mode cells and end-to-end generated binding, while A does not; a small sub-acquisition difference is descriptive objective sensitivity, not a bottleneck. This diagnostic rule must not replace or repair the frozen Q0 label.
9. **Online training rows are time/order confounded.** Each logged row is evaluated at a different pre-update checkpoint in a fixed repeated order. Those records diagnose the optimizer but are not a balanced per-key learning curve. Primary conditional metrics must come from dropout-off evaluation of all 128 rows at common initialization and final checkpoints.
10. **Greedy accuracy alone is too coarse.** A balanced constant action scores 1/2, and near-tie logits can flip many actions. Report the paired A/B correct/incorrect discordance table, balanced accuracy, all 16 key-mode cell summaries over eight templates, signed margin distributions, action concentration, and format validity. Require margin and generation to agree for the positive mechanism reading.
11. **Exact training prompts do not establish a learned key rule.** Even perfect conditional behavior can be exact-row/template memorization. No held form, opposite map, root, or fresh key is tested. The maximum interpretation is acquisition usable on the 128 trained root1/W+ prompts; not key-rule generalization, capacity, retention, parenting, or H1/H2.

## Minimum stronger design at the same GPU budget

Keep two fits, 512 updates, 384 generations, and the 1,800-second cap, but make the estimand **removal of nondecision gradients**:

- Arm A updates with \(L_F\) exactly as archived.
- Arm B keeps only the decision gradient but updates with \(L_{B*}=\ell_d/N\), using that row's original response-token count. This preserves the decision term's exact coefficient and the 1/8-versus-1/7 weighting; only the nondecision gradient terms are removed. Because the model's ordinary one-label loss returns \(\ell_d\), the harness must apply the explicit factor and test the shifted full-vocabulary CE algebra. This does not add a fit or update. If the intended question is instead the composite one-token recipe, retain \(L_D\) but rewrite the conclusion to that exact composite and abandon a tail-interference interpretation.
- Use identical right-padded input/attention tensors in both arms and a native prefix-invariance canary. If padding prevents exact historical replay, label the experiment a controlled mechanistic analogue; do not claim it reproduces the old fit. If natural tensors are retained to preserve exact replay, a positive result remains conditional on the unresolved BF16 shape mechanism.
- Run sequentially on one pinned GPU. Bind actual initial LoRA and base hashes, ordered trainables, pre-forward RNG states, dtypes, and first/last pre/post-update norms. At a few already scheduled steps, decompose decision and nondecision gradient norms/cosines from the same forward without changing the declared update; this adds no examples, optimizer steps, or generations and identifies whether removed gradients oppose or dominate the decision term.
- Make final dropout-off teacher-forced decision margins on all 128 prompts the mechanistic endpoint and ordinary unprefilled greedy accuracy the behavioral confirmation. Reuse the shared zero-update/OFF state only after tensor/output identity is proven. Predeclare the paired estimand and a bounded support rule; classify integrity/reproduction failure, A-only acquisition, both acquisition, B-only acquisition, both null, and small non-acquiring differences separately.

Under this repaired design, **B-only acquisition would support nondecision-gradient interference for this exact root1/W+/seed-1, 256-update recipe**. It would still not demonstrate general key-rule learning or explain length weighting. Under the current design, a B advantage supports only a composite one-token-objective advantage and should not be called an isolated objective bottleneck.
