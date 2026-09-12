# Adjudication: one-root pairwise binding falsifier after Q0 and SEQ-089

**Date:** 2026-09-12
**Status:** fresh scientific adjudication; **REWORK, then launch the single
contract below**. The checked-in SEQ-089 probe cannot execute this contract.
This memo changes no builder code, launches or stops no job, and does not edit
`research_loop/COORDINATION.md`.
**Fit cap:** at most three fresh fits are attempted. `OFF` and the initial
objective audit are no-update states, not fits.

## Ruling

The next writer spend remains the frozen root-1 Q0 surface, before Level 1 or
W-H1. The launch target is not a semantic simplification: it retains the eight
opaque tools, two modes, eight exact and four held phrasings, the arbitrary
`orientation(tool) XOR mode` map, its exact complement, strict unprefilled
generation, and the complete locality surface.

Run two mandatory pairwise cells, `P_AUTH` and `P_DERANGED`, using
target-independent natural common prefixes and four-prompt XOR quartets as the
optimizer unit. A third slot is assigned prospectively by a no-update
objective-separation audit and the fixed release rules below:

1. `V_AUTH` if full-vocabulary and two-action gradients are nondegenerate at
   initialization and both pairwise canaries pass;
2. otherwise `P_UNARY_TOOL` only when an XOR canary or exact-acquisition gate
   has failed and the unary cell can localize opaque-key writing versus the
   tool-by-mode interaction; or
3. no third fit when the objectives are degenerate and both pairwise maps pass
   exact acquisition.

This dominates a mandatory `V_AUTH`: at a common prefix
`L_V-L_P=-log M`, where `M` is the total probability of the two legal branch
tokens. If `M` and the parameter gradients already make that contrast
negligible, another vocabulary fit is not a meaningful control. It also
dominates replacing the complement with a vocabulary arm: AUTH alone cannot
establish arbitrary conditional binding.

The current evidence supports the descriptive statement that large common
output changes coexist with failed key-conditioned decisions. It does not yet
establish “common-mode domination” as the cause. Balanced labels prevent a
global answer prior from passing the registered gates; they do not generally
make the cross-entropy gradient of a prompt-independent bias vanish.

## Disagreements disposed

| issue | adjudication |
|---|---|
| Two-prompt mode pair versus four-prompt canary | Use a four-prompt XOR quartet: two opposite-orientation tools, both modes, one template. A two-prompt pair can pass by learning `m0 -> a0, m1 -> a1` while ignoring the tool. |
| Empirical `epsilon` versus a real directional test | Repeated dropout-off forwards must be bit-identical. Gate both FP64 `signed <grad(d), parameter_delta>` and the observed signed FP32-recomputed margin change for all four prompts. A zero empirical spread is not a meaningful tolerance. |
| Same-tool pair versus quartet optimizer units | Use the quartet for every step. This balances action, mode, orientation, and tool within the optimizer update and directly presents the interaction that failed Q0. |
| Mandatory vocabulary control versus possible degeneracy | Audit natural-common-prefix `M` and actual LoRA gradients before fitting. Run `V_AUTH` only when the contrast is nondegenerate. Otherwise spend the possible third cell on the unary opaque-tool localizer, and only after XOR failure. |
| AUTH objective contrast versus complementary qualification | `P_AUTH` and `P_DERANGED` are the mandatory qualification pair. `V_AUTH` is only an objective-control cell and cannot qualify a vocabulary-loss arbitrary writer without its own future complement. |
| Coupled canaries versus executable lifecycle | Run serially on one A40. Each fit's first quartet is its real first optimizer step and the worker either stops there or continues uninterrupted. Do not pause/resume, restore a partially trained optimizer, occupy two GPUs, or add an out-of-budget canary update. |
| 256 pair steps versus quartet dose | Four corpus sweeps give 128 quartet updates, 512 row presentations, and 32 presentations per `(tool,mode)` key. Save at 32/64/128 updates (8/16/32 presentations per key). This preserves the proposed row-dose curve without doubling it merely to preserve a step count after enlarging the optimizer unit. |
| Exact-only screen versus writer qualification | Retain the stricter exact `.90`, held `.80`, complementary-map, strict-generation, interface, and locality conjunction. The exact-only `.80` screen from the minimal code audit is not the launch target. |
| Relative two-action TV versus locality | Gate itemwise changes in within-pair choice `q`, absolute legal branch-token mass `M`, strict legality, and strict action identity. Absolute mass is gate-bearing, not diagnostic-only. |
| Historical OFF versus contemporary OFF | Run one shared contemporary no-fit OFF panel with the same natural-prefix implementation. Historical Q0/SEQ-089 OFF remains context only. |
| Rescue attribution | A positive is evidence for the composite common-prefix, quartet-balanced, doubled-row-presentation recipe. Relative to historical Q0 it does not isolate prefix shape, batching, dose, or objective. Only a nondegenerate contemporary P-versus-V contrast speaks to normalization. |

