# V10R2 semantic-action carrier audit

Date: 2026-09-12 UTC
Status: docs-only prospective ruling. No builder, Astra-owned file, request,
model, adapter, process, GPU, node, or remote ref was changed.

## Decision

Retire `ACT: a0` / `ACT: a1` as the W0 V10R2 scientific action surface. Keep
the binary complementary-map task, but express its two choices as real actions
accepted by the organism's existing marker interface:

```text
ACT: -mem2reg
ACT: -gvn
```

This is an interface correction, not evidence-driven prompt tuning. In the
last grounded-copy development check, every one of 32 `a1` targets generated
exactly `ACT: a1`, while every one of 32 `a0` targets generated `ACT: a a`
(31) or `ACT: a` (1), with no truncations. The model demonstrably conditioned
on the visible row, but one artificial label was not a reliable generative
action. The strongest tested direct-copy condition therefore had an empirical
strict ceiling of 32/64. That action alphabet is now a construct-validity
bottleneck, not a useful positive control for a writer that must ultimately
act.

Do not loosen the parser to accept `ACT: a a`, search more instructions, or
let candidate likelihood rehabilitate this alphabet. Those moves would test a
private repair rule or score-only discrimination rather than the declared
generated-action contract. Preserve the a0/a1 runs as development diagnostics;
they are nonpromotable.

The proposed strings are already examples of the actual CompilerGym action
language. `loop.py` / `batch_loop.py` hand the open text after `ACT:` to the
gym, and `CompilerGym.evaluate` accepts comma-separated LLVM pass names,
explicitly including `-mem2reg` and `-gvn`. By contrast, a0/a1 and
`native_0` ... `native_7` exist only inside the W0 assay. This makes the new
pair marker-native and backend-executable while retaining the smallest binary
redirection problem. The fits remain disposable mechanism assays and must not
become child, parent, or final-gym artifacts.

Do not switch to JSON or structured tool calls in V10R2. The current organism
has an `ACT:` text boundary and consumes an open action string; it does not
consume a tool-call object. Adding a schema, constrained decoder, and tool-call
parser would introduce a second motor system. A success would then establish
serialization through that new system, not carriage through Dream--LoRA--
Think's action path. Structured calls are appropriate only if the whole
organism interface is migrated and the same schema is used for waking,
writing, scoring, replay, and final evaluation.

## Frozen semantic exact-row carrier

Use fresh opaque roots, tool IDs, and held-template literals that were never in
the a0/a1 diagnostics. Freeze them, the pair above, and all request bytes
before any output. For each selected held `(tool, mode)` task, the one user
message is exactly:

```text
Choose exactly one executable compiler action. Reply with exactly one line: ACT: -mem2reg or ACT: -gvn. Write no other text.
Binding:
{tool} {mode} -> ACT: {target}
Task:
For {tool}, the selected mode is {mode}; choose now.
```

There is one final LF. Render it through the pinned Qwen chat template with
`add_generation_prompt=True`, then tokenize with `add_special_tokens=False`.
Generation and scoring for an item must have byte-identical user content and
identical rendered-prefix token IDs. The model sees one matching binding row,
the task, and the response contract. It does not see root, map name, slot,
orientation, target index, another row, a writer, or an adapter.

The common response contract and chat wrapper, but **not** `Binding:` or its
answer row, become the prefix for writer train examples, no-row primary
generation/scoring, and binary locality prompts. Training necessarily has its
supervised target continuation; it must not contain a declarative
`tool mode -> target` row or any held task. Primary and locality requests
contain neither an answer row nor a target hint. Give carrier requests their
own typed kind and cache namespace; forbid their prompt or token IDs from fit,
primary, and locality manifests. This is what removes retrieval from the OFF
canary without handing the writer the test answer.

Before model requests, fail closed unless both candidate strings:

- are distinct entries in the frozen backend action registry and are accepted
  as single actions by a fixed public smoke program;
- round-trip exactly through the pinned tokenizer and strict parser;
- have explicit response-token masks through their final LF and EOS; and
- fit the generation cap with at least eight tokens of headroom.

