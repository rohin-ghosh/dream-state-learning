# Semantic W0 terminal reduction and causal-score contradiction

Date: 2026-09-12 UTC

Status: independent watcher-side reduction of the completed diagnostic run
`astra_semantic_writer_Q0_20260912_attempt1` plus raw validation of the
no-fit supplementary score repair
`astra_semantic_rescore_20260912_attempt1`. This is not a new fit, a repaired
gate, or a scientific promotion. It changes no builder source, job, model,
adapter, benchmark, or claim authority.

## Result in one sentence

Strict generation shows that the four rank-8 adapters did not learn the held
key-conditioned mapping (`0.500--0.578` balanced accuracy, only `1--5/64`
better than OFF). The original unequal-shape BF16 candidate scores are
invalid; a terminal equal-shape no-fit rescore repairs their causal
consistency and shows a large broad action-class shift plus only partial
conditional association. This run does not qualify the writer, and exact-
train evaluation is still needed to distinguish failed storage from failed
held-form extraction.

## Authoritative terminal facts

The node-3 run has `report.json` SHA-256
`31ea19f9d0c8807a30252340dc0582e829bb4ac6d1c438f712e590a909ad31af`
(`348402` bytes), all fourteen stages complete, controller `98756` absent,
and GPU 0 released. `RESOURCE.json` reports `1414.6955` seconds. Original-
source replay reproduces the report. The frozen label is
`OPTIMIZATION_INCONCLUSIVE`; its aggregate gates are:

```text
oracle_ok       true
interface_ok    true
binding_ok      false
optimization_ok false
spill_ok        false
```

All four adapters retain strict generation validity `1.0`, zero multiple
ACTs, zero truncations, and all eight native copy canaries. Their held-form
mapping results are:

| root/map | BA | OFF gain | opposite BA | registered mean conditional gain |
|---|---:|---:|---:|---:|
| root 0 / W+ | .578125 | .078125 | .421875 | .879937 |
| root 0 / W- | .515625 | .015625 | .484375 | 1.001103 |
| root 1 / W+ | .500000 | .015625 | .500000 | .664463 |
| root 1 / W- | .531250 | .015625 | .468750 | .570680 |

Every registered spill family fails the `.05` reported mean-TV bound, with
values from `.275157` to `.659671`. The score contradiction below means these
cannot presently be promoted as calibrated probability distances; they remain
the frozen reducer outputs.

The fixed `.5`-nat all-key optimization gate is itself impossible for 30 of
64 key/map cells from OFF headroom alone. Its failure must not be interpreted
as evidence against learning. Binding near chance in strict generation is a
separate valid negative observation. Score-derived spill and gain values are
provisional until the causal-score path is repaired.

## Causal-score contradiction found during the new reduction

For each saved score pair `(s0,s1)`, define

```text
L_ACT = log(exp(s0) + exp(s1)).
```

The two candidates purport to be complete native continuations
`ACT: -mem2reg\n`+EOS and `ACT: -gvn\n`+EOS. If the stored scores were valid
causal log likelihoods under the same prefix, `L_ACT(ON)-L_ACT(OFF)` would
measure total probability entering the two-action class without crediting
either member as correct. Applying it to the sealed records produces:

| adapter | own held | missing | unsupported | neighbour | wrong root |
|---|---:|---:|---:|---:|---:|
| root 0 / W+ | 25.581 | 28.972 | 27.737 | 27.743 | 25.325 |
| root 0 / W- | 25.603 | 28.968 | 27.773 | 27.748 | 25.333 |
| root 1 / W+ | 25.343 | 28.619 | 29.591 | 29.218 | 25.618 |
| root 1 / W- | 25.352 | 28.592 | 29.541 | 29.240 | 25.596 |

These are arithmetic transformations of the stored scores, **not validated
probability-mass gains**. The interpretation fails an elementary causal
check: `266/832` score requests, all ON, have
`exp(s0)+exp(s1)>1.000001`; the maximum is `1.3802383379`. Two distinct
complete LF+EOS continuations under one identical causal prefix cannot have
summed probability above one.

The builder's completed no-fit diagnosis localizes the inconsistency. For the
maximal contradictory prompt, the probability of the same two next tokens
changes according to which future suffix is appended:

```text
OFF candidate A forward: .991418 / .008577
OFF candidate B forward: .989008 / .010987
OFF prefix-only forward: .982007 / .017986

ON  candidate A forward: .705245 / .293990
ON  candidate B forward: .319712 / .676831
ON  prefix-only forward: .592001 / .406876
```

The maximum common-prefix log-probability disagreement is `1.2788` nats OFF
and `4.7599` nats ON. Recorded eager-attention masks do contain causal
`-inf`-equivalent future entries, so this is not literal future-token leakage.
The builder's follow-up localized the defect to sequence-shape sensitivity in
BF16 for this prompt:

```text
BF16, natural unequal lengths: summed mass 1.380238, inconsistent prefix
BF16, equal total shape:       summed mass 0.997894, exact prefix agreement
FP32, natural unequal lengths: summed mass 0.998979, max delta 7.06e-5
FP32, equal total shape:       summed mass 0.998970, exact agreement
```

