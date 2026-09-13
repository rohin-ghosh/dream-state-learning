# Result-blind protocol for the Q0 terminal audit

**Date:** 2026-09-13 UTC  
**Role:** independent terminal auditor  
**State at authorship:** result blind. I did not open the live Q0 root, inspect
its logs, query its process/GPU, or read any Q0 outcome. I changed no builder
source, test, job, adapter, model, GPU state, threshold, or claim.

## Governing precedence

Audit the sealed terminal against these sources, in this order:

1. `2026-09-12_pairwise_binding_falsifier_adjudication.md`;
2. `2026-09-12_q0_pairwise_falsifier_implementation_closure_v2.md`, whose
   amendments control where the first document differs;
3. `ASTRA_Q0_NUMERICAL_REGISTRATION_2026-09-13.md`;
4. `2026-09-12_q0_pairwise_falsifier_mathematical_redteam.md`; and
5. `2026-09-12_q0_claim_bearing_implementation_preflight.md` for executable
   receipts and test coverage.

The audit is failure-inclusive. No missing record, favorable checkpoint,
optional arm, retry, replacement seed, rounded value, or average across maps
may rescue a failed mandatory gate.

## A. Custody and identity — required before reading efficacy

- [ ] The collected directory is the exact root named by its prepared
  manifest and start receipt; controller PID, start time, bound GPU UUID,
  command, deadline and attempt number agree across receipts.
- [ ] The controller used a `2700`-second maximum reservation (or an earlier
  lease cutoff), one pinned A40, owned process-group custody, and one attempt.
  There was no pause/resume, retry, replacement fit, selected checkpoint, or
  changed seed/rank/rate/quartet.
- [ ] Executor, tests, source archive, contract, dependency allowlist,
  prepared material, tokenizer/model inventory, schedule and request-panel
  bytes are hash-bound from preparation through launch, raw collection,
  reduction and replay. No SEQ-120, birth, formation, old fitted adapter, or
  later exploratory outcome is a dependency.
- [ ] The public base is
  `Qwen/Qwen2.5-7B-Instruct@a09a35458c702b33eeacc393d103063234e8bc28`,
  with a complete matching local model/tokenizer inventory. Every fitted arm
  starts from the clean base, not another adapter.
- [ ] The archived root-1 source projection matches the frozen material:
  orientation `[0,1,1,0,1,0,0,1]`, actions `-mem2reg/-gvn`, eight opaque
  tools, two modes, eight exact and four held templates, all locality panels,
  and eight copy items.
- [ ] Raw evidence was closed before reduction. The immutable inventory/seal
  covers all raw records, adapters, snapshots, stdout/stderr, receipts and
  accounting. A fresh read-only reducer replay reconstructs the material and
  produces byte-identical report/label bytes.
- [ ] Terminal release is real: controller and owned descendants are absent,
  the selected GPU is empty of the owned process group, and cleanup/release
  receipts agree. A marker alone is not terminal custody evidence.

Any custody mismatch is an integrity abort. Stop before interpreting science.

## B. Material and forward-path integrity

- [ ] Preparation contains exactly `128` unique exact prefixes, `64` held
  items, locality families `8 missing-mode + 8 unsupported-mode + 16
  neighbour-ID + 64 wrong-root`, and `8` native-copy items. Exact and held
  template sets and all panel decision-prefix hashes are disjoint except for
  intentional cross-adapter prompt identity.
- [ ] Both complete action candidates were independently tokenized for every
  pairwise item. Their maximal common token prefix is identical, decodes to a
  natural assistant continuation ending in `ACT: -`, and re-tokenizing the
  rendered conversation through that text gives the same IDs. The next token
  is always the same rediscovered pair of distinct native branch IDs.
- [ ] The actual forward ends at that decision prefix. After the assistant
  boundary it contains no branch token, suffix, LF, EOS, padding, label,
  mask, or target-shaped tensor. The frozen symmetric user prompt may name
  both legal actions.
- [ ] Flipping AUTH to DERANGED leaves every forwarded input and schedule
  identity byte-identical. Pairing/schedule hashes use only target-free
  coordinates `(root, tool, mode, template, decision_prefix_hash)`.
- [ ] There are `32` frozen XOR quartets per sweep. Each has two
  opposite-orientation tools, both modes, one template, `2/2` targets under
  either map, and every exact row exactly once. The identical quartet order is
  repeated four times.
- [ ] Linux native acceptance and untouched dependency regressions passed on
  the exact launched source. The receipt names the environment and covers
  material/token boundaries, real Torch objectives, numerical equality and
  adjacent failures, cheap-policy canaries, RNG/state mutation, lifecycle,
  every reducer boundary, tamper rejection, replay and cleanup.

## C. Initialization, objective and lifecycle integrity

