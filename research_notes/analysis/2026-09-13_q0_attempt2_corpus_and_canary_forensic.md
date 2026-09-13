# Q0 attempt 2: corpus, token, and first-update-canary forensic

**Date:** 2026-09-13 UTC  
**Role:** fresh watcher-side forensic requested after Rohin message 32.  
**Mutation scope:** research note only. I did not change builder source, the
sealed Q0 root, a model, tokenizer, adapter, GPU, threshold, or future
experiment. I did not inspect any Q0-FULLDOSE output.

## Bottom line

I found **no target-map, token-boundary, schedule, or loss-masking defect** in
the frozen Q0 attempt-2 material. The 128 exact labels match the intended XOR
map, the opposite map is its exact complement, the optimizer sees only a
target-independent natural prefix, and the two branch IDs are stable.

I did find a decisive **test-design defect in the first-update stopping rule**:
one mean-loss optimizer update was required to improve every one of four
individual examples. That is not what the optimized objective guarantees. On
this actual surface the base model begins with an enormous `-mem2reg` bias, so
cross-entropy gives almost all first-step weight to the two `-gvn` targets and
almost none to the two already-correct `-mem2reg` targets. The sealed gradient
geometry predicts the observed `2/4` signed-projection pattern before using the
actual AdamW delta.

This means:

> Attempt 2 validly proves that the registered all-four first-update
> conjunction failed. It does **not** test whether the prospectively specified
> 128-update rank-8 Q0 fit would acquire the table.

The result is therefore evidence against the canary as a learnability gate,
not evidence that the corpus was malformed or that LoRA cannot write opaque
tool-by-mode bindings. Continuing with a newly declared full-dose contract is
scientifically justified; it is not a rescue of attempt 2.

## Evidence inspected

- frozen counter-repair source capsule
  `astra_q0_counter_source_20260913_attempt1.tgz`;
- frozen executor `gpu/astra_pairwise_q0.py` and its focused tests;
- original sealed Q0 material projected from capsule SHA-256
  `422b27e5...65f0`;
- attempt-2 metadata capsule SHA-256 `5b5184a6...483`, including the native
  `prepared.json`, zero-update audit, OFF readouts, and all three stopped
  first-update records;
- the binding adjudication, implementation closure, mathematical red-team,
  and prior independent raw-tensor terminal audit.

The independently reproduced terminal and tensor arithmetic remain accepted:
`EARLY_XOR_QUARTET_STOP_AUTH`, with projection/observed counts AUTH `2/4,
3/4`, DERANGED `2/4, 1/4`, and unary `2/4, 2/4`. The separate CPU reducer
thread-count defect documented in the terminal audit is real but label
invariant and unrelated to the corpus finding below.

## 1. Material and labels: correct

The source material is exactly:

- 8 opaque root-1 tool identifiers;
- 2 modes;
- 8 training phrasings, giving `8 x 2 x 8 = 128` exact rows;
- 4 held phrasings, giving `8 x 2 x 4 = 64` held rows;
- 8 missing-mode, 8 unsupported-mode, 16 neighbour-ID, 64 wrong-root, and 8
  copy rows.

For AUTH, every exact target equals `orientation(tool) XOR mode`. All `128/128`
original `W+` targets match the executor's reconstructed target, with `64/64`
class balance. All `128/128` original `W-` targets match the exact complement,
also `64/64`. Unary correctly removes mode and targets orientation alone.

Every optimizer unit has two opposite-orientation tools, both modes, and one
shared template. Each quartet is `2/2` balanced for AUTH, DERANGED, and unary.
All 128 rows occur once per sweep and the same 32-quartet schedule is repeated
four times. Scheduling uses target-free coordinates. There is no plus/minus
label in the prompt because AUTH and DERANGED are separate fresh adapters;
therefore Rohin's proposed “opposite maps blending together” cannot explain
attempt 2. The two maps were never trained into one adapter.

## 2. Tokenization and target placement: correct, with one scope limit

Across all 288 non-copy prompts:

- the complete decision-prefix length is 90--102 tokens;
- the assistant-only suffix is exactly the same three tokens decoding to
  `ACT: -`;
- the divergent branch IDs are always `[10536, 21404]`, decoding first to the
  `mem...` versus `gv...` branches;
