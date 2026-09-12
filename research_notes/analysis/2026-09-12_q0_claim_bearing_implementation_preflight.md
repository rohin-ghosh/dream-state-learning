# Q0 claim-bearing implementation preflight

**Date:** 2026-09-12  
**Verdict:** **IMPLEMENTABLE WITH ONE NEW EXECUTOR AND ONE NEW FOCUSED TEST
FILE; do not edit or reuse the outputs of the archived executors.**  
**Scope:** fresh read-only preflight of the adjudicated Q0 contract against the
current committed writer, corpus, trainer, readout, tests, coordination record,
and Astra artifacts. No builder source was edited and no model or GPU was run.

## Bottom line for Astra

Create, at minimum:

```text
gpu/astra_pairwise_q0.py
tests/test_astra_pairwise_q0.py
```

The new module may import frozen helpers, but the archived modules must remain
byte-identical. Their terminal replays pin their source hashes. In particular,
do **not** edit:

```text
gpu/astra_semantic_objective_probe.py
organism_v6/semantic_writer_diagnostic.py
organism_v6/multikey_writer_gateway_simple.py
```

The new executor should consume only root 1's sealed Q0 prompts/material and
the clean base identity from the archived terminal Q0 root. It must create all
new adapters from the clean base. It must not consume an old fitted adapter.

This is a substantial objective/readout change, but not a new benchmark. The
frozen surface remains: eight opaque tools, two modes, eight exact and four
held templates, AUTH XOR, its exact complement, four locality families, eight
native-copy items, root 1, seed 1, rank 8, and LR `3e-5`.

## Evidence cut inspected

The implementation target is
`research_notes/analysis/2026-09-12_pairwise_binding_falsifier_adjudication.md`
(current file SHA-256
`254655bbeef0723811f44b2bbd166e783fc67b928c1a18e90470487ba73387e4`).
The source cut inspected was repository commit
`65211cee86178e9e231c9b2da620589f5b981ce5` with these relevant source hashes:

| artifact | SHA-256 |
|---|---|
| `gpu/astra_semantic_objective_probe.py` | `98a90f33dcd5582b9e32fe21d08dd29283c82b955ff350c8c994d2903b2f0d41` |
| `tests/test_semantic_objective_probe.py` | `0a327ab022b434d89cdcd881ab795f4ee28ff896679d45da16b03be1ddb95de0` |
| `organism_v6/semantic_writer_diagnostic.py` | `d6ea45ac6bfb5cabe6cbd1224f4cf101e96cbd0e07c029e934c2aa3e03e1ddb0` |
| `tests/test_semantic_writer_diagnostic.py` | `daf0f95a30f5a6a6dedb020c97283ac39addb9648b588a85dfc5bee1ee38622b` |
| `organism_v6/multikey_writer_gateway_simple.py` | `b9fd33c7c11b2f57395f08d609bb1df004d9663eeefd143060bb1a24a34f10c8` |
| `organism_v6/train_adapter_v3.py` | `7bbf165fcb4b8ae3a1180328bcd19f57382c30516daddc95fd61e8a2c749fad7` |
| `organism_v6/conditional_behavior_corpus.py` | `a0ea3717508f05b751935fa3070792d33fe4a21dd46d8a2a93dadb6c2a8b606a` |
| `tests/test_conditional_behavior_corpus.py` | `33dff503eeccc9aa1e0c95db7df44bf7356eb8d6d47ee90e6ef27e83112cdd46` |

The latest relevant Astra commits are `5f6e1f1d` (Level-1 corpus) and
`785cd462` (native Level-1 material audit plus replay launch material). Those
Level-1 artifacts are downstream preparation, not a Q0 implementation. A
fresh audit found a perfect public-ID shortcut in their REVISE surface, and
the committed package has no complete runner/reducer. Nothing from it should
enter this Q0 run.

The archived SEQ-089 executor is also not a starting implementation in place:
it fixes full-response/first-choice arms, one-row `output.loss` steps, only
exact generation, no held/locality gates, and no terminal classifier. Its
useful value is as a lifecycle skeleton and as the sealed material verifier.

## Reuse versus replace

### Reuse unchanged

- `astra_semantic_objective_probe.verify_original`: exact archived Q0
  manifest/seal/material verification for root 1, subject to a fresh runtime
  deadline/GPU binding in the new executor.
- `semantic_writer_diagnostic.build_material`, `render`, and its root-1
  train/held/locality/copy topology. Use them through the sealed projection;
  do not regenerate a new task.
