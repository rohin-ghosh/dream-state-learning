# Scientific red-team: pair-balanced common-prefix binding falsifier

**Date:** 2026-09-12  
**Status:** independent read-only scientific/code review; **REWORK before
launch**.  
**Scope:** the proposed three-fit experiment in
`2026-09-12_binding_writer_failure_diagnosis_and_minimal_falsifier.md`, the
current coordination evidence through the Q0/SEQ-089/SEQ-098--103 entries,
the locally archived semantic artifacts, and the applicable training paths.
I changed no builder code, launched/stopped no job, and did not edit
`research_loop/COORDINATION.md`.

## Verdict

The proposed final **AUTH + exact-complement DERANGED**, exact-form, held-form,
strict-generation conjunction is a sound operational test of conditional
binding on this finite synthetic surface. A constant action prior cannot reach
both action recalls, the per-key gates, or promptwise complementary flips.
Those parts should be retained.

The experiment is not launch-ready as written, however, and its strongest
mechanistic claim is overstated:

1. the two-prompt canary rules out only an input-independent action bias; it
   can pass by learning the globally available `m0` versus `m1` feature and
   therefore does not test the opaque-tool-by-mode XOR that failed Q0;
2. balanced labels do not in general cancel the cross-entropy gradient of a
   global action bias;
3. `V_AUTH` versus `P_AUTH` may be almost a null contrast because the two
   legal branch tokens can already exhaust the distribution after the forced
   `ACT: -` prefix;
4. the locality gate repeats the previously identified blind spot by making
   absolute legal-branch mass diagnostic rather than gate-bearing;
5. the coupled “run two updates in both P cells, then continue both” lifecycle
   is not specified without pausing/resuming optimizer state or occupying two
   GPUs; and
6. the three full fits jointly change prefix shape, minibatch structure and
   effective row dose relative to Q0. They can establish a working recipe,
   but cannot attribute a rescue to pairwise normalization alone.

My recommended repair is still at most three fits. Replace the pair canary
with a **four-prompt XOR quartet**, audit objective separation before fitting,
make absolute branch mass a locality gate, and use balanced quartets as the
optimizer unit. If the V/P contrast is numerically degenerate at OFF, spend
the third fit on a unary opaque-tool control instead of an effectively
duplicate vocabulary arm.

## What the existing evidence actually localizes

The negative observations are strong but the causal diagnosis must remain
prospective.

- The four Q0 adapters are near chance on both held and exact training forms
  and mostly select one action. This excludes a held-paraphrase-only failure
  for those instances.
- SEQ-089's decision-only fit made a real update yet selected `-gvn` on all
  128 exact prompts. Therefore common response-prefix, suffix and EOS loss is
  not necessary for the collapse. Known target-dependent 7/8-token BF16 shape
  exposure prevents treating that fit as a clean common-prefix test, but the
  result already weakens “carrier-token gradients are the cause” relative to
  “the optimizer follows an easier global calibration basin.”
- SEQ-103 shows that the original elementary checkpoint really has a constant
  red readout under HF/PEFT as well as vLLM, while EOS is learned almost
  perfectly. That rules out a required backend/load explanation for that
  checkpoint; it does not identify why the conditional gradient lost.
- `train_adapter_v3.py` validates the SEQ-101 accounting correction: it uses
  the model's mean token loss and backpropagates `loss / grad_accum`. It is not
  the Q0 execution path. Q0 and SEQ-089 use their own one-row AdamW loops in
  `semantic_writer_diagnostic.py` and `astra_semantic_objective_probe.py`.
  The new manual P/V loss therefore needs its own complete optimizer, RNG and
  batch-denominator contract; inheriting the V3 name or recipe is insufficient.

The defensible current statement is thus: **these adapters strongly changed
common output behavior but did not create usable key-conditioned decisions**.
“Common-mode domination” is a plausible model, not yet a demonstrated cause.

## Mathematical correction: balance blocks success, not all bias gradients

Let `d_i = z_i(mem2reg) - z_i(gvn)`, `s_i` be the correct sign, and include a
prompt-independent bias `b`, so the pairwise loss is