The smoke result is an interface receipt only. Its score is not shown to the
model, used to select the pair, or treated as a task outcome.

## Requests and pass threshold

The positive carrier is unchanged in size: two roots x two complementary maps
x 16 keys x one fresh held form = 64 items. Each root-map cell has exactly
eight targets of each action. W+ and W- reuse the same root/key/task and differ
only in the supplied target row, producing 32 map-swap pairs.

For every item make two OFF-clean-base requests (128 total):

1. Greedy generation, no retry or repair, `max_new_tokens=32`. Valid means the
   complete nontruncated response is exactly one of the two declared `ACT:`
   lines under the predeclared ASCII outer-trim rule, with no other text.
2. Full-continuation teacher-forced scoring of `ACT: -mem2reg\n` plus EOS and
   `ACT: -gvn\n` plus EOS. Sum every response-token log probability. A
   nonfinite/missing score or tie is wrong.

Candidate scoring is scientifically needed here because the W0 optimization
and binding gates are defined on full candidate NLL and margins. It separates
"the weights prefer the right complete action" from "the model can emit the
action." It is a diagnostic half of the gate, never a substitute for strict
generation.

Release fits only if the complete carrier satisfies all of:

- generated balanced accuracy at least `.90` in **each** balanced 16-item
  root-map cell (therefore at least 15/16 correct in every cell);
- candidate-choice balanced accuracy at least `.90` in each cell (also at
  least 15/16);
- aggregate generated validity at least `.95` (at least 61/64), with zero
  truncations and zero multiple-`ACT` outputs;
- changing only the W+ versus W- row redirects strict generation on at least
  29/32 paired coordinates and redirects candidate argmax on at least 29/32,
  evaluated separately; and
- all model/tokenizer/OFF identity, request completeness, token-mask, resource,
  seal, and exact-replay checks pass.

Report both candidate token counts, all four confusion matrices, score margins,
generation--score agreement, invalid bytes, and paired redirection even on a
failed gate. Do not length-normalize the candidate likelihoods: the complete
continuations are the actions the generator must choose. Balanced targets and
complementary row swaps make a global preference for either semantic action
insufficient to pass.

## Writer surface and locality amendment

If the carrier passes, substitute the semantic pair everywhere the prospective
V10R2 W0 contract currently says a0/a1. Keep the two roots, complementary maps,
orientation and nuisance balancing, eight train plus four held forms per key,
four independent clean-base rank-8 fits, fixed dose/recipe, strict generation,
full-candidate NLL, all-key margins, shortcut checks, and existing primary
thresholds. Do not run the post-V10R2 writer-recipe factorial until this
semantic-surface W0 is terminal; if it later runs, it inherits this pair.

For clarity, “existing primary thresholds” means, in each 64-item root-map
cell: every key's median target NLL gain at least `.50`, W+/W- mean-gain
asymmetry at most `.25`, generated BA at least `.80`, each 32-item stratum
accuracy at least `.75`, at least 12/16 key margins at least `.50` and at least
6/8 within each stratum, OFF-gain at least `.20`, own-minus-opposite-map BA at
least `.50`, aggregate validity at least `.95`, stratum validity at least
`.875`, and zero multiple-`ACT` outputs. These remain conjunctive across all
four root-map fits; no cell pooling or fallback promotion is allowed.

Make locality correspond to the shared semantic action vocabulary:

- per root: missing-mode `n=8`, unsupported-m2 `n=8`, and one-character-neighbor
  `n=16`, under the same chat and two-action response contract;
- per fitted adapter: the other root's complete no-row held panel (`n=64`) as
  a wrong-root family, never as an owner-primary observation; and
- per root: eight fixed copy prompts, one apiece for `-sroa`, `-simplifycfg`,
  `-instcombine`, `-licm`, `-loop-unroll`, `-adce`, `-bdce`, and
  `-argpromotion`. Each prompt is exactly `Copy exactly one executable action
  line and no other text:\nACT: {action}\n` inside the same chat wrapper. The
  build aborts if any is absent from the frozen backend registry. OFF and every
  fitted adapter must generate the requested exact action on 8/8. This replaces
  `ACT: native_i`, which was not native.