## Frozen material and common-prefix contract

Use the archived root-1 Q0 material and seed-1 clean-base construction. Root-1
orientations are the frozen vector `[0,1,1,0,1,0,0,1]`. Let target bit zero be
`-mem2reg` and target bit one be `-gvn`:

```text
y_AUTH(tool, mode) = orientation(tool) XOR mode
y_DERANGED         = 1 XOR y_AUTH
y_UNARY(tool,mode) = orientation(tool)
```

Preparation must rediscover and pin the native branch token IDs from both
candidate encodings; the archived values `10536` and `21404` are checks, not
trusted literals. For every row, the only training input is the frozen user
prompt plus the assistant continuation through the common `ACT: -` prefix.
It contains no branch token, suffix, LF, EOS, padding, label tensor, carrier
row, explanation, or other future assistant token. Flipping any target or map
must leave its input IDs and input hash byte-identical. Each natural-length row
is forwarded separately; losses are averaged only after the four forwards.

Construct the 32 training quartets per sweep without inspecting a model:

1. Within each orientation, order the four tools by the canonical digest of
   `['Q0-XOR-PAIR-v1', root1, tool]`; pair equal ranks across the two
   orientations.
2. For every paired tool pair and each exact template `0..7`, take both modes
   for both tools in fixed `(orientation0-m0, orientation0-m1,
   orientation1-m0, orientation1-m1)` order.
3. Order the 32 quartets by the canonical digest of
   `['Q0-XOR-SCHEDULE-v1', four ordered source-row hashes]`. The first is the
   canary. Repeat this exact quartet order four times in every released arm.

Preparation stops before model load unless there are exactly 128 unique
target-independent prefixes, 64 targets of each action under AUTH and
DERANGED, 32 complete quartets, two distinct branch tokens at one common
decision position per row, the registered 8-by-2-by-8 topology, all 64 held
items, and the full locality/copy inventory. There is no padding fallback,
alternate token boundary, pair substitution, or selected retry.

## Objectives and zero-update arm selection

For natural-common-prefix last-position FP32 logits `z`, define

```text
d = z[mem2reg] - z[gvn]
s = +1 for target mem2reg, -1 for target gvn
L_P = softplus(-s*d)
L_V = logsumexp(z over the full vocabulary) - z[target]
M = softmax(z over the full vocabulary)[mem2reg]
  + softmax(z over the full vocabulary)[gvn]
```

`P_AUTH`, `P_DERANGED`, and `P_UNARY_TOOL` use the mean of four `L_P` values.
`V_AUTH` uses the mean of four `L_V` values. Both equations are formed
explicitly in FP32 from the same BF16 forward logits; native `output.loss` is
not an admissible substitute.

Before any fit, one disposable fresh-initialization worker runs with dropout
off and no optimizer step. On all 128 exact prefixes it records `M` and
`-log(M)`. On all 32 scheduled quartets it obtains the ordered LoRA-parameter
mean gradients `g_P` and `g_V` from the same forward graphs and records

```text
R = norm(g_V - g_P) / max(norm(g_P), 1e-12)
C = cosine(g_V, g_P).
```

Nonfinite values, zero `g_P`, input drift, or failure to destroy the worker
cleanly is `NONREPORTABLE_PRECHECK_ABORT`. Otherwise the V/P contrast is
`OBJECTIVE_CONTRAST_DEGENERATE_AT_INIT` if and only if every exact row has
`-log(M) < 1e-3`, every quartet has `R < .05`, and every quartet has
`C > .999`. It is `OBJECTIVE_CONTRAST_NONDEGENERATE_AT_INIT` otherwise. This
decision is sealed before fitting and is never revised from outcomes.

## Canary and optimizer lifecycle

