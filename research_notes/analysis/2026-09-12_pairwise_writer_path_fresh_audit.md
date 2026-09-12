# Fresh audit: minimum pairwise writer path after SEQ-089

Date: 2026-09-12 UTC

Scope: read-only scientific/code audit of `gpu/astra_semantic_objective_probe.py`
(SHA-256 `98a90f33dcd5582b9e32fe21d08dd29283c82b955ff350c8c994d2903b2f0d41`),
`tests/test_semantic_objective_probe.py` (SHA-256
`0a327ab022b434d89cdcd881ab795f4ee28ff896679d45da16b03be1ddb95de0`),
the SEQ-089 design, terminal memo, independent reduction and post-audit, and
the relevant semantic and V10R1 writer gateway paths at repository state
`04f9b7885fcace8e9753ae7539cb028f82e61985`. I did not run tests, models,
GPUs, or network operations and did not inspect or change live coordination.

## Verdict

**REWORK before launch; the path is constructible in the existing probe
skeleton, but the current bytes cannot run or adjudicate it.** SEQ-089 is a
sound narrow null: in one reproduced root-1/W+/seed-1 instance, ordinary
full-response CE and ordinary first-divergent-token full-vocabulary CE both
made real LoRA updates yet produced the same constant `-gvn` policy and
64/128 exact-row accuracy. It does not test a correct-versus-wrong action
contrast.

The minimum causal follow-up is one final two-arm comparison on the same 128
exact prompts:

1. a common-prefix, full-vocabulary decision CE control; and
2. a common-prefix, two-legal-action pairwise CE treatment.

Both arms must forward **only** the target-independent prompt plus common
assistant prefix ending immediately before the first divergent action token.
This removes SEQ-089's 7-versus-8-token target-shape exposure. Two fresh fits
are necessary: a lone pairwise fit could show acquisition, but could not
attribute it to pairwise normalization rather than the newly shortened,
equal-shape training path. A historical first-choice adapter is not an
admissible control for that changed path.

A new shared-OFF GPU stage is not part of the minimum. Absolute binding and
the paired V-versus-P contrast answer this question, while the pinned prior
OFF result may remain descriptive only. Omitting OFF reduces the run to four
model stages, 512 optimizer steps, 256 final generations, and 256 final
decision-prefix evaluations. This is strictly below SEQ-089's five stages,
512 steps, 384 generations, and 384 final prefix evaluations. A retained OFF
stage would still fit the old cap but would not strengthen the causal
P-versus-V inference.

## Exact objective and estimand

For row `i`, let `x_i` be the token sequence through the common `ACT: -`
assistant prefix, with no target branch token, action suffix, newline, EOS,
padding, or other future assistant token appended. (The user instruction
still names both legal actions symmetrically.) The actual native branch tokens are
`t0=10536` for `-mem2reg` and `t1=21404` for `-gvn`; preparation must discover
and pin them rather than trust these literals. From the single last-position
logit vector `z_i.float()` and target `y_i`:

\[
L_V(i)=\log\sum_{v\in\mathcal V}e^{z_{iv}}-z_{i,t_{y_i}},
\qquad
L_P(i)=\log(e^{z_{i,t0}}+e^{z_{i,t1}})-z_{i,t_{y_i}}.
\]

Equivalently, with `d_i=z_i[t0]-z_i[t1]` and `s_i=+1` for target 0 and `-1`
for target 1, `L_P=softplus(-s_i*d_i)`. Both losses must be formed explicitly
in FP32 from the same BF16 forward logits. `L_P` is a first-branch-token
correct-versus-wrong objective, not a full-continuation likelihood ratio.
That limitation is useful here: it excludes suffix length, LF and EOS from
the intervention while end-to-end unprefilled generation tests whether the
base still completes the selected branch into the strict action line.

The identified contrast is therefore **two-action normalization versus
full-vocabulary normalization on the same common-prefix logits**, including
their different gradient scale and AdamW moment trajectories. A P-only win
supports that exact pairwise optimization recipe in this deterministic
instance. It does not isolate an abstract representation mechanism or prove
that pairwise loss introduced information unavailable to V.

## A no-extra-update early gate

The post-audit's separate one-update canary is directionally valuable but is
not the minimum safe implementation. Updating, restoring only LoRA tensors
and RNG, and recreating AdamW leaves mutable model buffers/caches and effective
warm-up state as an unnecessary restoration confound; it also adds an
optimizer step outside the stated 512-step cap. Do not use that path.

Instead, make the canary the first two **real, budgeted** training steps:

- During CPU preparation, form the 64 `(slot, template)` pairs containing
  `m0` and `m1`. Assert that every pair has opposite targets. Select the
  lowest canonical hash over
  `['seq089-pairwise-canary-v1', source_hash_m0, source_hash_m1]` among pairs
  whose two common-prefix inputs have equal length. Freeze the selected pair,
  the hash domain, and mode order before any model access.
