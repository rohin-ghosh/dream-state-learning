# Level-1 teaching-corpus x plasticity: minimal red-team protocol

**Date:** 2026-09-12  
**Role:** fresh adversarial experimental design  
**Scope:** proposal only. Nothing here launches a run, changes the organism, or
changes a scientific claim.

## Verdict on the 17:25 builder candidate

Keep its good boundaries: an open-loop, sourced 80-row corpus; fresh rank-8
LoRAs on the frozen Qwen2.5-7B-Instruct base; no parent, child-authored text,
compiler, or sleep; ordinary parent-free readout; and a sealed development /
confirmation split.

It is not decisive as written:

1. The task-only equal-token arm changes pedagogy, causal order, and target
   structure together. Even perfect native-token equality would not isolate
   corpus *content*. Replace it in the primary experiment with a coherent
   equal-dose complementary wrong-binding arm. The task-only arm may remain a
   separately labelled exploratory arm, but is not needed for the smallest
   causal test.
2. Sixty-four addition demonstrations can teach a global `PREDICT:` ritual
   while frozen-Qwen arithmetic supplies every sum. Exact sums exclude a
   constant number, but do not show that the LoRA learned when different
   actions apply. The arithmetic material needs matched inputs requiring
   opposite actions.
3. Sixteen device/colour facts without a wrong binding can show colour-token
   priming, not device-conditioned memory.
4. `seed=0`, four epochs, `lr=3e-4` is one aggressive recipe, not a plasticity
   result or replication. Changing epochs after seeing it would confound
   plasticity with dose. Cross corpus content with two learning rates while
   keeping every exposure fixed, and precommit seeds `0,1,2`.
5. Development readout may decide only whether a frozen, predeclared cell is
   expanded. It may not change corpus bytes, panels, thresholds, epochs, or
   confirmation cases.

## Non-negotiable release condition

This experiment is ineligible unless the two-input/opposite-action writer
canary has a terminal **pass** on the exact two action strings, native chat
prefix, tokenizer, scorer, loss path, LoRA placement, and optimizer family used
here. A pass must include opposite signed movement from one common,
target-independent prefix, valid jointly normalized two-action scores, clean
reload, and bound initial tensors / RNG / optimizer receipts. A generation-only
pass, a pseudo-probability score path, or a pass on different action bytes does
not release this test. No corpus or panel outcome may be inspected before that
receipt.

## Frozen experiment

### Material and arms

Use the proposed 80 rows, but make the 64 arithmetic rows conditional:

- Choose 32 operand pairs. Render every pair twice, once under each of two
  single-token nonce mode keys. Under the true map, key `K0` means one
  canary-qualified legal action (addition) and `K1` the opposite action
  (subtraction). The target is exactly one numerical `PREDICT:` followed by
  exactly one legal `ACT:`; the prediction must precede the action. The two
  rows in a pair therefore demand opposite actions and different correct
  predictions from otherwise matched inputs.
- Distribute the 64 rows across definition-backed, varied worked, corrective,
  and bare-practice renderings. All end in the same native response contract;
  prose or a reflection slogan is never a scored target by itself.
- Retain 16 invented device/colour observations, four colours exactly four
  times each. These are a separate factual-content bank.

There are only two trained content arms:

- **T (true teaching):** `K0 -> add`, `K1 -> subtract`, and the true 16
  device/colour bindings.
- **W (wrong binding):** swap the two nonce-mode meanings everywhere in the
  lessons, worked examples, corrections, and targets; derange colours within
  four fixed device quartets. Each quartet still contains each colour once.
  W is scored both against the true map and its own presealed map.

For every operand pair, T and W contain the same keys, operands, row skeletons,
and multiset of two complete responses; only the key-response binding changes.
Any keyed definition or correction changes consistently with that binding.
For every device quartet they contain the same prompts and colour-target
multiset. Batch the two arithmetic rows together (two pairs per batch) and each
device quartet together. Before any model call, the Qwen tokenizer must prove,
T versus W: identical row count; identical per-batch input and target length
multisets; identical complete target-token multiset including EOS; identical
unmasked target positions; no truncation; and no loss-bearing padding. “Same
examples”, word count, or padded tensor size is not token-dose parity.