\[
L(b)=\frac1N\sum_i \operatorname{softplus}[-s_i(d_i+b)].
\]

Then

\[
\frac{\partial L}{\partial b}
=-\frac1N\sum_i s_i\,\sigma[-s_i(d_i+b)].
\]

`sum(s_i)=0` does **not** make this derivative zero unless the prediction-
dependent weights also match. For one positive/negative pair the derivative
is `0.5[-sigmoid(-d_pos-b) + sigmoid(d_neg+b)]`. A global bias can therefore
receive a large early update by centering an initially skewed prior, although
it cannot solve a fixed-denominator balanced-accuracy gate. The proposal
should say that balance prevents a global prior from **passing**, not that it
removes its optimization gradient.

The exact V/P relationship is also important. With
`M_i = p(t0|x_i)+p(t1|x_i)`,

\[
L_V-L_P=-\log M_i.
\]

Thus the only V/P difference at a common prefix is the gradient that raises
total mass on the two legal branch tokens. It is not an independent source of
binding information. In the locally archived SEQ-089 first training row,
`decision_ce=0.0076213782` and the gold-versus-other margin is `4.875`. Those
numbers imply `p_gold=0.9924076`, `p_other~=0.0075771`, and
`M~=0.9999847`: only about `1.53e-5` probability lies outside the pair in that
target-shaped forward. Because the known BF16 length effect makes this one row
noncanonical, it is not enough to delete `V_AUTH`; it is enough to require a
full natural common-prefix OFF audit before paying for it.

## Why the proposed two-prompt canary can false-pass

For one tool and one template, W+ has opposite labels for `m0` and `m1`.
Requiring their margins to move oppositely rejects a pure common shift in `d`,
but a mode-only rule

```text
m0 -> action A
m1 -> action B
```

passes perfectly. That rule ignores the opaque tool. It then fails on tools
with the opposite orientation, which is exactly the multi-key interference
the canary is supposed to localize. Calling a failed/passed pair
`LOCAL_CONDITIONAL_GRADIENT_*` is therefore too broad.

The repaired canary should use four prompts with one shared template:

```text
tool U (orientation 0): m0 -> a0, m1 -> a1
tool V (orientation 1): m0 -> a1, m1 -> a0
```

Select the quartet by a prospective canonical hash from opposite-orientation
tool pairs. The archived root-1 native inventory contains equal-length choices
(for example slots 0 and 2 have equal token length within every shared
template), so no future padding is required for the selected canary. Do not
hard-code that favorable example; freeze the hash rule and complete eligible
inventory before model access.

One optimizer update must average all four losses before stepping. The four
targets are balanced overall, within mode, within orientation, and within
tool. A global action bias, mode-only rule, or tool-only rule cannot move all
four margins correctly; the required signal is the tool-by-mode interaction.
Run the same quartet and update formation in all fitted cells.

The proposed numerical floor `epsilon = maximum repeated raw-logit spread` is
also inadequate. Deterministic repeated BF16 forwards often give exactly zero
spread, so an arbitrary one-ULP change passes; converting BF16 logits to FP32
after the matmul does not restore lost precision. Require instead:

- repeated dropout-off forwards are bit-identical, otherwise integrity abort;
- before the update, compute the four FP32 per-prompt margin gradients;
- after the actual AdamW step, retain the FP32 parameter delta and require
  `s_i <grad(d_i), delta_theta> > 0` for all four prompts, accumulated in FP64;
- independently require the observed dropout-off signed margins to increase
  for all four, preferably with the final hidden-state/output-head product
  recomputed in FP32 and agreement in sign with the projection; and
- record the complete 4x4 signed gradient Gram matrix. Its off-diagonal
  structure is more diagnostic of multi-key conflict than two raw signs.

This tests the actual optimizer step while avoiding the false precision of a
zero empirical noise floor. A canary pass remains a local tangent result, not
full acquisition.

## Acquisition and locality gates

The proposed exact and held gates are appropriately noncompensatory and should
stay. Spell their integer forms out to avoid rounding ambiguity:

- exact: at least `116/128` correct per P map, at least `56/64` recall for
  each action, at least 14/16 key-mode cells at `>=7/8`, and at least
  `112/128` identical prompts correct under both complementary adapters;
- held: at least `52/64` correct per P map, at least `48/64` recall for each
  action, at least `48/64` promptwise complementary double-correct flips, and
  the stated 12/16 key coverage;
- all primary results require strict unprefilled generation as well as the
  common-prefix signed margin. A forced `ACT: -` score cannot compensate for
  failure to enter the interface freely.

The locality section needs a substantive repair. Define, from one natural
common-prefix FP32 forward,

```text
d = z0 - z1
M = softmax(z)[t0] + softmax(z)[t1]       # absolute legal branch-token mass
q = softmax([z0,z1])[0]                    # within-pair choice
A = strict generated single-legal-action indicator
```

For every missing, unsupported, neighbour and wrong-root prompt, gate **all**
of the following against the shared OFF record:

- mean itemwise `abs(q_ON-q_OFF) <= .05`;
- mean itemwise `abs(M_ON-M_OFF) <= .05`;
- mean itemwise `abs(A_ON-A_OFF) <= .05`, with directional valid-to-invalid
  and invalid-to-valid counts reported separately; and
- no item above `.10` on either probability delta, or a separately justified
  prospectively fixed tail bound.

Use itemwise absolute changes, never `abs(mean change)`. The prior W0 audit
already demonstrated cancellation and normalized-binary-TV false passes, and
SEQ-086 found broad three-category mass shifts around `.978--.999`. Making
`M` merely diagnostic repeats that known failure. `M` is branch-token mass,
not probability of the complete action strings; name it accordingly.

“Wrong-root redirection remains at OFF” is currently not executable. Apply
the same fixed numeric gates above to wrong-root prompts and report AUTH versus
DERANGED promptwise flips there. A qualified adapter must not acquire
complementary wrong-root flips beyond the prospective allowance.

## Dose and attribution

The proposed schedule has 64 two-row pair updates per sweep and four sweeps:
256 optimizer steps and 512 row presentations per fit. It therefore gives 32
presentations per `(tool,mode)` key, twice Q0's 16, while also changing the
input to the natural common prefix and changing one-row steps into matched
pairs. The three arms match one another, so a positive is valid evidence for
the **composite recipe**. It does not isolate pairing, prefix shape or added
dose relative to historical Q0.

`V_AUTH` versus `P_AUTH` isolates only all-vocabulary versus two-action
normalization inside that new composite. `P_DERANGED` tests target reversal
and base/map alignment. No cell supplies an optimizer-seed replication, so
even a complete pass is “this initialization/root,” not a robust writer-rate
claim.

The proposed coupled early-stop order also needs an executable lifecycle.
One GPU cannot run two P workers to two steps, keep both optimizer/RNG states
live, and then continue both without either a pause/resume protocol or doing a
full first fit before the second canary. Prefer a simple serial contract:
each P worker performs its own first real quartet update and either continues
uninterrupted or seals an early stop. If avoiding any full spend before both
canaries is essential, explicitly allocate two GPUs and bind hardware as a
nuisance, or implement and test exact optimizer/model/RNG checkpoint-resume.
Do not imply this staging is free.

## Recommended maximum-three-fit falsifier

### Stage 0: zero-fit objective-separation audit

On all 128 exact natural common prefixes, and on the 32 prospective XOR
quartets, record `M`, `L_V-L_P`, and the actual dropout-off quartet gradients
for V and P at the shared initialization. Define

```text
R = norm(g_V - g_P) / max(norm(g_P), 1e-12)
```

per quartet. Predeclare the V control as *degenerate* if every exact row has
`-log(M) < 1e-3` nats and every quartet has `R < .05` with gradient cosine
above `.999`. These are development-resolution thresholds, not biological or
paper claims. The audit costs no optimizer step and directly measures whether
the proposed objective contrast exists in this instance.

### Mandatory fits: `P_AUTH` and `P_DERANGED`