Thus separately forwarding unequal-length candidates in BF16 did not supply
one coherent causal probability measure. This localization was one-prompt
evidence; the terminal complete rescore below supplies the all-request check.

Therefore neither this table nor the report's NLL/conditional-TV terminology
is valid probability evidence yet. The builder made a scoped, non-material
repair: pad both candidates to identical total length with future-only EOS
tokens, preserve the original scored-token mask, make positions explicit, and
fail closed unless the shared-prefix distributions agree and the disjoint
candidate mass is at most `1 + 1e-6`. Sixty-two CPU tests pass. This is an
internally coherent fixed-shape diagnostic because those invariants pass over
all `832` saved requests. It is not yet a canonical, generation-equivalent
likelihood: the motivating prompt's first branch probability was `.5920` at
the natural prefix shape, `.7052` under equal-shape BF16, and `.7289` under
equal-shape FP32. A shared-prefix/trie scorer, or a complete higher-precision
comparison showing decision invariance, is required before treating these as
model-intrinsic likelihood/NLL gates. The original report stays unchanged.

The supplementary no-fit rescore completed at `14:00:28 UTC` in `347.468`
seconds. It made zero fits, produced `832` replacement diagnostic scores, and
reused all `880` original generated outputs. Its terminal
`supplementary_report.json` SHA-256 is
`f066f98d19cd3801253d63b0cf0622b77865feabffddaf26c25baa96a32e18df`.
Independent raw enumeration finds exact equality in all `2,496` shared-prefix
token log probabilities and zero mass violations; the largest two-candidate
mass is `.9989317839`.

Under this fixed-shape diagnostic, mean conditional target gains are `1.079`,
`.951`, `.647`, and `.608` nats for root0/W+, root0/W-, root1/W+, and
root1/W-. These positive means coexist with many negative per-key gains and
generation near chance. Meanwhile the mean gain in total probability assigned
to the two registered native actions is about `25.93--26.69` nats in all four
cells and remains broad on missing, unsupported, neighbour, and wrong-root
prompts. Repaired binary spill means remain large (`.280--.656`). The
bounded diagnostic interpretation is therefore not selective mapping:
training strongly installed the native two-action response class, with incomplete
key-conditioned association and extensive off-target change. This cannot
promote the frozen run gates.

A fresh implementation/custody audit also finds that the supplementary runner
does not verify the original sealed inventory before consuming adapters and
generation records, nor seal a replayably state/hardware-bound supplementary
inventory. The builder's own external checks and this watcher's raw arithmetic
support debugging use, but paper-grade promotion requires those bindings and
corruption/wrong-state tests.

Training did optimize something real: mean target-token loss is
`.244--.267`; the last 32 training steps average `.094--.101`, and adapter
update norms are `1.789--1.886`. Those facts do not establish selective
mapping storage. Most supervised response tokens are common native-action
syntax, consistent with the repaired score evidence that common action-class
mass dominated conditional association.

## Highest-information next measurement

Before another writer fit, reuse these four saved adapters for exact-train
**strict generation**, which is independent of this score convention. For
score-based localization, use prefix-by-prefix scoring or validate the full
panel against a canonical higher-precision reference, with original-seal and
state binding repaired. Together these are the minimum
measurements that separate:

1. **stored but not extracted across renderings**: exact-train conditional
   mapping is strong while held mapping remains near chance; next test a
   cross-view/paraphrase compiler;
2. **mapping not stored**: exact-train conditional mapping is also weak; next
   test an identity-focused or pairwise contrastive write objective; or
3. **stored selectively but accompanied by broad action-class change**:
   exact-train and held conditional mappings are strong while a repaired
   absolute endpoint changes out of scope; next test disjoint frozen-OFF
   preservation.

The exact-train panel must keep strict generation separate from conditional
choice and a causally valid absolute two-action endpoint. It cannot repair or
promote this run. No new fit is needed, and no writer branch should be selected
until the generation read and scorer repair land.

If case 2 holds, the most direct next recipe is not another heat or rank sweep.
The present token-mean SFT target rewards many shared `ACT:`/syntax/EOS tokens
for every row and only a small differentiating span. A prospectively bound
pairwise objective over the correct and incorrect complete action
continuations would cancel shared syntax and train the conditional decision
itself. That is a writer-recipe hypothesis, not a conclusion from this run.

## Claim boundary

This diagnostic establishes neither authentic experiential learning nor a
general limitation of LoRA. It establishes that this exact rank-8,
token-mean-SFT, 128-row/two-epoch recipe failed held-form conditional
generation on four supervised root/map instances, and that its score path is
invalid under unequal-shape BF16 evaluation. The supplementary equal-shape
rescore is internally consistent and strongly suggests broad native-action-
class change, but it is a shape-conditioned diagnostic with incomplete
custody—not a canonical likelihood assay. It does **not** qualify the writer
or establish exact-row storage. Exact-train generation and validated scoring
are still required to distinguish failed storage from failed held-view
extraction.