For each fitted adapter and each binary family, compare against that prompt's
clean-base OFF record. Let `q` be the two-candidate softmax distribution from
complete-candidate scores. Require mean binary TV
`mean(0.5 * sum_j |q_ON[j]-q_OFF[j]|) <= .05` separately for missing,
unsupported, neighbor, and wrong-root panels. Also require the **absolute**
difference in strict two-action emission rate, `|rate_ON-rate_OFF| <= .05`,
per family. The absolute value closes the current signed-rate loophole in which
a large loss of legal emissions can pass. Report per-item TV and maxima; do not
pool families, roots, or adapter maps to rescue a failure. Retain the existing
opposite-map owner check as the redirection rather than locality control.

## Meaning of W0 after the change

A carrier pass proves only that the clean base can copy a directly visible
binary binding into two real, executable `ACT:` strings, both as free text and
as candidate likelihood, on the frozen panel. It removes 16-row table search
from the positive control. It does not prove full-table retrieval, and because
row count, prompt length, salience, and answer position also change, it does
not identify retrieval as the cause of earlier full-table errors.

A subsequent W0 pass would establish that four fresh rank-8 adapters can carry
complementary, seen-key conditional selection between two familiar semantic
actions under held no-row renderings, while preserving unrelated semantic
actions and bounded missing/neighbor/wrong-root behavior. That is materially
closer to Dream--LoRA--Think than artificial byte labels, but still does not
establish open-ended action-sequence learning, useful compiler policy,
unseen-key generalization, lived-outcome learning, retention across sleeps,
DREAM, parenting, or increased intelligence. No carrier observation enters
the writer numerator or denominator.

The old W0 interpretation must therefore change from “native a0/a1 action
carriage” to “binary semantic action selection through the organism's native
marker path.” Old a0/a1 outcomes are not comparable successes or failures of
that revised construct. Full-table behavior may remain a labeled
`TEXT_TABLE_SEARCH` development panel, never a fit gate.

## Fit-eligibility rule

No writer fit is presently eligible. The next eligible controller must freeze
the semantic V10R2 amendment, fresh material, exact prompt/token bytes, 64-item
carrier, 128 OFF requests, semantic interface panel, locality denominators,
thresholds, anti-flow checks, and zero-fit terminal path before inference.
It then runs and seals **all** OFF carrier generation/scoring and the OFF
8/8-per-root semantic interface panel before any optimizer step. Only a fully
conjunctive `SEMANTIC_EXACT_ROW_CARRIER_OK` may automatically release the four
declared fits. Failure seals `ASSAY_INVALID_SEMANTIC_ACTION_SURFACE` with zero
steps; no inspection-driven synonym, prompt, pair, cap, parser, or threshold
change is allowed in that scope.

Astra's 64-call reused-calibration-row diagnostics, including the final
grounded-copy variant, are development-only. They lack fresh material and
candidate scoring. They diagnose table selection and, decisively, the a0/a1
surface asymmetry; they are not the fresh fit-eligibility canary above.

## Evidence inspected

- current `origin/main` at `bd81f917`, including `76c6c042`, which records the
  final 32/64 grounded-copy outcome;
- the frozen V9/V10/V10R1 scopes, the exact-row carrier audit, the post-V10R2
  writer-factorial audit, and Astra's frozen lookup/grounded-copy memos;
- `organism_v6/multikey_writer_gateway_simple.py`, including artificial
  candidates, prompt construction, parser, scoring, spill panels, and gates;
- `organism_v6/loop.py`, `batch_loop.py`, `gym_backend.py`, `cgym_eval.py`,
  `bootstrap.txt`, and the reasoning-gym adapter, establishing that the real
  organism boundary is open text after `ACT:` rather than a0/a1 or a structured
  tool call.