- both complete candidates share the exact prefix and diverge at the recorded
  decision position;
- neither target branch enters the assistant span before the decision;
- no padding, EOS, suffix, or target-shaped label enters the forward.

Both branch IDs do occur once in every **user** prompt because the prompt lists
both permitted answers in a fixed order. This is symmetric with respect to the
row target and is not label leakage. It does, however, make the bounded task a
candidate-conditioned choice problem, not arbitrary free generation.

The executor does not use ordinary SFT labels or a masking tensor. It forwards
the common prefix, reads the two branch logits, and applies
`softplus(-s*(z_mem-z_gvn))`. Consequently the inherited material field
`context_masked=true` is descriptive legacy metadata, not a hidden masking
operation. The loss implementation and target-bit indexing are correct.

Only the first divergent token is trained. The remaining action suffix is not
a target. This is an intentional minimal choice writer, and final strict
unprefilled generation would have checked the entire action string and
interface if a fit had reached it. It weakens the breadth of a possible pass;
it does not explain the early stop.

## 3. Actual defect: the first-update conjunction contradicts the objective

At zero update, the base margin

```text
d = z_mem2reg - z_gvn
```

is positive on **128/128 exact rows**, with range `1.875 .. 9.0` and mean
`5.5098`. Greedy OFF generation is correspondingly almost constant:

```text
exact: 127/128 mem2reg, 1/128 gvn
held:   63/64  mem2reg, 1/64  gvn
all non-copy generation panels: 286 mem2reg, 2 gvn
```

On all 64 AUTH `mem2reg` targets the mean pairwise-loss derivative weight is
only `0.01049`; on all 64 `gvn` targets it is `0.98941`. Balanced labels did
not create balanced gradient pressure. It only prevented a constant policy
from passing the eventual full-surface accuracy gate.

The registered first quartet makes the mechanism especially transparent. Its
dropout-off margins are:

```text
[5.5377, 7.5417, 5.2742, 5.4192]
```

For AUTH signs `[+,-,-,+]`, the four loss derivative weights are:

```text
[0.00392, 0.99947, 0.99490, 0.00441]
```

Let `h_i = s_i grad(d_i)` and let `G_ij=<h_i,h_j>` be the sealed signed Gram
matrix. For an ordinary deterministic SGD step on the mean pairwise loss, the
unscaled desirable projection for row `j` is

```text
(1/4) sum_i weight_i G_ji.
```

Using only the sealed margins and Gram matrix gives:

```text
AUTH       [-5163, +5337, +6341, -5401]
DERANGED   [+4874, -4870, -5688, +5111]
UNARY      [-4914, -4992, +6752, +5894]
```

Those signs predict the exact observed **2/4 projection split in every arm**.
The actual AdamW projections differ in magnitude but not in this pattern.
This is not an obscure numerical edge: the negative recorded projections are
about `-4.1` to `-4.6`, versus error bounds around `4e-8`.

The reason is simple. The four prompts initially induce very similar raw
action-margin directions. Cross-entropy concentrates the first update on the
two currently wrong `gvn` rows, so it mostly lowers the common `mem2reg`
margin. That helps the two wrong rows and can hurt the two already-correct
rows. A mean objective is allowed to make this trade.

The stopped step even supplies direct evidence of that mismatch:

```text
dropout-off mean pair loss, AUTH:  3.2075 -> 3.0648  (improved)
dropout-off mean pair loss, unary: 2.6768 -> 2.3785  (improved)
```

Both were rejected because not every constituent margin improved. DERANGED's
dropout-off mean changed `2.7427 -> 2.7502`, a small worsening under its
dropout-active update; that is a valid one-step observation but still not a
full-dose learnability result.

## 4. Why one step is additionally unrepresentative for this LoRA

The native audit proves standard fresh LoRA initialization: every `lora_B`
matrix is zero while `lora_A` is nonzero. On the first backward pass, useful
task gradient initially reaches the B side; only after B becomes nonzero can A
learn new input projections. Requiring the very first update to already
improve four opposing opaque-key/mode cases assumes that the random initial A
projection contains the complete separable interaction. The proposed 128-step
fit exists precisely to create and refine that interaction, but the stop rule
prevents it.