**OFF** is the adapter-free frozen base under the same readout. Repeated OFF
reloads are technical controls, not independent learners.

### Plasticity and experimental units

Vary one plasticity knob only:

- `P_hi`: learning rate `3e-4` (the builder's aggressive candidate, not called
  safe until the safety screen passes);
- `P_lo`: learning rate `1e-4`.

Fix rank `8`, alpha / dropout / target modules, optimizer and objective to the
canary-qualified stack; batch size `4`; four epochs; fixed example order; no
packing, truncation, warm start, merge, best checkpoint, retry, or seed search.
Each adapter sees `80 x 4 = 320` row exposures and makes exactly
`(80 / 4) x 4 = 80` optimizer steps.

The learner is the experimental unit. Seeds are exactly `0,1,2`, paired across
T/W and both learning rates. The full design is:

`2 contents x 2 learning rates x 3 seeds = 12` fresh adapters,
`12 x 80 = 960` optimizer steps, and `12 x 320 = 3,840` row exposures.

The causal contrast is a matched seed block, not an arithmetic item, template,
generation, checkpoint, or repeated OFF call. If both learning rates are
retained, there are three matched T/W-by-plasticity blocks; do not manufacture
larger `n` by pooling prompts.

Every fit starts from the same frozen base with an empty new LoRA. Within a
seed block, initial trainable tensor bytes and RNG state must match across T/W
and learning rate. Record base, revision, tokenizer, corpus, split, trainer,
initial/final tensor, RNG, optimizer, and environment hashes.

## Parent-free readout

Every checkpoint is serialized and reloaded in a fresh process. Each item has
a fresh context containing only the ordinary task/action contract and that
item. It contains no lesson, worked example, teacher, transcript, note, brief,
retrieval state, prior item, feedback, or update.

- **Exact-form acquisition:** all 64 arithmetic training decision prefixes and
  all 16 factual items after reload. Score T on the true map and W on its own
  map. Low streaming loss alone cannot pass.
- **Development only:** 32 arithmetic requests = eight new operand pairs x two
  keys x two unseen forms, plus one held-form query for each of the 16 taught
  devices. These are the builder's proposed 48 first-look requests.
- **Sealed confirmation:** another disjoint 32 arithmetic requests with the
  same balance but new operands and forms; a second unseen query form for the
  16 taught devices; 16 wholly untaught devices whose correct response is
  explicit unknown; and 16 interface cases (eight exact native-action copies
  and eight ordinary unrelated tasks). Confirmation bytes remain unread until
  seed expansion is complete.

For arithmetic, the primary observation is strict open-loop generation: the
correct number appears in `PREDICT:`, before exactly one correct `ACT:`, with no
teacher forcing. Also record the canonical common-prefix logit margin between
the two legal actions. For each operand/form, score the K0/K1 pair jointly: a
pair succeeds only when both opposite actions and both predictions are
correct. Always-add, always-subtract, a constant number, and a global action
prior score at most one member of every pair.

For facts, require the exact colour under held wording and score all four
colour candidates. A paragraph about remembering, use of the word “reflect”,
or bare production of `PREDICT:` earns nothing.

## Predeclared qualification

A learning rate qualifies only if **each of seeds 0, 1, and 2** meets all of
the following on sealed confirmation:

1. **Acquisition:** T on its train map and W on its own train map each achieve
   at least `.90` strict exact-form accuracy.
2. **Conditional carriage:** T has arithmetic balanced accuracy at least
   `.80`, at least `.75` within each key and form, at least `12/16` complete
   opposite-action pairs, and positive median signed action margin. W meets the
   same thresholds on its own complementary map. On the true map, T exceeds W
   by at least `.25` balanced accuracy and the margin redirection has the
   predeclared sign. OFF must be no better than `.625`; otherwise the panel has
   inadequate headroom and does not confirm teaching.
3. **Taught content:** T recalls at least `12/16` true colours; W recalls at
   least `12/16` of its deranged colours; and T exceeds W by at least `.25` on
   true bindings. OFF above `6/16`, or T and W both high on true bindings,
   invalidates the content interpretation.