All attempted arms use the same pinned Qwen2.5-7B-Instruct base, rank-8 LoRA,
alpha 16, dropout `.05`, zero-B standard initialization, the same seven
projection families, seed 1, BF16 base/forward, FP32 trainables/gradients/loss
and AdamW state, eager attention, and AdamW `lr=3e-5`, betas `(.9,.999)`,
`eps=1e-8`, weight decay `.01`, no scheduler or clipping, `foreach=False`,
`fused=False`, no TF32, no gradient checkpointing, and deterministic
algorithms. Each worker must begin from the exact same ordered trainable
names/shapes/dtypes/tensor digest, parameter order, empty optimizer state,
step-0 logits digest, and CPU/CUDA RNG state. Hash the pre-forward RNG state
for every one of the 512 row forwards and require equality across every pair
of full arms that is causally compared.

For the first scheduled quartet in each attempted arm:

1. With dropout off, require repeated raw logits to be bit-identical and
   compute each prompt's ordered FP32 gradient of canonical `d`.
2. Prove those diagnostic evaluations leave RNG, named buffers, train/eval
   mode, tensors, and the empty optimizer state unchanged.
3. In train mode, perform the four registered forwards in order, average the
   registered losses, do exactly one backward and one AdamW step, and retain
   the full FP32 parameter delta.
4. With dropout off, recompute each last-hidden-state/output-head dot product
   in FP32 and require, for all four prompts, both
   `s * <grad(d), delta_theta> > 0` accumulated in FP64 and
   `signed_margin_after > signed_margin_before`.
5. Record the 4-by-4 signed margin-gradient Gram matrix. It is diagnostic,
   not a substitute for the two pass predicates.

This canary rules out a pure global, mode-only, or tool-only update on the
selected quartet. It is a local tangent test, not acquisition evidence.

Execution is serial on one pinned A40:

- Attempt `P_AUTH`. A canary pass continues in the same process, with the same
  optimizer and RNG stream, through update 128. A miss seals after update 1;
  no `P_DERANGED` or `V_AUTH` is launched.
- If AUTH passes its canary, complete it before attempting `P_DERANGED`.
  DERANGED follows the same uninterrupted rule. This deliberately spends a
  completed AUTH fit before learning the DERANGED canary result; it avoids an
  untested pause/resume protocol and a cross-GPU nuisance.
- If both P canaries pass, complete both P fits. If the initialization audit
  was nondegenerate, the third slot is `V_AUTH` on the identical schedule. If
  it was degenerate, release `P_UNARY_TOOL` only when either P map later fails
  exact acquisition; otherwise stop at two fits.
- If either P canary fails, the only allowed remaining fit is
  `P_UNARY_TOOL`. It has its own first-quartet canary (tool-opposite rather
  than XOR-opposite signs) and continues only on a pass.

No worker is resumed, no optimizer is reconstructed mid-fit, no checkpoint is
selected, and no alternate seed, quartet, order, learning rate, rank, or retry
is allowed.

## Dose, checkpoints, and bounded evaluation

Each completed fit makes exactly 128 optimizer updates and 512 natural-row
training forwards: 32 quartets times four frozen sweeps. This is 32 row
presentations per `(tool,mode)` key. Save LoRA-only snapshots after updates
32, 64, and 128 without resetting optimizer or RNG; these correspond to
8, 16, and 32 presentations per key. Thus update 64 matches historical Q0's
row-presentation dose, but not its one-row AdamW step structure.

After the fit is terminal, fresh workers reload every snapshot and run the
complete 128 exact plus 64 held common-prefix dropout-off margin panel. Run
strict generation and the full locality/interface panels only at update 128.
This preserves the acquisition curve without paying for repeated expensive
generation at intermediate doses. A shared contemporary OFF worker runs the
same final panels once. Every request has a fixed denominator and no retry.

Maximum fitted work is three fits, 384 optimizer updates, and 1,536 training
row forwards, plus the sealed no-update objective audit and evaluation. The
controller must predeclare a `2,700`-second (`0.75` A40-hour) reservation cap
or the earlier lease cutoff, with exact forward, backward, generation, token,
wall-time, and cleanup counts reported. The cap is a ceiling, not a runtime
claim. Early canary and two-fit stops are part of the information-efficiency
design.

## Noncompensatory acquisition and locality gates

