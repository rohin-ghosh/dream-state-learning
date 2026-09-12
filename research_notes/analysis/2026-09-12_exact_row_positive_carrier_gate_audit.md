# Exact-row positive-carrier gate for a prospective W0 V10R2

Date: 2026-09-12 UTC  
Status: docs-only, prospective audit. No builder source, Astra-owned file, run,
adapter, job, process, GPU, or node was changed.

## Verdict

Use an exact-row condition only as a typed, OFF-clean-base positive-carrier
canary. It should replace neither primary adapter evaluation nor the meaning of
V10R1's full-table `oracle_ok` without an explicit V10R2 amendment.

The smallest fit-eligibility canary has 64 fixed items: one held form for every
one of the 16 `(tool, mode)` keys in each of four root-map cells. On each item,
run both strict free generation and two-candidate full-continuation scoring
under the same chat rendering and explicit response contract. This is 128
typed requests. The canary row exposes the correct binding directly; it tests
whether an exact text carrier can deliver that binding through the declared
native action interface. It does not test multi-row retrieval or a writer.

The already observed 64 calibration items can support one paired development
diagnostic against their archived full-table `chat_explicit_32` outputs. They
cannot make a writer fit eligible. A fit-eligibility gate needs new opaque
identifiers and new held-template literals, frozen before model output, because
the old items and the interface choice are now development-exposed.

## Evidence that fixes the scope

Origin/main at `a778b23f` records:

- W0 attempt 2 gave all 256 full-table OFF oracle generations 32 tokens, no
  EOS, `truncated:true`, and no strict legal action. Its four oracle BAs were
  zero. All 464 OFF generations, including primary and spill, truncated.
- The prospective five-condition calibration selected 64 items without using
  outcomes: one held form per key in each root-map cell.
- Only chat plus the fixed explicit instruction repaired most formatting:
  61/64 valid, 0 truncated, 0 multiple-ACT, but only 45/64 correct. Cell
  correctness was 10, 11, 13, and 11 of 16; all four miss the old `.90`
  full-table oracle threshold.
- Chat alone, explicit instruction alone in raw mode, and a 256-token raw cap
  did not repair the interface. Candidate likelihood was not measured in this
  calibration.
- Astra's currently live `astra_oracle_lookup_20260912_attempt1` is exactly a
  64-call, strict-generation, reused-calibration-row follow-up. It copies one
  authentic key-selected row, preserves chat/explicit/32-token/parser bytes,
  and compares against the archived full-table outputs. Its own frozen
  boundary says development-only, no qualification. It has no candidate-score
  requests and no fresh identifiers or held forms.

Thus the remaining full-table failure mixes at least two requirements:
selecting the applicable row from 16 visible rows and emitting the selected
action. The exact-row canary removes the former requirement from the positive
control. It does not retroactively diagnose every old error as retrieval.

## Exact prompt and visibility

For a preselected held task with public key `(tool, mode)` and correct action
`target`, the complete user-message bytes are:

```text
Reply with exactly one line: ACT: a0 or ACT: a1. Do not include explanations.
Explicit action table:
{tool} {mode} -> ACT: {target}
Task:
For {tool}, the selected mode is {mode}; choose now.
```

There is one final LF after `choose now.`. The instruction, headers, selected
row literal, task literal, and order are inherited from the calibrated
full-table condition; the only deletion is the 15 nonmatching rows. Do not add
"relevant", a rationale, a map name, or another answer hint.

Render this as exactly one user message with the pinned Qwen tokenizer's
`apply_chat_template(tokenize=False, add_generation_prompt=True)`, then
tokenize with `add_special_tokens=False`. This preserves the tokenizer's
default system message and exact assistant-generation boundary. Generation
and candidate scoring for an item must have identical rendered-prefix token
IDs.

The model sees the response contract, the unique canonical row containing the
answer, and the unchanged held task. It does not see root, map name, slot,
stratum, orientation, template ID, seed, audit target, any other table row,
fit material, or an adapter. Row selection is a deterministic exact lookup on
the public `(tool, mode)` key before outputs exist; it must return exactly one
row or abort. The row and every derivative are confined to typed
`carrier_generate` and `carrier_score` requests and a disjoint cache kind.

"Matched" means the chat wrapper and response contract are shared by future
training, primary generation/scoring, and binary spill requests. It does not
mean the answer row is shared: no fit row, primary request, spill request,
adapter request, or unrelated-native request may contain it. Adding the answer
row to training or primary evaluation would destroy the W0 estimand.

## Scoring, denominators, and gate

The frozen material is four cells × 16 keys × one held form = 64 items. Within
each root-map cell there are exactly eight `a0` and eight `a1` targets. W+ and
W- use the same root/key/task and complementary answer rows, giving 32 paired
map-swap coordinates. No cell may borrow successes from another.

For each item:

1. Generate greedily with `do_sample=False`, seed 0, at most 32 new tokens,
   no retry or output repair. Preserve complete decoded bytes, EOS, token IDs,
   and truncation. Score correct only when the unchanged V10 parser accepts the
   complete output as exactly `ACT: a0` or `ACT: a1` after its ASCII outer trim;
   truncation is invalid.