- Use the selected `m0,m1` rows first, followed by all other rows in their
  original relative order; repeat that exact 128-row permutation twice in
  **both** arms. This changes the historical order, so the result is a new
  controlled comparison and must not claim another reproduction of the old
  adapter.
- Run P first. In both P and V workers, perform the same dropout-off
  before-step and after-step-2 measurements on the two selected prefixes,
  with identical warm-up calls. Assert these measurements leave CPU/CUDA RNG
  and all named model buffers unchanged before returning to train mode.
- P proceeds beyond step 2 only if the canonical raw log odds move in opposite
  target-correct directions: `delta d > 0` for the target-0 member and
  `delta d < 0` for the target-1 member. Repeated pre-update evaluations must
  be bit-identical; otherwise this is an integrity stop, not a tolerance to
  estimate from the result. A prompt-independent action-bias update gives the
  same `delta d` to both members and cannot pass this gate.

This early gate uses no restoration, no extra optimizer update, no alternate
pair, and no selected retry. Its few short inference forwards plus the removal
of every target suffix are well inside the deleted OFF-stage work. The
prepared limits should nevertheless state their exact batch/example count;
“shorter” is not a substitute for accounting.

## Why this distinguishes binding from a global prior

The source material already supplies exactly 64 examples of each action and,
for every `(slot, template)`, a mode-flip pair with opposite gold actions. Do
not reduce success to aggregate accuracy. For each final adapter, preserve all
128 strict generations and canonical raw log odds `d`, signed margins `s*d`,
both action recalls, 16 slot-mode cells, eight templates, two strata, and the
64 matched mode-flip pairs.

Freeze `acquisition_pass(arm)` as all of:

- fixed-denominator generated BA at least `0.80` (`correct >=103/128`), each
  action recall at least `48/64`, and strict validity at least `122/128`;
- at least `48/64` matched `(slot,template)` mode-flip pairs have **both**
  strict generations correct and both signed margins positive;
- every template has at least `12/16` correct generations, and each 64-row
  stratum has at least `48/64`; and
- the median signed margin is positive in at least `12/16` slot-mode cells
  and at least `6/8` cells per stratum.

These reuse the existing gateway's 0.80 aggregate, 0.75 stratum, 0.95 validity,
and 12/16 plus 6/8 key coverage conventions, while adding the directly
relevant opposite-label pair predicate. A constant action obtains one zero
recall and zero double-correct mode-flip pairs. A mere global logit shift also
cannot move the two members' signed margins in the correct direction
simultaneously.

For the pairwise-specific conclusion, additionally require the paired final
margin difference `signed_margin_P-signed_margin_V` to have strictly positive
mean separately in the 64 target-0 rows and the 64 target-1 rows. All
inequalities use stored full-precision values and fixed integer denominators;
display rounding is irrelevant.

This is an exact-training-surface acquisition screen only. Unlike the V10R1
gateway, it has no held forms, opposite map, second root, two-candidate NLL
gain, spill TV, or unrelated-interface panel. No outcome may be called
`MULTIKEY_BINDING_PASS`, writer qualification, generalization, retention,
parenting, or H1/H2 evidence. A positive result may only motivate a separately
prospective held/spill gateway test.

## What the current code can and cannot supply

Useful infrastructure can be retained:

- `verify_original`, native tokenization and source/input pins;
- the fixed root1/W+/seed-1 material and 8x2x8 balance checks;
- fresh same-GPU deterministic workers, rank-8 construction, AdamW recipe,
  adapter serialization/reload, deadlines and owned-worker cleanup;
- `build_rows`' discovery of the first divergent token and its gold/other
  token identities; and
- unprefilled greedy generation plus the already-correct common-prefix margin
  forward.

The current bytes cannot implement the proposal:

- `ARMS`, `STAGES`, `SCOPE` and `LIMITS` are hard-coded to full-response versus
  first-choice plus OFF.
- `build_rows` retains only the gold full target tensor and a target-shaped
  one-live-label mask. It does not store a target-independent training input,
  the ordered two-action token table, 64 mode-flip pairs, the selected canary
  pair, or the new schedule.
- `labels_for`, `forward_metrics` and `training_step` call the HF labels path
  on the 7/8-token target-dependent tensor and backpropagate `output.loss`.
  There is no manual V or P objective.
- Pairing currently checks only initial LoRA digest and dtype counts. It does
  not bind ordered trainable names/shapes/dtypes, optimizer membership and
  hyperparameters, empty initial state, pre-forward RNG, or common step-0
  logits.
- Final records store only gold-minus-other margin. That erases the canonical
  sign needed to detect a common action shift.