Only `P_AUTH` plus `P_DERANGED` can qualify the arbitrary writer. Both must
independently pass every applicable gate; averages and one-map success cannot
compensate.

### Exact forms, per P map

- at least `116/128` strict correct generations;
- at least `56/64` recall for each action;
- strict validity at least `122/128`, with zero multiple actions;
- at least `14/16` `(tool,mode)` cells have at least `7/8` correct; and
- median signed ON-minus-OFF margin gain is positive separately in both
  64-row target classes.

On the 128 identical prompts, at least `112/128` must be strict-correct under
both P adapters and flip to their complementary registered actions.

### Held forms, per P map

- at least `52/64` strict correct generations;
- at least `24/32` recall for each action (the held class denominator is 32,
  not 64);
- strict validity at least `61/64`, with zero multiple actions; and
- at least `12/16` `(tool,mode)` cells have positive median signed margin.

On the 64 identical held prompts, at least `48/64` must be strict-correct
under both P adapters and flip to their complementary registered actions.
Every final fitted state and OFF must retain native copy `8/8`.

### Locality, per final fitted state against shared OFF

For each of the frozen missing-mode (`n=8`), unsupported-mode (`n=8`),
neighbor-ID (`n=16`), and wrong-root (`n=64`) families, compute on each
natural common prefix

```text
q = softmax([z_mem2reg,z_gvn])[mem2reg]
M = full-vocabulary probability mass on those two branch tokens
A = indicator that generation is exactly one legal action
I = indicator that the fitted strict action identity differs from OFF
```

Gate every family separately:

- mean itemwise `abs(q_ON-q_OFF) <= .05`;
- mean itemwise `abs(M_ON-M_OFF) <= .05`;
- no item has either probability delta above `.10`;
- mean itemwise `abs(A_ON-A_OFF) <= .05`; and
- mean `I <= .05`.

Report valid-to-invalid and invalid-to-valid counts separately. For wrong-root
prompts, also require the fraction with two legal, mutually opposite strict
outputs under `P_AUTH` and `P_DERANGED` to be at most `.05`. Never use the
absolute value of a signed mean, normalized two-action TV alone, or
candidate-sequence BF16 scores. Legal branch-token mass is not the probability
of a full action string and must be named accordingly.

`V_AUTH`, when run, receives the same exact, held, interface, and locality
evaluation. `P_UNARY_TOOL` is diagnostic: require its exact and held aggregate
and class-recall thresholds above plus at least `7/8` tools at `>=14/16`
exact correctness. It can never satisfy or replace the complementary XOR
qualification.

## Terminal labels and precedence

Integrity labels outrank scientific labels:

1. Any source/seal/tokenizer/device/runtime/input mismatch, nonfinite value,
   unequal required initialization/RNG receipt, mutated diagnostic state,
   incomplete denominator, adapter/reload/deadline/cleanup failure, or retry
   is `NONREPORTABLE_PRECHECK_ABORT` or `NONREPORTABLE_RUNTIME_ABORT`.
2. An AUTH or DERANGED quartet miss is respectively
   `EARLY_XOR_QUARTET_STOP_AUTH` or `EARLY_XOR_QUARTET_STOP_DERANGED`. A unary
   miss is `EARLY_UNARY_TOOL_STOP`. These reject only the registered local
   path, not LoRA capacity in general.
3. If both XOR canaries pass but either P map fails the final exact gate, use
   `LOCAL_XOR_DIRECTIONS_NOT_PRESERVED`. Checkpoint curves and any unary/V
   result are diagnostic suffixes, not a rescue. Attach `MAP_ASYMMETRY` when
   exactly one P map passes exact acquisition and `BOTH_XOR_EXACT_NULL` when
   neither does.
4. If both exact gates pass but either held gate fails, use
   `STORED_NOT_EXTRACTABLE`.
5. If exact and held pass but interface or locality fails, use
   `CONDITIONAL_BINDING_WITH_SPILL_OR_INTERFACE_FAILURE`.
6. Only if both maps pass exact, held, complementary flips, copy, interface,
   and all locality gates use `SUPERVISED_ONE_ROOT_XOR_BINDING_PASS`.

When `V_AUTH` runs, attach exactly one objective qualifier:

- `PAIRWISE_NORMALIZATION_SUPPORT_AUTH_INSTANCE` only if the P writer
  qualifies, `P_AUTH` passes, `V_AUTH` fails, and mean final
  `signed_margin_P-signed_margin_V` is positive separately in both AUTH target
  classes;
- `COMMON_PREFIX_BOTH_OBJECTIVES_PASS_AUTH_INSTANCE` if both AUTH cells pass;
- `PAIRWISE_REJECTED_AUTH_INSTANCE` if V passes and P_AUTH fails; or
- `OBJECTIVE_CONTRAST_AMBIGUOUS` for every other pattern.

If the unary cell runs, attach `UNARY_TOOL_PASS_XOR_FAIL` only when its stated
gates pass; otherwise attach `OPAQUE_TOOL_WRITE_FAILURE_THIS_RECIPE`. These
qualifiers do not alter the primary XOR label.

## Claim boundary and next gate

`SUPERVISED_ONE_ROOT_XOR_BINDING_PASS` would establish that one deterministic
rank-8 LoRA recipe acquired and extracted complementary arbitrary
tool-by-mode action bindings on one finite synthetic Q0 root while respecting
the registered local scope. Its complementary, class-recall, key-coverage and
locality conjunction excludes a constant action prior, a pure mode rule, and
a pure tool rule as explanations of the pass.

It would not establish seed/root robustness, a general writer, experiential
memory, retention, parenting, DREAM/SLEEP, H1, H2, clean lineage, or general
LoRA capacity. A P-versus-V result concerns normalization in this AUTH
instance only. An initial V/P degeneracy supports no pairwise-necessity claim.
A unary result localizes the failure but can never weaken or replace the XOR
target.

On any early XOR stop or final exact failure, end rank/LR/heat/paraphrase and
objective tuning on this Q0 writer family and revisit representation/task
construction, using the unary result if available. On exact pass but held
failure, vary views at fixed acquisition dose. On locality failure, repair
routing/scope. Only a full two-map pass permits the already ordered Level-1
test; W-H1 remains the non-negotiable exact paper-surface gate after Level 1.

## Evidence checked

- `research_notes/analysis/2026-09-12_binding_writer_failure_diagnosis_and_minimal_falsifier.md`
- `research_notes/analysis/2026-09-12_pairbalanced_common_prefix_falsifier_scientific_redteam.md`
- `research_notes/analysis/2026-09-12_binding_writer_gate_priority_decision.md`
- `research_notes/analysis/2026-09-12_pairwise_writer_path_fresh_audit.md`
- `research_notes/analysis/2026-09-12_semantic_w0_common_mode_terminal_reduction.md`
- `research_notes/analysis/2026-09-12_semantic_objective_terminal_reduction.md`
- `research_notes/analysis/2026-09-12_semantic_objective_terminal_fresh_postaudit.md`
- `research_notes/astra_memos/ASTRA_SEMANTIC_WRITER_TERMINAL_2026-09-12.md`
- `research_notes/astra_memos/ASTRA_SEMANTIC_RESCORE_TERMINAL_2026-09-12.md`
- archived Q0 terminal capsule SHA-256 `422b27e5...65f0`
- archived SEQ-089 terminal capsule SHA-256 `d7524e0a...3390`, including
  `report.json` SHA-256 `4ca53169...659`, all 128 rows and both 256-step traces
- `research_notes/astra_memos/receipts_20260912/astra_objective_analysis_20260912.json`
- `research_notes/astra_memos/receipts_20260912/astra_canonical_seq087_090_review_20260912.md`
- current immutable SEQ-089 module/test hashes `98a90f33...d41` and
  `0a327ab0...e0`
- `organism_v6/semantic_writer_diagnostic.py`
- `organism_v6/multikey_writer_gateway_simple.py`
- `research_loop/COORDINATION.md` Q0, SEQ-089, and 19:41--19:48 UTC entries

The archived facts supporting this disposition are unchanged: Q0 held
generation is `37/64`, `33/64`, `32/64`, and `34/64`; exact generation is
`68/128`, `68/128`, `64/128`, and `63/128`, with coarse single-action
collapse. SEQ-089's full-response and first-choice arms each produced
`64/128`, generated `-gvn` on `128/128`, shared the exact initial LoRA tensor
digest, and made nonzero updates. The first-choice arm still forwarded
target-dependent 7/8-token future shapes, so it is not the common-prefix V
control specified here.