LoRA dropout `.05` makes the gate still less suitable: training uses four
sequential dropout-active forwards while the canary evaluates a dropout-off
surface. The contract correctly narrows a miss to this exact sampled path, but
then incorrectly uses that path to prevent measuring the actual acquisition
endpoint.

Finally, the canary observes one hash-selected quartet—two tools and one of
eight templates. It is not an average over the table. All three attempted arms
reuse that same geometry, initialization, and dropout RNG. Their three `2/4`
patterns are therefore not three independent pieces of evidence.

## 5. Corpus and endpoint risks that are real but did not cause this stop

These are **theoretical or claim-scope risks**, not diagnosed implementation
defects:

1. **Fixed answer order and meaningful action names.** Every user prompt lists
   `-mem2reg` before `-gvn`. The all-row base bias could be a first-option copy
   prior, a lexical/compiler prior, or both. The current data cannot separate
   them. It materially affects optimization geometry even though labels are
   balanced.
2. **One root, one initialization.** A future pass remains a finite-table
   engineering result, not robustness or connected experiential knowledge.
3. **Opaque identifiers are long and held rows reuse the same identifiers.**
   Held wording tests paraphrase extraction, not new-key generalization. That
   is the intended claim but must remain explicit.
4. **Locality panels are not fully format matched.** Wrong-root rows use the
   root-0 `Tool/mode` dialect while training uses root-1 `Unit/setting`; the
   missing/unsupported/neighbour panels use another terse wording. These can
   miss spill that is active only under the trained phrasing distribution.
   They do not affect the early result.
5. **Repeated sweep order.** The same deterministic quartet order is used four
   times. This can create order effects at full dose, but no evidence exists
   either way because only update one ran.
6. **Candidate-conditioned first token.** A pass would establish selection of
   one of two supplied actions followed by strict completion—not general
   thought/action sequence compilation.

None of these licenses changing a completed result. They constrain what Q0
could have established and motivate side diagnostics for the successor.

## 6. Cheap additions that do not change the Q1 primary contract

1. **Always publish the zero-update bias audit.** From already required OFF
   logits, report the full `d` histogram, OFF action counts, and pairwise
   derivative-weight mass by target class. This would have exposed the
   `0.0105` versus `0.9894` gradient imbalance before launch.
2. **Add a reducer-only objective-compatible first-step diagnostic.** Report
   before/after mean pair loss, target-class mean signed margin, and number of
   individual improvements. Keep it descriptive; never use an all-example
   conjunction to stop a full-dose fit.
3. **Add a CPU regression demonstrating the false-negative geometry.** A
   factorized zero-B XOR toy should start with a strong one-action bias, miss
   the all-4 first step, and learn after subsequent updates. The existing toy
   begins with the ideal XOR feature already present and therefore cannot test
   this failure mode.
4. **Add a no-fit prompt-order sidecar.** On a small fixed subset, reverse the
   order of the two listed alternatives while leaving the requested task
   unchanged. Report how much `d` and greedy choice move. This separates
   first-option pressure from lexical action prior without selecting or
   changing Q1.
5. **At Q1 checkpoints, report both target classes separately.** Early
   debiasing followed by conditional separation is the expected trajectory;
   aggregate loss alone can hide it, and per-row monotonicity falsely rejects
   it.
6. **Optionally add same-dialect foreign-ID locality later.** This strengthens
   spill interpretation but should be a non-primary side panel, not a post-hoc
   amendment to the frozen Q1 gate.

## Disposition

Classify the evidence as follows:

- **Actual defect:** the registered per-row `4/4` first-update efficacy stop;
  the previously documented unbound reducer thread count is a separate exact-
  replay defect.
- **Expected optimization geometry:** all-action base bias, saturated
  cross-entropy weights, zero-B first-step restriction, shared prompt
  gradients, and dropout-active versus dropout-off variation.
- **No defect found:** target reconstruction, complementary maps, label
  balance, target-free schedule, natural common-prefix tokenization, branch-ID
  ordering, or target leakage into the assistant prefix.
- **Unresolved because it never ran:** whether 128 updates acquire exact and
  held mappings, whether strict action generation survives, whether locality
  holds, and whether rank/rate/dose are adequate.

The old primary label must remain immutable. The scientifically correct next
sentence is: **the early-stop test was too strong and objective-incompatible;
the full-dose endpoint remains unmeasured.**