- `multikey_writer_gateway_simple` canonical JSON, digest, file/tree hash,
  checked-path, snapshot/environment pinning, deterministic Torch setup,
  trainable inventory, GPU identity, and no-retry worker primitives.
- `semantic_writer_diagnostic.fit_model` only as a construction helper for
  the exact rank-8/all-seven-projection/AdamW recipe. Immediately re-audit
  every returned field; do not reuse its row-wise trainer.
- `semantic_writer_diagnostic.load_eval_model`, subject to accepting a fixed
  snapshot directory rather than only its old `fit_<state>/adapter` layout.
- `writer_interface_calibration._generate` plus
  `semantic_carrier_diagnostic.strict_output` for unprefilled greedy output.
- The original root-1 orientation vector
  `[0,1,1,0,1,0,0,1]`, action strings `-mem2reg/-gvn`, exact/held prompts,
  and locality/copy prompts.
- The owned process-group cleanup pattern, fresh-process model loads, sealed
  receipts, deadline/lease checks, and no-retry behavior from the objective
  probe and semantic writer.

### Do not reuse for a scientific Q0 result

- `train_adapter_v3`: it performs ordinary full-response CE, may pack,
  truncate, checkpoint gradients, shuffle groups, skip nonfinite batches, and
  uses a different optimizer surface. Q0 requires an explicit prefix-only
  P/V objective and exact quartet updates.
- `semantic_writer_diagnostic.train_rows`, `carrier.score`, `score_sums`,
  `reduce_records`, `cell_gates`, or `classify`: the trainer is one-row
  full-continuation CE; the old candidate scorer has the known unequal-shape
  BF16 defect; the reducer uses obsolete thresholds and binary-normalized TV.
- Any SEQ-089 labels/masks after the decision position. A live-label mask on a
  complete target-shaped tensor is still target-shaped input.
- The Level-1 corpus or its `1e-4`/full-response recipe. Q0 must precede it.

## Exact new material projection

For every root-1 exact, held, missing-mode, unsupported-mode, neighbour-ID,
and wrong-root prompt:

1. Render the frozen user prompt with the native Qwen chat template.
2. Encode both complete candidates independently.
3. Prove identical IDs through the assistant tokens for `ACT: -` and one
   common branch position thereafter.
4. Rediscover two distinct branch IDs. Require the native values to equal the
   archived checks `10536` and `21404`, but never use those literals to build
   the input.
5. Store only `decision_input_ids = candidate_ids[:branch_position]`. There
   are no labels. Record the rendered-user boundary, assistant boundary,
   branch position, both candidate hashes, common-input hash, and expected
   target bit separately.
6. Flip AUTH to DERANGED (or the target bit directly) and prove every input ID
   and common-input hash remains byte-identical.

Preparation must prove:

- exactly `128` unique exact common prefixes and `64` held items;
- exact target counts `64/64` under AUTH and independently under DERANGED;
- `8 tools x 2 modes x 8 exact templates` and all `64` held coordinates;
- `32` complete exact quartets, with every exact row appearing once;
- every quartet has two opposite-orientation tools, both modes, one template,
  and target counts `2/2` under each XOR map;
- exact AUTH/DERANGED target complement at all 128+64 primary items;
- all `8+8+16+64=96` locality items and `8` native-copy items;
- train templates `0..7` and held templates `8..11` remain disjoint;
- target/map values never enter the schedule hash or common-input bytes; and
- there is no padding, truncation, fallback branch boundary, alternate pair,
  or selected retry.

Build the schedule literally from the adjudicated digest domains:

```text
['Q0-XOR-PAIR-v1', root1, tool]
['Q0-XOR-SCHEDULE-v1', four ordered source-row hashes]
```

Pair equal digest ranks across the two orientation classes, enumerate template
`0..7`, order each quartet `(orientation0-m0, orientation0-m1,
orientation1-m0, orientation1-m1)`, then digest-sort the 32 quartets. Serialize
that order before model load. Repeat the identical 32-quartet order four
times; do not reshuffle between sweeps.

## Objective-audit worker

The first GPU worker is a disposable, zero-update LoRA initialization, not a
fit. It must match the later fit initialization inventory and digest.

For each row, forward only the natural common prefix. Let the emitted BF16
last-position vector be cast to FP32 as `z`, then compute explicitly:

```text
d   = z[mem2reg] - z[gvn]
L_P = softplus(-s*d)
L_V = logsumexp(z) - z[target]
M   = softmax(z)[mem2reg] + softmax(z)[gvn]
```