4. **Scope and interface:** at least `15/16` untaught devices return unknown;
   exact copy is `8/8`; unrelated-task validity is at least `.95`; there are
   zero multiple-`ACT` emissions. Separately for untaught-device and unrelated
   families, mean two-action TV from the same-block OFF distribution is at
   most `.05`, and the absolute change in legal-action emission rate is at
   most `.05`. Report maxima even though the gate uses means.

Report every seed and family. With three blocks, use conjunctive replication
and descriptive matched effects, not a prompt-level p-value or a population
reliability claim. The plasticity contrast is the three paired differences
`(T-W)_P_hi - (T-W)_P_lo`; it is interpretable only if both rates complete all
three blocks.

## Leakage and shortcut audit

Before OFF or training, freeze and hash the source ledger, T/W maps, all raw
rows, tokenizer output, train/development/confirmation operands, device IDs,
templates, order, parsers, and thresholds. Train, development, and
confirmation operand pairs are disjoint. Taught device IDs necessarily recur
for recall; their held sentences and templates do not. Untaught IDs occur
nowhere in training.

The build must mechanically show:

- action labels are 32/32 in each arithmetic corpus and one of each per
  operand pair; each key, form, operand-length bin, and result-length bin is
  balanced;
- every arithmetic result and complete response has the same corpus marginal
  in T and W; colours are 4/4/4/4 in both;
- no literal held rendering, held operand pair, untaught device ID, target
  action, or future result is present in an evaluation input, apart from the
  two equally displayed legal action strings in the neutral action contract;
- a constant-label, key-only, operand-only, result-length-only, template-only,
  and colour-prior baseline cannot exceed its registered chance ceiling;
- neither corpus nor item was chosen using OFF/ON model output or a prior
  research readout.

Any failure aborts rather than inviting a synonym, resplit, new seed, or
threshold repair inside this experiment.

## Staging and GPU-hour stop

1. **Zero-fit gate:** canary receipt, CPU corpus audits, hashes, native-token
   parity, and OFF/interface headroom. Failure means zero adapters.
2. **Sentinel:** fit T and W at both learning rates with seed 0 only: four
   adapters, 320 optimizer steps. At step 20 perform only finite-loss, tensor,
   reload, and eight-copy interface checks; a destructive pair stops that
   learning rate. At step 80 read only the 48 development requests.
3. **Expansion:** a rate is expanded only if both T and W acquire their own
   exact-form maps, retain interface, and show the registered true-versus-wrong
   redirection on development. Add seeds 1 and 2 for both arms: four adapters
   and 320 steps per retained rate. Only then open confirmation. No confirmation
   result can trigger another fit.

Thus the terminal paths are exactly four adapters (no rate retained), eight
(one retained), or twelve (both retained). Cap the four-adapter sentinel at
`90` aggregate A40-minutes, including its readout. Expansion adds at most the
same `90` minutes per retained learning rate, so total hard caps are `90`,
`180`, or `270` aggregate A40-minutes. Native profiling may lower these caps,
never raise them after outcomes. If `1e-4` acquires but fails only locality,
`3e-5` is a separately presealed future experiment, not an improvised rescue;
if neither rate acquires, do not add epochs or corpus repeats.

## Claim boundary and terminal interpretations

- **Full pass:** this exact authored corpus, versus an equal-dose complementary
  corpus, installed a narrow nonce-conditioned predict-before-act routine and
  nonce facts in fresh rank-8 Qwen LoRAs at the qualifying learning rate(s),
  outside teaching form and with the registered scope/interface bounds.
- **Ordering improves but T does not beat W:** global ritual/interface carriage,
  not content-sensitive teaching.
- **Facts pass but paired arithmetic fails:** narrow factual carriage only.
- **Own-map acquisition passes but held form or spill fails:** stored or fitted,
  but not selectively usable.
- **Null:** this corpus/writer/plasticity package failed; not evidence that LoRA
  post-training, teaching, or Qwen is generally incapable.

Even a full pass is an open-loop supervised level-1 positive control. It is
not a “perfect corpus”, raw-experience compilation, child-authored DREAM,
sleep, retention across sleeps, parenting, autonomous self-learning, H1, H2,
or increased intelligence. Its only promotion value is to define a qualified
target distribution and plasticity setting for the later child-authored,
parent-free H1 bridge.