- The reducer has no acquisition predicate or mutually exclusive prospective
  outcome; its fixed interpretation string is not result-conditioned.
- The current tests validate mask placement and mocked HF loss plumbing, not
  pairwise loss algebra, its gradients, target-independent shapes, RNG
  equality, a global-bias negative canary, or classifier precedence.

## Exact builder-code changes required

Only the probe and its focused test need change; the existing writer gateway
should remain a pinned dependency, not be edited for this diagnostic.

In `gpu/astra_semantic_objective_probe.py`, Astra would need to:

1. Version the experiment anew; replace the arms with `vocab_decision` and
   `paired_action`; use the four fit/generate stages with `paired_action`
   first; bind the new objective recipe and lower evaluation/stage limits.
2. Extend `build_rows` to encode both candidates, prove exact shared IDs before
   the first difference, assert the first difference is at the same native
   position and maps target 0/1 to two distinct pinned tokens, and save
   `decision_input_ids = candidate0_ids[:decision_position]`. Assert this
   tensor is byte-identical whichever target is designated and its assistant
   continuation contains no branch token, suffix, LF, EOS, or padding. Hash
   it separately.
3. Construct and serialize all 64 `(slot,template)` mode pairs, the exact
   target-blind canary selection trace, and the common 256-step schedule.
4. Delete the label-mask dispatch for training. Add one manual forward that
   supplies only `decision_input_ids`, no `labels`, an all-one attention mask,
   and `use_cache=False`; compute the two equations above in FP32, validate
   finite loss/logits, then perform exactly one backward and AdamW step.
   Log canonical raw `d`, signed margin, V and P losses from the same logits,
   actual logit/loss dtype, and row/input hashes.
5. Add an ordered initialization/optimizer receipt: trainable name, shape,
   dtype and initial tensor digest; LoRA A/B zero/nonzero convention; exact
   optimizer parameter order and param-group values; and proof that optimizer
   state is empty. Require exact cross-arm equality before interpretation.
6. Hash CPU and CUDA RNG state immediately before every training forward and
   require the full 256-hash sequences to match across arms. Record the
   pre-step-0 logits digest. Run the symmetric early diagnostic described
   above, asserting no RNG or named-buffer mutation around its eval calls.
7. Make evaluation return both canonical `d=t0-t1` and signed gold margin.
   Reduce all fixed cells/pairs, paired arm discordance, class-stratified
   P-minus-V margins, action concentration and strict validity.
8. Add result-conditioned terminal states and a clean early-canary stop path.
   A scientific canary miss must preserve its two steps and cleanup evidence
   in a sealed `EARLY_PAIRWISE_LOCAL_SEPARATION_STOP`, not masquerade as a
   generic integrity exception. Integrity mismatches remain nonreportable.
9. Bind exact actual cost: main and early-diagnostic forwards/examples,
   optimizer steps, generated tokens, stages, wall time and lease/cleanup.
   Preserve no retry/resume and fresh reload identity.

The prepared `recipe` must not continue claiming the unchanged gateway
`EXECUTION_RECIPE`: model/LoRA/AdamW fields are inherited, but input formation,
objective, arm order, early gate and schedule are new versioned fields.

## Exact focused-test additions/replacements

In `tests/test_semantic_objective_probe.py`, Astra would need golden tests that:

1. verify all 128 common prefixes against both native candidate encodings,
   flip every target and prove training-input/hash invariance, reject a shared-
   prefix/index/token mismatch, and enumerate 64 opposite-target mode pairs;
2. freeze canary hash selection and schedule bytes and prove selection is
   independent of gradient, logits and outcomes;
3. use real small CPU Torch tensors to prove both loss equations, P's
   equivalence to `softplus`, target reversal, finite FP32 behavior, and that
   P logit gradients are nonzero only on the two legal tokens with opposite
   signs while V assigns mass outside them;
4. prove the training call receives only the common prefix, no labels/gold
   token/future suffix, performs one forward/backward/update, and fails before
   update on nonfinite loss/logits or missing/nonfinite gradients;
5. prove ordered trainable/optimizer receipts and empty state, not unordered
   dtype counts, and mutation-fail every name, shape, dtype, parameter order,
   beta/epsilon/weight-decay/foreach/fused value and initialization digest;
6. prove per-step CPU/CUDA RNG equality is required, an arm-specific random
   draw is rejected, and symmetric eval diagnostics preserve RNG, buffers and
   train/eval mode;
7. exercise a conditional toy model where the first two updates move the two
   raw odds oppositely and a bias-only toy model where both move together and
   the canary stops before step 3 and before the V worker;
8. recompute canonical versus signed margins, all label/cell/template/stratum
   and 64 pair denominators, paired discordance and both class-stratified
   P-minus-V means from complete raw fixtures;