Do not call native `output.loss`. For each quartet, retain its four forward
graphs, average the four `L_P` values and the four `L_V` values separately,
and use `torch.autograd.grad` to obtain ordered gradients without populating
`.grad` or stepping. Compute `R` and cosine by streaming FP64 dot products
over the ordered trainables; do not concatenate a multi-million-element
vector. Record per-quartet loss/norm/R/cosine values, ordered trainable
inventory and gradient digests. Record all 128 `M` and `-log(M)` values.

Seal exactly one of:

```text
OBJECTIVE_CONTRAST_DEGENERATE_AT_INIT
OBJECTIVE_CONTRAST_NONDEGENERATE_AT_INIT
```

using the exact universal conjunction in the adjudication. Zero `g_P`, a
nonfinite value/cosine, input drift, parameter/RNG/buffer mutation, or failed
worker cleanup is `NONREPORTABLE_PRECHECK_ABORT`, not “degenerate.”

## Fit worker and gradient canary

Every attempted arm starts a fresh seed-1 clean-base rank-8 LoRA and empty
AdamW state. Record and compare across all causally compared arms:

- ordered trainable name, shape, dtype, `requires_grad`, and tensor digest;
- LoRA A/B initialization convention and full initial tensor digest;
- ordered optimizer parameter names, exact param-group/default fields, and
  zero initial state entries;
- CPU RNG, every CUDA RNG, model parameter, named-buffer, mode, and step-0
  logits digests; and
- the pre-forward RNG hash for every actual row forward (512 for every
  completed arm; the first four only for an early canary stop).

For the first quartet only:

1. In a state-neutral `eval()` block, forward each row separately. Repeated
   outputs must be bit-identical.
2. Define the **canary margin** by recomputing the final hidden-state dot the
   two fixed output-head rows in FP32. Use this same FP32-recomputed `d32` for
   `grad(d32)`, before/after observed margins, and projection signs. Continue
   to use BF16-emitted logits cast to FP32 for the registered training loss.
3. Obtain four ordered per-prompt `grad(d32)` vectors with `autograd.grad` and
   record their 4x4 signed Gram matrix using FP64 accumulation.
4. Prove diagnostics leave RNG, all named buffers and parameters, mode, `.grad`
   fields, and empty optimizer state unchanged; restore `train()`.
5. Run the four dropout-active prefix forwards in registered order; average
   their explicit losses; do one backward and exactly one AdamW step.
6. Retain the complete FP32 parameter delta as a sealed safetensors artifact
   (plus digest/norm). Require, for all four prompts,
   `s*<grad(d32),delta> > 0` in FP64.
7. Re-enter the neutral diagnostic and require every recomputed signed `d32`
   to be strictly larger than before. Record the ordinary BF16-cast margins
   as a diagnostic, never as a substitute.

The canary update is update 1 of 128. It is not an extra update. A scientific
canary miss writes a sealed reportable early-stop receipt after update 1; an
integrity mismatch is a nonreportable abort.

After a canary pass, continue in the same process, optimizer, and RNG stream.
Each update forwards four natural-length rows separately, averages the four
losses, then performs one backward and one step. Save immutable LoRA-only
snapshots at updates `32`, `64`, and `128`. Verify saving does not mutate
model/optimizer/RNG state. A completed fit is exactly `128` updates, `512`
row forwards, and `32` presentations per tool-mode key.

## Evaluation and raw records

Use a fresh base load for every snapshot. At updates 32 and 64 run only the
complete `128 exact + 64 held` common-prefix, dropout-off margin panel. At
update 128 additionally run:

- strict unprefilled greedy generation on all 128 exact and 64 held prompts;
- common-prefix q/M and strict generation on all 96 locality prompts; and
- unprefilled native copy on all 8 copy prompts.

Run one contemporary OFF final panel with precisely the same inputs and
operations before any fit. Fail before fitting if OFF cannot copy `8/8`.

Each prefix record must contain `z0`, `z1`, canonical `d=z0-z1`, target sign,
signed margin, stable `q=softmax([z0,z1])[mem2reg]`, full-vocabulary legal
branch-token mass `M`, common-input/request/source hashes, snapshot/adapter
hash, and load receipt. q and M come from one natural-prefix forward, never
from two future-shaped candidate forwards. Each generation record preserves
all generated IDs, text, EOS/truncation/multiple-ACT state, strict action, and
request/load/adapter hashes. There are no retries or dropped denominators.

## Acceptance reducer

Implement a pure reducer that rebuilds the entire material/schedule/request
projection and refuses missing, duplicate, extra, retried, nonfinite, or
wrong-state records before computing science labels.

For each P map at update 128, require all adjudicated integer gates exactly:

- exact: `>=116/128`, each action `>=56/64`, validity `>=122/128`, zero
  multiple actions, `>=14/16` keys at `>=7/8`, and positive median signed
  ON-minus-OFF margin gain in each 64-row target class;
- exact complement: `>=112/128` identical prompts strict-correct under both
  adapters and emitting the two registered opposite actions;
- held: `>=52/64`, each action `>=24/32`, validity `>=61/64`, zero multiple
  actions, and `>=12/16` keys with positive median signed margin;
- held complement: `>=48/64` prompts strict-correct under both and opposite;
- native copy: OFF and each P state `8/8`; and
- every locality family separately: mean itemwise `|delta q|<=.05`, mean
  itemwise `|delta M|<=.05`, no probability delta `>.10`, mean itemwise
  `|A_ON-A_OFF|<=.05`, and strict action-identity change rate `<=.05`.

For locality, report valid-to-invalid and invalid-to-valid counts. On the 64
wrong-root prompts, also require the P_AUTH/P_DERANGED mutually opposite legal
output fraction `<=.05`.

Evaluate V_AUTH and P_UNARY_TOOL on the same panels, but keep their result
separate from the primary P-map conjunction. Unary's positive diagnostic
requires the exact/held aggregate and class-recall thresholds, primary
validity, copy/locality, and at least `7/8` tools at `>=14/16` exact. It can
never qualify Q0.

The primary terminal classifier must implement the adjudicated precedence:

```text
NONREPORTABLE_PRECHECK_ABORT / NONREPORTABLE_RUNTIME_ABORT
EARLY_XOR_QUARTET_STOP_AUTH / EARLY_XOR_QUARTET_STOP_DERANGED
LOCAL_XOR_DIRECTIONS_NOT_PRESERVED (+ MAP_ASYMMETRY or BOTH_XOR_EXACT_NULL)
STORED_NOT_EXTRACTABLE
CONDITIONAL_BINDING_WITH_SPILL_OR_INTERFACE_FAILURE
SUPERVISED_ONE_ROOT_XOR_BINDING_PASS
```

Attach the registered objective/unary qualifier without changing that primary
label. Store every intermediate checkpoint curve, but never select a
checkpoint or alter the label from it.

## Fixed controller order and release table

The only allowed order is:

1. CPU prepare/seal and native tokenizer audit; no model load.
2. Zero-update objective-audit worker.
3. Contemporary OFF final panel; copy `8/8` before any fit.
4. `P_AUTH`: first quartet is canary; continue uninterrupted through 128 only
   on pass; then evaluate snapshots 32/64/128.
5. If AUTH canary passed, `P_DERANGED` under the identical rule; then evaluate
   its completed snapshots.
6. Select the possible third fit from only the sealed initialization audit,
   canary states, and final exact acquisition:
   - either P canary fails -> `P_UNARY_TOOL` only;
   - both P canaries pass and audit is nondegenerate -> `V_AUTH`, regardless
     of later P exact outcome;
   - both P canaries pass, audit is degenerate, and either P final exact gate
     fails -> `P_UNARY_TOOL`;
   - both P canaries pass, audit is degenerate, and both P final exact gates
     pass -> no third fit.
7. Evaluate the attempted third fit at the same fixed snapshots if it
   completes, reduce once, seal once, and prove the GPU/process group empty.

No pause/resume, restored optimizer, changed seed/rate/rank/quartet, alternate
boundary, checkpoint selection, retry, or replacement fit is allowed. Bind a
`2700`-second/`0.75` A40-hour controller ceiling and the earlier lease cutoff.
Report exact forward/backward/update/generation/generated-token/model-load,
wall-time, cleanup, early-stop, and unattempted-stage counts.

## Required tests before launch

Run these on the Linux execution environment, not the macOS laptop:

1. **Pure material tests:** all counts/topology/balance, map complement,
   schedule golden bytes, each row exactly once per sweep, target-flip input
   invariance, no future assistant branch/suffix/LF/EOS/padding, held-template
   disjointness, and all leakage mutations rejected.
2. **Native tokenizer tests:** exact Qwen chat render and two-candidate common
   boundary on every exact/held/locality row; branch IDs discovered and equal
   to the two archived checks; no truncation; candidate order reversal gives
   the same prefix and decision position.
3. **Real CPU Torch objective tests:** P/V equations, P-softplus equivalence,
   target reversal, finite FP32 loss, P gradients only on the two legal logits,
   V outside-pair mass gradient, R/cosine calculation, and every degeneracy
   threshold immediately above/below equality.
4. **Canary toy tests with real autograd/AdamW:** a true XOR-feature toy
   passes all four projections/margins; global-bias, mode-only, and tool-only
   toys fail; unary passes only the tool test; a canary stop performs one
   update and dispatches no prohibited next arm.