- [ ] All attempted fits use rank `8`, alpha `16`, LoRA dropout `.05`, all
  seven registered projection families, seed `1`, BF16 base/forward, FP32
  trainables/gradients/loss/AdamW state, and AdamW `lr=3e-5`, betas
  `(.9,.999)`, eps `1e-8`, weight decay `.01`, no scheduler/clipping,
  `foreach=False`, `fused=False`, no TF32/checkpointing, and deterministic
  algorithms.
- [ ] The no-update audit and every causally compared fit have identical
  ordered trainable names/shapes/dtypes, initial LoRA tensor digest and
  step-zero logits digest. Optimizer state is initially empty and its exact
  parameter order/defaults are recorded.
- [ ] Training uses explicit natural-prefix equations from BF16 logits cast
  to FP32: `L_P=softplus(-s*(z_mem2reg-z_gvn))`; `L_V=logsumexp(z)-z_target`.
  Native `output.loss` is never used.
- [ ] The zero-update audit records all `128` legal branch-token masses `M`
  and all `32` quartet P/V gradients, norms, `norm(V-P)`, R and cosine where
  defined. Its objective-contrast decision is sealed before fitting.
- [ ] Missing/disconnected/nonfinite gradients, wrong inventories or mutated
  audit state are integrity aborts. A present finite P-gradient norm at or
  below `1e-12` is instead the reportable scientific
  `ZERO_XOR_TANGENT_AT_INIT`; cosine is `null`, never epsilon-manufactured.
- [ ] Contemporary OFF is evaluated through the same final path before any
  fit and passes native copy `8/8`. Historical OFF is not substituted.
- [ ] The actual branch follows the fixed release table: mandatory P_AUTH;
  mandatory P_DERANGED when AUTH passes; exactly one DERANGED canary step
  after an AUTH canary miss; and at most one prospectively permitted
  V_AUTH/P_UNARY_TOOL diagnostic. At most three fits are attempted.
- [ ] A completed arm has exactly `128` optimizer updates, `512` ordered row
  forwards and `32` presentations per `(tool,mode)`, with immutable snapshots
  after updates `32/64/128`. Update 1 is the canary, not an extra update.
- [ ] Pre-forward CPU/CUDA RNG hashes match across causally compared arms for
  every shared row forward. Diagnostics and snapshot saves do not alter RNG,
  tensors, buffers, mode, `.grad`, optimizer state or the ongoing stream.

## D. First-update numerical canary

- [ ] Dropout-off repeated forwards are bit-identical and state-neutral.
  Canary gradients and before/after margins use the registered FP64
  hidden-state/output-head recomputation surface `d_canary64`; training uses
  the separate `z_train32` surface.
- [ ] The actual train-mode first quartet uses dropout `.05`, four separate
  prefix forwards in frozen order, one averaged loss, one backward and one
  AdamW step. The full FP32 delta is `theta_after-theta_before` and is sealed.
- [ ] For every one of the four signed prompts, FP64 multiplication and
  reduction give `dot_i = <s_i grad(d_i),delta>` strictly above
  `4 * gamma_(n-1) * abs_sum_i`. The receipt stores dot, absolute-product sum,
  bound and ratio.
- [ ] Every signed observed margin improvement is strictly above its analogous
  FP64 two-dot error bound. Equality fails. The signed `4x4` Gram matrix is
  stored and passes its registered approximate-PSD implementation check; it
  is not used as a substitute for the eight directional predicates.
- [ ] A canary miss is a valid result for this exact sampled
  seed/quartet/dropout path, not a universal LoRA claim. It stops that arm at
  update 1 under the registered lifecycle and is never retried.

## E. Complete denominators and readout integrity

- [ ] Every snapshot is loaded into a fresh base and bound to its adapter
  directory/tensor digest. Updates 32 and 64 contain all `128 exact + 64 held`
  prefix margins. Update 128 also contains all exact/held strict generations,
  all `96` locality prefix+generation records and all `8` copy records.
- [ ] Each prefix record contains raw logits, canonical margin/sign, `q`,
  full-vocabulary legal branch-token mass `M`, hashes and load receipt. Each
  generation record preserves raw IDs/text, EOS/truncation state, closed
  action enum and attempts=`1`. No request is retried or dropped.
- [ ] With two completed P maps and no optional completed fit, the expected
  accounting is `256` training updates, `1024` training row forwards, `128`
  no-update audit forwards, `1632` OFF/snapshot prefix readouts and `888`
  strict-generation/copy requests. Other valid lifecycle branches must
  reconcile exactly from the same per-stage counts.

Any incomplete, duplicated, extra, retried, nonfinite, wrong-load or
wrong-adapter denominator is a nonreportable integrity abort, not a failed
science gate.