9. cover every equality boundary immediately above and below the acquisition
   thresholds and all terminal classifier branches/precedence; and
10. update controller tests to four fresh stages, 512 maximum optimizer
    steps, 256 generations/final margins, explicitly capped early diagnostic
    work, fresh reloads, deadline failure, cleanup, no retry, and both the
    reportable canary stop and nonreportable integrity stop.

Mocks are appropriate for lifecycle failures, but mocked `output.loss` cannot
validate the new scientific core; the small-tensor objective and bias-only
tests must exercise actual autograd on CPU.

## Hidden confounds and required disposition

- **Initialization:** equal seed and a zero-B check are insufficient. LoRA A is
  randomly initialized, parameter enumeration controls AdamW slots, and a
  tensor-count dtype receipt loses order/shape. Require exact initial tensor
  digest plus ordered inventory and step-0 logits/RNG equality.
- **RNG/dropout:** LoRA dropout is `0.05`. Same seed does not prove the two
  fresh processes reach each forward at the same RNG counter. Per-step
  pre-forward hashes are required; early eval calls must be symmetric and
  demonstrably RNG-neutral.
- **Target shape:** SEQ-089's one-live-label arm still forwarded the complete
  target-shaped 7/8-token sequence. Merely masking, padding, or appending the
  gold token to the new input retains a target-dependent numerical path.
  Prefix-only input is the decisive repair.
- **Optimizer:** AdamW is not invariant to the V/P gradient substitution,
  epsilon, moments and weight decay. That difference is the treatment, not a
  nuisance to explain away. A raw-gradient directional derivative is not a
  valid prediction of an AdamW step; the early gate must observe the actual
  two budgeted updates.
- **Dtypes:** the pinned base/logits are BF16 while observed LoRA parameters,
  gradients and moments were FP32. Form both losses from `logits.float()` and
  record actual ordered dtypes. Do not compare a native HF CE scalar in one
  arm with an explicit FP32 scalar in the other.
- **Online metrics/order:** dropout-active pre-update rows occur at different
  checkpoints and are not a balanced learning curve. Only the common final
  dropout-off panel is gate-bearing. Canary-first order is new and must be
  identical across arms.
- **Teacher-forced versus free action:** forcing `ACT: -` can reveal a branch
  preference that the model never reaches freely. Both positive signed
  margins and strict unprefilled generations on the same paired rows are
  mandatory.

## Prospective stop rules

1. **Before GPU:** stop with no model load if any source/input/seal/tokenizer
   hash changes; there are not exactly 128 unique prefixes, 64/64 targets,
   64 complete opposite-label mode pairs, two distinct branch tokens, a
   target-independent common prefix for every row, or one fixed eligible
   canary pair. No padding fallback or alternate token boundary is allowed.
2. **Integrity at runtime:** any device/base/runtime mismatch, unequal initial
   tensor or ordered optimizer receipt, nonempty initial optimizer state,
   unequal pre-forward RNG sequence, changed early-eval RNG/buffer state,
   nonfinite/missing gradient or update, incomplete fixed denominator,
   adapter/reload/hash/cleanup/deadline failure is `NONREPORTABLE_ABORT`.
   Launch no replacement or retry.
3. **Early scientific stop:** if P's two already-budgeted canary updates do
   not move the opposite-label raw odds in opposite correct directions, seal
   `EARLY_PAIRWISE_LOCAL_SEPARATION_STOP`, launch no V worker, and do not tune
   the pair, seed, LR or order. This rejects this local pairwise path, not
   LoRA capacity in general.
4. **Final classification:** if P passes and V fails and both target-stratified
   P-minus-V mean signed-margin differences are positive, report
   `PAIRWISE_FOCUS_SUPPORT_THIS_INSTANCE`. If both pass, report
   `COMMON_PREFIX_PATH_SUPPORT_PAIRWISE_NOT_NECESSARY`; if V alone passes,
   report `PAIRWISE_REJECTED_THIS_INSTANCE`; if neither passes, report
   `TERMINAL_OBJECTIVE_NULL_THIS_INSTANCE`. Any acquisition pattern failing
   the required class-stratified causal contrast is
   `ACQUISITION_WITH_AMBIGUOUS_OBJECTIVE_CONTRAST`, not pairwise support.
5. **Program stop:** on the early stop or final neither-pass, end rank/LR/heat,
   paraphrase, mask and objective tuning on this semantic-writer assay and
   revisit carrier/representation/task construction. A P-specific positive
   permits only a separately preregistered held/spill qualification; it does
   not alter Q0 or any paper-level claim by itself.

This is the smallest path that tests the remaining pairwise optimizer idea,
rules out a constant/global-action explanation on matched opposite-label
conditions, avoids target-future shape, and stays below the already spent
SEQ-089 GPU envelope.