5. **State/RNG tests:** ordered initialization and optimizer receipts; empty
   state; per-forward cross-arm RNG identity; deliberate extra RNG draw,
   parameter/buffer/mode/`.grad` mutation, parameter reorder, or changed
   optimizer field fails.
6. **Checkpoint/lifecycle tests:** exact 32/64/128 snapshots without optimizer
   reset, fresh reload identity, variable release table above, OFF-before-fit,
   2700-second cutoff, early stop, runtime abort, no retry/resume, cleanup, and
   sealed replay.
7. **Reducer tests:** fixed complete raw fixtures for pass and every terminal
   branch; every inclusive integer/probability boundary and adjacent failure;
   class recall, key coverage, complementary flips, q/M/A/I itemwise locality,
   tail bounds, native copy, wrong-root flips, V/unary qualifiers, and
   integrity-over-science precedence.
8. **Regression suite:** the untouched archived objective/writer/gateway tests
   plus the new focused file, on Linux with GNU `/usr/bin/timeout`.

The local macOS command over the three archived suites ran 105 tests but is
not an admissible regression result: 24 errors and 18 failures were dominated
by the repository's intentional symlink-safe path rejection of macOS
`/var -> /private/var`, absence of GNU `/usr/bin/timeout`, and one resolved-vs-
unresolved temp-path expectation. This is an environment mismatch, not a Q0
scientific result. The bound suite must be run in the same Linux environment
as preparation/execution and its receipt must name that environment.

## Contract ambiguities that Astra must resolve exactly as follows

There are two literal contradictions and one missing label in the adjudicated
prose. They are implementation blockers if left implicit, but they do not make
the experiment impossible.

1. **“Input contains no branch token” is impossible literally.** The frozen
   Q0 user instruction symmetrically names both complete legal actions, so the
   branch token IDs already occur in the user portion. Preserve that frozen
   prompt. Interpret the exclusion as: *the appended assistant continuation
   contains only `ACT: -` and contains no branch token or later target token*.
   Record user/assistant span boundaries and test this scoped property. Do not
   silently rewrite the prompt.
2. **Optional controls cannot veto the P qualification.** “Only P_AUTH plus
   P_DERANGED can qualify” conflicts with “every final fitted state ... must
   retain copy 8/8.” Apply copy/locality/interface gates from OFF and the two P
   states to the primary label. Evaluate V/unary identically and use failures
   only in their registered qualifier. Otherwise merely running an optional
   diagnostic could destroy an already valid P result.
3. **V_AUTH has no early-canary terminal label.** Add
   `EARLY_V_AUTH_QUARTET_STOP` as an objective-control suffix only. It does not
   change an already determined primary P label and forces
   `OBJECTIVE_CONTRAST_AMBIGUOUS`. Preserve the attempted update and do not
   retry. The existing AUTH/DERANGED/unary early labels remain primary where
   specified.

One numerical ambiguity should also be eliminated: the registered training
loss is computed from BF16-emitted logits cast to FP32, while the canary asks
for an FP32 hidden-state/output-head recomputation. Name these `z_train32` and
`d_canary32` respectively. Train with the former; use the latter consistently
for canary gradients, projections, and before/after margin gates.

No other gate is mathematically impossible. In particular, zero-B LoRA makes
the initial A gradients zero, but B gradients and `grad(d)` are nonzero; the
FP64 projection test remains meaningful. The 32 quartets exactly cover 128
rows, four sweeps give the required 512 presentations, and the integer gates
are arithmetically attainable.

## No-ambiguity handoff

1. Astra owns the two new files and may add a thin launcher only if it contains
   no scientific logic.
2. Preserve all old source bytes and archived roots.
3. Implement pure material/objective/reducer helpers first; get the new Linux
   CPU suite green.
4. Materialize a fresh native preparation from the sealed root-1 Q0 artifact;
   inspect and bind its source, tokenizer, schedule, panel, and branch-token
   hashes before model load.
5. Log a dated Builder preflight line naming the exact tests and prepared-root
   hashes.
6. Execute only the fixed controller order above on one pinned A40. Treat any
   already-running Level-1 result as exploratory and upstream-invalid; it
   cannot substitute for Q0.
7. After terminal cleanup, replay the sealed reducer from raw records before
   stating a label.
8. A full pass supports only one supervised, one-root XOR conditional writer.
   It releases repaired Level 1; it does not support parenting, DREAM/SLEEP,
   experiential H1, connected knowledge, recurrence, lifetime learning, or
   memory-baseline superiority.