## F. Efficacy gates — each P map independently, update 128 only

**Exact forms (`n=128`):**

- [ ] strict correct `>=116/128`;
- [ ] each target-action recall `>=56/64`;
- [ ] strict valid `>=122/128`, with `0` multiple-action outputs;
- [ ] at least `14/16` tool-mode keys have `>=7/8` correct; and
- [ ] median signed ON-minus-OFF margin gain is `>0` separately in both
  64-row target classes.

**Held forms (`n=64`):**

- [ ] strict correct `>=52/64`;
- [ ] each target-action recall `>=24/32`;
- [ ] strict valid `>=61/64`, with `0` multiple-action outputs; and
- [ ] at least `12/16` tool-mode keys have positive median signed margin.

Even-count medians are the arithmetic mean of the two middle sorted values.
No checkpoint other than update 128 qualifies the writer.

## G. Complementarity gates — noncompensatory

- [ ] On the `128` identical exact prompts, at least `112/128` are
  strict-correct under both P_AUTH and P_DERANGED and emit their registered
  opposite actions.
- [ ] On the `64` identical held prompts, at least `48/64` are strict-correct
  under both maps and emit their registered opposite actions.
- [ ] P_AUTH and P_DERANGED each pass every individual exact, held, copy and
  locality gate. One map, one target class, one key, or an optional arm cannot
  compensate for the other.

## H. Locality and bounded no-harm gates — each P state versus OFF

The closed generation identity is `MEM2REG | GVN | OTHER_SINGLE(exact text) |
INVALID | MULTIPLE`. `A=1` only for exactly one of MEM2REG/GVN. For **each**
locality family separately:

- [ ] mean itemwise `abs(q_ON-q_OFF) <= .05`;
- [ ] mean itemwise `abs(M_ON-M_OFF) <= .05`;
- [ ] no item has either probability delta `>.10`;
- [ ] legal-action status changes `abs(A_ON-A_OFF)` are exactly `0/8`
  missing-mode, `0/8` unsupported-mode, `0/16` neighbour-ID, and at most
  `3/64` wrong-root;
- [ ] strict generated-identity changes are exactly `0/8`, `0/8`, `0/16`,
  and at most `3/64`, respectively; and
- [ ] mutually opposite legal P_AUTH/P_DERANGED outputs on wrong-root prompts
  are at most `3/64`.

- [ ] OFF, P_AUTH and P_DERANGED each retain native copy `8/8`; exact/held
  multiple-action counts are zero; valid-to-invalid and invalid-to-valid
  locality transitions are separately reported.

These are only registered branch-choice, legal-mass, generation and interface
locality/no-harm gates. They do not prove global behavioral or distributional
no-harm.

## I. Terminal classification and claim gate

Apply integrity-before-science precedence, then the first applicable label:

1. `NONREPORTABLE_PRECHECK_ABORT` or `NONREPORTABLE_RUNTIME_ABORT`;
2. `ZERO_XOR_TANGENT_AT_INIT` when its registered finite-norm branch occurs;
3. `EARLY_XOR_QUARTET_STOP_AUTH` or
   `EARLY_XOR_QUARTET_STOP_DERANGED`;
4. `LOCAL_XOR_DIRECTIONS_NOT_PRESERVED`, with `MAP_ASYMMETRY` when exactly
   one P map passes exact acquisition or `BOTH_XOR_EXACT_NULL` when neither
   does;
5. `STORED_NOT_EXTRACTABLE` when exact acquisition/complementarity passes but
   either held conjunction fails;
6. `CONDITIONAL_BINDING_WITH_SPILL_OR_INTERFACE_FAILURE` when exact and held
   pass but copy or any locality/interface gate fails; or
7. `SUPERVISED_ONE_ROOT_XOR_BINDING_PASS` only when the complete two-map
   exact, held, complementarity, copy and locality conjunction passes.

Optional V/unary arms receive only their registered suffix. A V or unary pass
cannot alter the primary P label; an early V miss is
`EARLY_V_AUTH_QUARTET_STOP` plus `OBJECTIVE_CONTRAST_AMBIGUOUS`.

The strongest possible result from this DEV root is narrowly bounded:

> One deterministic rank-8 recipe installed and extracted complementary
> finite `(opaque tool, mode)->action` bindings on one researcher-supplied
> synthetic root under the registered locality surface.

It is **not** a fresh-root replication and does not establish child-authored
experience, learning, DREAM/SLEEP, parenting, connected/compressed memory,
traversal, lifetime improvement, baseline superiority, or a general writer.
A full DEV pass freezes the recipe and permits two unchanged failure-inclusive
confirmations plus the separately excluded endogenous one-SLEEP relay; mixed
confirmation subtypes may not be majority-voted into robustness.