2. Separately teacher-force the exact complete candidates `ACT: a0\n` plus EOS
   and `ACT: a1\n` plus EOS after the identical prefix. Sum all candidate token
   log probabilities. Non-finite or missing scores are nonreportable; a tie is
   wrong. Candidate scoring cannot replace generation.

The prospective canary passes only if all of these predeclared conditions hold:

- strict generated BA is at least `.90` in each 16-item root-map cell, which
  on this balanced denominator means at least 15/16 correct in each cell;
- candidate-choice BA is at least `.90` in each cell, likewise at least 15/16;
- generated validity is at least `.95` over the fixed 64 items (at least
  61/64), with zero truncated outputs and zero line-anchored multiple-ACT
  outputs;
- on the 32 paired coordinates, switching only the supplied W+ versus W-
  exact row redirects the strict generated action on at least 29/32 pairs and,
  separately, redirects the candidate argmax on at least 29/32 pairs; and
- every request, pair, prompt/token, model/tokenizer, OFF-load, resource, and
  post-exit seal/replay check passes exactly.

Report cell confusion counts, validity, truncation, multiple ACT, target-minus-
opposite score margins, paired redirection, and generation/score agreement even
when the conjunctive gate fails. These 64 deterministic prompts are nested
within two engineered roots, not 64 independent learner seeds; the threshold
is an operational canary, not an inferential reliability estimate.

The live Astra follow-up already supplies the immediate 64 exact-row
generations against the archived full-table `chat_explicit_32` baseline. Its
result can diagnose whether removing the other 15 rows improves strict action
selection on this fixed development panel. It is not the 128-request canary
specified here: it lacks candidate scoring and reuses the outcome-inspected
calibration items. A further old-row scoring pass could add a development
likelihood diagnostic but still would not supply freshness or fit eligibility.

## What a pass does and does not establish

A fresh pass shows that, on the frozen panel, the clean base can follow a
directly exposed `(tool, mode) -> action` binding under the selected chat and
strict native-action interface, both in unconstrained generation and in
full-candidate likelihood. The complementary row swap makes a constant task
prior an inadequate account of a passing result.

An old-row exact pass paired with the 45/64 full-table result would show that
removing irrelevant rows and making the applicable binding uniquely visible
improves this fixed development surface. It removes retrieval from the new
positive control. It does **not** isolate retrieval causally from the bundled
changes in prompt length, answer position, attention competition, or salience,
and it does not prove that retrieval caused all 19 old errors.

It does not show full-table lookup, LoRA writing, stored conditional bindings,
native behavior from candidate scoring alone, unseen-key generalization,
retention, reliability across fits, lived learning, child authorship, DREAM,
parenting, H1/H2, recurrence, continual learning, or a whole organism. It does
not promote either V10R1 root or repair the failed attempt-2 seal.

W0 remains nonvacuous only if the exact row is confined to this OFF positive
control. The four adapters must still start from the clean base, receive no
held answer row, and satisfy the unchanged all-key NLL-gain, map-specific
generation, shortcut, interface, spill, and opposite-map gates on no-row
primary prompts. A pass may then support a same-semantics text-carrier ceiling
and assay-validity statement; it contributes zero correct observations to the
adapter result.

## Fatal flaw and next-fit eligibility

The fatal shortcut is to take Astra's live 64-call result, or any other
exact-row condition on the already inspected calibration items, and call that
the unchanged V10R1 oracle gate or use it to release a fit. That would silently
change the positive-control construct after outcomes; the live run also lacks
the candidate half of the proposed carrier gate. Placing the row on the
writer's train/primary surface instead hands the treatment its answer and
makes W0 vacuous. Score-only admission is likewise invalid because it does not
establish the declared generated-action interface.

No writer fit is eligible on the current evidence. The smallest honest rule is:

> Freeze a new V10R2 contract, fresh identifiers and held forms, the exact
> prompt/tokenizer bytes, 64-item panel, 128 typed requests, thresholds, cache
> anti-flow, stage order, and zero-fit terminal path before outputs. Run every
> OFF exact-row generation and score first in fresh clean-base process(es). If
> and only if the complete conjunctive carrier gate and replay pass, the same
> sealed controller may automatically release the four declared new clean-base
> fits; otherwise it seals `ASSAY_INVALID_EXACT_ROW_CARRIER` with zero optimizer
> steps. No human inspection, prompt edit, threshold edit, retry, old adapter,
> or old held row may intervene between canary and dispatch.

Rename the gate in V10R2 (`exact_row_carrier_ok`, not the inherited full-table
`oracle_ok`) and narrow the claim accordingly. Retain full-table behavior as a
separate, non-gating retrieval diagnostic if useful. This removes retrieval as
an assay prerequisite without removing the writer's actual no-row binding
burden.

## Sources inspected

- origin/main `a778b23f`, including the terminal calibration memo/capsule and
  the frozen source/handoff/launch record for Astra's live 64-call lookup
- the frozen V9/V10/V10R1 scopes and W0 implementation/terminal audits
- the current prospective V10R2 smallest-successor audit
- the exact `TEXT_SAME_SEMANTICS` W0 carrier contract