Use the exact frozen root-1 prompts and complementary maps. Form 32
prospectively matched XOR quartets per corpus sweep: pair each orientation-0
tool with one orientation-1 tool, and include both modes at the same template.
Accumulate the two natural-length same-tool pairs, average the four row losses,
then make one AdamW step. This avoids padding/target-future shape while making
every update label-, mode- and orientation-balanced.

Use four sweeps: 128 optimizer updates, the same 512 row presentations and 32
presentations per key as the proposed design. Save at 32/64/128 updates,
corresponding to 8/16/32 presentations per key. The first quartet is the real
canary described above. An own-cell canary failure stops that worker with a
scientific early-stop record; provenance/RNG/nonfinite failures are separate
nonreportable aborts.

Intermediate checkpoints need only the complete exact/held dropout-off margin
panel. Run strict generation, spill, wrong-root and copy panels at the final
fresh reload. Repeating every expensive generation/locality panel three times
adds little information; the margin curve already localizes acquisition dose.

### Third fit, selected prospectively from Stage 0

- If V and P are nondegenerate, run `V_AUTH` on the identical quartet schedule.
  Its outcome identifies only the pair-normalization effect within this
  composite recipe.
- If V and P are degenerate, do **not** pay for a duplicate control. Run
  `P_UNARY_TOOL`, with balanced target `y=orientation(tool)` independent of
  mode, on the same tools/templates/row count. Balanced opposite-orientation
  quartets then test whether the adapter can bind an opaque tool at all without
  the XOR interaction. Unary pass plus XOR failure localizes interaction or
  cross-key optimization; unary failure localizes a more basic opaque-key
  writer failure. The unary cell is a diagnostic positive control and can
  never qualify the conditional XOR writer.

This decision uses only OFF gradients, before fitted outcomes, and remains at
most three fits.

## Outcome claims

- Both P maps passing exact, held, promptwise complementary flips, strict
  generation and repaired locality establishes supervised conditional
  binding on one finite Q0 root. That excludes a global answer prior as the
  explanation of the pass.
- One P map passing and its complement failing is alignment/optimization
  asymmetry, not qualification.
- Quartet canary pass followed by exact failure means local XOR directions
  exist but the multi-update dynamics do not preserve them.
- Unary pass with XOR failure points to interaction/multi-key interference;
  unary failure points to opaque-key representation/optimization at this
  rank and recipe.
- P beating a genuinely nondegenerate V supports two-action normalization in
  this instance. If Stage 0 is degenerate, no pairwise-necessity claim is
  available.
- None of these outcomes establishes seed robustness, experiential memory,
  parenting, DREAM/SLEEP, retention, H1 or H2.

## Evidence checked

- `research_loop/COORDINATION.md`, Q0 and SEQ-089/098--103 entries through the
  current tail;
- `research_notes/analysis/2026-09-12_binding_writer_failure_diagnosis_and_minimal_falsifier.md`;
- `research_notes/analysis/2026-09-12_pairwise_writer_path_fresh_audit.md`;
- `research_notes/analysis/2026-09-12_semantic_objective_terminal_reduction.md`;
- `research_notes/analysis/2026-09-12_semantic_w0_common_mode_terminal_reduction.md`;
- `research_notes/analysis/2026-09-12_repetition_dose_normalization_correction.md`;
- `research_notes/astra_memos/ASTRA_SEMANTIC_WRITER_TERMINAL_2026-09-12.md`;
- `research_notes/astra_memos/ASTRA_SEMANTIC_RESCORE_TERMINAL_2026-09-12.md`;
- `research_notes/astra_memos/ASTRA_HF_PARITY_TERMINAL_2026-09-12.md`;
- the archived semantic writer prepared/terminal and SEQ-089 objective
  capsules, including actual root-1 rows, token lengths and first-step record;
- `organism_v6/train_adapter_v3.py`;
- `organism_v6/multikey_writer_gateway_simple.py`;
- `organism_v6/semantic_carrier_diagnostic.py`;
- `organism_v6/semantic_writer_diagnostic.py`; and
- `gpu/astra_semantic_objective_probe.py`.
